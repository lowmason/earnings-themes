# Point-in-Time DJIA Cohort Amendment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

> **This plan implements no roadmap stage.** It amends the roadmap and its parent
> spec so the cohort stage becomes plannable. Tick no stage; append no COMPLETE
> stamp. `specs/point-in-time-djia-cohort.md` §Roadmap amendment: "No stage is
> marked complete by adopting this specification."

**Goal:** Carry out the amendment that `specs/point-in-time-djia-cohort.md`
requires — renumber the roadmap to sixteen stages, insert Stage 4 (point-in-time
DJIA cohort) and Stage 15 (full DJIA eight-quarter run) as fully-specified
entries routed to `writing-plans`, reconcile the stages the cohort changes, and
update every downstream reference in the parent spec, `README.md`, `CLAUDE.md`,
and the Stage 1 plan.

**Architecture:** Documentation only. Five Markdown files change; no Python, no
dependency, no `uv.lock` edit. Each task ends in a `grep` whose expected output is
written out, and the final task runs a cross-file sweep asserting every `Stage N`
mention in the repository resolves to a title in the sixteen-stage list. That
sweep is this plan's acceptance test.

**Tech Stack:** Markdown, `git`, and BSD `sed`/`grep`/`awk` as shipped on macOS
(Darwin 25.6.0, zsh). Note BSD `sed` requires `-i ''`; GNU `sed` uses plain `-i`.

## Global Constraints

Every task's requirements include these.

**Locators.** `A §n` is `AGENTS.md` by line-section. `Rn`/`Vn` are
`specs/evidence-linked-theme-extraction.md`. `Dn` are the roadmap's recorded user
decisions. **`P` is `specs/point-in-time-djia-cohort.md`** — a locator this plan
introduces: `P-C1`–`P-C7` are its Decisions table rows, `P-A4`/`P-A5`/`P-A15` its
three Acceptance-criteria groups, `P-VF`/`P-VI`/`P-VL` its deterministic-fixture,
offline-integration, and optional-live verification groups, and `P §Section`
cites a section by name.

**Values copied verbatim from `P`; never paraphrase or round these.**

- Analytical window: calendar period ends `2024Q3` through `2026Q2`, the half-open
  interval `[2024-07-01, 2026-07-01)` (`P-C3`).
- Public-information cutoff: the date `2026-09-22` (`P-C4`).
- Membership reference: `first_publication_time` (`P-C2`).
- Pilot target: **40** expected issuer-events (`P-C5`).
- Full-run shape: the observed count "is not forced to equal `30 × 8`" (`P-C6`).
- CIK: a 10-character zero-padded string (`P §Acceptance criteria`).
- Universe name: `djia`.

**Do not edit `AGENTS.md`.** It is cited by line number throughout the parent
spec and roadmap (`CLAUDE.md` §Gotchas; highest cited line 780). This amendment
needs no `AGENTS.md` change: `P §Roadmap amendment` names only the parent spec,
the roadmap, and the README. If a future reviewer wants an `AGENTS.md` pointer,
it must be **appended to an existing line**, never inserted as a new one.

**Line insertions in the other files are safe.** Verified: no file cites
`specs/evidence-linked-theme-extraction.md`, the roadmap, or `CLAUDE.md` by line
number.

**No stage is ticked.** Every roadmap checkbox stays `- [ ]`. No `COMPLETE` stamp
is appended anywhere.

