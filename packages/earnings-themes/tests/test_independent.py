"""Dev's independent pass (the Stage 6 spec, GS19, §The independent pass): the
user's record takes the draft's form without a drafting aid and is checked as a
draft is; the wording guard reads its claims but never its quotes, which are the
release's own words. Synthetic text only (GS13)."""

from datetime import date

import pytest
from earnings_core.hashing import sha256_hex
from earnings_themes import tomlfile
from earnings_themes.annotation import (
    GoldDraft,
    IndependentRecord,
    check_independent,
    load_independent,
    without_quotes,
)
from earnings_themes.codebook import CodebookStatus
from earnings_themes.gold import Origin
from earnings_themes.independent import (
    LEDGER,
    IndependentLedger,
    IndependentReadings,
    LedgerRow,
    ledger_check,
    ledger_problem,
    load_ledger,
    verify_independent,
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


def test_a_record_under_a_codebook_that_is_not_approved_is_refused(
    bundle, codebook
) -> None:
    """P16-2(a): refused as ``validate_gold`` refuses it, and nothing else is
    checked (the Stage 11 spec, A6(2))."""
    unapproved = codebook.model_copy(
        update={"status": CodebookStatus.DRAFT, "approval": None}
    )
    assert check_independent(
        record(no_theme=True), bundle=bundle, codebook=unapproved
    ) == [Refusal("codebook", "codebook_not_approved")]


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
            (
                "has a ledger row but its independent record is lost; it is reported"
                " lost, never rewritten (GS19)"
            ),
        ),
        (None, None, f"is a dev bundle with no independent record: {COMES_FIRST}"),
        (
            IndependentLedger(rows=(row(sha256_hex(RECORD), TRAIN),)),
            None,
            f"is a dev bundle with no independent record: {COMES_FIRST}",
        ),
        (
            IndependentLedger(rows=(row(sha256_hex(RECORD)), row("0" * 64))),
            None,
            "has more than one ledger row (GS19)",
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


def test_a_ledger_row_has_no_free_text_field(tmp_path) -> None:
    """The ledger holds an event, a hash, and a day, and nothing else (GS3)."""
    path = tmp_path / LEDGER
    data = {
        "rows": [
            {
                "event_id": DEV,
                "sha256": sha256_hex(RECORD),
                "recorded_on": date(2026, 10, 12),
                "note": "x",
            }
        ]
    }
    path.write_text(tomlfile.dumps(data), encoding="utf-8")
    with pytest.raises(RecordError):
        load_ledger(path)


@pytest.mark.parametrize(
    ("ledger", "found", "problem"),
    [
        (None, None, "no_independent_record"),
        (IndependentLedger(), None, "no_independent_record"),
        (None, RECORD, "no_ledger_row"),
        (
            IndependentLedger(rows=(row(sha256_hex(RECORD), TRAIN),)),
            RECORD,
            "no_ledger_row",
        ),
        (
            IndependentLedger(rows=(row(sha256_hex(RECORD)), row("0" * 64))),
            None,
            "repeated_ledger_row",
        ),
        (IndependentLedger(rows=(row(sha256_hex(RECORD)),)), None, "record_lost"),
        (IndependentLedger(rows=(row("0" * 64),)), RECORD, "record_changed"),
        (IndependentLedger(rows=(row(sha256_hex(RECORD)),)), RECORD, None),
    ],
)
def test_the_ledger_check_names_each_problem(ledger, found, problem) -> None:
    """The guard's decision as a ``Problem``, which a refusal can carry; the phrases
    ``ledger_problem`` prints are unchanged (the Stage 11 spec, A6(3))."""
    assert ledger_check(ledger, DEV, found) == problem


DATA = tomlfile.dumps(record_data()).encode()
"""The synthetic dev bundle's independent record, as the user's file holds it."""
BROKEN = b"claim = 'Demand rose widely\n"
"""Bytes that are not TOML, holding a phrase a refusal must never print."""


def drafted(**changes) -> GoldDraft:
    """The synthetic dev bundle's kept draft."""
    return parse(gold_draft(DEV, **changes), GoldDraft, "draft")


def verify(bundle, codebook, data: bytes, **changes):
    """``verify_independent`` over the synthetic dev bundle, with the kept draft and
    a ledger whose one row holds ``data``'s hash; ``changes`` replace the ledger,
    the record or the draft, and may name another ``event_id``. Another codebook is
    passed positionally: ``codebook`` is a parameter here."""
    arguments = {
        "ledger": IndependentLedger(rows=(row(sha256_hex(data)),)),
        "record": data,
        "drafted": drafted(),
        "bundle": bundle,
        "codebook": codebook,
        **changes,
    }
    event_id = arguments.pop("event_id", DEV)
    return verify_independent(event_id, **arguments)


def test_a_matching_record_and_the_kept_draft_are_anchored_in_memory(
    bundle, codebook
) -> None:
    """P16-2(b), the Stage 11 spec's A6(3): the record matches its one ledger row
    and checks clean, so it and the kept draft are anchored, the record's items as
    the user's own and the draft's as drafted. Here the record copies the draft, so
    both point at the same spans."""
    readings = verify(bundle, codebook, DATA)
    assert isinstance(readings, IndependentReadings)
    assert readings.event_id == DEV
    mine, theirs = readings.record, readings.draft

    def origins(reading) -> set[Origin]:
        items = (
            *reading.quotes,
            *reading.claims,
            *reading.assignments,
            *reading.hard_negatives,
        )
        return {item.origin for item in items}

    assert origins(mine) == {Origin.ANNOTATOR_ADDED}
    assert origins(theirs) == {Origin.DRAFTED_ACCEPTED}
    assert [q.model_dump(exclude={"origin"}) for q in mine.quotes] == [
        q.model_dump(exclude={"origin"}) for q in theirs.quotes
    ]
    sizes = (
        len(mine.quotes),
        len(mine.claims),
        len(mine.assignments),
        len(mine.hard_negatives),
    )
    assert sizes == (3, 2, 2, 1)
    assert (mine.no_theme, theirs.no_theme) == (False, False)


@pytest.mark.parametrize(
    ("ledger", "found", "problem"),
    [
        (None, None, "no_independent_record"),
        (None, DATA, "no_ledger_row"),
        (IndependentLedger(rows=(row(sha256_hex(DATA)),)), None, "record_lost"),
        (IndependentLedger(rows=(row("0" * 64),)), BROKEN, "record_changed"),
    ],
)
def test_a_record_that_does_not_match_its_ledger_is_never_parsed(
    bundle, codebook, ledger, found, problem
) -> None:
    """The ledger is checked before the record is read: bytes that do not match
    their row are refused as the ledger's problem, even when they are not TOML."""
    assert verify(bundle, codebook, DATA, ledger=ledger, record=found) == [
        Refusal("ledger", problem)
    ]


def test_a_record_that_does_not_read_is_named_never_quoted(bundle, codebook) -> None:
    with pytest.raises(RecordError) as refused:
        verify(bundle, codebook, BROKEN)
    assert refused.value.problems == ("not TOML at line 2, column 1",)
    assert "Demand" not in str(refused.value)


def test_the_record_is_checked_before_either_reading(bundle, codebook) -> None:
    mismatched = tomlfile.dumps(record_data(no_theme=True)).encode()
    assert verify(bundle, codebook, mismatched) == [
        Refusal("no_theme", "no_theme_mismatch")
    ]
    unapproved = codebook.model_copy(
        update={"status": CodebookStatus.DRAFT, "approval": None}
    )
    assert verify(bundle, unapproved, DATA) == [
        Refusal("codebook", "codebook_not_approved")
    ]


def test_a_kept_draft_that_does_not_anchor_is_refused_by_item(bundle, codebook) -> None:
    moved = drafted(quotes=_moved_quote())
    assert verify(bundle, codebook, DATA, drafted=moved) == [
        Refusal("draft quote q1", "locator_not_found")
    ]
    twice = gold_draft(DEV)
    twice["quotes"].append(dict(twice["quotes"][0]))
    repeated = parse(twice, GoldDraft, "draft")
    assert verify(bundle, codebook, DATA, drafted=repeated) == [
        Refusal("draft quote q1", "duplicate_id")
    ]


def test_another_event_s_bundle_or_draft_is_refused(bundle, codebook) -> None:
    assert verify(bundle, codebook, DATA, event_id=TRAIN) == [
        Refusal("event_id", "unknown_document")
    ]
    other = parse(gold_draft(TRAIN), GoldDraft, "draft")
    assert verify(bundle, codebook, DATA, drafted=other) == [
        Refusal("event_id", "unknown_document")
    ]
