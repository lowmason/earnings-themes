# layout-1 and the browser diagnostic path: verification record

This record verifies plan B of `specs/completed/structure-aware-canonicalization.md`, the
browser diagnostic path. Plan 5 (`specs/plans/completed/5-structure-aware-canonicalization.md`)
built it. With plan A, whose record is `docs/verification/walker-1.md`, it completes
Stage 3.

## What was verified

| Plan B exit criterion | Evidence |
| --- | --- |
| 1. The extra, the pinned binaries and the setup command; no processing run downloads | The `browser-capture` extra and `uv.lock`; `browser/chrome-for-testing.toml`; `earnings-pipeline browser setup`; `test_a_capture_never_runs_selenium_manager` |
| 2. Calibration, classified, with no gold change | `docs/verification/browser-calibration.md` |
| 3. The network guard | `test_every_request_is_blocked_recorded_and_never_made`, under `isolated/1` and under Fetch interception alone; `test_document_javascript_never_runs` |
| 4. One rendered-text hash | `test_two_captures_have_the_same_text_and_layout_hashes`; the recapture of every committed capture |
| 5. Exact spans or `alignment_failed`; the contract with the real pair | `test_every_layout1_unit_is_an_exact_span_or_an_alignment_failure`; `tests/contracts/test_element_schema_parsers.py` |
| 6. The comparison | `docs/verification/layout-1-comparison.md` |
| 7. ADR 0002 | `docs/adr/0002-keep-the-browser-capture-diagnostic-only.md`, outcome 1; nothing is promoted, so nothing is re-canonicalized |
| 8. R3.5 final | `docs/verification/R3.5-text-fidelity.md`, with both legs |
| 9. The import scan and the runtime checks | `tests/contracts/test_import_scan.py`; `packages/earnings-ingestion/tests/test_import_boundaries.py` |
| 10. No browser by default; browser checks opt-in, skipping visibly, recording the environment | The documented command, `-m "not live and not browser"`; the browser checks, run with `-m browser -rs` |

## The environment

`environment: Chrome for Testing 154.0.8037.57, chromedriver 154.0.8037.57, Selenium
4.49.0, Darwin 26.6.2 arm64`. The eight release captures share it
(`test_every_capture_shares_one_pinned_environment`).

The final browser checks ran on 2026-09-26: `22 passed, 642 deselected`.

## The pre-registration

- **The freeze.** Commit `cdc77b87bd94` froze 23 files on 2026-09-26, before any
  release was captured.
- **Post-freeze fixes.** None.
- **A corrected check.** After the release captures, one unfrozen plan test failed on
  Pharmacyclics (`0000949699-08-000023_ex-99-1`):
  `test_every_layout1_unit_is_an_exact_span_or_an_alignment_failure`, in
  `tests/integration/test_browser_fixtures.py`.
  - **The cause.** C1 types the 12 column blocks of that `<pre>` release as cell-less
    `table` units, exactly as `walker-1` does. The test counted every `table` element
    as a cell container, so it missed them.
  - **What held.** All 46 of the release's units were exact spans, and
    `validate_elements` accepted them.
  - **The correction.** With the user's approval, the test now excludes only table
    containers, the elements that are some element's parent.
  - **Its standing.** No frozen file changed, so this is not an amendment, and no
    number in the comparison depends on the test.
- **What the planner saw before the freeze** (plan 5, PB-13):
  - the three development releases, which layout-1 and `anchored-1` were developed
    on;
  - the units, derived from the gold and the frozen walker's output;
  - structural greps of the fixture sources: no stylesheet, no `class` attribute, no
    `<th>`, no bold `font` shorthand, and Becton Dickinson's 1,394 inline
    `display: none`;
  - one load of National Health Investors' `innerText`, twice, for a determinism
    check, with no layout read;
  - the review-gate findings' element types in the committed `walker-1` fixtures;
  - the triggers on `walker-1`'s output: `prose_row` on Southwest Airlines and
    National Health Investors.

## Calibration

- `0000706863-16-000110_ex-99-1` (narrative-only): 42 differences, 11 in whitespace
  and 31 in table-cell separation.
- `0000877860-13-000100_ex-99-1` (table-bearing): 615 differences, 37 in whitespace
  and 578 in table-cell separation.
- `0000009389-10-000004_ex-99-1` (malformed layout): 629 differences, 149 in
  whitespace, 479 in table-cell separation, and 1 in image alternative text.

None has a visible-character difference. The copies are calibration observations, not
gold, and no gold changed.

## R3.5's second leg

