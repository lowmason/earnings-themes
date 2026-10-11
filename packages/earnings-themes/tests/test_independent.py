"""Dev's independent pass (the Stage 6 spec, GS19, §The independent pass): the
user's record takes the draft's form without a drafting aid and is checked as a
draft is; the wording guard reads its claims but never its quotes, which are the
release's own words. Synthetic text only (GS13)."""

from datetime import date

import pytest
from earnings_core.hashing import sha256_hex
from earnings_themes import tomlfile
from earnings_themes.annotation import (
    IndependentRecord,
    check_independent,
    load_independent,
    without_quotes,
)
from earnings_themes.independent import (
    LEDGER,
    IndependentLedger,
    LedgerRow,
    ledger_problem,
    load_ledger,
)
from earnings_themes.problems import Refusal
from earnings_themes.records import RecordError, parse
from earnings_themes.synthetic import DEV, LINES, TRAIN, build_synthetic, gold_draft
from earnings_themes.wording import WIDTH

INDEPENDENT = "Lowell Mason (independent pass)"


@pytest.fixture(scope="module")
def bundle():
    return build_synthetic(DEV).bundle


def record_data(**changes) -> dict:
    """``gold_draft`` over the synthetic dev bundle, signed, without its aid."""
    data = gold_draft(DEV)
    data.update({"annotator": INDEPENDENT, **changes})
    del data["drafting_aid"]
    return data


def record(**changes) -> IndependentRecord:
    return parse(record_data(**changes), IndependentRecord, "record")


def test_a_record_in_the_draft_s_form_checks_clean(bundle, codebook) -> None:
    assert check_independent(record(), bundle=bundle, codebook=codebook) == []


def test_a_record_has_no_drafting_aid_and_is_signed(tmp_path) -> None:
    with pytest.raises(RecordError):
        parse(gold_draft(DEV, annotator=INDEPENDENT), IndependentRecord, "record")
    with pytest.raises(RecordError):
        parse(record_data(annotator="   "), IndependentRecord, "record")
    path = tmp_path / "record.toml"
    path.write_text(tomlfile.dumps(record_data()), encoding="utf-8")
    assert load_independent(path) == record()


def test_a_record_for_another_event_is_refused(bundle, codebook) -> None:
    other = record(event_id=TRAIN)
    assert check_independent(other, bundle=bundle, codebook=codebook) == [
        Refusal("event_id", "unknown_document")
    ]


def _moved_quote() -> list[dict]:
    quotes = gold_draft(DEV)["quotes"]
    return [{**quotes[0], "text": "Words that are nowhere in it."}, *quotes[1:]]


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ({"no_theme": True}, Refusal("no_theme", "no_theme_mismatch")),
        (
            {
                "assignments": [
                    {"claim_id": "c1", "theme_id": "supply", "support": "supports"},
                    {"claim_id": "c2", "theme_id": "unmatched", "support": "uncertain"},
                ]
            },
            Refusal("assignment c1/supply", "unknown_theme"),
        ),
        ({"quotes": _moved_quote()}, Refusal("quote q1", "locator_not_found")),
    ],
)
def test_a_bad_record_is_refused_by_item(bundle, codebook, change, refusal) -> None:
    assert check_independent(record(**change), bundle=bundle, codebook=codebook) == [
        refusal
    ]


def test_the_wording_guard_reads_the_claims_never_the_quotes(bundle, codebook) -> None:
    """A quote is the release's own text, so the guard skips it; a claim that
    copies the same text is refused (D16-3)."""
    paragraph = LINES["paragraph"]
    assert len(paragraph) >= WIDTH
    quotes = [{"quote_id": "q1", "text": paragraph}]
    claim = {"claim_id": "c1", "quote_ids": ["q1"], "claim": "Demand rose widely."}
    assignments = [{"claim_id": "c1", "theme_id": "demand", "support": "supports"}]
    clean = record(
        quotes=quotes, claims=[claim], assignments=assignments, hard_negatives=[]
    )
    assert check_independent(clean, bundle=bundle, codebook=codebook) == []
    copied = record(
        quotes=quotes,
        claims=[{**claim, "claim": paragraph}],
        assignments=assignments,
        hard_negatives=[],
    )
    assert check_independent(copied, bundle=bundle, codebook=codebook) == [
        Refusal(f"claims[0].claim ({DEV})", "source_wording")
    ]
    assert without_quotes(copied).quotes == ()
    assert without_quotes(copied).claims == copied.claims


RECORD = b'event_id = "invented"\n'
COMES_FIRST = "the user's independent pass and its ledger row come first (GS19)"


def row(digest: str, event_id: str = DEV) -> LedgerRow:
    return LedgerRow(event_id=event_id, sha256=digest, recorded_on=date(2026, 10, 12))


@pytest.mark.parametrize(
    ("ledger", "found", "reason"),
    [
        (
            IndependentLedger(rows=(row(sha256_hex(RECORD)),)),
            None,
            f"is a dev bundle with no independent record: {COMES_FIRST}",
        ),
        (
            None,
            RECORD,
            (
                "is a dev bundle whose independent record has no ledger row:"
                f" {COMES_FIRST}"
            ),
        ),
        (
            IndependentLedger(rows=(row(sha256_hex(RECORD), TRAIN),)),
            RECORD,
            (
                "is a dev bundle whose independent record has no ledger row:"
                f" {COMES_FIRST}"
            ),
        ),
        (
            IndependentLedger(rows=(row(sha256_hex(RECORD)), row("0" * 64))),
            RECORD,
            "has more than one ledger row (GS19)",
        ),
        (
            IndependentLedger(rows=(row("0" * 64),)),
            RECORD,
            (
                "has an independent record that does not match its ledger row; the"
                " record is never edited (GS19)"
            ),
        ),
        (IndependentLedger(rows=(row(sha256_hex(RECORD)),)), RECORD, None),
    ],
)
def test_a_dev_draft_waits_for_a_record_that_matches_its_one_row(
    ledger, found, reason
) -> None:
    assert ledger_problem(ledger, DEV, found) == reason


def test_the_ledger_reads_as_rows_of_hashes(tmp_path) -> None:
    path = tmp_path / LEDGER
    digest = sha256_hex(RECORD)
    data = {
        "rows": [{"event_id": DEV, "sha256": digest, "recorded_on": date(2026, 10, 12)}]
    }
    path.write_text(tomlfile.dumps(data), encoding="utf-8")
    assert load_ledger(path) == IndependentLedger(rows=(row(digest),))
    path.write_text("rows = [\n", encoding="utf-8")
    with pytest.raises(RecordError):
        load_ledger(path)
    path.write_text(
        tomlfile.dumps({"rows": [{**data["rows"][0], "sha256": "X"}]}), encoding="utf-8"
    )
    with pytest.raises(RecordError):
        load_ledger(path)
