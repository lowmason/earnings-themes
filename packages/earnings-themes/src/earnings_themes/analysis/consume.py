"""Rebind current analytical inputs without inference or implicit artifact lookup.

Application validation owns original ingestion-to-projection derivation. This
boundary independently checks C2 projections, supplied canonical bytes, and the
provenance digest already bound by extraction's support/coding consumers.
"""

import json
from collections import Counter
from dataclasses import fields, replace

from earnings_core import (
    ArtifactRef,
    CanonicalDocument,
    DocumentElement,
    OverlayMask,
    TextSpan,
    apply_masks,
    canonical_json,
    digest,
    sha256_hex,
)
from pydantic import BaseModel

from earnings_themes.anchoring import Bundle, bundle_problems, mask_id
from earnings_themes.codebook import Codebook, CodebookStatus, _structure, codebook_hash
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.decide import DecisionSet, support_run_hash
from earnings_themes.coding.records import CodingRun, PolicyReference
from earnings_themes.coding.store import reverify_coding_run
from earnings_themes.extraction import validate_stored_run
from earnings_themes.extraction.store import StoredRun, refused_quotes
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.records import FileHash, StoredSupportRun, SupportSources
from earnings_themes.support.store import reverify_support_run

from .problems import AnalysisError
from .records import (
    AcquisitionStatus,
    AnalysisInputs,
    AnalysisPolicy,
    BoundAnalysis,
    CanonicalSnapshot,
    DocumentMetadata,
    ExpectedEvent,
    FixtureAuthorization,
    RawCacheInputs,
    RawCacheVerification,
    RawSnapshot,
)


def _require(condition: bool) -> None:
    if not condition:
        raise AnalysisError("input_changed")


def _fresh[M: BaseModel](value: M, model: type[M]) -> M:
    _require(type(value) is model)
    return model.model_validate_json(
        canonical_json(value.model_dump(mode="python", warnings=False))
    )


def _stored_fresh(value, model):
    _require(type(value) is model)
    rows = {}
    for field in fields(model):
        given = getattr(value, field.name)
        if field.name == "record":
            _require(isinstance(given, BaseModel))
            rows[field.name] = _fresh(given, type(given))
        else:
            _require(type(given) is tuple)
            _require(all(isinstance(row, BaseModel) for row in given))
            rows[field.name] = tuple(_fresh(row, type(row)) for row in given)
    return model(**rows)


def strict_analysis_inputs(inputs: AnalysisInputs) -> AnalysisInputs:
    """Reconstruct strict contracts; retain only the explicitly injected policy/cache."""
    _require(type(inputs) is AnalysisInputs)
    # Re-run container identity/uniqueness checks even on forged frozen instances.
    replace(inputs)
    sources = inputs.sources
    _require(type(sources) is SupportSources and type(sources.bundles) is tuple)
    bundles = []
    for bundle in sources.bundles:
        _require(type(bundle) is Bundle)
        _require(type(bundle.elements) is tuple and type(bundle.masks) is tuple)
        _require(type(bundle.name) is str and bool(bundle.name.strip()))
        bundles.append(
            Bundle(
                bundle.name,
                _fresh(bundle.document, CanonicalDocument),
                tuple(_fresh(e, DocumentElement) for e in bundle.elements),
                tuple(_fresh(m, OverlayMask) for m in bundle.masks),
            )
        )
    sources = replace(
        sources,
        stored_run=validate_stored_run(sources.stored_run),
        codebook=_fresh(sources.codebook, Codebook),
        bundles=tuple(bundles),
    )
    material = {}
    for name in (
        "expected",
        "acquisition",
        "metadata",
        "copies",
        "no_theme",
        "raw_verification",
    ):
        material[name] = tuple(_fresh(row, type(row)) for row in getattr(inputs, name))
    _require(type(inputs.raw_caches) is RawCacheInputs)
    _require(
        inputs.raw_caches.coding is None
        or type(inputs.raw_caches.coding) is CodingCache
    )
    _require(
        inputs.raw_caches.support is None
        or type(inputs.raw_caches.support) is SupportCache
    )
    snapshots = tuple(
        RawSnapshot(s.doc_id, _fresh(s.artifact, ArtifactRef), s.data)
        for s in inputs.raw_snapshots
    )
    authorization = inputs.fixture_authorization
    if authorization is not None:
        authorization = FixtureAuthorization(
            **{
                f.name: getattr(authorization, f.name)
                for f in fields(FixtureAuthorization)
            }
        )
    return replace(
        inputs,
        sources=sources,
        support=_stored_fresh(inputs.support, StoredSupportRun),
        coding=_stored_fresh(inputs.coding, CodingRun),
        raw_snapshots=snapshots,
        canonical_snapshots=tuple(
            CanonicalSnapshot(s.doc_id, s.data) for s in inputs.canonical_snapshots
        ),
        analysis_policy=_fresh(inputs.analysis_policy, AnalysisPolicy),
        fixture_authorization=authorization,
        **material,
    )


