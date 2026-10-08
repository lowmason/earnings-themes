# Stage 10 fixture vertical slice verification

## Historical documentation and implementation checkpoints

The following record preserves the earlier pending states, failures, skips and deviations as history; the current completion reconciliation is appended below.

Documentation checkpoint, 2026-10-07. Stage 10 implementation has fixture V8/V10
proof; overall completion remains pending. Task 11 specification and quality were
approved at `25d71813041b7e5b5f2ee7345fc0da533502517b`. This Task 12 documentation
phase starts at `9345bdbf23c6f3a894cbecea4b4819cc79be5bf2` and awaits its own fresh
review. Final whole-branch and independent second-opinion reviews, human-only
root/both Stage 6 wording gates and observed/disposed V5 remain controller-owned.
No Stage 10 stamp, roadmap tick, plan retirement or integration is asserted.

The machinery uses saved permitted synthetic acquisition inputs and scripted
invented replies, then refusing replay transports. No pilot document, signed gold,
draft, protected view or codebook example is read; no SEC request, source fetch,
model call, model download or billable inference runs. Frozen-v0 tests read
metadata/rules with example resolution explicitly refused. Fixture declarations
are predetermined processing adjudications, never pipeline-derived evaluation gold.

## V8: actual replay CLI and current consumers

`tests/integration/test_theme_vertical_slice.py::test_v8_raw_fixture_to_cited_report`
replays the public saved-response acquisition path, checks all 80 saved transition
records, validates the canonical artifact through the public decoder, and invokes
`earnings-pipeline extract run --config PATH` on fully prepared confined temporary
material. The checked-in `tests/fixtures/themes/stage10/replay-config.json` is a
template filled by `tests/integration/stage10_cases.py`, not directly runnable.
Its fixture clock, hashes, identities, ceilings and exact stage/cache lineage are
explicit. The workflow receipt independently records actual operational UTC;
replay does not establish deterministic fresh model calls.

V8 publishes fourteen typed analytical tables and schema-2 processing, with one
exact quote, two themes, two original claim-evidence links and four
assignment-claim links. Public support/coding/analysis readers and current gates
reverify after publication. Nonempty retained-quote exactness is 1.0; empty quote
results have null exactness, not a perfect rate. Assertions cover exact CP span,
actual canonical highlight occurrence, source and saved snapshot citations,
unchanged selected input hashes, fixture scope and zero CLI dispatch/token-count
calls. Release roles remain not_applicable; no transcript claim is inferred.

The same file separately exercises replay cache miss, unexpected extraction abort
with unreported usage, empty replies without no-theme declaration, publication
failure/retry, state-pending retry, local-only export withholding and absent-browser
canonical fallback. These outcomes establish missingness and immutable retry
behavior on invented inputs, not model quality or native browser behavior.

## V10: independent declared population and counting arithmetic

`tests/integration/test_theme_coverage.py::test_v10_declared_matrix_counts_and_restrictions`
uses the ten-event declared hand matrix with predetermined status/reason/declaration
metadata. Ten expected release slots include seven available/parsed and three
observable cases. All ten transcript slots have no document identity, are
unobservable with transcript_not_in_scope, and have null rates/empty_denominator.

| View / unit | Numerator | Denominator | Rate |
| --- | ---: | ---: | ---: |
| Q1 direct child / issuer_period | 1 | 2 | 0.5 |
| Q1 parent self-or-descendant / issuer_period | 1 | 2 | 0.5 |
| Q2 parent self-or-descendant / issuer_period | 0 | 1 | 0 |
| Parent presence / issuer_window | 1 | 2 | 0.5 |
| Parent descriptive / firm_quarter | 1 | 3 | 1/3 |
| Parent / equal_issuer_mean | 0.5 | 2 | 0.25 |
| Each of two overlapping families / issuer_window | 1 | 2 | 0.5 |

Each issuer-period contributes at most once. Equal-issuer mean first computes each
issuer's observed-period fraction, then averages once per issuer; its numerator is
the sum of those fractions. Expected/available/observable/excluded counts and
missing-period restrictions accompany the rates. Direct, parent and family rows
stay separate. Current masks exclude headline evidence but retain audit rows;
copies, extra exact evidence and original claim links cannot inflate issuer votes.
Frozen child assignments survive parent roll-up and no mapping creates a theme.

