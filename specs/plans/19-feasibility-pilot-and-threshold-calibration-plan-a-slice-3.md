# Stage 11 Plan A, Slice 3: Evaluation, Support Labels and Calibration Implementation Plan

**Status: COMPLETE (2026-10-13)** — executed via subagent-driven-development; deferred items in specs/deferred_items.md

> **Execution record.** This is plan A's third slice only: Stage 11 is not ticked, `Plan A: COMPLETE` is not appended and the spec is not retired. Slice 4 (A8) is next; see §Handoffs.
>
> - **Counts at `eccb77c`.** Scoped checks: evaluation, tomlfile, import boundaries and `test_import_scan` 297 passed; coding and support 1519 passed, 1 skipped, 2 deselected; contracts, integration and workflow 605 passed, 1 deselected; Ruff clean; `uv lock --check` resolved 153 packages. The user's gates in the main checkout: the root suite 4719 passed, 2 skipped, 28 deselected, 1 warning in 889.65 s; the Stage 6 wording test 7 passed. The plan's 161 / 1517 / 603 and '170 tests' were stale (command 1 was already 161 after Task 9).
> - **Plan text now stale.** Task 13's `NEVER_GATED` and superset validator (lines ~5683, 5894, 5969) and the `GateRule.gated` dictionary row (~6064); Global Constraints' 'a schema failure raises Pydantic's `ValidationError`' (`freeze_preregistration` and `load_preregistration` raise `RecordError`); Task 4 and Task 7's `unit_tally` / `char_counts` return types (now `EvidenceTally`); `report._first_duplicate` (now `problems.first_duplicate`); the 45 exports (now 46).
> - **Review chain.** Every task passed a task review (opus for Tasks 5, 12 and 14, sonnet or opus otherwise) with at most one fix round. The final whole-branch review (an Opus code-reviewer, 'with fixes', and Codex, three P2 findings) was fixed in five rounds, each re-reviewed by both seats; `Codex reviewed 90a7f33`.
> - **Spec.** Task 1's ten amendments landed in `2ec4df9`. Line 298 ('A tie goes to the candidate using fewer signals') was corrected in the slice-stamp commit, because the amended menu made every candidate single-signal.

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `earnings_themes.evaluation`, with A9's dictionary rows for its records. It holds:
- the pilot's metrics with event-clustered bootstrap intervals, and V6's gate evaluator (A3);
- the support-label records, the sampler and the label view (A4);
- the preregistration, calibration and the calibrated policy (A5).

The work uses no pilot text and loads no model.

**Architecture:**
- **`earnings_themes.evaluation`** is a new, pure subpackage. It reads no file, sends no request, loads no model and prints nothing. The application gathers its inputs in slice 4 (A8).
  - **Scoring (A3):**
    - `align` maps spans to pointer units.
    - `cells` reads a gold reading into event × theme cells, under FP20's `uncertain` and `tie_group` conventions.
    - `scores` tallies them.
    - `agreement` and `bootstrap` give κ, AC1, Fleiss' κ and event-clustered percentile intervals.
    - `verdicts` reads judge trials.
    - `records` holds the report and gate records.
    - `report` computes every §Metrics figure for a partition.
    - `gates` derives V6's gates and evaluates a report against them.
  - **Labels (A4):**
    - `labels` holds `SupportLabel`, its committed TOML, and `labels check`'s refusals.
    - `sampling` draws the deterministic sample from IDs alone.
    - `label_view` renders the local markdown the user labels from.
  - **Calibration (A5):**
    - `preregistration` holds the committed preregistration.
    - `calibration` runs the floor test, fits the scorer-cutoff menu, selects, and writes `CalibrationArtifact`.
    - `policy` binds the artifact as Stage 9's `AssignmentPolicy`.
- **Two Stage 8 and 9 seams (Task 12):**
  - `coding.decide.decision_inputs` gives calibration exactly the views that `decide_assignments` votes on (D19-5).
  - `support.metrics.accepted_claim_recall` gives label recall beside precision.
- **`tomlfile`** writes finite floats, which the preregistration and the gates hold.
- **The spec:** Task 1 amends FP10, FP14, FP18, FP22, A3, §Preregistration, §Calibration, §Failure handling and §Metrics, as the user decided on 2026-10-12 (D19-1, D19-3, D19-4, D19-18).

**Tech Stack:** Python 3.14.0 uv workspace; Pydantic v2 (strict, frozen); the standard library's `random.Random` for the bootstrap; pytest; Ruff. No new dependency.

**Spec:** `specs/feasibility-pilot-and-threshold-calibration.md`, approved 2026-10-11, merged to `main` at `c1e7ac7`, amended by plan 18; read at `7948d94`. This plan implements:
- §Plan A: A3, A4, A5, and A9's data-dictionary rows for their records;
- §Verification's plan A items: the known-answer metric and bootstrap tests; the sampler's signature and the label view's sentinel; the import boundary (`evaluation` imports no ingestion and no httpx); the reject-everything gate test; the data-dictionary checks;
- FP4, FP8–FP10, FP13–FP15, FP17, FP18, FP20 and FP21, with FP10, FP14 and FP18 as Task 1 amends them.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 11 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

**This plan is plan A's third slice, not plan A.** The spec's Rollout says the Roadmap line's "plan completion" means plan B's, and plan A's own completion appends `Plan A: COMPLETE`. Plan 19 does neither. On completion it:
- does not tick Stage 11;
- does not append the spec's `Plan A: COMPLETE` line;
- does not retire the spec.

Instead, it appends a slice stamp to the spec's Rollout and retires only itself (Task 16). Plan A's last slice is A8, with A9's dictionary rows for its records (D19-2).

## Global Constraints

- **GS13, blinding.**
  - The executing session never opens pilot text, a kept draft, or anything under `data/runs/gold/` or `data/runs/pilot/`. It never opens anything under the main checkout's `data/`.
  - Execute in a fresh worktree, which has no `data/` at all.
  - Never load a model, a tokenizer or a scorer runtime. No test here needs one: they use invented records, scripted judge trials, and Stage 9's invented assessed case.
  - Never run `-m live` (`EDGAR_IDENTITY` is exported in this shell) or `-m browser`.
  - Tests read only invented records, the synthetic layer, Stage 1's committed fixtures, and committed prompts.
- **Tracebacks.** Never pass `--tb=long`, `--tb=auto`, `--full-trace`, `-l`, `--showlocals`, `--pdb`, or `-vv`.
- **User gates.** The default (root) suite and the Stage 6 wording test run in the main checkout, and the user runs them in their own terminal (Task 16). The executor never runs:
  - `pytest packages apps tests`;
  - `tests/integration/test_stage6_wording.py`;
  - `tests/integration/test_stage6_pilot_v1.py`.

  A failing user gate is reported by test name and reason only.
- **The user's gate file.** This plan does not edit `tests/integration/test_stage6_wording.py`. Its globs already cover Stage 11's evaluation records (plan 17).
- **`CLAUDE.md`.** Never edit it without asking the user first.
- **TDD.** Every code task writes its failing tests first, and watches them fail for the stated reason. Task 1 is a docs-only spec amendment, and Task 16 runs the checks.
- **No copied logic (D18-1).** The plan's code calls or extracts a shared helper; it never copies an existing block. Task 12 extracts `decision_input` from `decide_assignments` for this reason. If an implementer finds the plan's code repeating a block that already exists, they call or extract it instead, and record a `> Deviation:` line.
- **The plan's code is verified.** Every task's code was replayed in order onto a clean `7948d94`. Each task's tests failed as Step 2 says and passed as Step 4 says, Ruff was clean after every task, and the end state is byte-identical to the verified prototype. Copy the code exactly. A step that fails as written is a finding to report, not something to patch around.
- **GS3, the public repository.** Committed files hold IDs, hashes, counts and the user's words, never release text, and never a path on this machine. This plan commits no evaluation record. The preregistration, labels, calibration artifact, report and gates are plan B's.
- **Refusals.** Each names its item by ID or field path, and its reason, never text.
  - An evaluation refusal is an `EvaluationError` carrying an `EvaluationProblem`, or a `Refusal` row from `check_labels`.
  - A Stage 9 seam's refusal is a `CodingError` with a closed reason.
  - A record that fails its schema raises Pydantic's `ValidationError`.
  - A committed record that does not hash to its `content_hash` raises `RecordError`.
- **GS17, units, and D19-4, the import boundary.**
  - `earnings-themes` imports only `earnings-core`, and ingestion and themes never import each other.
  - `evaluation` imports `earnings-core`, themes records, and pure Stage 7–9 code: `extraction.units`, `support.metrics`, `support.context` and `coding.decide`, with their records modules.
  - It never imports ingestion, httpx, `support.nli`, an NLI runtime, `extraction.local` or `coding.local`.
  - Task 2 adds `earnings_themes.evaluation` to `PIPELINE_PREFIXES`, so no gold-drafting module may import it, and a fresh-process test pins the rest.
  - Every task runs `test_import_boundaries.py` and `tests/contracts/test_import_scan.py` in its own command.
- **Data dictionary (A9).**
  - Every new model, enum and dataclass gets its own `###` table, headed by its name, in `docs/data-dictionary.md`'s new section "Stage 11 evaluation (plan 19)", in the task that adds it.
  - It is also registered in `EVALUATION_MODELS`, `EVALUATION_ENUMS` or `EVALUATION_DATACLASSES` in `tests/contracts/test_data_dictionary.py`. Task 2's registry test fails on any evaluation model, enum or dataclass left unregistered.
  - A changed existing contract (Task 12) updates its existing paragraph and row.
- **No committed record changes.** No schema version changes. `MetricReport.reason` gains `no_labeled_positive`; until Task 14, `MetricReport` is computed, never stored.
- **The lockfile.** No task runs `uv lock`. `uv lock --check` must print `Resolved 153 packages`, as at `7948d94`.
- **Ruff.** Default line length, 88. Run `uv run --locked ruff format <changed Python files>` before each commit. `uv run --locked ruff check .` and `uv run --locked ruff format --check .` must be clean.
- **Commits.**
  - Before each commit, run `git log -3 --oneline`, since the user may commit on the branch mid-run.
  - End each commit message with the attribution trailer your session's instructions give.
- **Line numbers** cited here are at `7948d94`. Recheck each before relying on it.
- **Agent verification scope.** The executor runs only these, in the worktree:
  - each task's own command (Steps 2 and 4);
  - `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_import_boundaries.py -q`
  - `uv run --locked --all-packages pytest packages/earnings-themes/tests/coding packages/earnings-themes/tests/support -q`
  - `uv run --locked --all-packages pytest tests/contracts tests/integration/test_coding_frozen_v0.py tests/integration/test_support_fixtures.py tests/integration/test_theme_frozen_v0.py tests/integration/test_theme_vertical_slice.py apps/earnings-pipeline/tests/test_theme_workflow.py -q`
  - `uv run --locked ruff check .`, `uv run --locked ruff format --check .`, and `uv lock --check`.

  After Task 15 these gave, on the replay: command 1 `161 passed`; command 2 `1517 passed, 1 skipped, 2 deselected`; command 3 `603 passed, 1 deselected`.

## Decisions

Taken by the user:
- **D19-1** (user, planning, 2026-10-12): Stage 9's gate stays, so a flagged target is never accepted. Applied in: Task 1 (spec amendment: FP10, FP22, §Preregistration, §Calibration, §Failure handling); Tasks 13–15.
  - **Why the menu collapses.** Stage 8 marks a target `assessed` only when all four trials answer `supported` and `fits` with no objection (`derive_outcome`, `support/assess.py:435`). Stage 9 sends every other target to review before any policy votes (`decision_vote`). So both families' consensus supports every target a policy can accept, and the spec's veto, judge-floor and both-agree candidates decide exactly as scorer-only does.
  - **What follows.** The menu holds scorer-cutoff candidates only. The judge floor is reported and recorded by V6, with `consequence = "reported_only"`, and changes no pilot decision. Label recall is capped by the share of positive labels whose targets came out `assessed`.
- **D19-2** (user, planning, 2026-10-12): this slice is A3–A5, with A9's dictionary rows for their records. A8 is slice 4, and its commands consume every module here. Applied in: scope; §Handoffs.
- **D19-3** (user, planning, 2026-10-12): the roll-up maps both gold and predicted themes to their level-one roots, then scores the same way, so two children of one level-one theme meet there. "Siblings earn nothing" holds at the exact level. Applied in: Task 1 (spec amendment: FP14, §Metrics); Tasks 3 and 7.
- **D19-4** (user, planning, 2026-10-12): `evaluation` imports pure Stage 7–9 code, so calibration and the report reuse `decision_vote`, `units`, `context_elements` and Stage 8's metrics rather than copying them (D18-1). FP18 and A3's opening are amended to say so. `PIPELINE_PREFIXES` gains `earnings_themes.evaluation`, and a fresh-process test shows that it loads no optional adapter. Applied in: Task 1 (spec amendment: FP18, A3); Task 2.

- **D19-18** (user, plan review, 2026-10-12): Task 1's wording is approved as written, including two additions beyond D19-1: FP22's sentence on a family below the floor, and §Calibration's tie-break between candidates that use as many signals. §Preregistration's menu bullet is amended too, since the preregistration is committed before any cutoff is fitted. The planner defaults D19-5 to D19-17 are accepted. Applied in: Task 1; Tasks 2–15.

Planner defaults (accepted at the plan review, D19-18):
- **D19-5:** calibration simulates each cutoff through Stage 9's own `decision_vote`, over the views that `decision_inputs` builds for `decide_assignments`. So a cutoff fitted on train decides on dev as Stage 9 will. Applied in: Tasks 12, 14 and 15.
- **D19-6:** a tie group resolves in this order:
  - the lowest-ID member the run predicted;
  - else the lowest-ID member already present through an untied row;
  - else its lowest-ID member.

  Its other members are excused: predicting one is neither a hit nor a false positive. Applied in: Task 3.
- **D19-7:** a reading's dangling references are tolerated and counted, never refused, so a kept draft scores as drafted. A dangling reference is a claim citing a quote the reading lacks, or an assignment citing a claim it lacks. This records P17-5(2)'s decision; the item stays open for slice 4. Applied in: Task 3.
- **D19-8:** gold-evidence recall is theme-agnostic: the share of gold-supporting units that any accepted assignment's quotes hold. Applied in: Tasks 4 and 7.
- **D19-9:** GS5's edited and rejected shares are over drafted items (accepted + edited + rejected). The added share is over signed items (accepted + edited + added). Applied in: Task 4.
- **D19-10:** a label figure's bootstrap resamples only the events that hold labels. An undefined resample is skipped and counted. The interval is undefined when more than the preregistered `max_undefined_share` of resamples are undefined. Applied in: Tasks 5 and 7.
- **D19-11:** what a gate becomes when its dev lower bound is undefined is preregistered as `undefined_gate`: `not_gated` or `point_estimate`. Applied in: Tasks 8 and 13.
- **D19-12:** the sampler ranks by a seeded digest and round-robins. Events go in rank order, one target per event per round, and each event's targets round-robin across its themes. A larger size extends the same sample, so the preregistered extension raises train's size by `extension_step` for each of `train_extensions`. Applied in: Tasks 9, 10 and 13.
- **D19-13:** the preregistration, the calibration artifact, the report and the gates each carry their own `content_hash`. `records.checked` refuses a record that does not hash to it, and `load_preregistration` and `load_gates` call it; A8's JSON readers will too. Applied in: Tasks 6, 8, 13 and 14.
- **D19-14:** the frozen configuration binds:
  - the extraction configuration;
  - the coding codebook, classifier, policy, ceilings and schema;
  - the support policy, ceilings, scorer, judges and extractor family.

  It binds no run ID, document, claim order, cache mode or stability run, so dev's replay reproduces train's hash. DeBERTa, which is reported only, is not bound. Applied in: Task 14.
- **D19-15:** judge agreement is also reported per family and presentation, each with its uncertain count. Stability's Fleiss' κ runs over every codebook theme × event, and its Jaccards over the unit sets and the (theme, unit) sets. Applied in: Task 7.
- **D19-16:** `tomlfile` writes a finite float as its `repr`, and refuses NaN and infinity. Labels are written train before dev, each by target ID. Applied in: Tasks 8 and 9.
- **D19-17:** the label view is built from the stored support run and its sources, through Stage 8's `context_elements`, so it needs no extraction re-run. Applied in: Task 11.

---

## File Structure

`EV` below is `packages/earnings-themes/src/earnings_themes/evaluation/`, and `TEV` is `packages/earnings-themes/tests/evaluation/`.

| File | Change | Responsibility |
| --- | --- | --- |
| `specs/feasibility-pilot-and-threshold-calibration.md` | Modify | Task 1's amendments; Task 16's slice stamp |
| `EV/__init__.py` | Create | The package docstring (Task 2); the public exports (Task 15) |
| `EV/problems.py` | Create | `EvaluationProblem`, `EvaluationError` |
| `EV/align.py` | Create | The pointer-unit index; spans to units; character overlap |
| `EV/cells.py` | Create | A gold reading's event × theme cells; level-one roots |
| `EV/scores.py` | Create | Tallies, and every count-based figure |
| `EV/agreement.py` | Create | Cohen's κ, Gwet's AC1, Fleiss' κ |
| `EV/bootstrap.py` | Create | The event-clustered percentile bootstrap |
| `EV/verdicts.py` | Create | A family's consensus; each trial's verdict |
| `EV/records.py` | Create | `Metric`; the report and gate records; content hashes |
| `EV/report.py` | Create | Every §Metrics figure for a partition; independent and stability figures |
| `EV/gates.py` | Create | V6's gates, their TOML, and the gate evaluator |
| `EV/labels.py` | Create | Support labels, their TOML, `labels check`, and the merge |
| `EV/sampling.py` | Create | The label pool and the deterministic sampler |
| `EV/label_view.py` | Create | The local label view's markdown |
| `EV/preregistration.py` | Create | The preregistration record and its TOML |
| `EV/calibration.py` | Create | The floor test, the fit, the selection, the artifact, the frozen configuration |
| `EV/policy.py` | Create | `CalibratedPolicy` |
| `packages/earnings-themes/src/earnings_themes/coding/decide.py` | Modify | `decision_input` (extracted) and `decision_inputs` |
| `packages/earnings-themes/src/earnings_themes/support/metrics.py` | Modify | `accepted_claim_recall`; `MetricReport.reason` |
| `packages/earnings-themes/src/earnings_themes/tomlfile.py` | Modify | Finite floats |
| `docs/data-dictionary.md` | Modify | The "Stage 11 evaluation (plan 19)" section; three Stage 8 and 9 paragraphs and rows |
| `tests/contracts/test_data_dictionary.py` | Modify | The evaluation registry and its four tests |
| `packages/earnings-themes/tests/test_import_boundaries.py` | Modify | `PIPELINE_PREFIXES`; the evaluation import tests |
| `TEV/__init__.py, cases.py, conftest.py` | Create | The test package, invented readings and views, and Stage 9's assessed case |
| `TEV/test_*.py` | Create | One test module for each evaluation module |
| `packages/earnings-themes/tests/{test_tomlfile,coding/test_decide,support/test_metrics}.py` | Modify | One test each, for Tasks 8 and 12 |

---

### Task 1: Amend the spec: FP10, FP14, FP18, FP22, A3, §Preregistration, §Calibration, §Failure handling and §Metrics (docs only)

**Files:**
- Modify: `specs/feasibility-pilot-and-threshold-calibration.md` `:59`, `:63`, `:67`, `:71`, `:157-158`, `:258`, `:259`, `:282-292`, `:323`, `:353`

**Interfaces:**
- Consumes: nothing.
- Produces: the amended spec that Tasks 2–15 implement, and that slice 4 (A8) and plan B read.

The spec's status line and every other line stay as they are. The user decided each change's substance on 2026-10-12 (D19-1, D19-3, D19-4), and approved this exact wording at the plan review (D19-18). Each edit replaces text that occurs exactly once in the spec.

- [x] **Step 1: Replace FP10's row**

Replace:

```text
| FP10 | **A preregistered policy menu.** Three or four transparent candidates are fit on train labels, and the selection rule picks one. It is frozen before dev is run (§Calibration). |
```

with:

```text
| FP10 | **A preregistered policy menu.** Transparent scorer-cutoff candidates are fit on train labels, and the selection rule picks one. It is frozen before dev is run (§Calibration). Stage 9 sends every target that is not `assessed` to review before any policy votes, and both families' consensus supports every `assessed` target, so a candidate that also reads the judges decides as scorer-only does. *(Amended by the user, plan 19, 2026-10-12.)* |
```

- [x] **Step 2: Replace FP14's row**

Replace:

```text
| FP14 | **Hierarchy credit.** Exact-theme F1 is gated. A level-one roll-up F1 is secondary. A sibling never earns credit. |
```

with:

```text
| FP14 | **Hierarchy credit.** Exact-theme F1 is gated. A level-one roll-up F1 is secondary. A sibling never earns credit at the exact level. *(Amended by the user, plan 19, 2026-10-12.)* |
```

- [x] **Step 3: Replace FP18's row**

Replace:

```text
| FP18 | *(design)* **Package placement.** `earnings_themes.evaluation` is pure and imports only `earnings-core` and themes records. The commands extend the existing `pilot` group. Coverage v2 stays in ingestion's `build_coverage`, and the app supplies its `NoThemeCount` rows, so ingestion never reads gold. |
```

with:

```text
| FP18 | *(design; amended by the user, plan 19, 2026-10-12)* **Package placement.** `earnings_themes.evaluation` is pure. It imports `earnings-core`, themes records and pure Stage 7–9 code (`extraction.units`, `support.metrics`, `support.context`, `coding.decide`), never ingestion, httpx, an NLI runtime or a concrete adapter, and no gold-drafting module imports it. The commands extend the existing `pilot` group. Coverage v2 stays in ingestion's `build_coverage`, and the app supplies its `NoThemeCount` rows, so ingestion never reads gold. |
```

- [x] **Step 4: Replace FP22's sentence on a family below the floor**

Replace:

```text
A judge family that then fails the floor leaves the scorer-only candidate, itself a finding.
```

with:

```text
A judge family that then fails the floor is reported, and recorded by V6, itself a finding *(amended by the user, plan 19, 2026-10-12)*.
```

- [x] **Step 5: Replace A3's opening**

Replace:

```text
A pure package that imports only `earnings-core` and themes records, never ingestion or
httpx. It holds:
```

with:

```text
A pure package that imports `earnings-core`, themes records and pure Stage 7–9 code
(`extraction.units`, `support.metrics`, `support.context`, `coding.decide`), never
ingestion, httpx, an NLI runtime or a concrete adapter
*(amended by the user, plan 19, 2026-10-12)*. It holds:
```

- [x] **Step 6: Replace §Preregistration's floor consequence**

Replace:

```text
- **the floor's consequence:** a family below it is excluded from every candidate's rule;
```

with:

```text
- **the floor's consequence:** reported, and recorded by V6. Stage 9 sends a flagged target to review before any policy votes, so the floor changes no pilot decision *(amended by the user, plan 19, 2026-10-12)*;
```

- [x] **Step 7: Replace §Preregistration's menu bullet**

Replace:

```text
- **the menu:** each candidate's exact rule, its fitted cutoffs, and the cutoff grid;
```

with:

```text
- **the menu:** each candidate's exact rule and its cutoff grid; the fitted cutoffs go in `calibration-v1.json` *(amended by the user, plan 19, 2026-10-12)*;
```

- [x] **Step 8: Replace §Calibration's menu**

Replace:

```text
**The menu.** Every candidate sends `refused` and `incomplete` targets to review, as
Stage 9 does. Candidates vote only `accept` or `review`, and `reject` stays unused in
the baseline. Each candidate uses at most two fitted cutoffs, over MiniCheck's joint
score and the eligible families' consensus. The preregistration fixes the exact rules.
Indicatively:
- **scorer only:** accept when the joint score ≥ t;
- **scorer with veto:** as above, unless an eligible family's consensus opposes;
- **judges with a scorer floor:** accept when every eligible family's consensus supports, and the joint score ≥ t;
- **both agree:** accept when the joint score ≥ t, and at least one eligible family's consensus supports with none opposing.

Each candidate also says whether a `flagged` target may be accepted.
```

with:

```text
**The menu** *(amended by the user, plan 19, 2026-10-12)*. Stage 9's gates run before
any candidate votes: `refused`, `incomplete` and `flagged` targets go to review, and
only an `assessed` target reaches the policy. Stage 8 marks a target `assessed` only
when all four trials answer `supported` and `fits` with no objection, so both
families' consensus supports every target a candidate can accept, and a rule that
also reads the judges decides as the scorer alone does. Every candidate is therefore
a scorer cutoff: accept, citing the eligible quotes, when MiniCheck's joint score ≥ t
and the target has an eligible quote; otherwise review. `reject` stays unused in the
baseline. The preregistration fixes each candidate's cutoff grid. Ties go to the lower
cutoff: within a candidate, and between candidates that use as many signals. Label
recall is capped by the share of positive labels whose targets came out `assessed`.
```

- [x] **Step 9: Replace §Failure handling's floor row**

Replace:

```text
| A family below the floor | Excluded from every candidate, as preregistered. |
```

with:

```text
| A family below the floor | Reported, and recorded by V6; no pilot decision changes. *(Amended by the user, plan 19, 2026-10-12.)* |
```

- [x] **Step 10: Replace §Metrics' roll-up row**

Replace:

```text
| Theme F1, rolled up | Both sides are mapped to their level-one ancestor (self or descendant), then scored the same way. Siblings earn nothing. | Secondary |
```

with:

```text
| Theme F1, rolled up | Both sides are mapped to their level-one ancestor (self or descendant), then scored the same way, so two children of one level-one theme meet there. A sibling earns nothing at the exact level. *(Amended by the user, plan 19, 2026-10-12.)* | Secondary |
```

- [x] **Step 11: Check that nothing else changed**

```bash
git diff --stat -- specs/feasibility-pilot-and-threshold-calibration.md
grep -c 'plan 19, 2026-10-12' specs/feasibility-pilot-and-threshold-calibration.md
```

Expected: one file changed, and `10` tagged edits.

- [x] **Step 12: Commit**

```bash
git log -3 --oneline
git add specs/feasibility-pilot-and-threshold-calibration.md
git commit -m "docs(specs): amend Stage 11 for the evaluation package (plan 19)"
```

---

### Task 2: The package, its refusals, and pointer-unit alignment (A3)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/__init__.py`
- Create: `packages/earnings-themes/tests/evaluation/cases.py`
- Create: `packages/earnings-themes/tests/evaluation/test_align.py`
- Modify: `packages/earnings-themes/tests/test_import_boundaries.py` (`:66-71`; `PIPELINE_PREFIXES`; two tests appended)
- Modify: `tests/contracts/test_data_dictionary.py` (imports; the evaluation registry)
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/__init__.py`
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/problems.py`
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/align.py`
- Modify: `docs/data-dictionary.md` (the evaluation section: `EvaluationProblem`, `UnitIndex`)

**Interfaces:**
- Consumes:
  - existing at `7948d94`: `earnings_core`: `CanonicalDocument`, `DocumentElement`, `ElementType`, `TextSpan`, `digest`; `earnings_themes.anchoring`: `Bundle`; `earnings_themes.annotation`: `Reading`; `earnings_themes.coding.decide`: `DecisionInput`, `eligible_quote_ids`; `earnings_themes.extraction.units`: `units`; `earnings_themes.gold`: `CodebookRef`, `DraftCounts`, `Gold`, `GoldAssignment`, `GoldClaim`, `GoldQuote`, `HardNegative`, `NegativeKind`, `Origin`, `ReleaseIdentification`, `ReleaseLabel`, `Support`; `earnings_themes.split`: `Partition`; `earnings_themes.support`: `derive_outcome`; `earnings_themes.support.records`: `CodebookReference`, `EntailmentSignal`, `EvidenceReference`, `JudgeAnswer`, `JudgeIdentity`, `JudgeTrial`, `Presentation`, `QuoteAssessment`, `RuntimeIdentity`, `ScorerIdentity`, `SignalStatus`, `Target`, `TargetRecord`; `earnings_themes.synthetic`: `PIN`
- Produces:
  - In `packages/earnings-themes/tests/evaluation/cases.py`:
    - `LINES`
    - `HASH`
    - `bundle(name: str='invented-evaluation', lines: tuple[str, ...]=LINES) -> Bundle`
    - `unit_ids(source: Bundle) -> tuple[str, ...]`
    - `quote(quote_id: str, start: int, end: int, element_id: str) -> GoldQuote`
    - `claim(claim_id: str, *quote_ids: str) -> GoldClaim`
    - `row(claim_id: str, theme_id: str, support: Support=Support.SUPPORTS, tie_group: str | None=None) -> GoldAssignment`
    - `negative(claim_id: str, quote_id: str, kind: NegativeKind, theme_id: str | None) -> HardNegative`
    - `reading(quotes=(), claims=(), assignments=(), negatives=(), label: ReleaseLabel=ReleaseLabel.RELEASE) -> Reading`
    - `example() -> tuple[Bundle, Reading]`
    - `gold(event_id: str, base: Reading, partition: str='dev', **changes) -> Gold`
    - `trial(target_id: str, family: str, presentation: str, claim_support: str, theme_fit: str, quotes: tuple[str, ...]=())`
    - `panel(target_id: str, first: tuple[str, str], second: tuple[str, str], quotes: tuple[str, ...]=())`
    - `decision_view(target_id: str, score: float, first: tuple[str, str], second: tuple[str, str])`
  - In `earnings_themes.evaluation.problems`:
    - `class EvaluationProblem(StrEnum)`: `malformed_record`, `parent_cycle`, `wrong_partition`, `unknown_event`, `unknown_target`, `duplicate_target`, `target_hash_mismatch`, `not_sampled`, `not_labelled`, `labels_changed`, `preregistration_mismatch`, `content_hash_mismatch`, `too_few_labels`, `no_candidate`, `unknown_metric`
    - `class EvaluationError(ValueError)`: methods `.__init__(problem: EvaluationProblem, subject: str='') -> None`
  - In `earnings_themes.evaluation.align`:
    - `type Span = tuple[int, int]`
    - `class UnitIndex` (frozen dataclass): fields `doc_id: str`, `spans: tuple[tuple[str, int, int], ...]`
    - `unit_index(bundle: Bundle) -> UnitIndex`
    - `units_over(index: UnitIndex, spans: Iterable[Span]) -> frozenset[str]`
    - `merged(spans: Iterable[Span]) -> tuple[Span, ...]`
    - `covered(spans: Iterable[Span]) -> int`
    - `char_overlap(a: Iterable[Span], b: Iterable[Span]) -> tuple[int, int]`

The package starts as its docstring alone, because Ruff's isort needs `evaluation/__init__.py` to treat `earnings_themes` as first-party. Task 15 adds the exports, once every module exists. `problems` names every evaluation refusal. `align` indexes a document's pointer units (ES12) through Stage 7's `units`, and maps a span to every unit it shares a character with (FP13).

`tests/evaluation/cases.py` holds the invented readings, trials and decision views that later tasks' tests use. Its Stage 8 and 9 imports sit inside functions, so it imports cleanly now. The import boundary (D19-4) and the dictionary registry land here, so every later module is held to both from its first commit.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/__init__.py`, empty.

Create `packages/earnings-themes/tests/evaluation/cases.py`:

```python
"""Invented readings over an invented four-paragraph document: no release text, and
no pilot text (GS13). Each paragraph is one pointer unit."""

from earnings_core import CanonicalDocument, DocumentElement, ElementType, TextSpan
from earnings_themes.anchoring import Bundle
from earnings_themes.annotation import Reading
from earnings_themes.gold import (
    Gold,
    GoldAssignment,
    GoldClaim,
    GoldQuote,
    HardNegative,
    NegativeKind,
    Origin,
    ReleaseIdentification,
    ReleaseLabel,
    Support,
)

LINES = (
    "Alpha built a plant.",
    "Beta cut prices.",
    "Gamma hired staff.",
    "Delta paid debt.",
)
"""Spans: [0, 20), [21, 37), [38, 56) and [57, 73)."""
HASH = "0" * 64


def bundle(name: str = "invented-evaluation", lines: tuple[str, ...] = LINES) -> Bundle:
    text = "\n".join(lines)
    document = CanonicalDocument.create(
        source_document_id=name,
        canonicalization_version="test-1",
        canonical_text=text,
    )
    elements, start = [], 0
    for line in lines:
        span = TextSpan(start=start, end=start + len(line))
        elements.append(DocumentElement.create(document, ElementType.PARAGRAPH, span))
        start = span.end + 1
    return Bundle(name, document, tuple(elements), ())


def unit_ids(source: Bundle) -> tuple[str, ...]:
    return tuple(e.element_id for e in source.elements)


def quote(quote_id: str, start: int, end: int, element_id: str) -> GoldQuote:
    return GoldQuote(
        quote_id=quote_id,
        start=start,
        end=end,
        element_id=element_id,
        quote_sha256=HASH,
        origin=Origin.DRAFTED_ACCEPTED,
    )


def claim(claim_id: str, *quote_ids: str) -> GoldClaim:
    return GoldClaim(
        claim_id=claim_id,
        quote_ids=quote_ids,
        claim="An invented claim.",
        origin=Origin.DRAFTED_ACCEPTED,
    )


def row(
    claim_id: str,
    theme_id: str,
    support: Support = Support.SUPPORTS,
    tie_group: str | None = None,
) -> GoldAssignment:
    return GoldAssignment(
        claim_id=claim_id,
        theme_id=theme_id,
        support=support,
        tie_group=tie_group,
        origin=Origin.DRAFTED_ACCEPTED,
    )


def negative(
    claim_id: str, quote_id: str, kind: NegativeKind, theme_id: str | None
) -> HardNegative:
    return HardNegative(
        claim_id=claim_id,
        quote_ids=(quote_id,),
        claim="An invented claim its quote does not support.",
        negative_kind=kind,
        theme_id=theme_id,
        origin=Origin.DRAFTED_ACCEPTED,
    )


def reading(
    quotes=(),
    claims=(),
    assignments=(),
    negatives=(),
    label: ReleaseLabel = ReleaseLabel.RELEASE,
) -> Reading:
    return Reading(
        no_theme=False,
        release_identification=ReleaseIdentification(label=label, note="Invented."),
        quotes=tuple(quotes),
        claims=tuple(claims),
        assignments=tuple(assignments),
        hard_negatives=tuple(negatives),
    )


def example() -> tuple[Bundle, Reading]:
    """The known-answer reading: ``q1`` is part of P0, ``q2`` crosses P1 and P2,
    ``q3`` is P3. ``c1`` supports capacity; ``c2`` is tie group ``g1`` over demand
    and pricing; ``c3`` is only uncertain for labor and costs; ``c4`` does not
    support debt, and costs is also decided by ``c1``'s ``does_not_support``."""
    source = bundle()
    p0, p1, _, p3 = unit_ids(source)
    return source, reading(
        quotes=(
            quote("q1", 0, 5, p0),
            quote("q2", 30, 45, p1),
            quote("q3", 57, 73, p3),
        ),
        claims=(
            claim("c1", "q1"),
            claim("c2", "q2"),
            claim("c3", "q3"),
            claim("c4", "q1"),
        ),
        assignments=(
            row("c1", "capacity"),
            row("c1", "costs", Support.DOES_NOT_SUPPORT),
            row("c2", "demand", tie_group="g1"),
            row("c2", "pricing", tie_group="g1"),
            row("c3", "labor", Support.UNCERTAIN),
            row("c3", "costs", Support.UNCERTAIN),
            row("c4", "debt", Support.DOES_NOT_SUPPORT),
            row("c4", "unmatched"),
        ),
        negatives=(
            negative("n1", "q3", NegativeKind.PERIOD, "capacity"),
            negative("n2", "q1", NegativeKind.ISSUER, "demand"),
            negative("n3", "q2", NegativeKind.SECTION, None),
        ),
    )


def gold(event_id: str, base: Reading, partition: str = "dev", **changes) -> Gold:
    """``base`` as signed gold for ``event_id``, with invented bindings."""
    from datetime import date

    from earnings_themes.gold import CodebookRef, DraftCounts
    from earnings_themes.split import Partition
    from earnings_themes.synthetic import PIN

    fields = {
        "event_id": event_id,
        "document_id": f"{event_id}-doc",
        "doc_id": f"{event_id}@test-1#0000000000000000",
        "canonical_hash": HASH,
        "pin": PIN,
        "split_hash": HASH,
        "partition": Partition(partition),
        "codebook": CodebookRef(
            codebook_id="invented", codebook_version=0, content_hash=HASH
        ),
        "annotator": "Invented Annotator",
        "drafting_aid": {"model_id": "invented-aid", "drafted_on": date(2026, 10, 1)},
        "counts": DraftCounts(accepted=1, edited=0, rejected=0, added=0),
        "no_theme": False,
        **base.model_dump(exclude={"no_theme"}),
        **changes,
    }
    return Gold.model_validate(fields)


def trial(
    target_id: str,
    family: str,
    presentation: str,
    claim_support: str,
    theme_fit: str,
    quotes: tuple[str, ...] = (),
):
    """One available judge trial with invented identity and answer; each of
    ``quotes`` is assessed ``supporting``."""
    from earnings_themes.support.records import (
        JudgeAnswer,
        JudgeIdentity,
        JudgeTrial,
        Presentation,
        QuoteAssessment,
        RuntimeIdentity,
        SignalStatus,
    )

    return JudgeTrial(
        trial_id=f"{target_id}-{family}-{presentation}",
        target_id=target_id,
        identity=JudgeIdentity(
            family=family,
            runtime=RuntimeIdentity(
                model_id=f"{family}-model",
                revision="1",
                files=(),
                runtime="scripted",
                runtime_version="1",
                device="cpu",
                precision="float32",
                encoding_version="1",
            ),
            input_limit=1000,
            output_limit=100,
            hosting="scripted",
            weight_license=None,
        ),
        presentation=Presentation(presentation),
        attempt_ids=(f"{target_id}-{family}-{presentation}-1",),
        status=SignalStatus.AVAILABLE,
        answer=JudgeAnswer(
            claim_support=claim_support,
            theme_fit=theme_fit,
            joint_support_score=0.5,
            quote_assessments=tuple(
                QuoteAssessment(quote_id=q, contribution="supporting") for q in quotes
            ),
            reason_codes=(),
            summary="Invented summary.",
        ),
        reason=None,
    )


def panel(
    target_id: str,
    first: tuple[str, str],
    second: tuple[str, str],
    quotes: tuple[str, ...] = (),
):
    """Four trials: family ``f0`` answers ``first`` and ``f1`` answers ``second``,
    each under both presentations."""
    return tuple(
        trial(target_id, family, presentation, *answers, quotes)
        for family, answers in (("f0", first), ("f1", second))
        for presentation in ("evidence_first", "claim_theme_first")
    )


def decision_view(
    target_id: str, score: float, first: tuple[str, str], second: tuple[str, str]
):
    """An invented one-quote target's decision view, its outcome derived by Stage 8's
    ``derive_outcome`` and its eligible quotes by Stage 9's, never fabricated."""
    from earnings_core import digest
    from earnings_themes.coding.decide import DecisionInput, eligible_quote_ids
    from earnings_themes.support import derive_outcome
    from earnings_themes.support.records import (
        CodebookReference,
        EntailmentSignal,
        EvidenceReference,
        RuntimeIdentity,
        ScorerIdentity,
        SignalStatus,
        Target,
        TargetRecord,
    )

    quote_id = "q1"
    record = TargetRecord(
        target_id=target_id,
        target=Target(
            source_run_id="invented-run",
            doc_id="invented-doc",
            claim_id=f"{target_id}-claim",
            theme_id="capacity",
            codebook=CodebookReference(
                codebook_id="invented", codebook_version=0, content_hash=HASH
            ),
        ),
        source_run_hash=HASH,
        claim_hash=HASH,
        input_hash=digest(target_id),
        original_quote_ids=(quote_id,),
        evidence_ids=(f"{target_id}-{quote_id}",),
        theme=None,
    )
    evidence = (
        EvidenceReference(
            target_id=target_id,
            quote_id=quote_id,
            doc_id="invented-doc",
            canonical_hash=HASH,
            element_id="paragraph-0-20",
            start=0,
            end=20,
            text_hash=HASH,
            validator_version="3",
            mask_ids=(),
        ),
    )
    scorer = ScorerIdentity(
        kind="scripted",
        input_limit=1000,
        runtime=RuntimeIdentity(
            model_id="invented-scorer",
            revision="1",
            files=(),
            runtime="scripted",
            runtime_version="1",
            device="cpu",
            precision="float32",
            encoding_version="1",
        ),
    )
    entailment = tuple(
        EntailmentSignal(
            signal_id=f"{target_id}-{scope}",
            target_id=target_id,
            scope=scope,
            quote_id=quote,
            evaluation_id=f"{target_id}-{scope}",
            identity=scorer,
            input_hash=HASH,
            status=SignalStatus.AVAILABLE,
            score=score,
            reason=None,
            input_tokens=1,
            latency_ms=0,
            cached=False,
        )
        for scope, quote in (("quote", quote_id), ("joint", None))
    )
    trials = panel(target_id, first, second, (quote_id,))
    outcome = derive_outcome(target_id, entailment, trials, (quote_id,))
    eligible = (
        eligible_quote_ids(evidence, trials) if outcome.status == "assessed" else ()
    )
    return DecisionInput(record, evidence, entailment, trials, outcome, eligible)
```

