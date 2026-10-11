# Dev's Independent Pass: Check and Guard (GS19) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the two code changes GS19 needs before any dev gold bundle is drafted: `gold anchor <event> --independent --check`, which checks the user's independent record of a dev bundle and prints its SHA-256, and a guard that stops `gold anchor` and `gold show` from touching a dev bundle's draft until that record matches its ledger row.

**Architecture:**
- **`earnings-themes`:** gains the record's contract and check in `annotation.py`, beside the draft contract they share helpers with. The ledger contract and the guard's pure decision go in a new module, `independent.py`. `annotation.py` is one of the six modules the gold brief lets a drafting session read; `independent.py` is not, and `annotation.py` must not import it.
- **The application (`apps/earnings-pipeline/.../gold_cli.py`):** reads the files, wires the `--independent` flag, and applies the guard. It looks the partition up first, so a train or test event never reads the ledger or the record.

**Tech Stack:** Python ≥3.14 uv workspace; Pydantic v2 (strict, frozen `Part` models); Typer; pytest; Ruff. No new dependency.

**Spec:**
- `specs/completed/pilot-codebook-split-and-gold-set-protocol.md`: GS19 and §The independent pass (amended 2026-10-11, PR #15).
- The backlog item `GS19 — Independent-pass check and dev guard` in `specs/deferred_items.md`.

> Roadmap: none. This closes a deferred item for Stage 6's spec, which is already complete and retired. On completion, do **not** move the spec again.

## Global Constraints

- **GS13, blinding.**
  - The executing session never opens pilot text or any file under the main checkout's `data/`.
  - Execute in a fresh worktree, which has no `data/` at all.
  - Tests use only the synthetic layer's invented text and Stage 1's committed fixtures.
  - No command prints a document's text. `test_stage6_cli.py`'s `quiet()` enforces this for every CLI call.
- **GS3, the public repository.** Committed files hold IDs, offsets, labels and hashes, never release text. The ledger holds no text and no free-text field.
- **GS17, units.** `earnings-themes` imports only `earnings-core`. Ingestion and themes never import each other. `annotation.py` must not import `earnings_themes.independent`.
- **Train and test are unchanged.** Only a dev event reads the ledger or the record. A train event anchors and shows exactly as before, even when the ledger is missing or malformed.
- **Refusals** name the event and the reason only, never text. They stop with exit code 1 and write nothing.
- **Agent verification scope.** The executor runs only these, in the worktree:
  - `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_independent.py -q`
  - `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/test_import_boundaries.py -q`
  - `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q`
  - `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`
  - `uv run --locked ruff check .` and `uv run --locked ruff format --check .`

  The executor never runs the root suite, the Stage 6 wording test (`tests/integration/test_stage6_wording.py`), `-m live`, or `-m browser`. Never pass `--tb=long`. Those are the user's (Task 5).
- **Data dictionary.** Every new model is documented in `docs/data-dictionary.md` and registered in `MODELS` of `tests/contracts/test_data_dictionary.py`, in the same task (AGENTS.md §191).
- **Fixed strings.**
  - Record `data/runs/gold/independent/<file>.toml`, where `<file>` is the event ID with its colon as an underscore.
  - Ledger `evaluation/<corpus>/pilot-v<N>/independent-pass.toml`.
  - Record signature `Lowell Mason (independent pass)`.

## Decisions this plan takes

Neither the spec nor the backlog item fixes these.

- **D16-1, the hash.** `--independent --check` prints the record's SHA-256 (`earnings_core.hashing.sha256_hex` over the file's bytes). It equals `shasum -a 256`'s output, so the user can copy it into the ledger.
- **D16-2, order.** `--independent --check` refuses when the bundle's draft, working copy, anchored file or view already exists. GS19 says none exists when the record is written; this is the one point at which code can confirm that.
- **D16-3, wording.** The record's quotes are the release's own words, so the wording guard reads the record without its quotes, through `without_quotes`. Every other string is the user's and is checked as a draft's is.
- **D16-4, partition.** The library check takes no partition. The application refuses `--independent` for any event that is not dev.
- **D16-5, a synthetic dev event in CLI tests.** The CLI tests' synthetic pilot has no dev event: each invented issuer's first event is in train and its later ones are excluded (GS6). The CLI tests therefore patch `SplitManifest.partition_of` to read `FIRST` as dev, *after* `frozen(repo)` has frozen codebook v0. The library tests use `earnings_themes.synthetic.DEV`, a real invented dev bundle.

## File structure

| File | Change | Responsibility |
| --- | --- | --- |
| `packages/earnings-themes/src/earnings_themes/annotation.py` | Modify | `IndependentRecord`, `load_independent`, `check_independent`, `without_quotes`; `_items` accepts the record |
| `packages/earnings-themes/src/earnings_themes/independent.py` | Create | `LEDGER`, `LedgerRow`, `IndependentLedger`, `load_ledger`, `ledger_problem` |
| `packages/earnings-themes/tests/test_independent.py` | Create | Library tests for both modules' new code |
| `apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py` | Modify | `--independent --check`, the guard on `anchor` and `show`, the docstring |
| `apps/earnings-pipeline/tests/test_stage6_cli.py` | Modify | CLI tests: the check, the guard, train unchanged |
| `docs/data-dictionary.md` | Modify | Three model sections; §Stage 6 files |
| `tests/contracts/test_data_dictionary.py` | Modify | Register three models |
| `specs/deferred_items.md` | Modify (Task 5) | Tick the GS19 item |

## Setup (before Task 1)

