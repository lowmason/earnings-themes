"""The shared SEC client (R1.3, D5): every SEC request in the monorepo goes through it.

- **One per machine.** ``open_sec_client`` holds the SEC lock while the client is open,
  so a second client stops instead of opening, in this process or another, from this
  checkout or any other. Share the one instance across workers: its throttle is
  thread-safe.
- **2 requests per second.** Request starts are spaced 0.5 s apart across every SEC
  host, redirect hops included (A §397), within a per-run budget.
- **Identity.** The User-Agent is the descriptive identity in ``EDGAR_IDENTITY``,
  configured outside Git and never recorded (A §393).
- **Refusals.** A 403 that persists, or SEC's block page, stops the run without
  changing identity (A §404).

Two limits remain, because A §398 asks for coordination across the outbound network.
The lock lives in ``machine_lock_dir()``, outside every checkout, so it coordinates the
processes of one machine, every worktree and clone included, and no more. Stage 1's
frozen harness keeps its own client and lock, so it must never run live at the same
time.
"""

import random
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime

import httpx

from earnings_ingestion.fetch.client import (
    DEFAULT_MAX_REQUESTS,
    PoliteClient,
    ProcessLock,
    Throttle,
    machine_lock_dir,
    require_identity,
)
from earnings_ingestion.sec.urls import SEC_HOSTS

IDENTITY_ENV = "EDGAR_IDENTITY"
MIN_INTERVAL_SECONDS = 0.5  # the project default of 2 requests per second (A §397)
BLOCK_MARKERS = (b"undeclared automated tool", b"request rate threshold exceeded")
LOCK_NAME = "sec-client.lock"
"""In ``machine_lock_dir()``: every SEC client on this machine takes this one lock."""


class SecClient(PoliteClient):
    """The shared SEC client. Open it with ``open_sec_client``, never directly."""

    def __init__(
        self,
        identity: str,
        *,
        throttle: Throttle,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        super().__init__(
            identity,
            throttle=throttle,
            host_allowed=SEC_HOSTS.__contains__,
            block_markers=BLOCK_MARKERS,
            transport=transport,
            sleep=sleep,
            rng=rng,
            now=now,
        )


@contextmanager
def open_sec_client(
    *,
    environ: Mapping[str, str] | None = None,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    transport: httpx.BaseTransport | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Iterator[SecClient]:
    """The machine's one SEC client, holding the SEC lock while open."""
    identity = require_identity(IDENTITY_ENV, environ)
    with ProcessLock(machine_lock_dir() / LOCK_NAME):
        throttle = Throttle(
            min_interval=MIN_INTERVAL_SECONDS,
            max_requests=max_requests,
            clock=clock,
            sleep=sleep,
        )
        client = SecClient(
            identity,
            throttle=throttle,
            transport=transport,
            sleep=sleep,
            rng=rng,
            now=now,
        )
        try:
            yield client
        finally:
            client.close()
