# Optional JEV shadow-decision integration

**Status:** Retained proposal for an optional layer. **Superseded on the
required-path question** by `specs/evidence-linked-theme-extraction.md` R14.3,
which declined to adopt JEV in the required path: it is closed, hosted,
waitlisted, and billable; it cannot extract spans or generate text, so it cannot
satisfy that spec's R5 or R7; and its published accuracy is measured as agreement
with other models rather than against ground truth.

That supersession is narrow. It reaches the adoption question only. The contracts,
provenance, status semantics, replay identity, and budget rules below were never
in conflict with the superseding spec and remain the design of record for this
layer if it is ever authorized.

Two gates now stand ahead of implementation that did not exist when this was
written: explicit paid-inference authorization, and the paired R8.2 baseline
comparison required by §15 criterion 17. That second gate obliges a run to make
the comparison *computable*; it does not oblige JEV to win it, and a result
favoring the open-weight baseline is a valid outcome that would close this
proposal rather than advance it. Until both gates are satisfied, this is a
proposal on file, not queued work.

**As of:** 2026-09-22. Status amended 2026-09-22 following
`specs/evidence-linked-theme-extraction.md` R14.3.

## 1. Decision

Add JEV as an optional, explicitly enabled decision backend inside the existing
`earnings-themes` package. The first integration evaluates two independent
semantic tasks on curated, already-verified evidence spans:

1. multi-label fixed-codebook theme mention; and
2. quote-to-claim semantic support.

The integration runs in **shadow mode only**. It records raw semantic decisions,
provenance, failures, and descriptive evaluation results without changing
accepted theme assignments or any production research output.

The default development and test path is offline replay. Live TypeSafe requests
require the optional dependency, explicit paid-inference authorization, an
explicit versioned model ID, positive document and run budgets, and credentials
supplied outside committed configuration.

## 2. Repository context

This specification is anchored to the committed repository plus the worktree
inspected on 2026-09-22:

- In the committed baseline, the root `pyproject.toml` is an intentional virtual
  uv workspace with no `[project]` table.
- The implemented package directories are `packages/earnings-core`,
  `packages/earnings-ingestion`, and `packages/earnings-themes`.
- The current worktree contains in-progress workspace, dependency, development-
  tooling, and pipeline-application edits. In particular, its root manifest adds
  a `[project]` named `earnings-themes` even though the member package already has
  that distribution name, and it registers `apps/earnings-pipeline` while the
  untracked application manifest is currently at `apps/pyproject.toml`. Those
  declarations conflict with the root's own virtual-workspace comments and do not
  yet form a resolvable workspace. A declaration in an uncommitted manifest is not
  implemented behavior until member paths, constraints, and the lockfile have
  been validated together, so this specification treats that work as unverified
  scaffolding.
- The domain packages remain pre-implementation stubs. There is no existing
  canonical document pipeline, extraction pipeline, decision backend, test
  suite, CI configuration, or application implementation to extend.
- The currently empty/untracked `config/`, `prompts/`, `codebooks/`, `tests/`, and
  `data/runs/` roots are the intended homes for configuration, versioned research
  artifacts, fixtures, and ignored run outputs. Because Git does not preserve
  empty directories, implementation must create only the needed tracked files and
  ignored output directories.

JEV fits the intended package boundaries. This specification does not require a
new decision package, a root project, or a pipeline application. It therefore
does not require JEV-specific changes to the workspace topology, `AGENTS.md`, or
`CLAUDE.md`.

Planning and execution must begin from an internally consistent workspace state:
registered member paths must exist, member Python constraints must resolve, and
`uv.lock` must agree with the manifests. The owner must first finish, commit, or
isolate the unrelated ingestion/application edits currently in progress. The JEV
plan may add only its required core/themes dependencies, optional extra, shared
test configuration, and resulting lockfile changes; it must not silently finish
or redesign unrelated worktree changes.

`AGENTS-jev-addendum.md` remains a non-binding proposal. For this integration,
this specification supersedes it wherever the two disagree, including retry
ownership. `AGENTS.md` remains the repository-wide authority.

## 3. Goals

The first integration must:

- define the minimum canonical-document and verified-evidence contracts needed
  to test decisions without building ingestion or extraction first;
- define provider-neutral request, observation, status, and run-summary contracts;
- keep all TypeSafe SDK imports behind one optional adapter boundary;
- support deterministic replay and injected test fakes with no credentials or
  network;
- support explicitly authorized live JEV shadow requests;
- evaluate theme mention and claim support as separate tasks;
- preserve the raw probability or distribution returned for every answer;
- record enough provenance to reproduce or audit each observation;
- distinguish negative semantic results from unavailable, deferred, failed, and
  unprocessed work;
- produce normalized shadow observations/attempts/diagnostics, a versioned data
  dictionary, a run manifest, and descriptive reports;
- remain installable, importable, and testable without JEV or its SDK; and
- demonstrate integration correctness without claiming model quality or
  production readiness.

## 4. Non-goals

This specification does not include:

- filing acquisition, canonicalization from source HTML, candidate extraction,
  or generative quote creation;
- production theme discovery or approval of a research taxonomy;
- decision thresholds, calibrated probabilities, automatic acceptance or
  rejection, or production label promotion;
- the planned 20–40-document gold set or a production-quality benchmark;
- LangGraph, LangChain, DSPy, CrewAI, hosted tracing, or a pipeline CLI;
- a general-purpose decision package or alternate provider integration;
- JEV use for employment extraction, entity resolution, ownership,
  classification, or other ingestion tasks;
- a shared remote cache, distributed execution, or service deployment; or
- a claim that a small synthetic fixture corpus measures real earnings-domain
  performance.

Those are later design decisions. None may be inferred from successful completion
of this shadow integration.

## 5. Architecture and ownership

### 5.1 `earnings-core`

`earnings-core` owns evidence facts that remain meaningful without JEV or theme
analysis:

- canonical document identity and canonical-text SHA-256;
- canonicalization/normalization version;
- source-document and provenance identifiers;
- zero-based, half-open Python string character offsets;
- verified target and context spans; and
- pure validation and slicing helpers.

It must not import the TypeSafe SDK, define JEV questions, apply theme semantics,
or own provider retry and configuration logic.

For every target span, deterministic validation must establish:

```text
0 <= target_start < target_end <= len(canonical_text)
0 <= context_start <= target_start < target_end <= context_end <= len(canonical_text)
quote_text == canonical_text[target_start:target_end]
context_text == canonical_text[context_start:context_end]
canonical_sha256 == lowercase_hex(sha256(canonical_text encoded as UTF-8))
```

For a transcript target, validation also requires:

```text
0 <= turn_start <= target_start < target_end <= turn_end <= len(canonical_text)
speaker_turn_id identifies those exact turn bounds
```

Invalid evidence is an input failure and must never be sent to a model.

### 5.2 `earnings-ingestion`

This JEV slice requires no changes to `earnings-ingestion`. Curated fixtures stand
in for its future canonical-document output. The integration must not introduce
a downloader, parser, issuer resolver, or alternate canonicalization path into
`earnings-themes`. Unrelated dependency edits remain outside this specification.

### 5.3 `earnings-themes`

`earnings-themes` owns:

- the provider-neutral decision-backend protocol;
- theme-mention and claim-support task contracts;
- task construction from versioned prompts and codebooks;
- the replay and TypeSafe adapters, plus injectable test fakes;
- live-run preflight and bounded operational policy;
- normalized decision observations;
- the shadow evaluator and descriptive report; and
- serialization to the declared analytical artifacts.

Only the TypeSafe adapter may import `typesafe_sdk`. Importing the base
`earnings_themes` package must not import or require the SDK transitively.

### 5.4 Repository artifacts

The implementation must use the intended top-level roots and create only the
required files and subdirectories rather than introduce parallel structures:

