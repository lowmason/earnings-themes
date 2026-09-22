# Roadmap: evidence-linked theme extraction

> For agentic workers: REQUIRED SKILL: derive-roadmap — resume via its
> reconcile step; route each unticked stage per its ROUTING line; never plan
> this document wholesale.

Source spec: `specs/evidence-linked-theme-extraction.md`. Derived 2026-09-22
from `main` at `bdcf0a4`; notes reconciled the same day after instruction-only
edits (no stage shipped).

## Gap analysis

¹ Searched `packages/*/src`, `apps/*/src`, `tests/{contracts,fixtures,integration}`,
`config/`, `codebooks/`, `prompts/`, and `expirements/` at `bdcf0a4`: each
`__init__.py` is a two-line `hello()` stub; every other listed directory is empty.

Decisions taken by the user on 2026-09-22, resolving the batched questions:
**D1** — V6 gates only metrics the pilot can estimate (R12.2 conflicts with
V6 as written); **D2** — the user is the sole annotator (R12.6, R8.4);
**D3** — R14.2's hosted ceiling is an optional stage; R5.3/V3 are unstaged.

| Req | Verdict | Evidence | Note |
|---|---|---|---|
| R1.1 | missing | none found¹ | |
| R1.2 | missing | none found¹ | Candidate library only as optional `edgar` extra (`packages/earnings-ingestion/pyproject.toml:21`) |
| R1.3 | missing | none found¹ | `tenacity` declared (`packages/earnings-ingestion/pyproject.toml:14`); no limiter |
| R1.4 | missing | none found¹ | State list differs from A §644 (adds restricted/acquired/completed; A has available/processed); spec is the later text — reconcile in-stage |
| R1.5 | missing | none found¹ | |
| R2.1 | missing | none found¹ | |
| R2.2 | missing | none found¹ | Open → V7 |
| R2.3 | missing | none found¹ | |
| R3.1 | missing | none found¹ | |
| R3.2 | missing | none found¹ | Python `str` indices are already code points; the hazard is the browser boundary (R7) |
| R3.3 | missing | none found¹ | |
| R3.4 | missing | none found¹ | Amends A §563; `AGENTS.md:592` points at the spec |
| R3.5 | missing | none found¹ | |
| R4.1 | missing | none found¹ | Open → V2 |
| R4.2 | missing | none found¹ | |
| R4.3 | missing | none found¹ | |
| R5.1 | missing | none found¹ | |
| R5.2 | missing | none found¹ | `rapidfuzz` in optional `fuzzy-localization` extra (`packages/earnings-themes/pyproject.toml:45`) |
| R5.3 | missing | none found¹ | Unstaged (D3) — see Completion |
| R5.4 | missing | none found¹ | |
| R5.5 | missing | none found¹ | |
| R6.1 | missing | none found¹ | |
| R6.2 | missing | none found¹ | |
| R7.1 | missing | none found¹ | |
| R7.2 | missing | none found¹ | Open → V5 |
| R8.1 | missing | none found¹ | |
| R8.2 | missing | none found¹ | Open → V4; no scorer dependency declared |
| R8.3 | missing | none found¹ | |
| R8.4 | missing | none found¹ | ≥50 labels supplied by the user (D2) |
| R8.5 | missing | none found¹ | |
| R8.6 | missing | none found¹ | |
| R9.1 | missing | none found¹ | |
| R9.2 | missing | none found¹ | |
| R9.3 | missing | none found¹ | |
| R9.4 | missing | none found¹ | |
| R9.5 | missing | none found¹ | See `embeddings` extra row |
| R9.6 | missing | none found¹ | |
| R9.7 | missing | `codebooks/` empty | No invented taxonomy (compliant); decision-record mechanism absent |
| R9.8 | missing | none found¹ | |
| R9.9 | missing | none found¹ | |
| R10.1 | missing | none found¹ | Amends A §452; `AGENTS.md:478` points at the spec |
| R10.2 | missing | none found¹ | |
| R10.3 | missing | none found¹ | |
| R11.1 | missing | none found¹ | |
| R11.2 | missing | none found¹ | |
| R11.3 | missing | none found¹ | |
| R11.4 | missing | none found¹ | |
| R11.5 | missing | none found¹ | |
| R11.6 | missing | none found¹ | |
| R12.1 | missing | none found¹ | |
| R12.2 | missing | none found¹ | Amends A §728; `AGENTS.md:748` points at the spec |
| R12.3 | missing | none found¹ | |
| R12.4 | missing | none found¹ | |
| R12.5 | missing | none found¹ | |
| R12.6 | missing | none found¹ | Single annotator (D2): agreement not measurable — see Completion |
| R12.7 | missing | none found¹ | |
| R12.8 | missing | none found¹ | |
| R12.9 | missing | none found¹ | |
| R12.10 | missing | none found¹ | |
| R13.1 | missing | none found¹ | Conflicts with R12.2; resolved by D1 — see Completion |
| R13.2 | missing | none found¹ | Binding with R6.1 |
| R13.3 | missing | none found¹ | Held-out result is feasibility-level (D1) |
| R14.1 | missing | none found¹ | Required dependencies carry no provider SDK (compliant surface); no fake adapter or replay |
| R14.2 | missing | none found¹ | Optional Stage 14 (D3) |
| R14.3 | implemented-as-specified | `packages/earnings-themes/pyproject.toml:33,50` (optional extras only); `AGENTS-jev-addendum.md:4-14`; `specs/jev-integration-spec.md:3-24` | Benchmark-against-R8.2 clause applies only under separate authorization |
| R14.4 | implemented-as-specified | `apps/earnings-pipeline/pyproject.toml:23` (`langgraph` optional only); no optimizer or multi-agent dependency declared | Standing constraint; "usable without frameworks" becomes testable once domain code exists |
| R14.5 | missing | `uv.lock`: edgartools 5.58.0 depends on `pandas` | V1 very likely non-vacuous |
| R14.6 | missing | none found¹ | |
| R14.7 | missing | none found¹ | |
| V1 | missing | none found¹ | |
| V2 | missing | none found¹ | |
| V3 | missing | none found¹ | Needs a billable call outside R14.2 and against R14.1; unstaged (D3) |
| V4 | missing | none found¹ | |
| V5 | missing | none found¹ | |
| V6 | missing | none found¹ | Scope narrowed by D1 |
| V7 | missing | none found¹ | |
| V8 | missing | none found¹ | |
| V9 | missing | none found¹ | |
| V10 | missing | none found¹ | |
| V11 | missing | none found¹ | |
| `extraction`/`openai`/`anthropic` extras | in-code-but-not-in-spec | `packages/earnings-themes/pyproject.toml:19,23-28` | Spec names no framework (A §664 proposes PydanticAI); hosted SDKs serve only R14.2/R5.3 — flag, not defect |
| `embeddings` extra | in-code-but-not-in-spec | `packages/earnings-themes/pyproject.toml:39` | Sits on the themes package; R9.5 places clustering outside the pipeline |
| `entity-matching` extra | in-code-but-not-in-spec | `packages/earnings-ingestion/pyproject.toml:25` | Serves company enrichment, out of this spec's scope (A §429) |
| Dev tooling | in-code-but-not-in-spec | `pyproject.toml:22-35` | `dev` group and Ruff config exist; no pytest config, `live` marker, or import mode (A §193); `CLAUDE.md` still calls the group missing |

