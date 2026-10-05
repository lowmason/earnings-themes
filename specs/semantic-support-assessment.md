# Semantic support assessment

**Status: SPEC APPROVED (2026-10-05)** — Stage 8; ready for writing-plans.

> For agentic workers: REQUIRED NEXT SKILL: writing-plans. This is the stage spec
> for Stage 8 of `specs/evidence-linked-theme-extraction-roadmap.md`. Plan this
> stage alone, in one plan. Do not implement Stage 9 coding or Stage 11 calibration
> with it.

Stage 8 assesses a proposed claim–theme pairing against its exact quoted evidence.
It consumes Stage 7's stored, codebook-free quote-claim contracts, re-verifies the
evidence, records an open-weight entailment score, and obtains independent model
judgments of claim support and theme fit. Its output is an auditable collection of
signals and review outcomes, never an accepted assignment.

Stage 9 proposes themes and calls this assessor before deciding which assignments
to retain. The roadmap is an implementation sequence; this runtime call introduces
no dependency on Stage 9 code. Stage 8 can be built and tested with explicit fixture
targets before the classifier exists.

The Stage 8 implementation must satisfy R8.1, R8.3, R8.5, the scorer and judge
machinery of R8.2/R8.4, the metric functions of R8.6, and V4, with R6.1 at the
support gate. Stage 11 owns
expert labels, judge calibration, pooling choices, the agreement floor and
production thresholds, observed support quality, and fresh-call stability. Stage 8
does not discharge those Stage 11 obligations.

## Basis and locators

- **R8.1–R8.6, R6.1, R14.1, R14.6, R14.7, V4:**
  `specs/evidence-linked-theme-extraction.md`.
- **The roadmap:** `specs/evidence-linked-theme-extraction-roadmap.md`, the
  2026-10-05 reconciliation after Stage 7, including its uncommitted reconciliation
  at design time. Its Stage 8 theme-definition input question is resolved here.
- **Stage 7:** `specs/completed/evidence-selection-and-verification.md`, especially
  ES2, ES3, ES11, ES22, Records, Storage, and Handoffs to later stages; implemented
  by plans 11 and 12, merged at `f4081c9`.
- **GS13:** `specs/completed/pilot-codebook-split-and-gold-set-protocol.md`, Decisions.
  It binds until the last Stage 14 test gold bundle is drafted.
- **Deferred items:** `specs/deferred_items.md`, sections
  `9-pilot-codebook-split-and-gold-set-protocol`,
  `11-evidence-selection-and-verification-plan-a`, and
  `12-evidence-selection-and-verification-plan-b`.
- **SSn:** this spec's decisions, approved in the Stage 8 brainstorming session on
  2026-10-05. The session opened no pilot document text or signed pilot gold, made
  no inference call, and sent no SEC request. It read the committed curated hard
  negatives over Stage 1 fixtures and the codebook's records, without opening the
  pilot passages its examples reference.

## Decisions

