# Semantic support: verified Stage 8 implementation

Date: 2026-10-05. Branch: `codex/stage8-semantic-support`.
Execution base: `5463a44c311a91fd4ef363f5bed63273f40f2898`.
Implementation checkpoint checked by the controller: `5eeb28ba79bfdf78cf96cde5211154cfc270fdf9`.
Task 12 documentation/public-export preparation starts at that checkpoint.

**Stage 8 is complete (2026-10-05).** The actual pinned primary inference smoke
passed under process-wide network denial, and the user reported passing results
for the complete root default suite and both full Stage 6 wording nodes at prepared
head `46eda6d263c7d23f01f4719cc81f38ed6121e948`. The final GPT-6.1 Max whole-branch
review, both scoped fix reviews, and verification-document review cleared all
findings. Plan 13 records completion and retirement; branch integration remains
the user's choice. This record establishes no pilot quality, agreement, or
fresh-call stability result.

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

## Final review fixes and independent checks

The GPT-6.1 Max reviewer examined the full branch from `5463a44` through
`8d97c57`. Two Important findings were fixed in `ec15c2b`: cached scorer usage
IDs now distinguish target/quote/scope while preserving raw score reuse, and bound
judge callbacks abort safely on unexpected failures rather than retrying them as
availability failures. The scoped review found one further Important exception-chain
issue, fixed in `e2cb007` with preserved safe diagnostics and suppressed chains.
The second scoped review marked it addressed and reported no new findings.

Invented-input regressions demonstrated 10 expected failures before the first fix,
then 11 passing cases, covering repeated text at separate exact spans through live
and replay publication/consumption, one-quote aliasing, and bound callback crashes.
Four further chain-suppression regressions failed before the amendment and passed
afterward, covering both callbacks with explicit causes and implicit context.
The worker's final affected checks returned 679 passed, 1 optional-runtime skip,
2 deselected. No live smoke or protected artifact reader ran.

The controller independently ran these checks at `ec15c2b`:

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_assess.py packages/earnings-themes/tests/support/test_judges.py packages/earnings-themes/tests/support/test_store.py packages/earnings-themes/tests/support/test_run.py packages/earnings-themes/tests/support/test_safe_output.py packages/earnings-themes/tests/support/test_cache.py -m "not live and not browser" -q --tb=short
uv run --locked --all-packages pytest packages/earnings-core/tests packages/earnings-themes/tests tests/contracts tests/integration/test_support_fixtures.py tests/integration/test_support_wording.py -m "not live and not browser" -q --tb=short
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked --all-packages pytest packages apps tests --ignore=tests/integration/test_stage6_records.py --ignore=tests/integration/test_stage6_wording.py --ignore=tests/integration/test_stage6_pilot_v1.py -m "not live and not browser" -q -rs --tb=short
```

Observed: 272 focused tests passed; 1358 affected tests passed, 1 optional-runtime
skip, 4 deselected in 43.01 seconds; Ruff check passed and 355 files were already
formatted; the broad blind subset returned 2628 passed, 5 skipped, 27 deselected
in 91.06 seconds. Its exclusions and skips have the same reasons recorded above.
It remains a subset result, never a complete root-suite result.

After the exception-chain amendment at `e2cb007`, the controller independently ran:

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_judges.py packages/earnings-themes/tests/support/test_assess.py packages/earnings-themes/tests/support/test_run.py packages/earnings-themes/tests/support/test_safe_output.py packages/earnings-themes/tests/test_import_boundaries.py tests/integration/test_support_wording.py -m "not live and not browser" -q --tb=short
```

Observed: 164 passed in 3.63 seconds. The amended callback behavior, safe errors,
import boundaries and support-only fixture wording gate passed. These results do
not discharge V4 or any user-only gate.

## V4: observed primary inference and identity

[ADR 0005](../adr/0005-adopt-local-minicheck-for-support-signals.md) records
the immutable revision, all eight upstream inference-file hashes, runtime pins,
weight terms, external configuration and runner. The controller matched all eight
supplied local file hashes to that manifest and observed the user’s confirmation
of applicable model/base-model weight terms for research use on 2026-10-05. The
external config SHA-256 is
`99bbbffafe16d3a92574eb8e1a6fed8b22e443533b1dad6fc3187f9797752ba6`.
No local checkpoint path, config content, request, reply or rationale is published.