Totals: 78 missing · 2 implemented-as-specified · 4 in-code-but-not-in-spec ·
0 implemented-differently · 0 out-of-repo.

## Stages

- [ ] Stage 1: Acquisition-library and parser fidelity (investigation)
      Objective: Establish by measurement which parser yields faithful typed elements on real releases, and what the pinned acquisition library returns.
      Spec: V1, V2 (discharging the open markers in R14.5 and R4.1); R1.3 for live fetches; A §242, A §425 for fixtures.
      Gap closed: V1, V2.
      Consumes: nothing.
      Produces: a decision record naming the parser, with V2 rates per candidate and fixture class; V1 return types for edgartools 5.58.0; a fixture corpus spanning V2's four release classes, with hand-marked structure, under `tests/fixtures/`.
      Exit: the decision record reports reading-order corruption, footnote merging, and header loss for every candidate on every class (V2); V1 lists the concrete return type of each exhibit and table path (V1); every committed fixture has a source-register entry recording its redistribution basis.
      ROUTING: brainstorming

- [ ] Stage 2: Core evidence spine
      Objective: Give `earnings-core` the contracts and exactness validator that every later stage builds on.
      Spec: R3.1–R3.4 (contracts), R4.1 (element contract), R5.4, R5.5, R6.1, R13.2, V9; A §193.
      Gap closed: R3.2, R3.3, R5.4, R5.5, R6.1, R13.2; V9 (all cases except normalization and sentence splitting); Dev tooling row.
      Consumes: Stage 1 decision record (element types and nesting observed on fixtures).
      Produces: `earnings-core` contracts for a hashed, versioned canonical document, typed elements with stable IDs and code-point spans, overlay masks, and prefix/suffix span locators; an R6.1 validator with no tolerance parameter; root pytest configuration with a registered `live` marker and collision-safe test imports.
      Exit: `uv run --locked --all-packages pytest packages apps tests -m "not live"` passes the Stage 2 V9 cases, each failure class rejected with a recorded reason (R3.2/R3.3/R5.4/R5.5/R6.1/R13.2); a test shows applying a mask leaves the canonical hash unchanged; the pytest configuration registers `live` (Dev tooling row).
      ROUTING: writing-plans

