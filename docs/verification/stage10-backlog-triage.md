# Completion backlog triage proposal — 2026-10-08

47 open, 34 closed, 42% closure; all 47 open items are 0–14 days old, 0 aged >45 days, oldest 13 days. This is the supplied pre-completion snapshot, not a newly executed stats command.


### Executed deferred statistics

Required developer Python 3.13 ran offline without downloads, exit 0:

```bash
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --no-project --python 3.13 --offline --no-python-downloads python /Users/lowell/.agents/skills/writing-plans/scripts/deferred_stats.py --json
```

Post-completion: **48 open / 35 closed / 83 total**, closure rate **0.4217 (42.17%)**. All 48 open items are 0–14 days old; 15–30, 31–45, 46–90 and 91+ buckets are zero. Aged >45 days and undated open items are zero. Oldest is 13 days (`1-release-parser-fidelity`). With at least 20 open items, the read-only proposal follows these statistics in `docs/verification/stage10-backlog-triage.md`; unrelated dispositions still require human `/deferred` selection. The 47-open baseline is retained distinctly. No aged-tail acknowledgement is needed.

## Original pre-completion read-only proposal

Read-only Steps 1–4 of `/Users/lowell/.agents/skills/writing-plans/references/deferred-backlog.md`. Every current open checkbox appears once below. All locators of the form `specs/deferred_items.md:N` refer to the source section/date printed in its group. Dispositions are proposals for human `/deferred`; none is executed here. No runtime, test, browser, protected reader, gold/draft/example, screenshot or real `data/` access occurred. Live roadmap stages remain outside this triage. Earlier extraction-invariant obligations already ticked closed are not counted again.

| Proposed disposition | Items |
|---|---:|
| Retire | 1 |
| Quick fix | 17 |
| Plan | 8 |
| Design | 6 |
| Hold | 15 |
| Total | 47 |

## Retire (1)

### Browser lifecycle — 5-structure-aware-canonicalization, 2026-09-26

- `specs/deferred_items.md:221` — **Harden the frozen capture adapter**, all three obligations. Concrete source evidence: `packages/earnings-ingestion/src/earnings_ingestion/browser/selenium_capture.py:421` now reads `current_url` inside `_step` with document-load failure handling; `:143` builds an opener with `ProxyHandler({})`; `:161` protects both `Page.getFrameTree` and `Fetch.enable`, closing the socket on startup failure at `:170`. The complete invented lifecycle test source `packages/earnings-ingestion/tests/test_browser_evidence_lifecycle.py:11` parameterizes url/proxy/frame/fetch failures; the relevant checks at `:156`, `:296` and `:327` cover failed outcomes, proxy isolation and cleanup. `expirements/parser-fidelity/layout1-preregistered.toml:30` and `:38` record both approved freeze amendments dated 2026-10-07, expressly preserving comparison inputs/metrics/policy semantics. Path-specific history includes `56225bd`, `981573b`, `7c7f943`. This is source-only evidence of landed repairs and tests, not a claim that this triage ran them; no partial obligation remains in this checkbox.

## Quick fix (17)

### Browser robustness — 5-structure-aware-canonicalization, 2026-09-26

- `specs/deferred_items.md:237` — **Report browser setup ordinary failures in one line**. Keep the recorded small handler change and tests; the recorded second-command trigger is applicable in the expanded application.
- `specs/deferred_items.md:243` — **Three small robustness fixes**. Keep the entire grouped obligation: explicit install failure, screenshot removal before fixture writing, and UTC conversion with the promised script test. No partial retirement.

### Cohort maintenance — 6-point-in-time-djia-cohort, 2026-09-26

- `specs/deferred_items.md:316` — **Four stale claims**. Correct every docstring/README statement or implement the stated host check with its test; retain the group until all four are settled.

### Event/cohort diagnostics and evidence — 7-event-discovery-eligibility-and-acquisition-plan-a, 2026-09-27

