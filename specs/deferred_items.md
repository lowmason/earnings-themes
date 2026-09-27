# Deferred items

## browser-rendering-integration — 2026-09-24

- [x] When Stage 1 is ticked complete in
      `specs/evidence-linked-theme-extraction-roadmap.md`, surface the approved
      `specs/browser-rendering-integration.md` design before Stage 2 planning.
      Stage 2 plans only the browser-neutral core contracts and tests; Stage 3
      owns Selenium capture, rendered-text calibration, DOM/layout extraction,
      and the diagnostic-first promotion decision; Stage 10 consumes the public
      renderer and canonical-span artifacts for cited evidence views. Do not add
      browser automation to Stage 1 or make it a dependency of `earnings-core`
      or `earnings-themes`. Size: cross-stage planning reminder. Done when the
      Stage 2 plan incorporates its assigned contract work and leaves explicit
      handoffs for the Stage 3 brainstorming pass and Stage 10 plan. → done in plan 3 (specs/plans/completed/3-core-evidence-spine.md)

## 2-point-in-time-djia-cohort — 2026-09-22
- [x] Renumber the two Stage 1 documents for the cohort amendment (plan 2 Task 7,
      skipped): `specs/release-parser-fidelity.md` still calls acquisition Stage 4
      and the codebook-and-split stage Stage 5 (lines 121, 164, 474, and the
      Handoffs table's bare `| 4 |` / `| 5 |` rows at 614-615), and
      `specs/plans/1-release-parser-fidelity.md` cites Stage 4 three times plus a
      lowercase `stage 4` column header at line 2988, which also appears in
      `expirements/parser-fidelity/discover.py:468`. Deferred because Stage 1
      execution is live on `stage-1-release-parser-fidelity` and edits plan 1 in
      the main checkout. The forward constraint at
      `specs/release-parser-fidelity.md:164-166` needs a change of meaning, not
      just a number: under P-C7 a selected event stays selected, so "leave them out
      of the pilot" is no longer available, and Stage 6 must instead place any
      fixture event the deterministic selection includes in the training
      partition (moot today: no fixture issuer is a DJIA member). The steps are in
      specs/plans/completed/2-point-in-time-djia-cohort.md, Task 7. Stage 1 keeps
      writing text in the old numbering (its decision record, V2 notes, and plan
      1's handoff sections), so the line numbers above will drift: re-derive them
      then, and run a case-insensitive `stage [45]` / `stage4` sweep over
      everything Stage 1 added after `6021323`. Size:
      quick-fix. Done when: Stage 1 execution is paused or its plan is retired,
      both documents are clean in git status, and the renumbering, including the
      reworded forward constraint, has landed. → done in plan 1 (`d3df93c`)
- [x] Rename the `stage4_flags` manifest field to `acquisition_flags` (plan 2
      Task 7 Steps 3 and 5, skipped): the field has reached code, in
      `expirements/parser-fidelity/promote_fixtures.py:157`,
      `expirements/parser-fidelity/test_promote_fixtures.py:106-110`
      (`test_stage4_flags`), and eight entries of
      `tests/fixtures/releases/manifest.toml`, as well as both Stage 1 documents,
      so it must change in documents and code together, which a live Stage 1 run
      cannot absorb. Size: quick-fix. Done when: Stage 1 execution is complete and
      the field is renamed in documents, code, test, and manifest in one change,
      or the user records a decision to keep `stage4_flags`. → done in plan 1 (`d3df93c`)
- [x] README Stage 1 status is stale on this base (plan 2 whole-plan review,
      Minor): `README.md:140-141` says the investigation harness and fixture
      corpus "have not been created yet", but `expirements/parser-fidelity/` and
      `tests/fixtures/releases/` exist since the Stage 1 commits. Outside plan 2's
      scope, and the paragraph is the user's. Size: quick-fix. Done when: the
      README's Stage 1 paragraph describes the harness and fixture corpus as they
      stand, at the latest when Stage 1 completes. → done in plan 1

## 1-release-parser-fidelity — 2026-09-25
- [x] Carry V2's findings into Stage 3: V2's "Residual failures (for Stage 3)"
      and "Findings for Stage 3" (`docs/verification/V2-parser-fidelity.md`) and
      ADR 0001's Consequences list what the walker leaves to the canonicalizer:
      split, merged and header-lost blocks by fixture, body text typed as
      headings (12 of 313 found body blocks), the eight Known gaps in
      `expirements/parser-fidelity/walker-rules.md`, W11's and W15's side
      effects, page numbers kept as `other`, and a script header that lists
      beautifulsoup4, which the walker never imports. The roadmap's Stage 3 entry
      consumes only "Stage 1 parser decision and fixtures", so these could be
      missed. Size: plan. Done when: the Stage 3 spec or plan compensates for or
      records each of V2's findings for Stage 3. → done in plan 4
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

## 3-core-evidence-spine — 2026-09-25
- [ ] Accept a stored `VerifiedSpan` in `validate_span` (final review, Important
      #2; the user chose a handoff note and deferred this): `VerifiedSpan` in
      `packages/earnings-core/src/earnings_core/evidence.py` validates only
      `start < end`, so a `model_copy(update=...)` or a JSON round trip can
      carry any `quote_text`. `validate_span` is typed to take a
      `SpanCandidate`, yet at runtime it already rejects a tampered copy with
      `quote_text_mismatch`, because both records share `_EvidenceFields`. Plan
      3's roadmap reconcile tells Stages 7 and 10 to re-run `validate_span` on
      stored spans at every R6.1 gate, and Stage 7 owns the verification stage
      (D-20). Fix: type the parameter to accept either record, or add a named
      re-verification helper, with a test that a round-tripped `VerifiedSpan`
      re-verifies and a tampered copy is rejected. Size: quick-fix. Done when:
      that API and its test land, at the latest when Stage 7 first stores
      `VerifiedSpan`s.
- [x] Report every crossing in `validate_elements` (final review, Minor;
      deferred by the user): `_crossings` in
      `packages/earnings-core/src/earnings_core/structure.py` never pushes an
      element it has reported, so a later crossing against that element goes
      unreported. With A=[0,10), B=[5,15) and C=[12,20), B is reported against A
      but not against C. The set is still refused, but D-8 promises every
      structural problem at once. Size: quick-fix. Done when: that case reports
      both crossings, with a test. → done in plan 4
- [ ] Prefer the genuine element in `resolve_pointer` (final review, Minor;
      deferred by the user): `resolve_pointer` in
      `packages/earnings-core/src/earnings_core/structure.py` returns
      `wrong_document` for the first element whose ID matches, while
      `validate_span`'s `_element` skips elements of another version. Under D-1
      an unchanged region keeps its `element_id` across versions, so for a
      mixed-version element list the outcome depends on list order. Size:
      quick-fix. Done when: `resolve_pointer` resolves the genuine element
      wherever it sits in the list, with a test that lists the stale element
      first.
- [x] Recheck construction-only invariants in `validate_elements` (final review,
      Minor; deferred by the user): `validate_elements` in
      `packages/earnings-core/src/earnings_core/structure.py` recomputes hashes
      and derived IDs (D-7) but not a level on a non-leveled type, table-cell
      context present exactly on `table_cell` elements, or self-parenting, so a
      `model_copy`'d cell stripped of its context passes. The `ContractModel`
      docstring in `packages/earnings-core/src/earnings_core/_model.py` says the
      validators recheck every stored invariant. Size: quick-fix. Done when:
      `_own_problems` rechecks all three with tests, or that docstring is
      narrowed to hashes and derived IDs. → done in plan 4
- [x] Close D-12's portability gaps in `ArtifactRef.storage_ref` (final review,
      Minor; deferred by the user): the check in
      `packages/earnings-core/src/earnings_core/artifacts.py` is a
      case-sensitive prefix test, so `FILE:///Users/...`, `File:/...`,
      `C:/Users/...` and `../...` all pass, short of D-12's aim of never
      publishing a home directory from this public repository. Size: quick-fix.
      Done when: `storage_ref` refuses a `file:` scheme in any case, a
      drive-letter path, and a `..` segment, with tests, before Stage 4 persists
      its first `ArtifactRef`. → done in plan 4
- [x] Validate `MaskedDocument` itself (final review, Minor; deferred by the
      user): `MaskedDocument` in
      `packages/earnings-core/src/earnings_core/masks.py` has no validator, so
      building one directly bypasses the checks in `apply_masks`: document
      match, bounds, and one policy version (D-18). Size: quick-fix. Done when:
      a `model_validator` on `MaskedDocument` enforces those checks and
      `apply_masks` relies on it, with a test that a directly built bad set is
      refused, at the latest when Stage 3 first builds `MaskedDocument`s. → done in plan 4
- [ ] Reject, don't raise, on unvalidated offsets (final review, Minor; deferred
      by the user): given a candidate built by `model_copy` with a float offset,
      `validate_span` in `packages/earnings-core/src/earnings_core/evidence.py`
      raises `TypeError` at the slice, and a bool offset whose slice matches
      raises a `ValidationError` when it builds the `TextSpan`. The checks are
      meant never to raise on bad evidence (R6.2). `parse_span_candidate`
      refuses both offsets, so only code that skips it can get there. Size:
      quick-fix. Done when: `validate_span` returns `malformed_record` for a
      non-integer or bool offset on an unvalidated candidate, with a test.
- [ ] Give `Rejection` a structured subject (final review, recommendation;
      deferred by the user): `Rejection` in
      `packages/earnings-core/src/earnings_core/rejections.py` names what it
      refused only in its `detail` prose, with no `doc_id`, candidate, or
      element reference, so Stage 7 must pair each rejection with its candidate
      to keep R6.2's audit trail. Size: design. Done when: Stage 7's
      rejection-store design records whether `Rejection` gains structured
      subject fields (a schema bump with a data-dictionary update) or the store
      pairs each rejection with its candidate.
- [x] Check import boundaries statically as well (final review, recommendation;
      deferred by the user): the three
      `packages/*/tests/test_import_boundaries.py` files inspect `sys.modules`
      after a top-level import, so an import inside a function escapes them.
      Size: quick-fix. Done when: an AST scan of each package's `src/` refuses
      sibling-package and browser imports alongside the runtime check, at the
      latest when Stage 3 adds the `browser-capture` extra to
      `earnings-ingestion` (B3). → done in plan 5

## 4-structure-aware-canonicalization-plan-a — 2026-09-25
- [x] Settle the review gate's open page-artifact and mask findings (plan 4,
      Task 11; the user kept these rules at the gate on 2026-09-25):
      `docs/verification/walker-1.md` ("The review gate") and
      `docs/verification/walker-1-report.md` list them. Under `walker-1`, C5 in
      `packages/earnings-ingestion/src/earnings_ingestion/canonical/compensate.py`
      types National Health Investors' own headline, "NHI Reports 17.2%
      Increase in Third Quarter Normalized FFO", as `page_artifact` on all five
      copies, because the walker typed it a paragraph, so the canonical fixtures
      Stage 7 receives exclude it from narrative eligibility. C5 also types
      Becton Dickinson's repeated statement titles. No C rule types the end
      marks ("# # #", "***", "###") or the running heads that carry a page
      number ("Ball Corp - N", FMC's "Page N/ ..."). M1-M5 in
      `canonical/boilerplate.py` leave Becton Dickinson's "1Represents a
      non-GAAP" footnotes, which the walker typed as paragraphs, and Southwestern
      Energy's forward-looking-statements continuation paragraph unmasked. A
      retype changes elements, so it needs `walker-2`; a mask change needs
      `boilerplate/2`. Styled headings are plan B's pre-registered target, and
      ADR 0002 decides promotion. Size: plan. Done when: plan B's verification
      record or ADR 0002 gives each finding a disposition: fixed under a new
      policy version, a plan B target, or a recorded limitation. → done in plan 5

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
- [ ] Harden the frozen capture adapter (final review, Minor #4). Three defects
      in `packages/earnings-ingestion/src/earnings_ingestion/browser/selenium_capture.py`:
      - `driver.current_url`, read after navigation, runs outside `_step`, so a
        WebDriver error there escapes `capture()` instead of returning a
        `failed` capture.
      - `_Interceptor.__init__` reads `http://<debugger address>/json` with
        `urllib.request.urlopen`, which routes even 127.0.0.1 through an
        `http_proxy` variable that `no_proxy` does not cover. On such a machine
        every capture fails at startup; an opener built with `ProxyHandler({})`
        avoids it.
      - A failing `Page.getFrameTree` or `Fetch.enable` there leaves the
        WebSocket open.
      The file is frozen by `expirements/parser-fidelity/layout1-preregistered.toml`
      and changes only through `preregister.py amend`, for a crash or an invalid
      element set. Size: plan. Done when: the next adapter or capture policy
      version lands all three, with tests.
- [ ] Report `browser setup`'s ordinary failures in one line (final review,
      Minor #5): `apps/earnings-pipeline/src/earnings_pipeline/cli.py` catches
      only `ValueError`, so an `httpx.HTTPError`, an `OSError`, or
      `subprocess.TimeoutExpired` from `reported_version` prints a traceback.
      Size: quick-fix. Revisit if: a real install fails with a traceback, or the
      CLI gains a second command.
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
- [x] Give the universe manifest an operative identity (final review, Important
      #1; the user corrected the wording and deferred the design): P6-12 said
      evidence published after the cutoff cannot change a manifest's content, but
      `content_hash` in
      `packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py` covers
      withheld assertions and findings, and the SEC artifacts that identities cite,
      which `ArtifactStore.latest` picks newest first. So curating a notice
      published after 2026-09-22, or re-running `earnings-pipeline cohort
      fetch-sec`, then refreezing, makes a new version in
      `config/universe/djia/manifests/` whose intervals, mappings, and candidate
      issuers are unchanged, and Stage 5's manifests would re-version with it.
      Options: an operative hash over the cutoff-admissible content, SEC artifacts
      pinned by hash in the curated files, or both; the committed v1 must stay
      loadable. Size: design. Done when: Stage 5's spec or plan decides what
      identifies the universe for its manifests, and a test shows that a withheld
      notice and a re-fetched SEC record leave that identity unchanged. → done in plan 7
- [x] Hold the SEC and web client locks once per machine (final review, Important
      #2): `LOCK_PATH` in
      `packages/earnings-ingestion/src/earnings_ingestion/sec/client.py` and in
      `packages/earnings-ingestion/src/earnings_ingestion/cohort/web.py` resolves
      under each checkout's `data/runs/`, so a second worktree or clone takes its
      own lock, and two checkouts could together exceed the project's 2 requests
      per second (R1.3). The docstrings and P6-16 say "one per machine";
      `docs/verification/djia-cohort.md` now says one checkout.
      `test_one_client_per_machine` cannot catch it, since both of its clients
      share one `tmp_path`. Fix: put both locks in one machine-wide place, such as
      the user's cache directory, with a test that two repository roots share one
      lock. Size: quick-fix. Done when: both locks are machine-wide and tested, and
      the record says one machine again, before a second checkout or Stage 5's
      EDGAR adapter sends SEC requests. → done in plan 7
- [x] Three robustness fixes in the cohort path (final review, Minor; paths under
      `packages/earnings-ingestion/src/earnings_ingestion/` unless given in full):
      - `_build` in `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`
        catches only `CohortError`, but a bad override makes `reconstruct`
        (`cohort/intervals.py`), `resolve` (`cohort/resolution.py`), or
        `acknowledge` (`cohort/findings.py`) raise `ValueError`, which prints a
        traceback, not a `problem:` line. `terms_digest` also runs outside any
        `try` in `cohort_cli.py`'s `terms` and in `cohort/live.py`, so a terms page
        that `walker-1` cannot read aborts `verify-live` before its record is
        written.
      - `read_submissions` in `sec/data.py` lets `KeyError` and `TypeError` escape
        on a malformed `formerNames` or `filings.files` entry, and reads a string
        `tickers` as characters, though its docstring promises `SecDataError`.
      - `retry_after_seconds` in `fetch/client.py` accepts any `str.isdigit()`
        value, so a non-ASCII digit such as a superscript two reaches `float()`
        and raises `ValueError` rather than being ignored.
      Size: quick-fix. Done when: each case has a test, and each ends as a
      `problem:` line, a `SecDataError`, or an ignored header. → parts 2 and 3 done in plan 7; part 1 restated under plan 7
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
- [ ] Report `events freeze`'s citation errors as `problem:` lines (plan 7's
      final review, Minor): `freeze_command` in
      `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py` catches only
      `EventFreezeRefused`, but `freeze_events` (`events/freeze.py`) builds the
      evidence record with `evidence_of` (`events/evidence.py`), which raises
      `LocatorError`, a `ValueError`, when a value it cites is not in a saved
      page's `walker-1` text, so the command prints a traceback. Nothing is
      written, since the record is built before either file. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`
      unless given in full. Size: quick-fix. Done when: such a case has a test
      and ends as a `problem:` line.
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
- [ ] Refuse a repeated acknowledgement (plan 7's final review, Minor):
      `EventOverridesFile._distinct` in `events/records.py` refuses a repeated
      `override_id` and, per P7-14, a second override of one kind for one
      `event_id`, but an `acknowledge` override names a `finding_id`, not an
      `event_id`, so two acknowledgements of one finding both load. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`.
      Size: quick-fix. Done when: `EventOverridesFile` refuses a `finding_id`
      repeated among acknowledgements, with a test.
- [ ] Bind an evidence record to its manifest when loading (plan 7's final
      review, Minor): `load_event_evidence` in `events/freeze.py` checks only
      that the file's name matches its `event_manifest_version`. Nothing
      compares its `event_manifest_hash` with the `content_hash` of the manifest
      beside it, so an evidence record from another corpus, or from other
      content under the same version, would load. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`.
      Size: quick-fix. Done when: loading an evidence record checks its
      `corpus_id` and `event_manifest_hash` against the manifest of its version,
      with a test.
