# Development history

## 23-run-path-performance — 2026-11-13
Plan: specs/plans/completed/23-run-path-performance.md · Spec: none

Differences from the design:
- Ruling: scaling.py --themes default is 22, not 2 — brief fixed the default only for realsize.py; README documents --themes 2 to reproduce D21-34's figures — a user who runs scaling.py bare compares 22-theme output to D21-34's 2-theme figures.
- Ruling: _check_records_once LRU is 512, not the brief's 16 — a cyclic scan of 44 lists (train: 4 + 2*20 docs) never hits an LRU of 16; values are None, so memory cost is small; content-keyed, cannot serve stale — DEVIATION FROM PLAN TEXT: record as D23-5 in plan 23 at Task 7 and tell the owner in the PR; cost if wrong: none for correctness, only RAM for 512 short keys.
- Ruling: artifact_hash shares _check_entry with _read_entry instead of calling _read_entry(path,key,kind) — artifact_hash gets its key only by parsing the bytes, so one read forces the split; every check still runs, bytes read once and hashed as read — record in D23-5.
- Ruling: _binding returns request.model_copy(deep=True) (JudgeRequest.reply_schema is a mutable dict inside a frozen model); identity returned without copy; extra _material_kind memo (kind only) is correctness-neutral — kept.
- Ruling: items 2 and 3 of fix 2 (outcome copy status/flags/missing after the post-vote reference read: unexpected_error -> input_changed; view.eligible_quote_ids changed in decision_vote's model_dump: base returned a wrong decision, now input_changed) — base detected neither; input_changed is already the closed code for a changed view; a deterministic policy never reaches them.
- Ruling: option R chosen over J (merging write_theme_report's two read-backs into its own scope: owner's call, spec-named read-back gates would become memo hits) and K (brief's raw_caches memo: probes show it publishes a changed cache file and changes two codes). If Task 7's projection is >= 8 h, report per-phase figures; the owner decides about J.
- Ruling: the fallback in _require_unchanged — workflow block: a policy changing the caller's RawSnapshot.data on its last read now refuses storage_corrupt (base: input_changed via the view compare); same at write_theme_report's views check; pinned by test_workflow_gate_scope.py. ACCEPTED as a recorded deviation: both are closed codes, both refuse before any write, no position-dependent codes. OWNER SHOULD SEE THIS IN THE PR.
- Ruling: two invisible changes (first check's last read + fallback's last read) now refuse input_changed (base passed); double fault in write_analysis_run gives input_changed where base gave storage_corrupt; a NaN Parameters.temperature now refuses every analysis gate with input_changed (the copy compares unequal to itself) — ACCEPTED: fail-closed, write nothing, no reasonable config reaches them (temperature defaults to 0.0).
- Deviation (Task 3): the record-list memo keeps 512 lists, not 16, and `artifact_hash` shares `_check_entry` with `_read_entry` (D23-6). Source: plan, Task 3.
- Deviation (Task 4): the task also digests the sources, the proposal record and the rows each vote reads, and `reverify_support_run` returns fresh outcome copies (D23-7). Source: plan, Task 4.
- Deviation (Task 5): the expected `_checked_bundle` count is 9, not 5, because `propose_run` has two fresh post-loop gates (D23-8). Source: plan, Task 5.
- Deviation (Task 6): no `raw_caches` memo, `_require_unchanged` and option R instead, 12 sweeps, not 8, and `storage_corrupt` where the base refused `input_changed` in one case (D23-9). Source: plan, Task 6.
- Deviation (Task 7): steps 3 to 5 moved to plan 24, Task 4, after the projection stopped at 13.49 h (D23-5). Plan 24 completed them on 2026-11-13 with a projection of 7.19 h. Source: plan, Task 7.
- Deferred: 2 items. Source: specs/deferred_items.md, § 23-run-path-performance.

## 24-cheaper-key-check — 2026-11-13
Plan: specs/plans/completed/24-cheaper-key-check.md · Spec: none

Differences from the design:
- Deviation (Task 2): the memo key holds the fragment name (D24-4), and `_light_material` also requires the top-level lists to be empty and each later marker to occur once (D24-5). Source: plan, Task 2.
- Deviation (Task 3): `_check_material` takes `kind`, `RecursionError` joins the fallback list, and a test-only conftest shim keeps two existing cost tests unchanged (D24-6). Source: plan, Task 3.
- Deferred: 1 item. Source: specs/deferred_items.md, § 24-cheaper-key-check.

## 25-recover-unusable-saved-responses — 2026-11-13
Plan: specs/plans/completed/25-recover-unusable-saved-responses.md · Spec: none

Differences from the design:
- Ruling: the owner's 'ship as planned, file it' decision covers the whole class 'responses that belong to a filing discovery does not read': an override's index page (acquisition or event override) and the index page/primary document of a set_release_filing-named filing without Item 2.02 — the manual-repair pointer in plan_refetch's refusal, Task 8's manual cases and the third deferred item name the whole class — the 'remedy that works' clause stays unmet for it; owner told in the final report.
- Ruling (final review): the class in the ruling above was too wide. `read_back` reads the index page of every listed filing, so `discover --refetch` reaches an override's index page. The unreached class is the primary document of a filing that `release-id/1` passes over (an 8-K/A, or an 8-K whose index page lists no Item 2.02 or no EX-99* exhibit). The refusal text, the `events.acquire` docstring and "Repairing the store" say so (commits 2c8dd9d, 4251137), and the third deferred item names only that class.
- Deviation (Task 4): `run_refetch` raises `RefetchInterrupted` (an `Exception` that carries `.partial` and has the original error as `__cause__`) on a mid-plan failure, so Task 5's CLI prints the partial `changed:` and `quarantined:` lines before the stop. The refusal for a saved URL that discovery does not read also names the manual repair in "Repairing the store". Source: plan, Task 4.
- Deviation (Task 5): a stopped refetch ends with its own tail, not discover's tail. Source: plan, Task 5.
- Deviation (Task 7): `acquire --refetch` prints each `quarantined:` line on every exit, a stop and Ctrl-C included, and has no `changed:` line. Source: plan, Task 7.
- Deviation (Task 8): the manual repair's step 2 moves only the record files that step 1 found, and the artifact only if its bytes are damaged, not the whole `retrievals/<sha256>/` directory. Source: plan, Task 8.
- Deferred: 4 items. Source: specs/deferred_items.md, § 25-recover-unusable-saved-responses.

Closed earlier deferred items:
- "Recover a saved response that is present but unusable (PR #6's review, P2.1" (deferred by PR #6 review).

## /deferred — 2026-11-13

Closed deferred items:
- "Refuse a committed test-partition gold at validate time (T12-M1):" (deferred by 9-pilot-codebook-split-and-gold-set-protocol): `gold validate` refuses gold that `readable()` holds back, before its bundle loads.
- "Hold `codebook freeze --adr` to a repo-relative path under docs/adr/" (deferred by 9-pilot-codebook-split-and-gold-set-protocol): `--adr` must be a relative path under docs/adr/.
- "Take `codebook freeze`'s drafting aid from the kept draft (plan 10, P10-7;" (deferred by 10-harden-the-gold-before-bundle-4): `codebook freeze` takes the aid from the kept draft and refuses a missing one.
- "Harden the import scans (plan 12's review's M2-1, M9-3, M2-2, and M2-6;" (deferred by 12-evidence-selection-and-verification-plan-b): the scans resolve relative imports, name each retrieval hit's file, and match network modules by dotted name over a file floor.
- "Let earnings-themes' tests collect without httpx (plan 12's pre-flight F3;" (deferred by 12-evidence-selection-and-verification-plan-b): httpx imports are skipped when absent, and a test collects the themes tests with httpx blocked.
- "Keep a refused map key out of a field path (plan 12's review's M8-9;" (deferred by 12-evidence-selection-and-verification-plan-b): `describe` redacts any path part that names no field of the model.
- "**P16-4 — GS19 review Minors (quick-fix bundle).** From plan 16's task and final" (deferred by 16-pilot-codebook-split-and-gold-set-protocol): (2)–(6) fixed: four tests, two docstrings, and a no-event refusal that asks for dev bundles.
- "**P17-3 — `build_curated` returns early on a repeat, skipping `validate_curated`.**" (deferred by 17-feasibility-pilot-and-threshold-calibration-plan-a-slice-1): `build_curated` reports a kept-draft repeat with the record's refusals in one run.
- "**P17-4 — Plan 17 review Minors (quick-fix bundle).** None blocking: (1)" (deferred by 17-feasibility-pilot-and-threshold-calibration-plan-a-slice-1): (1)–(3), (4b), (4c), (5)–(7) fixed; (4a) and the `_PHRASES` guard dropped as the item allows.
- "**P18-1 — Say which hashes now cover a support run's cache mode.** Plan 18 added" (deferred by 18-feasibility-pilot-and-threshold-calibration-plan-a-slice-2): the data dictionary names the digests that cover `cache_mode` and `stability_run_id`.
- "**P18-2 — The scorer file's pinned-field list is not exhaustive.**" (deferred by 18-feasibility-pilot-and-threshold-calibration-plan-a-slice-2): the dictionary and `model_runtime` name every condition `_pinned` refuses.
- "Harden decide's memo against a policy that plants values under its private kind" (deferred by 23-run-path-performance): a missing row's `target_id` is copied before policy code runs.
