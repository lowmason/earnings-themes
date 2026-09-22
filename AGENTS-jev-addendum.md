# Proposed AGENTS.md addendum: decision models and Jev

Status: proposed; not applied to an existing repository. Reviewed 2026-09-22.

## Architecture and dependency boundaries

Jev is an optional backend for bounded semantic decisions. It is not the project orchestrator, generative extraction model, canonical-text parser, or source of record. Keep vendor SDK imports inside the decision-provider adapter. The theme package owns the codebook and question definitions; the workflow owns routing and retries; the shared contracts package owns evidence identifiers and decision records.

Paid inference must be explicitly enabled. The repository must remain installable and testable without a TypeSafe API key. A disabled backend must use the configured baseline or produce an explicit review/deferred status, never fabricated negative labels. Do not silently substitute another model or provider in a research run.

## Evidence invariants

Preserve the original source artifact and an immutable, versioned canonical text. Each evidence span must resolve to a valid `(document_id, canonical_sha256, start, end)` tuple. Quotes displayed in reports must be sliced from that canonical text, not generated or rewritten by a model. Invalid hashes, offsets, and citations are deterministic failures.

Separate three questions: whether a span is exact, whether its context supports an interpretation, and whether the underlying company statement is independently true. A model judgment about semantic support establishes neither quote exactness nor external factual truth.

Preserve document type, speaker role, section, reporting period, and source availability date. Analyst questions must not become management assertions. Dates, totals, units, numerical comparisons, identity constraints, and ownership-graph invariants remain code-controlled.

## Question and codebook design

Use one Noul per theme for multi-label coding. Use Choice only when the alternatives are mutually exclusive, with an insufficient-evidence or none-of-the-above outcome where appropriate. A Score is an ordinal rubric judgment, not a reported numeric value.

Write every question so it contains the full task, relevant theme definition, inclusion/exclusion criteria, and target span reference. Do not rely on question IDs conveying meaning. Same-request questions cannot depend on one another's answers. Separate stages in code when there is a dependency.

Distinguish topic mention, asserted direction, denial, uncertainty, and forward-looking language. Bind the label to the target span; surrounding context is for interpretation, not evidence for a different target.

Freeze and version the codebook, question set, segmentation/context construction, model, calibration, and decision policy for each research vintage. Discovery of new themes requires a separate exploration and human-approval process; do not mutate the production codebook during coding.

## Reliability and security

Start in shadow mode. Do not filter out passages, publish labels, merge entities, or change production results solely because an unvalidated Jev output is confident. Select thresholds using adjudicated development data and evaluate on untouched, grouped/time-aware holdouts. Preserve rejected cases and audit false negatives.

Keep raw model probabilities and full Choice/Score distributions separate from calibrated probabilities and routing decisions. Noul has no separate confidence field. Unknown, unavailable, unsupported, abstained, and negative are different statuses. An API failure never means a theme is absent.

Treat filing text and tool outputs as untrusted data. A classifier must not authorize shell execution, network access, database writes, or secret disclosure. Enforce allowlists, write permissions, and destructive-action approval in code. Do not send restricted material to an external provider without approval.

Use bounded concurrency, timeouts, retry budgets, and a circuit breaker. Keep secrets outside tracked files. Avoid logging request bodies by default. Test authentication failures, rate limits, malformed and missing answers, model mismatches, and provider outages with fixtures rather than live requests in ordinary CI.

## Provenance, caching, and promotion

Record the requested and returned model IDs, backend, SDK/lockfile version, request ID, canonical hash, target/context offsets, serialized question hash, codebook version, input usage, timing, raw response, decision policy, calibration version, and final status.

Key inference caches by the pinned model and exact serialized state/questions, including all context that can influence the answer. Store routing policy separately so thresholds can be reevaluated without another inference call. Never reuse inference results across altered text, questions, context windows, or models.

Promote a backend only after measuring theme precision/recall, support false-acceptance, calibration, selective risk/coverage, run stability, end-to-end cost, and coverage by issuer/period/document/speaker. Exact quote integrity must pass for every published quote. Model changes create a new research vintage or an explicit full backfill, not an unmarked time-series break.

## Optional coding-agent assistance

The official TypeSafe skill can help a coding agent implement the adapter. Review and pin any installed skill and its reference files. Installation does not replace the agent's generative model and does not grant permission to make paid requests. Keep project evidence, testing, and security rules authoritative.
