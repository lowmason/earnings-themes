# Event discovery, eligibility, and acquisition

> For agentic workers: REQUIRED NEXT SKILL: writing-plans. This is the stage spec
> for Stage 5 of `specs/evidence-linked-theme-extraction-roadmap.md`. Plan it as two
> plans, in order: plan A (§Plan A) first, and plan B (§Plan B) only after plan A
> ships with the real manifests frozen. Never plan both in one plan.

Stage 5 enumerates the expected earnings events of the frozen DJIA cohort. It
identifies each event's release filing and first publication from SEC filing
metadata, joins the event to the cohort's membership intervals, and freezes the
event manifest and the 40-event pilot manifest. Only then does it acquire the
pilot's releases.

It closes R1.1, R1.2, R1.4, R1.5 and R14.5 of
`specs/evidence-linked-theme-extraction.md`. Of `specs/point-in-time-djia-cohort.md`
it closes P-C2 (the event join), P-C5, P-C7 (the freeze-before-outcomes half), P-A5,
P-VF's period-window, eligibility-reason and selection cases, and P-VI. It keeps that
spec's Stage 5 contracts and its six-step order, and it defines `djia-pilot/1`, the
pilot policy that the universe manifest names.

Locators:
- **`A §n`** is `AGENTS.md`, by line.
- **`Rn` and `Vn`** are the theme spec's requirements and verifications.
- **`P-Cn`, `P-A5`, `P-VF`, `P-VI`** and **`P §Section`** cite the cohort spec, as
  the roadmap does.
- **`P6-n`** are plan 6's decisions
  (`specs/plans/completed/6-point-in-time-djia-cohort.md`).
- **D5** is the roadmap's decision that Stage 4 builds the shared SEC client and every
  later adapter sends through it.
- **V1 and V2** are `docs/verification/V1-edgartools-return-types.md` and
  `docs/verification/V2-parser-fidelity.md`.
- **v1** is the frozen cohort,
  `config/universe/djia/manifests/djia-2024q3-2026q2-v1.json`.
- **`EVn`** are this spec's decisions.

Designed 2026-09-27 in a brainstorming session, from
`stage-5-event-discovery-eligibility-and-acquisition` at `93d4cb7`.

## Decisions

Taken with the user on 2026-09-27. Rows marked *(design)* were proposed in the design
and approved with it.

| ID | Decision |
| --- | --- |
| EV1 | One spec, two plans, in order. Plan A builds the prerequisites, discovery, eligibility, and both freezes (P §Stage 5, steps 1–5). It ends when the user has reviewed and frozen the real manifests. Plan B acquires the pilot's releases and keeps the processing-state table (step 6). Stage 5 is complete only when both are. |
| EV2 | **The P-C7 boundary** (the roadmap's open question, first half). Under P-C7, *acquisition* is retrieving a document that can enter the corpus: a release exhibit. *Discovery evidence* is not acquisition, and discovery reads it before the freeze: SEC's submissions data, companyfacts, a filing's index page, and the 8-K's own primary document. A frozen event names its release *filing* (accession and acceptance time), never an exhibit. R1.2's exhibit and content legs run at acquisition, and their outcomes are processing states. |
| EV3 | **Identification failure** (the open question, second half). An event whose release filing cannot be identified is `ambiguous`, with the reason `no_release_filing` or `several_release_filings`. The freeze refuses until a signed override either sets the filing, citing it, or retains the event as unresolved and excluded with its reason (P §Failure handling). The row stays in the manifest and in every coverage report. |
| EV4 | **The universe's operative identity** (closes plan 6's deferred item). `operative_hash(manifest)` hashes the cohort manifest's cutoff-admissible facts (§Prerequisites). Stage 5's records key on it. The pilot seed uses it where P §Deterministic pilot selection says "universe version", which is a stated reading of P. Every record still names the `universe_version` it read. |
| EV5 | Plan 6's two deferred date items stay deferred: what an override's dates mean, and whether fund holdings match only names cited by the report's date. Stage 5 takes the date-free mappings as they stand. In v1, no security's issuer or CIK changes within the window. |
| EV6 | Fiscal labels are fixed before the freeze, from companyfacts' `fy` and `fp` for the slot's periodic report. A 10-K's `FY` is kept as the source writes it, never renamed `Q4`. |
| EV7 | Quarters with several Item 2.02 filings are resolved by rule first (`release-id/1`), and then by review. |
| EV8 | *(design)* `djia-pilot/1` keeps its name and is defined here (§Pilot selection). It is not bumped, so the universe needs no refreeze. |
| EV9 | *(design)* First publication comes from EDGAR only. `first_publication_time` equals the release filing's acceptance time. That is an upper bound on true first availability, since an issuer's newswire release can precede its 8-K. In v1, no transition issuer's release falls within a week of its membership change. The nearest are Intel's of 2024-10-31, 8 days before, and NVIDIA's of 2024-11-20, 12 days after. |
| EV10 | *(design)* The acceptance time is the filing index page's "Accepted" value, read in America/New_York. The submissions `acceptanceDateTime` is only a cross-check (§Acceptance time). |
| EV11 | *(design)* Records hash facts, never incidental evidence. The event manifest's content hash covers its definition and rows. Citations and retrieval times sit in an evidence record beside it. So a re-fetch never re-versions a manifest or re-seeds the pilot, and a changed fact always does. |
| EV12 | *(design)* Stage 5 has its own store root, `data/raw/events/`, and its own fixture root, `tests/fixtures/events/`. Nothing it saves reaches Stage 4's build or Stage 4's committed synthetic cohort. |
| EV13 | *(design)* Eligibility reads each bound's timing through one-sided unordered windows on the Eastern calendar (§Eligibility). It needs no trading calendar. |

## Scope

In scope:
- the prerequisites that Stage 5's requests and keys need: machine-wide client locks,
  the universe's operative identity, and a verified acceptance-time rule;
- discovery of the expected events and their release filings from SEC filing
  metadata;
- the membership join, eligibility, and review overrides;
- the frozen event manifest and its evidence record;
- `djia-pilot/1` and the frozen pilot manifest;
- acquisition of the pilot's releases, exhibit choice, content confirmation, and the
  processing-state table (plan B);
- synthetic fixtures and offline replay for all of it.