Create `packages/earnings-themes/tests/evaluation/test_align.py`:

```python
"""Alignment: spans to pointer units by character overlap, and character Jaccard's
counts (the Stage 11 spec, A3; FP13)."""

from earnings_themes.evaluation.align import (
    char_overlap,
    covered,
    merged,
    unit_index,
    units_over,
)

from .cases import bundle, unit_ids


def test_each_paragraph_is_one_unit_in_document_order() -> None:
    source = bundle()
    index = unit_index(source)
    assert index.doc_id == source.document.doc_id
    assert [(s, e) for _, s, e in index.spans] == [
        (0, 20),
        (21, 37),
        (38, 56),
        (57, 73),
    ]


def test_a_span_maps_to_every_unit_it_shares_a_character_with() -> None:
    source = bundle()
    p0, p1, p2, p3 = unit_ids(source)
    index = unit_index(source)
    assert units_over(index, [(0, 5)]) == {p0}
    assert units_over(index, [(30, 45)]) == {p1, p2}
    assert units_over(index, [(20, 21)]) == set()
    assert units_over(index, [(19, 22)]) == {p0, p1}
    assert units_over(index, [(0, 5), (57, 73)]) == {p0, p3}


def test_spans_merge_and_count_each_character_once() -> None:
    assert merged([(5, 9), (0, 3), (2, 6), (12, 14)]) == ((0, 9), (12, 14))
    assert covered([(0, 5), (3, 8), (8, 10)]) == 10
    assert char_overlap([(0, 5), (57, 73)], [(0, 20)]) == (5, 36)
    assert char_overlap([(30, 45)], [(21, 37)]) == (7, 24)
    assert char_overlap([], []) == (0, 0)
```

In `packages/earnings-themes/tests/test_import_boundaries.py`, replace:

```python
    "earnings_themes.support",
    "earnings_themes.coding",
    "earnings_themes.analysis",
    "earnings_pipeline",
)
NLI_RUNTIME = {
```

with:

```python
    "earnings_themes.support",
    "earnings_themes.coding",
    "earnings_themes.analysis",
    "earnings_themes.evaluation",
    "earnings_pipeline",
)
NLI_RUNTIME = {
```

Append to the end of `packages/earnings-themes/tests/test_import_boundaries.py`, after two blank lines:

```python
def test_public_evaluation_import_loads_no_optional_adapter():
    """D19-4: evaluation imports pure Stage 7-9 code, never ingestion, httpx, an
    NLI runtime, or a concrete adapter."""
    modules = [m for m in MODULES if m.startswith("earnings_themes.evaluation")]
    loaded = modules_loaded_by(modules)
    assert top_level(loaded) & (FORBIDDEN | NLI_RUNTIME) == set()
    assert {
        LOCAL,
        "earnings_themes.support.nli",
        "earnings_themes.coding.local",
    }.isdisjoint(loaded)


def test_pipeline_scan_detects_planted_evaluation_import(tmp_path):
    package = tmp_path / "earnings_themes"
    package.mkdir()
    path = package / "gold.py"
    path.write_text("def later():\n    from .evaluation import labels\n")
    assert pipeline_imports(path) == [
        "earnings_themes.evaluation.labels",
        "earnings_themes.evaluation",
    ]
```

In `tests/contracts/test_data_dictionary.py`, replace:

```python
import re
from dataclasses import fields
```

with:

```python
import importlib
import pkgutil
import re
from dataclasses import fields, is_dataclass
```

In `tests/contracts/test_data_dictionary.py`, replace:

```python
from earnings_themes import annotation, codebook, gold, independent, problems, split
```

with:

```python
from earnings_themes import (
    annotation,
    codebook,
    evaluation,
    gold,
    independent,
    problems,
    split,
)
```

Keep the parentheses and the trailing comma: later tasks add a module to this block, and Ruff keeps it open.

In `tests/contracts/test_data_dictionary.py`, replace:

```python
from earnings_themes.coding.store import SCHEMAS
```

with:

```python
from earnings_themes.coding.store import SCHEMAS
from earnings_themes.evaluation import (
    align,
)
from earnings_themes.evaluation import problems as evaluation_problems
```

`EVALUATION_MODELS` starts empty: no evaluation model exists until Task 5, which adds the model test with the first ones.

Append to the end of `tests/contracts/test_data_dictionary.py`, after two blank lines:

```python
EVALUATION_MODELS: list[type[BaseModel]] = []
EVALUATION_ENUMS = [
    evaluation_problems.EvaluationProblem,
]
EVALUATION_DATACLASSES = [
    align.UnitIndex,
]


@pytest.mark.parametrize("enum", EVALUATION_ENUMS, ids=lambda e: e.__name__)
def test_evaluation_values_documented(enum: type[StrEnum]) -> None:
    assert documented(enum.__name__) == {member.value for member in enum}


@pytest.mark.parametrize("record", EVALUATION_DATACLASSES, ids=lambda r: r.__name__)
def test_evaluation_dataclass_fields_documented(record: type) -> None:
    assert documented(record.__name__) == {field.name for field in fields(record)}


def test_evaluation_registry_covers_every_defined_record_enum_and_dataclass() -> None:
    """A new evaluation record, enum or dataclass fails here until registered."""
    defined = {
        value
        for info in pkgutil.iter_modules(evaluation.__path__)
        for value in vars(
            importlib.import_module(f"{evaluation.__name__}.{info.name}")
        ).values()
        if isinstance(value, type)
        and value.__module__.startswith(f"{evaluation.__name__}.")
        and not value.__name__.startswith("_")
    }
    assert {v for v in defined if issubclass(v, BaseModel)} == set(EVALUATION_MODELS)
    assert {v for v in defined if issubclass(v, StrEnum)} == set(EVALUATION_ENUMS)
    assert {v for v in defined if is_dataclass(v)} == set(EVALUATION_DATACLASSES)
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_align.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`2 errors`), with `ImportError: cannot import name 'evaluation' from 'earnings_themes'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation'`.

- [x] **Step 3: Write the implementation**

Create `packages/earnings-themes/src/earnings_themes/evaluation/__init__.py`:

```python
"""Stage 11's evaluation: scoring the pilot, the user's support labels, and
calibration (the Stage 11 spec, A3–A5).

Pure: it reads no file, sends no request, loads no model and prints nothing. It
imports pure Stage 7–9 code and never ingestion, httpx, an NLI runtime or a concrete
adapter, and no gold-drafting module imports it (D19-4).
"""
```

Create `packages/earnings-themes/src/earnings_themes/evaluation/problems.py`:

```python
"""Why Stage 11's evaluation refused something (the Stage 11 spec, §Failure
handling).

A refusal names its subject by ID and gives a closed reason, never text (GS13).
Checks over a set return ``Refusal`` rows (``earnings_themes.problems``); a
computation that cannot go on raises ``EvaluationError``.
"""

from enum import StrEnum


class EvaluationProblem(StrEnum):
    """Stage 11's evaluation reasons."""

    MALFORMED_RECORD = "malformed_record"
    PARENT_CYCLE = "parent_cycle"
    WRONG_PARTITION = "wrong_partition"
    UNKNOWN_EVENT = "unknown_event"
    UNKNOWN_TARGET = "unknown_target"
    DUPLICATE_TARGET = "duplicate_target"
    TARGET_HASH_MISMATCH = "target_hash_mismatch"
    NOT_SAMPLED = "not_sampled"
    NOT_LABELLED = "not_labelled"
    LABELS_CHANGED = "labels_changed"
    PREREGISTRATION_MISMATCH = "preregistration_mismatch"
    CONTENT_HASH_MISMATCH = "content_hash_mismatch"
    TOO_FEW_LABELS = "too_few_labels"
    NO_CANDIDATE = "no_candidate"
    UNKNOWN_METRIC = "unknown_metric"


class EvaluationError(ValueError):
    """One refusal: its reason, and its subject's ID when it has one."""

    def __init__(self, problem: EvaluationProblem, subject: str = "") -> None:
        super().__init__(f"{subject}: {problem.value}" if subject else problem.value)
        self.problem = problem
        self.subject = subject
```

Create `packages/earnings-themes/src/earnings_themes/evaluation/align.py`:

```python
"""Gold and run quotes in pointer units, and their characters (the Stage 11 spec,
A3's alignment and FP13; ES12).

- **Units.** A span maps to every unit whose span shares at least one character
  with it. A run quote is a whole unit (ES12), so it maps to that unit; a gold quote
  may be part of a unit, or cross several.
- **Characters.** Spans are half-open ``[start, end)`` offsets into one document's
  canonical text. Character Jaccard is the characters two span sets share over the
  characters either covers.

Nothing here reads text, so nothing here can print it (GS13).
"""

from collections.abc import Iterable
from dataclasses import dataclass

from earnings_themes.anchoring import Bundle
from earnings_themes.extraction.units import units

type Span = tuple[int, int]


@dataclass(frozen=True)
class UnitIndex:
    """One document's units: each one's element ID, start and end, in document
    order."""

    doc_id: str
    spans: tuple[tuple[str, int, int], ...]


def unit_index(bundle: Bundle) -> UnitIndex:
    """The bundle's pointer units (ES12), by span."""
    return UnitIndex(
        bundle.document.doc_id,
        tuple((u.element_id, u.span.start, u.span.end) for u in units(bundle)),
    )


def units_over(index: UnitIndex, spans: Iterable[Span]) -> frozenset[str]:
    """The units sharing at least one character with any of ``spans``."""
    found: set[str] = set()
    for start, end in spans:
        found.update(e for e, s, t in index.spans if s < end and start < t)
    return frozenset(found)


def merged(spans: Iterable[Span]) -> tuple[Span, ...]:
    """The union of ``spans``, as sorted, disjoint spans."""
    out: list[list[int]] = []
    for start, end in sorted(spans):
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return tuple((start, end) for start, end in out)


def covered(spans: Iterable[Span]) -> int:
    """How many characters ``spans`` cover, each counted once."""
    return sum(end - start for start, end in merged(spans))


def char_overlap(a: Iterable[Span], b: Iterable[Span]) -> tuple[int, int]:
    """The characters ``a`` and ``b`` share, and the characters either covers."""
    a, b = tuple(a), tuple(b)
    union = covered((*a, *b))
    return covered(a) + covered(b) - union, union
```

Append to the end of `docs/data-dictionary.md`, after one blank line:

```markdown
## Stage 11 evaluation (plan 19)

`earnings_themes.evaluation` scores the pilot, samples and checks the user's support
labels, and calibrates the assignment policy (the Stage 11 spec, A3–A5). It reads no
file and prints nothing; the application gathers its inputs (A8). It imports pure
Stage 7–9 code (`extraction.units`, `support.metrics`, `support.context`,
`coding.decide`), never ingestion, httpx, an NLI runtime or the local adapter, and
no gold-drafting module imports it (D19-4). A refusal is an `EvaluationError`, or a
`Refusal` row, naming an ID and an `EvaluationProblem`, never text.

Scoring conventions (FP20, D19-3, D19-6, D19-7, D19-8, D19-9): a span maps to every
pointer unit it shares a character with. A theme is present in an event when a gold
assignment pairs it with a claim under `supports`. A tie group resolves to a member
the run predicted, else one already present, else its lowest theme ID, and its
other members are excused. A theme whose every row is `uncertain` is left out and
counted. A reference to a quote or claim the reading lacks is counted as dangling.
The roll-up maps both sides to level-one roots. Gold-evidence recall counts the
gold-supporting units any accepted assignment holds. GS5's edited and rejected
shares are over drafted items, and the added share over signed items. Every
interval is the event-clustered percentile bootstrap.

### `EvaluationProblem`

| Value | Meaning |
| --- | --- |
| `malformed_record` | A record or input that does not have the expected shape |
| `parent_cycle` | A codebook whose parents loop |
| `wrong_partition` | A record or label of another partition, or a partition never reported |
| `unknown_event` | A target or label whose event is not among the inputs |
| `unknown_target` | A label or sample ID the support run does not hold |
| `duplicate_target` | A target ID given twice |
| `target_hash_mismatch` | A label whose input hash is not the support run's |
| `not_sampled` | A label for a target outside the sample |
| `not_labelled` | A sampled target with no label |
| `labels_changed` | Committed labels that a working file would change |
| `preregistration_mismatch` | A record bound to another preregistration, or one that no longer hashes to itself |
| `content_hash_mismatch` | A frozen record that does not hash to its `content_hash` |
| `too_few_labels` | Fewer usable train joint labels than preregistered (R8.4) |
| `no_candidate` | A calibration artifact with no selection, which binds no policy |
| `unknown_metric` | A metric the report does not hold |

### `UnitIndex`

| Field | Meaning |
| --- | --- |
| `doc_id` | The document |
| `spans` | Each pointer unit's element ID, start and end, in document order (ES12) |
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_align.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `379 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/__init__.py packages/earnings-themes/tests/evaluation/cases.py packages/earnings-themes/tests/evaluation/test_align.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/__init__.py packages/earnings-themes/src/earnings_themes/evaluation/problems.py packages/earnings-themes/src/earnings_themes/evaluation/align.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/__init__.py packages/earnings-themes/tests/evaluation/cases.py packages/earnings-themes/tests/evaluation/test_align.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/__init__.py packages/earnings-themes/src/earnings_themes/evaluation/problems.py packages/earnings-themes/src/earnings_themes/evaluation/align.py docs/data-dictionary.md
git commit -m "feat(themes): evaluation package, refusals and pointer-unit alignment (A3)"
```

---

### Task 3: `cells`: a gold reading's event × theme cells (A3; FP20, D19-6, D19-7)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_cells.py`
- Modify: `tests/contracts/test_data_dictionary.py` (imports; the evaluation registry)
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/cells.py`
- Modify: `docs/data-dictionary.md` (the evaluation section: `EventCells`)

**Interfaces:**
- Consumes:
  - from Task 2: `align.Span`, `align.UnitIndex`, `align.unit_index`, `align.units_over`, `problems.EvaluationError`, `problems.EvaluationProblem`, `tests/evaluation/cases.py: claim`, `tests/evaluation/cases.py: example`, `tests/evaluation/cases.py: quote`, `tests/evaluation/cases.py: reading`, `tests/evaluation/cases.py: row`, `tests/evaluation/cases.py: unit_ids`
  - existing at `7948d94`: `earnings_themes.codebook`: `Codebook`, `UNMATCHED`; `earnings_themes.gold`: `GoldAssignment`, `GoldClaim`, `GoldQuote`, `HardNegative`, `Support`
- Produces:
  - In `earnings_themes.evaluation.cells`:
    - `class GoldReading(Protocol)`: methods `.quotes() -> tuple[GoldQuote, ...]`, `.claims() -> tuple[GoldClaim, ...]`, `.assignments() -> tuple[GoldAssignment, ...]`, `.hard_negatives() -> tuple[HardNegative, ...]`
    - `class EventCells` (frozen dataclass): fields `present: frozenset[str]`, `excused: frozenset[str]`, `uncertain: frozenset[str]`, `units: Mapping[str, frozenset[str]]`, `spans: Mapping[str, tuple[Span, ...]]`, `dangling: int`; methods `.scored(theme_id: str) -> bool`
    - `level_one(codebook: Codebook) -> dict[str, str]`
    - `event_cells(reading: GoldReading, index: UnitIndex, predicted: Iterable[str]=(), theme_map: Mapping[str, str] | None=None) -> EventCells`

`event_cells` reads one gold reading into the event's theme cells, under FP20's conventions. The reading is signed `Gold`, or an independent `Reading`, through the `GoldReading` protocol.
- A theme is present when a `supports` row pairs it with a claim (P9-4).
- A tie group is one either-of cell, resolved as D19-6 says. Its other members are excused.
- A theme whose every row is `uncertain` is left out and counted.
- A dangling reference is counted, never refused (D19-7).

`level_one` gives each theme's level-one root for the roll-up (D19-3), and refuses a parent cycle.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_cells.py`:

```python
"""Gold cells under FP20's conventions, with known answers (the Stage 11 spec,
§Metrics; R12.6)."""

from types import SimpleNamespace

import pytest
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.cells import event_cells, level_one
from earnings_themes.evaluation.problems import EvaluationError

from .cases import claim, example, quote, reading, row, unit_ids


def test_present_excused_uncertain_and_evidence_with_the_tie_predicted() -> None:
    source, gold = example()
    p0, p1, p2, _ = unit_ids(source)
    cells = event_cells(gold, unit_index(source), predicted={"pricing", "labor"})
    assert cells.present == {"capacity", "pricing"}
    assert cells.excused == {"demand"}
    assert cells.uncertain == {"labor"}
    assert cells.units == {"capacity": {p0}, "pricing": {p1, p2}}
    assert cells.spans == {"capacity": ((0, 5),), "pricing": ((30, 45),)}
    assert cells.dangling == 0


def test_an_unpredicted_tie_group_resolves_to_its_lowest_member() -> None:
    source, gold = example()
    cells = event_cells(gold, unit_index(source))
    assert cells.present == {"capacity", "demand"}
    assert cells.excused == {"pricing"}


def test_a_tie_group_resolves_to_a_member_already_present() -> None:
    source, base = example()
    gold = base.model_copy(
        update={
            "claims": (*base.claims, claim("c5", "q3")),
            "assignments": (
                *base.assignments,
                row("c5", "capacity", tie_group="g2"),
                row("c5", "labor", tie_group="g2"),
            ),
        }
    )
    p0, _, _, p3 = unit_ids(source)
    cells = event_cells(gold, unit_index(source))
    assert "labor" in cells.excused and "labor" not in cells.uncertain
    assert cells.units["capacity"] == {p0, p3}


def test_dangling_references_are_counted_and_add_nothing() -> None:
    source, _ = example()
    p0 = unit_ids(source)[0]
    gold = reading(
        quotes=(quote("q1", 0, 5, p0),),
        claims=(claim("c1", "q1", "q9"),),
        assignments=(row("c1", "capacity"), row("c8", "capacity")),
    )
    cells = event_cells(gold, unit_index(source))
    assert cells.units == {"capacity": {p0}}
    assert cells.dangling == 2


def test_level_one_maps_each_theme_to_its_root() -> None:
    book = SimpleNamespace(
        themes=(
            SimpleNamespace(theme_id="capital", parent_id=None),
            SimpleNamespace(theme_id="capex", parent_id="capital"),
            SimpleNamespace(theme_id="buybacks", parent_id="capital"),
            SimpleNamespace(theme_id="pricing", parent_id=None),
        )
    )
    assert level_one(book) == {
        "capital": "capital",
        "capex": "capital",
        "buybacks": "capital",
        "pricing": "pricing",
    }
    loop = SimpleNamespace(
        themes=(
            SimpleNamespace(theme_id="a", parent_id="b"),
            SimpleNamespace(theme_id="b", parent_id="a"),
        )
    )
    with pytest.raises(EvaluationError, match="parent_cycle"):
        level_one(loop)
```

In `tests/contracts/test_data_dictionary.py`, add `cells,` to the `from earnings_themes.evaluation import (...)` block, in alphabetical order.

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_DATACLASSES`:

```python
    cells.EventCells,
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_cells.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`2 errors`), with `ImportError: cannot import name 'cells' from 'earnings_themes.evaluation'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.cells'`.

- [x] **Step 3: Write the implementation**
> Deviation (final review, 2026-10-13): `cells.event_cells` counts one `dangling` per claim-to-missing-quote reference and per assignment row citing a missing claim, whatever its support, theme or tie (D19-7), not only claims supporting a present theme; it also returns `EventCells.evidence`, one new `EvidenceCell(themes, units, spans)` per untied present theme and per tie group, so unit and character scoring treat a tie group as one either-of cell (FP20); `GoldReading` gains `release_identification`.

Create `packages/earnings-themes/src/earnings_themes/evaluation/cells.py`:

```python
"""Gold presence and evidence per event and theme, under Stage 11's conventions
(the Stage 11 spec, §Metrics and FP20; P9-4; R12.6).

- **Present.** A theme is present in an event when an assignment pairs it with a
  claim under ``supports``. ``unmatched`` is never a theme (P9-4).
- **Tie groups.** Rows sharing a ``tie_group`` are alternatives for one claim
  (R12.6), one either-of cell. The group resolves to a supporting member the run
  predicted, else to one already present, else to its lowest theme ID. Its other
  members are excused, so predicting one is not a false positive (D19-6).
- **Uncertain only.** A theme whose every gold row is ``uncertain`` is left out of
  scoring and counted (FP20).
- **Evidence.** A present theme's gold spans are the quotes of the claims that
  support it, after the tie groups resolve. A reference to a quote or a claim that
  the reading does not hold is counted as ``dangling`` and adds nothing, so a kept
  draft is compared as drafted (P17-5(2), D19-7).
- **Roll-up.** ``theme_map`` maps every theme before anything else; ``level_one``
  maps each theme to its root, on both sides (D19-3).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol

from earnings_themes.codebook import UNMATCHED, Codebook
from earnings_themes.evaluation.align import Span, UnitIndex, units_over
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.gold import (
    GoldAssignment,
    GoldClaim,
    GoldQuote,
    HardNegative,
    Support,
)


class GoldReading(Protocol):
    """What scoring reads from signed gold or an anchored reading (A6(3))."""

    @property
    def quotes(self) -> tuple[GoldQuote, ...]: ...

    @property
    def claims(self) -> tuple[GoldClaim, ...]: ...

    @property
    def assignments(self) -> tuple[GoldAssignment, ...]: ...

    @property
    def hard_negatives(self) -> tuple[HardNegative, ...]: ...


@dataclass(frozen=True)
class EventCells:
    """One event's gold cells: the present themes, each with its gold units and
    spans; the excused and uncertain-only themes; and the dangling references."""

    present: frozenset[str]
    excused: frozenset[str]
    uncertain: frozenset[str]
    units: Mapping[str, frozenset[str]]
    spans: Mapping[str, tuple[Span, ...]]
    dangling: int

    def scored(self, theme_id: str) -> bool:
        """Whether a prediction of ``theme_id`` is scored at all."""
        return theme_id in self.present or (
            theme_id not in self.excused and theme_id not in self.uncertain
        )


def level_one(codebook: Codebook) -> dict[str, str]:
    """Each theme's level-one ancestor: its root, or itself (D19-3)."""
    parents = {theme.theme_id: theme.parent_id for theme in codebook.themes}
    roots: dict[str, str] = {}
    for theme_id in parents:
        current, seen = theme_id, {theme_id}
        while (parent := parents.get(current)) is not None:
            if parent in seen:
                raise EvaluationError(EvaluationProblem.PARENT_CYCLE, theme_id)
            current = parent
            seen.add(current)
        roots[theme_id] = current
    return roots


def event_cells(
    reading: GoldReading,
    index: UnitIndex,
    predicted: Iterable[str] = (),
    theme_map: Mapping[str, str] | None = None,
) -> EventCells:
    """``reading``'s cells over ``index``, with its tie groups resolved against
    ``predicted``, whose themes ``theme_map`` has already mapped."""

    def mapped(theme_id: str) -> str:
        return theme_id if theme_map is None else theme_map.get(theme_id, theme_id)

    predicted = frozenset(predicted)
    quotes = {q.quote_id: (q.start, q.end) for q in reading.quotes}
    claims = {c.claim_id: c.quote_ids for c in reading.claims}
    dangling = sum(q not in quotes for ids in claims.values() for q in ids)
    rows = [
        (a.claim_id, mapped(a.theme_id), a.support, a.tie_group)
        for a in reading.assignments
        if a.theme_id != UNMATCHED
    ]
    supporting: dict[str, set[str]] = {}
    groups: dict[str, tuple[str, set[str]]] = {}
    for claim_id, theme_id, support, group in rows:
        if support is not Support.SUPPORTS:
            continue
        if group is None:
            supporting.setdefault(theme_id, set()).add(claim_id)
        else:
            groups.setdefault(group, (claim_id, set()))[1].add(theme_id)
    present_untied = set(supporting)
    excused: set[str] = set()
    for group in sorted(groups):
        claim_id, members = groups[group]
        candidates = (members & predicted) or (members & present_untied) or members
        chosen = min(candidates)
        supporting.setdefault(chosen, set()).add(claim_id)
        excused |= members - {chosen}
    present = frozenset(supporting)
    decided = {
        theme for _, theme, support, _ in rows if support is not Support.UNCERTAIN
    }
    uncertain = {theme for _, theme, _, _ in rows} - decided - present - excused
    spans: dict[str, tuple[Span, ...]] = {}
    for theme_id, claim_ids in supporting.items():
        dangling += sum(c not in claims for c in claim_ids)
        found = {quotes[q] for c in claim_ids for q in claims.get(c, ()) if q in quotes}
        spans[theme_id] = tuple(sorted(found))
    return EventCells(
        present=present,
        excused=frozenset(excused - present),
        uncertain=frozenset(uncertain),
        units={t: units_over(index, s) for t, s in spans.items()},
        spans=spans,
        dangling=dangling,
    )
```

Append to the end of `docs/data-dictionary.md`, after one blank line:

```markdown
### `EventCells`

| Field | Meaning |
| --- | --- |
| `present` | Themes present in the event, after tie groups resolve |
| `excused` | A resolved tie group's other members: predicting one is not a false positive |
| `uncertain` | Themes whose every gold row is `uncertain`: left out, counted |
| `units` | Each present theme's gold-supporting units |
| `spans` | Each present theme's gold-supporting spans |
| `dangling` | References to quotes or claims the reading lacks |
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_cells.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `382 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_cells.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/cells.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_cells.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/cells.py docs/data-dictionary.md
git commit -m "feat(themes): gold event-by-theme cells with tie groups and level-one roots (A3)"
```

---

### Task 4: `scores`: tallies and count figures (A3; D19-8, D19-9)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_scores.py`
- Modify: `tests/contracts/test_data_dictionary.py` (imports; the evaluation registry)
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/scores.py`
- Modify: `docs/data-dictionary.md` (the evaluation section: `Tally`)

**Interfaces:**
- Consumes:
  - from Task 2: `align.Span`, `align.UnitIndex`, `align.char_overlap`, `align.unit_index`, `align.units_over`, `tests/evaluation/cases.py: claim`, `tests/evaluation/cases.py: example`, `tests/evaluation/cases.py: quote`, `tests/evaluation/cases.py: reading`, `tests/evaluation/cases.py: row`, `tests/evaluation/cases.py: unit_ids`
  - from Task 3: `cells.EventCells`, `cells.GoldReading`, `cells.event_cells`
  - existing at `7948d94`: `earnings_themes.gold`: `DraftCounts`, `NegativeKind`, `ReleaseLabel`
- Produces:
  - In `earnings_themes.evaluation.scores`:
    - `class Tally` (frozen dataclass): fields `tp: int = 0`, `fp: int = 0`, `fn: int = 0`
    - `ratio(numerator: int, denominator: int) -> float | None`
    - `precision(tally: Tally) -> float | None`
    - `recall(tally: Tally) -> float | None`
    - `f1(tally: Tally) -> float | None`
    - `total(tallies: Iterable[Tally]) -> Tally`
    - `theme_tallies(cells: EventCells, predicted: Iterable[str]) -> dict[str, Tally]`
    - `per_theme(events: Iterable[Mapping[str, Tally]]) -> dict[str, Tally]`
    - `macro_f1(themes: Mapping[str, Tally]) -> float | None`
    - `rare_themes(events: Iterable[EventCells], most: int=2) -> frozenset[str]`
    - `unit_tally(cells: EventCells, accepted_units: Mapping[str, frozenset[str]]) -> Tally`
    - `char_counts(cells: EventCells, accepted_spans: Mapping[str, tuple[Span, ...]]) -> tuple[int, int]`
    - `evidence_recall_counts(cells: EventCells, accepted_units: Mapping[str, frozenset[str]]) -> tuple[int, int]`
    - `hard_negative_counts(reading: GoldReading, index: UnitIndex, accepted_units: Mapping[str, frozenset[str]]) -> dict[NegativeKind, tuple[int, int]]`
    - `release_tally(confirmed: bool, label: ReleaseLabel) -> Tally | None`
    - `gs5_shares(counts: Iterable[DraftCounts]) -> dict[str, float | None]`

`scores` turns cells and predictions into the tallies and counts that `report` combines:
- theme hits;
- unit and character overlap, over the cells present or predicted;
- theme-agnostic gold-evidence recall (D19-8);
- hard-negative false acceptances, by kind;
- release identification;
- rare themes, those with gold in 2 or fewer events;
- GS5's shares (D19-9).

Every known answer is hand-computed over `cases.example()`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_scores.py`:

```python
"""Per-event counts and their figures, with hand-computed known answers (the Stage
11 spec, §Metrics; R12.5, R12.8, R13.1)."""

import pytest
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.cells import event_cells
from earnings_themes.evaluation.scores import (
    Tally,
    char_counts,
    evidence_recall_counts,
    f1,
    gs5_shares,
    hard_negative_counts,
    macro_f1,
    per_theme,
    precision,
    rare_themes,
    recall,
    release_tally,
    theme_tallies,
    total,
    unit_tally,
)
from earnings_themes.gold import DraftCounts, NegativeKind, ReleaseLabel

from .cases import claim, example, quote, reading, row, unit_ids


def test_exact_cells_skip_excused_and_uncertain_predictions() -> None:
    """Both tie members predicted: the lower resolves the group, and the other is
    excused, not a false positive."""
    source, gold = example()
    predicted = {"pricing", "labor", "debt", "demand"}
    cells = event_cells(gold, unit_index(source), predicted)
    assert theme_tallies(cells, predicted) == {
        "capacity": Tally(fn=1),
        "debt": Tally(fp=1),
        "demand": Tally(tp=1),
    }


def test_micro_and_macro_f1_over_two_events() -> None:
    first = {"capacity": Tally(fn=1), "debt": Tally(fp=1), "pricing": Tally(tp=1)}
    second = {"capacity": Tally(tp=1), "demand": Tally(fp=1)}
    micro = total(t for event in (first, second) for t in event.values())
    assert micro == Tally(tp=2, fp=2, fn=1)
    assert precision(micro) == 0.5
    assert recall(micro) == pytest.approx(2 / 3)
    assert f1(micro) == pytest.approx(4 / 7)
    themes = per_theme((first, second))
    assert themes["capacity"] == Tally(tp=1, fn=1)
    assert macro_f1(themes) == pytest.approx((2 / 3 + 0 + 1 + 0) / 4)


def test_empty_denominators_are_none_never_zero() -> None:
    assert precision(Tally(fn=3)) is None
    assert recall(Tally(fp=3)) is None
    assert f1(Tally()) is None
    assert macro_f1({}) is None


def test_the_roll_up_maps_both_sides_to_level_one_so_siblings_meet() -> None:
    source, _ = example()
    p0 = unit_ids(source)[0]
    gold = reading(
        quotes=(quote("q1", 0, 5, p0),),
        claims=(claim("c1", "q1"),),
        assignments=(row("c1", "capex"),),
    )
    roots = {"capital": "capital", "capex": "capital", "buybacks": "capital"}
    exact = event_cells(gold, unit_index(source), {"buybacks"})
    assert theme_tallies(exact, {"buybacks"}) == {
        "buybacks": Tally(fp=1),
        "capex": Tally(fn=1),
    }
    rolled = {roots["buybacks"]}
    up = event_cells(gold, unit_index(source), rolled, theme_map=roots)
    assert theme_tallies(up, rolled) == {"capital": Tally(tp=1)}


def test_unit_and_character_overlap_over_present_and_predicted_cells() -> None:
    source, gold = example()
    p0, p1, _, p3 = unit_ids(source)
    cells = event_cells(gold, unit_index(source), {"pricing", "capacity"})
    accepted_units = {"pricing": frozenset({p1}), "capacity": frozenset({p0, p3})}
    assert unit_tally(cells, accepted_units) == Tally(tp=2, fp=1, fn=1)
    assert f1(unit_tally(cells, accepted_units)) == pytest.approx(2 / 3)
    spans = {"pricing": ((21, 37),), "capacity": ((0, 20), (57, 73))}
    assert char_counts(cells, spans) == (12, 60)


def test_uncertain_only_predictions_add_no_extra_units() -> None:
    """``labor`` is uncertain only; the unpredicted tie resolves to demand."""
    source, gold = example()
    p3 = unit_ids(source)[3]
    cells = event_cells(gold, unit_index(source), {"labor"})
    assert unit_tally(cells, {"labor": frozenset({p3})}) == Tally(fn=3)


def test_gold_evidence_recall_counts_units_whatever_their_theme() -> None:
    source, gold = example()
    p0, p1, _, p3 = unit_ids(source)
    cells = event_cells(gold, unit_index(source), {"pricing"})
    accepted = {"debt": frozenset({p0, p3}), "pricing": frozenset({p1})}
    assert evidence_recall_counts(cells, accepted) == (2, 3)
    assert evidence_recall_counts(cells, {}) == (0, 3)


def test_hard_negatives_by_kind() -> None:
    source, gold = example()
    p0, _, _, p3 = unit_ids(source)
    accepted = {"capacity": frozenset({p0, p3})}
    assert hard_negative_counts(gold, unit_index(source), accepted) == {
        NegativeKind.PERIOD: (1, 1),
        NegativeKind.ISSUER: (1, 0),
    }


def test_release_identification_leaves_ambiguous_out() -> None:
    assert release_tally(True, ReleaseLabel.RELEASE) == Tally(tp=1)
    assert release_tally(True, ReleaseLabel.NOT_RELEASE) == Tally(fp=1)
    assert release_tally(False, ReleaseLabel.RELEASE) == Tally(fn=1)
    assert release_tally(False, ReleaseLabel.NOT_RELEASE) == Tally()
    assert release_tally(True, ReleaseLabel.AMBIGUOUS) is None


def test_gs5_shares_over_summed_counts() -> None:
    counts = (
        DraftCounts(accepted=6, edited=2, rejected=2, added=1),
        DraftCounts(accepted=4, edited=1, rejected=0, added=3),
    )
    shares = gs5_shares(counts)
    assert shares["edited"] == pytest.approx(3 / 15)
    assert shares["rejected"] == pytest.approx(2 / 15)
    assert shares["added"] == pytest.approx(4 / 17)
    assert gs5_shares(()) == {"edited": None, "rejected": None, "added": None}


def test_rare_themes_are_present_in_at_most_two_events() -> None:
    source, _ = example()
    p0 = unit_ids(source)[0]
    index = unit_index(source)

    def present(*themes: str):
        gold = reading(
            quotes=(quote("q1", 0, 5, p0),),
            claims=(claim("c1", "q1"),),
            assignments=tuple(row("c1", t) for t in themes),
        )
        return event_cells(gold, index)

    events = (present("a", "b"), present("a"), present("a", "c"))
    assert rare_themes(events) == {"b", "c"}
```

