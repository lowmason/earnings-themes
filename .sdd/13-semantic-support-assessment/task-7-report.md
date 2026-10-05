# Task 7 implementation report

Status: DONE. Implementation commit: `d0dec05` —
`feat(support): assess independent signals with auditable review outcomes`.

## Scope and implemented behavior

Implemented Stage 8 assessment only, in the isolated managed checkout. Added
sequential per-quote/joint entailment signals, a one-quote joint alias, four
independent judge trials (two supplied families × two presentations), at most two
attempts per trial, fixed retry feedback, raw replay, complete-input counting,
request/token allowance accounting, and categorical review outcomes. Valid
negative/uncertain answers finish their trial without retry. No acceptance field,
score threshold, numeric disagreement tolerance, pooling, majority vote,
classification, live inference or new command was added.

Initial invalid evidence returns a refused target with zero dispatch. Evidence is
reverified before each scorer/cache reuse, before each judge attempt, and before
publication. Changes after dispatch abort publication with fixed `input_changed`
from no exception chain; completed raw cache artifacts and settled accounting
remain local. No synthetic zero-dispatch refusal is returned after calls occur.

Incomplete outcomes preserve semantic flags. Quote contribution comparisons sort
by quote ID. Low NLI values alone do not flag, high values do not erase objections,
contextual quote contributions alone are permitted, and context-only assertion
support is flagged. Required signal/trial coverage is validated at derivation.

## Actual public APIs and approved plan deviations

- `assess_target(input: ResolvedInput, scorer: EntailmentScorer,
  judges: tuple[Judge, Judge], policy: SupportPolicy, allowance: Allowance,
  *, cache: SupportCache, extractor_family: str) -> AssessmentResult`.
  The controller approved adding required keyword-only `extractor_family` because
  neither ResolvedInput nor the Stage 7 source identity carries explicit lineage.
  Aliases never establish it. Missing, blank, malformed or equal-family lineage
  preflight refuses before scorer/judge dispatch. Task 8 must pass this argument.
- `derive_outcome(target_id: str, entailment: tuple[EntailmentSignal, ...],
  trials: tuple[JudgeTrial, ...], evidence_ids: tuple[str, ...]) -> ReviewOutcome`.
  `evidence_ids` contains quote IDs, as established by resolution. Fixed categorical
  flags are documented in the data dictionary.
- `SupportCache.put(key, raw, *, refusal_reason: str | None = None) -> str` and
  `SupportCache.refusal_reason(key) -> str | None` are controller-approved minimal
  Task 6 integration elaborations. Raw judge replies naming the wrong model remain
  cached under the expected request/identity binding and are always reparsed as
  unusable attempts. Scorer input/identity bindings stay strict.
- `SupportCacheEntry.refusal_reason` is optional and admits only fixed judge
  transport/schema failures (`transport_error`, `model_mismatch`,
  `tool_call_refused`, `malformed_reply`, `invalid_references`), never semantic
  objections. Combined reply/refusal metadata is integrity-hashed, checked on
  reuse, and included in incompatible-existing-entry checks. This preserves an
  otherwise-valid transport-refused raw answer as unusable in live and replay.
  Prior Stage 8 development envelopes without the combined digest are invalidated
  as corrupt; support/core/extraction/Stage 6 schema versions are unchanged.
- `unexpected_error(error: Exception) -> SupportError` in problems.py is an approved
  narrow scorer/assessor diagnostic seam. It attaches `diagnostic` using exact
  trusted builtin exception type identities; custom/untrusted class names become
  fixed `Exception`. str/repr print only `unexpected_error`; no message, raw reply,
  request or arbitrary class name enters diagnostics. Scorer failures retain their
  existing unavailable semantics.

## TDD evidence

Initial required RED command:

```text
uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_assess.py -q
E   ModuleNotFoundError: No module named 'earnings_themes.support.assess'
ERROR packages/earnings-themes/tests/support/test_assess.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.06s
```

Exit 2, expected because assessment/outcome derivation did not exist. After the
first implementation the same command returned `24 passed in 1.03s` (exit 0).

Additional integration RED evidence:

```text
uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_assess.py packages/earnings-themes/tests/support/test_cache.py -q
7 failed, 91 passed in 1.55s
```

Three valid attached transport-refusal replay regressions failed because the cached
answer was promoted to usable; four cache metadata tests failed with unexpected
`refusal_reason` argument. After metadata implementation and safe diagnostics,
the same two-file suite returned `100 passed in 1.51s` (exit 0).

