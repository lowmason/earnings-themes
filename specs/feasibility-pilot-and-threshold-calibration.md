# Feasibility pilot and threshold calibration

> For agentic workers: REQUIRED NEXT SKILL: writing-plans. This is the stage spec
> for Stage 11 of `specs/evidence-linked-theme-extraction-roadmap.md`. Plan it as two
> plans, in order: plan A (§Plan A) first, and plan B (§Plan B) only after plan A has
> merged. Never plan both in one plan, and never plan a later stage with it.

Stage 11 runs the pipeline over the hand-coded pilot for the first time. It calibrates
an assignment policy against the user's support labels, measures every R13.1 metric
with event-level uncertainty, and records V6's gates. Plan A builds the machinery
without opening pilot text. Plan B runs it once the 28 train and dev bundles are
signed.

It closes R8.2 (the quality comparison of both scorers), R8.4, R8.6, R12.2, R12.7,
R12.8 and R12.10 of `specs/evidence-linked-theme-extraction.md`; R13.1 and V6 as D1
narrows them; and R12.4's no-theme count and R12.5's hard-negative scoring, per D4.
It selects no production model or policy, compares no configurations, and reads no
test bundle.

**This spec tightens R8.4 without amending it.** R8.4 lets V6 set the agreement floor's
number from the pilot. Here the number is preregistered before any agreement is
computed (FP9). V6 records that preregistered number as the gate.

Locators:
- **`A §n`** is `AGENTS.md`, by line.
- **`Rn`** and **`Vn`** are the theme spec's requirements and verification items, and
  **`D1`**–**`D5`** the roadmap's decisions.
- **`GSn`** are the Stage 6 spec's decisions
  (`specs/completed/pilot-codebook-split-and-gold-set-protocol.md`), **`ESn`** the
  Stage 7 spec's (`specs/completed/evidence-selection-and-verification.md`), and
  **`SSn`** the Stage 8 spec's (`specs/completed/semantic-support-assessment.md`).
- **`P16-n`** are plan 16's deferred items (`specs/deferred_items.md`,
  `16-pilot-codebook-split-and-gold-set-protocol`).
- **`RC §7`** is the source review the theme spec cites for κ's expected range.
- **`FPn`** are this spec's decisions.

Designed 2026-10-11 in a brainstorming session on branch
`stage-11-feasibility-pilot-design`, from `main` at `cff6313`. The session opened no
pilot text, no kept draft, and nothing under `data/`. At that point 3 of the 28 train
and dev bundles were signed, and no dev ledger row existed.

## Decisions

Taken with the user on 2026-10-11. Rows marked *(design)* were proposed in the design
sections and approved with them.

