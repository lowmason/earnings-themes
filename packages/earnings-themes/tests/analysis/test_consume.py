"""Current-input consumption over invented, real upstream fixture runs only."""

from dataclasses import replace

import pytest
from earnings_themes.analysis import AnalysisError


def gate(inputs):
    from earnings_themes.analysis import reverify_analysis_inputs

    return reverify_analysis_inputs(inputs)


def test_current_roundtripped_inputs_bind(analysis_inputs):
    bound = gate(analysis_inputs)
    assert bound.metadata == analysis_inputs.metadata
    assert len(bound.binding_hash) == 64
    assert len(bound.decisions.decisions) == 2


def test_changed_canonical_source_refuses(analysis_inputs):
    source = analysis_inputs.sources
    bundle = source.bundles[0]
    document = bundle.document.model_copy(
        update={"canonical_text": bundle.document.canonical_text + "!"}
    )
    changed = replace(
        analysis_inputs,
        sources=replace(source, bundles=(replace(bundle, document=document),)),
    )
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(changed)


def test_every_original_link_refuses_staleness(analysis_inputs):
    source = analysis_inputs.sources
    stored = source.stored_run
    claim = stored.claims[0].model_copy(update={"quote_ids": ("invented-absent",)})
    changed = replace(
        analysis_inputs,
        sources=replace(
            source, stored_run=replace(stored, claims=(claim, *stored.claims[1:]))
        ),
    )
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(changed)


def test_review_does_not_become_absence(review_analysis_inputs):
    bound = gate(review_analysis_inputs)
    assert not bound.decisions.policy
    assert {d.reason for d in bound.decisions.decisions} == {"calibration_required"}
    assert bound.completions == ()


# Forge immutable wrappers deliberately: the gate must not trust construction.
def forged(value, **changes):
    import copy

    result = copy.copy(value)
    for field, part in changes.items():
        object.__setattr__(result, field, part)
    return result


def change_source(inputs, **changes):
    return replace(inputs, sources=replace(inputs.sources, **changes))


@pytest.mark.parametrize(
    "field",
    [
        "canonical_hash",
        "element",
        "masks",
        "mask_policy",
        "mask_hash",
        "manifest_hash",
        "snapshot",
        "snapshot_inventory",
        "source_document",
    ],
    ids=[
        "hash",
        "element",
        "masks",
        "policy",
        "mask-binding",
        "manifest-binding",
        "bytes",
        "inventory",
        "identity",
    ],
)
def test_every_current_canonical_binding_refuses(analysis_inputs, field):
    import json

    from earnings_core import MaskCategory, OverlayMask, TextSpan

    bundle = analysis_inputs.sources.bundles[0]
    if field == "canonical_hash":
        changed = forged(
            analysis_inputs,
            sources=replace(
                analysis_inputs.sources,
                bundles=(
                    replace(
                        bundle,
                        document=bundle.document.model_copy(
                            update={"canonical_hash": "0" * 64}
                        ),
                    ),
                ),
            ),
        )
    elif field == "element":
        element = bundle.elements[0].model_copy(
            update={"span": TextSpan(start=1, end=bundle.elements[0].span.end)}
        )
        changed = change_source(
            analysis_inputs,
            bundles=(replace(bundle, elements=(element, *bundle.elements[1:])),),
        )
    elif field == "masks":
        mask = OverlayMask(
            doc_id=bundle.document.doc_id,
            canonical_hash=bundle.document.canonical_hash,
            span=bundle.elements[0].span,
            category=MaskCategory.SAFE_HARBOR,
            policy_id="invented-mask",
            policy_version="1",
        )
        changed = change_source(
            analysis_inputs, bundles=(replace(bundle, masks=(mask,)),)
        )
    elif field in ("mask_policy", "mask_hash", "manifest_hash", "source_document"):
        key = {
            "mask_policy": "mask_policy_version",
            "mask_hash": "mask_manifest_hash",
            "manifest_hash": "canonical_manifest_hash",
            "source_document": "source_document_id",
        }[field]
        changed = forged(
            analysis_inputs,
            metadata=(
                analysis_inputs.metadata[0].model_copy(
                    update={
                        key: "0" * 64 if field.endswith("hash") else "invented-other"
                    }
                ),
            ),
        )
    elif field == "snapshot_inventory":
        changed = replace(analysis_inputs, canonical_snapshots=())
    else:
        snapshot = analysis_inputs.canonical_snapshots[0]
        data = json.loads(snapshot.data)
        data["manifest"]["mask_policy_version"] = "2"
        changed = replace(
            analysis_inputs,
            canonical_snapshots=(replace(snapshot, data=json.dumps(data).encode()),),
        )
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(changed)