| ID | Decision |
| --- | --- |
| SS1 | **Explicit targets.** The caller supplies a stored extraction run, matching canonical bundles, an approved codebook, and document-scoped claim–theme targets. Stage 9 owns theme proposals; Stage 8 owns assessment. Stage 7 remains codebook-free. |
| SS2 | **Frozen definitions.** The assessor resolves the selected theme's definition and inclusion/exclusion rules from the codebook identified by ID, version, and hash. A caller cannot replace the definition. Examples are not dereferenced. |
| SS3 | **Exactness first.** All linked quotes pass `reverify_span` before any scoring, before support-result publication, and at the downstream consuming gate. One invalid or missing link refuses the entire target. |
| SS4 | **Two semantic axes.** Entailment scores source evidence against the unchanged claim. The judge separately assesses claim support and theme fit. A codebook definition is never placed in the entailment premise as evidence. |
| SS5 | **Primary scorer.** MiniCheck-Flan-T5-Large, the 770M MiniCheck-FT5 choice in R8.2. A narrow local adapter obtains raw support scores with no wrapper chunking, maximum-over-chunks aggregation, or built-in cutoff. V4 pins the actual checkpoint and runtime. |
| SS6 | **Named alternative.** A fine-tuned DeBERTa-v3-base NLI adapter behind the same interface, explicitly selected for a comparison. It never silently replaces a failed primary. No new fine-tuning is undertaken here. |
| SS7 | **Multiple quotes.** Store per-quote scores and a distinct joint-evidence score. Noncontiguous quotes retain separate records and are presented as individually labeled passages. No maximum or average becomes an acceptance rule. |
| SS8 | **Attribution context.** The judge receives the containing narrative block and preceding heading separately from quoted evidence. Context can disambiguate attribution, time, or negation; it cannot supply a missing assertion. |
| SS9 | **No silent truncation.** Each adapter checks the complete rendered input against its declared limit. An over-limit signal is recorded as unavailable with `input_too_long`; it is never scored after clipping. |
| SS10 | **Independent cross-family panel.** Two configured open-weight judge families, different from each other, with at least one different from the extractor. Family lineage is explicit configuration, not inferred from an alias. |
| SS11 | **Two presentations per family.** Evidence-first and claim/theme-first, with identical content and roles and document-order evidence in both. Four independent trials per target; no judge sees another result or the entailment scores. |
| SS12 | **Typed judge signals.** Separate categorical claim-support and theme-fit answers, an uncalibrated joint-support score, a contribution assessment for every supplied quote, reason codes, and a bounded local rationale. |
| SS13 | **No rewriting or promotion.** A closed reply schema admits no replacement quote text, offsets, claim, theme definition, new theme, tool request, or accepted status. Invalid evidence cannot reach a judge. |
| SS14 | **Review outcomes.** `refused`, `incomplete`, `flagged`, and `assessed` describe assessment processing. None is an accepted assignment or a ground-truth support label. |
| SS15 | **Bounded retries.** At most two attempts per judge trial, provisional. Only an unusable response is retried. A valid negative or uncertain answer is final for that trial. |
| SS16 | **Separate versioning.** `SUPPORT_SCHEMA_VERSION = 1` and `SUPPORT_VERSION = "semantic-support/1"`. No change to core schema 2, extraction schema 1, or Stage 6 schemas. |
| SS17 | **Persistence and replay.** Explicit Polars/Parquet support records, an immutable run manifest, and a support-specific raw-signal cache. Cached evidence is still re-verified. Stage 11 adds fresh-call bypass. |
| SS18 | **Explicit ceilings.** Caller-supplied scorer-evaluation, judge-request, and token ceilings include all presentations and retries. Exhaustion is visible; missing signals never imply unsupported content or no themes. |
| SS19 | **Metrics without calibration.** Pure AUC-ROC and accepted-claim precision functions consume external binary human labels and acceptance decisions. Stage 11 chooses views and reports observed quality. |
| SS20 | **Fixture development.** Tests use synthetic text and Stage 1's canonical fixtures, including the 29 curated hard negatives with their original partial-unit spans. Invented cases cover negation, which the curated set lacks. |
| SS21 | **GS13.** No pilot extraction, signed pilot gold reading, gold drafting, or pilot example dereferencing. Drafting modules import no support code. Prompts use invented examples; replies and rationales remain local. |
| SS22 | **One stage and one plan.** No command or Stage 5 state-table write. Stage 10 owns the first extraction command; Stage 11 owns the first pilot extraction, calibration and stability; concurrency remains with Stage 15. |

The alternatives considered were exhaustive claim-by-theme scoring inside Stage 8
and claim-only support with theme support postponed to Stage 9. SS1 was approved:
the first alternative would make the assessor perform theme discovery; the second
would leave its R8.1 theme-specific input unresolved.

## Scope

In:

- target resolution and input integrity checks over Stage 7 records;
- canonical evidence/context views and exact-span reverification;
- a scripted entailment adapter, the local MiniCheck primary, and the DeBERTa
  alternative, with a shared scorer interface;
- typed independent judge trials, using the existing local chat transport;
- support-specific signals, review outcomes, ceilings, cache, and immutable store;
- pure metric functions, offline contract tests, a V4 gate, and a verification
  record.

Out:

- theme proposal, classification, assignment acceptance, novelty routing, direction
  attributes, or parent-theme roll-ups: Stages 9 and 10;
- pilot document extraction or reading, signed pilot gold, annotation, judge
  calibration, numeric quality thresholds, pooling selection, agreement-floor
  selection, and fresh-call stability/bypass: Stage 11, with test gold at Stage 14;
- changing codebook v0, resolving its example passages, or adding an inferred sector;
- extraction-record hardening beyond the target's consuming checks;
- concurrent workers, hosted inference, Jev, model training, a new workflow
  framework, or choosing the production model.

## Ownership and interfaces

`earnings_themes.support` owns the domain logic. It imports core span/hash helpers
and the existing themes contracts; it imports neither ingestion nor the application.
The application will load artifacts and pass them in at Stage 10. No package reads
a repository-relative configuration or prompt implicitly, downloads weights on
import, opens a client on import, or searches for a latest codebook.

Public seams:

- `resolve_target(stored_run, bundles, codebook, target)` produces an immutable
  resolved assessment input, or a refusal naming the target and reasons.
- `assess_target(input, scorer, judges, policy, allowance)` produces signals,
  individual trials, usage, and a review outcome. It performs the R6.1 gate itself;
  possessing a resolved input does not waive a re-check.
- `assess_run(...)` coordinates targets in supplied order under explicit ceilings.
- `write_support_run(directory, result, sources)` and
  `read_support_run(directory)` persist and read the support artifacts. Consumers
  pass the source records and bundles again before using a stored result.
