"""The shared SEC client (R1.3, D5): one per machine, 2 requests per second across SEC
hosts, and a stop on a persistent 403 without changing identity."""

import random
import threading
from datetime import UTC, datetime
from itertools import pairwise

import httpx
import pytest
from earnings_ingestion.fetch.client import AccessStop
from earnings_ingestion.sec.client import MIN_INTERVAL_SECONDS, open_sec_client
from earnings_ingestion.sec.identifiers import pad_cik, unpad_cik
from earnings_ingestion.sec.urls import archive_url, is_sec_host, submissions_url

IDENTITY = "Jane Doe earnings-themes research jane@example.org"
ENVIRON = {"EDGAR_IDENTITY": IDENTITY}


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def opened(tmp_path, handler, clock=None):
    clock = clock or FakeClock()
    return open_sec_client(
        tmp_path,
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


def test_the_client_needs_an_identity(tmp_path) -> None:
    with (
        pytest.raises(AccessStop, match="EDGAR_IDENTITY"),
        open_sec_client(tmp_path, environ={}),
    ):
        pass


def test_one_client_per_machine(tmp_path) -> None:
    def ok(request):
        return httpx.Response(200, text="ok")

    with (
        opened(tmp_path, ok),
        pytest.raises(AccessStop, match="another client holds"),
        opened(tmp_path, ok),
    ):
        pass
    with opened(tmp_path, ok):
        pass


def test_the_client_reaches_sec_hosts_only(tmp_path) -> None:
    with (
        opened(tmp_path, lambda request: httpx.Response(200)) as client,
        pytest.raises(AccessStop, match="outside this client's hosts"),
    ):
        client.get("https://www.example.org/x")


def test_concurrent_workers_stay_at_or_below_two_requests_per_second(tmp_path) -> None:
    """Twelve workers alternate between www.sec.gov and data.sec.gov through the one
    client; every start is at least 0.5 s after the last."""
    seen_agents = []

    def handler(request):
        seen_agents.append(request.headers["user-agent"])
        return httpx.Response(200, headers={"Content-Type": "application/json"})

    with opened(tmp_path, handler) as client:
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


def test_a_persistent_403_stops_without_rotating_identity(tmp_path) -> None:
    agents = []

    def handler(request):
        agents.append(request.headers["user-agent"])
        return httpx.Response(403)

    with (
        opened(tmp_path, handler) as client,
        pytest.raises(AccessStop, match="403 persisted"),
    ):
        client.get(submissions_url("320193"))
    assert agents == [IDENTITY, IDENTITY]


def test_sec_block_page_stops_the_run(tmp_path) -> None:
    def handler(request):
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text="Request Rate Threshold Exceeded",
        )

    with (
        opened(tmp_path, handler) as client,
        pytest.raises(AccessStop, match="block or rate-limit page"),
    ):
        client.fetch(submissions_url("320193"), {"application/json"})
