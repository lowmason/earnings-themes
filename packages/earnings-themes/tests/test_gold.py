"""The gold contract (the Stage 6 spec, §The gold): the build anchors every quote
and derives every origin, and the validator refuses each problem by item and
reason, never by text."""

import pytest
from earnings_themes.annotation import (
    CuratedDraft,
    GoldDraft,
    build_curated,
    build_gold,
    signed,
    validate_curated,
    validate_gold,
)
from earnings_themes.gold import (
    Gold,
    HardNegativeSet,
    Origin,
    gold_toml,
    load_gold,
    load_hard_negatives,
)
from earnings_themes.problems import Refusal
from earnings_themes.records import RecordError, parse
from earnings_themes.split import Partition
from earnings_themes.synthetic import (
    DEV,
    LATER,
    PIN,
    TEST,
    TRAIN,
    build_synthetic,
    curated_draft,
    gold_draft,
    synthetic_split,
)

SIGNED = "Lowell Mason (verified a Claude draft)"


@pytest.fixture(scope="module")
def bundles():
    return {e: build_synthetic(e).bundle for e in (TRAIN, DEV, TEST, LATER)}


def build(bundles, codebook, drafted: dict, working: dict | None = None):
    return build_gold(
        parse(drafted, GoldDraft, "draft"),
        parse(working or drafted, GoldDraft, "working"),
        bundle=bundles[drafted["event_id"]],
        pin=PIN,
        split=synthetic_split(),
        codebook=codebook,
    )


def check(gold: Gold, bundles, codebook, **options):
    return validate_gold(
        gold,
        bundle=bundles[gold.event_id],
        pin=PIN,
        split=synthetic_split(),
        codebook=codebook,
        **options,
    )


def test_an_accepted_draft_builds_unsigned_and_fails_only_on_its_signature(
    bundles, codebook
) -> None:
    gold = build(bundles, codebook, gold_draft())
    assert isinstance(gold, Gold)
    assert gold.partition is Partition.TRAIN
    assert gold.document_id == f"{TRAIN}:release"
    assert gold.annotator == ""
    assert {item.origin for item in (*gold.quotes, *gold.claims)} == {
        Origin.DRAFTED_ACCEPTED
    }
    assert gold.counts.model_dump() == {
        "accepted": 8,
        "edited": 0,
        "rejected": 0,
        "added": 0,
    }
    assert check(gold, bundles, codebook) == [Refusal("annotator", "unsigned")]


def test_origins_come_from_comparing_the_working_copy_with_the_draft(
    bundles, codebook
) -> None:
    drafted = gold_draft()
    working = gold_draft(annotator=SIGNED)
    working["claims"][1]["claim"] = "Margins were flat, in the user's words."
    del working["hard_negatives"][0]
    working["quotes"].append({"quote_id": "q4", "text": "Quarterly results"})
    working["claims"].append(
        {"claim_id": "c3", "quote_ids": ["q3", "q4"], "claim": "A heading."}
    )
    working["assignments"].append(
        {"claim_id": "c3", "theme_id": "unmatched", "support": "uncertain"}
    )
    gold = build(bundles, codebook, drafted, working)
    assert isinstance(gold, Gold)
    assert gold.counts.model_dump() == {
        "accepted": 6,
        "edited": 1,
        "rejected": 1,
        "added": 3,
    }
    assert gold.claims[1].origin is Origin.DRAFTED_EDITED
    assert gold.quotes[3].origin is Origin.ANNOTATOR_ADDED
    assert check(gold, bundles, codebook) == []


def test_a_signed_file_round_trips_and_holds_no_quote(
    bundles, codebook, tmp_path
) -> None:
    gold = build(bundles, codebook, gold_draft(annotator=SIGNED))
    assert isinstance(gold, Gold)
    path = tmp_path / f"{TRAIN}.toml"
    path.write_text(gold_toml(gold), encoding="utf-8")
    assert load_gold(path) == gold
    text = path.read_text(encoding="utf-8")
    assert "Margins held steady" not in text
    assert "Revenue grew" not in text


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ({"no_theme": True}, Refusal("no_theme", "no_theme_mismatch")),
        (
            {"quotes": [{"quote_id": "q1", "text": "Region Sales"}]},
            Refusal("quote q1", "not_narrative"),
        ),
        (
            {"quotes": [{"quote_id": "q1", "text": "Revenue grew in every region."}]},
            Refusal("quote q1", "ambiguous_occurrence"),
        ),
        (
            {"quotes": [{"quote_id": "q1", "text": "Scanned text from an image."}]},
            Refusal("quote q1", "ocr_derived_text"),
        ),
    ],
)
def test_a_bad_draft_is_refused_by_item(bundles, codebook, change, refusal) -> None:
    draft = gold_draft(**change)
    if "quotes" in change:
        draft.update(claims=[], assignments=[], hard_negatives=[], no_theme=True)
    assert build(bundles, codebook, draft) == [refusal]


