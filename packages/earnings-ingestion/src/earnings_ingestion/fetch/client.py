"""A polite HTTP client for source adapters: one identity, one throttle, bounded retries.

Ported from Stage 1's live-fetch client, ``expirements/parser-fidelity/pf_fetch.py``
(D5: port it, never import it). What changed:

- The throttle is thread-safe, so workers share one client and one allowance.
- A host filter refuses any request, redirect hops included, outside the client's
  hosts.
- A text/html body carrying a block page stops the run before the content type is
  checked, so a block page served where JSON was expected also stops it.
- ``fetch`` returns the bytes and a ``Retrieval`` and writes nothing. The artifact
  store decides where bytes live.

A §393-408 govern every client. Each request start, redirect hops included, passes
the throttle. Timeouts are explicit, retries are bounded, with exponential backoff and
jitter, and ``Retry-After`` is honoured. A 403 that persists stops the run and the
identity is never changed. The identity is sent as the User-Agent and never recorded.

Each package client holds its lock in ``machine_lock_dir()``, one directory per user
outside every checkout, so one client runs per machine however many worktrees or
clones exist.
"""

import email.utils
import fcntl
import os
import random
import re
import sys
import threading
import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Self
from urllib.parse import urlsplit

import httpx
from earnings_core import sha256_hex

from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod

DEFAULT_MAX_REQUESTS = 500
MAX_ATTEMPTS = 4
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_CAP_SECONDS = 60.0
MAX_RETRY_AFTER_SECONDS = 300.0
TIMEOUT = httpx.Timeout(30.0, connect=10.0)
FORBIDDEN_LIMIT = 2  # a 403 on an attempt and again on its retry is "persistent"
BLOCK_SCAN_BYTES = 20_000
LOCK_DIR_VARIABLE = "EARNINGS_LOCK_DIR"

_CONTACT = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class AccessStop(RuntimeError):
    """The run must stop and be reported.

    Raised for a missing identity, a spent budget, a held lock, a persistent 403,
    exhausted retries, a block page, or a host outside the client's filter.
    """


class UnexpectedResponse(RuntimeError):
    """A response that must not be kept; the caller may skip the item and go on."""


def require_identity(variable: str, environ: Mapping[str, str] | None = None) -> str:
    """The descriptive User-Agent in ``variable``, which lives outside Git."""
    value = (os.environ if environ is None else environ).get(variable, "").strip()
    if len(value.split()) < 2 or not _CONTACT.search(value):
        raise AccessStop(
            f"{variable} must be set outside Git to a descriptive User-Agent with a"
            " real contact, such as 'Jane Doe earnings-themes research"
            " jane@example.org'"
        )
    return value


def machine_lock_dir() -> Path:
    """Where every package client's lock lives: one directory per user, outside
    every checkout (plan 7, P7-5).

    ``$EARNINGS_LOCK_DIR`` overrides it, for tests. Otherwise it is the user's cache:
    ``~/Library/Caches/earnings-themes/locks`` on macOS, and elsewhere
    ``$XDG_CACHE_HOME/earnings-themes/locks``, or ``~/.cache`` when that variable is
    unset or not absolute.
    """
    override = os.environ.get(LOCK_DIR_VARIABLE)
    if override:
        return Path(override)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "earnings-themes" / "locks"
    xdg = os.environ.get("XDG_CACHE_HOME", "")
    cache = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / ".cache"
    return cache / "earnings-themes" / "locks"


def retry_after_seconds(value: str | None, now: datetime) -> float | None:
    """The wait a ``Retry-After`` header asks for, in seconds, or None if unreadable."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, (when - now).total_seconds())


class Throttle:
    """Spaces request starts ``min_interval`` apart across threads, within a budget.

    The lock is held while waiting, so starts are serialised. ``starts`` records each
    start's clock reading, taken under the lock.
    """

    def __init__(
        self,
        *,
        min_interval: float,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.min_interval = min_interval
        self.max_requests = max_requests
        self.starts: list[float] = []
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()

    @property
    def count(self) -> int:
        """Requests started so far."""
        return len(self.starts)

    def acquire(self) -> None:
        with self._lock:
            if len(self.starts) >= self.max_requests:
                raise AccessStop(
                    f"request budget of {self.max_requests} reached; rerun to continue"
                )
            now = self._clock()
            if self.starts and now < self.starts[-1] + self.min_interval:
                self._sleep(self.starts[-1] + self.min_interval - now)
                now = self._clock()
            self.starts.append(now)


class ProcessLock:
    """An exclusive, non-blocking ``flock``: one holder per path on this machine.

    A second lock on the same path fails, in this process or another.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle: IO[str] | None = None

    def __enter__(self) -> Self:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("w")
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            raise AccessStop(f"another client holds {self.path}") from None
        self._handle = handle
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._handle is not None:
            fcntl.flock(self._handle, fcntl.LOCK_UN)
            self._handle.close()
            self._handle = None