The planning session commits this plan as the first commit of branch `gs19-independent-pass-check`, cut from `main` at `2169fcd`. Execution checks that branch out in a worktree:

```bash
cd /Users/lowell/Projects/earnings-themes
git switch main
git worktree add .claude/worktrees/gs19-independent-pass-check gs19-independent-pass-check
cd .claude/worktrees/gs19-independent-pass-check
uv sync --locked --all-packages --group dev
```

Expected:
- the worktree exists, on `gs19-independent-pass-check`;
- `git log --oneline -2` shows the plan's commit above `2169fcd`;
- `specs/plans/16-pilot-codebook-split-and-gold-set-protocol.md` is present;
- there is no `data/` directory.

Every later command runs from the worktree's root.

---

### Task 1: The independent record's contract and check (library)

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/annotation.py`
- Create: `packages/earnings-themes/tests/test_independent.py`
- Modify: `docs/data-dictionary.md` (a new section after `### \`CuratedDraft\``)
- Modify: `tests/contracts/test_data_dictionary.py` (`MODELS`)

**Interfaces:**
- Consumes: from `annotation.py` itself, `QuoteDraft`, `ClaimDraft`, `AssignmentDraft`, `HardNegativeDraft`, `_items`, `_Origins`, `_ids`, `_pointers`, `_wording`; from `earnings_themes.gold`, `ReleaseIdentification` and `no_theme_of`; from `earnings_themes.anchoring`, `Bundle`; from `earnings_themes.codebook`, `Codebook`.
- Produces:
  - `class IndependentRecord(Part)`, with fields `event_id`, `annotator` (NonBlank), `no_theme`, `release_identification`, `quotes`, `claims`, `assignments` and `hard_negatives`, and no `drafting_aid`.
  - `load_independent(path: Path) -> IndependentRecord`
  - `check_independent(record: IndependentRecord, *, bundle: Bundle, codebook: Codebook) -> list[Refusal]`
  - `without_quotes(record: IndependentRecord) -> IndependentRecord`

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/test_independent.py`:

```python
"""Dev's independent pass (the Stage 6 spec, GS19, §The independent pass): the
user's record takes the draft's form without a drafting aid and is checked as a
draft is; the wording guard reads its claims but never its quotes, which are the
release's own words. Synthetic text only (GS13)."""

