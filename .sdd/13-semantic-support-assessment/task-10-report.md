# Task 10 report

Status: DONE

Implementation commit: `a296079` — `test(support): cover curated partial spans and hostile judge replies`.
The final handoff also includes a separate documentation commit containing this report.

## Scope and APIs

Changed only the five Task 10 test/helper files and this report. No product,
drafting, codebook, fixture, provider, or configuration files changed. The
pre-existing untracked plan remains untracked and unchanged.

`curated_cases(path: Path, bundles: Mapping[str, Bundle], codebook: Codebook)
-> tuple[tuple[SupportSources, Target, str], ...]` and its `curated` pytest
fixture live exclusively in `tests/integration/test_support_fixtures.py`.
The translator reads only the explicitly supplied permitted hard-negative file,
Stage 1 canonical fixtures, and approved codebook records. It binds the approved
codebook identity/hash without resolving examples. Each original pointer passes
`check_pointer` before reconstruction through `parse_span_candidate` and
`validate_span` using unchanged offsets, element ID, and canonical slice. A
failed match/pointer/span raises a fixed fixture-only reason.

All 29 original pointers and unchanged curated claims are exercised, with kinds
`issuer=4`, `period=13`, and `section=12`. Assertions compare original offsets,
element IDs, quote hashes, and mask IDs against translated records, and prove
partial-unit spans exist. IDs translate explicitly to `q-start-end`; software and
provenance bind the curated file SHA-256, fixture ID, and translation map.
`adapter_kind="curated-fixture"` labels the manually assembled stored input.
This is contract translation, not Stage 7 model output or evidence of extraction
accuracy. Scripted objections preserve raw scorer/judge scores and produce
flagged processing outcomes; no model-quality claim is made.

Synthetic unit helpers in `support/cases.py` provide invented paragraph bundles,
hostile source instructions, and eight hostile reply categories. Tests check
closed-schema/tool/ID refusals, two-attempt limits, unchanged source/codebook
hashes, retained temporary raw replies, no accepted field, and no socket trips.
The nine invented processing cases cover positive support, negation, competitor,
prior period, wrong-theme positive, context-only assertion, contextual quote,
distributed support, and compound partial support. All conclusions are scripted.

Offline integration uses `write_run/read_run` for an invented manually scripted
extraction fixture, explicit targets, `assess_run`, `write_support_run/read_support_run`,
and `reverify_support_run`. Live fake dispatch populates the cache; replay retains
outcomes with zero fresh dispatch and re-verifies sources. Changed evidence after
cache creation and after storage refuses consuming paths. Partial panels and
ceilings remain incomplete with semantic objections retained.

Safe-output tests plant invented sentinels in every string field across support
contracts, source text and claim, request, raw reply, rationale, unknown ID/key,
transport error, corrupted cache, persisted manifest, and persisted evidence row.
Computed boolean diagnostics are bound before assertions; errors, retry feedback,
str/repr and summaries omit private strings. Raw artifacts exist only beneath
pytest temporary directories. Existing AST/fresh-interpreter guards, including
planted forbidden imports, and the permitted Stage 1 support wording node pass.
No pilot source/gold/draft/data paths were accessed; no live/network/model/SEC or
billable calls were made. No product defect or scoped product fix was necessary.

## RED evidence

Command:

```text
uv run --locked --all-packages python3 -m pytest tests/integration/test_support_fixtures.py packages/earnings-themes/tests/support/test_injection.py packages/earnings-themes/tests/support/test_safe_output.py -q
```

Result: **9 failed, 1 passed**. The integration test failed with missing
`curated_cases`; eight initial injection helper checks failed with missing
`hostile_reply`. Before implementing the helper, those checks were strengthened
into behavioral assertions for unusable replies, immutable inputs, no dispatchable
tools, and retained raw artifacts.

Behavioral RED command:

```text
uv run --locked --all-packages python3 -m pytest packages/earnings-themes/tests/support/test_injection.py -q
```

Result: **8 failed** at the missing helper, before implementation.

## GREEN evidence

Final required node command:

```text
uv run --locked --all-packages python3 -m pytest tests/integration/test_support_fixtures.py packages/earnings-themes/tests/support/test_injection.py packages/earnings-themes/tests/support/test_safe_output.py tests/contracts/test_support_contracts.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/integration/test_support_wording.py -q
```

Result: **102 passed in 22.82s**, no warnings or skips.

Explicit existing mutation/input gates:

```text
uv run --locked --all-packages python3 -m pytest packages/earnings-themes/tests/support/test_assess.py::test_mutated_canonical_after_dispatch_aborts_and_keeps_completed_raw packages/earnings-themes/tests/support/test_assess.py::test_invalid_evidence_refuses_zero_dispatch -q
```

Result: **2 passed in 0.05s**. Invalid initial evidence dispatches nothing;
post-dispatch canonical mutation safely aborts and retains cache/accounting.

Final lint command:

```text
uv run --locked ruff check tests/integration/test_support_fixtures.py packages/earnings-themes/tests/support/cases.py packages/earnings-themes/tests/support/test_injection.py packages/earnings-themes/tests/support/test_safe_output.py tests/contracts/test_support_contracts.py
```

Result: **All checks passed!**

Formatting command:

```text
uv run --locked ruff format --check tests/integration/test_support_fixtures.py packages/earnings-themes/tests/support/{cases,test_injection,test_safe_output}.py tests/contracts/test_support_contracts.py
```

Result: **5 files already formatted**. `git diff --check` was clean before commit.
An earlier lint run found three mechanical test-only issues; they were corrected
and the final scoped lint command above passed.

## Self-review and limits

Checked file ownership, exact-pointer preservation, frozen codebook binding,
fixture identity/provenance, source-redacted failure assertions, socket guards,
and unchanged producer contracts. No unrelated untracked file was staged.
These tests verify processing/contracts and scripted replay only, not semantic
accuracy, calibration, stability, real weights, or V4 real inference. Those are
outside this task. The integration file is 444 lines because the translator and
fixture must remain there; no test-only translator was moved into product code.
Clean Code applied: cohesive invented-case helper (G30), named fixture/provenance
bindings (N1/G19), boundary assertions for invalid evidence and partial panels
(T5), and per-string-field privacy sweeps (T6).
