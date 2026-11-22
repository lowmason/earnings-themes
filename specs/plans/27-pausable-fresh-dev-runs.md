# Pausable Fresh Dev Runs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the owner stop a fresh dev run (`pilot21 run --partition dev --fresh <id>`) and resume it under the same ID with `--resume`, with the coding request ceiling counted as in an uninterrupted run.

**Architecture:** Two small code changes and no record change. (1) In fresh mode, the coding cache marks the first read in a process of a reply that an earlier process wrote, and `_attempt` charges that reply to the allowance and records it as a dispatched row, as the uninterrupted run did. (2) The application relaxes the one guard in `make_pass` that refuses an existing fresh run, behind an explicit `--resume` option, and lets `make_run` resume at the record stage. D21-36 rejected counting cached requests for a *replay*. This plan does it for *fresh* mode only, where a stored reply is the run's own earlier dispatch.

**Tech Stack:** Python 3.14.0, pydantic, Typer, pytest; uv workspace (`earnings-themes`, `earnings-pipeline`).

**Spec:** `specs/feasibility-pilot-and-threshold-calibration.md` (FP11, FP12, §Failure handling; amended in Task 4). The requirements are D21-38 in `specs/plans/21-feasibility-pilot-and-threshold-calibration-plan-b.md`. Read it first: it holds the owner's four answers, the nine rules and the evidence.

## Global Constraints

- No cache key, record shape, Parquet table, hash, `configuration_hash`, version string or stored-run validator changes (D21-38). The train cache (about 107 GB) and the dev caches must replay byte for byte. The pinned key digests and output hashes from plan 23 and the existing replay tests pass unchanged after every task.
- Live and replay modes behave exactly as before. Every existing test passes unchanged, except the one renamed in Task 2 (its assertions stay). If another existing test fails, stop and report its name. Do not edit, skip or loosen it.
- Invented fixtures only (GS13). No agent opens `data/`, a pilot view, a working file or a cache entry under `data/`. No agent runs the root suite, the Stage 6 wording gate, browser tests, `-m live` or the `root-user` modes. No agent runs a real pilot command or starts a model server.
- Every pilot command refuses `input_changed` off the pinned lockfile `e2f8ec4d2ba556a51f30d8dcf9a3b122af4aaa5ed87ca4dc030b91e1930ddc16`, and this worktree's `uv.lock` differs. Run only the targeted invented-input tests listed in Task 5. Do not edit `uv.lock` or `pyproject.toml`.
- Failing test first in every code task. Run it, see it fail for the stated reason, and commit the failing tests alone before the implementation commit.
- Only closed reasons leave the application. No free text, traceback or model reply is printed.
- Extraction and support ceilings stay per process (D21-38 rule 4). Concurrent workers stay barred (Stage 15).
- Write docs in plain technical English (see `rules/write-with-asd-ste100.md`). Do not edit `CLAUDE.md` without the owner's yes.

## Review Focus

Inputs and failures the spec implies, most likely first. Each has a test in the task named.

