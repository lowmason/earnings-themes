# Deferred items

## 2-point-in-time-djia-cohort — 2026-09-22
- [ ] Renumber the two Stage 1 documents for the cohort amendment (plan 2 Task 7,
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
      specs/plans/completed/2-point-in-time-djia-cohort.md, Task 7. Size:
      quick-fix. Done when: Stage 1 execution is paused or its plan is retired,
      both documents are clean in git status, and the renumbering, including the
      reworded forward constraint, has landed.
- [ ] Rename the `stage4_flags` manifest field to `acquisition_flags` (plan 2
      Task 7 Steps 3 and 5, skipped): the field has reached code, in
      `expirements/parser-fidelity/promote_fixtures.py:157`,
      `expirements/parser-fidelity/test_promote_fixtures.py:106-110`
      (`test_stage4_flags`), and eight entries of
      `tests/fixtures/releases/manifest.toml`, as well as both Stage 1 documents,
      so it must change in documents and code together, which a live Stage 1 run
      cannot absorb. Size: quick-fix. Done when: Stage 1 execution is complete and
      the field is renamed in documents, code, test, and manifest in one change,
      or the user records a decision to keep `stage4_flags`.
- [ ] README Stage 1 status is stale on this base (plan 2 whole-plan review,
      Minor): `README.md:140-141` says the investigation harness and fixture
      corpus "have not been created yet", but `expirements/parser-fidelity/` and
      `tests/fixtures/releases/` exist since the Stage 1 commits. Outside plan 2's
      scope, and the paragraph is the user's. Size: quick-fix. Done when: the
      README's Stage 1 paragraph describes the harness and fixture corpus as they
      stand, at the latest when Stage 1 completes.