- **Against `innerText`:** 41 hunks, 39 Unicode and 2 other.
- **Against the copies:** 43 hunks, 39 Unicode and 4 other.

No hunk is a numeric sign, a scale, a superscript, a footnote or a table heading.
Each Unicode hunk is a bullet glyph that the canonical text omits. Two other hunks,
in both references, are joined words in Becton Dickinson's canonical text
(`ForeignCurrencyTranslation`, where the browser shows three words). The copies add
two more: image alternative texts that `innerText` omits.

## The comparison and ADR 0002

- **Targeted classes.** Units lost, for walker-1, layout-1 and the fallback:
  - headings typed `paragraph` by W12: of 23, 23, 14 and 21;
  - prose inside data tables: of 38, 38, 32 and 32;
  - content hidden by stylesheets: no units.
- **Regressions.** layout-1: 0. The fallback: 0.
- **The decision.** `docs/adr/0002-keep-the-browser-capture-diagnostic-only.md`
  records outcome 1, chosen by the user on 2026-09-26. The reason is that promotion's
  gain is small for the stage that consumes it, while its cost falls on every
  document:
  - it would recover 6 of the 38 prose-in-table units that R4.2 keeps from Stage 7's
    narrative extraction, in 2 of 8 documents;
  - it would make a pinned-platform capture an input to canonicalization for every
    Stage 5 and Stage 15 release.

  The user adopted this reasoning from the recommendation given at the gate, and
  added no note.

## The review gate's findings

Plan 4's review gate left these open (`docs/verification/walker-1.md`, "The review
gate"). Each now has a disposition (plan 5, PB-21). This closes the deferred item
"Settle the review gate's open page-artifact and mask findings".

| Finding | Types: walker-1 / layout-1 / fallback | Disposition |
| --- | --- | --- |
| National Health Investors' headline | `page_artifact` 5 / `heading` 1, `page_artifact` 4 / `heading` 1, `page_artifact` 4 | A limitation of `walker-1`, excluded from narrative eligibility |
| Becton Dickinson's statement titles | `page_artifact` 9 / `page_artifact` 9 / `page_artifact` 9 | A limitation of `walker-1` |
| End marks | `paragraph` 4, `footnote` 3 / `paragraph` 3, `footnote` 3, `heading` 1 (Pharmacyclics' `###`) / `paragraph` 4, `footnote` 3 | A limitation: no rule types them, and C5 is not amended |
| Ball's numbered running heads | `paragraph` 3 / `paragraph` 3 / `paragraph` 3 | A limitation of `walker-1` |
| FMC's numbered running heads | `heading` 5 / `heading` 5 / `heading` 5 | A limitation of `walker-1` |
| Becton Dickinson's non-GAAP footnotes, unmasked | `paragraph` 3 / `paragraph` 3 / `paragraph` 3 | A limitation of `boilerplate/1`: a mask change needs `boilerplate/2`, which no stage plans |
| Southwestern Energy's forward-looking continuation, unmasked | `paragraph` 1 / `paragraph` 1 / `paragraph` 1 | A limitation of `boilerplate/1`: at the gate the user declined a rule fitted to one test-set instance |

## Limitations

- **Platform.** The pin covers mac-arm64 only. Anywhere else a capture is
  `unavailable`.
- **The crash database.** Chrome's crash handler keeps its database in
  `~/Library/Application Support/Google/Chrome for Testing/Crashpad`, outside the
  temporary profile (PB-6).
- **layout-1's output.** layout-1 emits no sentences and no list containers. Nothing
  the comparison scores reads them, and ADR 0002 promotes nothing, so no canonical
  document carries layout-1's elements.
- **Class 3.** It has no units: no fixture carries a stylesheet, so content that a
  stylesheet hides was never measured on a release.
- **Development-set numbers.** The fixtures were Stage 1's test set, and the classes
  were named from its failures (SC2). R12.2's validation set is the independent test.
- **Machine paths in the captures.** In seven of the eight release captures, the
  blocked-request URLs carry the capturing machine's temporary directory
  (`file:///private/var/folders/…/earnings-capture-<random>/page/<image>`). The
  frozen adapter writes them, and no metric reads them. At the final review the user
  chose to record this rather than rewrite the committed captures. The deferred
  items carry the fix for the next capture.
- **Words joined across `<br>` in table cells.** R3.5's second leg shows `walker-1`
  joining Becton Dickinson's header cells `Foreign<br>Currency<br>Translation` as
  `ForeignCurrencyTranslation`. A change to canonical text needs a new policy
  version (SC14), so this stays a limitation of `walker-1`. Table cells are cell
  evidence, outside narrative extraction (R4.2).
