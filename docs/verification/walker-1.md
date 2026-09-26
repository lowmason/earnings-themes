# walker-1: plan A's verification record

This record verifies plan A of `specs/structure-aware-canonicalization.md`, the
canonicalizer, for Stage 3 of `specs/evidence-linked-theme-extraction-roadmap.md`.
Plan 4 (`specs/plans/4-structure-aware-canonicalization-plan-a.md`) built it. Plan B,
the browser diagnostic path, adds its own record, and Stage 3 is complete only then.

**Outcome:** `walker-1` turns all eight Stage 1 fixtures, offline, into valid hashed
canonical documents. Their canonical fixtures were committed after the review gate.

Two generated reports sit beside this record, and harness tests keep both current:

- `walker-1-report.md` holds the re-score, the page-artifact report, and the mask
  report.
- `R3.5-text-fidelity.md` holds R3.5's report, plan A's leg.

Every number here is a development-set number: the fixtures were Stage 1's test set
(SC2).

## What was verified

The items are numbered as in the spec's §Verification (plan A).

| Item | Evidence | Result |
| --- | --- | --- |
| 1. Port equality | `expirements/parser-fidelity/test_port_equality.py` | Equal on 11 synthetic constructs, the 8 fixtures, the 3 development releases, nesting 254 deep, and 9 decoding cases. The committed modules are exactly `port_walker.py`'s output, and no frozen file changed. |
| 2. Re-score | `walker-1-report.md` | See "Re-score" and "Page artifacts" |
| 3. Golden master | `tests/integration/test_canonical_golden.py` | The eight canonical fixtures regenerate byte for byte |
| 4. R3.1 and R4.1 | `tests/integration/test_canonical_fixtures.py` | Every fixture canonicalizes under a network guard. `validate_elements` returns nothing, every span slices its unit, the hashes round-trip, and every sentence verifies. |
| 5. R4.2 | `tests/integration/test_canonical_fixtures.py` | No narrative element or sentence overlaps a table, and all three positive controls hold |
| 6. R4.3 | `packages/earnings-core/tests/test_ocr.py`, `tests/integration/test_canonical_fixtures.py`, `packages/earnings-ingestion/tests/test_canonicalize.py` | A span over OCR text is refused with `ocr_derived_text`. Every fixture element is `native`. Image-only HTML fails with `no_native_text` and its image count. |
| 7. V9 normalization | `packages/earnings-ingestion/tests/test_normalize.py` | Every case the spec lists |
| 8. V9 sentence splitting | `packages/earnings-ingestion/tests/test_sentences.py` | Every case the spec lists |
| 9. Rules | `packages/earnings-ingestion/tests/test_compensate.py`, `test_boilerplate.py`, `test_sentences.py` | Positive and negative cases for each of C1–C5, M1–M5, and S1 |
| 10. R3.5 | `R3.5-text-fidelity.md` | Committed after this record, by plan 4's Task 13 |
| 11. Suites | plan 4's Task 14 | Checked at plan 4's final verification |

## Re-score

The frozen `score.py` scored three projections of each fixture (PA-13):

- the frozen walker;
- `walker-1` with C1 alone;
- the whole of `walker-1`.

The counts are exact, pooled by class. These are the counts as first generated,
before the gate:

- **C1.** No regression. Pharmacyclics' twelve `<pre>` statements become tables, so
  narrative_only's `header_table` losses fall from 12/12 to 4/12. The tables have no
  cells, so their header texts sit in no header cell. The manifest records this
  limitation as `pre_table_without_cells`.
- **C2–C5.** One regression: clean_html's `header_section` losses rise from 7/30 to
  13/30. C5 retyped FMC's repeated statement titles as `page_artifact`, which projects
  to `other`. Six section headings were lost with them: b056, b057, b062, b079, b088
  and b089. The review gate resolved it (see "The review gate").
- **Everything else.** Every other class and metric is unchanged, and no denominator
  changed.

## Page artifacts

These are the counts as first generated, before the gate. Against the gold's 97
`page_artifact` blocks, counted per anchor, 87 canonical blocks begin with a gold
anchor, and 60 of those are typed `page_artifact`.

Over the eight fixtures, the rules retyped:

| Rule | Retypes |
| --- | --- |
| C1 | 12 |
| C2 | 8 |
| C3 | 13 |
| C4 | 0 |
| C5 | 82 |

