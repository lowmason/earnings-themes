"""The robots gate: RFC 9309 longest match for the ``*`` group."""

import random
from datetime import UTC, datetime

import httpx
import pytest
from earnings_ingestion.fetch.client import AccessStop, PoliteClient, Throttle
from earnings_ingestion.fetch.robots import RobotsGate, decide, parse_robots

ROBOTS = """
User-agent: SomeBot
Disallow: /

User-agent: *
Allow: /w/api.php?action=mobileview&
Disallow: /w/
Disallow: /api/
Disallow: /*.pdf$
Allow: /wiki/Special:Export
Disallow: /wiki/Special:
Disallow:
"""


def gate_for(handler) -> tuple[RobotsGate, PoliteClient]:
    client = PoliteClient(
        "Jane Doe earnings-themes research jane@example.org",
        throttle=Throttle(min_interval=0.0),
        transport=httpx.MockTransport(handler),
        sleep=lambda seconds: None,
        rng=random.Random(0),
        now=lambda: datetime(2026, 9, 27, tzinfo=UTC),
    )
    return RobotsGate(client), client


@pytest.mark.parametrize(
    ("target", "allowed"),
    [
        ("/wiki/Dow_Jones_Industrial_Average?oldid=123", True),
        ("/w/index.php?oldid=123&action=raw", False),
        ("/w/api.php?action=mobileview&page=X", True),
        ("/api/rest_v1/page/html/X", False),
        ("/files/release.pdf", False),
        ("/files/release.pdf?download=1", True),
        ("/wiki/Special:Export/X", True),
        ("/wiki/Special:History", False),
    ],
)
def test_the_longest_matching_rule_decides(target, allowed) -> None:
    assert decide(parse_robots(ROBOTS), target)[0] is allowed


def test_other_agents_groups_are_ignored_and_an_empty_disallow_adds_nothing() -> None:
    rules = parse_robots(ROBOTS)
    assert all(rule.pattern != "/" for rule in rules)
    assert len(rules) == 6


def test_an_allow_rule_wins_a_tie() -> None:
    rules = parse_robots("User-agent: *\nDisallow: /a\nAllow: /a\n")
    assert decide(rules, "/a")[0] is True


def test_the_gate_reads_robots_once_per_origin() -> None:
    fetched = []

    def handler(request):
        fetched.append(str(request.url))
        return httpx.Response(200, text=ROBOTS)

    gate, _ = gate_for(handler)
    first = gate.verdict("https://en.example.org/w/index.php?title=X")
    second = gate.verdict("https://en.example.org/wiki/X?oldid=9")
    assert (first.allowed, first.rule) == (False, "Disallow: /w/")
    assert (second.allowed, second.rule) == (True, None)
    assert fetched == ["https://en.example.org/robots.txt"]


@pytest.mark.parametrize(
    ("status", "allowed"), [(404, True), (410, True), (401, False)]
)
def test_a_missing_robots_allows_and_a_refused_one_disallows(status, allowed) -> None:
    gate, _ = gate_for(lambda request: httpx.Response(status))
    verdict = gate.verdict("https://en.example.org/wiki/X")
    assert (verdict.allowed, verdict.robots_status) == (allowed, status)


def test_a_persistent_403_on_robots_stops_the_source() -> None:
    gate, _ = gate_for(lambda request: httpx.Response(403))
    with pytest.raises(AccessStop, match="403 persisted"):
        gate.verdict("https://www.example.com/terms")
