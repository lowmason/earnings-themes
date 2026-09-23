# Roadmap: evidence-linked theme extraction

> For agentic workers: REQUIRED SKILL: derive-roadmap — resume via its
> reconcile step; route each unticked stage per its ROUTING line; never plan
> this document wholesale.

Source spec: `specs/evidence-linked-theme-extraction.md`. Derived 2026-09-22
from `main` at `bdcf0a4`; notes reconciled the same day after instruction-only
edits (no stage shipped).

Amending spec: `specs/point-in-time-djia-cohort.md`, adopted 2026-09-22. It
inserted Stage 4 (point-in-time DJIA cohort) and Stage 15 (full DJIA
eight-quarter run), renumbered former Stages 4–13 to 5–14 and former Stage 14 to
16, and moved pilot-sample selection out of the codebook stage into Stage 5. No
stage shipped. **`P` cites that spec**: `P-C1`–`P-C7` are its Decisions rows,
`P-A4`/`P-A5`/`P-A15` its three Acceptance-criteria groups, `P-VF`/`P-VI`/`P-VL`
its deterministic-fixture, offline-integration, and optional-live verification
groups, and `P §Section` cites a section by name.

## Gap analysis

¹ Searched `packages/*/src`, `apps/*/src`, `tests/{contracts,fixtures,integration}`,
`config/`, `codebooks/`, `prompts/`, and `expirements/` at `bdcf0a4`: each
`__init__.py` is a two-line `hello()` stub; every other listed directory is empty.

² Searched the same paths at `6021323` for index-membership, cohort, or
security-to-issuer resolution code: none. `expirements/parser-fidelity/` and
`tests/fixtures/releases/` now hold Stage 1's harness and release fixtures, whose
CIK fields serve EDGAR discovery and fixture provenance only.

Decisions taken by the user on 2026-09-22, resolving the batched questions:
**D1** — V6 gates only metrics the pilot can estimate (R12.2 conflicts with
V6 as written); **D2** — the user is the sole annotator (R12.6, R8.4);
**D3** — R14.2's hosted ceiling is an optional stage; R5.3/V3 are unstaged.

**D4** — taken 2026-09-22 with the cohort amendment, resolving R12.4/R12.5
against `P-C7`. R12.4 required the pilot manifest to *hold* unavailable,
restricted, and parser-failure bundles; `P-C7` forbids selection from depending
on acquisition, parse, or theme outcomes. Selection stays outcome-blind, and
failure-class coverage becomes an **observed report over the frozen manifest**: a
class absent from the 40 selected events is reported as a coverage gap and is
never repaired by reselecting. R12.5's curated hard negatives move to fixtures
held outside the pilot manifest, exercised by contract tests rather than by event
selection. Widened at review the same day: hard-negative claims drawn from
confusable periods, issuers, and sections of the frozen pilot documents are also
annotated with the gold set and scored with the pilot metrics, which changes no
pilot row.

