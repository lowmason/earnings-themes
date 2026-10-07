# Coverage-Aware Aggregation and Cited Export, Stage 10 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Carry saved, permitted earnings-release fixtures through the shipped extraction, support, and deductive-coding libraries into typed analytical rows, explicit coverage denominators, immutable evidence views, and a cited report, without treating unfinished assessments as negative observations.

**Architecture:** `earnings-themes.analysis` owns analytical contracts, current-input verification, completion evidence, rows, prevalence, and immutable analytical storage. The application converts ingestion records to those contracts and composes acquisition replay, canonicalization, extraction, coding proposals, support assessment, explicit assignment decisions, evidence views, reporting, and new processing-state runs. Ingestion owns the backwards-compatible state-table extension and the single browser adapter. Themes imports neither ingestion nor the application. Core schema 2 and canonical coordinates remain unchanged.

**Tech Stack:** The existing Python >=3.14 uv workspace, Pydantic, Polars/Parquet, pytest and Ruff; standard-library HTML escaping, URL encoding, hashing and atomic publication. Optional capture uses the shipped public `BrowserRenderer`, pinned Chrome for Testing 154.0.8037.57 on mac-arm64, and the existing `browser-capture` extra. No new dependency, framework, type checker, model download, hosted inference, runtime worker pool, or database is required.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 10 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

**Status:** Planned on 2026-10-06. This document authorizes no execution in the planning session. Stage 10 remains unticked. Its authoritative completion stamp belongs in the shared system specification's **Rollout**, after execution and observed gates. Keep that specification live.

## Reconciliation and inspected baseline

The first command in the planning session was Git status. It showed clean `main...origin/main`; HEAD was `7d9b2cb7d989a769ae1429afe8d3f3b1d180dea4`. The user supplied Stage 9's merge through [PR #13](https://github.com/lowmason/earnings-themes/pull/13) and deletion of its local/remote branches. No branch, worktree, extraction, runtime change, stage tick, specification retirement, staging, or commit occurred while writing this plan.

`derive-roadmap` resumed through reconciliation. The complete roadmap was read, including its reconciliation notes, all stages, Stage 10's full entry and stamp procedure. The authoritative stamps agree with stages 1–9 being complete:

| Stage | Authoritative stamp / implementation |
| --- | --- |
| 1 | `specs/release-parser-fidelity.md`, Rollout; plan 1 |
| 2 | `specs/evidence-linked-theme-extraction.md`, Rollout; plan 3 |
| 3 | `specs/completed/structure-aware-canonicalization.md`, Rollout; plans 4/5 |
| 4 | `specs/point-in-time-djia-cohort.md`, Rollout; plan 6; still live for Stage 15 |
| 5 | `specs/completed/event-discovery-eligibility-and-acquisition.md`, Rollout; plans 7/8 |
| 6 | `specs/completed/pilot-codebook-split-and-gold-set-protocol.md`, Rollout; plan 9 |
| 7 | `specs/completed/evidence-selection-and-verification.md`, Rollout; plans 11/12 |
| 8 | `specs/completed/semantic-support-assessment.md`, completion record; plan 13 |
| 9 | `specs/evidence-linked-theme-extraction.md`, Rollout; plan 14 |

Stage 10 is the next unticked stage and routes directly to `writing-plans`; no new whole-system brainstorming or separate Stage 10 specification is needed. Active and completed plan filenames were checked: the highest ID is completed plan 14, so the next ID is **15**. Preserve every later stage's order, routing, exit, and ownership.

Read before drafting: root AGENTS.md (no nearer instruction file was found in the owning source/spec/docs trees); README; workspace and all four member pyprojects; configured pytest/Ruff checks and CI presence (no repository CI workflow or configured type checker was found); `docs/earnings-ingestion.md`; `docs/earnings-themes.md`; the shared system and browser specifications; completed Stage 7/8 specifications and their verification records; completed plan 14 and `docs/verification/deductive-coding.md`; upstream core/structure/event/pilot handoffs cited by the roadmap; applicable deferred items; and relevant source/contracts/test code in core, ingestion, extraction, support, coding, and the application. Protected contents were not opened. No test was run in this planning session.

The user supplied the following upstream baseline, which is **not Stage 10 verification**: scoped blind controller checks 1110 passed without warnings; sequential extraction/support checks 700 passed, 2 live deselected, one existing optional Torch/Python 3.14 warning; Ruff passed with 385 already formatted files; user full suite 3532 passed, 1 skipped, 27 deselected; user Stage 6 fixture and pilot wording nodes 1 passed each.

Important shipped behavior:

- Extraction schema 1 / `pointer-traversal/1` stores document/window/visit/quote/claim/rejection tables. `read_run` currently parses tables but lacks several record and cross-table invariants. `write_run` checks exact spans. Both need the prerequisite in Task 1 before downstream stored consumption.
- `read_support_run` checks typed storage and raw-reference/hash bindings; `reverify_support_run(stored, sources)` re-resolves current sources, masks, themes, contexts and exact evidence. `assessed` is a processing outcome, not acceptance.
- `read_coding_run` checks its nine published files; `reverify_coding_run(stored, sources, support, policy)` re-decides and reprojects against the current complete inputs and the explicitly supplied policy. Missing policy produces `review/calibration_required`; fixture acceptance remains `kind="fixture"`.
- Quote IDs such as `q-0-100` and claim IDs such as `c-0-100-1-0` are document-scoped. Use composite keys; never join on either ID alone. Keep every original claim–quote link, including links not selected as assignment evidence.
- Stage 5 schema-1 `StateTransition` allows `parsed -> partial/completed/completed-no-theme`, but **not** `parsed -> failed`; its `failed` means `parse_failed` with a canonicalization `FailureReason`. Task 4 adds a separate schema-2 processing transition without relabeling an extraction failure as a parse failure or rewriting acquisition bytes.
- Frozen v0 selects a fitting subtheme instead of its parent. Parent/family prevalence is an analytical view, not new assignment rows or a codebook edit.
- Public `BrowserRenderer.capture(saved_html, capture_policy, *, source_document_id)` renders saved bytes; it does **not** navigate a text-fragment link. V5 must distinguish capture, actual link behavior, and fallback behavior.

## Global Constraints

This entire section must be copied unchanged into every implementer, fix, task-reviewer, final-reviewer and second-opinion brief. The controller obeys it too. Workers are not alone in the codebase: preserve others' work, edit only their assigned task files, and accommodate earlier approved changes. Execution is sequential; no implementation/review agents or runtime workers run concurrently.

1. **Stage 10 only.** Implement the theme vertical slice, first offline extraction command, processing-state mapping, coverage-aware analysis and cited export described here. Do not implement Stage 11 calibration, quality gates, production model/panel selection, signal pooling/view choices, agreement floors, or fresh-call stability. Stage 11 is the first extraction over pilot documents. Stage 12 owns a new inductive/hybrid codebook; Stage 13 owns transcripts and speaker-schema changes; Stage 14 owns configuration comparison and final test-gold drafting; Stage 15 owns full-cohort execution and worker/cache/store/allowance safety; Stage 16 owns optional hosted inference.
2. **Blinding in every session and agent.** Never open, search, print, or execute a reader of pilot document text, signed gold, drafts, working copies, views, or anything under the real repository's `data/`. Do not dereference codebook examples. Never draft gold or turn pipeline outputs into gold. Use invented fixtures, permitted Stage 1 fixtures, and `tests/fixtures/events/acquisition.json` with its synthetic saved inputs. Temporary miniature repositories created by tests may have their own invented `data/` directories; they must not resolve into the real protected tree. Read and audit test source before choosing nodes. Neither the controller nor any agent runs full-root tests or any Stage 6 wording node. These are user-only gates, even the fixture wording node.
3. Preserve this row verbatim, binding through Stage 14's final test-gold drafting:

| GS13 | *(design)* **Blinding**, after F9. A drafting session starts fresh. It sees only its brief, the contracts and validator, the frozen codebook when it drafts gold, and the text it is given: the 20 training bundles for the codebook, or one bundle for gold. It never sees Stages 7–9's code, prompts, or outputs, or another bundle's gold. No session reads a dev or test bundle before v0 is approved, and none reads a test bundle before Stage 14 freezes its configuration (GS18). The session that implements this spec never prints or opens pilot document text. |

4. **Authority and exactness.** A retained quote is a contiguous span of one immutable canonical document, with strict integer, zero-based Python code-point offsets in `[start,end)`. Reverify identity, canonical hash, attribution, text and current masks through code before aggregation and again before publication/export. Construct displayed quote text by slicing that saved canonical text. Do not stitch, fix wording, normalize chunks, use first-match search, or verify through HTML re-parsing, browser text, screenshots or OCR. All original claim–quote links survive, with document-qualified identity.
5. **Current consuming gates.** Harden extraction records first. Then use matching `SupportSources`, current bundles/masks/codebook and the explicitly supplied assignment policy with `read_support_run`/`reverify_support_run` and `read_coding_run`/`reverify_coding_run`. Validate even sources with zero assignments or zero targets. Neither a stored `assessed` row nor a cache hit grants acceptance. Missing policy retains `review/calibration_required`. Fixture-policy acceptance is visibly fixture-scoped in every manifest, table/report and command result; reject fixture policy on a non-fixture corpus.
6. **Processing and observability.** Preserve refused, flagged, incomplete, review, rejected, accepted, and valid-unmatched outcomes separately. Zero accepted targets or zero retained quotes never establishes `completed-no-theme`. An unavailable source, restricted source, failed parse/extraction, partial assessment or absent transcript never becomes a negative theme observation. Use expected issuer-period events and explicit missing reasons, not the successful quote table, for denominators.
7. **Time and analytical units.** Retain issuer/entity and zero-padded CIK, fiscal labels/period end, filing/publication/event/retrieval/extraction times, and dated eligibility/membership references independently. Preserve unknown fiscal labels. Compare one explicitly bound codebook version and mask/analysis policy at a time. Count disclosure copies once, keep each issuer's contribution at most one in a period, and print numerator, denominator, unit, time window and restrictions. Release speaker role is `not_applicable`, never inferred management speech.
8. **Masks, hierarchy and families.** Retain masked evidence for audit; exclude every overlapping masked quote from headline prevalence. Freeze existing assignments and v0: fitting children remain children. Parent roll-up is parent **or any descendant** presence, distinct by analysis unit. Family mappings are explicit, versioned, possibly overlapping analysis-time mappings; they do not create themes or modify assignments/codebooks. Separate family and parent rows from direct-theme rows.
9. **Rights and security.** Carry `RightsStatus`, `rights_basis`, access and explicit retention/export permissions. Free access does not establish redistribution rights. Retain/export text, text-bearing URLs, canonical views and source artifacts only as permitted. Captured screenshots remain `local_only`; they never enter public export or Git. Canonical views work offline without Selenium, capture or network. Escape untrusted text and attributes, use no source JavaScript, remote resource, live fetch, browser extension/profile, or embedded code. Use the single public ingestion renderer through the application and its bounded isolated policy; no second Selenium implementation.
10. **Reproducibility and diagnostic safety.** Preserve frozen universe/event/pilot/acquisition artifacts and prior state runs byte-for-byte. New runs/artifacts are atomic and immutable; never overwrite a prior run. Bind schemas, policy versions, prompts, identities, software/lock hashes, input/table/artifact hashes and explicit ceilings. A raw-cache reference/hash does not verify external bytes without that cache; record `not_supplied` or `not_bound` honestly. Print only validated IDs, counts and closed reasons; never source wording, rejection detail, rationale, raw reply, exception chain, arbitrary map key, dataframe, model or path from an untrusted error. Hash untrusted diagnostic identifiers rather than echo them.
11. **Offline scope and routing.** No SEC request, credentials, hosted/billable inference, real model call, model download, concurrent runtime worker, full-root pytest or protected wording node is authorized for agents. Default checks use audited invented/permitted fixtures and fail-closed replay transports. Approved Codex route substitution: GPT-6.1 Sol Medium (`gpt-6.1-sol`, `medium`) wherever Sonnet is required; GPT-6.1 Sol Ultra (`gpt-6.1-sol`, `ultra`) wherever Opus is required. Fresh task implementer, then spec-conformance approval, then code-quality approval, before the next task. Final whole-branch review and second opinion are sequential and both use Sol Ultra. No agent inherits the planning session's history.
12. **Scope and completion discipline.** Preserve AGENTS.md, source notes, shared specification, codebook/split/gold and unrelated deferred work. No root/package reorganization or unrelated dependency upgrade. Run meaningful failing tests before pipeline/library implementation and passing scoped checks afterwards. Surface deviations with their exact interface/compatibility consequence; do not silently weaken a gate. Completion requires observed V8/V10, honest V5 availability/behavior/fallback evidence, reviews and user-only gates. Stamp only Stage 10 in the shared specification, reconcile later handoffs without changing their order/routing/ownership, and retire only this plan. Integrate the future branch deliberately; clean up only owned, no-longer-needed worktrees.

## Decisions fixed by this plan

### Approved preflight amendment C1 (2026-10-06)

The user approved both explicit raw-snapshot seams before implementation. Task 2 adds `RawSnapshot`, a frozen `repr=False` dataclass with `doc_id: str`, `artifact: ArtifactRef`, and `data: bytes`, and `AnalysisInputs.raw_snapshots: tuple[RawSnapshot, ...]`. The tuple is document-qualified, has no loader or implicit I/O, and refuses duplicate/stale document bindings. Task 9 loads only explicitly selected confined source files and supplies their bytes. Task 3 rechecks source identity, actual byte hashes and current permissions; raw payloads never enter analytical manifests/tables.

Task 7 also changes the explicit public signature to `make_evidence_view(bound: BoundAnalysis, doc_id: str, quote_id: str, *, audience: Literal["local", "export"], raw_snapshot: RawSnapshot | None) -> EvidenceView`. Its required keyword argument must match the selected document's snapshot in the currently rebound `AnalysisInputs`; mismatched or omitted available snapshots refuse as `input_changed`. `None` represents an explicitly absent/withheld snapshot, never an implicit lookup. Missing retainable raw bytes retain the planned `raw_snapshot_missing` publication gate. Task 8 rechecks every actual byte/hash/rights binding before including a permitted snapshot. Tasks 2/3/7/8/9, their tests, dictionary and later briefs carry both seams together. No core, canonical coordinate, acquisition schema, rights rule or protected artifact authorization changes.

### Approved execution amendment C2 (2026-10-06)

The user approved the minimal explicit binding amendment after Task 3 identified missing verification material, before runtime edits or tests. Task 3 may extend Task 2 analytical records/exports/fixtures/dictionary to implement these required fields. No upstream/core schema or ingestion dependency is added. Application validation owns faithful derivation from original event/pilot/state artifacts; themes verifies the explicitly supplied current projections, canonical bytes, and existing upstream-bound provenance. Independent reconstruction of original ingestion manifests in themes is not claimed.

### Explicit input contract

Add four explicit fields to `AnalysisInputs`:

```python
analysis_policy: AnalysisPolicy
canonical_snapshots: tuple[CanonicalSnapshot, ...]
fixture_authorization: FixtureAuthorization | None
selected_universe_hash: str
```

New frozen `repr=False` dataclasses, defined in analysis records:

```python
CanonicalSnapshot(doc_id: str, data: bytes)
FixtureAuthorization(
    corpus_id: Literal["djia-synthetic", "stage10-invented"],
    event_manifest_hash: str,
    pilot_hash: str,
    provenance_hash: str,
)
```

`CanonicalSnapshot.data` is the existing full canonical JSON artifact, not a new external manifest format. It contains exactly `document`, `elements`, `manifest`, `masks`. The application validates it with the existing ingestion reader. Themes independently decodes this explicit in-memory JSON, reconstructs its core document/elements/masks contracts, checks equality with the current bundle, and checks manifest source/version/raw hash, policy/version/count, and element counts. No ingestion runtime import, callback, implicit loader, or HTML reparsing is needed. Duplicate/missing/extra selected snapshots refuse. Empty masks still have a manifest and explicit policy binding.

The fixture authorization is an explicit approval inventory entry, never inferred from a book/document name. Only an application-supplied allowlisted inventory, or an explicitly constructed invented test inventory, may supply it. Bind its event/pilot/provenance hashes to all current expected/acquisition records. Fixture scope requires this entry; research scope refuses it and fixture assignment policies. A filesystem root is unnecessary inside the pure gate: Task 9 confines selected paths before reading bytes. The pure gate binds the explicit authorization inventory; the application additionally confines selected paths. No filename or root assertion alone authorizes fixture acceptance.

### Normative analytical hash meanings

Existing canonical serialization has no self-hash and there is no separate mask manifest. The user approved the following exact analytical meanings, using existing `earnings_core.digest` and `sha256_hex`:

- `canonical_manifest_hash = digest(decoded_canonical_json["manifest"])`.
- `mask_manifest_hash = digest({"doc_id": doc_id, "canonical_hash": canonical_hash, "mask_policy_id": manifest["mask_policy_id"], "mask_policy_version": manifest["mask_policy_version"], "masks": decoded_canonical_json["masks"]})`. This is an analytical digest of published fields, not a new on-disk mask manifest.
- `AnalysisPolicy.population_hash = the selected pilot's published content hash`; `event_ids` must equal the declared selected expected population and each expected row must carry that pilot hash. Empty selection retains explicit handling; it does not silently choose a population.
- Define `provenance_hash = digest({"selected_universe_hash": selected_universe_hash, "expected": sorted ExpectedEvent JSON rows by event_id, "acquisition": sorted AcquisitionStatus JSON rows by document_id, "metadata": sorted DocumentMetadata JSON rows by doc_id, "canonical_artifacts": sorted [{"doc_id": snapshot.doc_id, "sha256": sha256_hex(snapshot.data)}] by doc_id})`. This normative formula makes every supplied current projection and artifact inventory independently comparable to the already upstream-bound provenance hash, including empty targets/assignments. Assignment/analysis policy hashes are excluded to avoid declaration cycles and preserve null-policy review; codebook/policy gates bind these separately. `no_theme` declarations compare their source/coding/support/book/analysis/assignment hashes directly with current checked values; they do not enter source provenance.
- Analysis policy hash remains its shipped `content_hash` property. Canonical text hash remains SHA-256 of UTF-8 bytes. Raw snapshots retain existing C1 byte/artifact/rights checks independently.

These formulas are a deliberate compatibility amendment: existing invented sources use arbitrary provenance/HASH values and must be regenerated through these formulas before creating support/coding runs. Existing upstream schema/version and reader signatures do not change. No retrospective claim is made that older arbitrary provenance labels were material-verified. Task 3 can fail closed on older AnalysisInputs lacking this explicit material.

Tasks 5/6/8 reject a caller analysis policy differing from `inputs.analysis_policy`. Task 9 loads only selected confined canonical files through the public ingestion reader, constructs projections and these hashes before replay, and supplies the matching approved fixture authorization inventory. Canonical snapshot payloads remain input-only and are never silently placed in analytical/export manifests. Tasks 7/8 rebind at publication; C1 raw snapshot semantics remain unchanged. Later briefs, dictionary and contracts carry this additive compatibility decision.

### Approved selected-universe extension to C2 (2026-10-06)