- **Typed as the gold types them.**
  - Every EDGAR header line (C2).
  - Becton Dickinson's and National Health Investors' page numbers (C3).
  - Running heads repeated three or more times (C5), such as "- MORE -", "-more-"
    and "/more".
- **Missed.** No rule reaches these:
  - 27 of the 87 anchored blocks, which stay untyped:
    - the end marks "# # #", "***" and "###", FMC's row of asterisks, and
      "---FINANCIALS ATTACHED---" (8);
    - running heads that carry a page number, and so never repeat verbatim: Ball's
      "Ball Corp - N" (3) and FMC's "Page N/ FMC Corporation Announces Fourth
      Quarter Results" (5);
    - Ball's "Condensed Financials (December 2009)" (3), FMC's underscore rules (6),
      and National Health Investors' "Exhibit 99" (2);
  - Southwestern Energy's "Page N of 5" lines and its "Southwestern Energy Company
    and Subsidiaries" running head. These never form whole blocks, so C4 fires on no
    fixture.

  Plan 4's text listed only the end marks and Southwestern's lines here; the counts
  above are the report's.
- **Typed beyond the gold.** 43 page artifacts match no gold anchor, all retyped by
  C5:
  - Southwestern's four lone "·" bullet glyphs;
  - Ball's address lines, which the walker splits in two;
  - Becton Dickinson's and FMC's statement titles and unit lines.

  National Health Investors' headline, "NHI Reports 17.2% Increase in Third Quarter
  Normalized FFO", is typed along with its four gold running heads: 5 of 5 copies.

## Masks

These are the counts as first generated, before the gate. Policy `boilerplate/1`
placed 27 masks on the eight fixtures.

The mask report flags every unmasked narrative block that mentions forward-looking
statements or non-GAAP measures (PA-20). It flags 15 blocks: 6 in Southwestern
Energy, 4 in Becton Dickinson, and 5 in FMC.

- **Flagged.**
  - Southwestern's forward-looking-statements paragraph, where it continues after a
    page break.
  - Becton Dickinson's "1Represents a non-GAAP…" footnotes, which are typed as
    paragraphs.
  - Body paragraphs and footnotes that mention non-GAAP measures without the
    disclaimer wording M4 requires.
- **Masked, and worth a look.**
  - Ball's "# # #" end mark is masked `safe_harbor`, because it falls inside M1's
    extent.
  - Pharmacyclics' company description is masked `repeated_legal` by M5.

## The review gate

On 2026-09-25, the user reviewed `walker-1-report.md` as first generated (§Gates
(plan A)).

- **The C2–C5 regression.** The user amended C5, choosing "Amend C5" with no further
  note. As amended, C5 never retypes a block the walker typed heading, though a
  heading still counts toward its text's occurrences. The option chosen gave its
  reason and its measured cost: it removes the regression, and Ball's three
  "Unaudited Notes to Condensed Financials (December 2009)" running heads and four
  "Ball Corporation" address fragments stay headings. Exit criterion 1 stands as
  approved.
- **Mask rules.** No amendment. The user kept M1–M5. Southwestern's
  forward-looking-statements continuation, the one real miss among the 15 flagged
  blocks, and Becton Dickinson's non-GAAP footnotes typed as paragraphs stay open
  findings for plan B. Catching the continuation would take a new rule fitted to one
  test-set instance.
- **Compensation rules.** C5 as above, and no other amendment. The user kept C2–C4
  and the rest of C5, knowing that National Health Investors' headline stays
  `page_artifact`: the walker typed it a paragraph, so the amendment does not reach
  it, and the fixtures Stage 7 receives exclude it from narrative eligibility. The
  headline, Becton Dickinson's statement titles, the untyped end marks, and the
  numbered running heads go to plan B and ADR 0002.
- **Tests an amendment added or rewrote.** In
  `packages/earnings-ingestion/tests/test_compensate.py`:
  - added `test_c5_never_retypes_a_heading`;
  - rewrote `test_c5_retypes_short_blocks_that_repeat_three_times`, whose running
    lines were styled headings and are now paragraphs;
  - rewrote `test_c5_drops_the_level_of_a_repeated_html_heading` as
    `test_a_retype_drops_a_headings_level`, which checks the level drop through C4.

  The amendment was committed on its own, before the fixtures.