Counting note: `P` counts **issuer-events** and targets exactly 40 (`P-C5`),
while R12.2 counts hand-coded documents or bundles at 20–40. The two are
compatible — 40 sits inside 20–40 — but one event may yield several bundles
(a release plus its transcript, copies, or revisions), so the bundle count can
exceed the event count. Never treat the two numbers as the same quantity.

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
| R12.4 | missing | none found¹ | Reframed by D4: observed coverage over the frozen pilot manifest |
| R12.5 | missing | none found¹ | Reframed by D4: out-of-manifest fixtures plus hard-negative claims in pilot documents |
| R12.6 | missing | none found¹ | Single annotator (D2): agreement not measurable — see Completion |
| R12.7 | missing | none found¹ | |
| R12.8 | missing | none found¹ | |
| R12.9 | missing | none found¹ | |
| R12.10 | missing | none found¹ | |
| R13.1 | missing | none found¹ | Conflicts with R12.2; resolved by D1 — see Completion |
| R13.2 | missing | none found¹ | Binding with R6.1 |
| R13.3 | missing | none found¹ | Held-out result is feasibility-level (D1) |
| R14.1 | missing | none found¹ | Required dependencies carry no provider SDK (compliant surface); no fake adapter or replay |
| R14.2 | missing | none found¹ | Optional Stage 16 (D3) |
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
| `entity-matching` extra | in-code-but-not-in-spec | `packages/earnings-ingestion/pyproject.toml:25` | Serves company enrichment, which is out of this spec's scope; Stage 4 may use it only to generate issuer-resolution candidates, since fuzzy similarity is a candidate score, never proof of identity (A §429) |
| Dev tooling | in-code-but-not-in-spec | `pyproject.toml:22-35` | `dev` group and Ruff config exist; no pytest config, `live` marker, or import mode (A §193) |
| P-C1 | missing | none found² | DJIA resolved point in time, not as one current roster; Stage 4 |
| P-C2 | missing | none found² | Eligibility keyed to `first_publication_time`; defined in Stage 4, joined in Stage 5 |
| P-C3 | missing | none found² | Window `[2024-07-01, 2026-07-01)`; reported fiscal labels stay separate fields |
| P-C4 | missing | none found² | Public-information cutoff `2026-09-22` |
| P-C5 | missing | none found² | Deterministic 40-event pilot; supersedes the codebook stage's former sample choice (D4) |
| P-C6 | missing | none found² | Full eight-quarter run is Stage 15; observed count never forced to `30 × 8` |
| P-C7 | missing | none found² | Cohort-before-acquisition order is binding; split across Stages 4 and 5 |
| P-A4 | missing | none found² | Stage 4 acceptance criteria |
| P-A5 | missing | none found² | Stage 5 acceptance criteria |
| P-A15 | missing | none found² | Stage 15 acceptance criteria |
| P-VF | missing | none found² | 19 deterministic fixture cases; split across Stages 4 and 5 |
| P-VI | missing | none found² | Offline integration replay, anchor evidence through frozen pilot manifest |
| P-VL | missing | none found² | Optional `live` verification of the real roster — source access and terms, dated-evidence parsing, reconciliation against the corroborating snapshot; never in default CI; Stage 4 |

Totals: 91 missing · 2 implemented-as-specified · 4 in-code-but-not-in-spec ·
0 implemented-differently · 0 out-of-repo. The 91 comprises 78 rows from
`specs/evidence-linked-theme-extraction.md` and 13 from
`specs/point-in-time-djia-cohort.md` (the `P-*` rows).

## Open questions

- **Stage 5 — R1.2/R1.5 against P-C7.** R1.2 and R1.5 identify a release and
  match events by exhibit content, but P-C7 freezes both manifests before any
  acquisition outcome exists. Stage 5's brainstorming decides whether an
  identification-only fetch counts as acquisition under P-C7, and what
  eligibility status an event slot gets when identification fails.

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