The user approved this extension after Task 6 identified the missing selected-universe binding. AnalysisInputs.selected_universe_hash is required: an exact built-in string of 64 lowercase hexadecimal SHA-256 characters. It means the selected universe's public earnings_ingestion.cohort.identity.operative_hash, the cutoff-admissible eligibility facts whose hash must equal the selected event and pilot universe_operative_hash. Keep this distinct from the codebook's discovery universe and source/artifact byte checksums.

analysis_provenance_hash adds required keyword-only selected_universe_hash: str and includes this value as a top-level member in the normative payload above. Strict input reconstruction, inventory recomputation and repeated binding checks retain it. Its digest must match current input, upstream source/coding/support lineage and fixture authorization, including empty work. AnalysisRunRecord.universe_hash comes solely from the checked selected value. Task 9 validates original selected universe/event/pilot/state artifacts through confined public readers before supplying the operative hash; pure themes does not import ingestion or verify absent universe bytes.

This required-field/helper/hash change fails closed for older inputs and intentionally invalidates older C2 provenance. Regenerate invented upstream runs, related cache identities, declarations, fixture authorizations and analytical bindings before verification; never relabel old runs. No core or upstream schema/reader changes, original-artifact rewrite, discovery-hash fallback, or hash inference is authorized. Tasks 8/9 test current publication and original derivation respectively.

### Task 7 fallback status clarification (2026-10-07)

The required canonical fallback may remain `status="available"` with `reason="raw_snapshot_missing"` when retainable raw bytes were not supplied. This narrow evidence-reference invariant requires nonnull valid canonical/view artifacts and a null raw artifact, retaining existing rights and byte checks. Only the documented available outcomes and the explicit raw-withholding outcome below are permitted. This marks the incomplete source-snapshot requirement without withholding a permitted canonical fallback; Task 8 must refuse complete cited publication when current permissions require that missing snapshot. No field, dtype, grain or schema version changes, and no existing analytical publication is migrated.

### Approved Task 7 capture permission amendment (2026-10-07)

The user approved adding exactly one required in-memory `EvidenceView.retain_capture: bool` field, restricted to a built-in bool and derived from the currently rebound selected `DocumentMetadata.retain_capture` plus permitted view retention/access. Withheld views carry False. No capture permission is inferred from text retention, rights labels or HTML. The public `capture_evidence_view(view, renderer, policy)` signature and persisted evidence/table schemas stay unchanged. Existing four-argument constructors must supply the explicit permission; later Tasks 8/9 preserve it. No published analytical artifact migration is required.

Available views denied capture return `not_requested` with `rights_restricted`, with accurate UTF-16 endpoints derived from the verified canonical snapshot, without accessing renderer environment or capture. Fully withheld views refuse with `AnalysisError("rights_restricted")` because they contain no canonical text from which honest browser coordinates can be derived. The actual `source_document_id` is decoded from existing full canonical JSON through the public ingestion decoder, never inferred from doc IDs or HTML. Screenshots and capture artifacts remain local_only.

### Task 7 review disposition: nested rights and raw withholding (2026-10-07)

The existing rights requirement also governs artifact references nested inside the complete canonical JSON. For export, fail closed with `withheld/rights_restricted` and no text-bearing bytes/references when that immutable payload contains a forbidden nested artifact reference, even if outer document metadata permits export. Do not relabel nested rights, rewrite immutable inputs, or invent an unapproved derivative. Permitted local canonical views remain available.

The existing required `snapshot_withheld` outcome is represented as `status="available", reason="snapshot_withheld"` when canonical text/view remains permitted but raw inclusion is denied by the selected audience's explicit permissions. This precise invariant requires a null raw artifact and valid nonnull canonical/view artifacts; existing `rights_basis` carries the rights context. It adds no field/schema/dtype/grain or arbitrary reason. `raw_snapshot_missing` remains distinct and takes precedence when required retainable raw bytes are actually absent; Task 8 must enforce that completeness gate from current permissions and supplied source inventory. Available reasons are exactly null, `raw_snapshot_missing`, or `snapshot_withheld`; withheld remains `rights_restricted` with no private artifacts/bytes. This controller disposition implements the original required rights outcome and supersedes the earlier narrower available-reason clarification.

### Task 5 projection clarification (2026-10-06)

Preserve document-level extraction refusals with `RejectionAudit.window_id: NonBlank | None`; its declared Polars String dtype and row grain remain unchanged. Null means the original refusal had no extraction window. Upstream claims/refusals expose a window and integer attempt ordinal, rather than an attempt ID. Analytical `attempt_id` is a derived pointer `a-{window_id}-{attempt}` when both original fields exist, scoped by source run and document; absent original attempts remain null. This pointer is not an upstream artifact ID. No upstream schema changes or published analytical artifacts require migration.

### Inputs and policy scope

The first command is `earnings-pipeline extract run --config <explicit-json>`. It supports **replay only** in Stage 10. There is no implicit current/latest discovery, paid provider, model launcher, tokenizer download or callback import by dotted path. The application supplies identity-only replay façades and the existing caches to the shipped functions; their dispatch/tokenizer methods raise fixed `replay_dispatch_forbidden` if reached. Shipped replay paths read cached input counts before dispatch, so no heuristic tokenizer is needed.

Programmatic `run_theme_workflow(config, runtime, *, now)` keeps an explicit injected protocol seam for future local production adapters and `AssignmentPolicy`; the Stage 10 CLI constructs only replay façades. A registered `fixture-supporting/1` deterministic policy is available solely with `scope="fixture"` and an allowlisted invented/synthetic corpus. It accepts only currently eligible, semantically supporting quote IDs offered by Stage 9, including masked evidence retained for audit; headline counting excludes masks afterwards. It contains no numeric score threshold, panel vote pooling or signal-view selection. `policy=null` keeps review. A calibrated-policy reference without its actual explicitly bound policy implementation is refused as `policy_unavailable`; Stage 11 supplies that implementation.

The fixture-policy corpus allowlist is exactly `djia-synthetic` and `stage10-invented`, additionally bound to the supplied permitted/invented manifest hashes and explicit `FixtureAuthorization` inventory. The application confines all selected paths, including temporary fixture roots; the pure themes gate validates the inventory without filesystem lookup. A name alone cannot authorize acceptance. `WorkflowConfig.fixture_started_at` is an optional UTC fixture clock, permitted only in fixture scope; stage run IDs, that fixed clock, policies, source provenance and software/lock identity are shared by the test cache seeder and CLI replay. The workflow receipt separately records actual execution UTC time. Research scope refuses a fixture clock and uses actual times or explicitly selected immutable stored runs. This avoids silently backdating research extraction to make a cache hit.

Caches and optional stored runs are explicit paths in the config. Source directories are never recursively scanned for documents. Read only the selected event IDs/doc IDs and their exact files. No Stage 6 pin, gold, draft, view or `validate_codebook(..., bundles=pilot)` call is part of this workflow. Loading frozen codebook metadata/rules via `load_codebook` is permitted; examples remain pointers and are never resolved.

### Completion evidence, independently of empty tables

`DocumentCompletion` binds a document/hash to all expected traversal units/windows, the extraction record, classifications, targets, assessments and assignment decisions. It records each layer's completeness and closed reason, plus an optional explicit `NoThemeDeclaration`. A declaration is a **processing adjudication**, not evaluation gold or a quality claim. It carries document/hash, source/coding/support run hashes, codebook reference, analysis/assignment policy hash, declaring actor ID, UTC date and literal `finding="no_theme"`; no excerpt or free-text reason. Fixtures supply an invented actor and declaration directly, never derive it from pipeline outputs.

The declaration is valid only when all required traversal windows have usable completed replies, all units were visited once, no unresolved extraction candidate/rejection, classification, assessment or decision remains, the explicit fixture/calibrated policy matches current bindings, and the declared document has no qualifying accepted assignment. A claimless run can satisfy the structural prerequisites, but its empty quotes/targets alone cannot supply the declaration. Empty eligible narrative or empty document selection remains `partial/no_eligible_units` or `empty_selection`, respectively. A fully completed valid-unmatched classification is visible as `valid_unmatched`; absent explicit adjudication it remains unobserved for headline absence.

| Evidence | New processing state | Analytical missing/completion reason |
| --- | --- | --- |
| Acquisition expected/acquired/unavailable/restricted/parse-failed | Preserve its existing state; write no fake processing transition | Original missing reason; expected/acquired also `not_processed` |
| Unexpected extraction abort with no validated `RunRecord` | `failed` via schema-2 processing transition | `processing_failed`; closed `unexpected_error` or `storage_corrupt`; usage `unreported` |
| Extraction document `failed` | `failed` | `processing_failed` plus closed extraction reason |
| Partial traversal, exhausted allowance, refused/incomplete classification/assessment, flagged/review decision | `partial` | `extraction_partial`, `classification_incomplete`, `assessment_refused`, `assessment_incomplete`, `assessment_flagged`, `calibration_required` or `policy_review` |
| Complete processing with >=1 accepted assignment, including masked-only audit acceptance | `completed` | No processing failure; separately record headline eligibility and mask exclusion |
| Complete processing, explicit valid no-theme declaration, matching policy | `completed-no-theme` | `explicit_no_theme`; eligible negative for the declared codebook only |
| Complete classification, valid unmatched claims, no declaration | `partial` | `valid_unmatched` |
| Complete rejected decisions, no accepted assignment, no declaration | `partial` | `no_theme_unconfirmed` |
| Zero quotes/targets with no declaration | `partial` | `no_theme_unconfirmed`, or an earlier structural failure reason |

When several obstacles occur, retain **all** layer outcomes in audit and choose the state summary by this order: unexpected abort/failed traversal; partial traversal; classification refusal/incompleteness; support refusal/incompleteness/flag; calibration/policy review; unmatched/no-theme-unconfirmed; completed/completed-no-theme. No precedence rule discards an original outcome.

This command does not require a fabricated extraction partial record after an arbitrary exception. Keep completed immutable stage runs/raw cache artifacts; record a separate application `WorkflowFailure` and the processing failure with fixed reason and usage availability. Do not invent a `RunRecord`, token count, raw response or partial quote set. The deferred non-`AdapterError` partial-record design is therefore **not triggered**. Revisit it explicitly only if an approved command change requires resumable partial extraction records.

### Denominators and equal issuer weighting

Build coverage from the **declared expected event population**, joined to latest validated acquisition/processing states by pilot/event/document IDs. A selected synthetic/pilot manifest defines a restricted population, not full-DJIA coverage. Retain events whose source/canonical/output is absent. Eligibility comes from the frozen event/membership join; ambiguous/ineligible events appear in coverage with their eligibility reason and never enter the eligible denominator.

Release-only processing owns release slots. Also emit a separate expected transcript coverage slot per declared event with `availability="not_yet_checked"`, `missing_reason="transcript_not_in_scope"`, `observable=false`; do not write a transcript Stage 5 `document_id`, imply a lawful transcript exists, or invent speaker metadata. Stage 13 adapts the schema/rights/speaker contracts. The report prints release and transcript availability separately and limits cross-document claims accordingly (R2.3).

Headline prevalence is **period-specific**, with at most one vote per issuer-period, irrespective of securities, copies, quotes, themes-per-quote, claims or targets. Denominator is distinct expected eligible issuer-periods satisfying complete observation for the specified document type, role and explicit policy/codebook; numerator is the subset with at least one unmasked accepted assignment in that direct/parent/family view. Print expected, available/parsed, final observable and excluded counts/reasons beside the rate. Denominator zero gives `rate=null`, `reason="empty_denominator"`.

Two additional labeled summaries are allowed: (a) distinct-issuer presence over a declared window, restricted to issuers with at least one fully observed period, with missing-period counts visible; (b) descriptive firm-quarter numerator/denominator over that window. Neither is silently substituted for period-specific headline prevalence. If an equal-issuer mean of within-issuer period rates is requested, compute each issuer's observed-period rate first, then average once per issuer; label the numerator as the sum of issuer fractions and denominator as issuers. Do not average quote rows or give issuers with more disclosed text/available quarters extra weight. This is analytical counting, not Stage 11's raw-signal pooling.

Parent presence is direct parent assignment **or any descendant**. Descendants are resolved from the selected frozen codebook with cycle/orphan checks; deduplicate each issuer-period/rolled-up-theme. Family presence follows explicit `theme_id -> family_id` memberships from a versioned mapping bound to the same codebook hash; a theme may enter multiple families. Missing mapping is no family view, not an invented default taxonomy. Reject mixed book versions/hashes and stale family mappings.

Disclosure-copy identity requires same event/issuer/period/document type and an explicit copy assertion bound to canonical hashes/source identities, or exact canonical-hash equality within that event. Never deduplicate across different periods, issuers or document types by text similarity. Keep all source records, document-qualified quote IDs, assignments and original claim links. Count distinct disclosure groups and distinct canonical span occurrences within each group; identical words at two offsets in one disclosure remain two quotes. If duplicate processing results disagree, retain the discrepancy in audit and mark `copy_processing_conflict` until resolved rather than treating copies as independent corroboration.

### Rights, evidence views and report publication

`audience="local"` and `audience="export"` are distinct publication profiles. Permission is explicit and source-specific, never inferred from SEC/free accessibility. Local-only permitted text can enter a local immutable view; exported versions withhold all text-bearing fields/links/views/raw source under local-only or restricted rights. Keep IDs, hashes, offsets and a plain source URL where permitted, with `withheld/rights_restricted`. Do not label withholding as lost extraction. Restricted acquisition with no lawful local text remains unobservable.

Each permitted accepted span has: current exact evidence metadata; a source text-fragment link made from exact text and `make_locator` context; an immutable saved source-artifact reference/hash where retention permits; and a standalone canonical HTML view with the **actual occurrence** highlighted and a stable anchor. The view is an explicitly labeled canonical snapshot, not a byte-identical source rendering or parser-fidelity claim. If raw source retention is forbidden, record `snapshot_withheld` and its rights reason instead of inventing the required fallback. Source-link drift/highlight failure never changes a verified span.

Use a separate per-span view, so overlapping spans and long pages need no ambiguous DOM range merger. Escape the complete canonical text and insert one `<mark id="p-<digest>">` from the verified `[start,end)` slice; show source/version/hash/offset metadata outside its `<pre>`. Static CSS is inline, no JavaScript or remote resources. Saved artifact filenames are content hashes, not arbitrary doc IDs. Canonical code-point offsets remain stored coordinates; convert to UTF-16 **only** in application browser-boundary expected-range metadata (`len(text[:offset].encode("utf-16-le")) // 2`). Neither conversion nor DOM observation becomes verification input.

