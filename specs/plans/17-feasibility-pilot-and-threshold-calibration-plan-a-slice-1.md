# Stage 11 Plan A, Slice 1: Gold-Side Fixes and Coverage v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close plan 10's kept-draft repeated-ID item, P16-2 and P16-3, and give the `pilot` group a counts-only GS5 recheck (`pilot recount`) and coverage v2 (`pilot coverage --version 2`): the Stage 11 spec's A6, A7, and the wording globs of A9, with no pilot text and no model.

**Architecture:**
- **`earnings-themes`:**
  - `annotation.py` refuses a kept draft that repeats an ID, and refuses an independent record under an unapproved codebook.
  - It also anchors one reading in memory (`anchor_reading`), rebuilds a committed file to recheck its counts (`recount`), and checks a committed file before its `no_theme` is counted (`check_countable`).
  - `independent.py` names the ledger's problems as `Problem` values (`ledger_check`), and verifies a dev record against its ledger before anchoring both readings (`verify_independent`).
  - `tomlfile.loads` reads bytes the way `read` reads a file.
- **`earnings-ingestion`:** `events/coverage.py`'s `build_coverage` takes the no-theme rows. The report validates them: bounded, one per partition, in order, and absent from version 1. Ingestion reads no gold, so the application counts the rows (FP18).
- **The application:** `pilot_cli.py` gains `pilot recount` and `pilot coverage --version 2`. In `stage6.py`, `Pinned.coverage_file(version)` replaces `coverage_path`.

**Tech Stack:** Python 3.14.0 uv workspace; Pydantic v2 (strict, frozen `Part` models); Typer; pytest; Ruff; `tomllib`. No new dependency.

**Spec:** `specs/feasibility-pilot-and-threshold-calibration.md`, approved 2026-10-11 and merged to `main` at `c1e7ac7`. This plan implements:
- §Plan A: A6, A7, and A9's first bullet;
- §Inputs, FP16, FP18, and §Deferred items.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 11 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

**This plan is plan A's first slice, not plan A.** The spec's Rollout says the Roadmap line's "plan completion" means plan B's. Plan A's own completion appends `Plan A: COMPLETE`. Plan 17 does neither of those things. On completion it:
- does not tick Stage 11;
- does not append the spec's `Plan A: COMPLETE` line;
- does not retire the spec.

Instead, it appends a slice stamp to the spec's Rollout and retires only itself (D17-11, Task 8). Plan A's remainder is A1–A5, A8, and A9's data-dictionary rows for those records. It is a later plan, written after this one merges.

## Global Constraints

- **GS13, blinding.**
  - The executing session never opens pilot text, a kept draft, or anything under `data/runs/gold/` or `data/runs/pilot/`. It never opens anything under the main checkout's `data/`.
  - Execute in a fresh worktree, which has no `data/` at all.
  - Never load a model.
  - Never run `-m live` (`EDGAR_IDENTITY` is exported in this shell) or `-m browser`.
  - Tests use only the synthetic layer's invented text, the synthetic cohort and acquisition, Stage 1's committed fixtures, and invented records.
  - No command prints a document's text; `test_stage6_cli.py`'s `quiet()` enforces this for every CLI call.
- **Tracebacks.** Never pass `--tb=long`, `--tb=auto`, `--full-trace`, `-l`, `--showlocals`, `--pdb`, or `-vv`.
- **User gates.** The default (root) suite and the Stage 6 wording test run in the main checkout, and the user runs them in their own terminal (Task 8). The executor never runs:
  - `pytest packages apps tests`;
  - `tests/integration/test_stage6_wording.py`;
  - `tests/integration/test_stage6_pilot_v1.py`.

  A failing user gate is reported by test name and reason only.
- **The user's gate file.** Task 7 edits `tests/integration/test_stage6_wording.py`. The executor edits it and runs Ruff over it, and nothing else.
- **`CLAUDE.md`.** Never edit it without asking the user first.
- **TDD.** Every task writes its failing test first and watches it fail for the stated reason.
- **GS3, the public repository.** Committed files hold IDs, hashes, counts, and the user's words, never release text. This plan commits no evaluation record.
- **Refusals.** Each names its item by ID or field path, and its reason, never text. A `Refusal`'s reason is a `Problem` or a `RejectionReason` value. A command that refuses exits 1 and writes nothing.
- **GS17, units.**
  - `earnings-themes` imports only `earnings-core`, and ingestion and themes never import each other.
  - `annotation.py` is a drafting module and must not import `earnings_themes.independent` (`test_import_boundaries.py`). `independent.py` may import `annotation.py`.
- **Data dictionary.** Every new `Problem` value and model is documented in `docs/data-dictionary.md`, in the same task (AGENTS.md §191). Every new model is also registered in `MODELS` of `tests/contracts/test_data_dictionary.py`.
- **Ruff.** Default line length, 88. Run `uv run --locked ruff format <changed files>` before each commit; `uv run --locked ruff check .` and `uv run --locked ruff format --check .` must be clean.
- **Commits.**
  - Before each commit, run `git log -3 --oneline`: the user may commit on the branch mid-run.
  - End each commit message with the attribution trailer your session's instructions give.
- **Agent verification scope.** The executor runs only these, in the worktree:
  - `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/test_independent.py packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_import_boundaries.py -q`
  - `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_coverage.py -q`
  - `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q`
  - `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`
  - `uv run --locked ruff check .` and `uv run --locked ruff format --check .`

---

## Decisions (D17-n)

- **D17-1, the slice.** The spec's §Plan A lets A6 and A7 form a first slice. The user chose A6, A7, and A9's wording globs on 2026-10-11:
  - the globs close P16-3, and the ledger they scan exists since plan 16;
  - the remainder is A1–A5, A8, and A9's data-dictionary rows for the records those add.
- **D17-2, A6(1).** `_repeats(draft, prefix)` refuses, as `duplicate_id`:
  - a repeated quote ID;
  - a repeated claim ID, where claims and hard negatives share one ID space, as `_ids` treats them;
  - a repeated assignment row, `<claim>/<theme>`.

  `build_curated` also refuses a repeated fixture (`draft <fixture_id>`), and each fixture's own repeats (`draft <fixture_id> quote q1`).
  - Subjects take the prefix `draft `, which tells them apart from the working copy's own `duplicate_id`.
  - They are collected with every other refusal, not returned early, so the user sees every reason at once.
  - `test_ids_themes_and_ties_are_checked` pins a draft that is also its working copy and repeats `c1`. Its pinned list gains `Refusal("draft claim c1", "duplicate_id")` first.
- **D17-3, A6(2).** `check_independent` returns `[Refusal("codebook", "codebook_not_approved")]` right after its event check. A record carries no codebook reference, so only the approval is checked.
- **D17-4, A6(3): readings now, figures later.** The user chose this on 2026-10-11.
  - `verify_independent` returns the two anchored readings, as an `IndependentReadings`. A3's comparison figures and A8's `pilot independent` are plan A's remainder.
  - The ledger's five problems become `Problem` values, through `ledger_check`. `ledger_problem` maps them to its unchanged phrases, so its parametrized test is unchanged.
  - `ledger_check` tests `ledger is not None`, which fixes P16-4's item (1).
  - The record's items are `annotator_added`, and the kept draft's are `drafted_accepted`.
  - The record's bytes are hashed for the ledger and parsed as those same bytes (`tomlfile.loads`).
- **D17-5, A6(4): rebuild with the working copy.** The user chose this on 2026-10-11.
  - `recount` rebuilds a committed file with `build_gold(kept draft, working copy)` and requires the committed bytes exactly.
  - Otherwise it names each differing count as `counts.<field>` (`counts_mismatch`), then the file as `record` (`not_rebuilt`, a new `Problem` value).
  - The command is `pilot recount [EVENTS]`. It has no GS19 guard: committed dev gold passed the guard when it was anchored.
  - It covers each event's gold, not the curated hard negatives, since GS5's shares are per partition.
  - A known-answer test pins that a prefix-only edit counts as `drafted_edited`.
- **D17-6, coverage v2 reads version 1's runs.** The user chose this on 2026-10-11. Version 2 refuses until `coverage-v1.json` is frozen, then rebuilds from its `run_ids`. So version 2's state counts equal version 1's, and a later run changes neither.
- **D17-7, the population.** Train and dev events from the frozen split, each with a parsed document under version 1's runs:
  - 28 for pilot v1 (20 and 8);
  - 11 and 0 for the synthetic pilot, whose split has no dev event (GS6).

  Both rows are always written, train then dev, so the synthetic pilot's dev row reads `0 of 0`. A refusal lists every such bundle without committed gold. No test or excluded event is read: only the split's train and dev events are.
