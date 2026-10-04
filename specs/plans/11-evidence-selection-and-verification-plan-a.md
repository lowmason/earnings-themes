# Evidence Selection and Verification, Plan A: Core and Anchoring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 7 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

> Plan A of Stage 7's spec, `specs/evidence-selection-and-verification.md`, §Plan A
> only (ES1). The stamp above is the spec's Rollout line, and its "plan completion"
> means plan B's: this plan's completion does not tick Stage 7. It appends the spec's
> `Plan A: COMPLETE` line, ticks the deferred items the spec gives plan A, and retires
> this plan alone, so the spec stays live for plan B (P11-1). Plan B is planned only
> after this plan merges.

**Goal:** Settle plan 3's three open items in `earnings-core` under
`VALIDATOR_VERSION` `"3"`, move `canonical_json` and `digest` into core, pin
`context_hash`'s byte format, and let a transparent `other` container hold a quote,
while proving that no committed record changes.

**Architecture:**

- **Core.**
  - `evidence.py` gains `reverify_span` (ES5), and `validate_span` checks its offsets
    before anything else.
  - `structure.py`'s `resolve_pointer` resolves the genuine element through a public
    `is_genuine`, which `evidence.py` now imports.
  - A new `digests.py` holds `canonical_json` and `digest`, moved verbatim (ES7).
  - `SCHEMA_VERSION` stays 2, since no contract changes.
- **Ingestion and themes.**
  - Both import the one core definition. Ingestion's `cohort/digests.py` and the
    copies in themes' `records.py` are deleted.
  - In `anchoring.py`, `_home` becomes the public `narrative_home`, and an `other`
    element whose children hold all its text no longer blocks a quote (ES9).
  - `context_hash` is unchanged, and a known-answer test pins it (ES8).
- **The proof.** No committed byte changes.
  - The worktree's default suite reloads and rehashes every committed record. Task 1
    first adds the Stage 6 references that no offline test checked.
  - `git diff --stat` over the record directories prints nothing (Task 8).
  - The user's default-suite run in the main checkout, where `data/` lives, is the
    last gate (Completion, Step 2).

**Tech Stack:** Python 3.14.0 and uv 0.12.15; pydantic 2.13.5, pytest 9.1.1, and
Ruff 0.16.8, all locked. No new dependency: `uv.lock` does not change.

## What plan A implements

The spec's §Plan A, its gates, and its share of §Deferred items and §Rollout:

| The spec | Task |
| --- | --- |
| §The core fixes, item 1: `reverify_span` (ES5) | 2 |
| §The core fixes, item 3: an unvalidated offset is `malformed_record` | 3 |
| §The core fixes, items 2 and 4: the genuine element, and `VALIDATOR_VERSION = "3"` (ES4) | 4 |
| §The `canonical_json` move (ES7, M6) | 5 |
| §`context_hash` (ES8, T6-M3) | 6 |
| §The narrative rule (ES9, T6-M1) | 7 |
| §The proof: each record mapped to the test that rehashes it, and a test for any not yet covered | 1, 8 |
| §The proof: the diff; §Gates, plan A, gate 1 | 8 |
| §The proof: the main checkout; §Gates, plan A, gate 2 | Completion, Step 2 |
| §Verification: `docs/verification/evidence-selection.md` records plan A's proof | 8; Completion, Step 2 |
| §Deferred items, plan A's share; §Rollout, plan A | Completion |

Item 3 comes before items 2 and 4: the version's docstring names both changed
outcomes, so the bump lands with the last of them (Task 4).

**Out of scope:**

- everything in §Plan B: `Rejection`'s subject (ES6), T6-M4's mask-branch test, and
  the wording guard's reading of `prompts/`;
- the roadmap's tick (P11-1);
- a check of every field of an unparsed candidate in `validate_span` (P11-10).

## Global Constraints

Every task's requirements include these.

**Locators.**

- `ESn` are the spec's decisions (`specs/evidence-selection-and-verification.md`),
  and `P11-n` this plan's (Plan decisions).
- `Rn` and `Vn` are the requirements and verification items of
  `specs/evidence-linked-theme-extraction.md`. `A §n` is `AGENTS.md`, by line.
- `D-n` are plan 3's decisions, and `GSn` the Stage 6 spec's. `P9-n`, `P10-n`, and
  `P7-n` are plans 9's, 10's, and 7's.
- `T6-M1`, `T6-M3`, `T3-M5`, and `M6` are plan 9's review items, and `M5` is plan
  10's count, as `specs/deferred_items.md` names them.
- Line numbers cite the branch at `186348d`.

**Versions and constants.**

| Name | Value | Where |
| --- | --- | --- |
| Base | `186348d`, the branch's tip at planning; only docs changed since `337c882` | the byte check's base |
| Branch and worktree | `stage-7-evidence-selection-and-verification`, unpushed, checked out in `/Users/lowell/Projects/earnings-themes/.claude/worktrees/stage-7-evidence-selection-and-verification`, which has no `data/` | Tasks 1 to 8, Completion |
| Main checkout | `/Users/lowell/Projects/earnings-themes`, on `main` at `c5719f8`, with `data/` | the user's gate only |
| Core schema | `2`, unchanged | `earnings_core.SCHEMA_VERSION` |
| Validator | `"2"`, becoming `"3"` (ES4); no committed record stores it | `earnings_core.VALIDATOR_VERSION` |
| Themes record schema; canonicalization | `1`, unchanged; `walker-1`, unchanged | `THEMES_SCHEMA_VERSION`; `canonical/` |
| The container | `other-3292-5040` in `0000949699-08-000023_ex-99-1`: 7 list items, 10 sentences, only newlines between them | `tests/fixtures/canonical/` |
| The fixture pin | of 686 sentences: 660 anchored, 26 `ambiguous_occurrence`, 0 `not_narrative` (plan 10 pinned 650, 26, 10) | `test_anchoring.py` |
| The known answer | `fd4874e7855a8b8d6c9df217cca901d75d1129624089f94a6db6cda22ef52280`, over a 47-byte pair | Task 6 |
| Pilot v1 | content hash `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926` | the pin |

**Offline, no SEC, and no models.**

- No step sends an SEC request or calls a model, and no task opens the SEC client.
- Default tests make no network call and no billable call, and need no credential.
- **`EDGAR_IDENTITY` is exported in this shell.** A `live` test's skip guard does not
  stop it, and live tests send real SEC requests. Never pass `-m live`, and never
  `-m browser`. To check collection, use `--collect-only`.

Plan 9's Blinding section follows verbatim, from
`specs/plans/completed/9-pilot-codebook-split-and-gold-set-protocol.md`, Global
Constraints. Its references, `guarded` (Task 10), P9-5, Human gates, and P9-22, are
plan 9's. Plan 11's additions follow the block, and narrow it where they differ.

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

**Plan 11's additions to Blinding.** These bind the same sessions, and every subagent
dispatch carries them with the block above:

- **The user's instruction for Stage 7 (ES2, 2026-10-04).** Open nothing under
  `data/`, in the worktree or in the main checkout, and read no gold. Plan A reads
  only committed records and Stage 1's fixtures. So this plan lists nothing under
  `data/` either: the block's allowance to list draft names goes unused. The worktree
  has no `data/` by design. Never create one there, copy one in, or link one.
- **Only programs read the gold.** This plan treats
  `evaluation/djia-2024q3-2026q2/pilot-v1/gold/*.toml` and
  `tests/fixtures/gold/hard-negatives.toml` as gold. Never open, `cat`, `grep`, or
  print either. The tests and loaders that read them print IDs, counts, labels, and
  hashes.
- **The search rule.** Never `find`, `grep`, `rg`, or list anything under `data/`.
  Every other search names its pathspecs, as this plan's commands do (`-- "*.py"`,
  or named directories), so no search prints a line of the gold.
- **The main checkout is the user's.** No session executing this plan runs a command
  there. The user runs the gate there (P11-12), and reports counts, node IDs, and
  exception types only.
- **Traceback flags.** The root `addopts` sets `--tb=short`, since pytest's default
  traceback prints a failing frame's arguments. Never pass `--tb=long`, `--tb=auto`,
  `--full-trace`, `-l`, `--showlocals`, `--pdb`, or `-vv`.
- **The exceptions stay spent.** Plan 9's two one-time exceptions are used up. No
  session reads a draft, working copy, anchored file, view, or text.
- **Codex is skipped** (P11-3).

**Bytes.**

- These committed records stay byte-identical:
  - universe v1 and its curated files (`config/universe/djia/`);
  - events v1, its evidence record, and pilot v1 (`config/corpus/djia-2024q3-2026q2/`);
  - the split, the coverage report, the briefs, and the three gold files
    (`evaluation/djia-2024q3-2026q2/pilot-v1/`);
  - codebook v0 (`codebooks/djia-pilot/codebook-v0.toml`);
  - everything under `tests/fixtures/`: the canonical fixtures, the synthetic cohort
    and events, and the curated hard negatives.
- `canonical_json` and `digest` move verbatim, so what they emit never changes (ES7).
  Nor does any byte that `context_hash` hashes (ES8).
- Task 8 shows it: the records' tests pass, and
  `git diff --stat 186348d -- config evaluation codebooks tests/fixtures` prints
  nothing.

**Do not touch.**

- Repository files:
  - `AGENTS.md`, which other files cite by line number;
  - `.gitignore`, whose credentials block stays last;
  - `.python-version`, which pins 3.14.0;
  - `uv.lock`, and every `pyproject.toml`.
- Everything under `config/`, `evaluation/` (the briefs included), `codebooks/`,
  `tests/fixtures/`, and `prompts/`. The gold brief already calls list items
  quotable, and is not edited (the spec, §The narrative rule).
- Frozen code and decisions: `walker-1`'s generated files (`canonical/decode.py`,
  `dom.py`, and `walker.py`), Stage 1's frozen harness under
  `expirements/parser-fidelity/`, and ADRs 0001 to 0003.
- Completed documents: the Stage 3 and Stage 6 specs, and plans 4 and 9, which the
  spec does not edit. Also the roadmap (P11-1).
- Code this plan leaves alone: `packages/earnings-themes/src/earnings_themes/synthetic.py`
  (P11-9), and every module of `apps/earnings-pipeline`.
- `docs/verification/pilot-v1-gold-set.md`, beyond Task 7's one bullet.
- `CLAUDE.md` and `README.md`, except the refresh at Completion, Step 7, and that
  only on the user's direct yes.

**Where, and git.**

- Run Tasks 1 to 8 and Completion in the worktree, on the branch, from the worktree's
  root. Never `cd` elsewhere: the working directory persists between commands.
- `git add` only the paths a task names, and `git rm` the two files Task 5 deletes.
  Never `git add -A` or `git add .`. After each commit, `git status --short` prints
  nothing.
- The user may commit on this branch while the plan runs. Run `git log --oneline -3`
  before every commit, and never rewrite a commit you did not make.
- **Never push.** `origin`, https://github.com/lowmason/earnings-themes, is public
  (Completion, Step 8).
- **The command sandbox.**
  - Use literal paths, with no shell variables, loops, or multi-line heredocs. Write
    a multi-line program to `/tmp/plan11-*.py` with the Write tool, then run it.
  - Quote a glob, or use a git pathspec: zsh aborts a command whose glob matches
    nothing.
  - `git grep` skips untracked files, so pass `--untracked` before a new file is
    committed.

**Tests.**

- Tests use synthetic text and Stage 1's committed fixtures only.
- Each new behavior the spec names gets a new test; other cases fold into existing
  tests. Plan A adds 10 collected tests: 3 in Task 2, 4 in Task 3, 1 in Task 4, 1 in
  Task 6, and 1 in Task 7. Task 5 moves 4 and adds none.
- **Baselines** at `186348d`, in the worktree:
  - the default suite: `1737 passed, 8 skipped, 24 deselected`, each skip a local leg
    that needs `data/` (Preconditions, Step 3);
  - the harness suite: `275 passed, 5 skipped`;
  - Ruff: `All checks passed!` and `297 files already formatted`.
- **The main checkout's baseline** at `c5719f8` (plan 10):
  `1744 passed, 1 skipped, 24 deselected`.
- **The default suite after each task**, with `8 skipped, 24 deselected` each time:

| After Task | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Passed | 1737 | 1740 | 1744 | 1745 | 1745 | 1746 | 1747 |

- If a count differs while nothing fails, stop and report it rather than editing a
  test to match.

**Text.**

- Every new or replaced line of Python is ASCII. The data dictionary's and the
  records' new text is ASCII.
- No file carries a backslash-u escape typed by hand. Task 6's escape literals come
  only from its generator (P11-8).
- Each code task's lint step ends with the escape check, which prints
  `escapes intact`. It allows `§`, which the existing docstrings hold.

**Edits.** Each change to an existing file is the line
``In `<path>`, replace:``, then a block with the exact old text, which matches once,
then the line `with:`, then a block with the new text. The Edit tool applies it as
given.

- Apply the edits in the order given. A later task's old text is the file as the
  earlier tasks leave it.
- If an old text does not match, stop and report it: the file has drifted from the
  plan.
- A new file is given whole after ``Create `<path>`:``.