- [ ] Stage 4: Point-in-time DJIA cohort
      Objective: Freeze a versioned, point-in-time DJIA universe — security-level membership intervals resolved to issuers and zero-padded CIKs — before any earnings document is acquired.
      Spec: P-C1, P-C2, P-C3, P-C4, P-C7, P-A4; P §Temporal definitions, §Data contracts (universe definition, membership assertion), §Membership evidence and source rights, §Issuer resolution, §Failure handling, §Verification; A §249–269 (index membership and identifiers, including the zero-padded CIK at A §264), A §429 (entity-resolution rules this stage follows).
      Gap closed: P-C1, P-C2 (the membership-reference definition only; the event join is Stage 5), P-C3, P-C4, P-C7 (the cohort-before-acquisition half), P-A4; P-VF (interval, resolution, conflict, and cutoff cases), P-VI (its membership-interval and issuer-resolution legs), P-VL.
      Consumes: Stage 2 contracts, provenance and hashing primitives, and the root pytest configuration with its registered `live` marker. No parser, canonicalizer, document, or model artifact — the stage is placed after Stage 3 so that acquisition follows it immediately, but Stage 2 is its only hard dependency.
      Produces: in `earnings-ingestion`, a versioned DJIA universe definition at P's universe grain (`universe_name = "djia"`, `period_end_start = 2024-07-01`, `period_end_stop = 2026-07-01`, `public_information_cutoff = 2026-09-22`, `membership_reference = first_publication_time`); security-level membership assertions at one row per index, security, effective interval, and source-evidence item, with half-open `[effective_from, effective_to)` intervals and a `status` of `supported`, `conflicting`, `ambiguous`, or `withheld`; security-to-issuer mappings carrying 10-character zero-padded CIK evidence; the derived union of candidate issuers over every membership interval that overlaps the eligible-publication range, `2024-07-01` through the `2026-09-22` cutoff (membership is judged at `first_publication_time`, so an issuer added after `2026-07-01` can still carry an eligible event); a membership source register with owner, URL, access method, cost, terms, redistribution status, coverage, update behavior, known limitations, and last verification date; a coverage and conflict report; synthetic redistributable fixtures; version-controlled manual override assertions with evidence, rationale, reviewer, and effective dates; an opt-in `live` verification that checks source accessibility and current terms, parses the dated evidence behind the real manifest, and reconciles official changes against the corroborating snapshot, recording retrieval metadata under the shared rate and identification policies (P-VL).
      Exit: every membership interval resolves to a source-evidence row and every resolved CIK is a 10-character zero-padded string (P-A4); fixture tests build intervals from an anchor plus additions and removals, with inclusive starts and exclusive ends, and an open interval carrying no `effective_to` (P-VF); a missing anchor snapshot refuses to freeze the manifest with the reason recorded, and conflicting effective dates persist as separate assertions rather than being merged and hold the freeze until a recorded review resolves them (P §Failure handling); the coverage and conflict report lists every interval conflict and coverage gap (P-A4); evidence first published after 2026-09-22 cannot revise the version (P-C4); a test shows no current snapshot silently backdated and no ETF holdings record treated as the official roster; a test shows historical ticker changes and multiple securities preserved, and one issuer's several securities deriving one issuer row (P-VF); source access and redistribution status are recorded for every source, with unclear rights keeping artifacts local; the universe manifest freezes with a version and content hash written atomically, and refuses to freeze on unresolved issuer identity unless the record is explicitly retained as unresolved and excluded with its reason; the default suite makes no network call, uses no proprietary roster, and needs no credentials, while the `live` verification runs only when opted in and records its result with retrieval metadata (P-VL).
      ROUTING: writing-plans — `specs/point-in-time-djia-cohort.md` is this stage's spec; it needs no brainstorming pass.

- [ ] Stage 5: Event discovery, eligibility, and acquisition
      Objective: Resolve expected earnings events and their first supported publication, freeze the eligible-event and 40-event pilot manifests, and only then acquire the selected releases from EDGAR.
      Spec: R1.1–R1.5, R14.5; A §391–427; P-C2, P-C5, P-C7, P-A5; P §Stage 5 — Event discovery, eligibility, and acquisition, §Temporal definitions, §Data contracts (expected event, pilot selection), §Deterministic pilot selection, §Failure handling.
      Gap closed: R1.1, R1.2, R1.3, R1.4, R1.5, R14.5; P-C2 (the event join), P-C5, P-C7 (the freeze-before-outcomes half), P-A5; P-VF (period-window, eligibility-reason, and selection cases), P-VI.
      Consumes: the frozen Stage 4 cohort — universe manifest, membership intervals, and security-to-issuer resolution with CIK evidence; Stage 1 V1 findings; Stage 2 contracts; Stage 3 canonicalizer (content inspection for R1.2/R1.5).
      Produces: an expected issuer-period event ledger over the eight period-end quarters in `[2024-07-01, 2026-07-01)`; release discovery that keeps `period_end`, the issuer's `reported_fiscal_year`/`reported_fiscal_quarter`, `first_publication_time`, `filing_acceptance_time`, and `retrieved_at` as separate fields; a per-event eligibility decision of `eligible`, `ineligible`, or `ambiguous` with its `eligibility_reason`; a frozen eligible-event manifest with a content hash; a frozen 40-event pilot manifest whose rows each record `issuer_coverage`, `membership_boundary`, `quarter_coverage`, or `longitudinal_fill`, plus the selection seed, policy version, and eligible-event manifest hash; an opt-in live EDGAR adapter behind the shared 2 req/s limiter with its User-Agent configured outside Git; immutable raw snapshots with retrieval metadata; a per-document processing-state table including expected-but-absent documents with a `missing_reason`; offline replay from saved responses.
      Exit: the six-step order in `P §Stage 5` is enforced and tested — both manifests freeze before any acquisition, parse, retention, or theme outcome exists, and a test shows the pilot manifest unchanged after acquisition and parser statuses change (P-C7); a selected event stays selected when acquisition, parsing, extraction, or support assessment fails; releases immediately before and after a membership transition resolve to the correct side, and a same-day transition without sufficient ordering precision stays `ambiguous` with no invented time (P-C2); an issuer with several securities yields one expected event per period (P-VF); both period-window boundaries and all three eligibility reasons are covered by fixtures (P-VF); shuffled input order yields a byte-identical pilot manifest that represents every eligible issuer and all eight quarters, and the underfilled, blocked, and mandatory-coverage-overflow cases each stop or mark the pilot as `P §Deterministic pilot selection` requires (P-C5); with at least 40 eligible events the pilot holds exactly 40, every row records its `selection_reason`, and fixtures cover the membership-boundary and repeated-issuer reasons (P-VF); changing membership evidence, issuer resolution, the event corpus, or the selection policy invalidates the manifest and produces a new version and hash (P-VF); freezing the eligible-event manifest refuses unresolved issuer identity or event eligibility unless the record is retained as unresolved and excluded with its reason (P §Failure handling); event records keep `period_end`, the reported fiscal labels, `first_publication_time`, `filing_acceptance_time`, and `retrieved_at` as separate fields, and EDGAR acceptance time establishes first publication only when no earlier supported public source exists, with an unknown time staying unknown (R1.5, P-A5); offline replay of saved EDGAR responses identifies the fixture issuers' releases, including a narrative-only release and alternative exhibit numbering (R1.1/R1.2); tests hold concurrent workers at or below 2 req/s and stop on a persistent 403 without rotating identity (R1.3); the state table represents every R1.4 state from fixtures (R1.4); library output is Polars at the boundary, or V1's vacuity is recorded (R14.5).
      ROUTING: brainstorming