- [ ] Stage 3: Structure-aware canonicalization
      Objective: Turn saved release bytes into hashed, versioned canonical documents with typed elements, quarantined table cells, and boilerplate masks.
      Spec: R3.1, R3.4 (versioned policy), R3.5, R4.1–R4.3, V9; A §498–516.
      Gap closed: R3.1, R3.5, R4.1, R4.2, R4.3; V9 (normalization, sentence splitting).
      Consumes: Stage 1 parser decision and fixtures; Stage 2 contracts and validator.
      Produces: an ingestion canonicalizer from saved bytes plus metadata to a canonical document version, with no network client; table cells stored as cell evidence with header context; OCR-derived elements flagged; masks from a versioned boilerplate policy; a repeatable R3.5 fidelity check.
      Exit: every Stage 1 fixture canonicalizes offline and passes the Stage 2 validator (R3.1/R4.1); a test shows no narrative element contains table-cell text (R4.2); a test shows OCR-derived text flagged and never verified as an original quotation (R4.3); V9 normalization and financial-abbreviation/decimal splitting cases pass; an R3.5 fidelity report on a sample covers all six named categories (R3.5).
      ROUTING: brainstorming

- [ ] Stage 4: Acquisition and event resolution
      Objective: Acquire earnings events from EDGAR under the shared access policy, recording a processing state for every expected document.
      Spec: R1.1–R1.5, R14.5; A §391–427.
      Gap closed: R1.1, R1.2, R1.3, R1.4, R1.5, R14.5.
      Consumes: Stage 1 V1 findings; Stage 2 contracts; Stage 3 canonicalizer (content inspection for R1.2/R1.5).
      Produces: an opt-in live EDGAR adapter behind a shared 2 req/s limiter, User-Agent configured outside Git; immutable raw snapshots with retrieval metadata; release identification and event records with separated time fields; a per-document processing-state table, including expected-but-absent documents with a `missing_reason`; offline replay from saved responses.
      Exit: offline replay of saved EDGAR responses identifies the fixture issuers' releases, including a narrative-only release and alternative exhibit numbering (R1.1/R1.2); tests hold concurrent workers at or below 2 req/s and stop on a persistent 403 (R1.3); event records keep each R1.5 time field separate with unknowns preserved (R1.5); the state table represents every R1.4 state from fixtures (R1.4); library output is Polars at the boundary, or V1's vacuity is recorded (R14.5).
      ROUTING: brainstorming

- [ ] Stage 5: Pilot codebook and gold-set protocol
      Objective: Fix the pilot sample, its issuer-and-time split, an approved codebook v0, and annotation tooling, so hand-coding runs while Stages 6–9 are built.
      Spec: R9.2, R9.7, R12.1–R12.6; R13.1 (release-identification labels); D2.
      Gap closed: R9.2, R9.7, R12.1, R12.3, R12.4, R12.5; R12.6 (limitation, D2).
      Consumes: Stage 3 canonical documents (gold spans bind to that canonicalization version); Stage 4 event bundles, issuer and fiscal-period identity, processing states.
      Produces: a codebook contract with R9.2's fields; codebook v0 drafted from training-partition bundles only and approved in a decision record; a gold-annotation contract and validator; a 20–40 event-bundle pilot manifest with its split. Gold spans name their canonical version; a later version re-anchors them before reuse, never mutates them.
      Exit: a test places each bundle, with all copies and revisions, in exactly one issuer-and-time split (R12.1/R12.3); the manifest holds no-theme, unavailable, restricted, and parser-failure bundles plus curated hard negatives (R12.4/R12.5); codebook v0's decision record names its training-partition discovery corpus (R9.2/R9.7); annotations on at least three bundles, including release-identification labels, pass the validator; the single-annotator limitation is recorded (R12.6, D2).
      ROUTING: brainstorming

