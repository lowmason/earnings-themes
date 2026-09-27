# DJIA earnings events and the pilot: verification record

This record verifies plan A of roadmap Stage 5: event discovery, eligibility, and the
freezes, which `specs/event-discovery-eligibility-and-acquisition.md` specifies. Plan 7
(`specs/plans/7-event-discovery-eligibility-and-acquisition-plan-a.md`) built it.
Plan B, which acquires the pilot's releases, adds its own sections.

## What was verified

| Item (S §Verification, plan A) | Evidence |
| --- | --- |
| 1. The prerequisites: machine-wide locks; the operative hash, with v1 loading unchanged; the acceptance-time record; two robustness fixes | `test_two_checkouts_share_one_lock`; `test_a_withheld_notice_changes_the_content_but_not_the_identity`; `test_a_refetched_sec_record_changes_the_content_but_not_the_identity`; `test_v1_loads_unchanged_and_has_an_operative_hash`; [`edgar-acceptance-time.md`](edgar-acceptance-time.md), with both legs; `test_a_malformed_registrant_is_refused_as_sec_data`; `test_retry_after_ignores_non_ascii_digits` |
| 2. Each reader refuses a changed shape | `test_malformed_items_are_refused`; `test_an_older_page_with_a_malformed_date_is_refused`; `test_a_page_of_another_shape_is_refused`; `test_facts_of_another_shape_are_refused` |
| 3. Acceptance time: both conventions, both daylight-saving seasons, and a mismatch that blocks | `test_the_accepted_value_is_eastern_wall_time`; `test_a_row_uses_one_convention_or_mismatches`; `test_a_row_in_neither_convention_is_a_blocking_mismatch` |
| 4. The discovery replay (R1.1, R1.2) | `test_each_release_is_identified_by_its_statements`; `test_the_preliminary_filing_is_dropped_and_the_gap_s_neighbor_too`; `test_exhibit_numbering_and_the_amendment`; `test_every_event_s_reason_before_any_override`; `test_the_layer_holds_what_discovery_fetches_and_no_filing_after_the_cutoff` |
| 5. No exhibit before the freeze (EV2), and only the shared client (R1.3, D5) | `test_discovery_requests_what_the_build_reads_and_never_an_exhibit`; `test_stage_5_has_no_client_or_throttle_of_its_own`; the live run below |
| 6. Slots (P-VF) | `test_two_securities_make_one_row_per_period`; `test_the_window_is_half_open`; `test_each_period_gap_case_blocks`; `test_an_issuer_without_a_slot_blocks`; `test_a_nike_like_calendar_trips_no_guard` |
| 7. Eligibility (P-C2, P-VF) | `test_the_bound_rules_in_winter`; `test_the_bound_rules_in_summer`; `test_every_reason_and_the_checks_order` |
| 8. The times and labels stay separate (R1.5, P-A5) | `test_an_eligible_row_keeps_every_time_and_label_apart`; `test_unknown_labels_stay_null_together`; `test_record_fields_stay_separate_and_unknown_labels_stay_null` |
| 9. The freeze | `test_the_freeze_refuses_and_names_each_reason`; `test_identical_content_is_the_same_version`; `test_a_refetch_with_the_same_facts_writes_nothing`; `test_a_changed_fact_writes_the_next_version` |
| 10. Selection (P-C5, P-VF) | `test_shuffled_input_gives_a_byte_identical_pilot`; `test_with_40_or_more_eligible_events_the_pilot_holds_exactly_40`; `test_the_event_count_guards`; `test_more_than_40_issuers_needs_a_scope_decision`; `test_mandatory_cases_beyond_the_target_refuse_before_filling`; `test_a_quarter_with_no_eligible_event_refuses` |
| 11. Invalidation (P-VF) | `test_a_moved_bound_changes_both`; `test_a_changed_mapping_changes_both`; `test_a_changed_interval_or_policy_changes_the_hash_and_a_version_alone_does_not`; `test_a_changed_event_fact_or_policy_reseeds_and_a_universe_version_does_not` |
| 12. P-VI | `test_p_vi_replays_offline_to_the_frozen_manifests`, under a socket guard with no identity set |
| 13. R14.5 | `test_stage_5_loads_no_acquisition_library`; `test_stage_5_imports_no_acquisition_library`; the R14.5 section below |
| 14. The suites | The default suite, 1293 passed and 24 deselected; the harness suite, 280 passed; Ruff; `uv.lock` unchanged |

## The frozen event manifest