- [ ] Stage 6: Pilot codebook, split, and gold-set protocol
      Objective: Take the frozen pilot manifest as given, split it by issuer and time, approve codebook v0, and validate annotations, so hand-coding runs while Stages 7–10 are built.
      Spec: R9.2, R9.7, R12.1–R12.6; R13.1 (release-identification labels); D2, D4; P-C5, P-C7.
      Gap closed: R9.2, R9.7, R12.1, R12.3, R12.4 (acquisition-outcome classes as observed coverage, D4), R12.5 (out-of-manifest fixtures and in-document hard-negative claims, D4); R12.6 (limitation, D2).
      Consumes: the frozen Stage 5 pilot manifest — this stage no longer selects the sample; Stage 3 canonical documents (gold spans bind to that canonicalization version); Stage 5 event bundles, issuer and fiscal-period identity, and processing states.
      Produces: a codebook contract with R9.2's fields; codebook v0 drafted from training-partition bundles only and approved in a decision record; a gold-annotation contract and validator, the contract also carrying hard-negative claims drawn from confusable periods, issuers, and sections of the frozen pilot documents (R12.5, D4); an issuer-and-time split over the frozen manifest; an observed failure-class coverage report over that manifest; curated hard negatives held as fixtures outside the manifest. Gold spans name their canonical version; a later version re-anchors them before reuse, never mutates them.
      Exit: a test places each bundle, with all copies and revisions, in exactly one issuer-and-time split (R12.1/R12.3); the coverage report states the observed count of unavailable, restricted, and parser-failure bundles in the frozen manifest, and a missing class is reported as a coverage gap, never repaired by reselecting; the no-theme count joins the report at Stage 11, once annotation is complete (R12.4, D4); a test shows the split and the report changing no row of the pilot manifest (P-C7); curated hard negatives exist as fixtures outside the pilot manifest, and the annotation validator accepts hard-negative claims (R12.5, D4); codebook v0's decision record names its training-partition discovery corpus (R9.2/R9.7); annotations on at least three bundles, including release-identification labels, pass the validator; the single-annotator limitation is recorded (R12.6, D2).
      ROUTING: brainstorming

- [ ] Stage 7: Evidence selection and verification
      Objective: Extract quote-claim candidates by pointer selection over every analysis-eligible element, keeping only code-verified spans.
      Spec: R5.1, R6.1 (before storage), R6.2, R10.1, R10.2, R14.1, R14.6, R14.7, V11.
      Gap closed: R5.1, R6.2, R10.1 (default path), R10.2, R14.1, R14.6; R14.7/V11 (tool-call and verification-bypass cases).
      Consumes: Stage 2 validator and locators; Stage 3 canonical fixtures only — not Stage 5.
      Produces: a themes extractor visiting every eligible element; a model-adapter interface with a fake adapter, response replay, and an R14.6-keyed cache; one open-weight local adapter behind the `live` marker, its weight license recorded; an auditable rejection record.
      Exit: offline fake-model runs over Stage 3 fixtures retain only R6.1-valid quotes, and every rejection records a reason after bounded retries (R5.1/R6.2); a coverage test shows every eligible element visited and no top-k discovery path (R10.1/R10.2); a test shows changing any R14.6 key component misses the cache (R14.6); the default suite makes no network or billable call (R14.1); the V11 fixture triggers no tool call and cannot bypass R6.1 (R14.7/V11).
      ROUTING: brainstorming

