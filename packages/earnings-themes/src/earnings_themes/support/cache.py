"""Versioned raw replies, full canonical bindings and sequential atomic writes.

Keys are SHA-256 strings carrying immutable canonical binding material. A bare
hash lacks the expected typed request/identity and is refused. Evidence exactness
is always rechecked by the caller, including after cache hits. No verdict is kept.
"""

import json
import os
import tempfile
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    OverlayMask,
    canonical_json,
    digest,
    sha256_hex,
)
from pydantic import Field, model_validator

from earnings_themes.extraction.adapters import ModelReply
from earnings_themes.extraction.records import Claim, Quote, RunRecord
from earnings_themes.records import Sha256Hex, record_json
from earnings_themes.support.judges import JudgeRequest
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    SUPPORT_SCHEMA_VERSION,
    SUPPORT_VERSION,
    ContextReference,
    EvidenceReference,
    JudgeIdentity,
    ResolvedInput,
    ScorerIdentity,
    SupportPolicy,
    SupportRecord,
    TargetRecord,
)
from earnings_themes.support.resolve import _validated
from earnings_themes.support.scorers import ScoreReply, ScoreRequest


class SupportCacheKey(str):
    """Digest text plus canonical local binding; repr never shows source text."""

    def __new__(cls, material: str):
        try:
            canonical = canonical_json(json.loads(material)).decode()
            if type(material) is not str or canonical != material:
                raise ValueError
            value = super().__new__(cls, digest(json.loads(material)))
            object.__getattribute__(value, "__dict__")["_material"] = material
            return value
        except (ValueError, TypeError, AttributeError):
            raise SupportError("malformed_record") from None

    def __getattribute__(self, name):
        if name == "__dict__":
            return MappingProxyType(object.__getattribute__(self, name))
        return super().__getattribute__(name)

    @property
    def material(self) -> str:
        return self.__dict__["_material"]

    def __setattr__(self, name, value):
        raise AttributeError("immutable_cache_key")


def _key(
    input: ResolvedInput,
    request: ScoreRequest | JudgeRequest,
    identity: ScorerIdentity | JudgeIdentity,
    policy: SupportPolicy,
    kind: Literal["scorer", "judge"],
) -> SupportCacheKey:
    request = _validated(request, ScoreRequest if kind == "scorer" else JudgeRequest)
    identity = _validated(
        identity, ScorerIdentity if kind == "scorer" else JudgeIdentity
    )
    policy = _validated(policy, SupportPolicy)
    # Include the original extraction span locator and full canonical structure,
    # without dereferencing any codebook examples or retaining review outcomes.
    source = input.sources
    bundles = [
        {
            "document": b.document.model_dump(mode="json"),
            "elements": [e.model_dump(mode="json") for e in b.elements],
            "masks": [m.model_dump(mode="json") for m in b.masks],
        }
        for b in source.bundles
    ]
    claims = [c.model_dump(mode="json") for c in source.stored_run.claims]
    quotes = [q.model_dump(mode="json") for q in source.stored_run.quotes]
    material = {
        "kind": kind,
        "schema_version": SUPPORT_SCHEMA_VERSION,
        "support_version": SUPPORT_VERSION,
        "record": input.record.model_dump(mode="json"),
        "evidence": [r.model_dump(mode="json") for r in input.evidence],
        "contexts": [r.model_dump(mode="json") for r in input.contexts],
        "claim": input.claim,
        "provenance_hash": source.provenance_hash,
        "source_run": source.stored_run.record.model_dump(mode="json"),
        "source_claims": claims,
        "source_quotes": quotes,
        "bundles": bundles,
        "request": request.model_dump(mode="json"),
        "identity": identity.model_dump(mode="json"),
        "policy": policy.model_dump(mode="json"),
    }
    key = SupportCacheKey(canonical_json(material).decode())
    SupportCache._binding(key, kind)
    return key


def scorer_key(
    input: ResolvedInput,
    request: ScoreRequest,
    identity: ScorerIdentity,
    policy: SupportPolicy,
) -> SupportCacheKey:
    return _key(input, request, identity, policy, "scorer")


def judge_key(
    input: ResolvedInput,
    request: JudgeRequest,
    identity: JudgeIdentity,
    policy: SupportPolicy,
) -> SupportCacheKey:
    return _key(input, request, identity, policy, "judge")


