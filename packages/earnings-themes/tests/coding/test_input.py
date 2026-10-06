"""Complete frozen coding input and its repeated exact-evidence gate."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from earnings_core import digest
from earnings_themes.codebook import codebook_hash
from earnings_themes.coding.input import resolve_coding_input, reverify_coding_input
from earnings_themes.coding.records import CodingError


def classify_after_gate(sources, doc_id, claim_id, dispatches):
    resolved = resolve_coding_input(sources, doc_id, claim_id)
    dispatches.append(resolved.input_hash)
    return resolved


def test_every_definition_is_bound_without_examples(coding_case):
    claim = coding_case.stored_run.claims[0]
    resolved = resolve_coding_input(coding_case, claim.doc_id, claim.claim_id)
    assert len(resolved.probes) == len(coding_case.codebook.themes) == 2
    assert [p.record.theme.theme_id for p in resolved.probes] == ["capacity", "demand"]
    assert all(
        "positive_examples" not in type(p.record.theme).model_fields
        for p in resolved.probes
    )
    assert reverify_coding_input(resolved).input_hash == resolved.input_hash


def test_mutated_source_is_refused_before_classification(coding_case):
    claim = coding_case.stored_run.claims[0]
    resolved = resolve_coding_input(coding_case, claim.doc_id, claim.claim_id)
    bundle = coding_case.bundles[0]
    damaged = replace(
        bundle,
        document=bundle.document.model_copy(
            update={"canonical_text": "Invented changed text"}
        ),
    )
    with pytest.raises(CodingError):
        reverify_coding_input(
            replace(resolved, sources=replace(coding_case, bundles=(damaged,)))
        )


@pytest.mark.parametrize(
    "kind,reason",
    [
        ("draft", "codebook_not_approved"),
        ("hash", "wrong_codebook"),
        ("version", "wrong_codebook"),
        ("id", "wrong_codebook"),
        ("unknown_parent", "unknown_parent"),
        ("parent_cycle", "parent_cycle"),
        ("duplicate_theme", "duplicate_theme"),
        ("reserved_theme", "duplicate_theme"),
        ("empty_themes", "wrong_codebook"),
    ],
)
def test_frozen_codebook_refuses_before_classification(coding_case, kind, reason):
    book = coding_case.codebook
    themes = book.themes
    if kind == "draft":
        book = book.model_copy(update={"status": "draft", "approval": None})
    elif kind == "hash":
        book = book.model_copy(update={"content_hash": digest("invented wrong hash")})
    elif kind == "version":
        book = book.model_copy(update={"codebook_version": 1})
    elif kind == "id":
        book = book.model_copy(update={"codebook_id": "invented-other"})
    else:
        if kind == "unknown_parent":
            themes = (themes[0].model_copy(update={"parent_id": "absent"}), themes[1])
        elif kind == "parent_cycle":
            themes = (
                themes[0].model_copy(update={"parent_id": themes[1].theme_id}),
                themes[1].model_copy(update={"parent_id": themes[0].theme_id}),
            )
        elif kind == "duplicate_theme":
            themes = (themes[0], themes[0])
        elif kind == "reserved_theme":
            themes = (themes[0].model_copy(update={"theme_id": "unmatched"}), themes[1])
        else:
            themes = ()
        book = book.model_copy(update={"themes": themes})
        book = book.model_copy(update={"content_hash": codebook_hash(book)})
    claim = coding_case.stored_run.claims[0]
    dispatches = []
    with pytest.raises(CodingError, match=f"^{reason}$"):
        classify_after_gate(
            replace(coding_case, codebook=book),
            claim.doc_id,
            claim.claim_id,
            dispatches,
        )
    assert dispatches == []


@pytest.mark.parametrize(
    "kind,reason",
    [
        ("unknown_claim", "unknown_claim"),
        ("duplicate_claim", "duplicate_claim"),
        ("missing_quote", "unknown_quote"),
        ("duplicate_quote", "duplicate_quote"),
        ("wrong_document_quote", "unknown_quote"),
        ("quote_id_span", "invalid_quote"),
        ("bad_original_link", "quote_text_mismatch"),
        ("foreign_masks", "masks_mismatch"),
        ("empty_bundles", "wrong_document"),
        ("duplicate_bundles", "wrong_document"),
        ("configuration_hash", "wrong_source_run"),
    ],
)
def test_source_integrity_refuses_before_classification(coding_case, kind, reason):
    sources = coding_case
    run = sources.stored_run
    claim = run.claims[0]
    quote = run.quotes[0]
    claim_id = claim.claim_id
    if kind == "unknown_claim":
        claim_id = "invented-unknown-claim"
    elif kind == "duplicate_claim":
        run = replace(run, claims=(claim, claim))
    elif kind == "missing_quote":
        run = replace(run, quotes=())
    elif kind == "duplicate_quote":
        run = replace(run, quotes=(quote, quote))
    elif kind == "wrong_document_quote":
        run = replace(
            run,
            quotes=(
                quote.model_copy(
                    update={
                        "span": quote.span.model_copy(
                            update={"doc_id": "invented-other-document"}
                        )
                    }
                ),
            ),
        )
    elif kind == "quote_id_span":
        quote = quote.model_copy(update={"quote_id": "q-1-2"})
        run = replace(
            run,
            quotes=(quote,),
            claims=(claim.model_copy(update={"quote_ids": (quote.quote_id,)}),),
        )
    elif kind == "bad_original_link":
        bad = quote.model_copy(
            update={
                "quote_id": "invented-bad-link",
                "span": quote.span.model_copy(update={"quote_text": "INVENTED_TAMPER"}),
            }
        )
        run = replace(
            run,
            quotes=(quote, bad),
            claims=(
                claim.model_copy(update={"quote_ids": (quote.quote_id, bad.quote_id)}),
            ),
        )
    elif kind == "foreign_masks":
        run = replace(
            run,
            quotes=(quote.model_copy(update={"mask_ids": ("invented-foreign-mask",)}),),
        )
    elif kind == "empty_bundles":
        sources = replace(sources, bundles=())
    elif kind == "duplicate_bundles":
        sources = replace(sources, bundles=sources.bundles * 2)
    elif kind == "configuration_hash":
        run = replace(
            run,
            record=run.record.model_copy(
                update={"configuration_hash": digest("invented changed configuration")}
            ),
        )
    dispatches = []
    with pytest.raises(CodingError, match=f"^{reason}$"):
        classify_after_gate(
            replace(sources, stored_run=run), claim.doc_id, claim_id, dispatches
        )
    assert dispatches == []


@pytest.mark.parametrize("construction", ["copy", "construct"])
@pytest.mark.parametrize("value", [False, True, 0.0, "0", -1])
def test_invalid_offsets_refuse_before_classification(coding_case, construction, value):
    run = coding_case.stored_run
    quote = run.quotes[0]
    fields = quote.span.model_dump()
    fields["start"] = value
    span = (
        quote.span.model_copy(update={"start": value})
        if construction == "copy"
        else type(quote.span).model_construct(**fields)
    )
    damaged = replace(run, quotes=(quote.model_copy(update={"span": span}),))
    claim = run.claims[0]
    dispatches = []
    with pytest.raises(CodingError):
        classify_after_gate(
            replace(coding_case, stored_run=damaged),
            claim.doc_id,
            claim.claim_id,
            dispatches,
        )
    assert dispatches == []


@pytest.mark.parametrize(
    "kind", ["definition", "claim", "codebook_version", "provenance"]
)
def test_changed_valid_source_is_refused_at_reverification(coding_input, kind):
    sources = coding_input.sources
    if kind in ("definition", "codebook_version"):
        book = sources.codebook
        if kind == "definition":
            book = book.model_copy(
                update={
                    "themes": (
                        book.themes[0].model_copy(
                            update={"definition": "A changed invented definition."}
                        ),
                        book.themes[1],
                    )
                }
            )
        else:
            book = book.model_copy(update={"codebook_version": 1})
        book = book.model_copy(update={"content_hash": codebook_hash(book)})
        sources = replace(sources, codebook=book)
    elif kind == "claim":
        run = sources.stored_run
        sources = replace(
            sources,
            stored_run=replace(
                run,
                claims=(
                    run.claims[0].model_copy(
                        update={"claim": "A changed invented operating claim."}
                    ),
                ),
            ),
        )
    else:
        sources = replace(
            sources, provenance_hash=digest("changed invented provenance")
        )
    with pytest.raises(CodingError, match="^input_changed$"):
        reverify_coding_input(replace(coding_input, sources=sources))


@pytest.mark.parametrize(
    "kind",
    [
        "sources_object",
        "run_object",
        "bundle_object",
        "bundles_list",
        "claims_list",
        "quotes_list",
        "elements_list",
        "masks_list",
        "themes_list",
    ],
)
def test_resolver_requires_exact_source_dataclass_and_container_types(
    coding_case, kind
):
    sources = coding_case
    if kind == "sources_object":
        sources = SimpleNamespace(**vars(sources))
    elif kind == "run_object":
        sources = replace(
            sources, stored_run=SimpleNamespace(**vars(sources.stored_run))
        )
    elif kind == "bundle_object":
        sources = replace(
            sources, bundles=(SimpleNamespace(**vars(sources.bundles[0])),)
        )
    elif kind == "bundles_list":
        sources = replace(sources, bundles=list(sources.bundles))
    elif kind in ("claims_list", "quotes_list"):
        name = kind.removesuffix("_list")
        sources = replace(
            sources,
            stored_run=replace(
                sources.stored_run, **{name: list(getattr(sources.stored_run, name))}
            ),
        )
    elif kind in ("elements_list", "masks_list"):
        name = kind.removesuffix("_list")
        bundle = sources.bundles[0]
        sources = replace(
            sources, bundles=(replace(bundle, **{name: list(getattr(bundle, name))}),)
        )
    else:
        sources = replace(
            sources,
            codebook=sources.codebook.model_copy(
                update={"themes": list(sources.codebook.themes)}
            ),
        )
    claim = coding_case.stored_run.claims[0]
    with pytest.raises(CodingError, match="^malformed_record$"):
        resolve_coding_input(sources, claim.doc_id, claim.claim_id)


@pytest.mark.parametrize(
    "kind",
    [
        "input_object",
        "probes_list",
        "probe_object",
        "evidence_list",
        "contexts_list",
        "claim_shape",
        "schema_bool",
        "evidence_bool",
        "evidence_float",
        "context_bool",
        "context_float",
        "input_hash",
        "missing_probe",
        "duplicate_probe",
        "reversed_probes",
        "forged_claim",
    ],
)
def test_retained_input_forgery_is_refused(coding_input, kind):
    probe = coding_input.probes[0]
    if kind == "input_object":
        changed = SimpleNamespace(**vars(coding_input))
    elif kind == "probes_list":
        changed = replace(coding_input, probes=list(coding_input.probes))
    elif kind == "input_hash":
        changed = replace(coding_input, input_hash=digest("invented changed input"))
    elif kind in ("missing_probe", "duplicate_probe", "reversed_probes"):
        probes = (
            coding_input.probes[1:]
            if kind == "missing_probe"
            else (probe, probe)
            if kind == "duplicate_probe"
            else tuple(reversed(coding_input.probes))
        )
        changed = replace(coding_input, probes=probes)
    else:
        if kind == "probe_object":
            probe = SimpleNamespace(**vars(probe))
        elif kind in ("evidence_list", "contexts_list"):
            name = kind.removesuffix("_list")
            probe = replace(probe, **{name: list(getattr(probe, name))})
        elif kind == "claim_shape":
            probe = replace(probe, claim=True)
        elif kind == "forged_claim":
            probe = replace(probe, claim="A forged invented claim.")
        elif kind == "schema_bool":
            probe = replace(
                probe, record=probe.record.model_copy(update={"schema_version": True})
            )
        else:
            name = "evidence" if kind.startswith("evidence") else "contexts"
            references = getattr(probe, name)
            reference = references[0]
            assert reference.start == 0
            forged = reference.model_copy(
                update={"start": False if kind.endswith("bool") else 0.0}
            )
            assert forged == reference
            probe = replace(probe, **{name: (forged, *references[1:])})
        changed = replace(coding_input, probes=(probe, *coding_input.probes[1:]))
    with pytest.raises(CodingError):
        reverify_coding_input(changed)


def test_resolver_never_reads_files_or_examples(coding_case, monkeypatch):
    import builtins

    import earnings_themes.codebook as codebook_module

    trips = []

    def forbidden(*args, **kwargs):
        trips.append("forbidden_reader")
        raise AssertionError("forbidden_reader")

    for name in (
        "validate_codebook",
        "anchor",
        "check_pointer",
        "load_codebook",
        "load_codebook_draft",
    ):
        monkeypatch.setattr(codebook_module, name, forbidden)
    with monkeypatch.context() as readers:
        readers.setattr(builtins, "open", forbidden)
        for name in ("open", "read_text", "read_bytes"):
            readers.setattr(Path, name, forbidden)
        claim = coding_case.stored_run.claims[0]
        resolved = resolve_coding_input(coding_case, claim.doc_id, claim.claim_id)
        assert reverify_coding_input(resolved).input_hash == resolved.input_hash
    assert trips == []


def test_complete_probe_order_is_independent_of_codebook_order(coding_case):
    book = coding_case.codebook.model_copy(
        update={"themes": tuple(reversed(coding_case.codebook.themes))}
    )
    book = book.model_copy(update={"content_hash": codebook_hash(book)})
    claim = coding_case.stored_run.claims[0]
    resolved = resolve_coding_input(
        replace(coding_case, codebook=book), claim.doc_id, claim.claim_id
    )
    assert [probe.record.theme.theme_id for probe in resolved.probes] == [
        "capacity",
        "demand",
    ]


def test_input_diagnostics_never_include_source_claim_or_definitions(coding_input):
    printed = repr(coding_input) + str(coding_input)
    assert "CodingInput" in printed
    for text in (
        coding_input.sources.bundles[0].document.canonical_text,
        coding_input.probes[0].claim,
        coding_input.probes[0].record.theme.definition,
    ):
        assert text not in printed


def test_all_original_links_reach_current_public_span_gate(coding_case, monkeypatch):
    import earnings_themes.support.resolve as module

    run = coding_case.stored_run
    claim, quote = run.claims[0], run.quotes[0]
    bad = quote.model_copy(
        update={
            "quote_id": "invented-bad-link",
            "span": quote.span.model_copy(update={"quote_text": "INVENTED_TAMPER"}),
        }
    )
    run = replace(
        run,
        quotes=(bad, quote),
        claims=(
            claim.model_copy(update={"quote_ids": (bad.quote_id, quote.quote_id)}),
        ),
    )
    original = module.reverify_span
    calls = []

    def current_gate(*args):
        calls.append(args[2].quote_text == quote.span.quote_text)
        return original(*args)

    monkeypatch.setattr(module, "reverify_span", current_gate)
    with pytest.raises(CodingError, match="^quote_text_mismatch$"):
        resolve_coding_input(
            replace(coding_case, stored_run=run), claim.doc_id, claim.claim_id
        )
    assert calls == [False, True]


@pytest.mark.parametrize(
    "flags,missing,reason",
    [
        ((), (), "invalid_references"),
        (("invented-unknown-reason",), (), "invalid_references"),
        (("invented-unknown-reason",), ("wrong_codebook",), "wrong_codebook"),
        (("unknown_quote",), ("wrong_codebook",), "unknown_quote"),
    ],
)
def test_refusal_selects_first_closed_reason(
    coding_input, monkeypatch, flags, missing, reason
):
    import earnings_themes.coding.input as module
    from earnings_themes.support.records import (
        RefusedTarget,
        ReviewOutcome,
        ReviewStatus,
    )

    record = coding_input.probes[0].record
    outcome = ReviewOutcome(
        target_id=record.target_id,
        status=ReviewStatus.REFUSED,
        flags=(),
        missing=(),
        signal_ids=(),
        trial_ids=(),
    ).model_copy(update={"flags": flags, "missing": missing})
    monkeypatch.setattr(
        module, "resolve_target", lambda *args, **kwargs: RefusedTarget(record, outcome)
    )
    with pytest.raises(CodingError, match=f"^{reason}$"):
        resolve_coding_input(
            coding_input.sources, coding_input.doc_id, coding_input.claim_id
        )