- [ ] Stage 8: Semantic support assessment
      Objective: Judge whether each verified span supports its claim under the theme definition, as signals that can only reject or flag.
      Spec: R8.1–R8.6, V4; R6.1 (before support judgment).
      Gap closed: R8.1, R8.3, R8.5, V4; R8.2 (primary scorer; alternative wired).
      Consumes: Stage 7 verified quote-claim pairs.
      Produces: a support assessor pairing an open-weight entailment score (primary) with a model-judge signal using order-swapping and cross-family judges; RG §3's alternative behind the same interface; AUC-ROC and accepted-claim precision computation; a V4 decision record with checkpoint identity in the manifest.
      Exit: the V4 record confirms the primary scorer's weight license and a self-hosted run with no API call (V4/R8.2); fixture pairs misattributed to a competitor, a prior period, or a negation are rejected or flagged (R8.1); scores persist as versioned signals, never verdicts (R8.3); a judge output editing evidence or promoting an invalid span is refused (R8.5).
      ROUTING: brainstorming

- [ ] Stage 9: Deductive coding
      Objective: Assign verified, supported spans to themes of a frozen approved codebook as versioned multi-label rows, routing non-matches to a novelty queue.
      Spec: R9.1 (deductive), R9.3, R9.4, R9.6, R9.8, R9.9, R14.7, V11.
      Gap closed: R9.1 (deductive), R9.3 (queue), R9.4, R9.6, R9.8, R9.9; R14.7/V11 (codebook case).
      Consumes: Stage 6 codebook contract and approved v0; Stage 7 verified spans; Stage 8 support decisions.
      Produces: an open-weight classifier emitting typed multi-label output with bounded retries against a frozen codebook version; assignment rows carrying codebook identifier and version; a novelty queue for human adjudication.
      Exit: fake-model replay exercises typed multi-label output with bounded retries against frozen v0 (R9.1/R9.8); one quote supporting two themes yields two rows sharing its quote identifier (R9.9); an unmatched candidate enters the novelty queue and no new theme identifier appears (R9.3); rows carry codebook identifier and version, and a mixed-version comparison is refused (R9.6); cluster labels and sentiment never populate theme fields (R9.4); the V11 fixture leaves the codebook unchanged (R14.7/V11).
      ROUTING: writing-plans

- [ ] Stage 10: Coverage-aware aggregation and cited export (theme vertical slice)
      Objective: Produce analytical rows, coverage-aware prevalence, and a source-linked report that carry one release end to end.
      Spec: R2.3, R3.4 (headline exclusion), R6.1 (before export), R7.1, R7.2, R11.1–R11.6, V5, V8, V10.
      Gap closed: R2.3, R3.4, R7.1, R7.2, R11.1, R11.2, R11.3, R11.4, R11.5; R11.6 (release roles); V5, V8, V10.
      Consumes: Stage 3 canonical documents and masks; Stage 5 processing-state table; Stages 7–9 verified, supported, coded assignments.
      Produces: Polars/Parquet rows at the R11.1 grain; prevalence tables printing numerator, denominator, unit, and restrictions; passage links paired with immutable snapshots; a cited report; the V8 offline end-to-end test.
      Exit: V8 passes with no network or credentials, from raw fixture to cited report (V8/R11.1); V10 reproduces hand-computed numerators and denominators across unavailable, restricted, failed, and no-theme documents, and reports missing-transcript coverage (V10/R11.2/R11.3/R2.3); a test shows masked spans absent from headline prevalence yet present in audit output (R3.4); tests show a disclosure's copies counted once and issuers weighted equally (R11.5/R11.4); release rows carry `not_applicable` speaker roles (R11.6); V5 records each target browser's highlight behavior, and the snapshot renders the span wherever the link fails (V5/R7.1/R7.2).
      ROUTING: writing-plans