In `tests/contracts/test_data_dictionary.py`, add `scores,` to the `from earnings_themes.evaluation import (...)` block, in alphabetical order.

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_DATACLASSES`:

```python
    scores.Tally,
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_scores.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`2 errors`), with `ImportError: cannot import name 'scores' from 'earnings_themes.evaluation'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.scores'`.

- [x] **Step 3: Write the implementation**
> Deviation (final review): `unit_tally` and `char_counts` return a new frozen `EvidenceTally(accepted_hits, accepted, gold_hits, gold)` instead of `Tally` and a `(shared, union)` pair, so one accepted item is one hit however many cells hold it; precision, recall, F1 and Jaccard come from it. `Tally` stays for theme and release tallies. No-tie readings score as the plan's code did.

Create `packages/earnings-themes/src/earnings_themes/evaluation/scores.py`:

```python
"""Stage 11's per-event counts, and the figures they combine into (the Stage 11
spec, §Metrics; R12.8, R13.1).

Each function scores one event. A partition's figure sums its events' counts, so the
event-clustered bootstrap (``bootstrap.py``) resamples whole events. A figure with an
empty denominator is ``None``, never zero (A §Non-negotiables: never coerce null).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from earnings_themes.evaluation.align import Span, UnitIndex, char_overlap, units_over
from earnings_themes.evaluation.cells import EventCells, GoldReading
from earnings_themes.gold import DraftCounts, NegativeKind, ReleaseLabel


@dataclass(frozen=True)
class Tally:
    """Hits, false positives, and misses."""

    tp: int = 0
    fp: int = 0
    fn: int = 0

    def __add__(self, other: "Tally") -> "Tally":
        return Tally(self.tp + other.tp, self.fp + other.fp, self.fn + other.fn)


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def precision(tally: Tally) -> float | None:
    return ratio(tally.tp, tally.tp + tally.fp)


def recall(tally: Tally) -> float | None:
    return ratio(tally.tp, tally.tp + tally.fn)


def f1(tally: Tally) -> float | None:
    return ratio(2 * tally.tp, 2 * tally.tp + tally.fp + tally.fn)


def total(tallies: Iterable[Tally]) -> Tally:
    return sum(tallies, Tally())


def theme_tallies(cells: EventCells, predicted: Iterable[str]) -> dict[str, Tally]:
    """One event's theme cells: each present theme a hit or a miss, each other
    scored prediction a false positive. Excused and uncertain-only cells score
    nothing (FP20)."""
    predicted = frozenset(predicted)
    return {
        theme: Tally(tp=1)
        if theme in cells.present and theme in predicted
        else Tally(fn=1)
        if theme in cells.present
        else Tally(fp=1)
        for theme in sorted(cells.present | predicted)
        if cells.scored(theme)
    }


def per_theme(events: Iterable[Mapping[str, Tally]]) -> dict[str, Tally]:
    """Each theme's counts, summed over events."""
    out: dict[str, Tally] = {}
    for tallies in events:
        for theme, tally in tallies.items():
            out[theme] = out.get(theme, Tally()) + tally
    return out


def macro_f1(themes: Mapping[str, Tally]) -> float | None:
    """The mean F1 over themes with gold or a prediction; ``themes`` holds only
    those, so each one's F1 is defined."""
    values = [value for value in map(f1, themes.values()) if value is not None]
    return sum(values) / len(values) if values else None


def rare_themes(events: Iterable[EventCells], most: int = 2) -> frozenset[str]:
    """The themes present in at most ``most`` of a partition's events (D1)."""
    seen: dict[str, int] = {}
    for cells in events:
        for theme in cells.present:
            seen[theme] = seen.get(theme, 0) + 1
    return frozenset(theme for theme, n in seen.items() if n <= most)


def unit_tally(
    cells: EventCells, accepted_units: Mapping[str, frozenset[str]]
) -> Tally:
    """One event's evidence units over its present and predicted cells: units in
    both, units only accepted, and gold units missed (FP13)."""
    tally = Tally()
    for theme in sorted(cells.present | accepted_units.keys()):
        if not cells.scored(theme):
            continue
        gold = cells.units.get(theme, frozenset())
        got = accepted_units.get(theme, frozenset())
        tally += Tally(len(gold & got), len(got - gold), len(gold - got))
    return tally


def char_counts(
    cells: EventCells, accepted_spans: Mapping[str, tuple[Span, ...]]
) -> tuple[int, int]:
    """One event's shared and union characters over the same cells as
    ``unit_tally``, for character Jaccard."""
    shared = union = 0
    for theme in sorted(cells.present | accepted_spans.keys()):
        if not cells.scored(theme):
            continue
        both, either = char_overlap(
            cells.spans.get(theme, ()), accepted_spans.get(theme, ())
        )
        shared, union = shared + both, union + either
    return shared, union


def evidence_recall_counts(
    cells: EventCells, accepted_units: Mapping[str, frozenset[str]]
) -> tuple[int, int]:
    """Gold-evidence recall's counts (R12.8 (iii)): the gold-supporting units that
    any accepted assignment holds, and all gold-supporting units (D19-8)."""
    gold = frozenset().union(*cells.units.values())
    got = frozenset().union(*accepted_units.values())
    return len(gold & got), len(gold)


def hard_negative_counts(
    reading: GoldReading,
    index: UnitIndex,
    accepted_units: Mapping[str, frozenset[str]],
) -> dict[NegativeKind, tuple[int, int]]:
    """Per negative kind (R12.5): the hard negatives that name a theme, and those
    falsely accepted, by an accepted assignment to that theme whose evidence units
    overlap the negative's."""
    quotes = {q.quote_id: (q.start, q.end) for q in reading.quotes}
    out: dict[NegativeKind, tuple[int, int]] = {}
    for negative in reading.hard_negatives:
        if negative.theme_id is None:
            continue
        own = units_over(index, (quotes[q] for q in negative.quote_ids if q in quotes))
        hit = bool(own & accepted_units.get(negative.theme_id, frozenset()))
        named, accepted = out.get(negative.negative_kind, (0, 0))
        out[negative.negative_kind] = (named + 1, accepted + hit)
    return out


def release_tally(confirmed: bool, label: ReleaseLabel) -> Tally | None:
    """Release identification's cell: the system's confirmed release against the
    gold label; ``ambiguous`` is left out and counted (R13.1)."""
    if label is ReleaseLabel.AMBIGUOUS:
        return None
    gold = label is ReleaseLabel.RELEASE
    return Tally(
        tp=int(confirmed and gold),
        fp=int(confirmed and not gold),
        fn=int(gold and not confirmed),
    )


def gs5_shares(counts: Iterable[DraftCounts]) -> dict[str, float | None]:
    """GS5's shares over summed counts: edited and rejected over drafted items,
    added over signed items (D19-9)."""
    rows = list(counts)
    accepted = sum(c.accepted for c in rows)
    edited = sum(c.edited for c in rows)
    rejected = sum(c.rejected for c in rows)
    added = sum(c.added for c in rows)
    drafted = accepted + edited + rejected
    return {
        "edited": ratio(edited, drafted),
        "rejected": ratio(rejected, drafted),
        "added": ratio(added, accepted + edited + added),
    }
```

Append to the end of `docs/data-dictionary.md`, after one blank line:

```markdown
### `Tally`

| Field | Meaning |
| --- | --- |
| `tp` | Hits |
| `fp` | False positives |
| `fn` | Misses |
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_scores.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `389 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_scores.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/scores.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_scores.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/scores.py docs/data-dictionary.md
git commit -m "feat(themes): evaluation tallies and count figures (A3)"
```

---

### Task 5: `agreement` and `bootstrap` (A3; D19-10)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_agreement.py`
- Create: `packages/earnings-themes/tests/evaluation/test_bootstrap.py`
- Modify: `tests/contracts/test_data_dictionary.py` (imports; the evaluation registry)
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/agreement.py`
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/bootstrap.py`
- Modify: `docs/data-dictionary.md` (the evaluation section: `BootstrapPlan`, `Interval`, `Estimate`)

**Interfaces:**
- Consumes:
  - from Task 2: `problems.EvaluationError`, `problems.EvaluationProblem`
  - existing at `7948d94`: `earnings_themes.records`: `Part`
- Produces:
  - In `earnings_themes.evaluation.agreement`:
    - `cohen_kappa(pairs: Sequence[tuple[int, int]]) -> float | None`
    - `gwet_ac1(pairs: Sequence[tuple[int, int]]) -> float | None`
    - `fleiss_kappa(ratings: Sequence[Sequence[int]]) -> float | None`
  - In `earnings_themes.evaluation.bootstrap`:
    - `class BootstrapPlan(Part)`: fields `seed: int`, `resamples: PositiveInt`, `level: float = Field(gt=0, lt=1)`, `max_undefined_share: float = Field(ge=0, lt=1)`
    - `class Interval(Part)`: fields `lower: float | None`, `upper: float | None`, `level: float`, `resamples: PositiveInt`, `undefined: NonNegativeInt`
    - `class Estimate(Part)`: fields `point: float | None`, `interval: Interval`
    - `estimate(per_event: Mapping[str, T], statistic: Callable[[Sequence[T]], float | None], plan: BootstrapPlan) -> Estimate`

`agreement` computes Cohen's κ and Gwet's AC1 over binary pairs, and Fleiss' κ over rater rows. Each returns `None` when it is undefined.

`bootstrap.estimate` resamples events with replacement under the preregistered seed. It skips and counts an undefined resample (D19-10), and reports the percentile interval, or no bounds when too many resamples are undefined. The dictionary's model test starts here, with the first evaluation models.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_agreement.py`:

```python
"""κ, AC1 and Fleiss' κ, with hand-computed known answers (the Stage 11 spec, A3)."""

import pytest
from earnings_themes.evaluation.agreement import cohen_kappa, fleiss_kappa, gwet_ac1
from earnings_themes.evaluation.problems import EvaluationError

PAIRS = [(1, 1)] * 20 + [(1, 0)] * 5 + [(0, 1)] * 10 + [(0, 0)] * 15
"""Observed 0.7; the first rater says 1 for 0.5, the second for 0.6."""


def test_cohen_kappa_known_answer() -> None:
    assert cohen_kappa(PAIRS) == pytest.approx(0.4)


def test_gwet_ac1_known_answer() -> None:
    assert gwet_ac1(PAIRS) == pytest.approx(0.205 / 0.505)


def test_fleiss_kappa_known_answer() -> None:
    ratings = [[1, 1, 1], [1, 1, 0], [0, 0, 0], [1, 0, 0]]
    assert fleiss_kappa(ratings) == pytest.approx(1 / 3)


def test_undefined_agreement_is_none() -> None:
    assert cohen_kappa([]) is None
    assert gwet_ac1([]) is None
    assert fleiss_kappa([]) is None
    assert cohen_kappa([(1, 1), (1, 1)]) is None
    assert fleiss_kappa([[0, 0], [0, 0]]) is None
    assert gwet_ac1([(1, 1), (1, 1)]) == pytest.approx(1.0)


def test_malformed_ratings_are_refused() -> None:
    with pytest.raises(EvaluationError, match="malformed_record"):
        cohen_kappa([(2, 1)])
    with pytest.raises(EvaluationError, match="malformed_record"):
        fleiss_kappa([[1], [0]])
    with pytest.raises(EvaluationError, match="malformed_record"):
        fleiss_kappa([[1, 0], [0, 1, 1]])
```

Create `packages/earnings-themes/tests/evaluation/test_bootstrap.py`:

```python
"""The event-clustered bootstrap: deterministic under its seed, events drawn whole,
and undefined resamples counted (the Stage 11 spec, A3; R12.7)."""

import random

import pytest
from earnings_themes.evaluation.bootstrap import BootstrapPlan, estimate

PLAN = BootstrapPlan(seed=7, resamples=200, level=0.9, max_undefined_share=0.1)


def mean(values) -> float | None:
    return sum(values) / len(values) if values else None


def test_the_point_is_the_statistic_over_every_event_once() -> None:
    result = estimate({"b": 3.0, "a": 1.0}, mean, PLAN)
    assert result.point == 2.0


def test_resamples_draw_whole_events_by_the_seeded_order() -> None:
    per_event = {"e2": 0.0, "e1": 1.0, "e3": 1.0}
    rng = random.Random(7)
    events = ["e1", "e2", "e3"]
    expected = sorted(
        mean([per_event[events[rng.randrange(3)]] for _ in events]) for _ in range(200)
    )
    position = 0.05 * 199
    lower = expected[9] + (expected[10] - expected[9]) * (position - 9)
    result = estimate(per_event, mean, PLAN)
    assert result.interval.lower == pytest.approx(lower)
    assert estimate(per_event, mean, PLAN) == result


def test_another_seed_draws_other_resamples() -> None:
    per_event = {f"e{i}": float(i) for i in range(10)}
    first = estimate(per_event, mean, PLAN)
    other = estimate(per_event, mean, PLAN.model_copy(update={"seed": 8}))
    assert first.point == other.point
    assert first.interval != other.interval


def test_a_constant_statistic_has_a_degenerate_interval() -> None:
    result = estimate({"a": 0.5, "b": 0.5}, mean, PLAN)
    assert (result.interval.lower, result.interval.upper) == (0.5, 0.5)
    assert result.interval.undefined == 0


def test_undefined_resamples_are_skipped_and_counted() -> None:
    per_event = {f"e{i}": i == 0 for i in range(10)}

    def needs_e0(drawn) -> float | None:
        return 1.0 if any(drawn) else None

    result = estimate(per_event, needs_e0, PLAN)
    rng = random.Random(7)
    draws = [
        [per_event[f"e{rng.randrange(10)}"] for _ in range(10)] for _ in range(200)
    ]
    expected = sum(not any(drawn) for drawn in draws)
    assert result.interval.undefined == expected
    assert expected > 20
    assert result.interval.lower is None and result.interval.upper is None
    loose = PLAN.model_copy(update={"max_undefined_share": 0.9})
    assert estimate(per_event, needs_e0, loose).interval.lower == 1.0


def test_no_events_is_undefined() -> None:
    result = estimate({}, mean, PLAN)
    assert result.point is None
    assert result.interval.lower is None
    assert result.interval.undefined == PLAN.resamples
```

In `tests/contracts/test_data_dictionary.py`, add `bootstrap,` to the `from earnings_themes.evaluation import (...)` block, in alphabetical order.

In `tests/contracts/test_data_dictionary.py`, replace:

```python
EVALUATION_MODELS: list[type[BaseModel]] = []
```

with:

```python
EVALUATION_MODELS = [
    bootstrap.BootstrapPlan,
    bootstrap.Interval,
    bootstrap.Estimate,
]
```

Insert the model test, followed by two blank lines, before the enum test's decorator:

In `tests/contracts/test_data_dictionary.py`, replace:

```python
@pytest.mark.parametrize("enum", EVALUATION_ENUMS
```

with:

```python
@pytest.mark.parametrize("model", EVALUATION_MODELS, ids=lambda m: m.__name__)
def test_evaluation_fields_documented(model: type[BaseModel]) -> None:
    assert documented(model.__name__) == set(model.model_fields)


@pytest.mark.parametrize("enum", EVALUATION_ENUMS
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_agreement.py packages/earnings-themes/tests/evaluation/test_bootstrap.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`3 errors`), with `ImportError: cannot import name 'bootstrap' from 'earnings_themes.evaluation'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.agreement'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.bootstrap'`.

- [x] **Step 3: Write the implementation**
> Deviation (Task 5 fix round, user decision 2026-10-12): agreement refusals name `pairs[i]` / `ratings[i]`; a wrong-length pair is an `EvaluationError`; the percentile boundary uses `undefined / resamples > share`, with three more bootstrap assertions. Final review: `agreement.judge_agreement` is the one pooled kappa/AC1 estimate that `report._agreement` and `calibration._family` both call; `Interval.lower/upper/level` and `Estimate.point` are finite `Real` (the type now lives in `bootstrap.py`).

Create `packages/earnings-themes/src/earnings_themes/evaluation/agreement.py`:

```python
"""Agreement between raters (the Stage 11 spec, A3 and §Preregistration; R8.4,
R12.10; RC §7).

- **Cohen's κ** and **Gwet's AC1** compare two raters' binary answers over the same
  items: a judge family's verdict and the user's label (FP9, FP21).
- **Fleiss' κ** compares any fixed number of raters, at least two, over the same
  items: k fresh runs' event × theme presence (FP12).

An empty population, or one whose chance agreement is total, is ``None``, never a
number (A §Non-negotiables).
"""

from collections.abc import Sequence

from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem


def _shares(pairs: Sequence[tuple[int, int]]) -> tuple[float, float, float] | None:
    """Observed agreement, and each rater's share of 1s; ``None`` with no items."""
    if not pairs:
        return None
    if any(a not in (0, 1) or b not in (0, 1) for a, b in pairs):
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD)
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    return observed, sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n


def cohen_kappa(pairs: Sequence[tuple[int, int]]) -> float | None:
    """Cohen's κ for two raters' binary answers."""
    shares = _shares(pairs)
    if shares is None:
        return None
    observed, first, second = shares
    chance = first * second + (1 - first) * (1 - second)
    return None if chance == 1 else (observed - chance) / (1 - chance)


def gwet_ac1(pairs: Sequence[tuple[int, int]]) -> float | None:
    """Gwet's AC1 for two raters' binary answers; its chance agreement is at most
    one half, so it is defined whenever there is an item."""
    shares = _shares(pairs)
    if shares is None:
        return None
    observed, first, second = shares
    mean = (first + second) / 2
    chance = 2 * mean * (1 - mean)
    return (observed - chance) / (1 - chance)


def fleiss_kappa(ratings: Sequence[Sequence[int]]) -> float | None:
    """Fleiss' κ: one row per item, holding each rater's category."""
    if not ratings:
        return None
    raters = len(ratings[0])
    if raters < 2 or any(len(row) != raters for row in ratings):
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD)
    categories = sorted({c for row in ratings for c in row})
    counts = [[list(row).count(c) for c in categories] for row in ratings]
    items = len(counts)
    observed = (
        sum(
            (sum(n * n for n in row) - raters) / (raters * (raters - 1))
            for row in counts
        )
        / items
    )
    shares = [
        sum(row[j] for row in counts) / (items * raters) for j in range(len(categories))
    ]
    chance = sum(p * p for p in shares)
    return None if chance == 1 else (observed - chance) / (1 - chance)
```

Create `packages/earnings-themes/src/earnings_themes/evaluation/bootstrap.py`:

```python
"""The event-clustered percentile bootstrap (the Stage 11 spec, A3; R12.7; FP9).

- **Events are the unit.** A resample draws as many events as the partition holds,
  with replacement, from its events in sorted order, by ``random.Random(seed)``'s
  ``randrange``. The statistic sees the drawn events' observations in draw order.
- **Undefined resamples.** A resample whose statistic is ``None`` is skipped and
  counted. When more than ``max_undefined_share`` of the resamples are undefined, or
  none is defined, the interval is undefined (FP9: preregistered).
- **The interval** is the two percentiles at ``(1 - level) / 2`` and its complement,
  each by linear interpolation between order statistics.

The same seed, resample count and observations give the same interval, so a pilot
figure reproduces (R14.6).
"""

import math
import random
from collections.abc import Callable, Mapping, Sequence

from pydantic import Field, NonNegativeInt, PositiveInt

from earnings_themes.records import Part


class BootstrapPlan(Part):
    """How every interval is drawn; preregistered (FP9)."""

    seed: int
    resamples: PositiveInt
    level: float = Field(gt=0, lt=1)
    max_undefined_share: float = Field(ge=0, lt=1)


class Interval(Part):
    """A percentile interval, or ``None`` bounds with the reason in its counts."""

    lower: float | None
    upper: float | None
    level: float
    resamples: PositiveInt
    undefined: NonNegativeInt


class Estimate(Part):
    """A point estimate over every event, and its interval."""

    point: float | None
    interval: Interval


def _quantile(ordered: Sequence[float], share: float) -> float:
    position = share * (len(ordered) - 1)
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def estimate[T](
    per_event: Mapping[str, T],
    statistic: Callable[[Sequence[T]], float | None],
    plan: BootstrapPlan,
) -> Estimate:
    """``statistic`` over every event once, and its event-clustered interval."""
    events = sorted(per_event)
    point = statistic([per_event[e] for e in events]) if events else None
    rng = random.Random(plan.seed)
    values: list[float] = []
    for _ in range(plan.resamples if events else 0):
        drawn = [per_event[events[rng.randrange(len(events))]] for _ in events]
        value = statistic(drawn)
        if value is not None:
            values.append(value)
    undefined = plan.resamples - len(values)
    if not values or undefined > plan.max_undefined_share * plan.resamples:
        lower = upper = None
    else:
        values.sort()
        tail = (1 - plan.level) / 2
        lower, upper = _quantile(values, tail), _quantile(values, 1 - tail)
    return Estimate(
        point=point,
        interval=Interval(
            lower=lower,
            upper=upper,
            level=plan.level,
            resamples=plan.resamples,
            undefined=undefined,
        ),
    )
```

Append to the end of `docs/data-dictionary.md`, after one blank line:

```markdown
### `BootstrapPlan`

| Field | Meaning |
| --- | --- |
| `seed` | `random.Random`'s seed |
| `resamples` | Resample count |
| `level` | The interval's level, such as 0.9 |
| `max_undefined_share` | Above this share of undefined resamples, the interval is undefined |

### `Interval`

| Field | Meaning |
| --- | --- |
| `lower` | The lower percentile, or null when undefined |
| `upper` | The upper percentile, or null when undefined |
| `level` | The interval's level |
| `resamples` | Resample count |
| `undefined` | Resamples whose statistic was undefined, skipped |

### `Estimate`

| Field | Meaning |
| --- | --- |
| `point` | The statistic over every event once, or null when undefined |
| `interval` | Its `Interval` |
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_agreement.py packages/earnings-themes/tests/evaluation/test_bootstrap.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `392 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_agreement.py packages/earnings-themes/tests/evaluation/test_bootstrap.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/agreement.py packages/earnings-themes/src/earnings_themes/evaluation/bootstrap.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_agreement.py packages/earnings-themes/tests/evaluation/test_bootstrap.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/agreement.py packages/earnings-themes/src/earnings_themes/evaluation/bootstrap.py docs/data-dictionary.md
git commit -m "feat(themes): agreement statistics and the event-clustered bootstrap (A3)"
```

---

### Task 6: `verdicts`, and the report and gate records (A3; FP4, FP15, D19-13)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_verdicts.py`
- Create: `packages/earnings-themes/tests/evaluation/test_records.py`
- Modify: `tests/contracts/test_data_dictionary.py` (imports; the evaluation registry)
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/verdicts.py`
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/records.py`
- Modify: `docs/data-dictionary.md` (the evaluation section: `Metric`, `Figure`, `PartitionReport`, `ReadingAgreement`, `IndependentFigures`, `PilotReport`, `Gate`, `Ungated`, `Gates`, `GateResult`, `GateVerdict`)

**Interfaces:**
- Consumes:
  - from Task 2: `tests/evaluation/cases.py: panel`, `tests/evaluation/cases.py: trial`
  - from Task 5: `bootstrap.Interval`
  - existing at `7948d94`: `earnings_core`: `digest`; `earnings_themes.records`: `IdPart`, `NonBlank`, `Part`, `RecordError`, `Sha256Hex`, `ThemesRecord`; `earnings_themes.split`: `Partition`; `earnings_themes.support.records`: `JudgeTrial`, `Presentation`
- Produces:
  - In `earnings_themes.evaluation.verdicts`:
    - `type Consensus = Literal['supports', 'opposes', 'uncertain']`
    - `families(trials: Iterable[JudgeTrial]) -> tuple[str, ...]`
    - `consensus(trials: Iterable[JudgeTrial], family: str) -> Consensus`
    - `family_verdict(trials: Iterable[JudgeTrial], family: str) -> Literal[0, 1]`
    - `trial_verdict(trial: JudgeTrial) -> tuple[Literal[0, 1], bool]`
  - In `earnings_themes.evaluation.records`:
    - `Real`
    - `class Metric(StrEnum)`: `release_precision`, `release_recall`, `theme_f1_micro`, `theme_f1_macro`, `theme_f1_rollup_micro`, `theme_f1_rollup_macro`, `span_unit_precision`, `span_unit_recall`, `span_unit_f1`, `span_char_jaccard`, `retention_quotes`, `retention_targets`, `gold_evidence_recall`, `support_precision`, `scorer_auc`, `judge_kappa`, `judge_ac1`, `hard_negative_false_acceptance`, `rare_theme_recall`, `gs5_edited_share`, `gs5_rejected_share`, `gs5_added_share`, `no_theme_share`, `stability_fleiss_kappa`, `stability_unit_jaccard`, `stability_assignment_jaccard`, `sector_prevalence`, `source_selection_bias`
    - `class Figure(Part)`: fields `metric: Metric`, `qualifier: IdPart | None = None`, `point: Real | None`, `interval: Interval | None`, `counts: tuple[tuple[NonBlank, NonNegativeInt], ...] = ()`, `reason: NonBlank | None = None`
    - `class PartitionReport(Part)`: fields `partition: Partition`, `in_sample: bool`, `events: tuple[IdPart, ...]`, `figures: tuple[Figure, ...]`; methods `.figure(metric: Metric, qualifier: str | None=None) -> Figure | None`
    - `class ReadingAgreement(Part)`: fields `release_agrees: bool`, `theme_f1: Real | None`, `unit_f1: Real | None`, `dangling: NonNegativeInt`
    - `class IndependentFigures(Part)`: fields `event_id: IdPart`, `record_vs_draft: ReadingAgreement`, `signed_vs_record: ReadingAgreement`
    - `class PilotReport(ThemesRecord)`: fields `report_version: PositiveInt`, `label: Literal['feasibility-only'] = 'feasibility-only'`, `preregistration_hash: Sha256Hex`, `calibration_hash: Sha256Hex`, `partitions: tuple[PartitionReport, ...]`, `independent: tuple[IndependentFigures, ...] = ()`, `content_hash: Sha256Hex`; methods `.partition(partition: Partition) -> PartitionReport | None`
    - `class Gate(Part)`: fields `metric: Metric`, `bound: Real`, `basis: Literal['lower_bound', 'point_estimate']`
    - `class Ungated(Part)`: fields `metric: Metric`, `reason: Literal['undefined_interval', 'undefined_point', 'not_in_report']`
    - `class Gates(ThemesRecord)`: fields `gates_version: PositiveInt`, `rule: Literal['dev-lower-bound/1'] = 'dev-lower-bound/1'`, `preregistration_hash: Sha256Hex`, `report_hash: Sha256Hex`, `judge_floor: Real`, `gates: tuple[Gate, ...]`, `ungated: tuple[Ungated, ...] = ()`, `content_hash: Sha256Hex`
    - `class GateResult(Part)`: fields `metric: Metric`, `bound: Real | None`, `value: Real | None`, `passed: bool`, `reason: Literal['met', 'below_bound', 'undefined', 'zero_gold_evidence_recall']`
    - `class GateVerdict(Part)`: fields `passed: bool`, `results: tuple[GateResult, ...]`
    - `content_hash(record: BaseModel) -> str`
    - `sealed(record: M) -> M`
    - `checked(record: M, name: str) -> M`

`verdicts` reads a family's consensus from its two presentations (§Calibration), and each trial's binary verdict. `records` holds:
- the 28 `Metric` values;
- `Figure`: a point and an interval, or a reason;
- `PartitionReport`, with train marked in-sample (FP4);
- `PilotReport`, labelled feasibility-only (R12.2);
- V6's `Gates` and their results.

Each committed record is sealed by its own `content_hash` (D19-13).

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_verdicts.py`:

```python
"""A family's consensus and each trial's verdict (the Stage 11 spec, §Calibration;
FP21)."""

import pytest
from earnings_themes.evaluation.verdicts import (
    consensus,
    families,
    family_verdict,
    trial_verdict,
)

from .cases import panel, trial

YES = ("supported", "fits")


@pytest.mark.parametrize(
    ("first", "consensus_value"),
    [
        (YES, "supports"),
        (("unsupported", "fits"), "opposes"),
        (("supported", "does_not_fit"), "opposes"),
        (("uncertain", "fits"), "uncertain"),
        (("supported", "uncertain"), "uncertain"),
    ],
)
def test_a_familys_consensus(first, consensus_value) -> None:
    trials = panel("t1", first, YES)
    assert consensus(trials, "f0") == consensus_value
    assert family_verdict(trials, "f0") == (1 if consensus_value == "supports" else 0)
    assert families(trials) == ("f0", "f1")


def test_split_presentations_are_uncertain() -> None:
    mixed = (
        trial("t1", "f0", "evidence_first", *YES),
        trial("t1", "f0", "claim_theme_first", "unsupported", "fits"),
    )
    assert consensus(mixed, "f0") == "uncertain"
    assert consensus(mixed[:1], "f0") == "uncertain"
    assert consensus((), "f0") == "uncertain"


def test_a_trials_verdict_and_uncertainty() -> None:
    assert trial_verdict(trial("t1", "f0", "evidence_first", *YES)) == (1, False)
    unsure = trial("t1", "f0", "evidence_first", "uncertain", "fits")
    assert trial_verdict(unsure) == (0, True)
    against = trial("t1", "f0", "evidence_first", "supported", "does_not_fit")
    assert trial_verdict(against) == (0, False)
```

Create `packages/earnings-themes/tests/evaluation/test_records.py`:

```python
"""The report and gate records: what they refuse, and their content hashes (the
Stage 11 spec, §Artifacts; FP4, FP15; R12.2)."""

import pytest
from earnings_themes.evaluation.bootstrap import Interval
from earnings_themes.evaluation.records import (
    Figure,
    Metric,
    PartitionReport,
    PilotReport,
    checked,
    content_hash,
    sealed,
)
from earnings_themes.records import RecordError
from earnings_themes.split import Partition
from pydantic import ValidationError

INTERVAL = Interval(lower=0.1, upper=0.9, level=0.9, resamples=10, undefined=0)


def figure(**changes) -> Figure:
    data = {"metric": Metric.THEME_F1_MICRO, "point": 0.5, "interval": INTERVAL}
    return Figure(**{**data, **changes})


def test_a_figure_has_an_interval_or_a_reason() -> None:
    assert figure().reason is None
    absent = figure(point=None, interval=None, reason="not estimated")
    assert absent.interval is None
    with pytest.raises(ValidationError, match="never both"):
        figure(reason="not estimated")
    with pytest.raises(ValidationError, match="never both"):
        figure(interval=None)


def test_counts_are_sorted_and_points_are_finite() -> None:
    assert figure(counts=(("fn", 1), ("tp", 2))).counts == (("fn", 1), ("tp", 2))
    with pytest.raises(ValidationError, match="sorted and unique"):
        figure(counts=(("tp", 2), ("fn", 1)))
    with pytest.raises(ValidationError):
        figure(point=float("nan"))
    assert figure(point=-0.25).point == -0.25


def test_only_train_and_dev_are_reported_and_train_is_in_sample() -> None:
    def report(partition, in_sample):
        return PartitionReport(
            partition=partition, in_sample=in_sample, events=("e1",), figures=()
        )

    assert report(Partition.TRAIN, True).in_sample
    assert not report(Partition.DEV, False).in_sample
    with pytest.raises(ValidationError, match="in-sample"):
        report(Partition.DEV, True)
    with pytest.raises(ValidationError, match="only train and dev"):
        report(Partition.TEST, False)


def test_one_figure_per_metric_and_qualifier() -> None:
    twice = (figure(), figure())
    with pytest.raises(ValidationError, match="one figure per"):
        PartitionReport(
            partition=Partition.DEV, in_sample=False, events=(), figures=twice
        )
    qualified = (figure(qualifier="f0"), figure(qualifier="f1"), figure())
    report = PartitionReport(
        partition=Partition.DEV, in_sample=False, events=(), figures=qualified
    )
    assert report.figure(Metric.THEME_F1_MICRO, "f1") == qualified[1]
    assert report.figure(Metric.THEME_F1_MICRO) == qualified[2]
    assert report.figure(Metric.SPAN_UNIT_F1) is None


def test_a_sealed_record_is_checked_by_its_content_hash() -> None:
    record = sealed(
        PilotReport(
            report_version=1,
            preregistration_hash="1" * 64,
            calibration_hash="2" * 64,
            partitions=(),
            content_hash="0" * 64,
        )
    )
    assert record.content_hash == content_hash(record) != "0" * 64
    assert record.label == "feasibility-only"
    assert checked(record, "report-v1.json") is record
    with pytest.raises(RecordError, match="content_hash"):
        checked(record.model_copy(update={"report_version": 2}), "report-v1.json")
```

In `tests/contracts/test_data_dictionary.py`, replace:

```python
from earnings_themes.evaluation import problems as evaluation_problems
```

with:

```python
from earnings_themes.evaluation import problems as evaluation_problems
from earnings_themes.evaluation import records as evaluation_records
```

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_MODELS`:

```python
    evaluation_records.Figure,
    evaluation_records.PartitionReport,
    evaluation_records.ReadingAgreement,
    evaluation_records.IndependentFigures,
    evaluation_records.PilotReport,
    evaluation_records.Gate,
    evaluation_records.Ungated,
    evaluation_records.Gates,
    evaluation_records.GateResult,
    evaluation_records.GateVerdict,
```

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_ENUMS`:

```python
    evaluation_records.Metric,
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_verdicts.py packages/earnings-themes/tests/evaluation/test_records.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`3 errors`), with `ImportError: cannot import name 'records' from 'earnings_themes.evaluation'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.records'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.verdicts'`.

- [x] **Step 3: Write the implementation**
> Deviation (Task 6 fix round, user decision 2026-10-12): `content_hash`, `sealed` and `checked` are defined once in `earnings_themes/records.py`, `split.py` calls them (`split_hash` is a thin wrapper) and `evaluation.records` re-exports them (D18-1); three hash-property tests added. Final review: `verdicts.family_judgement` returns the family verdict and its `uncertain` flag together.