| Artifact | Intended location |
| --- | --- |
| Versioned semantic task wording | `prompts/jev/` |
| Explicitly test-only codebook | `codebooks/` with test-only status metadata |
| Versioned machine/human data dictionary | `docs/data-dictionary/jev-shadow-v1.json` and `.md` |
| Canonical documents, spans, labels, and replay responses | `tests/fixtures/jev/` |
| Package unit tests | the owning package's `tests/` directory |
| Cross-package/offline vertical test | `tests/integration/` |
| Optional live compatibility test | a registered `live` pytest test |
| Normalized live-attempt accounting | `request_attempts.parquet` inside the selected run directory |
| Normalized request diagnostics | `request_diagnostics.parquet` inside the selected run directory |
| Raw responses and generated run artifacts | caller-selected path under `data/runs/` |

Exact module filenames are an implementation-plan concern, but their ownership
and dependency direction are requirements of this specification.

## 6. Decision contracts

### 6.1 Verified evidence input

Each decision input must make these fields available directly or through a
stable reference:

- document and source identifiers;
- canonical text and SHA-256;
- normalization and segmentation versions;
- target and context start/end offsets;
- exact target quote and context sliced from canonical text;
- document type and section where applicable;
- speaker role plus speaker-turn ID and turn start/end offsets for transcripts;
- source/reference/publication metadata or an explicit missing reason; and
- fixture or corpus version.

The context span may equal the target span. A target must not cross a transcript
speaker boundary: transcript inputs require turn bounds, and target offsets must
fall wholly within exactly one identified turn. Non-transcript speaker/turn fields
are `not_applicable`; an unresolved transcript role is `unknown` rather than
management. Context may cross a turn boundary, but the target role always refers
only to the containing turn.

### 6.2 Theme-mention task

Theme coding asks one binary question per theme against the same verified target.
It must not use a single mutually exclusive Choice across all themes, because one
span may mention more than one theme.

Each question includes the theme ID, complete definition, inclusion rules,
exclusion rules, boundary cases, question version, and content hash. Question IDs
are bookkeeping only; the full semantics must be present in the question.

The target quote is the evidence being classified. Context may disambiguate the
target but must not cause a positive result merely because other context mentions
the topic.

For this task, denial still counts as topic mention. For example, a statement that
there are no plans for layoffs mentions workforce reduction. It does not establish
that layoffs are planned or occurring. Direction, stance, certainty, and event
truth require separate tasks and are outside this specification.

The normalized observation stores the raw yes-probability. This specification
defines no probability threshold and creates no accepted theme assignment.
The TypeSafe adapter maps each of these questions to a Noul; other backends must
preserve the same binary-question semantics.

### 6.3 Claim-support task

Claim support evaluates one atomic claim against one verified target and its
permitted context. It uses exactly these mutually exclusive outcomes:

- `supports`: the target, interpreted with context, supports the complete claim;
- `contradicts`: the target explicitly conflicts with the claim; and
- `insufficient_evidence`: the target does not establish the complete claim,
  including when necessary context is absent.

The normalized observation preserves the selected outcome, the full probability
distribution, and the SDK's confidence field verbatim when returned, under the
name `provider_confidence_raw`. The project does not recompute or overwrite that
field. Any future project-derived certainty statistic requires a separate field,
algorithm/version, and design decision. Provider confidence is derived from the
distribution; it is not an independently calibrated probability that the research
interpretation is correct.

The TypeSafe adapter maps this task to a Choice whose criteria are exactly the
three outcomes above; other backends must preserve the same closed outcome set.

Exactness, semantic support, and external factual truth remain separate. A support
decision cannot repair an invalid quote or prove that the company's statement is
true outside the source.

### 6.4 Task isolation

Theme mention and claim support must be sent as separate semantic requests, even
when they reference the same target span. The theme request must not receive the
candidate claim, because claim wording could influence whether the target appears
to mention a theme. Each task family has its own request hash, observation rows,
coverage counts, and descriptive results.

Multiple independent theme questions may share one theme request for a target.
Every returned answer still becomes its own normalized observation. The exact
question set and batching definition are part of the request serialization and
provenance.

### 6.5 Provider-visible state and local provenance

Version 1 sends a data-minimized `semantic-state-v1` object containing exactly:

- schema version and task kind;
- the exact target text and permitted context text;
- the validated document-type value;
- the exact section label, or null when it has no domain value; and
- speaker role as `management`, `analyst`, `unknown`, or `not_applicable`.

The provider also receives the selected model ID, the complete applicable prompt
instructions, stable opaque question IDs, and complete question objects. A theme
request never receives claim text; a claim-support question necessarily contains
its claim text and three outcome criteria. No other input field is provider-visible
in version 1.

Document, source, issuer, fixture, corpus, and speaker-turn IDs; canonical hashes;
offsets and turn bounds; normalization/segmentation versions; source URLs and
publication/reference metadata; reference labels; and authorization records remain
local provenance and must not be placed in SDK state, question wording, headers,
or provider metadata. The external-inference authorization applies to the full
provider-visible payload. `decision-request-v1` binds both the provider-visible
semantic state and the local evidence identity for audit/replay, but only the
semantic state and questions cross the adapter boundary.

## 7. Provider-neutral backend boundary

The backend protocol accepts an immutable, fully validated semantic request and
returns either:

- raw semantic answers plus provider metadata; or
- a typed operational outcome describing why answers are unavailable.

The protocol must not publish labels, modify evidence, mutate the codebook, apply
acceptance thresholds, create ingestion assertions, or make authorization
decisions.

Provider-neutral runner code must not depend on SDK response classes or
exceptions. The TypeSafe adapter translates SDK requests, responses, and failures
at the boundary. The replay adapter implements the same protocol from committed
fixtures.

Before an answer becomes `observed`, adapter-independent validation must establish
that binary probabilities are finite and within `[0, 1]`; Choice keys exactly
match the declared outcomes; every Choice probability is finite and within
`[0, 1]`; the selected outcome is present and has maximal probability, with ties
allowed; and the distribution sums to 1 within an absolute tolerance of `1e-6`.
An expected answer with an unknown type, duplicate raw question ID, or invalid
shape is `failed_response`.

Partial batched responses are handled per expected question. If the top-level
response and returned model are valid, each valid expected answer survives as
`observed`; each missing or invalid expected answer becomes `failed_response`.
Unexpected answer IDs are retained in request-level diagnostics but create no
work-item row and do not invalidate otherwise valid expected answers. A malformed
top-level response or returned-model mismatch makes every question in that request
`failed_response`. Response-shape failures are terminal and are not retried.

Construction failures have deterministic atomicity. Invalid shared evidence or
shared task/prompt state makes every expected work item that depends on that
shared object `failed_input`, and no request is formed for them. After shared
validation succeeds, each question/codebook entry is validated independently. An
invalid question becomes `failed_input` and is excluded; the remaining valid theme
questions, if any, form one sorted batch whose serialization and hash contain only
that remainder. If none remain, no theme request is scheduled. A claim-support
request has one question, so a question-local failure eliminates that request.
This validation and re-batching occurs before request ordering or budget
reservation and must not be re-run differently after a provider failure.

## 8. Execution modes and live-call authorization

### 8.1 Offline default

Replay is the default execution mode for development, ordinary tests, and the
offline vertical slice. Importing a module, constructing a backend, encountering
a replay miss, or generating a report must never trigger a live fallback.

A safe committed configuration may select replay and shadow mode, but must not
contain a model default, credential, or positive paid-inference budget.

### 8.2 Optional TypeSafe adapter

The TypeSafe SDK must be an optional dependency extra of
`packages/earnings-themes`; it is not a root, core, ingestion, or unconditional
runtime dependency. The current worktree sketches such an extra but has not locked
or verified it. The implementation plan must resolve a version compatible with
the workspace's finalized Python constraints, update `uv.lock` intentionally,
and review the dependency diff.

The adapter may make a request only when all of these gates pass:

1. the optional dependency is installed;
2. the TypeSafe backend is explicitly selected;
3. shadow is the selected mode;
4. paid inference is explicitly enabled;
5. a concrete, versioned model ID is supplied;
6. positive per-document and per-run request, estimated-input-token, and
   estimated-cost ceilings are supplied with a dated pricing basis;
7. fixture/source metadata explicitly authorizes external inference for the
   content being sent; and
