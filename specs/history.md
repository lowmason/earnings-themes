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
