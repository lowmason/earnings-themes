# Deductive coding: verified library behavior

Date: 2026-10-05. Branch: `codex/stage9-deductive-coding`.
Task 10 execution checkpoint: `94f3beb6547a841969a33875d57620c0c71d8e18`.
Final whole-branch code review: `e95a6b04eac5a1a8d205fdcd8874d89e959a7f13`.

The library boundary and its blind fixture checks are implemented. **Stage 9
completion remains unverified:** the user-only full-root and both Stage 6 wording
gates remain pending. Final whole-branch review is specification-conformant and
quality-approved, with no implementation findings. No stage tick, authoritative
completion stamp, plan retirement or branch integration is established here.
The shared system specification remains live.

## Implemented boundary

`earnings_themes.coding` exposes the actual existing record and transient classes,
not wrappers: coding schema/version, policy/ceilings, original `SupportSources`,
`CodingInput`, `ProposalRun`, `AssignmentPolicy`, `DecisionInput`, `DecisionSet`,
`Assignment`, `CodingRun`, and the proposal/attribute/novelty/decision/run parts.
It retains the previously public record helpers. Concrete `ClassifierBinding`,
`LocalAdapter`, `CodingCache`, and scripted classifier objects require explicit
module imports. Ordinary import creates no runtime, client or cache instance and
loads no optional model runtime, concrete local adapter or hosted provider.

| Seam | Verified library behavior |
| --- | --- |
| `resolve_coding_input(sources, doc_id, claim_id)` / `reverify_coding_input(input)` | Resolve every frozen theme through Stage 8, preserving the unchanged claim and every original document-qualified quote link, exact spans, masks, hierarchy and provenance. Examples stay unopened. |
| `propose_run(run_id, sources, claim_order, classifier, policy, ceilings, *, cache, started_at, software)` | Preflight metadata and all requested claims, preserve caller order, propose typed multi-label targets under explicit shared request/token ceilings and at most two attempts. No support or acceptance call is implicit. |
| `decide_assignments(proposals, support, sources, policy)` | Reverify source/support bindings and apply an explicit external pure policy only to eligible assessed targets. Missing/refused/incomplete/flagged assessment remains visible. No-policy assessed targets retain calibration-required review. |
| `project_assignments(decisions, support)` | Reverify saved decisions and current evidence, project accepted original quote–theme rows, and retain separate supporting claim links. Projection does not reproduce an external policy's vote. |
| `assignment_frame(rows, *, scope="production")` | Preserve typed empty frames; refuse duplicate grain/IDs, mixed codebook versions/hashes, and fixture-policy rows under default production scope. This structural frame check does not replace current-source reverification. |
| `write_coding_run(directory, result, sources, support, policy)` | Reverify before any output I/O; publish eight exact-schema Parquet tables and a manifest through a temporary sibling and rename; refuse existing destinations and clean failed partials. |
| `read_coding_run(directory)` | Validate confined published files, hashes, schemas, typed rows, references, original proposal identity and accounting. Current sources and external raw-cache bytes are not opened by this structural reader. |
| `reverify_coding_run(stored, sources, support, policy)` | Rebind current canonical evidence, codebook and policy; repeat the actual pure policy and compare saved decisions/assignments in canonical JSON bytes. Changed or absent policy refuses saved accepting results. No inference or reclassification occurs. |

The [data dictionary](../data-dictionary.md) documents every new model/enum field,
the reused source and transient dataclasses, nested nullable schemas and all eight
table grains. `load_codebook(path)` parses an explicitly supplied frozen artifact.
`validate_codebook(...)` needs discovery/example evidence and belongs upstream;
blind Stage 9 neither calls it on pilot artifacts nor dereferences those examples.

## Evidence, semantic decisions and version bindings

Core schema **2**, validator **`"3"`**, Stage 6 themes schema **1** and codebook v0,
extraction schema **1** / **`pointer-traversal/1`**, and support schema **1** /
**`semantic-support/1`** remain unchanged. Coding has its separate schema **1** /
**`deductive-coding/1`**. The Stage 7 claim serialization contract is copied
byte-for-byte into the coding contract test; producer claims remain codebook-free
and quotes remain pointer records without copied quote text.

Exactness checks preserve zero-based Python character offsets and half-open spans.
An invalid original quote link refuses the whole input, even when another link is
valid. Invalid candidates and bounded-attempt failures retain fixed audit reasons;
they cannot become unmatched classifications or accepted assignments. Exactness
does not establish thematic support. Evidence gates run before dispatch, before
publication, before decision/projection and at stored-run consumption. Existing
overlay masks remain audit references, not an implicit prevalence filter.