8. a present, nonblank API key is available outside committed configuration.

Missing any gate yields a structured preflight deferral before network dispatch.
The adapter must pass the configured model on every call. It must not inherit the
SDK's moving alias default, accept `jev-latest`/`jev-preview` as a reproducible
version, silently select a provider, or substitute another model after failure.
Any additional key-format validation performed by the pinned SDK is recorded as a
pre-dispatch configuration deferral; credential authenticity is known only from a
provider authentication response.

The response's versioned model ID must be recorded and checked against the
requested version. A mismatch is a failed response requiring review, not a valid
shadow observation.

### 8.3 Configuration contract

The provider-neutral version 1 run configuration contains the following fields;
unknown fields are invalid:

- `mode`, whose only value in this specification is `shadow`;
- `backend`, either `replay` or `typesafe`;
- `allow_paid_inference`, defaulting to false;
- `model_id`, required for TypeSafe and null for replay;
- `fixture_set_id`, required for replay and null for TypeSafe;
- `document_request_ceiling`, `document_input_token_ceiling`, and
  `document_cost_ceiling_microunits`;
- `run_request_ceiling`, `run_input_token_ceiling`, and
  `run_cost_ceiling_microunits`;
- `pricing_basis_id`, `pricing_basis_hash`, `estimator_set_id`, and
  `estimator_set_hash`, each required for live execution and null for replay;
- `attempt_timeout_seconds` and `max_attempts`, inclusive of the initial dispatch;
- `retry_initial_backoff_seconds`, `retry_max_backoff_seconds`,
  `retry_jitter_fraction`, and `max_provider_retry_delay_seconds`;
- `retain_raw_response`, defaulting to false; and
- `output_directory`, required when persistence is requested and otherwise null.

The six ceiling values are null or zero in a safe committed replay configuration
and positive for live execution. The referenced estimator set covers the input-
token estimator and every output-dependent billing-component upper-bound
estimator, including each estimator's version and compatible provider, model, and
tokenizer identity. Timeout is positive, `max_attempts >= 1`, backoff/delay values
are nonnegative with initial no greater than maximum, and jitter is in `[0, 1]`.

Version 1 uses one document-ceiling triplet applied independently to every
document and one run-ceiling triplet; it has no per-document override map. The
three members of each triplet are provider-request attempts, estimated input
tokens, and cost microunits.

The dated pricing basis is a versioned `pricing-basis-v1` object containing its
ID/version, provider ID, source locator and content hash, retrieval/verification
time, inclusive UTC `valid_from` and `valid_through` times, ISO 4217 currency,
applicable versioned model IDs, and every billing component. Each component names
its billing unit (for example request or input token), a nonnegative integer
`rate_microunits`, and a positive integer `units_per_rate`. Component cost is
`ceil(usage_units * rate_microunits / units_per_rate)`. All project-estimated,
ceiling, and reconciled costs use signed 64-bit integer microunits (one millionth
of a unit) of that one configured currency; no binary floating-point or implicit
foreign-exchange conversion is allowed. A provider-reported amount is stored
separately as microunits of its accompanying ISO currency. A foreign-currency
reported amount is never converted, compared, or included in configured-currency
totals. Nonnegative provider decimals are rounded upward to microunits; arithmetic
is checked for overflow, and each calculated billing component is rounded upward
before summation.
Live preflight fails unless the call time is inside the recorded validity interval,
every required rate and estimator is present, the basis and estimator set both
cover the selected provider/model, and all comparable values use the one declared
currency.

`run-config-v1` has a fixed key set. Mode-inapplicable or live-gate values that
are not supplied are represented by explicit null or the declared safe default,
so a structurally valid replay or deferred-live configuration still has one
canonical hash. An unknown key, wrong type, or missing schema key is a
configuration-validation failure and produces no effective-configuration hash.
Structural validation does not itself authorize a live call; the gates in Section
8.2 are evaluated afterward.

Credentials are not configuration fields. The TypeSafe adapter obtains its key
from the provider's standard environment mechanism at execution time. A committed
replay configuration identifies a fixture set. Each replay fixture manifest
contains the concrete `recorded_model_id` from the captured request; the replay
runner uses that value when constructing its request identity. A recorded fixture
model never populates live `model_id` and therefore cannot become a live default.

Each fixture/source record also carries two independent authorization decisions:
`external_inference_authorization` and `raw_response_retention_authorization`.
Each is `allowed`, `prohibited`, or `unknown` and includes its basis, reviewer or
source, and decision date. Live dispatch requires the first to be `allowed`.
`retain_raw_response=true` additionally requires the second to be `allowed`;
otherwise affected work is `deferred_configuration` before dispatch. A runtime
flag cannot grant rights that the metadata does not establish. Committed
synthetic fixtures may use an `allowed` basis of `synthetic_test_fixture`.

## 9. Replay identity and reproducibility

### 9.1 Artifact fingerprints

Semantic artifact hashes use versioned typed objects rather than source-file bytes.
Each object is serialized as RFC 8785 JSON Canonicalization Scheme bytes in UTF-8,
hashed with SHA-256, and stored as lowercase hexadecimal. Version 1 permits only
JSON strings, booleans, nulls, integers, finite numbers, arrays, and objects.
Unknown fields are prohibited. Text is hashed exactly as loaded and validated,
without Unicode normalization, whitespace normalization, or case folding.

The seven artifact schemas are:

- `prompt-artifact-v1`: schema version, prompt ID and version, task kind, and the
  complete instruction text;
- `question-artifact-v1`: schema version, question ID and version, task kind,
  complete rendered wording, and all task-specific semantics. A theme question
  includes theme ID, definition, inclusion rules, exclusion rules, and boundary
  cases. A support question includes claim ID and text plus the complete ordered
  outcome criteria;
- `codebook-artifact-v1`: schema version, codebook ID, version, status, and every
  complete theme record, with themes sorted by theme ID and each rule list kept in
  its declared order;
- `authorization-record-v1`: schema version, fixture/source record ID, and both
  authorization decisions, each with its decision type, `allowed`, `prohibited`,
  or `unknown` value, basis, reviewer or source, and ISO 8601 decision date; and
- `pricing-basis-v1`: the complete provider/model applicability, validity,
  currency, source, and billing-component object defined in Section 8.3;
- `estimator-set-v1`: schema version, estimator-set ID/version, provider/model and
  tokenizer compatibility, the input-token estimator ID/version, and the
  ID/version of the upper-bound estimator for every output-dependent billing
  component; and
- `run-config-v1`: schema version and the complete effective non-secret
  configuration after defaults and validation, including backend, mode, model or
  fixture-set selection, all document/run ceilings, pricing basis, estimator set,
  retry policy, retention setting, output location, API-key presence Boolean, and
  API-key environment-variable name. Authorization metadata is hashed and recorded
  separately because it describes the source content, not the run configuration.
  The configuration object never includes the key or any derivative of it.

The hashes cover the complete canonical objects, including their schema-version
fields. A TOML, YAML, or Python representation is first parsed into the applicable
typed object, so source formatting cannot change a semantic hash. A semantic
change requires a changed object and hash; a schema change requires a new schema
version. Golden canonical bytes and hashes for all seven schemas are committed as
fixtures.

These semantic hashes are distinct from two other checksums. `canonical_sha256`
is the SHA-256 of the canonical text's exact UTF-8 bytes as defined in Section 5,
and persisted-file checksums are SHA-256 over exact file bytes. The run manifest
labels each checksum kind so they cannot be interchanged.

### 9.2 Decision-request identity

Replay identity uses a versioned `decision-request-v1` object serialized and
hashed by the same RFC 8785/SHA-256 procedure. It does not normalize or case-fold
canonical text, quotes, context, claims, or question wording; those values are
serialized exactly as validated.

The version 1 object includes every input capable of changing an answer plus the
local evidence identity that prevents observations from floating between spans:

- request schema version and task kind;
- the complete `semantic-state-v1` provider payload defined in Section 6.5;
- a local evidence-binding object containing document/target IDs, canonical hash,
  target/context offsets, normalization and segmentation versions, speaker-turn
  ID/bounds when applicable, and source/reference/publication metadata;
