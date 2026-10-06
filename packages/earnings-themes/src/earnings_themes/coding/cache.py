"""Coding-only raw responses and counted input; immutable sequential publication."""

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Literal

from earnings_core import canonical_json, digest, sha256_hex
from pydantic import Field

from earnings_themes.coding.records import (
    CODING_SCHEMA_VERSION,
    CODING_VERSION,
    CodingError,
    CodingRecord,
    CodingRequest,
    checked,
)
from earnings_themes.extraction.adapters import ModelReply
from earnings_themes.records import Sha256Hex
from earnings_themes.support.records import JudgeIdentity

RawRefusal = Literal["transport_error", "model_mismatch", "tool_call_refused"]
ARTIFACT_REFERENCE = re.compile(r"[0-9a-f]{64}\.json\Z")


def coding_key(request: CodingRequest, identity: JudgeIdentity) -> str:
    """Strict complete request/runtime binding; no accepted decision is included."""
    request = checked(request, CodingRequest)
    identity = checked(identity, JudgeIdentity)
    return digest(
        {
            "coding_schema": CODING_SCHEMA_VERSION,
            "coding_version": CODING_VERSION,
            "request": request.model_dump(mode="json"),
            "identity": identity.model_dump(mode="json"),
        }
    )


def raw_reply_hash(
    reply: ModelReply, refusal_reason: RawRefusal | None, input_tokens: int
) -> str:
    if (
        type(input_tokens) is not int
        or input_tokens < 0
        or (
            refusal_reason is not None
            and (
                type(refusal_reason) is not str
                or refusal_reason
                not in ("transport_error", "model_mismatch", "tool_call_refused")
            )
        )
    ):
        raise CodingError("malformed_record")
    return digest(
        {
            "reply": checked(reply, ModelReply).model_dump(mode="json"),
            "refusal_reason": refusal_reason,
            "input_tokens": input_tokens,
        }
    )


class CodingCacheEntry(CodingRecord):
    key: Sha256Hex
    request: CodingRequest = Field(repr=False)
    identity: JudgeIdentity = Field(repr=False)
    input_tokens: int = Field(ge=0)
    reply: ModelReply = Field(repr=False)
    reply_hash: Sha256Hex
    refusal_reason: RawRefusal | None = None


class CodingCache:
    """Caller-selected local directory; no dispatch, startup I/O or fresh bypass."""

    def __init__(self, directory: Path, mode: Literal["live", "replay"]) -> None:
        if type(mode) is not str or mode not in ("live", "replay"):
            raise CodingError("malformed_record")
        self._directory = Path(directory)
        self.mode = mode

    def _read(self, reference: str) -> tuple[CodingCacheEntry, bytes] | None:
        if type(reference) is not str or not ARTIFACT_REFERENCE.fullmatch(reference):
            raise CodingError("cache_corrupt")
        path = self._directory / reference
        try:
            if path.is_symlink():
                raise CodingError("cache_corrupt")
            payload = path.read_bytes()
        except FileNotFoundError:
            return None
        except OSError:
            raise CodingError("cache_corrupt") from None
        try:
            entry = checked(json.loads(payload), CodingCacheEntry)
            if (
                reference != f"{entry.key}.json"
                or entry.key != coding_key(entry.request, entry.identity)
                or entry.reply_hash
                != raw_reply_hash(entry.reply, entry.refusal_reason, entry.input_tokens)
            ):
                raise CodingError("cache_corrupt")
            return entry, payload
        except (ValueError, TypeError, OverflowError):
            raise CodingError("cache_corrupt") from None

    def get(
        self, request: CodingRequest, identity: JudgeIdentity
    ) -> CodingCacheEntry | None:
        request = checked(request, CodingRequest)
        identity = checked(identity, JudgeIdentity)
        found = self._read(f"{coding_key(request, identity)}.json")
        if found is None:
            return None
        entry, _ = found
        if entry.request.model_dump(mode="json") != request.model_dump(
            mode="json"
        ) or entry.identity.model_dump(mode="json") != identity.model_dump(mode="json"):
            raise CodingError("cache_corrupt")
        return entry

    def put(
        self,
        request: CodingRequest,
        identity: JudgeIdentity,
        reply: ModelReply,
        *,
        input_tokens: int,
        refusal_reason: RawRefusal | None = None,
    ) -> str:
        request = checked(request, CodingRequest)
        identity = checked(identity, JudgeIdentity)
        reply = checked(reply, ModelReply)
        key = coding_key(request, identity)
        entry = checked(
            {
                "key": key,
                "request": request.model_dump(mode="json"),
                "identity": identity.model_dump(mode="json"),
                "reply": reply.model_dump(mode="json"),
                "input_tokens": input_tokens,
                "refusal_reason": refusal_reason,
                "reply_hash": raw_reply_hash(reply, refusal_reason, input_tokens),
            },
            CodingCacheEntry,
        )
        reference = f"{key}.json"
        existing = self.get(request, identity)
        if existing is not None:
            if canonical_json(existing.model_dump(mode="json")) != canonical_json(
                entry.model_dump(mode="json")
            ):
                raise CodingError("cache_corrupt")
            return reference
        partial = None
        failure = None
        try:
            self._directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=self._directory, prefix=f"{key}.", suffix=".partial", delete=False
            ) as stream:
                partial = Path(stream.name)
                stream.write(canonical_json(entry.model_dump(mode="json")))
            try:
                os.link(partial, self._directory / reference)
            except FileExistsError:
                existing = self.get(request, identity)
                if existing is None or canonical_json(
                    existing.model_dump(mode="json")
                ) != canonical_json(entry.model_dump(mode="json")):
                    raise CodingError("cache_corrupt") from None
        except CodingError as error:
            failure = error
        except OSError:
            failure = CodingError("storage_corrupt")
        finally:
            if partial is not None:
                try:
                    partial.unlink(missing_ok=True)
                except OSError:
                    if failure is None:
                        failure = CodingError("storage_corrupt")
        if failure is not None:
            raise failure from None
        return reference

    def artifact_hash(self, reference: str) -> str:
        """Hash bytes only after exact-reference and complete entry validation."""
        found = self._read(reference)
        if found is None:
            raise CodingError("cache_corrupt")
        _, payload = found
        return sha256_hex(payload)

    def __repr__(self) -> str:
        return f"CodingCache(mode={self.mode})"

    __str__ = __repr__
