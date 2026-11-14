# Deferred items

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

## 3-core-evidence-spine — 2026-09-25
- [x] Accept a stored `VerifiedSpan` in `validate_span` (final review, Important
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
      `VerifiedSpan`s. → done in plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md)
- [x] Report every crossing in `validate_elements` (final review, Minor;
      deferred by the user): `_crossings` in
      `packages/earnings-core/src/earnings_core/structure.py` never pushes an
      element it has reported, so a later crossing against that element goes
      unreported. With A=[0,10), B=[5,15) and C=[12,20), B is reported against A
      but not against C. The set is still refused, but D-8 promises every
      structural problem at once. Size: quick-fix. Done when: that case reports
      both crossings, with a test. → done in plan 4
- [x] Prefer the genuine element in `resolve_pointer` (final review, Minor;
      deferred by the user): `resolve_pointer` in
      `packages/earnings-core/src/earnings_core/structure.py` returns
      `wrong_document` for the first element whose ID matches, while
      `validate_span`'s `_element` skips elements of another version. Under D-1
      an unchanged region keeps its `element_id` across versions, so for a
      mixed-version element list the outcome depends on list order. Size:
      quick-fix. Done when: `resolve_pointer` resolves the genuine element
      wherever it sits in the list, with a test that lists the stale element
      first. → done in plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md)
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
- [x] Reject, don't raise, on unvalidated offsets (final review, Minor; deferred
      by the user): given a candidate built by `model_copy` with a float offset,
      `validate_span` in `packages/earnings-core/src/earnings_core/evidence.py`
      raises `TypeError` at the slice, and a bool offset whose slice matches
      raises a `ValidationError` when it builds the `TextSpan`. The checks are
      meant never to raise on bad evidence (R6.2). `parse_span_candidate`
      refuses both offsets, so only code that skips it can get there. Size:
      quick-fix. Done when: `validate_span` returns `malformed_record` for a
      non-integer or bool offset on an unvalidated candidate, with a test. → done in plan 11 (specs/plans/completed/11-evidence-selection-and-verification-plan-a.md)
- [x] Give `Rejection` a structured subject (final review, recommendation;
      deferred by the user): `Rejection` in
      `packages/earnings-core/src/earnings_core/rejections.py` names what it
      refused only in its `detail` prose, with no `doc_id`, candidate, or
      element reference, so Stage 7 must pair each rejection with its candidate
      to keep R6.2's audit trail. Size: design. Done when: Stage 7's
      rejection-store design records whether `Rejection` gains structured
      subject fields (a schema bump with a data-dictionary update) or the store
      pairs each rejection with its candidate. → done in plan 12 (specs/plans/completed/12-evidence-selection-and-verification-plan-b.md): the store pairs each core `Rejection` with its subject (ES6)
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
- [x] Harden the frozen capture adapter (final review, Minor #4). Three defects
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
      version lands all three, with tests. → done in plan 15
      (`specs/plans/completed/15-evidence-linked-theme-extraction.md`): all three
      lifecycle/isolation fixes, covering invented tests and two approved frozen
      adapter amendments landed; no actual capture regeneration is asserted.

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

## 7-event-discovery-eligibility-and-acquisition-plan-a — 2026-09-27
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
- [x] Decide which frozen version is current after a revert (PR #6's review,
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
      freezes a changed v2, reverts, and runs select. → done in plan 8
- [x] Refuse a frozen version that repeats another's content or lacks its
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
      recorded. → done in plan 8
- [x] Decide whether loading a pilot re-derives its selection (PR #6's review,
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
      pilots still load. → done in plan 8
- [x] Cross-check an index page against its submissions row beyond the
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
      before it fetches, with synthetic cases for both disagreements. → done in plan 8
- [x] Refuse a redirected response (PR #6's review, F13): the shared client
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
      a synthetic redirected record; before plan B's first acquisition. → done in plan 8
- [x] Read a primary document with no Item line as unread (PR #6's review, found
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
      without a traceback. → done in plan 8
- [x] Print the request count on every stop, and take an approved count in every
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
      the next live cohort run or plan B's first live request. → done in plan 8
- [x] Check the CLIs' store and corpus paths before anything runs (PR #6's
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
      absolute path; each with a test, before plan B's first acquisition. → done in plan 8
- [x] Refuse a relative `EARNINGS_LOCK_DIR` (PR #6's review, F29):
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
      live SEC request. → done in plan 8
- [x] Commit the check that the real frozen records hold no source wording (PR
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
      test that skips without the store does not protect CI. → done in plan 8