- Metric functions accept explicit labeled observations; they discover no artifact
  or partition themselves.

The stage's models and enums are documented in `docs/data-dictionary.md` in the
implementation change, with producer/consumer contract tests.

### Reusing chat transport

Stage 7's local transport already sends messages, a schema, and parameters, refuses
non-loopback endpoints, ignores environment proxies, follows no redirect, sends no
key or tools, and checks the reply's model identity. Reuse those behaviors.

Introduce a small structural chat-request protocol covering `messages`,
`reply_schema`, and `parameters`, which the local adapter's `body` and `complete`
accept. Existing `ModelRequest` satisfies it unchanged; a support `JudgeRequest`
also satisfies it, with a support-specific subject. Stage 7's serialized requests,
record fields, cache keys, `ModelAdapter` seam, and outcomes stay unchanged. The
support runner translates transport failures into its own problem vocabulary.

The support code does not put assessment IDs into extraction window fields, reuse
`EXTRACTOR_VERSION` for a judge, or adopt extraction cache semantics as a support
contract. Only `extraction.local` needs to import httpx. A caller supplies the local
adapter explicitly; the default support package does not import that module.

The NLI adapter lives in `support.nli`, behind an explicit `support-nli` extra.
Dependencies needed for local weights stay in that extra. Loading them occurs only
when constructing the concrete scorer; the plain support package and default fake
tests need none of them. Verify Python 3.14 and platform compatibility before
pinning them, then review the lockfile diff without unrelated upgrades.

## Input boundary

### An assessment target

A target names its source extraction run, `doc_id`, `claim_id`, selected `theme_id`,
and expected codebook ID/version/hash. Its derived `target_id` hashes that identity
and the resolved input content. Quote IDs are resolved from the stored claim, not
supplied as an alternative set by the caller. A caller cannot drop a difficult quote
or rewrite a claim inside an assessment request.

The production source is `StoredRun` from
`earnings_themes.extraction.store.read_run`. Its reader validates rows and schemas;
it does not verify evidence. Stage 8 checks, before dispatch:

- the source run's document/hash mapping, matching `DocumentRecord`, and supplied
  bundle agree on the immutable document;
- the requested claim occurs exactly once under `(doc_id, claim_id)`;
- quote references are nonempty and distinct, and each resolves exactly once under
  `(doc_id, quote_id)`; conflicting duplicate quote records are refused;
- each quote ID agrees with its span, its document/hash matches the source, and the
  current masks match the bundle's masks;
- `bundle_problems` finds no element or mask problem, and every linked span passes
  `reverify_span` under the current `VALIDATOR_VERSION`;
- the claim's words and referenced evidence match the resolved-input hash.

Nothing treats loading, a type annotation, or an earlier `validator_version` as
proof. Reverification reconstructs the evidence from canonical text. One bad quote
refuses the whole target, preserving Stage 7's whole-candidate policy.

These are consuming checks on the records needed for support. They do not move all
of plan 12's deferred window/count validators into Stage 8.

### The approved definition

Consume the existing Stage 6 `Codebook` and `Theme` contracts. Recompute
`codebook_hash`, compare it with both the codebook's hash and the target's expected
reference, require approved status and approval metadata, and require exactly one
matching theme. Check unique theme IDs and a valid, acyclic parent-reference graph.
An unknown theme, `unmatched`, a draft, a changed hash, or a stale expected reference
refuses the target.

The model-facing snapshot contains the selected theme's ID, label, parent ID,
definition, inclusion rules, and exclusion rules, plus the frozen codebook reference.
These strings are copied exactly from the supplied approved record. Parent rules
are not inherited implicitly, examples are not opened, and sector tags are not
turned into issuer classifications. Stage 9 owns coding and hierarchy choices.

Stage 6's `validate_codebook` remains responsible for discovery-corpus and example
validation: it needs the pilot training bundles. Stage 8's integrity gate does not
call it or pretend to have revalidated those passages. Full approval validity is
established upstream; the current assessment binds to that frozen artifact.

## Evidence and attribution context

Every quoted passage is the re-verified canonical slice, with its original offsets,
hash, element ID, and masks. Sort passages by `(start, end, quote_id)` for
presentation; preserve the claim's original references in provenance.

For the judge's context, select the nearest containing `paragraph`, `list_item`, or
`footnote` in the quote element's parent chain, including that element itself. If
none exists, use the quote element. A partial quote's containing sentence is
therefore still visible as context. A candidate context block must stay inside the
quote's innermost enclosing section and speaker turn, when present.

Supply the nearest preceding element typed `heading` as separately labeled context:
its end must be at or before the context block's start, and it must stay within those
same enclosing boundaries. Choose the greatest end, then greatest start, then
lexicographically smallest element ID to break ties. Duplicate context elements
appear once, in document order. Adapting this release-only rule to transcripts
belongs to Stage 13.

