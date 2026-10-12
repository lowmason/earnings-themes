"""Dev's independent pass: the ledger, the guard's decision, and Stage 11's
verification (the Stage 6 spec, GS19, §The independent pass; the Stage 11 spec,
A6(3)).

- **The ledger.** ``evaluation/<corpus>/pilot-v<N>/independent-pass.toml`` holds
  one row per dev bundle: its event, the SHA-256 of the user's independent record,
  and the day it was recorded. It holds no text, and gains a row, committed on its
  own, before each dev bundle's drafting session starts.
- **The guard.** A dev bundle's draft is neither anchored nor shown until its
  record exists and matches its one ledger row, so no one sees a dev draft before
  the user's own reading is fixed. The application applies it to dev events only.
- **Verification.** Stage 11 checks each record against its ledger row and as a
  draft is checked, then anchors it and the kept draft in memory. The two readings
  are compared, and nothing anchored is written (FP16).

The gold brief does not let a drafting session read this module, and
``annotation``, which it may read, does not import it.
"""

from datetime import date
from pathlib import Path

from earnings_core.hashing import sha256_hex

from earnings_themes import tomlfile
from earnings_themes.anchoring import Bundle
from earnings_themes.annotation import (
    GoldDraft,
    IndependentRecord,
    Reading,
    anchor_reading,
    check_independent,
)
from earnings_themes.codebook import Codebook
from earnings_themes.problems import Problem, Refusal
from earnings_themes.records import IdPart, Part, Sha256Hex, ThemesRecord, parse

LEDGER = "independent-pass.toml"
"""The ledger's file name, in the pilot's evaluation directory."""

_FIRST = "the user's independent pass and its ledger row come first (GS19)"


class LedgerRow(Part):
    """One dev bundle's independent pass."""

    event_id: IdPart
    sha256: Sha256Hex
    recorded_on: date


class IndependentLedger(ThemesRecord):
    """``independent-pass.toml``: one row per dev bundle, written by hand."""

    rows: tuple[LedgerRow, ...] = ()


def load_ledger(path: Path) -> IndependentLedger:
    return parse(tomlfile.read(path), IndependentLedger, path.name)


_PHRASES = {
    Problem.NO_INDEPENDENT_RECORD: (
        f"is a dev bundle with no independent record: {_FIRST}"
    ),
    Problem.NO_LEDGER_ROW: (
        f"is a dev bundle whose independent record has no ledger row: {_FIRST}"
    ),
    Problem.REPEATED_LEDGER_ROW: "has more than one ledger row (GS19)",
    Problem.RECORD_LOST: (
        "has a ledger row but its independent record is lost; it is reported"
        " lost, never rewritten (GS19)"
    ),
    Problem.RECORD_CHANGED: (
        "has an independent record that does not match its ledger row; the"
        " record is never edited (GS19)"
    ),
}
"""The phrase ``ledger_problem`` prints for each of ``ledger_check``'s problems."""


def ledger_check(
    ledger: IndependentLedger | None, event_id: str, record: bytes | None
) -> Problem | None:
    """Why a dev bundle's draft may not be anchored or shown yet, or ``None`` when
    its record exists and matches its one ledger row. ``record`` is the independent
    record's bytes, ``None`` when it is absent, and ``ledger`` is ``None`` when none
    is committed.

    The event's ledger rows are read first, so a row whose record is gone is told
    apart from a pass not yet written: with no row, a missing record means the pass
    comes first, and a record without a row means the row comes first; two rows are
    refused whether or not the record exists; one row and no record is a lost
    record, reported and never rewritten; one row and a record that does not hash to
    it is a changed record."""
    rows = ledger.rows if ledger is not None else ()
    rows = [r for r in rows if r.event_id == event_id]
    if not rows:
        if record is None:
            return Problem.NO_INDEPENDENT_RECORD
        return Problem.NO_LEDGER_ROW
    if len(rows) > 1:
        return Problem.REPEATED_LEDGER_ROW
    if record is None:
        return Problem.RECORD_LOST
    if rows[0].sha256 != sha256_hex(record):
        return Problem.RECORD_CHANGED
    return None


def ledger_problem(
    ledger: IndependentLedger | None, event_id: str, record: bytes | None
) -> str | None:
    """``ledger_check``'s problem as the phrase that follows the event ID in a
    refusal, naming no text, or ``None``."""
    problem = ledger_check(ledger, event_id, record)
    return None if problem is None else _PHRASES[problem]


class IndependentReadings(Part):
    """A dev bundle's two readings, anchored in memory and never written: Stage 11's
    comparison figures are computed from them, and the anchored records stay local
    (the Stage 11 spec, A6(3), FP16)."""

    event_id: IdPart
    record: Reading
    draft: Reading


def verify_independent(
    event_id: str,
    *,
    ledger: IndependentLedger | None,
    record: bytes | None,
    drafted: GoldDraft,
    bundle: Bundle,
    codebook: Codebook,
) -> IndependentReadings | list[Refusal]:
    """A dev bundle's independent record checked against its one ledger row and by
    ``check_independent``, then it and the kept draft anchored over ``bundle`` in
    memory; or every reason they cannot be (P16-2(b); the Stage 11 spec, A6(3)).

    ``record`` is the record's bytes, ``None`` when it is absent, and ``ledger`` is
    ``None`` when none is committed. The bytes the row hashes are the bytes parsed,
    and only after they match. A record that does not read raises ``RecordError``,
    naming its problems, never its text. The kept draft's refusals are prefixed
    ``draft``. Nothing is written."""
    if {bundle.name, drafted.event_id} != {event_id}:
        return [Refusal("event_id", Problem.UNKNOWN_DOCUMENT)]
    if (problem := ledger_check(ledger, event_id, record)) is not None:
        return [Refusal("ledger", problem)]
    # ledger_check has refused an absent record, so ``record`` holds bytes here.
    parsed = parse(tomlfile.loads(record, "record"), IndependentRecord, "record")
    if refusals := check_independent(parsed, bundle=bundle, codebook=codebook):
        return refusals
    mine = anchor_reading(parsed, bundle, "")
    theirs = anchor_reading(drafted, bundle, "draft ")
    found = [r for side in (mine, theirs) if isinstance(side, list) for r in side]
    if found:
        return found
    return IndependentReadings(event_id=event_id, record=mine, draft=theirs)
