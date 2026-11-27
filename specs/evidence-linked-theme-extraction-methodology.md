# Evidence-linked theme extraction from earnings releases — methodology

> For agentic workers: when specs/evidence-linked-theme-extraction-critique.md
> exists beside this file, REQUIRED SKILL: describe-critique-methodology
> (synthesize mode) — do not draft a spec directly.

This document describes a built system in math and prose. It omits the
implementation on purpose. The reviewer should critique the method.

**The owner's main concern is cost in time.** The system runs every model on one
local machine. One pilot pass over 20 documents took about 60 hours of wall time.
A replay of that pass, which runs no model at all, took a further 14 hours. The
owner wants to know which parts of the method cause this cost, and what a better
method would look like. The section "Computational cost model" puts the observed
figures in one place. Open questions Q1 to Q6 ask about them directly.

**One constraint is binding on every proposal: keep all the manual labels.** The
section "Human labels and what binds them" lists each label set and what would
invalidate it. A proposal that would discard a label set must say so and must say
how that set would be reused.

## Purpose and estimand

A firm's quarterly earnings release states results, causes, outlooks, risks and
plans. The system finds the themes that each release discusses. Every theme it
reports must be bound to an exact, locatable span of the release's text.

The final estimand is theme prevalence over a point-in-time cohort of firms. For
theme k and quarter τ, prevalence is

