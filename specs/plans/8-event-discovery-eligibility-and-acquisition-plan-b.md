# Acquisition and Processing States (Stage 5, plan B) — Implementation Plan

**Status: COMPLETE (2026-09-28)** — executed via executing-plans; nothing deferred

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 5 — on plan
> completion, tick the stage and re-validate later stages against what shipped.
>
> This is plan B of Stage 5's two plans (EV1), and the spec's last. Its completion
> ticks Stage 5, appends the spec's stage stamp, and retires the spec with the plan
> (P8-1).

**Goal:** Build plan B of `specs/event-discovery-eligibility-and-acquisition.md` in
`earnings-ingestion` and `apps/earnings-pipeline`, and acquire the frozen pilot's
releases:

- first, the deferred items from PR #6's review that must land before any
  acquisition or live request, and the design choices F4 and F10 as the user decided
  them on 2026-09-28;
- the processing states of R1.4, and their Parquet table under `data/runs/events/`;
- R1.2's exhibit choice, and `release-content/1`, which confirms an exhibit as its
  slot's release;
- acquisition of each pilot event's release document through the shared SEC client,
  with `set_release_document` overrides and the `corpus_error` guard;
- a synthetic acquisition that replays offline (P-VI), and `events acquire`;
- the live acquisition, after the user approves its count, and its record.

It ends when the pilot's releases are acquired, reviewed, and recorded, and Stage 5 is
ticked.

**Architecture:**

- **Before any request.** Tasks 1 to 10 settle the deferred items that name plan B:
  - the lock directory, redirects, the Item-line reader, and the index page's
    cross-check;
  - the CLIs' paths and request counts;
  - the frozen versions: F22's duplicates, F10's reselection, and F4's rule that
    the build decides which version is current;
  - F20's committed check that no record quotes a saved page.
- **The states** (`packages/earnings-ingestion/src/earnings_ingestion/events/`).
  `states.py` holds R1.4's states, their missing reasons, and the transitions R1.4
  allows. `state_table.py` writes each run's transitions as one Parquet file.
- **The choice and the confirmation.** `exhibits.py` orders a release filing's
  `EX-99*` exhibits as R1.2 does. `content.py` is `release-content/1`: the exhibit's
  canonical text states the slot's period, and its opening announces results.
- **Acquisition.** `acquire.py` records `expected` for each pilot event, tries each
  document's exhibits in order through the fetch it is given, and records `acquired`
  and then `parsed`, `failed`, or `unavailable`. It writes canonical documents under
  `data/runs/events/canonical/`, and a `set_release_document` override in
  `config/corpus/<corpus>/acquisition-overrides.toml` names another exhibit.
- **Commands** (`apps/earnings-pipeline`): `earnings-pipeline events acquire`, which
  reads the current event manifest and pilot (F4), states its request count, and
  opens the shared SEC client with the approved count as its cap.

**Tech Stack:**

- Python 3.14.0 and uv 0.12.15. No new dependency: `uv.lock` does not change.
- Already declared and locked:
  - httpx 0.28.1, through the shared SEC client;
  - lxml 6.1.3, under `walker-1`;
  - Polars 1.44.2, which writes and reads the state table's Parquet with no pyarrow
    or pandas;
  - pydantic 2.13.5, typer 0.27.2, pytest 9.1.1, and Ruff 0.16.8.
- From the standard library: `tomllib`, `json`, `re`, `zoneinfo`, and `collections`.

## The spec this plan implements

The roadmap's Stage 5 entry scopes the stage
(`specs/evidence-linked-theme-extraction-roadmap.md`, Stage 5). Its Consumes line,
reconciled on 2026-09-28 (`277e21b`), names plan 7's Handoffs to plan B and the
deferred items from PR #6's review that plan B must settle first.

- **The stage spec.** `specs/event-discovery-eligibility-and-acquisition.md`, cited
  as `S`, was approved on 2026-09-27. Plan A (plan 7) shipped in PR #6. This plan
  implements plan B:
  - S §Plan B: §Gate, §Exhibit choice, §Content confirmation, §What acquisition can
    change, §Processing states, §Verification (plan B), and §Gates (plan B);
  - S §Commands, as amended here (P8-4);
  - S §Exit criteria: the roadmap's Stage 5 Exit, clause by clause, and §Plan B;
  - S §Rollout, on plan B's completion.
- **Plan A's handoff.** `specs/plans/completed/7-event-discovery-eligibility-and-acquisition-plan-a.md`
  §Handoffs, "To plan B", with its deviation: `frozen_pilots(directory)` takes only
  the directory, and lists every version checked for its hash and name but not its
  chain (`17ce98e`). Plan B reads the pilot it picks through `load_pilot(path,
  universe)`, which checks the chain.
- **The deferred items** (`specs/deferred_items.md`, `## PR #6 review (plan 7)`),
  as the roadmap's Consumes line lists them:
  - two design choices, which the user decided on 2026-09-28: F4, which frozen
    version is current after a revert (P8-4), and F10, whether loading a pilot
    re-derives its selection (P8-3);
  - five that land before the first acquisition or live request: F13, F31 and F35,
    F19 and F38, F29, and F20;
  - three in the code plan B reads: F12 and "Read a primary document with no Item
    line as unread" land here, and P2.1 and P2.2 stay deferred (P8-2);
  - F22 lands with F4, since both decide which frozen version a command reads.
- **The cohort spec.** `specs/point-in-time-djia-cohort.md` (`P`). With plan A, this
  plan closes P-C7's freeze-before-outcomes half and P-VI.
- **`AGENTS.md`** (`A`): A §391–427, the acquisition and access policy, which the
  shared SEC client already implements (R1.3, D5); and A §376, which asks each
  expected but absent document for its `missing_reason`.
- **Out of scope.** Acquiring releases outside the pilot, which is Stage 15's job with
  this plan's adapter. Rerunning the R3.5 check or the layout comparison on the pilot
  releases. Transcripts. Any model call. The other open deferred items, which
  Completion lists.
- **The user's decisions of 2026-09-28.** The planning session put four choices to
  the user, and P8-2, P8-3, P8-4, and the plan-time replay below record the answers.

## Global Constraints

Every task's requirements include these.

**Locators:**

- `A §n` is `AGENTS.md` at line `n`.
- `Rn` are requirements in `specs/evidence-linked-theme-extraction.md`.
- `S` cites `specs/event-discovery-eligibility-and-acquisition.md`, the stage spec:
  - `EV1`–`EV13` are its Decisions rows;
  - `S §Section` cites a section by name;
  - "item n" of S §Verification (plan B) is written `SV n`.
- `P` cites `specs/point-in-time-djia-cohort.md`, as the roadmap does: `P-Cn`,
  `P-VF`, `P-VI`, and `P §Section`.
- `Dn` are the roadmap's decisions, `P6-n` are plan 6's, `P7-n` are plan 7's
  (`specs/plans/completed/7-event-discovery-eligibility-and-acquisition-plan-a.md`),
  and `P8-n` are this plan's, listed below.
- `Fn` and `Pn.n` name the items of `specs/deferred_items.md`,
  `## PR #6 review (plan 7)`, by the review's finding numbers, as the items do.
- **v1** is the frozen cohort,
  `config/universe/djia/manifests/djia-2024q3-2026q2-v1.json`. **events v1** and
  **pilot v1** are `events-v1.json` and `pilot-v1.json` in
  `config/corpus/djia-2024q3-2026q2/`.

**Versions and constants.**

| Name | Value | Where |
| --- | --- | --- |
| Ingestion record schema | `1`, unchanged: the state records join it (P6-5) | `INGESTION_SCHEMA_VERSION` |
| Core schema | `2`, unchanged | `earnings_core` |
| Canonicalization of exhibits | `walker-1`, unchanged | `canonical/` |
| Discovery, eligibility, and selection policies | `release-id/1`, `eligibility/1`, `djia-pilot/1`, unchanged | `events/` |
| Content policy | `release-content/1`, defined here | `events/content.py` (Task 13) |
| Corpus and pilot | `djia-2024q3-2026q2`, and `djia-2024q3-2026q2-pilot` | `config/corpus/djia-2024q3-2026q2/` |
| events v1 | content hash `2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7` | `events-v1.json` |
| pilot v1 | content hash `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926`, 40 events | `pilot-v1.json` |
| Stage 5's store | `data/raw/events/`, source `sec-edgar` (EV12) | `EVENTS_STORE` in `events/build.py` |
| Acquisition overrides | `acquisition-overrides.toml`, beside the frozen records, in no manifest's hash | `OVERRIDES_FILE` in `events/acquire.py` (Task 16) |
| Run outputs | `data/runs/events/`: `states/<run_id>.parquet` and `canonical/<doc_id>.json` | `RUNS_DIR` in `events_cli.py` (Task 19) |
| SEC client | 0.5 s between request starts (2 req/s), shared across SEC hosts; the approved count as each run's cap | `sec/client.py` |

**Offline and no models.**

- Default tests make no network call and no billable call. They need no credential,
  and every acquisition test runs on synthetic data.
- Live tests carry the `live` marker. Each skips without its identity and runs only
  with `-m live`, and only at a human gate. This plan runs none.
- **`EDGAR_IDENTITY` is exported in this shell.** A live test's skip guard does not
  stop it, and it sends real requests. Never pass `-m live` outside a gate. To check
  collection, use `--collect-only`.
- No step calls a model.

**Network access.** Live requests happen only at the gates in "Human gates" below,
each after the user's clear yes in chat, to the count stated.

- Every request goes through `open_sec_client`. Stage 5 adds no throttle of its own
  (R1.3, D5), and makes no web-client request.
- A persistent 403 stops the run. Report it, and never rotate identity (A §404).
- Acquisition fetches exhibits only. Every index page it reads was saved by plan A's
  discovery, and an override's filing is saved by `events discover --filing`, at a
  gate of its own.
- Nothing downloads a dependency, and `uv.lock` does not change.

**Identities.** `EDGAR_IDENTITY` belongs to the user and is configured outside Git.
Never print it, commit it, or record it anywhere. A `Retrieval` record never carries
it.

**Do not touch:**

- Stage 1's frozen harness and records: every file that
  `expirements/parser-fidelity/FROZEN.toml` lists, `tests/fixtures/releases/` and
  its gold, the V1 and V2 records, and ADR 0001.
- `walker-1`: `packages/earnings-ingestion/src/earnings_ingestion/canonical/`,
  `tests/fixtures/canonical/`, and the golden test. Acquisition calls `canonicalize`
  as it is.
- The frozen records: cohort v1 and everything under `config/universe/djia/`;
  events v1, its evidence record, `overrides.toml`, and pilot v1 under
  `config/corpus/djia-2024q3-2026q2/`; and `tests/fixtures/cohort/`, which stays
  byte-identical. Nothing in this plan refreezes or edits them (P-C7). Only the gated
  Task 21 may add `acquisition-overrides.toml` beside them.
- `AGENTS.md`. Other files cite it by line number (`CLAUDE.md` §Gotchas).
- `specs/event-discovery-eligibility-and-acquisition.md`, except Task 9's §Commands
  amendment and Completion's stage stamp.
- `.gitignore`: no edit, and its credentials block stays last. `data/*` already
  ignores `data/raw/events/` and `data/runs/events/`.
- `.python-version`, which pins 3.14.0.

**Stay in the main checkout.** Execute every task in the main checkout, on this
branch, never in a separate worktree. `data/` is gitignored, so a worktree lacks
what these read and write:

- Task 9's offline check, and Tasks 10, 16, and 20's tests, read plan A's saved
  responses under `data/raw/events/sec-edgar/`, and the tests skip without them;
- Task 13's local test reads Stage 1's saved exhibits under `data/raw/discovery/`;
- the live run saves its exhibits there, and writes its states and canonical
  documents under `data/runs/events/`.

Do not rename, move, or hide a `data/` directory to exercise a skip: monkeypatch the
path instead.

**Staging discipline.**

- `git add` only the paths a task names, never `git add -A` or `git add .`.
- After each commit, `git status --short` must print nothing, apart from local
  untracked files that predate this plan. So a later task's file never enters an
  earlier commit.
- `tests/fixtures/events/` is generated, and only Tasks 14 and 18 commit it, as
  `tests/integration/regenerate_event_fixtures.py` writes it.
- `config/corpus/djia-2024q3-2026q2/` changes only at the gated Task 21, and only by
  adding `acquisition-overrides.toml`.

The user may commit on this branch while the plan runs. Run `git log --oneline -3`
before each commit, and never rewrite a commit you did not make.

**Unicode escapes.** Every new or replaced Python file in this plan is ASCII, except
`§` in citations such as `A §404`.

- Tests build non-ASCII inputs from code points with `chr(0x...)`.
- No file carries a backslash-u escape that a tool channel might decode on the way
  to disk.
- Each task that writes Python runs the escape check below. It prints
  `escapes intact`, or else the name of each file holding another non-ASCII
  character.

**Writing files from this plan.** Every code block that holds a whole file follows a
line of one of two forms:

- ``Create `<path>`:``;
- ``Replace `<path>` with:``.

Extract each such file with the helper below rather than retyping it. Retyping
thousands of lines invites silent slips, and a tool channel that decodes an escape
would do it again on a retry. The Preconditions save the two helpers once, as
`/tmp/plan8-extract.py` and `/tmp/plan8-escapes.py`. If `/tmp` has been cleared,
save them again from here.

`/tmp/plan8-extract.py`:

````python
"""Extract one file block from plan 8; run from the repository root.

usage: python3 /tmp/plan8-extract.py <path> [block number, default 1]
"""

import sys
from pathlib import Path

PLAN = Path("specs/plans/8-event-discovery-eligibility-and-acquisition-plan-b.md")
target = sys.argv[1]
wanted = int(sys.argv[2]) if len(sys.argv) > 2 else 1
modes = {
    f"Create `{target}`:": "w",
    f"Replace `{target}` with:": "w",
    f"Append to `{target}`:": "a",
}
lines = PLAN.read_text(encoding="utf-8").splitlines(keepends=True)
found = [(n, modes[line.strip()]) for n, line in enumerate(lines) if line.strip() in modes]
if len(found) < wanted:
    sys.exit(f"{PLAN} has no block {wanted} for {target}")
intro, mode = found[wanted - 1]
start = next(i for i in range(intro + 1, len(lines)) if lines[i].startswith("```"))
ticks = "`" * (len(lines[start]) - len(lines[start].lstrip("`")))
end = next(i for i in range(start + 1, len(lines)) if lines[i].rstrip() == ticks)
path = Path(target)
path.parent.mkdir(parents=True, exist_ok=True)
with path.open(mode, encoding="utf-8", newline="\n") as out:
    out.write("".join(lines[start + 1 : end]))
verb = "appended to" if mode == "a" else "extracted"
print(f"{verb} {target}: {end - start - 1} lines")
````

`/tmp/plan8-escapes.py`:

```python
"""Print each named file holding a non-ASCII character other than the section sign;
print 'escapes intact' when there is none."""

import sys
from pathlib import Path

ALLOWED = {chr(0xA7)}
bad = [
    name
    for name in sys.argv[1:]
    if any(ord(char) > 127 and char not in ALLOWED for char in Path(name).read_text(encoding="utf-8"))
]
print("\n".join(bad) or "escapes intact")
```

- A step that says **extract** a path runs `python3 /tmp/plan8-extract.py <path>`,
  which prints `extracted <path>: <n> lines`. The block number is `1` unless the
  step names another.
- **Edits to existing files.** Most existing files change by exact replacement, not
  whole. The plan gives each such change as a script, ``Create `/tmp/plan8-<name>.py`:``,
  that holds every old and new text. A step that says **apply** `<name>` runs:

  ```bash
  python3 /tmp/plan8-extract.py /tmp/plan8-<name>.py && python3 /tmp/plan8-<name>.py
  ```

  Each old text must match exactly once, and nothing is written unless every
  replacement in the script applies. A file that has drifted from the plan stops the
  script with its path. The script prints `edited <path>: <n> replacement(s)` for
  each file.
- The scripts that edit Markdown files hold those files' non-ASCII characters, such
  as `≥`, `–`, and `—`, as the files do. The escape check reads only the
  repository's Python files.
- If the escape check names a file, extract or apply it again and rerun the check.

**Lint.** `uv run --locked ruff check .` and `uv run --locked ruff format --check .`
pass after every task, and the code below already passes both.

- The Expected `N files already formatted` counts assume a clean checkout: 252
  before Task 1, growing with each task's new Python files.
- A different count with no `Would reformat` line comes from local untracked Python
  files, and is not a failure.

**Expected outputs.** At plan time this plan was replayed on a scratch branch cut
from `277e21b`, in the main checkout, as the user chose: every task through Task 19,
Task 20's test, and Task 22's documents, which the plan then re-applied from its own
blocks to the same trees. Those Expected outputs are what the replay printed. The replay
sent no request, and wrote nothing under the main checkout's `data/` or `config/`.
The scratch branch was deleted once this plan was written.

Tasks 20 to 22 act on live data, so most of their outputs are predictions, marked as
such: the live run's states, the review, and the record. Each of those tasks also
marks its **checks**: outputs that hold whatever the live data say, such as the
default suite's count. A prediction that differs is reported, and is not a failure.
A check that differs stops the task.

Anywhere else, if a count differs while nothing fails, stop and report it rather than
editing a test to match.

**Test imports.** Ruff sorts `earnings_core` and `earnings_ingestion` as third-party
imports in test files, in one block with `pytest`, so keep the imports as written.
Inside `earnings_ingestion` they are first-party.

**Public repository.** `origin` (https://github.com/lowmason/earnings-themes) is
public, so everything committed is published.

- The synthetic exhibits are invented and redistributable. Their wording is modeled
  on Stage 1's saved exhibits, never copied from them.
- The committed records hold facts, URLs, locators, and hashes, never a source's
  wording (P6-3). Task 10's test checks that for every record under
  `config/corpus/`, and each gate runs it.
- Saved SEC responses, the state table, and canonical documents, which hold filings'
  text, stay under the gitignored `data/`. `events acquire` refuses a runs directory
  outside `data/runs/` (P8-13).
- A real `acquisition-overrides.toml` names its reviewer, who is the user.

**Commit attribution.** End each commit message with the attribution line your
session's instructions specify. The commit blocks below omit it deliberately: the
right line names the model actually executing the work.

**Commands.** These recur:

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

- The first is the **default suite**.
- The second is the **harness suite**. No task changes the harness, so it stays at
  its baseline, `280 passed`.
- The third is **lint**.

## Plan decisions

The spec leaves these choices open, so the plan makes them. The user can overturn any
of them before execution. The planning session of 2026-09-28 put four choices to the
user, and P8-2, P8-3, P8-4, and the plan-time replay record the answers. The code
records each decision where it applies. None retunes a rule plan A froze. Where a
rule needed a reading, the reading is stated, and four readings are **flagged for the
user**, because each narrows the spec's words or adds to them: P8-6, P8-8, P8-9, and
P8-11. The user accepted all four as written on 2026-09-28, before execution.

**P8-1 — Plan B completes Stage 5, and the spec retires with it.** EV1 splits the
stage into two plans, and S §Rollout's "plan completion" means plan B's. So
Completion appends S §Rollout's stage stamp, naming plans 7 and 8, ticks Stage 5 in
the roadmap through the roadmap reconcile, and retires the spec to
`specs/completed/` with this plan: no other live plan implements it.

**P8-2 — Which deferred items land, and where (the user's answer on scope).** The
roadmap's Stage 5 Consumes line names ten items of `## PR #6 review (plan 7)`. Tasks
1 to 10 land every one before the first acquisition or live request, except P2.1 and
P2.2:

| Item | Task | What lands |
| --- | --- | --- |
| F29, a relative `EARNINGS_LOCK_DIR` | 1 | `machine_lock_dir()` raises `AccessStop` naming the variable |
| F13, a redirected response | 2 | `SecClient.fetch` refuses a response served from another URL before it is saved; `SavedResponses.get` and the build's citation check refuse one already saved, by raising |
| An Item line missing | 3 | `read_text` reads text with no Item line as unread, and `events build` over such a candidate ends without a traceback |
| F12, the index page against its row | 4 | the index page's form must equal the row's, and the row's primary document must be listed typed as the form, in the build and in discovery before it fetches |
| F19 and F38, the CLIs' paths | 5 | every command that saves fetched bytes refuses a store root outside `data/raw` before any client opens; paths print relative to the repository, or in full |
| F31 and F35, the request counts | 6 | every stop prints "requests sent: N", `OSError` and Ctrl-C included; `cohort fetch-sec` and `verify-live` need `--max-requests`, and the `verify-live` record gains `requests_sent` |
| F22, repeated content and missing evidence | 7 | listing refuses two versions of one content, for event manifests, pilots, and universes, and an event manifest whose evidence record is missing |
| F10 | 8 | P8-3 |
| F4 | 9 | P8-4 |
| F20, the quote check | 10 | P8-5 |
| P2.1 and P2.2, recovering an unusable saved response | none | stays deferred |

- **P2.1 and P2.2 stay deferred.** The user chose to leave store recovery for its own
  plan. Acquisition reports a saved response that cannot be read as a problem naming
  the manual repair, and never fetches it again, so the append-only store is never
  overwritten (`REPAIR` in `events/acquire.py`). Task 22's record documents that
  repair, as the item asks meanwhile.
- **F22 lands with F4.** Both decide which frozen version a command reads, and F4's
  rule needs at most one version per content.
- **Items that stay open.** Every other item of `## PR #6 review (plan 7)` stays open:
  F27, F21, F11 and F24, P5.4, P4.3, P2.3, P4.1, the co-registrant release, and the
  per-candidate citations. None is in acquisition's path. Completion lists them.

**P8-3 — Loading a pilot selects it again (F10; the user's answer).** `load_pilot`
rechecks the chain, as plan 7 made it, and then:

- requires `selection_policy_version == "djia-pilot/1"`, refusing any other before
  selecting, since no other policy exists to rerun;
- runs `select_pilot` over the pilot's event manifest and the universe, and requires
  it to reproduce the pilot's `content_hash`.

So a hand-edited pilot whose content hash was recomputed is refused: a row exchanged
for another event, another policy, another `pilot_id`, or `underfilled` flipped. The
check never compares `universe_version`, since a universe re-versioned with the same
operative hash legitimately differs there (EV4). Loading now depends on the current
selection code: a change to `djia-pilot/1`'s code that changes a selection makes the
frozen pilots it no longer reproduces refuse to load. That is intended, since such a
change must be a new policy version (EV8). events v1 and pilot v1 reload and
reselect unchanged (Task 8).

**P8-4 — The build decides which frozen version is current (F4; the user's
answer).** Plan 7's P7-18 had `events select` read the highest-numbered event
manifest. After a change frozen as v2 and then reverted, `events freeze` said
"unchanged: v1" while `events select` drew a pilot from the withdrawn v2.

- **Event manifests.** `current_events(build, directory)` is the frozen version
  whose content hash the build reproduces. It refuses while the build holds the
  freeze, and when no version holds the content. `events select` and `events
  acquire` rebuild offline, read it, and print its version and hash.
- **Pilots.** `current_pilot(directory, events, universe)` is the pilot frozen over
  the current event manifest, loaded by `load_pilot` (P8-3). It refuses when none
  is, or when more than one is.
- **Universes stay "latest".** The real cohort's rebuild no longer reproduces v1's
  content hash (P7-3), so the build cannot decide a universe. Every consumer keeps
  reading a universe's latest version, and `cohort freeze` refuses a build that
  holds an older version's content: a universe is never reverted.
- **The record.** Task 9 amends S §Commands with this rule, superseding P7-18's
  "latest", and the data dictionary gains the reading notes.
- **The processing states follow.** A document's current state is its latest
  transition under the current pilot's content hash (P8-6), so a revert to an
  earlier pilot never inherits a later pilot's history.

**P8-5 — The quote check (F20).** `tests/integration/test_corpus_quotes.py` checks,
offline, that no string in a corpus's committed records copies a saved page:

- **The records.** Every `events-v*.json`, which includes the evidence records,
  every `pilot-v*.json`, and every `*overrides.toml`, `acquisition-overrides.toml`
  included, in each directory under `config/corpus/`.
- **The pages.** Every saved HTML page, read as `walker-1` text, and every plain-text
  page, as written. A page `walker-1` cannot read, such as the image-only exhibit,
  has no text to quote. The JSON responses, submissions and companyfacts, hold
  facts, not wording, and are not read.
- **The window.** A string fails when any 40-character window of it occurs in a
  page's text. Full dates, such as "September 30, 2024", are masked on both sides
  first, so a date phrase, which is a fact, passes: events v1's `overrides.toml`
  holds a 40-character phrase built around one.
- **Skipping.** The real check skips without `data/raw/events/sec-edgar/`, so it
  does not protect CI. Each gate runs it and reads `passed`. The synthetic check
  always runs, and a rationale that copies 40 characters of a synthetic page fails
  it, while one that copies 39 does not.

**P8-6 — The processing states (a reading of S §Processing states; flagged).**
`events/states.py` holds R1.4's nine states and S's transition table, and adds three
things the table leaves open:

- **Missing reasons for every state in which the document is not at hand** (A §376):

  | State | `missing_reason` |
  | --- | --- |
  | `expected` | `not_yet_checked` |
  | `unavailable` | `not_found`, or `no_confirmed_release` |
  | `restricted` | `rights_restricted` |
  | `failed` | `parse_failed`, with Stage 3's `FailureReason` as `failure_reason` |

  Every other state carries none. S names only `not_found` and
  `no_confirmed_release`; the other three are added so that every expected but
  absent document says why.
- **Reopening.** `unavailable` and `failed` go back to `acquired` only under an
  acquisition override (P8-11), which the transition names. S's table has no such
  row, but S §What acquisition can change lets an override name another exhibit.
- **`restricted` comes from fixtures only.** No source this stage reads forbids
  local processing, since SEC documents are public. `partial`, `completed`, and
  `completed-no-theme` are set by later stages, and fixtures represent them now.
- **Order and chaining.** A document's transitions order by `(recorded_at, run_id,
  sequence)`. The first starts at `expected`, and each comes from the state the one
  before it reached. The current state is the latest transition recorded under the
  current pilot's content hash, and each pilot's transitions chain on their own
  (P8-4).
- **The grain.** One expected document per pilot event, its release, with the ID
  `<event_id>:release`. Each transition records the frozen accession and the one
  acquired, the exhibit, the artifact hash, the retrieval time, the `doc_id`, the
  override, the `corpus_error`, and every exhibit attempt.

**P8-7 — The state table.** `events/state_table.py` holds `StateTransition` rows as a
Polars frame of a fixed schema, so a column that is null in every row keeps its type,
and an exhibit's attempts are a list of structs.

- **One file per run.** `write_run` writes one run's transitions as Parquet to
  `data/runs/events/states/<run_id>.parquet`, through `fetch.store.write_new`: atomic,
  and never replacing a file that holds other bytes. A run that records nothing
  writes nothing.
- **Reading.** `read_runs` reads every run in a directory, refuses a file of another
  schema, and checks that each document's history chains (P8-6).
- **Canonical documents.** A confirmed exhibit's canonical document goes to
  `data/runs/events/canonical/<doc_id>.json`, as `to_fixture_json` writes Stage 3's
  fixtures, through `write_new`.
- **The dictionary.** The state records join ingestion schema version 1 (P6-5), and
  `docs/data-dictionary.md` documents every field and value under its drift test.

**P8-8 — Exhibit choice (a reading of S §Exhibit choice; flagged).** S leaves plan B
"the words" of rule 2. `events/exhibits.py` orders a release filing's exhibits typed
`EX-99*` on its saved index page, each group by sequence number:

1. `named`: each whose number the Item 2.02 text names, in "Exhibit 99.1",
   "Exhibit No. 99.1", or a list such as "Exhibits 99.1 and 99.2";
2. `described`: each whose description on the index page has the word "release",
   as a whole word, so "Press release" and "Earnings release" count and "Released"
   does not;
3. `lowest_sequence`: the rest.

Three readings:

- **A number is 99 and an integer sub-number.** So "99.01" names `EX-99.1`, and
  "Exhibit 99" names `EX-99` alone, never `EX-99.1`.
- **Only the Item 2.02 sections are read**, as `release-id/1` reads them, never Item
  9.01's list, which names every exhibit.
- **Every exhibit is a candidate**, in that order, so a first choice that is not
  confirmed yields to the next (S §Content confirmation).

On the real pilot, 37 of the 40 release filings' first choices are named, and 3 are
by lowest sequence: Verizon's two filings, each with one `EX-99`, and Procter &
Gamble's.

**P8-9 — `release-content/1` (a reading of S §Content confirmation; flagged).** S
leaves plan B the vocabulary. An exhibit that `walker-1` canonicalized is confirmed
when both hold:

- **The period.** Its whole canonical text states the slot's period as
  `release-id/1` reads a statement: a full date after "ended" or "ending" that is the
  period end, or a fiscal period that matches the slot's labels, judged only for
  `Q1`, `Q2`, `Q3`, and `FY` (`release.states_period`, which Task 13 makes public).
  The whole text is read, since a release's tables often carry the date.
- **The announcement.** Its opening, the first 12 heading, paragraph, and list-item
  elements joined by spaces, announces results: "report", "announce", "post", or
  "deliver", in a form the pattern lists, then within 160 characters, with no full
  stop between, "results", "earnings", "net income", "net earnings", "net loss",
  "net sales", "revenue", "sales", "profit", or "EPS", in any case.

Stage 1's 168 saved exhibits fixed the vocabulary, locally: it rejects the six that
are not releases, V2's AMC pro forma overview among them, and confirms 156 of the
162 releases. Every one of the 168 states some period, so the twelve it rejects
are exactly those whose openings announce nothing the pattern reads. A real release
missed that way would be `unavailable` with `no_confirmed_release` until the review's
override names it (P8-11). Stage 1's eight committed releases and the synthetic
exhibits pin the rule in the default suite. A local test over the 168, which Stage 1
saved under `data/raw/discovery/`, pins the twelve, and skips without them.

**P8-10 — The synthetic layer's exhibits.** Plan A's synthetic event layer names each
candidate's exhibits on its index page, but serves none. Task 14 adds the exhibits
acquisition fetches, `layer.exhibit_bodies()`, and Task 18 adds
`synthetic.serve(bodies, retrieved_at)`, a fake fetch that answers each exhibit's URL
and refuses any other with `UnexpectedResponse`, as SEC refuses a missing page. The
cases, each on an eligible pilot event:

| Case | Event | What acquisition does |
| --- | --- | --- |
| Two exhibits, the first a supplement | Acme, 2025-09-25 | EX-99.1, the supplement, is not confirmed, and EX-99.2, the release, is: the Item 2.02 text names both |
| `EX-99` numbering | Eastfield, 2025-10-17 | the only exhibit is `EX-99` |
| `EX-99.01` numbering, and the AMC-like overview | Corvid, 2025-07-30 | the overview announces nothing: `unavailable`, `no_confirmed_release` |
| A narrative-only release | Dynamo, 2025-10-21 | a release with no table is confirmed |
| An image-only exhibit | Eastfield, 2026-04-17 | `walker-1` finds no text: `failed`, `parse_failed`, `no_native_text` |
| An exhibit SEC never serves | Dynamo, 2025-04-22 | `unavailable`, `not_found` |

Every other event's exhibit is its release. Regenerating the fixture changes two
index pages, two primary documents, and the evidence record, and leaves the event
manifest's and the pilot's content hashes unchanged.

**P8-11 — Acquisition overrides (a reading of S §What acquisition can change;
flagged).** A signed `set_release_document` override names an event's release
document.

- **Where.** `config/corpus/<corpus_id>/acquisition-overrides.toml`, beside the
  frozen records. No manifest hashes it, since P-C7 forbids acquisition to edit a
  frozen record. It holds at most one override per event.
- **What it names.** An exhibit of the frozen release filing, or of another filing
  by the issuer. That filing's index page must be saved: `events discover --filing
  CIK ACCESSION` saves it, at a gate. The override cites the page, as plan A's
  overrides are checked (`build.citations_refused`).
- **What it decides.** Its document is the release once it canonicalizes.
  `release-content/1`'s verdict is recorded in the attempt, and does not decide, since
  the reviewer has read the exhibit.
- **The `corpus_error` guard.** When the other filing's acceptance time would change
  the event's eligibility under `eligibility/1`, each of its transitions marks a
  `corpus_error` for the next corpus version, and nothing is fixed in place. In v1 no
  release lies near a membership change, so this is a guard.
- **When it applies.** To a document that is `expected`, `acquired`, `unavailable`, or
  `failed`. One that is `parsed` is a problem, as is an override that does not check;
  its document is not attempted.

**P8-12 — Requests.** Acquisition sends only through the fetch it is given.

- **Only the CLI opens the client** (P6-22, D5). `fetch/responses.py` holds `Fetched`
  and `UnexpectedResponse`, which `fetch/client.py` returns and raises, and loads no
  network library. So discovery and acquisition import them from there, and the
  import scan needs no allowance.
- **What counts as an attempt.** `UnexpectedResponse`, a status other than 200, an
  unexpected media type, or a redirect (F13), makes that exhibit's attempt
  `not_fetched`, and the next exhibit is tried. `AccessStop` ends the run: its
  transitions so far are written, and every document not attempted stays `expected`.
- **Exhibits only.** Acquisition saves exhibits, never an index page or a primary
  document, so it never changes what the event build reads, and the build still
  reproduces events v1 after it (P8-4).
- **The count.** `planned_requests` gives two numbers before anything is sent: the
  first choices not saved, and every candidate not saved, over the documents a run
  would attempt, an override's document counting as both. The second is the most a
  run can send. On the real pilot, offline, it gives `(40, 56)`: 40 release filings
  list 56 `EX-99*` exhibits. So the live gate's count is 56, inside S's "about 40 to
  60".

**P8-13 — `events acquire`.**

- **What it reads.** It rebuilds offline and reads the current event manifest and the
  pilot frozen over it (P8-4), and the acquisition overrides. It prints each one's
  version and hash, and refuses when any does not load.
- **The count.** It prints "at most N requests to SEC, through the shared client; F
  first choices". With N at 0 it opens no client. Otherwise it needs
  `--max-requests`, the count the user approved, which becomes the client's cap.
- **Paths.** It refuses a store root outside `data/raw` (F19) and a runs directory
  outside `data/runs`, since canonical documents hold filings' text and stay out of
  Git.
- **Output.** One line per pilot document, in selection order, with its state and
  reasons; a `corpus_error` line where one is marked; the counts by state; "fetched
  N; requests sent: M"; and the run's file. Every stop prints "requests sent: N; a
  rerun attempts what is left". A problem prints as a `problem:` line and exits 1.
- **Reruns.** A rerun attempts only documents still `expected` or `acquired`, and
  fetches only exhibits not saved.

## Requirement map

S §Verification (plan B), item by item:

| Item | What shows it | Task |
| --- | --- | --- |
| SV 1: `events acquire` refuses without a frozen pilot whose chain checks | `test_acquire_refuses_without_a_pilot_over_the_current_manifest`; `test_acquire_refuses_a_pilot_djia_pilot_1_does_not_reselect`; `test_a_pilot_not_frozen_over_the_manifest_is_refused`; and the chain itself: `test_loading_selects_again`, `test_the_build_decides_which_version_is_current` | 8, 9, 16, 19 |
| SV 2: `EX-99`, `EX-99.1`, and `EX-99.01` numbering | `test_each_numbering_is_named`; `test_plan_b_s_exhibit_numbering`; `test_each_case_comes_to_its_state` | 12, 14, 16 |
| SV 2: a narrative-only release | `test_the_narrative_release_has_no_table`; `test_each_case_comes_to_its_state` | 14, 16 |
| SV 2: a first choice that fails, and a next exhibit that confirms | `test_named_exhibits_come_first_by_sequence`; `test_each_case_comes_to_its_state` (Acme's supplement, then its release) | 12, 16 |
| SV 2: the AMC-like overview fails | `test_an_overview_that_announces_nothing_is_not_confirmed`; `test_stage_1_s_saved_exhibits_are_judged_as_before`, locally; `test_each_case_comes_to_its_state` (Corvid) | 13, 16 |
| SV 3: every R1.4 state from fixtures, and every expected but absent document's `missing_reason` | `test_every_state_is_represented_from_fixtures`; `test_a_state_carries_its_own_details`; `test_only_the_transitions_r1_4_allows`; `test_a_history_must_chain` | 11 |
| SV 4: P-C7, after acquisition, a `failed` parse, and later stages' states | `test_acquisition_changes_no_frozen_record_and_the_build_still_decides`; `test_p_vi_replays_the_acquisition_offline`, which writes `partial`, `completed`, and `completed-no-theme` after the replay and finds the frozen records byte-identical, with every event still selected | 16, 18 |
| SV 5: only the shared client, with no throttle of its own; a 403 stops the run and leaves the rest `expected` | `test_stage_5_opens_no_client_of_its_own`; `test_stage_5_has_no_client_or_throttle_of_its_own`; `test_acquire_fetches_through_the_shared_client_within_its_count`; `test_a_persistent_403_stops_the_run_and_leaves_the_rest_expected`; `test_acquire_stops_on_a_persistent_403_and_leaves_the_rest_expected` | 15, 16, 19 |
| SV 6: offline replay reproduces the states | `test_p_vi_replays_the_acquisition_offline`, on the synthetic store; `test_offline_replay_reproduces_the_live_acquisition`, on the real store after the live run | 18, 20 |
| SV 7: the suites pass, and `uv.lock` does not change | each task's checks | all |

S §Exit criteria, §Plan B:

| Exit item | Where | Task |
| --- | --- | --- |
| 1. SV 1 to 6 pass | the table above | 8 to 20 |
| 2. The pilot's releases are acquired after the gate, and the record gains the run | `data/runs/events/` (local); `docs/verification/djia-events.md` | 20, 21, 22 |
| 3. The default suite, the harness suite, and Ruff pass | each task's checks | all |

The roadmap's Stage 5 Exit clauses that plan B meets (S §Exit criteria, "clause by
clause"):

| Clause | Where | Task |
| --- | --- | --- |
| The pilot is unchanged after acquisition and parser statuses change (P-C7) | SV 4 | 16, 18 |
| A selected event stays selected when a later step fails | SV 4 | 18 |
| Offline replay identifies releases, including a narrative-only one and alternative numbering (R1.1, R1.2), for exhibits | SV 2 | 12 to 16 |
| The adapter sends only through the shared client (R1.3, D5) | SV 5 | 15, 16, 19 |
| Every R1.4 state is represented from fixtures | SV 3 | 11 |

The deferred items that land (P8-2):

| Item | What shows it | Task |
| --- | --- | --- |
| F29 | `test_a_relative_lock_directory_is_refused` | 1 |
| F13 | `test_a_redirected_response_is_refused_before_it_is_saved`; `test_a_redirected_record_is_refused_where_it_is_read` | 2 |
| No Item line | `test_a_text_with_no_item_line_at_all_states_nothing`; `test_a_candidate_with_no_item_line_builds` | 3 |
| F12 | `test_an_index_page_of_another_form_is_a_problem`; `test_a_row_whose_primary_document_the_index_does_not_type_as_its_form`; `test_discover_filing_checks_the_index_page_before_it_fetches_the_document` | 4 |
| F19 and F38 | `test_a_fetching_command_refuses_a_store_outside_data_raw`; `test_discover_refuses_a_store_outside_data_raw`; `test_freeze_prints_a_manifest_outside_the_repo_in_full`; `test_freeze_and_select_print_a_corpus_outside_the_repo_in_full`; `test_a_store_under_a_symlinked_data_directory_is_under_data_raw` | 5 |
| F31 and F35 | `test_discover_prints_its_count_when_saving_fails`; `test_discover_prints_its_count_when_a_saved_body_is_gone`; `test_discover_prints_its_count_on_ctrl_c`; `test_a_live_command_needs_the_approved_count`; `test_verify_live_prints_its_count_when_it_stops`; `test_run_live_caps_each_client_and_records_what_both_sent` | 6 |
| F22 | `test_two_versions_of_one_content_are_refused`, for event manifests with pilots, and for universes; `test_a_manifest_without_its_evidence_is_refused` | 7 |
| F10 | `test_loading_selects_again`, with four tamperings; `test_a_pilot_with_a_row_swapped_for_another_eligible_event_is_refused`, on events v1 and pilot v1 | 8 |
| F4 | `test_the_build_decides_which_version_is_current`, which freezes v1 and a changed v2, reverts, and reads v1; `test_select_reads_the_version_the_build_reproduces`; `test_no_current_version_without_a_frozen_one_that_holds_the_build`; `test_a_revert_to_an_older_version_is_refused` and `test_freeze_refuses_a_revert`, for universes | 9 |
| F20 | `test_the_real_corpus_records_quote_no_saved_page`, at each gate; `test_the_synthetic_corpus_records_quote_no_saved_page`; `test_a_rationale_that_copies_40_characters_is_caught` | 10 |

## Human gates

S §Gates (plan B), with the stops that the real data can force:

| Gate | When | Who | What it unblocks |
| --- | --- | --- | --- |
| The live acquisition | Task 20, Steps 6 and 7 | user | `events acquire --max-requests 56`: at most 56 SEC requests through the shared client, as `EDGAR_IDENTITY`, of which 40 are first choices. `planned_requests` derived both offline (P8-12), and `events acquire` states them again before it opens the client. |
| A rerun of acquisition | Task 20, whenever acquisition stops | user | The rerun and its count, which `events acquire` states before it sends anything. A persistent 403 is reported and never retried with another identity (A §404). |
| The review | Task 21, Steps 1 and 2 | user | The decision on each document that is not `parsed`: accept its state, or write a `set_release_document` override, with its rationale in the user's words and the user's signature |
| One filing's pages | Task 21, whenever an override names a filing whose index page is not saved | user | `events discover --filing CIK ACCESSION`: at most 2 requests for each filing |
| The override's acquisition | Task 21, Step 4 | user | `events acquire` again, at the count it states: at most one request per override |
| A stop no override answers | Task 20 or 21, whenever `events acquire` prints a `problem:` line for a saved response that cannot be read | user | A stop. The repair is by hand (P8-2), and P2.1 and P2.2 stay deferred |
| The record | Task 22, Step 2 | user | `docs/verification/djia-events.md`'s acquisition sections, which the user reads before they are committed: the requests by gate, the states by count, the overrides, the failures, and that no model was called |

- **No `-m live` test.** No task runs one. `EDGAR_IDENTITY` is exported, so such a
  run would send real requests and need a gate of its own.
- **Hard stops.** In subagent-driven execution, every gate runs in the controller
  session with the user, never in a subagent. Each gate is a hard stop: nothing after
  it starts until the user has answered. A subagent that reaches a gate stops and
  reports back instead.

## File map

`…/fetch/`, `…/sec/`, `…/cohort/`, and `…/events/` below are under
`packages/earnings-ingestion/src/earnings_ingestion/`; `…/tests/` is
`packages/earnings-ingestion/tests/`; and `…/pipeline/` is
`apps/earnings-pipeline/src/earnings_pipeline/`, with its tests in
`apps/earnings-pipeline/tests/`.

| Path | Responsibility | Task |
| --- | --- | --- |
| `…/fetch/client.py`; `…/tests/test_fetch_client.py` | A relative lock directory is refused | 1 |
| `…/sec/client.py`, `…/events/saved.py`, `…/events/build.py`; `…/tests/test_sec_client.py`, `test_events_build.py` | Redirected responses | 2 |
| `…/events/release.py`; `…/tests/test_events_release.py`, `test_events_build.py` | Text with no Item line | 3 |
| `…/events/filings.py`, `discover.py`, `build.py`; `…/tests/test_events_filings.py`, `test_events_discover.py`; `test_events_cli.py` | The index page against its row | 4 |
| `…/pipeline/paths.py`, `cohort_cli.py`, `events_cli.py`; `test_paths.py`, `test_cohort_cli.py`, `test_events_cli.py` | The CLIs' paths | 5, 19 |
| `…/pipeline/cohort_cli.py`, `events_cli.py`; `…/cohort/live.py`, `records.py`; `…/tests/test_cohort_live.py`; `tests/integration/test_cohort_live.py`; `docs/data-dictionary.md` | Request counts on every stop, and approved counts | 6 |
| `…/cohort/freeze.py`, `…/events/freeze.py`, `pilot.py`; `…/tests/test_cohort_build.py`, `test_events_freeze.py`, `test_events_pilot.py`; `tests/integration/test_event_corpus_v1.py`; `…/pipeline/cohort_cli.py`, `events_cli.py`; `docs/data-dictionary.md`; `specs/event-discovery-eligibility-and-acquisition.md` (§Commands) | F22, F10, and F4 | 7, 8, 9 |
| `tests/integration/test_corpus_quotes.py` | The quote check | 10, 18 |
| `…/events/states.py`, `state_table.py`; `…/tests/test_events_states.py`, `test_events_state_table.py`; `docs/data-dictionary.md`, `tests/contracts/test_data_dictionary.py` | The processing states and their table | 11 |
| `…/events/exhibits.py`; `…/tests/test_events_exhibits.py` | Exhibit choice | 12 |
| `…/events/content.py`, `release.py`; `…/tests/test_events_content.py` | `release-content/1` | 13 |
| `…/events/layer.py`, `synthetic.py`; `…/tests/test_events_layer.py`; `tests/fixtures/events/` (generated) | The synthetic exhibits, and `serve` | 14, 18 |
| `…/fetch/responses.py`, `client.py`; `…/events/discover.py`; `…/tests/test_import_boundaries.py`; `tests/contracts/test_import_scan.py` | The fetched record without a client | 15, 16 |
| `…/events/acquire.py`; `…/tests/test_events_acquire.py`; `tests/integration/test_event_store_v1.py` | Acquisition, and the real store's checks | 16, 17, 19, 20 |
| `…/events/records.py`, `build.py`; `…/tests/test_events_records.py`; `docs/data-dictionary.md`, `tests/contracts/test_data_dictionary.py` | Acquisition overrides | 17 |
| `…/events/fixture.py`; `tests/integration/test_event_fixtures.py`; `tests/fixtures/events/acquisition.json` (generated) | The synthetic acquisition, replayed offline | 18 |
| `…/pipeline/events_cli.py`; `test_events_cli.py` | `events acquire` | 19 |
| `config/corpus/djia-2024q3-2026q2/acquisition-overrides.toml` | The reviewed acquisition overrides, if the review writes any | 21 |
| `docs/verification/djia-events.md`; `CLAUDE.md`; `README.md` | The record and the current state | 22 |
| `data/raw/events/`, `data/runs/events/` | The saved exhibits, the state table, and the canonical documents: local and uncommitted | 20, 21 |

No other file changes, and `uv.lock` does not change.

## Preconditions — read before Task 1

- **Branch.** Work on `stage-5-plan-b-acquisition` in the main checkout. At planning
  time its commits above `main` (`0379fd5`) were the roadmap reconcile (`277e21b`)
  and this plan's commit, and the branch was unpushed. Run this and read the result:

  ```bash
  git switch stage-5-plan-b-acquisition && git log --oneline -3 && git status --short
  ```

  Expected: the head is `docs(plan): plan 8, Stage 5 plan B: acquisition and processing states`,
  or a later commit the user made, and the status is empty.
- **Stay in the main checkout** (Global Constraints). Do not execute in a separate
  worktree.
- **Environment.** Run `uv sync --locked --all-packages`; the `dev` group syncs by
  default.
  - `uv --version` must print uv 0.12.15.
  - The interpreter is Python 3.14.0, pinned by `.python-version`.
- **Helpers.** Save the two helpers from Global Constraints, then check both:

  ```bash
  python3 /tmp/plan8-extract.py docs/no-such-file.md; python3 /tmp/plan8-escapes.py specs/plans/8-event-discovery-eligibility-and-acquisition-plan-b.md
  ```

  Expected: `specs/plans/8-event-discovery-eligibility-and-acquisition-plan-b.md has no block 1 for docs/no-such-file.md`,
  then the plan's own path. The plan holds non-ASCII characters, so this shows that
  the check works.
- **Baselines:**

  ```bash
  uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
  uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
  uv run --locked ruff check . && uv run --locked ruff format --check .
  uv run --locked --all-packages python expirements/parser-fidelity/fetch_policy_pages.py verify
  ```

  Expected: `1368 passed, 24 deselected`; `280 passed`; `All checks passed!` and
  `252 files already formatted`; `register quotes verified`.

  If the harness reports 278 passed and 2 skipped, the rendered copies are missing:
  stop and ask.
- **Local data.** These must exist. If any is missing, stop and ask:
  - `data/raw/events/sec-edgar/`, plan A's saved responses: the index pages of the
    pilot's release filings, and their Item 2.02 text, which acquisition reads, and
    which Tasks 10, 16, and 20's tests read;
  - `data/raw/discovery/`, Stage 1's saved pages, whose 168 exhibits Task 13's local
    test reads;
  - `config/corpus/djia-2024q3-2026q2/` with events v1, its evidence record,
    `overrides.toml`, and pilot v1, all committed.

  `data/runs/events/` need not exist: the live run creates it.
- **Identity.** Check it without printing it:

  ```bash
  [ -n "$(printenv EDGAR_IDENTITY)" ] && echo "EDGAR_IDENTITY set" || echo "EDGAR_IDENTITY unset"
  ```

  Only the gates need it. If it is set, remember that a `-m live` run really reaches
  SEC (Global Constraints).

---

### Task 1: Refuse a relative lock directory (F29)

PR #6's review, F29. `machine_lock_dir()` returned `$EARNINGS_LOCK_DIR` as given, so a
relative value resolved against each process's working directory: two checkouts would
take two SEC locks, and together could send 4 requests a second against the project's
2 per machine (R1.3). The variable is a test override (P7-5). It must now be absolute,
and a relative one raises `AccessStop`, which every CLI already reports as a stop,
before plan B's first live request.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py`.
- Test (modify, by exact replacement):
  `packages/earnings-ingestion/tests/test_fetch_client.py`.

**Interfaces:**

- Consumes: plan 7's `machine_lock_dir() -> Path`, `LOCK_DIR_VARIABLE`, and
  `AccessStop` in `fetch/client.py`.
- Produces: `machine_lock_dir()` raises `AccessStop` naming `EARNINGS_LOCK_DIR` for a
  relative value.

- [x] **Step 1: Write the failing test**

Create `/tmp/plan8-task1-tests.py`:

```python
"""Plan 8: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_fetch_client.py": [
        (
            "def test_concurrent_workers_share_one_allowance() -> None:\n",
            "def test_a_relative_lock_directory_is_refused(monkeypatch) -> None:\n"
            "    \"\"\"A relative override would resolve against each process's working directory,\n"
            "    so two checkouts would hold two SEC locks and could send twice the project's\n"
            "    rate between them (PR #6's review, F29).\"\"\"\n"
            "    monkeypatch.setenv(LOCK_DIR_VARIABLE, \".locks\")\n"
            "    with pytest.raises(AccessStop, match=LOCK_DIR_VARIABLE):\n"
            "        machine_lock_dir()\n"
            "\n"
            "\n"
            "def test_concurrent_workers_share_one_allowance() -> None:\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task1-tests`.

- [x] **Step 2: Run the test to verify it fails**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_client.py -q`

Expected: FAIL: `1 failed, 19 passed`, with `Failed: DID NOT RAISE AccessStop`.

- [x] **Step 3: Refuse the relative value**

Create `/tmp/plan8-task1-source.py`:

```python
"""Plan 8: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py": [
        (
            "    ``$EARNINGS_LOCK_DIR`` overrides it, for tests. Otherwise it is the user's cache:\n",
            "    ``$EARNINGS_LOCK_DIR`` overrides it, for tests, and must be absolute: a relative\n"
            "    value would resolve against each process's working directory, so two checkouts\n"
            "    would take two locks (PR #6's review, F29). Otherwise it is the user's cache:\n",
        ),
        (
            "        return Path(override)\n",
            "        if not Path(override).is_absolute():\n"
            "            raise AccessStop(\n"
            "                f\"{LOCK_DIR_VARIABLE} must be an absolute path, not {override!r}\"\n"
            "            )\n"
            "        return Path(override)\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task1-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_client.py -q`

Expected: `20 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py packages/earnings-ingestion/tests/test_fetch_client.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1369 passed, 24 deselected`; `All checks passed!` and
`252 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py packages/earnings-ingestion/tests/test_fetch_client.py
git commit -m "fix(fetch): refuse a relative EARNINGS_LOCK_DIR (F29)"
```

---

### Task 2: Refuse a redirected response (F13)

PR #6's review, F13. The shared client follows redirects within SEC's hosts and
records `final_url`, but nothing read it. `SavedResponses` served each retrieval under
its `request_url`, and the build's citation check accepted a citation grounded in a
redirected record. So a primary document that redirected elsewhere was read as the
candidate's 8-K and cited under the URL requested. Plan B's exhibits become canonical
text, so this lands before the first acquisition:

- `SecClient.fetch` refuses a response SEC served from another URL, with
  `UnexpectedResponse`, before it is saved.
- `SavedResponses.get` raises `ValueError` when a URL's newest retrieval was
  redirected. It never skips it: the URL stays among the saved ones, so discovery
  never fetches it again, and every reader reports it.
- `_citations_refused` in `events/build.py` refuses a citation whose URL's retrievals
  were all redirected.

None of the 661 records saved behind events v1 was redirected, so v1 rebuilds
unchanged.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/sec/client.py`,
  `events/saved.py`, and `events/build.py`.
- Test (modify, by exact replacement):
  `packages/earnings-ingestion/tests/test_sec_client.py` and `test_events_build.py`.

**Interfaces:**

- Consumes: `PoliteClient.fetch(url, expected_types) -> Fetched`, `Fetched`, and
  `UnexpectedResponse` in `fetch/client.py`; `Retrieval.request_url` and
  `final_url` in `fetch/records.py`.
- Produces: `SecClient.fetch(url, expected_types) -> Fetched`, which raises
  `UnexpectedResponse` on a redirect; `SavedResponses.get(url)`, which raises
  `ValueError` on a redirected record.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task2-tests.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_events_build.py": [
        (
            "from earnings_ingestion.cohort.freeze import load_manifest\n",
            "from earnings_core import RightsStatus, sha256_hex\n"
            "from earnings_ingestion.cohort.freeze import load_manifest\n"
            "from earnings_ingestion.cohort.locators import ArtifactText\n",
        ),
        (
            "from earnings_ingestion.sec.urls import (\n",
            "from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod\n"
            "from earnings_ingestion.sec.urls import (\n",
        ),
        (
            "def test_a_filing_accepted_after_the_cutoff_is_refused(universe, tmp_path) -> None:\n",
            "def redirected(layer: SyntheticStore, url: str, body: bytes) -> None:\n"
            "    \"\"\"Save ``body`` as a retrieval of ``url`` that SEC answered from another URL.\"\"\"\n"
            "    record = Retrieval(\n"
            "        request_url=url,\n"
            "        final_url=f\"{url}.moved\",\n"
            "        retrieved_at=datetime(2026, 9, 29, tzinfo=UTC),\n"
            "        retrieval_method=RetrievalMethod.HTTP,\n"
            "        http_status=200,\n"
            "        media_type=\"text/html\",\n"
            "        content_type=\"text/html\",\n"
            "        byte_count=len(body),\n"
            "        sha256=sha256_hex(body),\n"
            "    )\n"
            "    layer.store.put(\n"
            "        \"sec-edgar\",\n"
            "        body,\n"
            "        record,\n"
            "        rights_status=RightsStatus.LOCAL_ONLY,\n"
            "        rights_basis=\"synthetic\",\n"
            "    )\n"
            "\n"
            "\n"
            "def test_a_redirected_record_is_refused_where_it_is_read(universe, tmp_path) -> None:\n"
            "    \"\"\"A saved response whose retrieval was redirected is refused by raising, never\n"
            "    skipped, so discovery never fetches it again, and it grounds no citation (PR\n"
            "    #6's review, F13).\"\"\"\n"
            "    layer = write_layer(tmp_path / \"data\" / \"raw\" / \"events\", tmp_path)\n"
            "    good = choose(layer, ACME_SET, ACME, \"2025-03-20 16:05:00\")\n"
            "    folder = archive_url(ACME.cik, good.accession, \"\")\n"
            "    moved = f\"{folder}moved.htm\"\n"
            "    body = b\"<html><body><p>Accepted 2025-03-20 16:05:00</p></body></html>\"\n"
            "    redirected(layer, moved, body)\n"
            "    saved = SavedResponses(layer.store)\n"
            "    assert moved in saved\n"
            "    with pytest.raises(ValueError, match=\"redirected\"):\n"
            "        saved.get(moved)\n"
            "    artifact = ArtifactText(body, \"text/html\")\n"
            "    citation = OverrideCitation(\n"
            "        source_id=\"sec-edgar\",\n"
            "        url=moved,\n"
            "        artifact_sha256=sha256_hex(body),\n"
            "        locator=artifact.find(\"2025-03-20 16:05:00\"),\n"
            "    )\n"
            "    assert refused(\n"
            "        universe, layer, good.model_copy(update={\"citations\": (citation,)})\n"
            "    ) == (\n"
            "        (f\"release-cik-0009990001-2025-02-28: {moved} was redirected to {moved}.moved\"),\n"
            "    )\n"
            "    page = filing_index_url(ACME.cik, good.accession)\n"
            "    redirected(layer, page, SavedResponses(layer.store).get(page).text.body)\n"
            "    problems = refused(universe, layer)\n"
            "    assert (\n"
            "        f\"{page}: it was redirected to {page}.moved, and a redirected response is\"\n"
            "        \" never read\"\n"
            "    ) in problems\n"
            "\n"
            "\n"
            "def test_a_filing_accepted_after_the_cutoff_is_refused(universe, tmp_path) -> None:\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_sec_client.py": [
        (
            "from earnings_ingestion.fetch.client import AccessStop, machine_lock_dir\n",
            "from earnings_ingestion.fetch.client import (\n"
            "    AccessStop,\n"
            "    UnexpectedResponse,\n"
            "    machine_lock_dir,\n"
            ")\n",
        ),
        (
            "        client.fetch(submissions_url(\"320193\"), {\"application/json\"})\n",
            "        client.fetch(submissions_url(\"320193\"), {\"application/json\"})\n"
            "\n"
            "\n"
            "def test_a_redirected_response_is_refused_before_it_is_saved() -> None:\n"
            "    \"\"\"A response served from another URL than the one requested is never saved or\n"
            "    read under the URL requested (PR #6's review, F13).\"\"\"\n"
            "\n"
            "    def handler(request):\n"
            "        if request.url.path == \"/moved.htm\":\n"
            "            return httpx.Response(\n"
            "                301, headers={\"Location\": \"https://www.sec.gov/other.htm\"}\n"
            "            )\n"
            "        return httpx.Response(200, headers={\"Content-Type\": \"text/html\"}, text=\"x\")\n"
            "\n"
            "    with (\n"
            "        opened(handler) as client,\n"
            "        pytest.raises(\n"
            "            UnexpectedResponse, match=\"redirected to https://www.sec.gov/other.htm\"\n"
            "        ),\n"
            "    ):\n"
            "        client.fetch(\"https://www.sec.gov/moved.htm\", {\"text/html\"})\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task2-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_build.py packages/earnings-ingestion/tests/test_sec_client.py -q`

Expected: FAIL: `2 failed, 54 passed`. The client saves the redirected response
(`Failed: DID NOT RAISE UnexpectedResponse`), and the build reads the redirected
record (`Failed: DID NOT RAISE ValueError`).

- [x] **Step 3: Refuse a redirect when fetched and when read**

> Deviation: after the final review (`55ea811`), `SecClient.fetch` also refuses a redirect without end (httpx's `TooManyRedirects`) and a body that cannot be decoded (`DecodingError`) as `UnexpectedResponse`, since httpx raises them as neither a transport error nor a refusal any caller caught.

Create `/tmp/plan8-task2-source.py`:

```python
"""Plan 8: exact replacements for 3 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/build.py": [
        (
            "    hashed; or, with the named filing's ``folder``, no citation there of an SEC\n"
            "    artifact retrieved from its own URL, at a locator that verifies.\"\"\"\n",
            "    hashed, or a cited URL whose retrievals were all redirected (F13); or, with the\n"
            "    named filing's ``folder``, no citation there of an SEC artifact retrieved from its\n"
            "    own URL, unredirected, at a locator that verifies.\"\"\"\n",
        ),
        (
            "        grounded |= (\n"
            "            inside\n"
            "            and citation.locator is not None\n"
            "            and any(r.request_url == citation.url for r in stored.retrievals)\n"
            "        )\n",
            "        own = [r for r in stored.retrievals if r.request_url == citation.url]\n"
            "        if own and all(r.final_url != r.request_url for r in own):\n"
            "            refused.append(\n"
            "                f\"{override.override_id}: {citation.url} was redirected to\"\n"
            "                f\" {own[-1].final_url}\"\n"
            "            )\n"
            "            failed |= inside\n"
            "            continue\n"
            "        grounded |= inside and citation.locator is not None and bool(own)\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/saved.py": [
        (
            "SEC's records (``cohort.register.SEC_RIGHTS``).\n"
            "\"\"\"\n"
            "\n",
            "SEC's records (``cohort.register.SEC_RIGHTS``).\n"
            "\n"
            "A response whose newest retrieval was redirected is refused by raising, never\n"
            "skipped: it stays among the saved URLs, so discovery never fetches it again, and\n"
            "every reader reports it (PR #6's review, F13). The shared SEC client refuses a\n"
            "redirect before it is saved, so only a record saved before that check can be one.\n"
            "\"\"\"\n"
            "\n",
        ),
        (
            "        ``FileNotFoundError`` or ``ValueError`` if its bytes are gone or changed.\"\"\"\n",
            "        ``FileNotFoundError`` or ``ValueError`` if its bytes are gone or changed, and\n"
            "        ``ValueError`` if it was redirected.\"\"\"\n",
        ),
        (
            "        stored = self.store.get(\n",
            "        if record.final_url != record.request_url:\n"
            "            raise ValueError(\n"
            "                f\"it was redirected to {record.final_url}, and a redirected response\"\n"
            "                \" is never read\"\n"
            "            )\n"
            "        stored = self.store.get(\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/sec/client.py": [
        (
            "  changing identity (A §404).\n",
            "  changing identity (A §404). A response SEC serves from another URL than the one\n"
            "  requested is refused before it is saved, so no saved response is ever read under a\n"
            "  URL it was not served from (PR #6's review, F13).\n",
        ),
        (
            "from collections.abc import Callable, Iterator, Mapping\n",
            "from collections.abc import Callable, Collection, Iterator, Mapping\n",
        ),
        (
            "    PoliteClient,\n",
            "    Fetched,\n"
            "    PoliteClient,\n",
        ),
        (
            "    machine_lock_dir,\n",
            "    UnexpectedResponse,\n"
            "    machine_lock_dir,\n",
        ),
        (
            "\n"
            "@contextmanager\n",
            "    def fetch(self, url: str, expected_types: Collection[str]) -> Fetched:\n"
            "        \"\"\"``PoliteClient.fetch``, refused with ``UnexpectedResponse`` when SEC served\n"
            "        the response from another URL.\"\"\"\n"
            "        fetched = super().fetch(url, expected_types)\n"
            "        if fetched.retrieval.final_url != url:\n"
            "            raise UnexpectedResponse(\n"
            "                f\"{url} was redirected to {fetched.retrieval.final_url}; a redirected\"\n"
            "                \" response is never saved\"\n"
            "            )\n"
            "        return fetched\n"
            "\n"
            "\n"
            "@contextmanager\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task2-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_build.py packages/earnings-ingestion/tests/test_sec_client.py -q`

Expected: `56 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/build.py packages/earnings-ingestion/src/earnings_ingestion/events/saved.py packages/earnings-ingestion/src/earnings_ingestion/sec/client.py packages/earnings-ingestion/tests/test_events_build.py packages/earnings-ingestion/tests/test_sec_client.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1371 passed, 24 deselected`; `All checks passed!` and
`252 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/build.py packages/earnings-ingestion/src/earnings_ingestion/events/saved.py packages/earnings-ingestion/src/earnings_ingestion/sec/client.py packages/earnings-ingestion/tests/test_events_build.py packages/earnings-ingestion/tests/test_sec_client.py
git commit -m "fix(sec): refuse a redirected response, when fetched and when read (F13)"
```

---

### Task 3: Read a primary document with no Item line as unread

PR #6's review, found with F13. `read_text` in `events/release.py` paired each Item
heading with the one after it through `zip(..., strict=True)`. Text with no line that
begins "Item" and a number made that raise `ValueError`, which escaped `build_events`
as a traceback, and the documents phase of `discover` as a stop no rerun could pass.
The module's docstring promises that a document with no such heading states nothing,
so such text now reads as unread, like text with other Item lines but no Item 2.02.
A redirected page (F13) or a heading `walker-1` does not start a line with could reach
it. events v1 does not: the build over its saved responses reads every candidate.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/events/release.py`.
- Test (modify, by exact replacement):
  `packages/earnings-ingestion/tests/test_events_release.py` and
  `test_events_build.py`.

**Interfaces:**

- Consumes: `read_text(text) -> Reading` and `Reading(unread=...)` in
  `events/release.py`.
- Produces: `read_text` returns `Reading(unread=...)` for text with no Item line.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task3-tests.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_events_build.py": [
        (
            "def test_a_filing_accepted_after_the_cutoff_is_refused(universe, tmp_path) -> None:\n",
            "def test_a_candidate_with_no_item_line_builds(universe, tmp_path) -> None:\n"
            "    \"\"\"A primary document with no Item line at all is read as unread, and the build\n"
            "    goes on (PR #6's review, \"Read a primary document with no Item line as\n"
            "    unread\").\"\"\"\n"
            "    layer = write_layer(tmp_path / \"data\" / \"raw\" / \"events\", tmp_path)\n"
            "    number = accession(DYNAMO, \"2024-10-22 06:45:00\")\n"
            "    ((filing, _),) = [(f, e) for f, e in filings(DYNAMO) if f.accession == number]\n"
            "    body = b\"<html><body><p>Dynamo Motors Co posted its results.</p></body></html>\"\n"
            "    save(\n"
            "        layer.store,\n"
            "        archive_url(DYNAMO.cik, number, filing.primary_document),\n"
            "        body,\n"
            "        \"text/html\",\n"
            "        datetime(2026, 9, 29, tzinfo=UTC),\n"
            "    )\n"
            "    built = run(universe, layer)\n"
            "    detail = built.details[\"cik-0009990005:2024-09-27\"]\n"
            "    (candidate,) = detail.identification.candidates\n"
            "    assert candidate.reading.unread == \"it has no Item 2.02 heading\"\n"
            "    assert detail.identification.method is IdentificationMethod.SOLE_CANDIDATE\n"
            "\n"
            "\n"
            "def test_a_filing_accepted_after_the_cutoff_is_refused(universe, tmp_path) -> None:\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_events_release.py": [
        (
            "    assert (reading.dates, reading.periods, reading.preliminary) == ((), (), False)\n"
            "\n"
            "\n",
            "    assert (reading.dates, reading.periods, reading.preliminary) == ((), (), False)\n"
            "\n"
            "\n"
            "def test_a_text_with_no_item_line_at_all_states_nothing() -> None:\n"
            "    \"\"\"A document whose text has no line that begins \"Item\" and a number reads as\n"
            "    unread, as one with other Item headings does, and never raises (PR #6's\n"
            "    review).\"\"\"\n"
            "    reading = read_text(\"Form 8-K\\nAcme Industrial Corp\\nIt posted its results.\")\n"
            "    assert reading.sections == ()\n"
            "    assert reading.unread == \"it has no Item 2.02 heading\"\n"
            "\n"
            "\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task3-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_build.py packages/earnings-ingestion/tests/test_events_release.py -q`

Expected: FAIL: `2 failed, 88 passed`, each with
`ValueError: zip() argument 2 is longer than argument 1`.

- [x] **Step 3: Read no Item line as unread**

Create `/tmp/plan8-task3-source.py`:

```python
"""Plan 8: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/release.py": [
        (
            "    for heading, following in zip(headings, [*headings[1:], None], strict=True):\n"
            "        if heading.group(1) != RESULTS_ITEM:\n"
            "            continue\n",
            "    for number, heading in enumerate(headings):\n"
            "        if heading.group(1) != RESULTS_ITEM:\n"
            "            continue\n"
            "        following = headings[number + 1] if number + 1 < len(headings) else None\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task3-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_build.py packages/earnings-ingestion/tests/test_events_release.py -q`

Expected: `90 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/release.py packages/earnings-ingestion/tests/test_events_build.py packages/earnings-ingestion/tests/test_events_release.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1373 passed, 24 deselected`; `All checks passed!` and
`252 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/release.py packages/earnings-ingestion/tests/test_events_build.py packages/earnings-ingestion/tests/test_events_release.py
git commit -m "fix(events): read a primary document with no Item line as unread"
```

---

### Task 4: Cross-check an index page against its submissions row (F12)

PR #6's review, F12. The build and discovery took a filing's form and primary
document from its submissions row, and compared the index page with the row on the
accession alone. If SEC's two records disagreed, an 8-K/A page listed as an 8-K could
become a candidate, and a row whose `primaryDocument` named the EX-99 file, or none,
would have discovery fetch an exhibit before the freeze, against EV2. Plan B reads
each index page's document table for the exhibits, so the check lands first:

- `filings.index_disagreement(filing, index)` says why an index page describes
  another filing than its row: its form must be the row's, and it must list the row's
  primary document, by its base name, typed as that form.
- The build reports a disagreement as a problem, in `_Reader` and for an override's
  named filing.
- `discover_filing` (the `--filing` remedy) now saves the index page first, and
  fetches the primary document only when the page agrees with the row. So its output
  names two phases: the filing, then "the filing's document".

None of events v1's 269 candidates disagrees, so v1 rebuilds unchanged.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/events/filings.py`,
  `build.py`, and `discover.py`.
- Test (modify, by exact replacement):
  `packages/earnings-ingestion/tests/test_events_filings.py`,
  `test_events_discover.py`, and `apps/earnings-pipeline/tests/test_events_cli.py`.

**Interfaces:**

- Consumes: `Filing` in `sec/data.py`; `FilingIndex`, its `form`, `accession`, and
  `documents`, and `read_filing_index` in `sec/filing_index.py`.
- Produces: `index_disagreement(filing: Filing, index: FilingIndex) -> str | None` in
  `events/filings.py`.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task4-tests.py`:

```python
"""Plan 8: exact replacements for 3 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/tests/test_events_cli.py": [
        (
            "        f\"8-K {FILED[1]}: 2 to fetch\",\n",
            "        f\"8-K {FILED[1]}: 1 to fetch\",\n"
            "        f\"8-K {FILED[1]}'s document: 1 to fetch\",\n",
        ),
        (
            "        f\"8-K {FILED[1]}: 1 to fetch\",\n"
            "        \"fetched 1; requests sent: 1\",\n",
            "        f\"8-K {FILED[1]}: 0 to fetch\",\n"
            "        f\"8-K {FILED[1]}'s document: 1 to fetch\",\n"
            "        \"fetched 1; requests sent: 1\",\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_events_discover.py": [
        (
            "from datetime import timedelta\n",
            "from dataclasses import replace\n"
            "from datetime import timedelta\n",
        ),
        (
            "def test_issuer_filings_lists_what_the_build_reads_and_lacks(tmp_path) -> None:\n",
            "def test_discover_filing_checks_the_index_page_before_it_fetches_the_document(\n"
            "    universe, layer, tmp_path\n"
            ") -> None:\n"
            "    \"\"\"An index page that disagrees with its submissions row stops ``--filing``\n"
            "    before the primary document is fetched (PR #6's review, F12).\"\"\"\n"
            "    (filing,) = [\n"
            "        filing\n"
            "        for filing, entry in filings(DYNAMO)\n"
            "        if isinstance(entry, Release) and \"7.01\" in entry.items\n"
            "    ]\n"
            "    index = filing_index_url(DYNAMO.cik, filing.accession)\n"
            "    responses = dict(layer)\n"
            "    responses[index] = (\n"
            "        index_page(DYNAMO.cik, replace(filing, form=\"8-K/A\")),\n"
            "        \"text/html\",\n"
            "    )\n"
            "    root = Path(shutil.copytree(RAW, tmp_path / \"data\" / \"raw\" / \"events\"))\n"
            "    recorder = Recorder(responses)\n"
            "    result, _, _ = run(\n"
            "        universe,\n"
            "        recorder,\n"
            "        ArtifactStore(root, tmp_path),\n"
            "        filing=(DYNAMO.cik, filing.accession),\n"
            "    )\n"
            "    assert recorder.requested == [index]\n"
            "    assert result.problems == [f\"{index}: its form is 8-K/A, but its row's is 8-K\"]\n"
            "\n"
            "\n"
            "def test_issuer_filings_lists_what_the_build_reads_and_lacks(tmp_path) -> None:\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_events_filings.py": [
        (
            "def test_a_submissions_file_of_another_registrant_is_a_problem(saved) -> None:\n",
            "def test_an_index_page_of_another_form_is_a_problem(saved) -> None:\n"
            "    \"\"\"The index page's form must be the submissions row's: a page for an 8-K/A\n"
            "    listed as an 8-K would make it a candidate the rule may choose (PR #6's review,\n"
            "    F12).\"\"\"\n"
            "    filing = release(29, \"2024-10-24 16:05:12\")\n"
            "    saved.submissions([filing])\n"
            "    body = index_page(CIK, replace(filing, form=\"8-K/A\"), EXHIBIT)\n"
            "    url = filing_index_url(CIK, filing.accession)\n"
            "    save(saved.store, url, body, HTML, RETRIEVED)\n"
            "    read = saved.read()\n"
            "    assert read.problems == (f\"{url}: its form is 8-K/A, but its row's is 8-K\",)\n"
            "    assert read.releases == ()\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\"named\", [\"acme-ex991.htm\", \"\"])\n"
            "def test_a_row_whose_primary_document_the_index_does_not_type_as_its_form(\n"
            "    saved, named\n"
            ") -> None:\n"
            "    \"\"\"The row's primary document must be listed in the index, typed as the form: a\n"
            "    row naming the EX-99 file, or none, would have discovery fetch an exhibit before\n"
            "    the freeze (EV2) (PR #6's review, F12).\"\"\"\n"
            "    filing = release(29, \"2024-10-24 16:05:12\")\n"
            "    saved.submissions([replace(filing, primary_document=named)])\n"
            "    saved.index(filing)\n"
            "    read = saved.read()\n"
            "    url = filing_index_url(CIK, filing.accession)\n"
            "    assert read.problems == (\n"
            "        (\n"
            "            f\"{url}: it lists no {named or '(none)'} typed 8-K, its row's primary\"\n"
            "            \" document\"\n"
            "        ),\n"
            "    )\n"
            "    assert read.releases == ()\n"
            "\n"
            "\n"
            "def test_a_submissions_file_of_another_registrant_is_a_problem(saved) -> None:\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task4-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/tests/test_events_discover.py packages/earnings-ingestion/tests/test_events_filings.py -q`

Expected: FAIL: `5 failed, 39 passed`.

- The three filings cases find no problem (`assert () == (...)`), where each expects
  "its form is 8-K/A, but its row's is 8-K", or "it lists no acme-ex991.htm typed
  8-K, its row's primary document", or "it lists no (none) typed 8-K".
- `test_discover_filing_checks_the_index_page_before_it_fetches_the_document`
  fetches the document anyway, and meets
  `UnexpectedResponse: HTTP 404 for https://www.sec.gov/Archives/edgar/data/9990005/000999000525000010/dyna-8k-20250722.htm`.
- `test_discover_filing_keeps_a_smaller_approved_cap` reads one phase,
  `8-K 0009990001-24-000003: 2 to fetch`, where it expects two.

- [x] **Step 3: Check the page against its row**

Create `/tmp/plan8-task4-source.py`:

```python
"""Plan 8: exact replacements for 3 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/build.py": [
        (
            "from earnings_ingestion.events.filings import IssuerFilings, Placed, issuer_filings\n",
            "from earnings_ingestion.events.filings import (\n"
            "    IssuerFilings,\n"
            "    Placed,\n"
            "    index_disagreement,\n"
            "    issuer_filings,\n"
            ")\n",
        ),
        (
            "    why = release_refusal(\n",
            "    if (why := index_disagreement(filing, index)) is not None:\n"
            "        return None, f\"{url}: {why}\"\n"
            "    why = release_refusal(\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/discover.py": [
        (
            "``set_release_filing`` that names a filing discovery did not read.\n",
            "``set_release_filing`` that names a filing discovery did not read. It reads the\n"
            "index page before it fetches the document, and fetches nothing more when the page\n"
            "describes another filing than the issuer's submissions row does (F12), which\n"
            "``Discovery.problems`` then names.\n",
        ),
        (
            "from earnings_ingestion.events.filings import RELEASE_FORMS, issuer_filings\n",
            "from earnings_ingestion.events.filings import (\n"
            "    RELEASE_FORMS,\n"
            "    index_disagreement,\n"
            "    issuer_filings,\n"
            ")\n",
        ),
        (
            "from earnings_ingestion.sec.urls import (\n",
            "from earnings_ingestion.sec.filing_index import read_filing_index\n"
            "from earnings_ingestion.sec.urls import (\n",
        ),
        (
            "    wanted = [(filing_index_url(cik, accession), HTML)]\n"
            "    if filing.form in RELEASE_FORMS:\n"
            "        wanted.append((archive_url(cik, accession, filing.primary_document), DOCUMENT))\n"
            "    run = _Run(fetch, store, say)\n"
            "    run.phase(f\"{filing.form} {accession}\", wanted)\n",
            "    index = filing_index_url(cik, accession)\n"
            "    run = _Run(fetch, store, say)\n"
            "    run.phase(f\"{filing.form} {accession}\", [(index, HTML)])\n"
            "    if filing.form not in RELEASE_FORMS:\n"
            "        return run.result\n"
            "    try:\n"
            "        page = read_filing_index(SavedResponses(store).get(index).text.body)\n"
            "    except (FileNotFoundError, ValueError) as exc:\n"
            "        run.result.problems.append(f\"{index}: {exc}\")\n"
            "        return run.result\n"
            "    if page.accession != accession:\n"
            "        why = f\"it is the index page of {page.accession}\"\n"
            "    else:\n"
            "        why = index_disagreement(filing, page)\n"
            "    if why is not None:\n"
            "        run.result.problems.append(f\"{index}: {why}\")\n"
            "        return run.result\n"
            "    document = archive_url(cik, accession, filing.primary_document)\n"
            "    run.phase(f\"{filing.form} {accession}'s document\", [(document, DOCUMENT)])\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/filings.py": [
        (
            "problem: no review can settle it, so the build stops and lists it. So is an accession\n"
            "that the issuer's files list more than once, in one block or two: it is refused,\n",
            "problem, and so is an index page whose form is not its submissions row's, or that\n"
            "does not list the row's primary document typed as that form (PR #6's review, F12):\n"
            "no review can settle it, so the build stops and lists it. So is an accession that\n"
            "the issuer's files list more than once, in one block or two: it is refused,\n",
        ),
        (
            "    \"\"\"The URLs of responses the build reads that are not saved.\"\"\"\n"
            "\n"
            "\n",
            "    \"\"\"The URLs of responses the build reads that are not saved.\"\"\"\n"
            "\n"
            "\n"
            "def index_disagreement(filing: Filing, index: FilingIndex) -> str | None:\n"
            "    \"\"\"Why ``index``, the index page of ``filing``'s accession, describes another\n"
            "    filing than its submissions row does, or ``None``: its form must be the row's,\n"
            "    and it must list the row's primary document, by its base name, typed as that\n"
            "    form (PR #6's review, F12).\"\"\"\n"
            "    if index.form != filing.form:\n"
            "        return f\"its form is {index.form}, but its row's is {filing.form}\"\n"
            "    name = filing.primary_document.rsplit(\"/\", 1)[-1]\n"
            "    if not any(\n"
            "        document.filename == name and document.doc_type == filing.form\n"
            "        for document in index.documents\n"
            "    ):\n"
            "        return (\n"
            "            f\"it lists no {name or '(none)'} typed {filing.form}, its row's primary\"\n"
            "            \" document\"\n"
            "        )\n"
            "    return None\n"
            "\n"
            "\n",
        ),
        (
            "            found[filing.accession] = (index, artifact, instant)\n",
            "            if (why := index_disagreement(filing, index)) is not None:\n"
            "                self.problems.append(f\"{url}: {why}\")\n"
            "                continue\n"
            "            found[filing.accession] = (index, artifact, instant)\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task4-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/tests/test_events_discover.py packages/earnings-ingestion/tests/test_events_filings.py -q`

Expected: `44 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/src/earnings_ingestion/events/build.py packages/earnings-ingestion/src/earnings_ingestion/events/discover.py packages/earnings-ingestion/src/earnings_ingestion/events/filings.py packages/earnings-ingestion/tests/test_events_discover.py packages/earnings-ingestion/tests/test_events_filings.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1377 passed, 24 deselected`; `All checks passed!` and
`252 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/src/earnings_ingestion/events/build.py packages/earnings-ingestion/src/earnings_ingestion/events/discover.py packages/earnings-ingestion/src/earnings_ingestion/events/filings.py packages/earnings-ingestion/tests/test_events_discover.py packages/earnings-ingestion/tests/test_events_filings.py
git commit -m "fix(events): cross-check an index page against its submissions row (F12)"
```

---

### Task 5: Check the CLIs' store and corpus paths first (F19, F38)

PR #6's review, F19 and F38. The CLIs resolved only `--repo`.

- **F19.** `--store` accepted any directory under the repository, and
  `tests/fixtures/**` is un-ignored. So `events --store tests/fixtures/x discover`
  would save real SEC responses where `git add -A` publishes them.
- **F38.** With a corpus directory outside the repository, or spelled through a
  symlinked prefix, `events freeze` and `events select` wrote their files and then
  crashed on `relative_to` while printing them.

`earnings_pipeline.paths` holds both checks. Every command that saves fetched bytes,
`events discover`, `cohort fetch`, and `cohort fetch-sec`, refuses a store root that
does not resolve under `<repo>/data/raw`, in its callback, before any client opens.
Task 19's `events acquire` joins them. Paths resolve only for the check, never for
the stored root, so a symlinked `data/` still works. Every command prints a path
relative to the repository when it lies under it, and in full otherwise. Building,
freezing, and selecting stay unguarded, since they fetch nothing.

**Files:**

- Create: `apps/earnings-pipeline/src/earnings_pipeline/paths.py`.
- Modify, by exact replacement:
  `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py` and `events_cli.py`.
- Test: create `apps/earnings-pipeline/tests/test_paths.py`; modify, by exact
  replacement, `test_cohort_cli.py` and `test_events_cli.py` there.

**Interfaces:**

- Consumes: the `Layout` of each CLI, with its `repo` and `store`.
- Produces, in `earnings_pipeline.paths`: `RAW = Path("data") / "raw"`,
  `raw_store_refusal(repo: Path, store: Path) -> str | None`, and
  `shown(path: Path, repo: Path) -> str`. Task 19 adds `RUNS` and `runs_refusal`.

- [x] **Step 1: Write the failing tests**

Create `apps/earnings-pipeline/tests/test_paths.py`:

```python
"""Where fetched bytes may be saved, and how paths print (PR #6's review, F19 and
F38)."""

from pathlib import Path

from earnings_pipeline.paths import raw_store_refusal, shown


def test_a_store_under_a_symlinked_data_directory_is_under_data_raw(
    tmp_path,
) -> None:
    repo, elsewhere = tmp_path / "repo", tmp_path / "disk"
    (elsewhere / "raw").mkdir(parents=True)
    repo.mkdir()
    (repo / "data").symlink_to(elsewhere)
    assert raw_store_refusal(repo, Path("data/raw/events")) is None
    assert raw_store_refusal(repo, Path("data/raw/../../tests/fixtures/x"))


def test_a_path_prints_relative_under_the_repo_and_in_full_elsewhere(
    tmp_path,
) -> None:
    repo = tmp_path / "repo"
    assert shown(repo / "config" / "x.json", repo) == "config/x.json"
    assert shown(tmp_path / "other" / "x.json", repo) == str(
        tmp_path / "other" / "x.json"
    )
```

Extract it with `python3 /tmp/plan8-extract.py apps/earnings-pipeline/tests/test_paths.py`.

Create `/tmp/plan8-task5-tests.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/tests/test_cohort_cli.py": [
        (
            "def run(repo: Path, *args: str):\n",
            "COHORT_STORE = Path(\"data\") / \"raw\" / \"cohort\"\n"
            "\n"
            "\n"
            "def run(repo: Path, *args: str, store: Path = FIXTURE_DIR / \"raw\"):\n",
        ),
        (
            "        str(FIXTURE_DIR / \"raw\"),\n",
            "        str(store),\n",
        ),
        (
            "    result = run(repo, \"fetch-sec\")\n",
            "    result = run(repo, \"fetch-sec\", store=COHORT_STORE)\n",
        ),
        (
            "    result = run(repo, \"fetch\", \"synthetic-index\", \"https://index.example/notices/new\")\n",
            "    result = run(\n"
            "        repo,\n"
            "        \"fetch\",\n"
            "        \"synthetic-index\",\n"
            "        \"https://index.example/notices/new\",\n"
            "        store=COHORT_STORE,\n"
            "    )\n",
        ),
        (
            "    assert \"Refused: application/pdf contradicts the bytes\" in refused.stderr\n",
            "    assert \"Refused: application/pdf contradicts the bytes\" in refused.stderr\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\n"
            "    \"command\",\n"
            "    [[\"fetch-sec\"], [\"fetch\", \"synthetic-index\", \"https://index.example/notices/n\"]],\n"
            ")\n"
            "def test_a_fetching_command_refuses_a_store_outside_data_raw(\n"
            "    repo, monkeypatch, command\n"
            ") -> None:\n"
            "    \"\"\"Fetched bytes are saved only under data/raw, which Git ignores; the check\n"
            "    comes before any client opens (PR #6's review, F19).\"\"\"\n"
            "\n"
            "    def refuse(*args, **kwargs):\n"
            "        raise AssertionError(\"a client opened\")\n"
            "\n"
            "    monkeypatch.setattr(cohort_cli, \"open_sec_client\", refuse)\n"
            "    monkeypatch.setattr(cohort_cli, \"open_web_client\", refuse)\n"
            "    result = run(repo, *command)\n"
            "    assert result.exit_code == 1\n"
            "    assert result.stderr.splitlines() == [\n"
            "        (\n"
            "            f\"Refused: {FIXTURE_DIR / 'raw'} does not resolve under data/raw, where\"\n"
            "            \" fetched bytes are kept out of Git\"\n"
            "        )\n"
            "    ]\n"
            "\n"
            "\n"
            "def test_freeze_prints_a_manifest_outside_the_repo_in_full(\n"
            "    repo, tmp_path_factory\n"
            ") -> None:\n"
            "    outside = tmp_path_factory.mktemp(\"elsewhere\") / \"cohort\"\n"
            "    shutil.copytree(repo / FIXTURE_DIR, outside)\n"
            "    result = RUNNER.invoke(\n"
            "        cli.app,\n"
            "        [\n"
            "            \"cohort\",\n"
            "            \"--repo\",\n"
            "            str(repo),\n"
            "            \"--config-dir\",\n"
            "            str(outside),\n"
            "            \"--store\",\n"
            "            str(FIXTURE_DIR / \"raw\"),\n"
            "            \"--register\",\n"
            "            str(outside / \"membership-source-register.toml\"),\n"
            "            \"--sec-register\",\n"
            "            str(outside / \"source-register.toml\"),\n"
            "            \"freeze\",\n"
            "        ],\n"
            "    )\n"
            "    assert result.exit_code == 0, result.output\n"
            "    (line,) = [line for line in result.stdout.splitlines() if \"-v1.json\" in line]\n"
            "    assert line.startswith(str(outside / \"manifests\" / \"djia-synthetic-v1.json\"))\n",
        ),
    ],
    "apps/earnings-pipeline/tests/test_events_cli.py": [
        (
            "EVENTS_HASH = \"438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58\"\n",
            "EVENTS_STORE = Path(\"data\") / \"raw\" / \"events\"\n"
            "EVENTS_HASH = \"438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58\"\n",
        ),
        (
            "    return tmp_path\n"
            "\n"
            "\n",
            "    return tmp_path\n"
            "\n"
            "\n"
            "@pytest.fixture\n"
            "def moved(repo: Path) -> Path:\n"
            "    \"\"\"The corpus's saved responses, moved under data/raw, where a command that\n"
            "    fetches may save.\"\"\"\n"
            "    (repo / EVENTS_STORE).parent.mkdir(parents=True)\n"
            "    shutil.move(repo / FIXTURE_DIR / \"raw\", repo / EVENTS_STORE)\n"
            "    return repo / EVENTS_STORE\n"
            "\n"
            "\n",
        ),
        (
            "def test_discover_names_a_saved_response_it_cannot_read_and_fails(\n"
            "    repo, monkeypatch\n"
            ") -> None:\n",
            "def test_discover_names_a_saved_response_it_cannot_read_and_fails(\n"
            "    repo, moved, monkeypatch\n"
            ") -> None:\n",
        ),
        (
            "    saved = SavedResponses(ArtifactStore(repo / FIXTURE_DIR / \"raw\", repo))\n"
            "    artifact = saved.get(url).artifact\n",
            "    saved = SavedResponses(ArtifactStore(moved, repo))\n"
            "    artifact = saved.get(url).artifact\n",
        ),
        (
            "    result = run(repo, \"discover\", \"--max-requests\", \"5\")\n",
            "    result = run(repo, \"discover\", \"--max-requests\", \"5\", store=EVENTS_STORE)\n",
        ),
        (
            "    result = run(repo, \"discover\", \"--filing\", \"0009990005\", \"0009990005-99-000001\")\n",
            "    result = run(\n"
            "        repo,\n"
            "        \"discover\",\n"
            "        \"--filing\",\n"
            "        \"0009990005\",\n"
            "        \"0009990005-99-000001\",\n"
            "        store=EVENTS_STORE,\n"
            "    )\n",
        ),
        (
            "    root = repo / FIXTURE_DIR / \"raw\" / SEC_SOURCE_ID / \"retrievals\"\n",
            "    root = repo / EVENTS_STORE / SEC_SOURCE_ID / \"retrievals\"\n",
        ),
        (
            "def test_discover_filing_keeps_a_smaller_approved_cap(repo, monkeypatch) -> None:\n",
            "def test_discover_filing_keeps_a_smaller_approved_cap(repo, moved, monkeypatch) -> None:\n",
        ),
        (
            "    result = run(repo, \"discover\", \"--max-requests\", \"1\", \"--filing\", *FILED)\n",
            "    result = run(\n"
            "        repo, \"discover\", \"--max-requests\", \"1\", \"--filing\", *FILED, store=EVENTS_STORE\n"
            "    )\n",
        ),
        (
            "    saved = SavedResponses(ArtifactStore(repo / FIXTURE_DIR / \"raw\", repo))\n"
            "    assert index in saved and document not in saved\n"
            "    result = run(repo, \"discover\", \"--filing\", *FILED)\n",
            "    saved = SavedResponses(ArtifactStore(moved, repo))\n"
            "    assert index in saved and document not in saved\n"
            "    result = run(repo, \"discover\", \"--filing\", *FILED, store=EVENTS_STORE)\n",
        ),
        (
            "def test_discover_filing_never_raises_its_cap(repo, monkeypatch) -> None:\n"
            "    unsave(repo, *FILED)\n"
            "    budgets = client(monkeypatch, served())\n"
            "    result = run(repo, \"discover\", \"--max-requests\", \"5\", \"--filing\", *FILED)\n",
            "def test_discover_filing_never_raises_its_cap(repo, moved, monkeypatch) -> None:\n"
            "    unsave(repo, *FILED)\n"
            "    budgets = client(monkeypatch, served())\n"
            "    result = run(\n"
            "        repo, \"discover\", \"--max-requests\", \"5\", \"--filing\", *FILED, store=EVENTS_STORE\n"
            "    )\n",
        ),
        (
            "    result = run(repo, \"discover\", \"--filing\", *FILED, *second)\n",
            "    result = run(repo, \"discover\", \"--filing\", *FILED, *second, store=EVENTS_STORE)\n",
        ),
        (
            "    assert \"Refused: pass one --filing\" in result.stderr\n",
            "    assert \"Refused: pass one --filing\" in result.stderr\n"
            "\n"
            "\n"
            "def test_discover_refuses_a_store_outside_data_raw(repo, monkeypatch) -> None:\n"
            "    \"\"\"tests/fixtures/ is committed, so fetched SEC pages saved there would reach this\n"
            "    public repository: discover refuses before any client opens (PR #6's review,\n"
            "    F19).\"\"\"\n"
            "\n"
            "    def refuse(**kwargs):\n"
            "        raise AssertionError(\"the client opened\")\n"
            "\n"
            "    monkeypatch.setattr(events_cli, \"open_sec_client\", refuse)\n"
            "    result = run(\n"
            "        repo, \"discover\", \"--max-requests\", \"1\", store=Path(\"tests/fixtures/x\")\n"
            "    )\n"
            "    assert result.exit_code == 1\n"
            "    assert result.stderr.splitlines() == [\n"
            "        (\n"
            "            \"Refused: tests/fixtures/x does not resolve under data/raw, where\"\n"
            "            \" fetched bytes are kept out of Git\"\n"
            "        )\n"
            "    ]\n"
            "\n"
            "\n"
            "def test_freeze_and_select_print_a_corpus_outside_the_repo_in_full(\n"
            "    repo, tmp_path_factory\n"
            ") -> None:\n"
            "    \"\"\"A corpus directory outside the repository, or spelled through a symlinked\n"
            "    prefix, prints in full rather than crashing after the write (F38).\"\"\"\n"
            "    outside = tmp_path_factory.mktemp(\"elsewhere\") / \"corpus\"\n"
            "    shutil.copytree(repo / FIXTURE_DIR, outside, ignore=shutil.ignore_patterns(\"raw\"))\n"
            "    layout = [\"--corpus-dir\", str(outside), \"--store\", str(FIXTURE_DIR / \"raw\")]\n"
            "\n"
            "    def invoke(command: str):\n"
            "        args = [\"events\", \"--repo\", str(repo), \"--universe-dir\", str(UNIVERSES)]\n"
            "        return RUNNER.invoke(\n"
            "            cli.app, [*args, *layout, \"--corpus-id\", \"djia-synthetic\", command]\n"
            "        )\n"
            "\n"
            "    froze = invoke(\"freeze\")\n"
            "    assert froze.exit_code == 0, froze.output\n"
            "    assert froze.stdout.splitlines()[1:] == [\n"
            "        f\"{outside / 'events-v1.json'}  {EVENTS_HASH}\",\n"
            "        str(outside / \"events-v1.evidence.json\"),\n"
            "    ]\n"
            "    selected = invoke(\"select\")\n"
            "    assert selected.exit_code == 0, selected.output\n"
            "    assert selected.stdout.splitlines()[-1] == (\n"
            "        f\"{outside / 'pilot-v1.json'}  {PILOT_HASH}\"\n"
            "    )\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task5-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py apps/earnings-pipeline/tests/test_paths.py -q`

Expected: FAIL: `1 error`, collecting `apps/earnings-pipeline/tests/test_paths.py`,
with `ModuleNotFoundError: No module named 'earnings_pipeline.paths'`.

- [x] **Step 3: Check the paths before anything runs**

Create `apps/earnings-pipeline/src/earnings_pipeline/paths.py`:

```python
"""Paths the commands check and print (PR #6's review, F19 and F38).

- **Where fetched bytes go.** A command that saves fetched bytes refuses a store root
  that does not resolve under ``<repo>/data/raw``, which Git ignores, before any
  client opens: ``tests/fixtures/`` is committed, so fetched SEC or index pages saved
  there would reach this public repository. Paths are resolved only for the check;
  the store keeps the root as given, so a symlinked ``data/`` still works.
- **What a command prints.** A path under the repository prints relative to it, and
  any other path, such as a corpus directory outside it or one spelled through a
  symlinked prefix, prints in full.
"""

from pathlib import Path

RAW = Path("data") / "raw"


def raw_store_refusal(repo: Path, store: Path) -> str | None:
    """Why fetched bytes may not be saved under ``repo / store``, or ``None``."""
    if (repo / store).resolve().is_relative_to((repo / RAW).resolve()):
        return None
    return (
        f"Refused: {store} does not resolve under {RAW}, where fetched bytes are"
        " kept out of Git"
    )


def shown(path: Path, repo: Path) -> str:
    """``path`` relative to ``repo`` when it lies under it, and in full otherwise."""
    return str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path)
```

Extract it with `python3 /tmp/plan8-extract.py apps/earnings-pipeline/src/earnings_pipeline/paths.py`.

Create `/tmp/plan8-task5-source.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py": [
        (
            "\"\"\"\n"
            "\n",
            "``fetch`` and ``fetch-sec`` refuse a ``--store`` that does not resolve under\n"
            "``data/raw``, before any client opens, and every command prints a path outside the\n"
            "repository in full (``earnings_pipeline.paths``).\n"
            "\"\"\"\n"
            "\n",
        ),
        (
            "cohort = typer.Typer(no_args_is_help=True, help=\"Stage 4's point-in-time DJIA cohort.\")\n",
            "from earnings_pipeline.paths import raw_store_refusal, shown\n"
            "\n"
            "cohort = typer.Typer(no_args_is_help=True, help=\"Stage 4's point-in-time DJIA cohort.\")\n"
            "FETCHING = frozenset({\"fetch\", \"fetch-sec\"})\n"
            "\"\"\"The commands that save fetched bytes under ``--store``.\"\"\"\n",
        ),
        (
            "    context.obj = Layout(repo.resolve(), config_dir, store, register, sec_register)\n",
            "    layout = Layout(repo.resolve(), config_dir, store, register, sec_register)\n"
            "    if context.invoked_subcommand in FETCHING and (\n"
            "        refusal := raw_store_refusal(layout.repo, store)\n"
            "    ):\n"
            "        _fail(refusal)\n"
            "    context.obj = layout\n",
        ),
        (
            "    typer.echo(f\"{frozen.path.relative_to(layout.repo)}  {definition.content_hash}\")\n",
            "    typer.echo(f\"{shown(frozen.path, layout.repo)}  {definition.content_hash}\")\n",
        ),
        (
            "    typer.echo(f\"record: {path.relative_to(layout.repo)}\")\n",
            "    typer.echo(f\"record: {shown(path, layout.repo)}\")\n",
        ),
    ],
    "apps/earnings-pipeline/src/earnings_pipeline/events_cli.py": [
        (
            "\n"
            "The universe is the latest frozen manifest in ``--universe-dir``, which holds one\n",
            "\n"
            "``discover`` refuses a ``--store`` that does not resolve under ``data/raw``, before\n"
            "any client opens, and every command prints a path outside the repository in full\n"
            "(``earnings_pipeline.paths``).\n"
            "\n"
            "The universe is the latest frozen manifest in ``--universe-dir``, which holds one\n",
        ),
        (
            "events = typer.Typer(\n",
            "from earnings_pipeline.paths import raw_store_refusal, shown\n"
            "\n"
            "events = typer.Typer(\n",
        ),
        (
            "\"\"\"What ``discover --filing`` fetches at most: an index page and an 8-K document.\"\"\"\n"
            "\n"
            "\n",
            "\"\"\"What ``discover --filing`` fetches at most: an index page and an 8-K document.\"\"\"\n"
            "FETCHING = frozenset({\"discover\"})\n"
            "\"\"\"The commands that save fetched bytes under ``--store``.\"\"\"\n"
            "\n"
            "\n",
        ),
        (
            "    context.obj = Layout(repo.resolve(), universe_dir, corpus_dir, store, corpus_id)\n",
            "    layout = Layout(repo.resolve(), universe_dir, corpus_dir, store, corpus_id)\n"
            "    if context.invoked_subcommand in FETCHING and (\n"
            "        refusal := raw_store_refusal(layout.repo, store)\n"
            "    ):\n"
            "        _fail(refusal)\n"
            "    context.obj = layout\n",
        ),
        (
            "    typer.echo(f\"{frozen.path.relative_to(layout.repo)}  {definition.content_hash}\")\n"
            "    typer.echo(f\"{frozen.evidence_path.relative_to(layout.repo)}\")\n",
            "    typer.echo(f\"{shown(frozen.path, layout.repo)}  {definition.content_hash}\")\n"
            "    typer.echo(shown(frozen.evidence_path, layout.repo))\n",
        ),
        (
            "    typer.echo(f\"{frozen.path.relative_to(layout.repo)}  {definition.content_hash}\")\n",
            "    typer.echo(f\"{shown(frozen.path, layout.repo)}  {definition.content_hash}\")\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task5-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py apps/earnings-pipeline/tests/test_paths.py -q`

Expected: `34 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/src/earnings_pipeline/paths.py apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py apps/earnings-pipeline/tests/test_paths.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1384 passed, 24 deselected`; `All checks passed!` and
`254 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/src/earnings_pipeline/paths.py apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py apps/earnings-pipeline/tests/test_paths.py
git commit -m "fix(pipeline): check the CLIs' store and corpus paths before anything runs (F19, F38)"
```

---

### Task 6: Print the request count on every stop, and take approved counts (F31, F35)

PR #6's review, F31 and F35. Each live gate records its request count, but:

- `events discover` printed "requests sent: N" only for the stops it caught. An
  `OSError` from saving, a saved body that was gone, and a Ctrl-C ended with a
  traceback and no count. `cohort_cli.py`'s handlers shared the pattern.
- `cohort fetch-sec` printed no count when it stopped, and `cohort verify-live` never
  printed one. Both ran under the client's default cap of 500 (P6-16), where `events
  discover` takes the count the user approved (P7-10).

Now `OSError` joins the stops, and a separate `except KeyboardInterrupt` prints the
count and re-raises, in both CLIs. `cohort fetch-sec` and `cohort verify-live` need
`--max-requests` and refuse before any client opens without it. They print their
requests sent on every exit, and the `verify-live` record gains `requests_sent`.
`cohort terms` sends one request and keeps the default.

**Files:**

- Modify, by exact replacement:
  `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py` and `events_cli.py`;
  `packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py` and
  `cohort/records.py`; and `docs/data-dictionary.md`.
- Test (modify, by exact replacement): `apps/earnings-pipeline/tests/test_cohort_cli.py`
  and `test_events_cli.py`; `packages/earnings-ingestion/tests/test_cohort_live.py`;
  and `tests/integration/test_cohort_live.py`, a `live` test whose call gains the cap.

**Interfaces:**

- Consumes: `open_sec_client(max_requests=...)`, `SecClient.throttle.count`, and the
  stop exceptions each CLI already catches.
- Produces: `cohort fetch-sec --max-requests N` and `cohort verify-live --max-requests
  N`, both required; `run_live(..., max_requests=N)` in `cohort/live.py`; and
  `LiveVerification.requests_sent: int` in `cohort/records.py`.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task6-tests.py`:

```python
"""Plan 8: exact replacements for 4 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/tests/test_cohort_cli.py": [
        (
            "    def fake_open():\n",
            "    def fake_open(*, max_requests):\n"
            "        assert max_requests == 5\n",
        ),
        (
            "    result = run(repo, \"fetch-sec\", store=COHORT_STORE)\n"
            "    assert result.exit_code == 1\n"
            "    assert \"Stopped: 403 persisted\" in result.stderr\n"
            "    assert requested == [\"https://www.sec.gov/files/company_tickers.json\"]\n",
            "    result = run(repo, \"fetch-sec\", \"--max-requests\", \"5\", store=COHORT_STORE)\n"
            "    assert result.exit_code == 1\n"
            "    assert \"Stopped: 403 persisted\" in result.stderr\n"
            "    assert result.stdout.splitlines() == [\"requests sent: 1\"]\n"
            "    assert requested == [\"https://www.sec.gov/files/company_tickers.json\"]\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\"command\", [\"fetch-sec\", \"verify-live\"])\n"
            "def test_a_live_command_needs_the_approved_count(repo, monkeypatch, command) -> None:\n"
            "    \"\"\"fetch-sec and verify-live take the count the user approved, as events\n"
            "    discover does, and refuse before any client opens (PR #6's review, F35).\"\"\"\n"
            "\n"
            "    def refuse(*args, **kwargs):\n"
            "        raise AssertionError(\"a client opened\")\n"
            "\n"
            "    monkeypatch.setattr(cohort_cli, \"open_sec_client\", refuse)\n"
            "    monkeypatch.setattr(cohort_cli, \"run_live\", refuse)\n"
            "    result = run(repo, command, store=COHORT_STORE)\n"
            "    assert result.exit_code == 1\n"
            "    assert \"Refused: pass --max-requests\" in result.stderr\n"
            "\n"
            "\n"
            "def test_verify_live_prints_its_count_when_it_stops(repo, monkeypatch) -> None:\n"
            "    def stopped(repo, *, max_requests, sent):\n"
            "        assert max_requests == 30\n"
            "        sent.count = 4\n"
            "        raise cohort_cli.AccessStop(\"another client holds the lock\")\n"
            "\n"
            "    monkeypatch.setattr(cohort_cli, \"run_live\", stopped)\n"
            "    result = run(repo, \"verify-live\", \"--max-requests\", \"30\")\n"
            "    assert result.exit_code == 1\n"
            "    assert result.stdout.splitlines() == [\"requests sent: 4\"]\n"
            "    assert \"Stopped: another client holds the lock\" in result.stderr\n",
        ),
    ],
    "apps/earnings-pipeline/tests/test_events_cli.py": [
        (
            "        f\"{outside / 'pilot-v1.json'}  {PILOT_HASH}\"\n"
            "    )\n",
            "        f\"{outside / 'pilot-v1.json'}  {PILOT_HASH}\"\n"
            "    )\n"
            "\n"
            "\n"
            "def test_discover_prints_its_count_when_saving_fails(repo, monkeypatch) -> None:\n"
            "    \"\"\"A full disk, or permissions, stops the run with its count, never a traceback\n"
            "    (PR #6's review, F31).\"\"\"\n"
            "    client(monkeypatch, served())\n"
            "\n"
            "    def full(*args, **kwargs):\n"
            "        raise OSError(28, \"No space left on device\")\n"
            "\n"
            "    monkeypatch.setattr(ArtifactStore, \"put\", full)\n"
            "    result = run(repo, \"discover\", \"--max-requests\", \"90\", store=EVENTS_STORE)\n"
            "    assert result.exit_code == 1\n"
            "    assert result.stdout.splitlines()[-1] == (\n"
            "        \"requests sent: 1; a rerun fetches only what is missing\"\n"
            "    )\n"
            "    assert \"Stopped: [Errno 28] No space left on device\" in result.stderr\n"
            "\n"
            "\n"
            "def test_discover_prints_its_count_when_a_saved_body_is_gone(\n"
            "    repo, moved, monkeypatch\n"
            ") -> None:\n"
            "    \"\"\"A companyfacts file whose body is gone stops the documents phase with the\n"
            "    count, never a traceback (F31).\"\"\"\n"
            "    url = \"https://data.sec.gov/api/xbrl/companyfacts/CIK0009990001.json\"\n"
            "    artifact = SavedResponses(ArtifactStore(moved, repo)).get(url).artifact\n"
            "    (repo / artifact.storage_ref).unlink()\n"
            "    client(monkeypatch, served())\n"
            "    result = run(repo, \"discover\", \"--max-requests\", \"5\", store=EVENTS_STORE)\n"
            "    assert result.exit_code == 1\n"
            "    assert result.stdout.splitlines()[-1] == (\n"
            "        \"requests sent: 0; a rerun fetches only what is missing\"\n"
            "    )\n"
            "    assert \"Stopped: no artifact\" in result.stderr\n"
            "\n"
            "\n"
            "def test_discover_prints_its_count_on_ctrl_c(repo, monkeypatch) -> None:\n"
            "    client(monkeypatch, served())\n"
            "    calls = []\n"
            "\n"
            "    def interrupted(*args, **kwargs):\n"
            "        calls.append(args)\n"
            "        raise KeyboardInterrupt\n"
            "\n"
            "    monkeypatch.setattr(ArtifactStore, \"put\", interrupted)\n"
            "    result = run(repo, \"discover\", \"--max-requests\", \"90\", store=EVENTS_STORE)\n"
            "    assert result.exit_code == 130\n"
            "    assert calls\n"
            "    assert \"requests sent: 1; a rerun fetches only what is missing\" in result.stdout\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_cohort_live.py": [
        (
            "from datetime import UTC, datetime\n"
            "\n"
            "from earnings_core import RightsStatus, sha256_hex\n"
            "from earnings_ingestion.cohort.live import verify_live\n",
            "from contextlib import contextmanager\n"
            "from datetime import UTC, datetime\n"
            "from types import SimpleNamespace\n"
            "\n"
            "from earnings_core import RightsStatus, sha256_hex\n"
            "from earnings_ingestion.cohort import live\n"
            "from earnings_ingestion.cohort.live import verify_live\n"
            "from earnings_ingestion.cohort.records import LiveVerification\n",
        ),
        (
            "    )\n"
            "    assert result.build_problems == ()\n",
            "    )\n"
            "    assert result.build_problems == ()\n"
            "\n"
            "\n"
            "def test_run_live_caps_each_client_and_records_what_both_sent(\n"
            "    tmp_path, monkeypatch\n"
            ") -> None:\n"
            "    \"\"\"Each client is capped at the approved count, and the record keeps the\n"
            "    requests both sent (PR #6's review, F35).\"\"\"\n"
            "\n"
            "    class Fake:\n"
            "        def __init__(self, count: int) -> None:\n"
            "            self.throttle = SimpleNamespace(count=count)\n"
            "            self.client = self\n"
            "            self.fetch = None\n"
            "\n"
            "    @contextmanager\n"
            "    def web(hosts, *, environ, max_requests):\n"
            "        assert max_requests == 7\n"
            "        yield Fake(2)\n"
            "\n"
            "    @contextmanager\n"
            "    def sec(*, environ, max_requests):\n"
            "        assert max_requests == 7\n"
            "        yield Fake(1)\n"
            "\n"
            "    empty = LiveVerification(\n"
            "        checked_at=datetime(2026, 9, 29, tzinfo=UTC),\n"
            "        checks=(),\n"
            "        build_problems=(),\n"
            "        rebuilt_content_hash=None,\n"
            "        frozen_content_hash=None,\n"
            "        blocking_finding_ids=(),\n"
            "    )\n"
            "    assert empty.requests_sent is None\n"
            "    monkeypatch.setattr(live, \"_targets\", lambda repo, options: [])\n"
            "    monkeypatch.setattr(live, \"open_web_client\", web)\n"
            "    monkeypatch.setattr(live, \"open_sec_client\", sec)\n"
            "    monkeypatch.setattr(live, \"verify_live\", lambda repo, **kwargs: empty)\n"
            "    result, path = live.run_live(tmp_path, max_requests=7)\n"
            "    assert result.requests_sent == 3\n"
            "    saved = LiveVerification.model_validate_json(path.read_text(encoding=\"utf-8\"))\n"
            "    assert saved.requests_sent == 3\n",
        ),
    ],
    "tests/integration/test_cohort_live.py": [
        (
            "REPO = Path(__file__).resolve().parents[2]\n"
            "\n"
            "\n",
            "REPO = Path(__file__).resolve().parents[2]\n"
            "LIVE_REQUESTS = 60\n"
            "\"\"\"Each client's cap: every terms page, curated page, and robots.txt, with room.\"\"\"\n"
            "\n"
            "\n",
        ),
        (
            "    result, path = run_live(REPO)\n",
            "    result, path = run_live(REPO, max_requests=LIVE_REQUESTS)\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task6-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/tests/test_cohort_live.py tests/integration/test_cohort_live.py -q`

Expected: FAIL: `8 failed, 34 passed, 1 deselected`. The deselected test is
`tests/integration/test_cohort_live.py`'s, which only a gate runs: the root
`pyproject.toml` deselects `live` and `browser` tests unless `-m` says otherwise.

- `cohort fetch-sec` and `verify-live` do not know `--max-requests` (exit code 2),
  and without it they open a client (`AssertionError('a client opened')`).
- `events discover` ends without "requests sent:" when saving fails, when a saved
  body is gone, and on Ctrl-C.
- `run_live` records no count
  (`'LiveVerification' object has no attribute 'requests_sent'`).

- [x] **Step 3: Print the count on every exit, and take the approved counts**

> Deviation: after the final review (`55ea811`), `discover`, `fetch-sec`, and `verify-live` print their count on any exit, their Ctrl-C handler widened to `BaseException`, so an error no stop names still ends with the count.

Create `/tmp/plan8-task6-source.py`:

```python
"""Plan 8: exact replacements for 5 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py": [
        (
            "    earnings-pipeline cohort fetch-sec                      # the shared SEC client\n",
            "    earnings-pipeline cohort fetch-sec --max-requests N     # the shared SEC client\n",
        ),
        (
            "    earnings-pipeline cohort verify-live\n",
            "    earnings-pipeline cohort verify-live --max-requests N\n",
        ),
        (
            "``fetch`` and ``fetch-sec`` refuse a ``--store`` that does not resolve under\n",
            "``fetch-sec`` and ``verify-live`` need ``--max-requests``, the count the user\n"
            "approved, and print the requests they sent on every exit (PR #6's review, F35).\n"
            "``fetch`` and ``fetch-sec`` refuse a ``--store`` that does not resolve under\n",
        ),
        (
            "from earnings_ingestion.cohort.live import ANY, run_live\n",
            "from earnings_ingestion.cohort.live import ANY, Sent, run_live\n",
        ),
        (
            "\"\"\"The commands that save fetched bytes under ``--store``.\"\"\"\n"
            "\n"
            "\n",
            "\"\"\"The commands that save fetched bytes under ``--store``.\"\"\"\n"
            "STOPS = (AccessStop, UnexpectedResponse, OSError, ValueError)\n"
            "\"\"\"What ends a live command with ``Stopped:``; ``OSError`` covers a full disk.\"\"\"\n"
            "APPROVED = typer.Option(help=\"The request count approved at the gate; the cap.\")\n"
            "\n"
            "\n",
        ),
        (
            "                typer.echo(f\"{ref.content_sha256}  {ref.storage_ref}  {url}\")\n"
            "    except (AccessStop, UnexpectedResponse, ValueError) as error:\n"
            "        _fail(f\"Stopped: {error}\")\n",
            "                typer.echo(f\"{ref.content_sha256}  {ref.storage_ref}  {url}\")\n"
            "    except STOPS as error:\n"
            "        _fail(f\"Stopped: {error}\")\n",
        ),
        (
            "def fetch_sec_command(context: typer.Context) -> None:\n"
            "    \"\"\"Save the SEC records the build reads, through the shared SEC client.\"\"\"\n"
            "    layout: Layout = context.obj\n"
            "    config = load_cohort_config(layout.repo / layout.config_dir)\n"
            "    try:\n"
            "        with open_sec_client() as sec:\n"
            "            result = fetch_sec(sec.fetch, layout.store(), layout.registers(), config)\n"
            "            requests = sec.throttle.count\n"
            "    except (AccessStop, UnexpectedResponse, ValueError) as error:\n"
            "        _fail(f\"Stopped: {error}\")\n"
            "    typer.echo(f\"fetched {len(result.fetched)}, already saved {len(result.kept)}\")\n"
            "    typer.echo(f\"requests sent: {requests}\")\n",
            "def fetch_sec_command(\n"
            "    context: typer.Context,\n"
            "    max_requests: Annotated[int | None, APPROVED] = None,\n"
            ") -> None:\n"
            "    \"\"\"Save the SEC records the build reads, through the shared SEC client.\"\"\"\n"
            "    layout: Layout = context.obj\n"
            "    if max_requests is None:\n"
            "        _fail(\"Refused: pass --max-requests, the request count the user approved\")\n"
            "    config = load_cohort_config(layout.repo / layout.config_dir)\n"
            "    sent = 0\n"
            "    try:\n"
            "        with open_sec_client(max_requests=max_requests) as sec:\n"
            "            try:\n"
            "                result = fetch_sec(\n"
            "                    sec.fetch, layout.store(), layout.registers(), config\n"
            "                )\n"
            "            finally:\n"
            "                sent = sec.throttle.count\n"
            "    except STOPS as error:\n"
            "        typer.echo(f\"requests sent: {sent}\")\n"
            "        _fail(f\"Stopped: {error}\")\n"
            "    except KeyboardInterrupt:\n"
            "        typer.echo(f\"requests sent: {sent}\")\n"
            "        raise\n"
            "    typer.echo(f\"fetched {len(result.fetched)}, already saved {len(result.kept)}\")\n"
            "    typer.echo(f\"requests sent: {sent}\")\n",
        ),
        (
            "    except (AccessStop, UnexpectedResponse, ValueError) as error:\n",
            "    except STOPS as error:\n",
        ),
        (
            "def verify_live_command(context: typer.Context) -> None:\n"
            "    \"\"\"The opt-in live verification (P-VL); saves its record under data/runs/.\"\"\"\n"
            "    layout: Layout = context.obj\n"
            "    try:\n"
            "        result, path = run_live(layout.repo)\n"
            "    except (AccessStop, ValueError) as error:\n"
            "        _fail(f\"Stopped: {error}\")\n",
            "def verify_live_command(\n"
            "    context: typer.Context,\n"
            "    max_requests: Annotated[int | None, APPROVED] = None,\n"
            ") -> None:\n"
            "    \"\"\"The opt-in live verification (P-VL); saves its record under data/runs/. Each\n"
            "    client is capped at --max-requests.\"\"\"\n"
            "    layout: Layout = context.obj\n"
            "    if max_requests is None:\n"
            "        _fail(\"Refused: pass --max-requests, the request count the user approved\")\n"
            "    sent = Sent()\n"
            "    try:\n"
            "        result, path = run_live(layout.repo, max_requests=max_requests, sent=sent)\n"
            "    except STOPS as error:\n"
            "        typer.echo(f\"requests sent: {sent.count}\")\n"
            "        _fail(f\"Stopped: {error}\")\n"
            "    except KeyboardInterrupt:\n"
            "        typer.echo(f\"requests sent: {sent.count}\")\n"
            "        raise\n",
        ),
        (
            "    typer.echo(f\"record: {shown(path, layout.repo)}\")\n",
            "    typer.echo(f\"requests sent: {result.requests_sent}\")\n"
            "    typer.echo(f\"record: {shown(path, layout.repo)}\")\n",
        ),
    ],
    "apps/earnings-pipeline/src/earnings_pipeline/events_cli.py": [
        (
            "approved on its own, and a second ``--filing`` is refused. ``discover`` exits 1 and\n"
            "names each saved submissions file, older page, index page, or primary document the\n"
            "build cannot read, which no rerun fetches again, since it is saved. ``build``, ``freeze``, and ``select`` read committed files and saved\n"
            "responses alone. ``build`` exits 1 while anything holds the freeze.\n",
            "approved on its own, and a second ``--filing`` is refused. It prints the requests it\n"
            "sent on every exit, a stop or a Ctrl-C included (PR #6's review, F31). ``discover``\n"
            "exits 1 and names each saved submissions file, older page, index page, or primary\n"
            "document the build cannot read, which no rerun fetches again, since it is saved.\n"
            "``build``, ``freeze``, and ``select`` read committed files and saved responses alone.\n"
            "``build`` exits 1 while anything holds the freeze.\n",
        ),
        (
            "\"\"\"The commands that save fetched bytes under ``--store``.\"\"\"\n"
            "\n"
            "\n",
            "\"\"\"The commands that save fetched bytes under ``--store``.\"\"\"\n"
            "STOPS = (AccessStop, UnexpectedResponse, OSError, ValueError, RuntimeError)\n"
            "\"\"\"What ends a live run with ``Stopped:`` and its request count; ``OSError`` covers a\n"
            "full disk and a saved body that is gone.\"\"\"\n"
            "\n"
            "\n",
        ),
        (
            "    except (AccessStop, UnexpectedResponse, ValueError, RuntimeError) as error:\n"
            "        typer.echo(f\"requests sent: {sent}; a rerun fetches only what is missing\")\n"
            "        _fail(f\"Stopped: {error}\")\n",
            "    except STOPS as error:\n"
            "        typer.echo(f\"requests sent: {sent}; a rerun fetches only what is missing\")\n"
            "        _fail(f\"Stopped: {error}\")\n"
            "    except KeyboardInterrupt:\n"
            "        typer.echo(f\"requests sent: {sent}; a rerun fetches only what is missing\")\n"
            "        raise\n",
        ),
    ],
    "docs/data-dictionary.md": [
        (
            "\n"
            "## Curated cohort files\n",
            "| `requests_sent` | non-negative integer or null | The requests both clients sent, each capped at the approved `--max-requests`; null in a record saved before plan 8 kept it |\n"
            "\n"
            "## Curated cohort files\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py": [
        (
            "client, and each check keeps its retrieval metadata. Nothing here runs in the\n"
            "default suite.\n",
            "client, and each check keeps its retrieval metadata. Each client is capped at the\n"
            "count the user approved, and the record keeps the requests both sent (PR #6's review,\n"
            "F35). Nothing here runs in the default suite.\n",
        ),
        (
            "from datetime import UTC, datetime\n",
            "from dataclasses import dataclass\n"
            "from datetime import UTC, datetime\n",
        ),
        (
            "def default_options() -> dict[str, Path]:\n",
            "@dataclass\n"
            "class Sent:\n"
            "    \"\"\"The requests a live run has sent so far, kept current as it stops.\"\"\"\n"
            "\n"
            "    count: int = 0\n"
            "\n"
            "\n"
            "def default_options() -> dict[str, Path]:\n",
        ),
        (
            "    repo: Path, *, environ: Mapping[str, str] | None = None\n"
            ") -> tuple[LiveVerification, Path]:\n"
            "    \"\"\"Open both clients, verify, and save the result under data/runs/cohort/live/.\"\"\"\n",
            "    repo: Path,\n"
            "    *,\n"
            "    max_requests: int,\n"
            "    environ: Mapping[str, str] | None = None,\n"
            "    sent: Sent | None = None,\n"
            ") -> tuple[LiveVerification, Path]:\n"
            "    \"\"\"Open both clients, each capped at ``max_requests``, verify, and save the result\n"
            "    under data/runs/cohort/live/. ``sent`` keeps the count both clients sent, even\n"
            "    when the run stops.\"\"\"\n"
            "    sent = Sent() if sent is None else sent\n",
        ),
        (
            "        open_web_client(web_hosts, environ=environ) as web,\n"
            "        open_sec_client(environ=environ) as sec,\n"
            "    ):\n"
            "        result = verify_live(\n"
            "            repo,\n"
            "            fetch_web=web.fetch,\n"
            "            fetch_sec=sec.fetch,\n"
            "            now=datetime.now(UTC),\n"
            "            options=options,\n"
            "        )\n",
            "        open_web_client(web_hosts, environ=environ, max_requests=max_requests) as web,\n"
            "        open_sec_client(environ=environ, max_requests=max_requests) as sec,\n"
            "    ):\n"
            "        try:\n"
            "            result = verify_live(\n"
            "                repo,\n"
            "                fetch_web=web.fetch,\n"
            "                fetch_sec=sec.fetch,\n"
            "                now=datetime.now(UTC),\n"
            "                options=options,\n"
            "            )\n"
            "        finally:\n"
            "            sent.count = web.client.throttle.count + sec.throttle.count\n"
            "    result = result.model_copy(update={\"requests_sent\": sent.count})\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/cohort/records.py": [
        (
            "    blocking_finding_ids: tuple[IdPart, ...]\n",
            "    blocking_finding_ids: tuple[IdPart, ...]\n"
            "    requests_sent: NonNegativeInt | None = None\n"
            "    \"\"\"What both clients sent; ``None`` in a record saved before it was kept.\"\"\"\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task6-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/tests/test_cohort_live.py tests/integration/test_cohort_live.py -q`

Expected: `42 passed, 1 deselected`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py packages/earnings-ingestion/src/earnings_ingestion/cohort/records.py packages/earnings-ingestion/tests/test_cohort_live.py tests/integration/test_cohort_live.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages pytest tests/integration/test_cohort_live.py -m live --collect-only -q
```

Expected: `escapes intact`; `1391 passed, 24 deselected`; `All checks passed!` and
`254 files already formatted`; and
`tests/integration/test_cohort_live.py::test_the_real_cohort_verifies_live`, then
`1 test collected`: collected, never run.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py docs/data-dictionary.md packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py packages/earnings-ingestion/src/earnings_ingestion/cohort/records.py packages/earnings-ingestion/tests/test_cohort_live.py tests/integration/test_cohort_live.py
git commit -m "fix(pipeline): print the request count on every stop; approved counts for live cohort commands (F31, F35)"
```

---

### Task 7: Refuse a repeated content or a missing evidence record (F22)

PR #6's review, F22. `event_manifest_version` is not hashed, so a hand-renumbered copy
of `events-v1.json` loaded beside v1 with the same content hash, and
`frozen_event_manifests` loaded a manifest whose evidence record was missing. No code
path writes either state, but with F4's rule (Task 9) a command must never find two
versions of one content. So listing the versions now refuses:

- in `frozen_event_manifests`, two versions that share a content hash, and a
  manifest whose `events-v<N>.evidence.json` is missing. `load_event_manifest` still
  reads one file alone, as the pilot's chain check and the tamper tests need.
- in `frozen_pilots`, two versions that share a content hash;
- in Stage 4's `frozen_manifests`, two cohort versions that share one (P6-14).

The data dictionary's reading notes say so.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py`,
  `events/freeze.py`, and `events/pilot.py`; and `docs/data-dictionary.md`.
- Test (modify, by exact replacement):
  `packages/earnings-ingestion/tests/test_cohort_build.py` and
  `test_events_freeze.py`.

**Interfaces:**

- Consumes: `frozen_event_manifests(directory)`, `frozen_pilots(directory)`, and
  `frozen_manifests(directory)`.
- Produces: each raises `ValueError` naming both files, "`<a>` and `<b>` hold one
  content", and `frozen_event_manifests` raises "`events-v<N>.json` has no
  `events-v<N>.evidence.json`".

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task7-tests.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_cohort_build.py": [
        (
            "def test_a_frozen_manifest_loads_without_any_saved_artifact(repo) -> None:\n",
            "def test_two_versions_of_one_content_are_refused(repo) -> None:\n"
            "    \"\"\"Stage 4's versions follow the same rule as Stage 5's (PR #6's review, F22).\"\"\"\n"
            "    manifests = repo / DIRECTORY / \"manifests\"\n"
            "    text = (manifests / \"djia-synthetic-v1.json\").read_text(encoding=\"utf-8\")\n"
            "    copy = text.replace('\"universe_version\": 1', '\"universe_version\": 2', 1)\n"
            "    (manifests / \"djia-synthetic-v2.json\").write_text(copy, encoding=\"utf-8\")\n"
            "    with pytest.raises(\n"
            "        ValueError, match=\"djia-synthetic-v1.json and djia-synthetic-v2.json hold one\"\n"
            "    ):\n"
            "        frozen_manifests(manifests, \"djia-synthetic\")\n"
            "\n"
            "\n"
            "def test_a_frozen_manifest_loads_without_any_saved_artifact(repo) -> None:\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_events_freeze.py": [
        (
            "        frozen_pilots(directory)\n",
            "        frozen_pilots(directory)\n"
            "\n"
            "\n"
            "def renumbered(path: Path, version: int) -> Path:\n"
            "    \"\"\"A hand-made copy of the frozen file at ``path`` under ``version``, which\n"
            "    neither content hash covers.\"\"\"\n"
            "    text = path.read_text(encoding=\"utf-8\")\n"
            "    field = (\n"
            "        \"pilot_version\" if path.name.startswith(\"pilot\") else \"event_manifest_version\"\n"
            "    )\n"
            "    copy = text.replace(f'\"{field}\": 1', f'\"{field}\": {version}', 1)\n"
            "    target = path.with_name(path.name.replace(\"-v1\", f\"-v{version}\"))\n"
            "    target.write_text(copy, encoding=\"utf-8\")\n"
            "    return target\n"
            "\n"
            "\n"
            "def test_two_versions_of_one_content_are_refused(universe, layer, tmp_path) -> None:\n"
            "    \"\"\"A copy renumbered by hand loads on its own, and listing the versions refuses\n"
            "    it, so no consumer reads it as the latest (PR #6's review, F22).\"\"\"\n"
            "    directory = tmp_path / \"corpus\"\n"
            "    frozen = freeze(reviewed(universe, layer), layer, directory)\n"
            "    pilot = freeze_pilot(\n"
            "        select_pilot(frozen.manifest, universe), universe, directory, now=NOW\n"
            "    )\n"
            "    copy = renumbered(frozen.path, 2)\n"
            "    shutil.copy(frozen.evidence_path, directory / \"events-v2.evidence.json\")\n"
            "    assert load_event_manifest(copy).definition.content_hash == (\n"
            "        frozen.manifest.definition.content_hash\n"
            "    )\n"
            "    with pytest.raises(ValueError, match=\"events-v1.json and events-v2.json hold one\"):\n"
            "        frozen_event_manifests(directory)\n"
            "    renumbered(pilot.path, 2)\n"
            "    with pytest.raises(ValueError, match=\"pilot-v1.json and pilot-v2.json hold one\"):\n"
            "        frozen_pilots(directory)\n"
            "\n"
            "\n"
            "def test_a_manifest_without_its_evidence_is_refused(universe, layer, tmp_path) -> None:\n"
            "    directory = tmp_path / \"corpus\"\n"
            "    frozen = freeze(reviewed(universe, layer), layer, directory)\n"
            "    frozen.evidence_path.unlink()\n"
            "    with pytest.raises(ValueError, match=\"events-v1.json has no events-v1.evidence\"):\n"
            "        frozen_event_manifests(directory)\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task7-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_events_freeze.py -q`

Expected: FAIL: `3 failed, 38 passed`, each with `Failed: DID NOT RAISE ValueError`.

- [x] **Step 3: Refuse them when listing**

Create `/tmp/plan8-task7-source.py`:

```python
"""Plan 8: exact replacements for 4 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/data-dictionary.md": [
        (
            "  version; new content takes the next.\n",
            "  version; new content takes the next. `frozen_manifests` refuses two versions of one\n"
            "  content (PR #6's review, F22).\n",
        ),
        (
            "  the directory holds.\n",
            "  the directory holds. Listing the versions also refuses two that hold one content,\n"
            "  and a manifest whose evidence record is missing (PR #6's review, F22).\n",
        ),
        (
            "  whose pilots name more than one `pilot_id`, and `freeze_pilot` refuses a pilot of\n"
            "  a corpus other than the one the directory holds.\n",
            "  whose pilots name more than one `pilot_id`, or two versions of one content (F22),\n"
            "  and `freeze_pilot` refuses a pilot of a corpus other than the one the directory\n"
            "  holds.\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py": [
        (
            "def frozen_manifests(directory: Path, universe_id: str) -> list[UniverseManifest]:\n"
            "    \"\"\"Every frozen version of ``universe_id``, oldest first.\"\"\"\n"
            "    manifests = [\n"
            "        load_manifest(path) for path in sorted(directory.glob(f\"{universe_id}-v*.json\"))\n"
            "    ]\n"
            "    return sorted(manifests, key=lambda m: m.definition.universe_version)\n",
            "def repeated_content(named: list[tuple[str, str]]) -> None:\n"
            "    \"\"\"Refuse two frozen files, named in ``(name, content hash)`` pairs, that hold one\n"
            "    content: a version is its content (P6-14), so a copy renumbered by hand would load\n"
            "    beside it, and a consumer taking the latest version would read the copy (PR #6's\n"
            "    review, F22).\"\"\"\n"
            "    first: dict[str, str] = {}\n"
            "    for name, digest in named:\n"
            "        if digest in first:\n"
            "            raise ValueError(f\"{first[digest]} and {name} hold one content, {digest}\")\n"
            "        first[digest] = name\n"
            "\n"
            "\n"
            "def frozen_manifests(directory: Path, universe_id: str) -> list[UniverseManifest]:\n"
            "    \"\"\"Every frozen version of ``universe_id``, oldest first; refused if two hold one\n"
            "    content.\"\"\"\n"
            "    manifests = sorted(\n"
            "        (load_manifest(path) for path in directory.glob(f\"{universe_id}-v*.json\")),\n"
            "        key=lambda m: m.definition.universe_version,\n"
            "    )\n"
            "    repeated_content(\n"
            "        [\n"
            "            (\n"
            "                manifest_path(\n"
            "                    directory, universe_id, m.definition.universe_version\n"
            "                ).name,\n"
            "                m.definition.content_hash,\n"
            "            )\n"
            "            for m in manifests\n"
            "        ]\n"
            "    )\n"
            "    return manifests\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/freeze.py": [
        (
            "  loading refuses a directory that holds two.\n",
            "  loading refuses a directory that holds two. Listing them also refuses two versions\n"
            "  of one content, and a manifest whose evidence record is missing (PR #6's review,\n"
            "  F22); loading one file checks neither, since the pilot's chain check reads it\n"
            "  alone.\n",
        ),
        (
            "from earnings_ingestion.events.build import EventBuild\n",
            "from earnings_ingestion.cohort.freeze import repeated_content\n"
            "from earnings_ingestion.events.build import EventBuild\n",
        ),
        (
            "    than one corpus: a file names its version, not its corpus.\"\"\"\n"
            "    manifests = [\n"
            "        load_event_manifest(path)\n"
            "        for path in directory.glob(\"events-v*.json\")\n"
            "        if not path.name.endswith(\".evidence.json\")\n"
            "    ]\n"
            "    if len(corpora := sorted({m.definition.corpus_id for m in manifests})) > 1:\n"
            "        raise ValueError(f\"{directory} holds more than one corpus: {corpora}\")\n"
            "    return sorted(manifests, key=lambda m: m.definition.event_manifest_version)\n",
            "    than one corpus (a file names its version, not its corpus), if two hold one\n"
            "    content, or if a manifest's evidence record is missing.\"\"\"\n"
            "    manifests = sorted(\n"
            "        (\n"
            "            load_event_manifest(path)\n"
            "            for path in directory.glob(\"events-v*.json\")\n"
            "            if not path.name.endswith(\".evidence.json\")\n"
            "        ),\n"
            "        key=lambda m: m.definition.event_manifest_version,\n"
            "    )\n"
            "    if len(corpora := sorted({m.definition.corpus_id for m in manifests})) > 1:\n"
            "        raise ValueError(f\"{directory} holds more than one corpus: {corpora}\")\n"
            "    versions = [m.definition.event_manifest_version for m in manifests]\n"
            "    repeated_content(\n"
            "        [\n"
            "            (manifest_path(directory, version).name, m.definition.content_hash)\n"
            "            for version, m in zip(versions, manifests, strict=True)\n"
            "        ]\n"
            "    )\n"
            "    for version in versions:\n"
            "        if not evidence_path(directory, version).exists():\n"
            "            raise ValueError(\n"
            "                f\"{manifest_path(directory, version).name} has no\"\n"
            "                f\" {evidence_path(directory, version).name}\"\n"
            "            )\n"
            "    return manifests\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py": [
        (
            "from earnings_ingestion.cohort.identity import operative_hash\n",
            "from earnings_ingestion.cohort.freeze import repeated_content\n"
            "from earnings_ingestion.cohort.identity import operative_hash\n",
        ),
        (
            "    more than one ``pilot_id``, which is ``<corpus_id>-pilot`` whatever the policy:\n"
            "    a file names its version, not its corpus.\"\"\"\n"
            "    pilots = [_read_pilot(path) for path in directory.glob(\"pilot-v*.json\")]\n"
            "    if len(named := sorted({m.definition.pilot_id for m in pilots})) > 1:\n"
            "        raise ValueError(f\"{directory} holds more than one pilot: {named}\")\n"
            "    return sorted(pilots, key=lambda m: m.definition.pilot_version)\n",
            "    more than one ``pilot_id``, which is ``<corpus_id>-pilot`` whatever the policy\n"
            "    (a file names its version, not its corpus), or if two hold one content (PR #6's\n"
            "    review, F22).\"\"\"\n"
            "    pilots = sorted(\n"
            "        (_read_pilot(path) for path in directory.glob(\"pilot-v*.json\")),\n"
            "        key=lambda m: m.definition.pilot_version,\n"
            "    )\n"
            "    if len(named := sorted({m.definition.pilot_id for m in pilots})) > 1:\n"
            "        raise ValueError(f\"{directory} holds more than one pilot: {named}\")\n"
            "    repeated_content(\n"
            "        [\n"
            "            (\n"
            "                pilot_path(directory, m.definition.pilot_version).name,\n"
            "                m.definition.content_hash,\n"
            "            )\n"
            "            for m in pilots\n"
            "        ]\n"
            "    )\n"
            "    return pilots\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task7-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_events_freeze.py -q`

Expected: `41 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py packages/earnings-ingestion/src/earnings_ingestion/events/freeze.py packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_events_freeze.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1394 passed, 24 deselected`; `All checks passed!` and
`254 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py packages/earnings-ingestion/src/earnings_ingestion/events/freeze.py packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_events_freeze.py
git commit -m "fix(events): refuse a frozen version that repeats another's content or lacks its evidence (F22)"
```

---

### Task 8: Loading a pilot selects it again (F10)

PR #6's review, F10, as the user decided it (P8-3). `check_chain` rechecked the hashes,
the seed, and eligibility, but not that `djia-pilot/1` produces the rows. Plan B's
gate is that the pilot loads and its chain checks, so `load_pilot` now also requires
the policy to be `djia-pilot/1`, and `select_pilot` over the pilot's event manifest
and universe to reproduce its content hash. The tamper tests rehash each edited pilot:
a row's event exchanged with another's, another policy, another `pilot_id`, and
`underfilled` flipped. The committed events v1 and pilot v1 reload and reselect.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py` and
  `docs/data-dictionary.md`.
- Test (modify, by exact replacement):
  `packages/earnings-ingestion/tests/test_events_pilot.py` and
  `tests/integration/test_event_corpus_v1.py`.

**Interfaces:**

- Consumes: `load_pilot(path, universe) -> PilotManifest`, `check_chain`, and
  `select_pilot(events, universe) -> PilotSelection` in `events/pilot.py`.
- Produces: `load_pilot` raises `ValueError` with "names `<policy>`, not
  djia-pilot/1" for another policy, and "selects ..." when the policy selects another
  pilot.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task8-tests.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_events_pilot.py": [
        (
            "def rehashed(manifest: EventManifest) -> EventManifest:\n",
            "@pytest.mark.parametrize(\"tamper\", [\"exchanged\", \"policy\", \"pilot_id\", \"underfilled\"])\n"
            "def test_loading_selects_again(corpus, universe, tmp_path, tamper) -> None:\n"
            "    \"\"\"A hand-edited pilot whose content hash is recomputed is refused, because\n"
            "    djia-pilot/1 over its event manifest and universe selects another (PR #6's\n"
            "    review, F10). A pilot naming another policy is refused before selecting.\"\"\"\n"
            "    frozen = freeze_pilot(\n"
            "        select_pilot(events_of(corpus), universe), universe, corpus, now=NOW\n"
            "    )\n"
            "    manifest, definition = frozen.manifest, frozen.manifest.definition\n"
            "    if tamper == \"exchanged\":\n"
            "        one, two, *rest = manifest.rows\n"
            "        rows = (\n"
            "            one.model_copy(update={\"event_id\": two.event_id}),\n"
            "            two.model_copy(update={\"event_id\": one.event_id}),\n"
            "            *rest,\n"
            "        )\n"
            "        manifest = manifest.model_copy(update={\"rows\": rows})\n"
            "    elif tamper == \"policy\":\n"
            "        seed = pilot_seed(\n"
            "            definition.eligible_event_manifest_hash,\n"
            "            definition.universe_operative_hash,\n"
            "            \"djia-pilot/2\",\n"
            "        )\n"
            "        definition = definition.model_copy(\n"
            "            update={\"selection_policy_version\": \"djia-pilot/2\", \"selection_seed\": seed}\n"
            "        )\n"
            "    elif tamper == \"pilot_id\":\n"
            "        definition = definition.model_copy(update={\"pilot_id\": \"djia-other-pilot\"})\n"
            "    else:\n"
            "        definition = definition.model_copy(update={\"underfilled\": False})\n"
            "    manifest = manifest.model_copy(update={\"definition\": definition})\n"
            "    hashed = definition.model_copy(\n"
            "        update={\"content_hash\": pilot_content_hash(manifest)}\n"
            "    )\n"
            "    frozen.path.write_bytes(\n"
            "        serialize(manifest.model_copy(update={\"definition\": hashed}))\n"
            "    )\n"
            "    message = \"names djia-pilot/2, not\" if tamper == \"policy\" else \"selects \"\n"
            "    with pytest.raises(ValueError, match=message):\n"
            "        load_pilot(frozen.path, universe)\n"
            "\n"
            "\n"
            "def rehashed(manifest: EventManifest) -> EventManifest:\n",
        ),
    ],
    "tests/integration/test_event_corpus_v1.py": [
        (
            "from pathlib import Path\n"
            "\n",
            "import shutil\n"
            "from pathlib import Path\n"
            "\n"
            "import pytest\n",
        ),
        (
            ")\n"
            "from earnings_ingestion.events.pilot import frozen_pilots, load_pilot, select_pilot\n",
            "    serialize,\n"
            ")\n"
            "from earnings_ingestion.events.pilot import frozen_pilots, load_pilot, select_pilot\n"
            "from earnings_ingestion.events.records import EventStatus, pilot_content_hash\n",
        ),
        (
            "def test_the_overrides_load() -> None:\n",
            "def test_a_pilot_with_a_row_swapped_for_another_eligible_event_is_refused(\n"
            "    tmp_path,\n"
            ") -> None:\n"
            "    \"\"\"Hashes, seed, and eligibility all check for a pilot whose row is swapped for an\n"
            "    unselected eligible event, its hash recomputed; only selecting again refuses it\n"
            "    (PR #6's review, F10).\"\"\"\n"
            "    universe = load_manifest(UNIVERSE)\n"
            "    events = load_event_manifest(CORPUS / \"events-v1.json\")\n"
            "    pilot = load_pilot(CORPUS / \"pilot-v1.json\", universe)\n"
            "    taken = {row.event_id for row in pilot.rows}\n"
            "    other = next(\n"
            "        row.event_id\n"
            "        for row in events.rows\n"
            "        if row.eligibility_status is EventStatus.ELIGIBLE and row.event_id not in taken\n"
            "    )\n"
            "    first = pilot.rows[0].model_copy(update={\"event_id\": other})\n"
            "    swapped = pilot.model_copy(update={\"rows\": (first, *pilot.rows[1:])})\n"
            "    definition = swapped.definition.model_copy(\n"
            "        update={\"content_hash\": pilot_content_hash(swapped)}\n"
            "    )\n"
            "    swapped = swapped.model_copy(update={\"definition\": definition})\n"
            "    shutil.copy(CORPUS / \"events-v1.json\", tmp_path / \"events-v1.json\")\n"
            "    (tmp_path / \"pilot-v1.json\").write_bytes(serialize(swapped))\n"
            "    with pytest.raises(ValueError, match=\"djia-pilot/1 over events-v1.json selects\"):\n"
            "        load_pilot(tmp_path / \"pilot-v1.json\", universe)\n"
            "\n"
            "\n"
            "def test_the_overrides_load() -> None:\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task8-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_pilot.py tests/integration/test_event_corpus_v1.py -q`

Expected: FAIL: `5 failed, 40 passed`, each with `Failed: DID NOT RAISE ValueError`:
the four tamperings of `test_loading_selects_again`, and
`test_a_pilot_with_a_row_swapped_for_another_eligible_event_is_refused` on pilot v1.

- [x] **Step 3: Select again when loading**

Create `/tmp/plan8-task8-source.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/data-dictionary.md": [
        (
            "  manifest; the seed; and that every row is an eligible event of that manifest.\n",
            "  manifest; the seed; and that every row is an eligible event of that manifest. It\n"
            "  then selects again: the pilot must name `djia-pilot/1`, and the policy run over\n"
            "  its event manifest and universe must reproduce its `content_hash` (PR #6's review,\n"
            "  F10).\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py": [
        (
            "whose operative hash is computed again.\n",
            "whose operative hash is computed again. It then selects again: the pilot must name\n"
            "``djia-pilot/1``, and the policy run over its event manifest and universe must\n"
            "reproduce its content hash, so a hand-edited pilot with its hash recomputed is\n"
            "refused (PR #6's review, F10; plan 8, P8-3). A frozen pilot's loading so depends on\n"
            "this code, and a change in what the policy selects must come as a new policy name,\n"
            "as the spec's §Pilot selection requires.\n",
        ),
        (
            "    \"\"\"A frozen pilot, refused unless its hash, its name, and its chain check.\"\"\"\n"
            "    manifest = _read_pilot(path)\n"
            "    check_chain(manifest, path.parent, universe)\n",
            "    \"\"\"A frozen pilot, refused unless its hash, its name, and its chain check, and\n"
            "    unless ``djia-pilot/1`` reselects it.\"\"\"\n"
            "    manifest = _read_pilot(path)\n"
            "    events = check_chain(manifest, path.parent, universe)\n"
            "    definition = manifest.definition\n"
            "    if definition.selection_policy_version != PILOT_POLICY:\n"
            "        raise ValueError(\n"
            "            f\"{path.name} names {definition.selection_policy_version}, not\"\n"
            "            f\" {PILOT_POLICY}, the policy this code runs\"\n"
            "        )\n"
            "    derived = select_pilot(events, universe).content_hash\n"
            "    if derived != definition.content_hash:\n"
            "        raise ValueError(\n"
            "            f\"{PILOT_POLICY} over events-v{definition.event_manifest_version}.json\"\n"
            "            f\" selects {derived}, not {path.name}\"\n"
            "        )\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task8-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_pilot.py tests/integration/test_event_corpus_v1.py -q`

Expected: `45 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py packages/earnings-ingestion/tests/test_events_pilot.py tests/integration/test_event_corpus_v1.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1399 passed, 24 deselected`; `All checks passed!` and
`254 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py packages/earnings-ingestion/tests/test_events_pilot.py tests/integration/test_event_corpus_v1.py
git commit -m "feat(events): loading a pilot selects it again (F10)"
```

---

### Task 9: The build decides which frozen version is current (F4)

PR #6's review, F4, as the user decided it (P8-4). `events select` read the
highest-numbered event manifest, and printed neither the version nor the hash it
read, so a change frozen as v2 and then reverted drew a pilot from the withdrawn v2.

- `events/freeze.py` gains `current_events(build, directory)`: the frozen version
  whose content hash the build reproduces. It refuses while the build holds the
  freeze, and when no version holds the content.
- `events/pilot.py` gains `current_pilot(directory, events, universe)`: the pilot
  frozen over the current event manifest, loaded by `load_pilot`.
- `events select` builds offline, reads the current version, and prints "reads
  `<corpus>` v`<N>`" with its path and hash. Task 19's `events acquire` reads both
  the same way.
- `cohort freeze` refuses a build that holds an older cohort version's content,
  since every consumer reads a universe's latest version.
- S §Commands gains the amendment that records the rule, superseding P7-18's
  "latest". The data dictionary's reading notes follow.

On the real corpus, the rebuild's content hash is still events v1's, `2348671b…`, so
`current_events` is events v1 and `current_pilot` is pilot v1.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py`,
  `events/freeze.py`, and `events/pilot.py`;
  `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py` and `events_cli.py`;
  `docs/data-dictionary.md`; and
  `specs/event-discovery-eligibility-and-acquisition.md`, its §Commands only.
- Test (modify, by exact replacement):
  `packages/earnings-ingestion/tests/test_cohort_build.py` and
  `test_events_freeze.py`; `apps/earnings-pipeline/tests/test_cohort_cli.py` and
  `test_events_cli.py`.

**Interfaces:**

- Consumes: `EventBuild`, with its `content_hash` and whether it holds the freeze;
  `frozen_event_manifests(directory)`, `FrozenEvents`, `frozen_pilots(directory)`,
  and `load_pilot`, from Tasks 7 and 8.
- Produces:
  - `current_events(build: EventBuild, directory: Path) -> FrozenEvents` in
    `events/freeze.py`, with `created=False`;
  - `current_pilot(directory: Path, events: EventManifest, universe:
    UniverseManifest) -> FrozenPilot` in `events/pilot.py`;
  - `_current(layout) -> tuple[FrozenEvents, UniverseManifest]` in `events_cli.py`,
    which Task 19's `acquire_command` reuses.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task9-tests.py`:

```python
"""Plan 8: exact replacements for 4 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/tests/test_cohort_cli.py": [
        (
            "    assert \"BLOCKING  membership_conflict:corvid-common\" in result.stderr\n"
            "\n"
            "\n",
            "    assert \"BLOCKING  membership_conflict:corvid-common\" in result.stderr\n"
            "\n"
            "\n"
            "def test_freeze_refuses_a_revert(repo) -> None:\n"
            "    universe = repo / FIXTURE_DIR / \"universe.toml\"\n"
            "    text = universe.read_text(encoding=\"utf-8\")\n"
            "    one, two = (f'selection_policy_version = \"djia-pilot/{n}\"' for n in (1, 2))\n"
            "    universe.write_text(text.replace(one, two, 1), encoding=\"utf-8\")\n"
            "    assert \"froze djia-synthetic v2\" in run(repo, \"freeze\").stdout\n"
            "    universe.write_text(text, encoding=\"utf-8\")\n"
            "    result = run(repo, \"freeze\")\n"
            "    assert result.exit_code == 1\n"
            "    assert isinstance(result.exception, SystemExit), result.exception\n"
            "    assert \"Refused: the build is djia-synthetic-v1.json's content, but v2\" in (\n"
            "        result.stderr\n"
            "    )\n"
            "\n"
            "\n",
        ),
    ],
    "apps/earnings-pipeline/tests/test_events_cli.py": [
        (
            "from earnings_ingestion.events.layer import DYNAMO, RETRIEVED, filings\n"
            "from earnings_ingestion.events.saved import SavedResponses\n"
            "from earnings_ingestion.events.synthetic import save, submissions_file\n",
            "from earnings_ingestion.events.layer import CORVID, DYNAMO, REPORTS, RETRIEVED, filings\n"
            "from earnings_ingestion.events.saved import SavedResponses\n"
            "from earnings_ingestion.events.synthetic import SyntheticStore, save, submissions_file\n",
        ),
        (
            "    assert lines[0] == \"  1  cik-0009990003:2026-03-31  issuer_coverage\"\n"
            "    assert lines[27] == (\n",
            "    assert lines[:2] == [\n"
            "        \"reads djia-synthetic v1\",\n"
            "        f\"tests/fixtures/events/events-v1.json  {EVENTS_HASH}\",\n"
            "    ]\n"
            "    assert lines[2] == \"  1  cik-0009990003:2026-03-31  issuer_coverage\"\n"
            "    assert lines[29] == (\n",
        ),
        (
            "    assert lines[28:] == [\n",
            "    assert lines[30:] == [\n",
        ),
        (
            "    assert \"Refused: no frozen event manifest in tests/fixtures/events\" in (\n"
            "        result.stderr\n"
            "    )\n",
            "    assert \"Refused: no frozen event manifest holds this build's content\" in (\n"
            "        result.stderr\n"
            "    )\n"
            "\n"
            "\n"
            "def test_select_reads_the_version_the_build_reproduces(repo) -> None:\n"
            "    \"\"\"Freeze v1, freeze a changed v2, revert, and select: the build decides which\n"
            "    version is current, so select reads v1 and names pilot v1 again (PR #6's\n"
            "    review, F4).\"\"\"\n"
            "    raw = repo / FIXTURE_DIR / \"raw\"\n"
            "\n"
            "    def corvid(days: int, *, agreeing: bool) -> None:\n"
            "        facts = [\n"
            "            (filing.accession, year, period)\n"
            "            for filing, report in filings(CORVID)\n"
            "            if report in REPORTS[CORVID]\n"
            "            for year, period in (report.labels[:1] if agreeing else report.labels)\n"
            "        ]\n"
            "        at = RETRIEVED + timedelta(days=days)\n"
            "        SyntheticStore(raw, repo, at).companyfacts(CORVID.cik, CORVID.name, facts)\n"
            "\n"
            "    corvid(1, agreeing=True)\n"
            "    assert run(repo, \"freeze\").stdout.splitlines()[0] == \"froze djia-synthetic v2\"\n"
            "    changed = run(repo, \"select\").stdout.splitlines()\n"
            "    assert changed[0] == \"reads djia-synthetic v2\"\n"
            "    assert changed[-2].startswith(\"froze djia-synthetic-pilot v2: \")\n"
            "    corvid(2, agreeing=False)\n"
            "    assert run(repo, \"freeze\").stdout.splitlines()[0] == \"unchanged: djia-synthetic v1\"\n"
            "    result = run(repo, \"select\")\n"
            "    assert result.exit_code == 0, result.output\n"
            "    lines = result.stdout.splitlines()\n"
            "    assert lines[:2] == [\n"
            "        \"reads djia-synthetic v1\",\n"
            "        f\"tests/fixtures/events/events-v1.json  {EVENTS_HASH}\",\n"
            "    ]\n"
            "    assert lines[-2:] == [\n"
            "        \"unchanged: djia-synthetic-pilot v1: 27 of target 27, underfilled\",\n"
            "        f\"tests/fixtures/events/pilot-v1.json  {PILOT_HASH}\",\n"
            "    ]\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_cohort_build.py": [
        (
            "def test_two_versions_of_one_content_are_refused(repo) -> None:\n",
            "def test_a_revert_to_an_older_version_is_refused(repo) -> None:\n"
            "    \"\"\"Every consumer reads a universe's latest version, so a build that holds an\n"
            "    older version's content while a newer one exists is refused, not named (PR #6's\n"
            "    review, F4).\"\"\"\n"
            "    manifests = repo / DIRECTORY / \"manifests\"\n"
            "    one, two = (f'selection_policy_version = \"djia-pilot/{n}\"' for n in (1, 2))\n"
            "    edit(repo, \"universe.toml\", one, two)\n"
            "    assert freeze(build(repo, **OPTIONS), manifests, now=LATER).created\n"
            "    edit(repo, \"universe.toml\", two, one)\n"
            "    with pytest.raises(ValueError, match=\"is djia-synthetic-v1.json's content, but v2\"):\n"
            "        freeze(build(repo, **OPTIONS), manifests, now=LATER)\n"
            "    assert sorted(path.name for path in manifests.iterdir()) == [\n"
            "        \"djia-synthetic-v1.json\",\n"
            "        \"djia-synthetic-v2.json\",\n"
            "    ]\n"
            "\n"
            "\n"
            "def test_two_versions_of_one_content_are_refused(repo) -> None:\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_events_freeze.py": [
        (
            "    freeze_events,\n",
            "    current_events,\n"
            "    freeze_events,\n",
        ),
        (
            "from earnings_ingestion.events.pilot import freeze_pilot, frozen_pilots, select_pilot\n",
            "from earnings_ingestion.events.pilot import (\n"
            "    current_pilot,\n"
            "    freeze_pilot,\n"
            "    frozen_pilots,\n"
            "    select_pilot,\n"
            ")\n",
        ),
        (
            "LATER = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)\n"
            "\n"
            "\n",
            "LATER = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)\n"
            "LATEST = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)\n"
            "\n"
            "\n",
        ),
        (
            "def test_a_changed_fact_writes_the_next_version(universe, layer, tmp_path) -> None:\n",
            "def corvid_facts(*, agreeing: bool) -> list[tuple[str, int, str]]:\n"
            "    \"\"\"Corvid's companyfacts facts: each report's labels, as the layer saves them, or\n"
            "    only its first, so that they agree.\"\"\"\n"
            "    return [\n"
            "        (filing.accession, year, period)\n"
            "        for filing, report in filings(CORVID)\n"
            "        if report in REPORTS[CORVID]\n"
            "        for year, period in (report.labels[:1] if agreeing else report.labels)\n"
            "    ]\n"
            "\n"
            "\n"
            "def test_a_changed_fact_writes_the_next_version(universe, layer, tmp_path) -> None:\n",
        ),
        (
            "    listed = filings(CORVID)\n"
            "    facts = [\n"
            "        (filing.accession, report.labels[0][0], report.labels[0][1])\n"
            "        for filing, report in listed\n"
            "        if report in REPORTS[CORVID]\n"
            "    ]\n"
            "    again.companyfacts(CORVID.cik, CORVID.name, facts)\n",
            "    again.companyfacts(CORVID.cik, CORVID.name, corvid_facts(agreeing=True))\n",
        ),
        (
            "    with pytest.raises(ValueError, match=\"events-v1.json has no events-v1.evidence\"):\n"
            "        frozen_event_manifests(directory)\n",
            "    with pytest.raises(ValueError, match=\"events-v1.json has no events-v1.evidence\"):\n"
            "        frozen_event_manifests(directory)\n"
            "\n"
            "\n"
            "def test_the_build_decides_which_version_is_current(universe, layer, tmp_path) -> None:\n"
            "    \"\"\"A change frozen as v2 and then reverted leaves v1 current, and the pilot\n"
            "    frozen over v1 with it (PR #6's review, F4).\"\"\"\n"
            "    directory = tmp_path / \"corpus\"\n"
            "    before = reviewed(universe, layer)\n"
            "    first = freeze(before, layer, directory)\n"
            "    first_pilot = freeze_pilot(\n"
            "        select_pilot(first.manifest, universe), universe, directory, now=NOW\n"
            "    )\n"
            "    changed = SyntheticStore(layer.store.root, layer.store.repo, LATER)\n"
            "    changed.companyfacts(CORVID.cik, CORVID.name, corvid_facts(agreeing=True))\n"
            "    second = freeze(build(universe, changed, before.overrides), changed, directory)\n"
            "    freeze_pilot(select_pilot(second.manifest, universe), universe, directory, now=NOW)\n"
            "    assert (second.path.name, len(frozen_pilots(directory))) == (\"events-v2.json\", 2)\n"
            "    reverted = SyntheticStore(layer.store.root, layer.store.repo, LATEST)\n"
            "    reverted.companyfacts(CORVID.cik, CORVID.name, corvid_facts(agreeing=False))\n"
            "    current = current_events(build(universe, reverted, before.overrides), directory)\n"
            "    assert (current.path, current.created) == (first.path, False)\n"
            "    pilot = current_pilot(directory, current.manifest, universe)\n"
            "    assert (pilot.path, pilot.manifest) == (first_pilot.path, first_pilot.manifest)\n"
            "\n"
            "\n"
            "def test_no_current_version_without_a_frozen_one_that_holds_the_build(\n"
            "    universe, layer, tmp_path\n"
            ") -> None:\n"
            "    directory = tmp_path / \"corpus\"\n"
            "    before = reviewed(universe, layer)\n"
            "    with pytest.raises(EventFreezeRefused):\n"
            "        current_events(build(universe, layer), directory)\n"
            "    with pytest.raises(ValueError, match=\"no frozen event manifest holds this build\"):\n"
            "        current_events(before, directory)\n"
            "    frozen = freeze(before, layer, directory)\n"
            "    with pytest.raises(ValueError, match=\"no pilot is frozen over events-v1.json\"):\n"
            "        current_pilot(directory, frozen.manifest, universe)\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task9-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_events_freeze.py -q`

Expected: FAIL: `1 error`, collecting `test_events_freeze.py`, with
`ImportError: cannot import name 'current_events' from 'earnings_ingestion.events.freeze'`.

- [x] **Step 3: Let the build decide, and record the rule**

Create `/tmp/plan8-task9-source.py`:

```python
"""Plan 8: exact replacements for 7 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py": [
        (
            "repository in full (``earnings_pipeline.paths``).\n",
            "repository in full (``earnings_pipeline.paths``). ``freeze`` refuses a revert, a build\n"
            "that holds an older version's content, since every consumer reads a universe's\n"
            "latest version (PR #6's review, F4).\n",
        ),
        (
            "    \"\"\"Freeze the build as a new version, or name the version that already holds it.\"\"\"\n",
            "    \"\"\"Freeze the build as a new version, or name the latest version when it already\n"
            "    holds the build; refuse a build that holds an older version (plan 8, P8-4).\"\"\"\n",
        ),
        (
            "    verb = \"froze\" if frozen.created else \"unchanged:\"\n",
            "    except ValueError as error:\n"
            "        _fail(f\"Refused: {error}\")\n"
            "    verb = \"froze\" if frozen.created else \"unchanged:\"\n",
        ),
    ],
    "apps/earnings-pipeline/src/earnings_pipeline/events_cli.py": [
        (
            "corpus, and ``select`` refuses unless the latest event manifest is ``--corpus-id``'s.\n",
            "corpus, and ``select`` one whose ``--corpus-id`` is not the directory's. The build\n"
            "decides which event manifest is current: ``select`` builds offline and reads the\n"
            "version that holds the build's content, which a revert makes an earlier one, and\n"
            "prints the version and hash it read (PR #6's review, F4; plan 8, P8-4).\n",
        ),
        (
            "    freeze_events,\n"
            "    frozen_event_manifests,\n",
            "    FrozenEvents,\n"
            "    current_events,\n"
            "    freeze_events,\n",
        ),
        (
            "        for reason in error.reasons:\n"
            "            typer.echo(f\"HOLDS  {reason}\", err=True)\n"
            "        raise typer.Exit(1) from error\n",
            "        _holds(error)\n",
        ),
        (
            "@events.command(\"select\")\n"
            "def select_command(context: typer.Context) -> None:\n"
            "    \"\"\"Run djia-pilot/1 on the latest frozen event manifest, and freeze the pilot.\"\"\"\n"
            "    layout: Layout = context.obj\n"
            "    try:\n"
            "        manifests = frozen_event_manifests(layout.corpus())\n"
            "    except ValueError as error:\n"
            "        _fail(f\"Refused: {error}\")\n"
            "    if not manifests:\n"
            "        _fail(f\"Refused: no frozen event manifest in {layout.corpus_dir}\")\n"
            "    frozen_events = manifests[-1]\n"
            "    read = frozen_events.definition\n"
            "    if read.corpus_id != layout.corpus_id:\n"
            "        _fail(\n"
            "            f\"Refused: {layout.corpus_dir} holds corpus {read.corpus_id},\"\n"
            "            f\" not {layout.corpus_id}\"\n"
            "        )\n",
            "def _holds(error: EventFreezeRefused) -> NoReturn:\n"
            "    for reason in error.reasons:\n"
            "        typer.echo(f\"HOLDS  {reason}\", err=True)\n"
            "    raise typer.Exit(1) from error\n"
            "\n"
            "\n"
            "def _current(layout: Layout) -> tuple[FrozenEvents, UniverseManifest]:\n"
            "    \"\"\"The event manifest the build reproduces, printed with its version and hash,\n"
            "    and the universe version it read (plan 8, P8-4).\"\"\"\n"
            "    built, _ = _build(layout)\n"
            "    try:\n"
            "        current = current_events(built, layout.corpus())\n"
            "    except EventFreezeRefused as error:\n"
            "        _holds(error)\n"
            "    except ValueError as error:\n"
            "        _fail(f\"Refused: {error}\")\n"
            "    read = current.manifest.definition\n"
            "    typer.echo(f\"reads {read.corpus_id} v{read.event_manifest_version}\")\n"
            "    typer.echo(f\"{shown(current.path, layout.repo)}  {read.content_hash}\")\n",
        ),
        (
            "    universe = matching[0]\n"
            "    try:\n"
            "        pilot = select_pilot(frozen_events, universe)\n",
            "    return current, matching[0]\n"
            "\n"
            "\n"
            "@events.command(\"select\")\n"
            "def select_command(context: typer.Context) -> None:\n"
            "    \"\"\"Run djia-pilot/1 on the event manifest the build reproduces, and freeze the\n"
            "    pilot.\"\"\"\n"
            "    layout: Layout = context.obj\n"
            "    current, universe = _current(layout)\n"
            "    try:\n"
            "        pilot = select_pilot(current.manifest, universe)\n",
        ),
    ],
    "docs/data-dictionary.md": [
        (
            "  version; new content takes the next. `frozen_manifests` refuses two versions of one\n"
            "  content (PR #6's review, F22).\n",
            "  version; new content takes the next. Every consumer reads the latest version, so\n"
            "  `freeze` refuses a build that holds an older version's content, and\n"
            "  `frozen_manifests` refuses two versions of one content (PR #6's review, F4, F22).\n",
        ),
        (
            "- **The content hash.** `content_hash` covers the canonical JSON of the definition,\n"
            "  less `event_manifest_version`, `universe_version`, `content_hash`, and `created_at`,\n",
            "- **The current version.** The build decides it: `current_events(build, directory)`\n"
            "  is the version that holds the build's content, which a revert makes an earlier\n"
            "  one. It refuses while the build holds the freeze, and when no version holds the\n"
            "  content. `events select` and `events acquire` read it, and print its version and\n"
            "  hash (PR #6's review, F4; plan 8, P8-4).\n"
            "- **The content hash.** `content_hash` covers the canonical JSON of the definition,\n"
            "  less `event_manifest_version`, `universe_version`, `content_hash`, and `created_at`,\n",
        ),
        (
            "  F10).\n",
            "  F10).\n"
            "- **The current pilot.** `current_pilot(directory, events, universe)` is the pilot\n"
            "  frozen over the current event manifest, loaded by `load_pilot` (F4).\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py": [
        (
            "  creation time. A build whose content matches a frozen manifest *is* that version,\n"
            "  and nothing is written; different content is the next version.\n",
            "  creation time. A build whose content matches the latest frozen manifest *is* that\n"
            "  version, and nothing is written; different content is the next version. Every\n"
            "  consumer reads a universe's latest version, so a build that holds an older\n"
            "  version's content is refused: a universe is never reverted (PR #6's review, F4;\n"
            "  plan 8, P8-4).\n",
        ),
        (
            "    for manifest in existing:\n",
            "    newest = max((m.definition.universe_version for m in existing), default=0)\n"
            "    for manifest in existing:\n",
        ),
        (
            "            return Frozen(manifest=manifest, path=path, created=False)\n"
            "    version = 1 + max((m.definition.universe_version for m in existing), default=0)\n",
            "            if manifest.definition.universe_version != newest:\n"
            "                raise ValueError(\n"
            "                    f\"the build is {path.name}'s content, but v{newest} is newer:\"\n"
            "                    \" every consumer reads a universe's latest version, so a revert\"\n"
            "                    \" is refused\"\n"
            "                )\n"
            "            return Frozen(manifest=manifest, path=path, created=False)\n"
            "    version = 1 + newest\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/freeze.py": [
        (
            "- Loading reads the committed JSON alone and rechecks the content hash and the name.\n",
            "- The build decides which version is current (PR #6's review, F4; plan 8, P8-4):\n"
            "  ``current_events`` is the version that holds the build's content, so a change\n"
            "  frozen as v2 and then reverted makes v1 current again. It refuses while the build\n"
            "  holds the freeze, and when no version holds its content. ``events select`` and\n"
            "  ``events acquire`` read it, never the highest-numbered version.\n"
            "- Loading reads the committed JSON alone and rechecks the content hash and the name.\n",
        ),
        (
            "def freeze_events(\n"
            "    build: EventBuild, saved: SavedResponses, directory: Path, *, now: datetime\n"
            ") -> FrozenEvents:\n"
            "    \"\"\"Freeze ``build`` into ``directory``, or return the version that holds it.\n"
            "    Refused if ``directory`` holds another corpus.\"\"\"\n",
            "def _versions(build: EventBuild, directory: Path) -> list[EventManifest]:\n"
            "    \"\"\"The versions in ``directory``, refused while ``build`` holds the freeze, or\n"
            "    if ``directory`` holds another corpus.\"\"\"\n",
        ),
        (
            "    for manifest in existing:\n",
            "    return existing\n"
            "\n"
            "\n"
            "def _holding(\n"
            "    build: EventBuild, directory: Path, existing: list[EventManifest]\n"
            ") -> FrozenEvents | None:\n"
            "    \"\"\"The version among ``existing`` that holds ``build``'s content.\"\"\"\n"
            "    for manifest in existing:\n",
        ),
        (
            "    version = 1 + max(\n",
            "    return None\n"
            "\n"
            "\n"
            "def current_events(build: EventBuild, directory: Path) -> FrozenEvents:\n"
            "    \"\"\"The frozen version that holds ``build``'s content: the current version, which\n"
            "    need not be the highest-numbered. Refused while ``build`` holds the freeze, and\n"
            "    when no version holds its content, since then it is not frozen.\"\"\"\n"
            "    held = _holding(build, directory, _versions(build, directory))\n"
            "    if held is None:\n"
            "        raise ValueError(\n"
            "            f\"no frozen event manifest holds this build's content,\"\n"
            "            f\" {build.content_hash}: run events freeze\"\n"
            "        )\n"
            "    return held\n"
            "\n"
            "\n"
            "def freeze_events(\n"
            "    build: EventBuild, saved: SavedResponses, directory: Path, *, now: datetime\n"
            ") -> FrozenEvents:\n"
            "    \"\"\"Freeze ``build`` into ``directory``, or return the version that holds it.\n"
            "    Refused if ``directory`` holds another corpus.\"\"\"\n"
            "    existing = _versions(build, directory)\n"
            "    if (held := _holding(build, directory, existing)) is not None:\n"
            "        return held\n"
            "    version = 1 + max(\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py": [
        (
            "as the spec's §Pilot selection requires.\n"
            "\"\"\"\n"
            "\n",
            "as the spec's §Pilot selection requires.\n"
            "\n"
            "The current pilot is the one frozen over the current event manifest, which the\n"
            "build decides (``current_pilot``; PR #6's review, F4; plan 8, P8-4), never the\n"
            "highest-numbered.\n"
            "\"\"\"\n"
            "\n",
        ),
        (
            "def frozen_pilots(directory: Path) -> list[PilotManifest]:\n",
            "def current_pilot(\n"
            "    directory: Path, events: EventManifest, universe: UniverseManifest\n"
            ") -> FrozenPilot:\n"
            "    \"\"\"The pilot frozen over ``events``, the current event manifest, loaded: its\n"
            "    chain checked against ``universe``, and reselected. Refused unless exactly one\n"
            "    version in ``directory`` names ``events``.\"\"\"\n"
            "    definition = events.definition\n"
            "    name = manifest_path(directory, definition.event_manifest_version).name\n"
            "    over = [\n"
            "        pilot\n"
            "        for pilot in frozen_pilots(directory)\n"
            "        if (\n"
            "            pilot.definition.event_manifest_version,\n"
            "            pilot.definition.eligible_event_manifest_hash,\n"
            "        )\n"
            "        == (definition.event_manifest_version, definition.content_hash)\n"
            "    ]\n"
            "    if not over:\n"
            "        raise ValueError(f\"no pilot is frozen over {name}: run events select\")\n"
            "    if len(over) > 1:\n"
            "        versions = [pilot.definition.pilot_version for pilot in over]\n"
            "        raise ValueError(f\"pilot versions {versions} are all frozen over {name}\")\n"
            "    path = pilot_path(directory, over[0].definition.pilot_version)\n"
            "    return FrozenPilot(load_pilot(path, universe), path, created=False)\n"
            "\n"
            "\n"
            "def frozen_pilots(directory: Path) -> list[PilotManifest]:\n",
        ),
    ],
    "specs/event-discovery-eligibility-and-acquisition.md": [
        (
            "- **`events select`** runs `djia-pilot/1` on the latest frozen event manifest and\n"
            "  freezes the pilot.\n",
            "- **`events select`** runs `djia-pilot/1` on the current event manifest and freezes\n"
            "  the pilot.\n"
            "- *Amended 2026-09-28, by the user's decision on PR #6's review, F4 (plan 8, P8-4):*\n"
            "  the build decides which version is current. `events select` and `events acquire`\n"
            "  rebuild offline and read the frozen event manifest whose content hash the build\n"
            "  reproduces. They refuse while the build holds the freeze, or when no version holds\n"
            "  its content, and each prints the version and hash it read. The current pilot is\n"
            "  the one frozen over that manifest. So a change frozen as v2 and then reverted makes\n"
            "  v1 current again, where \"the latest frozen event manifest\", which this section\n"
            "  said before and plan 7's P7-18 followed, would have drawn a pilot from the\n"
            "  withdrawn v2. A universe stays \"the latest version\" for every consumer, since the\n"
            "  real cohort's rebuild no longer reproduces v1's content hash (plan 7, P7-3). So\n"
            "  `cohort freeze` refuses a build that holds an older version's content: a universe\n"
            "  is never reverted.\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task9-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_events_freeze.py -q`

Expected: `84 passed`.

- [x] **Step 5: Check the real corpus offline**

The real corpus's current version must still be events v1 and pilot v1. This reads
committed files and the saved responses, and sends nothing:

```bash
uv run --locked --all-packages python - <<'EOF'
from pathlib import Path

from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.build import CORPUS_ID, build_events, load_overrides
from earnings_ingestion.events.freeze import current_events
from earnings_ingestion.events.pilot import current_pilot
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.store import ArtifactStore

repo = Path.cwd()
corpus = repo / "config/corpus/djia-2024q3-2026q2"
universe = load_manifest(repo / "config/universe/djia/manifests/djia-2024q3-2026q2-v1.json")
saved = SavedResponses(ArtifactStore(repo / "data/raw/events", repo))
build = build_events(
    universe, saved, load_overrides(corpus / "overrides.toml"), corpus_id=CORPUS_ID
)
events = current_events(build, corpus)
pilot = current_pilot(corpus, events.manifest, universe)
print(events.path.name, events.manifest.definition.content_hash[:8])
print(pilot.path.name, pilot.manifest.definition.content_hash[:8])
EOF
```

Expected: `events-v1.json 2348671b` and `pilot-v1.json 3839c800`.

- [x] **Step 6: Run the checks**

```bash
python3 /tmp/plan8-escapes.py apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py packages/earnings-ingestion/src/earnings_ingestion/events/freeze.py packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_events_freeze.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1404 passed, 24 deselected`; `All checks passed!` and
`254 files already formatted`.

- [x] **Step 7: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/tests/test_cohort_cli.py apps/earnings-pipeline/tests/test_events_cli.py docs/data-dictionary.md packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py packages/earnings-ingestion/src/earnings_ingestion/events/freeze.py packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_events_freeze.py specs/event-discovery-eligibility-and-acquisition.md
git commit -m "feat(events): the build decides which frozen version is current (F4)"
```

---

### Task 10: The real records quote no saved page (F20)

PR #6's review, F20, and P8-5. Plan 7's gates checked the real records against the
saved pages with a scratch script, and the committed P6-3 test reads only the
synthetic corpus. Plan B's review is where a reviewer is likeliest to copy wording,
into an override's rationale, so the check is committed now, before any acquisition.
It is a check of committed records, not new behavior, so it passes as soon as it is
written: events v1's records, pilot v1, and `overrides.toml` quote no saved page. Its
third test shows it would catch a rationale that copies 40 characters, and not one
that copies 39.

**Files:**

- Create: `tests/integration/test_corpus_quotes.py`.

**Interfaces:**

- Consumes: `ArtifactText(body, media_type).canonical` in `cohort/locators.py`,
  which reads HTML as `walker-1` text; the synthetic corpus's `FIXTURE_DIR` in
  `events/fixture.py`.
- Produces: the test module's helpers, `records(directory) -> list[Path]`,
  `pages(store) -> list[str]`, and `quoted(paths, store) -> set[str]`, and
  `WIDTH = 40`. `records` already matches `acquisition-overrides.toml`, through
  `*overrides.toml`. Task 18 makes `pages` skip a page `walker-1` cannot read.

- [x] **Step 1: Write the check**

Create `tests/integration/test_corpus_quotes.py`:

```python
"""P6-3 over the committed corpus records (PR #6's review, F20; plan 8, P8-5): no
40-character window of any string in a corpus's event manifests, evidence records,
pilots, and overrides occurs in the text of a saved page.

- **Facts are allowed.** Each full date is masked, in the records and the pages
  alike, before the windows are cut. v1's ``overrides.toml`` says "for the quarter
  ended" and a date, as filings do, and that phrase is 40 characters. With dates
  masked, no 30-character window of v1 occurs in a saved page, so 40 leaves a
  margin, and still catches a phrase copied into a longer rationale, which a
  whole-string comparison misses.
- **The pages.** HTML is read as walker-1 text, and plain text as written. JSON
  responses, the submissions and companyfacts files, hold facts, not wording, and
  are not read.
- **Where it runs.** The real records are checked against Stage 5's saved store,
  which is local, so that test skips without it. A skip does not protect CI, so each
  freeze's gate runs this module with ``-rs`` and reads "passed". The synthetic
  corpus is checked against its committed pages, and a rationale that copies 40
  characters of one is caught.
"""

import json
import re
from pathlib import Path

import pytest
import tomllib
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.events.fixture import FIXTURE_DIR

REPO = Path(__file__).resolve().parents[2]
STORE = REPO / "data" / "raw" / "events" / "sec-edgar"
SYNTHETIC_STORE = REPO / FIXTURE_DIR / "raw" / "sec-edgar"
WIDTH = 40
RECORDS = ("events-v*.json", "pilot-v*.json", "*overrides.toml")
"""The event manifests with their evidence records, the pilots, and the overrides,
the event manifest's and acquisition's."""
MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?"
    r"|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
DATE = re.compile(rf"\b{MONTH}\.?\s+\d{{1,2}},?\s+\d{{4}}\b")


def records(corpus: Path) -> list[Path]:
    return sorted(path for pattern in RECORDS for path in corpus.glob(pattern))


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in strings(item)]
    return []


def load(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    return tomllib.loads(text) if path.suffix == ".toml" else json.loads(text)


def masked(text: str) -> str:
    """``text`` with each full date replaced by a NUL, which no page's text holds."""
    return DATE.sub("\0", text)


def pages(root: Path) -> list[str]:
    """The masked text of each HTML and plain-text page saved under ``root``."""
    found = []
    for path in sorted([*root.glob("*.html"), *root.glob("*.txt")]):
        body = path.read_bytes()
        if path.suffix == ".html":
            text = ArtifactText(body, "text/html").canonical[0]
        else:
            text = body.decode("utf-8", errors="replace")
        found.append(masked(text))
    return found


def quoted(paths: list[Path], root: Path) -> set[str]:
    """Each string in ``paths`` one of whose 40-character windows, dates masked,
    occurs in a page saved under ``root``."""
    windows: dict[str, str] = {}
    for path in paths:
        for string in strings(load(path)):
            text = masked(string)
            for start in range(len(text) - WIDTH + 1):
                windows.setdefault(text[start : start + WIDTH], string)
    found = set()
    for text in pages(root):
        for start in range(len(text) - WIDTH + 1):
            if (string := windows.get(text[start : start + WIDTH])) is not None:
                found.add(string)
    return found


def test_the_real_corpus_records_quote_no_saved_page() -> None:
    if not STORE.is_dir():
        pytest.skip(
            f"{STORE.relative_to(REPO)} is not saved here: each freeze's gate runs"
            " this test"
        )
    corpus = [
        path
        for directory in sorted((REPO / "config" / "corpus").iterdir())
        if directory.is_dir()
        for path in records(directory)
    ]
    assert corpus
    assert quoted(corpus, STORE) == set()


def test_the_synthetic_corpus_records_quote_no_saved_page() -> None:
    corpus = records(REPO / FIXTURE_DIR)
    assert [path.name for path in corpus] == [
        "events-v1.evidence.json",
        "events-v1.json",
        "overrides.toml",
        "pilot-v1.json",
    ]
    assert quoted(corpus, SYNTHETIC_STORE) == set()


@pytest.mark.parametrize(("width", "caught"), [(WIDTH, True), (WIDTH - 1, False)])
def test_a_rationale_that_copies_40_characters_is_caught(
    tmp_path, width: int, caught: bool
) -> None:
    """A rationale that copies 40 characters of a saved page, inside words of its
    own, is caught, and one that copies 39 is not: the window is 40."""
    text = next(text for text in pages(SYNTHETIC_STORE) if "announced" in text)
    start = text.index("announced")
    copied = f"Reviewed [{text[start : start + width]}] by hand."
    source = REPO / FIXTURE_DIR / "overrides.toml"
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    at = next(n for n, line in enumerate(lines) if line.startswith("rationale = "))
    lines[at] = f"rationale = {json.dumps(copied, ensure_ascii=False)}\n"
    overrides = tmp_path / "overrides.toml"
    overrides.write_text("".join(lines), encoding="utf-8")
    assert quoted([overrides], SYNTHETIC_STORE) == ({copied} if caught else set())
```

Extract it with `python3 /tmp/plan8-extract.py tests/integration/test_corpus_quotes.py`.

- [x] **Step 2: Run it**

Run: `uv run --locked --all-packages pytest tests/integration/test_corpus_quotes.py -q`

Expected: `4 passed`: the real corpus, which reads `data/raw/events/sec-edgar/`, the
synthetic corpus, and a rationale that copies 40 characters, caught, and one that
copies 39, not caught. If it reports `1 skipped`, the store is missing: stop and ask
(Preconditions).

- [x] **Step 3: Run the checks**

```bash
python3 /tmp/plan8-escapes.py tests/integration/test_corpus_quotes.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1408 passed, 24 deselected`; `All checks passed!` and
`255 files already formatted`.

- [x] **Step 4: Commit**

```bash
git log --oneline -3
git add tests/integration/test_corpus_quotes.py
git commit -m "test(events): the real corpus records quote no saved page (F20)"
```

---

### Task 11: The processing states and their table (R1.4)

S §Processing states, P8-6, and P8-7. Every later task records a document's state
through these records, so they come first, with the data dictionary's section and its
drift test.

- `events/states.py` holds R1.4's nine states (`DocumentState`), the missing reasons
  (`MissingReason`) and which state carries which (`REASONS`), and the transitions
  R1.4 allows (`NEXT`). `ExhibitAttempt` records one exhibit's attempt, and
  `StateTransition` one change of state, validated on construction.
- `check_histories` checks that each document's transitions chain, per pilot, and
  `current_states(transitions, pilot_hash)` gives each document's latest transition
  under that pilot.
- `events/state_table.py` holds the transitions as a Polars frame of a fixed schema,
  writes one run's as `<run_id>.parquet` through `write_new`, and reads a directory
  of runs back, checking each file's schema and the histories.
- `docs/data-dictionary.md` gains "earnings-ingestion processing-state records,
  schema version 1", with every field and value, and "Processing-state runs".

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/states.py` and
  `events/state_table.py`.
- Modify, by exact replacement: `docs/data-dictionary.md`.
- Test: create `packages/earnings-ingestion/tests/test_events_states.py` and
  `test_events_state_table.py`; modify, by exact replacement,
  `tests/contracts/test_data_dictionary.py`.

**Interfaces:**

- Consumes: `IngestionRecord` and `FailureReason` in `canonical/records.py`;
  `Accession` in `events/records.py`; `write_new` in `fetch/store.py`.
- Produces, in `events/states.py`:
  - `DocumentState`, `MissingReason`, `ExhibitChoice` (`named`, `described`,
    `lowest_sequence`, `override`), and `AttemptOutcome` (`confirmed`,
    `not_confirmed`, `canonicalization_failed`, `not_fetched`), each a `StrEnum`;
  - `REASONS`, `NEXT`, and `REOPENED`;
  - `ExhibitAttempt(accession, filename, exhibit_type, choice, outcome,
    artifact_sha256, failure_reason, detail)`;
  - `StateTransition(document_id, event_id, run_id, sequence, recorded_at,
    from_state, to_state, missing_reason, failure_reason, pilot_id, pilot_version,
    pilot_hash, frozen_accession, accession, exhibit, artifact_sha256,
    retrieved_at, doc_id, override_id, corpus_error, attempts)`;
  - `check_histories(transitions) -> None` and
    `current_states(transitions, pilot_hash) -> dict[str, StateTransition]`.
- Produces, in `events/state_table.py`: `STATES_DIR`, `SCHEMA`,
  `state_frame(transitions) -> pl.DataFrame`,
  `write_run(directory, transitions) -> Path`, and
  `read_runs(directory) -> list[StateTransition]`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_state_table.py`:

```python
"""The processing-state table (the Stage 5 spec, §Processing states, Storage): a
Polars frame, written as Parquet, one file per run, atomically, never replacing one."""

from datetime import UTC, datetime

import polars as pl
import pytest
from earnings_ingestion.events.state_table import (
    SCHEMA,
    read_runs,
    state_frame,
    write_run,
)
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitAttempt,
    ExhibitChoice,
    MissingReason,
    StateTransition,
)

AT = datetime(2026, 9, 29, 14, 0, tzinfo=UTC)
FROZEN = "0009990003-25-000005"
PILOT = "a" * 64


def transition(sequence: int, before, after, **fields) -> StateTransition:
    return StateTransition(
        document_id="cik-0009990003:2025-06-30:release",
        event_id="cik-0009990003:2025-06-30",
        run_id="acquire-20260929T140000Z",
        sequence=sequence,
        recorded_at=AT,
        from_state=before,
        to_state=after,
        pilot_id="djia-synthetic-pilot",
        pilot_version=1,
        pilot_hash=PILOT,
        frozen_accession=FROZEN,
        **fields,
    )


RUN = [
    transition(
        0,
        None,
        DocumentState.EXPECTED,
        missing_reason=MissingReason.NOT_YET_CHECKED,
    ),
    transition(
        1,
        DocumentState.EXPECTED,
        DocumentState.ACQUIRED,
        accession=FROZEN,
        exhibit="crvd-20250730-ex9901.htm",
        artifact_sha256="b" * 64,
        retrieved_at=AT,
    ),
    transition(
        2,
        DocumentState.ACQUIRED,
        DocumentState.UNAVAILABLE,
        missing_reason=MissingReason.NO_CONFIRMED_RELEASE,
        attempts=(
            ExhibitAttempt(
                accession=FROZEN,
                filename="crvd-20250730-ex9901.htm",
                exhibit_type="EX-99.01",
                choice=ExhibitChoice.NAMED,
                outcome=AttemptOutcome.NOT_CONFIRMED,
                artifact_sha256="b" * 64,
                detail="its opening announces no results",
            ),
            ExhibitAttempt(
                accession=FROZEN,
                filename="crvd-20250730-ex9902.htm",
                exhibit_type="EX-99.02",
                choice=ExhibitChoice.LOWEST_SEQUENCE,
                outcome=AttemptOutcome.NOT_FETCHED,
                detail="HTTP 404",
            ),
        ),
    ),
]


def test_a_run_round_trips_through_parquet(tmp_path) -> None:
    path = write_run(tmp_path / "states", RUN)
    assert path.name == "acquire-20260929T140000Z.parquet"
    frame = pl.read_parquet(path)
    assert frame.schema == SCHEMA
    assert frame.height == 3
    assert read_runs(tmp_path / "states") == RUN


def test_the_frame_keeps_its_schema_when_a_column_is_all_null() -> None:
    frame = state_frame(RUN[:1])
    assert frame.schema == SCHEMA
    assert frame["attempts"].to_list() == [[]]


def test_a_run_is_never_replaced(tmp_path) -> None:
    write_run(tmp_path, RUN)
    write_run(tmp_path, RUN)
    changed = [
        RUN[0].model_copy(update={"recorded_at": datetime(2026, 9, 30, tzinfo=UTC)})
    ]
    with pytest.raises(FileExistsError, match="holds other bytes"):
        write_run(tmp_path, changed)


def test_a_run_file_holds_one_run(tmp_path) -> None:
    other = RUN[0].model_copy(update={"run_id": "acquire-other"})
    with pytest.raises(ValueError, match="one run's transitions"):
        write_run(tmp_path, [RUN[1], other])
    with pytest.raises(ValueError, match="no transition"):
        write_run(tmp_path, [])


def test_reading_refuses_another_schema_or_a_broken_history(tmp_path) -> None:
    state_frame(RUN).drop("corpus_error").write_parquet(tmp_path / "odd.parquet")
    with pytest.raises(ValueError, match="odd.parquet does not have the state table"):
        read_runs(tmp_path)
    (tmp_path / "odd.parquet").unlink()
    write_run(tmp_path, RUN[1:])
    with pytest.raises(ValueError, match="starts at expected"):
        read_runs(tmp_path)


def test_no_directory_is_no_run(tmp_path) -> None:
    assert read_runs(tmp_path / "absent") == []
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/tests/test_events_state_table.py`.

Create `packages/earnings-ingestion/tests/test_events_states.py`:

```python
"""The processing states (the Stage 5 spec, §Processing states; R1.4): the records,
the transitions R1.4 allows, and each document's current state under a pilot."""

from datetime import UTC, datetime, timedelta

import pytest
from earnings_ingestion.canonical.records import FailureReason
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitAttempt,
    ExhibitChoice,
    MissingReason,
    StateTransition,
    check_histories,
    current_states,
)
from pydantic import ValidationError

PILOT = "a" * 64
OTHER_PILOT = "b" * 64
SHA = "c" * 64
AT = datetime(2026, 9, 29, 14, 0, tzinfo=UTC)
FROZEN = "0009990001-25-000012"
EXHIBIT = ExhibitAttempt(
    accession=FROZEN,
    filename="acme-20250925-ex992.htm",
    exhibit_type="EX-99.2",
    choice=ExhibitChoice.NAMED,
    outcome=AttemptOutcome.CONFIRMED,
    artifact_sha256=SHA,
)
DOC_ID = f"{FROZEN}_acme-20250925-ex992.htm@walker-1#0123456789abcdef"


def step(
    state: DocumentState,
    before: DocumentState | None,
    *,
    event: str = "cik-0009990001:2025-08-31",
    run: str = "run-1",
    sequence: int = 0,
    pilot: str = PILOT,
    **fields,
) -> StateTransition:
    details = {
        DocumentState.EXPECTED: {"missing_reason": MissingReason.NOT_YET_CHECKED},
        DocumentState.ACQUIRED: {
            "accession": FROZEN,
            "exhibit": EXHIBIT.filename,
            "artifact_sha256": SHA,
            "retrieved_at": AT,
        },
        DocumentState.PARSED: {
            "accession": FROZEN,
            "exhibit": EXHIBIT.filename,
            "artifact_sha256": SHA,
            "retrieved_at": AT,
            "doc_id": DOC_ID,
            "attempts": (EXHIBIT,),
        },
        DocumentState.FAILED: {
            "missing_reason": MissingReason.PARSE_FAILED,
            "failure_reason": FailureReason.NO_NATIVE_TEXT,
        },
        DocumentState.UNAVAILABLE: {"missing_reason": MissingReason.NOT_FOUND},
        DocumentState.RESTRICTED: {"missing_reason": MissingReason.RIGHTS_RESTRICTED},
    }.get(state, {})
    values = {
        "document_id": f"{event}:release",
        "event_id": event,
        "run_id": run,
        "sequence": sequence,
        "recorded_at": AT + timedelta(minutes=sequence),
        "from_state": before,
        "to_state": state,
        "pilot_id": "djia-synthetic-pilot",
        "pilot_version": 1,
        "pilot_hash": pilot,
        "frozen_accession": FROZEN,
        **details,
    }
    return StateTransition(**{**values, **fields})


E, A, P, F, U, R = (
    DocumentState.EXPECTED,
    DocumentState.ACQUIRED,
    DocumentState.PARSED,
    DocumentState.FAILED,
    DocumentState.UNAVAILABLE,
    DocumentState.RESTRICTED,
)


def test_every_state_is_represented_from_fixtures() -> None:
    """R1.4's nine states, each reached by a transition it allows, and every
    document that is expected but absent carries its missing_reason."""
    later = (
        DocumentState.PARTIAL,
        DocumentState.COMPLETED,
        DocumentState.COMPLETED_NO_THEME,
    )
    histories = [
        [step(E, None)],
        [step(E, None), step(U, E, sequence=1)],
        [step(E, None), step(R, E, sequence=1)],
        [step(E, None), step(A, E, sequence=1)],
        [step(E, None), step(A, E, sequence=1), step(F, A, sequence=2)],
        [
            step(E, None),
            step(A, E, sequence=1),
            step(U, A, sequence=2, missing_reason=MissingReason.NO_CONFIRMED_RELEASE),
        ],
        [step(E, None), step(A, E, sequence=1), step(P, A, sequence=2)],
        *(
            [
                step(E, None),
                step(A, E, sequence=1),
                step(P, A, sequence=2),
                step(state, P, run="run-2", recorded_at=AT + timedelta(hours=1)),
            ]
            for state in later
        ),
    ]
    transitions = [
        transition.model_copy(
            update={
                "event_id": event,
                "document_id": f"{event}:release",
                "run_id": f"{transition.run_id}-{number}",
            }
        )
        for number, history in enumerate(histories)
        for event in [f"cik-0009990001:2025-{number + 1:02d}-01"]
        for transition in history
    ]
    check_histories(transitions)
    current = current_states(transitions, PILOT)
    assert {t.to_state for t in current.values()} == set(DocumentState)
    for transition in current.values():
        absent = transition.to_state in {E, F, U, R}
        assert (transition.missing_reason is not None) is absent


@pytest.mark.parametrize(
    ("state", "fields", "message"),
    [
        (E, {"missing_reason": None}, "expected carries a missing_reason"),
        (U, {"missing_reason": MissingReason.PARSE_FAILED}, "unavailable carries"),
        (
            A,
            {"missing_reason": MissingReason.NOT_FOUND},
            "acquired carries no missing_reason",
        ),
        (F, {"failure_reason": None}, "failed names its FailureReason"),
        (U, {"failure_reason": FailureReason.PARSE_FAILED}, "only failed names"),
        (A, {"artifact_sha256": None}, "acquired names its accession"),
        (P, {"doc_id": None}, "parsed names its accession"),
    ],
)
def test_a_state_carries_its_own_details(state, fields, message) -> None:
    before = {E: None, U: E, A: E, F: A, P: A}[state]
    with pytest.raises(ValidationError, match=message):
        step(state, before, **fields)


def test_only_the_transitions_r1_4_allows() -> None:
    with pytest.raises(ValidationError, match="expected cannot become parsed"):
        step(P, E)
    with pytest.raises(ValidationError, match="the start cannot become acquired"):
        step(A, None)
    with pytest.raises(ValidationError, match="completed cannot become"):
        step(DocumentState.PARTIAL, DocumentState.COMPLETED)
    with pytest.raises(ValidationError, match="only under an acquisition override"):
        step(A, U)
    assert step(A, U, override_id="release-doc-acme").from_state is U
    assert step(A, F, override_id="release-doc-acme").from_state is F


def test_a_history_must_chain() -> None:
    with pytest.raises(ValueError, match="starts at expected, not from acquired"):
        check_histories([step(P, A)])
    with pytest.raises(ValueError, match="comes from acquired, but its state was"):
        check_histories([step(E, None), step(P, A, sequence=1)])
    with pytest.raises(ValueError, match="run-1 #0 is recorded twice"):
        check_histories([step(E, None), step(E, None)])


def test_the_current_state_is_the_latest_under_the_current_pilot() -> None:
    """A revert to an earlier pilot never inherits a later pilot's history (plan 8,
    P8-4): each pilot's transitions chain on their own."""
    mine = [step(E, None), step(A, E, sequence=1), step(P, A, sequence=2)]
    other = [
        step(E, None, run="run-2", pilot=OTHER_PILOT),
        step(U, E, run="run-2", sequence=1, pilot=OTHER_PILOT),
    ]
    check_histories([*mine, *other])
    (current,) = current_states([*other, *mine], PILOT).values()
    assert current.to_state is P
    (theirs,) = current_states([*mine, *other], OTHER_PILOT).values()
    assert theirs.to_state is U
    assert current_states(mine, OTHER_PILOT) == {}


def test_later_runs_follow_earlier_ones_by_time_then_run_then_sequence() -> None:
    first = [step(E, None), step(A, E, sequence=1)]
    rerun = [
        step(P, A, run="run-2", sequence=0).model_copy(
            update={"recorded_at": AT + timedelta(minutes=1)}
        )
    ]
    check_histories([*rerun, *first])
    (current,) = current_states([*rerun, *first], PILOT).values()
    assert (current.run_id, current.to_state) == ("run-2", P)
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/tests/test_events_states.py`.

Create `/tmp/plan8-task11-tests.py`:

```python
"""Plan 8: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "tests/contracts/test_data_dictionary.py": [
        (
            "retrieval metadata, the cohort's records and curated files, and Stage 5's event\n"
            "and pilot records.\n",
            "retrieval metadata, the cohort's records and curated files, and Stage 5's event,\n"
            "pilot, and processing-state records.\n",
        ),
        (
            "from earnings_ingestion.events import acceptance\n",
            "from earnings_ingestion.events import acceptance, states\n",
        ),
        (
            "]\n"
            "ENUMS = [\n",
            "    states.ExhibitAttempt,\n"
            "    states.StateTransition,\n"
            "]\n"
            "ENUMS = [\n",
        ),
        (
            "]\n"
            "\n",
            "    states.DocumentState,\n"
            "    states.MissingReason,\n"
            "    states.ExhibitChoice,\n"
            "    states.AttemptOutcome,\n"
            "]\n"
            "\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task11-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_state_table.py packages/earnings-ingestion/tests/test_events_states.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL: `3 errors`, in collection: `No module named
'earnings_ingestion.events.state_table'`, `No module named
'earnings_ingestion.events.states'`, and, in the dictionary's drift test,
`cannot import name 'states' from 'earnings_ingestion.events'`.

- [x] **Step 3: Write the states, the table, and their dictionary section**

> Deviation: after the final review (`55ea811`), with the user's choice, runs are ordered by their earliest `recorded_at`, then `run_id`, and each run's transitions by `sequence` (`in_order`), amending P8-6's order so that a clock that steps back during a run cannot break a chain. A `StateTransition`'s `document_id` must be `<event_id>:release`; `read_runs` refuses a file Polars cannot read, by name, as a `ValueError`; and the dictionary gives `ExhibitAttempt.detail`'s `walker-1` failure detail.

Create `packages/earnings-ingestion/src/earnings_ingestion/events/state_table.py`:

```python
"""The processing-state table (the Stage 5 spec, §Processing states, Storage; plan 8,
P8-7).

- **The frame.** ``state_frame`` holds ``StateTransition`` rows as a Polars frame of
  the fixed ``SCHEMA``, so a column that is null in every row keeps its type, and an
  exhibit's attempts are a list of structs.
- **One file per run.** ``write_run`` writes one run's transitions as Parquet to
  ``<run_id>.parquet``, atomically, and never replaces a file that holds other bytes.
  The runs live under the gitignored ``data/runs/events/states/``.
- **Reading.** ``read_runs`` reads every run in a directory, refuses a file of another
  schema, and checks that each document's transitions chain under each pilot.
"""

import io
from collections.abc import Sequence
from pathlib import Path

import polars as pl

from earnings_ingestion.events.states import StateTransition, check_histories
from earnings_ingestion.fetch.store import write_new

STATES_DIR = Path("data") / "runs" / "events" / "states"

ATTEMPT = pl.Struct(
    {
        "accession": pl.String,
        "filename": pl.String,
        "exhibit_type": pl.String,
        "choice": pl.String,
        "outcome": pl.String,
        "artifact_sha256": pl.String,
        "failure_reason": pl.String,
        "detail": pl.String,
    }
)
SCHEMA = pl.Schema(
    {
        "schema_version": pl.Int64,
        "document_id": pl.String,
        "event_id": pl.String,
        "run_id": pl.String,
        "sequence": pl.Int64,
        "recorded_at": pl.Datetime("us", "UTC"),
        "from_state": pl.String,
        "to_state": pl.String,
        "missing_reason": pl.String,
        "failure_reason": pl.String,
        "pilot_id": pl.String,
        "pilot_version": pl.Int64,
        "pilot_hash": pl.String,
        "frozen_accession": pl.String,
        "accession": pl.String,
        "exhibit": pl.String,
        "artifact_sha256": pl.String,
        "retrieved_at": pl.Datetime("us", "UTC"),
        "doc_id": pl.String,
        "override_id": pl.String,
        "corpus_error": pl.String,
        "attempts": pl.List(ATTEMPT),
    }
)


def state_frame(transitions: Sequence[StateTransition]) -> pl.DataFrame:
    """``transitions`` as a frame of ``SCHEMA``."""
    rows = [transition.model_dump(mode="python") for transition in transitions]
    return pl.DataFrame(rows, schema=SCHEMA, orient="row")


def write_run(directory: Path, transitions: Sequence[StateTransition]) -> Path:
    """Write one run's transitions to ``<run_id>.parquet`` in ``directory``."""
    runs = {transition.run_id for transition in transitions}
    if not runs:
        raise ValueError("no transition to write")
    if len(runs) > 1:
        raise ValueError(f"a run file holds one run's transitions, not {sorted(runs)}")
    buffer = io.BytesIO()
    state_frame(transitions).write_parquet(buffer)
    path = directory / f"{runs.pop()}.parquet"
    write_new(path, buffer.getvalue())
    return path


def read_runs(directory: Path) -> list[StateTransition]:
    """Every transition of every run in ``directory``, refused unless each file has
    ``SCHEMA`` and each document's transitions chain."""
    transitions = []
    for path in sorted(directory.glob("*.parquet")):
        frame = pl.read_parquet(path)
        if frame.schema != SCHEMA:
            raise ValueError(f"{path.name} does not have the state table's schema")
        transitions += [
            StateTransition.model_validate(row, strict=False)
            for row in frame.iter_rows(named=True)
        ]
    check_histories(transitions)
    return transitions
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/state_table.py`.

Create `packages/earnings-ingestion/src/earnings_ingestion/events/states.py`:

```python
"""The processing states of Stage 5's expected documents (the Stage 5 spec,
§Processing states; R1.4; plan 8, P8-6 and P8-7).

- **Documents.** Each pilot event expects one document, its release:
  ``<event_id>:release``.
- **Transitions.** Every change of state is a ``StateTransition``, kept with its run,
  time, reason, and details. ``NEXT`` holds the transitions R1.4 allows, and an
  ``unavailable`` or ``failed`` document goes back to ``acquired`` only under an
  acquisition override (``set_release_document``). ``parsed`` goes on to
  ``partial``, ``completed``, or ``completed-no-theme`` only when a later stage sets
  it; fixtures represent those now. ``restricted`` comes from fixtures only: no
  source this stage reads forbids local processing, since SEC documents are public.
- **Missing reasons.** A state in which the document is not at hand carries a
  ``missing_reason``: ``expected``, ``unavailable``, ``restricted``, and ``failed``.
  Every other state carries none, so a document that is expected but absent always
  says why (R1.4; A §376).
- **Order.** A document's transitions are ordered by ``recorded_at``, then
  ``run_id``, then ``sequence``, the position in its run, and must chain: the first
  starts at ``expected``, and each comes from the state the one before it reached.
- **The current state.** A document's current state is its latest transition among
  those recorded under the current pilot's content hash, and each pilot's
  transitions chain on their own. So a revert to an earlier pilot never inherits a
  later pilot's history (plan 8, P8-4).

These join ingestion schema version 1 (P6-5), and ``docs/data-dictionary.md``
documents every field and value.
"""

from collections.abc import Iterable
from enum import StrEnum
from typing import Self

from earnings_core.artifacts import NonBlankStr
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)

from earnings_ingestion.canonical.records import FailureReason, IngestionRecord
from earnings_ingestion.events.records import Accession


class DocumentState(StrEnum):
    """R1.4's processing states."""

    EXPECTED = "expected"
    ACQUIRED = "acquired"
    PARSED = "parsed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    RESTRICTED = "restricted"
    PARTIAL = "partial"
    COMPLETED = "completed"
    COMPLETED_NO_THEME = "completed-no-theme"


class MissingReason(StrEnum):
    """Why a document is not at hand, in AGENTS.md's words where it has them."""

    NOT_YET_CHECKED = "not_yet_checked"
    NOT_FOUND = "not_found"
    NO_CONFIRMED_RELEASE = "no_confirmed_release"
    RIGHTS_RESTRICTED = "rights_restricted"
    PARSE_FAILED = "parse_failed"


REASONS = {
    DocumentState.EXPECTED: frozenset({MissingReason.NOT_YET_CHECKED}),
    DocumentState.UNAVAILABLE: frozenset(
        {MissingReason.NOT_FOUND, MissingReason.NO_CONFIRMED_RELEASE}
    ),
    DocumentState.RESTRICTED: frozenset({MissingReason.RIGHTS_RESTRICTED}),
    DocumentState.FAILED: frozenset({MissingReason.PARSE_FAILED}),
}
"""The missing reasons each state may carry; a state not listed carries none."""

NEXT: dict[DocumentState | None, frozenset[DocumentState]] = {
    None: frozenset({DocumentState.EXPECTED}),
    DocumentState.EXPECTED: frozenset(
        {DocumentState.ACQUIRED, DocumentState.UNAVAILABLE, DocumentState.RESTRICTED}
    ),
    DocumentState.ACQUIRED: frozenset(
        {DocumentState.PARSED, DocumentState.FAILED, DocumentState.UNAVAILABLE}
    ),
    DocumentState.PARSED: frozenset(
        {
            DocumentState.PARTIAL,
            DocumentState.COMPLETED,
            DocumentState.COMPLETED_NO_THEME,
        }
    ),
    DocumentState.FAILED: frozenset({DocumentState.ACQUIRED}),
    DocumentState.UNAVAILABLE: frozenset({DocumentState.ACQUIRED}),
    DocumentState.RESTRICTED: frozenset(),
    DocumentState.PARTIAL: frozenset(),
    DocumentState.COMPLETED: frozenset(),
    DocumentState.COMPLETED_NO_THEME: frozenset(),
}
"""The transitions R1.4 allows, from each state; ``None`` is the start."""

REOPENED = frozenset({DocumentState.FAILED, DocumentState.UNAVAILABLE})
"""States that go back to ``acquired`` only under an acquisition override."""


class ExhibitChoice(StrEnum):
    """Why an exhibit was tried, in the order R1.2 tries them."""

    NAMED = "named"
    DESCRIBED = "described"
    LOWEST_SEQUENCE = "lowest_sequence"
    OVERRIDE = "override"


class AttemptOutcome(StrEnum):
    """What one exhibit's attempt came to."""

    CONFIRMED = "confirmed"
    NOT_CONFIRMED = "not_confirmed"
    CANONICALIZATION_FAILED = "canonicalization_failed"
    NOT_FETCHED = "not_fetched"


class ExhibitAttempt(BaseModel):
    """One exhibit tried for a document: immutable, closed, strictly typed."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    accession: Accession
    filename: NonBlankStr
    exhibit_type: NonBlankStr
    choice: ExhibitChoice
    outcome: AttemptOutcome
    artifact_sha256: Sha256Hex | None = None
    failure_reason: FailureReason | None = None
    detail: NonBlankStr | None = None

    @model_validator(mode="after")
    def _outcome(self) -> Self:
        fetched = self.outcome is not AttemptOutcome.NOT_FETCHED
        if (self.artifact_sha256 is not None) is not fetched:
            raise ValueError("an attempt names its artifact exactly when it fetched it")
        failed = self.outcome is AttemptOutcome.CANONICALIZATION_FAILED
        if (self.failure_reason is not None) is not failed:
            raise ValueError(
                "an attempt names a FailureReason exactly when canonicalization failed"
            )
        return self


class StateTransition(IngestionRecord):
    """One document's change of state, in one run."""

    document_id: IdPart
    event_id: IdPart
    run_id: IdPart
    sequence: NonNegativeInt
    """Its position in its run."""
    recorded_at: AwareDatetime
    from_state: DocumentState | None
    to_state: DocumentState
    missing_reason: MissingReason | None = None
    failure_reason: FailureReason | None = None
    pilot_id: IdPart
    pilot_version: PositiveInt
    pilot_hash: Sha256Hex
    frozen_accession: Accession
    """The event manifest's release filing for the event."""
    accession: Accession | None = None
    """The filing whose exhibit was acquired: the frozen one, or an override's."""
    exhibit: NonBlankStr | None = None
    """The acquired exhibit's file name."""
    artifact_sha256: Sha256Hex | None = None
    retrieved_at: AwareDatetime | None = None
    doc_id: NonBlankStr | None = None
    override_id: IdPart | None = None
    corpus_error: NonBlankStr | None = None
    """Set when an override's filing would change the event's eligibility."""
    attempts: tuple[ExhibitAttempt, ...] = ()

    @model_validator(mode="after")
    def _state(self) -> Self:
        before = "the start" if self.from_state is None else self.from_state.value
        if self.to_state not in NEXT[self.from_state]:
            raise ValueError(f"{before} cannot become {self.to_state}")
        if (
            self.from_state in REOPENED
            and self.to_state is DocumentState.ACQUIRED
            and self.override_id is None
        ):
            raise ValueError(
                f"{before} becomes acquired only under an acquisition override"
            )
        allowed = REASONS.get(self.to_state, frozenset())
        if allowed and self.missing_reason not in allowed:
            raise ValueError(
                f"{self.to_state} carries a missing_reason of {sorted(allowed)}"
            )
        if not allowed and self.missing_reason is not None:
            raise ValueError(f"{self.to_state} carries no missing_reason")
        failed = self.to_state is DocumentState.FAILED
        if failed and self.failure_reason is None:
            raise ValueError("failed names its FailureReason")
        if not failed and self.failure_reason is not None:
            raise ValueError("only failed names a FailureReason")
        acquired = (self.accession, self.exhibit, self.artifact_sha256)
        if self.to_state in (DocumentState.ACQUIRED, DocumentState.PARSED) and (
            None in (*acquired, self.retrieved_at)
        ):
            raise ValueError(
                f"{self.to_state} names its accession, exhibit, artifact, and"
                " retrieval time"
            )
        if self.to_state is DocumentState.PARSED and self.doc_id is None:
            raise ValueError("parsed names its accession, exhibit, and doc_id")
        return self


def _order(transition: StateTransition) -> tuple:
    return (transition.recorded_at, transition.run_id, transition.sequence)


def check_histories(transitions: Iterable[StateTransition]) -> None:
    """Refuse a run position recorded twice, or a document's transitions, under one
    pilot, that do not chain from ``expected``."""
    seen: set[tuple[str, int]] = set()
    histories: dict[tuple[str, str], list[StateTransition]] = {}
    for transition in transitions:
        position = (transition.run_id, transition.sequence)
        if position in seen:
            raise ValueError(
                f"{transition.run_id} #{transition.sequence} is recorded twice"
            )
        seen.add(position)
        key = (transition.pilot_hash, transition.document_id)
        histories.setdefault(key, []).append(transition)
    for (_, document), history in histories.items():
        state: DocumentState | None = None
        for transition in sorted(history, key=_order):
            if transition.from_state != state:
                if state is None:
                    raise ValueError(
                        f"{document} starts at expected, not from"
                        f" {transition.from_state}"
                    )
                raise ValueError(
                    f"{document}: {transition.run_id} #{transition.sequence} comes"
                    f" from {transition.from_state}, but its state was {state}"
                )
            state = transition.to_state


def current_states(
    transitions: Iterable[StateTransition], pilot_hash: str
) -> dict[str, StateTransition]:
    """Each document's latest transition recorded under the pilot of ``pilot_hash``,
    by ``document_id``."""
    current: dict[str, StateTransition] = {}
    for transition in sorted(transitions, key=_order):
        if transition.pilot_hash == pilot_hash:
            current[transition.document_id] = transition
    return current
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/states.py`.

Create `/tmp/plan8-task11-source.py`:

```python
"""Plan 8: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/data-dictionary.md": [
        (
            "  frozen over the current event manifest, loaded by `load_pilot` (F4).\n",
            "  frozen over the current event manifest, loaded by `load_pilot` (F4).\n"
            "\n"
            "## earnings-ingestion processing-state records, schema version 1\n"
            "\n"
            "- **Package.** The records, and the transitions R1.4 allows, are in\n"
            "  `earnings_ingestion.events.states`; the table's Parquet schema is in\n"
            "  `earnings_ingestion.events.state_table` (Stage 5, plan 8).\n"
            "- **Schema version.** These records join ingestion schema version `1`.\n"
            "  `StateTransition` carries it as `schema_version`; `ExhibitAttempt` does not.\n"
            "- **Documents.** Each pilot event expects one document, its release, whose\n"
            "  `document_id` is `<event_id>:release`.\n"
            "\n"
            "### `DocumentState`\n"
            "\n"
            "R1.4's processing states. A §644's `available` is `acquired`, and its `processed` is\n"
            "`completed` or `completed-no-theme`.\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `expected` | A pilot event's release, before it is attempted |\n"
            "| `acquired` | A candidate exhibit's bytes are saved |\n"
            "| `parsed` | A candidate canonicalized, and `release-content/1` confirmed it or an acquisition override named it |\n"
            "| `failed` | No candidate was confirmed, and one failed to canonicalize |\n"
            "| `unavailable` | No candidate could be fetched, or every one fetched canonicalized and none was confirmed |\n"
            "| `restricted` | The source's rights forbid local processing; fixtures only, since SEC documents are public |\n"
            "| `partial` | Set by a later stage; fixtures only in Stage 5 |\n"
            "| `completed` | Set by a later stage; fixtures only in Stage 5 |\n"
            "| `completed-no-theme` | Set by a later stage, which found no theme; fixtures only in Stage 5 |\n"
            "\n"
            "### `MissingReason`\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `not_yet_checked` | `expected`: not attempted yet |\n"
            "| `not_found` | `unavailable`: no candidate exhibit could be fetched |\n"
            "| `no_confirmed_release` | `unavailable`: every candidate fetched canonicalized, and none was confirmed |\n"
            "| `rights_restricted` | `restricted`: the source's rights forbid local processing |\n"
            "| `parse_failed` | `failed`: `failure_reason` gives Stage 3's reason |\n"
            "\n"
            "### `ExhibitChoice`\n"
            "\n"
            "Why an exhibit was tried, in R1.2's order.\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `named` | The Item 2.02 text names its number, such as \"Exhibit 99.1\" |\n"
            "| `described` | Its description on the index page names a release |\n"
            "| `lowest_sequence` | Neither: the rest, lowest sequence first |\n"
            "| `override` | A `set_release_document` override names it |\n"
            "\n"
            "### `AttemptOutcome`\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `confirmed` | It canonicalized, and `release-content/1` confirmed it |\n"
            "| `not_confirmed` | It canonicalized, and `release-content/1` did not confirm it |\n"
            "| `canonicalization_failed` | `walker-1` refused it, with a `FailureReason` |\n"
            "| `not_fetched` | The client refused its response: a status other than 200, an unexpected media type, or a redirect |\n"
            "\n"
            "### `ExhibitAttempt`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `accession` | accession | The filing that lists the exhibit |\n"
            "| `filename` | string | The exhibit's file name on the index page |\n"
            "| `exhibit_type` | string | Its type on the index page, such as `EX-99.1` |\n"
            "| `choice` | `ExhibitChoice` | Why it was tried |\n"
            "| `outcome` | `AttemptOutcome` | What the attempt came to |\n"
            "| `artifact_sha256` | 64 lowercase hex or null | The saved bytes' SHA-256; exactly when it was fetched |\n"
            "| `failure_reason` | `FailureReason` or null | Exactly when canonicalization failed |\n"
            "| `detail` | string or null | What confirmation lacked, or the client's refusal |\n"
            "\n"
            "### `StateTransition`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `schema_version` | `1` | Ingestion record schema version |\n"
            "| `document_id` | ID part | `<event_id>:release` |\n"
            "| `event_id` | ID part | The pilot event |\n"
            "| `run_id` | ID part | The run that recorded it, and its file's name |\n"
            "| `sequence` | int ≥ 0 | Its position in its run |\n"
            "| `recorded_at` | UTC datetime | When it was recorded |\n"
            "| `from_state` | `DocumentState` or null | The state before; null at the start |\n"
            "| `to_state` | `DocumentState` | The state after; `NEXT` allows it from `from_state` |\n"
            "| `missing_reason` | `MissingReason` or null | Exactly for `expected`, `unavailable`, `restricted`, and `failed` |\n"
            "| `failure_reason` | `FailureReason` or null | Exactly for `failed` |\n"
            "| `pilot_id` | ID part | The pilot the run read |\n"
            "| `pilot_version` | int ≥ 1 | Its version |\n"
            "| `pilot_hash` | 64 lowercase hex | Its `content_hash`, which scopes the current state |\n"
            "| `frozen_accession` | accession | The event manifest's `release_accession` for the event |\n"
            "| `accession` | accession or null | The filing whose exhibit was acquired: the frozen one, or an override's |\n"
            "| `exhibit` | string or null | The acquired exhibit's file name |\n"
            "| `artifact_sha256` | 64 lowercase hex or null | Its saved bytes' SHA-256 |\n"
            "| `retrieved_at` | UTC datetime or null | When those bytes were retrieved |\n"
            "| `doc_id` | string or null | Its `walker-1` canonical document, for `parsed` |\n"
            "| `override_id` | ID part or null | The acquisition override applied; needed to leave `failed` or `unavailable` |\n"
            "| `corpus_error` | string or null | Set when the override's filing would change the event's eligibility, for the next corpus version |\n"
            "| `attempts` | tuple of `ExhibitAttempt` | Every exhibit tried, in order, on the transition that concludes them |\n"
            "\n"
            "## Processing-state runs\n"
            "\n"
            "- **Where.** `data/runs/events/states/<run_id>.parquet` holds one run's transitions\n"
            "  as a Polars frame of `state_table.SCHEMA`. It is written once, atomically, and\n"
            "  never replaced or committed.\n"
            "- **Order.** A document's transitions are ordered by `recorded_at`, `run_id`, and\n"
            "  `sequence`, and must chain from `expected`.\n"
            "- **The current state.** A document's current state is its latest transition among\n"
            "  those recorded under the current pilot's `pilot_hash`, so a revert to an earlier\n"
            "  pilot never inherits a later pilot's history.\n"
            "- **Canonical documents.** `data/runs/events/canonical/<doc_id>.json` holds each\n"
            "  parsed release's `walker-1` document in the canonical fixture format.\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task11-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_state_table.py packages/earnings-ingestion/tests/test_events_states.py tests/contracts/test_data_dictionary.py -q`

Expected: `124 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/state_table.py packages/earnings-ingestion/src/earnings_ingestion/events/states.py packages/earnings-ingestion/tests/test_events_state_table.py packages/earnings-ingestion/tests/test_events_states.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1432 passed, 24 deselected`; `All checks passed!` and
`259 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-ingestion/src/earnings_ingestion/events/state_table.py packages/earnings-ingestion/src/earnings_ingestion/events/states.py packages/earnings-ingestion/tests/test_events_state_table.py packages/earnings-ingestion/tests/test_events_states.py tests/contracts/test_data_dictionary.py
git commit -m "feat(events): the processing states and their Parquet table (R1.4)"
```

---

### Task 12: R1.2's exhibit choice

S §Exhibit choice, and P8-8. `exhibit_order(index, item_text)` lists a release
filing's `EX-99*` exhibits in the order acquisition tries them: those the Item 2.02
text names, then those whose description names a release, then the rest, each group
by sequence. `named_numbers(text)` reads the numbers a text names, as 99 with an
integer sub-number, so "99.01" names `EX-99.1` and "Exhibit 99" names `EX-99` alone.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/exhibits.py`.
- Test: create `packages/earnings-ingestion/tests/test_events_exhibits.py`.

**Interfaces:**

- Consumes: `FilingIndex`, `IndexDocument` (`sequence`, `description`, `filename`,
  `doc_type`), and `FilingIndex.exhibits_99()` in `sec/filing_index.py`;
  `ExhibitChoice` from Task 11.
- Produces: `Number = tuple[int, int | None]`; `named_numbers(text: str) ->
  set[Number]`; `ExhibitCandidate(document: IndexDocument, choice: ExhibitChoice)`;
  and `exhibit_order(index: FilingIndex, item_text: str) ->
  tuple[ExhibitCandidate, ...]`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_exhibits.py`:

```python
"""R1.2's exhibit choice (the Stage 5 spec, §Exhibit choice): the exhibit the Item
2.02 text names, then one whose description names a release, then the lowest
sequence, each group by sequence."""

from datetime import date

import pytest
from earnings_ingestion.events.exhibits import exhibit_order, named_numbers
from earnings_ingestion.events.states import ExhibitChoice
from earnings_ingestion.sec.filing_index import FilingIndex, IndexDocument


def index(*documents: tuple[int, str, str, str]) -> FilingIndex:
    return FilingIndex(
        accession="0009990001-25-000012",
        form="8-K",
        filing_date=date(2025, 9, 25),
        accepted="2025-09-25 16:05:00",
        period_of_report=date(2025, 9, 25),
        items=("2.02", "9.01"),
        documents=(
            IndexDocument(1, "8-K", "acme-8k-20250925.htm", "8-K"),
            *(IndexDocument(*document) for document in documents),
            IndexDocument(None, "Complete submission text file", "x.txt", " "),
        ),
    )


@pytest.mark.parametrize(
    ("text", "numbers"),
    [
        ("furnished as Exhibit 99.1.", {(99, 1)}),
        ("in Exhibit 99 to this report", {(99, None)}),
        ("as Exhibit 99.01 hereto", {(99, 1)}),
        ("as Exhibits 99.1 and 99.2.", {(99, 1), (99, 2)}),
        ("Exhibits 99.1, 99.2, and 99.3", {(99, 1), (99, 2), (99, 3)}),
        ("exhibit no. 99.2 and Exhibit 99.3", {(99, 2), (99, 3)}),
        ("a copy is attached as Exhibit 99.1 & 99.2", {(99, 1), (99, 2)}),
        ("furnished its quarterly earnings release.", set()),
        ("Exhibit 10.1 is the credit agreement", set()),
    ],
)
def test_the_numbers_a_text_names(text: str, numbers: set) -> None:
    assert named_numbers(text) == numbers


def order(filing: FilingIndex, text: str) -> list[tuple[str, ExhibitChoice]]:
    return [(c.document.filename, c.choice) for c in exhibit_order(filing, text)]


def test_named_exhibits_come_first_by_sequence() -> None:
    filing = index(
        (2, "Press release", "ex991.htm", "EX-99.1"),
        (3, "Supplemental information", "ex992.htm", "EX-99.2"),
        (4, "Investor presentation", "ex993.htm", "EX-99.3"),
    )
    assert order(filing, "furnished as Exhibits 99.2 and 99.3") == [
        ("ex992.htm", ExhibitChoice.NAMED),
        ("ex993.htm", ExhibitChoice.NAMED),
        ("ex991.htm", ExhibitChoice.DESCRIBED),
    ]


@pytest.mark.parametrize(
    ("kind", "said"),
    [
        ("EX-99", "Exhibit 99"),
        ("EX-99.1", "Exhibit 99.1"),
        ("EX-99.01", "Exhibit 99.1"),
    ],
)
def test_each_numbering_is_named(kind: str, said: str) -> None:
    filing = index((2, "Financial tables", "ex.htm", kind))
    assert order(filing, f"furnished as {said}.") == [("ex.htm", ExhibitChoice.NAMED)]


def test_a_description_that_names_a_release_comes_next() -> None:
    filing = index(
        (2, "Supplemental schedules", "ex991.htm", "EX-99.1"),
        (3, "PRESS RELEASE DATED OCTOBER 21, 2025", "ex992.htm", "EX-99.2"),
        (4, "Earnings release, financial tables", "ex993.htm", "EX-99.3"),
    )
    assert order(filing, "furnished its release") == [
        ("ex992.htm", ExhibitChoice.DESCRIBED),
        ("ex993.htm", ExhibitChoice.DESCRIBED),
        ("ex991.htm", ExhibitChoice.LOWEST_SEQUENCE),
    ]


def test_otherwise_the_lowest_sequence_first() -> None:
    filing = index(
        (3, "Exhibit", "b.htm", "EX-99.2"),
        (2, "Exhibit", "a.htm", "EX-99.1"),
        (4, "Charter", "c.htm", "EX-3.1"),
    )
    assert order(filing, "") == [
        ("a.htm", ExhibitChoice.LOWEST_SEQUENCE),
        ("b.htm", ExhibitChoice.LOWEST_SEQUENCE),
    ]


def test_released_is_not_a_release() -> None:
    filing = index((2, "Released guidance", "a.htm", "EX-99.1"))
    assert order(filing, "") == [("a.htm", ExhibitChoice.LOWEST_SEQUENCE)]


def test_a_filing_without_ex_99_has_no_candidate() -> None:
    assert exhibit_order(index((2, "Charter", "c.htm", "EX-3.1")), "Exhibit 99.1") == ()
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/tests/test_events_exhibits.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_exhibits.py -q`

Expected: FAIL: `1 error`, with
`ModuleNotFoundError: No module named 'earnings_ingestion.events.exhibits'`.

- [x] **Step 3: Order the exhibits**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/exhibits.py`:

```python
"""R1.2's exhibit choice (the Stage 5 spec, §Exhibit choice; plan 8, P8-8).

The candidates are the release filing's exhibits typed ``EX-99*`` on its saved index
page, tried in this order, each group by sequence number:

1. ``named``: each whose number the Item 2.02 text names, in "Exhibit 99.1",
   "Exhibit No. 99.1", or a list such as "Exhibits 99.1 and 99.2". A number is 99
   and a sub-number read as an integer, so "99.01" names ``EX-99.1``, and
   "Exhibit 99" names ``EX-99`` alone.
2. ``described``: each whose description on the index page has the word
   "release", such as "Press release" or "Earnings release".
3. ``lowest_sequence``: the rest.

Only the Item 2.02 sections are read, never Item 9.01's list, which names every
exhibit.
"""

import re
from dataclasses import dataclass

from earnings_ingestion.events.states import ExhibitChoice
from earnings_ingestion.sec.filing_index import FilingIndex, IndexDocument

_NUMBER = r"99(?:\.\d+)?(?!\d)"
_SEPARATOR = r"(?:\s*,\s*(?:and\s+)?|\s+and\s+|\s*&\s*)"
_NAMED = re.compile(
    rf"\bexhibits?\s+(?:no\.?\s*)?(?P<list>{_NUMBER}(?:{_SEPARATOR}{_NUMBER})*)",
    re.IGNORECASE,
)
_TYPE = re.compile(rf"^EX-(?P<number>{_NUMBER})$", re.IGNORECASE)
_RELEASE = re.compile(r"\brelease\b", re.IGNORECASE)

Number = tuple[int, int | None]


def _number(written: str) -> Number:
    main, _, sub = written.partition(".")
    return int(main), int(sub) if sub else None


def named_numbers(text: str) -> set[Number]:
    """The exhibit numbers ``text`` names."""
    return {
        _number(written)
        for match in _NAMED.finditer(text)
        for written in re.findall(_NUMBER, match["list"])
    }


@dataclass(frozen=True)
class ExhibitCandidate:
    document: IndexDocument
    choice: ExhibitChoice


def _type_number(document: IndexDocument) -> Number | None:
    match = _TYPE.match(document.doc_type.strip())
    return None if match is None else _number(match["number"])


def exhibit_order(index: FilingIndex, item_text: str) -> tuple[ExhibitCandidate, ...]:
    """The filing's ``EX-99*`` exhibits in the order R1.2 tries them."""
    exhibits = sorted(index.exhibits_99(), key=lambda document: document.sequence or 0)
    named = named_numbers(item_text)
    groups: dict[ExhibitChoice, list[ExhibitCandidate]] = {
        choice: []
        for choice in (
            ExhibitChoice.NAMED,
            ExhibitChoice.DESCRIBED,
            ExhibitChoice.LOWEST_SEQUENCE,
        )
    }
    for document in exhibits:
        if _type_number(document) in named:
            choice = ExhibitChoice.NAMED
        elif _RELEASE.search(document.description):
            choice = ExhibitChoice.DESCRIBED
        else:
            choice = ExhibitChoice.LOWEST_SEQUENCE
        groups[choice].append(ExhibitCandidate(document, choice))
    return tuple(candidate for group in groups.values() for candidate in group)
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/exhibits.py`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_exhibits.py -q`

Expected: `17 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/exhibits.py packages/earnings-ingestion/tests/test_events_exhibits.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1449 passed, 24 deselected`; `All checks passed!` and
`261 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/exhibits.py packages/earnings-ingestion/tests/test_events_exhibits.py
git commit -m "feat(events): R1.2's exhibit choice"
```

---

### Task 13: `release-content/1`

S §Content confirmation, and P8-9. `confirm(result, period_end, fiscal_year,
fiscal_period)` says whether a canonicalized exhibit is its slot's release: its whole
text states the period, as `release-id/1` reads a statement, and its opening
announces results. `release.py`'s period test becomes public as `states_period`, so
the two policies read a period one way; `release-id/1`'s behavior is unchanged, and
events v1 rebuilds to the same hash.

The tests pin the rule on Stage 1's eight committed releases, which must each be
confirmed, and on built texts. `test_stage_1_s_saved_exhibits_are_judged_as_before`
reads Stage 1's 168 saved exhibits under `data/raw/discovery/`, and pins the twelve
whose openings announce nothing; it skips without them.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/content.py`.
- Modify, by exact replacement: `events/release.py`.
- Test: create `packages/earnings-ingestion/tests/test_events_content.py`.

**Interfaces:**

- Consumes: `Canonicalized` in `canonical/records.py`, with its `document` and
  `elements`; `ElementType` in `earnings_core`; `canonicalize`.
- Produces:
  - in `events/release.py`: `states_period(text: str, period_end: date,
    fiscal_year: int | None, fiscal_period: str | None) -> bool`;
  - in `events/content.py`: `CONTENT_POLICY = "release-content/1"`, `OPENING = 12`,
    `Confirmation(period, announced, detail)` with its `confirmed` property,
    `opening(result) -> str`, and `confirm(result, period_end, fiscal_year,
    fiscal_period) -> Confirmation`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_content.py`:

```python
"""``release-content/1`` (the Stage 5 spec, §Content confirmation): an exhibit is the
slot's release when its text states the slot's period, as ``release-id/1`` reads it,
and its opening announces results. Stage 1's eight committed releases and invented
texts pin the vocabulary; Stage 1's 168 saved exhibits are checked where saved."""

from datetime import date
from pathlib import Path

import pytest
from earnings_ingestion.canonical import CanonicalizationFailure, canonicalize
from earnings_ingestion.events.content import OPENING, confirm

REPO = Path(__file__).resolve().parents[3]
RELEASES = REPO / "tests" / "fixtures" / "releases"
DISCOVERY = REPO / "data" / "raw" / "discovery"

STAGE_1 = {
    "0000007332-09-000032_ex-99": (date(2009, 9, 30), 2009, "Q3"),
    "0000009389-10-000004_ex-99-1": (date(2009, 12, 31), 2009, "FY"),
    "0000010795-22-000014_ex-99-1": (date(2021, 12, 31), 2022, "Q1"),
    "0000037785-14-000003_ex-99-1": (date(2013, 12, 31), 2013, "FY"),
    "0000092380-07-000011_ex-99-1": (date(2007, 3, 31), 2007, "Q1"),
    "0000706863-16-000110_ex-99-1": (date(2016, 6, 30), 2016, "Q2"),
    "0000877860-13-000100_ex-99-1": (date(2013, 9, 30), 2013, "Q3"),
    "0000949699-08-000023_ex-99-1": (date(2008, 6, 30), 2008, "FY"),
}
"""Each committed release's period end and fiscal labels, from its filing."""

NOT_ANNOUNCED = {
    "0000015847-10-000006_ex-99",
    "0000068270-05-000104_ex-99",
    "0000700565-07-000011_ex-99",
    "0000897101-15-000604_ex-99-1",
    "0001065280-12-000007_ex-99-1",
    "0001104659-24-081453_ex-99-1",
    "0001172358-08-000017_ex-99-1",
    "0001367644-10-000005_ex-99-1",
    "0001377789-24-000036_ex-99-1",
    "0001493152-20-014749_ex-99",
    "0001538716-20-000102_ex-99-1",
    "0001572910-14-000003_ex-99-1",
}
"""Stage 1's saved exhibits whose opening announces no results: the six that are not
releases (AMC's pro forma overview, Donaldson's guidance, Dorchester's and Phillips 66
Partners' distributions, Aviat's delayed 10-K, and Oportun's business update), and six
releases worded otherwise."""


def html(*blocks: str) -> bytes:
    return f"<html><body>{''.join(blocks)}</body></html>".encode()


def canonical(raw: bytes, name: str = "0009990001-25-000012_ex991.htm"):
    result = canonicalize(raw, source_document_id=name, media_type="text/html")
    assert not isinstance(result, CanonicalizationFailure), result
    return result


@pytest.mark.parametrize("fixture", sorted(STAGE_1))
def test_stage_1_s_committed_releases_are_confirmed(fixture: str) -> None:
    period_end, year, period = STAGE_1[fixture]
    result = canonical((RELEASES / fixture / "source.html").read_bytes(), fixture)
    check = confirm(result, period_end, year, period)
    assert (check.period, check.announced, check.confirmed) == (True, True, True)
    assert check.detail is None


RELEASE = html(
    "<h1>Acme Industrial Corp Reports Third Quarter Fiscal 2025 Results</h1>",
    "<p>Acme Industrial Corp today reported net sales of $1.2 billion for the quarter"
    " ended February 28, 2025.</p>",
)


def test_a_release_states_its_period_by_date_or_by_labels() -> None:
    result = canonical(RELEASE)
    assert confirm(result, date(2025, 2, 28), None, None).confirmed
    assert confirm(result, date(2025, 3, 1), 2025, "Q3").confirmed
    wrong = confirm(result, date(2025, 3, 1), 2025, "Q2")
    assert (wrong.period, wrong.announced, wrong.confirmed) == (False, True, False)
    assert wrong.detail == "it states no period ended 2025-03-01, and no Q2 2025"


def test_labels_other_than_a_quarter_or_a_year_judge_nothing() -> None:
    result = canonical(
        html("<p>Acme reported results for the third quarter of fiscal 2025.</p>")
    )
    assert not confirm(result, date(2025, 2, 28), 2025, "H1").period
    assert confirm(result, date(2025, 2, 28), 2025, "Q3").period


def test_a_fourth_quarter_or_full_year_is_the_year_s_period() -> None:
    result = canonical(
        html("<p>Corvid announced its fourth quarter and full year 2025 results.</p>")
    )
    assert confirm(result, date(2025, 12, 31), 2025, "FY").confirmed


def test_an_overview_that_announces_nothing_is_not_confirmed() -> None:
    """V2's AMC case: a pro forma overview that states the period, and announces no
    results."""
    result = canonical(
        html(
            "<h1>Pro Forma Financial Overview</h1>",
            "<p>Twelve months ended June 30, 2025</p>",
            "<table><tr><td>Revenue</td><td>1,000</td></tr></table>",
        )
    )
    check = confirm(result, date(2025, 6, 30), None, None)
    assert (check.period, check.announced, check.confirmed) == (True, False, False)
    assert check.detail == "its opening announces no results"


def test_only_the_opening_is_read_for_the_announcement() -> None:
    filler = [f"<p>Line {n}.</p>" for n in range(OPENING)]
    late = canonical(
        html(
            *filler,
            "<p>Acme reported results for the quarter ended February 28, 2025.</p>",
        )
    )
    assert not confirm(late, date(2025, 2, 28), None, None).announced
    early = canonical(
        html(
            *filler[1:],
            "<p>Acme reported results for the quarter ended February 28, 2025.</p>",
        )
    )
    assert confirm(early, date(2025, 2, 28), None, None).announced


@pytest.mark.parametrize(
    ("sentence", "announced"),
    [
        ("Dynamo Motors posted record revenue in its third quarter.", True),
        ("Eastfield Bank announces second quarter 2025 net income.", True),
        ("Borealis Air delivered EPS of $1.10.", True),
        ("Acme reported. Results follow in the tables.", False),
        ("Acme announced a quarterly cash distribution.", False),
        ("Acme updated its guidance for fiscal 2025 sales.", False),
    ],
)
def test_the_announcement_s_vocabulary(sentence: str, announced: bool) -> None:
    check = confirm(
        canonical(html(f"<p>{sentence}</p>")), date(2025, 9, 30), None, None
    )
    assert check.announced is announced


def test_stage_1_s_saved_exhibits_are_judged_as_before() -> None:
    """Of Stage 1's 168 saved exhibits, exactly these twelve announce no results in
    their opening. Every one states some period, so the announcement decides."""
    if not DISCOVERY.is_dir():
        pytest.skip("data/raw/discovery is not saved here")
    silent = set()
    pages = sorted(p for p in DISCOVERY.iterdir() if (p / "source.html").is_file())
    for page in pages:
        result = canonical((page / "source.html").read_bytes(), page.name)
        if not confirm(result, date(1900, 1, 1), None, None).announced:
            silent.add(page.name)
    assert len(pages) == 168
    assert silent == NOT_ANNOUNCED
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/tests/test_events_content.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_content.py -q`

Expected: FAIL: `1 error`, with
`ModuleNotFoundError: No module named 'earnings_ingestion.events.content'`.

- [x] **Step 3: Write the policy, and share the period test**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/content.py`:

```python
"""``release-content/1``: whether an exhibit is its slot's release (the Stage 5 spec,
§Content confirmation; plan 8, P8-9).

An exhibit that ``walker-1`` canonicalized is confirmed when both hold:

- **The period.** Its whole canonical text states the slot's period as
  ``release-id/1`` reads a statement: a full date after "ended" or "ending" that is
  the period end, or a fiscal period that matches the slot's labels, judged only for
  ``Q1``, ``Q2``, ``Q3``, and ``FY`` (``release.states_period``). The whole text is
  read, since a release's tables often carry the date.
- **The announcement.** Its opening, the first 12 heading, paragraph, and list-item
  elements joined by spaces, announces results: "report", "announce", "post", or
  "deliver", in a form the pattern lists, followed within 160 characters, with no
  full stop between, by "results", "earnings", "net income", "net earnings", "net
  loss", "net sales", "revenue", "sales", "profit", or "EPS", in any case.

Stage 1's 168 saved exhibits fixed the vocabulary. It rejects the six that are not
releases, V2's AMC pro forma overview among them, and confirms 156 of the 162
releases; every one of the 168 states some period in its whole text. Stage 1's eight
committed releases and the synthetic exhibits pin it in the default suite.
"""

import re
from dataclasses import dataclass
from datetime import date

from earnings_core import ElementType

from earnings_ingestion.canonical.records import Canonicalized
from earnings_ingestion.events.release import states_period

CONTENT_POLICY = "release-content/1"
OPENING = 12
"""How many heading, paragraph, and list-item elements make the opening."""
_BLOCKS = frozenset({ElementType.HEADING, ElementType.PARAGRAPH, ElementType.LIST_ITEM})
_VERB = (
    r"\b(?:report(?:s|ed|ing)?|announce(?:s|d|ing)?|post(?:s|ed)?|deliver(?:s|ed)?)\b"
)
_NOUN = (
    r"\b(?:results?|earnings|net\s+(?:income|earnings|loss|sales)|revenues?|sales"
    r"|profit|eps)\b"
)
_ANNOUNCES = re.compile(rf"{_VERB}[^.]{{0,160}}?{_NOUN}", re.IGNORECASE)


@dataclass(frozen=True)
class Confirmation:
    period: bool
    """The text states the slot's period."""
    announced: bool
    """The opening announces results."""
    detail: str | None
    """What it lacks; ``None`` when confirmed."""

    @property
    def confirmed(self) -> bool:
        return self.period and self.announced


def opening(result: Canonicalized) -> str:
    """The first ``OPENING`` heading, paragraph, and list-item elements' text."""
    text = result.document.canonical_text
    blocks = [
        text[element.span.start : element.span.end]
        for element in result.elements
        if element.type in _BLOCKS
    ][:OPENING]
    return " ".join(" ".join(block.split()) for block in blocks)


def confirm(
    result: Canonicalized,
    period_end: date,
    fiscal_year: int | None,
    fiscal_period: str | None,
) -> Confirmation:
    """Whether ``result`` is the release of the slot ending ``period_end``, with the
    fiscal labels ``fiscal_year`` and ``fiscal_period``."""
    stated = states_period(
        result.document.canonical_text, period_end, fiscal_year, fiscal_period
    )
    announced = _ANNOUNCES.search(opening(result)) is not None
    lacks = []
    if not stated:
        labelled = fiscal_year is not None and fiscal_period is not None
        also = f", and no {fiscal_period} {fiscal_year}" if labelled else ""
        lacks.append(f"it states no period ended {period_end}{also}")
    if not announced:
        lacks.append("its opening announces no results")
    return Confirmation(stated, announced, "; ".join(lacks) or None)
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/content.py`.

Create `/tmp/plan8-task13-source.py`:

```python
"""Plan 8: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/release.py": [
        (
            "def _matches(period: FiscalPeriod, labels: FiscalLabels | None) -> bool | None:\n"
            "    \"\"\"Whether a fiscal period matches the slot's labels; ``None`` when unjudged.\"\"\"\n"
            "    if labels is None or labels.fiscal_period not in _JUDGED:\n"
            "        return None\n"
            "    wanted = {\"Q4\", \"FY\"} if labels.fiscal_period == \"FY\" else {labels.fiscal_period}\n"
            "    return period.year == labels.fiscal_year and period.period in wanted\n",
            "def _wanted(fiscal_period: str) -> frozenset[str] | None:\n"
            "    \"\"\"The periods that match labels of ``fiscal_period``; ``None`` when unjudged.\"\"\"\n"
            "    if fiscal_period not in _JUDGED:\n"
            "        return None\n"
            "    return frozenset({\"Q4\", \"FY\"} if fiscal_period == \"FY\" else {fiscal_period})\n"
            "\n"
            "\n"
            "def _matches(period: FiscalPeriod, labels: FiscalLabels | None) -> bool | None:\n"
            "    \"\"\"Whether a fiscal period matches the slot's labels; ``None`` when unjudged.\"\"\"\n"
            "    wanted = None if labels is None else _wanted(labels.fiscal_period)\n"
            "    if wanted is None:\n"
            "        return None\n"
            "    return period.year == labels.fiscal_year and period.period in wanted\n"
            "\n"
            "\n"
            "def states_period(\n"
            "    text: str, period_end: date, fiscal_year: int | None, fiscal_period: str | None\n"
            ") -> bool:\n"
            "    \"\"\"Whether ``text`` states the period ending ``period_end`` as the rule reads a\n"
            "    statement: a full date after \"ended\" or \"ending\" that is ``period_end``, or a\n"
            "    fiscal period that matches the labels ``fiscal_year`` and ``fiscal_period``,\n"
            "    judged only for ``Q1``, ``Q2``, ``Q3``, and ``FY``. ``release-content/1`` reads\n"
            "    an exhibit's whole text this way (plan 8, P8-9).\"\"\"\n"
            "    if period_end in _dates(text):\n"
            "        return True\n"
            "    wanted = None if fiscal_period is None else _wanted(fiscal_period)\n"
            "    if fiscal_year is None or wanted is None:\n"
            "        return False\n"
            "    return any(\n"
            "        period.year == fiscal_year and period.period in wanted\n"
            "        for period in _periods(text)\n"
            "    )\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task13-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_content.py -q`

Expected: `20 passed`. If it reports `19 passed, 1 skipped`, Stage 1's saved exhibits
are missing: stop and ask (Preconditions).

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/content.py packages/earnings-ingestion/src/earnings_ingestion/events/release.py packages/earnings-ingestion/tests/test_events_content.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1469 passed, 24 deselected`; `All checks passed!` and
`263 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/content.py packages/earnings-ingestion/src/earnings_ingestion/events/release.py packages/earnings-ingestion/tests/test_events_content.py
git commit -m "feat(events): release-content/1 confirms an exhibit as its slot's release"
```

---

### Task 14: The synthetic layer's exhibits

P8-10. Plan A's layer names each candidate's exhibits on its index page, and serves
none. `layer.exhibit_bodies()` now gives every exhibit acquisition fetches, keyed by
URL, and `synthetic.exhibit_page(page, registrant, period_end)` writes each invented
page: a release, a narrative-only release, a supplement, an overview, or an
image-only page. Six events carry plan B's cases (P8-10). Their wording is invented,
modeled on Stage 1's exhibits without copying them.

`Release.exhibits` replaces the single `exhibit`, so the index pages and Item 2.02 text
of two filings change, and so does the evidence record that cites them. The event
manifest's and the pilot's content hashes do not change, since no fact changes.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/events/layer.py` and
  `events/synthetic.py`.
- Test (modify, by exact replacement):
  `packages/earnings-ingestion/tests/test_events_layer.py`.
- Regenerate: `tests/fixtures/events/`.

**Interfaces:**

- Consumes: plan A's `Registrant`, `SyntheticFiling`, and `Release` in
  `events/layer.py`; `archive_url` in `sec/urls.py`.
- Produces:
  - in `events/layer.py`: `Exhibit(kind, description, page="release")`,
    `RELEASE_EXHIBIT`, `Release.exhibits: tuple[Exhibit, ...]`,
    `exhibit_name(registrant, filing, kind) -> str`, and
    `exhibit_bodies() -> dict[str, tuple[bytes, str]]`, each exhibit's body and media
    type by URL;
  - in `events/synthetic.py`: `exhibit_page(page: str, registrant: str, period_end:
    date) -> bytes`.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task14-tests.py`:

```python
"""Plan 8: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_events_layer.py": [
        (
            "from earnings_ingestion.cohort.freeze import load_manifest\n"
            "from earnings_ingestion.events.acceptance import Convention\n"
            "from earnings_ingestion.events.eligibility import decide, memberships\n"
            "from earnings_ingestion.events.filings import IssuerFilings, issuer_filings\n"
            "from earnings_ingestion.events.layer import ACME, filings, write_layer\n",
            "from earnings_ingestion.canonical import CanonicalizationFailure, canonicalize\n"
            "from earnings_ingestion.canonical.records import FailureReason\n"
            "from earnings_ingestion.cohort.freeze import load_manifest\n"
            "from earnings_ingestion.events.acceptance import Convention\n"
            "from earnings_ingestion.events.content import confirm\n"
            "from earnings_ingestion.events.eligibility import decide, memberships\n"
            "from earnings_ingestion.events.filings import IssuerFilings, issuer_filings\n"
            "from earnings_ingestion.events.layer import (\n"
            "    ACME,\n"
            "    CORVID,\n"
            "    DYNAMO,\n"
            "    EASTFIELD,\n"
            "    exhibit_bodies,\n"
            "    exhibit_name,\n"
            "    filings,\n"
            "    write_layer,\n"
            ")\n",
        ),
        (
            "def test_the_conventions_and_the_older_pages(read) -> None:\n",
            "def test_plan_b_s_exhibit_numbering(read) -> None:\n"
            "    \"\"\"Acme's release for 2025-08-31 lists a supplement as EX-99.1 before the release\n"
            "    as EX-99.2, and Eastfield's for 2025-09-30, an eligible event, is typed EX-99.\"\"\"\n"
            "    acme = read[\"cik-0009990001\"].identified[\"cik-0009990001:2025-08-31\"]\n"
            "    assert [\n"
            "        (d.doc_type, d.description) for d in acme.release.placed.index.exhibits_99()\n"
            "    ] == [(\"EX-99.1\", \"Supplemental information\"), (\"EX-99.2\", \"Press release\")]\n"
            "    eastfield = read[\"cik-0009990006\"].identified[\"cik-0009990006:2025-09-30\"]\n"
            "    assert [d.doc_type for d in eastfield.release.placed.index.exhibits_99()] == [\n"
            "        \"EX-99\"\n"
            "    ]\n"
            "\n"
            "\n"
            "def exhibit_url(registrant, accepted: str, kind: str) -> str:\n"
            "    (filing,) = [f for f, _ in filings(registrant) if f.accepted == accepted]\n"
            "    return archive_url(\n"
            "        registrant.cik, filing.accession, exhibit_name(registrant, filing, kind)\n"
            "    )\n"
            "\n"
            "\n"
            "CASES = [\n"
            "    (ACME, \"2025-09-25 16:05:00\", \"EX-99.1\", date(2025, 8, 31), 2026, \"Q1\", False),\n"
            "    (ACME, \"2025-09-25 16:05:00\", \"EX-99.2\", date(2025, 8, 31), 2026, \"Q1\", True),\n"
            "    (EASTFIELD, \"2025-10-17 07:30:00\", \"EX-99\", date(2025, 9, 30), 2025, \"Q3\", True),\n"
            "    (CORVID, \"2025-07-30 16:05:00\", \"EX-99.01\", date(2025, 6, 30), None, None, False),\n"
            "    (DYNAMO, \"2025-10-21 06:45:00\", \"EX-99.1\", date(2025, 9, 26), 2025, \"Q3\", True),\n"
            "    (CORVID, \"2025-04-30 16:05:00\", \"EX-99.01\", date(2025, 3, 31), 2025, \"Q1\", True),\n"
            "]\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\n"
            "    (\"registrant\", \"accepted\", \"kind\", \"period_end\", \"year\", \"period\", \"confirmed\"),\n"
            "    CASES,\n"
            ")\n"
            "def test_each_exhibit_is_what_its_case_needs(\n"
            "    registrant, accepted, kind, period_end, year, period, confirmed\n"
            ") -> None:\n"
            "    \"\"\"The supplement and the AMC-like overview state the period and announce\n"
            "    nothing; each release, the narrative-only one too, is confirmed.\"\"\"\n"
            "    body, media_type = exhibit_bodies()[exhibit_url(registrant, accepted, kind)]\n"
            "    result = canonicalize(body, source_document_id=\"x\", media_type=media_type)\n"
            "    assert not isinstance(result, CanonicalizationFailure)\n"
            "    check = confirm(result, period_end, year, period)\n"
            "    assert (check.period, check.confirmed) == (True, confirmed)\n"
            "\n"
            "\n"
            "def test_the_narrative_release_has_no_table() -> None:\n"
            "    body, _ = exhibit_bodies()[exhibit_url(DYNAMO, \"2025-10-21 06:45:00\", \"EX-99.1\")]\n"
            "    assert b\"<table\" not in body\n"
            "    other, _ = exhibit_bodies()[exhibit_url(DYNAMO, \"2025-02-11 06:45:00\", \"EX-99.1\")]\n"
            "    assert b\"<table\" in other\n"
            "\n"
            "\n"
            "def test_an_image_only_exhibit_and_one_sec_does_not_serve() -> None:\n"
            "    \"\"\"Eastfield's release for 2026-03-31 is an image, which walker-1 refuses, and\n"
            "    Dynamo's for 2025-03-28 is listed on its index page but never served.\"\"\"\n"
            "    body, media_type = exhibit_bodies()[\n"
            "        exhibit_url(EASTFIELD, \"2026-04-17 07:30:00\", \"EX-99.1\")\n"
            "    ]\n"
            "    result = canonicalize(body, source_document_id=\"x\", media_type=media_type)\n"
            "    assert isinstance(result, CanonicalizationFailure)\n"
            "    assert result.reason is FailureReason.NO_NATIVE_TEXT\n"
            "    assert exhibit_url(DYNAMO, \"2025-04-22 06:45:00\", \"EX-99.1\") not in exhibit_bodies()\n"
            "\n"
            "\n"
            "def test_the_conventions_and_the_older_pages(read) -> None:\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task14-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_layer.py -q`

Expected: FAIL: `1 error`, with
`ImportError: cannot import name 'exhibit_bodies' from 'earnings_ingestion.events.layer'`.

- [x] **Step 3: Add the exhibits**

Create `/tmp/plan8-task14-source.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/layer.py": [
        (
            "It saves no exhibit (EV2). Every company, filing, and word is invented; each case\n"
            "takes its shape from the real filings plan 7 read, never their wording.\n",
            "It saves no exhibit (EV2): ``exhibit_bodies()`` gives each candidate's exhibits,\n"
            "which plan B's acquisition fetches (plan 8, P8-10). Every company, filing, and word\n"
            "is invented; each case takes its shape from the real filings plans 7 and 8 read,\n"
            "never their wording.\n",
        ),
        (
            "  release. A release and a 10-Q accepted after the cutoff are never read.\n",
            "  release. A release and a 10-Q accepted after the cutoff are never read. Its release\n"
            "  for 2025-08-31 lists a supplement as ``EX-99.1`` before the release as ``EX-99.2``,\n"
            "  and its Item 2.02 text names both, so the first choice fails and the next confirms.\n",
        ),
        (
            "  release for 2025-09-26 is narrative-only.\n"
            "- **Eastfield Bank** leaves on 2026-06-22. It has no 10-Q for 2025-06-30, the first\n"
            "  ``period_gap`` case. Its submissions give true UTC. One older page is read, and one\n"
            "  is skipped by its dates.\n",
            "  release for 2025-09-26 is narrative-only, in its Item 2.02 text and in its exhibit,\n"
            "  which has no table. The exhibit of its release for 2025-03-28 is never served.\n"
            "- **Eastfield Bank** leaves on 2026-06-22. It has no 10-Q for 2025-06-30, the first\n"
            "  ``period_gap`` case. Its submissions give true UTC. One older page is read, and one\n"
            "  is skipped by its dates. Its release for 2025-09-30 is typed ``EX-99``, and the\n"
            "  exhibit of its release for 2026-03-31 is an image, which walker-1 refuses.\n",
        ),
        (
            "    SyntheticFiling,\n",
            "    HTML,\n"
            "    SyntheticFiling,\n",
        ),
        (
            "    older_page_entry,\n"
            ")\n",
            "    exhibit_page,\n"
            "    older_page_entry,\n"
            ")\n"
            "from earnings_ingestion.sec.urls import archive_url\n",
        ),
        (
            "class Release:\n",
            "class Exhibit:\n"
            "    \"\"\"An exhibit on a release filing's index page, and the invented page it is.\"\"\"\n"
            "\n"
            "    kind: str\n"
            "    \"\"\"Its type, such as ``EX-99.1``.\"\"\"\n"
            "    description: str\n"
            "    page: str = \"release\"\n"
            "    \"\"\"``release``, ``narrative``, ``supplement``, ``overview``, or ``image``, as\n"
            "    ``synthetic.exhibit_page`` writes them; ``missing`` when SEC never serves it.\"\"\"\n"
            "\n"
            "\n"
            "RELEASE_EXHIBIT = (Exhibit(\"EX-99.1\", \"Earnings release\"),)\n"
            "\n"
            "\n"
            "@dataclass(frozen=True)\n"
            "class Release:\n",
        ),
        (
            "    exhibit: tuple[str, str] = (\"EX-99.1\", \"Earnings release\")\n"
            "    \"\"\"The index page's only exhibit: its type and description.\"\"\"\n",
            "    exhibits: tuple[\"Exhibit\", ...] = ()\n"
            "    \"\"\"The index page's exhibits, in sequence; an earnings release typed ``EX-99.1``\n"
            "    when none is given.\"\"\"\n",
        ),
        (
            "_BOREALIS_EXHIBIT = (\"EX-99\", \"Earnings release\")\n"
            "_CORVID_EXHIBIT = (\"EX-99.01\", \"Earnings release\")\n",
            "_BOREALIS_EXHIBIT = (Exhibit(\"EX-99\", \"Earnings release\"),)\n"
            "_CORVID_EXHIBIT = (Exhibit(\"EX-99.01\", \"Earnings release\"),)\n",
        ),
        (
            "            exhibit=(\"EX-99.1\", \"Press release\"),\n",
            "            exhibits=(Exhibit(\"EX-99.1\", \"Press release\"),),\n",
        ),
        (
            "            _said(_ACME, \"its results for the first quarter of fiscal 2026\"),\n",
            "            (\n"
            "                (\n"
            "                    f\"{_ACME} announced its results for the first quarter of fiscal\"\n"
            "                    \" 2026, in the release furnished as Exhibit 99.2, with\"\n"
            "                    \" supplemental information furnished as Exhibit 99.1.\"\n"
            "                ),\n"
            "            ),\n"
            "            exhibits=(\n"
            "                Exhibit(\"EX-99.1\", \"Supplemental information\", \"supplement\"),\n"
            "                Exhibit(\"EX-99.2\", \"Press release\"),\n"
            "            ),\n",
        ),
        (
            "        Release(\"2024-07-25 07:00:00\", None, exhibit=_BOREALIS_EXHIBIT),\n",
            "        Release(\"2024-07-25 07:00:00\", None, exhibits=_BOREALIS_EXHIBIT),\n",
        ),
        (
            "            exhibit=_BOREALIS_EXHIBIT,\n"
            "        ),\n"
            "        Release(\"2024-11-12 09:00:00\", None, form=\"8-K/A\", exhibit=_BOREALIS_EXHIBIT),\n",
            "            exhibits=_BOREALIS_EXHIBIT,\n"
            "        ),\n"
            "        Release(\"2024-11-12 09:00:00\", None, form=\"8-K/A\", exhibits=_BOREALIS_EXHIBIT),\n",
        ),
        (
            "            _said(_BOREALIS, \"its fourth quarter and full year 2024 results\", \"99\"),\n"
            "            exhibit=_BOREALIS_EXHIBIT,\n"
            "        ),\n",
            "            _said(_BOREALIS, \"its fourth quarter and full year 2024 results\", \"99\"),\n"
            "            exhibits=_BOREALIS_EXHIBIT,\n"
            "        ),\n",
        ),
        (
            "            exhibit=_BOREALIS_EXHIBIT,\n",
            "            exhibits=_BOREALIS_EXHIBIT,\n",
        ),
        (
            "            _said(_CORVID, \"its full-year 2024 results\", \"99.01\"),\n"
            "            exhibit=_CORVID_EXHIBIT,\n"
            "        ),\n",
            "            _said(_CORVID, \"its full-year 2024 results\", \"99.01\"),\n"
            "            exhibits=_CORVID_EXHIBIT,\n"
            "        ),\n",
        ),
        (
            "            _said(_CORVID, \"its Q1 2025 results\", \"99.01\"),\n"
            "            exhibit=_CORVID_EXHIBIT,\n"
            "        ),\n",
            "            _said(_CORVID, \"its Q1 2025 results\", \"99.01\"),\n"
            "            exhibits=_CORVID_EXHIBIT,\n"
            "        ),\n",
        ),
        (
            "            exhibit=(\"EX-99.01\", \"Pro forma overview\"),\n",
            "            exhibits=(Exhibit(\"EX-99.01\", \"Pro forma overview\", \"overview\"),),\n",
        ),
        (
            "            _said(_CORVID, \"its third-quarter 2025 results\", \"99.01\"),\n"
            "            exhibit=_CORVID_EXHIBIT,\n"
            "        ),\n",
            "            _said(_CORVID, \"its third-quarter 2025 results\", \"99.01\"),\n"
            "            exhibits=_CORVID_EXHIBIT,\n"
            "        ),\n",
        ),
        (
            "            _said(_CORVID, \"its fourth quarter and full year 2025 results\", \"99.01\"),\n"
            "            exhibit=_CORVID_EXHIBIT,\n"
            "        ),\n",
            "            _said(_CORVID, \"its fourth quarter and full year 2025 results\", \"99.01\"),\n"
            "            exhibits=_CORVID_EXHIBIT,\n"
            "        ),\n",
        ),
        (
            "            _said(_CORVID, \"its first quarter of 2026 results\", \"99.01\"),\n"
            "            exhibit=_CORVID_EXHIBIT,\n"
            "        ),\n",
            "            _said(_CORVID, \"its first quarter of 2026 results\", \"99.01\"),\n"
            "            exhibits=_CORVID_EXHIBIT,\n"
            "        ),\n",
        ),
        (
            "            exhibit=_CORVID_EXHIBIT,\n",
            "            exhibits=_CORVID_EXHIBIT,\n",
        ),
        (
            "        ),\n"
            "        Release(\"2025-07-22 06:45:00\", None, items=(\"7.01\", \"9.01\")),\n",
            "            exhibits=(Exhibit(\"EX-99.1\", \"Earnings release\", \"missing\"),),\n"
            "        ),\n"
            "        Release(\"2025-07-22 06:45:00\", None, items=(\"7.01\", \"9.01\")),\n",
        ),
        (
            "            (f\"{_DYNAMO} furnished its quarterly earnings release as Exhibit 99.1.\",),\n"
            "        ),\n"
            "        Release(\n",
            "            (f\"{_DYNAMO} furnished its quarterly earnings release as Exhibit 99.1.\",),\n"
            "            exhibits=(Exhibit(\"EX-99.1\", \"Earnings release\", \"narrative\"),),\n"
            "        ),\n"
            "        Release(\n",
        ),
        (
            "            _said(_EASTFIELD, \"third quarter of 2025 earnings\"),\n",
            "            _said(_EASTFIELD, \"third quarter of 2025 earnings\", \"99\"),\n"
            "            exhibits=(Exhibit(\"EX-99\", \"Earnings release\"),),\n",
        ),
        (
            "            _said(_EASTFIELD, \"first quarter 2026 earnings\"),\n"
            "        ),\n"
            "        Release(\n",
            "            _said(_EASTFIELD, \"first quarter 2026 earnings\"),\n"
            "            exhibits=(Exhibit(\"EX-99.1\", \"Earnings release\", \"image\"),),\n"
            "        ),\n"
            "        Release(\n",
        ),
        (
            "def _exhibit(registrant: Registrant, filing: SyntheticFiling, release: Release):\n"
            "    kind, description = release.exhibit\n"
            "    digits = kind.removeprefix(\"EX-\").replace(\".\", \"\")\n"
            "    name = f\"{registrant.stem}-{filing.filing_date:%Y%m%d}-ex{digits}.htm\"\n"
            "    return ((description, name, kind),)\n",
            "def exhibit_name(registrant: Registrant, filing: SyntheticFiling, kind: str) -> str:\n"
            "    \"\"\"The file name of ``filing``'s exhibit of type ``kind``.\"\"\"\n"
            "    digits = kind.removeprefix(\"EX-\").replace(\".\", \"\")\n"
            "    return f\"{registrant.stem}-{filing.filing_date:%Y%m%d}-ex{digits}.htm\"\n"
            "\n"
            "\n"
            "def _exhibits(release: Release) -> tuple[Exhibit, ...]:\n"
            "    return release.exhibits or RELEASE_EXHIBIT\n"
            "\n"
            "\n"
            "def _exhibit(registrant: Registrant, filing: SyntheticFiling, release: Release):\n"
            "    return tuple(\n"
            "        (\n"
            "            exhibit.description,\n"
            "            exhibit_name(registrant, filing, exhibit.kind),\n"
            "            exhibit.kind,\n"
            "        )\n"
            "        for exhibit in _exhibits(release)\n"
            "    )\n",
        ),
        (
            "            number = entry.exhibit[0].removeprefix(\"EX-\")\n"
            "            items = [\n"
            "                (\"2.02\", entry.text),\n"
            "                *entry.other,\n"
            "                (\"9.01\", (f\"Exhibit {number}: {entry.exhibit[1]}.\",)),\n"
            "            ]\n",
            "            listed = tuple(\n"
            "                f\"Exhibit {exhibit.kind.removeprefix('EX-')}: {exhibit.description}.\"\n"
            "                for exhibit in _exhibits(entry)\n"
            "            )\n"
            "            items = [(\"2.02\", entry.text), *entry.other, (\"9.01\", listed)]\n",
        ),
        (
            "    return store\n"
            "\n"
            "\n",
            "    return store\n"
            "\n"
            "\n"
            "def _period_end(registrant: Registrant, filing: SyntheticFiling) -> date:\n"
            "    \"\"\"The latest period end before ``filing``: the one its release reports.\"\"\"\n"
            "    return max(r.period for r in REPORTS[registrant] if r.period < filing.filing_date)\n"
            "\n"
            "\n"
            "def exhibit_bodies() -> dict[str, tuple[bytes, str]]:\n"
            "    \"\"\"Each candidate release filing's exhibits, by URL, with their media type: what\n"
            "    SEC serves when plan B's acquisition fetches them. An exhibit whose page is\n"
            "    ``missing`` is listed on its index page and never served.\"\"\"\n"
            "    bodies = {}\n"
            "    for registrant in REGISTRANTS:\n"
            "        for filing, entry in filings(registrant):\n"
            "            if isinstance(entry, Report) or entry.text is None:\n"
            "                continue\n"
            "            if \"2.02\" not in entry.items or not _in_range(filing):\n"
            "                continue\n"
            "            period_end = _period_end(registrant, filing)\n"
            "            for exhibit in _exhibits(entry):\n"
            "                if exhibit.page == \"missing\":\n"
            "                    continue\n"
            "                url = archive_url(\n"
            "                    registrant.cik,\n"
            "                    filing.accession,\n"
            "                    exhibit_name(registrant, filing, exhibit.kind),\n"
            "                )\n"
            "                page = exhibit_page(exhibit.page, registrant.name, period_end)\n"
            "                bodies[url] = (page, HTML)\n"
            "    return bodies\n"
            "\n"
            "\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py": [
        (
            "def save(\n",
            "def _written(day: date) -> str:\n"
            "    return f\"{day:%B} {day.day}, {day.year}\"\n"
            "\n"
            "\n"
            "def exhibit_page(page: str, registrant: str, period_end: date) -> bytes:\n"
            "    \"\"\"An invented EX-99 exhibit for the quarter ending ``period_end``:\n"
            "\n"
            "    - ``release``: a headline and a paragraph that report the quarter's results,\n"
            "      and a table of figures;\n"
            "    - ``narrative``: the same without a table, like Stage 1's narrative-only class;\n"
            "    - ``supplement``: supplemental tables under a heading, announcing nothing;\n"
            "    - ``overview``: a pro forma overview, like V2's AMC case, announcing nothing;\n"
            "    - ``image``: an image and no text, which walker-1 refuses.\n"
            "    \"\"\"\n"
            "    name, ended = escape(registrant), _written(period_end)\n"
            "    table = (\n"
            "        \"<table><tr><td>Net sales</td><td>1,000</td></tr>\"\n"
            "        \"<tr><td>Net income</td><td>100</td></tr></table>\"\n"
            "    )\n"
            "    parts = {\n"
            "        \"release\": [\n"
            "            f\"<h1>{name} Reports Results for the Quarter Ended {ended}</h1>\",\n"
            "            (\n"
            "                f\"<p>{name} today reported net sales of $1,000 million for the\"\n"
            "                f\" quarter ended {ended}.</p>\"\n"
            "            ),\n"
            "            table,\n"
            "        ],\n"
            "        \"narrative\": [\n"
            "            f\"<h1>{name} Reports Results for the Quarter Ended {ended}</h1>\",\n"
            "            (\n"
            "                f\"<p>{name} today reported higher deliveries for the quarter ended\"\n"
            "                f\" {ended}.</p>\"\n"
            "            ),\n"
            "            \"<p>The company will discuss the quarter on a call this morning.</p>\",\n"
            "        ],\n"
            "        \"supplement\": [\n"
            "            \"<h1>Supplemental Financial Information</h1>\",\n"
            "            f\"<p>Quarter ended {ended}</p>\",\n"
            "            table,\n"
            "        ],\n"
            "        \"overview\": [\n"
            "            \"<h1>Pro Forma Financial Overview</h1>\",\n"
            "            f\"<p>Twelve months ended {ended}</p>\",\n"
            "            table,\n"
            "        ],\n"
            "        \"image\": ['<p><img src=\"release.png\" alt=\"\"></p>'],\n"
            "    }[page]\n"
            "    return (\n"
            "        \"<!DOCTYPE html><html><head><title>Exhibit 99</title></head><body>\"\n"
            "        f\"{''.join(parts)}</body></html>\\n\"\n"
            "    ).encode()\n"
            "\n"
            "\n"
            "def save(\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task14-source`.

- [x] **Step 4: Regenerate the synthetic corpus**

```bash
uv run --locked --all-packages python tests/integration/regenerate_event_fixtures.py
find tests/fixtures/events -type f | wc -l
python3 -c "import json; [print(n, json.load(open(f'tests/fixtures/events/{n}'))['definition']['content_hash']) for n in ('events-v1.json', 'pilot-v1.json')]"
git status --short tests/fixtures/events
```

Expected: `wrote tests/fixtures/events/pilot-v1.json`; `172`;
`events-v1.json 438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58` and
`pilot-v1.json 71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c`,
unchanged; and 17 status lines: `M` for `events-v1.evidence.json`, `D` for four saved
pages and their four retrieval records, and `??` for four new pages and their four
retrieval directories. The four new pages are the Acme and Eastfield filings' index
pages and primary documents, which now name the new exhibits. If a hash differs,
stop: an earlier task's code differs from the plan's.

- [x] **Step 5: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_layer.py -q tests/integration/test_event_fixtures.py`

Expected: `24 passed`.

- [x] **Step 6: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/layer.py packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py packages/earnings-ingestion/tests/test_events_layer.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1478 passed, 24 deselected`; `All checks passed!` and
`263 files already formatted`.

- [x] **Step 7: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/layer.py packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py packages/earnings-ingestion/tests/test_events_layer.py tests/fixtures/events
git commit -m "feat(events): the synthetic layer's exhibits, for plan B's cases"
```

---

### Task 15: `fetch.responses`: the fetched record without a client

P8-12. Discovery imports `Fetched` from `fetch/client.py`, which loads httpx, so the
import scan carries an allowance for it, and discovery is kept out of the offline
path's boundary test. Acquisition needs `Fetched` and `UnexpectedResponse` too.
`fetch/responses.py` now holds both, `fetch/client.py` imports them from there, so
every existing import of them from `fetch.client` still works, and discovery imports
them from `fetch.responses`. The scan then needs no allowance, and discovery joins the
offline path's boundary test.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/fetch/responses.py`.
- Modify, by exact replacement: `fetch/client.py` and `events/discover.py`.
- Test (modify, by exact replacement):
  `packages/earnings-ingestion/tests/test_import_boundaries.py` and
  `tests/contracts/test_import_scan.py`.

**Interfaces:**

- Consumes: `Fetched(body, retrieval)` and `UnexpectedResponse` in
  `fetch/client.py`.
- Produces: `earnings_ingestion.fetch.responses.Fetched` and
  `earnings_ingestion.fetch.responses.UnexpectedResponse`, which `fetch.client` still
  exports.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task15-tests.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_import_boundaries.py": [
        (
            "    \"earnings_ingestion.events.eligibility\",\n",
            "    \"earnings_ingestion.events.discover\",\n"
            "    \"earnings_ingestion.events.eligibility\",\n",
        ),
        (
            "@pytest.mark.parametrize(\"module\", [*EVENTS, \"earnings_ingestion.events.discover\"])\n",
            "@pytest.mark.parametrize(\"module\", EVENTS)\n",
        ),
        (
            "    \"\"\"Building, freezing, and selecting read saved responses (A §410).\"\"\"\n",
            "    \"\"\"Building, freezing, and selecting read saved responses (A §410), and\n"
            "    discovery takes a fetch callable, so it loads no client; only the CLI opens one\n"
            "    (P6-22; plan 8, P8-12).\"\"\"\n",
        ),
    ],
    "tests/contracts/test_import_scan.py": [
        (
            "FETCHED = \"earnings_ingestion.fetch.client.Fetched\"\n",
            "",
        ),
        (
            "    resolve. Only discovery's import of ``Fetched`` is allowed.\"\"\"\n",
            "    resolve. None is allowed: ``Fetched`` and ``UnexpectedResponse`` come from\n"
            "    ``fetch.responses``, which holds no client (plan 8, P8-12).\"\"\"\n",
        ),
        (
            "        and (path, name) != (DISCOVER, FETCHED)\n",
            "",
        ),
        (
            "\n"
            "\n"
            "def test_discovery_imports_the_fetched_record_it_is_allowed() -> None:\n"
            "    \"\"\"The one allowance is still in use, so it cannot outlive its import.\"\"\"\n"
            "    assert FETCHED in {name for _, name in imported_names(DISCOVER)}\n",
            "",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task15-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py -q`

Expected: FAIL: `2 failed, 65 passed`. Discovery loads `httpx` and
`earnings_ingestion.fetch.client`, and the scan reports
`packages/earnings-ingestion/src/earnings_ingestion/events/discover.py:47 imports earnings_ingestion.fetch.client.Fetched`.

- [x] **Step 3: Move the two names**

Create `packages/earnings-ingestion/src/earnings_ingestion/fetch/responses.py`:

```python
"""What a fetch returns, or how it refuses a response (plan 8, P8-12).

These hold no client and load no network library, so a package function that takes
a fetch callable, such as discovery or acquisition, never loads the client that the
CLI opens (P6-22). ``fetch.client`` raises and returns them.
"""

from dataclasses import dataclass

from earnings_ingestion.fetch.records import Retrieval


class UnexpectedResponse(RuntimeError):
    """A response that must not be kept; the caller may skip the item and go on."""


@dataclass(frozen=True)
class Fetched:
    """A validated response body and the record of its retrieval."""

    body: bytes
    retrieval: Retrieval
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/src/earnings_ingestion/fetch/responses.py`.

Create `/tmp/plan8-task15-source.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/discover.py": [
        (
            "from earnings_ingestion.fetch.client import Fetched\n",
            "from earnings_ingestion.fetch.responses import Fetched\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py": [
        (
            "  store decides where bytes live.\n",
            "  store decides where bytes live. ``Fetched`` and ``UnexpectedResponse`` live in\n"
            "  ``fetch.responses``, which loads no network library.\n",
        ),
        (
            "from dataclasses import dataclass\n",
            "",
        ),
        (
            "\n"
            "DEFAULT_MAX_REQUESTS = 500\n",
            "from earnings_ingestion.fetch.responses import Fetched, UnexpectedResponse\n"
            "\n"
            "DEFAULT_MAX_REQUESTS = 500\n",
        ),
        (
            "\n"
            "\n"
            "class UnexpectedResponse(RuntimeError):\n"
            "    \"\"\"A response that must not be kept; the caller may skip the item and go on.\"\"\"\n",
            "",
        ),
        (
            "\n"
            "\n"
            "@dataclass(frozen=True)\n"
            "class Fetched:\n"
            "    \"\"\"A validated response body and the record of its retrieval.\"\"\"\n"
            "\n"
            "    body: bytes\n"
            "    retrieval: Retrieval\n",
            "",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task15-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py -q`

Expected: `67 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/discover.py packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py packages/earnings-ingestion/src/earnings_ingestion/fetch/responses.py packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1478 passed, 24 deselected`; `All checks passed!` and
`264 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/discover.py packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py packages/earnings-ingestion/src/earnings_ingestion/fetch/responses.py packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py
git commit -m "refactor(fetch): Fetched and UnexpectedResponse load no network library"
```

---

### Task 16: Acquisition (R1.2, R1.4)

S §Plan B, P8-6, and P8-12. `acquire(events, pilot, store, fetch, ...)` acquires
each pilot event's release document:

- It refuses a pilot not frozen over the event manifest it is given.
- It records `expected` for each pilot event with no transition under the pilot, in
  selection order.
- For each document `expected` or `acquired`, it reads the release filing's saved
  index page and Item 2.02 text, orders the exhibits (Task 12), and tries each: a
  saved exhibit is read from the store, and any other is fetched through `fetch` and
  saved. The first exhibit's bytes make the document `acquired`. `walker-1`
  canonicalizes each, and the first that `release-content/1` confirms makes it
  `parsed`, with its canonical document written under `canonical_dir`. Otherwise it
  becomes `unavailable` or `failed`, as P8-6 maps them. Every attempt is recorded.
- `UnexpectedResponse` is an attempt, and `AccessStop` ends the run with its
  transitions written and the rest `expected`.
- A saved response that cannot be read is a problem naming the manual repair, and is
  never fetched again (P8-2).
- It writes the run's transitions as one file, and nothing when it records nothing.

`planned_requests(events, pilot, store, states_dir)` states what a run would fetch.
On the real pilot, offline, it is `(40, 56)`, which
`test_the_first_acquisition_sends_40_to_56_requests` pins: it reads the real store,
and skips without it. `test_acquisition_changes_no_frozen_record_and_the_build_still_decides`
checks P-C7 after a run with a failure, and the import tests add every new module.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py`.
- Test: create `packages/earnings-ingestion/tests/test_events_acquire.py` and
  `tests/integration/test_event_store_v1.py`; modify, by exact replacement,
  `packages/earnings-ingestion/tests/test_import_boundaries.py` and
  `tests/contracts/test_import_scan.py`.

**Interfaces:**

- Consumes: Tasks 11 to 15; `SavedResponses` in `events/saved.py`;
  `read_filing_index`; `read_document` in `events/release.py`; `canonicalize`, and
  `to_fixture_json` in `canonical/serialize.py`; `ArtifactStore.put`; `archive_url`
  and `filing_index_url`; `EventManifest` and `PilotManifest`.
- Produces, in `events/acquire.py`:
  - `Fetch = Callable[[str, Collection[str]], Fetched]`; `EXHIBIT_TYPES`;
    `ATTEMPTED`; `REPAIR`;
  - `document_id(event_id: str) -> str`, which is `<event_id>:release`;
  - `Acquisition(run_id, transitions, states, fetched, problems, path)`;
  - `planned_requests(events, pilot, store, states_dir) -> tuple[int, int]`;
  - `acquire(events, pilot, store, fetch, *, states_dir, canonical_dir, run_id,
    now=...) -> Acquisition`. Task 17 adds the universe and the overrides, and
    Task 19 adds the overrides to `planned_requests`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_acquire.py`:

```python
"""Plan B's acquisition (the Stage 5 spec, §Plan B) over the synthetic layer and the
committed synthetic event manifest and pilot, with a fetch that serves the layer's
exhibits and counts each request."""

import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.acquire import (
    EXHIBIT_TYPES,
    acquire,
    planned_requests,
)
from earnings_ingestion.events.build import build_events, load_overrides
from earnings_ingestion.events.fixture import (
    COHORT_MANIFEST,
    FIXTURE_DIR,
    SYNTHETIC_CORPUS,
)
from earnings_ingestion.events.freeze import current_events, load_event_manifest
from earnings_ingestion.events.layer import exhibit_bodies, write_layer
from earnings_ingestion.events.pilot import current_pilot, load_pilot
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitChoice,
    MissingReason,
    current_states,
)
from earnings_ingestion.fetch.client import AccessStop, Fetched, UnexpectedResponse
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore

REPO = Path(__file__).resolve().parents[3]
FETCHED = datetime(2026, 9, 29, 15, 0, tzinfo=UTC)
NOW = datetime(2026, 9, 29, 15, 30, tzinfo=UTC)
E, A, P, F, U = (
    DocumentState.EXPECTED,
    DocumentState.ACQUIRED,
    DocumentState.PARSED,
    DocumentState.FAILED,
    DocumentState.UNAVAILABLE,
)


class Served:
    """SEC as the layer's exhibits: a 404 for any other URL, and a persistent 403
    once ``stop_after`` requests are sent."""

    def __init__(self, stop_after: int | None = None) -> None:
        self.bodies = exhibit_bodies()
        self.stop_after = stop_after
        self.requested: list[str] = []

    def __call__(self, url: str, types) -> Fetched:
        assert types == EXHIBIT_TYPES
        if self.stop_after is not None and len(self.requested) >= self.stop_after:
            raise AccessStop(f"403 persisted for {url}; stopping")
        self.requested.append(url)
        if url not in self.bodies:
            raise UnexpectedResponse(f"HTTP 404 for {url}")
        body, media_type = self.bodies[url]
        retrieval = Retrieval(
            request_url=url,
            final_url=url,
            retrieved_at=FETCHED,
            retrieval_method=RetrievalMethod.HTTP,
            http_status=200,
            media_type=media_type,
            content_type=media_type,
            byte_count=len(body),
            sha256=sha256_hex(body),
        )
        return Fetched(body=body, retrieval=retrieval)


def refuse(url: str, types) -> Fetched:
    raise AssertionError(f"a rerun fetched {url}")


@pytest.fixture(scope="module")
def frozen():
    universe = load_manifest(REPO / COHORT_MANIFEST)
    events = load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json")
    pilot = load_pilot(REPO / FIXTURE_DIR / "pilot-v1.json", universe)
    return universe, events, pilot


@pytest.fixture
def store(tmp_path) -> ArtifactStore:
    """The layer's saved responses, which hold no exhibit."""
    return write_layer(tmp_path / "data" / "raw" / "events", tmp_path).store


def run(frozen, store, fetch, tmp_path, run_id: str = "acquire-1"):
    _, events, pilot = frozen
    return acquire(
        events,
        pilot,
        store,
        fetch,
        states_dir=tmp_path / "states",
        canonical_dir=tmp_path / "canonical",
        run_id=run_id,
        now=lambda: NOW,
    )


def test_a_run_records_each_pilot_event_and_acquires_its_release(
    frozen, store, tmp_path
) -> None:
    served = Served()
    assert planned_requests(*frozen[1:], store, tmp_path / "states") == (27, 28)
    result = run(frozen, store, served, tmp_path)
    states = result.states
    assert len(states) == 27
    assert Counter(t.to_state for t in states.values()) == {P: 24, U: 2, F: 1}
    assert len(served.requested) == 28
    assert len(result.fetched) == 27
    assert len(result.transitions) == 80
    assert result.problems == ()
    assert result.path == tmp_path / "states" / "acquire-1.parquet"
    assert read_runs(tmp_path / "states") == list(result.transitions)
    parsed = [t for t in states.values() if t.to_state is P]
    assert sorted(p.name for p in (tmp_path / "canonical").iterdir()) == sorted(
        f"{t.doc_id}.json" for t in parsed
    )


def test_each_case_comes_to_its_state(frozen, store, tmp_path) -> None:
    states = run(frozen, store, Served(), tmp_path).states

    def attempts(event_id: str):
        return [
            (a.filename, a.choice, a.outcome)
            for a in states[f"{event_id}:release"].attempts
        ]

    acme = states["cik-0009990001:2025-08-31:release"]
    assert (acme.to_state, acme.exhibit) == (P, "acme-20250925-ex992.htm")
    assert attempts("cik-0009990001:2025-08-31") == [
        ("acme-20250925-ex991.htm", ExhibitChoice.NAMED, AttemptOutcome.NOT_CONFIRMED),
        ("acme-20250925-ex992.htm", ExhibitChoice.NAMED, AttemptOutcome.CONFIRMED),
    ]
    eastfield = states["cik-0009990006:2025-09-30:release"]
    assert (eastfield.to_state, eastfield.exhibit) == (P, "efb-20251017-ex99.htm")
    corvid = states["cik-0009990003:2025-06-30:release"]
    assert (corvid.to_state, corvid.missing_reason) == (
        U,
        MissingReason.NO_CONFIRMED_RELEASE,
    )
    assert attempts("cik-0009990003:2025-06-30") == [
        (
            "crvd-20250730-ex9901.htm",
            ExhibitChoice.NAMED,
            AttemptOutcome.NOT_CONFIRMED,
        )
    ]
    assert corvid.attempts[0].detail == "its opening announces no results"
    narrative = states["cik-0009990005:2025-09-26:release"]
    assert narrative.to_state is P
    image = states["cik-0009990006:2026-03-31:release"]
    assert (image.to_state, image.missing_reason, image.failure_reason) == (
        F,
        MissingReason.PARSE_FAILED,
        "no_native_text",
    )
    missing = states["cik-0009990005:2025-03-28:release"]
    assert (missing.from_state, missing.to_state, missing.missing_reason) == (
        E,
        U,
        MissingReason.NOT_FOUND,
    )
    assert missing.attempts[0].outcome is AttemptOutcome.NOT_FETCHED
    assert missing.attempts[0].detail.startswith("HTTP 404 for ")


def test_a_rerun_fetches_nothing_and_records_nothing(frozen, store, tmp_path) -> None:
    first = run(frozen, store, Served(), tmp_path)
    assert planned_requests(*frozen[1:], store, tmp_path / "states") == (0, 0)
    again = run(frozen, store, refuse, tmp_path, run_id="acquire-2")
    assert (again.transitions, again.path) == ((), None)
    assert again.states == first.states


def test_a_persistent_403_stops_the_run_and_leaves_the_rest_expected(
    frozen, store, tmp_path
) -> None:
    """R1.3: the run stops, its transitions so far are written, and a rerun takes up
    each document not yet attempted, fetching nothing twice."""
    stopped = Served(stop_after=3)
    with pytest.raises(AccessStop, match="403 persisted"):
        run(frozen, store, stopped, tmp_path)
    pilot_hash = frozen[2].definition.content_hash
    after = current_states(read_runs(tmp_path / "states"), pilot_hash)
    assert Counter(t.to_state for t in after.values()) == {E: 24, P: 3}
    order = [row.event_id for row in frozen[2].rows]
    assert [after[f"{event}:release"].to_state for event in order[:4]] == [P, P, P, E]
    served = Served()
    rest = run(frozen, store, served, tmp_path, run_id="acquire-2")
    assert Counter(t.to_state for t in rest.states.values()) == {P: 24, U: 2, F: 1}
    assert not set(served.requested) & set(stopped.requested)


def test_a_saved_exhibit_that_cannot_be_read_is_a_problem_never_fetched_again(
    frozen, store, tmp_path
) -> None:
    served = Served()
    first = frozen[2].rows[0].event_id
    row = next(row for row in frozen[1].rows if row.event_id == first)
    folder = row.release_accession.replace("-", "")
    url = next(url for url in served.bodies if f"/{folder}/" in url)
    fetched = served(url, EXHIBIT_TYPES)
    store.put(
        SEC_SOURCE_ID,
        fetched.body,
        fetched.retrieval,
        rights_status=SEC_RIGHTS.rights_status,
        rights_basis=SEC_RIGHTS.rights_basis,
    )
    saved_path = next((store.root / "sec-edgar").glob(f"{fetched.retrieval.sha256}.*"))
    saved_path.write_bytes(b"changed")
    served.requested.clear()
    result = run(frozen, store, served, tmp_path)
    (problem,) = result.problems
    assert problem.startswith(f"{url}: ")
    assert "repair the store by hand" in problem
    assert url not in served.requested
    assert result.states[f"{first}:release"].to_state is E


def test_acquisition_changes_no_frozen_record_and_the_build_still_decides(
    frozen, store, tmp_path
) -> None:
    """P-C7: after acquisition, failures included, the event manifest and the pilot
    are byte-identical, the build still reproduces v1, and the pilot over it is
    still v1, every selected event still selected (P8-4)."""
    corpus = tmp_path / "corpus"
    shutil.copytree(REPO / FIXTURE_DIR, corpus, ignore=shutil.ignore_patterns("raw"))
    before = {path.name: path.read_bytes() for path in corpus.iterdir()}
    result = run(frozen, store, Served(), tmp_path)
    assert {t.to_state for t in result.states.values()} >= {F, U}
    assert {path.name: path.read_bytes() for path in corpus.iterdir()} == before
    universe, events, pilot = frozen
    built = build_events(
        universe,
        SavedResponses(store),
        load_overrides(corpus / "overrides.toml"),
        corpus_id=SYNTHETIC_CORPUS,
    )
    current = current_events(built, corpus)
    assert current.manifest == events
    assert current_pilot(corpus, current.manifest, universe).manifest == pilot
    assert [row.event_id for row in pilot.rows] == list(
        dict.fromkeys(t.event_id for t in result.states.values())
    )


def test_a_pilot_not_frozen_over_the_manifest_is_refused(frozen, store, tmp_path):
    _, events, pilot = frozen
    other = pilot.model_copy(
        update={
            "definition": pilot.definition.model_copy(
                update={"eligible_event_manifest_hash": "0" * 64}
            )
        }
    )
    with pytest.raises(ValueError, match="is not frozen over events-v1.json"):
        acquire(
            events,
            other,
            store,
            refuse,
            states_dir=tmp_path / "states",
            canonical_dir=tmp_path / "canonical",
            run_id="acquire-1",
        )
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/tests/test_events_acquire.py`.

Create `tests/integration/test_event_store_v1.py`:

```python
"""The real corpus's frozen records against Stage 5's local store, which only this
machine holds: the test skips without it, so each gate runs it and reads "passed".

``planned_requests`` is what ``events acquire`` states before it sends anything, and
the live gate's count (plan 8, P8-12): the pilot's 40 release filings list 56
``EX-99*`` exhibits, and R1.2's order puts one first in each. That count holds until
the first acquisition saves its exhibits, so the test then skips.
"""

from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.acquire import planned_requests
from earnings_ingestion.events.freeze import load_event_manifest
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.fetch.store import ArtifactStore

REPO = Path(__file__).resolve().parents[2]
STORE = REPO / "data" / "raw" / "events"
CORPUS = REPO / "config" / "corpus" / "djia-2024q3-2026q2"
UNIVERSE = (
    REPO / "config" / "universe" / "djia" / "manifests" / "djia-2024q3-2026q2-v1.json"
)
STATES = REPO / "data" / "runs" / "events" / "states"


def test_the_first_acquisition_sends_40_to_56_requests(tmp_path) -> None:
    if not (STORE / "sec-edgar").is_dir():
        pytest.skip("data/raw/events is not saved here: each gate runs this test")
    if any(STATES.glob("*.parquet")):
        pytest.skip(
            "the first acquisition has run: docs/verification/djia-events.md"
            " records its count"
        )
    events = load_event_manifest(CORPUS / "events-v1.json")
    pilot = load_pilot(CORPUS / "pilot-v1.json", load_manifest(UNIVERSE))
    store = ArtifactStore(STORE, REPO)
    assert planned_requests(events, pilot, store, tmp_path / "states") == (40, 56)
```

Extract it with `python3 /tmp/plan8-extract.py tests/integration/test_event_store_v1.py`.

Create `/tmp/plan8-task16-tests.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_import_boundaries.py": [
        (
            "    \"earnings_ingestion.events.build\",\n",
            "    \"earnings_ingestion.events.acquire\",\n"
            "    \"earnings_ingestion.events.build\",\n"
            "    \"earnings_ingestion.events.content\",\n",
        ),
        (
            "    \"earnings_ingestion.events.filings\",\n",
            "    \"earnings_ingestion.events.exhibits\",\n"
            "    \"earnings_ingestion.events.filings\",\n",
        ),
        (
            "    \"earnings_ingestion.events.synthetic\",\n",
            "    \"earnings_ingestion.events.state_table\",\n"
            "    \"earnings_ingestion.events.states\",\n"
            "    \"earnings_ingestion.events.synthetic\",\n",
        ),
        (
            "    \"\"\"R14.5: no edgartools, pandas, or pyarrow output crosses the boundary.\"\"\"\n",
            "    \"\"\"R14.5: no edgartools, pandas, or pyarrow output crosses the boundary; the\n"
            "    state table is Polars alone.\"\"\"\n",
        ),
        (
            "    discovery takes a fetch callable, so it loads no client; only the CLI opens one\n"
            "    (P6-22; plan 8, P8-12).\"\"\"\n",
            "    discovery and acquisition take a fetch callable, so none loads a client; only\n"
            "    the CLI opens one (P6-22; plan 8, P8-12).\"\"\"\n",
        ),
    ],
    "tests/contracts/test_import_scan.py": [
        (
            "DISCOVER = SOURCES[\"earnings_ingestion\"] / \"events\" / \"discover.py\"\n"
            "\n"
            "\n",
            "DISCOVER = SOURCES[\"earnings_ingestion\"] / \"events\" / \"discover.py\"\n"
            "ACQUIRE = SOURCES[\"earnings_ingestion\"] / \"events\" / \"acquire.py\"\n"
            "\n"
            "\n",
        ),
        (
            "    discover`` spends only the count the CLI's gate approved.\"\"\"\n"
            "    paths = stage_5_modules()\n"
            "    assert DISCOVER in paths\n",
            "    discover`` and ``events acquire`` spend only the count the CLI's gate approved.\"\"\"\n"
            "    paths = stage_5_modules()\n"
            "    assert {DISCOVER, ACQUIRE} <= set(paths)\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task16-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_acquire.py packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/integration/test_event_store_v1.py -q`

Expected: FAIL: `2 errors`, collecting `test_events_acquire.py` and
`tests/integration/test_event_store_v1.py`, each with
`ModuleNotFoundError: No module named 'earnings_ingestion.events.acquire'`.

- [x] **Step 3: Write the acquisition**

> Deviation: after the final review (`55ea811`), a canonical file already under its `doc_id` that differs only in its manifest is kept, and any other difference is a problem, not a stop; `Acquisition.states` returns the state the run recorded when a problem follows a document's first exhibit; and an index page never saved names `events discover`, without the repair hint.

Create `packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py`:

```python
"""Plan B's acquisition: each pilot event's release document, fetched through the
shared SEC client, canonicalized, and confirmed (the Stage 5 spec, §Plan B; plan 8,
P8-6 to P8-12).

- **What it reads.** The caller passes the current event manifest and the pilot
  frozen over it, as ``events acquire`` reads them (P8-4). Acquisition writes no
  frozen record (P-C7).
- **Expected.** A run first records ``expected`` for each pilot event that has no
  transition under the pilot, in selection order.
- **Attempts.** It then attempts each document whose current state is ``expected``
  or ``acquired``. It reads the release filing's saved index page and Item 2.02 text,
  and tries the filing's ``EX-99*`` exhibits in R1.2's order (``exhibit_order``). A
  saved exhibit is read from the store; any other is fetched and saved. The first
  exhibit's bytes make the document ``acquired``. ``walker-1`` canonicalizes each,
  and the first that ``release-content/1`` confirms makes it ``parsed``, with its
  canonical document written under ``canonical_dir``. Otherwise the document is
  ``unavailable`` with ``not_found`` when no exhibit could be fetched, ``failed``
  with ``parse_failed`` and the first ``FailureReason`` when one failed to
  canonicalize, and ``unavailable`` with ``no_confirmed_release`` when each fetched
  canonicalized and none was confirmed. Every attempt is recorded.
- **Requests.** Only ``fetch`` sends, which ``events acquire`` gives as the shared
  SEC client's (R1.3, D5); acquisition has no throttle of its own. A response the
  client refuses (``UnexpectedResponse``: a status other than 200, an unexpected
  media type, or a redirect) is that exhibit's attempt, and the next is tried.
  ``AccessStop`` ends the run: its transitions so far are written, and each document
  not attempted stays ``expected``. Acquisition saves exhibits only, never an index
  page or a primary document, so it never changes what the event build reads.
- **Problems.** A saved response that cannot be read is a problem naming its repair;
  it is never fetched again, and its document keeps its state.
- **The run.** Each run writes its transitions to ``<run_id>.parquet`` under
  ``states_dir``, even when it stops, and writes nothing when it records nothing.
"""

from collections.abc import Callable, Collection
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from earnings_ingestion.canonical import (
    CanonicalizationFailure,
    Canonicalized,
    canonicalize,
)
from earnings_ingestion.canonical.serialize import to_fixture_json
from earnings_ingestion.cohort.locators import ArtifactText, CitableArtifact
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.content import confirm
from earnings_ingestion.events.exhibits import ExhibitCandidate, exhibit_order
from earnings_ingestion.events.freeze import manifest_path
from earnings_ingestion.events.records import EventManifest, EventRow, PilotManifest
from earnings_ingestion.events.release import read_document
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.state_table import read_runs, write_run
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitAttempt,
    MissingReason,
    StateTransition,
    current_states,
)
from earnings_ingestion.fetch.responses import Fetched, UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore, write_new
from earnings_ingestion.sec.data import SecDataError
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import archive_url, filing_index_url

Fetch = Callable[[str, Collection[str]], Fetched]
EXHIBIT_TYPES = frozenset({"text/html", "text/plain"})
ATTEMPTED = frozenset({DocumentState.EXPECTED, DocumentState.ACQUIRED})
REPAIR = (
    "repair the store by hand: a saved response is never fetched again (PR #6's"
    " review, P2.1)"
)


def document_id(event_id: str) -> str:
    return f"{event_id}:release"


@dataclass(frozen=True)
class Acquisition:
    run_id: str
    transitions: tuple[StateTransition, ...]
    """This run's."""
    states: dict[str, StateTransition]
    """Each pilot document's current state after the run, in selection order."""
    fetched: tuple[str, ...]
    """The URLs fetched and saved."""
    problems: tuple[str, ...]
    path: Path | None
    """The run's file; ``None`` when it recorded nothing."""


@dataclass(frozen=True)
class _Filing:
    """A pilot event's release filing, as its saved pages give it."""

    candidates: tuple[ExhibitCandidate, ...]


def _filing(saved: SavedResponses, row: EventRow) -> _Filing:
    """The filing's exhibits in R1.2's order, read from its saved index page and
    Item 2.02 text; raises ``ValueError``, naming the URL, when a page is not saved
    or cannot be read."""
    url = filing_index_url(row.cik, row.release_accession)
    try:
        artifact = saved.get(url)
        if artifact is None:
            raise ValueError(f"{url} is not saved: run events discover")
        index = read_filing_index(artifact.text.body)
    except (FileNotFoundError, SecDataError) as exc:
        raise ValueError(f"{url}: {exc}; {REPAIR}") from exc
    except ValueError as exc:
        raise ValueError(f"{url}: {exc}; {REPAIR}") from exc
    primary = [d for d in index.documents if d.doc_type == index.form]
    text = ""
    if primary:
        document = archive_url(row.cik, row.release_accession, primary[0].filename)
        try:
            found = saved.get(document)
        except (FileNotFoundError, ValueError) as exc:
            raise ValueError(f"{document}: {exc}; {REPAIR}") from exc
        reading = None if found is None else read_document(found)
        if reading is not None and reading.sections:
            body, _ = found.text.canonical
            text = " ".join(body[start:end] for start, end in reading.sections)
    return _Filing(exhibit_order(index, text))


def planned_requests(
    events: EventManifest,
    pilot: PilotManifest,
    store: ArtifactStore,
    states_dir: Path,
) -> tuple[int, int]:
    """What a run would fetch: the first choices not saved, and every candidate not
    saved, over the documents it would attempt. The second is the most it can send."""
    saved = SavedResponses(store)
    rows = {row.event_id: row for row in events.rows}
    current = current_states(read_runs(states_dir), pilot.definition.content_hash)
    first = most = 0
    for pilot_row in pilot.rows:
        state = current.get(document_id(pilot_row.event_id))
        if state is not None and state.to_state not in ATTEMPTED:
            continue
        row = rows[pilot_row.event_id]
        try:
            candidates = _filing(saved, row).candidates
        except ValueError:
            continue
        urls = [
            archive_url(row.cik, row.release_accession, c.document.filename)
            for c in candidates
        ]
        missing = [url for url in urls if url not in saved]
        most += len(missing)
        if urls and urls[0] in missing:
            first += 1
    return first, most


class _Run:
    def __init__(
        self, pilot: PilotManifest, run_id: str, now: Callable[[], datetime]
    ) -> None:
        self.pilot, self.run_id, self.now = pilot.definition, run_id, now
        self.transitions: list[StateTransition] = []

    def record(
        self,
        before: StateTransition | None,
        row: EventRow,
        state: DocumentState,
        **details: object,
    ) -> StateTransition:
        transition = StateTransition(
            document_id=document_id(row.event_id),
            event_id=row.event_id,
            run_id=self.run_id,
            sequence=len(self.transitions),
            recorded_at=self.now(),
            from_state=None if before is None else before.to_state,
            to_state=state,
            pilot_id=self.pilot.pilot_id,
            pilot_version=self.pilot.pilot_version,
            pilot_hash=self.pilot.content_hash,
            frozen_accession=row.release_accession,
            **details,
        )
        self.transitions.append(transition)
        return transition


class _Unusable(Exception):
    """A saved exhibit that cannot be read."""


def _exhibit(
    saved: SavedResponses,
    store: ArtifactStore,
    fetch: Fetch,
    url: str,
    fetched: list[str],
) -> CitableArtifact:
    """The exhibit at ``url``, read from the store, or fetched and saved."""
    if url in saved:
        try:
            artifact = saved.get(url)
        except (FileNotFoundError, ValueError) as exc:
            raise _Unusable(f"{url}: {exc}; {REPAIR}") from exc
        assert artifact is not None
        return artifact
    got = fetch(url, EXHIBIT_TYPES)
    ref = store.put(
        SEC_SOURCE_ID,
        got.body,
        got.retrieval,
        rights_status=SEC_RIGHTS.rights_status,
        rights_basis=SEC_RIGHTS.rights_basis,
    )
    fetched.append(url)
    return CitableArtifact(
        source_id=SEC_SOURCE_ID,
        url=url,
        artifact=ref,
        retrieved_at=got.retrieval.retrieved_at,
        text=ArtifactText(got.body, got.retrieval.media_type),
    )


def _write(canonical_dir: Path, result: Canonicalized) -> None:
    path = canonical_dir / f"{result.document.doc_id}.json"
    write_new(path, to_fixture_json(result).encode())


def _attempt(
    run: _Run,
    state: StateTransition,
    row: EventRow,
    candidates: tuple[ExhibitCandidate, ...],
    saved: SavedResponses,
    store: ArtifactStore,
    fetch: Fetch,
    canonical_dir: Path,
    fetched: list[str],
) -> StateTransition:
    attempts: list[ExhibitAttempt] = []
    failure = None
    for candidate in candidates:
        name = candidate.document.filename
        url = archive_url(row.cik, row.release_accession, name)
        tried = {
            "accession": row.release_accession,
            "filename": name,
            "exhibit_type": candidate.document.doc_type.strip(),
            "choice": candidate.choice,
        }
        try:
            artifact = _exhibit(saved, store, fetch, url, fetched)
        except UnexpectedResponse as refused:
            attempts.append(
                ExhibitAttempt(
                    **tried, outcome=AttemptOutcome.NOT_FETCHED, detail=str(refused)
                )
            )
            continue
        acquired = {
            "accession": row.release_accession,
            "exhibit": name,
            "artifact_sha256": artifact.artifact.content_sha256,
            "retrieved_at": artifact.retrieved_at,
        }
        if state.to_state is DocumentState.EXPECTED:
            state = run.record(state, row, DocumentState.ACQUIRED, **acquired)
        result = canonicalize(
            artifact.text.body,
            source_document_id=f"{row.release_accession}_{name}",
            media_type=artifact.text.media_type,
        )
        sha = artifact.artifact.content_sha256
        if isinstance(result, CanonicalizationFailure):
            attempts.append(
                ExhibitAttempt(
                    **tried,
                    outcome=AttemptOutcome.CANONICALIZATION_FAILED,
                    artifact_sha256=sha,
                    failure_reason=result.reason,
                    detail=result.detail,
                )
            )
            failure = failure or result.reason
            continue
        check = confirm(
            result,
            row.period_end,
            row.reported_fiscal_year,
            row.reported_fiscal_quarter,
        )
        if not check.confirmed:
            attempts.append(
                ExhibitAttempt(
                    **tried,
                    outcome=AttemptOutcome.NOT_CONFIRMED,
                    artifact_sha256=sha,
                    detail=check.detail,
                )
            )
            continue
        attempts.append(
            ExhibitAttempt(
                **tried, outcome=AttemptOutcome.CONFIRMED, artifact_sha256=sha
            )
        )
        _write(canonical_dir, result)
        return run.record(
            state,
            row,
            DocumentState.PARSED,
            **acquired,
            doc_id=result.document.doc_id,
            attempts=tuple(attempts),
        )
    if state.to_state is DocumentState.EXPECTED:
        reason = {"missing_reason": MissingReason.NOT_FOUND}
        return run.record(
            state, row, DocumentState.UNAVAILABLE, **reason, attempts=tuple(attempts)
        )
    if failure is not None:
        return run.record(
            state,
            row,
            DocumentState.FAILED,
            missing_reason=MissingReason.PARSE_FAILED,
            failure_reason=failure,
            attempts=tuple(attempts),
        )
    return run.record(
        state,
        row,
        DocumentState.UNAVAILABLE,
        missing_reason=MissingReason.NO_CONFIRMED_RELEASE,
        attempts=tuple(attempts),
    )


def acquire(
    events: EventManifest,
    pilot: PilotManifest,
    store: ArtifactStore,
    fetch: Fetch,
    *,
    states_dir: Path,
    canonical_dir: Path,
    run_id: str,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Acquisition:
    """Acquire the release of each pilot event of ``pilot``, which must be frozen
    over ``events``."""
    definition, read = pilot.definition, events.definition
    if (definition.event_manifest_version, definition.eligible_event_manifest_hash) != (
        read.event_manifest_version,
        read.content_hash,
    ):
        name = manifest_path(Path(), read.event_manifest_version).name
        raise ValueError(
            f"{definition.pilot_id} v{definition.pilot_version} is not frozen over {name}"
        )
    rows = {row.event_id: row for row in events.rows}
    current = current_states(read_runs(states_dir), definition.content_hash)
    saved = SavedResponses(store)
    run = _Run(pilot, run_id, now)
    fetched: list[str] = []
    problems: list[str] = []
    try:
        for pilot_row in pilot.rows:
            key = document_id(pilot_row.event_id)
            if key not in current:
                current[key] = run.record(
                    None,
                    rows[pilot_row.event_id],
                    DocumentState.EXPECTED,
                    missing_reason=MissingReason.NOT_YET_CHECKED,
                )
        for pilot_row in pilot.rows:
            key, row = document_id(pilot_row.event_id), rows[pilot_row.event_id]
            if current[key].to_state not in ATTEMPTED:
                continue
            try:
                candidates = _filing(saved, row).candidates
                current[key] = _attempt(
                    run,
                    current[key],
                    row,
                    candidates,
                    saved,
                    store,
                    fetch,
                    canonical_dir,
                    fetched,
                )
            except (_Unusable, ValueError) as problem:
                problems.append(str(problem))
    finally:
        path = write_run(states_dir, run.transitions) if run.transitions else None
    return Acquisition(
        run_id=run_id,
        transitions=tuple(run.transitions),
        states={
            document_id(r.event_id): current[document_id(r.event_id)]
            for r in pilot.rows
        },
        fetched=tuple(fetched),
        problems=tuple(problems),
        path=path,
    )
```

Extract it with `python3 /tmp/plan8-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_acquire.py packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/integration/test_event_store_v1.py -q`

Expected: `85 passed`. `test_the_first_acquisition_sends_40_to_56_requests` reads the
real store; if it reports `skipped`, stop and ask (Preconditions).

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py packages/earnings-ingestion/tests/test_events_acquire.py packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/integration/test_event_store_v1.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1496 passed, 24 deselected`; `All checks passed!` and
`267 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py packages/earnings-ingestion/tests/test_events_acquire.py packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py tests/integration/test_event_store_v1.py
git commit -m "feat(events): acquire each pilot event's release document (R1.2, R1.4)"
```

---

### Task 17: `set_release_document` overrides and the `corpus_error` guard

S §What acquisition can change, and P8-11. `acquisition-overrides.toml` names an
event's release document: an exhibit of the frozen filing, or of another filing by the
issuer whose index page is saved, cited as plan A's overrides are.

- `events/records.py` gains `AcquisitionOverride` and `AcquisitionOverridesFile`,
  which holds at most one override per `override_id` and per event.
- `build.py`'s citation check becomes public as `citations_refused`, taking either
  kind of override.
- `acquire` applies each override to a document that is `expected`, `acquired`,
  `unavailable`, or `failed`. Its document is the release once it canonicalizes, and
  the confirmation is recorded without deciding. When the other filing's acceptance
  would change eligibility, each of its transitions marks a `corpus_error`, and
  nothing is fixed in place. An override that does not check, or that names a
  `parsed` document, is a problem.
- `load_acquisition_overrides(path)` reads the file, and an absent file is empty.

No manifest hashes the file, and after an override's acquisition the build still
reproduces the frozen event manifest.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py`,
  `events/records.py`, and `events/build.py`; and `docs/data-dictionary.md`.
- Test (modify, by exact replacement):
  `packages/earnings-ingestion/tests/test_events_acquire.py` and
  `test_events_records.py`; and `tests/contracts/test_data_dictionary.py`.

**Interfaces:**

- Consumes: Task 16's `acquire`; `EventOverride`'s citations and `Citation` in
  `events/records.py`; `decide` and `memberships` in `events/eligibility.py`;
  `accepted_instant` in `events/acceptance.py`.
- Produces:
  - in `events/records.py`: `AcquisitionOverride(override_id, kind, event_id,
    accession, exhibit, citations, rationale, reviewer, recorded_on)`, with `kind`
    `"set_release_document"`, and `AcquisitionOverridesFile(overrides)`;
  - in `events/build.py`: `citations_refused(override, saved, folder) -> list[str]`;
  - in `events/acquire.py`: `OVERRIDDEN`, `OVERRIDES_FILE =
    "acquisition-overrides.toml"`, `load_acquisition_overrides(path) ->
    AcquisitionOverridesFile`, and `corpus_error(row, instant, membership, universe)
    -> str | None`; and `acquire(events, pilot, universe, store, fetch, *,
    overrides, states_dir, canonical_dir, run_id, now=...) -> Acquisition`, which
    now takes the universe, for eligibility, and the overrides.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task17-tests.py`:

```python
"""Plan 8: exact replacements for 3 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_events_acquire.py": [
        (
            "from datetime import UTC, datetime\n",
            "from datetime import UTC, date, datetime\n",
        ),
        (
            "from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID\n",
            "from earnings_ingestion.cohort.records import OverrideCitation\n"
            "from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID\n",
        ),
        (
            "    planned_requests,\n",
            "    load_acquisition_overrides,\n"
            "    planned_requests,\n",
        ),
        (
            "from earnings_ingestion.events.layer import exhibit_bodies, write_layer\n"
            "from earnings_ingestion.events.pilot import current_pilot, load_pilot\n",
            "from earnings_ingestion.events.layer import (\n"
            "    REGISTRANTS,\n"
            "    exhibit_bodies,\n"
            "    filings,\n"
            "    write_layer,\n"
            ")\n"
            "from earnings_ingestion.events.pilot import current_pilot, load_pilot\n"
            "from earnings_ingestion.events.records import (\n"
            "    AcquisitionOverride,\n"
            "    AcquisitionOverridesFile,\n"
            ")\n",
        ),
        (
            "\n"
            "REPO = Path(__file__).resolve().parents[3]\n",
            "from earnings_ingestion.sec.filing_index import read_filing_index\n"
            "from earnings_ingestion.sec.urls import filing_index_url\n"
            "\n"
            "REPO = Path(__file__).resolve().parents[3]\n",
        ),
        (
            "def run(frozen, store, fetch, tmp_path, run_id: str = \"acquire-1\"):\n"
            "    _, events, pilot = frozen\n",
            "def run(frozen, store, fetch, tmp_path, run_id: str = \"acquire-1\", overrides=()):\n"
            "    universe, events, pilot = frozen\n",
        ),
        (
            "        store,\n"
            "        fetch,\n",
            "        universe,\n"
            "        store,\n"
            "        fetch,\n"
            "        overrides=AcquisitionOverridesFile(schema_version=1, overrides=overrides),\n",
        ),
        (
            "            store,\n"
            "            refuse,\n",
            "            frozen[0],\n"
            "            store,\n"
            "            refuse,\n"
            "            overrides=AcquisitionOverridesFile(schema_version=1),\n",
        ),
        (
            "            run_id=\"acquire-1\",\n"
            "        )\n",
            "            run_id=\"acquire-1\",\n"
            "        )\n"
            "\n"
            "\n"
            "def document_override(\n"
            "    store, cik: str, accession: str, exhibit: str, event_id: str, **changes\n"
            ") -> AcquisitionOverride:\n"
            "    \"\"\"A ``set_release_document`` citing its filing's saved index page by the\n"
            "    Accepted value's locator, as a reviewer would.\"\"\"\n"
            "    page = SavedResponses(store).get(filing_index_url(cik, accession))\n"
            "    accepted = read_filing_index(page.text.body).accepted\n"
            "    values = {\n"
            "        \"override_id\": f\"release-doc-{event_id.replace(':', '-')}\",\n"
            "        \"kind\": \"set_release_document\",\n"
            "        \"event_id\": event_id,\n"
            "        \"accession\": accession,\n"
            "        \"exhibit\": exhibit,\n"
            "        \"citations\": (\n"
            "            OverrideCitation(\n"
            "                source_id=SEC_SOURCE_ID,\n"
            "                url=page.url,\n"
            "                artifact_sha256=page.artifact.content_sha256,\n"
            "                locator=page.text.find(accepted),\n"
            "            ),\n"
            "        ),\n"
            "        \"rationale\": \"Chosen by review.\",\n"
            "        \"reviewer\": \"Synthetic Reviewer\",\n"
            "        \"recorded_on\": date(2026, 9, 29),\n"
            "    }\n"
            "    return AcquisitionOverride(**{**values, **changes})\n"
            "\n"
            "\n"
            "def accession_of(registrant_cik: str, accepted: str) -> str:\n"
            "    (registrant,) = [r for r in REGISTRANTS if r.cik == registrant_cik]\n"
            "    (filing,) = [f for f, _ in filings(registrant) if f.accepted == accepted]\n"
            "    return filing.accession\n"
            "\n"
            "\n"
            "EASTFIELD_Q1 = \"cik-0009990006:2026-03-31\"\n"
            "LATE = \"2026-07-17 07:30:00\"\n"
            "\"\"\"Eastfield's release for 2026-06-30, accepted after it left on 2026-06-22.\"\"\"\n"
            "\n"
            "\n"
            "def test_an_override_takes_another_filing_s_exhibit_and_marks_a_corpus_error(\n"
            "    frozen, store, tmp_path\n"
            ") -> None:\n"
            "    \"\"\"Eastfield's release for 2026-03-31 failed: its exhibit is an image. A\n"
            "    reviewer names its next release's exhibit, accepted after Eastfield left, so the\n"
            "    record marks a corpus_error and fixes nothing in place; the exhibit is taken\n"
            "    though release-content/1 does not confirm it for the quarter (P8-11).\"\"\"\n"
            "    first = run(frozen, store, Served(), tmp_path)\n"
            "    assert first.states[f\"{EASTFIELD_Q1}:release\"].to_state is F\n"
            "    late = accession_of(\"0009990006\", LATE)\n"
            "    override = document_override(\n"
            "        store, \"0009990006\", late, \"efb-20260717-ex991.htm\", EASTFIELD_Q1\n"
            "    )\n"
            "    corpus = tmp_path / \"corpus\"\n"
            "    shutil.copytree(REPO / FIXTURE_DIR, corpus, ignore=shutil.ignore_patterns(\"raw\"))\n"
            "    served = Served()\n"
            "    second = run(\n"
            "        frozen, store, served, tmp_path, run_id=\"acquire-2\", overrides=(override,)\n"
            "    )\n"
            "    assert second.problems == ()\n"
            "    acquired, parsed = second.transitions\n"
            "    assert (acquired.from_state, acquired.to_state) == (F, A)\n"
            "    assert (parsed.to_state, parsed.accession, parsed.frozen_accession) == (\n"
            "        P,\n"
            "        late,\n"
            "        frozen[1]\n"
            "        .rows[[r.event_id for r in frozen[1].rows].index(EASTFIELD_Q1)]\n"
            "        .release_accession,\n"
            "    )\n"
            "    assert {acquired.override_id, parsed.override_id} == {override.override_id}\n"
            "    assert parsed.corpus_error == acquired.corpus_error\n"
            "    assert \"not_member_at_publication\" in parsed.corpus_error\n"
            "    (attempt,) = parsed.attempts\n"
            "    assert (attempt.choice, attempt.outcome) == (\n"
            "        ExhibitChoice.OVERRIDE,\n"
            "        AttemptOutcome.NOT_CONFIRMED,\n"
            "    )\n"
            "    assert served.requested == [\n"
            "        url for url in served.bodies if url.endswith(\"efb-20260717-ex991.htm\")\n"
            "    ]\n"
            "    universe, events, pilot = frozen\n"
            "    built = build_events(\n"
            "        universe,\n"
            "        SavedResponses(store),\n"
            "        load_overrides(corpus / \"overrides.toml\"),\n"
            "        corpus_id=SYNTHETIC_CORPUS,\n"
            "    )\n"
            "    assert current_events(built, corpus).manifest == events\n"
            "    assert current_pilot(corpus, events, universe).manifest == pilot\n"
            "    third = run(\n"
            "        frozen, store, refuse, tmp_path, run_id=\"acquire-3\", overrides=(override,)\n"
            "    )\n"
            "    assert third.transitions == ()\n"
            "\n"
            "\n"
            "def test_an_override_of_the_frozen_filing_or_a_member_s_filing_marks_no_error(\n"
            "    frozen, store, tmp_path\n"
            ") -> None:\n"
            "    \"\"\"Acme's release for 2025-08-31 is its second exhibit, and its release for\n"
            "    2025-02-28 is named from the 8-K of 2025-03-11, while Acme is a member.\"\"\"\n"
            "    second = document_override(\n"
            "        store,\n"
            "        \"0009990001\",\n"
            "        accession_of(\"0009990001\", \"2025-09-25 16:05:00\"),\n"
            "        \"acme-20250925-ex992.htm\",\n"
            "        \"cik-0009990001:2025-08-31\",\n"
            "    )\n"
            "    earlier = document_override(\n"
            "        store,\n"
            "        \"0009990001\",\n"
            "        accession_of(\"0009990001\", \"2025-03-11 08:00:00\"),\n"
            "        \"acme-20250311-ex991.htm\",\n"
            "        \"cik-0009990001:2025-02-28\",\n"
            "    )\n"
            "    result = run(frozen, store, Served(), tmp_path, overrides=(second, earlier))\n"
            "    for override in (second, earlier):\n"
            "        state = result.states[f\"{override.event_id}:release\"]\n"
            "        assert (state.to_state, state.exhibit, state.override_id) == (\n"
            "            P,\n"
            "            override.exhibit,\n"
            "            override.override_id,\n"
            "        )\n"
            "        assert state.corpus_error is None\n"
            "        assert [a.choice for a in state.attempts] == [ExhibitChoice.OVERRIDE]\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\n"
            "    (\"change\", \"problem\"),\n"
            "    [\n"
            "        ({\"accession\": \"0009990006-26-000099\"}, \"is not saved: run events discover\"),\n"
            "        ({\"exhibit\": \"efb-absent.htm\"}, \"lists no efb-absent.htm\"),\n"
            "        ({\"event_id\": \"cik-0009990002:2024-09-30\"}, \"is not a pilot event\"),\n"
            "        ({\"citations\": (\"wrong\",)}, \"no citation is in\"),\n"
            "    ],\n"
            ")\n"
            "def test_an_override_that_does_not_check_is_a_problem(\n"
            "    frozen, store, tmp_path, change, problem\n"
            ") -> None:\n"
            "    late = accession_of(\"0009990006\", LATE)\n"
            "    override = document_override(\n"
            "        store, \"0009990006\", late, \"efb-20260717-ex991.htm\", EASTFIELD_Q1\n"
            "    )\n"
            "    if change.get(\"citations\") == (\"wrong\",):\n"
            "        wrong = override.citations[0].model_copy(\n"
            "            update={\"url\": \"https://www.sec.gov/Archives/edgar/data/1/x-index.htm\"}\n"
            "        )\n"
            "        change = {\"citations\": (wrong,)}\n"
            "    changed = override.model_copy(update=change)\n"
            "    result = run(frozen, store, Served(), tmp_path, overrides=(changed,))\n"
            "    assert any(problem in found for found in result.problems), result.problems\n"
            "    if \"event_id\" not in change:\n"
            "        assert result.states[f\"{EASTFIELD_Q1}:release\"].override_id is None\n"
            "\n"
            "\n"
            "def test_an_override_of_a_parsed_document_is_a_problem(frozen, store, tmp_path) -> None:\n"
            "    run(frozen, store, Served(), tmp_path)\n"
            "    override = document_override(\n"
            "        store,\n"
            "        \"0009990001\",\n"
            "        accession_of(\"0009990001\", \"2025-09-25 16:05:00\"),\n"
            "        \"acme-20250925-ex991.htm\",\n"
            "        \"cik-0009990001:2025-08-31\",\n"
            "    )\n"
            "    result = run(\n"
            "        frozen, store, refuse, tmp_path, run_id=\"acquire-2\", overrides=(override,)\n"
            "    )\n"
            "    assert result.problems == (\n"
            "        (\n"
            "            f\"{override.override_id}: cik-0009990001:2025-08-31:release is parsed,\"\n"
            "            \" which no override changes\"\n"
            "        ),\n"
            "    )\n"
            "\n"
            "\n"
            "def test_the_overrides_file_loads_or_is_empty(tmp_path) -> None:\n"
            "    assert load_acquisition_overrides(tmp_path / \"absent.toml\").overrides == ()\n"
            "    path = tmp_path / \"acquisition-overrides.toml\"\n"
            "    path.write_text(\n"
            "        'schema_version = 1\\n\\n[[overrides]]\\noverride_id = \"x\"\\n'\n"
            "        'kind = \"set_release_document\"\\nevent_id = \"cik-0009990006:2026-03-31\"\\n'\n"
            "        'accession = \"0009990006-26-000016\"\\nexhibit = \"efb.htm\"\\n'\n"
            "        'rationale = \"r\"\\nreviewer = \"v\"\\nrecorded_on = 2026-09-29\\n\\n'\n"
            "        '[[overrides.citations]]\\nsource_id = \"sec-edgar\"\\nurl = \"u\"\\n',\n"
            "        encoding=\"utf-8\",\n"
            "    )\n"
            "    (loaded,) = load_acquisition_overrides(path).overrides\n"
            "    assert (loaded.override_id, loaded.recorded_on) == (\"x\", date(2026, 9, 29))\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_events_records.py": [
        (
            "\"\"\"Stage 5's records: event rows, findings, overrides, and the manifest's hash.\"\"\"\n",
            "\"\"\"Stage 5's records: event rows, findings, overrides, acquisition overrides, and the\n"
            "manifest's hash.\"\"\"\n",
        ),
        (
            "    EventFindingKind,\n",
            "    AcquisitionOverride,\n"
            "    AcquisitionOverridesFile,\n"
            "    EventFindingKind,\n",
        ),
        (
            "        manifest(rows=(row(), row()))\n",
            "        manifest(rows=(row(), row()))\n"
            "\n"
            "\n"
            "def document_override(**changes: object) -> AcquisitionOverride:\n"
            "    values = {\n"
            "        \"override_id\": \"release-doc-acme-2025-08-31\",\n"
            "        \"kind\": \"set_release_document\",\n"
            "        \"event_id\": \"cik-0009990001:2025-08-31\",\n"
            "        \"accession\": \"0009990001-25-000012\",\n"
            "        \"exhibit\": \"acme-20250925-ex992.htm\",\n"
            "        \"citations\": (\n"
            "            OverrideCitation(\n"
            "                source_id=\"sec-edgar\",\n"
            "                url=\"https://www.sec.gov/Archives/edgar/data/9990001/\"\n"
            "                \"000999000125000012/0009990001-25-000012-index.htm\",\n"
            "            ),\n"
            "        ),\n"
            "        \"rationale\": \"The press release is the second exhibit.\",\n"
            "        \"reviewer\": \"Synthetic Reviewer\",\n"
            "        \"recorded_on\": date(2026, 9, 29),\n"
            "    }\n"
            "    return AcquisitionOverride(**{**values, **changes})\n"
            "\n"
            "\n"
            "def test_an_acquisition_override_names_a_document_and_cites_its_filing() -> None:\n"
            "    assert document_override().exhibit == \"acme-20250925-ex992.htm\"\n"
            "    with pytest.raises(ValidationError, match=\"cites the filing's index page\"):\n"
            "        document_override(citations=())\n"
            "    with pytest.raises(ValidationError, match=\"set_release_document\"):\n"
            "        document_override(kind=\"set_release_filing\")\n"
            "\n"
            "\n"
            "def test_an_acquisition_overrides_file_holds_one_override_per_event() -> None:\n"
            "    one = document_override()\n"
            "    AcquisitionOverridesFile(schema_version=1, overrides=(one,))\n"
            "    with pytest.raises(ValidationError, match=\"override_id repeated\"):\n"
            "        AcquisitionOverridesFile(schema_version=1, overrides=(one, one))\n"
            "    other = document_override(override_id=\"release-doc-acme-again\")\n"
            "    with pytest.raises(ValidationError, match=\"event_id repeated\"):\n"
            "        AcquisitionOverridesFile(schema_version=1, overrides=(one, other))\n",
        ),
    ],
    "tests/contracts/test_data_dictionary.py": [
        (
            "    events.EventManifestDefinition,\n",
            "    events.AcquisitionOverride,\n"
            "    events.AcquisitionOverridesFile,\n"
            "    events.EventManifestDefinition,\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task17-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_acquire.py packages/earnings-ingestion/tests/test_events_records.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL: `3 errors`, in collection:
`cannot import name 'load_acquisition_overrides' from 'earnings_ingestion.events.acquire'`,
`cannot import name 'AcquisitionOverride' from 'earnings_ingestion.events.records'`,
and, in the dictionary's drift test,
`module 'earnings_ingestion.events.records' has no attribute 'AcquisitionOverride'`.

- [x] **Step 3: Write the overrides, and apply them**

> Deviation: after the final review (`55ea811`), an override applied under its ID that now names another exhibit than the document's last acquisition is a problem: an applied override is not edited in place.

Create `/tmp/plan8-task17-source.py`:

```python
"""Plan 8: exact replacements for 4 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/data-dictionary.md": [
        (
            "### `EventManifestDefinition`\n",
            "### `AcquisitionOverride`\n"
            "\n"
            "A reviewer's choice of an event's release document (S §What acquisition can change;\n"
            "plan 8, P8-11). `events acquire` applies it; no manifest hashes it.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `override_id` | ID part | A curated slug |\n"
            "| `kind` | `\"set_release_document\"` | The decision |\n"
            "| `event_id` | ID part | A pilot event |\n"
            "| `accession` | accession | The filing: the event's frozen release filing, or another filing by the issuer, whose index page is saved |\n"
            "| `exhibit` | string | The document's file name on that filing's index page |\n"
            "| `citations` | tuple of `OverrideCitation` | At least one; one cites an SEC artifact in the filing's folder, retrieved from its own URL, at a locator that verifies |\n"
            "| `rationale` | string | Why |\n"
            "| `reviewer` | string | Who decided; the user, never an agent |\n"
            "| `recorded_on` | date | When |\n"
            "\n"
            "### `AcquisitionOverridesFile`\n"
            "\n"
            "`config/corpus/<corpus_id>/acquisition-overrides.toml`.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `schema_version` | `1` | The file's version |\n"
            "| `overrides` | tuple of `AcquisitionOverride` | Unique `override_id`s and `event_id`s |\n"
            "\n"
            "### `EventManifestDefinition`\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py": [
        (
            "- **Problems.** A saved response that cannot be read is a problem naming its repair;\n",
            "- **Overrides.** A ``set_release_document`` in ``acquisition-overrides.toml`` names\n"
            "  an event's document: an exhibit of the frozen release filing, or of another filing\n"
            "  by the issuer whose index page is saved (``events discover --filing`` saves one),\n"
            "  cited as ``build.citations_refused`` checks. Its document, once it canonicalizes,\n"
            "  is the release, and ``release-content/1``'s verdict is recorded without deciding.\n"
            "  An override applies to a document that is ``expected``, ``acquired``,\n"
            "  ``unavailable``, or ``failed``, and each of its transitions names it. When the\n"
            "  other filing's acceptance would change the event's eligibility, each marks a\n"
            "  ``corpus_error`` for the next corpus version, and nothing is fixed in place (P8-11).\n"
            "  An override that does not check is a problem, and its document is not attempted.\n"
            "- **Problems.** A saved response that cannot be read is a problem naming its repair;\n",
        ),
        (
            "from earnings_ingestion.cohort.locators import ArtifactText, CitableArtifact\n"
            "from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID\n"
            "from earnings_ingestion.events.content import confirm\n"
            "from earnings_ingestion.events.exhibits import ExhibitCandidate, exhibit_order\n"
            "from earnings_ingestion.events.freeze import manifest_path\n"
            "from earnings_ingestion.events.records import EventManifest, EventRow, PilotManifest\n",
            "from earnings_ingestion.cohort.config import load_toml\n"
            "from earnings_ingestion.cohort.locators import ArtifactText, CitableArtifact\n"
            "from earnings_ingestion.cohort.records import UniverseManifest\n"
            "from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID\n"
            "from earnings_ingestion.events.acceptance import (\n"
            "    EASTERN,\n"
            "    AcceptanceTimeError,\n"
            "    accepted_instant,\n"
            ")\n"
            "from earnings_ingestion.events.build import citations_refused\n"
            "from earnings_ingestion.events.content import confirm\n"
            "from earnings_ingestion.events.eligibility import IssuerMembership, decide, memberships\n"
            "from earnings_ingestion.events.exhibits import ExhibitCandidate, exhibit_order\n"
            "from earnings_ingestion.events.freeze import manifest_path\n"
            "from earnings_ingestion.events.records import (\n"
            "    AcquisitionOverride,\n"
            "    AcquisitionOverridesFile,\n"
            "    EventManifest,\n"
            "    EventRow,\n"
            "    PilotManifest,\n"
            ")\n",
        ),
        (
            "    MissingReason,\n",
            "    ExhibitChoice,\n"
            "    MissingReason,\n",
        ),
        (
            "from earnings_ingestion.sec.filing_index import read_filing_index\n",
            "from earnings_ingestion.sec.filing_index import FilingIndex, read_filing_index\n",
        ),
        (
            "REPAIR = (\n",
            "OVERRIDDEN = ATTEMPTED | {DocumentState.UNAVAILABLE, DocumentState.FAILED}\n"
            "\"\"\"The states from which an acquisition override moves a document.\"\"\"\n"
            "OVERRIDES_FILE = \"acquisition-overrides.toml\"\n"
            "REPAIR = (\n",
        ),
        (
            "    return f\"{event_id}:release\"\n"
            "\n"
            "\n",
            "    return f\"{event_id}:release\"\n"
            "\n"
            "\n"
            "def load_acquisition_overrides(path: Path) -> AcquisitionOverridesFile:\n"
            "    \"\"\"The corpus's ``acquisition-overrides.toml``, read strictly; empty when\n"
            "    absent.\"\"\"\n"
            "    if not path.exists():\n"
            "        return AcquisitionOverridesFile(schema_version=1)\n"
            "    return load_toml(path, AcquisitionOverridesFile)\n"
            "\n"
            "\n",
        ),
        (
            "def acquire(\n",
            "@dataclass(frozen=True)\n"
            "class _Named:\n"
            "    \"\"\"An override's filing, checked, and what it would do to eligibility.\"\"\"\n"
            "\n"
            "    index: FilingIndex\n"
            "    corpus_error: str | None\n"
            "\n"
            "\n"
            "def corpus_error(\n"
            "    row: EventRow,\n"
            "    instant: datetime,\n"
            "    membership: IssuerMembership,\n"
            "    universe: UniverseManifest,\n"
            ") -> str | None:\n"
            "    \"\"\"Why a release accepted at ``instant`` would change ``row``'s eligibility, for\n"
            "    the next corpus version; ``None`` when eligibility/1 decides it as before.\"\"\"\n"
            "    definition = universe.definition\n"
            "    decision = decide(\n"
            "        row.period_end,\n"
            "        instant,\n"
            "        None,\n"
            "        membership,\n"
            "        start=definition.period_end_start,\n"
            "        stop=definition.period_end_stop,\n"
            "        cutoff=definition.public_information_cutoff,\n"
            "    )\n"
            "    if (decision.status, decision.reason) == (\n"
            "        row.eligibility_status,\n"
            "        row.eligibility_reason,\n"
            "    ):\n"
            "        return None\n"
            "    return (\n"
            "        f\"accepted {instant.astimezone(EASTERN):%Y-%m-%d %H:%M:%S} Eastern, the\"\n"
            "        f\" filing would make the event {decision.status}, {decision.reason}, not\"\n"
            "        f\" {row.eligibility_status}, {row.eligibility_reason}: the next corpus\"\n"
            "        \" version corrects it\"\n"
            "    )\n"
            "\n"
            "\n"
            "def _named(\n"
            "    saved: SavedResponses,\n"
            "    row: EventRow,\n"
            "    override: AcquisitionOverride,\n"
            "    membership: IssuerMembership,\n"
            "    universe: UniverseManifest,\n"
            ") -> _Named:\n"
            "    \"\"\"The override's filing, from its saved index page; raises ``ValueError``,\n"
            "    naming the override, when the page is not saved or does not check.\"\"\"\n"
            "    tag = override.override_id\n"
            "    url = filing_index_url(row.cik, override.accession)\n"
            "    try:\n"
            "        artifact = saved.get(url)\n"
            "        if artifact is None:\n"
            "            raise ValueError(\n"
            "                f\"{tag}: {url} is not saved: run events discover --filing\"\n"
            "                f\" {row.cik} {override.accession}\"\n"
            "            )\n"
            "        index = read_filing_index(artifact.text.body)\n"
            "        instant = accepted_instant(index.accepted)\n"
            "    except (FileNotFoundError, SecDataError, AcceptanceTimeError) as exc:\n"
            "        raise ValueError(f\"{tag}: {url}: {exc}\") from exc\n"
            "    if index.accession != override.accession:\n"
            "        raise ValueError(f\"{tag}: {url} is the index page of {index.accession}\")\n"
            "    if override.exhibit not in {document.filename for document in index.documents}:\n"
            "        raise ValueError(f\"{tag}: {url} lists no {override.exhibit}\")\n"
            "    folder = archive_url(row.cik, override.accession, \"\")\n"
            "    if refused := citations_refused(override, saved, folder):\n"
            "        raise ValueError(\"; \".join(refused))\n"
            "    error = None\n"
            "    if override.accession != row.release_accession:\n"
            "        error = corpus_error(row, instant, membership, universe)\n"
            "    return _Named(index, error)\n"
            "\n"
            "\n"
            "def _apply(\n"
            "    run: _Run,\n"
            "    state: StateTransition,\n"
            "    row: EventRow,\n"
            "    override: AcquisitionOverride,\n"
            "    named: _Named,\n"
            "    saved: SavedResponses,\n"
            "    store: ArtifactStore,\n"
            "    fetch: Fetch,\n"
            "    canonical_dir: Path,\n"
            "    fetched: list[str],\n"
            ") -> StateTransition:\n"
            "    \"\"\"Take the override's document as the release, once it canonicalizes.\"\"\"\n"
            "    (document,) = [d for d in named.index.documents if d.filename == override.exhibit]\n"
            "    url = archive_url(row.cik, override.accession, override.exhibit)\n"
            "    try:\n"
            "        artifact = _exhibit(saved, store, fetch, url, fetched)\n"
            "    except UnexpectedResponse as refused:\n"
            "        raise ValueError(f\"{override.override_id}: {refused}\") from refused\n"
            "    marks = {\"override_id\": override.override_id, \"corpus_error\": named.corpus_error}\n"
            "    acquired = {\n"
            "        \"accession\": override.accession,\n"
            "        \"exhibit\": override.exhibit,\n"
            "        \"artifact_sha256\": artifact.artifact.content_sha256,\n"
            "        \"retrieved_at\": artifact.retrieved_at,\n"
            "    }\n"
            "    if state.to_state is not DocumentState.ACQUIRED:\n"
            "        state = run.record(state, row, DocumentState.ACQUIRED, **acquired, **marks)\n"
            "    tried = {\n"
            "        \"accession\": override.accession,\n"
            "        \"filename\": override.exhibit,\n"
            "        \"exhibit_type\": document.doc_type.strip() or \"(none)\",\n"
            "        \"choice\": ExhibitChoice.OVERRIDE,\n"
            "        \"artifact_sha256\": artifact.artifact.content_sha256,\n"
            "    }\n"
            "    result = canonicalize(\n"
            "        artifact.text.body,\n"
            "        source_document_id=f\"{override.accession}_{override.exhibit}\",\n"
            "        media_type=artifact.text.media_type,\n"
            "    )\n"
            "    if isinstance(result, CanonicalizationFailure):\n"
            "        attempt = ExhibitAttempt(\n"
            "            **tried,\n"
            "            outcome=AttemptOutcome.CANONICALIZATION_FAILED,\n"
            "            failure_reason=result.reason,\n"
            "            detail=result.detail,\n"
            "        )\n"
            "        return run.record(\n"
            "            state,\n"
            "            row,\n"
            "            DocumentState.FAILED,\n"
            "            missing_reason=MissingReason.PARSE_FAILED,\n"
            "            failure_reason=result.reason,\n"
            "            attempts=(attempt,),\n"
            "            **marks,\n"
            "        )\n"
            "    check = confirm(\n"
            "        result, row.period_end, row.reported_fiscal_year, row.reported_fiscal_quarter\n"
            "    )\n"
            "    outcome = (\n"
            "        AttemptOutcome.CONFIRMED if check.confirmed else AttemptOutcome.NOT_CONFIRMED\n"
            "    )\n"
            "    attempt = ExhibitAttempt(**tried, outcome=outcome, detail=check.detail)\n"
            "    _write(canonical_dir, result)\n"
            "    return run.record(\n"
            "        state,\n"
            "        row,\n"
            "        DocumentState.PARSED,\n"
            "        **acquired,\n"
            "        doc_id=result.document.doc_id,\n"
            "        attempts=(attempt,),\n"
            "        **marks,\n"
            "    )\n"
            "\n"
            "\n"
            "def acquire(\n",
        ),
        (
            "    pilot: PilotManifest,\n"
            "    store: ArtifactStore,\n"
            "    fetch: Fetch,\n",
            "    pilot: PilotManifest,\n"
            "    universe: UniverseManifest,\n"
            "    store: ArtifactStore,\n"
            "    fetch: Fetch,\n",
        ),
        (
            "    states_dir: Path,\n"
            "    canonical_dir: Path,\n",
            "    overrides: AcquisitionOverridesFile,\n"
            "    states_dir: Path,\n"
            "    canonical_dir: Path,\n",
        ),
        (
            "    over ``events``.\"\"\"\n",
            "    over ``events``; ``universe`` is the one ``events`` read.\"\"\"\n",
        ),
        (
            "    problems: list[str] = []\n",
            "    selected = {row.event_id for row in pilot.rows}\n"
            "    problems = [\n"
            "        f\"{override.override_id}: {override.event_id} is not a pilot event\"\n"
            "        for override in overrides.overrides\n"
            "        if override.event_id not in selected\n"
            "    ]\n"
            "    named = {override.event_id: override for override in overrides.overrides}\n"
            "    members = memberships(universe)\n",
        ),
        (
            "            if current[key].to_state not in ATTEMPTED:\n",
            "            state = current[key]\n"
            "            override = named.get(row.event_id)\n"
            "            if override is not None:\n"
            "                applied = state.override_id == override.override_id\n"
            "                if applied and state.to_state not in ATTEMPTED:\n"
            "                    continue\n"
            "                if state.to_state not in OVERRIDDEN:\n"
            "                    problems.append(\n"
            "                        f\"{override.override_id}: {key} is {state.to_state}, which no\"\n"
            "                        \" override changes\"\n"
            "                    )\n"
            "                    continue\n"
            "                try:\n"
            "                    found = _named(\n"
            "                        saved, row, override, members[row.issuer_id], universe\n"
            "                    )\n"
            "                    current[key] = _apply(\n"
            "                        run,\n"
            "                        state,\n"
            "                        row,\n"
            "                        override,\n"
            "                        found,\n"
            "                        saved,\n"
            "                        store,\n"
            "                        fetch,\n"
            "                        canonical_dir,\n"
            "                        fetched,\n"
            "                    )\n"
            "                except (_Unusable, ValueError) as problem:\n"
            "                    problems.append(str(problem))\n"
            "                continue\n"
            "            if state.to_state not in ATTEMPTED:\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/build.py": [
        (
            "    EventFinding,\n",
            "    AcquisitionOverride,\n"
            "    EventFinding,\n",
        ),
        (
            "def _citations_refused(\n"
            "    override: EventOverride, saved: SavedResponses, folder: str | None\n",
            "def citations_refused(\n"
            "    override: EventOverride | AcquisitionOverride,\n"
            "    saved: SavedResponses,\n"
            "    folder: str | None,\n",
        ),
        (
            "        refused = _citations_refused(override, saved, folder)\n",
            "        refused = citations_refused(override, saved, folder)\n",
        ),
        (
            "            problems.extend(_citations_refused(override, saved, None))\n",
            "            problems.extend(citations_refused(override, saved, None))\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/records.py": [
        (
            "  ``overrides.toml`` like Stage 4's (P6-18).\n",
            "  ``overrides.toml`` like Stage 4's (P6-18). ``AcquisitionOverride`` names an event's\n"
            "  release document, from ``acquisition-overrides.toml``, which no manifest hashes\n"
            "  (plan 8, P8-11).\n",
        ),
        (
            "class EventManifestDefinition(_Part):\n",
            "class AcquisitionOverride(_Part):\n"
            "    \"\"\"A reviewer's signed choice of an event's release document (S §What acquisition\n"
            "    can change; plan 8, P8-11): an exhibit of the frozen release filing, or of\n"
            "    another filing by the issuer, citing that filing's index page.\"\"\"\n"
            "\n"
            "    override_id: IdPart\n"
            "    kind: Literal[\"set_release_document\"]\n"
            "    event_id: IdPart\n"
            "    accession: Accession\n"
            "    exhibit: NonBlankStr\n"
            "    \"\"\"The document's file name on the filing's index page.\"\"\"\n"
            "    citations: tuple[OverrideCitation, ...]\n"
            "    rationale: NonBlankStr\n"
            "    reviewer: NonBlankStr\n"
            "    recorded_on: date\n"
            "\n"
            "    @model_validator(mode=\"after\")\n"
            "    def _cited(self) -> Self:\n"
            "        if not self.citations:\n"
            "            raise ValueError(\"a set_release_document cites the filing's index page\")\n"
            "        return self\n"
            "\n"
            "\n"
            "class AcquisitionOverridesFile(_Part):\n"
            "    \"\"\"``config/corpus/<corpus_id>/acquisition-overrides.toml``, which no manifest\n"
            "    hashes: acquisition never re-versions a frozen record (P-C7).\"\"\"\n"
            "\n"
            "    schema_version: Literal[1]\n"
            "    overrides: tuple[AcquisitionOverride, ...] = ()\n"
            "\n"
            "    @model_validator(mode=\"after\")\n"
            "    def _distinct(self) -> Self:\n"
            "        for field in (\"override_id\", \"event_id\"):\n"
            "            counts = Counter(getattr(override, field) for override in self.overrides)\n"
            "            if repeated := sorted(name for name, n in counts.items() if n > 1):\n"
            "                raise ValueError(f\"{field} repeated: {repeated}\")\n"
            "        return self\n"
            "\n"
            "\n"
            "class EventManifestDefinition(_Part):\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task17-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_acquire.py packages/earnings-ingestion/tests/test_events_records.py tests/contracts/test_data_dictionary.py -q`

Expected: `146 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan8-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py packages/earnings-ingestion/src/earnings_ingestion/events/build.py packages/earnings-ingestion/src/earnings_ingestion/events/records.py packages/earnings-ingestion/tests/test_events_acquire.py packages/earnings-ingestion/tests/test_events_records.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1508 passed, 24 deselected`; `All checks passed!` and
`267 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py packages/earnings-ingestion/src/earnings_ingestion/events/build.py packages/earnings-ingestion/src/earnings_ingestion/events/records.py packages/earnings-ingestion/tests/test_events_acquire.py packages/earnings-ingestion/tests/test_events_records.py tests/contracts/test_data_dictionary.py
git commit -m "feat(events): set_release_document overrides, with a corpus_error guard"
```

---

### Task 18: The synthetic acquisition replays offline (P-VI, P-C7)

SV 4 and SV 6. `write_fixture` now acquires the synthetic pilot's releases from the
layer's exhibits, through `synthetic.serve`, and commits the run's transitions as
`tests/fixtures/events/acquisition.json`: 80 transitions, with the 27 pilot documents
ending `parsed` 24, `unavailable` 2, and `failed` 1. The exhibits it fetched are saved
in the committed store.

`test_p_vi_replays_the_acquisition_offline` copies the committed store, acquires again
under a socket guard, and finds the same transitions. The one request it sends is the
exhibit SEC never serves. It then writes `partial`, `completed`, and
`completed-no-theme` as later stages would, and finds the frozen records
byte-identical and `djia-pilot/1` still selecting every event.

Three tests change with the store: discovery's and the CLI's helpers skip the
exhibits' URLs, which discovery never fetches, and the quote check skips a page
`walker-1` cannot read, now that the image-only exhibit is saved.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/events/fixture.py` and
  `events/synthetic.py`.
- Test (modify, by exact replacement): `tests/integration/test_event_fixtures.py` and
  `test_corpus_quotes.py`; `packages/earnings-ingestion/tests/test_events_discover.py`;
  and `apps/earnings-pipeline/tests/test_events_cli.py`.
- Regenerate: `tests/fixtures/events/`, which gains `acquisition.json`.

**Interfaces:**

- Consumes: Task 14's `exhibit_bodies`; Tasks 16 and 17's `acquire`.
- Produces:
  - in `events/synthetic.py`: `retrieval_of(url, body, media_type, retrieved_at) ->
    Retrieval` and `serve(bodies, retrieved_at) -> Callable[[str, Collection[str]],
    Fetched]`, which raises `UnexpectedResponse(f"HTTP 404 for {url}")` for any other
    URL;
  - in `events/fixture.py`: `ACQUIRED_AT = datetime(2026, 9, 29, 13, 0, tzinfo=UTC)`,
    `ACQUISITION_RUN = "acquire-synthetic"`, `ACQUISITION = "acquisition.json"`,
    `transitions_json(transitions) -> str`, and `load_transitions(path) ->
    tuple[StateTransition, ...]`.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task18-tests.py`:

```python
"""Plan 8: exact replacements for 4 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/tests/test_events_cli.py": [
        (
            "from earnings_ingestion.events.layer import CORVID, DYNAMO, REPORTS, RETRIEVED, filings\n",
            "from earnings_ingestion.events.layer import (\n"
            "    CORVID,\n"
            "    DYNAMO,\n"
            "    REPORTS,\n"
            "    RETRIEVED,\n"
            "    exhibit_bodies,\n"
            "    filings,\n"
            ")\n",
        ),
        (
            "    root = REPO / FIXTURE_DIR / \"raw\"\n",
            "    \"\"\"The fixture's saved responses, but the exhibits acquisition saved.\"\"\"\n"
            "    root = REPO / FIXTURE_DIR / \"raw\"\n",
        ),
        (
            "    for path in sorted((root / SEC_SOURCE_ID / \"retrievals\").glob(\"*/*.json\")):\n"
            "        record = Retrieval.model_validate_json(path.read_text(encoding=\"utf-8\"))\n",
            "    exhibits = exhibit_bodies()\n"
            "    for path in sorted((root / SEC_SOURCE_ID / \"retrievals\").glob(\"*/*.json\")):\n"
            "        record = Retrieval.model_validate_json(path.read_text(encoding=\"utf-8\"))\n"
            "        if record.request_url in exhibits:\n"
            "            continue\n",
        ),
        (
            "    gone = []\n",
            "    exhibits = exhibit_bodies()\n"
            "    gone = []\n",
        ),
        (
            "        if folder in record.request_url:\n",
            "        if folder in record.request_url and record.request_url not in exhibits:\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_events_discover.py": [
        (
            "    filings,\n",
            "    exhibit_bodies,\n"
            "    filings,\n",
        ),
        (
            "    \"\"\"Every response saved under ``root``, by URL.\"\"\"\n"
            "    store = ArtifactStore(root, repo)\n"
            "    found = {}\n"
            "    for path in sorted((root / SEC_SOURCE_ID / \"retrievals\").glob(\"*/*.json\")):\n"
            "        record = Retrieval.model_validate_json(path.read_text(encoding=\"utf-8\"))\n",
            "    \"\"\"Every response saved under ``root``, by URL, but the exhibits acquisition\n"
            "    saved (plan 8): discovery fetches the rest.\"\"\"\n"
            "    store = ArtifactStore(root, repo)\n"
            "    found = {}\n"
            "    exhibits = exhibit_bodies()\n"
            "    for path in sorted((root / SEC_SOURCE_ID / \"retrievals\").glob(\"*/*.json\")):\n"
            "        record = Retrieval.model_validate_json(path.read_text(encoding=\"utf-8\"))\n"
            "        if record.request_url in exhibits:\n"
            "            continue\n",
        ),
    ],
    "tests/integration/test_corpus_quotes.py": [
        (
            "- **The pages.** HTML is read as walker-1 text, and plain text as written. JSON\n",
            "- **The pages.** HTML is read as walker-1 text, and plain text as written; a page\n"
            "  walker-1 cannot read, such as an image-only exhibit, has no text to quote. JSON\n",
        ),
        (
            "from earnings_ingestion.cohort.locators import ArtifactText\n",
            "from earnings_ingestion.cohort.locators import ArtifactText, LocatorError\n",
        ),
        (
            "        if path.suffix == \".html\":\n"
            "            text = ArtifactText(body, \"text/html\").canonical[0]\n"
            "        else:\n"
            "            text = body.decode(\"utf-8\", errors=\"replace\")\n",
            "        if path.suffix != \".html\":\n"
            "            text = body.decode(\"utf-8\", errors=\"replace\")\n"
            "        else:\n"
            "            try:\n"
            "                text = ArtifactText(body, \"text/html\").canonical[0]\n"
            "            except LocatorError:\n"
            "                continue\n",
        ),
    ],
    "tests/integration/test_event_fixtures.py": [
        (
            "responses to its frozen event manifest and pilot (P-VI; SV12).\n",
            "responses to its frozen event manifest and pilot (P-VI; SV12), and to its\n"
            "acquisition's transitions (plan 8), leaving every frozen record byte-identical\n"
            "(P-C7).\n",
        ),
        (
            "import socket\n",
            "import shutil\n"
            "import socket\n",
        ),
        (
            "from earnings_ingestion.cohort.locators import ArtifactText\n"
            "from earnings_ingestion.cohort.synthetic import build_options\n",
            "from earnings_ingestion.cohort.locators import ArtifactText, LocatorError\n"
            "from earnings_ingestion.cohort.synthetic import build_options\n"
            "from earnings_ingestion.events.acquire import acquire\n",
        ),
        (
            "    COHORT_MANIFEST,\n",
            "    ACQUIRED_AT,\n"
            "    ACQUISITION,\n"
            "    ACQUISITION_RUN,\n"
            "    COHORT_MANIFEST,\n",
        ),
        (
            "    write_fixture,\n",
            "    load_transitions,\n"
            "    write_fixture,\n",
        ),
        (
            "from earnings_ingestion.events.saved import SavedResponses\n",
            "from earnings_ingestion.events.records import AcquisitionOverridesFile\n"
            "from earnings_ingestion.events.saved import SavedResponses\n"
            "from earnings_ingestion.events.state_table import read_runs, write_run\n"
            "from earnings_ingestion.events.states import DocumentState, current_states\n"
            "from earnings_ingestion.fetch.responses import UnexpectedResponse\n",
        ),
        (
            "MANIFESTS = (\"events-v1.json\", \"events-v1.evidence.json\", \"pilot-v1.json\")\n"
            "\n"
            "\n",
            "MANIFESTS = (\"events-v1.json\", \"events-v1.evidence.json\", \"pilot-v1.json\")\n"
            "RECORDS = (*MANIFESTS, ACQUISITION)\n"
            "\n"
            "\n",
        ),
        (
            "    assert set(MANIFESTS) | {\"overrides.toml\"} <= set(committed)\n",
            "    assert set(RECORDS) | {\"overrides.toml\"} <= set(committed)\n",
        ),
        (
            "def test_every_citation_verifies_against_the_committed_store() -> None:\n",
            "@pytest.mark.usefixtures(\"offline\")\n"
            "def test_p_vi_replays_the_acquisition_offline(tmp_path: Path) -> None:\n"
            "    \"\"\"Plan B, item 6: acquisition over a copy of the committed store reproduces the\n"
            "    committed run, sending only the one request SEC never answered; and item 4\n"
            "    (P-C7): after it, a failure included, and after later stages' states, the frozen\n"
            "    records are byte-identical and djia-pilot/1 still selects every event.\"\"\"\n"
            "    universe = load_manifest(REPO / COHORT_MANIFEST)\n"
            "    events = load_event_manifest(ROOT / \"events-v1.json\")\n"
            "    pilot = load_pilot(ROOT / \"pilot-v1.json\", universe)\n"
            "    before = {name: (ROOT / name).read_bytes() for name in MANIFESTS}\n"
            "    shutil.copytree(ROOT / \"raw\", tmp_path / \"raw\")\n"
            "    requested = []\n"
            "\n"
            "    def sec(url: str, types) -> None:\n"
            "        requested.append(url)\n"
            "        raise UnexpectedResponse(f\"HTTP 404 for {url}\")\n"
            "\n"
            "    states = tmp_path / \"states\"\n"
            "    result = acquire(\n"
            "        events,\n"
            "        pilot,\n"
            "        universe,\n"
            "        ArtifactStore(tmp_path / \"raw\", tmp_path),\n"
            "        sec,\n"
            "        overrides=AcquisitionOverridesFile(schema_version=1),\n"
            "        states_dir=states,\n"
            "        canonical_dir=tmp_path / \"canonical\",\n"
            "        run_id=ACQUISITION_RUN,\n"
            "        now=lambda: ACQUIRED_AT,\n"
            "    )\n"
            "    assert result.transitions == load_transitions(ROOT / ACQUISITION)\n"
            "    assert len(requested) == 1\n"
            "    assert requested[0].endswith(\"/dyna-20250422-ex991.htm\")\n"
            "    parsed = [t for t in result.states.values() if t.to_state is DocumentState.PARSED]\n"
            "    later = [\n"
            "        parsed[n].model_copy(\n"
            "            update={\n"
            "                \"run_id\": \"stage-6\",\n"
            "                \"sequence\": n,\n"
            "                \"recorded_at\": ACQUIRED_AT.replace(hour=14),\n"
            "                \"from_state\": DocumentState.PARSED,\n"
            "                \"to_state\": state,\n"
            "                \"attempts\": (),\n"
            "            }\n"
            "        )\n"
            "        for n, state in enumerate(\n"
            "            (\n"
            "                DocumentState.PARTIAL,\n"
            "                DocumentState.COMPLETED,\n"
            "                DocumentState.COMPLETED_NO_THEME,\n"
            "            )\n"
            "        )\n"
            "    ]\n"
            "    write_run(states, later)\n"
            "    current = current_states(read_runs(states), pilot.definition.content_hash)\n"
            "    assert {t.to_state for t in current.values()} == {\n"
            "        DocumentState.PARSED,\n"
            "        DocumentState.FAILED,\n"
            "        DocumentState.UNAVAILABLE,\n"
            "        DocumentState.PARTIAL,\n"
            "        DocumentState.COMPLETED,\n"
            "        DocumentState.COMPLETED_NO_THEME,\n"
            "    }\n"
            "    assert {name: (ROOT / name).read_bytes() for name in MANIFESTS} == before\n"
            "    assert load_pilot(ROOT / \"pilot-v1.json\", universe) == pilot\n"
            "    assert [row.event_id for row in pilot.rows] == [\n"
            "        t.event_id for t in current.values()\n"
            "    ]\n"
            "\n"
            "\n"
            "def test_every_citation_verifies_against_the_committed_store() -> None:\n",
        ),
        (
            "def test_the_committed_records_quote_no_saved_page() -> None:\n",
            "def page_text(path: Path) -> str:\n"
            "    \"\"\"A saved page's walker-1 text; an image-only exhibit has none to quote.\"\"\"\n"
            "    try:\n"
            "        return ArtifactText(path.read_bytes(), \"text/html\").canonical[0]\n"
            "    except LocatorError:\n"
            "        return \"\"\n"
            "\n"
            "\n"
            "def test_the_committed_records_quote_no_saved_page() -> None:\n",
        ),
        (
            "        for name in MANIFESTS\n",
            "        for name in RECORDS\n",
        ),
        (
            "        ArtifactText(path.read_bytes(), \"text/html\").canonical[0]\n"
            "        for path in sorted((ROOT / \"raw\" / \"sec-edgar\").glob(\"*.html\"))\n",
            "        page_text(path) for path in sorted((ROOT / \"raw\" / \"sec-edgar\").glob(\"*.html\"))\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task18-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/tests/test_events_discover.py tests/integration/test_corpus_quotes.py tests/integration/test_event_fixtures.py -q`

Expected: FAIL: `1 error`, collecting `tests/integration/test_event_fixtures.py`,
with `ImportError: cannot import name 'ACQUIRED_AT' from 'earnings_ingestion.events.fixture'`.

- [x] **Step 3: Acquire in the fixture, and serve the exhibits**

Create `/tmp/plan8-task18-source.py`:

```python
"""Plan 8: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/fixture.py": [
        (
            "- ``pilot-v1.json``, the frozen pilot, which is underfilled.\n",
            "- ``pilot-v1.json``, the frozen pilot, which is underfilled;\n"
            "- the pilot's exhibits, which acquisition saves under ``raw/`` from the layer's\n"
            "  ``exhibit_bodies`` (plan 8, P8-10), and ``acquisition.json``, that run's\n"
            "  transitions, which offline replay reproduces.\n",
        ),
        (
            "from collections.abc import Sequence\n",
            "import tempfile\n"
            "from collections.abc import Sequence\n",
        ),
        (
            "from earnings_ingestion.events.build import EventBuild, build_events, load_overrides\n"
            "from earnings_ingestion.events.freeze import freeze_events\n"
            "from earnings_ingestion.events.layer import review, write_layer\n"
            "from earnings_ingestion.events.pilot import FrozenPilot, freeze_pilot, select_pilot\n"
            "from earnings_ingestion.events.records import EventOverride, EventOverridesFile\n"
            "from earnings_ingestion.events.saved import SavedResponses\n",
            "from earnings_ingestion.events.acquire import acquire\n"
            "from earnings_ingestion.events.build import EventBuild, build_events, load_overrides\n"
            "from earnings_ingestion.events.freeze import freeze_events\n"
            "from earnings_ingestion.events.layer import exhibit_bodies, review, write_layer\n"
            "from earnings_ingestion.events.pilot import FrozenPilot, freeze_pilot, select_pilot\n"
            "from earnings_ingestion.events.records import (\n"
            "    AcquisitionOverridesFile,\n"
            "    EventOverride,\n"
            "    EventOverridesFile,\n"
            ")\n"
            "from earnings_ingestion.events.saved import SavedResponses\n"
            "from earnings_ingestion.events.states import StateTransition\n"
            "from earnings_ingestion.events.synthetic import serve\n",
        ),
        (
            "FROZEN_AT = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)\n"
            "\n"
            "\n",
            "FROZEN_AT = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)\n"
            "ACQUIRED_AT = datetime(2026, 9, 29, 13, 0, tzinfo=UTC)\n"
            "ACQUISITION_RUN = \"acquire-synthetic\"\n"
            "ACQUISITION = \"acquisition.json\"\n"
            "\n"
            "\n",
        ),
        (
            "def write_fixture(\n",
            "def transitions_json(transitions: Sequence[StateTransition]) -> str:\n"
            "    \"\"\"A run's transitions as indented JSON with sorted keys.\"\"\"\n"
            "    data = [transition.model_dump(mode=\"json\") for transition in transitions]\n"
            "    return json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + \"\\n\"\n"
            "\n"
            "\n"
            "def load_transitions(path: Path) -> tuple[StateTransition, ...]:\n"
            "    \"\"\"The transitions ``transitions_json`` wrote.\"\"\"\n"
            "    return tuple(\n"
            "        StateTransition.model_validate_json(json.dumps(item))\n"
            "        for item in json.loads(path.read_text(encoding=\"utf-8\"))\n"
            "    )\n"
            "\n"
            "\n"
            "def write_fixture(\n",
        ),
        (
            "    return freeze_pilot(pilot, universe, root, now=FROZEN_AT)\n",
            "    selected = freeze_pilot(pilot, universe, root, now=FROZEN_AT)\n"
            "    with tempfile.TemporaryDirectory() as scratch:\n"
            "        run = acquire(\n"
            "            frozen.manifest,\n"
            "            selected.manifest,\n"
            "            universe,\n"
            "            saved.store,\n"
            "            serve(exhibit_bodies(), ACQUIRED_AT),\n"
            "            overrides=AcquisitionOverridesFile(schema_version=1),\n"
            "            states_dir=Path(scratch) / \"states\",\n"
            "            canonical_dir=Path(scratch) / \"canonical\",\n"
            "            run_id=ACQUISITION_RUN,\n"
            "            now=lambda: ACQUIRED_AT,\n"
            "        )\n"
            "    (root / ACQUISITION).write_text(transitions_json(run.transitions), encoding=\"utf-8\")\n"
            "    return selected\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py": [
        (
            "from collections.abc import Mapping, Sequence\n",
            "from collections.abc import Callable, Collection, Mapping, Sequence\n",
        ),
        (
            "from earnings_ingestion.fetch.store import ArtifactStore\n",
            "from earnings_ingestion.fetch.responses import Fetched, UnexpectedResponse\n"
            "from earnings_ingestion.fetch.store import ArtifactStore\n",
        ),
        (
            "def save(\n"
            "    store: ArtifactStore,\n"
            "    url: str,\n"
            "    body: bytes,\n"
            "    media_type: str,\n"
            "    retrieved_at: datetime,\n"
            ") -> None:\n"
            "    \"\"\"Save ``body`` as a retrieval of ``url`` under the ``sec-edgar`` source.\"\"\"\n"
            "    retrieval = Retrieval(\n",
            "def retrieval_of(\n"
            "    url: str, body: bytes, media_type: str, retrieved_at: datetime\n"
            ") -> Retrieval:\n"
            "    \"\"\"A 200 response's retrieval record, served from ``url`` itself.\"\"\"\n"
            "    return Retrieval(\n",
        ),
        (
            "    store.put(\n",
            "\n"
            "\n"
            "def save(\n"
            "    store: ArtifactStore,\n"
            "    url: str,\n"
            "    body: bytes,\n"
            "    media_type: str,\n"
            "    retrieved_at: datetime,\n"
            ") -> None:\n"
            "    \"\"\"Save ``body`` as a retrieval of ``url`` under the ``sec-edgar`` source.\"\"\"\n"
            "    store.put(\n",
        ),
        (
            "        retrieval,\n",
            "        retrieval_of(url, body, media_type, retrieved_at),\n",
        ),
        (
            "    )\n"
            "\n"
            "\n"
            "class SyntheticStore:\n",
            "    )\n"
            "\n"
            "\n"
            "def serve(\n"
            "    bodies: Mapping[str, tuple[bytes, str]], retrieved_at: datetime\n"
            ") -> Callable[[str, Collection[str]], Fetched]:\n"
            "    \"\"\"SEC as ``bodies``, invented responses by URL, retrieved at ``retrieved_at``:\n"
            "    any other URL is refused as the shared client reports a 404 (plan 8, P8-10).\"\"\"\n"
            "\n"
            "    def fetch(url: str, types: Collection[str]) -> Fetched:\n"
            "        if url not in bodies:\n"
            "            raise UnexpectedResponse(f\"HTTP 404 for {url}\")\n"
            "        body, media_type = bodies[url]\n"
            "        if media_type not in types:\n"
            "            raise UnexpectedResponse(f\"content type {media_type!r} for {url}\")\n"
            "        return Fetched(body, retrieval_of(url, body, media_type, retrieved_at))\n"
            "\n"
            "    return fetch\n"
            "\n"
            "\n"
            "class SyntheticStore:\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task18-source`.

- [x] **Step 4: Regenerate the synthetic corpus**

```bash
uv run --locked --all-packages python tests/integration/regenerate_event_fixtures.py
find tests/fixtures/events -type f | wc -l
python3 -c "import json; [print(n, json.load(open(f'tests/fixtures/events/{n}'))['definition']['content_hash']) for n in ('events-v1.json', 'pilot-v1.json')]"
python3 -c "import json; print(len(json.load(open('tests/fixtures/events/acquisition.json'))))"
```

Expected: `wrote tests/fixtures/events/pilot-v1.json`; `227`; the two hashes of Task
14, unchanged; and `80`. If a hash differs, stop.

- [x] **Step 5: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/tests/test_events_discover.py tests/integration/test_corpus_quotes.py tests/integration/test_event_fixtures.py -q`

Expected: `41 passed`.

- [x] **Step 6: Run the checks**

```bash
python3 /tmp/plan8-escapes.py apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/src/earnings_ingestion/events/fixture.py packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py packages/earnings-ingestion/tests/test_events_discover.py tests/integration/test_corpus_quotes.py tests/integration/test_event_fixtures.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1509 passed, 24 deselected`; `All checks passed!` and
`267 files already formatted`.

- [x] **Step 7: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/tests/test_events_cli.py packages/earnings-ingestion/src/earnings_ingestion/events/fixture.py packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py packages/earnings-ingestion/tests/test_events_discover.py tests/integration/test_corpus_quotes.py tests/integration/test_event_fixtures.py tests/fixtures/events
git commit -m "test(events): the synthetic fixture's acquisition replays offline (P-VI, P-C7)"
```

---

### Task 19: `events acquire`

S §Gate, SV 1, SV 5, and P8-13. `earnings-pipeline events acquire` reads the current
event manifest and the pilot frozen over it, and the acquisition overrides. It prints
their versions and hashes, states what it would send, and opens the shared SEC client
only when it would fetch, capped at the approved `--max-requests`. It prints each
document's state and its request count on every exit, and refuses a store outside
`data/raw` or a runs directory outside `data/runs`. `planned_requests` gains the
override's document, which Task 17's application fetches.

The tests run it on the synthetic corpus with a fake client, never `open_sec_client`:
it reads the current records and states its count, fetches within the count, needs
the count only when it would fetch, stops on a persistent 403 with the rest
`expected`, and refuses a pilot that is not over the current manifest or that
`djia-pilot/1` does not reselect.

**Files:**

- Modify, by exact replacement:
  `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py` and `paths.py`;
  `packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py`.
- Test (modify, by exact replacement): `apps/earnings-pipeline/tests/test_events_cli.py`
  and `test_paths.py`; `packages/earnings-ingestion/tests/test_events_acquire.py`.

**Interfaces:**

- Consumes: Task 9's `_current(layout)` and `current_pilot`; Task 5's
  `raw_store_refusal` and `shown`; Tasks 16 and 17's `acquire`,
  `planned_requests`, `load_acquisition_overrides`, and `OVERRIDES_FILE`;
  `open_sec_client(max_requests=...)`.
- Produces:
  - `earnings-pipeline events acquire [--max-requests N] [--runs-dir DIR]`, with
    `RUNS_DIR = Path("data") / "runs" / "events"` in `events_cli.py`;
  - in `earnings_pipeline.paths`: `RUNS = Path("data") / "runs"` and
    `runs_refusal(repo: Path, runs: Path) -> str | None`;
  - in `events/acquire.py`: `planned_requests(events, pilot, store, states_dir,
    overrides=None) -> tuple[int, int]`, which counts an override's document.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan8-task19-tests.py`:

```python
"""Plan 8: exact replacements for 3 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/tests/test_events_cli.py": [
        (
            "from earnings_ingestion.events.layer import (\n",
            "from earnings_ingestion.events.freeze import serialize\n"
            "from earnings_ingestion.events.layer import (\n",
        ),
        (
            "from earnings_ingestion.events.saved import SavedResponses\n",
            "from earnings_ingestion.events.records import PilotManifest, pilot_content_hash\n"
            "from earnings_ingestion.events.saved import SavedResponses\n"
            "from earnings_ingestion.events.state_table import read_runs\n"
            "from earnings_ingestion.events.states import DocumentState\n",
        ),
        (
            "    assert \"requests sent: 1; a rerun fetches only what is missing\" in result.stdout\n",
            "    assert \"requests sent: 1; a rerun fetches only what is missing\" in result.stdout\n"
            "\n"
            "\n"
            "MISSING = \"dyna-20250422-ex991.htm\"\n"
            "\"\"\"The one exhibit of the synthetic pilot that SEC never served.\"\"\"\n"
            "\n"
            "\n"
            "def forget_exhibits(store: Path) -> list[str]:\n"
            "    \"\"\"Delete the retrieval records of every saved exhibit, so acquisition lacks\n"
            "    them; return their URLs.\"\"\"\n"
            "    exhibits = exhibit_bodies()\n"
            "    gone = []\n"
            "    for path in sorted((store / SEC_SOURCE_ID / \"retrievals\").glob(\"*/*.json\")):\n"
            "        record = Retrieval.model_validate_json(path.read_text(encoding=\"utf-8\"))\n"
            "        if record.request_url in exhibits:\n"
            "            path.unlink()\n"
            "            gone.append(record.request_url)\n"
            "    return gone\n"
            "\n"
            "\n"
            "def acquire_lines(result) -> list[str]:\n"
            "    return result.stdout.splitlines()\n"
            "\n"
            "\n"
            "def test_acquire_reads_the_current_records_and_states_its_count(\n"
            "    repo, moved, monkeypatch\n"
            ") -> None:\n"
            "    \"\"\"Every saved exhibit is read from the store; only the one SEC never served is\n"
            "    requested, through the shared client, within the approved count.\"\"\"\n"
            "    budgets = client(monkeypatch, served())\n"
            "    result = run(repo, \"acquire\", \"--max-requests\", \"1\", store=EVENTS_STORE)\n"
            "    assert result.exit_code == 0, result.output\n"
            "    assert budgets == [1]\n"
            "    lines = acquire_lines(result)\n"
            "    assert lines[:5] == [\n"
            "        \"reads djia-synthetic v1\",\n"
            "        f\"tests/fixtures/events/events-v1.json  {EVENTS_HASH}\",\n"
            "        \"pilot djia-synthetic-pilot v1\",\n"
            "        f\"tests/fixtures/events/pilot-v1.json  {PILOT_HASH}\",\n"
            "        \"at most 1 requests to SEC, through the shared client; 1 first choices\",\n"
            "    ]\n"
            "    assert lines[5] == \"  1  cik-0009990003:2026-03-31:release  parsed\"\n"
            "    assert lines[12] == (\n"
            "        \"  8  cik-0009990003:2025-06-30:release  unavailable, no_confirmed_release\"\n"
            "    )\n"
            "    assert lines[-3:] == [\n"
            "        \"parsed 24, unavailable 2, failed 1\",\n"
            "        \"fetched 0; requests sent: 1\",\n"
            "        lines[-1],\n"
            "    ]\n"
            "    assert lines[-1].startswith(\"data/runs/events/states/acquire-\")\n"
            "    again = run(repo, \"acquire\", store=EVENTS_STORE)\n"
            "    assert again.exit_code == 0, again.output\n"
            "    assert budgets == [1]\n"
            "    assert acquire_lines(again)[4] == \"nothing to fetch; the client stays closed\"\n"
            "    assert acquire_lines(again)[-2:] == [\n"
            "        \"parsed 24, unavailable 2, failed 1\",\n"
            "        \"fetched 0; requests sent: 0\",\n"
            "    ]\n"
            "\n"
            "\n"
            "def test_acquire_fetches_through_the_shared_client_within_its_count(\n"
            "    repo, moved, monkeypatch\n"
            ") -> None:\n"
            "    \"\"\"D5: every exhibit goes through the shared client, whose budget is the approved\n"
            "    count; acquisition has no throttle of its own.\"\"\"\n"
            "    assert len(forget_exhibits(moved)) == 27\n"
            "    budgets = client(monkeypatch, {**served(), **exhibit_bodies()})\n"
            "    result = run(repo, \"acquire\", \"--max-requests\", \"28\", store=EVENTS_STORE)\n"
            "    assert result.exit_code == 0, result.output\n"
            "    assert budgets == [28]\n"
            "    lines = acquire_lines(result)\n"
            "    assert lines[4] == (\n"
            "        \"at most 28 requests to SEC, through the shared client; 27 first choices\"\n"
            "    )\n"
            "    assert lines[-2] == \"fetched 27; requests sent: 28\"\n"
            "\n"
            "\n"
            "def test_acquire_needs_the_approved_count_when_it_would_fetch(\n"
            "    repo, moved, monkeypatch\n"
            ") -> None:\n"
            "    budgets = client(monkeypatch, served())\n"
            "    result = run(repo, \"acquire\", store=EVENTS_STORE)\n"
            "    assert result.exit_code == 1\n"
            "    assert budgets == []\n"
            "    assert result.stderr == (\n"
            "        \"Refused: pass --max-requests, the request count the user approved\\n\"\n"
            "    )\n"
            "    assert \"requests sent\" not in result.stdout\n"
            "\n"
            "\n"
            "def test_acquire_stops_on_a_persistent_403_and_leaves_the_rest_expected(\n"
            "    repo, moved, monkeypatch\n"
            ") -> None:\n"
            "    forget_exhibits(moved)\n"
            "    client(monkeypatch, {**served(), **exhibit_bodies()}, status=403)\n"
            "    result = run(repo, \"acquire\", \"--max-requests\", \"28\", store=EVENTS_STORE)\n"
            "    assert result.exit_code == 1\n"
            "    assert \"Stopped: 403 persisted\" in result.stderr\n"
            "    assert \"requests sent: 2; a rerun attempts what is left\" in result.stdout\n"
            "    (path,) = (repo / \"data\" / \"runs\" / \"events\" / \"states\").glob(\"*.parquet\")\n"
            "    states = {t.to_state for t in read_runs(path.parent)}\n"
            "    assert states == {DocumentState.EXPECTED}\n"
            "\n"
            "\n"
            "def test_acquire_refuses_without_a_pilot_over_the_current_manifest(\n"
            "    repo, moved, monkeypatch\n"
            ") -> None:\n"
            "    budgets = client(monkeypatch, served())\n"
            "    (repo / FIXTURE_DIR / \"pilot-v1.json\").unlink()\n"
            "    result = run(repo, \"acquire\", \"--max-requests\", \"1\", store=EVENTS_STORE)\n"
            "    assert result.exit_code == 1\n"
            "    assert budgets == []\n"
            "    assert \"Refused: no pilot is frozen over events-v1.json: run events select\" in (\n"
            "        result.stderr\n"
            "    )\n"
            "\n"
            "\n"
            "def test_acquire_refuses_a_pilot_djia_pilot_1_does_not_reselect(\n"
            "    repo, moved, monkeypatch\n"
            ") -> None:\n"
            "    \"\"\"F10: a hand-edited pilot whose hash is recomputed is refused at the gate.\"\"\"\n"
            "    budgets = client(monkeypatch, served())\n"
            "    path = repo / FIXTURE_DIR / \"pilot-v1.json\"\n"
            "    pilot = PilotManifest.model_validate_json(path.read_bytes())\n"
            "    one, two, *rest = pilot.rows\n"
            "    rows = (\n"
            "        one.model_copy(update={\"event_id\": two.event_id}),\n"
            "        two.model_copy(update={\"event_id\": one.event_id}),\n"
            "        *rest,\n"
            "    )\n"
            "    swapped = pilot.model_copy(update={\"rows\": rows})\n"
            "    hashed = swapped.definition.model_copy(\n"
            "        update={\"content_hash\": pilot_content_hash(swapped)}\n"
            "    )\n"
            "    path.write_bytes(serialize(swapped.model_copy(update={\"definition\": hashed})))\n"
            "    result = run(repo, \"acquire\", \"--max-requests\", \"1\", store=EVENTS_STORE)\n"
            "    assert result.exit_code == 1\n"
            "    assert budgets == []\n"
            "    assert \"djia-pilot/1 over events-v1.json selects\" in result.stderr\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\n"
            "    (\"option\", \"value\", \"refusal\"),\n"
            "    [\n"
            "        (\"--store\", \"tests/fixtures/events/raw\", \"does not resolve under data/raw\"),\n"
            "        (\"--runs-dir\", \"tests/fixtures/runs\", \"does not resolve under data/runs\"),\n"
            "    ],\n"
            ")\n"
            "def test_acquire_refuses_a_path_git_would_keep(\n"
            "    repo, moved, monkeypatch, option, value, refusal\n"
            ") -> None:\n"
            "    budgets = client(monkeypatch, served())\n"
            "    args = [\"acquire\", \"--max-requests\", \"1\"]\n"
            "    if option == \"--runs-dir\":\n"
            "        args += [option, value]\n"
            "        result = run(repo, *args, store=EVENTS_STORE)\n"
            "    else:\n"
            "        result = run(repo, *args, store=Path(value))\n"
            "    assert result.exit_code == 1\n"
            "    assert budgets == []\n"
            "    assert refusal in result.stderr\n",
        ),
    ],
    "apps/earnings-pipeline/tests/test_paths.py": [
        (
            "\"\"\"Where fetched bytes may be saved, and how paths print (PR #6's review, F19 and\n"
            "F38).\"\"\"\n",
            "\"\"\"Where fetched bytes and run outputs may be written, and how paths print (PR #6's\n"
            "review, F19 and F38; plan 8, P8-13).\"\"\"\n",
        ),
        (
            "from earnings_pipeline.paths import raw_store_refusal, shown\n",
            "from earnings_pipeline.paths import raw_store_refusal, runs_refusal, shown\n",
        ),
        (
            "    )\n",
            "    )\n"
            "\n"
            "\n"
            "def test_run_outputs_stay_under_data_runs(tmp_path) -> None:\n"
            "    assert runs_refusal(tmp_path, Path(\"data/runs/events\")) is None\n"
            "    refusal = runs_refusal(tmp_path, Path(\"data/raw/../runs-elsewhere\"))\n"
            "    assert refusal is not None\n"
            "    assert \"does not resolve under data/runs\" in refusal\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_events_acquire.py": [
        (
            "    result = run(frozen, store, Served(), tmp_path, overrides=(second, earlier))\n",
            "    file = AcquisitionOverridesFile(schema_version=1, overrides=(second, earlier))\n"
            "    assert planned_requests(*frozen[1:], store, tmp_path / \"states\", file) == (27, 27)\n"
            "    result = run(frozen, store, Served(), tmp_path, overrides=(second, earlier))\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task19-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_events_cli.py apps/earnings-pipeline/tests/test_paths.py packages/earnings-ingestion/tests/test_events_acquire.py -q`

Expected: FAIL: `1 error`, collecting `apps/earnings-pipeline/tests/test_paths.py`,
with `ImportError: cannot import name 'runs_refusal' from 'earnings_pipeline.paths'`.

- [x] **Step 3: Write the command**

> Deviation: after the final review (`55ea811`), `events acquire` caps the client at the smaller of `--max-requests` and the count it states, as `discover --filing` does. It holds `.acquire.lock` in `--runs-dir` while it counts and records, so two runs, offline ones included, never fork a history. It refuses an unreadable run file or a held lock with `Refused:` before any client opens, and prints its count on any exit. A redirect loop, 21 requests under httpx's limit, now stops the run at the cap unless the cap leaves room for it, when it is recorded `not_fetched`.

Create `/tmp/plan8-task19-source.py`:

```python
"""Plan 8: exact replacements for 3 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/src/earnings_pipeline/events_cli.py": [
        (
            "and select and freeze its pilot (plan 7, P7-18).\n",
            "select and freeze its pilot (plan 7, P7-18), and acquire the pilot's releases (plan\n"
            "8, P8-13).\n",
        ),
        (
            "\n"
            "Only ``discover`` uses the network, through the shared SEC client. It states its\n",
            "    earnings-pipeline events acquire --max-requests N    # the shared SEC client\n"
            "\n"
            "Only ``discover`` uses the network, through the shared SEC client. It states its\n",
        ),
        (
            "``discover`` refuses a ``--store`` that does not resolve under ``data/raw``, before\n"
            "any client opens, and every command prints a path outside the repository in full\n",
            "``acquire`` reads the event manifest the build reproduces and the pilot frozen over\n"
            "it, which ``load_pilot`` checks and reselects, and refuses otherwise. It states what\n"
            "it would send before it opens the client: at most N requests, one per exhibit not\n"
            "saved, and how many are first choices. With nothing to fetch the client stays\n"
            "closed; otherwise ``--max-requests``, the count the user approved, is required and is\n"
            "the client's cap. It prints each pilot document's state, and its request count on\n"
            "every exit. It writes its run under ``--runs-dir``, and exits 1 on a problem.\n"
            "\n"
            "``discover`` and ``acquire`` refuse a ``--store`` that does not resolve under\n"
            "``data/raw``, and ``acquire`` a ``--runs-dir`` outside ``data/runs``, before any\n"
            "client opens; every command prints a path outside the repository in full\n",
        ),
        (
            "from dataclasses import dataclass\n",
            "from collections import Counter\n"
            "from dataclasses import dataclass\n",
        ),
        (
            "from earnings_ingestion.events.build import (\n",
            "from earnings_ingestion.events.acquire import (\n"
            "    OVERRIDES_FILE,\n"
            "    acquire,\n"
            "    load_acquisition_overrides,\n"
            "    planned_requests,\n"
            ")\n"
            "from earnings_ingestion.events.build import (\n",
        ),
        (
            "from earnings_ingestion.events.pilot import freeze_pilot, select_pilot\n",
            "from earnings_ingestion.events.pilot import current_pilot, freeze_pilot, select_pilot\n",
        ),
        (
            "from earnings_pipeline.paths import raw_store_refusal, shown\n",
            "from earnings_pipeline.paths import raw_store_refusal, runs_refusal, shown\n",
        ),
        (
            "FETCHING = frozenset({\"discover\"})\n",
            "FETCHING = frozenset({\"discover\", \"acquire\"})\n",
        ),
        (
            "full disk and a saved body that is gone.\"\"\"\n"
            "\n"
            "\n",
            "full disk and a saved body that is gone.\"\"\"\n"
            "RUNS_DIR = Path(\"data\") / \"runs\" / \"events\"\n"
            "\n"
            "\n",
        ),
        (
            "    )\n"
            "    typer.echo(f\"{shown(frozen.path, layout.repo)}  {definition.content_hash}\")\n",
            "    )\n"
            "    typer.echo(f\"{shown(frozen.path, layout.repo)}  {definition.content_hash}\")\n"
            "\n"
            "\n"
            "def _closed(url: str, types) -> None:\n"
            "    raise AccessStop(f\"{url} was to be fetched, though nothing was counted to fetch\")\n"
            "\n"
            "\n"
            "@events.command(\"acquire\")\n"
            "def acquire_command(\n"
            "    context: typer.Context,\n"
            "    max_requests: Annotated[\n"
            "        int | None,\n"
            "        typer.Option(help=\"The request count approved at the gate; the client's cap.\"),\n"
            "    ] = None,\n"
            "    runs_dir: Annotated[\n"
            "        Path, typer.Option(help=\"Where the state table and canonical documents go.\")\n"
            "    ] = RUNS_DIR,\n"
            ") -> None:\n"
            "    \"\"\"Acquire the current pilot's release documents through the shared SEC client,\n"
            "    and record each one's processing state.\"\"\"\n"
            "    layout: Layout = context.obj\n"
            "    if refusal := runs_refusal(layout.repo, runs_dir):\n"
            "        _fail(refusal)\n"
            "    current, universe = _current(layout)\n"
            "    try:\n"
            "        pilot = current_pilot(layout.corpus(), current.manifest, universe)\n"
            "        overrides = load_acquisition_overrides(layout.corpus() / OVERRIDES_FILE)\n"
            "    except ValueError as error:\n"
            "        _fail(f\"Refused: {error}\")\n"
            "    definition = pilot.manifest.definition\n"
            "    typer.echo(f\"pilot {definition.pilot_id} v{definition.pilot_version}\")\n"
            "    typer.echo(f\"{shown(pilot.path, layout.repo)}  {definition.content_hash}\")\n"
            "    runs = layout.repo / runs_dir\n"
            "    arguments = (current.manifest, pilot.manifest, universe, layout.store())\n"
            "    options = {\n"
            "        \"overrides\": overrides,\n"
            "        \"states_dir\": runs / \"states\",\n"
            "        \"canonical_dir\": runs / \"canonical\",\n"
            "        \"run_id\": f\"acquire-{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}\",\n"
            "    }\n"
            "    first, most = planned_requests(\n"
            "        current.manifest, pilot.manifest, layout.store(), runs / \"states\", overrides\n"
            "    )\n"
            "    if most == 0:\n"
            "        typer.echo(\"nothing to fetch; the client stays closed\")\n"
            "    else:\n"
            "        typer.echo(\n"
            "            f\"at most {most} requests to SEC, through the shared client;\"\n"
            "            f\" {first} first choices\"\n"
            "        )\n"
            "        if max_requests is None:\n"
            "            _fail(\"Refused: pass --max-requests, the request count the user approved\")\n"
            "    sent = 0\n"
            "    try:\n"
            "        if most == 0:\n"
            "            result = acquire(*arguments, _closed, **options)\n"
            "        else:\n"
            "            with open_sec_client(max_requests=max_requests) as sec:\n"
            "                try:\n"
            "                    result = acquire(*arguments, sec.fetch, **options)\n"
            "                finally:\n"
            "                    sent = sec.throttle.count\n"
            "    except STOPS as error:\n"
            "        typer.echo(f\"requests sent: {sent}; a rerun attempts what is left\")\n"
            "        _fail(f\"Stopped: {error}\")\n"
            "    except KeyboardInterrupt:\n"
            "        typer.echo(f\"requests sent: {sent}; a rerun attempts what is left\")\n"
            "        raise\n"
            "    for row in pilot.manifest.rows:\n"
            "        state = result.states[f\"{row.event_id}:release\"]\n"
            "        reasons = [str(r) for r in (state.missing_reason, state.failure_reason) if r]\n"
            "        said = \", \".join([str(state.to_state), *reasons])\n"
            "        typer.echo(f\"{row.selection_order:>3}  {state.document_id}  {said}\")\n"
            "        if state.corpus_error is not None:\n"
            "            typer.echo(f\"     corpus_error: {state.corpus_error}\")\n"
            "    counts = Counter(state.to_state for state in result.states.values())\n"
            "    typer.echo(\", \".join(f\"{state} {n}\" for state, n in counts.most_common()))\n"
            "    typer.echo(f\"fetched {len(result.fetched)}; requests sent: {sent}\")\n"
            "    if result.path is not None:\n"
            "        typer.echo(shown(result.path, layout.repo))\n"
            "    for problem in result.problems:\n"
            "        typer.echo(f\"problem: {problem}\", err=True)\n"
            "    if result.problems:\n"
            "        raise typer.Exit(1)\n",
        ),
    ],
    "apps/earnings-pipeline/src/earnings_pipeline/paths.py": [
        (
            "- **What a command prints.** A path under the repository prints relative to it, and\n",
            "- **Where run outputs go.** ``events acquire`` refuses a runs directory that does not\n"
            "  resolve under ``<repo>/data/runs``: the canonical documents it writes hold\n"
            "  filings' text, which is local-only and never committed (plan 8, P8-13).\n"
            "- **What a command prints.** A path under the repository prints relative to it, and\n",
        ),
        (
            "RAW = Path(\"data\") / \"raw\"\n"
            "\n"
            "\n",
            "RAW = Path(\"data\") / \"raw\"\n"
            "RUNS = Path(\"data\") / \"runs\"\n"
            "\n"
            "\n",
        ),
        (
            "def shown(path: Path, repo: Path) -> str:\n",
            "def runs_refusal(repo: Path, runs: Path) -> str | None:\n"
            "    \"\"\"Why run outputs may not be written under ``repo / runs``, or ``None``.\"\"\"\n"
            "    if (repo / runs).resolve().is_relative_to((repo / RUNS).resolve()):\n"
            "        return None\n"
            "    return (\n"
            "        f\"Refused: {runs} does not resolve under {RUNS}, where canonical documents,\"\n"
            "        \" which hold filings' text, are kept out of Git\"\n"
            "    )\n"
            "\n"
            "\n"
            "def shown(path: Path, repo: Path) -> str:\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py": [
        (
            "def planned_requests(\n",
            "def _pending(\n"
            "    state: StateTransition | None, override: AcquisitionOverride | None\n"
            ") -> str | None:\n"
            "    \"\"\"What a run does with a document: ``override`` applies its override,\n"
            "    ``attempt`` tries its exhibits, ``refused`` reports an override of a document\n"
            "    no override moves, and ``None`` leaves it.\"\"\"\n"
            "    current = DocumentState.EXPECTED if state is None else state.to_state\n"
            "    if override is not None:\n"
            "        applied = state is not None and state.override_id == override.override_id\n"
            "        if applied and current not in ATTEMPTED:\n"
            "            return None\n"
            "        return \"override\" if current in OVERRIDDEN else \"refused\"\n"
            "    return \"attempt\" if current in ATTEMPTED else None\n"
            "\n"
            "\n"
            "def planned_requests(\n",
        ),
        (
            ") -> tuple[int, int]:\n"
            "    \"\"\"What a run would fetch: the first choices not saved, and every candidate not\n"
            "    saved, over the documents it would attempt. The second is the most it can send.\"\"\"\n",
            "    overrides: AcquisitionOverridesFile | None = None,\n"
            ") -> tuple[int, int]:\n"
            "    \"\"\"What a run would fetch: the first choices not saved, and every candidate not\n"
            "    saved, over the documents it would attempt, an override's document counting as\n"
            "    both. The second is the most it can send.\"\"\"\n",
        ),
        (
            "    first = most = 0\n"
            "    for pilot_row in pilot.rows:\n"
            "        state = current.get(document_id(pilot_row.event_id))\n"
            "        if state is not None and state.to_state not in ATTEMPTED:\n"
            "            continue\n"
            "        row = rows[pilot_row.event_id]\n",
            "    named = {} if overrides is None else {o.event_id: o for o in overrides.overrides}\n"
            "    first = most = 0\n"
            "    for pilot_row in pilot.rows:\n"
            "        row = rows[pilot_row.event_id]\n"
            "        override = named.get(row.event_id)\n"
            "        pending = _pending(current.get(document_id(row.event_id)), override)\n"
            "        if pending == \"override\":\n"
            "            url = archive_url(row.cik, override.accession, override.exhibit)\n"
            "            if url not in saved:\n"
            "                first, most = first + 1, most + 1\n"
            "            continue\n"
            "        if pending != \"attempt\":\n"
            "            continue\n",
        ),
        (
            "            if override is not None:\n"
            "                applied = state.override_id == override.override_id\n"
            "                if applied and state.to_state not in ATTEMPTED:\n"
            "                    continue\n"
            "                if state.to_state not in OVERRIDDEN:\n"
            "                    problems.append(\n"
            "                        f\"{override.override_id}: {key} is {state.to_state}, which no\"\n"
            "                        \" override changes\"\n"
            "                    )\n"
            "                    continue\n",
            "            pending = _pending(state, override)\n"
            "            if pending == \"refused\":\n"
            "                problems.append(\n"
            "                    f\"{override.override_id}: {key} is {state.to_state}, which no\"\n"
            "                    \" override changes\"\n"
            "                )\n"
            "                continue\n"
            "            if pending == \"override\":\n",
        ),
        (
            "            if state.to_state not in ATTEMPTED:\n",
            "            if pending != \"attempt\":\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task19-source`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_events_cli.py apps/earnings-pipeline/tests/test_paths.py packages/earnings-ingestion/tests/test_events_acquire.py -q`

Expected: `48 passed`.

- [x] **Step 5: Read the real count offline**

`events acquire` with no `--max-requests` states its count and refuses before it opens
the client, so it sends nothing:

```bash
uv run --locked earnings-pipeline events acquire; echo "exit $?"
```

Expected:

```text
reads djia-2024q3-2026q2 v1
config/corpus/djia-2024q3-2026q2/events-v1.json  2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7
pilot djia-2024q3-2026q2-pilot v1
config/corpus/djia-2024q3-2026q2/pilot-v1.json  3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926
at most 56 requests to SEC, through the shared client; 40 first choices
Refused: pass --max-requests, the request count the user approved
exit 1
```

- [x] **Step 6: Run the checks**

```bash
python3 /tmp/plan8-escapes.py apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/src/earnings_pipeline/paths.py apps/earnings-pipeline/tests/test_events_cli.py apps/earnings-pipeline/tests/test_paths.py packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py packages/earnings-ingestion/tests/test_events_acquire.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1518 passed, 24 deselected`; `All checks passed!` and
`267 files already formatted`.

- [x] **Step 7: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/src/earnings_pipeline/paths.py apps/earnings-pipeline/tests/test_events_cli.py apps/earnings-pipeline/tests/test_paths.py packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py packages/earnings-ingestion/tests/test_events_acquire.py
git commit -m "feat(pipeline): events acquire, gated on the current pilot (P8-13)"
```

---

### Task 20: The live acquisition (gate)

S §Gates (plan B), gate 1, and SV 6. The replay test is committed first, so that the
live run's states are checked offline the moment they exist. Then the user approves
the stated count, and `events acquire` runs through the shared SEC client.

Every step before Step 6 is offline. Steps 6 and 7 are the gate: nothing in Step 7
runs until the user has said yes in chat.

**Files:**

- Replace: `tests/integration/test_event_store_v1.py`.
- Local, never committed: `data/raw/events/sec-edgar/`, which gains the exhibits, and
  `data/runs/events/`, which the run creates.

**Interfaces:**

- Consumes: `events acquire` (Task 19); `acquire`, `load_acquisition_overrides`,
  `read_runs`, and `current_states`.
- Produces: `test_offline_replay_reproduces_the_live_acquisition`, which skips until
  an acquisition run is saved; and the live run's states.

- [x] **Step 1: Write the replay test**

The count test, from Task 16, now skips once an acquisition run is saved, since the
run saves the exhibits it counts. The replay test then takes over.

Replace `tests/integration/test_event_store_v1.py` with:

```python
"""The real corpus's frozen records against Stage 5's local store, which only this
machine holds: the test skips without it, so each gate runs it and reads "passed".

``planned_requests`` is what ``events acquire`` states before it sends anything, and
the live gate's count (plan 8, P8-12): the pilot's 40 release filings list 56
``EX-99*`` exhibits, and R1.2's order puts one first in each. That count holds until
the first acquisition saves its exhibits, so the test then skips. Once the live run
is saved, offline replay over the store reproduces each document's state (the Stage 5
spec, §Verification (plan B), item 6).
"""

from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.acquire import (
    OVERRIDES_FILE,
    acquire,
    load_acquisition_overrides,
    planned_requests,
)
from earnings_ingestion.events.freeze import load_event_manifest
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import StateTransition, current_states
from earnings_ingestion.fetch.responses import UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore

REPO = Path(__file__).resolve().parents[2]
STORE = REPO / "data" / "raw" / "events"
CORPUS = REPO / "config" / "corpus" / "djia-2024q3-2026q2"
UNIVERSE = (
    REPO / "config" / "universe" / "djia" / "manifests" / "djia-2024q3-2026q2-v1.json"
)
STATES = REPO / "data" / "runs" / "events" / "states"


def test_the_first_acquisition_sends_40_to_56_requests(tmp_path) -> None:
    if not (STORE / "sec-edgar").is_dir():
        pytest.skip("data/raw/events is not saved here: each gate runs this test")
    if any(STATES.glob("*.parquet")):
        pytest.skip(
            "the first acquisition has run: docs/verification/djia-events.md"
            " records its count"
        )
    events = load_event_manifest(CORPUS / "events-v1.json")
    pilot = load_pilot(CORPUS / "pilot-v1.json", load_manifest(UNIVERSE))
    store = ArtifactStore(STORE, REPO)
    assert planned_requests(events, pilot, store, tmp_path / "states") == (40, 56)


def facts(state: StateTransition) -> tuple:
    return (
        state.to_state,
        state.missing_reason,
        state.failure_reason,
        state.accession,
        state.exhibit,
        state.artifact_sha256,
        state.doc_id,
        state.override_id,
    )


def test_offline_replay_reproduces_the_live_acquisition(tmp_path) -> None:
    """Each pilot document's state, replayed from the saved store with every
    exhibit never saved refused as SEC refused it, is the state the live runs left."""
    if not any(STATES.glob("*.parquet")):
        pytest.skip("no acquisition run is saved here: the live gate runs this test")
    universe = load_manifest(UNIVERSE)
    events = load_event_manifest(CORPUS / "events-v1.json")
    pilot = load_pilot(CORPUS / "pilot-v1.json", universe)
    live = current_states(read_runs(STATES), pilot.definition.content_hash)

    def unsaved(url: str, types) -> None:
        raise UnexpectedResponse(f"{url} is not saved")

    replay = acquire(
        events,
        pilot,
        universe,
        ArtifactStore(STORE, REPO),
        unsaved,
        overrides=load_acquisition_overrides(CORPUS / OVERRIDES_FILE),
        states_dir=tmp_path / "states",
        canonical_dir=tmp_path / "canonical",
        run_id="replay",
    )
    assert replay.fetched == ()
    assert {key: facts(state) for key, state in replay.states.items()} == {
        key: facts(state) for key, state in live.items()
    }
```

Extract it with `python3 /tmp/plan8-extract.py tests/integration/test_event_store_v1.py 2`.

- [x] **Step 2: Run it**

Run: `uv run --locked --all-packages pytest tests/integration/test_event_store_v1.py -q -rs`

Expected: `1 passed, 1 skipped`, and the skip reads
`no acquisition run is saved here: the live gate runs this test`.

- [x] **Step 3: Run the checks**

```bash
python3 /tmp/plan8-escapes.py tests/integration/test_event_store_v1.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1518 passed, 1 skipped, 24 deselected`;
`All checks passed!` and `267 files already formatted`.

- [x] **Step 4: Commit**

```bash
git log --oneline -3
git add tests/integration/test_event_store_v1.py
git commit -m "test(events): offline replay reproduces the live acquisition's states"
```

- [x] **Step 5: Check everything the gate relies on, offline**

```bash
uv run --locked --all-packages pytest tests/integration/test_corpus_quotes.py tests/integration/test_event_store_v1.py -q
uv run --locked earnings-pipeline events acquire; echo "exit $?"
ls data/runs/events 2>&1
[ -n "$(printenv EDGAR_IDENTITY)" ] && echo "EDGAR_IDENTITY set" || echo "EDGAR_IDENTITY unset"
```

Expected:

- `5 passed, 1 skipped`: the quote check passes on the real corpus, and the count
  test pins `(40, 56)`;
- Task 19, Step 5's output: events v1 and pilot v1 with their hashes, then
  `at most 56 requests to SEC, through the shared client; 40 first choices`, the
  refusal, and `exit 1`;
- `ls: data/runs/events: No such file or directory`: no run has been written;
- `EDGAR_IDENTITY set`.

If any differs, stop and report it: the gate's count is not what the user will be
asked to approve.

- [x] **Step 6 (gate): Ask the user to approve the count**

Put this to the user in chat, and wait for a clear yes:

> `earnings-pipeline events acquire --max-requests 56` will send at most 56 requests
> to SEC through the shared client, as `EDGAR_IDENTITY`, at 2 requests a second: one
> for each `EX-99*` exhibit of the pilot's 40 release filings that it tries, and 40
> of them are first choices. It fetches exhibits only, saves them under
> `data/raw/events/`, and writes the processing states and canonical documents under
> `data/runs/events/`, all gitignored. It changes no committed file. May I run it?

A different count, or a no, stops the task.

- [x] **Step 7: Run the acquisition**

> Deviation: predictions only; every check matched. The run exited 0 and sent 40 requests of the approved 56, fetching 40: 39 documents `parsed` and 1 `unavailable`, `no_confirmed_release`. That one was not JPMorgan's, 3M's, or Verizon's, the likeliest predicted, but Disney's for 2026-03-28, #26: its release states the period but opens as a letter to shareholders. No stop, retry, or rerun was needed.

```bash
uv run --locked earnings-pipeline events acquire --max-requests 56 > /tmp/plan8-acquire-1.txt 2>&1; echo "exit $?"
cat /tmp/plan8-acquire-1.txt
```

Expected, checks:

- the first five lines of Step 5's output, down to
  `at most 56 requests to SEC, through the shared client; 40 first choices`;
- one line for each of the 40 pilot documents, in selection order:
  `<order>  <event_id>:release  <state>[, <reasons>]`;
- the counts by state, which sum to 40;
- `fetched <f>; requests sent: <s>`, with `s` at most 56 and `f` at most `s`;
- the run's file, `data/runs/events/states/acquire-<timestamp>.parquet`;
- `exit 0`, or `exit 1` with `problem:` lines, which Task 21 takes to the user.

Expected, a prediction: most or all of the 40 documents `parsed`, and `s` between 40
and 56. Each document whose first choice is confirmed sends one request, and each
first choice that is not confirmed adds one for each exhibit tried after it.
`release-content/1` reads a period as `release-id/1` does, so if any release goes
`unavailable` with `no_confirmed_release`, the likeliest are the issuers whose
periods that reader already read poorly: JPMorgan, 3M, and Verizon
(`docs/verification/djia-events.md`, Limitations). A full date after "ended" still
confirms theirs.

If the run stops, it prints `Stopped:` and
`requests sent: N; a rerun attempts what is left`, and every document not attempted
stays `expected`. Report both to the user. A persistent 403 or SEC's block page is
never retried with another identity (A §404). A rerun is a gate of its own:
`events acquire` with no count states what is left (Step 5's command), the user
approves that count, and the rerun takes it as `--max-requests`, with its output in
`/tmp/plan8-acquire-2.txt`, and so on.

- [x] **Step 8: Replay the run offline, and check the frozen records**

`/tmp/plan8-review.py` lists each pilot document that is not `parsed`, with every
exhibit it tried and each outcome, then the counts by state. It reads the state
table, and sends nothing:

Create `/tmp/plan8-review.py`:

```python
"""Print each pilot document that is not parsed, with every exhibit it tried, from a
state table or a fixture's transitions; then the counts by state. It sends nothing.

usage: uv run --locked --all-packages python /tmp/plan8-review.py
           <pilot-v<N>.json> <states directory, or transitions .json>
"""

import json
import sys
from collections import Counter
from pathlib import Path

from earnings_ingestion.events.fixture import load_transitions
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import current_states

pilot_path, source = Path(sys.argv[1]), Path(sys.argv[2])
pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
transitions = load_transitions(source) if source.suffix == ".json" else read_runs(source)
states = current_states(transitions, pilot["definition"]["content_hash"])
for row in pilot["rows"]:
    document = f"{row['event_id']}:release"
    state = states.get(document)
    if state is None:
        print(f"{row['selection_order']:>3}  {document}  no transition")
        continue
    if state.to_state == "parsed":
        continue
    reasons = [str(r) for r in (state.missing_reason, state.failure_reason) if r]
    print(f"{row['selection_order']:>3}  {document}  {', '.join([str(state.to_state), *reasons])}")
    print(f"     release filing {state.frozen_accession}")
    for attempt in state.attempts:
        detail = f": {attempt.detail}" if attempt.detail else ""
        print(
            f"     {attempt.exhibit_type} {attempt.filename} ({attempt.choice}),"
            f" {attempt.outcome}{detail}"
        )
counts = Counter(str(state.to_state) for state in states.values())
print(", ".join(f"{state} {n}" for state, n in counts.most_common()))
```

Extract it with `python3 /tmp/plan8-extract.py /tmp/plan8-review.py`.

On the synthetic corpus's committed run, it printed:

```text
  6  cik-0009990006:2026-03-31:release  failed, parse_failed, no_native_text
     release filing 0009990006-26-000016
     EX-99.1 efb-20260417-ex991.htm (named), canonicalization_failed: no text is left after N1
  8  cik-0009990003:2025-06-30:release  unavailable, no_confirmed_release
     release filing 0009990003-25-000005
     EX-99.01 crvd-20250730-ex9901.htm (named), not_confirmed: its opening announces no results
 24  cik-0009990005:2025-03-28:release  unavailable, not_found
     release filing 0009990005-25-000008
     EX-99.1 dyna-20250422-ex991.htm (named), not_fetched: HTTP 404 for https://www.sec.gov/Archives/edgar/data/9990005/000999000525000008/dyna-20250422-ex991.htm
parsed 24, unavailable 2, failed 1
```

That was
`uv run --locked --all-packages python /tmp/plan8-review.py tests/fixtures/events/pilot-v1.json tests/fixtures/events/acquisition.json`.

Then run:

```bash
uv run --locked --all-packages pytest tests/integration/test_event_store_v1.py tests/integration/test_corpus_quotes.py -q -rs
uv run --locked --all-packages python /tmp/plan8-review.py config/corpus/djia-2024q3-2026q2/pilot-v1.json data/runs/events/states
uv run --locked earnings-pipeline events build > /tmp/plan8-build.txt 2>&1; echo "exit $?"
tail -1 /tmp/plan8-build.txt
git status --short
```

Expected on the real run, checks:

- `5 passed, 1 skipped`: `test_offline_replay_reproduces_the_live_acquisition`
  passes, the count test skips with
  `the first acquisition has run: docs/verification/djia-events.md records its count`,
  and the quote check passes, now over the saved exhibits too;
- the review's last line equals the run's counts line;
- `exit 0`, and `263 events, 239 eligible, content 2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7`:
  the build still reproduces events v1 (P-C7, P8-12);
- `git status --short` prints nothing: acquisition wrote only under `data/`.

If the replay test fails, stop: the saved store does not reproduce the states, and
the record cannot claim SV 6.

Save the output of Steps 7 and 8 for the record (Task 22).

---

### Task 21: The review, overrides, and reruns (gate)

S §What acquisition can change, and P8-11. Every document that is not `parsed` goes to
the user. The user either accepts its state, which is then a recorded outcome, or
names its release document in a `set_release_document` override. A selected event
stays selected either way (P-C7), and no frozen record changes.

If Task 20's run left every document `parsed`, with no `problem:` line, this task
writes nothing: note that in the record, and go to Task 22.

**Files:**

- Create, only if the review writes an override:
  `config/corpus/djia-2024q3-2026q2/acquisition-overrides.toml`.
- Local, never committed: whatever `events discover --filing` and the overrides'
  acquisition save under `data/`.

**Interfaces:**

- Consumes: `/tmp/plan8-review.py`'s listing; `AcquisitionOverride`'s fields, which
  `docs/data-dictionary.md` lists; `earnings-pipeline cohort cite`, which prints a
  citation's locator.
- Produces: the reviewed acquisition overrides, and the documents' final states.

- [x] **Step 1 (gate): Take each problem, and each document not parsed, to the user**

> Deviation: no `problem:` line arose. The one document not parsed, Disney's, went to the user, who chose an override naming its only `EX-99.1`, `fy2026_q2xprxex991.htm`, and gave its rationale and signature. No rerun, `events discover --filing`, or store repair was needed.

A `problem:` line comes first. One that ends "repair the store by hand" names a saved
response that cannot be read: acquisition never fetches it again (P8-2). Show it to
the user, who decides whether to repair the store as `docs/verification/djia-events.md`
will describe ("Repairing the store", Task 22) and rerun, at a gate of its own. Any
other `problem:` line is a stop: report it, and change nothing.

Then put each document from `/tmp/plan8-review.py` to the user, with its lines, one at
a time or in one batch:

| What the review shows | The decision |
| --- | --- |
| `unavailable, no_confirmed_release`: every exhibit canonicalized, and `release-content/1` confirmed none | Whether one of the exhibits tried is the release after all, which an override names; or whether the filing holds no release, and the state stands |
| `unavailable, not_found`: no exhibit could be fetched | Whether another filing by the issuer holds the release, which an override names. If the attempt's detail shows a status other than 404, such as a server error, the failure may be transient: a rerun alone never retries an `unavailable` document, but an override naming the same exhibit fetches it again, at a stated count of 1. Or the state stands |
| `failed, parse_failed, <reason>`: an exhibit failed to canonicalize | Whether another exhibit is the release, which an override names; or the state stands, as a parser outcome (R1.4) |

The user may read the saved exhibits. They are local, and none of their wording enters
a committed file.

**To see a filing's documents,** for an exhibit of the frozen filing or of another:

```text
uv run --locked --all-packages python /tmp/plan8-folder.py data/raw/events [GATE: the CIK, 10 digits] [GATE: the accession]
```

It lists what the store saved from the filing's folder, each with its SHA-256, and
the index page's Accepted value and every document it lists. It sends nothing:

Create `/tmp/plan8-folder.py`:

```python
"""List what a store saved from one filing's folder, each with its SHA-256; then the
index page's Accepted value, as the page writes it, and every document it lists. It
sends nothing.

usage: uv run --locked --all-packages python /tmp/plan8-folder.py
           <store> <CIK> <accession>
"""

import sys
from pathlib import Path

from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import filing_index_url

store, cik, accession = sys.argv[1:]
root = Path(store, "sec-edgar")
index_url = filing_index_url(cik, accession)
folder = index_url.rsplit("/", 1)[0] + "/"
found = set()
for path in root.glob("retrievals/*/*.json"):
    record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
    if record.request_url.startswith(folder):
        found.add((record.request_url, record.sha256))
for url, sha256 in sorted(found):
    print(sha256, url)
    if url == index_url:
        (body,) = root.glob(f"{sha256}.*")
        index = read_filing_index(body.read_bytes())
        print(f"  Accepted {index.accepted}")
        for document in index.documents:
            print(
                f"  {document.sequence}  {document.doc_type}  {document.filename}"
                f"  {document.description}"
            )
print(f"{len(found)} saved in {folder}")
```

Extract it with `python3 /tmp/plan8-extract.py /tmp/plan8-folder.py`.

On the synthetic corpus, for Acme's filing of 2025-09-25, it printed:

```text
ce2d87349936de216d5b2cb199b1b8cdd745407c0fe1edd7a77df5e053ad038b https://www.sec.gov/Archives/edgar/data/9990001/000999000125000012/0009990001-25-000012-index.htm
  Accepted 2025-09-25 16:05:00
  1  8-K  acme-8k-20250925.htm  8-K
  2  EX-99.1  acme-20250925-ex991.htm  Supplemental information
  3  EX-99.2  acme-20250925-ex992.htm  Press release
  None    0009990001-25-000012.txt  Complete submission text file
1fe294187724c46e8eb1db180ab11065f198a4b515c58baa685aa8664975304e https://www.sec.gov/Archives/edgar/data/9990001/000999000125000012/acme-20250925-ex991.htm
abcaef2db0dd06e459d68f9af0d893afed131601c1998c4ae4e669d8e5601206 https://www.sec.gov/Archives/edgar/data/9990001/000999000125000012/acme-20250925-ex992.htm
1b79bced23938d91b1527c6162aaf3d790f8ba81ea3db4fb936c0efc413712a1 https://www.sec.gov/Archives/edgar/data/9990001/000999000125000012/acme-8k-20250925.htm
4 saved in https://www.sec.gov/Archives/edgar/data/9990001/000999000125000012/
```

That was
`uv run --locked --all-packages python /tmp/plan8-folder.py tests/fixtures/events/raw 0009990001 0009990001-25-000012`.
If another filing's index page is not saved, the user approves at most 2 requests
for `uv run --locked earnings-pipeline events discover --filing [GATE: the CIK] [GATE: the accession] --max-requests 2`
first.

- [x] **Step 2 (gate): Write the overrides the user decided**

**To cite the filing,** cite its index page at its Accepted value, which Step 1's
listing shows:

```text
uv run --locked --all-packages earnings-pipeline cohort --store data/raw/events cite sec-edgar [GATE: the index page's sha256] --find "[GATE: its Accepted value]"
```

On the synthetic corpus, for Acme's filing above, it printed:

```text
canonical_sha256 = "09e05c4ab6ac8822af806cc5e88e36288f970a3ee7f9c1b733a77d80e5353072"
span = [89, 108]
cited_sha256 = "5b0f9bb93d7d3775ea22123dc61d9760b9929f9cc7a01b68160cc94afba6f9f4"
```

That was `cohort --store tests/fixtures/events/raw cite sec-edgar ce2d8734… --find "2025-09-25 16:05:00"`.
`cite` also prints the cited text on stderr, which is never committed.

**Write `config/corpus/djia-2024q3-2026q2/acquisition-overrides.toml`.** Its fields are
listed in `docs/data-dictionary.md`, under `AcquisitionOverride`. It begins:

```toml
# Reviewed acquisition decisions for the real pilot (plan 8, P8-11; the Stage 5 spec,
# §What acquisition can change). No manifest hashes this file. Each records its
# rationale, reviewer, and date; the reviewer is the user.
schema_version = 1
```

One entry for each override:

```toml
[[overrides]]
override_id = "[GATE: a short slug, such as release-doc-vz-2026-03-31]"
kind = "set_release_document"
event_id = "[GATE: the event_id]"
accession = "[GATE: the accession of the filing that holds the release]"
exhibit = "[GATE: the exhibit's file name, as the index page lists it]"
rationale = "[GATE: the user's reason, in the user's words]"
reviewer = "[GATE: the user's name, as they sign it]"
recorded_on = [GATE: today's date]

[[overrides.citations]]
source_id = "sec-edgar"
url = "[GATE: the index page's URL]"
artifact_sha256 = "[GATE: its sha256]"

[overrides.citations.locator]
kind = "text_span"
canonicalization_version = "walker-1"
canonical_sha256 = "[GATE: cite's canonical_sha256]"
start = [GATE: the first number of cite's span]
end = [GATE: the second number of cite's span]
cited_sha256 = "[GATE: cite's cited_sha256]"
```

- **The signature.** The implementer never writes `reviewer`. The user gives the name
  in chat, for each override or once for all.
- **The rationale** is the user's words, never an exhibit's. Step 3's quote check
  refuses a 40-character window copied from a saved page.
- **One per event.** The file holds at most one override for each event (P8-11).

- [x] **Step 3: Check the overrides offline**

```bash
grep -n 'GATE:' config/corpus/djia-2024q3-2026q2/acquisition-overrides.toml
uv run --locked --all-packages pytest tests/integration/test_corpus_quotes.py -q
uv run --locked earnings-pipeline events acquire; echo "exit $?"
```

Expected, checks: nothing from `grep`; `4 passed`; and `events acquire` prints the
records it read, then `at most <n> requests to SEC, through the shared client; <n>
first choices`, with `n` the number of overrides whose exhibit is not saved, or
`nothing to fetch; the client stays closed` when every such exhibit is saved, which
then acquires offline. Without a count it refuses when `n` is above 0, with `exit 1`.
A `problem:` line names an override that does not check: fix it and repeat.

- [x] **Step 4 (gate): Acquire the overrides' documents**

> Deviation: `n` was 0, since the exhibit was already saved, so no count went to the user. The override's acquisition ran with the client closed, sent 0 requests, and parsed Disney's document with no `corpus_error`, leaving the pilot 40 `parsed`.

When `n` is above 0, put the count to the user, as Task 20, Step 6 did, and wait for
a clear yes. Then:

```bash
uv run --locked earnings-pipeline events acquire --max-requests [GATE: n] > /tmp/plan8-acquire-overrides.txt 2>&1; echo "exit $?"
cat /tmp/plan8-acquire-overrides.txt
uv run --locked --all-packages python /tmp/plan8-review.py config/corpus/djia-2024q3-2026q2/pilot-v1.json data/runs/events/states
```

Expected, checks: each overridden document now `parsed`, and each of its transitions
names its override; no `corpus_error` line, since no v1 release lies near a
membership change (S §What acquisition can change); and `exit 0`. A `corpus_error`
line is reported to the user and recorded, and nothing is fixed in place: the next
corpus version corrects it.

- [x] **Step 5: Replay, and commit the overrides**

```bash
uv run --locked --all-packages pytest tests/integration/test_event_store_v1.py tests/integration/test_corpus_quotes.py -q
uv run --locked earnings-pipeline events build > /tmp/plan8-build.txt 2>&1; echo "exit $?"; tail -1 /tmp/plan8-build.txt
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
```

Expected, checks: `5 passed, 1 skipped`, the replay now reproducing the overrides'
documents too; `exit 0` and events v1's content line, unchanged; and
`1518 passed, 1 skipped, 24 deselected`.

```bash
git log --oneline -3
git add config/corpus/djia-2024q3-2026q2/acquisition-overrides.toml
git commit -m "feat(corpus): the reviewed acquisition overrides for the real pilot"
```

Commit only if the review wrote the file.

---

### Task 22: The verification record, and the current state

S §Gates (plan B), gate 2, and S §Rollout's refresh of the current state.

- **The record.** `docs/verification/djia-events.md` gains plan B's sections: what
  was verified, what landed before any acquisition, the acquisition, its requests,
  the store's manual repair, and plan B's limitations. Its numbers come from Tasks 20
  and 21, so the template holds `[GATE: …]` slots. Fill each from the named output,
  and never leave one.
- **The current state.** `CLAUDE.md` and `README.md` describe Stage 5 as complete.

**Files:**

- Modify, by exact replacement: `docs/verification/djia-events.md`, `CLAUDE.md`, and
  `README.md`.
- Regenerate, only if Task 21 ran `events discover --filing`:
  `docs/verification/edgar-acceptance-time.md`, with
  `uv run --locked --all-packages python tests/integration/regenerate_acceptance_time_record.py`.

**Interfaces:**

- Consumes: everything this plan built, and the outputs of Tasks 20 and 21.
- Produces: documentation only. The test counts stay at Task 20's.

- [x] **Step 1: Apply the record and the current state**

Create `/tmp/plan8-task21-source.py`:

```python
"""Plan 8: exact replacements for 3 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "CLAUDE.md": [
        (
            "This repo is documentation-first: its working code is the Stage 1 investigation harness in `expirements/parser-fidelity/`, the Stage 2 contracts in `packages/earnings-core`, Stage 3's canonicalizer and browser diagnostic path in `packages/earnings-ingestion`, Stage 4's point-in-time DJIA cohort and shared SEC client there too, and Stage 5's event discovery, eligibility, and pilot selection (its plan A) beside them; `earnings-themes` is still a `hello()` scaffold, and the rest is instructions.\n",
            "This repo is documentation-first: its working code is the Stage 1 investigation harness in `expirements/parser-fidelity/`, the Stage 2 contracts in `packages/earnings-core`, Stage 3's canonicalizer and browser diagnostic path in `packages/earnings-ingestion`, Stage 4's point-in-time DJIA cohort and shared SEC client there too, and Stage 5's event discovery, eligibility, pilot selection, and acquisition beside them; `earnings-themes` is still a `hello()` scaffold, and the rest is instructions.\n",
        ),
        (
            "| `specs/event-discovery-eligibility-and-acquisition.md` | **Stage 5's stage spec**, approved 2026-09-27. It splits the stage into two plans (EV1). Plan A (plan 7) discovered the cohort's events and froze the event manifest and the pilot. Plan B, acquisition and processing states, is not written yet, so the spec stays live. |\n",
            "| `specs/event-discovery-eligibility-and-acquisition.md` | **Stage 5's stage spec**, approved 2026-09-27, and complete. It split the stage into two plans (EV1): plan A (plan 7) discovered the cohort's events and froze the event manifest and the pilot, and plan B (plan 8) acquired the pilot's releases and records their processing states. Its §Commands amendment (plan 8, P8-4) makes the build decide which frozen version is current. |\n",
        ),
        (
            "## Current state: Stages 1–4 and Stage 5's plan A complete; `earnings-themes` still a scaffold\n",
            "## Current state: Stages 1–5 complete; `earnings-themes` still a scaffold\n",
        ),
        (
            "Stage 5's plan A (event discovery, eligibility, and the freezes; plan 7, `specs/event-discovery-eligibility-and-acquisition.md`) is done, and plan B, acquisition, is next:\n"
            "\n"
            "- `packages/earnings-ingestion/src/earnings_ingestion/events/` finds each cohort issuer's quarterly slots and release filings in SEC's filing metadata (`release-id/1`), and judges each event's eligibility by point-in-time membership at its EDGAR acceptance time (`eligibility/1`). It freezes the event manifest with its evidence record, and then the pilot (`djia-pilot/1`). `earnings-pipeline events` holds its commands. Only `events discover` sends requests, through the shared SEC client, and it fetches no exhibit.\n",
            "Stage 5 (event discovery, eligibility, and acquisition; plans 7 and 8, `specs/event-discovery-eligibility-and-acquisition.md`) is done:\n"
            "\n"
            "- `packages/earnings-ingestion/src/earnings_ingestion/events/` finds each cohort issuer's quarterly slots and release filings in SEC's filing metadata (`release-id/1`), and judges each event's eligibility by point-in-time membership at its EDGAR acceptance time (`eligibility/1`). It freezes the event manifest with its evidence record, and then the pilot (`djia-pilot/1`). `earnings-pipeline events` holds its commands. Only `events discover` and `events acquire` send requests, both through the shared SEC client, and discovery fetches no exhibit.\n",
        ),
        (
            "\n"
            "`earnings-themes` still contains only a `hello()` stub, as do the top-level modules of `earnings-ingestion` and `apps/earnings-pipeline`; the application's commands are `earnings-pipeline browser setup` and the `earnings-pipeline cohort` and `events` groups. `data/` is gitignored and holds only local, uncommitted material: fetched pages under `data/raw/`, the cohort's saved evidence under `data/raw/cohort/`, Stage 5's saved SEC responses under `data/raw/events/`, and under `data/runs/` Stage 1's run outputs and live lock, the user's rendered copies, the browser capture store, and the cohort's live-verification records; `prompts/` and `codebooks/` are empty directories. `origin` is set to https://github.com/lowmason/earnings-themes, which is **public** — treat anything committed here as publicly visible.\n",
            "- The build decides which frozen version is current: `events select` and `events acquire` read the event manifest whose content hash the rebuild reproduces, and the pilot frozen over it (`current_events`, `current_pilot`; plan 8, P8-4). `load_pilot` also reselects: `djia-pilot/1` over the pilot's event manifest must reproduce its hash (P8-3).\n"
            "- `events acquire` (plan 8) tries each pilot release filing's `EX-99*` exhibits in R1.2's order (`events/exhibits.py`), confirms one by `release-content/1` (`events/content.py`), and records R1.4's processing states (`events/states.py`, `state_table.py`) as one Parquet file per run under `data/runs/events/states/`, with each confirmed exhibit's canonical document under `data/runs/events/canonical/`. A `set_release_document` override goes in `acquisition-overrides.toml` beside the frozen records, which no manifest hashes. `tests/fixtures/events/acquisition.json` is the synthetic acquisition, which replays offline. A saved response that cannot be read is never fetched again, and its repair is manual (`docs/verification/djia-events.md`, \"Repairing the store\").\n"
            "\n"
            "`earnings-themes` still contains only a `hello()` stub, as do the top-level modules of `earnings-ingestion` and `apps/earnings-pipeline`; the application's commands are `earnings-pipeline browser setup` and the `earnings-pipeline cohort` and `events` groups. `data/` is gitignored and holds only local, uncommitted material: fetched pages under `data/raw/`, the cohort's saved evidence under `data/raw/cohort/`, Stage 5's saved SEC responses, the pilot's exhibits among them, under `data/raw/events/`, and under `data/runs/` Stage 1's run outputs and live lock, the user's rendered copies, the browser capture store, the cohort's live-verification records, and Stage 5's processing states and canonical documents under `data/runs/events/`; `prompts/` and `codebooks/` are empty directories. `origin` is set to https://github.com/lowmason/earnings-themes, which is **public** — treat anything committed here as publicly visible.\n",
        ),
    ],
    "README.md": [
        (
            "> **Project status (2026-09-27): Stages 1 to 4 complete, and the\n"
            "> first of Stage 5's two plans.** The `uv` workspace, package boundaries,\n"
            "> specifications, and staged roadmap exist. `earnings-core` holds the shared\n"
            "> evidence contracts, and `earnings-ingestion` canonicalizes releases, rebuilds the\n"
            "> point-in-time DJIA cohort, and discovers and freezes its earnings events and pilot,\n"
            "> each with offline tests. `earnings-themes` still contains a placeholder API; there\n"
            "> is no theme extraction, approved theme codebook, or published dataset yet.\n",
            "> **Project status ([GATE: today's date, YYYY-MM-DD]): Stages 1 to 5 complete.**\n"
            "> The `uv` workspace, package boundaries, specifications, and staged roadmap exist.\n"
            "> `earnings-core` holds the shared evidence contracts, and `earnings-ingestion`\n"
            "> canonicalizes releases, rebuilds the point-in-time DJIA cohort, discovers and\n"
            "> freezes its earnings events and pilot, and acquires the pilot's releases, each with\n"
            "> offline tests. `earnings-themes` still contains a placeholder API; there is no theme\n"
            "> extraction, approved theme codebook, or published dataset yet.\n",
        ),
        (
            "stages. Stages 1 to 4 are complete, and so is the first of Stage 5's two plans.\n",
            "stages. Stages 1 to 5 are complete.\n",
        ),
        (
            "**Stage 5: event discovery, eligibility, and acquisition** is half done. Its first\n",
            "**Stage 5: event discovery, eligibility, and acquisition** is complete. Its first\n",
        ),
        (
            "acquired. The [verification record](docs/verification/djia-events.md) has the\n"
            "details. The next milestone is Stage 5's second plan, which acquires the pilot's\n"
            "releases.\n",
            "acquired. Its second plan then acquires the pilot's releases from EDGAR through the\n"
            "shared client, chooses and confirms each release exhibit, and records each document's\n"
            "processing state. The [verification record](docs/verification/djia-events.md) has\n"
            "the details. The roadmap resumes with Stage 6: the pilot codebook, split, and\n"
            "gold-set protocol.\n",
        ),
    ],
    "docs/verification/djia-events.md": [
        (
            "Plan B, which acquires the pilot's releases, adds its own sections.\n",
            "Plan B, which acquired the pilot's releases, has its own sections, from \"Plan B:\n"
            "acquisition and processing states\" on.\n",
        ),
        (
            "  package client.\n",
            "  package client.\n"
            "\n"
            "## Plan B: acquisition and processing states\n"
            "\n"
            "Plan 8 (`specs/plans/8-event-discovery-eligibility-and-acquisition-plan-b.md`) built\n"
            "plan B of the Stage 5 spec: the processing states, R1.2's exhibit choice,\n"
            "`release-content/1`, acquisition through the shared SEC client, and\n"
            "`earnings-pipeline events acquire`. It then acquired the pilot's releases.\n"
            "\n"
            "### What was verified (plan B)\n"
            "\n"
            "| Item (S §Verification, plan B) | Evidence |\n"
            "| --- | --- |\n"
            "| 1. `events acquire` refuses without a frozen pilot whose chain checks | `test_acquire_refuses_without_a_pilot_over_the_current_manifest`; `test_acquire_refuses_a_pilot_djia_pilot_1_does_not_reselect`; `test_a_pilot_not_frozen_over_the_manifest_is_refused`; `test_loading_selects_again`; `test_the_build_decides_which_version_is_current` |\n"
            "| 2. Exhibit choice and confirmation: `EX-99`, `EX-99.1`, and `EX-99.01`; a narrative-only release; a first choice that fails and a next exhibit that confirms; the AMC-like overview, which fails | `test_each_numbering_is_named`; `test_plan_b_s_exhibit_numbering`; `test_the_narrative_release_has_no_table`; `test_named_exhibits_come_first_by_sequence`; `test_an_overview_that_announces_nothing_is_not_confirmed`; `test_each_case_comes_to_its_state` |\n"
            "| 3. Every R1.4 state from fixtures, each expected but absent document with its `missing_reason` | `test_every_state_is_represented_from_fixtures`; `test_a_state_carries_its_own_details`; `test_only_the_transitions_r1_4_allows`; `test_a_history_must_chain` |\n"
            "| 4. P-C7: the frozen records unchanged, and every selected event still selected, after acquisition, a failed parse, and later stages' states | `test_acquisition_changes_no_frozen_record_and_the_build_still_decides`; `test_p_vi_replays_the_acquisition_offline`; after the live run, the rebuild below |\n"
            "| 5. Only the shared client, with no throttle of its own; a persistent 403 stops the run and leaves the rest `expected` | `test_stage_5_opens_no_client_of_its_own`; `test_stage_5_has_no_client_or_throttle_of_its_own`; `test_acquire_fetches_through_the_shared_client_within_its_count`; `test_a_persistent_403_stops_the_run_and_leaves_the_rest_expected`; `test_acquire_stops_on_a_persistent_403_and_leaves_the_rest_expected` |\n"
            "| 6. Offline replay reproduces the states | `test_p_vi_replays_the_acquisition_offline`, on the synthetic store; `test_offline_replay_reproduces_the_live_acquisition`, on the real store |\n"
            "| 7. The suites | The default suite, [GATE: Task 22, Step 3's count]; the harness suite, 280 passed; Ruff; `uv.lock` unchanged |\n"
            "\n"
            "### Before any acquisition\n"
            "\n"
            "The deferred items from PR #6's review that named plan B landed first (plan 8,\n"
            "P8-2): a relative lock directory is refused (F29); a redirected response is refused\n"
            "when fetched and when read (F13); a primary document with no Item line reads as\n"
            "unread; an index page must agree with its submissions row (F12); every fetching\n"
            "command refuses a store outside `data/raw` (F19, F38); every stop prints its request\n"
            "count, and `cohort fetch-sec` and `verify-live` take an approved count (F31, F35);\n"
            "two frozen versions of one content are refused (F22); and\n"
            "`tests/integration/test_corpus_quotes.py` checks that no committed record quotes a\n"
            "saved page (F20). Two were the user's design choices:\n"
            "\n"
            "- **The build decides which frozen version is current** (F4). `events select` and\n"
            "  `events acquire` read the event manifest whose content hash the rebuild\n"
            "  reproduces, and the pilot frozen over it. The spec's §Commands records the rule.\n"
            "- **Loading a pilot selects it again** (F10). `djia-pilot/1` over the pilot's event\n"
            "  manifest and universe must reproduce its content hash.\n"
            "\n"
            "Recovering a saved response that is present but unusable (P2.1, P2.2) stays\n"
            "deferred; \"Repairing the store\" below gives the manual repair.\n"
            "\n"
            "### The acquisition\n"
            "\n"
            "- **What it read.** events v1, content hash\n"
            "  `2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7`, and pilot v1,\n"
            "  `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926`, which\n"
            "  `events acquire` printed before it sent anything.\n"
            "- **The runs.** [GATE: each run's file under `data/runs/events/states/`, and what it\n"
            "  did: the first acquisition, a rerun after a stop, or an override's acquisition]\n"
            "- **The states.** [GATE: the last run's counts line, such as \"parsed 40\"], of the\n"
            "  pilot's 40 release documents. Their canonical documents are under\n"
            "  `data/runs/events/canonical/`, named by `doc_id`.\n"
            "- **Exhibit choice.** [GATE: how many documents the first exhibit in R1.2's order\n"
            "  confirmed, and each that needed a later exhibit, with the exhibit that confirmed]\n"
            "- **Documents not parsed.** [GATE: each, from `/tmp/plan8-review.py`: its event, its\n"
            "  state and reasons, the exhibits tried with each outcome, and the review's decision;\n"
            "  or \"None.\"]\n"
            "- **Overrides.** [GATE: each `set_release_document` in\n"
            "  `config/corpus/djia-2024q3-2026q2/acquisition-overrides.toml`: its ID, its event,\n"
            "  its exhibit, its rationale's gist, and whether it marked a `corpus_error`; or\n"
            "  \"None: the review wrote no `acquisition-overrides.toml`.\"]\n"
            "- **Replay.** `test_offline_replay_reproduces_the_live_acquisition` acquired again\n"
            "  from the saved store, refusing every exhibit that was never saved, as SEC refused\n"
            "  it, and reproduced each document's state (SV 6).\n"
            "- **P-C7.** After acquisition, `events build` still reproduced events v1's content\n"
            "  hash, and no frozen record changed: acquisition writes only under `data/`.\n"
            "\n"
            "### The requests (plan B)\n"
            "\n"
            "| Step | Client | Requests |\n"
            "| --- | --- | --- |\n"
            "| Plan 8, Task 20, `events acquire --max-requests 56` | SEC | [GATE: requests sent and fetched, under the approved cap of 56, of the stated 56 and 40 first choices] |\n"
            "| Plan 8, Task 20, reruns | SEC | [GATE: each rerun's approved cap and requests sent, or \"none\"] |\n"
            "| Plan 8, Task 21, `events discover --filing` | SEC | [GATE: each filing and its requests, or \"none\"] |\n"
            "| Plan 8, Task 21, the overrides' acquisition | SEC | [GATE: its approved cap and requests sent, or \"none\"] |\n"
            "\n"
            "No `-m live` test ran. No model was called, and no billable service was used.\n"
            "\n"
            "### Repairing the store\n"
            "\n"
            "Acquisition never fetches a response it has saved, and the store is append-only. So a\n"
            "saved exhibit whose bytes are gone or changed, or that a reader refuses, stops its\n"
            "document with a `problem:` line that ends \"repair the store by hand\". Until the\n"
            "deferred recovery lands (P2.1, P2.2), the repair moves files out of the store, and\n"
            "never deletes one:\n"
            "\n"
            "1. Find the response's retrieval records by its URL:\n"
            "   `grep -l '\"request_url\":\"<URL>\"' data/raw/events/sec-edgar/retrievals/*/*.json`.\n"
            "2. Move each record's directory, `retrievals/<sha256>/`, and the artifact it names,\n"
            "   `<sha256>.<extension>`, from `data/raw/events/sec-edgar/` to a dated directory\n"
            "   under `data/quarantine/`, outside the store.\n"
            "3. Rerun `events acquire`. Its stated count now includes that URL, and the rerun is\n"
            "   a gate of its own.\n"
            "\n"
            "[GATE: \"No repair was needed in plan 8's runs.\", or each repair made]\n"
            "\n"
            "### Limitations (plan B)\n"
            "\n"
            "- **`release-content/1` is fixed.** Its vocabulary came from Stage 1's 168 saved\n"
            "  exhibits, where it rejects the six that are not releases and misses six of the 162\n"
            "  releases, whose openings announce nothing the pattern reads. A release it misses\n"
            "  is `unavailable` with `no_confirmed_release` until a reviewed override names it,\n"
            "  and the rule changes only as `release-content/2`. [GATE: how many real releases it\n"
            "  missed, or \"It missed none of the pilot's releases.\"]\n"
            "- **Exhibits only.** Acquisition saves exhibits, never an index page or a primary\n"
            "  document, so the event build reads what it read before.\n"
            "- **The first count is pinned once.** `test_the_first_acquisition_sends_40_to_56_requests`\n"
            "  pins the gate's count, and skips once an acquisition run is saved. This record keeps\n"
            "  the count.\n"
            "- **`restricted` is represented by fixtures only.** SEC documents are public, so no\n"
            "  real document is `restricted`. `partial`, `completed`, and `completed-no-theme`\n"
            "  wait for later stages.\n",
        ),
    ],
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task21-source`.

- [x] **Step 2 (gate): Fill the slots, and have the user read the record**

> Deviation: after the final review, the user chose (`a06e2d0`) to quote the override's signed rationale exactly, where the record had paraphrased it, and to give check 7 the suite count after the review's fixes, 1535 passed and 1 skipped.

Fill every `[GATE: …]` slot in the three files from Tasks 20 and 21's outputs. Then:

```bash
grep -n 'GATE:' docs/verification/djia-events.md CLAUDE.md README.md
```

Expected: nothing. Ask the user to read `docs/verification/djia-events.md`'s plan B
sections, and wait for their approval before Step 4. The user may add to it; record
each addition as a deviation.

- [x] **Step 3: Final verification**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages python expirements/parser-fidelity/fetch_policy_pages.py verify
uv lock --check
git diff --stat 277e21b -- uv.lock AGENTS.md .gitignore .python-version config/universe tests/fixtures/cohort tests/fixtures/canonical
git diff --stat 277e21b -- config/corpus
```

Expected, checks: `1518 passed, 1 skipped, 24 deselected`; `280 passed`;
`All checks passed!` and `267 files already formatted`; `register quotes verified`;
`uv lock --check` passes; the first `git diff` prints nothing; and the second prints
nothing, or only `acquisition-overrides.toml` if Task 21 wrote it.

- [x] **Step 4: Commit**

```bash
git log --oneline -3
git add docs/verification/djia-events.md CLAUDE.md README.md
git commit -m "docs(events): record plan B's acquisition, and refresh the current state"
```

Add `docs/verification/edgar-acceptance-time.md` too if Step 1's regeneration ran.

---

## Handoffs

S §Handoffs to later stages lists what each later stage receives from Stage 5. Plan B
completes that list:

### To Stage 6 (the pilot codebook, split, and gold-set protocol)

- **The frozen pilot.** `current_pilot(directory, events, universe)` is the pilot
  frozen over the current event manifest, and `load_pilot(path, universe)` rechecks
  its chain and reselects it (P8-3, P8-4). The real one is pilot v1, 40 events.
- **The processing states.** `read_runs(data/runs/events/states)` reads every run,
  and `current_states(transitions, pilot_hash)` gives each pilot document's state.
  An expected but absent document carries its `missing_reason` (P8-6). The coverage
  report Stage 6 writes counts `unavailable`, `restricted`, and `failed` documents
  from them, and never reselects.

  > Deviation: after the final review (`55ea811`), `in_order` gives the order `check_histories` and `current_states` use: runs by their earliest `recorded_at`, then `run_id`, and each run's transitions by `sequence`. `events acquire` holds `.acquire.lock` in `data/runs/events` while it records; a later stage that writes runs to the same table takes it too.
- **The canonical documents.** Each `parsed` document's row names its `doc_id`, and
  its `walker-1` canonical document is `data/runs/events/canonical/<doc_id>.json`,
  local and never committed. Gold spans bind to those `doc_id`s. The saved exhibit
  regenerates it offline through `canonicalize`, since the store keeps its bytes.
- **Later states.** `partial`, `completed`, and `completed-no-theme` follow `parsed`
  (`NEXT`), set by later stages through new runs of the state table, never by editing
  a run file.

### To Stage 10 (coverage and denominators)

- The state table, for denominators, with every document's `missing_reason`; and the
  event manifest's issuer-period rows, which name every expected event.

### To Stage 15 (the full eight-quarter run)

- **The adapter.** `acquire` takes a pilot manifest today. Stage 15 acquires every
  eligible event, so it passes a manifest of those events, or generalizes the
  document list, reusing exhibit choice (`exhibit_order`), `release-content/1`
  (`confirm`), the states, and `planned_requests` for its gate's count.
- **The current version.** F4's rule (P8-4): the build decides which event manifest
  is current, and a universe is never reverted.
- **Recovery.** P2.1 and P2.2 stay deferred: a saved response that cannot be read is
  repaired by hand (`docs/verification/djia-events.md`, "Repairing the store"). A
  run of Stage 15's size makes the deferred recovery worth landing first.

### Deferred items that stay open

- **From PR #6's review of plan 7:** F27, F21, F11 and F24, P5.4, P4.3, P2.1 and
  P2.2, P2.3, P4.1, the co-registrant release, and the per-candidate citations.
- **From plans 1, 3, 5, 6, and 7:** every open item, as `specs/deferred_items.md`
  gives them.

## Completion

After Task 22, run the final whole-branch review. Then:

1. **Plan Completion Protocol** (writing-plans).
   - Run the resolve-before-defer gate.
   - Mark up this plan: tick the steps, add `> Deviation:` and `> Skipped:` notes, and
     add the status header.
   - A gate whose remedy was not needed is not skipped: note what the real data gave,
     such as "no override was needed".
2. **The stage stamp.** Append a blank line and these two lines to the end of
   `specs/event-discovery-eligibility-and-acquisition.md`, putting the completion date
   in place of `YYYY-MM-DD` (S §Rollout):

   ```text
   > Stage 5: COMPLETE (YYYY-MM-DD) — implemented by plans 7 (specs/plans/completed/7-event-discovery-eligibility-and-acquisition-plan-a.md) and 8 (specs/plans/completed/8-event-discovery-eligibility-and-acquisition-plan-b.md).
   > Next: resume the roadmap.
   ```

3. **Deferred items.** In `specs/deferred_items.md`, under
   `## PR #6 review (plan 7) — 2026-09-27`, tick the ten items this plan closed, each
   ending `→ done in plan 8` (P8-2):

Create `/tmp/plan8-tick.py`:

```python
"""Tick the deferred items plan 8 closed, each ending "→ done in plan 8"."""

from pathlib import Path

PATH = Path("specs/deferred_items.md")
DONE = [
    "Decide which frozen version is current after a revert (PR #6's review,",
    "Refuse a frozen version that repeats another's content or lacks its",
    "Decide whether loading a pilot re-derives its selection (PR #6's review,",
    "Cross-check an index page against its submissions row beyond the",
    "Refuse a redirected response (PR #6's review, F13): the shared client",
    "Read a primary document with no Item line as unread (PR #6's review, found",
    "Print the request count on every stop, and take an approved count in every",
    "Check the CLIs' store and corpus paths before anything runs (PR #6's",
    "Refuse a relative `EARNINGS_LOCK_DIR` (PR #6's review, F29):",
    "Commit the check that the real frozen records hold no source wording (PR",
]
lines = PATH.read_text(encoding="utf-8").splitlines(keepends=True)
for start in DONE:
    (at,) = [n for n, line in enumerate(lines) if line == f"- [ ] {start}\n"]
    lines[at] = f"- [x] {start}\n"
    end = at + 1
    while end < len(lines) and lines[end].startswith("      "):
        end += 1
    lines[end - 1] = lines[end - 1].rstrip("\n") + " → done in plan 8\n"
PATH.write_text("".join(lines), encoding="utf-8")
print(f"ticked {len(DONE)} items")
```

   ```bash
   python3 /tmp/plan8-extract.py /tmp/plan8-tick.py && python3 /tmp/plan8-tick.py
   ```

   Expected: `ticked 10 items`. Then append a
   `## 8-event-discovery-eligibility-and-acquisition-plan-b — YYYY-MM-DD` section,
   with the completion date, holding any item of this plan's own that the gate
   deferred, in the schema of `references/deferred-backlog.md`. Skip the section if
   the gate deferred nothing.

   Commit steps 1 to 3 together as
   `docs(specs): mark up plan 8, record Stage 5's completion, and tick deferred items`.
4. **Backlog triage.** Run
   `uv run --no-project --python 3.13 python ~/.claude/skills/writing-plans/scripts/deferred_stats.py`,
   and report its summary line. Present the triage rubric if its thresholds trip.
5. **Retire the plan and the spec (P8-1).** No other live plan implements the spec.

   ```bash
   git mv specs/plans/8-event-discovery-eligibility-and-acquisition-plan-b.md specs/plans/completed/
   git mv specs/event-discovery-eligibility-and-acquisition.md specs/completed/
   ```

   Then re-point every path to them outside the retired plans, and mark the spec
   complete under its title:

Create `/tmp/plan8-retire.py`:

```python
"""After the git mv: re-point the retired plan's and spec's paths, and mark the spec
complete under its title.

usage: python3 /tmp/plan8-retire.py <completion date, YYYY-MM-DD>
"""

import sys
from pathlib import Path

day = sys.argv[1]
MOVED = {
    "specs/event-discovery-eligibility-and-acquisition.md": (
        "specs/completed/event-discovery-eligibility-and-acquisition.md"
    ),
    "specs/plans/8-event-discovery-eligibility-and-acquisition-plan-b.md": (
        "specs/plans/completed/8-event-discovery-eligibility-and-acquisition-plan-b.md"
    ),
}
FILES = [
    "CLAUDE.md",
    "README.md",
    "docs/verification/djia-events.md",
    "docs/verification/edgar-acceptance-time.md",
    "tests/integration/regenerate_acceptance_time_record.py",
    "specs/evidence-linked-theme-extraction-roadmap.md",
]
for name in FILES:
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    count = sum(text.count(old) for old in MOVED)
    for old, new in MOVED.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print(f"re-pointed {name}: {count}")
spec = Path(MOVED["specs/event-discovery-eligibility-and-acquisition.md"])
title = "# Event discovery, eligibility, and acquisition\n"
text = spec.read_text(encoding="utf-8")
assert text.startswith(title), "the spec's title moved"
status = (
    f"\n**Status: COMPLETE ({day})** — Stage 5; implemented by plans 7 and 8;"
    " retired to specs/completed/.\n"
)
spec.write_text(title + status + text[len(title) :], encoding="utf-8")
print(f"marked {spec} complete")
```

   ```bash
   python3 /tmp/plan8-extract.py /tmp/plan8-retire.py && python3 /tmp/plan8-retire.py [GATE: the completion date, YYYY-MM-DD]
   git grep -n -e "specs/event-discovery-eligibility-and-acquisition.md" -e "specs/plans/8-event-discovery" -- . ':!specs/plans/completed' ':!specs/completed'
   uv run --locked ruff check . && uv run --locked ruff format --check .
   ```

   Expected: `re-pointed CLAUDE.md: 2`, `re-pointed README.md: 1`,
   `re-pointed docs/verification/djia-events.md: 2`,
   `re-pointed docs/verification/edgar-acceptance-time.md: 1`,
   `re-pointed tests/integration/regenerate_acceptance_time_record.py: 1`,
   `re-pointed specs/evidence-linked-theme-extraction-roadmap.md: 1`, and
   `marked specs/completed/event-discovery-eligibility-and-acquisition.md complete`;
   no `git grep` output; and lint passes. The generated
   `edgar-acceptance-time.md` and its generator change together, so the record still
   regenerates as it reads. The retired plan and spec keep their own mentions, as
   plans 4 to 7 do. Commit as `chore(specs): retire plan 8 and the Stage 5 spec`.
6. **The roadmap.** Run the derive-roadmap skill's reconcile step on
   `specs/evidence-linked-theme-extraction-roadmap.md`, as S §Rollout asks:
   - tick Stage 5;
   - close the roadmap's Open question with EV2 and EV3;
   - re-validate Stages 6, 10, 11, and 15 against what shipped (Handoffs above).

   Commit as `docs(roadmap): tick Stage 5 and reconcile the later stages`.
7. **Integrate** with finishing-a-development-branch.
   - Open a pull request from `stage-5-plan-b-acquisition` to `main`, as Stages 1 to
     4 and plan A did.
   - The branch was unpushed at planning, so this is its first push, and the
     repository is public. `data/` stays local: check `git status --short` and the
     pull request's file list before pushing.
8. **Report.**
   - State the commands actually run, and their results.
   - State every live request, by gate, with its count.
   - Give the pilot's and the event manifest's versions and content hashes, and the
     acquisition's states by count.
   - State that no model was called.
   - Name the four flagged readings, P8-6, P8-8, P8-9, and P8-11, which the user
     accepted as written on 2026-09-28, before execution.