def analysis_provenance_hash(
    *,
    expected: tuple[ExpectedEvent, ...],
    acquisition: tuple[AcquisitionStatus, ...],
    metadata: tuple[DocumentMetadata, ...],
    canonical_snapshots: tuple[CanonicalSnapshot, ...],
) -> str:
    """C2 current-projection digest; no policy/declaration cycle or external lookup."""
    return digest(
        {
            "expected": [
                r.model_dump(mode="json")
                for r in sorted(expected, key=lambda r: r.event_id)
            ],
            "acquisition": [
                r.model_dump(mode="json")
                for r in sorted(acquisition, key=lambda r: r.document_id)
            ],
            "metadata": [
                r.model_dump(mode="json")
                for r in sorted(metadata, key=lambda r: r.doc_id)
            ],
            "canonical_artifacts": [
                {"doc_id": s.doc_id, "sha256": sha256_hex(s.data)}
                for s in sorted(canonical_snapshots, key=lambda s: s.doc_id)
            ],
        }
    )


def _decode_canonical(snapshot: CanonicalSnapshot):
    # Reject duplicate JSON members instead of accepting last-member replacement.
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result)
            result[key] = value
        return result

    data = json.loads(snapshot.data, object_pairs_hook=unique)
    _require(
        type(data) is dict
        and set(data) == {"document", "elements", "manifest", "masks"}
    )
    _require(type(data["elements"]) is list and type(data["masks"]) is list)
    document = CanonicalDocument.model_validate_json(canonical_json(data["document"]))
    elements = tuple(
        DocumentElement.model_validate_json(canonical_json(e)) for e in data["elements"]
    )
    masks = tuple(
        OverlayMask.model_validate_json(canonical_json(m)) for m in data["masks"]
    )
    _require(document.doc_id == snapshot.doc_id)
    return data, document, elements, masks


def _verify_canonical(snapshot, bundle, metadata, policy):
    data, document, elements, masks = _decode_canonical(snapshot)
    _require(
        (document, elements, masks) == (bundle.document, bundle.elements, bundle.masks)
    )
    manifest = data["manifest"]
    _require(type(manifest) is dict)
    # The application validates the full ingestion schema; these are the current
    # source/structure/policy bindings owned by this analytical consumption gate.
    _require(
        type(manifest.get("schema_version")) is int and manifest["schema_version"] == 1
    )
    for field, expected in (
        ("source_document_id", document.source_document_id),
        ("canonicalization_version", document.canonicalization_version),
        ("raw_sha256", metadata.raw_hash),
        ("mask_policy_id", metadata.mask_policy_id),
        ("mask_policy_version", metadata.mask_policy_version),
        ("element_counts", dict(Counter(e.type.value for e in elements))),
    ):
        _require(manifest.get(field) == expected)
    _require(type(manifest.get("element_counts")) is dict)
    _require(
        all(type(n) is int and n >= 0 for n in manifest["element_counts"].values())
    )
    _require(
        type(manifest.get("mask_count")) is int and manifest["mask_count"] == len(masks)
    )
    _require(type(manifest.get("raw_bytes")) is int and manifest["raw_bytes"] >= 0)
    _require(
        (metadata.mask_policy_id, metadata.mask_policy_version)
        == (policy.mask_policy_id, policy.mask_policy_version)
    )
    apply_masks(
        document,
        masks,
        policy_id=policy.mask_policy_id,
        policy_version=policy.mask_policy_version,
    )
    _require(not bundle_problems(bundle))
    _require(metadata.canonical_manifest_hash == digest(manifest))
    _require(
        metadata.mask_manifest_hash
        == digest(
            {
                "doc_id": document.doc_id,
                "canonical_hash": document.canonical_hash,
                "mask_policy_id": manifest["mask_policy_id"],
                "mask_policy_version": manifest["mask_policy_version"],
                "masks": data["masks"],
            }
        )
    )
    return manifest


def _verify_book(book):
    _require(book.status is CodebookStatus.APPROVED and book.approval is not None)
    _require(book.content_hash == codebook_hash(book))
    # The shipped pure structure gate never resolves example pointers. The full
    # validate_codebook consumer is unsuitable here because it loads examples.
    _require(not _structure(book.themes))