- **Post-hoc numbers.** The committed fixtures and both generated reports were
  measured after the C5 amendment, so their numbers are post-hoc.
  - The user decided on a pre-amendment what-if: a scratch run of the report with C5
    amended. The regenerated report equals it byte for byte.
  - After the amendment, the re-score's verdict lists no regression. clean_html's
    `header_section` losses are back to 7/30, and C1's improvement stands.
  - C5 retypes 62 blocks, not 82: Ball 7 instead of 14, and FMC 5 instead of 18.
    57 of the 87 anchored blocks are typed `page_artifact`, not 60. Ball's three
    "Unaudited Notes…" running heads join the untyped blocks, which makes 30.
  - Page artifacts matching no gold anchor fall from 43 to 26: FMC's from 13 to 0,
    and Ball's from 8 to 4, the street-address lines. The "Typed beyond the gold"
    list above describes the report as first generated.
  - The masks did not change.

The names `walker-1` and `boilerplate/1` stand, because neither was published before
the gate.

## After the final review

Plan 4's final whole-branch review, on 2026-09-25, found two Important issues. The
user chose each fix.

- **Crafted input raised.** Like the frozen code, `canonicalize` raised on input it
  cannot read:
  - a charset label naming a codec that is not a text encoding, or one that refuses
    `errors="replace"`;
  - a label that decodes to a lone surrogate;
  - a span or font weight that `int()` refuses.

  It now returns `parse_failed` with the exception in the detail. An invalid
  `source_document_id` still raises. The port stays verbatim, and no output changed.
  The spec's §Failures still reads "`parse_failed` — lxml raised" and "Decoding never
  fails", as approved. This record, the data dictionary, and `records.py` give the
  reading as built. The regression tests are in
  `packages/earnings-ingestion/tests/test_canonicalize.py`:
  `test_input_the_decoder_or_walker_cannot_read_fails_to_parse` and
  `test_an_invalid_source_document_id_raises_even_when_parsing_fails`.
- **The Python pin.** The fixtures record `python_version`, so under any other 3.14.x
  the golden test failed all eight with "regenerate", although the canonical output
  was identical under 3.14.7. `.python-version` now pins 3.14.0, so a bump regenerates
  the fixtures deliberately (PA-14).
- **Two report corrections.**
  - "Post-hoc numbers" above now gives the page artifacts that match no gold anchor.
  - R3.5's report no longer attributes all 14 header texts in no cell to C1 tables.
    Pharmacyclics' C1 tables hold 12 of them, and Southwestern Energy's grid tables
    hold 2.

## V2 disposition, as built

The spec's §V2 disposition gives every one of V2's findings for Stage 3 a
disposition. The table below shows how plan A built the compensated rows. Every other
row stands as the spec records it: either a limitation of `walker-1` or a target of
plan B. This closes the deferred item "Carry V2's findings into Stage 3".

| Finding | Disposition | Evidence |
| --- | --- | --- |
| Tables drawn in `<pre>` are not exposed as tables | C1 | Pharmacyclics' twelve `<pre>` statements are tables (`test_canonical_fixtures.py`) |
| 12 table header texts in Pharmacyclics' `<pre>` tables | C1, without header cells | The re-score's 12/12 falls to 4/12; the limitation `pre_table_without_cells` |
| Known gap: the EDGAR header line is a paragraph | C2 | All eight EDGAR header lines are typed `page_artifact` |
| Page numbers kept as `other`, and W8 also takes four-digit years | C3 | 13 page numbers are retyped, and Ball's two years stay `other` (PA-22) |
| Known gap: "Page N of M" is a paragraph | C4 | Tested, but it fires on no fixture: Southwestern's lines never form whole blocks |
| edgartools decodes with `errors="replace"` | Compensated | `canonicalize` decodes the bytes itself, by the ported rule |
| `walker.parse` raises the global recursion limit | Compensated | The port walks nesting 254 deep at the default limit and leaves the limit unchanged |
| Encoding labels outside the short list use `codecs.lookup` | Limitation | `test_a_label_outside_the_short_list_decodes_by_codecs_not_whatwg` |
| The development set never exercised ten constructs | Exercised | `test_synthetic_constructs_walk_equally`, 11 cases |
| Encoding coverage: every fixture is ASCII | V9 synthetic cases; R3.5 | `test_normalize.py`. R3.5 finds 88 non-ASCII characters, from character references (PA-16). |
| The walker's script header lists beautifulsoup4 | No action | The port imports only lxml |