Out of scope:
- acquiring releases outside the pilot, which is Stage 15's job with plan B's adapter;
- publication sources other than EDGAR, such as newswires or investor-relations pages
  (EV9);
- transcripts (Stage 13) and any theme work;
- the two deferred date items (EV5);
- rerunning the R3.5 fidelity check or the layout comparison on the pilot releases,
  since no clause of Stage 5's Exit asks for either;
- any model call, and any acquisition library (§R14.5).

## Inputs

- **The frozen cohort** (plan 6 §Handoffs).
  - `cohort.freeze.load_manifest(path)` reads a manifest and rechecks its hash. The
    latest version in `config/universe/djia/manifests/` wins.
  - `manifest.issuers` holds one row per CIK, with its securities, and
    `candidate_issuer_ids` names the issuers that Stage 5 enumerates. A
    `retained_unresolved` mapping is already excluded, so an issuer without a resolved
    mapping never gets a slot.
  - Intervals are half-open dates whose bounds keep their timing and basis (P6-23).
  - The synthetic cohort, `tests/fixtures/cohort/manifests/djia-synthetic-v1.json`, is
    the offline cohort for P-VI, and it stays byte-identical.
- **The shared SEC client** (R1.3, D5).
  - This means `sec.client.open_sec_client`, `SecClient.fetch(url, expected_types)`,
    `fetch.store.ArtifactStore`, and `sec.data`'s readers.
  - Stage 5 adds no throttle of its own.
- **Stage 3's `canonicalize`**, under `walker-1`, which needs no browser (ADR 0002).
  Plan A reads 8-K item text through it. Plan B reads release text through it, and its
  `FailureReason` values become processing states.
- **Stage 1's findings.**
  - V2's finding for Stage 5 is that a filing's only EX-99 is not necessarily its
    press release.
  - V1 found that edgartools' table and filing paths return pandas or pyarrow objects.
  - `expirements/parser-fidelity/discover.py` is the reference design for parsing
    index pages: port it, never import it.
- **The `sec-edgar` register entry** in `docs/source-register.toml` covers every SEC
  request. Its `access_method` gains companyfacts
  (`data.sec.gov/api/xbrl/companyfacts/`), which it does not yet name.

## Findings from saved data

These were observed on 2026-09-27 from local, gitignored data, with no request sent.
They ground the design, and plan A's records re-derive what they rely on.

1. **SEC writes `acceptanceDateTime` in two conventions, one per file.**
   - Stage 1 saved 221 submissions files and older pages under
     `data/raw/discovery/`. 227 of their rows are filings whose index page it also
     saved.
   - Every file uses one convention throughout. 143 rows give true UTC. 84 give the
     Eastern wall-clock digits of the index page's "Accepted" value, followed by a
     `Z`.
   - Among the 172 main files, the 76 whose latest filing is on or before 2026-04-02
     give Eastern digits, and the 96 whose latest filing is on or after 2026-04-09
     give UTC. That split is consistent with SEC changing its generator in early April
     2026 and regenerating a file whenever its registrant files. This is an
     inference, and the rule in §Acceptance time does not depend on it.
   - The index page's Eastern value matched in every case.
2. **Candidate filings.** Stage 4 saved the 33 issuers' submissions on 2026-09-26 and
   2026-09-27.
   - Their recent blocks list 295 Item 2.02 8-Ks filed from 2024-07-01 through the
     cutoff.
   - Goldman Sachs' and JPMorgan's recent blocks start in September 2025, so their
     earlier filings sit in 6 and 13 older pages.
3. **Period ends.** Each issuer whose recent block covers the window has 8 original
   10-Q or 10-K period ends in it. The exception is Coca-Cola, with 7, since its
   second quarter of 2026 ends 2026-07-03. Goldman Sachs' and JPMorgan's older pages
   were not read. Projected from filing dates, and not yet established: about 263
   slots, of which about 239 are eligible.
4. **Quarters with two Item 2.02 filings.** Eight in-window slots in the recent blocks
   have two:
   - Boeing and Caterpillar for the quarter ended 2024-09-30;
   - Honeywell for 2025-09-30;
   - Goldman Sachs for 2025-12-31;
   - Chevron and Honeywell for 2026-03-31;
   - Nike for 2026-05-31;
   - IBM for 2026-06-30.
   
   Taking the earliest filing would record the wrong first publication for any slot
   whose earlier filing is not the results release. These are leads: plan A
   establishes each one from saved evidence.

## Plan A — discovery, eligibility, and the freezes

### Prerequisites

These are plan A's first tasks, done before any Stage 5 request.