**Commands.** These recur, run from the worktree's root:

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' <files>
```

- The first is the **default suite**. In the worktree its 8 local legs skip, and
  `-rs` prints each.
- The second is the **harness suite**, which no task changes.
- The third is **lint**.
- The fourth is the **escape check**, over the Python files a task names.

**Commit attribution.** End each commit message with the attribution line your
session's instructions specify. The commit blocks below omit it deliberately: the
right line names the model actually executing the work.

## Plan decisions

The planning session of 2026-10-04 put three choices to the user, and P11-2 to P11-4
record the answers. At the handoff the user confirmed P11-10, and asked for this plan
to be committed (P11-11). P11-12 is the user's instruction. The rest are the plan's
own.

**P11-1 — A plan A (the spec's ES1 and §Rollout).** This plan implements §Plan A
only. Its completion:

- keeps the spec live for plan B;
- does not tick Stage 7 in the roadmap;
- appends the spec's `Plan A: COMPLETE` line at the spec's end;
- retires this plan alone, as plan 7 did for Stage 5 (P7-1).

**P11-2 — The net covers every Stage 6 reference (the user's answer, "All Stage 6
refs").**

- **The gap.** Every committed record already has a test that reloads it through its
  loader and rehashes it (The proof's map). But no offline test checks that the Stage
  6 records name the pin and the split that the suite recomputes. Codebook v0's
  discovery corpus, the coverage report's pin, and each gold file's pin and split
  hash are checked only by the local legs, which skip in the worktree.
- **The fold.** Task 1 folds those checks into `test_stage6_records.py`. The gold has
  no content hash of its own, so its references and IDs are what an offline check can
  hold.
- **What it catches.** If the moved functions changed the pin's or the split's hash,
  each record that names them would fail the worktree's suite, not only the main
  checkout's.

**P11-3 — Codex (the user's answer).** Skipped. No `Codex reviewed` line is written.
At the final review and at finishing-a-development-branch's Step 4b, state the
reason: "GS13: a Codex review cannot carry the Blinding section, and the main
checkout's `data/` holds pilot text, the held-out test bundles' included."

**P11-4 — T3-M5's two functions (the user's answer).** Plan 9's gaps item lists
`canonical_json` and `digest` among T3-M5's functions with no direct test. Their
moved known-answer tests now test them in core. Completion notes T3-M5's two as done
in plan 11, and the gaps item stays open for the rest.

**P11-5 — The net comes first (plan-made).** Task 1 lands before any code changes.
Each later task's default-suite run then checks every committed record, references
included, against the code as that task leaves it. Task 1's checks pass at once:
they pin committed records, and no task may change one.

**P11-6 — `is_genuine` (plan-made).** The genuine-element predicate moves from
`evidence._genuine` to a public `is_genuine` in `structure.py`, beside
`resolve_pointer`, which uses it.

- `evidence.py` imports it, so no module imports another's private name.
- No import cycle forms: `structure.py` imports nothing from `evidence.py`.
- It is not exported from the package root, since the spec's §Inputs lists no such
  export.

**P11-7 — The moved module and its tests (plan-made).**

- **The module** keeps its name, `earnings_core/digests.py`, and its code verbatim.
  Two parts differ:
  - its docstring, which now says every record hash uses it and where it came from;
  - `sha256_hex`'s import, which comes from `earnings_core.hashing`, since the
    package root imports this module.
- **The tests.** The four known-answer tests move to
  `packages/earnings-core/tests/test_digests.py`, with their expectations unchanged.
  Core's tests import no sibling package, so a local `StrEnum` stands in for the
  cohort's `AssertedAction`, and core's `SpanLocator` for the cohort's
  `EvidenceLocator`.

**P11-8 — A generator writes the known answer (plan-made, from the spec's
§`context_hash`).**

- **Why.** The test's pair holds a non-ASCII character, a double quote, and a
  backslash. The tool channel decodes typed backslash-u escapes into literal
  characters, so neither this plan nor an implementer types the literals.
- **The generator.** `/tmp/plan11-context-hash.py` builds the pair from code points.
  It computes the bytes and the hash from the spec's formula, never from
  `context_hash`, and appends the test with each value written by `ascii()`.
- **What this plan shows.** The generator, never the literals.
- **The checks.** Ruff then re-quotes one literal, and the escape check confirms
  that the file holds escape text only.

**P11-9 — The list bundle stays in the test (plan-made).** `list_bundle`, Task 7's
invented document, lives in `test_anchoring.py`, not `earnings_themes.synthetic`: no
other test uses it. Plan B's injection bundle goes in `synthetic.py` on its own terms.

**P11-10 — Offsets only, and first (plan-made, from the spec's item 3; confirmed by
the user at the handoff).**

- **What is checked.** `validate_span` checks `start` and `end` before any other
  check, and only those, as the spec's item 3 and its deferred item name. The detail
  names the field, as `parse_span_candidate`'s does, and never the value.
- **What is not.** Other fields of a candidate built by `model_copy` are not checked
  here. A `prefix` or `suffix` without a length, such as `None`, still raises at
  `len`.
- **Why that is safe today.** Every caller in the repository parses its candidate
  first, and `reverify_span` parses every field of a stored span. So no stored span
  reaches `validate_span` unparsed.
- **The user's answer.** At the handoff, the user chose offsets only over also
  refusing a `prefix` or `suffix` that is not a `str`. If the final review raises
  it, cite this answer. Whether to defer it is the user's call at the
  resolve-before-defer gate.

**P11-11 — The plan is committed at planning (the user's answer at the handoff).**
The planning session committed this file alone, on the branch, unpushed. So
Preconditions, Step 1 finds it committed, and skips Step 2's commit. If the file is
ever found untracked, Step 2 commits it.

**P11-12 — The last gate is the user's (the user's instruction).**

- **What.** The user runs the default suite in the main checkout at plan A's tip, on
  a detached HEAD, from a checkout with no tracked change. So the local legs run
  against `data/`: the gold rechecks, the coverage report's reproduction, the wording
  guard's pilot leg, the corpus quotes, and the event store.
- **Who.** No session runs a command there.
- **Failures.** One is reported by its node ID and exception type, never its
  traceback (the spec's §Gates).
- **When.** After the final review, at the code's last commit. Every later commit
  touches only `specs/`, `docs/verification/evidence-selection.md`, and `CLAUDE.md`,
  which no test reads.

## File map

| Path | Change | Task |
| --- | --- | --- |
| `tests/integration/test_stage6_records.py` | binds codebook v0, the coverage report, and the gold to the recomputed pin and split | 1 |
| `packages/earnings-core/src/earnings_core/evidence.py` | `reverify_span` (2); the offset check (3); `is_genuine` imported, `_genuine` removed (4) | 2, 3, 4 |
| `packages/earnings-core/src/earnings_core/structure.py` | `resolve_pointer`; `is_genuine` | 4 |
| `packages/earnings-core/src/earnings_core/rejections.py` | `VALIDATOR_VERSION = "3"` | 4 |
| `packages/earnings-core/src/earnings_core/digests.py` | new: `canonical_json` and `digest`, moved | 5 |
| `packages/earnings-core/src/earnings_core/__init__.py` | exports `reverify_span` (2), `canonical_json` and `digest` (5) | 2, 5 |
| `packages/earnings-core/tests/test_evidence.py` | 2 tests, 3 cases (2); 1 test, 4 cases (3) | 2, 3 |
| `packages/earnings-core/tests/test_structure.py` | 1 test | 4 |
| `packages/earnings-core/tests/test_public_api.py` | the public set (2, 5); the validator pin (4) | 2, 4, 5 |
| `packages/earnings-core/tests/test_digests.py` | new: the moved known-answer tests | 5 |
| `packages/earnings-ingestion/src/earnings_ingestion/cohort/digests.py` | deleted | 5 |
| `packages/earnings-ingestion/tests/test_cohort_digests.py` | deleted | 5 |
| `packages/earnings-ingestion/src/earnings_ingestion/cohort/`: `build.py`, `config.py`, `findings.py`, `identity.py`, `locators.py`, `register.py`, `synthetic.py` | import the core definition | 5 |
| `packages/earnings-ingestion/src/earnings_ingestion/events/`: `coverage.py`, `pilot.py`, `records.py` | import the core definition | 5 |
| `packages/earnings-ingestion/tests/test_cohort_findings.py` | imports the core `digest` | 5 |
| `packages/earnings-themes/src/earnings_themes/records.py` | drops its copies | 5 |
| `packages/earnings-themes/src/earnings_themes/split.py`, `codebook.py` | import the core `digest` | 5 |
| `packages/earnings-themes/src/earnings_themes/anchoring.py` | `context_hash`'s docstring (6); the narrative rule and `narrative_home` (7) | 6, 7 |
| `packages/earnings-themes/tests/test_anchoring.py` | the known answer (6); the container test and the fixture pin (7) | 6, 7 |
| `docs/data-dictionary.md` | §`VerifiedSpan` (2); §`RejectionReason` (3); the validator bullet (4); the canonical JSON bullet (5); `context_sha256` (6); `not_narrative` (7) | 2 to 7 |
| `docs/verification/pilot-v1-gold-set.md` | one bullet under M5 | 7 |
| `/tmp/plan11-context-hash.py` | the generator; never committed | 6 |
| `docs/verification/evidence-selection.md` | new: plan A's proof (8) and the gate (Completion) | 8, Completion |
| `specs/deferred_items.md`, the spec, and this plan | Completion | Completion |
| `CLAUDE.md` | "Current state", only on the user's yes | Completion |

**Read, never written:**

- `apps/earnings-pipeline/src/earnings_pipeline/stage6.py`, whose `Layout`,
  `load_pinned`, `PILOT_V1`, `PILOT_V1_HASH`, `UNIVERSE_V1`, `CODEBOOK_FILE`, and
  `file_stem` Task 1 imports;
- `packages/earnings-core/tests/conftest.py`, whose `sample` fixture Tasks 2 to 4
  use;
- `packages/earnings-themes/tests/conftest.py`, whose `fixtures` and `synthetic`
  fixtures Tasks 6 and 7 use;
- the committed records the proof rehashes, through their tests only.

## The proof's map

Each committed record, and the tests that reload it through its loader and recompute
its content hash with the moved functions. Task 8 runs the worktree's column by node
ID. The last column runs only at the user's gate (P11-12).

| Record | Path | Rehashed offline, in the worktree, by | Rechecked in the main checkout only, by |
| --- | --- | --- | --- |
| Universe v1 | `config/universe/djia/` | `packages/earnings-ingestion/tests/test_cohort_identity.py::test_v1_loads_unchanged_and_has_an_operative_hash`: content hash `2d9743945dc5748fccec4c4963f6fa891a41e8863d56e99841569ff25fa884b4`, operative hash `c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573` | — |
| The synthetic cohort | `tests/fixtures/cohort/` | `tests/integration/test_cohort_fixtures.py::test_the_fixture_regenerates_byte_for_byte` and `::test_saved_evidence_replays_to_the_frozen_manifest` | — |
| Events v1 and its evidence record | `config/corpus/djia-2024q3-2026q2/` | `tests/integration/test_event_corpus_v1.py::test_events_v1_loads_unchanged_with_its_evidence_record`: `2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7` | — |
| Pilot v1, reselected | `config/corpus/djia-2024q3-2026q2/` | `tests/integration/test_event_corpus_v1.py::test_pilot_v1_loads_unchanged_and_djia_pilot_1_reselects_it`; `tests/integration/test_stage6_pilot_v1.py::test_the_pin_is_pilot_v1_and_its_chain` | — |
| The synthetic events and acquisition | `tests/fixtures/events/` | `tests/integration/test_event_fixtures.py::test_the_fixture_regenerates_byte_for_byte`, `::test_p_vi_replays_offline_to_the_frozen_manifests`, and `::test_p_vi_replays_the_acquisition_offline` | — |
| The split | `evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json` | `tests/integration/test_stage6_pilot_v1.py::test_the_committed_split_reproduces_byte_for_byte` | — |
| The coverage report | `evaluation/djia-2024q3-2026q2/pilot-v1/coverage-v1.json` | `tests/integration/test_stage6_records.py`: its hash, and its pin (Task 1) | `tests/integration/test_stage6_pilot_v1.py::test_the_committed_coverage_report_reproduces_from_its_runs` |
| Codebook v0 | `codebooks/djia-pilot/codebook-v0.toml` | `tests/integration/test_stage6_records.py`: its hash, ADR 0003's citation, and its corpus's pin and split hash (Task 1) | `tests/integration/test_stage6_pilot_v1.py::test_committed_records_validate_against_the_local_store`, codebook case |
| The three gold files | `evaluation/djia-2024q3-2026q2/pilot-v1/gold/` | `tests/integration/test_stage6_records.py`: each parses, codes against v0, holds together by ID, and names the pin and the split hash (Task 1) | the same local test, gold case: each pointer, quote hash, and context hash against its document |
| The curated hard negatives | `tests/fixtures/gold/hard-negatives.toml` | `tests/integration/test_stage6_pilot_v1.py::test_the_curated_hard_negatives_validate_offline`: pin, codebook, pointers, and context hashes over Stage 1's fixtures | — |
| The canonical fixtures | `tests/fixtures/canonical/` | `tests/integration/test_canonical_golden.py::test_the_canonical_fixture_regenerates_byte_for_byte`, 8 cases | — |

The main checkout's run also covers what has no committed record of its own: the
event store (`test_event_store_v1.py`), the corpus quotes (`test_corpus_quotes.py`),
the confirmed exhibits (`test_events_content.py`), and the wording guard's pilot leg
(`test_stage6_wording.py`).

## Expected outputs

At planning, on 2026-10-04, in the worktree at `186348d`:

- **Tasks 1 to 7 were replayed in place, in this plan's order.**
  - Each edit was applied as given, and each red and green run printed the Expected
    output its step gives.
  - Ruff passed on the result, and the escape check printed `escapes intact`.
  - Task 8's checks then ran:
    - the proof's map printed `20 passed, 3 skipped`;
    - `git diff --stat 186348d -- config evaluation codebooks tests/fixtures` printed
      nothing;
    - the default suite printed `1747 passed, 8 skipped, 24 deselected`, and the
      harness suite `275 passed, 5 skipped`;
    - `uv.lock` was unchanged.
- **Two discriminating checks.**
  - A variant of `reverify_span` that dumps the span failed
    `test_a_tampered_stored_span_is_refused_and_never_dumped[float-offset]`
    (`1 failed, 17 passed` on `test_evidence.py`), so that test tells the two apart.
  - Task 6's mutation step printed its Expected output.
- **This plan's own text was checked against the replay.**
  - A script applied this plan's edit blocks for Tasks 1 to 7 in order, with Task
    6's generator and `ruff format` between them. Each old text matched exactly once.
  - The resulting `git diff` was byte-identical to the replay's, and so were the two
    new core files and the generated test file.
  - Ruff passed, and the default suite printed
    `1747 passed, 8 skipped, 24 deselected`.
  - A dry run of Completion's 14 edits found each old text exactly once.
- **The worktree was restored.** `git restore` was run on every edited path and the
  new files were removed; `git status --short` then printed nothing. Then, at the
  user's request, this file was committed alone (P11-11). Nothing else was
  committed.
- **Not replayed:**
  - Task 8's record, which is written at execution;
  - the user's gate in the main checkout, which no planning session may run.

A `[GATE: ...]` mark in the record is a value the user's gate reports. Fill it from
the user's report, and never predict it.

## Preconditions — before Task 1

- [ ] **Step 1: Probe the state**

Run each from the worktree's root,
`/Users/lowell/Projects/earnings-themes/.claude/worktrees/stage-7-evidence-selection-and-verification`:

```bash
git branch --show-current
git log --oneline -3
git status --short
test -e data && echo "data/ is present" || echo "no data/"
```

Expected:

- `stage-7-evidence-selection-and-verification`;
- the top commit is
  `186348d docs(roadmap): Stage 7's spec amends its handoff from Stages 3 and 6`, or
  this plan's commit on top of it;
- `?? specs/plans/11-evidence-selection-and-verification-plan-a.md`, or nothing once
  the plan is committed;
- `no data/`.

Read the first row that matches:

| What the probe shows | Go to |
| --- | --- |
| `data/ is present` | Stop and ask the user: the worktree has no `data/` by design (ES2) |
| Commits after this plan's commit, each naming its task | Resume after the last task whose commit is there |
| This plan committed, and nothing else since `186348d` | Step 3 |
| Any other change since `186348d`, or any other untracked file | Stop and report it |
| As expected | Step 2 |

- [ ] **Step 2: Commit this plan**

```bash
git log --oneline -3
git add specs/plans/11-evidence-selection-and-verification-plan-a.md
git commit -m "docs(specs): plan 11, Stage 7's plan A: core and anchoring"
git status --short
```

Expected: the commit, then `git status --short` prints nothing.

- [ ] **Step 3: Confirm the baselines**

```bash
uv sync --locked --all-packages --group dev
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `1737 passed, 8 skipped, 24 deselected`, with exactly these skip lines,
each a local leg that needs `data/`:

```text
SKIPPED [1] packages/earnings-ingestion/tests/test_events_content.py:154: data/raw/discovery is not saved here
SKIPPED [1] tests/integration/test_corpus_quotes.py:104: data/raw/events/sec-edgar is not saved here: each freeze's gate runs this test
SKIPPED [1] tests/integration/test_event_store_v1.py:40: data/raw/events is not saved here: each gate runs this test
SKIPPED [1] tests/integration/test_event_store_v1.py:69: no acquisition run is saved here: the live gate runs this test
SKIPPED [1] tests/integration/test_stage6_pilot_v1.py:133: data/runs/events/ is not here: each Stage 6 gate runs this test
SKIPPED [2] tests/integration/test_stage6_pilot_v1.py:164: data/runs/events/ is not here: each Stage 6 gate runs this test
SKIPPED [1] tests/integration/test_stage6_wording.py:93: data/runs/events/ is not here: each Stage 6 gate runs this test with -rs
```

Then `275 passed, 5 skipped`; then `All checks passed!` and
`297 files already formatted`. Any other count: stop and report it.

### Task 1: The proof's net: Stage 6's references, offline (P11-2)

**Files:**
- Modify: `tests/integration/test_stage6_records.py:1-68`

**Interfaces:**
- Consumes, all existing:
  - from `earnings_pipeline.stage6`: `Layout(repo, universe, pilot, pilot_hash)`,
    `load_pinned(layout)`, and the constants `PILOT_V1`, `PILOT_V1_HASH`, and
    `UNIVERSE_V1`;
  - `load_pinned(...)`'s `.pin`, a themes `Pin`, and `.coverage_pin`, ingestion's
    `PilotPin`;
  - `load_split(path) -> SplitManifest` in `earnings_themes.split`;
  - `Codebook.discovery_corpus`, with `.pin` and `.split_hash`;
  - `Gold.pin` and `Gold.split_hash`;
  - `load_coverage(path)` and its `.pin`.
- Produces: the offline net that the proof's map cites,
  `test_codebook_v0_the_coverage_report_and_the_gold_hold_offline`, still one test.

- [ ] **Step 1: Fold in the reference checks**

In `tests/integration/test_stage6_records.py`, replace:

```python
content hash, is approved, and is cited by ADR 0003; the coverage report hashes to
its own; and each gold file is named for its event, codes against v0, agrees with
its ``no_theme``, and holds together by ID.
```

with:

```python
content hash, is approved, and is cited by ADR 0003; the coverage report hashes to
its own; codebook v0, the coverage report, and each gold file bind to the pin and
the split that the suite recomputes (plan 11, P11-2); and each gold file is named
for its event, codes against v0, agrees with its ``no_theme``, and holds together
by ID.
```

In `tests/integration/test_stage6_records.py`, replace:

```python
from earnings_pipeline.stage6 import CODEBOOK_FILE, file_stem
```

with:

```python
from earnings_pipeline.stage6 import (
    CODEBOOK_FILE,
    PILOT_V1,
    PILOT_V1_HASH,
    UNIVERSE_V1,
    Layout,
    file_stem,
    load_pinned,
)
```

In `tests/integration/test_stage6_records.py`, replace:

```python
from earnings_themes.gold import CodebookRef, load_gold, no_theme_of
```

with:

```python
from earnings_themes.gold import CodebookRef, load_gold, no_theme_of
from earnings_themes.split import load_split
```

In `tests/integration/test_stage6_records.py`, replace:

```python
def test_codebook_v0_the_coverage_report_and_the_gold_hold_offline() -> None:
    codebook = load_codebook(REPO / CODEBOOK_FILE)
    stored = codebook.content_hash
    recomputed = codebook_hash(codebook)
    status = codebook.status
    adr = codebook.approval.adr if codebook.approval is not None else None
    cited = stored in (REPO / ADR).read_text(encoding="utf-8")
    assert (recomputed, status, adr, cited) == (
        stored,
        CodebookStatus.APPROVED,
        ADR,
        True,
    )

    load_coverage(EVALUATION / "coverage-v1.json")
```

with:

```python
def test_codebook_v0_the_coverage_report_and_the_gold_hold_offline() -> None:
    pinned = load_pinned(Layout(REPO, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH))
    split_hash = load_split(EVALUATION / "split-v1.json").content_hash
    codebook = load_codebook(REPO / CODEBOOK_FILE)
    stored = codebook.content_hash
    recomputed = codebook_hash(codebook)
    status = codebook.status
    adr = codebook.approval.adr if codebook.approval is not None else None
    cited = stored in (REPO / ADR).read_text(encoding="utf-8")
    corpus = codebook.discovery_corpus
    assert (recomputed, status, adr, cited, corpus.pin, corpus.split_hash) == (
        stored,
        CodebookStatus.APPROVED,
        ADR,
        True,
        pinned.pin,
        split_hash,
    )

    coverage = load_coverage(EVALUATION / "coverage-v1.json")
    assert coverage.pin == pinned.coverage_pin
```

In `tests/integration/test_stage6_records.py`, replace:

```python
            "file_stem": path.stem == file_stem(gold.event_id),
```

with:

```python
            "file_stem": path.stem == file_stem(gold.event_id),
            "pin": gold.pin == pinned.pin,
            "split_hash": gold.split_hash == split_hash,
```

- [ ] **Step 2: Run it**

```bash
uv run --locked --all-packages pytest tests/integration/test_stage6_records.py -q
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
```

Expected: `1 passed`; then `1737 passed, 8 skipped, 24 deselected`, with
Preconditions' skip lines.

The checks pass at once (P11-5), since they pin committed records. Never edit a
committed record to make one pass. If one fails, stop and report the failing check's
name: a record names another pin or split than the suite recomputes.

- [ ] **Step 3: Lint, and the escape check**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' tests/integration/test_stage6_records.py
```

Expected: `All checks passed!`, `297 files already formatted`, and `escapes intact`.

- [ ] **Step 4: Commit**

```bash
git log --oneline -3
git add tests/integration/test_stage6_records.py
git commit -m "test(integration): bind Stage 6's records to the recomputed pin and split (plan 11, P11-2)"
git status --short
```

Expected: `git status --short` prints nothing.

### Task 2: `reverify_span` (plan 3's item 1; ES5)

**Files:**
- Modify: `packages/earnings-core/src/earnings_core/evidence.py:1` (the docstring), `:176` (before `_reject`)
- Modify: `packages/earnings-core/src/earnings_core/__init__.py:23-28`, and `__all__`
- Modify: `docs/data-dictionary.md:191-192` (§`VerifiedSpan`)
- Test: `packages/earnings-core/tests/test_evidence.py`, `packages/earnings-core/tests/test_public_api.py`

**Interfaces:**
- Consumes:
  - `parse_span_candidate(raw: object) -> SpanCandidate | Rejection` and
    `validate_span(document, elements, candidate) -> VerifiedSpan | Rejection` in
    `earnings_core.evidence`;
  - `SpanCandidate.model_fields`, whose eight names `VerifiedSpan` shares, beside its
    own `validator_version`;
  - the fixture `sample` in `packages/earnings-core/tests/conftest.py`: its
    `.document`, `.elements`, and `.candidate(text) -> SpanCandidate`.
- Produces:
  `reverify_span(document: CanonicalDocument, elements: Sequence[DocumentElement], span: VerifiedSpan) -> VerifiedSpan | Rejection`,
  exported from `earnings_core`. Plan B's `write_run` calls it, and so does each
  later R6.1 gate.

- [ ] **Step 1: Write the failing tests**

In `packages/earnings-core/tests/test_evidence.py`, replace:

```python
import inspect
import json

import pytest
```

with:

```python
import inspect
import json
import warnings

import pytest
```

In `packages/earnings-core/tests/test_evidence.py`, replace:

```python
    parse_span_candidate,
    validate_span,
)
from earnings_core.locators import SpanLocator, make_locator, resolve_locator
```

with:

```python
    parse_span_candidate,
    reverify_span,
    validate_span,
)
from earnings_core.locators import SpanLocator, make_locator, resolve_locator
```

Two tests follow the file's last one, cover the spec's three cases, and pin that the
span is never dumped:

In `packages/earnings-core/tests/test_evidence.py`, replace:

```python
def test_a_malformed_record_names_the_offending_field(sample) -> None:
    outcome = parse_span_candidate(sample.raw("Margins held", start=1.5))
    assert isinstance(outcome, Rejection)
    assert outcome.detail.startswith("start:")
```

with:

```python
def test_a_malformed_record_names_the_offending_field(sample) -> None:
    outcome = parse_span_candidate(sample.raw("Margins held", start=1.5))
    assert isinstance(outcome, Rejection)
    assert outcome.detail.startswith("start:")


def test_a_stored_span_re_verifies_under_the_current_validator(sample) -> None:
    """A span read back from JSON verifies again into a fresh span, even one an
    earlier validator stamped: a stored span's type alone is not proof (ES5)."""
    candidate = sample.candidate("Margins held at last year's level.")
    verified = validate_span(sample.document, sample.elements, candidate)
    assert isinstance(verified, VerifiedSpan)
    stored = VerifiedSpan.model_validate_json(verified.model_dump_json())
    assert reverify_span(sample.document, sample.elements, stored) == verified
    older = VerifiedSpan.model_validate(
        {**verified.model_dump(), "validator_version": "1"}
    )
    assert reverify_span(sample.document, sample.elements, older) == verified


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (
            lambda span: {"quote_text": "Margins held"},
            RejectionReason.QUOTE_TEXT_MISMATCH,
        ),
        (
            lambda span: {"start": float(span.start)},
            RejectionReason.MALFORMED_RECORD,
        ),
    ],
    ids=["changed-text", "float-offset"],
)
def test_a_tampered_stored_span_is_refused_and_never_dumped(
    sample, change, reason
) -> None:
    """``model_copy`` skips validation, so a stored span may hold anything. It is
    refused with a reason, never raised, and never dumped, since dumping a float
    in an integer field warns (ES5)."""
    candidate = sample.candidate("Margins held at last year's level.")
    verified = validate_span(sample.document, sample.elements, candidate)
    assert isinstance(verified, VerifiedSpan)
    tampered = verified.model_copy(update=change(verified))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        outcome = reverify_span(sample.document, sample.elements, tampered)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is reason
```

The root exports it:

In `packages/earnings-core/tests/test_public_api.py`, replace:

```python
    "resolve_pointer",
    "sha256_hex",
```

with:

```python
    "resolve_pointer",
    "reverify_span",
    "sha256_hex",
```

- [ ] **Step 2: Run them to see them fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests tests/contracts/test_data_dictionary.py -q
```

Expected: the run stops at collection with `1 error`. `test_evidence.py` cannot
import `reverify_span`, which does not exist yet.

- [ ] **Step 3: Write `reverify_span`, and export it**

In `packages/earnings-core/src/earnings_core/evidence.py`, replace:

```python
"""Evidence spans: parse an untrusted candidate, then verify it exactly (R6.1)."""
```

with:

```python
"""Evidence spans: parse an untrusted candidate, verify it exactly, and verify a
stored span again at each later gate (R6.1)."""
```

In `packages/earnings-core/src/earnings_core/evidence.py`, replace:

```python
def _reject(reason: RejectionReason, detail: str) -> Rejection:
    return Rejection(reason=reason, detail=detail)
```

with:

```python
def reverify_span(
    document: CanonicalDocument,
    elements: Sequence[DocumentElement],
    span: VerifiedSpan,
) -> VerifiedSpan | Rejection:
    """Verify a stored span again, as each later R6.1 gate must: its type alone is
    not proof, since ``model_copy(update=...)`` skips validation (ES5).

    The span's candidate fields, all but ``validator_version``, are read into a
    mapping and parsed as a fresh candidate, so a value construction would refuse
    is ``malformed_record``. The span is never dumped: dumping a copy that holds a
    float in an integer field warns. A span that verifies comes back fresh, under
    the current ``VALIDATOR_VERSION``.
    """
    fields = {name: getattr(span, name) for name in SpanCandidate.model_fields}
    candidate = parse_span_candidate(fields)
    if isinstance(candidate, Rejection):
        return candidate
    return validate_span(document, elements, candidate)


def _reject(reason: RejectionReason, detail: str) -> Rejection:
    return Rejection(reason=reason, detail=detail)
```

In `packages/earnings-core/src/earnings_core/__init__.py`, replace:

```python
    parse_span_candidate,
    validate_span,
)
from earnings_core.hashing import hash_canonical_text, sha256_hex
```

with:

```python
    parse_span_candidate,
    reverify_span,
    validate_span,
)
from earnings_core.hashing import hash_canonical_text, sha256_hex
```

In `packages/earnings-core/src/earnings_core/__init__.py`, replace:

```python
    "resolve_pointer",
    "sha256_hex",
```

with:

```python
    "resolve_pointer",
    "reverify_span",
    "sha256_hex",
```

In `docs/data-dictionary.md`, replace:

```markdown
A span that passed every check (R6.1). Its `quote_text` is sliced from the canonical
text, never copied from a candidate (A §523).
```

with:

```markdown
A span that passed every check (R6.1). Its `quote_text` is sliced from the canonical
text, never copied from a candidate (A §523). A stored one is verified again with
`reverify_span` at each later gate, since its type alone is not proof.
```

- [ ] **Step 4: Run them to see them pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests tests/contracts/test_data_dictionary.py -q
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
```

Expected: `349 passed`; then `1740 passed, 8 skipped, 24 deselected`.

- [ ] **Step 5: Lint, and the escape check**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' packages/earnings-core/src/earnings_core/evidence.py packages/earnings-core/src/earnings_core/__init__.py packages/earnings-core/tests/test_evidence.py packages/earnings-core/tests/test_public_api.py
```

Expected: `All checks passed!`, `297 files already formatted`, and `escapes intact`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-core/src/earnings_core/evidence.py packages/earnings-core/src/earnings_core/__init__.py packages/earnings-core/tests/test_evidence.py packages/earnings-core/tests/test_public_api.py docs/data-dictionary.md
git commit -m "feat(core): reverify_span verifies a stored span again (plan 11, ES5)"
git status --short
```

