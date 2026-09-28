"""The polite client: the access policy of A §393-408, ported from pf_fetch (D5)."""

import gzip
import random
import sys
import threading
from datetime import UTC, datetime
from itertools import pairwise

import httpx
import pytest
from earnings_core import sha256_hex
from earnings_ingestion.fetch.client import (
    LOCK_DIR_VARIABLE,
    AccessStop,
    PoliteClient,
    ProcessLock,
    Throttle,
    UnexpectedResponse,
    machine_lock_dir,
    require_identity,
    retry_after_seconds,
)
from earnings_ingestion.fetch.records import RetrievalMethod

IDENTITY = "Jane Doe earnings-themes research jane@example.org"
NOW = datetime(2026, 9, 22, 12, 0, 0, tzinfo=UTC)
MARKERS = (b"undeclared automated tool",)


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def make_client(handler, *, clock=None, max_requests=500, host_allowed=None):
    clock = clock or FakeClock()
    throttle = Throttle(
        min_interval=0.5,
        max_requests=max_requests,
        clock=clock.clock,
        sleep=clock.sleep,
    )
    client = PoliteClient(
        IDENTITY,
        throttle=throttle,
        host_allowed=host_allowed or (lambda host: host.endswith("example.gov")),
        block_markers=MARKERS,
        transport=httpx.MockTransport(handler),
        sleep=clock.sleep,
        rng=random.Random(0),
        now=lambda: NOW,
    )
    return client, clock


def test_identity_must_be_descriptive_with_a_contact() -> None:
    assert require_identity("X_IDENTITY", {"X_IDENTITY": IDENTITY}) == IDENTITY
    for bad in ({}, {"X_IDENTITY": "jane@example.org"}, {"X_IDENTITY": "Jane Doe"}):
        with pytest.raises(AccessStop, match="X_IDENTITY"):
            require_identity("X_IDENTITY", bad)


def test_throttle_spaces_request_starts_and_enforces_the_budget() -> None:
    clock = FakeClock()
    throttle = Throttle(
        min_interval=0.5, max_requests=2, clock=clock.clock, sleep=clock.sleep
    )
    throttle.acquire()
    clock.now += 0.1
    throttle.acquire()
    assert clock.sleeps == [pytest.approx(0.4)]
    with pytest.raises(AccessStop, match="budget"):
        throttle.acquire()
    assert throttle.count == 2
    assert throttle.starts == [100.0, pytest.approx(100.5)]


def test_the_user_agent_is_the_identity() -> None:
    seen = []

    def handler(request):
        seen.append(request.headers["user-agent"])
        return httpx.Response(200, text="ok")

    client, _ = make_client(handler)
    client.get("https://www.example.gov/x")
    assert seen == [IDENTITY]


def test_redirect_hops_are_spaced_and_counted() -> None:
    def handler(request):
        if request.url.path == "/old":
            return httpx.Response(
                301, headers={"Location": "https://www.example.gov/new"}
            )
        return httpx.Response(200, text="ok")

    client, clock = make_client(handler)
    response = client.get("https://www.example.gov/old")
    assert str(response.url) == "https://www.example.gov/new"
    assert client.throttle.count == 2
    assert clock.sleeps == [pytest.approx(0.5)]


def test_a_redirect_off_the_allowed_hosts_stops_the_run() -> None:
    def handler(request):
        return httpx.Response(301, headers={"Location": "https://elsewhere.org/x"})

    client, _ = make_client(handler)
    with pytest.raises(AccessStop, match="outside this client's hosts"):
        client.get("https://www.example.gov/x")
    with pytest.raises(AccessStop, match="outside this client's hosts"):
        client.get("https://elsewhere.org/y")
    assert client.throttle.count == 1


def test_429_honours_retry_after_then_succeeds() -> None:
    responses = [
        httpx.Response(429, headers={"Retry-After": "7"}),
        httpx.Response(200, text="ok"),
    ]
    client, clock = make_client(lambda request: responses.pop(0))
    assert client.get("https://www.example.gov/x").status_code == 200
    assert client.throttle.count == 2
    assert max(clock.sleeps) >= 7


def test_a_persistent_403_stops_without_changing_identity() -> None:
    once = [httpx.Response(403), httpx.Response(200, text="ok")]
    client, _ = make_client(lambda request: once.pop(0))
    assert client.get("https://www.example.gov/x").status_code == 200

    agents = []

    def forbidden(request):
        agents.append(request.headers["user-agent"])
        return httpx.Response(403)

    client, _ = make_client(forbidden)
    with pytest.raises(AccessStop, match="403 persisted"):
        client.get("https://www.example.gov/x")
    assert client.throttle.count == 2
    assert agents == [IDENTITY, IDENTITY]