- [ ] Stage 6: Evidence selection and verification
      Objective: Extract quote-claim candidates by pointer selection over every analysis-eligible element, keeping only code-verified spans.
      Spec: R5.1, R6.1 (before storage), R6.2, R10.1, R10.2, R14.1, R14.6, R14.7, V11.
      Gap closed: R5.1, R6.2, R10.1 (default path), R10.2, R14.1, R14.6; R14.7/V11 (tool-call and verification-bypass cases).
      Consumes: Stage 2 validator and locators; Stage 3 canonical fixtures only — not Stage 4.
      Produces: a themes extractor visiting every eligible element; a model-adapter interface with a fake adapter, response replay, and an R14.6-keyed cache; one open-weight local adapter behind the `live` marker, its weight license recorded; an auditable rejection record.
      Exit: offline fake-model runs over Stage 3 fixtures retain only R6.1-valid quotes, and every rejection records a reason after bounded retries (R5.1/R6.2); a coverage test shows every eligible element visited and no top-k discovery path (R10.1/R10.2); a test shows changing any R14.6 key component misses the cache (R14.6); the default suite makes no network or billable call (R14.1); the V11 fixture triggers no tool call and cannot bypass R6.1 (R14.7/V11).
      ROUTING: brainstorming

- [ ] Stage 7: Semantic support assessment
      Objective: Judge whether each verified span supports its claim under the theme definition, as signals that can only reject or flag.
      Spec: R8.1–R8.6, V4; R6.1 (before support judgment).
      Gap closed: R8.1, R8.3, R8.5, V4; R8.2 (primary scorer; alternative wired).
      Consumes: Stage 6 verified quote-claim pairs.
      Produces: a support assessor pairing an open-weight entailment score (primary) with a model-judge signal using order-swapping and cross-family judges; RG §3's alternative behind the same interface; AUC-ROC and accepted-claim precision computation; a V4 decision record with checkpoint identity in the manifest.
      Exit: the V4 record confirms the primary scorer's weight license and a self-hosted run with no API call (V4/R8.2); fixture pairs misattributed to a competitor, a prior period, or a negation are rejected or flagged (R8.1); scores persist as versioned signals, never verdicts (R8.3); a judge output editing evidence or promoting an invalid span is refused (R8.5).
      ROUTING: brainstorming

- [ ] Stage 8: Deductive coding
      Objective: Assign verified, supported spans to themes of a frozen approved codebook as versioned multi-label rows, routing non-matches to a novelty queue.
      Spec: R9.1 (deductive), R9.3, R9.4, R9.6, R9.8, R9.9, R14.7, V11.
      Gap closed: R9.1 (deductive), R9.3 (queue), R9.4, R9.6, R9.8, R9.9; R14.7/V11 (codebook case).
      Consumes: Stage 5 codebook contract and approved v0; Stage 6 verified spans; Stage 7 support decisions.
      Produces: an open-weight classifier emitting typed multi-label output with bounded retries against a frozen codebook version; assignment rows carrying codebook identifier and version; a novelty queue for human adjudication.
      Exit: fake-model replay exercises typed multi-label output with bounded retries against frozen v0 (R9.1/R9.8); one quote supporting two themes yields two rows sharing its quote identifier (R9.9); an unmatched candidate enters the novelty queue and no new theme identifier appears (R9.3); rows carry codebook identifier and version, and a mixed-version comparison is refused (R9.6); cluster labels and sentiment never populate theme fields (R9.4); the V11 fixture leaves the codebook unchanged (R14.7/V11).
      ROUTING: writing-plans

