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

## 26-harden-ingestion-error-reporting-and-refusals — 2026-11-14
Plan: specs/plans/completed/26-harden-ingestion-error-reporting-and-refusals.md · Spec: none

Differences from the design:
- Ruling (Task 1): Task 1 finding 1 (multi-line Failed:) is a fix — the item's title reads "Report `browser setup`'s ordinary failures in one line" (specs/deferred_items.md:46), and httpx's raise_for_status message has 2-3 lines; print the first line only, so the plan test's single-line cases are unchanged — cost if wrong: a 302's "Redirect location" line is no longer printed (the first line still names the URL).
- Ruling (Task 2): Task 2 finding 2 (pydantic ValidationError prints unprefixed continuation lines) is a fix — specs/deferred_items.md:153 "Done when: each case has a test, and each ends as a `problem:` line or in `verify-live`'s record." — add `error_lines(error)` to apps/.../paths.py ("What a command prints"): one line per `ValidationError.errors()` entry ("<loc>: <msg>", loc dotted, omitted when empty), else the non-empty lines of str(error); `_build` prints `problem: <line>` for each; Task 8 reuses it for the events overrides loader — cost if wrong: one small helper more than the plan named.
- Ruling (Task 5): Task 5 concern 1 — test_events_acceptance.py::test_a_mismatch_is_named_and_leaves_the_convention_to_the_other_rows changes its input from None to a neither-convention value, and its None case moves to a new test with D2's outcome — plan Task 5 Step 3: "`survey` cross-checks only rows with a value (`filing.accepted_at is not None`). So a row with no value is never a mismatch" — cost if wrong: none; the test's intent (a mismatch is named) is kept.
- Ruling, contradicts spec (Task 5): Task 5 finding 4 (the floor counts a pre-window report that _visible judged invisible, so an older report the guards read is skipped) is a fix — specs/deferred_items.md:316 "A bound must keep the reports that the slots and their `period_gap` guards read, including the last one before the window (`events/slots.py`)." — compute the floor over pre-window original periodic reports whose visibility is not False (visible or unknown) — cost if wrong: none for v1 (no pre-window report accepted after the cutoff); the brief's "among the file's original periodic reports" is narrowed.
- Ruling (Task 6): Task 6 concern 1 (the new date check runs only when repeats() refused nothing) accepted — a filing listed in two files makes its page's dates reach the next page's filingFrom, and the repeat check already refuses it with the same remedy ("the submissions file with its older pages"); the existing one-problem tests test_events_filings.py:570 and test_events_discover.py:528 stay unchanged — cost if wrong: a shifted page shows only after the repeat is fixed (the build is refused either way).
- Ruling (Task 7): Task 7 concern 1 (retrieved_at must match a retrieval of the cited URL, not any retrieval of the bytes) accepted — the item's title is "Bind each evidence citation to its artifact's retrievals", and `_citations_refused` in events/build.py already checks the cited URL's own retrievals — cost if wrong: Task 10's real-store check fails if a v1 citation took its time from another URL's retrieval of the same bytes.
- Ruling (Task 7): Task 7 concern 2 (test_a_cited_artifact_that_cannot_be_read_names_a_remedy_that_works and test_a_cited_artifact_whose_bytes_are_gone_names_a_remedy move to a copy of the committed synthetic store; assertions unchanged) accepted — a store discovery filled carries the run's retrieval times, which the new check refuses by design — cost if wrong: none.
- Ruling (Task 8): Task 8 concern 1 (djia-events.md "Repairing the store" bullet (a): the new sentence replaces three now-false sentences instead of being added) accepted — leaving "names no file" beside the new sentence would contradict it — cost if wrong: none.
- Ruling (Task 9): Task 9 concern 1 (test_events_cli.py::test_discover_prints_its_count_when_a_saved_body_is_gone replaced in place by the plan test test_discover_handles_a_vanished_companyfacts_artifact, same input) accepted — specs/deferred_items.md:529 "discovery ... skips that issuer, and reports it after the documents phase; ... and a vanished companyfacts artifact ends as a handled stop with the count printed" replaces the old "Stopped: no artifact ... a rerun fetches only what is missing" — cost if wrong: none; SystemExit and the count are still asserted.
- Ruling (Task 9): Task 9 concern 3 (issuer_companyfacts and discover_filing's index read report a record that turns unreadable after SavedResponses loads it as a refetch problem) stays out — it predates this task and belongs to "Name a damaged retrieval record instead of stopping every reader" (deferred_items.md:1342, not in scope) — NOTE for that item at completion.
- Ruling: owner chose "Fix it here" (2026-11-14) for the replay-test candidate. Out-of-plan fix dispatched from BASE 40206fd under fix-replay-brief.md (sonnet implementer); one file, tests/integration/test_event_store_v1.py. No mutant run: the test skips without data/; the owner's rerun of that test is the evidence. Plan 26 Steps 3-4 treated as passed apart from this pre-existing failure.
- Deviation (Task 1): `Failed:` prints only the first line of the error. Source: plan, Task 1.
- Deviation (Task 2): a new helper, `error_lines(error)`, prints one `problem:` line for each pydantic error entry. Source: plan, Task 2.
- Deviation (Task 5): one acceptance test takes a neither-convention value, and its None case moves to a new test. Source: plan, Task 5.
- Deviation (Task 5): the floor counts only pre-window reports whose visibility is not False. Source: plan, Task 5.
- Deviation (Task 6): the page-date check runs only when the repeat check refused nothing. Source: plan, Task 6.
- Deviation (Task 7): `retrieved_at` binds to a retrieval of the cited URL. Source: plan, Task 7.
- Deviation (Task 8): the new sentence in "Repairing the store" replaces three that it made false. Source: plan, Task 8.
- Deviation (Task 9): one CLI test is replaced in place by the plan test. Source: plan, Task 9.
- Deviation (Task 10): commit `04723a8` fixes an older replay test that failed the root suite, and only its file was run again. Source: plan, Task 10.
- Decision D2 (spec amendment): Item L541 takes reading (a): a missing `acceptanceDateTime` has nothing to cross-check. The saved index page's Accepted value places the filing, and its cross-check is null. This is the owner's ruling in the `/deferred` pass. It widens the carried item "Cite the index page that places a periodic report" (PR #6 review (plan 7)) to rows with no value, which v1 does not have. Source: plan, `## Decisions`.
- Decision D3 (spec amendment): Item L979 is per-issuer: two cohort issuers' events may share one co-registrant release. Only two events of one issuer may not. This is the owner's ruling in the `/deferred` pass. Source: plan, `## Decisions`.
- Deferred: 7 items. Source: specs/deferred_items.md, § 26-harden-ingestion-error-reporting-and-refusals.

Closed earlier deferred items:
- "Report `browser setup`'s ordinary failures in one line (final review," (deferred by 5-structure-aware-canonicalization).
- "Three small robustness fixes (final review, Minor #6):" (deferred by 5-structure-aware-canonicalization).
- "Four stale claims (final review, Minor; paths under" (deferred by 6-point-in-time-djia-cohort).
- "Report the cohort CLI's override and terms errors as `problem:` lines" (deferred by 7-event-discovery-eligibility-and-acquisition-plan-a).
- "Show the operative hashes in `verify-live` (plan 7, P7-3): plan 7's Task" (deferred by 7-event-discovery-eligibility-and-acquisition-plan-a).
- "Report `events freeze`'s citation errors as `problem:` lines (plan 7's" (deferred by 7-event-discovery-eligibility-and-acquisition-plan-a).
- "Bound the periodic reports that can block on acceptance time (plan 7's" (deferred by 7-event-discovery-eligibility-and-acquisition-plan-a).
- "Refuse a repeated acknowledgement (plan 7's final review, Minor):" (deferred by 7-event-discovery-eligibility-and-acquisition-plan-a).
- "Bind each evidence citation to its artifact's retrievals (PR #6's review," (deferred by PR #6 review).
- "Bind older submissions pages to their dates, and pad the page skip (PR #6's" (deferred by PR #6 review).
- "Refuse two findings that share one `finding_id` (PR #6's review, P4.3):" (deferred by PR #6 review).
- "Read companyfacts in discovery through the problem-collecting reader (PR" (deferred by PR #6 review).
- "Refuse a fund filing listed twice in the cohort build (PR #6's review," (deferred by PR #6 review).
- "Decide whether two issuers' events may share one release (PR #6's review" (deferred by PR #6 review).
- "Print a `quarantined:` line when a plain save moves damaged bytes aside (plan" (deferred by 25-recover-unusable-saved-responses).