1. **Machine-wide client locks** (the deferred item "Hold the SEC and web client locks
   once per machine").
   - The locks in `sec/client.py` and `cohort/web.py` move from each checkout's
     `data/runs/` to one per-user directory outside every checkout.
     - That directory is the user's cache directory:
       `~/Library/Caches/earnings-themes/locks/` on macOS, and elsewhere
       `$XDG_CACHE_HOME/earnings-themes/locks/`, falling back to `~/.cache/`.
     - An environment variable overrides it for tests.
     - No dependency is added.
   - A test shows two repository roots sharing one lock, for each client.
   - The docstrings and `docs/verification/djia-cohort.md` say "one machine" again.
   - Stage 1's frozen harness keeps its own lock, so the two still never run live
     together.
2. **The universe's operative identity** (the deferred item "Give the universe
   manifest an operative identity"; EV4).
   - `operative_hash(manifest)` is the SHA-256 of the canonical JSON
     (`cohort.digests.canonical_json`) of this projection:
     - the definition's `universe_id`, `universe_name`, `period_end_start`,
       `period_end_stop`, `public_information_cutoff`, `membership_reference`, and
       `selection_policy_version`;
     - each interval's `security_id`, both bounds with their timing and basis, and
       its `assertion_ids`;
     - each mapping's `security_id`, `status`, `issuer_id`, and `cik`;
     - each issuer's `issuer_id`, `cik`, and `security_ids`;
     - `candidate_issuer_ids`.
   - Everything else is left out:
     - the version, the content hash, and the creation time;
     - `expected_member_count` and `source_register_version`;
     - the sources, the securities, and the assertions, withheld ones included;
     - each mapping's candidates, citations, method, override, and reason;
     - the issuers' names, the overrides, and the report.
   - Tests on the synthetic cohort's builder:
     - a withheld notice and a re-fetched SEC record each change `content_hash` but
       not the operative hash;
     - a moved bound, a changed mapping, and a new supporting assertion each change
       both;
     - v1 loads unchanged and has an operative hash.
3. **The acceptance-time record**, `docs/verification/edgar-acceptance-time.md`
   (EV10).
   - An offline script recomputes Finding 1 from saved pages and writes the record's
     table. It sends no request.
   - After the real discovery run, it adds a second leg over Stage 5's own pages,
     which cover the window's filings.
4. **Two robustness fixes in code that Stage 5 relies on.** These are parts 2 and 3 of
   the deferred item "Three robustness fixes in the cohort path".
   - `read_submissions` raises `SecDataError`, rather than `KeyError` or `TypeError`,
     on a malformed `formerNames` or `filings.files` entry, and it refuses a string
     `tickers`.
   - `retry_after_seconds` ignores a `Retry-After` value made of non-ASCII digits.

### Store, client, and readers

- **Store.** Responses are saved in an `ArtifactStore` rooted at `data/raw/events/`,
  under source `sec-edgar` (EV12).
- **Client.** Every request goes through `open_sec_client`. The package functions take
  saved bytes and a fetch callable, and only the CLI opens the client (P6-22).
- **What discovery fetches.** It fetches submissions files, the older pages it needs,
  and companyfacts. It fetches the index page of every 8-K in the range whose
  submissions `items` include `2.02`, and the primary document of every candidate
  (§Candidates and `release-id/1`). It never fetches an exhibit (EV2).
- **Readers.** These are pure functions of saved bytes, and each raises
  `SecDataError` on any other shape (A §407).
  - The submissions reader also yields each filing's `items`, and each older page's
    `filingFrom` and `filingTo`. What Stage 4's readers accept does not change, since
    Stage 4's synthetic submissions carry no `items` column.
  - A companyfacts reader yields `fy` and `fp` by accession. An accession whose facts
    disagree yields no labels.
  - A filing-index reader yields the form, "Accepted", "Period of Report", "Items",
    and the document table (sequence, description, file name, and type). It is ported
    from Stage 1's `parse_filing_index`.
- **The cutoff.** Discovery reads only filings accepted on or before 2026-09-22 on the
  Eastern calendar. A later filing is never a slot, a candidate, or a source of labels
  (P-C4).
- **Older pages.** An older page is read when its own `filingFrom`–`filingTo` range
  meets `[2024-07-01, 2026-09-22]`. Otherwise it is skipped by those dates, and the
  skip is recorded (R1.1).

### Slots (step 1)

- **One slot per candidate issuer per period end.**
  - A period end is a distinct `reportDate` among the issuer's original `10-Q`,
    `10-K`, `10-QT`, and `10-KT` filings that were accepted by the cutoff and fall in
    `[2024-07-01, 2026-07-01)`.
  - Amendments never make slots, so period ends are reported by the source, never
    inferred.
- **The ID.** `event_id` is `<issuer_id>:<period_end>`, for example
  `cik-0000320193:2024-09-28`. Several securities of one issuer make one slot.
- **Fiscal labels** (EV6).
  - `reported_fiscal_year` is companyfacts' `fy` for the slot's periodic report.
  - `reported_fiscal_quarter` is its `fp` as written: `Q1`, `Q2`, `Q3`, or `FY`.
  - Missing or disagreeing labels stay null, with a non-blocking
    `fiscal_labels_unknown` finding.
- **Guards.** Each is a blocking finding that an `acknowledge` override answers.
  - `period_gap` fires in three cases, each meaning that an in-window period end may
    be missing:
    - two consecutive visible period ends of an issuer, at least one of them inside
      the window, are more than 105 days apart;
    - no visible period end precedes the issuer's first in-window one, and that one
      lies 92 or more days after the window's start;
    - no visible period end follows the issuer's last in-window one, and that one
      lies more than 91 days before the window's stop.
  - The guard judges the window's edges by quarter length, never by filing lag. A
    rule keyed to the cutoff would falsely flag Nike, whose last in-window period ends
    2026-05-31, since its next 10-Q is not due until after the cutoff.
  - `no_slots` fires when a candidate issuer has no slot.
  - Checked on 2026-09-27 against Stage 4's saved recent blocks, filtered to the
    cutoff:
    - the first and third cases fire for no issuer, and `no_slots` for none;
    - the second fires only for Goldman Sachs and JPMorgan, whose earlier filings sit
      in older pages those files leave out, and which discovery reads.
  - Fixtures trip every case.

### Candidates and `release-id/1` (step 2)

- **Candidates.** Take a slot with period end P. P′ is the issuer's next visible
  period end, or the cutoff if none is visible. The slot's candidates are the original
  8-Ks that meet all three conditions:
  - they were accepted after P and on or before P′, on the Eastern calendar;
  - their submissions `items` include `2.02`, and the index page's Items confirm it;
  - their index page lists at least one exhibit typed `EX-99*`. That includes `EX-99`,
    `EX-99.1`, `EX-99.01`, and any other numbering.
  
  8-K/A filings in the range are recorded but never chosen by the rule. An override
  may choose one, citing it.
- **The rule `release-id/1`**, applied to each slot's candidates:
  1. **Item text.** The candidate's primary document is canonicalized by `walker-1`.
     Its Item 2.02 text runs from the "Item 2.02" heading to the next "Item" heading.
     A document that fails to canonicalize, or has no such heading, states nothing.
  2. **Stated periods.** The rule records the dates the text writes in full, such as
     "September 30, 2024" or "Sept. 30, 2024". It also records the fiscal periods the
     text names: an ordinal or `Q` quarter with a year, "fiscal 2025", or "full year".
     - A stated date matches the slot when it equals P.
     - A stated fiscal period is judged only when the slot has labels. It then matches
       when it equals them: the first to third quarter for `Q1`–`Q3`, or the fourth
       quarter or full year for `FY`, with the year equal to `fy`.
  3. **Preliminary.** The rule records whether the text calls the results
     preliminary.
  4. **Resolution.**
     - Drop each candidate that has judged statements, none of which matches. A
       candidate that states nothing, or only unjudged fiscal periods, stays.
     - Drop each candidate that calls its results preliminary.
     - If one candidate is left, it is the release filing. Its method is
       `stated_period` if it states P, and otherwise `sole_candidate`.
     - If none is left, the event is `ambiguous` with `no_release_filing`. If several
       are left, it is `ambiguous` with `several_release_filings`.
- **The rule is fixed before the real run.** Plan A pins its phrase lists with
  synthetic fixtures modeled on the two-filing quarters of Finding 4. After the real
  discovery run, the rule changes only as `release-id/2`, with a recorded reason. A
  case the rule gets wrong goes to review.

### Acceptance time (EV10)

- **The value.** `filing_acceptance_time` is the release filing's index-page
  "Accepted" value.
  - That wall-clock time is localized to America/New_York, so daylight saving is
    handled.
  - It is stored as a UTC instant, with `source_timezone` set to `America/New_York`.
- **The cross-check.** The filing's submissions `acceptanceDateTime` must either equal
  that instant, or carry its Eastern digits followed by `Z` (Finding 1).
  - Anything else is a blocking `acceptance_time_mismatch` finding, so a changed
    format stops the build instead of being guessed at.
  - The reader never infers a file's convention from its dates.
- **First publication.** `first_publication_time` equals `filing_acceptance_time`, and
  `first_publication_source_id` is `sec-edgar` (EV9). The evidence record states the
  upper-bound limitation.
- **Stage 4's reader is unchanged.** `Filing.accepted_at` still carries SEC's value as
  written.
- **Dates.** Every date judgment in Stage 5 uses the instant's Eastern calendar date:
  the cutoff, the candidate windows, and the interval bounds.

### Eligibility (step 3) — `eligibility/1`

- **Issuer membership at an instant T.**
  - An interval holds T when T is on or after its start and before its end, each
    judged by the bound rules below.
  - An `anchor_snapshot` start is a lower bound: every release on or after its date is
    inside, and every window release follows the anchor.
  - The issuer is a member when any of its securities' intervals holds T. It is not a
    member when none holds T and none is unordered at T. Otherwise its membership is
    unordered.
  - `MembershipInterval.contains(day)` is not used, because it ignores timing.
- **Bound rules.** Take a bound on Eastern date D, with timing τ, and a release at
  Eastern date d and time t:

  | τ | d < D | d = D | d > D |
  | --- | --- | --- | --- |
  | `before_open` | before | after if t ≥ 09:30, else unordered | after |
  | `after_close` | before | before if t < 13:00, else unordered | after |
  | `unspecified` | before | unordered | after |

  - 09:30 ET is the regular open, which is the same on every trading day.
  - 13:00 ET is NYSE's earliest scheduled close.
  - So no trading calendar is needed (EV13).
  - P confines ambiguity to a release that shares a date with the change, so a release
    made after the previous day's close is ordered by its date.
- **Status and reason.** The checks run in order, and the first that applies decides:

  | Check | Outcome | Status | Reason |
  | --- | --- | --- | --- |
  | 1. Window | `period_end` outside `[2024-07-01, 2026-07-01)` | `ineligible` | `period_end_outside_window` |
  | 2. Identification | no release filing | `ambiguous` | `no_release_filing` or `several_release_filings` |
  | 3. Cutoff | publication's Eastern date after 2026-09-22 | `ineligible` | `published_after_cutoff` |
  | 4. Membership | member | `eligible` | `member_at_publication` |
  | | not a member | `ineligible` | `not_member_at_publication` |
  | | unordered | `ambiguous` | `same_day_transition` |

  Slots lie in the window, and candidates precede the cutoff, by construction. So
  checks 1 and 3 are defensive, and fixtures exercise them. In v1, every `ineligible`
  row should read `not_member_at_publication`.
- **`membership_assertion_id`** names the assertion that decides check 4:
  - for a member, the assertion that opens the interval holding T, `member_at` or
    `added`, taking the smallest ID when several merged;
  - for a non-member, the nearer in days of two assertions: the `removed` one that
    closes the last interval before T, and the `added` one that opens the first
    interval after T. A tie goes to the removal;
  - for an unordered case, the assertion of the unordered bound;
  - null when check 1 or 2 decided.

### Review overrides

- **The file.** The events' overrides live in
  `config/corpus/djia-2024q3-2026q2/overrides.toml`, read strictly like Stage 4's
  curated files (P6-18).
  - Each override records its ID, kind, rationale, reviewer, and recording date.
  - The reviewer is the user; the implementer never fills that field in.
- **`set_release_filing`** names an event and an 8-K or 8-K/A of its issuer that was
  accepted by the cutoff and whose index page is saved, and cites it.
  - The event takes that filing's acceptance time, and its method becomes `override`.
  - Its eligibility is computed again, and may come out as any status.
  - A filing accepted after the cutoff is refused (P-C4).
- **`retain_unresolved`** names an `ambiguous` event and its reason.
  - The event keeps its status and reason, is marked retained, and is excluded from the
    pilot's eligible set.
  - This is the only way to settle `same_day_transition`, because EDGAR alone cannot
    order it (EV9).
- **`acknowledge`** names a `period_gap` or `no_slots` finding and its digest. It goes
  stale when the finding changes, which blocks the freeze again, as in Stage 4 (P6-7).
- **Refusals.** An override that names no such event, finding, or filing is refused.

### The event manifest (step 4)

One record serves as both P's "complete eligible-event manifest" and Stage 15's
"frozen expected-event ledger".

- **Definition.** `corpus_id` (`djia-2024q3-2026q2`), `event_manifest_version`,
  `universe_id`, `universe_version`, `universe_operative_hash`,
  `discovery_policy_version` (`release-id/1`), `eligibility_policy_version`
  (`eligibility/1`), `public_information_cutoff`, `content_hash`, and `created_at`.
- **Rows.** There is one row per slot, sorted by `event_id`. Each row holds:
  - `event_id`, `issuer_id`, `cik`, `period_end`, `reported_fiscal_year`, and
    `reported_fiscal_quarter`;
  - `periodic_accession` and `periodic_form`;
  - `release_accession`, `candidate_accessions`, and `identification_method`;
  - `filing_acceptance_time`, `first_publication_time`, `source_timezone`, and
    `first_publication_source_id`;
  - `membership_assertion_id`, `eligibility_status`, `eligibility_reason`,
    `retained`, and `override_ids`.
- **Also hashed:** the findings, each with its resolution, and the overrides applied.
- **The evidence record** (EV11).
  - It is `events-v<N>.evidence.json`, written beside the manifest at the freeze. It is
    never replaced, and it lies outside the hash.
  - For each event it cites the following, using Stage 4's `Citation` and
    `EvidenceLocator`:
    - the periodic report's submissions row and its companyfacts labels;
    - the release filing's index page and "Accepted" value;
    - the Item 2.02 text span;
    - each candidate's index page;
    - the cross-checked `acceptanceDateTime`.
  - It also records the convention each submissions file used, the older pages read
    and skipped, and every `retrieved_at`.
- **Freezing** follows P6-14.
  - It refuses while any blocking finding is unanswered, or any `ambiguous` row is not
    retained, and it names each one.
  - The content hash is the SHA-256 of the canonical JSON of the definition, without
    its version, hash, and creation time, together with the rows, the findings, and
    the overrides.
  - Content that matches a frozen version *is* that version, and nothing is written.
    New content takes the next version.
  - Writes are atomic and never replace a file. Loading rechecks the hash and the file
    name.
- **Files.** `config/corpus/djia-2024q3-2026q2/events-v<N>.json` and its evidence
  record are committed. They hold facts, URLs, hashes, and locators, never source text
  (P6-3).
- **The data dictionary.** Plan A's records join ingestion schema version 1 (P6-5):
  the event manifest and its rows, the evidence record, the overrides, and the pilot
  manifest. Each is documented in `docs/data-dictionary.md`, whose drift test covers
  it.

### P's expected-event contract, field by field

| P field | Where it lives |
| --- | --- |
| `event_id`, `issuer_id`, `period_end`, `reported_fiscal_year`, `reported_fiscal_quarter` | event manifest row |
| `first_publication_time`, `first_publication_source_id`, `filing_acceptance_time` | event manifest row |
| `membership_assertion_id`, `eligibility_status`, `eligibility_reason` | event manifest row |
| `processing_status`, `missing_reason` | processing-state table (plan B), joined on `event_id` |
| `retrieved_at` (P §Temporal definitions) | evidence record for discovery; processing-state table for acquisition |

Every field keeps its own column, and no record substitutes one time for another
(R1.5, P-A5).

### Pilot selection (step 5) — `djia-pilot/1`

`djia-pilot/1` reads only a frozen event manifest (EV8). In what follows:
- `E` is the manifest's `eligible` rows, and `U` is their issuers;
- an event's quarter is the calendar quarter of its `period_end`, from `2024Q3`
  through `2026Q2`.

**Seed and ordering.**
- The seed is the SHA-256 hex of the canonical JSON of an object with three keys
  (EV4):
  - `eligible_event_manifest_hash`, the frozen event manifest's `content_hash`;
  - `selection_policy_version`, the string `djia-pilot/1`;
  - `universe_operative_hash`, the operative hash the event manifest records.
- `h(x)` is the SHA-256 hex of the UTF-8 string `<seed>:<x>`, where `<seed>` is that
  hex. Every order and tie below uses `h`, so the input's row order cannot matter.

**Guards**, checked before selecting:
- `|U| > 40`: refuse with `scope_decision_needed`. An issuer is never silently
  omitted.
- `|E| < 20`: refuse with `blocked`.
- `20 ≤ |E| < 40`: the target is `|E|`, and the pilot is marked `underfilled`. The
  steps below then take every event, each with a reason, and step 3's refusal enforces
  P's coverage requirement.
- Otherwise the target is 40.

**Steps.**
1. **Issuer coverage.** Issuers go in `h(issuer_id)` order. Each issuer takes its
   eligible event from the quarter with the fewest selections so far, with ties broken
   by `h(event_id)`. Reason: `issuer_coverage`.
2. **Membership boundaries.**
   - A transition in scope is an issuer-level entry or exit dated in
     `[2024-07-01, 2026-09-22]`, meaning an issuer's membership starting or ending.
     A second security joining a member issuer is not one, and neither is an
     `anchor_snapshot` start.
   - For each transition, the target is the nearest eligible event on the member side.
     After an entry, that is the issuer's eligible event with the earliest
     `first_publication_time` after the entry. Before an exit, it is the one with the
     latest `first_publication_time` before the exit.
   - A target not yet selected is added. Additions are ordered by the transition's
     date, then by `h(event_id)`. Reason: `membership_boundary`.
   - A transition with no eligible event on its member side is reported, not refused.
3. **Quarter coverage.** For each quarter with no selection, in time order, add its
   event whose issuer has the fewest selections, with ties broken by `h(event_id)`.
   Reason: `quarter_coverage`. A quarter with no eligible event refuses with
   `quarter_uncovered`.
4. **Overflow.** If steps 1–3 hold more events than the target, refuse with
   `mandatory_overflow`, before filling. P forbids discarding a mandatory case to keep
   the cap.
5. **Fill.** Repeat until the target is met:
   - among the issuers that still have unselected eligible events, look at those with
     the fewest selections, and at their unselected events;
   - take the one whose `period_end` is farthest, in days, from its issuer's nearest
     selected `period_end`;
   - break ties by `h(event_id)`.
   
   Reason: `longitudinal_fill`.

**The pilot manifest**, `config/corpus/djia-2024q3-2026q2/pilot-v<N>.json`.
- It has P's fields:
  - `pilot_id` (`djia-2024q3-2026q2-pilot`), `pilot_version`, `universe_version`,
    `eligible_event_manifest_hash`, `selection_policy_version`, `selection_seed`,
    `content_hash`, and `created_at`;
  - per row, `event_id`, `selection_order` (the order taken, from 1), and
    `selection_reason`.
- It adds `universe_operative_hash`, `event_manifest_version`, `target`,
  `underfilled`, and the reported transitions that have no event on their member side.
- It freezes by the event manifest's rules. A refusal writes nothing and names its
  reason.
- Loading rechecks the chain: the pilot's hash, the event manifest it names, and that
  manifest's universe operative hash.

**Invalidation.** A new event manifest version, or a new policy, gives a new seed and a
new pilot version. A frozen pilot is never edited. No acquisition, parse, or later
outcome is an input to any step.

**v1, projected.** `|U|` is 33 and `|E|` is about 239.
- Step 1 takes 33 events.
- Step 2 adds at most three:
  - NVIDIA's release of 2024-11-20, after its entry;
  - Sherwin-Williams' first release after its entry;
  - Verizon's last release before its exit.
- Dow, Intel, and Alphabet each have one eligible event, which step 1 has already
  taken.
- Step 3 should add none, and step 5 adds at least 4.

**The synthetic cohort** has 5 issuers and about 31 eligible events, so P-VI takes the
underfilled path. The other paths use event rows built directly.

### Commands

These live in `apps/earnings-pipeline`, as an `events` group (P6-22). The plan settles
their names and flags.
- **`events discover`** is the live discovery run.
  - It opens the SEC client and states its request count first.
  - It is resumable: a rerun fetches only what the store lacks.
- **`events build`** is offline. It prints the slots, identification, eligibility,
  and findings, and exits 1 while anything blocks.
- **`events freeze`** freezes the event manifest, refusing as `build` does.
- **`events select`** runs `djia-pilot/1` on the latest frozen event manifest and
  freezes the pilot.

### The synthetic event layer

- **The generator.** It is package code, like `cohort/synthetic.py`, because P-VI
  consumes its output.
  - It invents submissions, companyfacts, index pages, 8-K primary documents, and
    exhibits for the synthetic cohort's CIKs, and saves them under
    `tests/fixtures/events/`.
  - It never touches `tests/fixtures/cohort/`.
  - `tests/fixtures/events/` regenerates from it byte for byte.
- **Its cases:**
  - a narrative-only release;
  - exhibits numbered `EX-99` and `EX-99.01`;
  - a quarter with a preliminary filing, then the actual release;
  - a quarter with no candidate;
  - a quarter with two candidates that the rule cannot separate;
  - an 8-K/A;
  - a pre-market release on the day of a `before_open` change;
  - each `period_gap` case, and a Nike-like calendar that trips none;
  - both acceptance-time conventions;
  - a filing accepted after the cutoff;
  - an AMC-like pro forma overview filed as a filing's only EX-99, for plan B.
- **Selection-level fixtures.** The exactly-40, `blocked`, `scope_decision_needed`,
  `mandatory_overflow`, and `quarter_uncovered` paths are tested on event rows built
  directly, not through SEC fixtures.

### Verification (plan A)

1. **Prerequisites.**
   - Two repository roots share each lock.
   - The operative-hash tests of §Prerequisites pass, and v1 loads unchanged.
   - The acceptance-time record regenerates from saved pages.
   - The two robustness fixes each have a test.
2. **Readers.** Each reader refuses a changed shape with `SecDataError`. The
   submissions reader still accepts Stage 4's synthetic files.
3. **Acceptance time.** Fixtures cover both conventions, a date in each
   daylight-saving season, and a mismatch, which blocks.
4. **Discovery replay (R1.1, R1.2).** Offline replay of the synthetic event layer's
   saved responses identifies every fixture issuer's release filings, including a
   narrative-only release and exhibits numbered `EX-99` and `EX-99.01`.
   - The preliminary-then-actual quarter resolves to the actual release.
   - The quarter with no candidate, and the one whose two candidates the rule cannot
     separate, are `ambiguous` with their reasons.
   - The 8-K/A is recorded and never chosen.
   - The filing accepted after the cutoff is never read.
5. **No exhibit before the freeze (EV2).** A recording transport over a synthetic
   discovery run shows requests only for submissions, older pages, companyfacts, index
   pages, and primary documents. It shows no request for an exhibit, and every request
   goes through the shared client, with no throttle of Stage 5's own (R1.3, D5).
6. **Slots.**
   - An issuer with two securities yields one slot per period (P-VF).
   - Period ends on each side of 2024-07-01 and of 2026-07-01 exercise both window
     boundaries (P-VF).
   - Each of the three `period_gap` cases, and an issuer without slots, blocks until
     acknowledged. A fiscal calendar like Nike's, whose next report falls after the
     cutoff, trips none.
7. **Eligibility (P-C2, P-VF).**
   - Releases just before and just after each timing's bound resolve to the correct
     side.
   - A release inside each unordered window is `ambiguous`, with `same_day_transition`
     and no invented time.
   - Every reason in the table has a fixture.
8. **Event records (R1.5, P-A5).** `period_end`, the fiscal labels,
   `first_publication_time`, `filing_acceptance_time`, and `retrieved_at` stay
   separate fields, and unknown labels stay null.
9. **Freeze.**
   - It refuses an unanswered finding and an unretained `ambiguous` row, naming each.
   - Identical content is the same version, and a re-fetched submissions file with the
     same facts writes nothing.
   - A changed fact writes the next version.
10. **Selection (P-C5, P-VF).**
    - Shuffled input yields a byte-identical pilot.
    - Every eligible issuer and all eight quarters are represented.
    - With at least 40 eligible events, the pilot holds exactly 40, each with its
      reason.
    - Fixtures produce `membership_boundary` rows and repeated-issuer
      `longitudinal_fill` rows.
    - The underfilled, `blocked`, `scope_decision_needed`, `mandatory_overflow`, and
      `quarter_uncovered` cases each refuse or mark the pilot as specified.
11. **Invalidation (P-VF).** A changed interval, mapping, event fact, or policy name
    yields a new version and hash, of the event manifest, the pilot, or both.
12. **P-VI.** Offline, from the synthetic cohort and event layer, the run produces
    membership intervals, resolution, eligibility, the frozen event manifest, and the
    frozen underfilled pilot. It uses no network, credentials, proprietary roster, or
    model call.
13. **R14.5.** An import-boundary test keeps edgartools, pandas, and pyarrow out of
    Stage 5's modules. The record states that no acquisition library's output crosses
    the ingestion boundary (§R14.5).
14. **Suites.** The default suite, the harness suite, and Ruff pass. `uv.lock` changes
    only if the plan adds a dependency, and none is planned.

### Gates (plan A)

1. **Discovery.** Before `events discover` runs live, the user approves its stated
   request count, about 700:
   - 33 submissions files;
   - about 19 older pages;
   - 33 companyfacts files;
   - about 305 index pages and 305 primary documents.
   
   `EDGAR_IDENTITY` is exported here, so a `-m live` test also sends requests, and it
   needs the same approval, with its count.
2. **Review.** After `events build` runs on the real data, the user reviews every
   finding and every `ambiguous` event, and signs each override.
3. **Freeze.** The user approves the event manifest's freeze, and then the pilot's.
4. **The record.** `docs/verification/djia-events.md` records the run:
   - the requests, by gate;
   - the slots, statuses, and reasons;
   - the overrides;
   - the pilot's rows, by reason;
   - both versions and hashes;
   - that no model was called.

## Plan B — acquisition and processing states

### Gate

`events acquire` refuses unless a frozen pilot loads and its chain checks
(§Pilot selection). It acquires only the pilot's releases. Stage 15 reuses the adapter
for every other eligible event.

### Exhibit choice (R1.2)

The exhibit is chosen from the release filing's saved index page and Item 2.02 text,
in this order:
1. among the exhibits typed `EX-99*`, the one that the Item 2.02 text names, for
   example "Exhibit 99.1";
2. otherwise, one whose description names a release (plan B fixes the words);
3. otherwise, the one with the lowest sequence number.

Fetching that exhibit is the acquisition. Its bytes and its `Retrieval` go to the
events store, and `walker-1` canonicalizes it.

### Content confirmation — `release-content/1`

- The exhibit's canonical text must state the slot's period, by its end date or by its
  fiscal labels, as in `release-id/1`. Its opening elements must announce results.
  Plan B fixes the vocabulary with fixtures.
- If confirmation fails, the filing's next `EX-99*` exhibit is tried, in the order
  above. Every attempt is recorded.
- V2's AMC case, a pro forma overview filed as a filing's only EX-99, is a fixture
  that must fail.

### What acquisition can change

- Nothing found at acquisition edits a frozen manifest, and a selected event stays
  selected (P-C7).
- A signed `set_release_document` override may name another exhibit, or an exhibit of
  another filing by the issuer, citing it.
  - The processing record keeps both the frozen filing and the one acquired.
  - If the other filing's acceptance time would change the event's eligibility, the
    record marks a `corpus_error` for the next corpus version, and nothing is fixed in
    place.
  - In v1 no release lies near a membership change, so this is a guard.

### Processing states (R1.4)

- **The rows.** There is one row per expected document. For Stage 5 that is the
  release of each pilot event.
- **The history.** Every transition is kept, with its time, run, reason, and details:
  the accession, the exhibit, the artifact hash, and the `doc_id`.

| From | To | Recorded |
| --- | --- | --- |
| (start) | `expected` | every pilot event, before acquisition |
| `expected` | `acquired` | a candidate exhibit's bytes are saved |
| `expected` | `unavailable` | `missing_reason` `not_found`: no candidate exhibit could be fetched |
| `expected` | `restricted` | the source's rights forbid local processing; fixtures only, since SEC documents are public |
| `acquired` | `parsed` | a candidate canonicalized and was confirmed as the release |
| `acquired` | `failed` | no candidate was confirmed, and one failed to canonicalize, with Stage 3's `FailureReason`: `unsupported_media_type`, `parse_failed`, `no_native_text`, or `invalid_elements` |
| `acquired` | `unavailable` | `missing_reason` `no_confirmed_release`: every candidate canonicalized, and none was confirmed |
| `parsed` | `partial`, `completed`, `completed-no-theme` | set by later stages; fixtures represent them now |

- **Reconciling A.** A §644 lists `available` and `processed`. R1.4's list is the
  later text, and it governs: `available` is `acquired`, and `processed` is
  `completed` or `completed-no-theme`.
- **Stopping.** A persistent 403 stops the run (R1.3), and events not yet attempted
  stay `expected`.
- **Storage.**
  - The table is a Polars frame, written as Parquet under the gitignored
    `data/runs/events/`, one file per run.
  - Writes are atomic and never replace an earlier run. The current state is the
    latest transition per document.
  - Canonical documents go under `data/runs/events/canonical/`, named by `doc_id`.
- **The data dictionary.** The processing-state rows and their transitions join
  ingestion schema version 1 (P6-5), and are documented in `docs/data-dictionary.md`
  under its drift test.

### Verification (plan B)

1. `events acquire` refuses without a frozen pilot whose chain checks.
2. **Exhibit choice and confirmation.** Fixtures cover:
   - `EX-99`, `EX-99.1`, and `EX-99.01` numbering;
   - a narrative-only release;
   - a filing whose first choice fails and whose next exhibit confirms;
   - the AMC-like overview, which fails.
3. **States (R1.4).** The state table represents every R1.4 state from fixtures, and
   every expected but absent document carries its `missing_reason`.
4. **P-C7.** After acquisition and parse states change, including to `failed`, and
   after later-stage states are written, the pilot and event manifests are
   byte-identical, and every selected event is still selected.
5. **The client.** The adapter sends only through the shared client, with no throttle
   of its own (R1.3, D5). A persistent 403 stops the run and leaves unattempted events
   `expected`.
6. **Replay.** Offline replay of saved responses reproduces the states.
7. **Suites.** The default suite, the harness suite, and Ruff pass.

### Gates (plan B)

1. Before `events acquire` runs live, the user approves its stated request count:
   about 40 to 60 exhibits, since the index pages are already saved.
2. `docs/verification/djia-events.md` gains the acquisition run: the requests, the
   states by count, the overrides, and the failures.

## R14.5

Stage 5 uses no acquisition library. edgartools stays an unused optional extra, and
the readers are the package's own. So no library output reaches the ingestion
boundary, and there is nothing to cast.

The record says exactly that, and does not call R14.5 vacuous, since V1 found that
edgartools' paths would need casts. The import-boundary test holds it
(§Verification (plan A), item 13).

## Deferred items

| Item in `specs/deferred_items.md` | Disposition |
| --- | --- |
| `6-point-in-time-djia-cohort`: Give the universe manifest an operative identity | Closed by plan A (§Prerequisites, EV4) |
| `6-point-in-time-djia-cohort`: Hold the SEC and web client locks once per machine | Closed by plan A, before any Stage 5 request |
| `6-point-in-time-djia-cohort`: Three robustness fixes in the cohort path | Parts 2 and 3 closed by plan A, since they sit in code Stage 5 relies on. Part 1, the cohort CLI's tracebacks, is restated as its own open item |
| `6-point-in-time-djia-cohort`: Decide what an override's dates mean | Stays open (EV5) |
| `6-point-in-time-djia-cohort`: Decide whether a fund report's holdings match only names cited by its date | Stays open (EV5) |
| `6-point-in-time-djia-cohort`: Four stale claims | Stays open: none is in Stage 5's path |
| `6-point-in-time-djia-cohort`: Let `verify-live` re-read the other hosts | Stays open: Stage 5 makes no web-client request |
| `5-structure-aware-canonicalization`: the four capture and browser-setup items | Stay open: Stage 5 captures nothing (ADR 0002) |
| `5-structure-aware-canonicalization`: Separate words split by `<br>` in table cells | Stays open: identification and confirmation read narrative text, not cells |
| `1-release-parser-fidelity`: the three open items | Stay open: Stage 5 does not time parsers, reuse the selection rule, or run the lock gate |
| `3-core-evidence-spine`: the four open items | Stay with Stage 7 |

## Handoffs from plan 6, answered

| Plan 6 Handoff to Stage 5 | Answer |
| --- | --- |
| The frozen cohort: `load_manifest`, the latest version, the synthetic manifest | §Inputs. P-VI replays the synthetic manifest |
| Intervals: half-open dates with timing and basis; same-day ordering is Stage 5's | §Eligibility, EV13 |
| Issuers: one row per CIK; `candidate_issuer_ids`; `retained_unresolved` excluded | §Slots: one slot per candidate issuer and period |
| The shared SEC client, the store, and `sec.data`'s readers | §Store, client, and readers; plan B's adapter |
| `acceptanceDateTime` is unverified | Finding 1, EV10, §Acceptance time |
| `selection_policy_version = "djia-pilot/1"` | EV8, §Pilot selection |
| `EDGAR_IDENTITY` may be exported | §Gates (plan A) and §Gates (plan B) |
| The manifest's `content_hash` covers withheld evidence and SEC files (deferred) | EV4, §Prerequisites |
| The locks hold per checkout (deferred) | §Prerequisites |
| Override dates and holdings by date (deferred) | EV5 |

## Exit criteria

### The roadmap's Stage 5 Exit, clause by clause

| Clause | Met by |
| --- | --- |
| The six-step order is enforced, and both manifests freeze before any outcome exists (P-C7) | Plan A, items 5 and 9. `events select` needs a frozen event manifest, and `events acquire` a frozen pilot |
| The pilot is unchanged after acquisition and parser statuses change (P-C7) | Plan B, item 4 |
| A selected event stays selected when a later step fails | Plan B, item 4 |
| Releases on either side of a transition, and same-day ambiguity (P-C2) | Plan A, item 7 |
| One expected event per period for an issuer with several securities (P-VF) | Plan A, item 6 |
| Both window boundaries, and every eligibility reason (P-VF) | Plan A, items 6 and 7 |
| A byte-identical pilot from shuffled input, with every issuer and quarter, and the underfilled, blocked, and overflow cases (P-C5) | Plan A, item 10 |
| Exactly 40 when at least 40 are eligible, with reasons and the boundary and repeated-issuer cases (P-VF) | Plan A, item 10 |
| A new version and hash on changed evidence, resolution, corpus, or policy (P-VF) | Plan A, item 11 |
| The freeze refuses unresolved rows unless retained (P §Failure handling) | Plan A, item 9 |
| The times and labels stay separate fields, and EDGAR acceptance stands in only as specified (R1.5, P-A5) | Plan A, item 8; EV9 |
| Offline replay identifies releases, including a narrative-only one and alternative numbering (R1.1, R1.2) | Plan A, item 4, for filings; plan B, item 2, for exhibits |
| The adapter sends only through the shared client (R1.3, D5) | Plan A, item 5; plan B, item 5 |
| Every R1.4 state is represented from fixtures | Plan B, item 3 |
| Library output is Polars at the boundary, or R14.5 is recorded (R14.5) | Plan A, item 13; §R14.5 |

### Plan A

1. Both locks are machine-wide and tested, and the records say one machine. This
   closes the deferred item.
2. The operative hash exists with its tests, and v1 loads unchanged. This closes the
   deferred item.
3. The acceptance-time record regenerates from saved pages, with both legs.
4. §Verification (plan A), items 2–13, pass.
5. The real event manifest and pilot are frozen and committed after the gates, and
   `docs/verification/djia-events.md` records the run.
6. The default suite, the harness suite, and Ruff pass.

### Plan B

1. §Verification (plan B), items 1–6, pass.
2. The pilot's releases are acquired after the gate, and the record gains the run.
3. The default suite, the harness suite, and Ruff pass.

## Handoffs to later stages

| Stage | Receives |
| --- | --- |
| 6 | The frozen pilot manifest, with its loader and chain check; each pilot event's issuer, period end, and fiscal labels; the processing-state table; the pilot releases' `walker-1` canonical documents, whose `doc_id`s gold spans bind to |
| 10 | The processing-state table, for denominators; the event manifest's issuer-period rows |
| 11 | The frozen pilot manifest |
| 15 | The frozen event manifest, which is its expected-event ledger; plan B's adapter, exhibit choice, and confirmation; the processing-state table; `operative_hash`; the machine-wide lock |

## Rollout

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 5 — on plan completion, tick the stage and re-validate later stages against what shipped.

"Plan completion" above means plan B's. Plan A's completion does not tick Stage 5.

- **On plan A's completion,** append this line, with the plan's ID and path:

  ```text
  > Plan A: COMPLETE (YYYY-MM-DD) — implemented by plan <id> (<path>). Next: write plan B.
  ```

- **On plan B's completion,** append the stage stamp, with both plans' IDs and paths:

  ```text
  > Stage 5: COMPLETE (YYYY-MM-DD) — implemented by plans <A id> (<path>) and <B id> (<path>).
  > Next: resume the roadmap.
  ```

  The roadmap reconcile then:
  - ticks Stage 5;
  - closes the roadmap's Open question with EV2 and EV3;
  - re-validates the later stages against what shipped.

Sequencing:
- Plan B needs plan A's frozen real pilot.
- Stage 6 needs plan B, since it annotates the acquired pilot releases.
- Stage 15 needs Stage 14 as well as this stage.

On each plan's completion, refresh the "Current state" section of `CLAUDE.md`. In the
handoff, state:
- which commands ran;
- every live request, by gate, with its count;
- that no model was called.

> Plan A: COMPLETE (2026-09-27) — implemented by plan 7 (specs/plans/completed/7-event-discovery-eligibility-and-acquisition-plan-a.md). Next: write plan B.