The classifier considers the complete approved definition snapshot, without an
example lookup, keyword shortlist, clipping or automatic ancestor assignment.
An ancestor/descendant proposal conflict is unusable and retried within the bound.
A valid explicit empty theme list alone creates pointer-only `no_theme_fit`
novelty. Sentiment, direction, topic and event type are nullable model-derived
annotations beside the unchanged claim; they cannot populate theme IDs or confer
importance or acceptance. There is no annotation-quality measurement here.

Stage 8's `assessed` is a processing result. Without a policy it becomes
`review/calibration_required`; missing assessment becomes
`review/missing_assessment` with null support status. An external accepting policy
can select only original quotes consistently labeled `supporting` by all four
complete family/presentation trials. Contextual, irrelevant, contradicting or
uncertain companions remain provenance and cannot enter accepted evidence.
Eligibility is necessary, never sufficient acceptance. No numeric cutoff,
pooling, majority rule or accepting package implementation is supplied.

Tests use an explicitly marked fixture policy for accepted-row mechanics.
Fixture rows/runs retain their provenance and require explicit fixture scope.
Calibrated references require a calibration artifact hash, but a typed reference
alone does not establish calibration, approval or production readiness.
Assignment grain is
`(coding_run_id, codebook_id, codebook_version, doc_id, theme_id, quote_id)`:
two themes share one unchanged quote ID in separate rows; several supporting
claims link to one row; identical quote IDs in different documents stay distinct.
Empty accepted output establishes neither no themes nor a perfect exactness rate.

The stored tables are `classifications`, `attempts`, `proposals`, `attributes`,
`decisions`, `assignments`, `assignment_claims` and `novelty`. Null policy,
missing support status, nullable annotation fields and nullable calibration
inside a nonnull fixture policy survive Parquet round trips. The original
proposal manifest/hash is reconstructed without substituting publication hashes.
External raw-reference/hash bindings remain provenance; readers do not claim to
verify bytes they do not open. Sequential publication establishes no coordinated
concurrent-writer guarantee.

## Observed blind verification

All commands below ran from the repository root with the installed reviewed
environment. The writable UV cache and `--locked --offline --no-sync` avoided
dependency resolution/downloads. Audits found no nearer instructions or configured
type checker. Root Ruff excludes Markdown and respects Git-ignored data, caches
and environments. Selected test readers use invented temporary records, permitted
Stage 1 canonical fixtures, source/test code and prompts. The v0 replay loads only
the frozen codebook artifact and forbids discovery/example resolution. No root
pytest or Stage 6 wording node ran in this session.

Public-export RED before initializer changes:

```bash
UV_CACHE_DIR=/private/tmp/earnings-stage9-uv uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_coding_contracts.py -q --tb=short
```

Observed **1 failed, 4 passed in 0.16s**, expected absent public `CodingSubject`.
After minimal exports, the same command passed **5 tests in 0.15s** with no
warnings. The dictionary RED before adding field/grain tables was **6 failed,
239 passed in 0.34s**; after documentation, **245 passed in 0.28s**. Expanded
contracts/dictionary then passed **266 tests in 0.31s**. An intermediate invented
fixture used a string instead of strict `ReviewStatus`; correcting only that
fixture resolved its three setup failures.

Final scoped commands:

```bash
UV_CACHE_DIR=/private/tmp/earnings-stage9-uv uv run --locked --offline --no-sync --all-packages ruff check .
UV_CACHE_DIR=/private/tmp/earnings-stage9-uv uv run --locked --offline --no-sync --all-packages ruff format --check .
UV_CACHE_DIR=/private/tmp/earnings-stage9-uv uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/support packages/earnings-themes/tests/test_extraction_records.py packages/earnings-themes/tests/test_extraction_injection.py packages/earnings-themes/tests/test_extraction_local.py -m 'not live and not browser' -q --tb=short
UV_CACHE_DIR=/private/tmp/earnings-stage9-uv uv run --locked --offline --no-sync --all-packages pytest packages/earnings-themes/tests/coding tests/contracts/test_coding_contracts.py tests/contracts/test_support_contracts.py tests/contracts/test_data_dictionary.py packages/earnings-themes/tests/test_import_boundaries.py tests/integration/test_coding_frozen_v0.py tests/integration/test_coding_wording.py tests/integration/test_support_wording.py -m 'not live and not browser' -q --tb=short
```

