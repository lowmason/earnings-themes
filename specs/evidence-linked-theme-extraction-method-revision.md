# Evidence-linked theme extraction — method revision: cost, support decision and prevalence

> For agentic workers: REQUIRED NEXT SKILL: derive-roadmap — do not plan
> this spec directly and do not split it into per-subsystem plans.

**Status:** DRAFT, synthesized 2026-11-27 from an external critique. It waits for the
owner's review.

This specification revises the method of the built theme-extraction system. It does
four things. It cuts the time of a pass, mainly in the classifier, the judge panel and
re-verification. It replaces the unanimity rule for semantic support with a fitted
score and a threshold with a precision guarantee. It adds a prediction-powered
estimate of theme prevalence beside the evidence-bound count. It also keeps every
manual label set. One train pass took about 60 h of model phases and 13 h of
verification. The critique estimates 11–18 h after its first eight fixes. This spec
treats that figure as an estimate to measure, not as a gate.

## Design provenance

This spec synthesizes two files on this branch:

- the methodology description, `specs/evidence-linked-theme-extraction-methodology.md`
  (committed at `ce72ea3` and completed at `7006cf1`, 2026-11-27)
- the external critique, `specs/evidence-linked-theme-extraction-critique.md`
  (committed at `31ac289`, 2026-11-27).

The critique is a first-pass Claude Chat Research review. Its own header says that no
point was adjudicated. So the session that wrote this spec made the triage calls. It
checked the critique's premises against the code and the verification records first.
The owner settled four points (§Decisions). The description had not moved: no commit
on any branch touched `packages`, `apps`, `prompts`, `config`, `evaluation` or
`codebooks` after `ce72ea3`.

**Locators.** `(methodology C5)` cites a component of the description, and
`(methodology §Computational cost model)` cites a section. `(critique CP10)` cites a
numbered point, `(critique Q2)` an answer to an open question, and `(critique Part 3)`,
`(critique TL;DR)` or `(critique Caveats)` a section. The critique numbers its points
CP1–CP32, so this spec never writes `C` for a critique point. A verdict other than a
plain accept is written beside the locator. This spec uses the description's notation
table without change: π_{k,τ}, s_P, s_A, y^σ, y^φ, y, O(t), Θ_c, Λ_V and the label
sets G, IP, HN, STr, SDv and TG.

**Facts checked during triage.** Each fact below changed a verdict or a requirement:

- The classifier's user message is JSON with sorted keys
  (`coding/prompt.py`, `json.dumps(data, sort_keys=True)`). So `attribution_context`
  and `claim` come before `codebook_rules` and `frozen_themes`. Themes are in
  theme-ID order for every claim, so a shared block exists but sits behind
  claim-specific text (critique CP10).
- The runtime is llama.cpp with Metal offload (ADR 0004, ADR 0006, D21-19).
- `djia-pilot/1` selects events by coverage steps and a hash order. It is purposive,
  with no inclusion probabilities, so G is not a probability sample (critique CP5).
- The train labels hold 41 joint positives and 22 joint negatives, with 7 excluded.
  The claim-support labels are 62 `supported` and 2 `unsupported`. Theme fit is
  `does_not_fit` for 20 of 67 decided targets (B4 record).
- 623 dev claims completed: 719 − 94 cut by the ceiling − 2 hierarchy conflicts.
- The outcome rule requires 4 trials over 2 families × 2 presentations. Any other
  panel shape makes every target `invalid_references`, then incomplete
  (`support/assess.py`, `derive_outcome`).
- Structured output is already on (D21-19). The judge schema accepts any non-blank
  `quote_id`. Train had 162 attempts with invalid references and 100 malformed ones.
- FP22 records that a schedule batched by judge family was considered and declined.
  The judges then ran together, with swap up to 13.2 GiB and pressure 2 (D21-19).
- D21-33's test T3: under an all-review baseline, support precision is left ungated as
  `undefined_point`, and the report fails its own gates on zero gold-evidence recall.
- On 2026-10-20, about 9 of 17 train gold drafts lost quotes as `not_narrative`. The
  Goldman Sachs release for the quarter ending 2024-12-31 (CIK 886982) lost 58 of 76
  quotes and 8 themes to a two-column layout table. The repository does not record
  this yet (MR22).
