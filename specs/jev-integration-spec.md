# Optional JEV shadow-decision integration

**Status:** Proposed implementation specification; design approved in the
brainstorming dialogue, written specification awaiting final review.

**As of:** 2026-09-22.

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
explicit versioned model ID, a positive run budget, and credentials supplied
outside committed configuration.

## 2. Repository context

This specification applies to the repository as it exists on 2026-09-22:

- The root `pyproject.toml` is an intentional virtual uv workspace with no
  `[project]` table.
- The implemented package directories are `packages/earnings-core`,
  `packages/earnings-ingestion`, and `packages/earnings-themes`. The current
  worktree is also registering a prospective `apps/earnings-pipeline` member,
  but that member has not yet been scaffolded and this specification does not
  depend on it.
- The domain packages remain pre-implementation stubs. There is no existing
  canonical document pipeline, extraction pipeline, decision backend, test
  suite, CI configuration, or application implementation to extend.
- The existing `config/`, `prompts/`, `codebooks/`, `tests/`, and `data/runs/`
  roots are the intended homes for configuration, versioned research artifacts,
  fixtures, and ignored run outputs.

JEV fits the existing package boundaries. This specification does not require a
new decision package, a root project, or creation of the prospective pipeline
application. It therefore does not require JEV-specific changes to the workspace
topology, `AGENTS.md`, or `CLAUDE.md`. Future implementation will update relevant
member dependencies and the workspace lockfile, but not the root's
virtual-workspace role.

## 3. Goals

The first integration must:

- define the minimum canonical-document and verified-evidence contracts needed
  to test decisions without building ingestion or extraction first;
- define provider-neutral request, observation, status, and run-summary contracts;
- keep all TypeSafe SDK imports behind one optional adapter boundary;
- support deterministic fake/replay execution with no credentials or network;
- support explicitly authorized live JEV shadow requests;
- evaluate theme mention and claim support as separate tasks;
- preserve the raw probability or distribution returned for every answer;
- record enough provenance to reproduce or audit each observation;
- distinguish negative semantic results from unavailable, deferred, failed, and
  unprocessed work;
