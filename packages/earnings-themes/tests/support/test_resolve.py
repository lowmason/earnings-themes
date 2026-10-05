"""Consuming invariants, independently forged around valid invented records."""

from dataclasses import replace

import pytest
from earnings_core import VALIDATOR_VERSION, digest
from earnings_themes.codebook import codebook_hash
from earnings_themes.support.records import RefusedTarget, ResolvedInput
from earnings_themes.support.resolve import resolve_target, reverify_input


def resolve(sources, target):
    return resolve_target(
        sources.stored_run,
        sources.bundles,
        sources.codebook,
        target,
        provenance_hash=sources.provenance_hash,
    )


def assert_refused(result):
    assert isinstance(result, RefusedTarget)
    assert result.outcome.status == "refused"
    assert result.record.evidence_ids == ()


def test_valid_order_and_deterministic_hash(case):
    sources, target = case
    result = resolve(sources, target)
    assert isinstance(result, ResolvedInput)
    assert result.record.original_quote_ids == sources.stored_run.claims[0].quote_ids
    assert result.record.evidence_ids == tuple(e.quote_id for e in result.evidence)
    assert [e.start for e in result.evidence] == sorted(
        e.start for e in result.evidence
    )
    assert resolve(sources, target).record == result.record
    assert isinstance(reverify_input(result), ResolvedInput)


@pytest.mark.parametrize(
    "field,value",
    [
        ("quote_text", "INVENTED_TAMPER"),
        ("start", True),
        ("start", 0.0),
        ("element_id", "unknown"),
        ("prefix", "invented-invalid-locator"),
        ("canonical_hash", "0" * 64),
        ("doc_id", "wrong"),
    ],
)
def test_one_tampered_quote_refuses_whole_target(case, field, value):
    sources, target = case
    q = sources.stored_run.quotes[0]
    run = replace(
        sources.stored_run,
        quotes=(
            q.model_copy(update={"span": q.span.model_copy(update={field: value})}),
            *sources.stored_run.quotes[1:],
        ),
    )
    assert_refused(resolve(replace(sources, stored_run=run), target))


@pytest.mark.parametrize(
    "kind",
    [
        "missing_claim",
        "duplicate_claim",
        "missing_quote",
        "duplicate_quote",
        "conflicting_quote",
        "repeat_link",
        "empty_links",
        "wrong_masks",
        "wrong_run",
        "wrong_mapping",
        "missing_document",
        "duplicate_document",
        "wrong_document_hash",
        "bad_document",
        "bad_element",
        "ocr",
        "bad_configuration_hash",
        "bad_provenance",
    ],
)
def test_source_integrity(case, kind):
    sources, target = case
    run = sources.stored_run
    q = run.quotes[0]
    c = run.claims[0]
    b = sources.bundles[0]
    if kind == "missing_claim":
        run = replace(run, claims=())
    elif kind == "duplicate_claim":
        run = replace(run, claims=(c, c))
    elif kind == "missing_quote":
        run = replace(run, quotes=run.quotes[1:])
    elif kind == "duplicate_quote":
        run = replace(run, quotes=(*run.quotes, q))
    elif kind == "conflicting_quote":
        run = replace(
            run, quotes=(*run.quotes, q.model_copy(update={"mask_ids": ("unknown",)}))
        )
    elif kind in ("repeat_link", "empty_links"):
        run = replace(
            run,
            claims=(
                c.model_copy(
                    update={
                        "quote_ids": (q.quote_id, q.quote_id)
                        if kind == "repeat_link"
                        else ()
                    }
                ),
            ),
        )
    elif kind == "wrong_masks":
        run = replace(
            run,
            quotes=(q.model_copy(update={"mask_ids": ("unknown",)}), *run.quotes[1:]),
        )
    elif kind == "wrong_run":
        target = target.model_copy(update={"source_run_id": "wrong"})
    elif kind == "wrong_mapping":
        run = replace(
            run,
            record=run.record.model_copy(
                update={"documents": {target.doc_id: "0" * 64}}
            ),
        )
    elif kind == "missing_document":
        run = replace(run, documents=())
    elif kind == "duplicate_document":
        run = replace(run, documents=run.documents * 2)
    elif kind == "wrong_document_hash":
        run = replace(
            run,
            documents=(
                run.documents[0].model_copy(update={"canonical_hash": "0" * 64}),
            ),
        )
    elif kind == "bad_document":
        sources = replace(
            sources,
            bundles=(
                replace(
                    b,
                    document=b.document.model_copy(
                        update={"canonical_text": "Changed"}
                    ),
                ),
            ),
        )
    elif kind in ("bad_element", "ocr"):
        field, value = (
            ("doc_id", "wrong") if kind == "bad_element" else ("text_origin", "ocr")
        )
        sources = replace(
            sources,
            bundles=(
                replace(
                    b,
                    elements=tuple(
                        e.model_copy(update={field: value}) for e in b.elements
                    ),
                ),
            ),
        )
    elif kind == "bad_configuration_hash":
        run = replace(
            run, record=run.record.model_copy(update={"configuration_hash": "0" * 64})
        )
    elif kind == "bad_provenance":
        sources = replace(sources, provenance_hash="invalid")
    sources = replace(sources, stored_run=run)
    assert_refused(resolve(sources, target))