- The description's scorer formula 2 N_T is loose (critique CP28 ii). A target has one
  joint signal and one signal per quote. This has no consequence for the method.

## Decisions

The owner made these decisions on 2026-11-27, in answer to the triage questions:

| ID | Decision |
| --- | --- |
| MRD1 | **Stage 11 finishes with one fresh run and the v1 gates.** B7 runs one fresh dev run, not three, recorded as an amendment of R12.10 and FP12. B8 reports V6 under the frozen v1 rule, with the critique's caveats. Stage 14 gets a paired exact gate rule in a v2 preregistration, frozen before any comparison. |
| MRD2 | **Two current judge families, batched.** Drop Mistral-Nemo and add a current non-Gemma family. Run all of one judge's trials, then the other's, which lifts the 14B cap. One trial per judge, in random order, with the order effect modelled. This keeps R8.4's cross-family rule and amends its order-swapping and FP22. |
| MRD3 | **PPI as a companion estimate.** Keep the evidence-bound count, with its quotes. Add a prediction-powered estimate with a fresh random gold draw at Stage 15. Planning sets the draw's size. |
| MRD4 | **About 100–150 new unaided owner labels, outside dev.** They are drawn at random from targets outside dev, so that dev stays clean for evaluation. A separate score-stratified set of 20–30 targets claim-support negatives. |

## Motivation

The pilot shows that the method spends most of its time where it buys no information
(methodology §Computational cost model):

- **The classifier dominates inference.** C5 took 33 h 21 min for 20 documents. Each
  call reads about 7,000 prompt tokens to write about 29. The shared codebook sits
  behind the claim, so a prefix cache can reuse only the instruction block
  (critique CP10).
- **The support stage yields almost nothing.** C6 took about 26 h. It marked 1 of 1,170
  train targets and 5 of 601 dev targets clear. The labels say that about 65% of
  targets are jointly positive. So the unanimity rule flags almost every target that
  the labels support (critique CP11). C7 then selected no policy (`no_candidate`).
- **Verification costs as much as a model phase.** Cache keys embed whole bundles,
  about 13 MB each. The write and read-back of the two train support runs took about
  13 h. A replay with no model took 14 h 13 min (critique CP18).
- **The support labels do not survive a method change.** They bind to run identity. A
  new classifier, prompt or host orphans all 94 of them (critique CP19).
- **The prevalence route is biased.** π_{k,τ} counts only accepted assignments. Any
  gate that trades recall for precision biases it downward. Reviewing every flagged
  target would mean about 14,000–22,000 targets for 240 events (critique CP5).

At current speed the full corpus would take about 40–45 days of continuous running.

## Core principle

Keep every manual label set and the exactness guarantee. Cut cost where it buys no
information. Change the support decision only to a form with a stated, measured
guarantee.

## What this spec amends

| Source | Item | Change | Requirement |
| --- | --- | --- | --- |
| `specs/evidence-linked-theme-extraction.md` | R8.4 | Order-swapping becomes a seeded random presentation order, with the order effect modelled. The cross-family rule stays. | MR6 |
| same | R11.2 | Adds the PPI companion estimate. The count stays, with its numerator, denominator and unit. | MR19 |
| same | R12.10 | For Stage 11, one fresh run compared with the frozen dev pass. | MR14 |
| `specs/feasibility-pilot-and-threshold-calibration.md` | FP8 | New unaided owner labels carry the guarantee. STr serves development only. | MR10 |
| same | FP10 | After Stage 11, a fitted score and a Learn-then-Test threshold replace the scorer cutoff with a recall floor. | MR9, MR11 |
| same | FP12 | k = 3 fresh runs becomes 1. | MR14 |
| same | FP15 | The v1 rule stays for Stage 11's V6. Stage 14 uses the v2 rule. | MR14, MR15 |
| same | FP22 | Judges run in family batches, not interleaved per target. The 14B cap lifts. | MR6 |
| `specs/completed/semantic-support-assessment.md` | The four-trial contract and the unanimity outcome | Two trials, one for each family, in random order. A fitted score decides among the targets that are neither refused nor incomplete. | MR6, MR9 |
| Stage 7 and Stage 8 caches | Keys that embed bundles | Keys bind the same R14.6 components by digest. R14.6 itself does not change. | MR13 |

## Requirements

### A. Labels and frozen inputs

