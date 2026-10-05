# Task 6 implementation report

Status: DONE.

Implemented sequential explicit scorer/judge reservations, settlement and safe immutable usage snapshots; support-specific raw response caching with full canonical binding keys, typed identity/request/raw reply validation, integrity checks and atomic publication. No source document, codebook example, signed gold, pilot text, network request or model call was read/made. No data directory was created. Existing changes and untracked plan were preserved.

## Interfaces for Task 7

- `support.allowance.Allowance(ceilings: SupportCeilings)`.
- `reserve_scorer(target_id, doc_id) -> str` reserves one evaluation after caller tokenizer/model-limit preflight.
- `reserve_judge(target_id, doc_id, input_tokens, completion_limit) -> str` reserves one request and full input plus allowed completion.
- `settle(reservation_id, usage: Usage | None) -> None`, once only. Missing usage retains the full token reservation; known usage charges actual tokens, including overspend. Request/evaluation counts and original token reservations remain in snapshots.
- `snapshot() -> tuple[UsageRecord, ...]`; fixed errors and count-only allowance repr.
- `reserved_judge_tokens(input_tokens, completion_limit) -> int`, strict integers; full input nonnegative and completion positive.
- `support.cache.scorer_key(input, request: ScoreRequest, identity: ScorerIdentity, policy) -> SupportCacheKey`; corresponding `judge_key` uses `JudgeRequest` and `JudgeIdentity`.
- `SupportCacheKey` is an ordinary SHA-256 `str` subclass with immutable canonical `.material` local binding. String/repr show digest only; its dictionary is read-only. Boundary digest/canonical/schema checks detect even deliberate low-level mutation. A bare digest safely refuses because it cannot carry expected typed request/identity binding. This is the controller-approved interface elaboration, not a mutable registry.
- `SupportCache(directory: Path, mode: Literal['live', 'replay'])`. `lookup(key, kind) -> ScoreReply | ModelReply | None`; neither mode dispatches. A replay miss must become `replay_miss` in the coordinator; live misses may dispatch. No bypass.
- `put(key, raw: ScoreReply | ModelReply) -> str` returns a relative artifact filename. `raw_ref(key) -> str` returns the same filename, `<digest>.json`. Resolve it beneath the caller-supplied cache directory.
- Cache reads return the original raw reply unchanged; the coordinator records cached status and consumes no allowance on hits. One-quote joint alias also reserves no extra evaluation.
- New `SupportCacheEntry(SupportRecord)` is documented and registered. It retains canonical material, typed request/identity, raw reply and integrity hash. Key material contains full original source-run bindings, claims/quotes including locator prefixes/suffixes, canonical documents, structures/masks, target/theme/codebook, context/evidence, request/parameters/schema/messages/presentation/retry feedback and runtime/checkpoint/limits plus policy versions. No examples are dereferenced.
- Scorer model/input mismatches and judge model mismatches are refused before caching. Unavailable scorer replies remain raw explicit unavailable signals, never zero or verdicts. Judge raw unusable schema/tool replies can remain auditable local artifacts and must be reparsed downstream.
- Every applicable count/token ceiling is checked before mutation. Scorer usage is separate from judge-token ceilings. Original reservations, actual usage and unknown flags are retained independently.

## TDD evidence

Applied test-driven-development and clean-code skills and the subagent-driven-development implementer procedure. Production code followed observed missing-module RED.

Initial RED command:

```text
uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_allowance.py packages/earnings-themes/tests/support/test_cache.py -q
```

Full safe output, exit 2:

```text
==================================== ERRORS ====================================
__ ERROR collecting packages/earnings-themes/tests/support/test_allowance.py ___
ImportError while importing test module '/Users/lowell/.codex/worktrees/stage8-semantic-support/earnings-themes/packages/earnings-themes/tests/support/test_allowance.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
packages/earnings-themes/tests/support/test_allowance.py:4: in <module>
    from earnings_themes.support.allowance import Allowance, reserved_judge_tokens
E   ModuleNotFoundError: No module named 'earnings_themes.support.allowance'
____ ERROR collecting packages/earnings-themes/tests/support/test_cache.py _____
ImportError while importing test module '/Users/lowell/.codex/worktrees/stage8-semantic-support/earnings-themes/packages/earnings-themes/tests/support/test_cache.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
packages/earnings-themes/tests/support/test_cache.py:7: in <module>
    from earnings_themes.support.cache import SupportCache, scorer_key, judge_key
E   ModuleNotFoundError: No module named 'earnings_themes.support.cache'
=========================== short test summary info ============================
ERROR packages/earnings-themes/tests/support/test_allowance.py
ERROR packages/earnings-themes/tests/support/test_cache.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
2 errors in 0.06s
```