@pytest.mark.parametrize(
    "kind",
    [
        "draft",
        "stale",
        "changed_definition",
        "unknown",
        "unmatched",
        "duplicate",
        "unknown_parent",
        "cycle",
        "blank_approval",
    ],
)
def test_frozen_codebook(case, kind):
    sources, target = case
    book = sources.codebook
    theme = book.themes[0]
    if kind == "draft":
        book = book.model_copy(update={"status": "draft", "approval": None})
    elif kind == "stale":
        target = target.model_copy(
            update={
                "codebook": target.codebook.model_copy(update={"codebook_version": 99})
            }
        )
    elif kind == "changed_definition":
        book = book.model_copy(
            update={
                "themes": (
                    theme.model_copy(
                        update={"definition": "Changed invented definition"}
                    ),
                )
            }
        )
    elif kind in ("unknown", "unmatched"):
        target = target.model_copy(update={"theme_id": kind})
    elif kind == "duplicate":
        book = book.model_copy(update={"themes": (theme, theme)})
    elif kind in ("unknown_parent", "cycle"):
        book = book.model_copy(
            update={
                "themes": (
                    theme.model_copy(
                        update={
                            "parent_id": "absent"
                            if kind == "unknown_parent"
                            else theme.theme_id
                        }
                    ),
                )
            }
        )
    elif kind == "blank_approval":
        book = book.model_copy(
            update={"approval": book.approval.model_copy(update={"approver": " "})}
        )
    if kind in ("duplicate", "unknown_parent", "cycle"):
        book = book.model_copy(update={"content_hash": codebook_hash(book)})
        target = target.model_copy(
            update={
                "codebook": target.codebook.model_copy(
                    update={"content_hash": book.content_hash}
                )
            }
        )
    assert_refused(resolve(replace(sources, codebook=book), target))


def test_examples_are_never_dereferenced(case, monkeypatch):
    import earnings_themes.codebook as module

    def forbidden(*args, **kwargs):
        raise AssertionError("example dereference")

    for name in ("validate_codebook", "anchor", "check_pointer"):
        monkeypatch.setattr(module, name, forbidden)
    assert isinstance(resolve(*case), ResolvedInput)


def test_old_validator_is_rechecked(case, monkeypatch):
    import earnings_themes.support.resolve as module

    sources, target = case
    run = sources.stored_run
    run = replace(
        run,
        quotes=tuple(
            q.model_copy(
                update={
                    "span": q.span.model_copy(update={"validator_version": "older"})
                }
            )
            for q in run.quotes
        ),
    )
    calls = []
    original = module.reverify_span

    def spy(*args):
        calls.append(1)
        return original(*args)

    monkeypatch.setattr(module, "reverify_span", spy)
    result = resolve(replace(sources, stored_run=run), target)
    assert isinstance(result, ResolvedInput)
    assert len(calls) == len(run.quotes)
    assert all(e.validator_version == VALIDATOR_VERSION for e in result.evidence)


def test_consuming_input_content_cannot_be_forged(case):
    result = resolve(*case)
    assert isinstance(result, ResolvedInput)
    assert_refused(reverify_input(replace(result, claim="Forged claim")))
    assert_refused(reverify_input(replace(result, evidence=())))
    assert_refused(
        reverify_input(
            replace(
                result,
                record=result.record.model_copy(
                    update={"input_hash": digest("changed")}
                ),
            )
        )
    )


def test_all_links_are_reverified_even_after_a_refusal(case, monkeypatch):
    import earnings_themes.support.resolve as module

    sources, target = case
    run = sources.stored_run
    quotes = tuple(
        q.model_copy(
            update={"span": q.span.model_copy(update={"quote_text": "INVENTED_TAMPER"})}
        )
        for q in run.quotes
    )
    calls = []
    original = module.reverify_span

    def spy(*args):
        calls.append(args[2].start)
        return original(*args)

    monkeypatch.setattr(module, "reverify_span", spy)
    assert_refused(
        resolve(replace(sources, stored_run=replace(run, quotes=quotes)), target)
    )
    assert len(calls) == len(quotes)