- **D17-8, `check_countable`.** `check_countable(gold, *, event_id, pin, split, codebook)` checks a committed file without its document: its event, pin, split, partition, codebook reference and approval, signature, and `no_theme` against its assignments. Coverage reads no document (P-C7's pattern), and `gold validate` covers the rest.
- **D17-9, ingestion's validation.**
  - `NoThemeCount` refuses `no_theme > bundles`.
  - `CoverageReport` refuses a repeated or misordered partition (`train`, `dev`, `test`), and any no-theme row in version 1.
  - `build_coverage(no_theme=…)` orders the rows itself.
  - The committed `coverage-v1.json` holds `"no_theme": []`, so its bytes and hash are unchanged.
- **D17-10, the wording globs.**
  - `STAGE6` gains `evaluation/*/pilot-v*/*.toml`, which scans the ledger and closes P16-3, and `evaluation/*/pilot-v*/labels/*.toml`. `evaluation/*/pilot-v*/*.json` is already there.
  - A new test makes each planned Stage 11 file empty under `tmp_path`, and shows the globs find it.
  - TOML comments stay unscanned, as for every TOML file the test reads, and the module docstring now says so. P16-3's done-when, "the globs cover the ledger", is met.
- **D17-11, rollout.**
  - Append a slice stamp at the end of the spec's Rollout section (Task 8).
  - Leave the roadmap untouched.
  - Keep the spec in `specs/`, an exception to the completion protocol's spec-retire rule, since plans for A's remainder and B follow.
  - Retire plan 17 to `specs/plans/completed/`.
  - Refresh `CLAUDE.md`'s "Current state" only with the user's approval.

## File structure

| File | Change | Task |
| --- | --- | --- |
| `packages/earnings-themes/src/earnings_themes/annotation.py` | `_repeats`, `_curated_repeats`; `check_independent`'s approval check; `Reading`, `anchor_reading`; `recount`; `check_countable` | 1, 2, 3, 4, 6 |
| `packages/earnings-themes/src/earnings_themes/independent.py` | `ledger_check`, `_PHRASES`; `IndependentReadings`, `verify_independent` | 2, 3 |
| `packages/earnings-themes/src/earnings_themes/problems.py` | Six new `Problem` values | 2, 4 |
| `packages/earnings-themes/src/earnings_themes/tomlfile.py` | `loads`; `read` through it | 3 |
| `packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py` | `PARTITIONS`; two validators; `build_coverage(no_theme=…)` | 5 |
| `apps/earnings-pipeline/src/earnings_pipeline/stage6.py` | `Pinned.coverage_file(version)` replaces `coverage_path` | 6 |
| `apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py` | `pilot recount`; `pilot coverage --version` | 4, 6 |
| `docs/data-dictionary.md` | `Problem` rows; `Reading`; `IndependentReadings`; `NoThemeCount` and `CoverageReport` meanings | 2, 3, 4, 5 |
| `packages/earnings-themes/tests/test_gold.py` | Repeats, recount, `check_countable` tests; one pinned list gains a row | 1, 4, 6 |
| `packages/earnings-themes/tests/test_independent.py` | Approval, `ledger_check`, and `verify_independent` tests | 2, 3 |
| `packages/earnings-themes/tests/test_tomlfile.py` | `loads` tests | 3 |
| `packages/earnings-ingestion/tests/test_events_coverage.py` | Version 2 tests | 5 |
| `apps/earnings-pipeline/tests/test_stage6_cli.py` | The repeat refusal; recount; coverage v2 | 1, 4, 6 |
| `tests/integration/test_stage6_pilot_v1.py` | Coverage v2 reproduction, which skips until B7 (user-run) | 6 |
| `tests/integration/test_stage6_wording.py` | **The user's gate file:** two globs and a test | 7 |
| `tests/contracts/test_data_dictionary.py` | `MODELS` gains `Reading` and `IndependentReadings` | 3 |
| `specs/feasibility-pilot-and-threshold-calibration.md`, `specs/deferred_items.md`, this plan | Completion | 8 |

## Setup (before Task 1)

The planning session committed this plan on branch `stage-11-plan-a-gold-and-coverage`, cut from `main` at `c1e7ac7`, and returned the main checkout to `main`.

- [ ] **Step 1: Ask the user where to execute.** The user decides whether to use a worktree when execution starts. Recommend one: a worktree has no `data/`, so GS13 holds by construction. With a worktree, follow using-git-worktrees for the existing branch, from the main checkout:

```bash
git worktree add .claude/worktrees/stage-11-plan-a-gold-and-coverage stage-11-plan-a-gold-and-coverage
```

Then work inside `.claude/worktrees/stage-11-plan-a-gold-and-coverage` and sync:

```bash
uv sync --locked --all-packages --group dev
```

- [ ] **Step 2: Record the baseline.** Run the scoped checks (Task 8, Step 1's commands). Expected: every test passes, and Ruff is clean. Record the pass counts.

---

### Task 1: Refuse a kept draft that repeats an ID (A6(1))

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/annotation.py` (module docstring; new `_repeats` and `_curated_repeats` after `_by_row` at :185; `build_gold` at :233; `build_curated` at :458)
- Test: `packages/earnings-themes/tests/test_gold.py` (the pinned list at :185; two new tests)
- Test: `apps/earnings-pipeline/tests/test_stage6_cli.py` (one new test)

**Interfaces:**
- Consumes: `_Origins` (:147), `_items` (:189), `GoldDraft`, `FixtureDraft`, `CuratedDraft`, `Problem.DUPLICATE_ID`, `Refusal`.
- Produces: `_repeats(draft: GoldDraft | IndependentRecord | FixtureDraft, prefix: str) -> list[Refusal]`, which Task 3's `anchor_reading` reuses. `build_gold` and `build_curated` keep their signatures.

- [ ] **Step 1: Write the failing tests**

In `packages/earnings-themes/tests/test_gold.py`, `test_ids_themes_and_ties_are_checked` builds a draft that is also its working copy and repeats `c1`. Change its first assertion's list, at :185, from:

```python
    assert build(bundles, codebook, draft) == [
        Refusal("claim c1", "duplicate_id"),
```

to:

```python
    assert build(bundles, codebook, draft) == [
        Refusal("draft claim c1", "duplicate_id"),
        Refusal("claim c1", "duplicate_id"),
```

Leave the list's other six rows as they are.

Append to the end of `packages/earnings-themes/tests/test_gold.py`:

```python
def test_a_kept_draft_that_repeats_an_id_is_refused(bundles, codebook) -> None:
    """Origins compare the kept draft's items by ID, so a repeat there would let its
    last copy stand for both, and GS5's rejected count would miss one when the
    working copy drops it. The kept draft is refused by ID, its subjects prefixed,
    and nothing is built (plan 10's deferred item; the Stage 11 spec, A6(1))."""
    drafted = gold_draft()
    drafted["quotes"].append(dict(drafted["quotes"][0]))
    drafted["claims"].append({**drafted["claims"][0], "claim": "Again."})
    drafted["hard_negatives"].append({**drafted["hard_negatives"][0], "claim_id": "c2"})
    drafted["assignments"].append(dict(drafted["assignments"][0]))
    assert build(bundles, codebook, drafted, gold_draft()) == [
        Refusal("draft quote q1", "duplicate_id"),
        Refusal("draft claim c1", "duplicate_id"),
        Refusal("draft claim c2", "duplicate_id"),
        Refusal("draft assignment c1/demand", "duplicate_id"),
    ]


def test_a_kept_curated_draft_that_repeats_a_fixture_or_an_id_is_refused(
    fixtures, codebook
) -> None:
    """The curated set's kept draft keys its fixtures by fixture ID, and each
    fixture's items by ID: a repeat of either is refused (A6(1))."""
    good = curated(fixtures)
    first = good.documents[0]
    repeated = good.model_copy(update={"documents": (*good.documents, first)})
    refusals = build_curated(repeated, good, bundles=fixtures, pin=PIN, codebook=codebook)
    assert refusals == [Refusal(f"draft {first.fixture_id}", "duplicate_id")]
    twice = first.model_copy(update={"quotes": (*first.quotes, first.quotes[0])})
    inner = good.model_copy(update={"documents": (twice, *good.documents[1:])})
    refusals = build_curated(inner, good, bundles=fixtures, pin=PIN, codebook=codebook)
    assert refusals == [Refusal(f"draft {first.fixture_id} quote q1", "duplicate_id")]
```

In `apps/earnings-pipeline/tests/test_stage6_cli.py`, add after `test_a_bad_gold_draft_is_refused_by_item_and_writes_nothing`:

```python
def test_a_kept_draft_that_repeats_an_id_is_refused_by_id(repo) -> None:
    """Plan 10's deferred item (the Stage 11 spec, A6(1)): the working copy dropped
    the repeat, so only the kept draft holds it; it is refused by ID, and nothing is
    written."""
    frozen(repo)
    drafted = gold_draft()
    drafted["quotes"].append(dict(drafted["quotes"][0]))
    write_drafts(repo, FIRST, drafted, gold_draft())
    result = run(repo, "gold", "anchor", FIRST)
    assert result.exit_code == 1
    assert lines(result) == [
        "refused: draft quote q1: duplicate_id",
        "Refused: 1 problem(s); nothing written",
    ]
    assert not (repo / "data" / "runs" / "gold" / "anchored").exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py -q
```

Expected: 3 failed:
- `test_ids_themes_and_ties_are_checked`: the list lacks `draft claim c1`;
- `test_a_kept_draft_that_repeats_an_id_is_refused`: a `Gold` is built where a list was expected;
- `test_a_kept_curated_draft_that_repeats_a_fixture_or_an_id_is_refused`: a `HardNegativeSet` is built.

Then run:

```bash
uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q -k repeats_an_id
```

Expected: 1 failed, with exit code 0 where 1 was expected.

- [ ] **Step 3: Implement**

In `packages/earnings-themes/src/earnings_themes/annotation.py`, replace the module docstring's second bullet:

```python
- **The build.** Every working quote is anchored, every item's origin derived by
  comparing the working copy with the draft, and the result validated. Any refusal
  writes nothing, and names its item by ID, never by text.
```

with:

```python
- **The build.** Every working quote is anchored, every item's origin derived by
  comparing the working copy with the draft, and the result validated. A kept draft
  that repeats an ID is refused, since origins compare its items by ID. Any refusal
  writes nothing, and names its item by ID, never by text.
```

Add after `_by_row` (:185–186):

```python
def _repeats(
    draft: GoldDraft | IndependentRecord | FixtureDraft, prefix: str
) -> list[Refusal]:
    """Each quote ID, claim ID (claims and hard negatives together), and assignment
    row that ``draft`` repeats. Origins compare a kept draft's items by ID, so a
    repeat would let its last copy stand for both, and GS5's ``rejected`` would miss
    one (plan 10's deferred item; the Stage 11 spec, A6(1))."""
    claims = (*getattr(draft, "claims", ()), *draft.hard_negatives)
    rows = [f"{a.claim_id}/{a.theme_id}" for a in getattr(draft, "assignments", ())]
    refusals = []
    for name, ids in (
        ("quote", [q.quote_id for q in draft.quotes]),
        ("claim", [c.claim_id for c in claims]),
        ("assignment", rows),
    ):
        for repeated in sorted({i for i in ids if ids.count(i) > 1}):
            refusals.append(Refusal(f"{prefix}{name} {repeated}", Problem.DUPLICATE_ID))
    return refusals


def _curated_repeats(drafted: CuratedDraft) -> list[Refusal]:
    """Each fixture the kept curated draft repeats, and each ID a fixture repeats."""
    fixture_ids = [d.fixture_id for d in drafted.documents]
    refusals = [
        Refusal(f"draft {repeated}", Problem.DUPLICATE_ID)
        for repeated in sorted({i for i in fixture_ids if fixture_ids.count(i) > 1})
    ]
    for document in drafted.documents:
        refusals += _repeats(document, f"draft {document.fixture_id} ")
    return list(dict.fromkeys(refusals))
```

In `build_gold`, change the docstring and the lines from `origins = _Origins()` to `if refusals: return refusals`, and the final return. The function becomes:

```python
def build_gold(
    drafted: GoldDraft,
    working: GoldDraft,
    *,
    bundle: Bundle,
    pin: Pin,
    split: SplitManifest,
    codebook: Codebook,
) -> Gold | list[Refusal]:
    """The gold ``working`` defines over ``bundle``, or every reason it cannot be.
    A kept draft that repeats an ID is refused with the rest, its subjects prefixed
    ``draft``."""
    if {drafted.event_id, working.event_id} != {bundle.name}:
        return [Refusal("event_id", Problem.UNKNOWN_DOCUMENT)]
    repeats = _repeats(drafted, "draft ")
    origins = _Origins()
    made, refusals = _items(drafted, working, bundle, origins, "")
    if refusals:
        return repeats + refusals
    try:
        partition = split.partition_of(bundle.name)
    except KeyError:
        return [Refusal("event_id", Problem.UNKNOWN_DOCUMENT)]
    gold = Gold(
        event_id=bundle.name,
        document_id=f"{bundle.name}:release",
        doc_id=bundle.document.doc_id,
        canonical_hash=bundle.document.canonical_hash,
        pin=pin,
        split_hash=split.content_hash,
        partition=partition,
        codebook=_codebook_ref(codebook),
        annotator=working.annotator,
        drafting_aid=drafted.drafting_aid,
        counts=origins.tally(),
        no_theme=working.no_theme,
        release_identification=working.release_identification,
        **made,
    )
    refusals = validate_gold(
        gold,
        bundle=bundle,
        pin=pin,
        split=split,
        codebook=codebook,
        require_signature=False,
    )
    return repeats + refusals or gold
```

`repeats + refusals or gold` reads as `(repeats + refusals) or gold`: a repeat alone still returns a list, never the built gold.

In `build_curated`, add `repeats = _curated_repeats(drafted)` after `origins = _Origins()`, and change:

```python
    if refusals:
        return refusals
    record = HardNegativeSet(
```

to:

```python
    if repeats or refusals:
        return repeats + refusals
    record = HardNegativeSet(
```

Also change its docstring to:

```python
    """The curated hard negatives ``working`` defines over Stage 1's fixtures. A
    kept draft that repeats a fixture or an ID is refused with the rest."""
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked ruff format packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/tests/test_gold.py apps/earnings-pipeline/tests/test_stage6_cli.py
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/test_independent.py -q
uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q
```

Expected: every test passes.

- [ ] **Step 5: Commit**

```bash
git log -3 --oneline
git add packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/tests/test_gold.py apps/earnings-pipeline/tests/test_stage6_cli.py
git commit -m "fix(themes): refuse a kept draft that repeats an ID (A6(1))"
```

---

### Task 2: Refuse a record under an unapproved codebook; name the ledger's problems (A6(2))

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/problems.py` (`Problem`, after `ADR_NOT_CITED` at :45; the class docstring)
- Modify: `packages/earnings-themes/src/earnings_themes/annotation.py` (`check_independent` at :286)
- Modify: `packages/earnings-themes/src/earnings_themes/independent.py` (`ledger_problem` at :48)
- Modify: `docs/data-dictionary.md` (§`Problem`)
- Test: `packages/earnings-themes/tests/test_independent.py`

**Interfaces:**
- Consumes: `CodebookStatus`, `IndependentLedger`, `sha256_hex`.
- Produces:
  - `Problem.NO_INDEPENDENT_RECORD`, `NO_LEDGER_ROW`, `REPEATED_LEDGER_ROW`, `RECORD_LOST`, and `RECORD_CHANGED`;
  - `ledger_check(ledger: IndependentLedger | None, event_id: str, record: bytes | None) -> Problem | None`, which Task 3's `verify_independent` uses;
  - `ledger_problem`, whose signature and phrases are unchanged.

- [ ] **Step 1: Write the failing tests**

In `packages/earnings-themes/tests/test_independent.py`, add to the imports:

```python
from earnings_themes.codebook import CodebookStatus
```

and add `ledger_check` to the `earnings_themes.independent` import list, which becomes:

```python
from earnings_themes.independent import (
    LEDGER,
    IndependentLedger,
    LedgerRow,
    ledger_check,
    ledger_problem,
    load_ledger,
)
```

Add after `test_a_record_for_another_event_is_refused`:

```python
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
```

Append to the end of the file:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_independent.py -q
```

Expected: collection fails with `ImportError: cannot import name 'ledger_check'`.

- [ ] **Step 3: Implement**

In `packages/earnings-themes/src/earnings_themes/problems.py`, change the class docstring to:

```python
    """Stage 6's own reasons, and Stage 11's for the gold; span checks give
    earnings-core's ``RejectionReason``."""
```

Add after `ADR_NOT_CITED = "adr_not_cited"`:

```python
    NO_INDEPENDENT_RECORD = "no_independent_record"
    NO_LEDGER_ROW = "no_ledger_row"
    REPEATED_LEDGER_ROW = "repeated_ledger_row"
    RECORD_LOST = "record_lost"
    RECORD_CHANGED = "record_changed"
```

In `annotation.py`'s `check_independent`, replace the docstring and the opening event check with:

```python
    """Every reason ``record`` does not hold over ``bundle``; empty when it does
    (GS19). A draft's checks, with no origins, partition, or signature to wait for:
    each quote anchored, the IDs, themes, ties, and ``no_theme``, and the wording
    guard over every string but the quotes. A codebook that is not approved is
    refused first, as ``validate_gold`` refuses it (P16-2(a))."""
    if record.event_id != bundle.name:
        return [Refusal("event_id", Problem.UNKNOWN_DOCUMENT)]
    if codebook.status is not CodebookStatus.APPROVED:
        return [Refusal("codebook", Problem.CODEBOOK_NOT_APPROVED)]
```

Leave the rest of the function unchanged.

In `independent.py`, add to the imports:

```python
from earnings_themes.problems import Problem
```

Replace `ledger_problem` (:48–79) with:

```python
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
```

In `docs/data-dictionary.md` §`Problem`, change the opening sentence:

```markdown
Stage 6's own refusal reasons; a span check's reason is earnings-core's
`RejectionReason`. A refusal names its item by ID or field path, never by text.
```

to:

```markdown
Stage 6's own refusal reasons, and Stage 11's for the gold; a span check's reason is
earnings-core's `RejectionReason`. A refusal names its item by ID or field path, never
by text.
```

Then add, after the `adr_not_cited` row:

```markdown
| `no_independent_record` | A dev bundle has neither an independent record nor a ledger row: the pass comes first (GS19) |
| `no_ledger_row` | A dev bundle's independent record has no ledger row: the row comes first (GS19) |
| `repeated_ledger_row` | The ledger holds more than one row for the event (GS19) |
| `record_lost` | A ledger row's independent record is gone; it is reported lost, never rewritten (GS19) |
| `record_changed` | An independent record does not hash to its ledger row; it is never edited (GS19) |
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked ruff format packages/earnings-themes/src/earnings_themes/problems.py packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/src/earnings_themes/independent.py packages/earnings-themes/tests/test_independent.py
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_independent.py packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/test_import_boundaries.py -q
uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py apps/earnings-pipeline/tests/test_stage6_cli.py -q
```

Expected: every test passes. `test_a_dev_draft_waits_for_a_record_that_matches_its_one_row` passes unchanged: the phrases are the same.

- [ ] **Step 5: Commit**

```bash
git log -3 --oneline
git add packages/earnings-themes/src/earnings_themes/problems.py packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/src/earnings_themes/independent.py packages/earnings-themes/tests/test_independent.py docs/data-dictionary.md
git commit -m "feat(themes): refuse an unapproved codebook in check_independent; name the ledger's problems (A6(2))"
```

---

### Task 3: Verify a dev record against its ledger and anchor both readings (A6(3))

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/tomlfile.py` (imports; `read` at :73; new `loads`)
- Modify: `packages/earnings-themes/src/earnings_themes/annotation.py` (new `Reading` after `class CuratedDraft`; new `_ITEMS` and `anchor_reading` after `check_independent`)
- Modify: `packages/earnings-themes/src/earnings_themes/independent.py` (module docstring; imports; new `IndependentReadings` and `verify_independent`)
- Modify: `docs/data-dictionary.md` (new §`Reading` and §`IndependentReadings`, after §`IndependentLedger`)
- Modify: `tests/contracts/test_data_dictionary.py` (`MODELS`)
- Test: `packages/earnings-themes/tests/test_tomlfile.py`
- Test: `packages/earnings-themes/tests/test_independent.py`

**Interfaces:**
- Consumes: `_repeats` (Task 1); `ledger_check` (Task 2); `_items`, `_Origins`, `check_independent`, `IndependentRecord`, `GoldDraft`, `parse`.
- Produces:
  - `tomlfile.loads(data: bytes, name: str) -> dict`;
  - `annotation.Reading(Part)`, with fields `no_theme`, `release_identification`, `quotes`, `claims`, `assignments`, and `hard_negatives`;
  - `annotation.anchor_reading(source: GoldDraft | IndependentRecord, bundle: Bundle, prefix: str) -> Reading | list[Refusal]`;
  - `independent.IndependentReadings(Part)`, with fields `event_id`, `record`, and `draft`;
  - `independent.verify_independent(event_id: str, *, ledger: IndependentLedger | None, record: bytes | None, drafted: GoldDraft, bundle: Bundle, codebook: Codebook) -> IndependentReadings | list[Refusal]`.

  Plan A's remainder computes A3's figures from `IndependentReadings`. `tomlfile.loads` is also used by Task 4.

- [ ] **Step 1: Write the failing tests**

In `packages/earnings-themes/tests/test_tomlfile.py`, change the import to:

```python
from earnings_themes.tomlfile import dumps, loads, read
```

and append:

```python
def test_bytes_read_as_the_file_holding_them_reads(tmp_path) -> None:
    """``loads`` reads bytes as ``read`` reads a file holding them, line endings
    included, so the bytes a ledger row hashes are the bytes parsed (GS19)."""
    data = b"a = 1\rb = 2\r\nc = 3\n"
    path = tmp_path / "record.toml"
    path.write_bytes(data)
    assert loads(data, "record.toml") == read(path) == {"a": 1, "b": 2, "c": 3}


def test_bytes_that_are_not_toml_or_not_utf_8_are_refused_by_name_only() -> None:
    with pytest.raises(RecordError) as refused:
        loads(b"claim = 'Revenue rose sharply\n", "record")
    assert (refused.value.name, refused.value.problems) == (
        "record",
        ("not TOML at line 2, column 1",),
    )
    assert "Revenue" not in str(refused.value)
    with pytest.raises(RecordError) as undecoded:
        loads(b"\xff", "record")
    assert undecoded.value.problems == ("not UTF-8",)
```

In `packages/earnings-themes/tests/test_independent.py`, change the `earnings_themes.annotation` import to:

```python
from earnings_themes.annotation import (
    GoldDraft,
    IndependentRecord,
    check_independent,
    load_independent,
    without_quotes,
)
```

add:

```python
from earnings_themes.gold import Origin
```

and change the `earnings_themes.independent` import to:

```python
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
```

Append to the end of the file:

```python
DATA = tomlfile.dumps(record_data()).encode()
"""The synthetic dev bundle's independent record, as the user's file holds it."""
BROKEN = b"claim = 'Demand rose widely\n"
"""Bytes that are not TOML, holding a phrase a refusal must never print."""


def drafted(**changes) -> GoldDraft:
    """The synthetic dev bundle's kept draft."""
    return parse(gold_draft(DEV, **changes), GoldDraft, "draft")


def verify(bundle, codebook, data: bytes, **changes):
    """``verify_independent`` over the synthetic dev bundle, with the kept draft and
    a ledger whose one row holds ``data``'s hash; ``changes`` replace any of them,
    and may name another ``event_id``."""
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
    assert verify(bundle, codebook, DATA, codebook=unapproved) == [
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
```

In `tests/contracts/test_data_dictionary.py`, add `annotation.Reading,` after `annotation.IndependentRecord,`, and `independent.IndependentReadings,` after `independent.IndependentLedger,` in `MODELS`.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_independent.py tests/contracts/test_data_dictionary.py -q
```

Expected: each of the three modules fails at collection with an `ImportError` (`loads`), an `ImportError` (`IndependentReadings`), and an `AttributeError` (`annotation.Reading`).

- [ ] **Step 3: Implement**

In `packages/earnings-themes/src/earnings_themes/tomlfile.py`, add `import io` to the imports (after `import json`), and replace `read` (:73–83) with:

```python
def loads(data: bytes, name: str) -> dict:
    """``data`` as TOML, read as ``read`` reads a file holding it, so the bytes a
    ledger row hashes are the bytes parsed (GS19); a refusal names ``name``, the line
    and the column, never the text."""
    try:
        return tomllib.loads(io.TextIOWrapper(io.BytesIO(data), encoding="utf-8").read())
    except tomllib.TOMLDecodeError as error:
        where = f"line {error.lineno}, column {error.colno}"
        raise RecordError(name, (f"not TOML at {where}",)) from None
    except UnicodeDecodeError:
        raise RecordError(name, ("not UTF-8",)) from None


def read(path: Path) -> dict:
    """``path`` as TOML; a refusal names the line and column, never the text."""
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        raise RecordError(path.name, ("not found",)) from None
    return loads(data, path.name)
```

`io.TextIOWrapper` applies the same universal-newline translation as `Path.read_text`, so a lone CR or a CRLF reads the same way through either.

In `annotation.py`, add after `class CuratedDraft`:

```python
class Reading(Part):
    """One reading of a bundle, anchored in memory and never written: the user's
    independent record, its items ``annotator_added``, or the kept draft, its items
    ``drafted_accepted`` (GS19; the Stage 11 spec, A6(3))."""

    no_theme: bool
    release_identification: ReleaseIdentification
    quotes: tuple[GoldQuote, ...] = ()
    claims: tuple[GoldClaim, ...] = ()
    assignments: tuple[GoldAssignment, ...] = ()
    hard_negatives: tuple[HardNegative, ...] = ()
```

Add after `check_independent`:

```python
_ITEMS = ("quotes", "claims", "assignments", "hard_negatives")


def anchor_reading(
    source: GoldDraft | IndependentRecord, bundle: Bundle, prefix: str
) -> Reading | list[Refusal]:
    """``source`` anchored over ``bundle`` in memory, or every reason it cannot be:
    a kept draft's items as drafted, and an independent record's as the user's own.
    A repeated ID is refused, since items are compared by ID. Nothing is written,
    and a refusal names its item by ID (GS13)."""
    drafted = source
    if isinstance(source, IndependentRecord):
        drafted = source.model_copy(update=dict.fromkeys(_ITEMS, ()))
    made, refusals = _items(drafted, source, bundle, _Origins(), prefix)
    refusals = _repeats(source, prefix) + refusals
    if refusals:
        return refusals
    return Reading(
        no_theme=source.no_theme,
        release_identification=source.release_identification,
        **made,
    )
```

In `independent.py`, replace the module docstring with:

```python
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
```

Replace its imports with:

```python
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
```

Append to the end of `independent.py`:

```python
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
```

In `docs/data-dictionary.md`, add after the §`IndependentLedger` table, before `## Stage 6 files`:

```markdown
### `Reading`

One reading of a dev bundle, anchored in memory and never written (the Stage 11 spec,
A6(3)): the user's independent record, its items `annotator_added`, or the kept draft,
its items `drafted_accepted`.

| Field | Type | Meaning |
| --- | --- | --- |
| `no_theme` | bool | As `Gold` |
| `release_identification` | `ReleaseIdentification` | As `Gold` |
| `quotes` | tuple of `GoldQuote` | Its quotes, anchored |
| `claims` | tuple of `GoldClaim` | Its claims |
| `assignments` | tuple of `GoldAssignment` | Its assignments |
| `hard_negatives` | tuple of `HardNegative` | Its hard-negative claims |

### `IndependentReadings`

What `verify_independent` returns for a dev bundle whose independent record matches
its one ledger row and checks clean. Stage 11's comparison figures are computed from
it; nothing of it is written or committed (FP16).

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | The dev bundle's event |
| `record` | `Reading` | The user's independent record |
| `draft` | `Reading` | The kept draft |
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked ruff format packages/earnings-themes/src/earnings_themes/tomlfile.py packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/src/earnings_themes/independent.py packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_independent.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/test_independent.py packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_import_boundaries.py -q
uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py apps/earnings-pipeline/tests/test_stage6_cli.py -q
```

Expected: every test passes. In particular, `test_import_boundaries.py` passes: `annotation.py` still does not import `independent.py`.

- [ ] **Step 5: Commit**

```bash
git log -3 --oneline
git add packages/earnings-themes/src/earnings_themes/tomlfile.py packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/src/earnings_themes/independent.py packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_independent.py tests/contracts/test_data_dictionary.py docs/data-dictionary.md
git commit -m "feat(themes): verify a dev record against its ledger and anchor both readings (A6(3))"
```

---

### Task 4: The counts-only recheck, `pilot recount` (A6(4))

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/problems.py` (`NOT_REBUILT`)
- Modify: `packages/earnings-themes/src/earnings_themes/annotation.py` (the `gold` import; new `recount` after `validate_gold`)
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py` (module docstring; imports; new `Events`, `_recount`, and `recount_command`)
- Modify: `docs/data-dictionary.md` (§`Problem`)
- Test: `packages/earnings-themes/tests/test_gold.py`
- Test: `apps/earnings-pipeline/tests/test_stage6_cli.py`

**Interfaces:**
- Consumes: `build_gold` (Task 1), `tomlfile.loads` (Task 3), `gold_toml`, `load_gold`, `load_gold_draft`, `pinned_codebook`, `pinned_split`, `documents`, `load_bundle`.
- Produces:
  - `annotation.recount(committed: bytes, drafted: GoldDraft, working: GoldDraft, *, bundle: Bundle, pin: Pin, split: SplitManifest, codebook: Codebook) -> list[Refusal]`;
  - `Problem.NOT_REBUILT`;
  - the CLI command `earnings-pipeline pilot recount [EVENTS]`.

- [ ] **Step 1: Write the failing tests**

In `packages/earnings-themes/tests/test_gold.py`, change the `earnings_themes.annotation` import to:

```python
from earnings_themes.annotation import (
    CuratedDraft,
    GoldDraft,
    build_curated,
    build_gold,
    recount,
    signed,
    validate_curated,
    validate_gold,
)
```

Append to the end of the file:

```python
def rebuilt(committed: bytes, bundles, codebook, drafted: dict, working: dict):
    """``recount`` of a committed file over its kept draft and working copy."""
    return recount(
        committed,
        parse(drafted, GoldDraft, "draft"),
        parse(working, GoldDraft, "working"),
        bundle=bundles[drafted["event_id"]],
        pin=PIN,
        split=synthetic_split(),
        codebook=codebook,
    )


def test_a_committed_file_that_rebuilds_has_nothing_to_report(
    bundles, codebook
) -> None:
    """The Stage 11 spec's A6(4): a committed file is rebuilt from its kept draft
    and working copy. A known answer for GS5's shares: a working copy that only
    adds a quote's context counts that quote as edited, since origins compare the
    draft's items, not their pointers."""
    drafted = gold_draft()
    working = gold_draft(annotator=SIGNED)
    working["quotes"][0]["prefix"] = "region. "
    gold = build(bundles, codebook, drafted, working)
    assert isinstance(gold, Gold)
    assert gold.counts.model_dump() == {
        "accepted": 7,
        "edited": 1,
        "rejected": 0,
        "added": 0,
    }
    assert rebuilt(gold_toml(gold).encode(), bundles, codebook, drafted, working) == []


def test_a_committed_file_that_does_not_rebuild_is_reported_by_field(
    bundles, codebook
) -> None:
    drafted = gold_draft()
    working = gold_draft(annotator=SIGNED)
    gold = build(bundles, codebook, drafted, working)
    assert isinstance(gold, Gold)
    counts = gold.counts.model_copy(update={"rejected": 1, "added": 2})
    tampered = gold_toml(gold.model_copy(update={"counts": counts})).encode()
    assert rebuilt(tampered, bundles, codebook, drafted, working) == [
        Refusal("counts.rejected", "counts_mismatch"),
        Refusal("counts.added", "counts_mismatch"),
        Refusal("record", "not_rebuilt"),
    ]
    resigned = gold_toml(gold.model_copy(update={"annotator": "Someone else"}))
    assert rebuilt(resigned.encode(), bundles, codebook, drafted, working) == [
        Refusal("record", "not_rebuilt")
    ]
    twice = gold_draft()
    twice["quotes"].append(dict(twice["quotes"][0]))
    committed = gold_toml(gold).encode()
    assert rebuilt(committed, bundles, codebook, twice, working) == [
        Refusal("draft quote q1", "duplicate_id")
    ]
```

In `apps/earnings-pipeline/tests/test_stage6_cli.py`, append to the end of the file:

```python
def snapshot(repo: Path) -> dict[str, bytes]:
    """Every file under the evaluation directory and data/runs/gold/."""
    roots = (repo / EVALUATION, repo / "data" / "runs" / "gold")
    return {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for root in roots
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_recount_rebuilds_each_committed_file_and_writes_nothing(repo) -> None:
    """The Stage 11 spec's A6(4): each committed file's counts come again from its
    kept draft and working copy; only IDs and counts are printed."""
    frozen(repo)
    write_drafts(repo, FIRST, gold_draft(), gold_draft(annotator=SIGNED))
    assert run(repo, "gold", "anchor", FIRST).exit_code == 0
    before = snapshot(repo)
    result = run(repo, "pilot", "recount")
    assert result.exit_code == 0, result.output
    assert lines(result) == [
        f"recounted {FIRST} (train): accepted 3, edited 0, rejected 0, added 0",
        "recounted 1 file(s): each rebuilds from its kept draft",
    ]
    assert lines(run(repo, "pilot", "recount", FIRST)) == lines(result)
    assert snapshot(repo) == before


def test_recount_reports_counts_that_do_not_rebuild_by_event_and_field(repo) -> None:
    frozen(repo)
    write_drafts(repo, FIRST, gold_draft(), gold_draft(annotator=SIGNED))
    assert run(repo, "gold", "anchor", FIRST).exit_code == 0
    edited = gold_draft(
        annotator=SIGNED,
        claims=[{"claim_id": "c1", "quote_ids": ["q1"], "claim": "Sales grew."}],
    )
    write_drafts(repo, FIRST, gold_draft(), edited)
    result = run(repo, "pilot", "recount")
    assert result.exit_code == 1
    assert lines(result) == [
        f"refused: {FIRST} counts.accepted: counts_mismatch",
        f"refused: {FIRST} counts.edited: counts_mismatch",
        f"refused: {FIRST} record: not_rebuilt",
        "Refused: 3 problem(s); GS5's shares wait until each is resolved",
    ]
    twice = gold_draft()
    twice["quotes"].append(dict(twice["quotes"][0]))
    write_drafts(repo, FIRST, twice, gold_draft(annotator=SIGNED))
    repeated = run(repo, "pilot", "recount")
    assert lines(repeated) == [
        f"refused: {FIRST} draft quote q1: duplicate_id",
        "Refused: 1 problem(s); GS5's shares wait until each is resolved",
    ]


def test_recount_needs_committed_gold_and_its_kept_drafts(repo) -> None:
    frozen(repo)
    nothing = run(repo, "pilot", "recount")
    assert nothing.exit_code == 1
    assert lines(nothing) == [f"Refused: no gold is committed under {EVALUATION}/gold"]
    second = f"{EVALUATION}/gold/{SECOND.replace(':', '_')}.toml"
    assert lines(run(repo, "pilot", "recount", SECOND)) == [
        f"Refused: {second} is not committed"
    ]
    write_drafts(repo, FIRST, gold_draft(), gold_draft(annotator=SIGNED))
    assert run(repo, "gold", "anchor", FIRST).exit_code == 0
    (repo / DRAFTS / f"{FIRST_FILE}.draft.toml").unlink()
    missing = run(repo, "pilot", "recount")
    assert missing.exit_code == 1
    assert lines(missing) == [
        f"Refused: {FIRST}: {DRAFTS.as_posix()}/{FIRST_FILE}.draft.toml is not here;"
        " GS5's counts rebuild from the kept draft and its working copy"
    ]
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py -q
```

Expected: collection fails with `ImportError: cannot import name 'recount'`.

```bash
uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q -k recount
```

Expected: 3 failed, each because Typer prints `No such command 'recount'` (exit code 2).

- [ ] **Step 3: Implement**

In `problems.py`, add after `RECORD_CHANGED = "record_changed"`:

```python
    NOT_REBUILT = "not_rebuilt"
```

In `annotation.py`, add `gold_toml` to the `earnings_themes.gold` import list, after `Support`:

```python
    Support,
    gold_toml,
    no_theme_of,
)
```

and add after `validate_gold`:

```python
def recount(
    committed: bytes,
    drafted: GoldDraft,
    working: GoldDraft,
    *,
    bundle: Bundle,
    pin: Pin,
    split: SplitManifest,
    codebook: Codebook,
) -> list[Refusal]:
    """Every reason a committed gold file is not what its kept draft and working copy
    build, each GS5 count that differs named by its field; empty when the rebuild is
    the committed bytes. GS5's shares are reported only once every file rebuilds
    (the Stage 11 spec, A6(4)). A committed file that does not read raises
    ``RecordError``."""
    made = build_gold(
        drafted, working, bundle=bundle, pin=pin, split=split, codebook=codebook
    )
    if isinstance(made, list):
        return made
    if gold_toml(made).encode() == committed:
        return []
    kept = parse(tomlfile.loads(committed, "gold"), Gold, "gold")
    return [
        Refusal(f"counts.{field}", Problem.COUNTS_MISMATCH)
        for field, count in made.counts.model_dump().items()
        if getattr(kept.counts, field) != count
    ] + [Refusal("record", Problem.NOT_REBUILT)]
```

In `apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py`, replace the module docstring with:

```python
"""``earnings-pipeline pilot``: Stage 6's split and coverage report (the Stage 6
spec, §The split and §The coverage report; plan 9), and Stage 11's counts-only
recheck and coverage v2 (the Stage 11 spec, A6(4) and A7; plan 17).

    uv run --locked earnings-pipeline pilot split
    uv run --locked earnings-pipeline pilot coverage
    uv run --locked earnings-pipeline pilot coverage --version 2
    uv run --locked earnings-pipeline pilot recount

``split`` and ``coverage`` read the pinned pilot by path and write a frozen record
under ``evaluation/<corpus>/pilot-v<N>/``, once: running either again with the same
result changes nothing, and a different result is refused. Neither reads a document,
selects anything, or sends a request (P-C7). ``coverage`` reads the state table; a
rebuild reads only the runs the report names. Version 2 reads version 1's runs, and
each signed gold file's ``no_theme`` for train and dev, and refuses until every train
and dev bundle with a parsed document has signed gold (R12.4).

``recount`` rebuilds each committed gold file from its kept draft and working copy,
under ``data/runs/gold/drafts/``, and reports any count that differs, by event and
field. It reads each file's document, prints only IDs and counts, and writes nothing
(GS5, GS13).
"""
```

Replace its imports with:

```python
from pathlib import Path
from typing import Annotated

import typer
from earnings_ingestion.events.coverage import build_coverage, load_coverage
from earnings_ingestion.events.freeze import serialize
from earnings_themes.annotation import load_gold_draft, recount
from earnings_themes.codebook import Codebook
from earnings_themes.gold import load_gold
from earnings_themes.records import RecordError, record_json
from earnings_themes.split import (
    SPLIT_POLICY,
    Partition,
    SplitEvent,
    SplitManifest,
    split_events,
)

from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
from earnings_pipeline.stage6 import (
    Layout,
    Pinned,
    documents,
    fail,
    file_stem,
    fixture_event_ids,
    guarded,
    load_bundle,
    load_pinned,
    options,
    record_error,
    transitions,
    write_once,
)
```

Append to the end of the file:

```python
Events = Annotated[
    list[str] | None,
    typer.Argument(help="Event IDs; every committed gold file when none is named."),
]


def _recount(
    layout: Layout,
    pinned: Pinned,
    split: SplitManifest,
    codebook: Codebook,
    doc_ids: dict[str, str],
    path: Path,
) -> int:
    """One committed gold file, rebuilt from its kept draft and working copy: its
    counts printed when it rebuilds, each refusal by event and field when not."""
    try:
        record = load_gold(path)
    except RecordError as error:
        record_error(error)
    event_id = record.event_id
    if path.stem != file_stem(event_id):
        fail(f"Refused: {layout.shown(path)} holds the gold of {event_id}")
    kept = [
        layout.drafts / f"{file_stem(event_id)}.{kind}.toml"
        for kind in ("draft", "working")
    ]
    for draft in kept:
        if not draft.is_file():
            fail(
                f"Refused: {event_id}: {layout.shown(draft)} is not here; GS5's"
                " counts rebuild from the kept draft and its working copy"
            )
    try:
        drafted = load_gold_draft(kept[0])
        working = load_gold_draft(kept[1])
    except RecordError as error:
        record_error(error)
    refusals = recount(
        path.read_bytes(),
        drafted,
        working,
        bundle=load_bundle(layout, doc_ids, event_id),
        pin=pinned.pin,
        split=split,
        codebook=codebook,
    )
    for refusal in refusals:
        typer.echo(f"refused: {event_id} {refusal}", err=True)
    if not refusals:
        counts = record.counts
        typer.echo(
            f"recounted {event_id} ({record.partition}): accepted {counts.accepted},"
            f" edited {counts.edited}, rejected {counts.rejected}, added"
            f" {counts.added}"
        )
    return len(refusals)


@pilot.command("recount")
@guarded
def recount_command(context: typer.Context, event_ids: Events = None) -> None:
    """Rebuild each committed gold file's GS5 counts from its kept draft and working
    copy; write nothing."""
    layout: Layout = context.obj
    codebook = pinned_codebook(layout)
    pinned = load_pinned(layout)
    split = pinned_split(layout, pinned)
    if event_ids:
        paths = [pinned.gold_dir / f"{file_stem(e)}.toml" for e in event_ids]
        if missing := [p for p in paths if not p.is_file()]:
            fail(f"Refused: {layout.shown(missing[0])} is not committed")
    else:
        paths = sorted(pinned.gold_dir.glob("*.toml"))
        if not paths:
            fail(
                f"Refused: no gold is committed under {layout.shown(pinned.gold_dir)}"
            )
    doc_ids = documents(layout, pinned)
    problems = sum(
        _recount(layout, pinned, split, codebook, doc_ids, path) for path in paths
    )
    if problems:
        fail(
            f"Refused: {problems} problem(s); GS5's shares wait until each is"
            " resolved"
        )
    typer.echo(f"recounted {len(paths)} file(s): each rebuilds from its kept draft")
```

In `docs/data-dictionary.md` §`Problem`, add after the `record_changed` row:

```markdown
| `not_rebuilt` | A committed gold file is not what its kept draft and working copy build (the Stage 11 spec, A6(4)) |
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked ruff format packages/earnings-themes/src/earnings_themes/problems.py packages/earnings-themes/src/earnings_themes/annotation.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py packages/earnings-themes/tests/test_gold.py apps/earnings-pipeline/tests/test_stage6_cli.py
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/test_independent.py packages/earnings-themes/tests/test_import_boundaries.py -q
uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py tests/contracts/test_data_dictionary.py -q
```

Expected: every test passes, including the existing coverage and split CLI tests.

- [ ] **Step 5: Commit**

```bash
git log -3 --oneline
git add packages/earnings-themes/src/earnings_themes/problems.py packages/earnings-themes/src/earnings_themes/annotation.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py packages/earnings-themes/tests/test_gold.py apps/earnings-pipeline/tests/test_stage6_cli.py docs/data-dictionary.md
git commit -m "feat(pipeline): pilot recount, the counts-only GS5 recheck (A6(4))"
```

---

### Task 5: Coverage v2's no-theme rows (A7, ingestion)

**Files:**
- Modify: `packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py` (module docstring's last bullet; new `PARTITIONS`; `NoThemeCount` at :102; `CoverageReport._counts_agree` at :123; `build_coverage` at :186)
- Modify: `docs/data-dictionary.md` (§`NoThemeCount` and §`CoverageReport`'s `no_theme` row)
- Test: `packages/earnings-ingestion/tests/test_events_coverage.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `PARTITIONS = ("train", "dev", "test")`;
  - `build_coverage(pilot, pin, transitions, *, run_ids=None, version=1, no_theme: Collection[NoThemeCount] = ())`, which Task 6's CLI calls;
  - `NoThemeCount` and `CoverageReport`, now validated.

- [ ] **Step 1: Write the failing tests**

In `packages/earnings-ingestion/tests/test_events_coverage.py`, change the coverage import to:

```python
from earnings_ingestion.events.coverage import (
    AppliedOverride,
    CoverageGap,
    NoThemeCount,
    build_coverage,
    load_coverage,
    parsed_documents,
    pilot_pin,
)
```

Append to the end of the file:

```python
def test_coverage_v2_adds_no_theme_rows_over_the_same_runs(synthetic) -> None:
    """The Stage 11 spec's A7: version 2 holds version 1's counts over version 1's
    runs, plus the rows the application counts from the signed gold, listed train,
    dev, test whatever order they arrive in, and it rebuilds byte for byte."""
    pilot, pin, transitions = synthetic
    first = build_coverage(pilot, pin, transitions)
    rows = [
        NoThemeCount(partition="dev", bundles=0, no_theme=0),
        NoThemeCount(partition="train", bundles=11, no_theme=1),
    ]
    later = [*transitions, *_later_run(transitions)]
    second = build_coverage(
        pilot, pin, later, run_ids=first.run_ids, version=2, no_theme=rows
    )
    assert [row.partition for row in second.no_theme] == ["train", "dev"]
    differ = {"coverage_version", "no_theme", "content_hash"}
    assert second.model_dump(exclude=differ) == first.model_dump(exclude=differ)
    again = build_coverage(
        pilot, pin, later, run_ids=first.run_ids, version=2, no_theme=rows[::-1]
    )
    assert serialize(again) == serialize(second)


def test_no_theme_rows_are_bounded_counted_once_and_absent_from_v1(synthetic) -> None:
    pilot, pin, transitions = synthetic
    with pytest.raises(ValueError, match="no more bundles have no theme than"):
        NoThemeCount(partition="train", bundles=1, no_theme=2)
    train = NoThemeCount(partition="train", bundles=2, no_theme=1)
    with pytest.raises(ValueError, match="counts each partition once"):
        build_coverage(pilot, pin, transitions, version=2, no_theme=[train, train])
    with pytest.raises(ValueError, match="coverage v1 holds no no-theme count"):
        build_coverage(pilot, pin, transitions, no_theme=[train])
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_coverage.py -q
```

Expected: 2 failed:
- the first with `TypeError: build_coverage() got an unexpected keyword argument 'no_theme'`;
- the second at `NoThemeCount(... no_theme=2)`, with `DID NOT RAISE`.

- [ ] **Step 3: Implement**

In `packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py`, replace the module docstring's last bullet:

```python
- **No theme.** ``no_theme`` stays empty until Stage 11 counts it over train and
  dev, and Stage 14 over test (R12.4, GS18).
```

with:

```python
- **No theme.** Version 1 holds none. From version 2, one row per partition
  counted, in train, dev, test order: Stage 11 counts train and dev, and Stage 14
  test (R12.4, GS18). The application counts them from the signed gold and passes
  them in, since ingestion reads no gold (the Stage 11 spec, FP18).
```

Add after `FAILURE_CLASSES` and its docstring:

```python
PARTITIONS = ("train", "dev", "test")
"""The partitions a no-theme row may name, in the order a report lists them."""
```

Replace `NoThemeCount` with:

```python
class NoThemeCount(_Part):
    """Stage 11's and Stage 14's count of annotated bundles with no theme."""

    partition: Literal["train", "dev", "test"]
    bundles: NonNegativeInt
    no_theme: NonNegativeInt

    @model_validator(mode="after")
    def _within(self) -> Self:
        if self.no_theme > self.bundles:
            raise ValueError("no more bundles have no theme than are counted")
        return self
```

In `CoverageReport._counts_agree`, add before `return self`:

```python
        partitions = [count.partition for count in self.no_theme]
        if partitions != sorted(set(partitions), key=PARTITIONS.index):
            raise ValueError(
                "no_theme counts each partition once, in train, dev, test order"
            )
        if self.coverage_version == 1 and self.no_theme:
            raise ValueError("coverage v1 holds no no-theme count (R12.4)")
```

Replace `build_coverage`'s signature and docstring, and add the `no_theme` field to the draft report:

```python
def build_coverage(
    pilot: PilotManifest,
    pin: PilotPin,
    transitions: Iterable[StateRecord],
    *,
    run_ids: Collection[str] | None = None,
    version: int = 1,
    no_theme: Collection[NoThemeCount] = (),
) -> CoverageReport:
    """The coverage report over ``pilot``'s documents, from ``run_ids`` or, when
    none is named, from every run recorded under the pilot. From version 2 it holds
    ``no_theme``'s rows, which the application counts from the signed gold (R12.4),
    in train, dev, test order."""
```

In the `CoverageReport(...)` call inside it, add after `overrides=_overrides(under, set(documents)),`:

```python
        no_theme=tuple(sorted(no_theme, key=lambda c: PARTITIONS.index(c.partition))),
```

In `docs/data-dictionary.md`, change §`NoThemeCount`'s rows to:

```markdown
| `partition` | `"train"`, `"dev"`, or `"test"` | The partition counted |
| `bundles` | int ≥ 0 | Its bundles with a parsed document, each with signed gold |
| `no_theme` | int ≥ 0 | Those whose gold has `no_theme` true; never more than `bundles` |
```

and §`CoverageReport`'s `no_theme` row to:

```markdown
| `no_theme` | tuple of `NoThemeCount` | Empty in version 1; from version 2, one row per partition counted, in train, dev, test order: Stage 11 adds train and dev, and Stage 14 test (R12.4, GS18) |
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked ruff format packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py packages/earnings-ingestion/tests/test_events_coverage.py
uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_coverage.py tests/contracts/test_data_dictionary.py -q
uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q -k coverage
```

Expected: every test passes. The existing `test_coverage_counts_each_state_and_rereads_only_its_runs` still gives `froze coverage v1: 27 documents`.

- [ ] **Step 5: Commit**

```bash
git log -3 --oneline
git add packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py packages/earnings-ingestion/tests/test_events_coverage.py docs/data-dictionary.md
git commit -m "feat(ingestion): coverage v2's validated no-theme rows (A7)"
```

---

### Task 6: `pilot coverage --version 2` (A7, application)

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/annotation.py` (new `check_countable` after `recount`)
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/stage6.py` (`Pinned.coverage_path` at :100–102)
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py` (imports; `coverage_command`; new `Version` and `_no_theme`)
- Test: `packages/earnings-themes/tests/test_gold.py`
- Test: `apps/earnings-pipeline/tests/test_stage6_cli.py`
- Test: `tests/integration/test_stage6_pilot_v1.py`. **The executor writes this test but never runs the file.** It skips until plan B's B7 commits `coverage-v2.json`, and the user's root suite runs it.

**Interfaces:**
- Consumes: `build_coverage(no_theme=…)`, `NoThemeCount`, and `parsed_documents` (Task 5); `pinned_codebook` and `pinned_split` (Task 4's imports); `_codebook`, `signed`, `no_theme_of`.
- Produces:
  - `annotation.check_countable(gold: Gold, *, event_id: str, pin: Pin, split: SplitManifest, codebook: Codebook) -> list[Refusal]`;
  - `Pinned.coverage_file(version: int) -> Path`;
  - the CLI option `pilot coverage --version {1,2}`.

- [ ] **Step 1: Write the failing tests**

In `packages/earnings-themes/tests/test_gold.py`, add `check_countable` to the `earnings_themes.annotation` import list, after `build_gold`:

```python
    build_gold,
    check_countable,
    recount,
```

Append to the end of the file:

```python
def test_a_committed_file_is_counted_only_when_it_holds_for_its_event(
    bundles, codebook
) -> None:
    """Coverage v2 counts a committed file's no_theme only once its event, pin,
    split, partition, codebook, signature, and no_theme hold, read without its
    document (the Stage 11 spec, A7)."""
    gold = build(bundles, codebook, gold_draft(annotator=SIGNED))
    assert isinstance(gold, Gold)

    def countable(record: Gold, event_id: str = TRAIN) -> list[Refusal]:
        return check_countable(
            record,
            event_id=event_id,
            pin=PIN,
            split=synthetic_split(),
            codebook=codebook,
        )

    assert countable(gold) == []
    tampered = gold.model_copy(
        update={
            "pin": PIN.model_copy(update={"pilot_hash": "4" * 64}),
            "split_hash": "5" * 64,
            "partition": Partition.DEV,
            "codebook": gold.codebook.model_copy(update={"codebook_version": 1}),
            "annotator": "   ",
            "no_theme": True,
        }
    )
    assert countable(tampered) == [
        Refusal("pin", "wrong_pin"),
        Refusal("split_hash", "wrong_split"),
        Refusal("partition", "wrong_partition"),
        Refusal("codebook", "wrong_codebook"),
        Refusal("annotator", "unsigned"),
        Refusal("no_theme", "no_theme_mismatch"),
    ]
    assert countable(gold, DEV) == [
        Refusal("event_id", "unknown_document"),
        Refusal("partition", "wrong_partition"),
    ]
```

In `apps/earnings-pipeline/tests/test_stage6_cli.py`, change the `earnings_themes.gold` import to:

```python
from earnings_themes.gold import (
    ReleaseIdentification,
    ReleaseLabel,
    gold_toml,
    load_gold,
    load_hard_negatives,
)
```

Append to the end of the file:

```python
def signed_training(repo: Path, no_theme: str) -> list[str]:
    """Signed gold, through gold anchor, for each training event with a parsed
    document: each quotes SENTENCE, which every synthetic training release holds
    once, and ``no_theme``'s one claim takes no theme."""
    split = load_split(repo / EVALUATION / "split-v1.json")
    events = [e for e in split.events_in(Partition.TRAIN) if e not in UNPARSED]
    unmatched = [{"claim_id": "c1", "theme_id": "unmatched", "support": "uncertain"}]
    for event_id in events:
        changes = {}
        if event_id == no_theme:
            changes = {"no_theme": True, "assignments": unmatched}
        write_drafts(
            repo,
            event_id,
            gold_draft(event_id, **changes),
            gold_draft(event_id, annotator=SIGNED, **changes),
        )
    result = run(repo, "gold", "anchor", *events)
    assert result.exit_code == 0, result.output
    return events


def test_coverage_takes_versions_1_and_2_and_v2_needs_v1(repo) -> None:
    assert lines(run(repo, "pilot", "coverage", "--version", "3")) == [
        "Refused: coverage has versions 1 and 2"
    ]
    early = run(repo, "pilot", "coverage", "--version", "2")
    assert early.exit_code == 1
    assert lines(early) == [
        f"Refused: {EVALUATION}/coverage-v1.json is not frozen; coverage v2 reads"
        " its runs: run pilot coverage"
    ]
    assert not (repo / EVALUATION / "coverage-v2.json").exists()


def test_coverage_v2_waits_for_every_train_and_dev_bundle_s_gold(repo) -> None:
    """The Stage 11 spec's A7: version 2 is refused until every train and dev
    bundle with a parsed document has signed gold, and each is named."""
    frozen(repo)
    assert run(repo, "pilot", "coverage").exit_code == 0
    split = load_split(repo / EVALUATION / "split-v1.json")
    events = [e for e in split.events_in(Partition.TRAIN) if e not in UNPARSED]
    result = run(repo, "pilot", "coverage", "--version", "2")
    assert result.exit_code == 1
    assert lines(result) == [
        *(f"no signed gold  {event_id}" for event_id in events),
        (
            "Refused: 11 train and dev bundle(s) with a parsed document have no"
            " signed gold; coverage v2 waits for every one (R12.4)"
        ),
    ]
    assert not (repo / EVALUATION / "coverage-v2.json").exists()


def test_coverage_v2_counts_no_theme_over_version_1_s_runs(repo) -> None:
    """The Stage 11 spec's A7: version 2 freezes once, holds version 1's runs and
    state counts, and adds train's and dev's rows; a later run changes nothing. The
    synthetic split has no dev event (GS6), so dev's row is 0 of 0."""
    frozen(repo)
    assert run(repo, "pilot", "coverage").exit_code == 0
    signed_training(repo, no_theme=FIRST)
    result = run(repo, "pilot", "coverage", "--version", "2")
    assert result.exit_code == 0, result.output
    assert lines(result)[1:9] == [
        "parsed  24",
        "failed  1",
        "unavailable  2",
        "gap  restricted  (D4: never repaired by reselecting)",
        "no_theme  train  1 of 11 bundles",
        "no_theme  dev  0 of 0 bundles",
        f"runs  {ACQUISITION_RUN}",
        "froze coverage v2: 27 documents",
    ]
    first = load_coverage(repo / EVALUATION / "coverage-v1.json")
    second = load_coverage(repo / EVALUATION / "coverage-v2.json")
    assert (second.run_ids, second.states) == (first.run_ids, first.states)
    kept = (repo / EVALUATION / "coverage-v2.json").read_bytes()
    states = repo / EVENT_RUNS / "states"
    parsed = next(t for t in read_runs(states) if t.to_state is DocumentState.PARSED)
    later = parsed.model_copy(
        update={
            "run_id": "stage-7",
            "sequence": 0,
            "recorded_at": ACQUIRED_AT.replace(hour=14),
            "from_state": DocumentState.PARSED,
            "to_state": DocumentState.PARTIAL,
            "attempts": (),
        }
    )
    write_run(states, [later])
    again = run(repo, "pilot", "coverage", "--version", "2")
    assert again.exit_code == 0, again.output
    assert lines(again)[-2] == "unchanged: coverage v2: 27 documents"
    assert (repo / EVALUATION / "coverage-v2.json").read_bytes() == kept


def test_coverage_v2_refuses_gold_it_may_not_count(repo) -> None:
    frozen(repo)
    assert run(repo, "pilot", "coverage").exit_code == 0
    signed_training(repo, no_theme=FIRST)
    path = repo / EVALUATION / "gold" / f"{FIRST_FILE}.toml"
    record = load_gold(path)
    other = record.pin.model_copy(update={"pilot_hash": "4" * 64})
    tampered = gold_toml(record.model_copy(update={"pin": other}))
    path.write_text(tampered, encoding="utf-8")
    result = run(repo, "pilot", "coverage", "--version", "2")
    assert result.exit_code == 1
    assert lines(result) == [
        f"refused: {FIRST} pin: wrong_pin",
        "Refused: 1 problem(s); nothing written",
    ]
    assert not (repo / EVALUATION / "coverage-v2.json").exists()
```

In `tests/integration/test_stage6_pilot_v1.py`, add after `test_the_committed_coverage_report_reproduces_from_its_runs`:

```python
def test_a_committed_coverage_v2_rebuilds_unchanged_from_v1_s_runs() -> None:
    """The Stage 11 spec's A7: coverage v2, frozen at plan B's B7, counts train's
    and dev's no-theme bundles over coverage v1's runs; rebuilding it changes
    nothing."""
    committed = EVALUATION / "coverage-v2.json"
    if not committed.is_file():
        pytest.skip("coverage-v2.json is frozen at plan B's B7")
    if not STATES.is_dir():
        pytest.skip("data/runs/events/ is not here: each Stage 6 gate runs this test")
    before = committed.read_bytes()
    result = RUNNER.invoke(
        cli.app, ["pilot", "--repo", str(REPO), "coverage", "--version", "2"]
    )
    assert result.exit_code == 0, result.output
    assert "unchanged: coverage v2: 40 documents" in result.output.splitlines()
    assert committed.read_bytes() == before
    report = load_coverage(committed)
    assert report.run_ids == load_coverage(EVALUATION / "coverage-v1.json").run_ids
    assert [(row.partition, row.bundles) for row in report.no_theme] == [
        ("train", 20),
        ("dev", 8),
    ]
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py -q
```

Expected: collection fails with `ImportError: cannot import name 'check_countable'`.

```bash
uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q -k "coverage_v2 or versions_1_and_2"
```

Expected: 4 failed, because Typer refuses `--version` as `No such option` (exit code 2).

- [ ] **Step 3: Implement**

In `annotation.py`, add after `recount`:

```python
def check_countable(
    gold: Gold,
    *,
    event_id: str,
    pin: Pin,
    split: SplitManifest,
    codebook: Codebook,
) -> list[Refusal]:
    """Every reason a committed gold file's ``no_theme`` may not be counted for
    ``event_id`` in coverage v2, read without its document: its event, pin, split,
    partition, codebook, signature, and ``no_theme`` against its assignments; empty
    when it may (the Stage 11 spec, A7; R12.4). ``gold validate`` checks the rest
    against the document."""
    refusals = []
    if gold.event_id != event_id:
        refusals.append(Refusal("event_id", Problem.UNKNOWN_DOCUMENT))
    if gold.pin != pin:
        refusals.append(Refusal("pin", Problem.WRONG_PIN))
    if gold.split_hash != split.content_hash:
        refusals.append(Refusal("split_hash", Problem.WRONG_SPLIT))
    try:
        partition = split.partition_of(event_id)
    except KeyError:
        partition = None
    if gold.partition != partition:
        refusals.append(Refusal("partition", Problem.WRONG_PARTITION))
    refusals += _codebook(gold.codebook, codebook)
    if not signed(gold.annotator):
        refusals.append(Refusal("annotator", Problem.UNSIGNED))
    if gold.no_theme != no_theme_of(gold.assignments):
        refusals.append(Refusal("no_theme", Problem.NO_THEME_MISMATCH))
    return refusals
```

In `apps/earnings-pipeline/src/earnings_pipeline/stage6.py`, replace:

```python
    @property
    def coverage_path(self) -> Path:
        return self.evaluation / "coverage-v1.json"
```

with:

```python
    def coverage_file(self, version: int) -> Path:
        """``coverage-v<version>.json``: version 1 by plan 9, version 2 by Stage 11."""
        return self.evaluation / f"coverage-v{version}.json"
```

In `pilot_cli.py`, change three imports:

```python
from earnings_ingestion.events.coverage import (
    NoThemeCount,
    build_coverage,
    load_coverage,
    parsed_documents,
)
```

```python
from earnings_themes.annotation import check_countable, load_gold_draft, recount
```

```python
from earnings_themes.problems import Refusal
```

The last is a new line, after the `earnings_themes.gold` import. Then add `refuse,` to the `earnings_pipeline.stage6` import list, after `record_error,`.

Replace the whole `@pilot.command("coverage")` function, `coverage_command`, with the code below. Its line numbers moved when Task 4 rewrote the module docstring and imports.

```python
Version = Annotated[
    int,
    typer.Option(
        "--version", help="1, or 2 with train's and dev's no-theme counts (R12.4)."
    ),
]


def _no_theme(
    layout: Layout, pinned: Pinned, run_ids: tuple[str, ...]
) -> list[NoThemeCount]:
    """Train's and dev's no-theme rows over the bundles with a parsed document
    under ``run_ids``. Each bundle needs committed gold whose pin, split, partition,
    codebook, signature, and ``no_theme`` hold, read without its document (R12.4)."""
    under = [t for t in transitions(layout) if t.run_id in run_ids]
    parsed = parsed_documents(under, pinned.pin.pilot_hash)
    split = pinned_split(layout, pinned)
    codebook = pinned_codebook(layout)
    rows: list[NoThemeCount] = []
    unsigned: list[str] = []
    refusals: list[Refusal] = []
    for partition in (Partition.TRAIN, Partition.DEV):
        events = [e for e in split.events_in(partition) if e in parsed]
        flags = []
        for event_id in events:
            path = pinned.gold_dir / f"{file_stem(event_id)}.toml"
            if not path.is_file():
                unsigned.append(event_id)
                continue
            try:
                gold = load_gold(path)
            except RecordError as error:
                record_error(error)
            found = check_countable(
                gold, event_id=event_id, pin=pinned.pin, split=split, codebook=codebook
            )
            refusals += [Refusal(f"{event_id} {r.subject}", r.reason) for r in found]
            flags.append(gold.no_theme)
        rows.append(
            NoThemeCount(
                partition=partition.value, bundles=len(events), no_theme=sum(flags)
            )
        )
    for event_id in unsigned:
        typer.echo(f"no signed gold  {event_id}", err=True)
    if unsigned:
        fail(
            f"Refused: {len(unsigned)} train and dev bundle(s) with a parsed document"
            " have no signed gold; coverage v2 waits for every one (R12.4)"
        )
    if refusals:
        refuse(refusals)
    return rows


@pilot.command("coverage")
@guarded
def coverage_command(context: typer.Context, version: Version = 1) -> None:
    """Count the pinned pilot's documents by state, and freeze coverage-v<N>.json;
    version 2 adds train's and dev's no-theme counts over version 1's runs."""
    layout: Layout = context.obj
    if version not in (1, 2):
        fail("Refused: coverage has versions 1 and 2")
    pinned = load_pinned(layout)
    first = pinned.coverage_file(1)
    if version == 2 and not first.is_file():
        fail(
            f"Refused: {layout.shown(first)} is not frozen; coverage v2 reads its"
            " runs: run pilot coverage"
        )
    try:
        run_ids = load_coverage(first).run_ids if first.is_file() else None
    except ValueError as error:
        fail(f"Refused: {error}")
    no_theme = _no_theme(layout, pinned, run_ids) if version == 2 else []
    try:
        report = build_coverage(
            pinned.pilot,
            pinned.coverage_pin,
            transitions(layout),
            run_ids=run_ids,
            version=version,
            no_theme=no_theme,
        )
    except ValueError as error:
        fail(f"Refused: {error}")
    path = pinned.coverage_file(version)
    created = write_once(path, serialize(report), layout)
    _said(pinned, layout)
    for count in report.states:
        if count.count:
            typer.echo(f"{count.state}  {count.count}")
    for gap in report.gaps:
        typer.echo(f"gap  {gap.state}  ({gap.basis}: never repaired by reselecting)")
    for override in report.overrides:
        typer.echo(
            f"override  {override.override_id}  {override.document_id}"
            f"  {override.verdict}"
        )
    for row in report.no_theme:
        typer.echo(
            f"no_theme  {row.partition}  {row.no_theme} of {row.bundles} bundles"
        )
    typer.echo(f"runs  {', '.join(report.run_ids)}")
    verb = "froze" if created else "unchanged:"
    typer.echo(
        f"{verb} coverage v{report.coverage_version}: {report.documents} documents"
    )
    typer.echo(f"{layout.shown(path)}  {report.content_hash}")
```

`Version` and `_no_theme` sit above `coverage_command`, so leave `Events`, `_recount`, and `recount_command` (Task 4) at the end of the file. The flow for version 1 is unchanged: it reads its own frozen file's runs when that file exists, every run otherwise, and holds no no-theme row.

Then run this and confirm it prints nothing:

```bash
grep -rn "coverage_path" packages apps tests
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked ruff format packages/earnings-themes/src/earnings_themes/annotation.py apps/earnings-pipeline/src/earnings_pipeline/stage6.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py packages/earnings-themes/tests/test_gold.py apps/earnings-pipeline/tests/test_stage6_cli.py tests/integration/test_stage6_pilot_v1.py
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/test_independent.py packages/earnings-themes/tests/test_import_boundaries.py -q
uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py packages/earnings-ingestion/tests/test_events_coverage.py tests/contracts/test_data_dictionary.py -q
uv run --locked ruff check tests/integration/test_stage6_pilot_v1.py
```

Expected:
- every test passes, including `test_coverage_counts_each_state_and_rereads_only_its_runs` for version 1;
- Ruff is clean on the integration file, which is not run.

- [ ] **Step 5: Commit**

```bash
git log -3 --oneline
git add packages/earnings-themes/src/earnings_themes/annotation.py apps/earnings-pipeline/src/earnings_pipeline/stage6.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py packages/earnings-themes/tests/test_gold.py apps/earnings-pipeline/tests/test_stage6_cli.py tests/integration/test_stage6_pilot_v1.py
git commit -m "feat(pipeline): pilot coverage --version 2 counts train's and dev's no-theme bundles (A7)"
```

---

### Task 7: The wording guard scans the ledger and Stage 11's records (A9; the user's gate file)

**This task edits `tests/integration/test_stage6_wording.py`, the user's gate file.** The executor edits it and runs Ruff over it, nothing else. The user runs it at Task 8's gate 2.

**Files:**
- Modify: `tests/integration/test_stage6_wording.py` (module docstring's first bullet; `STAGE6` at :37; new `STAGE11` and one test)

**Interfaces:**
- Consumes: `STAGE6`.
- Produces: `STAGE11`, the planned Stage 11 paths, which plan A's remainder and plan B rely on being scanned.

- [ ] **Step 1: Write the test, and the globs it needs**

There is no red step the executor can run: the file is the user's gate. The new test fails without the globs, because the ledger path matches none of `STAGE6`'s patterns today (P16-3), and the user's gate 2 shows it passing.

Replace the module docstring's first bullet:

```python
- **The files.** Under ``evaluation/``: the split, the coverage report, the gold,
  and the briefs; codebook v0, ADR 0003, and the verification record; and the
  curated hard negatives: whichever are committed yet. Also Stage 7's prompts,
  under ``prompts/`` (the Stage 7 spec, §Wording guard). A Markdown file is read a
  paragraph at a time, its lines joined, so a phrase copied across a wrapped line is
  still caught.
```

with:

```python
- **The files.** Under ``evaluation/``: the split, the coverage reports, the gold,
  and the briefs; the independent-pass ledger (P16-3), and the records Stage 11
  commits beside it, its labels among them (the Stage 11 spec, A9); codebook v0, ADR
  0003, and the verification record; and the curated hard negatives: whichever are
  committed yet. Also Stage 7's prompts, under ``prompts/`` (the Stage 7 spec,
  §Wording guard). A Markdown file is read a paragraph at a time, its lines joined,
  so a phrase copied across a wrapped line is still caught. A TOML file is read
  through ``tomllib``, so its comments are not scanned.
```

Change `STAGE6` to:

```python
STAGE6 = (
    "evaluation/*/pilot-v*/*.json",
    "evaluation/*/pilot-v*/*.toml",
    "evaluation/*/pilot-v*/labels/*.toml",
    "evaluation/*/pilot-v*/gold/*.toml",
    "evaluation/*/pilot-v*/briefs/*.md",
    "codebooks/*/codebook-v*.toml",
    "docs/adr/0003-*.md",
    "docs/verification/pilot-v1-gold-set.md",
    "tests/fixtures/gold/*.toml",
    "prompts/**/*.md",
)
```

Add after `PROMPTS`:

```python
STAGE11 = (
    "evaluation/djia-2024q3-2026q2/pilot-v1/independent-pass.toml",
    "evaluation/djia-2024q3-2026q2/pilot-v1/preregistration-v1.toml",
    "evaluation/djia-2024q3-2026q2/pilot-v1/labels/support-labels-v1.toml",
    "evaluation/djia-2024q3-2026q2/pilot-v1/calibration-v1.json",
    "evaluation/djia-2024q3-2026q2/pilot-v1/coverage-v2.json",
    "evaluation/djia-2024q3-2026q2/pilot-v1/report-v1.json",
    "evaluation/djia-2024q3-2026q2/pilot-v1/gates-v1.toml",
)
"""The ledger (plan 16) and the records Stage 11 commits (the Stage 11 spec,
§Artifacts)."""
```

Add after `test_the_prompts_are_among_the_files_checked`:

```python
def test_the_ledger_and_stage_11_s_records_are_among_the_files_checked(
    tmp_path: Path,
) -> None:
    """The ledger (P16-3) and each record Stage 11 commits beside the gold are
    scanned once committed (the Stage 11 spec, A9). Most are not written yet, so
    each is made empty under ``tmp_path``, and ``STAGE6``'s patterns find it."""
    for name in STAGE11:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).touch()
    found = {
        path.relative_to(tmp_path).as_posix()
        for pattern in STAGE6
        for path in tmp_path.glob(pattern)
    }
    assert set(STAGE11) <= found
```

- [ ] **Step 2: Check it with Ruff only**

```bash
uv run --locked ruff format tests/integration/test_stage6_wording.py
uv run --locked ruff check tests/integration/test_stage6_wording.py
```

Expected: Ruff is clean. Do not run pytest on this file.

- [ ] **Step 3: Commit**

```bash
git log -3 --oneline
git add tests/integration/test_stage6_wording.py
git commit -m "test(stage6): scan the ledger and Stage 11's records in the wording guard (A9, P16-3)"
```

---

### Task 8: Scoped checks, the user's gates, and completion (gate)

**Files:**
- Modify: `specs/feasibility-pilot-and-threshold-calibration.md` (the slice stamp, at the end of §Rollout)
- Modify: `specs/deferred_items.md` (ticks and a note)
- Modify: this plan (completion markup), then `git mv` it to `specs/plans/completed/`

- [ ] **Step 1: Run every scoped check in the worktree**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/test_independent.py packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_import_boundaries.py packages/earnings-ingestion/tests/test_events_coverage.py apps/earnings-pipeline/tests/test_stage6_cli.py tests/contracts/test_data_dictionary.py -q
uv run --locked ruff check .
uv run --locked ruff format --check .
git diff --stat main...HEAD -- evaluation config data CLAUDE.md
```

Expected:
- every test passes, and Ruff prints no finding;
- the last command prints nothing: no committed record, no curated file, and no `CLAUDE.md` line changed.

Record the exact pass counts for the handoff.

- [ ] **Step 2 (gate): Hand the user the checks only they run**

Put this to the user in chat, with `<sha>` set to `git rev-parse HEAD`, and wait for the results:

> Plan 17 (Stage 11 plan A, slice 1) is implemented on `stage-11-plan-a-gold-and-coverage` at `<sha>`. Four checks are yours, because they read pilot data or run the full suite.
>
> Run them in the main checkout, `/Users/lowell/Projects/earnings-themes`, after `git switch --detach <sha>`, and finish with `git switch main`:
>
> 1. **The root suite:** `uv run --locked --all-packages pytest packages apps tests -m "not live and not browser"`.
>    - The baseline at `cff6313` was 4296 passed, 1 skipped, 28 deselected, 1 warning, in 857 s.
>    - Expect more passed (this plan's tests) and 0 failed.
>    - Expect one more skip: `test_a_committed_coverage_v2_rebuilds_unchanged_from_v1_s_runs`, until plan B's B7.
>
>    Please send the passed, skipped and deselected counts.
> 2. **The Stage 6 wording test:** `uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs`.
>    - This plan edited that file (Task 7). It gains `evaluation/*/pilot-v*/*.toml`, which scans the ledger once you commit it, and `labels/*.toml`, plus one test.
>    - Expect 7 passed and 0 skipped (6 before).
> 3. **The committed gold, checked and recounted:**
>    - `uv run --locked earnings-pipeline gold validate` should print three `valid: … (train), …, signed` lines.
>    - Then `uv run --locked earnings-pipeline pilot recount` should print one `recounted <event> (train): accepted N, edited N, rejected N, added N` line per committed file, then `recounted 3 file(s): each rebuilds from its kept draft`.
>    - A refusal there names an event and a field only. It means that file's counts no longer rebuild from its kept draft and working copy. Please send that line, which GS5's shares wait on.
> 4. **Coverage:**
>    - `uv run --locked earnings-pipeline pilot coverage` should end with `unchanged: coverage v1: 40 documents` and its path and hash.
>    - Then `uv run --locked earnings-pipeline pilot coverage --version 2` should exit 1, with one `no signed gold  <event>` line per train and dev bundle without committed gold. That is 25 while 3 are signed. Then `Refused: 25 train and dev bundle(s) …`.
>    - `evaluation/djia-2024q3-2026q2/pilot-v1/coverage-v2.json` must not exist afterwards.

If any check fails, stop, and debug it with systematic-debugging before going on. Debug from the test name and reason the user reports, never from pilot text.

- [ ] **Step 3: Run the Plan Completion Protocol**

Follow writing-plans' Plan Completion Protocol:
- **Resolve-before-defer:** ask the user about anything left open, in one batch (AskUserQuestion, default option first).
- **Markup:** tick the steps, and set the status header `**Status: COMPLETE (YYYY-MM-DD)** — executed via <skill>; …`.
- **Deferred items,** in `specs/deferred_items.md`:
  - tick `10-harden-the-gold-before-bundle-4`'s item "Refuse a kept draft that repeats an ID" with `→ done in plan 17`;
  - tick `P16-2` with `→ done in plan 17: check_independent refuses an unapproved codebook; verify_independent checks the ledger and anchors both readings`;
  - tick `P16-3` with `→ done in plan 17: STAGE6 globs evaluation/*/pilot-v*/*.toml`, but only after the user's gate 2 passes;
  - under `P16-4`, add `(1) fixed in plan 17: ledger_check tests ledger is not None`, and leave it unticked, since items (2)–(6) remain;
  - plan 12's two items stay deferred (FP19).
- **Backlog triage:** run it as the protocol describes.
- **The slice stamp (D17-11):** append at the end of the spec's §Rollout, after its last paragraph:

  ```text
  > Plan A, slice 1: COMPLETE (YYYY-MM-DD) — implemented by plan 17 (specs/plans/completed/17-feasibility-pilot-and-threshold-calibration-plan-a-slice-1.md): A6, A7, and A9's wording globs. Next: write plan A's remainder (A1–A5, A8, and A9's dictionary rows).
  ```

  Commit it as `docs(specs): stamp Stage 11 plan A's first slice`.

  Do not append `Plan A: COMPLETE`. Do not tick Stage 11 on the roadmap.
- **Retire:** `git mv` this plan to `specs/plans/completed/` in one `chore(specs): retire plan 17` commit.

  **Do not move the spec**, an exception to the protocol's spec-retire rule (D17-11): plans for A's remainder and B still implement it.

- [ ] **Step 4: Hand off what goes stale**

Tell the user, without editing these files:
- `CLAUDE.md`'s "Current state" names Stages 1–10. Stage 11's first slice could be noted there, but per the spec's Rollout and the user's rule, only with the user's approval.
- Plan A's remainder is next: a writing-plans session from `main`, using this plan's §Handoffs.

Then go on with finishing-a-development-branch.

---

## Handoffs to plan A's remainder

Verified at `c1e7ac7`, while this plan was written. Recheck each line number before relying on it.

- **FP23 and stored-run reuse.** `apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py` binds `"replay"` twice:
  - at :957, a stored coding run is reused only when `record.cache_mode == "replay"`;
  - at :1020, the support configuration hash includes `"cache_mode": "replay"`.

  The spec's A8 names only the first.

  A stored coding run is reused with its decisions. Coding cache keys bind the request and the runtime identity, and no run ID (`coding/cache.py:29`, `coding_key`). Support cache keys bind the extraction `RunRecord` (`support/cache.py:107`, `"source_run"`).

  So reusing only the pass's extraction run, and replaying coding and support from the pass's caches, might dispatch nothing without widening :957. The remainder's design should settle this with the user before planning A8's `pilot run`.
- **A1, fresh mode, is a schema change for each of the three cache classes.**
  - Extraction's `RunRecord` and Stage 8's `SupportRunRecord` record no cache mode.
  - Coding's is `Literal["live", "replay"]` (`coding/records.py:326`), with store invariants at `coding/store.py:492` and :514.
- **`pilot independent` (A8) composes `verify_independent`** with `gold_cli.py`'s `_independent_path` and `_read_ledger`. Move those two to `stage6.py` when this second caller arrives. It runs for dev events only, and prints A3's figures computed from `IndependentReadings`. The anchored readings stay in memory, or local under `data/runs/pilot/` (FP16).
- **Plan B's B7** freezes coverage v2 with `pilot coverage --version 2`, and runs `pilot recount` before GS5's shares are reported (§Failure handling).
- **A9's dictionary rows** for the remainder's records (labels, preregistration, calibration, report, gates) go with the tasks that add them. Task 7's globs already scan their paths.
- **Size.** The remainder is likely two or more plans: A1 and A2, the runtime; A3–A5, evaluation, labels and calibration; and A8, the commands.

---

## Self-review

- **Spec coverage:**

  | Spec point | Where it's built |
  | --- | --- |
  | A6(1): `build_gold` and `build_curated` refuse a kept draft that repeats a quote, claim or fixture ID, with a test | Task 1 (library and CLI tests) |
  | A6(2): `check_independent` refuses an unapproved codebook, with a test (P16-2a) | Task 2 |
  | A6(3): check against the ledger hash, `check_independent`, anchor both in memory, write nothing; invented records (P16-2b) | Task 3. The figures go to the remainder, by the user's choice (D17-4) |
  | A6(4): a counts-only recheck rebuilds each committed file's GS5 counts from its kept draft, and reports a mismatch by event and field | Task 4 |
  | A7: `--version 2` reads each signed file's `no_theme`, and passes train and dev rows to `build_coverage` | Tasks 5 and 6 |
  | A7: refuses until all train and dev files are signed | Task 6 (D17-7: the split's train and dev bundles with a parsed document, 28 for pilot v1) |
  | A7: reproduces byte for byte on the synthetic cohort | Tasks 5 and 6 (rebuild, and a later run, unchanged) |
  | A9: globs for `pilot-v*/*.toml`, `*.json` and `labels/*.toml`; the first closes P16-3 | Task 7. `*.json` was already globbed |
  | §Deferred items: plan 10's item, P16-2 and P16-3 | Task 8, Step 3 |
  | §Verification: "A6's refusals and the independent comparison over invented records; coverage v2's byte reproduction; the wording guard and data-dictionary checks" | Tasks 1–7 |
  | §Gates, plan A: the session's scoped tests and Ruff; the user's suite and wording gate | Task 8, Steps 1 and 2 |
  | FP18: commands extend `pilot`; coverage v2 stays in ingestion's `build_coverage`, with the application supplying the rows | Tasks 4–6 |

  Not here, by D17-1: A1–A5, A8, and A9's dictionary rows for those records.
- **Placeholders:** none.
  - Every code step shows its code.
  - The user's gates ask for counts that no session can know in advance.
  - `<sha>` and the dates are filled in at execution.
- **Type consistency.** These names are used identically across Tasks 1–7:
  - `_repeats(draft, prefix)`, `_curated_repeats(drafted)`;
  - `ledger_check(ledger, event_id, record) -> Problem | None`, `ledger_problem(...) -> str | None`;
  - `tomlfile.loads(data, name)`;
  - `Reading`, `anchor_reading(source, bundle, prefix)`;
  - `IndependentReadings(event_id, record, draft)`, `verify_independent(event_id, *, ledger, record, drafted, bundle, codebook)`;
  - `recount(committed, drafted, working, *, bundle, pin, split, codebook) -> list[Refusal]`;
  - `check_countable(gold, *, event_id, pin, split, codebook) -> list[Refusal]`;
  - `PARTITIONS`, `NoThemeCount`, `build_coverage(..., no_theme=...)`;
  - `Pinned.coverage_file(version)`, `Version`, `_no_theme(layout, pinned, run_ids)`, `Events`, `_recount(...)`, `recount_command`;
  - `Problem.NO_INDEPENDENT_RECORD`, `NO_LEDGER_ROW`, `REPEATED_LEDGER_ROW`, `RECORD_LOST`, `RECORD_CHANGED`, and `NOT_REBUILT`.