Expected: `git status --short` prints nothing.

### Task 3: An unvalidated offset is `malformed_record` (plan 3's item 3)

**Files:**
- Modify: `packages/earnings-core/src/earnings_core/evidence.py:84-100` (`validate_span`)
- Modify: `docs/data-dictionary.md:256-257` (§`RejectionReason`)
- Test: `packages/earnings-core/tests/test_evidence.py`

**Interfaces:**
- Consumes:
  - `validate_span` and `_reject` in `evidence.py`;
  - `sample.candidate("Prepared remarks")`, which spans `[0, 16)`;
  - Task 2's `test_a_stored_span_re_verifies_under_the_current_validator`, which
    this task's test goes before.
- Produces: `validate_span` returns
  `Rejection(reason=RejectionReason.MALFORMED_RECORD, detail="<field>: an offset is an int, not a <type>")`
  for an offset whose type is not exactly `int`. It never raises on one (P11-10).

- [ ] **Step 1: Write the failing test**

One case per offset and type. The bool start's slice matches, so only a type check
can refuse it:

In `packages/earnings-core/tests/test_evidence.py`, replace:

```python
def test_a_stored_span_re_verifies_under_the_current_validator(sample) -> None:
```

with:

```python
@pytest.mark.parametrize(
    ("field", "value"),
    [("start", False), ("start", 0.0), ("end", 16.0), ("end", True)],
    ids=["bool-start-whose-slice-matches", "float-start", "float-end", "bool-end"],
)
def test_an_unvalidated_offset_is_malformed_and_never_raises(
    sample, field, value
) -> None:
    """A candidate built by ``model_copy`` skips ``parse_span_candidate``, so an
    offset may be a float or a bool: each is ``malformed_record``, never an
    exception, even where its slice would match (R3.2, R6.2)."""
    candidate = sample.candidate("Prepared remarks")
    assert (candidate.start, candidate.end) == (0, 16)
    unvalidated = candidate.model_copy(update={field: value})
    outcome = validate_span(sample.document, sample.elements, unvalidated)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.MALFORMED_RECORD
    assert outcome.detail.startswith(f"{field}:")


def test_a_stored_span_re_verifies_under_the_current_validator(sample) -> None:
```

- [ ] **Step 2: Run it to see it fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_evidence.py -q
```

Expected: `4 failed, 18 passed`.

- The bool start raises a `ValidationError` when `validate_span` builds the
  `TextSpan`.
- The float start and the float end raise `TypeError` at the slice.
- The bool end is refused, but as `quote_text_mismatch`.

- [ ] **Step 3: Check the offsets first**

In `packages/earnings-core/src/earnings_core/evidence.py`, replace:

```python
    a threshold (R13.2): text is compared with ``==``, never normalized. Check the
    element set once with ``validate_elements`` before checking spans against it.
    """
    problem = document_integrity_problem(document)
    if problem is not None:
        return _reject(RejectionReason.DOCUMENT_INTEGRITY, problem)
    text = document.canonical_text
```

with:

```python
    a threshold (R13.2): text is compared with ``==``, never normalized. Check the
    element set once with ``validate_elements`` before checking spans against it.

    An offset that is not an ``int``, or is a ``bool``, is ``malformed_record``
    before any check, as ``parse_span_candidate`` would have found: a candidate
    built by ``model_copy`` skips it, and a bad offset is refused, never raised.
    """
    for name in ("start", "end"):
        offset = getattr(candidate, name)
        if type(offset) is not int:
            return _reject(
                RejectionReason.MALFORMED_RECORD,
                f"{name}: an offset is an int, not a {type(offset).__name__}",
            )
    problem = document_integrity_problem(document)
    if problem is not None:
        return _reject(RejectionReason.DOCUMENT_INTEGRITY, problem)
    text = document.canonical_text
```

In `docs/data-dictionary.md`, replace:

```markdown
`parse_span_candidate` records `malformed_record`. `validate_span` then runs its checks
in the order of the next eleven rows and records the first failure.
```

with:

```markdown
`parse_span_candidate` records `malformed_record`, and so does `validate_span` for an
offset that is not an `int`, or is a `bool`, on a candidate that skipped parsing.
`validate_span` then runs its checks in the order of the next eleven rows and records
the first failure.
```

- [ ] **Step 4: Run them to see them pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests tests/contracts/test_data_dictionary.py -q
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
```

Expected: `353 passed`; then `1744 passed, 8 skipped, 24 deselected`.

- [ ] **Step 5: Lint, and the escape check**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' packages/earnings-core/src/earnings_core/evidence.py packages/earnings-core/tests/test_evidence.py
```

Expected: `All checks passed!`, `297 files already formatted`, and `escapes intact`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-core/src/earnings_core/evidence.py packages/earnings-core/tests/test_evidence.py docs/data-dictionary.md
git commit -m "fix(core): validate_span refuses an unvalidated offset, never raises (plan 11)"
git status --short
```

Expected: `git status --short` prints nothing.

### Task 4: The genuine element, and `VALIDATOR_VERSION = "3"` (plan 3's item 2; ES4)

**Files:**
- Modify: `packages/earnings-core/src/earnings_core/structure.py:43-72` (`resolve_pointer`; `is_genuine` after it)
- Modify: `packages/earnings-core/src/earnings_core/evidence.py:10-19` (imports), `:180-215` (`_genuine` and its three callers)
- Modify: `packages/earnings-core/src/earnings_core/rejections.py:7-12`
- Modify: `docs/data-dictionary.md:13-15` (the validator bullet)
- Test: `packages/earnings-core/tests/test_structure.py`, `packages/earnings-core/tests/test_public_api.py`

**Interfaces:**
- Consumes:
  - `derive_element_id(type, span)` in `earnings_core.elements`, and
    `document_integrity_problem` in `earnings_core.documents`;
  - the fixture `sample`: `.element(ElementType, text) -> DocumentElement`,
    `.elements`, `.document`, and `.text`.
- Produces:
  - `is_genuine(document: CanonicalDocument, element: DocumentElement) -> bool` in
    `earnings_core.structure`, which is not exported from the root (P11-6);
  - `resolve_pointer` returns the span of the genuine element wherever it sits;
  - `VALIDATOR_VERSION == "3"`, which plan B's cache key holds.

- [ ] **Step 1: Write the failing tests, and document the version**

The stale element is listed first, as the deferred item asks, and then a tampered
one is:

In `packages/earnings-core/tests/test_structure.py`, replace:

```python
def test_a_tampered_pointer_target_is_rejected(sample) -> None:
    heading = sample.element(ElementType.HEADING, "Prepared remarks")
    moved = heading.model_copy(update={"span": TextSpan(start=0, end=8)})
    outcome = resolve_pointer(sample.document, [moved], heading.element_id)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.ELEMENT_ID_MISMATCH
```

with:

```python
def test_a_tampered_pointer_target_is_rejected(sample) -> None:
    heading = sample.element(ElementType.HEADING, "Prepared remarks")
    moved = heading.model_copy(update={"span": TextSpan(start=0, end=8)})
    outcome = resolve_pointer(sample.document, [moved], heading.element_id)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.ELEMENT_ID_MISMATCH


def test_the_genuine_element_resolves_wherever_it_sits(sample) -> None:
    """An unchanged region keeps its ID across versions (D-1), so a list may name a
    stale element, or a tampered one, before the genuine one. The genuine element
    resolves wherever it sits; only when none has the ID is the pointer refused."""
    heading = sample.element(ElementType.HEADING, "Prepared remarks")
    older = CanonicalDocument.create(
        source_document_id="sample-call",
        canonicalization_version="test-0",
        canonical_text=sample.text,
    )
    stale = DocumentElement.create(older, ElementType.HEADING, heading.span, level=1)
    moved = heading.model_copy(update={"span": TextSpan(start=0, end=8)})
    assert stale.element_id == heading.element_id
    for first in (stale, moved):
        listed = [first, *sample.elements]
        resolved = resolve_pointer(sample.document, listed, heading.element_id)
        assert resolved == heading.span
    alone = resolve_pointer(sample.document, [stale], heading.element_id)
    assert isinstance(alone, Rejection)
    assert alone.reason is RejectionReason.WRONG_DOCUMENT
```

In `packages/earnings-core/tests/test_public_api.py`, replace:

```python
    assert earnings_core.VALIDATOR_VERSION == "2"
```

with:

```python
    assert earnings_core.VALIDATOR_VERSION == "3"
```

In `docs/data-dictionary.md`, replace:

```markdown
- **Validator version.** `"2"` (`earnings_core.VALIDATOR_VERSION`), stamped on every
  `Rejection` and `VerifiedSpan`. Caches key on it (R14.6); bump it whenever a check
  changes.
```

with:

```markdown
- **Validator version.** `"3"` (`earnings_core.VALIDATOR_VERSION`), stamped on every
  `Rejection` and `VerifiedSpan`. Caches key on it (R14.6); bump it whenever a check
  changes. Version 3 (Stage 7) refuses an unvalidated offset that is not an `int`,
  or is a `bool`, as `malformed_record` where version 2 raised, and resolves a
  pointer to this version's genuine element wherever it sits in the list. No
  committed record stores it.
```

- [ ] **Step 2: Run them to see them fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests tests/contracts/test_data_dictionary.py -q
```

Expected: `3 failed, 351 passed`.

- `test_versions_are_pinned` fails, since the version is still `"2"`.
- `test_the_genuine_element_resolves_wherever_it_sits` fails, since the stale
  element listed first is refused as `wrong_document`.
- `test_the_documented_versions_are_the_packages` fails, since the dictionary says
  `"3"`.

- [ ] **Step 3: Resolve the genuine element, and bump the version**

In `packages/earnings-core/src/earnings_core/structure.py`, replace:

```python
    Only an element of this document version resolves; anything else is an invalid
    pointer with a recorded reason (R5.1, V9).
    """
    problem = document_integrity_problem(document)
    if problem is not None:
        return Rejection(reason=RejectionReason.DOCUMENT_INTEGRITY, detail=problem)
    for element in elements:
        if element.element_id != element_id:
            continue
        if element.doc_id != document.doc_id:
            return Rejection(
                reason=RejectionReason.WRONG_DOCUMENT,
                detail=f"element {element_id} belongs to {element.doc_id},"
                f" not {document.doc_id}",
            )
        if derive_element_id(element.type, element.span) != element_id:
            return Rejection(
                reason=RejectionReason.ELEMENT_ID_MISMATCH,
                detail=f"element {element_id} does not match its type and span",
            )
        return element.span
    return Rejection(
        reason=RejectionReason.UNKNOWN_ELEMENT,
        detail=f"no element {element_id!r} in {document.doc_id}",
    )
```

with:

```python
    Only a genuine element resolves, wherever it sits in ``elements``. When none has
    the ID, the pointer is invalid with a recorded reason (R5.1, V9), from the first
    element that has it: another version's is ``wrong_document``, and a tampered
    one ``element_id_mismatch``. With no such element, it is ``unknown_element``.
    """
    problem = document_integrity_problem(document)
    if problem is not None:
        return Rejection(reason=RejectionReason.DOCUMENT_INTEGRITY, detail=problem)
    named = [element for element in elements if element.element_id == element_id]
    for element in named:
        if is_genuine(document, element):
            return element.span
    if not named:
        return Rejection(
            reason=RejectionReason.UNKNOWN_ELEMENT,
            detail=f"no element {element_id!r} in {document.doc_id}",
        )
    first = named[0]
    if first.doc_id != document.doc_id:
        return Rejection(
            reason=RejectionReason.WRONG_DOCUMENT,
            detail=f"element {element_id} belongs to {first.doc_id},"
            f" not {document.doc_id}",
        )
    return Rejection(
        reason=RejectionReason.ELEMENT_ID_MISMATCH,
        detail=f"element {element_id} does not match its type and span",
    )


def is_genuine(document: CanonicalDocument, element: DocumentElement) -> bool:
    """An element of this document version whose ID still matches its type and span."""
    return element.doc_id == document.doc_id and element.element_id == (
        derive_element_id(element.type, element.span)
    )
```

`evidence.py` uses the one predicate (P11-6):

In `packages/earnings-core/src/earnings_core/evidence.py`, replace:

```python
from earnings_core.elements import (
    DocumentElement,
    ElementType,
    TextOrigin,
    derive_element_id,
)
from earnings_core.hashing import Sha256Hex
from earnings_core.locators import SpanLocator, occurrences
from earnings_core.rejections import VALIDATOR_VERSION, Rejection, RejectionReason
from earnings_core.spans import TextSpan
```

with:

```python
from earnings_core.elements import DocumentElement, ElementType, TextOrigin
from earnings_core.hashing import Sha256Hex
from earnings_core.locators import SpanLocator, occurrences
from earnings_core.rejections import VALIDATOR_VERSION, Rejection, RejectionReason
from earnings_core.spans import TextSpan
from earnings_core.structure import is_genuine
```

In `packages/earnings-core/src/earnings_core/evidence.py`, replace:

```python
def _genuine(document: CanonicalDocument, element: DocumentElement) -> bool:
    """An element of this document version whose ID still matches its type and span."""
    return element.doc_id == document.doc_id and element.element_id == (
        derive_element_id(element.type, element.span)
    )


