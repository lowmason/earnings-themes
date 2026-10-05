# Semantic support: implementation evidence and pending completion gates

Date: 2026-10-05. Branch: `codex/stage8-semantic-support`.
Execution base: `5463a44c311a91fd4ef363f5bed63273f40f2898`.
Implementation checkpoint checked by the controller: `5eeb28ba79bfdf78cf96cde5211154cfc270fdf9`.
Task 12 documentation/public-export preparation starts at that checkpoint.

**Stage 8 is not complete.** Offline implementation evidence is recorded below.
Required V4 actual primary inference, the user's complete root default suite and
both full Stage 6 wording nodes, and final whole-branch review remain unobserved.
No plan/spec retirement, roadmap completion tick, or integration follows from this
record. It contains no pilot quality, agreement, or fresh-call stability result.

## Implemented library seams

`earnings_themes.support` exports the explicit `Target`, `SupportSources`, and
`ResolvedInput` contracts; target resolution, target/run assessment; immutable
storage and a consuming gate; and pure metrics with typed inputs and reports.
Neither public initializer imports a concrete adapter. Callers select artifacts,
prompts, codebook/theme references, model identities, ceilings, and cache paths.
There is no implicit configuration lookup, latest-codebook discovery or import-time
client creation, file write, or model download.

| Seam | Implemented boundary |
| --- | --- |
| `resolve_target(stored_run, bundles, codebook, target, *, provenance_hash)` | Binds source-run provenance, document/claim identity, every original quote link, current masks and selected frozen theme. Returns `ResolvedInput` or `RefusedTarget`; never dereferences codebook examples. |
| `assess_target(input, scorer, judges, policy, allowance, *, cache, extractor_family)` | Requires explicit extractor lineage, validates panel/policy/runtime identities and re-verifies exact evidence before dispatch and before returning signals. |
| `assess_run(run_id, sources, targets, scorer, judges, policy, ceilings, *, extractor_family, cache, started_at, software)` | Preflights run metadata, UTC time, software/lock identity and ceilings, then assesses targets sequentially in supplied order. |
| `write_support_run(directory, result, sources)` | Re-resolves non-refused inputs and exact spans before publishing eight explicit-schema Parquet tables and `run.json` into a new directory atomically. |
| `read_support_run(directory)` | Checks published table hashes/schemas, typed rows, references, required signal/trial cardinality, recomputed outcomes/counts and ceilings. |
| `reverify_support_run(stored, sources)` | Repeats source/evidence/theme/context resolution and scorer-input hash checks before downstream use; returns processing outcomes only. |
| `auc_roc(population, labels, signals, *, task, view)` | Joins an explicit human-label task to one selected continuous view, with tied scores earning half credit. |
| `accepted_claim_precision(population, labels, decisions, *, task)` | Measures support among externally accepted labeled targets and reports accepted targets without labels. Acceptance is supplied by the caller. |

The public metric parts are `HumanLabel`, `ContinuousSignal`, `Acceptance`, and
`MetricReport`. Duplicate IDs, mixed tasks/views, mismatched joins and invalid
labels/scores refuse. Empty/one-class AUC and no labeled accepted targets produce
`None` with closed reasons, never a fabricated perfect score or negative label.
The [data dictionary](../data-dictionary.md) records the full schemas and signatures.

## Exactness, signals, accounting, and storage

Every linked quote passes `reverify_span` during resolution, before scoring, before
assessment-result publication, before stored-run publication, and at downstream
consumption. A missing or invalid quote refuses the whole initial target without
dispatch. Post-dispatch mutation aborts publication with fixed `input_changed`,
retaining completed raw cache artifacts/accounting locally. Offsets remain
zero-based Python character indices and half-open spans. Context is separately
labeled, never promoted into quoted evidence or used to repair a span.

The scorer retains per-quote and joint raw signals; a one-quote joint slot aliases
one evaluation. Scores remain finite, uncalibrated values in `[0,1]`. Two explicitly
configured judge families, with at least one different from the extractor family,
each receive independent `evidence_first` and `claim_theme_first` trials. Exactly
four family/presentation slots are required. Each trial permits at most two attempts,
provisionally; only unusable replies retry. Valid negative or uncertain replies
are final. Local rationale is nonblank and bounded to 500 characters. Scorer scores,
other trial replies and raw rationale never appear in another trial or retry feedback.