def test_server_errors_are_retried_a_bounded_number_of_times() -> None:
    client, _ = make_client(lambda request: httpx.Response(503))
    with pytest.raises(AccessStop, match="503"):
        client.get("https://www.example.gov/x")
    assert client.throttle.count == 4


def test_retry_after_accepts_seconds_and_http_dates() -> None:
    assert retry_after_seconds("12", NOW) == 12.0
    assert retry_after_seconds("Tue, 22 Sep 2026 12:00:30 GMT", NOW) == 30.0
    assert retry_after_seconds("soon", NOW) is None


@pytest.mark.parametrize(
    "value",
    [chr(0xB2), chr(0xFF11) + chr(0xFF12), chr(0x0661) + chr(0x0660)],
    ids=["superscript-two", "fullwidth-twelve", "arabic-indic-ten"],
)
def test_retry_after_ignores_non_ascii_digits(value) -> None:
    """Plan 6's deferred robustness fix: a header of other scripts' digits is
    unreadable, so it is ignored, never obeyed and never an error."""
    assert retry_after_seconds(value, NOW) is None


def test_fetch_returns_decoded_bytes_and_a_retrieval() -> None:
    body = b'{"a": 1}'

    def handler(request):
        return httpx.Response(
            200,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Content-Encoding": "gzip",
            },
            content=gzip.compress(body),
        )

    client, _ = make_client(handler)
    fetched = client.fetch("https://www.example.gov/a.json", {"application/json"})
    assert fetched.body == body
    retrieval = fetched.retrieval
    assert retrieval.sha256 == sha256_hex(body)
    assert retrieval.byte_count == len(body)
    assert retrieval.media_type == "application/json"
    assert retrieval.content_type == "application/json; charset=utf-8"
    assert retrieval.retrieved_at == NOW
    assert retrieval.retrieval_method is RetrievalMethod.HTTP
    assert IDENTITY not in retrieval.model_dump_json()


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, headers={"Content-Type": "text/plain"}, text="{}"),
        httpx.Response(404, headers={"Content-Type": "application/json"}, text="{}"),
    ],
)
def test_unexpected_responses_are_refused(response) -> None:
    client, _ = make_client(lambda request: response)
    with pytest.raises(UnexpectedResponse):
        client.fetch("https://www.example.gov/a.json", {"application/json"})


def test_a_block_page_stops_the_run_even_where_json_was_expected() -> None:
    block = httpx.Response(
        200,
        headers={"Content-Type": "text/html"},
        text="Your Request Originates from an Undeclared Automated Tool",
    )
    client, _ = make_client(lambda request: block)
    with pytest.raises(AccessStop, match="block or rate-limit page"):
        client.fetch("https://www.example.gov/a.json", {"application/json"})


def test_only_one_lock_holder_at_a_time(tmp_path) -> None:
    path = tmp_path / "client.lock"
    with ProcessLock(path), pytest.raises(AccessStop), ProcessLock(path):
        pass
    with ProcessLock(path):
        pass


def test_the_lock_directory_is_the_users_cache_outside_every_checkout(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.delenv(LOCK_DIR_VARIABLE)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "darwin")
    mac = tmp_path / "Library" / "Caches" / "earnings-themes" / "locks"
    assert machine_lock_dir() == mac
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    assert machine_lock_dir() == tmp_path / ".cache" / "earnings-themes" / "locks"
    monkeypatch.setenv("XDG_CACHE_HOME", "relative/cache")
    assert machine_lock_dir() == tmp_path / ".cache" / "earnings-themes" / "locks"
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert machine_lock_dir() == tmp_path / "xdg" / "earnings-themes" / "locks"
    monkeypatch.setenv(LOCK_DIR_VARIABLE, str(tmp_path / "override"))
    assert machine_lock_dir() == tmp_path / "override"


def test_concurrent_workers_share_one_allowance() -> None:
    """Eight threads through one client: starts at least 0.5 s apart, so no more
    than two start in any second (R1.3's 2 requests per second)."""
    client, _ = make_client(lambda request: httpx.Response(200, text="ok"))
    barrier = threading.Barrier(8)

    def worker(n: int) -> None:
        barrier.wait()
        client.get(f"https://www.example.gov/{n}")

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    starts = client.throttle.starts
    assert len(starts) == 8
    assert all(b - a >= 0.5 - 1e-9 for a, b in pairwise(starts))
    assert all(
        sum(start <= other < start + 1.0 for other in starts) <= 2 for start in starts
    )