Safe companion IDs are
`tests/integration/test_theme_coverage.py::test_v10_evidence_claim_and_copy_inflation_preserves_issuer_votes`
and
`tests/integration/test_theme_frozen_v0.py::test_frozen_child_direct_assignment_parent_rollup`.
The independent frozen acquisition baseline has 27 release slots: 24 parsed,
two unavailable and one failed. Its invented processing check uses denominator
24; that acquisition population is distinct from the ten-event V10 matrix and
from the restricted V8 selection. Missing/unmatched/review/failed/empty outcomes
never silently become no-theme. No full-DJIA or pilot prevalence is established.

## Shipped interfaces and compatibility

Actual public signatures are documented in the
[data dictionary](../data-dictionary.md#stage-10-documentation-checkpoint-and-compatibility):
`load_workflow_config(path: Path, *, repo: Path) -> WorkflowConfig`;
`run_theme_workflow(config: WorkflowConfig, runtime: WorkflowRuntime, *, now: Callable[[], datetime]) -> WorkflowResult`;
`write_analysis_run(directory, result, inputs, policy, families, evidence) -> Path`;
`read_analysis_run(directory: Path) -> StoredAnalysisRun`;
`reverify_analysis_run(stored, inputs, policy, families) -> None`;
`write_theme_report(directory, stored, inputs, policy, families, views, *, audience) -> Path`;
and `make_evidence_view(bound, doc_id, quote_id, *, audience, raw_snapshot) -> EvidenceView`.
All publication inputs are required; raw_snapshot and audience are required
keywords. EvidenceView requires the explicit retain_capture bool. Structural read
or assessed/cache-hit status grants no acceptance or current validity.

C1 supplies explicit raw bytes; C2 supplies canonical JSON bytes and current
projection/hash authorization, with required selected_universe_hash equal to the
selected operative universe identity. Older arbitrary/C2 provenance and caches
must be legitimately regenerated, never relabeled. Core schema 2 and canonical CP
coordinates remain unchanged. Valid schema-1 partial/null missingness survives;
malformed schema-2 partial/null/unknown/processing_failed missingness refuses.

Analysis binds its parsed acquisition baseline; receipts separately bind appended
current processing bytes. Same-workflow pending/recorded retry checks actual
analysis bytes, all completions and the immediate immutable predecessor against
current inputs. Other-workflow completed reuse requires explicit paired analysis
directory/run.json SHA, all selected stored stages and current history/policies.
There is no latest discovery, general terminal reopening or concurrency proof.

Fixture policy requires explicit allowlisted authorization/hash bindings; policy
null retains calibration review, and no calibrated CLI implementation is registered.
Local/export rights are rechecked, including nested canonical artifact references.
Rights-denied raw inclusion records snapshot_withheld; absent required retainable
raw bytes refuse complete publication. Text-denied views have no private bytes or
links. Static escaped views mark saved CP slices; UTF-16 exists only at the browser
boundary and never verifies quotes. Captures/screenshots are local_only and report
inputs do not supply a durable capture or native-highlight observation.

## Safe checks and evidence provenance

From the explicit checkout with the reviewed environment already installed:

```bash
POLARS_MAX_THREADS=2 UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py contracts
POLARS_MAX_THREADS=2 UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py vertical
POLARS_MAX_THREADS=2 UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py stage10
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync ruff check packages apps tests tools
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync ruff format --check packages apps tests tools
```

Each runtime is fully awaited before another starts. The captured-output runner
prints safe counts/IDs/fixed reasons, disables external pytest plugin autoloading
and explicitly loads the reviewed pytest_asyncio plugin. Its 72-file stage10 union
has a bounded 900-second deadline; all individual groups retain 300. The
approved human-only root-user deadline is 1800 seconds; wording and browser
modes retain 300. The pure selector does not admit additional groups or options.
The runner cannot authorize a protected reader. Agents never invoke root/Stage 6
wording/browser/user-only modes or raw-output diagnostics. No type checker is
configured. Task 12 source-only preflight confirms all 253 audited source/helper
SHA-256s match Task 11's 72-node audit, with unchanged imports/reader references.

Task 11's recorded covering results: vertical 21, coverage 59, contracts 547,
producer repair 73, upstream 1,684 with one optional-runtime skip, runner 16,
dictionary 315, final permitted Stage 10 wording 1; all other final counters zero.
The final union passed 2,736 with one optional-runtime skip and no warnings or
failures. Ruff lint had zero findings, format checked 368 files and diff-check
passed. These are predecessor results, not newly inferred executions. The selected
installed numerical-runtime test can check already installed libraries and softmax
on an invented tensor; it loads no model/weights and authorizes no installation.
The observed skip proves neither installed-library execution nor a full environment
inventory. Task 12's fresh results are recorded below.

## Recorded deviations and unresolved limits

Historical ignored Task 1–6 reports were reconstructed from durable/human
checkpoints after loss, not restored originals. Later reports preserve the actual
RED/GREEN/setup evidence. Task 7 required approved available fallback/raw-withholding
and explicit capture-permission contract dispositions; nested rights remain binding.
Task 8 accidentally overlapped two export runs; interruption exposed runner/stdlib
frames without test/source content. Those provisional results were superseded by
sequential covering checks and a deterministic metadata-only interruption repair.
Its earlier POLARS_MAX_THREADS=2 setting preceded the conditioned authorization;
no timeout/oversubscription root cause is claimed. Later rounds explicitly approve
that ephemeral limit without persistent configuration change.

Task 9 distinguished fixture setup/probe failures from behavioral TDD, corrected
public document grammar and narrow schema-2 missingness, and obtained approved
baseline/current-state/stored-analysis dispositions. Review repairs confined all
selected/deterministic children before reads, skipped fully withheld optional
capture, and normalized capture resource-type JSON to the unchanged public boundary.
Temporary probes were removed. Large/untyped orchestration remains a nonblocking
controller-triage finding, not a resolved item or new deferral.

Task 10's three lifecycle/isolation repairs used a human-approved broader crash
category exception; only the URL read was an uncaught crash. The first amendment
followed implementation; the second retains it and completes redirect refusal
within the same approved loopback isolation repair. No pin, comparison metric/input
or capture-policy semantics changed. The protocol was written after fake checks
and adapter edits, before any actual browser observation; that historical ordering
fact is retained, not retroactively corrected.

Task 11 initially observed 349 legacy invented-producer failures. Its four-path
test-only repair supplied valid IDs/windows/visits/counters without changing spans,
interpretations, original links, validators, source/gold or codebook; curated Stage 1
IDs remain mapped. The original combined 300-second runner timeout had all-zero
placeholder counters, not successful test outcomes. A synthetic RED/GREEN routing
regression preceded the stage10-only 900-second disposition and successful union.
One invented-only manual ValidationError frame escaped before fully caught metadata
handling; the probe was removed. Its approximately 380-line seed_case and variable
tuple return remain nonblocking controller-triage findings.

Task 12's first source-only audit summary treated the audit's integer selected-file
count as a list and exposed a stdlib TypeError frame without protected/source data.
The corrected audit fully catches errors and emits only fixed/count metadata;
all 253 current hashes matched. This was a preflight script error, not a test failure
or behavioral RED. No prose-only busy-work test was added.

V5 native/capture/manual fallback is pending under the
[separate observation protocol](stage10-browser.md). Target is Chrome for Testing
154.0.8037.57/mac-arm64 plus matching driver under ISOLATED_1. The six-case invented
local_file bundle hash is
70f13f640e1ee84fa9372d19256c2873cb8c4ff188b7450dd4522c61c1c83129;
its prepared index is /private/tmp/earnings-stage10-v5/v1/index.html. Prepared static
artifacts, fake renderers and absent-browser fallback prove no installed target,
native highlighting, capture or manually visible fallback. External HTTPS remains
unverified; lifecycle approval is no V5 completion waiver. Protected ignored-byte
equality is unverified. No protected input was copied/read to improve it. Human
full-root and both Stage 6 wording gates must be observed at the final reviewed
implementation HEAD; Stage 9 results do not discharge Stage 10 gates. Stage 11 owns
first pilot extraction, expert labels/calibration and all-four-cache fresh-call
stability; subsequent taxonomy/transcript/configuration/full-cohort/hosted work
retains its original stages and routes.


## Task 12 fresh documentation-phase results

All commands above ran sequentially in the explicit managed checkout, offline,
locked/no-sync with the fixed temporary cache; test commands used the approved
POLARS_MAX_THREADS=2. Initial contracts: 547 passed/1 failed, fixed test_failed,
only test_data_dictionary.py::test_analysis_final_validation_gate_is_documented.
Its source isolates a tested exact Task 8 ownership phrase removed by the prose
refresh. Restoring that phrase while stating the path is implemented corrected it;
no test/registry/runtime changed. Rerun contracts: 548 passed, all other counters
zero. Vertical: 21 passed, all other counters zero. Stage10: 2,736 passed/1 optional
runtime skip, all other counters zero. Each final group exited zero with reason
null. Ruff lint exited zero with zero findings; Ruff format-check exited zero with
368 files already formatted. Ruff child output was captured, with only static
codes/counts emitted. Diff-check passes; only the four assigned documentation
paths changed. No type checker, native/human gate or live extraction ran. This
result-only record awaits fresh task review and does not establish Stage 10 completion.


## Task 12 approved root-only deadline repair

At the previously reviewed `cb1cda84be1e2b4387641e2744af2d37d7468b51`, the human
invoked the complete root-user command and received `runner_timeout` at its
inherited 300-second bound. All-zero counters and empty IDs are timeout
placeholders, not evidence of zero tests executed or successful tests. No failing
or stalled test was isolated. The active-primary-VIRTUAL_ENV warning described
uv choosing the worktree environment; it was not a pytest warning. No successful
full-root runtime duration is inferred.

The narrowly approved repair changes only the fixed root-user bound to 1800
seconds. The stage10 bound stays 900; every other group stays 300; run_checks
retains its default 300 and signature. Root nodes remain packages/apps/tests with
marker `not live and not browser` and explicit `--user-only` admission. The
captured-output boundary, exact allowlists, plugin/hash-safe diagnostics, closed
reasons, unknown-option refusal and absence of automatic retries are unchanged.

The source-only preflight matched all 253 prior audited hashes at dispatch HEAD
`0938af8ba44c316f2360134ae8782e2f1a9dd17a`. The full captured runner group ran
sequentially with the same locked/offline/no-sync command and approved temporary
cache/POLARS_MAX_THREADS=2: RED 16 passed/1 failed, with only
`tests/contracts/test_stage10_check_runner.py::test_full_root_deadline_is_fixed_without_dispatching_human_modes`
and reason test_failed; GREEN 17 passed, all other counters zero, IDs empty and
reason null. The regression discriminates inherited 300 from approved 1800,
requires the pure selector, checks every fixed deadline, unchanged default and
root node/marker metadata, and inspects both dispatch paths without invoking
root or wording modes. Existing invented stage10/coverage stubs verify dispatch;
the browser stub explicitly expects its unchanged 300 seconds.

Scoped Ruff lint and format-check for tools/stage10_checks.py and
tests/contracts/test_stage10_check_runner.py passed, and git diff-check passed.
No unchanged domain suite was repeated. Actual human root/both Stage 6 wording
and V5 evidence at the later reviewed implementation HEAD remain pending;
prior whole-branch approvals cover cb1cda8, not this new source. The controller
owns fresh scoped reviews and subsequent gates; this repair asserts no Stage 10
completion.


## Task 12 synthetic event CLI refusal-contract repair

At clean BASE `7b65a77d75bdd549d8809d73963b208e0e0352a8`, the human's
full-root guarded run reported 4,239 passed, one failed, nine skipped and 28
deselected, with zero collection failures or pytest warnings. Its sole safe
failure ID was
`apps/earnings-pipeline/tests/test_events_cli.py::test_acquire_refuses_a_run_file_it_cannot_read`,
with reason `test_failed`. No process exit or current-run duration was supplied;
the shell prompt's preceding duration does not establish this run's timing. The
full-root human gate remains failed; skips and deselections are not passes. The
VIRTUAL_ENV warning concerns uv's worktree environment choice, not pytest warnings.

Source investigation identifies a legacy synthetic assertion mismatch. The
Stage 10 state reader deliberately emits the closed `state_storage_corrupt`
reason for malformed acquisition Parquet, and the acquisition preflight refuses
before opening the SEC client. The old test expected a filename-bearing message.
Production behavior remains unchanged. The repaired test passes invented
`b"not parquet"` to the real state reader, requires exact stderr
`Refused: state_storage_corrupt\n`, and retains exit 1 and an empty client-budget
list. Explicit safe `plain` and `diagnostic-sentinel` parameter IDs cover the
original filename and a wholly invented sentinel filename with the same refusal.
No parser, reader or CLI stub replaces that path.

The implementer's pre-mutation guarded exact-node RED reported zero passed and
one failed, all other counters zero, the same sole safe ID and reason
`test_failed`; the fully awaited child exit was 1. After repair, the exact covering
selection comprised that node's two parameters,
`test_acquire_refuses_while_another_run_holds_its_runs`, and
`test_acquire_needs_the_approved_count_when_it_would_fetch`. GREEN reported four
passed, all other counters zero, empty failure IDs, reason null and child exit 0.
Both runs used locked/offline/no-sync all-packages Python, the fixed temporary
cache, POLARS_MAX_THREADS=2 and the captured `run_checks` boundary with timeout
300 and marker `not live and not browser`. Selected nodes, helpers, application
autouse lock isolation and relevant acquisition/reader paths were source-audited;
fixture copies and invented data directories stay in pytest temporary roots, and
the client helper uses MockTransport. The prior 253-file audit is supporting
provenance: 251 hashes remain equal, with the two approved root-deadline repair
paths accounting for its differences. No protected reader was authorized by
that earlier audit.

Scoped locked/offline/no-sync Ruff lint and format-check of the modified Python
test passed, as did git diff-check. Their subprocess output was captured and
only closed status/count metadata reported. No unchanged domain suite, root,
Stage 6 wording, actual browser/SDK/install inventory, live request or model call
ran. Safe RED/GREEN/static records and the detailed implementer report are kept
in the ignored task directory; these are fresh scoped results, not full-root
success or Stage 10 completion.

Fresh sequential scoped reviews, a new human full-root gate, both Stage 6 wording
gates and observed/disposed V5 remain pending at the final reviewed HEAD. Earlier
approvals apply to their recorded ranges. Historical timeout evidence and the
existing deviations/controller-triage findings above remain unchanged. Screenshots
remain unopened and local_only; ignored-byte equality remains unverified. No
stamp, deferred disposition, plan retirement, integration or cleanup is asserted.

## Completion reconciliation — 2026-10-08

Stage 10 technical implementation and human completion gates are satisfied; its shared Rollout stamp and roadmap tick are recorded and only plan 15 is retired. The new completion documentation delta awaits sequential scoped controller review. Integration selection, branch/worktree cleanup and final controller report remain pending. The original checkpoint sections above are historical, including their pending-gate wording.

Both sequential independent whole-branch seats approved `7d9b2cb7d989a769ae1429afe8d3f3b1d180dea4` → `cb1cda84be1e2b4387641e2744af2d37d7468b51`; both scoped seats approved the root-timeout delta `cb1cda84be1e2b4387641e2744af2d37d7468b51` → `7b65a77d75bdd549d8809d73963b208e0e0352a8` and the refusal-test delta `7b65a77d75bdd549d8809d73963b208e0e0352a8` → `611f84a564ed9bfd4a52cf6682bf2c6a88676a23`. No Critical/Important finding remains in those ranges. Human root at the latter HEAD: 4241 passed, 9 skipped, 28 deselected; fixture wording and exact-HEAD-guarded pilot helper: 1 passed each, no skips. Zero failures/collection failures/warnings, empty safe IDs and null reasons. Root exit and elapsed time were not supplied. Binding for subsequent human reports uses the continuous same-checkout metadata and helper guard, rather than a separately repasted SHA.

V5 native/manual gate is observed on 2026-10-08: pinned Chrome target available/used; five highlighted and drift not_highlighted; all six independent canonical fallbacks span_visible, repeated second occurrence; plain control opened with two unhighlighted items. Capture command skipped once with cause unspecified, actual screenshot capture unverified; local-file results do not establish HTTPS or automatic long-page scrolling. Original scenario order/status vocabulary, 23 freeze inputs and two approved amendments are retained.


Resolve-before-defer: both final seats classify the orchestration/helper-typing M1 and variable fixture tuple M2 as nonblocking maintenance, now P15-M1/P15-M2 (Size: plan) with explicit triggers and Done when conditions in `specs/deferred_items.md`. M3’s protocol-ordering history is retained without a checkbox. The fully repaired renderer group alone closes; the durable 47-item baseline and current proposal are in [stage10-backlog-triage.md](stage10-backlog-triage.md). No unrelated deferred work executes.

The original named final-review role was unavailable; the controller used two fresh full-form Sol Ultra seats sequentially at the same implementation HEAD. The subsequent two review pairs are scoped to their exact repair ranges. The later clarification removed a reviewer-inferred extra protected-hash-attestation gate; it did not relax GC/GS13. Protected ignored-byte equality remains unverified, while the tracked reviewed ranges contain no protected changes and agents made no protected reader/writer operation. Neither old reviews nor human gates review this new documentation delta.

Actual public seams remain `load_workflow_config(path: Path, *, repo: Path) -> WorkflowConfig`, `run_theme_workflow(config: WorkflowConfig, runtime: WorkflowRuntime, *, now: Callable[[], datetime]) -> WorkflowResult`, structural `read_analysis_run(directory: Path) -> StoredAnalysisRun` and current `reverify_analysis_run(stored, inputs, policy, families) -> None`. Fourteen analytical table schemas and analysis/report/workflow schema 1; processing schema 2 preserves legacy schema 1; core schema 2 remains unchanged. No pilot extraction, production quality/calibration, all-four-cache fresh stability, transcript extraction, SEC request, model call/download or hosted dispatch is claimed.

Human native/manual V5 details and limitations are durable in [stage10-browser.md](stage10-browser.md) and its safe observation JSON. All six fallback outcomes reflect human inline invented-page evidence; no actual capture files were opened by agents or copied into Git/export. The capture skip’s SDK/binary/platform cause remains unreported despite the available pinned manual target.

### Executed deferred statistics

Required developer Python 3.13 ran offline without downloads, exit 0:

```bash
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --no-project --python 3.13 --offline --no-python-downloads python /Users/lowell/.agents/skills/writing-plans/scripts/deferred_stats.py --json
```

Post-completion: **48 open / 35 closed / 83 total**, closure rate **0.4217 (42.17%)**. All 48 open items are 0–14 days old; 15–30, 31–45, 46–90 and 91+ buckets are zero. Aged >45 days and undated open items are zero. Oldest is 13 days (`1-release-parser-fidelity`). With at least 20 open items, the read-only proposal follows these statistics in `docs/verification/stage10-backlog-triage.md`; unrelated dispositions still require human `/deferred` selection. The 47-open baseline is retained distinctly. No aged-tail acknowledgement is needed.

### Fresh completion documentation checks

After allowlisted source comparison against the retained 253-source audit, 251 sources matched; only the previously reviewed guarded runner and its regression test differed. The changed guard and exact selected contracts/vertical registries, imports, fixtures and readers were audited before collection. Selected readers use permitted Stage 1/synthetic event fixtures, invented temporary repositories or source/docs/AST; no protected real-data/example reader is dispatched. The human modes were never invoked, even through a fake transport.

Sequential captured checks with `POLARS_MAX_THREADS=2` and `UV_CACHE_DIR=/private/tmp/earnings-stage10-uv`:

```bash
uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py contracts
uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py vertical
uv run --locked --offline --no-sync ruff check packages apps tests tools --output-format json
uv run --locked --offline --no-sync ruff format --check packages apps tests tools
git diff --check
```

Fresh contracts: **548 passed**; vertical: **21 passed**. Both exit 0 with zero failures, collection failures, skips, deselections and warnings, IDs [] and reason null. Ruff lint exit 0, zero findings; format exit 0, **368 files already formatted**. Diff check exit 0. Probe construction and execution were inside an outer catch, with captured output and only closed safe metadata emitted. Stage10/root/Stage6 wording/browser were not rerun for this documentation delta. No artificial documentation RED was added; the prior 547/1 regression and corrected 548 remain in the historical record. These checks establish this delta’s consistency, not the pending scoped review or integration.