_REFUSAL_REASONS = frozenset(
    {
        "transport_error",
        "model_mismatch",
        "tool_call_refused",
        "malformed_reply",
        "invalid_references",
    }
)


def _raw_hash(raw, refusal_reason):
    return digest(
        {"reply": raw.model_dump(mode="json"), "refusal_reason": refusal_reason}
    )


class SupportCacheEntry(SupportRecord):
    key: Sha256Hex
    kind: Literal["scorer", "judge"]
    material: str = Field(repr=False)
    request: ScoreRequest | JudgeRequest = Field(repr=False)
    identity: ScorerIdentity | JudgeIdentity = Field(repr=False)
    reply_hash: Sha256Hex
    reply: ScoreReply | ModelReply = Field(repr=False)
    refusal_reason: str | None = None

    @model_validator(mode="after")
    def _closed_refusal(self):
        if self.refusal_reason is not None and (
            self.kind != "judge" or self.refusal_reason not in _REFUSAL_REASONS
        ):
            raise ValueError("invalid_reason")
        return self


class SupportCache:
    """Caller-selected raw artifact directory; no dispatch or import-time I/O."""

    def __init__(self, directory: Path, mode: Literal["live", "replay"]) -> None:
        if mode not in ("live", "replay"):
            raise SupportError("malformed_record")
        self._directory = Path(directory)
        self.mode = mode

    @staticmethod
    def _binding(key: SupportCacheKey, kind: str):
        try:
            if type(key) is not SupportCacheKey or kind not in ("scorer", "judge"):
                raise ValueError
            material = json.loads(key.material)
            expected_fields = {
                "kind",
                "schema_version",
                "support_version",
                "record",
                "evidence",
                "contexts",
                "claim",
                "provenance_hash",
                "source_run",
                "source_claims",
                "source_quotes",
                "bundles",
                "request",
                "identity",
                "policy",
            }
            if set(material) != expected_fields:
                raise ValueError
            if (
                canonical_json(material).decode() != key.material
                or digest(material) != str(key)
                or material["kind"] != kind
                or material["schema_version"] != SUPPORT_SCHEMA_VERSION
                or material["support_version"] != SUPPORT_VERSION
            ):
                raise ValueError
            for name, model in (
                ("record", TargetRecord),
                ("policy", SupportPolicy),
                ("source_run", RunRecord),
            ):
                model.model_validate_json(canonical_json(material[name]))
            for name, model in (
                ("evidence", EvidenceReference),
                ("contexts", ContextReference),
                ("source_claims", Claim),
                ("source_quotes", Quote),
            ):
                if type(material[name]) is not list:
                    raise ValueError
                for record in material[name]:
                    model.model_validate_json(canonical_json(record))
            if type(material["claim"]) is not str or not material["claim"].strip():
                raise ValueError
            provenance = material["provenance_hash"]
            if (
                type(provenance) is not str
                or len(provenance) != 64
                or any(c not in "0123456789abcdef" for c in provenance)
            ):
                raise ValueError
            if type(material["bundles"]) is not list:
                raise ValueError
            for bundle in material["bundles"]:
                if set(bundle) != {"document", "elements", "masks"}:
                    raise ValueError
                CanonicalDocument.model_validate_json(
                    canonical_json(bundle["document"])
                )
                for name, model in (
                    ("elements", DocumentElement),
                    ("masks", OverlayMask),
                ):
                    if type(bundle[name]) is not list:
                        raise ValueError
                    for record in bundle[name]:
                        model.model_validate_json(canonical_json(record))
            request = (
                ScoreRequest if kind == "scorer" else JudgeRequest
            ).model_validate_json(canonical_json(material["request"]))
            identity = (
                ScorerIdentity if kind == "scorer" else JudgeIdentity
            ).model_validate_json(canonical_json(material["identity"]))
            return request, identity
        except (ValueError, TypeError, KeyError, AttributeError):
            raise SupportError("malformed_record") from None

    def artifact_hash(self, reference: str) -> str:
        """Hash a validated local cache artifact by its confined digest filename."""
        try:
            if (
                type(reference) is not str
                or len(reference) != 69
                or not reference.endswith(".json")
                or any(c not in "0123456789abcdef" for c in reference[:64])
            ):
                raise ValueError
            path = self._directory / reference
            if path.is_symlink():
                raise ValueError
            payload = path.read_bytes()
            entry = SupportCacheEntry.model_validate_json(payload)
            key = SupportCacheKey(entry.material)
            if reference != self.raw_ref(key) or self._entry(key, entry.kind) != entry:
                raise ValueError
            return sha256_hex(payload)
        except (OSError, ValueError, TypeError, AttributeError):
            raise SupportError("cache_corrupt") from None

    def raw_ref(self, key: SupportCacheKey) -> str:
        try:
            kind = json.loads(key.material)["kind"]
        except (ValueError, TypeError, KeyError, AttributeError):
            raise SupportError("malformed_record") from None
        self._binding(key, kind)
        return f"{key}.json"

    def _reply(self, key, kind, raw):
        request, identity = self._binding(key, kind)
        if kind == "scorer":
            raw = _validated(raw, ScoreReply)
            if raw.identity != identity:
                raise SupportError("model_mismatch")
            if raw.input_hash != request.input_hash:
                raise SupportError("input_changed")
        else:
            raw = _validated(raw, ModelReply)
            # Wrong-model replies remain auditable unusable attempts. The expected
            # runtime stays bound by the key; parse_answer rejects the raw identity.
        return raw

    def _entry(self, key: SupportCacheKey, kind: Literal["scorer", "judge"]):
        request, identity = self._binding(key, kind)
        path = self._directory / self.raw_ref(key)
        if not path.exists():
            return None
        try:
            entry = SupportCacheEntry.model_validate_json(path.read_bytes())
            if (
                entry.key != str(key)
                or entry.kind != kind
                or entry.material != key.material
                or entry.request != request
                or entry.identity != identity
                or entry.reply_hash != _raw_hash(entry.reply, entry.refusal_reason)
            ):
                raise ValueError
            self._reply(key, kind, entry.reply)
            return entry
        except (OSError, ValueError, TypeError):
            raise SupportError("cache_corrupt") from None

    def lookup(self, key: SupportCacheKey, kind: Literal["scorer", "judge"]):
        entry = self._entry(key, kind)
        return None if entry is None else entry.reply

    def refusal_reason(self, key: SupportCacheKey) -> str | None:
        """Integrity-checked fixed transport refusal, never a semantic verdict."""
        entry = self._entry(key, "judge")
        return None if entry is None else entry.refusal_reason

    def put(
        self,
        key: SupportCacheKey,
        raw: ScoreReply | ModelReply,
        *,
        refusal_reason: str | None = None,
    ) -> str:
        kind = "scorer" if isinstance(raw, ScoreReply) else "judge"
        if refusal_reason is not None and (
            kind != "judge" or refusal_reason not in _REFUSAL_REASONS
        ):
            raise SupportError("malformed_record")
        request, identity = self._binding(key, kind)
        raw = self._reply(key, kind, raw)
        existing = self._entry(key, kind)
        if existing is not None:
            if existing.reply != raw or existing.refusal_reason != refusal_reason:
                raise SupportError("cache_corrupt")
            return self.raw_ref(key)
        entry = SupportCacheEntry(
            key=str(key),
            kind=kind,
            material=key.material,
            request=request,
            identity=identity,
            reply_hash=_raw_hash(raw, refusal_reason),
            reply=raw,
            refusal_reason=refusal_reason,
        )
        partial = None
        storage_failure = None
        try:
            self._directory.mkdir(parents=True, exist_ok=True)
            path = self._directory / self.raw_ref(key)
            with tempfile.NamedTemporaryFile(
                dir=self._directory, prefix=f"{key}.", suffix=".partial", delete=False
            ) as stream:
                partial = Path(stream.name)
                stream.write(record_json(entry))
            os.replace(partial, path)
        except OSError:
            storage_failure = SupportError("storage_corrupt")
        finally:
            if partial is not None:
                try:
                    partial.unlink(missing_ok=True)
                except OSError:
                    if storage_failure is None:
                        storage_failure = SupportError("storage_corrupt")
        if storage_failure is not None:
            raise storage_failure from None
        return self.raw_ref(key)

    def __repr__(self) -> str:
        return f"SupportCache(mode={self.mode})"

    __str__ = __repr__
