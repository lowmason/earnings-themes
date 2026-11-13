# Run-Path Performance Implementation Plan

**Status: COMPLETE (2026-11-13)** — executed via subagent-driven-development; deferred items in specs/deferred_items.md

Outcome: Tasks 1 to 6 were executed and reviewed. Task 7's projection stopped at 13.49 h (D23-5), and plan 24 (`specs/plans/completed/24-cheaper-key-check.md`) finished the work: the projected train `pilot run` is 7.19 h on invented text. The owner's root and wording gates passed at `5804663` (5,810 passed; wording 7 passed).

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make one train-scale `pilot21` replay command (`run`, `labels`, `calibrate`, `report`) finish within 8 h, without changing a stored record, hash, cache key or refusal reason.

**Architecture:** Each spec-named gate still re-verifies its inputs in full. Inside one gate, an unchanged input is validated once and the result is reused. A new `earnings_themes.scope` module holds a context-scoped memo: the outermost gated call opens a scope, nested gated calls join it, and publication gates always open a fresh one. Separately, the support cache stops repeating work that depends only on an immutable key's text.

**Tech Stack:** Python 3.14.0, pydantic, `contextvars`, `functools.lru_cache`, pytest; uv workspace (`earnings-themes`, `earnings-pipeline`).

**Spec:** none. The requirements are D21-34 in `specs/plans/21-feasibility-pilot-and-threshold-calibration-plan-b.md`. Read it first. It holds the measurements, the gates the specs require, and the owner's three answers.

## Global Constraints

- No stored record, Parquet table, manifest, hash, `configuration_hash`, version string or cache-key format may change. Train's support cache (7,792 entries, about 107 GB, P21-1) must still replay. Tasks 1's pinned digests and pinned output hashes must pass after every task.
- Every existing test passes unchanged. If a test fails, stop and report its name and failure to the owner. Do not edit, skip or loosen an existing test.
- Spec-required gates stay in full (D21-34): exact spans before scoring, before support publication and at each consuming gate (Stage 8 SS3, R8.5, R6.1); current sources, masks and codebook at each consuming gate (plan 15 §5); raw-cache bytes through the cache's own reader before `verified` (plan 15 Task 3).
- Refusal reasons stay the same closed codes. Only when an in-place mutation inside one gate is detected may change: at the end of that gate instead of at once (owner, D21-34).
- `assess_run` and its scorer/judge dispatch path get no scope memo. Per-target resolution there stays as it is.
- The Stage 8 spec says that "possessing a resolved input does not waive a re-check" (`specs/completed/semantic-support-assessment.md:120`). This plan meets it as D21-34 states: every gate still re-checks. Only a repeat inside one gate reuses that gate's first check (D23-1).
- Two memos are content-keyed and process-wide, not scoped: `_binding_once` and `_check_records_once` (Task 3). They survive across gates, including fresh ones. They are exact, because each is a pure function of immutable text, so changed text always gets a new key. `artifact_hash` still reads and hashes the entry bytes on every call.
- Each memoized body is a module-level function called through its module's globals, so a test can count its calls with `monkeypatch.setattr`.
- Tests and helpers use invented text only (GS13). No agent opens `data/`, pilot views, working files or cache entries under `data/`. No agent runs the root suite, the Stage 6 wording gate, browser or user-only modes, or `-m live`.
- Commands: `uv run --locked --all-packages pytest <paths> -m "not live and not browser" -q --tb=short`; `uv run --locked ruff check .`; `uv run --locked ruff format --check .`.

## Review Focus

1. Two runs whose sources differ in one element must not share a memoized validation. The second must be validated, and a key whose bundle text was altered must still refuse (Task 3).
2. A bound policy that mutates another target's data in place during `evaluate` must still make `decide_assignments` refuse with `input_changed`, now at the end of the gate (Task 4; the existing `test_policy_cannot_mutate_a_later_targets_raw_signals` stays green).
3. A gate that raises must not leave a cached result behind. The same bad input must refuse again on the next call in the same scope (Task 2).
4. B7's fresh runs call live adapters. Classification refuses a source mutated during the model callback before publication, as today (Task 5; existing `test_invalid_source_mutation_during_callback_aborts_publication` stays green).
5. A scope must release everything it holds when it closes. Memory in an 8 h run must not grow with the number of gates run (Task 2).