**Tests were not run.** This is an instruction-only change. Per
`specs/evidence-linked-theme-extraction.md` §Rollout and `CLAUDE.md`
§Conventions, the completion report must state that application tests and live
extraction were not run. Do not run `pytest` to "verify" this plan — there is no
pytest configuration yet (that is Stage 2's deliverable) and no code changed.

**Ruff still applies.** `[tool.ruff] extend-exclude = ["*.md"]` means Ruff will
not reformat these files, but run `uv run --locked ruff check .` and
`uv run --locked ruff format --check .` once in the final task to confirm nothing
regressed.

**Commit attribution.** End each commit message with the attribution line your
session's instructions specify. The commit blocks below omit it deliberately —
the correct line names the model actually executing the work.

---

## Working-tree preconditions — read before Task 1

**Stage 1 is being executed on `stage-1-release-parser-fidelity` while this plan
was being written.** Sixteen commits landed on that branch during the planning
session, building the parser-fidelity harness under `expirements/parser-fidelity/`,
and `specs/plans/1-release-parser-fidelity.md` now carries uncommitted tick marks
from that execution. Treat every path below as live.

Re-run this before Task 1 and read the result, rather than trusting the numbers
here:

```bash
cd /Users/lowell/Projects/earnings-themes
git branch --show-current
git log --oneline -5
git status --short
```

What the amendment expects, and what to do if it differs:

| Path | Expected at planning time | If it differs |
| --- | --- | --- |
| `README.md` | tracked, **empty in HEAD**, ~269 uncommitted lines | if already committed, skip its baseline commit in Task 1 Step 2 |
| `specs/plans/2-point-in-time-djia-cohort.md` | untracked — this file | if committed, skip its baseline commit |
| `specs/plans/1-release-parser-fidelity.md` | **tracked and modified** by live Stage 1 execution | see the hazard below |
| `specs/release-parser-fidelity.md` | tracked, clean | see the hazard below |
| `expirements/parser-fidelity/` | Stage 1 work in progress, partly untracked | leave it alone entirely |

**The Task 7 hazard.** Task 7 edits the two Stage 1 documents, and a concurrent
session is writing one of them. Running a `sed` over a file another agent is
mid-edit loses work. Therefore:

- **Confirm Stage 1 execution is paused or finished before running Task 7.** If it
  is still in flight, do Tasks 1–6, 8, and 9 and stop; report Task 7 as blocked on
  Stage 1 execution, and defer it with `Done when: Stage 1 execution is paused or
  its plan is retired, and the two documents are clean in git status`.
- Tasks 1–6 and 8 touch no file Stage 1 execution uses, so they are safe to run
  concurrently.
- Task 9's sweep will report the stale Stage 4/5 references in those two documents
  until Task 7 runs. That is an expected, recorded gap, not a failure.

**Branch handling.** `git switch -c` from the current HEAD carries the uncommitted
`README.md` and this plan with it. Two consequences:

1. **Do not discard this branch** — it will be the only place the README and this
   plan are committed. Integrate it via `finishing-a-development-branch`.
2. Because Stage 1 execution continues on `stage-1-release-parser-fidelity`, the
   two branches will both need integrating. Merge order does not matter for
   correctness here — the amendment touches the roadmap, the parent spec, the
   README, and `CLAUDE.md`, none of which Stage 1 execution writes — but if
   Task 7 ran, expect to resolve its two documents by hand.

---

### Task 1: Branch, commit the baseline, and renumber the existing stages

Renumbering is mechanical and comes first so that later tasks insert into a
correctly-numbered file. Old Stages 4–13 become 5–14; old Stage 14 becomes 16;
4 and 15 are deliberately left empty for Task 2.

| Old | New | Title (unchanged in this task) |
| --- | --- | --- |
| 4 | 5 | Acquisition and event resolution |
| 5 | 6 | Pilot codebook and gold-set protocol |
| 6 | 7 | Evidence selection and verification |
| 7 | 8 | Semantic support assessment |
| 8 | 9 | Deductive coding |
| 9 | 10 | Coverage-aware aggregation and cited export (theme vertical slice) |
| 10 | 11 | Feasibility pilot and threshold calibration |
| 11 | 12 | Inductive and hybrid codebook |
| 12 | 13 | Transcript extension (conditional on V7) |
| 13 | 14 | Configuration comparison and held-out evaluation |
| 14 | 16 | Hosted quality ceiling (optional) |

**Files:**
- Modify: `specs/evidence-linked-theme-extraction-roadmap.md` (stage entries at
  lines 141–240; the R14.2 gap note at line 87; the stamp list at line 253; the
  Completion note at line 274)
- Commit (baseline only, unmodified): `README.md`,
  `specs/plans/1-release-parser-fidelity.md`

**Interfaces:**
- Consumes: nothing.
- Produces: a roadmap whose `- [ ] Stage N:` headings read
  `1,2,3,5,6,7,8,9,10,11,12,13,14,16` — the 4 and 15 gaps Task 2 fills.

- [ ] **Step 1: Create the branch**

```bash
cd /Users/lowell/Projects/earnings-themes
git switch -c cohort-amendment
git status --short
```

Expected: `?? specs/plans/` and ` M README.md`, unchanged by the switch.

- [ ] **Step 2: Commit the baseline artifacts**

Two commits, because these are two unrelated pre-existing deliverables. No file
is edited here.

**Do not stage `specs/plans/1-release-parser-fidelity.md`.** It is already
tracked, and its uncommitted changes belong to the live Stage 1 execution — they
are that session's to commit, not this one's. `git add README.md` and
`git add specs/plans/2-...` name their files explicitly for exactly this reason:
never `git add -A` in this task.

```bash
git add README.md
git commit -m "docs: add the repository README

Commits the README written in the working tree, previously unrecorded (README.md
is empty in HEAD). No content change; the cohort amendment edits it next."

git add specs/plans/2-point-in-time-djia-cohort.md
git commit -m "docs(specs): add the cohort amendment plan

The plan this branch executes, written by writing-plans against
specs/point-in-time-djia-cohort.md. Committed first so the amendment commits that
follow can be read against it."
```

Neither commit changes a byte of content — they only record what was already in
the working tree.

- [ ] **Step 3: Write the failing check**

Before editing, confirm the file is in the pre-amendment state.

Run:

```bash
grep -c "^- \[ \] Stage " specs/evidence-linked-theme-extraction-roadmap.md
grep -n "^- \[ \] Stage 14:" specs/evidence-linked-theme-extraction-roadmap.md
grep -n "^- \[ \] Stage 16:" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected:
```
14
231:- [ ] Stage 14: Hosted quality ceiling (optional)
```
and the third `grep` prints nothing and exits 1 — Stage 16 does not exist yet.
That absence is the failing condition this task fixes.

- [ ] **Step 4: Renumber every single-number `Stage N` reference**

Descending order matters: each rule's output is higher than every later rule's
input, so no line is renumbered twice in one pass. Ascending order would cascade
4→5→6→7 and corrupt the file.

```bash
sed -i '' \
  -e 's/Stage 14/Stage 16/g' \
  -e 's/Stage 13/Stage 14/g' \
  -e 's/Stage 12/Stage 13/g' \
  -e 's/Stage 11/Stage 12/g' \
  -e 's/Stage 10/Stage 11/g' \
  -e 's/Stage 9/Stage 10/g' \
  -e 's/Stage 8/Stage 9/g' \
  -e 's/Stage 7/Stage 8/g' \
  -e 's/Stage 6/Stage 7/g' \
  -e 's/Stage 5/Stage 6/g' \
  -e 's/Stage 4/Stage 5/g' \
  specs/evidence-linked-theme-extraction-roadmap.md
```

On GNU `sed`, drop the `''` after `-i`.

This is safe against near-misses: `Stage 14` does not contain the substring
`Stage 4` (it contains `Stage 1` followed by `4`), and no rule sources `Stage 1`,
`Stage 2`, `Stage 3`, `Stage 15`, or `Stage 16`. It does **not** touch `R14.2`,
`A §391–427`, or `V7`, none of which contain the word `Stage`.

- [ ] **Step 5: Fix the four plural-`Stages` references by hand**

`sed` reached none of these. The pattern `Stage 6` does not match the string
`Stages 6–9` — after `Stage` comes `s`, not a space — so every line using the
plural form survived Step 4 unchanged. Verified by dry run; do not assume
otherwise.

Replace (in the entry now headed `Stage 6: Pilot codebook and gold-set
protocol`, Objective line):

```text
so hand-coding runs while Stages 6–9 are built.
```

With:

```text
so hand-coding runs while Stages 7–10 are built.
```

> Old 6–9 = new 7–10. Task 3 replaces this entry wholesale and repeats the same
> value; fixing it here keeps Task 1's file correct on its own.

Replace (in the entry now headed `Stage 10: Coverage-aware aggregation and cited
export`, Consumes line):

```text
Consumes: Stage 3 canonical documents and masks; Stage 5 processing-state table; Stages 6–8 verified, supported, coded assignments.
```

With:

```text
Consumes: Stage 3 canonical documents and masks; Stage 5 processing-state table; Stages 7–9 verified, supported, coded assignments.
```

> The `Stage 5 processing-state table` half was already correct — `Stage 4`
> singular did match in Step 4. Only the plural range needs changing.

Replace (in the entry now headed `Stage 13: Transcript extension`, Consumes
line):

```text
      Consumes: Stages 3 and 4; Stage 10 aggregation; Stage 11 metrics.
```

With:

```text
      Consumes: Stages 3 and 5; Stage 10 aggregation; Stage 11 metrics.
```

> **The highest-risk line in the task.** Left unfixed it points transcripts at
> the cohort stage instead of acquisition — a silent coupling to the wrong
> dependency, which is exactly the class of error this plan exists to prevent.

Replace (in the `## Stage-spec stamp` section):

```text
A stage routed straight to writing-plans (Stages 2, 8, 9, 13, 14) has no stage
```

With:

```text
A stage routed straight to writing-plans (Stages 2, 9, 10, 14, 16) has no stage
```

> Old 8, 9, 13, 14 → new 9, 10, 14, 16; Stage 2 is unchanged. Task 2 adds the
> new stages to this list.

- [ ] **Step 6: Verify the renumber**

Run:

```bash
grep -n "^- \[ \] Stage " specs/evidence-linked-theme-extraction-roadmap.md \
  | sed 's/.*Stage \([0-9]*\).*/\1/' | paste -sd, -
```

Expected: `1,2,3,5,6,7,8,9,10,11,12,13,14,16`

Run:

```bash
grep -n "not Stage" specs/evidence-linked-theme-extraction-roadmap.md
grep -n "Optional Stage" specs/evidence-linked-theme-extraction-roadmap.md
grep -n "parks if V7\|is optional$" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected (line numbers may differ by a line or two):
```
163:      Consumes: Stage 2 validator and locators; Stage 3 canonical fixtures only — not Stage 5.
87:| R14.2 | missing | none found¹ | Optional Stage 16 (D3) |
274:- **Stage 13** parks if V7 finds no qualifying corpus; **Stage 16** is optional.
```

Then confirm all four plural-`Stages` lines from Step 5 landed:

```bash
grep -n "Stages" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected exactly five lines — the `## Stages` heading plus the four fixed
references, with no `Stages 6–9`, `Stages 6–8`, `Stages 3 and 4`, or
`Stages 2, 8` surviving:
```
112:## Stages
151:      Objective: ... so hand-coding runs while Stages 7–10 are built.
190:      Consumes: ... Stages 7–9 verified, supported, coded assignments.
217:      Consumes: Stages 3 and 5; Stage 10 aggregation; Stage 11 metrics.
253:A stage routed straight to writing-plans (Stages 2, 9, 10, 14, 16) has no stage
```

Run:

```bash
grep -c "Stage 4\|Stage 15" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected: `0` — both numbers are vacant until Task 2.

- [ ] **Step 7: Commit**

```bash
git add specs/evidence-linked-theme-extraction-roadmap.md
git commit -m "docs(roadmap): renumber stages for the cohort insertion

Former Stages 4-13 become 5-14 and former Stage 14 becomes 16, leaving 4 and 15
vacant for the point-in-time DJIA cohort and the full eight-quarter run
(specs/point-in-time-djia-cohort.md, Architecture and revised stages). Titles,
routing, and checkbox states are unchanged; no stage is ticked."
```

---

### Task 2: Insert Stage 4 and Stage 15

**Files:**
- Modify: `specs/evidence-linked-theme-extraction-roadmap.md` (the header
  `Source spec:` paragraph; a new entry between Stage 3 and Stage 5; a new entry
  between Stage 14 and Stage 16; the stamp list)

**Interfaces:**
- Consumes: Task 1's renumbered roadmap.
- Produces: sixteen stage entries numbered `1`–`16` with no gaps; the `P`
  locator defined in the header; Stages 4 and 15 both `ROUTING: writing-plans`
  with `specs/point-in-time-djia-cohort.md` named as their stage spec.

- [ ] **Step 1: Write the failing check**

Run:

```bash
grep -n "^- \[ \] Stage 4:\|^- \[ \] Stage 15:" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected: no output, exit status 1.

- [ ] **Step 2: Define the `P` locator in the header**

Replace:

```text
Source spec: `specs/evidence-linked-theme-extraction.md`. Derived 2026-09-22
from `main` at `bdcf0a4`; notes reconciled the same day after instruction-only
edits (no stage shipped).
```

With:

```text
Source spec: `specs/evidence-linked-theme-extraction.md`. Derived 2026-09-22
from `main` at `bdcf0a4`; notes reconciled the same day after instruction-only
edits (no stage shipped).

Amending spec: `specs/point-in-time-djia-cohort.md`, adopted 2026-09-22. It
inserted Stage 4 (point-in-time DJIA cohort) and Stage 15 (full DJIA
eight-quarter run), renumbered former Stages 4–13 to 5–14 and former Stage 14 to
16, and moved pilot-sample selection out of the codebook stage into Stage 5. No
stage shipped. **`P` cites that spec**: `P-C1`–`P-C7` are its Decisions rows,
`P-A4`/`P-A5`/`P-A15` its three Acceptance-criteria groups, `P-VF`/`P-VI`/`P-VL`
its deterministic-fixture, offline-integration, and optional-live verification
groups, and `P §Section` cites a section by name.
```

- [ ] **Step 3: Insert the Stage 4 entry**

Insert immediately after the Stage 3 entry's `ROUTING: brainstorming` line and
its following blank line, so Stage 4 sits between Stage 3 and Stage 5. Match the
surrounding entries exactly: six leading spaces on every line after the heading,
one blank line between entries.

```text
- [ ] Stage 4: Point-in-time DJIA cohort
      Objective: Freeze a versioned, point-in-time DJIA universe — security-level membership intervals resolved to issuers and zero-padded CIKs — before any earnings document is acquired.
      Spec: P-C1, P-C2, P-C3, P-C4, P-C7, P-A4; P §Temporal definitions, §Data contracts (universe definition, membership assertion), §Membership evidence and source rights, §Issuer resolution, §Failure handling, §Verification; A §264 (zero-padded CIK), A §429 (the enrichment boundary this stage does not cross).
      Gap closed: P-C1, P-C2 (the membership-reference definition only; the event join is Stage 5), P-C3, P-C4, P-C7 (the cohort-before-acquisition half), P-A4; P-VF (interval, resolution, conflict, and cutoff cases), P-VI (its membership-interval and issuer-resolution legs).
      Consumes: Stage 2 contracts, provenance and hashing primitives, and the root pytest configuration with its registered `live` marker. No parser, canonicalizer, document, or model artifact — the stage is placed after Stage 3 so that acquisition follows it immediately, but Stage 2 is its only hard dependency.
      Produces: in `earnings-ingestion`, a versioned DJIA universe definition at P's universe grain (`universe_name = "djia"`, `period_end_start = 2024-07-01`, `period_end_stop = 2026-07-01`, `public_information_cutoff = 2026-09-22`, `membership_reference = first_publication_time`); security-level membership assertions at one row per index, security, effective interval, and source-evidence item, with half-open `[effective_from, effective_to)` intervals and a `status` of `supported`, `conflicting`, `ambiguous`, or `withheld`; security-to-issuer mappings carrying 10-character zero-padded CIK evidence; the derived union of candidate issuers over `[2024-07-01, 2026-07-01)`; a membership source register with owner, URL, access method, cost, terms, redistribution status, coverage, update behavior, known limitations, and last verification date; a coverage and conflict report; synthetic redistributable fixtures; version-controlled manual override assertions with evidence, rationale, reviewer, and effective dates; an opt-in `live` source-accessibility and terms check.
      Exit: every membership interval resolves to a source-evidence row and every resolved CIK is a 10-character zero-padded string (P-A4); fixture tests build intervals from an anchor plus additions and removals, with inclusive starts and exclusive ends, and an open interval carrying no `effective_to` (P-VF); a missing anchor snapshot and conflicting effective dates each refuse to freeze the manifest with the reason recorded, and conflicts persist as separate assertions rather than being merged (P §Failure handling); evidence first published after 2026-09-22 cannot revise the version (P-C4); a test shows no current snapshot silently backdated and no ETF holdings record treated as the official roster; a test shows historical ticker changes and multiple securities preserved, and one issuer's several securities deriving one issuer row (P-VF); source access and redistribution status are recorded for every source, with unclear rights keeping artifacts local; the universe manifest freezes with a version and content hash written atomically, and refuses to freeze on unresolved issuer identity unless the record is explicitly retained as unresolved and excluded with its reason; the default suite makes no network call, uses no proprietary roster, and needs no credentials.
      ROUTING: writing-plans — `specs/point-in-time-djia-cohort.md` is this stage's spec; it needs no brainstorming pass.
```

- [ ] **Step 4: Insert the Stage 15 entry**

Insert between the Stage 14 entry and the Stage 16 entry, same formatting.

```text
- [ ] Stage 15: Full DJIA eight-quarter run
      Objective: Run the configuration frozen by Stage 14 over every eligible event in the complete DJIA manifest, reporting the observed corpus shape rather than forcing it to a target.
      Spec: P-C6, P-A15; P §Stage 15 — Full DJIA eight-quarter run; R11.1–R11.3 (grain, denominators, coverage), R12.10 (replay bypass), R14.6 (cache keys), R14.1 (no billable call on the required path).
      Gap closed: P-C6, P-A15.
      Consumes: the frozen Stage 5 expected-event ledger and eligible-event manifest; the Stage 14 selected configuration, frozen by hash; Stage 11 metrics and the Stage 10 export path; cached pilot artifacts whose R14.6 cache key still matches. It reselects nothing.
      Produces: analytical outputs over every eligible event at the R11.1 grain, each row carrying universe, corpus, codebook, schema, and run versions; a coverage report giving expected, eligible, acquired, parsed, processed, failed, partial, and completed-no-theme counts by issuer and period; a reconciliation of the observed event count against the approximate `30 × 8` shape that attributes every departure to a membership transition or a missing event.
      Exit: every expected-event ledger row carries an eligibility and coverage status, and every eligible event a terminal or resumable processing status (P-A15); ineligible and ambiguous rows appear in coverage and status output without being processed as eligible, alongside the failed, unavailable, partial, and completed-no-theme cases; a test shows compatible pilot artifacts reused without producing duplicate accepted rows; a test shows the run performing no reselection, and the reported count is the observed count, never forced to equal `30 × 8` (P-C6); the coverage report names the transitions and missing events behind any departure from that shape.
      ROUTING: writing-plans — `specs/point-in-time-djia-cohort.md` is this stage's spec; it needs no brainstorming pass.
```

- [ ] **Step 5: Add the new stages to the stamp list**

In the `## Stage-spec stamp` section, replace **the whole four-line paragraph**.
Its first line already carries Task 1 Step 5's renumbering; the other three are
untouched so far. Quote all four lines when you match — replacing only the first
leaves the remaining three orphaned mid-sentence.

Replace:

```text
A stage routed straight to writing-plans (Stages 2, 9, 10, 14, 16) has no stage
spec: its plan header carries the Roadmap line directly, and its COMPLETE line
is appended to the Rollout section of `specs/evidence-linked-theme-extraction.md`,
which is the stamp a resume reads for those stages.
```

With:

```text
A stage routed straight to writing-plans (Stages 2, 9, 10, 14, 16) has no stage
spec of its own: its plan header carries the Roadmap line directly, and its
COMPLETE line is appended to the Rollout section of
`specs/evidence-linked-theme-extraction.md`, which is the stamp a resume reads
for those stages. Stages 4 and 15 are also routed to writing-plans but do have a
stage spec — `specs/point-in-time-djia-cohort.md` — so their COMPLETE lines
follow the normal stamp convention against that file.
```

- [ ] **Step 6: Verify**

Run:

```bash
grep -n "^- \[ \] Stage " specs/evidence-linked-theme-extraction-roadmap.md \
  | sed 's/.*Stage \([0-9]*\).*/\1/' | paste -sd, -
```

Expected: `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16`

Run:

```bash
grep -c "ROUTING: writing-plans" specs/evidence-linked-theme-extraction-roadmap.md
grep -n "P-C6\|P-A4" specs/evidence-linked-theme-extraction-roadmap.md | head -4
grep -c "^- \[x\]" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected: `7` routing lines (Stages 2, 4, 9, 10, 14, 15, 16); `P-C6` and `P-A4`
each appearing in the new entries; `0` ticked stages.

- [ ] **Step 7: Commit**

```bash
git add specs/evidence-linked-theme-extraction-roadmap.md
git commit -m "docs(roadmap): add Stage 4 cohort and Stage 15 full run

Stage 4 freezes a versioned point-in-time DJIA universe with security-level
membership intervals and zero-padded CIKs before any document is acquired. Stage
15 runs the Stage 14 configuration over the complete eligible-event manifest and
reports the observed count rather than forcing 30 x 8. Both are routed to
writing-plans against specs/point-in-time-djia-cohort.md. Defines the P locator.
Neither stage is ticked."
```

---

### Task 3: Reconcile Stage 5, Stage 6, and Stage 11, and record D4

Renumbering alone leaves three entries saying the wrong thing. Stage 5 must
absorb event discovery, eligibility, and the binding freeze order. Stage 6 must
stop choosing the sample. Stage 11 must consume the frozen manifest rather than a
manifest the codebook stage owned.

This task also records **D4**, the user's 2026-09-22 resolution of a real
conflict: the old Stage 5 Exit required the pilot manifest to *hold* unavailable,
restricted, and parser-failure bundles (R12.4), which conditions selection on
acquisition and parse outcomes — exactly what `P-C7` forbids. D4 makes
failure-class coverage an **observed report over the frozen manifest**, and moves
curated hard negatives (R12.5) to fixtures held outside it.

**Files:**
- Modify: `specs/evidence-linked-theme-extraction-roadmap.md` (the decisions
  paragraph in §Gap analysis; the Stage 5, Stage 6, and Stage 11 entries)

**Interfaces:**
- Consumes: Task 2's sixteen-stage roadmap.
- Produces: Stage 5 titled `Event discovery, eligibility, and acquisition` and
  Stage 6 titled `Pilot codebook, split, and gold-set protocol`; D4 recorded
  beside D1–D3; every reference to a pilot manifest pointing at Stage 5 as its
  owner.

- [ ] **Step 1: Write the failing check**

Run:

```bash
grep -n "^- \[ \] Stage 5:\|^- \[ \] Stage 6:" specs/evidence-linked-theme-extraction-roadmap.md
grep -c "D4" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected:
```
- [ ] Stage 5: Acquisition and event resolution
- [ ] Stage 6: Pilot codebook and gold-set protocol
0
```

- [ ] **Step 2: Record D4**

Replace:

```text
Decisions taken by the user on 2026-09-22, resolving the batched questions:
**D1** — V6 gates only metrics the pilot can estimate (R12.2 conflicts with
V6 as written); **D2** — the user is the sole annotator (R12.6, R8.4);
**D3** — R14.2's hosted ceiling is an optional stage; R5.3/V3 are unstaged.
```

With:

```text
Decisions taken by the user on 2026-09-22, resolving the batched questions:
**D1** — V6 gates only metrics the pilot can estimate (R12.2 conflicts with
V6 as written); **D2** — the user is the sole annotator (R12.6, R8.4);
**D3** — R14.2's hosted ceiling is an optional stage; R5.3/V3 are unstaged.

**D4** — taken 2026-09-22 with the cohort amendment, resolving R12.4/R12.5
against `P-C7`. R12.4 required the pilot manifest to *hold* unavailable,
restricted, and parser-failure bundles; `P-C7` forbids selection from depending
on acquisition, parse, or theme outcomes. Selection stays outcome-blind, and
failure-class coverage becomes an **observed report over the frozen manifest**: a
class absent from the 40 selected events is reported as a coverage gap and is
never repaired by reselecting. R12.5's curated hard negatives move to fixtures
held outside the pilot manifest, exercised by contract tests rather than by event
selection.

Counting note: `P` counts **issuer-events** and targets exactly 40 (`P-C5`),
while R12.2 counts hand-coded documents or bundles at 20–40. The two are
compatible — 40 sits inside 20–40 — but one event may yield several bundles
(a release plus its transcript, copies, or revisions), so the bundle count can
exceed the event count. Never treat the two numbers as the same quantity.
```

- [ ] **Step 3: Replace the Stage 5 entry**

**Bound the replacement precisely.** `ROUTING: brainstorming` is the last line of
several entries, so "replace the entry" is ambiguous unless you anchor both ends.
The region to replace is the eight lines from

```text
- [ ] Stage 5: Acquisition and event resolution
```

through the **first** following

```text
      ROUTING: brainstorming
```

inclusive — and **not** the blank line after it. Find the boundaries first:

```bash
grep -n "^- \[ \] Stage 5:\|^- \[ \] Stage 6:" specs/evidence-linked-theme-extraction-roadmap.md
```

The Stage 5 region runs from the first line number to two lines before the second
(the `ROUTING` line, then a blank line, then the Stage 6 heading).

Replace that region with:

```text
- [ ] Stage 5: Event discovery, eligibility, and acquisition
      Objective: Resolve expected earnings events and their first supported publication, freeze the eligible-event and 40-event pilot manifests, and only then acquire the selected releases from EDGAR.
      Spec: R1.1–R1.5, R14.5; A §391–427; P-C2, P-C5, P-C7, P-A5; P §Stage 5 — Event discovery, eligibility, and acquisition, §Temporal definitions, §Data contracts (expected event, pilot selection), §Deterministic pilot selection, §Failure handling.
      Gap closed: R1.1, R1.2, R1.3, R1.4, R1.5, R14.5; P-C2 (the event join), P-C5, P-C7 (the freeze-before-outcomes half), P-A5; P-VF (period-window, eligibility-reason, and selection cases), P-VI.
      Consumes: the frozen Stage 4 cohort — universe manifest, membership intervals, and security-to-issuer resolution with CIK evidence; Stage 1 V1 findings; Stage 2 contracts; Stage 3 canonicalizer (content inspection for R1.2/R1.5).
      Produces: an expected issuer-period event ledger over the eight period-end quarters in `[2024-07-01, 2026-07-01)`; release discovery that keeps `period_end`, the issuer's `reported_fiscal_year`/`reported_fiscal_quarter`, `first_publication_time`, `filing_acceptance_time`, and `retrieved_at` as separate fields; a per-event eligibility decision of `eligible`, `ineligible`, or `ambiguous` with its `eligibility_reason`; a frozen eligible-event manifest with a content hash; a frozen 40-event pilot manifest whose rows each record `issuer_coverage`, `membership_boundary`, `quarter_coverage`, or `longitudinal_fill`, plus the selection seed, policy version, and eligible-event manifest hash; an opt-in live EDGAR adapter behind the shared 2 req/s limiter with its User-Agent configured outside Git; immutable raw snapshots with retrieval metadata; a per-document processing-state table including expected-but-absent documents with a `missing_reason`; offline replay from saved responses.
      Exit: the six-step order in `P §Stage 5` is enforced and tested — both manifests freeze before any acquisition, parse, retention, or theme outcome exists, and a test shows the pilot manifest unchanged after acquisition and parser statuses change (P-C7); a selected event stays selected when acquisition, parsing, extraction, or support assessment fails; releases immediately before and after a membership transition resolve to the correct side, and a same-day transition without sufficient ordering precision stays `ambiguous` with no invented time (P-C2); both period-window boundaries and all three eligibility reasons are covered by fixtures (P-VF); shuffled input order yields a byte-identical pilot manifest that represents every eligible issuer and all eight quarters, and the underfilled, blocked, and mandatory-coverage-overflow cases each stop or mark the pilot as `P §Deterministic pilot selection` requires (P-C5); changing membership evidence, issuer resolution, the event corpus, or the selection policy invalidates the manifest and produces a new version and hash (P-VF); EDGAR acceptance time establishes first publication only when no earlier supported public source exists, and an unknown time stays unknown; offline replay of saved EDGAR responses identifies the fixture issuers' releases, including a narrative-only release and alternative exhibit numbering (R1.1/R1.2); tests hold concurrent workers at or below 2 req/s and stop on a persistent 403 without rotating identity (R1.3); the state table represents every R1.4 state from fixtures (R1.4); library output is Polars at the boundary, or V1's vacuity is recorded (R14.5).
      ROUTING: brainstorming
```

> `ROUTING` stays `brainstorming`: `P` fixes the contracts and the selection
> algorithm, but the acquisition half still carries the open EDGAR-access and
> source-rights design that the original entry was routed for.

- [ ] **Step 4: Replace the Stage 6 entry**

Bound it the same way as Step 3: from

```text
- [ ] Stage 6: Pilot codebook and gold-set protocol
```

through the **first** following `      ROUTING: brainstorming`, inclusive,
stopping before the blank line that precedes the Stage 7 heading.

Replace that region with:

```text
- [ ] Stage 6: Pilot codebook, split, and gold-set protocol
      Objective: Take the frozen pilot manifest as given, split it by issuer and time, approve codebook v0, and validate annotations, so hand-coding runs while Stages 7–10 are built.
      Spec: R9.2, R9.7, R12.1–R12.6; R13.1 (release-identification labels); D2, D4; P-C5, P-C7.
      Gap closed: R9.2, R9.7, R12.1, R12.3, R12.4 (as observed coverage, D4), R12.5 (as out-of-manifest fixtures, D4); R12.6 (limitation, D2).
      Consumes: the frozen Stage 5 pilot manifest — this stage no longer selects the sample; Stage 3 canonical documents (gold spans bind to that canonicalization version); Stage 5 event bundles, issuer and fiscal-period identity, and processing states.
      Produces: a codebook contract with R9.2's fields; codebook v0 drafted from training-partition bundles only and approved in a decision record; a gold-annotation contract and validator; an issuer-and-time split over the frozen manifest; an observed failure-class coverage report over that manifest; curated hard negatives held as fixtures outside the manifest. Gold spans name their canonical version; a later version re-anchors them before reuse, never mutates them.
      Exit: a test places each bundle, with all copies and revisions, in exactly one issuer-and-time split (R12.1/R12.3); the coverage report states the observed count of no-theme, unavailable, restricted, and parser-failure bundles in the frozen manifest, and a missing class is reported as a coverage gap, never repaired by reselecting (R12.4, D4); a test shows the split and the report changing no row of the pilot manifest (P-C7); curated hard negatives exist as fixtures outside the pilot manifest (R12.5, D4); codebook v0's decision record names its training-partition discovery corpus (R9.2/R9.7); annotations on at least three bundles, including release-identification labels, pass the validator; the single-annotator limitation is recorded (R12.6, D2).
      ROUTING: brainstorming
```

- [ ] **Step 5: Fix the Stage 11 Consumes line**

Replace:

```text
      Consumes: the Stage 6 manifest fully annotated by the user; at least 50 user support labels on Stage 8 outputs (D2); the Stage 10 pipeline.
```

With:

```text
      Consumes: the frozen Stage 5 pilot manifest, split by Stage 6 and fully annotated by the user; at least 50 user support labels on Stage 8 outputs (D2); the Stage 10 pipeline.
```

> Task 1's `sed` correctly turned `Stage 5 manifest` into `Stage 6 manifest`,
> but after D4 the manifest is Stage 5's artifact and Stage 6 only splits it.

- [ ] **Step 6: Verify**

Run:

```bash
grep -n "^- \[ \] Stage 5:\|^- \[ \] Stage 6:" specs/evidence-linked-theme-extraction-roadmap.md
grep -c "D4" specs/evidence-linked-theme-extraction-roadmap.md
grep -n "no longer selects the sample" specs/evidence-linked-theme-extraction-roadmap.md
grep -n "frozen Stage 5 pilot manifest, split by Stage 6" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected:
```
- [ ] Stage 5: Event discovery, eligibility, and acquisition
- [ ] Stage 6: Pilot codebook, split, and gold-set protocol
```
`grep -c` returning `4` — it counts *lines*, not occurrences, and `D4` appears on
four: the decisions paragraph's first line plus Stage 6's `Spec:`, `Gap closed:`,
and `Exit:` lines (the latter two mention it twice each). One hit each for the
last two greps.

Run:

```bash
grep -n "20–40 event-bundle pilot manifest" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected: no output — the old sample-choosing text is gone.

Finally, confirm Steps 3 and 4 replaced exactly their own regions and did not
swallow a neighbour:

```bash
grep -c "^- \[ \] Stage " specs/evidence-linked-theme-extraction-roadmap.md
grep -c "^      ROUTING: " specs/evidence-linked-theme-extraction-roadmap.md
```

Expected: `16` and `16`. A count of 15 means a replacement consumed the following
entry's heading; 17 means a heading was duplicated.

- [ ] **Step 7: Commit**

```bash
git add specs/evidence-linked-theme-extraction-roadmap.md
git commit -m "docs(roadmap): move pilot selection into the event stage

Stage 5 becomes event discovery, eligibility, and acquisition, and owns the
binding freeze order: the eligible-event and 40-event pilot manifests freeze
before any acquisition or parse outcome exists. Stage 6 keeps the codebook,
split, and gold-set protocol and no longer chooses the sample. Records D4: R12.4
failure-class coverage becomes an observed report over the frozen manifest and
R12.5 hard negatives move to out-of-manifest fixtures, because conditioning
selection on processing outcomes is what P-C7 forbids. Notes that P counts
issuer-events while R12.2 counts bundles."
```

---

### Task 4: Record the cohort requirements in the gap analysis

The roadmap's §Completion re-runs "the gap rubric over every row above". Cohort
requirements absent from that table would escape the conformance audit.

**Files:**
- Modify: `specs/evidence-linked-theme-extraction-roadmap.md` (the gap table's
  tail, after the `Dev tooling` row; the `Totals:` line)

**Interfaces:**
- Consumes: Tasks 2 and 3 (the `P` locator and D4 must already be defined).
- Produces: thirteen `P-*` rows and a corrected totals line. Every `Gap closed:`
  key used in Tasks 2 and 3 resolves to a row here.

- [ ] **Step 1: Write the failing check**

Run:

```bash
grep -c "^| P-" specs/evidence-linked-theme-extraction-roadmap.md
grep -n "^Totals:" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected:
```
0
109:Totals: 78 missing · 2 implemented-as-specified · 4 in-code-but-not-in-spec ·
```

- [ ] **Step 2: Insert the `P-*` rows**

Insert the rows **directly beneath the `Dev tooling` row with no blank line
between them** — a blank line ends the Markdown table, and the 13 rows would then
render as a paragraph of pipe characters. The blank line that currently precedes
`Totals:` stays where it is, now below the new rows.

Keep the `| Req | Verdict | Evidence | Note |` column order
and reuse the existing `none found¹` evidence marker — footnote 1's search
covered `packages/*/src`, `apps/*/src`, `tests/`, `config/`, `codebooks/`,
`prompts/`, and `expirements/`, which is where cohort code would live.

```text
| P-C1 | missing | none found¹ | DJIA resolved point in time, not as one current roster; Stage 4 |
| P-C2 | missing | none found¹ | Eligibility keyed to `first_publication_time`; defined in Stage 4, joined in Stage 5 |
| P-C3 | missing | none found¹ | Window `[2024-07-01, 2026-07-01)`; reported fiscal labels stay separate fields |
| P-C4 | missing | none found¹ | Public-information cutoff `2026-09-22` |
| P-C5 | missing | none found¹ | Deterministic 40-event pilot; supersedes the codebook stage's former sample choice (D4) |
| P-C6 | missing | none found¹ | Full eight-quarter run is Stage 15; observed count never forced to `30 × 8` |
| P-C7 | missing | none found¹ | Cohort-before-acquisition order is binding; split across Stages 4 and 5 |
| P-A4 | missing | none found¹ | Stage 4 acceptance criteria |
| P-A5 | missing | none found¹ | Stage 5 acceptance criteria |
| P-A15 | missing | none found¹ | Stage 15 acceptance criteria |
| P-VF | missing | none found¹ | 19 deterministic fixture cases; split across Stages 4 and 5 |
| P-VI | missing | none found¹ | Offline integration replay, anchor evidence through frozen pilot manifest |
| P-VL | missing | none found¹ | Optional `live` source-accessibility check; never in default CI |
```

- [ ] **Step 3: Correct the totals**

Replace:

```text
Totals: 78 missing · 2 implemented-as-specified · 4 in-code-but-not-in-spec ·
0 implemented-differently · 0 out-of-repo.
```

With:

```text
Totals: 91 missing · 2 implemented-as-specified · 4 in-code-but-not-in-spec ·
0 implemented-differently · 0 out-of-repo. The 91 comprises 78 rows from
`specs/evidence-linked-theme-extraction.md` and 13 from
`specs/point-in-time-djia-cohort.md` (the `P-*` rows).
```

- [ ] **Step 4: Note the cohort deferrals in §Completion**

The cohort spec defers nothing, but §Completion's audit needs to know the `P-*`
rows are in scope. Replace:

```text
Retire this roadmap only after a conformance audit of the accumulated system:
re-run the gap rubric over every row above, with evidence per verdict
(implementing stage and plan, `> Deviation:` notes, deferred entries). Each
```

With:

```text
Retire this roadmap only after a conformance audit of the accumulated system:
re-run the gap rubric over every row above — including the 13 `P-*` rows from
`specs/point-in-time-djia-cohort.md` — with evidence per verdict (implementing
stage and plan, `> Deviation:` notes, deferred entries). Each
```

- [ ] **Step 5: Verify**

Run:

```bash
grep -c "^| P-" specs/evidence-linked-theme-extraction-roadmap.md
grep -n "^Totals: 91" specs/evidence-linked-theme-extraction-roadmap.md
```

Expected: `13`, and one hit for the totals line.

The count above passes even if the rows fell outside the table, so confirm table
membership directly:

```bash
sed -n '/Dev tooling/,/^Totals:/p' specs/evidence-linked-theme-extraction-roadmap.md
```

Expected: the `Dev tooling` row, then the 13 `| P-…` rows with **no blank line
between the `Dev tooling` row and `| P-C1 |`**, then exactly one blank line, then
`Totals:`. A blank line above `| P-C1 |` means the table was broken — move the
rows up.

Cross-check that every `Gap closed:` key resolves to a table row:

```bash
grep -o "P-[A-Z0-9]*" specs/evidence-linked-theme-extraction-roadmap.md | sort -u | paste -sd, -
```

Expected: `P-A15,P-A4,P-A5,P-C1,P-C2,P-C3,P-C4,P-C5,P-C6,P-C7,P-VF,P-VI,P-VL`
— thirteen keys, no fourteenth, no typo.

- [ ] **Step 6: Commit**

```bash
git add specs/evidence-linked-theme-extraction-roadmap.md
git commit -m "docs(roadmap): add cohort rows to the gap analysis

Thirteen P-* rows record the cohort spec's decisions, acceptance criteria, and
verification groups as missing, so the Completion audit covers them. Totals rise
to 91 missing with the split by source spec stated."
```

---

### Task 5: Amend the parent specification

**Files:**
- Modify: `specs/evidence-linked-theme-extraction.md` (the opening scope
  sentence around line 8; the amends/supersedes block around line 52; the
  `Company enrichment` out-of-scope bullet at line 599; §Rollout)

**Interfaces:**
- Consumes: nothing from earlier tasks — this file's edits are independent, but
  it is sequenced here so the roadmap it points at already exists in its final
  shape.
- Produces: a parent spec that puts point-in-time cohort selection in scope,
  keeps general company enrichment out, and names the amending spec. It uses
  **no roadmap stage numbers**, so future renumbering cannot invalidate it.

- [ ] **Step 1: Write the failing check**

Run:

```bash
grep -n "seven stages" specs/evidence-linked-theme-extraction.md
grep -c "point-in-time-djia-cohort" specs/evidence-linked-theme-extraction.md
```

Expected:
```
8:source text. It covers seven stages — acquisition and event resolution,
0
```

- [ ] **Step 2: Widen the scope sentence**

Replace:

```text
source text. It covers seven stages — acquisition and event resolution,
structure-aware canonicalization, evidence selection, deterministic span
verification, semantic support assessment, codebook construction and coding, and
coverage-aware aggregation — plus the evaluation design that decides whether any
of it works.
```

With:

```text
source text. It covers eight stages — point-in-time cohort selection, acquisition
and event resolution, structure-aware canonicalization, evidence selection,
deterministic span verification, semantic support assessment, codebook
construction and coding, and coverage-aware aggregation — plus the evaluation
design that decides whether any of it works.
```

> Count the list after editing: cohort selection (1), acquisition and event
> resolution (2), canonicalization (3), evidence selection (4), span
> verification (5), support assessment (6), codebook and coding (7),
> aggregation (8).

- [ ] **Step 3: Name the amending spec**

Insert after the `**This spec supersedes**` paragraph and before the
`**Naming.**` paragraph:

```text
**This spec is amended by** `specs/point-in-time-djia-cohort.md`. That
specification defines the firm universe and event corpus this one consumes: a
versioned, point-in-time DJIA cohort frozen before any document is acquired; a
40-event feasibility pilot selected deterministically from frozen event metadata
rather than chosen during codebook construction; and a later full run over the
eight calendar period-end quarters in `[2024-07-01, 2026-07-01)` under a
`2026-09-22` public-information cutoff. Where the two conflict on the firm
universe, the event corpus, or how the pilot sample is chosen, it governs.
Everything here about canonicalization, evidence selection, verification,
support, coding, and aggregation stands unchanged.
```

- [ ] **Step 4: Carve the cohort out of the enrichment exclusion**

Replace:

```text
- **Company enrichment** — membership, identifiers, subsidiaries, employment,
  locations, industry classification. These supply optional dated context through
  joins, never evidence for words absent from a document (`A §445`). `AGENTS.md`
  governs them unchanged.
```

With:

```text
- **Company enrichment** — subsidiaries, employment, locations, industry
  classification, and identifier enrichment beyond what the cohort needs. These
  supply optional dated context through joins, never evidence for words absent
  from a document (`A §445`). `AGENTS.md` governs them unchanged. **In scope by
  amendment:** point-in-time index membership and the
  security-to-issuer-to-CIK resolution the cohort depends on, per
  `specs/point-in-time-djia-cohort.md`. That carve-out is narrow — GICS, SIC, and
  NAICS never alter cohort eligibility, and no enrichment dataset becomes a
  dependency of theme extraction.
```

- [ ] **Step 5: State the ordering constraint in §Rollout**

Insert after the paragraph beginning `The two tracks stay connected` and before
the paragraph beginning `Three requirements amend binding instructions`:

```text
**Cohort before corpus.** `specs/point-in-time-djia-cohort.md` places a frozen,
point-in-time cohort before document acquisition, and freezes the eligible-event
and pilot manifests before any acquisition, parse, retention, or theme outcome is
known. Do not begin document acquisition until those artifacts can be frozen: a
sample conditioned on what happened to download or parse cleanly cannot support
the coverage-aware denominators R11.2 and R11.3 require.
```

- [ ] **Step 6: Verify**

Run:

```bash
grep -n "eight stages" specs/evidence-linked-theme-extraction.md
grep -n "This spec is amended by\|In scope by amendment\|Cohort before corpus" specs/evidence-linked-theme-extraction.md
grep -c "point-in-time-djia-cohort" specs/evidence-linked-theme-extraction.md
```

Expected: one hit for `eight stages`, one hit each for the three new markers, and
`3` mentions of the cohort spec — one per edit in Steps 3, 4, and 5.

Confirm no roadmap stage number entered this file — only the two
`docs/earnings-themes.md` citations should match:

```bash
grep -n "Stage [0-9]" specs/evidence-linked-theme-extraction.md
```

Expected exactly three lines, all of the pre-existing `` `S` Stage n `` form:
```
62:second model checking the first (`A §518`, `S` Stage 2) — and on the analytical
217:the wording. *(chosen as ablation; `A §518`, `S` Stage 2, RG §3, RX §3)*
468:measuring fresh-call variability (`A §728`, `S` Stage 6).
```
(Line numbers shift by the lines inserted above them; the three `` `S` ``
citations must be the only matches.)

- [ ] **Step 7: Commit**

```bash
git add specs/evidence-linked-theme-extraction.md
git commit -m "docs(spec): put point-in-time cohort selection in scope

The scope sentence covers eight stages; a new paragraph names
specs/point-in-time-djia-cohort.md as the amending spec and states where it
governs; the company-enrichment exclusion carves out index membership and the
security-to-issuer-to-CIK resolution the cohort needs while keeping
subsidiaries, employment, locations, and industry classification out; Rollout
states that cohort freezing precedes acquisition. No roadmap stage numbers are
introduced here, so renumbering cannot invalidate this file."
```

---

### Task 6: Update the README

**Files:**
- Modify: `README.md` (§Current roadmap, around lines 120–146; the source-register
  bullet around line 228)

**Interfaces:**
- Consumes: Tasks 2–5.
- Produces: a README naming the sixteen-stage roadmap, linking the cohort spec,
  and correcting the source-register claim.

- [ ] **Step 1: Write the failing check**

Run:

```bash
grep -c "point-in-time-djia-cohort" README.md
grep -n "is a Stage 1 deliverable" README.md
```

Expected:
```
0
230:  is a Stage 1 deliverable; it does not exist yet.
```

- [ ] **Step 2: Describe the amended roadmap**

Replace:

```text
The implementation is organized as a staged, evidence-first roadmap. No stage is
marked complete yet.
```

With:

```text
The implementation is organized as a staged, evidence-first roadmap of sixteen
stages. No stage is marked complete yet.

The roadmap was amended on 2026-09-22 by
[the point-in-time DJIA cohort specification](specs/point-in-time-djia-cohort.md).
It inserts **Stage 4: point-in-time DJIA cohort** before any document is
acquired, moves the 40-event feasibility pilot into **Stage 5** as a
deterministic selection frozen before any acquisition or parse outcome is known,
and adds **Stage 15: the full DJIA eight-quarter run** over calendar period ends
from `2024Q3` through `2026Q2`. The firm universe is the Dow Jones Industrial
Average resolved point in time, not one current roster: a current list would
introduce survivorship bias into earlier periods.
```

- [ ] **Step 3: Link the cohort spec in the planning-documents list**

Replace:

```text
- [Stage 1 parser-fidelity specification](specs/release-parser-fidelity.md)
  — the current milestone's scope and measurement design.
```

With:

```text
- [Stage 1 parser-fidelity specification](specs/release-parser-fidelity.md)
  — the current milestone's scope and measurement design.
- [Point-in-time DJIA cohort specification](specs/point-in-time-djia-cohort.md)
  — the firm universe, event corpus, and deterministic pilot selection; the
  stage specification for roadmap Stages 4, 5, and 15.
```

- [ ] **Step 4: Correct the source-register claim**

Replace:

```text
- The source register that records access, licensing, and redistribution status
  is a Stage 1 deliverable; it does not exist yet.
```

With:

```text
- The source register that records access, licensing, and redistribution status
  is a Stage 1 deliverable for release fixtures, and Stage 4 adds a second
  register for index-membership sources. Neither exists yet. A free or
  open-source acquisition tool confers no rights to the underlying index data.
```

- [ ] **Step 5: Verify**

Run:

```bash
grep -c "point-in-time-djia-cohort" README.md
grep -n "sixteen stages\|Stage 15\|index-membership sources" README.md
grep -o "Stage [0-9]*" README.md | sort -u
```

Expected: `2` cohort-spec links; one hit each for `sixteen stages`,
`Stage 15`, and `index-membership sources`; and the third command printing only
`Stage 1`, `Stage 2`, `Stage 4`, `Stage 5`, and `Stage 15`.

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: describe the cohort amendment in the README

The roadmap summary states sixteen stages and describes the inserted cohort
stage, the deterministic 40-event pilot, and the full eight-quarter run. Links
the cohort specification. Corrects the source-register bullet: Stage 1 registers
release fixtures, Stage 4 adds a membership-source register."
```

---

### Task 7: Renumber the Stage 1 documents

Both Stage 1 documents were written against the pre-amendment numbering, and they
differ in which numbers they use:

| File | Stale references | Becomes |
| --- | --- | --- |
| `specs/release-parser-fidelity.md` | `Stage 4` (acquisition), `Stage 5` (pilot split), the Handoffs table's bare `\| 4 \|` and `\| 5 \|` rows, `stage4_flags` ×2 | Stage 5, Stage 6, rows 5 and 6, `acquisition_flags` |
| `specs/plans/1-release-parser-fidelity.md` | `Stage 4` ×3, `stage4_flags` ×6 | Stage 5, `acquisition_flags` |

The Handoffs table is the trap: its stage column holds **bare numbers** with no
`Stage` prefix, so no `Stage N` `sed` reaches them.

Both documents also carry the old number **in a field name** — `stage4_flags`, a
key in the fixture manifest and the name of a test. Renaming it to
`acquisition_flags` decouples the field from stage numbering permanently.

**Check first whether the field has reached code.** At planning time it had not —
it existed only in these two documents, with nothing under
`expirements/parser-fidelity/` using it — but Stage 1 execution is live and may
have written it since:

```bash
grep -rn "stage4_flags" expirements/ tests/ packages/ apps/ 2>/dev/null
```

- **No output:** rename freely (Steps 3 and 5).
- **Any output:** the field is in code. Do **not** rename it here — a live
  execution owns those files. Apply the prose renumbering only, and defer the
  rename with `Done when: Stage 1 execution is complete and the manifest field
  can be renamed in documents and code together`.

> If your human partner prefers to keep the field name regardless, apply the
> prose steps only and skip the rename. Say which you did in the task report.

**Files:**
- Modify: `specs/release-parser-fidelity.md` (lines 121, 147, 164, 474, 614–615)
- Modify: `specs/plans/1-release-parser-fidelity.md` (lines 3205, 3246, 3359,
  3363, 3590, 7593, 9315, 9353)

**Interfaces:**
- Consumes: the renumbering in Task 1.
- Produces: both Stage 1 documents citing the amended numbering, and
  `acquisition_flags` as the manifest field name.

- [ ] **Step 1: Write the failing check**

Run:

```bash
grep -n "Stage [45]" specs/release-parser-fidelity.md
grep -n "Stage 4\|stage4_flags" specs/plans/1-release-parser-fidelity.md
```

Expected 3 lines from the spec:
```
121:   - Issuers that also exercise Stage 4's cases: a narrative-only release, and a
164:The annotator reads every fixture closely. Stage 5 must therefore place fixture
474:  - (a) listing an issuer's filings (Stage 4, R1.1);
```

and 8 lines from the plan:
```
3205:  other than EX-99.1, for Stage 4;
3246:    - `source_id`, `redistribution_basis`, `stage4_flags`, `pilot_split`;
3359:def test_stage4_flags(layout):
3363:        e["primary_class"]: e["stage4_flags"]
3590:        ("stage4_flags", flags),
7593:## For Stage 4
9315:  residual failures, altered anchors), and Stage 4 (the V1 record, `stage4_flags`)
9353:- `stage4_flags`
```

- [ ] **Step 2: Confirm which numbers move in each file**

Run:

```bash
grep -o "Stage [0-9]*" specs/release-parser-fidelity.md | sort -u
grep -o "Stage [0-9]*" specs/plans/1-release-parser-fidelity.md | sort -u
```

Expected: the spec uses Stages 1–5; the plan uses Stages 1–4 and **no Stage 5**.
Stages 1, 2, and 3 keep their numbers in both files, so none of those references
change. The plan's lack of any `Stage 5` is what makes its single-rule `sed` safe
in Step 4.

- [ ] **Step 3: Renumber the Stage 1 spec (descending)**

Two rules, highest first, so `Stage 4` does not get renumbered twice:

```bash
sed -i '' -e 's/Stage 5/Stage 6/g' -e 's/Stage 4/Stage 5/g' \
  specs/release-parser-fidelity.md
grep -n "Stage [56]" specs/release-parser-fidelity.md
```

Expected 3 lines:
```
121:   - Issuers that also exercise Stage 5's cases: a narrative-only release, and a
164:The annotator reads every fixture closely. Stage 6 must therefore place fixture
474:  - (a) listing an issuer's filings (Stage 5, R1.1);
```

Line 164 is the one to read carefully: it is about the **pilot split** placing
fixtures in the training partition, which is the codebook-and-split stage — old
Stage 5, now Stage 6 — not acquisition.

Now the Handoffs table, whose stage column is bare numbers the `sed` above cannot
reach. Replace:

```text
| 4 | The V1 record; the manifest's `stage4_flags` |
| 5 | `pilot_split = "train_or_exclude"` on every fixture event |
```

With:

```text
| 5 | The V1 record; the manifest's `acquisition_flags` |
| 6 | `pilot_split = "train_or_exclude"` on every fixture event |
```

> Rows 2 and 3 above them are unchanged — Stages 2 and 3 keep their numbers.
> Renumber these two only, and keep them in ascending order.

Then the field-definition row. Replace:

```text
| `stage4_flags` | Any of `narrative_only_release`, `alternative_exhibit_numbering` |
```

With:

```text
| `acquisition_flags` | Any of `narrative_only_release`, `alternative_exhibit_numbering` |
```

Verify the spec is fully converted:

```bash
grep -n "stage4_flags\|^| [0-9] |" specs/release-parser-fidelity.md
```

Expected: no `stage4_flags`, and the Handoffs rows reading `| 2 |`, `| 3 |`,
`| 5 |`, `| 6 |`.

- [ ] **Step 4: Renumber the plan's prose references**

```bash
sed -i '' 's/Stage 4/Stage 5/g' specs/plans/1-release-parser-fidelity.md
grep -n "Stage 5" specs/plans/1-release-parser-fidelity.md
```

Expected 3 lines:
```
3205:  other than EX-99.1, for Stage 5;
7593:## For Stage 5
9315:  residual failures, altered anchors), and Stage 5 (the V1 record, `stage4_flags`)
```

This `sed` is safe: plan 1 contains no `Stage 5` to collide with, no
`Stage 40`-style number, and no `Stage 4` inside a longer numeral.

- [ ] **Step 5: Rename the field**

```bash
sed -i '' 's/stage4_flags/acquisition_flags/g' specs/plans/1-release-parser-fidelity.md
grep -n "acquisition_flags\|stage4_flags" specs/plans/1-release-parser-fidelity.md
```

Expected 6 lines, no remaining `stage4_flags`:
```
3246:    - `source_id`, `redistribution_basis`, `acquisition_flags`, `pilot_split`;
3359:def test_acquisition_flags(layout):
3363:        e["primary_class"]: e["acquisition_flags"]
3590:        ("acquisition_flags", flags),
9315:  residual failures, altered anchors), and Stage 5 (the V1 record, `acquisition_flags`)
9353:- `acquisition_flags`
```

Note that `test_stage4_flags` became `test_acquisition_flags` in the same pass —
the test name is the field name plus the `test_` prefix, so it stays consistent.

- [ ] **Step 6: Check the field's ordering is still stated consistently**

The field appears in a manifest key list (3246), a tuple of ordered pairs (3590),
and a class-test value list (9353). Read all three and confirm the rename left
each list's order unchanged.

Run:

```bash
sed -n '3244,3248p;3586,3592p;9348,9356p' specs/plans/1-release-parser-fidelity.md
```

Expected: `acquisition_flags` sits in the same position it occupied before —
between `redistribution_basis` and `pilot_split` in the key list and the tuple.

- [ ] **Step 7: Commit**

```bash
git add specs/release-parser-fidelity.md specs/plans/1-release-parser-fidelity.md
git commit -m "docs(specs): retarget the Stage 1 documents' stage references

Acquisition and event resolution moved from Stage 4 to Stage 5 in the cohort
amendment, and the codebook-and-split stage from 5 to 6, so both Stage 1
documents follow. Renames the manifest field stage4_flags to acquisition_flags,
and test_stage4_flags with it, so the numbering stops living in a field name. Also
renumbers the Handoffs table's bare stage column, which no Stage N substitution
reaches. No other change to either document."
```

---

### Task 8: Register the cohort spec in CLAUDE.md

`CLAUDE.md`'s document-status table is what an agent reads first to learn which
documents bind. Without a row, the amendment is invisible to a fresh session.

**Files:**
- Modify: `CLAUDE.md` (the document-status table, after the roadmap row at
  line 15)

**Interfaces:**
- Consumes: Tasks 2–6.
- Produces: a document-status row naming the cohort spec and what it governs.

- [ ] **Step 1: Write the failing check**

Run:

```bash
grep -c "point-in-time-djia-cohort" CLAUDE.md
grep -n "Live staged roadmap" CLAUDE.md
```

Expected:
```
0
15:| `specs/evidence-linked-theme-extraction-roadmap.md` | **Live staged roadmap** for that spec. Resume it via the `derive-roadmap` skill's reconcile step and route each unticked stage per its ROUTING line; never plan it wholesale. |
```

- [ ] **Step 2: Insert the row**

Insert immediately after the roadmap row (line 15) so it sits beside the two
documents it amends:

```text
| `specs/point-in-time-djia-cohort.md` | **Amends both documents above** (adopted 2026-09-22, plan 2). Adds Stage 4, a versioned point-in-time DJIA cohort frozen before any document is acquired; moves the 40-event feasibility pilot into Stage 5 as a deterministic selection frozen before any acquisition or parse outcome is known; adds Stage 15, the full eight-quarter run. Governs on the firm universe, the event corpus, and pilot selection. Its window is `[2024-07-01, 2026-07-01)` and its public-information cutoff is `2026-09-22`. It is the stage spec for Stages 4, 5, and 15; no stage is complete. |
```

- [ ] **Step 3: Note the cohort carve-out beside the enrichment boundary**

`CLAUDE.md` currently sends readers to `AGENTS.md` for membership. Replace:

```text
**Not summarized below — go to `AGENTS.md` directly** for: §Source strategy (per-field source table), §Domain rules (membership/identifiers, industry classification, subsidiaries, employment, locations), §Shared data contracts and provenance (the dataset/grain table), §Models, orchestration, caching, and cost, §Tests and acceptance criteria (incl. the evaluation metric table), and §Delivery milestones.
```

With:

```text
**Not summarized below — go to `AGENTS.md` directly** for: §Source strategy (per-field source table), §Domain rules (membership/identifiers, industry classification, subsidiaries, employment, locations), §Shared data contracts and provenance (the dataset/grain table), §Models, orchestration, caching, and cost, §Tests and acceptance criteria (incl. the evaluation metric table), and §Delivery milestones. **Exception:** point-in-time index membership and security-to-issuer-to-CIK resolution are now governed by `specs/point-in-time-djia-cohort.md`, not by `AGENTS.md` §Domain rules. Subsidiaries, employment, locations, and industry classification stay with `AGENTS.md` and out of the theme-extraction path.
```

- [ ] **Step 4: Verify**

Run:

```bash
grep -c "point-in-time-djia-cohort" CLAUDE.md
grep -n "^| \`specs/point-in-time-djia-cohort.md\`" CLAUDE.md
awk -F'|' '/^\| `specs\// {print NR": "NF}' CLAUDE.md
```

Expected: `2` mentions; the new row present at line 16; and the third command
printing three lines, each with `4`:

```text
14: 4
15: 4
16: 4
```

That table has two columns, so a correctly-formed row splits into four fields on
`|` — an empty field at each end. A different count on line 16 means a stray or
missing pipe. (Before the insertion this command prints only `14: 4` and `15: 4`.
The architecture table further down the file has five fields per row; ignore it.)

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude): register the point-in-time cohort specification

Adds a document-status row for specs/point-in-time-djia-cohort.md stating what
it amends and where it governs, and notes the one exception to the 'go to
AGENTS.md for membership' pointer: point-in-time index membership and
security-to-issuer-to-CIK resolution now follow the cohort spec."
```

---

### Task 9: Cross-file sweep

The amendment's real failure mode is a missed reference, not a bad edit. This
task asserts that every `Stage N` mention anywhere in the repository resolves to
a title in the sixteen-stage list.

**Files:**
- Read only: all five amended files plus `specs/point-in-time-djia-cohort.md`
- Create: nothing. The sweep is a command, not a committed script — this plan
  ships no code.

**Interfaces:**
- Consumes: Tasks 1–8.
- Produces: verified consistency, and the completion report's evidence.

- [ ] **Step 1: Assert every stage number is in range**

The exclusion of `` `S` Stage n `` must happen **before** `grep -o` strips the
surrounding context, or it silently matches nothing.

Run:

```bash
cd /Users/lowell/Projects/earnings-themes
grep -rn "Stage [0-9]" \
  specs/evidence-linked-theme-extraction-roadmap.md \
  specs/evidence-linked-theme-extraction.md \
  specs/point-in-time-djia-cohort.md \
  specs/release-parser-fidelity.md \
  specs/plans/1-release-parser-fidelity.md \
  README.md CLAUDE.md \
  | grep -v '`S` Stage' \
  | grep -o "Stage [0-9]*" | sort -u -k2 -n | paste -sd, -
```

Expected exactly:

```text
Stage 1,Stage 2,Stage 3,Stage 4,Stage 5,Stage 6,Stage 7,Stage 8,Stage 9,Stage 10,Stage 11,Stage 12,Stage 13,Stage 14,Stage 15,Stage 16
```

Three notes on this command, each load-bearing:

- **The `` `S` Stage `` exclusion must precede `grep -o`.** After `-o` strips the
  surrounding context there is nothing left to exclude, so the filter would
  silently match nothing and the `docs/earnings-themes.md` learning-path stages
  cited in the parent spec would be counted as roadmap stages.
- **`docs/` and `AGENTS.md` are deliberately absent** from the file list.
  `docs/earnings-themes.md` numbers its own Stages 0–4 (the learning path) and
  `AGENTS.md` never mentions the roadmap — verified. Adding either produces false
  positives.
- **This plan file is deliberately absent too.** Its prose names `Stage 0` and
  `Stage 40` as counterexamples, which would fail its own check.

This is a **range guard, not the acceptance test.** It passes both before and
after the amendment, because `specs/point-in-time-djia-cohort.md` already lists
Stages 1–16. Its job is to catch an out-of-range typo such as `Stage 17` or a
number left at `Stage 0`. Step 2 is the check that actually fails on a stale
tree.

- [ ] **Step 2: Assert the roadmap's sixteen titles match the spec's list**

Run:

```bash
while IFS='|' read -r n title; do
  if grep -q "^- \[ \] Stage $n: $title" specs/evidence-linked-theme-extraction-roadmap.md; then
    echo "ok $n"
  else
    echo "MISMATCH $n: expected prefix '$title'"
  fi
done <<'EOF'
1|Acquisition-library and parser fidelity
2|Core evidence spine
3|Structure-aware canonicalization
4|Point-in-time DJIA cohort
5|Event discovery, eligibility, and acquisition
6|Pilot codebook, split, and gold-set protocol
7|Evidence selection and verification
8|Semantic support assessment
9|Deductive coding
10|Coverage-aware aggregation and cited export
11|Feasibility pilot and threshold calibration
12|Inductive and hybrid codebook
13|Transcript extension
14|Configuration comparison and held-out evaluation
15|Full DJIA eight-quarter run
16|Hosted quality ceiling (optional)
EOF
```

Expected: sixteen `ok` lines, none `MISMATCH`. The check is a prefix match, so
the roadmap's parentheticals (`(investigation)`, `(theme vertical slice)`,
`(conditional on V7)`) do not break it. These sixteen titles are exactly
`P §Architecture and revised stages`.

