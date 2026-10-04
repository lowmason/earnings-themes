# Harden the Pilot Gold Before Bundle 4 — Implementation Plan

**Status: COMPLETE (2026-10-03)** — executed via subagent-driven-development; deferred items in specs/deferred_items.md

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

> Requirement: `specs/deferred_items.md`, section
> `9-pilot-codebook-split-and-gold-set-protocol — 2026-10-03`, the item "Harden the
> gold before the next Task 19 bundle is anchored". The plan has no spec: that item,
> of Size `plan`, is its requirement, and no brainstorming preceded it. Its
> completion ticks the item, and it lands before any further pilot v1 bundle, the
> 4th of 28 train and dev, is anchored.

**Goal:** Harden Stage 6's gold before the next bundle: refuse a claim no assignment
row codes and a quote nothing cites (M1), take each record's drafting aid from its
kept draft (T8-M1), and count the pilot's sentences that sit in a list item under an
`other` element (M5); with two folds from plan 9's gaps item, T8-M2 and T6-M2.

**Architecture:**

- **Code.** Every change is in `earnings-themes`: `problems.py` gains one `Problem`
  member, and `annotation.py` changes in `_ids`, `validate_curated`, `build_gold`,
  and `build_curated`. The application, `anchoring.py`, and every model are
  unchanged.
- **Records.** No committed byte changes. Each committed record re-anchors from its
  kept draft and signed working copy to the same bytes, which Task 5 shows.
- **The count.** A program in this plan (Task 5) reads canonical documents through
  the application's loaders, and prints IDs and counts only. It runs first on Stage
  1's fixtures, as calibration against a pinned test (Task 4), then over the pilot.
  The verification record holds the result.

**Tech Stack:** Python 3.14.0 and uv 0.12.15; pydantic 2.13.5, typer 0.27.2, pytest
9.1.1, and Ruff 0.16.8, all locked. No new dependency: `uv.lock` does not change.

## The item this plan implements

`specs/deferred_items.md`, line 1026 at `0242468`, deferred by the user on 2026-10-03
from plan 9's final review. Its three parts, with their code at `0242468`:

1. **M1.** `_ids` (`packages/earnings-themes/src/earnings_themes/annotation.py:258-298`)
   accepts a claim with no assignment row, and a quote that no claim or hard negative
   cites, though R9.9 codes every claim, under a theme or `unmatched`. Refuse both,
   with a new `Problem` member (`problems.py:13`) and its row in
   `docs/data-dictionary.md` §`Problem`, which `tests/contracts/test_data_dictionary.py`
   holds in sync with the enum. Task 1.
2. **T8-M1.** `build_gold` (`annotation.py:211`; `drafting_aid=working.drafting_aid`
   at `:241`) and `build_curated` (`:396`; at `:444`) take `drafting_aid` from the
   working copy, so an edit there would change the recorded model or date (GS5).
   Take it from the kept draft, and show by re-anchoring that the three committed
   bundles and `tests/fixtures/gold/hard-negatives.toml` are unchanged. Tasks 3 and 5.
3. **M5.** Count, by a program that prints counts only, the narrative sentences of
   the 40 pilot documents that sit in a walker-1 list item under an `other` element,
   which the anchor refuses as `not_narrative` (`anchoring.py:119-120`, T6-M1), and
   record the count in `docs/verification/pilot-v1-gold-set.md`. Calibrate the
   program first on Stage 1's committed fixtures, where plan 9's final review
   measured 10 such sentences, in 1 of 8. Tasks 4 and 5.

**Done when** (the item): (1) and (2) land with their tests, and (3)'s count is in
the verification record, before any further bundle is anchored.

**Two folds** (P10-2), from the item "Stage 6's test and validation gaps that the
final review deferred", in the same section:

- **T8-M2.** `validate_curated` turns a missing document into a spurious
  `counts_mismatch`, and never refuses a duplicate fixture ID. Task 2.
- **T6-M2.** The Stage 1 anchoring test accepts any result past 500 of 686 sentences
  instead of pinning exact counts. Task 4, which makes M5's calibration a committed
  test.

**Out of scope:**

- the rest of the gaps item, and every other open item;
- `codebook freeze`'s drafting aid (P10-7);
- whether a list item under `other` becomes quotable, which Stage 7 decides from
  this plan's count ("Settle two anchoring questions before Stage 7"), so
  `anchoring.py` does not change;
- the remaining 25 train and dev bundles, which follow plan 9's Task 19, Steps 1 to
  7, after this plan.

## Global Constraints

Every task's requirements include these.

**Locators.**

- `M1`, `M5`, and `T8-M1` are plan 9's final-review findings that the item names;
  `T6-M1`, `T6-M2`, and `T8-M2` are plan 9's ledger findings that the deferred items
  name.
- `GS1`–`GS18` are the Stage 6 spec's decisions
  (`specs/completed/pilot-codebook-split-and-gold-set-protocol.md`); `P9-n` are plan
  9's, and `P10-n` this plan's (Plan decisions).
- `Rn` are requirements in `specs/evidence-linked-theme-extraction.md`; R9.9 gives
  one assignment row per claim and theme.
- Line numbers cite `main` at `0242468`.

**Versions and constants.**

| Name | Value | Where |
| --- | --- | --- |
| Base | `main` at `0242468`, PR #8's merge | the byte check's base |
| Branch | `harden-the-gold-before-bundle-4`, in the main checkout | Preconditions |
| Themes record schema | `1`, unchanged: a `Problem` value is a refusal reason, never a stored field | `THEMES_SCHEMA_VERSION` |
| Core schema; canonicalization | `2`, unchanged; `walker-1`, unchanged | `earnings_core`; `canonical/` |
| The new refusal | `Problem.UNREFERENCED`, value `unreferenced` (P10-1) | `problems.py` |
| The three signed bundles | `cik-0000051143:2024-12-31`, `cik-0000093410:2025-03-31`, `cik-0000310158:2025-06-30` | `evaluation/djia-2024q3-2026q2/pilot-v1/gold/` |
| The calibration fixture | `0000949699-08-000023_ex-99-1`: 10 sentences in 7 list items under one `other` element | `tests/fixtures/canonical/` |

**Offline, no SEC, and no models.**

- No step sends an SEC request or calls a model, and no task opens the SEC client.
- Default tests make no network call and no billable call, and need no credential.
- **`EDGAR_IDENTITY` is exported in this shell.** A `live` test's skip guard does not
  stop it, and live tests send real SEC requests. Never pass `-m live`, and never
  `-m browser`. To check collection, use `--collect-only`.

Plan 9's Blinding section follows verbatim, from
`specs/plans/completed/9-pilot-codebook-split-and-gold-set-protocol.md`, Global
Constraints. Its references, `guarded` (Task 10), P9-5, Human gates, and P9-22, are
plan 9's; plan 10's additions follow the block.