- **The manifest.** `config/corpus/djia-2024q3-2026q2/events-v1.json`, content hash
  `2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7`, created
  2026-09-27T19:53:45.900695Z. It read the universe `djia-2024q3-2026q2` v1, whose
  operative hash is
  `c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573`, under
  `release-id/1` and `eligibility/1`.
- **The evidence record.** `events-v1.evidence.json`, 1,854,769 bytes. For each
  event it cites the periodic report and its labels, the release filing and its
  Accepted value, the Item 2.02 text, and each candidate. It also gives each file's
  convention and every retrieval time.
- **The events.** 263 events of 33 issuers:
  - 239 `eligible`, `member_at_publication`;
  - 24 `ineligible`, `not_member_at_publication`: seven each for Intel and Dow,
    after their exits; seven for Alphabet, before its entry; one each for NVIDIA
    and Sherwin-Williams, before their entries; and one for Verizon, after its
    exit.
- **Identification.** 241 events by `stated_period`, 10 by `sole_candidate`, and 12
  by `override`. Six slots had two candidates:
  - Boeing's for 2024-09-30, IBM's for 2026-06-30, and Nike's for 2026-05-31: the
    rule dropped the filing that calls its results preliminary;
  - Honeywell's for 2025-09-30: the rule dropped a recast of 2025-12-22 that states
    other periods;
  - Caterpillar's for 2024-09-30 and Honeywell's for 2026-03-31: the rule kept both
    filings, so each was `several_release_filings` until the review.

  Two more Item 2.02 8-Ks in range were passed over, since their index pages list
  no `EX-99*` exhibit: Goldman Sachs' `0000886982-26-000004` and Chevron's
  `0000093410-26-000108`.
- **Findings.** Two `fiscal_labels_unknown`, reported and never blocking:
  companyfacts holds no fact of Visa's or Dow's report for 2026-06-30, so those two
  events' fiscal labels stay null (EV6). No `period_gap`, `no_slots`, or
  acceptance-time finding arose.
- **The review.** Signed by Lowell Mason on 2026-09-27. Twelve events were
  `ambiguous` before the review, and each override is a `set_release_filing` that
  names one of the rule's candidates:
  - `release-cat-2024-09-30`: `cik-0000018230:2024-09-30`, `0000018230-24-000050`,
    from `several_release_filings`. "This is the press release for the quarter
    ended September 30, 2024."
  - `release-hon-2026-03-31`: `cik-0000773840:2026-03-31`, `0000773840-26-000055`,
    from `several_release_filings`. "This is the release filed before the
    spin-off."
  - JPMorgan's eight events, each from `no_release_filing` and each set to its only
    candidate, with one rationale: "These are the correct releases; fixed bad prose
    that would not select them."
    - `release-jpm-2024-09-30`: `cik-0000019617:2024-09-30`, `0000019617-24-000555`;
    - `release-jpm-2024-12-31`: `cik-0000019617:2024-12-31`, `0000019617-25-000040`;
    - `release-jpm-2025-03-31`: `cik-0000019617:2025-03-31`, `0000019617-25-000332`;
    - `release-jpm-2025-06-30`: `cik-0000019617:2025-06-30`, `0000019617-25-000518`;
    - `release-jpm-2025-09-30`: `cik-0000019617:2025-09-30`, `0001628280-25-044845`;
    - `release-jpm-2025-12-31`: `cik-0000019617:2025-12-31`, `0001628280-26-001902`;
    - `release-jpm-2026-03-31`: `cik-0000019617:2026-03-31`, `0001628280-26-024990`;
    - `release-jpm-2026-06-30`: `cik-0000019617:2026-06-30`, `0001628280-26-048078`.
  - `release-mmm-2024-09-30`: `cik-0000066740:2024-09-30`, `0000066740-24-000098`,
    from `no_release_filing`. "Correct release even though year wasn't given."
  - `release-vz-2024-12-31`: `cik-0000732712:2024-12-31`, `0000732712-25-000003`,
    from `no_release_filing`. "Only candidate."

  In the ten `no_release_filing` events, the rule had dropped the only candidate,
  the release itself, because each period it read in the Item 2.02 text was
  another one (see Limitations).

## The pilot

- **The manifest.** `config/corpus/djia-2024q3-2026q2/pilot-v1.json`, content hash
  `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926`, created
  2026-09-27T19:55:58.504040Z, with seed
  `fd4bd5429c7c01515f9efbe1fbfccb2107ce748e882021553a538e84518b9ee8`. It was drawn
  under `djia-pilot/1` from event manifest v1.
