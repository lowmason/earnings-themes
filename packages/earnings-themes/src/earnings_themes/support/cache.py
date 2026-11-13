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
            if _light_material(material, "canonical") is not None:
                # The text is canonical JSON, so its digest is the hash of its bytes.
                value = super().__new__(cls, sha256_hex(material.encode()))
            else:
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


def _check_bundles(bundles) -> None:
    """Validate the ``bundles`` value of one material; any failure is a ValueError."""
    if type(bundles) is not list:
        raise ValueError
    for bundle in bundles:
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


# A key's text is 12 to 13 MB at pilot size, and 99.7% of it is three values that are
# the same in every key of one source. They are checked once per SHA-256 of their text,
# and only the small rest of the key is parsed. The canonical key order puts
# ``bundles`` first and the other two after ``schema_version``.
_FRAGMENT_MEMO_SIZE = 64
"""Fragment checks kept: each is a pair of short strings, and no text is kept."""
_FRAGMENT_NAMES = ("bundles", "source_claims", "source_quotes")
_BUNDLES_START = '{"bundles":'
_CLAIM_MARKER = ',"claim":'
_CLAIMS_MARKER = ',"source_claims":'
_QUOTES_MARKER = ',"source_quotes":'
_RUN_MARKER = ',"source_run":'


def _split_material(material: str) -> tuple[tuple[str, str, str], str] | None:
    """The three big values of a key's text, and the text with each replaced by ``[]``.

    A value is the text strictly between two markers, and a marker is the first one
    after the text before it. A marker can also sit inside a value, and then the value
    is cut short: it is no JSON text, and no check accepts it. ``None`` when a marker
    is missing or out of order.
    """
    if not material.startswith(_BUNDLES_START):
        return None
    bundles_start = len(_BUNDLES_START)
    bundles_end = material.find(_CLAIM_MARKER, bundles_start)
    if bundles_end < 0:
        return None
    claims_marker = material.find(_CLAIMS_MARKER, bundles_end)
    if claims_marker < 0:
        return None
    claims_start = claims_marker + len(_CLAIMS_MARKER)
    claims_end = material.find(_QUOTES_MARKER, claims_start)
    if claims_end < 0:
        return None
    quotes_start = claims_end + len(_QUOTES_MARKER)
    quotes_end = material.find(_RUN_MARKER, quotes_start)
    if quotes_end < 0:
        return None
    fragments = (
        material[bundles_start:bundles_end],
        material[claims_start:claims_end],
        material[quotes_start:quotes_end],
    )
    placeholder = (
        material[:bundles_start]
        + "[]"
        + material[bundles_end:claims_start]
        + "[]"
        + material[claims_end:quotes_start]
        + "[]"
        + material[quotes_end:]
    )
    return fragments, placeholder


def _check_fragment(
    level: Literal["canonical", "valid"],
    name: Literal["bundles", "source_claims", "source_quotes"],
    fragment: str,
) -> None:
    """Check one big value of a key's text; any failure is a ValueError.

    ``canonical``: the text is the canonical JSON of its own parse, and is one value,
    because the whole text is parsed. ``valid`` adds today's checks of the parse: a
    list, and then each bundle, claim or quote record as ``_validate_binding`` does.
    """
    try:
        parsed = json.loads(fragment)
        if canonical_json(parsed) != fragment.encode():
            raise ValueError
        if level == "valid":
            if name == "bundles":
                _check_bundles(parsed)
            else:
                if type(parsed) is not list:
                    raise ValueError
                _check_records_once(Claim if name == "source_claims" else Quote, parsed)
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ValueError from None


_checked_fragments: OrderedDict[tuple[str, str], None] = OrderedDict()
_checked_fragments_lock = threading.Lock()


def _fragment_checked(
    level: Literal["canonical", "valid"],
    name: Literal["bundles", "source_claims", "source_quotes"],
    fragment: str,
) -> None:
    """``_check_fragment``, unless a text of identical content already passed.

    The check is a pure function of the level, the name and the text, and the SHA-256
    of the text fixes it. So a text that differs in one character has another digest
    and is checked in full. The name is part of the key because the ``valid`` check
    differs by name. Only a text that passed is remembered, and no text is kept. The
    lock covers the memo only: two threads may check one text once each.
    """
    memo_key = (f"{level}:{name}", sha256_hex(fragment.encode()))
    with _checked_fragments_lock:
        if memo_key in _checked_fragments:
            _checked_fragments.move_to_end(memo_key)
            return
    _check_fragment(level, name, fragment)
    with _checked_fragments_lock:
        _checked_fragments[memo_key] = None
        while len(_checked_fragments) > _FRAGMENT_MEMO_SIZE:
            _checked_fragments.popitem(last=False)