def test_forged_nested_schema_integer_is_refused(case):
    sources, target = case
    run = sources.stored_run
    q = run.quotes[0]
    q = q.model_copy(
        update={"span": q.span.model_copy(update={"schema_version": True})}
    )
    assert_refused(
        resolve(
            replace(sources, stored_run=replace(run, quotes=(q, *run.quotes[1:]))),
            target,
        )
    )


def test_same_bare_quote_id_in_another_document_is_not_a_duplicate(case):
    sources, target = case
    run = sources.stored_run
    q = run.quotes[0]
    other = q.model_copy(
        update={"span": q.span.model_copy(update={"doc_id": "other-document"})}
    )
    result = resolve(
        replace(sources, stored_run=replace(run, quotes=(*run.quotes, other))), target
    )
    assert isinstance(result, ResolvedInput)


def test_changed_canonical_version_is_refused(case):
    from earnings_core import CanonicalDocument

    sources, target = case
    bundle = sources.bundles[0]
    doc = CanonicalDocument.create(
        source_document_id=bundle.document.source_document_id,
        canonicalization_version="test-2",
        canonical_text=bundle.document.canonical_text,
    )
    assert_refused(
        resolve(replace(sources, bundles=(replace(bundle, document=doc),)), target)
    )


def test_source_changes_are_detected_at_consuming_gate(case):
    result = resolve(*case)
    sources = result.sources
    run = sources.stored_run
    claim = run.claims[0].model_copy(update={"claim": "A changed invented claim."})
    changed = replace(sources, stored_run=replace(run, claims=(claim,)))
    refused = reverify_input(replace(result, sources=changed))
    assert_refused(refused)
    assert refused.outcome.missing == ("input_changed",)


@pytest.mark.parametrize(
    "kind",
    [
        "unknown_quote_field",
        "unknown_nested_field",
        "nonstring_document_key",
        "boolean_codebook_schema",
    ],
)
def test_raw_fields_cannot_disappear_during_json_dump(case, kind):
    sources, target = case
    run = sources.stored_run
    q = run.quotes[0]
    if kind == "unknown_quote_field":
        run = replace(
            run,
            quotes=(
                q.model_copy(update={"untrusted_extra": "INVENTED_SENTINEL"}),
                *run.quotes[1:],
            ),
        )
    elif kind == "unknown_nested_field":
        run = replace(
            run,
            quotes=(
                q.model_copy(
                    update={
                        "span": q.span.model_copy(
                            update={"untrusted_extra": "INVENTED_SENTINEL"}
                        )
                    }
                ),
                *run.quotes[1:],
            ),
        )
    elif kind == "nonstring_document_key":
        run = replace(
            run,
            record=run.record.model_copy(
                update={"documents": {**run.record.documents, 123: "0" * 64}}
            ),
        )
    else:
        sources = replace(
            sources,
            codebook=sources.codebook.model_copy(update={"schema_version": True}),
        )
    assert_refused(resolve(replace(sources, stored_run=run), target))


@pytest.mark.parametrize(
    "field,value", [("start", 0.0), ("start", False), ("schema_version", True)]
)
def test_consuming_gate_refuses_equal_valued_evidence_forgery(case, field, value):
    resolved = resolve(*case)
    reference = resolved.evidence[0]
    assert reference.start == 0
    forged = reference.model_copy(update={field: value})
    assert forged == reference
    result = reverify_input(
        replace(resolved, evidence=(forged, *resolved.evidence[1:]))
    )
    assert_refused(result)
    assert result.outcome.missing == ("malformed_record",)


@pytest.mark.parametrize(
    "kind", ["record_schema", "evidence_list", "contexts_list", "claim_shape"]
)
def test_consuming_gate_requires_strict_retained_shape(case, kind):
    resolved = resolve(*case)
    if kind == "record_schema":
        forged = replace(
            resolved, record=resolved.record.model_copy(update={"schema_version": True})
        )
    elif kind == "evidence_list":
        forged = replace(resolved, evidence=list(resolved.evidence))
    elif kind == "contexts_list":
        forged = replace(resolved, contexts=[])
    else:
        forged = replace(resolved, claim=True)
    result = reverify_input(forged)
    assert_refused(result)
    assert result.outcome.missing == ("malformed_record",)


@pytest.mark.parametrize(
    "field,value", [("start", 0.0), ("start", False), ("schema_version", True)]
)
def test_consuming_gate_revalidates_context_references(case, field, value):
    from earnings_themes.support.records import ContextReference

    resolved = resolve(*case)
    reference = resolved.evidence[0]
    fields = {
        name: getattr(reference, name)
        for name in ContextReference.model_fields
        if name != "kind"
    }
    context = ContextReference(**fields, kind="block").model_copy(update={field: value})
    result = reverify_input(replace(resolved, contexts=(context,)))
    assert_refused(result)
    assert result.outcome.missing == ("malformed_record",)
