import gzip
import hashlib
import json
import random
from datetime import UTC, datetime

import httpx
import pytest
from pf_fetch import (
    EdgarFetcher,
    LiveLock,
    LivePolicyStop,
    Throttle,
    UnexpectedResponse,
    meta_path,
    require_identity,
    retry_after_seconds,
)

IDENTITY = "Jane Doe earnings-themes research jane@example.org"
NOW = datetime(2026, 9, 22, 12, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def make_fetcher(handler, clock=None, max_requests=500):
    clock = clock or FakeClock()
    throttle = Throttle(max_requests=max_requests, clock=clock.clock, sleep=clock.sleep)
    fetcher = EdgarFetcher(
        IDENTITY,
        throttle=throttle,
        transport=httpx.MockTransport(handler),
        sleep=clock.sleep,
        rng=random.Random(0),
        now=lambda: NOW,
    )
    return fetcher, clock


def test_identity_must_be_descriptive_with_a_contact():
    assert require_identity({"EDGAR_IDENTITY": IDENTITY}) == IDENTITY
    for bad in (
        {},
        {"EDGAR_IDENTITY": "jane@example.org"},
        {"EDGAR_IDENTITY": "Jane Doe"},
    ):
        with pytest.raises(LivePolicyStop):
            require_identity(bad)


def test_throttle_spaces_request_starts_and_enforces_the_budget():
    clock = FakeClock()
    throttle = Throttle(max_requests=2, clock=clock.clock, sleep=clock.sleep)
    throttle.acquire()
    clock.now += 0.1
    throttle.acquire()
    assert clock.sleeps == [pytest.approx(0.4)]
    with pytest.raises(LivePolicyStop):
        throttle.acquire()
    assert throttle.count == 2


def test_user_agent_is_the_identity():
    seen = []

    def handler(request):
        seen.append(request.headers["user-agent"])
        return httpx.Response(200, text="ok")

    fetcher, _ = make_fetcher(handler)
    fetcher.get("https://www.sec.gov/x")
    assert seen == [IDENTITY]


def test_redirect_hops_are_spaced_and_counted():
    def handler(request):
        if request.url.path == "/old":
            return httpx.Response(301, headers={"Location": "https://www.sec.gov/new"})
        return httpx.Response(200, text="ok")

    fetcher, clock = make_fetcher(handler)
    response = fetcher.get("https://www.sec.gov/old")
    assert str(response.url) == "https://www.sec.gov/new"
    assert fetcher.throttle.count == 2
    assert clock.sleeps == [pytest.approx(0.5)]


def test_429_honours_retry_after_then_succeeds():
    responses = [
        httpx.Response(429, headers={"Retry-After": "7"}),
        httpx.Response(200, text="ok"),
    ]
    fetcher, clock = make_fetcher(lambda request: responses.pop(0))
    assert fetcher.get("https://www.sec.gov/x").status_code == 200
    assert fetcher.throttle.count == 2
    assert max(clock.sleeps) >= 7


def test_a_single_403_is_retried_but_a_persistent_403_stops_the_run():
    once = [httpx.Response(403), httpx.Response(200, text="ok")]
    fetcher, _ = make_fetcher(lambda request: once.pop(0))
    assert fetcher.get("https://www.sec.gov/x").status_code == 200

    fetcher, _ = make_fetcher(lambda request: httpx.Response(403))
    with pytest.raises(LivePolicyStop, match="403 persisted"):
        fetcher.get("https://www.sec.gov/x")
    assert fetcher.throttle.count == 2


def test_server_errors_are_retried_a_bounded_number_of_times():
    fetcher, _ = make_fetcher(lambda request: httpx.Response(503))
    with pytest.raises(LivePolicyStop, match="503"):
        fetcher.get("https://www.sec.gov/x")
    assert fetcher.throttle.count == 4


def test_retry_after_accepts_seconds_and_http_dates():
    assert retry_after_seconds("12", NOW) == 12.0
    assert retry_after_seconds("Tue, 22 Sep 2026 12:00:30 GMT", NOW) == 30.0
    assert retry_after_seconds("soon", NOW) is None


def test_fetch_and_save_writes_decoded_bytes_and_metadata(tmp_path):
    body = b"<html><body>\x93Release\x94</body></html>"

    def handler(request):
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html", "Content-Encoding": "gzip"},
            content=gzip.compress(body),
        )

    fetcher, _ = make_fetcher(handler)
    dest = tmp_path / "x" / "source.html"
    saved = fetcher.fetch_and_save(
        "https://www.sec.gov/Archives/x.htm", dest, {"text/html"}
    )
    assert dest.read_bytes() == body
    assert saved.sha256 == hashlib.sha256(body).hexdigest()
    assert saved.bytes == len(body)
    assert saved.retrieved_at == "2026-09-22T12:00:00Z"
    meta = json.loads(meta_path(dest).read_text())
    assert meta["url"] == "https://www.sec.gov/Archives/x.htm"
    assert IDENTITY not in meta_path(dest).read_text()


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, headers={"Content-Type": "application/json"}, text="{}"),
        httpx.Response(404, headers={"Content-Type": "text/html"}, text="missing"),
    ],
)
def test_unexpected_responses_are_not_saved(tmp_path, response):
    fetcher, _ = make_fetcher(lambda request: response)
    dest = tmp_path / "source.html"
    with pytest.raises(UnexpectedResponse):
        fetcher.fetch_and_save("https://www.sec.gov/x.htm", dest, {"text/html"})
    assert not dest.exists()


def test_a_block_page_served_with_200_stops_the_run(tmp_path):
    block = httpx.Response(
        200,
        headers={"Content-Type": "text/html"},
        text="Your Request Originates from an Undeclared Automated Tool",
    )
    fetcher, _ = make_fetcher(lambda request: block)
    dest = tmp_path / "source.html"
    with pytest.raises(LivePolicyStop, match="block or rate-limit page"):
        fetcher.fetch_and_save("https://www.sec.gov/x.htm", dest, {"text/html"})
    assert not dest.exists()


def test_only_one_live_process_at_a_time(tmp_path):
    lock_path = tmp_path / "live.lock"
    with LiveLock(lock_path), pytest.raises(LivePolicyStop), LiveLock(lock_path):
        pass
    with LiveLock(lock_path):
        pass