- [ ] Stage 9: Coverage-aware aggregation and cited export (theme vertical slice)
      Objective: Produce analytical rows, coverage-aware prevalence, and a source-linked report that carry one release end to end.
      Spec: R2.3, R3.4 (headline exclusion), R6.1 (before export), R7.1, R7.2, R11.1–R11.6, V5, V8, V10.
      Gap closed: R2.3, R3.4, R7.1, R7.2, R11.1, R11.2, R11.3, R11.4, R11.5; R11.6 (release roles); V5, V8, V10.
      Consumes: Stage 3 canonical documents and masks; Stage 4 processing-state table; Stages 6–8 verified, supported, coded assignments.
      Produces: Polars/Parquet rows at the R11.1 grain; prevalence tables printing numerator, denominator, unit, and restrictions; passage links paired with immutable snapshots; a cited report; the V8 offline end-to-end test.
      Exit: V8 passes with no network or credentials, from raw fixture to cited report (V8/R11.1); V10 reproduces hand-computed numerators and denominators across unavailable, restricted, failed, and no-theme documents, and reports missing-transcript coverage (V10/R11.2/R11.3/R2.3); a test shows masked spans absent from headline prevalence yet present in audit output (R3.4); tests show a disclosure's copies counted once and issuers weighted equally (R11.5/R11.4); release rows carry `not_applicable` speaker roles (R11.6); V5 records each target browser's highlight behavior, and the snapshot renders the span wherever the link fails (V5/R7.1/R7.2).
      ROUTING: writing-plans

- [ ] Stage 10: Feasibility pilot and threshold calibration
      Objective: Run the pipeline against the hand-coded pilot, calibrate the judge, and gate the metrics the pilot can estimate.
      Spec: R8.2, R8.4, R8.6, R12.2, R12.7, R12.8, R12.10, R13.1, R13.3, V6; D1, D2.
      Gap closed: R8.2, R8.4, R8.6, R12.2, R12.7, R12.8, R12.10; R13.1/V6 (per D1).
      Consumes: the Stage 5 manifest fully annotated by the user; at least 50 user support labels on Stage 7 outputs (D2); the Stage 9 pipeline.
      Produces: implementations of every R13.1 metric plus retention, stability, and AUC-ROC; a pilot report with issuer- or event-level uncertainty; a judge-calibration report with its pre-registered floor; the V6 decision record of gates.
      Exit: the pilot report gives every R13.1 metric's observed distribution with event-level intervals, labeled feasibility-only (R12.2/R12.7); the V6 record gates only pilot-estimable metrics, marks rare-theme recall, sector prevalence, and source-selection bias descriptive-only, and is committed before any configuration comparison (V6/R13.1, D1); judge agreement with the user's labels is reported against its pre-registered floor, with AUC-ROC for both scorers (R8.4/R8.6/R8.2); a reject-everything configuration fails the suite (R12.8); k-run stability is computed with replay bypassed (R12.10).
      ROUTING: brainstorming

- [ ] Stage 11: Inductive and hybrid codebook
      Objective: Discover candidate themes offline from training-partition evidence, approve them as a new codebook version, and re-code the declared corpus.
      Spec: R9.1 (inductive, hybrid), R9.3 (approval), R9.5, R10.3, R12.3.
      Gap closed: R9.1, R9.3, R9.5, R10.3; `embeddings` extra row.
      Consumes: Stage 8 coding and novelty queue; Stage 10 splits and metrics.
      Produces: an offline clustering aid outside the application pipeline; consolidation preserving evidence pointers and contradictory claims; an approval path from candidate codebook to a new frozen version; a hybrid mode; re-coding under the new version.
      Exit: a test shows candidate themes derive from training-partition data only (R12.3); a test shows consolidation keeps every evidence pointer and contradictory claim (R10.3); approval is recorded in a decision record and re-coded rows carry the new version (R9.1/R9.3); an import check shows no clustering dependency reachable from the application pipeline (R9.5, `embeddings` row).
      ROUTING: brainstorming

