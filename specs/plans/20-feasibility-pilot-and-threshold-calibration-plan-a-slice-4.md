**Status: COMPLETE (2026-10-13)** — executed via subagent-driven-development; nothing deferred

# Stage 11 Plan A, Slice 4: Pilot Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development. Execute in a fresh GPT-6.1 Medium session and a fresh worktree. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish plan A with A8's pilot commands, A9's dictionary rows for their new records, and the deferred boundary fixes those commands need, using invented inputs only.

**Architecture:** The existing `pilot` group delegates to focused application modules for intake, local checkpoints, passes and replay, labels, calibration, and reports. The application composes the existing Stage 7–9 libraries and the pure evaluation package; shared configuration and validation helpers are extracted once and consumed by both the workflow and pilot commands. Local pass records separate extraction, classification, and the two support phases from frozen-policy decisions.

**Tech Stack:** Python 3.14.0, the existing uv workspace, Pydantic v2 strict frozen records, the standard library, pytest, Ruff. No new dependency or lockfile update.

**Spec:** `specs/feasibility-pilot-and-threshold-calibration.md`, approved 2026-10-11 and amended by plans 18 and 19. Read the live spec at `50158620670007ead8d8773f7028c9a977a8a190`, and `specs/plans/completed/19-feasibility-pilot-and-threshold-calibration-plan-a-slice-3.md`, especially Global Constraints and Handoffs H1–H16. This plan implements A8 and only A9's dictionary work owed by A8. Plan 17 already shipped A9's wording globs.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 11 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

**This is plan A's last slice.** The spec's Rollout overrides the generic roadmap completion instruction: this plan appends `Plan A: COMPLETE`, retires only this plan, and leaves Stage 11 unticked and the shared spec live. Plan B supplies Stage 11's output and retires the spec. B1 and B2 may start after plan A merges; B3 waits for the visibility gate. This document does not plan or execute plan B.

**Starting point:** Main at `5015862`, PR #23 merged 2026-10-13, clean, with no live plan. Writing-plans' `entry_check.py` allocated **20** after scanning branches, refs, and worktrees. Execution starts from the commit containing this approved plan; the code patches below are against the implementation baseline `5015862` and are applied in task order.

## Global Constraints

- **GS13 and GS3, blinding and repository contents.** Never open pilot text, a kept draft, anything in the main checkout's `data/`, or existing files under `data/runs/gold/` or `data/runs/pilot/`. Execute in a fresh worktree with no inherited data. Tests may create invented records in a temporary directory bearing those names; they never read the real directories. Every command prints only IDs, counts, closed reasons and figures. No quote, claim, context, definition, raw model reply, untrusted exception message or input excerpt is printed. Each A8 command, `pilot recount`, and coverage v2 receives an invented-input marker sentinel.
- **No runtime or network during implementation.** Never load a model, tokenizer, scorer or NLI runtime. Do not call `build_runtime` with native components or send a request. Tests use invented records, synthetic metadata, scripted adapters and injected callbacks. The current owner's invented-fixtures-only scope is tighter than plan 19's old Stage 1 fixture allowance. Never run live, browser or user-only modes, including `-m live` and `-m browser`.
- **Tracebacks.** Use `--tb=short -q`. Never pass `--tb=long`, `--tb=auto`, `--full-trace`, `-l`, `--showlocals`, `--pdb`, or `-vv`. A failing user gate is reported by test name and reason only.
- **User gates.** Agents never execute `pytest packages apps tests`, `tests/integration/test_stage6_wording.py`, `tests/integration/test_stage6_pilot_v1.py`, browser tests or user-only tests. Root collection with `--collect-only -q` is explicitly allowed for the selected-count prediction. Task 13 hands the actual reviewed commit SHA to the user, who runs the gates in the main checkout after `git switch --detach <sha>`. The last user gate at `eccb77c` gave 4719 passed, 2 skipped and 28 deselected; this is historical evidence, not an expected count for execution.
- **Protected files.** Do not edit `CLAUDE.md`, `AGENTS.md`, the roadmap, or `tests/integration/test_stage6_wording.py`. At completion, prepare a concrete `CLAUDE.md` Current state diff and request the user's approval before applying it. Approval of this implementation plan does not approve that later diff.
- **TDD and exact code.** Write each task's tests before its implementation and observe the stated failure. Tests characterizing already-correct behavior may pass during the red step; do not manufacture a failure. Apply the complete code below. If it fails as written, report the finding and resolve it with review, rather than silently improvising around it. Report actual test counts; review fixes make numeric expectations stale.
- **D18-1, no copied domain logic.** Extract or call the existing helper. `coding_configuration`, `source_bindings`, `validate_proposal_support`, the workflow's configuration hashes and policy-reference validation, `support.records.support_configuration`, and Stage 6's shared selectors each have one implementation. Do not copy `theme_workflow.py`'s hash blocks or recreate Stage 8/9 policy logic in the application.
- **D19-4 and GS17, imports and units.** Themes depends on core; themes and ingestion do not import each other. `evaluation` imports core and pure themes Stage 7–9 modules, never ingestion, httpx, a concrete adapter, `support.nli`, an NLI runtime, `extraction.local`, or `coding.local`. No gold-drafting module imports evaluation. Application modules compose the packages. Keep Python half-open character offsets and pointer-traversal/1 evidence units. Run the import-boundary and import-scan checks with the scoped verification command.
- **Refusals.** Identify the item by ID or field path, with a closed reason, never its text. Preserve the existing distinct error contracts: `EvaluationError`/`EvaluationProblem`, `CodingError`, Pydantic validation failures, and `RecordError` for unreadable or incorrectly hashed committed records. The shared hash primitive does not erase those error types. At a command boundary, unexpected exception text is withheld because it can contain source wording.
- **FP2 and partition safety.** Before any pilot source can be loaded, verify the full pinned train/dev inventory and visibility gate: 20 train events, 8 dev events, all 28 signed gold files and the 8 dev ledger rows. Re-derive the split from the pinned issuer-time rule; a self-sealed reduced split cannot lower the gate. Reject test and excluded partitions before reading their documents. Bind source documents and codebook to the signed gold and pinned split, rather than trusting a valid hash alone.
- **FP7 and FP22, phases.** Use the shipped prompts and baseline configuration. Run all extraction, then all classification, then MiniCheck support and DeBERTa support. Gemma must be unloaded before support; both judges and MiniCheck remain resident together, as B1 verifies within 36 GB. The counts-only operator checkpoint implements that lifecycle boundary without adding a server-management framework. No pass writes decisions or Stage 5 state.
- **FP23, ordinary replay.** Reuse only the live pass's stored extraction run. Replay coding and support into new runs under the calibrated policy; do not reuse the pass's stored coding or support run, and do not re-extract. Refuse every cache miss before workflow publication or state changes. A fresh run is never reused by ordinary `pilot run`. Workflow stored-coding reuse remains replay-only.
- **FP11/FP12, stability and failures.** A fresh dev run uses its own new `cache/fresh/<id>/` directory for all four reply kinds. It never reads or overwrites main cache bytes. Reject an already used fresh ID; after a crash, use a new ID and retain the partial attempt's provenance. Partial runs remain visible and never count toward k = 3. The three complete fresh runs must have distinct IDs, the exact dev event inventory, the same frozen baseline and the same settings. Temperature-0 stability measures runtime nondeterminism; do not present it as sampled-temperature robustness.
- **H1–H3 and H9, label and calibration inputs.** Reverify support before building the pool or local contextual view; its target/outcome uniqueness and order are tested. Run `check_labels` before `merge_labels`. Hash the exact committed label bytes that were parsed. Validate extraction/support source-run bindings and proposal/support coherence with the extracted Stage 9 gate before constructing the frozen configuration or decision views.
- **H4–H6, frozen policy.** The application owns the checked calibration JSON reader and recomputes the public `configuration_hash` before binding a policy or running the workflow. Handle only `EvaluationProblem.NO_CANDIDATE` as the all-review feasibility result. A corrupt artifact, wrong hash or another evaluation failure must refuse and cannot become `no_candidate`.
- **H7, workflow seam.** Shared hash computation calls `support.records.support_configuration`, including its six authoritative keys. Touching `theme_workflow.py` triggers P15-M1's revisit: this plan makes the necessary typed helper extraction and deliberately leaves broad workflow decomposition outside scope.
- **H8 and local labels.** The working file is `SupportLabelSet` TOML, with `unsure` defaults and a user-supplied `labelled_on` date. The local Markdown view holds context but no scores, judge answers, flags or extractor identity. Both stay ignored and local. Committed labels contain only IDs, hashes, answers, date and extension metadata. Initial unsure values are real answers excluded and counted; finish edits before promotion. A train extension must add targets and preserve all committed labels. Train/dev promotion is atomic and append-only.
- **H10–H15, reports.** Gate results stay a list: two `GOLD_EVIDENCE_RECALL` rows can coexist. Stability figures live in dev's `PartitionReport.figures`; `PilotReport` retains its shape and contains exactly train and dev. Judge families are IdPart-safe at config intake. Export the nine approved APIs. Report qualifiers `minicheck`/`deberta` map explicitly to `MetricReport.view` values `minicheck_joint`/`deberta_joint`. Tolerate and count dangling hard-negative quote references, alongside existing dangling reading references.
- **H16 and leave-alone metrics.** Preserve the shipped tie-group evidence algorithm and lowest-ID convention. P19-3's possible maximum matching and P19-4's label-bootstrap population remain pilot/plan B questions. The judge floor remains reported-only; a flagged target remains in review before policy votes. Gold-evidence recall is theme-agnostic and strictly positive for a passing configuration. Every report figure is feasibility-only and train is in-sample.
- **Retention and GS5.** Retention (i) uses quote-reference occurrences, per event: kept is `sum(len(claim.quote_ids))`; offered is kept plus `sum(len(rejection.labels))` for candidate-level rejections with `candidate_index is not None`. Count retry proposals again and exclude whole replies that never parsed into candidates. Never use `RunRecord.candidates` as this denominator. Recheck GS5 counts against the kept draft before reporting shares; a mismatch blocks their report. Preserve D19-9's drafted/signed denominators.
- **A9 dictionary contracts.** Every new Pydantic model, enum, dataclass and public structural type has its own `###` table in `docs/data-dictionary.md`, registered or explicitly tested in `tests/contracts/test_data_dictionary.py` in the task introducing it. Qualify the application's `pilot_records.RunRecord` heading to distinguish extraction's `RunRecord`. Changed contracts update their existing rows. No wording-glob work remains.
- **Dependencies and tools.** No dependency, Python floor or schema-version change; no `uv lock` update. Use `uv sync --locked --all-packages --group dev --offline` in the fresh worktree and `uv lock --check --offline` for consistency. Use literal git and script commands, with tool workdir rather than compound `cd && git` or variable command names. Ruff's configured line length is 88. Run Ruff check and format check after each task and repository-wide at the end. No configured type checker exists at this baseline.
- **Commits.** Before each execution commit run `git log -3 --oneline`, then stage only that task's files and use its commit message. Apply any attribution trailer required by the execution session. This planning session commits no prototype code and does not execute the plan. The approved plan is committed alone on a branch from main after user review.

## Decisions

All eight owner answers were received as one batch on 2026-10-13, before writing this plan.

- **D20-1** (owner, brief, 2026-10-13): B2 writes `preregistration-v1.toml` as a plan B procedure using `freeze_preregistration` and `preregistration_toml`; A8 adds no `pilot preregister`. Applied in: command scope, Task 13's B2 handoff.
- **D20-2** (owner, brief, 2026-10-13): append stability figures to dev's `PartitionReport.figures`, preserving `PilotReport`'s fields. Applied in: Tasks 4 and 11.
- **D20-3** (owner, brief, 2026-10-13): constrain `ChatModelFile.family` to `IdPart` at config intake, before hashing model files or loading runtimes. Applied in: Task 6.
- **D20-4** (owner, brief, 2026-10-13): export `joint_score`, `sealed`, `claim_label`, `joint_label`, `Figure`, `ReadingAgreement`, `IndependentFigures`, `EvidenceTally`, and `configuration_hash`; document short report qualifiers against joint scorer-view names. Applied in: Task 3 and dictionary rows.
- **D20-5** (owner, brief, 2026-10-13): use the existing `SupportLabelSet` TOML writer/reader for local working labels, with unsure defaults edited by the user; the contextual view remains a separate local file. Applied in: Task 9.
- **D20-6** (owner, brief, 2026-10-13): retention (i) counts kept and offered quote-reference occurrences per event, including retries and excluding unparsed whole replies. Applied in: Task 11 and dictionary documentation.
- **D20-7** (owner, brief, 2026-10-13): adopt the P19-1 boundary set and explicitly retain its remaining items as stated in the disposition table below. Applied in: Tasks 1–4, dictionary rows and completion's P19-1 ticking pass.
- **D20-8** (owner, brief, 2026-10-13): adopt all listed P17-2 gaps, P17-1's shared selectors with existing Stage 6 regressions preserved, and P17-5's train/dev-only command scope, sentinels, independent `RecordError` handling, and parsed-document binding. D19-7 already decides P17-5(2): dangling references are tolerated and counted. Applied in: Tasks 3, 5, 11 and 12.

**Inherited brief decisions:** D18-1 (shared helpers), D19-4 (pure import boundary), D19-5 (Stage 9's decision inputs), D19-6 (lowest-ID tie convention), D19-7 (count dangling references), D19-8/D19-9 (evidence recall and GS5 grains), D19-10/D19-11 (bootstrap/undefined gates), D19-12 (sample prefix), D19-13 (content hashes), D19-14 (frozen configuration), D19-15 (stability and agreement), D19-16 (TOML/label ordering), and D19-17 (context from stored support) remain in force. Apply them in the Global Constraints and the consuming tasks; this plan reopens none of them.

**Plan review approved by the owner on 2026-10-13, including the following defaults and the plan-only commit:**

- **D20-9** (owner, plan review, 2026-10-13): Approves P20-A: a counts-only, required operator acknowledgment between classification and support confirms Gemma is unloaded and both judges/MiniCheck are ready. The existing runtime builder loads Python scorer/tokenizer objects before extraction; B1 must include them in its resident-memory check. It cannot stop an external Gemma server. Tests inject the acknowledgment and prove a refusal dispatches no support request and persists no support phase. Applied in: Global Constraints, Task 8's phase boundary and Task 12's command wrapper.
- **D20-10** (owner, plan review, 2026-10-13): Approves P20-B: shared `committed_gold` returns a parsed list so the entire selection can be preflighted before any bundle loads. Gold validation therefore prints no earlier `valid` lines when a later selected record is malformed. Empty gold validation still succeeds and empty recount still refuses. Applied in: Task 5; existing successful output and refusal/status meanings otherwise stay intact.

Approval authorizes this plan-only commit. It does not authorize execution in the planning session or the later protected `CLAUDE.md` Current state edit.

## Deferred-item dispositions

Read `specs/deferred_items.md` sections 17–19. Tick items only after implementation and the user's gates, with `→ done in plan 20`; do not mark them complete in this planning branch.

| Item | Disposition and closure evidence |
| --- | --- |
| P17-1 | Task 5 extracts committed-gold selection, stems, kept-draft paths, independent path, ledger reader and Events into Stage 6. Existing Stage 6 regressions remain in the user's full-suite gate. |
| P17-2(1) | Task 5 covers recount stem, missing working copy, unreadable draft/working/gold, no-write snapshots, repeated exit=1, and sentinels. |
| P17-2(2),(4) | Task 3 pins the edited item's origin and `build_gold`'s anchor-refusal path carrying repeats. |
| P17-2(3),(5) | Task 5 covers unreadable coverage gold and direct dev-before-train `CoverageReport` rejection; the latter already passes at baseline. |
| P17-5(1) | Task 5 rejects test/excluded selections from either record or authoritative split before text; recount and coverage v2 receive sentinels. |
| P17-5(2) | D19-7 is the disposition: tolerate and count dangling references. Task 4 adds hard-negative dangling counts; no blanket draft semantic-validation gate is introduced. |
| P17-5(3),(4) | Task 11 catches independent `RecordError`; Task 3's optional `doc_id` check and Task 5's coverage caller bind signed gold to the parsed document ID. |
| P18-1/P18-2 | Remain open exactly as plan 18 left them. Neither doc-precision item is silently folded into A8. |
| P19-1 | All individual bullets are adopted or consciously retained below, satisfying its disposition closure condition. Changed boundaries receive tests. |
| P19-2/P19-3/P19-4 | Remain open. Targeted P19-2 cases needed for new boundaries do not close its whole batch. Tie evidence and bootstrap populations are unchanged. |
| P17-3/P17-4 | Remain open. Necessary touched-path changes do not close these broader bundles; do not opportunistically tick them. |
| P15-M1 | Revisited because Task 6 touches the workflow: make the required typed seam extraction, keep the broader decomposition item open. |

Each P19-1 bullet has a concrete disposition:

| P19-1 bullet | Decision | Home |
| --- | --- | --- |
| Unused `UNKNOWN_METRIC` | Retain; no removal. | `evaluation/problems.py` untouched |
| Hash checks and structural type | Adopt one hash-comparison primitive and a content-hash protocol, preserving error contracts. The alleged second public `calibration.checked` is absent at the actual baseline; do not remove a fictional helper. | Task 2 |
| `Candidate.signals` | Adopt `Literal[1]`, also for the fitted candidate. | Task 2 |
| GateRule and wrong-partition subject | Adopt GateRule intake and the given partition in the refusal. | Task 2 |
| PilotReport partition uniqueness | Adopt exactly one train and one dev. | Task 2 |
| GS5 counts, qualifier names, stability refusals | Adopt counts and run/event checks; keep qualifiers and document their mapping. | Tasks 4 and 7 dictionary |
| Hard-negative dangling refs and quote spans | Tolerate/count; share the quote-span map. | Task 4 |
| Four parent-chain walks | Retain; no broad extraction. | Existing code unchanged |
| Label merge, sampler bounds, missing evidence doc | Validate merged labels, reject invalid bounds, closed missing-doc refusal. | Tasks 2–3 |
| TOML non-finite-float key message | Retain. | `tomlfile.py` untouched |
| Private trial reference / policy outcome style | Retain both existing styles. | Existing code unchanged |
| Support metric missing-decision counter | Retain existing behavior and fields. | `support/metrics.py` untouched |
| Nine missing exports | Export all nine approved APIs. | Task 3 |

---

## Task map and code application

| Task | Deliverable | Files and ownership |
| --- | --- | --- |
| 1 | Shared source/configuration and coherence gate | `coding/records.py`, `coding/run.py`, `coding/decide.py`, `coding/__init__.py`; invented coding tests |
| 2 | Evaluation boundary contracts | themes `records.py`, evaluation records, gates, calibration, preregistration, labels, sampling and policy; boundary tests |
| 3 | Public exports and document-binding errors | evaluation exports and label view, annotation; public/gold tests |
| 4 | Counts and stability diagnostics | evaluation cells, scores, report; invented report tests |
| 5 | Shared Stage 6 selectors and legacy safeguards | app `stage6.py`, `gold_cli.py`, `pilot_cli.py`; invented Stage 6 cases and synthetic coverage test |
| 6 | Typed workflow seams and safe family intake | app `theme_config.py`, `theme_workflow.py`, `model_runtime.py`; seam tests |
| 7 | A8 records, readers and metadata-first intake | app `pilot_records.py`, `pilot_inputs.py`, shared split derivation; record/intake tests and dictionary contracts |
| 8 | Phase pass, ordinary replay and fresh dev runs | app `pilot_workflow.py`; scripted workflow tests |
| 9 | Sample, local view and label promotion | app `pilot_labels.py`; invented label tests |
| 10 | Calibration from committed exact bytes | app `pilot_calibration.py`; invented calibration tests |
| 11 | Independent comparisons, report and gates | app `pilot_reporting.py`; strict report intake, collectors and dictionary contracts |
| 12 | Command registration and output boundaries | app `pilot_commands.py`, `pilot_cli.py`, `stage6.py`; invented command sentinels |
| 13 | Scoped verification, user gates and completion | no further production behavior; completion markup only after all gates and owner questions resolve |

Within themes, `coding/` and `evaluation/` mean subdirectories of `packages/earnings-themes/src/earnings_themes/`. Every task lists complete repository-relative paths below. Workers own only their task's files; they are not alone in the repository and must accommodate earlier edits rather than reverting them.

A `diff` block is a complete unified patch relative to the preceding task. Blank context lines are empty rather than carrying a trailing space; Git accepts this form, and the final patch chain was checked from clean main. Apply its full contents with `git apply` (no index or staging flag). A new file is represented by an empty original file (`@@ -0,0 ...`); the replay verified this form. Do not retrieve anything from a planning scratch directory: all required code is embedded here. Put the test patch in place, run the red command, then apply the implementation patch, run green and Ruff, and commit only after task review. The later completion task performs no live pilot operation.

### Task 1: Share coding configuration and proposal/support source binding

**Files:**

- Modify: `packages/earnings-themes/src/earnings_themes/coding/records.py`
- Modify: `packages/earnings-themes/src/earnings_themes/coding/run.py`
- Modify: `packages/earnings-themes/src/earnings_themes/coding/decide.py`
- Modify: `packages/earnings-themes/src/earnings_themes/coding/__init__.py`
- Create: `packages/earnings-themes/tests/coding/test_shared.py`

- Modify: `docs/data-dictionary.md`
- Modify: `tests/contracts/test_data_dictionary.py`

**Interfaces:**

Produces public coding.coding_configuration(*, source_run_id:str, source_run_hash:str, documents:tuple[tuple[str,str],...], codebook:CodebookReference, classifier_identity:JudgeIdentity, coding_policy:CodingPolicySnapshot, ceilings:CodingCeilings, requested_claim_order:tuple[tuple[str,str],...], schema_hash:str, cache_mode:Literal["live","replay","fresh"], coding_version:str=CODING_VERSION, validator_version:str=VALIDATOR_VERSION)->dict[str,object]; coding.source_bindings(sources:SupportSources)->SourceBindings; coding.validate_proposal_support(proposals:ProposalRun,support:StoredSupportRun,sources:SupportSources)->None. SourceBindings fields are source_run_id, source_run_hash, documents and codebook. Application prebinding and calibration consume these; decide_assignments and propose_run call their shared implementations.

- [x] **Step 1: Write the exact test changes**

```diff
--- a/packages/earnings-themes/tests/coding/test_shared.py
+++ b/packages/earnings-themes/tests/coding/test_shared.py
@@ -0,0 +1,82 @@
+"""Shared configuration and source-binding gates over invented records only."""
+
+from dataclasses import replace
+
+import pytest
+from earnings_core import digest
+from earnings_themes.coding import (
+    coding_configuration,
+    source_bindings,
+    validate_proposal_support,
+)
+from earnings_themes.coding.records import CodingError
+
+
+def test_coding_configuration_reproduces_existing_manifest(assessed_case):
+    record = assessed_case.proposals.record
+    keys = (
+        "source_run_id",
+        "source_run_hash",
+        "documents",
+        "codebook",
+        "classifier_identity",
+        "coding_policy",
+        "ceilings",
+        "requested_claim_order",
+        "schema_hash",
+        "coding_version",
+        "validator_version",
+        "cache_mode",
+    )
+    material = coding_configuration(**{key: getattr(record, key) for key in keys})
+    assert set(material) == set(keys)
+    assert digest(material) == record.configuration_hash
+    bindings = source_bindings(assessed_case.sources)
+    assert set(bindings) == {
+        "source_run_id",
+        "source_run_hash",
+        "documents",
+        "codebook",
+    }
+    assert bindings == {key: getattr(record, key) for key in bindings}
+    validate_proposal_support(
+        assessed_case.proposals, assessed_case.support, assessed_case.sources
+    )
+
+
+def test_source_run_id_is_bound_even_when_manifest_hash_is_unchanged(assessed_case):
+    support = assessed_case.support
+    altered = replace(
+        support, record=support.record.model_copy(update={"source_run_id": "other"})
+    )
+    with pytest.raises(CodingError, match="^(input_changed|storage_corrupt)$"):
+        validate_proposal_support(
+            assessed_case.proposals, altered, assessed_case.sources
+        )
+
+
+def test_shared_gate_uses_support_outcome_uniqueness_check(assessed_case):
+    support = assessed_case.support
+    altered = replace(support, outcomes=(*support.outcomes, support.outcomes[0]))
+    with pytest.raises(CodingError):
+        validate_proposal_support(
+            assessed_case.proposals, altered, assessed_case.sources
+        )
+
+
+def test_shared_gate_requires_current_proposal_configuration(assessed_case):
+    proposals = assessed_case.proposals
+    altered = replace(
+        proposals,
+        record=proposals.record.model_copy(update={"configuration_hash": "f" * 64}),
+    )
+    with pytest.raises(CodingError, match="^input_changed$"):
+        validate_proposal_support(altered, assessed_case.support, assessed_case.sources)
+
+
+def test_shared_gate_uses_support_outcome_order_check(assignment_case_factory):
+    case = assignment_case_factory(themes=("capacity", "demand"))
+    assert len(case.support.outcomes) == 2
+    altered = replace(case.support, outcomes=tuple(reversed(case.support.outcomes)))
+    with pytest.raises(CodingError):
+        validate_proposal_support(case.proposals, altered, case.sources)
```

The same task adds its dictionary contract test:

```diff
--- a/tests/contracts/test_data_dictionary.py
+++ b/tests/contracts/test_data_dictionary.py
@@ -43,7 +43,7 @@
 from earnings_themes.coding.cache import CodingCacheEntry
 from earnings_themes.coding.decide import DecisionInput, DecisionSet
 from earnings_themes.coding.input import CodingInput
-from earnings_themes.coding.run import ProposalRun
+from earnings_themes.coding.run import ProposalRun, SourceBindings
 from earnings_themes.coding.store import SCHEMAS
 from earnings_themes.evaluation import (
     align,
@@ -671,6 +671,20 @@
     assert "schema-2 partial" in text and "schema-1 partial" in text


+def test_source_bindings_and_shared_coding_gates_documented():
+    assert documented("SourceBindings") == set(SourceBindings.__annotations__)
+    text = DICTIONARY.read_text(encoding="utf-8")
+    assert "source_bindings(sources: SupportSources) -> SourceBindings" in text
+    assert (
+        "validate_proposal_support(proposals: ProposalRun, support: StoredSupportRun,"
+        in text
+    )
+    assert (
+        "coding_configuration(*, source_run_id, source_run_hash, documents, codebook,"
+        in text
+    )
+
+
 EVALUATION_MODELS = [
     bootstrap.BootstrapPlan,
     bootstrap.Interval,
```

- [x] **Step 2: Run the scoped red check**

```bash
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/coding/test_shared.py --tb=short -q
```

Expected: collection fails with ImportError for coding_configuration.

- [x] **Step 3: Apply the exact library changes**

```diff
--- a/packages/earnings-themes/src/earnings_themes/coding/records.py
+++ b/packages/earnings-themes/src/earnings_themes/coding/records.py
@@ -7,7 +7,7 @@
 from enum import StrEnum
 from typing import Any, Literal, Self

-from earnings_core import digest
+from earnings_core import VALIDATOR_VERSION, digest
 from pydantic import (
     AwareDatetime,
     Field,
@@ -243,6 +243,38 @@
     requests_per_run: int = Field(ge=0)
     tokens_per_document: int = Field(ge=0)
     tokens_per_run: int = Field(ge=0)
+
+
+def coding_configuration(
+    *,
+    source_run_id: str,
+    source_run_hash: str,
+    documents: tuple[tuple[str, str], ...],
+    codebook: CodebookReference,
+    classifier_identity: JudgeIdentity,
+    coding_policy: CodingPolicySnapshot,
+    ceilings: CodingCeilings,
+    requested_claim_order: tuple[tuple[str, str], ...],
+    schema_hash: str,
+    cache_mode: Literal["live", "replay", "fresh"],
+    coding_version: str = CODING_VERSION,
+    validator_version: str = VALIDATOR_VERSION,
+) -> dict[str, object]:
+    """The complete configuration material shared by production and revalidation."""
+    return {
+        "source_run_id": source_run_id,
+        "source_run_hash": source_run_hash,
+        "documents": documents,
+        "codebook": codebook.model_dump(mode="json"),
+        "classifier_identity": classifier_identity.model_dump(mode="json"),
+        "coding_policy": coding_policy.model_dump(mode="json"),
+        "ceilings": ceilings.model_dump(mode="json"),
+        "requested_claim_order": requested_claim_order,
+        "schema_hash": schema_hash,
+        "coding_version": coding_version,
+        "validator_version": validator_version,
+        "cache_mode": cache_mode,
+    }


 class ClassificationRecord(CodingRecord):
--- a/packages/earnings-themes/src/earnings_themes/coding/run.py
+++ b/packages/earnings-themes/src/earnings_themes/coding/run.py
@@ -4,6 +4,7 @@
 from collections.abc import Mapping, Sequence
 from dataclasses import dataclass
 from datetime import datetime
+from typing import TypedDict

 from earnings_core import VALIDATOR_VERSION, digest

@@ -38,6 +39,7 @@
     ProposalRecord,
     ProposalRunRecord,
     checked,
+    coding_configuration,
 )
 from earnings_themes.extraction.records import RunRecord
 from earnings_themes.extraction.store import StoredRun
@@ -58,7 +60,15 @@
         return tuple(proposal.target for proposal in self.proposals)


-def _source_bindings(sources: SupportSources) -> dict:
+class SourceBindings(TypedDict):
+    source_run_id: str
+    source_run_hash: str
+    documents: tuple[tuple[str, str], ...]
+    codebook: CodebookReference
+
+
+def source_bindings(sources: SupportSources) -> SourceBindings:
+    """The validated source manifest and codebook shared by run prebinding."""
     if (
         type(sources) is not SupportSources
         or type(sources.stored_run) is not StoredRun
@@ -154,22 +164,17 @@
         )
         identity = _classifier_identity(classifier)
         ceiling_value = checked(ceilings, CodingCeilings)
-        bindings = _source_bindings(sources)
+        bindings = source_bindings(sources)
         schema_hash = digest(CodingReply.model_json_schema())
-        configuration = {
-            **{
-                k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v
-                for k, v in bindings.items()
-            },
-            "classifier_identity": identity.model_dump(mode="json"),
-            "coding_policy": snapshot.model_dump(mode="json"),
-            "ceilings": ceiling_value.model_dump(mode="json"),
-            "requested_claim_order": order,
-            "schema_hash": schema_hash,
-            "coding_version": CODING_VERSION,
-            "validator_version": VALIDATOR_VERSION,
-            "cache_mode": cache.mode,
-        }
+        configuration = coding_configuration(
+            **bindings,
+            classifier_identity=identity,
+            coding_policy=snapshot,
+            ceilings=ceiling_value,
+            requested_claim_order=order,
+            schema_hash=schema_hash,
+            cache_mode=cache.mode,
+        )
         record = checked(
             ProposalRunRecord.model_construct(
                 run_id=run_id,
@@ -279,7 +284,7 @@
         if _current_identity(classifier) != identity:
             raise CodingError("model_mismatch")
         if (
-            _source_bindings(sources) != bindings
+            source_bindings(sources) != bindings
             or digest(_policy(policy).model_dump(mode="json")) != policy_hash
             or checked(ceilings, CodingCeilings) != ceiling_value
             or tuple(sorted(software.items())) != record.software
--- a/packages/earnings-themes/src/earnings_themes/coding/decide.py
+++ b/packages/earnings-themes/src/earnings_themes/coding/decide.py
@@ -23,6 +23,7 @@
     ProposalRecord,
     ProposalRunRecord,
     checked,
+    coding_configuration,
 )
 from earnings_themes.coding.run import ProposalRun
 from earnings_themes.support import reverify_support_run
@@ -138,25 +139,20 @@
         raise CodingError("input_changed")
     if record.documents != tuple(sorted(sources.stored_run.record.documents.items())):
         raise CodingError("input_changed")
-    configuration = {
-        name: getattr(record, name).model_dump(mode="json")
-        if hasattr(getattr(record, name), "model_dump")
-        else getattr(record, name)
-        for name in (
-            "source_run_id",
-            "source_run_hash",
-            "documents",
-            "codebook",
-            "classifier_identity",
-            "coding_policy",
-            "ceilings",
-            "requested_claim_order",
-            "schema_hash",
-            "coding_version",
-            "validator_version",
-            "cache_mode",
-        )
-    }
+    configuration = coding_configuration(
+        source_run_id=record.source_run_id,
+        source_run_hash=record.source_run_hash,
+        documents=record.documents,
+        codebook=record.codebook,
+        classifier_identity=record.classifier_identity,
+        coding_policy=record.coding_policy,
+        ceilings=record.ceilings,
+        requested_claim_order=record.requested_claim_order,
+        schema_hash=record.schema_hash,
+        coding_version=record.coding_version,
+        validator_version=record.validator_version,
+        cache_mode=record.cache_mode,
+    )
     if (
         digest(configuration) != record.configuration_hash
         or record.validator_version != VALIDATOR_VERSION
@@ -353,6 +349,42 @@
     return "review", "policy_review", ()


+def _proposal_support_inputs(
+    proposals: ProposalRun, support: StoredSupportRun, sources: SupportSources
+) -> tuple[tuple[ReviewOutcome, ...], dict[str, TargetRecord], dict[str, TargetRecord]]:
+    """The shared reverified gate before calibration or assignment consumption."""
+    outcomes = reverify_support_run(support, sources)
+    current = _proposal_inputs(proposals, sources)
+    if (
+        support.record.source_run_hash != proposals.record.source_run_hash
+        or support.record.source_run_id != proposals.record.source_run_id
+        or support.record.codebook != proposals.record.codebook
+        or support.record.documents != proposals.record.documents
+    ):
+        raise CodingError("input_changed")
+    stored = {
+        digest(row.target.model_dump(mode="json")): row for row in support.targets
+    }
+    if not set(stored) <= set(current):
+        raise CodingError("invalid_references")
+    return outcomes, current, stored
+
+
+def validate_proposal_support(
+    proposals: ProposalRun, support: StoredSupportRun, sources: SupportSources
+) -> None:
+    """Refuse a proposal/support pair unless both bind the complete current source."""
+    try:
+        proposal_run_hash(proposals)
+        _proposal_support_inputs(proposals, support, sources)
+    except CodingError:
+        raise
+    except SupportError as error:
+        raise CodingError(str(error)) from None
+    except Exception:  # noqa: BLE001 - boundary failures never print source data
+        raise CodingError("unexpected_error") from None
+
+
 def decide_assignments(
     proposals: ProposalRun,
     support: StoredSupportRun,
@@ -362,20 +394,9 @@
     """One decision per proposal, after current evidence and frozen-policy checks."""
     try:
         proposal_hash = proposal_run_hash(proposals)
-        outcomes = reverify_support_run(support, sources)
-        current = _proposal_inputs(proposals, sources)
-        if (
-            support.record.source_run_hash != proposals.record.source_run_hash
-            or support.record.source_run_id != proposals.record.source_run_id
-            or support.record.codebook != proposals.record.codebook
-            or support.record.documents != proposals.record.documents
-        ):
-            raise CodingError("input_changed")
-        stored = {
-            digest(row.target.model_dump(mode="json")): row for row in support.targets
-        }
-        if not set(stored) <= set(current):
-            raise CodingError("invalid_references")
+        outcomes, current, stored = _proposal_support_inputs(
+            proposals, support, sources
+        )
         support_hash = support_run_hash(support)
         support_content_hash = _support_content_hash(support)
         reference = _policy_reference(policy, proposals, support)
--- a/packages/earnings-themes/src/earnings_themes/coding/__init__.py
+++ b/packages/earnings-themes/src/earnings_themes/coding/__init__.py
@@ -6,6 +6,7 @@
     DecisionInput,
     DecisionSet,
     decide_assignments,
+    validate_proposal_support,
 )
 from earnings_themes.coding.input import (
     CodingInput,
@@ -40,8 +41,9 @@
     ProposalRecord,
     ProposalRunRecord,
     checked,
+    coding_configuration,
 )
-from earnings_themes.coding.run import ProposalRun, propose_run
+from earnings_themes.coding.run import ProposalRun, propose_run, source_bindings
 from earnings_themes.coding.store import (
     read_coding_run,
     reverify_coding_run,
@@ -84,6 +86,7 @@
     "SupportSources",
     "assignment_frame",
     "checked",
+    "coding_configuration",
     "decide_assignments",
     "project_assignments",
     "propose_run",
@@ -91,5 +94,7 @@
     "resolve_coding_input",
     "reverify_coding_input",
     "reverify_coding_run",
+    "source_bindings",
+    "validate_proposal_support",
     "write_coding_run",
 ]
```

Apply the matching dictionary rows in this implementation step:

```diff
--- a/docs/data-dictionary.md
+++ b/docs/data-dictionary.md
@@ -6913,3 +6913,38 @@
 `no_candidate`, subject `selection`, for one without a selection. `evaluate`
 applies the selected `ScorerCutoff`: accept with the eligible quotes when the joint
 score reaches the cutoff and an eligible quote exists, otherwise review.
+
+## Stage 11 shared and application boundaries (plan 20, A8/A9)
+
+These APIs reuse the existing coding, support and evaluation gates. They keep
+persisted field names and schema versions.
+
+### `SourceBindings`
+
+A nonpersisted `TypedDict` returned by
+`source_bindings(sources: SupportSources) -> SourceBindings` after validating the
+source manifest and codebook. It is used before dispatch, after dispatch and when
+the application prebinds the coding configuration.
+
+| Field | Type | Meaning |
+| --- | --- | --- |
+| `source_run_id` | string | The extraction run's identity |
+| `source_run_hash` | SHA-256 | Digest of the extraction manifest and complete source provenance hash |
+| `documents` | tuple of (string, SHA-256) | Document IDs and canonical hashes, sorted by document ID |
+| `codebook` | CodebookReference | Frozen codebook identity, version and content hash |
+
+### Shared coding gates
+
+
+`coding_configuration(*, source_run_id, source_run_hash, documents, codebook,
+classifier_identity, coding_policy, ceilings, requested_claim_order, schema_hash,
+cache_mode, coding_version, validator_version)` returns the same twelve-key
+configuration material that `ProposalRunRecord.configuration_hash` binds. Coding
+production and proposal reconstruction both call this definition.
+
+`validate_proposal_support(proposals: ProposalRun, support: StoredSupportRun,
+sources: SupportSources) -> None` reuses the gate before `decide_assignments`:
+reverify the support run, recompute proposed inputs, bind the extraction source run
+ID/hash, documents and codebook, and require support targets to be among the
+proposals. The existing support gate establishes unique outcomes in target order.
+The application applies it to both support runs before calibration or reporting.
```

- [x] **Step 4: Run the scoped green check and changed-file Ruff**

```bash
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/coding/test_shared.py --tb=short -q
uv run --locked --offline --no-sync ruff check packages/earnings-themes/src/earnings_themes/coding/records.py packages/earnings-themes/src/earnings_themes/coding/run.py packages/earnings-themes/src/earnings_themes/coding/decide.py packages/earnings-themes/src/earnings_themes/coding/__init__.py packages/earnings-themes/tests/coding/test_shared.py
uv run --locked --offline --no-sync ruff format --check packages/earnings-themes/src/earnings_themes/coding/records.py packages/earnings-themes/src/earnings_themes/coding/run.py packages/earnings-themes/src/earnings_themes/coding/decide.py packages/earnings-themes/src/earnings_themes/coding/__init__.py packages/earnings-themes/tests/coding/test_shared.py
```

Expected: all selected tests pass and Ruff is clean. Record the actual counts.


Run the static dictionary contracts in both the red and green steps:

```bash
uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_data_dictionary.py --tb=short -q
uv run --locked --offline --no-sync ruff check tests/contracts/test_data_dictionary.py
uv run --locked --offline --no-sync ruff format --check tests/contracts/test_data_dictionary.py
```

Before the rows exist, the newly added dictionary checks fail for the missing table/contract. After code and rows are applied, they pass. Stage `docs/data-dictionary.md` and `tests/contracts/test_data_dictionary.py` in this task's commit along with its listed code files.

- [x] **Step 5: Commit this task during the later authorized execution**

```bash
git log -3 --oneline
git add packages/earnings-themes/src/earnings_themes/coding/records.py packages/earnings-themes/src/earnings_themes/coding/run.py packages/earnings-themes/src/earnings_themes/coding/decide.py packages/earnings-themes/src/earnings_themes/coding/__init__.py packages/earnings-themes/tests/coding/test_shared.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(pilot): share coding configuration and proposal/support source binding"
```

---

### Task 2: Validate evaluation boundaries and share the content-hash check

**Files:**

- Modify: `packages/earnings-themes/src/earnings_themes/records.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/records.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/gates.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/calibration.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/preregistration.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/labels.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/sampling.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/policy.py`
- Create: `packages/earnings-themes/tests/evaluation/test_boundary_tidy.py`
- Modify: `packages/earnings-themes/tests/evaluation/test_gates.py`
- Modify: `packages/earnings-themes/tests/evaluation/test_records.py`
- Modify: `packages/earnings-themes/tests/evaluation/test_calibration.py`

- Modify: `docs/data-dictionary.md`
- Modify: `tests/contracts/test_data_dictionary.py`

**Interfaces:**

Produces records.HashedRecord structural Protocol, records.hash_matches(record:HashedRecord)->bool; sealed and checked are bounded by HashedRecord. derive_gates(report:PilotReport,*,rule:GateRule,judge_floor:float,preregistration_hash:str,version:int=1)->Gates replaces its prior gated/undefined_gate arguments. Application passes rule=preregistration.gates. PilotReport requires exactly one train and one dev partition, either order. Candidate and CandidateFit signals are Literal[1]. merge_labels keeps its signature and returns a validated reconstructed record.

- [x] **Step 1: Write the exact test changes**

```diff
--- a/packages/earnings-themes/tests/evaluation/test_boundary_tidy.py
+++ b/packages/earnings-themes/tests/evaluation/test_boundary_tidy.py
@@ -0,0 +1,150 @@
+"""Approved boundary tidies exercised with invented records only."""
+
+from datetime import date
+
+import pytest
+from earnings_themes.evaluation.gates import derive_gates, evaluate_gates
+from earnings_themes.evaluation.labels import (
+    ClaimAnswer,
+    FitAnswer,
+    SupportLabel,
+    SupportLabelSet,
+    merge_labels,
+)
+from earnings_themes.evaluation.preregistration import (
+    REQUIRED_GATES,
+    Candidate,
+    GateRule,
+)
+from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
+from earnings_themes.evaluation.records import PartitionReport, PilotReport
+from earnings_themes.evaluation.sampling import sample_targets
+from earnings_themes.records import RecordError
+from earnings_themes.split import Partition
+from pydantic import ValidationError
+
+HASH = "1" * 64
+
+
+def partition(kind):
+    return PartitionReport(
+        partition=kind, in_sample=kind is Partition.TRAIN, events=(), figures=()
+    )
+
+
+def report(*parts):
+    return PilotReport(
+        report_version=1,
+        preregistration_hash=HASH,
+        calibration_hash=HASH,
+        partitions=parts,
+        content_hash=HASH,
+    )
+
+
+@pytest.mark.parametrize(
+    "parts",
+    [(), (Partition.TRAIN,), (Partition.DEV,), (Partition.TRAIN, Partition.TRAIN)],
+)
+def test_report_requires_exactly_one_train_and_dev(parts):
+    with pytest.raises(ValidationError, match="one train and one dev"):
+        report(*(partition(kind) for kind in parts))
+
+
+def test_report_accepts_both_partition_orders():
+    for kinds in ((Partition.TRAIN, Partition.DEV), (Partition.DEV, Partition.TRAIN)):
+        assert len(report(*(partition(kind) for kind in kinds)).partitions) == 2
+
+
+def test_every_candidate_uses_one_signal():
+    with pytest.raises(ValidationError):
+        Candidate(
+            candidate_id="c1",
+            rule="scorer_cutoff",
+            signal="minicheck_joint",
+            signals=2,
+            grid=(0.5,),
+        )
+
+
+def test_derive_gates_takes_and_rechecks_the_preregistered_rule():
+    base = report(partition(Partition.TRAIN), partition(Partition.DEV))
+    rule = GateRule(
+        rule="dev-lower-bound/1",
+        gated=tuple(sorted(REQUIRED_GATES)),
+        undefined_gate="not_gated",
+    )
+    result = derive_gates(base, rule=rule, judge_floor=0.4, preregistration_hash=HASH)
+    assert {r.metric for r in result.ungated} == REQUIRED_GATES
+    with pytest.raises(EvaluationError) as refused:
+        derive_gates(
+            base,
+            rule=rule.model_copy(update={"undefined_gate": "typo"}),
+            judge_floor=0.4,
+            preregistration_hash=HASH,
+        )
+    assert (refused.value.problem, refused.value.subject) == (
+        EvaluationProblem.MALFORMED_RECORD,
+        "rule",
+    )
+
+
+@pytest.mark.parametrize(("size", "cap", "subject"), [(-1, 1, "size"), (1, 0, "cap")])
+def test_sampling_refuses_invalid_bounds(size, cap, subject):
+    with pytest.raises(EvaluationError) as refused:
+        sample_targets((), seed=1, size=size, cap=cap)
+    assert (refused.value.problem, refused.value.subject) == (
+        EvaluationProblem.MALFORMED_RECORD,
+        subject,
+    )
+
+
+def test_merged_labels_revalidate_cross_partition_target_ids():
+    def label(kind):
+        return SupportLabel(
+            target_id="same-target",
+            target_input_hash=HASH,
+            partition=kind,
+            claim_support=ClaimAnswer.SUPPORTED,
+            theme_fit=FitAnswer.FITS,
+            labelled_on=date(2026, 10, 1),
+        )
+
+    train = SupportLabelSet(preregistration_hash=HASH, labels=(label(Partition.TRAIN),))
+    dev = SupportLabelSet(preregistration_hash=HASH, labels=(label(Partition.DEV),))
+    with pytest.raises(RecordError, match="one label per target"):
+        merge_labels(train, dev, Partition.DEV)
+
+
+def test_wrong_partition_refusals_use_the_same_field_path():
+    base = report(partition(Partition.TRAIN), partition(Partition.DEV))
+    rule = GateRule(
+        rule="dev-lower-bound/1",
+        gated=tuple(sorted(REQUIRED_GATES)),
+        undefined_gate="not_gated",
+    )
+    gates = derive_gates(base, rule=rule, judge_floor=0.4, preregistration_hash=HASH)
+    missing = base.model_copy(update={"partitions": (partition(Partition.TRAIN),)})
+    for call in (
+        lambda: derive_gates(
+            missing, rule=rule, judge_floor=0.4, preregistration_hash=HASH
+        ),
+        lambda: evaluate_gates(gates, partition(Partition.TRAIN)),
+    ):
+        with pytest.raises(EvaluationError) as refused:
+            call()
+        assert (refused.value.problem, refused.value.subject) == (
+            EvaluationProblem.WRONG_PARTITION,
+            "partition",
+        )
+
+
+def test_hash_helpers_have_a_hashed_record_contract_and_shared_check():
+    from earnings_themes import records
+
+    assert hasattr(records, "HashedRecord")
+    base = report(partition(Partition.TRAIN), partition(Partition.DEV))
+    sealed = records.sealed(base)
+    assert records.hash_matches(sealed)
+    assert not records.hash_matches(sealed.model_copy(update={"report_version": 2}))
+    assert records.checked.__type_params__[0].__bound__ is records.HashedRecord
--- a/packages/earnings-themes/tests/evaluation/test_gates.py
+++ b/packages/earnings-themes/tests/evaluation/test_gates.py
@@ -10,6 +10,7 @@
     gates_toml,
     load_gates,
 )
+from earnings_themes.evaluation.preregistration import REQUIRED_GATES, GateRule
 from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
 from earnings_themes.evaluation.records import Metric, PilotReport, sealed
 from earnings_themes.evaluation.report import EventObservation, partition_report
@@ -19,12 +20,13 @@
 from .test_report import BOOK, PLAN, labelled, observations

 HASH = "1" * 64
-GATED = (
-    Metric.THEME_F1_MICRO,
-    Metric.SPAN_UNIT_F1,
-    Metric.GOLD_EVIDENCE_RECALL,
-    Metric.SUPPORT_PRECISION,
-)
+GATED = tuple(sorted(REQUIRED_GATES))
+
+
+def rule(undefined_gate="not_gated"):
+    return GateRule(
+        rule="dev-lower-bound/1", gated=GATED, undefined_gate=undefined_gate
+    )


 def pilot(dev) -> PilotReport:
@@ -33,7 +35,12 @@
             report_version=1,
             preregistration_hash=HASH,
             calibration_hash=HASH,
-            partitions=(dev,),
+            partitions=(
+                dev.model_copy(
+                    update={"partition": Partition.TRAIN, "in_sample": True}
+                ),
+                dev,
+            ),
             content_hash="0" * 64,
         )
     )
@@ -49,8 +56,7 @@
 def gates_of(baseline, **options):
     return derive_gates(
         pilot(baseline),
-        gated=GATED,
-        undefined_gate=options.get("undefined_gate", "not_gated"),
+        rule=rule(options.get("undefined_gate", "not_gated")),
         judge_floor=0.4,
         preregistration_hash=HASH,
     )
@@ -133,17 +139,15 @@
     )
     with pytest.raises(EvaluationError, match="wrong_partition"):
         derive_gates(
-            pilot(train),
-            gated=GATED,
-            undefined_gate="not_gated",
+            pilot(baseline).model_copy(update={"partitions": (train,)}),
+            rule=rule(),
             judge_floor=0.4,
             preregistration_hash=HASH,
         )
     with pytest.raises(EvaluationError) as refused:
         derive_gates(
             pilot(baseline),
-            gated=GATED,
-            undefined_gate="not_gated",
+            rule=rule(),
             judge_floor=0.4,
             preregistration_hash="2" * 64,
         )
--- a/packages/earnings-themes/tests/evaluation/test_records.py
+++ b/packages/earnings-themes/tests/evaluation/test_records.py
@@ -80,7 +80,14 @@
             report_version=1,
             preregistration_hash="1" * 64,
             calibration_hash="2" * 64,
-            partitions=(),
+            partitions=(
+                PartitionReport(
+                    partition=Partition.TRAIN, in_sample=True, events=(), figures=()
+                ),
+                PartitionReport(
+                    partition=Partition.DEV, in_sample=False, events=(), figures=()
+                ),
+            ),
             content_hash="0" * 64,
         )
     )
@@ -104,7 +111,12 @@
             report_version=1,
             preregistration_hash="1" * 64,
             calibration_hash="2" * 64,
-            partitions=(dev,),
+            partitions=(
+                dev,
+                dev.model_copy(
+                    update={"partition": Partition.TRAIN, "in_sample": True}
+                ),
+            ),
             content_hash="0" * 64,
         )
     )
--- a/packages/earnings-themes/tests/evaluation/test_calibration.py
+++ b/packages/earnings-themes/tests/evaluation/test_calibration.py
@@ -266,16 +266,10 @@
     ("menu", "fitted", "chosen"),
     [
         pytest.param(
-            [("plenty", 3, [0.9]), ("frugal", 1, [0.0, 0.5])],
+            [("plenty", 1, [0.9]), ("frugal", 1, [0.0, 0.5])],
             {"plenty": 0.9, "frugal": 0.0},
             ("plenty", 0.9),
-            id="higher-precision-beats-fewer-signals",
-        ),
-        pytest.param(
-            [("pair", 2, [0.7]), ("solo", 1, [0.9])],
-            {"pair": 0.7, "solo": 0.9},
-            ("solo", 0.9),
-            id="tied-precision-fewer-signals-beats-lower-cutoff",
+            id="higher-precision-wins",
         ),
         pytest.param(
             [("high", 1, [0.9]), ("low", 1, [0.7])],
@@ -290,14 +284,14 @@
             id="all-tied-lower-candidate-id",
         ),
         pytest.param(
-            [("never", 1, [1.0]), ("ok", 5, [0.9])],
+            [("never", 1, [1.0]), ("ok", 1, [0.9])],
             {"never": None, "ok": 0.9},
             ("ok", 0.9),
             id="a-candidate-without-a-cutoff-is-skipped",
         ),
     ],
 )
-def test_selection_orders_candidates_by_precision_signals_cutoff_and_id(
+def test_selection_orders_single_signal_candidates_by_precision_cutoff_and_id(
     menu, fitted, chosen
 ) -> None:
     """Over the 60 targets of ``population()``. Any cutoff above 0.6 up to 0.95
@@ -307,7 +301,7 @@
     30/40 = 0.75, a tie that goes to the lower cutoff within a candidate. Cutoff 1.0
     accepts nothing (0.95 < 1.0): no labelled accepted target, so no precision, and
     recall 0/40 does not meet rho. Across candidates the key is (-precision, signals,
-    cutoff, candidate_id), each case below decided by one successive term."""
+    cutoff, candidate_id), every signals value is 1; the remaining terms decide each case below."""
     preregistration = menu_of(*menu)
     _, label_set, _, _ = population()
     artifact = run(preregistration, rebound(preregistration, label_set))
```

The same task adds its dictionary contract test:

```diff
--- a/tests/contracts/test_data_dictionary.py
+++ b/tests/contracts/test_data_dictionary.py
@@ -685,6 +685,16 @@
     )


+def test_hashed_record_and_gate_boundary_documented():
+    assert documented("HashedRecord") == {"content_hash", "model_dump", "model_copy"}
+    text = DICTIONARY.read_text(encoding="utf-8")
+    assert "hash_matches(record: HashedRecord) -> bool" in text
+    assert (
+        "derive_gates(report, *, rule: GateRule, judge_floor, preregistration_hash,"
+        in text
+    )
+
+
 EVALUATION_MODELS = [
     bootstrap.BootstrapPlan,
     bootstrap.Interval,
```

- [x] **Step 2: Run the scoped red check**

```bash
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/evaluation/test_boundary_tidy.py --tb=short -q
```

Expected: the new typed rule and validators are absent, so the intended boundary cases fail. Characterizations may pass. Record actual failure/pass counts.

- [x] **Step 3: Apply the exact library changes**

```diff
--- a/packages/earnings-themes/src/earnings_themes/records.py
+++ b/packages/earnings-themes/src/earnings_themes/records.py
@@ -14,7 +14,7 @@

 import json
 from pathlib import Path
-from typing import Annotated, Literal
+from typing import Annotated, Any, Literal, Protocol, Self

 from earnings_core import canonical_json, digest
 from earnings_core.documents import IdPart
@@ -66,6 +66,17 @@
         self.problems = problems


+class HashedRecord(Protocol):
+    """The structural contract for immutable records carrying a content hash."""
+
+    @property
+    def content_hash(self) -> str: ...
+
+    def model_dump(self, **kwargs: Any) -> dict[str, Any]: ...
+
+    def model_copy(self, *, update: dict[str, Any]) -> Self: ...
+
+
 def record_json(record: BaseModel) -> bytes:
     """Indented JSON with sorted keys, as the corpus records are written."""
     text = json.dumps(
@@ -101,19 +112,24 @@
         raise RecordError(path.name, (f"not JSON at line {error.lineno}",)) from None


-def content_hash(record: BaseModel) -> str:
+def content_hash(record: HashedRecord) -> str:
     """The digest of every field but ``content_hash``."""
     return digest(record.model_dump(mode="json", exclude={"content_hash"}))


-def sealed[M: BaseModel](record: M) -> M:
+def sealed[M: HashedRecord](record: M) -> M:
     """``record`` with its ``content_hash`` filled in."""
     return record.model_copy(update={"content_hash": content_hash(record)})


-def checked[M: BaseModel](record: M, name: str) -> M:
+def hash_matches(record: HashedRecord) -> bool:
+    """Whether the shared content digest matches the recorded content hash."""
+    return content_hash(record) == record.content_hash
+
+
+def checked[M: HashedRecord](record: M, name: str) -> M:
     """``record``, refused unless it hashes to its ``content_hash``."""
-    if content_hash(record) != record.content_hash:
+    if not hash_matches(record):
         raise RecordError(name, ("does not hash to its content_hash",))
     return record

@@ -128,6 +144,7 @@

 __all__ = [
     "THEMES_SCHEMA_VERSION",
+    "HashedRecord",
     "IdPart",
     "NonBlank",
     "Part",
@@ -138,6 +155,7 @@
     "checked",
     "content_hash",
     "describe",
+    "hash_matches",
     "parse",
     "read_json",
     "record_json",
--- a/packages/earnings-themes/src/earnings_themes/evaluation/records.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/records.py
@@ -160,6 +160,13 @@
     independent: tuple[IndependentFigures, ...] = ()
     content_hash: Sha256Hex

+    @model_validator(mode="after")
+    def _both_partitions_once(self) -> Self:
+        partitions = [report.partition for report in self.partitions]
+        if len(partitions) != 2 or set(partitions) != {Partition.TRAIN, Partition.DEV}:
+            raise ValueError("one train and one dev partition are required")
+        return self
+
     def partition(self, partition: Partition) -> PartitionReport | None:
         return next((p for p in self.partitions if p.partition is partition), None)

--- a/packages/earnings-themes/src/earnings_themes/evaluation/gates.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/gates.py
@@ -9,11 +9,10 @@
   everything fails (R12.8).
 """

-from collections.abc import Sequence
 from pathlib import Path
-from typing import Literal

 from earnings_themes import tomlfile
+from earnings_themes.evaluation.preregistration import GateRule
 from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
 from earnings_themes.evaluation.records import (
     Gate,
@@ -27,7 +26,7 @@
     checked,
     sealed,
 )
-from earnings_themes.records import parse
+from earnings_themes.records import RecordError, parse
 from earnings_themes.split import Partition

 HEADER = (
@@ -39,23 +38,26 @@
 def derive_gates(
     report: PilotReport,
     *,
-    gated: Sequence[Metric],
-    undefined_gate: Literal["not_gated", "point_estimate"],
+    rule: GateRule,
     judge_floor: float,
     preregistration_hash: str,
     version: int = 1,
 ) -> Gates:
     """V6's gates from ``report``'s dev partition (FP15)."""
+    try:
+        rule = parse(rule.model_dump(mode="json"), GateRule, "rule")
+    except (RecordError, AttributeError):
+        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "rule") from None
     dev = report.partition(Partition.DEV)
     if dev is None:
-        raise EvaluationError(EvaluationProblem.WRONG_PARTITION, "dev")
+        raise EvaluationError(EvaluationProblem.WRONG_PARTITION, "partition")
     if report.preregistration_hash != preregistration_hash:
         raise EvaluationError(
             EvaluationProblem.PREREGISTRATION_MISMATCH, "preregistration_hash"
         )
     gates: list[Gate] = []
     ungated: list[Ungated] = []
-    for metric in sorted(set(gated)):
+    for metric in sorted(rule.gated):
         figure = dev.figure(metric)
         if figure is None:
             ungated.append(Ungated(metric=metric, reason="not_in_report"))
@@ -63,7 +65,7 @@
             gates.append(
                 Gate(metric=metric, bound=figure.interval.lower, basis="lower_bound")
             )
-        elif undefined_gate == "point_estimate" and figure.point is not None:
+        elif rule.undefined_gate == "point_estimate" and figure.point is not None:
             gates.append(
                 Gate(metric=metric, bound=figure.point, basis="point_estimate")
             )
@@ -86,7 +88,7 @@
 def evaluate_gates(gates: Gates, report: PartitionReport) -> GateVerdict:
     """Whether a configuration's dev figures pass every gate (FP15, R12.8)."""
     if report.partition is not Partition.DEV:
-        raise EvaluationError(EvaluationProblem.WRONG_PARTITION, report.partition.value)
+        raise EvaluationError(EvaluationProblem.WRONG_PARTITION, "partition")
     results = []
     for gate in gates.gates:
         figure = report.figure(gate.metric)
--- a/packages/earnings-themes/src/earnings_themes/evaluation/calibration.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/calibration.py
@@ -39,10 +39,17 @@
 )
 from earnings_themes.evaluation.preregistration import Preregistration
 from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
-from earnings_themes.evaluation.records import Real, content_hash, sealed
+from earnings_themes.evaluation.records import Real, sealed
 from earnings_themes.evaluation.verdicts import families, family_judgement
 from earnings_themes.extraction.records import RunRecord
-from earnings_themes.records import IdPart, NonBlank, Part, Sha256Hex, ThemesRecord
+from earnings_themes.records import (
+    IdPart,
+    NonBlank,
+    Part,
+    Sha256Hex,
+    ThemesRecord,
+    hash_matches,
+)
 from earnings_themes.split import Partition
 from earnings_themes.support.metrics import (
     Acceptance,
@@ -116,7 +123,7 @@
     """One candidate's fitted cutoff, or ``None`` when no cutoff meets ρ."""

     candidate_id: IdPart
-    signals: PositiveInt
+    signals: Literal[1]
     cutoff: Real | None
     precision: Real | None
     recall: Real | None
@@ -275,7 +282,7 @@
     ``views`` are the MiniCheck support run's ``decision_inputs``; ``alternative``
     is DeBERTa's joint score by target; ``events`` maps each target to its event;
     ``configuration`` is ``frozen_configuration``'s."""
-    if content_hash(preregistration) != preregistration.content_hash:
+    if not hash_matches(preregistration):
         raise EvaluationError(
             EvaluationProblem.PREREGISTRATION_MISMATCH, "content_hash"
         )
--- a/packages/earnings-themes/src/earnings_themes/evaluation/preregistration.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/preregistration.py
@@ -76,7 +76,7 @@
     candidate_id: IdPart
     rule: Literal["scorer_cutoff"]
     signal: Literal["minicheck_joint"]
-    signals: PositiveInt
+    signals: Literal[1]
     grid: Annotated[tuple[Share, ...], Field(min_length=1)]

     @model_validator(mode="after")
--- a/packages/earnings-themes/src/earnings_themes/evaluation/labels.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/labels.py
@@ -182,7 +182,14 @@
     labels, the added ones."""
     new = working.of(partition)
     if committed is None:
-        return working.model_copy(update={"labels": new})
+        return parse(
+            {
+                **working.model_dump(mode="json"),
+                "labels": [l.model_dump(mode="json") for l in new],
+            },
+            SupportLabelSet,
+            "labels",
+        )
     if committed.preregistration_hash != working.preregistration_hash:
         raise EvaluationError(EvaluationProblem.PREREGISTRATION_MISMATCH, "labels")
     old = committed.of(partition)
@@ -204,6 +211,12 @@
     kept = tuple(
         label for label in committed.labels if label.partition is not partition
     )
-    return committed.model_copy(
-        update={"labels": (*kept, *new), "train_extensions": extensions}
-    )
+    return parse(
+        {
+            **committed.model_dump(mode="json"),
+            "labels": [label.model_dump(mode="json") for label in (*kept, *new)],
+            "train_extensions": extensions,
+        },
+        SupportLabelSet,
+        "labels",
+    )
--- a/packages/earnings-themes/src/earnings_themes/evaluation/sampling.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/sampling.py
@@ -64,6 +64,10 @@
     pool: Sequence[PoolTarget], *, seed: int, size: int, cap: int
 ) -> tuple[str, ...]:
     """The sampled target IDs, in draw order."""
+    if type(size) is not int or size < 0:
+        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "size")
+    if type(cap) is not int or cap <= 0:
+        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "cap")
     if (duplicate := first_duplicate(t.target_id for t in pool)) is not None:
         raise EvaluationError(EvaluationProblem.DUPLICATE_TARGET, duplicate)
     themes: dict[str, dict[str, list[str]]] = {}
--- a/packages/earnings-themes/src/earnings_themes/evaluation/policy.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/policy.py
@@ -15,7 +15,7 @@
 from earnings_themes.coding.records import PolicyReference, PolicyVote
 from earnings_themes.evaluation.calibration import CalibrationArtifact, ScorerCutoff
 from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
-from earnings_themes.evaluation.records import content_hash
+from earnings_themes.records import hash_matches
 from earnings_themes.support.records import CodebookReference


@@ -30,7 +30,7 @@
         classifier_configuration_hash: str,
         support_configuration_hash: str,
     ) -> None:
-        if content_hash(artifact) != artifact.content_hash:
+        if not hash_matches(artifact):
             raise EvaluationError(
                 EvaluationProblem.CONTENT_HASH_MISMATCH, "content_hash"
             )
```

Apply the matching dictionary rows in this implementation step:

```diff
--- a/docs/data-dictionary.md
+++ b/docs/data-dictionary.md
@@ -6625,7 +6625,7 @@
 | `label` | `feasibility-only` (R12.2) |
 | `preregistration_hash` | The preregistration it follows |
 | `calibration_hash` | The calibration artifact whose policy it scores |
-| `partitions` | Train's and dev's `PartitionReport` |
+| `partitions` | Exactly one train and one dev `PartitionReport`, in either order; duplicate or missing partitions refuse |
 | `independent` | Each dev event's `IndependentFigures` |
 | `content_hash` | Digest of every other field |

@@ -6768,7 +6768,7 @@
 | `candidate_id` | The candidate |
 | `rule` | `scorer_cutoff` |
 | `signal` | `minicheck_joint` |
-| `signals` | How many signals it reads, for the tie-break |
+| `signals` | Exactly `1`: the MiniCheck joint signal; the tie-break field is retained |
 | `grid` | Its cutoffs, sorted |

 ### `SelectionRule`
@@ -6837,7 +6837,7 @@
 | Field | Meaning |
 | --- | --- |
 | `candidate_id` | The candidate |
-| `signals` | Signals it reads |
+| `signals` | Exactly `1`, matching the single-signal `Candidate` |
 | `cutoff` | The fitted cutoff, or null when none meets ρ |
 | `precision` | Train labelled precision there against the joint label, or null |
 | `recall` | Train label recall there against the joint label, or null |
@@ -6948,3 +6948,24 @@
 ID/hash, documents and codebook, and require support targets to be among the
 proposals. The existing support gate establishes unique outcomes in target order.
 The application applies it to both support runs before calibration or reporting.
+
+### `HashedRecord`
+
+A nonpersisted structural `Protocol` bounding `sealed` and `checked`; its existing
+record implementations keep their fields and serialized schema. The shared
+comparison is `hash_matches(record: HashedRecord) -> bool`. `checked` maps a failed
+comparison to `RecordError`; calibration maps it to `preregistration_mismatch`,
+and the calibrated policy maps it to `content_hash_mismatch`.
+
+| Member | Meaning |
+| --- | --- |
+| `content_hash` | The stored digest of every other serialized field |
+| `model_dump` | JSON-compatible serialization used by the shared content digest |
+| `model_copy` | Immutable reconstruction used to fill the content hash |
+
+### Preregistered gate boundary
+
+`derive_gates(report, *, rule: GateRule, judge_floor, preregistration_hash,
+version=1)` takes and rechecks the preregistered rule; an arbitrary metric list or
+undefined-gate string cannot replace it. Gate wrong-partition errors name
+`partition`.
```

- [x] **Step 4: Run the scoped green check and changed-file Ruff**

```bash
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/evaluation/test_boundary_tidy.py --tb=short -q
uv run --locked --offline --no-sync ruff check packages/earnings-themes/src/earnings_themes/records.py packages/earnings-themes/src/earnings_themes/evaluation/records.py packages/earnings-themes/src/earnings_themes/evaluation/gates.py packages/earnings-themes/src/earnings_themes/evaluation/calibration.py packages/earnings-themes/src/earnings_themes/evaluation/preregistration.py packages/earnings-themes/src/earnings_themes/evaluation/labels.py packages/earnings-themes/src/earnings_themes/evaluation/sampling.py packages/earnings-themes/src/earnings_themes/evaluation/policy.py packages/earnings-themes/tests/evaluation/test_boundary_tidy.py packages/earnings-themes/tests/evaluation/test_gates.py packages/earnings-themes/tests/evaluation/test_records.py packages/earnings-themes/tests/evaluation/test_calibration.py
uv run --locked --offline --no-sync ruff format --check packages/earnings-themes/src/earnings_themes/records.py packages/earnings-themes/src/earnings_themes/evaluation/records.py packages/earnings-themes/src/earnings_themes/evaluation/gates.py packages/earnings-themes/src/earnings_themes/evaluation/calibration.py packages/earnings-themes/src/earnings_themes/evaluation/preregistration.py packages/earnings-themes/src/earnings_themes/evaluation/labels.py packages/earnings-themes/src/earnings_themes/evaluation/sampling.py packages/earnings-themes/src/earnings_themes/evaluation/policy.py packages/earnings-themes/tests/evaluation/test_boundary_tidy.py packages/earnings-themes/tests/evaluation/test_gates.py packages/earnings-themes/tests/evaluation/test_records.py packages/earnings-themes/tests/evaluation/test_calibration.py
```

Expected: all selected tests pass and Ruff is clean. Record the actual counts.


Run the static dictionary contracts in both the red and green steps:

```bash
uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_data_dictionary.py --tb=short -q
uv run --locked --offline --no-sync ruff check tests/contracts/test_data_dictionary.py
uv run --locked --offline --no-sync ruff format --check tests/contracts/test_data_dictionary.py
```

Before the rows exist, the newly added dictionary checks fail for the missing table/contract. After code and rows are applied, they pass. Stage `docs/data-dictionary.md` and `tests/contracts/test_data_dictionary.py` in this task's commit along with its listed code files.

- [x] **Step 5: Commit this task during the later authorized execution**

```bash
git log -3 --oneline
git add packages/earnings-themes/src/earnings_themes/records.py packages/earnings-themes/src/earnings_themes/evaluation/records.py packages/earnings-themes/src/earnings_themes/evaluation/gates.py packages/earnings-themes/src/earnings_themes/evaluation/calibration.py packages/earnings-themes/src/earnings_themes/evaluation/preregistration.py packages/earnings-themes/src/earnings_themes/evaluation/labels.py packages/earnings-themes/src/earnings_themes/evaluation/sampling.py packages/earnings-themes/src/earnings_themes/evaluation/policy.py packages/earnings-themes/tests/evaluation/test_boundary_tidy.py packages/earnings-themes/tests/evaluation/test_gates.py packages/earnings-themes/tests/evaluation/test_records.py packages/earnings-themes/tests/evaluation/test_calibration.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(pilot): validate evaluation boundaries and share the content-hash check"
```

---

### Task 3: Expose evaluation helpers and close document-binding errors

**Files:**

- Modify: `packages/earnings-themes/src/earnings_themes/annotation.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/label_view.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/__init__.py`
- Create: `packages/earnings-themes/tests/evaluation/test_public_api.py`
- Modify: `packages/earnings-themes/tests/test_gold.py`
- Modify: `packages/earnings-themes/tests/evaluation/test_cells.py`

- Modify: `docs/data-dictionary.md`
- Modify: `tests/contracts/test_data_dictionary.py`

**Interfaces:**

Produces check_countable(gold:Gold,*,event_id:str,pin:Pin,split:SplitManifest,codebook:Codebook,doc_id:str|None=None)->list[Refusal]. Stage6/A8 coverage callers supply doc_id=parsed_documents[event_id]. Root evaluation exports joint_score, sealed, claim_label, joint_label, Figure, ReadingAgreement, IndependentFigures, EvidenceTally and configuration_hash. label_views keeps its signature; callers must reverify_support_run first.

- [x] **Step 1: Write the exact test changes**

```diff
--- a/packages/earnings-themes/tests/evaluation/test_public_api.py
+++ b/packages/earnings-themes/tests/evaluation/test_public_api.py
@@ -0,0 +1,39 @@
+"""Public consumer helpers and closed view errors, using invented records."""
+
+from dataclasses import replace
+
+import pytest
+from earnings_themes import evaluation
+from earnings_themes.evaluation.label_view import label_views
+from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
+
+
+@pytest.mark.parametrize(
+    "name",
+    [
+        "joint_score",
+        "sealed",
+        "claim_label",
+        "joint_label",
+        "Figure",
+        "ReadingAgreement",
+        "IndependentFigures",
+        "EvidenceTally",
+        "configuration_hash",
+    ],
+)
+def test_application_helpers_are_exported(name):
+    assert name in evaluation.__all__
+    assert getattr(evaluation, name) is not None
+
+
+def test_label_view_missing_evidence_document_is_a_closed_error(assessed_case):
+    case = assessed_case
+    evidence = case.support.evidence[0].model_copy(update={"doc_id": "absent"})
+    altered = replace(case.support, evidence=(evidence,))
+    with pytest.raises(EvaluationError) as refused:
+        label_views(altered, case.sources, (case.support.targets[0].target_id,))
+    assert (refused.value.problem, refused.value.subject) == (
+        EvaluationProblem.MALFORMED_RECORD,
+        "evidence.doc_id",
+    )
--- a/packages/earnings-themes/tests/test_gold.py
+++ b/packages/earnings-themes/tests/test_gold.py
@@ -116,7 +116,11 @@
         "rejected": 1,
         "added": 3,
     }
-    assert gold.claims[1].origin is Origin.DRAFTED_EDITED
+    assert [(claim.claim_id, claim.origin) for claim in gold.claims] == [
+        ("c1", Origin.DRAFTED_ACCEPTED),
+        ("c2", Origin.DRAFTED_EDITED),
+        ("c3", Origin.ANNOTATOR_ADDED),
+    ]
     assert gold.quotes[3].origin is Origin.ANNOTATOR_ADDED
     assert gold.drafting_aid.model_dump() == AID
     assert check(gold, bundles, codebook) == []
@@ -160,6 +164,35 @@
     assert build(bundles, codebook, draft) == [refusal]


+def test_working_quote_anchor_refusal_keeps_the_drafted_duplicate_refusal(
+    bundles, codebook
+) -> None:
+    drafted = gold_draft()
+    drafted["quotes"].append(dict(drafted["quotes"][0]))
+    working = gold_draft()
+    working["quotes"][0]["text"] = "Invented absent wording."
+    refusals = build(bundles, codebook, drafted, working)
+    assert refusals == [
+        Refusal("draft quote q1", "duplicate_id"),
+        Refusal("quote q1", "locator_not_found"),
+    ]
+
+
+def test_countable_binds_the_current_parsed_document_id(bundles, codebook) -> None:
+    gold = build(bundles, codebook, gold_draft(annotator=SIGNED))
+    assert isinstance(gold, Gold)
+    options = {
+        "event_id": TRAIN,
+        "pin": PIN,
+        "split": synthetic_split(),
+        "codebook": codebook,
+    }
+    assert check_countable(gold, doc_id=gold.doc_id, **options) == []
+    assert check_countable(gold, doc_id="other-document", **options) == [
+        Refusal("doc_id", "wrong_document")
+    ]
+
+
 def test_ids_themes_and_ties_are_checked(bundles, codebook, fixtures) -> None:
     """Every ID resolves and every quote is cited, in a bundle's gold and in each
     fixture of the curated set; every claim in a bundle's gold takes an assignment
--- a/packages/earnings-themes/tests/evaluation/test_cells.py
+++ b/packages/earnings-themes/tests/evaluation/test_cells.py
@@ -122,7 +122,7 @@
     """``EventCells.evidence`` holds ``EvidenceCell``s, so both are public."""
     assert {"EventCells", "EvidenceCell"} <= set(evaluation.__all__)
     assert evaluation.EvidenceCell is EvidenceCell
-    assert len(evaluation.__all__) == len(set(evaluation.__all__)) == 46
+    assert len(evaluation.__all__) == len(set(evaluation.__all__)) == 55


 def test_level_one_maps_each_theme_to_its_root() -> None:
```

The same task adds its dictionary contract test:

```diff
--- a/tests/contracts/test_data_dictionary.py
+++ b/tests/contracts/test_data_dictionary.py
@@ -695,6 +695,12 @@
     )


+def test_current_document_and_label_rendering_boundaries_documented():
+    text = DICTIONARY.read_text(encoding="utf-8")
+    assert "check_countable(..., doc_id=parsed_document_id)" in text
+    assert "field path `evidence.doc_id`" in text
+
+
 EVALUATION_MODELS = [
     bootstrap.BootstrapPlan,
     bootstrap.Interval,
```

- [x] **Step 2: Run the scoped red check**

```bash
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/evaluation/test_public_api.py packages/earnings-themes/tests/test_gold.py::test_countable_binds_the_current_parsed_document_id packages/earnings-themes/tests/test_gold.py::test_working_quote_anchor_refusal_keeps_the_drafted_duplicate_refusal packages/earnings-themes/tests/test_gold.py::test_origins_come_from_comparing_the_working_copy_with_the_draft --tb=short -q
```

Expected: exports are missing, the missing evidence document yields StopIteration, and the doc_id keyword is absent; the existing gold-characterization checks already pass. Record actual failure/pass counts.

- [x] **Step 3: Apply the exact library changes**

```diff
--- a/packages/earnings-themes/src/earnings_themes/annotation.py
+++ b/packages/earnings-themes/src/earnings_themes/annotation.py
@@ -596,6 +596,7 @@
     pin: Pin,
     split: SplitManifest,
     codebook: Codebook,
+    doc_id: str | None = None,
 ) -> list[Refusal]:
     """Every reason a committed gold file's ``no_theme`` may not be counted for
     ``event_id`` in coverage v2, read without its document: its event, pin, split,
@@ -605,6 +606,8 @@
     refusals = []
     if gold.event_id != event_id:
         refusals.append(Refusal("event_id", Problem.UNKNOWN_DOCUMENT))
+    if doc_id is not None and gold.doc_id != doc_id:
+        refusals.append(Refusal("doc_id", RejectionReason.WRONG_DOCUMENT))
     return refusals + _standing(
         gold, event_id=event_id, pin=pin, split=split, codebook=codebook
     )
--- a/packages/earnings-themes/src/earnings_themes/evaluation/label_view.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/label_view.py
@@ -34,7 +34,11 @@
 def _quote(
     text: str, sources: SupportSources, evidence: EvidenceReference
 ) -> list[str]:
-    bundle = next(b for b in sources.bundles if b.document.doc_id == evidence.doc_id)
+    bundle = next(
+        (b for b in sources.bundles if b.document.doc_id == evidence.doc_id), None
+    )
+    if bundle is None:
+        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "evidence.doc_id")
     context = context_elements(bundle, evidence.element_id)
     block = context[-1].span
     start, end = evidence.start, evidence.end
--- a/packages/earnings-themes/src/earnings_themes/evaluation/__init__.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/__init__.py
@@ -16,7 +16,9 @@
 from earnings_themes.evaluation.calibration import (
     CalibrationArtifact,
     calibrate,
+    configuration_hash,
     frozen_configuration,
+    joint_score,
 )
 from earnings_themes.evaluation.cells import (
     EventCells,
@@ -35,6 +37,8 @@
     SupportLabel,
     SupportLabelSet,
     check_labels,
+    claim_label,
+    joint_label,
     labels_toml,
     load_labels,
     merge_labels,
@@ -48,11 +52,15 @@
 )
 from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
 from earnings_themes.evaluation.records import (
+    Figure,
     Gates,
     GateVerdict,
+    IndependentFigures,
     Metric,
     PartitionReport,
     PilotReport,
+    ReadingAgreement,
+    sealed,
 )
 from earnings_themes.evaluation.report import (
     Accepted,
@@ -63,6 +71,7 @@
     stability_figures,
 )
 from earnings_themes.evaluation.sampling import PoolTarget, label_pool, sample_targets
+from earnings_themes.evaluation.scores import EvidenceTally

 __all__ = [
     "Accepted",
@@ -75,8 +84,11 @@
     "EventCells",
     "EventObservation",
     "EvidenceCell",
+    "EvidenceTally",
+    "Figure",
     "GateVerdict",
     "Gates",
+    "IndependentFigures",
     "Interval",
     "LabelledTarget",
     "Metric",
@@ -84,12 +96,15 @@
     "PilotReport",
     "PoolTarget",
     "Preregistration",
+    "ReadingAgreement",
     "SupportLabel",
     "SupportLabelSet",
     "UnitIndex",
     "calibrate",
     "check_labels",
+    "claim_label",
     "compare_readings",
+    "configuration_hash",
     "derive_gates",
     "estimate",
     "evaluate_gates",
@@ -97,6 +112,8 @@
     "freeze_preregistration",
     "frozen_configuration",
     "gates_toml",
+    "joint_label",
+    "joint_score",
     "label_pool",
     "label_views",
     "labels_toml",
@@ -108,6 +125,7 @@
     "partition_report",
     "preregistration_toml",
     "sample_targets",
+    "sealed",
     "stability_figures",
     "unit_index",
     "units_over",
```

Apply the matching dictionary rows in this implementation step:

```diff
--- a/docs/data-dictionary.md
+++ b/docs/data-dictionary.md
@@ -6969,3 +6969,11 @@
 version=1)` takes and rechecks the preregistered rule; an arbitrary metric list or
 undefined-gate string cannot replace it. Gate wrong-partition errors name
 `partition`.
+
+### Gold and rendering consumer boundaries
+
+`check_countable(..., doc_id=parsed_document_id)` binds a gold file to
+the current parsed document ID without loading text; mismatches return `doc_id:
+wrong_document`. `label_views` remains a pure renderer, and its application caller
+must reverify support before rendering. A missing evidence document closes as
+`malformed_record`, with field path `evidence.doc_id`.
```

- [x] **Step 4: Run the scoped green check and changed-file Ruff**

```bash
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/evaluation/test_public_api.py packages/earnings-themes/tests/test_gold.py::test_countable_binds_the_current_parsed_document_id packages/earnings-themes/tests/test_gold.py::test_working_quote_anchor_refusal_keeps_the_drafted_duplicate_refusal packages/earnings-themes/tests/test_gold.py::test_origins_come_from_comparing_the_working_copy_with_the_draft --tb=short -q
uv run --locked --offline --no-sync ruff check packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/src/earnings_themes/evaluation/label_view.py packages/earnings-themes/src/earnings_themes/evaluation/__init__.py packages/earnings-themes/tests/evaluation/test_public_api.py packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/evaluation/test_cells.py
uv run --locked --offline --no-sync ruff format --check packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/src/earnings_themes/evaluation/label_view.py packages/earnings-themes/src/earnings_themes/evaluation/__init__.py packages/earnings-themes/tests/evaluation/test_public_api.py packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/evaluation/test_cells.py
```

Expected: all selected tests pass and Ruff is clean. Record the actual counts.


Run the static dictionary contracts in both the red and green steps:

```bash
uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_data_dictionary.py --tb=short -q
uv run --locked --offline --no-sync ruff check tests/contracts/test_data_dictionary.py
uv run --locked --offline --no-sync ruff format --check tests/contracts/test_data_dictionary.py
```

Before the rows exist, the newly added dictionary checks fail for the missing table/contract. After code and rows are applied, they pass. Stage `docs/data-dictionary.md` and `tests/contracts/test_data_dictionary.py` in this task's commit along with its listed code files.

- [x] **Step 5: Commit this task during the later authorized execution**

```bash
git log -3 --oneline
git add packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/src/earnings_themes/evaluation/label_view.py packages/earnings-themes/src/earnings_themes/evaluation/__init__.py packages/earnings-themes/tests/evaluation/test_public_api.py packages/earnings-themes/tests/test_gold.py packages/earnings-themes/tests/evaluation/test_cells.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(pilot): expose evaluation helpers and close document-binding errors"
```

Consumer check after the green step (all invented):

```bash
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/evaluation/test_cells.py --tb=short -q
```

---

### Task 4: Retain report counts and validate stability IDs

**Files:**

- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/cells.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/scores.py`
- Modify: `packages/earnings-themes/src/earnings_themes/evaluation/report.py`
- Create: `packages/earnings-themes/tests/evaluation/test_report_tidy.py`
- Modify: `packages/earnings-themes/tests/evaluation/test_report.py`

- Modify: `docs/data-dictionary.md`
- Modify: `tests/contracts/test_data_dictionary.py`

**Interfaces:**

Produces stability_figures(runs:Sequence[Sequence[EventObservation]],codebook:Codebook,plan:BootstrapPlan,*,run_ids:Sequence[str])->tuple[Figure,...]. Application supplies the verified fresh run IDs, and appends returned figures to dev PartitionReport.figures. Shared cells.quote_spans and scores.gs5_counts serve existing consumers. No hard_negative_counts return-shape change and no tie-evidence algorithm change.

- [x] **Step 1: Write the exact test changes**

> Deviation: Owner approved scalar assertions that keep failure output free of record wording; RED output thereafter was captured and surfaced only as names, closed reasons and counts.

```diff
--- a/packages/earnings-themes/tests/evaluation/test_report_tidy.py
+++ b/packages/earnings-themes/tests/evaluation/test_report_tidy.py
@@ -0,0 +1,99 @@
+"""Counts and stability diagnostics, over invented readings and observations."""
+
+from dataclasses import replace
+
+import pytest
+from earnings_themes.evaluation.align import unit_index
+from earnings_themes.evaluation.cells import event_cells
+from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
+from earnings_themes.evaluation.records import Metric
+from earnings_themes.evaluation.report import (
+    compare_readings,
+    partition_report,
+    stability_figures,
+)
+from earnings_themes.evaluation.scores import hard_negative_counts
+from earnings_themes.gold import DraftCounts, NegativeKind
+from earnings_themes.split import Partition
+
+from .cases import example, negative, reading
+from .test_report import BOOK, PLAN, observations
+
+
+def test_gs5_figures_retain_the_counts_and_their_denominator():
+    rows = observations()
+    counts = (
+        DraftCounts(accepted=3, edited=1, rejected=2, added=1),
+        DraftCounts(accepted=2, edited=1, rejected=1, added=3),
+    )
+    rows = tuple(
+        replace(o, gold=o.gold.model_copy(update={"counts": c}))
+        for o, c in zip(rows, counts, strict=True)
+    )
+    report = partition_report(rows, (), BOOK, PLAN, partition=Partition.DEV)
+    for metric, numerator, denominator in (
+        (Metric.GS5_EDITED_SHARE, 2, 10),
+        (Metric.GS5_REJECTED_SHARE, 3, 10),
+        (Metric.GS5_ADDED_SHARE, 4, 11),
+    ):
+        assert dict(report.figure(metric).counts) == {
+            "accepted": 5,
+            "edited": 2,
+            "rejected": 3,
+            "added": 4,
+            "numerator": numerator,
+            "denominator": denominator,
+        }
+
+
+def test_stability_requires_unique_run_ids():
+    rows = observations()
+    with pytest.raises(EvaluationError) as refused:
+        stability_figures((rows, rows), BOOK, PLAN, run_ids=("fresh1", "fresh1"))
+    assert (refused.value.problem, refused.value.subject) == (
+        EvaluationProblem.MALFORMED_RECORD,
+        "fresh1",
+    )
+
+
+def test_stability_refuses_a_duplicate_event_by_run_and_event_id():
+    rows = observations()
+    with pytest.raises(EvaluationError) as refused:
+        stability_figures(
+            ((*rows, rows[0]), (*rows, rows[0])),
+            BOOK,
+            PLAN,
+            run_ids=("fresh1", "fresh2"),
+        )
+    assert (refused.value.problem, refused.value.subject) == (
+        EvaluationProblem.MALFORMED_RECORD,
+        "fresh1:e1",
+    )
+
+
+def test_stability_names_the_run_with_a_different_event_set():
+    rows = observations()
+    with pytest.raises(EvaluationError) as refused:
+        stability_figures((rows, rows[:1]), BOOK, PLAN, run_ids=("fresh1", "fresh2"))
+    assert refused.value.subject == "fresh2"
+
+
+@pytest.mark.parametrize("ids", [(), ("fresh1",), ("fresh1", " ")])
+def test_stability_refuses_invalid_run_ids(ids):
+    rows = observations()
+    with pytest.raises(EvaluationError) as refused:
+        stability_figures((rows, rows), BOOK, PLAN, run_ids=ids)
+    assert refused.value.problem is EvaluationProblem.MALFORMED_RECORD
+    assert refused.value.subject == "run_ids"
+
+
+def test_negative_dangling_quotes_are_tolerated_counted_and_not_false_hits():
+    source, complete = example()
+    missing = reading(
+        negatives=(negative("n-missing", "absent", NegativeKind.PERIOD, "capacity"),)
+    )
+    index = unit_index(source)
+    assert event_cells(missing, index).dangling == 1
+    assert hard_negative_counts(missing, index, {}) == {NegativeKind.PERIOD: (1, 0)}
+    assert compare_readings(complete, missing, index).dangling == 1
+    assert compare_readings(missing, missing, index).dangling == 2
--- a/packages/earnings-themes/tests/evaluation/test_report.py
+++ b/packages/earnings-themes/tests/evaluation/test_report.py
@@ -546,7 +546,7 @@

 def test_stability_over_identical_and_empty_runs() -> None:
     runs = observations()
-    same = stability_figures((runs, runs), BOOK, PLAN)
+    same = stability_figures((runs, runs), BOOK, PLAN, run_ids=("fresh1", "fresh2"))
     by_metric = {f.metric: f.point for f in same}
     assert by_metric == {
         Metric.STABILITY_FLEISS_KAPPA: pytest.approx(1.0),
@@ -559,7 +559,12 @@
         )
         for o in runs
     )
-    apart = {f.metric: f.point for f in stability_figures((runs, empty), BOOK, PLAN)}
+    apart = {
+        f.metric: f.point
+        for f in stability_figures(
+            (runs, empty), BOOK, PLAN, run_ids=("fresh1", "fresh2")
+        )
+    }
     assert apart[Metric.STABILITY_FLEISS_KAPPA] == pytest.approx(-0.2)
     assert apart[Metric.STABILITY_UNIT_JACCARD] == 0.0
     # Every resample holds an event with accepted pairs in the first run (e1: four,
@@ -567,4 +572,4 @@
     # union, and the mean over the one pair of runs is 0.
     assert apart[Metric.STABILITY_ASSIGNMENT_JACCARD] == 0.0
     with pytest.raises(EvaluationError, match="malformed_record"):
-        stability_figures((runs,), BOOK, PLAN)
+        stability_figures((runs,), BOOK, PLAN, run_ids=("fresh1",))
```

The same task adds its dictionary contract test:

```diff
--- a/tests/contracts/test_data_dictionary.py
+++ b/tests/contracts/test_data_dictionary.py
@@ -701,6 +701,14 @@
     assert "field path `evidence.doc_id`" in text


+def test_stage11_application_metric_vocabulary_documented():
+    assert documented("Scorer-view vocabulary") == {"minicheck", "deberta"}
+    text = DICTIONARY.read_text(encoding="utf-8")
+    assert "| `minicheck` | `minicheck_joint` |" in text
+    assert "| `deberta` | `deberta_joint` |" in text
+    assert "accepted, edited, rejected, added, numerator and denominator" in text
+
+
 EVALUATION_MODELS = [
     bootstrap.BootstrapPlan,
     bootstrap.Interval,
```

- [x] **Step 2: Run the scoped red check**

```bash
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/evaluation/test_report_tidy.py --tb=short -q
```

Expected: counts, the run_ids keyword and the negative dangling-reference counter are absent. Record actual failures.

- [x] **Step 3: Apply the exact library changes**

> Deviation: Owner approved a closed missing-heading dictionary refusal instead of printing the dictionary excerpt.

```diff
--- a/packages/earnings-themes/src/earnings_themes/evaluation/cells.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/cells.py
@@ -105,6 +105,11 @@
     return roots


+def quote_spans(reading: GoldReading) -> dict[str, Span]:
+    """The shared quote-ID to canonical span map for cells and hard negatives."""
+    return {quote.quote_id: (quote.start, quote.end) for quote in reading.quotes}
+
+
 def event_cells(
     reading: GoldReading,
     index: UnitIndex,
@@ -118,11 +123,13 @@
         return theme_id if theme_map is None else theme_map.get(theme_id, theme_id)

     predicted = frozenset(predicted)
-    quotes = {q.quote_id: (q.start, q.end) for q in reading.quotes}
+    quotes = quote_spans(reading)
     claims = {c.claim_id: c.quote_ids for c in reading.claims}
-    dangling = sum(q not in quotes for ids in claims.values() for q in ids) + sum(
-        a.claim_id not in claims for a in reading.assignments
-    )
+    dangling = sum(
+        q not in quotes
+        for claim in (*reading.claims, *reading.hard_negatives)
+        for q in claim.quote_ids
+    ) + sum(a.claim_id not in claims for a in reading.assignments)
     rows = [
         (a.claim_id, mapped(a.theme_id), a.support, a.tie_group)
         for a in reading.assignments
--- a/packages/earnings-themes/src/earnings_themes/evaluation/scores.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/scores.py
@@ -16,7 +16,7 @@
     covered,
     units_over,
 )
-from earnings_themes.evaluation.cells import EventCells, GoldReading
+from earnings_themes.evaluation.cells import EventCells, GoldReading, quote_spans
 from earnings_themes.gold import DraftCounts, NegativeKind, ReleaseLabel


@@ -204,7 +204,7 @@
     """Per negative kind (R12.5): the hard negatives that name a theme, and those
     falsely accepted, by an accepted assignment to that theme whose evidence units
     overlap the negative's."""
-    quotes = {q.quote_id: (q.start, q.end) for q in reading.quotes}
+    quotes = quote_spans(reading)
     out: dict[NegativeKind, tuple[int, int]] = {}
     for negative in reading.hard_negatives:
         if negative.theme_id is None:
@@ -229,14 +229,22 @@
     )


+def gs5_counts(counts: Iterable[DraftCounts]) -> dict[str, int]:
+    """The shared summed source counts behind each GS5 share."""
+    rows = tuple(counts)
+    return {
+        name: sum(getattr(row, name) for row in rows)
+        for name in ("accepted", "edited", "rejected", "added")
+    }
+
+
 def gs5_shares(counts: Iterable[DraftCounts]) -> dict[str, float | None]:
     """GS5's shares over summed counts: edited and rejected over drafted items,
     added over signed items (D19-9)."""
-    rows = list(counts)
-    accepted = sum(c.accepted for c in rows)
-    edited = sum(c.edited for c in rows)
-    rejected = sum(c.rejected for c in rows)
-    added = sum(c.added for c in rows)
+    totals = gs5_counts(counts)
+    accepted, edited, rejected, added = (
+        totals[name] for name in ("accepted", "edited", "rejected", "added")
+    )
     drafted = accepted + edited + rejected
     return {
         "edited": ratio(edited, drafted),
--- a/packages/earnings-themes/src/earnings_themes/evaluation/report.py
+++ b/packages/earnings-themes/src/earnings_themes/evaluation/report.py
@@ -46,6 +46,7 @@
     char_counts,
     evidence_recall_counts,
     f1,
+    gs5_counts,
     gs5_shares,
     hard_negative_counts,
     macro_f1,
@@ -320,12 +321,23 @@
         _counts(rare_themes=len(rare)),
     )
     counts = {e: x.observation.gold.counts for e, x in events.items()}
+    totals = gs5_counts(counts.values())
     for metric, key in (
         (Metric.GS5_EDITED_SHARE, "edited"),
         (Metric.GS5_REJECTED_SHARE, "rejected"),
         (Metric.GS5_ADDED_SHARE, "added"),
     ):
-        figures.add(metric, counts, lambda drawn, k=key: gs5_shares(drawn)[k])
+        denominator = (
+            totals["accepted"]
+            + totals["edited"]
+            + totals["added" if key == "added" else "rejected"]
+        )
+        figures.add(
+            metric,
+            counts,
+            lambda drawn, k=key: gs5_shares(drawn)[k],
+            _counts(**totals, numerator=totals[key], denominator=denominator),
+        )
     no_theme = {e: x.observation.gold.no_theme for e, x in events.items()}
     figures.add(
         Metric.NO_THEME_SHARE,
@@ -498,16 +510,32 @@
     runs: Sequence[Sequence[EventObservation]],
     codebook: Codebook,
     plan: BootstrapPlan,
+    *,
+    run_ids: Sequence[str],
 ) -> tuple[Figure, ...]:
     """FP12's k fresh runs over one partition's events (R12.10): Fleiss' κ over
     event × theme presence, for every codebook theme, and the mean pairwise Jaccard
     of the runs' accepted evidence units and of their accepted (theme, unit)
     pairs."""
+    if (
+        isinstance(run_ids, str | bytes)
+        or len(run_ids) != len(runs)
+        or any(type(run_id) is not str or not run_id.strip() for run_id in run_ids)
+    ):
+        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "run_ids")
+    if (duplicate := first_duplicate(run_ids)) is not None:
+        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, duplicate)
     if len(runs) < 2:
         raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "runs")
+    for run_id, run in zip(run_ids, runs, strict=True):
+        if (duplicate := first_duplicate(o.event_id for o in run)) is not None:
+            raise EvaluationError(
+                EvaluationProblem.MALFORMED_RECORD, f"{run_id}:{duplicate}"
+            )
     events = sorted(o.event_id for o in runs[0])
-    if any(sorted(o.event_id for o in run) != events for run in runs):
-        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "runs")
+    for run_id, run in zip(run_ids, runs, strict=True):
+        if sorted(o.event_id for o in run) != events:
+            raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, run_id)
     themes = sorted(t.theme_id for t in codebook.themes)
     per_event: dict[str, tuple[tuple[frozenset, frozenset, frozenset], ...]] = {}
     for event_id in events:
```

Apply the matching dictionary rows in this implementation step:

```diff
--- a/docs/data-dictionary.md
+++ b/docs/data-dictionary.md
@@ -6419,7 +6419,7 @@
 members are excused; for unit and character scoring the group stays one evidence
 cell, which any member's evidence covers, and an accepted unit or character is one
 hit however many cells hold it. A theme whose every row is `uncertain` is left out
-and counted. A claim's reference to a quote, or any assignment's reference to a
+and counted. A claim or hard negative's reference to a quote, or any assignment's reference to a
 claim, that the reading lacks is counted as dangling, one per reference. The roll-up
 maps both sides to level-one roots. Gold-evidence recall counts the gold-supporting
 units any accepted assignment holds. GS5's edited and rejected shares are over
@@ -6463,7 +6463,7 @@
 | `units` | Each present theme's gold-supporting units |
 | `spans` | Each present theme's gold-supporting spans |
 | `evidence` | The `EvidenceCell`s unit and character scoring read: each present theme's own untied evidence, then each tie group's |
-| `dangling` | References the reading cannot resolve, one each: a claim's quote the reading lacks, and any assignment's claim it lacks, whatever its support, theme or tie (D19-7) |
+| `dangling` | References the reading cannot resolve, one each: a claim or hard negative's quote the reading lacks, and any assignment's claim it lacks, whatever its support, theme or tie; tolerated and counted (D19-7) |

 ### `EvidenceCell`

@@ -6587,7 +6587,7 @@
 | `qualifier` | A family, `family:presentation`, a scorer view, or a negative kind; null when the metric is reported once |
 | `point` | The point estimate, or null when undefined |
 | `interval` | Its `Interval`; null exactly when the metric is not estimated |
-| `counts` | Named counts behind the figure, sorted by name |
+| `counts` | Named counts behind the figure, sorted by name; GS5 figures retain accepted, edited, rejected, added, numerator and denominator |
 | `reason` | Why the metric is not estimated; null otherwise |

 ### `PartitionReport`
@@ -6606,7 +6606,7 @@
 | `release_agrees` | Whether the two release-identification labels agree |
 | `theme_f1` | Exact theme F1 of one reading against the other |
 | `unit_f1` | Unit F1 of their evidence |
-| `dangling` | Dangling references in either reading |
+| `dangling` | Sum of both readings' dangling quote and claim references, including hard-negative quote references; tolerated, never refused |

 ### `IndependentFigures`

@@ -6703,7 +6703,7 @@
 | `claim_label` | The user's claim label, or null when unsure |
 | `joint_label` | The joint label, or null |
 | `accepted` | Whether the run accepted it |
-| `scores` | Each scorer view's joint score |
+| `scores` | Named joint scores keyed `minicheck` and `deberta`; see the scorer-view vocabulary below |
 | `trials` | Its four judge trials |

 ### `ClaimAnswer`
@@ -6977,3 +6977,27 @@
 wrong_document`. `label_views` remains a pure renderer, and its application caller
 must reverify support before rendering. A missing evidence document closes as
 `malformed_record`, with field path `evidence.doc_id`.
+
+### Report counts and stability identities
+
+`stability_figures(runs, codebook, plan, *, run_ids)` requires one unique nonblank
+ID per run and unique events within each run. Different event sets refuse with
+the offending run ID; repeated events name the run and event. `quote_spans`
+provides the shared canonical quote map used by event cells and hard-negative
+scoring; negative dangling references remain tolerated and counted. `gs5_counts`
+is the shared sum behind GS5 shares and their figure counts. Edited and rejected
+shares use accepted + edited + rejected as denominator; added shares use accepted
++ edited + added.
+
+Stability figures remain in dev's `PartitionReport.figures`.
+
+### `Scorer-view vocabulary`
+
+The report uses short scorer qualifiers and score-map keys. Calibration's raw
+`MetricReport.view` names retain the joint scope. Both score against the
+`claim_support` label; support precision separately uses `joint_support`.
+
+| Report qualifier / score-map key | MetricReport.view | Meaning |
+| --- | --- | --- |
+| `minicheck` | `minicheck_joint` | Primary MiniCheck joint score |
+| `deberta` | `deberta_joint` | Alternative DeBERTa joint score, reported only |
```

- [x] **Step 4: Run the scoped green check and changed-file Ruff**

```bash
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/evaluation/test_report_tidy.py --tb=short -q
uv run --locked --offline --no-sync ruff check packages/earnings-themes/src/earnings_themes/evaluation/cells.py packages/earnings-themes/src/earnings_themes/evaluation/scores.py packages/earnings-themes/src/earnings_themes/evaluation/report.py packages/earnings-themes/tests/evaluation/test_report_tidy.py packages/earnings-themes/tests/evaluation/test_report.py
uv run --locked --offline --no-sync ruff format --check packages/earnings-themes/src/earnings_themes/evaluation/cells.py packages/earnings-themes/src/earnings_themes/evaluation/scores.py packages/earnings-themes/src/earnings_themes/evaluation/report.py packages/earnings-themes/tests/evaluation/test_report_tidy.py packages/earnings-themes/tests/evaluation/test_report.py
```

Expected: all selected tests pass and Ruff is clean. Record the actual counts.


Run the static dictionary contracts in both the red and green steps:

```bash
uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_data_dictionary.py --tb=short -q
uv run --locked --offline --no-sync ruff check tests/contracts/test_data_dictionary.py
uv run --locked --offline --no-sync ruff format --check tests/contracts/test_data_dictionary.py
```

Before the rows exist, the newly added dictionary checks fail for the missing table/contract. After code and rows are applied, they pass. Stage `docs/data-dictionary.md` and `tests/contracts/test_data_dictionary.py` in this task's commit along with its listed code files.

- [x] **Step 5: Commit this task during the later authorized execution**

```bash
git log -3 --oneline
git add packages/earnings-themes/src/earnings_themes/evaluation/cells.py packages/earnings-themes/src/earnings_themes/evaluation/scores.py packages/earnings-themes/src/earnings_themes/evaluation/report.py packages/earnings-themes/tests/evaluation/test_report_tidy.py packages/earnings-themes/tests/evaluation/test_report.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(pilot): retain report counts and validate stability ids"
```

---

### Task 5: Share Stage 6 selections and close the legacy command gaps

**Files:**

- Modify: `apps/earnings-pipeline/src/earnings_pipeline/stage6.py`
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py`
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py`
- Modify: `apps/earnings-pipeline/tests/test_stage6_cli.py`
- Modify: `packages/earnings-ingestion/tests/test_events_coverage.py`

**Interfaces:**

Consumes Task 3's `check_countable(gold, *, event_id, pin, split, codebook, doc_id=None)`. Produces the public `Events` argument alias and the following helpers in `earnings_pipeline.stage6`:

```python
committed_gold(layout: Layout, pinned: Pinned, event_ids: list[str] | None, *, require_nonempty: bool = False) -> list[tuple[Path, Gold]]
kept_drafts(layout: Layout, event_id: str) -> tuple[Path, Path]
independent_path(layout: Layout, event_id: str) -> Path
read_ledger(pinned: Pinned) -> IndependentLedger | None
require_train_dev(event_id: str, partition: Partition) -> None
```

The list return enables whole-selection partition preflight before bundle loading. This is owner-approved D20-10 (P20-B). Gold anchor retains its existing `--check` fallback to the kept draft when a working copy is absent. Both gold and pilot commands call the same helpers; existing Stage 6 output contracts remain in the user gate.

- [x] **Step 1: Add the exact tests**

```diff
diff --git a/apps/earnings-pipeline/tests/test_stage6_cli.py b/apps/earnings-pipeline/tests/test_stage6_cli.py
index 32539ee..d6c807e 100644
--- a/apps/earnings-pipeline/tests/test_stage6_cli.py
+++ b/apps/earnings-pipeline/tests/test_stage6_cli.py
@@ -31,7 +31,7 @@ from earnings_ingestion.events.state_table import read_runs, write_run
 from earnings_ingestion.events.states import DocumentState
 from earnings_ingestion.fetch.responses import UnexpectedResponse
 from earnings_ingestion.fetch.store import ArtifactStore
-from earnings_pipeline import cli, gold_cli
+from earnings_pipeline import cli, gold_cli, pilot_cli, stage6
 from earnings_pipeline.stage6 import (
     Layout,
     documents,
@@ -1272,6 +1272,7 @@ def test_recount_reports_counts_that_do_not_rebuild_by_event_and_field(repo) ->
     twice["quotes"].append(dict(twice["quotes"][0]))
     write_drafts(repo, FIRST, twice, gold_draft(annotator=SIGNED))
     repeated = run(repo, "pilot", "recount")
+    assert repeated.exit_code == 1
     assert lines(repeated) == [
         f"refused: {FIRST} draft quote q1: duplicate_id",
         "Refused: 1 problem(s); GS5's shares wait until each is resolved",
@@ -1337,6 +1338,323 @@ def test_coverage_takes_versions_1_and_2_and_v2_needs_v1(repo) -> None:
     assert not (repo / EVALUATION / "coverage-v2.json").exists()


+PLAN20_MARKER = "INVENTED_PRIVATE_MARKER_FOR_STAGE11_LEGACY_COMMANDS"
+
+
+@pytest.fixture
+def plan20_repo(tmp_path: Path, acquired: Path) -> Path:
+    """Only invented acquisition inputs; no Stage 1 source text is copied/read."""
+    ignore = shutil.ignore_patterns("raw")
+    for directory in (COHORT_MANIFEST.parent, FIXTURE_DIR):
+        shutil.copytree(REPO / directory, tmp_path / directory, ignore=ignore)
+    (tmp_path / CANONICAL).mkdir(parents=True)
+    (tmp_path / RELEASES).parent.mkdir(parents=True)
+    (tmp_path / RELEASES).write_text("fixtures = []\n", encoding="utf-8")
+    shutil.copytree(acquired / "data", tmp_path / "data")
+    return tmp_path
+
+
+def plan20_run(repo: Path, *args: str):
+    result = run(repo, "pilot", *args)
+    assert PLAN20_MARKER not in result.output
+    return result
+
+
+def plan20_draft(event_id: str = FIRST, **changes) -> dict:
+    return gold_draft(
+        event_id,
+        claims=[{"claim_id": "c1", "quote_ids": ["q1"], "claim": PLAN20_MARKER}],
+        **changes,
+    )
+
+
+def plan20_sign(repo: Path, event_ids: tuple[str, ...] = (FIRST,)) -> None:
+    for event_id in event_ids:
+        write_drafts(
+            repo,
+            event_id,
+            plan20_draft(event_id),
+            plan20_draft(event_id, annotator=SIGNED),
+        )
+    result = run(repo, "gold", "anchor", *event_ids)
+    assert result.exit_code == 0, result.output
+    assert PLAN20_MARKER not in result.output
+
+
+def plan20_coverage(repo: Path) -> None:
+    assert plan20_run(repo, "coverage").exit_code == 0
+    split = load_split(repo / EVALUATION / "split-v1.json")
+    events = tuple(e for e in split.events_in(Partition.TRAIN) if e not in UNPARSED)
+    plan20_sign(repo, events)
+
+
+def test_plan20_shared_paths_and_committed_gold_selection(plan20_repo) -> None:
+    frozen(plan20_repo)
+    layout = Layout(
+        plan20_repo, COHORT_MANIFEST, FIXTURE_DIR / "pilot-v1.json", PILOT_HASH
+    )
+    pinned = load_pinned(layout)
+    assert stage6.committed_gold(layout, pinned, None) == []
+    plan20_sign(plan20_repo)
+    path = plan20_repo / EVALUATION / "gold" / f"{FIRST_FILE}.toml"
+    assert stage6.committed_gold(layout, pinned, None) == [(path, load_gold(path))]
+    assert stage6.committed_gold(layout, pinned, [FIRST]) == [(path, load_gold(path))]
+    assert stage6.kept_drafts(layout, FIRST) == (
+        plan20_repo / DRAFTS / f"{FIRST_FILE}.draft.toml",
+        plan20_repo / DRAFTS / f"{FIRST_FILE}.working.toml",
+    )
+    assert stage6.independent_path(layout, FIRST) == (
+        plan20_repo / INDEPENDENT_DIR / f"{FIRST_FILE}.toml"
+    )
+    assert stage6.read_ledger(pinned) is None
+    write_ledger(plan20_repo, [ledger_row(FIRST, "0" * 64)])
+    assert stage6.read_ledger(pinned).rows[0].event_id == FIRST
+
+
+def test_plan20_empty_selection_preserves_each_commands_contract(plan20_repo) -> None:
+    frozen(plan20_repo)
+    before = snapshot(plan20_repo)
+    valid = run(plan20_repo, "gold", "validate")
+    assert valid.exit_code == 0, valid.output
+    assert lines(valid) == [f"no gold committed under {EVALUATION}/gold"]
+    result = plan20_run(plan20_repo, "recount")
+    assert result.exit_code == 1
+    assert lines(result) == [f"Refused: no gold is committed under {EVALUATION}/gold"]
+    assert snapshot(plan20_repo) == before
+
+
+def test_plan20_recount_stem_mismatch_writes_nothing(plan20_repo) -> None:
+    frozen(plan20_repo)
+    plan20_sign(plan20_repo)
+    folder = plan20_repo / EVALUATION / "gold"
+    renamed = folder / f"{SECOND.replace(':', '_')}.toml"
+    (folder / f"{FIRST_FILE}.toml").rename(renamed)
+    before = snapshot(plan20_repo)
+    result = plan20_run(plan20_repo, "recount")
+    assert result.exit_code == 1
+    assert lines(result) == [
+        f"Refused: {renamed.relative_to(plan20_repo).as_posix()} holds the gold of {FIRST}"
+    ]
+    assert snapshot(plan20_repo) == before
+
+
+def test_plan20_recount_missing_working_copy_writes_nothing(plan20_repo) -> None:
+    frozen(plan20_repo)
+    plan20_sign(plan20_repo)
+    (plan20_repo / DRAFTS / f"{FIRST_FILE}.working.toml").unlink()
+    before = snapshot(plan20_repo)
+    result = plan20_run(plan20_repo, "recount")
+    assert result.exit_code == 1
+    assert lines(result) == [
+        (
+            f"Refused: {FIRST}: {DRAFTS.as_posix()}/{FIRST_FILE}.working.toml is not"
+            " here; GS5's counts rebuild from the kept draft and its working copy"
+        )
+    ]
+    assert snapshot(plan20_repo) == before
+
+
+@pytest.mark.parametrize("kind", ["gold", "draft", "working"])
+def test_plan20_recount_unreadable_record_names_fields_not_text(
+    plan20_repo, kind
+) -> None:
+    frozen(plan20_repo)
+    plan20_sign(plan20_repo)
+    path = (
+        plan20_repo / EVALUATION / "gold" / f"{FIRST_FILE}.toml"
+        if kind == "gold"
+        else plan20_repo / DRAFTS / f"{FIRST_FILE}.{kind}.toml"
+    )
+    path.write_text(f'quotes = ["{PLAN20_MARKER}",\n', encoding="utf-8")
+    before = snapshot(plan20_repo)
+    result = plan20_run(plan20_repo, "recount")
+    assert result.exit_code == 1
+    assert lines(result) == [
+        f"problem: {path.name}: not TOML at line 2, column 1",
+        f"Refused: {path.name} does not read as its record",
+    ]
+    assert snapshot(plan20_repo) == before
+
+
+def test_plan20_recount_repeated_kept_id_refuses_and_writes_nothing(
+    plan20_repo,
+) -> None:
+    frozen(plan20_repo)
+    plan20_sign(plan20_repo)
+    twice = plan20_draft()
+    twice["quotes"].append(dict(twice["quotes"][0]))
+    write_drafts(plan20_repo, FIRST, twice, plan20_draft(annotator=SIGNED))
+    before = snapshot(plan20_repo)
+    result = plan20_run(plan20_repo, "recount")
+    assert result.exit_code == 1
+    assert lines(result) == [
+        f"refused: {FIRST} draft quote q1: duplicate_id",
+        "Refused: 1 problem(s); GS5's shares wait until each is resolved",
+    ]
+    assert snapshot(plan20_repo) == before
+
+
+def test_plan20_recount_preflights_all_selected_partitions(
+    plan20_repo, monkeypatch
+) -> None:
+    frozen(plan20_repo)
+    layout = Layout(
+        plan20_repo, COHORT_MANIFEST, FIXTURE_DIR / "pilot-v1.json", PILOT_HASH
+    )
+    pinned = load_pinned(layout)
+    parsed = documents(layout, pinned)
+    split = load_split(pinned.split_path)
+    selected = tuple(e for e in split.events_in(Partition.TRAIN) if e in parsed)[:2]
+    plan20_sign(plan20_repo, selected)
+    held_back = selected[1]
+    path = pinned.gold_dir / f"{held_back.replace(':', '_')}.toml"
+    record = load_gold(path).model_copy(update={"partition": Partition.TEST})
+    path.write_text(gold_toml(record), encoding="utf-8")
+
+    def forbidden_bundle(*args, **kwargs):
+        raise AssertionError(PLAN20_MARKER)
+
+    monkeypatch.setattr(pilot_cli, "load_bundle", forbidden_bundle)
+    before = snapshot(plan20_repo)
+    result = plan20_run(plan20_repo, "recount")
+    assert result.exit_code == 1
+    assert lines(result) == [
+        (
+            f"Refused: {held_back} is a test bundle; pilot evaluation takes train"
+            " and dev only"
+        )
+    ]
+    assert snapshot(plan20_repo) == before
+
+
+def test_plan20_legacy_success_paths_keep_markers_private(plan20_repo) -> None:
+    frozen(plan20_repo)
+    plan20_sign(plan20_repo)
+    before = snapshot(plan20_repo)
+    recounted = plan20_run(plan20_repo, "recount", FIRST)
+    assert recounted.exit_code == 0, recounted.output
+    assert lines(recounted) == [
+        f"recounted {FIRST} (train): accepted 3, edited 0, rejected 0, added 0",
+        "recounted 1 file(s): each rebuilds from its kept draft",
+    ]
+    assert snapshot(plan20_repo) == before
+    plan20_coverage(plan20_repo)
+    covered = plan20_run(plan20_repo, "coverage", "--version", "2")
+    assert covered.exit_code == 0, covered.output
+    before = snapshot(plan20_repo)
+    repeated = plan20_run(plan20_repo, "coverage", "--version", "2")
+    assert repeated.exit_code == 0, repeated.output
+    assert "unchanged: coverage v2" in repeated.output
+    assert snapshot(plan20_repo) == before
+
+
+@pytest.mark.parametrize("command", ["recount", "coverage"])
+@pytest.mark.parametrize("partition", [Partition.TEST, Partition.EXCLUDED])
+@pytest.mark.parametrize("changed", ["record", "split"])
+def test_plan20_legacy_commands_refuse_held_back_partitions_before_text(
+    plan20_repo, monkeypatch, command, partition, changed
+) -> None:
+    frozen(plan20_repo)
+    if command == "coverage":
+        plan20_coverage(plan20_repo)
+    else:
+        plan20_sign(plan20_repo)
+    if changed == "record":
+        path = plan20_repo / EVALUATION / "gold" / f"{FIRST_FILE}.toml"
+        record = load_gold(path).model_copy(update={"partition": partition})
+        path.write_text(gold_toml(record), encoding="utf-8")
+    else:
+        lookup = SplitManifest.partition_of
+
+        def partition_of(self, event_id):
+            return partition if event_id == FIRST else lookup(self, event_id)
+
+        monkeypatch.setattr(SplitManifest, "partition_of", partition_of)
+
+    def forbidden_bundle(*args, **kwargs):
+        raise AssertionError(PLAN20_MARKER)
+
+    monkeypatch.setattr(pilot_cli, "load_bundle", forbidden_bundle)
+    before = snapshot(plan20_repo)
+    args = ("--version", "2") if command == "coverage" else ()
+    result = plan20_run(plan20_repo, command, *args)
+    assert result.exit_code == 1
+    assert lines(result) == [
+        (
+            f"Refused: {FIRST} is a {partition} bundle; pilot evaluation takes train"
+            " and dev only"
+        )
+    ]
+    assert snapshot(plan20_repo) == before
+
+
+def test_plan20_coverage_unreadable_gold_names_record_not_text(plan20_repo) -> None:
+    frozen(plan20_repo)
+    plan20_coverage(plan20_repo)
+    path = plan20_repo / EVALUATION / "gold" / f"{FIRST_FILE}.toml"
+    path.write_text(f'quotes = ["{PLAN20_MARKER}",\n', encoding="utf-8")
+    before = snapshot(plan20_repo)
+    result = plan20_run(plan20_repo, "coverage", "--version", "2")
+    assert result.exit_code == 1
+    assert lines(result) == [
+        f"problem: {path.name}: not TOML at line 2, column 1",
+        f"Refused: {path.name} does not read as its record",
+    ]
+    assert snapshot(plan20_repo) == before
+
+
+def test_plan20_coverage_checks_parsed_document_id_without_loading_text(
+    plan20_repo, monkeypatch
+) -> None:
+    frozen(plan20_repo)
+    plan20_coverage(plan20_repo)
+    path = plan20_repo / EVALUATION / "gold" / f"{FIRST_FILE}.toml"
+    record = load_gold(path).model_copy(update={"doc_id": "another-invented-doc"})
+    path.write_text(gold_toml(record), encoding="utf-8")
+
+    def forbidden_bundle(*args, **kwargs):
+        raise AssertionError(PLAN20_MARKER)
+
+    monkeypatch.setattr(pilot_cli, "load_bundle", forbidden_bundle)
+    before = snapshot(plan20_repo)
+    result = plan20_run(plan20_repo, "coverage", "--version", "2")
+    assert result.exit_code == 1
+    assert lines(result) == [
+        f"refused: {FIRST} doc_id: wrong_document",
+        "Refused: 1 problem(s); nothing written",
+    ]
+    assert snapshot(plan20_repo) == before
+
+
+@pytest.mark.parametrize("command", ["recount", "coverage"])
+def test_plan20_legacy_commands_withhold_unforeseen_exception_text(
+    plan20_repo, monkeypatch, command
+) -> None:
+    frozen(plan20_repo)
+    if command == "coverage":
+        plan20_coverage(plan20_repo)
+    else:
+        plan20_sign(plan20_repo)
+
+    def broken(*args, **kwargs):
+        raise ValueError(PLAN20_MARKER)
+
+    monkeypatch.setattr(
+        pilot_cli, "check_countable" if command == "coverage" else "recount", broken
+    )
+    before = snapshot(plan20_repo)
+    args = ("--version", "2") if command == "coverage" else ()
+    result = plan20_run(plan20_repo, command, *args)
+    assert result.exit_code == 1
+    assert lines(result) == [
+        (
+            "Refused: an unforeseen ValueError; its message is withheld, since it"
+            " may quote a document (GS13)"
+        )
+    ]
+    assert snapshot(plan20_repo) == before
+
+
 def test_coverage_v2_waits_for_every_train_and_dev_bundle_s_gold(repo) -> None:
     """The Stage 11 spec's A7: version 2 is refused until every train and dev
     bundle with a parsed document has signed gold, and each is named."""
```

```diff
diff --git a/packages/earnings-ingestion/tests/test_events_coverage.py b/packages/earnings-ingestion/tests/test_events_coverage.py
index 3812704..62dac8d 100644
--- a/packages/earnings-ingestion/tests/test_events_coverage.py
+++ b/packages/earnings-ingestion/tests/test_events_coverage.py
@@ -11,6 +11,7 @@ from earnings_ingestion.cohort.freeze import load_manifest
 from earnings_ingestion.events.coverage import (
     AppliedOverride,
     CoverageGap,
+    CoverageReport,
     NoThemeCount,
     build_coverage,
     load_coverage,
@@ -263,3 +264,18 @@ def test_no_theme_rows_are_bounded_counted_once_and_absent_from_v1(synthetic) ->
         build_coverage(pilot, pin, transitions, version=2, no_theme=[train, train])
     with pytest.raises(ValueError, match="coverage v1 holds no no-theme count"):
         build_coverage(pilot, pin, transitions, no_theme=[train])
+
+
+def test_coverage_record_refuses_dev_before_train_without_builder_sorting(
+    synthetic,
+) -> None:
+    """P17-2(5): exercise the record's ordering gate, not the builder's sort."""
+    pilot, pin, transitions = synthetic
+    report = build_coverage(pilot, pin, transitions, version=2)
+    rows = (
+        NoThemeCount(partition="dev", bundles=1, no_theme=0),
+        NoThemeCount(partition="train", bundles=2, no_theme=1),
+    )
+    fields = {**report.model_dump(), "no_theme": rows}
+    with pytest.raises(ValueError, match="in train, dev, test order"):
+        CoverageReport.model_validate(fields)
```

- [x] **Step 2: Observe red, and the already-correct coverage regression**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -k plan20 --tb=short -q
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-ingestion/tests/test_events_coverage.py --tb=short -q
```

The first fails for the missing shared selector, test/excluded gates occurring after attempted bundle loading, and coverage accepting an incorrect parsed document ID. The remaining refusal and no-write cases already pass. The second characterizes the existing validator and already passes: a hand-built dev-before-train tuple is rejected even though the builder normally sorts it. Do not run the entire Stage 6 CLI file as an agent; its legacy source fixtures are outside this plan's current invented-only scope.

- [x] **Step 3: Apply the shared-helper and command changes**

```diff
diff --git a/apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py b/apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py
index e96e300..85cf62e 100644
--- a/apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py
+++ b/apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py
@@ -55,12 +55,7 @@ from earnings_themes.gold import (
     load_gold,
     load_hard_negatives,
 )
-from earnings_themes.independent import (
-    LEDGER,
-    IndependentLedger,
-    ledger_problem,
-    load_ledger,
-)
+from earnings_themes.independent import ledger_problem
 from earnings_themes.records import RecordError
 from earnings_themes.split import Partition, SplitManifest
 from earnings_themes.view import render_curated_view, render_text, render_view
@@ -70,16 +65,21 @@ from earnings_pipeline.stage6 import (
     CODEBOOK_FILE,
     FIXTURE_MANIFEST,
     HARD_NEGATIVES,
+    Events,
     Layout,
     Pinned,
+    committed_gold,
     documents,
     fail,
     file_stem,
     guarded,
+    independent_path,
+    kept_drafts,
     load_bundle,
     load_fixture,
     load_pinned,
     options,
+    read_ledger,
     record_error,
     refuse,
     replace,
@@ -92,7 +92,6 @@ gold = typer.Typer(no_args_is_help=True, help="Stage 6's gold set.")
 gold.callback()(options)
 CURATED = "hard-negatives"

-Events = Annotated[list[str] | None, typer.Argument(help="Event IDs.")]
 Curated = Annotated[
     bool, typer.Option("--hard-negatives", help="The curated hard negatives.")
 ]
@@ -143,8 +142,7 @@ def _open(layout: Layout, split: SplitManifest, event_id: str) -> None:
 def _drafts(layout: Layout, name: str, check: bool) -> tuple[Path, Path]:
     """The kept draft and the working copy. ``--check`` without a working copy
     checks the draft alone, as a drafting session checks its own."""
-    drafted = layout.drafts / f"{file_stem(name)}.draft.toml"
-    working = layout.drafts / f"{file_stem(name)}.working.toml"
+    drafted, working = kept_drafts(layout, name)
     if check and drafted.is_file() and not working.is_file():
         typer.echo(f"checking the draft alone: {name} has no working copy yet")
         working = drafted
@@ -158,29 +156,14 @@ def _drafts(layout: Layout, name: str, check: bool) -> tuple[Path, Path]:
     return drafted, working


-def _independent_path(layout: Layout, event_id: str) -> Path:
-    """The user's independent record of a dev bundle, local and never committed."""
-    return layout.gold_runs / "independent" / f"{file_stem(event_id)}.toml"
-
-
-def _read_ledger(pinned: Pinned) -> IndependentLedger | None:
-    """The pilot's independent-pass ledger, or ``None`` when none is committed. A
-    ledger that does not read is refused, naming its file and its problems only."""
-    path = pinned.evaluation / LEDGER
-    try:
-        return load_ledger(path) if path.is_file() else None
-    except RecordError as error:
-        record_error(error)
-
-
 def _guard(layout: Layout, pinned: Pinned, split: SplitManifest, event_id: str) -> None:
     """GS19: a dev bundle's draft is neither anchored nor shown until the user's
     independent record exists and matches its ledger row. Only a dev bundle reads
     the ledger or the record, so train and test are unchanged."""
     if split.partition_of(event_id) is not Partition.DEV:
         return
-    ledger = _read_ledger(pinned)
-    record = _independent_path(layout, event_id)
+    ledger = read_ledger(pinned)
+    record = independent_path(layout, event_id)
     found = record.read_bytes() if record.is_file() else None
     if (reason := ledger_problem(ledger, event_id, found)) is not None:
         fail(f"Refused: {event_id} {reason}")
@@ -219,13 +202,13 @@ def _check_independent(
             f"Refused: {event_id}: {layout.shown(existing[0])} exists; the"
             " independent pass comes before the draft (GS19)"
         )
-    ledger = _read_ledger(pinned)
+    ledger = read_ledger(pinned)
     if ledger is not None and any(row.event_id == event_id for row in ledger.rows):
         fail(
             f"Refused: {event_id}: the independent record already has a ledger row;"
             " --independent --check runs before its row is committed (GS19)"
         )
-    path = _independent_path(layout, event_id)
+    path = independent_path(layout, event_id)
     if not path.is_file():
         fail(
             f"Refused: {event_id}: {layout.shown(path)} is not here; the user"
@@ -491,14 +474,8 @@ def _validate_event(
     codebook: Codebook,
     doc_ids: dict[str, str],
     texts: dict[str, str],
-    path: Path,
+    record: Gold,
 ) -> int:
-    try:
-        record: Gold = load_gold(path)
-    except RecordError as error:
-        record_error(error)
-    if path.stem != file_stem(record.event_id):
-        fail(f"Refused: {layout.shown(path)} holds the gold of {record.event_id}")
     split = pinned_split(layout, pinned)
     bundle = load_bundle(layout, doc_ids, record.event_id)
     refusals = validate_gold(
@@ -554,18 +531,14 @@ def validate_command(
     if hard_negatives:
         problems += _validate_curated(layout, pinned, codebook)
     if event_ids or not hard_negatives:
-        if event_ids:
-            paths = [pinned.gold_dir / f"{file_stem(e)}.toml" for e in event_ids]
-            missing = [p for p in paths if not p.is_file()]
-            if missing:
-                fail(f"Refused: {layout.shown(missing[0])} is not committed")
-        else:
-            paths = sorted(pinned.gold_dir.glob("*.toml"))
-            if not paths:
-                typer.echo(f"no gold committed under {layout.shown(pinned.gold_dir)}")
-        doc_ids = documents(layout, pinned) if paths else {}
-        texts = wording_texts(layout, pinned) if paths else {}
-        for path in paths:
-            problems += _validate_event(layout, pinned, codebook, doc_ids, texts, path)
+        records = committed_gold(layout, pinned, event_ids)
+        if not records:
+            typer.echo(f"no gold committed under {layout.shown(pinned.gold_dir)}")
+        doc_ids = documents(layout, pinned) if records else {}
+        texts = wording_texts(layout, pinned) if records else {}
+        for _, record in records:
+            problems += _validate_event(
+                layout, pinned, codebook, doc_ids, texts, record
+            )
     if problems:
         fail(f"Refused: {problems} problem(s)")
diff --git a/apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py b/apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py
index 20bb3b3..7794242 100644
--- a/apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py
+++ b/apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py
@@ -34,7 +34,7 @@ from earnings_ingestion.events.coverage import (
 from earnings_ingestion.events.freeze import serialize
 from earnings_themes.annotation import check_countable, load_gold_draft, recount
 from earnings_themes.codebook import Codebook
-from earnings_themes.gold import load_gold
+from earnings_themes.gold import Gold, load_gold
 from earnings_themes.problems import Refusal
 from earnings_themes.records import RecordError, record_json
 from earnings_themes.split import (
@@ -47,18 +47,22 @@ from earnings_themes.split import (

 from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
 from earnings_pipeline.stage6 import (
+    Events,
     Layout,
     Pinned,
+    committed_gold,
     documents,
     fail,
     file_stem,
     fixture_event_ids,
     guarded,
+    kept_drafts,
     load_bundle,
     load_pinned,
     options,
     record_error,
     refuse,
+    require_train_dev,
     transitions,
     write_once,
 )
@@ -143,8 +147,15 @@ def _no_theme(
                 gold = load_gold(path)
             except RecordError as error:
                 record_error(error)
+            require_train_dev(event_id, split.partition_of(event_id))
+            require_train_dev(event_id, gold.partition)
             found = check_countable(
-                gold, event_id=event_id, pin=pinned.pin, split=split, codebook=codebook
+                gold,
+                event_id=event_id,
+                pin=pinned.pin,
+                split=split,
+                codebook=codebook,
+                doc_id=parsed[event_id],
             )
             refusals += [Refusal(f"{event_id} {r.subject}", r.reason) for r in found]
             flags.append(gold.no_theme)
@@ -221,12 +232,6 @@ def coverage_command(context: typer.Context, version: Version = 1) -> None:
     typer.echo(f"{layout.shown(path)}  {report.content_hash}")


-Events = Annotated[
-    list[str] | None,
-    typer.Argument(help="Event IDs; every committed gold file when none is named."),
-]
-
-
 def _recount(
     layout: Layout,
     pinned: Pinned,
@@ -234,20 +239,12 @@ def _recount(
     codebook: Codebook,
     doc_ids: dict[str, str],
     path: Path,
+    record: Gold,
 ) -> int:
     """One committed gold file, rebuilt from its kept draft and working copy: its
     counts printed when it rebuilds, each refusal by event and field when not."""
-    try:
-        record = load_gold(path)
-    except RecordError as error:
-        record_error(error)
     event_id = record.event_id
-    if path.stem != file_stem(event_id):
-        fail(f"Refused: {layout.shown(path)} holds the gold of {event_id}")
-    kept = [
-        layout.drafts / f"{file_stem(event_id)}.{kind}.toml"
-        for kind in ("draft", "working")
-    ]
+    kept = kept_drafts(layout, event_id)
     for draft in kept:
         if not draft.is_file():
             fail(
@@ -289,20 +286,22 @@ def recount_command(context: typer.Context, event_ids: Events = None) -> None:
     codebook = pinned_codebook(layout)
     pinned = load_pinned(layout)
     split = pinned_split(layout, pinned)
-    if event_ids:
-        paths = [pinned.gold_dir / f"{file_stem(e)}.toml" for e in event_ids]
-        if missing := [p for p in paths if not p.is_file()]:
-            fail(f"Refused: {layout.shown(missing[0])} is not committed")
-    else:
-        paths = sorted(pinned.gold_dir.glob("*.toml"))
-        if not paths:
-            fail(f"Refused: no gold is committed under {layout.shown(pinned.gold_dir)}")
+    records = committed_gold(layout, pinned, event_ids, require_nonempty=True)
+    for _, record in records:
+        event_id = record.event_id
+        try:
+            partition = split.partition_of(event_id)
+        except KeyError:
+            fail(f"Refused: {event_id} is not in the split")
+        require_train_dev(event_id, partition)
+        require_train_dev(event_id, record.partition)
     doc_ids = documents(layout, pinned)
     problems = sum(
-        _recount(layout, pinned, split, codebook, doc_ids, path) for path in paths
+        _recount(layout, pinned, split, codebook, doc_ids, path, record)
+        for path, record in records
     )
     if problems:
         fail(
             f"Refused: {problems} problem(s); GS5's shares wait until each is resolved"
         )
-    typer.echo(f"recounted {len(paths)} file(s): each rebuilds from its kept draft")
+    typer.echo(f"recounted {len(records)} file(s): each rebuilds from its kept draft")
diff --git a/apps/earnings-pipeline/src/earnings_pipeline/stage6.py b/apps/earnings-pipeline/src/earnings_pipeline/stage6.py
index 4529875..e90c14a 100644
--- a/apps/earnings-pipeline/src/earnings_pipeline/stage6.py
+++ b/apps/earnings-pipeline/src/earnings_pipeline/stage6.py
@@ -45,8 +45,11 @@ from earnings_ingestion.events.states import StateTransition
 from earnings_ingestion.fetch.store import write_new
 from earnings_themes.anchoring import Bundle
 from earnings_themes.codebook import CODEBOOK_ID, CODEBOOK_VERSION
+from earnings_themes.gold import Gold, load_gold
+from earnings_themes.independent import LEDGER, IndependentLedger, load_ledger
 from earnings_themes.problems import Problem, Refusal
 from earnings_themes.records import Pin, RecordError
+from earnings_themes.split import Partition
 from earnings_themes.wording import labelled_strings, shared
 from pydantic import BaseModel

@@ -62,6 +65,10 @@ CODEBOOK_FILE = Path("codebooks") / CODEBOOK_ID / f"codebook-v{CODEBOOK_VERSION}
 FIXTURE_MANIFEST = Path("tests") / "fixtures" / "releases" / "manifest.toml"
 CANONICAL_FIXTURES = Path("tests") / "fixtures" / "canonical"
 HARD_NEGATIVES = Path("tests") / "fixtures" / "gold" / "hard-negatives.toml"
+Events = Annotated[
+    list[str] | None,
+    typer.Argument(help="Event IDs; every committed gold file when none is named."),
+]


 @dataclass(frozen=True)
@@ -113,6 +120,70 @@ def file_stem(event_id: str) -> str:
     return event_id.replace(":", "_")


+def kept_drafts(layout: Layout, event_id: str) -> tuple[Path, Path]:
+    """The kept draft and its working copy, under the event's portable file stem."""
+    stem = file_stem(event_id)
+    return (
+        layout.drafts / f"{stem}.draft.toml",
+        layout.drafts / f"{stem}.working.toml",
+    )
+
+
+def independent_path(layout: Layout, event_id: str) -> Path:
+    """The user's independent record of a dev bundle, local and never committed."""
+    return layout.gold_runs / "independent" / f"{file_stem(event_id)}.toml"
+
+
+def read_ledger(pinned: Pinned) -> IndependentLedger | None:
+    """The independent-pass ledger, or None if absent; malformed records refuse."""
+    path = pinned.evaluation / LEDGER
+    try:
+        return load_ledger(path) if path.is_file() else None
+    except RecordError as error:
+        record_error(error)
+
+
+def committed_gold(
+    layout: Layout,
+    pinned: Pinned,
+    event_ids: list[str] | None,
+    *,
+    require_nonempty: bool = False,
+) -> list[tuple[Path, Gold]]:
+    """Selected committed files, parsed and checked against their event stems.
+
+    Validation permits no committed files; recount requires at least one. Both
+    refuse missing named files, unreadable records and mismatched file stems.
+    """
+    if event_ids:
+        paths = [pinned.gold_dir / f"{file_stem(e)}.toml" for e in event_ids]
+        if missing := [path for path in paths if not path.is_file()]:
+            fail(f"Refused: {layout.shown(missing[0])} is not committed")
+    else:
+        paths = sorted(pinned.gold_dir.glob("*.toml"))
+    if require_nonempty and not paths:
+        fail(f"Refused: no gold is committed under {layout.shown(pinned.gold_dir)}")
+    selected = []
+    for path in paths:
+        try:
+            record = load_gold(path)
+        except RecordError as error:
+            record_error(error)
+        if path.stem != file_stem(record.event_id):
+            fail(f"Refused: {layout.shown(path)} holds the gold of {record.event_id}")
+        selected.append((path, record))
+    return selected
+
+
+def require_train_dev(event_id: str, partition: Partition) -> None:
+    """Stage 11 commands refuse held-back events before reading their text."""
+    if partition not in (Partition.TRAIN, Partition.DEV):
+        fail(
+            f"Refused: {event_id} is a {partition} bundle; pilot evaluation takes"
+            " train and dev only"
+        )
+
+
 def fail(message: str) -> NoReturn:
     typer.echo(message, err=True)
     raise typer.Exit(1)
```

- [x] **Step 4: Verify green and Ruff**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -k plan20 --tb=short -q
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-ingestion/tests/test_events_coverage.py --tb=short -q
uv run --locked --offline --no-sync ruff check apps/earnings-pipeline/src/earnings_pipeline/stage6.py apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/tests/test_stage6_cli.py packages/earnings-ingestion/tests/test_events_coverage.py
uv run --locked --offline --no-sync ruff format --check apps/earnings-pipeline/src/earnings_pipeline/stage6.py apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/tests/test_stage6_cli.py packages/earnings-ingestion/tests/test_events_coverage.py
```

Expected: all selected invented/synthetic cases pass and Ruff is clean. Report the actual counts.

- [x] **Step 5: Review and commit the task**

```bash
git log -3 --oneline
git add apps/earnings-pipeline/src/earnings_pipeline/stage6.py apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/tests/test_stage6_cli.py packages/earnings-ingestion/tests/test_events_coverage.py
git commit -m "refactor(pilot): share Stage 6 selections and guard legacy evaluation"
```

---

### Task 6: Extract typed workflow seams and constrain judge families

**Files:**

- Modify: `apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py`
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/theme_config.py`
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py`
- Create: `apps/earnings-pipeline/tests/test_pilot_seams.py`
- Modify: `docs/data-dictionary.md` and `tests/contracts/test_data_dictionary.py` for `WorkflowInputs`

**Interfaces:**

Consumes Task 1's `coding_configuration`, `source_bindings`, and the shared proposal/support coherence gate; the existing `support.records.support_configuration`; and `WorkflowRuntime`. Produces:

```python
parse_workflow_config(path: Path, *, repo: Path) -> WorkflowConfig
load_workflow_inputs(config: WorkflowConfig, runtime: WorkflowRuntime) -> WorkflowInputs
validate_workflow_policy(config: WorkflowConfig, policy: AssignmentPolicy | None) -> None
workflow_provenance(config: WorkflowConfig, expected: tuple[ExpectedEvent, ...], baseline: dict[str, StateTransition], metadata: tuple[DocumentMetadata, ...], canonical: tuple[CanonicalSnapshot, ...]) -> tuple[tuple[AcquisitionStatus, ...], str]
workflow_configuration_hashes(config: WorkflowConfig, sources: SupportSources, *, cache_mode: Literal["live", "replay", "fresh"] = "replay") -> tuple[str, str]
verify_extraction_configuration(config: WorkflowConfig, result: StoredRun, bundles: tuple[Bundle, ...], template: PromptTemplate) -> None
finalize_coding(proposal: ProposalRun, support: StoredSupportRun, sources: SupportSources, policy: AssignmentPolicy | None) -> CodingRun
```

`WorkflowInputs` is a frozen dataclass with expected events, invented/source bundles, document metadata, canonical snapshots, raw snapshots, codebook, prompt template, acquisition projections and provenance hash. Metadata parsing is shared, while the existing extraction-only configuration loader still refuses an assignment policy. A pass/fresh runner reads acquisition predecessors without writing processing transitions. The workflow keeps its terminal/self-or-descendant rule.

- [x] **Step 1: Write the exact seam tests**

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/tests/test_pilot_seams.py
@@ -0,0 +1,134 @@
+"""A8's shared workflow seams, with invented sources and no concrete runtime."""
+
+import importlib
+import json
+
+import pytest
+from earnings_core import digest
+from earnings_pipeline.model_runtime import ChatModelFile
+from earnings_pipeline.theme_config import WorkflowError, load_workflow_config
+from pydantic import ValidationError
+
+cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_workflow")
+model_cases = importlib.import_module("apps.earnings-pipeline.tests.test_model_runtime")
+
+
+def test_family_is_id_safe_before_hashing_or_loading(tmp_path):
+    fields = model_cases.chat_file(tmp_path, "invented", "unsafe family", 8080)
+    with pytest.raises(ValidationError):
+        ChatModelFile.model_validate_json(json.dumps(fields, default=str))
+
+
+def test_metadata_loader_shares_parse_confine_and_preserves_extract_policy_gate(
+    tmp_path,
+):
+    from earnings_pipeline.theme_config import parse_workflow_config
+    from earnings_themes.coding.records import PolicyReference
+
+    config, _ = cases.seed_case(tmp_path, seed=False, review=True)
+    path = tmp_path / "bound.json"
+    config = config.model_copy(
+        update={
+            "policy_reference": PolicyReference(
+                policy_id="calibrated-invented",
+                policy_hash="a" * 64,
+                kind="calibrated",
+                codebook={
+                    "codebook_id": "invented",
+                    "codebook_version": 0,
+                    "content_hash": "a" * 64,
+                },
+                classifier_configuration_hash="b" * 64,
+                support_configuration_hash="c" * 64,
+                calibration_reference="d" * 64,
+            )
+        }
+    )
+    path.write_text(config.model_dump_json())
+    parsed = parse_workflow_config(path, repo=tmp_path)
+    assert parsed.policy_reference == config.policy_reference
+    assert parsed.repo == tmp_path
+    with pytest.raises(WorkflowError, match="policy_unavailable"):
+        load_workflow_config(path, repo=tmp_path)
+
+
+def test_typed_inputs_and_hashes_use_the_same_library_configuration(tmp_path):
+    from earnings_pipeline.theme_workflow import (
+        load_workflow_inputs,
+        replay_runtime,
+        workflow_configuration_hashes,
+    )
+    from earnings_themes.coding.cache import CodingCache
+    from earnings_themes.coding.run import propose_run
+    from earnings_themes.support.records import SupportSources, support_configuration
+
+    config, _ = cases.seed_case(tmp_path, review=True)
+    runtime = replay_runtime(config)
+    loaded = load_workflow_inputs(config, runtime)
+    from earnings_themes.extraction.cache import CachedAdapter
+    from earnings_themes.extraction.run import extract_run
+    from earnings_themes.extraction.store import StoredRun
+
+    extraction = StoredRun.of(
+        extract_run(
+            loaded.bundles,
+            CachedAdapter(
+                runtime.extractor, tmp_path / config.extraction_cache, "replay"
+            ),
+            config.extraction_policy,
+            loaded.template,
+            config.extraction_ceilings,
+            run_id=config.extraction_run_id,
+            started_at=config.fixture_started_at,
+            software=config.software,
+        )
+    )
+    sources = SupportSources(
+        extraction, loaded.bundles, loaded.codebook, loaded.provenance_hash
+    )
+    proposal = propose_run(
+        config.coding_run_id,
+        sources,
+        tuple((c.doc_id, c.claim_id) for c in extraction.claims),
+        runtime.classifier,
+        config.coding_policy,
+        config.coding_ceilings,
+        cache=CodingCache(tmp_path / config.coding_cache, "replay"),
+        started_at=extraction.record.started_at,
+        software=config.software,
+    )
+    coding_hash, support_hash = workflow_configuration_hashes(config, sources)
+    assert coding_hash == proposal.record.configuration_hash
+    assert support_hash == digest(
+        support_configuration(
+            config.support_policy,
+            config.support_ceilings,
+            config.scorer_identity,
+            config.judge_identities,
+            config.extractor_family,
+            "replay",
+        )
+    )
+    assert all(
+        a.dispatch_calls == a.count_calls == 0
+        for a in (
+            runtime.extractor,
+            runtime.classifier,
+            runtime.scorer,
+            *runtime.judges,
+        )
+    )
+    assert loaded.acquisition
+    assert isinstance(loaded.provenance_hash, str)
+
+
+def test_shared_policy_reference_gate_refuses_unbound_policy(tmp_path):
+    from earnings_pipeline.theme_workflow import validate_workflow_policy
+
+    config, _ = cases.seed_case(tmp_path, seed=False, review=True)
+    validate_workflow_policy(config, None)
+    with pytest.raises(WorkflowError, match="policy_mismatch"):
+        validate_workflow_policy(config, object())
+    config = config.model_copy(update={"policy_reference": object()})
+    with pytest.raises(WorkflowError, match="policy_unavailable"):
+        validate_workflow_policy(config, None)
```

The same task adds its dictionary contract test:

```diff
--- a/tests/contracts/test_data_dictionary.py
+++ b/tests/contracts/test_data_dictionary.py
@@ -645,6 +645,7 @@
     model_runtime.ChatModelFile,
 ]
 WORKFLOW_DATACLASSES = [
+    theme_workflow.WorkflowInputs,
     theme_workflow.WorkflowRuntime,
     theme_workflow.WorkflowResult,
     model_runtime.LiveRuntime,
@@ -707,6 +708,14 @@
     assert "| `minicheck` | `minicheck_joint` |" in text
     assert "| `deberta` | `deberta_joint` |" in text
     assert "accepted, edited, rejected, added, numerator and denominator" in text
+
+
+def test_workflow_prebound_configuration_interface_documented():
+    text = DICTIONARY.read_text(encoding="utf-8")
+    assert (
+        "workflow_configuration_hashes(config: WorkflowConfig, sources: SupportSources,"
+        in text
+    )


 EVALUATION_MODELS = [
```

- [x] **Step 2: Observe the intended red failures**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_seams.py --tb=short -q
```

Expected: unsafe family does not raise yet, and imports of the two new shared input helpers fail. No runtime builder or native component is invoked.

- [x] **Step 3: Apply the shared extraction and typing changes**

> Deviation: Updated the required IdPart dictionary row; the two reviewed loader/hash docstrings were corrected with Task 7.

```diff
--- a/apps/earnings-pipeline/src/earnings_pipeline/theme_config.py
+++ b/apps/earnings-pipeline/src/earnings_pipeline/theme_config.py
@@ -270,13 +270,11 @@
     config._repo = repo.resolve()


-def load_workflow_config(path: Path, *, repo: Path) -> WorkflowConfig:
+def parse_workflow_config(path: Path, *, repo: Path) -> WorkflowConfig:
     """Read this JSON only, confine every selection before any source loading."""
     try:
         config = WorkflowConfig.model_validate_json(path.read_bytes())
         validate_paths(config, repo=repo)
-        if config.policy_reference is not None:
-            raise WorkflowError("policy_unavailable")
         return config
     except WorkflowError:
         raise
@@ -284,6 +282,14 @@
         raise WorkflowError("malformed_record") from None


+def load_workflow_config(path: Path, *, repo: Path) -> WorkflowConfig:
+    """The extract CLI still refuses an externally supplied assignment policy."""
+    config = parse_workflow_config(path, repo=repo)
+    if config.policy_reference is not None:
+        raise WorkflowError("policy_unavailable")
+    return config
+
+
 def read_selected(config: WorkflowConfig, selected: FileSelection) -> bytes:
     data = confined_path(config.repo, selected.path).read_bytes()
     if sha256_hex(data) != selected.sha256:
--- a/apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py
+++ b/apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py
@@ -44,7 +44,7 @@
 from earnings_themes.coding.local import ClassifierBinding
 from earnings_themes.coding.records import CodingError
 from earnings_themes.extraction.records import LOCAL_STRUCTURED, LOCAL_TIMEOUT_S
-from earnings_themes.records import NonBlank, RecordError, parse
+from earnings_themes.records import IdPart, NonBlank, RecordError, parse
 from earnings_themes.support.chat_tokens import ChatTokenCounter, ChatTokenizerConfig
 from earnings_themes.support.judges import JudgeBinding, validate_panel
 from earnings_themes.support.model_files import files_hash, verify_files
@@ -90,7 +90,7 @@
     identity, and its weights' and tokenizer's files, under directories relative to
     the models root."""

-    family: NonBlank
+    family: IdPart
     base_url: NonBlank
     model_id: NonBlank
     runtime: NonBlank
--- a/apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py
+++ b/apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py
@@ -20,6 +20,7 @@
     PROCESSING_PREDECESSOR_FIELDS,
     DocumentState,
     ProcessingTransition,
+    StateTransition,
     check_histories,
     current_states,
     in_order,
@@ -46,18 +47,21 @@
 )
 from earnings_themes.analysis.records import TABLE_SCHEMAS
 from earnings_themes.anchoring import Bundle
-from earnings_themes.codebook import load_codebook
+from earnings_themes.codebook import Codebook, load_codebook
 from earnings_themes.coding.adapters import Classifier
 from earnings_themes.coding.assignments import project_assignments
 from earnings_themes.coding.cache import CodingCache
 from earnings_themes.coding.decide import AssignmentPolicy, decide_assignments
 from earnings_themes.coding.records import (
+    CodingPolicySnapshot,
+    CodingReply,
     CodingRun,
     CodingRunRecord,
     PolicyReference,
     PolicyVote,
+    coding_configuration,
 )
-from earnings_themes.coding.run import ProposalRun, propose_run
+from earnings_themes.coding.run import ProposalRun, propose_run, source_bindings
 from earnings_themes.coding.store import SCHEMAS as CODING_SCHEMAS
 from earnings_themes.coding.store import (
     read_coding_run,
@@ -66,7 +70,7 @@
 )
 from earnings_themes.extraction.adapters import ModelAdapter
 from earnings_themes.extraction.cache import CachedAdapter
-from earnings_themes.extraction.prompt import parse_template
+from earnings_themes.extraction.prompt import PromptTemplate, parse_template
 from earnings_themes.extraction.run import extract_run
 from earnings_themes.extraction.store import SCHEMAS as EXTRACTION_SCHEMAS
 from earnings_themes.extraction.store import StoredRun, read_run, write_run
@@ -78,9 +82,10 @@
 )
 from earnings_themes.support.cache import SupportCache
 from earnings_themes.support.judges import Judge, validate_panel
-from earnings_themes.support.records import SupportSources
+from earnings_themes.support.records import SupportSources, support_configuration
 from earnings_themes.support.scorers import EntailmentScorer
 from earnings_themes.support.store import SCHEMAS as SUPPORT_SCHEMAS
+from earnings_themes.support.store import StoredSupportRun
 from pydantic import AwareDatetime, Field, model_validator

 from earnings_pipeline.evidence_views import make_evidence_view
@@ -380,6 +385,18 @@
     return _artifact(config, path)


+def validate_workflow_policy(
+    config: WorkflowConfig, policy: AssignmentPolicy | None
+) -> None:
+    if config.policy_reference is not None:
+        _require(
+            policy is not None and policy.reference == config.policy_reference,
+            "policy_unavailable",
+        )
+    elif config.assignment_policy is None:
+        _require(policy is None, "policy_mismatch")
+
+
 def _load_metadata(config, runtime):
     validate_paths(config, repo=config.repo)
     _require(
@@ -390,14 +407,7 @@
         "model_mismatch",
     )
     validate_panel(config.extractor_family, config.judge_identities)
-    if config.policy_reference is not None:
-        _require(
-            runtime.assignment_policy is not None
-            and runtime.assignment_policy.reference == config.policy_reference,
-            "policy_unavailable",
-        )
-    elif config.assignment_policy is None:
-        _require(runtime.assignment_policy is None, "policy_mismatch")
+    validate_workflow_policy(config, runtime.assignment_policy)
     for selected in (
         config.universe,
         config.events,
@@ -516,6 +526,102 @@
         book,
         template,
     )
+
+
+@dataclass(frozen=True, repr=False)
+class WorkflowInputs:
+    """Verified source inputs shared by the workflow and the pilot's phase runner."""
+
+    expected: tuple[ExpectedEvent, ...]
+    bundles: tuple[Bundle, ...]
+    metadata: tuple[DocumentMetadata, ...]
+    canonical: tuple[CanonicalSnapshot, ...]
+    raw: tuple[RawSnapshot, ...]
+    codebook: Codebook
+    template: PromptTemplate
+    acquisition: tuple[AcquisitionStatus, ...]
+    provenance_hash: str
+
+
+def workflow_provenance(
+    config: WorkflowConfig,
+    expected: tuple[ExpectedEvent, ...],
+    baseline: dict[str, StateTransition],
+    metadata: tuple[DocumentMetadata, ...],
+    canonical: tuple[CanonicalSnapshot, ...],
+) -> tuple[tuple[AcquisitionStatus, ...], str]:
+    acquisition = _projections(config, baseline, metadata)
+    provenance = analysis_provenance_hash(
+        selected_universe_hash=config.universe_hash,
+        expected=expected,
+        acquisition=acquisition,
+        metadata=metadata,
+        canonical_snapshots=canonical,
+    )
+    return acquisition, provenance
+
+
+def load_workflow_inputs(
+    config: WorkflowConfig, runtime: WorkflowRuntime
+) -> WorkflowInputs:
+    """Rebind the immutable acquisition inputs; read no processing output or state.
+
+    Pilot passes and fresh runs use the acquisition predecessors even after a normal
+    run records its separate processing transition. They never append a transition.
+    The workflow's terminal/self-or-descendant rule remains in `_baseline` unchanged.
+    """
+    expected, bundles, metadata, canonical, raw, book, template = _load_metadata(
+        config, runtime
+    )
+    history = _checked_history(config, confined_path(config.repo, config.states_dir))
+    baseline, _ = _baseline(
+        config, [s for s in history if not isinstance(s, ProcessingTransition)], None
+    )
+    acquisition, provenance = workflow_provenance(
+        config, expected, baseline, metadata, canonical
+    )
+    return WorkflowInputs(
+        expected,
+        bundles,
+        metadata,
+        canonical,
+        raw,
+        book,
+        template,
+        acquisition,
+        provenance,
+    )
+
+
+def workflow_configuration_hashes(
+    config: WorkflowConfig,
+    sources: SupportSources,
+    *,
+    cache_mode: Literal["live", "replay", "fresh"] = "replay",
+) -> tuple[str, str]:
+    """The replay coding/support hashes, before any policy is bound or voted."""
+    coding = coding_configuration(
+        **source_bindings(sources),
+        classifier_identity=config.classifier_identity,
+        coding_policy=CodingPolicySnapshot(
+            **config.coding_policy.model_dump(exclude={"prompt_text"})
+        ),
+        ceilings=config.coding_ceilings,
+        requested_claim_order=tuple(
+            (c.doc_id, c.claim_id) for c in sources.stored_run.claims
+        ),
+        schema_hash=digest(CodingReply.model_json_schema()),
+        cache_mode=cache_mode,
+    )
+    support = support_configuration(
+        config.support_policy,
+        config.support_ceilings,
+        config.scorer_identity,
+        config.judge_identities,
+        config.extractor_family,
+        cache_mode,
+    )
+    return digest(coding), digest(support)


 def _baseline(config, history, existing_analysis):
@@ -686,6 +792,17 @@
         )
         write_run(directory, result, bundles)
         result = read_run(directory)
+    verify_extraction_configuration(config, result, bundles, template)
+    return result
+
+
+def verify_extraction_configuration(
+    config: WorkflowConfig,
+    result: StoredRun,
+    bundles: tuple[Bundle, ...],
+    template: PromptTemplate,
+) -> None:
+    """Bind stored extraction metadata without restricting its reusable cache mode."""
     record = result.record
     _require(
         record.run_id == config.extraction_run_id
@@ -703,10 +820,15 @@
         config.fixture_started_at is None
         or record.started_at == config.fixture_started_at
     )
-    return result
-
-
-def _coding(config, sources, support, proposal, policy):
+
+
+def finalize_coding(
+    proposal: ProposalRun,
+    support: StoredSupportRun,
+    sources: SupportSources,
+    policy: AssignmentPolicy | None,
+) -> CodingRun:
+    """Project Stage 9's decisions once, shared by workflow and fresh pilot runs."""
     decisions = decide_assignments(proposal, support, sources, policy)
     assignments, links = project_assignments(decisions, support)
     record = CodingRunRecord(
@@ -897,13 +1019,8 @@
         with ProcessLock(states_dir / ".acquire.lock"):
             history = _checked_history(config, states_dir)
             baseline, terminals = _baseline(config, history, existing)
-            acquisition = _projections(config, baseline, metadata)
-            provenance = analysis_provenance_hash(
-                selected_universe_hash=config.universe_hash,
-                expected=expected,
-                acquisition=acquisition,
-                metadata=metadata,
-                canonical_snapshots=canonical,
+            acquisition, provenance = workflow_provenance(
+                config, expected, baseline, metadata, canonical
             )
             if not configuration_path.exists():
                 write_new(configuration_path, config_bytes)
@@ -1008,18 +1125,7 @@
             )
             _require(
                 support.record.configuration_hash
-                == digest(
-                    {
-                        "policy": config.support_policy.model_dump(mode="json"),
-                        "ceilings": config.support_ceilings.model_dump(mode="json"),
-                        "scorer": config.scorer_identity.model_dump(mode="json"),
-                        "judges": [
-                            i.model_dump(mode="json") for i in config.judge_identities
-                        ],
-                        "extractor_family": config.extractor_family,
-                        "cache_mode": "replay",
-                    }
-                )
+                == workflow_configuration_hashes(config, sources)[1]
             )
             _require(tuple(t.target for t in support.targets) == proposal.targets)
             _require(support.record.started_at == started)
@@ -1035,7 +1141,7 @@
             if config.assignment_policy:
                 _require(config.scope == "fixture", "policy_mismatch")
             if previous_coding is None:
-                coding = _coding(config, sources, support, proposal, policy)
+                coding = finalize_coding(proposal, support, sources, policy)
                 write_coding_run(coding_dir, coding, sources, support, policy)
             coding = read_coding_run(coding_dir)
             reverify_coding_run(coding, sources, support, policy)
```

Apply the matching dictionary rows in this implementation step:

```diff
--- a/docs/data-dictionary.md
+++ b/docs/data-dictionary.md
@@ -7001,3 +7001,28 @@
 | --- | --- | --- |
 | `minicheck` | `minicheck_joint` | Primary MiniCheck joint score |
 | `deberta` | `deberta_joint` | Alternative DeBERTa joint score, reported only |
+
+### `WorkflowInputs`
+
+A transient `earnings_pipeline.theme_workflow` dataclass containing the verified
+source inputs shared by the ordinary workflow and the pilot phase runner.
+`load_workflow_inputs(config, runtime)` derives acquisition provenance from the
+immutable acquisition predecessors. It appends no processing transition.
+`workflow_configuration_hashes(config: WorkflowConfig, sources: SupportSources,
+*, cache_mode="replay") -> tuple[str, str]` returns coding then support hashes,
+using the shared configuration definitions before a policy is bound or voted.
+`validate_workflow_policy(config: WorkflowConfig, policy: AssignmentPolicy | None)
+-> None` validates the configured policy reference for metadata loading and
+ordinary pilot runs, refusing with `policy_unavailable` or `policy_mismatch`.
+
+| Field | Type | Meaning |
+| --- | --- | --- |
+| `expected` | tuple of ExpectedEvent | Explicit expected event selection |
+| `bundles` | tuple of Bundle | Canonical documents with original structure and masks |
+| `metadata` | tuple of DocumentMetadata | Checked source and document metadata |
+| `canonical` | tuple of CanonicalSnapshot | Immutable canonical artifact bindings |
+| `raw` | tuple of RawSnapshot | Immutable raw artifact bindings |
+| `codebook` | Codebook | The frozen approved codebook |
+| `template` | PromptTemplate | The pinned extraction prompt template |
+| `acquisition` | tuple of AcquisitionStatus | Checked projections of immutable acquisition predecessors |
+| `provenance_hash` | SHA-256 string | Digest binding the selected universe, acquisition, metadata and canonical snapshots |
```

- [x] **Step 4: Verify green, existing invented workflow consumers and Ruff**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_seams.py apps/earnings-pipeline/tests/test_theme_workflow.py --tb=short -q
uv run --locked --offline --no-sync ruff check apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py apps/earnings-pipeline/src/earnings_pipeline/theme_config.py apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py apps/earnings-pipeline/tests/test_pilot_seams.py
uv run --locked --offline --no-sync ruff format --check apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py apps/earnings-pipeline/src/earnings_pipeline/theme_config.py apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py apps/earnings-pipeline/tests/test_pilot_seams.py
```

Expected: selected tests pass and Ruff is clean. `test_theme_workflow.py` constructs every canonical source in memory from invented strings; it reads synthetic metadata and committed prompts only. Report actual counts.


Run the static dictionary contracts in both the red and green steps:

```bash
uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_data_dictionary.py --tb=short -q
uv run --locked --offline --no-sync ruff check tests/contracts/test_data_dictionary.py
uv run --locked --offline --no-sync ruff format --check tests/contracts/test_data_dictionary.py
```

Before the rows exist, the newly added dictionary checks fail for the missing table/contract. After code and rows are applied, they pass. Stage `docs/data-dictionary.md` and `tests/contracts/test_data_dictionary.py` in this task's commit along with its listed code files.

- [x] **Step 5: Review and commit the task**

```bash
git log -3 --oneline
git add apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py apps/earnings-pipeline/src/earnings_pipeline/theme_config.py apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py apps/earnings-pipeline/tests/test_pilot_seams.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "refactor(workflow): share typed pilot configuration seams"
```

---

### Task 7: Add strict pilot checkpoints and enforce metadata-first intake

**Files:**

- Create: `apps/earnings-pipeline/src/earnings_pipeline/pilot_records.py`
- Create: `apps/earnings-pipeline/src/earnings_pipeline/pilot_inputs.py`
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/stage6.py`
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py` (existing split command consumes the shared derivation)
- Create: `apps/earnings-pipeline/tests/test_pilot_records.py`
- Create: `apps/earnings-pipeline/tests/test_pilot_intake.py`
- Modify: `docs/data-dictionary.md` and `tests/contracts/test_data_dictionary.py` for all new contracts

**Interfaces:**

Consumes the shared Stage 6 helpers and Task 6's `parse_workflow_config`. Produces strict `PilotSettings`, local `ProposalSnapshot`, `PassRecord` and `pilot_records.RunRecord`; frozen `PilotIntake`; and:

```python
load_settings(path: Path, *, repo: Path) -> PilotSettings
read_json[M: Part](path: Path, model: type[M], name: str, *, seal: bool = True) -> M
read_calibration(path: Path) -> CalibrationArtifact
json_bytes(record: Part) -> bytes
derive_split(layout: Layout, pinned: Pinned) -> SplitManifest
require_committed(repo: Path, path: Path, name: str) -> None
open_pilot(layout: Layout, settings_path: Path, partition: Partition) -> PilotIntake
```

`PilotIntake` holds layout, pinned records, split, codebook, preregistration, settings, selected workflow config, partition and signed gold. Its `local` property confines `data/runs/pilot`. `ProposalSnapshot` stays local because classifier output can contain model wording; checkpoint summaries and committed analytical artifacts carry metadata only. `require_committed` compares exact bytes with `git show HEAD:<confined-relative-path>`, captures output and redacts any error. It opens no source text.

- [x] **Step 1: Write the exact record and intake tests**

> Deviation: Owner approved focused unreadable-record cases and stronger realistic reduced-split and calibration-hash-corruption tests.

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/tests/test_pilot_records.py
@@ -0,0 +1,86 @@
+"""Strict local A8 records and intake guards, entirely invented."""
+
+import importlib
+import json
+
+import pytest
+from earnings_core import sha256_hex
+from earnings_pipeline.theme_config import WorkflowError
+from earnings_themes.records import RecordError
+from pydantic import ValidationError
+
+cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_workflow")
+
+
+def test_settings_confine_all_files_and_bind_bytes(tmp_path):
+    from earnings_pipeline.pilot_records import PilotSettings, load_settings
+
+    config, _ = cases.seed_case(tmp_path, seed=False, review=True)
+    path = tmp_path / "workflow.json"
+    path.write_text(config.model_dump_json())
+    selected = {"path": "workflow.json", "sha256": sha256_hex(path.read_bytes())}
+    fields = {
+        "train": selected,
+        "dev": selected,
+        "runtime_manifest": selected,
+        "alternative_scorer": {
+            **config.scorer_identity.model_dump(mode="json"),
+            "kind": "deberta",
+        },
+    }
+    settings_path = tmp_path / "settings.json"
+    settings_path.write_text(json.dumps(fields))
+    settings = load_settings(settings_path, repo=tmp_path)
+    assert isinstance(settings, PilotSettings)
+    fields["train"]["path"] = "../outside.json"
+    settings_path.write_text(json.dumps(fields))
+    with pytest.raises(WorkflowError, match="malformed_record"):
+        load_settings(settings_path, repo=tmp_path)
+
+
+def test_pass_record_requires_dev_fresh_and_checked_hash(tmp_path):
+    from earnings_pipeline.pilot_records import PassRecord, read_json
+    from earnings_themes.records import sealed
+
+    selected = {
+        "directory": "data/runs/pilot/train/pass/extraction",
+        "sha256": "a" * 64,
+    }
+    fields = {
+        "partition": "train",
+        "mode": "fresh",
+        "stability_run_id": "fresh-1",
+        "event_ids": ["invented:event"],
+        "configuration_hash": "b" * 64,
+        "extraction": selected,
+        "proposals": {
+            "path": "data/runs/pilot/train/pass/proposals.json",
+            "sha256": "c" * 64,
+        },
+        "primary": selected,
+        "alternative": selected,
+        "status": "complete",
+        "content_hash": "0" * 64,
+    }
+    with pytest.raises(ValidationError):
+        PassRecord.model_validate_json(json.dumps(fields))
+    fields.update(partition="dev")
+    record = sealed(PassRecord.model_validate_json(json.dumps(fields)))
+    path = tmp_path / "pass.json"
+    path.write_text(record.model_dump_json())
+    assert read_json(path, PassRecord, "pass") == record
+    fields = record.model_dump(mode="json")
+    fields["status"] = "partial"
+    path.write_text(json.dumps(fields))
+    with pytest.raises(RecordError):
+        read_json(path, PassRecord, "pass")
+
+
+def test_calibration_reader_redacts_untrusted_bytes_and_checks_hash(tmp_path):
+    from earnings_pipeline.pilot_records import read_calibration
+
+    path = tmp_path / "calibration.json"
+    path.write_text('"INVENTED_SOURCE_SENTINEL"')
+    with pytest.raises(RecordError) as caught:
+        read_calibration(path)
+    assert "INVENTED_SOURCE_SENTINEL" not in str(caught.value)
--- /dev/null
+++ b/apps/earnings-pipeline/tests/test_pilot_intake.py
@@ -0,0 +1,105 @@
+"""Visibility and partition boundaries refuse before any source or model is opened."""
+
+from pathlib import Path
+from types import SimpleNamespace
+
+import pytest
+from earnings_pipeline.stage6 import Layout
+from earnings_themes.split import Partition
+
+
+def test_test_and_excluded_refuse_before_metadata_or_source_loading(
+    tmp_path, monkeypatch
+):
+    import earnings_pipeline.pilot_inputs as module
+
+    trips = []
+
+    def blocked(*args):
+        trips.append(True)
+        raise AssertionError("INVENTED_SOURCE_SENTINEL")
+
+    monkeypatch.setattr(module, "load_pinned", blocked)
+    for partition in (Partition.TEST, Partition.EXCLUDED):
+        with pytest.raises(module.WorkflowError, match="malformed_record"):
+            module.open_pilot(
+                Layout(tmp_path, Path("u"), Path("p"), "a" * 64),
+                tmp_path / "settings.json",
+                partition,
+            )
+    assert trips == []
+
+
+def test_visibility_refuses_missing_gold_before_documents_or_settings(
+    tmp_path, monkeypatch
+):
+    import earnings_pipeline.pilot_inputs as module
+    from earnings_themes.records import RecordError
+
+    trips = []
+    pinned = SimpleNamespace(
+        events=SimpleNamespace(definition=SimpleNamespace(corpus_id="invented")),
+        gold_dir=tmp_path / "gold",
+        evaluation=tmp_path / "evaluation",
+    )
+    split = SimpleNamespace(
+        events_in=lambda p: (
+            ("invented:train",) if p is Partition.TRAIN else ("invented:dev",)
+        )
+    )
+    monkeypatch.setattr(module, "load_pinned", lambda layout: pinned)
+    monkeypatch.setattr(module, "pinned_split", lambda layout, pin: split)
+    monkeypatch.setattr(module, "derive_split", lambda layout, pin: split)
+    monkeypatch.setattr(module, "pinned_codebook", lambda layout: object())
+
+    def blocked(*args, **kwargs):
+        trips.append(True)
+        raise AssertionError("INVENTED_SOURCE_SENTINEL")
+
+    monkeypatch.setattr(module, "documents", blocked)
+    monkeypatch.setattr(module, "load_settings", blocked)
+    with pytest.raises(RecordError, match="visibility"):
+        module.open_pilot(
+            Layout(tmp_path, Path("u"), Path("p"), "a" * 64),
+            tmp_path / "settings.json",
+            Partition.TRAIN,
+        )
+    assert trips == []
+
+
+def test_self_sealed_reduced_split_refuses_before_gold_or_source(tmp_path, monkeypatch):
+    import earnings_pipeline.pilot_inputs as module
+    from earnings_themes.records import RecordError
+
+    monkeypatch.setattr(module, "load_pinned", lambda layout: object())
+    monkeypatch.setattr(module, "pinned_split", lambda layout, pin: object())
+    monkeypatch.setattr(module, "derive_split", lambda layout, pin: object())
+    with pytest.raises(RecordError, match="binding_mismatch"):
+        module.open_pilot(
+            Layout(tmp_path, Path("u"), Path("p"), "a" * 64),
+            tmp_path / "settings.json",
+            Partition.TRAIN,
+        )
+
+
+def test_committed_metadata_refuses_missing_or_changed_head_bytes(
+    tmp_path, monkeypatch
+):
+    import earnings_pipeline.pilot_inputs as module
+    from earnings_themes.records import RecordError
+
+    path = tmp_path / "metadata.json"
+    path.write_bytes(b"INVENTED_METADATA_SENTINEL")
+    calls = []
+
+    def git(args, **kwargs):
+        calls.append((args, kwargs["cwd"]))
+        return SimpleNamespace(
+            returncode=0, stdout=b"changed", stderr=b"INVENTED_EXCEPTION_SENTINEL"
+        )
+
+    monkeypatch.setattr(module.subprocess, "run", git)
+    with pytest.raises(RecordError, match="not_committed") as caught:
+        module.require_committed(tmp_path, path, "gold")
+    assert "INVENTED" not in str(caught.value)
+    assert calls == [(["git", "show", "HEAD:metadata.json"], tmp_path)]
```

The same task adds its dictionary contract test:

```diff
--- a/tests/contracts/test_data_dictionary.py
+++ b/tests/contracts/test_data_dictionary.py
@@ -25,7 +25,13 @@
 from earnings_ingestion.events import acceptance, coverage, states
 from earnings_ingestion.events import records as events
 from earnings_ingestion.fetch import records as fetch
-from earnings_pipeline import model_runtime, theme_config, theme_workflow
+from earnings_pipeline import (
+    model_runtime,
+    pilot_inputs,
+    pilot_records,
+    theme_config,
+    theme_workflow,
+)
 from earnings_themes import (
     annotation,
     codebook,
@@ -718,6 +724,52 @@
     )


+PILOT_MODELS = {
+    "PilotSettings": pilot_records.PilotSettings,
+    "ProposalSnapshot": pilot_records.ProposalSnapshot,
+    "PassRecord": pilot_records.PassRecord,
+    "pilot_records.RunRecord": pilot_records.RunRecord,
+}
+PILOT_DATACLASSES = {
+    "PilotIntake": pilot_inputs.PilotIntake,
+}
+PILOT_ENUMS = {}
+PILOT_MODULES = [pilot_records, pilot_inputs]
+
+
+@pytest.mark.parametrize(("name", "model"), PILOT_MODELS.items(), ids=PILOT_MODELS)
+def test_pilot_application_fields_documented(name, model):
+    assert documented(name) == set(model.model_fields)
+
+
+@pytest.mark.parametrize(
+    ("name", "record"), PILOT_DATACLASSES.items(), ids=PILOT_DATACLASSES
+)
+def test_pilot_application_dataclass_fields_documented(name, record):
+    assert documented(name) == {field.name for field in fields(record)}
+
+
+@pytest.mark.parametrize(("name", "enum"), PILOT_ENUMS.items(), ids=PILOT_ENUMS)
+def test_pilot_application_enum_values_documented(name, enum):
+    assert documented(name) == {member.value for member in enum}
+
+
+def test_pilot_application_registry_is_complete():
+    defined = {
+        value
+        for module in PILOT_MODULES
+        for value in vars(module).values()
+        if isinstance(value, type)
+        and value.__module__ == module.__name__
+        and not value.__name__.startswith("_")
+    }
+    assert {v for v in defined if issubclass(v, BaseModel)} == set(
+        PILOT_MODELS.values()
+    )
+    assert {v for v in defined if issubclass(v, StrEnum)} == set(PILOT_ENUMS.values())
+    assert {v for v in defined if is_dataclass(v)} == set(PILOT_DATACLASSES.values())
+
+
 EVALUATION_MODELS = [
     bootstrap.BootstrapPlan,
     bootstrap.Interval,
```

- [x] **Step 2: Observe red**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_records.py apps/earnings-pipeline/tests/test_pilot_intake.py --tb=short -q
```

Expected: all new application imports are absent. The cases pin safe record errors, family/mode/partition boundaries, visibility before source reads, a self-sealed reduced split, and missing/changed committed metadata.

- [x] **Step 3: Apply the records, checked readers and intake**

> Deviation: Owner approved require_committed OSError conversion to closed RecordError refusals and the two Task 6 docstring corrections; reviews closed.

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/src/earnings_pipeline/pilot_records.py
@@ -0,0 +1,146 @@
+"""A8's strict configuration and local checkpoints; metadata checkpoints carry IDs and hashes; proposal snapshots stay local."""
+
+import json
+from pathlib import Path
+from typing import Literal, Self
+
+from earnings_core import canonical_json
+from earnings_themes.coding.records import (
+    AttributeRecord,
+    ClassificationRecord,
+    CodingAttempt,
+    NoveltyItem,
+    ProposalRecord,
+    ProposalRunRecord,
+)
+from earnings_themes.coding.run import ProposalRun
+from earnings_themes.evaluation import CalibrationArtifact
+from earnings_themes.records import (
+    IdPart,
+    Part,
+    RecordError,
+    Sha256Hex,
+    ThemesRecord,
+    checked,
+    parse,
+)
+from earnings_themes.split import Partition
+from earnings_themes.support.records import ScorerIdentity
+from pydantic import model_validator
+
+from earnings_pipeline.theme_config import (
+    FileSelection,
+    StoredSelection,
+    WorkflowError,
+    confined_path,
+)
+
+
+class PilotSettings(Part):
+    """Two explicit workflow selections and the B1 runtime manifest."""
+
+    train: FileSelection
+    dev: FileSelection
+    runtime_manifest: FileSelection
+    alternative_scorer: ScorerIdentity
+
+
+class ProposalSnapshot(Part):
+    """Local classifier output, persisted before any assignment decision exists."""
+
+    record: ProposalRunRecord
+    classifications: tuple[ClassificationRecord, ...]
+    attempts: tuple[CodingAttempt, ...]
+    proposals: tuple[ProposalRecord, ...]
+    attributes: tuple[AttributeRecord, ...]
+    novelty: tuple[NoveltyItem, ...]
+
+    @classmethod
+    def of(cls, run: ProposalRun) -> Self:
+        return cls(**{name: getattr(run, name) for name in cls.model_fields})
+
+    def run(self) -> ProposalRun:
+        return ProposalRun(
+            **{name: getattr(self, name) for name in type(self).model_fields}
+        )
+
+
+class PassRecord(ThemesRecord):
+    """A local pass with stored extraction, proposals and both support runs."""
+
+    partition: Partition
+    mode: Literal["live", "fresh"]
+    stability_run_id: IdPart | None
+    event_ids: tuple[IdPart, ...]
+    configuration_hash: Sha256Hex
+    extraction: StoredSelection
+    proposals: FileSelection
+    primary: StoredSelection
+    alternative: StoredSelection
+    status: Literal["complete", "partial"]
+    content_hash: Sha256Hex
+
+    @model_validator(mode="after")
+    def _partition_and_mode(self) -> Self:
+        if self.partition not in (Partition.TRAIN, Partition.DEV):
+            raise ValueError("wrong_partition")
+        if (self.mode == "fresh") != (self.stability_run_id is not None):
+            raise ValueError("malformed_record")
+        if self.mode == "fresh" and self.partition is not Partition.DEV:
+            raise ValueError("wrong_partition")
+        if tuple(sorted(set(self.event_ids))) != self.event_ids:
+            raise ValueError("malformed_record")
+        return self
+
+
+class RunRecord(ThemesRecord):
+    """A local frozen-policy run, referencing its pass and coding decisions."""
+
+    partition: Partition
+    fresh: IdPart | None
+    event_ids: tuple[IdPart, ...]
+    pass_record: FileSelection
+    coding: StoredSelection
+    calibration_hash: Sha256Hex
+    configuration_hash: Sha256Hex
+    status: Literal["complete", "partial"]
+    content_hash: Sha256Hex
+
+    @model_validator(mode="after")
+    def _partition(self) -> Self:
+        if self.partition not in (Partition.TRAIN, Partition.DEV):
+            raise ValueError("wrong_partition")
+        if self.fresh is not None and self.partition is not Partition.DEV:
+            raise ValueError("wrong_partition")
+        if tuple(sorted(set(self.event_ids))) != self.event_ids:
+            raise ValueError("malformed_record")
+        return self
+
+
+def load_settings(path: Path, *, repo: Path) -> PilotSettings:
+    settings = read_json(path, PilotSettings, "settings", seal=False)
+    for selected in (settings.train, settings.dev, settings.runtime_manifest):
+        confined_path(repo, selected.path)
+    if settings.alternative_scorer.kind != "deberta":
+        raise WorkflowError("model_mismatch")
+    return settings
+
+
+def read_json[M: Part](
+    path: Path, model: type[M], name: str, *, seal: bool = True
+) -> M:
+    """Closed reader; names are caller-owned field paths, never untrusted filenames."""
+    try:
+        value = json.loads(path.read_bytes())
+    except (OSError, ValueError):
+        raise RecordError(name, ("malformed_record",)) from None
+    result = parse(value, model, name)
+    return checked(result, name) if seal else result
+
+
+def read_calibration(path: Path) -> CalibrationArtifact:
+    return read_json(path, CalibrationArtifact, "calibration")
+
+
+def json_bytes(record: Part) -> bytes:
+    return canonical_json(record.model_dump(mode="json"))
--- /dev/null
+++ b/apps/earnings-pipeline/src/earnings_pipeline/pilot_inputs.py
@@ -0,0 +1,220 @@
+"""Metadata-only partition and visibility gates precede every A8 source read."""
+
+import subprocess
+from dataclasses import dataclass
+from pathlib import Path
+
+from earnings_core import sha256_hex
+from earnings_themes.annotation import check_countable
+from earnings_themes.codebook import Codebook
+from earnings_themes.evaluation import Preregistration, load_preregistration
+from earnings_themes.gold import CodebookRef, Gold, load_gold
+from earnings_themes.independent import ledger_check
+from earnings_themes.records import RecordError
+from earnings_themes.split import Partition, SplitManifest
+
+from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
+from earnings_pipeline.pilot_records import PilotSettings, load_settings
+from earnings_pipeline.stage6 import (
+    CODEBOOK_FILE,
+    Layout,
+    Pinned,
+    derive_split,
+    documents,
+    file_stem,
+    independent_path,
+    load_pinned,
+    read_ledger,
+)
+from earnings_pipeline.theme_config import (
+    FileSelection,
+    WorkflowConfig,
+    WorkflowError,
+    confined_path,
+    parse_workflow_config,
+)
+
+
+@dataclass(frozen=True, repr=False)
+class PilotIntake:
+    layout: Layout
+    pinned: Pinned
+    split: SplitManifest
+    codebook: Codebook
+    preregistration: Preregistration
+    settings: PilotSettings
+    config: WorkflowConfig
+    partition: Partition
+    gold: tuple[Gold, ...]
+
+    @property
+    def local(self) -> Path:
+        return confined_path(self.layout.repo, "data/runs/pilot", "data/runs/pilot")
+
+
+def require_committed(repo: Path, path: Path, name: str) -> None:
+    """A signed metadata file must be identical to HEAD before it opens a source."""
+    path = confined_path(repo, path.relative_to(repo).as_posix())
+    result = subprocess.run(
+        ["git", "show", "HEAD:" + path.relative_to(repo).as_posix()],
+        cwd=repo,
+        capture_output=True,
+        check=False,
+    )
+    if result.returncode != 0 or result.stdout != path.read_bytes():
+        raise RecordError(name, ("not_committed",))
+
+
+def _configuration(repo: Path, selected: FileSelection) -> WorkflowConfig:
+    path = confined_path(repo, selected.path)
+    if sha256_hex(path.read_bytes()) != selected.sha256:
+        raise WorkflowError("input_changed")
+    return parse_workflow_config(path, repo=repo)
+
+
+def open_pilot(
+    layout: Layout, settings_path: Path, partition: Partition
+) -> PilotIntake:
+    if partition not in (Partition.TRAIN, Partition.DEV):
+        raise WorkflowError("malformed_record")
+    pinned = load_pinned(layout)
+    split = pinned_split(layout, pinned)
+    if split != derive_split(layout, pinned):
+        raise RecordError("split", ("binding_mismatch",))
+    if pinned.events.definition.corpus_id == "djia-2024q3-2026q2" and (
+        len(split.events_in(Partition.TRAIN)) != 20
+        or len(split.events_in(Partition.DEV)) != 8
+    ):
+        raise RecordError("visibility", ("partition_count_mismatch",))
+    codebook = pinned_codebook(layout)
+    selected = tuple(
+        sorted((*split.events_in(Partition.TRAIN), *split.events_in(Partition.DEV)))
+    )
+    # A missing signature is detected before acquisition metadata or settings can open a source.
+    missing = [
+        event
+        for event in selected
+        if not (pinned.gold_dir / f"{file_stem(event)}.toml").is_file()
+    ]
+    if missing:
+        raise RecordError(
+            "visibility", tuple(f"{event}: not_signed" for event in missing)
+        )
+    doc_ids = documents(layout, pinned)
+    gold = []
+    for event in selected:
+        path = pinned.gold_dir / f"{file_stem(event)}.toml"
+        require_committed(layout.repo, path, "gold")
+        record = load_gold(path)
+        if record.doc_id != doc_ids.get(event):
+            raise RecordError("visibility", (f"{event}: document_mismatch",))
+        if refusals := check_countable(
+            record,
+            event_id=event,
+            pin=pinned.pin,
+            split=split,
+            codebook=codebook,
+            doc_id=doc_ids[event],
+        ):
+            raise RecordError(
+                "visibility",
+                tuple(f"{event} {r.subject}: {r.reason}" for r in refusals),
+            )
+        gold.append(record)
+    require_committed(
+        layout.repo, pinned.evaluation / "independent-pass.toml", "ledger"
+    )
+    ledger = read_ledger(pinned)
+    for event in split.events_in(Partition.DEV):
+        selected_path = independent_path(layout, event)
+        path = confined_path(
+            layout.repo,
+            selected_path.relative_to(layout.repo).as_posix(),
+            "data/runs/gold/independent",
+        )
+        data = path.read_bytes() if path.is_file() else None
+        if problem := ledger_check(ledger, event, data):
+            raise RecordError("visibility", (f"{event}: {problem.value}",))
+    require_committed(
+        layout.repo, pinned.evaluation / "preregistration-v1.toml", "preregistration"
+    )
+    preregistration = load_preregistration(
+        pinned.evaluation / "preregistration-v1.toml"
+    )
+    book_ref = CodebookRef(
+        codebook_id=codebook.codebook_id,
+        codebook_version=codebook.codebook_version,
+        content_hash=codebook.content_hash,
+    )
+    if (
+        preregistration.pin != pinned.pin
+        or preregistration.split_hash != split.content_hash
+        or preregistration.codebook != book_ref
+    ):
+        raise RecordError("preregistration", ("binding_mismatch",))
+    settings = load_settings(settings_path, repo=layout.repo)
+    configs = {
+        Partition.TRAIN: _configuration(layout.repo, settings.train),
+        Partition.DEV: _configuration(layout.repo, settings.dev),
+    }
+    book_hash = sha256_hex((layout.repo / CODEBOOK_FILE).read_bytes())
+    for part, config in configs.items():
+        if config.codebook.sha256 != book_hash or {
+            source.event_id: source.doc_id for source in config.sources
+        } != {event: doc_ids[event] for event in split.events_in(part)}:
+            raise RecordError("settings", ("source_binding_mismatch",))
+        if (
+            config.scope != "research"
+            or config.selected_event_ids != tuple(sorted(split.events_in(part)))
+            or config.pilot_hash != pinned.pin.pilot_hash
+            or config.policy_reference is not None
+            or config.assignment_policy is not None
+            or any(
+                value is not None
+                for value in (
+                    config.stored_extraction,
+                    config.stored_coding,
+                    config.stored_support,
+                    config.stored_analysis,
+                )
+            )
+        ):
+            raise WorkflowError("malformed_record")
+        for reference in (
+            config.extraction_cache,
+            config.coding_cache,
+            config.support_cache,
+            config.output_dir,
+        ):
+            confined_path(layout.repo, reference, "data/runs/pilot")
+    a, b = configs[Partition.TRAIN], configs[Partition.DEV]
+    for field in (
+        "extraction_identity",
+        "extractor_family",
+        "extraction_policy",
+        "extraction_ceilings",
+        "classifier_identity",
+        "coding_policy",
+        "coding_ceilings",
+        "scorer_identity",
+        "judge_identities",
+        "support_policy",
+        "support_ceilings",
+        "codebook",
+        "extraction_prompt",
+        "coding_prompt",
+        "support_prompt",
+    ):
+        if getattr(a, field) != getattr(b, field):
+            raise RecordError("settings", (f"{field}: configuration_mismatch",))
+    return PilotIntake(
+        layout,
+        pinned,
+        split,
+        codebook,
+        preregistration,
+        settings,
+        configs[partition],
+        partition,
+        tuple(g for g in gold if g.partition is partition),
+    )
--- a/apps/earnings-pipeline/src/earnings_pipeline/stage6.py
+++ b/apps/earnings-pipeline/src/earnings_pipeline/stage6.py
@@ -49,7 +49,7 @@
 from earnings_themes.independent import LEDGER, IndependentLedger, load_ledger
 from earnings_themes.problems import Problem, Refusal
 from earnings_themes.records import Pin, RecordError
-from earnings_themes.split import Partition
+from earnings_themes.split import Partition, SplitEvent, SplitManifest, split_events
 from earnings_themes.wording import labelled_strings, shared
 from pydantic import BaseModel

@@ -111,6 +111,22 @@
     @property
     def gold_dir(self) -> Path:
         return self.evaluation / "gold"
+
+
+def derive_split(layout: Layout, pinned: Pinned) -> SplitManifest:
+    """The authoritative issuer-time/1 split, shared by freeze and pilot intake."""
+    rows = {row.event_id: row for row in pinned.events.rows}
+    events = [
+        SplitEvent(
+            event_id=row.event_id,
+            issuer_id=rows[row.event_id].issuer_id,
+            period_end=rows[row.event_id].period_end,
+        )
+        for row in pinned.pilot.rows
+    ]
+    return split_events(
+        events, pinned.pin, fixture_event_ids=fixture_event_ids(layout, pinned.events)
+    )


 def file_stem(event_id: str) -> str:
--- a/apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py
+++ b/apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py
@@ -40,9 +40,7 @@
 from earnings_themes.split import (
     SPLIT_POLICY,
     Partition,
-    SplitEvent,
     SplitManifest,
-    split_events,
 )

 from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
@@ -51,10 +49,10 @@
     Layout,
     Pinned,
     committed_gold,
+    derive_split,
     documents,
     fail,
     file_stem,
-    fixture_event_ids,
     guarded,
     kept_drafts,
     load_bundle,
@@ -85,21 +83,8 @@
     """Split the pinned pilot by issuer-time/1, and freeze split-v1.json."""
     layout: Layout = context.obj
     pinned = load_pinned(layout)
-    rows = {row.event_id: row for row in pinned.events.rows}
-    events = [
-        SplitEvent(
-            event_id=row.event_id,
-            issuer_id=rows[row.event_id].issuer_id,
-            period_end=rows[row.event_id].period_end,
-        )
-        for row in pinned.pilot.rows
-    ]
-    try:
-        manifest = split_events(
-            events,
-            pinned.pin,
-            fixture_event_ids=fixture_event_ids(layout, pinned.events),
-        )
+    try:
+        manifest = derive_split(layout, pinned)
     except ValueError as error:
         fail(f"Refused: {error}")
     created = write_once(pinned.split_path, record_json(manifest), layout)
```

Apply the matching dictionary rows in this implementation step:

```diff
--- a/docs/data-dictionary.md
+++ b/docs/data-dictionary.md
@@ -7026,3 +7026,93 @@
 | `template` | PromptTemplate | The pinned extraction prompt template |
 | `acquisition` | tuple of AcquisitionStatus | Checked projections of immutable acquisition predecessors |
 | `provenance_hash` | SHA-256 string | Digest binding the selected universe, acquisition, metadata and canonical snapshots |
+
+### `PilotSettings`
+
+A strict local `earnings_pipeline.pilot_records` configuration. File selections
+are confined to the repository, and the alternative scorer must have kind
+`deberta`. The settings file and each selected file retain separate hash pins.
+
+| Field | Type | Meaning |
+| --- | --- | --- |
+| `train` | FileSelection | Explicit train workflow configuration path and SHA-256 |
+| `dev` | FileSelection | Explicit dev workflow configuration path and SHA-256 |
+| `runtime_manifest` | FileSelection | B1 runtime manifest path and SHA-256 |
+| `alternative_scorer` | ScorerIdentity | Frozen alternative DeBERTa identity, reported only |
+
+### `ProposalSnapshot`
+
+A strict local checkpoint of classifier output before an assignment decision
+exists. It reconstructs `ProposalRun` without repeating classification. Its
+proposal and novelty records can contain model wording; this snapshot is a local
+input, not a public report artifact.
+
+| Field | Type | Meaning |
+| --- | --- | --- |
+| `record` | ProposalRunRecord | Coding proposal manifest and configuration binding |
+| `classifications` | tuple of ClassificationRecord | Claim classification results |
+| `attempts` | tuple of CodingAttempt | Auditable classifier attempts |
+| `proposals` | tuple of ProposalRecord | Proposed claim-theme targets |
+| `attributes` | tuple of AttributeRecord | Separate analyst attributes |
+| `novelty` | tuple of NoveltyItem | Local novelty suggestions |
+
+### `PassRecord`
+
+A schema-1 local checkpoint for an extraction, classification and support pass.
+The events are unique and sorted. `fresh` passes require a stability run ID and
+are dev-only; `live` passes have no stability run ID. The file is sealed before
+consumption, and its referenced artifacts are independently verified.
+
+| Field | Type | Meaning |
+| --- | --- | --- |
+| `schema_version` | integer | `1` |
+| `partition` | Partition | `train` or `dev` |
+| `mode` | literal | `live` or `fresh` |
+| `stability_run_id` | IdPart or null | Fresh dev pass identity; absent for live passes |
+| `event_ids` | tuple of IdPart | Sorted unique event selection |
+| `configuration_hash` | SHA-256 | Digest of the complete selected WorkflowConfig |
+| `extraction` | StoredSelection | Extraction store and run identity |
+| `proposals` | FileSelection | Local ProposalSnapshot path and SHA-256 |
+| `primary` | StoredSelection | Primary MiniCheck support store and run identity |
+| `alternative` | StoredSelection | Alternative DeBERTa support store and run identity |
+| `status` | literal | `complete` or `partial` |
+| `content_hash` | SHA-256 | Digest of every other serialized field |
+
+### `pilot_records.RunRecord`
+
+The qualified heading distinguishes this schema-1 local frozen-policy checkpoint
+from extraction's `RunRecord`. Events are unique and sorted, and a non-null
+`fresh` identity is dev-only. This record references the verified pass and coding
+decisions rather than materializing model wording.
+
+| Field | Type | Meaning |
+| --- | --- | --- |
+| `schema_version` | integer | `1` |
+| `partition` | Partition | `train` or `dev` |
+| `fresh` | IdPart or null | Fresh dev stability run identity, or null for the ordinary run |
+| `event_ids` | tuple of IdPart | Sorted unique event selection |
+| `pass_record` | FileSelection | Sealed PassRecord path and SHA-256 |
+| `coding` | StoredSelection | Frozen-policy coding store and run identity |
+| `calibration_hash` | SHA-256 | Consumed calibration artifact's content hash |
+| `configuration_hash` | SHA-256 | Frozen configuration and selected policy binding from the calibration artifact |
+| `status` | literal | `complete` or `partial` |
+| `content_hash` | SHA-256 | Digest of every other serialized field |
+
+### `PilotIntake`
+
+A transient `earnings_pipeline.pilot_inputs` dataclass. `open_pilot` verifies
+split signatures, gold document bindings, the committed dev independent-reading
+ledger, preregistration and configuration pins before loading canonical text.
+The derived `local` property is a path accessor, not a serialized field.
+
+| Field | Type | Meaning |
+| --- | --- | --- |
+| `layout` | Layout | Repository paths for the pinned local artifacts |
+| `pinned` | Pinned | Verified Stage 6 pilot, split and codebook pins |
+| `split` | SplitManifest | Verified partition and document bindings |
+| `codebook` | Codebook | Frozen approved codebook |
+| `preregistration` | Preregistration | Verified calibration, sampling and gate rules |
+| `settings` | PilotSettings | Verified train/dev configurations and runtime pins |
+| `config` | WorkflowConfig | Current partition's verified workflow selection |
+| `partition` | Partition | Requested `train` or `dev` partition |
+| `gold` | tuple of Gold | Checked committed gold for the current selection |
```

- [x] **Step 4: Verify green and Ruff**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_records.py apps/earnings-pipeline/tests/test_pilot_intake.py --tb=short -q
uv run --locked --offline --no-sync ruff check apps/earnings-pipeline/src/earnings_pipeline/stage6.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/src/earnings_pipeline/pilot_records.py apps/earnings-pipeline/src/earnings_pipeline/pilot_inputs.py apps/earnings-pipeline/tests/test_pilot_records.py apps/earnings-pipeline/tests/test_pilot_intake.py
uv run --locked --offline --no-sync ruff format --check apps/earnings-pipeline/src/earnings_pipeline/stage6.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/src/earnings_pipeline/pilot_records.py apps/earnings-pipeline/src/earnings_pipeline/pilot_inputs.py apps/earnings-pipeline/tests/test_pilot_records.py apps/earnings-pipeline/tests/test_pilot_intake.py
```

Expected: invented tests pass; Ruff is clean. Report actual counts.


Run the static dictionary contracts in both the red and green steps:

```bash
uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_data_dictionary.py --tb=short -q
uv run --locked --offline --no-sync ruff check tests/contracts/test_data_dictionary.py
uv run --locked --offline --no-sync ruff format --check tests/contracts/test_data_dictionary.py
```

Before the rows exist, the newly added dictionary checks fail for the missing table/contract. After code and rows are applied, they pass. Stage `docs/data-dictionary.md` and `tests/contracts/test_data_dictionary.py` in this task's commit along with its listed code files.

- [x] **Step 5: Review and commit the task**

```bash
git log -3 --oneline
git add apps/earnings-pipeline/src/earnings_pipeline/stage6.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/src/earnings_pipeline/pilot_records.py apps/earnings-pipeline/src/earnings_pipeline/pilot_inputs.py apps/earnings-pipeline/tests/test_pilot_records.py apps/earnings-pipeline/tests/test_pilot_intake.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(pilot): add checked checkpoints and visibility intake"
```

---

### Task 8: Run phase-separated passes and frozen-policy replay

**Files:**

- Create: `apps/earnings-pipeline/src/earnings_pipeline/pilot_workflow.py`
- Create: `apps/earnings-pipeline/tests/test_pilot_workflow.py`
- Modify: `docs/data-dictionary.md` and `tests/contracts/test_data_dictionary.py` for `LoadedPass`

**Interfaces:**

Consumes `PassRecord`/`RunRecord`, the shared workflow seams, strict Stage 7–9 readers, caches, and the public configuration hash. Produces frozen `LoadedPass(record, sources, proposal, primary, alternative)` and:

```python
load_pass(config: WorkflowConfig, record: PassRecord) -> LoadedPass
make_pass(config: WorkflowConfig, runtime: WorkflowRuntime, alternative: EntailmentScorer, *, partition: Partition, directory: Path, fresh: str | None, support_ready: Callable[[], None], now: Callable[[], datetime]) -> PassRecord
bind_policy(config: WorkflowConfig, loaded: LoadedPass, artifact: CalibrationArtifact, *, replay: bool) -> AssignmentPolicy | None
verify_replay_cache(config: WorkflowConfig, loaded: LoadedPass) -> None
make_run(config: WorkflowConfig, loaded: LoadedPass, artifact: CalibrationArtifact, *, directory: Path, now: Callable[[], datetime]) -> RunRecord
```

The phase runner persists local extraction, a decision-free proposal snapshot and both support runs. It invokes `support_ready` after classification and before support (D20-9, approving P20-A). Ordinary replay verifies every primary request through replay-only adapters before invoking the workflow. Fresh decisions use the already-fresh pass in memory and append no Stage 5 transition. Pass reload rebinds source, prompt/configuration, target inventory, modes and recomputed completeness; a seal alone cannot turn a partial pass into a complete one. Task 9's intake-aware `checked_pass` additionally binds the configured alternative scorer and partition/event inventory at every consuming command.

- [x] **Step 1: Write the exact phase and replay tests**

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/tests/test_pilot_workflow.py
@@ -0,0 +1,429 @@
+"""A8 phase order and zero-dispatch replay over entirely invented source text."""
+
+import importlib
+import json
+import shutil
+
+import pytest
+from earnings_pipeline.theme_workflow import WorkflowRuntime, replay_runtime
+from earnings_themes.coding.adapters import ScriptedClassifier
+from earnings_themes.extraction.adapters import ModelReply, ScriptedAdapter
+from earnings_themes.split import Partition
+
+cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_workflow")
+coding_cases = importlib.import_module("packages.earnings-themes.tests.coding.cases")
+
+
+def seed_case(tmp_path, **kwargs):
+    config, payload = cases.seed_case(tmp_path, **kwargs)
+    updates = {}
+    for name in ("extraction_cache", "coding_cache", "support_cache"):
+        path = tmp_path / config.__getattribute__(name)
+        target = tmp_path / "data/runs/pilot/caches" / name
+        target.parent.mkdir(parents=True, exist_ok=True)
+        if path.exists():
+            shutil.move(str(path), str(target))
+        updates[name] = target.relative_to(tmp_path).as_posix()
+    return config.model_copy(update=updates), payload
+
+
+def runtime(config, phases):
+    extractor = ScriptedAdapter(
+        lambda request: (
+            phases.append("extract"),
+            ModelReply(
+                model="scripted",
+                text=json.dumps(
+                    {
+                        "candidates": [
+                            {"quote_labels": ["U1"], "claim": "Invented expansion."}
+                        ]
+                    }
+                ),
+            ),
+        )[1]
+    )
+    classifier = ScriptedClassifier(
+        lambda request: (
+            phases.append("classify"),
+            ModelReply(
+                model=config.classifier_identity.runtime.model_id,
+                text=json.dumps({"theme_ids": ["capacity"], "attributes": {}}),
+            ),
+        )[1],
+        lambda request: 5,
+        config.classifier_identity,
+    )
+    scorer, judges = coding_cases.make_support_parts()
+    return WorkflowRuntime(extractor, classifier, scorer, judges, None, None)
+
+
+def test_pass_stores_phases_without_decisions_or_state_and_resume_uses_cache(tmp_path):
+    from earnings_pipeline.pilot_workflow import load_pass, make_pass
+
+    config, _ = seed_case(tmp_path, seed=False, review=True)
+    phases = []
+    rt = runtime(config, phases)
+    alternative = coding_cases.make_support_parts()[0]
+    before = {p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()}
+    record = make_pass(
+        config,
+        rt,
+        alternative,
+        partition=Partition.TRAIN,
+        directory=tmp_path / "data/runs/pilot/train/pass",
+        fresh=None,
+        support_ready=lambda: phases.append("ready"),
+        now=lambda: cases.NOW,
+    )
+    assert record.status == "complete"
+    assert phases.index("extract") < phases.index("classify") < phases.index("ready")
+    loaded = load_pass(config, record)
+    assert loaded.proposal.record.run_id == config.coding_run_id
+    assert loaded.primary.targets
+    assert not (tmp_path / "data/runs/pilot/train/pass/coding").exists()
+    assert before == {
+        p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()
+    }
+    again = make_pass(
+        config,
+        replay_runtime(config),
+        alternative,
+        partition=Partition.TRAIN,
+        directory=tmp_path / "data/runs/pilot/train/pass",
+        fresh=None,
+        support_ready=lambda: None,
+        now=lambda: cases.NOW,
+    )
+    assert again == record
+
+
+def test_unacknowledged_checkpoint_never_calls_support(tmp_path):
+    from earnings_pipeline.pilot_workflow import make_pass
+
+    config, _ = seed_case(tmp_path, seed=False, review=True)
+    phases = []
+    rt = runtime(config, phases)
+
+    def refused():
+        raise RuntimeError("INVENTED_EXCEPTION_SENTINEL")
+
+    with pytest.raises(RuntimeError):
+        make_pass(
+            config,
+            rt,
+            rt.scorer,
+            partition=Partition.TRAIN,
+            directory=tmp_path / "data/runs/pilot/train/pass",
+            fresh=None,
+            support_ready=refused,
+            now=lambda: cases.NOW,
+        )
+    assert not (tmp_path / "data/runs/pilot/train/pass/support").exists()
+
+
+def test_fresh_directory_is_never_resumed_and_main_caches_survive(tmp_path):
+    from earnings_pipeline.pilot_workflow import make_pass
+    from earnings_pipeline.theme_config import WorkflowError
+
+    config, _ = seed_case(tmp_path, seed=True, review=True)
+    phases = []
+    rt = runtime(config, phases)
+    before = {
+        p.relative_to(tmp_path): p.read_bytes()
+        for kind in (config.extraction_cache, config.coding_cache, config.support_cache)
+        for p in (tmp_path / kind).glob("*.json")
+    }
+    directory = tmp_path / "data/runs/pilot/dev/fresh/stability-1"
+    record = make_pass(
+        config,
+        rt,
+        rt.scorer,
+        partition=Partition.DEV,
+        directory=directory,
+        fresh="stability-1",
+        support_ready=lambda: None,
+        now=lambda: cases.NOW,
+    )
+    assert record.mode == "fresh"
+    assert phases
+    assert before == {p: (tmp_path / p).read_bytes() for p in before}
+    with pytest.raises(WorkflowError, match="state_run_conflict"):
+        make_pass(
+            config,
+            rt,
+            rt.scorer,
+            partition=Partition.DEV,
+            directory=directory,
+            fresh="stability-1",
+            support_ready=lambda: None,
+            now=lambda: cases.NOW,
+        )
+
+
+def bound_artifact(config, loaded, *, none=False):
+    from earnings_themes.evaluation import frozen_configuration, sealed
+    from earnings_themes.evaluation.calibration import configuration_hash
+
+    factory = importlib.import_module(
+        "packages.earnings-themes.tests.evaluation.test_policy"
+    )
+    artifact = factory.artifact_with(0.2)
+    selection = None if none else artifact.selection
+    fields = artifact.model_dump(mode="json")
+    fields.update(
+        selection=None if selection is None else selection.model_dump(mode="json"),
+        outcome="no_candidate" if none else "selected",
+        configuration_hash=configuration_hash(
+            frozen_configuration(
+                loaded.sources.stored_run.record,
+                loaded.proposal.record,
+                loaded.primary.record,
+                config.support_policy,
+            ),
+            selection,
+        ),
+    )
+    from earnings_themes.evaluation import CalibrationArtifact
+
+    return sealed(CalibrationArtifact.model_validate_json(json.dumps(fields)))
+
+
+@pytest.mark.parametrize("none", [False, True])
+def test_normal_run_reuses_live_pass_and_replays_without_dispatch(tmp_path, none):
+    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run
+    from earnings_themes.coding.store import read_coding_run
+
+    config, _ = seed_case(tmp_path, seed=False, review=True)
+    rt = runtime(config, [])
+    passed = make_pass(
+        config,
+        rt,
+        rt.scorer,
+        partition=Partition.TRAIN,
+        directory=tmp_path / "data/runs/pilot/train/pass",
+        fresh=None,
+        support_ready=lambda: None,
+        now=lambda: cases.NOW,
+    )
+    loaded = load_pass(config, passed)
+    artifact = bound_artifact(config, loaded, none=none)
+    record = make_run(
+        config,
+        loaded,
+        artifact,
+        directory=tmp_path / "data/runs/pilot/train/run",
+        now=lambda: cases.NOW,
+    )
+    assert record.fresh is None
+    coding = read_coding_run(tmp_path / record.coding.directory)
+    assert {d.status for d in coding.decisions} == (
+        {"review"} if none else {"accepted"}
+    )
+    assert coding.record.cache_mode == "replay"
+    assert coding.record.cache_hits > 0
+    assert coding.record.requests == 0
+
+
+@pytest.mark.parametrize("cache", ["coding_cache", "support_cache"])
+def test_policy_tamper_and_missing_replay_entry_are_refused(tmp_path, cache):
+    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run
+    from earnings_pipeline.theme_config import WorkflowError
+    from earnings_themes.records import RecordError
+
+    config, _ = seed_case(tmp_path, seed=False, review=True)
+    rt = runtime(config, [])
+    passed = make_pass(
+        config,
+        rt,
+        rt.scorer,
+        partition=Partition.TRAIN,
+        directory=tmp_path / "data/runs/pilot/train/pass",
+        fresh=None,
+        support_ready=lambda: None,
+        now=lambda: cases.NOW,
+    )
+    loaded = load_pass(config, passed)
+    artifact = bound_artifact(config, loaded)
+    with pytest.raises(RecordError):
+        make_run(
+            config,
+            loaded,
+            artifact.model_copy(update={"usable_labels": 59}),
+            directory=tmp_path / "data/runs/pilot/train/tamper",
+            now=lambda: cases.NOW,
+        )
+    for entry in (tmp_path / getattr(config, cache)).glob("*.json"):
+        entry.unlink()
+    before = {p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()}
+    with pytest.raises(WorkflowError, match="replay_miss"):
+        make_run(
+            config,
+            loaded,
+            artifact,
+            directory=tmp_path / "data/runs/pilot/train/missing",
+            now=lambda: cases.NOW,
+        )
+
+    assert not (tmp_path / "data/runs/pilot/train/missing").exists()
+    assert before == {
+        p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()
+    }
+
+
+@pytest.mark.parametrize(
+    "child", ["extraction", "proposals.json", "support", "alternative"]
+)
+def test_interrupted_pass_refuses_phase_symlink_before_source_read(tmp_path, child):
+    from earnings_pipeline.pilot_workflow import make_pass
+    from earnings_pipeline.theme_config import WorkflowError
+
+    config, _ = seed_case(tmp_path, seed=False, review=True)
+    root = tmp_path / "data/runs/pilot/train/pass"
+    root.mkdir(parents=True)
+    outside = tmp_path / "outside"
+    outside.mkdir()
+    (root / child).symlink_to(outside)
+    rt = runtime(config, [])
+    with pytest.raises(WorkflowError, match="malformed_record"):
+        make_pass(
+            config,
+            rt,
+            rt.scorer,
+            partition=Partition.TRAIN,
+            directory=root,
+            fresh=None,
+            support_ready=lambda: None,
+            now=lambda: cases.NOW,
+        )
+
+
+def test_scorer_cache_corruption_refuses_before_publication(tmp_path):
+    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run
+    from earnings_pipeline.theme_config import WorkflowError
+
+    config, _ = seed_case(tmp_path, seed=False, review=True)
+    rt = runtime(config, [])
+    record = make_pass(
+        config,
+        rt,
+        rt.scorer,
+        partition=Partition.TRAIN,
+        directory=tmp_path / "data/runs/pilot/train/pass",
+        fresh=None,
+        support_ready=lambda: None,
+        now=lambda: cases.NOW,
+    )
+    loaded = load_pass(config, record)
+    artifact = bound_artifact(config, loaded)
+    scorer = next(
+        p
+        for p in (tmp_path / config.support_cache).glob("*.json")
+        if json.loads(p.read_bytes())["kind"] == "scorer"
+    )
+    scorer.write_text("INVENTED_CORRUPT_SENTINEL")
+    with pytest.raises(WorkflowError, match="cache_corrupt"):
+        make_run(
+            config,
+            loaded,
+            artifact,
+            directory=tmp_path / "data/runs/pilot/train/corrupt",
+            now=lambda: cases.NOW,
+        )
+    assert not (tmp_path / "data/runs/pilot/train/corrupt").exists()
+
+
+def test_fresh_policy_decides_without_changing_acquisition_state(tmp_path):
+    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run
+
+    config, _ = seed_case(tmp_path, seed=False, review=True)
+    rt = runtime(config, [])
+    base = make_pass(
+        config,
+        rt,
+        rt.scorer,
+        partition=Partition.DEV,
+        directory=tmp_path / "data/runs/pilot/dev/pass",
+        fresh=None,
+        support_ready=lambda: None,
+        now=lambda: cases.NOW,
+    )
+    artifact = bound_artifact(config, load_pass(config, base))
+    before = {p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()}
+    directory = tmp_path / "data/runs/pilot/dev/fresh/s-1"
+    fresh = make_pass(
+        config,
+        rt,
+        rt.scorer,
+        partition=Partition.DEV,
+        directory=directory,
+        fresh="s-1",
+        support_ready=lambda: None,
+        now=lambda: cases.NOW,
+    )
+    record = make_run(
+        config,
+        load_pass(config, fresh),
+        artifact,
+        directory=directory,
+        now=lambda: cases.NOW,
+    )
+    assert record.fresh == "s-1" and record.status == "complete"
+    assert before == {
+        p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()
+    }
+
+
+def test_crash_resume_binds_policies_and_complete_requires_all_proposals(tmp_path):
+    from dataclasses import replace
+
+    from earnings_pipeline.pilot_workflow import _complete, load_pass, make_pass
+    from earnings_pipeline.theme_config import WorkflowError
+
+    config, _ = seed_case(tmp_path, seed=False, review=True)
+    rt = runtime(config, [])
+    directory = tmp_path / "data/runs/pilot/train/pass"
+    record = make_pass(
+        config,
+        rt,
+        rt.scorer,
+        partition=Partition.TRAIN,
+        directory=directory,
+        fresh=None,
+        support_ready=lambda: None,
+        now=lambda: cases.NOW,
+    )
+    loaded = load_pass(config, record)
+    truncated = replace(
+        loaded.primary,
+        targets=(),
+        evidence=(),
+        contexts=(),
+        entailment=(),
+        trials=(),
+        attempts=(),
+        usage=(),
+        outcomes=(),
+    )
+    assert not _complete(
+        loaded.sources.stored_run, loaded.proposal, truncated, truncated
+    )
+    (directory / "pass.json").unlink()
+    changed = config.model_copy(
+        update={
+            "support_ceilings": config.support_ceilings.model_copy(
+                update={"scorer_per_run": config.support_ceilings.scorer_per_run + 1}
+            )
+        }
+    )
+    with pytest.raises(WorkflowError, match="input_changed"):
+        make_pass(
+            changed,
+            rt,
+            rt.scorer,
+            partition=Partition.TRAIN,
+            directory=directory,
+            fresh=None,
+            support_ready=lambda: None,
+            now=lambda: cases.NOW,
+        )
```

The same task adds its dictionary contract test:

```diff
--- a/tests/contracts/test_data_dictionary.py
+++ b/tests/contracts/test_data_dictionary.py
@@ -29,6 +29,7 @@
     model_runtime,
     pilot_inputs,
     pilot_records,
+    pilot_workflow,
     theme_config,
     theme_workflow,
 )
@@ -732,9 +733,10 @@
 }
 PILOT_DATACLASSES = {
     "PilotIntake": pilot_inputs.PilotIntake,
+    "LoadedPass": pilot_workflow.LoadedPass,
 }
 PILOT_ENUMS = {}
-PILOT_MODULES = [pilot_records, pilot_inputs]
+PILOT_MODULES = [pilot_records, pilot_inputs, pilot_workflow]


 @pytest.mark.parametrize(("name", "model"), PILOT_MODELS.items(), ids=PILOT_MODELS)
```

- [x] **Step 2: Observe red**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_workflow.py --tb=short -q
uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_data_dictionary.py --tb=short -q
```

Expected: the new phase-runner module/contract is missing. The scripted cases cover the acknowledgment boundary, no-state writes, live-pass zero-dispatch replay, fresh isolation and crash IDs, policy tampering, missing/corrupt replay entries, symlink preflight, resumed configuration changes and partial-status spoofing. No native model is loaded.

- [x] **Step 3: Apply the phase runner**

> Deviation: Owner approved coding/stability run-ID comparisons on reload, with resealed-record regressions, to enforce configured IDs.

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/src/earnings_pipeline/pilot_workflow.py
@@ -0,0 +1,585 @@
+"""Phase-by-phase passes and frozen-policy runs. No pass or fresh run changes state."""
+
+import json
+from collections.abc import Callable, Iterable
+from dataclasses import dataclass, replace
+from datetime import datetime
+from pathlib import Path
+
+from earnings_core import digest, sha256_hex
+from earnings_ingestion.fetch.store import write_new
+from earnings_themes.coding import validate_proposal_support
+from earnings_themes.coding.cache import CodingCache
+from earnings_themes.coding.decide import AssignmentPolicy
+from earnings_themes.coding.records import ClassificationRecord
+from earnings_themes.coding.run import ProposalRun, propose_run
+from earnings_themes.coding.store import (
+    read_coding_run,
+    write_coding_run,
+)
+from earnings_themes.evaluation import (
+    CalibratedPolicy,
+    CalibrationArtifact,
+    EvaluationError,
+    EvaluationProblem,
+    frozen_configuration,
+)
+from earnings_themes.evaluation.calibration import configuration_hash
+from earnings_themes.extraction.cache import CachedAdapter
+from earnings_themes.extraction.records import ExtractionRejection
+from earnings_themes.extraction.run import extract_run
+from earnings_themes.extraction.store import StoredRun, read_run, write_run
+from earnings_themes.records import checked, sealed
+from earnings_themes.split import Partition
+from earnings_themes.support import (
+    assess_run,
+    read_support_run,
+    write_support_run,
+)
+from earnings_themes.support.cache import SupportCache
+from earnings_themes.support.records import (
+    EntailmentSignal,
+    JudgeTrial,
+    SupportSources,
+    support_configuration,
+)
+from earnings_themes.support.scorers import EntailmentScorer
+from earnings_themes.support.store import StoredSupportRun
+
+from earnings_pipeline.pilot_records import (
+    PassRecord,
+    ProposalSnapshot,
+    RunRecord,
+    json_bytes,
+    read_json,
+)
+from earnings_pipeline.theme_config import (
+    FileSelection,
+    StoredSelection,
+    WorkflowConfig,
+    WorkflowError,
+    confined_path,
+    read_selected,
+    validate_paths,
+)
+from earnings_pipeline.theme_workflow import (
+    WorkflowRuntime,
+    finalize_coding,
+    load_workflow_inputs,
+    replay_runtime,
+    run_theme_workflow,
+    validate_workflow_policy,
+    verify_extraction_configuration,
+    workflow_configuration_hashes,
+)
+
+
+@dataclass(frozen=True, repr=False)
+class LoadedPass:
+    record: PassRecord
+    sources: SupportSources
+    proposal: ProposalRun
+    primary: StoredSupportRun
+    alternative: StoredSupportRun
+
+
+def selected_file(config: WorkflowConfig, path: Path) -> FileSelection:
+    return FileSelection(
+        path=path.relative_to(config.repo).as_posix(),
+        sha256=sha256_hex(path.read_bytes()),
+    )
+
+
+def selected_run(config: WorkflowConfig, path: Path) -> StoredSelection:
+    return StoredSelection(
+        directory=path.relative_to(config.repo).as_posix(),
+        sha256=sha256_hex((path / "run.json").read_bytes()),
+    )
+
+
+def pilot_path(config: WorkflowConfig, path: Path) -> Path:
+    return confined_path(
+        config.repo, path.relative_to(config.repo).as_posix(), "data/runs/pilot"
+    )
+
+
+def phase_path(config: WorkflowConfig, path: Path) -> Path:
+    path = pilot_path(config, path)
+    if path.is_dir():
+        for child in path.iterdir():
+            pilot_path(config, child)
+    return path
+
+
+def stored_directory(config: WorkflowConfig, selected: StoredSelection) -> Path:
+    path = phase_path(
+        config, confined_path(config.repo, selected.directory, "data/runs/pilot")
+    )
+    if sha256_hex((path / "run.json").read_bytes()) != selected.sha256:
+        raise WorkflowError("input_changed")
+    # Every child is checked before a public reader can open it.
+    for child in path.iterdir():
+        confined_path(
+            config.repo, child.relative_to(config.repo).as_posix(), "data/runs/pilot"
+        )
+    return path
+
+
+def load_pass(config: WorkflowConfig, record: PassRecord) -> LoadedPass:
+    checked(record, "pass")
+    if record.configuration_hash != digest(config.model_dump(mode="json")):
+        raise WorkflowError("input_changed")
+    if record.event_ids != config.selected_event_ids:
+        raise WorkflowError("input_changed")
+    loaded = load_workflow_inputs(config, replay_runtime(config))
+    extraction = read_run(stored_directory(config, record.extraction))
+    verify_extraction_configuration(config, extraction, loaded.bundles, loaded.template)
+    if (
+        extraction.record.cache_mode != record.mode
+        or extraction.record.stability_run_id != record.stability_run_id
+    ):
+        raise WorkflowError("input_changed")
+    _integrity(extraction.rejections)
+    sources = SupportSources(
+        extraction, loaded.bundles, loaded.codebook, loaded.provenance_hash
+    )
+    path = confined_path(config.repo, record.proposals.path, "data/runs/pilot")
+    read_selected(config, record.proposals)
+    proposal = read_json(path, ProposalSnapshot, "proposals", seal=False).run()
+    primary = read_support_run(stored_directory(config, record.primary))
+    alternative = read_support_run(stored_directory(config, record.alternative))
+    if primary.record.scorer_identity != config.scorer_identity or any(
+        run.record.cache_mode != record.mode
+        or run.record.stability_run_id != record.stability_run_id
+        for run in (primary, alternative)
+    ):
+        raise WorkflowError("input_changed")
+    if (
+        proposal.record.configuration_hash
+        != workflow_configuration_hashes(config, sources, cache_mode=record.mode)[0]
+    ):
+        raise WorkflowError("input_changed")
+    for run in (primary, alternative):
+        expected = digest(
+            support_configuration(
+                config.support_policy,
+                config.support_ceilings,
+                run.record.scorer_identity,
+                config.judge_identities,
+                config.extractor_family,
+                record.mode,
+            )
+        )
+        if run.record.configuration_hash != expected:
+            raise WorkflowError("input_changed")
+    _integrity(proposal.classifications)
+    _integrity(
+        (
+            *primary.entailment,
+            *primary.trials,
+            *alternative.entailment,
+            *alternative.trials,
+        )
+    )
+    validate_proposal_support(proposal, primary, sources)
+    validate_proposal_support(proposal, alternative, sources)
+    if tuple(t.target_id for t in primary.targets) != tuple(
+        t.target_id for t in alternative.targets
+    ):
+        raise WorkflowError("input_changed")
+    expected_status = (
+        "complete"
+        if _complete(extraction, proposal, primary, alternative)
+        else "partial"
+    )
+    if record.status != expected_status:
+        raise WorkflowError("input_changed")
+    return LoadedPass(record, sources, proposal, primary, alternative)
+
+
+def _complete(
+    extraction: StoredRun, proposal: ProposalRun, *support: StoredSupportRun
+) -> bool:
+    return (
+        all(d.outcome.value == "completed" for d in extraction.documents)
+        and all(c.status == "completed" for c in proposal.classifications)
+        and all(
+            tuple(t.target for t in run.targets) == proposal.targets for run in support
+        )
+        and not any(
+            o.status.value in {"incomplete", "refused"}
+            for run in support
+            for o in run.outcomes
+        )
+    )
+
+
+def _integrity(
+    rows: Iterable[
+        ExtractionRejection | ClassificationRecord | EntailmentSignal | JudgeTrial
+    ],
+) -> None:
+    for row in rows:
+        reason = getattr(row, "reason", None)
+        reason = getattr(reason, "value", reason)
+        if reason in {
+            "cache_corrupt",
+            "input_changed",
+            "model_mismatch",
+            "malformed_record",
+        }:
+            raise WorkflowError(reason)
+
+
+def check_cache_paths(config: WorkflowConfig, fresh: str | None) -> None:
+    for reference in (
+        config.extraction_cache,
+        config.coding_cache,
+        config.support_cache,
+    ):
+        path = confined_path(config.repo, reference, "data/runs/pilot")
+        if fresh is not None:
+            path = confined_path(
+                config.repo, reference + "/fresh/" + fresh, "data/runs/pilot"
+            )
+        for child in path.glob("*.json"):
+            pilot_path(config, child)
+
+
+def make_pass(
+    config: WorkflowConfig,
+    runtime: WorkflowRuntime,
+    alternative: EntailmentScorer,
+    *,
+    partition: Partition,
+    directory: Path,
+    fresh: str | None,
+    support_ready: Callable[[], None],
+    now: Callable[[], datetime],
+) -> PassRecord:
+    if partition not in (Partition.TRAIN, Partition.DEV) or (
+        fresh and partition is not Partition.DEV
+    ):
+        raise WorkflowError("malformed_record")
+    directory = confined_path(
+        config.repo, directory.relative_to(config.repo).as_posix(), "data/runs/pilot"
+    )
+    check_cache_paths(config, fresh)
+    mode = "fresh" if fresh is not None else "live"
+    if fresh is not None:
+        for cache in (
+            config.extraction_cache,
+            config.coding_cache,
+            config.support_cache,
+        ):
+            confined_path(config.repo, cache + "/fresh/" + fresh, "data/runs/pilot")
+    if fresh is not None and (
+        directory.exists()
+        or any(
+            (confined_path(config.repo, cache) / "fresh" / fresh).exists()
+            for cache in (
+                config.extraction_cache,
+                config.coding_cache,
+                config.support_cache,
+            )
+        )
+    ):
+        raise WorkflowError("state_run_conflict")
+    manifest = pilot_path(config, directory / "pass.json")
+    if manifest.exists():
+        record = read_json(manifest, PassRecord, "pass")
+        load_pass(config, record)
+        return record
+    for name in ("extraction", "support", "alternative", "proposals.json", "pass.json"):
+        phase_path(config, directory / name)
+    loaded = load_workflow_inputs(config, runtime)
+    directory.mkdir(parents=True, exist_ok=True)
+    started = config.fixture_started_at or now()
+    extract_dir = phase_path(config, directory / "extraction")
+    if not extract_dir.exists():
+        result = extract_run(
+            loaded.bundles,
+            CachedAdapter(
+                runtime.extractor,
+                confined_path(config.repo, config.extraction_cache),
+                mode,
+                stability_run_id=fresh,
+            ),
+            config.extraction_policy,
+            loaded.template,
+            config.extraction_ceilings,
+            run_id=config.extraction_run_id,
+            started_at=started,
+            software=config.software,
+        )
+        write_run(extract_dir, StoredRun.of(result), loaded.bundles)
+    extraction = read_run(extract_dir)
+    verify_extraction_configuration(config, extraction, loaded.bundles, loaded.template)
+    if (
+        extraction.record.cache_mode != mode
+        or extraction.record.stability_run_id != fresh
+    ):
+        raise WorkflowError("input_changed")
+    _integrity(extraction.rejections)
+    sources = SupportSources(
+        extraction, loaded.bundles, loaded.codebook, loaded.provenance_hash
+    )
+    snapshot = pilot_path(config, directory / "proposals.json")
+    if snapshot.exists():
+        proposal = read_json(snapshot, ProposalSnapshot, "proposals", seal=False).run()
+    else:
+        proposal = propose_run(
+            config.coding_run_id,
+            sources,
+            tuple((c.doc_id, c.claim_id) for c in extraction.claims),
+            runtime.classifier,
+            config.coding_policy,
+            config.coding_ceilings,
+            cache=CodingCache(
+                confined_path(config.repo, config.coding_cache),
+                mode,
+                stability_run_id=fresh,
+            ),
+            started_at=extraction.record.started_at,
+            software=config.software,
+        )
+        write_new(snapshot, json_bytes(ProposalSnapshot.of(proposal)))
+    if (
+        proposal.record.configuration_hash
+        != workflow_configuration_hashes(config, sources, cache_mode=mode)[0]
+        or proposal.record.run_id != config.coding_run_id
+        or proposal.record.stability_run_id != fresh
+    ):
+        raise WorkflowError("input_changed")
+    _integrity(proposal.classifications)
+    # The local server operator performs this checkpoint; adapters cannot unload servers.
+    support_ready()
+    supports = []
+    for kind, scorer in (("support", runtime.scorer), ("alternative", alternative)):
+        path = phase_path(config, directory / kind)
+        if not path.exists():
+            support = assess_run(
+                config.support_run_id
+                + ("-alternative" if kind == "alternative" else ""),
+                sources,
+                proposal.targets,
+                scorer,
+                runtime.judges,
+                config.support_policy,
+                config.support_ceilings,
+                extractor_family=config.extractor_family,
+                cache=SupportCache(
+                    confined_path(config.repo, config.support_cache),
+                    mode,
+                    stability_run_id=fresh,
+                ),
+                started_at=extraction.record.started_at,
+                software=config.software,
+            )
+            write_support_run(path, support, sources)
+        support = read_support_run(path)
+        if (
+            support.record.scorer_identity != scorer.identity
+            or support.record.cache_mode != mode
+            or support.record.stability_run_id != fresh
+        ):
+            raise WorkflowError("input_changed")
+        expected = digest(
+            support_configuration(
+                config.support_policy,
+                config.support_ceilings,
+                scorer.identity,
+                config.judge_identities,
+                config.extractor_family,
+                mode,
+            )
+        )
+        if support.record.configuration_hash != expected:
+            raise WorkflowError("input_changed")
+        _integrity((*support.entailment, *support.trials))
+        validate_proposal_support(proposal, support, sources)
+        supports.append(support)
+    status = "complete" if _complete(extraction, proposal, *supports) else "partial"
+    record = sealed(
+        PassRecord(
+            partition=partition,
+            mode=mode,
+            stability_run_id=fresh,
+            event_ids=config.selected_event_ids,
+            configuration_hash=digest(config.model_dump(mode="json")),
+            extraction=selected_run(config, extract_dir),
+            proposals=selected_file(config, snapshot),
+            primary=selected_run(config, directory / "support"),
+            alternative=selected_run(config, directory / "alternative"),
+            status=status,
+            content_hash="0" * 64,
+        )
+    )
+    write_new(manifest, json_bytes(record))
+    return record
+
+
+def bind_policy(
+    config: WorkflowConfig,
+    loaded: LoadedPass,
+    artifact: CalibrationArtifact,
+    *,
+    replay: bool,
+) -> AssignmentPolicy | None:
+    checked(artifact, "calibration")
+    frozen = frozen_configuration(
+        loaded.sources.stored_run.record,
+        loaded.proposal.record,
+        loaded.primary.record,
+        config.support_policy,
+    )
+    if configuration_hash(frozen, artifact.selection) != artifact.configuration_hash:
+        raise WorkflowError("input_changed")
+    if replay:
+        coding_hash, support_hash = workflow_configuration_hashes(
+            config, loaded.sources
+        )
+    else:
+        coding_hash, support_hash = (
+            loaded.proposal.record.configuration_hash,
+            loaded.primary.record.configuration_hash,
+        )
+    try:
+        return CalibratedPolicy(
+            artifact,
+            codebook=loaded.primary.record.codebook,
+            classifier_configuration_hash=coding_hash,
+            support_configuration_hash=support_hash,
+        )
+    except EvaluationError as error:
+        if error.problem is EvaluationProblem.NO_CANDIDATE:
+            return None
+        raise
+
+
+def verify_replay_cache(config: WorkflowConfig, loaded: LoadedPass) -> None:
+    """Exercise every primary replay request before publication or state changes."""
+    check_cache_paths(config, None)
+    runtime = replay_runtime(config)
+    proposal = propose_run(
+        config.coding_run_id,
+        loaded.sources,
+        tuple((c.doc_id, c.claim_id) for c in loaded.sources.stored_run.claims),
+        runtime.classifier,
+        config.coding_policy,
+        config.coding_ceilings,
+        cache=CodingCache(confined_path(config.repo, config.coding_cache), "replay"),
+        started_at=loaded.sources.stored_run.record.started_at,
+        software=config.software,
+    )
+    for row in proposal.classifications:
+        if row.reason in {"replay_miss", "replay_dispatch_forbidden"}:
+            raise WorkflowError("replay_miss")
+        if row.reason in {
+            "cache_corrupt",
+            "input_changed",
+            "model_mismatch",
+            "malformed_record",
+        }:
+            raise WorkflowError(row.reason)
+    support = assess_run(
+        config.support_run_id,
+        loaded.sources,
+        proposal.targets,
+        runtime.scorer,
+        runtime.judges,
+        config.support_policy,
+        config.support_ceilings,
+        extractor_family=config.extractor_family,
+        cache=SupportCache(confined_path(config.repo, config.support_cache), "replay"),
+        started_at=loaded.sources.stored_run.record.started_at,
+        software=config.software,
+    )
+    for assessment in support.assessments:
+        for row in (*assessment.entailment, *assessment.trials):
+            if row.reason in {"replay_miss", "replay_dispatch_forbidden"}:
+                raise WorkflowError("replay_miss")
+            if row.reason in {
+                "cache_corrupt",
+                "input_changed",
+                "model_mismatch",
+                "malformed_record",
+            }:
+                raise WorkflowError(row.reason)
+
+
+def make_run(
+    config: WorkflowConfig,
+    loaded: LoadedPass,
+    artifact: CalibrationArtifact,
+    *,
+    directory: Path,
+    now: Callable[[], datetime],
+) -> RunRecord:
+    directory = confined_path(
+        config.repo, directory.relative_to(config.repo).as_posix(), "data/runs/pilot"
+    )
+    fresh = loaded.record.stability_run_id
+    if fresh is None and loaded.record.mode != "live":
+        raise WorkflowError("input_changed")
+    policy = bind_policy(config, loaded, artifact, replay=fresh is None)
+    coding_dir = phase_path(config, directory / "coding")
+    if fresh is not None:
+        coding = finalize_coding(
+            loaded.proposal, loaded.primary, loaded.sources, policy
+        )
+        write_coding_run(coding_dir, coding, loaded.sources, loaded.primary, policy)
+    else:
+        verify_replay_cache(config, loaded)
+        fields = config.model_dump(mode="json")
+        fields.update(
+            output_dir=directory.relative_to(config.repo).as_posix(),
+            stored_extraction=loaded.record.extraction.model_dump(mode="json"),
+            stored_coding=None,
+            stored_support=None,
+            stored_analysis=None,
+            policy_reference=None
+            if policy is None
+            else policy.reference.model_dump(mode="json"),
+        )
+        replay_config = WorkflowConfig.model_validate_json(json.dumps(fields))
+        validate_paths(replay_config, repo=config.repo)
+        runtime = replace(replay_runtime(replay_config), assignment_policy=policy)
+        validate_workflow_policy(replay_config, policy)
+        result = run_theme_workflow(replay_config, runtime, now=now)
+        if result.status == "failed" or result.reason in {
+            "replay_miss",
+            "replay_dispatch_forbidden",
+        }:
+            raise WorkflowError(result.reason or "processing_failed")
+    coding = read_coding_run(coding_dir)
+    # Cache misses can be represented as refused/incomplete stage rows; none is a successful replay.
+    if fresh is None and any(
+        reason in {"replay_miss", "replay_dispatch_forbidden"}
+        for reason, _ in (
+            *coding.record.counts_by_reason,
+            *coding.record.counts_by_decision_reason,
+        )
+    ):
+        raise WorkflowError("replay_miss")
+    pass_path = (
+        confined_path(
+            config.repo, loaded.record.extraction.directory, "data/runs/pilot"
+        ).parent
+        / "pass.json"
+    )
+    record = sealed(
+        RunRecord(
+            partition=loaded.record.partition,
+            fresh=fresh,
+            event_ids=loaded.record.event_ids,
+            pass_record=selected_file(config, pass_path),
+            coding=selected_run(config, coding_dir),
+            calibration_hash=artifact.content_hash,
+            configuration_hash=artifact.configuration_hash,
+            status=loaded.record.status,
+            content_hash="0" * 64,
+        )
+    )
+    write_new(pilot_path(config, directory / "run-record.json"), json_bytes(record))
+    return record
```

Apply the matching dictionary rows in this implementation step:

```diff
--- a/docs/data-dictionary.md
+++ b/docs/data-dictionary.md
@@ -7116,3 +7116,18 @@
 | `config` | WorkflowConfig | Current partition's verified workflow selection |
 | `partition` | Partition | Requested `train` or `dev` partition |
 | `gold` | tuple of Gold | Checked committed gold for the current selection |
+
+### `LoadedPass`
+
+A transient `earnings_pipeline.pilot_workflow` dataclass. `load_pass` checks the
+sealed checkpoint, its selected files and stored runs, source provenance,
+proposal-to-support bindings for both scorers, and frozen configuration before
+returning these inputs to calibration, assignment or reporting.
+
+| Field | Type | Meaning |
+| --- | --- | --- |
+| `record` | PassRecord | Verified local pass checkpoint |
+| `sources` | SupportSources | Original extraction, canonical, raw and codebook bindings |
+| `proposal` | ProposalRun | Reconstructed verified classifier proposals |
+| `primary` | StoredSupportRun | Reverified primary MiniCheck support results |
+| `alternative` | StoredSupportRun | Reverified alternative DeBERTa support results |
```

- [x] **Step 4: Verify green and Ruff**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_workflow.py tests/contracts/test_data_dictionary.py --tb=short -q
uv run --locked --offline --no-sync ruff check apps/earnings-pipeline/src/earnings_pipeline/pilot_workflow.py apps/earnings-pipeline/tests/test_pilot_workflow.py tests/contracts/test_data_dictionary.py
uv run --locked --offline --no-sync ruff format --check apps/earnings-pipeline/src/earnings_pipeline/pilot_workflow.py apps/earnings-pipeline/tests/test_pilot_workflow.py tests/contracts/test_data_dictionary.py
```

Expected: selected cases pass and Ruff is clean. Report actual counts.

- [x] **Step 5: Review and commit the task**

```bash
git log -3 --oneline
git add apps/earnings-pipeline/src/earnings_pipeline/pilot_workflow.py apps/earnings-pipeline/tests/test_pilot_workflow.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(pilot): add phase passes and frozen-policy replay"
```

---

### Task 9: Sample, render and merge support labels

**Files:** create `apps/earnings-pipeline/tests/test_pilot_labels.py` and `apps/earnings-pipeline/src/earnings_pipeline/pilot_labels.py`. This task uses only invented fixtures. Apply its dictionary supplement in this same task before its checkpoint.

**Interfaces:**

Consumes `PilotIntake`, `LoadedPass`, and the package's `SupportLabelSet` TOML reader/writer. Produces:

```python
checked_pass(intake: PilotIntake, loaded: LoadedPass, *, fresh: bool = False) -> None
local_path(intake: PilotIntake, path: Path) -> Path
sample(intake: PilotIntake, loaded: LoadedPass, extensions: int) -> tuple[str, ...]
working_path(intake: PilotIntake) -> Path
committed_labels(intake: PilotIntake) -> SupportLabelSet | None
write_view(intake: PilotIntake, loaded: LoadedPass, extensions: int, labelled_on: date) -> tuple[Path, Path]
check_working(intake: PilotIntake, loaded: LoadedPass, extensions: int) -> Path
```

The view is local Markdown and the working file is local TOML. Promotion validates the entire working file and preserves existing committed rows and extension metadata. Unknown label targets are refused using a field path.

- [x] **Step 1: Add the failing tests**

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/tests/test_pilot_labels.py
@@ -0,0 +1,141 @@
+"""Local label templates and append-only checked labels, over invented passes."""
+
+import importlib
+from datetime import date
+from types import SimpleNamespace
+
+import pytest
+from earnings_themes.evaluation import load_labels
+from earnings_themes.records import RecordError
+from earnings_themes.split import Partition
+
+cases = importlib.import_module("apps.earnings-pipeline.tests.test_pilot_workflow")
+prereg_cases = importlib.import_module(
+    "packages.earnings-themes.tests.evaluation.test_preregistration"
+)
+
+
+def make_case(tmp_path):
+    from earnings_pipeline.pilot_workflow import load_pass, make_pass
+
+    config, _ = cases.seed_case(tmp_path, seed=False, review=True)
+    rt = cases.runtime(config, [])
+    record = make_pass(
+        config,
+        rt,
+        rt.scorer,
+        partition=Partition.TRAIN,
+        directory=tmp_path / "data/runs/pilot/train/pass",
+        fresh=None,
+        support_ready=lambda: None,
+        now=lambda: cases.cases.NOW,
+    )
+    loaded = load_pass(config, record)
+    prereg = prereg_cases.freeze_preregistration(prereg_cases.fields())
+    intake = SimpleNamespace(
+        config=config,
+        settings=SimpleNamespace(
+            alternative_scorer=loaded.alternative.record.scorer_identity
+        ),
+        partition=Partition.TRAIN,
+        preregistration=prereg,
+        local=tmp_path / "data/runs/pilot",
+        pinned=SimpleNamespace(evaluation=tmp_path / "evaluation"),
+        layout=SimpleNamespace(shown=lambda path: path.name),
+    )
+    return intake, loaded
+
+
+def test_view_writes_local_template_with_unsure_defaults_and_never_prints(
+    tmp_path, capsys
+):
+    from earnings_pipeline.pilot_labels import sample, write_view
+
+    intake, loaded = make_case(tmp_path)
+    drawn = sample(intake, loaded, 0)
+    view, working = write_view(intake, loaded, 0, date(2026, 10, 13))
+    assert drawn
+    assert view.is_relative_to(intake.local / "labels/views")
+    assert "Invented expansion." in view.read_text()
+    assert "score" not in view.read_text().lower()
+    labels = load_labels(working)
+    assert {l.claim_support.value for l in labels.labels} == {"unsure"}
+    assert {l.theme_fit.value for l in labels.labels} == {"unsure"}
+    assert "deliberately confirm labelled_on" in working.read_text()
+    assert capsys.readouterr().out == ""
+
+
+def test_check_never_promotes_a_changed_hash_or_counter_without_growth(
+    tmp_path, monkeypatch
+):
+    import earnings_pipeline.pilot_labels as module
+    from earnings_pipeline.pilot_labels import check_working, write_view
+    from earnings_themes.evaluation import labels_toml
+
+    monkeypatch.setattr(module, "require_committed", lambda *args: None)
+    intake, loaded = make_case(tmp_path)
+    _, working = write_view(intake, loaded, 0, date(2026, 10, 13))
+    labels = load_labels(working)
+    changed = labels.labels[0].model_copy(update={"target_input_hash": "a" * 64})
+    working.write_text(labels_toml(labels.model_copy(update={"labels": (changed,)})))
+    with pytest.raises(RecordError, match="target_hash_mismatch"):
+        check_working(intake, loaded, 0)
+    working.write_text(labels_toml(labels))
+    target = check_working(intake, loaded, 0)
+    before = target.read_bytes()
+    working.write_text(labels_toml(labels.model_copy(update={"train_extensions": 1})))
+    with pytest.raises(RecordError, match="labels_changed"):
+        check_working(intake, loaded, 1)
+    assert target.read_bytes() == before
+
+
+def test_labels_reject_wrong_alternative_and_confine_working_symlinks(tmp_path):
+    from dataclasses import replace
+
+    from earnings_pipeline.pilot_labels import write_view
+    from earnings_pipeline.theme_config import WorkflowError
+
+    intake, loaded = make_case(tmp_path)
+    intake.settings.alternative_scorer = (
+        loaded.alternative.record.scorer_identity.model_copy(
+            update={"input_limit": 999}
+        )
+    )
+    with pytest.raises(WorkflowError, match="input_changed"):
+        write_view(intake, loaded, 0, date(2026, 10, 13))
+    intake.settings.alternative_scorer = loaded.alternative.record.scorer_identity
+    (intake.local / "labels").mkdir(parents=True)
+    outside = tmp_path / "outside.toml"
+    outside.write_text("INVENTED_PRIVATE_SENTINEL")
+    (intake.local / "labels/train-working.toml").symlink_to(outside)
+    with pytest.raises(WorkflowError, match="malformed_record"):
+        write_view(intake, replace(loaded), 0, date(2026, 10, 13))
+    assert outside.read_text() == "INVENTED_PRIVATE_SENTINEL"
+
+
+def test_existing_label_base_requires_head_and_unknown_target_is_redacted(
+    tmp_path, monkeypatch
+):
+    import earnings_pipeline.pilot_labels as module
+    from earnings_themes.evaluation import labels_toml
+
+    intake, loaded = make_case(tmp_path)
+    _, working = module.write_view(intake, loaded, 0, date(2026, 10, 13))
+    labels = load_labels(working)
+    changed = labels.labels[0].model_copy(
+        update={"target_id": "INVENTED SOURCE SENTINEL sentence"}
+    )
+    working.write_text(labels_toml(labels.model_copy(update={"labels": (changed,)})))
+    with pytest.raises(RecordError) as found:
+        module.check_working(intake, loaded, 0)
+    assert "INVENTED SOURCE" not in str(found.value)
+    working.write_text(labels_toml(labels))
+    target = module.check_working(intake, loaded, 0)
+    target.write_text("INVENTED SOURCE SENTINEL sentence")
+
+    def refuse(*args):
+        raise RecordError("labels", ("not_committed",))
+
+    monkeypatch.setattr(module, "require_committed", refuse)
+    with pytest.raises(RecordError, match="not_committed"):
+        module.check_working(intake, loaded, 0)
```

- [x] **Step 2: Confirm red**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_labels.py --tb=short -q
```

Expected: the new module is missing; the new task tests fail before implementation. Record the actual output.

- [x] **Step 3: Add the exact implementation**

> Deviation: Implemented the omitted dictionary supplement and closed missing committed label-base/Git failure refusals under owner-authorized spec-compliance corrections.

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/src/earnings_pipeline/pilot_labels.py
@@ -0,0 +1,189 @@
+"""Deterministic support labels: local views, user answers, checked append-only merge."""
+
+from datetime import date
+from pathlib import Path
+
+from earnings_themes.evaluation import (
+    SupportLabel,
+    SupportLabelSet,
+    check_labels,
+    label_pool,
+    label_views,
+    labels_toml,
+    load_labels,
+    merge_labels,
+    sample_targets,
+)
+from earnings_themes.evaluation.labels import ClaimAnswer, FitAnswer
+from earnings_themes.records import RecordError
+from earnings_themes.split import Partition
+from earnings_themes.support import reverify_support_run
+
+from earnings_pipeline.pilot_inputs import PilotIntake, require_committed
+from earnings_pipeline.pilot_workflow import LoadedPass
+from earnings_pipeline.stage6 import replace
+from earnings_pipeline.theme_config import WorkflowError, confined_path
+
+TEMPLATE = (
+    "# Working labels: read every view, edit both answers, and deliberately confirm labelled_on.\n"
+    "# unsure is a real answer, not a blank. Finish the whole sample before labels check.\n"
+    "# Existing committed labels cannot be edited; a train extension adds new targets.\n"
+)
+
+
+def checked_pass(
+    intake: PilotIntake, loaded: LoadedPass, *, fresh: bool = False
+) -> None:
+    if (
+        loaded.record.partition is not intake.partition
+        or loaded.record.event_ids != intake.config.selected_event_ids
+        or loaded.alternative.record.scorer_identity
+        != intake.settings.alternative_scorer
+        or (not fresh and loaded.record.mode != "live")
+    ):
+        raise WorkflowError("input_changed")
+
+
+def local_path(intake: PilotIntake, path: Path) -> Path:
+    return confined_path(
+        intake.config.repo,
+        path.relative_to(intake.config.repo).as_posix(),
+        "data/runs/pilot",
+    )
+
+
+def sample(intake: PilotIntake, loaded: LoadedPass, extensions: int) -> tuple[str, ...]:
+    checked_pass(intake, loaded)
+    if type(extensions) is not int or extensions < 0:
+        raise RecordError("train_extensions", ("malformed_record",))
+    outcomes = reverify_support_run(loaded.primary, loaded.sources)
+    events = {source.doc_id: source.event_id for source in intake.config.sources}
+    pool = label_pool(loaded.primary.targets, outcomes, events)
+    plan = intake.preregistration.sampling
+    train = intake.partition is Partition.TRAIN
+    size = (
+        plan.train_size + extensions * plan.extension_step if train else plan.dev_size
+    )
+    cap = plan.train_cap if train else plan.dev_cap
+    return sample_targets(pool, seed=plan.seed, size=size, cap=cap)
+
+
+def working_path(intake: PilotIntake) -> Path:
+    return local_path(
+        intake, intake.local / "labels" / f"{intake.partition.value}-working.toml"
+    )
+
+
+def committed_labels(intake: PilotIntake) -> SupportLabelSet | None:
+    path = confined_path(
+        intake.config.repo,
+        (intake.pinned.evaluation / "labels" / "support-labels-v1.toml")
+        .relative_to(intake.config.repo)
+        .as_posix(),
+    )
+    if not path.is_file():
+        return None
+    require_committed(intake.config.repo, path, "labels")
+    record = load_labels(path)
+    if record.preregistration_hash != intake.preregistration.content_hash:
+        raise RecordError("labels", ("preregistration_mismatch",))
+    return record
+
+
+def _checked(
+    record: SupportLabelSet,
+    intake: PilotIntake,
+    loaded: LoadedPass,
+    drawn: tuple[str, ...],
+) -> None:
+    found = check_labels(
+        record,
+        partition=intake.partition,
+        sample=drawn,
+        input_hashes={t.target_id: t.input_hash for t in loaded.primary.targets},
+        preregistration_hash=intake.preregistration.content_hash,
+    )
+    if found:
+        raise RecordError(
+            "labels", tuple(f"labels.target_id: {r.reason}" for r in found)
+        )
+
+
+def write_view(
+    intake: PilotIntake, loaded: LoadedPass, extensions: int, labelled_on: date
+) -> tuple[Path, Path]:
+    drawn = sample(intake, loaded, extensions)
+    working = working_path(intake)
+    old = load_labels(working) if working.is_file() else committed_labels(intake)
+    kept = {} if old is None else {l.target_id: l for l in old.of(intake.partition)}
+    if old is not None:
+        own = SupportLabelSet(
+            preregistration_hash=old.preregistration_hash,
+            train_extensions=old.train_extensions,
+            labels=tuple(kept.values()),
+        )
+        _checked(own, intake, loaded, tuple(kept))
+        if not set(kept) <= set(drawn):
+            raise RecordError("labels", ("not_sampled",))
+    hashes = {t.target_id: t.input_hash for t in loaded.primary.targets}
+    labels = tuple(
+        kept.get(target)
+        or SupportLabel(
+            target_id=target,
+            target_input_hash=hashes[target],
+            partition=intake.partition,
+            claim_support=ClaimAnswer.UNSURE,
+            theme_fit=FitAnswer.UNSURE,
+            labelled_on=labelled_on,
+        )
+        for target in drawn
+    )
+    committed = committed_labels(intake)
+    train_extensions = (
+        extensions
+        if intake.partition is Partition.TRAIN
+        else (committed.train_extensions if committed else 0)
+    )
+    record = SupportLabelSet(
+        preregistration_hash=intake.preregistration.content_hash,
+        train_extensions=train_extensions,
+        labels=labels,
+    )
+    view = local_path(
+        intake, intake.local / "labels/views" / f"{intake.partition.value}.md"
+    )
+    # sample() reverifies before the library renderer is called (H1).
+    replace(view, label_views(loaded.primary, loaded.sources, drawn))
+    replace(working, TEMPLATE + labels_toml(record))
+    return view, working
+
+
+def check_working(intake: PilotIntake, loaded: LoadedPass, extensions: int) -> Path:
+    working = load_labels(working_path(intake))
+    drawn = sample(intake, loaded, extensions)
+    _checked(working, intake, loaded, drawn)
+    committed = committed_labels(intake)
+    expected = (
+        extensions
+        if intake.partition is Partition.TRAIN
+        else (committed.train_extensions if committed else 0)
+    )
+    if working.train_extensions != expected:
+        raise RecordError("train_extensions", ("labels_changed",))
+    if (
+        committed is not None
+        and extensions > committed.train_extensions
+        and intake.partition is Partition.TRAIN
+        and len(working.of(Partition.TRAIN)) <= len(committed.of(Partition.TRAIN))
+    ):
+        raise RecordError("train_extensions", ("labels_changed",))
+    merged = merge_labels(committed, working, intake.partition)
+    target = confined_path(
+        intake.config.repo,
+        (intake.pinned.evaluation / "labels/support-labels-v1.toml")
+        .relative_to(intake.config.repo)
+        .as_posix(),
+    )
+    # This named file is append-only through merge_labels, unlike immutable versioned artifacts.
+    replace(target, labels_toml(merged))
+    return target
```

- [x] **Step 4: Confirm green and formatting**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_labels.py --tb=short -q
uv run --locked --offline --no-sync --all-packages ruff check apps/earnings-pipeline/tests/test_pilot_labels.py apps/earnings-pipeline/src/earnings_pipeline/pilot_labels.py
uv run --locked --offline --no-sync --all-packages ruff format --check apps/earnings-pipeline/tests/test_pilot_labels.py apps/earnings-pipeline/src/earnings_pipeline/pilot_labels.py
git diff --check
```

Expected: all named tests pass and Ruff is clean. Save the actual task evidence; then request the task review before committing its reviewed implementation and dictionary changes.

- [x] **Step 5: Review and commit this task**

Close the task review before committing.

```bash
git add apps/earnings-pipeline/src/earnings_pipeline/pilot_labels.py apps/earnings-pipeline/tests/test_pilot_labels.py
git commit -m "feat(pilot): add sample view and checked label promotion"
```

### Task 10: Calibrate from committed train labels

**Files:** create `apps/earnings-pipeline/tests/test_pilot_calibration.py` and `apps/earnings-pipeline/src/earnings_pipeline/pilot_calibration.py`. This task uses only invented fixtures. Apply its dictionary supplement in this same task before its checkpoint.

**Interfaces:**

Consumes Task 9's checked baseline and committed labels, Task 7's committed-byte gate, and `calibrate` / `CalibrationArtifact` from evaluation. Produces:

```python
read_label_bytes(path: Path) -> tuple[SupportLabelSet, bytes]
calibrate_pilot(intake: PilotIntake, loaded: LoadedPass) -> Path
checked_calibration(intake: PilotIntake) -> CalibrationArtifact
validate_calibration_labels(intake: PilotIntake, artifact: CalibrationArtifact) -> None
evaluation_path(intake: PilotIntake, name: str) -> Path
```

Calibration hashes the exact parsed label bytes. Later validation finds those original bytes in reachable HEAD history, refuses changed train labels or extension metadata, and permits a dev append. Output targets are confined before immutable writes.

- [x] **Step 1: Add the failing tests**

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/tests/test_pilot_calibration.py
@@ -0,0 +1,130 @@
+"""Calibration intake binds exactly parsed bytes and Stage 9's proposal/source gate."""
+
+import importlib
+
+import pytest
+from earnings_core import sha256_hex
+from earnings_themes.evaluation import EvaluationError
+
+cases = importlib.import_module("apps.earnings-pipeline.tests.test_pilot_labels")
+
+
+def test_calibration_hashes_exact_label_bytes_and_checks_sample(tmp_path, monkeypatch):
+    from datetime import date
+
+    import earnings_pipeline.pilot_calibration as module
+    from earnings_pipeline.pilot_labels import check_working, write_view
+
+    monkeypatch.setattr(module, "require_committed", lambda *args: None)
+    intake, loaded = cases.make_case(tmp_path)
+    _, working = write_view(intake, loaded, 0, date(2026, 10, 13))
+    target = check_working(intake, loaded, 0)
+    target.write_bytes(b"# invented intentional comment\n" + target.read_bytes())
+    before = target.read_bytes()
+    seen = {}
+
+    def capture(preregistration, labels, **kwargs):
+        seen.update(kwargs)
+        return cases.cases.bound_artifact(intake.config, loaded)
+
+    monkeypatch.setattr(module, "calibrate", capture)
+    artifact = module.calibrate_pilot(intake, loaded)
+    assert seen["labels_hash"] == sha256_hex(before)
+    assert artifact.is_file()
+    assert target.read_bytes() == before
+    assert working.is_file()
+
+
+def test_too_few_labels_refuses_without_artifact(tmp_path, monkeypatch):
+    from datetime import date
+
+    import earnings_pipeline.pilot_calibration as module
+    from earnings_pipeline.pilot_labels import check_working, write_view
+
+    monkeypatch.setattr(module, "require_committed", lambda *args: None)
+    intake, loaded = cases.make_case(tmp_path)
+    write_view(intake, loaded, 0, date(2026, 10, 13))
+    check_working(intake, loaded, 0)
+    with pytest.raises(EvaluationError, match="too_few_labels"):
+        module.calibrate_pilot(intake, loaded)
+    assert not (intake.pinned.evaluation / "calibration-v1.json").exists()
+
+
+def test_calibration_requires_head_labels_before_any_label_read(tmp_path, monkeypatch):
+    import earnings_pipeline.pilot_calibration as module
+    from earnings_themes.records import RecordError
+
+    intake, loaded = cases.make_case(tmp_path)
+
+    def refuse(*args):
+        raise RecordError("labels", ("not_committed",))
+
+    monkeypatch.setattr(module, "require_committed", refuse)
+    monkeypatch.setattr(
+        module,
+        "read_label_bytes",
+        lambda *args: pytest.fail("label read preceded HEAD gate"),
+    )
+    with pytest.raises(RecordError, match="not_committed"):
+        module.calibrate_pilot(intake, loaded)
+
+
+@pytest.mark.parametrize(
+    "changed,missing", [(False, False), (True, False), (False, True)]
+)
+def test_original_label_history_allows_dev_append_but_refuses_train_edits_or_missing_hash(
+    tmp_path, monkeypatch, changed, missing
+):
+    from datetime import date
+    from types import SimpleNamespace
+
+    import earnings_pipeline.pilot_calibration as module
+    from earnings_pipeline.pilot_labels import write_view
+    from earnings_themes.evaluation import labels_toml, load_labels
+    from earnings_themes.records import RecordError
+    from earnings_themes.split import Partition
+
+    intake, loaded = cases.make_case(tmp_path)
+    _, working = write_view(intake, loaded, 0, date(2026, 10, 13))
+    labels = load_labels(working)
+    original = labels_toml(labels).encode()
+    current = labels.model_copy(
+        update={
+            "labels": (
+                *labels.labels,
+                labels.labels[0].model_copy(
+                    update={"partition": Partition.DEV, "target_id": "dev-target"}
+                ),
+            )
+        }
+    )
+    if changed:
+        train = current.labels[0].model_copy(update={"labelled_on": date(2026, 10, 14)})
+        current = current.model_copy(update={"labels": (train, *current.labels[1:])})
+    path = intake.pinned.evaluation / "labels/support-labels-v1.toml"
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(labels_toml(current))
+    artifact = cases.cases.bound_artifact(intake.config, loaded).model_copy(
+        update={
+            "preregistration_hash": labels.preregistration_hash,
+            "labels_hash": sha256_hex(original),
+        }
+    )
+    monkeypatch.setattr(module, "require_committed", lambda *args: None)
+
+    def git(args, **kwargs):
+        assert kwargs["capture_output"] and not kwargs["check"]
+        assert args[:2] in (["git", "rev-list"], ["git", "show"])
+        data = (
+            (b"a" * 40 + b"\n")
+            if args[1] == "rev-list"
+            else (b"missing" if missing else original)
+        )
+        return SimpleNamespace(returncode=0, stdout=data)
+
+    monkeypatch.setattr(module.subprocess, "run", git)
+    if changed or missing:
+        with pytest.raises(RecordError, match="labels_changed"):
+            module.validate_calibration_labels(intake, artifact)
+    else:
+        module.validate_calibration_labels(intake, artifact)
```

- [x] **Step 2: Confirm red**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_calibration.py --tb=short -q
```

Expected: the new module is missing; the new task tests fail before implementation. Record the actual output.

- [x] **Step 3: Add the exact implementation**

> Deviation: Implemented the omitted dictionary supplement, closed Git-launch labels_changed refusal, and corrected content_hash versus workflow configuration_hash documentation.

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/src/earnings_pipeline/pilot_calibration.py
@@ -0,0 +1,132 @@
+"""The train calibration boundary: sample, source and exact-label-byte bindings."""
+
+import re
+import subprocess
+from pathlib import Path
+
+from earnings_core import sha256_hex
+from earnings_themes import tomlfile
+from earnings_themes.coding import validate_proposal_support
+from earnings_themes.coding.decide import decision_inputs
+from earnings_themes.evaluation import (
+    CalibrationArtifact,
+    SupportLabelSet,
+    calibrate,
+    frozen_configuration,
+    joint_score,
+)
+from earnings_themes.records import RecordError, parse
+from earnings_themes.split import Partition
+
+from earnings_pipeline.pilot_inputs import PilotIntake, require_committed
+from earnings_pipeline.pilot_labels import _checked, checked_pass, sample
+from earnings_pipeline.pilot_records import json_bytes, read_calibration
+from earnings_pipeline.pilot_workflow import LoadedPass
+from earnings_pipeline.stage6 import write_once
+from earnings_pipeline.theme_config import confined_path
+
+
+def read_label_bytes(path: Path) -> tuple[SupportLabelSet, bytes]:
+    try:
+        data = path.read_bytes()
+    except OSError:
+        raise RecordError("labels", ("malformed_record",)) from None
+    return parse(tomlfile.loads(data, "labels"), SupportLabelSet, "labels"), data
+
+
+def calibrate_pilot(intake: PilotIntake, loaded: LoadedPass) -> Path:
+    if intake.partition is not Partition.TRAIN:
+        raise RecordError("partition", ("wrong_partition",))
+    checked_pass(intake, loaded)
+    path = intake.pinned.evaluation / "labels/support-labels-v1.toml"
+    require_committed(intake.config.repo, path, "labels")
+    labels, data = read_label_bytes(path)
+    own = SupportLabelSet(
+        preregistration_hash=labels.preregistration_hash,
+        train_extensions=labels.train_extensions,
+        labels=labels.of(Partition.TRAIN),
+    )
+    _checked(own, intake, loaded, sample(intake, loaded, labels.train_extensions))
+    validate_proposal_support(loaded.proposal, loaded.primary, loaded.sources)
+    validate_proposal_support(loaded.proposal, loaded.alternative, loaded.sources)
+    views = decision_inputs(loaded.primary, loaded.sources)
+    alternative = decision_inputs(loaded.alternative, loaded.sources)
+    events = {s.doc_id: s.event_id for s in intake.config.sources}
+    artifact = calibrate(
+        intake.preregistration,
+        labels,
+        labels_hash=sha256_hex(data),
+        views=views,
+        alternative={target: joint_score(view) for target, view in alternative.items()},
+        events={t.target_id: events[t.target.doc_id] for t in loaded.primary.targets},
+        configuration=frozen_configuration(
+            loaded.sources.stored_run.record,
+            loaded.proposal.record,
+            loaded.primary.record,
+            intake.config.support_policy,
+        ),
+    )
+    target = evaluation_path(intake, "calibration-v1.json")
+    write_once(target, json_bytes(artifact), intake.layout)
+    return target
+
+
+def checked_calibration(intake: PilotIntake) -> CalibrationArtifact:
+    path = evaluation_path(intake, "calibration-v1.json")
+    require_committed(intake.config.repo, path, "calibration")
+    artifact = read_calibration(path)
+    if artifact.preregistration_hash != intake.preregistration.content_hash:
+        raise RecordError("calibration", ("preregistration_mismatch",))
+    validate_calibration_labels(intake, artifact)
+    return artifact
+
+
+def validate_calibration_labels(
+    intake: PilotIntake, artifact: CalibrationArtifact
+) -> None:
+    path = intake.pinned.evaluation / "labels/support-labels-v1.toml"
+    require_committed(intake.config.repo, path, "labels")
+    current, data = read_label_bytes(path)
+    if current.preregistration_hash != artifact.preregistration_hash:
+        raise RecordError("labels", ("preregistration_mismatch",))
+    relative = path.relative_to(intake.config.repo).as_posix()
+    original = data if sha256_hex(data) == artifact.labels_hash else None
+    if original is None:
+        history = subprocess.run(
+            ["git", "rev-list", "HEAD", "--", relative],
+            cwd=intake.config.repo,
+            capture_output=True,
+            check=False,
+        )
+        if history.returncode == 0:
+            for revision in history.stdout.decode(
+                "ascii", errors="ignore"
+            ).splitlines():
+                if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
+                    raise RecordError("labels", ("labels_changed",))
+                result = subprocess.run(
+                    ["git", "show", revision + ":" + relative],
+                    cwd=intake.config.repo,
+                    capture_output=True,
+                    check=False,
+                )
+                if (
+                    result.returncode == 0
+                    and sha256_hex(result.stdout) == artifact.labels_hash
+                ):
+                    original = result.stdout
+                    break
+    if original is None:
+        raise RecordError("labels", ("labels_changed",))
+    old = parse(tomlfile.loads(original, "labels"), SupportLabelSet, "labels")
+    if (
+        old.preregistration_hash != current.preregistration_hash
+        or old.train_extensions != current.train_extensions
+        or old.of(Partition.TRAIN) != current.of(Partition.TRAIN)
+    ):
+        raise RecordError("labels", ("labels_changed",))
+
+
+def evaluation_path(intake: PilotIntake, name: str) -> Path:
+    root = intake.pinned.evaluation.relative_to(intake.config.repo).as_posix()
+    return confined_path(intake.config.repo, root + "/" + name, root)
```

- [x] **Step 4: Confirm green and formatting**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_calibration.py --tb=short -q
uv run --locked --offline --no-sync --all-packages ruff check apps/earnings-pipeline/tests/test_pilot_calibration.py apps/earnings-pipeline/src/earnings_pipeline/pilot_calibration.py
uv run --locked --offline --no-sync --all-packages ruff format --check apps/earnings-pipeline/tests/test_pilot_calibration.py apps/earnings-pipeline/src/earnings_pipeline/pilot_calibration.py
git diff --check
```

Expected: all named tests pass and Ruff is clean. Save the actual task evidence; then request the task review before committing its reviewed implementation and dictionary changes.

- [x] **Step 5: Review and commit this task**

Close the task review before committing.

```bash
git add apps/earnings-pipeline/src/earnings_pipeline/pilot_calibration.py apps/earnings-pipeline/tests/test_pilot_calibration.py
git commit -m "feat(pilot): calibrate exact committed label bytes"
```

### Task 11: Gather verified independent, baseline and stability figures

**Files:** create `apps/earnings-pipeline/src/earnings_pipeline/pilot_reporting.py` and `apps/earnings-pipeline/tests/test_pilot_reporting.py`. Add LoadedRun’s dictionary table and registry in this same task. Use only invented fixtures.

**Interfaces:**

Consumes Tasks 7–10's intake, pass/run checkpoints, label validation and calibration reader, plus the pure evaluation report/gate APIs. Produces:

```python
LoadedRun(record: RunRecord, passed: LoadedPass, primary: StoredSupportRun, coding: CodingRun, policy: AssignmentPolicy | None)
load_run(intake: PilotIntake, path: Path) -> LoadedRun
quote_retention(extraction: StoredRun, doc_id: str) -> tuple[int, int]
observations(intake: PilotIntake, run: LoadedRun) -> tuple[EventObservation, ...]
labelled_targets(intake: PilotIntake, run: LoadedRun, labels: SupportLabelSet) -> tuple[LabelledTarget, ...]
recount_all(intake: PilotIntake, run: LoadedRun) -> None
independent_figures(intake: PilotIntake, loaded: LoadedPass) -> tuple[IndependentFigures, ...]
checked_stability(runs: Sequence[LoadedRun], events: tuple[str, ...], configuration_hash: str, calibration_hash: str) -> tuple[str, ...]
write_report(train: PilotIntake, dev: PilotIntake, train_run: LoadedRun, dev_run: LoadedRun, fresh: Sequence[LoadedRun], *, version: int = 1) -> Path
write_gates(intake: PilotIntake, *, report_version: int = 1, version: int = 1) -> Path
coverage_gate(intake: PilotIntake) -> None
```

`LoadedRun` is a frozen dataclass. Its dictionary row and the complete public pilot-record registry land here. Retention counts quote-reference occurrences per event; stability figures are appended to dev's existing `PartitionReport.figures`. Gate verdicts remain an ordered list.

- [x] **Step 1: Add the failing tests**

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/tests/test_pilot_reporting.py
@@ -0,0 +1,182 @@
+"""Counts-only collectors, strict run intake, and complete fresh-run membership."""
+
+import importlib
+from types import SimpleNamespace
+
+import pytest
+from earnings_themes.records import RecordError
+
+cases = importlib.import_module("apps.earnings-pipeline.tests.test_pilot_labels")
+
+
+def test_retention_counts_quote_occurrences_and_retry_rejections():
+    from earnings_pipeline.pilot_reporting import quote_retention
+
+    source = SimpleNamespace(
+        claims=(
+            SimpleNamespace(doc_id="d", quote_ids=("q1", "q2")),
+            SimpleNamespace(doc_id="d", quote_ids=("q1",)),
+            SimpleNamespace(doc_id="other", quote_ids=("q3",)),
+        ),
+        rejections=(
+            SimpleNamespace(doc_id="d", candidate_index=0, labels=("q1", "q2")),
+            SimpleNamespace(doc_id="d", candidate_index=0, labels=("q1",)),
+            SimpleNamespace(doc_id="d", candidate_index=None, labels=("whole",)),
+        ),
+    )
+    assert quote_retention(source, "d") == (3, 6)
+
+
+def test_stability_refuses_partial_duplicate_or_changed_inventory_before_figures():
+    from earnings_pipeline.pilot_reporting import checked_stability
+    from earnings_themes.split import Partition
+
+    record = SimpleNamespace(
+        partition=Partition.DEV,
+        fresh="r1",
+        status="complete",
+        event_ids=("e1",),
+        configuration_hash="a" * 64,
+        calibration_hash="b" * 64,
+    )
+    loaded = SimpleNamespace(record=record)
+    with pytest.raises(RecordError, match="complete_fresh_runs"):
+        checked_stability((loaded, loaded, loaded), ("e1",), "a" * 64, "b" * 64)
+    records = [
+        SimpleNamespace(record=SimpleNamespace(**{**record.__dict__, "fresh": f"r{i}"}))
+        for i in range(3)
+    ]
+    assert checked_stability(records, ("e1",), "a" * 64, "b" * 64) == ("r0", "r1", "r2")
+    records[1].record.status = "partial"
+    with pytest.raises(RecordError, match="complete_fresh_runs"):
+        checked_stability(records, ("e1",), "a" * 64, "b" * 64)
+
+
+def test_loaded_run_checks_calibration_head_and_pass_binding_before_coding(
+    tmp_path, monkeypatch
+):
+    import earnings_pipeline.pilot_reporting as module
+    from earnings_pipeline.pilot_records import RunRecord, read_json
+    from earnings_pipeline.pilot_workflow import make_run
+
+    intake, loaded = cases.make_case(tmp_path)
+    artifact = cases.cases.bound_artifact(intake.config, loaded)
+    record = make_run(
+        intake.config,
+        loaded,
+        artifact,
+        directory=tmp_path / "data/runs/pilot/train/run",
+        now=lambda: cases.cases.cases.NOW,
+    )
+    path = tmp_path / "data/runs/pilot/train/run/run-record.json"
+
+    def refuse(*args):
+        raise RecordError("calibration", ("not_committed",))
+
+    monkeypatch.setattr(module, "require_committed", refuse)
+    monkeypatch.setattr(
+        module,
+        "read_calibration",
+        lambda *args: pytest.fail("artifact read preceded HEAD gate"),
+    )
+    with pytest.raises(RecordError, match="not_committed"):
+        module.load_run(intake, path)
+    assert read_json(path, RunRecord, "run") == record
+
+
+def test_coverage_and_recount_gates_precede_every_share_figure(tmp_path, monkeypatch):
+    import earnings_pipeline.pilot_reporting as module
+    from earnings_themes.split import Partition
+
+    current = SimpleNamespace(
+        preregistration=SimpleNamespace(content_hash="a" * 64),
+        partition=Partition.TRAIN,
+    )
+    dev = SimpleNamespace(
+        preregistration=current.preregistration,
+        partition=Partition.DEV,
+        config=SimpleNamespace(selected_event_ids=("e1",)),
+    )
+    base = SimpleNamespace(
+        record=SimpleNamespace(
+            fresh=None, calibration_hash="b" * 64, configuration_hash="c" * 64
+        )
+    )
+    monkeypatch.setattr(
+        module, "evaluation_path", lambda *args: tmp_path / "report.json"
+    )
+    monkeypatch.setattr(module, "checked_stability", lambda *args: ("r1", "r2", "r3"))
+    monkeypatch.setattr(
+        module,
+        "coverage_gate",
+        lambda *args: (_ for _ in ()).throw(
+            RecordError("coverage", ("binding_mismatch",))
+        ),
+    )
+    monkeypatch.setattr(
+        module,
+        "recount_all",
+        lambda *args: pytest.fail("recount preceded coverage gate"),
+    )
+    monkeypatch.setattr(
+        module,
+        "partition_report",
+        lambda *args, **kwargs: pytest.fail("figures preceded gates"),
+    )
+    with pytest.raises(RecordError, match="binding_mismatch"):
+        module.write_report(current, dev, base, base, ())
+    monkeypatch.setattr(module, "coverage_gate", lambda *args: None)
+    monkeypatch.setattr(
+        module,
+        "recount_all",
+        lambda *args: (_ for _ in ()).throw(RecordError("gold", ("counts_mismatch",))),
+    )
+    with pytest.raises(RecordError, match="counts_mismatch"):
+        module.write_report(current, dev, base, base, ())
+
+
+def test_complete_normal_run_collects_live_labels_and_replay_decisions(
+    tmp_path, monkeypatch
+):
+    from datetime import date
+
+    import earnings_pipeline.pilot_calibration as calibration
+    import earnings_pipeline.pilot_reporting as module
+    from earnings_core import sha256_hex
+    from earnings_pipeline.pilot_labels import check_working, write_view
+    from earnings_pipeline.pilot_records import json_bytes
+    from earnings_pipeline.pilot_workflow import make_run
+    from earnings_themes.records import sealed
+
+    intake, passed = cases.make_case(tmp_path)
+    write_view(intake, passed, 0, date(2026, 10, 13))
+    label_path = check_working(intake, passed, 0)
+    artifact = sealed(
+        cases.cases.bound_artifact(intake.config, passed).model_copy(
+            update={
+                "preregistration_hash": intake.preregistration.content_hash,
+                "labels_hash": sha256_hex(label_path.read_bytes()),
+            }
+        )
+    )
+    artifact_path = intake.pinned.evaluation / "calibration-v1.json"
+    artifact_path.write_bytes(json_bytes(artifact))
+    monkeypatch.setattr(module, "require_committed", lambda *args: None)
+    monkeypatch.setattr(calibration, "require_committed", lambda *args: None)
+    make_run(
+        intake.config,
+        passed,
+        artifact,
+        directory=tmp_path / "data/runs/pilot/train/run",
+        now=lambda: cases.cases.cases.NOW,
+    )
+    run = module.load_run(
+        intake, tmp_path / "data/runs/pilot/train/run/run-record.json"
+    )
+    from earnings_themes.evaluation import load_labels
+
+    targets = module.labelled_targets(intake, run, load_labels(label_path))
+    assert len(targets) == 1
+    assert set(targets[0].scores) == {"minicheck", "deberta"}
+    assert targets[0].accepted
+    assert run.record.status == "complete"
```

The same task adds its dictionary contract test:

```diff
--- a/tests/contracts/test_data_dictionary.py
+++ b/tests/contracts/test_data_dictionary.py
@@ -17,6 +17,7 @@

 import earnings_core as core
 import earnings_ingestion.canonical as ingestion
+import earnings_pipeline as pipeline
 import pytest
 from earnings_ingestion import browser, layout
 from earnings_ingestion.cohort import config as cohort_config
@@ -29,6 +30,7 @@
     model_runtime,
     pilot_inputs,
     pilot_records,
+    pilot_reporting,
     pilot_workflow,
     theme_config,
     theme_workflow,
@@ -734,9 +736,9 @@
 PILOT_DATACLASSES = {
     "PilotIntake": pilot_inputs.PilotIntake,
     "LoadedPass": pilot_workflow.LoadedPass,
+    "LoadedRun": pilot_reporting.LoadedRun,
 }
 PILOT_ENUMS = {}
-PILOT_MODULES = [pilot_records, pilot_inputs, pilot_workflow]


 @pytest.mark.parametrize(("name", "model"), PILOT_MODELS.items(), ids=PILOT_MODELS)
@@ -759,10 +761,13 @@
 def test_pilot_application_registry_is_complete():
     defined = {
         value
-        for module in PILOT_MODULES
-        for value in vars(module).values()
+        for info in pkgutil.iter_modules(pipeline.__path__)
+        if info.name.startswith("pilot_")
+        for value in vars(
+            importlib.import_module(f"{pipeline.__name__}.{info.name}")
+        ).values()
         if isinstance(value, type)
-        and value.__module__ == module.__name__
+        and value.__module__ == f"{pipeline.__name__}.{info.name}"
         and not value.__name__.startswith("_")
     }
     assert {v for v in defined if issubclass(v, BaseModel)} == set(
```

- [x] **Step 2: Confirm red**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_reporting.py --tb=short -q
uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_data_dictionary.py --tb=short -q
```

Expected: the new module is absent; capture the actual task failures.

- [x] **Step 3: Apply the exact implementation**

> Deviation: Owner selected accepted/assessed retention (ii), replacing the supplied accepted/all denominator; invented mixed outcomes changed (1, 5) to (1, 2). Stability mutation coverage also closed the review Minor.

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/src/earnings_pipeline/pilot_reporting.py
@@ -0,0 +1,494 @@
+"""Verified local observations produce counts-only feasibility reports and gates."""
+
+from collections.abc import Sequence
+from dataclasses import dataclass
+from pathlib import Path
+
+from earnings_ingestion.events.coverage import build_coverage, load_coverage
+from earnings_ingestion.events.states import ProcessingTransition
+from earnings_themes.annotation import load_gold_draft, recount
+from earnings_themes.coding import validate_proposal_support
+from earnings_themes.coding.decide import AssignmentPolicy, decision_inputs
+from earnings_themes.coding.records import CodingRun
+from earnings_themes.coding.store import read_coding_run, reverify_coding_run
+from earnings_themes.evaluation import (
+    IndependentFigures,
+    PilotReport,
+    SupportLabelSet,
+    claim_label,
+    derive_gates,
+    gates_toml,
+    joint_label,
+    joint_score,
+)
+from earnings_themes.evaluation.align import unit_index
+from earnings_themes.evaluation.report import (
+    Accepted,
+    EventObservation,
+    LabelledTarget,
+    compare_readings,
+    partition_report,
+    stability_figures,
+)
+from earnings_themes.extraction.store import StoredRun
+from earnings_themes.independent import verify_independent
+from earnings_themes.records import RecordError, sealed
+from earnings_themes.split import Partition
+from earnings_themes.support import read_support_run
+from earnings_themes.support.store import StoredSupportRun
+
+from earnings_pipeline.pilot_calibration import (
+    evaluation_path,
+    validate_calibration_labels,
+)
+from earnings_pipeline.pilot_inputs import PilotIntake, require_committed
+from earnings_pipeline.pilot_labels import (
+    _checked,
+    checked_pass,
+    committed_labels,
+    sample,
+)
+from earnings_pipeline.pilot_records import (
+    PassRecord,
+    RunRecord,
+    json_bytes,
+    read_calibration,
+    read_json,
+)
+from earnings_pipeline.pilot_workflow import (
+    LoadedPass,
+    bind_policy,
+    load_pass,
+    phase_path,
+    stored_directory,
+)
+from earnings_pipeline.stage6 import (
+    file_stem,
+    independent_path,
+    kept_drafts,
+    read_ledger,
+    write_once,
+)
+from earnings_pipeline.theme_config import WorkflowError, confined_path, read_selected
+from earnings_pipeline.theme_workflow import (
+    _baseline,
+    _checked_history,
+    load_workflow_inputs,
+    replay_runtime,
+    workflow_configuration_hashes,
+)
+
+
+@dataclass(frozen=True, repr=False)
+class LoadedRun:
+    record: RunRecord
+    passed: LoadedPass
+    primary: StoredSupportRun
+    coding: CodingRun
+    policy: AssignmentPolicy | None
+
+
+def load_run(intake: PilotIntake, path: Path) -> LoadedRun:
+    config = intake.config
+    path = confined_path(
+        config.repo, path.relative_to(config.repo).as_posix(), "data/runs/pilot"
+    )
+    record = read_json(path, RunRecord, "run")
+    if (
+        record.partition is not intake.partition
+        or record.event_ids != config.selected_event_ids
+    ):
+        raise WorkflowError("input_changed")
+    artifact_path = evaluation_path(intake, "calibration-v1.json")
+    require_committed(config.repo, artifact_path, "calibration")
+    artifact = read_calibration(artifact_path)
+    if artifact.preregistration_hash != intake.preregistration.content_hash:
+        raise WorkflowError("input_changed")
+    validate_calibration_labels(intake, artifact)
+    if (
+        record.calibration_hash != artifact.content_hash
+        or record.configuration_hash != artifact.configuration_hash
+    ):
+        raise WorkflowError("input_changed")
+    pass_path = confined_path(config.repo, record.pass_record.path, "data/runs/pilot")
+    read_selected(config, record.pass_record)
+    passed = load_pass(config, read_json(pass_path, PassRecord, "pass"))
+    checked_pass(intake, passed, fresh=record.fresh is not None)
+    if (
+        record.fresh != passed.record.stability_run_id
+        or record.status != passed.record.status
+    ):
+        raise WorkflowError("input_changed")
+    policy = bind_policy(config, passed, artifact, replay=record.fresh is None)
+    coding_dir = stored_directory(config, record.coding)
+    primary = (
+        passed.primary
+        if record.fresh is not None
+        else read_support_run(phase_path(config, coding_dir.parent / "support"))
+    )
+    if record.fresh is None and (
+        primary.record.configuration_hash
+        != workflow_configuration_hashes(config, passed.sources)[1]
+        or primary.record.cache_mode != "replay"
+        or primary.record.stability_run_id is not None
+    ):
+        raise WorkflowError("input_changed")
+    if (
+        primary.record.scorer_identity != config.scorer_identity
+        or tuple(t.target for t in primary.targets) != passed.proposal.targets
+    ):
+        raise WorkflowError("input_changed")
+    validate_proposal_support(passed.proposal, primary, passed.sources)
+    coding = read_coding_run(coding_dir)
+    expected_coding = workflow_configuration_hashes(
+        config, passed.sources, cache_mode="fresh" if record.fresh else "replay"
+    )[0]
+    if coding.record.configuration_hash != expected_coding:
+        raise WorkflowError("input_changed")
+    if coding.record.stability_run_id != record.fresh or coding.record.cache_mode != (
+        "fresh" if record.fresh else "replay"
+    ):
+        raise WorkflowError("input_changed")
+    reverify_coding_run(coding, passed.sources, primary, policy)
+    return LoadedRun(record, passed, primary, coding, policy)
+
+
+def quote_retention(extraction: StoredRun, doc_id: str) -> tuple[int, int]:
+    kept = sum(len(c.quote_ids) for c in extraction.claims if c.doc_id == doc_id)
+    rejected = sum(
+        len(r.labels)
+        for r in extraction.rejections
+        if r.doc_id == doc_id and r.candidate_index is not None
+    )
+    return kept, kept + rejected
+
+
+def observations(intake: PilotIntake, run: LoadedRun) -> tuple[EventObservation, ...]:
+    checked_pass(intake, run.passed, fresh=run.record.fresh is not None)
+    sources = run.passed.sources
+    extraction = sources.stored_run
+    bundles = {bundle.document.doc_id: bundle for bundle in sources.bundles}
+    gold = {record.event_id: record for record in intake.gold}
+    quotes = {(q.span.doc_id, q.quote_id): q.span for q in extraction.quotes}
+    inputs = load_workflow_inputs(intake.config, replay_runtime(intake.config))
+    if inputs.provenance_hash != sources.provenance_hash:
+        raise WorkflowError("input_changed")
+    history = _checked_history(
+        intake.config, confined_path(intake.config.repo, intake.config.states_dir)
+    )
+    baseline, _ = _baseline(
+        intake.config,
+        [r for r in history if not isinstance(r, ProcessingTransition)],
+        None,
+    )
+    out = []
+    for source in intake.config.sources:
+        doc_id = source.doc_id
+        bundle = bundles.get(doc_id)
+        if bundle is None or source.event_id not in gold:
+            raise RecordError("observations", (f"{source.event_id}: missing_document",))
+        accepted = tuple(
+            Accepted(
+                decision.theme_id,
+                tuple(
+                    (quotes[(doc_id, q)].start, quotes[(doc_id, q)].end)
+                    for q in decision.supporting_quote_ids
+                ),
+            )
+            for decision in run.coding.decisions
+            if decision.doc_id == doc_id and decision.status == "accepted"
+        )
+        state = baseline[source.event_id + ":release"]
+        if state.doc_id != doc_id or state.to_state.value != "parsed":
+            raise RecordError(
+                "observations", (f"{source.event_id}: missing_acquisition",)
+            )
+        kept = [
+            a
+            for a in state.attempts
+            if (a.accession, a.filename, a.artifact_sha256)
+            == (state.accession, state.exhibit, state.artifact_sha256)
+        ]
+        if len(kept) > 1:
+            raise RecordError(
+                "observations", (f"{source.event_id}: duplicate_attempt",)
+            )
+        confirmed = bool(kept and kept[0].outcome.value == "confirmed")
+        targets = [t for t in run.primary.targets if t.target.doc_id == doc_id]
+        out.append(
+            EventObservation(
+                source.event_id,
+                gold[source.event_id],
+                unit_index(bundle),
+                accepted,
+                confirmed,
+                quote_retention(extraction, doc_id),
+                (
+                    sum(
+                        d.status == "accepted"
+                        for d in run.coding.decisions
+                        if d.doc_id == doc_id
+                    ),
+                    len(targets),
+                ),
+            )
+        )
+    return tuple(out)
+
+
+def labelled_targets(
+    intake: PilotIntake, run: LoadedRun, labels: SupportLabelSet
+) -> tuple[LabelledTarget, ...]:
+    own = SupportLabelSet(
+        preregistration_hash=labels.preregistration_hash,
+        train_extensions=labels.train_extensions,
+        labels=labels.of(intake.partition),
+    )
+    _checked(
+        own, intake, run.passed, sample(intake, run.passed, labels.train_extensions)
+    )
+    primary = decision_inputs(run.primary, run.passed.sources)
+    alternative = decision_inputs(run.passed.alternative, run.passed.sources)
+    targets = {t.target_id: t for t in run.primary.targets}
+    events = {s.doc_id: s.event_id for s in intake.config.sources}
+    accepted = {d.target_id for d in run.coding.decisions if d.status == "accepted"}
+    return tuple(
+        LabelledTarget(
+            label.target_id,
+            events[targets[label.target_id].target.doc_id],
+            claim_label(label),
+            joint_label(label),
+            label.target_id in accepted,
+            {
+                "minicheck": joint_score(primary[label.target_id]),
+                "deberta": joint_score(alternative[label.target_id]),
+            },
+            primary[label.target_id].trials,
+        )
+        for label in own.labels
+    )
+
+
+def recount_all(intake: PilotIntake, run: LoadedRun) -> None:
+    bundles = {b.name: b for b in run.passed.sources.bundles}
+    for gold in intake.gold:
+        draft, working = kept_drafts(intake.layout, gold.event_id)
+        paths = [
+            confined_path(
+                intake.config.repo,
+                p.relative_to(intake.config.repo).as_posix(),
+                "data/runs/gold/drafts",
+            )
+            for p in (draft, working)
+        ]
+        path = intake.pinned.gold_dir / f"{file_stem(gold.event_id)}.toml"
+        require_committed(intake.config.repo, path, "gold")
+        found = recount(
+            path.read_bytes(),
+            load_gold_draft(paths[0]),
+            load_gold_draft(paths[1]),
+            bundle=bundles[gold.event_id],
+            pin=intake.pinned.pin,
+            split=intake.split,
+            codebook=intake.codebook,
+        )
+        if found:
+            raise RecordError(
+                "gold", tuple(f"{gold.event_id} {r.subject}: {r.reason}" for r in found)
+            )
+
+
+def independent_figures(
+    intake: PilotIntake, loaded: LoadedPass
+) -> tuple[IndependentFigures, ...]:
+    if intake.partition is not Partition.DEV:
+        raise RecordError("partition", ("wrong_partition",))
+    checked_pass(intake, loaded)
+    require_committed(
+        intake.config.repo, intake.pinned.evaluation / "independent-pass.toml", "ledger"
+    )
+    ledger = read_ledger(intake.pinned)
+    bundles = {b.name: b for b in loaded.sources.bundles}
+    signed = {g.event_id: g for g in intake.gold}
+    out = []
+    for event in intake.config.selected_event_ids:
+        draft, _ = kept_drafts(intake.layout, event)
+        draft = confined_path(
+            intake.config.repo,
+            draft.relative_to(intake.config.repo).as_posix(),
+            "data/runs/gold/drafts",
+        )
+        local = independent_path(intake.layout, event)
+        local = confined_path(
+            intake.config.repo,
+            local.relative_to(intake.config.repo).as_posix(),
+            "data/runs/gold/independent",
+        )
+        readings = verify_independent(
+            event,
+            ledger=ledger,
+            record=local.read_bytes() if local.is_file() else None,
+            drafted=load_gold_draft(draft),
+            bundle=bundles[event],
+            codebook=intake.codebook,
+        )
+        if isinstance(readings, list):
+            raise RecordError(
+                "independent",
+                tuple(f"{event} {r.subject}: {r.reason}" for r in readings),
+            )
+        index = unit_index(bundles[event])
+        out.append(
+            IndependentFigures(
+                event_id=event,
+                record_vs_draft=compare_readings(
+                    readings.record, readings.draft, index
+                ),
+                signed_vs_record=compare_readings(
+                    signed[event], readings.record, index
+                ),
+            )
+        )
+    return tuple(out)
+
+
+def checked_stability(
+    runs: Sequence[LoadedRun],
+    events: tuple[str, ...],
+    configuration_hash: str,
+    calibration_hash: str,
+) -> tuple[str, ...]:
+    ids = tuple(run.record.fresh for run in runs)
+    if (
+        len(runs) != 3
+        or any(
+            run.record.partition is not Partition.DEV
+            or run.record.status != "complete"
+            or run.record.fresh is None
+            or run.record.event_ids != events
+            or run.record.configuration_hash != configuration_hash
+            or run.record.calibration_hash != calibration_hash
+            for run in runs
+        )
+        or len(set(ids)) != 3
+    ):
+        raise RecordError("stability", ("complete_fresh_runs",))
+    return tuple(str(run_id) for run_id in ids)
+
+
+def write_report(
+    train: PilotIntake,
+    dev: PilotIntake,
+    train_run: LoadedRun,
+    dev_run: LoadedRun,
+    fresh: Sequence[LoadedRun],
+    *,
+    version: int = 1,
+) -> Path:
+    target = evaluation_path(train, f"report-v{version}.json")
+    if (
+        train.partition is not Partition.TRAIN
+        or dev.partition is not Partition.DEV
+        or train.preregistration != dev.preregistration
+    ):
+        raise RecordError("partition", ("wrong_partition",))
+    if (
+        train_run.record.fresh is not None
+        or dev_run.record.fresh is not None
+        or train_run.record.calibration_hash != dev_run.record.calibration_hash
+        or train_run.record.configuration_hash != dev_run.record.configuration_hash
+    ):
+        raise WorkflowError("input_changed")
+    ids = checked_stability(
+        fresh,
+        dev.config.selected_event_ids,
+        dev_run.record.configuration_hash,
+        dev_run.record.calibration_hash,
+    )
+    # GS5 is a gate for the whole report, before any shares or output are built.
+    coverage_gate(train)
+    recount_all(train, train_run)
+    recount_all(dev, dev_run)
+    labels = committed_labels(train)
+    if labels is None:
+        raise RecordError("labels", ("missing_labels",))
+    plan = train.preregistration.bootstrap
+    train_report = partition_report(
+        observations(train, train_run),
+        labelled_targets(train, train_run, labels),
+        train.codebook,
+        plan,
+        partition=Partition.TRAIN,
+    )
+    dev_report = partition_report(
+        observations(dev, dev_run),
+        labelled_targets(dev, dev_run, labels),
+        dev.codebook,
+        plan,
+        partition=Partition.DEV,
+    )
+    figures = stability_figures(
+        tuple(observations(dev, run) for run in fresh), dev.codebook, plan, run_ids=ids
+    )
+    dev_report = dev_report.model_copy(
+        update={"figures": (*dev_report.figures, *figures)}
+    )
+    report = sealed(
+        PilotReport(
+            report_version=version,
+            preregistration_hash=train.preregistration.content_hash,
+            calibration_hash=train_run.record.calibration_hash,
+            partitions=(train_report, dev_report),
+            independent=independent_figures(dev, dev_run.passed),
+            content_hash="0" * 64,
+        )
+    )
+    write_once(target, json_bytes(report), train.layout)
+    return target
+
+
+def write_gates(
+    intake: PilotIntake, *, report_version: int = 1, version: int = 1
+) -> Path:
+    if intake.partition is not Partition.DEV:
+        raise RecordError("partition", ("wrong_partition",))
+    path = evaluation_path(intake, f"report-v{report_version}.json")
+    require_committed(intake.config.repo, path, "report")
+    report = read_json(path, PilotReport, "report")
+    gates = derive_gates(
+        report,
+        rule=intake.preregistration.gates,
+        judge_floor=intake.preregistration.floor.floor,
+        preregistration_hash=intake.preregistration.content_hash,
+        version=version,
+    )
+    target = evaluation_path(intake, f"gates-v{version}.toml")
+    write_once(target, gates_toml(gates), intake.layout)
+    return target
+
+
+def coverage_gate(intake: PilotIntake) -> None:
+    from earnings_pipeline.pilot_cli import _no_theme
+    from earnings_pipeline.stage6 import EVENT_RUNS, transitions
+
+    states = confined_path(intake.config.repo, EVENT_RUNS.as_posix() + "/states")
+    _checked_history(intake.config, states)
+
+    first_path = intake.pinned.coverage_file(1)
+    second_path = intake.pinned.coverage_file(2)
+    require_committed(intake.config.repo, first_path, "coverage")
+    require_committed(intake.config.repo, second_path, "coverage")
+    first = load_coverage(first_path)
+    second = load_coverage(second_path)
+    if first.run_ids != second.run_ids:
+        raise RecordError("coverage", ("binding_mismatch",))
+    rebuilt = build_coverage(
+        intake.pinned.pilot,
+        intake.pinned.coverage_pin,
+        transitions(intake.layout),
+        run_ids=first.run_ids,
+        version=2,
+        no_theme=_no_theme(intake.layout, intake.pinned, first.run_ids),
+    )
+    if rebuilt != second:
+        raise RecordError("coverage", ("binding_mismatch",))
```

Apply the matching dictionary rows in this implementation step:

```diff
--- a/docs/data-dictionary.md
+++ b/docs/data-dictionary.md
@@ -7131,3 +7131,19 @@
 | `proposal` | ProposalRun | Reconstructed verified classifier proposals |
 | `primary` | StoredSupportRun | Reverified primary MiniCheck support results |
 | `alternative` | StoredSupportRun | Reverified alternative DeBERTa support results |
+
+### `LoadedRun`
+
+A transient `earnings_pipeline.pilot_reporting` dataclass. `load_run` verifies the
+sealed run checkpoint, committed calibration artifact, pass selection, frozen
+configuration, cache mode and stability identity, then reverifies coding against
+the consumed support run and bound policy. Reporting renders these checked inputs
+into the existing `PilotReport`; this dataclass adds no report fields or sidecar.
+
+| Field | Type | Meaning |
+| --- | --- | --- |
+| `record` | pilot_records.RunRecord | Verified local frozen-policy run checkpoint |
+| `passed` | LoadedPass | Verified extraction, proposals and both support runs |
+| `primary` | StoredSupportRun | Consumed primary support results, reloaded for an ordinary replay or retained for a fresh run |
+| `coding` | CodingRun | Reverified frozen-policy coding decisions and assignments |
+| `policy` | AssignmentPolicy or null | Verified bound policy, or null for the verified no-candidate calibration outcome |
```

- [x] **Step 4: Confirm green and review**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_reporting.py --tb=short -q
uv run --locked --offline --no-sync --all-packages ruff check apps/earnings-pipeline/src/earnings_pipeline/pilot_reporting.py apps/earnings-pipeline/tests/test_pilot_reporting.py
uv run --locked --offline --no-sync --all-packages ruff format --check apps/earnings-pipeline/src/earnings_pipeline/pilot_reporting.py apps/earnings-pipeline/tests/test_pilot_reporting.py
git diff --check
uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_data_dictionary.py --tb=short -q
```

Expected: every named test passes, Ruff is clean, and the diff has no whitespace errors. Record the actual output, request task review, and commit only after the review checkpoint closes.

- [x] **Step 5: Review and commit this task**

Close the task review before committing.

```bash
git add apps/earnings-pipeline/src/earnings_pipeline/pilot_reporting.py apps/earnings-pipeline/tests/test_pilot_reporting.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(pilot): collect verified pilot reports and gates"
```

### Task 12: Register all A8 commands and close every output boundary

**Files:** create `apps/earnings-pipeline/src/earnings_pipeline/pilot_commands.py` and `apps/earnings-pipeline/tests/test_pilot_commands.py`; modify `pilot_cli.py` and `stage6.py` for registration and closed metadata errors. Use only invented fixtures.

**Interfaces:**

Consumes Tasks 7–11's typed application APIs, `pilot`'s existing Typer group, and the existing opt-in `LiveRuntime` builder. Produces:

```python
safe[**P](command: Callable[P, None]) -> Callable[P, None]
part(value: str) -> Partition
identifier(value: str) -> str
intake(context: typer.Context, settings: Path, partition: str) -> PilotIntake
baseline(current: PilotIntake) -> LoadedPass
artifact(current: PilotIntake) -> CalibrationArtifact
live(current: PilotIntake, models_root: Path) -> LiveRuntime
support_checkpoint() -> None
utc_now() -> datetime
register(pilot: typer.Typer) -> None
```

Every command requires `--settings`. `pass` requires `--models-root`; `labels view` requires `--labelled-on YYYY-MM-DD`. Pass/run/labels/calibrate default to train, independent to dev; report gathers both partitions and gates reads dev. A fresh run requires dev, an ID and `--models-root`. Labels accept `--extensions` (default 0); report accepts repeated `--fresh` IDs and `--version` (default 1); gates accepts `--report-version` and `--version` (both default 1). Models are never built for ordinary replay. The support checkpoint is owner-approved D20-9 (P20-A).

- [x] **Step 1: Add the failing tests**

> Deviation: The reviewed fix expanded the runtime-construction guard across all eleven CLI help paths; the correction passed scoped checks and re-review.

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/tests/test_pilot_commands.py
@@ -0,0 +1,135 @@
+"""Every A8 command is counts-only and keeps model/runtime dispatch behind intake."""
+
+import importlib
+
+import pytest
+from earnings_pipeline.cli import app
+from typer.testing import CliRunner
+
+MARKER = "INVENTED_SOURCE_JUDGE_LABEL_EXCEPTION_SENTINEL"
+
+
+@pytest.mark.parametrize(
+    "command",
+    [
+        "pass",
+        "run",
+        "calibrate",
+        "independent",
+        "report",
+        "gates",
+        "labels sample",
+        "labels view",
+        "labels check",
+    ],
+)
+def test_each_command_redacts_unexpected_source_judge_label_exception(
+    command, tmp_path, monkeypatch
+):
+    module = importlib.import_module("earnings_pipeline.pilot_commands")
+
+    def refuse(*args, **kwargs):
+        raise ValueError(MARKER)
+
+    monkeypatch.setattr(module, "open_pilot", refuse)
+    args = [
+        "pilot",
+        "--repo",
+        str(tmp_path),
+        *command.split(),
+        "--settings",
+        "invented.json",
+    ]
+    if command == "pass":
+        args += ["--models-root", str(tmp_path)]
+    if command == "labels view":
+        args += ["--labelled-on", "2026-10-13"]
+    result = CliRunner().invoke(app, args)
+    assert result.exit_code == 1
+    assert MARKER not in result.output
+    assert "ValueError" in result.output
+
+
+@pytest.mark.parametrize(
+    "command",
+    [
+        "pass",
+        "run",
+        "calibrate",
+        "independent",
+        "labels sample",
+        "labels view",
+        "labels check",
+    ],
+)
+@pytest.mark.parametrize("partition", ["test", "excluded"])
+def test_forbidden_partition_refuses_before_metadata(
+    command, partition, tmp_path, monkeypatch
+):
+    module = importlib.import_module("earnings_pipeline.pilot_commands")
+    monkeypatch.setattr(
+        module, "open_pilot", lambda *args: pytest.fail("metadata opened")
+    )
+    args = [
+        "pilot",
+        "--repo",
+        str(tmp_path),
+        *command.split(),
+        "--settings",
+        "invented.json",
+        "--partition",
+        partition,
+    ]
+    if command == "pass":
+        args += ["--models-root", str(tmp_path)]
+    if command == "labels view":
+        args += ["--labelled-on", "2026-10-13"]
+    result = CliRunner().invoke(app, args)
+    assert result.exit_code == 1
+    assert "partition" in result.output
+    assert "metadata opened" not in result.output
+
+
+def test_negative_support_checkpoint_aborts_and_help_loads_no_runtime(
+    tmp_path, monkeypatch
+):
+    module = importlib.import_module("earnings_pipeline.pilot_commands")
+    from earnings_pipeline.theme_config import WorkflowError
+
+    monkeypatch.setattr(module.typer, "confirm", lambda *args, **kwargs: False)
+    with pytest.raises(WorkflowError):
+        module.support_checkpoint()
+    result = CliRunner().invoke(app, ["pilot", "--help"])
+    assert result.exit_code == 0
+    for word in (
+        "pass",
+        "run",
+        "calibrate",
+        "independent",
+        "report",
+        "gates",
+        "labels",
+    ):
+        assert word in result.output
+
+
+@pytest.mark.parametrize("command", ["split", "recount", "coverage"])
+def test_legacy_metadata_value_errors_never_print_source_text(
+    command, tmp_path, monkeypatch
+):
+    import earnings_pipeline.stage6 as module
+
+    def refuse(*args, **kwargs):
+        raise ValueError(MARKER)
+
+    monkeypatch.setattr(module, "load_manifest", refuse)
+    import earnings_pipeline.pilot_cli as legacy
+
+    monkeypatch.setattr(legacy, "pinned_codebook", lambda *args: object())
+    args = ["pilot", "--repo", str(tmp_path), command]
+    if command == "coverage":
+        args += ["--version", "2"]
+    result = CliRunner().invoke(app, args)
+    assert result.exit_code == 1
+    assert MARKER not in result.output
+    assert "pinned_metadata" in result.output
```

- [x] **Step 2: Confirm red**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_commands.py --tb=short -q
```

Expected: the new module is absent; capture the actual task failures.

- [x] **Step 3: Apply the exact implementation**

```diff
--- /dev/null
+++ b/apps/earnings-pipeline/src/earnings_pipeline/pilot_commands.py
@@ -0,0 +1,378 @@
+"""Thin A8 commands; every printed value is an ID, hash, count, or closed state."""
+
+from __future__ import annotations
+
+import functools
+from collections.abc import Callable
+from datetime import date, datetime, timezone
+from pathlib import Path
+from typing import TYPE_CHECKING, Annotated
+
+import typer
+from earnings_core import canonical_json
+from earnings_themes.coding.records import CodingError
+from earnings_themes.evaluation import EvaluationError, evaluate_gates, load_gates
+from earnings_themes.records import IdPart, RecordError
+from earnings_themes.split import Partition
+from earnings_themes.support.problems import SupportError
+
+from earnings_pipeline.pilot_calibration import calibrate_pilot, checked_calibration
+from earnings_pipeline.pilot_inputs import PilotIntake, open_pilot, require_committed
+from earnings_pipeline.pilot_labels import (
+    check_working,
+    checked_pass,
+    sample,
+    write_view,
+)
+from earnings_pipeline.pilot_records import PassRecord, read_calibration, read_json
+from earnings_pipeline.pilot_reporting import (
+    independent_figures,
+    load_run,
+    write_gates,
+    write_report,
+)
+from earnings_pipeline.pilot_workflow import (
+    LoadedPass,
+    bind_policy,
+    load_pass,
+    make_pass,
+    make_run,
+)
+from earnings_pipeline.stage6 import Layout, guarded
+from earnings_pipeline.theme_config import WorkflowError, confined_path, read_selected
+
+if TYPE_CHECKING:
+    from earnings_themes.evaluation import CalibrationArtifact
+
+    from earnings_pipeline.model_runtime import LiveRuntime
+
+commands = typer.Typer()
+labels = typer.Typer(
+    no_args_is_help=True, help="Sample, view and check support labels."
+)
+Settings = Annotated[
+    Path, typer.Option("--settings", help="The local workflow selection JSON.")
+]
+PartitionOption = Annotated[str, typer.Option("--partition", help="train or dev.")]
+
+
+def safe[**P](command: Callable[P, None]) -> Callable[P, None]:
+    @functools.wraps(command)
+    def run(*args: P.args, **kwargs: P.kwargs) -> None:
+        try:
+            command(*args, **kwargs)
+        except RecordError as error:
+            field = (
+                error.name
+                if error.name
+                in {
+                    "partition",
+                    "fresh",
+                    "labels",
+                    "labelled_on",
+                    "calibration",
+                    "stability",
+                    "visibility",
+                    "preregistration",
+                    "ledger",
+                    "report",
+                    "settings",
+                    "pass",
+                    "run",
+                    "gold",
+                    "coverage",
+                }
+                else "record.fields"
+            )
+            typer.echo(f"Refused: {field}: malformed_record", err=True)
+            raise typer.Exit(1) from None
+        except WorkflowError as error:
+            typer.echo(f"Refused: configuration: {error.reason}", err=True)
+            raise typer.Exit(1) from None
+        except EvaluationError as error:
+            typer.echo(f"Refused: evaluation: {error.problem.value}", err=True)
+            raise typer.Exit(1) from None
+        except (CodingError, SupportError):
+            typer.echo("Refused: assessment: malformed_record", err=True)
+            raise typer.Exit(1) from None
+
+    return guarded(run)
+
+
+def part(value: str) -> Partition:
+    if value not in {"train", "dev"}:
+        raise RecordError("partition", ("wrong_partition",))
+    return Partition(value)
+
+
+def identifier(value: str) -> str:
+    # Parse the existing IdPart without defining a new record for CLI arguments.
+    from pydantic import TypeAdapter, ValidationError
+
+    try:
+        return TypeAdapter(IdPart).validate_python(value, strict=True)
+    except ValidationError:
+        raise RecordError("fresh", ("malformed_record",)) from None
+
+
+def intake(context: typer.Context, settings: Path, partition: str) -> PilotIntake:
+    selected = part(partition)
+    layout: Layout = context.obj
+    path = confined_path(layout.repo, settings.as_posix())
+    return open_pilot(layout, path, selected)
+
+
+def baseline(current: PilotIntake) -> LoadedPass:
+    path = current.local / current.partition.value / "pass/pass.json"
+    record = read_json(
+        confined_path(
+            current.config.repo,
+            path.relative_to(current.config.repo).as_posix(),
+            "data/runs/pilot",
+        ),
+        PassRecord,
+        "pass",
+    )
+    loaded = load_pass(current.config, record)
+    checked_pass(current, loaded)
+    return loaded
+
+
+def artifact(current: PilotIntake) -> CalibrationArtifact:
+    return checked_calibration(current)
+
+
+def live(current: PilotIntake, models_root: Path) -> LiveRuntime:
+    from earnings_pipeline.model_runtime import build_runtime
+
+    selected = current.settings.runtime_manifest
+    path = confined_path(current.config.repo, selected.path)
+    require_committed(current.config.repo, path, "runtime_manifest")
+    read_selected(current.config, selected)
+    built = build_runtime(path, models_root)
+    if (
+        built.alternative_scorer.identity != current.settings.alternative_scorer
+        or built.extractor_family != current.config.extractor_family
+    ):
+        raise WorkflowError("model_mismatch")
+    return built
+
+
+def support_checkpoint() -> None:
+    typer.echo("checkpoint: extraction and classification complete")
+    if not typer.confirm(
+        "Unload Gemma, load both judges, and confirm support is ready", default=False
+    ):
+        raise WorkflowError("malformed_record")
+
+
+def utc_now() -> datetime:
+    return datetime.now(timezone.utc)
+
+
+@commands.command("pass")
+@safe
+def pass_command(
+    context: typer.Context,
+    settings: Settings,
+    models_root: Annotated[Path, typer.Option("--models-root")],
+    partition: PartitionOption = "train",
+) -> None:
+    current = intake(context, settings, partition)
+    runtime = live(current, models_root)
+    record = make_pass(
+        current.config,
+        runtime.workflow,
+        runtime.alternative_scorer,
+        partition=current.partition,
+        directory=current.local / current.partition.value / "pass",
+        fresh=None,
+        support_ready=support_checkpoint,
+        now=utc_now,
+    )
+    typer.echo(
+        f"partition {record.partition.value} status {record.status} events {len(record.event_ids)}"
+    )
+
+
+@commands.command("run")
+@safe
+def run_command(
+    context: typer.Context,
+    settings: Settings,
+    partition: PartitionOption = "train",
+    fresh: Annotated[str | None, typer.Option("--fresh")] = None,
+    models_root: Annotated[Path | None, typer.Option("--models-root")] = None,
+) -> None:
+    selected = part(partition)
+    fresh_id = None if fresh is None else identifier(fresh)
+    if fresh_id is not None and (selected is not Partition.DEV or models_root is None):
+        raise RecordError("fresh", ("wrong_partition",))
+    current = intake(context, settings, partition)
+    loaded = baseline(current)
+    calibration = artifact(current)
+    # FP12: changed settings or artifact refuse BEFORE a fresh dispatch.
+    bind_policy(current.config, loaded, calibration, replay=True)
+    if fresh_id is not None:
+        runtime = live(current, models_root)
+        record = make_pass(
+            current.config,
+            runtime.workflow,
+            runtime.alternative_scorer,
+            partition=current.partition,
+            directory=current.local / "fresh" / fresh_id / "pass",
+            fresh=fresh_id,
+            support_ready=support_checkpoint,
+            now=utc_now,
+        )
+        loaded = load_pass(current.config, record)
+        checked_pass(current, loaded, fresh=True)
+    directory = (
+        current.local / "fresh" / fresh_id / "run"
+        if fresh_id
+        else current.local / current.partition.value / "run"
+    )
+    result = make_run(
+        current.config, loaded, calibration, directory=directory, now=utc_now
+    )
+    typer.echo(
+        f"partition {result.partition.value} status {result.status} events {len(result.event_ids)} fresh {result.fresh or 'none'}"
+    )
+
+
+@labels.command("sample")
+@safe
+def sample_command(
+    context: typer.Context,
+    settings: Settings,
+    partition: PartitionOption = "train",
+    extensions: Annotated[int, typer.Option("--extensions")] = 0,
+) -> None:
+    current = intake(context, settings, partition)
+    drawn = sample(current, baseline(current), extensions)
+    typer.echo(f"partition {current.partition.value} targets {len(drawn)}")
+    for target in drawn:
+        typer.echo(target)
+
+
+@labels.command("view")
+@safe
+def view_command(
+    context: typer.Context,
+    settings: Settings,
+    labelled_on: Annotated[
+        str,
+        typer.Option(
+            "--labelled-on", help="Your deliberate completion date, YYYY-MM-DD."
+        ),
+    ],
+    partition: PartitionOption = "train",
+    extensions: Annotated[int, typer.Option("--extensions")] = 0,
+) -> None:
+    selected = part(partition)
+    try:
+        completed = date.fromisoformat(labelled_on)
+    except ValueError:
+        raise RecordError("labelled_on", ("malformed_record",)) from None
+    current = intake(context, settings, selected.value)
+    loaded = baseline(current)
+    write_view(current, loaded, extensions, completed)
+    typer.echo(
+        f"partition {current.partition.value} targets {len(sample(current, loaded, extensions))} local_views 1 working_labels 1"
+    )
+
+
+@labels.command("check")
+@safe
+def check_command(
+    context: typer.Context,
+    settings: Settings,
+    partition: PartitionOption = "train",
+    extensions: Annotated[int, typer.Option("--extensions")] = 0,
+) -> None:
+    current = intake(context, settings, partition)
+    loaded = baseline(current)
+    check_working(current, loaded, extensions)
+    typer.echo(
+        f"partition {current.partition.value} targets {len(sample(current, loaded, extensions))} labels checked"
+    )
+
+
+@commands.command("calibrate")
+@safe
+def calibrate_command(
+    context: typer.Context, settings: Settings, partition: PartitionOption = "train"
+) -> None:
+    if part(partition) is not Partition.TRAIN:
+        raise RecordError("partition", ("wrong_partition",))
+    current = intake(context, settings, partition)
+    path = calibrate_pilot(current, baseline(current))
+    result = read_calibration(path)
+    typer.echo(f"calibration {result.content_hash} outcome {result.outcome}")
+
+
+@commands.command("independent")
+@safe
+def independent_command(
+    context: typer.Context, settings: Settings, partition: PartitionOption = "dev"
+) -> None:
+    if part(partition) is not Partition.DEV:
+        raise RecordError("partition", ("wrong_partition",))
+    current = intake(context, settings, partition)
+    figures = independent_figures(current, baseline(current))
+    for figure in figures:
+        typer.echo(canonical_json(figure.model_dump(mode="json")))
+
+
+@commands.command("report")
+@safe
+def report_command(
+    context: typer.Context,
+    settings: Settings,
+    fresh: Annotated[list[str] | None, typer.Option("--fresh")] = None,
+    version: Annotated[int, typer.Option("--version")] = 1,
+) -> None:
+    ids = tuple(identifier(value) for value in (fresh or []))
+    train = intake(context, settings, "train")
+    dev = intake(context, settings, "dev")
+    first = load_run(train, train.local / "train/run/run-record.json")
+    second = load_run(dev, dev.local / "dev/run/run-record.json")
+    reruns = tuple(
+        load_run(dev, dev.local / "fresh" / run_id / "run/run-record.json")
+        for run_id in ids
+    )
+    target = write_report(train, dev, first, second, reruns, version=version)
+    from earnings_themes.evaluation import PilotReport
+
+    report = read_json(target, PilotReport, "report")
+    typer.echo(
+        f"report {report.content_hash} partitions {len(report.partitions)} independent {len(report.independent)}"
+    )
+
+
+@commands.command("gates")
+@safe
+def gates_command(
+    context: typer.Context,
+    settings: Settings,
+    report_version: Annotated[int, typer.Option("--report-version")] = 1,
+    version: Annotated[int, typer.Option("--version")] = 1,
+) -> None:
+    current = intake(context, settings, "dev")
+    target = write_gates(current, report_version=report_version, version=version)
+    from earnings_themes.evaluation import PilotReport
+
+    report = read_json(
+        current.pinned.evaluation / f"report-v{report_version}.json",
+        PilotReport,
+        "report",
+    )
+    gates = load_gates(target)
+    verdict = evaluate_gates(gates, report.partition(Partition.DEV))
+    typer.echo(canonical_json(verdict.model_dump(mode="json")))
+
+
+def register(pilot: typer.Typer) -> None:
+    for command in commands.registered_commands:
+        pilot.command(command.name)(command.callback)
+    pilot.add_typer(labels, name="labels")
--- a/apps/earnings-pipeline/src/earnings_pipeline/stage6.py
+++ b/apps/earnings-pipeline/src/earnings_pipeline/stage6.py
@@ -262,7 +262,7 @@
         events = load_event_manifest(manifest_path(path.parent, version))
         coverage_pin = pilot_pin(pilot, events, universe)
     except (OSError, ValueError) as error:
-        fail(f"Refused: {error}")
+        fail(f"Refused: pinned_metadata: {type(error).__name__}")
     if pilot.definition.content_hash != layout.pilot_hash:
         fail(
             f"Refused: {layout.shown(path)} holds pilot"
@@ -283,7 +283,7 @@
     try:
         return read_runs(layout.repo / EVENT_RUNS / "states")
     except (OSError, ValueError) as error:
-        fail(f"Refused: {error}")
+        fail(f"Refused: state_metadata: {type(error).__name__}")


 def documents(layout: Layout, pinned: Pinned) -> dict[str, str]:
--- a/apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py
+++ b/apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py
@@ -86,7 +86,7 @@
     try:
         manifest = derive_split(layout, pinned)
     except ValueError as error:
-        fail(f"Refused: {error}")
+        fail(f"Refused: pilot_record: {type(error).__name__}")
     created = write_once(pinned.split_path, record_json(manifest), layout)
     _said(pinned, layout)
     for partition in Partition:
@@ -179,7 +179,7 @@
     try:
         run_ids = load_coverage(first).run_ids if first.is_file() else None
     except ValueError as error:
-        fail(f"Refused: {error}")
+        fail(f"Refused: pilot_record: {type(error).__name__}")
     no_theme = _no_theme(layout, pinned, run_ids or ()) if version == 2 else []
     try:
         report = build_coverage(
@@ -191,7 +191,7 @@
             no_theme=no_theme,
         )
     except ValueError as error:
-        fail(f"Refused: {error}")
+        fail(f"Refused: pilot_record: {type(error).__name__}")
     path = pinned.coverage_file(version)
     created = write_once(path, serialize(report), layout)
     _said(pinned, layout)
@@ -290,3 +290,8 @@
             f"Refused: {problems} problem(s); GS5's shares wait until each is resolved"
         )
     typer.echo(f"recounted {len(records)} file(s): each rebuilds from its kept draft")
+
+
+from earnings_pipeline.pilot_commands import register as register_a8
+
+register_a8(pilot)
```

- [x] **Step 4: Confirm green and review**

```bash
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_commands.py --tb=short -q
uv run --locked --offline --no-sync --all-packages ruff check apps/earnings-pipeline/src/earnings_pipeline/pilot_commands.py apps/earnings-pipeline/tests/test_pilot_commands.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/src/earnings_pipeline/stage6.py
uv run --locked --offline --no-sync --all-packages ruff format --check apps/earnings-pipeline/src/earnings_pipeline/pilot_commands.py apps/earnings-pipeline/tests/test_pilot_commands.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/src/earnings_pipeline/stage6.py
git diff --check
```

Expected: every named test passes, Ruff is clean, and the diff has no whitespace errors. Record the actual output, request task review, and commit only after the review checkpoint closes.

- [x] **Step 5: Review and commit this task**

Close the task review before committing.

```bash
git add apps/earnings-pipeline/src/earnings_pipeline/pilot_commands.py apps/earnings-pipeline/tests/test_pilot_commands.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/src/earnings_pipeline/stage6.py
git commit -m "feat(pilot): register counts-only A8 commands"
```

### Task 13: Scoped verification, user gates and Plan A completion

**Files:**

- Modify after all gates: `specs/deferred_items.md`, this plan's completion markup, and the end of `specs/feasibility-pilot-and-threshold-calibration.md`'s Rollout.
- Retire only this plan to `specs/plans/completed/20-feasibility-pilot-and-threshold-calibration-plan-a-slice-4.md`.
- Prepare a concrete `CLAUDE.md` Current state diff; apply only if the user approves it.
- Do not edit `AGENTS.md`, the roadmap, the Stage 6 wording gate or the spec's status/other sections.

**Interfaces:** Consumes the reviewed implementation SHA, actual scoped test counts, and the user's main-checkout gate results. Produces the Plan A completion stamp, a retired plan, deferred-item dispositions and the execution-to-plan-B handoff. No pilot command runs as part of this task.

- [x] **Step 1: Run the scoped agent checks**

Run these separately, from the execution worktree. They are explicitly allowed invented/synthetic/static checks. Do not broaden `-k plan20`, combine it with `coverage`, or run the entire Stage 6 CLI file.

```bash
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/evaluation packages/earnings-themes/tests/coding/test_shared.py packages/earnings-themes/tests/test_tomlfile.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py --tb=short -q
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_pilot_seams.py apps/earnings-pipeline/tests/test_pilot_records.py apps/earnings-pipeline/tests/test_pilot_intake.py apps/earnings-pipeline/tests/test_pilot_workflow.py apps/earnings-pipeline/tests/test_pilot_labels.py apps/earnings-pipeline/tests/test_pilot_calibration.py apps/earnings-pipeline/tests/test_pilot_reporting.py apps/earnings-pipeline/tests/test_pilot_commands.py apps/earnings-pipeline/tests/test_theme_workflow.py --tb=short -q
uv run --locked --offline --no-sync --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -k plan20 --tb=short -q
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-ingestion/tests/test_events_coverage.py --tb=short -q
uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/test_gold.py::test_countable_binds_the_current_parsed_document_id packages/earnings-themes/tests/test_gold.py::test_working_quote_anchor_refusal_keeps_the_drafted_duplicate_refusal packages/earnings-themes/tests/test_gold.py::test_origins_come_from_comparing_the_working_copy_with_the_draft --tb=short -q
uv run --locked --offline --no-sync ruff check .
uv run --locked --offline --no-sync ruff format --check .
uv lock --check --offline
git diff --check
git diff --name-only main...HEAD -- evaluation config data CLAUDE.md AGENTS.md specs/evidence-linked-theme-extraction-roadmap.md tests/integration/test_stage6_wording.py
```

Expected: tests pass with their actual counts; Ruff and diff checks are clean; the locked workspace remains 153 packages; the final command has no output before any separately approved Current state edit. Do not run `uv lock` to make this pass. No type-checker command is configured at the baseline. Review any changed public interfaces and the dictionary contracts together.

- [x] **Step 2: Finish task reviews and the final whole-branch review**

> Deviation: All task and final reviews closed; dictionary settings-pin precision was corrected and re-reviewed. The independent Codex CLI second opinion was skipped under the controller-is-Codex recipe.

Use subagent-driven-development's two-stage task reviews, then requesting-code-review's final whole-branch review. Give reviewers the spec, this plan, the base and tip SHAs, and the same no-data/no-model/no-root-suite constraints. Resolve findings before proceeding. Run new relevant checks when fixes land and report actual counts. Do not treat planning's prototype review as the execution branch's final review.

- [x] **Step 3: Predict selection and hand the user literal SHA-pinned gate commands**

> Deviation: Owner gates exposed two legacy test expectations; reviewed test-only fixes aligned approved coding exports and the closed pinned_metadata refusal, then the owner reran the root gate at d56d57c.

```bash
git rev-parse HEAD
uv run --locked --offline --no-sync --all-packages pytest packages apps tests -m "not live and not browser" --collect-only -q | tail
```

The second command collects only. Record its selected count, skipped/deselected collection information if shown, and actual command output. It does not authorize agents to execute the root suite. Expected counts are observations at this SHA; no fixed total from the planning prototype is binding.

Use the following metadata-only script to generate the exact main-checkout handoff. It prints the actual reviewed SHA, never a placeholder or variable command name:

```bash
uv run --locked --offline --no-sync python - <<'PY'
import re
import subprocess

sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
if re.fullmatch(r"[0-9a-f]{40}", sha) is None:
    raise SystemExit("reviewed_sha: malformed_record")
print(f"Plan 20 implementation reviewed at {sha}")
print(f"git switch --detach {sha}")
print('uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" --tb=short -q')
print("uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py --tb=short -q -rs")
print("git switch main")
PY
```

Send the generated commands to the user and state they run in the **main checkout**, alongside the collection prediction and actual agent counts. The historical user run at `eccb77c` was 4719 passed / 2 skipped / 28 deselected. Wait for the user's root-suite and wording-gate results. Agents never execute either gate, the pilot integration file, live/browser or user-only modes. If a gate fails, use systematic-debugging from the reported test name and reason only; do not ask for or inspect pilot text. After a code fix, hand over its new SHA and await the relevant gates again.

- [x] **Step 4: Resolve leftovers and request the protected Current state edit**

> Deviation: Owner approved the exact Current state diff on 2026-10-13; its single old-heading guard passed. Resolve-before-defer closed all findings with nothing newly deferred.

Run writing-plans' resolve-before-defer gate. Batch owner questions about any skipped steps or unresolved review findings. Answers that unblock implementation must be acted on, followed by the relevant reviews/checks/gates, before completion markup. Defer only items with the skill's required paths, reason, size and closure condition. Existing P18-1/P18-2, P19-2/P19-3/P19-4 and the unrelated P17 bundles remain open.

Show this exact proposed Current state change as a diff before writing it:

```diff
-## Current state: Stages 1–10 complete
+## Current state: Stages 1–10 complete; Stage 11 plan A complete
+
+Stage 11's plan A machinery is complete (plans 17–20): fresh caches and runtime
+assembly; pure evaluation, labels and calibration; and counts-only pilot commands.
+The implementation opened no pilot text and loaded no model. Plan B still owns the
+model choices, preregistration, pilot runs, committed figures and V6 record;
+Stage 11 remains unticked. B1 and B2 may start after plan A merges; B3 waits for all
+28 signed train/dev bundles and the 8 dev ledger rows. See
+`specs/feasibility-pilot-and-threshold-calibration.md` and plan 20's retired handoff.
```

The owner's permission rule and the spec's Rollout require approval for this edit. If approved, apply the following exact replacement after confirming the old heading still occurs once; if declined, record that disposition and leave the file unchanged. Do not write first and ask afterward.

```bash
uv run --locked --offline --no-sync python - <<'PY'
from pathlib import Path

path = Path("CLAUDE.md")
old = "## Current state: Stages 1–10 complete\n"
new = """## Current state: Stages 1–10 complete; Stage 11 plan A complete

Stage 11's plan A machinery is complete (plans 17–20): fresh caches and runtime
assembly; pure evaluation, labels and calibration; and counts-only pilot commands.
The implementation opened no pilot text and loaded no model. Plan B still owns the
model choices, preregistration, pilot runs, committed figures and V6 record;
Stage 11 remains unticked. B1 and B2 may start after plan A merges; B3 waits for all
28 signed train/dev bundles and the 8 dev ledger rows. See
`specs/feasibility-pilot-and-threshold-calibration.md` and plan 20's retired handoff.
"""
text = path.read_text()
if text.count(old) != 1:
    raise SystemExit("CLAUDE.Current state: input_changed")
path.write_text(text.replace(old, new, 1))
PY
```

The text describes execution's actual verification. If execution violated its scope, correct that claim before proposing the diff; planning's separate prototype audit does not turn into an implementation claim.

- [x] **Step 5: Mark up completion, tick the closed backlog items and stamp only Plan A**

After the partition of done/deferred work and all owner questions are final, tick this plan's completed steps and add one-line `> Deviation:` or `> Skipped:` notes at the steps that changed. Add the completion status using the actual date and whether the resolved gate deferred anything. Use one of the two exact forms below. Do not pre-tick steps during implementation; maintain the execution ledger until this point.

The completion status is one of:

```text
**Status: COMPLETE (YYYY-MM-DD)** — executed via subagent-driven-development; nothing deferred
**Status: COMPLETE (YYYY-MM-DD)** — executed via subagent-driven-development; deferred items in specs/deferred_items.md
```

Use this metadata-only script after the done/deferred partition is final. The literal `no` argument means the gate deferred nothing. If it deferred items, use `uv run --locked --offline --no-sync python - yes` with the same script body. This records the resolved partition and creates no new approval gate.

```bash
uv run --locked --offline --no-sync python - no <<'PY_STATUS'
from datetime import date
from pathlib import Path
import sys

path = Path("specs/plans/20-feasibility-pilot-and-threshold-calibration-plan-a-slice-4.md")
text = path.read_text()
if text.startswith("**Status: COMPLETE ("):
    raise SystemExit("plan.status: already_complete")
answer = sys.argv[1]
if answer not in ("yes", "no"):
    raise SystemExit("plan.status: invalid_disposition")
disposition = (
    "deferred items in specs/deferred_items.md" if answer == "yes" else "nothing deferred"
)
status = (
    f"**Status: COMPLETE ({date.today().isoformat()})** — executed via "
    f"subagent-driven-development; {disposition}"
)
path.write_text(status + "\n\n" + text)
PY_STATUS
```

The earlier-item ticking pass runs even if nothing new was deferred. The following exact edit adds the pointer at each item's heading and preserves the item history. Run it only once closure evidence for P17-1, P17-2, P17-5 and P19-1 is satisfied by implementation, conscious dispositions and the user's gates:

```bash
uv run --locked --offline --no-sync python - <<'PY'
from pathlib import Path
import re

path = Path("specs/deferred_items.md")
text = path.read_text()
for item in ("P17-1", "P17-2", "P17-5", "P19-1"):
    pattern = rf"(?ms)^- \[ \] (\*\*{re.escape(item)} — .*?\*\*)"
    text, count = re.subn(pattern, r"- [x] \1 → done in plan 20", text)
    if count != 1:
        raise SystemExit(f"{item}: input_changed")
path.write_text(text)
PY
```

Append a `20-feasibility-pilot-and-threshold-calibration-plan-a-slice-4` deferred section only if the resolve-before-defer gate actually deferred something. Use the full self-contained deferred-item schema; never append an empty section or delete old items.

Append the following line at the end of the shared spec's Rollout, with the execution completion date. This does not amend a settled requirement or retire the spec:

```bash
uv run --locked --offline --no-sync python - <<'PY'
from datetime import date
from pathlib import Path
import re

path = Path("specs/feasibility-pilot-and-threshold-calibration.md")
text = path.read_text()
if re.search(r"(?m)^> Plan A: COMPLETE \(", text):
    raise SystemExit("Rollout.Plan A: already_complete")
if text.count("## Rollout\n") != 1:
    raise SystemExit("Rollout: input_changed")
stamp = (
    f"> Plan A: COMPLETE ({date.today().isoformat()}) — implemented by plan 20 "
    "(specs/plans/completed/20-feasibility-pilot-and-threshold-calibration-plan-a-slice-4.md). "
    "Next: B1 and B2; plan B's B3 waits for the visibility gate."
)
path.write_text(text.rstrip() + "\n\n" + stamp + "\n")
PY
```

Run `git diff --check` and review the status/backlog/stamp diff. Only if the user separately approved and the concrete Current state change was applied, run `git add CLAUDE.md`; otherwise leave it unstaged. Then:

```bash
git log -3 --oneline
git add specs/plans/20-feasibility-pilot-and-threshold-calibration-plan-a-slice-4.md specs/deferred_items.md specs/feasibility-pilot-and-threshold-calibration.md
git diff --cached --check
git commit -m "docs(specs): complete Stage 11 plan A"
```

No roadmap box or Stage 11 stamp is written.

- [ ] **Step 6: Report backlog health and retire only this plan**

Run the loaded writing-plans backlog script from the repository root:

```bash
uv run --offline --no-project --python 3.13 python /Users/lowell/.agents/skills/writing-plans/scripts/deferred_stats.py
```

 Report open count, closure rate and aged tail. If its threshold is met (20+ open items or any aged tail), run the referenced rubric's four read-only triage steps and present a grouped, sorted proposal. Triage does not block retirement; changing dispositions belongs to the owner.

```bash
git log -3 --oneline
git mv specs/plans/20-feasibility-pilot-and-threshold-calibration-plan-a-slice-4.md specs/plans/completed/20-feasibility-pilot-and-threshold-calibration-plan-a-slice-4.md
git add specs/plans/completed/20-feasibility-pilot-and-threshold-calibration-plan-a-slice-4.md
git commit -m "chore(specs): retire plan 20"
```

Do not move `specs/feasibility-pilot-and-threshold-calibration.md`; plan B still implements it. No new relative links here change depth; recheck any added during execution. Run finishing-a-development-branch only after this completion chain, with the user's gate evidence included.

- [ ] **Step 7: Hand over what plan B consumes, without planning or running it**

The next writing-plans session starts after plan A merges. It reads the spec and this retired plan. B1 owns model choices and downloads, licenses, the memory check, native smoke, and numeric ceilings. No prototype model identity or invented test ceiling is a baseline choice. B2 owns the numeric preregistration and commits it alone before B3. The operator support checkpoint is mandatory for pass/fresh. B3's visibility remains all 28 signed/committed train/dev files and 8 dev ledger rows.

D20-1's B2 procedure uses a local, metadata-only `data/runs/pilot/preregistration-fields.toml` whose values the user chooses in plan B. The following literal script is the handoff mechanism, not an A8 command or a task to run here:

```bash
uv run --locked --all-packages python - <<'PY'
from pathlib import Path
from earnings_themes import tomlfile
from earnings_themes.evaluation import freeze_preregistration, preregistration_toml

fields = tomlfile.read(Path("data/runs/pilot/preregistration-fields.toml"))
record = freeze_preregistration(fields)
target = Path("evaluation/djia-2024q3-2026q2/pilot-v1/preregistration-v1.toml")
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("x", encoding="utf-8") as stream:
    stream.write(preregistration_toml(record))
print(record.content_hash)
PY
```

The future plan B procedure supplies and reviews those fields, runs this script in the user's terminal and commits the result before B3. This plan selects no floor, cutoff grid, model, ceiling, seed or resample count for the actual pilot.

B8's already-approved `docs/verification/pilot-v1-feasibility.md` must cite the exact SHA-256 of the committed `independent-pass.toml` used for the comparisons, alongside the per-event figures in the existing report. FP16 requires no extra sidecar or PilotReport field. A metadata-only user script can obtain that byte hash with `sha256_hex(Path("evaluation/djia-2024q3-2026q2/pilot-v1/independent-pass.toml").read_bytes())` after the committed-byte gate. The report's stability figures are in dev, and gate results are kept as a list. Tie-evidence matching and the P19-4 bootstrap population stay open for their stated triggers; no configuration comparison happens before V6.

---

## Handoffs to later stages

This plan ships machinery only. The spec's Handoffs table governs what Stages 12, 14, 15 and 16 receive after plan B. The as-built application APIs, strict readers, shared hash helpers, local checkpoint paths, fresh IDs and failure semantics above are plan B's inputs. Stage 11 remains open, so no later roadmap entry is rewritten here. Execution traps and deviations are recorded in the Plan B consuming handoff below. No real pilot figures were produced.

## Planning verification — 2026-10-13

Historical planning evidence follows; it describes the prototype before execution and is distinct from the execution verification below.

This is a verified implementation plan, not an executed implementation. Main remains clean at `5015862`. The only change on `plan-20-stage11-a8` is this plan. The owner approved it and its plan-only commit on 2026-10-13; no prototype code is included. Prototype code was kept uncommitted in isolated scratch worktrees. Tasks 1–12 were replayed in order from clean main, with the test changes before the implementation changes. The final document contains the corrected patches, including the EOF-context correction found at Task 12. Repository Ruff check and format check were clean after each task.

| Task | Observed red | Observed scoped green |
| --- | --- | --- |
| 1 | Missing shared API / dictionary type during collection | 373 passed |
| 2 | 11 boundary failures; dictionary has 1 missing-table failure | 381 passed |
| 3 | 12 failures across exports, gold binding and dictionary | 383 passed |
| 4 | 9 failures across report diagnostics and dictionary | 379 passed |
| 5 | 11 failures, 11 passes and 59 deselected; existing direct coverage regression already passes | 22 passed / 59 deselected, then 11 coverage tests passed separately |
| 6 | 4 seam failures; dictionary collection lacks WorkflowInputs | 377 passed |
| 7 | 7 missing-module failures | 386 passed, 1 skipped |
| 8 | 14 missing-module failures | 394 passed, 1 skipped |
| 9 | 4 missing-module failures | 4 passed |
| 10 | 6 missing-module failures | 6 passed |
| 11 | 5 missing-module failures | 386 passed, 1 skipped |
| 12 | 27 failures; the 3 legacy cases separately show the planted exception marker leaking | 27 passed |

The final replay passed these exact independent scoped groups: library/evaluation/import/dictionary **712 passed, 1 skipped**; application seams, A8 commands and existing invented workflow consumers **106 passed**; Stage 6 `-k plan20` **22 passed, 59 deselected**; synthetic coverage **11 passed**; selected gold cases **3 passed**. The dictionary skip is its empty enum registry's pytest parameterization, not an unverified model contract. Repository Ruff was clean with **491 files already formatted**, `git diff --check` was clean, and `uv lock --check --offline` resolved the unchanged **153 packages**. A sandbox cache-permission failure on the lock check was resolved by using the isolated writable uv cache; no dependency changed.

All 24 patches re-extracted from the final Markdown applied in order to a second clean checkout of `5015862`. That final patch replay, the tested red/green replay and the reviewed prototype have the same changed-file set, and all **53 code, test and dictionary files are byte-identical**. Source review closed its findings; a supplementary read-only complete-plan review found no remaining substantive gap. Root's own self-review checked A8/Labels/Calibration/Metrics/Artifacts/Failure handling/Wording guard/Deferred items/Rollout coverage, H1–H16 and inherited constraints, all 13 task interfaces, all 67 unchecked steps, complete code blocks, placeholder phrases and type names. Six inline Python command bodies parse cleanly. Completion replacement guards were checked read-only against the approved public metadata; this found and fixed the indented Rollout template's false-positive stamp guard.

Root **collection only** produced `4862/4890 tests collected (28 deselected)` on this prototype. Execution must rerun the collection command at its actual reviewed SHA and report actual selected/pass/skip counts. This number is an observation, not an expected-total assertion.

**Verification limits and scope audit:** No model/tokenizer/scorer/NLI runtime was loaded, no network call was made, no actual pilot text or existing gold/pilot run data was opened, and no root suite, wording gate, pilot integration gate, live/browser or user-only mode was executed. The user-gated completion/stamping/retirement operations and protected Current state edit were not performed; only their syntax and public-input guards were checked. Two earlier planning selections exceeded the invented-only verification scope: an initial broad baseline included legacy tests using committed Stage 1 source fixtures, and an overbroad combined `-k` expression later selected five legacy coverage cases. Those runs are excluded from readiness evidence, were disclosed to the owner, and were replaced by the separate allowed commands above. The scoped final replay does not verify native runtime behavior, B1's memory fit, server unloading, any real pilot result, or the user's gates. The owner approved the operator checkpoint and parsed-list preflight on 2026-10-13 as D20-9/D20-10 (P20-A/P20-B).

## Execution Handoff

Historical planning-to-execution handoff follows; execution has now completed as recorded below.

The owner approved the plan and its plan-only commit on 2026-10-13. D20-9/D20-10 record the review decisions, and their task references are updated. Self-review was repeated for these metadata changes; the verified code blocks are unchanged. Do not implement this plan in the planning session.

After approval and the plan-only commit on `plan-20-stage11-a8`, open a **fresh GPT-6.1 Medium session**, load **subagent-driven-development**, and create a **fresh worktree** using using-git-worktrees from the commit containing the approved plan. Execute the saved plan and the spec in task order, with a fresh worker per task and both review stages. No execution-choice question remains: the owner selected this process. Drop the planning conversation; this document contains the interfaces, exact code, tests, constraints and completion protocol needed by the new session.


## Execution verification — 2026-10-13

Reviewed implementation SHA: `d56d57c13a20e6ebfa1b9e20d1b1c70945f123ce` (base `7cb56b678822ad6b14716bde826ff31b815ea96d`). Tasks 1–12 completed in order with task reviews and recorded RED/GREEN evidence; all final review findings closed. The resolve-before-defer gate found no skipped implementation or new deferred item. Existing deferred bundles remain open except P17-1, P17-2, P17-5 and P19-1, whose implementation/disposition closure is recorded above. The owner separately approved the exact protected Current state diff.

Agent scoped verification at `e64d95501494dfa570faed4ef1ec412a47a21122`: evaluation/library/import/dictionary **714 passed, 1 skipped**; application seams, commands and workflow **138 passed**; Stage 6 `-k plan20` **22 passed, 59 deselected**; synthetic coverage **11 passed**; selected gold tests **3 passed** (total **888 passed, 1 skipped**). Subsequent dictionary review correction: **383 passed, 1 skipped**. Final legacy-test fix: named RED **2 failed**, named GREEN **2 passed**, contracts/commands **63 passed**, Stage 6 plan20 **22 passed, 59 deselected**. Repository Ruff check/format check and diff checks were clean; **491 files** were formatted and the locked workspace remained **153 packages**. No type checker is configured. An independent Codex CLI second opinion was skipped under the controller-is-Codex recipe; this is not additional review evidence.

Collection only at the reviewed SHA selected **4896/4924 tests, 28 deselected**. The owner executed the main-checkout root gate at that SHA: **4893 passed, 3 skipped, 28 deselected, 1 warning** in **919.87 seconds** (Torch/Python 3.14 warning). The owner's wording gate at `b26010394cedc81ee987a312bd995f8620c16026` gave **7 passed**; the subsequent commit changed only two unrelated legacy tests, so that wording result remains applicable. Agents did not execute either user gate.

Execution opened no pilot text or existing gold/pilot run data, loaded no model/tokenizer/scorer/NLI runtime, and made no network call. Verification uses invented/synthetic/static inputs and does not establish native smoke, resident memory fit, external-server unloading, real pilot quality or feasibility. Retention (ii), safe failures, reload identity checks, label-base refusals and dictionary supplements intentionally diverge from the supplied patches as annotated; embedded patch bodies retain their approved planning text. Task 13's retirement and final handoff checkboxes remain pending for the controller until those actions occur.

## Plan B consuming handoff

Plan B starts after plan A merges and consumes the focused `earnings_pipeline.pilot_*` modules, `pilot_commands.py`, shared coding/support configuration helpers, checked committed-byte readers and evaluation APIs shipped by plans 17–20; the spec's Plan B, Preregistration, Metrics, Artifacts and Rollout sections remain authoritative. This is a consuming handoff, not a plan or authorization to run B.

- **B1:** Choose models, downloads, licenses and numeric ceilings; verify native smoke and resident memory. Synthetic model identities and ceilings are not baseline choices. Runtime assembly cannot stop an external Gemma server. Pass/fresh require the counts-only operator acknowledgment after classification and before support; B1 must account for resident Python scorers/tokenizers and both judges/MiniCheck.
- **B2:** The user chooses metadata-only local preregistration fields and uses Task 13 step 7's literal `freeze_preregistration`/`preregistration_toml` mechanism, then commits preregistration alone before B3. No actual floor, grid, model, ceiling, seed or resample count was chosen here.
- **B3 and replay/fresh consumers:** Enforce all **28 signed/committed train/dev bundles and 8 dev ledger rows** before source loading. Test/excluded partitions refuse before text. Resealed reduced splits and wrong configured coding/stability IDs refuse; no missing committed label base or Git failure can silently start an extension. Ordinary replay reuses extraction only and refuses cache misses; fresh IDs and caches remain separate, and partial runs never count toward k = 3. Retention (ii) uses assessed targets only; retention (i) uses quote-reference occurrences and retries, with GS5 count reconciliation.
- **B8 and later-stage outputs:** `docs/verification/pilot-v1-feasibility.md` must cite the exact SHA-256 of the committed `independent-pass.toml` used in comparisons, alongside existing per-event figures. No new sidecar or PilotReport field is needed. Stability lives in dev figures; gate results stay a list. No configuration comparison precedes V6. The spec's Handoffs table governs later stages after B completes; Stage 11 remains unticked and the shared spec remains live.
- **Existing backlog:** `specs/deferred_items.md` P18-1/P18-2, P19-2/P19-3/P19-4 and unrelated P17 bundles remain open for their stated closure conditions/triggers. Tie-group maximum matching and the label-bootstrap population remain pilot/Plan B questions. P15-M1's broad workflow decomposition remains open after the typed seam extraction. No new item was deferred by this execution.