**This is the plan's acceptance test, and it discriminates.** Run on the
pre-amendment roadmap it prints `ok 1`, `ok 2`, `ok 3` and then thirteen
`MISMATCH` lines — verified before this plan was written. If you see sixteen `ok`
lines, the amendment landed; if you see any `MISMATCH`, the number it names is the
entry to fix.

- [ ] **Step 3: Assert the dependency edges are consistent**

Run:

```bash
grep -n "      Consumes:" specs/evidence-linked-theme-extraction-roadmap.md
```

Read every line and confirm each cited stage number is **lower** than the entry
it appears in — no stage consumes a later one. Two lines deserve a second look:

- Stage 7's `not Stage 5` (it must forbid acquisition coupling, not cohort
  coupling).
- Stage 11's `the frozen Stage 5 pilot manifest, split by Stage 6`.

- [ ] **Step 4: Assert nothing was ticked and no stamp was added**

Run:

```bash
grep -c "^- \[x\]" specs/evidence-linked-theme-extraction-roadmap.md
grep -rn "COMPLETE (20" specs/evidence-linked-theme-extraction-roadmap.md specs/evidence-linked-theme-extraction.md
```

Expected: `0` ticked stages, and no `COMPLETE` stamp in either file (the
`Stage N: COMPLETE (YYYY-MM-DD)` template text in §Stage-spec stamp is a
template, not a stamp — it contains `YYYY`, not a year, so it will not match).