$$
\pi_{k,\tau} \;=\; \frac{\#\{\, i \in \mathcal{I}_\tau : \exists\ \text{accepted assignment } (i,\tau,k) \,\}}{\#\{\, i \in \mathcal{I}_\tau : \text{firm } i \text{ has an observable, processed release for } \tau \,\}}
$$

The numerator counts distinct firms, not quotes. The denominator counts only firms
whose release was acquired and processed. A firm whose release is missing,
restricted or failed is excluded from the denominator and counted apart. It is
never counted as a firm without the theme. Firms have equal weight.

The intermediate estimand, on which the pilot is judged, is the set of
event-level theme presences and their supporting evidence:

$$
\widehat{Y}_e \;=\; \{\, (k,\ Q_{e,k}) : k \in \mathcal{K},\ Q_{e,k} \neq \emptyset \,\}
$$

Here Q_{e,k} is the set of accepted quotes that support theme k in event e.

## Component inventory

| Component (by methodological role) | Output | Consumes |
|---|---|---|
| C1. Point-in-time cohort and event resolution | Event set 𝓔, with one release document per event | Index membership records, filing metadata |
| C2. Canonicalization and structural segmentation | Canonical text x_d, its hash, typed elements, boilerplate masks M_d | Saved release bytes |
| C3. Exhaustive pointer extraction (model) | Candidate claims, each with cited units | Units U_d in windows |
| C4. Deterministic span verification | Accepted quotes, or a recorded rejection | Candidates, x_d |
| C5. Deductive classification against a fixed codebook (model) | Proposed theme set Θ_c for each claim | Claim, quotes, context, codebook 𝒦 |
| C6. Semantic support assessment (two scorers, two judges, two presentations) | Review outcome O(t) and raw signals for each target | Targets t = (c, k) |
| C7. Assignment policy and its calibration | Accept or review for each target | O(t), s_P(t), human support labels |
| C8. Coverage-aware aggregation | Prevalence π_{k,τ} with its numerator and denominator | Accepted assignments, processing states |
| C9. Evaluation against human gold | Metrics, event-clustered intervals, quality gates | System output, gold, labels |

C3, C5 and C6 run language models. They carry nearly all inference cost. C4 and
the verification at every later step carry most of the non-inference cost. The
per-component sections below give these four the most space.

## Composition

For each event e, let d_e be its release document. The pipeline composes as
follows:

1. C2 maps the saved bytes to x_d and to an ordered unit sequence U_d = (u_1, …, u_n).
2. C3 packs the units into windows ω_1, …, ω_m. It calls the extractor once per
   window. Each call returns zero or more candidates c = (S_c, ℓ_c). S_c is a set of
   unit labels and ℓ_c is a one-sentence claim in the model's own words.
3. C4 keeps c only if every label in S_c names a quotable unit of its window. The
   quotes of c are then the exact unit spans x_d[a_i, b_i) for u_i ∈ S_c.
4. C5 calls the classifier once per accepted claim. It returns Θ_c ⊆ 𝒦. Each
   pair t = (c, k) with k ∈ Θ_c becomes a support target.
5. C6 computes, for each target, two entailment scores and four judge trials. A
   deterministic rule turns them into an outcome O(t).
6. C7 applies a policy ψ. The policy accepts t only if O(t) is "clear" and the
   calibrated rule votes to accept. Every other target goes to human review.
7. C8 projects accepted targets onto the analytical grain
   firm × quarter × document type × speaker role × theme × quote,
   and computes π_{k,τ}.

The composition is a chain of filters, not a probabilistic model. No stage
combines signals into a posterior. Acceptance requires every gate to pass:

$$
\text{accept}(t) \;=\; \mathbb{1}[\text{C4 passes}] \cdot \mathbb{1}[k \in \Theta_c] \cdot \mathbb{1}[O(t) = O_{\text{clear}}] \cdot \psi(t)
$$

Because the factors multiply, the yield of the chain is the product of the
per-stage pass rates. One stage with a very low pass rate makes the whole chain
yield nothing.

## Cross-component assumptions

A1. **Code is the only authority on exactness.** A model may propose evidence and
judge support. It may never change wording, offsets or the codebook. If this
fails, quoted text could differ from the source, and every later stage would rest
on fabricated evidence.

A2. **The canonical text never changes beneath stored spans.** Any change to
canonicalization creates a new version. If this fails, every stored offset,
every gold annotation and every human label becomes invalid at once.

A3. **The unit is the evidence grain.** Model quotes are whole units. Gold quotes
may be parts of units, so they are compared in units. If units are too coarse,
evidence precision is bounded above by unit granularity.

A4. **Exhaustive traversal.** Every eligible unit is shown to the extractor in
some window. No retrieval step drops a unit first. If this fails, single-mention
themes are lost before any model sees them.

A5. **Signals are independent of each other's answers.** No judge sees another
trial, a score, or the extractor's identity. If this fails, agreement between
signals is inflated.

A6. **The judge families differ from the extractor's family and from each
other.** If this fails, a judge may share the extractor's errors.

A7. **Each target is assessed alone.** A claim's support depends only on its own
quotes and a fixed attribution context. If this fails, evidence spread across a
document is judged incomplete.

A8. **Reproducibility by replay.** Every model reply is cached under a key that
binds every input. A replay reproduces the run byte for byte with no model. A
changed input misses the cache and fails visibly. The method also re-verifies
every invariant at every consuming step. This is the largest non-inference cost
(see the cost model).

A9. **The required path runs only on open-weight, self-hosted models.** No call
is billable. A hosted model is allowed only for one optional quality-ceiling
comparison, with a fixed small budget. Open question Q5 asks the reviewer to
question this assumption.

A10. **Hardware.** One machine with 36 GB of unified memory runs all models. The
generative models run 4-bit quantized on its GPU. The two entailment scorers run
on its CPU. Both judges and the primary scorer must fit in memory at the same
time. This caps each judge at about 14B parameters.

## Notation

| Symbol | Meaning | Domain / units |
|---|---|---|
| 𝓔, e | Event set and one event (one issuer, one fiscal quarter) | finite set |
| 𝓘_τ, i | Firms in the cohort at quarter τ, and one firm | finite set |
| τ | Calendar period-end quarter | 8 quarters |
| π_{k,τ} | Prevalence of theme k in quarter τ | [0, 1] |
| Q_{e,k} | Accepted quotes that support theme k in event e | set of spans |
| Ŷ_e | System output for event e: themes present, each with its quotes | set of pairs |
| q | A stored quote text | Unicode string |
| ε_X, ε_C, ε_J | Share of extractor, classifier and judge calls that needed a second attempt | [0, 1] |
| ψ | The assignment policy in force | accept or review |
| d, d_e | A release document, and the one for event e | — |
| x_d | Canonical text of d | Unicode string |
| \|x_d\| | Length of x_d | code points |
| h(·) | SHA-256 of the UTF-8 bytes of a string | 256-bit digest |
| [a, b) | Half-open span of code-point offsets | 0 ≤ a < b ≤ \|x_d\| |
| M_d | Boilerplate masks over x_d (spans excluded from headline counts) | set of spans |
| U_d, u_i, n | Ordered leaf narrative units of d, one unit, their count | sequence; n ≈ 135 per document on train |
| L | Window character budget | 4,000 characters |
| ω_j, m | One window and the number of windows in d | m ≈ 5.5 per document on train |
| f_X | Extractor model | Gemma 4 31B-it, 4-bit |
| c = (S_c, ℓ_c) | Candidate: cited unit labels, and a claim sentence | — |
| r | Attempt bound for any model call | 2 |
| 𝒦, k, α(k) | Codebook, one theme, its parent theme | 22 themes, two levels |
| f_C | Classifier model | the same model as f_X |
| Θ_c | Proposed theme set for claim c | subset of 𝒦 |
| t = (c, k) | Support target | — |
| s_P(t) | Primary entailment score: quoted evidence as premise, claim as hypothesis | [0, 1] |
| s_A(t) | Alternative entailment score, same premise and hypothesis | [0, 1] |
| g_1, g_2 | Judge models of two families | Qwen2.5-14B-Instruct and Mistral-Nemo-Instruct (12B), 4-bit |
| p | Presentation order of a judge prompt | evidence first, or claim and theme first |
| T_{j,p}(t) | One judge trial: judge j, presentation p | four per target |
| σ, φ | A trial's claim-support and theme-fit answers | {supported, unsupported, uncertain}; {fits, does not fit, uncertain} |
| R_{j,p}(t) | A trial's reason codes | subset of 10 fixed codes |
| O(t) | Review outcome | O_ref, O_inc, O_flag, O_clear |
| ψ_θ | Cutoff policy on s_P with cutoff θ | accept or review |
| Γ | Preregistered cutoff grid | {0, 0.05, …, 0.95} |
| ρ | Recall floor in policy selection | 0.4 |
| y^σ, y^φ | Human support label: claim support and theme fit | same domains as σ, φ |
| y | Joint label: y^σ = supported and y^φ = fits | {0, 1} |
| κ_j | Cohen's kappa of judge family j against y | [−1, 1] |
| κ_0 | Preregistered agreement floor, on the lower bound | 0.4 |
| B | Bootstrap resamples, clustered by event | 10,000 |
| G_e | Signed gold for event e | theme presences, quotes, claims, hard negatives |
| K_s | Fresh repeat runs for stability | 3 |
| N_W, N_C, N_T | Window, claim and target counts of a run | integers |
| λ_X, λ_C, λ_J, λ_S | Mean wall time per extractor call, classifier call, judge call and scorer call | seconds |
| Λ_V | Wall time of verification and storage that sends no request | hours |

## Human labels and what binds them

All human labels must be kept. The table states each set, who made it, and what
it is bound to. The binding decides which method changes would orphan it.

| Label set | Size | Made by | Bound to | Survives a new model or prompt? |
|---|---|---|---|---|
| Signed gold G_e (train and dev) | 28 events (20 train, 8 dev) | Drafted by a frontier model in fresh sessions, then verified, read for omissions and signed by the owner | Canonical text x_d, its hash, unit identity, the codebook version | Yes, if canonicalization and the codebook stay fixed |
| Independent dev passes | 8 events | The owner alone, before any draft | Canonical text and unit identity; only their hashes and per-event figures are stored | Yes, on the same condition |
| Hard negatives | Inside each signed gold file, plus a curated fixture set | Part of the signed gold | Canonical text | Yes, on the same condition |
| Train support labels (y^σ, y^φ) | 70 targets, 63 usable | A hosted model, from a blinded view, under the owner's override; no human review | The target's identity, which is a digest of the source extraction run, the claim, the theme and their inputs | **No.** A new extractor, classifier, prompt or host changes every target identity |
| Dev support labels (y^σ, y^φ) | 24 targets (3 per event) | The owner, unaided, never seeing a score or a judge answer | The same target identity | **No**, for the same reason |
| Test gold | 7 events | Not yet made | — | — |

So the gold survives any change to C3 to C7. The support labels survive only if
C3 and C5 stay fixed. A faster extractor or classifier must either keep the
current runs as frozen inputs for calibration, or map old targets onto new ones
by their content. Q4 asks the reviewer about this.

## Computational cost model

### Call counts

The number of model calls in one pass follows from the method's structure:

$$
\begin{aligned}
\text{extractor calls} &\approx N_W \cdot (1 + \epsilon_X), \qquad N_W = \sum_d m_d \\
\text{classifier calls} &\approx N_C \cdot (1 + \epsilon_C) \\
\text{judge calls} &\approx 4\, N_T \cdot (1 + \epsilon_J) \\
\text{scorer calls} &\approx 2\, N_T \;(\text{one per scorer, plus per-quote signals})
\end{aligned}
$$

Each ε is the share of calls that needed a second attempt. On train, ε_X = 0,
ε_C ≈ 0.009 and ε_J ≈ 0.04. N_T ≈ N_C, because nearly every claim gets exactly
one proposed theme.

### Observed per-call cost (train pass, 20 documents)

All figures below were observed on the real train pass.

| Role | Calls | Mean prompt tokens | Mean output tokens | Mean wall time per call | Phase wall time |
|---|---:|---:|---:|---:|---:|
| Extractor f_X | 109 | ≈ 1,100 | ≈ 420 | λ_X ≈ 45 s | 1 h 22 min |
| Classifier f_C | 1,181 | ≈ 7,000 | ≈ 29 | λ_C ≈ 100 s | 33 h 21 min |
| Judges g_1, g_2, with the primary scorer | 4,863 | ≈ 1,700 | ≈ 127 | ≈ 14 s per cache entry | 19 h 30 min |
| Alternative scorer s_A (CPU) | 1,463 | — | — | ≈ 15 s | 6 h 15 min |

Three facts stand out:

- **The classifier dominates inference.** Each call resends the whole frozen
  codebook with the claim. So each call reads about 7,000 prompt tokens to emit
  about 29. The cost is prompt reading, not generation.
- **The judges are the second cost.** Each target costs four judge calls, and
  most of these trials disagree or object (see C6).
- **Memory pressure slows every call.** The machine swapped up to 22 GB. One
  episode of pressure doubled the classifier's reply time from about 80 s to about
  155 s.

On the dev pass (8 documents, 719 claims, 601 targets), the judges were about 1.7
times slower per call than on the fitting check. Their prompts were longer (about
2,500 tokens against 1,600). The primary scorer took 5.4 s per call on CPU, against
2.45 s earlier. The dev pass ran about 35 h across three processes, with a pause.

### The verification term Λ_V

The method re-verifies every invariant at every step that consumes a stored
record. Each cache key binds every input of its call, including whole source
bundles. One key is about 13 MB, and the train support cache holds 7,792 entries,
about 107 GB. Verification cost grows with targets × trials × attempts, and each
of several gates repeats it.

These figures were observed on real runs. None of these steps sends a model
request:

| Step | Wall time |
|---|---:|
| Train pass: write and read-back of the two support runs | ≈ 13 h |
| Loading the train pass for any label step | ≈ 32 min each |
| Calibration (load, validation, bootstrap) | 1 h 7 min |
| Full replay of the train pass (no model loaded) | 14 h 13 min |
| Full replay of the dev pass (no model loaded) | 10 h 58 min, 95% CPU-bound |

Two engineering passes cut a projected 115 h replay to a projected 7.2 h, from
floors measured on invented text. The real replay then took 14.2 h, about twice
the projection. The cause of the gap is not measured.

### Totals and projection

| Run | Wall time | Kind of figure |
|---|---:|---|
| Train pass, 20 documents | ≈ 60 h of model phases, plus ≈ 13 h verification | observed |
| Train replay | 14 h 13 min | observed |
| Dev pass, 8 documents | ≈ 35 h | observed |
| Dev replay | 10 h 58 min | observed |
| One fresh dev run for stability | 29 to 35 h; three are required | estimate |
| Full corpus: about 30 issuers × 8 quarters, about 240 events | ≈ 40 to 45 days of continuous running | projection by linear scaling from train; it ignores any growth in Λ_V |

The machine is also the owner's working computer. So the runs happen overnight
and pause by day. That stretches calendar time further.

### Cost against yield

The pilot's most expensive stages produced almost no usable output:

- C6 cost about 26 h on train. Of 1,170 targets, 1 was clear, 1,105 were
  flagged and 64 were incomplete. On dev, 5 of 601 were clear.
- So C7 could accept nothing. At every cutoff in Γ, recall on the train labels
  was 0. No cutoff reached ρ, and calibration selected no policy. Every target
  stays in human review.
- Neither judge family met κ_0 on train. These figures compare with labels that
  a model made (see the label table), not with a person.

The reviewer should judge whether the cost buys anything, and where.

## Per-component descriptions

### C1. Point-in-time cohort and event resolution

**Problem.** Choose the firms and their quarterly releases without hindsight.

**Procedure.** The cohort is the set of index members on each date, rebuilt from
dated membership sources and frozen with its own hash before any release is
fetched. An event is one firm's release for one fiscal quarter. It is eligible
if the firm was a member at the filing's acceptance time. The release is the
exhibit that a content check confirms. A 40-event pilot was drawn by a fixed rule
from frozen metadata before any release text was seen. It was split by issuer and
time into 20 train, 8 dev, 7 test and 5 excluded events.

**Assumptions.** Membership records are complete. Acceptance time is the right
availability time. A wrong exhibit choice would put a non-release in the corpus.

**Evaluation.** Release identification precision and recall against gold. Coverage
counts by processing state.

**Cost.** Deterministic and fast. It is not a cost driver.

### C2. Canonicalization and structural segmentation

**Problem.** Turn markup into one fixed text with stable offsets and typed
structure.

**Procedure.** A deterministic parser turns markup into text. It normalizes
Unicode and whitespace once, and hashes the result. It emits typed elements:
headings, paragraphs, list items, table cells and sentences. Each element has a
span in x_d. Units are the leaf narrative elements in reading order. Table cells
are a separate evidence type and are never quotable as prose. Boilerplate is a
mask over x_d, not a deletion.

**Assumptions.** The parser reads the source faithfully. A fidelity check against
rendered pages supports this on a fixture sample. The parser chose layout tables
as non-narrative, so some prose inside layout tables is not quotable. That limits
recall.

**Evaluation.** Element fidelity against hand-marked structure. Byte-identical
regeneration.

**Cost.** Deterministic, seconds per document.

### C3. Exhaustive pointer extraction

**Problem.** Find every claim in the release, with the units that support it,
without letting the model write the quoted text.

**Data-generating story.** Each unit u_i either does or does not carry one or more
claims. The latent truth is the set of claims and their supporting units. The gold
G_e records the human version of this set.

**Procedure.**

1. Pack the units of d, in order and by block, into windows of at most L
   characters. Each window also has one context line that cannot be quoted.
2. Show the extractor the window with labels U1 … Un in place of offsets. Ask it
   for a list of (labels, claim sentence) pairs in a closed JSON form.
3. Validate the reply. Retry once with feedback that names only fields and fixed
   reasons. Drop the window's reply after r attempts and record why.
4. Pass each candidate to C4.

Each window is one independent call. No window sees another window's output, and
nothing merges claims across windows. Decoding is greedy (temperature 0).

**Assumptions.** A claim rests on units that fall in one window. A claim that
spans a window boundary is split or lost. The model's recall within a 4,000
character window is high. This is assumed, not measured, apart from the gold
comparison.

**Evaluation.** Gold-evidence recall in units, unit-level F1, character-level
overlap as a secondary figure, and event × theme presence after C5.

**Cost.** About 5.5 windows per document, about 45 s per window. Not a cost
driver.

### C4. Deterministic span verification

**Problem.** Guarantee that every stored quote is the exact source text.

**Procedure.** A candidate passes only if every cited label opens a quotable line
of its own window. The quote is then x_d[a_i, b_i) for each cited unit. Before
storage, before any support judgment, before export, and at every later step that
reads it, the method checks

$$
0 \le a < b \le |x_d|,\qquad q = x_d[a, b),\qquad \text{stored hash} = h(x_d).
$$

A failure rejects the record and keeps the reason. Nothing is repaired.

**Assumptions.** None beyond A1 and A2.

**Evaluation.** Exactness is 1.0 over retained quotes by construction. So it is
reported only with retention, and a run that rejects everything fails.

**Cost.** The check itself is cheap. Its repetition at every consuming step,
with keys that embed full bundles, is the term Λ_V.

### C5. Deductive classification against a fixed codebook

**Problem.** Map each claim to zero or more themes of a fixed codebook.

**Procedure.** For each claim c, call the classifier once. Its prompt holds the
claim, its quotes, a fixed attribution context, and every theme definition with
its parent, inclusion and exclusion rules, examples and hard negatives. The reply
is a closed list of theme identifiers, plus optional topic, sentiment, direction
and event-type annotations. The most specific fitting theme is proposed, never its
parent as well. A reply that names both a theme and its ancestor is a hierarchy
conflict, and is retried once. A per-document ceiling of 128 requests bounds the
calls. Claims past it are cut and recorded as incomplete. On dev, one 220-claim
document lost 94 claims to this ceiling.

**Assumptions.** One call per claim, with no shared context between claims of a
document. The model reads 22 definitions with equal care on every call. Claims
are independent given the codebook.

**Evaluation.** Event × theme micro and macro F1 against gold at the exact level.
A parent-level roll-up F1 is secondary.

**Cost.** The dominant inference term: N_C calls × about 7,000 prompt tokens. On
train, 33 h for 20 documents. Most of each prompt is the same codebook text on
every call.

### C6. Semantic support assessment

**Problem.** An exact quote need not support its claim. The claim may misread
negation, period, scope or attribution. The theme may not fit. Decide, for each
target, whether both hold.

**Procedure.** For each target t = (c, k):

1. Compute s_P(t) with a self-hosted 770M-parameter factual-consistency checker.
   The premise is the quoted evidence and the hypothesis is the claim. Compute
   s_A(t) with an NLI cross-encoder from another family, as a comparison. Neither
   score sees the theme.
2. Run four judge trials, T_{j,p} for j ∈ {1, 2} and p ∈ {evidence first, claim
   first}. The content is the same in both presentations. Only the block order
   differs. Each trial returns σ, φ, a score in [0, 1], one contribution label for
   each quote, reason codes from a fixed list of ten, and a short rationale. Each
   trial gets at most r attempts. Only an unusable reply is retried. A valid
   negative or uncertain answer is final.
3. Derive the outcome by precedence:
   - O_ref if the target fails an integrity or exactness check;
   - otherwise O_inc if any required score or trial is unavailable after its
     attempts;
   - otherwise O_flag if any trial gives a reason code, an objection or
     "uncertain"; or the categorical answers differ across the four trials; or any
     quote is marked irrelevant, contradicting or uncertain; or support rests only
     on context;
   - otherwise O_clear.

So O_clear requires **unanimity** over four trials, on two questions, on every
quote's contribution, with no reason code at all. No numeric tolerance or
majority vote softens it. Scores are kept, but no score can override a
categorical objection.

**Assumptions.** Judges of about 14B parameters at 4 bits can follow the closed
reply form and the rubric. The rule's strictness is assumed to buy precision.
The pilot did not test that assumption. Order swapping is a bias check, not a
measure of stability.

**Evaluation.** Scorer AUC against y^σ. Judge κ and Gwet's AC1 against y, with
event-clustered 90% bootstrap intervals. On train, the AUC values rest on 2
negative labels out of 64. Kappa: Qwen 0.344 (0.180, 0.476), Mistral 0.005
(−0.092, 0.101).

**Observed outcome rates.** Train: 1 clear, 1,105 flagged, 64 incomplete, out of
1,170. Dev: 5 clear, 559 flagged, 37 incomplete, out of 601. About 2% of judge
trials stayed unavailable after two attempts, mostly for invalid quote
references.

**Cost.** 4 N_T judge calls plus 2 N_T scorer calls. About 26 h on train.

### C7. Assignment policy and its calibration

**Problem.** Turn support evidence into accept or review, with a known
precision, fitted on train labels before dev is seen.

**Procedure.** The preregistered menu holds one rule family: accept t if O(t) =
O_clear and s_P(t) ≥ θ, for θ ∈ Γ. On train labels, select

$$
\theta^\star = \arg\max_{\theta \in \Gamma}\ \text{precision}_{\text{train}}(\theta)\quad \text{s.t.}\quad \text{recall}_{\text{train}}(\theta) \ge \rho ,
$$

with ties broken toward fewer signals, then a lower cutoff. If no θ meets ρ,
select nothing, and every target stays in review. Labels were drawn from
targets with outcome clear or flagged, at most 5 per train event and 3 per dev
event, by a fixed seed, never by score.

The judge floor is reported, not used to decide. A family meets it if the 90%
lower bound of κ_j is at least κ_0.

**Assumptions.** Enough targets reach O_clear for a cutoff on s_P to matter.
The pilot shows this fails: with 1 clear target out of 1,170, recall cannot
exceed 1/41 for any θ.

**Evaluation.** Held-out precision and recall on dev labels, with event-clustered
intervals.

**Cost.** Small in itself. Its run time comes from loading and re-verifying the
stored pass (Λ_V).

### C8. Coverage-aware aggregation

**Problem.** Compute prevalence without treating missing documents as absent
themes.

**Procedure.** A processing-state table exists for every expected document before
any count: expected, unavailable, restricted, acquired, parsed, partial, failed,
completed, or completed with no theme. The denominator of π_{k,τ} uses only
completed states. Masked boilerplate spans and duplicate copies of a disclosure
do not count. Zero accepted assignments is never read as "no themes".

**Assumptions.** Missingness is unrelated to themes. This is not tested.

**Evaluation.** Hand-computed numerators and denominators on fixtures.

**Cost.** Small.

### C9. Evaluation against human gold

**Problem.** Decide whether the system works, with honest uncertainty, on a
small pilot.

**Procedure.** The pilot is a feasibility check, not a validation set. Train
figures are marked in-sample. Dev is evaluated once with the frozen baseline.
Each quality gate is the dev baseline's 90% event-clustered bootstrap lower bound.
A later configuration passes if its dev point estimate meets every gate.
Gold-evidence recall must be above 0, and an undefined metric fails. Stability is
measured by K_s fresh runs over dev, at temperature 0. So a near-perfect result
shows only runtime determinism. The test split is held out for one later
comparison.

**Gated metrics.** Release-identification precision and recall; event × theme
micro and macro F1; unit-level span F1; gold-evidence recall; support precision.

**Assumptions.** The event is the sampling unit. Twenty-eight events are enough
to expose gross failures, not to estimate rare-theme recall.

**Cost.** Small, apart from the three fresh stability runs, which repeat C3 to
C6 in full: about 30 h each.

## Assumptions and limitations of the whole method

1. **Strict unanimity in C6.** If any trial objects, the target is flagged. With
   four trials from small quantized judges, this sends nearly every target to
   review. The pilot's chain yield is about 0.1%.
2. **One classifier call per claim, each resending the codebook.** This makes C5
   cost about 100 s per claim on this hardware. The cost grows linearly with
   claims, and some releases have over 200 claims.
3. **Re-verification at every step.** Λ_V is about as large as the model phases.
   It also makes each label or calibration step take tens of minutes.
4. **Support labels bind to run identity.** Any upstream change orphans them
   (see the label table).
5. **Small, skewed label sets.** 62 of 64 usable train claim labels are
   "supported". AUC on 2 negatives says nothing. Train labels are model-made.
6. **Gold drafted by a frontier model.** Gold was model-drafted, then verified and
   signed by the owner. Dev was first labelled independently by the owner. A
   frontier-model comparison would share the drafter's family. The method
   records this but does not correct for it.
7. **One machine.** Memory pressure, swap and the owner's other work change call
   times by a factor of up to 2. The runs are serial: one request at a time.
8. **Temperature 0 everywhere.** Stability runs measure determinism, not
   sampling robustness.

## Open questions for the reviewer

Q1. **Where is the cost, and what is the state of the art for each term?** Which
of λ_C, the four-trial judge panel, and Λ_V should a better method attack first?
For C5, consider prompt-prefix caching, batching several claims per call,
classifying per window instead of per claim, a two-stage retrieval of candidate
themes, or a small trained classifier. For C6, consider fewer trials, a single
stronger judge, a cascade that calls judges only when the scorer is uncertain, or
dropping a judge family that shows no agreement. Rank them by expected time saved
against expected quality lost.

Q2. **Is the unanimity rule for O_clear sound?** Is there a published way to
combine two scorers and four judge trials into a calibrated support decision,
such as a learned aggregator, a latent-class model of rater reliability, or
selective prediction with a coverage target? What would it need from the labels
the system already has?

Q3. **Is the model choice right for this hardware?** A 31B model at 4 bits does
both extraction and classification on 36 GB. Would a smaller model, a
mixture-of-experts model, a different runtime with continuous batching, or
speculative decoding give a better quality per hour? Which published benchmarks
of quantized open-weight models on extraction or classification apply?

Q4. **How can the manual labels be kept through a method change?** The gold and
the independent passes bind to canonical text, so they survive. The 94 support
labels bind to run identity, so they do not. What is the sound practice: keep the
current runs frozen as the calibration set, re-key targets by content (claim
text, theme and quote spans), or re-label? Each proposal under Q1 to Q3 should say
which label sets it keeps.

Q5. **What would relaxing the local-only rule buy?** Separate two cases. (a)
Speed-ups that keep every model open-weight and local. (b) Rented GPU hardware
or a hosted model, with a budget. For (b), state the quality gain the literature
supports, the cost, the rights and reproducibility trade-offs, and the risk that a
hosted model of the gold drafter's family agrees with the gold for the wrong
reason.

Q6. **Is the re-verification design proportionate?** The method re-checks every
invariant at every consuming step, with cache keys that embed whole bundles. What
do reproducible pipelines in the literature do instead, for example
content-addressed storage with one check at write time, or Merkle-style digests,
while keeping the exactness guarantee?

Q7. **Is exhaustive windowed traversal the right discovery design?** Would a
document-level pass, a hierarchical pass, or long-context reading with
pointer output keep the coverage guarantee at lower cost? What does recent work on
long-context recall say about 4,000-character windows against whole releases of
this size?

Q8. **Is the evaluation design adequate for a 28-event pilot?** Are
event-clustered bootstrap lower bounds a sound way to set gates at this sample
size? Is κ the right agreement statistic when 62 of 64 labels are positive?