def verify_current_inventory(inputs: AnalysisInputs, extraction: StoredRun) -> None:
    """Bind every selected source, including sources with no quotes or targets."""
    bundles = {b.document.doc_id: b for b in inputs.sources.bundles}
    metadata = {m.doc_id: m for m in inputs.metadata}
    snapshots = {s.doc_id: s for s in inputs.canonical_snapshots}
    _require(len(bundles) == len(inputs.sources.bundles))
    _require(
        set(bundles)
        == set(metadata)
        == set(snapshots)
        == set(extraction.record.documents)
    )
    _require(
        extraction.record.documents
        == {d: b.document.canonical_hash for d, b in bundles.items()}
    )
    policy = inputs.analysis_policy
    _require(policy.event_ids == tuple(sorted(e.event_id for e in inputs.expected)))
    _require(all(e.pilot_hash == policy.population_hash for e in inputs.expected))
    _require(all(a.event_id in policy.event_ids for a in inputs.acquisition))
    _require(
        {a.doc_id for a in inputs.acquisition if a.doc_id is not None} == set(bundles)
    )
    actual_provenance = analysis_provenance_hash(
        expected=inputs.expected,
        acquisition=inputs.acquisition,
        metadata=inputs.metadata,
        canonical_snapshots=inputs.canonical_snapshots,
    )
    _require(
        actual_provenance == inputs.provenance_hash == inputs.sources.provenance_hash
    )
    authorization = inputs.fixture_authorization
    if policy.scope == "fixture":
        _require(authorization is not None)
        _require(policy.population_id == authorization.corpus_id)
        _require(
            authorization.pilot_hash == policy.population_hash
            and authorization.provenance_hash == actual_provenance
        )
        _require(
            all(
                e.event_manifest_hash == authorization.event_manifest_hash
                and e.pilot_hash == authorization.pilot_hash
                for e in inputs.expected
            )
        )
        _require(
            all(a.pilot_hash == authorization.pilot_hash for a in inputs.acquisition)
        )
    else:
        _require(authorization is None)
        _require(
            inputs.coding.record.policy is None
            or inputs.coding.record.policy.kind != "fixture"
        )
    _verify_book(inputs.sources.codebook)
    for doc_id, bundle in bundles.items():
        row = metadata[doc_id]
        manifest = _verify_canonical(snapshots[doc_id], bundle, row, policy)
        acquired = next(a for a in inputs.acquisition if a.doc_id == doc_id)
        _require(acquired.retrieved_at == row.retrieved_at)
        raw = next((s for s in inputs.raw_snapshots if s.doc_id == doc_id), None)
        if raw is not None:
            _require(row.retain_raw and row.access_status == "available")
            _require(
                raw.artifact == row.raw_artifact
                and raw.artifact.content_sha256 == row.raw_hash
            )
            _require(
                raw.artifact.rights_status == row.rights_status
                and raw.artifact.rights_basis == row.rights_basis
            )
            if not raw.artifact.matches(raw.data):
                raise AnalysisError("storage_corrupt")
            _require(len(raw.data) == manifest["raw_bytes"])
    reference = inputs.coding.record.policy
    try:
        actual_reference = (
            _fresh(inputs.assignment_policy.reference, PolicyReference)
            if inputs.assignment_policy is not None
            else None
        )
    except Exception:  # noqa: BLE001 - foreign properties may carry arbitrary causes
        raise AnalysisError("input_changed") from None
    _require(reference == actual_reference)
    if actual_reference is not None:
        _require(actual_reference.kind != "fixture" or policy.scope == "fixture")
    source_hash = digest(
        {
            "record": extraction.record.model_dump(mode="json"),
            "provenance_hash": actual_provenance,
        }
    )
    coding_hash = digest(inputs.coding.record.model_dump(mode="json"))
    support_hash = support_run_hash(inputs.support)
    for declaration in inputs.no_theme:
        _require(declaration.doc_id in metadata)
        _require(
            declaration.canonical_hash == metadata[declaration.doc_id].canonical_hash
        )
        _require(
            (
                declaration.source_run_hash,
                declaration.coding_run_hash,
                declaration.support_run_hash,
            )
            == (source_hash, coding_hash, support_hash)
        )
        _require(declaration.codebook == inputs.coding.record.codebook)
        _require(declaration.analysis_policy_hash == policy.content_hash)
        _require(
            declaration.assignment_policy == actual_reference
            and declaration.policy_scope == policy.scope
        )


def verify_original_links_and_masks(
    inputs: AnalysisInputs, extraction: StoredRun
) -> None:
    """Check all original quotes/links before filtering any assignment evidence."""
    _require(not refused_quotes(extraction, inputs.sources.bundles))
    bundles = {b.document.doc_id: b for b in inputs.sources.bundles}
    quotes = {(q.span.doc_id, q.quote_id): q for q in extraction.quotes}
    for quote in extraction.quotes:
        bundle = bundles[quote.span.doc_id]
        span = TextSpan(start=quote.span.start, end=quote.span.end)
        current_masks = tuple(
            sorted(mask_id(m) for m in bundle.masks if m.span.overlaps(span))
        )
        _require(quote.mask_ids == current_masks)
    for claim in extraction.claims:
        _require(all((claim.doc_id, q) in quotes for q in claim.quote_ids))


