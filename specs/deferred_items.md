# Deferred items

## 1-release-parser-fidelity — 2026-09-25
- [ ] Time parsers without their imports before relying on speed (V2, "Notes on
      ADR 0001 after acceptance", "Fast."): the harness's `parse_seconds`
      includes the library import for edgartools, sec-parser and the control,
      which import inside `parse()`, but not for the walker, so ADR 0001's speed
      comparison is overstated by an unmeasured import time. P16 defines runtime
      without imports. Runtime was neither ranked nor a tie-break, and the
      adapters are frozen as Stage 1's record, so nothing was re-timed. Fix:
      import outside the timed region, then re-time. Size: quick-fix. Revisit if:
      a decision relies on parser speed, such as Stage 3's canonicalizer design
      or an ADR superseding 0001.
- [ ] Compare exactly if the selection rule is reused (V2, Limitations, "Exact
      ties"): `expirements/parser-fidelity/select_parser.py` compares
      floating-point rates against a 1/n tie margin, so a difference of exactly
      1/n can round either way, and the control check can count a spurious win.
      No Stage 1 difference sits at 1/n, so no number changed, and the rule
      cannot change after scoring (P11). Fix: compare integer counts or
      `fractions.Fraction` rates, with a test at exactly 1/n. Size: quick-fix.
      Revisit if: the rule or `select_parser.py` is reused for another
      selection, such as a re-measurement under ADR 0001's superseding triggers.
- [ ] Keep `EDGAR_IDENTITY` out of the lock gate's adapter processes (V2,
      "Deviations from the plan", "The lock gate's environment"):
      `lock_gate.parse_fixtures` in `expirements/parser-fidelity/lock_gate.py`
      passes the whole environment to the adapters, unlike the candidate
      runner, which `f2a644e` scrubbed. Adapter output is not logged there and no
      file holds the identity; the gate stays as it ran, as Stage 1's record.
      Fix: pass the runner's scrubbed environment, with a test that the identity
      is absent. Size: quick-fix. Revisit if: the lock gate runs again, such as
      to re-check a sec-parser release under ADR 0001.

## 5-structure-aware-canonicalization — 2026-09-26
- [ ] Keep the capturing machine's paths out of committed captures (final
      review, Important #2; before the first push the user chose to record it
      rather than rewrite the captures): in `tests/fixtures/browser/`, the
      blocked-request URLs of seven release captures carry this Mac's temporary
      directory (`file:///private/var/folders/…/earnings-capture-<random>/page/<image>`).
      `SeleniumRenderer` writes them, in
      `packages/earnings-ingestion/src/earnings_ingestion/browser/selenium_capture.py`,
      which plan 5's pre-registration froze, and no metric reads them. Fix: have
      `tests/integration/capture_browser_fixtures.py`, or the adapter under a new
      capture policy version, write a fixed placeholder for the scratch prefix.
      Size: quick-fix. Revisit if: the committed captures are regenerated, such
      as for a new pin or capture policy version.
