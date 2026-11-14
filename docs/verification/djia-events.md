# DJIA earnings events and the pilot: verification record

This record verifies plan A of roadmap Stage 5: event discovery, eligibility, and the
freezes, which `specs/completed/event-discovery-eligibility-and-acquisition.md` specifies. Plan 7
(`specs/plans/completed/7-event-discovery-eligibility-and-acquisition-plan-a.md`) built it.
Plan B, which acquired the pilot's releases, has its own sections, from "Plan B:
acquisition and processing states" on.

## What was verified

| Item (S §Verification, plan A) | Evidence |
| --- | --- |
| 1. The prerequisites: machine-wide locks; the operative hash, with v1 loading unchanged; the acceptance-time record; two robustness fixes | `test_two_checkouts_share_one_lock`; `test_a_withheld_notice_changes_the_content_but_not_the_identity`; `test_a_refetched_sec_record_changes_the_content_but_not_the_identity`; `test_v1_loads_unchanged_and_has_an_operative_hash`; [`edgar-acceptance-time.md`](edgar-acceptance-time.md), with both legs; `test_a_malformed_registrant_is_refused_as_sec_data`; `test_retry_after_ignores_non_ascii_digits` |
| 2. Each reader refuses a changed shape | `test_malformed_items_are_refused`; `test_an_older_page_with_a_malformed_date_is_refused`; `test_a_page_of_another_shape_is_refused`; `test_facts_of_another_shape_are_refused` |
| 3. Acceptance time: both conventions, both daylight-saving seasons, and a mismatch that blocks | `test_the_accepted_value_is_eastern_wall_time`; `test_a_row_uses_one_convention_or_mismatches`; `test_a_row_in_neither_convention_is_a_blocking_mismatch` |
| 4. The discovery replay (R1.1, R1.2) | `test_each_release_is_identified_by_its_statements`; `test_the_preliminary_filing_is_dropped_and_the_gap_s_neighbor_too`; `test_exhibit_numbering_and_the_amendment`; `test_every_event_s_reason_before_any_override`; `test_the_layer_holds_what_discovery_fetches_and_no_filing_after_the_cutoff` |
| 5. No exhibit before the freeze (EV2), and only the shared client (R1.3, D5) | `test_discovery_requests_what_the_build_reads_and_never_an_exhibit`; `test_stage_5_has_no_client_or_throttle_of_its_own`; `test_stage_5_opens_no_client_of_its_own`; the live run below |
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
- **A fresh store** (EV11). Each of the 12 overrides cites an index page by its
  artifact hash and a locator, and the manifest hashes each override whole, with its
  citations. `data/raw/events/` is never committed, so a rebuild on another machine,
  or from a fresh discovery, finds a cited page only if SEC serves the same bytes. If
  it serves other bytes, even with the same `walker-1` text, the build refuses that
  override until it is re-cited, and the re-cited override changes the content hash:
  a new events version and a re-seeded pilot, though no fact changed. The committed v1
  files load without the store. Hashing only an override's decision fields, or giving
  the event manifest an operative identity, would close this, under a new events
  version (`specs/deferred_items.md`).