**MR1 — Content keys for support labels.** *(critique CP19, Q4, methodology §Human
labels and what binds them)*

1. Each support label gets two content keys:
   - key_σ = h(h(x_d) ‖ the sorted quote spans [a_i, b_i) ‖ the sorted attribution-context
     spans ‖ norm(ℓ_c))
   - key_φ = h(norm(ℓ_c) ‖ k ‖ the codebook's ID, version and content hash).
   norm is C2's own Unicode and whitespace normalization, applied to the claim
   sentence.
2. key_σ includes the attribution-context spans, because σ depends on the fixed
   attribution context (methodology A7). The critique's key omits them.
3. A committed mapping record re-keys all 94 existing labels, 70 in STr and 24 in SDv.
   The frozen label files are never edited. The mapping must be one-to-one on the
   current train and dev runs.
4. Every later label, including MR10's, carries both keys.

(chosen) content keys. (rejected) freezing the old runs as the calibration set: it
keeps the labels but strands them on obsolete targets. (rejected) labelling again: it
spends owner time that content keys save (critique Q4).

**MR2 — Freeze C3.** *(critique Q4, TL;DR, CP29, Q3)* The pilot's frozen train
and dev extraction runs are the inputs of every revised later stage, read by replay.
C3's windows, prompt and model (Gemma 4 31B-it) do not change in this revision. So all
claims and spans reproduce, and MR1's keys resolve. This sits in tension with R12.9's
Stage 14 extraction arms. Those arms map labels from old to new by identical quote-span
sets, and the owner confirms any claim rewording (critique Q4).

### B. Classifier (C5)

**MR3 — The shared block comes first.** *(critique CP10, methodology C5)* The classifier
request puts all claim-independent content first: the instructions, the codebook rules
and the theme definitions in theme-ID order. The claim, its quoted evidence and its
attribution context come after it. The order is explicit in the request builder, not a
side effect of key sorting. The change is a new prompt or coding version, never an
in-place edit.

- Whether llama.cpp reuses the prefix across Gemma 4's sliding-window layers with the
  current server flags, or needs `--swa-full`, is *(open — resolved by verification,
  not argument)*. MV1 discharges it.
- The share of the request's tokens that the shared block holds is *(open — resolved
  by verification, not argument)*. MV1 discharges it.
- The critique estimates a saving of 25–29 h per train pass. That is an estimate, and
  MV16 measures it.
- Codebook order can change LLM coders' answers (critique CP7). So MV1 measures Θ_c's
  agreement with the frozen run. y^φ survives through key_φ either way.

**MR4 — No document is cut by the classifier ceiling.** *(critique CP22, accept in
part)* The 128-request ceiling for each document (D21-12) cut 94 of 220 claims in one
dev document. The cut falls on long releases, so π tilts toward themes of short ones.
Once MR3's call time is measured, the per-document ceiling is sized from the observed
claim counts so that no pilot document is cut. A run-wide ceiling stays as the
explicit guard (ES21). MV15 compares the cut document's dev recall with the other
documents'.

**MR5 — Classifier model comparison, conditional.** *(critique CP30, Q3)* After MR3,
compare the QAT 31B checkpoint and the Gemma 4 26B-A4B mixture-of-experts model with
the current classifier. Measure time per call and Θ_c agreement on 50 train claims,
and event × theme F1 on train gold. A model change is recorded in a decision record.
It is never picked silently, because the production model is deliberately unresolved.
Θ_c may change, and y^φ survives through key_φ.

### C. Support assessment (C6) and decision (C7)

**MR6 — Judge panel: two current families, batched by family (MRD2).** *(critique CP13,
CP14, CP15, CP20, R8.4, FP22)*

1. Mistral-Nemo leaves the panel. Its κ against the joint label is 0.005
   (−0.092, 0.101). Under unanimity it could only veto.
2. The panel is two current open-weight judges from two different families. Neither is
   Gemma (A6). Neither is from a label drafter's family (MR18). A decision record, like
   ADR 0006, chooses them from MV3's model-card checks and MV6's measured agreement.
   Each candidate's license and self-hostability are *(open — resolved by verification,
   not argument)*, and MV3 discharges them.
3. Judges run one family at a time: all of one judge's trials, then all of the other's.
   This amends FP22, whose interleaved schedule kept both judges and the scorer in
   memory at once. A judge's size is then bounded by one judge plus the scorer in
   36 GB, which MV7 measures.
