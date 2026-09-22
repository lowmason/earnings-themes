"""The Stage 1 live-fetch client (spec: Live-fetch policy).

Every network call in Stage 1 goes through this module: one identity, one throttle
(request starts at least 0.5 s apart, at most ``max_requests`` per run), explicit
timeouts, bounded retries with exponential backoff and jitter, ``Retry-After``
honoured, and a stop on a 403 that persists. Only 200 responses of the expected
content type are saved; an SEC block or rate-limit page is a failure. The identity
is sent as the User-Agent and never written to disk.
"""

from __future__ import annotations

import email.utils
import fcntl
import hashlib
import json
import os
import random
import re
import time
from collections.abc import Callable, Collection
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Self

import httpx

IDENTITY_ENV = "EDGAR_IDENTITY"
MIN_INTERVAL_SECONDS = 0.5  # the project default of 2 requests/second (A §397)
DEFAULT_MAX_REQUESTS = 500
MAX_ATTEMPTS = 4
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_CAP_SECONDS = 60.0
MAX_RETRY_AFTER_SECONDS = 300.0
TIMEOUT = httpx.Timeout(30.0, connect=10.0)
FORBIDDEN_LIMIT = 2  # a 403 on an attempt and again on its retry is "persistent"

_CONTACT = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
_BLOCK_MARKERS = (b"undeclared automated tool", b"request rate threshold exceeded")


class LivePolicyStop(RuntimeError):
    """The run must stop and be reported (identity, budget, persistent 403, retries)."""


class UnexpectedResponse(RuntimeError):
    """A response that must not be saved; the caller may skip the item and continue."""


def require_identity(environ: dict[str, str] | None = None) -> str:
    value = (os.environ if environ is None else environ).get(IDENTITY_ENV, "").strip()
    if len(value.split()) < 2 or not _CONTACT.search(value):
        raise LivePolicyStop(
            f"{IDENTITY_ENV} must be set outside Git to a descriptive User-Agent with a real "
            "contact, such as 'Jane Doe earnings-themes research jane@example.org'"
        )
    return value


class Throttle:
    """Spaces request starts and enforces the per-run request budget."""

    def __init__(
        self,
        *,
        min_interval: float = MIN_INTERVAL_SECONDS,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.min_interval = min_interval
        self.max_requests = max_requests
        self.count = 0
        self._clock = clock
        self._sleep = sleep
        self._last_start: float | None = None

    def acquire(self) -> None:
        if self.count >= self.max_requests:
            raise LivePolicyStop(
                f"request budget of {self.max_requests} reached; rerun to continue"
            )
        now = self._clock()
        if self._last_start is not None and now < self._last_start + self.min_interval:
            self._sleep(self._last_start + self.min_interval - now)
            now = self._clock()
        self._last_start = now
        self.count += 1


class LiveLock:
    """Only one live Stage 1 process runs at a time (an exclusive, non-blocking flock)."""

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
            raise LivePolicyStop(f"another live process holds {self.path}") from None
        self._handle = handle
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._handle is not None:
            fcntl.flock(self._handle, fcntl.LOCK_UN)
            self._handle.close()
            self._handle = None


@dataclass(frozen=True)
class SavedResponse:
    url: str
    retrieved_at: str
    http_status: int
    content_type: str
    bytes: int
    sha256: str


def meta_path(dest: Path) -> Path:
    return dest.with_name(dest.name + ".meta.json")


def read_meta(dest: Path) -> SavedResponse:
    return SavedResponse(**json.loads(meta_path(dest).read_text(encoding="utf-8")))


def retry_after_seconds(value: str | None, now: datetime) -> float | None:
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


class EdgarFetcher:
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
        self.throttle = throttle
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

    def _before_request(self, request: httpx.Request) -> None:
        """httpx calls this for every request it sends, redirect hops included."""
        self.throttle.acquire()

    def close(self) -> None:
        self._client.close()

    def get(self, url: str) -> httpx.Response:
        forbidden = 0
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self._client.get(url)
            except httpx.TransportError as exc:
                if attempt == MAX_ATTEMPTS:
                    raise LivePolicyStop(
                        f"{type(exc).__name__} after {attempt} attempts: {url}"
                    ) from exc
                self._backoff(attempt, None)
                continue
            if response.status_code == 403:
                forbidden += 1
                if forbidden >= FORBIDDEN_LIMIT:
                    raise LivePolicyStop(
                        f"403 persisted for {url}; stopping without changing identity"
                    )
                self._backoff(attempt, response)
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == MAX_ATTEMPTS:
                    raise LivePolicyStop(
                        f"HTTP {response.status_code} after {attempt} attempts: {url}"
                    )
                self._backoff(attempt, response)
                continue
            return response
        raise LivePolicyStop(f"no response for {url}")

    def fetch_and_save(
        self, url: str, dest: Path, expected_types: Collection[str]
    ) -> SavedResponse:
        response = self.get(url)
        content_type = response.headers.get("content-type", "")
        media_type = content_type.split(";")[0].strip().lower()
        if response.status_code != 200:
            raise UnexpectedResponse(f"HTTP {response.status_code} for {url}")
        if media_type not in expected_types:
            raise UnexpectedResponse(
                f"content type {content_type!r} for {url}; expected {sorted(expected_types)}"
            )
        body = response.content  # Content-Encoding already decoded; charset untouched
        if media_type == "text/html" and any(
            marker in body[:20000].lower() for marker in _BLOCK_MARKERS
        ):
            raise UnexpectedResponse(f"SEC block or rate-limit page for {url}")
        saved = SavedResponse(
            url=str(response.url),
            retrieved_at=self._now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            http_status=response.status_code,
            content_type=content_type,
            bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
        )
        _write_atomic(dest, body)
        _write_atomic(
            meta_path(dest),
            (json.dumps(asdict(saved), indent=2, sort_keys=True) + "\n").encode(),
        )
        return saved

    def _backoff(self, attempt: int, response: httpx.Response | None) -> None:
        delay = min(BACKOFF_CAP_SECONDS, BACKOFF_BASE_SECONDS * 2 ** (attempt - 1))
        delay *= self._rng.uniform(0.5, 1.0)
        header = response.headers.get("retry-after") if response is not None else None
        requested = retry_after_seconds(header, self._now())
        if requested is not None:
            if requested > MAX_RETRY_AFTER_SECONDS:
                raise LivePolicyStop(
                    f"server asked to wait {requested:.0f}s; stopping the run"
                )
            delay = max(delay, requested)
        self._sleep(delay)


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
