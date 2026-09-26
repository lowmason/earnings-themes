# 0002. Keep the browser capture diagnostic-only

- **Status:** Accepted
- **Date:** 2026-09-26
- **Deciders:** Lowell Mason
- **Blast radius:** the canonicalization version of every release document, and every
  stage that binds to a `doc_id`: Stages 5, 6, 7, 10 and 15.

## Context

What was known on 2026-09-26, when Stage 3's plan B
(`specs/plans/5-structure-aware-canonicalization.md`) finished its pre-registered
comparison (`docs/verification/layout-1-comparison.md`):

- **The question.** The browser spec's diagnostic-first promotion rule keeps
  browser-derived structure diagnostic. It changes only when a Stage 3 decision
  record shows that the structure repairs named residual failures under a
  predeclared rule, without violating the element and span invariants. This ADR is
  that record (Stage 3 spec, §Promotion decision).
- **The base.** `walker-1`, from ADR 0001 and plan 4: the ported lxml walker with
  C1–C5. Its eight canonical fixtures are committed.
- **The candidate.** `layout-1` reads the pinned browser's rendering:
  - Chrome for Testing and chromedriver 154.0.8037.57, with Selenium 4.49.0;
  - capture policy `isolated/1`, with layout metadata `layout-metadata-1`.

  Its blocks pass through the same C1–C5 and map onto `walker-1`'s canonical text
  under `anchored-1`. It never changes canonical text (SC14).
- **The pre-registration.** Before any release was captured, commit
  `cdc77b87bd94` fixed the units, the rules, and the 23 files that decide the numbers.
  No post-freeze fix was needed. One unfrozen check,
  `tests/integration/test_browser_fixtures.py`, had its unit accounting corrected
  after capture, with the user's approval, and no number in the comparison depends
  on it; `docs/verification/layout-1.md` records it. Plan 5's PB-13 discloses what the
  planner saw before the freeze.
- **The targeted classes.** Units lost, for `walker-1`, `layout-1` and the fallback,
  from the report's "Targeted classes":
  1. headings typed `paragraph` by W12: of 23 units, 23, 14 and 21;
  2. prose inside data tables: of 38 units, 38, 32 and 32;
  3. content hidden by stylesheets: no units, because no fixture carries a
     stylesheet.
- **Regressions,** from the report's Verdict:
  - `layout-1`: 0;
  - the fallback: 0.
- **Alignment.** `layout-1` placed all 4,884 of its units over the eight fixtures as
  exact spans, with 0 alignment failures.
- **What the rule allows.** Every outcome: 1 (diagnostic-only capture); 2 (the
  fallback, as `walker-2`); 3 (`layout-1` for every document).
- **Development-set numbers.** The fixtures were Stage 1's test set, and the classes
  were named from V2's residual failures on them (SC2). The comparison is not an
  independent validation (R12.2).
- **The cost of promotion.** Any promotion makes a browser capture an input to
  canonicalization for every document the new version covers, Stage 5's and Stage
  15's releases included. layout-1's geometry needs the pinned platform and font set.

## Decision

**Outcome 1: diagnostic-only capture.** `walker-1` stays the canonicalization policy
for every document. The browser capture, `layout-1` and `anchored-1` stay diagnostic:
nothing they produce enters a canonical document. Lowell Mason chose this outcome at
the gate, adopting the recommendation given there, which rested on four points:

- **The consumer's gain is small.** Stage 7 is the stage that needs the repair: R4.2
  keeps table cells out of narrative extraction. Promotion recovers 6 of the 38
  prose-in-table units, in 2 of the 8 documents.
- **Its cost falls on every document.** Every Stage 5 and Stage 15 release would need
  a pinned-platform capture before canonicalizing, and would fail without one.
- **The evidence is thin.** It is eight development-set documents. Six of the seven
  heading units that `layout-1` recovers beyond the fallback lie in one 2008 `<pre>`
  release, where the report's probe also shows `layout-1` typing the `###` end mark
  as a heading.
- **Deferring is cheap.** Canonical text and hashes are identical under every
  outcome, and the comparison can be repeated under a new pre-registration on
  Stage 5's pilot releases.

## Consequences

- **Positive.**
  - No capture is an input to canonicalization, so Stages 5 and 15 need no browser.
  - `walker-1`'s `doc_id`s stand, and Stage 6 annotation may begin on them.
- **Negative.**
  - The targeted classes' losses stay as `walker-1` has them.
  - The review gate's findings are limitations of `walker-1` and `boilerplate/1`,
    recorded in `docs/verification/layout-1.md`.
- **Neutral / follow-on.**
  - Stage 10 receives `BrowserRenderer` for V5's target-browser checks and its
    screenshot fallback.
  - The committed captures, `layout-1` and the comparison stay available for a later
    evaluation, such as one on Stage 5's pilot releases.

## Alternatives considered

- **Outcome 2, the fallback as `walker-2`.** The rule allowed it. It repaired classes
  1 and 2, cutting units lost from 23 to 21 and from 38 to 32, with no regression, by
  switching the two documents where `prose_row` fires: Southwest Airlines and
  National Health Investors. Not chosen, because its capture dependency covers every
  document, switched or not, for a gain in 2 of 8.
- **Outcome 3, `layout-1` for every document as `walker-2`.** The rule allowed it. It
  repaired classes 1 and 2, cutting units lost from 23 to 14 and from 38 to 32, with
  no regression, and cut narrative-only heading loss from 9/16 to 2/16. Not chosen,
  because it carries the same capture dependency, and most of its margin over
  outcome 2 lies in one release.

## Trade-offs & reversibility

- **Canonical text never changed.** Every outcome keeps `walker-1`'s text, so offsets
  and hashes carry over. A later reversal changes elements only, under a new version.
- **What would trigger a superseding ADR:**
  - the R12.2 validation set, or Stage 5's pilot releases, showing different results;
  - a change of browser, platform or font set, which needs a new capture policy
    version and a new comparison;
  - a layout extractor that repairs a targeted class with no regression under a new
    pre-registration.