4. Each target gets one trial for each family. Each trial's presentation order is drawn
   at random from a seed recorded in the run. The order effect is a term in MR9's
   score. This amends R8.4's "order-swapping".
5. The outcome contract changes with a new support version: two trials, one for each
   family. A trial that is unavailable after its attempts still makes the target
   incomplete.

(chosen) two current families, batched. (rejected) one judge behind a cascade, the
critique's Q1 advice: it breaks R8.4's cross-family rule (MRD2). (rejected) keeping the
four-trial panel with a new aggregation only: it keeps the swap and the 14B cap (MRD2).
(rejected) dropping Mistral-Nemo with no replacement: it leaves one family (MRD2).

**MR7 — The judge reply schema names the target's quotes.** *(critique CP16, accept in
part)* Each judge request carries a reply schema whose quote-ID field accepts only the
target's own quote IDs. Most unavailable trials came from invalid quote references,
and the current schema accepts any non-blank string. The rationale field stays. It
leaves only if an A/B on the labelled targets shows that removing it costs no
agreement. The critique's 25–30% saving from shorter output is an estimate.

**MR8 — Scorers: the alternative on labelled targets only, and one candidate.**
*(critique CP17, CP12, R8.2)*

1. The production path computes s_P only. s_A runs over the labelled targets, so R8.2's
   AUC comparison of both scorers stands. Today the alternative run is a second support
   run that replays every judge reply, and it took 6 h 15 min on train.
2. A stronger grounding checker, such as Bespoke-MiniCheck-7B, is a candidate for s_P
   (critique CP12, accept in part). Its license, self-hostability and current standing
   on LLM-AggreFact are *(open — resolved by verification, not argument)*, and MV3
   discharges them. It replaces s_P only if MR10's negatives show a better AUC against
   y^σ. Until then, s_P's AUC rests on 2 negatives and shows nothing.

**MR9 — A fitted support score replaces unanimity.** *(critique CP11, CP8, CP12, Q2,
methodology C6 step 3)*

1. O_ref and O_inc keep their precedence. A target that fails an integrity check, or
   lacks a required signal, is never accepted. Exactness stays code's alone (A1).
2. For every other target, a logistic aggregator with weakly informative priors gives a
   support score (critique Q2a). Its inputs are s_P(t), each family's σ and φ answers,
   the quotes' contribution labels, the presence of reason codes, and each trial's
   presentation order. C5's own φ confidence is an input only if the runtime returns
   token probabilities. That is *(open — resolved by verification, not argument)*, and
   MV2 discharges it.
3. The score estimates P(y = 1). The plan pre-declares whether that is one joint model
   or the product of separate σ and φ models. Separate σ and φ fits are always reported
   (critique CP12).
4. The aggregator is fitted on STr. It is never fitted on SDv. SDv are dev labels, and
   C7's design fits on train only and holds dev for evaluation (methodology C7, MRD4).
   The critique's Q2 suggests fitting on STr ∪ SDv, and this spec rejects that part.
5. A Dawid–Skene latent-class model is fitted as a sensitivity analysis only. Two
   correlated families identify it weakly (critique Q2b).
6. Theme fit stays an independent judge question. (rejected) the critique's claim that
   it repeats C5's decision (CP12): the labels reject C5's proposed theme for 20 of 67
   decided train targets.
7. Before the aggregator is adopted, MV5 compares majority vote, mean score and
   unanimity with y on the stored trials, with no model call (critique CP8, CP11).

**MR10 — New unaided owner labels (MRD4).** *(critique CP24, Q2, Q8, CP27)*

1. The owner labels about 100–150 targets for σ and φ, unaided: no model draft and no
   score or judge output visible. This is FP8's original rule. The labelling view is
   B4's blinded view.
2. The frame is targets outside dev: train targets with no label, or targets of new
   events outside the pilot. The plan chooses the frame and records it before drawing.
   The draw is seeded, with known inclusion probabilities.
3. The calibration targets are disjoint from STr's targets, which fit MR9's score.
4. A separate score-stratified set of 20–30 targets enriches claim-support negatives
   (critique Q8). Its inclusion probabilities are known and weight its estimates. It
   never enters MR11's calibration set, because sampling by score breaks the random
   sample that a guarantee needs (critique Q2).