- claim text for claim-support requests, through the complete question object;
- complete question contents and question-set ordering/canonicalization rule;
- prompt and codebook IDs, versions, and hashes;
- requested model ID;
- adapter/request-shaping version; and
- an explicit model-parameters object, which is empty when no parameters are
  supported.

Optional fields with no semantic value are omitted; explicit null is retained only
where null has domain meaning. Object keys follow RFC 8785 ordering. Theme
questions are sorted by stable question ID before serialization; arrays whose
order is semantically meaningful preserve their declared order. Unknown extra
fields are prohibited in version 1. Adding one requires a new request-schema or
request-shaping version.

Structurally identical typed requests must serialize identically. Changed semantic
state, local evidence binding, claim, questions, model, or request shaping must
miss rather than reuse an old response. A replay miss returns an explicit status
and never calls the network. Golden serialization bytes and hashes are committed
as fixtures.

Raw model observations and derived reporting policy are versioned separately so
future thresholds can be evaluated without relabeling a raw response as though it
came from a new model call.

## 10. Observations and output artifacts

### 10.1 Decision observation

Every invocation requires a caller-supplied `run_id` matching
`[a-z0-9][a-z0-9._-]{0,127}`. It is an operational identifier, not a semantic
cache key. The manifest records the `caller-supplied-v1` construction method, and
the immutable destination check enforces uniqueness within the selected output
parent. The runner never derives a path from an unvalidated ID and never silently
replaces a colliding ID.

Before backend execution, the runner expands the fixture corpus into an expected-
work ledger with one row per semantic question. The final decision-observation
grain is exactly one row per `(run_id, work_item_id)`. `work_item_id` is the
lowercase SHA-256 of an RFC 8785 canonical `work-item-v1` object containing its
schema version, task kind, target-span ID, question ID, and exactly one applicable
theme ID or claim ID. Every expected row receives exactly one final status,
including work never reached after an earlier run failure.

The persisted Parquet schema uses these physical types:

- IDs, enums, hashes, model names, versions, reason codes, and artifact references:
  UTF-8 string;
- offsets, token counts, attempt counts, request counts, and all cost microunit
  fields: nullable `Int64`;
- probabilities, confidence, and latency: nullable `Float64`;
- conditional flags: nullable Boolean; the row-wide raw-retention-enabled flag is
  required Boolean;
- timestamps: UTC microsecond timestamp; and
- secondary reason codes: non-null list of UTF-8 strings in declared precedence
  order, empty when there is only one applicable reason; and
- Choice distributions: nullable list of structs with `label: string` and
  `probability: Float64`, sorted by label.

The exact version 1 observation columns are:

- identity/status: `run_id`, `work_item_id`, `task_kind`,
  `fixture_corpus_version`, `document_id`, `target_span_id`, `theme_id`,
  `claim_id`, `question_id`, `requested_backend`, `mode`, `status`,
  `status_reason_code`, `secondary_reason_codes`, `status_detail`, and
  `finalized_at`;
- evidence/task provenance: `document_type`, `section`, `speaker_role`,
  `canonical_sha256`, `normalization_version`, `segmentation_version`,
  `target_start`, `target_end`, `context_start`, `context_end`, `prompt_id`,
  `prompt_version`, `prompt_hash`, `question_version`, `question_hash`,
  `codebook_id`, `codebook_version`, `codebook_hash`,
  `authorization_record_hash`, `external_inference_authorization`, and
  `raw_response_retention_authorization`;
- configuration/request provenance: `configuration_hash`,
  `pricing_basis_hash`, `estimator_set_hash`, `request_hash`,
  `request_sequence`, `adapter_name`, `adapter_version`,
  `request_shaping_version`, `sdk_version`, `requested_model_id`,
  `returned_model_id`, and `provider_request_id`;
- semantic result: `binary_yes_probability`, `choice_selected`,
  `choice_distribution`, and `provider_confidence_raw`; and
- operations: `attempt_count`, `reserved_request_count`,
  `reserved_input_tokens`, `reconciled_input_tokens`,
  `reserved_cost_microunits`, `reconciled_cost_microunits`, `currency`,
  `latency_ms`, `reservation_underestimate`,
  `reservation_delta_input_tokens`, `reservation_delta_cost_microunits`,
  `ceiling_overrun`, `ceiling_overrun_scope`,
  `budget_reconciliation_unknown`, `raw_retention_enabled`,
  `raw_retention_reason`, and `raw_response_ref`.

No additional observation column is permitted without a new data-dictionary
schema version. Exact physical types and stage/status nullability follow this
section and Section 10.6.

These fields are required for every row: run and work-item IDs; task kind;
fixture/corpus version; document and target-span IDs from the ledger; theme or
claim/question ID; normalized requested backend (`replay`, `typesafe`, or
`unconfigured`); shadow mode; final status; a stable status-reason code; and UTC
row-finalization time. Human-readable status detail is optional.

Other fields are required only after the stage that can produce them:

| Field group | Required when | Otherwise |
| --- | --- | --- |
| Canonical, prompt, question, and codebook hashes plus offsets | The corresponding input validated | Null with the final failure/deferral reason |
| Pricing-basis and estimator-set hashes | Live pricing/estimator configuration validated | Null as `not_applicable` for replay or with the configuration reason |
| Request hash, zero-based request sequence, and adapter/request-shaping version | Request serialization completed and the request was scheduled | Null |
| Effective non-secret configuration hash | Configuration was successfully defaulted and validated into `run-config-v1` | Null with a configuration reason when parsing or validation fails |
| External-inference and raw-retention authorization decisions and metadata hashes | The fixture/source metadata parsed | Null with an input failure if authorization metadata could not be parsed |
| Adapter and SDK versions | That adapter/SDK loaded | Null |
| Requested model | A live model was supplied or a replay fixture supplied `recorded_model_id` | Null |
| Returned model, provider request ID, raw-response reference | Provider returned the value or a retained artifact exists | Null |
| Semantic answer, distribution, and `provider_confidence_raw` | Status is `observed` and the answer type supplies the field | Null |
| Attempt count and request-level reserved/reported usage, cost, currency, and latency aggregates | Dispatch occurred or the value can be measured | Null |
| `budget_reconciliation_unknown` | Any live attempt accounting was finalized, including an ambiguous disposition | Null only before live dispatch |
| Input-token and cost reservation deltas | The corresponding component is determinable | Null only for the indeterminate component or before dispatch |
| `reservation_underestimate`, `ceiling_overrun`, and ceiling-overrun scope | Live attempt accounting was finalized | Apply the componentwise truth rule below; scope is non-null exactly when `ceiling_overrun=true` |

Budget flags use three-valued componentwise logic. An aggregate flag is true when
any determinable component proves it; false only when every applicable component
is determinable and none proves it; otherwise it is null. Thus an ambiguous
foreign-currency attempt may still prove an input-token underestimate or ceiling
breach while its cost delta remains null and
`budget_reconciliation_unknown=true`. Null is never interpreted as false.

Every row records whether raw retention was enabled and a retention reason when
the raw-response reference is null. Null or unavailable numeric values remain
null; they never become zero. If a batched request fails, each eligible question
still receives its own row under the partial-response policy in Section 7.
Request-level usage and budget fields are repeated on each question row in a
batch for traceability, but totals are computed once per `(run_id,
request_sequence)`, never by summing observation rows.

### 10.2 Request attempts

