# Evidence selection and verification

Stage 7's verification record (`specs/evidence-selection-and-verification.md`,
§Verification). Plan A's section records its proof and the main checkout's gate;
plan B appends its own. Every entry holds IDs, counts, test names, and hashes, and
never a release's wording (ES2).

## Plan A: core and anchoring (plan 11)

Plan 11 (`specs/plans/completed/11-evidence-selection-and-verification-plan-a.md`) landed the
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
  - The default suite printed `1748 passed, 8 skipped, 24 deselected`. Plan A
    added 11 collected tests: 10 in its tasks, and 1 in the final review's fixes.
    Its 8 skips are the local legs that need `data/`.
  - The harness suite printed `275 passed, 5 skipped`.
  - Ruff passed, and `uv.lock` is unchanged.

### The main checkout

On 2026-10-04, the user ran the default suite in the main checkout at plan A's
tip, `5c4259e`, on a detached HEAD, from a checkout with no tracked change. It
printed `1755 passed, 1 skipped, 24 deselected`. Its skip was
`tests/integration/test_event_store_v1.py:42`: the first acquisition has run, and
`docs/verification/djia-events.md` records its count. The other 7 legs that skip in
the worktree ran there and passed. No test failed.

## Plan B: the extractor (plan 12)

Plan 12 (`specs/plans/12-evidence-selection-and-verification-plan-b.md`) landed the
spec's §Plan B: `earnings_themes.extraction`, its tests, and the local adapter behind
the `local-model` extra. No committed record changed. No session read pilot text or
gold, and no default test calls a model or opens a socket (ES2, R14.1).

- **Units and windows (ES12, ES13).** Stage 3's eight fixtures hold 797 units: 686
  sentences, 108 headings, 1 paragraph, and 2 footnotes. At the default budget of
  4000 characters they pack into 37 windows: 9, 5, 7, 6, 3, 2, 2, and 3, in the
  fixtures' sorted order. One block is longer than the budget,
  `paragraph-15361-19669` in `0000010795-22-000014_ex-99-1`, at 4301 characters, and
  has `w-15361-19669` to itself. Every unit lies in exactly one window, and every
  eligible element holds a unit (R10.1). The plan reads structure and lengths, never
  a unit's text (R10.2): the only text it reads is `narrative_home`'s whitespace test
  of a container (ES9), which ranks and selects nothing.
- **The mixed scripted run (R5.1, R6.2).** Its 37 windows gave 61 requests, 549
  candidates, 537 claims, and 525 quotes. Its rejections: 6 `blank_claim`, 6
  `malformed_reply`, 12 `tool_call_refused`, 6 `transport_error`, and 6
  `unknown_label`. 31 windows completed and 6 failed, so 6 documents are partial and
  2 complete. Every retained quote verifies again, every parsed candidate is one claim
  or one rejection, and no window makes more than 2 attempts. A fake that cites every
  label keeps all 797 units as quotes.
- **R14.6.** One case per key component, 21 in all: changing it misses, and the inner
  adapter is called again. An identical key hits, and calls nothing.
- **R14.1.** The scripted runs happen under the socket guard, which recorded nothing.
  The local adapter's tests run on httpx's `MockTransport`, but one, which runs its
  real transport against a refused socket. Only `extraction.local` loads httpx, and
  no themes module imports it. The default suite imports it without the
  `local-model` extra all the same: `earnings-ingestion` depends on httpx, and the
  workspace's one environment holds every member's dependencies (F3).
- **R14.7 and V11.** The injection document's obeying replies are refused: a tool
  call as `tool_call_refused`; a codebook rewrite, or offsets or quote text beside
  the labels, as `malformed_reply`; and offsets, copied text, or another document's
  element given as a label as `unknown_label`. A spoofed label resolves to the unit
  code labeled. No request body carries `tools`, and only spans that code sliced are
  stored.
- **GS13 and ES16.** The six drafting modules import nothing from the extractor. A
  rejection prints as its reason and IDs, by `str` and by `repr`. The store, the
  cache, and the configuration refuse a record by its fields, and the extractor's own
  messages name paths, IDs, offsets, and counts, never a stored string. The local
  adapter refuses a base URL without naming any part of it. Feedback shows a label
  only when it is `U<n>`.
- **The store (ES6).** `write_run` verifies every quote again before it writes, and
  pairs each core `Rejection` with its subject. `read_run` reads a run back record
  for record.
- **The suites, in the worktree.**
  - The default suite printed `1926 passed, 8 skipped, 25 deselected`. Plan B added
    178 collected tests, and the live test is the new deselected one. Its 8 skips
    are the local legs that need `data/`.
  - The harness suite printed `275 passed, 5 skipped`.
  - Ruff passed over 318 files. `uv lock --check` passed, and the lock's one change
    is the `local-model` extra.

### The roadmap's Exit, by test