5. The labels are committed alone before any calibration reads them, as IDs, content
   keys, hashes and answers, with no free text (FP17).

**MR11 — An acceptance threshold with a precision guarantee.** *(critique CP9, Q2)*

1. A target t is accepted only if three things hold:
   - O(t) is neither O_ref nor O_inc.
   - k ∈ Θ_c.
   - its MR9 score is at least λ̂.
2. Learn-then-Test on MR10's calibration labels chooses λ̂. It ensures that precision
   is at least 1 − α with probability at least 1 − δ (Angelopoulos et al. 2025). Event
   clusters are the exchangeable units.
3. The owner sets α and δ in preregistration v2 (MR15). Quality thresholds are
   deliberately unresolved in this repository, and no session picks them.
4. With zero errors, n accepted calibration targets give the one-sided bound δ^{1/n}.
   A 0.90 bound at δ = 0.1 needs n ≥ 22, and a 0.95 bound needs n ≥ 45. One error
   roughly doubles n (critique Q2).
5. If no λ̂ meets the guarantee, nothing is accepted and every target stays in review.
   That is a valid finding.
6. A cascade that calls judges only where s_P is uncertain is adopted only if MR10's
   negatives show that s_P separates σ. Its band is pre-declared (critique Q1). s_P's
   AUC now rests on 2 negatives and shows nothing.

(chosen) Learn-then-Test, or conformal risk control if the plan pre-declares it.
(rejected) the grid search with a recall floor: it gives no guarantee (critique CP9).

### D. Verification and storage (Λ_V)

**MR12 — Profile before redesign.** *(critique CP18)* Plans 23 and 24 projected a 7.2 h
train replay from floors measured on invented text, and the real replay took 14.2 h. The
cause is not measured. So one replay is profiled before MR13 is designed. The profile
splits wall time between reading and hashing bundles, deriving keys, invariant checks,
and Parquet I/O. The owner runs it, and it reports timings only (MV8).

**MR13 — A digest-addressed store with checks at write.** *(critique CP18, Q6, accept in
part)*

1. Each canonical document and each output blob is stored once, under its own SHA-256.
2. A cache key binds every R14.6 component by digest, not by embedding the bundle. A
   changed input still misses the cache and fails visibly (A8).
3. Each quote record carries (h(x_d), a, b, h(q)).
4. The full span check runs before storage, before support judgment and before
   export: 0 ≤ a < b ≤ |x_d|, q = x_d[a, b), and stored hash = h(x_d). These are the
   project's three invariant gates. x_d loads once for each document, so the check is
   cheap. Other consuming steps check digests only. (rejected) checking only once at
   write, as the critique proposes: it would drop two of the project's gates.
5. A run manifest of output digests makes "same run" a digest comparison. A replay
   compares output digests.
6. A full re-verification runs before export and on demand (critique Q6).
7. The frozen train and dev pilot runs stay replayable. A migration maps their old
   entries into the new store, and a replay under the new store reproduces their
   outputs (MV9).

The critique estimates the write and read-back falling from about 13 h to under 1 h,
and a replay from 14.2 h to under 1 h. Those are estimates, and MV16 measures them.

### E. Evaluation (C9)

**MR14 — Stage 11 finishes with one fresh run and the v1 gates (MRD1).** *(critique
CP21, CP25, CP26, R12.10, FP12, FP15)*

1. B7 runs one fresh dev run, not three, through plan 27's pausable fresh runs. R12.10's
   agreement across runs compares that run with the frozen dev pass.
2. The rationale: at temperature 0 the runs measure only runtime determinism (FP12),
   and one run outside replay measures it (critique CP21). (rejected) the critique's
   claim that a replay already shows it: a replay calls no model, so it shows only that
   the cache reproduces.
3. Plan 21 records this amendment as a decision when it is applied.
4. B8 reports V6 under the frozen v1 rule, `dev-lower-bound/1`. The V6 record states the
   caveats:
   - 8 dev clusters are too few for a reliable cluster bootstrap (Cameron, Gelbach and
     Miller 2008).
   - B = 10,000 exceeds the 6,435 distinct resamples of 8 clusters.
   - the rule is unpaired and lenient: a configuration equal to the baseline passes about
     95% of the time.
   - under the all-review baseline, support precision is ungated (`undefined_point`,
     D21-33).