- `specs/deferred_items.md:375` — **Cohort override and terms errors as problem lines**. Implement the recorded error boundaries and tests, including verification-record handling.
- `specs/deferred_items.md:387` — **Show operative hashes in verify-live**. Add both operative identities to output and record, with the stated register-only-change test.
- `specs/deferred_items.md:522` — **Cite Item 2.02 for an override outside candidates**. Add the span or refuse build, with the stated test; coordinate the site with the per-candidate evidence plan below.
- `specs/deferred_items.md:589` — **Refuse repeated acknowledgement**. Add the recorded finding-ID uniqueness check and test.

### Acquisition audit and validation — PR #6 review (plan 7), 2026-09-27

- `specs/deferred_items.md:666` — **Bind each evidence citation to artifact retrievals**. Cover URL/source/time and release-index identity, preserving permitted existing records.
- `specs/deferred_items.md:798` — **Cite the index page placing a periodic report**. Implement the explicitly specified optional field, consuming checks, dictionary and synthetic compatibility test.
- `specs/deferred_items.md:814` — **Refuse colliding finding IDs**. Raise the recorded structured build problem before manifest hashing; include CLI coverage.
- `specs/deferred_items.md:854` — **Read companyfacts through the problem-collecting reader**. Share tolerant CIK-checked reads in both named paths and cover continuing other issuers plus handled missing bytes/counts.
- `specs/deferred_items.md:958` — **Refuse repeated fund filings**. Implement the specified accession/pointer refusal and synthetic test, without deduplication.

### Annotation and codebook guards — 9-pilot-codebook-split-and-gold-set-protocol, 2026-10-03

- `specs/deferred_items.md:1100` — **Refuse committed test gold at validate time**. Retain the specified readability gate/test until the explicit later relaxation; this triage authorizes no gold reader.
- `specs/deferred_items.md:1106` — **Constrain codebook freeze ADR path**. Implement the spelled-out repo-relative docs/adr constraint/test before a later freeze.

### Annotation provenance — 10-harden-the-gold-before-bundle-4, 2026-10-03

- `specs/deferred_items.md:1118` — **Take freeze drafting aid from kept draft**. Implement the stated source-of-provenance correction/test without altering approved v0.
- `specs/deferred_items.md:1126` — **Refuse repeated IDs in a kept draft**. Cover both builders and all recorded ID types; maintain rejection accounting.

### Optional dependency collection — 12-evidence-selection-and-verification-plan-b, 2026-10-05

- `specs/deferred_items.md:1252` — **Collect themes tests without httpx**. Use the recorded import-skip remedy or establish the stated isolated-environment result. No such run is claimed here.

## Plan (8), ranked

Ranked by recorded correctness/compatibility dependencies and breadth; there is no aged item to promote. These are future planning proposals, not authorization to execute any later stage.

### 1. Event selection correctness — 7-event-discovery-eligibility-and-acquisition-plan-a, 2026-09-27

- `specs/deferred_items.md:401` — **Write release-id/2**. Highest correctness priority: the full amended obligation covers period patterns, false-drop survivors, override-rule agreement, late releases, preserved v1 loading and prerequisite evidence work. Plan sequencing must honor the explicit user choices and per-candidate citations prerequisite; no pilot document access is proposed here.

### 2. Candidate audit trail — PR #6 review (plan 7), 2026-09-27

- `specs/deferred_items.md:984` — **Cite every candidate's qualifying fields and primary document**. Required before the next event version, and coupled to the outside-candidate override citation; preserve optional-field compatibility and surface the recorded inferred-reading choice rather than silently deciding it.

### 3. Store recovery — PR #6 review (plan 7), 2026-09-27

- `specs/deferred_items.md:829` — **Recover present but unusable saved responses**. A coherent multi-site quarantine/refetch/fsync/remedy plan prevents the recorded permanent failed-closed stop while preserving valid immutable bytes.

### 4. Event CLI robustness — 7-event-discovery-eligibility-and-acquisition-plan-a, 2026-09-27

- `specs/deferred_items.md:461` — **Report events freeze citation errors cleanly**, including all PR-widened obligations. Multi-command loaders, writes, concurrent selection and orphan evidence recovery need sequencing/tests; the earlier partial ValueError handler does not retire the checkbox.