Safe scorer diagnostic RED added two cases: `5 failed, 32 passed in 1.24s` included
three still-pending metadata failures and two missing diagnostic AttributeErrors.
Both scorer cases became green after the approved seam fix, with custom exception
names and messages redacted.

Self-review defect RED, focused assessment command: `2 failed, 37 passed in 1.37s`.
Malformed typed raw usage incorrectly raised `malformed_record` rather than
retryable `malformed_reply`; result usage latency remained allowance default zero.
Fixes at the raw response boundary and result usage rows yielded
`39 passed in 1.40s`. Preflight malformed records retain their original refusal.

Postdispatch mutation RED, same focused command: `1 failed, 39 passed in 1.32s`.
An invented mutated canonical source reached later cache-key validation rather
than the current evidence gate. After per-operation/publication reverification,
the regression proves safe abort, exactly one retained raw artifact/settled
operation, and no later scorer/judge dispatch.

## Final verification (all exit 0)

```text
uv run --locked --all-packages pytest packages/earnings-themes/tests/support -q
431 passed in 2.06s
```

All support tests run on invented text and inherited offline network guards; every
applicable no_network fixture asserts empty trip records. No network/model,
weights download, SEC/browser request or billable call was made.

```text
uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q
208 passed in 0.23s
```

The existing SupportCacheEntry field registry automatically covers the new field;
no model/enum registration was needed. The dictionary was updated in this change.

Modified-file commands (assess.py, cache.py, problems.py, scorers.py, test_assess.py,
test_cache.py, cases.py, conftest.py under their owning support paths):

```text
uv run --locked ruff check <the eight modified Python files>
All checks passed!
uv run --locked ruff format --check <the eight modified Python files>
8 files already formatted
```

`git diff --check` produced no output. No root/full Stage 6/wording/live suite ran.

## Files and self-review

Created support/assess.py and tests/support/test_assess.py. Modified tests/support
cases.py and conftest.py, plus approved supporting cache.py/test_cache.py,
problems.py/scorers.py, and docs/data-dictionary.md. The root plan's preexisting
untracked copy was not staged or changed. No data directory was created or read;
no signed pilot gold, drafts, codebook example passages or pilot text were opened.
The six drafting modules were untouched and no support import was added to them.

Self-review read the code/diff and confirmed independent request histories,
one-quote alias accounting, initial/final integrity behavior, known failure versus
unexpected abort semantics, closed safe feedback, semantic outcome precedence,
wrong-model and refused-raw replay, and usage settlement. It caught and restored
four preexisting parameterized cache regression blocks inadvertently encompassed
while replacing the old wrong-model cache expectation; final all-support count
includes all 16 restored cases. Existing tests were preserved except the explicitly
approved wrong-model cache expectation change. Cohesive helpers separate scorer,
trial, attempt, review, and preflight responsibilities (clean-code G30/G34/N1).

Remaining concerns: none blocking. Real inference/V4, full import/wording guards,
run storage and Stage 11 calibration/stability remain with their assigned tasks.


## Round 1 review fix: complete two-family panel coverage

Implementation commit: `73be715` — `fix(support): require complete two-family outcome panel`.
Verified the review finding against derive_outcome and the original Task 7 brief
using receiving-code-review. Four distinct family/presentation pairs alone did
not establish two complete families. Added an invented regression representing
(A, evidence_first), (A, claim_theme_first), (B, evidence_first),
(C, evidence_first), with all other signals positive and available.

RED:

```text
uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_assess.py -q
E   AssertionError: assert <ReviewStatus...D: 'assessed'> == 'incomplete'
1 failed, 40 passed in 1.67s
```

Minimal fix: derive_outcome now groups presentation sets by family, requires
exactly two families, and requires each set to equal the complete configured
presentation set. The malformed panel becomes incomplete with invalid_references.
No other outcome, retry, cache, schema, budget or dispatch behavior changed.

GREEN:

```text
uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_assess.py -q
41 passed in 1.61s
uv run --locked ruff check packages/earnings-themes/src/earnings_themes/support/assess.py packages/earnings-themes/tests/support/test_assess.py
All checks passed!
uv run --locked ruff format --check packages/earnings-themes/src/earnings_themes/support/assess.py packages/earnings-themes/tests/support/test_assess.py
2 files already formatted
```

All commands exited 0; git diff --check produced no output. Tests use existing
invented fixtures and inherited no_network guards. No root, Stage 6 wording,
live/model, data, pilot text/gold, or codebook example access occurred. Self-review
confirmed the change is confined to the finding and does not amend earlier commits.
