"""The codebook contract and its freeze (the Stage 6 spec, §The codebook): R9.2's
fields, examples only from training bundles or flagged synthetic, a content hash
that ADR 0003 can cite before approval, and one refusal per problem."""

from datetime import date

import pytest
from earnings_themes.codebook import (
    Approval,
    Codebook,
    CodebookDraft,
    CodebookStatus,
    codebook_hash,
    codebook_toml,
    freeze_codebook,
    load_codebook,
    validate_codebook,
)
from earnings_themes.problems import Refusal
from earnings_themes.records import RecordError, parse
from earnings_themes.synthetic import (
    DEV,
    PIN,
    TEST,
    TRAIN,
    build_synthetic,
    codebook_draft,
    synthetic_split,
)

APPROVAL = Approval(
    approver="Lowell Mason",
    approved_on=date(2026, 10, 2),
    adr="docs/adr/0003-approve-pilot-codebook-v0.md",
)


@pytest.fixture
def bundles():
    return {e: build_synthetic(e).bundle for e in (TRAIN, DEV, TEST)}


def freeze(draft: dict, bundles, approval=None):
    return freeze_codebook(
        parse(draft, CodebookDraft, "draft"),
        pin=PIN,
        split=synthetic_split(),
        bundles=bundles,
        approval=approval,
    )


def test_a_draft_freezes_with_its_examples_anchored(bundles) -> None:
    codebook = freeze(codebook_draft(), bundles)
    assert isinstance(codebook, Codebook)
    assert codebook.status is CodebookStatus.DRAFT
    assert codebook.approval is None
    corpus = codebook.discovery_corpus
    assert corpus.event_ids == (TRAIN,)
    assert corpus.doc_ids == (bundles[TRAIN].document.doc_id,)
    assert corpus.split_hash == synthetic_split().content_hash
    (theme,) = codebook.themes
    (positive,) = theme.positive_examples
    assert positive.pointer is not None
    assert positive.pointer.event_id == TRAIN
    assert positive.pointer.context_sha256 is not None
    (negative,) = theme.hard_negatives
    assert negative.synthetic
    assert codebook.content_hash == codebook_hash(codebook)


def test_approval_leaves_the_content_hash_unchanged(bundles) -> None:
    draft = freeze(codebook_draft(), bundles)
    approved = freeze(codebook_draft(), bundles, APPROVAL)
    assert isinstance(draft, Codebook)
    assert isinstance(approved, Codebook)
    assert approved.status is CodebookStatus.APPROVED
    assert approved.content_hash == draft.content_hash


def test_the_committed_file_round_trips_and_holds_no_quote(bundles, tmp_path) -> None:
    codebook = freeze(codebook_draft(), bundles, APPROVAL)
    assert isinstance(codebook, Codebook)
    path = tmp_path / "codebook-v0.toml"
    path.write_text(codebook_toml(codebook), encoding="utf-8")
    assert load_codebook(path) == codebook
    assert "Revenue grew" not in path.read_text(encoding="utf-8")


def example(**fields) -> dict:
    return codebook_draft(
        themes=[
            {
                **codebook_draft()["themes"][0],
                "positive_examples": [fields],
            }
        ]
    )


@pytest.mark.parametrize(
    ("fields", "reason"),
    [
        ({"event_id": DEV, "text": "Margins held steady."}, "outside_training"),
        ({"event_id": TEST, "text": "Margins held steady."}, "outside_training"),
        ({"text": "Margins held steady."}, "synthetic_unflagged"),
        (
            {"event_id": TRAIN, "text": "Revenue grew in every region."},
            "ambiguous_occurrence",
        ),
        ({"event_id": TRAIN, "text": "Region Sales"}, "not_narrative"),
        ({"event_id": TRAIN, "text": "Nothing like this."}, "locator_not_found"),
        (
            {"synthetic": True, "event_id": TRAIN, "text": "Margins held steady."},
            "malformed",
        ),
    ],
)
def test_an_example_that_cannot_stand_is_refused(bundles, fields, reason) -> None:
    assert freeze(example(**fields), bundles) == [
        Refusal("theme demand.positive_examples[0]", reason)
    ]


def test_theme_structure_is_checked(bundles) -> None:
    base = codebook_draft()["themes"][0]
    themes = [
        {**base, "theme_id": "a", "parent_id": "b"},
        {**base, "theme_id": "b", "parent_id": "a"},
        {**base, "theme_id": "c", "parent_id": "missing"},
        {**base, "theme_id": "c"},
    ]
    assert freeze(codebook_draft(themes=themes), bundles) == [
        Refusal("theme c", "duplicate_id"),
        Refusal("theme c", "unknown_theme"),
        Refusal("theme a", "parent_cycle"),
        Refusal("theme b", "parent_cycle"),
    ]


def test_wording_copied_from_a_training_bundle_is_refused(bundles) -> None:
    copied = "The user wrote: Revenue grew in every region. Margins held steady."
    draft = codebook_draft()
    draft["themes"][0]["definition"] = copied
    assert freeze(draft, bundles) == [
        Refusal(f"themes[0].definition ({TRAIN})", "source_wording")
    ]


def test_another_codebook_and_a_missing_bundle_are_refused(bundles) -> None:
    assert freeze(codebook_draft(codebook_version=1), bundles) == [
        Refusal("codebook", "wrong_codebook")
    ]
    del bundles[TRAIN]
    assert freeze(codebook_draft(), bundles) == [
        Refusal("discovery_corpus", "unknown_document")
    ]


def test_a_draft_without_its_fields_does_not_parse() -> None:
    draft = codebook_draft()
    draft["themes"][0]["exclusion_rules"] = []
    with pytest.raises(RecordError) as refused:
        parse(draft, CodebookDraft, "codebook.working.toml")
    assert refused.value.problems == (
        (
            "themes.0.exclusion_rules: Tuple should have at least 1 item after"
            " validation, not 0"
        ),
        "themes: Tuple should have at least 1 item after validation, not 0",
    )


def test_a_frozen_version_validates_and_needs_its_adr(bundles) -> None:
    codebook = freeze(codebook_draft(), bundles, APPROVAL)
    assert isinstance(codebook, Codebook)
    check = {"pin": PIN, "split": synthetic_split(), "bundles": bundles}
    adr = f"The codebook's content hash is {codebook.content_hash}."
    assert validate_codebook(codebook, adr_text=adr, **check) == []
    assert validate_codebook(codebook, adr_text="no hash", **check) == [
        Refusal("codebook.approval.adr", "adr_not_cited")
    ]
    draft = freeze(codebook_draft(), bundles)
    assert isinstance(draft, Codebook)
    assert validate_codebook(draft, adr_text=adr, **check) == [
        Refusal("codebook.status", "codebook_not_approved")
    ]


def test_a_tampered_version_is_refused(bundles) -> None:
    codebook = freeze(codebook_draft(), bundles, APPROVAL)
    assert isinstance(codebook, Codebook)
    adr = codebook.content_hash
    check = {"pin": PIN, "split": synthetic_split(), "bundles": bundles}
    theme = codebook.themes[0]
    (positive,) = theme.positive_examples
    moved = positive.pointer.model_copy(update={"event_id": DEV})
    tampered = codebook.model_copy(
        update={
            "themes": (
                theme.model_copy(
                    update={
                        "positive_examples": (
                            positive.model_copy(update={"pointer": moved}),
                        )
                    }
                ),
            )
        }
    )
    assert validate_codebook(tampered, adr_text=adr, **check) == [
        Refusal("codebook.content_hash", "content_hash_mismatch"),
        Refusal("theme demand.positive_examples[0]", "outside_training"),
    ]