## Decisions

- **D23-1** (owner, brief, 2026-11-12): Inside one gate, each unchanged input is validated once and reused. Per-target re-checks compare content digests. In-place mutation between two targets is caught at the end of the gate (D21-34, “Once per gate, shared”). Applied in: Global Constraints, Tasks 2–6.
- **D23-2** (owner, brief, 2026-11-12): This is its own plan. D21-34 in plan 21 records the pause in B6 (D21-34, “Own plan + D21-34”). Applied in: header, Task 7.
- **D23-3** (owner, brief, 2026-11-12): One train-scale pilot replay command finishes within 8 h on the owner's machine (D21-34, “Under 8 h (overnight)”). Live passes are bounded by model time and are outside this budget. Applied in: Goal, Task 7.
- **D23-4** (owner, plan review, 2026-11-12): “Approve both” — D21-34's text and this plan as written at `1c76e23`. Applied in: header.
- **D23-5** (owner, execution, 2026-11-13): Task 7's projection was 13.49 h (invented text at real key size, floors): proposal replay 3.45 h, support replay 2.99 h, 12 raw-cache sweeps 5.42 h, 9 decides 1.10 h, load 0.53 h. Task 7's stop rule fired. The owner chose “Plan cheaper key check”, and then “Key check only” as its scope, so the `resolve_target` memo stays out. Applied in: header, Task 7 (steps 3 to 5 move to plan 24).
- **D23-6** (controller ruling, execution, 2026-11-13, for the owner's review in the PR): Task 3 changed two details of the text. The record-list memo keeps 512 lists, not 16, because a cyclic scan of 44 lists never hits an LRU of 16. `artifact_hash` shares `_check_entry` with `_read_entry` and does not call `_read_entry`, because it has no key until it has parsed the bytes. Applied in: Task 3.
- **D23-7** (controller ruling, execution, 2026-11-13, for the owner's review in the PR): Task 4 added more than its text names. `decide_assignments` digests the sources, the proposal record, and the rows each vote reads (evidence, entailment, trials, the outcome copy) before external code runs, and compares them before each vote. `reverify_support_run` returns fresh shallow copies of its outcomes on every call. Three review rounds found each hole; the existing mutation tests stay green. Applied in: Task 4.
- **D23-8** (controller ruling, execution, 2026-11-13, for the owner's review in the PR): Task 5's expected `_checked_bundle` count is 9, not 5. `propose_run` has two fresh post-loop gates, so the final bundle check runs after the identity read, and `classify_claim` ends each claim with a fresh full current-request check. Applied in: Task 5.
- **D23-9** (controller ruling, execution, 2026-11-13, for the owner's review in the PR): Task 6 has no `raw_caches` memo, because a changed cache file would be published and two refusal codes would change. Each full check ends with a policy-free compare (`_require_unchanged`) and a fresh fallback check. The second raw-cache sweep reuses the first only when the cache objects and the raw bindings are unchanged (option R), so a sweep runs 12 times, not 8. In the workflow block, a policy that changes the caller's `RawSnapshot.data` on its last read now refuses `storage_corrupt` where base refused `input_changed`. A test pins this one difference. Applied in: Task 6.

---

### Task 1: Pin today's outputs and commit the harness

**Files:**
- Create: `packages/earnings-themes/tests/support/test_cache_known_answer.py`
- Create: `apps/earnings-pipeline/tests/test_pilot_run_bytes.py`
- Create: `expirements/run-path-performance/README.md`
- Modify: `expirements/run-path-performance/realsize.py` and `scaling.py` (committed with this plan; the scripts that produced D21-34's figures)

**Interfaces:**
- Produces: `realsize.py` CLI `python expirements/run-path-performance/realsize.py <docs> <paragraphs> [--themes N]`, printing one line per phase (`<phase> n=<count> <seconds> s`) and the per-unit costs that Task 7 projects. It builds N invented themes (default 22, as codebook v0) in the pattern of `tests/coding/cases.py::invented_codebook`.

- [x] **Step 1: Write the pinned-digest test.** `test_support_and_coding_cache_names_are_pinned` runs the invented `assessed_case` fixture path (`make_proposal_job` then `make_assessed_case`, live mode, `tmp_path` caches). It asserts `sorted(p.name for p in (tmp_path / "support-cache").rglob("*.json"))` and the same for `classifier-cache` equal two literal lists. Fill the lists by running the test once on this commit. Each name is `<sha256>.json`, so the names pin the key digests.
- [x] **Step 2: Write the output-bytes test.** `test_pilot_run_writes_the_same_bytes[selected|none]` reuses `test_pilot_workflow.py`'s `seed_case`, `runtime` and `bound_artifact`. It runs `make_pass`, then `make_run` (replay, train), and asserts `{relative path: sha256}` for every file under the pass and run directories equals a literal dict. Fill each dict from one run on this commit. Run the test twice. If any hash differs between the two runs, stop and report. Do not drop a file to make it stable.
- [x] **Step 3: Run both tests.** Expected: PASS (they pin today's behavior).
- [x] **Step 4: Extend the harness.** Add `--themes N` to `realsize.py` and `scaling.py`. Write the README: invented text only, how to run, and that the costs are floors.
- [x] **Step 5: Record the baseline.** Run `realsize.py 20 1850 --themes 22` and keep its output for Task 7. Planning-time reference with 2 themes: proposal replay 2.56 s per claim, support replay 2.95 s per entry, `artifact_hash` 1.35 s per judge entry, `decide_assignments` 67 s at 21 targets.
- [x] **Step 6: Run ruff and the two new tests; commit** `test(perf): pin cache digests and run bytes; add run-path harness (plan 23)`.

### Task 2: The gate scope

**Files:**
- Create: `packages/earnings-themes/src/earnings_themes/scope.py`
- Test: `packages/earnings-themes/tests/test_scope.py`

**Interfaces:**
- Produces:
  - `gate(*, fresh: bool = False) -> ContextManager[None]`: opens a scope, or joins the open one unless `fresh`. A `fresh` scope hides the outer memo until it closes.
  - `gated(function=None, *, fresh: bool = False)`: decorator form of `gate` for a whole call.
  - `once(kind: str, objects: tuple[object, ...], compute: Callable[[], T]) -> T`: inside a scope, returns the value computed earlier for the same `kind` and the same objects (compared by identity), else calls `compute`. Outside a scope it always calls `compute`. The scope holds strong references to the keyed objects, so an identity cannot be reused while the scope is open. An exception is never stored.
  - `remember(kind: str, objects: tuple[object, ...], value: object) -> None`: inside a scope, stores `value` under one more key, so a later `once` with those objects returns it. Outside a scope it does nothing.
- The active scope lives in a `contextvars.ContextVar`.

- [x] **Step 1: Write the failing tests:**
  - `test_once_outside_a_scope_always_computes`;
  - `test_once_inside_a_gate_computes_once_per_identity`: two equal but distinct objects compute twice;
  - `test_nested_gate_joins_and_fresh_gate_hides_the_outer_memo`;
  - `test_an_exception_is_not_remembered`;
  - `test_closing_the_outermost_gate_releases_the_memo`: use a `weakref` to a keyed object, and check that it dies after the gate closes;
  - `test_gated_decorator_opens_or_joins`;
  - `test_remember_adds_a_second_key`.
- [x] **Step 2: Run** `pytest packages/earnings-themes/tests/test_scope.py`. Expected: FAIL (module missing).
- [x] **Step 3: Implement `scope.py`** to the interfaces above. Import nothing from other `earnings_themes` modules.
- [x] **Step 4: Run the tests.** Expected: PASS.
- [x] **Step 5: Commit** `feat(themes): add a gate-scoped validation memo (plan 23)`.

### Task 3: Support-cache lookups do each check once

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/support/cache.py` (`_binding`, `raw_ref`, `_entry`, `_reply`, `lookup`, `artifact_hash`)
- Test: `packages/earnings-themes/tests/support/test_cache_cost.py`

**Interfaces:**
- Produces, as module-level functions:
  - `_validate_binding(key_text: str, material: str, kind: str) -> tuple[request, identity]`: today's `_binding` body.
  - `_binding_once`: `functools.lru_cache(maxsize=8)` around `_validate_binding`. `SupportCache._binding(key, kind)` calls it with `(str(key), key.material, kind)`.
  - `_check_records(model, records: list) -> None`: validates one record list.
  - `_check_records_once(model, records)`: remembers `(model.__name__, digest(records))` in a bounded LRU (maxsize 16), so a bundle, claim or quote list identical in content is validated once.
  - If a request or identity model returned by `_binding_once` is not frozen, the call returns a `model_copy()`, so one caller cannot change another caller's value.
- `artifact_hash(reference)` and `_entry` share one private reader, `_read_entry(path, key, kind) -> SupportCacheEntry`. It reads the bytes once, runs every check `_entry` runs today, and returns the entry. `artifact_hash` hashes the same bytes it read.

- [x] **Step 1: Write the failing tests** over invented sources with 2 documents and a 2-theme codebook:
  - `test_a_lookup_validates_its_binding_once`: `_validate_binding` runs once for one `lookup`, and not again when the same key is looked up a second time.
  - `test_bundle_records_are_validated_once_across_keys`: across all scorer and judge lookups of one assessed case, `_check_records` runs once per distinct list, not once per lookup.
  - `test_artifact_hash_reads_each_entry_once`: count `Path.read_bytes` in the cache directory. One `artifact_hash` call reads once.
  - `test_changed_bundle_text_is_validated_and_refused`: build a second source with one element changed. Its keys validate their bundle list anew, and a key whose material was edited still raises `SupportError("malformed_record")`.
- [x] **Step 2: Run them.** Expected: FAIL on the counts.
- [x] **Step 3: Implement** to the interfaces. The material, entry bytes and file names stay byte-identical.
- [x] **Step 4: Run** `pytest packages/earnings-themes/tests/support` and Task 1's two tests. Expected: PASS.
- [x] **Step 5: Measure** `realsize.py 20 1850 --themes 22`. Record the support-replay and `artifact_hash` costs per entry in the commit body.
- [x] **Step 6: Commit** `perf(themes): check each support-cache binding once (plan 23)`.

> Deviation: the record-list memo keeps 512 lists, not 16, and `artifact_hash` shares `_check_entry` with `_read_entry` (D23-6).

### Task 4: One support re-verification per gate in decide

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/support/resolve.py` (extract `_checked_bundle`), `support/store.py` (`reverify_support_run`), `coding/decide.py` (`_proposal_inputs`, `decide_assignments`, `validate_proposal_support`)
- Test: `packages/earnings-themes/tests/coding/test_decide_cost.py`

**Interfaces:**
- Consumes: Task 2's `gate`, `gated`, `once`.
- Produces:
  - `support.resolve._checked_bundle(bundle: Bundle) -> Bundle`: today's validation of the document, elements and masks, plus `bundle_problems`, taken from `resolve_target`. It is called through `once("bundle", (bundle,), ...)`.
  - `support.store._reverify_support_run(stored, sources)`: today's body. The public `reverify_support_run` is `@gated` and calls it through `once("support", (stored, sources), ...)`.
  - `coding.decide._proposal_inputs` is called through `once("proposal_inputs", (proposals, sources), ...)`.
  - `decide_assignments` and `validate_proposal_support` are `@gated`.
- In `decide_assignments`:
  - The full `require_current()` runs once before the loop, in the open scope.
  - Per target: `_policy_reference` is compared again, and the target's own support row, outcome and proposal are each compared by `digest` with the values taken at the start.
  - After the loop: one full `require_current()` inside `gate(fresh=True)`.
  - `decision_vote`'s `_view_hash` check stays as it is.

- [x] **Step 1: Write the failing tests:**
  - `test_decide_reverifies_the_support_run_twice_at_any_size`: count `_reverify_support_run` over 3 targets and over 6 targets. Expected: 2 both times.
  - `test_a_gate_validates_each_bundle_once`: count `_checked_bundle` while resolving 2 claims × 2 themes on one document inside `gate()`. Expected: 1.
  - `test_reverify_outside_a_gate_still_checks_each_call`: two top-level `reverify_support_run` calls count 2.
- [x] **Step 2: Run them.** Expected: FAIL.
- [x] **Step 3: Implement** to the interfaces.
- [x] **Step 4: Run** `pytest packages/earnings-themes/tests/coding packages/earnings-themes/tests/support` and Task 1's tests. Expected: PASS, including every existing mutation test in `test_decide.py`.
- [x] **Step 5: Commit** `perf(themes): re-verify support once per decide gate (plan 23)`.

> Deviation: the task also digests the sources, the proposal record and the rows each vote reads, and `reverify_support_run` returns fresh outcome copies (D23-7).

### Task 5: One resolution per claim in classification

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/coding/classify.py` (`classify_claim`), `coding/run.py` (`propose_run`)
- Test: `packages/earnings-themes/tests/coding/test_classify_cost.py`

**Interfaces:**
- Consumes: Task 2's `gated`; Task 4's `_checked_bundle`.
- `classify_claim` is `@gated`, so one claim's inputs, prompt rendering and attempts share one scope.
- In `propose_run` (`coding/run.py`), the resolution of every claim before the loop (today lines 209–211) runs inside one `gate(fresh=True)`, and the checks after the loop and before publication (today lines 269–304) run inside another. Both stay outside every claim's scope, as today.

- [x] **Step 1: Write the failing test** `test_each_claim_checks_its_bundle_once`: count `_checked_bundle` during `propose_run` replay of 3 claims on one document with a 2-theme codebook. Expected: 5 (one for the pre-loop gate, one per claim gate, and one for the post-loop gate). Today the same replay runs `resolve_target` about 74 times per claim.
- [x] **Step 2: Run it.** Expected: FAIL.
- [x] **Step 3: Implement.**
- [x] **Step 4: Run** `pytest packages/earnings-themes/tests/coding` and Task 1's tests. Expected: PASS, including `test_invalid_source_mutation_during_callback_aborts_publication` and `test_classification_final_preflight_checks_bindings_after_callback`.
- [x] **Step 5: Commit** `perf(themes): resolve each claim once per classification gate (plan 23)`.

> Deviation: the expected `_checked_bundle` count is 9, not 5, because `propose_run` has two fresh post-loop gates (D23-8).

### Task 6: Analysis gates share one verification

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/analysis/consume.py` (`reverify_analysis_inputs`, `_cache_verification`), `analysis/store.py` (`write_analysis_run`, `reverify_analysis_run`), `analysis/prevalence.py`, `analysis/completion.py`, `analysis/coverage.py`, `analysis/rows.py` (the `@gated` entries); `apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py` (`run_theme_workflow` analysis phase); `apps/earnings-pipeline/src/earnings_pipeline/theme_report.py` (`write_theme_report`)
- Test: `apps/earnings-pipeline/tests/test_pilot_gate_counts.py`

**Interfaces:**
- `consume._reverify_analysis_inputs(inputs)`: today's body. The public `reverify_analysis_inputs` is `@gated` and calls it through `once("analysis", (inputs,), ...)`. Then it calls `remember("analysis", (bound.inputs,), bound)`. This matters because `strict_analysis_inputs` returns a copy, and `BoundAnalysis.inputs` holds that copy. A planning probe of the tiny `make_run` found that 78 of 128 `strict_analysis_inputs` calls received an earlier result's `.inputs` copy, not the caller's object. Without the second key, those calls would all miss.
- `_cache_verification(inputs)` is called through `once("raw_caches", (inputs.raw_caches.coding, inputs.raw_caches.support, inputs.coding, inputs.support), ...)`.
- `document_completions`, `build_coverage`, `build_analysis` and `build_observations` are `@gated` (they join).
- The publication and read-back gates, `write_analysis_run`, `reverify_analysis_run` and `write_theme_report`, are `@gated(fresh=True)`.
- In `run_theme_workflow`, the consuming steps before publication run inside one `with gate():` block: `reverify_analysis_inputs`, `document_completions`, the transitions that use them, and `build_analysis`, which is now assigned to a variable inside the block. `write_analysis_run` is called after the block.

- [x] **Step 1: Write the failing test** `test_one_pilot_run_counts_its_gates`. It runs Task 1's tiny `make_pass` and `make_run` (both artifacts) and counts calls through monkeypatched module globals. Today's counts: `_proposal_support_inputs` 67, `_cache_verification` 192, `_reverify_analysis_inputs` 64 (body), `_reverify_support_run` 473. Expected bounds: `_proposal_support_inputs` ≤ 12, `_cache_verification` ≤ 8, `_reverify_analysis_inputs` ≤ 8, `_reverify_support_run` ≤ 30.
- [x] **Step 2: Run it.** Expected: FAIL.
- [x] **Step 3: Implement** to the interfaces.
- [x] **Step 4: Run** `pytest packages/earnings-themes/tests/analysis apps/earnings-pipeline/tests` and Task 1's tests. Expected: PASS, including `test_policy_callback_mutation_refuses_before_writes` and `test_policy_mutation_of_original_inputs_refuses`.
- [x] **Step 5: Commit** `perf: share one verification per analysis gate (plan 23)`.

> Deviation: no `raw_caches` memo, `_require_unchanged` and option R instead, 12 sweeps, not 8, and `storage_corrupt` where the base refused `input_changed` in one case (D23-9).

### Task 7: Check the budget and record it

> Execution note (2026-11-13): steps 1 and 2 are done (`1b5562f`). Step 2 stopped at 13.49 h, so D23-5 moves steps 3 to 5 to plan 24, Task 4, which measures again after its change.

**Files:**
- Modify: `expirements/run-path-performance/realsize.py` (projection), `docs/verification/pilot-v1-feasibility.md`, `specs/plans/21-feasibility-pilot-and-threshold-calibration-plan-b.md` (Status line only)

- [x] **Step 1: Add `--project`** to `realsize.py`. It prints the projected train `pilot run` time from the measured per-unit costs: 1,171 claims × proposal replay × 2 passes, plus 7,800 support entries × support replay × 2 passes, plus Task 6's sweep count × 4,866 judge entries × `artifact_hash`, plus Task 6's decide count × 1,170 targets × decide cost per target, plus 32 min for the load (the measured pre-plan time, an upper bound).
- [x] **Step 2: Run** `realsize.py 20 1850 --themes 22 --project`. Expected: a projection under 8 h. If it is 8 h or more, stop and report the per-phase figures to the owner. Do not add optimizations this plan does not name.
- [x] **Step 3: Record** a section "Plan 23 run-path performance, <date>" in the verification doc: a before/after table per phase, the projection, the gate counts, and the note that these are invented-text floors. In plan 21's Status line, add that plan 23 merged, if it has, and that B6 may resume (D21-34).
- [x] **Step 4: Run** `uv run --locked ruff check .`, `uv run --locked ruff format --check .` and `uv run --locked --all-packages pytest packages apps tests/contracts -m "not live and not browser" -q --tb=short`. Expected: clean, all pass. Then ask the owner to run the root suite and `tests/integration/test_stage6_wording.py` at the branch head.
- [x] **Step 5: Commit** `docs(pilot): record the run-path performance correction (plan 23)`.

> Deviation: steps 3 to 5 moved to plan 24, Task 4, after the projection stopped at 13.49 h (D23-5). Plan 24 completed them on 2026-11-13 with a projection of 7.19 h.