@pytest.mark.parametrize(
    "field",
    [
        "source_hash",
        "configuration_hash",
        "book",
        "rule",
        "assignment",
        "assignment_claim",
        "quote_span",
        "orphan",
        "links",
        "claim_text",
    ],
    ids=[
        "source",
        "configuration",
        "book",
        "rule",
        "assignment",
        "assignment-link",
        "span",
        "orphan",
        "claim-links",
        "interpretation",
    ],
)
def test_upstream_current_binding_refuses(analysis_inputs, field):

    sources = analysis_inputs.sources
    stored = sources.stored_run
    if field in ("source_hash", "configuration_hash"):
        key = "source_run_hash" if field == "source_hash" else field
        support = replace(
            analysis_inputs.support,
            record=analysis_inputs.support.record.model_copy(update={key: "0" * 64}),
        )
        changed = replace(analysis_inputs, support=support)
    elif field in ("book", "rule"):
        book = (
            sources.codebook.model_copy(update={"content_hash": "0" * 64})
            if field == "book"
            else sources.codebook.model_copy(
                update={
                    "rules": sources.codebook.rules.model_copy(
                        update={"multi_label": "Invented changed rule."}
                    )
                }
            )
        )
        changed = change_source(analysis_inputs, codebook=book)
    elif field in ("assignment", "assignment_claim"):
        key = "assignments" if field == "assignment" else "assignment_claims"
        rows = getattr(analysis_inputs.coding, key)
        row = rows[0].model_copy(
            update={"quote_id": "invented-absent"}
            if field == "assignment"
            else {"claim_id": "invented-absent"}
        )
        changed = replace(
            analysis_inputs,
            coding=replace(analysis_inputs.coding, **{key: (row, *rows[1:])}),
        )
    elif field == "quote_span":
        quote = stored.quotes[-1]
        quote = quote.model_copy(
            update={
                "span": quote.span.model_copy(
                    update={"quote_text": "Invented stale span."}
                )
            }
        )
        changed = change_source(
            analysis_inputs,
            stored_run=replace(stored, quotes=(*stored.quotes[:-1], quote)),
        )
    else:
        if field == "orphan":
            changes = {"quote_ids": (stored.quotes[0].quote_id,)}
            claims = tuple(c.model_copy(update=changes) for c in stored.claims)
        elif field == "claim_text":
            claims = (
                stored.claims[0].model_copy(
                    update={"claim": "Invented different interpretation."}
                ),
                *stored.claims[1:],
            )
        else:
            claims = (
                stored.claims[0].model_copy(
                    update={"quote_ids": tuple(reversed(stored.claims[0].quote_ids))}
                ),
                *stored.claims[1:],
            )
        changed = change_source(
            analysis_inputs, stored_run=replace(stored, claims=claims)
        )
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(changed)


@pytest.mark.parametrize(
    "field",
    [
        "issuer",
        "period",
        "expected",
        "acquisition",
        "authorization",
        "scope",
        "population",
    ],
    ids=[
        "issuer",
        "period",
        "expected",
        "acquisition",
        "authorization",
        "scope",
        "population",
    ],
)
def test_projection_policy_and_authorization_refuse(analysis_inputs, field):
    from datetime import date

    if field in ("issuer", "period"):
        metadata = analysis_inputs.metadata[0].model_copy(
            update={"entity_id": "invented-other"}
            if field == "issuer"
            else {"period_end": date(2025, 6, 30)}
        )
        changed = forged(analysis_inputs, metadata=(metadata,))
    elif field == "expected":
        changed = forged(analysis_inputs, expected=())
    elif field == "acquisition":
        changed = forged(
            analysis_inputs,
            acquisition=(
                analysis_inputs.acquisition[0].model_copy(
                    update={"state_run_id": "invented-stale"}
                ),
            ),
        )
    elif field == "authorization":
        changed = replace(
            analysis_inputs,
            fixture_authorization=replace(
                analysis_inputs.fixture_authorization, event_manifest_hash="0" * 64
            ),
        )
    else:
        policy = analysis_inputs.analysis_policy.model_copy(
            update={"scope": "research"}
            if field == "scope"
            else {"population_hash": "0" * 64}
        )
        changed = replace(analysis_inputs, analysis_policy=policy)
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(changed)