Every persisted run emits `request_attempts.parquet`, including an empty file for
a replay-only or preflight-deferred run. Its grain is one row per
`(run_id, request_sequence, attempt_number)`, where attempt numbers start at one.
Its exact columns are `run_id`, `request_sequence`, `attempt_number`,
`document_id`, `request_hash`, `backend`, `requested_model_id`,
`returned_model_id`, `provider_request_id`, `started_at`, `ended_at`, `latency_ms`,
`attempt_outcome_code`, `billing_disposition`, `reserved_request_count`,
`reserved_input_tokens`, `reserved_cost_microunits`, `reported_billable_units`,
`provider_reported_cost_microunits`, `provider_reported_currency`,
`released_input_tokens`, `released_cost_microunits`, `reconciled_input_tokens`,
`reconciled_cost_microunits`, `currency`, `pricing_basis_hash`,
`estimator_set_hash`, `reservation_underestimate`,
`reservation_delta_input_tokens`, `reservation_delta_cost_microunits`,
`ceiling_overrun`, `ceiling_overrun_scope`, and
`budget_reconciliation_unknown`. `reported_billable_units` is a list of structs
with `component: string` and nonnegative `units: Int64`, sorted by component.
Attempt outcome is exactly `response`, `authentication_error`,
`permission_error`, `request_validation_error`, `rate_limited`, `overloaded`,
`timeout`, `transport_error`, or `provider_error`.

Each attempt has exactly one `billing_disposition`:

- `reported_usage`: billable usage is sufficient for deterministic reconciliation
  and the response contains no incompatible-currency cost assertion;
- `confirmed_not_processed`: explicit response metadata or transport-level proof
  that no request bytes reached the provider establishes processing/billing did
  not begin; or
- `ambiguous`: the other disposition cannot be selected unambiguously because
  billing evidence is missing, incompatible, or contradictory.

Disposition precedence is deterministic. Explicit confirmed-not-processed evidence
wins when reported billable units/cost are absent or all zero. Without that
evidence, sufficient billable usage selects `reported_usage`; otherwise the result
is `ambiguous`. Confirmed-not-processed evidence paired with any nonzero reported
usage or cost is contradictory, selects `ambiguous`, and emits a
`billing_evidence_conflict` diagnostic. Thus no attempt can satisfy two
dispositions.

The row also carries `budget_reconciliation_unknown` as required Boolean.
Token/cost deltas and the aggregate underestimate/overrun fields follow the
componentwise three-valued rule in Section 10.1 even when disposition is
`ambiguous`; ambiguity does not erase a comparison that is independently known.
Observation rows repeat only request-level aggregates for query convenience;
attempt accounting and manifest/summary totals use this table as the authority.
The in-memory runner result exposes the same normalized attempt rows even when
persistence is disabled.

### 10.3 Request diagnostics

Every persisted run emits `request_diagnostics.parquet`, including an empty file
with the declared schema when there are no diagnostics. Its grain is one row per
`(run_id, request_sequence, attempt_number, diagnostic_index)`. Request sequence
and the within-attempt diagnostic index are zero-based; attempt number is zero for
pre-dispatch diagnostics and one through `max_attempts` for dispatch attempts.
Within an attempt, diagnostics are sorted by diagnostic code, expected question
ID, and unexpected answer ID using the Section 12 string-ordering rule before the
index is assigned; null sorts last.

Each row contains run ID, request sequence, attempt number, diagnostic index,
diagnostic code and severity, backend, task kind, nullable request hash, requested
and returned model IDs, nullable provider request ID, nullable expected question
ID, nullable unexpected answer ID, UTC event time, and optional sanitized detail.
Diagnostic detail must not contain evidence text, question bodies, raw responses,
credentials, or authorization headers. Severity is exactly `info`, `warning`, or
`error`. The version 1 diagnostic-code enum is `unexpected_answer_id`,
`returned_model_mismatch`, `malformed_top_level_response`, `provider_error`,
`provider_cost_disagreement`, `provider_currency_mismatch`,
`billing_evidence_conflict`,
`reservation_underestimate`, `ceiling_overrun`,
`budget_reconciliation_unknown`, and `raw_retention_suppressed`. Each unexpected
answer ID receives its own diagnostic row even when raw-response retention is
disabled. Diagnostics never create expected-work rows or semantic answers. A new
code requires a new diagnostics/data-dictionary schema version.

### 10.4 Run manifest and coverage

The run manifest identifies the fixture corpus, software and lockfile versions,
artifact hashes, authorization decisions and their bases/dates, per-document and
per-run budgets and accounting, pricing-basis and estimator-set IDs/versions/
hashes and model/tokenizer compatibility, start/end times, and output locations.
When configuration validation succeeds, it contains the complete effective
**non-secret** `run-config-v1` object and hash. When validation fails, those two
fields are null; instead, the manifest contains structured validation reason codes
and an attempted-configuration summary containing only successfully parsed,
allowlisted non-secret fields. Unknown fields are named only by a generic
`unknown_field` reason—their names and values are not copied. It records
credential presence as a Boolean and the environment-variable name used, never
the credential value or a reversible derivative. It also records reservation
underestimates, ceiling-overrun scopes, and any unknown reconciliation.
`run_status` is `partial` whenever any row is `deferred_budget`, any budget-safety
stop is selected, or a graceful provider/response run-stop from Section 12.1 is
selected, even if the affected request is last and there are zero deferred or
`unprocessed` rows. It is `completed` only when every expected row is finalized
and none of those conditions occurred; configuration deferrals alone do not make a
run partial. A hard interruption has no final manifest and remains an unpromoted
staging directory.

Coverage uses the expected-work ledger as its denominator. It reports expected,
observed, each deferred and failed status, replay misses, and `unprocessed` rows
separately for theme mention and claim support. Provider/configuration
unavailability is represented by its specific deferral status, not by an
unexplained missing row. A table of successful answers alone is not a coverage
report.

### 10.5 Persistence and report

When the caller requests persistence, the shadow runner writes to an explicit,
caller-selected parent under `data/runs/`. The final child directory is the
immutable `run_id`; if it already exists, the run fails with an output collision
and never overwrites it. The writer builds every artifact in a unique sibling
`run_id.partial-*` directory, validates file checksums, writes the final manifest
last, and promotes the complete directory with a same-filesystem atomic rename.
An interrupted staging directory is not a completed run and must remain visibly
partial until an explicit cleanup policy handles it.

The promoted run directory contains:

- normalized decision observations in Parquet;
- normalized request attempts in Parquet;
- request diagnostics in Parquet;
- the exact machine-readable data dictionary used for the run;
- a machine-readable run manifest and summary;
- an optional raw-response artifact only when retention is configured and the
  applicable source authorization explicitly permits it; and
- a concise human-readable shadow report.

The machine summary is the report oracle. It contains stable schema/version,
status and diagnostic counts, denominators, requested and returned models, usage,
attempts, latency, currency/cost microunits, reservation-underestimate,
ceiling-overrun, and unknown-reconciliation fields.
Request-level quantities are aggregated once per request sequence. For observed
reference-labeled theme tasks it reports
Brier score `mean((p_yes - y)^2)` and mean yes-probability separately for `y=0`
and `y=1`; for observed reference-labeled support tasks it reports top-choice
match count and `matches / observed_labeled_support_tasks`. A metric with a zero
denominator is null with denominator zero, never zero-valued performance. Each
metric states its observed labeled denominator. Deferred, failed, replay-miss,
and unprocessed work remains in coverage and is never counted as a disagreement.

The human-readable report renders that summary. It must identify the corpus as
test-only and state that descriptive results on small synthetic fixtures are not
a production-quality estimate or acceptance threshold. Golden fixtures assert
exact stable summary fields and counts, with `1e-12` absolute tolerance for
derived floating metrics; prose formatting is not a snapshot contract.

The runner returns the same normalized observations, request attempts, request
diagnostics, and summary to library callers, whether or not persistence is
enabled. Its public result type exposes only shadow observations, operational
attempts/diagnostics, coverage, and descriptive summaries. This slice defines no
accepted-assignment type, writer, callback, or production-output interface. It
does not require a CLI or write files on import.

### 10.6 Data dictionary and schema evolution

`docs/data-dictionary/jev-shadow-v1.json` is the machine authority for every
persisted or returned artifact; the adjacent Markdown is rendered from it. The
JSON dictionary carries its own schema version and, for observations, attempts,
diagnostics, manifest, and summary, declares exact field names/order, physical and
logical types, nullability predicate, grain/key, enum vocabulary, units/currency,
foreign-key target, description, and hash/canonicalization rule. The implementation
validates emitted artifacts against this dictionary before promotion. The exact
JSON used by a run is copied into the run directory and its file checksum is
recorded in the manifest.