- [ ] Report `browser setup`'s ordinary failures in one line (final review,
      Minor #5): `apps/earnings-pipeline/src/earnings_pipeline/cli.py` catches
      only `ValueError`, so an `httpx.HTTPError`, an `OSError`, or
      `subprocess.TimeoutExpired` from `reported_version` prints a traceback.
      Size: quick-fix. Revisit if: a real install fails with a traceback, or the
      CLI gains a second command.
      → triggered 2026-11-13: The CLI now registers seven command groups (browser, cohort, events, extract, pilot, codebook, gold) in apps/earnings-pipeline/src/earnings_pipeline/cli.py. The second group, cohort, arrived in b9603b1 (2026-09-26) and events in 73e6fbc (2026-09-27). The browser setup handler still catches only ValueError. The item is still open.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Three small robustness fixes (final review, Minor #6):
      - `install` in
        `packages/earnings-ingestion/src/earnings_ingestion/browser/install.py`
        ends with `assert done is not None`, which `-O` strips.
      - `tests/integration/capture_browser_fixtures.py` writes whatever the store
        returns, though its docstring promises fixtures without screenshots.
        Only `tests/integration/test_browser_fixtures.py` would catch a stored
        capture that has some.
      - `browser/store.py` stamps failure files with a literal `Z`, though
        `unrendered` accepts any aware time.
      Size: quick-fix. Done when: `install` raises explicitly, the capture script
      drops screenshots before writing, and the store converts to UTC, with a
      test for the script.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Separate words split by `<br>` in table cells (final review, Minor #7;
      R3.5's second leg): `walker-1` canonicalizes Becton Dickinson's header
      cells `Foreign<br>Currency<br>Translation`
      (`tests/fixtures/releases/0000010795-22-000014_ex-99-1/source.html`) as
      `ForeignCurrencyTranslation`. These are the two "other" hunks of leg 2 in
      `docs/verification/R3.5-text-fidelity.md`. A change to canonical text needs
      a new policy version (SC14), and table cells stay outside narrative
      extraction (R4.2). Size: plan. Revisit if: a stage needs cell-text
      fidelity, such as Stage 7's cell evidence or Stage 10's evidence views, or
      a `walker-2` is planned for another reason.

## 6-point-in-time-djia-cohort — 2026-09-26
- [ ] Four stale claims (final review, Minor; paths under
      `packages/earnings-ingestion/src/earnings_ingestion/` unless given in full):
      - `fetch/robots.py`'s docstring says a response the client gives up on
        disallows everything, but `client.get` raises `AccessStop`, which
        propagates out of `verdict`.
      - `cohort/web.py`'s docstring says the client reaches only registered
        sources' hosts, but `cohort_cli.py` opens it for whatever hosts its URLs
        name, and `fetch_page` in `cohort/acquire.py` checks that the source
        exists, not that the URL's host is the source's.
      - `LocatorKind.TEXT_SPAN`'s docstring in `cohort/records.py` names HTML
        only, and `cohort/pdftext.py`'s module docstring says pypdf's logger is
        held "below ERROR", where the code holds it at ERROR.
      - `README.md`'s `docs/` row omits the membership register, the
        `djia-cohort` record, ADR 0002, and the Stage 3 records.
      Size: quick-fix. Done when: each claim matches the code, or `fetch_page`
      checks the URL's host against its source, with a test.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Decide what an override's dates mean (final review, Minor, and Codex's
      review of PR #5): every `Override`
      records `effective_from`, and optionally `effective_to`, and
      `docs/data-dictionary.md` describes them as the period the decision covers,
      but nothing under
      `packages/earnings-ingestion/src/earnings_ingestion/cohort/` reads them, so
      a `holding_alias` or `set_issuer` applies on every date. The frozen v1 shows
      it: `ibm-common`'s interval and anchor assertion start on 2024-06-24, the
      anchor's date, but `ibm-issuer` and `alias-ibm` take effect on 2024-07-01.
      IBM's CIK is the same on both dates, so nothing is misattributed, but a rule
      that scopes overrides must say whether an override covers the part of an
      interval inside the window or its whole span. `OverridesFile` also refuses a
      `holding_name` that two `holding_alias` overrides share; scoping could relax
      that to periods that do not overlap. Size: design.
      Done when: the dictionary says the dates are a record only, or the build
      scopes each override by them, with a test.
      → acknowledged 2026-11-13 (claude/deferred-6fe05c): changes only a new cohort version; cohort v1 is frozen and Stage 15 consumes it unchanged.
- [ ] Decide whether a fund report's holdings match only names cited by its date
      (Codex's review of PR #5): `match_holdings` in
      `packages/earnings-ingestion/src/earnings_ingestion/cohort/corroboration.py`
      matches each holding against every name published by the cutoff, including
      names whose `observed_on` falls after the report's date, so a later name
      could match an earlier holding and hide a difference. Filtering by
      `observed_on` changes nothing in v1: rebuilt in memory with the filter, which
      drops as many as six names from a report, no reconciliation and not the
      content hash changes. But a name's first citation is not its start, so the
      filter would turn a rename cited only after a report into a blocking
      difference until a reviewer adds a `holding_alias`. Decide it with the
      override dates above, so that names and overrides are scoped alike.
      Size: design. Done when: the decision is recorded, and a test shows whether a
      name cited after a report's date matches that report's holding.
      → acknowledged 2026-11-13 (claude/deferred-6fe05c): changes only a new cohort version; cohort v1 is frozen and Stage 15 consumes it unchanged.
- [ ] Let `verify-live` re-read the other hosts after one refuses (final review,
      recommendation; P6-20): `verify_live` in
      `packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py` sends
      every non-SEC check through one web client, which stops at the first
      persistent 403. On 2026-09-26 S&P Global's host refused at robots.txt, and
      the Wikimedia terms, both S&P DJI notices, and the Wikipedia anchor went
      unrequested (`docs/verification/djia-cohort.md`, Limitations). Options: a
      web client per host, or refusing hosts checked last; either needs a
      decision on whether AGENTS.md's stop on a persistent 403 covers the run or
      one host. Size: design. Done when: that decision is recorded, and a test
      shows that a refusal on one host leaves the other hosts' checks requested.
      → acknowledged 2026-11-13 (claude/deferred-6fe05c): verify-live is an owner-run check of the frozen cohort, and no run of it is scheduled.

## 7-event-discovery-eligibility-and-acquisition-plan-a — 2026-09-27
- [ ] Report the cohort CLI's override and terms errors as `problem:` lines
      (plan 6's "Three robustness fixes", part 1, restated by plan 7): `_build`
      in `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py` catches
      only `CohortError`, but a bad override makes `reconstruct`
      (`cohort/intervals.py`), `resolve` (`cohort/resolution.py`), or
      `acknowledge` (`cohort/findings.py`) raise `ValueError`, which prints a
      traceback. `terms_digest` also runs outside any `try` in `cohort_cli.py`'s
      `terms` and in `cohort/live.py`, so a terms page that `walker-1` cannot
      read aborts `verify-live` before its record is written. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/` unless given in
      full. Size: quick-fix. Done when: each case has a test, and each ends as a
      `problem:` line or in `verify-live`'s record.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Show the operative hashes in `verify-live` (plan 7, P7-3): plan 7's Task
      16 named companyfacts in the `sec-edgar` entry of
      `docs/source-register.toml`, and a universe manifest's content hash
      covers that entry through `source_register_version`. So a rebuild of
      cohort v1 no longer reproduces v1's content hash, although its operative
      hash (`cohort/identity.py`), on which Stage 5 keys, is unchanged.
      `earnings-pipeline cohort verify-live` prints and records only
      `rebuilt_content_hash` and `frozen_content_hash` (`cohort/live.py`, and
      `LiveVerification` in `cohort/records.py`), so every run from now on shows
      a difference that no fact explains. Record both versions' operative
      hashes beside them. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: quick-fix.
      Done when: `verify-live`'s output and record tell a register-only change
      from a changed fact, with a test.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Write `release-id/2` (plan 7's Task 20 review, and its final review):
      `release-id/1` in
      `packages/earnings-ingestion/src/earnings_ingestion/events/release.py`
      dropped the only candidate of ten real events, each the release itself, so
      each needed a `set_release_filing` override in
      `config/corpus/djia-2024q3-2026q2/overrides.toml`:
      - its year-first quarter pattern requires "fiscal" before the year, which
        P7-7's prose ("in either order") does not, so in JPMorgan's eight
        releases, which write the year first without it, the rule read only the
        prior-year comparison and the report dates after "ended", none of them
        the slot's period;
      - 3M's release for 2024-09-30 names its quarter without a year and its
        full year with one, which the rule read as FY 2024; Verizon's for
        2024-12-31 names its quarter and full year together in a form outside
        the rule's list, while the older quarters in its long Item 2.02 section
        were read;
      - the drop rule judges every stated period against a sole candidate, so a
        prior-year comparison, a boilerplate report date, or a full-year figure
        can drop the release itself.
      The rule is fixed (the Stage 5 spec, §Candidates): a change is
      `release-id/2`, and so a new event manifest version, with the spec's
      drop rule decided again. Size: plan. Done when: a rebuild under
      `release-id/2` identifies these ten releases with no override, the
      synthetic corpus's identifications are unchanged or re-versioned, and the
      frozen v1 still loads.
      Amended by PR #6's review (2026-09-27, F2 and F15). A false drop can also
      pass the release to another candidate silently. A candidate that states no
      judged period is never dropped, so when the rule drops the true release, an
      unread co-candidate, such as an 8-K that SEC lists with Item 2.02 but whose
      document has no Item 2.02 heading (Caterpillar's `0000018230-24-000047` for
      2024-09-30 is one), becomes the release as `sole_candidate`, with no
      finding and no review. Its earlier acceptance time can change the event's
      eligibility, and an event that turns ineligible is never acquired, so plan
      B's content check never sees it. Both halves occur in v1, though never
      together: each of v1's `sole_candidate` rows had one candidate, and no v1 row
      is wrong. Plan 7 expects a correct `sole_candidate` after a drop when the
      survivor's Item 2.02 text was read but states no judged period, so the case
      to catch is a survivor with no Item 2.02 section. Any rebuild under
      `release-id/1` before this lands adds that build-level gate first. Also, a
      `set_release_filing` outranks the rule and is never stale, as the spec and
      P7-16 intend, but nothing reports whether the rule agrees with it; once
      `release-id/2` exists, a signed override could silently contradict a pick
      the rule now makes. Done when, in addition: a slot where the rule drops a
      candidate and keeps one with no Item 2.02 section either holds the freeze (a
      finding answered by a `set_release_filing`, or an acknowledgement bound to
      its digest) or comes out `ambiguous`, with a sibling of
      `test_a_candidate_with_no_item_2_02_heading_stays` (in
      `packages/earnings-ingestion/tests/test_events_release.py`) in which the
      true release is dropped, and a build-level test that the case holds the
      freeze; and `events build` reports, for each `set_release_filing`, whether
      the rule agrees, names another filing, or resolves nothing, with
      `release-id/2` deciding whether a contradiction holds the freeze. Also
      (PR #6's combined review): a release accepted after its event's next period
      end P′ lies in the next event's range, and when its text states no judged
      period, `release-id/1` makes it that event's release as `sole_candidate`.
      Since PR #6 bounds a `set_release_filing` to `(P, P′]`, no override can give
      it back to its own event, and no override can take a rule's pick away from
      an event that is not `ambiguous`. `release-id/2` decides both.
      Before it freezes a new events version, the per-candidate citations item
      under PR #6's review lands too.
      → acknowledged 2026-11-13 (claude/deferred-6fe05c): needed only before a new events version; Stage 15 consumes events v1 unchanged, and no new version is planned.
- [ ] Report `events freeze`'s citation errors as `problem:` lines (plan 7's
      final review, Minor): `freeze_command` in
      `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py` catches only
      `EventFreezeRefused`, but `freeze_events` (`events/freeze.py`) builds the
      evidence record with `evidence_of` (`events/evidence.py`), which raises
      `LocatorError`, a `ValueError`, when a value it cites is not in a saved
      page's `walker-1` text, so the command prints a traceback. Nothing is
      written, since the record is built before either file. PR #6's corpus fix
      (F5) then gave `freeze_command` an `except ValueError` after
      `EventFreezeRefused`, so this case now ends as `Refused: <error>` with exit
      1, not a traceback; it is still untested, and it says `Refused:` where the
      done-when asks for `problem:`. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`
      unless given in full. Size: quick-fix. Done when: such a case has a test
      and ends as a `problem:` line.
      Widened by PR #6's review (2026-09-27, F23, F36, and F37). Every `events`
      command has loads and writes outside any handler for their error type, so
      each case below ends in a traceback, not a `problem:` or `Refused:` line.
      Each fails closed, with no partial file and no request after the failure,
      except a freeze that fails between its two writes (the third bullet), which
      leaves its evidence record behind.
      - `load_overrides` (`events/build.py`) raises `TOMLDecodeError`, or a
        pydantic `ValidationError` for a repeated `override_id`, a second
        override of one kind, or an extra key, and `_build` in `events_cli.py`
        catches only `EventBuildError`. Wrap only the `load_overrides` call in
        `except (OSError, ValueError)` and print `problem: <path>: <error>`; do not
        widen the handler around `build_events`, since `EventBuildError` and
        `LocatorError` are `ValueError`s too. Treat the cohort's overrides loader
        in `cohort_cli.py` the same way, with the first item of this section.
      - `Layout.universes()` runs outside any handler in every command,
        `SavedResponses` in build and freeze, and `write_new` in freeze and select
        (PR #6's F5 fix put select's `frozen_event_manifests` inside a `ValueError`
        handler, so a tampered event manifest already ends as `Refused:`). So a
        tampered universe manifest, an empty or
        truncated retrieval record (a `ValidationError` that names no file), or
        two racing selects (`FileExistsError`) print tracebacks, and `events
        discover` advises a rerun that meets the same stop. `universes()` should
        refuse with `Refused: <path>: <error>`; select's loads move inside its
        `try`, which also catches `FileExistsError` and says to rerun `events
        select` (PR #6's F5 fix moved `frozen_event_manifests` inside a
        `ValueError` handler; `FileExistsError` is still uncaught); an
        unreadable retrieval record becomes a `problem:` line naming
        its path, which discover names instead of advising a rerun; and
        `freeze_command` catches `(OSError, ValueError)` after `EventBuildError`.
        `ArtifactStore.retrievals` and `latest` can follow, or wait for the
        store-recovery item under PR #6's review below.
      - `freeze_events` (`events/freeze.py`) writes the evidence record first, so
        a crash before the manifest is written leaves `events-v<N>.evidence.json`
        alone. An unchanged retry heals it, but a retry after a re-fetch or a
        changed fact raises a `FileExistsError` that does not name the cause, on
        every later freeze. When the evidence file exists without its manifest and
        its bytes differ, raise a named refusal that tells the user to delete the
        leftover file; never overwrite it.
      Size, as widened: plan. Done when, in addition: a repeated `override_id`, a
      second override of one kind, and a TOML syntax error each end `events build`
      and `events freeze` with a `problem:` line; a tampered universe manifest
      makes build refuse cleanly; an empty retrieval record ends build with a
      `problem:` line naming
      its path; and a leftover evidence file with other bytes gives the named
      refusal while an identical one still completes the freeze; each with a test
      and no traceback.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Cite the Item 2.02 text of a release an override names outside the
      candidates (plan 7's final review, Minor): `_event` in `events/evidence.py`
      sets `item_text` only when the event's release is one of `release-id/1`'s
      candidates, as plan 7's Task 13 specified, but the Stage 5 spec's evidence
      record cites each release's Item 2.02 span, and plan 7's review table lets
      a `set_release_filing` name an 8-K the rule passed over. Such an event
      would freeze with `item_text` null, and its primary document may not be
      saved. Every event of `config/corpus/djia-2024q3-2026q2/events-v1.json`
      has its span. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`.
      Size: quick-fix. Done when: an override naming a passed-over 8-K either
      freezes with its Item 2.02 span cited or is refused by `build`, with a
      test.
      The per-candidate citations item under PR #6's review touches the same
      `item_text` code; land the two together.
      → acknowledged 2026-11-13 (claude/deferred-6fe05c): needed only before a new events version; Stage 15 consumes events v1 unchanged, and no new version is planned.
- [ ] Bound the periodic reports that can block on acceptance time (plan 7's
      final review, Minor): `issuer_filings` in `events/filings.py` passes every
      periodic report with a `reportDate` to `_visible`, so one whose index page
      is not saved and whose `acceptanceDateTime` is empty becomes an
      `acceptance_time_unknown` finding that holds the freeze, however old it
      is. A release 8-K is reported for a missing `acceptanceDateTime` only when
      filed on or after the window's start. None arose in v1. A bound must keep
      the reports that the slots and their `period_gap` guards read, including
      the last one before the window (`events/slots.py`). Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`.
      Size: quick-fix. Done when: a test shows that an old periodic report with
      no `acceptanceDateTime` neither holds the freeze nor changes a slot.
      Amended by PR #6's review (2026-09-27, F7). The remedy P7-8 gives for
      `acceptance_time_unknown`, saving the filing's index page with
      `earnings-pipeline events discover --filing` and rebuilding, does not clear
      a row with no `acceptanceDateTime`. Once the page is saved, `survey` in
      `events/acceptance.py` cross-checks the row, `convention_of` finds no
      convention for the missing value, and `issuer_filings` makes it a blocking
      `acceptance_time_mismatch`, which no override can acknowledge. So an
      in-window periodic report, or an Item 2.02 8-K, with no value holds the
      freeze for good, and a date bound does not help. The 8-K trigger in
      `issuer_filings` also has no upper bound: a no-value Item 2.02 8-K filed on
      or after the window's start blocks even when it was filed after the cutoff,
      and can never be an event. None arose in v1: none of the 112,236 rows the v1
      build reads has an empty value. The user chooses between two readings:
      - (a) a missing value is nothing to cross-check: the index page places the
        filing, and its cross-check is null, recorded beside EV10 and P7-8; or
      - (b) it stays a permanent block, and P7-8, the module docstrings of
        `events/discover.py` and `events/filings.py`, the `build_command`
        docstring in `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py`
        and the `events discover --filing` hint it prints for each
        `acceptance_time_unknown` finding (both added by PR #6's P4.4 fix), and
        the `acceptance_time_unknown` row of `docs/data-dictionary.md` stop
        promising that saved data clears it. PR #6's
        `test_build_names_each_blocking_finding_s_own_remedy` (in
        `apps/earnings-pipeline/tests/test_events_cli.py`) builds its unknown from
        a row with no value, the one case where the `--filing` hint cannot clear
        it; under either reading, move its hint assertion to a value whose file
        establishes no convention, and pin the chosen wording for a no-value
        row.
      With either, bound the 8-K trigger from above with a margin past the
      cutoff: a filing accepted after 17:30 takes the next business day's filing
      date, so its filing date can fall after its acceptance date. Size, as
      amended: design until the user chooses, then quick-fix. Done when, in
      addition: the chosen reading is recorded;
      `test_a_missing_value_is_unknown_unless_filed_before_the_range` (in
      `packages/earnings-ingestion/tests/test_events_filings.py`) goes on to save
      each unknown filing's index page and asserts the chosen outcome (under (a),
      no finding, the report among the periodic reports, and the 8-K among the
      releases); a build-level test takes an emptied 10-Q through its saved index
      page to the freeze; and a no-value Item 2.02 8-K filed past the cutoff's
      margin raises no finding.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Refuse a repeated acknowledgement (plan 7's final review, Minor):
      `EventOverridesFile._distinct` in `events/records.py` refuses a repeated
      `override_id` and, per P7-14, a second override of one kind for one
      `event_id`, but an `acknowledge` override names a `finding_id`, not an
      `event_id`, so two acknowledgements of one finding both load. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`.
      Size: quick-fix. Done when: `EventOverridesFile` refuses a `finding_id`
      repeated among acknowledgements, with a test.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md

## PR #6 review (plan 7) — 2026-09-27
- [ ] Decide what identifies the event manifest when a store is rebuilt (PR #6's
      review, F27): `EventManifest`'s content hash in `events/records.py` hashes
      each override whole, and each `set_release_filing` cites an index page by its
      artifact hash and a locator, which `_citations_refused` in `events/build.py`
      looks up in the store. `data/raw/events/` is never committed, so on another
      machine, or after a fresh discovery, SEC serving a cited page with other
      bytes, even with the same `walker-1` text, refuses the override until it is
      re-cited, and the re-cited override re-versions the manifest and re-seeds the
      pilot (`pilot_seed` in `events/pilot.py` takes the content hash), though no
      fact changed. That falls short of EV11's aim that a re-fetch never re-versions
      a manifest; `docs/verification/djia-events.md` records it under Limitations.
      Stage 4 closed the same gap with an operative hash (`cohort/identity.py`) that
      leaves overrides out. Options: hash only an override's decision fields (its
      kind, targets, and reason, not its citations), or give the event manifest an
      operative identity for the pilot's seed to key on. Either changes events v1's
      content hash or its pilot's seed, so it lands only with a new events version,
      and the committed v1 must stay loadable. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: design. Done
      when: the decision is recorded, and a test shows that re-citing an override's
      page from other bytes leaves the chosen identity and the pilot's seed
      unchanged.
      → acknowledged 2026-11-13 (claude/deferred-6fe05c): needed only before a new events version; Stage 15 consumes events v1 unchanged, and no new version is planned.
- [ ] Bind each evidence citation to its artifact's retrievals (PR #6's review,
      F21; the rest of plan 7's "Bind an evidence record to its manifest when
      loading", which PR #6 closed): `check_evidence` in `events/evidence.py`
      verifies each citation's bytes and locator only, so a record passes with a
      citation or `files[]` URL re-pointed to another URL, a `source_id` other
      than `sec-edgar`, or a `retrieved_at` that matches no retrieval. PR #6 made
      loading bind the record to its manifest's rows. Records are built from the
      store and only tests read them, so this hardens the audit trail.
      `cohort/build.py` and `_citations_refused` in `events/build.py` already
      check a citation's URL against its artifact's retrievals. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: quick-fix.
      Done when: `check_evidence` refuses a citation or `files[]` URL that is
      not among its artifact's retrievals' request URLs, a `source_id` other than
      `sec-edgar`, and a `retrieved_at` that matches no retrieval, and each row's
      release citation is its release's index page, unless loading already
      checks it; each with a test, while the real and synthetic v1 records still
      pass.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Bind older submissions pages to their dates, and pad the page skip (PR #6's
      review, F11 and F24): `read_older_page` in `sec/data.py` binds a page to
      its entry by `filingCount` alone (PR #6's third Codex round), and
      `issuer_filings` in `events/filings.py` skips a page whose `filingTo` is
      before the window's start or whose `filingFrom` is after the cutoff, as the
      Stage 5 spec's §Store, client, and readers "Older pages" bullet says.
      - SEC can re-cut page boundaries between runs, and discovery never
        re-fetches a saved main file, so a resumed run can pair a main file of one
        day with pages of another, and a re-cut page with the same count passes.
        A filing then listed in two files would become two candidates, which PR
        #6 now reports as a problem, but a filing that drifts into a skipped page
        drops out with no problem raised, and only a `period_gap` guard can catch
        it. Every observed outcome fails loudly or holds the freeze, and the 19
        pages behind v1 have distinct counts, so a re-cut would almost surely
        change one.
      - `filingFrom` and `filingTo` are filing dates, not acceptance dates. A
        filing accepted after 17:30 takes the next business day's filing date, so
        a page can hold filings accepted one to three days before its
        `filingFrom` (15 of the 19 pages behind v1 do), and a page skipped for
        starting the day after the cutoff can hide a filing accepted on the
        cutoff's evening. On all 19 pages, `filingTo` is the next-newer page's
        `filingFrom` less two days, a day off the page's last filing date either
        way, while the `SkippedPage.filing_to` row of `docs/data-dictionary.md`
        calls it the page's last. This is reachable only by discovery from a
        fresh store about a year after 2026-09-22, or under a cutoff deep in the
        older pages.
      Do not require the latest date within a day of `filingTo`: a long weekend
      breaks that. Recovering from a caught re-cut needs a fresh store (see the
      store-recovery item below). Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: plan. Done
      when: each page's dates must stay below the next-newer page's
      `filingFrom`, or the recent block's earliest date, and optionally its
      earliest date must equal its `filingFrom`, so that a page with the right
      count but shifted dates is refused; the spec's bullet is amended to read a
      page unless its `filingTo` is before the start less a few days or its
      `filingFrom` is after the cutoff plus about seven days, and a synthetic
      older page whose only filing was accepted on the cutoff at 18:00 ET, with
      `filingFrom` the next business day, is read and its filing stays visible;
      the dictionary's `filing_to` row is corrected; and events v1 still rebuilds
      unchanged.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Cite the index page that places a periodic report (PR #6's review, P5.4):
      after P7-8's `--filing` remedy, `_visible` in `events/filings.py` places a
      periodic report by its saved index page, but `_event` in
      `events/evidence.py` cites only its submissions row, whose
      `acceptanceDateTime` was the ambiguous value, and `EventCitations` has no
      field for the page. So the page's URL, hash, and retrieval time appear
      nowhere in the evidence record. The spec's list of citations is met to the
      letter, and v1 never took this path. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: quick-fix.
      Done when: `EventCitations` gains `periodic_accepted: Citation | None =
      None`, whose default keeps the committed v1 evidence loading, filled with
      the page at its Accepted value when the page placed the report and among
      the citations `check_evidence` verifies; `docs/data-dictionary.md`
      documents it; the synthetic evidence fixture is regenerated for its new
      null field; and a synthetic build whose report is placed by a saved index
      page cites that page.
      → acknowledged 2026-11-13 (claude/deferred-6fe05c): needed only before a new events version; Stage 15 consumes events v1 unchanged, and no new version is planned.
- [ ] Refuse two findings that share one `finding_id` (PR #6's review, P4.3):
      each copy of a filing row that follows no convention, or has no value,
      emits its own `acceptance_time_mismatch` or `acceptance_time_unknown`
      finding under one ID, and `EventManifest` refuses the repeated ID with a
      pydantic `ValidationError`, which `events build` prints as a traceback,
      because it reads the content hash before its exit on a held freeze.
      `events freeze` refuses cleanly first, so nothing corrupt can freeze. PR #6
      refused an accession listed twice in one issuer's files, but a finding's ID
      names no issuer, so an accession listed under two cohort issuers can still
      collide. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: quick-fix.
      Done when: `build_events` in `events/build.py` counts finding IDs before it
      resolves them and reports each repeat as an `EventBuildError` problem, and
      `events build` over a store with a repeated mismatch row exits 1 with a
      `problem:` line and no traceback, with tests.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [x] Recover a saved response that is present but unusable (PR #6's review, P2.1
      and P2.2): discovery (`events/discover.py`) fetches only URLs with no
      retrieval record, and `issuer_filings` in `events/filings.py` reports a
      file whose bytes are gone or changed, or that a reader refuses, as a
      problem, never as missing. So `events discover` fetches nothing for it,
      `--filing` cannot refetch a saved index page, `discover_filing`'s hint to
      run `events discover` cannot help, and the build stops on the file for
      good; the only way out is deleting store files by hand, which the
      append-only store forbids. Worse, `write_new` in `fetch/store.py` treats an
      artifact whose bytes no longer hash to its name as a conflict, so once an
      artifact is truncated and its record lost, every refetch spends a request
      and ends in an uncaught `FileExistsError`. With no fsync before the link,
      an OS crash or power loss can leave that state, though killing the process
      cannot. It fails closed, and the trigger is local damage or a wrong-shape
      response that is not a block page. Meanwhile, document the manual repair in
      `docs/verification/djia-events.md`. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: plan. Done
      when: `issuer_filings` and identification tell an unusable response from a
      missing one; an explicit opt-in refetch states its count first and can
      refetch a submissions file with its older pages; the store quarantines
      bytes that no longer hash to their name by renaming them, never deleting or
      replacing a valid file, `cohort/acquire.py` included, and syncs before the
      link; each problem line names a remedy that works; and a test truncates a
      fixture index page, runs the opt-in refetch over a fake fetch, sees exactly
      that URL fetched, and rebuilds the synthetic events v1 content hash.
      → planned 2026-11-13: specs/plans/25-recover-unusable-saved-responses.md
      → done 2026-11-13 (plan 25): the primary document of a filing that `release-id/1`
      passes over stays a manual repair → item: 25-recover-unusable-saved-responses — 2026-11-13
- [ ] Read companyfacts in discovery through the problem-collecting reader (PR
      #6's review, P2.3): in the documents phase of `discover` in
      `events/discover.py`, the saved read of each issuer's companyfacts and
      `read_companyfacts` run outside the reader that collects problems, so one
      gone, changed, or wrong-shape companyfacts file ends the phase, for every
      issuer, before any primary document is fetched. A `SecDataError` stops with
      a message naming no URL and a rerun hint no rerun can satisfy, and a
      missing body raises `FileNotFoundError`, a traceback that also loses the
      requests-sent line (see the request-count item below). Discovery also skips
      the build's companyfacts CIK check. The read-back that PR #6's F18 fix
      added, `_unreadable` in the same file, repeats that unguarded read, so
      guard both. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: quick-fix.
      Done when: discovery reads companyfacts through a shared version of the
      build's tolerant read with its CIK check (`_companyfacts` in
      `events/build.py`), records the problem with the discovery problems PR #6
      added, skips that issuer, and reports it after the documents phase; with
      one synthetic issuer's companyfacts truncated, discovery still fetches
      another issuer's missing primary document and names the companyfacts URL;
      and a vanished companyfacts artifact ends as a handled stop with the count
      printed.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Refuse a fund filing listed twice in the cohort build (PR #6's review,
      P4.1): `_fund_filings` in `cohort/build.py` joins the fund's recent block
      and its saved older pages without checking for a repeated accession, so
      `current_filings` in `cohort/corroboration.py` emits a non-blocking finding
      that names the filing as its own replacement, or, for a late filing,
      repeated withheld findings and reconciliations under one ID. The cohort then
      freezes a new content version carrying a false statement, though its
      operative hash does not move. This Stage 4 code predates PR #6, and DIA's
      saved file has no older pages and no repeats. PR #6 refused the same repeat
      among an issuer's files in the event build. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: quick-fix.
      Done when: a synthetic fund whose recent block and older page share one
      N-PORT makes the cohort build raise `CohortError` naming that accession and
      each copy's pointer, never deduplicating it, with a test.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Decide whether two issuers' events may share one release (PR #6's review
      of its F1 fix): `shared_releases` in `events/build.py` refuses a
      `release_accession` that two rows share anywhere in the corpus, as the
      Stage 5 spec says ("No two events share a release"). A co-registrant 8-K
      that `release-id/1` identifies as two cohort issuers' release would then
      stop the build with a problem that no override can settle, since each
      issuer's own files list it. No two v1 issuers are co-registrants, so v1 is
      unaffected. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: quick-fix,
      after the user's decision. Done when: the user chooses per-issuer or
      corpus-wide, the spec says which, and a synthetic co-registrant 8-K shows
      the chosen behavior in a test.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
- [ ] Cite each candidate's qualifying fields and primary document (PR #6's Codex
      round 5, comment 4117725089): the Stage 5 spec's evidence list (§The event
      manifest), which `_event` in `events/evidence.py` follows, cites a candidate
      only by its index page at its Accepted value, and the Item 2.02 text of the
      release alone; P7-15 keeps readings out of the record. AGENTS.md asks each
      assertion for a checksum and a field-level locator, and keeps conflicting
      observations. So no locator cites what qualified a candidate (Item 2.02 in
      its submissions row, an `EX-99*` row on its index page), no hash pins a
      non-release candidate's primary document or the text that dropped it, and a
      filing passed over for want of an `EX-99*` exhibit is in no record. In v1
      that is six candidates and two filings, which the Limitations of
      `docs/verification/djia-events.md` name; no v1 row is wrong, and v1's
      evidence record is never replaced. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: plan. It lands
      before the next events version is frozen (see the `release-id/2` item),
      together with the item on the Item 2.02 text of a release an override names
      outside the candidates, which touches the same code. Done when: the spec's
      evidence list is amended; `EventCitations` gains an optional per-candidate
      field, absent when not recorded so that v1 still loads, whose entries cite
      each candidate's submissions row at `form`, `items`, and `primaryDocument`,
      its index page's Item 2.02 line and each `EX-99*` row, its primary document
      by hash with its Item 2.02 spans (with no locator when the rule could not
      read it), and `release-id/1`'s outcome for it; a passed-over list cites each
      such filing's index page and reason; `check_evidence` and
      `load_event_evidence` cover the new fields, binding them to each row's
      `candidate_accessions`; the data dictionary and its drift test follow; and
      the synthetic evidence fixture regenerates, with tests for a dropped
      co-candidate, an unread candidate, and a passed-over filing. Recording each
      candidate's reading as a fact would reverse P7-15, so that is the user's
      open choice; if adopted, the readings are marked as inferred.
      → acknowledged 2026-11-13 (claude/deferred-6fe05c): needed only before a new events version; Stage 15 consumes events v1 unchanged, and no new version is planned.

## 9-pilot-codebook-split-and-gold-set-protocol — 2026-10-03

- [x] Draft, verify, and sign the other 17 train and 8 dev bundles of pilot v1
      (plan 9, Handoffs). Stage 6's exit needed three; Stage 11 uses all 28.
      Each follows plan 9's Task 19, Steps 1 to 7
      (specs/plans/completed/9-pilot-codebook-split-and-gold-set-protocol.md):
      a fresh Claude Opus 5.5 session per bundle under
      evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md, then the user's
      verification, omission pass, and signature. Size: plan. Done when: all 28
      train and dev gold files under evaluation/djia-2024q3-2026q2/pilot-v1/gold/
      are committed and `earnings-pipeline gold validate` passes. Amended
      2026-10-11 (Stage 6 spec, GS19): each of the 8 dev bundles first gets the
      user's independent pass, with its ledger row committed before drafting, and
      waits for the `--independent --check` item below. Pilot order's #2 and #4
      are dev. Train bundles proceed unchanged.
      → retired 2026-11-13: 28 gold files in evaluation/djia-2024q3-2026q2/pilot-v1/gold on main; docs/verification/pilot-v1-feasibility.md "O6 gate, 2026-10-31 (D21-26)" records 28 valid and signed under `gold validate`, exit 0, at `66d4e55` (PRs #31, #32); the validate result comes from that record and was not re-run.
- [x] Harden the gold before the next Task 19 bundle is anchored (plan 9's final
      review: M1, T8-M1, and M5, deferred by the user on 2026-10-03). (1) `_ids`
      in packages/earnings-themes/src/earnings_themes/annotation.py accepts a
      claim with no assignment row, and a quote that no claim or hard negative
      cites, though R9.9 codes every claim (a theme or `unmatched`): refuse both,
      with a new `Problem` member and its row in docs/data-dictionary.md; the three
      committed bundles already pass. (2) `build_gold` and `build_curated` take
      `drafting_aid` from the working copy, not the kept draft, so an edit there
      would change the recorded model or date (GS5): take it from the draft, and
      confirm by byte compare that the three committed bundles and
      tests/fixtures/gold/hard-negatives.toml re-anchor unchanged. (3) Count, by a
      program that prints counts only, the narrative sentences of the 40 pilot
      documents that sit in a walker-1 list item under an `other` element, which
      `anchor` refuses as `not_narrative`
      (packages/earnings-themes/src/earnings_themes/anchoring.py:119-120, T6-M1);
      Stage 1's fixtures hold 10 such sentences, in 1 of 8. Size: plan. Done when:
      (1) and (2) land with their tests, and (3)'s count is in
      docs/verification/pilot-v1-gold-set.md, before any further bundle is
      anchored. → done in plan 10 (specs/plans/completed/10-harden-the-gold-before-bundle-4.md)
- [x] Move `canonical_json` and its digest into earnings-core (plan 9, Task 3; the
      user's decision of 2026-09-28; final review M6).
      packages/earnings-themes/src/earnings_themes/records.py:75-91 copies them
      from packages/earnings-ingestion/src/earnings_ingestion/cohort/digests.py,
      since themes may not import ingestion and Stage 6 left earnings-core
      unchanged (GS17); records.py:48-57 also repeats the pilot pin that
      packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py:60-70
      defines. Each copy is pinned by its own package's reproduction tests.
      Size: plan. Done when: in the first stage whose spec may change
      earnings-core, both packages import one core definition of each, and every
      committed record (cohort, events, split, coverage report, codebook v0, gold,
      and hard negatives) still reproduces byte for byte. → done in plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md)
- [ ] Stage 6's test and validation gaps that the final review deferred (plan 9's
      ledger Minors, triaged 2026-10-03). Under packages/earnings-themes/ unless
      named: the pin's `universe_version` comes from the caller's universe, not the
      pilot's definition (packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py,
      T2-M1);
      `pilot_pin`'s two chain refusals are untested (T2-M2); `canonical_json`,
      `digest`, `record_json`, `describe`, `read_json`, `parse`, and refusal
      ordering have no direct test (records.py, T3-M5); nor do `partition_of`'s
      `KeyError`, `events_in`, a row's reason only when excluded, or the
      fixed-windows check (split.py, T4-M3); the Stage 1 anchoring test accepts any
      result past 500 of 686 sentences instead of pinning exact counts (T6-M2);
      `bundle_problems` has no production caller, and its mask branch is untested
      (anchoring.py:100-112, T6-M4); P9-19's type order is untested for list items,
      footnotes, speaker turns, and sections (T6-M5); several validate and freeze
      branches are untested (codebook.py, T7-M1); `build_synthetic` gives every
      synthetic bundle one `doc_id`, so a cross-bundle swap is a no-op
      (synthetic.py:49, T7-M6); `validate_curated` turns a missing document
      into a spurious `counts_mismatch` and never refuses a duplicate fixture ID
      (annotation.py, T8-M2); the views have no direct test (view.py, T9-M1); the
      import boundary blocks httpx but not requests, aiohttp, or urllib3 (T9-M2);
      `fixture_event_ids` is never tested with a match (apps/earnings-pipeline,
      stage6.py, T10-M1); the ADR's citation of the hash is checked in two places,
      and freeze never re-validates the bytes it writes (codebook_cli.py and
      codebook.py:346, T11-M2); several CLI branches are untested and one
      assertion is vacuous (apps/earnings-pipeline/tests/test_stage6_cli.py:432-438;
      T11-M3, T11-M4, T11-M6, T12-M6); `gold anchor --check` returns before the
      committed-content pre-check (gold_cli.py, T12-M2); the hard-negatives
      offline test runs in the real checkout rather than a copy of the committed
      files (T13-M1); and `pinned_codebook` loads v0 without rehashing it
      (codebook_cli.py:150-158). Size: plan. Done when: a plan lands each with its
      test, or records why one is dropped. T8-M2 and T6-M2 → done in plan 10
      (specs/plans/completed/10-harden-the-gold-before-bundle-4.md). T3-M5's
      `canonical_json` and `digest` → done in plan 11
      (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md).
      T6-M4 and T9-M2 → done in plan 12
      (specs/plans/completed/12-evidence-selection-and-verification-plan-b.md).
- [x] Settle two anchoring questions before Stage 7 recomputes context hashes or
      fixes its narrative set: pin `context_hash`'s byte format with a
      known-answer test, and add `ensure_ascii=False` to its row in
      docs/data-dictionary.md (T6-M3); and decide whether a list item under an
      `other` element becomes quotable, using the count the bundle-hardening item
      above records (T6-M1). Code: packages/earnings-themes/src/earnings_themes/anchoring.py.
      Size: plan. Done when: Stage 7's plan lands both, or records why not. → done in plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md)
- [x] Refuse a committed test-partition gold at validate time (T12-M1):
      `gold validate` never calls `readable()`, so a hand-committed test bundle
      would validate before Stage 14
      (apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py). Size: quick-fix.
      Done when: `gold validate` refuses test gold, with a test, or Stage 14's
      commit relaxes `readable()`.
      → done 2026-11-13 (/deferred quick fix): `gold validate` refuses committed gold that `readable()` holds back, test or excluded, before its bundle is loaded; test `test_gold_validate_refuses_test_gold_before_reading_its_bundle`.
- [x] Hold `codebook freeze --adr` to a repo-relative path under docs/adr/
      (T11-M1); v0's committed path is. apps/earnings-pipeline/src/earnings_pipeline/codebook_cli.py.
      Size: quick-fix. Done when: it lands with a test, before codebook v1 is
      frozen.
      → done 2026-11-13 (/deferred quick fix): `codebook freeze --adr` refuses an absolute path, a path with `..`, and a path outside docs/adr/ before anything is written; test `test_codebook_freeze_takes_adr_only_under_docs_adr`.
- [x] Watch `fail(f"Refused: {error}")`, which prints an error's raw text at
      apps/earnings-pipeline/src/earnings_pipeline/stage6.py:178,199 and
      pilot_cli.py:69-70,95-96 (T10-M3). Today its inputs are config and state
      rows, never document text. Size: quick-fix. Revisit if: a stage writes free
      text to the state table or to the pilot's records.
      → retired 2026-11-13: `e64d955` (2026-10-13) replaced the raw `{error}` prints in stage6.py and pilot_cli.py with `type(error).__name__` or counts; grep of apps/earnings-pipeline/src finds `fail(f"Refused: {error}")` only in events_cli.py and cohort_cli.py, outside the named files.

## 10-harden-the-gold-before-bundle-4 — 2026-10-03

- [x] Take `codebook freeze`'s drafting aid from the kept draft (plan 10, P10-7;
      T8-M1's pattern). apps/earnings-pipeline/src/earnings_pipeline/codebook_cli.py
      reads only data/runs/gold/drafts/codebook.working.toml, and
      packages/earnings-themes/src/earnings_themes/codebook.py:319 copies that
      copy's `drafting_aid`, so an edit there would change the recorded model or
      date (GS5). Codebook v0 is frozen and approved, so only a later version is
      affected. Size: quick-fix. Done when: `codebook freeze` takes the aid from
      codebook.draft.toml, with a test, before codebook v1 is frozen.
      → done 2026-11-13 (/deferred quick fix): `codebook freeze` reads data/runs/gold/drafts/codebook.draft.toml and takes its `drafting_aid`, and refuses a missing kept draft; tests `test_codebook_freeze_takes_its_drafting_aid_from_the_kept_draft` and `test_codebook_freeze_refuses_a_missing_kept_draft`.
- [x] Refuse a kept draft that repeats an ID (plan 10's final review, T2-m1,
      widened; deferred at plan 10's completion gate). In
      packages/earnings-themes/src/earnings_themes/annotation.py, `_Origins.compare`
      (:135) keys the kept draft's items by ID, and `build_curated` (:414) keys its
      fixtures by fixture ID, so a kept draft that repeats a quote, claim, or
      fixture keeps only the last copy, and GS5's `rejected` count misses the
      repeat if the working copy drops it; `CuratedDraft` has no uniqueness
      validator. `gold anchor --check` with no working copy already refuses the
      repeat as `duplicate_id`, so only a draft that skipped that check is
      affected. Size: quick-fix. Done when: build_gold and build_curated refuse a
      kept draft with a repeated ID, with a test, before Stage 11 counts the
      rejected shares. → done in plan 17: `build_gold` and `build_curated` refuse a
      repeated quote, claim, assignment row or fixture as `duplicate_id`, subjects
      prefixed `draft `, collected with every other refusal. The user's gate 3
      (2026-10-11, 3406ba4) ran `pilot recount` over the three signed train files: each
      rebuilds from its kept draft, so none repeats an ID.

## 11-evidence-selection-and-verification-plan-a — 2026-10-04

- [x] Print only a refusal's reason and IDs over pilot text (plan 11's final
      review; GS13; deferred by the user). In
      packages/earnings-core/src/earnings_core/evidence.py, `validate_span`'s
      `quote_text_mismatch`, `locator_mismatch`, and `ambiguous_occurrence`
      details embed text through `!r`, and `reverify_span` passes them through
      unchanged, so a refusal over a pilot document carries pilot text in its
      `detail`. The Stage 7 spec's Records section lets that detail stay in the
      local store, since `data/` is gitignored, so only printing and committing
      are at issue. Size: quick-fix. Done when: plan B's gates and commands print
      or commit only the reason and IDs for a refusal over pilot text, with a
      test. → done in plan 12 (specs/plans/completed/12-evidence-selection-and-verification-plan-b.md): a refusal prints as its reason and IDs, with sentinel tests; Stage 10's first command inherits it

## 12-evidence-selection-and-verification-plan-b — 2026-10-05

- [ ] Share one span-verification path and one set of test helpers (plan 12's
      pre-flight F1 and F7, and its review's M2-4 and M7-6; deferred by the
      user). In packages/earnings-themes/src/earnings_themes/extraction/extract.py,
      `verify` and `masks_over` repeat anchoring.py's `_verify` and
      `_masks_over`, and units.py's `_rank` repeats `narrative_home`'s ordering
      key. The tests repeat the forbidden-import lists
      (tests/contracts/test_import_scan.py and
      packages/earnings-themes/tests/test_import_boundaries.py), the AST walkers,
      and the foreign-mask helpers (test_extraction_run.py's `foreign_mask` and
      test_anchoring.py's `remask`). anchoring.py is Stage 6's frozen module, so
      plan 12 copied rather than refactored. Both copies call core's
      `validate_span`, so a drift could change a reason or an ID but cannot
      weaken exactness. Size: plan. Done when: anchoring's freeze lifts and each
      pair shares one definition, with the suites unchanged.
- [x] Enforce the extraction records' invariants (plan 12's pre-flight F5, its
      review's I3-2 and M3-1 to M3-3, and its final review's m3; deferred by the
      user). In packages/earnings-themes/src/earnings_themes/extraction/records.py:
      `WindowRecord` checks neither `end > start` nor its `window_id`'s format,
      though docs/data-dictionary.md documents `end` as `int > start`; no check
      covers `Claim.claim_id`'s format, `attempts` against `requests`,
      `unreported <= requests`, or `DocumentRecord.windows_failed <= windows`;
      `_reason_when_failed` repeats in `Visit` and `WindowRecord`, and only
      `Visit`'s is tested; and the `min_length=1` on `Claim.quote_ids` and
      `WindowRecord.unit_ids` is untested. New validators shift the test counts,
      so they wait. Size: plan. Done when: the validators land with tests, before
      Stage 10 reads a stored run back.
      → done in Stage 10 plan 15 Tasks 1/3: strict validators and stored-run
      gates, with independent specification/quality approvals and current
      consuming checks (`7820506`, `38bd613`; 199 extraction tests passed).
- [ ] Make the cache and the store safe for concurrent workers (plan 12's
      review's M5-2, M5-3, M8-1, and M8-2; deferred by the user).
      packages/earnings-themes/src/earnings_themes/extraction/adapters.py's
      `AdapterError` does not pickle (`super().__init__(problem.value)`).
      cache.py's `.partial` name is per key, so two writers of one key collide,
      and a stored entry keeps `reply.cached` as given. store.py's
      check-then-rename gives a concurrent writer an `OSError` rather than the
      documented `FileExistsError`, and its run directory's 0700 mode, kept from
      `mkdtemp`, is undocumented. One process runs today, so none bites. Size:
      plan. Done when: Stage 15's orchestration lands its workers with these
      fixed or ruled out.
- [ ] Widen the default tests' socket guard (plan 12's review's M7-1; deferred by
      the user). packages/earnings-themes/tests/conftest.py's `no_network`
      patches six entries, the connections and the forward lookups. A send
      without a connection, a reverse lookup, a name imported from `socket`
      before the patch, and a socket opened in C or another process pass
      unguarded. The guard is opt-in, and its own test exercises 2 of the 6
      entries; its docstring has said so since `76fa5a4`. Size: plan. Revisit
      if: a default test needs isolation beyond the scripted runs, or a library
      under test opens a socket another way.
- [x] Harden the import scans (plan 12's review's M2-1, M9-3, M2-2, and M2-6;
      deferred by the user).
      packages/earnings-themes/tests/test_import_boundaries.py's
      `extraction_imports` and tests/contracts/test_import_scan.py's themes scans
      skip relative imports (`node.level == 0`); `retrieval_imports` reports a
      line without its file; and `themes_network_imports` has no files-scanned
      floor and lists clients by name. No source module uses a relative import
      today. Size: quick-fix. Revisit if: a module under
      packages/earnings-themes/src adopts a relative import.
      → triggered 2026-11-13: Modules under packages/earnings-themes/src now use relative imports: 32 top-level `from .` lines, for example analysis/completion.py lines 13-16 and analysis/store.py line 18. The first came in d338f7c (2026-10-06), so "No source module uses a relative import today" no longer holds. tests/contracts/test_import_scan.py still skips them (`node.level == 0` in `imported` and `local_adapter_imports`). The real boundary risk is low, because a relative import stays inside earnings_themes. The item is still open.
      → done 2026-11-13 (/deferred quick fix): tests/contracts/test_import_scan.py resolves relative imports against the file's package (`imported`, `local_adapter_imports`), `retrieval_imports` returns each hit's file, and the network scan matches dotted names, adds the standard library's network modules, and requires at least 75 files; test_import_boundaries.py's `pipeline_imports` already resolved relative imports.
- [ ] Close plan 12's test gaps (its review's M1-2, M1-3, M2-3, M3-5, M4-2, M4-4,
      M5-4, M6-1, M6-2, M6-5, M7-2 to M7-4, M8-7, M8-8, M9-2, M10-2, and M10-3;
      deferred by the user). Under packages/earnings-themes/tests:
      test_extraction_windows.py's never-split check passes by construction, and
      its label check compares keys only; the reversed-span validator is
      unexercised; the drafting-module guard was never seen red against a real
      drafting module; `ExtractionRejection`'s repr IDs are unpinned; the
      prompt template's two section guards and a repeated heading are untested,
      and a test pins pydantic's error order; no reply-carrying `AdapterError`
      passes through `CachedAdapter`; P12-6's resend is pinned for one problem
      only, and ES20's first refusal is not discriminated; a test pins
      pydantic-core's JSON wording; the cross-document token carry, the mask
      check's `doc_id` half, and a refused bundle through `extract_run` are
      unpinned; no test reads another schema version's row, and two sentinel
      cases do not pin the refused path; the model-mismatch test does not check
      that the refused reply rides on the error; and two injection tests have
      teeth in one case only. Size: plan. Done when: a test-hardening pass closes
      them, or records why one is dropped.
- [ ] Decide whether a run survives an error that is not an `AdapterError` (plan
      12's Task 7 decision and its final review's m2; deferred by the user).
      packages/earnings-themes/src/earnings_themes/extraction/extract.py catches
      only `AdapterError`, and run.py has no handler. So a cached entry that does
      not read (`RecordError` or `ValueError` from cache.py, `UnicodeDecodeError`
      from `read_json`) ends the run with no `RunRecord`, and the spend of the
      earlier attempts goes unrecorded. Run metadata is validated only when the
      `RunRecord` is built, after every dispatch. Failing loud matches the repo's
      repair-by-hand stance, accepted replies stay cached, and `extract_window`
      and `extract_run` say so since `76fa5a4`. A recorded outcome would be a new
      `ExtractionProblem`, a schema change. Size: design. Revisit if: Stage 10 or
      11 needs a partial run record after such an error.
- [ ] Decide whether the wording guard scans Python sources (plan 12's Task 10
      review; deferred by the user). tests/integration/test_stage6_wording.py's
      `STAGE6` globs cover the committed Stage 6 files and `prompts/**/*.md`, but
      no `.py` file, so synthetic.py's injection document and the test strings
      are never checked against pilot text. They are invented, and the Task 10
      reviewer's 40-character check against Stage 1's fixtures found no match.
      Widening the guard to `.py` would sweep in the tests and the guard itself.
      Size: design. Revisit if: a test or synthetic string is ever derived from
      release text.
- [x] Let earnings-themes' tests collect without httpx (plan 12's pre-flight F3;
      deferred by the user). tests/contracts/test_data_dictionary.py and
      packages/earnings-themes/tests/test_extraction_local.py,
      test_extraction_injection.py, and test_extraction_live.py import
      `earnings_themes.extraction.local`, which imports httpx. The default suite
      finds httpx through earnings-ingestion's dependencies, not themes'
      `local-model` extra, so a themes-only environment would fail at
      collection. Size: quick-fix. Done when: those modules `importorskip` httpx,
      or a themes-only run is shown to pass.
      → done 2026-11-13 (/deferred quick fix): test_extraction_local.py and test_extraction_live.py `importorskip` httpx, and the injection test and two tests of coding/test_adapters.py import it inside the test; `test_the_themes_tests_collect_without_httpx` collects packages/earnings-themes/tests with httpx blocked. tests/contracts/test_data_dictionary.py imports earnings-ingestion and earnings-pipeline, which require httpx, so no themes-only run includes it.
- [x] Keep a refused map key out of a field path (plan 12's review's M8-9;
      deferred by the user).
      packages/earnings-themes/src/earnings_themes/records.py's `describe`,
      Stage 6's frozen code, keeps a dictionary key in the field path when that
      key's value is refused, so a corrupted run.json can echo a key of
      `RunRecord.documents`, `rejections_by_reason`, or `software`. Those keys
      are code-written document IDs, reason values, and software names, never
      release text. Size: quick-fix. Revisit if: a `RunRecord` map key can hold
      model or release text, or Stage 6's freeze lifts.
      → triggered 2026-11-13: Plan 12's freeze list (specs/plans/completed/12-evidence-selection-and-verification-plan-b.md, lines 230-231) names packages/earnings-themes/src/earnings_themes/records.py as a frozen Stage 6 module, yet that file changed later in ee68622 (2026-10-12) and a3b12c4 (2026-10-13). This is a reading of "Stage 6's freeze", not a decision that it lifted. The fix is still open: describe in records.py keeps a map key in the path when the key's value is refused (checked 2026-11-13 with a one-key dict).
      → done 2026-11-13 (/deferred quick fix): `describe(error, model)` redacts each path part that names no field in the model's tree, and `parse` passes its model (`parse_reply` does not: `Reply` holds no dict, and its problems are resend feedback inside the extraction cache key); test `test_a_map_key_whose_value_is_refused_stays_out_of_the_path`.
- [ ] Keep the live test's failure output to IDs and counts (plan 12's review's
      M9-4; deferred by the user).
      packages/earnings-themes/tests/test_extraction_live.py's assertions over
      the stored run would print records, Stage 1 text and the model's claims,
      on a failure. It runs only over a Stage 1 fixture, and its one run at the
      gate passed. Size: quick-fix. Revisit if: the live test, or one like it,
      runs over pilot text.
- [ ] Check the block rule against transcripts (plan 12's review's M1-5;
      deferred by the user).
      packages/earnings-themes/src/earnings_themes/extraction/units.py's
      `block_of` returns any non-sentence narrative ancestor, a section, turn, or
      heading included, not only a paragraph, list item, or footnote, and
      windows.py assumes a block's units are contiguous. walker-1's releases
      never interleave blocks, and test_extraction_windows.py would catch it on
      the fixtures. Size: design. Revisit if: transcripts add speaker turns or
      sections as blocks.

## 15-evidence-linked-theme-extraction — 2026-10-08

- [ ] **P15-M1 — Typed workflow phases and helper results.** Both independent
      final technical review seats identified the large public orchestration
      function (about 429 lines) and 15 untyped private helpers in
      `apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py` as
      nonblocking maintenance. Source: completed plan 15, final reviews over
      `7d9b2cb` → `cb1cda8`, and `docs/verification/theme-vertical-slice.md`,
      completion reconciliation. Size: plan. Revisit if: the next authorized
      workflow maintenance change touches orchestration or identity/retry phases.
      Use typed internal phase/result records and smaller helpers while preserving
      public signatures, current consuming gates, lock scope and receipt bindings.
      Deferred because current gates and regression coverage are sound; this is
      not a prerequisite for Stage 11. Done when: those internal handoffs are
      typed, the phase responsibilities are explicit, and the existing invented
      retry/failure/publication/current-input checks pass with unchanged behavior.
- [ ] **P15-M2 — Typed fixture-seeding result and named helpers.** Both independent
      final review seats identified the roughly 380-line `seed_case` in
      `tests/integration/stage10_cases.py`, returning two or three tuple elements,
      as nonblocking test maintenance. Source: completed plan 15, the same final
      review range and `docs/verification/theme-vertical-slice.md`, completion
      reconciliation. Size: plan. Revisit if: the next authorized Stage 10 fixture
      maintenance change extends seeding. Replace the variable tuple with one
      typed result containing optional material and named seeding helpers,
      preserving spans, original links, IDs, behavior and covering assertions.
      Deferred because current tests verify the public behavior; this is not a
      Stage 11 prerequisite. Done when: all callers consume that consistent
      result, each seeding responsibility is named and the existing invented
      integration/coverage/fixture regressions retain their coverage and pass.

## GS19 amendment (Stage 6 spec) — 2026-10-11

- [x] **GS19 — Independent-pass check and dev guard.** The user's independent pass
      on each dev bundle (specs/completed/pilot-codebook-split-and-gold-set-protocol.md,
      §The independent pass) needs two changes in `gold anchor`/`gold show`
      (apps/earnings-pipeline, earnings_themes.annotation). (1) `gold anchor <event>
      --independent --check` anchors and checks
      `data/runs/gold/independent/<file>.toml` in the gold brief's draft form, with
      no `[drafting_aid]` and a non-blank `annotator`, and prints counts and
      refusals by item and reason, writing nothing. (2) For a dev event, `gold
      anchor` (with or without `--check`) and `gold show` refuse a draft or working
      copy unless `evaluation/djia-2024q3-2026q2/pilot-v1/independent-pass.toml`
      holds a row for the event whose `sha256` matches the local record. Train and
      test behavior is unchanged. Tests use invented records only, and the
      implementing session never opens pilot text (GS13). Size: plan.
      Blocks: every dev bundle; pilot order's #2 and #4 are dev. Done when: both
      behaviors are tested, a train bundle anchors byte for byte as before, and the
      three committed gold files re-anchor unchanged. → done in plan 16
      (specs/plans/completed/16-pilot-codebook-split-and-gold-set-protocol.md):
      `gold anchor <event> --independent --check` and the dev guard on `gold anchor` and
      `gold show`; at 4ba5f35 the root suite gave 4294 passed and the three train files
      re-anchored `unchanged`.

## 16-pilot-codebook-split-and-gold-set-protocol — 2026-10-11

- [x] **P16-1 — Root-suite command cannot collect the Stage 10 runner test.** The
      documented `uv run --locked --all-packages pytest packages apps tests -m "not live
      and not browser"` (CLAUDE.md Commands, AGENTS.md:206) aborts at collection with
      `ModuleNotFoundError: No module named 'tools'` from
      tests/contracts/test_stage10_check_runner.py:8. `tools/` has no `__init__.py`,
      pyproject.toml's `[tool.pytest]` uses `--import-mode=importlib` with no `pythonpath`,
      and `uv run pytest` does not put the repo root on `sys.path`; only
      tools/stage10_checks.py (`run_checks`, `PYTHONPATH` at line 212) supplies it, and
      every Stage 10 route goes through that runner. Found by the user's gate 1 for plan 16
      (2026-10-11, 4ba5f35): the same command with `PYTHONPATH="$PWD"` collected 4323 and
      gave 4294 passed, 1 skipped, 28 deselected, 1 warning in 836 s. It predates plan 16,
      which touches none of tools/, pyproject.toml, uv.lock or that test. Deferred because
      the fix changes repo-wide test configuration or the documented gate command and
      deserves its own reviewed change; a background task was flagged for it. Options:
      `pythonpath = ["."]` in `[tool.pytest]` (check tests/test_pytest_configuration.py and
      the fresh-process boundary tests), a path shim in the runner test, or the
      `PYTHONPATH` form in the documented command (AGENTS.md is cited by line: change a line
      in place, never insert). Also replace README's "a successful full-root duration
      remains unknown" with the observed 836 s for the plain command. Size: quick-fix.
      Done when: the documented root command collects and runs without a hand-set
      `PYTHONPATH` (or the documented command carries it) and the user has re-run it. → done
      in 5be419e: `pythonpath = ["."]` in `[tool.pytest]`, pinned by two tests in
      tests/test_pytest_configuration.py (`python -I -m pytest` models the console script).
      The user re-ran the plain documented command with no `PYTHONPATH` on 2026-10-11: 4243
      passed, 9 skipped, 28 deselected in 819 s. Also found: 11 of the 13 test files that
      import root-level names by dotted path (`tests.`, `apps.`, `packages.`, `tools.`)
      could not be collected alone, and the same option fixes them. README's duration
      sentence and CLAUDE.md's `[tool.pytest]` paragraph are updated; AGENTS.md:206 needed
      no change.
- [x] **P16-2 — Stage 11 reuse of the GS19 record check.** (a) `check_independent` in
      packages/earnings-themes/src/earnings_themes/annotation.py skips the
      codebook-approval check that `validate_gold` makes through `_codebook`; harmless while
      codebook v0 is approved, but Stage 11 will reuse the function. (b) `gold anchor
      <event> --independent --check` (apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py,
      `_check_independent`) now refuses once the event has a ledger row, so it cannot serve
      Stage 11's "check each record against its ledger hash, then anchor both"
      (specs/completed/pilot-codebook-split-and-gold-set-protocol.md, §What Stage 11 gets);
      Stage 11 needs its own path built on `load_independent`, `check_independent` and
      `ledger_problem`. Source: plan 16's final review (M2) and its scoped re-review.
      Deferred because it is Stage 11's work. Size: design. Done when: Stage 11's plan
      verifies each record against its ledger hash and anchors both readings, and
      `check_independent` refuses a non-approved codebook, with a test. → done in plan 17:
      `check_independent` refuses an unapproved codebook; `verify_independent` checks the
      ledger and anchors both readings (`IndependentReadings`). The comparison figures and
      the `pilot independent` command (A3, A8) are plan A's remainder.
- [x] **P16-3 — The Stage 6 wording test does not scan the ledger.** The `STAGE6` glob tuple
      in tests/integration/test_stage6_wording.py lists `evaluation/*/pilot-v*/*.json` and
      `evaluation/*/pilot-v*/gold/*.toml` but not `pilot-v*/*.toml`, so
      evaluation/djia-2024q3-2026q2/pilot-v1/independent-pass.toml (plan 16) is never
      scanned for committed text, and TOML comments in it are invisible to both
      `load_ledger` and that test. The strict `LedgerRow` model (three fields, no free text)
      keeps the risk low. Deferred because that test is the user's gate file (plan 16's
      final review, M3). Size: quick-fix. Done when: the globs cover the ledger, or the user
      records that the strict model suffices. → done in plan 17: `STAGE6` gains
      `evaluation/*/pilot-v*/*.toml` and `evaluation/*/pilot-v*/labels/*.toml`, with a test
      that each planned Stage 11 file is found. The user's gate 2 (2026-10-11, 3406ba4):
      7 passed. TOML comments stay unscanned, as for every TOML file that test reads; the
      module docstring says so.
- [x] **P16-4 — GS19 review Minors (quick-fix bundle).** From plan 16's task and final
      reviews, none blocking: (1) `ledger_problem` in
      packages/earnings-themes/src/earnings_themes/independent.py tests
      `ledger.rows if ledger else ()`, a truthiness test on a model; `ledger is not None`
      says what it means. (2) apps/earnings-pipeline/tests/test_stage6_cli.py has no test for
      a malformed independent record through `--independent --check` (the `RecordError`
      path), nor for D16-2 refusing on a working copy, anchored file or view (only the draft
      is tested). (3) The `anchor` command's docstring in gold_cli.py does not mention
      `--independent`. (4) The `show` guard is tested only with nothing anchored; add a case
      with an anchored dev record whose independent record no longer matches the ledger.
      (5) `_guard`'s docstring should say it reads the ledger on disk, not the committed
      ledger (committing the row first is procedure, GS19). (6) "--independent takes events,
      not --hard-negatives" also prints when no event is named; the plan pinned the text and
      its test, so changing it edits a pinned expectation. Size: quick-fix. Done when: each is
      fixed or consciously dropped, with the CLI tests passing. (1) fixed in plan 17:
      `ledger_check` tests `ledger is not None`; items (2)–(6) remain.
      → done 2026-11-13 (/deferred quick fix): (2) tests for a malformed independent record and for a working copy, anchored file or view closing the pass; (3) and (5) docstrings; (4) a `gold show` test after the ledger row changes; (6) `--independent --check` with no event now asks for the dev bundles, and the pinned `--hard-negatives` text is unchanged.
- [ ] **P16-5 — Multi-event `gold anchor` and `gold show` write before a later refusal.** The
      guard, like `_open` before it, runs per event inside the loop in
      apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py, so `gold anchor E_train
      E_dev` writes E_train's files before refusing E_dev (the refused event itself writes
      nothing). A pattern that predates GS19, noted by plan 16's task and final reviews.
      Size: design. Revisit if: a multi-event run leaves a partial state that confuses a
      gate, or a drafting-session workflow starts passing several events at once.

## 17-feasibility-pilot-and-threshold-calibration-plan-a-slice-1 — 2026-10-11

- [x] **P17-1 — `pilot recount` copies `gold validate`'s file selection, stem check and
      kept-draft paths.** → done in plan 20 In apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py,
      `recount_command` (named events, then "is not committed", then the gold glob),
      `_recount` (load the file, check its stem), the kept-draft and working-copy paths,
      and the `Events` alias repeat apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py
      (`gold validate`, `_validate_event`, and the draft paths near `_open`) closely, not
      verbatim. Plan 17's Task 4 brief mandated the shape; its task review logged it as
      Minor. If the committed-gold path rules change, the two copies drift. Source: plan
      17's Task 4 review and final review. Deferred because a clean fix moves shared
      helpers (`committed_gold(layout, pinned, event_ids)`, `kept_drafts(layout, event_id)`)
      into apps/earnings-pipeline/src/earnings_pipeline/stage6.py, the same move the plan's
      Handoffs already schedule for `_independent_path` and `_read_ledger` when A8's
      `pilot independent` arrives. Size: quick-fix. Done when: `stage6.py` holds the shared
      helpers, `gold_cli.py` and `pilot_cli.py` use them, and the Stage 6 CLI tests pass
      unchanged. Do it with A8.
- [x] **P17-2 — Test-coverage gaps in plan 17's commands (batch).** → done in plan 20 (1) `pilot recount`
      (apps/earnings-pipeline/tests/test_stage6_cli.py): no test for the stem-mismatch
      refusal, a missing working copy (only a missing kept draft is tested), an unreadable
      draft or committed file (`record_error`), or that a refusal writes nothing (the
      success path has the byte snapshot); `test_recount_reports_counts_that_do_not_rebuild_by_event_and_field`
      does not assert `exit_code == 1` for its repeated case. (2) The known-answer test in
      packages/earnings-themes/tests/test_gold.py pins `edited: 1`, not which item's
      `origin` is `drafted_edited`. (3) `pilot coverage --version 2`: the `RecordError`
      path in `_no_theme` (a committed gold file that does not parse) is untested.
      (4) `build_gold`'s return on `_items` anchor refusals carrying the kept draft's
      repeats is untested. (5) `CoverageReport`
      (packages/earnings-ingestion/tests/test_events_coverage.py): no test feeds a
      hand-built dev-before-train `no_theme` tuple to the validator, so its "misordered"
      half is unexercised (`build_coverage` sorts first). Source: plan 17's task reviews
      and final review. Size: plan. Done when: each is covered or consciously dropped; A8's
      sentinel tests (the spec asks for one per command) may close (1) and (3).
- [x] **P17-3 — `build_curated` returns early on a repeat, skipping `validate_curated`.**
      In packages/earnings-themes/src/earnings_themes/annotation.py, `build_curated`
      returns `repeats + refusals` before it builds the record, so a kept curated draft
      that repeats an ID and also fails another curated check takes two runs to show both,
      against D17-2's "collected with every other refusal" (`build_gold` does collect).
      Plan 17's Task 1 brief mandated the early return, and the set's drafts are already
      committed. The record builds fine when only the kept draft repeats, so the fix is to
      build it and return `repeats + validate_curated(...)`. Size: quick-fix. Done when:
      both reasons print in one run, with a test.
      → done 2026-11-13 (/deferred quick fix): `build_curated` returns early only for item refusals, and otherwise returns `repeats + validate_curated(...)`; test `test_a_kept_curated_repeat_is_refused_with_every_curated_check`.
- [x] **P17-4 — Plan 17 review Minors (quick-fix bundle).** None blocking: (1)
      `pilot_cli.py`'s `coverage_command` passes `run_ids or ()` to `_no_theme`, so if the
      `version == 2` guard were removed it would count nothing instead of failing; narrow
      the type properly instead. (2) When some train or dev bundles have no gold, `pilot
      coverage --version 2` stops at `fail` before `refuse`, so a problem with existing
      gold shows only on the next run (D17-7 requires only the missing list). (3)
      `transitions(layout)` is read twice in version 2. (4) `annotation.py`: `_duplicates`
      branches on `isinstance(i, tuple)` to render an assignment row; `check_independent`'s
      inline codebook-status test repeats `_codebook`'s (a shared `_approved(codebook)`
      would stop them drifting); `ledger_check` rebinds `rows` from a tuple to a list;
      `_PHRASES` in independent.py has no completeness guard (the parametrized
      `ledger_problem` test covers all five today). (5) packages/earnings-themes/src/earnings_themes/codebook.py
      (~:193) has the same sort-the-repeats pattern for theme IDs. (6)
      packages/earnings-themes/tests/test_import_boundaries.py: the closure test's
      docstring still names an indirect import "through `records` or `tomlfile`", and no
      probe pins the crash a plant in `tomlfile.py` now causes (a circular import). (7) The
      new wording test's name reads "stage_11_s". Source: plan 17's task and final reviews.
      Size: quick-fix. Done when: each is fixed or consciously dropped, with the scoped
      tests passing. Revisit if: one of those functions is touched again.
      → done 2026-11-13 (/deferred quick fix): (1) and (3) coverage v2 reads the transitions once and refuses a missing v1 in its own branch; (2) bad committed gold is named beside the missing list, with a test; (4) `_approved` is shared and `ledger_check` binds `rows` once; (5) `duplicates` moved to problems.py for annotation.py and codebook.py; (6) the closure docstring is corrected and a tomlfile plant is pinned as a circular import; (7) the wording test is renamed. Consciously dropped, as the item allows: (4)'s `isinstance` branch, because a `claim/theme` string rendered by the caller sorts differently for IDs that hold `-` or `.`; and a `_PHRASES` guard, because the parametrized `ledger_problem` test reaches all five returns.
- [x] **P17-5 — Decisions for plan A's remainder (A3, A8).** → done in plan 20 (1) `pilot recount` runs over
      committed gold and refuses no partition, and `pilot coverage --version 2` reads
      train and dev by construction; the spec's sentence after A8's table says "Every
      command refuses test and excluded events…". Settle whether it covers this slice's
      `pilot` commands, alongside the sentinel tests the plan's Handoffs extend to
      `recount` and `coverage --version 2`. (2) `anchor_reading` checks the kept draft only
      for anchoring and repeats, never with `_ids` (dangling quote references, unknown
      themes, a `no_theme` mismatch); A3's figures decide whether to validate it or
      tolerate dangling references. (3) `verify_independent` raises `RecordError` for an
      unreadable record instead of returning a refusal; `pilot independent` must catch it.
      (4) `check_countable` (packages/earnings-themes/src/earnings_themes/annotation.py)
      could compare `gold.doc_id` with the parsed `doc_id` that `_no_theme` already holds,
      at no cost and still without reading a document; `gold validate` covers it today,
      and the user's gate 3 shows the three signed files valid. Source: plan 17's final
      review. Size: plan. Done when: the plan that implements A8 records a decision on
      each, with tests for those it adopts.

## 18-feasibility-pilot-and-threshold-calibration-plan-a-slice-2 — 2026-10-12

- [x] **P18-1 — Say which hashes now cover a support run's cache mode.** Plan 18 added
      `cache_mode` and `stability_run_id` to `SupportRunRecord`, so every digest of that
      record's dump now covers both fields:
      - `support_run_hash` and `_support_content_hash`
        (packages/earnings-themes/src/earnings_themes/coding/decide.py:96 and :101);
      - their consumers: decide.py:339-340, coding/assignments.py:106, coding/store.py:758,
        and analysis/consume.py:375 and :385;
      - the `run.json` byte hash
        (apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py:1027).
      The code is right, but no sentence in docs/data-dictionary.md says this. Deferred at
      plan 18's resolve-before-defer gate (the user's ruling, 2026-10-12): it is a
      doc-precision note, not a defect. Source: plan 18's Task 4 review. Size: quick-fix.
      Done when: docs/data-dictionary.md's support-record section names the digests that
      cover the two fields, with tests/contracts/test_data_dictionary.py passing.
      → done 2026-11-13 (/deferred quick fix): the support records section's "Fresh mode" paragraph names `support_run_hash`, `_support_content_hash`, the comparisons that read them, and the support stage's `run.json` byte hash.
- [x] **P18-2 — The scorer file's pinned-field list is not exhaustive.**
      - Where the list appears: the "Stage 11 live runtime" section of
        docs/data-dictionary.md, and the module docstring of
        apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py.
      - What it names: the pinned fields whose mismatch makes a scorer file
        `malformed_record`, namely the revision, runtime versions, encoding version and
        label mapping.
      - What it omits: `LocalScorerConfig._pinned`
        (packages/earnings-themes/src/earnings_themes/support/nli.py:48-69) also refuses a
        missing or repeated file name, and a MiniCheck `input_limit` above 512.
      Deferred at plan 18's resolve-before-defer gate (the user's ruling, 2026-10-12) as a
      doc-precision note. Source: plan 18's fix-wave re-review. Size: quick-fix. Done
      when: both places name every condition `_pinned` refuses, or say the list is by
      example.
      → done 2026-11-13 (/deferred quick fix): both places name every condition `_pinned` refuses: a relative local directory, the four pinned fields, a MiniCheck `input_limit` above 512, a repeated file name, and a missing required file.

## 19-feasibility-pilot-and-threshold-calibration-plan-a-slice-3 — 2026-10-13

- [x] **P19-1 — Tidy `earnings_themes.evaluation`'s API before slice 4 consumes it.** → done in plan 20
      None is a defect today; each is a contract roughness the per-task and final
      reviews logged and the user deferred at plan 19's resolve-before-defer gate
      (2026-10-13). Files are under packages/earnings-themes/src/earnings_themes/:
      - `evaluation/problems.py`: `EvaluationProblem.UNKNOWN_METRIC` is never raised.
      - Three ways to refuse a hash mismatch (`records.checked`, the calibration
        artifact's own check in `evaluation/calibration.py`, and `CalibratedPolicy`'s
        `content_hash_mismatch`), and two public `checked` helpers: the one in
        `records.py` and a re-implementation in `calibration.py` with a different error
        type. `sealed` and `checked` bound `BaseModel`, which does not guarantee a
        `content_hash` field.
      - `evaluation/preregistration.py`: `Candidate.signals` is `PositiveInt` though the
        menu is single-signal.
      - `evaluation/gates.py`: `derive_gates` takes any `Sequence[Metric]` for `gated`
        instead of a `GateRule`; `WRONG_PARTITION` names the expected partition in
        `derive_gates` and the given one elsewhere.
      - `evaluation/records.py`: `PilotReport.partitions` has no unique, train-and-dev
        validator.
      - `evaluation/report.py`: the GS5 figures carry no counts; the qualifier
        vocabulary (`minicheck`, `deberta`) differs from `MetricReport.view`
        (`minicheck_joint`, `deberta_joint`); `stability_figures` names no run in its
        run-set refusal and does not reject duplicate event IDs within a run.
      - `evaluation/scores.py` and `cells.py`: `hard_negative_counts` drops a hard
        negative's dangling quote IDs silently (D19-7, P17-5(2)); the quote-to-span map
        is built in both modules.
      - Four parent-chain walks (`codebook._structure`,
        `support/resolve.check_theme_graph`, `analysis/prevalence._views`,
        `evaluation/cells.level_one`): one shared helper in `codebook.py` (D18-1).
      - `evaluation/labels.py`, `sampling.py` and `label_view.py`: `merge_labels` uses
        `model_copy`, which skips `_one_label_per_target` (unreachable with real IDs; it
        fails on reload); `sample_targets` accepts `size < 0` and `cap = 0`;
        `label_view._quote` raises a bare `StopIteration` on an unknown evidence
        document (unreachable after `reverify_support_run`).
      - `tomlfile.py` (beside `evaluation/`, not in it): the non-finite-float
        `ValueError` names no key.
      - `evaluation/calibration.py`: the private `_Trial` lacks
        `AssignmentPolicy.reference`; `evaluation/policy.py` tests `selection is None`
        where `artifact.outcome` would say the same.
      - `support/metrics.py`: a positive label with no decision counts as not accepted,
        but no `MetricReport` counter shows how many.
      - The package's `__init__` exports omit `joint_score`, `sealed`, `claim_label`,
        `joint_label`, `Figure`, `ReadingAgreement`, `IndependentFigures`,
        `EvidenceTally` and `configuration_hash` (plan 19's Handoffs H13).
      Source: plan 19's task reviews and final review. Size: plan. Done when: the plan
      that implements A8 has adopted or rejected each, with tests for those it changes.
- [ ] **P19-2 — Close the evaluation package's thin-test and coverage gaps.**
      Test-only; deferred at plan 19's gate (2026-10-13). Files are under
      packages/earnings-themes/tests/evaluation/ unless noted:
      - `cases.py` builds the same `RuntimeIdentity` literal in `trial` and
        `decision_view`; `EvaluationError` has no direct test; the module docstring of
        tests/contracts/test_data_dictionary.py does not mention the evaluation section.
      - `test_cells.py`/`test_scores.py`: no direct test of `EventCells.scored` or the
        `theme_map` roll-up path; thin edge cases (a negative with `theme_id` `None`, a
        negative with a dangling quote, `evidence_recall_counts` with no gold,
        `macro_f1` dropping an undefined F1).
      - `test_report.py`: untested branches (`PartitionReport` sorted and unique events,
        `trial_verdict` with an answer of `None`, `consensus` with `len(own) != 2`); the
        D19-10 unlabelled-event filter; no figure crosses `max_undefined_share`;
        `GS5` test sets `DraftCounts` through `model_copy`; `Gate`, `Ungated`, `Gates`,
        `GateResult`, `GateVerdict`, `ReadingAgreement` and `IndependentFigures` are
        covered only by the dictionary registry test.
      - `test_gates.py`: the `not_in_report` and `undefined_point` branches, the
        `below_bound` reason, a round trip of `[[ungated]]`, and the positivity rule as
        the sole failure. Lower-bound gates can be vacuous (both F1 gates have lower
        bound 0.0 in the fixture), so R12.8 holds only through the positivity row and
        support precision; the pilot's real bounds decide whether that matters.
      - `test_sampling.py`: uneven lane depth, fewer than the cap, a single theme or
        event; the prefix test uses one size pair; the signature test pins names only.
      - `test_label_view.py`: a quote at a block start renders two spaces, `Exclude when:`
        has no blank line after its list, a target with no evidence renders silently, and
        the refused-outcome test reuses `events` from the loop.
      - packages/earnings-themes/tests/coding/test_decide.py: the `decision_inputs` refusal mapping
        (`SupportError` to `CodingError`) is untested, and the decide test compares the
        decided status, not the view contents, so D19-5 is pinned indirectly.
      - `test_preregistration.py`: the `match=` patterns do not pin the slot of a
        refusal; two tests share a setup; the secondary pydantic error text; a duplicate
        id with an unsorted grid reports only the grid error.
      - `test_calibration.py`: the identity test's docstring says it varies every
        run-identity field but never varies the extraction record's `cache_mode` and
        `stability_run_id`; its records come from `model_copy`, which does not validate.
      - Names that claim more than they pin: `test_the_hash_is_stable_across_json_key_order`
        (`PilotReport` has no dict field) and a `test_bootstrap.py` docstring that says
        the oracle is recomputed from `random.Random(8)` alone.
      Source: plan 19's task reviews. Size: plan. Done when: the tests land, or each is
      judged redundant against what the plan that implements A8 adds.
- [ ] **P19-3 — Decide whether tie-group evidence needs a maximum matching.**
      `scores.unit_tally` and `char_counts` score evidence by accepted `(theme, item)`
      pairs against gold `(cell, item)` pairs, where a tie group is one either-of cell
      (FP20). Redundant correct alternatives, whether excused or scored, each count as a
      hit, so the gated `span_unit_f1` can rise when a run asserts an extra correct
      alternative; and which member is excused follows D19-6's lowest-ID rule, so a
      wrong item carried by an excused member is not a false positive while the same item
      carried by the chosen member is. Plan 19 tried a per-cell 'one credit per slot' rule
      and reverted it: it depended on theme IDs and could lower a score when a correct
      item was added (commits `c7aa473` and `90a7f33`). The stricter alternative is a
      maximum matching of accepted pairs to gold `(cell, item)` pairs, scored themes
      first, per atomic segment for characters, with unmatched in-slot pairs neutral; it
      has trade-offs of its own (it can give up monotonicity if excused in-cell pairs stay
      accepted). The effect is documented in docs/data-dictionary.md under `EvidenceCell`
      and in plan 19's Handoffs (H16). Source: plan 19's final review. Size: design.
      Revisit if: the pilot's signed gold contains tie groups with overlapping evidence,
      or a dev gate's `span_unit_f1` bound turns on them.
      → triggered 2026-11-13: The pilot's signed gold holds 33 tie_group rows in 9 of its 28 files (counts only, from evaluation/djia-2024q3-2026q2/pilot-v1/gold/ and the partitions in split-v1.json): 31 rows in 8 train files and 2 rows in 1 dev file. Rows that share a tie_group are alternative themes for one claim, so they share that claim's quotes. Reading that as "overlapping evidence" is a reading. The second half of the signal, a dev gate's span_unit_f1 bound, is untested because no dev gate has run. No gold file was opened beyond these counts.
- [ ] **P19-4 — `SUPPORT_PRECISION` and `SCORER_AUC` resample every event that holds any
      labelled target.** `evaluation/report.py` (`_label_figures`) puts each event with
      at least one `LabelledTarget` into the bootstrap population, including an event
      with no usable label of the relevant kind (no accepted target for precision, no
      positive or negative for AUC). D19-10 says 'the events that hold labels', which
      the code meets, so plan 19's final reviewer ruled it as is; the judge-agreement
      figures were changed to use joint-labelled events only. Restricting the others
      would move a gated dev lower bound (the existing pin
      `test_support_precision_interval_skips_draws_without_an_accepted_label` shows an
      event with a joint label and no accepted target giving 12 undefined resamples).
      Source: plan 19's final review. Size: quick-fix. Revisit if: a dev gate's
      `SUPPORT_PRECISION` lower bound depends on events without a usable label.

## 21-feasibility-pilot-and-threshold-calibration-plan-b — 2026-11-11

- [ ] **P21-1 — Stop the support cache from growing with the square of the run size.**
      `_key` in packages/earnings-themes/src/earnings_themes/support/cache.py puts
      the whole source run into each key's material. The material holds every bundle
      (document, elements and masks), every stored claim and every stored quote.
      `put` writes that material into each entry, and `_entry` reads it back and
      compares it on each lookup. Thus each entry gets larger as the run holds more
      documents, and the number of entries also grows with the run. The extraction
      and coding caches do not embed bundles. After the B3 train pass (20 events),
      the support cache held 7,792 entries of about 13.7 MB each, about 107 GB
      (`docs/verification/pilot-v1-feasibility.md`, "Step 2: the train pass").
      The figures that follow are linear estimates from that pass, not measurements.
      One run over Stage 15's 239 eligible events would write about 93,000 entries
      of about 164 MB, about 15 TB. Twelve runs of 20 events would write about
      1.3 TB. The main checkout's disk had 460 GiB free on 2026-11-11. D21-30 left
      this cost as a later item and did not measure it. It also left two related
      costs: the repeated source resolution in each reverification, and the artifact
      hash that reads each entry again. R14.6 names the canonical hash as a key
      component, not the canonical text, and the material already holds
      `provenance_hash`. Whether a hash can replace the embedded run is a design
      decision. That decision also covers `SUPPORT_VERSION` and the cache layout.
      Do not change the key before Stage 11 completes. A new key misses every cached
      train entry, and Task 6 replays the frozen train baseline (D21-29) from those
      entries. A new key also stops Stage 15 from reusing the pilot's support
      entries, which the roadmap's Stage 15 Consumes line expects where the key
      still matches. Source: the B3 train pass and a session question on Stage 11–16
      run time (2026-11-11). Size: design. Revisit if: Stage 15's plan is written,
      or a run with more than the pilot's 40 events is planned. Done when: Stage
      15's plan has decided the key's form, and a test shows that an entry's size
      does not depend on the number of documents in the run. Otherwise, the plan
      records why it splits the run instead, with the measured disk need.

## 23-run-path-performance — 2026-11-13
- [ ] Decide whether `write_theme_report`'s two read-backs may share one scope (plan 23,
      option J, final review). Plan 23 reached 12 raw-cache sweeps over one pilot run, not
      the planned 8 (D23-9). Merging the two read-backs in `write_theme_report` into one
      scope would remove 4 sweeps. The controller refused it, because it turns two
      spec-named read-back gates into memo hits. After plan 24 one sweep over 4,866 judge
      entries costs about 4.3 min (3,076 s for 12 sweeps), so removing 4 saves about 0.3 h
      of the 7.19 h projection
      (`docs/verification/pilot-v1-feasibility.md`, "Plans 23 and 24 run-path
      performance"). See `specs/plans/completed/23-run-path-performance.md` (D23-9) and
      `packages/earnings-themes/src/earnings_themes/analysis/consume.py`. Size: design.
      Done when: the owner rules whether those two read-back gates may share one scope,
      and either the exact-count test in `apps/earnings-pipeline/tests/test_pilot_gate_counts.py`
      shows 8 sweeps or the plan records that 12 stays.
- [x] Harden decide's memo against a policy that plants values under its private kind
      string (plan 23, ruling N1, final review). A policy that calls
      `scope.once("proposal_inputs", ...)` with decide's private kind string can change and
      restore the memo's dict, so a missing-assessment row gets a wrong `target_id` with no
      refusal. The ruling put this outside the threat model: it needs a policy that knows
      the private string and calls the scope module directly. The cheap fix: snapshot each
      missing key's `target_id` string at the start of `decide_assignments`
      (`packages/earnings-themes/src/earnings_themes/coding/decide.py`) and read the
      snapshot at the row. Size: quick-fix. Done when: a test with such a policy shows the
      row's `target_id` equals the value at the start of the call.
      → done 2026-11-13 (/deferred quick fix): `decide_assignments` copies each missing key's `target_id` before any policy code runs, and the row reads the copy; test `test_a_policy_cannot_redirect_a_missing_rows_target_id` plants and restores the memo and sees the original ID.

## 24-cheaper-key-check — 2026-11-13
- [ ] Cut the proposal replay cost (plan 24, D24-2, final review). Proposal replay is the
      largest term left in the train `pilot run` projection: 3.55 h of 7.19 h, with about
      800 `resolve_target` calls per claim (18 `reverify_coding_input` calls x 22 themes),
      5.46 s per claim at real key size. The owner kept it out of plan 24 and chose to
      stop at the key check. The margin under the 8 h goal is about 0.7 h, and the figure
      is a floor on invented text. Source: `docs/verification/pilot-v1-feasibility.md`,
      "Plans 23 and 24 run-path performance". Size: plan. Revisit if: the first real B6
      train `pilot run` takes more than 7 h, or Stage 15's plan needs a run of more than
      40 events (about 239 eligible events). Done when: a plan memoizes or batches
      those calls, `resolve_target`'s counts per claim are pinned by a test, and a new
      projection shows the proposal replay term lower, with every record and hash
      unchanged.

## 25-recover-unusable-saved-responses — 2026-11-13
- [ ] Let `cohort fetch-sec` refetch an unusable saved N-PORT document (plan 25's
      scope check): `fetch_sec` in `cohort/acquire.py` decides a filing is kept
      with `store.latest`, which raises when the newest artifact is gone or
      changed. `cohort fetch-sec` then stops with `Stopped: no artifact …` and no
      remedy. Plan 25's quarantine already covers its writes. Cohort v1 is frozen
      and Stage 15 consumes it unchanged, so nobody rebuilds the cohort store
      until a new cohort version. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/` and
      `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`. Size: quick-fix.
      Revisit if: `cohort fetch-sec` stops on a saved N-PORT document that is gone
      or changed.
- [ ] Name a damaged retrieval record instead of stopping every reader (plan 25's
      scope check): `SavedResponses.__init__` (`events/saved.py`) and
      `ArtifactStore.retrievals` and `latest` (`fetch/store.py`) read
      each record with `Retrieval.model_validate_json` and no handler, so a
      truncated record raises a validation error out of every command, with no
      file named. A record's name carries the first 12 hex digits of its bytes'
      SHA-256, so damage is detectable, but the URL inside an unreadable record is
      unknown, so a refetch cannot be named for it. `run_refetch` (`events/recover.py`)
      also reads `read_back` outside its own guard, so a stop there after a save
      prints no `quarantined:` or `changed:` line. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Plan 25's sync makes new
      damage unlikely, and the manual repair in `docs/verification/djia-events.md`
      still covers old damage. Size: design. Revisit if: any `events` or `cohort`
      command stops with a validation error on a file under `retrievals/`.
- [ ] Let `events discover --refetch` reach the primary document of a filing that
      `release-id/1` passes over (plan 25's final review): `read_back`
      (`events/discover.py`) lists the unusable responses of each issuer's listings,
      each listed filing's index page, each candidate's primary document, and
      companyfacts. `identify` (`events/release.py`) reads a primary document only
      for an in-range 8-K whose index page lists Item 2.02 and an EX-99* exhibit.
      A `set_release_filing` override can name an 8-K/A, or an 8-K without them, and
      cites its primary document. If that file is damaged, `citations_refused`
      (`events/build.py`) prints a problem that names `events discover --refetch`,
      and `plan_refetch` (`events/recover.py`) refuses the URL and points to the
      manual route in `docs/verification/djia-events.md`, "Repairing the store", (c).
      Three smaller cases share that refusal or its wording. An index page listed
      only on an out-of-range older page gets the same refusal, and neither
      `discover` nor `discover --filing` saves it. `acquire --refetch`'s refusal
      (`events/acquire.py`, `_refusal`) says that an index page or a primary document
      is refetched by `discover --refetch`, which is too broad for a passed-over
      primary document. A cited exhibit's `cited_remedy` names `discover --refetch`,
      which then points to `acquire --refetch`, and a build that cannot read the
      exhibit cannot run `acquire`, though no committed override or evidence record
      cites an exhibit today. Size: plan. Done when: a test truncates a primary
      document that a `set_release_filing` override cites for an 8-K/A, sees
      `discover --refetch` accept and repair it, and rebuilds the frozen content
      hash, and each `refetch_remedy` and `cited_remedy` line names a command that
      accepts its URL.
- [ ] Print a `quarantined:` line when a plain save moves damaged bytes aside (plan
      25's final review, declined): `events discover`, `events discover --filing`
      and `cohort fetch-sec` save through `ArtifactStore.put`, which quarantines a
      damaged artifact when a save needs its name. Only `discover --refetch` and
      `acquire --refetch` print the moved paths, so after a plain save the damaged
      bytes sit under `<root>/<source_id>/quarantine/` with no report. The bytes are
      kept, and nothing valid is moved. Paths are under
      `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py` and
      `cohort_cli.py`. Size: quick-fix. Done when: each of the three commands prints
      one `quarantined:` line for each distinct path in `store.quarantined`, under a
      test that damages an artifact and saves its URL again.
      → planned 2026-11-13: specs/plans/26-harden-ingestion-error-reporting-and-refusals.md