- [ ] Stage 11: Feasibility pilot and threshold calibration
      Objective: Run the pipeline against the hand-coded pilot, calibrate the judge, and gate the metrics the pilot can estimate.
      Spec: R8.2, R8.4, R8.6, R12.2, R12.4, R12.5, R12.7, R12.8, R12.10, R13.1, R13.3, V6; D1, D2, D4.
      Gap closed: R8.2, R8.4, R8.6, R12.2, R12.7, R12.8, R12.10; R13.1/V6 (per D1); R12.4 (no-theme count) and R12.5 (hard-negative scoring), per D4.
      Consumes: the frozen Stage 5 pilot manifest, split by Stage 6 and fully annotated by the user; the Stage 6 D4 coverage report; at least 50 user support labels on Stage 8 outputs (D2); the Stage 10 pipeline.
      Produces: implementations of every R13.1 metric plus retention, stability, and AUC-ROC; a pilot report with issuer- or event-level uncertainty; a judge-calibration report with its pre-registered floor; the V6 decision record of gates.
      Exit: the pilot report gives every R13.1 metric's observed distribution with event-level intervals, labeled feasibility-only (R12.2/R12.7); the V6 record gates only pilot-estimable metrics, marks rare-theme recall, sector prevalence, and source-selection bias descriptive-only, and is committed before any configuration comparison (V6/R13.1, D1); judge agreement with the user's labels is reported against its pre-registered floor, with AUC-ROC for both scorers (R8.4/R8.6/R8.2); a reject-everything configuration fails the suite (R12.8); k-run stability is computed with replay bypassed (R12.10); the D4 coverage report gains the observed no-theme count over the fully annotated manifest (R12.4, D4); pilot metrics include the annotated hard-negative claims (R12.5, D4).
      ROUTING: brainstorming

- [ ] Stage 12: Inductive and hybrid codebook
      Objective: Discover candidate themes offline from training-partition evidence, approve them as a new codebook version, and re-code the declared corpus.
      Spec: R9.1 (inductive, hybrid), R9.3 (approval), R9.5, R10.3, R12.3.
      Gap closed: R9.1, R9.3, R9.5, R10.3; `embeddings` extra row.
      Consumes: Stage 9 coding and novelty queue; Stage 11 splits and metrics.
      Produces: an offline clustering aid outside the application pipeline; consolidation preserving evidence pointers and contradictory claims; an approval path from candidate codebook to a new frozen version; a hybrid mode; re-coding under the new version.
      Exit: a test shows candidate themes derive from training-partition data only (R12.3); a test shows consolidation keeps every evidence pointer and contradictory claim (R10.3); approval is recorded in a decision record and re-coded rows carry the new version (R9.1/R9.3); an import check shows no clustering dependency reachable from the application pipeline (R9.5, `embeddings` row).
      ROUTING: brainstorming

- [ ] Stage 13: Transcript extension (conditional on V7)
      Objective: Add lawfully usable transcripts with speaker roles, or record that no candidate corpus qualifies.
      Spec: R2.1, R2.2, R4.1 (speaker turns), R11.6, V7; D2.
      Gap closed: R2.1, R2.2, V7; R11.6 (management/analyst split).
      Consumes: Stages 3 and 5; Stage 10 aggregation; Stage 11 metrics.
      Produces: a V7 record per candidate corpus; if one qualifies, a rights-gated transcript adapter storing locators and local features where terms forbid redistribution, and speaker turns with role and attribution status.
      Exit: V7 records each candidate's license, redistribution terms, and diarization accuracy against a user-labeled sample (V7); if none supports the management/analyst split, R2.2 is recorded as failed and the stage parks; otherwise fixture transcripts yield role-attributed turns, unresolved roles stay `other`/`unknown`, and restricted text is never redistributed (R2.1/R2.2/R11.6).
      ROUTING: brainstorming