@pytest.mark.parametrize(
    "mode",
    ["no-claims", "unmatched", "review"],
    ids=["zero-quotes", "zero-targets", "zero-assignments"],
)
def test_empty_layers_still_rebind_every_source(analysis_input_factory, mode):
    options = (
        {"claims": ()}
        if mode == "no-claims"
        else {"themes": ()}
        if mode == "unmatched"
        else {"review": True}
    )
    inputs, _ = analysis_input_factory(**options)
    bound = gate(inputs)
    assert not inputs.coding.assignments
    assert not bound.completions
    bundle = inputs.sources.bundles[0]
    changed = change_source(inputs, bundles=(replace(bundle, elements=()),))
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(changed)
    stale = replace(
        inputs,
        metadata=(inputs.metadata[0].model_copy(update={"mask_policy_version": "2"}),),
    )
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(stale)


def test_document_qualified_identical_quote_ids(analysis_input_factory):
    inputs, _ = analysis_input_factory(documents=2, first_text="Invented " + "x" * 91)
    bound = gate(inputs)
    quotes = bound.inputs.sources.stored_run.quotes
    assert sum(q.quote_id == "q-0-100" for q in quotes) == 2
    assert len({(q.span.doc_id, q.quote_id) for q in quotes}) == 4
    assert len(bound.inputs.coding.assignments) == 4


def test_second_original_contextual_quote_cannot_disappear(analysis_input_factory):
    # Only the first invented paragraph supports acceptance.
    inputs, _ = analysis_input_factory(contribution={"q-27-53": "contextual"})
    bound = gate(inputs)
    assert all(len(d.supporting_quote_ids) == 1 for d in bound.decisions.decisions)
    # The second span remains original evidence despite contributing only context.
    second = inputs.sources.stored_run.quotes[-1]
    # A stale second span must refuse even when the first suffices for acceptance.
    changed_quote = second.model_copy(
        update={
            "span": second.span.model_copy(
                update={"quote_text": "Invented changed companion."}
            )
        }
    )
    changed = change_source(
        inputs,
        stored_run=replace(
            inputs.sources.stored_run,
            quotes=(*inputs.sources.stored_run.quotes[:-1], changed_quote),
        ),
    )
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(changed)
    assert all(len(c.quote_ids) == 2 for c in inputs.sources.stored_run.claims)


@pytest.mark.parametrize(
    "field",
    ["bundle", "metadata", "mask_policy", "snapshot", "masks"],
    ids=["bundle", "metadata", "policy", "snapshot", "masks"],
)
def test_policy_mutation_of_original_inputs_refuses(analysis_inputs, field):
    actual = analysis_inputs.assignment_policy
    touched = []

    class MutatingPolicy:
        reference = actual.reference

        def evaluate(self, view):
            if not touched:
                touched.append(True)
                if field == "bundle":
                    object.__setattr__(
                        analysis_inputs.sources.bundles[0].document,
                        "canonical_text",
                        "Invented changed caller document.",
                    )
                elif field == "metadata":
                    object.__setattr__(
                        analysis_inputs.metadata[0],
                        "publisher",
                        "Invented changed publisher.",
                    )
                elif field == "mask_policy":
                    object.__setattr__(
                        analysis_inputs.analysis_policy, "mask_policy_version", "2"
                    )
                elif field == "masks":
                    from earnings_core import MaskCategory, OverlayMask

                    bundle = analysis_inputs.sources.bundles[0]
                    mask = OverlayMask(
                        doc_id=bundle.document.doc_id,
                        canonical_hash=bundle.document.canonical_hash,
                        span=bundle.elements[0].span,
                        category=MaskCategory.SAFE_HARBOR,
                        policy_id="invented-mask",
                        policy_version="1",
                    )
                    object.__setattr__(bundle, "masks", (mask,))
                else:
                    object.__setattr__(
                        analysis_inputs.canonical_snapshots[0], "data", b"{}"
                    )
            return actual.evaluate(view)

    changed = replace(analysis_inputs, assignment_policy=MutatingPolicy())
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(changed)
    assert touched == [True]


def test_malicious_policy_exception_has_closed_output(analysis_inputs):
    actual = analysis_inputs.assignment_policy

    class ExplodingPolicy:
        reference = actual.reference

        def evaluate(self, view):
            try:
                raise RuntimeError("Invented SENTINEL inner exception")
            except RuntimeError as inner:
                raise RuntimeError("Invented SENTINEL outer exception") from inner

    with pytest.raises(AnalysisError) as raised:
        gate(replace(analysis_inputs, assignment_policy=ExplodingPolicy()))
    assert str(raised.value) == "input_changed"
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__
    assert "SENTINEL" not in repr(raised.value)