def _light_material(material: str, level: Literal["canonical", "valid"]) -> dict | None:
    """The parse of a key's small rest, when its text is canonical JSON; else ``None``.

    The rest is the text with its three big values replaced by ``[]``. It is returned
    only if every big value passed its check at ``level``, and the rest is the
    canonical JSON of its own parse. Then the whole text is canonical JSON too.

    Each of the three values must also be the top-level one. A nested key can be named
    like a marker, for example in ``request.reply_schema``, which holds any JSON. The
    split would then take the nested text, and the returned parse would hold ``[]``
    where the key holds a value. So each of the two later markers must occur exactly
    once in the rest, and a top-level key of that name must be there too. Then the one
    occurrence is the top-level one. ``bundles`` needs no count, because it is the
    first key and is read from the start of the text. This only accepts: on any doubt
    the answer is ``None``, and the caller runs today's code, which gives today's
    outcome.
    """
    if type(material) is not str:
        return None
    try:
        split = _split_material(material)
        if split is None:
            return None
        fragments, placeholder = split
        if (
            placeholder.count(_CLAIMS_MARKER) != 1
            or placeholder.count(_QUOTES_MARKER) != 1
        ):
            return None
        for name, fragment in zip(_FRAGMENT_NAMES, fragments, strict=True):
            _fragment_checked(level, name, fragment)
        parsed = json.loads(placeholder)
        if canonical_json(parsed) != placeholder.encode():
            return None
        if type(parsed) is not dict or any(
            parsed.get(name) != [] for name in _FRAGMENT_NAMES
        ):
            return None
        return parsed
    except (ValueError, TypeError, RecursionError):
        return None


def _check_material(material: dict, kind: str, fragments_checked: bool):
    """The typed ``(request, identity)`` of a key's parsed material, or ValueError.

    Every check of ``_validate_binding`` but the two on the text: that it is the
    canonical JSON of its parse, and that its hash is the key. With
    ``fragments_checked`` the three big values are not read, because
    ``_check_fragment`` at level ``valid`` already did the checks on them, and the
    parse holds ``[]`` in their place. Both paths of ``_validate_binding`` call this
    one body, so a check added here applies to both.
    """
    if set(material) != _BINDING_FIELDS:
        raise ValueError
    if (
        material["kind"] != kind
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
        if fragments_checked and name in _FRAGMENT_NAMES:
            continue
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
    if not fragments_checked:
        _check_bundles(material["bundles"])
    request = (ScoreRequest if kind == "scorer" else JudgeRequest).model_validate_json(
        canonical_json(material["request"])
    )
    identity = (
        ScorerIdentity if kind == "scorer" else JudgeIdentity
    ).model_validate_json(canonical_json(material["identity"]))
    return request, identity


def _validate_binding(key_text: str, material_text: str, kind: str):
    """The key's typed ``(request, identity)``, or ``malformed_record``.

    A pure function of its three immutable texts, which is what makes
    ``_binding_once`` exact. A text that is canonical JSON, and is the hash ``key_text``
    names, is checked through its small rest and its three big values' memo. Anything
    else, or any failure on that path, runs the whole text through the checks one
    more time, and that run gives the outcome. So the memo can only skip work on a text
    that passed, and never decides a refusal.
    """
    try:
        light = _light_material(material_text, "valid")
        if light is not None and sha256_hex(material_text.encode()) == key_text:
            return _check_material(light, kind, True)
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
        pass
    try:
        material = json.loads(material_text)
        # As today, a wrong set of fields is refused before the text is dumped.
        if set(material) != _BINDING_FIELDS:
            raise ValueError
        canonical = canonical_json(material)
        if canonical.decode() != material_text or sha256_hex(canonical) != key_text:
            raise ValueError
        return _check_material(material, kind, False)
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
    """The kind a material names, read once per text instead of once per call.

    A canonical text is read through its small rest, and its three big values pass
    the same memo as in the constructor. Any other text is parsed whole, which gives
    today's value or today's error.
    """
    light = _light_material(material_text, "canonical")
    if light is not None and "kind" in light:
        return light["kind"]
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