5. The V6 record says that Stage 14 adjudicates under MR15's v2 rule.
6. A sampling-robustness arm stays in Stage 14 (FP12).

**MR15 — Stage 14's gates under preregistration v2.** *(critique CP25, CP26, Q8)*
Preregistration v2 is frozen and committed alone before any Stage 14 configuration runs
on dev. It holds:

1. the baseline configuration, which is MR24's revised method.
2. the set of configurations to compare. A configuration outside the set needs a new
   preregistration version before its dev results are read.
3. for each gated metric, the paired per-event difference d_e = M_new(e) − M_base(e)
   and a non-inferiority margin. The owner sets the margins.
4. an exact sign-flip test over the 2^8 = 256 sign patterns of the 8 dev events, with a
   declared test level.
5. intervals reported as descriptive only. A bootstrap never uses more resamples than
   there are distinct resamples, and exact enumeration replaces it where it can.
6. α and δ for MR11.

**MR16 — Agreement statistics.** *(critique CP27, Q8)* Judge agreement with the joint
label y reports κ together with sensitivity, specificity, and positive and negative
specific agreement, each with exact intervals. Gwet's AC1 is a secondary figure, never
a substitute for κ (Vach and Gerke 2023). For y^σ, the report states that specificity
cannot be estimated until MR10's negatives exist.

**MR17 — Gold anchoring is measured with IP.** *(critique CP23)* B7 already compares
each independent pass with its kept draft. It extends the comparison to the signed dev
gold. The comparison covers event × theme agreement, quote-unit overlap, the themes in G
that IP lacks, and the reverse. It counts G's additions over IP that match the drafter's
draft, which is the anchoring signature. The result is descriptive only (D1). Only
per-event figures are committed (FP16).

**MR18 — No evaluation by a drafter's family.** *(critique Q5)* Claude drafted G. Codex,
an OpenAI model, drafted STr and SDv. No model of the Claude family is evaluated against
G, and no model of the OpenAI family is calibrated against STr or SDv. A model of either
family that is used anyway is evaluated only against IP and MR10's owner labels.
Stage 16 already records the Claude conflict.

### F. Estimand and coverage (C8)

**MR19 — A prediction-powered companion estimate of prevalence (MRD3).** *(critique
CP5, CP23, R11.2)*

1. π_{k,τ} stays as defined. It is reported as the evidence-bound count, with its quotes,
   numerator, denominator and unit. The report labels it as biased downward by the gate.
2. A companion estimate is added:

   $$
   \hat\pi^{PP}_{k,\tau} \;=\; \frac{1}{N}\sum_{i}\hat f_{ik} \;+\; \frac{1}{|L|}\sum_{i\in L}\big(Y_{ik}-\hat f_{ik}\big)
   $$

   Here i runs over the N completed events of quarter τ, f̂_{ik} is a pre-declared
   event-level prediction computed for every completed event, and Y_{ik} is the gold
   presence on the rectifier set L. Candidates for f̂ are the proposal indicator (some
   claim has k ∈ Θ_c) and the accepted-assignment indicator.
3. L is a fresh random draw from the eligible, completed events of the Stage 15
   manifest. A seeded rule draws it, with known inclusion probabilities, and the rule is
   frozen before any of its text is seen. Unequal probabilities are weighted, as
   design-based supervised learning does (Egami et al. 2023).
4. The pilot's G is never L, because `djia-pilot/1` is purposive.
5. L's gold follows the Stage 6 protocol, with GS19's independent pass first, so that
   MR17's anchoring check covers it.
6. The plan sets |L| from a target interval width and the owner's labelling budget, and
   records it before drawing.
7. The plan pre-declares how per-quarter estimates get their rectifier: strata by
   quarter, or a stated pooling assumption.
8. A feasibility illustration on the 20 train events compares π̂^PP with the plug-in,
   leaving one event out at a time. It is labelled illustrative, because G is purposive.

**MR20 — Bounds for missingness.** *(critique CP3)* Beside each π_{k,τ}, the report
gives the worst-case bounds [n_k / (N_obs + N_miss), (n_k + N_miss) / (N_obs + N_miss)],
computed from the processing-state table. They make C8's untested assumption 1
quantitative.