### 5. Historical submissions bounds — PR #6 review (plan 7), 2026-09-27

- `specs/deferred_items.md:701` — **Bind older-page dates and pad page skips**. Preserve the specified temporal-boundary and unchanged-version checks together; correctness at older-page/cutoff boundaries warrants a planned change.

### 6. Stage 6 hardening — 9-pilot-codebook-split-and-gold-set-protocol, 2026-10-03

- `specs/deferred_items.md:1057` — **Stage 6 test/validation gaps**. Keep every residual named branch/contract gap; the explicitly recorded completions from plans 10–12 satisfy only parts of this grouped item. A later plan must land or explicitly drop each remaining obligation; no user-only wording node is delegated here.

### 7. Extraction test hardening — 12-evidence-selection-and-verification-plan-b, 2026-10-05

- `specs/deferred_items.md:1213` — **Close plan 12 test gaps**. A batch plan covers the full recorded validator/prompt/cache/retry/budget/mask/schema/sentinel/injection list; nearby strict-record repairs alone do not discharge the group.

### 8. Canonical cell fidelity — 5-structure-aware-canonicalization, 2026-09-26

- `specs/deferred_items.md:256` — **Separate words split by br in table cells**. Evidence-view use supplies the recorded relevance trigger; size remains Plan because canonical text/policy versioning is required. Preserve frozen text and offsets; do not retrofit wording under existing IDs.

## Design (6), ranked

### 1. Acceptance-time semantics — 7-event-discovery-eligibility-and-acquisition-plan-a, 2026-09-27

- `specs/deferred_items.md:537` — **Bound periodic reports and settle missing acceptance values**. The amended Size is Design until the user selects reading (a) or (b); settle that explicit choice, temporal margins and truthful remedy wording before the implementation/test sequence.

### 2. Cohort temporal semantics — 6-point-in-time-djia-cohort, 2026-09-26

- `specs/deferred_items.md:332` — **Decide override dates**. Decide record-only versus scoped application and overlapping aliases; the dictionary/runtime contract must agree.
- `specs/deferred_items.md:348` — **Decide which dated names match fund holdings**. Coordinate with override semantics so later-cited names and dated overrides use one explicit temporal rule.

### 3. Manifest reproducibility — PR #6 review (plan 7), 2026-09-27

- `specs/deferred_items.md:609` — **Decide event identity after store rebuild**. Citation bytes versus operative decision identity is an explicit version/seed contract choice; keep v1 loadable.

### 4. Shared release unit — PR #6 review (plan 7), 2026-09-27

- `specs/deferred_items.md:972` — **Decide whether issuers share a release**. Although implementation is quick after selection, the recorded user choice (per-issuer/corpus-wide) is still open, so route first to Design with spec/test consequences.

### 5. Host-specific refusal boundary — 6-point-in-time-djia-cohort, 2026-09-26

- `specs/deferred_items.md:362` — **Let verification reach other hosts after refusal**. The recorded AGENTS stop scope is an open protocol decision, requiring agreement and a fake-client test before any live use.

## Hold (15)

### Owner-only hold — 9-pilot-codebook-split-and-gold-set-protocol, 2026-10-03

- `specs/deferred_items.md:1017` — **Remaining train/dev gold bundles**. Only the owner can discharge the protected fresh-session verification/omission/signature workflow. Preserve its source obligation; do not select, draft, inspect or execute it as Stage 10 completion work.

### Frozen measurement watches — 1-release-parser-fidelity, 2026-09-25

- `specs/deferred_items.md:70` — **Parser timings excluding imports**. Hold until a recorded decision relies on speed; frozen Stage 1 evidence is not re-timed merely to tidy the backlog.
- `specs/deferred_items.md:80` — **Exact selection tie comparisons**. Hold until selection-rule reuse; preserve the original scored record.
- `specs/deferred_items.md:89` — **Scrub identity from lock-gate adapters**. Hold until the lock gate is run again; no credential/environment inspection here.

### Capture regeneration — 5-structure-aware-canonicalization, 2026-09-26