The missing modules were the expected brief Step 2 failure. First GREEN after implementation: 69 passed in 1.27s across allowance/cache/scorers.

Additional observed RED cycles:

- Focused allowance/cache command: binding dictionary mutation test reported `Failed: DID NOT RAISE TypeError`, 1 failed and 64 passed. Fixed immutable key dictionary with a mapping proxy.
- `uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_cache.py::test_unknown_binding_keys_refused_safely -q`: each of record/policy/source_run reported `Failed: DID NOT RAISE SupportError`, 3 failed in 0.04s. Added complete closed typed material validation at the cache boundary and during key construction.
- Stricter key boundary correctly refused mutation fixtures containing invalid spans/core IDs/hashes; these test setup errors were corrected to legal nonempty spans, actual changed context kinds, and valid newly created canonical document versions. No production validation was weakened.

## Final verification

All commands ran in the isolated checkout with task-scope escalation. No full root suite, full Stage 6 wording, live, browser, pilot wording or real-inference checks ran.

```text
uv run --locked ruff check packages/earnings-themes/src/earnings_themes/support/allowance.py packages/earnings-themes/src/earnings_themes/support/cache.py packages/earnings-themes/tests/support/test_allowance.py packages/earnings-themes/tests/support/test_cache.py tests/contracts/test_data_dictionary.py
All checks passed!
```

```text
uv run --locked ruff format --check packages/earnings-themes/src/earnings_themes/support/allowance.py packages/earnings-themes/src/earnings_themes/support/cache.py packages/earnings-themes/tests/support/test_allowance.py packages/earnings-themes/tests/support/test_cache.py tests/contracts/test_data_dictionary.py
5 files already formatted
```

Final GREEN command and full output, exit 0:

```text
uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_allowance.py packages/earnings-themes/tests/support/test_cache.py packages/earnings-themes/tests/support/test_scorers.py tests/contracts/test_data_dictionary.py -q
........................................................................ [ 22%]
........................................................................ [ 44%]
........................................................................ [ 66%]
........................................................................ [ 88%]
....................................                                     [100%]
324 passed in 0.44s
```

`git diff --check`: exit 0, no output.

## Files changed

- New support/allowance.py and support/cache.py.
- New tests/support/test_allowance.py and tests/support/test_cache.py.
- docs/data-dictionary.md and tests/contracts/test_data_dictionary.py: required new model documentation/registry.
- This report.

## Self-review and limitations

Exhaustion is atomic; all target/document/run count ceilings and both token ceilings have focused tests. Four trials plus a retry consume five reservations. Settlement preserves unknown usage, original reservations and actual overspend. Cache key mutation tests cover normative material groups, original locators, evidence/context bounds, source structure and valid canonical versions. Corruption, incompatible existing contents, model/input mismatch, immutable bindings, low-level forged bindings, and sentinel-safe fixed errors are tested. Import/runtime dependencies remain default-safe and offline.

Coordinator ownership remains explicit: full tokenizer/context/output preflight precedes reservations; replay misses never dispatch; evidence is reverified on cache hits and after scoring; cache hits are recorded outside dispatch allowance. Sequential atomic publication has no concurrent-writer guarantee. Stage 11 fresh bypass/calibration/stability remain deferred. Existing drafting module guards are untouched by this task; no support imports were added to drafting modules. Source-note filenames named by root AGENTS.md are absent at repository root; no source-note rewrite was attempted.

Commit subject: `feat(support): bound dispatch and cache raw versioned signals`.


## Mutation coverage matrix against Task 6 key table