| ID | Decision |
| --- | --- |
| FP1 | **Two plans, one spec.** Plan A builds and tests everything that needs no pilot text, while gold drafting continues. Plan B runs the pilot. Steps B1 and B2 may start as soon as plan A merges. B3 onward waits for the visibility gate (FP2). |
| FP2 | **The visibility gate.** No pipeline output exists for any pilot bundle until all 28 train and dev bundles are signed and committed, each dev bundle after its ledger row (GS19). So neither the user nor a drafting session sees a model's reading of a bundle before it is signed (GS13, GS19, R12.6). Test and excluded events are never run (GS18). |
| FP3 | **The user runs every live step.** Any command that loads a model or reads pilot text runs in the user's own terminal. It prints IDs, counts, reasons and metric figures only. A refusal prints its reason and IDs. Agents see only that output. |
| FP4 | **Partition roles.** Train (20 events) is where calibration happens: the labels that fit the policy, the judge floor test, and the policy selection. Dev (8 events) evaluates the frozen baseline once. Its distributions set V6's gates, and its held-out labels report held-out quality. Train figures are reported and marked in-sample. |
| FP5 | **Baseline models.** Gemma 4 31B-it (ADR 0004's verified checkpoint) extracts and classifies. ADR 0006 records it as the pilot baseline only. The production model stays open, and Stage 14 may compare models. |
| FP6 | **Judges.** Two open-weight, self-hosted judges, from two families, neither of them Gemma. ADR 0006 names their checkpoints after a V4-style check: a weight license that permits this use, self-hosting with no API call, a fit in the machine's 36 GB, and hashed weights. This spec names no checkpoint. |
| FP7 | **Prompts as shipped.** `pointer-1`, Stage 9's classifier prompt and Stage 8's judge prompt run unchanged. A prompt revision informed by train gold is a Stage 14 arm, measured against V6. |
| FP8 | **Support labels.** The user writes them unaided, never seeing a score, a judge answer, or the extractor's identity. 70 targets are sampled from train (at most 5 per event) and 24 from dev (3 per event), never by score. The labels are committed as IDs and answers only (§Labels). Calibration needs at least 50 usable train labels (R8.4). |
| FP9 | **Preregistration,** committed before any pilot output exists (§Preregistration). It fixes: the floor statistic (Cohen's κ, with Gwet's AC1 reported alongside), its unit (an event-clustered bootstrap 90% lower bound), and a numeric floor the user picks from RC §7's 0.3–0.6 range; the policy menu and its selection rule; the sampling plan; the bootstrap's seed and resample count; and V6's gate rule. |
| FP10 | **A preregistered policy menu.** Three or four transparent candidates are fit on train labels, and the selection rule picks one. It is frozen before dev is run (§Calibration). |
| FP11 | **Fresh calls.** A `fresh` mode on each of the three cache classes, alongside `live` and `replay`, covering their four kinds of cached reply. It always dispatches, never reads, and writes to a directory scoped to the stability run. Its mode and run ID are recorded in run provenance. |
| FP12 | **Stability.** k = 3 fresh runs over dev's 8 events, at the baseline's own settings. A near-perfect result at temperature 0 is labelled as runtime nondeterminism only, not robustness to sampling. A sampled-temperature arm is left to Stage 14. |
| FP13 | **Comparison grain.** Themes are scored as event × theme presence. Evidence is scored in pointer units (ES12). Character Jaccard is reported as a secondary figure. |
| FP14 | **Hierarchy credit.** Exact-theme F1 is gated. A level-one roll-up F1 is secondary. A sibling never earns credit. |
| FP15 | **V6's gate rule.** Each gate is the dev baseline's 90% bootstrap lower bound. A configuration passes when its dev point estimate meets every gate. Two rules hold whatever the bound: gold-evidence recall must be strictly above zero, and an undefined metric (`None`) fails its gate. The judge floor is the preregistered number. |
| FP16 | **The independent record stays local.** Its anchored form is never committed. Only per-event figures and the ledger hash are committed, so P16-3 never applies to a pointer file. |
| FP17 | **Labels are committed,** as IDs, hashes and answers, with no free text, so calibration reproduces from committed files. |
| FP18 | *(design)* **Package placement.** `earnings_themes.evaluation` is pure and imports only `earnings-core` and themes records. The commands extend the existing `pilot` group. Coverage v2 stays in ingestion's `build_coverage`, and the app supplies its `NoThemeCount` rows, so ingestion never reads gold. |
| FP19 | *(design)* **No pytest over pilot text.** The pilot runs through commands. So plan 12's failure-output guard, whose trigger is a live test over pilot text, is never triggered. A crashed run resumes from its cached replies, so plan 12's partial-`RunRecord` item is not triggered either. |
| FP20 | *(design)* **Gold conventions for scoring** (§Metrics): a cell whose only evidence is `uncertain` is left out and counted; a `tie_group` is one either-of cell. |
| FP21 | *(design)* **Two answers per label.** Each target gets the user's `claim_support` and `theme_fit` answers, the judge reply's two questions. The joint label is both holding. MiniCheck and DeBERTa only judge claim support (`score_requests` uses the claim alone as the hypothesis), so their AUC uses `claim_support`. The policy and the judge floor use the joint label. |
| FP22 | *(design)* **Phase by phase, judges resident together.** Stage 8 runs a target's four trials back to back, alternating families. So `pilot pass` runs all extraction, then all classification, then support, and Gemma is unloaded before support. B1's memory check is both judges and MiniCheck resident at once, within 36 GB. That caps each judge at roughly 14B parameters at Q4, which the user accepted. A judge family that then fails the floor leaves the scorer-only candidate, itself a finding. A Stage 8 schedule batched by family, which would allow one larger judge at a time, was considered and declined. |
| FP23 | *(design)* **Replay reuses the pass's stored runs.** Support cache keys bind the extraction run's record (`support/cache.py:107`), so a re-run extraction would miss every support entry. `pilot run` therefore never re-extracts. It reuses the pass's stored extraction, coding and support runs through the workflow's stored-run reuse, and dispatches nothing. Replay needs no model server running. |

## Scope

In scope:
- plan A's machinery (§Plan A);
- plan B's run, labels, calibration, report and V6 record (§Plan B);
- P16-2, and the plan 10 refusal of a kept draft that repeats an ID;
- coverage v2's no-theme count for train and dev (R12.4, D4).

Out of scope:
- **the 25 unsigned bundles.** Signing them is plan 9's Task 19, with GS19 for dev, and it is plan B's precondition, not this stage's work;
- **the production model and policy, and configuration comparison:** Stage 14 (R13.3);
- **prompt revision:** a Stage 14 arm (FP7);
- **the test partition:** Stage 14 (GS18);
- **gates for rare-theme recall, sector prevalence and source-selection bias:** descriptive or not estimated (D1);
- **codebook changes:** Stage 12. **Concurrent workers:** Stage 15. **Hosted calls:** Stage 16.

## Inputs

- **From Stage 6:** `load_pinned`, `load_split`, `load_coverage`, `load_gold`, and `load_hard_negatives`.
  - The signed gold sits under `evaluation/djia-2024q3-2026q2/pilot-v1/gold/`, one file per event (P9-3). Its header carries `no_theme` (P9-4) and the GS5 counts (`accepted`, `edited`, `rejected`, `added`).
  - The dev ledger, `evaluation/djia-2024q3-2026q2/pilot-v1/independent-pass.toml`, read through `load_ledger` and `ledger_problem`.
  - `load_independent` and `check_independent` (`annotation.py`).
  - The kept drafts under `data/runs/gold/drafts/`, for GS5. Only a counts-only program reads them.
- **From Stage 5:** each document's kept attempt outcome (`confirmed` or `not_confirmed`, `events/states.py`), as the system's release identification.
- **From Stage 7:** `extract_run`, `read_run`, and `CachedAdapter` with `CacheMode`.
  - `pointer-traversal/1` units (ES12) are the evidence grain.
  - Its quotes are whole units, unlike gold's partial quotes (Stage 7 spec, §The difference from P9-19).
- **From Stage 8:** `assess_run` (one scorer per run), `SupportCache`, `read_support_run`, `reverify_support_run`, `auc_roc`, and `accepted_claim_precision`.
  - The judge reply's `claim_support` and `theme_fit`, and the four family × presentation trials.
  - The review outcomes `refused`, `incomplete`, `flagged`, and `assessed`.
  - `MiniCheckScorer` (primary, ADR 0005) and `DebertaScorer` (alternative), each behind `LocalScorerConfig`.
- **From Stage 9:** `AssignmentPolicy.evaluate(DecisionInput) -> PolicyVote`, `PolicyReference` (whose `kind="calibrated"` needs a `calibration_reference`), `CodingCache`, `ClassifierBinding`, and `JudgeBinding`.
- **From Stage 10:** `run_theme_workflow` and `WorkflowRuntime`, with scope `research`.
  - Terminal or partial reprocessing needs an explicit policy (plan 15 §Handoffs).
  - Its self-or-descendant parent rule.
- **From ingestion:** `build_coverage` and its declared `NoThemeCount` (`events/coverage.py:102`).

## Order of work

```text
Plan A (no pilot text) ── merge ──► B1 ADR 0006 + smoke ─► B2 preregistration
                                                    │
                     visibility gate (FP2): 28 signed, 8 ledger rows
                                                    ▼
B3 train pass ─► B4 train labels ─► B5 calibrate + freeze ─► B6 train and dev runs, dev labels
                                                                    ▼
                         B7 stability, independent pass, coverage v2, GS5
                                                                    ▼
                                      B8 pilot report ─► V6 record (ADR 0007)
```

Each step's commit lands before the next step starts. B8's V6 record is committed
before any configuration comparison (R13.3).

## Plan A

Plan A opens no pilot text and loads no model. Its tests use invented records,
Stage 1's committed fixtures, the synthetic cohort and acquisition, and scripted
adapters. If writing-plans finds plan A too large for one plan, A6 and A7 form a first
slice. They are small, touch only gold and coverage, and A6(1) helps the remaining
bundles.

### A1. Fresh-call mode

- `fresh` joins `live` and `replay` on three classes: extraction's `CachedAdapter`, `CodingCache`, and `SupportCache` (its scorer and judge entries).
- `fresh` always dispatches and never reads, even on a key that is already cached.
- It writes each reply under `<cache>/fresh/<stability_run_id>/`. So it never collides with the main cache's bytes, and a stability run replays afterwards from its own directory (R14.6).
- Keys are unchanged.
- Every run record carries `cache_mode` and, under `fresh`, the stability run ID.
- Tests: a fully populated cache gives zero hits under `fresh`; dispatches equal requests; a later `replay` over the fresh directory reproduces the run.

### A2. Live runtime assembly

- A builder makes a `WorkflowRuntime` for scope `research` from `config/models/*.toml`: the extractor and classifier, the scorer, and two judges.
- It verifies every weight hash and runtime identity.
- It refuses a panel that breaks Stage 8's family rules before any dispatch.
- It chooses no model. ADR 0006 writes the configs (B1).
- A second support run, with `DebertaScorer` and the same judges, gives the alternative scorer's signals. It shares the first support run's stored extraction run. `SupportPolicy` carries no scorer identity, so its judge calls hit the cache in `live` mode.
- Token counters are local tokenizers, never a server call, so constructing the runtime for replay needs no model server.
- Tests use scripted transports, and a replay test uses transports that fail on any call.

### A3. `earnings_themes.evaluation`

A pure package that imports only `earnings-core` and themes records, never ingestion or
httpx. It holds:
- **alignment:** gold quotes, and run quotes, mapped to pointer units by character overlap, per document;
- **the metrics** of §Metrics;
- **the bootstrap:** event-clustered, with a seed and resample count taken from the preregistration, and percentile intervals;
- **agreement:** Cohen's κ, Gwet's AC1, and Fleiss' κ;
- **the gate evaluator:** reads a gates file and a metric report, and returns pass or fail per gate. Gold-evidence recall must be strictly above zero whatever its gate, and a `None` metric fails, so a reject-everything configuration fails (R12.8).

Known-answer tests use hand-computed figures for every metric, including the
`uncertain`, `tie_group` and macro-exclusion conventions. The bootstrap is
deterministic under its seed. A test shows a reject-everything policy failing invented
gates.

### A4. Support labels

- **`SupportLabel`** is a strict record: `target_id`, `target_input_hash`, `partition`, `claim_support` (`supported`, `unsupported`, `unsure`), `theme_fit` (`fits`, `does_not_fit`, `unsure`), and `labelled_on`. It has no free-text field.
- **The sampler** is deterministic, from the preregistration's seed.
  - Its caller filters the pool to `assessed` and `flagged` targets, leaving out `refused` and `incomplete`. The sampler itself takes only target IDs, event IDs and proposed themes.
  - It round-robins across events in seeded order, one target at a time, until it reaches the partition's size or every event is at its cap or exhausted. Within an event, it round-robins across proposed themes in seeded-hash order.
  - Its signature takes no score, judge answer or outcome, so it cannot sample by any of them.
- **The label view** is local markdown under `data/runs/pilot/labels/views/`: each target's claim, its quotes in context, and the theme's definition. A sentinel test shows it never contains a score, a judge answer, a flag, or the extractor's identity.
- **`labels check`** refuses a label whose target hash doesn't match its support run, and a label set that differs from the deterministic sample.

### A5. Preregistration and calibration

- **`Preregistration`** is a schema with a loader that rehashes the committed file.
- **`calibrate`** refuses unless the committed preregistration matches its recorded hash and the train labels hold at least 50 usable joint labels.
- It runs the floor test, fits and selects the policy (§Calibration), and writes a `CalibrationArtifact`.
- **`CalibratedPolicy`** implements `AssignmentPolicy` from the artifact, with `PolicyReference(kind="calibrated", calibration_reference=<the artifact's hash>)`.

### A6. Gold-side fixes

1. `build_gold` and `build_curated` refuse a kept draft that repeats a quote, claim or fixture ID, with a test (plan 10's deferred item).
2. `check_independent` refuses a codebook that isn't approved, as `validate_gold` does, with a test (P16-2a).
3. `verify_independent(event)` checks the local record against its ledger hash, checks it with `check_independent`, and anchors it and the kept draft in memory. It returns the comparison figures and writes nothing. Its tests use invented records (P16-2b).
4. A counts-only recheck rebuilds each committed file's GS5 counts from its kept draft, and reports any mismatch by event and field.

### A7. Coverage v2

- `pilot coverage --version 2` reads each signed file's `no_theme` and passes `NoThemeCount` rows for train and dev to `build_coverage`.
- It refuses until all 28 train and dev files are signed.
- Coverage v2 reproduces byte for byte on the synthetic cohort.

### A8. Commands

These extend the existing `pilot` group:

| Command | Does |
| --- | --- |
| `pilot pass --partition train\|dev` | Composes Stages 7–9's libraries in `live` mode, phase by phase (FP22): extraction, classification, then both support runs. Writes local runs and no Stage 5 state. Makes no decision. |
| `pilot run --partition train\|dev` | Runs `run_theme_workflow` under the calibrated policy, reusing the partition's stored pass runs (FP23). Refuses without a calibration artifact, or if any request would dispatch. |
| `pilot run --partition dev --fresh <id>` | One stability run: the pass and the decisions under the frozen policy, with all four reply kinds `fresh`. Writes no Stage 5 state. |
| `pilot labels sample\|view\|check --partition train\|dev` | §Labels. |
| `pilot calibrate` | §Calibration. |
| `pilot independent` | A6's comparison for each dev event, printing figures only. |
| `pilot report` | §Metrics, for each partition, into `report-v1.json`. |
| `pilot gates` | FP15's rule over the dev report, into `gates-v1.toml`. |

Every command refuses test and excluded events and prints only IDs, counts, reasons
and figures. A sentinel test per command plants marker text in invented inputs and
shows that it never prints.

The workflow's stored-run reuse (`theme_workflow.py`) now requires a stored coding run
to have been recorded in `replay` mode. Plan A widens that to `live`, provided every
other identity it checks still matches. A test shows reuse of a `live` pass dispatching
nothing. A `fresh` run is never reused by `pilot run`.

### A9. Wording guard and data dictionary

- `tests/integration/test_stage6_wording.py` gains globs for `evaluation/*/pilot-v*/*.toml`, `*.json` and `labels/*.toml`. The first also scans the ledger, which closes P16-3. This edits the user's gate file, through the plan.
- `docs/data-dictionary.md` gets a row for every new record, and `test_data_dictionary.py` enforces it.

## Plan B

1. **B1. ADR 0006 and the smoke.** May run once plan A merges.
   - The session checks candidate model cards for the two judges (FP6) and for DeBERTa. The user chooses and downloads them, and confirms that both judges and MiniCheck fit in 36 GB resident at once (FP22), and that Gemma fits alone.
   - ADR 0006 records, for each model: its role, model ID, weights' SHA-256, runtime and version, and its license, quoted with URL and date. It records Gemma as the baseline extractor and classifier only (FP5).
   - The user then runs one live smoke through A2's runtime over one Stage 1 fixture, never pilot text. Its per-call timings set plan B's request and token ceilings.
2. **B2. Preregistration.** May run before the gold gate. The user picks the numbers, and `preregistration-v1.toml` is committed on its own, before B3 (§Preregistration).
3. **B3. The train pass.** After the visibility gate (FP2), the user runs `pilot pass --partition train`.
4. **B4. Train labels.** `pilot labels sample` and `view`. The user labels unaided, then runs `pilot labels check`, and the labels are committed.
5. **B5. Calibration.** `pilot calibrate` writes `calibration-v1.json`, which is committed. The baseline configuration's hash is frozen in it.
6. **B6. The runs.** `pilot run --partition train` gives train's in-sample decisions. `pilot pass --partition dev`, then `pilot run --partition dev`, is the first dev output. Dev labels are then sampled, written, checked and committed (24 targets).
7. **B7. Dev evaluation.**
   - Three `pilot run --partition dev --fresh <id>` runs.
   - `pilot independent`.
   - `pilot coverage --version 2`, committed.
   - A6's GS5 recheck, which must report no mismatch before the shares are reported.
8. **B8. The report and V6.**
   - `pilot report` writes `report-v1.json`, and `docs/verification/pilot-v1-feasibility.md` gives its prose and tables, every figure labelled feasibility-only (R12.2).
   - `pilot gates` writes `gates-v1.toml`.
   - ADR 0007, the V6 decision record, cites both. It records the gated metrics, the descriptive-only metrics, those not estimated, and the judge floor. The user approves it, and it is committed before any configuration comparison.
   - The gate evaluator is rerun against `gates-v1.toml`, with the reject-everything case.

## Preregistration

`evaluation/djia-2024q3-2026q2/pilot-v1/preregistration-v1.toml`, committed alone
before B3, in the manner of `expirements/parser-fidelity/layout1-preregistered.toml`.
It holds no text. It fixes:
- **the floor:** Cohen's κ between each judge family's binary verdict and the joint label, over every usable label. The verdict is 1 when the family's consensus supports (§Calibration) and 0 otherwise, so an uncertain consensus counts as not supporting and cannot shrink the population. The uncertain count is reported alongside. A family's 90% event-bootstrap lower bound must meet the user's number, picked from RC §7's 0.3–0.6 range. Gwet's AC1 is reported alongside, never gated;
- **the floor's consequence:** a family below it is excluded from every candidate's rule;
- **the menu:** each candidate's exact rule, its fitted cutoffs, and the cutoff grid;
- **the selection rule:** the label-recall floor ρ, the objective, and the tie-break;
- **the sampling plan:** the seed, the per-partition sizes and caps (FP8), the target pool, and the extension rule if fewer than 50 train joint labels are usable;
- **the bootstrap:** its seed, resample count, and the 90% percentile interval; how a resample with an undefined metric is handled; and what a gate becomes when a dev interval is undefined, which is likely for macro F1 and dev precision;
- **V6's rule:** FP15, and the list of gated metrics (§Metrics).

## Labels

- For each sampled target, the user answers two questions (FP21), reading only the label view:
  - does the cited evidence support the claim, with its attribution, time, scope and polarity;
  - does the claim fit the theme's definition and its inclusion and exclusion rules?
- `unsure` is allowed for either answer. It is excluded from every statistic and counted.
- The joint label is 1 when both answers are positive, 0 when either is negative, and left out otherwise.
- The committed file is `evaluation/djia-2024q3-2026q2/pilot-v1/labels/support-labels-v1.toml`.
- The user writes labels into a local working file, which `labels check` validates and copies.
- Train and dev labels share the file, distinguished by `partition`. Dev labels are added in B6.

## Calibration

**A family's consensus** on a target is `supports` when both of its presentations
answer `supported` and `fits`. It is `opposes` when both answer `unsupported` or
`does_not_fit`. Otherwise it is uncertain.

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

**Fitting and selection.**
- Each candidate's cutoff maximises train labelled precision (`accepted_claim_precision`, label task `joint_support`) subject to label recall ≥ ρ.
- The selection rule picks the candidate with the highest such precision. A tie goes to the candidate using fewer signals.
- If no candidate meets ρ, the artifact records `no_candidate`. No policy is bound, every target stays in review, and the report and V6 record say that no configuration passes. That is a feasibility finding, not an error.

**The artifact,** `calibration-v1.json`, holds no text. It holds:
- the preregistration hash and the label file's hash;
- every candidate's fitted cutoffs and train figures;
- each family's κ, AC1, interval and floor verdict;
- the selection;
- AUC-ROC for MiniCheck and DeBERTa against `claim_support`;
- the frozen configuration hash, over the models, prompts, policy and ceilings.

## Metrics

**General rules.**
- Each metric is computed per partition, with a point estimate and a 90% event-clustered bootstrap interval (R12.7).
- Train is marked in-sample (FP4).
- Every figure is labelled feasibility-only (R12.2).

**Gold conventions** (FP20):
- A gold theme is present in an event when an assignment pairs it with a claim under `supports` (P9-4).
- A cell whose only gold evidence is `uncertain` is left out and counted.
- A `tie_group` is one either-of cell. Predicting any member satisfies it, and predicting another member is not a false positive.

| Metric | Definition | Status |
| --- | --- | --- |
| Release-ID precision and recall | System: the kept attempt is `confirmed`. Gold: `release_identification.label`, with `ambiguous` left out and counted. | Gated (R13.1) |
| Theme F1, exact | Micro F1 over event × theme cells. Macro F1 is the mean per-theme F1 over themes with gold or a prediction in the partition; the rest are counted. Predicted presence means an accepted assignment. | **Gated** |
| Theme F1, rolled up | Both sides are mapped to their level-one ancestor (self or descendant), then scored the same way. Siblings earn nothing. | Secondary |
| Span overlap | Per event × theme: unit precision, recall and F1 between the gold quotes' units and the accepted assignments' quote units. Character Jaccard is also reported. | **Gated** (unit F1) |
| Retention (R12.8) | (i) verified ÷ proposed quotes; (ii) accepted ÷ assessed targets; (iii) gold-evidence recall, the share of gold-supporting units recovered by accepted assignments. | **Gated** on (iii) |
| Support precision | `accepted_claim_precision` on the joint label (task `joint_support`): in-sample on train, held out on dev. | **Gated** (dev) |
| Scorer AUC (R8.6) | `auc_roc` for MiniCheck and DeBERTa, each a named joint view, against the `claim_support` answer (task `claim_support`). | Reported |
| Judge agreement (R8.4) | κ and AC1 for each family's binary verdict (the floor's population) and, descriptively, for each of the four views with uncertain answers counted. | **Floor** (FP9) |
| Hard-negative false acceptance (R12.5) | For each gold hard negative that names a theme: an accepted assignment to that theme whose quote units overlap the negative's units. A rate, overall and per `negative_kind`. | Reported |
| Stability (R12.10) | Over FP12's three runs: Fleiss' κ on event × theme presence, and mean pairwise Jaccard of the unit sets and of the accepted-assignment sets. | Reported |
| Rare-theme recall | Recall over themes with gold support in 2 or fewer events of the partition. | Descriptive (D1) |
| Sector prevalence, source-selection bias | Not estimated, with the reason (R12.2, D1). | Not estimated |
| Independent pass (dev) | Per event: record vs kept draft, and signed file vs record, each on release-ID agreement, exact theme F1, and unit F1 (GS19). | Descriptive (D1) |
| GS5 shares | Edited, rejected and added shares per partition, from the committed counts after A6(4)'s recheck. | Reported |
| No-theme count (R12.4) | Signed files with `no_theme = true`, per partition, in coverage v2. | Reported |

## Artifacts

Committed, holding IDs, hashes, numbers and the user's answers only (GS3):
- ADR 0006 (its slug chosen when written) and its `config/models/*.toml`;
- under `evaluation/djia-2024q3-2026q2/pilot-v1/`: `preregistration-v1.toml`, `labels/support-labels-v1.toml`, `calibration-v1.json`, `coverage-v2.json`, `report-v1.json`, and `gates-v1.toml`;
- ADR 0007, the V6 record;
- `docs/verification/pilot-v1-feasibility.md`.

Local only, under `data/runs/pilot/`: the passes, runs and fresh caches; the label
views and working file; and the anchored independent records (FP16).

## Failure handling

| Situation | Handling |
| --- | --- |
| Fewer than 50 usable train joint labels | `calibrate` refuses (R8.4). The user labels the sample's remainder, or a preregistered extension draws more with the same seed. |
| A family below the floor | Excluded from every candidate, as preregistered. |
| No candidate meets ρ | `no_candidate`, as in §Calibration. |
| A live pass or run crashes | Rerun it. Cached replies replay. |
| A fresh run crashes | Discard it and rerun under a new stability run ID. Both IDs are recorded, and a partial fresh run never counts toward k. |
| A ceiling is hit | A visible `partial` status, never silent truncation. |
| A corrupt record, cache entry or label hash; a test or excluded event | Refused, printed as reason and IDs. |
| A GS5 recheck mismatch | The shares are not reported until the event's gold is re-signed or the mismatch is explained in the verification doc. |

## Wording guard and blinding

- GS13 holds until Stage 14's last test bundle is drafted:
  - no drafting session reads `data/runs/pilot/`, this stage's commands, its artifacts, or the label views;
  - the gold brief's §What you may read is an allowlist that already excludes `data/runs/pilot/` and every extraction stage's code, prompts and outputs, so it needs no change.
- The sessions that implement plans A and B never open pilot text, a kept draft, or anything under `data/runs/gold/` or `data/runs/pilot/`.
- A failing user-run gate is reported by test name and reason only.

## Verification

Plan A, in the default suite:
- the known-answer metric and bootstrap tests;
- the fresh-mode zero-hit and replay tests;
- the sampler's signature and the label view's sentinel;
- each command's sentinel;
- the import boundary: `evaluation` imports no ingestion and no httpx;
- the reject-everything gate test;
- A6's refusals and the independent comparison over invented records;
- coverage v2's byte reproduction;
- the wording guard and data-dictionary checks.

## Gates

Plan A:
1. The session runs plan A's scoped tests and Ruff.
2. The user runs the default suite and the wording gate in the main checkout, at plan A's tip, and reports the counts.

Plan B: each of B1–B8 is a user-run step whose printed counts and figures the session
records. B8 ends with the user's default suite and wording gate at plan B's tip, and
the user's approval of ADR 0007.

## Deferred items

Stage 11 closes these (`specs/deferred_items.md`):
- `10-harden-the-gold-before-bundle-4`: the refusal of a kept draft that repeats an ID (A6(1));
- `16-pilot-codebook-split-and-gold-set-protocol`: P16-2 (A6(2), A6(3)) and P16-3 (A9).

Plan 12's live-test failure-output item and its partial-`RunRecord` item stay deferred,
since their triggers are never met (FP19). Plan 9's 25 unsigned bundles are plan B's
precondition.

## Exit criteria

### The roadmap's Stage 11 Exit, clause by clause

| Clause | Met by |
| --- | --- |
| The pilot report gives every R13.1 metric's observed distribution with event-level intervals, labelled feasibility-only (R12.2/R12.7) | `report-v1.json` and the verification doc (B8) |
| The V6 record gates only pilot-estimable metrics, marks rare-theme recall, sector prevalence and source-selection bias as descriptive only, and is committed before any configuration comparison (V6/R13.1, D1) | ADR 0007 and `gates-v1.toml` (B8) |
| Judge agreement with the user's labels is reported against its preregistered floor, with AUC-ROC for both scorers (R8.4/R8.6/R8.2) | `calibration-v1.json` (B5) |
| A reject-everything configuration fails the suite (R12.8) | A3's test, rerun against `gates-v1.toml` (B8) |
| k-run stability with every response cache bypassed (R12.10) | A1, and B7's three fresh runs |
| Coverage gains the observed no-theme count for train and dev (R12.4, D4) | A7, and `coverage-v2.json` (B7) |
| Pilot metrics include the annotated hard negatives (R12.5, D4) | The hard-negative false-acceptance rate (B8) |

### Plan A

Plan A is complete when every A1–A9 test passes in the default suite, the user's main-
checkout gates pass, and the deferred items above are ticked. It runs no pilot text and
loads no model.

## Handoffs to later stages

| Stage | Receives |
| --- | --- |
| 12 | Train-only evidence and novelty, and the pilot's per-theme figures, to inform discovery. No codebook change happens here. |
| 14 | `gates-v1.toml` and the gate evaluator; the frozen baseline configuration hash; the calibrated policy; `fresh` mode; dev for the comparisons; the in-sample caveat on train. Prompt revisions and a sampled-temperature stability arm are its arms. |
| 15 | The baseline configuration and policy, and the pilot's cached replies, if their keys still match. Concurrency stays its work. |
| 16 | The gold drafting conflict is unchanged (GS4). The dev independent-pass figures inform how a Claude ceiling is read. |

## Rollout

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 11 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

"Plan completion" above means plan B's. Plan A's completion does not tick Stage 11.

- **On plan A's completion,** append this line, with the plan's ID and path:

  ```text
  > Plan A: COMPLETE (YYYY-MM-DD) — implemented by plan <id> (<path>). Next: B1 and B2; plan B's B3 waits for the visibility gate.
  ```

- **On plan B's completion,** append the stage stamp, with both plans' IDs and paths:

  ```text
  > Stage 11: COMPLETE (YYYY-MM-DD) — implemented by plans <A id> (<path>) and <B id> (<path>).
  > Next: resume the roadmap.
  ```

On each plan's completion, refresh the "Current state" section of `CLAUDE.md`, with the
user's approval.