**Blinding (GS13, and the user's instruction of 2026-09-28).** These bind the
executing session, every subagent it dispatches, and every reviewer:

- **Never open, `cat`, print, `grep`, or paste pilot document text.** That text is in
  `data/runs/events/canonical/`, `data/raw/events/`, and everything under
  `data/runs/gold/`: the drafts, working copies, anchored files, views, and texts.
  Never search under `data/`, and never read a file there with a tool that shows
  its contents. Listing file names under `data/runs/gold/drafts/`, which are IDs,
  is allowed.
- **Programs print IDs, counts, reasons, paths, and hashes.** A programmatic check
  may read pilot text, as the commands and the local legs do. What it prints is
  never text: a refusal names its item by ID or field path, and an unforeseen error
  by its type alone (`guarded`, Task 10).
- **Tests use synthetic text and Stage 1's fixtures only.** A test over pilot
  documents asserts on IDs, counts, labels, and hashes, and binds any result before
  asserting on it, since pytest's report of a failed assert shows each call's
  arguments.
- **Never run a local leg with `-l`, `--showlocals`, `--pdb`, `--tb=long`, or
  `-vv`.** Each prints local values, which may hold pilot text, on a failure.
- **No release wording in this session's own words.** Commit messages, deviation
  notes, the verification record, and chat hold IDs, counts, and hashes, never a
  release's wording or a paraphrase of its content.
- **Drafting happens elsewhere.** The codebook and gold are drafted in fresh
  sessions the user starts with a committed brief, never in the executing session
  or a subagent (P9-5). The executing session never reads a draft, a working copy,
  or a view.
- **Subagents.** Every subagent dispatch, whether implementer, task reviewer, or
  the final code reviewer, carries this Blinding section verbatim. Gates run only
  in the controller session, with the user (Human gates).
- **Codex.** A Codex review takes no prompt, so it cannot carry this section, and
  it can read `data/`. It runs only as the user decides at Completion (P9-22).

**Plan 10's additions to Blinding.** These carry forward plan 9's two notes on that
section, and bind the same sessions:

- **Traceback flags.** The root `addopts` sets `--tb=short`, since pytest's default
  traceback prints a failing frame's arguments (plan 9, `c77824a`). Never pass
  `--tb=long`, `--tb=auto`, `--full-trace`, `-l`, `--showlocals`, `--pdb`, or `-vv`
  where the local legs run.
- **The exceptions are spent.** The two exceptions the user authorized at plan 9's
  Gate 3 were one-time and are used up: the executing session read the codebook
  draft once, and edited its working copy by script. This session reads no draft,
  working copy, anchored file, view, or text. Only programs read pilot text here:
  `gold anchor`, `gold validate`, the local legs, and Task 5's program, each of
  which prints IDs, counts, reasons, paths, and hashes.
- **The search rule.** Never `find`, `grep`, `rg`, or list a directory under
  `data/`, except the listing of file names under `data/runs/gold/drafts/` that the
  block above allows. The File map names every path a task needs. Plan 9's
  implementers slipped on five tasks.
- **The controller's task.** Task 5 reads the pilot's documents through programs,
  and runs only in the controller session, never in a subagent. Plan 10 drafts
  nothing and has no user gate: its decisions were taken at planning (P10-1 to
  P10-3).
- **Codex is skipped** (P10-3).

**Bytes.**

- These committed records stay byte-identical: the three gold files under
  `evaluation/djia-2024q3-2026q2/pilot-v1/gold/`,
  `tests/fixtures/gold/hard-negatives.toml`, codebook v0, the split, and the
  coverage report.
- Never change `gold.HEADER`, a field's order, or a model's fields on `Gold`,
  `HardNegativeSet`, `Codebook`, or `SplitManifest`, or anything `gold_toml`,
  `codebook_toml`, or `record_json` emit.
- Task 5 shows it: re-anchoring prints `unchanged:` for each record, never
  `Refused`, and `git diff --stat 0242468 -- evaluation codebooks tests/fixtures config`
  prints nothing.

**Do not touch.**

- `AGENTS.md`, which other files cite by line number; `.gitignore`, whose
  credentials block stays last; `.python-version`, which pins 3.14.0; and `uv.lock`.
- Everything under `evaluation/` (the briefs included), `codebooks/`, `config/`, and
  `tests/fixtures/`. The gold brief already tells a drafting session to fix its draft
  until `gold anchor --check` prints no refusal, so the new refusal needs no brief
  change.
- `walker-1`'s generated files (`canonical/decode.py`, `dom.py`, and `walker.py`),
  Stage 1's frozen harness under `expirements/parser-fidelity/`, and ADRs 0001 to
  0003.
- `packages/earnings-themes/src/earnings_themes/anchoring.py`: Stage 7 decides its
  narrative set (T6-M1).
- The retired Stage 6 spec and plan 9. The spec's validator already checks "the
  IDs" (§Anchoring and validation), which M1 completes.
- `CLAUDE.md` and `README.md`: this plan changes neither, and a `CLAUDE.md` change
  needs the user's direct consent.

**Where, and git.**

- Execute every task in the main checkout, `/Users/lowell/Projects/earnings-themes`,
  on the branch, never in a worktree: `data/` lives only there.
- `git add` only the paths a task names, never `git add -A` or `git add .`. After
  each commit, `git status --short` prints nothing.
- The user may commit on this branch while the plan runs. Run `git log --oneline -3`
  before every commit, and never rewrite a commit you did not make.
- **Never push.** `origin`, https://github.com/lowmason/earnings-themes, is public
  (Completion, Step 7).

**Tests.**

- Tests use synthetic text (`earnings_themes/synthetic.py`) and Stage 1's committed
  fixtures only.
- Fold new cases into existing tests whose names still fit: the user's pattern.
  Every task here folds, so the default suite's count stays at its baseline; a
  genuinely new test would also update the verification record's counts.
- **Baselines** at `0242468`: the default suite `1744 passed, 1 skipped, 24
  deselected`; the local legs with the wording guard `14 passed`, with no skip; the
  harness `280 passed`; Ruff `All checks passed!` and `297 files already formatted`.
- If a count differs while nothing fails, stop and report it rather than editing a
  test to match.

**Text.** Every new or replaced line of Python is ASCII, and no file carries a
backslash-u escape. The data dictionary's and the record's new text is ASCII. Each
code task's lint step ends with the escape check, which prints `escapes intact`. It
allows `§`, which the existing docstrings hold.

**Edits.** Each change to an existing file comes as the line
``In `<path>`, replace:``, a block holding the exact old text, which matches once,
the line `with:`, and a block holding the new text. The Edit tool applies it as
given.

- Apply the edits in the order given. A later task's old text is the file as the
  earlier tasks leave it.
- If an old text does not match, stop and report it: the file has drifted from the
  plan.
- The one new file, Task 5's program, is given whole after ``Create `<path>`:``.

**Commands.** These recur:

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py -q -rs
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

- The first is the **default suite**. In the main checkout it runs the local legs
  too.
- The second is the **local legs**, with the wording guard.
- The third is the **harness suite**, which no task changes.
- The fourth is **lint**.

**Commit attribution.** End each commit message with the attribution line your
session's instructions specify. The commit blocks below omit it deliberately: the
right line names the model actually executing the work.

## Plan decisions

The planning session of 2026-10-03 put three choices to the user, and P10-1 to P10-3
record the answers. P10-4 to P10-8 are the plan's own.

**P10-1 — The refusal's name (the user's answer).** `unreferenced`: one `Problem`
member for both cases, as the item asks. It is the converse of the `unknown_*`
family: the record holds the item, but nothing in it names the item. The subject
says which kind it is, as `duplicate_id`'s does: `claim c3: unreferenced` and
`quote q4: unreferenced`, and in the curated set
`<fixture_id> quote q2: unreferenced`.

