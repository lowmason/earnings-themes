# Task 5 report

Status: DONE, implementation committed at `5b9ea8a48539c6635e38bca186470915966f769a` (`feat: project verified analytical rows and disclosure copies`). This is the committed implementation HEAD at report creation; the report is committed separately so it can name that immutable implementation. Overall review BASE remains `6c1c541f0dff00e6010e98cfd8cfc873e43abaa1`. Preserved controller clarification commit `feab7748ef0eeb1a924b0279519df4bd92bb0189`.

## Implementation and interfaces

Added public `build_observations(bound: BoundAnalysis) -> AnalysisTables`. It rebinds through the current extraction/support/coding/canonical/mask/provenance/policy/snapshot/cache gates, compares the binding hash, and uses freshly checked inventories rather than trusting prior decisions in a bound wrapper. It projects fourteen exact Polars schemas. The four later-stage frames (completions, coverage, prevalence, evidence) remain typed and empty; no empty result implies a negative theme observation.

The observation grain is the declared issuer/period/type/role/theme/document/quote/book-version grain. Two accepted themes for one quote produce two observations; two supporting claims do not multiply that grain. The regression has two observations and four assignment-claim links. Every original claim–quote and original assignment–claim–decision–target link remains document-qualified and unchanged. Equal local quote IDs across documents remain separate evidence. Original classification, decision, novelty and refusal outcomes survive even when there are zero assignments.

All retained quote text is a fresh canonical code-point slice. Current mask overlaps retain audit evidence and exclude it through `headline_eligible=false`. Release role is `not_applicable`. Theme IDs come only from checked Stage 9 assignments, never sentiment/topic/event/cluster attributes. Local retention permissions withhold both canonical text and model-derived interpretation while keeping hashes and IDs. Metadata digests retain the current complete source/rights/time bindings. The dictionary defines the full coding-run digest, interpretation hash, evidence-ID formula and extraction-time meaning.

Copies group only within one event/issuer/period/type, by exact canonical hash or a current hash-bound explicit assertion. All source records and original evidence IDs survive; copy-row, disclosure-group and span-occurrence counts are separate units. The group digest binds every sorted member metadata row and the complete sorted assertion inventory. Each document has one copy row with its first sorted applicable original assertion pointer and hash; all supplied assertions remain in checked inputs and their group digest. Representatives are deterministic. Outcomes/evidence disagreement marks every group member `copy_processing_conflict`, retaining all rows. Fingerprints compare acquisition state, extraction completeness/windows/refusals, actual quote occurrences, masks, claim multiplicity, classifications and decisions; score/rationale-only variation is not a processing disagreement. Downstream Task 6 must exclude unresolved groups from observation denominators. Reviewed unequal canonical hashes retain hash-qualified occurrence identity.

## Approved compatibility resolution

Before edits/runtime, reported the upstream nullable refusal-window and absent upstream attempt-ID blockers. The controller documented and committed their resolution before implementation resumed. Changed only `RejectionAudit.window_id` to `NonBlank | None`; analytical schema 1, its Polars string dtype and row grain are unchanged, and no analytical schema-1 artifact has yet been published. Claims use derived `a-{window_id}-{attempt}` pointers scoped by source run/document. Refusals without an original attempt retain null pointers. The actual upstream stored-run gate requires null attempt and candidate index whenever window is absent, so the reported attempt-without-window contingency is excluded by that gate. Refusals copy closed reasons/subject IDs and only current element IDs, never labels, detail or source-bearing core rejection strings.

## Audit and safety

Read the task brief, full unchanged Global Constraints/GS13 and approved C1/C2 decisions; the controller resolution; root instructions, README, workspace/member pyprojects and source notes; owning contracts/gates and downstream dictionary contracts; the implementer prompt; and test-driven-development, clean-code, clean-coder and verification-before-completion guidance. No nearer AGENTS file or configured type checker was found; README states no CI configuration exists.

Audited new test imports and the shared analysis cases/conftest, their coding-case helpers, extraction/support/coding public run/cache/store readers, themes conftest and synthetic fixture construction. Readers select invented temporary run/cache artifacts, committed prompts or permitted Stage 1 fixtures; the used codebook fixture constructs synthetic inputs only and dereferences no pilot examples. Audited consume/records/dictionary allowlisted files, their imports/fixtures/readers and runner metadata boundary before execution. Registered only exact `test_rows.py` and `test_safe_output.py` nodes for `rows`. Added tests use actual generated/round-tripped upstream runs and explicit invented policies, not mocked acceptance. The byte-hash regression reads only three exact `run.json` files in its own freshly created invented temporary root. The no-I/O test prohibits Path readers during projection with caches absent. Socket guards remain active for invented run generation.