@pytest.mark.parametrize(
    "change", ["missing", "reference", "vote"], ids=["missing", "reference", "vote"]
)
def test_assignment_policy_must_match_and_repeat(analysis_inputs, change):
    actual = analysis_inputs.assignment_policy
    if change == "missing":
        policy = None
    else:

        class ChangedPolicy:
            reference = (
                actual.reference.model_copy(update={"policy_hash": "0" * 64})
                if change == "reference"
                else actual.reference
            )

            def evaluate(self, view):
                from earnings_themes.coding.records import PolicyVote

                return PolicyVote(action="review", supporting_quote_ids=())

        policy = ChangedPolicy()
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(replace(analysis_inputs, assignment_policy=policy))


def test_missing_cache_cannot_claim_verification(analysis_inputs):
    from earnings_themes.analysis import RawCacheVerification

    claims = (
        RawCacheVerification(
            stage="judge",
            status="verified",
            bindings=(),
            method="invented-assertion",
            version="1",
        ),
    )
    bound = gate(replace(analysis_inputs, raw_verification=claims))
    statuses = {r.stage: r.status for r in bound.inputs.raw_verification}
    assert statuses == {
        "extraction": "not_bound",
        "classifier": "not_supplied",
        "judge": "not_supplied",
        "scorer": "not_supplied",
    }


def test_supplied_actual_cache_bytes_are_verified(analysis_input_factory):
    inputs, _ = analysis_input_factory(caches=True)
    bound = gate(inputs)
    statuses = {r.stage: r for r in bound.inputs.raw_verification}
    assert statuses["classifier"].status == "verified"
    assert statuses["judge"].status == "verified"
    assert len(statuses["classifier"].bindings) > 0
    assert len(statuses["judge"].bindings) > 0
    assert statuses["scorer"].status == "not_bound"
    assert statuses["extraction"].status == "not_bound"


@pytest.mark.parametrize("stage", ["classifier", "judge"], ids=["classifier", "judge"])
def test_tampered_supplied_cache_bytes_refuse(analysis_input_factory, stage):
    inputs, root = analysis_input_factory(caches=True)
    reference = (
        inputs.coding.attempts[0].raw_ref
        if stage == "classifier"
        else inputs.support.attempts[0].raw_ref
    )
    path = (
        root
        / ("classifier-cache" if stage == "classifier" else "support-cache")
        / reference
    )
    path.write_bytes(b'{"invented": "tampered"}')
    with pytest.raises(AnalysisError, match="^storage_corrupt$"):
        gate(inputs)


def test_raw_snapshot_hash_tampering_is_storage_corrupt(analysis_inputs):
    snapshot = analysis_inputs.raw_snapshots[0]
    changed = replace(
        analysis_inputs, raw_snapshots=(replace(snapshot, data=snapshot.data + b"!"),)
    )
    with pytest.raises(AnalysisError, match="^storage_corrupt$"):
        gate(changed)


def test_raw_snapshot_absence_stays_explicit(analysis_inputs):
    bound = gate(replace(analysis_inputs, raw_snapshots=()))
    assert bound.inputs.raw_snapshots == ()
    assert bound.inputs.metadata[0].retain_raw


@pytest.mark.parametrize(
    "field", ["artifact", "source", "rights"], ids=["artifact", "source", "rights"]
)
def test_snapshot_identity_and_rights_refuse(analysis_inputs, field):
    snapshot = analysis_inputs.raw_snapshots[0]
    if field == "artifact":
        raw = forged(
            snapshot,
            artifact=snapshot.artifact.model_copy(
                update={"storage_ref": "invented/other.txt"}
            ),
        )
        changed = forged(analysis_inputs, raw_snapshots=(raw,))
    elif field == "source":
        changed = forged(
            analysis_inputs,
            raw_snapshots=(replace(snapshot, doc_id="invented-absent"),),
        )
    else:
        changed = forged(
            analysis_inputs,
            metadata=(
                analysis_inputs.metadata[0].model_copy(update={"retain_raw": False}),
            ),
        )
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(changed)


