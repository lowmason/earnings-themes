"""The shared SEC client (R1.3, D5): one per machine, 2 requests per second across SEC
hosts, and a stop on a persistent 403 without changing identity."""

import random
import subprocess
import sys
import threading
from datetime import UTC, datetime
from itertools import pairwise

import httpx
import pytest
from earnings_ingestion.fetch.client import (
    AccessStop,
    UnexpectedResponse,
    machine_lock_dir,
)
from earnings_ingestion.sec.client import (
    LOCK_NAME,
    MIN_INTERVAL_SECONDS,
    open_sec_client,
)
from earnings_ingestion.sec.identifiers import Cik, pad_cik, unpad_cik
from earnings_ingestion.sec.urls import archive_url, is_sec_host, submissions_url
from pydantic import TypeAdapter, ValidationError

IDENTITY = "Jane Doe earnings-themes research jane@example.org"
ENVIRON = {"EDGAR_IDENTITY": IDENTITY}


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def opened(handler, clock=None):
    clock = clock or FakeClock()
    return open_sec_client(
        environ=ENVIRON,
        transport=httpx.MockTransport(handler),
        clock=clock.clock,
        sleep=clock.sleep,
        rng=random.Random(0),
        now=lambda: datetime(2026, 9, 27, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    ("value", "padded"),
    [(320193, "0000320193"), ("320193", "0000320193"), ("0000320193", "0000320193")],
    ids=["int", "unpadded", "padded"],
)
def test_a_cik_is_ten_zero_padded_digits(value, padded) -> None:
    assert pad_cik(value) == padded
    assert unpad_cik(padded) == "320193"


@pytest.mark.parametrize("value", ["", "0", "12345678901", "32O193", True, -5])
def test_a_non_cik_is_refused(value) -> None:
    with pytest.raises(ValueError, match="not a CIK"):
        pad_cik(value)


def _digits(text: str, zero: int) -> str:
    """``text``'s digits written in the script whose zero is code point ``zero``."""
    return "".join(chr(zero + int(digit)) for digit in text)


@pytest.mark.parametrize("zero", [0xFF10, 0x0660], ids=["fullwidth", "arabic-indic"])
def test_a_cik_is_written_in_ascii_digits_only(zero) -> None:
    with pytest.raises(ValueError, match="not a CIK"):
        pad_cik(_digits("320193", zero))
    with pytest.raises(ValidationError):
        TypeAdapter(Cik).validate_python(_digits("0000320193", zero))


def test_urls_use_each_endpoints_cik_form() -> None:
    assert (
        submissions_url("320193")
        == "https://data.sec.gov/submissions/CIK0000320193.json"
    )
    assert archive_url("0001041130", "0001752724-24-212345", "primary_doc.xml") == (
        "https://www.sec.gov/Archives/edgar/data/1041130/000175272424212345/"
        "primary_doc.xml"
    )


def test_only_sec_hosts_are_sec_hosts() -> None:
    assert is_sec_host("www.sec.gov") and is_sec_host("DATA.SEC.GOV")
    assert not is_sec_host("sec.gov.example.org")


def test_a_trailing_dot_does_not_hide_a_sec_host() -> None:
    assert is_sec_host("www.sec.gov.") and is_sec_host("DATA.SEC.GOV.")
    assert not is_sec_host("sec.gov.example.org.")


def test_the_client_needs_an_identity() -> None:
    with (
        pytest.raises(AccessStop, match="EDGAR_IDENTITY"),
        open_sec_client(environ={}),
    ):
        pass


def ok(request):
    return httpx.Response(200, text="ok")


def test_one_client_per_machine() -> None:
    with (
        opened(ok),
        pytest.raises(AccessStop, match="another client holds"),
        opened(ok),
    ):
        pass
    with opened(ok):
        pass


CHILD = """
import sys
from earnings_ingestion.fetch.client import AccessStop
from earnings_ingestion.sec.client import open_sec_client
try:
    with open_sec_client(environ={"EDGAR_IDENTITY": sys.argv[1]}):
        print("opened")
except AccessStop as stop:
    print(stop)
"""


def test_two_checkouts_share_one_lock(tmp_path, monkeypatch) -> None:
    """A second worktree or clone is another process in another directory. It finds
    the lock this one holds, in the machine's lock directory (plan 6's deferred item).
    """
    first, second = tmp_path / "checkout-a", tmp_path / "checkout-b"
    first.mkdir()
    second.mkdir()
    monkeypatch.chdir(first)
    with opened(ok):
        child = subprocess.run(
            [sys.executable, "-c", CHILD, IDENTITY],
            cwd=second,
            capture_output=True,
            text=True,
            check=True,
        )
    assert child.stdout.strip() == (
        f"another client holds {machine_lock_dir() / LOCK_NAME}"
    )


def test_the_client_reaches_sec_hosts_only() -> None:
    with (
        opened(lambda request: httpx.Response(200)) as client,
        pytest.raises(AccessStop, match="outside this client's hosts"),
    ):
        client.get("https://www.example.org/x")


def test_the_client_refuses_a_sec_host_written_with_a_trailing_dot() -> None:
    with (
        opened(lambda request: httpx.Response(200)) as client,
        pytest.raises(AccessStop, match="outside this client's hosts"),
    ):
        client.get("https://www.sec.gov./files/company_tickers.json")


def test_concurrent_workers_stay_at_or_below_two_requests_per_second() -> None:
    """Twelve workers alternate between www.sec.gov and data.sec.gov through the one
    client; every start is at least 0.5 s after the last."""
    seen_agents = []

    def handler(request):
        seen_agents.append(request.headers["user-agent"])
        return httpx.Response(200, headers={"Content-Type": "application/json"})

    with opened(handler) as client:
        barrier = threading.Barrier(12)

        def worker(n: int) -> None:
            host = "www.sec.gov" if n % 2 else "data.sec.gov"
            barrier.wait()
            client.get(f"https://{host}/{n}")

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        starts = client.throttle.starts
    assert client.throttle.min_interval == MIN_INTERVAL_SECONDS == 0.5
    assert len(starts) == 12
    assert all(b - a >= 0.5 - 1e-9 for a, b in pairwise(starts))
    assert all(sum(s <= t < s + 1.0 for t in starts) <= 2 for s in starts)
    assert set(seen_agents) == {IDENTITY}


def test_a_persistent_403_stops_without_rotating_identity() -> None:
    agents = []

    def handler(request):
        agents.append(request.headers["user-agent"])
        return httpx.Response(403)

    with (
        opened(handler) as client,
        pytest.raises(AccessStop, match="403 persisted"),
    ):
        client.get(submissions_url("320193"))
    assert agents == [IDENTITY, IDENTITY]


def test_sec_block_page_stops_the_run() -> None:
    def handler(request):
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text="Request Rate Threshold Exceeded",
        )

    with (
        opened(handler) as client,
        pytest.raises(AccessStop, match="block or rate-limit page"),
    ):
        client.fetch(submissions_url("320193"), {"application/json"})


