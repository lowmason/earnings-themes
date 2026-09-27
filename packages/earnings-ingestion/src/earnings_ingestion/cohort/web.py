"""The cohort's client for sources outside SEC: roster revisions and index notices.

- **Polite.** One request per second across these hosts, within a per-run budget,
  with the SEC client's retries, ``Retry-After`` handling, and stop on a persistent
  403. The User-Agent is the identity in ``SOURCE_IDENTITY``, configured outside Git
  and never recorded.
- **Registered hosts only.** It reaches only the hosts it is opened for, the hosts of
  registered sources, and never an SEC host: SEC requests go through the shared SEC
  client alone (D5).
- **Robots first.** Each page is checked against its site's robots.txt (RFC 9309)
  before it is requested. A disallowed page is refused, never fetched: a person saves
  it in a browser and registers it instead (P §Membership evidence: live acquisition
  never bypasses robots restrictions).
- **One per machine.** Its lock lives in ``machine_lock_dir()``, outside every
  checkout, like the SEC client's.
"""

import random
import time
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx

from earnings_ingestion.fetch.client import (
    DEFAULT_MAX_REQUESTS,
    AccessStop,
    Fetched,
    PoliteClient,
    ProcessLock,
    Throttle,
    machine_lock_dir,
    require_identity,
)
from earnings_ingestion.fetch.robots import RobotsGate
from earnings_ingestion.sec.urls import is_sec_host

IDENTITY_ENV = "SOURCE_IDENTITY"
MIN_INTERVAL_SECONDS = 1.0
LOCK_NAME = "web-client.lock"
"""In ``machine_lock_dir()``: every cohort web client on this machine takes it."""


class RobotsRefusal(AccessStop):
    """robots.txt disallows the page; save it in a browser and register it."""


class WebFetcher:
    """Fetches a page only after its site's robots.txt allows it."""

    def __init__(self, client: PoliteClient, gate: RobotsGate) -> None:
        self.client = client
        self.gate = gate

    def fetch(self, url: str, expected_types: Collection[str]) -> Fetched:
        verdict = self.gate.verdict(url)
        if not verdict.allowed:
            reason = verdict.rule or f"robots.txt answered {verdict.robots_status}"
            raise RobotsRefusal(
                f"{url} is refused by robots.txt ({reason}); save it in a browser"
                " and register it with `earnings-pipeline cohort register`"
            )
        return self.client.fetch(url, expected_types)


def hosts_of(urls: Iterable[str]) -> frozenset[str]:
    return frozenset(urlsplit(url).hostname or "" for url in urls) - {""}


@contextmanager
def open_web_client(
    hosts: Iterable[str],
    *,
    environ: Mapping[str, str] | None = None,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    transport: httpx.BaseTransport | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Iterator[WebFetcher]:
    """The machine's one cohort web client, for ``hosts`` only."""
    allowed = frozenset(host.lower() for host in hosts)
    sec = sorted(host for host in allowed if is_sec_host(host))
    if sec:
        raise ValueError(f"SEC hosts go through the shared SEC client: {sec}")
    identity = require_identity(IDENTITY_ENV, environ)
    with ProcessLock(machine_lock_dir() / LOCK_NAME):
        throttle = Throttle(
            min_interval=MIN_INTERVAL_SECONDS,
            max_requests=max_requests,
            clock=clock,
            sleep=sleep,
        )
        client = PoliteClient(
            identity,
            throttle=throttle,
            host_allowed=allowed.__contains__,
            transport=transport,
            sleep=sleep,
            rng=rng,
            now=now,
        )
        try:
            yield WebFetcher(client, RobotsGate(client))
        finally:
            client.close()