def test_ids_themes_and_ties_are_checked(bundles, codebook, fixtures) -> None:
    """Every ID resolves, every claim takes an assignment row, and every quote is
    cited, in a bundle's gold and in each fixture of the curated set (R9.9; plan
    10)."""
    draft = gold_draft(no_theme=True)
    draft["quotes"].append({"quote_id": "q4", "text": "Quarterly results"})
    draft["claims"].append({"claim_id": "c1", "quote_ids": ["q9"], "claim": "Again."})
    draft["claims"].append({"claim_id": "c3", "quote_ids": ["q1"], "claim": "Uncoded."})
    draft["assignments"] = [
        {
            "claim_id": "c1",
            "theme_id": "pricing",
            "support": "uncertain",
            "tie_group": "t1",
        },
        {
            "claim_id": "c2",
            "theme_id": "unmatched",
            "support": "uncertain",
            "tie_group": "t1",
        },
        {"claim_id": "c9", "theme_id": "unmatched", "support": "uncertain"},
    ]
    assert build(bundles, codebook, draft) == [
        Refusal("claim c1", "duplicate_id"),
        Refusal("claim c1", "unknown_quote"),
        Refusal("quote q4", "unreferenced"),
        Refusal("assignment c1/pricing", "unknown_theme"),
        Refusal("assignment c9/unmatched", "unknown_claim"),
        Refusal("claim c3", "unreferenced"),
        Refusal("tie_group t1", "tie_group"),
    ]

    curated = curated_draft(fixtures)
    first = curated["documents"][0]
    first["hard_negatives"][1]["quote_ids"] = ["q1"]
    parsed = parse(curated, CuratedDraft, "curated")
    refusals = build_curated(
        parsed, parsed, bundles=fixtures, pin=PIN, codebook=codebook
    )
    assert refusals == [Refusal(f"{first['fixture_id']} quote q2", "unreferenced")]

    good = parse(curated_draft(fixtures, SIGNED), CuratedDraft, "curated")
    record = build_curated(good, good, bundles=fixtures, pin=PIN, codebook=codebook)
    assert isinstance(record, HardNegativeSet)
    first_id = record.documents[0].fixture_id
    repeated = good.model_copy(
        update={"documents": (*good.documents, good.documents[0])}
    )
    refusals = build_curated(
        good, repeated, bundles=fixtures, pin=PIN, codebook=codebook
    )
    assert refusals == [Refusal(first_id, "duplicate_id")]
    others = {name: bundle for name, bundle in fixtures.items() if name != first_id}
    refusals = validate_curated(record, bundles=others, pin=PIN, codebook=codebook)
    assert refusals == [Refusal(first_id, "unknown_document")]
    moved = record.documents[0].model_copy(update={"doc_id": "other@walker-1#0"})
    tampered = record.model_copy(update={"documents": (moved, *record.documents[1:])})
    refusals = validate_curated(tampered, bundles=fixtures, pin=PIN, codebook=codebook)
    assert refusals == [Refusal(f"{first_id} doc_id", "wrong_document")]


def test_a_claim_that_copies_the_release_is_refused(bundles, codebook) -> None:
    draft = gold_draft()
    draft["claims"][0]["claim"] = (
        "Per the release, Revenue grew in every region. Margins held steady."
    )
    assert build(bundles, codebook, draft) == [
        Refusal(f"claims[0].claim ({TRAIN})", "source_wording")
    ]