| Normative row | Focused test coverage and captured material |
| --- | --- |
| Source content | `test_full_source_document_changes_key` creates valid changed document identity/hash/text versions; `test_target_binding_changes_key` covers claim hash/input hash; `test_normative_material_changes_key` covers claim words; `test_every_evidence_field_changes_digest` covers quote ID, document hash, element ID, offsets, text hash, verifier version and masks; `test_original_quote_locator_changes_key` covers prefix/suffix/text; `test_structure_bounds_change_key` covers canonical element bounds; `test_context_bounds_and_locator_material_change_key` covers context bounds/element/hash/kind. Complete source bundles and original extraction quote locators are in material. |
| Target binding | `test_every_theme_field_changes_digest` covers theme ID/label/definition/parent and inclusion/exclusion rules; `test_codebook_binding_changes_digest` covers codebook ID/version/hash; `test_target_binding_changes_key` covers document, target, input and source-run bindings; `test_normative_material_changes_key[provenance]` covers source provenance. |
| Adapter identity | `test_runtime_material_changes_key` parametrizes model ID, revision, file manifest, runtime/version, device, precision and encoding; `test_normative_material_changes_key[limits]` covers scorer limit; `test_judge_invocation_changes_key` covers family, input and output limits. Whole typed identities are in material. |
| Invocation | `test_judge_invocation_changes_key` covers complete messages including invented retry feedback, reply schema and presentation; `test_all_judge_model_settings_change_key` covers temperature/seed/max_tokens/structured; prompt and policy seed mutations are also covered. Entire typed rendered requests, subject hashes, schema and policy text are in material. |
| Policy | `test_incompatible_policy_versions_refused` covers support/schema version incompatibility; verifier version is explicitly mutated in evidence; prompt text and settings change the digest. Whole policy plus fixed support/schema versions bind rendering/scoring semantics; no hidden scoring settings exist. |

Controller checkpoint was 320 passing before four focused coverage additions
(judge input limit, structured output, two incompatible versions). Final 324/324
passing output above is after those additions; implementation did not change.

## Review round 1: filesystem cleanup exception safety

Verified the Important finding at `SupportCache.put`: `partial.unlink` was outside
the storage `OSError` handler, and a cleanup failure could replace the intended
fixed error with raw filesystem diagnostics. Applied receiving-code-review and
TDD, changing only cache.py, test_cache.py and this report.

RED command:

```text
uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_cache.py::test_cleanup_failure_keeps_fixed_storage_error -q
```

Observed exit 1, safe output:

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
_____________ test_cleanup_failure_keeps_fixed_storage_error[True] _____________
packages/earnings-themes/tests/support/test_cache.py:531: in test_cleanup_failure_keeps_fixed_storage_error
    assert type(caught).__name__ == "SupportError"
E   AssertionError: assert 'OSError' == 'SupportError'
E
E     - SupportError
E     + OSError
____________ test_cleanup_failure_keeps_fixed_storage_error[False] _____________
packages/earnings-themes/tests/support/test_cache.py:531: in test_cleanup_failure_keeps_fixed_storage_error
    assert type(caught).__name__ == "SupportError"
E   AssertionError: assert 'OSError' == 'SupportError'
E
E     - SupportError
E     + OSError
=========================== short test summary info ============================
FAILED packages/earnings-themes/tests/support/test_cache.py::test_cleanup_failure_keeps_fixed_storage_error[True]
FAILED packages/earnings-themes/tests/support/test_cache.py::test_cleanup_failure_keeps_fixed_storage_error[False]
2 failed in 0.05s
```

The parametrized regression covers both publication failure followed by cleanup
failure, and cleanup failure after successful publication. Injected filesystem
errors contain invented sentinel paths; the test checks error type before any
printable text, so no raw sentinel exception appears in RED output.

Implementation retains a fixed `storage_failure` through cleanup. A cleanup error
creates a fixed error only when no original storage failure exists. After cleanup,
the preserved error is raised `from None`. No raw filesystem error can replace the
original fixed publication error. No unrelated cache behavior changed.

GREEN and focused checks (all exit 0):

```text
uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_cache.py -q
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 0.28s
```

```text
uv run --locked ruff check packages/earnings-themes/src/earnings_themes/support/cache.py packages/earnings-themes/tests/support/test_cache.py
All checks passed!
```

```text
uv run --locked ruff format --check packages/earnings-themes/src/earnings_themes/support/cache.py packages/earnings-themes/tests/support/test_cache.py
2 files already formatted
```

`git diff --check`: exit 0, no output. No broad root, Stage 6 wording or live tests
were run. Original Task 6 commit is preserved; this correction is a separate
commit with subject `fix(support): redact cache cleanup failures`.