def test_a_redirected_response_is_refused_before_it_is_saved() -> None:
    """A response served from another URL than the one requested is never saved or
    read under the URL requested (PR #6's review, F13)."""

    def handler(request):
        if request.url.path == "/moved.htm":
            return httpx.Response(
                301, headers={"Location": "https://www.sec.gov/other.htm"}
            )
        return httpx.Response(200, headers={"Content-Type": "text/html"}, text="x")

    with (
        opened(handler) as client,
        pytest.raises(
            UnexpectedResponse, match="redirected to https://www.sec.gov/other.htm"
        ),
    ):
        client.fetch("https://www.sec.gov/moved.htm", {"text/html"})


@pytest.mark.parametrize(
    ("served", "refusal"),
    [
        (
            {"headers": {"Content-Encoding": "gzip"}, "content": b"not gzip"},
            "sent a body that cannot be decoded",
        ),
        ({"loop": True}, "was redirected without end"),
    ],
    ids=["undecodable", "redirect-loop"],
)
def test_a_response_httpx_cannot_finish_is_refused_as_unexpected(
    served, refusal
) -> None:
    """httpx's ``DecodingError`` and ``TooManyRedirects`` are neither transport
    errors nor refusals, so the client refuses them as it refuses a redirect, and
    each caller records the exhibit's attempt (plan 8's final review)."""

    def handler(request):
        if served.get("loop"):
            return httpx.Response(301, headers={"Location": str(request.url)})
        headers = {"Content-Type": "text/html", **served["headers"]}
        return httpx.Response(200, headers=headers, content=served["content"])

    with opened(handler) as client, pytest.raises(UnexpectedResponse, match=refusal):
        client.fetch("https://www.sec.gov/x.htm", {"text/html"})
