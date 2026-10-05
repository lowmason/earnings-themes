"""The R14.6-keyed reply cache, with replay (the Stage 7 spec, §The adapter protocol
and §The cache key).

- **The key.** A record with one field per component: the request's subject, the
  adapter's identity, the parameters, the reply schema's hash, and the hash of the
  request's messages, the exact text the model is sent, which covers the window's
  text, any feedback, and so the attempt. The cache file is named by the key's
  digest.
- **Two modes.** A hit returns the stored reply and calls nothing. In ``replay``, a
  miss is ``replay_miss`` and never a call. In ``live``, a miss calls the inner
  adapter and stores its reply atomically, under a directory the caller supplies.
- **What is stored.** Raw model output, never a verdict: verification always runs
  again over it, so a changed contract never trusts a cached result (A §681). A
  reply that carries tool calls or names another model is never stored, so a
  swapped model is never cached under another model's identity. A stored entry that
  does not read is refused by its file name and fields, never its text (GS13).
"""

import os
from enum import StrEnum
from pathlib import Path

from earnings_core import digest
from pydantic import PositiveInt

from earnings_themes.extraction.adapters import (
    AdapterError,
    ModelAdapter,
    ModelReply,
    ModelRequest,
)
from earnings_themes.extraction.records import (
    AdapterIdentity,
    ExtractionProblem,
    ExtractionRecord,
)
from earnings_themes.records import (
    NonBlank,
    Part,
    Sha256Hex,
    parse,
    read_json,
    record_json,
)


class CacheKey(Part):
    """One field per R14.6 component."""

    doc_id: NonBlank
    canonical_hash: Sha256Hex
    window_id: NonBlank
    unit_ids: tuple[NonBlank, ...]
    adapter_kind: NonBlank
    model_id: NonBlank
    weights_sha256: Sha256Hex | None
    runtime: NonBlank | None
    runtime_version: NonBlank | None
    structured: bool
    temperature: float
    seed: int
    max_tokens: PositiveInt
    window_budget: PositiveInt | None
    claim_limit: PositiveInt
    prompt_sha256: Sha256Hex
    reply_schema_sha256: Sha256Hex
    request_sha256: Sha256Hex
    extractor_version: NonBlank
    validator_version: NonBlank
    codebook_hash: Sha256Hex | None


def cache_key(request: ModelRequest, identity: AdapterIdentity) -> CacheKey:
    """The key of ``request`` sent to the adapter ``identity`` names."""
    return CacheKey(
        **request.subject.model_dump(),
        **identity.model_dump(),
        **request.parameters.model_dump(),
        reply_schema_sha256=digest(request.reply_schema),
        request_sha256=digest(request.model_dump(mode="json", include={"messages"})),
    )


class CacheEntry(ExtractionRecord):
    """One stored reply, under its key."""

    key: CacheKey
    reply: ModelReply


class CacheMode(StrEnum):
    REPLAY = "replay"
    LIVE = "live"


class CachedAdapter:
    """The cache wrapper: an adapter over ``inner``, with ``inner``'s identity. A mode
    given as its value reads as its member, so ``"replay"`` never calls ``inner``,
    and any other value raises ``ValueError`` here."""

    def __init__(
        self, inner: ModelAdapter, directory: Path, mode: CacheMode | str
    ) -> None:
        self._inner = inner
        self._directory = directory
        self._mode = CacheMode(mode)

    @property
    def identity(self) -> AdapterIdentity:
        return self._inner.identity

    def complete(self, request: ModelRequest) -> ModelReply:
        key = cache_key(request, self.identity)
        path = self._directory / f"{digest(key)}.json"
        if path.is_file():
            entry = parse(read_json(path), CacheEntry, path.name)
            if entry.key != key:
                raise ValueError(f"{path.name} holds the entry of another key")
            return entry.reply.model_copy(update={"cached": True})
        if self._mode is CacheMode.REPLAY:
            raise AdapterError(ExtractionProblem.REPLAY_MISS)
        reply = self._inner.complete(request)
        if not reply.tool_calls and reply.model == self.identity.model_id:
            self._directory.mkdir(parents=True, exist_ok=True)
            partial = path.with_suffix(".partial")
            partial.write_bytes(record_json(CacheEntry(key=key, reply=reply)))
            os.replace(partial, path)
        return reply