The version 1 identifier nullability contract is fixed:

- observation `run_id`, `work_item_id`, `document_id`, `target_span_id`, and
  `question_id` are never null;
- observation `theme_id` is non-null only for theme mention and `claim_id` is
  non-null only for claim support; exactly one is non-null;
- observation `request_hash` and `request_sequence` are non-null only after a
  request is serialized/scheduled; requested/returned model IDs and provider
  request ID follow the stage rules in Section 10.1;
- attempt `run_id`, `request_sequence`, and `attempt_number` are never null;
  provider request ID and returned model remain nullable because a transport
  failure may yield neither; and
- diagnostic `run_id`, `request_sequence`, `attempt_number`,
  `diagnostic_index`, and `diagnostic_code` are never null; expected-question and
  unexpected-answer IDs remain nullable exactly as described in Section 10.3.

Adding or renaming a field, changing a nullability predicate or enum, changing a
grain, or changing units requires a new data-dictionary/schema version and an
explicit compatibility/backfill decision. Undeclared ad hoc columns are forbidden.

## 11. Status and error semantics

At minimum, the implementation must distinguish:

| Outcome | Meaning |
| --- | --- |
| `observed` | A structurally valid raw semantic answer was recorded in shadow mode. |
| `deferred_configuration` | Optional dependency, authorization, model, key, or other required configuration is absent, invalid, unknown, or explicitly not authorized. |
| `deferred_budget` | Dispatch or retry would exceed a document or run ceiling, or safe reconciliation of a prior live attempt is impossible. |
| `deferred_provider` | A transient provider/transport condition exhausted its allowed retry policy, or an ambiguous dispatch made retry unsafe. |
| `failed_input` | Canonical hash, span, task, or request validation failed before dispatch. |
| `failed_provider` | A terminal authentication, permission, request-validation, or unclassified provider/SDK error occurred. |
| `failed_response` | The response was malformed, incomplete, unknown, or came from an unexpected model. |
| `replay_miss` | No exact replay fixture exists for the serialized request. |
| `unprocessed` | The expected work item was not reached because the run terminated earlier. |

Every observation has exactly one version 1 `status_reason_code` allowed for its
status. Within each row of the table below, codes are in strict highest-to-lowest
precedence order: the first applicable code is primary, and every other applicable
code for that same status is stored once in non-null `secondary_reason_codes` in
the same order. Cross-status precedence is determined by Sections 7 and 12.1;
accounting conditions additionally use their flags and diagnostics rather than an
invented combined status.

| Status | Allowed version 1 reason codes |
| --- | --- |
| `observed` | `valid_answer` |
| `deferred_configuration` | `configuration_invalid`, `optional_dependency_missing`, `backend_not_selected`, `mode_not_shadow`, `paid_inference_disabled`, `model_id_missing_or_unversioned`, `budget_gate_invalid`, `pricing_basis_invalid`, `estimator_set_invalid`, `external_inference_not_allowed`, `raw_retention_not_allowed`, `api_key_missing_or_blank`, `api_key_format_invalid`, `sdk_retry_control_unavailable` |
| `deferred_budget` | `reconciliation_unknown_stop`, `ceiling_overrun_stop`, `reservation_underestimate_stop`, `run_ceiling_would_exceed`, `document_ceiling_would_exceed` |
| `deferred_provider` | `rate_limit_retry_exhausted`, `overload_retry_exhausted`, `timeout_retry_exhausted`, `transport_retry_exhausted`, `retry_after_exceeds_limit`, `processing_started_retry_unsafe`, `ambiguous_dispatch` |
| `failed_input` | `artifact_invalid`, `canonical_hash_mismatch`, `target_bounds_invalid`, `context_bounds_invalid`, `quote_mismatch`, `context_mismatch`, `speaker_turn_invalid`, `shared_task_state_invalid`, `question_invalid`, `request_serialization_failed`, `authorization_metadata_invalid` |
| `failed_provider` | `authentication_failed`, `permission_denied`, `provider_request_rejected`, `unclassified_provider_error` |
| `failed_response` | `returned_model_mismatch`, `top_level_response_malformed`, `answer_missing`, `answer_type_unknown`, `answer_shape_invalid`, `answer_id_duplicate`, `answer_probability_invalid`, `choice_keys_mismatch`, `choice_selection_invalid`, `choice_probability_sum_invalid` |
| `replay_miss` | `exact_request_not_found` |
| `unprocessed` | `stopped_after_response_failure`, `stopped_after_authentication_failure`, `stopped_after_permission_failure`, `stopped_after_unclassified_provider_error`, `stopped_after_processing_started_retry_unsafe`, `stopped_after_retry_exhaustion` |

Adding or changing a reason code requires a new observation/data-dictionary schema
version. Human-readable detail may add context but must never be used as a machine
category.

An operational outcome is never converted to a semantic no, contradiction, or
insufficient-evidence answer. An `observed` answer is still only a raw shadow
measurement, not an accepted research label. `unprocessed` is assigned only while
finalizing a gracefully failed/partial run; a hard interruption leaves only an
unpromoted staging directory and therefore cannot masquerade as complete coverage.

## 12. Retry, budget, and logging policy

### 12.1 Deterministic version 1 scheduler

Version 1 executes live and replay requests sequentially with maximum concurrency
one. After building the expected-work ledger, it forms at most one theme batch per
target and one claim-support request per `(target_span_id, claim_id)`. It never
batches across targets, task families, or documents. Questions inside a theme
batch are sorted by question ID as required by Section 9.

Requests whose inputs can be validated and serialized are sorted by:

```text
(document_id, target_start, target_end, task_rank, request_hash)
```

String components use lexicographic order over their UTF-8 bytes, numeric offsets
use ascending order, and `task_rank` is `0` for theme mention and `1` for claim
support. The resulting zero-based position is `request_sequence`. Invalid work is
finalized as `failed_input` before this ordering; a run-wide preflight failure is
finalized before any request is scheduled. Sequential execution plus the stable
order makes reservations atomic and makes finite-budget outcomes reproducible.

The scheduler applies these stop rules:

| Condition | Affected request/work | Later work |
| --- | --- | --- |
| Run-wide live preflight failure, such as missing dependency, model, key, paid authorization, or valid run ceilings | All otherwise eligible live work is `deferred_configuration`; no dispatch occurs | Run is `completed` because every expected row is finalized |
| Record-specific authorization for the requested live-inference or raw-retention action is not `allowed` | Affected work is `deferred_configuration` | Continue in stable order |
| Input or request-construction failure | Affected work is `failed_input` | Continue in stable order |
| Replay miss | Affected work is `replay_miss` | Continue in stable order; never fall through to live execution |
| Valid response or question-local partial response | Finalize each question under Section 7 | Continue in stable order |
| Extra answer ID only | Record diagnostics; expected answers retain their own outcomes | Continue in stable order |
| Malformed top-level response or returned-model mismatch | Every question in the request is `failed_response` | Finalize all later work as `unprocessed`; run is `partial` |
| Request-specific terminal validation error from the provider | Every question in the request is `failed_provider` | Continue in stable order |
| Provider authentication/permission failure | Every question in the request is `failed_provider` | Finalize all later work as `unprocessed`; run is `partial` |
| Unclassified provider/SDK error | Every question in the request is `failed_provider` with `unclassified_provider_error`; do not retry | Finalize all later work as `unprocessed`; run is `partial` unless budget-safety precedence applies |
| Retryable failure known to precede provider processing, after bounded retry exhaustion | Every question in the request is `deferred_provider` | Finalize all later work as `unprocessed`; run is `partial` |
| Transient provider failure has known/reconciled billing evidence that processing began | Every question in the request is `deferred_provider` with `processing_started_retry_unsafe`; do not retry | Finalize all later work as `unprocessed`; run is `partial` unless the budget-safety precedence below applies |
| Timeout or transport failure after dispatch may have reached the provider | Every question in the request is `deferred_provider`; retain the reservation and mark reconciliation unknown | Do not retry; finalize all later live work as `deferred_budget`; run is `partial` |
| Per-document ceiling prevents a reservation | This and all later requests for that document are `deferred_budget` | Continue with the next document if run accounting remains known and within its ceilings; run is `partial` |
| Per-run ceiling prevents a reservation | This and all later requests are `deferred_budget` | Run is `partial` even though every expected row is finalized |
| Known actual usage or cost exceeds its reservation | Keep the request's semantic outcomes; mark `reservation_underestimate` and any separate document/run ceiling breach | Finalize all later live work as `deferred_budget`; the estimator is no longer demonstrably conservative and the run is `partial` |
| Post-response usage/cost is insufficient for reconciliation | Keep any valid semantic outcomes and mark reconciliation unknown | Finalize all later live work as `deferred_budget`; run is `partial` |