def _cache_verification(inputs):
    statuses = [
        RawCacheVerification(
            stage="extraction",
            status="not_bound",
            bindings=(),
            method="schema-1-no-raw-bindings",
            version="1",
        )
    ]
    for stage, cache, bindings in (
        (
            "classifier",
            inputs.raw_caches.coding,
            tuple(
                (name[4:], h)
                for name, h in inputs.coding.record.artifact_hashes
                if name.startswith("raw/")
            ),
        ),
        (
            "judge",
            inputs.raw_caches.support,
            tuple(
                (name[4:], h)
                for name, h in inputs.support.record.artifact_hashes
                if name.startswith("raw/")
            ),
        ),
    ):
        checked = {}
        if cache is not None:
            try:
                for reference, expected in bindings:
                    if cache.artifact_hash(reference) != expected:
                        raise AnalysisError("storage_corrupt")
                    checked[reference] = expected
            except Exception:  # noqa: BLE001 - external cache diagnostics are opaque
                raise AnalysisError("storage_corrupt") from None
        statuses.append(
            RawCacheVerification(
                stage=stage,
                status="not_supplied" if cache is None else "verified",
                bindings=tuple(
                    FileHash(relative_path=r, sha256=h)
                    for r, h in sorted(checked.items())
                ),
                method="artifact-hash"
                if cache is not None
                else "explicit-cache-absent",
                version="1",
            )
        )
    # Schema 1 support publishes judge raw hashes, not scorer raw-cache hashes.
    statuses.append(
        RawCacheVerification(
            stage="scorer",
            status="not_supplied" if inputs.raw_caches.support is None else "not_bound",
            bindings=(),
            method="schema-1-no-scorer-raw-bindings",
            version="1",
        )
    )
    return tuple(sorted(statuses, key=lambda s: s.stage))


def _binding_material(inputs):
    def stored(value):
        return {
            f.name: (
                getattr(value, f.name).model_dump(mode="json")
                if f.name == "record"
                else [r.model_dump(mode="json") for r in getattr(value, f.name)]
            )
            for f in fields(type(value))
        }

    return {
        "provenance_hash": inputs.provenance_hash,
        "analysis_policy": inputs.analysis_policy.model_dump(mode="json"),
        "source": stored(inputs.sources.stored_run),
        "book": inputs.sources.codebook.model_dump(mode="json"),
        "support": stored(inputs.support),
        "coding": stored(inputs.coding),
        "copies": [c.model_dump(mode="json") for c in inputs.copies],
        "no_theme": [d.model_dump(mode="json") for d in inputs.no_theme],
        "raw": [
            {
                "doc_id": s.doc_id,
                "artifact": s.artifact.model_dump(mode="json"),
                "sha256": sha256_hex(s.data),
            }
            for s in inputs.raw_snapshots
        ],
        "raw_verification": [
            r.model_dump(mode="json") for r in inputs.raw_verification
        ],
    }


def bind_checked_analysis(
    inputs: AnalysisInputs, decisions: DecisionSet
) -> BoundAnalysis:
    """Retain checked references and compute a content binding, never a valid flag."""
    return BoundAnalysis(
        inputs,
        decisions,
        inputs.expected,
        inputs.acquisition,
        inputs.metadata,
        inputs.copies,
        (),
        digest(_binding_material(inputs)),
    )


def reverify_analysis_inputs(inputs: AnalysisInputs) -> BoundAnalysis:
    """Fail closed before analysis, and repeat all bindings after policy callbacks."""
    try:
        checked = strict_analysis_inputs(inputs)
        extraction = checked.sources.stored_run
        verify_current_inventory(checked, extraction)
        verify_original_links_and_masks(checked, extraction)
        checked = replace(checked, raw_verification=_cache_verification(checked))
        before = digest(_binding_material(checked))
        reverify_support_run(checked.support, checked.sources)
        decisions = reverify_coding_run(
            checked.coding, checked.sources, checked.support, checked.assignment_policy
        )
        # Reconstruct original caller references too: callbacks can mutate them,
        # even when the detached checked records themselves remain immutable.
        current = strict_analysis_inputs(inputs)
        verify_current_inventory(current, current.sources.stored_run)
        verify_original_links_and_masks(current, current.sources.stored_run)
        current = replace(current, raw_verification=_cache_verification(current))
        _require(digest(_binding_material(current)) == before)
        verify_current_inventory(checked, extraction)
        verify_original_links_and_masks(checked, extraction)
        _require(_cache_verification(checked) == checked.raw_verification)
        _require(digest(_binding_material(checked)) == before)
        return bind_checked_analysis(checked, decisions)
    except AnalysisError:
        raise
    except Exception:  # noqa: BLE001 - suppress arbitrary model/policy/source errors
        raise AnalysisError("input_changed") from None