def _element(
```

with:

```python
def _element(
```

In `packages/earnings-core/src/earnings_core/evidence.py`, replace:

```python
        if element.element_id == element_id and _genuine(document, element):
```

with:

```python
        if element.element_id == element_id and is_genuine(document, element):
```

In `packages/earnings-core/src/earnings_core/evidence.py`, replace:

```python
        if element.type is ElementType.SPEAKER_TURN and _genuine(document, element)
```

with:

```python
        if element.type is ElementType.SPEAKER_TURN and is_genuine(document, element)
```

In `packages/earnings-core/src/earnings_core/evidence.py`, replace:

```python
        if element.text_origin is TextOrigin.OCR and _genuine(document, element)
```

with:

```python
        if element.text_origin is TextOrigin.OCR and is_genuine(document, element)
```

In `packages/earnings-core/src/earnings_core/rejections.py`, replace:

```python
VALIDATOR_VERSION = "2"
"""Bump when any check changes: caches key on the verifier version (R14.6).

Version 2 (Stage 3) added the OCR refusal, reports every crossing pair, and rechecks
the element invariants that construction checks and ``model_copy`` skips.
"""
```

with:

```python
VALIDATOR_VERSION = "3"
"""Bump when any check changes: caches key on the verifier version (R14.6).

Version 2 (Stage 3) added the OCR refusal, reports every crossing pair, and rechecks
the element invariants that construction checks and ``model_copy`` skips. Version 3
(Stage 7) changed two outcomes: ``validate_span`` refuses an offset that is not an
``int``, or is a ``bool``, as ``malformed_record``, where it raised; and
``resolve_pointer`` resolves this version's genuine element wherever it sits in the
list, where a stale or tampered element listed first with its ID was refused.
"""
```

- [ ] **Step 4: Run them to see them pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests tests/contracts/test_data_dictionary.py -q
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
```

Expected: `354 passed`; then `1745 passed, 8 skipped, 24 deselected`. No committed
record stores the validator version (ES4), so none changes.

- [ ] **Step 5: Lint, and the escape check**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' packages/earnings-core/src/earnings_core/structure.py packages/earnings-core/src/earnings_core/evidence.py packages/earnings-core/src/earnings_core/rejections.py packages/earnings-core/tests/test_structure.py packages/earnings-core/tests/test_public_api.py
```

Expected: `All checks passed!`, `297 files already formatted`, and `escapes intact`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-core/src/earnings_core/structure.py packages/earnings-core/src/earnings_core/evidence.py packages/earnings-core/src/earnings_core/rejections.py packages/earnings-core/tests/test_structure.py packages/earnings-core/tests/test_public_api.py docs/data-dictionary.md
git commit -m "fix(core): resolve the genuine element wherever it sits; validator 3 (plan 11, ES4)"
git status --short
```

Expected: `git status --short` prints nothing.

### Task 5: One `canonical_json` and `digest`, in `earnings-core` (ES7, M6)

**Files:**
- Create: `packages/earnings-core/src/earnings_core/digests.py`, `packages/earnings-core/tests/test_digests.py`
- Modify: `packages/earnings-core/src/earnings_core/__init__.py:8`, and `__all__`
- Delete: `packages/earnings-ingestion/src/earnings_ingestion/cohort/digests.py`, `packages/earnings-ingestion/tests/test_cohort_digests.py`
- Modify, in `packages/earnings-ingestion/src/earnings_ingestion/`:
  - `cohort/build.py:18-36`;
  - `cohort/config.py:20-33`;
  - `cohort/findings.py:11`;
  - `cohort/identity.py:28`;
  - `cohort/locators.py:22-29`;
  - `cohort/register.py:18-23`;
  - `cohort/synthetic.py:23-26`;
  - `events/coverage.py:24-35`;
  - `events/pilot.py:52-54`;
  - `events/records.py:38-52`.
- Modify: `packages/earnings-ingestion/tests/test_cohort_findings.py:6`
- Modify: `packages/earnings-themes/src/earnings_themes/records.py:5-19`, `:69-91`, and `__all__`; `split.py:26-38`; `codebook.py:24`, `:37`
- Modify: `docs/data-dictionary.md:605-607` (the cohort's canonical JSON bullet)
- Test: `packages/earnings-core/tests/test_public_api.py`

**Interfaces:**
- Consumes: `sha256_hex` in `earnings_core.hashing`.
- Produces: `canonical_json(value: object) -> bytes` and `digest(value: object) -> str`,
  exported from `earnings_core`. Plan B's records hash through them, as every
  committed record's content hash already does.

The functions move verbatim (P11-7), so every content hash is the same.

- [ ] **Step 1: Write the moved tests**

The expectations are unchanged. A local enum and a core model stand in for the
cohort's (P11-7). The non-ASCII text is built from code points.

Create `packages/earnings-core/tests/test_digests.py`:

```python
"""Canonical JSON: the one serialization every record hash is computed over (ES7).

Moved from earnings-ingestion's cohort tests with their expectations unchanged. A
local enum and a core model stand in for the cohort's, since core's tests import no
sibling package.
"""

from datetime import UTC, date, datetime
from enum import StrEnum

import pytest
from earnings_core import SpanLocator, canonical_json, digest, sha256_hex


class Action(StrEnum):
    ADDED = "added"


def test_keys_are_sorted_without_whitespace_and_text_stays_utf8() -> None:
    value = {"b": [1, 2], "a": "Soci" + chr(0xE9) + "t" + chr(0xE9)}
    expected = '{"a":"Soci' + chr(0xE9) + "t" + chr(0xE9) + '","b":[1,2]}'
    assert canonical_json(value) == expected.encode("utf-8")
    assert digest(value) == sha256_hex(expected.encode("utf-8"))


def test_dates_and_enums_are_written_as_iso_text_and_values() -> None:
    value = {
        "on": date(2024, 11, 8),
        "at": datetime(2024, 11, 1, 21, 0, tzinfo=UTC),
        "action": Action.ADDED,
    }
    assert canonical_json(value) == (
        b'{"action":"added","at":"2024-11-01T21:00:00+00:00","on":"2024-11-08"}'
    )


def test_a_model_is_dumped_in_json_mode_first() -> None:
    locator = SpanLocator(exact="caf" + chr(0xE9), prefix="the ", suffix=" line")
    assert canonical_json(locator) == canonical_json(locator.model_dump(mode="json"))


def test_a_value_without_a_json_form_is_refused() -> None:
    with pytest.raises(TypeError, match="no canonical JSON form"):
        canonical_json({"x": {1, 2}})
```

In `packages/earnings-core/tests/test_public_api.py`, replace:

```python
    "apply_masks",
    "derive_doc_id",
    "derive_element_id",
    "document_integrity_problem",
```

with:

```python
    "apply_masks",
    "canonical_json",
    "derive_doc_id",
    "derive_element_id",
    "digest",
    "document_integrity_problem",
```

- [ ] **Step 2: Run them to see them fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests -q
```

Expected: the run stops at collection with `1 error`. `test_digests.py` cannot
import `canonical_json` from `earnings_core`.

- [ ] **Step 3: Move the module into core, and export it**

Create `packages/earnings-core/src/earnings_core/digests.py`:

```python
"""Canonical JSON and its SHA-256, the one serialization every record hash uses.

Keys are sorted, separators carry no whitespace, and non-ASCII characters are
written as themselves in UTF-8. Dates and datetimes are ISO 8601 strings. A hash
computed here is reproducible from the committed values alone. Moved unchanged from
earnings-ingestion's cohort, so earnings-themes imports the same definition (ES7).
"""

import json
from datetime import date

from pydantic import BaseModel

from earnings_core.hashing import sha256_hex


def _default(value: object) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"{type(value).__name__} has no canonical JSON form")


def canonical_json(value: object) -> bytes:
    """``value`` as canonical JSON bytes; a model is dumped in JSON mode first."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    text = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_default,
    )
    return text.encode("utf-8")


def digest(value: object) -> str:
    """SHA-256 of ``value``'s canonical JSON."""
    return sha256_hex(canonical_json(value))
```

In `packages/earnings-core/src/earnings_core/__init__.py`, replace:

```python
from earnings_core.chunks import TextChunk
```

with:

```python
from earnings_core.chunks import TextChunk
from earnings_core.digests import canonical_json, digest
```

In `packages/earnings-core/src/earnings_core/__init__.py`, replace:

```python
    "apply_masks",
    "derive_doc_id",
    "derive_element_id",
    "document_integrity_problem",
```

with:

```python
    "apply_masks",
    "canonical_json",
    "derive_doc_id",
    "derive_element_id",
    "digest",
    "document_integrity_problem",
```

- [ ] **Step 4: Run core's tests**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests -q
```

Expected: `202 passed`.

- [ ] **Step 5: Point ingestion at the core definition, and delete its copy**

In `packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py`, replace:

```python
from pathlib import Path

from earnings_ingestion.cohort.config import (
```

with:

```python
from pathlib import Path

from earnings_core import digest

from earnings_ingestion.cohort.config import (
```

In `packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py`, replace:

```python
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.findings import acknowledge, make_finding
```

with:

```python
from earnings_ingestion.cohort.findings import acknowledge, make_finding
```

In `packages/earnings-ingestion/src/earnings_ingestion/cohort/config.py`, replace:

```python
import tomllib
from earnings_core.artifacts import NonBlankStr
```

with:

```python
import tomllib
from earnings_core import canonical_json
from earnings_core.artifacts import NonBlankStr
```

In `packages/earnings-ingestion/src/earnings_ingestion/cohort/config.py`, replace:

```python
from earnings_ingestion.cohort.digests import canonical_json
from earnings_ingestion.cohort.records import BoundTiming, Override, OverrideKind
```

with:

```python
from earnings_ingestion.cohort.records import BoundTiming, Override, OverrideKind
```

In `packages/earnings-ingestion/src/earnings_ingestion/cohort/findings.py`, replace:

```python
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import (
```

with:

```python
from earnings_core import digest

from earnings_ingestion.cohort.records import (
```

In `packages/earnings-ingestion/src/earnings_ingestion/cohort/identity.py`, replace:

```python
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import UniverseManifest
```

with:

```python
from earnings_core import digest

from earnings_ingestion.cohort.records import UniverseManifest
```

In `packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py`, replace:

```python
from earnings_core import ArtifactRef, hash_canonical_text, sha256_hex
```

with:

```python
from earnings_core import ArtifactRef, canonical_json, hash_canonical_text, sha256_hex
```

In `packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py`, replace:

```python
from earnings_ingestion.cohort.digests import canonical_json
from earnings_ingestion.cohort.pdftext import PDFTEXT_VERSION, PdfTextError, pdf_text
```

with:

```python
from earnings_ingestion.cohort.pdftext import PDFTEXT_VERSION, PdfTextError, pdf_text
```

In `packages/earnings-ingestion/src/earnings_ingestion/cohort/register.py`, replace:

```python
from earnings_core import RightsStatus
from earnings_core.artifacts import NonBlankStr
from earnings_core.hashing import Sha256Hex
from pydantic import BaseModel, ConfigDict, model_validator

from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import EvidenceClass, SourceRights, SourceRole
```

with:

```python
from earnings_core import RightsStatus, digest
from earnings_core.artifacts import NonBlankStr
from earnings_core.hashing import Sha256Hex
from pydantic import BaseModel, ConfigDict, model_validator

from earnings_ingestion.cohort.records import EvidenceClass, SourceRights, SourceRole
```

In `packages/earnings-ingestion/src/earnings_ingestion/cohort/synthetic.py`, replace:

```python
from earnings_core import RightsStatus, sha256_hex

from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.digests import canonical_json
from earnings_ingestion.cohort.freeze import freeze
```

with:

```python
from earnings_core import RightsStatus, canonical_json, sha256_hex

from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.freeze import freeze
```

In `packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py`, replace:

```python
from earnings_core.documents import IdPart
```

with:

```python
from earnings_core import digest
from earnings_core.documents import IdPart
```

In `packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py`, replace:

```python
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.identity import operative_hash
```

with:

```python
from earnings_ingestion.cohort.identity import operative_hash
```

In `packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py`, replace:

```python
from earnings_core import sha256_hex

from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.freeze import repeated_content
```

with:

```python
from earnings_core import digest, sha256_hex

from earnings_ingestion.cohort.freeze import repeated_content
```

In `packages/earnings-ingestion/src/earnings_ingestion/events/records.py`, replace:

```python
from earnings_core.artifacts import NonBlankStr
from earnings_core.documents import IdPart
```

with:

```python
from earnings_core import digest
from earnings_core.artifacts import NonBlankStr
from earnings_core.documents import IdPart
```

In `packages/earnings-ingestion/src/earnings_ingestion/events/records.py`, replace:

```python
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import Citation, OverrideCitation
```

with:

```python
from earnings_ingestion.cohort.records import Citation, OverrideCitation
```

In `packages/earnings-ingestion/tests/test_cohort_findings.py`, replace:

```python
from earnings_ingestion.cohort.digests import digest
```

with:

```python
from earnings_core import digest
```

Then delete the module and its tests, which Step 1 moved:

```bash
git rm packages/earnings-ingestion/src/earnings_ingestion/cohort/digests.py packages/earnings-ingestion/tests/test_cohort_digests.py
```

Expected: two `rm '...'` lines.

- [ ] **Step 6: Point themes at the core definition, and drop its copies**

In `packages/earnings-themes/src/earnings_themes/records.py`, replace:

```python
  sorted keys, no whitespace, UTF-8. earnings-themes imports only earnings-core, so
  ``canonical_json`` repeats ``earnings_ingestion.cohort.digests``'s form rather than
  importing it.
```

with:

```python
  sorted keys, no whitespace, UTF-8. ``canonical_json`` and ``digest`` are
  earnings-core's, the one definition earnings-ingestion uses too (ES7).
```

In `packages/earnings-themes/src/earnings_themes/records.py`, replace:

```python
import json
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from earnings_core import sha256_hex
```

with:

```python
import json
from pathlib import Path
from typing import Annotated, Literal

from earnings_core import canonical_json
```

In `packages/earnings-themes/src/earnings_themes/records.py`, replace:

```python
def _default(value: object) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"{type(value).__name__} has no canonical JSON form")


def canonical_json(value: object) -> bytes:
    """``value`` as canonical JSON bytes; a model is dumped in JSON mode first."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    text = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_default,
    )
    return text.encode("utf-8")


def digest(value: object) -> str:
    """SHA-256 of ``value``'s canonical JSON."""
    return sha256_hex(canonical_json(value))


def record_json(record: BaseModel) -> bytes:
```

with:

```python
def record_json(record: BaseModel) -> bytes:
```

In `packages/earnings-themes/src/earnings_themes/records.py`, replace:

```python
    "ThemesRecord",
    "canonical_json",
    "describe",
    "digest",
    "parse",
```

with:

```python
    "ThemesRecord",
    "describe",
    "parse",
```

In `packages/earnings-themes/src/earnings_themes/split.py`, replace:

```python
from pydantic import PositiveInt, StringConstraints, model_validator

from earnings_themes.records import (
    IdPart,
    Part,
    Pin,
    RecordError,
    Sha256Hex,
    ThemesRecord,
    digest,
    parse,
    read_json,
)
```

with:

```python
from earnings_core import digest
from pydantic import PositiveInt, StringConstraints, model_validator

from earnings_themes.records import (
    IdPart,
    Part,
    Pin,
    RecordError,
    Sha256Hex,
    ThemesRecord,
    parse,
    read_json,
)
```

In `packages/earnings-themes/src/earnings_themes/codebook.py`, replace:

```python
from earnings_core import RejectionReason
```

with:

```python
from earnings_core import RejectionReason, digest
```

In `packages/earnings-themes/src/earnings_themes/codebook.py`, replace:

```python
    ThemesRecord,
    digest,
    parse,
)
```

with:

```python
    ThemesRecord,
    parse,
)
```

In `docs/data-dictionary.md`, replace:

```markdown
- **Canonical JSON.** Every cohort hash is SHA-256 over canonical JSON
  (`earnings_ingestion.cohort.digests`): sorted keys, separators without whitespace,
  UTF-8 with non-ASCII characters written as themselves, and dates in ISO 8601.
```

with:

```markdown
- **Canonical JSON.** Every cohort hash is SHA-256 over canonical JSON
  (`earnings_core.canonical_json` and `earnings_core.digest`, which every record
  hash uses): sorted keys, separators without whitespace, UTF-8 with non-ASCII
  characters written as themselves, and dates in ISO 8601.
```

- [ ] **Step 7: Run the suite, and check that one definition is left**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
git grep --untracked -n -e "def canonical_json" -e "def digest(" -- "*.py"
git grep --untracked -n "cohort.digests" -- "*.py" "docs/*.md"
```

Expected: `1745 passed, 8 skipped, 24 deselected`, since the 4 moved tests left
ingestion and joined core. The first `git grep` prints exactly:

```text
packages/earnings-core/src/earnings_core/digests.py:23:def canonical_json(value: object) -> bytes:
packages/earnings-core/src/earnings_core/digests.py:37:def digest(value: object) -> str:
```

The second prints nothing. The suite's record tests reran every content hash through
the moved functions (The proof's map), so their passing is the move's byte proof.

- [ ] **Step 8: Lint, and the escape check**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' packages/earnings-core/src/earnings_core/digests.py packages/earnings-core/src/earnings_core/__init__.py packages/earnings-core/tests/test_digests.py packages/earnings-core/tests/test_public_api.py packages/earnings-themes/src/earnings_themes/records.py packages/earnings-themes/src/earnings_themes/split.py packages/earnings-themes/src/earnings_themes/codebook.py
```

Expected: `All checks passed!`, `297 files already formatted`, and `escapes intact`.
The file count is unchanged: two files arrive in core, and two leave ingestion.

- [ ] **Step 9: Commit**

```bash
git log --oneline -3
git add packages/earnings-core/src/earnings_core/digests.py packages/earnings-core/src/earnings_core/__init__.py packages/earnings-core/tests/test_digests.py packages/earnings-core/tests/test_public_api.py packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py packages/earnings-ingestion/src/earnings_ingestion/cohort/config.py packages/earnings-ingestion/src/earnings_ingestion/cohort/findings.py packages/earnings-ingestion/src/earnings_ingestion/cohort/identity.py packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py packages/earnings-ingestion/src/earnings_ingestion/cohort/register.py packages/earnings-ingestion/src/earnings_ingestion/cohort/synthetic.py packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py packages/earnings-ingestion/src/earnings_ingestion/events/records.py packages/earnings-ingestion/tests/test_cohort_findings.py packages/earnings-themes/src/earnings_themes/records.py packages/earnings-themes/src/earnings_themes/split.py packages/earnings-themes/src/earnings_themes/codebook.py docs/data-dictionary.md
git commit -m "refactor(core): one canonical_json and digest, in earnings-core (plan 11, ES7)"
git status --short
```

Expected: the commit holds the two deletions that Step 5 staged, and
`git status --short` prints nothing.

### Task 6: `context_hash`'s known answer (ES8, T6-M3)

**Files:**
- Create: `/tmp/plan11-context-hash.py`, never committed
- Modify: `packages/earnings-themes/tests/test_anchoring.py:5-8` (imports), and its end (the generated test)
- Modify: `packages/earnings-themes/src/earnings_themes/anchoring.py:94-97` (`context_hash`'s docstring)
- Modify: `docs/data-dictionary.md:1824` (`context_sha256`)

**Interfaces:**
- Consumes: `context_hash(prefix: str, suffix: str) -> str` in
  `earnings_themes.anchoring`, unchanged; and `sha256_hex` from `earnings_core`.
- Produces: `test_context_hash_is_the_sha256_of_a_compact_utf8_json_pair`, last in
  `test_anchoring.py`. It pins the byte format of every committed `context_sha256`.
  Task 7 edits the imports as this task leaves them.

The test is written by a generator, never by hand (P11-8). Never type its literals,
and never edit them afterwards. To write the test again, restore
`test_anchoring.py` with `git restore`, which undoes Step 1's uncommitted edit too;
reapply Step 1's edit; then rerun Steps 3 and 4.

- [ ] **Step 1: The imports the generated test needs**

In `packages/earnings-themes/tests/test_anchoring.py`, replace:

```python
from collections import Counter

import pytest
from earnings_core import RejectionReason, TextSpan, make_locator
```

with:

```python
import json
from collections import Counter

import pytest
from earnings_core import RejectionReason, TextSpan, make_locator, sha256_hex
```

- [ ] **Step 2: Write the generator**

Create `/tmp/plan11-context-hash.py`:

```python
"""Plan 11, Task 6 (T6-M3, ES8): append context_hash's known-answer test.

The pair holds a non-ASCII character, a double quote, and a backslash. Each is built
here from its code point and written into the test as escape text by ``ascii``, so
no tool can normalize it. The bytes and the hash come from the spec's formula, never
from ``context_hash``, which the test then holds to them.

usage: uv run --locked python /tmp/plan11-context-hash.py
"""

import hashlib
import json
from pathlib import Path

TEST = Path("packages/earnings-themes/tests/test_anchoring.py")
NAME = "test_context_hash_is_the_sha256_of_a_compact_utf8_json_pair"
E_ACUTE, QUOTE, BACKSLASH = chr(0xE9), chr(0x22), chr(0x5C)

prefix = "the caf" + E_ACUTE + " line, " + QUOTE + "net" + QUOTE + " "
suffix = " under C:" + BACKSLASH + "notes"
data = json.dumps([prefix, suffix], ensure_ascii=False, separators=(",", ":")).encode(
    "utf-8"
)
expected = hashlib.sha256(data).hexdigest()

BODY = '''

def {name}() -> None:
    """T6-M3 (ES8): the byte format the three signed bundles and the curated hard
    negatives store. The pair holds a non-ASCII character, a double quote, and a
    backslash, so ``ensure_ascii=False``, the escaping, and the separators all
    show; an ASCII-only pair could not show the first. Plan 11's Task 6 wrote
    these literals as escape text, from code points."""
    prefix = {prefix}
    suffix = {suffix}
    pair = {pair}
    expected = "{expected}"
    assert context_hash(prefix, suffix) == expected
    assert sha256_hex(pair) == expected
    escaped = json.dumps([prefix, suffix], separators=(",", ":")).encode("ascii")
    assert escaped != pair
'''

source = TEST.read_text(encoding="utf-8")
if NAME in source:
    raise SystemExit(f"{TEST} already holds {NAME}")
body = BODY.format(
    name=NAME,
    prefix=ascii(prefix),
    suffix=ascii(suffix),
    pair=ascii(data),
    expected=expected,
)
TEST.write_text(source + body, encoding="utf-8")
print(expected)
```

- [ ] **Step 3: Generate the test, and format it**

```bash
uv run --locked python /tmp/plan11-context-hash.py
uv run --locked ruff format packages/earnings-themes/tests/test_anchoring.py
```

Expected: `fd4874e7855a8b8d6c9df217cca901d75d1129624089f94a6db6cda22ef52280`, then
`1 file reformatted`, since Ruff puts the suffix's literal in double quotes. If the
generator prints `already holds`, the test exists: go to Step 4.

- [ ] **Step 4: Run it**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_anchoring.py -q
```

Expected: `19 passed`. It passes at once, since it pins today's behavior (ES8).

- [ ] **Step 5: Show that the pin can fail, then restore it**

```bash
sed -i '' 's/ensure_ascii=False, separators/ensure_ascii=True, separators/' packages/earnings-themes/src/earnings_themes/anchoring.py
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_anchoring.py -q
sed -i '' 's/ensure_ascii=True, separators/ensure_ascii=False, separators/' packages/earnings-themes/src/earnings_themes/anchoring.py
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_anchoring.py -q
git diff --quiet -- packages/earnings-themes/src/earnings_themes/anchoring.py && echo "anchoring.py unchanged"
```

Expected: `1 failed, 18 passed`; then `19 passed`; then `anchoring.py unchanged`.

- [ ] **Step 6: Document the format**

In `packages/earnings-themes/src/earnings_themes/anchoring.py`, replace:

```python
    """The SHA-256 of a locator's prefix and suffix, as a two-item JSON array."""
```

with:

```python
    """The SHA-256 of a locator's prefix and suffix, as a compact two-item JSON array
    in UTF-8 with ``ensure_ascii=False``: the byte format the committed gold stores,
    which a known-answer test pins (T6-M3)."""
```

In `docs/data-dictionary.md`, replace:

```markdown
| `context_sha256` | 64 lowercase hex or null | When the text repeats: SHA-256 of `make_locator`'s prefix and suffix, as a compact JSON pair |
```

with:

```markdown
| `context_sha256` | 64 lowercase hex or null | When the text repeats: SHA-256 of `make_locator`'s prefix and suffix as a compact JSON pair in UTF-8, `json.dumps([prefix, suffix], ensure_ascii=False, separators=(",", ":"))` |
```

- [ ] **Step 7: The suite, lint, and the escape check**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' packages/earnings-themes/tests/test_anchoring.py packages/earnings-themes/src/earnings_themes/anchoring.py
```

Expected: `1746 passed, 8 skipped, 24 deselected`; `All checks passed!` and
`297 files already formatted`; and `escapes intact`, which shows that the test's
literals are escape text.

- [ ] **Step 8: Commit**

```bash
git log --oneline -3
git add packages/earnings-themes/tests/test_anchoring.py packages/earnings-themes/src/earnings_themes/anchoring.py docs/data-dictionary.md
git commit -m "test(themes): pin context_hash's byte format (plan 11, ES8)"
git status --short
```

Expected: `git status --short` prints nothing.

### Task 7: The narrative rule: a transparent container (ES9, T6-M1)

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/anchoring.py:1-17` (the module docstring), `:119-130` (`_outside_narrative`, `_home`), `:177` (`anchor`), `:207-213` (`check_pointer`)
- Modify: `docs/data-dictionary.md:1714` (`not_narrative`)
- Modify: `docs/verification/pilot-v1-gold-set.md:235-237` (one bullet appended under M5)
- Test: `packages/earnings-themes/tests/test_anchoring.py`

**Interfaces:**
- Consumes:
  - from `earnings_themes.anchoring`: `Bundle(name, document, elements, masks)`,
    `NARRATIVE`, `bundle_problems`, `anchor`, `check_pointer`, and `SpanPointer`;
  - `CanonicalDocument.create(source_document_id=, canonicalization_version=, canonical_text=)`;
  - `DocumentElement.create(document, type, span, *, level=None, parent_id=None)`;
  - the fixture `fixtures` in `packages/earnings-themes/tests/conftest.py`: Stage 1's
    eight bundles by name;
  - the imports as Task 6 leaves them.
- Produces:
  - `narrative_home(bundle: Bundle, span: TextSpan) -> DocumentElement | str`,
    public in `earnings_themes.anchoring`. It returns the most specific narrative
    element that holds `span`, or `"not_narrative"`, or `"outside_element"`. Plan B's
    units are the elements that are their own `narrative_home`.
  - `_transparent(element, elements, text) -> bool`, which stays private.

- [ ] **Step 1: Write the failing tests, and document the exception**

In `packages/earnings-themes/tests/test_anchoring.py`, replace:

```python
from earnings_core import RejectionReason, TextSpan, make_locator, sha256_hex
from earnings_themes.anchoring import (
    SpanPointer,
    anchor,
    bundle_problems,
    check_pointer,
    context_hash,
    mask_id,
    quote_hash,
)
```

with:

```python
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    RejectionReason,
    TextSpan,
    make_locator,
    sha256_hex,
)
from earnings_themes.anchoring import (
    Bundle,
    SpanPointer,
    anchor,
    bundle_problems,
    check_pointer,
    context_hash,
    mask_id,
    narrative_home,
    quote_hash,
)
```

The test document is invented. A container blocks once it holds text of its own, and
a 4-character `other` div still blocks, as the spec's §The narrative rule asks:

In `packages/earnings-themes/tests/test_anchoring.py`, replace:

```python
def test_the_synthetic_bundle_is_sound(synthetic) -> None:
    assert bundle_problems(synthetic.bundle) == []
```

with:

```python
def test_the_synthetic_bundle_is_sound(synthetic) -> None:
    assert bundle_problems(synthetic.bundle) == []


def list_bundle(lead: str) -> Bundle:
    """Invented text: a heading; a list container of type ``other``, as walker-1
    makes one (W7), whose two list items hold one sentence each, with ``lead`` as
    the container's own text before its first item; and a 4-character ``other``
    div."""
    text = f"Outlook\n{lead}Sales rose.\nCosts fell.\nNote\n"
    document = CanonicalDocument.create(
        source_document_id="0009990001-25-000002_ex991.htm",
        canonicalization_version="walker-1",
        canonical_text=text,
    )

    def span(needle: str) -> TextSpan:
        start = text.index(needle)
        return TextSpan(start=start, end=start + len(needle))

    first, second = span("Sales rose."), span("Costs fell.")
    container = DocumentElement.create(
        document,
        ElementType.OTHER,
        TextSpan(start=first.start - len(lead), end=second.end),
    )
    elements = [
        DocumentElement.create(document, ElementType.HEADING, span("Outlook"), level=1),
        container,
    ]
    for item_span in (first, second):
        item = DocumentElement.create(
            document, ElementType.LIST_ITEM, item_span, parent_id=container.element_id
        )
        sentence = DocumentElement.create(
            document, ElementType.SENTENCE, item_span, parent_id=item.element_id
        )
        elements += [item, sentence]
    elements.append(DocumentElement.create(document, ElementType.OTHER, span("Note")))
    return Bundle("synthetic-list", document, tuple(elements), ())


def test_only_a_container_whose_children_hold_its_text_is_transparent() -> None:
    """ES9 (T6-M1): an ``other`` element with children and no non-space character
    outside them is a transparent container. It no longer blocks a quote, and it is
    never a quote's home. An ``other`` element with text of its own still blocks,
    and so does a container with text outside its children."""
    bundle = list_bundle("")
    assert bundle_problems(bundle) == []
    sentence = next(e for e in bundle.elements if e.type is ElementType.SENTENCE)
    pointer = anchor(bundle, "Sales rose.")
    assert isinstance(pointer, SpanPointer)
    assert pointer.element_id == sentence.element_id
    assert narrative_home(bundle, sentence.span) == sentence
    assert check_pointer(bundle, pointer) == []
    container = next(e for e in bundle.elements if e.type is ElementType.OTHER)
    named = SpanPointer(**{**pointer.model_dump(), "element_id": container.element_id})
    assert check_pointer(bundle, named) == ["not_narrative"]
    assert anchor(bundle, "Sales rose.\nCosts fell.") == "outside_element"
    assert anchor(bundle, "Note") == "not_narrative"

    led = list_bundle("Also: ")
    assert bundle_problems(led) == []
    assert anchor(led, "Sales rose.") == "not_narrative"
```

The fixture pin moves to 660/26/0, and each of the 10 sentences anchors to itself:

In `packages/earnings-themes/tests/test_anchoring.py`, replace:

```python
    """Each of the 686 sentences of Stage 1's fixtures anchors to itself, or is
    refused: 26 repeat, so need context, and 10 sit in a list item under an
    ``other`` element, all in one fixture, so are not narrative (T6-M1). Plan 10
    pins these counts (T6-M2), and calibrates its count over the pilot on the 10."""
```

with:

```python
    """Each of the 686 sentences of Stage 1's fixtures anchors to itself, or is
    refused because its text repeats: 26 do, so need context. The 10 that sit in a
    list item under an ``other`` element, all in one fixture, anchor, since that
    element is a transparent container (ES9). Plan 10 pinned 650 anchored, 26
    repeated, and those 10 not narrative (T6-M2); plan 11 moves the 10."""
```

In `packages/earnings-themes/tests/test_anchoring.py`, replace:

```python
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

with:

```python
            pointer = anchor(bundle, exact)
            verdict = pointer if isinstance(pointer, str) else "anchored"
            if not isinstance(pointer, str):
                assert pointer.element_id == element.element_id
                assert check_pointer(bundle, pointer) == []
            verdicts[verdict] += 1
            if any(item.span.contains(element.span) for item in items):
                under_other[f"{name}: {verdict}"] += 1
    assert verdicts == {"anchored": 660, "ambiguous_occurrence": 26}
    assert verdicts["not_narrative"] == 0
    assert under_other == {"0000949699-08-000023_ex-99-1: anchored": 10}
```

In `docs/data-dictionary.md`, replace:

```markdown
| `not_narrative` | A quote overlaps a table, cell, page artifact, or other non-narrative element (GS15) |
```

with:

```markdown
| `not_narrative` | A quote overlaps a table, cell, page artifact, or other non-narrative element (GS15), other than a transparent container: an `other` element whose children hold every non-space character of its span (ES9) |
```

- [ ] **Step 2: Run them to see them fail**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_anchoring.py -q
```

Expected: the run stops at collection with `1 error`. `test_anchoring.py` cannot
import `narrative_home`, which does not exist yet.

- [ ] **Step 3: The rule, and `narrative_home`**

In `packages/earnings-themes/src/earnings_themes/anchoring.py`, replace:

```python
  the text repeats. The text must occur exactly once with that context. Its span is
  attributed to the most specific narrative element that holds it, and the span is
  then built through ``parse_span_candidate`` and checked by ``validate_span``: code
  is the authority on exactness, and no offset comes from a browser.
- **Narrative only.** A quote never overlaps a ``table``, ``table_cell``,
  ``page_artifact``, or ``other`` element (R4.2, GS15). A quote under a boilerplate
  mask is allowed, and its masks are recorded.
```

with:

```python
  the text repeats. The text must occur exactly once with that context. Its span is
  attributed to ``narrative_home``, the most specific narrative element that holds
  it, and the span is then built through ``parse_span_candidate`` and checked by
  ``validate_span``: code is the authority on exactness, and no offset comes from a
  browser.
- **Narrative only.** A quote never overlaps a ``table``, ``table_cell``,
  ``page_artifact``, or ``other`` element (R4.2, GS15), except a transparent
  container: an ``other`` element with children and no non-space character outside
  them, which walker-1 makes from a list (ES9). A quote under a boilerplate mask is
  allowed, and its masks are recorded.
```

In `packages/earnings-themes/src/earnings_themes/anchoring.py`, replace:

```python
def _outside_narrative(elements: list[DocumentElement], span: TextSpan) -> bool:
    return any(e.type not in NARRATIVE and e.span.overlaps(span) for e in elements)


def _home(bundle: Bundle, span: TextSpan) -> DocumentElement | str:
    elements = _genuine(bundle)
    if _outside_narrative(elements, span):
        return Problem.NOT_NARRATIVE.value
```

with:

```python
def _transparent(
    element: DocumentElement, elements: list[DocumentElement], text: str
) -> bool:
    """An ``other`` element with at least one child and no non-space character of
    its span outside its children's spans (ES9)."""
    if element.type is not ElementType.OTHER:
        return False
    children = sorted(
        (e for e in elements if e.parent_id == element.element_id),
        key=lambda e: e.span.start,
    )
    if not children:
        return False
    own, position = [], element.span.start
    for child in children:
        own.append(text[position : child.span.start])
        position = max(position, child.span.end)
    own.append(text[position : element.span.end])
    return not "".join(own).strip()


def _outside_narrative(
    elements: list[DocumentElement], span: TextSpan, text: str
) -> bool:
    return any(
        e.type not in NARRATIVE
        and e.span.overlaps(span)
        and not _transparent(e, elements, text)
        for e in elements
    )


def narrative_home(bundle: Bundle, span: TextSpan) -> DocumentElement | str:
    """The most specific narrative element that holds ``span``, by P9-19's order:
    the shortest, then the earliest type in ``NARRATIVE``. Or why none does:
    ``not_narrative`` when a non-narrative element overlaps it, a transparent
    container excepted (ES9), and ``outside_element`` when no narrative element
    holds it whole."""
    elements = _genuine(bundle)
    if _outside_narrative(elements, span, bundle.document.canonical_text):
        return Problem.NOT_NARRATIVE.value
```

In `packages/earnings-themes/src/earnings_themes/anchoring.py`, replace:

```python
    span = TextSpan(start=starts[0], end=starts[0] + len(exact))
    home = _home(bundle, span)
```

with:

```python
    span = TextSpan(start=starts[0], end=starts[0] + len(exact))
    home = narrative_home(bundle, span)
```

In `packages/earnings-themes/src/earnings_themes/anchoring.py`, replace:

```python
    if any(e.type not in NARRATIVE for e in named) or _outside_narrative(
        elements, span
    ):
        reasons.append(Problem.NOT_NARRATIVE.value)
    home = _home(bundle, span)
```

with:

```python
    if any(e.type not in NARRATIVE for e in named) or _outside_narrative(
        elements, span, text
    ):
        reasons.append(Problem.NOT_NARRATIVE.value)
    home = narrative_home(bundle, span)
```

- [ ] **Step 4: Run them to see them pass**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests tests/contracts/test_data_dictionary.py tests/integration/test_stage6_records.py tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py apps/earnings-pipeline/tests/test_stage6_cli.py -q -rs
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
```

Expected: `287 passed, 4 skipped`, the skips being the local legs at
`test_stage6_pilot_v1.py:133` and `:164` (2) and `test_stage6_wording.py:93`. Then
`1747 passed, 8 skipped, 24 deselected`. The curated hard negatives still validate
offline over Stage 1's fixtures under the rule
(`test_the_curated_hard_negatives_validate_offline`).

- [ ] **Step 5: Record the rule under M5**

Counts and IDs only, never a sentence: the wording guard reads this file.

In `docs/verification/pilot-v1-gold-set.md`, replace:

```markdown
- **What follows.** No gold quote can rest on such a sentence until Stage 7 decides
  whether a list item under an `other` element becomes quotable
  (`specs/deferred_items.md`, T6-M1).
```

with:

```markdown
- **What follows.** No gold quote can rest on such a sentence until Stage 7 decides
  whether a list item under an `other` element becomes quotable
  (`specs/deferred_items.md`, T6-M1).
- **Stage 7's rule (plan 11).** An `other` element whose children hold every
  non-space character of its span is a transparent container, and no longer blocks
  a quote (ES9). In `0000949699-08-000023_ex-99-1`, `other-3292-5040` is one, so
  its 10 sentences now anchor: the test pins 660 anchored, 26 repeated, and 0 not
  narrative. No pilot verdict changed, since no pilot release holds such a sentence
  (0 of 5139).
```

```bash
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs
```

Expected: `4 passed, 1 skipped`. The fixture leg passes, and the pilot leg skips
without `data/`, and runs at the user's gate.

- [ ] **Step 6: Lint, and the escape check**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
python3 -c 'import sys; ok={chr(0xA7)}; bad=[n for n in sys.argv[1:] if any(ord(c)>127 and c not in ok for c in open(n,encoding="utf-8").read())]; print("\n".join(bad) or "escapes intact")' packages/earnings-themes/src/earnings_themes/anchoring.py packages/earnings-themes/tests/test_anchoring.py
```

Expected: `All checks passed!`, `297 files already formatted`, and `escapes intact`.

- [ ] **Step 7: Commit**

```bash
git log --oneline -3
git add packages/earnings-themes/src/earnings_themes/anchoring.py packages/earnings-themes/tests/test_anchoring.py docs/data-dictionary.md docs/verification/pilot-v1-gold-set.md
git commit -m "feat(themes): a transparent container no longer blocks a quote (plan 11, ES9)"
git status --short
```

Expected: `git status --short` prints nothing.

### Task 8: The proof, and the record (controller)

This is the spec's first gate for plan A (§Gates, plan A, gate 1), and it runs in the
controller session. Its record is what the user's gate completes.

**Files:**
- Create: `docs/verification/evidence-selection.md`

**Interfaces:**
- Consumes: Tasks 1 to 7, and The proof's map.
- Produces: the record's plan A section, whose `[GATE: ...]` marks Completion, Step 2
  fills.

- [ ] **Step 1: Run the proof's map by node ID**

```bash
uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_identity.py::test_v1_loads_unchanged_and_has_an_operative_hash tests/integration/test_cohort_fixtures.py::test_the_fixture_regenerates_byte_for_byte tests/integration/test_cohort_fixtures.py::test_saved_evidence_replays_to_the_frozen_manifest tests/integration/test_event_corpus_v1.py::test_events_v1_loads_unchanged_with_its_evidence_record tests/integration/test_event_corpus_v1.py::test_pilot_v1_loads_unchanged_and_djia_pilot_1_reselects_it tests/integration/test_event_fixtures.py::test_the_fixture_regenerates_byte_for_byte tests/integration/test_event_fixtures.py::test_p_vi_replays_offline_to_the_frozen_manifests tests/integration/test_event_fixtures.py::test_p_vi_replays_the_acquisition_offline tests/integration/test_stage6_pilot_v1.py::test_the_pin_is_pilot_v1_and_its_chain tests/integration/test_stage6_pilot_v1.py::test_the_committed_split_reproduces_byte_for_byte tests/integration/test_stage6_pilot_v1.py::test_the_curated_hard_negatives_validate_offline tests/integration/test_stage6_records.py::test_codebook_v0_the_coverage_report_and_the_gold_hold_offline tests/integration/test_canonical_golden.py::test_the_canonical_fixture_regenerates_byte_for_byte tests/integration/test_stage6_pilot_v1.py::test_the_committed_coverage_report_reproduces_from_its_runs tests/integration/test_stage6_pilot_v1.py::test_committed_records_validate_against_the_local_store -q -rs
```

Expected: `20 passed, 3 skipped`, with these skip lines, the main checkout's column:

```text
SKIPPED [1] tests/integration/test_stage6_pilot_v1.py:133: data/runs/events/ is not here: each Stage 6 gate runs this test
SKIPPED [2] tests/integration/test_stage6_pilot_v1.py:164: data/runs/events/ is not here: each Stage 6 gate runs this test
```

- [ ] **Step 2: The diff**

```bash
git diff --stat 186348d -- config evaluation codebooks tests/fixtures
git status --short
```

Expected: nothing, from either command.

- [ ] **Step 3: One definition**

```bash
git grep -n -e "def canonical_json" -e "def digest(" -- "*.py"
git grep -n "cohort.digests" -- "*.py" "docs/*.md"
```

Expected: Task 5's two lines in `packages/earnings-core/src/earnings_core/digests.py`,
then nothing.

- [ ] **Step 4: The suites**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
git diff --quiet 186348d -- uv.lock && echo "uv.lock unchanged"
```

Expected:

- `1747 passed, 8 skipped, 24 deselected`, with Preconditions' 8 skip lines;
- `275 passed, 5 skipped`;
- `All checks passed!` and `297 files already formatted`;
- `uv.lock unchanged`.

- [ ] **Step 5: Write the record**

Create `docs/verification/evidence-selection.md`:

```markdown
# Evidence selection and verification

Stage 7's verification record (`specs/evidence-selection-and-verification.md`,
§Verification). Plan A's section records its proof and the main checkout's gate;
plan B appends its own. Every entry holds IDs, counts, test names, and hashes, and
never a release's wording (ES2).

## Plan A: core and anchoring (plan 11)

Plan 11 (`specs/plans/11-evidence-selection-and-verification-plan-a.md`) landed the
spec's §Plan A. It changed functions and tests, and no committed record.

- **The core fixes (ES4, ES5).**
  - `reverify_span` verifies a stored span again from its fields, and never dumps
    it.
  - `validate_span` refuses an offset that is not an `int`, or is a `bool`, as
    `malformed_record`, where it raised.
  - `resolve_pointer` resolves the genuine element wherever it sits in the list.
  - `VALIDATOR_VERSION` is `"3"`, and no committed record stores it.
- **One canonical JSON (ES7).** `canonical_json` and `digest` live in
  `earnings_core.digests`, moved verbatim with their known-answer tests. Both
  packages import that one definition. The duplicated pilot pin stays, with its own
  reproduction tests.
- **`context_hash` (ES8).** A known-answer test pins its byte format, with a pair
  holding a non-ASCII character, a double quote, and a backslash:
  `fd4874e7855a8b8d6c9df217cca901d75d1129624089f94a6db6cda22ef52280`, over 47 bytes.
- **The narrative rule (ES9).** An `other` element whose children hold every
  non-space character of its span is a transparent container, and no longer blocks
  a quote.
  - Stage 1's 686 sentences now give 660 anchored, 26 repeated, and 0 not narrative.
  - The 10 that moved sit under `other-3292-5040` in `0000949699-08-000023_ex-99-1`.
  - No pilot verdict changed (M5: 0 of 5139).

### The proof

Each committed record, and the tests that reload it through its loader and recompute
its content hash with the moved functions:

| Record | Rehashed offline, in the worktree, by | Rechecked in the main checkout only, by |
| --- | --- | --- |
| Universe v1 | `test_cohort_identity.py::test_v1_loads_unchanged_and_has_an_operative_hash` | — |
| The synthetic cohort | `test_cohort_fixtures.py`: regenerates byte for byte, and replays | — |
| Events v1 and its evidence record | `test_event_corpus_v1.py::test_events_v1_loads_unchanged_with_its_evidence_record` | — |
| Pilot v1, reselected | `test_event_corpus_v1.py::test_pilot_v1_loads_unchanged_and_djia_pilot_1_reselects_it`; `test_stage6_pilot_v1.py::test_the_pin_is_pilot_v1_and_its_chain` | — |
| The synthetic events and acquisition | `test_event_fixtures.py`: regenerates byte for byte, and replays both | — |
| The split | `test_stage6_pilot_v1.py::test_the_committed_split_reproduces_byte_for_byte` | — |
| The coverage report | `test_stage6_records.py`: its hash and its pin | `test_stage6_pilot_v1.py::test_the_committed_coverage_report_reproduces_from_its_runs` |
| Codebook v0 | `test_stage6_records.py`: its hash, ADR 0003, its corpus's pin and split hash | `test_stage6_pilot_v1.py::test_committed_records_validate_against_the_local_store`, codebook case |
| The three gold files | `test_stage6_records.py`: each parses, codes against v0, holds together by ID, and names the pin and split hash | the same local test, gold case |
| The curated hard negatives | `test_stage6_pilot_v1.py::test_the_curated_hard_negatives_validate_offline` | — |
| The canonical fixtures | `test_canonical_golden.py::test_the_canonical_fixture_regenerates_byte_for_byte`, 8 cases | — |

- **Offline.** The worktree's column, run by node ID, printed `20 passed, 3
  skipped`. The three skips are the main checkout's column.
- **The diff.** `git diff --stat 186348d -- config evaluation codebooks
  tests/fixtures` printed nothing.
- **One definition.** `def canonical_json` and `def digest(` occur once each, in
  `packages/earnings-core/src/earnings_core/digests.py`, and nothing names
  `cohort.digests`.
- **The suites, in the worktree.**
  - The default suite printed `1747 passed, 8 skipped, 24 deselected`. Its 8 skips
    are the local legs that need `data/`.
  - The harness suite printed `275 passed, 5 skipped`.
  - Ruff passed, and `uv.lock` is unchanged.

### The main checkout

On [GATE: the date], the user ran the default suite in the main checkout at plan A's
tip, `[GATE: the tip's short hash]`, on a detached HEAD, from a checkout with no
tracked change. It printed `[GATE: the summary line]`. Its skip was
[GATE: the skip line's location and reason]. [GATE: "No test failed.", or each
failure's node ID and exception type, with its fix's commit.]
```

- [ ] **Step 6: Commit the record**

```bash
git log --oneline -3
git add docs/verification/evidence-selection.md
git commit -m "docs(verification): record plan 11's proof (Stage 7, plan A)"
git status --short
```

Expected: `git status --short` prints nothing.

## Completion

- [ ] **Step 1: The final review**

Run the final whole-branch review with the `code-reviewer` agent, on Opus, over
`186348d..HEAD`. Its dispatch carries:

- as the requirements: this plan, and the spec's §Plan A, §Gates, §Deferred items,
  and §Rollout;
- Global Constraints' Blinding section verbatim, with plan 11's additions.

Codex is skipped (P11-3): state the reason at the review.

- Resolve the review's findings with the user before Step 2.
- If the resolution changes any file under `packages/`, `apps/`, or `tests/`:
  - rerun Task 8's Steps 1 to 4;
  - update the record's counts;
  - commit, before the gate.

- [ ] **Step 2: The main checkout's gate (the user's; P11-12)**

This is plan A's last gate (the spec's §Gates, plan A, gate 2). In the worktree:

```bash
git status --short
git log --oneline -1
```

Expected: nothing, then the tip, plan A's last code commit or a later record commit.

Ask the user, in chat, to run these five commands in the main checkout, with the
tip's short hash written in for `<tip>`:

```bash
cd /Users/lowell/Projects/earnings-themes
git status --short --untracked-files=no
git switch --detach <tip>
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs
git switch main
```

Ask the user to report three things:

- the summary line;
- the skip line;
- for any failure, its node ID and exception type only.

Expected:

- **The status.** `git status --short --untracked-files=no` prints nothing. A tracked
  change, such as a bundle in mid-edit, would block the switch or be carried along.
  If it prints anything, the user commits or sets it aside first.
- **The summary.** `1754 passed, 1 skipped, 24 deselected`. That is main's
  `1744 passed, 1 skipped` at `c5719f8` (plan 10), plus plan A's 10 new tests. Of the
  8 local legs that skip in the worktree, 7 run and pass there, and one still skips.
- **A failure.** The user reports its node ID and exception type only, never the
  traceback or the assertion's text (the spec's §Gates). Fix it in the worktree,
  blind, with a test where one is missing. Then rerun Task 8's Steps 1 to 4, and this
  step.
- **A count that differs with no failure.** Ask the user for the skip lines, and
  compare them with Preconditions' list. Never edit a test to match.

Then fill each `[GATE: ...]` mark in `docs/verification/evidence-selection.md` from
the user's report, and commit:

```bash
grep -c "GATE" docs/verification/evidence-selection.md
git log --oneline -3
git add docs/verification/evidence-selection.md
git commit -m "docs(verification): the main checkout's gate at plan 11's tip"
git status --short
```

Expected: `0`, since every mark is filled; then the commit; then nothing.

- [ ] **Step 3: Mark up this plan** (writing-plans' Plan Completion Protocol)

- Run the resolve-before-defer gate. The spec says Stage 7 defers nothing new, so
  any leftover goes to the user before anything is deferred.
- Tick the steps, add `> Deviation:` and `> Skipped:` notes, and add the status
  header. Notes hold IDs, counts, and hashes only (Blinding).

- [ ] **Step 4: The deferred items, and the spec's line**

Tick plan 3's three items, and plan 9's two that the spec gives plan A (the spec's
§Deferred items). `Rejection`'s subject and T6-M4 stay open for plan B.

In `specs/deferred_items.md`, replace:

```markdown
- [ ] Accept a stored `VerifiedSpan` in `validate_span` (final review, Important
```

with:

```markdown
- [x] Accept a stored `VerifiedSpan` in `validate_span` (final review, Important
```

In `specs/deferred_items.md`, replace:

```markdown
      that API and its test land, at the latest when Stage 7 first stores
      `VerifiedSpan`s.
```

with:

```markdown
      that API and its test land, at the latest when Stage 7 first stores
      `VerifiedSpan`s. → done in plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md)
```

In `specs/deferred_items.md`, replace:

```markdown
- [ ] Prefer the genuine element in `resolve_pointer` (final review, Minor;
```

with:

```markdown
- [x] Prefer the genuine element in `resolve_pointer` (final review, Minor;
```

In `specs/deferred_items.md`, replace:

```markdown
      wherever it sits in the list, with a test that lists the stale element
      first.
```

with:

```markdown
      wherever it sits in the list, with a test that lists the stale element
      first. → done in plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md)
```

In `specs/deferred_items.md`, replace:

```markdown
- [ ] Reject, don't raise, on unvalidated offsets (final review, Minor; deferred
```

with:

```markdown
- [x] Reject, don't raise, on unvalidated offsets (final review, Minor; deferred
```

In `specs/deferred_items.md`, replace:

```markdown
      non-integer or bool offset on an unvalidated candidate, with a test.
```

with:

```markdown
      non-integer or bool offset on an unvalidated candidate, with a test. → done in plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md)
```

In `specs/deferred_items.md`, replace:

```markdown
- [ ] Move `canonical_json` and its digest into earnings-core (plan 9, Task 3; the
```

with:

```markdown
- [x] Move `canonical_json` and its digest into earnings-core (plan 9, Task 3; the
```

In `specs/deferred_items.md`, replace:

```markdown
      and hard negatives) still reproduces byte for byte.
```

with:

```markdown
      and hard negatives) still reproduces byte for byte. → done in plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md)
```

In `specs/deferred_items.md`, replace:

```markdown
- [ ] Settle two anchoring questions before Stage 7 recomputes context hashes or
```

with:

```markdown
- [x] Settle two anchoring questions before Stage 7 recomputes context hashes or
```

In `specs/deferred_items.md`, replace:

```markdown
      Size: plan. Done when: Stage 7's plan lands both, or records why not.
```

with:

```markdown
      Size: plan. Done when: Stage 7's plan lands both, or records why not. → done in plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md)
```

Note T3-M5's two functions in the gaps item, which stays open (P11-4):

In `specs/deferred_items.md`, replace:

```markdown
      test, or records why one is dropped. T8-M2 and T6-M2 → done in plan 10
      (specs/plans/completed/10-harden-the-gold-before-bundle-4.md).
```

with:

```markdown
      test, or records why one is dropped. T8-M2 and T6-M2 → done in plan 10
      (specs/plans/completed/10-harden-the-gold-before-bundle-4.md). T3-M5's
      `canonical_json` and `digest` → done in plan 11
      (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md).
```

If the gate at Step 3 deferred anything, append
`## 11-evidence-selection-and-verification-plan-a — YYYY-MM-DD` to the end of
`specs/deferred_items.md`, after a blank line. Use the completion date. Each item
follows the schema of `references/deferred-backlog.md`. Never append an empty
section.

Append the spec's plan A line, with the completion date for `YYYY-MM-DD`:

In `specs/evidence-selection-and-verification.md`, replace:

```markdown
- that no SEC request was sent.
```

with:

```markdown
- that no SEC request was sent.

> Plan A: COMPLETE (YYYY-MM-DD) — implemented by plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md). Next: write plan B.
```

Commit Steps 3 and 4 together:

```bash
git log --oneline -3
git add specs/plans/11-evidence-selection-and-verification-plan-a.md specs/deferred_items.md specs/evidence-selection-and-verification.md
git commit -m "docs(specs): mark up plan 11, tick its deferred items, and stamp plan A"
git status --short
```

Expected: `git status --short` prints nothing.

- [ ] **Step 5: Backlog triage**

```bash
uv run --no-project --python 3.13 python /Users/lowell/.claude/skills/writing-plans/scripts/deferred_stats.py
```

Report its summary line, and present the triage rubric if its thresholds trip.

- [ ] **Step 6: Retire this plan only** (P11-1)

The spec stays live, since plan B implements it too. Re-point the record's path to
this plan:

```bash
git mv specs/plans/11-evidence-selection-and-verification-plan-a.md specs/plans/completed/
sed -i '' 's#specs/plans/11-evidence-selection-and-verification-plan-a.md#specs/plans/completed/11-evidence-selection-and-verification-plan-a.md#g' docs/verification/evidence-selection.md
git grep -n "specs/plans/11-evidence" -- docs CLAUDE.md specs/evidence-selection-and-verification.md specs/deferred_items.md
git log --oneline -3
git add specs/plans/completed/11-evidence-selection-and-verification-plan-a.md docs/verification/evidence-selection.md
git commit -m "chore(specs): retire plan 11"
git status --short
```

Expected: no `git grep` output; the commit; then nothing.

- [ ] **Step 7: `CLAUDE.md`'s current state (only on the user's yes)**

The spec's §Rollout asks for the refresh, and `CLAUDE.md` changes only with the
user's direct consent. Run this step in the controller session, never in a subagent.

- Ask the user with AskUserQuestion, showing the two edits below in a preview. The
  options are: apply them, or leave `CLAUDE.md` unchanged.
- On a yes, apply them and commit them alone.
- If an old text does not match, re-draft the edit against the current file, and ask
  again.

In `CLAUDE.md`, replace:

```markdown
| `AGENTS-jev-addendum.md`, `specs/jev-integration-spec.md` |
```

with:

```markdown
| `specs/evidence-selection-and-verification.md` | **Stage 7's stage spec**, approved 2026-10-04, and live until plan B completes. It splits the stage into two plans (ES1): plan A (plan 11) settles earnings-core's open items, moves `canonical_json` into core, and lets a transparent `other` container hold a quote; plan B builds the extractor. It amends the Stage 3 and Stage 6 handoffs at two points: `other` elements (ES9) and the pointer unit (ES12). |
| `AGENTS-jev-addendum.md`, `specs/jev-integration-spec.md` |
```

In `CLAUDE.md`, replace:

```markdown
The top-level modules of `earnings-themes`, `earnings-ingestion`, and `apps/earnings-pipeline` still hold only a `hello()` stub;
```

with:

```markdown
Stage 7's plan A (plan 11, `specs/plans/completed/11-evidence-selection-and-verification-plan-a.md`) is done, and plan B, the extractor, is next (`specs/evidence-selection-and-verification.md`):

- `earnings-core` holds `reverify_span`, which verifies a stored span again at each later gate (ES5), and `canonical_json` and `digest` (`digests.py`), the one definition both packages import (ES7); `earnings_ingestion/cohort/digests.py` is gone. `validate_span` refuses an unvalidated offset as `malformed_record`, `resolve_pointer` resolves the genuine element wherever it sits, and `VALIDATOR_VERSION` is `"3"`, which no committed record stores.
- `anchoring.py`'s `narrative_home` is public, and an `other` element whose children hold all its text is a transparent container that no longer blocks a quote (ES9): Stage 1's fixtures anchor 660 sentences, 26 repeat, and none is refused as not narrative. A known-answer test pins `context_hash`'s byte format (ES8).
- No committed record changed. `docs/verification/evidence-selection.md` maps each record to the test that rehashes it, and records the user's default-suite run in the main checkout.

The top-level modules of `earnings-themes`, `earnings-ingestion`, and `apps/earnings-pipeline` still hold only a `hello()` stub;
```

On a yes:

```bash
git log --oneline -3
git add CLAUDE.md
git commit -m "docs: CLAUDE.md's current state after Stage 7's plan A (plan 11)"
git status --short
```

Expected: `git status --short` prints nothing.

- [ ] **Step 8: Integrate**

Use finishing-a-development-branch. Its Step 4b states P11-3's reason.

- **Never push.** The choice among its options is the user's, in that session. A push
  happens only when the user explicitly says to push there.
- **Before any push the user asks for**, check every commit it publishes, and the
  tree at its tip, by count, so no path is printed:

```bash
git fetch origin main
git rev-list --count origin/main..HEAD -- data/
git ls-tree -r --name-only HEAD -- data/ | awk 'END { print NR }'
```

Expected: `0` and `0`. Otherwise stop and report it.

- **The worktree.** Whether it stays for plan B or is removed is the user's choice,
  at that skill's cleanup step. Plan B is planned only after this branch merges (ES1).

- [ ] **Step 9: Report**

- **Commands.** State the commands actually run, and their results.
- **What did not happen.** No session opened pilot text, read gold, or ran
  extraction. No model was called from code, and no SEC request was sent (the
  spec's §Rollout).
- **The proof.** Give its counts, and the user's gate line.
- **The backlog.** List the deferred items ticked and noted, and give the backlog's
  summary line.
- **Codex.** State that it was skipped (P11-3).
- **What follows.** Plan B may be planned once this branch merges (ES1).