- `specs/deferred_items.md:209` — **Machine paths in committed captures**. Hold until regeneration/new pin/policy; the renderer lifecycle repairs do not establish that existing captures were regenerated or sanitized.

### State diagnostic watch — 9-pilot-codebook-split-and-gold-set-protocol, 2026-10-03

- `specs/deferred_items.md:1110` — **Raw error text in Stage 6/pilot commands**. Hold until free text enters those state/pilot inputs; no invented trigger or broad cleanup is assumed.

### Frozen helpers and later orchestration — 12-evidence-selection-and-verification-plan-b, 2026-10-05

- `specs/deferred_items.md:1155` — **Share verification/test helper definitions**. Blocked on anchoring's recorded freeze lifting; retain every repeated pair and unchanged-suite condition.
- `specs/deferred_items.md:1184` — **Concurrent cache/store safety**. The explicit closure depends on Stage 15 orchestration/workers; preserve pickling, partial-name collisions, cached flag, rename failure type and mode documentation as later obligations.

### Conditional isolation and diagnostic watches — 12-evidence-selection-and-verification-plan-b, 2026-10-05

- `specs/deferred_items.md:1195` — **Widen socket guard**. Hold until a default test needs stronger isolation or another socket route appears; recorded limited protection remains explicit.
- `specs/deferred_items.md:1204` — **Harden import scans**. Hold until relative source imports appear, as recorded; keep all path/floor/client-list obligations together.
- `specs/deferred_items.md:1231` — **Non-AdapterError partial-run survival**. Hold until the recorded need for a partial record arises; that trigger would initiate the explicitly recorded Design/schema decision, not an automatic patch.
- `specs/deferred_items.md:1243` — **Python wording guard**. Hold until synthetic/test strings derive from release text; any future protocol design and user-only wording check stays outside this task.
- `specs/deferred_items.md:1261` — **Refused map-key field paths**. Hold until model/release text may enter a map key or Stage 6 freeze lifts; current consuming safety does not itself prove this older grouped path retired.
- `specs/deferred_items.md:1270` — **Live-test failure diagnostics**. Hold until a live test runs over protected pilot text; this task authorizes no such run.
- `specs/deferred_items.md:1277` — **Transcript block rule**. Hold until transcripts introduce the recorded speaker-turn/section block trigger; preserve future Design ownership, not transcript execution here.

## Limits and selection boundary

The source backlog was read completely in numbered ranges through line 1285, including all widened obligations. Source files were opened only to substantiate the renderer retirement; its adapter, lifecycle test and preregistration record were read completely, with path-specific history. No unrelated merit review was performed. Conditional Holds reflect the recorded unsatisfied/external triggers; this pass does not prove global absence of every possible trigger. No checkbox, tracked source, codebook, split, gold or roadmap is changed by this report. Task 12 may reconcile the supported renderer retirement; all other dispositions await human `/deferred` selection. This report is preparation, not code review or completion approval.

## Completion reconciliation — 2026-10-08

The table and all 47 locators above preserve the pre-change proposal and its source dates. Task 12 executed only the supported frozen-adapter retirement: every one of its three obligations, tests and approved amendments landed. The other 46 original open items remain unchanged; their Quick fix/Plan/Design/Hold dispositions are proposals for human `/deferred`, not execution. The extraction-invariant item was already closed and is not recounted.

Two authorized nonblocking Plan follow-ups are now recorded under plan 15 (2026-10-08) in `specs/deferred_items.md`: **P15-M1**, typed workflow phases/results in `apps/earnings-pipeline/src/earnings_pipeline/theme_workflow.py`, triggered by next authorized workflow maintenance; **P15-M2**, consistent typed optional-material fixture result/named seeding helpers in `tests/integration/stage10_cases.py`, triggered by next authorized fixture maintenance. Their full scope and Done when conditions remain in that source section; neither is a Stage 11 prerequisite. The current open proposal therefore contains 17 Quick fix, 10 Plan, 6 Design and 15 Hold items (48 total), with the sole Retire proposal implemented. Actual post-completion statistics are recorded above. No unrelated disposition, deletion or rewrite is authorized; aged >45 days is zero, so no aged-tail acknowledgement is invented.