Conditions can coincide. The current request first receives the semantic/provider
statuses required by Sections 7 and 11; accounting flags do not overwrite them.
For later work, budget safety has precedence: an underestimate, ceiling breach, or
unknown reconciliation produces the applicable `deferred_budget` finalization
even when the same response also has a model or shape failure. If accounting is
known and within bounds, the provider stop/continue rule applies. This precedence
is part of the scheduler contract and must be covered by table-driven tests.

A hard process interruption is different from a graceful stop: it leaves only the
unpromoted staging directory and no final rows or manifest claiming completion.

### 12.2 Retry ownership

The TypeSafe adapter owns the retry loop in this slice. It must disable automatic
SDK retries for every System One call using the pinned SDK's supported zero-retry
policy; if the resolved SDK cannot demonstrably do that, live execution is blocked
until this specification is revised. One SDK call is one observable attempt.

The adapter retry loop has an explicit per-attempt timeout, finite total attempt
limit, bounded backoff, and support for provider retry guidance exposed by the
pinned SDK. `max_attempts` includes the initial dispatch. A provider retry delay
is honored when it is within the configured maximum. If the provider asks for a
longer delay, the adapter ends the request as `deferred_provider` rather than
retrying sooner than instructed. No runner, workflow, or caller may wrap the
adapter in another automatic retry loop. This assignment supersedes the
workflow-owned retry proposal in `AGENTS-jev-addendum.md` because no orchestration
workflow exists in this scope.

Authentication, permission, request-validation, and unclassified provider/SDK
errors are terminal for the current request and are never retried; Section 12.1
determines whether the run continues. A rate
limit, overload, timeout, or transport failure may retry only when the adapter has
affirmative evidence that provider processing did not begin. A failure after
dispatch whose billing is ambiguous is never retried. Eligible retries remain
within both the attempt and document/run budgets. Exhaustion produces the typed
outcome and stop behavior in Section 12.1 and preserves independently completed
observations.

### 12.3 Budget reservation and reconciliation

Before each live attempt, the adapter reserves against both the request's document
ledger and the run ledger: one provider request, an input-token upper-bound
estimate produced by a named/versioned estimator, and cost calculated in integer
microunits under `pricing-basis-v1`. The cost reservation covers every billed
component, using named/versioned upper bounds for any output-dependent component;
live preflight fails if a component cannot be bounded. A batched request is
charged wholly to its single document. Request count measures provider-call
attempts, including retries. A reservation is atomic and succeeds only when the
resulting cumulative values are less than or equal to every applicable document
and run ceiling.

Every dispatched attempt receives exactly one billing disposition from Section
10.2. An error class alone never proves that an attempt was unbilled. A provider
error without sufficient usage is `confirmed_not_processed` only when explicit
response metadata or transport-level proof establishes that no request bytes
reached processing; an HTTP status code alone is insufficient. Otherwise it is
`ambiguous`. The semantic/provider status and scheduler stop rule remain those for
the actual error, subject to the budget-safety precedence in Section 12.1.

For `confirmed_not_processed`, the provider-request reservation remains consumed
because an attempt occurred, and the adapter **must** release the entire token and
cost reservations before considering an eligible retry. For `reported_usage`, the
adapter **must** replace the token reservation with reported input usage and
compute cost from all reported billable units and the pinned pricing formula. If
the provider also reports cost in the configured currency, reconciliation uses the
larger of that value and the calculated cost and records any disagreement. After
every `reported_usage` reconciliation, the adapter must release exactly any
positive token/cost surplus. Retaining optional surplus is not permitted because
it would make scheduling implementation-dependent.

Every `ambiguous` disposition, regardless of cause, must retain the full token and
cost reservation, set `budget_reconciliation_unknown=true`, emit the
`budget_reconciliation_unknown` diagnostic plus any cause-specific diagnostic,
and prohibit retry. The current request keeps its independently determined
semantic/provider status; all later live work is `deferred_budget`. The following
paragraphs select statuses and cause diagnostics but do not alter that accounting
rule.

Unless `confirmed_not_processed` already won under Section 10.2 precedence, a
provider-reported cost in another currency selects `ambiguous`, because version 1
neither converts nor compares it, and emits `provider_currency_mismatch`. A zero
foreign-currency cost paired with valid confirmed-not-processed evidence remains
`confirmed_not_processed`; no conversion is needed to establish zero billing.

A timeout or transport failure after dispatch may have reached the provider. It
selects `ambiguous`, and the affected questions become `deferred_provider` with
reason `ambiguous_dispatch`.

Known actual usage or reconciled cost above its reservation sets
`reservation_underestimate=true`, records the known delta, and emits a diagnostic.
Separately, `ceiling_overrun=true` only when reconciled document or run totals
for any determinable request/token/cost dimension actually exceed a configured
ceiling; its nullable scope is `document`, `run`, or `both`. Both flags follow the
componentwise three-valued rule in Section 10.1. A reservation underestimate that
remains below both ceilings therefore has no ceiling-overrun scope. In either case,
the current response keeps its
independently determined semantic status—a valid answer remains `observed`—and
all later live work becomes `deferred_budget` because the estimator is no longer
demonstrably conservative.

If a response contains semantic answers but lacks the usage or cost inputs needed
for the pinned pricing formula, those answers likewise keep their independently
determined status and the attempt selects `ambiguous`. Unknown values remain null
rather than zero. Neither an underestimate nor a ceiling overrun is hidden by
retroactively changing a semantic answer to a failure.

The manifest records every document ledger and the run ledger: reservations,
released surplus, reported usage, pricing-basis ID and currency,
estimated/reconciled cost microunits, reservation underestimates, ceiling overruns,
and unknown reconciliation. Summary totals deduplicate batched observation rows
by request sequence.

### 12.4 Logging and sensitive content

Normal logging must not include canonical text, quotes, context, claims, question
bodies, raw responses, API keys, or authorization headers. The TypeSafe SDK's
debug mode can include request and response bodies; the integration must keep it
disabled by default. Deliberate debug use is limited to permitted test data and
requires an explicit operator action.

Raw responses, if retained, belong in ignored run artifacts rather than logs.
Secrets and credentials must never enter committed files, fixtures, manifests,
or exception text.

## 13. Fixtures

The initial corpus is small, curated, and redistributable. Prefer synthetic text
so ordinary tests have no filing or transcript redistribution ambiguity. It must
assign stable document, target-span, and work-item source IDs even to deliberately
malformed cases, and exercise at least:

- a span that mentions multiple themes;
- a clear non-mention;
- a denial that mentions a theme without asserting the event;
- supported, contradicted, and insufficient-evidence claims;
- context that disambiguates the target without becoming substitute evidence;
- management, analyst, unknown, and non-transcript role treatment as applicable;
- Unicode and non-ASCII text for character-offset validation;
- malformed hashes and offsets;
- all declared operational statuses; and
- a partial run containing both completed and `unprocessed` work.

Fixture reference labels exist to test the evaluator and report. They are not an
approved production codebook, gold corpus, calibration set, or vendor benchmark.
Any non-synthetic fixture must record its source and redistribution basis.

## 14. Test requirements

Default tests are deterministic, offline, and non-billable. They must cover:

### Core evidence contracts