Create `packages/earnings-themes/src/earnings_themes/evaluation/verdicts.py`:

```python
"""A judge family's consensus and each trial's verdict on a target (the Stage 11
spec, §Calibration and §Metrics; FP21).

- **Consensus.** A family supports a target when both of its presentations answer
  ``supported`` and ``fits``; it opposes when both answer ``unsupported`` or
  ``does_not_fit``; otherwise it is uncertain, as it is when a presentation is
  missing or unanswered.
- **Verdicts.** A family's binary verdict is 1 exactly when it supports, so an
  uncertain consensus counts as not supporting (§Preregistration). A single trial's
  verdict is 1 when it answers ``supported`` and ``fits``, and it is uncertain when
  either answer is ``uncertain``.
"""

from collections.abc import Iterable
from typing import Literal

from earnings_themes.support.records import JudgeTrial, Presentation

type Consensus = Literal["supports", "opposes", "uncertain"]


def families(trials: Iterable[JudgeTrial]) -> tuple[str, ...]:
    """The judge families in ``trials``, sorted."""
    return tuple(sorted({trial.identity.family for trial in trials}))


def consensus(trials: Iterable[JudgeTrial], family: str) -> Consensus:
    """``family``'s consensus over its two presentations."""
    own = [trial for trial in trials if trial.identity.family == family]
    answers = [trial.answer for trial in own]
    if {trial.presentation for trial in own} != set(Presentation) or len(own) != 2:
        return "uncertain"
    if any(answer is None for answer in answers):
        return "uncertain"
    if all(a.claim_support == "supported" and a.theme_fit == "fits" for a in answers):
        return "supports"
    if all(
        a.claim_support == "unsupported" or a.theme_fit == "does_not_fit"
        for a in answers
    ):
        return "opposes"
    return "uncertain"


def family_verdict(trials: Iterable[JudgeTrial], family: str) -> Literal[0, 1]:
    """1 when ``family`` supports, else 0."""
    return 1 if consensus(trials, family) == "supports" else 0


def trial_verdict(trial: JudgeTrial) -> tuple[Literal[0, 1], bool]:
    """One trial's binary verdict, and whether either of its answers is uncertain."""
    answer = trial.answer
    if answer is None:
        return 0, True
    supports = answer.claim_support == "supported" and answer.theme_fit == "fits"
    unsure = "uncertain" in (answer.claim_support, answer.theme_fit)
    return (1 if supports else 0), unsure
```

Create `packages/earnings-themes/src/earnings_themes/evaluation/records.py`:

```python
"""Stage 11's committed evaluation records: the pilot report and V6's gates (the
Stage 11 spec, §Metrics and §Artifacts; FP15; R12.2, R12.7).

- **Ids, numbers and hashes only** (GS3). A figure names its metric and, where one
  metric is reported several times, a qualifier: a judge family, a family and
  presentation as ``family:presentation``, a scorer view, or a negative kind.
- **Frozen.** Each top-level record carries ``content_hash``: the digest of every
  other field (``sealed``), rechecked when read (``checked``).
- **Feasibility only.** Every figure is labelled feasibility-only (R12.2), and train
  is marked in-sample (FP4).
"""

from enum import StrEnum
from typing import Annotated, Literal, Self

from earnings_core import digest
from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt, model_validator

from earnings_themes.evaluation.bootstrap import Interval
from earnings_themes.records import (
    IdPart,
    NonBlank,
    Part,
    RecordError,
    Sha256Hex,
    ThemesRecord,
)
from earnings_themes.split import Partition

Real = Annotated[float, Field(allow_inf_nan=False)]
"""A finite number; a statistic such as κ may be negative."""


class Metric(StrEnum):
    """The pilot report's metrics (§Metrics)."""

    RELEASE_PRECISION = "release_precision"
    RELEASE_RECALL = "release_recall"
    THEME_F1_MICRO = "theme_f1_micro"
    THEME_F1_MACRO = "theme_f1_macro"
    THEME_F1_ROLLUP_MICRO = "theme_f1_rollup_micro"
    THEME_F1_ROLLUP_MACRO = "theme_f1_rollup_macro"
    SPAN_UNIT_PRECISION = "span_unit_precision"
    SPAN_UNIT_RECALL = "span_unit_recall"
    SPAN_UNIT_F1 = "span_unit_f1"
    SPAN_CHAR_JACCARD = "span_char_jaccard"
    RETENTION_QUOTES = "retention_quotes"
    RETENTION_TARGETS = "retention_targets"
    GOLD_EVIDENCE_RECALL = "gold_evidence_recall"
    SUPPORT_PRECISION = "support_precision"
    SCORER_AUC = "scorer_auc"
    JUDGE_KAPPA = "judge_kappa"
    JUDGE_AC1 = "judge_ac1"
    HARD_NEGATIVE_FALSE_ACCEPTANCE = "hard_negative_false_acceptance"
    RARE_THEME_RECALL = "rare_theme_recall"
    GS5_EDITED_SHARE = "gs5_edited_share"
    GS5_REJECTED_SHARE = "gs5_rejected_share"
    GS5_ADDED_SHARE = "gs5_added_share"
    NO_THEME_SHARE = "no_theme_share"
    STABILITY_FLEISS_KAPPA = "stability_fleiss_kappa"
    STABILITY_UNIT_JACCARD = "stability_unit_jaccard"
    STABILITY_ASSIGNMENT_JACCARD = "stability_assignment_jaccard"
    SECTOR_PREVALENCE = "sector_prevalence"
    SOURCE_SELECTION_BIAS = "source_selection_bias"


class Figure(Part):
    """One metric's point estimate and interval, with the counts behind it; or,
    for a metric that is not estimated, its reason."""

    metric: Metric
    qualifier: IdPart | None = None
    point: Real | None
    interval: Interval | None
    counts: tuple[tuple[NonBlank, NonNegativeInt], ...] = ()
    reason: NonBlank | None = None

    @model_validator(mode="after")
    def _sorted_counts_and_reason(self) -> Self:
        names = [name for name, _ in self.counts]
        if names != sorted(set(names)):
            raise ValueError("counts must be sorted and unique")
        if (self.interval is None) != (self.reason is not None):
            raise ValueError("a figure has an interval or a reason, never both")
        return self


class PartitionReport(Part):
    """One partition's figures; train is in-sample (FP4)."""

    partition: Partition
    in_sample: bool
    events: tuple[IdPart, ...]
    figures: tuple[Figure, ...]

    @model_validator(mode="after")
    def _train_or_dev(self) -> Self:
        if self.partition not in (Partition.TRAIN, Partition.DEV):
            raise ValueError("only train and dev are reported")
        if self.in_sample != (self.partition is Partition.TRAIN):
            raise ValueError("train, and only train, is in-sample")
        if self.events != tuple(sorted(set(self.events))):
            raise ValueError("events must be sorted and unique")
        keys = [(f.metric.value, f.qualifier or "") for f in self.figures]
        if len(keys) != len(set(keys)):
            raise ValueError("one figure per metric and qualifier")
        return self

    def figure(self, metric: Metric, qualifier: str | None = None) -> Figure | None:
        return next(
            (f for f in self.figures if (f.metric, f.qualifier) == (metric, qualifier)),
            None,
        )


class ReadingAgreement(Part):
    """Two readings of one bundle compared (GS19): release identification, exact
    theme F1, and unit F1, with their dangling references (D19-7)."""

    release_agrees: bool
    theme_f1: Real | None
    unit_f1: Real | None
    dangling: NonNegativeInt


class IndependentFigures(Part):
    """One dev event's independent-pass figures (§Metrics, D1: descriptive)."""

    event_id: IdPart
    record_vs_draft: ReadingAgreement
    signed_vs_record: ReadingAgreement


class PilotReport(ThemesRecord):
    """``report-v<N>.json``: every partition's figures, feasibility-only (R12.2)."""

    report_version: PositiveInt
    label: Literal["feasibility-only"] = "feasibility-only"
    preregistration_hash: Sha256Hex
    calibration_hash: Sha256Hex
    partitions: tuple[PartitionReport, ...]
    independent: tuple[IndependentFigures, ...] = ()
    content_hash: Sha256Hex

    def partition(self, partition: Partition) -> PartitionReport | None:
        return next((p for p in self.partitions if p.partition is partition), None)


class Gate(Part):
    """One gated metric's bound (FP15)."""

    metric: Metric
    bound: Real
    basis: Literal["lower_bound", "point_estimate"]


class Ungated(Part):
    """A preregistered gated metric that the dev baseline cannot gate."""

    metric: Metric
    reason: Literal["undefined_interval", "undefined_point", "not_in_report"]


class Gates(ThemesRecord):
    """``gates-v<N>.toml``: V6's gates from the dev baseline (FP15)."""

    gates_version: PositiveInt
    rule: Literal["dev-lower-bound/1"] = "dev-lower-bound/1"
    preregistration_hash: Sha256Hex
    report_hash: Sha256Hex
    judge_floor: Real
    gates: tuple[Gate, ...]
    ungated: tuple[Ungated, ...] = ()
    content_hash: Sha256Hex


class GateResult(Part):
    """One gate's outcome for a configuration's dev point estimate."""

    metric: Metric
    bound: Real | None
    value: Real | None
    passed: bool
    reason: Literal["met", "below_bound", "undefined", "zero_gold_evidence_recall"]


class GateVerdict(Part):
    """Whether a configuration passes every gate, and each gate's outcome."""

    passed: bool
    results: tuple[GateResult, ...]


def content_hash(record: BaseModel) -> str:
    """The digest of every field but ``content_hash``."""
    return digest(record.model_dump(mode="json", exclude={"content_hash"}))


def sealed[M: BaseModel](record: M) -> M:
    """``record`` with its ``content_hash`` filled in."""
    return record.model_copy(update={"content_hash": content_hash(record)})


def checked[M: BaseModel](record: M, name: str) -> M:
    """``record``, refused unless it hashes to its ``content_hash``."""
    if content_hash(record) != record.content_hash:
        raise RecordError(name, ("does not hash to its content_hash",))
    return record
```

Append to the end of `docs/data-dictionary.md`, after one blank line:

```markdown
### `Metric`

| Value | Meaning |
| --- | --- |
| `release_precision` | Confirmed releases that gold labels `release` (R13.1); `ambiguous` left out |
| `release_recall` | Gold releases the system confirmed |
| `theme_f1_micro` | Micro F1 over event × theme cells, exact (gated) |
| `theme_f1_macro` | Mean per-theme F1 over themes with gold or a prediction (gated) |
| `theme_f1_rollup_micro` | Micro F1 after both sides map to level-one roots (secondary) |
| `theme_f1_rollup_macro` | Macro F1 after the same mapping (secondary) |
| `span_unit_precision` | Accepted evidence units that are gold units, per cell |
| `span_unit_recall` | Gold units the accepted evidence holds, per cell |
| `span_unit_f1` | Their F1 (gated) |
| `span_char_jaccard` | Shared over union characters, per cell (secondary) |
| `retention_quotes` | Verified over proposed quotes (R12.8 (i)) |
| `retention_targets` | Accepted over assessed targets (R12.8 (ii)) |
| `gold_evidence_recall` | Gold-supporting units any accepted assignment holds (R12.8 (iii), gated, strictly above zero) |
| `support_precision` | Joint labels of accepted targets (gated on dev) |
| `scorer_auc` | AUC-ROC of a scorer view against the claim label (R8.6); qualifier: the view |
| `judge_kappa` | Cohen's κ against the joint label; qualifier: a family, or `family:presentation` |
| `judge_ac1` | Gwet's AC1, beside κ |
| `hard_negative_false_acceptance` | Hard negatives falsely accepted (R12.5); qualifier: none, or a negative kind |
| `rare_theme_recall` | Recall over themes present in at most two events (descriptive, D1) |
| `gs5_edited_share` | Edited over drafted items (GS5) |
| `gs5_rejected_share` | Rejected over drafted items |
| `gs5_added_share` | Added over signed items |
| `no_theme_share` | Signed bundles with `no_theme` (R12.4) |
| `stability_fleiss_kappa` | Fleiss' κ over event × theme presence across fresh runs (R12.10) |
| `stability_unit_jaccard` | Mean pairwise Jaccard of the runs' accepted evidence units |
| `stability_assignment_jaccard` | Mean pairwise Jaccard of the runs' accepted (theme, unit) pairs |
| `sector_prevalence` | Not estimated (R12.2, D1) |
| `source_selection_bias` | Not estimated (R12.2, D1) |

### `Figure`

| Field | Meaning |
| --- | --- |
| `metric` | The `Metric` |
| `qualifier` | A family, `family:presentation`, a scorer view, or a negative kind; null when the metric is reported once |
| `point` | The point estimate, or null when undefined |
| `interval` | Its `Interval`; null exactly when the metric is not estimated |
| `counts` | Named counts behind the figure, sorted by name |
| `reason` | Why the metric is not estimated; null otherwise |

### `PartitionReport`

| Field | Meaning |
| --- | --- |
| `partition` | `train` or `dev` |
| `in_sample` | True exactly for train (FP4) |
| `events` | The partition's events, sorted |
| `figures` | One `Figure` per metric and qualifier |

### `ReadingAgreement`

| Field | Meaning |
| --- | --- |
| `release_agrees` | Whether the two release-identification labels agree |
| `theme_f1` | Exact theme F1 of one reading against the other |
| `unit_f1` | Unit F1 of their evidence |
| `dangling` | Dangling references in either reading |

### `IndependentFigures`

| Field | Meaning |
| --- | --- |
| `event_id` | The dev event |
| `record_vs_draft` | The kept draft against the user's independent record |
| `signed_vs_record` | The user's record against the signed file |

### `PilotReport`

| Field | Meaning |
| --- | --- |
| `schema_version` | `1` |
| `report_version` | The report's version |
| `label` | `feasibility-only` (R12.2) |
| `preregistration_hash` | The preregistration it follows |
| `calibration_hash` | The calibration artifact whose policy it scores |
| `partitions` | Train's and dev's `PartitionReport` |
| `independent` | Each dev event's `IndependentFigures` |
| `content_hash` | Digest of every other field |

### `Gate`

| Field | Meaning |
| --- | --- |
| `metric` | The gated metric |
| `bound` | The dev baseline's lower bound, or its point estimate |
| `basis` | `lower_bound` or `point_estimate` (FP15) |

### `Ungated`

| Field | Meaning |
| --- | --- |
| `metric` | A preregistered gated metric the baseline cannot gate |
| `reason` | `undefined_interval`, `undefined_point` or `not_in_report` |

### `Gates`

| Field | Meaning |
| --- | --- |
| `schema_version` | `1` |
| `gates_version` | The gates' version |
| `rule` | `dev-lower-bound/1` (FP15) |
| `preregistration_hash` | The preregistration it follows |
| `report_hash` | The report whose dev partition set the gates |
| `judge_floor` | The preregistered judge floor |
| `gates` | Each `Gate` |
| `ungated` | Each `Ungated` |
| `content_hash` | Digest of every other field |

### `GateResult`

| Field | Meaning |
| --- | --- |
| `metric` | The metric |
| `bound` | Its gate, or null for the gold-evidence rule |
| `value` | The configuration's dev point estimate |
| `passed` | Whether it passes |
| `reason` | `met`, `below_bound`, `undefined` or `zero_gold_evidence_recall` |

### `GateVerdict`

| Field | Meaning |
| --- | --- |
| `passed` | Whether every result passes |
| `results` | Each `GateResult` |
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_verdicts.py packages/earnings-themes/tests/evaluation/test_records.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `404 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_verdicts.py packages/earnings-themes/tests/evaluation/test_records.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/verdicts.py packages/earnings-themes/src/earnings_themes/evaluation/records.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_verdicts.py packages/earnings-themes/tests/evaluation/test_records.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/verdicts.py packages/earnings-themes/src/earnings_themes/evaluation/records.py docs/data-dictionary.md
git commit -m "feat(themes): judge verdicts, and the pilot report and gate records (A3)"
```

---

### Task 7: `report`: every §Metrics figure for a partition (A3; D19-3, D19-15)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_report.py`
- Modify: `tests/contracts/test_data_dictionary.py` (imports; the evaluation registry)
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/report.py`
- Modify: `docs/data-dictionary.md` (the evaluation section: `Accepted`, `EventObservation`, `LabelledTarget`)

**Interfaces:**
- Consumes:
  - from Task 2: `align.Span`, `align.UnitIndex`, `align.unit_index`, `align.units_over`, `problems.EvaluationError`, `problems.EvaluationProblem`, `tests/evaluation/cases.py: claim`, `tests/evaluation/cases.py: example`, `tests/evaluation/cases.py: gold`, `tests/evaluation/cases.py: panel`, `tests/evaluation/cases.py: quote`, `tests/evaluation/cases.py: reading`, `tests/evaluation/cases.py: row`, `tests/evaluation/cases.py: unit_ids`
  - from Task 3: `cells.EventCells`, `cells.GoldReading`, `cells.event_cells`, `cells.level_one`
  - from Task 4: `scores.Tally`, `scores.char_counts`, `scores.evidence_recall_counts`, `scores.f1`, `scores.gs5_shares`, `scores.hard_negative_counts`, `scores.macro_f1`, `scores.per_theme`, `scores.precision`, `scores.rare_themes`, `scores.ratio`, `scores.recall`, `scores.release_tally`, `scores.theme_tallies`, `scores.total`, `scores.unit_tally`
  - from Task 5: `agreement.cohen_kappa`, `agreement.fleiss_kappa`, `agreement.gwet_ac1`, `bootstrap.BootstrapPlan`, `bootstrap.estimate`
  - from Task 6: `records.Figure`, `records.Metric`, `records.PartitionReport`, `records.ReadingAgreement`, `verdicts.families`, `verdicts.family_verdict`, `verdicts.trial_verdict`
  - existing at `7948d94`: `earnings_themes.codebook`: `Codebook`; `earnings_themes.gold`: `Gold`, `ReleaseLabel`; `earnings_themes.split`: `Partition`; `earnings_themes.support.metrics`: `precision_value`, `ranked_auc`; `earnings_themes.support.records`: `JudgeTrial`
- Produces:
  - In `earnings_themes.evaluation.report`:
    - `NOT_ESTIMATED`
    - `class Accepted` (frozen dataclass): fields `theme_id: str`, `spans: tuple[Span, ...]`
    - `class EventObservation` (frozen dataclass): fields `event_id: str`, `gold: Gold`, `index: UnitIndex`, `accepted: tuple[Accepted, ...]`, `release_confirmed: bool`, `quotes: tuple[int, int]`, `targets: tuple[int, int]`
    - `class LabelledTarget` (frozen dataclass): fields `target_id: str`, `event_id: str`, `claim_label: Literal[0, 1] | None`, `joint_label: Literal[0, 1] | None`, `accepted: bool`, `scores: Mapping[str, float | None]`, `trials: tuple[JudgeTrial, ...]`
    - `partition_report(observations: Sequence[EventObservation], labelled: Sequence[LabelledTarget], codebook: Codebook, plan: BootstrapPlan, *, partition: Partition) -> PartitionReport`
    - `compare_readings(reference: GoldReading, other: GoldReading, index: UnitIndex) -> ReadingAgreement`
    - `stability_figures(runs: Sequence[Sequence[EventObservation]], codebook: Codebook, plan: BootstrapPlan) -> tuple[Figure, ...]`

`partition_report` computes every §Metrics figure for train or dev, each with its event-clustered interval. It reads per-event observations and the sampled targets' labels. The figures:
- release-ID precision and recall;
- exact and rolled-up theme F1 (D19-3);
- unit and character overlap;
- retention (i)–(iii);
- support precision and scorer AUC;
- judge κ and AC1 (D19-15);
- hard-negative false acceptance;
- rare-theme recall and the no-theme share;
- GS5's shares;
- the two figures marked not estimated.

`compare_readings` gives the dev independent pass's per-event figures (GS19), and `stability_figures` gives FP12's k-run figures.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_report.py`:

```python
"""A partition's figures, with hand-computed known answers (the Stage 11 spec,
§Metrics; R12.5, R12.7, R12.8, R12.10, R13.1)."""

from types import SimpleNamespace

import pytest
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.bootstrap import BootstrapPlan
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.evaluation.records import Metric
from earnings_themes.evaluation.report import (
    NOT_ESTIMATED,
    Accepted,
    EventObservation,
    LabelledTarget,
    compare_readings,
    partition_report,
    stability_figures,
)
from earnings_themes.gold import ReleaseLabel
from earnings_themes.split import Partition

from .cases import claim, example, gold, panel, quote, reading, row, unit_ids

PLAN = BootstrapPlan(seed=11, resamples=50, level=0.9, max_undefined_share=0.5)
BOOK = SimpleNamespace(
    themes=tuple(
        SimpleNamespace(theme_id=t, parent_id=None)
        for t in ("capacity", "costs", "debt", "demand", "labor", "pricing")
    )
)


def observations() -> tuple[EventObservation, EventObservation]:
    source, first = example()
    p0 = unit_ids(source)[0]
    index = unit_index(source)
    second = reading(
        quotes=(quote("q1", 0, 20, p0),),
        claims=(claim("c1", "q1"),),
        assignments=(row("c1", "unmatched"),),
        label=ReleaseLabel.NOT_RELEASE,
    )
    return (
        EventObservation(
            event_id="e1",
            gold=gold("e1", first),
            index=index,
            accepted=(
                Accepted("pricing", ((21, 37),)),
                Accepted("capacity", ((0, 20),)),
                Accepted("capacity", ((57, 73),)),
                Accepted("debt", ((57, 73),)),
            ),
            release_confirmed=True,
            quotes=(3, 4),
            targets=(3, 5),
        ),
        EventObservation(
            event_id="e2",
            gold=gold("e2", second, no_theme=True),
            index=index,
            accepted=(Accepted("capacity", ((0, 20),)),),
            release_confirmed=True,
            quotes=(1, 2),
            targets=(1, 1),
        ),
    )


def labelled() -> tuple[LabelledTarget, ...]:
    yes, no, unsure = (
        ("supported", "fits"),
        ("unsupported", "fits"),
        ("uncertain", "fits"),
    )
    return (
        LabelledTarget(
            "t1",
            "e1",
            1,
            1,
            True,
            {"minicheck": 0.9, "deberta": 0.8},
            panel("t1", yes, yes),
        ),
        LabelledTarget(
            "t2",
            "e1",
            0,
            0,
            True,
            {"minicheck": 0.7, "deberta": 0.9},
            panel("t2", yes, no),
        ),
        LabelledTarget(
            "t3",
            "e2",
            1,
            None,
            False,
            {"minicheck": 0.4, "deberta": None},
            panel("t3", unsure, yes),
        ),
        LabelledTarget(
            "t4",
            "e2",
            0,
            0,
            False,
            {"minicheck": 0.2, "deberta": 0.1},
            panel("t4", ("unsupported", "does_not_fit"), no),
        ),
    )


@pytest.fixture(scope="module")
def report():
    return partition_report(
        observations(), labelled(), BOOK, PLAN, partition=Partition.DEV
    )


@pytest.mark.parametrize(
    ("metric", "qualifier", "point"),
    [
        (Metric.THEME_F1_MICRO, None, 2 / 3),
        (Metric.THEME_F1_MACRO, None, 5 / 9),
        (Metric.SPAN_UNIT_PRECISION, None, 2 / 5),
        (Metric.SPAN_UNIT_RECALL, None, 2 / 3),
        (Metric.SPAN_UNIT_F1, None, 0.5),
        (Metric.SPAN_CHAR_JACCARD, None, 12 / 96),
        (Metric.RETENTION_QUOTES, None, 4 / 6),
        (Metric.RETENTION_TARGETS, None, 4 / 6),
        (Metric.GOLD_EVIDENCE_RECALL, None, 2 / 3),
        (Metric.RELEASE_PRECISION, None, 0.5),
        (Metric.RELEASE_RECALL, None, 1.0),
        (Metric.NO_THEME_SHARE, None, 0.5),
        (Metric.HARD_NEGATIVE_FALSE_ACCEPTANCE, None, 0.5),
        (Metric.HARD_NEGATIVE_FALSE_ACCEPTANCE, "period", 1.0),
        (Metric.HARD_NEGATIVE_FALSE_ACCEPTANCE, "issuer", 0.0),
        (Metric.RARE_THEME_RECALL, None, 1.0),
        (Metric.GS5_EDITED_SHARE, None, 0.0),
        (Metric.SUPPORT_PRECISION, None, 0.5),
        (Metric.SCORER_AUC, "minicheck", 0.75),
        (Metric.SCORER_AUC, "deberta", 0.5),
        (Metric.JUDGE_KAPPA, "f0", 0.4),
        (Metric.JUDGE_KAPPA, "f1", 1.0),
        (Metric.JUDGE_KAPPA, "f0:evidence_first", 0.4),
    ],
)
def test_known_answers(report, metric, qualifier, point) -> None:
    figure = report.figure(metric, qualifier)
    assert figure is not None
    assert figure.point == pytest.approx(point)
    assert figure.interval is not None and figure.interval.resamples == PLAN.resamples


def test_counts_keep_what_was_left_out(report) -> None:
    micro = dict(report.figure(Metric.THEME_F1_MICRO).counts)
    assert micro == {"tp": 2, "fp": 2, "fn": 0, "uncertain_left_out": 1}
    macro = dict(report.figure(Metric.THEME_F1_MACRO).counts)
    assert macro == {"themes_scored": 3, "themes_left_out": 3}
    support = dict(report.figure(Metric.SUPPORT_PRECISION).counts)
    assert support == {"labelled": 3, "accepted": 2, "accepted_unlabelled": 0}


def test_dev_is_held_out_and_two_metrics_are_not_estimated(report) -> None:
    assert report.partition is Partition.DEV and not report.in_sample
    assert report.events == ("e1", "e2")
    for metric in (Metric.SECTOR_PREVALENCE, Metric.SOURCE_SELECTION_BIAS):
        figure = report.figure(metric)
        assert figure.point is None and figure.interval is None
        assert figure.reason == NOT_ESTIMATED


def test_the_report_is_deterministic(report) -> None:
    again = partition_report(
        observations(), labelled(), BOOK, PLAN, partition=Partition.DEV
    )
    assert again == report


def test_wrong_partitions_and_unknown_events_are_refused() -> None:
    with pytest.raises(EvaluationError, match="wrong_partition"):
        partition_report(observations(), (), BOOK, PLAN, partition=Partition.TEST)
    with pytest.raises(EvaluationError, match="wrong_partition"):
        partition_report(observations(), (), BOOK, PLAN, partition=Partition.TRAIN)
    stray = LabelledTarget("t9", "e9", 1, 1, True, {}, ())
    with pytest.raises(EvaluationError, match="unknown_event"):
        partition_report(observations(), (stray,), BOOK, PLAN, partition=Partition.DEV)


def test_two_readings_compared() -> None:
    source, reference = example()
    p0 = unit_ids(source)[0]
    other = reading(
        quotes=(quote("q1", 0, 5, p0),),
        claims=(claim("c1", "q1"),),
        assignments=(row("c1", "capacity"),),
    )
    agreement = compare_readings(reference, other, unit_index(source))
    assert agreement.release_agrees is True
    assert agreement.theme_f1 == pytest.approx(2 / 3)
    assert agreement.unit_f1 == pytest.approx(0.5)
    assert agreement.dangling == 0


def test_stability_over_identical_and_empty_runs() -> None:
    runs = observations()
    same = stability_figures((runs, runs), BOOK, PLAN)
    by_metric = {f.metric: f.point for f in same}
    assert by_metric == {
        Metric.STABILITY_FLEISS_KAPPA: pytest.approx(1.0),
        Metric.STABILITY_UNIT_JACCARD: 1.0,
        Metric.STABILITY_ASSIGNMENT_JACCARD: 1.0,
    }
    empty = tuple(
        EventObservation(
            o.event_id, o.gold, o.index, (), o.release_confirmed, o.quotes, o.targets
        )
        for o in runs
    )
    apart = {f.metric: f.point for f in stability_figures((runs, empty), BOOK, PLAN)}
    assert apart[Metric.STABILITY_FLEISS_KAPPA] == pytest.approx(-0.2)
    assert apart[Metric.STABILITY_UNIT_JACCARD] == 0.0
    with pytest.raises(EvaluationError, match="malformed_record"):
        stability_figures((runs,), BOOK, PLAN)
```

In `tests/contracts/test_data_dictionary.py`, add `report,` to the `from earnings_themes.evaluation import (...)` block, in alphabetical order.

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_DATACLASSES`:

```python
    report.Accepted,
    report.EventObservation,
    report.LabelledTarget,
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_report.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`2 errors`), with `ImportError: cannot import name 'report' from 'earnings_themes.evaluation'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.report'`.

- [x] **Step 3: Write the implementation**
> Deviation (Task 7 fix round and final review): roll-up figures keep their rolled `EventCells` and use `len(set(roots.values()))`; duplicate events and targets name the repeated ID (`problems.first_duplicate`, shared with `sampling`); a gold/observation event mismatch is `malformed_record`; `_label_figures` lists judge families from joint-labelled targets only; the SPAN_UNIT_* figure counts are `accepted_hits`, `accepted`, `gold_hits`, `gold` and SPAN_CHAR_JACCARD's are `shared`, `union`; `ReadingAgreement.unit_f1` follows the new `EvidenceTally` F1.

Create `packages/earnings-themes/src/earnings_themes/evaluation/report.py`:

```python
"""A partition's figures from its events' observations (the Stage 11 spec,
§Metrics; R12.2, R12.5, R12.7, R12.8, R12.10, R13.1).

The application gathers the observations from the runs (A8); this module reads
nothing and prints nothing.

- **Events are the clusters.** Every interval resamples whole events (R12.7). The
  label figures resample the events that hold labels.
- **Label figures** take the joint label for support precision and judge agreement,
  and the claim label for scorer AUC (FP21). A missing label leaves its target out;
  it is never a negative.
- **Not estimated.** Sector prevalence and source-selection bias are reported with
  their reason (R12.2, D1).
"""

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations
from typing import Literal

from earnings_themes.codebook import Codebook
from earnings_themes.evaluation.agreement import cohen_kappa, fleiss_kappa, gwet_ac1
from earnings_themes.evaluation.align import Span, UnitIndex, units_over
from earnings_themes.evaluation.bootstrap import BootstrapPlan, estimate
from earnings_themes.evaluation.cells import (
    EventCells,
    GoldReading,
    event_cells,
    level_one,
)
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import (
    Figure,
    Metric,
    PartitionReport,
    ReadingAgreement,
)
from earnings_themes.evaluation.scores import (
    Tally,
    char_counts,
    evidence_recall_counts,
    f1,
    gs5_shares,
    hard_negative_counts,
    macro_f1,
    per_theme,
    precision,
    rare_themes,
    ratio,
    recall,
    release_tally,
    theme_tallies,
    total,
    unit_tally,
)
from earnings_themes.evaluation.verdicts import families, family_verdict, trial_verdict
from earnings_themes.gold import Gold
from earnings_themes.split import Partition
from earnings_themes.support.metrics import precision_value, ranked_auc
from earnings_themes.support.records import JudgeTrial

NOT_ESTIMATED = "not estimated from a pilot sample (R12.2, D1)"


@dataclass(frozen=True)
class Accepted:
    """One accepted assignment: its theme, and its evidence spans in the event's
    document."""

    theme_id: str
    spans: tuple[Span, ...]


@dataclass(frozen=True)
class EventObservation:
    """One event: its signed gold, its document's units, the run's accepted
    assignments, whether its kept attempt is ``confirmed`` (R13.1), and two
    retention counts, each (kept, offered): quotes (R12.8 (i)) and support targets,
    accepted over assessed (R12.8 (ii))."""

    event_id: str
    gold: Gold
    index: UnitIndex
    accepted: tuple[Accepted, ...]
    release_confirmed: bool
    quotes: tuple[int, int]
    targets: tuple[int, int]


@dataclass(frozen=True)
class LabelledTarget:
    """One labelled support target: the user's claim and joint labels (FP21),
    whether the run accepted it, each scorer view's joint score, and its four judge
    trials."""

    target_id: str
    event_id: str
    claim_label: Literal[0, 1] | None
    joint_label: Literal[0, 1] | None
    accepted: bool
    scores: Mapping[str, float | None]
    trials: tuple[JudgeTrial, ...]


@dataclass(frozen=True)
class _Event:
    observation: EventObservation
    cells: EventCells
    tallies: dict[str, Tally]
    rolled: dict[str, Tally]
    units: Tally
    chars: tuple[int, int]
    evidence: tuple[int, int]
    release: Tally | None
    negatives: dict[str, tuple[int, int]]


def _accepted(index: UnitIndex, accepted: Iterable[Accepted]):
    spans: dict[str, tuple[Span, ...]] = {}
    for row in accepted:
        spans[row.theme_id] = tuple(sorted({*spans.get(row.theme_id, ()), *row.spans}))
    return spans, {theme: units_over(index, s) for theme, s in spans.items()}


def _event(observation: EventObservation, roots: Mapping[str, str]) -> _Event:
    spans, units = _accepted(observation.index, observation.accepted)
    predicted = set(spans)
    gold = observation.gold
    cells = event_cells(gold, observation.index, predicted)
    up = {roots.get(t, t) for t in predicted}
    rolled = event_cells(gold, observation.index, up, theme_map=roots)
    negatives = hard_negative_counts(gold, observation.index, units)
    return _Event(
        observation=observation,
        cells=cells,
        tallies=theme_tallies(cells, predicted),
        rolled=theme_tallies(rolled, up),
        units=unit_tally(cells, units),
        chars=char_counts(cells, spans),
        evidence=evidence_recall_counts(cells, units),
        release=release_tally(
            observation.release_confirmed, gold.release_identification.label
        ),
        negatives={kind.value: counts for kind, counts in negatives.items()},
    )


def _counts(**counts: int) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(counts.items()))


def _summed(pairs: Iterable[tuple[int, int]]) -> float | None:
    rows = list(pairs)
    return ratio(sum(a for a, _ in rows), sum(b for _, b in rows))


def _tally_counts(tally: Tally, **more: int) -> tuple[tuple[str, int], ...]:
    return _counts(tp=tally.tp, fp=tally.fp, fn=tally.fn, **more)


class _Figures:
    def __init__(self, plan: BootstrapPlan) -> None:
        self.plan = plan
        self.out: list[Figure] = []

    def add[T](
        self,
        metric: Metric,
        per_event: Mapping[str, T],
        statistic: Callable[[Sequence[T]], float | None],
        counts: tuple[tuple[str, int], ...] = (),
        qualifier: str | None = None,
    ) -> None:
        result = estimate(per_event, statistic, self.plan)
        self.out.append(
            Figure(
                metric=metric,
                qualifier=qualifier,
                point=result.point,
                interval=result.interval,
                counts=counts,
            )
        )


def _event_figures(
    figures: _Figures, events: Mapping[str, _Event], themes: int
) -> None:
    def tallies(name: str) -> dict[str, Iterable[Tally]]:
        return {e: getattr(x, name).values() for e, x in events.items()}

    def merged(name: str) -> Tally:
        return total(t for x in events.values() for t in getattr(x, name).values())

    release = {e: x.release for e, x in events.items()}
    shown = total(t for t in release.values() if t is not None)
    ambiguous = sum(t is None for t in release.values())
    for metric, measure in (
        (Metric.RELEASE_PRECISION, precision),
        (Metric.RELEASE_RECALL, recall),
    ):
        figures.add(
            metric,
            release,
            lambda drawn, m=measure: m(total(t for t in drawn if t is not None)),
            _tally_counts(shown, ambiguous=ambiguous),
        )
    left = sum(len(x.cells.uncertain) for x in events.values())
    for micro, macro, name in (
        (Metric.THEME_F1_MICRO, Metric.THEME_F1_MACRO, "tallies"),
        (Metric.THEME_F1_ROLLUP_MICRO, Metric.THEME_F1_ROLLUP_MACRO, "rolled"),
    ):
        figures.add(
            micro,
            tallies(name),
            lambda drawn: f1(total(t for event in drawn for t in event)),
            _tally_counts(merged(name), uncertain_left_out=left),
        )
        scored = len(per_theme(getattr(x, name) for x in events.values()))
        figures.add(
            macro,
            {e: getattr(x, name) for e, x in events.items()},
            lambda drawn: macro_f1(per_theme(drawn)),
            _counts(themes_scored=scored, themes_left_out=themes - scored),
        )
    units = {e: x.units for e, x in events.items()}
    unit_total = total(units.values())
    for metric, measure in (
        (Metric.SPAN_UNIT_PRECISION, precision),
        (Metric.SPAN_UNIT_RECALL, recall),
        (Metric.SPAN_UNIT_F1, f1),
    ):
        figures.add(
            metric,
            units,
            lambda drawn, m=measure: m(total(drawn)),
            _tally_counts(unit_total),
        )
    chars = {e: x.chars for e, x in events.items()}
    figures.add(
        Metric.SPAN_CHAR_JACCARD,
        chars,
        _summed,
        _counts(
            shared=sum(a for a, _ in chars.values()),
            union=sum(b for _, b in chars.values()),
        ),
    )
    for metric, pick in (
        (Metric.RETENTION_QUOTES, lambda x: x.observation.quotes),
        (Metric.RETENTION_TARGETS, lambda x: x.observation.targets),
        (Metric.GOLD_EVIDENCE_RECALL, lambda x: x.evidence),
    ):
        pairs = {e: pick(x) for e, x in events.items()}
        figures.add(
            metric,
            pairs,
            _summed,
            _counts(
                kept=sum(a for a, _ in pairs.values()),
                offered=sum(b for _, b in pairs.values()),
            ),
        )
    kinds = sorted({k for x in events.values() for k in x.negatives})
    for kind in (None, *kinds):
        pairs = {
            e: tuple(
                (named, hit)
                for k, (named, hit) in x.negatives.items()
                if kind is None or k == kind
            )
            for e, x in events.items()
        }
        figures.add(
            Metric.HARD_NEGATIVE_FALSE_ACCEPTANCE,
            pairs,
            lambda drawn: ratio(
                sum(hit for event in drawn for _, hit in event),
                sum(named for event in drawn for named, _ in event),
            ),
            _counts(
                named=sum(n for rows in pairs.values() for n, _ in rows),
                accepted=sum(h for rows in pairs.values() for _, h in rows),
            ),
            qualifier=kind,
        )
    rare = rare_themes(x.cells for x in events.values())
    rare_tallies = {
        e: tuple(t for theme, t in x.tallies.items() if theme in rare)
        for e, x in events.items()
    }
    figures.add(
        Metric.RARE_THEME_RECALL,
        rare_tallies,
        lambda drawn: recall(total(t for event in drawn for t in event)),
        _counts(rare_themes=len(rare)),
    )
    counts = {e: x.observation.gold.counts for e, x in events.items()}
    for metric, key in (
        (Metric.GS5_EDITED_SHARE, "edited"),
        (Metric.GS5_REJECTED_SHARE, "rejected"),
        (Metric.GS5_ADDED_SHARE, "added"),
    ):
        figures.add(metric, counts, lambda drawn, k=key: gs5_shares(drawn)[k])
    no_theme = {e: x.observation.gold.no_theme for e, x in events.items()}
    figures.add(
        Metric.NO_THEME_SHARE,
        no_theme,
        lambda drawn: ratio(sum(drawn), len(drawn)),
        _counts(no_theme=sum(no_theme.values()), bundles=len(no_theme)),
    )


def _label_figures(
    figures: _Figures, labelled: Sequence[LabelledTarget], events: Iterable[str]
) -> None:
    by_event: dict[str, tuple[LabelledTarget, ...]] = {
        e: tuple(t for t in labelled if t.event_id == e) for e in events
    }
    by_event = {e: ts for e, ts in by_event.items() if ts}

    def joint_accepted(drawn) -> float | None:
        return precision_value(
            [
                t.joint_label
                for ts in drawn
                for t in ts
                if t.accepted and t.joint_label is not None
            ]
        )

    figures.add(
        Metric.SUPPORT_PRECISION,
        by_event,
        joint_accepted,
        _counts(
            labelled=sum(t.joint_label is not None for t in labelled),
            accepted=sum(t.accepted for t in labelled),
            accepted_unlabelled=sum(
                t.accepted and t.joint_label is None for t in labelled
            ),
        ),
    )
    for view in sorted({v for t in labelled for v in t.scores}):

        def auc(drawn, v=view) -> float | None:
            rows = [
                (t.claim_label, t.scores.get(v))
                for ts in drawn
                for t in ts
                if t.claim_label is not None and t.scores.get(v) is not None
            ]
            return ranked_auc(
                [s for label, s in rows if label == 1],
                [s for label, s in rows if label == 0],
            )

        scored = [
            t
            for t in labelled
            if t.claim_label is not None and t.scores.get(view) is not None
        ]
        figures.add(
            Metric.SCORER_AUC,
            by_event,
            auc,
            _counts(
                positive=sum(t.claim_label == 1 for t in scored),
                negative=sum(t.claim_label == 0 for t in scored),
            ),
            qualifier=view,
        )
    trials = [trial for t in labelled for trial in t.trials]
    for family in families(trials):
        _agreement(
            figures,
            by_event,
            family,
            lambda t, f=family: (family_verdict(t.trials, f), False),
        )
        for presentation in sorted({x.presentation.value for x in trials}):

            def verdict(t: LabelledTarget, f=family, p=presentation):
                trial = next(
                    (
                        x
                        for x in t.trials
                        if x.identity.family == f and x.presentation.value == p
                    ),
                    None,
                )
                return (0, True) if trial is None else trial_verdict(trial)

            _agreement(figures, by_event, f"{family}:{presentation}", verdict)


def _agreement(
    figures: _Figures,
    by_event: Mapping[str, tuple[LabelledTarget, ...]],
    qualifier: str,
    verdict: Callable[[LabelledTarget], tuple[int, bool]],
) -> None:
    pairs = {
        e: tuple(
            (verdict(t)[0], t.joint_label) for t in ts if t.joint_label is not None
        )
        for e, ts in by_event.items()
    }
    unsure = sum(
        verdict(t)[1]
        for ts in by_event.values()
        for t in ts
        if t.joint_label is not None
    )
    counts = _counts(labels=sum(len(p) for p in pairs.values()), uncertain=unsure)
    for metric, measure in (
        (Metric.JUDGE_KAPPA, cohen_kappa),
        (Metric.JUDGE_AC1, gwet_ac1),
    ):
        figures.add(
            metric,
            pairs,
            lambda drawn, m=measure: m([p for event in drawn for p in event]),
            counts,
            qualifier=qualifier,
        )


def partition_report(
    observations: Sequence[EventObservation],
    labelled: Sequence[LabelledTarget],
    codebook: Codebook,
    plan: BootstrapPlan,
    *,
    partition: Partition,
) -> PartitionReport:
    """Every §Metrics figure for one partition's events and labels."""
    if partition not in (Partition.TRAIN, Partition.DEV):
        raise EvaluationError(EvaluationProblem.WRONG_PARTITION, partition.value)
    ids = [o.event_id for o in observations]
    if len(ids) != len(set(ids)):
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "events")
    for observation in observations:
        if observation.gold.partition is not partition or (
            observation.gold.event_id != observation.event_id
        ):
            raise EvaluationError(
                EvaluationProblem.WRONG_PARTITION, observation.event_id
            )
    for target in labelled:
        if target.event_id not in ids:
            raise EvaluationError(EvaluationProblem.UNKNOWN_EVENT, target.target_id)
    if len({t.target_id for t in labelled}) != len(labelled):
        raise EvaluationError(EvaluationProblem.DUPLICATE_TARGET, "labels")
    roots = level_one(codebook)
    events = {o.event_id: _event(o, roots) for o in observations}
    figures = _Figures(plan)
    _event_figures(figures, events, len(codebook.themes))
    _label_figures(figures, labelled, sorted(ids))
    for metric in (Metric.SECTOR_PREVALENCE, Metric.SOURCE_SELECTION_BIAS):
        figures.out.append(
            Figure(metric=metric, point=None, interval=None, reason=NOT_ESTIMATED)
        )
    return PartitionReport(
        partition=partition,
        in_sample=partition is Partition.TRAIN,
        events=tuple(sorted(ids)),
        figures=tuple(figures.out),
    )


def compare_readings(
    reference: GoldReading, other: GoldReading, index: UnitIndex
) -> ReadingAgreement:
    """``other`` scored against ``reference``, as a run is against gold: its present
    themes as predictions, and their units as evidence (GS19, A6(3))."""
    theirs = event_cells(other, index)
    mine = event_cells(reference, index, theirs.present)
    return ReadingAgreement(
        release_agrees=reference.release_identification.label
        == other.release_identification.label,
        theme_f1=f1(total(theme_tallies(mine, theirs.present).values())),
        unit_f1=f1(unit_tally(mine, theirs.units)),
        dangling=mine.dangling + theirs.dangling,
    )


def stability_figures(
    runs: Sequence[Sequence[EventObservation]],
    codebook: Codebook,
    plan: BootstrapPlan,
) -> tuple[Figure, ...]:
    """FP12's k fresh runs over one partition's events (R12.10): Fleiss' κ over
    event × theme presence, for every codebook theme, and the mean pairwise Jaccard
    of the runs' accepted evidence units and of their accepted (theme, unit)
    pairs."""
    if len(runs) < 2:
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "runs")
    events = sorted(o.event_id for o in runs[0])
    if any(sorted(o.event_id for o in run) != events for run in runs):
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "runs")
    themes = sorted(t.theme_id for t in codebook.themes)
    per_event: dict[str, tuple[tuple[frozenset, frozenset, frozenset], ...]] = {}
    for event_id in events:
        rows = []
        for run in runs:
            o = next(x for x in run if x.event_id == event_id)
            _, units = _accepted(o.index, o.accepted)
            pairs = frozenset((t, u) for t, us in units.items() for u in us)
            rows.append((frozenset(units), frozenset(u for _, u in pairs), pairs))
        per_event[event_id] = tuple(rows)

    def kappa(drawn) -> float | None:
        return fleiss_kappa(
            [
                [int(theme in run[0]) for run in event]
                for event in drawn
                for theme in themes
            ]
        )

    def jaccard(position: int):
        def mean(drawn) -> float | None:
            values = []
            for a, b in combinations(range(len(runs)), 2):
                left = {(i, x) for i, e in enumerate(drawn) for x in e[a][position]}
                right = {(i, x) for i, e in enumerate(drawn) for x in e[b][position]}
                union = left | right
                if union:
                    values.append(len(left & right) / len(union))
            return sum(values) / len(values) if values else None

        return mean

    figures = _Figures(plan)
    count = _counts(runs=len(runs), events=len(events), themes=len(themes))
    figures.add(Metric.STABILITY_FLEISS_KAPPA, per_event, kappa, count)
    figures.add(Metric.STABILITY_UNIT_JACCARD, per_event, jaccard(1), count)
    figures.add(Metric.STABILITY_ASSIGNMENT_JACCARD, per_event, jaccard(2), count)
    return tuple(figures.out)
```

Append to the end of `docs/data-dictionary.md`, after one blank line:

```markdown
### `Accepted`

| Field | Meaning |
| --- | --- |
| `theme_id` | An accepted assignment's theme |
| `spans` | Its evidence spans in the event's document |

### `EventObservation`

| Field | Meaning |
| --- | --- |
| `event_id` | The event |
| `gold` | Its signed gold |
| `index` | Its document's `UnitIndex` |
| `accepted` | The run's accepted assignments |
| `release_confirmed` | Whether its kept attempt is `confirmed` (R13.1) |
| `quotes` | Verified and proposed quotes (R12.8 (i)) |
| `targets` | Accepted and assessed targets (R12.8 (ii)) |

### `LabelledTarget`

| Field | Meaning |
| --- | --- |
| `target_id` | The support target |
| `event_id` | Its event |
| `claim_label` | The user's claim label, or null when unsure |
| `joint_label` | The joint label, or null |
| `accepted` | Whether the run accepted it |
| `scores` | Each scorer view's joint score |
| `trials` | Its four judge trials |
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_report.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `424 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_report.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/report.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_report.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/report.py docs/data-dictionary.md
git commit -m "feat(themes): the pilot report's figures for a partition (A3)"
```

---

### Task 8: `gates`, and floats in `tomlfile` (A3; FP15, R12.8, D19-11, D19-16)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_gates.py`
- Modify: `packages/earnings-themes/tests/test_tomlfile.py`
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/gates.py`
- Modify: `packages/earnings-themes/src/earnings_themes/tomlfile.py` (`:3-13`, `:29-34`)

**Interfaces:**
- Consumes:
  - from Task 2: `problems.EvaluationError`, `problems.EvaluationProblem`
  - from Task 6: `records.Gate`, `records.GateResult`, `records.GateVerdict`, `records.Gates`, `records.Metric`, `records.PartitionReport`, `records.PilotReport`, `records.Ungated`, `records.checked`, `records.sealed`
  - from Task 7: `report.EventObservation`, `report.partition_report`, `tests/evaluation/test_report.py: BOOK`, `tests/evaluation/test_report.py: PLAN`, `tests/evaluation/test_report.py: labelled`, `tests/evaluation/test_report.py: observations`
  - existing at `7948d94`: `earnings_themes.records`: `RecordError`, `parse`; `earnings_themes.split`: `Partition`; `earnings_themes`: `tomlfile`
- Produces:
  - In `earnings_themes.evaluation.gates`:
    - `HEADER`
    - `derive_gates(report: PilotReport, *, gated: Sequence[Metric], undefined_gate: Literal['not_gated', 'point_estimate'], judge_floor: float, preregistration_hash: str, version: int=1) -> Gates`
    - `evaluate_gates(gates: Gates, report: PartitionReport) -> GateVerdict`
    - `gates_toml(gates: Gates) -> str`
    - `load_gates(path: Path) -> Gates`
  - In `earnings_themes.tomlfile`: `dumps` writes a finite float as its `repr`, and raises `ValueError` ("TOML holds no infinite or NaN float here") for NaN or infinity.

`derive_gates` turns the dev partition's figures into V6's gates (FP15). Each gated metric's gate is its 90% lower bound. When that bound is undefined, the preregistration's `undefined_gate` decides (D19-11).

`evaluate_gates` checks a dev report against the gates. Whatever the gates, gold-evidence recall must be above zero, and an undefined metric fails. So a reject-everything configuration fails (R12.8), and a test shows it. The gates file is TOML, so `tomlfile` learns to write finite floats (D19-16).

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_gates.py`:

```python
"""V6's gates: derived from the dev baseline, and a configuration that rejects
everything fails them (the Stage 11 spec, A3 and FP15; R12.8)."""

from dataclasses import replace

import pytest
from earnings_themes.evaluation.gates import (
    derive_gates,
    evaluate_gates,
    gates_toml,
    load_gates,
)
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.evaluation.records import Metric, PilotReport, sealed
from earnings_themes.evaluation.report import EventObservation, partition_report
from earnings_themes.records import RecordError
from earnings_themes.split import Partition

from .test_report import BOOK, PLAN, labelled, observations

HASH = "1" * 64
GATED = (
    Metric.THEME_F1_MICRO,
    Metric.SPAN_UNIT_F1,
    Metric.GOLD_EVIDENCE_RECALL,
    Metric.SUPPORT_PRECISION,
)


def pilot(dev) -> PilotReport:
    return sealed(
        PilotReport(
            report_version=1,
            preregistration_hash=HASH,
            calibration_hash=HASH,
            partitions=(dev,),
            content_hash="0" * 64,
        )
    )


@pytest.fixture(scope="module")
def baseline():
    return partition_report(
        observations(), labelled(), BOOK, PLAN, partition=Partition.DEV
    )


def gates_of(baseline, **options):
    return derive_gates(
        pilot(baseline),
        gated=GATED,
        undefined_gate=options.get("undefined_gate", "not_gated"),
        judge_floor=0.4,
        preregistration_hash=HASH,
    )


def test_each_gate_is_the_baselines_lower_bound(baseline) -> None:
    gates = gates_of(baseline)
    for gate in gates.gates:
        figure = baseline.figure(gate.metric)
        assert gate.basis == "lower_bound"
        assert gate.bound == figure.interval.lower
    assert {g.metric for g in gates.gates} | {u.metric for u in gates.ungated} == set(
        GATED
    )
    assert gates.report_hash == pilot(baseline).content_hash


def test_the_baseline_passes_its_own_gates(baseline) -> None:
    verdict = evaluate_gates(gates_of(baseline), baseline)
    assert verdict.passed, verdict.results


def test_a_configuration_that_rejects_everything_fails(baseline) -> None:
    """R12.8: no accepted assignment leaves gold-evidence recall at zero and
    support precision undefined, and either fails whatever the bounds."""
    rejecting = tuple(
        EventObservation(
            o.event_id, o.gold, o.index, (), o.release_confirmed, o.quotes, (0, 1)
        )
        for o in observations()
    )
    labels = tuple(replace(t, accepted=False) for t in labelled())
    report = partition_report(rejecting, labels, BOOK, PLAN, partition=Partition.DEV)
    gates = gates_of(baseline)
    assert {Metric.SUPPORT_PRECISION, Metric.GOLD_EVIDENCE_RECALL} <= {
        g.metric for g in gates.gates
    }
    verdict = evaluate_gates(gates, report)
    assert not verdict.passed
    failed = {(r.metric, r.reason) for r in verdict.results if not r.passed}
    assert (Metric.GOLD_EVIDENCE_RECALL, "zero_gold_evidence_recall") in failed
    assert (Metric.SUPPORT_PRECISION, "undefined") in failed


def test_an_undefined_interval_is_ungated_or_gated_at_the_point(baseline) -> None:
    figures = tuple(
        f.model_copy(update={"interval": f.interval.model_copy(update={"lower": None})})
        if f.metric is Metric.SPAN_UNIT_F1
        else f
        for f in baseline.figures
    )
    dev = baseline.model_copy(update={"figures": figures})
    off = gates_of(dev)
    assert [(u.metric, u.reason) for u in off.ungated] == [
        (Metric.SPAN_UNIT_F1, "undefined_interval")
    ]
    on = gates_of(dev, undefined_gate="point_estimate")
    gate = next(g for g in on.gates if g.metric is Metric.SPAN_UNIT_F1)
    assert (gate.basis, gate.bound) == ("point_estimate", 0.5)


def test_gates_round_trip_through_toml_and_refuse_a_changed_file(
    baseline, tmp_path
) -> None:
    gates = gates_of(baseline)
    path = tmp_path / "gates-v1.toml"
    path.write_text(gates_toml(gates), encoding="utf-8")
    assert load_gates(path) == gates
    path.write_text(
        gates_toml(gates).replace("judge_floor = 0.4", "judge_floor = 0.5"),
        encoding="utf-8",
    )
    with pytest.raises(RecordError, match="content_hash"):
        load_gates(path)


def test_gates_need_the_dev_partition_and_its_preregistration(baseline) -> None:
    train = baseline.model_copy(
        update={"partition": Partition.TRAIN, "in_sample": True}
    )
    with pytest.raises(EvaluationError, match="wrong_partition"):
        derive_gates(
            pilot(train),
            gated=GATED,
            undefined_gate="not_gated",
            judge_floor=0.4,
            preregistration_hash=HASH,
        )
    with pytest.raises(EvaluationError, match="preregistration_mismatch"):
        derive_gates(
            pilot(baseline),
            gated=GATED,
            undefined_gate="not_gated",
            judge_floor=0.4,
            preregistration_hash="2" * 64,
        )
    with pytest.raises(EvaluationError, match="wrong_partition"):
        evaluate_gates(gates_of(baseline), train)
```

Append to the end of `packages/earnings-themes/tests/test_tomlfile.py`, after two blank lines:

```python
def test_floats_round_trip_and_a_non_finite_float_is_refused() -> None:
    """Stage 11's preregistration and gates hold floats (plan 19)."""
    data = {
        "floor": 0.4,
        "small": 1e-07,
        "big": 1e16,
        "whole": 5.0,
        "grid": [0.0, 0.25],
    }
    assert tomllib.loads(dumps(data)) == data
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError, match="infinite or NaN"):
            dumps({"x": bad})
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_gates.py packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`1 error`), with `ModuleNotFoundError: No module named 'earnings_themes.evaluation.gates'`.

- [x] **Step 3: Write the implementation**
> Deviation (final review): `derive_gates`' mismatch refusal names `preregistration_hash`, and the gold-evidence positivity row's reason is `undefined` when the value is null, `zero_gold_evidence_recall` only for 0.0.

Create `packages/earnings-themes/src/earnings_themes/evaluation/gates.py`:

```python
"""V6's gates and the gate evaluator (the Stage 11 spec, A3 and FP15; R12.8, R13.1).

- **The rule** (FP15). Each preregistered gated metric's gate is the dev baseline's
  90% bootstrap lower bound. When that bound is undefined, the preregistration says
  whether the metric is left ungated or gated at the baseline's point estimate.
- **Passing.** A configuration passes when its dev point estimate meets every gate.
  Whatever the gates, gold-evidence recall must be strictly above zero, and an
  undefined (``None``) metric fails its gate, so a configuration that rejects
  everything fails (R12.8).
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from earnings_themes import tomlfile
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import (
    Gate,
    GateResult,
    Gates,
    GateVerdict,
    Metric,
    PartitionReport,
    PilotReport,
    Ungated,
    checked,
    sealed,
)
from earnings_themes.records import parse
from earnings_themes.split import Partition

HEADER = (
    "Stage 11's V6 gates (FP15): each gated metric's bound is the dev baseline's 90%"
    " bootstrap lower bound. Written by `earnings-pipeline pilot gates`."
)


def derive_gates(
    report: PilotReport,
    *,
    gated: Sequence[Metric],
    undefined_gate: Literal["not_gated", "point_estimate"],
    judge_floor: float,
    preregistration_hash: str,
    version: int = 1,
) -> Gates:
    """V6's gates from ``report``'s dev partition (FP15)."""
    dev = report.partition(Partition.DEV)
    if dev is None:
        raise EvaluationError(EvaluationProblem.WRONG_PARTITION, "dev")
    if report.preregistration_hash != preregistration_hash:
        raise EvaluationError(EvaluationProblem.PREREGISTRATION_MISMATCH, "report")
    gates: list[Gate] = []
    ungated: list[Ungated] = []
    for metric in sorted(set(gated)):
        figure = dev.figure(metric)
        if figure is None:
            ungated.append(Ungated(metric=metric, reason="not_in_report"))
        elif figure.interval is not None and figure.interval.lower is not None:
            gates.append(
                Gate(metric=metric, bound=figure.interval.lower, basis="lower_bound")
            )
        elif undefined_gate == "point_estimate" and figure.point is not None:
            gates.append(
                Gate(metric=metric, bound=figure.point, basis="point_estimate")
            )
        else:
            reason = "undefined_point" if figure.point is None else "undefined_interval"
            ungated.append(Ungated(metric=metric, reason=reason))
    return sealed(
        Gates(
            gates_version=version,
            preregistration_hash=preregistration_hash,
            report_hash=report.content_hash,
            judge_floor=judge_floor,
            gates=tuple(gates),
            ungated=tuple(ungated),
            content_hash="0" * 64,
        )
    )


def evaluate_gates(gates: Gates, report: PartitionReport) -> GateVerdict:
    """Whether a configuration's dev figures pass every gate (FP15, R12.8)."""
    if report.partition is not Partition.DEV:
        raise EvaluationError(EvaluationProblem.WRONG_PARTITION, report.partition.value)
    results = []
    for gate in gates.gates:
        figure = report.figure(gate.metric)
        value = None if figure is None else figure.point
        if value is None:
            passed, reason = False, "undefined"
        elif value < gate.bound:
            passed, reason = False, "below_bound"
        else:
            passed, reason = True, "met"
        results.append(
            GateResult(
                metric=gate.metric,
                bound=gate.bound,
                value=value,
                passed=passed,
                reason=reason,
            )
        )
    figure = report.figure(Metric.GOLD_EVIDENCE_RECALL)
    value = None if figure is None else figure.point
    positive = value is not None and value > 0
    results.append(
        GateResult(
            metric=Metric.GOLD_EVIDENCE_RECALL,
            bound=None,
            value=value,
            passed=positive,
            reason="met" if positive else "zero_gold_evidence_recall",
        )
    )
    return GateVerdict(passed=all(r.passed for r in results), results=tuple(results))


def gates_toml(gates: Gates) -> str:
    """The committed file: metrics, bounds and hashes only (GS3)."""
    return tomlfile.dumps(gates.model_dump(mode="json"), header=HEADER)


def load_gates(path: Path) -> Gates:
    """A gates file, refused unless it hashes to its ``content_hash``."""
    return checked(parse(tomlfile.read(path), Gates, path.name), path.name)
```

In `packages/earnings-themes/src/earnings_themes/tomlfile.py`, replace:

```python
No TOML writer is locked, and GS17 adds no dependency, so ``dumps`` writes the one
shape these records need: scalars, arrays of scalars, tables, and arrays of tables,
in key order. A string is a TOML basic string, written as JSON writes one, which TOML
reads the same way, with DEL escaped as TOML requires.
"""

import io
import json
import re
from collections.abc import Mapping
from datetime import date
```

with:

```python
No TOML writer is locked, and GS17 adds no dependency, so ``dumps`` writes the one
shape these records need: scalars, arrays of scalars, tables, and arrays of tables,
in key order. A float is written as Python's ``repr``, which TOML reads back
exactly; Stage 11's preregistration and gates hold floats. A string is a TOML basic
string, written as JSON writes one, which TOML reads the same way, with DEL escaped
as TOML requires.
"""

