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
      `release-id/2` deciding whether a contradiction holds the freeze.
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
        `SavedResponses` in build and freeze, `frozen_event_manifests` in select,
        and `write_new` in freeze and select. So a tampered manifest, an empty or
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
      makes build refuse cleanly; a tampered `events-v1.json` makes select refuse
      cleanly; an empty retrieval record ends build with a `problem:` line naming
      its path; and a leftover evidence file with other bytes gives the named
      refusal while an identical one still completes the freeze; each with a test
      and no traceback.
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
        promising that saved data clears it.
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
- [ ] Refuse a repeated acknowledgement (plan 7's final review, Minor):
      `EventOverridesFile._distinct` in `events/records.py` refuses a repeated
      `override_id` and, per P7-14, a second override of one kind for one
      `event_id`, but an `acknowledge` override names a `finding_id`, not an
      `event_id`, so two acknowledgements of one finding both load. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`.
      Size: quick-fix. Done when: `EventOverridesFile` refuses a `finding_id`
      repeated among acknowledgements, with a test.
- [x] Bind an evidence record to its manifest when loading (plan 7's final
      review, Minor): `load_event_evidence` in `events/freeze.py` checks only
      that the file's name matches its `event_manifest_version`. Nothing
      compares its `event_manifest_hash` with the `content_hash` of the manifest
      beside it, so an evidence record from another corpus, or from other
      content under the same version, would load. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`.
      Size: quick-fix. Done when: loading an evidence record checks its
      `corpus_id` and `event_manifest_hash` against the manifest of its version,
      with a test. → fixed in PR #6 (Codex round 4, C1)

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
- [ ] Decide which frozen version is current after a revert (PR #6's review,
      F4): `freeze_events` in `events/freeze.py` returns an older version when the
      build's content matches it, but `select_command` in
      `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py` always reads the
      highest-numbered event manifest, and prints neither the version nor the hash
      it read. So after a change is frozen as v2 and then reverted, `events
      freeze` says "unchanged: v1" while `events select` draws a new pilot from
      the withdrawn v2. The code follows the spec's §Commands ("the latest frozen
      event manifest") and P7-18, so this is a gap in the versioning model, shared
      by every consumer that takes the latest version, plan B's pilot pick among
      them. The pilot records the event manifest version and hash it read, so the
      chain can be audited. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/` unless given in full.
      Size: design. Done when: the rule for the current version after a revert,
      for event manifests, universes, and pilots, is recorded as an amendment to
      the spec's §Commands and P7-18; `events select`, and plan B's pilot pick,
      read the version the current build matches or refuse when a newer one
      exists, and print the version and hash they read; and a test freezes v1,
      freezes a changed v2, reverts, and runs select.
- [ ] Refuse a frozen version that repeats another's content or lacks its
      evidence (PR #6's review, F22): `event_manifest_version` is not hashed, so a
      hand-renumbered copy of `events-v1.json` loads beside v1 with the same
      content hash, and `frozen_event_manifests` in `events/freeze.py` loads a
      manifest whose `events-v<N>.evidence.json` is missing. In that state `events
      freeze` names v1 while `events select` binds a new pilot to the copy, which
      has no evidence record. No code path writes either state, since the freeze
      writes the evidence first and matches on content. Stage 4's
      `frozen_manifests` in `cohort/freeze.py` has the same shape (P6-14). Check
      the evidence file in `frozen_event_manifests`, not in
      `load_event_manifest`, which the pilot's chain check and a tamper test use.
      Paths are under `packages/earnings-ingestion/src/earnings_ingestion/`.
      Size: quick-fix. Done when: `frozen_event_manifests` refuses a manifest
      whose evidence file is missing; it and `frozen_pilots` in `events/pilot.py`
      refuse two versions that share a content hash, each with a test; and
      Stage 4's `frozen_manifests` does the same, or the reason it does not is
      recorded.
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
- [ ] Decide whether loading a pilot re-derives its selection (PR #6's review,
      F10): `check_chain` in `events/pilot.py` rechecks the hashes, the seed, and
      eligibility, as the spec's §Pilot selection and plan 7's Task 14 list, but
      not that `djia-pilot/1` produces the rows. So a hand-edited pilot with its
      content hash recomputed loads: one with a row swapped for another eligible
      event, or one naming another policy, another `pilot_id`, or `underfilled`
      at target 40. Plan B's gate is that the pilot loads and its chain checks.
      Re-deriving at load time makes a frozen pilot's loading depend on the
      current selection code, so plan B should choose it deliberately. Do not
      compare `universe_version`: a universe re-versioned with the same operative
      hash differs there legitimately. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: design. Done
      when: plan B records the choice, and, if it re-derives, `load_pilot`
      compares the selection policy version and requires that `select_pilot`
      over its event manifest and universe reproduce its content hash, with
      tamper tests (a swapped row, the policy, the `pilot_id`, and
      `underfilled`), each rehashed and refused, while the real and synthetic v1
      pilots still load.
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
- [ ] Cross-check an index page against its submissions row beyond the
      accession (PR #6's review, F12): the build and discovery take a filing's
      form and primary document from its submissions row, and the index page's
      form and document table, which `sec/filing_index.py` reads, are compared
      with the row on the accession alone. If SEC's two records disagreed, a
      page for an 8-K/A listed as an 8-K could become a candidate the rule
      chooses, and a row whose `primaryDocument` names the EX-99 file, or is
      empty, would have discovery (`events/discover.py`) fetch an exhibit before
      the freeze, against EV2, and read as an unread candidate that can freeze as
      the release. None of v1's 269 candidates disagrees. Slots take the row's
      report date by design (P7-9), and an unread candidate staying is the spec's
      rule. Plan B reads each index page's document table for the EX-99 exhibits
      anyway. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: plan. Done
      when: the index page's form must equal the row's, and the row's primary
      document, compared by its base name, must be listed in the index typed as
      the form, each a problem otherwise, checked in the build and in discovery
      before it fetches, with synthetic cases for both disagreements.
- [ ] Refuse a redirected response (PR #6's review, F13): the shared client
      (`fetch/client.py`) follows redirects within SEC's hosts and records
      `final_url`, but nothing reads it. `SavedResponses` in `events/saved.py`,
      like Stage 4's `ArtifactStore.latest` in `fetch/store.py`, serves each
      retrieval under its `request_url`, and `_citations_refused` in
      `events/build.py` accepts a citation grounded in a redirected record. So a
      primary document that redirects to another page is read as the
      candidate's 8-K and cited under the URL requested. None of the 661 records
      saved behind v1 was redirected; plan B's exhibits, which become canonical
      text and quotes, raise the stakes. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: quick-fix.
      Done when: a fetch whose `final_url` differs from its `request_url` is
      refused before it is saved, and `SavedResponses.get` and
      `_citations_refused` refuse one already saved, by raising, never by
      skipping it, which would make discovery refetch it on every run, each with
      a synthetic redirected record; before plan B's first acquisition.
- [ ] Read a primary document with no Item line as unread (PR #6's review, found
      with F13): `read_text` in `events/release.py` pairs each Item heading with the
      one after it through `zip(..., strict=True)`, which raises `ValueError` when
      the text has no line that begins "Item" and a number at all, so it never
      returns its `Reading(unread=...)`. Text with some other Item line but no Item
      2.02 reads as unread, as it should. The module docstring promises that a
      document with no such heading states nothing. `read_document` does not catch
      the error, and `identify` wraps only `saved.get`, so it escapes `build_events`
      in `events/build.py`, which `events build` and `events freeze` print as a
      traceback, and the documents phase of `discover` in `events/discover.py`,
      where `discover_command` in
      `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py` catches it as a
      `ValueError` and says a rerun fetches only what is missing, and every rerun
      meets the same stop. A primary document that redirects to a page with no Item
      line (F13), or one whose Item headings `walker-1` does not start a line with,
      can reach it through plan A's commands today. v1 does not: the build over the
      saved responses behind v1 reads each of its candidates without raising. Paths
      are under `packages/earnings-ingestion/src/earnings_ingestion/` unless given
      in full. Size: quick-fix. Done when: `read_text` returns `Reading(unread=...)`
      for text with no Item line, with a unit test in
      `packages/earnings-ingestion/tests/test_events_release.py`, and `events build`
      over a synthetic candidate whose primary document has no Item line ends
      without a traceback.
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
- [ ] Recover a saved response that is present but unusable (PR #6's review, P2.1
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
- [ ] Print the request count on every stop, and take an approved count in every
      live cohort command (PR #6's review, F31 and F35); paths are under
      `apps/earnings-pipeline/src/earnings_pipeline/`:
      - `discover_command` in `events_cli.py` reads the count in a `finally` but
        prints it only when it catches `AccessStop`, `UnexpectedResponse`,
        `ValueError`, or `RuntimeError`, so an `OSError` from
        `ArtifactStore.put` (a full disk, permissions), a `FileNotFoundError` for
        a saved body that is gone, and a Ctrl-C end with a traceback and no
        count, though each live gate records the count. `cohort_cli.py`'s
        handlers share the pattern.
      - `cohort fetch-sec` prints no count when a 403, a block page, or an
        unexpected response stops it, and `cohort verify-live` never prints one,
        though plan 6's gate table records the requests sent. Both run under the
        client's default cap of 500 (P6-16), where `events discover` takes the
        count the user approved (P7-10); committed config fixes fetch-sec's
        volume, 44 requests in v1's run.
      Fix: add `OSError` to the stop tuple, and a separate `except
      KeyboardInterrupt` that prints the count and re-raises (a bare outer
      `finally` would print it twice), in both CLIs; give `fetch-sec` and
      `verify-live` a required `--max-requests` (`terms` sends one request and
      can keep the default), print their requests sent on every exit, and add
      the count to the `verify-live` record. Size: quick-fix. Done when: with a
      monkeypatched fake client, never `open_sec_client`, a `put` raising
      `OSError` and a deleted companyfacts body each end `events discover` with
      "Stopped:" and "requests sent: N"; and `fetch-sec` without the flag exits 1
      before it opens the client, and a stop prints its count; with tests, before
      the next live cohort run or plan B's first live request.
- [ ] Check the CLIs' store and corpus paths before anything runs (PR #6's
      review, F19 and F38): `events_cli.py` and `cohort_cli.py`, under
      `apps/earnings-pipeline/src/earnings_pipeline/`, resolve only `--repo`.
      - `--store` accepts any repo-relative directory, and `tests/fixtures/**` is
        un-ignored, so `events --store tests/fixtures/... discover` would save
        real SEC responses where `git add -A` publishes them to this public
        repository, and a later freeze would cite them as `local_only` bytes kept
        under `data/raw/`. That takes a non-default flag and a commit, and the
        flag is documented design (P7-18), as Stage 4's is.
      - With an absolute `--corpus-dir` outside the repo, or a path inside it
        spelled through a symlinked prefix (`/var` for `/private/var`), `events
        freeze` and `events select` write their frozen files and then crash on
        `relative_to` while printing them, and a rerun prints "unchanged:" and
        crashes again. `cohort_cli.py` has had the same code since Stage 4.
      Fix: in every command that writes fetched bytes (`events discover`, plan
      B's `events acquire`, `cohort fetch`, and `cohort fetch-sec`), refuse a
      store root that does not resolve under `<repo>/data/raw`, in the callback,
      before any client opens, leaving build, freeze, and select unguarded;
      resolve paths only for such checks, never the stored root, which would
      break a symlinked `data/`; and print paths relative to the repo when
      possible and absolute otherwise. `test_discover_filing_spends_at_most_two_requests`
      then needs `store=data/raw/events`. Size: quick-fix. Done when: `events
      --store tests/fixtures/x discover --max-requests 1`, with `open_sec_client`
      patched to fail, exits 1 with "Refused" and never opens the client, and so
      do the cohort's fetching commands; and `events freeze` and `events select`
      with an absolute corpus directory outside the repo exit 0 and print its
      absolute path; each with a test, before plan B's first acquisition.
- [ ] Refuse a relative `EARNINGS_LOCK_DIR` (PR #6's review, F29):
      `machine_lock_dir` in `fetch/client.py` returns the override as given, so a
      relative value resolves against each process's working directory, and two
      checkouts would take two SEC locks and could together send 4 requests per
      second, against the project's 2 per machine (R1.3). Three lines later the
      same function ignores a relative `XDG_CACHE_HOME`. The variable is a test
      override (P7-5), which only the test fixtures set, to an absolute
      directory, so only a hand-made export triggers this. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Size: quick-fix.
      Done when: a relative value makes `machine_lock_dir` raise `AccessStop`
      naming the variable, or is ignored as the XDG rule does, with a test using
      `monkeypatch.setenv(LOCK_DIR_VARIABLE, ".locks")`, before plan B's first
      live SEC request.
- [ ] Commit the check that the real frozen records hold no source wording (PR
      #6's review, F20): the committed P6-3 test in
      `tests/integration/test_event_fixtures.py` scans only the synthetic
      corpus's pages. The real v1 records were checked at plan 7's gates with a
      scratch script whose source is in plan 7, and plan 7's handoff points plan
      B at it. Plan B's exhibit acquisition is where a reviewer is likeliest to
      copy wording, into an override's rationale for instance, and the default
      suite reads only `tests/fixtures/events/`. A 30-character window would flag
      a generic date phrase in v1's `overrides.toml`, so compare whole strings, or
      long shingles that allow for facts. Size: quick-fix. Done when: an offline
      test, skipped when `data/raw/events/sec-edgar/` is absent, compares
      `config/corpus/*/events-v*.json`, `*.evidence.json`, `pilot-v*.json`, and
      `overrides.toml` with the saved HTML, text, and exhibit pages; a temporary
      corpus whose rationale copies 40 characters of a synthetic saved page fails
      it while the real v1 records pass; and each freeze's gate runs it, since a
      test that skips without the store does not protect CI.
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
- [ ] Decide whether two issuers' events may share one release (PR #6's review
      of its F1 fix): `_shared_releases` in `events/build.py` refuses a
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