Outcomes preserve `refused`, `incomplete`, `flagged`, and `assessed`, with all known
semantic flags and missing-signal reasons. No outcome, numeric cutoff, pooling rule,
majority vote or panel consensus creates acceptance. Full input is counted before
dispatch; over-limit inputs yield `input_too_long` without clipping or hidden chunking.
Explicit scorer evaluation ceilings per target/document/run, judge request ceilings
per target/document/run, and judge token ceilings per document/run cover retries
and presentations. Missing actual usage retains the reservation and is reported.
Cache hits spend no dispatch allowance. Manifest counts reconcile with usage rows;
`billable_cost` remains `"none, self-hosted"`.

`live` and `replay` both reuse raw cache hits. Replay misses yield `replay_miss`
without dispatch; live dispatches misses only. Reuse repeats evidence verification.
No fresh-call bypass is implemented. Raw judge transport refusal metadata stays
integrity-bound through `SupportCache.put(..., refusal_reason=...)` and
`SupportCache.refusal_reason(key)`, so a refused raw reply cannot become usable in
replay. Raw wrong-model judge replies remain auditable unusable attempts.

Support schema stays `1` and support policy stays `semantic-support/1`; core schema
`2`, extraction schema `1`, Stage 6 schemas and extraction/verifier versions stay
unchanged. The tables are `targets`, `evidence`, `contexts`, `entailment`, `trials`,
`attempts`, `usage`, and `outcomes`; empty tables keep declared schemas. Existing
output directories are refused and failed publication cleans its temporary sibling.
`artifact_hashes` binds `<table>.parquet` published bytes and `raw/<digest>.json`
external-cache bytes. `JudgeAttempt.raw_ref` stays a confined cache filename.
The reader checks complete raw-reference/hash bindings but cannot verify external
cache bytes without that cache. `SupportCache.artifact_hash(reference)` validates
and hashes those external bytes separately. No raw request/reply is copied into the
support run directory. Requests, replies and rationales remain local and uncommitted.

## Observed offline checks

These first checks were executed by the controller at checkpoint `5eeb28b` in the
blind execution checkout. They are transcribed from its observed command record;
the documentation worker did not repeat the long suites.

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests packages/earnings-themes/tests tests/contracts tests/integration/test_support_fixtures.py tests/integration/test_support_wording.py -m "not live and not browser" -q --tb=short
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Observed: **1347 passed, 4 deselected**, 43.15 seconds; one documented PyTorch JIT
FutureWarning with the optional runtime present. Ruff check passed; 355 files were
already formatted. No type checker is configured in the root/member pyprojects.

```bash
uv sync --locked --all-packages --group dev
uv run --locked --all-packages pytest packages apps tests --ignore=tests/integration/test_stage6_records.py --ignore=tests/integration/test_stage6_wording.py --ignore=tests/integration/test_stage6_pilot_v1.py -m "not live and not browser" -q -rs --tb=short
```

Observed: sync resolved 153 packages and removed 20 optional packages, including the
five heavy support runtime packages. The broad blind subset returned **2616 passed,
5 skipped, 27 deselected**, 87.04 seconds. Skips were the absent discovery input in
`test_events_content`, absent optional runtime in support `test_nli`, and absent
SEC event/acquisition-run inputs in `test_corpus_quotes` and `test_event_store_v1`.
This is a subset result, not a full root-default-suite pass. The three excluded
modules remain user-only because of their pilot/signed-gold access. The controller
reaudited new support/integration test source without opening protected artifacts;
no new pilot/gold reader changed those exclusions. Core/fixture implementation did
not change, so the Stage 1 harness was not rerun for Task 12.

The public-export regression was run before the export addition:

```bash
uv run --locked --all-packages pytest tests/contracts/test_support_contracts.py::test_support_public_seams_retain_implemented_objects -q --tb=short
```

Observed red result: **1 failed**, with the fixed field-name diagnostic
`ResolvedInput` missing from `support.__all__`. After adding the required exports,
the documentation worker ran:

```bash
uv run --locked --all-packages pytest tests/contracts/test_support_contracts.py tests/contracts/test_data_dictionary.py packages/earnings-themes/tests/test_import_boundaries.py packages/earnings-themes/tests/support/test_metrics.py packages/earnings-themes/tests/support/test_safe_output.py tests/integration/test_support_wording.py -m "not live and not browser" -q --tb=short
uv run --locked ruff check packages/earnings-themes/src/earnings_themes/support/__init__.py tests/contracts/test_support_contracts.py
uv run --locked ruff format --check packages/earnings-themes/src/earnings_themes/support/__init__.py tests/contracts/test_support_contracts.py
```