1. A stop leaves debris (a `.support-*` or `.coding-*` temporary directory beside a phase directory, `*.partial` files in a cache directory). The resume must ignore it and finish (Task 2).
2. A typo in the ID, or `--resume` on an ID with no state. It must refuse. It must never start a new run silently (Task 2).
3. A second stop after a resume, in another phase. The run still finishes with the same result as an uninterrupted run (Task 2).
4. A pause after a document was cut. The resumed run keeps the same cut claims (Task 1).
5. A stop between publishing `run/coding` and writing `run-record.json`. The resume finishes. A `run/coding` made under another calibration refuses `input_changed` (Task 3).
6. A stop prints one closed line and exits 130, with no traceback on the Terminal panel. This holds mid-run, at the operator checkpoint prompt (`typer.Abort`) and before any state exists (Task 2).
7. A stop while a phase directory is being published (extraction, coding or support). It leaves no partial phase directory, and the resume finishes (Task 2, case `extraction_write`; the writers' own `BaseException` handling is verified by reading, not by a new test).

## Decisions

- **D21-38** (owner, plan 21, 2026-11-22): pausable fresh dev runs, nine rules, as recorded in plan 21. Applied in: Global Constraints and Tasks 1 to 5.
- **D27-1** (controller ruling, planning, 2026-11-22, for the owner's review of this plan): the first read of a carried reply is charged in `_attempt` through a new `CodingCache.consume_carried`, not in `propose_run`. Reason: `_attempt` already holds the request, the cache entry and the allowance, and `propose_run` would have to rebuild all three. Applied in: Task 1.
- **D27-2** (controller ruling, planning, 2026-11-22, for the owner's review of this plan): the "no `run-record.json`" check lives in `run_command`, not `make_pass`, because only `run_command` knows the run directory. Applied in: Task 2.

---

### Task 1: Charge a run's own earlier coding replies

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/coding/cache.py` (`CodingCache`: `__init__`, `put`, new method)
- Modify: `packages/earnings-themes/src/earnings_themes/coding/classify.py` (`_attempt`, the `entry is not None` branch, about lines 277-282)
- Modify: `packages/earnings-themes/tests/coding/cases.py` (`make_proposal_job.script`: raise a `BaseException` value, so a test can inject `KeyboardInterrupt()` into the reply queue)
- Test: `packages/earnings-themes/tests/coding/test_carried_charge.py` (new)

**Interfaces:**
- Consumes: `coding_key(request, identity) -> str` (`coding/cache.py`), `CodingAllowance.reserve(doc_id, claim_id, input_tokens, max_output) -> int` and `.reconcile(doc_id, reserved, usage)` (`coding/classify.py:69,102`), `make_proposal_job(sources, policy, identity, root).run(replies, cache_mode, *, ceilings, claim_order, stability_run_id, directory)` (`tests/coding/cases.py:154`), `make_sources(..., claim_texts=, other_bundles=)`.
- Produces: `CodingCache.consume_carried(self, key: str) -> bool`. It returns True at most once per key per cache instance, and only when `mode == "fresh"` and this instance has not itself written (`put`) or already consumed the key. It returns False in every other case. `_attempt` calls it only on a cache hit.

- [ ] **Step 1: Write the failing tests** in `test_carried_charge.py`. Use five claims in one document and a second document of five claims (`claim_texts` of length 5, one `other_bundles`), reply `{"theme_ids": ["capacity"], "attributes": {}}`.

```python
def test_resumed_fresh_run_records_the_same_rows_and_totals_as_an_uninterrupted_run(job, tmp_path):
    # 4 claims, ceilings roomy. A = uninterrupted fresh run, id "a".
    # B = first process raises KeyboardInterrupt() on its 3rd reply, second process finishes, id "b".
    assert calls_in_second_process == 2
    assert B.attempts == A.attempts
    assert (B.record.requests, B.record.cache_hits, B.record.reserved_tokens,
            B.record.charged_tokens, B.record.latency_ms) == (4, 0, *same_as_A)
    assert B.classifications == A.classifications and B.proposals == A.proposals
    # If the scripted adapter measures wall time, drop the latency comparison only.

def test_a_pause_after_a_cut_keeps_the_cut_set(job, tmp_path):
    # two documents of 5 claims, requests_per_document=3: each document cuts 2 claims.
    # Interrupt on the 4th reply (first claim of document 2), then resume.
    cut = lambda run: [(c.doc_id, c.claim_id) for c in run.classifications
                       if c.reason == "requests_exhausted"]
    assert cut(B) == cut(A) and len(cut(A)) == 4
    assert B.record.requests == A.record.requests == 6

def test_consume_carried_is_true_once_for_a_reply_an_earlier_process_wrote(job, tmp_path):
    # populate fresh/s-1 with one run; open a NEW CodingCache(root, "fresh", stability_run_id="s-1")
    assert cache.consume_carried(key) is True
    assert cache.consume_carried(key) is False          # duplicate-key hit: not charged
    # a key this instance put() itself: False. mode "live" and "replay": always False.

def test_live_and_replay_hits_stay_cached_and_uncharged(job):
    # live run twice over one directory: second run has requests == 0 and every row cached
    # with reserved_tokens == 0. A replay over it does the same.

def test_a_carried_reply_that_no_longer_fits_a_ceiling_is_cut_not_a_crash(job):
    # fresh run with requests_per_document=3 over 3 claims; resume the same ID with
    # requests_per_document=1: claim 1 is carried and charged; claims 2 and 3 end
    # "requests_exhausted" with cached False, reserved_tokens 0 and raw_ref None.
```

- [ ] **Step 2: Run the tests and see them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/coding/test_carried_charge.py -m "not live and not browser" -q`
Expected: FAIL. The first two fail because the resumed run dispatches differently (rows are `cached=True` and the cut claims get dispatched). The third and fifth fail with `AttributeError` on `consume_carried` or a wrong row. The fourth already passes. Commit the tests alone: `test(coding): pin the charge of a fresh run's own earlier replies (D21-38)`.

- [ ] **Step 3: Implement `CodingCache.consume_carried`** in `coding/cache.py`. Keep an in-memory `self._seen: set[str]` per instance. `put` adds its key. `consume_carried` returns False unless `self.mode == "fresh"` and the key is new to `_seen`, then adds it. It reads no file and writes none.

- [ ] **Step 4: Change `_attempt`'s hit branch** in `coding/classify.py`. When `cache.consume_carried(coding_key(request, identity))` is true, follow the dispatch path's accounting with the stored reply instead of calling the classifier: `tokens = entry.input_tokens`, `reserved = allowance.reserve(input.doc_id, input.claim_id, tokens, request.parameters.max_tokens)`, then `allowance.reconcile(input.doc_id, reserved, raw.usage)` in a `finally`. The row has `cached=False`, `reserved_tokens=reserved`, `latency_ms=raw.latency_ms`, and the existing `raw_ref`, `raw_hash` and `unreported` formulas. If `reserve` raises `requests_exhausted` or `tokens_exhausted`, the existing `except CodingError` path must give a row with `cached=False`, `reserved_tokens=0`, `raw_ref=None`, `raw_hash=None`, so `coding/store.py::_check_accounting` still accepts it. Every other hit stays as it is (cached, not charged).

- [ ] **Step 5: Run the tests and the package suite**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/coding -m "not live and not browser" -q`
Expected: PASS, with no change to any pinned digest or hash test.

- [ ] **Step 6: Commit** the implementation: `feat(coding): charge a fresh run's own earlier replies to the ceiling (D21-38)`.

### Task 2: `--resume` in `make_pass` and `run_command`

**Files:**
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/pilot_workflow.py` (`make_pass`, the `state_run_conflict` block, about lines 335-346)
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/pilot_commands.py` (`run_command`, about lines 203-247)
- Test: `apps/earnings-pipeline/tests/test_pilot_workflow.py`, `apps/earnings-pipeline/tests/test_pilot_commands.py`

**Interfaces:**
- Consumes: Task 1's behavior (a resumed fresh pass charges its own replies), `make_pass`, `load_pass`, `processed`, `WorkflowError` closed reasons (`state_run_conflict`, `malformed_record`, `input_changed`).
- Produces: `make_pass(config, runtime, alternative, *, partition, directory, fresh, support_ready, now, resume: bool = False) -> PassRecord`. `fresh_state_exists(config: WorkflowConfig, directory: Path, fresh: str) -> bool` in `pilot_workflow.py`: True when the pass directory or any of the three `fresh/<id>` cache directories exists. `make_pass` and `run_command` share it. `run_command` gains `resume: Annotated[bool, typer.Option("--resume")] = False`. The two closed stop lines are `Stopped: rerun the same command with --resume` (state exists) and `Stopped before any state was written: rerun the same command` (no state).

Rules, from D21-38 rule 2. In `make_pass`: `resume` with `fresh is None` or a non-dev partition raises `malformed_record`. Without `resume`, existing state still raises `state_run_conflict`. With `resume`, no state raises `malformed_record` (nothing to resume), and otherwise the run goes on through the existing flow, which already skips a finished phase and reads a finished `pass.json`. In `run_command`: `--resume` without `--fresh` or off dev raises `RecordError("fresh", ("wrong_partition",))` before intake, as today's checks do. With `--resume` and an existing `fresh/<id>/run/run-record.json`, it raises `WorkflowError("state_run_conflict")`. For a fresh run, both `KeyboardInterrupt` and `typer.Abort` are caught (`typer.confirm` at the operator checkpoint turns SIGINT into `Abort`). The command prints one of the two stop lines to stderr, chosen by `fresh_state_exists`, and exits with status 130 (`typer.Exit(130)`). A non-fresh run is unchanged. `bind_policy` still runs before `make_pass` (FP12). The tests raise `KeyboardInterrupt` and resume inside one pytest process, but production resumes in a new process. If a resume test fails on leftover `earnings_themes.scope` state, treat it as a real cleanup bug, not a test artifact.

- [ ] **Step 1: Write the failing tests.**

In `test_pilot_workflow.py` (reuse `seed_case`, `runtime`, `coding_cases.make_support_parts`; inject a stop by a callable that raises `KeyboardInterrupt()` on its Nth call):
- Rename `test_fresh_directory_is_never_resumed_and_main_caches_survive` to `test_fresh_directory_without_resume_refuses_and_main_caches_survive`. Keep every assertion.
- `test_resume_matches_an_uninterrupted_run_after_a_stop` parametrized over `stop in ("extraction", "extraction_write", "classification", "after_proposals", "support", "alternative")`. `after_proposals` raises from `support_ready`. `extraction_write` monkeypatches `earnings_themes.extraction.store.os.rename` to raise `KeyboardInterrupt` once (`write_run` removes its temporary directory in a `finally`, so no `extraction/` exists afterwards). Assert: the resumed pass is `complete`; `processed(load_pass(...))` is True; its classification IDs and statuses, target IDs and outcome statuses equal a reference fresh run under another ID; the second process dispatches only what the first did not (count calls); the three main caches are byte-identical afterwards.
- `test_two_stops_then_a_resume_finish_the_run` (stop in classification, resume, stop in support, resume).
- `test_resume_with_no_state_refuses_and_dispatches_nothing` (`malformed_record`, zero calls).
- `test_resume_ignores_debris_from_a_hard_stop`: after a stop in support, create `.extraction-debris`, `.coding-debris` and `.support-debris` directories beside the phase directories and a `<64 hex>.x.partial` file in each of the three fresh cache directories, then resume and finish.
- `test_resume_without_fresh_or_off_dev_refuses_malformed_record`.

In `test_pilot_commands.py` (extend the parametrized fresh test at about line 197 with `resume`):
- the order `bind, live, pass, load, check, run` holds with `--resume`, and `make_pass` receives `resume=True`;
- `--resume` without `--fresh` and `--resume` on train refuse before intake, naming `fresh`;
- `--resume` over an existing `run-record.json` prints `Refused: configuration: state_run_conflict`;
- `test_a_stop_prints_one_closed_line_and_exits_130`, three cases: `make_pass` raises `KeyboardInterrupt` after it created state (the `--resume` line); `support_checkpoint` raises `typer.Abort` (the `--resume` line); `intake` raises `KeyboardInterrupt` before any state exists (the no-state line, which does not mention `--resume`). Assert exit code 130, the one closed line, and no `Traceback` in the output.

- [ ] **Step 2: Run the tests and see them fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_pilot_workflow.py apps/earnings-pipeline/tests/test_pilot_commands.py -m "not live and not browser" -q`
Expected: FAIL (`make_pass` and `run_command` take no `resume`; a resume refuses `state_run_conflict`). Commit the tests alone: `test(pilot): pin pause and resume of a fresh dev run (D21-38)`.

- [ ] **Step 3: Implement** the `make_pass` guard and the `run_command` option, the `run-record.json` check and the stop line, as the rules above state. Do not touch any other check in either function.

- [ ] **Step 4: Run the tests** (command of Step 2).
Expected: PASS.

- [ ] **Step 5: Commit**: `feat(pilot): resume a stopped fresh dev run under its own ID (D21-38)`.

### Task 3: Resume at the record stage

**Files:**
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/pilot_workflow.py` (`make_run`, the `fresh is not None` branch, about lines 620-624)
- Test: `apps/earnings-pipeline/tests/test_pilot_workflow.py`

**Interfaces:**
- Consumes: `finalize_coding(proposal, support, sources, policy) -> CodingRun`, `write_coding_run`, `read_coding_run(directory) -> CodingRun`, `reverify_coding_run(stored, sources, support, policy)` (`coding/store.py:733`).
- Produces: in a fresh run, when `run/coding` already exists, `make_run` reads it back with `read_coding_run` and calls `reverify_coding_run` on it. This is the consuming gate that `write_coding_run` runs before it publishes (D21-34), so the read-back path must not skip it. It then compares the read-back run with `finalize_coding`'s result: equal tables, and an equal record once the `*.parquet` entries are removed from each `artifact_hashes` (the `raw/...` hashes stay in the comparison). Any difference raises `WorkflowError("input_changed")`. It then skips `write_coding_run` and writes `run-record.json` as usual. A missing `run/coding` is written as today.

- [ ] **Step 1: Write the failing tests.**
- `test_a_stop_after_coding_is_published_resumes_to_the_same_record`: make the `write_new` of `run-record.json` raise `KeyboardInterrupt` once (monkeypatch), call `make_run` again, and assert the `RunRecord` equals the record of a clean run (reuse the `seed_case` and `bound_artifact` helpers at `test_pilot_workflow.py:338-381`).
- `test_a_published_coding_run_from_another_policy_refuses_input_changed`: publish with `bound_artifact(..., none=False)`, then call `make_run` with the `none=True` artifact; expect `input_changed`, and no `run-record.json`.
- `test_the_read_back_path_runs_the_consuming_gate`: spy on `reverify_coding_run` (import it into `pilot_workflow`); a resume over a published `run/coding` calls it once.

- [ ] **Step 2: Run them and see them fail**
Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_pilot_workflow.py -k "stop_after_coding or another_policy" -q`
Expected: FAIL with `FileExistsError: coding_destination_exists` (the first) and no refusal (the second). Commit alone: `test(pilot): pin resume at the record stage (D21-38)`.

- [ ] **Step 3: Implement** the read-back and comparison in `make_run`'s fresh branch. Leave the non-fresh branch unchanged.

- [ ] **Step 4: Run the tests** (Step 2's command, then the whole file).
Expected: PASS.

- [ ] **Step 5: Commit**: `feat(pilot): resume a fresh run at the record stage (D21-38)`.

### Task 4: Spec, docstring and verification-record amendments

**Files:**
- Modify: `specs/feasibility-pilot-and-threshold-calibration.md` (lines 60, 139, 143, 358)
- Modify: `packages/earnings-themes/src/earnings_themes/extraction/cache.py` (docstring lines 12-13 and 100-102)
- Modify: `docs/verification/pilot-v1-feasibility.md` (new section at the end)
- Modify: `specs/plans/21-feasibility-pilot-and-threshold-calibration-plan-b.md` (Status line: append ` B7 waits for plan 27's code (D21-38).`)

Spec amendments. The existing tags read "Amended by the user", so these match. The owner approves this wording at plan review. Append each sentence to the end of its line, after the existing amendment tag:

- FP11 (line 60): *(Amended by the user, plan 27, 2026-11-22: a stopped run may resume under its own ID with `--resume`, D21-38. A resumed run reads only its own directory.)*
- Line 139: *(Amended by the user, plan 27, 2026-11-22: the directory starts empty at a first start. `--resume` is the one way to start on a non-empty directory of the same ID. A reply that an earlier process of the run wrote is charged once to the coding allowance and recorded as a dispatched row, so a resumed run's coding counters equal an uninterrupted run's, D21-38.)*
- Line 143: *(Amended by the user, plan 27, 2026-11-22: the zero-hit statement holds for a run that never resumed. In a resumed run, extraction and support hits may be the run's own earlier replies.)*
- Line 358 (the "A fresh run crashes" row): *(Amended by the user, plan 27, 2026-11-22: a stopped run may resume under its own ID. A run that cannot finish after a resume, or is `processed no`, is discarded and its ID stays burned, D21-38.)*

The same wording, shortened, replaces the two docstring passages in `extraction/cache.py` (they say a fresh directory "must start empty" and that A8 "refuses an existing ID"). Add that `--resume` is the exception and that nothing in `cache_directory` checks it.

- [ ] **Step 1:** Apply the four spec edits, the docstring edit and the Status-line edit.
- [ ] **Step 2:** Add the section `## Pausing and resuming fresh dev runs (D21-38)` to the verification record. It holds, in plain English: the pause procedure (rule 1), the resume command (rule 2), the operator rules (rule 7), and an empty table with the columns `run ID | stop (UTC) | phase | cause | cache files at resume (extraction / coding / support) | git SHA before / after | resume wall time`, plus a line per run for the claims cut by document. The procedure also names the cleanest pause: answer `N` at the operator checkpoint, right after `proposals.json` is sealed. That prints a `Refused: configuration: malformed_record` line, and a rerun with `--resume` does not refuse again. No result goes in it yet.
- [ ] **Step 3:** Run `uv run --locked ruff check .` and `uv run --locked ruff format --check .`.
Expected: no findings.
- [ ] **Step 4: Commit**: `docs(pilot): amend the fresh-run rules for pause and resume (D21-38)`.

### Task 5: Targeted checks, owner gates and landing

**Files:** none changed. Evidence goes in the verification record's new section.

- [ ] **Step 1: The agent runs the targeted invented-input checks.**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/coding apps/earnings-pipeline/tests/test_pilot_workflow.py apps/earnings-pipeline/tests/test_pilot_commands.py apps/earnings-pipeline/tests/test_pilot_run_bytes.py -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: all pass. State exactly which commands ran.

- [ ] **Step 2: The owner runs the gates** in their own terminal, as for plans 23 and 24: the root suite and the Stage 6 wording gate. Agents do not run them. Record the owner's counts and the commit SHA they ran at.

- [ ] **Step 3: Open the PR** and follow the pull-request lifecycle rule. The PR holds the plan-only commit, the RED test commits and the implementation commits.

- [ ] **Step 4: Land on the owner's checkout (the owner's yes first).** Every pilot command refuses off the pinned lock, and `origin/main`'s `uv.lock` is not the pin, so the merge alone gives the owner nothing to run. After the merge:
  1. Check that the files this plan changed did not move on `main` since the base of `data/dev-labels`: `git diff --stat 81d09b9 <the PR's first parent> -- packages/earnings-themes/src/earnings_themes/coding packages/earnings-themes/src/earnings_themes/extraction/cache.py packages/earnings-themes/tests/coding apps/earnings-pipeline/src/earnings_pipeline/pilot_workflow.py apps/earnings-pipeline/src/earnings_pipeline/pilot_commands.py apps/earnings-pipeline/tests/test_pilot_workflow.py apps/earnings-pipeline/tests/test_pilot_commands.py apps/earnings-pipeline/tests/test_pilot_run_bytes.py`. It was empty on 2026-11-22 at `dfc336b`. If it is not empty at the merge, stop and report: the cherry-pick may conflict, and that changes how B7 gets the code.
  2. With the owner's yes, cherry-pick this plan's code and test commits (not the docs commits) onto `data/dev-labels` in the main checkout. Never touch `uv.lock` or `pyproject.toml`. Never `uv sync` or `git switch` while a run is active.
  3. Check that `uv.lock` still hashes to `e2f8ec4d2ba556a51f30d8dcf9a3b122af4aaa5ed87ca4dc030b91e1930ddc16`.
  4. The owner runs the targeted test command of Step 1 in the main checkout on `data/dev-labels`, when no run is active. That checkout's base differs from the one the gates ran on. Record the counts.
  5. Record the merge SHA and the cherry-picked SHA in the verification record. The cherry-picked SHA is the "code SHA" that D21-38 rule 6 compares across a run's segments.
- [ ] **Step 5:** Follow the plan completion protocol. Note for the next session: B7 may now start. Its first real pause and resume is B7's evidence, timed and recorded (D21-38 rule 7).

## Self-review

- **Spec coverage.** D21-38 rule 1 and 7: Task 4 (procedure) and the handoff brief. Rule 2: Tasks 2 and 3. Rule 3: Task 2 (tests for any stop). Rule 4: Task 1. Rule 5: Task 2 (main caches untouched) and Task 4. Rule 6: Task 4 (table). Rule 8: Task 2. Rule 9: Task 5.
- **Types.** `consume_carried`, `resume`, `make_pass`, `run_command`, and the closed line use the same names in every task.
- **Proportion.** About 3,000 words, against D21-38's 900. The tests carry the detail.