- **Its rows.** 40 of target 40: 33 `issuer_coverage`, 3 `membership_boundary`, and
  4 `longitudinal_fill`. No `quarter_coverage` row was needed.
- **Coverage.** By period end, 2024Q3 6, 2024Q4 6, 2025Q1 4, 2025Q2 4, 2025Q3 4,
  2025Q4 4, 2026Q1 5, and 2026Q2 7; and 33 of 33 eligible issuers.
- **Transitions.** v1 has six, all before the open: Intel's, Dow's, Sherwin-Williams',
  and NVIDIA's on 2024-11-08, and Verizon's and Alphabet's on 2026-06-29.
  Step 2 added three rows, each the nearest eligible event on its transition's
  member side: NVIDIA's release of 2024-11-20, for the quarter ended 2024-10-27,
  after its entry; Sherwin-Williams' of 2025-01-30, for 2024-12-31, after its
  entry; and Verizon's of 2026-04-27, for 2026-03-31, before its exit. Intel, Dow,
  and Alphabet each have one eligible event, which step 1 had already taken. No
  transition was reported.

## The requests

| Step | Client | Requests |
| --- | --- | --- |
| Planning, the format probe (P7-6), 2026-09-27 | SEC | 19, approved by the user: 16 primary documents and 3 companyfacts files, saved under `data/raw/events/`. They were sent under the per-checkout lock, before Task 1 made it machine-wide |
| Task 19, Step 3, `events discover` | SEC | 642 sent and 642 fetched, under the approved cap of 700: 63 submissions and companyfacts files; 314, then 10, then 0 older pages and index pages, over three passes; and 255 primary documents |
| Task 19, reruns | SEC | none |
| Task 20, `events discover --filing` | SEC | none |

No `-m live` test ran, and no exhibit was requested. No model was called, and no
billable service was used.

## Acceptance time

[`edgar-acceptance-time.md`](edgar-acceptance-time.md) gives both legs.
Leg 2, from Stage 5's own pages, cross-checked 305 rows in 43 files: all 305 are in
true UTC, and none in Eastern digits with `Z`. All 33 submissions files are in true
UTC. Every row
follows one of the two conventions, and no file follows both. So a filing's
acceptance time is its index page's Accepted value, and SEC's `acceptanceDateTime`
only cross-checks it (EV10).

## R14.5

Stage 5 uses no acquisition library. edgartools stays an unused optional extra, and
the readers are the package's own. So no library output reaches the ingestion
boundary, and there is nothing to cast. That is not R14.5 held vacuously: V1 found
that edgartools' table and filing paths return pandas or pyarrow objects, which would
need casts. `test_stage_5_loads_no_acquisition_library` checks each Stage 5 module at
runtime, and `test_stage_5_imports_no_acquisition_library` checks their source.

## Limitations

- **First publication is an upper bound** (EV9). `first_publication_time` is the
  release filing's EDGAR acceptance. A company that put its release on a newswire
  first published it earlier. For three events, the rule dropped an earlier Item
  2.02 8-K as preliminary, so `first_publication_time` is the later release's
  acceptance: Boeing's `0000012927-24-000067` of 2024-10-11, for 2024-09-30; IBM's
  `0000051143-26-000070` of 2026-07-14, for 2026-06-30; and Nike's
  `0000320187-26-000070` of 2026-06-23, for 2026-05-31.
- **Same-day ordering.** EDGAR alone cannot order a release against a membership
  change on the same day. None arose in v1.
- **`release-id/1` is fixed.** It reads a stated date only after "ended" or "ending"
  (P7-7). A case it gets wrong goes to review, and the rule changes only as
  `release-id/2`. Ten such cases went to review here. Its year-first quarter
  pattern needs "fiscal" before the year, so the quarter in JPMorgan's eight
  releases, written year first without it, was never read, while each release's
  prior-year comparison and older report dates were read and matched no slot. 3M's
  and Verizon's releases name their quarters in forms outside the rule's list.
- **Retrieved after the cutoff.** SEC's records were retrieved after 2026-09-22. The
  cutoff is enforced on each filing's acceptance date, never on its retrieval date
  (P-C4).
- **Cohort v1's content hash.** The `sec-edgar` register entry now names companyfacts
  (Task 16), and v1's content hash covers that entry. So a rebuild of the cohort no
  longer reproduces v1's content hash, and `earnings-pipeline cohort verify-live`
  reports the difference. Its operative hash, which Stage 5 keys on, is unchanged
  (P7-3).
- **One machine.** The SEC and web client locks coordinate one machine's processes.
  Stage 1's harness client keeps its own lock, so it must never run live beside a
  package client.