import pytest
from earnings_themes import tomlfile
from earnings_themes.annotation import (
    IndependentRecord,
    check_independent,
    load_independent,
    without_quotes,
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
    data = gold_draft(DEV, annotator=INDEPENDENT, **changes)
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


def test_the_wording_guard_reads_the_claims_never_the_quotes(
    bundle, codebook
) -> None:
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
```

The `codebook` fixture comes from `packages/earnings-themes/tests/conftest.py`. It is the synthetic codebook, approved, whose one theme is `demand`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_independent.py -q`
Expected: collection fails with `ImportError: cannot import name 'IndependentRecord' from 'earnings_themes.annotation'`.

- [ ] **Step 3: Implement the contract and check in `annotation.py`**

Add the model directly after `class GoldDraft`:

```python
class IndependentRecord(Part):
    """``data/runs/gold/independent/<event>.toml``: the user's own reading of a dev
    bundle, written before its draft exists, in the draft's form without a drafting
    aid (the Stage 6 spec, GS19). Never committed, and never edited once its
    ledger row is."""

    event_id: IdPart
    annotator: NonBlank
    no_theme: bool
    release_identification: ReleaseIdentification
    quotes: tuple[QuoteDraft, ...] = ()
    claims: tuple[ClaimDraft, ...] = ()
    assignments: tuple[AssignmentDraft, ...] = ()
    hard_negatives: tuple[HardNegativeDraft, ...] = ()
```

Add the loader directly after `load_curated_draft`:

```python
def load_independent(path: Path) -> IndependentRecord:
    return parse(tomlfile.read(path), IndependentRecord, path.name)
```

Change `_items` so it takes the record. Replace its signature's two parameter annotations and its claims-branch condition. The rest of the function is unchanged:

```python
def _items(
    drafted: GoldDraft | IndependentRecord | FixtureDraft,
    working: GoldDraft | IndependentRecord | FixtureDraft,
    bundle: Bundle,
    origins: _Origins,
    prefix: str,
) -> tuple[dict[str, tuple], list[Refusal]]:
```

and replace

```python
    if isinstance(working, GoldDraft) and isinstance(drafted, GoldDraft):
```

with

```python
    if not isinstance(working, FixtureDraft) and not isinstance(drafted, FixtureDraft):
```

Add the check and its helper directly after `build_gold`:

```python
def without_quotes(record: IndependentRecord) -> IndependentRecord:
    """``record`` with no quote: what the wording guard reads, since a quote is the
    release's own text and every other string is the user's (GS3, F20)."""
    return record.model_copy(update={"quotes": ()})


def check_independent(
    record: IndependentRecord, *, bundle: Bundle, codebook: Codebook
) -> list[Refusal]:
    """Every reason ``record`` does not hold over ``bundle``; empty when it does
    (GS19). A draft's checks, with no origins, partition, or signature to wait for:
    each quote anchored, the IDs, themes, ties, and ``no_theme``, and the wording
    guard over every string but the quotes."""
    if record.event_id != bundle.name:
        return [Refusal("event_id", Problem.UNKNOWN_DOCUMENT)]
    made, refusals = _items(record, record, bundle, _Origins(), "")
    if refusals:
        return refusals
    if record.no_theme != no_theme_of(made["assignments"]):
        refusals.append(Refusal("no_theme", Problem.NO_THEME_MISMATCH))
    refusals += _ids(
        made["quotes"],
        made["claims"],
        made["assignments"],
        made["hard_negatives"],
        codebook.theme_ids(),
        "",
    )
    refusals += _pointers(made["quotes"], bundle, "")
    return refusals + _wording(without_quotes(record), {bundle.name: bundle})
```

Update the module docstring's first bullet. Replace `- **Drafts.** A drafting session writes ``<name>.draft.toml``, which is kept` … through `by their text, with context when the text repeats.` with:

```text
- **Drafts.** A drafting session writes ``<name>.draft.toml``, which is kept
  unchanged, and the user edits ``<name>.working.toml`` beside it. Both name quotes
  by their text, with context when the text repeats. A dev bundle's independent
  record (GS19) takes the same form, without a drafting aid, and is checked, never
  built.
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_independent.py packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/test_import_boundaries.py -q`
Expected: all pass. `test_gold.py` passing shows the `_items` change left drafts unchanged.

- [ ] **Step 5: Document and register the model**

In `docs/data-dictionary.md`, insert this section after the `### \`CuratedDraft\`` table, directly before `## Stage 6 files`:

```markdown
### `IndependentRecord`

`data/runs/gold/independent/<event>.toml`: the user's own reading of a dev bundle,
written before its draft exists; never committed, and never edited once its ledger
row is (GS19).

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | The bundle's event |
| `annotator` | string | The user's signature; never blank |
| `no_theme` | bool | As `Gold` |
| `release_identification` | `ReleaseIdentification` | As `Gold` |
| `quotes` | tuple of `QuoteDraft` | Quotes, by text |
| `claims` | tuple of `ClaimDraft` | Claims |
| `assignments` | tuple of `AssignmentDraft` | Assignments |
| `hard_negatives` | tuple of `HardNegativeDraft` | Hard-negative claims; optional |
```

In `tests/contracts/test_data_dictionary.py`, add `annotation.IndependentRecord,` to `MODELS` directly after `annotation.CuratedDraft,`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`
Expected: all pass, including `test_every_field_is_documented[IndependentRecord]`.

- [ ] **Step 6: Lint and commit**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
git add packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/tests/test_independent.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(themes): check a dev bundle's independent record (GS19)"
```

---

### Task 2: The ledger and the guard's decision (library)

**Files:**
- Create: `packages/earnings-themes/src/earnings_themes/independent.py`
- Modify: `packages/earnings-themes/tests/test_independent.py` (append)
- Modify: `docs/data-dictionary.md` (two sections after `IndependentRecord`; §Stage 6 files)
- Modify: `tests/contracts/test_data_dictionary.py` (import and `MODELS`)

**Interfaces:**
- Consumes: `earnings_core.hashing.sha256_hex(data: bytes) -> str`; `earnings_themes.records`' `IdPart`, `Part`, `Sha256Hex`, `ThemesRecord` and `parse`; `earnings_themes.tomlfile.read`.
- Produces:
  - `LEDGER = "independent-pass.toml"`
  - `class LedgerRow(Part)`, with `event_id`, `sha256` and `recorded_on: date`
  - `class IndependentLedger(ThemesRecord)`, with `rows: tuple[LedgerRow, ...] = ()`
  - `load_ledger(path: Path) -> IndependentLedger`
  - `ledger_problem(ledger: IndependentLedger | None, event_id: str, record: bytes | None) -> str | None`. It returns a phrase that follows the event ID in a refusal, or `None`.

- [ ] **Step 1: Write the failing tests**

Append to `packages/earnings-themes/tests/test_independent.py`. Merge the new imports into the module's import block, keeping Ruff's order:

```python
from datetime import date

from earnings_core.hashing import sha256_hex
from earnings_themes.independent import (
    LEDGER,
    IndependentLedger,
    LedgerRow,
    ledger_problem,
    load_ledger,
)

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
            "is a dev bundle whose independent record has no ledger row:"
            f" {COMES_FIRST}",
        ),
        (
            IndependentLedger(rows=(row(sha256_hex(RECORD), TRAIN),)),
            RECORD,
            "is a dev bundle whose independent record has no ledger row:"
            f" {COMES_FIRST}",
        ),
        (
            IndependentLedger(rows=(row(sha256_hex(RECORD)), row("0" * 64))),
            RECORD,
            "has more than one ledger row (GS19)",
        ),
        (
            IndependentLedger(rows=(row("0" * 64),)),
            RECORD,
            "has an independent record that does not match its ledger row; the"
            " record is never edited (GS19)",
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
    data = {"rows": [{"event_id": DEV, "sha256": digest, "recorded_on": date(2026, 10, 12)}]}
    path.write_text(tomlfile.dumps(data), encoding="utf-8")
    assert load_ledger(path) == IndependentLedger(rows=(row(digest),))
    path.write_text("rows = [\n", encoding="utf-8")
    with pytest.raises(RecordError):
        load_ledger(path)
    path.write_text(tomlfile.dumps({"rows": [{**data["rows"][0], "sha256": "X"}]}), encoding="utf-8")
    with pytest.raises(RecordError):
        load_ledger(path)
```

Ruff's formatter will rewrap the two long lines in the last test. That is expected.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_independent.py -q`
Expected: collection fails with `ModuleNotFoundError: No module named 'earnings_themes.independent'`.

- [ ] **Step 3: Implement `independent.py`**

Create `packages/earnings-themes/src/earnings_themes/independent.py`:

```python
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


def ledger_problem(
    ledger: IndependentLedger | None, event_id: str, record: bytes | None
) -> str | None:
    """Why a dev bundle's draft may not be anchored or shown yet, or ``None``.
    ``record`` is the independent record's bytes, ``None`` when it is absent, and
    ``ledger`` is ``None`` when none is committed. The phrase follows the event ID
    in a refusal, and names no text."""
    if record is None:
        return f"is a dev bundle with no independent record: {_FIRST}"
    rows = [r for r in (ledger.rows if ledger else ()) if r.event_id == event_id]
    if not rows:
        return f"is a dev bundle whose independent record has no ledger row: {_FIRST}"
    if len(rows) > 1:
        return "has more than one ledger row (GS19)"
    if rows[0].sha256 != sha256_hex(record):
        return (
            "has an independent record that does not match its ledger row; the"
            " record is never edited (GS19)"
        )
    return None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_independent.py packages/earnings-themes/tests/test_import_boundaries.py -q`
Expected: all pass. The boundary test imports every themes module, the new one included, and confirms it loads nothing forbidden.

- [ ] **Step 5: Document and register the ledger**

In `docs/data-dictionary.md`, insert directly after the `IndependentRecord` section (still before `## Stage 6 files`):

```markdown
### `LedgerRow`

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | A dev bundle's event |
| `sha256` | SHA-256 hex | Of the independent record's bytes, as `shasum -a 256` prints it |
| `recorded_on` | date | When the pass was recorded |

### `IndependentLedger`

`evaluation/<corpus>/pilot-v<N>/independent-pass.toml`: committed, and holds no
text. It gains one row, committed on its own, before each dev bundle's drafting
session starts (GS19).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Themes record schema version |
| `rows` | tuple of `LedgerRow` | One per dev bundle |
```

In the same file's `## Stage 6 files` list, append this bullet after the **File names.** bullet:

```markdown
- **Dev's independent pass (GS19).** `data/runs/gold/independent/<event>.toml`,
  local and never committed, is the user's own reading of a dev bundle.
  `evaluation/<corpus>/pilot-v<N>/independent-pass.toml`, committed, holds each
  record's SHA-256. Unlike the records above, it gains a row per dev bundle rather
  than being written once. A dev bundle's draft is neither anchored nor shown until
  its record matches its row.
```

In `tests/contracts/test_data_dictionary.py`:
- change `from earnings_themes import annotation, codebook, gold, problems, split` to `from earnings_themes import annotation, codebook, gold, independent, problems, split`;
- add `independent.LedgerRow,` and `independent.IndependentLedger,` to `MODELS` directly after `annotation.IndependentRecord,`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`
Expected: all pass.

- [ ] **Step 6: Lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/test_independent.py
uv run --locked ruff check . && uv run --locked ruff format --check .
git add packages/earnings-themes/src/earnings_themes/independent.py packages/earnings-themes/tests/test_independent.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(themes): the independent-pass ledger and the dev guard's decision (GS19)"
```

---

### Task 3: `gold anchor <event> --independent --check` (application)

**Files:**
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py`
- Modify: `apps/earnings-pipeline/tests/test_stage6_cli.py`

**Interfaces:**
- Consumes: `check_independent`, `load_independent` and `without_quotes` (Task 1); `earnings_core.hashing.sha256_hex`; from `gold_cli.py`, `_open`, `pinned_split`, `load_bundle`, `wording_refusals`, `refuse`, `record_error`, `fail` and `file_stem`.
- Produces:
  - `_independent_path(layout: Layout, event_id: str) -> Path`
  - `_check_independent(layout, pinned, codebook, doc_ids, texts, event_id) -> None`
  - the `--independent` option on `anchor`
  - in the tests: `as_dev(monkeypatch)`, `independent_record(**changes)`, `write_independent(repo, record)`, `ledger_row(event_id, digest)` and `write_ledger(repo, rows)`. Task 4 reuses them.

- [ ] **Step 1: Write the failing tests**

In `apps/earnings-pipeline/tests/test_stage6_cli.py`:

- add `import hashlib` and `from datetime import date` to the imports;
- change `from earnings_themes.split import Partition, load_split` to `from earnings_themes.split import Partition, SplitManifest, load_split`;
- after the `SIGNED = …` constant add:

```python
INDEPENDENT = "Lowell Mason (independent pass)"
INDEPENDENT_DIR = Path("data") / "runs" / "gold" / "independent"
COMES_FIRST = "the user's independent pass and its ledger row come first (GS19)"
```

After the `gold_draft` helper, add the helpers:

```python
def as_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    """Read FIRST as a dev bundle (D16-5). The synthetic split has no dev event:
    each invented issuer's first event is in train, and its later ones are excluded
    (GS6). Only the split's lookup is patched, so the build and the validator agree.
    Call it after ``frozen``, whose codebook cites FIRST as a training example."""
    lookup = SplitManifest.partition_of

    def partition_of(self: SplitManifest, event_id: str) -> Partition:
        return Partition.DEV if event_id == FIRST else lookup(self, event_id)

    monkeypatch.setattr(SplitManifest, "partition_of", partition_of)


def independent_record(**changes) -> dict:
    """``gold_draft`` as the user's independent record: signed, with no aid."""
    record = gold_draft(annotator=INDEPENDENT, **changes)
    del record["drafting_aid"]
    return record


def write_independent(repo: Path, record: dict) -> Path:
    path = repo / INDEPENDENT_DIR / f"{FIRST_FILE}.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomlfile.dumps(record), encoding="utf-8")
    return path


def ledger_row(event_id: str, digest: str) -> dict:
    return {"event_id": event_id, "sha256": digest, "recorded_on": date(2026, 10, 12)}


def write_ledger(repo: Path, rows: list[dict]) -> None:
    path = repo / EVALUATION / "independent-pass.toml"
    path.write_text(tomlfile.dumps({"rows": rows}), encoding="utf-8")
```

At the end of the file, add the tests:

```python
def test_the_dev_patch_reads_first_as_dev(repo, monkeypatch) -> None:
    """D16-5's patch works: FIRST's draft anchors as dev, with its record and
    matching ledger row in place, so this passes with and without the guard."""
    frozen(repo)
    as_dev(monkeypatch)
    path = write_independent(repo, independent_record())
    write_ledger(repo, [ledger_row(FIRST, hashlib.sha256(path.read_bytes()).hexdigest())])
    write_drafts(repo, FIRST, gold_draft())
    result = run(repo, "gold", "anchor", FIRST, "--check")
    assert result.exit_code == 0, result.output
    assert lines(result)[0].startswith(f"{FIRST} (dev): ")


def test_an_independent_record_is_checked_and_its_hash_printed(
    repo, monkeypatch
) -> None:
    """GS19's check: counts, the record's SHA-256 for the ledger, nothing written.
    Its quote is a whole sentence of the release, which the wording guard skips
    (D16-3), so the check is clean."""
    frozen(repo)
    as_dev(monkeypatch)
    path = write_independent(repo, independent_record())
    result = run(repo, "gold", "anchor", FIRST, "--independent", "--check")
    assert result.exit_code == 0, result.output
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert lines(result) == [
        (
            f"{FIRST} (dev, independent): 1 quotes, 1 claims, 1 assignments, 0 hard"
            " negatives; no_theme false"
        ),
        f"sha256 {digest}  {INDEPENDENT_DIR}/{FIRST_FILE}.toml",
        f"checked {FIRST}: nothing written",
    ]
    assert not (repo / "data" / "runs" / "gold" / "anchored").exists()
    assert not (repo / EVALUATION / "gold").exists()


def test_a_bad_independent_record_is_refused_by_item(repo, monkeypatch) -> None:
    frozen(repo)
    as_dev(monkeypatch)
    assignments = [{"claim_id": "c1", "theme_id": "supply", "support": "supports"}]
    write_independent(repo, independent_record(assignments=assignments))
    result = run(repo, "gold", "anchor", FIRST, "--independent", "--check")
    assert result.exit_code == 1
    assert lines(result) == [
        "refused: assignment c1/supply: unknown_theme",
        "Refused: 1 problem(s); nothing written",
    ]


def test_an_independent_claim_that_copies_any_text_is_refused(
    repo, monkeypatch
) -> None:
    """The record's claims are checked against every text the committed guard
    reads, as a draft's are (GS3)."""
    frozen(repo)
    as_dev(monkeypatch)
    other = first_fixture(repo)
    copied = unique_window(guarded_texts(repo), other)
    claims = [{"claim_id": "c1", "quote_ids": ["q1"], "claim": f"Ours: {copied}"}]
    write_independent(repo, independent_record(claims=claims))
    result = run(repo, "gold", "anchor", FIRST, "--independent", "--check")
    assert result.exit_code == 1
    assert [line for line in lines(result) if line.startswith("refused: ")] == [
        f"refused: claims[0].claim ({other}): source_wording"
    ]


def test_the_independent_pass_is_for_dev_bundles_only(repo) -> None:
    frozen(repo)
    write_independent(repo, independent_record())
    result = run(repo, "gold", "anchor", FIRST, "--independent", "--check")
    assert result.exit_code == 1
    assert lines(result) == [
        f"Refused: {FIRST} is a train bundle; the independent pass is for dev"
        " bundles (GS19)"
    ]


def test_the_independent_pass_needs_check_and_events(repo) -> None:
    assert lines(run(repo, "gold", "anchor", FIRST, "--independent")) == [
        "Refused: --independent checks the user's record and writes nothing;"
        " add --check"
    ]
    curated = run(repo, "gold", "anchor", "--hard-negatives", "--independent", "--check")
    assert lines(curated) == ["Refused: --independent takes events, not --hard-negatives"]


def test_a_missing_independent_record_is_named(repo, monkeypatch) -> None:
    frozen(repo)
    as_dev(monkeypatch)
    result = run(repo, "gold", "anchor", FIRST, "--independent", "--check")
    assert result.exit_code == 1
    assert lines(result) == [
        f"Refused: {FIRST}: {INDEPENDENT_DIR}/{FIRST_FILE}.toml is not here; the"
        " user writes it before the draft (GS19)"
    ]


def test_the_independent_pass_comes_before_the_draft(repo, monkeypatch) -> None:
    """D16-2: once a draft exists, the record can no longer be shown to predate it."""
    frozen(repo)
    as_dev(monkeypatch)
    write_independent(repo, independent_record())
    write_drafts(repo, FIRST, gold_draft())
    result = run(repo, "gold", "anchor", FIRST, "--independent", "--check")
    assert result.exit_code == 1
    assert lines(result) == [
        f"Refused: {FIRST}: data/runs/gold/drafts/{FIRST_FILE}.draft.toml exists;"
        " the independent pass comes before the draft (GS19)"
    ]
```

`Path` prints with `/` separators on macOS and Linux, so `f"{INDEPENDENT_DIR}/…"` matches `layout.shown`'s output there. The suite does not run on Windows.

- [ ] **Step 2: Run the tests to verify they fail as expected**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q -k "dev_patch or independent"`

Expected:
- `test_the_dev_patch_reads_first_as_dev` **PASSES**. This proves D16-5's patch makes FIRST anchor as `(dev)` before any guard exists.
- Every `independent` test **FAILS**. Typer exits 2 with `No such option: --independent`, so each failure shows exit code 2 or a mismatched `lines(...)`.

If the dev-patch test fails, stop. The patch target has not taken, which is a test-setup problem to fix before going on.

- [ ] **Step 3: Implement the check in `gold_cli.py`**

Imports. Add `from earnings_core.hashing import sha256_hex` among the third-party imports, and extend the `earnings_themes.annotation` import list to:

```python
from earnings_themes.annotation import (
    build_curated,
    build_gold,
    check_independent,
    load_curated_draft,
    load_gold_draft,
    load_independent,
    signed,
    validate_curated,
    validate_gold,
    without_quotes,
)
```

After the `Curated = Annotated[…]` definition, add:

```python
Independent = Annotated[
    bool,
    typer.Option(
        "--independent",
        help="With --check: the user's independent record of a dev bundle (GS19).",
    ),
]
```

After `_drafts`, add:

```python
def _independent_path(layout: Layout, event_id: str) -> Path:
    """The user's independent record of a dev bundle, local and never committed."""
    return layout.gold_runs / "independent" / f"{file_stem(event_id)}.toml"


def _check_independent(
    layout: Layout,
    pinned: Pinned,
    codebook: Codebook,
    doc_ids: dict[str, str],
    texts: dict[str, str],
    event_id: str,
) -> None:
    """GS19's check: anchor and check the user's independent record of a dev
    bundle, print its SHA-256 for the ledger, and write nothing. It runs only
    before the bundle's draft, working copy, anchored file, or view exists (D16-2)."""
    split = pinned_split(layout, pinned)
    _open(layout, split, event_id)
    partition = split.partition_of(event_id)
    if partition is not Partition.DEV:
        fail(
            f"Refused: {event_id} is a {partition} bundle; the independent pass is"
            " for dev bundles (GS19)"
        )
    stem = file_stem(event_id)
    later = (
        layout.drafts / f"{stem}.draft.toml",
        layout.drafts / f"{stem}.working.toml",
        layout.gold_runs / "anchored" / f"{stem}.toml",
        layout.gold_runs / "views" / f"{stem}.md",
    )
    if existing := [path for path in later if path.is_file()]:
        fail(
            f"Refused: {event_id}: {layout.shown(existing[0])} exists; the"
            " independent pass comes before the draft (GS19)"
        )
    path = _independent_path(layout, event_id)
    if not path.is_file():
        fail(
            f"Refused: {event_id}: {layout.shown(path)} is not here; the user"
            " writes it before the draft (GS19)"
        )
    try:
        record = load_independent(path)
    except RecordError as error:
        record_error(error)
    bundle = load_bundle(layout, doc_ids, event_id)
    if refusals := check_independent(record, bundle=bundle, codebook=codebook):
        refuse(refusals)
    if found := wording_refusals(without_quotes(record), texts):
        refuse(found)
    typer.echo(
        f"{event_id} (dev, independent): {len(record.quotes)} quotes,"
        f" {len(record.claims)} claims, {len(record.assignments)} assignments,"
        f" {len(record.hard_negatives)} hard negatives; no_theme"
        f" {str(record.no_theme).lower()}"
    )
    typer.echo(f"sha256 {sha256_hex(path.read_bytes())}  {layout.shown(path)}")
    typer.echo(f"checked {event_id}: nothing written")
```

Replace `anchor_command` with:

```python
@gold.command("anchor")
@guarded
def anchor_command(
    context: typer.Context,
    event_ids: Events = None,
    hard_negatives: Curated = False,
    check: Annotated[
        bool, typer.Option("--check", help="Anchor and check; write nothing.")
    ] = False,
    independent: Independent = False,
) -> None:
    """Anchor each working copy; commit the record once it is signed."""
    layout: Layout = context.obj
    if independent and not check:
        fail(
            "Refused: --independent checks the user's record and writes nothing;"
            " add --check"
        )
    if independent and (hard_negatives or not event_ids):
        fail("Refused: --independent takes events, not --hard-negatives")
    if not event_ids and not hard_negatives:
        fail("Refused: name the events to anchor, or --hard-negatives")
    codebook = pinned_codebook(layout)
    pinned = load_pinned(layout)
    texts = wording_texts(layout, pinned)
    if hard_negatives:
        _anchor_curated(layout, pinned, codebook, texts, check)
    if event_ids:
        doc_ids = documents(layout, pinned)
        for event_id in event_ids:
            if independent:
                _check_independent(layout, pinned, codebook, doc_ids, texts, event_id)
            else:
                _anchor_event(layout, pinned, codebook, doc_ids, texts, event_id, check)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q`
Expected: all pass, including every existing test. The train path is untouched.

- [ ] **Step 5: Lint and commit**

```bash
uv run --locked ruff format apps/earnings-pipeline/tests/test_stage6_cli.py
uv run --locked ruff check . && uv run --locked ruff format --check .
git add apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py apps/earnings-pipeline/tests/test_stage6_cli.py
git commit -m "feat(pipeline): gold anchor --independent --check for dev bundles (GS19)"
```

---

### Task 4: The dev guard on `gold anchor` and `gold show` (application)

**Files:**
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py`
- Modify: `apps/earnings-pipeline/tests/test_stage6_cli.py`

**Interfaces:**
- Consumes: `LEDGER`, `load_ledger` and `ledger_problem` (Task 2); `_independent_path` and the test helpers (Task 3).
- Produces: `_guard(layout: Layout, pinned: Pinned, split: SplitManifest, event_id: str) -> None`, called by `_anchor_event` and by `show_command`'s event branch, never by `gold show --text`.

- [ ] **Step 1: Write the failing tests**

Append to `apps/earnings-pipeline/tests/test_stage6_cli.py`:

```python
def test_a_dev_draft_waits_for_its_matching_ledger_row(repo, monkeypatch) -> None:
    """GS19's guard: neither the drafting session's check, nor the anchor, nor the
    view touches a dev draft until the user's record matches its one ledger row."""
    frozen(repo)
    as_dev(monkeypatch)
    write_drafts(repo, FIRST, gold_draft())
    no_record = f"Refused: {FIRST} is a dev bundle with no independent record: {COMES_FIRST}"
    for args in (("anchor", FIRST, "--check"), ("anchor", FIRST), ("show", FIRST)):
        result = run(repo, "gold", *args)
        assert result.exit_code == 1
        assert lines(result) == [no_record]
    path = write_independent(repo, independent_record())
    no_row = (
        f"Refused: {FIRST} is a dev bundle whose independent record has no ledger"
        f" row: {COMES_FIRST}"
    )
    assert lines(run(repo, "gold", "anchor", FIRST)) == [no_row]
    (repo / EVALUATION / "independent-pass.toml").write_text("rows = [\n", encoding="utf-8")
    assert lines(run(repo, "gold", "anchor", FIRST)) == [
        "problem: independent-pass.toml: not TOML at line 2, column 1",
        "Refused: independent-pass.toml does not read as its record",
    ]
    write_ledger(repo, [ledger_row(FIRST, "0" * 64)])
    assert lines(run(repo, "gold", "anchor", FIRST)) == [
        f"Refused: {FIRST} has an independent record that does not match its ledger"
        " row; the record is never edited (GS19)"
    ]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    write_ledger(repo, [ledger_row(FIRST, digest)])
    anchored = run(repo, "gold", "anchor", FIRST)
    assert anchored.exit_code == 0, anchored.output
    assert lines(anchored)[0].startswith(f"{FIRST} (dev): ")
    shown = run(repo, "gold", "show", FIRST)
    assert lines(shown) == [f"view  data/runs/gold/views/{FIRST_FILE}.md"]


@pytest.mark.parametrize("ledger", [None, "rows = [\n"])
def test_a_train_draft_reads_no_ledger_or_record(repo, ledger) -> None:
    """Train is unchanged: with no ledger, or one that does not read, and no
    record, a train draft anchors and shows as before."""
    frozen(repo)
    if ledger is not None:
        (repo / EVALUATION / "independent-pass.toml").write_text(ledger, encoding="utf-8")
    write_drafts(repo, FIRST, gold_draft())
    anchored = run(repo, "gold", "anchor", FIRST)
    assert anchored.exit_code == 0, anchored.output
    assert lines(anchored)[0].startswith(f"{FIRST} (train): ")
    shown = run(repo, "gold", "show", FIRST)
    assert lines(shown) == [f"view  data/runs/gold/views/{FIRST_FILE}.md"]


def test_a_dev_bundle_s_text_is_written_before_its_pass(repo, monkeypatch) -> None:
    """``gold show --text`` is not guarded: the user's pass needs the text."""
    frozen(repo)
    as_dev(monkeypatch)
    result = run(repo, "gold", "show", "--text", FIRST)
    assert result.exit_code == 0, result.output
    assert lines(result) == ["wrote 1 text under data/runs/gold/texts"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q -k "ledger_row or reads_no_ledger or written_before"`

Expected:
- `test_a_dev_draft_waits_for_its_matching_ledger_row` **FAILS**: the first `anchor --check` exits 0, because no guard exists yet.
- `test_a_train_draft_reads_no_ledger_or_record` and `test_a_dev_bundle_s_text_is_written_before_its_pass` **PASS** already. They pin behavior the guard must keep.

- [ ] **Step 3: Implement the guard in `gold_cli.py`**

Add the import:

```python
from earnings_themes.independent import LEDGER, ledger_problem, load_ledger
```

After `_independent_path`, add:

```python
def _guard(layout: Layout, pinned: Pinned, split: SplitManifest, event_id: str) -> None:
    """GS19: a dev bundle's draft is neither anchored nor shown until the user's
    independent record exists and matches its ledger row. Only a dev bundle reads
    the ledger or the record, so train and test are unchanged."""
    if split.partition_of(event_id) is not Partition.DEV:
        return
    path = pinned.evaluation / LEDGER
    try:
        ledger = load_ledger(path) if path.is_file() else None
    except RecordError as error:
        record_error(error)
    record = _independent_path(layout, event_id)
    found = record.read_bytes() if record.is_file() else None
    if (reason := ledger_problem(ledger, event_id, found)) is not None:
        fail(f"Refused: {event_id} {reason}")
```

In `_anchor_event`, call the guard directly after `_open`:

```python
    split = pinned_split(layout, pinned)
    _open(layout, split, event_id)
    _guard(layout, pinned, split, event_id)
    bundle = load_bundle(layout, doc_ids, event_id)
```

In `show_command`'s `if event_ids:` loop, call it directly after `_open`:

```python
        for event_id in event_ids:
            _open(layout, split, event_id)
            _guard(layout, pinned, split, event_id)
            committed = pinned.gold_dir / f"{file_stem(event_id)}.toml"
```

Leave `_show_texts` unchanged.

Extend the module docstring. After the usage line `uv run --locked earnings-pipeline gold validate`, add the line:

```text
    uv run --locked earnings-pipeline gold anchor <dev event> --independent --check
```

and after the sentence ending `No command prints a document's text (GS13).`, add:

```text
A dev bundle's draft (GS19) is neither anchored nor shown until the user's
independent record, ``data/runs/gold/independent/<name>.toml``, matches its row in
the pilot's ``independent-pass.toml``. ``anchor --independent --check`` checks that
record before its draft exists, prints its SHA-256 for the ledger, and writes
nothing.
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q`
Expected: all pass. That includes `test_the_dev_patch_reads_first_as_dev`, which writes its record and ledger first, and every pre-existing train test.

- [ ] **Step 5: Lint and commit**

```bash
uv run --locked ruff format apps/earnings-pipeline/tests/test_stage6_cli.py
uv run --locked ruff check . && uv run --locked ruff format --check .
git add apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py apps/earnings-pipeline/tests/test_stage6_cli.py
git commit -m "feat(pipeline): guard dev drafts behind the independent-pass ledger (GS19)"
```

---

### Task 5: Scoped checks, the user's gates, and completion (gate)

**Files:**
- Modify: `specs/deferred_items.md` (tick the GS19 item)
- Modify: this plan (completion markup), then `git mv` it to `specs/plans/completed/`

- [ ] **Step 1: Run every scoped check in the worktree**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_independent.py packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/test_import_boundaries.py apps/earnings-pipeline/tests/test_stage6_cli.py tests/contracts/test_data_dictionary.py -q
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Expected: every test passes, and Ruff prints no finding. Record the exact pass counts for the handoff.

- [ ] **Step 2 (gate): Hand the user the checks only they run**

Put this to the user in chat, with `<sha>` set to `git rev-parse HEAD`, and wait for the results:

> The GS19 check and guard are implemented on `gs19-independent-pass-check` at `<sha>`. Three checks are yours, because they read pilot data or run the full suite. Run them in the main checkout, `/Users/lowell/Projects/earnings-themes`, after `git switch --detach <sha>`, and finish with `git switch main`:
>
> 1. The root suite: `uv run --locked --all-packages pytest packages apps tests -m "not live and not browser"`. Please send the passed, skipped and deselected counts.
> 2. The Stage 6 wording test: `uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs`. Please send its counts.
> 3. The three signed train bundles, re-anchored and validated:
>    `uv run --locked earnings-pipeline gold anchor cik-0000051143:2024-12-31 cik-0000093410:2025-03-31 cik-0000310158:2025-06-30` — each event's last line should read `unchanged: evaluation/djia-2024q3-2026q2/pilot-v1/gold/<file>.toml`;
>    then `uv run --locked earnings-pipeline gold validate` — three `valid: … (train), …, signed` lines.

If any check fails, stop and debug it with systematic-debugging before going on.

- [ ] **Step 3: Run the Plan Completion Protocol**

Follow writing-plans' Plan Completion Protocol:

- **Resolve-before-defer:** ask the user about anything left open, in one batch.
- **Markup:** tick the steps; set the status header to `**Status: COMPLETE (YYYY-MM-DD)** — executed via <skill>; …`.
- **Deferred items:** in `specs/deferred_items.md`, tick the `GS19 — Independent-pass check and dev guard` item with `→ done in plan 16`. The plan-9 item for the 25 bundles stays open.
- **Backlog triage:** run it as the protocol describes.
- **Retire:** `git mv` this plan to `specs/plans/completed/` in one `chore(specs): retire plan 16` commit. The spec is already in `specs/completed/`, so do not move it.

- [ ] **Step 4: Hand off what goes stale**

Tell the user, without editing these files:
- `CLAUDE.md` line 80 says the dev bundles "wait for its check and guard to land". Updating it needs the user's OK.
- Plan 9's Task 19 note says no dev bundle is drafted before the check and guard land. That is now met; the note can stay as history or be updated.

Then go on with finishing-a-development-branch.

---

## Self-review

- **Spec coverage, §The independent pass:**

  | Spec point | Where it's built |
  | --- | --- |
  | The record (form, no aid, signature, hard negatives optional) | Task 1 |
  | The check: anchors every quote, checks every item, prints counts and refusals, writes nothing | Tasks 1 and 3 |
  | The guard: anchor with and without `--check` and show refuse, the refusal names event and reason only, `--text` unguarded | Task 4 |
  | The ledger: event, sha256, recorded_on; no text | Task 2 |
  | Immutability | Enforced by the hash mismatch refusal (Task 4) |
  | Blinding: `annotation` does not import `independent` | Global Constraints; Task 2's module docstring |

  The order, the signature and Stage 11's use are procedure or Stage 11's work, not code. Backlog item done-when: both behaviors tested (Tasks 3 and 4); a train bundle anchors as before (`test_a_train_draft_reads_no_ledger_or_record` and every pre-existing test); the three committed files re-anchor unchanged (Task 5's gate 3).
- **Placeholders:** none. Every code step shows its code. The user's gate (Task 5) asks for counts, which no session can know in advance.
- **Type consistency:** these names are used identically across Tasks 1 to 4:
  - `IndependentRecord`, `check_independent(record, *, bundle, codebook)`, `without_quotes(record)`, `load_independent(path)`
  - `LedgerRow`, `IndependentLedger`, `LEDGER`, `load_ledger(path)`, `ledger_problem(ledger, event_id, record)`
  - `_independent_path(layout, event_id)`, `_check_independent(layout, pinned, codebook, doc_ids, texts, event_id)`, `_guard(layout, pinned, split, event_id)`