- **What the evidence record cites for a candidate** (Codex's fifth review of PR #6).
  As the Stage 5 spec's evidence list and P7-15 have it, `events-v1.evidence.json`
  cites each candidate by its index page at its Accepted value, and the Item 2.02 text
  of the release alone. So in the six two-candidate events, no hash pins the other
  candidate's primary document: Boeing's `0000012927-24-000067`, IBM's
  `0000051143-26-000070`, and Nike's `0000320187-26-000070`, each dropped as
  preliminary; Honeywell's `0000773840-25-000125`, dropped as stating another period;
  and Caterpillar's `0000018230-24-000047` and Honeywell's `0000773840-26-000084`,
  which the rule kept and the review's overrides did not choose. The two 8-Ks passed
  over for want of an `EX-99*` exhibit, above, are in neither JSON file. These
  decisions are recorded only here. A replay of the pinned rule over re-fetched pages
  can re-derive them, but it cannot show that a re-fetched document is the one the
  rule read. The evidence record is never replaced, so a later events version carries
  these citations (`specs/deferred_items.md`).
- **One machine.** The SEC and web client locks coordinate one machine's processes.
  Stage 1's harness client keeps its own lock, so it must never run live beside a
  package client.

## Plan B: acquisition and processing states

Plan 8 (`specs/plans/completed/8-event-discovery-eligibility-and-acquisition-plan-b.md`) built
plan B of the Stage 5 spec: the processing states, R1.2's exhibit choice,
`release-content/1`, acquisition through the shared SEC client, and
`earnings-pipeline events acquire`. It then acquired the pilot's releases.

### What was verified (plan B)

| Item (S §Verification, plan B) | Evidence |
| --- | --- |
| 1. `events acquire` refuses without a frozen pilot whose chain checks | `test_acquire_refuses_without_a_pilot_over_the_current_manifest`; `test_acquire_refuses_a_pilot_djia_pilot_1_does_not_reselect`; `test_a_pilot_not_frozen_over_the_manifest_is_refused`; `test_loading_selects_again`; `test_the_build_decides_which_version_is_current` |
| 2. Exhibit choice and confirmation: `EX-99`, `EX-99.1`, and `EX-99.01`; a narrative-only release; a first choice that fails and a next exhibit that confirms; the AMC-like overview, which fails | `test_each_numbering_is_named`; `test_plan_b_s_exhibit_numbering`; `test_the_narrative_release_has_no_table`; `test_named_exhibits_come_first_by_sequence`; `test_an_overview_that_announces_nothing_is_not_confirmed`; `test_each_case_comes_to_its_state` |
| 3. Every R1.4 state from fixtures, each expected but absent document with its `missing_reason` | `test_every_state_is_represented_from_fixtures`; `test_a_state_carries_its_own_details`; `test_only_the_transitions_r1_4_allows`; `test_a_history_must_chain` |
| 4. P-C7: the frozen records unchanged, and every selected event still selected, after acquisition, a failed parse, and later stages' states | `test_acquisition_changes_no_frozen_record_and_the_build_still_decides`; `test_p_vi_replays_the_acquisition_offline`; after the live run, the rebuild below |
| 5. Only the shared client, with no throttle of its own; a persistent 403 stops the run and leaves the rest `expected` | `test_stage_5_opens_no_client_of_its_own`; `test_stage_5_has_no_client_or_throttle_of_its_own`; `test_acquire_fetches_through_the_shared_client_within_its_count`; `test_a_persistent_403_stops_the_run_and_leaves_the_rest_expected`; `test_acquire_stops_on_a_persistent_403_and_leaves_the_rest_expected` |
| 6. Offline replay reproduces the states | `test_p_vi_replays_the_acquisition_offline`, on the synthetic store; `test_offline_replay_reproduces_the_live_acquisition`, on the real store |
| 7. The suites | The default suite, 1544 passed, 1 skipped, 24 deselected, after the final review's fixes; the harness suite, 280 passed; Ruff; `uv.lock` unchanged |

### Before any acquisition

The deferred items from PR #6's review that named plan B landed first (plan 8,
P8-2): a relative lock directory is refused (F29); a redirected response is refused
when fetched and when read (F13); a primary document with no Item line reads as
unread; an index page must agree with its submissions row (F12); every fetching
command refuses a store outside `data/raw` (F19, F38); every stop prints its request
count, and `cohort fetch-sec` and `verify-live` take an approved count (F31, F35);
two frozen versions of one content are refused (F22); and
`tests/integration/test_corpus_quotes.py` checks that no committed record quotes a
saved page (F20). Two were the user's design choices:

- **The build decides which frozen version is current** (F4). `events select` and
  `events acquire` read the event manifest whose content hash the rebuild
  reproduces, and the pilot frozen over it. The spec's §Commands records the rule.
- **Loading a pilot selects it again** (F10). `djia-pilot/1` over the pilot's event
  manifest and universe must reproduce its content hash.

