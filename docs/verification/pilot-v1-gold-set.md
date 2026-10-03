# Pilot v1's codebook, split, and gold set: verification record

This record verifies roadmap Stage 6, which
`specs/pilot-codebook-split-and-gold-set-protocol.md` specifies and plan 9
(`specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md`) built. Each gate
appends its section as it closes. The record holds IDs, counts, hashes, and dates,
never a release's wording or a paraphrase of it (GS3, GS13).

## The pin

- **The pilot.** Pilot v1, `config/corpus/djia-2024q3-2026q2/pilot-v1.json`,
  `djia-2024q3-2026q2-pilot`, content hash
  `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926`: 40 events over
  33 issuers.
- **The events.** Events v1, `events-v1.json` beside it, content hash
  `2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7`.
- **The universe.** Universe v1,
  `config/universe/djia/manifests/djia-2024q3-2026q2-v1.json`, operative hash
  `c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573`.
- **What Stage 6 sent.** No SEC request, and no model call from code. The drafting
  sessions are listed at the end.

## Gate 1: the split and the coverage report

- **The split.** `evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json`, split v1 by
  `issuer-time/1`, content hash
  `5c4a2f3c5ed9ffc2cf0065658ec4e75311220338cf9b3fe07802c0db9fcd0e53`.
  - 20 train, 8 dev, 7 test, and 5 excluded.
  - Each excluded event is the later event of an issuer the pilot holds in an
    earlier partition (`issuer_in_earlier_partition`): `cik-0000004962:2026-06-30`,
    `cik-0000320187:2026-05-31`, `cik-0000731766:2026-06-30`,
    `cik-0000732712:2026-03-31`, and `cik-0001403161:2026-06-30`.
  - Two of the pilot's three `membership_boundary` events are in train, and the
    third is excluded. No event is a Stage 1 fixture's (P9-15).
- **The coverage report.** `coverage-v1.json`, coverage v1, content hash
  `7b1d8b8a10fa837e686addc6a60d43803782cc418f377efeb24e215d903f4060`.
  - It reads runs `acquire-20260928T153046989675Z` and
    `acquire-20260928T153714715420Z`.
  - All 40 documents are `parsed`.
  - `unavailable`, `restricted`, and `failed` are coverage gaps (D4), never
    repaired by reselecting.
  - One override applies: `release-doc-dis-2026-03-28`, on
    `cik-0001744489:2026-03-28:release`, with the verdict `not_confirmed`.
  - The no-theme count joins at Stage 11 for train and dev, and at Stage 14 for
    test.
- **The user's review.** The user read both on 2026-09-29, and approved them.
- **Checks.** The rebuilt split and report reproduce both files byte for byte. The
  local legs printed `11 passed, 3 skipped`, and the wording guard `5 passed`.

## Gate 2: the backup

On 2026-09-29, the user confirmed that `data/` is backed up outside the
repository (GS12). The backup's location is the user's, and is not recorded. No
drafting session had started.

## The brief review

On 2026-09-29, the user reviewed both briefs before any drafting session
started (P9-6): `evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md` and
`gold.md`. Neither changed. After the review, the wording guard and the codebook
brief's test printed `6 passed`.

## Gate 3: codebook v0

- **The discovery corpus.** The 20 training events' parsed documents, which
  `briefs/codebook.md` lists, and no dev or test document (R9.2, R12.3, P9-16).
- **The drafting session.** On 2026-10-02, a fresh Claude Code session
  in the main checkout, running Claude Opus 5.5 (`claude-opus-5-5`), read
  `briefs/codebook.md`, the contracts it names, and the 20 training texts. It wrote
  `data/runs/gold/drafts/codebook.draft.toml`, which is kept, unchanged and
  uncommitted.
- **The revisions.** On 2026-10-03, three more Claude Code sessions changed the
  working copy, never the draft; ADR 0003 records their models and what they read.
  At the user's direction, the session running plan 9 applied the user's choices by
  script. A fresh revision session, given the brief and a revision prompt the user
  reviewed, read the 20 training texts and added `mix`, `tax`, and `impairments`,
  and a positive example each to `macro` and `regulation`. A review session made
  two edits the user authorized.
- **The user's edits.** The user chose each change, or the rule for making it, and
  reviewed the result, and ADR 0003's Context gives the account, which the user
  confirmed. `codebook freeze` printed no refusal after the plan 9 session's edits,
  and the revision session ran it until it printed none.