- [ ] Stage 14: Configuration comparison and held-out evaluation
      Objective: Run R12.9's ablations against the V6 gates, freeze one selected configuration, and evaluate it once on the held-out split.
      Spec: R5.2, R10.1 (whole-document arm), R10.2 (retrieval-only arm), R11.5 (dedup arm), R12.9, R13.3; D1.
      Gap closed: R5.2, R12.9, R13.3.
      Consumes: Stage 11 gates, metrics, and splits; Stage 12 inductive and hybrid codebooks; Stage 13 transcripts if shipped, else that arm is recorded as not run.
      Produces: a generate-then-verify comparator; whole-document and retrieval-only modes; an ablation report with quality, latency, tokens, and cost per arm; a selection decision record; one held-out evaluation report.
      Exit: a test shows generate-then-verify rejects every unresolvable candidate and never repairs wording (R5.2); the ablation report covers every available R12.9 arm and adjudicates against V6's gates (R12.9); the selected configuration is frozen by hash and evaluated on the held-out split once, a second run under the same protocol is refused, and the report is labeled feasibility-level (R13.3, D1).
      ROUTING: writing-plans

- [ ] Stage 15: Full DJIA eight-quarter run
      Objective: Run the configuration frozen by Stage 14 over every eligible event in the complete DJIA manifest, reporting the observed corpus shape rather than forcing it to a target.
      Spec: P-C6, P-A15; P §Stage 15 — Full DJIA eight-quarter run; R1.3, R1.4 (access policy, processing states); R11.1–R11.3 (grain, denominators, coverage), R12.10 (replay bypass), R14.6 (cache keys), R14.1 (no billable call on the required path).
      Gap closed: P-C6, P-A15.
      Consumes: the frozen Stage 5 expected-event ledger and eligible-event manifest; the Stage 5 EDGAR adapter, shared limiter, and processing-state table; the Stage 3 canonicalizer; the Stage 14 selected configuration, frozen by hash; Stage 11 metrics and the Stage 10 export path; cached pilot artifacts whose R14.6 cache key still matches. It reselects nothing.
      Produces: acquisition and canonicalization of every eligible release not already acquired for the pilot, under the shared 2 req/s limiter, each outcome recorded in the processing-state table; analytical outputs over every eligible event at the R11.1 grain, each row carrying universe, corpus, codebook, schema, and run versions; a coverage report giving expected, eligible, acquired, parsed, processed, failed, partial, and completed-no-theme counts by issuer and period; a reconciliation of the observed event count against the approximate `30 × 8` shape that attributes every departure to a membership transition or a missing event.
      Exit: every expected-event ledger row carries an eligibility and coverage status, and every eligible event a terminal or resumable processing status (P-A15); ineligible and ambiguous rows appear in coverage and status output without being processed as eligible, alongside the failed, unavailable, partial, and completed-no-theme cases; a test shows compatible pilot artifacts reused without producing duplicate accepted rows; a test shows the run performing no reselection, and the reported count is the observed count, never forced to equal `30 × 8` (P-C6); the coverage report names the transitions and missing events behind any departure from that shape; the default suite makes no network or billable call, and live acquisition runs only behind the `live` marker (R1.3, R14.1).
      ROUTING: writing-plans — `specs/point-in-time-djia-cohort.md` is this stage's spec; it needs no brainstorming pass.

- [ ] Stage 16: Hosted quality ceiling (optional)
      Objective: Measure a hosted frontier model's quality ceiling on a frozen subset within the $100 authorization.
      Spec: R14.2; D3.
      Gap closed: R14.2.
      Consumes: Stage 14 frozen configuration; Stage 11 metrics.
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

A stage routed straight to writing-plans (Stages 2, 9, 10, 14, 16) has no stage
spec of its own: its plan header carries the Roadmap line directly, and its
COMPLETE line is appended to the Rollout section of
`specs/evidence-linked-theme-extraction.md`, which is the stamp a resume reads
for those stages. Stages 4 and 15 are also routed to writing-plans but do have a
stage spec — `specs/point-in-time-djia-cohort.md` — so their COMPLETE lines
follow the normal stamp convention against that file.

## Completion

Retire this roadmap only after a conformance audit of the accumulated system:
re-run the gap rubric over every row above — including the 13 `P-*` rows from
`specs/point-in-time-djia-cohort.md` — with evidence per verdict (implementing
stage and plan, `> Deviation:` notes, deferred entries). Each
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
- **Stage 13** parks if V7 finds no qualifying corpus; **Stage 16** is optional.

Not staged because no requirement asks for them: the learning path's LangGraph,
DSPy, and CrewAI exercises (R14.4). Out of scope per the spec: importance
ranking, taxonomy content, company enrichment, and prompt-optimizer compilation.