- [ ] Stage 12: Transcript extension (conditional on V7)
      Objective: Add lawfully usable transcripts with speaker roles, or record that no candidate corpus qualifies.
      Spec: R2.1, R2.2, R4.1 (speaker turns), R11.6, V7; D2.
      Gap closed: R2.1, R2.2, V7; R11.6 (management/analyst split).
      Consumes: Stages 3 and 4; Stage 9 aggregation; Stage 10 metrics.
      Produces: a V7 record per candidate corpus; if one qualifies, a rights-gated transcript adapter storing locators and local features where terms forbid redistribution, and speaker turns with role and attribution status.
      Exit: V7 records each candidate's license, redistribution terms, and diarization accuracy against a user-labeled sample (V7); if none supports the management/analyst split, R2.2 is recorded as failed and the stage parks; otherwise fixture transcripts yield role-attributed turns, unresolved roles stay `other`/`unknown`, and restricted text is never redistributed (R2.1/R2.2/R11.6).
      ROUTING: brainstorming

- [ ] Stage 13: Configuration comparison and held-out evaluation
      Objective: Run R12.9's ablations against the V6 gates, freeze one selected configuration, and evaluate it once on the held-out split.
      Spec: R5.2, R10.1 (whole-document arm), R10.2 (retrieval-only arm), R11.5 (dedup arm), R12.9, R13.3; D1.
      Gap closed: R5.2, R12.9, R13.3.
      Consumes: Stage 10 gates, metrics, and splits; Stage 11 inductive and hybrid codebooks; Stage 12 transcripts if shipped, else that arm is recorded as not run.
      Produces: a generate-then-verify comparator; whole-document and retrieval-only modes; an ablation report with quality, latency, tokens, and cost per arm; a selection decision record; one held-out evaluation report.
      Exit: a test shows generate-then-verify rejects every unresolvable candidate and never repairs wording (R5.2); the ablation report covers every available R12.9 arm and adjudicates against V6's gates (R12.9); the selected configuration is frozen by hash and evaluated on the held-out split once, a second run under the same protocol is refused, and the report is labeled feasibility-level (R13.3, D1).
      ROUTING: writing-plans

- [ ] Stage 14: Hosted quality ceiling (optional)
      Objective: Measure a hosted frontier model's quality ceiling on a frozen subset within the $100 authorization.
      Spec: R14.2; D3.
      Gap closed: R14.2.
      Consumes: Stage 13 frozen configuration; Stage 10 metrics.
      Produces: a hosted adapter behind per-document and per-run ceilings enforced before dispatch; a ceiling report.
      Exit: an offline budget-exhaustion test yields a visible partial or failed status, never silent truncation; recorded spend stays within $100 with a pricing basis; no required-path module imports the hosted adapter; the report is labeled an ablation ceiling (R14.2).
      ROUTING: writing-plans

## Stage-spec stamp

Every stage spec's Rollout note carries this line, which writing-plans copies
verbatim into the stage plan's header:

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage N — on plan
> completion, tick the stage and re-validate later stages against what shipped.

On completion the stamp becomes authoritative:

> Stage N: COMPLETE (YYYY-MM-DD) — implemented by plan <id> (path).
> Next: resume the roadmap.

A stage routed straight to writing-plans (Stages 2, 8, 9, 13, 14) has no stage
spec: its plan header carries the Roadmap line directly, and its COMPLETE line
is appended to the Rollout section of `specs/evidence-linked-theme-extraction.md`,
which is the stamp a resume reads for those stages.

## Completion

Retire this roadmap only after a conformance audit of the accumulated system:
re-run the gap rubric over every row above, with evidence per verdict
(implementing stage and plan, `> Deviation:` notes, deferred entries). Each
requirement still unmet exits one of two ways: a new stage (the roadmap stays
live), or conscious deferral with a written why. Deferrals already decided on
2026-09-22:

- **R5.3, V3** (D3) — V3 needs a billable call outside R14.2's authorization and
  at odds with R14.1; revisit only under a separate authorization.
- **R13.1 gates for rare-theme recall, sector prevalence, and source-selection
  bias** (D1) — R12.2 says the pilot cannot estimate them; they await a larger
  event-level validation set that this roadmap does not build.
- **R12.6 agreement** (D2) — single annotator; agreement is not measurable and is
  recorded as a limitation, not met.
- **Stage 12** parks if V7 finds no qualifying corpus; **Stage 14** is optional.

Not staged because no requirement asks for them: the learning path's LangGraph,
DSPy, and CrewAI exercises (R14.4). Out of scope per the spec: importance
ranking, taxonomy content, company enrichment, and prompt-optimizer compilation.