import io
import json
import math
import re
from collections.abc import Mapping
from datetime import date
```

In `packages/earnings-themes/src/earnings_themes/tomlfile.py`, replace:

```python
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
```

with:

```python
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("TOML holds no infinite or NaN float here")
        return repr(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_gates.py packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `410 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_gates.py packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/src/earnings_themes/evaluation/gates.py packages/earnings-themes/src/earnings_themes/tomlfile.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_gates.py packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/src/earnings_themes/evaluation/gates.py packages/earnings-themes/src/earnings_themes/tomlfile.py
git commit -m "feat(themes): V6's gates and their evaluator; floats in tomlfile (A3)"
```

---

### Task 9: `labels`: support labels and `labels check` (A4; FP17, FP21, D19-16)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_labels.py`
- Modify: `tests/contracts/test_data_dictionary.py` (imports; the evaluation registry)
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/labels.py`
- Modify: `docs/data-dictionary.md` (the evaluation section: `ClaimAnswer`, `FitAnswer`, `SupportLabel`, `SupportLabelSet`)

**Interfaces:**
- Consumes:
  - from Task 2: `problems.EvaluationError`, `problems.EvaluationProblem`
  - existing at `7948d94`: `earnings_themes.problems`: `Refusal`; `earnings_themes.records`: `NonBlank`, `Part`, `RecordError`, `Sha256Hex`, `ThemesRecord`, `parse`; `earnings_themes.split`: `Partition`; `earnings_themes.support.metrics`: `HumanLabel`, `LabelTask`; `earnings_themes`: `tomlfile`
- Produces:
  - In `earnings_themes.evaluation.labels`:
    - `LABELLED`
    - `HEADER`
    - `class ClaimAnswer(StrEnum)`: `supported`, `unsupported`, `unsure`
    - `class FitAnswer(StrEnum)`: `fits`, `does_not_fit`, `unsure`
    - `class SupportLabel(Part)`: fields `target_id: NonBlank`, `target_input_hash: Sha256Hex`, `partition: Partition`, `claim_support: ClaimAnswer`, `theme_fit: FitAnswer`, `labelled_on: date`
    - `class SupportLabelSet(ThemesRecord)`: fields `preregistration_hash: Sha256Hex`, `train_extensions: NonNegativeInt = 0`, `labels: tuple[SupportLabel, ...] = ()`; methods `.of(partition: Partition) -> tuple[SupportLabel, ...]`
    - `claim_label(label: SupportLabel) -> Literal[0, 1] | None`
    - `joint_label(label: SupportLabel) -> Literal[0, 1] | None`
    - `human_labels(labels: Sequence[SupportLabel], task: LabelTask) -> tuple[HumanLabel, ...]`
    - `usable(labels: Sequence[SupportLabel]) -> int`
    - `labels_toml(labels: SupportLabelSet) -> str`
    - `load_labels(path: Path) -> SupportLabelSet`
    - `check_labels(working: SupportLabelSet, *, partition: Partition, sample: Sequence[str], input_hashes: Mapping[str, str], preregistration_hash: str) -> list[Refusal]`
    - `merge_labels(committed: SupportLabelSet | None, working: SupportLabelSet, partition: Partition) -> SupportLabelSet`

`SupportLabel` holds a target's ID and input hash, its partition, the user's two answers, and a date, with no free text (FP17, FP21). `SupportLabelSet` is the committed file's record, and its labels are written train before dev, each by target ID (D19-16).

`check_labels` is A4's `labels check`. It refuses a working file's labels that do not match the sample, the support run's input hashes, or the preregistration. `merge_labels` lets committed labels change only through a preregistered train extension.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_labels.py`:

```python
"""Support labels: derived labels, the committed file, and ``labels check``'s
refusals (the Stage 11 spec, A4 and §Labels; FP17, FP21)."""

from datetime import date

import pytest
from earnings_themes.evaluation.labels import (
    ClaimAnswer,
    FitAnswer,
    SupportLabel,
    SupportLabelSet,
    check_labels,
    claim_label,
    human_labels,
    joint_label,
    labels_toml,
    load_labels,
    merge_labels,
    usable,
)
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.problems import Refusal
from earnings_themes.records import RecordError
from earnings_themes.split import Partition

PREREG = "a" * 64
INPUT = "b" * 64


def label(
    target_id: str, claim: str, fit: str, partition: str = "train"
) -> SupportLabel:
    return SupportLabel(
        target_id=target_id,
        target_input_hash=INPUT,
        partition=Partition(partition),
        claim_support=ClaimAnswer(claim),
        theme_fit=FitAnswer(fit),
        labelled_on=date(2026, 10, 20),
    )


@pytest.mark.parametrize(
    ("claim", "fit", "claim_value", "joint_value"),
    [
        ("supported", "fits", 1, 1),
        ("supported", "does_not_fit", 1, 0),
        ("supported", "unsure", 1, None),
        ("unsupported", "fits", 0, 0),
        ("unsupported", "unsure", 0, 0),
        ("unsure", "fits", None, None),
        ("unsure", "does_not_fit", None, 0),
        ("unsure", "unsure", None, None),
    ],
)
def test_claim_and_joint_labels(claim, fit, claim_value, joint_value) -> None:
    one = label("t1", claim, fit)
    assert claim_label(one) == claim_value
    assert joint_label(one) == joint_value


def test_human_labels_leave_unsure_out() -> None:
    labels = (label("t1", "supported", "fits"), label("t2", "unsure", "fits"))
    joint = human_labels(labels, "joint_support")
    assert [(h.target_id, h.supported) for h in joint] == [("t1", 1)]
    assert len(human_labels(labels, "claim_support")) == 1
    assert usable(labels) == 1


def test_a_label_holds_no_text_and_only_train_or_dev() -> None:
    assert set(SupportLabel.model_fields) == {
        "target_id",
        "target_input_hash",
        "partition",
        "claim_support",
        "theme_fit",
        "labelled_on",
    }
    with pytest.raises(ValueError, match="only train and dev"):
        label("t1", "supported", "fits", "test")
    with pytest.raises(ValueError, match="one label per target"):
        SupportLabelSet(
            preregistration_hash=PREREG,
            labels=(label("t1", "supported", "fits"), label("t1", "unsure", "fits")),
        )


def test_the_file_round_trips_train_then_dev(tmp_path) -> None:
    labels = SupportLabelSet(
        preregistration_hash=PREREG,
        labels=(
            label("t3", "unsure", "fits", "dev"),
            label("t2", "supported", "fits"),
            label("t1", "unsupported", "does_not_fit"),
        ),
    )
    path = tmp_path / "support-labels-v1.toml"
    path.write_text(labels_toml(labels), encoding="utf-8")
    loaded = load_labels(path)
    assert [x.target_id for x in loaded.labels] == ["t1", "t2", "t3"]
    assert set(loaded.labels) == set(labels.labels)
    path.write_text("labels = 3\n", encoding="utf-8")
    with pytest.raises(RecordError):
        load_labels(path)


def test_check_refuses_by_target_and_reason() -> None:
    working = SupportLabelSet(
        preregistration_hash=PREREG,
        labels=(
            label("t1", "supported", "fits"),
            label("t2", "supported", "fits", "dev"),
            label("t3", "supported", "fits"),
            label("t4", "supported", "fits"),
            label("t9", "supported", "fits"),
        ),
    )
    refusals = check_labels(
        working,
        partition=Partition.TRAIN,
        sample=("t1", "t3", "t4", "t5", "t2"),
        input_hashes={"t1": INPUT, "t2": INPUT, "t3": "c" * 64},
        preregistration_hash="d" * 64,
    )
    assert refusals == sorted(
        [
            Refusal("labels", "preregistration_mismatch"),
            Refusal("t2", "wrong_partition"),
            Refusal("t3", "target_hash_mismatch"),
            Refusal("t4", "unknown_target"),
            Refusal("t9", "not_sampled"),
            Refusal("t5", "not_labelled"),
        ]
    )


def test_a_matching_working_file_has_nothing_to_refuse() -> None:
    working = SupportLabelSet(
        preregistration_hash=PREREG, labels=(label("t1", "unsure", "unsure"),)
    )
    assert (
        check_labels(
            working,
            partition=Partition.TRAIN,
            sample=("t1",),
            input_hashes={"t1": INPUT},
            preregistration_hash=PREREG,
        )
        == []
    )


def test_merging_adds_dev_and_extends_train_but_never_changes_labels() -> None:
    train = SupportLabelSet(
        preregistration_hash=PREREG, labels=(label("t1", "supported", "fits"),)
    )
    committed = merge_labels(None, train, Partition.TRAIN)
    dev = SupportLabelSet(
        preregistration_hash=PREREG, labels=(label("d1", "unsure", "fits", "dev"),)
    )
    both = merge_labels(committed, dev, Partition.DEV)
    assert {x.target_id for x in both.labels} == {"t1", "d1"}
    assert merge_labels(both, dev, Partition.DEV) == both
    extended = SupportLabelSet(
        preregistration_hash=PREREG,
        train_extensions=1,
        labels=(label("t1", "supported", "fits"), label("t2", "unsure", "fits")),
    )
    grown = merge_labels(both, extended, Partition.TRAIN)
    assert grown.train_extensions == 1
    assert {x.target_id for x in grown.of(Partition.TRAIN)} == {"t1", "t2"}
    changed = SupportLabelSet(
        preregistration_hash=PREREG, labels=(label("t1", "unsupported", "fits"),)
    )
    with pytest.raises(EvaluationError, match="labels_changed"):
        merge_labels(both, changed, Partition.TRAIN)
    other = SupportLabelSet(preregistration_hash="e" * 64, labels=())
    with pytest.raises(EvaluationError, match="preregistration_mismatch"):
        merge_labels(both, other, Partition.DEV)
```

In `tests/contracts/test_data_dictionary.py`, add `labels,` to the `from earnings_themes.evaluation import (...)` block, in alphabetical order.

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_MODELS`:

```python
    labels.SupportLabel,
    labels.SupportLabelSet,
```

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_ENUMS`:

```python
    labels.ClaimAnswer,
    labels.FitAnswer,
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_labels.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`2 errors`), with `ImportError: cannot import name 'labels' from 'earnings_themes.evaluation'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.labels'`.

- [x] **Step 3: Write the implementation**
> Deviation (final review): `merge_labels`' `labels_changed` names the sorted IDs of the committed labels the working partition drops or changes (the added IDs when it only adds), not the partition.

Create `packages/earnings-themes/src/earnings_themes/evaluation/labels.py`:

```python
"""The user's support labels (the Stage 11 spec, A4 and §Labels; FP8, FP17, FP21;
R8.4).

- **Two answers per target** (FP21): does the cited evidence support the claim,
  and does the claim fit the theme? Either may be ``unsure``.
- **Derived labels.** The claim label is the first answer, ``unsure`` left out. The
  joint label is 1 when both answers are positive, 0 when either is negative, and
  left out otherwise. A label left out is counted, never a negative.
- **Committed as IDs, hashes and answers** (FP17): no free-text field exists, so the
  file cannot hold a release's words (GS3).
- **The working file.** The user writes one partition's labels into a local file of
  the same shape; ``check_labels`` checks it against the sample and the support run,
  and ``merge_labels`` adds it to the committed file.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Literal, Self

from pydantic import NonNegativeInt, model_validator

from earnings_themes import tomlfile
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.problems import Refusal
from earnings_themes.records import NonBlank, Part, Sha256Hex, ThemesRecord, parse
from earnings_themes.split import Partition
from earnings_themes.support.metrics import HumanLabel, LabelTask

LABELLED = (Partition.TRAIN, Partition.DEV)
HEADER = (
    "Stage 11 support labels (FP8, FP17, FP21): target IDs, input hashes and the"
    " user's answers, never text. Written by `earnings-pipeline pilot labels check`."
)


class ClaimAnswer(StrEnum):
    """Does the cited evidence support the claim, with its attribution, time,
    scope and polarity?"""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNSURE = "unsure"


class FitAnswer(StrEnum):
    """Does the claim fit the theme's definition and its rules?"""

    FITS = "fits"
    DOES_NOT_FIT = "does_not_fit"
    UNSURE = "unsure"


class SupportLabel(Part):
    """One target's two answers, bound to the input the support run assessed."""

    target_id: NonBlank
    target_input_hash: Sha256Hex
    partition: Partition
    claim_support: ClaimAnswer
    theme_fit: FitAnswer
    labelled_on: date

    @model_validator(mode="after")
    def _train_or_dev(self) -> Self:
        if self.partition not in LABELLED:
            raise ValueError("only train and dev targets are labelled")
        return self


class SupportLabelSet(ThemesRecord):
    """``labels/support-labels-v1.toml``, or a working file of one partition."""

    preregistration_hash: Sha256Hex
    train_extensions: NonNegativeInt = 0
    labels: tuple[SupportLabel, ...] = ()

    @model_validator(mode="after")
    def _one_label_per_target(self) -> Self:
        ids = [label.target_id for label in self.labels]
        if len(ids) != len(set(ids)):
            raise ValueError("one label per target")
        return self

    def of(self, partition: Partition) -> tuple[SupportLabel, ...]:
        return tuple(label for label in self.labels if label.partition is partition)


def claim_label(label: SupportLabel) -> Literal[0, 1] | None:
    """The claim-support label; ``unsure`` is left out."""
    return {ClaimAnswer.SUPPORTED: 1, ClaimAnswer.UNSUPPORTED: 0}.get(
        label.claim_support
    )


def joint_label(label: SupportLabel) -> Literal[0, 1] | None:
    """1 when both answers are positive, 0 when either is negative, else left out."""
    claim, fit = label.claim_support, label.theme_fit
    if claim is ClaimAnswer.UNSUPPORTED or fit is FitAnswer.DOES_NOT_FIT:
        return 0
    if claim is ClaimAnswer.SUPPORTED and fit is FitAnswer.FITS:
        return 1
    return None


def human_labels(
    labels: Sequence[SupportLabel], task: LabelTask
) -> tuple[HumanLabel, ...]:
    """``labels`` as Stage 8's ``HumanLabel`` for ``task``, those left out omitted."""
    derive = claim_label if task == "claim_support" else joint_label
    return tuple(
        HumanLabel(target_id=label.target_id, task=task, supported=value)
        for label in labels
        if (value := derive(label)) is not None
    )


def usable(labels: Sequence[SupportLabel]) -> int:
    """How many labels have a joint label (R8.4: calibration needs 50 from train)."""
    return sum(joint_label(label) is not None for label in labels)


def _order(label: SupportLabel) -> tuple[int, str]:
    return LABELLED.index(label.partition), label.target_id


def labels_toml(labels: SupportLabelSet) -> str:
    """The committed file: train then dev, each by target ID."""
    ordered = labels.model_copy(
        update={"labels": tuple(sorted(labels.labels, key=_order))}
    )
    return tomlfile.dumps(ordered.model_dump(mode="python"), header=HEADER)


def load_labels(path: Path) -> SupportLabelSet:
    return parse(tomlfile.read(path), SupportLabelSet, path.name)


def check_labels(
    working: SupportLabelSet,
    *,
    partition: Partition,
    sample: Sequence[str],
    input_hashes: Mapping[str, str],
    preregistration_hash: str,
) -> list[Refusal]:
    """Why ``working`` is not ``partition``'s labels for ``sample``: each refusal
    names a target ID and a reason, never an answer (§Labels)."""
    refusals = []
    if working.preregistration_hash != preregistration_hash:
        refusals.append(Refusal("labels", EvaluationProblem.PREREGISTRATION_MISMATCH))
    sampled = set(sample)
    for label in working.labels:
        subject = label.target_id
        if label.partition is not partition:
            refusals.append(Refusal(subject, EvaluationProblem.WRONG_PARTITION))
        elif subject not in sampled:
            refusals.append(Refusal(subject, EvaluationProblem.NOT_SAMPLED))
        elif subject not in input_hashes:
            refusals.append(Refusal(subject, EvaluationProblem.UNKNOWN_TARGET))
        elif input_hashes[subject] != label.target_input_hash:
            refusals.append(Refusal(subject, EvaluationProblem.TARGET_HASH_MISMATCH))
    labelled = {label.target_id for label in working.labels}
    refusals += [
        Refusal(target_id, EvaluationProblem.NOT_LABELLED)
        for target_id in sample
        if target_id not in labelled
    ]
    return sorted(refusals)


def merge_labels(
    committed: SupportLabelSet | None,
    working: SupportLabelSet,
    partition: Partition,
) -> SupportLabelSet:
    """``committed`` with ``working``'s ``partition`` labels added. A partition
    already committed changes only when train is extended (§Failure handling): its
    committed labels kept as they are, and more extensions."""
    new = working.of(partition)
    if committed is None:
        return working.model_copy(update={"labels": new})
    if committed.preregistration_hash != working.preregistration_hash:
        raise EvaluationError(EvaluationProblem.PREREGISTRATION_MISMATCH, "labels")
    old = committed.of(partition)
    extensions = committed.train_extensions
    if old and set(old) != set(new):
        extended = (
            partition is Partition.TRAIN
            and set(old) <= set(new)
            and working.train_extensions > committed.train_extensions
        )
        if not extended:
            raise EvaluationError(EvaluationProblem.LABELS_CHANGED, partition.value)
    if partition is Partition.TRAIN:
        extensions = max(extensions, working.train_extensions)
    kept = tuple(
        label for label in committed.labels if label.partition is not partition
    )
    return committed.model_copy(
        update={"labels": (*kept, *new), "train_extensions": extensions}
    )
```

Append to the end of `docs/data-dictionary.md`, after one blank line:

```markdown
### `ClaimAnswer`

| Value | Meaning |
| --- | --- |
| `supported` | The evidence supports the claim |
| `unsupported` | It does not |
| `unsure` | The user cannot tell; left out |

### `FitAnswer`

| Value | Meaning |
| --- | --- |
| `fits` | The claim fits the theme |
| `does_not_fit` | It does not |
| `unsure` | The user cannot tell; left out |

### `SupportLabel`

| Field | Meaning |
| --- | --- |
| `target_id` | The support target |
| `target_input_hash` | Its `TargetRecord.input_hash` in the support run |
| `partition` | `train` or `dev` |
| `claim_support` | The `ClaimAnswer` |
| `theme_fit` | The `FitAnswer` |
| `labelled_on` | The date the user labelled it |

### `SupportLabelSet`

| Field | Meaning |
| --- | --- |
| `schema_version` | `1` |
| `preregistration_hash` | The preregistration whose sample it labels |
| `train_extensions` | Preregistered extensions drawn for train |
| `labels` | Each `SupportLabel`, one per target |
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_labels.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `413 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_labels.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/labels.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_labels.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/labels.py docs/data-dictionary.md
git commit -m "feat(themes): support labels and labels check (A4)"
```

---

### Task 10: `sampling`: the label pool and the deterministic sampler (A4; FP8, D19-12)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_sampling.py`
- Modify: `tests/contracts/test_data_dictionary.py` (imports; the evaluation registry)
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/sampling.py`
- Modify: `docs/data-dictionary.md` (the evaluation section: `PoolTarget`)

**Interfaces:**
- Consumes:
  - from Task 2: `problems.EvaluationError`, `problems.EvaluationProblem`
  - existing at `7948d94`: `earnings_core`: `digest`; `earnings_themes.support.records`: `ReviewOutcome`, `ReviewStatus`, `TargetRecord`
- Produces:
  - In `earnings_themes.evaluation.sampling`:
    - `POOL`
    - `class PoolTarget` (frozen dataclass): fields `target_id: str`, `event_id: str`, `theme_id: str`
    - `label_pool(targets: Sequence[TargetRecord], outcomes: Sequence[ReviewOutcome], events_by_doc: Mapping[str, str]) -> tuple[PoolTarget, ...]`
    - `sample_targets(pool: Sequence[PoolTarget], *, seed: int, size: int, cap: int) -> tuple[str, ...]`

`label_pool` keeps the support run's `assessed` and `flagged` targets (A4). `sample_targets` takes only target, event and theme IDs, so it cannot sample by a score, an answer or an outcome, and a signature test pins that. Its seeded round-robin (D19-12) has a known answer, and a larger size extends the same sample.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_sampling.py`:

```python
"""The label sampler: IDs only, seeded-hash order, round-robin, capped, and
extensible (the Stage 11 spec, A4; FP8)."""

import inspect
from collections import Counter
from dataclasses import fields

import pytest
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.evaluation.sampling import PoolTarget, sample_targets

POOL = tuple(
    PoolTarget(f"{event}-{theme}-{n}", event, theme)
    for event in ("e1", "e2", "e3")
    for theme in ("capacity", "demand")
    for n in range(3)
)


def test_the_sampler_sees_only_ids() -> None:
    assert list(inspect.signature(sample_targets).parameters) == [
        "pool",
        "seed",
        "size",
        "cap",
    ]
    assert [f.name for f in fields(PoolTarget)] == ["target_id", "event_id", "theme_id"]


def test_the_known_sample() -> None:
    """Pins the digest ranks and the round-robin (R14.6)."""
    assert sample_targets(POOL, seed=19, size=7, cap=3) == (
        "e1-demand-1",
        "e2-capacity-1",
        "e3-demand-0",
        "e1-capacity-2",
        "e2-demand-1",
        "e3-capacity-0",
        "e1-demand-2",
    )


def test_rounds_take_one_target_per_event_and_alternate_themes() -> None:
    drawn = sample_targets(POOL, seed=19, size=9, cap=3)
    events = [t.split("-")[0] for t in drawn]
    assert sorted(events[:3]) == ["e1", "e2", "e3"]
    assert Counter(events) == {"e1": 3, "e2": 3, "e3": 3}
    for event in ("e1", "e2", "e3"):
        themes = [t.split("-")[1] for t in drawn if t.startswith(event)]
        assert themes[0] != themes[1]


def test_the_cap_and_the_size_bound_the_sample() -> None:
    assert len(sample_targets(POOL, seed=19, size=100, cap=2)) == 6
    assert len(sample_targets(POOL, seed=19, size=4, cap=3)) == 4
    assert sample_targets((), seed=19, size=4, cap=3) == ()


def test_a_larger_size_extends_the_same_sample() -> None:
    small = sample_targets(POOL, seed=19, size=5, cap=3)
    large = sample_targets(POOL, seed=19, size=8, cap=3)
    assert large[:5] == small


def test_the_seed_decides_the_order_and_nothing_else_does() -> None:
    assert sample_targets(POOL, seed=19, size=9, cap=3) == sample_targets(
        tuple(reversed(POOL)), seed=19, size=9, cap=3
    )
    assert sample_targets(POOL, seed=19, size=9, cap=3) != sample_targets(
        POOL, seed=20, size=9, cap=3
    )


def test_a_repeated_target_is_refused() -> None:
    with pytest.raises(EvaluationError, match="duplicate_target"):
        sample_targets((*POOL, POOL[0]), seed=19, size=3, cap=3)
```

In `tests/contracts/test_data_dictionary.py`, add `sampling,` to the `from earnings_themes.evaluation import (...)` block, in alphabetical order.

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_DATACLASSES`:

```python
    sampling.PoolTarget,
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_sampling.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`2 errors`), with `ImportError: cannot import name 'sampling' from 'earnings_themes.evaluation'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.sampling'`.

- [x] **Step 3: Write the implementation**
> Deviation (final review): `sample_targets`' `duplicate_target` names the repeated target ID, through the shared `problems.first_duplicate`.

Create `packages/earnings-themes/src/earnings_themes/evaluation/sampling.py`:

```python
"""The label sample (the Stage 11 spec, A4 and §Preregistration; FP8).

- **The pool** is the partition's ``assessed`` and ``flagged`` targets; ``refused``
  and ``incomplete`` targets are left out (``label_pool``).
- **The sampler** sees only target, event and theme IDs, so it cannot sample by a
  score, a judge answer or an outcome.
- **Seeded-hash order.** Events, an event's themes, and a theme's targets are each
  ordered by the digest of the seed and their IDs. Within an event the sampler
  round-robins across its themes; across events it takes one target per event per
  round, at most ``cap`` from any event, until it holds ``size`` or every event is
  at its cap or exhausted.
- **Extension.** With the cap fixed, a larger size draws a sample that begins with
  the smaller one, so a preregistered extension adds to the labels already written
  (§Failure handling).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from earnings_core import digest

from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.support.records import ReviewOutcome, ReviewStatus, TargetRecord

POOL = (ReviewStatus.ASSESSED, ReviewStatus.FLAGGED)


@dataclass(frozen=True)
class PoolTarget:
    """A target the sampler may draw: its ID, its event, and its proposed theme."""

    target_id: str
    event_id: str
    theme_id: str


def label_pool(
    targets: Sequence[TargetRecord],
    outcomes: Sequence[ReviewOutcome],
    events_by_doc: Mapping[str, str],
) -> tuple[PoolTarget, ...]:
    """The ``assessed`` and ``flagged`` targets, each with its event (FP8)."""
    status = {outcome.target_id: outcome.status for outcome in outcomes}
    pool = []
    for record in targets:
        if status.get(record.target_id) not in POOL:
            continue
        event_id = events_by_doc.get(record.target.doc_id)
        if event_id is None:
            raise EvaluationError(EvaluationProblem.UNKNOWN_EVENT, record.target_id)
        pool.append(PoolTarget(record.target_id, event_id, record.target.theme_id))
    return tuple(pool)


def _rank(seed: int, *ids: str) -> str:
    return digest({"seed": seed, "ids": list(ids)})


def sample_targets(
    pool: Sequence[PoolTarget], *, seed: int, size: int, cap: int
) -> tuple[str, ...]:
    """The sampled target IDs, in draw order."""
    if len({t.target_id for t in pool}) != len(pool):
        raise EvaluationError(EvaluationProblem.DUPLICATE_TARGET, "pool")
    themes: dict[str, dict[str, list[str]]] = {}
    for target in pool:
        by_theme = themes.setdefault(target.event_id, {})
        by_theme.setdefault(target.theme_id, []).append(target.target_id)
    queues: dict[str, list[str]] = {}
    for event_id, by_theme in themes.items():
        lanes = [
            sorted(ids, key=lambda i, t=theme: _rank(seed, event_id, t, i))
            for theme, ids in sorted(
                by_theme.items(), key=lambda kv: _rank(seed, event_id, kv[0])
            )
        ]
        depth = max(len(lane) for lane in lanes)
        queue = [lane[r] for r in range(depth) for lane in lanes if r < len(lane)]
        queues[event_id] = queue[:cap]
    events = sorted(queues, key=lambda e: _rank(seed, e))
    drawn = [queues[e][r] for r in range(cap) for e in events if r < len(queues[e])]
    return tuple(drawn[:size])
```

Append to the end of `docs/data-dictionary.md`, after one blank line:

```markdown
### `PoolTarget`

| Field | Meaning |
| --- | --- |
| `target_id` | An `assessed` or `flagged` target |
| `event_id` | Its event |
| `theme_id` | Its proposed theme |
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_sampling.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `407 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_sampling.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/sampling.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_sampling.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/sampling.py docs/data-dictionary.md
git commit -m "feat(themes): the deterministic label sampler (A4)"
```

---

### Task 11: `label_view`: the local label view (A4; D19-17)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/conftest.py`
- Create: `packages/earnings-themes/tests/evaluation/test_label_view.py`
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/label_view.py`

**Interfaces:**
- Consumes:
  - from Task 2: `problems.EvaluationError`, `problems.EvaluationProblem`
  - from Task 10: `sampling.PoolTarget`, `sampling.label_pool`
  - existing at `7948d94`: `earnings_themes.support.context`: `context_elements`; `earnings_themes.support.records`: `EvidenceReference`, `StoredSupportRun`, `SupportSources`; `earnings_themes.support`: `reverify_support_run`
- Produces:
  - In `earnings_themes.evaluation.label_view`:
    - `INSTRUCTIONS`
    - `label_views(support: StoredSupportRun, sources: SupportSources, sample: Sequence[str]) -> str`

`label_views` renders the markdown the user labels from. For each sampled target it shows the claim, the quotes marked in their context through Stage 8's `context_elements`, and the theme's definition and rules (D19-17). A sentinel test plants a score, a judge answer, a flag and the extractor's identity in a flagged case, and shows that none reaches the view. `tests/evaluation/conftest.py` reuses Stage 9's invented assessed case.

- [x] **Step 1: Write the failing tests**
> Deviation (final review): the label view's blinding sentinel is rewritten to read the text after `INSTRUCTIONS`, plant the review-status words and the judge's score, and fail when a verdict or status is rendered.

Create `packages/earnings-themes/tests/evaluation/conftest.py`:

```python
"""Stage 9's invented assessed case, reused from the coding tests: one invented
document, claim, quote and theme, assessed by scripted judges (GS13)."""

from importlib import import_module

_coding = import_module("packages.earnings-themes.tests.coding.conftest")

coding_case = _coding.coding_case
coding_policy = _coding.coding_policy
classifier_identity = _coding.classifier_identity
proposal_job = _coding.proposal_job
assessed_case = _coding.assessed_case
```

Create `packages/earnings-themes/tests/evaluation/test_label_view.py`:

```python
"""The label view and the label pool (the Stage 11 spec, A4; FP8). The view shows
the claim, its quotes in context and the theme, and nothing a model said."""

from importlib import import_module

import pytest
from earnings_themes.evaluation.label_view import label_views
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.evaluation.sampling import PoolTarget, label_pool
from earnings_themes.support import reverify_support_run

_cases = import_module("packages.earnings-themes.tests.coding.cases")


@pytest.fixture
def flagged_case(assessed_case, tmp_path):
    """The same target, judged with a marked score and an uncertain quote, so its
    view could leak either."""
    return _cases.make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "flagged",
        parts=_cases.make_support_parts("uncertain", score=0.123456789),
    )


def test_the_view_shows_the_claim_quote_and_theme(assessed_case) -> None:
    case = assessed_case
    target = case.support.targets[0]
    view = label_views(case.support, case.sources, (target.target_id,))
    assert f"## 1. {target.target_id}" in view
    assert "**Claim:** An invented operating claim." in view
    assert "⟦Lumen added a press and served more orders.⟧" in view
    assert "**Theme:** Capacity" in view
    assert "- Explicit equipment or facility expansion." in view
    assert "- Orders without equipment changes." in view


def test_the_view_holds_no_score_answer_flag_or_model_identity(flagged_case) -> None:
    case = flagged_case
    reverify_support_run(case.support, case.sources)
    assert case.support.outcomes[0].status == "flagged"
    target = case.support.targets[0]
    view = label_views(case.support, case.sources, (target.target_id,))
    for planted in (
        "0.123456789",
        "0.12345",
        "Invented fixture assessment",
        "uncertain",
        "quote_uncertain",
        "invented-support",
        "invented-family",
        "invented-extractor",
        "scripted",
        case.support.record.run_id,
        case.sources.stored_run.record.run_id,
    ):
        assert planted not in view, planted


def test_an_unknown_target_is_refused(assessed_case) -> None:
    case = assessed_case
    with pytest.raises(EvaluationError, match="unknown_target"):
        label_views(case.support, case.sources, ("support-unknown",))


def test_the_pool_is_assessed_and_flagged_targets_with_their_events(
    assessed_case, flagged_case
) -> None:
    for case in (assessed_case, flagged_case):
        target = case.support.targets[0]
        events = {target.target.doc_id: "e1"}
        assert label_pool(case.support.targets, case.support.outcomes, events) == (
            PoolTarget(target.target_id, "e1", target.target.theme_id),
        )
    refused = flagged_case.support.outcomes[0].model_copy(update={"status": "refused"})
    assert label_pool(flagged_case.support.targets, (refused,), events) == ()
    with pytest.raises(EvaluationError, match="unknown_event"):
        label_pool(flagged_case.support.targets, flagged_case.support.outcomes, {})
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_label_view.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`1 error`), with `ModuleNotFoundError: No module named 'earnings_themes.evaluation.label_view'`.

- [x] **Step 3: Write the implementation**

Create `packages/earnings-themes/src/earnings_themes/evaluation/label_view.py`:

```python
"""The local label view (the Stage 11 spec, A4 and §Labels; FP8; GS13).

For each sampled target, in sample order: its claim, each quote in its block with
the nearest heading, and the theme's definition and rules. It holds no score, no
judge answer, no flag or reason code, and no model's identity, so the user labels
unaided (FP8). The view holds release text, so it is written only under
``data/runs/pilot/labels/views/`` and never printed (A8).
"""

from collections.abc import Sequence

from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.support.context import context_elements
from earnings_themes.support.records import (
    EvidenceReference,
    StoredSupportRun,
    SupportSources,
)

INSTRUCTIONS = (
    "Answer two questions for each target, from this view alone:\n"
    "- claim_support: does the cited evidence support the claim, with its"
    " attribution, time, scope and polarity? supported, unsupported or unsure.\n"
    "- theme_fit: does the claim fit the theme's definition and its rules?"
    " fits, does_not_fit or unsure.\n"
    "Each quote is shown in its block, between ⟦ and ⟧."
)


def _flat(text: str) -> str:
    return " ".join(text.split())


def _quote(
    text: str, sources: SupportSources, evidence: EvidenceReference
) -> list[str]:
    bundle = next(b for b in sources.bundles if b.document.doc_id == evidence.doc_id)
    context = context_elements(bundle, evidence.element_id)
    block = context[-1].span
    start, end = evidence.start, evidence.end
    lines = []
    if len(context) == 2:
        heading = context[0].span
        lines.append(f"*{_flat(text[heading.start : heading.end])}*")
    before = text[block.start : start] if block.start <= start else ""
    after = text[end : block.end] if end <= block.end else ""
    lines.append(
        f"> {_flat(before)} ⟦{_flat(text[start:end])}⟧ {_flat(after)}".rstrip()
    )
    return lines


def label_views(
    support: StoredSupportRun, sources: SupportSources, sample: Sequence[str]
) -> str:
    """The markdown view of ``sample``'s targets, from a reverified support run."""
    targets = {t.target_id: t for t in support.targets}
    claims = {(c.doc_id, c.claim_id): c.claim for c in sources.stored_run.claims}
    texts = {b.document.doc_id: b.document.canonical_text for b in sources.bundles}
    out = ["# Support labels", "", INSTRUCTIONS]
    for number, target_id in enumerate(sample, 1):
        record = targets.get(target_id)
        if record is None:
            raise EvaluationError(EvaluationProblem.UNKNOWN_TARGET, target_id)
        target, theme = record.target, record.theme
        claim = claims.get((target.doc_id, target.claim_id))
        if theme is None or claim is None or target.doc_id not in texts:
            raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, target_id)
        out += ["", f"## {number}. {target_id}", "", f"**Claim:** {_flat(claim)}", ""]
        for evidence in support.evidence:
            if evidence.target_id == target_id:
                out += [*_quote(texts[target.doc_id], sources, evidence), ""]
        out += [f"**Theme:** {_flat(theme.label)}", "", _flat(theme.definition), ""]
        out += ["Include when:", *(f"- {_flat(r)}" for r in theme.inclusion_rules)]
        out += ["Exclude when:", *(f"- {_flat(r)}" for r in theme.exclusion_rules)]
    return "\n".join(out) + "\n"
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_label_view.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `404 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/conftest.py packages/earnings-themes/tests/evaluation/test_label_view.py packages/earnings-themes/src/earnings_themes/evaluation/label_view.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/conftest.py packages/earnings-themes/tests/evaluation/test_label_view.py packages/earnings-themes/src/earnings_themes/evaluation/label_view.py
git commit -m "feat(themes): the support label view (A4)"
```

---

### Task 12: Stage 8 and 9 seams: `decision_inputs` and `accepted_claim_recall` (A5; D19-5)

**Files:**
- Modify: `packages/earnings-themes/tests/coding/test_decide.py`
- Modify: `packages/earnings-themes/tests/support/test_metrics.py` (`:7-12`)
- Modify: `packages/earnings-themes/src/earnings_themes/coding/decide.py` (`:271-276`, `:372-396`)
- Modify: `packages/earnings-themes/src/earnings_themes/support/metrics.py` (`:45-50`)
- Modify: `docs/data-dictionary.md` (`:3623-3628`, `:3653-3659`, `:4319-4324`; three Stage 8 and 9 paragraphs and rows)

**Interfaces:**
- Consumes:
  - nothing from an earlier task.
- Produces:
  - In `earnings_themes.coding.decide`: `decision_input(support: StoredSupportRun, target: TargetRecord, outcome: ReviewOutcome) -> DecisionInput` and `decision_inputs(support: StoredSupportRun, sources: SupportSources) -> dict[str, DecisionInput]`, which raises `CodingError` with a closed reason.
  - In `earnings_themes.support.metrics`: `accepted_claim_recall(population: Sequence[str], labels: Sequence[HumanLabel], decisions: Sequence[Acceptance], *, task: LabelTask) -> MetricReport`; `MetricReport.reason` gains `no_labeled_positive`.

Two seams that calibration needs, extracted rather than copied (D18-1):
- `decision_input` is `decide_assignments`' inline view-building block, moved out unchanged.
- `decision_inputs` reverifies a support run and builds every target's view, so calibration votes on exactly what Stage 9 votes on (D19-5).
- `accepted_claim_recall` is label recall, beside Stage 8's `accepted_claim_precision`, with a new `no_labeled_positive` reason. No record stores a `MetricReport` before this plan; Task 14's `CalibrationArtifact` is the first.

- [x] **Step 1: Write the failing tests**

Append to the end of `packages/earnings-themes/tests/coding/test_decide.py`, after two blank lines:

```python
def test_decision_inputs_are_the_views_decide_assignments_votes_on(
    assessed_case, contextual_case, fixture_policy
) -> None:
    from earnings_themes.coding.decide import decision_inputs, decision_vote

    target = assessed_case.support.targets[0]
    view = decision_inputs(assessed_case.support, assessed_case.sources)[
        target.target_id
    ]
    assert view.outcome.status == "assessed"
    assert view.eligible_quote_ids == tuple(
        sorted(e.quote_id for e in assessed_case.support.evidence)
    )
    decided = assessed_case.decide(fixture_policy).decisions[0]
    assert decision_vote(view, fixture_policy)[0] == decided.status == "accepted"
    contextual = decision_inputs(contextual_case.support, contextual_case.sources)
    assert contextual[target.target_id].eligible_quote_ids == ()
```

In `packages/earnings-themes/tests/support/test_metrics.py`, replace:

```python
    HumanLabel,
    MetricReport,
    accepted_claim_precision,
    auc_roc,
)
from pydantic import ValidationError
```

with:

```python
    HumanLabel,
    MetricReport,
    accepted_claim_precision,
    accepted_claim_recall,
    auc_roc,
)
from pydantic import ValidationError
```

Append to the end of `packages/earnings-themes/tests/support/test_metrics.py`, after two blank lines:

```python
def test_accepted_claim_recall_is_the_share_of_supported_labels_accepted() -> None:
    labels = [label("a", 1), label("b", 1), label("c", 0), label("d", 1)]
    decisions = [
        Acceptance(target_id=target, task=TASK, accepted=accepted)
        for target, accepted in (("a", True), ("b", False), ("c", True), ("e", True))
    ]
    report = accepted_claim_recall(
        ["a", "b", "c", "d", "e"], labels, decisions, task=TASK
    )
    assert report.value == pytest.approx(1 / 3)
    assert (
        report.joined_count,
        report.accepted_count,
        report.accepted_without_label_count,
        report.missing_label_count,
    ) == (3, 3, 1, 1)
    none = accepted_claim_recall(["c"], labels[2:3], decisions[2:3], task=TASK)
    assert (none.value, none.reason) == (None, "no_labeled_positive")
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/coding/test_decide.py packages/earnings-themes/tests/support/test_metrics.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`1 error`), with `ImportError: cannot import name 'accepted_claim_recall' from 'earnings_themes.support.metrics'`.

- [x] **Step 3: Write the implementation**
> Deviation (Task 12 fix round, user decision 2026-10-12): `accepted_claim_recall` and `accepted_claim_precision` share a private `_acceptance_join` and `_acceptance_report` in `support/metrics.py` (D18-1); four `MetricReport` dictionary rows name recall; a defined-0.0 recall test is added.

In `packages/earnings-themes/src/earnings_themes/coding/decide.py`, replace:

```python
    )


def _view_hash(view: DecisionInput) -> str:
    return digest(
        {
```

with:

```python
    )


def decision_input(
    support: StoredSupportRun, target: TargetRecord, outcome: ReviewOutcome
) -> DecisionInput:
    """One stored target's view: its evidence, signals and trials, and, when it is
    ``assessed``, its eligible quotes. ``outcome`` is the reverified outcome."""
    evidence = tuple(
        row for row in support.evidence if row.target_id == target.target_id
    )
    entailment = tuple(
        row for row in support.entailment if row.target_id == target.target_id
    )
    trials = tuple(row for row in support.trials if row.target_id == target.target_id)
    eligible = (
        eligible_quote_ids(evidence, trials) if outcome.status == "assessed" else ()
    )
    return DecisionInput(target, evidence, entailment, trials, outcome, eligible)


def decision_inputs(
    support: StoredSupportRun, sources: SupportSources
) -> dict[str, DecisionInput]:
    """Every stored target's view, by target ID, after the consuming gate
    reverifies the run, as ``decide_assignments`` builds them (Stage 11's
    calibration reads exactly these, plan 19)."""
    try:
        outcomes = {o.target_id: o for o in reverify_support_run(support, sources)}
        return {
            target.target_id: decision_input(
                support, target, outcomes[target.target_id]
            )
            for target in support.targets
        }
    except CodingError:
        raise
    except SupportError as error:
        raise CodingError(str(error)) from None
    except Exception:  # noqa: BLE001 - boundary failures never print source data
        raise CodingError("unexpected_error") from None


def _view_hash(view: DecisionInput) -> str:
    return digest(
        {
```

In `packages/earnings-themes/src/earnings_themes/coding/decide.py`, replace:

```python
                support_status, flags, missing = None, (), ("missing_assessment",)
            else:
                outcome = by_id[target.target_id]
                evidence = tuple(
                    row for row in support.evidence if row.target_id == target.target_id
                )
                entailment = tuple(
                    row
                    for row in support.entailment
                    if row.target_id == target.target_id
                )
                trials = tuple(
                    row for row in support.trials if row.target_id == target.target_id
                )
                eligible = (
                    eligible_quote_ids(evidence, trials)
                    if outcome.status == "assessed"
                    else ()
                )
                view = DecisionInput(
                    target, evidence, entailment, trials, outcome, eligible
                )
                status, reason, quote_ids = decision_vote(view, policy)
                require_current()
                target_id = target.target_id
```

with:

```python
                support_status, flags, missing = None, (), ("missing_assessment",)
            else:
                outcome = by_id[target.target_id]
                view = decision_input(support, target, outcome)
                status, reason, quote_ids = decision_vote(view, policy)
                require_current()
                target_id = target.target_id
```

In `packages/earnings-themes/src/earnings_themes/support/metrics.py`, replace:

```python
class MetricReport(SafePart):
    value: Score | None
    reason: Literal["no_scored_labels", "one_class", "no_labeled_accepted"] | None
    task: LabelTask
    view: NonBlank = Field(repr=False)
    population_count: NonNegativeInt
```

with:

```python
class MetricReport(SafePart):
    value: Score | None
    reason: (
        Literal[
            "no_scored_labels",
            "one_class",
            "no_labeled_accepted",
            "no_labeled_positive",
        ]
        | None
    )
    task: LabelTask
    view: NonBlank = Field(repr=False)
    population_count: NonNegativeInt
```

Append to the end of `packages/earnings-themes/src/earnings_themes/support/metrics.py`, after two blank lines:

```python
def accepted_claim_recall(
    population: Sequence[str],
    labels: Sequence[HumanLabel],
    decisions: Sequence[Acceptance],
    *,
    task: LabelTask,
) -> MetricReport:
    """The share of supported labels that external decisions accepted (Stage 11's
    label recall, plan 19); a target with no decision is not accepted."""
    ids = _population(population, task, "external_acceptance")
    human = _index(labels, HumanLabel, ids, task)
    external = _index(decisions, Acceptance, ids, task)
    accepted = {target_id for target_id, item in external.items() if item.accepted}
    positive = {target_id for target_id, item in human.items() if item.supported == 1}
    value = len(positive & accepted) / len(positive) if positive else None
    return MetricReport(
        value=value,
        reason=None if value is not None else "no_labeled_positive",
        task=task,
        view="external_acceptance",
        population_count=len(ids),
        labeled_count=len(human),
        scored_count=0,
        joined_count=len(positive),
        accepted_count=len(accepted),
        missing_score_count=0,
        missing_label_count=len(ids) - len(human),
        accepted_without_label_count=len(accepted - human.keys()),
    )
```

In `docs/data-dictionary.md`, replace:

```markdown
counts are zero. These functions establish semantics, not observed quality;
Stage 11 owns view selection, calibration, pooling, and thresholds.

### `HumanLabel`

| Field | Meaning |
```

with:

```markdown
counts are zero. These functions establish semantics, not observed quality;
Stage 11 owns view selection, calibration, pooling, and thresholds.

`accepted_claim_recall(population, labels, decisions, *, task)` (plan 19) is the
share of labels marked supported whose target an external decision accepted. Its
denominator is the human-labeled positive targets, reported as `joined_count`; no
such target yields `no_labeled_positive`. A target with no decision is not
accepted, and nothing is inferred. Stage 11's calibration reads it beside
precision, as label recall.

### `HumanLabel`

| Field | Meaning |
```

In `docs/data-dictionary.md`, replace:

```markdown
| Field | Meaning |
| --- | --- |
| `value` | Finite metric in `[0,1]`, or `None` when undefined. |
| `reason` | `None` for a defined value; otherwise `no_scored_labels`, `one_class`, or `no_labeled_accepted`. |
| `task` | Explicit selected label task. |
| `view` | Selected score view for AUC, or `external_acceptance` for precision. |
| `population_count` | Number of unique supplied population IDs. |
```

with:

```markdown
| Field | Meaning |
| --- | --- |
| `value` | Finite metric in `[0,1]`, or `None` when undefined. |
| `reason` | `None` for a defined value; otherwise `no_scored_labels`, `one_class`, `no_labeled_accepted`, or `no_labeled_positive`. |
| `task` | Explicit selected label task. |
| `view` | Selected score view for AUC, or `external_acceptance` for precision. |
| `population_count` | Number of unique supplied population IDs. |
```

In `docs/data-dictionary.md`, replace:

```markdown
label it `supporting`. This is an eligibility restriction, never sufficient
acceptance; contextual companions remain raw provenance.

`AssignmentPolicy.reference: PolicyReference` and
`evaluate(view: DecisionInput) -> PolicyVote` form a pure deterministic external
policy seam. No accepting implementation is shipped in the package. Tests supply
```

with:

```markdown
label it `supporting`. This is an eligibility restriction, never sufficient
acceptance; contextual companions remain raw provenance.

`decision_input(support, target, outcome) -> DecisionInput` builds one stored
target's view from its reverified outcome, and `decision_inputs(support, sources)
-> dict[str, DecisionInput]` reverifies the run and builds every target's view,
keyed by target ID, exactly as `decide_assignments` builds them (plan 19). Stage
11's calibration reads these, so a cutoff fitted on train decides as Stage 9 will.

`AssignmentPolicy.reference: PolicyReference` and
`evaluate(view: DecisionInput) -> PolicyVote` form a pure deterministic external
policy seam. No accepting implementation is shipped in the package. Tests supply
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/coding/test_decide.py packages/earnings-themes/tests/support/test_metrics.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `503 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/coding/test_decide.py packages/earnings-themes/tests/support/test_metrics.py packages/earnings-themes/src/earnings_themes/coding/decide.py packages/earnings-themes/src/earnings_themes/support/metrics.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/coding/test_decide.py packages/earnings-themes/tests/support/test_metrics.py packages/earnings-themes/src/earnings_themes/coding/decide.py packages/earnings-themes/src/earnings_themes/support/metrics.py docs/data-dictionary.md
git commit -m "feat(themes): decision_inputs and accepted_claim_recall for calibration (A5)"
```

---

### Task 13: `preregistration` (A5; FP9, D19-1, D19-11, D19-12, D19-13)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_preregistration.py`
- Modify: `tests/contracts/test_data_dictionary.py` (imports; the evaluation registry)
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/preregistration.py`
- Modify: `docs/data-dictionary.md` (the evaluation section: `FloorRule`, `Candidate`, `SelectionRule`, `SamplingPlan`, `GateRule`, `Preregistration`)

**Interfaces:**
- Consumes:
  - from Task 5: `bootstrap.BootstrapPlan`
  - from Task 6: `records.Metric`, `records.checked`, `records.sealed`
  - existing at `7948d94`: `earnings_themes.gold`: `CodebookRef`; `earnings_themes.records`: `IdPart`, `Part`, `Pin`, `RecordError`, `Sha256Hex`, `ThemesRecord`, `parse`; `earnings_themes.synthetic`: `PIN`; `earnings_themes`: `tomlfile`
- Produces:
  - In `earnings_themes.evaluation.preregistration`:
    - `Share`
    - `REQUIRED_GATES`
    - `NEVER_GATED`
    - `HEADER`
    - `class FloorRule(Part)`: fields `statistic: Literal['cohen_kappa']`, `reported: Literal['gwet_ac1']`, `population: Literal['family_verdict_vs_joint_label']`, `bound: Literal['event_bootstrap_lower']`, `floor: Annotated[float, Field(ge=0.3, le=0.6, allow_inf_nan=False)]`, `consequence: Literal['reported_only']`
    - `class Candidate(Part)`: fields `candidate_id: IdPart`, `rule: Literal['scorer_cutoff']`, `signal: Literal['minicheck_joint']`, `signals: PositiveInt`, `grid: Annotated[tuple[Share, ...], Field(min_length=1)]`
    - `class SelectionRule(Part)`: fields `recall_floor: Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)]`, `objective: Literal['max_train_precision']`, `tie_break: Literal['fewer_signals_then_lower_cutoff']`
    - `class SamplingPlan(Part)`: fields `seed: int`, `pool: Literal['assessed_and_flagged']`, `train_size: PositiveInt`, `train_cap: PositiveInt`, `dev_size: PositiveInt`, `dev_cap: PositiveInt`, `minimum_usable: Annotated[int, Field(ge=50)]`, `extension_step: PositiveInt`
    - `class GateRule(Part)`: fields `rule: Literal['dev-lower-bound/1']`, `gated: Annotated[tuple[Metric, ...], Field(min_length=1)]`, `undefined_gate: Literal['not_gated', 'point_estimate']`
    - `class Preregistration(ThemesRecord)`: fields `preregistration_version: PositiveInt`, `pin: Pin`, `split_hash: Sha256Hex`, `codebook: CodebookRef`, `floor: FloorRule`, `menu: Annotated[tuple[Candidate, ...], Field(min_length=1)]`, `selection: SelectionRule`, `sampling: SamplingPlan`, `bootstrap: BootstrapPlan`, `gates: GateRule`, `content_hash: Sha256Hex`
    - `freeze_preregistration(fields: Mapping[str, object]) -> Preregistration`
    - `preregistration_toml(record: Preregistration) -> str`
    - `load_preregistration(path: Path) -> Preregistration`

`Preregistration` is the committed file's schema (§Preregistration). It holds:
- the judge floor, which is reported only (D19-1);
- the scorer-cutoff menu and its grids, and the selection rule;
- the sampling plan (FP8, D19-12) and the bootstrap;
- V6's gate rule. Its gated metrics must include §Metrics' gated ones, and exclude its descriptive ones (D1).

`freeze_preregistration` seals it. `load_preregistration` refuses a file that no longer hashes to itself (D19-13).

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_preregistration.py`:

```python
"""The preregistration: its schema, its self-hash, and the gate list it must hold
(the Stage 11 spec, A5 and §Preregistration; FP9)."""

import pytest
from earnings_themes.evaluation.preregistration import (
    REQUIRED_GATES,
    freeze_preregistration,
    load_preregistration,
    preregistration_toml,
)
from earnings_themes.evaluation.records import Metric
from earnings_themes.records import RecordError
from earnings_themes.synthetic import PIN

HASH = "0" * 64


def fields(**changes) -> dict:
    """An invented preregistration's fields; the user picks the real numbers (B2)."""
    data = {
        "preregistration_version": 1,
        "pin": PIN.model_dump(mode="json"),
        "split_hash": HASH,
        "codebook": {
            "codebook_id": "invented",
            "codebook_version": 0,
            "content_hash": HASH,
        },
        "floor": {
            "statistic": "cohen_kappa",
            "reported": "gwet_ac1",
            "population": "family_verdict_vs_joint_label",
            "bound": "event_bootstrap_lower",
            "floor": 0.4,
            "consequence": "reported_only",
        },
        "menu": [
            {
                "candidate_id": "scorer-only",
                "rule": "scorer_cutoff",
                "signal": "minicheck_joint",
                "signals": 1,
                "grid": [0.0, 0.5, 0.9],
            }
        ],
        "selection": {
            "recall_floor": 0.5,
            "objective": "max_train_precision",
            "tie_break": "fewer_signals_then_lower_cutoff",
        },
        "sampling": {
            "seed": 19,
            "pool": "assessed_and_flagged",
            "train_size": 70,
            "train_cap": 5,
            "dev_size": 24,
            "dev_cap": 3,
            "minimum_usable": 50,
            "extension_step": 10,
        },
        "bootstrap": {
            "seed": 23,
            "resamples": 200,
            "level": 0.9,
            "max_undefined_share": 0.05,
        },
        "gates": {
            "rule": "dev-lower-bound/1",
            "gated": sorted(m.value for m in REQUIRED_GATES),
            "undefined_gate": "not_gated",
        },
    }
    return {**data, **changes}


def test_it_round_trips_and_hashes_itself(tmp_path) -> None:
    record = freeze_preregistration(fields())
    path = tmp_path / "preregistration-v1.toml"
    path.write_text(preregistration_toml(record), encoding="utf-8")
    assert load_preregistration(path) == record
    edited = path.read_text(encoding="utf-8").replace("floor = 0.4", "floor = 0.5")
    path.write_text(edited, encoding="utf-8")
    with pytest.raises(RecordError, match="content_hash"):
        load_preregistration(path)


@pytest.mark.parametrize(
    "gated",
    [
        sorted(m.value for m in REQUIRED_GATES - {Metric.SPAN_UNIT_F1}),
        sorted({*(m.value for m in REQUIRED_GATES), "rare_theme_recall"}),
    ],
)
def test_the_gates_must_be_the_specs(gated) -> None:
    gates = {"rule": "dev-lower-bound/1", "gated": gated, "undefined_gate": "not_gated"}
    with pytest.raises(RecordError, match="gated metrics"):
        freeze_preregistration(fields(gates=gates))


@pytest.mark.parametrize(
    ("section", "change"),
    [
        ("floor", {"floor": 0.7}),
        ("sampling", {"minimum_usable": 49}),
        ("selection", {"recall_floor": 0.0}),
    ],
)
def test_out_of_range_numbers_are_refused(section, change) -> None:
    data = fields()
    with pytest.raises(RecordError):
        freeze_preregistration({**data, section: {**data[section], **change}})


def test_an_unsorted_grid_is_refused() -> None:
    menu = [{**fields()["menu"][0], "grid": [0.5, 0.0]}]
    with pytest.raises(RecordError, match="sorted and unique"):
        freeze_preregistration(fields(menu=menu))
```

In `tests/contracts/test_data_dictionary.py`, add `preregistration,` to the `from earnings_themes.evaluation import (...)` block, in alphabetical order.

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_MODELS`:

```python
    preregistration.FloorRule,
    preregistration.Candidate,
    preregistration.SelectionRule,
    preregistration.SamplingPlan,
    preregistration.GateRule,
    preregistration.Preregistration,
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_preregistration.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`2 errors`), with `ImportError: cannot import name 'preregistration' from 'earnings_themes.evaluation'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.preregistration'`.

- [x] **Step 3: Write the implementation**
> Deviation (Task 13 fix round, user decision 2026-10-12): `GateRule` requires `gated` to equal `REQUIRED_GATES` exactly, so `NEVER_GATED` and the superset validator are gone; validator messages name the offending items; `_distinct_candidates` is a `field_validator("menu")`. Final review: `Preregistration.bootstrap.level` must be 0.9.

Create `packages/earnings-themes/src/earnings_themes/evaluation/preregistration.py`:

```python
"""The preregistration (the Stage 11 spec, A5 and §Preregistration; FP9, FP10,
FP15; R8.4).

``preregistration-v1.toml`` is committed on its own before any pilot output exists
(B2). It holds no text: the judge floor, the policy menu and its selection rule, the
label sample, the bootstrap, and V6's gate rule. It carries its own
``content_hash``, and ``load_preregistration`` refuses a file that does not hash to
it, so a later edit is caught (FP9).

- **The floor** is reported and recorded by V6; under Stage 9's routing it changes
  no decision (D19-1).
- **The menu** holds scorer-cutoff candidates over MiniCheck's joint score, each with
  its cutoff grid (D19-1).
- **The gates** must include every metric §Metrics gates, and may never include one
  it marks descriptive or not estimated (D1).
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, PositiveInt, model_validator

from earnings_themes import tomlfile
from earnings_themes.evaluation.bootstrap import BootstrapPlan
from earnings_themes.evaluation.records import Metric, checked, sealed
from earnings_themes.gold import CodebookRef
from earnings_themes.records import IdPart, Part, Pin, Sha256Hex, ThemesRecord, parse

Share = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]

REQUIRED_GATES = frozenset(
    {
        Metric.RELEASE_PRECISION,
        Metric.RELEASE_RECALL,
        Metric.THEME_F1_MICRO,
        Metric.THEME_F1_MACRO,
        Metric.SPAN_UNIT_F1,
        Metric.GOLD_EVIDENCE_RECALL,
        Metric.SUPPORT_PRECISION,
    }
)
"""The metrics §Metrics gates."""
NEVER_GATED = frozenset(
    {
        Metric.RARE_THEME_RECALL,
        Metric.SECTOR_PREVALENCE,
        Metric.SOURCE_SELECTION_BIAS,
    }
)
"""Descriptive only, or not estimated (D1)."""
HEADER = (
    "Stage 11's preregistration (FP9), committed before any pilot output exists."
    " Numbers, rules and hashes only. Its content_hash covers every other field."
)


class FloorRule(Part):
    """The judge agreement floor (FP9, R8.4)."""

    statistic: Literal["cohen_kappa"]
    reported: Literal["gwet_ac1"]
    population: Literal["family_verdict_vs_joint_label"]
    bound: Literal["event_bootstrap_lower"]
    floor: Annotated[float, Field(ge=0.3, le=0.6, allow_inf_nan=False)]
    consequence: Literal["reported_only"]


class Candidate(Part):
    """One menu candidate: accept an assessed target with an eligible quote when
    its MiniCheck joint score is at least the fitted cutoff (D19-1)."""

    candidate_id: IdPart
    rule: Literal["scorer_cutoff"]
    signal: Literal["minicheck_joint"]
    signals: PositiveInt
    grid: Annotated[tuple[Share, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def _sorted_grid(self) -> Self:
        if list(self.grid) != sorted(set(self.grid)):
            raise ValueError("the grid must be sorted and unique")
        return self


class SelectionRule(Part):
    """How a candidate is chosen (§Calibration)."""

    recall_floor: Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)]
    objective: Literal["max_train_precision"]
    tie_break: Literal["fewer_signals_then_lower_cutoff"]


class SamplingPlan(Part):
    """The label sample (FP8)."""

    seed: int
    pool: Literal["assessed_and_flagged"]
    train_size: PositiveInt
    train_cap: PositiveInt
    dev_size: PositiveInt
    dev_cap: PositiveInt
    minimum_usable: Annotated[int, Field(ge=50)]
    extension_step: PositiveInt


class GateRule(Part):
    """V6's rule (FP15)."""

    rule: Literal["dev-lower-bound/1"]
    gated: Annotated[tuple[Metric, ...], Field(min_length=1)]
    undefined_gate: Literal["not_gated", "point_estimate"]

    @model_validator(mode="after")
    def _the_spec_gates(self) -> Self:
        gated = set(self.gated)
        if len(gated) != len(self.gated):
            raise ValueError("a metric is gated once")
        if not REQUIRED_GATES <= gated or gated & NEVER_GATED:
            raise ValueError("the gates must be §Metrics' gated metrics")
        return self


class Preregistration(ThemesRecord):
    """``preregistration-v<N>.toml``."""

    preregistration_version: PositiveInt
    pin: Pin
    split_hash: Sha256Hex
    codebook: CodebookRef
    floor: FloorRule
    menu: Annotated[tuple[Candidate, ...], Field(min_length=1)]
    selection: SelectionRule
    sampling: SamplingPlan
    bootstrap: BootstrapPlan
    gates: GateRule
    content_hash: Sha256Hex

    @model_validator(mode="after")
    def _distinct_candidates(self) -> Self:
        ids = [candidate.candidate_id for candidate in self.menu]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate IDs must be unique")
        return self


def freeze_preregistration(fields: Mapping[str, object]) -> Preregistration:
    """``fields`` as a preregistration, with its ``content_hash``."""
    draft = parse({**fields, "content_hash": "0" * 64}, Preregistration, "draft")
    return sealed(draft)


def preregistration_toml(record: Preregistration) -> str:
    """The committed file (B2)."""
    return tomlfile.dumps(record.model_dump(mode="json"), header=HEADER)


def load_preregistration(path: Path) -> Preregistration:
    """The committed preregistration, refused unless it hashes to its
    ``content_hash``."""
    return checked(parse(tomlfile.read(path), Preregistration, path.name), path.name)
```

Append to the end of `docs/data-dictionary.md`, after one blank line:

```markdown
### `FloorRule`

| Field | Meaning |
| --- | --- |
| `statistic` | `cohen_kappa` |
| `reported` | `gwet_ac1`, beside it |
| `population` | `family_verdict_vs_joint_label` |
| `bound` | `event_bootstrap_lower` |
| `floor` | The user's number, from 0.3 to 0.6 (RC §7) |
| `consequence` | `reported_only` (D19-1) |

### `Candidate`

| Field | Meaning |
| --- | --- |
| `candidate_id` | The candidate |
| `rule` | `scorer_cutoff` |
| `signal` | `minicheck_joint` |
| `signals` | How many signals it reads, for the tie-break |
| `grid` | Its cutoffs, sorted |

### `SelectionRule`

| Field | Meaning |
| --- | --- |
| `recall_floor` | ρ: the label recall a cutoff must reach |
| `objective` | `max_train_precision` |
| `tie_break` | `fewer_signals_then_lower_cutoff` |

### `SamplingPlan`

| Field | Meaning |
| --- | --- |
| `seed` | The sampler's seed |
| `pool` | `assessed_and_flagged` |
| `train_size` | Train's sample size |
| `train_cap` | Train's per-event cap |
| `dev_size` | Dev's sample size |
| `dev_cap` | Dev's per-event cap |
| `minimum_usable` | Usable train joint labels calibration needs; at least 50 (R8.4) |
| `extension_step` | Targets each extension adds to train's size |

### `GateRule`

| Field | Meaning |
| --- | --- |
| `rule` | `dev-lower-bound/1` (FP15) |
| `gated` | The gated metrics: every one §Metrics gates, and none it marks descriptive or not estimated |
| `undefined_gate` | `not_gated` or `point_estimate`, for a dev interval that is undefined |

### `Preregistration`

| Field | Meaning |
| --- | --- |
| `schema_version` | `1` |
| `preregistration_version` | Its version |
| `pin` | The pilot pin (GS2) |
| `split_hash` | The split |
| `codebook` | The codebook |
| `floor` | The `FloorRule` |
| `menu` | Each `Candidate` |
| `selection` | The `SelectionRule` |
| `sampling` | The `SamplingPlan` |
| `bootstrap` | The `BootstrapPlan` |
| `gates` | The `GateRule` |
| `content_hash` | Digest of every other field |
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_preregistration.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `413 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_preregistration.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/preregistration.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_preregistration.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/preregistration.py docs/data-dictionary.md
git commit -m "feat(themes): the Stage 11 preregistration record (A5)"
```

---

### Task 14: `calibration` (A5; FP10, FP21, D19-1, D19-5, D19-14)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_calibration.py`
- Modify: `tests/contracts/test_data_dictionary.py` (imports; the evaluation registry)
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/calibration.py`
- Modify: `docs/data-dictionary.md` (the evaluation section: `ScorerCutoff`, `CutoffFigure`, `CandidateFit`, `FamilyAgreement`, `ScorerAuc`, `Selection`, `CalibrationArtifact`)

**Interfaces:**
- Consumes:
  - from Task 2: `problems.EvaluationError`, `problems.EvaluationProblem`, `tests/evaluation/cases.py: decision_view`
  - from Task 5: `agreement.cohen_kappa`, `agreement.gwet_ac1`, `bootstrap.Estimate`, `bootstrap.estimate`
  - from Task 6: `records.Real`, `records.content_hash`, `records.sealed`, `verdicts.consensus`, `verdicts.families`, `verdicts.family_verdict`
  - from Task 9: `labels.ClaimAnswer`, `labels.FitAnswer`, `labels.SupportLabel`, `labels.SupportLabelSet`, `labels.claim_label`, `labels.human_labels`, `labels.joint_label`
  - from Task 12: `earnings_themes.support.metrics.accepted_claim_recall`
  - from Task 13: `preregistration.Preregistration`, `preregistration.freeze_preregistration`, `tests/evaluation/test_preregistration.py: fields`
  - existing at `7948d94`: `earnings_core`: `digest`, `sha256_hex`; `earnings_themes.coding.decide`: `DecisionInput`, `decision_vote`; `earnings_themes.coding.records`: `PolicyVote`, `ProposalRunRecord`; `earnings_themes.extraction.records`: `Parameters`, `RunRecord`; `earnings_themes.records`: `IdPart`, `NonBlank`, `Part`, `Sha256Hex`, `ThemesRecord`; `earnings_themes.split`: `Partition`; `earnings_themes.support.metrics`: `Acceptance`, `ContinuousSignal`, `MetricReport`, `accepted_claim_precision`, `auc_roc`; `earnings_themes.support.records`: `SignalStatus`, `SupportPolicy`, `SupportRunRecord`
- Produces:
  - In `earnings_themes.evaluation.calibration`:
    - `joint_score(view: DecisionInput) -> float | None`
    - `class ScorerCutoff` (frozen dataclass): fields `cutoff: float`; methods `.vote(view: DecisionInput) -> PolicyVote`
    - `accepts(rule: ScorerCutoff, view: DecisionInput) -> bool`
    - `class CutoffFigure(Part)`: fields `cutoff: Real`, `precision: Real | None`, `recall: Real | None`, `accepted: NonNegativeInt`
    - `class CandidateFit(Part)`: fields `candidate_id: IdPart`, `signals: PositiveInt`, `cutoff: Real | None`, `precision: Real | None`, `recall: Real | None`, `grid: tuple[CutoffFigure, ...]`
    - `class FamilyAgreement(Part)`: fields `family: NonBlank`, `kappa: Estimate`, `ac1: Estimate`, `labels: NonNegativeInt`, `uncertain: NonNegativeInt`, `meets_floor: bool`
    - `class ScorerAuc(Part)`: fields `scorer: Literal['minicheck', 'deberta']`, `report: MetricReport`
    - `class Selection(Part)`: fields `candidate_id: IdPart`, `rule: Literal['scorer_cutoff']`, `signal: Literal['minicheck_joint']`, `cutoff: Real`
    - `class CalibrationArtifact(ThemesRecord)`: fields `calibration_version: PositiveInt`, `preregistration_hash: Sha256Hex`, `labels_hash: Sha256Hex`, `configuration_hash: Sha256Hex`, `train_labels: NonNegativeInt`, `usable_labels: NonNegativeInt`, `families: tuple[FamilyAgreement, ...]`, `candidates: tuple[CandidateFit, ...]`, `outcome: Literal['selected', 'no_candidate']`, `selection: Selection | None`, `scorers: tuple[ScorerAuc, ...]`, `content_hash: Sha256Hex`
    - `frozen_configuration(extraction: RunRecord, proposals: ProposalRunRecord, support: SupportRunRecord, support_policy: SupportPolicy) -> dict[str, object]`
    - `calibrate(preregistration: Preregistration, labels: SupportLabelSet, *, labels_hash: str, views: Mapping[str, DecisionInput], alternative: Mapping[str, float | None], events: Mapping[str, str], configuration: Mapping[str, object], version: int=1) -> CalibrationArtifact`

`calibrate` refuses:
- a preregistration or label set that is not the frozen one;
- an unknown or changed target;
- fewer usable joint labels than preregistered (R8.4).

It then:
- reports each family's κ and AC1 against the joint label: the floor (D19-1);
- fits each candidate's cutoff on train, by Stage 9's own vote (D19-5), and selects one;
- reports both scorers' AUC against the claim label (FP21);
- seals the artifact with the frozen configuration's hash (D19-14).

The 60-target known answer is hand-computed in `population()`'s docstring.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_calibration.py`:

```python
"""Calibration over invented decision views, with hand-computed known answers (the
Stage 11 spec, A5 and §Calibration; R8.4, R8.6; D19-1, D19-5)."""

from datetime import date
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_themes.evaluation.calibration import (
    ScorerCutoff,
    accepts,
    calibrate,
    frozen_configuration,
    joint_score,
)
from earnings_themes.evaluation.labels import (
    ClaimAnswer,
    FitAnswer,
    SupportLabel,
    SupportLabelSet,
)
from earnings_themes.evaluation.preregistration import freeze_preregistration
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.extraction.records import Parameters
from earnings_themes.split import Partition
from earnings_themes.support.records import SupportPolicy

from .cases import decision_view
from .test_preregistration import fields

REPO = Path(__file__).resolve().parents[4]
YES, NO = ("supported", "fits"), ("unsupported", "fits")
PREREG = freeze_preregistration(fields())


def population():
    """60 targets in 12 events, 5 each. Assessed: 20 at 0.95 labelled 1, 10 at 0.6
    labelled 1, 10 at 0.6 labelled 0. Flagged (f1 opposes): 10 at 0.3 labelled 1,
    10 at 0.3 labelled 0."""
    rows = (
        [(0.95, YES, 1)] * 20
        + [(0.6, YES, 1)] * 10
        + [(0.6, YES, 0)] * 10
        + [(0.3, NO, 1)] * 10
        + [(0.3, NO, 0)] * 10
    )
    views, labels, events = {}, [], {}
    for n, (score, second, value) in enumerate(rows):
        target_id = f"t{n:02}"
        view = decision_view(target_id, score, YES, second)
        views[target_id] = view
        events[target_id] = f"e{n // 5:02}"
        labels.append(
            SupportLabel(
                target_id=target_id,
                target_input_hash=view.target.input_hash,
                partition=Partition.TRAIN,
                claim_support=ClaimAnswer.SUPPORTED
                if value
                else ClaimAnswer.UNSUPPORTED,
                theme_fit=FitAnswer.FITS,
                labelled_on=date(2026, 10, 20),
            )
        )
    label_set = SupportLabelSet(
        preregistration_hash=PREREG.content_hash, labels=tuple(labels)
    )
    alternative = {t: 1 - joint_score(v) for t, v in views.items()}
    return views, label_set, events, alternative


def run(preregistration=PREREG, labels=None):
    views, label_set, events, alternative = population()
    return calibrate(
        preregistration,
        labels or label_set,
        labels_hash="c" * 64,
        views=views,
        alternative=alternative,
        events=events,
        configuration={"invented": "configuration"},
    )


def test_assessed_and_flagged_views_are_genuine() -> None:
    views, *_ = population()
    assert views["t00"].outcome.status == "assessed"
    assert views["t45"].outcome.status == "flagged"
    assert views["t00"].eligible_quote_ids == ("q1",)
    assert accepts(ScorerCutoff(0.9), views["t00"])
    assert not accepts(ScorerCutoff(0.9), views["t25"])
    assert not accepts(ScorerCutoff(0.0), views["t45"])


def test_the_fit_and_selection_known_answer() -> None:
    artifact = run()
    fit = artifact.candidates[0]
    assert [(g.cutoff, g.precision, g.recall, g.accepted) for g in fit.grid] == [
        (0.0, 0.75, 0.75, 40),
        (0.5, 0.75, 0.75, 40),
        (0.9, 1.0, 0.5, 20),
    ]
    assert (fit.cutoff, fit.precision, fit.recall) == (0.9, 1.0, 0.5)
    assert artifact.outcome == "selected"
    assert artifact.selection.cutoff == 0.9
    assert (artifact.train_labels, artifact.usable_labels) == (60, 60)


def test_a_precision_tie_goes_to_the_lower_cutoff() -> None:
    data = fields()
    tighter = freeze_preregistration(
        {**data, "selection": {**data["selection"], "recall_floor": 0.6}}
    )
    _, label_set, _, _ = population()
    labels = label_set.model_copy(update={"preregistration_hash": tighter.content_hash})
    artifact = run(tighter, labels)
    assert artifact.selection.cutoff == 0.0


def test_no_cutoff_meeting_rho_is_no_candidate() -> None:
    data = fields()
    strict = freeze_preregistration(
        {**data, "selection": {**data["selection"], "recall_floor": 0.8}}
    )
    _, label_set, _, _ = population()
    labels = label_set.model_copy(update={"preregistration_hash": strict.content_hash})
    artifact = run(strict, labels)
    assert artifact.outcome == "no_candidate" and artifact.selection is None
    assert artifact.candidates[0].cutoff is None


def test_the_floor_test_is_reported_by_family() -> None:
    artifact = run()
    by_family = {f.family: f for f in artifact.families}
    assert by_family["f0"].kappa.point == pytest.approx(0.0)
    assert by_family["f1"].kappa.point == pytest.approx(0.25)
    assert by_family["f1"].uncertain == 0
    assert not by_family["f0"].meets_floor
    assert by_family["f1"].kappa.interval.resamples == PREREG.bootstrap.resamples


def test_auc_for_both_scorers_against_the_claim_label() -> None:
    by_scorer = {s.scorer: s.report for s in run().scorers}
    assert by_scorer["minicheck"].value == pytest.approx(0.75)
    assert by_scorer["deberta"].value == pytest.approx(0.25)
    assert by_scorer["minicheck"].task == "claim_support"


def test_the_artifact_is_deterministic_and_hashed() -> None:
    assert run() == run()
    assert run().content_hash != "0" * 64


def test_too_few_usable_labels_are_refused() -> None:
    _, label_set, _, _ = population()
    fewer = label_set.model_copy(update={"labels": label_set.labels[:49]})
    with pytest.raises(EvaluationError, match="too_few_labels"):
        run(labels=fewer)


def test_labels_must_bind_the_preregistration() -> None:
    _, label_set, _, _ = population()
    other = label_set.model_copy(update={"preregistration_hash": "d" * 64})
    with pytest.raises(EvaluationError, match="preregistration_mismatch"):
        run(labels=other)


def test_a_changed_target_input_is_refused() -> None:
    _, label_set, _, _ = population()
    first = label_set.labels[0].model_copy(update={"target_input_hash": "e" * 64})
    changed = label_set.model_copy(update={"labels": (first, *label_set.labels[1:])})
    with pytest.raises(EvaluationError, match="target_hash_mismatch"):
        run(labels=changed)


def test_an_edited_preregistration_is_refused() -> None:
    edited = PREREG.model_copy(update={"preregistration_version": 2})
    with pytest.raises(EvaluationError, match="preregistration_mismatch"):
        run(edited)


def keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in keys(v)}
    return set()


def test_the_frozen_configuration_binds_no_run(assessed_case) -> None:
    prompt = (REPO / "prompts" / "support" / "judge-1.md").read_text(encoding="utf-8")
    policy = SupportPolicy(
        support_version="semantic-support/1",
        prompt_text=prompt,
        prompt_hash=sha256_hex(prompt.encode("utf-8")),
        parameters=Parameters(max_tokens=64),
    )
    case = assessed_case
    records = (
        case.sources.stored_run.record,
        case.proposals.record,
        case.support.record,
    )
    frozen = frozen_configuration(*records, policy)
    assert set(frozen) == {"extraction", "coding", "support"}
    assert not keys(frozen) & {
        "run_id",
        "source_run_id",
        "documents",
        "cache_mode",
        "stability_run_id",
        "requested_claim_order",
        "started_at",
    }
    other = policy.model_copy(update={"parameters": Parameters(max_tokens=65)})
    with pytest.raises(EvaluationError, match="malformed_record"):
        frozen_configuration(*records, other)
```

In `tests/contracts/test_data_dictionary.py`, add `calibration,` to the `from earnings_themes.evaluation import (...)` block, in alphabetical order.

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_MODELS`:

```python
    calibration.CutoffFigure,
    calibration.CandidateFit,
    calibration.FamilyAgreement,
    calibration.ScorerAuc,
    calibration.Selection,
    calibration.CalibrationArtifact,
```

In `tests/contracts/test_data_dictionary.py`, append to `EVALUATION_DATACLASSES`:

```python
    calibration.ScorerCutoff,
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_calibration.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`2 errors`), with `ImportError: cannot import name 'calibration' from 'earnings_themes.evaluation'`; `ModuleNotFoundError: No module named 'earnings_themes.evaluation.calibration'`.

- [x] **Step 3: Write the implementation**
> Deviation (Task 14 fix round, user decision 2026-10-12): `support_configuration(...)` is defined once in `support/records.py` and called by `support/run.py` and `calibration.frozen_configuration` (D18-1); `configuration_hash(configuration, selection)` is public in `calibration.py`; refusal subjects are `content_hash` and `labels`; dictionary rows say 'against the joint label'; test gaps closed. Final review: `_family` calls `agreement.judge_agreement`; the dictionary gains a `Calibrated policy` paragraph.

Create `packages/earnings-themes/src/earnings_themes/evaluation/calibration.py`:

```python
"""Calibration (the Stage 11 spec, A5 and §Calibration; FP9, FP10, FP21; R8.4,
R8.6).

- **The labels** are train's, and at least the preregistered number must have a
  joint label (R8.4).
- **The floor test.** Each judge family's binary verdict against the joint label:
  Cohen's κ with its event-clustered bootstrap lower bound against the preregistered
  floor, and Gwet's AC1 beside it. It is reported and changes no decision (D19-1).
- **Fitting.** Each candidate's cutoff is the grid value with the highest train
  labelled precision whose label recall is at least ρ; a tie goes to the lower
  cutoff. A target counts as accepted exactly when Stage 9's ``decision_vote``
  accepts it under that cutoff, so a flagged, incomplete or refused target never
  is, and calibration decides as ``decide_assignments`` will (D19-5).
- **Selection.** The fitted candidate with the highest precision; a tie goes to the
  one reading fewer signals, then the lower cutoff. When none meets ρ, the outcome is
  ``no_candidate``: a feasibility finding, not an error.
- **AUC** for MiniCheck and DeBERTa against the claim label (R8.6, FP21).
- **The frozen configuration** binds the models, prompts, policies and ceilings,
  never a run's IDs, documents, claim order, cache mode or stability run, so a dev
  run reproduces it.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Self

from earnings_core import digest
from pydantic import NonNegativeInt, PositiveInt, model_validator

from earnings_themes.coding.decide import DecisionInput, decision_vote
from earnings_themes.coding.records import PolicyVote, ProposalRunRecord
from earnings_themes.evaluation.agreement import cohen_kappa, gwet_ac1
from earnings_themes.evaluation.bootstrap import Estimate, estimate
from earnings_themes.evaluation.labels import (
    SupportLabelSet,
    claim_label,
    human_labels,
    joint_label,
)
from earnings_themes.evaluation.preregistration import Preregistration
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import Real, content_hash, sealed
from earnings_themes.evaluation.verdicts import consensus, families, family_verdict
from earnings_themes.extraction.records import RunRecord
from earnings_themes.records import IdPart, NonBlank, Part, Sha256Hex, ThemesRecord
from earnings_themes.split import Partition
from earnings_themes.support.metrics import (
    Acceptance,
    ContinuousSignal,
    MetricReport,
    accepted_claim_precision,
    accepted_claim_recall,
    auc_roc,
)
from earnings_themes.support.records import (
    SignalStatus,
    SupportPolicy,
    SupportRunRecord,
)


def joint_score(view: DecisionInput) -> float | None:
    """The target's available joint entailment score, or ``None``."""
    return next(
        (
            signal.score
            for signal in view.entailment
            if signal.scope == "joint" and signal.status is SignalStatus.AVAILABLE
        ),
        None,
    )


@dataclass(frozen=True)
class ScorerCutoff:
    """The scorer-cutoff rule (D19-1): accept with the eligible quotes when the
    joint score is at least ``cutoff``; otherwise review."""

    cutoff: float

    def vote(self, view: DecisionInput) -> PolicyVote:
        score = joint_score(view)
        if score is not None and score >= self.cutoff and view.eligible_quote_ids:
            return PolicyVote(
                action="accept", supporting_quote_ids=view.eligible_quote_ids
            )
        return PolicyVote(action="review")


@dataclass(frozen=True)
class _Trial:
    """A rule in the shape ``decision_vote`` calls; it reads no reference."""

    rule: ScorerCutoff

    def evaluate(self, view: DecisionInput) -> PolicyVote:
        return self.rule.vote(view)


def accepts(rule: ScorerCutoff, view: DecisionInput) -> bool:
    """Whether Stage 9 accepts ``view`` under ``rule``."""
    return decision_vote(view, _Trial(rule))[0] == "accepted"


class CutoffFigure(Part):
    """One grid cutoff's train figures."""

    cutoff: Real
    precision: Real | None
    recall: Real | None
    accepted: NonNegativeInt


class CandidateFit(Part):
    """One candidate's fitted cutoff, or ``None`` when no cutoff meets ρ."""

    candidate_id: IdPart
    signals: PositiveInt
    cutoff: Real | None
    precision: Real | None
    recall: Real | None
    grid: tuple[CutoffFigure, ...]


class FamilyAgreement(Part):
    """One judge family against the joint label (R8.4): reported, never gating a
    decision (D19-1)."""

    family: NonBlank
    kappa: Estimate
    ac1: Estimate
    labels: NonNegativeInt
    uncertain: NonNegativeInt
    meets_floor: bool


class ScorerAuc(Part):
    """One scorer's AUC-ROC against the claim label (R8.6)."""

    scorer: Literal["minicheck", "deberta"]
    report: MetricReport


class Selection(Part):
    """The selected candidate and its cutoff."""

    candidate_id: IdPart
    rule: Literal["scorer_cutoff"]
    signal: Literal["minicheck_joint"]
    cutoff: Real


class CalibrationArtifact(ThemesRecord):
    """``calibration-v<N>.json``: no text (§Calibration)."""

    calibration_version: PositiveInt
    preregistration_hash: Sha256Hex
    labels_hash: Sha256Hex
    configuration_hash: Sha256Hex
    train_labels: NonNegativeInt
    usable_labels: NonNegativeInt
    families: tuple[FamilyAgreement, ...]
    candidates: tuple[CandidateFit, ...]
    outcome: Literal["selected", "no_candidate"]
    selection: Selection | None
    scorers: tuple[ScorerAuc, ...]
    content_hash: Sha256Hex

    @model_validator(mode="after")
    def _selected_exactly_when_chosen(self) -> Self:
        if (self.outcome == "selected") != (self.selection is not None):
            raise ValueError("a selection exactly when the outcome is selected")
        return self


def frozen_configuration(
    extraction: RunRecord,
    proposals: ProposalRunRecord,
    support: SupportRunRecord,
    support_policy: SupportPolicy,
) -> dict[str, object]:
    """The models, prompts, policies and ceilings a calibrated policy is frozen
    with; ``support_policy`` must be the one ``support`` ran under."""
    bound = {
        "policy": support_policy.model_dump(mode="json"),
        "ceilings": support.ceilings.model_dump(mode="json"),
        "scorer": support.scorer_identity.model_dump(mode="json"),
        "judges": [j.model_dump(mode="json") for j in support.judge_identities],
        "extractor_family": support.extractor_family,
    }
    if (
        digest({**bound, "cache_mode": support.cache_mode})
        != support.configuration_hash
    ):
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "support_policy")
    return {
        "extraction": extraction.configuration.model_dump(mode="json"),
        "coding": {
            "codebook": proposals.codebook.model_dump(mode="json"),
            "classifier_identity": proposals.classifier_identity.model_dump(
                mode="json"
            ),
            "coding_policy": proposals.coding_policy.model_dump(mode="json"),
            "ceilings": proposals.ceilings.model_dump(mode="json"),
            "schema_hash": proposals.schema_hash,
            "coding_version": proposals.coding_version,
            "validator_version": proposals.validator_version,
        },
        "support": {
            **bound,
            "codebook": support.codebook.model_dump(mode="json"),
            "support_version": support.support_version,
            "validator_version": support.validator_version,
        },
    }


def _family(
    preregistration: Preregistration,
    family: str,
    joint: Mapping[str, int],
    views: Mapping[str, DecisionInput],
    events: Mapping[str, str],
) -> FamilyAgreement:
    per_event: dict[str, list[tuple[int, int]]] = {}
    for target_id, label in joint.items():
        verdict = family_verdict(views[target_id].trials, family)
        per_event.setdefault(events[target_id], []).append((verdict, label))
    plan = preregistration.bootstrap
    kappa = estimate(
        per_event, lambda drawn: cohen_kappa([p for e in drawn for p in e]), plan
    )
    ac1 = estimate(
        per_event, lambda drawn: gwet_ac1([p for e in drawn for p in e]), plan
    )
    lower = kappa.interval.lower
    return FamilyAgreement(
        family=family,
        kappa=kappa,
        ac1=ac1,
        labels=len(joint),
        uncertain=sum(consensus(views[t].trials, family) == "uncertain" for t in joint),
        meets_floor=lower is not None and lower >= preregistration.floor.floor,
    )


def calibrate(
    preregistration: Preregistration,
    labels: SupportLabelSet,
    *,
    labels_hash: str,
    views: Mapping[str, DecisionInput],
    alternative: Mapping[str, float | None],
    events: Mapping[str, str],
    configuration: Mapping[str, object],
    version: int = 1,
) -> CalibrationArtifact:
    """Calibrate on train's labels: the floor test, the fit, the selection and AUC.
    ``views`` are the MiniCheck support run's ``decision_inputs``; ``alternative``
    is DeBERTa's joint score by target; ``events`` maps each target to its event;
    ``configuration`` is ``frozen_configuration``'s."""
    if content_hash(preregistration) != preregistration.content_hash:
        raise EvaluationError(EvaluationProblem.PREREGISTRATION_MISMATCH, "content")
    if labels.preregistration_hash != preregistration.content_hash:
        raise EvaluationError(EvaluationProblem.PREREGISTRATION_MISMATCH, "labels")
    train = labels.of(Partition.TRAIN)
    for label in train:
        view = views.get(label.target_id)
        if view is None:
            raise EvaluationError(EvaluationProblem.UNKNOWN_TARGET, label.target_id)
        if view.target.input_hash != label.target_input_hash:
            raise EvaluationError(
                EvaluationProblem.TARGET_HASH_MISMATCH, label.target_id
            )
        if label.target_id not in events:
            raise EvaluationError(EvaluationProblem.UNKNOWN_EVENT, label.target_id)
    joint = {
        label.target_id: value
        for label in train
        if (value := joint_label(label)) is not None
    }
    if len(joint) < preregistration.sampling.minimum_usable:
        raise EvaluationError(EvaluationProblem.TOO_FEW_LABELS, str(len(joint)))
    agreement = tuple(
        _family(preregistration, family, joint, views, events)
        for family in families(t for i in joint for t in views[i].trials)
    )
    population = sorted(joint)
    human = human_labels(
        [label for label in train if label.target_id in joint], "joint_support"
    )
    rho = preregistration.selection.recall_floor
    fits = []
    for candidate in preregistration.menu:
        grid = []
        for cutoff in candidate.grid:
            decisions = [
                Acceptance(
                    target_id=t,
                    task="joint_support",
                    accepted=accepts(ScorerCutoff(cutoff), views[t]),
                )
                for t in population
            ]
            p = accepted_claim_precision(
                population, human, decisions, task="joint_support"
            )
            r = accepted_claim_recall(
                population, human, decisions, task="joint_support"
            )
            grid.append(
                CutoffFigure(
                    cutoff=cutoff,
                    precision=p.value,
                    recall=r.value,
                    accepted=p.accepted_count,
                )
            )
        meeting = [
            g
            for g in grid
            if g.precision is not None and g.recall is not None and g.recall >= rho
        ]
        best = min(meeting, key=lambda g: (-g.precision, g.cutoff), default=None)
        fits.append(
            CandidateFit(
                candidate_id=candidate.candidate_id,
                signals=candidate.signals,
                cutoff=None if best is None else best.cutoff,
                precision=None if best is None else best.precision,
                recall=None if best is None else best.recall,
                grid=tuple(grid),
            )
        )
    chosen = min(
        (f for f in fits if f.cutoff is not None),
        key=lambda f: (-f.precision, f.signals, f.cutoff, f.candidate_id),
        default=None,
    )
    selection = (
        None
        if chosen is None
        else Selection(
            candidate_id=chosen.candidate_id,
            rule="scorer_cutoff",
            signal="minicheck_joint",
            cutoff=chosen.cutoff,
        )
    )
    claimed = [label for label in train if claim_label(label) is not None]
    ids = sorted(label.target_id for label in train)
    claims = human_labels(claimed, "claim_support")
    scorers = tuple(
        ScorerAuc(
            scorer=scorer,
            report=auc_roc(
                ids,
                claims,
                [
                    ContinuousSignal(
                        target_id=t, task="claim_support", view=view, score=score(t)
                    )
                    for t in ids
                ],
                task="claim_support",
                view=view,
            ),
        )
        for scorer, view, score in (
            ("minicheck", "minicheck_joint", lambda t: joint_score(views[t])),
            ("deberta", "deberta_joint", lambda t: alternative.get(t)),
        )
    )
    return sealed(
        CalibrationArtifact(
            calibration_version=version,
            preregistration_hash=preregistration.content_hash,
            labels_hash=labels_hash,
            configuration_hash=digest(
                {
                    "configuration": dict(configuration),
                    "selection": None
                    if selection is None
                    else selection.model_dump(mode="json"),
                }
            ),
            train_labels=len(train),
            usable_labels=len(joint),
            families=agreement,
            candidates=tuple(fits),
            outcome="no_candidate" if selection is None else "selected",
            selection=selection,
            scorers=scorers,
            content_hash="0" * 64,
        )
    )
```