**P10-2 — Two folds (the user's answer).** T8-M2 (Task 2) and T6-M2 (Task 4), from
plan 9's gaps item; not T12-M1, which is Stage 14's concern. The gaps item stays
open, and Completion notes the two as done in plan 10.

**P10-3 — Codex (the user's answer).** Skipped. No `Codex reviewed` line is
written. At the final review and at finishing-a-development-branch's Step 4b, state
the reason: "GS13: a Codex review cannot carry the Blinding section, and the main
checkout's `data/` holds pilot text, the held-out test bundles' included."

**P10-4 — Where M1's checks sit (plan-made).**

- **In `_ids`, unchanged in signature.** `tests/integration/test_stage6_records.py`
  calls it positionally over the committed gold, so that test becomes an offline
  check that no committed bundle holds an unreferenced item.
- **The uncited-quote check** comes right after the unknown-quote refusals, and
  **the uncoded-claim check** right after the assignment refusals, before the tie
  groups. Each runs in record order, and refuses an ID once (`dict.fromkeys`).
- **Hard negatives** cite quotes, but take no assignment row: they carry their own
  `theme_id`. In the curated set `_ids` gets no claims, so only the quote check
  applies there, per fixture.

**P10-5 — The drafting aid (plan-made, from the item's words).** The build takes the
kept draft's `drafting_aid`, and never refuses a working copy whose aid differs: an
edit there changes nothing, and the data dictionary's `GoldDraft` and `CuratedDraft`
rows say so.

**P10-6 — The count's definition (plan-made).**

- **The definition.** A sentence element counts when its span lies within a
  `list_item` element whose span lies within an `other` element.
- **Why it is safe.** On Stage 1's fixtures, containment, the parent chain, and
  overlap with an `other` element give the same 10 sentences, in 7 list items in one
  fixture, and the anchor refuses all 10 as `not_narrative`. So the definition
  reproduces plan 9's final-review count.
- **What the program also prints.** The anchor's verdict on each counted sentence,
  since a sentence whose text repeats is refused first as `ambiguous_occurrence`;
  and each document's sentences and `not_narrative` sentences, for any reason.
- **Where it lives.** In this plan, as plan 9's counting script did (plan 9, Task 19,
  Step 8), and it is not committed. The pilot's count is measured at execution and
  never predicted.

**P10-7 — Out of scope, deferred at Completion (plan-made).** `codebook freeze` reads
only the working copy (`apps/earnings-pipeline/src/earnings_pipeline/codebook_cli.py:108`),
and `freeze_codebook` copies its aid (`codebook.py:319`), which is T8-M1's pattern.
Codebook v0 is frozen and approved, so only a later version is affected.

**P10-8 — The roadmap (plan-made).** Stage 11's Consumes line says the gold
hardening is "due before the next" bundle. Completion replaces that phrase, by exact
replacement, rather than leaving it for the next reconcile.

## File map

| Path | Change | Task |
| --- | --- | --- |
| `packages/earnings-themes/src/earnings_themes/problems.py` | `Problem.UNREFERENCED` | 1 |
| `packages/earnings-themes/src/earnings_themes/annotation.py` | `_ids` (1); `validate_curated` (2); `build_gold` and `build_curated` (3) | 1, 2, 3 |
| `docs/data-dictionary.md` | §`Problem`'s new row (1); §`GoldDraft`'s and §`CuratedDraft`'s `drafting_aid` rows (3) | 1, 3 |
| `packages/earnings-themes/tests/test_gold.py` | folds into `test_ids_themes_and_ties_are_checked` (1, 2), `test_origins_come_from_comparing_the_working_copy_with_the_draft` (1, 3), and `test_curated_hard_negatives_over_stage_1_fixtures_validate` (3) | 1, 2, 3 |
| `packages/earnings-themes/tests/test_anchoring.py` | pins `test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors` | 4 |
| `/tmp/plan10-list-items.py` | the count; not committed | 5 |
| `docs/verification/pilot-v1-gold-set.md` | plan 10's section, appended | 5 |
| `data/runs/gold/anchored/*.toml`, local | rewritten, with the same bytes, by Task 5's re-anchor | 5 |
| `specs/deferred_items.md`, the roadmap, and this plan | Completion | Completion |

**Read, never written:**

- `tests/integration/test_stage6_records.py`, which calls `_ids`;
- `apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py` and `stage6.py`, whose
  loaders Task 5's program imports: `fixture_bundles`, `load_pinned`, `documents`,
  and `load_bundle`;
- `packages/earnings-themes/src/earnings_themes/synthetic.py`, whose `AID`,
  `gold_draft`, and `curated_draft` the tests use;
- under `data/runs/gold/drafts/`, the four kept drafts and their signed working
  copies, which only `gold anchor` reads.

## Expected outputs

At planning, on 2026-10-03, nothing in the repository changed: no branch, no
worktree, and no edit.

- **Tasks 1 to 4 were replayed.** Their edits were applied, in this plan's order, to
  copies of the edited files under `/tmp`, imported ahead of the installed package
  through `PYTHONPATH`. Every red and green run printed the Expected output its step
  gives, and Ruff, run on each file through `--stdin-filename` with the repository's
  settings, passed.
- **The committed records were probed, read-only.**
  - A program printing counts only found no claim without an assignment row, and no
    uncited quote, in the three committed bundles or in the curated set's 8
    fixtures, whose IDs are distinct.
  - A program printing booleans only found each kept draft's `drafting_aid` equal to
    its working copy's and its committed record's, for the three bundles and the
    curated set. So Task 3 changes no committed byte.
  - `gold anchor --check`, which writes nothing, printed over the four records the
    counts that Task 5's Step 1 expects, and `gold validate` printed the lines its
    Step 2 expects.
- **The count program ran on the fixtures only.** It printed Step 6's lines on Stage
  1's fixtures. It did not run over the pilot: that count is this plan's
  deliverable.

A `[COUNT: …]` mark in Task 5 is a value its program measures. Fill it in from the
program's output, and never predict it, as plan 9's `[GATE: …]` marks were filled.

## Preconditions — before Task 1

- [x] **Step 1: Probe the state**

```bash
cd /Users/lowell/Projects/earnings-themes
git branch --show-current; git log --oneline -3; git status --short
git diff --stat 0242468 main
ls evaluation/djia-2024q3-2026q2/pilot-v1/gold
```

Expected, checks:

- the branch is `main`, and the top commit is
  `0242468 Merge pull request #8 from lowmason/stage-6-pilot-codebook-split-and-gold-set`;
- `git status --short` prints `?? specs/plans/10-harden-the-gold-before-bundle-4.md`,
  this plan, written at planning and not yet committed;
- `git diff --stat 0242468 main` prints nothing;
- the `ls` prints the three gold files, `cik-0000051143_2024-12-31.toml`,
  `cik-0000093410_2025-03-31.toml`, and `cik-0000310158_2025-06-30.toml`.

Read the first row that matches:

| What the probe shows | Go to |
| --- | --- |
| The branch `harden-the-gold-before-bundle-4` exists | `git switch harden-the-gold-before-bundle-4`; read `git log --oneline 0242468..HEAD`, and resume after the last task whose commit is there (each commit message names its task) |
| A fourth gold file, or any change since `0242468` under `evaluation/` or `tests/fixtures/` | Stop and ask the user: this plan must land before bundle 4 |
| `main` holds this plan's file, committed by the user, and nothing else since `0242468` | Step 2, without its `git add` and its first `git commit` |
| As expected | Step 2 |

- [x] **Step 2: Branch, and commit this plan**

```bash
git switch -c harden-the-gold-before-bundle-4
git log --oneline -3
git add specs/plans/10-harden-the-gold-before-bundle-4.md
git commit -m "docs(specs): plan 10, harden the pilot gold before bundle 4"
git status --short
```

Expected: `Switched to a new branch 'harden-the-gold-before-bundle-4'`, then the
commit, and `git status --short` prints nothing.

- [x] **Step 3: Confirm the baselines**

```bash
uv sync --locked --all-packages --group dev
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py -q -rs
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `1744 passed, 1 skipped, 24 deselected`; `14 passed`; `280 passed`;
`All checks passed!` and `297 files already formatted`. Any other count: stop and
report it.

- [x] **Step 4: Confirm the drafts that the re-anchor reads**

```bash
ls data/runs/gold/drafts/
```

Expected: ten names, `<stem>.draft.toml` and `<stem>.working.toml` for each of
`cik-0000051143_2024-12-31`, `cik-0000093410_2025-03-31`, `cik-0000310158_2025-06-30`,
`codebook`, and `hard-negatives`. These names are IDs, which Blinding allows
listing; never open the files.

### Task 1: Refuse an unreferenced claim or quote (M1)

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/problems.py:35` (`Problem`)
- Modify: `packages/earnings-themes/src/earnings_themes/annotation.py:258-298` (`_ids`)
- Modify: `docs/data-dictionary.md:1732` (§`Problem`)
- Test: `packages/earnings-themes/tests/test_gold.py`
  (`test_origins_come_from_comparing_the_working_copy_with_the_draft`,
  `test_ids_themes_and_ties_are_checked`)

**Interfaces:**
- Consumes:
  - `_ids(quotes, claims, assignments, negatives, themes, prefix) -> list[Refusal]`
    in `annotation.py`, whose signature does not change (P10-4);
  - `Refusal(subject: str, reason: str)` and `Problem` in `problems.py`;
  - the synthetic `gold_draft(event_id=TRAIN, **changes) -> dict` and
    `curated_draft(bundles, annotator="") -> dict` in `earnings_themes/synthetic.py`;
  - the test fixtures `bundles` (`test_gold.py`), `codebook`, and `fixtures`
    (`conftest.py`).
- Produces:
  - `Problem.UNREFERENCED == "unreferenced"`;
  - `_ids` refuses `Refusal(f"{prefix}quote {quote_id}", Problem.UNREFERENCED)` for
    each quote that no claim or hard negative cites, and
    `Refusal(f"{prefix}claim {claim_id}", Problem.UNREFERENCED)` for each claim with
    no assignment row;
  - Task 2 extends `test_ids_themes_and_ties_are_checked` after this task's last line
    in it, and Task 3 edits
    `test_origins_come_from_comparing_the_working_copy_with_the_draft` as this task
    leaves it.

M1 breaks one existing test, which this task repairs first.
`test_origins_come_from_comparing_the_working_copy_with_the_draft` deletes the hard
negative `n1`, which leaves its quote `q3` cited by nothing. The smallest repair
keeps every count the test asserts: the claim `c3` the test adds cites `q3` as well
as `q4`. Its origin is `annotator_added` either way.

- [x] **Step 1: Write the failing tests, and document the new value**

In `test_origins_come_from_comparing_the_working_copy_with_the_draft`, the added
claim rests on the deleted hard negative's quote too:

In `packages/earnings-themes/tests/test_gold.py`, replace:

```python
    working["claims"].append(
        {"claim_id": "c3", "quote_ids": ["q4"], "claim": "A heading."}
    )
```

with:

```python
    working["claims"].append(
        {"claim_id": "c3", "quote_ids": ["q3", "q4"], "claim": "A heading."}
    )
```

Fold M1's cases into `test_ids_themes_and_ties_are_checked`. A bundle's gold gains
a quote no claim cites and a claim with no row. In the curated set, a hard negative
points at another quote, so the quote it cited is cited by nothing:

In `packages/earnings-themes/tests/test_gold.py`, replace:

```python
def test_ids_themes_and_ties_are_checked(bundles, codebook) -> None:
    draft = gold_draft(no_theme=True)
    draft["claims"].append({"claim_id": "c1", "quote_ids": ["q9"], "claim": "Again."})
```

with:

```python
def test_ids_themes_and_ties_are_checked(bundles, codebook, fixtures) -> None:
    """Every ID resolves, every claim takes an assignment row, and every quote is
    cited, in a bundle's gold and in each fixture of the curated set (R9.9; plan
    10)."""
    draft = gold_draft(no_theme=True)
    draft["quotes"].append({"quote_id": "q4", "text": "Quarterly results"})
    draft["claims"].append({"claim_id": "c1", "quote_ids": ["q9"], "claim": "Again."})
    draft["claims"].append({"claim_id": "c3", "quote_ids": ["q1"], "claim": "Uncoded."})
```

In `packages/earnings-themes/tests/test_gold.py`, replace:

```python
        Refusal("claim c1", "unknown_quote"),
        Refusal("assignment c1/pricing", "unknown_theme"),
        Refusal("assignment c9/unmatched", "unknown_claim"),
        Refusal("tie_group t1", "tie_group"),
    ]
```

with:

```python
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
```

Document the value. `test_every_value_is_documented[Problem]` then fails until the
enum holds it:

In `docs/data-dictionary.md`, replace:

```markdown
| `unknown_document` | The event or fixture has no document here, or is not in the split |
```

with:

```markdown
| `unknown_document` | The event or fixture has no document here, or is not in the split |
| `unreferenced` | The record holds an item nothing in it names: a claim with no assignment row, or a quote no claim or hard negative cites (R9.9) |
```

- [x] **Step 2: Run them to see them fail**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py tests/contracts/test_data_dictionary.py -q
```

Expected: `2 failed, 171 passed`.

- `test_ids_themes_and_ties_are_checked` fails at its first assert, which lacks the
  two `unreferenced` refusals.
- `test_every_value_is_documented[Problem]` fails, since the dictionary documents a
  value the enum lacks.
- The repaired origins test passes: `c3` citing `q3` is valid before M1 too.

- [x] **Step 3: Add the member, and the two checks**

In `packages/earnings-themes/src/earnings_themes/problems.py`, replace:

```python
    UNKNOWN_DOCUMENT = "unknown_document"
```

with:

```python
    UNKNOWN_DOCUMENT = "unknown_document"
    UNREFERENCED = "unreferenced"
```

In `_ids`, the uncited-quote check comes right after the unknown-quote refusals:

In `packages/earnings-themes/src/earnings_themes/annotation.py`, replace:

```python
                refusals.append(Refusal(subject, Problem.UNKNOWN_QUOTE))
    rows = [(a.claim_id, a.theme_id) for a in assignments]
```

with:

```python
                refusals.append(Refusal(subject, Problem.UNKNOWN_QUOTE))
    cited = {q for claim in (*claims, *negatives) for q in claim.quote_ids}
    for quote_id in dict.fromkeys(quote_ids):
        if quote_id not in cited:
            refusals.append(Refusal(f"{prefix}quote {quote_id}", Problem.UNREFERENCED))
    rows = [(a.claim_id, a.theme_id) for a in assignments]
```

The uncoded-claim check comes right after the assignment refusals:

In `packages/earnings-themes/src/earnings_themes/annotation.py`, replace:

```python
            refusals.append(Refusal(subject, Problem.UNKNOWN_THEME))
    groups: dict[str, list[GoldAssignment]] = {}
```

with:

```python
            refusals.append(Refusal(subject, Problem.UNKNOWN_THEME))
    coded = {a.claim_id for a in assignments}
    for claim_id in dict.fromkeys(c.claim_id for c in claims):
        if claim_id not in coded:
            refusals.append(Refusal(f"{prefix}claim {claim_id}", Problem.UNREFERENCED))
    groups: dict[str, list[GoldAssignment]] = {}
```

- [x] **Step 4: Run them to see them pass**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests tests/contracts/test_data_dictionary.py tests/integration/test_stage6_records.py apps/earnings-pipeline/tests/test_stage6_cli.py -q
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
```

Expected: `275 passed`, with the offline check of the committed bundles
(`test_stage6_records.py`) and the CLI tests, which build gold and curated sets.
Then `1744 passed, 1 skipped, 24 deselected`: the default suite now validates the
committed records under M1, offline and against the local store.

- [x] **Step 5: Lint, and the escape check**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' packages/earnings-themes/src/earnings_themes/problems.py packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/tests/test_gold.py
```

Expected: `All checks passed!`, `297 files already formatted`, and `escapes intact`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-themes/src/earnings_themes/problems.py packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/tests/test_gold.py docs/data-dictionary.md
git commit -m "feat(themes): refuse an unreferenced claim or quote (plan 10, M1)"
git status --short
```

Expected: `git status --short` prints nothing.

### Task 2: The curated set's validator (T8-M2)

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/annotation.py:455-499`
  (`validate_curated`)
- Test: `packages/earnings-themes/tests/test_gold.py`
  (`test_ids_themes_and_ties_are_checked`)

**Interfaces:**
- Consumes:
  - Task 1's form of `test_ids_themes_and_ties_are_checked`, whose last line is
    `    assert refusals == [Refusal(f"{first['fixture_id']} quote q2", "unreferenced")]`;
  - `build_curated(drafted, working, *, bundles, pin, codebook) -> HardNegativeSet | list[Refusal]`
    and
    `validate_curated(record, *, bundles, pin, codebook, require_signature=True) -> list[Refusal]`;
  - `SIGNED`, which `test_gold.py` defines.
- Produces:
  - `validate_curated` refuses a repeated fixture ID as
    `Refusal(<fixture_id>, Problem.DUPLICATE_ID)`, after the `negative_kinds` check
    and before any fixture's own refusals;
  - it counts every document's items before any refusal of that document, so a
    missing or moved fixture is refused once, never also as `counts_mismatch`;
  - the subject is the bare fixture ID, as `validate_curated`'s `unknown_document`
    subject is.

Today a missing fixture yields `<fixture_id>: unknown_document` and
`counts: counts_mismatch`, and a moved one `<fixture_id> doc_id: wrong_document` and
`counts: counts_mismatch`. A working copy that repeats a fixture builds a
`HardNegativeSet` with no refusal. The planning session confirmed all three.

- [x] **Step 1: Write the failing test**

Extend `test_ids_themes_and_ties_are_checked`, after Task 1's curated assert:

In `packages/earnings-themes/tests/test_gold.py`, replace:

```python
    assert refusals == [Refusal(f"{first['fixture_id']} quote q2", "unreferenced")]
```

with:

```python
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
```

- [x] **Step 2: Run it to see it fail**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py -q
```

Expected: `1 failed, 16 passed`. `test_ids_themes_and_ties_are_checked` fails at
`assert refusals == [Refusal(first_id, "duplicate_id")]`, since the build returns a
`HardNegativeSet`.

- [x] **Step 3: Refuse a repeated fixture, and count every fixture's items**

In `packages/earnings-themes/src/earnings_themes/annotation.py`, replace:

```python
        refusals.append(Refusal("hard_negatives", Problem.NEGATIVE_KINDS))
    items: list[BaseModel] = []
    for document in record.documents:
        prefix = f"{document.fixture_id} "
        bundle = bundles.get(document.fixture_id)
```

with:

```python
        refusals.append(Refusal("hard_negatives", Problem.NEGATIVE_KINDS))
    fixture_ids = [d.fixture_id for d in record.documents]
    for repeated in sorted({i for i in fixture_ids if fixture_ids.count(i) > 1}):
        refusals.append(Refusal(repeated, Problem.DUPLICATE_ID))
    items: list[BaseModel] = []
    for document in record.documents:
        prefix = f"{document.fixture_id} "
        items += [*document.quotes, *document.hard_negatives]
        bundle = bundles.get(document.fixture_id)
```

The loop's last line moved to its top, so a refused fixture's items are still
counted:

In `packages/earnings-themes/src/earnings_themes/annotation.py`, replace:

```python
        refusals += _pointers(document.quotes, bundle, prefix)
        items += [*document.quotes, *document.hard_negatives]
```

with:

```python
        refusals += _pointers(document.quotes, bundle, prefix)
```

- [x] **Step 4: Run them to see them pass**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests tests/contracts/test_data_dictionary.py tests/integration/test_stage6_records.py apps/earnings-pipeline/tests/test_stage6_cli.py -q
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
```

Expected: `275 passed`; then `1744 passed, 1 skipped, 24 deselected`. The default
suite includes `test_the_curated_hard_negatives_validate_offline`, which validates
the committed curated set, with its 8 distinct fixtures, under the new check.

- [x] **Step 5: Lint, and the escape check**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/tests/test_gold.py
```

Expected: `All checks passed!`, `297 files already formatted`, and `escapes intact`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/tests/test_gold.py
git commit -m "fix(themes): refuse a repeated fixture, and count a refused fixture's items (plan 10, T8-M2)"
git status --short
```

Expected: `git status --short` prints nothing.

### Task 3: The drafting aid comes from the kept draft (T8-M1)

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/annotation.py`
  (`build_gold`, `:241` at `0242468`; `build_curated`, `:444`)
- Modify: `docs/data-dictionary.md:2159,2182` (the `drafting_aid` rows of §`GoldDraft`
  and §`CuratedDraft`)
- Test: `packages/earnings-themes/tests/test_gold.py` (its imports;
  `test_origins_come_from_comparing_the_working_copy_with_the_draft`;
  `test_curated_hard_negatives_over_stage_1_fixtures_validate`)

**Interfaces:**
- Consumes:
  - Task 1's form of the origins test, where `c3` cites `["q3", "q4"]`;
  - `AID` in `earnings_themes/synthetic.py`:
    `{"model_id": "claude-opus-5-5", "drafted_on": date(2026, 10, 1)}`;
  - `build_gold(drafted, working, *, bundle, pin, split, codebook)` and
    `build_curated(drafted, working, *, bundles, pin, codebook)`, whose signatures do
    not change.
- Produces: `Gold.drafting_aid` and `HardNegativeSet.drafting_aid` hold the kept
  draft's aid, whatever the working copy's says (P10-5). Task 5 re-anchors the
  committed records on this.

- [x] **Step 1: Write the failing tests, and document the rule**

> Deviation: the implementer applied this step's two `docs/data-dictionary.md` edits before its three test-body edits; the files are independent and every edit preceded Step 2's red run, so the commit holds this step's edits exactly (`6422b71`).

The imports:

In `packages/earnings-themes/tests/test_gold.py`, replace:

```python
import pytest
from earnings_themes.annotation import (
```

with:

```python
from datetime import date

import pytest
from earnings_themes.annotation import (
```

In `packages/earnings-themes/tests/test_gold.py`, replace:

```python
from earnings_themes.synthetic import (
    DEV,
```

with:

```python
from earnings_themes.synthetic import (
    AID,
    DEV,
```

The origins test gives the working copy another drafting date, and asserts the
draft's:

In `packages/earnings-themes/tests/test_gold.py`, replace:

```python
    bundles, codebook
) -> None:
    drafted = gold_draft()
    working = gold_draft(annotator=SIGNED)
```

with:

```python
    bundles, codebook
) -> None:
    """Each item's origin, and the drafting aid, come from the kept draft: the
    working copy's drafting aid is never read (GS5; plan 10)."""
    drafted = gold_draft()
    working = gold_draft(annotator=SIGNED)
    working["drafting_aid"] = {**AID, "drafted_on": date(2026, 10, 3)}
```

In `packages/earnings-themes/tests/test_gold.py`, replace:

```python
    assert gold.quotes[3].origin is Origin.ANNOTATOR_ADDED
    assert check(gold, bundles, codebook) == []
```

with:

```python
    assert gold.quotes[3].origin is Origin.ANNOTATOR_ADDED
    assert gold.drafting_aid.model_dump() == AID
    assert check(gold, bundles, codebook) == []
```

The curated set's test does the same:

In `packages/earnings-themes/tests/test_gold.py`, replace:

```python
    fixtures, codebook, tmp_path
) -> None:
    draft = curated(fixtures)
    record = build_curated(draft, draft, bundles=fixtures, pin=PIN, codebook=codebook)
    assert isinstance(record, HardNegativeSet)
    assert record.pin == PIN
```

with:

```python
    fixtures, codebook, tmp_path
) -> None:
    """The curated set builds, validates, and round-trips, and its drafting aid is
    the kept draft's: the working copy's is never read (GS5; plan 10)."""
    draft = curated(fixtures)
    aid = draft.drafting_aid.model_copy(update={"drafted_on": date(2026, 10, 3)})
    working = draft.model_copy(update={"drafting_aid": aid})
    record = build_curated(draft, working, bundles=fixtures, pin=PIN, codebook=codebook)
    assert isinstance(record, HardNegativeSet)
    assert record.pin == PIN
    assert record.drafting_aid == draft.drafting_aid
```

The data dictionary's two draft rows:

In `docs/data-dictionary.md`, replace:

```markdown
| `annotator` | string | Blank in the draft; the user signs the working copy |
| `drafting_aid` | `DraftingAid` | The drafting session |
| `no_theme` | bool | As `Gold` |
```

with:

```markdown
| `annotator` | string | Blank in the draft; the user signs the working copy |
| `drafting_aid` | `DraftingAid` | The drafting session; the record takes the kept draft's, never the working copy's (GS5) |
| `no_theme` | bool | As `Gold` |
```

In `docs/data-dictionary.md`, replace:

```markdown
| `annotator` | string | Blank in the draft; the user signs the working copy |
| `drafting_aid` | `DraftingAid` | The drafting session |
| `documents` | tuple of `FixtureDraft` | At least one |
```

with:

```markdown
| `annotator` | string | Blank in the draft; the user signs the working copy |
| `drafting_aid` | `DraftingAid` | The drafting session; the record takes the kept draft's, never the working copy's (GS5) |
| `documents` | tuple of `FixtureDraft` | At least one |
```

- [x] **Step 2: Run them to see them fail**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py tests/contracts/test_data_dictionary.py -q
```

Expected: `2 failed, 171 passed`:
`test_origins_come_from_comparing_the_working_copy_with_the_draft`, at
`assert gold.drafting_aid.model_dump() == AID`, and
`test_curated_hard_negatives_over_stage_1_fixtures_validate`, at
`assert record.drafting_aid == draft.drafting_aid`.

- [x] **Step 3: Take the aid from the draft**

In `packages/earnings-themes/src/earnings_themes/annotation.py`, replace:

```python
        drafting_aid=working.drafting_aid,
        counts=origins.tally(),
        no_theme=working.no_theme,
```

with:

```python
        drafting_aid=drafted.drafting_aid,
        counts=origins.tally(),
        no_theme=working.no_theme,
```

In `packages/earnings-themes/src/earnings_themes/annotation.py`, replace:

```python
        drafting_aid=working.drafting_aid,
        counts=origins.tally(),
        codebook=_codebook_ref(codebook),
```

with:

```python
        drafting_aid=drafted.drafting_aid,
        counts=origins.tally(),
        codebook=_codebook_ref(codebook),
```

- [x] **Step 4: Run them to see them pass**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests tests/contracts/test_data_dictionary.py tests/integration/test_stage6_records.py apps/earnings-pipeline/tests/test_stage6_cli.py -q
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
```

Expected: `275 passed`; then `1744 passed, 1 skipped, 24 deselected`.

- [x] **Step 5: Lint, and the escape check**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/tests/test_gold.py
```

Expected: `All checks passed!`, `297 files already formatted`, and `escapes intact`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/tests/test_gold.py docs/data-dictionary.md
git commit -m "fix(themes): take the drafting aid from the kept draft (plan 10, T8-M1)"
git status --short
```

Expected: `git status --short` prints nothing.

### Task 4: Pin the Stage 1 anchoring counts (T6-M2, M5's calibration)

**Files:**
- Test: `packages/earnings-themes/tests/test_anchoring.py` (its imports;
  `test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors`)

**Interfaces:**
- Consumes: `anchor`, `check_pointer`, and `bundle_problems` in `anchoring.py`; the
  `fixtures` fixture in `conftest.py`, Stage 1's eight canonical fixtures by ID.
- Produces: the pinned counts. 650 sentences anchor, 26 are `ambiguous_occurrence`,
  and 10 are `not_narrative`, all in list items under an `other` element in
  `0000949699-08-000023_ex-99-1`. Task 5's program calibrates against them, with this
  test's definition: a list item whose span lies within an `other` element's span.

The test pins today's behavior, so it passes as soon as it is written. Step 3 shows
that it can fail.

- [x] **Step 1: Pin the counts**

In `packages/earnings-themes/tests/test_anchoring.py`, replace:

```python
import pytest
from earnings_core import RejectionReason, TextSpan, make_locator
```

with:

```python
from collections import Counter

import pytest
from earnings_core import RejectionReason, TextSpan, make_locator
```

In `packages/earnings-themes/tests/test_anchoring.py`, replace:

```python
    fixtures,
) -> None:
    anchored = 0
    for bundle in fixtures.values():
        assert bundle_problems(bundle) == []
        text = bundle.document.canonical_text
        for element in bundle.elements:
            if element.type.value != "sentence":
                continue
            exact = text[element.span.start : element.span.end]
            pointer = anchor(bundle, exact)
            if isinstance(pointer, str):
                assert pointer in {"ambiguous_occurrence", "not_narrative"}
                continue
            assert pointer.element_id == element.element_id
            assert check_pointer(bundle, pointer) == []
            anchored += 1
    assert anchored > 500
```

with:

```python
    fixtures,
) -> None:
    """Each of the 686 sentences of Stage 1's fixtures anchors to itself, or is
    refused: 26 repeat, so need context, and 10 sit in a list item under an
    ``other`` element, all in one fixture, so are not narrative (T6-M1). Plan 10
    pins these counts (T6-M2), and calibrates its count over the pilot on the 10."""
    verdicts: Counter[str] = Counter()
    under_other: Counter[str] = Counter()
    for name, bundle in fixtures.items():
        assert bundle_problems(bundle) == []
        text = bundle.document.canonical_text
        others = [e for e in bundle.elements if e.type.value == "other"]
        items = [
            e
            for e in bundle.elements
            if e.type.value == "list_item"
            and any(other.span.contains(e.span) for other in others)
        ]
        for element in bundle.elements:
            if element.type.value != "sentence":
                continue
            exact = text[element.span.start : element.span.end]
            pointer = anchor(bundle, exact)
            if isinstance(pointer, str):
                verdicts[pointer] += 1
                if any(item.span.contains(element.span) for item in items):
                    under_other[f"{name}: {pointer}"] += 1
                continue
            assert pointer.element_id == element.element_id
            assert check_pointer(bundle, pointer) == []
            verdicts["anchored"] += 1
    assert verdicts == {
        "anchored": 650,
        "ambiguous_occurrence": 26,
        "not_narrative": 10,
    }
    assert under_other == {"0000949699-08-000023_ex-99-1: not_narrative": 10}
```

- [x] **Step 2: Run it**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_anchoring.py -q
```

Expected: `18 passed`.

- [x] **Step 3: Show that the pin can fail, then restore it**

```bash
sed -i '' 's/"anchored": 650,/"anchored": 651,/' packages/earnings-themes/tests/test_anchoring.py
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_anchoring.py -q
sed -i '' 's/"anchored": 651,/"anchored": 650,/' packages/earnings-themes/tests/test_anchoring.py
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_anchoring.py -q
grep -c '"anchored": 650,' packages/earnings-themes/tests/test_anchoring.py
```

Expected: `1 failed, 17 passed`; then `18 passed`; then `1`.

- [x] **Step 4: The default suite, lint, and the escape check**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' packages/earnings-themes/tests/test_anchoring.py
```

Expected: `1744 passed, 1 skipped, 24 deselected`; `All checks passed!`,
`297 files already formatted`, and `escapes intact`.

- [x] **Step 5: Commit**

```bash
git log --oneline -3
git add packages/earnings-themes/tests/test_anchoring.py
git commit -m "test(themes): pin the Stage 1 anchoring counts (plan 10, T6-M2)"
git status --short
```

Expected: `git status --short` prints nothing.

### Task 5: The bytes, the count, and the record (controller)

This task runs in the controller session only, never in a subagent (Blinding). It
reads the pilot's documents through `gold anchor`, `gold validate`, the local legs,
and its program, each of which prints IDs, counts, reasons, paths, and hashes.

**Files:**
- Create: `/tmp/plan10-list-items.py`, never committed
- Local, rewritten with the same bytes: `data/runs/gold/anchored/hard-negatives.toml`
  and the three bundles' anchored files
- Modify: `docs/verification/pilot-v1-gold-set.md`, by appending plan 10's section

**Interfaces:**
- Consumes:
  - Tasks 1 to 4;
  - `earnings-pipeline gold anchor` and `gold validate`;
  - `fixture_bundles(layout)` in `gold_cli.py`;
  - `Layout`, `load_pinned`, `documents`, and `load_bundle` in `stage6.py`;
  - `anchor` in `anchoring.py`.
- Produces: the bytes' proof, M5's count, and the verification record's plan 10
  section, which is the item's last clause.

- [x] **Step 1: Re-anchor the committed records (T8-M1's proof)**

```bash
uv run --locked --all-packages earnings-pipeline gold anchor cik-0000051143:2024-12-31 cik-0000093410:2025-03-31 cik-0000310158:2025-06-30 --hard-negatives; echo "exit $?"
```

Expected, exactly; the curated set comes first, as `gold anchor` takes it first:

```text
hard-negatives: 8 fixtures, 29 hard negatives (issuer 4, period 13, section 12)
origins: accepted 58, edited 0, rejected 0, added 0
anchored  data/runs/gold/anchored/hard-negatives.toml
unchanged: tests/fixtures/gold/hard-negatives.toml
cik-0000051143:2024-12-31 (train): 62 quotes, 46 claims, 57 assignments, 8 hard negatives; no_theme false
origins: accepted 173, edited 0, rejected 0, added 0
anchored  data/runs/gold/anchored/cik-0000051143_2024-12-31.toml
unchanged: evaluation/djia-2024q3-2026q2/pilot-v1/gold/cik-0000051143_2024-12-31.toml
cik-0000093410:2025-03-31 (train): 56 quotes, 40 claims, 62 assignments, 13 hard negatives; no_theme false
origins: accepted 171, edited 0, rejected 0, added 0
anchored  data/runs/gold/anchored/cik-0000093410_2025-03-31.toml
unchanged: evaluation/djia-2024q3-2026q2/pilot-v1/gold/cik-0000093410_2025-03-31.toml
cik-0000310158:2025-06-30 (train): 103 quotes, 71 claims, 97 assignments, 11 hard negatives; no_theme false
origins: accepted 282, edited 0, rejected 0, added 0
anchored  data/runs/gold/anchored/cik-0000310158_2025-06-30.toml
unchanged: evaluation/djia-2024q3-2026q2/pilot-v1/gold/cik-0000310158_2025-06-30.toml
exit 0
```

A signed record whose rebuilt bytes differ from the committed file is refused before
anything is written (`gold_cli.py`, `_write`). If any line starts with `Refused` or
`refused:`:

- stop, and report the record, its item, and the reason to the user;
- never edit a committed record, a draft, or a working copy to make it pass;
- never run the anchor with `--check` in place of this step: `--check` returns
  before it compares the rebuilt bytes with the committed file.

- [x] **Step 2: Validate them**

```bash
uv run --locked --all-packages earnings-pipeline gold validate; echo "exit $?"
uv run --locked --all-packages earnings-pipeline gold validate --hard-negatives; echo "exit $?"
```

Expected, exactly:

```text
valid: cik-0000051143:2024-12-31 (train), 62 quotes, 46 claims, signed
valid: cik-0000093410:2025-03-31 (train), 56 quotes, 40 claims, signed
valid: cik-0000310158:2025-06-30 (train), 103 quotes, 71 claims, signed
exit 0
valid: hard-negatives, 8 fixtures, 29 hard negatives, signed
exit 0
```

- [x] **Step 3: The byte check**

```bash
git diff --stat 0242468 -- evaluation codebooks tests/fixtures config
git status --short
```

Expected: nothing, from either command.

- [x] **Step 4: The local legs**

```bash
uv run --locked --all-packages pytest tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py -q -rs
```

Expected: `14 passed`.

- [x] **Step 5: Write the count program**

Create `/tmp/plan10-list-items.py`:

```python
"""Plan 10, Task 5 (M5): count the narrative sentences that sit in a walker-1 list
item under an ``other`` element, which the anchor refuses (T6-M1). It reads each
canonical document through the application's loaders, and prints IDs and counts,
never text (GS13).

usage: uv run --locked --all-packages python /tmp/plan10-list-items.py fixtures|pilot
"""

import sys
from collections import Counter
from pathlib import Path

import typer
from earnings_core import ElementType
from earnings_pipeline.gold_cli import fixture_bundles
from earnings_pipeline.stage6 import (
    PILOT_V1,
    PILOT_V1_HASH,
    UNIVERSE_V1,
    Layout,
    documents,
    load_bundle,
    load_pinned,
)
from earnings_themes.anchoring import Bundle, SpanPointer, anchor

LAYOUT = Layout(Path.cwd(), UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH)


def corpus_bundles(corpus: str) -> dict[str, Bundle]:
    """Stage 1's eight fixtures, or the pilot's parsed documents by event ID."""
    if corpus == "fixtures":
        return fixture_bundles(LAYOUT)
    pinned = load_pinned(LAYOUT)
    doc_ids = documents(LAYOUT, pinned)
    return {e: load_bundle(LAYOUT, doc_ids, e) for e in sorted(doc_ids)}


def count(bundle: Bundle) -> tuple[int, Counter[str], int, int]:
    """The list items inside an ``other`` element; the anchor's verdict on each
    sentence inside one of them; the document's sentences; and how many of those
    the anchor refuses as not narrative, for any reason."""
    others = [e for e in bundle.elements if e.type is ElementType.OTHER]
    items = [
        e
        for e in bundle.elements
        if e.type is ElementType.LIST_ITEM
        and any(other.span.contains(e.span) for other in others)
    ]
    text = bundle.document.canonical_text
    under: Counter[str] = Counter()
    sentences = refused = 0
    for element in bundle.elements:
        if element.type is not ElementType.SENTENCE:
            continue
        pointer = anchor(bundle, text[element.span.start : element.span.end])
        verdict = "anchored" if isinstance(pointer, SpanPointer) else pointer
        sentences += 1
        refused += verdict == "not_narrative"
        if any(item.span.contains(element.span) for item in items):
            under[verdict] += 1
    return len(items), under, sentences, refused


def main(corpus: str) -> None:
    found = corpus_bundles(corpus)
    verdicts: Counter[str] = Counter()
    items = sentences = refused = holding = 0
    for name, bundle in found.items():
        its_items, under, its_sentences, its_refused = count(bundle)
        items += its_items
        sentences += its_sentences
        refused += its_refused
        verdicts.update(under)
        if under:
            holding += 1
            shown = ", ".join(f"{v} {n}" for v, n in sorted(under.items()))
            print(
                f"  {name}: {its_items} list items, {under.total()} sentences ({shown})"
            )
    shown = ", ".join(f"{v} {n}" for v, n in sorted(verdicts.items())) or "none"
    print(
        f"{corpus}: {verdicts.total()} sentences in {items} list items under an"
        f" `other` element, in {holding} of {len(found)} documents; the anchor:"
        f" {shown}; of {sentences} sentences in all, not_narrative {refused}"
    )


if __name__ == "__main__":
    corpus = sys.argv[1] if len(sys.argv) > 1 else ""
    if corpus not in {"fixtures", "pilot"}:
        sys.exit(__doc__.strip().splitlines()[-1])
    try:
        main(corpus)
    except typer.Exit as error:
        sys.exit(error.exit_code)
    except Exception as error:  # noqa: BLE001 - withheld by design (GS13)
        sys.exit(
            f"stopped: an unforeseen {type(error).__name__}; its message is"
            " withheld, since it may quote a document (GS13)"
        )
```

- [x] **Step 6: Calibrate it on Stage 1's fixtures**

```bash
uv run --locked --all-packages python /tmp/plan10-list-items.py fixtures; echo "exit $?"
```

Expected, exactly:

```text
  0000949699-08-000023_ex-99-1: 7 list items, 10 sentences (not_narrative 10)
fixtures: 10 sentences in 7 list items under an `other` element, in 1 of 8 documents; the anchor: not_narrative 10; of 686 sentences in all, not_narrative 10
exit 0
```

This is plan 9's final-review count, and Task 4's pin. Anything else: stop and
report it. The program does not then measure what the review measured, and its count
over the pilot would mean nothing.

- [x] **Step 7: Count the pilot**

```bash
uv run --locked --all-packages python /tmp/plan10-list-items.py pilot; echo "exit $?"
```

Expected, in form; the numbers are the measurement:

- one indented line for each pilot event that holds such a sentence:
  `  <event_id>: <i> list items, <s> sentences (<verdict> <n>, ...)`;
- then
  ``pilot: <S> sentences in <L> list items under an `other` element, in <D> of 40 documents; the anchor: <verdicts, or none>; of <T> sentences in all, not_narrative <Z>``;
- then `exit 0`.

Keep the output for Step 9. A `Refused:` or `stopped:` line, or another exit, stops
the task: report it as printed. Such a line names an item, or an exception's type,
never text.

- [x] **Step 8: The suites**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
git diff --quiet 0242468 -- uv.lock && echo "uv.lock unchanged"
```

Expected: `1744 passed, 1 skipped, 24 deselected`; `280 passed`; `All checks passed!`
and `297 files already formatted`; `uv.lock unchanged`.

- [x] **Step 9: Append plan 10's section to the record**

Append to `docs/verification/pilot-v1-gold-set.md`, filling each `[COUNT: …]` from
Step 7's output:

```markdown

## Plan 10: the gold hardened before bundle 4

Plan 10 (`specs/plans/10-harden-the-gold-before-bundle-4.md`) closed three findings
of plan 9's final review before any further bundle was anchored: M1, T8-M1, and M5.
It also closed two of plan 9's deferred test and validation gaps, T8-M2 and T6-M2
(`specs/deferred_items.md`).

- **Every claim coded, and every quote cited (M1).** The validator refuses a claim
  with no assignment row, and a quote that no claim or hard negative cites, as
  `unreferenced` (R9.9). Neither the three committed bundles nor the curated hard
  negatives hold one, and `tests/integration/test_stage6_records.py` now checks the
  committed bundles for one offline.
- **The drafting aid (T8-M1).** `build_gold` and `build_curated` take
  `drafting_aid` from the kept draft, never the working copy, so an edit there
  cannot change the recorded model or date (GS5).
- **The curated set's validator (T8-M2).** A missing or moved fixture is refused
  once, never also as `counts_mismatch`, and a repeated fixture ID is refused as
  `duplicate_id`.
- **The bytes.** `gold anchor` rebuilt each committed record from its kept draft
  and signed working copy, and printed `unchanged:` for the three bundles and
  `tests/fixtures/gold/hard-negatives.toml`, and no refusal. `gold validate`
  printed `valid:` for each, and `git diff --stat 0242468 -- evaluation codebooks
  tests/fixtures config` printed nothing.
- **The suites.** The default suite printed `1744 passed, 1 skipped, 24
  deselected`; the local legs and the wording guard, `14 passed`; and the harness
  suite, `280 passed`. Ruff passed, and `uv.lock` is unchanged.

### Sentences in a list item under an `other` element (M5)

walker-1 nests some list items in an element of type `other`, and the anchor
refuses a sentence in one as not narrative, since the `other` element overlaps it
(T6-M1). The program in plan 10's Task 5 counted these sentences through the
application's loaders, with the anchor's verdict on each, printing IDs and counts
only:

| Documents | Sentences | List items | Documents holding one | The anchor's verdicts | All sentences | All `not_narrative` |
| --- | --- | --- | --- | --- | --- | --- |
| Stage 1's 8 fixtures | 10 | 7 | 1 of 8 | `not_narrative` 10 | 686 | 10 |
| Pilot v1's 40 releases | [COUNT: S] | [COUNT: L] | [COUNT: D] of 40 | [COUNT: each verdict and its count, or none] | [COUNT: T] | [COUNT: Z] |

- **The calibration.** The fixtures' row is plan 9's final-review count, which
  `test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors` now pins
  (T6-M2), beside 650 sentences anchored and 26 whose text repeats.
- **The pilot's releases.** [COUNT: each event the program listed, in its order,
  as `<event_id>` (<s> sentences); or "No pilot release holds one."]
- **What follows.** No gold quote can rest on such a sentence until Stage 7 decides
  whether a list item under an `other` element becomes quotable
  (`specs/deferred_items.md`, T6-M1).
```

Then:

```bash
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs
grep -c "COUNT" docs/verification/pilot-v1-gold-set.md
```

Expected: `5 passed`, since the wording guard reads the record; then `0`, since every
mark is filled.

- [x] **Step 10: Commit the record**

```bash
git log --oneline -3
git add docs/verification/pilot-v1-gold-set.md
git commit -m "docs(verification): record plan 10's hardening and the list-item count"
git status --short
```

Expected: `git status --short` prints nothing.

## Completion

- [x] **Step 1: The final review**

> Deviation: the final review (Opus, over `0242468..e57f6ae`) found the branch ready to merge, with no Critical or Important finding. At the gate on 2026-10-03 the user chose one polish commit outside this plan's edits (`2982781`): a guard in each drafting-aid test that the working copy's aid differs from the draft's (T3-m1); the `drafting_aid` rows of §`Gold` and §`HardNegativeSet` naming the kept draft (FR-m1); and three docstrings' wording (FR-m2, T1-m3). The default suite stayed at `1744 passed, 1 skipped, 24 deselected`. T2-m1, widened to a kept draft's repeated quote, claim, or fixture, was deferred (Step 3), and every other Minor was dropped.

Run the final whole-branch review with the `code-reviewer` agent, on Opus, over
`0242468..HEAD`. Its dispatch carries:

- this plan, and the deferred item it implements, as the requirements;
- Global Constraints' Blinding section verbatim, with plan 10's additions.

Codex is skipped (P10-3): state the reason at the review. Resolve the review's
findings with the user before Step 2.

- [x] **Step 2: Mark up this plan** (writing-plans' Plan Completion Protocol)

- Run the resolve-before-defer gate.
- Tick the steps, add `> Deviation:` and `> Skipped:` notes, and add the status
  header. Notes hold IDs, counts, and hashes only (Blinding).

- [x] **Step 3: The deferred items**

Tick the item:

In `specs/deferred_items.md`, replace:

```markdown
- [ ] Harden the gold before the next Task 19 bundle is anchored (plan 9's final
```

with:

```markdown
- [x] Harden the gold before the next Task 19 bundle is anchored (plan 9's final
```

In `specs/deferred_items.md`, replace:

```markdown
      docs/verification/pilot-v1-gold-set.md, before any further bundle is
      anchored.
```

with:

```markdown
      docs/verification/pilot-v1-gold-set.md, before any further bundle is
      anchored. → done in plan 10 (specs/plans/completed/10-harden-the-gold-before-bundle-4.md)
```

Note the gaps item's two folds. It stays open:

In `specs/deferred_items.md`, replace:

```markdown
(codebook_cli.py:150-158). Size: plan. Done when: a plan lands each with its
      test, or records why one is dropped.
```

with:

```markdown
(codebook_cli.py:150-158). Size: plan. Done when: a plan lands each with its
      test, or records why one is dropped. T8-M2 and T6-M2 → done in plan 10
      (specs/plans/completed/10-harden-the-gold-before-bundle-4.md).
```

Then append `## 10-harden-the-gold-before-bundle-4 — YYYY-MM-DD`, with the
completion date, to the end of `specs/deferred_items.md`, after a blank line. It
holds at least P10-7's item, below, and any other item the gate deferred, each in the
schema of `references/deferred-backlog.md`:

```markdown
- [ ] Take `codebook freeze`'s drafting aid from the kept draft (plan 10, P10-7;
      T8-M1's pattern). apps/earnings-pipeline/src/earnings_pipeline/codebook_cli.py
      reads only data/runs/gold/drafts/codebook.working.toml, and
      packages/earnings-themes/src/earnings_themes/codebook.py:319 copies that
      copy's `drafting_aid`, so an edit there would change the recorded model or
      date (GS5). Codebook v0 is frozen and approved, so only a later version is
      affected. Size: quick-fix. Done when: `codebook freeze` takes the aid from
      codebook.draft.toml, with a test, before codebook v1 is frozen.
```

Commit Steps 2 and 3 together:

```bash
git log --oneline -3
git add specs/plans/10-harden-the-gold-before-bundle-4.md specs/deferred_items.md
git commit -m "docs(specs): mark up plan 10, and tick the gold hardening"
git status --short
```

- [ ] **Step 4: Backlog triage**

```bash
uv run --no-project --python 3.13 python ~/.claude/skills/writing-plans/scripts/deferred_stats.py
```

Report its summary line, and present the triage rubric if its thresholds trip.

- [ ] **Step 5: Retire this plan**

Plan 10 has no spec to retire.

```bash
git mv specs/plans/10-harden-the-gold-before-bundle-4.md specs/plans/completed/
sed -i '' 's#specs/plans/10-harden-the-gold-before-bundle-4.md#specs/plans/completed/10-harden-the-gold-before-bundle-4.md#g' docs/verification/pilot-v1-gold-set.md
git grep -n "specs/plans/10-harden" -- . ':!specs/plans/completed'
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs
git log --oneline -3
git add specs/plans/completed/10-harden-the-gold-before-bundle-4.md docs/verification/pilot-v1-gold-set.md
git commit -m "chore(specs): retire plan 10"
git status --short
```

Expected: no `git grep` output; `5 passed`; and `git status --short` prints nothing.

- [ ] **Step 6: The roadmap** (P10-8)

In Stage 11's Consumes line:

In `specs/evidence-linked-theme-extraction-roadmap.md`, replace:

```markdown
of which three are signed and the other 25, with the gold hardening due before the next of them, are deferred items (`specs/deferred_items.md`, `9-pilot-codebook-split-and-gold-set-protocol`);
```

with:

```markdown
of which three are signed and the other 25 are deferred items (`specs/deferred_items.md`, `9-pilot-codebook-split-and-gold-set-protocol`), each anchored under the gold that plan 10 hardened (`specs/plans/completed/10-harden-the-gold-before-bundle-4.md`);
```

```bash
git log --oneline -3
git add specs/evidence-linked-theme-extraction-roadmap.md
git commit -m "docs(roadmap): Stage 11's gold is hardened (plan 10)"
git status --short
```

- [ ] **Step 7: Integrate**

Use finishing-a-development-branch. Its Step 4b states P10-3's reason.

- **Never push.** The choice among its options is the user's, in that session. A
  push happens only when the user explicitly says to push there.
- **Before any push the user asks for**, check every commit it publishes, and the
  tree at its tip, by count, so no path is printed:

```bash
git fetch origin main
git rev-list --count origin/main..HEAD -- data/
git ls-tree -r --name-only HEAD -- data/ | awk 'END { print NR }'
```

Expected: `0` and `0`. Otherwise stop and report it.

- [ ] **Step 8: Report**

- State the commands actually run, and their results.
- State that no model was called from code, and no SEC request was sent.
- Give Task 5's `unchanged:` lines and the pilot's count.
- List the deferred items ticked, noted, and appended, and the backlog's summary
  line.
- State that Codex was skipped (P10-3).
- Note that the remaining 25 bundles may now follow plan 9's Task 19, Steps 1 to 7.