No protected pilot text, signed gold, drafts, views, real data directory, codebook example pointers, wording gate, human mode, full-root suite, browser, SEC request, hosted inference, real model, model download, credential or network access was used. No additional agent/runtime worker was launched. No dependency/lockfile, upstream extraction/support/coding module, plan, source note, frozen artifact or unrelated file was edited. Raw/canonical snapshot payloads are never projected into analytical frames. Diagnostics are closed reasons with suppressed exception chains; guarded test results expose only counts/validated IDs.

## TDD and checks actually observed

All pytest executions used this exact command form from the owned worktree:

```text
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py GROUP
```

RED, before library implementation:

- `GROUP=rows`: exit 1; 13 failed, 2 passed; zero collection failures/warnings. The public projection was absent. Two unsupported-contribution cases additionally exposed an invented fixture-policy setup problem (empty evidence offered to an accept vote); the fixture now takes an explicit hash-bound reject/review action rather than weakening any current gate.
- `GROUP=records`: exit 1; 1 failed, 59 passed; zero collection failures/warnings. The targeted document-level refusal could not retain a null window under the old analytical field.

Intermediate guarded checks retained safe failure metadata only. A later irrelevant-contribution assertion incorrectly assumed every upstream result was rejected; the real semantic safety layer can flag/review it. Corrected the assertion to compare the original upstream outcomes exactly. No production gate was weakened. Added focused exact-original-link, immutable-manifest-byte, attribute isolation, zero-extraction and closed-policy-exception regressions before final verification.

Final GREEN:

| Group | Passed | Failed | Collection failures | Warnings | Skips |
| --- | ---: | ---: | ---: | ---: | ---: |
| rows | 24 | 0 | 0 | 0 | 0 |
| consume | 93 | 0 | 0 | 0 | 0 |
| records | 61 | 0 | 0 | 0 | 0 |
| dictionary | 301 | 0 | 0 | 0 | 0 |

Final Ruff commands, both exit 0:

```text
RUFF_CACHE_DIR=/private/tmp/earnings-stage10-ruff UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync ruff check packages apps tests tools
RUFF_CACHE_DIR=/private/tmp/earnings-stage10-ruff UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync ruff format --check packages apps tests tools
```

Lint: all checks passed. Format: 340 files already formatted. `git diff --check`: exit 0. An initial Ruff invocation could not create its worktree cache under the filesystem sandbox; moved only Ruff's cache to the explicit temporary path above, then observed successful scoped checks. No network/dependency change or raw pytest diagnostic fallback was used.

## Files changed

- `packages/earnings-themes/src/earnings_themes/analysis/rows.py`: pure checked projection, full original/audit rows and disclosure groups/conflicts.
- `packages/earnings-themes/src/earnings_themes/analysis/__init__.py`: minimal public export.
- `packages/earnings-themes/src/earnings_themes/analysis/records.py`: only the approved nullable refusal window.
- `packages/earnings-themes/tests/analysis/test_rows.py`: invented projection/grain/link/copy/outcome/rights/staleness/mixed-version/no-I/O/hash regressions.
- `packages/earnings-themes/tests/analysis/test_records.py`: targeted nullable refusal model/table round trip.
- `packages/earnings-themes/tests/analysis/test_safe_output.py`: row-specific policy exception regression.
- `packages/earnings-themes/tests/analysis/cases.py`: narrow optional invented masks, per-document themes/text/event assignment, explicit action, retention and classifier-reply fixture extensions; existing defaults preserved.
- `docs/data-dictionary.md`: public interface, derived pointers/nullability, hash/rights/copy/conflict semantics.
- `tests/contracts/test_data_dictionary.py`: exact interface/nullability documentation regression.
- `tools/stage10_checks.py`: exact rows-node registration only.
- This report.

## Self-review, limits and handoff

Reviewed the full new source and diff, exact ownership, schema/grains/FKs, current gate call, every original link, rejection privacy, copy unit restrictions, rights filtering, deterministic hashing and intermediate/final validation boundary. Regression verifies unchanged upstream row hashes and source/support/coding manifest byte hashes. No unresolved implementation blocker was found.

Applied clean-code rules: G30/G34, cohesive copy grouping, quote projection, original audit projection and orchestration helpers within the assigned rows module; N1/N4, names identify their analytical units and document-qualified inventories; T1/T5/T6, tests cover empty/unmatched/review/refused/incomplete, repeated text, duplicate copies, masked evidence, stale/mixed inputs and the reported nullable-boundary defect. No adjacent cleanup or separate tidying was performed.

This is Task 5 only. It does not implement completion proof, denominators/prevalence, publication views/export, production policies or pilot extraction. Typed intermediate tables intentionally defer only the observation-to-completion FK while completions are empty. Future completion/serialization/publication must invoke the final FK gate and current consuming/publication gates, preserve the complete checked metadata/assertion inventory and reuse the dictionary's hash/ID meanings. Acceptance remains visibly fixture-scoped. Protected/user-only gates remain unrun and no pilot accuracy, stability or full-cohort completeness is claimed. Ready for the controller's sequential fresh spec and quality reviews, with Ultra review at the shared nullable-contract boundary.
