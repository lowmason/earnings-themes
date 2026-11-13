"""Versioned raw replies, full canonical bindings and sequential atomic writes.

Keys are SHA-256 strings carrying immutable canonical binding material. A bare
hash lacks the expected typed request/identity and is refused. Evidence exactness
is always rechecked by the caller, including after cache hits. No verdict is kept.
"""

import json
import os
import tempfile
import threading
from collections import OrderedDict
from functools import lru_cache
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
from earnings_themes.extraction.cache import cache_directory
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


_BINDING_MEMO_SIZE = 8
"""Bindings kept: each holds one key's text, which is about 13 MB at pilot size."""
_RECORD_MEMO_SIZE = 512
"""Record lists kept: a source holds two per document, and each entry is a digest."""
_BINDING_FIELDS = frozenset(
    {
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
)


def _check_records(model, records: list) -> None:
    """Validate each record of one list as ``model``; any failure is a ValueError."""
    for record in records:
        model.model_validate_json(canonical_json(record))


_checked_records: OrderedDict[tuple[str, str], None] = OrderedDict()
_checked_records_lock = threading.Lock()


def _check_records_once(model, records: list) -> None:
    """Validate one record list, unless a list of identical content already passed.

    Validation is a pure function of each record's canonical JSON, and the digest of
    the list fixes every one of those texts. So a list that differs in any element has
    another digest and is validated in full. Only a list that passed is remembered.
    """
    memo_key = (f"{model.__module__}.{model.__qualname__}", digest(records))
    with _checked_records_lock:
        if memo_key in _checked_records:
            _checked_records.move_to_end(memo_key)
            return
    _check_records(model, records)
    with _checked_records_lock:
        _checked_records[memo_key] = None
        while len(_checked_records) > _RECORD_MEMO_SIZE:
            _checked_records.popitem(last=False)


def _validate_binding(key_text: str, material_text: str, kind: str):
    """The key's typed ``(request, identity)``, or ``malformed_record``.

    A pure function of its three immutable texts, which is what makes
    ``_binding_once`` exact.
    """
    try:
        material = json.loads(material_text)
        if set(material) != _BINDING_FIELDS:
            raise ValueError
        canonical = canonical_json(material)
        if (
            canonical.decode() != material_text
            or sha256_hex(canonical) != key_text
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
            _check_records_once(model, material[name])
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
            CanonicalDocument.model_validate_json(canonical_json(bundle["document"]))
            for name, model in (
                ("elements", DocumentElement),
                ("masks", OverlayMask),
            ):
                if type(bundle[name]) is not list:
                    raise ValueError
                _check_records_once(model, bundle[name])
        request = (
            ScoreRequest if kind == "scorer" else JudgeRequest
        ).model_validate_json(canonical_json(material["request"]))
        identity = (
            ScorerIdentity if kind == "scorer" else JudgeIdentity
        ).model_validate_json(canonical_json(material["identity"]))
        return request, identity
    except (ValueError, TypeError, KeyError, AttributeError):
        raise SupportError("malformed_record") from None


@lru_cache(maxsize=_BINDING_MEMO_SIZE)
def _binding_once(key_text: str, material_text: str, kind: str):
    """``_validate_binding``, remembered by the exact text it was given.

    A change to any text is a different key, so it is validated anew. A call that
    raises is not remembered, so a refusal is never served as success.
    """
    return _validate_binding(key_text, material_text, kind)


@lru_cache(maxsize=_BINDING_MEMO_SIZE)
def _material_kind(material_text: str):
    """The kind a material names, parsed once per text instead of once per call."""
    return json.loads(material_text)["kind"]


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


def _checked_reply(request, identity, kind, raw):
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


def _check_entry(entry, key, kind) -> None:
    """Every check a stored entry must pass against its key; a failure raises."""
    request, identity = SupportCache._binding(key, kind)
    if (
        entry.key != str(key)
        or entry.kind != kind
        or entry.material != key.material
        or entry.request != request
        or entry.identity != identity
        or entry.reply_hash != _raw_hash(entry.reply, entry.refusal_reason)
    ):
        raise ValueError
    _checked_reply(request, identity, kind, entry.reply)


def _read_entry(path, key, kind):
    """Read an entry's bytes once, parse them and run every check; else cache_corrupt."""
    try:
        entry = SupportCacheEntry.model_validate_json(path.read_bytes())
        _check_entry(entry, key, kind)
        return entry
    except (OSError, ValueError, TypeError):
        raise SupportError("cache_corrupt") from None


class SupportCache:
    """Caller-selected raw artifact directory, or under ``fresh`` its stability
    run's own (A1); no dispatch or import-time I/O."""

    def __init__(
        self,
        directory: Path,
        mode: Literal["live", "replay", "fresh"],
        *,
        stability_run_id: str | None = None,
    ) -> None:
        try:
            member, self._directory = cache_directory(
                Path(directory), mode, stability_run_id
            )
        except ValueError:
            raise SupportError("malformed_record") from None
        self.mode = member.value
        self._stability_run_id = stability_run_id

    @property
    def stability_run_id(self) -> str | None:
        return self._stability_run_id

    @staticmethod
    def _binding(key: SupportCacheKey, kind: str):
        try:
            if type(key) is not SupportCacheKey or kind not in ("scorer", "judge"):
                raise ValueError
            request, identity = _binding_once(str(key), key.material, kind)
        except (ValueError, TypeError, KeyError, AttributeError):
            raise SupportError("malformed_record") from None
        # The models are frozen, but a judge request holds a schema dict. A copy
        # keeps one caller from changing the value the memo serves to the next.
        return request.model_copy(deep=True), identity

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
            if reference != self.raw_ref(key):
                raise ValueError
            _check_entry(entry, key, entry.kind)
            return sha256_hex(payload)
        except (OSError, ValueError, TypeError, AttributeError):
            raise SupportError("cache_corrupt") from None

    def raw_ref(self, key: SupportCacheKey) -> str:
        try:
            kind = _material_kind(key.material)
        except (ValueError, TypeError, KeyError, AttributeError):
            raise SupportError("malformed_record") from None
        self._binding(key, kind)
        return f"{key}.json"

    def _reply(self, key, kind, raw):
        request, identity = self._binding(key, kind)
        return _checked_reply(request, identity, kind, raw)

    def _entry(self, key: SupportCacheKey, kind: Literal["scorer", "judge"]):
        # A bad key or kind is refused before the file is looked for.
        self._binding(key, kind)
        path = self._directory / self.raw_ref(key)
        if not path.exists():
            return None
        return _read_entry(path, key, kind)

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