**MR21 — An intensity companion.** *(critique CP6)* For each event and theme, the report
gives the accepted units for theme k divided by the event's eligible narrative units. It
also counts the event-level presences that rest on one unit. Both are computed on G and
on system output. They make the results comparable with the finance literature and show
how fragile a single-unit presence is.

### G. Recall risks

**MR22 — The layout-table loss is measured.** *(critique CP4, accepted and upgraded)*
The owner runs a count over the kept train and dev drafts. It gives, for each event, the
quotes refused as `not_narrative` and the themes lost. A verification record stores the
counts and IDs only. The count reproduces the 2026-10-20 observation (§Design
provenance). Every recall report states that the gold and the extractor share this
blind spot, so recall against G cannot see it. (rejected) the critique's check of G
quotes against layout-table elements: anchoring refuses such quotes, so signed G holds
none. A parser fix needs a `walker-2` and a re-projection of G, IP and HN (A2), and it is
out of scope here.

**MR23 — The duplicate-claim rate is measured.** *(critique CP29, Q7, accept in part)*

1. A count over the train claims finds pairs in one document whose cited unit sets meet
   a pre-declared Jaccard threshold and whose normalized claims are nearly identical.
   It reports counts only.
2. Duplicates are removed before C5 only if their share exceeds a pre-declared value.
   The removal is a filter after the frozen C3, not a change to C3.
3. Removal keeps the original claim IDs, so that MR1's keys still resolve.
4. This relates to R11.5's dedup arm in Stage 14.

### H. Cost

**MR24 — The revised baseline and its measured cost.** *(critique Part 3, intro, TL;DR,
Caveats)*

1. After the requirements above land, a train pass and a dev pass run under the revised
   method.
2. Each pass records wall time for each phase, call counts, prompt and output tokens,
   `cache_n`, and Λ_V. Each is compared with the current figures: about 60 h of model
   phases and about 13 h of verification per train pass, and 14 h 13 min per train
   replay.
3. The critique's projection, about 11–18 h per train pass and 6–13 days for the corpus,
   is an estimate, not a gate.
4. These passes are the baseline that preregistration v2 names (MR15).
5. The full-corpus projection is computed again from the measured figures, including
   any growth in Λ_V.

## Verification

Agents never open pilot text and never load a model (GS13). Every check on real data is
run by the owner and reports counts, hashes and timings only.