Append to the end of `docs/data-dictionary.md`, after one blank line:

```markdown
### `ScorerCutoff`

| Field | Meaning |
| --- | --- |
| `cutoff` | Accept an assessed target with an eligible quote when its joint score reaches this |

### `CutoffFigure`

| Field | Meaning |
| --- | --- |
| `cutoff` | A grid cutoff |
| `precision` | Train labelled precision at it, or null |
| `recall` | Train label recall at it, or null |
| `accepted` | Targets accepted at it |

### `CandidateFit`

| Field | Meaning |
| --- | --- |
| `candidate_id` | The candidate |
| `signals` | Signals it reads |
| `cutoff` | The fitted cutoff, or null when none meets ρ |
| `precision` | Precision there |
| `recall` | Recall there |
| `grid` | Each `CutoffFigure` |

### `FamilyAgreement`

| Field | Meaning |
| --- | --- |
| `family` | The judge family |
| `kappa` | Cohen's κ `Estimate` |
| `ac1` | Gwet's AC1 `Estimate` |
| `labels` | Usable joint labels |
| `uncertain` | Targets whose family consensus is uncertain |
| `meets_floor` | Whether κ's lower bound reaches the floor; reported only (D19-1) |

### `ScorerAuc`

| Field | Meaning |
| --- | --- |
| `scorer` | `minicheck` or `deberta` |
| `report` | Its `MetricReport` against the claim label |

### `Selection`

| Field | Meaning |
| --- | --- |
| `candidate_id` | The selected candidate |
| `rule` | `scorer_cutoff` |
| `signal` | `minicheck_joint` |
| `cutoff` | Its fitted cutoff |

### `CalibrationArtifact`

| Field | Meaning |
| --- | --- |
| `schema_version` | `1` |
| `calibration_version` | Its version |
| `preregistration_hash` | The preregistration |
| `labels_hash` | SHA-256 of the committed label file |
| `configuration_hash` | Digest of the frozen configuration and the selection |
| `train_labels` | Train labels |
| `usable_labels` | Of them, with a joint label |
| `families` | Each `FamilyAgreement` |
| `candidates` | Each `CandidateFit` |
| `outcome` | `selected` or `no_candidate` |
| `selection` | The `Selection`, or null |
| `scorers` | Each `ScorerAuc` |
| `content_hash` | Digest of every other field |
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_calibration.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `425 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_calibration.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/calibration.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_calibration.py tests/contracts/test_data_dictionary.py packages/earnings-themes/src/earnings_themes/evaluation/calibration.py docs/data-dictionary.md
git commit -m "feat(themes): calibrate the scorer-cutoff menu on train labels (A5)"
```

---

### Task 15: `CalibratedPolicy` and the package's exports (A5)

**Files:**
- Create: `packages/earnings-themes/tests/evaluation/test_policy.py`
- Create: `packages/earnings-themes/src/earnings_themes/evaluation/policy.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/__init__.py`

**Interfaces:**
- Consumes:
  - from Task 2: `problems.EvaluationError`, `problems.EvaluationProblem`
  - from Task 6: `records.content_hash`, `records.sealed`
  - from Task 12: `earnings_themes.coding.decide.decision_inputs`
  - from Task 14: `calibration.CalibrationArtifact`, `calibration.ScorerCutoff`, `calibration.accepts`, `tests/evaluation/test_calibration.py: run`
  - existing at `7948d94`: `earnings_core`: `digest`; `earnings_themes.coding.decide`: `DecisionInput`; `earnings_themes.coding.records`: `PolicyReference`, `PolicyVote`; `earnings_themes.support.records`: `CodebookReference`
- Produces:
  - In `earnings_themes.evaluation.policy`:
    - `class CalibratedPolicy`: methods `.__init__(artifact: CalibrationArtifact, *, codebook: CodebookReference, classifier_configuration_hash: str, support_configuration_hash: str) -> None`, `.reference() -> PolicyReference`, `.evaluate(view: DecisionInput) -> PolicyVote`
  - `earnings_themes.evaluation` re-exports its public API: `Accepted`, `BootstrapPlan`, `CalibratedPolicy`, `CalibrationArtifact`, `Estimate`, `EvaluationError`, `EvaluationProblem`, `EventCells`, `EventObservation`, `GateVerdict`, `Gates`, `Interval`, `LabelledTarget`, `Metric`, `PartitionReport`, `PilotReport`, `PoolTarget`, `Preregistration`, `SupportLabel`, `SupportLabelSet`, `UnitIndex`, `calibrate`, `check_labels`, `compare_readings`, `derive_gates`, `estimate`, `evaluate_gates`, `event_cells`, `freeze_preregistration`, `frozen_configuration`, `gates_toml`, `label_pool`, `label_views`, `labels_toml`, `level_one`, `load_gates`, `load_labels`, `load_preregistration`, `merge_labels`, `partition_report`, `preregistration_toml`, `sample_targets`, `stability_figures`, `unit_index`, `units_over`.

`CalibratedPolicy` binds a selected artifact as Stage 9's `AssignmentPolicy`, with `PolicyReference(kind="calibrated", calibration_reference=<the artifact's hash>)`. It refuses a `no_candidate` artifact, or one whose content changed. A parity test shows that it decides as calibration simulated, and that a flagged target stays in review. The package's `__init__` gains its public exports.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/evaluation/test_policy.py`:

```python
"""The calibrated policy decides exactly as calibration simulated (the Stage 11
spec, A5; Stage 9's ``AssignmentPolicy``; D19-5)."""

from importlib import import_module

import pytest
from earnings_themes.coding.decide import decision_inputs
from earnings_themes.evaluation.calibration import ScorerCutoff, accepts
from earnings_themes.evaluation.policy import CalibratedPolicy
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.evaluation.records import sealed

from .test_calibration import run

_cases = import_module("packages.earnings-themes.tests.coding.cases")


def artifact_with(cutoff: float):
    base = run()
    selection = base.selection.model_copy(update={"cutoff": cutoff})
    return sealed(base.model_copy(update={"selection": selection}))


def bind(case, artifact) -> CalibratedPolicy:
    return CalibratedPolicy(
        artifact,
        codebook=case.support.record.codebook,
        classifier_configuration_hash=case.proposals.record.configuration_hash,
        support_configuration_hash=case.support.record.configuration_hash,
    )


@pytest.mark.parametrize(("cutoff", "status"), [(0.2, "accepted"), (0.3, "review")])
def test_decisions_match_the_simulated_calibration(
    assessed_case, cutoff, status
) -> None:
    case = assessed_case
    policy = bind(case, artifact_with(cutoff))
    decision = case.decide(policy).decisions[0]
    assert decision.status == status
    view = next(iter(decision_inputs(case.support, case.sources).values()))
    assert accepts(ScorerCutoff(cutoff), view) == (status == "accepted")
    assert decision.policy == policy.reference
    assert policy.reference.kind == "calibrated"
    assert policy.reference.calibration_reference == artifact_with(cutoff).content_hash


def test_a_flagged_target_stays_in_review(assessed_case, tmp_path) -> None:
    case = _cases.make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "flagged",
        parts=_cases.make_support_parts("uncertain", score=0.99),
    )
    decision = case.decide(bind(case, artifact_with(0.0))).decisions[0]
    assert (decision.status, decision.reason) == ("review", "assessment_flagged")


def test_no_candidate_or_a_changed_artifact_binds_no_policy(assessed_case) -> None:
    base = run()
    none = sealed(
        base.model_copy(update={"outcome": "no_candidate", "selection": None})
    )
    with pytest.raises(EvaluationError, match="no_candidate"):
        bind(assessed_case, none)
    changed = base.model_copy(update={"usable_labels": 59})
    with pytest.raises(EvaluationError, match="content_hash_mismatch"):
        bind(assessed_case, changed)
```

- [x] **Step 2: Run them to see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_policy.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL (`1 error`), with `ModuleNotFoundError: No module named 'earnings_themes.evaluation.policy'`.

- [x] **Step 3: Write the implementation**
> Deviation (Task 15 fix round, user decision 2026-10-12): `CalibratedPolicy`'s refusals name `content_hash` (mismatch) and `selection` (no candidate). Final review: `EvidenceCell` is exported, so `__all__` holds 46 names, not the plan's 45.

Create `packages/earnings-themes/src/earnings_themes/evaluation/policy.py`:

```python
"""The calibrated assignment policy (the Stage 11 spec, A5; Stage 9's
``AssignmentPolicy``).

It applies the calibration artifact's selected rule. Stage 9 binds a policy
reference to one coding run's and one support run's configuration hashes
(``_policy_reference``), and the Stage 10 workflow fixes that reference before its
runs exist, so the caller supplies both hashes and the codebook (plan 19's handoff
to A8). An artifact with no selection binds no policy: every target stays in review
(``no_candidate``).
"""

from earnings_core import digest

from earnings_themes.coding.decide import DecisionInput
from earnings_themes.coding.records import PolicyReference, PolicyVote
from earnings_themes.evaluation.calibration import CalibrationArtifact, ScorerCutoff
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import content_hash
from earnings_themes.support.records import CodebookReference


class CalibratedPolicy:
    """``AssignmentPolicy`` from a calibration artifact."""

    def __init__(
        self,
        artifact: CalibrationArtifact,
        *,
        codebook: CodebookReference,
        classifier_configuration_hash: str,
        support_configuration_hash: str,
    ) -> None:
        if content_hash(artifact) != artifact.content_hash:
            raise EvaluationError(
                EvaluationProblem.CONTENT_HASH_MISMATCH, "calibration"
            )
        selection = artifact.selection
        if selection is None:
            raise EvaluationError(EvaluationProblem.NO_CANDIDATE, "calibration")
        self._rule = ScorerCutoff(selection.cutoff)
        self._reference = PolicyReference(
            policy_id=f"calibrated-{selection.candidate_id}",
            policy_hash=digest(selection.model_dump(mode="json")),
            kind="calibrated",
            codebook=codebook,
            classifier_configuration_hash=classifier_configuration_hash,
            support_configuration_hash=support_configuration_hash,
            calibration_reference=artifact.content_hash,
        )

    @property
    def reference(self) -> PolicyReference:
        return self._reference

    def evaluate(self, view: DecisionInput) -> PolicyVote:
        return self._rule.vote(view)
```

Replace the whole file: its docstring stays, and the exports follow it.

In `packages/earnings-themes/src/earnings_themes/evaluation/__init__.py`, replace:

```python
"""Stage 11's evaluation: scoring the pilot, the user's support labels, and
calibration (the Stage 11 spec, A3–A5).

Pure: it reads no file, sends no request, loads no model and prints nothing. It
imports pure Stage 7–9 code and never ingestion, httpx, an NLI runtime or a concrete
adapter, and no gold-drafting module imports it (D19-4).
"""
```

with:

```python
"""Stage 11's evaluation: scoring the pilot, the user's support labels, and
calibration (the Stage 11 spec, A3–A5).

Pure: it reads no file, sends no request, loads no model and prints nothing. It
imports pure Stage 7–9 code and never ingestion, httpx, an NLI runtime or a concrete
adapter, and no gold-drafting module imports it (D19-4).
"""

from earnings_themes.evaluation.align import UnitIndex, unit_index, units_over
from earnings_themes.evaluation.bootstrap import (
    BootstrapPlan,
    Estimate,
    Interval,
    estimate,
)
from earnings_themes.evaluation.calibration import (
    CalibrationArtifact,
    calibrate,
    frozen_configuration,
)
from earnings_themes.evaluation.cells import EventCells, event_cells, level_one
from earnings_themes.evaluation.gates import (
    derive_gates,
    evaluate_gates,
    gates_toml,
    load_gates,
)
from earnings_themes.evaluation.label_view import label_views
from earnings_themes.evaluation.labels import (
    SupportLabel,
    SupportLabelSet,
    check_labels,
    labels_toml,
    load_labels,
    merge_labels,
)
from earnings_themes.evaluation.policy import CalibratedPolicy
from earnings_themes.evaluation.preregistration import (
    Preregistration,
    freeze_preregistration,
    load_preregistration,
    preregistration_toml,
)
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import (
    Gates,
    GateVerdict,
    Metric,
    PartitionReport,
    PilotReport,
)
from earnings_themes.evaluation.report import (
    Accepted,
    EventObservation,
    LabelledTarget,
    compare_readings,
    partition_report,
    stability_figures,
)
from earnings_themes.evaluation.sampling import PoolTarget, label_pool, sample_targets

__all__ = [
    "Accepted",
    "BootstrapPlan",
    "CalibratedPolicy",
    "CalibrationArtifact",
    "Estimate",
    "EvaluationError",
    "EvaluationProblem",
    "EventCells",
    "EventObservation",
    "GateVerdict",
    "Gates",
    "Interval",
    "LabelledTarget",
    "Metric",
    "PartitionReport",
    "PilotReport",
    "PoolTarget",
    "Preregistration",
    "SupportLabel",
    "SupportLabelSet",
    "UnitIndex",
    "calibrate",
    "check_labels",
    "compare_readings",
    "derive_gates",
    "estimate",
    "evaluate_gates",
    "event_cells",
    "freeze_preregistration",
    "frozen_configuration",
    "gates_toml",
    "label_pool",
    "label_views",
    "labels_toml",
    "level_one",
    "load_gates",
    "load_labels",
    "load_preregistration",
    "merge_labels",
    "partition_report",
    "preregistration_toml",
    "sample_targets",
    "stability_figures",
    "unit_index",
    "units_over",
]
```

- [x] **Step 4: Run the tests to see them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation/test_policy.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py -q`

Expected: PASS, `417 passed`.

- [x] **Step 5: Format, lint and commit**

```bash
uv run --locked ruff format packages/earnings-themes/tests/evaluation/test_policy.py packages/earnings-themes/src/earnings_themes/evaluation/policy.py packages/earnings-themes/src/earnings_themes/evaluation/__init__.py
uv run --locked ruff check .
uv run --locked ruff format --check .
git log -3 --oneline
git add packages/earnings-themes/tests/evaluation/test_policy.py packages/earnings-themes/src/earnings_themes/evaluation/policy.py packages/earnings-themes/src/earnings_themes/evaluation/__init__.py
git commit -m "feat(themes): the calibrated assignment policy and evaluation exports (A5)"
```

---

### Task 16: Scoped checks, the user's gates, and completion (gate)

**Files:**
- Modify: `specs/feasibility-pilot-and-threshold-calibration.md` (the slice stamp, at the end of §Rollout)
- Modify: `specs/deferred_items.md` (only if execution defers anything)
- Modify: this plan (completion markup), then `git mv` it to `specs/plans/completed/`

- [x] **Step 1: Run every scoped check in the worktree**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/evaluation packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_import_boundaries.py -q
uv run --locked --all-packages pytest packages/earnings-themes/tests/coding packages/earnings-themes/tests/support -q
uv run --locked --all-packages pytest tests/contracts tests/integration/test_coding_frozen_v0.py tests/integration/test_support_fixtures.py tests/integration/test_theme_frozen_v0.py tests/integration/test_theme_vertical_slice.py apps/earnings-pipeline/tests/test_theme_workflow.py -q
uv run --locked ruff check .
uv run --locked ruff format --check .
uv lock --check
git diff --stat main...HEAD -- evaluation config data CLAUDE.md tests/integration/test_stage6_wording.py
```

Expected:
- every test passes, and Ruff prints no finding. The replay gave command 1 `161 passed`, command 2 `1517 passed, 1 skipped, 2 deselected` and command 3 `603 passed, 1 deselected`;
- `uv lock --check` prints `Resolved 153 packages`;
- the last command prints nothing: no evaluation record, no model config, no `CLAUDE.md` line and no gate file changed.

Record the exact pass counts for the handoff.

- [x] **Step 2 (gate): Hand the user the checks only they run**

Put this to the user in chat, with `<sha>` set to `git rev-parse HEAD`, and wait for the results:

> Plan 19 (Stage 11 plan A, slice 3) is implemented on `<branch>` at `<sha>`. Two checks are yours, because they run the full suite and the wording gate.
>
> Run them in the main checkout after `git switch --detach <sha>`, and finish with `git switch main`:
>
> 1. **The root suite:** `uv run --locked --all-packages pytest packages apps tests -m "not live and not browser"`.
>    - The last recorded run, at `351ac94` (plan 18's gate), gave 4428 passed, 2 skipped, 28 deselected and 1 warning, in 835 s. `main` has since gained PR #21's test changes.
>    - This plan adds 170 tests. Expect `main`'s count plus 170 passed, the same skips, and 0 failed.
>
>    Please send the passed, skipped and deselected counts.
> 2. **The Stage 6 wording test:** `uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs`.
>    - This plan did not edit it. Expect 7 passed and 0 skipped, as at `351ac94`.

If any check fails, stop, and debug it with systematic-debugging before going on. Debug from the test name and reason the user reports, never from pilot text.

- [x] **Step 3: Run the Plan Completion Protocol**
> Deviation: the final whole-branch review (an Opus code-reviewer and Codex) raised findings that the user ordered fixed in five rounds after the review (bc9769e to eccb77c); each is recorded as a Deviation under its task above. Codex found defects in two ranges (`f5d5f15`, and the one-credit rule of `c7aa473`, which was reverted); its last review, `90a7f33`, found nothing.

Follow writing-plans' Plan Completion Protocol:
- **Resolve-before-defer:** ask the user about anything left open, in one batch (AskUserQuestion, default option first).
- **Markup:** tick the steps, and set the status header `**Status: COMPLETE (YYYY-MM-DD)** — executed via <skill>; …`.
- **Deferred items:** this slice closes none of `specs/deferred_items.md`'s open items. P17-5's "Done when" names the plan that implements A8. D19-7 decides its item (2), which slice 4's plan records when it closes the item. Append a `19-…` section only if execution deferred something.
- **Backlog triage:** run it as the protocol describes.
- **The slice stamp:** append at the end of the spec's §Rollout, after plan 18's stamp:

  ```text
  > Plan A, slice 3: COMPLETE (YYYY-MM-DD) — implemented by plan 19 (specs/plans/completed/19-feasibility-pilot-and-threshold-calibration-plan-a-slice-3.md): A3, A4, A5, and A9's dictionary rows for their records; FP10, FP14, FP18, FP22, A3, §Preregistration, §Calibration, §Failure handling and §Metrics amended. Next: write plan A's last slice (A8, with A9's dictionary rows for its records).
  ```

  Commit it as `docs(specs): stamp Stage 11 plan A's third slice`.

  Do not append `Plan A: COMPLETE`. Do not tick Stage 11 on the roadmap.
- **Retire:** `git mv` this plan to `specs/plans/completed/` in one `chore(specs): retire plan 19` commit.

  **Do not move the spec.** This is an exception to the protocol's spec-retire rule: the plans for A8 and plan B still implement it.

- [x] **Step 4: Hand off what goes stale**

Tell the user these, without editing the files:
- `CLAUDE.md`'s "Current state" names Stages 1–10. Stage 11's slices could be noted there, but per the spec's Rollout and the user's rule, only with the user's approval.
- Plan A's last slice is next: a writing-plans session from `main` for A8, using this plan's §Handoffs.

Then go on with finishing-a-development-branch.

---

## Handoffs to plan A's last slice (A8)

Verified at `7948d94` while this plan was written. Recheck each line number before relying on it.

- **`pilot labels sample`.**
  - Reverify the partition's MiniCheck pass support run (`reverify_support_run`).
  - Build `label_pool(support.targets, outcomes, events_by_doc)` from the reverified outcomes. `events_by_doc` maps each document to its event; an unknown document is `unknown_event`.
  - Draw `sample_targets(pool, seed=preregistration.sampling.seed, size=…, cap=…)`. For train, the size is `train_size + train_extensions × extension_step` and the cap is `train_cap`. For dev, they are `dev_size` and `dev_cap`.
  - The sample is a prefix: a larger size extends it (D19-12).
- **`pilot labels view`.**
  - Write `label_views(support, sources, sample)` under `data/runs/pilot/labels/views/`. Never print it and never commit it: it holds quotes in context (GS13, GS3).
  - A8 also writes the working file's skeleton: each sampled target's ID and `target_input_hash`, its partition, and blank answers. Its format is A8's choice.
- **`pilot labels check`.**
  - Run `load_labels` on the working file, then `check_labels(working, partition=…, sample=…, input_hashes=…, preregistration_hash=…)`, then `merge_labels(committed, working, partition)`, then `labels_toml` to the committed path.
  - `input_hashes` maps target ID to `TargetRecord.input_hash`.
  - A train extension raises `train_extensions` and must be a superset of the committed train labels (`labels_changed` otherwise).
- **`pilot calibrate`.** Call `calibrate(preregistration, labels, labels_hash=…, views=…, alternative=…, events=…, configuration=…)` with:
  - `labels_hash`: the SHA-256 of the committed label file's bytes;
  - `views`: `decision_inputs(support, sources)` over train's reverified MiniCheck support run;
  - `alternative`: `{target_id: joint_score(view)}` over the DeBERTa run's `decision_inputs`;
  - `events`: target ID to event, by document;
  - `configuration`: `frozen_configuration(extraction_record, proposal_record, minicheck_support_record, support_policy)`. A support policy the run did not run under is `malformed_record`.
- **`pilot run`.**
  - Bind `CalibratedPolicy(artifact, codebook=…, classifier_configuration_hash=…, support_configuration_hash=…)`.
  - The two hashes are the replayed coding and support runs' configuration hashes, which the workflow checks (`_policy_reference`). The workflow computes them inside `run_theme_workflow` (`theme_workflow.py`, around `:1010-1022`) and in `propose_run`. Precompute them before the workflow runs by extracting those computations into shared helpers that both call (D18-1). Never copy them.
  - Bind with `dataclasses.replace(replay_runtime(config), assignment_policy=policy)`. Set `config.policy_reference = policy.reference`: research scope fixes it up front (`theme_workflow.py:395`).
  - Before deciding, `pilot run` recomputes `frozen_configuration` over its own records and compares `digest({"configuration": …, "selection": …})` with the artifact's `configuration_hash`. A mismatch is a refusal. Both partitions must use one ceilings configuration, or dev cannot reproduce it.
  - With a `no_candidate` artifact, `CalibratedPolicy` refuses. `pilot run` then runs with no policy, every target stays in review, and the report and V6 record say that no configuration passes (§Calibration).
- **`pilot report`.**
  - Build each `EventObservation` from:
    - the signed gold and `unit_index(bundle)`;
    - each accepted decision's theme and its evidence spans (`Accepted`);
    - `release_confirmed`, from Stage 5's kept attempt;
    - `quotes=(kept, offered)`;
    - `targets=(accepted, assessed)`.
  - Retention (i)'s source columns are undecided. A8 picks them from the extraction run's records.
  - Each `LabelledTarget` takes the label's `claim_label` and `joint_label`, the decision's `accepted`, `scores` keyed `"minicheck"` and `"deberta"`, and the target's trials.
  - `stability_figures(runs, codebook, plan)` runs over the three fresh runs.
  - The independent pass gives `compare_readings(reference, other, index)` for record vs draft and signed vs record. `verify_independent` raises `RecordError` for an unreadable record, so catch it (P17-5(3)).
  - Assemble and seal a `PilotReport` (`sealed`).
- **`pilot gates`.**
  - Call `derive_gates(report, gated=preregistration.gates.gated, undefined_gate=preregistration.gates.undefined_gate, judge_floor=preregistration.floor.floor, preregistration_hash=preregistration.content_hash)`, then write it with `gates_toml`.
  - `evaluate_gates` checks any later configuration's dev report.
- **B2 needs a tool to write the preregistration.** No `pilot preregister` command exists. `freeze_preregistration(fields)` and `preregistration_toml` do the work. The user decides between an A8 command and a plan B procedure.
- **Deferred into slice 4, unchanged:** P17-1 and P17-2 go with A8, as do P17-5's items (1), (3) and (4). D19-7 decides item (2), which slice 4 records when it closes P17-5 (`specs/deferred_items.md`, section `17-feasibility-pilot-and-threshold-calibration-plan-a-slice-1`). P18-1 and P18-2 stay as plan 18 left them.
- **Slice 4's dictionary rows** cover A8's command records and any new working-file record.
- **Added at completion** (per-task reviews and the final review; none is closed by plan 19):
  - **H1.** `pilot labels view` must call `reverify_support_run` before `label_views`, write only under `data/runs/pilot/labels/views/` and never print; `label_views` does not reverify (GS13, GS3). `check_labels` must run before `merge_labels`; the order is not enforced in code.
  - **H2.** `calibrate` never relates `labels_hash` to the labels: verify `sha256(labels_toml(labels)) == labels_hash`, or hash the bytes that were parsed.
  - **H3.** `frozen_configuration` does not check `extraction.run_id == support.source_run_id` nor that proposals and support agree (`coding/decide.py:367-378`): `pilot calibrate` must apply that gate, extracted from `decide_assignments`, never copied. `decision_inputs` does not check it either.
  - **H4.** `pilot run` must call the public `calibration.configuration_hash` and compare it with `artifact.configuration_hash`; `CalibratedPolicy` accepts any hashes it is given.
  - **H5.** Branch on `.problem is EvaluationProblem.NO_CANDIDATE`: catching every `EvaluationError` would let a tampered artifact (`content_hash_mismatch`) run with every target in review.
  - **H6.** A8 owns the calibration-artifact reader (the `RecordError` path for a committed `calibration-v<N>.json`); slice 3 has none.
  - **H7.** `apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py` (~:1009-1022) still builds `support_configuration`'s six keys inline; when A8 extracts the workflow's hash computations it should call `support.records.support_configuration`. Touching `theme_workflow.py` also fires deferred item P15 M1's 'Revisit if'.
  - **H8.** `merge_labels` lets `train_extensions` rise with no new labels; the caller must tie the counter to growth.
  - **H9.** `label_pool` is last-wins and skips a target with no outcome: confirm `reverify_support_run` guarantees one outcome per target.
  - **H10.** `GateVerdict` can hold two `GOLD_EVIDENCE_RECALL` results (the gate row with a bound, the positivity row with `bound=None`); never key results by metric.
  - **H11.** `stability_figures` has no home in `PilotReport`: append them to dev's `PartitionReport.figures` (the unique `(metric, qualifier)` validator allows it) or add a field before any report is committed.
  - **H12.** Judge family names must be `IdPart`-safe: constrain `ChatModelFile.family` at config intake (B1), or refuse early in `partition_report`; a non-`IdPart` family would crash a `Figure.qualifier`.
  - **H13.** The export list omits `joint_score`, `sealed`, `claim_label`, `joint_label`, `Figure`, `ReadingAgreement`, `IndependentFigures`, `EvidenceTally` and `configuration_hash`: import them from their submodules, or decide at A8.
  - **H14.** Pin the scorer-view vocabulary in the dictionary: report qualifiers `minicheck` and `deberta` against `MetricReport.view` values `minicheck_joint` and `deberta_joint`.
  - **H15.** `scores.hard_negative_counts` still drops a hard negative's dangling quote IDs silently (D19-7, P17-5(2)); A8's report should surface them if a kept draft can hold any.
  - **H16 (for plan B).** Tie-group evidence is scored by accepted `(theme, item)` pairs. Redundant correct alternatives, whether excused or scored, each count as hits, so the gated `span_unit_f1` can rise when a run adds a correct alternative, and which member is excused follows D19-6's lowest-ID rule. A maximum matching of accepted pairs to gold `(cell, item)` pairs (scored first, per atomic segment for characters, unmatched in-slot pairs neutral) is the stricter alternative with trade-offs of its own: it can give up monotonicity if excused in-cell pairs stay accepted. Decide from the pilot's gold if overlapping tie groups matter (`specs/deferred_items.md`, section `19-…`). The data dictionary's `EvidenceCell` paragraph says this is recorded here.

---

## Self-review

- **Spec coverage:**

  | Spec point | Where it's built |
  | --- | --- |
  | A3: alignment of gold and run quotes to pointer units by character overlap | Task 2 (`align`) |
  | A3: the metrics of §Metrics | Tasks 3, 4 and 7 (`cells`, `scores`, `report`) |
  | A3: the event-clustered bootstrap, seeded from the preregistration, with percentile intervals | Task 5 (`bootstrap`); Task 13 (`Preregistration.bootstrap`) |
  | A3: Cohen's κ, Gwet's AC1 and Fleiss' κ | Task 5 (`agreement`) |
  | A3: the gate evaluator; gold-evidence recall above zero; `None` fails | Task 8 (`evaluate_gates`) |
  | A3 tests: hand-computed known answers, including `uncertain`, `tie_group` and macro exclusion | Tasks 3, 4 and 7 |
  | A3 tests: a deterministic bootstrap; a reject-everything policy fails invented gates | Tasks 5 and 8 |
  | A4: `SupportLabel`, strict, with no free text | Task 9 |
  | A4: a deterministic sampler that takes IDs only, round-robin by event and theme | Task 10 (with the signature test) |
  | A4: the label view and its sentinel | Task 11 |
  | A4: `labels check` refuses a target-hash mismatch and a set that differs from the sample | Task 9 (`check_labels`) |
  | A5: `Preregistration`, with a loader that rehashes the file | Task 13 |
  | A5: `calibrate` refuses a mismatched preregistration and fewer than 50 usable joint labels | Task 14 |
  | A5: the floor test, the fit and selection, and `CalibrationArtifact` | Task 14, as Task 1 amends §Calibration (D19-1) |
  | A5: `CalibratedPolicy` with `PolicyReference(kind="calibrated")` | Task 15 |
  | §Metrics: each row, with point, interval and in-sample flag; feasibility-only label | Tasks 6 and 7 |
  | §Calibration: AUC for MiniCheck and DeBERTa against `claim_support`; the frozen configuration hash | Task 14 (D19-14) |
  | A9: a dictionary row for every new record, enforced by `test_data_dictionary.py` | Tasks 2–15 |
  | §Verification: the import boundary for `evaluation` | Task 2 (D19-4) |
  | FP10, FP14, FP18, FP22, A3, §Preregistration, §Calibration, §Failure handling, §Metrics | Task 1 (D19-1, D19-3, D19-4) |

  Not here, by D19-2: A8's commands and their sentinels, the files they write, and A9's dictionary rows for A8's records.
- **Placeholders:** none.
  - Every code step shows its code, rendered from the verified prototype.
  - The user's gate asks for counts that no session can know in advance.
  - `<sha>`, `<branch>` and the dates are filled in at execution.
- **Type consistency.** Generated from the code itself: each task's Interfaces lists its modules' public signatures as the prototype defines them. The replay applied the tasks in order and ran each task's tests, so every name a task consumes exists by then.