The actual primary is `lytang/MiniCheck-Flan-T5-Large`, revision
`96eafd01cee2d16cf81aaa2fb226b14f422a37b3`. Its locally matched native `.bin`
weight SHA-256 is
`41291881e13c6235ed47149cec903bee9493e45d9d7325587a9fa2e266c526c0`.
The run used Python 3.14.0 arm64, Torch 2.14.1, Transformers 5.18.0,
SentencePiece 0.2.2, Tokenizers 0.23.2 and Safetensors 0.8.0; CPU float32;
complete input limit 512; `minicheck-first-step/1`; and logit mapping `[3,209]`.
Native checkpoint loading used `weights_only=True`, local-only files, and
disabled remote/custom code.

With `EARNINGS_SUPPORT_PRIMARY_CONFIG` supplied externally, the controller ran:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /usr/bin/sandbox-exec \
  -p '(version 1) (allow default) (deny network*)' \
  uv run --offline --locked --all-packages --extra support-nli pytest \
  packages/earnings-themes/tests/support/test_nli_live.py::test_minicheck_local_primary \
  -m live -q -rs --tb=short
```

Observed on 2026-10-05: **1 passed, 0 skipped in 12.84 seconds**. Actual primary
inference on invented text produced a finite signal, counted complete input,
verified checkpoint/runtime identity and bound that identity through a synthetic
support-run manifest. Socket trip count was zero. The process ran under macOS
`/usr/bin/sandbox-exec` with `(deny network*)`, in addition to both offline
environment settings. Earlier independent runner probes observed C curl baseline
exit 0 versus sandbox exit 7, and an unpatched child socket connected at baseline
versus EPERM under that policy. Python patches alone were never the denial claim.
No API inference or weight acquisition occurred in this gate.

An earlier user attempt with no supplied config visibly returned **1 skipped in
0.01 seconds**; it did not satisfy V4. The later actual passed result discharges
the primary gate. The explicit DeBERTa alternative remains wired and mocked, but
its optional real-checkpoint smoke was not run; it supplies no primary evidence.
No MPS execution or model-quality comparison was observed. The earlier PyTorch
JIT FutureWarning remains a runtime limitation for JIT use on Python 3.14+; the
actual primary eager path passed. This smoke establishes compatibility of this
configured path, not semantic accuracy, calibration, or general platform coverage.

## Observed user-only gates and downstream obligations

The controller prepared 51 committed branch files at `46eda6d` in the user’s
pilot-artifact checkout, preserving the user’s roadmap reconciliation. All copied
file hashes still matched the prepared branch when the results were recorded.
The user ran these commands and reported safe counts only:

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q -rs --tb=short
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py::test_no_stage_6_file_quotes_a_stage_1_fixture -q -rs --tb=short
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py::test_no_stage_6_file_quotes_a_pilot_document -q -rs --tb=short
```

Observed on 2026-10-05: the **full root default suite passed 2651 tests, with
2 skipped and 27 deselected in 108.67 seconds**. The skips were optional runtime
absence and the already-recorded first acquisition. The explicit full fixture
wording node passed **1 test in 0.19 seconds**; the explicit pilot wording node
passed **1 test in 0.61 seconds**. These results supplement the blind subset and
support-only fixture checks above. Implementing/reviewing sessions stayed blind;
no protected artifact was opened to record or verify this documentation. All
required completion gates are observed, and no Stage 8 work is deferred.

Stage 9 receives explicit target assessment, raw views and quote contributions and
owns assignment decisions. Stage 10 receives the store/reader/consuming gate and
adds the first command, coverage/state mapping and export reverification. Stage 11
supplies at least 50 expert support labels, view/pooling choices, agreement-floor
preregistration, production judge selection, thresholds/V6, observed quality and
fresh-call bypass covering extraction, scorer and judge caches. Four panel trials
are bias diagnostics, not k-run stability evidence. Stage 13 adapts release context
to transcript speaker/section boundaries; Stage 15 owns concurrency/backfill.
Existing extraction-record, recovery, gold-drafting and other deferred obligations
remain open under their original triggers. Plan 13 closes none of those unrelated items.


## Documentation-completion verification

The completion worker changed documentation only, then ran the blind checks:

```bash
uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py tests/contracts/test_support_contracts.py packages/earnings-themes/tests/test_import_boundaries.py tests/integration/test_support_wording.py -m 'not live and not browser' -q --tb=short
```

Observed: **230 passed in 1.35 seconds**. The full root, full Stage 6 wording and
real inference gates were not repeated by this worker; their observed results
above remain the completion evidence. Backlog statistics independently returned
48 open, 33 ever closed, 41% closure, no items aged >45 days, oldest 10 days, and
all 48 in the 0–14-day band. The local read-only triage covers every open item;
no disposition was executed and no earlier item or grouped partial obligation was
closed. No Stage 8 item was deferred.