Ruff check: **All checks passed**. Format check: **385 files already formatted**.
Sequential upstream suite: **700 passed, 2 deselected, 1 warning in 9.81s**,
exit 0. Both deselections are explicit live scorer smokes. The existing optional
PyTorch softmax test emits a Python 3.14 `torch.jit.script` FutureWarning recommending
`torch.compile` or `torch.export`; it was recorded without an unrelated patch.
Sequential coding/contract/import/v0/wording suite: **1110 passed in 54.39s**,
exit 0, no warnings. Both final pytest processes completed sequentially before
this record was finalized. `git diff --check` also passed with exit 0.

Operational deviation: the first coding suite (**1110 passed in 54.10s**, no
warnings) briefly overlapped a separately launched upstream test process
(**700 passed, 2 deselected, 1 warning in 9.11s**). Both finished before the final
upstream/coding reruns, which run sequentially. No concurrent runtime workers were
introduced. This is a disclosed test-runner deviation, not a concurrency claim.

The synthetic and frozen-v0 checks establish typed multi-label/retry/replay,
novelty, shared quote identity, mixed-version refusal, contribution restrictions,
immutable storage, closed injection behavior and import/blinding boundaries.
Frozen v0 is `djia-pilot`, version `0`, hash
`635975d1ec952cf5719ea3b473870f96e7e3a52bc3015cc1ac5725aa80ec1e79`, 22 themes,
four with parents. That is metadata exercised against invented evidence, not a
revalidation of discovery/example passages. Classifier/scorer/judge behavior uses
scripted callbacks or raw fixture replay. **Zero real model, hosted or billable
inference calls and zero model downloads** occurred in this task. Scripted
request/token-accounting assertions are not observed production usage or quality.
Planning baseline counts are not Stage 9 implementation acceptance evidence.

The controller independently ran the same scoped selections sequentially:
**1110 passed in 51.35s**, exit 0, no warnings; then **700 passed, 2 live
deselected, 1 existing Torch FutureWarning in 7.78s**, exit 0. Root Ruff passed,
**385 files** were already formatted, and the diff whitespace check passed.
The final reviewer checked the entire ten-task branch from
`2bd535f5993b922ddd11b1995c015628a0361a21` through
`e95a6b04eac5a1a8d205fdcd8874d89e959a7f13`, the complete plan, contracts,
reported checks and cross-task gates. Its verdict was specification-conformant
and quality-approved, with no Critical, Important or new Minor implementation
findings. Merge readiness remains conditional on the user-only gates and
controller completion work. The reviewer opened no protected artifacts and
ran no tests or inference. The separate Codex CLI review was skipped under
the review skill's same-model-family rule because the controller is Codex;
no completed Codex second-opinion review is claimed.

## Pending completion gates and downstream ownership

| Gate | Current status |
| --- | --- |
| Final whole-branch specification and code-quality review | Approved at the code revision above; no implementation findings |
| Full root default suite (`packages apps tests`) | Pending user-only result; unverified |
| `test_stage6_wording.py::test_no_stage_6_file_quotes_a_stage_1_fixture` | Pending user-only result; unverified |
| `test_stage6_wording.py::test_no_stage_6_file_quotes_a_pilot_document` | Pending user-only result; unverified |
| Roadmap tick, authoritative stamp, reconciliation, retirement and integration | Pending controller after required gates resolve |

User gate reports must contain only counts, test IDs and fixed reasons. An absent
gate is unverified, never passing. GS13 remains binding through Stage 14's final
test-gold drafting: this implementation opens no pilot text, signed gold, drafts,
working copies/views, protected data or example evidence; drafting sessions still
receive no coding, extraction or support code/prompts/outputs.

Stage 10 owns the first extraction command, Stage 5 processing/coverage mapping,
prevalence denominators, parent/family roll-ups and cited export with current
evidence checks. Stage 11 owns first pilot extraction/coding, expert support labels,
calibration artifacts, production model/policy and thresholds, view/pooling choices,
agreement floors/V6 and fresh-call stability with bypass across extraction,
classifier, scorer and judge caches. Stage 12 owns human novelty adjudication and
reviewed new versions. Transcript adaptation stays with Stage 13, test gold with
Stage 14, concurrent workers and store/cache hardening with Stage 15, and any
separately authorized hosted ceiling with Stage 16.

No pilot coding, calibration, production model/policy, observed coding quality,
annotation quality, agreement floor or fresh-call stability was established.
No CLI, acquisition, source download, Stage 5 state write, model selection,
codebook discovery/change, new framework or later-stage implementation was added.
