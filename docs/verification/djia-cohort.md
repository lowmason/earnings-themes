# The point-in-time DJIA cohort: verification record

This record verifies roadmap Stage 4, the point-in-time DJIA cohort, which
`specs/point-in-time-djia-cohort.md` specifies. Plan 6
(`specs/plans/completed/6-point-in-time-djia-cohort.md`) built it.

## What was verified

| Exit clause | Evidence |
| --- | --- |
| Every interval rests on source evidence; every CIK is 10 characters (P-A4) | `test_every_interval_rests_on_supported_evidence`; `test_every_resolved_cik_is_ten_digits_and_one_issuer_per_cik`; the real manifest's load check (Task 17, Step 12) |
| Intervals from an anchor plus changes; inclusive starts, exclusive ends, open intervals (P-VF) | `test_anchor_additions_and_removals_make_half_open_intervals`; `test_intervals_are_half_open` |
| A missing anchor refuses the freeze with its reason; conflicts stay separate and hold it until review | `test_a_missing_anchor_refuses_the_freeze_with_its_reason`; `test_conflicting_dates_stay_separate_and_hold_until_one_is_rejected`; `test_before_review_its_findings_hold_the_freeze` |
| The report lists every conflict and gap (P-A4) | `test_every_break_in_the_sequence_is_a_conflict`; `test_every_uncorroborated_quarter_is_a_gap`; the real report below |
| Evidence published after the cutoff changes no interval, mapping, count, or candidate issuer (P-C4); it is still recorded, as withheld, so a refreeze that includes it makes a new version with the same facts (see Limitations) | `test_evidence_published_after_the_cutoff_is_withheld`; `test_a_row_published_after_the_cutoff_never_changes_an_identity` |
| No snapshot backdated; no ETF holdings treated as the roster | `test_a_later_snapshot_is_never_backdated_into_the_anchor`; `test_fund_holdings_are_never_the_roster` |
| Ticker changes and multiple securities preserved; one issuer row per issuer (P-VF) | `test_a_ticker_change_keeps_both_identities_and_resolves_once`; `test_two_securities_of_one_issuer_derive_one_issuer_row` |
| Access and redistribution recorded for every source; unclear rights stay local | `docs/membership-source-register.toml`; `test_the_manifest_records_rights_for_every_source_it_cites`; `test_saved_evidence_stays_local_and_the_fixture_is_committed` |
| Frozen with a version and hash, atomically; refused on unresolved identity unless retained and excluded | `test_identical_content_keeps_its_version`; `test_a_tampered_manifest_is_refused`; `test_a_written_file_is_never_replaced`; `test_a_retained_unresolved_security_is_excluded_and_the_freeze_proceeds` |
| No network, proprietary roster, or credential by default; `live` opt-in and recorded (P-VL) | `test_saved_evidence_replays_to_the_frozen_manifest`, under a socket guard; `test_the_offline_cohort_path_loads_no_network_client`; the live run below |
| Workers share 2 req/s through the SEC client; a persistent 403 stops without a new identity (R1.3, D5) | `test_concurrent_workers_stay_at_or_below_two_requests_per_second`; `test_a_persistent_403_stops_without_rotating_identity`; `test_one_client_per_machine` |

## The frozen cohort

- **The manifest.** `config/universe/djia/manifests/djia-2024q3-2026q2-v1.json`,
  content hash `2d9743945dc5748fccec4c4963f6fa891a41e8863d56e99841569ff25fa884b4`,
  created `2026-09-26T22:54:39.381766Z`.
- **The anchor.** `wikipedia-rev-1230712338`, Wikipedia revision `1230712338`, saved
  2024-06-24. It was fetched through the web client on 2026-09-26.
- **The changes.** One line each:
  - `spdji-2024-11-01`, announced 2024-11-01, effective 2024-11-08 before the open:
    added `nvidia-common` and `sherwin-williams-common`; removed `intel-common` and
    `dow-common`; a PDF notice saved by hand.
  - `spdji-2026-06-23`, announced 2026-06-23, effective 2026-06-29 before the open:
    added `alphabet-common`; removed `verizon-common`; a PDF notice saved by hand.

  Both notices are cited through `pdftext-1`. The user supplied three other S&P DJI
  notices, and none states a DJIA change in the window, so none is curated: 3M's
  spin-off, announced before the window; Honeywell's spin-off, which leaves it in
  the index; and a Transportation Average change. The June 2026 notice also keeps
  Honeywell in the index under a new name, which changes no membership.

  `alphabet-common` follows Task 17's rule for share classes: the cited notice names
  no class, so the ID ends in `-common`, although GOOGL is Alphabet's Class A stock.
  A Class C listing (GOOG) would need an ID of its own, and this one cannot be
  renamed without a new version.
- **Size.** 33 intervals over 33 securities, and 33 candidate issuers.
- **Corroboration.** Nine of the fund's N-PORT reports were compared, dated
  2024-07-31 through 2026-07-31, one for each quarter of the fund's fiscal year.
  Each held all 30 members of the reconstructed roster on its date, IBM through
  `alias-ibm`. None was superseded by an amendment or withheld: the last was filed
  2026-09-18, before the cutoff. The report found no gap. Quarterly holdings place
  each change within a quarter, and only the notices date it. The user's end-state
  list, as of 2026-09-22, matched all 30 by ticker. It was published after the
  cutoff, so it is withheld: reported, and never applied.