Text-fragment syntax/percent-encoding follows the primary [WICG draft](https://wicg.github.io/scroll-to-text-fragment/) consulted on 2026-10-06: encode text parameters, including literal dash, comma and ampersand, and retain prefix/suffix context for repeated occurrences. This draft specifies a matching mechanism, not a guarantee that a particular browser highlights a local or external page. V5 records observations.

The default report is escaped standalone HTML with coverage tables, direct/parent/optional-family prevalence, restrictions, policy scope, non-acceptance/novelty audit counts, and evidence citations. Every cited assignment links its document-qualified quote to its immutable view and source link, or explicitly withheld metadata. Claims are labeled model-derived; raw scores/panel trials remain assessment evidence with no quality/acceptance claim. No raw request/reply/rationale or rejection detail is copied into the report.


### Task9 processing/provenance execution disposition (2026-10-07)

Controller source-audited actual records.py/states.py/consume.py/coverage.py after a pre-edit NEEDS_CONTEXT. This implements the already required schema-2 missingness and two-artifact retry boundary without changing C2's normative hash, AnalysisInputs/public signatures, fourteen schemas, source artifacts or processing graph. No general terminal reopening, latest-run discovery or source-provenance exclusion is authorized.

1. Narrow missing-reason compatibility: Analysis AcquisitionStatus for state=partial/state_schema_version=2 requires exactly one of the existing ProcessingMissingReason values except processing_failed: extraction_partial, classification_incomplete, assessment_refused, assessment_incomplete, assessment_flagged, calibration_required, policy_review, valid_unmatched, no_theme_unconfirmed, no_eligible_units, copy_processing_conflict. Schema1 partial retains legacy missing_reason=None. Reject schema2 partial null/unknown/processing_failed. No new fields/types/schema/dtype/grain, and no ingestion import in themes. Existing state_run_id/state_schema_version/document_id resolve the original processing_reason in immutable state history; do not invent a parse failure or clear missingness. Document this fail-closed validator compatibility decision and test producer/consumer/coverage together with invented records. Existing valid schema1 remains compatible; formerly accepted malformed schema2-partial null is refused, not migrated/relabelled.

2. Distinguish source acquisition baseline from appended processing authority. C2 continues hashing every field of the selected acquisition projection and every other approved member; never remove state/run/schema/reason or patch old hashes. On a first workflow, read/recheck the latest validated parsed acquisition predecessor under the common ProcessLock. Publish its derived processing outcome, then append schema2 with actual analysis-manifest SHA and that document's actual completion hash; this append cannot mutate the preceding analytical publication. The report's coverage processing outcome is derived from checked completions; state_run_id/schema remain the explicitly selected acquisition baseline reference. The workflow receipt separately binds the actual appended/current state-file bytes and status. Label this as analysis-as-published plus separately verified current processing, not a claim that original schema1 reference is the later state file.

3. Same-workflow retry: resolve only deterministic artifacts belonging to the explicit configured workflow/output/run IDs (or explicitly supplied stored artifacts), never scan/select latest source/stage runs. Read original public stage/analysis manifests; reconstruct their exact parsed predecessor from validated current history, not an arbitrary earlier row. It must be the immediate immutable acquisition predecessor of the terminal ProcessingTransition; check_histories and PROCESSING_PREDECESSOR_FIELDS equality still apply. Only a terminal with matching configured processing_run_id AND processing_run_hash equal to actual selected existing analysis run.json bytes AND per-doc completion_hash/outcome/reasons matching currently reverified analysis may authorize this baseline. Bind current universe/event/pilot, source/canonical/raw/masks/rights, book, policies, selected stages/caches and complete config/identities again; old receipt/cache-hit alone grants nothing. A differing config, publisher bytes, source, policy, completion, ownership or history refuses before new publication/state. The actual source/baseline hash must equal the stored source/support/coding/analysis bindings; no regeneration/relabeling under a new digest to force equality.

4. Pending versus recorded state: when latest remains the same parsed predecessor, retry the identical analysis hash/completion and append once under the common lock after recheck. When matching schema2 terminal is already recorded, reuse its validated exact state artifact/hash with no duplicate transition, report state_recorded; do not reopen it. Preserve prior pending receipt, emit a new immutable content-hashed receipt. Failed stage/publication uses its separately bound WorkflowFailure artifact; do not treat a failure-hash terminal as an analysis-hash completion or retry it into success. An incompatible or other-workflow terminal is state_not_processable.

5. Explicit stored-completed consumption by a different workflow can use no_state_change only when caller additionally selects the actual published analysis directory and pinned run.json SHA (a narrow optional paired selection in the new WorkflowConfig, documented/validated in Task9), alongside all explicit stored extraction/support/coding stages. Read/reverify those bytes with the same selected current inputs/analysis policy/family mapping; latest terminal processing_run_hash must match them, completion hashes/outcomes must match and immutable parsed predecessor must reconstruct the identical C2 baseline. If missing/changed/foreign analysis bytes or differing requested policy/family/declarations, refuse; never infer provenance from terminal IDs/hash alone. Do not append a zero-transition file or pretend a new configuration reused completed processing. Same-workflow retry uses its deterministic own artifacts without requiring changed config; no automatic other-workflow analysis selection. New WorkflowConfig has no previously published schema to migrate; add only the necessary explicit selector fields, not a new predecessor analytical inventory/framework.

6. Extra narrowly granted ownership for this actual blocker: analysis/records.py AcquisitionStatus validator only; tests/analysis/test_records.py; minimal invented partial projection test in tests/analysis/test_coverage.py; cross-package producer/consumer tests in tests/contracts/test_processing_state_compatibility.py; dictionary/registry already owned. No changes to ingestion state graph/reader/writer, themes provenance helper or AnalysisInputs/store/report/frame schemas. Meaningful guarded records/coverage/states RED before validator fix; exact records/coverage GREEN plus required workflow/states/consume/export/dictionary, affected Ruff/checkformat/diffcheck. Keep every check sequential and audit all imports/fixtures/transitive readers. No root/user-wording/browser/model/network/protected operations. FreshUltra Task9 review must judge all this additional safety/compatibility surface; report exact implementation semantics/disposition deviations before further changes.

This explicit controller disposition preserves approved C1/C2 and realizes the plan's already authorized immutable acquisition/publication/state receipt design; it is not a redesign or a waiver of current gates. If implementation exposes another irreducible seam, return concrete NEEDS_CONTEXT before silent alteration.

## File ownership and interfaces

All paths below are repository-relative for implementation. The execution controller records each task's BASE before dispatch, grants only its listed ownership, and provides actual signatures from approved predecessors. Task tests may use their package's existing invented helpers; shared new fixtures live only at the explicit paths below. No task edits `evaluation/`, frozen codebooks, signed gold, split files or protected artifacts.

| Owner / exact files | Responsibility / tasks |
| --- | --- |
| `tools/stage10_checks.py` (new), `tools/stage10_pytest.py` (new), `tests/contracts/test_stage10_check_runner.py` (new) | Audited allowlisted groups and metadata-only failure runner; Task 1, expanded Tasks 10/11 |
| `packages/earnings-themes/src/earnings_themes/extraction/records.py`, `store.py`, `__init__.py`; `packages/earnings-themes/tests/test_extraction_records.py`, `test_extraction_store.py` | Stage 7 prerequisite and public gate export; Task 1 |
| `packages/earnings-themes/src/earnings_themes/analysis/__init__.py`, `records.py`, `problems.py` (new); `packages/earnings-themes/tests/analysis/__init__.py`, `cases.py`, `conftest.py`, `test_records.py`, `test_safe_output.py` (new) | Explicit normalized analytical contracts / invented fixtures; Task 2 |
| `packages/earnings-themes/src/earnings_themes/analysis/consume.py` (new); `packages/earnings-themes/tests/analysis/test_consume.py` (new) | Current upstream consuming gates; Task 3 |
| `packages/earnings-ingestion/src/earnings_ingestion/events/states.py`, `state_table.py`; `packages/earnings-ingestion/tests/test_events_states.py`, `test_events_state_table.py`; `tests/contracts/test_processing_state_compatibility.py` (new) | Schema-2 processing transitions alongside immutable schema 1; Task 4 |
| `packages/earnings-themes/src/earnings_themes/analysis/rows.py` (new); `packages/earnings-themes/tests/analysis/test_rows.py` (new) | R11.1 observations, originals/audit and copy grouping; Task 5 |
| `packages/earnings-themes/src/earnings_themes/analysis/completion.py`, `coverage.py`, `prevalence.py` (new); `packages/earnings-themes/tests/analysis/test_completion.py`, `test_coverage.py`, `test_prevalence.py` (new) | Completion proof, denominators, mask/hierarchy/family views and V10; Task 6 |
| `apps/earnings-pipeline/src/earnings_pipeline/evidence_views.py`, `browser_evidence.py` (new); `apps/earnings-pipeline/tests/test_evidence_views.py`, `test_browser_evidence.py` (new) | Static canonical snapshots, links, rights and public-renderer boundary; Task 7 |
| `packages/earnings-themes/src/earnings_themes/analysis/store.py` (new); `packages/earnings-themes/tests/analysis/test_store.py` (new); `apps/earnings-pipeline/src/earnings_pipeline/theme_report.py` (new); `apps/earnings-pipeline/tests/test_theme_report.py` (new) | Typed immutable analytical publication and cited local/export reports; Task 8 |
| `apps/earnings-pipeline/src/earnings_pipeline/theme_config.py`, `theme_workflow.py`, `extract_cli.py` (new), `cli.py`; `apps/earnings-pipeline/tests/test_theme_config.py`, `test_theme_workflow.py`, `test_extract_cli.py` (new) | Explicit replay composition, paths, policy scope and processing run; Task 9 |
| `packages/earnings-ingestion/src/earnings_ingestion/browser/selenium_capture.py`; `packages/earnings-ingestion/tests/test_browser_evidence_lifecycle.py` (new); `apps/earnings-pipeline/tests/test_browser_evidence.py`; `tests/integration/test_stage10_browser.py` (new); `expirements/parser-fidelity/layout1-preregistered.toml`; `docs/verification/stage10-browser.md` (new), `docs/verification/layout-1.md`; `specs/browser-rendering-integration.md` | Narrow capture lifecycle assessment/amendment/disclosure, V5 record/user gate; Task 10 |
| `tests/fixtures/themes/stage10/scenario.json`, `family-map-v1.json`, `replay-config.json` (new; invented metadata only); `tests/integration/stage10_cases.py`, `test_theme_vertical_slice.py`, `test_theme_coverage.py`, `test_theme_frozen_v0.py`, `test_theme_wording.py` (new); `tests/contracts/test_analysis_contracts.py` (new); `tests/contracts/test_import_scan.py`, `test_data_dictionary.py`; themes `tests/test_import_boundaries.py` | V8/V10, frozen metadata plumbing, public/import/wording and blind verification; Task 11. Also seed `docs/verification/theme-vertical-slice.md` with actual fixture evidence under the sequential shared grant below |
| `README.md`, `CLAUDE.md` current-state sections; `docs/data-dictionary.md`; `docs/verification/theme-vertical-slice.md` (new); shared specification Rollout; roadmap reconciliation/handoffs; `specs/deferred_items.md`; this plan (then completed path) | Documentation, reviews, observed gates, authoritative completion and deliberate integration; Task 12 |

No pyproject/uv.lock change is planned. Do not add Selenium to default imports. Updating docs/data-dictionary.md belongs in **each contract-changing task**, with final completeness checks in Task 12; this shared documentation ownership is sequential.

**Sequential verification-document ownership clarification (2026-10-07):** Task 11 step 6 already requires the new V8/V10 verification record. Task 11 may seed `docs/verification/theme-vertical-slice.md` with its actual fixture-only arithmetic, safe commands/counts and explicitly pending V5/user gates. Task 12 then finishes this document and completion evidence. This resolves the table/step mismatch without new functionality, pilot extraction or concurrent ownership.

Public interfaces to implement (concrete arguments, no implicit I/O):

```python
# earnings_themes.extraction.store
validate_stored_run(run: StoredRun) -> StoredRun

# earnings_themes.analysis
reverify_analysis_inputs(inputs: AnalysisInputs) -> BoundAnalysis
build_observations(bound: BoundAnalysis) -> AnalysisTables
document_completions(bound: BoundAnalysis) -> tuple[DocumentCompletion, ...]
build_coverage(bound: BoundAnalysis, completions: tuple[DocumentCompletion, ...]) -> pl.DataFrame
prevalence(tables: AnalysisTables, coverage: pl.DataFrame,
           book: Codebook, policy: AnalysisPolicy,
           families: ThemeFamilyMap | None) -> pl.DataFrame
build_analysis(inputs: AnalysisInputs, policy: AnalysisPolicy,
               families: ThemeFamilyMap | None) -> AnalysisRun
write_analysis_run(directory: Path, result: AnalysisRun,
                   inputs: AnalysisInputs, policy: AnalysisPolicy,
                   families: ThemeFamilyMap | None,
                   evidence: tuple[EvidenceViewReference, ...]) -> Path
read_analysis_run(directory: Path) -> StoredAnalysisRun
reverify_analysis_run(stored: StoredAnalysisRun, inputs: AnalysisInputs,
                      policy: AnalysisPolicy,
                      families: ThemeFamilyMap | None) -> None

# earnings_ingestion.events.state_table / states
ProcessingTransition  # schema 2, independent processing failure semantics
StateRecord = StateTransition | ProcessingTransition
write_processing_run(directory: Path,
                     transitions: Sequence[ProcessingTransition]) -> Path
read_runs(directory: Path) -> list[StateRecord]  # reads both exact schemas
current_states(transitions: Iterable[StateRecord], pilot_hash: str) -> dict[str, StateRecord]

# earnings_pipeline.evidence_views / browser_evidence / theme_report
make_evidence_view(bound: BoundAnalysis, doc_id: str, quote_id: str,
                   *, audience: Literal["local", "export"],
                   raw_snapshot: RawSnapshot | None) -> EvidenceView
capture_evidence_view(view: EvidenceView, renderer: BrowserRenderer,
                      policy: CapturePolicy) -> CaptureObservation
write_theme_report(directory: Path, stored: StoredAnalysisRun,
                   inputs: AnalysisInputs, policy: AnalysisPolicy,
                   families: ThemeFamilyMap | None,
                   views: tuple[EvidenceView, ...],
                   *, audience: Literal["local", "export"]) -> Path

# earnings_pipeline.theme_workflow
run_theme_workflow(config: WorkflowConfig, runtime: WorkflowRuntime,
                   *, now: Callable[[], datetime]) -> WorkflowResult
```

`BoundAnalysis` and `AnalysisTables` are frozen `repr=False` containers. Public `build_analysis`, analytical write/reverify and application publication call the current gates themselves; possession of a prior `BoundAnalysis` never permits skipping reverification after callbacks or a later export. Pure row/count helpers accept only their explicitly checked in-memory inputs and perform no source discovery or I/O.

## Contract and schema inventory

All new analytical models use a strict, extra-forbid, frozen `AnalysisPart` with `schema_version: Literal[1] = 1`; source-bearing fields have `repr=False`. Persist dates as `pl.Date`, timestamps as `pl.Datetime("us","UTC")`, offsets/counts as `pl.Int64`, flags as `pl.Boolean`, nullable strings as `pl.String`, ID collections as `pl.List(pl.String)` and structured references as explicit `pl.Struct` schemas. Empty tables retain those declared types. Never infer a schema or convert via pandas.

| Contract | Complete essential fields / invariants |
| --- | --- |
| `ExpectedEvent` | `event_id`, `entity_id`, `cik`, `period_end`, nullable `fiscal_year`/`fiscal_quarter`, `eligibility_status` (`eligible/ineligible/ambiguous`), closed `eligibility_reason`, `membership_assertion_id`, `event_manifest_hash`, `pilot_hash`; event identity unique and fiscal facts agree with the frozen event row |
| `AcquisitionStatus` | `event_id`, `document_id` (release slot), `state`, nullable `missing_reason`/closed parse `failure_reason`, nullable `doc_id`, `source_document_id`, `raw_hash`, `accession`, `exhibit`, UTC `retrieved_at`, `state_run_id`, `state_schema_version`, `pilot_hash`; no text/detail/attempt detail |
| `DocumentMetadata` | `doc_id`, `event_id`, `entity_id`, `cik`, `doc_type="release"`, `publisher`, validated HTTP(S) `source_url`, `source_document_id`, `raw_artifact`/`raw_hash`, `canonical_hash`, `canonicalization_version`, `parser_version`, `canonical_manifest_hash`, `mask_policy_id`/`mask_policy_version`/`mask_manifest_hash`, nullable `filing_at`/`published_at`/`event_at`, UTC `retrieved_at`, `period_end`, nullable fiscal labels, `rights_status`, `rights_basis`, `access_status`, `retain_text`, `export_text`, `retain_raw`, `export_raw`, `retain_capture`; IDs/hashes/period agree with canonical/acquisition/expected inputs; permissions cannot widen source rights |
| `CopyAssertion` | `copy_id`, `event_id`, sorted `doc_ids`, sorted `(doc_id,canonical_hash)` bindings, `method="same_event_exact_hash"` or `"reviewed_copy"`, `evidence_ref`, `rule_version`, nullable actor/date for reviewed assertions; no cross-event/issuer/type merge |
| `AnalysisPolicy` | `policy_id="coverage-analysis"`, `version="1"`, `population_id`, exact sorted `event_ids`, `population_hash`, `doc_types=("release",)`, `speaker_roles=("not_applicable",)`, `mask_policy_id`/version, `dedup_rule="same-event-disclosure/1"`, `parent_rule="self-or-descendant/1"`, `headline_unit="issuer_period"`, `window_issuer_rule="any-complete-period/1"`, `include_family_view` bool, `scope="fixture"` or `"research"`; no acceptance threshold or scorer-view setting |
| `ThemeFamilyMap` | `mapping_id`, positive `version`, `content_hash`, exact `CodebookReference`, sorted unique `memberships` of `(theme_id,family_id)`, family labels; allow overlap, refuse unknown theme/duplicate pair/mixed/stale codebook; mapping hash uses existing canonical digest |
| `NoThemeDeclaration` | Fields defined under completion above; unique per doc; fixture actor/policy visibly fixture-bound; no free-text or gold assertion |
| `DocumentCompletion` | `doc_id`, `event_id`, `canonical_hash`, `source_run_hash`, `coding_run_hash`, `support_run_hash`, codebook/policy refs, `traversal_complete`, `classification_complete`, `assessment_complete`, `decision_complete`, `eligible_units`, `completed_windows`, `failed_windows`, accepted/masked/rejected/review/refused/flagged/incomplete/unmatched counts, `processing_state`, ordered closed `reasons`, nullable `declaration_hash`, `observable`, `policy_scope`; completeness never derived from accepted-row count |
| `EvidenceViewReference` | `evidence_id`, `doc_id`, `quote_id`, `canonical_hash`, `start`, `end`, `validator_version`, `element_id`, current `mask_ids`, `locator_hash`, quote-text hash, nullable source text-fragment URL, plain source URL, nullable raw/canonical/view artifact refs with hashes, stable `anchor_id`, `audience`, `rights_status`/`rights_basis`, `status="available"/"withheld"`, nullable fixed reason; source-bearing fields private |
| `CaptureObservation` | `evidence_id`, `doc_id`, `quote_id`, `canonical_hash`, CP span and browser-boundary UTF-16 span, nullable capture ID/artifact refs, capture policy/environment identity, `status="completed"/"partial"/"failed"/"unavailable"/"not_requested"`, nullable closed reason, `screenshots_rights="local_only"`; capture status is not highlight success or quote verification |
| `RawCacheVerification` | stage (`extraction/classifier/scorer/judge`), status (`verified/not_supplied/not_bound`), sorted confined reference/hash bindings, verification method/version; `verified` only after actual supplied bytes have passed the appropriate cache reader/hash method |
| `AnalysisRunRecord` | analysis schema/version; run ID/UTC date; scope/audience; population/event/pilot/universe hashes; ordered doc/hash, canonical/mask manifest, extraction/coding/support/configuration/prompt/identity references; codebook, assignment policy or null, analysis policy, family map or null; completion/copy hashes; validator/software/lock identities; counts by state/decision/reason; raw verification statuses; sorted table and evidence artifact hashes; `billable_cost="none, self-hosted"`; canonical hashing excludes only explicitly documented operational publication fields; a separate report manifest binds the report bytes, avoiding a circular hash or mutation of published `run.json` |
| `AnalysisInputs` | frozen repr-false dataclass holding `SupportSources`, stored support/coding runs, actual `AssignmentPolicy | None`, normalized expected events/acquisition/doc metadata, copy assertions, no-theme declarations, explicit provenance hash, raw-verification records, `RawCacheInputs`, `raw_snapshots: tuple[RawSnapshot, ...]`, `analysis_policy: AnalysisPolicy`, `canonical_snapshots: tuple[CanonicalSnapshot, ...]`, and `fixture_authorization: FixtureAuthorization | None`; not an ingestion/network client |
| `RawSnapshot` | frozen repr-false dataclass: `doc_id: str`, `artifact: ArtifactRef`, `data: bytes`; explicitly supplied raw source bytes, actual hash and source/rights binding checked at consuming/publication gates; no loader or persisted raw payload |
| `CanonicalSnapshot` | frozen repr-false dataclass: `doc_id: str`, `data: bytes`; explicit existing four-part canonical JSON snapshot; pure gate reconstructs core document/elements/masks and compares current bindings, application validates full artifact through public ingestion reader; no implicit loader |
| `FixtureAuthorization` | frozen repr-false dataclass: `corpus_id: Literal["djia-synthetic", "stage10-invented"]`, `event_manifest_hash: str`, `pilot_hash: str`, `provenance_hash: str`; explicit approved fixture inventory binding; fixture scope requires it, research scope refuses it and fixture policies; no name/root inference |
| `RawCacheInputs` | frozen repr-false dataclass: `coding: CodingCache | None`, `support: SupportCache | None`; neither constructor opens a cache; extraction stored-run raw bindings remain `not_bound` because schema 1 publishes none |
| `BoundAnalysis` | frozen repr-false dataclass: `inputs: AnalysisInputs`, `decisions: DecisionSet`, strict normalized inventories, `binding_hash: Sha256Hex`; hash computed from current checked contents; no reusable unchecked validity flag |
| `AnalysisTables` | frozen repr-false dataclass: `frames: Mapping[str, pl.DataFrame]`, with exactly the fourteen declared table names and explicit schemas; row/grain/FK validation before serialization |
| `AnalysisRun` / `StoredAnalysisRun` | frozen repr-false dataclasses: `record: AnalysisRunRecord`, `tables: AnalysisTables`; stored records additionally bind actual published byte hashes; structural read alone grants no current validity |
| `EvidenceView` | frozen repr-false dataclass: `reference: EvidenceViewReference`, `html: bytes | None`, `canonical_bytes: bytes | None`, `raw_bytes: bytes | None`, required `retain_capture: bool`; available bytes must match their reference hashes and rights profile, withheld fields are null |
| `ReportManifest` | report schema/version, report ID/UTC date/audience/scope, selected analysis manifest byte hash, current binding hash, codebook/assignment/analysis/family references, sorted report/view/source artifact hashes, withholding/capture/V5 limitations; publish separately from immutable analysis `run.json` |
| `WorkflowConfig` | schema 1; run ID; scope; replay mode literal; nullable UTC `fixture_started_at` allowed only for fixture scope; explicit universe/event/pilot files and pinned hashes; sorted selected event IDs; states/canonical/source metadata paths; prompts and complete extraction/coding/support policies/ceilings/identities/lineage; raw cache paths; nullable explicit stored extraction/support/coding directories; nullable fixture-policy selector or externally supplied policy reference; analysis/family/declaration configs; audience; output directory; capture flag/policy/installed-binary reference or null; strict confined paths and UTC timestamps |
| `WorkflowFailure` | run ID, phase (`preflight/extraction/coding/support/analysis/publication/state`), validated event/doc IDs, closed reason, completed stage manifest IDs/hashes, usage availability (`known/unreported`), UTC date; no fabricated partial extraction record, text/detail or traceback |
| `WorkflowRuntime` | frozen repr-false dataclass: explicit `ModelAdapter`, `Classifier`, `EntailmentScorer`, two `Judge`s, nullable actual `AssignmentPolicy`, nullable public `BrowserRenderer`; Stage 10 CLI supplies replay façades only |
| `WorkflowResult` / `WorkflowReceipt` | result holds validated run/artifact IDs/hashes, per-phase/state counts and fixed status; receipt is schema 1 with run ID/UTC date, immutable analysis/report/failure refs, nullable state-file ref/hash, and `state_pending/state_recorded/no_state_change/failed`; write a new content-hashed receipt per state outcome, never overwrite an earlier receipt |

The persisted analytical tables and exact row grains are:

| Table | Grain and fields |
| --- | --- |
| `observations` | One `(entity_id,period_end,doc_type,speaker_role,theme_id,doc_id,quote_id,codebook_id,codebook_version)`; also event/assignment IDs, book hash, canonical hash/start/end/element/validator, current mask IDs, `headline_eligible`, disclosure group, policy kind/hash, source/coding/support run refs, evidence ID, nullable rights-filtered `quote_text`, publication/retrieval/extraction times and source metadata reference. Quote text is materialized from the canonical span. No claim multiplication of this grain. |
| `quotes` | Every retained `(doc_id,quote_id)` reverified, including masked/unassigned quotes; CP span/hash/element/current masks, source refs and nullable rights-filtered text |
| `claims` | Every `(doc_id,claim_id)` with extraction window/attempt, model-derived interpretation hash and rights-filtered local interpretation, original quote ID list and source run; no sentiment/topic used as theme |
| `claim_evidence` | Every original `(doc_id,claim_id,quote_id)`; no pruning to accepted/supporting-only evidence |
| `assignment_claims` | Every original Stage 9 assignment–claim–decision–target link; document-qualified |
| `classifications` | Every original classification, including refused/incomplete and valid-unmatched; IDs, status, fixed reason and proposed theme IDs; no raw reply |
| `decisions` | Every original decision with status/reason/policy, support status/flags/missing, original/supported quote ID links and hashes; no raw rationale |
| `novelty` | Every valid-unmatched original pointer-only novelty row with reason `no_theme_fit`; no new taxonomy |
| `rejections` | Stage 7 refusal subject IDs, fixed reason, attempt/index, optional trusted element IDs; never source-bearing label/detail |
| `completions` | `DocumentCompletion` rows; separates layer completeness from acceptance |
| `coverage` | One declared `(event_id,doc_type,speaker_role)` slot, including absent releases and transcript-not-in-scope; entity/CIK/period/eligibility, expected/available/parsed/observable, latest state/run/schema, fixed missing reasons, policy scope, accepted/masked/review/rejected/refused/flagged/incomplete/unmatched counts, copy/metadata/completion refs |
| `prevalence` | One `(population_hash,period-or-window,doc_type,speaker_role,view_kind,view_id,codebook_id,version,analysis_policy_hash,family_map_hash-or-null,unit)`; numerator, denominator, nullable rate, empty reason, expected/available/observable/excluded counts and fixed restrictions; `view_kind=direct/parent/family`; no mixed-version comparison |
| `copies` | Every document-to-disclosure-group membership, representative ID, copy assertion/rule/hash and conflict status; originals remain reachable |
| `evidence` | `EvidenceViewReference` rows, plus opaque optional capture observation references; screenshots local-only |

All persisted tables include analytical schema version 1 and appropriate foreign keys. Use explicit `TABLE_SCHEMAS` beside these record definitions; data dictionary and contract tests enumerate every field, dtype, enum and foreign key.

## Sequential execution and verification protocol

Start execution in a **fresh** session. Read this plan and Global Constraints first; recheck status/HEAD, preserve the saved plan and any other uncommitted work. Use `using-git-worktrees` to create/reuse an isolated execution checkout only when execution is authorized, carrying the plan explicitly without copying protected ignored files. Default future branch name is `codex/stage10-coverage-export`. Record actual base/ownership in the ledger; do not assume today's clean SHA is still current. No branch/worktree is created by this planning session.

For every task below:

1. Record its BASE SHA before dispatch. Use the skill's task-brief script; prepend the complete identical Global Constraints. Give the fresh implementer only its brief, relevant source/contracts, permitted fixture references and actual prior interfaces, never controller history or protected contents.
2. Implementer writes a meaningful failing test, observes its guarded failure, makes the smallest implementation, runs the named passing checks, self-reviews, and records safe command/results. Future execution may commit task changes; this planning session may not.
3. Stop the implementer before dispatching the read-only `task-reviewer`. Its first phase checks spec/plan conformance, its second checks quality; require explicit approval for **both**. Use the BASE-to-current-HEAD review package, not `HEAD~1`. Reviewers do not execute protected readers and use only the same guarded allowlist if a check is necessary.
4. Fix genuine Critical/Important findings, re-run covering checks, obtain scoped re-review and resolve every “cannot verify” item. Reconcile plan-mandated contradictions with the user rather than silently choosing another requirement. Minor findings remain in the ledger for final triage. No next task until both approvals and passing checks are recorded.
5. Append `Task N: complete (commits <base>..<head>, spec approved, quality approved)` and interface/deviation facts to the plan's `.sdd` ledger. At context pressure, take a clean task-boundary handoff to a fresh controller; resume by reconciling ledger signatures and commits, never redoing completed tasks.

Every brief also directs its agent to this plan's **Decisions fixed by this plan**, **Contract and schema inventory**, its exact **File ownership** row and **Guarded check commands**. These are requirements, not optional background; the skill's task-text extraction alone does not carry them. Do not make a worker guess types or scope from an isolated snippet. Shared contract changes update `docs/data-dictionary.md` and its registry in `tests/contracts/test_data_dictionary.py` in the same task, so each contract checkpoint can run that exact test without waiting for Task 11.

| Tasks | Implementer route | Task reviewer route |
| --- | --- | --- |
| 1, 3, 4, 7, 8, 9, 10 | Sol Medium; escalate effort/context per skill, structural redesign uses Sol Ultra | Sol Ultra (consumption, compatibility, rights/publication and lifecycle risk) |
| 2, 5, 6, 11, 12 | Sol Medium | Sol Medium; Sol Ultra if the actual diff changes a shared safety/compatibility boundary |
| Final whole branch and independent second opinion | No implementation while review runs | Sol Ultra for each, **sequentially** |

The user's sequential constraint overrides skills' suggestions to launch final seats together. Read the subagent-driven-development templates/model-selection and requesting-code-review recipes in the execution session. Use the approved Codex substitution, not unsupported Sonnet/Opus IDs or an inherited model pin. Two sequential review seats at the same BASE/HEAD satisfy final independent review; if the second-opinion mechanism is unavailable, record that fact and obtain its disposition before integration, never claim it ran.

### Guarded check commands

Task 1 introduces `tools/stage10_checks.py GROUP`. It resolves the repository root from its own location, uses a hardcoded group-to-node allowlist, disables external pytest plugin auto-loading and explicitly enables the reviewed workspace `pytest_asyncio.plugin`, runs the child interpreter with captured stdout/stderr and a timeout, and prints only pass/fail/skip/deselected/warning counts, validated static test IDs or hashed case IDs, and fixed `test_failed/collection_failed/runner_failed/runner_timeout/runner_interrupted` reasons. The child plugin writes a metadata-only JSON result in a private temporary directory. Never print raw captured output, failure frames/longrepr, traceback, warnings, parametrized source values or subprocess exceptions. Return pytest's nonzero status. No automatic rerun with verbose diagnostics. Explicit plugin loading keeps the user full-root gate compatible with the project's dev dependency while preventing an unrelated installed plugin from opening protected inputs.

For the initial runner's own tests, the controller uses a one-time captured child command and emits only its exit code; its source/fixtures are entirely invented. After that, all pytest commands in this plan run through the guarded runner. Tests themselves use explicit safe parametrization IDs and assert IDs/counts/hashes/booleans rather than whole source-bearing objects. The runner is an output guard, **not** permission to execute a protected reader.

```bash
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py runner
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py extraction
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py GROUP
```

`GROUP` in the command form means one of the exact names below; each task names its actual group. The fixed temporary uv cache is a sandbox-compatible cache, not a change to dependencies. No sync/download is implicit. If the environment lacks reviewed dependencies, resolve that setup limitation explicitly; don't switch to a network/billable/protected path.

| Group | Exact collected files (all future new paths are listed in file ownership) |
| --- | --- |
| `runner` | `tests/contracts/test_stage10_check_runner.py` |
| `dictionary` | `tests/contracts/test_data_dictionary.py` |
| `extraction` | themes `tests/test_extraction_records.py`, `test_extraction_store.py`, `test_extraction_window.py`, `test_extraction_run.py`, `test_extraction_windows.py`, `test_extraction_cache.py`, `test_extraction_injection.py` |
| `records` | themes `tests/analysis/test_records.py`, `test_safe_output.py` |
| `consume` | themes `tests/analysis/test_consume.py`; `tests/contracts/test_support_contracts.py`, `test_coding_contracts.py` |
| `states` | ingestion `tests/test_events_states.py`, `test_events_state_table.py`; `tests/contracts/test_processing_state_compatibility.py`; `tests/integration/test_event_fixtures.py`, `test_event_corpus_v1.py` |
| `rows` | themes `tests/analysis/test_rows.py`, `test_safe_output.py` |
| `coverage` | themes `tests/analysis/test_completion.py`, `test_coverage.py`, `test_prevalence.py` |
| `evidence` | application `tests/test_evidence_views.py`, `test_browser_evidence.py`; core `tests/test_locators.py`, `test_evidence.py` |
| `export` | themes `tests/analysis/test_store.py`; application `tests/test_theme_report.py` |
| `workflow` | application `tests/test_theme_config.py`, `test_theme_workflow.py`, `test_extract_cli.py`, `test_cli.py` |
| `browser-unit` | ingestion `tests/test_browser_evidence_lifecycle.py`, `test_browser_renderer.py`, `test_browser_records.py`, `test_browser_store.py`; application `tests/test_browser_evidence.py` |
| `vertical` | `tests/integration/test_theme_vertical_slice.py`, `test_theme_coverage.py`, `test_theme_frozen_v0.py`, `test_theme_wording.py` |
| `contracts` | `tests/contracts/test_analysis_contracts.py`, `test_processing_state_compatibility.py`, `test_data_dictionary.py`, `test_import_scan.py`, `test_support_contracts.py`, `test_coding_contracts.py`; themes `tests/test_import_boundaries.py`; ingestion `tests/test_import_boundaries.py` |
| `upstream` | themes extraction files in `extraction`; support/coding files in the exact lists below; `tests/integration/test_support_fixtures.py`, `test_support_wording.py`, `test_coding_frozen_v0.py`, `test_coding_wording.py` |
| `stage10` | Union of the explicit audited non-browser groups, with duplicate files removed; no broad root traversal |

Every group uses `-m 'not live and not browser' --tb=no --show-capture=no -q`; no `-vv`, `-l`, `--showlocals`, `--full-trace` or raw-output fallback. Before adding a file/group, audit its top-level imports, fixtures and readers against the blinding rule. All existing basenames listed here were checked during planning. If a later authorized change renames a file, record the exact scoped correction; never expand to a directory to compensate.

The `upstream` support list is exactly: `test_allowance.py`, `test_assess.py`, `test_cache.py`, `test_context.py`, `test_injection.py`, `test_judges.py`, `test_metrics.py`, `test_nli.py`, `test_prompt.py`, `test_records.py`, `test_resolve.py`, `test_run.py`, `test_safe_output.py`, `test_scorers.py`, `test_store.py`, all under `packages/earnings-themes/tests/support/`. The coding list is exactly: `test_adapters.py`, `test_assignments.py`, `test_cache.py`, `test_classify.py`, `test_decide.py`, `test_injection.py`, `test_input.py`, `test_prompt.py`, `test_records.py`, `test_run.py`, `test_safe_output.py`, `test_store.py`, all under `packages/earnings-themes/tests/coding/`. `test_nli_live.py` is not collected. No wildcard/directory collection expands this list.

The only human modes are `browser-user`, `root-user`, `wording-fixture-user` and `wording-pilot-user`; require an explicit `--user-only` flag. That flag is an accidental-invocation guard, not a claim that software can identify a human caller; all agent briefs still forbid those modes. Unknown groups/options yield a fixed runner reason without echoing the input. User modes keep the same captured-output/metadata-only boundary.

Ruff runs on `packages apps tests tools`, with Markdown excluded by existing config. Use `uv run --locked --offline --no-sync ruff check packages apps tests tools` and `ruff format --check packages apps tests tools`. No type checker is configured; if a later approved change adds one, run its affected checks. No root default suite is an agent check.

## Tasks

### Task 1: Guard diagnostics and harden Stage 7 before stored-run consumption

**Files:** Create `tools/stage10_checks.py`, `tools/stage10_pytest.py`, `tests/contracts/test_stage10_check_runner.py`; modify `packages/earnings-themes/src/earnings_themes/extraction/records.py`, `store.py`, `__init__.py`, `packages/earnings-themes/tests/test_extraction_records.py`, `test_extraction_store.py`, `docs/data-dictionary.md`, `tests/contracts/test_data_dictionary.py`. **Produces:** public `validate_stored_run`; safe tests/reader/publication errors; no extraction schema/cache-key/extractor version bump.

**Interfaces:** Consumes existing `StoredRun`, `WindowRecord`, `Claim`, `DocumentRecord`, `RunRecord`, `read_run`/`write_run`, and current `refused_quotes(run,bundles)`. Produces `validate_stored_run(run: StoredRun) -> StoredRun`, exported from the extraction package without concrete adapters. Check commands: `runner` and `extraction`; red expects a fixed `test_failed`/`collection_failed` plus nonzero exit, green expects all selected tests passing and no new warning.

- [x] **1. Add failing runner sentinel tests, then the runner.** Child output contains invented sentinel text in an exception, warning, parametrized ID and captured stdout. The parent must emit none of it, preserve failure exit, report fixed counts/reasons and hash an unsafe case suffix. Test collection failure and timeout too. The metadata plugin's central rule is:

```python
def safe_test_id(nodeid: str) -> str:
    base, _, case = nodeid.partition("[")
    path, _, name = base.partition("::")
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", path) or not re.fullmatch(
        r"[A-Za-z0-9_:]+", name
    ):
        return "test-" + hashlib.sha256(nodeid.encode()).hexdigest()[:12]
    suffix = "" if not case else "[case-" + hashlib.sha256(case.encode()).hexdigest()[:8] + "]"
    return base + suffix
```

Pass only scalar counts, these IDs and closed reasons across the child boundary; plugin reports no text/detail. Capture collection/plugin exceptions in the parent without dumping them. Verify `runner` green before any other group.

- [x] **2. Observe red extraction tests for the deferred invariant defects.** Add explicit cases for: empty/reversed window span; wrong `w-start-end` ID; malformed `c-windowStart-windowEnd-attempt-candidateIndex`; request/cache-hit counts greater than dispatched attempts; `unreported > requests`; completed/failed window reason contradiction; unknown document/rejection reason; document failed windows greater than windows; duplicate/empty quote links and unit IDs; nested `model_construct`/`model_copy` bypass; booleans/non-strict counters. Preserve replay misses as dispatched attempts: `attempts >= requests + cache_hits`, not equality. Attempts stay bounded to two; a budget-stopped unsent window may have zero attempts.

```python
@pytest.mark.parametrize("change", [
    {"end": 0}, {"window_id": "w-1-10"},
    {"requests": 2}, {"cache_hits": 1}, {"unreported": 2},
], ids=["empty", "wrong-id", "requests", "hits", "unreported"])
def test_window_refuses_impossible_record(change):
    fields = dict(
        doc_id="invented-doc", window_id="w-0-10", start=0, end=10,
        unit_ids=("paragraph-0-10",), attempts=1,
        outcome=WindowOutcome.COMPLETED, reason=None,
        requests=1, cache_hits=0, prompt_tokens=3, completion_tokens=2,
        unreported=0, latency_ms=0, exhausted=False,
    )
    with pytest.raises(ValidationError):
        WindowRecord.model_validate(fields | change)
```

```python
@model_validator(mode="after")
def _window_invariants(self) -> Self:
    if self.start >= self.end or self.window_id != f"w-{self.start}-{self.end}":
        raise ValueError("invalid_window")
    if self.attempts > 2 or self.requests + self.cache_hits > self.attempts:
        raise ValueError("invalid_accounting")
    if self.unreported > self.requests:
        raise ValueError("invalid_accounting")
    completed = self.outcome is WindowOutcome.COMPLETED
    if completed != (self.reason is None):
        raise ValueError("invalid_outcome")
    return self
```

Use strict validated copies before evaluating counts; existing typed enums and fixed reason registry are authoritative. `DocumentRecord`'s actual counter is **`windows_failed`**; it has no reason field, so reject unknown reasons on `WindowRecord`, `Visit` and `RunRecord.rejections_by_reason`, rather than adding a document reason field. Claim ID numeric parts must match its window ID/attempt, and candidate index is nonnegative. Do not introduce text validation against pilot/gold.

- [x] **3. Add relational store tests and the minimal public gate.** Revalidate all nested models from JSON through their real constructors; check unique document IDs, document-qualified quote/claim IDs, `(doc,window)`/visit keys, claim/window/document references, every linked quote, ordered unit visits and per-document/run counts/usage totals/rejection counts. Validate document counters against actual rows, run document/hash mapping against document rows, aggregate windows/failed/quote/claim/candidate/rejection counts, and dispatched request/cache/usage totals. Candidate count equals retained claims plus candidate-scoped rejections, not transport/window rejections. Avoid inventing an attempt ledger the schema doesn't contain. Both `read_run` and `write_run` call `validate_stored_run`; the writer still calls `refused_quotes` against current bundles before publishing. Fixed `malformed_record/storage_corrupt` errors suppress chains; existing refusal repr/str remain reason-and-ID-only. Add missing-schema/file/symlink/path and forged-row sentinel cases without printing offending data.

- [x] **4. Run `runner` and `extraction` green and the scoped Ruff checks.** Re-run the mixed scripted Stage 1 traversal and replay tests to prove valid existing schema-1 records still load unchanged; no frozen output regeneration. Check changed-field dictionary coverage. Record exact safe counts and the absence of model/network dispatch.

- [x] **5. Checkpoint:** spec-conformance then quality approval; commit the future task; close only the extraction-record invariant deferred item if **every** listed invariant and consumer check passes. The arbitrary-error partial-record and concurrency items remain open.

Task 1 checkpoint (2026-10-06): implemented in `04a9db1..7820506`; independent Sol Ultra specification conformance and task quality approved after fix round 1. Guarded runner 10, extraction 199, dictionary 246 passed with all other counts zero; scoped Ruff passed. The extraction invariant backlog entry remains pending current downstream consuming-gate checks in Task 3; its closure is conditional, not omitted. Partial-record and concurrency entries remain open.

### Task 2: Define analytical contracts and a completely invented fixture matrix

**Files:** New analysis records/problems/init/test fixtures; dictionary. **Produces:** schema inventory above, `AnalysisInputs`, `BoundAnalysis`, `AnalysisTables`, `AnalysisRun`/`StoredAnalysisRun`; no I/O/import side effects.

**Interfaces:** Consumes core schema-2 contracts, existing `Codebook`/`CodebookReference`, `PolicyReference`, `SupportSources`, `StoredSupportRun`, `CodingRun`, `DecisionSet`, `AssignmentPolicy` and existing caches. Produces all strict inventory models and these fixture names in `analysis/conftest.py`: `analysis_inputs` (one fully bound invented fixture-policy source/run set); `analysis_policy`; `family_map`; `counting_case` (the independent V10 tables/coverage/book/policy/families); and `analysis_run` once Task 6 exists. `cases.py` owns deterministic constructors, not gold. Check: `records`, plus `test_data_dictionary.py` through the runner's named `dictionary` group, red/green as above.

- [x] **1. Write failing record tests.** Exercise unknown/extra fields, boolean offsets/counters, missing codebook/policy hashes, conflicting event/doc fiscal facts, non-UTC timestamps, duplicate memberships, mixed/stale book, fixture acceptance on research scope, widened rights, empty typed tables and source-bearing `repr/str`. Use invented metadata and `earnings_themes.synthetic`/existing coding fixture patterns. Do not import test helpers into runtime modules.

```python
def test_family_map_refuses_duplicate_pair(family_map):
    fields = family_map.model_dump(mode="json")
    fields["memberships"] = [fields["memberships"][0]] * 2
    with pytest.raises(ValidationError):
        ThemeFamilyMap.model_validate_json(json.dumps(fields))
```

```python
class AnalysisPart(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    schema_version: Literal[1] = 1

class AnalysisError(ValueError):
    def __init__(self, reason: str) -> None:
        if reason not in ANALYSIS_REASONS:
            reason = "unexpected_error"
        self.reason = reason
        super().__init__(reason)

@dataclass(frozen=True, repr=False)
class AnalysisInputs:
    sources: SupportSources
    support: StoredSupportRun
    coding: CodingRun
    assignment_policy: AssignmentPolicy | None
    expected: tuple[ExpectedEvent, ...]
    acquisition: tuple[AcquisitionStatus, ...]
    metadata: tuple[DocumentMetadata, ...]
    copies: tuple[CopyAssertion, ...]
    no_theme: tuple[NoThemeDeclaration, ...]
    provenance_hash: str
    raw_verification: tuple[RawCacheVerification, ...]
    raw_caches: RawCacheInputs
    raw_snapshots: tuple[RawSnapshot, ...]
    analysis_policy: AnalysisPolicy
    canonical_snapshots: tuple[CanonicalSnapshot, ...]
    fixture_authorization: FixtureAuthorization | None
```

`ANALYSIS_REASONS` is the closed union of reasons explicitly specified in this plan plus `malformed_record/storage_corrupt/input_changed/mixed_codebook/policy_mismatch/rights_restricted/empty_denominator/copy_processing_conflict/empty_selection/unexpected_error`. Upstream closed statuses/reasons are retained as fields, not reinterpreted by string matching.

Define the table-row models in `records.py` as `Observation`, `QuoteAudit`, `ClaimAudit`, `ClaimEvidence`, `ClassificationAudit`, `DecisionAudit`, `RejectionAudit`, `CoverageRow`, `PrevalenceRow` and `CopyRow`, with exactly the fields/grains in the persisted-table inventory. Existing `AssignmentClaimLink` and pointer-only `NoveltyItem` supply the original link/novelty payloads; analytical schema/FKs are added explicitly in the frames. These names also define the row-model-to-table schema registry; no later task invents an alternative schema.

- [x] **2. Implement strict models and explicit `TABLE_SCHEMAS`.** Use existing canonical JSON/digest, core ID/hash/contracts and Stage 9 CodebookReference/PolicyReference objects; no copied codebook schema. Add complete field validators and foreign-key documentation. Nullable fiscal/time metadata stays null. This event-bound slice requires the frozen event's zero-padded ten-character CIK; missing or conflicting identity refuses publication with a fixed binding reason rather than inventing an identifier or adding an unspecified metadata extension. No schema-global ingestion/core bump.

- [x] **3. Build the following hand fixture as typed in-memory inputs.** Literal IDs below are invented. Use a two-level book `capacity -> capacity_expansion`, plus `demand`; no positive/negative example reader. Fixed date Q1=2025-03-31, Q2=2025-06-30. Per-span repeated text/astral characters are invented in `analysis/cases.py`.

| Event | Acquisition / processing | Assignment/completion evidence | Headline observable / capacity presence |
| --- | --- | --- | --- |
| A-Q1 | parsed, complete | accepted `capacity_expansion`, two claims linked to one quote; second exact disclosure copy | yes / 1, counted once |
| A-Q2 | parsed, complete traversal | valid explicit fixture no-theme declaration, no quotes/targets | yes / 0 |
| B-Q1 | parsed, complete | accepted capacity evidence entirely overlapped by a current mask | yes / 0; evidence remains audit |
| B-Q2 | unavailable | fixed source reason | no / unknown |
| C-Q1 | parsed | assessed target but absent assignment policy, `review/calibration_required` | no / unknown |
| D-Q1 | failed parse | original `parse_failed` and FailureReason | no / unknown |
| E-Q1 | restricted | original `rights_restricted` | no / unknown |
| F-Q1 | parsed, complete classification | valid-unmatched novelty, no explicit no-theme declaration | no / unknown |
| G-Q1 | parsed, complete assessment | rejected targets, no no-theme declaration | no / unknown |
| H-Q1 | parsed, partial processing | separate refused, flagged and incomplete targets/decisions retained | no / unknown |

The mixed policy corpus above is an audit/completion fixture, not one publishable accepted run: use separate explicitly bound coding runs for `policy=null` and fixture-policy cases, then normalized event-level completion rows for the count-only V10 fixture. Publication refuses mixing those policy bindings in one analytical accepted-run selection. This prevents a test shortcut from weakening the real consuming gate.

- [x] **4. Run `records` green; add public-object identity tests and dictionary entries.** Check that no initializer loads concrete adapters or source files.

- [x] **5. Checkpoint:** both task approvals. No acceptance/quality claim follows from invented records.

Task 2 checkpoint (2026-10-06): implemented in `04b3043..af6d59e`; Sol Ultra specification and quality approved after scoped fixes. Records 55 and dictionary 293 passed with all other counts zero; scoped Ruff passed. Public `validate_analysis_tables(tables: AnalysisTables) -> AnalysisTables` reconstructs current frames and enforces full references; complete run containers retain its result. Intermediate tables defer only empty completion references. Task 6 constructs complete runs; Task 8 invokes the full gate before serialization/publication. Exact `records` group registration was the narrow audited runner ownership correction.

### Task 3: Rebind and reverify every current input before analysis

**Files:** `analysis/consume.py`, its tests, analysis exports/dictionary. **Produces:** `reverify_analysis_inputs` with fail-closed current binding; no inference.

**Interfaces:** Consumes Task 1's `validate_stored_run`, Task 2's `AnalysisInputs`/`RawCacheInputs`, existing `reverify_span(document,elements,span)`, `refused_quotes`, `reverify_support_run(stored,sources)` and `reverify_coding_run(stored,sources,support,policy)`. Produces `reverify_analysis_inputs(inputs: AnalysisInputs) -> BoundAnalysis`. Check: `consume`, `extraction`, `dictionary`, red stale-input refusals then green fixed reasons.

- [x] **1. Write red consumption tests using real round-tripped invented upstream runs.** Change one component at a time: canonical text/hash/element, current mask membership or policy, original claim quote link, second linked quote, quote's stored span, selected book/hash/rule, support source/run/config hash, assignment policy/reference/vote, coding assignment/claim links, metadata issuer/period/doc mapping, expected population, and declaration binding. Include zero accepted assignments, zero targets, orphan quotes, two documents both called `q-0-100`, source callback mutation during policy evaluation and a malicious exception with an invented sentinel chain. Every stale input refuses before rows or files are produced; the second originally linked quote cannot disappear just because only one supports acceptance.

```python
def test_changed_canonical_source_refuses(analysis_inputs):
    sources = analysis_inputs.sources
    first, *rest = sources.bundles
    document = first.document.model_copy(update={
        "canonical_text": first.document.canonical_text + "!",
    })
    changed = replace(analysis_inputs, sources=replace(
        sources, bundles=(replace(first, document=document), *rest),
    ))
    with pytest.raises(AnalysisError, match="^input_changed$"):
        reverify_analysis_inputs(changed)
```

- [x] **2. Implement the gate in this order, checking strict types/identities first.** Use `validate_stored_run`; validate every bundle's document/elements/masks; compare the full extraction document/hash inventory to selected current bundles and metadata; call `refused_quotes` for **all** stored quotes; recompute mask IDs and mask-manifest/policy binding, including empty masks. Validate complete original claim–quote links before any filter. Verify approved book metadata/hash via existing pure codebook hash/rule checks without resolving examples. Verify source provenance and every event/doc/acquisition/current metadata binding. Then call the shipped support and coding consuming gates, and repeat source/quote/mask binding after policy callbacks.

```python
def reverify_analysis_inputs(inputs: AnalysisInputs) -> BoundAnalysis:
    try:
        checked = strict_analysis_inputs(inputs)
        extraction = validate_stored_run(checked.sources.stored_run)
        verify_current_inventory(checked, extraction)
        refusals = refused_quotes(extraction, checked.sources.bundles)
        if refusals:
            raise AnalysisError("input_changed")
        verify_original_links_and_masks(checked, extraction)
        reverify_support_run(checked.support, checked.sources)
        decisions = reverify_coding_run(
            checked.coding, checked.sources, checked.support,
            checked.assignment_policy,
        )
        verify_current_inventory(checked, extraction)
        verify_original_links_and_masks(checked, extraction)
        return bind_checked_analysis(checked, decisions)
    except AnalysisError:
        raise
    except Exception:
        raise AnalysisError("input_changed") from None
```

The four helper names above live in `consume.py` and own exactly the inventory/link/mask/strict-binding checks in this step. `bind_checked_analysis` computes canonical content hashes and retains checked references, not cached “valid” booleans. Reject mismatched/missing policy rather than substituting a fixture/default; fixture-only selectors cannot operate on pilot metadata. Reverify refused/flagged/incomplete original evidence insofar as it exists; preserve the original refusal outcome when no valid span exists, never fabricate a quote for it.

- [x] **3. Prove raw provenance limits explicitly.** Supplied support/coding cache refs pass their public `artifact_hash` methods and expected hashes using the actual `RawCacheInputs`; missing cache means `not_supplied`, not verified. Never trust a caller-supplied `verified` label without that byte check. Extraction schema 1 does not publish external raw bindings; report `not_bound` even when the current replay checked its request-cache entries, and describe those two claims separately. Do not invent a raw hash from a reference string or add an unbound ledger. Tampered supplied bytes fail fixed `storage_corrupt`. Raw artifacts are not copied to an exported analytical run.

- [x] **4. Run `consume` and `extraction` green, scoped Ruff and safe-output cases.** Assert no callbacks besides the explicitly supplied deterministic policy and no network/model calls.

- [x] **5. Checkpoint:** both approvals before Task 4. Every subsequent aggregate/export calls this gate again at its boundary.

Task 3 checkpoint (2026-10-06): implemented in `de3fae7..38bd613`; Sol Ultra specification and quality approved after one diagnostics fix. Consume 93, records 59, extraction 199, dictionary 296 passed with all other counts zero; required scoped Ruff passed. C1/C2 current byte/projection bindings and caller-reference rechecks are implemented. Public `analysis_provenance_hash` supplies the normative C2 digest for explicit fixture/application seeders. Only the extraction-record invariant deferred item closes with the prior Task 1 approvals plus current consumer verification; partial-record/concurrency remain open.

### Task 4: Add processing-state schema 2 without changing frozen acquisition

**Files:** Ingestion state/state-table and compatibility tests; dictionary. **Produces:** `ProcessingTransition`, `StateRecord`, `write_processing_run`; mixed-version readers/current states. **Compatibility decision:** retain schema-1 model/schema/writer semantics and bytes; add a second table schema and explicit dispatch.

**Interfaces:** Consumes unchanged legacy `StateTransition`, `SCHEMA`, `state_frame`, `write_run`, `in_order/check_histories/current_states` and `write_new(path,bytes)`. Produces schema-2 `ProcessingTransition`, `StateRecord`, `PROCESSING_SCHEMA`, `write_processing_run(directory,transitions) -> Path` and mixed-schema `read_runs(directory) -> list[StateRecord]`; no other transition graph changes. Check: `states`, `dictionary`; red schema-2 failure rejection before implementation, green old/new compatibility.

- [x] **1. Write red compatibility tests.** Schema-1 acquisition round-trips unchanged; legacy `parsed -> failed` remains refused. Schema-2 allows `parsed -> failed` with `missing_reason="processing_failed"`, fixed `processing_reason`, no parse `failure_reason`; completed/partial/no-theme have appropriate closed completion metadata. Test mixed histories, wrong pilot/doc/event, duplicate position, malformed schema/version, rejected terminal replay, state-data forgery, and all-null new columns. Read `tests/fixtures/events/acquisition.json` through its existing fixture loader; do not run an acquisition over pilot artifacts.

```python
class ProcessingTransition(StateTransition):
    schema_version: Literal[2] = 2
    processing_run_id: IdPart
    processing_run_hash: Sha256Hex
    completion_hash: Sha256Hex
    processing_reason: ProcessingReason | None = None
    missing_reason: ProcessingMissingReason | None = None

    @model_validator(mode="after")
    def _state(self) -> Self:
        validate_processing_transition(self)
        return self
```

Override the inherited `_state` validator by the **same name** and test that schema-1 validation remains unchanged. `validate_processing_transition` requires a release document, `from_state=parsed`, acquired source/doc fields copied exactly from its current predecessor, UTC timestamps, no new acquisition attempts/override/corpus error, and `to_state` only partial/completed/completed-no-theme/failed. Failure requires `processing_failed` and a closed processing reason and **no** canonical parse FailureReason. Non-failure missing/completion reasons follow the table above. `completion_hash` for an abort binds `WorkflowFailure`, explicitly tagged as failure evidence; never counterfeit a completion record.

`ProcessingMissingReason` is a closed string enum with `processing_failed`, `extraction_partial`, `classification_incomplete`, `assessment_refused`, `assessment_incomplete`, `assessment_flagged`, `calibration_required`, `policy_review`, `valid_unmatched`, `no_theme_unconfirmed`, `no_eligible_units`, and `copy_processing_conflict`. `ProcessingReason` uses these plus existing closed extraction/support/coding failure values and `explicit_no_theme/unexpected_error/storage_corrupt/input_changed`; no free string or canonical parse enum is accepted. Completed rows have null missing reason; completed-no-theme records `processing_reason=explicit_no_theme`; partial rows require their missing/processing reason; failed rows require processing_failed plus the closed cause. Preserve the original acquisition override ID/corpus-error provenance when present; set **new** attempts empty, never discard the predecessor's retained override history. Reject a new override in a processing transition.

- [x] **2. Implement an explicit schema-2 Polars table.** Keep `SCHEMA` and `state_frame`/`write_run` unchanged for schema 1. `PROCESSING_SCHEMA` uses the legacy columns with schema version 2 plus the four processing columns, their declared dtypes, and permits only processing rows. `write_processing_run` writes one run atomically with `write_new`; preflight the combined history before writing. `read_runs` selects the appropriate exact schema then validates the correct model, refuses unknown schemas and suppresses arbitrary source-bearing diagnostics at the new application boundary. Annotate `in_order/check_histories/current_states` with `StateRecord`; their ordering remains earliest UTC run time, run ID, sequence. Do not add transcript slots or reopen terminal states.

- [x] **3. Define retry semantics.** Reusing the same processing run ID/hash with identical file bytes is idempotent. An existing run with different bytes refuses. A terminal/partial document from another processing run refuses as `state_not_processable`; Stage 10 does not silently reopen it to rerun a different policy. New analysis of already completed stored runs may publish a separate analytical run without writing a new state transition. Future reprocessing/recovery policy remains an explicit Stage 11/15 decision.

- [x] **4. Run `states` green and scoped Ruff.** Verify synthetic and committed universe/event/pilot metadata loaders remain unchanged using the audited metadata-only nodes; no source wording/gold/local store reader. Record before/after hashes of immutable **permitted** fixture artifacts in tests. Full-root/Stage 6 compatibility checks remain user-only.

- [x] **5. Checkpoint:** both approvals; document migration and old/new producer-consumer coverage. No core/ingestion global schema bump or acquisition artifact rewrite.

Task 4 checkpoint (2026-10-06): implemented in `947f35f..04be9a1`; independent Sol Ultra specification and quality approved after one consumer-compatibility fix round. Guarded states 102 and dictionary 300 passed with all other counts zero; scoped Ruff passed. Schema-1 model/table/writer definitions and synthetic acquisition bytes remain unchanged. Schema-2 transitions use explicit mixed readers and immutable retries. Narrow acquisition/coverage consumer fixes prevent reopening processing terminals and retain canonical availability after processing failure, without treating it as theme absence. Actual completion/failure artifact validation remains the Task 9 application gate.

### Task 5: Project R11.1 rows while retaining all original evidence and outcomes

**Files:** `analysis/rows.py`, tests, schemas/dictionary. **Produces:** typed observations and full audit/link tables.

**Interfaces:** Consumes checked Task 3 `BoundAnalysis`, Stage 9 `Assignment`/`AssignmentClaimLink` and Task 2 row schemas. Produces `build_observations(bound: BoundAnalysis) -> AnalysisTables`, with original and audit frames plus copies; completion/coverage/prevalence/evidence frames initially keep their declared empty schema for later stages. Check: `rows`, `consume`, `dictionary`.

- [x] **1. Red tests establish row grain and link cardinality.** One verified quote accepted for two themes gives two observation rows with the same document-qualified quote; two claims supporting the same quote/theme yield one observation and two assignment-claim links. Two documents with equal local quote IDs remain distinct. All original claim links survive even contextual/irrelevant/unselected ones. Zero-assignment runs retain quote/claim/rejection/outcome tables. Release rows all have `not_applicable`; sentiment/topic/cluster/attributes never populate `theme_id`. Masked assignments remain audit with `headline_eligible=false`.

```python
def test_projection_keeps_every_original_link(analysis_inputs):
    tables = build_observations(reverify_analysis_inputs(analysis_inputs))
    actual = set(tables.frames["claim_evidence"].select(
        "doc_id", "claim_id", "quote_id",
    ).iter_rows())
    expected = {
        (claim.doc_id, claim.claim_id, qid)
        for claim in analysis_inputs.sources.stored_run.claims
        for qid in claim.quote_ids
    }
    assert actual == expected
    assert tables.frames["observations"]["speaker_role"].unique().to_list() == [
        "not_applicable",
    ]
```

```python
def observation_key(row: Observation) -> tuple:
    return (
        row.entity_id, row.period_end, row.doc_type, row.speaker_role,
        row.theme_id, row.doc_id, row.quote_id,
        row.codebook_id, row.codebook_version,
    )

def original_links(run: StoredRun) -> tuple[ClaimEvidence, ...]:
    return tuple(
        ClaimEvidence(doc_id=claim.doc_id, claim_id=claim.claim_id, quote_id=qid)
        for claim in run.claims for qid in claim.quote_ids
    )
```

- [x] **2. Implement exact projection.** Build quote lookup by `(span.doc_id,quote_id)`, source metadata by doc ID, and event metadata by event ID. Materialize text only from canonical `[start:end]`; recomputed mask overlap controls headline eligibility. Keep assignment policy/source/support/codebook hashes and every link. Copy refusal reason/IDs only; never `str(rejection)` from a core rejection with detail or whole Pydantic rows. Use explicit Polars schemas for all tables, including empty output.

- [x] **3. Implement disclosure groups and audit conflicts.** Exact-hash copies can group only within one event/issuer/period/type; reviewed assertions require their metadata/hash binding. Do not remap original doc/quote IDs or rewrite source assignments. Count group/span occurrences separately from source-copy row counts. Two equal strings at different offsets remain distinct. Detect incompatible copy outcomes before prevalence; retain all rows and flag `copy_processing_conflict`. A copied disclosure is never independent corroboration.

- [x] **4. Run `rows` and `consume` green, scoped Ruff.** Test deliberate mixed-version assignment/source inputs refuse rather than concatenate.

- [x] **5. Checkpoint:** both approvals; immutable upstream row hashes unchanged.

Task 5 checkpoint (2026-10-06): implemented in `6c1c541..9be7800`; fresh Sol Ultra specification conformance and code quality approved, with no findings. Guarded rows 24, consume 93, records 61 and dictionary 301 passed with all other counts zero; scoped Ruff passed. Public `build_observations` repeats current gates and preserves original/audit links and source IDs, exact canonical slices, masked evidence and copy conflict status. The documented nullable refusal window and derived window/attempt pointers preserve valid upstream cases; intermediate completion/count/evidence frames remain typed and empty.

### Task 6: Derive completion, expected coverage and hand-computed prevalence

**Files:** `analysis/completion.py`, `coverage.py`, `prevalence.py` and tests; dictionary. **Produces:** complete-observation eligibility and R11.2–R11.6 counts; no calibration.

**Interfaces:** Consumes `BoundAnalysis`, `AnalysisTables`, `AnalysisPolicy`, `ThemeFamilyMap`, `Codebook` and the shipped structural `plan_windows`. Produces `document_completions`, `build_coverage`, `prevalence` and `build_analysis` with the exact public signatures above. `build_analysis` repeats the current gate, then fills the fourteen typed frames and manifest content bindings. Check: `coverage`, `rows`, `states`, `dictionary`; red expected count/empty-proof failure, then exact green hand results.

- [x] **1. Red completion tests cover every mapping row.** Check complete/partial/failed traversal, replay misses/exhaustion, no eligible units, missing classification, refused/flagged/incomplete support, review/absent policy, rejected-all, valid-unmatched, masked-only accepted and explicit no-theme. Empty accepted/quote/target tables without declaration **never** become no-theme. A mismatched/stale/duplicate declaration refuses. A declaration with unresolved candidate rejection or missing unit/target is invalid. Fixture declarations cannot authorize research/pilot absence.

- [x] **2. Implement completeness from expected work, not outputs.** Recompute expected units/windows using the shipped structural planner and extraction configuration; compare exact window/unit identities and visit outcomes. Compare requested claim order to all retained claims, classification inventory, proposed targets, four required assessment trial slots/per-quote/joint contributions and final decisions through shipped gates. Retain legitimate empty target sets only when no target was proposed; no target count itself supplies absence. Derive `DocumentCompletion` using the precedence/mapping above.

- [x] **3. Red coverage/prevalence tests use the ten-event hand matrix.** Expected releases 10, parsed/available 7, complete observable 3 (A-Q1/A-Q2/B-Q1), excluded 7 with their precise reasons; expected transcripts 10, available/observable 0 and not-in-scope 10. No absent transcript is a release failure or negative transcript theme. Complete masked-only B remains observed but contributes no headline capacity evidence.

| View / unit | Numerator | Denominator | Rate / restriction |
| --- | --- | --- | --- |
| Q1 direct `capacity_expansion`, issuer-period | 1 | 2 | 1/2 |
| Q1 parent `capacity`, issuer-period | 1 | 2 | 1/2; child rolled up once |
| Q2 parent `capacity`, issuer-period | 0 | 1 | 0; A-Q2 explicit no-theme |
| Window distinct-issuer capacity presence | 1 | 2 | 1/2; any complete period, B-Q2 missing |
| Descriptive window firm-quarter capacity | 1 | 3 | 1/3; explicitly not equal-issuer window mean |
| Requested equal-issuer mean | 0.5 (sum of 1/2 and 0/1) | 2 issuers | 1/4 |
| Transcript capacity, issuer-period | 0 | 0 | null / empty_denominator; no observed transcript |

Assign A-Q1's child to families `operations` and `expansion`; both Q1 family rows are 1/2. Add an extra direct-parent assignment and many duplicate quotes/claims/copies in a mutation fixture: parent/family/issuer numerators remain one for A. Unknown family theme/version and hierarchy cycles/orphans refuse. Unknown fiscal quarter does not become publication calendar quarter; tests group by supported period end.

```python
def test_v10_parent_period_counts(counting_case):
    frame = prevalence(
        counting_case.tables, counting_case.coverage, counting_case.book,
        counting_case.policy, counting_case.families,
    ).filter(
        (pl.col("view_kind") == "parent") & (pl.col("view_id") == "capacity")
        & (pl.col("unit") == "issuer_period")
    ).sort("period_end")
    assert frame.select("numerator", "denominator").rows() == [(1, 2), (0, 1)]
    assert frame["rate"].to_list() == [0.5, 0.0]
```

```python
def counted_units(frame: pl.DataFrame, ids: list[str]) -> pl.DataFrame:
    return frame.select(ids).unique().sort(ids)

# Count only after coverage has supplied eligible complete observation units.
units = counted_units(coverage.filter(pl.col("observable")), ["entity_id", "period_end"])
positive = counted_units(
    observations.filter(pl.col("headline_eligible")).join(
        units, on=["entity_id", "period_end"], how="inner", validate="m:1"
    ),
    ["entity_id", "period_end", "theme_id"],
)
```

The production function also partitions by document type/role/book/policy/population/view, validates all join cardinalities, creates explicit zero numerator rows for selected themes with observed units, and uses null rate for zero denominator. Do not let a nullable availability flag coerce to true/false silently. Expected/available/observable counts come from coverage, not quote rows.

- [x] **4. Add the frozen synthetic acquisition V10 leg.** Load its 27 selected expected events and original state run (24 parsed, 2 unavailable, 1 failed). Attach invented complete fixture processing to all 24 parsed slots: release observation denominator 24, expected 27, availability 24/27; with one capacity presence per parsed slot, firm-quarter numerator 24/denominator 24. Missing transcript slots remain 27/27. Add a **separate newly invented manifest** with a restricted event for its restricted/empty-denominator case; never modify the committed synthetic event/pilot/acquisition files. The ten-event matrix above supplies mixed no-theme/review/negative/partial counts and equal-issuer arithmetic independently.

- [x] **5. Run `coverage`, `rows`, `states` green; record V10 hand expectations/results and mask/copy/equal-weight evidence.** There is no pilot prevalence, production quality gate, agreement or scorer calibration result.

- [x] **6. Checkpoint:** both approvals. Parent/family rows are analysis-time views; original v0 and assignments remain unchanged.

Task 6 checkpoint (2026-10-06): implemented in `518df96..84e36b2`; independent Sol Ultra specification conformance and code quality approved after one public-policy fix round. Initial required checks passed: coverage 52, records 69, consume 98, rows 24, states 102, dictionary 302, all other counters zero; fix-round coverage 58 and dictionary 302 passed with scoped Ruff. Expected-work completion proof, explicit declaration handling, masks/copy conflicts, ten-event equal-issuer arithmetic and frozen 27-event acquisition denominator are verified offline. The approved selected-universe extension binds the public operative hash into current provenance and the run manifest; original artifact validation remains Task 9. Public prevalence binds every observable completion, including declared negatives, to one assignment-policy reference and matching accepted observations. No pilot prevalence or calibration claim follows.

### Task 7: Build escaped immutable canonical evidence views and durable links

**Files:** Application evidence/browser-boundary modules and tests; analytical evidence-reference models/dictionary. **Produces:** no-browser static views and honest source links/rights statuses.

**Interfaces:** Consumes `BoundAnalysis` and `reverify_analysis_inputs`, `reverify_span(document,elements,span)`, `make_locator(document,span)`, existing `ArtifactRef`/`RightsStatus` and public `BrowserRenderer.capture`. Produces `make_evidence_view` and `capture_evidence_view` with the public signatures above, plus content-hashed `EvidenceView` bytes/references. Check: `evidence`, `consume`, `dictionary`, with literal safe expectation statuses and no browser.

- [x] **1. Write red view/link tests on invented text.** Include `<script>`, HTML attributes/ampersands/quotes, literal dash/comma, newline, decomposed Unicode, emoji before the quote, equal repeated sentences at two offsets, overlapping quotations in separate views and a long page. The second occurrence's mark and locator must use its actual span. Altered canonical/hash/offset/mask/current policy refuses before HTML. No quote verification reads rendered output. Static HTML contains no script, external CSS/font/image/link preload or unsafe href scheme.

```python
def test_mark_is_exact_occurrence_and_escaped():
    text = "😀 first <script> then second <script>"
    start = text.rindex("<script>")
    rendered = marked_text(text, start, start + len("<script>"), "p-invented")
    assert '<mark id="p-invented">&lt;script&gt;</mark>' in rendered
    assert rendered.index("<mark") > rendered.index("&lt;script&gt;")
    assert "<script>" not in rendered
    assert len(text[:start].encode("utf-16-le")) // 2 == start + 1
```

```python
def marked_text(text: str, start: int, end: int, anchor: str) -> str:
    return (
        html.escape(text[:start])
        + '<mark id="' + html.escape(anchor, quote=True) + '">'
        + html.escape(text[start:end]) + '</mark>'
        + html.escape(text[end:])
    )

def directive_term(text: str) -> str:
    return urllib.parse.quote(text, safe="").replace("-", "%2D")

def text_directive(locator: SpanLocator) -> str:
    parts = []
    if locator.prefix:
        parts.append(directive_term(locator.prefix) + "-,")
    parts.append(directive_term(locator.exact))
    if locator.suffix:
        parts.append(",-" + directive_term(locator.suffix))
    return "#:~:text=" + "".join(parts)
```

The shipped `SpanLocator` text field is **`exact`**, with `prefix` and `suffix`; use it unchanged. Preserve the source URL's legitimate query but replace its existing fragment; validate HTTP(S) and user-info/control characters without printing refused values. The snapshot's stable `#p-...` anchor uses the canonical span independently of native text-fragment support.

- [x] **2. Implement view preparation with current gates.** Select a `(doc_id,quote_id)` from checked evidence, call current exact verification and `make_locator(document, TextSpan(...))`, and derive anchor/evidence ID from doc/hash/start/end/verifier. Build UTF-8 standalone HTML with `white-space:pre-wrap`, visible `<mark>` style and escaped metadata. Raw source reference/hash and canonical text/artifact hash remain separate. Hash actual HTML bytes; publish under content hash only. No HTML parser, source text replacement, whitespace normalization, OCR or browser Range enters the verifier.

- [x] **3. Implement explicit local/export rights decisions.** Test redistributable, permitted local-only retention, restricted/no-retention, no raw bytes and local-only screenshots. Export strips quote text, interpretation text derived from restricted sources, text-fragment URL/context and local view/raw artifact references when forbidden, but retains permitted IDs/hashes/offsets/plain source URL and `withheld/rights_restricted`. A hash-only raw reference without bytes cannot be called an immutable saved snapshot: mark `raw_snapshot_missing` and preserve the canonical fallback where allowed. Missing required retainable raw snapshot makes cited publication incomplete with a fixed reason; no silent success.

- [x] **4. Keep capture optional and public.** `browser_evidence.py` depends on the public ingestion `BrowserRenderer`/`CapturePolicy`, not Selenium internals. Pass the exact saved canonical HTML bytes and source ID to `capture`; compare the capture's raw hash to those HTML bytes solely for provenance. Record completed/partial/failed/unavailable/not-requested separately. Compute expected UTF-16 endpoints here only, retaining CP endpoints beside them. Catch arbitrary adapter errors as fixed failed observation with suppressed chain; never print `RenderedCapture.detail`, layout text or screenshots. The default view path imports no concrete browser implementation and needs no capture/network.

- [x] **5. Run `evidence`, `consume` green, scoped Ruff.** Prove the report/view can open from a local filesystem without Selenium or browser binaries; tests inspect invented static HTML bytes, not browser-derived evidence exactness.

- [x] **6. Checkpoint:** both approvals. V5 actual highlighting remains a separate Task 10 observed gate.

> Task 7 verified checkpoint (2026-10-07): implementation `fff592e..693b5c3`; fresh Ultra review at `d73089d` and fresh scoped Ultra re-review at `693b5c3`, specification and quality approved, no open findings. Final covering guarded checks: evidence 81, records 82, dictionary 304, consume 98 (565 passed; all other counters zero); affected Ruff/checkformat passed. Views/capture references are prepared only; durable publication and observed V5 remain later gates.

### Task 8: Publish immutable analytical Parquet and a cited rights-aware report

**Files:** Analysis store, application report and tests; schema exports/dictionary. **Produces:** immutable analytical `run.json`/fourteen Parquet tables, and a separately published audience-specific report bundle with evidence artifacts and `report.json`.

**Interfaces:** Consumes `build_analysis`, current inputs/policy/families, typed frames and `EvidenceViewReference`; produces `write_analysis_run/read_analysis_run/reverify_analysis_run` and `write_theme_report` at the exact public signatures. Analytical storage validates evidence bindings, not absent external snapshot bytes; the report writer receives actual `EvidenceView` bytes, re-renders/rechecks the current canonical span/template, verifies each provided artifact hash and includes permitted bytes before claiming a saved fallback. Check: `export`, `evidence`, `consume`, `dictionary`.

```python
def test_changed_policy_refuses_before_any_publication(
    analysis_inputs, analysis_policy, family_map, tmp_path,
):
    result = build_analysis(analysis_inputs, analysis_policy, family_map)
    changed = replace(analysis_inputs, assignment_policy=None)
    destination = tmp_path / "analysis"
    with pytest.raises(AnalysisError, match="^input_changed$"):
        write_analysis_run(
            destination, result, changed, analysis_policy, family_map, evidence=(),
        )
    assert destination.exists() is False
```

- [x] **1. Red publication tests.** Round-trip all table schemas/rows including empties. Refuse mixed/stale current source/masks/support/book/policy/family/completion/copy bindings, table-byte tampering, unsafe/symlinked manifest filenames, missing evidence snapshot, external-cache hash mismatch and changed policy callback. Existing destination refuses other bytes; failed publication removes only its own temporary sibling. Rights-filtered report exposes no invented forbidden sentinel or raw rationale/rejection detail. A source/cache path cannot enter public manifest or HTML accidentally.

```python
def checked_publication(result, inputs, policy, families):
    current = build_analysis(inputs, policy, families)
    if analytical_content_hash(current) != analytical_content_hash(result):
        raise AnalysisError("input_changed")
    return current

# Publish into a new sibling only after current gates and evidence checks pass.
with new_run_directory(directory) as temporary:
    for name, frame in checked.tables.items():
        require_exact_schema(name, frame)
        frame.write_parquet(temporary / f"{name}.parquet")
    write_manifest_last(temporary, checked, evidence)
```

`new_run_directory` is a small analysis-store helper following existing immutable sibling/rename semantics, with confined file names and cleanup, not a generic transaction framework. Manifest hashes bind actual published bytes; raw-cache verification records retain their honest status. Reader verifies manifest schema, exact table set, byte hashes, declared dtypes, typed rows, row grains, foreign keys and recomputed counts. Structural read is not current verification; export uses `reverify_analysis_run`.

- [x] **2. Implement report data/rendering.** Read counts from the validated analytical tables, never reimplement aggregation in the app. Print population/scope/book/policy, supported period, numerator/denominator/unit, availability and missing-reason counts, masked/copy exclusions, partial/review/unmatched counts and transcript coverage. Each displayed quote comes from the current canonical slice and links its original document-qualified evidence to source and immutable fallback; claimed interpretation is explicitly model-derived. Snapshot/capture withholding, raw-cache not-supplied/not-bound and browser failure are visible limitations, not extraction negatives.

- [x] **3. Produce separate immutable local/export profiles.** Local-only screenshots stay in the local capture store, outside exported artifacts. Analytical publication is `analysis/<run_id>/run.json` plus its tables; report publication is a distinct immutable `reports/<report_id>-<audience>/` bundle with `report.json`, HTML and permitted content-hashed evidence artifacts. ReportManifest binds the already-published analysis manifest hash and all included bytes. Do not add/modify report fields inside a previously published analysis `run.json`, and do not create a circular report/analysis hash. Exported manifests/reports point only to artifacts actually included and permitted. No export follows a local absolute path or symlink. Never overwrite an earlier audience/run. The report is usable offline with static anchors even without native text-fragment support.

- [x] **4. Run `export`, `evidence`, `consume` green and scoped Ruff.** Report safe artifact IDs/hash/counts, not rendered HTML or source content. No accuracy or “configuration passing” statement is allowed before Stage 11 V6.

- [x] **5. Checkpoint:** both approvals; publication is reviewable before any external sharing. This plan adds no automatic publishing or message sending.

Observed Task8 checkpoint (2026-10-07): reviewed implementation e00bc36 plus media-type fix ca8fa25; fresh independent SolUltra original review and fresh scoped re-review approve both specification and quality, no open findings. Final covering GREEN export34/evidence81/consume98/dictionary305/runner11=529passed/allothercounters0; affected Ruff/checkformat/diffcheck pass. Full reports remain ignored under .sdd/15-evidence-linked-theme-extraction. Exact public signatures/schema grains unchanged; actual-byte publication/current reverify and separate ReportManifest implemented. Historical overlap/interruption-output and before-timeout thread-setting deviations remain recorded, not relabeled compliant. Runner now closes interruption as runner_interrupted/exit130; controller explicitly authorizes ephemeral POLARS_MAX_THREADS=2 for later exact guarded runs as a resource ceiling, no timeout/rootcause claim. Task9 original metadata derivation, Task10/user V5, Task11 V8/V10 and Task12/user final gates remain pending; Stage10 is not stamped complete.

### Task 9: Add the first explicit replay extraction command and processing run

**Files:** Application config/workflow/CLI/new tests and `cli.py`; dictionary. **Produces:** `extract run`, new Stage 5 processing-state run and immutable analytical/report output; no live CLI mode.

**Interfaces:** Consumes every approved upstream public function, normalized analytical records, processing writer, public `ProcessLock` and report/evidence boundaries. Produces strict `WorkflowConfig`, `WorkflowRuntime`, `WorkflowResult/WorkflowReceipt/WorkflowFailure`, `run_theme_workflow(config,runtime,*,now) -> WorkflowResult`, and `extract run --config`. `WorkflowError` is a fixed-reason `ValueError` using the exact failure/status/replay reasons defined here; it suppresses arbitrary cause/context at CLI boundaries. Check: `workflow`, `states`, `consume`, `export`, `dictionary`.

The config module also exposes `load_workflow_config(path: Path, *, repo: Path) -> WorkflowConfig`; it reads only that JSON and validates its confined selected paths before source loading. A malformed/unsupported mode is `WorkflowError("malformed_record")`, with no Pydantic/raw JSON output. `test_theme_config.py` owns `invented_replay_config(tmp_path)`, returning a complete fixture config using the inventory's exact fields and literal fixture identities; no production default is inferred.

```python
def test_live_mode_refuses_before_input_loading(tmp_path):
    payload = invented_replay_config(tmp_path)
    payload["mode"] = "live"
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(WorkflowError, match="^malformed_record$"):
        load_workflow_config(path, repo=tmp_path)
    assert (tmp_path / "data" / "runs").exists() is False
```

- [x] **1. Red config/CLI preflight tests.** Require explicit manifests and expected selected IDs, hashes, source metadata, current canonical/mask manifest, book, prompts, identities/lineage, ceilings, cache paths and audience/output. Reject absolute/unconfined artifact references, path traversal/symlink escapes, protected implicit discovery, live/hosted mode, missing actual policy for a calibrated reference, fixture policy on non-fixture population and malformed timestamps/ceilings. Preflight failure creates no file/call/state transition. Help does not inspect an input, install a browser or instantiate a model.

- [x] **2. Implement strict path/config loading and replay façades.** Use the app's established layout/path boundaries but never print raw `runs_refusal`/parser exceptions. All selected input file paths are explicit and checked against their intended root; run IDs are safe components. Load existing frozen universe/event/pilot metadata through public loaders and verify the configured hashes and selection, without altering or reselecting after outcomes. Normalize acquisition/source metadata into Task 2 contracts. Read saved canonical JSON through the public ingestion serializer; verify its manifest/raw/current mask bindings. Scope-validation refuses fixture acceptance on the real pilot, without opening its canonical document.

```python
class ReplayOnlyClassifier:
    def __init__(self, identity: JudgeIdentity) -> None:
        self._identity = identity

    @property
    def identity(self) -> JudgeIdentity:
        return self._identity

    def count_tokens(self, request: CodingRequest) -> int:
        raise WorkflowError("replay_dispatch_forbidden")

    def complete(self, request: CodingRequest) -> ModelReply:
        raise WorkflowError("replay_dispatch_forbidden")
```

Use analogous identity-only façades for extraction, scorer and both judges; their unreachable dispatch/count methods are the fail-closed contract. `CachedAdapter(..., mode=REPLAY)`, `CodingCache(...,"replay")`, `SupportCache(...,"replay")` retain shipped request/policy/runtime identity validation and refuse misses. Tests seed caches with **scripted invented** calls in fixture construction; the CLI never seeds a production cache or calls that scripted builder. Raw-cache bytes stay local. Validate their actual public-reader/hash bindings when supplied.

- [x] **3. Compose public functions sequentially.** In order: frozen metadata/current acquisition; explicit canonical bundles; extraction (`extract_run` or hardened explicit stored `read_run`); `SupportSources`; all-claim `propose_run`; targets exactly from proposals; `assess_run`; read/publish/reverify support; `decide_assignments` and `project_assignments`; build strict `CodingRun` through its shipped manifest fields; `write_coding_run/read_coding_run/reverify_coding_run`; Task 3 gate; Task 6 completion and analysis; Task 7 views/optional public capture; Task 8 analysis/report publication; finally processing state run. Use the actual shipped proposal/support/coding signatures and `ProposalRun`/`CodingRunRecord` types; don't add a competing classifier/support implementation or claim-evidence repair. Stored stages must bind the explicit current inputs and run selections; no “latest run” choice.

- [x] **4. Map and append state without rewriting acquisition.** Acquire the existing public ingestion `ProcessLock` at `<configured events runs root>/.acquire.lock`, the **same lock** used by acquisition, before reading/rechecking history and while appending processing transitions. No new worker/concurrency design. Process only currently `parsed` release slots; leave unavailable/restricted/parse-failed/expected states unchanged and present in coverage. Copy immutable accession/raw/doc/pilot fields from each predecessor into schema-2 rows. `processing_run_id` is the configured workflow ID; `processing_run_hash` binds the published analysis manifest bytes (or WorkflowFailure bytes for an abort); `completion_hash` binds that document's checked completion (or the tagged failure). State receipts separately bind the state-file hash, avoiding a manifest/state hash cycle. Record UTC time/sequence, verify combined history then call `write_processing_run`. Do not fabricate zero transitions into a state file; report `no_state_change` when only consuming stored completed runs.

- [x] **5. Handle failures concretely.** Unexpected extraction/cache/storage exceptions suppress chains, retain any already-published immutable stage/cache artifacts, write a metadata-only `WorkflowFailure`, and append a schema-2 `failed` transition for the affected parsed slot when state ownership/history still matches. No extraction partial record is invented. A changed history/terminal state refuses the append; report `state_not_processable` with failure artifact ID only. Analysis/export refusal never replaces a completed upstream run or falsely establishes no-theme. If analytical publication succeeded and state append failed, keep output as `state_pending` in a separate immutable workflow receipt; retry the identical state/run hash idempotently. Readers never call a pending receipt “fully published processing”. Test this two-artifact failure boundary rather than claiming cross-directory atomicity.

- [x] **6. Register CLI and fixed diagnostics.** `cli.py` only adds `app.add_typer(extract, name="extract")`. CLI emits run ID, closed phase/status/reasons, row/state counts and portable artifact IDs/hashes. No raw source, paths from arbitrary exceptions, `repr(result)`, dataframe, rejection detail or validation error. Test Click/Typer ordinary exits and crashes with sentinel source text; unknown diagnostic identifiers become hash tokens. No callback/exception chain reaches stderr.

- [x] **7. Run `workflow`, `states`, `consume`, `export` green, scoped Ruff.** Socket guard observes zero trips; every façade dispatch/count counter is zero; optional concrete adapters are absent from default imports. Confirm frozen permitted input bytes unchanged, source statuses retained and replay miss visible. Record red/green commands/counts.

- [x] **8. Checkpoint:** both approvals. The command exists; its fixture success is not pilot extraction or production acceptance. The non-AdapterError partial-record design remains deferred because the separate failure receipt suffices.

**Execution checkpoint:** Task 9 complete, inclusive BASE `fbff343cb8773eef74602b39ced7388233059855` through reviewed implementation `8ebc9700dd1a19fbcedd1bf95948e81f06decb48`; original plus fresh scoped Sol Ultra review approve specification and quality. Latest covering groups: workflow 59, records 89, coverage 59, states 103, consume 98, export 34, dictionary 315 (757 passes, all other counters zero); scoped Ruff and diff checks pass. The original orchestration-size Minor remains for final triage. Fixture success does not establish pilot or V5 browser acceptance. Detailed RED/GREEN history, seam dispositions and review evidence remain in the ignored progress ledger.

### Task 10: Verify V5 presentation/fallback and address only capture defects it requires

**Files:** Browser lifecycle boundary/test and V5 files listed in ownership; guarded runner; dictionary/browser handoff additions. **Produces:** metadata-only V5 observations, narrow lifecycle fixes if required by these tests, no new browser engine/automation framework/layout metric.

**Interfaces:** Consumes unchanged public `BrowserRenderer.capture(saved_html,capture_policy,*,source_document_id)`, Task 7 `CaptureObservation`/UTF-16 boundary metadata, shipped `SeleniumRenderer` and preregistration amendment/verify commands. Produces bounded capture outcomes/cleanup and a separately observed V5 protocol; no new renderer signature or highlight-success inference. Agent checks: `browser-unit`, `evidence`, `contracts`, `dictionary`; real `browser-user` is human-only.

The target set is **pinned Chrome for Testing 154.0.8037.57, mac-arm64**. The planning session asked about additional browsers; absent a selected expansion, the shipped target is the complete declared target set. Adding Safari/Firefox later requires separate availability/behavior records; do not claim cross-browser coverage now. Browser binaries/capture stores may live in protected `data/`, so actual browser execution and install-path inspection are **user-only** for these blind sessions. Agents use invented bytes and injected fake renderers in unit tests.

- [x] **1. Write the V5 protocol before running a browser.** `docs/verification/stage10-browser.md` records target/pin/policy, invented test IDs, expected canonical CP/UTF-16 spans/hash/anchor, source-link behavior vocabulary (`highlighted/page_top/not_highlighted/wrong_occurrence/failed/unavailable`), fallback result (`span_visible/failed/withheld`), capture result separately, observer/date, fixed failure reason and local screenshot artifact IDs where permitted. Start observed fields as **pending**, not fabricated passes. A usable canonical fallback is required for every permitted span when native highlighting fails. Rights withholding is explicit and cannot be claimed as rendered fallback success.

- [x] **2. Assess the roadmap's deferred capture defects against the required boundary.** The following are in scope because V5 uses public capture and B5/B8 require bounded failures and cleanup:

| Actual defect | Required behavior / minimal change |
| --- | --- |
| `driver.current_url` outside `_step` leaks a source-bearing WebDriver exception | Wrap this read in the existing bounded `_step`; return fixed failed capture on error |
| Debugger discovery through inherited HTTP proxy can leave local isolation or make capture startup fail | Use a dedicated `urllib.request.build_opener(ProxyHandler({}))` solely for validated loopback debugger discovery; no global opener/environment mutation |
| Failure in `Page.getFrameTree`/`Fetch.enable` leaks the already-open WebSocket | Put post-connection initialization in try/except with socket close before re-raising the existing safe startup failure |

Do not change extraction/canonical text, layout mapping/metrics, capture pin, source JS/network rules or `ISOLATED_1` semantics. Keep Stage 3 fixture capture bytes and reports unchanged. The adapter is frozen: apply its permitted `preregister.py amend` protocol and disclose the exact lifecycle/startup-crash rationale and old/new file hash in a standalone amendment commit; verify the preregistration. The proxy fix belongs to this same explicit startup/isolation amendment, not an unrecorded unrelated edit. If the preregistration's `crash`/`invalid-elements` rule cannot truthfully cover the proposed boundary fix, obtain a concrete amendment disposition before changing the frozen file; do not mislabel it or bypass the freeze. This is the only conditional approval in this task and does not authorize rewriting the frozen comparison. Keep all three in the review package; close the deferred grouped adapter item only when all three are landed/verified under an accepted amendment.

**Execution amendment disposition (2026-10-07):** The user explicitly approved exactly these three disclosed lifecycle repairs after the implementer identified the literal freeze mismatch. Only the unbounded current URL read is an uncaught capture crash; debugger proxy isolation and initialization socket cleanup address caught startup failures and cleanup. This is a narrow exception to the existing fixture-capture crash rule, authorizing the existing `crash` amendment category as an explicitly disclosed broader lifecycle/isolation classification for these three fixes only. No actual fixture/native capture prerequisite is claimed: agent validation uses invented injected doubles. Preserve comparison inputs, mapping/types/metrics, Stage 3 capture bytes/reports and measured results, browser pin and policy semantics. Record old/new adapter hashes and the user-approved exception in the standalone amendment/disclosure; no other frozen-file changes are authorized.

**Review safety clarification (2026-10-07):** Task 10 review reproduced an external redirect using invented in-memory HTTP responses, with zero network calls. The literal `build_opener(ProxyHandler({}))` sample retains urllib's default redirect handler and therefore fails this plan's validated-loopback requirement. Reject every redirect in the dedicated discovery opener before a second request, preserving the global opener/environment and existing bounded startup reason. This completes the already user-approved loopback-isolation repair, not a fourth lifecycle exception or a policy/metric/input change. Record a second standalone amendment with the previous/current adapter hashes and the same explicitly approved broader `crash` classification; retain the first amendment. Final V5 pointer, prepared capture JSON and observations also require temporary-file atomic publication with a no-replace boundary, not direct exclusive/final writes. Use invented interrupted-write and existing-target regressions; no new infrastructure or actual browser is authorized.

- [x] **3. Red fake lifecycle tests, minimal fix, green.** Invoke the existing adapter with injected invented driver/socket/discovery doubles; a failing current URL returns `failed`, a proxy environment never routes debugger discovery to an external proxy, and both initialization failures close the socket. Assert child/process/interceptor cleanup at the current public boundary. Guard exception output. Use only this module for Selenium/websocket imports and retain its optional import isolation. No actual browser or protected install directory is inspected by an agent.

The three concrete replacements retain the existing watchdog/reason vocabulary:

```python
current_url = _step(
    watchdog, CaptureReason.DOCUMENT_LOAD_FAILURE, lambda: driver.current_url,
)
if current_url.partition("#")[0] != url:
    raise _Failure(CaptureReason.DOCUMENT_LOAD_FAILURE,
                   "the browser did not stay on the saved file")

# _NoRedirects refuses every redirect before a second HTTP operation.
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}), _NoRedirects(),
)
with opener.open(f"http://{debugger_address}/json", timeout=10) as reply:
    targets = json.load(reply)

try:
    self._main_frame = self._call("Page.getFrameTree", {})["frameTree"]["frame"]["id"]
    self._call("Fetch.enable", {
        "patterns": [{"urlPattern": "*", "requestStage": "Request"}],
    })
    self._socket.settimeout(0.2)
except BaseException:
    with contextlib.suppress(Exception):
        self._socket.close()
    raise
```

Validate discovery/WebSocket hosts and ports as loopback before opening them; do not print refused URLs. Run fake tests without the optional SDK by loading the adapter in an isolated child with minimal Selenium/websocket module doubles supplied by the test, restoring them at child exit; test code imports no real browser at collection. These are SDK interface doubles, not another runtime automation implementation. An installed SDK may run the same injected tests without starting a process. The browser-user test covers the real adapter separately.

After the fixed adapter commit, the future recorded amendment command is:

```bash
uv run --locked --offline --no-sync --all-packages python expirements/parser-fidelity/preregister.py amend packages/earnings-ingestion/src/earnings_ingestion/browser/selenium_capture.py --reason crash --note "Stage 10: user-approved exception for three lifecycle/isolation repairs under the existing crash category; invented fake validation only, no actual fixture/native observation; comparison inputs and metrics unchanged."
uv run --locked --offline --no-sync --all-packages python expirements/parser-fidelity/preregister.py verify
```

Use that reason only after the truthful amendment disposition in Step 2. Disclose the change/post-hoc amendment in `docs/verification/layout-1.md` as the frozen protocol requires, preserving its old measured numbers and fixtures. Do not merely update a stored hash without the amendment record.

- [x] **4. Keep unrelated deferred work outside this task.** No `<br>`/table-cell canonicalization change: the evidence view displays canonical narrative, not an independent cell-fidelity comparison, so a new `walker-2` is unnecessary. No committed capture regeneration/path-placeholder repair, screenshot regeneration script change, installer assert/UTC bundle change or generic `browser setup` cleanup. The old setup traceback item is not needed by the new no-install replay command; its trigger/remaining work stays recorded, even though the CLI already has other commands. If a real V5 user failure triggers a necessary extra fix, state the exact requirement and revise scope before implementation.

- [x] **5. Add fake V5 and user-only real tests.** Fake tests cover each capture and link/fallback status without claiming native behavior. `tests/integration/test_stage10_browser.py` is marked `browser`, builds only invented canonical pages, calls `capture_evidence_view` through the public renderer, verifies provenance/boundary metadata and local screenshot rights/cleanup, and records unavailable/failed explicitly. A successful capture does **not** automatically mark native source-link highlighting successful. Supply an invented static index with unique/repeated/astral/long-page/drift/no-text-fragment cases; the user opens its generated passage links in the declared target with network disabled and reports each behavior/fallback result by ID. The expected fallback is visibly highlighted at the correct occurrence through a static anchor, including when the source link drifts to page-top. No pilot/live-source browsing is part of V5.

```bash
# USER ONLY; guarded output, invented browser cases, no browser setup/download.
uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py browser-user --user-only
```

`browser-user` collects only `tests/integration/test_stage10_browser.py`, with `-m browser`; it does not sync the extra or install binaries. If the optional dependency/binary/platform is missing, report `unavailable` with fixed reason and canonical fallback results; a skipped/failed native check is not a passing native check. Record actual observer/environment/outcomes in V5 before completion. If no target is available, explicitly record the limitation and require a completion disposition; do not claim tested highlight support.

The manual index's “saved source” passage links target the content-hashed **invented saved source HTML**, with the same text directive, separately from the canonical fallback anchor and external source URL. Record `tested_transport="local_file"` and the actual source-artifact hash beside each observation; local-file native behavior is not evidence that an external HTTPS page highlighted. Remote/production HTTPS behavior remains explicitly unverified in Stage 10. No server, external fetch or second browser driver is introduced to hide a local-file limitation. If that transport cannot exercise native highlighting, record the native failure/unavailability and the independent correct fallback; obtain the explicit V5 completion disposition rather than fabricating a highlighted result.

- [x] **6. Run `browser-unit`, `evidence`, `contracts` green and applicable preregistration verification; collect only user-supplied safe V5 counts/IDs/statuses.** Request no screenshot/source/traceback paste. Optional screenshots stay local and are not opened by blind agents. The canonical-view check must pass independently of browser availability.

- [x] **7. Checkpoint:** both approvals. V5's observed record must distinguish pending, native success/failure/unavailability, capture and fallback. No parser-fidelity remeasurement or additional browser ownership is implied.

**Task 10 implementation checkpoint (2026-10-07):** Specification and code quality approved at `7c7f9434c66eadf7424f89d62c56b18f0c4c4405`, incorporating the original review and scoped fix review. All seven implementation checkpoints are complete. This records programmatic/fake implementation completion only: actual V5 native/capture/manual fallback observations, protected-artifact equality and final user-only gates remain pending. Final browser-unit 69 passed; covering evidence 94, current contracts subset 516, dictionary 315 and runner 14 passed, all other counters zero; Ruff and the two-transition preregistration verification passed. Original Minor M1 records protocol writing after fake checks/adapter editing, before any actual browser. No Stage 10 completion stamp is authorized by this checkpoint.

### Task 11: Prove V8 end to end and final scoped blind contracts

**Files:** New shared invented fixtures/integration tests/public/import/data-dictionary tests and guarded runner. **Produces:** actual fixture V8/V10 results and no-protected-reader evidence.

**Interfaces:** Consumes the real replay CLI and all public readers/current gates, Task 6 hand matrix, Task 7 view/report artifacts and fixture constructors; produces `stage10_cases.py`'s `vertical_case` fixture helper with `invoke_replay_cli` and metadata-only `safe_summary`. Check: `vertical`, `coverage`, `contracts`, `upstream`, `stage10`, `dictionary`, scoped Ruff; red must fail the V8/V10 behavior before completing integration, green proves fixture machinery only.

- [ ] **1. Build permitted fixture files without source/gold copying.** `scenario.json` contains the ten invented event/status/declaration cases; `family-map-v1.json` contains the invented capacity-child overlapping memberships; `replay-config.json` is a portable fixture-scope template with exact relative roots and fixture identities/ceilings, filled into a temporary mini-repository by `stage10_cases.py` (no unknown path placeholders are accepted by the loader). Invented raw HTML and scripted raw cache replies are generated in that test-only module. Reuse the explicitly permitted synthetic acquisition fixture/public saved-response/canonicalization path; preserve every committed fixture byte. Do not regenerate Stage 1/browser gold or freeze output into gold.

Cache seeding order is binding: (1) seed extraction raw entries with a scripted adapter, discard that live-accounting result, then make the **replay** extraction record with the fixed fixture IDs/clock/software; (2) seed classifier raw entries against that replay source, discard live-accounting proposals, then produce replay proposals; (3) seed scorer/judge raw entries against those exact replay targets/sources, then produce replay support; (4) bind the fixture AssignmentPolicy reference to those replay classifier/support configuration hashes. The CLI uses those identical identities/prompts/ceilings/source provenance/clock/software. Do not assume a cache seeded against a different live/source-run hash will replay successfully; existing complete-request bindings intentionally refuse that mismatch. No fixture no-theme finding is inferred from these outputs: its finding/actor is predetermined by `scenario.json`, and only its reference hashes are filled from the selected fixtures.

- [ ] **2. Red V8 test starts at saved raw bytes.** Build the synthetic cohort/event/pilot from permitted metadata or load its frozen fixtures; replay acquisition using saved responses with a refusing network stub, canonicalize one declared parsed synthetic release, generate scripted pointer replies/coding/support cache entries with invented claims/policies, then invoke the real replay CLI over a temporary miniature repository. Read its new processing run, typed analytical Parquet, evidence metadata and cited report through public readers and repeat current consuming gates. Assert exact-span rate is defined only when quotes exist, row grains, one quote/two themes, all claim links, CP/highlight occurrence, immutable input/run hashes, fixture policy scope and no transcript claim. No reader opens real `data/`.

```python
def test_v8_raw_fixture_to_cited_report(vertical_case, no_network):
    result = vertical_case.invoke_replay_cli()
    assert result.exit_code == 0
    summary = vertical_case.safe_summary()
    assert summary["scope"] == "fixture"
    assert summary["processing_schema"] == 2
    assert summary["observation_grain_unique"] is True
    assert summary["all_original_links_preserved"] is True
    assert summary["exact_spans_reverified"] is True
    assert summary["source_and_snapshot_citations"] is True
    assert summary["immutable_inputs_unchanged"] is True
    assert summary["dispatch_calls"] == 0
    assert no_network == []
```

These helper outputs are booleans/counts/hashes only; assert no whole result/report/canonical object whose failure repr could print source. Independently test full replay with inner transports raising if called, partial replay misses, unexpected extraction abort, publication/state-pending failure/retry, rights withholding and absent browser. Don't claim deterministic fresh LLM output; deterministic fixture/replay rows/hash bindings are the claim, with operational UTC/run metadata explicitly separated.

- [ ] **3. V10 integration reproduces the hand matrix and synthetic baseline.** Assert the exact numerator/denominator/rates and fixed exclusion/transcript reasons from Task 6; test quote/claim/copy inflation leaves issuer counts unchanged; masked evidence is in audit but absent from headlines; direct/parent/family rows are separate with original assignments unchanged. Include all-unavailable/all-restricted/all-failed/empty-observable cases and null rate. Mixed book/policy/corpus selection refuses publication.

- [ ] **4. Public/import/frozen-v0/wording tests.** `test_analysis_contracts.py` verifies exports are the implemented public objects, typed table schemas/keys and immutable writer/current gate contracts. `test_theme_frozen_v0.py` loads only frozen v0 metadata/rules through `load_codebook`, checks the existing hash `635975d1ec952cf5719ea3b473870f96e7e3a52bc3015cc1ac5725aa80ec1e79`, selects a real child/parent ID from its metadata, and uses entirely invented extraction/support/assignment evidence to verify child-only direct coding and parent roll-up without rewriting the book or assignments. An example resolver spy raises if called; no `validate_codebook` pilot bundle reader, signed gold or example dereference occurs. Extend the existing AST/fresh-interpreter import tests: analysis imports core/themes only; app composes public ingestion/themes; drafting modules import no extraction/support/coding/analysis/report; only existing Selenium adapter imports browser SDKs; ordinary CLI/help imports no concrete model/browser downloader. Add a planted forbidden relative-import case if new relative imports are introduced; otherwise use absolute internal imports and leave the deferred broad scanner extension untouched. `test_theme_wording.py` compares new prompts/report templates/docs against **only permitted** Stage 1 fixture wording under a guarded test, with fixed reason/IDs on failure; it is not either protected Stage 6 wording node. Do not copy literal release prose into the plan/docs/report templates.

- [ ] **5. Run `vertical`, `coverage`, `contracts`, `upstream`, then `stage10` and scoped Ruff.** Audit all selected sources/fixtures once more before the combined group. No full-root run, no gold-vocabulary signed-file reader, no Stage 6 integration modules, no corpus-quote/local-store integration, no live/model/browser test. Record warnings as counts/fixed known categories; optional Torch warning remains an upstream limitation if present, not a Stage 10 pass excuse.

- [ ] **6. Checkpoint:** both approvals. Record V8 fixture-only and V10 hand-check evidence in the new verification document; V5/user-only gates may still be pending and completion must remain pending until observed/disposed.

### Task 12: Document, review, stamp, reconcile, retire and integrate deliberately

**Files:** Documentation/completion ownership above. **Produces:** reviewed final implementation, observed completion gates, authoritative Stage 10 stamp, precise later handoffs and retired plan. This entire task is **future execution**, not an action in the planning session.

- [ ] **1. Finish public documentation.** Update the data dictionary for every analytical/state model, schema, dtype, grain, FK, closed reason and consuming interface; describe compatibility, report audience/rights and browser-boundary offsets. README documents exact replay CLI/config and guarded checks, honest fixture scope, explicit policy/denominators and optional V5 status; refresh only the relevant README/CLAUDE current-state sections. `docs/verification/theme-vertical-slice.md` records actual safe commands/counts/test IDs, V8/V10 arithmetic, V5 observation reference, known limitations and no pilot/model/SEC call. Record every deviation and actual public signature before downstream reconciliation.

- [ ] **2. Task review and final whole-branch review.** After Task 12 documentation changes pass `contracts`, `vertical`, `stage10`, Ruff and its task spec/quality review, dispatch one read-only Sol Ultra `code-reviewer` over the merge BASE to final implementation HEAD. Give the full plan/identical Global Constraints, authoritative requirements, diff file and unresolved Minor list. When it returns, dispatch the independent Sol Ultra second opinion at the **same HEAD**, sequentially. No edits or workers while either review runs. Verify findings rather than blindly applying them; one fix implementer handles the combined required findings, with covering blind red/green checks and scoped re-review. Record both reviewed SHAs and outcomes; a skipped/unavailable second seat is explicit, not “approved”.

- [ ] **3. Obtain the future user-only gates at the final reviewed implementation head.** The user runs full-root default tests and both Stage 6 wording nodes in their artifact checkout, preferably through the guarded runner's explicit `root-user`, `wording-fixture-user`, `wording-pilot-user` modes. Those modes are available only for a human-invoked command; every agent brief forbids invoking them. They collect exactly:

```bash
# USER ONLY; the wrapper captures all failure output and prints safe metadata.
uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py root-user --user-only
uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py wording-fixture-user --user-only
uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py wording-pilot-user --user-only
```

The `root-user` node set is exactly `packages apps tests` with `-m 'not live and not browser'`; the two wording sets are exactly `tests/integration/test_stage6_wording.py::test_no_stage_6_file_quotes_a_stage_1_fixture` and `tests/integration/test_stage6_wording.py::test_no_stage_6_file_quotes_a_pilot_document`. All three retain `--tb=no --show-capture=no -q` internally. Do not substitute an unguarded terminal run to diagnose a failure.

Request **only** counts, safe test IDs, fixed reasons and reviewed HEAD, never source text, gold, screenshots or traceback. Raw terminal output from the underlying commands must not be pasted. If a gate fails, reproduce/isolate with permitted invented inputs and obtain new user counts after a fix; never open protected artifacts to diagnose it. User-run V5 from Task 10 must also be observed with honest native/fallback outcomes or an explicit unavailable-target completion disposition. Upstream Stage 9 results do not discharge these Stage 10 gates. Do not stamp COMPLETE while a required gate/review/availability disposition is pending.

- [ ] **4. Run writing-plans' resolve-before-defer and completion protocol.** Collect leftovers/review findings in one batch, resolve necessary in-scope work before deferring; mark every task checkbox from evidence, add exact deviations/skips and actual test results. Do not tick an earlier grouped deferred item until **all** its obligations are satisfied. Close extraction invariants only if Task 1 completed fully; close renderer hardening only if all three fixes/amendment/tests completed. Leave partial-record/concurrency/cache/allowance/safety, gold, transcript, canonical table fidelity and unrelated work under their original triggers. Add any approved new deferral with ID/context/source, scope/trigger, size, reason and concrete done-when. Run:

```bash
uv run --no-project --python 3.13 python /Users/lowell/.agents/skills/writing-plans/scripts/deferred_stats.py
```

This is a dev statistics command, not the workspace runtime interpreter. It reads only the deferred specification. If environment setup would download, obtain setup authorization or report the limitation; do not silently install. At >=20 open items or any aged >45 days, do the skill's read-only triage and present dispositions for the user's `/deferred` decision; don't rewrite unrelated deferred work or invent an aged-tail acknowledgement. Record statistics, pending dispositions and resolve-before-defer decisions.

- [ ] **5. Stamp the authoritative shared specification and reconcile the roadmap.** Append to **`specs/evidence-linked-theme-extraction.md`, Rollout**, with the actual completion date (the token below is replaced only at observed completion):

```text
> Stage 10: COMPLETE (YYYY-MM-DD) — implemented by plan 15 (specs/plans/completed/15-evidence-linked-theme-extraction.md).
> Next: resume the roadmap.
```

Keep the shared specification live. Do not create a competing completed Stage 10 system spec or retire the browser/point-in-time/shared specification. Then run `derive-roadmap` reconciliation: verify the stamp, tick **only Stage 10**, record actual shipped interfaces/compatibility/V8/V10/V5 and honest scope, and revalidate stages 11–16 without changing their order or routes. No later implementation starts. Update handoffs exactly as follows, using actual approved signatures:

| Later stage | New handoff / ownership preserved |
| --- | --- |
| 11, ROUTING brainstorming | First pilot extraction; explicit replay/workflow/current-gate seam, schema-2 processing failure/completion contracts, expected coverage and policy-scope tables. Owns actual production adapters/panel/policy, at least 50 expert labels, calibration thresholds/views/pooling/agreement floor, V6/quality and bypass of **all four** extraction/classifier/scorer/judge caches for fresh-call stability. `assessed` and fixture V8 remain no acceptance-quality claim. Terminal/partial reprocessing needs an explicit policy; no silent Stage 10 reopening. |
| 12, ROUTING brainstorming | Versioned analytical family mapping and self-or-descendant parent counts are views over unchanged v0. A new taxonomy/hierarchy or inductive/hybrid book still requires training-only discovery, approval, a new version and re-coding. No mapping masquerades as a new theme. |
| 13, ROUTING brainstorming, conditional V7 | Release-only `not_applicable`, explicit transcript-not-in-scope coverage, and release-only Stage 5 ID/schema limit. Owns lawful source selection, transcript identity/speaker attribution/context and producer-consumer schema adaptation. Missing transcript coverage supplies no nonexistent/negative transcript signal. |
| 14, ROUTING writing-plans | Stable analytical/coverage/export artifacts and explicit copy/mask/book/policy/family controls for its required ablations; GS13 unchanged through its final gold drafting, GS18 freeze precedes test text/gold. No fresh-call stability or held-out extraction occurred in Stage 10. |
| 15, ROUTING writing-plans | Immutable append/read state schemas, explicit expected-event selection and current gates. Owns full cohort, recovery/reprocessing, concurrent worker/cache/store/pickle/allowance safety and coordinated source traffic. The sequential `.acquire.lock` append reuse is not a concurrency/backfill proof. |
| 16, ROUTING writing-plans | Same pure policy/evidence/export seam; optional hosted calls/budget/privacy reviews remain separate and unimplemented. |

- [ ] **6. Retire only this completed plan and review documentation delta.** Move via `git mv specs/plans/15-evidence-linked-theme-extraction.md specs/plans/completed/15-evidence-linked-theme-extraction.md` in future execution, update its status/checks/deviations and references, and commit completion records. Run guarded `contracts`/`vertical` and Ruff for the affected final delta; obtain a sequential scoped review of completion/stamp/handoff changes after the earlier whole-branch review. Repeat user/whole-branch checks only if new runtime changes/failures justify it. Never cite an old reviewed SHA as review of later code.

- [ ] **7. Deliberate branch integration and cleanup.** Apply `finishing-a-development-branch`: confirm all required observed gates/reviews, inspect deferred statistics/aged tail, identify actual base/worktree ownership, then present concrete merge/PR/keep/discard options. Default recommendation is a reviewable PR, following the project's prior flow; do not merge or discard without authorization. A created PR must be attached with `attach_artifact`. Preserve the worktree while a PR is under review; after an authorized successful merge and appropriate merged-result checks, remove/archive only the owned execution worktree, then delete the integrated branch. Never force-delete, reset or clean another checkout. Delete only this plan's `.sdd` workspace after resolve-before-defer/retirement evidence is durable. Keep pending review/PR/worktree explicitly if integration is not yet chosen.

- [ ] **8. Final completion report.** Link plan/verification/report artifacts, identify actual checks and scope, state user-only/V5/review evidence, disclose remaining deferrals/limitations and integration status, and hand off **Stage 11 planning through derive-roadmap**. Never claim full-universe extraction, production acceptance/calibration, model accuracy, transcript coverage or a browser highlight behavior without observed evidence.

## Requirement-to-task coverage and plan self-review

| Binding requirement / handoff | Tasks / meaningful evidence |
| --- | --- |
| Stage 10 routing, reconciliation, next-ID and authoritative stamp | Header/reconciliation; Task 12 stamp in shared Rollout, retire only plan and preserve later order/routes |
| R2.3 observability / missing transcript | Tasks 2/6/8/11; expected slot matrix, no transcript state fabrication, coverage/restrictions in report |
| R3.4 overlay-mask headline exclusion with audit | Tasks 3/5/6/7/11; current mask rebind, masked-only case, headline numerator unchanged/audit evidence retained |
| R6.1 strict exactness before storage/aggregation/export, document identity | Tasks 1/3/5/7/8/9/11; altered/hash/second-link/callback tests, all spans reverified from canonical source, CP/UTF-16 boundary tests |
| R6.2 refusal/retry/empty output semantics | Tasks 1/2/6/9/11; no-template partial record, all-zero/empty/no-declaration/exhaustion/failed cases, reason-only output |
| R7.1/R7.2 passage/context/immutable snapshot | Tasks 7/8/10/11; repeated occurrence/escaping/directive encoding/current source and saved canonical/raw hashes, offline static anchor and V5 observed outcomes |
| R11.1 Polars/Parquet row grain | Tasks 2/5/8/11; one quote/two themes, two claims/one observation, empty explicit schema, originals/foreign keys/round-trip |
| R11.2 prevalence and hierarchy/family views | Tasks 5/6/8/11; hand counts and explicit unit/population/book/policy/time/restrictions, self-or-descendant roll-up and overlapping versioned families |
| R11.3 expected denominator/status/missing reason | Tasks 2/4/6/9/11; ten-event matrix and original 27-event acquisition, schema-2 processing failures, no missing/unmatched/review -> negative coercion |
| R11.4 equal issuer weight | Tasks 5/6/11; duplicate/copy/quote/claim inflation and A/B period/equal-issuer arithmetic |
| R11.5 copies counted once | Tasks 2/5/6/9/11; within-event identity, unchanged originals, distinct disclosure/span counting, cross-period refusal and conflicting-copy audit |
| R11.6 release speaker roles | Tasks 2/5/6/11; `not_applicable` rows/coverage, transcript Stage 13 boundary |
| Provenance/time/schema/replay/immutable outputs | Tasks 1–4/8/9/11; input hashes/current gates/metadata UTC/nulls, mixed schemas, raw-cache actual-byte limits, atomics and state-pending receipt tests |
| B1 single optional renderer through application | Tasks 7/9/10/11; public protocol, AST/default import checks, no themes-ingestion dependency/new Selenium copy |
| B5/B6 canonical HTML/rights/sole exactness coordinate | Tasks 3/7/8/10/11; escaped per-span views, browser-boundary conversion only, no browser/OCR/HTML verifier, withheld text/artifact tests |
| Browser isolation/bounds/cleanup and Stage 3 freeze | Task 10 explicit three-defect assessment, truthful preregistration amendment gate, fake lifecycle tests and user V5 record; unrelated deferred work preserved |
| V5 each declared target behavior/fallback | Task 10; pinned target record separates native/availability/capture/static fallback, user-only observation; no fake browser-success claim |
| V8 offline raw-to-cited-report | Tasks 9/11; real CLI replay in temporary invented repository, permitted saved acquisition, zero dispatch/socket trips, current gates and report citation hashes |
| V10 hand denominator check | Tasks 2/6/11; explicit arithmetic and unavailable/restricted/failed/no-theme/missing transcript/all-zero strata |
| Stage 7 invariant prerequisite / arbitrary-error conditional | Task 1 before any stored consumption; Task 9 separate failure receipt avoids triggering partial extraction record design |
| Stage 8/9 consuming gates, explicit policy and original links | Tasks 3/5/8/9/11; raw outcomes separate, all original links/document keys, fixture policy visibly scoped, absent policy review |
| GS13 and all-session blinding / safe failure output | Global Constraints exact row; Tasks 1/3/9/10/11/12 guards, explicit no-root/no-Stage6 agent nodes and safe user-only reports |
| Sequential model routing/reviews/checkpoints | Execution protocol and every task; Sol Medium/Ultra substitution, two approvals before next task, sequential final seats |
| Documentation/backlog/completion/branch integration | Task 12; field dictionary, verification evidence, resolve-before-defer/stats/triage, shared stamp, downstream reconciliation, plan-only retirement and deliberate integration |

Self-review performed while drafting: each Stage 10 entry/exit and cited binding requirement maps to a task above; task dependencies put invariant hardening before consumption and current gates before publication; codebook/assignment/historical/artifact ownership stays with its shipped owner; no numeric calibration, production panel, pilot extraction, transcript schema or runtime concurrency leaks into scope. Commands select only named audited paths; full-root and both Stage 6 wording nodes remain user-only. Every runtime task specifies interfaces, owned files, red tests, minimal behavior, green checks and a review checkpoint. The exact GS13 row is retained.

**Decisions still requiring observed evidence/disposition during execution:** native V5 behavior and target availability; any truthful frozen-adapter amendment disposition under the existing preregistration restriction; final user-only checks; final code review and branch integration. These are concrete gates, not blank implementation requirements. Production policy/model/quality thresholds and later-stage research choices remain deliberately owned by Stage 11. No implementation or current-stage success is claimed by this plan. Human review of the saved plan is pending; no independent plan-review agent was dispatched in the planning session.

## Fresh-session execution handoff

Use a fresh GPT-6.1 Sol Medium execution session in `/Users/lowell/Projects/earnings-themes` and invoke `subagent-driven-development` on this saved plan. Read its complete Global Constraints, recheck current Git state, preserve uncommitted work, and perform the preflight plan-conflict review before any implementation. Use the approved Sol Ultra structural/reviewer route where specified. Execute Tasks 1–12 sequentially with identical blinding for every agent and both task approvals before proceeding; take durable fresh-session checkpoints when needed. Begin with the diagnostic guard and extraction invariant prerequisite. Do not read pilot/gold/data, run root/Stage 6 gates, download/call models, or begin Stage 11. This planning session stops at the saved plan.