- produce normalized shadow observations, a run manifest, and descriptive reports;
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
canonical_sha256 == sha256(canonical_text encoded as UTF-8)
```

Invalid evidence is an input failure and must never be sent to a model.

### 5.2 `earnings-ingestion`

`earnings-ingestion` is unchanged by this specification. Curated fixtures stand
in for its future canonical-document output. The integration must not introduce
a downloader, parser, issuer resolver, or alternate canonicalization path into
`earnings-themes`.

### 5.3 `earnings-themes`

`earnings-themes` owns:

- the provider-neutral decision-backend protocol;
- theme-mention and claim-support task contracts;
- task construction from versioned prompts and codebooks;
- fake/replay and TypeSafe adapters;
- live-run preflight and bounded operational policy;
- normalized decision observations;
- the shadow evaluator and descriptive report; and
- serialization to the declared analytical artifacts.

Only the TypeSafe adapter may import `typesafe_sdk`. Importing the base
`earnings_themes` package must not import or require the SDK transitively.

### 5.4 Repository artifacts

The implementation must use the existing roots rather than introduce parallel
top-level structures:

| Artifact | Intended location |
| --- | --- |
| Versioned semantic task wording | `prompts/jev/` |
| Explicitly test-only codebook | `codebooks/` with test-only status metadata |
| Canonical documents, spans, labels, and replay responses | `tests/fixtures/jev/` |
| Package unit tests | the owning package's `tests/` directory |
| Cross-package/offline vertical test | `tests/integration/` |
| Optional live compatibility test | a registered `live` pytest test |
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
- document type, section, and speaker role where applicable;
- source/reference/publication metadata available in the fixture; and
- fixture or corpus version.

The context span may equal the target span. A target must not cross a transcript
speaker boundary. Unknown speaker role remains explicit rather than becoming
management.

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

### 6.3 Claim-support task

Claim support evaluates one atomic claim against one verified target and its
permitted context. It uses exactly these mutually exclusive outcomes:

- `supports`: the target, interpreted with context, supports the complete claim;
- `contradicts`: the target explicitly conflicts with the claim; and
- `insufficient_evidence`: the target does not establish the complete claim,
  including when necessary context is absent.

The normalized observation preserves the selected outcome, the full probability
distribution, and vendor confidence when returned. Confidence is derived from the
distribution; it is not an independently calibrated probability that the research
interpretation is correct.

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

## 7. Provider-neutral backend boundary

The backend protocol accepts an immutable, fully validated semantic request and
returns either:

- raw semantic answers plus provider metadata; or
- a typed operational outcome describing why answers are unavailable.

The protocol must not publish labels, modify evidence, mutate the codebook, apply
acceptance thresholds, create ingestion assertions, or make authorization
decisions.

Provider-neutral application code must not depend on SDK response classes or
exceptions. The TypeSafe adapter translates SDK requests, responses, and failures
at the boundary. The replay adapter implements the same protocol from committed
fixtures.

## 8. Execution modes and live-call authorization

### 8.1 Offline default

Replay is the default execution mode for development, ordinary tests, and the
offline vertical slice. Importing a module, constructing a backend, encountering
a replay miss, or generating a report must never trigger a live fallback.

A safe committed configuration may select replay and shadow mode, but must not
contain a model default, credential, or positive paid-inference budget.

### 8.2 Optional TypeSafe adapter

The TypeSafe SDK becomes an optional dependency extra of
`packages/earnings-themes`; it is not a root, core, ingestion, or unconditional
runtime dependency. The implementation plan must resolve a Python 3.14-compatible
SDK version, update `uv.lock` intentionally, and review the dependency diff.

The adapter may make a request only when all of these gates pass:

1. the optional dependency is installed;
2. the TypeSafe backend is explicitly selected;
3. shadow is the selected mode;
4. paid inference is explicitly enabled;
5. a concrete, versioned model ID is supplied;
6. a positive request and/or input-token budget is supplied; and
7. a valid API key is available outside committed configuration.

Missing any gate yields a structured preflight deferral before network dispatch.
The adapter must pass the configured model on every call. It must not inherit the
SDK's moving alias default, accept `jev-latest`/`jev-preview` as a reproducible
version, silently select a provider, or substitute another model after failure.

The response's versioned model ID must be recorded and checked against the
requested version. A mismatch is a failed response requiring review, not a valid
shadow observation.

## 9. Replay identity and reproducibility

Replay identity is the hash of a canonical serialization that includes every
input capable of changing an answer:

- request schema version and task kind;
- canonical document and target/context text and offsets;
- document, speaker, and section metadata included in state;
- claim text for claim-support requests;
- complete question contents and question-set ordering/canonicalization rule;
- prompt and codebook IDs, versions, and hashes;
- requested model ID;
- adapter/request-shaping version; and
- model parameters or supported extra fields, if any.

Semantically identical inputs must serialize identically. Changed text, context,
claim, questions, model, or request shaping must miss rather than reuse an old
response. A replay miss returns an explicit status and never calls the network.

Raw model observations and derived reporting policy are versioned separately so
future thresholds can be evaluated without relabeling a raw response as though it
came from a new model call.

## 10. Observations and output artifacts

### 10.1 Decision observation

Every attempted answer produces an auditable observation or explicit operational
outcome with, at minimum:

- run, request, task, question, document, and target-span IDs;
- theme ID or claim ID as applicable;
- canonical, prompt, question, codebook, request, and configuration hashes;
- backend, adapter/SDK version, requested model, and returned model;
- raw yes-probability or selected choice and full distribution;
- provider confidence only when the answer type supplies it;
- request ID when returned, token usage, attempt count, and latency;
- observation status and precise reason/details for non-observed work;
- raw-response reference or a reason the raw response was not retained; and
- UTC run timestamps and software/lockfile provenance.

Null or unavailable numeric values remain null. They must not become zero.

### 10.2 Run manifest and coverage

The run manifest identifies the fixture corpus, complete configuration, software
and lockfile versions, artifact hashes, authorization mode, budgets, start/end
times, and output locations.

Coverage uses the full set of eligible fixture tasks as its denominator. It
reports expected, observed, deferred, failed, and replay-miss counts separately
for theme mention and claim support. A table of successful answers alone is not a
coverage report.

### 10.3 Persistence and report

When the caller requests persistence, the shadow runner writes atomically to an
explicit caller-selected run directory:

- normalized decision observations in Parquet;
- a machine-readable run manifest and summary;
- an optional raw-response artifact when retention is permitted; and
- a concise human-readable shadow report.

The report describes task coverage, statuses, output distributions, requested and
returned models, usage, attempts, latency, and fixture-reference agreement where
labels exist. It must identify the corpus as test-only and state that agreement on
small synthetic fixtures is not a production-quality estimate.

The runner returns the same normalized observations and summary to library callers.
It does not require a CLI or write files on import.

## 11. Status and error semantics

At minimum, the implementation must distinguish:

| Outcome | Meaning |
| --- | --- |
| `observed` | A structurally valid raw semantic answer was recorded in shadow mode. |
| `deferred_configuration` | Optional dependency, authorization, model, key, or other required configuration is absent. |
| `deferred_budget` | Dispatch or retry would exceed the explicit run budget. |
| `deferred_provider` | A transient provider/transport condition exhausted its bounded retry allowance. |
| `failed_input` | Canonical hash, span, task, or request validation failed before dispatch. |
| `failed_provider` | A terminal authentication or request-validation error occurred. |
| `failed_response` | The response was malformed, incomplete, unknown, or came from an unexpected model. |
| `replay_miss` | No exact replay fixture exists for the serialized request. |

An operational outcome is never converted to a semantic no, contradiction, or
insufficient-evidence answer. An `observed` answer is still only a raw shadow
measurement, not an accepted research label.

## 12. Retry, budget, and logging policy

Exactly one layer owns retries. The TypeSafe adapter must configure:

- an explicit request timeout;
- a finite attempt limit;
- bounded backoff and supported provider retry guidance; and
- accounting that charges every attempt against the run budget.

Authentication and request-validation errors are terminal. Rate limiting,
overload, timeout, and transient transport failures may retry within both the
attempt and run budgets. Exhaustion produces a typed deferral and preserves any
independently completed observations in a visibly partial run.

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
exercise at least:

- a span that mentions multiple themes;
- a clear non-mention;
- a denial that mentions a theme without asserting the event;
- supported, contradicted, and insufficient-evidence claims;
- context that disambiguates the target without becoming substitute evidence;
- management, analyst, unknown, and non-transcript role treatment as applicable;
- Unicode and non-ASCII text for character-offset validation;
- malformed hashes and offsets;
- all declared operational statuses; and
- a partial run containing both completed and unavailable work.

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
- separation of theme and support request state; and
- stable question, codebook, and request hashes.

### Backend behavior

- deterministic fake/replay results and exact replay misses;
- no network fallback on any replay path;
- base package import when the optional SDK is absent;
- adapter translation through a fake SDK client;
- explicit versioned model forwarding and returned-model verification;
- raw probability/distribution and usage preservation;
- bounded retry and budget accounting; and
- every status/error mapping in Section 11.

### Outputs and safety

- Parquet schema and round-trip behavior;
- complete denominators and partial-run reporting;
- atomic writes to explicit destinations;
- absence of secrets and request bodies from normal logs;
- no write or network side effect on import; and
- proof that shadow observations cannot enter an accepted-assignment output.

Add one offline end-to-end test from canonical fixture through evidence validation,
task construction, replay, normalized observations, manifest, and report.

A separately marked `live` smoke test may check authenticated API compatibility.
It requires all live-call gates, is excluded from ordinary CI, must use only
permitted test data, and is not required for implementation acceptance.

The current worktree is adding a root development dependency group, but it still
has no shared pytest configuration, registered `live` marker, test suite, or CI.
The implementation plan must inspect the state it receives and add only the
remaining setup needed to run these tests; it must not assume an in-progress
workspace edit is complete merely because it is present in `pyproject.toml`.

## 15. Acceptance criteria

The initial integration is complete only when all of the following are true:

1. The virtual workspace root and package dependency direction remain intact:
   ingestion and themes may depend on core, a pipeline app may depend on all three,
   and no package may depend on the application.
2. Base installation and imports work without the JEV extra or credentials.
3. The optional SDK is isolated to the TypeSafe adapter and intentionally locked.
4. All ordinary tests pass offline with no network or billable calls.
5. Invalid evidence is rejected before backend execution.
6. Replay is deterministic and never falls through to live inference.
7. Live preflight rejects every missing authorization/configuration gate before
   dispatch and always forwards a versioned model ID.
8. Theme mention and claim support remain separate requests and observations.
9. Every attempted task appears in coverage as observed, deferred, failed, or a
   replay miss; no unknown is coerced to a negative answer.
10. Replay produces normalized Parquet observations, a complete manifest, and the
    expected descriptive shadow report from the curated corpus.
11. Shadow results cannot modify accepted assignments or production outputs.
12. Documentation states that no quality threshold, production promotion, live
    benchmark, or earnings-domain performance claim has been established.

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
- additional providers or local baselines; and
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

The public SDK and service documentation are mutable. The implementation plan
must recheck the current SDK version, supported Python range, request/response
types, retry behavior, model availability, pricing, rate limits, data handling,
and logging behavior before adding the dependency or authorizing a live test.
Current documentation establishes interface facts, not performance on this
project's corpus.