@dataclass(frozen=True)
class Fetched:
    """A validated response body and the record of its retrieval."""

    body: bytes
    retrieval: Retrieval


class PoliteClient:
    """GET under the access policy of A §393-408. Share one instance across workers.

    ``host_allowed`` decides which hosts the client may reach; ``block_markers`` are
    lowercase byte strings whose presence in an HTML body means the server refused
    automated access.
    """

    def __init__(
        self,
        identity: str,
        *,
        throttle: Throttle,
        host_allowed: Callable[[str], bool] = lambda host: True,
        block_markers: Collection[bytes] = (),
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.throttle = throttle
        self._host_allowed = host_allowed
        self._markers = tuple(block_markers)
        self._sleep = sleep
        self._rng = rng or random.Random()
        self._now = now
        self._client = httpx.Client(
            headers={"User-Agent": identity, "Accept-Encoding": "gzip, deflate"},
            timeout=TIMEOUT,
            follow_redirects=True,
            transport=transport,
            event_hooks={"request": [self._before_request]},
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _check_host(self, url: str) -> None:
        host = (urlsplit(url).hostname or "").lower()
        if not self._host_allowed(host):
            raise AccessStop(f"{url} is outside this client's hosts")

    def _before_request(self, request: httpx.Request) -> None:
        """httpx calls this for every request it sends, redirect hops included."""
        self._check_host(str(request.url))
        self.throttle.acquire()

    def get(self, url: str) -> httpx.Response:
        """The response to one GET, after bounded retries on 403, 429, 5xx, and
        transport errors."""
        self._check_host(url)
        forbidden = 0
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self._client.get(url)
            except httpx.TransportError as exc:
                if attempt == MAX_ATTEMPTS:
                    raise AccessStop(
                        f"{type(exc).__name__} after {attempt} attempts: {url}"
                    ) from exc
                self._backoff(attempt, None)
                continue
            if response.status_code == 403:
                forbidden += 1
                if forbidden >= FORBIDDEN_LIMIT:
                    raise AccessStop(
                        f"403 persisted for {url}; stopping without changing identity"
                    )
                self._backoff(attempt, response)
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == MAX_ATTEMPTS:
                    raise AccessStop(
                        f"HTTP {response.status_code} after {attempt} attempts: {url}"
                    )
                self._backoff(attempt, response)
                continue
            return response
        raise AccessStop(f"no response for {url}")

    def fetch(self, url: str, expected_types: Collection[str]) -> Fetched:
        """A 200 response of an expected media type, or ``UnexpectedResponse``.

        A text/html body with a block marker raises ``AccessStop`` whatever was
        expected.
        """
        response = self.get(url)
        content_type = response.headers.get("content-type", "")
        media_type = content_type.split(";")[0].strip().lower()
        body = response.content  # Content-Encoding already decoded; charset untouched
        head = body[:BLOCK_SCAN_BYTES].lower()
        if media_type == "text/html" and any(mark in head for mark in self._markers):
            raise AccessStop(
                f"block or rate-limit page for {url}; stopping without changing"
                " identity"
            )
        if response.status_code != 200:
            raise UnexpectedResponse(f"HTTP {response.status_code} for {url}")
        if media_type not in expected_types:
            raise UnexpectedResponse(
                f"content type {content_type!r} for {url};"
                f" expected {sorted(expected_types)}"
            )
        retrieval = Retrieval(
            request_url=url,
            final_url=str(response.url),
            retrieved_at=self._now(),
            retrieval_method=RetrievalMethod.HTTP,
            http_status=response.status_code,
            media_type=media_type,
            content_type=content_type,
            byte_count=len(body),
            sha256=sha256_hex(body),
        )
        return Fetched(body=body, retrieval=retrieval)

    def _backoff(self, attempt: int, response: httpx.Response | None) -> None:
        delay = min(BACKOFF_CAP_SECONDS, BACKOFF_BASE_SECONDS * 2 ** (attempt - 1))
        delay *= self._rng.uniform(0.5, 1.0)
        header = response.headers.get("retry-after") if response is not None else None
        requested = retry_after_seconds(header, self._now())
        if requested is not None:
            if requested > MAX_RETRY_AFTER_SECONDS:
                raise AccessStop(
                    f"server asked to wait {requested:.0f}s; stopping the run"
                )
            delay = max(delay, requested)
        self._sleep(delay)
