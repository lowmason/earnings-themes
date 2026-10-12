"""Dev's independent pass: the ledger and the guard's decision (the Stage 6 spec,
GS19, §The independent pass).

- **The ledger.** ``evaluation/<corpus>/pilot-v<N>/independent-pass.toml`` holds
  one row per dev bundle: its event, the SHA-256 of the user's independent record,
  and the day it was recorded. It holds no text, and gains a row, committed on its
  own, before each dev bundle's drafting session starts.
- **The guard.** A dev bundle's draft is neither anchored nor shown until its
  record exists and matches its one ledger row, so no one sees a dev draft before
  the user's own reading is fixed. The application applies it to dev events only.

The gold brief does not let a drafting session read this module, and
``annotation``, which it may read, does not import it.
"""

from datetime import date
from pathlib import Path

from earnings_core.hashing import sha256_hex

from earnings_themes import tomlfile
from earnings_themes.problems import Problem
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