Observed: **336 passed**, 1.51 seconds; Ruff check passed and both Python files
were already formatted. The regression checks that public seams retain the actual
implemented objects. Import checks cover ordinary imports without concrete adapters,
the six drafting modules' AST and fresh-interpreter boundaries, and detection of
planted forbidden support imports. Safe-output tests redact unknown values/map keys
and source-bearing exceptions/representations; feedback retains fixed reasons and
trusted field names. The support-only fixture wording leg passed. It does not
establish the full user-only wording gate.

The integration fixtures include **29 curated hard negatives**: 4 issuer, 13 period,
12 section cases, with their original partial-unit spans and curated fixture
provenance. They are fixture inputs, never extractor output. Invented cases exercise
positive, negation, competitor, prior-period, wrong-theme, context-only, contextual,
distributed and compound-partial routing; injected replies exercise unusable edits
and tool requests. These scripted cases verify machinery, not observed model accuracy.
No protected pilot text, signed gold, draft, working copy or view was read here.
GS13 remains binding through Stage 14's final test-gold drafting.

## V4: metadata and runner evidence; actual inference pending

[ADR 0005](../adr/0005-adopt-local-minicheck-for-support-signals.md) records the
upstream metadata/license sources, external configuration template, expected
inference-file hashes and the local verification boundary. The primary is
`lytang/MiniCheck-Flan-T5-Large` revision
`96eafd01cee2d16cf81aaa2fb226b14f422a37b3`; the explicitly selected alternative is
`MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` revision
`6f5cf0a2b59cabb106aca4c287eed12e357e90eb`. Neither is silently substituted.
The primary's upstream LFS weight checksum is
`41291881e13c6235ed47149cec903bee9493e45d9d7325587a9fa2e266c526c0`.
This is expected upstream metadata, not an observed checksum of acquired local weights.

The documented runtime pins are Python 3.14.0 arm64, Torch 2.14.1,
Transformers 5.18.0, SentencePiece 0.2.2, Tokenizers 0.23.2 and Safetensors 0.8.0.
The primary uses the native `.bin` checkpoint with explicit `weights_only=True`;
the alternative uses its native safetensors. Encoding/serialization, revisions,
file hashes, device, precision and limits participate in scorer identity/cache
bindings. The upstream cards mark artifacts MIT; acquisition-time weight/base-model
terms, intended use and locally hashed files still require user verification.
No weights or usable external primary configuration were supplied.

Task 11's offline adapter/import checks and runtime-import/tensor checks do not
prove real checkpoint inference. PyTorch warns that `torch.jit.script` is unsupported
on Python 3.14+; the adapter uses eager evaluation and `torch.inference_mode`.
Actual primary eager compatibility remains pending V4 rather than inferred from
mocked tests. The default sync subsequently removed the optional runtime.

The controller separately verified the macOS process network-denial mechanism:
loopback C curl baseline exit 0 versus sandbox exit 7; an unpatched child socket
connected at baseline and returned EPERM under the network-denied policy. That probe
was a runner check, not a primary model smoke. ADR 0005 gives the exact named V4
runner under `/usr/bin/sandbox-exec` with `(deny network*)`, offline environment
settings and local-only loading. No live/model/weight network call was made in this
Task 12 preparation. The primary named node has not run; the optional alternative
smoke was also not run and provides no primary evidence. Missing-weight/config skips
cannot discharge V4.

## Required human gates and downstream obligations

The following commands remain **unrun/unobserved** in the user's pilot-artifact
checkout. The controller first prepares that checkout with the branch's committed
support prompts and guard changes. Only the user runs these gates and reports
passed counts, or failing test IDs/fixed reasons/counts without source text or traces.

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs --tb=short
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py::test_no_stage_6_file_quotes_a_stage_1_fixture -q -rs --tb=short
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py::test_no_stage_6_file_quotes_a_pilot_document -q -rs --tb=short
```

Use no locals, verbose, debugger, or long/automatic/full traceback options. The
implementing/reviewing sessions remain blind. Passed observed human results are
required before completion; skipping or deferring them cannot replace the gate.
The final whole-branch review and its resolution are also pending.

Stage 9 receives explicit target assessment, raw views and quote contributions and
owns assignment decisions. Stage 10 receives the store/reader/consuming gate and
adds the first command, coverage/state mapping and export reverification. Stage 11
supplies at least 50 expert support labels, view/pooling choices, agreement-floor
preregistration, production judge selection, thresholds/V6, observed quality and
fresh-call bypass covering extraction, scorer and judge caches. Four panel trials
are bias diagnostics, not k-run stability evidence. Stage 13 adapts release context
to transcript speaker/section boundaries; Stage 15 owns concurrency/backfill.
Existing extraction-record, recovery, gold-drafting and other deferred obligations
remain open under their original triggers. This preparation closes none of them.