- [ ] **Step 5: Confirm no code or dependency changed**

Run:

```bash
git diff --stat 41b7c7c..HEAD -- packages apps pyproject.toml uv.lock
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Expected: empty diff stat for code paths (documentation only); Ruff reporting no
issues. `AGENTS.md` must also be untouched:

```bash
git diff --stat 41b7c7c..HEAD -- AGENTS.md
```

Expected: empty.

- [ ] **Step 6: Review the full diff**

```bash
git diff 41b7c7c..HEAD --stat
```

Expected exactly these seven files, nothing else:

```text
CLAUDE.md
README.md
specs/evidence-linked-theme-extraction-roadmap.md
specs/evidence-linked-theme-extraction.md
specs/plans/1-release-parser-fidelity.md
specs/plans/2-point-in-time-djia-cohort.md
specs/release-parser-fidelity.md
```

`README.md` and `specs/plans/1-release-parser-fidelity.md` will show large
insertion counts — those are Task 1's baseline commits of pre-existing
working-tree content, not amendment edits. To see only the amendment's own diff
for those two, compare against the baseline commits instead of `41b7c7c`.

- [ ] **Step 7: Commit the sweep evidence**

No file changed in this task, so there is nothing to commit unless Steps 1–3
found a mismatch. If they did, fix it and commit:

```bash
git add -A
git commit -m "docs: fix stage references missed by the cohort renumber"
```

If they found nothing, record the sweep's output in the completion report
instead.

---

## Completion

After Task 9 passes, run the **Plan Completion Protocol** from the
`writing-plans` skill:

1. **Resolve-before-defer gate.** Collect skipped steps and unfixed review
   findings. One item is a known candidate: if Task 7 Step 4 was skipped because
   your human partner chose to keep the `stage4_flags` field name, that is a
   deferral needing a `Done when:` condition.
2. **Markup** this file: tick every completed step, add `> Deviation:` notes, and
   add the status header.
3. **Update** `specs/deferred_items.md` (create it with a single
   `# Deferred items` title line if it does not exist).