- canonical UTF-8 hashing and hash mismatch;
- zero-based half-open target/context offsets;
- exact quote slicing, Unicode, and invalid ranges; and
- speaker-boundary and canonical-version invariants represented by fixtures.

### Task construction and semantics

- one binary question per theme and multiple positive themes for one target;
- complete, versioned definitions and boundary rules in every question;
- denial as mention but not event assertion;
- exactly three claim-support outcomes;
- separation of theme and support request state;
- shared-state versus question-local construction failures and deterministic
  reduced-batch hashing;
- golden canonical bytes and hashes for prompt, question, codebook,
  authorization-record, pricing-basis, estimator-set, and effective non-secret
  configuration objects;
- RFC 8785 request bytes and golden request hashes;
- exact `semantic-state-v1` disclosure with provenance-only fields absent from the
  fake SDK payload; and
- transcript turn-boundary validation.

### Backend behavior

- deterministic replay results, injected test fakes, and exact replay misses;
- no network fallback on any replay path;
- base package import when the optional SDK is absent;
- adapter translation through a fake SDK client;
- explicit versioned model forwarding and returned-model verification;
- valid, partial, malformed, missing, duplicate, extra-ID, and top-level-invalid
  response handling;
- raw probability/distribution, `provider_confidence_raw`, and usage preservation;
- deterministic sequential scheduling and every stop/continue branch in Section
  12.1;
- primary/secondary reason-code precedence for coincident gates, validation
  failures, document/run ceilings, and accounting conditions;
- disabled SDK retries, adapter-owned bounded retries, ambiguous-timeout
  reservation, per-document and per-run accounting, batched-request charging,
  integer-microunit rounding, incompatible currency, reservation underestimates,
  ceiling overruns, and unknown reconciliation;
- global and record-specific authorization preflight, including proof that a
  runtime retention flag cannot grant raw-response permission; and
- every status/error mapping in Section 11.

### Outputs and safety

- observation/attempt/diagnostic Parquet types, per-status nullability,
  uniqueness, and round-trip behavior against the versioned data dictionary;
- exact status-reason and diagnostic-code vocabularies with undeclared columns or
  enum values rejected;
- expected-work denominators, per-question final rows, and partial-run reporting;
- `partial` run status for budget exhaustion/safety stops and provider stops,
  including when the stopped request is last;
- request diagnostics, including unexpected answer IDs when raw retention is off;
- request-deduplicated usage/cost totals for batched observations;
- caller-supplied run-ID validation, path traversal rejection, and collision
  handling;
- whole-run staging/promotion, checksum failure, interruption, and destination
  collision without overwrite;
- stable machine-summary counts and fixture-reference metrics;
- absence of secrets and request bodies from normal logs;
- no write or network side effect on import; and
- proof that the public runner result exposes no accepted-assignment or
  production-writer interface.

Add one offline end-to-end test from canonical fixture through evidence validation,
task construction, replay, normalized observations, manifest, and report.

A separately marked `live` smoke test may check authenticated API compatibility.
It requires all live-call gates, is excluded from ordinary CI, must use only
permitted test data, and is not required for implementation acceptance.

After the workspace-stability precondition in Section 2 is satisfied, the JEV plan
may add the missing shared pytest/Ruff configuration, registered `live` marker,
and only those test dependencies needed by this slice. It must not assume a
dependency is usable merely because it appears in an uncommitted manifest.

## 15. Acceptance criteria

The initial integration is complete only when all of the following are true:

1. The workspace-stability precondition in Section 2 is met without the JEV
   change silently completing unrelated ingestion/application work.
2. The virtual workspace root and package dependency direction remain intact:
   ingestion and themes may depend on core, a pipeline app may depend on all three,
   and no package may depend on the application.
3. Base installation and imports work without the JEV extra or credentials.
4. The optional SDK is isolated to the TypeSafe adapter and intentionally locked.
5. All ordinary tests pass offline with no network or billable calls.
6. Invalid evidence is rejected before backend execution.
7. Golden artifact/request serialization and replay are deterministic and never
   fall through to live inference.
8. Live preflight rejects every missing authorization/configuration gate before
   dispatch and always forwards a versioned model ID.
9. The version 1 scheduler order and stop/continue matrix are deterministic; SDK
   retries are disabled; and attempts, reservations, reconciliation, overruns,
   and retry outcomes match every document and run ceiling, with exhaustion or a
   budget-safety stop reported as a `partial` run.
10. Theme mention and claim support remain separate requests and observations.
11. Every expected work item has exactly one final row in a finalized run,
    including `unprocessed`; no unknown is coerced to a negative answer.
12. Valid answers in a partial batch survive while missing/malformed answers
    receive `failed_response` under the declared policy.
13. Replay produces normalized Parquet observations, an empty schema-valid
    request-attempt table, request diagnostics, the versioned data dictionary, a
    complete manifest, and the expected descriptive shadow report from the curated
    corpus.
14. Run persistence never overwrites an existing run and exposes only completely
    promoted final directories as completed runs.
15. The public runner result has no accepted-assignment or production-writer
    interface.
16. Documentation states that no quality threshold, production promotion, live
    benchmark, or earnings-domain performance claim has been established.
17. Every claim-support observation carries a paired baseline score from the
    open-weight entailment scorer named in `specs/evidence-linked-theme-extraction.md`
    R8.2, computed over the identical target span and claim and recorded as its own
    observation with separate model identity, parameters, and provenance. Shadow
    completion does not require JEV to beat that baseline; it requires the
    comparison to be computable from the run's own artifacts.

Criterion 17 exists because `specs/evidence-linked-theme-extraction.md` R14.3
permits this layer only as an option "benchmarked against R8.2". A shadow run
that cannot produce that comparison cannot inform the decision it exists to
inform. This is a descriptive, same-corpus, offline comparison between two
backends on fixture evidence — not the production-quality benchmark excluded in
§4, and not evidence of earnings-domain performance. R8.2 also makes the
open-weight scorer this integration's incumbent rather than a deferred
alternative; §16 is amended accordingly.

Application tests and any optional live smoke test must be reported separately.
A successful offline fixture run must not be described as a full-corpus or live
JEV validation.

## 16. Deferred follow-on decisions

After this slice exists, separate design work may consider:

- a real adjudicated earnings corpus and grouped/time-aware evaluation split;
- per-task and per-theme calibration and routing thresholds;
- promotion from shadow observations to reviewed or accepted assignments;
- candidate extraction or deterministic window coding;
- a production codebook and change/backfill policy;
- pipeline orchestration, checkpointing, and operator-facing commands;
- additional providers, and baselines beyond the R8.2 scorer already required
  by §15 criterion 17; and
- carefully scoped ingestion applications.

Each follow-on must preserve the evidence, cost, rights, time, and missingness
rules in `AGENTS.md`. This specification grants no advance approval for paid
backfills or production promotion.

## 17. Sources and mutable assumptions

Project context:

- `AGENTS.md`
- `CLAUDE.md`
- `docs/earnings-themes.md`
- `docs/earnings-ingestion.md`

TypeSafe documentation checked on 2026-09-22:

- Python SDK and installation: `https://docs.typesafe.ai/sdk/python`
- SDK usage, model selection, retries, errors, and logging:
  `https://docs.typesafe.ai/sdk/python/usage`
- HTTP API and answer shapes: `https://docs.typesafe.ai/api`
- Models and moving aliases: `https://docs.typesafe.ai/models`
- Choice/Score confidence semantics: `https://docs.typesafe.ai/confidence`
- Official Python SDK and package metadata:
  `https://github.com/typesafe-ai/typesafe-sdk-python`

Canonical serialization:

- IETF RFC 8785, JSON Canonicalization Scheme:
  `https://www.rfc-editor.org/rfc/rfc8785`

The public SDK and service documentation are mutable. The implementation plan
must recheck the current SDK version, supported Python range, request/response
types, retry behavior, model availability, pricing, rate limits, data handling,
and logging behavior before locking or using the dependency or authorizing a live
test.
Current documentation establishes interface facts, not performance on this
project's corpus.