- **MV1** *(discharges MR3's two open items)* — The owner runs MR3's request order on
  one train document. The record holds `cache_n` for each call, the time per call, the
  shared block's share of prompt tokens, and Θ_c's agreement with the frozen run. If
  `cache_n` covers only the instruction block, the check is repeated with `--swa-full`,
  and the record says which setting reuses the prefix.
- **MV2** *(discharges MR9's φ-confidence input)* — A check on the runtime documentation
  and one call on a fixture with no pilot text show whether llama.cpp returns token
  probabilities for the classifier's reply.
- **MV3** — Model-card checks record each candidate judge's license, self-hostability,
  family and release date in a decision record, as FP6 did for ADR 0006. A candidate
  grounding checker gets the same check, together with its current standing on
  LLM-AggreFact (critique CP12).
- **MV4** — All 94 labels map one-to-one under MR1's keys on the current train and dev
  runs. The frozen label files' hashes are unchanged.
- **MV5** — An analysis of the stored trials, with no model call, compares majority
  vote, mean score and unanimity with y. It also estimates each current family's order
  effect, P(σ = supported | evidence first) − P(σ = supported | claim first).
- **MV6** — The owner reruns only the judge stage on the 84 labelled targets for each
  candidate panel. The record gives MR16's statistics for each family.
- **MV7** — Under the family-batched schedule, one judge and the scorer fit in 36 GB. The
  record gives resident set size, swap and pressure, as B1 recorded them.
- **MV8** — One replay is profiled, with its wall time split as MR12 states.
- **MV9** — Under the new store, a replay of the frozen train pass reproduces its
  outputs. A fixture test shows that a damaged blob is refused at read by its digest.
  Fixture tests show that the full span check runs before storage, before support
  judgment and before export.
- **MV10** — Fixture tests show that a C5 prompt change leaves every label resolved,
  and that a C3 change that moves spans leaves a label visibly unresolved.
- **MV11** — The default suite passes with no network and no billable call. Fixture
  tests cover MR9's aggregator, MR11's threshold (the all-review case included),
  MR19's estimator against a hand-computed fixture, MR20's bounds and MR21's intensity.
- **MV12** — B7's fresh dev run is complete, and plan 21's decision log records MRD1's
  amendment. B8's V6 record carries MR14's caveats.
- **MV13** — Preregistration v2 is committed alone before any Stage 14 configuration
  runs on dev, with its content hash.
- **MV14** — MR10's labels are committed alone before any calibration reads them, with
  their frame, inclusion probabilities and seeds.
- **MV15** — A verification record holds MR22's layout-table counts, MR23's duplicate
  counts and MR4's comparison of the cut document's recall.
- **MV16** — MR24's revised train and dev passes record measured phase times against the
  baseline figures.

## Out of scope

- **A parser fix for layout tables.** It needs a `walker-2` and re-projection of G, IP
  and HN. MR22 only measures the loss (critique CP4).
- **A distilled small classifier** (critique CP7, Q1, Part 3 rank 15), rejected for now.
  The critique rates its own confidence low, and the classifier would learn model labels
  whose theme fit the labels reject for 20 of 67 decided targets.
- **Several claims in one C5 call** (critique Q1), deferred. It changes C5 assumption 1
  and every Θ_c. It is a candidate Stage 14 arm, after MR3.
- **A window overlap or boundary check in C3** (critique Q7), deferred. It changes C3,
  which this revision freezes (MR2). It is a candidate Stage 14 arm.
- **Rented GPUs or hosted open-weight models** (critique CP32, Q5), deferred. R14.1 is a
  standing owner decision, and the critique itself sequences rental after its ranks 1–3.
  The costed option is recorded for a later decision. On 2026-11-27 the critique priced
  a RunPod H100 at $2.89/h and Gemma 4 31B-it on OpenRouter at $0.10 per 1M input tokens
  and $0.34 per 1M output tokens: about $1.9 for a train pass and $25–35 for the corpus.
  It noted that one model name can be served at fp4 or fp8, so a provider and precision
  must be pinned. Revisit once MV16 gives measured times.
- **Parallel judge slots or continuous batching** (critique CP31). They land with
  Stage 15's concurrency items (support writers, allowance coordination, cache and store
  publication), not here.
- **A single judge behind a cascade, and dropping a family with no replacement**
  (critique Q1, CP13), rejected by MRD2.
- **Freezing the old runs as the calibration set, or labelling again** (critique Q4),
  rejected in MR1.
- **The test gold**, which stays sealed until Stage 14 (GS18, critique Q8).
- **Correcting the description's scorer formula** (critique CP28 ii). It has no
  consequence for the method, and §Design provenance records it.

## Rollout note

1. **The blocking open item comes first.** MV1 settles whether llama.cpp reuses the
   prefix across Gemma 4's sliding-window layers. MR3's saving and MR4's ceiling sizing
   depend on it.
2. **Order constraints.** MR1 lands before any change that alters C5–C7 outputs (MR3,
   MR5, MR6, MR9). MR12 comes before MR13. MR10's labels come before MR11's
   calibration. MR15 is frozen before any Stage 14 comparison.
3. **Stage 11 is in flight.** MR14 and MR17 apply to plan 21's B7 and B8 now, and plan 21
   records them as decisions when it applies them.
4. **derive-roadmap reconciles this spec into the live roadmap**,
   `specs/evidence-linked-theme-extraction-roadmap.md`:
   - it amends Stage 11's B7 scope and exit (MR14, MR17).
   - it places the other requirements between Stage 11 and Stage 14, as it judges.
   - it amends Stage 14 for preregistration v2, the paired gates, the revised baseline and
     label mapping by span sets (MR2, MR15, MR24).
   - it amends Stage 15 for the rectifier draw, the bounds and the intensity companion
     (MR19–MR21).
   This spec is not one stage. derive-roadmap decides its stages, and each stage it routes
   carries the roadmap's stage-spec stamp.
5. **Repository state.** This spec, the description and the critique sit on branch
   `claude/theme-extraction-critique-b433ce`, built on
   `claude/local-llm-performance-fb9869`. SDv is on the `data/dev-labels` branch. It must
   reach the main line before MR1's re-key lands, or MR1 reads it there.