4. **Backlog triage** via
   `uv run --no-project --python 3.13 python ~/.claude/skills/writing-plans/scripts/deferred_stats.py`.
5. **Retire** this plan to `specs/plans/completed/` with
   `chore(specs): retire plan 2`. **Do not retire
   `specs/point-in-time-djia-cohort.md`** — it stays live in `specs/` as the
   stage spec for Stages 4, 5, and 15. Re-point this file's relative links for
   its new depth when it moves.

**The completion report must state:** that this was an instruction-only change,
that application tests and live extraction were not run, that no stage was
ticked, and that no real DJIA roster, event corpus, parser result, or theme
result was established (`P §Roadmap amendment`).

**What comes next, and what must not.** The roadmap's next unticked stage is
still Stage 1. Stage 4 is now plannable but **not yet buildable**: its `Consumes`
line names Stage 2's contracts, provenance and hashing primitives, and the root
pytest configuration with its registered `live` marker, none of which exist. Work
Stages 1, 2, and 3 in order, then route Stage 4 to `writing-plans` against
`specs/point-in-time-djia-cohort.md`.

**Branch integration.** This branch is the only place the 269-line `README.md` and
this plan are committed, so do not discard it. Run
`finishing-a-development-branch`. Note that `stage-1-release-parser-fidelity` is
also live with Stage 1 execution: both branches need integrating, and if Task 7
ran, its two documents are the only files the two branches both touch.
