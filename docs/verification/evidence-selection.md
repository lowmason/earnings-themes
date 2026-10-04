# Evidence selection and verification

Stage 7's verification record (`specs/evidence-selection-and-verification.md`,
§Verification). Plan A's section records its proof and the main checkout's gate;
plan B appends its own. Every entry holds IDs, counts, test names, and hashes, and
never a release's wording (ES2).

## Plan A: core and anchoring (plan 11)

Plan 11 (`specs/plans/11-evidence-selection-and-verification-plan-a.md`) landed the
spec's §Plan A. It changed functions and tests, and no committed record.

- **The core fixes (ES4, ES5).**
  - `reverify_span` verifies a stored span again from its fields, and never dumps
    it.
  - `validate_span` refuses an offset that is not exactly an `int`, or is a
    `bool`, as `malformed_record`, where version 2 raised, returned another
    check's reason, or, for an `int` subclass, accepted the span, since the offset
    check now runs first.
  - `resolve_pointer` resolves the genuine element wherever it sits in the list.
  - `VALIDATOR_VERSION` is `"3"`, and no committed record stores it.
- **One canonical JSON (ES7).** `canonical_json` and `digest` live in
  `earnings_core.digests`, moved verbatim with their known-answer tests. Both
  packages import that one definition. The duplicated pilot pin stays, with its own
  reproduction tests.
- **`context_hash` (ES8).** A known-answer test pins its byte format, with a pair
  holding a non-ASCII character, a double quote, and a backslash:
  `fd4874e7855a8b8d6c9df217cca901d75d1129624089f94a6db6cda22ef52280`, over 47 bytes.
- **The narrative rule (ES9).** An `other` element with at least one child, whose
  children hold every non-space character of its span, is a transparent container,
  and no longer blocks a quote.
  - Stage 1's 686 sentences now give 660 anchored, 26 repeated, and 0 not narrative.
  - The 10 that moved sit under `other-3292-5040` in `0000949699-08-000023_ex-99-1`.
  - No pilot verdict changed (M5: 0 of 5139).

### The proof

Each committed record, and the tests that reload it through its loader and recompute
its content hash with the moved functions:

| Record | Rehashed offline, in the worktree, by | Rechecked in the main checkout only, by |
| --- | --- | --- |
| Universe v1 | `test_cohort_identity.py::test_v1_loads_unchanged_and_has_an_operative_hash` | — |
| The synthetic cohort | `test_cohort_fixtures.py`: regenerates byte for byte, and replays | — |
| Events v1 and its evidence record | `test_event_corpus_v1.py::test_events_v1_loads_unchanged_with_its_evidence_record` | — |
| Pilot v1, reselected | `test_event_corpus_v1.py::test_pilot_v1_loads_unchanged_and_djia_pilot_1_reselects_it`; `test_stage6_pilot_v1.py::test_the_pin_is_pilot_v1_and_its_chain` | — |
| The synthetic events and acquisition | `test_event_fixtures.py`: regenerates byte for byte, and replays both | — |
| The split | `test_stage6_pilot_v1.py::test_the_committed_split_reproduces_byte_for_byte` | — |
| The coverage report | `test_stage6_records.py`: its hash and its pin | `test_stage6_pilot_v1.py::test_the_committed_coverage_report_reproduces_from_its_runs` |
| Codebook v0 | `test_stage6_records.py`: its hash, ADR 0003, its corpus's pin and split hash | `test_stage6_pilot_v1.py::test_committed_records_validate_against_the_local_store`, codebook case |
| The three gold files | `test_stage6_records.py`: each parses, codes against v0, holds together by ID, and names the pin and split hash | the same local test, gold case |
| The curated hard negatives | `test_stage6_pilot_v1.py::test_the_curated_hard_negatives_validate_offline` | — |
| The canonical fixtures | `test_canonical_golden.py::test_the_canonical_fixture_regenerates_byte_for_byte`, 8 cases | — |

- **Offline.** The worktree's column, run by node ID, printed `20 passed, 3
  skipped`. The three skips are the main checkout's column.
- **The diff.** `git diff --stat 186348d -- config evaluation codebooks
  tests/fixtures` printed nothing.
- **One definition.** `def canonical_json` and `def digest(` occur once each, in
  `packages/earnings-core/src/earnings_core/digests.py`, and nothing names
  `cohort.digests`.
- **The suites, in the worktree.**
  - The default suite printed `1747 passed, 8 skipped, 24 deselected`. Its 8 skips
    are the local legs that need `data/`.
  - The harness suite printed `275 passed, 5 skipped`.
  - Ruff passed, and `uv.lock` is unchanged.

### The main checkout

On [GATE: the date], the user ran the default suite in the main checkout at plan A's
tip, `[GATE: the tip's short hash]`, on a detached HEAD, from a checkout with no
tracked change. It printed `[GATE: the summary line]`. Its skip was
[GATE: the skip line's location and reason]. [GATE: "No test failed.", or each
failure's node ID and exception type, with its fix's commit.]