Plan 25 recovered a saved response that is present but unusable (P2.1 and P2.2, two
review items from PR #6). "Repairing the store" below gives its commands.

### The acquisition

- **What it read.** events v1, content hash
  `2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7`, and pilot v1,
  `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926`, which
  `events acquire` printed before it sent anything.
- **The runs.** Two, both on 2026-09-28, under `data/runs/events/states/`:
  - `acquire-20260928T153046989675Z.parquet`, the first acquisition: 120 transitions,
    `expected` for each of the 40 documents, then each one's attempt. It ended
    `parsed 39, unavailable 1`, and exited 0 with no `problem:` line.
  - `acquire-20260928T153714715420Z.parquet`, the override's acquisition: 2
    transitions, which took Disney's release from `unavailable` through `acquired` to
    `parsed` under `release-doc-dis-2026-03-28`. Its exhibit was already saved, so
    `events acquire` stated "nothing to fetch; the client stays closed" and ran
    offline.
- **The states.** `parsed 40`, of the pilot's 40 release documents. Their canonical
  documents are under `data/runs/events/canonical/`, named by `doc_id`.
- **Exhibit choice.** The first run tried one exhibit for each document, its first
  choice in R1.2's order: 37 `named` and 3 `lowest_sequence`, as P8-8 predicted.
  `release-content/1` confirmed 39 of the 40 first choices, 36 `named` and 3
  `lowest_sequence`, so no document needed a later exhibit. The one it did not
  confirm was its filing's only `EX-99` exhibit.
- **Documents not parsed.** After the first run, one:
  - #26, `cik-0001744489:2026-03-28:release` (Disney, the quarter ended 2026-03-28),
    `unavailable, no_confirmed_release`. Release filing `0001744489-26-000036`;
    `EX-99.1 fy2026_q2xprxex991.htm (named), not_confirmed: its opening announces no
    results`. The index page describes the exhibit as the earnings release, Item
    2.02 names it, and its text states the period, but it is written as a letter to
    shareholders, so its first 12 blocks hold no verb-then-results phrase. The review
    named it in an override, and the override's acquisition parsed it.

  None remains.
- **Overrides.** One, in
  `config/corpus/djia-2024q3-2026q2/acquisition-overrides.toml`:
  `release-doc-dis-2026-03-28`, for `cik-0001744489:2026-03-28`, naming
  `fy2026_q2xprxex991.htm` of the frozen release filing `0001744489-26-000036`, and
  citing that filing's index page at its Accepted value. Its rationale, as signed:
  "Misstated as shareholder letter". Signed by Lowell Mason, 2026-09-28. It marked
  no `corpus_error`, since it names the frozen filing. The attempt keeps
  `release-content/1`'s verdict, `not_confirmed`, and the reviewer's decision stands
  (P8-11).
- **Replay.** `test_offline_replay_reproduces_the_live_acquisition` acquired again
  from the saved store, refusing every exhibit that was never saved, as SEC refused
  it, and reproduced each document's state (SV 6).
- **P-C7.** After acquisition, `events build` still reproduced events v1's content
  hash, and no frozen record changed: acquisition writes only under `data/`.

### The requests (plan B)

| Step | Client | Requests |
| --- | --- | --- |
| Plan 8, Task 20, `events acquire --max-requests 56` | SEC | 40 sent and 40 fetched, under the approved cap of 56, of the stated 56 and 40 first choices |
| Plan 8, Task 20, reruns | SEC | None: the run did not stop |
| Plan 8, Task 21, `events discover --filing` | SEC | None: the override names the frozen filing, whose index page was saved |
| Plan 8, Task 21, the overrides' acquisition | SEC | None: its exhibit was saved, so `events acquire` stated nothing to fetch and never opened the client |

No `-m live` test ran. No model was called, and no billable service was used.

### Repairing the store

Discovery and acquisition never fetch a response they have saved, and the store is
append-only. The store keeps each response's bytes in an artifact file, named by the
SHA-256 of the bytes. It keeps one retrieval record, a small JSON file, for each
fetch. A saved response can become unusable, which means a reader cannot use it. Its
`problem:` line then names the command that repairs it. Plan 25 added two counted
refetch commands for this. A manual route remains for the damage they do not reach.

**Three kinds of damage.** Only the second is quarantined.

- **Bytes gone.** The retrieval record exists, but the artifact file does not. A
  refetch saves the URL again, and the save writes a file for the bytes it gets.
- **Bytes changed.** The file no longer hashes to its name. The store meets this when
  a refetch returns bytes whose hash is that name. It moves the damaged bytes into
  `quarantine/`, and then writes the file again.
- **Bytes valid, but a reader refuses them.** An example is an index page for another
  accession. The store never moves a valid file. A refetch saves a newer retrieval of
  the URL, and `SavedResponses` reads the newest retrieval of each URL.

**Where damaged bytes go.** The store moves them to
`<source>/quarantine/<artifact SHA-256>/<damaged bytes' SHA-256><extension>`.
`<source>` is the artifact's source directory, `<root>/<source_id>`. In the events
store that is `data/raw/events/sec-edgar`, so the damaged bytes sit under
`data/raw/events/sec-edgar/quarantine/`. The folder sits inside the source directory
because `os.link` needs one filesystem. The store links the bytes at the new name
before it unlinks the old one, so the bytes always have a name. It never deletes
damaged bytes, and it keeps the same damage once. No reader looks in `quarantine/`.

The store syncs each new file to disk before it links the file into place. It does not
sync directory entries. A lost entry leaves a missing file, not a damaged one, and that
is the "bytes gone" case.

**The two refetch commands.** Each takes `--refetch URL` once for each URL.

- `events discover --refetch URL` accepts a saved response that discovery reads and
  cannot use. That means a submissions file, an older page, a companyfacts file, and
  the index page or primary document of a filing that discovery reads. A submissions
  file brings every older page saved for its issuer, because a damaged file cannot
  list them. It runs no discovery phase, so it fetches nothing that a refetched file
  now lists.
- `events acquire --refetch URL` accepts a saved exhibit that a run would try and
  cannot read. Discovery never fetches an exhibit (EV2, a rule of the Stage 5 spec),
  so only this command refetches one.

Each command states its count first, and it refuses before it opens the client. It
refuses a URL that is not unusable: a response that reads, or one that is not saved.
So a refetch never replaces a usable response under a frozen citation. The refetch
needs `--max-requests`, the count the user approved. That count is the client's cap,
and each retry counts against it.

1. Run the command with each `--refetch URL`, and without `--max-requests`. It prints
   its count, and then it refuses. It sends no request.
   - `discover` prints `refetch: N requests to SEC, through the shared client`, and
     then each URL.
   - `acquire` prints `at most N requests to SEC, through the shared client; M first
     choices`, and then a `refetch:` line for each URL. Its N counts the whole run:
     every exhibit that is not saved, and each exhibit that `--refetch` names.
2. Get the count approved. Run the command again with `--max-requests` set to it.
3. Read the output. Each `quarantined: PATH` line names a damaged file that the run
   moved. Each `problem:` line names a saved response that is still unusable, and the
   command then exits 1.
4. After `discover --refetch` of a submissions file, run a plain
   `events discover --max-requests N`. The refetch runs no discovery phase, so the
   refreshed file may list filings that are not saved. That run needs its own
   approved count.
5. On `discover --refetch`, a `changed: URL` line means the URL returned other bytes
   than any earlier retrieval of it. Run `events build`, and compare its content hash
   with the frozen one before you rely on the response. `acquire --refetch` prints no
   `changed:` line, because `events build` never reads an exhibit.

A refetch that returns other bytes saves them under a new name. The damaged file stays
where it is, and nothing is quarantined. A frozen record that cites the old bytes by
hash stays broken. The problem line says so.

**A refetch that stops.** A persistent 403, a spent count, or a full disk stops the
run. Every stop prints a line that begins `requests sent: N`, and then a `Stopped:`
line. Before them, `discover --refetch` prints the `quarantined:` and `changed:` lines
for what it saved first. `acquire --refetch` prints its `quarantined:` lines.

**A Ctrl-C.** It prints the `requests sent: N` line too. `acquire --refetch` still
prints its `quarantined:` lines. `discover --refetch` prints no `quarantined:` or
`changed:` line. After a Ctrl-C of `discover --refetch`, run `events build`, compare
its content hash with the frozen one, and look in `quarantine/`.

After any stop or Ctrl-C, each URL that the run saved reads again, and a rerun refuses
it. A rerun may name only the URLs or exhibits that are still unusable.

**The manual route.** Three kinds of damage have no `--refetch`:

- **(a) A damaged retrieval record.** A record that cannot be read stops each command
  that reads it, with a validation error that names no file. The events store stops
  with that error. In the cohort store, `cohort build` prints it as a `problem:` line.
  The URL inside the record is unknown, so no refetch can name it.
- **(b) The cohort store.** `cohort fetch-sec` fetches each filed N-PORT document once.
  It stops with a `Stopped:` line when a saved one is gone or changed. The line names
  the artifact's SHA-256 and no URL.
- **(c) A response of a filing that discovery does not read.** That means an
  override's index page, and the index page or primary document of a filing that a
  `set_release_filing` override named, such as a filing without Item 2.02. Their
  problem lines name `events discover --refetch`, but it refuses them and points here.

The manual repair moves damaged files out of the store, and never deletes one. A
damaged retrieval record moves. An artifact moves only if its bytes are damaged. A
valid artifact stays where it is, even when other URLs share it.

`<source>` is a source directory of the store. The events store has one,
`data/raw/events/sec-edgar/`. The cohort store has one for each source, such as
`data/raw/cohort/sec-edgar/` and `data/raw/cohort/dia-nport/`, which holds the fund's
N-PORT documents.

1. Find the damaged files.
   - For (c), list the response's retrieval records by its URL:
     `grep -l '"request_url":"<URL>"' <source>/retrievals/*/*.json`.
   - For (a), the URL is unknown. A record's name ends with the first 12 hex digits of
     its own SHA-256. Set `<store>` to `data/raw/events` or `data/raw/cohort`, the
     store whose command stopped. This lists each record whose name does not match:

     ```bash
     for f in <store>/*/retrievals/*/*.json; do
       name=${f##*-}
       [ "$(shasum -a 256 "$f" | cut -c1-12)" = "${name%.json}" ] || echo "$f"
     done
     ```

   - For (b), the `Stopped:` line names the artifact's SHA-256, `<sha256>`. The line
     is `no artifact <sha256> for source 'dia-nport': its retrieval records remain, but
     its bytes are gone`, or `<path>/<sha256>.xml no longer hashes to its name`. The
     records are the files in `<source>/retrievals/<sha256>/`.
   - To tell whether an artifact is damaged, run
     `shasum -a 256 <source>/<sha256>.<extension>`. A different digest means damaged
     bytes. A missing file means the bytes are gone.
2. Move the record files that step 1 found from `<source>/retrievals/<sha256>/` to
   `<source>/quarantine/manual-<date>/`. Leave the directory's other records in place.
   For (a), move the damaged record file alone. Move the artifact
   `<sha256>.<extension>` there too, only if its bytes no longer hash to its name. A
   missing artifact needs no move. A URL with no record left is unsaved, and a rerun
   fetches it.
3. Rerun the command that stopped, at a count the user approved:
   - For (a) in the events store, run `events build`. Each
     `nothing saved from <URL>: run events discover` line names a URL that a rerun
     fetches. Plain `events discover` prints only the cap you give it, and then it
     sends. The user approves N from those lines, and then you run
     `events discover --max-requests N`. `events acquire` does state its count first.
     For an exhibit, rerun it, and its stated count now includes the URL.
   - For (a) in the cohort store, rerun the command that saves the source of the
     moved record. `cohort fetch-sec --max-requests N` saves `sec-edgar` and
     `dia-nport`. `cohort fetch SOURCE_ID URL` fetches a page of a registered source.
     `cohort register SOURCE_ID FILE --url URL` saves a page that a person saved in a
     browser. `docs/membership-source-register.toml` says which route each source
     takes. It fetches `wikipedia-djia`, and a person saves `spdji-announcements`
     notices. Then run `cohort build`. For `sec-edgar` and `dia-nport`, it names each
     URL that is still unsaved, as `nothing saved from <url> for <source>`. It reads
     `wikipedia-djia` and `spdji-announcements` pages by hash. For those, it prints
     `no artifact <sha256> for source '<source>' under <root>`, which names no URL.
     The URL to pass is the `url` beside that `artifact_sha256` in
     `config/universe/djia/evidence.toml` or `overrides.toml`.
   - For (b), run `cohort fetch-sec --max-requests N`. It fetches the ticker list,
     every submissions file, and the fund's older pages again, so N is larger than one
     document. The user approves N. The command states no count first.
   - For (c), run `events discover --filing <cik> <accession>`, with the issuer's
     10-digit CIK, as the universe manifest spells it. `<accession>` is the dashed
     form, `<10 digits>-<2 digits>-<6 digits>`. The command has no dry run, unlike
     `--refetch`. It sends as soon as it runs, so the user approves its 2 requests
     first. It fetches whichever of the index page and the 8-K document is now
     unsaved. It takes `--max-requests` only to lower that cap.
4. Run the build, `events build` or `cohort build`, and compare its content hash with
   the frozen one.

No repair was needed in plan 8's runs.

Plan 25 sent no request. Its approved request count was 0. The first live use of
`--refetch` is a Stage 15 gate (Stage 15 is the full eight-quarter run). It runs at the
count that the command states first.

### Limitations (plan B)

- **`release-content/1` is fixed.** Its vocabulary came from Stage 1's 168 saved
  exhibits, where it rejects the six that are not releases and misses six of the 162
  releases, whose openings announce nothing the pattern reads. A release it misses
  is `unavailable` with `no_confirmed_release` until a reviewed override names it,
  and the rule changes only as `release-content/2`. It missed one of the pilot's 40
  releases: Disney's for the quarter ended 2026-03-28, written as a letter to
  shareholders, which the reviewed override names.
- **Exhibits only.** Acquisition saves exhibits, never an index page or a primary
  document, so the event build reads what it read before.
- **The first count is pinned once.** `test_the_first_acquisition_sends_40_to_56_requests`
  pins the gate's count, and skips once an acquisition run is saved. This record keeps
  the count.
- **`restricted` is represented by fixtures only.** SEC documents are public, so no
  real document is `restricted`. `partial`, `completed`, and `completed-no-theme`
  wait for later stages.