def test_no_theme_declaration_stale_binding_refuses(analysis_inputs):
    from earnings_core import digest
    from earnings_themes.analysis import NoThemeDeclaration
    from earnings_themes.coding.decide import support_run_hash

    from .cases import NOW

    declaration = NoThemeDeclaration(
        doc_id=analysis_inputs.metadata[0].doc_id,
        canonical_hash=analysis_inputs.metadata[0].canonical_hash,
        source_run_hash=analysis_inputs.support.record.source_run_hash,
        coding_run_hash=digest(analysis_inputs.coding.record.model_dump(mode="json")),
        support_run_hash=support_run_hash(analysis_inputs.support),
        codebook=analysis_inputs.coding.record.codebook,
        analysis_policy_hash="0" * 64,
        assignment_policy=analysis_inputs.assignment_policy.reference,
        actor_id="invented-declarer",
        declared_at=NOW,
        policy_scope="fixture",
    )
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(replace(analysis_inputs, no_theme=(declaration,)))


def test_unsupplied_caches_trigger_no_implicit_file_io(analysis_inputs, monkeypatch):
    from pathlib import Path

    def forbidden(*args, **kwargs):
        raise AssertionError("invented-io-forbidden")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    assert gate(analysis_inputs).inputs.raw_caches == analysis_inputs.raw_caches


def test_binding_is_content_based_and_repeated(analysis_inputs):
    first = gate(analysis_inputs)
    assert gate(first.inputs).binding_hash == first.binding_hash
    assert first.inputs.sources.stored_run is not analysis_inputs.sources.stored_run
    assert first.inputs.metadata[0] is not analysis_inputs.metadata[0]


def no_theme_declaration(inputs):
    from earnings_core import digest
    from earnings_themes.analysis import NoThemeDeclaration
    from earnings_themes.coding.decide import support_run_hash

    from .cases import NOW

    return NoThemeDeclaration(
        doc_id=inputs.metadata[0].doc_id,
        canonical_hash=inputs.metadata[0].canonical_hash,
        source_run_hash=inputs.support.record.source_run_hash,
        coding_run_hash=digest(inputs.coding.record.model_dump(mode="json")),
        support_run_hash=support_run_hash(inputs.support),
        codebook=inputs.coding.record.codebook,
        analysis_policy_hash=inputs.analysis_policy.content_hash,
        assignment_policy=inputs.assignment_policy.reference,
        actor_id="invented-declarer",
        declared_at=NOW,
        policy_scope="fixture",
    )


@pytest.mark.parametrize(
    "field",
    [
        "source_run_hash",
        "coding_run_hash",
        "support_run_hash",
        "canonical_hash",
        "analysis_policy_hash",
    ],
    ids=["source", "coding", "support", "document", "policy"],
)
def test_every_declaration_run_binding_refuses(analysis_input_factory, field):
    inputs, _ = analysis_input_factory(themes=())
    declaration = no_theme_declaration(inputs)
    valid = gate(replace(inputs, no_theme=(declaration,)))
    assert not valid.completions
    stale = declaration.model_copy(update={field: "0" * 64})
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(replace(inputs, no_theme=(stale,)))


def test_zero_target_book_rules_are_checked(analysis_input_factory):
    inputs, _ = analysis_input_factory(claims=())
    book = inputs.sources.codebook
    from earnings_themes.codebook import codebook_hash

    cyclic = book.model_copy(
        update={
            "themes": tuple(
                t.model_copy(update={"parent_id": t.theme_id}) for t in book.themes
            )
        }
    )
    cyclic = cyclic.model_copy(update={"content_hash": codebook_hash(cyclic)})
    with pytest.raises(AnalysisError, match="^input_changed$"):
        gate(change_source(inputs, codebook=cyclic))


def test_closed_cache_exception(analysis_input_factory, monkeypatch):
    from earnings_themes.coding.cache import CodingCache

    inputs, _ = analysis_input_factory(caches=True)

    def broken(*args):
        raise RuntimeError("Invented SENTINEL cache failure")

    monkeypatch.setattr(CodingCache, "artifact_hash", broken)
    with pytest.raises(AnalysisError, match="^storage_corrupt$") as raised:
        gate(inputs)
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__


@pytest.mark.parametrize(
    "field",
    ["doc_id", "data", "authorization"],
    ids=["doc-id", "bytes", "authorization"],
)
def test_forged_c2_container_types_refuse(analysis_inputs, field):
    if field == "authorization":
        authorization = forged(
            analysis_inputs.fixture_authorization, corpus_id="invented-unapproved"
        )
        changed = forged(analysis_inputs, fixture_authorization=authorization)
    else:
        snapshot = forged(
            analysis_inputs.canonical_snapshots[0],
            **{field: True if field == "doc_id" else bytearray(b"{}")},
        )
        changed = forged(analysis_inputs, canonical_snapshots=(snapshot,))
    with pytest.raises(AnalysisError):
        gate(changed)