| Clause | Tests |
| --- | --- |
| R5.1 and R6.2 | `test_extraction_run.py::test_a_mixed_scripted_run_over_the_fixtures` |
| R10.1 and R10.2 | `test_extraction_windows.py`: `test_the_stage_1_fixtures_hold_797_units_in_37_windows`, `test_every_unit_lies_in_exactly_one_window`, `test_every_eligible_element_holds_a_unit`, and `test_the_plan_reads_structure_and_lengths_never_text`; `test_extraction_run.py::test_citing_every_label_keeps_every_unit`; `test_import_scan.py::test_the_extractor_imports_no_retrieval_embedding_or_fuzzy_matching` |
| R14.6 | `test_extraction_cache.py`: `test_every_key_component_has_a_case`, `test_changing_one_key_component_misses`, 21 cases, and `test_an_identical_key_hits_and_calls_nothing` |
| R14.1 | `test_extraction_run.py::test_the_guard_blocks_and_records_every_connection`, and the mixed run under the same guard; `test_import_boundaries.py`; `test_import_scan.py::test_no_themes_module_imports_a_client_sdk_or_framework`; `test_extraction_local.py` |
| R14.7 and V11 | `test_extraction_injection.py`, 7 tests |
| GS13 | `test_import_boundaries.py::test_the_drafting_modules_import_nothing_from_the_extractor` |

Run by node ID in the worktree, they printed `74 passed`. `git diff --stat eb180cd --
config evaluation codebooks tests/fixtures` printed nothing.

### Deviations from the plan

The user ruled on each. Where the code differs from the plan's text, the code
governs.

- **F2 (Task 3, `f6c596a`).** `WindowRecord.attempts` and its data-dictionary row
  read "Dispatched attempts: requests, cache hits, and replay misses". The plan's
  text left out replay misses, which the extractor counts.
- **F4 (Tasks 1, 5, and 10).** Three of the plan's Interfaces lines were wrong, and
  its code governs: `narrative_home` takes `(bundle, span)`, an adapter's `identity`
  is a property, and `injection_bundle()` returns a `Synthetic`.
- **F6 (Task 1, `56ad223`).** The docstrings of `units.py`, `windows.py`, and
  `test_extraction_windows.py` say the plan never reads a unit's text, where the
  plan's text said it reads no text at all. `narrative_home`'s whitespace test of a
  container (ES9) reads text, and ranks and selects nothing (R10.2). This record
  says the same.
- **F9 (Task 9, `25dc5f0`).**
  `test_a_reply_that_is_not_a_completion_is_a_transport_error` also asserts that
  each refusal has a cause or suppresses its context, so its check that the cause
  quotes nothing cannot pass on a missing cause.
- **F3 (accepted).** The default suite imports httpx through `earnings-ingestion`,
  not the `local-model` extra (R14.1, above).
- **I3-1 (Task 3, `cb89b6d`).** `ExtractionRejection`'s `repr`, like its `str`,
  shows its IDs and reason only, never a label or a core rejection's detail. Its
  sentinel tests check `repr`, and `str` of a list, too.
- **I8-1 (Task 8, `a1d6e8d`).** Two validators in `extraction/records.py` name no
  stored value: `Quote`'s names the ID it expects, and `RunRecord`'s counts the
  unknown reasons. The store's sentinel test also plants its sentinel in a quote ID
  and in a run's rejection reason, and the round-trip test binds its result before
  asserting on it.
- **I9-1 (Task 9, `fb569fd` and `3ce2bf5`).** `loopback_url` also refuses a base URL
  that carries credentials, which httpx would send as Basic auth, one whose port is
  not a number from 0 to 65535, and one that does not parse. No refusal names any
  part of the URL. One new test holds the three cases.
- **I10-1 (Task 10, `35a1367`).** `injection_bundle()`'s docstring says the spoofing
  paragraph is built without sentences, so that one unit holds a line break. The
  plan's text said S1 left it unsplit, which S1 does not.
- **The final review.** The `code-reviewer` agent, on Opus, reviewed
  `eb180cd..e407a62` and found nothing Critical; Codex was skipped (P12-4). The user
  ruled to fix three of its items, with their polish, and to defer or drop the rest
  at Completion:
  - **I1 (`209387d`).** `CachedAdapter` reads a mode given as its value as its
    member, so `"replay"` never calls the model, and a misspelled mode refuses
    construction. One new test.
  - **m1 (`b6715de`).** `loopback_url` also refuses a base URL that holds
    surrounding whitespace or an ASCII control character, which urlsplit and httpx
    would read differently, so the URL it checks is the URL httpx sends. The
    module's docstring and the dictionary's `base_url` row name every refusal, the
    scheme's included. Two new cases, in the renamed
    `test_a_malformed_url_or_one_with_credentials_is_refused_naming_no_value`.
  - **Docs (`76fa5a4`).** `extract_window` and `extract_run` say that an error other
    than an `AdapterError` ends the run; the dictionary's `Claim` row says its ID is
    unique together with `doc_id`; and five docstrings close the review's gaps.
- **The counts.** I9-1's three cases and the final review's three tests are the only
  tests a ruling added. So plan B added 178 tests, not 172; the default suite passed
  1926, not 1920; and the node-ID run passed 74, not 69.

### The model (ADR 0004)

[GATE: the model, its runtime and version, its weights' SHA-256, and its license, as
ADR 0004 records them, with the ADR's path.]

### The live run

On [GATE: the date], the session ran the live test once, by its node ID, against
[GATE: the model ID] under [GATE: the runtime and its version]. It printed
`[GATE: the summary line]`, and its count line, `[GATE: the test's printed line]`.

### The main checkout

On [GATE: the date], the user ran the wording guard in the main checkout at plan B's
tip, `[GATE: the tip's short hash]`, on a detached HEAD, from a checkout with no
tracked change. It printed `[GATE: the summary line]`. [GATE: "No test failed.", or
each failure's node ID and exception type, with its fix's commit.]