- **Blinding.** At the user's request, the session running plan 9 read the draft
  once, its example quotes from 18 training releases included, and later edited the
  working copy: two exceptions to GS13 the user authorized, which ADR 0003 records.
  It opened no training text under `data/runs/gold/texts/`, and no view or canonical
  document. No session read a dev or test document.
- **The freeze.** `codebooks/djia-pilot/codebook-v0.toml`: 22 themes and
  96 examples, content hash `635975d1ec952cf5719ea3b473870f96e7e3a52bc3015cc1ac5725aa80ec1e79`.
- **The approval.** Lowell Mason approved v0 on 2026-10-03 in
  `docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md`, which cites the hash.
  `codebook validate` printed `valid:`.
- **Checks.** The local legs printed `12 passed, 2 skipped`, and the wording guard
  `5 passed`. Before the approval, none of the record's 642 strings shared 40
  characters with any of the 40 pilot releases or Stage 1's 8 fixtures, and no
  passage was both a positive example and a hard negative of one theme.

## Gate 4: the curated hard negatives

- **The drafting session.** On 2026-10-03, a fresh session running
  Claude Opus 5.5 read `briefs/gold.md` and the texts of Stage 1's eight fixtures,
  and wrote `data/runs/gold/drafts/hard-negatives.draft.toml`.
- **The record.** `tests/fixtures/gold/hard-negatives.toml`, outside the pilot and in
  no partition (R12.5):
  - 8 fixtures and 29 hard negatives: `issuer` 4, `period` 13, and `section` 12;
  - origins: accepted 58, edited 0, rejected 0, and added 0;
  - signed on 2026-10-03, as `annotator = "Lowell Mason (verified a Claude draft)"`.
- **Checks.** `gold validate --hard-negatives` printed `valid:`, and the default suite
  now checks the record offline: `1742 passed, 2 skipped, 24 deselected`.

## Gate 5: three signed train bundles

The first three train events in the pilot's selection order (P9-7), chosen by order
before any text was read. Each was drafted in its own fresh session, anchored,
verified item by item, read whole for omissions, signed, validated, and committed
as `evaluation/djia-2024q3-2026q2/pilot-v1/gold/<event>.toml`, the event's ID with
its colon as an underscore (P9-3). The counting script in plan 9's Task 19, Step 8
counted them from the committed files, and each bundle's commit holds its
omission-pass and signing dates:

| Event | Release label | Quotes | Claims | Assignments | Hard negatives | `no_theme` | Accepted | Edited | Rejected | Added | Omission pass | Signed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cik-0000051143:2024-12-31` | `release` | 62 | 46 | 57 | 8 | `false` | 173 | 0 | 0 | 0 | 2026-10-03 | 2026-10-03 |
| `cik-0000093410:2025-03-31` | `release` | 56 | 40 | 62 | 13 | `false` | 171 | 0 | 0 | 0 | 2026-10-03 | 2026-10-03 |
| `cik-0000310158:2025-06-30` | `release` | 103 | 71 | 97 | 11 | `false` | 282 | 0 | 0 | 0 | 2026-10-03 | 2026-10-03 |
| **Total** | | 221 | 157 | 216 | 32 | | 626 | 0 | 0 | 0 | | |

Each is `train` and signed by the user; `gold validate` printed `valid:` for each,
and the gold leg passes. The accepted, edited, rejected, and added counts compare
each signed file with its kept draft (GS5).

## Drafting sessions

| Gate | Draft, under `data/runs/gold/drafts/` | Brief | Model | Date |
| --- | --- | --- | --- | --- |
| 3 | `codebook.draft.toml` | `codebook.md` | Claude Opus 5.5 (`claude-opus-5-5`) | 2026-10-02 |
| 4 | `hard-negatives.draft.toml` | `gold.md` | Claude Opus 5.5 (`claude-opus-5-5`) | 2026-10-03 |
| 5 | `cik-0000051143_2024-12-31.draft.toml` | `gold.md` | Claude Opus 5.5 (`claude-opus-5-5`) | 2026-10-03 |
| 5 | `cik-0000093410_2025-03-31.draft.toml` | `gold.md` | Claude Opus 5.5 (`claude-opus-5-5`) | 2026-10-03 |
| 5 | `cik-0000310158_2025-06-30.draft.toml` | `gold.md` | Claude Opus 5.5 (`claude-opus-5-5`) | 2026-10-03 |

- **Where they ran.** Each session was fresh, started by the user in the main
  checkout with its committed brief, and drafted one thing (P9-5). Gate 3's
  revision and review sessions changed the codebook's working copy, never a
  draft; the Gate 3 section and ADR 0003 describe them.
- **What never drafted.** Outside two exceptions the user authorized for codebook
  v0, the executing session and its subagents drafted nothing, and never read a
  draft, a working copy, a view, or a pilot text. The executing session read the
  codebook draft once, and applied the user's changes to the codebook's working
  copy by script, one synthetic hard negative in its own words included; the
  Gate 3 section and ADR 0003 record both. Implementer subagents on five tasks
  searched beyond their search rule, by finds, greps, or a listing of directory
  names, and none exposed pilot text.
- **The drafts.** They stay under `data/runs/gold/drafts/`, unchanged and
  uncommitted, for GS5's shares at Stage 11. `gold anchor --check`, which writes
  nothing, rebuilt each signed record from its kept draft with the committed
  counts.

## What was verified

| Item (S §Verification; 7 and 8 are plan 9's) | Evidence |
| --- | --- |
| 1. The split over the synthetic pilot and over pilot v1, reproducing `split-v1.json` | `test_each_issuer_keeps_the_partition_of_its_earliest_event`; `test_a_fixture_event_is_never_held_out`; `test_the_issuer_rule_comes_before_the_fixture_rule`; `test_the_order_of_the_input_changes_nothing`; `test_the_split_gives_the_spec_s_counts_and_exclusions`; `test_the_committed_split_reproduces_byte_for_byte` |
| 2. The split and the report leave the pilot unchanged (P-C7) | `test_the_split_changes_no_frozen_record`; `test_split_freezes_once_and_prints_only_ids_and_counts`; `test_coverage_counts_each_state_and_rereads_only_its_runs` |
| 3. The coverage report over the synthetic acquisition, with its non-zero classes | `test_the_synthetic_acquisition_is_counted_by_state`; `test_a_pilot_holding_no_failure_class_reports_three_gaps`; `test_a_rebuild_reads_only_the_runs_it_names` |
| 4. The codebook and gold contracts, the anchor, and the validator, with a tamper test for each refusal | `test_codebook.py`, `test_gold.py`, and `test_anchoring.py`, among them `test_a_tampered_version_is_refused`, `test_another_document_pin_split_codebook_or_partition_is_refused`, and `test_a_tampered_pointer_is_refused`; `test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors`; `test_curated_hard_negatives_over_stage_1_fixtures_validate`; `test_the_curated_hard_negatives_validate_offline` |
| 5. The wording guard's fixture leg | `test_no_stage_6_file_quotes_a_stage_1_fixture`; `test_a_copy_across_a_wrapped_line_is_caught` |
| 6. The local legs | `test_the_committed_coverage_report_reproduces_from_its_runs`; `test_committed_records_validate_against_the_local_store`; `test_no_stage_6_file_quotes_a_pilot_document`: `14 passed` |
| 7. Blinding (GS13) | `test_an_unforeseen_error_is_named_by_type_never_by_message`; `test_a_draft_that_is_not_toml_is_named_never_quoted`; `test_a_dev_or_test_bundle_waits_its_turn`; `test_no_text_is_written_for_an_excluded_event`; `test_a_file_that_is_not_toml_is_refused_by_position_only`; the CLI tests' `quiet` canary |
| 8. No model and no network in `earnings-themes` (R14.1) | `test_importing_earnings_themes_loads_nothing_forbidden`; `test_every_module_is_imported` |
| 9. The suites | The default suite, `1743 passed, 1 skipped, 24 deselected`; the harness suite, 280 passed; Ruff; `uv.lock` unchanged |

## Limitations

- **One annotator.** One person verified and signed every item, so inter-annotator
  agreement is not measurable (R12.6, D2).
- **One drafting model.** Every draft came from Claude Opus 5.5, and the user
  verified drafts rather than annotating from blank (GS4). A Claude model scored
  against this gold shares its drafter's family, and Stage 16 records that conflict
  for any Claude ceiling.
- **Three of 28.** Three train bundles are signed. The other 17 train and 8 dev
  bundles follow Task 19's procedure after this plan, and the 7 test bundles wait
  for Stage 14 (GS18).
- **No observed failure class.** All 40 documents are parsed, so `unavailable`,
  `restricted`, and `failed` are coverage gaps, not observed counts (D4).
- **Accepted as drafted.** The user accepted every drafted item unchanged: 626 in
  the three bundles, whose omission passes added none, and 58 in the curated hard
  negatives. Every edited, rejected, and added count is zero (GS5): each signed
  record holds exactly its draft's items.