- **The review.** Signed by Lowell Mason:
  - `ibm-issuer`, `set_issuer`, `ibm-common` to CIK `0000051143`: SEC's record for
    that CIK lists the ticker IBM, International Business Machines Corp's short
    name.
  - `alias-ibm`, `holding_alias`, `ibm-common` for the fund's holding International
    Business Machines Corp: the fund lists IBM under its legal name.
- **At the freeze.** `identity:ibm-common`, resolved by `ibm-issuer`, and
  `withheld:user-list-2026-09-26`, noted. The first build's nine
  `difference:dia-nport:<accession>` findings, one for each report and all IBM's,
  no longer arise once `alias-ibm` matches the holding.

## The format probe and the requests

| Step | Client | Requests |
| --- | --- | --- |
| Task 5, the format probe | SEC | 4, with the user's approval: `1 passed`, and nothing saved |
| The PDF spike, while `specs/completed/pdf-citation-text.md` was designed | uv, outside the lockfile | pypdf 6.19.0 and pdfminer.six 20260107, run from uv's cache; no project file changed |
| The replay of Task 16b, while the amendment was planned | uv, to PyPI | one `uv add`, approved by the user: `Resolved 152 packages` and `+ pypdf==6.19.0`; the tree was then restored, offline |
| Task 16b, Step 3, the `uv add` of `pypdf==6.19.0` | uv, to PyPI | `Resolved 152 packages`, then `+ pypdf==6.19.0`, installed beside the rebuilt `earnings-ingestion` |
| Task 17, Step 2, the terms pages | web and SEC | Wikimedia's: about 2 web requests (robots.txt and the page), run by the user. SEC's: 1. S&P Global's: 2 web requests, both answered 403 at robots.txt, so the user saved the page in a browser and `cohort terms --saved` hashed it, with no request |
| Task 17, Step 4, the evidence pages | web | 2: `en.wikipedia.org`'s robots.txt and revision 1230712338. Saved by hand, with no request: S&P DJI's notices `1475162` and `1484126`, both PDFs |
| Task 17, Step 7, `fetch-sec` | SEC | 44: the ticker list, 34 submissions records (33 companies and the fund), and 9 N-PORT reports |
| Task 18, Step 1, `verify-live` | web and SEC | 3: SEC's terms page, and S&P Global's robots.txt twice, a 403 each time; the web client then sent nothing more |

At planning, before this plan existed, one run of the probe reached SEC by accident.
`EDGAR_IDENTITY` was set, and a `-m live` run meant to confirm the skip sent about
five requests before failing on a bug. It saved nothing.

## The live verification

2026-09-26: 1 `unchanged`, 1 `refused`, 4 `failed`, and none `changed`.

- SEC's terms page, for `dia-nport`, was unchanged.
- S&P Global's terms page, `https://www.spglobal.com/en/terms-of-use`, was refused.
  Its host answered `robots.txt` with a 403 that persisted, as at Task 17, so the
  web client stopped without changing identity (P6-20). Nothing was retried.
- The four later checks on that client were not requested, so each reads `failed`:
  Wikimedia's terms page, both S&P DJI notices, and the Wikipedia anchor.

The rebuilt content hash equals the frozen one. The record is under
`data/runs/cohort/live/`, local and uncommitted.

## Limitations

- **The report's own.** The manifest's `report.limitations`:
  - the anchor's date bounds each anchored start from below;
  - fund holdings are an ETF proxy;
  - SEC's identity records were retrieved after the cutoff;
  - intervals are resolved to the day.
- **One machine.** The SEC and web client locks live in the user's cache directory,
  outside every checkout (plan 7, which moved them from each checkout's `data/runs/`),
  so every worktree and clone on a machine shares them. A lock coordinates one
  machine's processes and no more. Stage 1's harness client keeps its own lock, so it
  must never run live beside a package client.
- **`acceptanceDateTime`.** The readers take SEC's offset as written, and Stage 4
  uses it only to order filings of one fund. Stage 5 found that SEC writes it in
  two conventions, one per file, and takes a filing's acceptance time from its
  index page instead (plan 7; `docs/verification/edgar-acceptance-time.md`).
- **Secondary anchor.** A Wikipedia revision can lag or err. The official changes
  and the fund's holdings check it, and each disagreement was reviewed.
- **`pdftext-1`.** It has no OCR, so a PDF without a text layer cannot be cited. It
  is bound to pypdf 6.19.0: another version's text is `pdftext-2`, and every PDF
  citation must then be made again.
- **Unverified live.** S&P Global's host refuses automated requests, and a client
  that meets a 403 sends nothing more (P6-20). So on 2026-09-26 `verify-live`
  re-read only SEC's terms page. S&P's and Wikimedia's terms, both S&P DJI notices,
  and the Wikipedia anchor were not re-read, and their saved bytes and the hashes
  taken at Task 17 remain the evidence.
- **Versions and the cutoff.** The content hash covers everything a manifest records,
  including withheld evidence and the SEC files that identities cite. So a refreeze
  after a notice published past the cutoff is curated, or after `fetch-sec` saves
  newer SEC records, makes a new version whose intervals, mappings, and candidate
  issuers are unchanged. Stage 5 keys on those, through the universe's operative
  hash (plan 7, `cohort/identity.py`). Plan 7's edit of the `sec-edgar` register
  entry changes a rebuild's content hash the same way, so `cohort verify-live` now
  reports a difference while the operative hash is v1's.
- **Citation checks.** The build checks that each cited row's name and ticker occur
  in its cited text, which a one- or two-letter ticker meets easily, and nothing ties
  an effective date or its timing to the date span mechanically. Each cited row and
  date was read when it was cited (Task 17, Steps 5 and 6).
