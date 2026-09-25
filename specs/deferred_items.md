# Deferred items

## browser-rendering-integration — 2026-09-24

- [ ] When Stage 1 is ticked complete in
      `specs/evidence-linked-theme-extraction-roadmap.md`, surface the approved
      `specs/browser-rendering-integration.md` design before Stage 2 planning.
      Stage 2 plans only the browser-neutral core contracts and tests; Stage 3
      owns Selenium capture, rendered-text calibration, DOM/layout extraction,
      and the diagnostic-first promotion decision; Stage 10 consumes the public
      renderer and canonical-span artifacts for cited evidence views. Do not add
      browser automation to Stage 1 or make it a dependency of `earnings-core`
      or `earnings-themes`. Size: cross-stage planning reminder. Done when the
      Stage 2 plan incorporates its assigned contract work and leaves explicit
      handoffs for the Stage 3 brainstorming pass and Stage 10 plan.

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
- [ ] README Stage 1 status is stale on this base (plan 2 whole-plan review,
      Minor): `README.md:140-141` says the investigation harness and fixture
      corpus "have not been created yet", but `expirements/parser-fidelity/` and
      `tests/fixtures/releases/` exist since the Stage 1 commits. Outside plan 2's
      scope, and the paragraph is the user's. Size: quick-fix. Done when: the
      README's Stage 1 paragraph describes the harness and fixture corpus as they
      stand, at the latest when Stage 1 completes.

## 3-employment-statistics-coverage — 2026-09-24
- [ ] Review: the national-total employment comparison in `check_invariants`
      (scripts/employment_statistics_coverage.py) has no rounding allowance, so
      annual-average rounding (+46 in 2022, +27 in 2023) makes `run` exit 2 on the
      2022–2025 files. Kept as-is under the 2026-09-24 ruling (no re-run, no code
      change); evidence in specs/findings/employment-statistics-coverage.md,
      section 6. Fix: give that comparison the `cells/2 + 1` employment allowance
      that `_nested_excess` already applies, plus a fixture test. Size: quick-fix.
      Done when: `run` on the 2022–2025 files reports no invariant failure and a
      test pins the allowance.

## 1-release-parser-fidelity — 2026-09-25
- [ ] Carry V2's findings into Stage 3: V2's "Residual failures (for Stage 3)"
      and "Findings for Stage 3" (`docs/verification/V2-parser-fidelity.md`) and
      ADR 0001's Consequences list what the walker leaves to the canonicalizer:
      split, merged and header-lost blocks by fixture, body text typed as
      headings (12 of 313 found body blocks), the eight Known gaps in
      `expirements/parser-fidelity/walker-rules.md`, W11's and W15's side
      effects, page numbers kept as `other`, and a script header that lists
      beautifulsoup4, which the walker never imports. The roadmap's Stage 3 entry
      consumes only "Stage 1 parser decision and fixtures", so these could be
      missed. Size: plan. Done when: the Stage 3 spec or plan compensates for or
      records each of V2's findings for Stage 3.
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