def test_another_document_pin_split_codebook_or_partition_is_refused(
    bundles, codebook
) -> None:
    gold = build(bundles, codebook, gold_draft(annotator=SIGNED))
    assert isinstance(gold, Gold)
    tampered = gold.model_copy(
        update={
            "pin": PIN.model_copy(update={"pilot_hash": "4" * 64}),
            "split_hash": "5" * 64,
            "partition": Partition.DEV,
            "codebook": gold.codebook.model_copy(update={"codebook_version": 1}),
            "doc_id": "other@walker-1#0000000000000000",
            "canonical_hash": "6" * 64,
        }
    )
    assert check(tampered, bundles, codebook) == [
        Refusal("doc_id", "wrong_document"),
        Refusal("canonical_hash", "canonical_hash_mismatch"),
        Refusal("pin", "wrong_pin"),
        Refusal("split_hash", "wrong_split"),
        Refusal("partition", "wrong_partition"),
        Refusal("codebook", "wrong_codebook"),
    ]


def test_an_excluded_event_takes_no_gold(bundles, codebook) -> None:
    assert build(bundles, codebook, gold_draft(LATER)) == [
        Refusal("partition", "excluded_event")
    ]


def test_counts_that_disagree_with_the_origins_are_refused(bundles, codebook) -> None:
    gold = build(bundles, codebook, gold_draft(annotator=SIGNED))
    assert isinstance(gold, Gold)
    tampered = gold.model_copy(
        update={"counts": gold.counts.model_copy(update={"accepted": 7})}
    )
    assert check(tampered, bundles, codebook) == [Refusal("counts", "counts_mismatch")]


def curated(fixtures, signed: bool = True) -> CuratedDraft:
    """Hard negatives over two Stage 1 fixtures, their quotes taken from each
    fixture's own unique narrative sentences, never typed here."""
    draft = curated_draft(fixtures, SIGNED if signed else "")
    return parse(draft, CuratedDraft, "curated")


def test_curated_hard_negatives_over_stage_1_fixtures_validate(
    fixtures, codebook, tmp_path
) -> None:
    draft = curated(fixtures)
    record = build_curated(draft, draft, bundles=fixtures, pin=PIN, codebook=codebook)
    assert isinstance(record, HardNegativeSet)
    assert record.pin == PIN
    assert validate_curated(record, bundles=fixtures, pin=PIN, codebook=codebook) == []
    path = tmp_path / "hard-negatives.toml"
    path.write_text(gold_toml(record), encoding="utf-8")
    assert load_hard_negatives(path) == record


def test_curated_hard_negatives_need_every_kind_and_a_signature(
    fixtures, codebook
) -> None:
    draft = curated(fixtures, signed=False)
    record = build_curated(draft, draft, bundles=fixtures, pin=PIN, codebook=codebook)
    assert isinstance(record, HardNegativeSet)
    assert validate_curated(record, bundles=fixtures, pin=PIN, codebook=codebook) == [
        Refusal("annotator", "unsigned")
    ]
    narrowed = record.model_copy(update={"documents": record.documents[:1]})
    assert Refusal("hard_negatives", "negative_kinds") in validate_curated(
        narrowed,
        bundles=fixtures,
        pin=PIN,
        codebook=codebook,
        require_signature=False,
    )


def test_curated_hard_negatives_carry_the_pin(fixtures, codebook) -> None:
    """The Stage 6 spec, §The pin: every Stage 6 record carries it, the curated
    hard negatives too, though they belong to no partition."""
    draft = curated(fixtures)
    record = build_curated(draft, draft, bundles=fixtures, pin=PIN, codebook=codebook)
    assert isinstance(record, HardNegativeSet)
    other = PIN.model_copy(update={"pilot_hash": "4" * 64})
    assert validate_curated(record, bundles=fixtures, pin=other, codebook=codebook) == [
        Refusal("pin", "wrong_pin")
    ]


def test_a_blank_signature_is_not_a_signature(bundles, codebook) -> None:
    """P9-18: signed means not blank, whitespace included, wherever it is asked."""
    assert [signed(name) for name in ("", "   ", SIGNED)] == [False, False, True]
    gold = build(bundles, codebook, gold_draft(annotator="   "))
    assert isinstance(gold, Gold)
    assert check(gold, bundles, codebook) == [Refusal("annotator", "unsigned")]


def test_a_theme_id_that_is_not_an_id_is_refused_by_its_field() -> None:
    """A refusal names a theme by its ID, so a theme_id is an ID: a phrase in
    its place is refused by field path, never echoed (GS13)."""
    draft = gold_draft()
    draft["assignments"][0]["theme_id"] = "Demand rose in every region"
    with pytest.raises(RecordError) as caught:
        parse(draft, GoldDraft, "draft")
    assert caught.value.problems[0].startswith("assignments.0.theme_id: ")
    assert "Demand" not in str(caught.value)