Context is sliced without normalization from the same canonical document and carries
element/span/hash references. It is not a new `Quote`, an evidence repair, or a
license to use an unquoted assertion. Absence of a heading remains absence. The
assessor infers no issuer identity, fiscal period, speaker, or role to fill a field.

Prompts distinguish quoted evidence, attribution context, the model-derived claim,
and codebook rules. All are data, never executable instructions. Only the quoted
evidence can support the claim; context can resolve its referents or expose a
contradiction. A judgment requiring an assertion found only in context flags
`context_only_support`. Stage 9 may later propose different evidence, but this
assessment never substitutes it.

The scorer receives only the exact quoted evidence and unchanged claim. For joint
scoring, it receives a versioned rendering of individually labeled passages with
explicit boundaries. That rendering is a model input, never a stored verbatim
quote. It inserts neither an ellipsis into quote text nor a claim of continuity.

## Entailment signals and V4

### The scorer interface

`EntailmentScorer` exposes its identity, input limit, and a scoring operation over
an exact premise and unchanged hypothesis. A successful result has a finite raw
support score in `[0,1]`, input token count, latency, model/runtime identity, and
input hash. A failure has a reason and no score; it never returns zero as a stand-in.
The scripted fake implements the same contract.

Produce one signal for each `(target_id, quote_id)` and one joint-evidence signal.
For a one-quote target, the joint signal may reference the identical raw evaluation
without dispatching twice. For several quotes, keep the joint evaluation separate.
Neither per-quote scores nor the joint score are reduced to a pass/fail label.
Low individual scores may reflect distributed support; a high individual score
does not validate the other passages.

Keep the claim exactly as Stage 7 stored it. Do not paraphrase, atomize, or split it
silently for the scorer. Compound-claim and distributed-evidence limitations are
recorded and exercised by fixtures; the judges can report partial support.

### Primary and alternative

The primary is `lytang/MiniCheck-Flan-T5-Large`, matching R8.2's MiniCheck-FT5.
The local adapter uses the checkpoint's documented premise/claim encoding and
support-label logits, then returns the raw two-label support probability. Assert
the expected tokenizer/label mapping for the pinned checkpoint at the V4 gate.
Inference runs in evaluation mode from verified local files, with no automatic
download or remote custom-code loading.

Use a narrow inference adapter rather than MiniCheck's convenience wrapper. The
wrapper's published source splits input, takes the maximum score over chunks, and
uses 0.5 for a label; its tokenizer also truncates. None of those defaults governs
this project. Tokenize the complete versioned input without truncation and refuse
an over-limit evaluation explicitly. No chunking or threshold is hidden inside the
adapter.

The named alternative is
`MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`, an already fine-tuned DeBERTa-v3-base
NLI checkpoint. It uses the checkpoint's explicit entailment/neutral/contradiction
label mapping and exposes raw entailment probability through the same interface.
Select it explicitly for comparison; never automatically fall back to it on an
error. The MiniCheck primary remains selected by default. Benchmarking their
quality belongs to Stage 11, not the V4 hosting smoke.

Model evidence checked on 2026-10-05:

- [MiniCheck model card](https://huggingface.co/lytang/MiniCheck-Flan-T5-Large):
  identifies the Flan-T5 grounding model and lists MIT licensing.
- [MiniCheck wrapper](https://github.com/Liyan06/MiniCheck/blob/main/minicheck/minicheck.py)
  and [inference implementation](https://github.com/Liyan06/MiniCheck/blob/main/minicheck/inference.py):
  evidence for the wrapper behaviors and the checkpoint's score encoding.
- [DeBERTa alternative model card](https://huggingface.co/MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli):
  identifies its NLI fine-tuning and lists MIT licensing.

These checks identify candidates and document the design; they do not discharge V4.
At implementation time, confirm the selected weights' terms permit this research
use and recheck the exact revision and inference API. Do not substitute a model's
software license for its weight license or record an unperformed run.

### V4 gate

1. Pin the primary's immutable repository revision, model configuration, tokenizer,
   and every inference file by SHA-256. Pin runtime/dependency versions, device,
   precision, input limit, and adapter encoding version.
2. Record the weight-license source, terms, verification date, and intended use in
   an ADR and `docs/verification/semantic-support.md`. Record the alternative's
   corresponding identity/license before enabling it.
3. The user acquires the weights outside the default tests. Inference loads from
   those verified local files with network access disabled. No import or ordinary
   assessment initiates a download.
4. Run the primary on invented text in an opt-in test, by its node ID with `-m live`.
   Confirm actual inference, a finite score, complete input handling, and no network
   or inference API call. Missing weights can skip development tests visibly but
   cannot satisfy the V4 completion gate.
5. Store the exact checkpoint and runtime identity in the support run manifest and
   the observed test outcome in the verification record. The alternative gets a
   separately named local smoke if enabled; it is not evidence that the primary ran.

Never run all tests with `-m live`: the repository's SEC live tests can send
requests. V4 makes no earnings-source request, no billable call, and no quality
claim about the earnings task.

## Model-judge signals

### Panel identity and independence

A judge configuration carries its model ID, weight hash/revision, runtime/version,
family lineage, and input/output limits. The caller supplies the extractor's family
lineage alongside the source run, whose existing identity lacks that field. No
extraction schema bump or name-based inference is needed. Missing lineage, equal
judge families, or a panel entirely in the extractor's family refuses the run at
preflight, before either a scorer or judge is dispatched.

Both judges are open-weight and self-hosted. Their actual checkpoints are explicit
configuration choices, with verified weight licenses before live use; Stage 7's
ADR 0004 chooses no judge or production model. Stage 8's default contract tests
need only scripted judges. Stage 11 selects and calibrates the live panel before
production use.

Each family receives two independent presentations:

- `evidence_first`: quoted evidence and attribution context, then claim and theme;
- `claim_theme_first`: claim and theme, then the same quoted evidence and context.

Within each block the text, roles, rules, and quote order are identical. NLI premise
and hypothesis are never reversed. Neither presentation sees the primary score,
extractor identity, another trial's answer, or another judge's rationale. Only
validation feedback for that trial's unusable reply may enter its retry.

Run the four trials sequentially, under the same policy and explicit ceilings.
Default temperature and seed may be zero as provisional settings; that is not a
stability claim. Family/model configuration and both presentation hashes persist.

### Closed reply contract

| Field | Contract |
| --- | --- |
| `claim_support` | `supported`, `unsupported`, or `uncertain`: does the cited evidence support the unchanged claim, with its attribution, time, scope, and polarity? |
| `theme_fit` | `fits`, `does_not_fit`, or `uncertain`: does the claim, insofar as supported, fit the selected definition and its inclusion/exclusion rules? |
| `joint_support_score` | Finite number in `[0,1]`, an uncalibrated ranking signal for both conditions holding. It is not a calibrated probability or acceptance decision. |
| `quote_assessments` | Exactly one entry for each supplied quote ID: `supporting`, `contextual`, `irrelevant`, `contradicting`, or `uncertain`, describing its contribution. Unknown, repeated, or missing references invalidate the reply. |
| `reason_codes` | A distinct list from the fixed vocabulary below; no arbitrary map keys. |
| `summary` | Nonblank rationale of at most 500 characters, provisional, retained locally and excluded from printable representations. |

The reason vocabulary is `wrong_attribution`, `wrong_period`, `negation`,
`scope_mismatch`, `partial_support`, `theme_mismatch`, `exclusion_conflict`,
`context_only_support`, `insufficient_evidence`, and `compound_claim`. Numerical
scores and categorical answers are preserved independently; no numeric cutoff is
invented to force agreement between them.

Every key at every level is closed. Replacement text, offsets, hashes, definitions,
new themes, tool calls, an accepted status, or a claimed verification bypass are
unusable replies, not suggestions to apply. The runner owns target identity and
exactness. A model can report a semantic objection, never modify these inputs.

Prompts live in `prompts/support/`, and the caller supplies their text. Examples are
invented, with no release wording, gold examples, or previous extraction results.
Bound rationale length, use the same rubric in both presentations, and judge the
claim/evidence rather than the verbosity of an extractor's explanation. No such
explanation or chain of thought is supplied.

### Retries and outcomes

At most two attempts per trial. Retry malformed JSON, schema/reference violations,
tool-call replies, model mismatch, or transport failure within the allowance. Feedback
names fields and fixed reasons, never input values or source wording. Keep the raw
reply locally and count any reported usage even when the reply is refused.

A valid `unsupported`, `does_not_fit`, or `uncertain` answer is final for its trial.
Judges do not debate, vote a refusal away, or get another attempt to become positive.
All usable and unusable attempts remain auditable.

Review outcomes are derived in this precedence order:

1. **`refused`:** target integrity, codebook, or exact-span gate fails. No signal is
   dispatched for that target. Invalid panel configuration is a run-level refusal
   at preflight, before any target is assessed.
2. **`incomplete`:** any required entailment signal or judge trial remains unavailable
   after its bounded attempts, including input limit, replay miss, or exhaustion.
   Keep any known semantic flags alongside this outcome.
3. **`flagged`:** all required signals exist, but any trial reports a reason code,
   objects, or is uncertain;
   categorical claim-support/theme-fit/quote-contribution answers change by family
   or presentation; a quote is irrelevant, contradicting, or uncertain; or support
   relies on an assertion only in attribution context. Record all reasons.
4. **`assessed`:** all required signals exist with no categorical objection. A quoted
   context contribution may be reported without implying that quote independently
   supports the theme.

Record numeric score differences without inventing a disagreement tolerance.
Disagreement is neither collapsed into a majority vote nor called uncertainty in the
source document itself. There is no automatic rejection based on an uncalibrated
score; semantic objections are review flags at this stage. Exactness failures are
deterministic refusals.

An `assessed` result cannot enter accepted analytical rows on that status alone.
Stage 9 owns assignment decisions, must respect refusals and missing evidence, and
must not turn contextual or irrelevant quote contributions into theme evidence.
Production use requires Stage 11's recorded calibration and policy. Unanimous model
answers do not discharge R8.3 or R8.4.

## Records, cache, ceilings, and storage

All support records carry `SUPPORT_SCHEMA_VERSION = 1`. The named policy
`semantic-support/1` covers resolution, context selection, input rendering, scoring
granularity, the judge rubric, presentation orders, retries, and review outcomes.
Changing any of those invalidates derived support results.

| Record | Grain and essential content |
| --- | --- |
| Target | Source run reference, document and claim identity, claim/input hashes, ordered evidence references, selected codebook/theme reference, derived target ID. |
| Evidence/context reference | Target and quote/element identity, canonical hash, offsets, text hash, current verification version for quotes, and current masks. Context is explicitly tagged. No duplicated quote text. |
| Entailment signal | Target, per-quote or joint scope, scorer/checkpoint identity, input hash, raw score or unavailable reason, tokens, latency, and cache status. |
| Judge trial | Target, family/model identity, presentation, attempts, typed answer or unavailable reason, raw reply reference, prompt/schema/request hashes, usage, latency, and cache status. |
| Review outcome | Target, `refused`/`incomplete`/`flagged`/`assessed`, all flags, missing-signal reasons, and references to the contributing signals. |
| Support run | Run ID, UTC time, source-run and document bindings, codebook/configuration hashes, model/family/checkpoint/runtime identities, support/schema/verifier versions, software/lock identity, explicit ceilings, counts and usage, and `billable_cost = "none, self-hosted"`. |

The cache stores raw scorer results and raw judge replies, apart from derived review
outcomes. Keys cover document identity/hash, claim and exact evidence/context input,
codebook/theme reference, scorer or judge identity with revisions/file hashes,
runtime/device/precision, model settings and limits, presentation order, prompt,
reply schema, rendered request, support version, and verifier version. Include source
provenance in derived target/run identity. Reuse never trusts a cached exactness or
review decision.

`replay` serves hits and makes no call on a miss; a miss records `replay_miss`.
`live` also serves hits; only misses dispatch. These names do not promise fresh
calls. Add no bypass here: Stage 11 must bypass both scorer and judge response caches
as well as extraction replay when its chosen stability experiment needs fresh calls.

Every run passes scorer-evaluation ceilings per target/document/run, judge-request
ceilings per target/document/run, and judge-token ceilings per document/run. Count
all families, presentation orders, and retries. Before a scorer evaluation, reserve
one evaluation and check the full input limit. Before a judge dispatch, reserve one
request and the complete input plus allowed completion tokens; missing actual usage
retains the reservation and is reported, never treated as zero. Cache hits consume
no dispatch allowance. A one-quote joint alias consumes no second evaluation.

Preflight metadata, configuration, identities, and ceilings before dispatch. Expected
adapter failures become unavailable signals and usage records. A corrupted source or
cache is refused safely; do not catch it as semantic unsupported. Unexpected errors
fail visibly by type with no text-bearing exception output; completed raw calls stay
cached. Durable recovery across arbitrary process failure is not introduced here.

Write a new run directory containing `run.json` and one explicit-schema Parquet file
per record kind. Publish a complete hidden sibling directory atomically; clean it
on a failed write, and refuse an existing destination. A pre-publication gate
re-verifies evidence and source/codebook bindings for every non-refused result.
Refused targets remain auditable as IDs/hashes/reasons, without claiming an accepted
evidence reference. `read_support_run` checks schema, typed fields, reference
integrity, and manifest hashes; the consuming gate still re-verifies source evidence.

Stage 8 writes only test temporary directories. Later callers choose local ignored
directories. Raw replies, rationales, requests, and any detail that could quote a
document stay uncommitted and local. No hosted tracing or paid endpoint is introduced.

## Metric functions and the Stage 11 boundary

Supply pure functions for:

- **AUC-ROC:** binary human support labels against one explicitly chosen continuous
  signal view, with tied scores earning half credit;
- **accepted-claim precision:** supported human labels among externally accepted,
  labeled targets. Acceptance is supplied by the caller, never inferred from
  `assessed`, a score, or a judge answer.

Require stable target IDs and an explicit label task (`claim_support` or
`joint_support`). Reject duplicate IDs, invalid labels, nonfinite/out-of-range
scores, mixed tasks, and mismatched joins. Distinct judge families/presentations
are distinct views of the same targets, not four independent human observations.
Per-quote scores need per-quote labels if evaluated; do not assign a joint claim's
label to each passage automatically.

Report labeled/scored/accepted counts, missing-score and missing-label counts, and
the view and task. A one-class or empty AUC is `None` with its reason. Precision
with no labeled accepted target is `None`, never 1.0. Precision describes the labeled
accepted subset; also report accepted targets without a human label. No missing
observation is converted to unsupported or zero.

Stage 11 supplies at least 50 expert support labels, chooses any pooling or numerical
decision policy, reports judge-to-human agreement, and pre-registers its agreement
floor before production use. It reports AUC-ROC for both scorers and precision on
accepted claims, alongside coverage/retention and R12.8's reject-everything check.
No model panel, fixture smoke, or replay result is a substitute for this calibration.

Stage 11 also owns fresh-call cache bypass and k-run stability. Stage 8's four
presentation/family trials are bias checks, not independent-run stability evidence.
Train gold first informs pipeline prompts at Stage 11; dev/test gold never does.
GS13 continues through Stage 14's test-gold drafting.

## Verification and blinding

Default tests are offline. No test invokes a real model, downloads weights, sends
an SEC request, opens a browser, or requires a credential. Fake adapters exercise
the orchestration and signal contracts; a no-network guard surrounds those runs.
The sole completion-time real inference is the V4 opt-in primary smoke on invented
text, with network access blocked.

### Contract cases

- **R6.1:** a stored quote round-trips and re-verifies; altered text, float/bool
  offsets, wrong document/hash/element, invalid locator, OCR evidence, and a changed
  canonical version refuse the target before either adapter is called. Missing,
  duplicate, or cross-document quote links cannot pass by matching bare IDs.
- **Theme boundary:** a draft, unknown theme, stale hash, duplicate theme ID, changed
  definition, and invalid parent graph refuse before inference. The model receives
  the exact selected definition/rules. No example passage is opened.
- **R8.1:** exercise all 29 curated hard-negative claims through a fixture-only
  translator into the same resolved quote-claim input. Reconstruct their original
  partial spans through core checks; never expand them to whole units or label them
  as extractor output. Source provenance is the curated fixture's hash and IDs.
  Scripted objections for issuer, period, and section produce visible flags.
- **Negation and positives:** invented canonical fixtures add negated assertions,
  competitor references, prior periods, clear supported positives, wrong-theme
  positives, context-only support, and distributed/compound evidence. A complete
  positive can be `assessed`; negatives can be `flagged`. This discriminates routing
  and does not claim model accuracy.
- **R8.3:** persist raw scores separately from outcomes. A high NLI score does not
  erase a judge's wrong-theme objection, unanimous judges cannot create acceptance,
  and per-quote/joint scores are not reduced by maximum or average.
- **R8.4 machinery:** verify two distinct families, one different from the extractor,
  and exactly two fresh-context presentations per family. The same content arrives
  in the two block orders, with no scorer/other-trial answer exposed. Categorical
  order/family disagreements flag; numeric differences remain raw.
- **R8.5/R14.7:** use an invented injection document and obeying fake replies. Tools,
  evidence edits, claim or codebook rewrites, new themes, invalid references, and an
  accepted status are refused as unusable. No tool exists to execute and no input
  record changes. Invalid spans never reach a judge that could promote them.
- **Failure semantics:** valid negative/uncertain replies are not retried; malformed
  replies have at most two attempts. Limits, misses, transport failures, partial
  panels, and exhaustion keep distinct reasons and never become no-theme cases.
- **Cache/store:** every key component has a changed-input miss case; identical
  inputs replay without dispatch. Tampered evidence cannot pass through a cache hit
  or stored-result reuse. Round-trips, schema/reference mismatches, existing output
  refusal, and interrupted publication are exercised.
- **R8.6 machinery:** hand-computed ranked/tied AUC and precision cases, one-class
  AUC, empty acceptance, missing labels/scores, invalid joins, and separate judge
  views establish metric semantics without opening the pilot.

### GS13 and safe output

These constraints apply to the implementing session and every implementer/reviewer
it dispatches:

- Never open, search, print, or paste anything under `data/`, pilot document text,
  signed pilot gold, drafts, working copies, or views. Stage 8's curated negative
  fixture is permitted; it references Stage 1's committed canonical fixtures.
- Never draft gold in this session or a subagent, or turn pipeline output into a
  gold draft. Drafting happens in fresh user-started sessions under its existing
  brief and cannot see Stages 7–9's code, prompts, or outputs.
- The six drafting modules (`gold.py`, `annotation.py`, `anchoring.py`,
  `codebook.py`, `records.py`, `tomlfile.py`) import nothing from support, directly
  or transitively. Extend both the AST and fresh-interpreter import guards and
  prove the guard detects a planted forbidden import. Leave the briefs unchanged.
- Use invented prompt examples. The existing wording guard includes
  `prompts/**/*.md`; its fixture leg checks support prompts. The user runs its pilot
  leg as a gate with only IDs/reasons/counts reported, since the gate session stays
  blind. Do not extend Python strings from release wording.
- Printed errors, feedback, `str`/`repr`, and verification records contain only safe
  IDs, hashes, field names, counts, and fixed reasons. Unknown values and map keys
  are redacted. Rejection details, replies, rationale, and tracebacks may contain
  source text and remain local. Sentinel tests exercise both exception and record
  representations, including malformed model-returned IDs/keys.
- Never use traceback/locals options that could reveal pilot text at the user's
  local gate. Its report names only test IDs, counts, and fixed reasons.

Do not weaken existing drafting import boundaries or the wording guard when adding
the optional NLI adapter. Every concrete adapter remains outside ordinary package
imports, and optional-dependency absence must not break default test collection.

## Deferred items and downstream handoffs

This stage does not silently close unrelated deferred items:

- **Extraction-record invariants:** remain due before Stage 10 reads stored runs.
  Stage 8 adds only its explicit target-reference/integrity gate.
- **Concurrent cache/store writers and `AdapterError` pickling:** remain with
  Stage 15's workers. Stage 8 runs sequentially.
- **Non-`AdapterError` extraction recovery:** remains conditional for Stages 10/11.
  A support run does not repair an extraction run that was never published.
- **Pilot live-test failure rendering:** lands before any such test reads pilot
  text. Stage 8's real smoke uses invented text and no pilot input.
- **Python wording scans and transcript block rules:** retain their existing
  conditional triggers. No new release-derived test string or transcript is added.
- **Gold drafting, duplicate kept-draft IDs, and test-gold refusal:** stay with
  Stages 11 and 14 under their existing triggers.

| Stage | Receives |
| --- | --- |
| 9 | `resolve_target`/`assess_target` for explicit proposed claim–theme pairings, per-quote contribution signals, raw scorer and judge views, and review outcomes. It proposes first, assesses, then decides assignments. No acceptance follows from `assessed`. |
| 10 | Typed support-run storage/reader and consuming gate, source-run/quote/codebook links, current masks, and visible refused/flagged/incomplete outcomes. It adds the first command and coverage/state mapping, and re-verifies before export. Zero accepted targets never implies no themes. |
| 11 | Primary/alternative raw scores, four individual judge views, all input/model/prompt/schema provenance, and pure metric functions. It acquires expert labels, calibrates judges and policies, sets V6 gates, and adds fresh-call bypass for extraction/scorer/judge caches. It is the first pilot extraction. |
| 13 | The release-only attribution-context policy, which needs an explicit adaptation for speaker turns and sections. No current release is labeled as a spoken management turn. |
| 15 | Sequential cache/store seams and versioned inputs; concurrency safety and backfill orchestration remain explicit later work. |

## Exit criteria and rollout

| Requirement | Stage 8 completion evidence |
| --- | --- |
| R8.1 | Exact evidence plus frozen selected theme reaches assessment; attribution/period/section/negation fixtures exercise visible objections without repairing quotes. |
| R8.2 / V4 | Actual pinned MiniCheck primary runs self-hosted without network/API inference; its weight terms and identity are recorded. The explicit DeBERTa alternative is wired behind the same interface. Calibration and quality comparison remain Stage 11. |
| R8.3 | Versioned raw signals and views persist separately from review outcomes; no score or panel consensus creates an accepted row. |
| R8.4, machinery only | Cross-family and order-swapped independent trials, bounded rationale, typed replies, and bias/disagreement diagnostics work offline. No claim of calibrated agreement. |
| R8.5 / R6.1 | Evidence re-verifies at every gate; invalid evidence cannot reach or be promoted by a judge; edits and codebook alterations are refused. |
| R8.6, machinery only | AUC-ROC and externally accepted-claim precision reproduce hand-calculated cases and explicit undefined/missing cases. No observed pilot quality claim. |
| GS13 / R14.1 | Drafting/import/wording and safe-rendering guards pass; default tests need no network, model weights or credentials; all live inference is explicitly gated and local. |

At completion, `docs/verification/semantic-support.md` records commands actually run,
offline checks, V4 identity/license/hosting evidence, the wording gate's observed
result, and limitations. The ADR records the scorer adoption, not a production
judge choice or an agreement floor. Record schema/interfaces in the data dictionary
and run relevant package/consumer checks and the root default suite; do not infer
success from collection or a skipped V4 smoke.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 8 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

On implementation completion, stamp this spec with the plan ID/date and retire it
to `specs/completed/` under the plan-completion protocol. Reconcile Stage 9's runtime
proposal–assessment ordering, Stage 10's store/gate, and Stage 11's calibration and
fresh-call obligations against the shipped interfaces. The design approval does not
tick Stage 8 or establish V4. Planning receives this approved, committed spec in a
fresh session.
