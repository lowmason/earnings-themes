"""A robots.txt gate for every source but SEC (P §Membership evidence and source rights).

Live acquisition must not bypass robots restrictions. The gate reads the rules of the
``*`` group under RFC 9309:

- the longest matching rule wins, and an allow rule wins a tie;
- ``*`` matches any run of characters, and a trailing ``$`` anchors the end;
- rules match the URL's path and query, compared as written.

A robots.txt answering 404 or 410 allows everything. Any other failure disallows
everything, which is stricter than RFC 9309: a 401 or another 4xx, or a response the
client gives up on. A 403 that persists stops the client itself (A §404).
CPython's ``urllib.robotparser`` is not used, because it applies the first matching
rule and knows no wildcards.
"""

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from earnings_ingestion.fetch.client import PoliteClient


@dataclass(frozen=True)
class Rule:
    allow: bool
    pattern: str


@dataclass(frozen=True)
class RobotsVerdict:
    """Whether ``url`` may be fetched, and why."""

    url: str
    allowed: bool
    robots_status: int
    rule: str | None
    """The deciding rule, e.g. ``Disallow: /w/``; None when no rule matched."""


def parse_robots(text: str) -> tuple[Rule, ...]:
    """The allow and disallow rules of every group whose user-agent is ``*``."""
    rules: list[Rule] = []
    agents: list[str] = []
    in_rules = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        field, colon, value = line.partition(":")
        if not colon:
            continue
        field, value = field.strip().lower(), value.strip()
        if field == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(value.lower())
        elif field in ("allow", "disallow"):
            in_rules = True
            if "*" in agents and value:
                rules.append(Rule(allow=field == "allow", pattern=value))
    return tuple(rules)


def _matches(pattern: str, target: str) -> bool:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    regex = "".join(".*" if char == "*" else re.escape(char) for char in body)
    return re.match(regex + (r"\Z" if anchored else ""), target, re.DOTALL) is not None


def decide(rules: tuple[Rule, ...], target: str) -> tuple[bool, Rule | None]:
    """RFC 9309's verdict for ``target``, a path with its query."""
    best: Rule | None = None
    for rule in rules:
        if not _matches(rule.pattern, target):
            continue
        if (
            best is None
            or len(rule.pattern) > len(best.pattern)
            or (len(rule.pattern) == len(best.pattern) and rule.allow)
        ):
            best = rule
    return (True if best is None else best.allow), best


class RobotsGate:
    """Reads each origin's robots.txt once, through the client, and answers per URL."""

    def __init__(self, client: PoliteClient) -> None:
        self._client = client
        self._origins: dict[str, tuple[int, tuple[Rule, ...] | None]] = {}

    def verdict(self, url: str) -> RobotsVerdict:
        parts = urlsplit(url)
        status, rules = self._rules(f"{parts.scheme}://{parts.netloc}")
        if rules is None:
            return RobotsVerdict(
                url=url, allowed=False, robots_status=status, rule=None
            )
        target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        allowed, rule = decide(rules, target)
        written = None
        if rule is not None:
            written = f"{'Allow' if rule.allow else 'Disallow'}: {rule.pattern}"
        return RobotsVerdict(
            url=url, allowed=allowed, robots_status=status, rule=written
        )

    def _rules(self, origin: str) -> tuple[int, tuple[Rule, ...] | None]:
        if origin not in self._origins:
            response = self._client.get(f"{origin}/robots.txt")
            if response.status_code == 200:
                rules: tuple[Rule, ...] | None = parse_robots(response.text)
            elif response.status_code in (404, 410):
                rules = ()
            else:
                rules = None
            self._origins[origin] = (response.status_code, rules)
        return self._origins[origin]
