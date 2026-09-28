# Event Discovery, Eligibility, and the Freezes (Stage 5, plan A) — Implementation Plan

**Status: COMPLETE (2026-09-27)** — executed via executing-plans; deferred items in specs/deferred_items.md

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 5 — on plan
> completion, tick the stage and re-validate later stages against what shipped.
>
> This is plan A of Stage 5's two plans (EV1). Its completion does **not** tick
> Stage 5: the spec's Rollout says that "plan completion" means plan B's. Completion
> below appends the spec's Plan A line instead, and leaves the spec live (P7-1).

**Goal:** Build plan A of `specs/event-discovery-eligibility-and-acquisition.md` in
`earnings-ingestion` and `apps/earnings-pipeline`, and freeze what it defines:

- the prerequisites that Stage 5's requests and keys need: machine-wide client locks,
  the universe's operative identity, a verified acceptance-time rule, and two
  robustness fixes;
- discovery of the frozen DJIA cohort's expected events and their release filings
  from SEC filing metadata, through the shared SEC client;
- the membership join and eligibility (`eligibility/1`), the release rule
  (`release-id/1`), and review overrides;
- the frozen event manifest and its evidence record;
- `djia-pilot/1` and the frozen 40-event pilot manifest;
- a synthetic event layer that replays all of it offline (P-VI).

It ends when the user has reviewed and frozen the real event manifest and pilot. No
release exhibit is fetched: acquisition is plan B's (EV2).

**Architecture:**

- **Prerequisites.**
  - `fetch/client.py`'s `machine_lock_dir()` puts the SEC and web client locks in
    the user's cache directory, so every checkout on a machine shares them.
  - `cohort/identity.py`'s `operative_hash(manifest)` hashes only the cohort's
    cutoff-admissible facts, and Stage 5's records key on it (EV4).
  - `sec/data.py` gains 8-K items and older-page dates, and refuses malformed
    registrants. `sec/filing_index.py` and `sec/companyfacts.py` read a filing's
    index page and a registrant's fiscal labels.
  - `events/acceptance.py` reads the index page's "Accepted" value in
    America/New_York and cross-checks SEC's two `acceptanceDateTime` conventions.
    `docs/verification/edgar-acceptance-time.md` records the finding from saved
    pages.
- **Discovery and the build** (`packages/earnings-ingestion/src/earnings_ingestion/events/`).
  - `discover.py` fetches submissions, the older pages it needs, companyfacts, the
    index page of each Item 2.02 8-K and 8-K/A in range, and the primary document
    of each candidate. It saves every response in `data/raw/events/` on arrival.
  - `build` reads the frozen cohort, the saved responses, and the overrides. It
    makes one slot per issuer and period end, finds each slot's candidates, applies
    `release-id/1` and `eligibility/1`, and reports every finding.
  - `freeze` writes `config/corpus/djia-2024q3-2026q2/events-v<N>.json` and its
    evidence record. `pilot` runs `djia-pilot/1` on the latest frozen manifest and
    writes `pilot-v<N>.json`.
- **Commands** (`apps/earnings-pipeline`): `earnings-pipeline events discover`,
  `build`, `freeze`, and `select`.

**Tech Stack:**

- Python 3.14.0 and uv 0.12.15. No new dependency: `uv.lock` does not change.
- Already declared and locked:
  - httpx 0.28.1, through the shared SEC client;
  - lxml 6.1.3, for index pages, and under `walker-1`;
  - pydantic 2.13.5;
  - typer 0.27.2, for the CLI;
  - pytest 9.1.1 and Ruff 0.16.8.
- From the standard library: `zoneinfo`, for America/New_York from the system's
  time zone database; `tomllib`; and `json`.

## The spec this plan implements

The roadmap's Stage 5 entry scopes the stage
(`specs/evidence-linked-theme-extraction-roadmap.md`, Stage 5): its Spec, Gap closed,
Consumes, Produces, and Exit lines, and decision D5.

- **The stage spec.** `specs/event-discovery-eligibility-and-acquisition.md`, cited
  as `S`, was approved by the user on 2026-09-27. It splits Stage 5 into two plans,
  in order (EV1). This plan implements plan A:
  - S §Prerequisites, all four items;
  - S §Store, client, and readers; §Slots; §Candidates and `release-id/1`;
    §Acceptance time; §Eligibility; §Review overrides; §The event manifest;
    §P's expected-event contract; §Pilot selection; §Commands; and §The synthetic
    event layer;
  - S §Verification (plan A), items 1–14, and §Gates (plan A);
  - S §R14.5, and S §Deferred items for the dispositions plan A closes;
  - S §Exit criteria, §Plan A.
- **The cohort spec.** `specs/point-in-time-djia-cohort.md` (`P`) binds Stage 5's
  eligibility and pilot contracts. This plan closes, with plan B:
  - P-C2's event join, P-C5, P-C7's freeze-before-outcomes half, and P-A5;
  - P-VF's period-window, eligibility-reason, and selection cases, and P-VI.
- **`AGENTS.md`** (`A`): A §391–427, the acquisition and access policy, which the
  shared SEC client already implements (R1.3, D5).
- **Out of scope.** Plan B: acquiring the pilot's releases, exhibit choice,
  `release-content/1`, and the processing-state table (S §Plan B). Stage 15's full
  run. Any model call.
- **The user's decisions of 2026-09-27.** The planning session put three choices to
  the user, and P7-2, P7-3, and P7-6 record the answers:
  - whether the event and pilot hashes cover `universe_version`;
  - whether cohort v1 is refrozen after this plan edits the `sec-edgar` register
    entry;
  - whether SEC's formats are probed at plan time.

## Global Constraints

Every task's requirements include these.

**Locators:**

- `A §n` is `AGENTS.md` at line `n`.
- `Rn` are requirements in `specs/evidence-linked-theme-extraction.md`.
- `S` cites `specs/event-discovery-eligibility-and-acquisition.md`, the stage spec:
  - `EV1`–`EV13` are its Decisions rows;
  - `S §Section` cites a section by name, and `S Finding n` its §Findings from saved
    data;
  - "item n" of S §Verification (plan A) is written `SV n`.
- `P` cites `specs/point-in-time-djia-cohort.md`, as the roadmap does: `P-Cn`,
  `P-A5`, `P-VF`, `P-VI`, and `P §Section`.
- `Dn` are the roadmap's decisions, `P6-n` are plan 6's
  (`specs/plans/completed/6-point-in-time-djia-cohort.md`), and `P7-n` are this
  plan's, listed below.
- **v1** is the frozen cohort,
  `config/universe/djia/manifests/djia-2024q3-2026q2-v1.json`.

**Versions and constants.**

| Name | Value | Where |
| --- | --- | --- |
| Ingestion record schema | `1`, unchanged: the new records join it (P6-5) | `INGESTION_SCHEMA_VERSION` |
| Core schema | `2`, unchanged | `earnings_core` |
| Canonicalization of 8-K text and cited pages | `walker-1`, unchanged | `canonical/` |
| Discovery policy | `release-id/1` | `events/release.py` (Task 9) |
| Eligibility policy | `eligibility/1` | `events/eligibility.py` (Task 10) |
| Selection policy | `djia-pilot/1`, defined here, not bumped (EV8) | `events/pilot.py` (Task 14) |
| Window | `[2024-07-01, 2026-07-01)`, from the cohort | v1's definition |
| Public-information cutoff | `2026-09-22`, on the Eastern calendar | v1's definition |
| Acceptance time zone | `America/New_York` | `events/acceptance.py` (Task 5) |
| Corpus | `djia-2024q3-2026q2` | `config/corpus/djia-2024q3-2026q2/` |
| Pilot | `djia-2024q3-2026q2-pilot` | `pilot-v<N>.json` there |
| Stage 5's store | `data/raw/events/`, source `sec-edgar` (EV12) | `EVENTS_STORE` in `events/build.py` (Task 12) |
| SEC client | 0.5 s between request starts (2 req/s), shared across SEC hosts; 500 requests per run | `sec/client.py`, unchanged |

**Offline and no models.**

- Default tests make no network call and no billable call. They need no credential,
  and every event test runs on synthetic data.
- Live tests carry the `live` marker. Each skips without its identity and runs only
  with `-m live`, and only at a human gate.
- **`EDGAR_IDENTITY` is exported in this shell.** A live test's skip guard does not
  stop it, and it sends real requests. Never pass `-m live` outside a gate. To check
  collection, use `--collect-only`.
- No step calls a model.

**Network access.** Live requests happen only at the gates in "Human gates" below,
each after the user's clear yes in chat. At plan time, 19 were sent with the user's
approval (P7-6), and their responses are already saved.

- Every request goes through `open_sec_client`. Stage 5 adds no throttle of its own
  (R1.3, D5), and makes no web-client request.
- A persistent 403 stops the run. Report it, and never rotate identity (A §404).
- No exhibit is fetched in this plan (EV2).
- Nothing downloads a dependency, and `uv.lock` does not change.

**Identities.** `EDGAR_IDENTITY` belongs to the user and is configured outside Git.
Never print it, commit it, or record it anywhere. A `Retrieval` record never carries
it.

**Do not touch:**

- Stage 1's frozen harness and records: every file that
  `expirements/parser-fidelity/FROZEN.toml` lists, `tests/fixtures/releases/` and
  its gold, the V1 and V2 records, and ADR 0001. `discover.py`'s index-page parser
  is ported, never imported.
- `walker-1`: `packages/earnings-ingestion/src/earnings_ingestion/canonical/`,
  `tests/fixtures/canonical/`, and the golden test. The events code calls
  `canonicalize` as it is.
- The cohort's frozen and curated files: `config/universe/djia/` and v1 in it, and
  `tests/fixtures/cohort/`, which stays byte-identical (EV12). This plan refreezes
  nothing (P7-3).
- `AGENTS.md`. Other files cite it by line number (`CLAUDE.md` §Gotchas).
- `specs/event-discovery-eligibility-and-acquisition.md`, except the Plan A line that
  Completion appends to its Rollout.
- `.gitignore`: no edit, and its credentials block stays last. `data/*` already
  ignores `data/raw/events/`.
- `.python-version`, which pins 3.14.0.

**Stay in the main checkout.** Execute every task in the main checkout, on this
branch, never in a separate worktree. `data/` is gitignored, so a worktree lacks
what these read and write:

- Task 5's record reads Stage 1's saved pages under `data/raw/discovery/`;
- Task 16's v1 check reads Stage 4's saved evidence under `data/raw/cohort/`;
- the live run saves into `data/raw/events/`, which already holds the 19 responses
  of the plan-time probe, and the freezes write under `config/corpus/`.

The locks are machine-wide once Task 1 lands, so another checkout's client can no
longer race this one, but the data stays per checkout.

**Staging discipline.**

- `git add` only the paths a task names, never `git add -A` or `git add .`.
- After each commit, `git status --short` must print nothing, apart from local
  untracked files that predate this plan. So a later task's file never enters an
  earlier commit.
- `tests/fixtures/events/` is generated, and only Task 15 commits it.
- `config/corpus/djia-2024q3-2026q2/` is curated and frozen, and only the gated
  Tasks 20 and 21 commit it.

The user may commit on this branch while the plan runs. Run `git log --oneline -3`
before each commit, and never rewrite a commit you did not make.

**Unicode escapes.** Every new or replaced Python file in this plan is ASCII, except
`§` in citations such as `A §407`.

- Tests build non-ASCII inputs from code points with `chr(0x...)`.
- No file carries a backslash-u escape that a tool channel might decode on the way
  to disk.
- Each task that writes Python runs the escape check below. It prints
  `escapes intact`, or else the name of each file holding another non-ASCII
  character.

**Writing files from this plan.** Every code block that holds a whole file, or text
to append, follows a line of one of three forms:

- ``Create `<path>`:``;
- ``Replace `<path>` with:``;
- ``Append to `<path>`:``.

Extract each such file with the helper below rather than retyping it. Retyping
thousands of lines invites silent slips, and a tool channel that decodes an escape
would do it again on a retry. The Preconditions save the two helpers once, as
`/tmp/plan7-extract.py` and `/tmp/plan7-escapes.py`. If `/tmp` has been cleared,
save them again from here.

`/tmp/plan7-extract.py`:

````python
"""Extract one file block from plan 7; run from the repository root.

usage: python3 /tmp/plan7-extract.py <path> [block number, default 1]
"""

import sys
from pathlib import Path

PLAN = Path("specs/plans/7-event-discovery-eligibility-and-acquisition-plan-a.md")
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

`/tmp/plan7-escapes.py`:

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

- A step that says **extract** a path runs `python3 /tmp/plan7-extract.py <path>`,
  which prints `extracted <path>: <n> lines`, or `appended to <path>: <n> lines` for
  an append. The block number is `1` unless the step names another.
- **Edits to existing files.** Most existing files change by exact replacement, not
  whole. The plan gives each such change as a script, ``Create `/tmp/plan7-<name>.py`:``,
  that holds every old and new text. A step that says **apply** `<name>` runs:

  ```bash
  python3 /tmp/plan7-extract.py /tmp/plan7-<name>.py && python3 /tmp/plan7-<name>.py
  ```

  Each old text must match exactly once, and nothing is written unless every
  replacement in the script applies. A file that has drifted from the plan stops the
  script with its path. The script prints `edited <path>: <n> replacement(s)` for
  each file.
- If the escape check names a file, extract or apply it again and rerun the check.

**Lint.** `uv run --locked ruff check .` and `uv run --locked ruff format --check .`
pass after every task, and the code below already passes both.

- The Expected `N files already formatted` counts assume a clean checkout: 211
  before Task 1, growing with each task's new Python files.
- A different count with no `Would reformat` line comes from local untracked Python
  files, and is not a failure.

**Expected outputs.** At plan time this plan was replayed on a scratch branch cut
from `1dff2ef`: every task through Task 18, and Task 22's documents. Those Expected
outputs are what the replay printed. The replay sent no request and wrote nothing
under the main checkout's `data/` or `config/`.

Tasks 19 to 22 act on live data, so most of their outputs are predictions, marked as
such:

- the live discovery and the record's second leg (Task 19);
- the review and the real manifests (Tasks 20 and 21);
- the verification record (Task 22).

Their other steps were replayed on the synthetic corpus, and their outputs are exact:
the record's second leg, and the helpers for the review, the approvals, and the P6-3
check. Each of those tasks also marks its **checks**: outputs that hold whatever the
live data say, such as the default suite's count. A prediction that differs is
reported, and is not a failure. A check that differs stops the task.

Anywhere else, if a count differs while nothing fails, stop and report it rather than
editing a test to match.

**Test imports.** Ruff sorts `earnings_core` and `earnings_ingestion` as third-party
imports in test files, in one block with `pytest`, so keep the imports as written.
Inside `earnings_ingestion` they are first-party.

**Public repository.** `origin` (https://github.com/lowmason/earnings-themes) is
public, so everything committed is published.

- The synthetic event layer is invented and redistributable. Its wording is modeled
  on the probe's filings, never copied from them.
- The real manifests and evidence record hold facts, URLs, locators, and hashes,
  never a source's wording (P6-3).
- Saved SEC responses stay under the gitignored `data/`.
- The real `overrides.toml` names its reviewer, who is the user.

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
  its baseline.
- The third is **lint**.

## Plan decisions

The spec leaves these choices open, so the plan makes them. The user can overturn any
of them before execution. The planning session of 2026-09-27 put three to the user,
and P7-2, P7-3, and P7-6 record the answers. The code records each decision where it
applies. None adds or retunes a spec rule: where a rule needed a reading, the reading
is stated. Four readings are **flagged for the user**, because each narrows the
spec's words or adds to them: P7-4, P7-7, P7-8, and P7-20. The user accepted all
four as written on 2026-09-27, before execution.

**P7-1 — Plan A only, and the spec stays live.** EV1 splits Stage 5 into two plans,
and plan B is planned only after this plan ships with the real manifests frozen.

- The Plan Completion Protocol would retire a spec that no live plan names, and at
  this plan's completion none would. This plan overrides that default, as plan 6's
  P6-1 did: the spec stays in `specs/`, because plan B implements it too.
- Completion appends the spec's Plan A line, retires only this plan, and does not
  tick Stage 5 in the roadmap (S §Rollout).

**P7-2 — The event and pilot hashes leave out `universe_version` (the user's
answer).** EV4 keys Stage 5's records on the universe's operative hash. The
`universe_version` a record read is still written in it, but outside its content
hash, as `event_manifest_version` and `pilot_version` are. So a cohort version whose
facts are unchanged never re-versions an event manifest or re-seeds the pilot, and
the pilot's chain check compares operative hashes, not versions.

**P7-3 — Cohort v1 stays, with no refreeze (the user's answer).** S §Inputs asks for
the `sec-edgar` register entry to name companyfacts, and Task 16 edits it. v1's
`source_register_version` hashes that entry, so a rebuild of the real cohort now has
a different content hash from v1's, while its operative hash is v1's.

- Task 16 shows both, from Stage 4's saved evidence.
- v1 stays the latest version, and no v2 is frozen: its facts are unchanged, and a
  version whose only change is a register entry's wording would re-version nothing
  that Stage 5 reads (EV4).
- **Limitation.** `earnings-pipeline cohort verify-live` compares a rebuild's content
  hash with the frozen one's, so it will now report a difference. Task 22's record
  states this, and Completion adds a deferred item for it. The deferred item "Let
  `verify-live` re-read the other hosts" stays open too (S §Deferred items).

**P7-4 — The operative projection's mappings (a reading of EV4; flagged).** S §Prerequisites
lists "each mapping's `security_id`, `status`, `issuer_id`, and `cik`". Taken
literally, that includes a security named only by evidence the cutoff withholds.
Such a security has no interval, so its mapping decides no event, yet curating the
withheld notice would change the operative hash. The first test S asks for, "a
withheld notice … change[s] `content_hash` but not the operative hash", fails under
the literal reading on the synthetic cohort, whose withheld notice names Fenwick.

- So the projection keeps the mapping of each security that has an interval, and
  leaves out the rest.
- In v1, all 33 mappings have intervals, so the two readings agree there.

**P7-5 — One lock directory per user.** S §Prerequisites names the directory, and
the plan names the rest:

- `fetch.client.machine_lock_dir()` returns `$EARNINGS_LOCK_DIR` when it is set;
  otherwise `~/Library/Caches/earnings-themes/locks` on macOS; otherwise
  `$XDG_CACHE_HOME/earnings-themes/locks` when that variable is an absolute path,
  and `~/.cache/earnings-themes/locks` if not. A relative `XDG_CACHE_HOME` is ignored,
  as the XDG specification says.
- `open_sec_client` and `open_web_client` lose their `repo` argument, since the lock
  no longer lives in a checkout.
- The test suites set `EARNINGS_LOCK_DIR` to a temporary directory, through an
  autouse fixture, so a test never touches the user's real lock.

**P7-6 — The plan-time format probe (the user's answer).** With the user's approval,
the planning session sent 19 SEC requests through `open_sec_client`, and saved the
responses in `data/raw/events/sec-edgar/`:

- the 16 primary documents of S Finding 4's eight two-filing quarters;
- companyfacts for Nike, Coca-Cola, and IBM.

What they showed pinned `release-id/1`'s phrase lists (P7-7), and the synthetic
filings are modeled on them without copying their wording. Every saved URL
reproduces exactly from `archive_url(cik, accession, primaryDocument)` and
`companyfacts_url(cik)`, so the live run finds them saved and does not fetch them
again. In the three companyfacts files, `fy` and `fp` agree within every accession,
and only non-periodic filings (an 8-K, a DEF 14A, two S-8s, and a 424B5) state
neither.

**P7-7 — `release-id/1`'s phrase lists, and one narrowing (flagged).** S §Candidates
leaves the phrase lists to the plan, pinned by fixtures modeled on Finding 4's
two-filing quarters. Task 9 reads four things in each candidate's Item 2.02 text:

- **Dates: only a full date after "ended" or "ending".** This narrows S's "the dates
  the text writes in full". The probe's 16 documents (P7-6) show why:
  - Nearly every Item 2.02 section writes its announcement date, which never equals
    P. Under the literal words, that date is a judged statement that always fails.
    For a slot without fiscal labels, Boeing's and Chevron's releases would then be
    dropped, leaving `no_release_filing`, and Honeywell's recast filed 2025-12-22
    would be chosen over its release of 2025-10-23 for 2025-09-30.
  - That recast writes "September 30, 2025" other than after "ended", and states
    other quarters' results. Under the literal words it matches P, and the quarter
    goes to review even with labels. Under the narrowing, the rule drops it.
- **Fiscal periods**, read quarters first:
  - ordinal quarters with their year, in either order, such as "third quarter of
    2024" and "fiscal 2025 second quarter";
  - `Q` quarters, "Q3 2024" and "3Q 2024";
  - full years, "fiscal 2025" and "full year 2024".

  The year-first and "3Q" forms are readings of S's "an ordinal or `Q` quarter with a
  year".
- **Preliminary:** "preliminary", or "expected" with "results" among the next three
  words.
- **Headings:** an Item 2.02 section runs from a line that begins "Item 2.02" to the
  next line that begins "Item" and a number.

The rule is fixed from here on. After the real run, it changes only as `release-id/2`
(S §Candidates).

**P7-8 — Where each filing is placed, and `acceptance_time_unknown` (flagged).**
S §Acceptance time takes a filing's acceptance time from its index page. It does not
say what places a filing whose index page is not saved, and discovery saves none for
periodic reports (P7-9). So:

- a filing whose index page is saved takes its Accepted value, and its submissions
  row is cross-checked;
- an original periodic report without one is placed by its file's convention, which
  the file's cross-checked rows establish, or else by both conventions, when their
  readings fall on the same side of the cutoff;
- a report whose readings fall on either side of the cutoff, or whose row has no
  value, is `acceptance_time_unknown`. So is an Item 2.02 8-K or 8-K/A with no value,
  filed on or after the window's start.
- `acceptance_time_unknown` blocks, and no override answers it. Its remedy is data:
  `events discover --filing CIK ACCESSION`, at most two requests at a gate, and then
  a rebuild.

At plan time, over Stage 4's saved submissions for v1's 33 issuers, no filing was
`acceptance_time_unknown`.

**P7-9 — The index pages discovery fetches.** Discovery fetches the index page of
every Item 2.02 8-K and 8-K/A that either convention places in
`[2024-07-01, 2026-09-22]`. So the page, never a file's convention, decides whether a
release is in range. An 8-K/A's page is fetched too, since the build records
amendments and an override may choose one. No periodic report's page is fetched: its
file's convention places it (P7-8).

**P7-10 — Discovery's budget and phases.** `events discover` needs
`--max-requests N`, the count the user approved, and it caps the shared client at N
for the run.

- It states N before any request, and each phase's count before that phase.
- There are three phases, and each reads what the one before saved:
  1. submissions files and companyfacts files;
  2. the older pages and index pages that `issuer_filings` finds missing, repeated
     until nothing is;
  3. the primary documents of `release-id/1`'s candidates.
- It fetches only what the store lacks, so a stopped run resumes.
- `--filing CIK ACCESSION` caps itself at two.

**P7-11 — `membership_assertion_id` beyond S's cases.** S names the assertion that
decides check 4, and sets it null "when check 1 or 2 decided". Two readings extend
that:

- it is null when check 3 decides too, since the cutoff is judged before membership;
- when several of an issuer's intervals hold T, the interval that opened first
  decides, and of its assertions, the smallest ID.

**P7-12 — The store is read once per build.** `SavedResponses` reads the retrieval
records once, and keeps the newest retrieval of each URL. Stage 4's
`ArtifactStore.latest` rereads every record on each call, which would make a build
over about 700 responses quadratic.

**P7-13 — An index page must be its filing's.** A saved index page whose accession
is another filing's is a problem, which stops the build, since no review can settle
it. A `set_release_filing` whose filing's page names another accession is refused.

**P7-14 — One override of each kind per event.** S §Review overrides says a
`set_release_filing` decides eligibility again, and "may come out as any status". That
includes `ambiguous` with `same_day_transition`, which only a `retain_unresolved`
settles.

- So the overrides file allows one override of each kind for an event, and refuses a
  second of the same kind.
- A `retain_unresolved` is judged against the row that the event's
  `set_release_filing` leaves.

**P7-15 — Readings are printed, not recorded.** `events build` prints, for review:

- each candidate's reading: its dates, periods, whether it is preliminary, and why it
  was dropped;
- each amendment;
- each Item 2.02 8-K that was passed over, with the reason.

The evidence record keeps the citations EV11 lists, but no reading. No later stage
reads one, and `release-id/1` recomputes it from the saved document.

**P7-16 — Refused and stale overrides.**

- **Refused.** An override that names no such event, finding, or filing is refused,
  as S §Review overrides says. That includes an acknowledgement of a finding that no
  longer arises. So is one that acknowledges any kind but `period_gap` or `no_slots`,
  and one whose citations fail. A refusal is a problem, which stops the build.
- **Stale.** An acknowledgement whose finding's digest has changed is stale (P6-7).
  So is a `retain_unresolved` whose event is no longer `ambiguous` with its reason,
  where S is silent. A stale override holds the freeze, and `events build` names it.
- **Unlike Stage 4.** In Stage 4, an acknowledgement whose finding vanished is stale.
  Here it is refused, because S's refusal rule names it.

**P7-17 — The synthetic event layer.** `events/layer.py` writes every response
discovery would fetch for the synthetic cohort's five candidate issuers. Every
company, filing, and word is invented, and each case takes its shape from the probe's
real filings, never their wording.

- **The cases**, by issuer:
  - Acme: a Nike-like fiscal year, Eastern digits, two candidates the rule cannot
    separate, and filings after the cutoff;
  - Borealis: a same-day release, `EX-99`, an 8-K/A, and the third `period_gap`
    case;
  - Corvid: an entry, the second `period_gap` case, `EX-99.01`, disagreeing labels,
    and an AMC-like overview for plan B;
  - Dynamo: two securities, a calendar ending 2026-07-03, a preliminary filing and
    then the release, a quarter with no candidate, and a narrative-only release;
  - Eastfield: an exit, the first `period_gap` case, true UTC, and an older page
    read and another skipped.
- **The review** records three acknowledgements, one `set_release_filing`, and two
  `retain_unresolved`.
- **The result.** 32 events, 27 of them eligible, so P-VI takes the underfilled path.
  The other selection paths are tested on rows built directly (S §The synthetic
  event layer).

**P7-18 — Commands and flags.** Task 17 settles them:

- `earnings-pipeline events [--repo] [--universe-dir] [--corpus-dir] [--store] [--corpus-id]`;
- its commands: `discover --max-requests N`, `discover --filing CIK ACCESSION`,
  `build`, `freeze`, and `select`.

The defaults are the real corpus's. The universe is the latest frozen version in
`--universe-dir`, and `select` reads the version its event manifest read.

**P7-19 — The acceptance-time record.**
`tests/integration/regenerate_acceptance_time_record.py` is a script that pytest
never collects, like Stage 4's fixture generator. It sends no request, and writes
`docs/verification/edgar-acceptance-time.md` from saved pages:

- leg 1 reads Stage 1's pages, and reproduces S Finding 1;
- leg 2 reads Stage 5's store, once Task 19's discovery has saved it.

It identifies submissions files by their URL, since companyfacts files share their
names.

**P7-20 — The pilot's second input, and transitions by day (flagged).** S §Pilot
selection says that `djia-pilot/1` "reads only a frozen event manifest" (EV8). But
its step 2 needs issuer-level entries and exits, and only the universe manifest holds
them.

- **The universe as a second input.** The pilot reads the universe version that its
  event manifest read. `select_pilot` and `load_pilot` check that the version's
  operative hash is the one the event manifest records. No acquisition, parse, or
  later outcome is an input.
- **Transitions by day.** An issuer's membership is the union, day by day, of its
  securities' intervals:
  - an entry is a start, other than an `anchor_snapshot`, whose previous day no
    interval holds;
  - an exit is an end whose day no interval holds;
  - either counts when dated in `[2024-07-01, 2026-09-22]`.

  So a handoff between two securities of one issuer is no transition, and a gap
  between two intervals is two transitions.
- **The member side** includes the transition's own day: on or after an entry's
  date, and on or before an exit's. Eligibility has already ordered a same-day
  release against the bound's timing.
- **On v1,** there are six transitions, all before the open:
  - on 2024-11-08, Intel's and Dow's exits and Sherwin-Williams' and NVIDIA's
    entries;
  - on 2026-06-29, Verizon's exit and Alphabet's entry.

## Requirement map

S §Verification (plan A), item by item. Items 2 to 13 are S §Exit criteria (plan A),
item 4.

| Item | What shows it | Task |
| --- | --- | --- |
| SV 1: two repository roots share each lock | `test_two_checkouts_share_one_lock`, for the SEC client and for the web client; `test_the_lock_directory_is_the_users_cache_outside_every_checkout` | 1 |
| SV 1: the operative hash, and v1 loads unchanged | `test_a_withheld_notice_changes_the_content_but_not_the_identity`; `test_a_refetched_sec_record_changes_the_content_but_not_the_identity`; `test_v1_loads_unchanged_and_has_an_operative_hash` | 3 |
| SV 1: the acceptance-time record regenerates from saved pages | `tests/integration/regenerate_acceptance_time_record.py`: leg 1 at Task 5; both legs at Task 19, after an offline run on the synthetic store | 5, 19 |
| SV 1: the two robustness fixes | `test_a_malformed_registrant_is_refused_as_sec_data`; `test_retry_after_ignores_non_ascii_digits` | 2 |
| SV 2: each reader refuses a changed shape, and Stage 4's synthetic submissions still read | `test_malformed_items_are_refused`; `test_an_older_page_with_a_malformed_date_is_refused`; `test_a_page_of_another_shape_is_refused`; `test_facts_of_another_shape_are_refused`; Stage 4's cohort tests, unchanged | 4 |
| SV 3: both conventions, a date in each daylight-saving season, and a blocking mismatch | `test_the_accepted_value_is_eastern_wall_time` (daylight and standard time); `test_a_row_uses_one_convention_or_mismatches`; `test_a_row_in_neither_convention_is_a_blocking_mismatch`; `test_the_conventions_and_the_older_pages` | 5, 7, 11 |
| SV 4: the discovery replay (R1.1, R1.2) | `test_each_release_is_identified_by_its_statements`; `test_the_preliminary_filing_is_dropped_and_the_gap_s_neighbor_too`; `test_exhibit_numbering_and_the_amendment`; `test_every_event_s_reason_before_any_override`; `test_the_layer_holds_what_discovery_fetches_and_no_filing_after_the_cutoff` | 11 |
| SV 5: no exhibit before the freeze (EV2), and only the shared client (R1.3, D5) | `test_discovery_requests_what_the_build_reads_and_never_an_exhibit`; `test_stage_5_has_no_client_or_throttle_of_its_own` | 16 |
| SV 6: slots (P-VF) | `test_two_securities_make_one_row_per_period`; `test_the_window_is_half_open`; `test_each_period_gap_case_blocks`; `test_an_issuer_without_a_slot_blocks`; `test_a_nike_like_calendar_trips_no_guard` | 8, 12 |
| SV 7: eligibility (P-C2, P-VF) | `test_the_bound_rules_in_winter`; `test_the_bound_rules_in_summer`; `test_every_reason_and_the_checks_order` | 10 |
| SV 8: event records (R1.5, P-A5) | `test_an_eligible_row_keeps_every_time_and_label_apart`; `test_unknown_labels_stay_null_together`; `test_record_fields_stay_separate_and_unknown_labels_stay_null` | 6, 12 |
| SV 9: the freeze | `test_the_freeze_refuses_and_names_each_reason`; `test_identical_content_is_the_same_version`; `test_a_refetch_with_the_same_facts_writes_nothing`; `test_a_changed_fact_writes_the_next_version` | 13 |
| SV 10: selection (P-C5, P-VF) | `test_shuffled_input_gives_a_byte_identical_pilot`; `test_with_40_or_more_eligible_events_the_pilot_holds_exactly_40`; `test_the_event_count_guards`; `test_more_than_40_issuers_needs_a_scope_decision`; `test_mandatory_cases_beyond_the_target_refuse_before_filling`; `test_a_quarter_with_no_eligible_event_refuses`; `test_the_synthetic_pilot_is_underfilled_and_takes_every_event` | 14 |
| SV 11: invalidation (P-VF) | `test_a_moved_bound_changes_both`; `test_a_changed_mapping_changes_both`; `test_a_changed_interval_or_policy_changes_the_hash_and_a_version_alone_does_not`; `test_a_changed_event_fact_or_policy_reseeds_and_a_universe_version_does_not`; `test_a_new_event_manifest_version_gives_the_next_pilot` | 3, 13, 14 |
| SV 12: P-VI | `test_p_vi_replays_offline_to_the_frozen_manifests`, under a socket guard with no identity set | 15 |
| SV 13: R14.5 | `test_stage_5_loads_no_acquisition_library`; `test_stage_5_imports_no_acquisition_library`; the record's R14.5 section | 18, 22 |
| SV 14: the suites pass, and `uv.lock` does not change | each task's checks | all |

S §Exit criteria (plan A), item by item:

| Exit item | Where | Task |
| --- | --- | --- |
| 1. Both locks are machine-wide and tested, and the records say one machine | `machine_lock_dir()`; the lock bullet of `docs/verification/djia-cohort.md` | 1 |
| 2. The operative hash exists with its tests, and v1 loads unchanged | `cohort/identity.py` | 3 |
| 3. The acceptance-time record regenerates from saved pages, with both legs | `docs/verification/edgar-acceptance-time.md` | 5, 19 |
| 4. SV 2 to 13 pass | the table above | 4 to 18 |
| 5. The real event manifest and pilot are frozen and committed after the gates, and the record gives the run | `config/corpus/djia-2024q3-2026q2/`; `docs/verification/djia-events.md` | 20, 21, 22 |
| 6. The default suite, the harness suite, and Ruff pass | each task's checks | all |

The cohort spec's items that this plan closes, with plan B:

| P item | Where | Task |
| --- | --- | --- |
| P-C2's event join: membership judged at first publication | `eligibility/1` | 10 |
| P-C5: a deterministic, seeded selection | `djia-pilot/1` | 14 |
| P-C7, both manifests frozen before any outcome | The event freeze refuses what is unanswered. `events select` needs a frozen event manifest. Neither reads an acquisition or parse outcome, and Tasks 20 and 21 freeze both before plan B acquires anything | 13, 14, 17, 20, 21 |
| P-A5: the times and labels stay separate fields | `EventRow` | 6 |
| P-VF: the period window, every eligibility reason, and selection | SV 6, 7, 10, and 11 | 8, 10, 14 |
| P-VI: the offline replay | SV 12 | 15 |

## Human gates

S §Gates (plan A), with the stops that the real data can force:

| Gate | When | Who | What it unblocks |
| --- | --- | --- | --- |
| Discovery | Task 19, Step 2 | user | `events discover --max-requests 700`: at most 700 SEC requests through the shared client, as `EDGAR_IDENTITY`, and about 680 predicted. The margin is small, but the run is resumable. |
| A rerun of discovery | Task 19, whenever discovery stops | user | The rerun and its count, stated before it runs. A persistent 403 is reported and never retried with another identity (A §404). |
| One filing's pages | Task 20, whenever `build` reports `acceptance_time_unknown`, or an override names a filing discovery did not save | user | `events discover --filing CIK ACCESSION`: at most 2 requests for each filing |
| The review | Task 20, Steps 2 and 3 | user | The decision on each blocking finding and each `ambiguous` event, each override's rationale in the user's words, and the signature |
| A stop no override answers | Task 20, whenever `build` reports `acceptance_time_mismatch` or a `problem:` line | user | A stop. EV10's rule, or a saved response, has failed. Changing a rule (`release-id/2`, or a spec change) is outside this plan. |
| The event manifest's freeze | Task 20, Step 4 | user | `events freeze`, after the user reads the approval view |
| The pilot's freeze | Task 21, Step 1 | user | `events select`, after the user reads the preview. A refusal (`blocked`, `scope_decision_needed`, `mandatory_overflow`, or `quarter_uncovered`) stops for the user. |
| The record | Task 22, Step 1 | user | `docs/verification/djia-events.md`, which the user reads before it is committed: the requests by gate, the statuses and reasons, the overrides, the pilot by reason, both versions and hashes, and that no model was called |

- **No `-m live` test.** No task runs one. `EDGAR_IDENTITY` is exported, so such a
  run would send real requests and need a gate of its own. Tasks 1 and 4 changed only
  the call signatures in Stage 4's live format probe.
- **Hard stops.** In subagent-driven execution, every gate runs in the controller
  session with the user, never in a subagent. Each gate is a hard stop: nothing after
  it starts until the user has answered. A subagent that reaches a gate stops and
  reports back instead.

## File map

`…/fetch/`, `…/sec/`, `…/cohort/`, and `…/events/` below are under
`packages/earnings-ingestion/src/earnings_ingestion/`, and `…/tests/` is
`packages/earnings-ingestion/tests/`.

| Path | Responsibility | Task |
| --- | --- | --- |
| `…/fetch/client.py`, `…/sec/client.py`, `…/cohort/web.py`, `…/cohort/live.py`; `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`; `…/tests/conftest.py`, `test_fetch_client.py`, `test_sec_client.py`, `test_cohort_web.py`; `apps/earnings-pipeline/tests/conftest.py`, `test_cohort_cli.py`; `tests/integration/test_sec_formats_live.py`; `docs/verification/djia-cohort.md` | Machine-wide client locks | 1 |
| `…/fetch/client.py`, `…/sec/data.py`; `…/tests/test_fetch_client.py`, `test_sec_data.py` | The two robustness fixes | 2 |
| `…/cohort/identity.py`; `…/tests/test_cohort_identity.py` | The universe's operative identity | 3 |
| `…/sec/data.py`, `filing_index.py`, `companyfacts.py`, `urls.py`; `…/cohort/acquire.py`, `build.py`; `…/tests/test_sec_data.py`, `test_sec_filing_index.py`, `test_sec_companyfacts.py`; `tests/integration/test_sec_formats_live.py` | SEC's readers for items, older pages, index pages, and companyfacts | 4 |
| `…/events/__init__.py`, `acceptance.py`; `…/tests/test_events_acceptance.py`; `tests/integration/regenerate_acceptance_time_record.py`; `docs/verification/edgar-acceptance-time.md` (generated) | Acceptance time, and its record's two legs | 5, 19 |
| `…/events/records.py`; `…/tests/test_events_records.py`; `docs/data-dictionary.md`, `tests/contracts/test_data_dictionary.py` | The event records (Task 6), the frozen event manifests (Task 13), and the pilot records (Task 14) | 6, 13, 14 |
| `…/events/saved.py`, `filings.py`, `synthetic.py`; `…/tests/test_events_filings.py` | Saved responses, an issuer's placed filings, and the synthetic formats. `synthetic.py` grows in Tasks 8 and 9, and `filings.py` in Task 16 | 7, 8, 9, 16 |
| `…/events/slots.py`; `…/tests/test_events_slots.py` | Slots, their guards, and their labels | 8 |
| `…/events/release.py`; `…/tests/test_events_release.py` | `release-id/1` | 9 |
| `…/events/eligibility.py`; `…/tests/test_events_eligibility.py` | `eligibility/1` | 10 |
| `…/events/layer.py`; `…/tests/test_events_layer.py` | The synthetic event layer, and its review (Task 12) | 11, 12 |
| `…/events/build.py`; `…/tests/test_events_build.py` | The build and the overrides | 12 |
| `…/events/evidence.py`, `freeze.py`; `…/tests/test_events_freeze.py` | The evidence record and the event freeze | 13 |
| `…/events/pilot.py`; `…/tests/test_events_pilot.py` | `djia-pilot/1`, and the pilot's freeze | 14 |
| `…/events/fixture.py`; `tests/integration/regenerate_event_fixtures.py`, `test_event_fixtures.py`; `tests/fixtures/events/` (generated); `.gitattributes` (one line appended) | The committed synthetic event corpus, replayed offline | 15 |
| `…/events/discover.py`; `…/tests/test_events_discover.py`; `docs/source-register.toml` | Discovery, and the `sec-edgar` entry's companyfacts | 16 |
| `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py`, `cli.py`; `apps/earnings-pipeline/tests/test_events_cli.py` | The `events` commands | 17 |
| `…/tests/test_import_boundaries.py`; `tests/contracts/test_import_scan.py` | The R14.5 import boundary | 18 |
| `config/corpus/djia-2024q3-2026q2/overrides.toml`; `events-v1.json` and `events-v1.evidence.json` there (generated) | The reviewed and frozen event manifest | 20 |
| `config/corpus/djia-2024q3-2026q2/pilot-v1.json` (generated) | The frozen pilot | 21 |
| `docs/verification/djia-events.md`; `CLAUDE.md`; `README.md`; `docs/verification/djia-cohort.md` (one bullet) | The verification record and the current state | 22 |
| `data/raw/events/` | Stage 5's saved responses, local and uncommitted | 19, 20 |

No other file changes, and `uv.lock` does not change.

## Preconditions — read before Task 1

- **Branch.** Work on `stage-5-event-discovery-eligibility-and-acquisition` in the
  main checkout. At planning time its commits above `main` (`4cfd101`) were the
  roadmap reconcile (`93d4cb7`), the spec (`349007f`), the spec's period-gap fix
  (`1dff2ef`), and this plan's commit, and the branch was unpushed. Run this and read
  the result:

  ```bash
  git switch stage-5-event-discovery-eligibility-and-acquisition && git log --oneline -3 && git status --short
  ```

  Expected: the head is `docs(plan): plan 7, Stage 5 plan A: discovery, eligibility, and the freezes`,
  or a later commit the user made, and the status is empty.
- **Stay in the main checkout** (Global Constraints). Do not execute in a separate
  worktree.
- **Environment.** Run `uv sync --locked --all-packages`; the `dev` group syncs by
  default.
  - `uv --version` must print uv 0.12.15.
  - The interpreter is Python 3.14.0, pinned by `.python-version`.
- **Helpers.** Save the two helpers from Global Constraints, then check both:

  ```bash
  python3 /tmp/plan7-extract.py docs/no-such-file.md; python3 /tmp/plan7-escapes.py specs/plans/7-event-discovery-eligibility-and-acquisition-plan-a.md
  ```

  Expected: `specs/plans/7-event-discovery-eligibility-and-acquisition-plan-a.md has no block 1 for docs/no-such-file.md`,
  then the plan's own path. The plan holds non-ASCII characters, so this shows that
  the check works.
- **Baselines:**

  ```bash
  uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
  uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
  uv run --locked ruff check . && uv run --locked ruff format --check .
  uv run --locked --all-packages python expirements/parser-fidelity/fetch_policy_pages.py verify
  ```

  Expected: `936 passed, 24 deselected`; `280 passed`; `All checks passed!` and
  `211 files already formatted`; `register quotes verified`.

  If the harness reports 278 passed and 2 skipped, the rendered copies are missing:
  stop and ask.
- **Local data.** These must exist. If any is missing, stop and ask:
  - `data/raw/discovery/submissions/` and `data/raw/discovery/filings/`, Stage 1's
    saved pages, which Task 5's record reads;
  - `data/raw/cohort/sec-edgar/`, Stage 4's saved SEC records, which Task 16's v1
    check reads;
  - `data/raw/events/sec-edgar/`, the plan-time probe's 19 responses:
    `ls data/raw/events/sec-edgar | wc -l` prints `20`, the 19 files and
    `retrievals/`.
- **Identity.** Check it without printing it:

  ```bash
  [ -n "$(printenv EDGAR_IDENTITY)" ] && echo "EDGAR_IDENTITY set" || echo "EDGAR_IDENTITY unset"
  ```

  Only the gates need it. If it is set, remember that a `-m live` run really reaches
  SEC (Global Constraints).

---

### Task 1: Machine-wide client locks

S §Prerequisites, item 1, and the deferred item "Hold the SEC and web client locks
once per machine". Stage 4 put each client's lock in its checkout's `data/runs/`, so
two checkouts on one machine could each hold "the" SEC client and together exceed
2 req/s. The locks move to one directory per user, outside every checkout (P7-5).

- **`machine_lock_dir()`** in `fetch/client.py` names that directory, and
  `EARNINGS_LOCK_DIR` overrides it.
- **`open_sec_client` and `open_web_client`** take no `repo`. Each takes its lock at
  `machine_lock_dir() / LOCK_NAME`, and the callers change to match.
- **Tests.** An autouse fixture in each suite's conftest points `EARNINGS_LOCK_DIR`
  at a fresh directory, so no test touches the real lock. A new test per client runs
  a second process from a second checkout while the first holds the client, and
  shows it refused with the same lock path.
- **Records.** `docs/verification/djia-cohort.md` says "one machine" again. Stage 1's
  harness keeps its own lock, so the two still never run live together.

**Files:**

- Modify, by exact replacement:
  - `packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py`,
    `sec/client.py`, `cohort/web.py`, and `cohort/live.py`;
  - `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`;
  - `docs/verification/djia-cohort.md`.
- Test (create): `apps/earnings-pipeline/tests/conftest.py`.
- Test (modify, by exact replacement): `packages/earnings-ingestion/tests/conftest.py`,
  `test_fetch_client.py`, `test_sec_client.py`, and `test_cohort_web.py`;
  `apps/earnings-pipeline/tests/test_cohort_cli.py`; and
  `tests/integration/test_sec_formats_live.py`.

**Interfaces:**

- Consumes: `fetch.client.ProcessLock`, unchanged.
- Produces:
  - `fetch/client.py`: `LOCK_DIR_VARIABLE = "EARNINGS_LOCK_DIR"`, and
    `machine_lock_dir() -> Path`;
  - `sec/client.py`: `LOCK_NAME = "sec-client.lock"`, and
    `open_sec_client(*, environ=None, max_requests=DEFAULT_MAX_REQUESTS, transport=None, clock=..., sleep=..., rng=None, now=...)`,
    with no `repo`;
  - `cohort/web.py`: `LOCK_NAME = "web-client.lock"`, and
    `open_web_client(hosts, *, environ=None, ...)`, with no `repo`;
  - the autouse fixture `machine_locks` in both suites' conftests.

  Every later task that opens a client calls these signatures.

- [x] **Step 1: Write the failing tests**

The new conftest for the application's tests holds only the lock fixture.

Create `apps/earnings-pipeline/tests/conftest.py`:

```python
"""Shared fixtures: a test's client locks never reach the user's cache (plan 7)."""

import pytest
from earnings_ingestion.fetch.client import LOCK_DIR_VARIABLE


@pytest.fixture(autouse=True)
def machine_locks(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The machine's lock directory, for this test only (plan 7, P7-5)."""
    monkeypatch.setenv(LOCK_DIR_VARIABLE, str(tmp_path_factory.mktemp("locks")))
```

Extract it with `python3 /tmp/plan7-extract.py apps/earnings-pipeline/tests/conftest.py`.

The other test changes are exact replacements:

- the package conftest gains the same autouse fixture;
- `test_sec_client.py` and `test_cohort_web.py` drop `tmp_path` from their helpers,
  and each gains `test_two_checkouts_share_one_lock`, which holds a client from one
  directory and runs a child process from another;
- `test_fetch_client.py` gains
  `test_the_lock_directory_is_the_users_cache_outside_every_checkout`;
- the CLI tests' fakes and the live format probe call the new signatures.

Create `/tmp/plan7-task1-tests.py`:

```python
"""Plan 7: exact replacements for 6 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/conftest.py": [
        (
            "\"\"\"Shared test data. Plan 5: a small completed capture, its layout payload, and\n"
            "builders for synthetic layout metadata. Plan 6: the synthetic cohort, and for\n"
            "pdftext-1 a PDF builder and the cohort with a PDF notice (Task 16b).\"\"\"\n"
            "\n"
            "import copy\n",
            "\"\"\"Shared test data. Plan 5: a small completed capture, its layout payload, and\n"
            "builders for synthetic layout metadata. Plan 6: the synthetic cohort, and for\n"
            "pdftext-1 a PDF builder and the cohort with a PDF notice (Task 16b). Plan 7: every\n"
            "test's client locks live in a fresh directory, never in the user's cache.\"\"\"\n"
            "\n"
            "import copy\n",
        ),
        (
            "    write_synthetic_cohort,\n"
            ")\n"
            "from earnings_ingestion.fetch.store import ArtifactStore\n"
            "\n",
            "    write_synthetic_cohort,\n"
            ")\n"
            "from earnings_ingestion.fetch.client import LOCK_DIR_VARIABLE\n"
            "from earnings_ingestion.fetch.store import ArtifactStore\n"
            "\n",
        ),
        (
            "    \"tables\": [],\n"
            "}\n"
            "\n"
            "\n",
            "    \"tables\": [],\n"
            "}\n"
            "\n"
            "\n"
            "@pytest.fixture(autouse=True)\n"
            "def machine_locks(\n"
            "    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch\n"
            ") -> None:\n"
            "    \"\"\"The machine's lock directory, for this test only: a client opened by a test\n"
            "    never takes, or waits on, the lock a live run holds (plan 7, P7-5).\"\"\"\n"
            "    monkeypatch.setenv(LOCK_DIR_VARIABLE, str(tmp_path_factory.mktemp(\"locks\")))\n"
            "\n"
            "\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_fetch_client.py": [
        (
            "import random\n"
            "import threading\n",
            "import random\n"
            "import sys\n"
            "import threading\n",
        ),
        (
            "from earnings_ingestion.fetch.client import (\n"
            "    AccessStop,\n",
            "from earnings_ingestion.fetch.client import (\n"
            "    LOCK_DIR_VARIABLE,\n"
            "    AccessStop,\n",
        ),
        (
            "    UnexpectedResponse,\n"
            "    require_identity,\n",
            "    UnexpectedResponse,\n"
            "    machine_lock_dir,\n"
            "    require_identity,\n",
        ),
        (
            "\n"
            "def test_concurrent_workers_share_one_allowance() -> None:\n",
            "\n"
            "def test_the_lock_directory_is_the_users_cache_outside_every_checkout(\n"
            "    tmp_path, monkeypatch\n"
            ") -> None:\n"
            "    monkeypatch.delenv(LOCK_DIR_VARIABLE)\n"
            "    monkeypatch.setenv(\"HOME\", str(tmp_path))\n"
            "    monkeypatch.setattr(sys, \"platform\", \"darwin\")\n"
            "    mac = tmp_path / \"Library\" / \"Caches\" / \"earnings-themes\" / \"locks\"\n"
            "    assert machine_lock_dir() == mac\n"
            "    monkeypatch.setattr(sys, \"platform\", \"linux\")\n"
            "    monkeypatch.delenv(\"XDG_CACHE_HOME\", raising=False)\n"
            "    assert machine_lock_dir() == tmp_path / \".cache\" / \"earnings-themes\" / \"locks\"\n"
            "    monkeypatch.setenv(\"XDG_CACHE_HOME\", \"relative/cache\")\n"
            "    assert machine_lock_dir() == tmp_path / \".cache\" / \"earnings-themes\" / \"locks\"\n"
            "    monkeypatch.setenv(\"XDG_CACHE_HOME\", str(tmp_path / \"xdg\"))\n"
            "    assert machine_lock_dir() == tmp_path / \"xdg\" / \"earnings-themes\" / \"locks\"\n"
            "    monkeypatch.setenv(LOCK_DIR_VARIABLE, str(tmp_path / \"override\"))\n"
            "    assert machine_lock_dir() == tmp_path / \"override\"\n"
            "\n"
            "\n"
            "def test_concurrent_workers_share_one_allowance() -> None:\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_sec_client.py": [
        (
            "import random\n"
            "import threading\n",
            "import random\n"
            "import subprocess\n"
            "import sys\n"
            "import threading\n",
        ),
        (
            "import pytest\n"
            "from earnings_ingestion.fetch.client import AccessStop\n"
            "from earnings_ingestion.sec.client import MIN_INTERVAL_SECONDS, open_sec_client\n"
            "from earnings_ingestion.sec.identifiers import Cik, pad_cik, unpad_cik\n",
            "import pytest\n"
            "from earnings_ingestion.fetch.client import AccessStop, machine_lock_dir\n"
            "from earnings_ingestion.sec.client import (\n"
            "    LOCK_NAME,\n"
            "    MIN_INTERVAL_SECONDS,\n"
            "    open_sec_client,\n"
            ")\n"
            "from earnings_ingestion.sec.identifiers import Cik, pad_cik, unpad_cik\n",
        ),
        (
            "\n"
            "def opened(tmp_path, handler, clock=None):\n"
            "    clock = clock or FakeClock()\n"
            "    return open_sec_client(\n"
            "        tmp_path,\n"
            "        environ=ENVIRON,\n",
            "\n"
            "def opened(handler, clock=None):\n"
            "    clock = clock or FakeClock()\n"
            "    return open_sec_client(\n"
            "        environ=ENVIRON,\n",
        ),
        (
            "\n"
            "def test_the_client_needs_an_identity(tmp_path) -> None:\n"
            "    with (\n"
            "        pytest.raises(AccessStop, match=\"EDGAR_IDENTITY\"),\n"
            "        open_sec_client(tmp_path, environ={}),\n"
            "    ):\n",
            "\n"
            "def test_the_client_needs_an_identity() -> None:\n"
            "    with (\n"
            "        pytest.raises(AccessStop, match=\"EDGAR_IDENTITY\"),\n"
            "        open_sec_client(environ={}),\n"
            "    ):\n",
        ),
        (
            "\n"
            "def test_one_client_per_machine(tmp_path) -> None:\n"
            "    def ok(request):\n"
            "        return httpx.Response(200, text=\"ok\")\n"
            "\n"
            "    with (\n"
            "        opened(tmp_path, ok),\n"
            "        pytest.raises(AccessStop, match=\"another client holds\"),\n"
            "        opened(tmp_path, ok),\n"
            "    ):\n"
            "        pass\n"
            "    with opened(tmp_path, ok):\n"
            "        pass\n",
            "\n"
            "def ok(request):\n"
            "    return httpx.Response(200, text=\"ok\")\n"
            "\n"
            "\n"
            "def test_one_client_per_machine() -> None:\n"
            "    with (\n"
            "        opened(ok),\n"
            "        pytest.raises(AccessStop, match=\"another client holds\"),\n"
            "        opened(ok),\n"
            "    ):\n"
            "        pass\n"
            "    with opened(ok):\n"
            "        pass\n",
        ),
        (
            "\n"
            "def test_the_client_reaches_sec_hosts_only(tmp_path) -> None:\n"
            "    with (\n"
            "        opened(tmp_path, lambda request: httpx.Response(200)) as client,\n"
            "        pytest.raises(AccessStop, match=\"outside this client's hosts\"),\n",
            "\n"
            "CHILD = \"\"\"\n"
            "import sys\n"
            "from earnings_ingestion.fetch.client import AccessStop\n"
            "from earnings_ingestion.sec.client import open_sec_client\n"
            "try:\n"
            "    with open_sec_client(environ={\"EDGAR_IDENTITY\": sys.argv[1]}):\n"
            "        print(\"opened\")\n"
            "except AccessStop as stop:\n"
            "    print(stop)\n"
            "\"\"\"\n"
            "\n"
            "\n"
            "def test_two_checkouts_share_one_lock(tmp_path, monkeypatch) -> None:\n"
            "    \"\"\"A second worktree or clone is another process in another directory. It finds\n"
            "    the lock this one holds, in the machine's lock directory (plan 6's deferred item).\n"
            "    \"\"\"\n"
            "    first, second = tmp_path / \"checkout-a\", tmp_path / \"checkout-b\"\n"
            "    first.mkdir()\n"
            "    second.mkdir()\n"
            "    monkeypatch.chdir(first)\n"
            "    with opened(ok):\n"
            "        child = subprocess.run(\n"
            "            [sys.executable, \"-c\", CHILD, IDENTITY],\n"
            "            cwd=second,\n"
            "            capture_output=True,\n"
            "            text=True,\n"
            "            check=True,\n"
            "        )\n"
            "    assert child.stdout.strip() == (\n"
            "        f\"another client holds {machine_lock_dir() / LOCK_NAME}\"\n"
            "    )\n"
            "\n"
            "\n"
            "def test_the_client_reaches_sec_hosts_only() -> None:\n"
            "    with (\n"
            "        opened(lambda request: httpx.Response(200)) as client,\n"
            "        pytest.raises(AccessStop, match=\"outside this client's hosts\"),\n",
        ),
        (
            "\n"
            "def test_the_client_refuses_a_sec_host_written_with_a_trailing_dot(tmp_path) -> None:\n"
            "    with (\n"
            "        opened(tmp_path, lambda request: httpx.Response(200)) as client,\n"
            "        pytest.raises(AccessStop, match=\"outside this client's hosts\"),\n",
            "\n"
            "def test_the_client_refuses_a_sec_host_written_with_a_trailing_dot() -> None:\n"
            "    with (\n"
            "        opened(lambda request: httpx.Response(200)) as client,\n"
            "        pytest.raises(AccessStop, match=\"outside this client's hosts\"),\n",
        ),
        (
            "\n"
            "def test_concurrent_workers_stay_at_or_below_two_requests_per_second(tmp_path) -> None:\n"
            "    \"\"\"Twelve workers alternate between www.sec.gov and data.sec.gov through the one\n",
            "\n"
            "def test_concurrent_workers_stay_at_or_below_two_requests_per_second() -> None:\n"
            "    \"\"\"Twelve workers alternate between www.sec.gov and data.sec.gov through the one\n",
        ),
        (
            "\n"
            "    with opened(tmp_path, handler) as client:\n"
            "        barrier = threading.Barrier(12)\n",
            "\n"
            "    with opened(handler) as client:\n"
            "        barrier = threading.Barrier(12)\n",
        ),
        (
            "\n"
            "def test_a_persistent_403_stops_without_rotating_identity(tmp_path) -> None:\n"
            "    agents = []\n",
            "\n"
            "def test_a_persistent_403_stops_without_rotating_identity() -> None:\n"
            "    agents = []\n",
        ),
        (
            "    with (\n"
            "        opened(tmp_path, handler) as client,\n"
            "        pytest.raises(AccessStop, match=\"403 persisted\"),\n",
            "    with (\n"
            "        opened(handler) as client,\n"
            "        pytest.raises(AccessStop, match=\"403 persisted\"),\n",
        ),
        (
            "\n"
            "def test_sec_block_page_stops_the_run(tmp_path) -> None:\n"
            "    def handler(request):\n",
            "\n"
            "def test_sec_block_page_stops_the_run() -> None:\n"
            "    def handler(request):\n",
        ),
        (
            "    with (\n"
            "        opened(tmp_path, handler) as client,\n"
            "        pytest.raises(AccessStop, match=\"block or rate-limit page\"),\n",
            "    with (\n"
            "        opened(handler) as client,\n"
            "        pytest.raises(AccessStop, match=\"block or rate-limit page\"),\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_cohort_web.py": [
        (
            "\"\"\"The cohort web client: registered hosts only, never SEC, robots.txt first.\"\"\"\n"
            "\n",
            "\"\"\"The cohort web client: registered hosts only, never SEC, robots.txt first, and\n"
            "one per machine.\"\"\"\n"
            "\n"
            "import subprocess\n"
            "import sys\n"
            "\n",
        ),
        (
            "from earnings_ingestion.cohort.web import (\n"
            "    RobotsRefusal,\n",
            "from earnings_ingestion.cohort.web import (\n"
            "    LOCK_NAME,\n"
            "    RobotsRefusal,\n",
        ),
        (
            ")\n"
            "from earnings_ingestion.fetch.client import AccessStop\n"
            "\n",
            ")\n"
            "from earnings_ingestion.fetch.client import AccessStop, machine_lock_dir\n"
            "\n",
        ),
        (
            "\n"
            "def opened(tmp_path, handler, hosts=(\"roster.example\",)):\n"
            "    return open_web_client(\n"
            "        tmp_path,\n"
            "        hosts,\n",
            "\n"
            "def opened(handler, hosts=(\"roster.example\",)):\n"
            "    return open_web_client(\n"
            "        hosts,\n",
        ),
        (
            "\n"
            "def test_an_allowed_page_is_fetched_after_robots(tmp_path) -> None:\n"
            "    seen = []\n",
            "\n"
            "def test_an_allowed_page_is_fetched_after_robots() -> None:\n"
            "    seen = []\n",
        ),
        (
            "\n"
            "    with opened(tmp_path, handler) as web:\n"
            "        fetched = web.fetch(\"https://roster.example/wiki/Roster?oldid=1\", {\"text/html\"})\n",
            "\n"
            "    with opened(handler) as web:\n"
            "        fetched = web.fetch(\"https://roster.example/wiki/Roster?oldid=1\", {\"text/html\"})\n",
        ),
        (
            "\n"
            "def test_a_disallowed_page_is_refused_unrequested(tmp_path) -> None:\n"
            "    seen = []\n",
            "\n"
            "def test_a_disallowed_page_is_refused_unrequested() -> None:\n"
            "    seen = []\n",
        ),
        (
            "    with (\n"
            "        opened(tmp_path, handler) as web,\n"
            "        pytest.raises(RobotsRefusal, match=\"Disallow: /w/\"),\n",
            "    with (\n"
            "        opened(handler) as web,\n"
            "        pytest.raises(RobotsRefusal, match=\"Disallow: /w/\"),\n",
        ),
        (
            "\n"
            "def test_an_unregistered_host_is_refused(tmp_path) -> None:\n"
            "    with opened(tmp_path, site) as web, pytest.raises(AccessStop, match=\"outside\"):\n"
            "        web.fetch(\"https://elsewhere.example/page\", {\"text/html\"})\n",
            "\n"
            "def test_an_unregistered_host_is_refused() -> None:\n"
            "    with opened(site) as web, pytest.raises(AccessStop, match=\"outside\"):\n"
            "        web.fetch(\"https://elsewhere.example/page\", {\"text/html\"})\n",
        ),
        (
            ")\n"
            "def test_sec_hosts_belong_to_the_sec_client(tmp_path, sec) -> None:\n"
            "    with (\n"
            "        pytest.raises(ValueError, match=\"shared SEC client\"),\n"
            "        opened(tmp_path, site, hosts=(\"roster.example\", sec)),\n"
            "    ):\n",
            ")\n"
            "def test_sec_hosts_belong_to_the_sec_client(sec) -> None:\n"
            "    with (\n"
            "        pytest.raises(ValueError, match=\"shared SEC client\"),\n"
            "        opened(site, hosts=(\"roster.example\", sec)),\n"
            "    ):\n",
        ),
        (
            "\n"
            "def test_an_identity_is_required(tmp_path) -> None:\n"
            "    with (\n"
            "        pytest.raises(AccessStop, match=\"SOURCE_IDENTITY\"),\n"
            "        open_web_client(tmp_path, [\"roster.example\"], environ={}),\n"
            "    ):\n"
            "        pass\n"
            "\n",
            "\n"
            "def test_an_identity_is_required() -> None:\n"
            "    with (\n"
            "        pytest.raises(AccessStop, match=\"SOURCE_IDENTITY\"),\n"
            "        open_web_client([\"roster.example\"], environ={}),\n"
            "    ):\n"
            "        pass\n"
            "\n"
            "\n"
            "CHILD = \"\"\"\n"
            "import sys\n"
            "from earnings_ingestion.cohort.web import open_web_client\n"
            "from earnings_ingestion.fetch.client import AccessStop\n"
            "try:\n"
            "    with open_web_client([\"roster.example\"], environ={\"SOURCE_IDENTITY\": sys.argv[1]}):\n"
            "        print(\"opened\")\n"
            "except AccessStop as stop:\n"
            "    print(stop)\n"
            "\"\"\"\n"
            "\n"
            "\n"
            "def test_two_checkouts_share_one_lock(tmp_path, monkeypatch) -> None:\n"
            "    \"\"\"A second worktree or clone is another process in another directory. It finds\n"
            "    the lock this one holds, in the machine's lock directory (plan 6's deferred item).\n"
            "    \"\"\"\n"
            "    first, second = tmp_path / \"checkout-a\", tmp_path / \"checkout-b\"\n"
            "    first.mkdir()\n"
            "    second.mkdir()\n"
            "    monkeypatch.chdir(first)\n"
            "    with opened(site):\n"
            "        child = subprocess.run(\n"
            "            [sys.executable, \"-c\", CHILD, ENVIRON[\"SOURCE_IDENTITY\"]],\n"
            "            cwd=second,\n"
            "            capture_output=True,\n"
            "            text=True,\n"
            "            check=True,\n"
            "        )\n"
            "    assert child.stdout.strip() == (\n"
            "        f\"another client holds {machine_lock_dir() / LOCK_NAME}\"\n"
            "    )\n"
            "\n",
        ),
    ],
    "apps/earnings-pipeline/tests/test_cohort_cli.py": [
        (
            "    @contextmanager\n"
            "    def fake_open(repo_path):\n"
            "        yield FakeSec()\n",
            "    @contextmanager\n"
            "    def fake_open():\n"
            "        yield FakeSec()\n",
        ),
        (
            "    @contextmanager\n"
            "    def fake_open(repo_path, hosts):\n"
            "        assert hosts == [\"index.example\"]\n",
            "    @contextmanager\n"
            "    def fake_open(hosts):\n"
            "        assert hosts == [\"index.example\"]\n",
        ),
    ],
    "tests/integration/test_sec_formats_live.py": [
        (
            "import os\n"
            "from pathlib import Path\n"
            "\n",
            "import os\n"
            "\n",
        ),
        (
            "pytestmark = pytest.mark.live\n"
            "REPO = Path(__file__).resolve().parents[2]\n"
            "JSON = frozenset({\"application/json\"})\n",
            "pytestmark = pytest.mark.live\n"
            "JSON = frozenset({\"application/json\"})\n",
        ),
        (
            "    ticker, cik, name = COMPANY\n"
            "    with open_sec_client(REPO, max_requests=MAX_REQUESTS) as client:\n"
            "        entries = read_company_tickers(client.fetch(COMPANY_TICKERS_URL, JSON).body)\n",
            "    ticker, cik, name = COMPANY\n"
            "    with open_sec_client(max_requests=MAX_REQUESTS) as client:\n"
            "        entries = read_company_tickers(client.fetch(COMPANY_TICKERS_URL, JSON).body)\n",
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

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_client.py packages/earnings-ingestion/tests/test_sec_client.py packages/earnings-ingestion/tests/test_cohort_web.py apps -q`

Expected: an `ImportError while loading conftest`, ending
`E   ImportError: cannot import name 'LOCK_DIR_VARIABLE' from 'earnings_ingestion.fetch.client'`.

- [x] **Step 3: Move the locks**

Create `/tmp/plan7-task1-source.py`:

```python
"""Plan 7: exact replacements for 6 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py": [
        (
            "identity is never changed. The identity is sent as the User-Agent and never recorded.\n"
            "\"\"\"\n",
            "identity is never changed. The identity is sent as the User-Agent and never recorded.\n"
            "\n"
            "Each package client holds its lock in ``machine_lock_dir()``, one directory per user\n"
            "outside every checkout, so one client runs per machine however many worktrees or\n"
            "clones exist.\n"
            "\"\"\"\n",
        ),
        (
            "import re\n"
            "import threading\n",
            "import re\n"
            "import sys\n"
            "import threading\n",
        ),
        (
            "BLOCK_SCAN_BYTES = 20_000\n"
            "\n",
            "BLOCK_SCAN_BYTES = 20_000\n"
            "LOCK_DIR_VARIABLE = \"EARNINGS_LOCK_DIR\"\n"
            "\n",
        ),
        (
            "    return value\n"
            "\n",
            "    return value\n"
            "\n"
            "\n"
            "def machine_lock_dir() -> Path:\n"
            "    \"\"\"Where every package client's lock lives: one directory per user, outside\n"
            "    every checkout (plan 7, P7-5).\n"
            "\n"
            "    ``$EARNINGS_LOCK_DIR`` overrides it, for tests. Otherwise it is the user's cache:\n"
            "    ``~/Library/Caches/earnings-themes/locks`` on macOS, and elsewhere\n"
            "    ``$XDG_CACHE_HOME/earnings-themes/locks``, or ``~/.cache`` when that variable is\n"
            "    unset or not absolute.\n"
            "    \"\"\"\n"
            "    override = os.environ.get(LOCK_DIR_VARIABLE)\n"
            "    if override:\n"
            "        return Path(override)\n"
            "    if sys.platform == \"darwin\":\n"
            "        return Path.home() / \"Library\" / \"Caches\" / \"earnings-themes\" / \"locks\"\n"
            "    xdg = os.environ.get(\"XDG_CACHE_HOME\", \"\")\n"
            "    cache = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / \".cache\"\n"
            "    return cache / \"earnings-themes\" / \"locks\"\n"
            "\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/sec/client.py": [
        (
            "- **One per machine.** ``open_sec_client`` holds the SEC lock while the client is open,\n"
            "  so a second client stops instead of opening, in this process or another. Share the\n"
            "  one instance across workers: its throttle is thread-safe.\n"
            "- **2 requests per second.** Request starts are spaced 0.5 s apart across every SEC\n",
            "- **One per machine.** ``open_sec_client`` holds the SEC lock while the client is open,\n"
            "  so a second client stops instead of opening, in this process or another, from this\n"
            "  checkout or any other. Share the one instance across workers: its throttle is\n"
            "  thread-safe.\n"
            "- **2 requests per second.** Request starts are spaced 0.5 s apart across every SEC\n",
        ),
        (
            "Two limits remain, because A §398 asks for coordination across the outbound network.\n"
            "The lock coordinates the processes of one machine only. Stage 1's frozen harness keeps\n"
            "its own client and lock, so it must never run live at the same time.\n"
            "\"\"\"\n",
            "Two limits remain, because A §398 asks for coordination across the outbound network.\n"
            "The lock lives in ``machine_lock_dir()``, outside every checkout, so it coordinates the\n"
            "processes of one machine, every worktree and clone included, and no more. Stage 1's\n"
            "frozen harness keeps its own client and lock, so it must never run live at the same\n"
            "time.\n"
            "\"\"\"\n",
        ),
        (
            "from datetime import UTC, datetime\n"
            "from pathlib import Path\n"
            "\n",
            "from datetime import UTC, datetime\n"
            "\n",
        ),
        (
            "    Throttle,\n"
            "    require_identity,\n",
            "    Throttle,\n"
            "    machine_lock_dir,\n"
            "    require_identity,\n",
        ),
        (
            "BLOCK_MARKERS = (b\"undeclared automated tool\", b\"request rate threshold exceeded\")\n"
            "LOCK_PATH = Path(\"data\") / \"runs\" / \"sec\" / \"sec-client.lock\"\n"
            "\"\"\"Relative to the repository root. Every package client uses this one path.\"\"\"\n"
            "\n",
            "BLOCK_MARKERS = (b\"undeclared automated tool\", b\"request rate threshold exceeded\")\n"
            "LOCK_NAME = \"sec-client.lock\"\n"
            "\"\"\"In ``machine_lock_dir()``: every SEC client on this machine takes this one lock.\"\"\"\n"
            "\n",
        ),
        (
            "def open_sec_client(\n"
            "    repo: Path,\n"
            "    *,\n",
            "def open_sec_client(\n"
            "    *,\n",
        ),
        (
            ") -> Iterator[SecClient]:\n"
            "    \"\"\"The machine's one SEC client, holding the SEC lock under ``repo`` while open.\"\"\"\n"
            "    identity = require_identity(IDENTITY_ENV, environ)\n"
            "    with ProcessLock(repo / LOCK_PATH):\n"
            "        throttle = Throttle(\n",
            ") -> Iterator[SecClient]:\n"
            "    \"\"\"The machine's one SEC client, holding the SEC lock while open.\"\"\"\n"
            "    identity = require_identity(IDENTITY_ENV, environ)\n"
            "    with ProcessLock(machine_lock_dir() / LOCK_NAME):\n"
            "        throttle = Throttle(\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/cohort/web.py": [
        (
            "  never bypasses robots restrictions).\n"
            "\"\"\"\n",
            "  never bypasses robots restrictions).\n"
            "- **One per machine.** Its lock lives in ``machine_lock_dir()``, outside every\n"
            "  checkout, like the SEC client's.\n"
            "\"\"\"\n",
        ),
        (
            "from datetime import UTC, datetime\n"
            "from pathlib import Path\n"
            "from urllib.parse import urlsplit\n",
            "from datetime import UTC, datetime\n"
            "from urllib.parse import urlsplit\n",
        ),
        (
            "    Throttle,\n"
            "    require_identity,\n",
            "    Throttle,\n"
            "    machine_lock_dir,\n"
            "    require_identity,\n",
        ),
        (
            "MIN_INTERVAL_SECONDS = 1.0\n"
            "LOCK_PATH = Path(\"data\") / \"runs\" / \"cohort\" / \"web-client.lock\"\n"
            "\n",
            "MIN_INTERVAL_SECONDS = 1.0\n"
            "LOCK_NAME = \"web-client.lock\"\n"
            "\"\"\"In ``machine_lock_dir()``: every cohort web client on this machine takes it.\"\"\"\n"
            "\n",
        ),
        (
            "def open_web_client(\n"
            "    repo: Path,\n"
            "    hosts: Iterable[str],\n",
            "def open_web_client(\n"
            "    hosts: Iterable[str],\n",
        ),
        (
            "    identity = require_identity(IDENTITY_ENV, environ)\n"
            "    with ProcessLock(repo / LOCK_PATH):\n"
            "        throttle = Throttle(\n",
            "    identity = require_identity(IDENTITY_ENV, environ)\n"
            "    with ProcessLock(machine_lock_dir() / LOCK_NAME):\n"
            "        throttle = Throttle(\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py": [
        (
            "    with (\n"
            "        open_web_client(repo, web_hosts, environ=environ) as web,\n"
            "        open_sec_client(repo, environ=environ) as sec,\n"
            "    ):\n",
            "    with (\n"
            "        open_web_client(web_hosts, environ=environ) as web,\n"
            "        open_sec_client(environ=environ) as sec,\n"
            "    ):\n",
        ),
    ],
    "apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py": [
        (
            "    try:\n"
            "        with open_web_client(layout.repo, hosts) as web:\n"
            "            for url in urls:\n",
            "    try:\n"
            "        with open_web_client(hosts) as web:\n"
            "            for url in urls:\n",
        ),
        (
            "    try:\n"
            "        with open_sec_client(layout.repo) as sec:\n"
            "            result = fetch_sec(sec.fetch, layout.store(), layout.registers(), config)\n",
            "    try:\n"
            "        with open_sec_client() as sec:\n"
            "            result = fetch_sec(sec.fetch, layout.store(), layout.registers(), config)\n",
        ),
        (
            "        return\n"
            "    layout: Layout = context.obj\n"
            "    host = urlsplit(url).hostname or \"\"\n",
            "        return\n"
            "    host = urlsplit(url).hostname or \"\"\n",
        ),
        (
            "        if is_sec_host(host):\n"
            "            with open_sec_client(layout.repo) as sec:\n"
            "                fetched = sec.fetch(url, ANY)\n"
            "        else:\n"
            "            with open_web_client(layout.repo, [host]) as web:\n"
            "                fetched = web.fetch(url, ANY)\n",
            "        if is_sec_host(host):\n"
            "            with open_sec_client() as sec:\n"
            "                fetched = sec.fetch(url, ANY)\n"
            "        else:\n"
            "            with open_web_client([host]) as web:\n"
            "                fetched = web.fetch(url, ANY)\n",
        ),
    ],
    "docs/verification/djia-cohort.md": [
        (
            "  - intervals are resolved to the day.\n"
            "- **One checkout.** The SEC and web client locks live under each checkout's\n"
            "  `data/runs/`, so they coordinate the processes of one checkout, not the whole\n"
            "  machine. A second worktree or clone takes locks of its own, and two could together\n"
            "  send more than 2 requests per second. Until the locks move to one place per\n"
            "  machine (`specs/deferred_items.md`), send SEC requests from one checkout at a time.\n"
            "  Stage 1's harness client must never run live beside a package client.\n"
            "- **`acceptanceDateTime`.** The readers take SEC's offset as written. Whether the\n",
            "  - intervals are resolved to the day.\n"
            "- **One machine.** The SEC and web client locks live in the user's cache directory,\n"
            "  outside every checkout (plan 7, which moved them from each checkout's `data/runs/`),\n"
            "  so every worktree and clone on a machine shares them. A lock coordinates one\n"
            "  machine's processes and no more. Stage 1's harness client keeps its own lock, so it\n"
            "  must never run live beside a package client.\n"
            "- **`acceptanceDateTime`.** The readers take SEC's offset as written. Whether the\n",
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

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_client.py packages/earnings-ingestion/tests/test_sec_client.py packages/earnings-ingestion/tests/test_cohort_web.py apps -q`

Expected: `60 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py packages/earnings-ingestion/src/earnings_ingestion/sec/client.py packages/earnings-ingestion/src/earnings_ingestion/cohort/web.py packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py apps/earnings-pipeline/tests/*.py packages/earnings-ingestion/tests/conftest.py packages/earnings-ingestion/tests/test_fetch_client.py packages/earnings-ingestion/tests/test_sec_client.py packages/earnings-ingestion/tests/test_cohort_web.py tests/integration/test_sec_formats_live.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `939 passed, 24 deselected`; `All checks passed!` and
`212 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py packages/earnings-ingestion/src/earnings_ingestion/sec/client.py packages/earnings-ingestion/src/earnings_ingestion/cohort/web.py packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py apps/earnings-pipeline/tests packages/earnings-ingestion/tests/conftest.py packages/earnings-ingestion/tests/test_fetch_client.py packages/earnings-ingestion/tests/test_sec_client.py packages/earnings-ingestion/tests/test_cohort_web.py tests/integration/test_sec_formats_live.py docs/verification/djia-cohort.md
git commit -m "fix(fetch): hold the SEC and web client locks once per machine"
```

---

### Task 2: Two robustness fixes in code Stage 5 relies on

S §Prerequisites, item 4: parts 2 and 3 of plan 6's deferred item "Three robustness
fixes in the cohort path". Stage 5 reads every candidate issuer's submissions and
sends several hundred requests, so both paths matter here.

- **`read_submissions`** raises `SecDataError`, never `KeyError` or `TypeError`, on
  a `formerNames` or `filings.files` entry that is not an object with a text `name`,
  and on a `from`, `to`, or `name` that is not text. It refuses a string `tickers`,
  which it would otherwise read character by character.
- **`retry_after_seconds`** ignores a `Retry-After` value of non-ASCII digits.
  `str.isdigit` accepts them all. `float` then raises on a superscript two, and
  silently reads fullwidth or Arabic-Indic digits as a number of seconds. HTTP
  allows only ASCII digits there, so such a value is ignored: never obeyed, and
  never an error.

Part 1 of the deferred item, the cohort CLI's tracebacks, is not in Stage 5's path.
Completion restates it as its own open item (S §Deferred items).

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/sec/data.py` and
  `fetch/client.py`.
- Test (modify, by exact replacement): `packages/earnings-ingestion/tests/test_sec_data.py`
  and `test_fetch_client.py`.

**Interfaces:**

- Consumes: Task 1's `fetch/client.py`.
- Produces, in `sec/data.py`: the private helpers `_named(entry, where) -> dict`,
  `_optional_text(value, where) -> str | None`, and `_former_name(entry, index)`,
  which Task 4's `_older_page` reuses.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan7-task2-tests.py`:

```python
"""Plan 7: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_sec_data.py": [
        (
            "\n"
            "def test_ragged_filing_columns_are_refused() -> None:\n",
            "\n"
            "def pages(entries: list) -> bytes:\n"
            "    \"\"\"The submissions file with ``entries`` as its ``filings.files``.\"\"\"\n"
            "    data = json.loads(submissions())\n"
            "    data[\"filings\"][\"files\"] = entries\n"
            "    return json.dumps(data).encode()\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\n"
            "    \"body\",\n"
            "    [\n"
            "        submissions(formerNames=[\"ACME WIDGETS INC\"]),\n"
            "        submissions(formerNames=[{\"from\": \"2001-01-01T00:00:00.000Z\"}]),\n"
            "        submissions(formerNames=[{\"name\": 7}]),\n"
            "        submissions(tickers=\"ACME\"),\n"
            "        submissions(tickers=[\"ACME\", 7]),\n"
            "        pages([\"CIK0009990001-submissions-001.json\"]),\n"
            "        pages([{\"filingCount\": 3}]),\n"
            "        pages([{\"name\": 3}]),\n"
            "    ],\n"
            "    ids=[\n"
            "        \"former-name-not-an-object\",\n"
            "        \"former-name-without-a-name\",\n"
            "        \"former-name-not-text\",\n"
            "        \"tickers-a-string\",\n"
            "        \"ticker-not-text\",\n"
            "        \"page-not-an-object\",\n"
            "        \"page-without-a-name\",\n"
            "        \"page-name-not-text\",\n"
            "    ],\n"
            ")\n"
            "def test_a_malformed_registrant_is_refused_as_sec_data(body) -> None:\n"
            "    \"\"\"Plan 6's deferred robustness fix: a changed shape raises SecDataError, never\n"
            "    KeyError or TypeError, and a string of tickers is not read as characters.\"\"\"\n"
            "    with pytest.raises(SecDataError):\n"
            "        read_submissions(body)\n"
            "\n"
            "\n"
            "def test_ragged_filing_columns_are_refused() -> None:\n",
        ),
    ],
    "packages/earnings-ingestion/tests/test_fetch_client.py": [
        (
            "\n"
            "def test_fetch_returns_decoded_bytes_and_a_retrieval() -> None:\n",
            "\n"
            "@pytest.mark.parametrize(\n"
            "    \"value\",\n"
            "    [chr(0xB2), chr(0xFF11) + chr(0xFF12), chr(0x0661) + chr(0x0660)],\n"
            "    ids=[\"superscript-two\", \"fullwidth-twelve\", \"arabic-indic-ten\"],\n"
            ")\n"
            "def test_retry_after_ignores_non_ascii_digits(value) -> None:\n"
            "    \"\"\"Plan 6's deferred robustness fix: a header of other scripts' digits is\n"
            "    unreadable, so it is ignored, never obeyed and never an error.\"\"\"\n"
            "    assert retry_after_seconds(value, NOW) is None\n"
            "\n"
            "\n"
            "def test_fetch_returns_decoded_bytes_and_a_retrieval() -> None:\n",
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

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_sec_data.py packages/earnings-ingestion/tests/test_fetch_client.py -q`

Expected: FAIL: `11 failed, 29 passed`. The malformed registrants raise `TypeError`
or `KeyError: 'name'`, or read without complaint (`DID NOT RAISE SecDataError`). The
superscript two raises `ValueError: could not convert string to float`, and the other
two digit strings are obeyed (`assert 12.0 is None`, `assert 10.0 is None`).

- [x] **Step 3: Refuse the malformed shapes, and ignore the digits**

Create `/tmp/plan7-task2-source.py`:

```python
"""Plan 7: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/sec/data.py": [
        (
            "\n"
            "def read_submissions(body: bytes) -> Registrant:\n",
            "\n"
            "def _named(entry: object, where: str) -> dict:\n"
            "    \"\"\"``entry`` if it is an object whose ``name`` is text.\"\"\"\n"
            "    if not isinstance(entry, dict) or not isinstance(entry.get(\"name\"), str):\n"
            "        raise SecDataError(f\"{where} is not an object with a text name\")\n"
            "    return entry\n"
            "\n"
            "\n"
            "def _optional_text(value: object, where: str) -> str | None:\n"
            "    if value is not None and not isinstance(value, str):\n"
            "        raise SecDataError(f\"{where} is not text\")\n"
            "    return value\n"
            "\n"
            "\n"
            "def _former_name(entry: object, index: int) -> FormerName:\n"
            "    pointer = f\"/formerNames/{index}\"\n"
            "    entry = _named(entry, pointer)\n"
            "    return FormerName(\n"
            "        name=entry[\"name\"],\n"
            "        valid_from=_optional_text(entry.get(\"from\"), f\"{pointer}/from\"),\n"
            "        valid_to=_optional_text(entry.get(\"to\"), f\"{pointer}/to\"),\n"
            "        pointer=pointer,\n"
            "    )\n"
            "\n"
            "\n"
            "def read_submissions(body: bytes) -> Registrant:\n",
        ),
        (
            "        raise SecDataError(\"the submissions file has no filings.recent\")\n"
            "    former = data.get(\"formerNames\") or []\n",
            "        raise SecDataError(\"the submissions file has no filings.recent\")\n"
            "    tickers = data[\"tickers\"]\n"
            "    if not isinstance(tickers, list) or not all(isinstance(t, str) for t in tickers):\n"
            "        raise SecDataError(\"tickers is not a list of text\")\n"
            "    former = data.get(\"formerNames\") or []\n",
        ),
        (
            "        name=str(data[\"name\"]),\n"
            "        tickers=tuple(str(ticker) for ticker in data[\"tickers\"]),\n"
            "        former_names=tuple(\n"
            "            FormerName(\n"
            "                name=str(entry[\"name\"]),\n"
            "                valid_from=entry.get(\"from\"),\n"
            "                valid_to=entry.get(\"to\"),\n"
            "                pointer=f\"/formerNames/{index}\",\n"
            "            )\n"
            "            for index, entry in enumerate(former)\n"
            "        ),\n"
            "        filings=read_filing_columns(filings[\"recent\"], \"/filings/recent\"),\n"
            "        older_pages=tuple(str(page[\"name\"]) for page in older),\n"
            "    )\n",
            "        name=str(data[\"name\"]),\n"
            "        tickers=tuple(tickers),\n"
            "        former_names=tuple(\n"
            "            _former_name(entry, index) for index, entry in enumerate(former)\n"
            "        ),\n"
            "        filings=read_filing_columns(filings[\"recent\"], \"/filings/recent\"),\n"
            "        older_pages=tuple(\n"
            "            _named(page, f\"/filings/files/{index}\")[\"name\"]\n"
            "            for index, page in enumerate(older)\n"
            "        ),\n"
            "    )\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py": [
        (
            "def retry_after_seconds(value: str | None, now: datetime) -> float | None:\n"
            "    \"\"\"The wait a ``Retry-After`` header asks for, in seconds, or None if unreadable.\"\"\"\n"
            "    if not value:\n",
            "def retry_after_seconds(value: str | None, now: datetime) -> float | None:\n"
            "    \"\"\"The wait a ``Retry-After`` header asks for, in seconds, or None if unreadable.\n"
            "\n"
            "    Only ASCII digits are seconds: ``str.isdigit`` also admits other scripts' digits,\n"
            "    which ``float`` would read or refuse, and HTTP means neither.\n"
            "    \"\"\"\n"
            "    if not value:\n",
        ),
        (
            "    value = value.strip()\n"
            "    if value.isdigit():\n"
            "        return float(value)\n",
            "    value = value.strip()\n"
            "    if value.isascii() and value.isdigit():\n"
            "        return float(value)\n",
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

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_sec_data.py packages/earnings-ingestion/tests/test_fetch_client.py -q`

Expected: `40 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/sec/data.py packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py packages/earnings-ingestion/tests/test_sec_data.py packages/earnings-ingestion/tests/test_fetch_client.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `950 passed, 24 deselected`; `All checks passed!` and
`212 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/sec/data.py packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py packages/earnings-ingestion/tests/test_sec_data.py packages/earnings-ingestion/tests/test_fetch_client.py
git commit -m "fix(sec): refuse malformed submissions and non-ASCII Retry-After digits"
```

---

### Task 3: The universe's operative identity

S §Prerequisites, item 2, EV4, and the deferred item "Give the universe manifest an
operative identity". v1's `content_hash` covers withheld evidence, the SEC records its
identities cite, and the register's version. So curating a notice published after
the cutoff, re-fetching an SEC record, or editing a register entry makes a new cohort
version whose facts are unchanged. Stage 5's records key on `operative_hash`, which
covers only the facts an event's eligibility can read.

- **The projection** holds the definition's window, cutoff, membership reference, and
  selection policy; every interval, whole; the mapping of each security that has an
  interval (P7-4); each issuer's CIK and securities; and the candidate issuers.
- **The tests** run on the synthetic cohort's builder, through Stage 4's `cohort_repo`
  fixture: a private copy of a repository that `write_synthetic_cohort` generated.
  - a withheld notice, a re-fetched SEC record, and a register edit each change the
    content hash but not the operative hash;
  - a moved bound, a changed mapping, and a new supporting assertion each change
    both;
  - v1 and the synthetic manifest load unchanged, and their operative hashes are
    pinned.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/identity.py`.
- Test (create): `packages/earnings-ingestion/tests/test_cohort_identity.py`.

**Interfaces:**

- Consumes: `cohort.digests.digest`; `cohort.records.UniverseManifest`;
  `cohort.build.build` and `EPOCH`; `cohort.freeze.load_manifest`;
  `cohort.synthetic.FIXTURE_DIR` and `build_options`; the `cohort_repo` fixture.
- Produces, in `cohort/identity.py`:
  - `DEFINITION`, the definition fields projected;
  - `operative_projection(manifest: UniverseManifest) -> dict`;
  - `operative_hash(manifest: UniverseManifest) -> str`, 64 lowercase hex.

  Tasks 12 and 14 record it, and Task 14's chain check compares it. v1's is
  `c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573`, and the
  synthetic cohort's is
  `57dcc2eb3d5f98e38717c54f9e2dc5419beca02f15fda04d2cb384d93358ae5c`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_cohort_identity.py`:

```python
"""The universe's operative identity (plan 7, EV4): evidence that decides no event
leaves it unchanged, and every fact an event's eligibility reads changes it."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.cohort.build import EPOCH, build
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.identity import operative_hash, operative_projection
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, build_options
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.urls import submissions_url

ROOT = Path(__file__).resolve().parents[3]
V1 = ROOT / "config" / "universe" / "djia" / "manifests" / "djia-2024q3-2026q2-v1.json"
SYNTHETIC = ROOT / FIXTURE_DIR / "manifests" / "djia-synthetic-v1.json"
OPTIONS = build_options()


def hashes(repo: Path) -> tuple[str, str]:
    """The build's content hash and operative hash."""
    built = build(repo, **OPTIONS)
    return built.content_hash, operative_hash(built.manifest(1, EPOCH))


def edit(repo: Path, name: str, old: str, new: str) -> None:
    path = repo / FIXTURE_DIR / name
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    path.write_text(text.replace(old, new), encoding="utf-8")


def change_block(repo: Path, evidence_id: str) -> str:
    """The ``[[changes]]`` table for ``evidence_id``, with its entries."""
    text = (repo / FIXTURE_DIR / "evidence.toml").read_text(encoding="utf-8")
    start = text.index(f'[[changes]]\nevidence_id = "{evidence_id}"')
    ends = [text.find(marker, start + 1) for marker in ("[[changes]]", "[[checks]]")]
    return text[start : min(end for end in ends if end != -1)]


@pytest.fixture
def repo(cohort_repo: Path) -> Path:
    return cohort_repo


def test_a_withheld_notice_changes_the_content_but_not_the_identity(repo) -> None:
    """The notice of 2026-09-25 was published after the cutoff. It names Fenwick,
    whose unresolved mapping has no interval, so it decides no event."""
    before = hashes(repo)
    edit(repo, "evidence.toml", change_block(repo, "index-2026-09-25"), "")
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] == before[1]


def test_a_refetched_sec_record_changes_the_content_but_not_the_identity(
    repo,
) -> None:
    before = hashes(repo)
    store = ArtifactStore(repo / FIXTURE_DIR / "raw", repo)
    url = submissions_url(9990001)
    old = store.latest(
        "sec-edgar",
        url,
        rights_status=RightsStatus.REDISTRIBUTABLE,
        rights_basis="synthetic",
    )
    body = json.dumps(json.loads(old.body), indent=1).encode()
    retrieval = Retrieval(
        request_url=url,
        final_url=url,
        retrieved_at=datetime(2026, 9, 28, 12, 0, tzinfo=UTC),
        retrieval_method=RetrievalMethod.HTTP,
        http_status=200,
        media_type="application/json",
        content_type="application/json",
        byte_count=len(body),
        sha256=sha256_hex(body),
    )
    store.put(
        "sec-edgar",
        body,
        retrieval,
        rights_status=RightsStatus.REDISTRIBUTABLE,
        rights_basis="synthetic",
    )
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] == before[1]


def test_a_register_edit_changes_the_content_but_not_the_identity(repo) -> None:
    """Plan 7 edits the sec-edgar entry, as the spec asks: the source register's
    version is in the content hash, never in the identity (P7-3)."""
    before = hashes(repo)
    edit(repo, "source-register.toml", 'owner = "Synthetic SEC"', 'owner = "SEC"')
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] == before[1]


def test_a_moved_bound_changes_both(repo) -> None:
    before = hashes(repo)
    edit(
        repo, "evidence.toml", "effective_on = 2026-06-22", "effective_on = 2026-06-23"
    )
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] != before[1]


def test_a_changed_mapping_changes_both(repo) -> None:
    before = hashes(repo)
    edit(repo, "overrides.toml", 'cik = "0009990006"', 'cik = "0009990007"')
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] != before[1]


def test_a_new_supporting_assertion_changes_both(repo) -> None:
    """A second notice restating the change of 2024-11-01 merges into its intervals,
    which then rest on one more assertion."""
    before = hashes(repo)
    block = change_block(repo, "index-2024-11-01")
    restated = block.replace(
        'evidence_id = "index-2024-11-01"', 'evidence_id = "index-2024-11-01-restated"'
    )
    edit(repo, "evidence.toml", "[[checks]]", f"{restated}[[checks]]")
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] != before[1]


def test_the_projection_holds_only_the_cutoff_admissible_facts() -> None:
    manifest = load_manifest(SYNTHETIC)
    projection = operative_projection(manifest)
    assert sorted(projection) == [
        "candidate_issuer_ids",
        "definition",
        "intervals",
        "issuers",
        "mappings",
    ]
    assert sorted(projection["definition"]) == [
        "membership_reference",
        "period_end_start",
        "period_end_stop",
        "public_information_cutoff",
        "selection_policy_version",
        "universe_id",
        "universe_name",
    ]
    assert "fenwick-common" not in {m["security_id"] for m in projection["mappings"]}


def test_v1_loads_unchanged_and_has_an_operative_hash() -> None:
    v1 = load_manifest(V1)
    assert v1.definition.content_hash == (
        "2d9743945dc5748fccec4c4963f6fa891a41e8863d56e99841569ff25fa884b4"
    )
    assert operative_hash(v1) == (
        "c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573"
    )
    assert operative_hash(load_manifest(SYNTHETIC)) == (
        "57dcc2eb3d5f98e38717c54f9e2dc5419beca02f15fda04d2cb384d93358ae5c"
    )
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_cohort_identity.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_identity.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.cohort.identity'`.

- [x] **Step 3: Write the projection**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/identity.py`:

```python
"""The universe's operative identity (plan 7; EV4 of the Stage 5 spec).

A manifest's ``content_hash`` covers everything it holds: withheld evidence, the SEC
records its identities cite, and the source register's version. So curating a notice
published after the cutoff, re-fetching an SEC record, or editing a register entry
makes a new version whose facts are unchanged.

``operative_hash`` covers only the cutoff-admissible facts that an event's
eligibility can read, and Stage 5's records key on it:

- the definition's window, cutoff, membership reference, and selection policy;
- every interval, with both bounds, their timing and basis, and its assertions;
- the mapping of each security that has an interval: its status, issuer, and CIK;
- each issuer's CIK and securities, and the candidate issuers.

A security named only by evidence the cutoff withholds has no interval, so its
mapping decides no event and is left out (plan 7, P7-4).
"""

from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import UniverseManifest

DEFINITION = (
    "universe_id",
    "universe_name",
    "period_end_start",
    "period_end_stop",
    "public_information_cutoff",
    "membership_reference",
    "selection_policy_version",
)


def operative_projection(manifest: UniverseManifest) -> dict:
    """The facts ``operative_hash`` covers, as canonical-JSON-ready data."""
    definition = manifest.definition.model_dump(mode="json", include=set(DEFINITION))
    intervals = sorted(
        manifest.intervals, key=lambda i: (i.security_id, i.effective_from)
    )
    with_interval = {interval.security_id for interval in intervals}
    return {
        "definition": definition,
        "intervals": [interval.model_dump(mode="json") for interval in intervals],
        "mappings": [
            mapping.model_dump(
                mode="json", include={"security_id", "status", "issuer_id", "cik"}
            )
            for mapping in sorted(manifest.mappings, key=lambda m: m.security_id)
            if mapping.security_id in with_interval
        ],
        "issuers": [
            issuer.model_dump(mode="json", include={"issuer_id", "cik", "security_ids"})
            for issuer in sorted(manifest.issuers, key=lambda i: i.issuer_id)
        ],
        "candidate_issuer_ids": sorted(manifest.candidate_issuer_ids),
    }


def operative_hash(manifest: UniverseManifest) -> str:
    """SHA-256 of the canonical JSON of ``operative_projection(manifest)``."""
    return digest(operative_projection(manifest))
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/cohort/identity.py`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_identity.py -q`

Expected: `8 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/identity.py packages/earnings-ingestion/tests/test_cohort_identity.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `958 passed, 24 deselected`; `All checks passed!` and
`214 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/cohort/identity.py packages/earnings-ingestion/tests/test_cohort_identity.py
git commit -m "feat(cohort): give the universe an operative identity"
```

---

### Task 4: SEC's readers for items, older pages, index pages, and companyfacts

S §Store, client, and readers. Discovery and the build read four more things from
SEC, each through a pure function of saved bytes that raises `SecDataError` on any
other shape (A §407).

- **Submissions** (`sec/data.py`).
  - Each `Filing` gains `items`, the 8-K items SEC lists, from the optional `items`
    column. A file without the column, like Stage 4's synthetic ones, reads as
    before, with no items.
  - Each older page becomes an `OlderPage` with its `filingFrom` and `filingTo`, both
    optional, so what Stage 4 accepts does not change. The two callers that fetch
    older pages now use `page.name`.
  - `_load` becomes public as `load_json`, since the companyfacts reader uses it.
- **URLs** (`sec/urls.py`): `companyfacts_url(cik)` and `filing_index_url(cik,
  accession)`, EDGAR's `<accession>-index.htm`.
- **Index pages** (`sec/filing_index.py`), ported from Stage 1's
  `parse_filing_index` (`expirements/parser-fidelity/discover.py`), never imported:
  - the header: the form, the accession, the filing date, "Accepted", "Period of
    Report", and "Items";
  - the Document Format Files table: sequence, description, file name, and type. A
    file name comes from the link, which for an inline XBRL document is
    `/ix?doc=/Archives/...`. The Data Files table is never read.
  - "Accepted" is returned as the page writes it, `YYYY-MM-DD HH:MM:SS` in Eastern
    wall time, once it is shown to be a real date and time. The project's lint
    forbids a naive datetime, and Task 5 owns the time zone.
  - `exhibits_99()` is the spec's `EX-99*`: any type starting `EX-99`, in any case,
    as Stage 1 matched it.
- **Companyfacts** (`sec/companyfacts.py`) gives each accession the `fy` and `fp` its
  facts state (EV6), with the JSON pointer of the first. An accession whose facts
  disagree, or leave either out, has no labels (`None`).

At plan time, the readers were run over every saved response: all 226 of Stage 1's
index pages read, each accession matching its folder, and 215 list an `EX-99*`
exhibit. All 300 of its submissions files and 51 older pages read, and all 181
older-page entries carry both dates. The three probe companyfacts files read, with
73, 70, and 72 accessions.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/sec/filing_index.py`
  and `sec/companyfacts.py`.
- Modify, by exact replacement: `packages/earnings-ingestion/src/earnings_ingestion/sec/data.py`,
  `sec/urls.py`, `cohort/acquire.py`, and `cohort/build.py`.
- Test (create): `packages/earnings-ingestion/tests/test_sec_filing_index.py` and
  `test_sec_companyfacts.py`.
- Test (modify, by exact replacement): `packages/earnings-ingestion/tests/test_sec_data.py`,
  and `tests/integration/test_sec_formats_live.py`.

**Interfaces:**

- Consumes: Task 2's `_named` and `_optional_text`; `sec.identifiers.pad_cik`.
- Produces:
  - `sec/data.py`:
    - `Filing.items: tuple[str, ...] = ()`, the last field;
    - `OlderPage(name: str, filing_from: date | None, filing_to: date | None, pointer: str)`;
    - `Registrant.older_pages: tuple[OlderPage, ...]`;
    - `load_json(body: bytes, what: str) -> object`;
  - `sec/urls.py`: `companyfacts_url(cik) -> str` and
    `filing_index_url(cik, accession) -> str`;
  - `sec/filing_index.py`:
    - `IndexDocument(sequence: int | None, description: str, filename: str, doc_type: str)`;
    - `FilingIndex(accession, form, filing_date: date, accepted: str, period_of_report: date | None, items: tuple[str, ...], documents: tuple[IndexDocument, ...])`,
      with `exhibits_99() -> tuple[IndexDocument, ...]`;
    - `read_filing_index(body: bytes) -> FilingIndex`;
  - `sec/companyfacts.py`:
    - `FiscalLabels(fiscal_year: int, fiscal_period: str, pointer: str)`;
    - `CompanyFacts(cik: str, labels: dict[str, FiscalLabels | None])`, keyed by
      accession;
    - `read_companyfacts(body: bytes) -> CompanyFacts`.

- [x] **Step 1: Write the failing tests**

The index-page tests build a page inline, shaped as EDGAR writes them: a header of
`infoHead` and `info` pairs, then the Document Format Files table, then a Data Files
table.

Create `packages/earnings-ingestion/tests/test_sec_filing_index.py`:

```python
"""A filing's EDGAR index page: form, acceptance, items, and documents (Stage 5)."""

from datetime import date

import pytest
from earnings_ingestion.sec.data import SecDataError
from earnings_ingestion.sec.filing_index import IndexDocument, read_filing_index

ROW = (
    '<tr><td scope="row">{seq}</td><td scope="row">{description}</td>'
    '<td scope="row"><a href="{href}">{name}</a></td>'
    '<td scope="row">{kind}</td><td scope="row">1000</td></tr>'
)


def page(
    *,
    form: str = "8-K",
    accession: str = "0009990001-24-000012",
    accepted: str = "2024-10-24 16:05:12",
    period: str | None = "2024-10-24",
    items: str | None = (
        "Item 2.02: Results of Operations and Financial Condition<br />"
        "Item 9.01: Financial Statements and Exhibits<br />"
    ),
) -> bytes:
    """An index page shaped as EDGAR writes them: a header of info pairs, then the
    Document Format Files table, then a Data Files table."""
    folder = "/Archives/edgar/data/9990001/000999000124000012"
    groups = [
        (
            '<div class="formGrouping"><div class="infoHead">Filing Date</div>'
            '<div class="info">2024-10-24</div><div class="infoHead">Accepted</div>'
            f'<div class="info">{accepted}</div><div class="infoHead">Documents</div>'
            '<div class="info">3</div></div>'
        )
    ]
    if period is not None:
        groups.append(
            '<div class="formGrouping"><div class="infoHead">Period of Report</div>'
            f'<div class="info">{period}</div></div>'
        )
    if items is not None:
        groups.append(
            '<div class="formGrouping"><div class="infoHead">Items</div>'
            f'<div class="info">{items}</div></div>'
        )
    rows = [
        ROW.format(
            seq=1,
            description="8-K",
            href=f"/ix?doc={folder}/acme-20241024.htm",
            name="acme-20241024.htm",
            kind=form,
        ),
        ROW.format(
            seq=2,
            description="PRESS RELEASE",
            href=f"{folder}/acme-ex991.htm",
            name="acme-ex991.htm",
            kind="EX-99.1",
        ),
        ROW.format(
            seq="&nbsp;",
            description="Complete submission text file",
            href=f"{folder}/{accession}.txt",
            name=f"{accession}.txt",
            kind="&nbsp;",
        ),
    ]
    data = ROW.format(
        seq=3,
        description="XBRL TAXONOMY EXTENSION SCHEMA DOCUMENT",
        href=f"{folder}/acme-20241024.xsd",
        name="acme-20241024.xsd",
        kind="EX-101.SCH",
    )
    return (
        "<html><head><title>EDGAR Filing Documents</title></head><body>"
        '<div class="formDiv"><div id="formHeader"><div id="formName">'
        f"<strong>Form {form}</strong> - Current report:</div>"
        '<div id="secNum"><strong>SEC Accession No.</strong> '
        f"{accession}</div></div>"
        f'<div class="formContent">{"".join(groups)}</div></div>'
        '<table class="tableFile" summary="Document Format Files">'
        "<tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th>"
        f"<th>Size</th></tr>{''.join(rows)}</table>"
        '<table class="tableFile" summary="Data Files">'
        "<tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th>"
        f"<th>Size</th></tr>{data}</table></body></html>"
    ).encode()


def test_the_header_and_the_documents_are_read() -> None:
    index = read_filing_index(page())
    assert index.accession == "0009990001-24-000012"
    assert index.form == "8-K"
    assert index.filing_date == date(2024, 10, 24)
    assert index.accepted == "2024-10-24 16:05:12"
    assert index.period_of_report == date(2024, 10, 24)
    assert index.items == ("2.02", "9.01")
    assert index.documents == (
        IndexDocument(1, "8-K", "acme-20241024.htm", "8-K"),
        IndexDocument(2, "PRESS RELEASE", "acme-ex991.htm", "EX-99.1"),
        IndexDocument(
            None,
            "Complete submission text file",
            "0009990001-24-000012.txt",
            "",
        ),
    )


@pytest.mark.parametrize(
    ("kind", "is_exhibit"),
    [
        ("EX-99", True),
        ("EX-99.1", True),
        ("EX-99.01", True),
        ("ex-99.2", True),
        ("EX-10.1", False),
        ("EX-101.INS", False),
    ],
)
def test_every_ex_99_numbering_is_an_exhibit_99(kind, is_exhibit) -> None:
    """The spec's ``EX-99*``: EX-99 with any numbering, as Stage 1 matched it."""
    body = page().replace(b">EX-99.1<", f">{kind}<".encode())
    assert bool(read_filing_index(body).exhibits_99()) is is_exhibit


def test_a_page_without_items_or_a_period_reads_empty() -> None:
    index = read_filing_index(page(form="10-Q", items=None, period=None))
    assert (index.items, index.period_of_report) == ((), None)


@pytest.mark.parametrize(
    "body",
    [
        b"<html><body>Request Rate Threshold Exceeded</body></html>",
        page(accepted="2024-10-24T16:05:12"),
        page(accepted="2024-10-24 4:05:12"),
        page(accepted="2024-02-30 16:05:12"),
        page(accepted="2024-10-24 24:05:12"),
        page().replace(b"Accepted", b"Received"),
        page(items="Results of Operations and Financial Condition<br />"),
        page().replace(b'summary="Document Format Files"', b'summary="Files"'),
        page(accession="not an accession"),
        b"",
    ],
    ids=[
        "block-page",
        "accepted-not-a-time",
        "accepted-not-padded",
        "accepted-no-such-day",
        "accepted-no-such-hour",
        "no-accepted",
        "items-without-numbers",
        "no-document-table",
        "no-accession",
        "empty",
    ],
)
def test_a_page_of_another_shape_is_refused(body) -> None:
    with pytest.raises(SecDataError):
        read_filing_index(body)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_sec_filing_index.py`.

Create `packages/earnings-ingestion/tests/test_sec_companyfacts.py`:

```python
"""SEC's companyfacts: the fiscal labels each periodic report states (Stage 5, EV6)."""

import json

import pytest
from earnings_ingestion.sec.companyfacts import FiscalLabels, read_companyfacts
from earnings_ingestion.sec.data import SecDataError


def fact(accn: str, fy: object, fp: object, **extra: object) -> dict:
    return {"end": "2024-08-31", "val": 1, "accn": accn, "fy": fy, "fp": fp} | extra


def facts(*entries: dict, concept: str = "Revenues") -> bytes:
    data = {
        "cik": 9990001,
        "entityName": "Acme Industrial Corp",
        "facts": {
            "us-gaap": {
                concept: {
                    "label": "Revenues",
                    "description": "Revenues.",
                    "units": {"USD": list(entries)},
                }
            }
        },
    }
    return json.dumps(data).encode()


def test_each_accession_takes_the_labels_its_facts_state() -> None:
    body = facts(
        fact("0009990001-24-000030", 2025, "Q1", form="10-Q"),
        fact("0009990001-24-000030", 2025, "Q1", start="2024-06-01"),
        fact("0009990001-24-000020", 2024, "FY", form="10-K"),
    )
    read = read_companyfacts(body)
    assert read.cik == "0009990001"
    assert read.labels["0009990001-24-000030"] == FiscalLabels(
        fiscal_year=2025,
        fiscal_period="Q1",
        pointer="/facts/us-gaap/Revenues/units/USD/0",
    )
    assert read.labels["0009990001-24-000020"].fiscal_period == "FY"


@pytest.mark.parametrize(
    "entries",
    [
        [fact("a", 2025, "Q1"), fact("a", 2025, "Q2")],
        [fact("a", 2025, "Q1"), fact("a", 2024, "Q1")],
        [fact("a", None, "Q1")],
        [fact("a", 2025, None)],
    ],
    ids=["periods-disagree", "years-disagree", "no-year", "no-period"],
)
def test_disagreeing_or_missing_labels_are_no_labels(entries) -> None:
    assert read_companyfacts(facts(*entries)).labels == {"a": None}


def test_a_concept_name_is_escaped_in_its_pointer() -> None:
    read = read_companyfacts(facts(fact("a", 2025, "Q3"), concept="Odd/Name~1"))
    assert read.labels["a"].pointer == "/facts/us-gaap/Odd~1Name~01/units/USD/0"


@pytest.mark.parametrize(
    "body",
    [
        b"<html>Undeclared Automated Tool</html>",
        b'{"cik": 9990001}',
        json.dumps({"cik": 9990001, "facts": {"us-gaap": {"R": {}}}}).encode(),
        facts({"end": "2024-08-31", "fy": 2025, "fp": "Q1"}),
        facts(fact("a", "2025", "Q1")),
        facts(fact("a", True, "Q1")),
        facts(fact("a", 2025, 1)),
    ],
    ids=[
        "html",
        "no-facts",
        "no-units",
        "no-accession",
        "year-not-a-number",
        "year-a-boolean",
        "period-not-text",
    ],
)
def test_facts_of_another_shape_are_refused(body) -> None:
    with pytest.raises(SecDataError):
        read_companyfacts(body)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_sec_companyfacts.py`.

The submissions tests gain the items, the older pages' dates, and their refusals, and
the live format probe calls `page.name`:

Create `/tmp/plan7-task4-tests.py`:

```python
"""Plan 7: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_sec_data.py": [
        (
            "from earnings_ingestion.sec.data import (\n"
            "    SecDataError,\n",
            "from earnings_ingestion.sec.data import (\n"
            "    OlderPage,\n"
            "    SecDataError,\n",
        ),
        (
            "    assert second.pointer(\"form\") == \"/filings/recent/form/1\"\n"
            "    assert registrant.older_pages == (\"CIK0009990001-submissions-001.json\",)\n"
            "\n",
            "    assert second.pointer(\"form\") == \"/filings/recent/form/1\"\n"
            "    assert registrant.older_pages == (\n"
            "        OlderPage(\n"
            "            name=\"CIK0009990001-submissions-001.json\",\n"
            "            filing_from=None,\n"
            "            filing_to=None,\n"
            "            pointer=\"/filings/files/0\",\n"
            "        ),\n"
            "    )\n"
            "    assert (first.items, second.items) == ((), ())\n"
            "\n"
            "\n"
            "def with_items(items: list) -> bytes:\n"
            "    data = json.loads(submissions())\n"
            "    data[\"filings\"][\"recent\"][\"items\"] = items\n"
            "    return json.dumps(data).encode()\n"
            "\n"
            "\n"
            "def test_items_are_read_when_the_column_is_present() -> None:\n"
            "    \"\"\"Stage 5 reads each filing's items; Stage 4's files, which carry no items\n"
            "    column, read as before (the Stage 5 spec, §Store, client, and readers).\"\"\"\n"
            "    first, second = read_submissions(with_items([\"\", \"2.02,9.01\"])).filings\n"
            "    assert (first.items, second.items) == ((), (\"2.02\", \"9.01\"))\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\"items\", [[\"2.02\"], [\"\", 202]], ids=[\"ragged\", \"not-text\"])\n"
            "def test_malformed_items_are_refused(items) -> None:\n"
            "    with pytest.raises(SecDataError):\n"
            "        read_submissions(with_items(items))\n"
            "\n"
            "\n"
            "def test_an_older_page_records_the_dates_it_covers() -> None:\n"
            "    body = pages(\n"
            "        [\n"
            "            {\n"
            "                \"name\": \"CIK0009990001-submissions-001.json\",\n"
            "                \"filingCount\": 2,\n"
            "                \"filingFrom\": \"2019-01-02\",\n"
            "                \"filingTo\": \"2024-06-28\",\n"
            "            }\n"
            "        ]\n"
            "    )\n"
            "    (page,) = read_submissions(body).older_pages\n"
            "    assert (page.filing_from, page.filing_to) == (date(2019, 1, 2), date(2024, 6, 28))\n"
            "\n"
            "\n"
            "def test_an_older_page_with_a_malformed_date_is_refused() -> None:\n"
            "    body = pages([{\"name\": \"p.json\", \"filingFrom\": \"2019-13-02\"}])\n"
            "    with pytest.raises(SecDataError, match=\"not a date\"):\n"
            "        read_submissions(body)\n"
            "\n",
        ),
    ],
    "tests/integration/test_sec_formats_live.py": [
        (
            "            for filing in read_submissions_page(\n"
            "                client.fetch(submissions_page_url(page), JSON).body\n"
            "            )\n",
            "            for filing in read_submissions_page(\n"
            "                client.fetch(submissions_page_url(page.name), JSON).body\n"
            "            )\n",
        ),
        (
            "        f\" {min(f.filing_date for f in fund.filings)}; older pages:\"\n"
            "        f\" {list(fund.older_pages)}; first older page: {len(older)} filings\"\n"
            "    )\n",
            "        f\" {min(f.filing_date for f in fund.filings)}; older pages:\"\n"
            "        f\" {[page.name for page in fund.older_pages]}; first older page: {len(older)} filings\"\n"
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

Apply `task4-tests`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_sec_data.py packages/earnings-ingestion/tests/test_sec_filing_index.py packages/earnings-ingestion/tests/test_sec_companyfacts.py -q`

Expected: FAIL: `3 errors during collection`:
`ImportError: cannot import name 'OlderPage' from 'earnings_ingestion.sec.data'`,
and `ModuleNotFoundError` for `earnings_ingestion.sec.filing_index` and
`earnings_ingestion.sec.companyfacts`.

- [x] **Step 3: Write the readers**

Create `packages/earnings-ingestion/src/earnings_ingestion/sec/filing_index.py`:

```python
"""A filing's EDGAR index page: form, acceptance, items, and documents (Stage 5).

``<accession>-index.htm`` is EDGAR's own record of a filing. Its header states the
form, the filing date, and the time EDGAR accepted the filing, in Eastern wall time
(the Stage 5 spec, Finding 1); an 8-K's lists the items it reports. Its Document
Format Files table lists each document filed, with its type, so an 8-K's EX-99
exhibits are found there. The table's reading is ported from Stage 1's
``parse_filing_index`` (``expirements/parser-fidelity/discover.py``).

``read_filing_index`` is a pure function of the saved bytes. It checks the shape it
relies on and raises ``SecDataError`` on any other, so a block page never reads as a
filing with no items or no exhibits (A §407).
"""

import re
from dataclasses import dataclass
from datetime import date, time
from urllib.parse import parse_qs, urlparse

import lxml.html
from lxml import etree

from earnings_ingestion.sec.data import SecDataError

ACCESSION = re.compile(r"\b\d{10}-\d{2}-\d{6}\b")
ACCEPTED = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
ITEM = re.compile(r"Item (\d+\.\d+)\b")


@dataclass(frozen=True)
class IndexDocument:
    sequence: int | None
    """The filing's own order; ``None`` for the complete submission text file."""
    description: str
    filename: str
    doc_type: str


@dataclass(frozen=True)
class FilingIndex:
    accession: str
    form: str
    filing_date: date
    accepted: str
    """EDGAR's acceptance time as the page writes it, ``YYYY-MM-DD HH:MM:SS`` in
    Eastern wall time; ``events.acceptance`` reads it as an instant."""
    period_of_report: date | None
    items: tuple[str, ...]
    documents: tuple[IndexDocument, ...]

    def exhibits_99(self) -> tuple[IndexDocument, ...]:
        """The documents typed ``EX-99*``: ``EX-99``, ``EX-99.1``, ``EX-99.01``, and
        any other numbering, as Stage 1 matched them."""
        return tuple(
            document
            for document in self.documents
            if document.doc_type.upper().startswith("EX-99")
        )


def _text(element: etree._Element) -> str:
    return element.text_content().strip()


def _root(body: bytes) -> etree._Element:
    try:
        root = lxml.html.document_fromstring(
            body, parser=lxml.html.HTMLParser(encoding="utf-8")
        )
    except (etree.LxmlError, ValueError) as exc:
        raise SecDataError(f"the index page is not HTML: {exc}") from exc
    if root is None:
        raise SecDataError("the index page is empty")
    return root


def _one(root: etree._Element, path: str, what: str) -> etree._Element:
    found = root.xpath(path)
    if len(found) != 1:
        raise SecDataError(f"the index page has {len(found)} {what}, not one")
    return found[0]


def _info(root: etree._Element) -> dict[str, etree._Element]:
    """The header's label and value pairs, e.g. ``Accepted`` to its value."""
    pairs = {}
    for head in root.xpath('//div[@class="formGrouping"]/div[@class="infoHead"]'):
        value = head.getnext()
        if value is None or value.get("class") != "info":
            raise SecDataError(f"the index page's {_text(head)!r} has no value")
        if _text(head) in pairs:
            raise SecDataError(f"the index page states {_text(head)!r} twice")
        pairs[_text(head)] = value
    return pairs


def _date(value: str, what: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SecDataError(f"the index page's {what} {value!r} is not a date") from exc


def _accepted(value: str) -> str:
    """The page's Accepted text, once it is a real date and time of day."""
    try:
        if ACCEPTED.fullmatch(value):
            date.fromisoformat(value[:10])
            time.fromisoformat(value[11:])
            return value
    except ValueError:
        pass
    raise SecDataError(f"the index page's Accepted {value!r} is not a date and time")


def _items(value: etree._Element) -> tuple[str, ...]:
    """``Item 2.02: Results of ...`` lines, which ``<br/>`` separates."""
    items = []
    for line in (piece.strip() for piece in value.itertext()):
        if not line:
            continue
        match = ITEM.match(line)
        if match is None:
            raise SecDataError(f"the index page's item {line!r} has no number")
        items.append(match.group(1))
    return tuple(items)


def _filename_from_href(href: str) -> str:
    parsed = urlparse(href)
    target = parse_qs(parsed.query).get("doc", [parsed.path])[0]
    return target.rsplit("/", 1)[-1]


def _documents(root: etree._Element) -> tuple[IndexDocument, ...]:
    table = _one(
        root,
        '//table[@summary="Document Format Files"]',
        "Document Format Files tables",
    )
    documents = []
    for row in table.iter("tr"):
        cells = row.findall("td")
        if len(cells) < 4:
            continue
        sequence = _text(cells[0])
        if sequence and not (sequence.isascii() and sequence.isdigit()):
            raise SecDataError(
                f"the index page's sequence {sequence!r} is not a number"
            )
        link = cells[2].find(".//a")
        filename = _filename_from_href(link.get("href", "")) if link is not None else ""
        filename = filename or next(iter(_text(cells[2]).split()), "")
        if not filename:
            raise SecDataError("the index page lists a document with no file name")
        documents.append(
            IndexDocument(
                sequence=int(sequence) if sequence else None,
                description=_text(cells[1]),
                filename=filename,
                doc_type=_text(cells[3]),
            )
        )
    if not documents:
        raise SecDataError("the index page's Document Format Files table is empty")
    return tuple(documents)


def read_filing_index(body: bytes) -> FilingIndex:
    root = _root(body)
    form = _text(_one(root, '//div[@id="formName"]/strong', "form names"))
    if not form.startswith("Form "):
        raise SecDataError(f"the index page's form name {form!r} is not 'Form ...'")
    accessions = ACCESSION.findall(_text(_one(root, '//div[@id="secNum"]', "numbers")))
    if len(accessions) != 1:
        raise SecDataError("the index page states no single accession number")
    info = _info(root)
    for label in ("Filing Date", "Accepted"):
        if label not in info:
            raise SecDataError(f"the index page states no {label}")
    period = info.get("Period of Report")
    return FilingIndex(
        accession=accessions[0],
        form=form.removeprefix("Form ").strip(),
        filing_date=_date(_text(info["Filing Date"]), "Filing Date"),
        accepted=_accepted(_text(info["Accepted"])),
        period_of_report=(
            _date(_text(period), "Period of Report") if period is not None else None
        ),
        items=_items(info["Items"]) if "Items" in info else (),
        documents=_documents(root),
    )
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/sec/filing_index.py`.

Create `packages/earnings-ingestion/src/earnings_ingestion/sec/companyfacts.py`:

```python
"""SEC's companyfacts: the fiscal labels each periodic report states (Stage 5, EV6).

``companyfacts`` holds every XBRL fact a registrant filed, each with the accession
that filed it and that filing's fiscal year (``fy``) and period (``fp``). Stage 5
takes a slot's fiscal labels from the facts of its periodic report, as the source
writes them: a 10-K's ``FY`` is never renamed ``Q4``.

``read_companyfacts`` is a pure function of the saved bytes. It checks the shape it
relies on and raises ``SecDataError`` on any other (A §407). An accession whose facts
disagree, or leave a label out, has no labels: only non-periodic filings such as
8-Ks and S-8s did so in the files plan 7 read.
"""

from dataclasses import dataclass

from earnings_ingestion.sec.data import SecDataError, json_pointer_token, load_json
from earnings_ingestion.sec.identifiers import pad_cik


@dataclass(frozen=True)
class FiscalLabels:
    fiscal_year: int
    fiscal_period: str
    """``Q1``, ``Q2``, ``Q3``, or ``FY``, as the source writes it."""
    pointer: str
    """The JSON pointer of the first fact stating them."""


@dataclass(frozen=True)
class CompanyFacts:
    cik: str
    labels: dict[str, FiscalLabels | None]
    """By accession: the labels its facts state, or ``None`` if they disagree or
    leave one out."""


def _statement(fact: object, pointer: str) -> tuple[str, int | None, str | None]:
    """A fact's accession, ``fy``, and ``fp``."""
    if not isinstance(fact, dict) or not isinstance(fact.get("accn"), str):
        raise SecDataError(f"{pointer} is not a fact with an accession")
    year, period = fact.get("fy"), fact.get("fp")
    if year is not None and (isinstance(year, bool) or not isinstance(year, int)):
        raise SecDataError(f"{pointer}/fy is not a year")
    if period is not None and not isinstance(period, str):
        raise SecDataError(f"{pointer}/fp is not text")
    return fact["accn"], year, period


def read_companyfacts(body: bytes) -> CompanyFacts:
    data = load_json(body, "the companyfacts file")
    if not isinstance(data, dict) or not isinstance(data.get("facts"), dict):
        raise SecDataError("the companyfacts file has no facts object")
    if "cik" not in data:
        raise SecDataError("the companyfacts file has no cik")
    stated: dict[str, list[tuple[int | None, str | None, str]]] = {}
    for taxonomy, concepts in data["facts"].items():
        if not isinstance(concepts, dict):
            raise SecDataError(
                f"/facts/{json_pointer_token(taxonomy)} is not an object"
            )
        for concept, entry in concepts.items():
            where = (
                f"/facts/{json_pointer_token(taxonomy)}/{json_pointer_token(concept)}"
            )
            if not isinstance(entry, dict) or not isinstance(entry.get("units"), dict):
                raise SecDataError(f"{where} has no units object")
            for unit, facts in entry["units"].items():
                pointer = f"{where}/units/{json_pointer_token(unit)}"
                if not isinstance(facts, list):
                    raise SecDataError(f"{pointer} is not a list")
                for index, fact in enumerate(facts):
                    accession, year, period = _statement(fact, f"{pointer}/{index}")
                    stated.setdefault(accession, []).append(
                        (year, period, f"{pointer}/{index}")
                    )
    labels: dict[str, FiscalLabels | None] = {}
    for accession, statements in stated.items():
        year, period, pointer = statements[0]
        agreed = all((y, p) == (year, period) for y, p, _ in statements)
        if agreed and year is not None and period is not None:
            labels[accession] = FiscalLabels(year, period, pointer)
        else:
            labels[accession] = None
    return CompanyFacts(cik=pad_cik(data["cik"]), labels=labels)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/sec/companyfacts.py`.

Then the submissions reader, the URLs, and the two callers of `older_pages`:

Create `/tmp/plan7-task4-source.py`:

```python
"""Plan 7: exact replacements for 4 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/sec/data.py": [
        (
            "- A registrant's submissions JSON holds its conformed name, former names, current\n"
            "  tickers, and filings. Older filings sit in separate pages that ``filings.files``\n"
            "  names.\n"
            "- An N-PORT primary document holds a fund's holdings on its report date.\n",
            "- A registrant's submissions JSON holds its conformed name, former names, current\n"
            "  tickers, and filings, with each filing's 8-K items where the file has that column.\n"
            "  Older filings sit in separate pages that ``filings.files`` names, each with the\n"
            "  filing dates it covers.\n"
            "- An N-PORT primary document holds a fund's holdings on its report date.\n",
        ),
        (
            "    index: int\n"
            "\n",
            "    index: int\n"
            "    items: tuple[str, ...] = ()\n"
            "    \"\"\"The 8-K items SEC lists for the filing, e.g. ``(\"2.02\", \"9.01\")``; empty for\n"
            "    other forms, and for files with no ``items`` column, such as Stage 4's synthetic\n"
            "    ones.\"\"\"\n"
            "\n",
        ),
        (
            "        return f\"{self.columns}/{json_pointer_token(column)}/{self.index}\"\n"
            "\n",
            "        return f\"{self.columns}/{json_pointer_token(column)}/{self.index}\"\n"
            "\n"
            "\n"
            "@dataclass(frozen=True)\n"
            "class OlderPage:\n"
            "    \"\"\"An older filings page, which is fetched separately when needed.\"\"\"\n"
            "\n"
            "    name: str\n"
            "    filing_from: date | None\n"
            "    filing_to: date | None\n"
            "    \"\"\"The filing dates the page covers, when the entry states them.\"\"\"\n"
            "    pointer: str\n"
            "\n",
        ),
        (
            "    filings: tuple[Filing, ...]\n"
            "    older_pages: tuple[str, ...]\n"
            "    \"\"\"Names of the older filing pages, fetched separately when needed.\"\"\"\n"
            "\n",
            "    filings: tuple[Filing, ...]\n"
            "    older_pages: tuple[OlderPage, ...]\n"
            "\n",
        ),
        (
            "\n"
            "def _load(body: bytes, what: str) -> object:\n"
            "    try:\n",
            "\n"
            "def load_json(body: bytes, what: str) -> object:\n"
            "    try:\n",
        ),
        (
            "def read_company_tickers(body: bytes) -> tuple[TickerEntry, ...]:\n"
            "    data = _load(body, \"company_tickers.json\")\n"
            "    if not isinstance(data, dict) or not data:\n",
            "def read_company_tickers(body: bytes) -> tuple[TickerEntry, ...]:\n"
            "    data = load_json(body, \"company_tickers.json\")\n"
            "    if not isinstance(data, dict) or not data:\n",
        ),
        (
            "        raise SecDataError(f\"{pointer}'s columns are not arrays of one length\")\n"
            "    filings = []\n"
            "    for index, row in enumerate(zip(*arrays, strict=True)):\n"
            "        accession, filed, reported, accepted, form, document = row\n"
            "        where = f\"{pointer} index {index}\"\n",
            "        raise SecDataError(f\"{pointer}'s columns are not arrays of one length\")\n"
            "    items = columns.get(\"items\", [\"\"] * len(arrays[0]))\n"
            "    if (\n"
            "        not isinstance(items, list)\n"
            "        or len(items) != len(arrays[0])\n"
            "        or not all(isinstance(value, str) for value in items)\n"
            "    ):\n"
            "        raise SecDataError(f\"{pointer}'s items are not text, one per filing\")\n"
            "    filings = []\n"
            "    for index, row in enumerate(zip(*arrays, items, strict=True)):\n"
            "        accession, filed, reported, accepted, form, document, listed = row\n"
            "        where = f\"{pointer} index {index}\"\n",
        ),
        (
            "                index=index,\n"
            "            )\n",
            "                index=index,\n"
            "                items=tuple(item.strip() for item in listed.split(\",\") if item.strip()),\n"
            "            )\n",
        ),
        (
            "\n"
            "def _former_name(entry: object, index: int) -> FormerName:\n",
            "\n"
            "def _older_page(entry: object, index: int) -> OlderPage:\n"
            "    pointer = f\"/filings/files/{index}\"\n"
            "    entry = _named(entry, pointer)\n"
            "    return OlderPage(\n"
            "        name=entry[\"name\"],\n"
            "        filing_from=_date(entry.get(\"filingFrom\"), f\"{pointer}/filingFrom\"),\n"
            "        filing_to=_date(entry.get(\"filingTo\"), f\"{pointer}/filingTo\"),\n"
            "        pointer=pointer,\n"
            "    )\n"
            "\n"
            "\n"
            "def _former_name(entry: object, index: int) -> FormerName:\n",
        ),
        (
            "def read_submissions(body: bytes) -> Registrant:\n"
            "    data = _load(body, \"the submissions file\")\n"
            "    if not isinstance(data, dict) or not {\"cik\", \"name\", \"tickers\", \"filings\"} <= set(\n",
            "def read_submissions(body: bytes) -> Registrant:\n"
            "    data = load_json(body, \"the submissions file\")\n"
            "    if not isinstance(data, dict) or not {\"cik\", \"name\", \"tickers\", \"filings\"} <= set(\n",
        ),
        (
            "        filings=read_filing_columns(filings[\"recent\"], \"/filings/recent\"),\n"
            "        older_pages=tuple(\n"
            "            _named(page, f\"/filings/files/{index}\")[\"name\"]\n"
            "            for index, page in enumerate(older)\n"
            "        ),\n"
            "    )\n",
            "        filings=read_filing_columns(filings[\"recent\"], \"/filings/recent\"),\n"
            "        older_pages=tuple(_older_page(page, index) for index, page in enumerate(older)),\n"
            "    )\n",
        ),
        (
            "    \"\"\"An older filings page: the same columns, at the top level.\"\"\"\n"
            "    return read_filing_columns(_load(body, \"the filings page\"), \"\")\n"
            "\n",
            "    \"\"\"An older filings page: the same columns, at the top level.\"\"\"\n"
            "    return read_filing_columns(load_json(body, \"the filings page\"), \"\")\n"
            "\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/sec/urls.py": [
        (
            "\n"
            "def archive_url(cik: str | int, accession: str, filename: str) -> str:\n",
            "\n"
            "def companyfacts_url(cik: str | int) -> str:\n"
            "    \"\"\"The XBRL facts SEC holds for a registrant, with each fact's fiscal labels.\"\"\"\n"
            "    return f\"https://data.sec.gov/api/xbrl/companyfacts/CIK{pad_cik(cik)}.json\"\n"
            "\n"
            "\n"
            "def archive_url(cik: str | int, accession: str, filename: str) -> str:\n",
        ),
        (
            "    )\n",
            "    )\n"
            "\n"
            "\n"
            "def filing_index_url(cik: str | int, accession: str) -> str:\n"
            "    \"\"\"A filing's EDGAR index page, ``<accession>-index.htm``.\"\"\"\n"
            "    return archive_url(cik, accession, f\"{accession}-index.htm\")\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/cohort/acquire.py": [
        (
            "        filings += read_submissions_page(\n"
            "            get(\"sec-edgar\", submissions_page_url(page), JSON)\n"
            "        )\n",
            "        filings += read_submissions_page(\n"
            "            get(\"sec-edgar\", submissions_page_url(page.name), JSON)\n"
            "        )\n",
        ),
    ],
    "packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py": [
        (
            "            for page in registrant.older_pages:\n"
            "                older = self._latest(SEC_SOURCE_ID, submissions_page_url(page))\n"
            "                if older is not None:\n",
            "            for page in registrant.older_pages:\n"
            "                older = self._latest(SEC_SOURCE_ID, submissions_page_url(page.name))\n"
            "                if older is not None:\n",
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

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_sec_data.py packages/earnings-ingestion/tests/test_sec_filing_index.py packages/earnings-ingestion/tests/test_sec_companyfacts.py -q`

Expected: `57 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/sec/*.py packages/earnings-ingestion/src/earnings_ingestion/cohort/acquire.py packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py packages/earnings-ingestion/tests/test_sec_*.py tests/integration/test_sec_formats_live.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `994 passed, 24 deselected`; `All checks passed!` and
`218 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/sec packages/earnings-ingestion/src/earnings_ingestion/cohort/acquire.py packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py packages/earnings-ingestion/tests/test_sec_data.py packages/earnings-ingestion/tests/test_sec_filing_index.py packages/earnings-ingestion/tests/test_sec_companyfacts.py tests/integration/test_sec_formats_live.py
git commit -m "feat(sec): read 8-K items, older-page dates, index pages, and companyfacts"
```

---

### Task 5: Acceptance time, and the record's first leg

S §Acceptance time (EV10), S Finding 1, and S §Prerequisites, item 3.

- **The instant.** A filing's acceptance time is its index page's "Accepted" value,
  Eastern wall time. `accepted_instant` localizes it to America/New_York and returns
  the UTC instant. A wall time that daylight saving repeats or skips is refused with
  `AcceptanceTimeError`, never guessed: `zoneinfo` gives such a time different
  offsets under `fold=0` and `fold=1`. EDGAR accepts filings from 06:00 to 22:00, so
  a real filing never meets one.
- **The cross-check.** SEC's `acceptanceDateTime` follows one of two conventions,
  one per file: the true UTC instant, or the instant's Eastern digits followed by
  `Z`. `convention_of` names the one a row follows, given the page's instant, and
  `None` means neither, which Task 7 turns into a blocking
  `acceptance_time_mismatch`.
- **Both readings.** `eastern_dates(written)` gives the Eastern date a value has under
  each convention it can follow. Task 7 uses it where no index page decides: a value
  with a non-zero offset can only be the instant it states.
- **Files.** `survey(name, filings, instants)` cross-checks each of a file's rows
  whose index page gives an instant. A file's convention is the one its matching
  rows share. A mismatch is reported apart and does not decide it, and a file whose
  rows follow both conventions has none. The convention is never inferred from the
  file's dates (S §Acceptance time).
- **Dates.** `eastern_date(instant)` is the calendar every Stage 5 date judgment uses.
- **The record** (P7-19). `tests/integration/regenerate_acceptance_time_record.py`,
  like Stage 4's `regenerate_cohort_fixtures.py`, is a script that pytest never
  collects. It sends no request. It reads saved pages and writes
  `docs/verification/edgar-acceptance-time.md`:
  - leg 1 reads Stage 1's pages under `data/raw/discovery/`, and reproduces S
    Finding 1 exactly;
  - leg 2 reads Stage 5's store under `data/raw/events/`, once Task 19's discovery
    run has saved submissions files and index pages there. Until then the record
    says so, and Task 19 regenerates it.
  - Leg 2 tells a submissions file from a companyfacts file by its URL, since
    both are named `CIK##########.json`. It reads no companyfacts file and no
    primary document. Task 19 runs it on the synthetic store before the live run.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/__init__.py` and
  `events/acceptance.py`; `tests/integration/regenerate_acceptance_time_record.py`.
- Generate: `docs/verification/edgar-acceptance-time.md`.
- Test (create): `packages/earnings-ingestion/tests/test_events_acceptance.py`.

**Interfaces:**

- Consumes: Task 4's `Filing`, `read_submissions`, `read_submissions_page`, and
  `read_filing_index`; `fetch.records.Retrieval`.
- Produces, in `events/acceptance.py`:
  - `SOURCE_TIMEZONE = "America/New_York"` and `EASTERN`, its `ZoneInfo`;
  - `Convention(StrEnum)`: `UTC = "utc"`, `EASTERN_DIGITS = "eastern_digits"`;
  - `AcceptanceTimeError(ValueError)`;
  - `accepted_instant(accepted: str) -> datetime`, a UTC instant;
  - `eastern_date(instant: datetime) -> date`;
  - `convention_of(written: datetime | None, instant: datetime) -> Convention | None`;
  - `eastern_dates(written: datetime) -> dict[Convention, date]`;
  - `CrossCheck(accession, written, instant, convention, pointer)`;
  - `FileSurvey(name, checks)`, with the properties `conventions`, `convention`,
    `mixed`, and `mismatches`;
  - `survey(name: str, filings: Iterable[Filing], instants: Mapping[str, datetime]) -> FileSurvey`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_acceptance.py`:

```python
"""EDGAR acceptance time (the Stage 5 spec, EV10 and §Acceptance time)."""

from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.events.acceptance import (
    AcceptanceTimeError,
    Convention,
    accepted_instant,
    convention_of,
    eastern_date,
    eastern_dates,
    survey,
)
from earnings_ingestion.sec.data import Filing


def written(value: str) -> datetime:
    """A submissions ``acceptanceDateTime`` as ``read_submissions`` returns it."""
    return datetime.fromisoformat(value)


@pytest.mark.parametrize(
    ("accepted", "instant"),
    [
        ("2024-10-24 16:05:12", datetime(2024, 10, 24, 20, 5, 12, tzinfo=UTC)),
        ("2025-01-28 07:00:03", datetime(2025, 1, 28, 12, 0, 3, tzinfo=UTC)),
    ],
    ids=["daylight-time", "standard-time"],
)
def test_the_accepted_value_is_eastern_wall_time(accepted, instant) -> None:
    assert accepted_instant(accepted) == instant


@pytest.mark.parametrize(
    "accepted",
    ["2025-11-02 01:30:00", "2025-03-09 02:30:00"],
    ids=["repeated-hour", "skipped-hour"],
)
def test_a_wall_time_daylight_saving_repeats_or_skips_is_refused(accepted) -> None:
    with pytest.raises(AcceptanceTimeError, match=accepted):
        accepted_instant(accepted)


def test_dates_are_judged_on_the_eastern_calendar() -> None:
    assert eastern_date(datetime(2026, 9, 23, 2, 0, tzinfo=UTC)) == date(2026, 9, 22)
    assert eastern_date(datetime(2026, 9, 23, 4, 0, tzinfo=UTC)) == date(2026, 9, 23)


@pytest.mark.parametrize(
    ("value", "convention"),
    [
        ("2024-10-24T20:05:12.000Z", Convention.UTC),
        ("2024-10-24T16:05:12.000Z", Convention.EASTERN_DIGITS),
        ("2024-10-24T16:05:12-04:00", Convention.UTC),
        ("2024-10-24T16:05:13.000Z", None),
        ("2024-10-24T16:05:12-05:00", None),
    ],
    ids=["utc", "eastern-digits", "stated-offset", "a-second-off", "wrong-offset"],
)
def test_a_row_uses_one_convention_or_mismatches(value, convention) -> None:
    instant = accepted_instant("2024-10-24 16:05:12")
    assert convention_of(written(value), instant) == convention


def test_a_row_without_a_value_mismatches() -> None:
    assert convention_of(None, accepted_instant("2024-10-24 16:05:12")) is None


def test_a_value_has_an_eastern_date_under_each_convention_it_can_be_in() -> None:
    assert eastern_dates(written("2026-09-23T01:30:00.000Z")) == {
        Convention.UTC: date(2026, 9, 22),
        Convention.EASTERN_DIGITS: date(2026, 9, 23),
    }
    assert eastern_dates(written("2026-09-22T15:00:00.000Z")) == {
        Convention.UTC: date(2026, 9, 22),
        Convention.EASTERN_DIGITS: date(2026, 9, 22),
    }
    assert eastern_dates(written("2026-09-22T23:30:00-04:00")) == {
        Convention.UTC: date(2026, 9, 22)
    }


def filing(index: int, value: str | None) -> Filing:
    return Filing(
        accession=f"0009990001-24-00001{index}",
        form="8-K",
        filing_date=date(2024, 10, 24),
        report_date=None,
        accepted_at=None if value is None else written(value),
        primary_document="acme-8k.htm",
        columns="/filings/recent",
        index=index,
        items=("2.02", "9.01"),
    )


INSTANTS = {
    "0009990001-24-000010": accepted_instant("2024-10-24 16:05:12"),
    "0009990001-24-000011": accepted_instant("2025-01-28 07:00:03"),
}


def test_a_file_s_convention_is_the_one_its_cross_checked_rows_share() -> None:
    rows = [
        filing(0, "2024-10-24T20:05:12.000Z"),
        filing(1, "2025-01-28T12:00:03.000Z"),
        filing(2, "2025-04-24T20:00:00.000Z"),
    ]
    checked = survey("CIK0009990001.json", rows, INSTANTS)
    assert checked.convention is Convention.UTC
    assert [check.accession for check in checked.checks] == [
        "0009990001-24-000010",
        "0009990001-24-000011",
    ]
    assert checked.checks[0].pointer == "/filings/recent/acceptanceDateTime/0"
    assert (checked.mismatches, checked.mixed) == ((), False)


def test_a_mismatch_is_named_and_leaves_the_convention_to_the_other_rows() -> None:
    rows = [filing(0, "2024-10-24T16:05:12.000Z"), filing(1, None)]
    checked = survey("CIK0009990001.json", rows, INSTANTS)
    assert checked.convention is Convention.EASTERN_DIGITS
    assert [check.accession for check in checked.mismatches] == ["0009990001-24-000011"]


def test_a_file_using_both_conventions_has_none() -> None:
    rows = [filing(0, "2024-10-24T16:05:12.000Z"), filing(1, "2025-01-28T12:00:03Z")]
    checked = survey("CIK0009990001.json", rows, INSTANTS)
    assert (checked.convention, checked.mixed) == (None, True)


def test_a_file_with_no_cross_checked_row_has_no_convention() -> None:
    checked = survey("CIK0009990001.json", [filing(2, "2025-04-24T20:00:00Z")], {})
    assert (checked.checks, checked.convention, checked.mixed) == ((), None, False)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_acceptance.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_acceptance.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events'`.

- [x] **Step 3: Write the acceptance-time module**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/__init__.py`:

```python
"""Stage 5: event discovery, eligibility, and the event and pilot freezes (plan 7)."""
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/__init__.py`.

Create `packages/earnings-ingestion/src/earnings_ingestion/events/acceptance.py`:

```python
"""EDGAR acceptance time (EV10 of the Stage 5 spec, §Acceptance time).

- A filing's acceptance time is its index page's "Accepted" value, which is Eastern
  wall time. ``accepted_instant`` localizes it to America/New_York and returns the UTC
  instant. A wall time that daylight saving repeats or skips is refused, never
  guessed.
- SEC's submissions ``acceptanceDateTime`` is only a cross-check. SEC writes it in two
  conventions, one per file (the spec's Finding 1): the true UTC instant, or the
  instant's Eastern wall-clock digits followed by ``Z``. ``convention_of`` names the
  one a row uses, and ``None`` is a mismatch, which blocks.
- A file's convention is the one its cross-checked rows share (``survey``). It is
  never inferred from the file's dates.
- Every date judgment uses the Eastern calendar date (``eastern_date``).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from earnings_ingestion.sec.data import Filing

SOURCE_TIMEZONE = "America/New_York"
EASTERN = ZoneInfo(SOURCE_TIMEZONE)


class Convention(StrEnum):
    UTC = "utc"
    """The value is the instant."""
    EASTERN_DIGITS = "eastern_digits"
    """The value is the instant's Eastern wall-clock digits, followed by ``Z``."""


class AcceptanceTimeError(ValueError):
    """An Accepted value that daylight saving repeats or skips."""


def accepted_instant(accepted: str) -> datetime:
    """The UTC instant of an index page's Accepted text, ``YYYY-MM-DD HH:MM:SS``."""
    wall = datetime.combine(
        date.fromisoformat(accepted[:10]),
        time.fromisoformat(accepted[11:]),
        tzinfo=EASTERN,
    )
    if wall.utcoffset() != wall.replace(fold=1).utcoffset():
        raise AcceptanceTimeError(
            f"{accepted} is repeated or skipped in {SOURCE_TIMEZONE}"
        )
    return wall.astimezone(UTC)


def eastern_date(instant: datetime) -> date:
    return instant.astimezone(EASTERN).date()


def convention_of(written: datetime | None, instant: datetime) -> Convention | None:
    """The convention of a row's ``acceptanceDateTime``, given the instant its index
    page states; ``None`` when it follows neither."""
    if written is None:
        return None
    if written == instant:
        return Convention.UTC
    if (
        written.utcoffset() == timedelta(0)
        and written.replace(tzinfo=EASTERN) == instant
    ):
        return Convention.EASTERN_DIGITS
    return None


def eastern_dates(written: datetime) -> dict[Convention, date]:
    """The Eastern date ``written`` gives under each convention it can follow: a value
    with a non-zero offset can only be the instant it states."""
    dates = {Convention.UTC: eastern_date(written)}
    if written.utcoffset() == timedelta(0):
        dates[Convention.EASTERN_DIGITS] = written.date()
    return dates


@dataclass(frozen=True)
class CrossCheck:
    """A submissions row checked against its filing's index page."""

    accession: str
    written: datetime | None
    instant: datetime
    convention: Convention | None
    pointer: str
    """The JSON pointer of the row's ``acceptanceDateTime``."""


@dataclass(frozen=True)
class FileSurvey:
    """A submissions file or older page, and the cross-checks of its rows."""

    name: str
    checks: tuple[CrossCheck, ...]

    @property
    def conventions(self) -> frozenset[Convention]:
        return frozenset(c.convention for c in self.checks if c.convention is not None)

    @property
    def convention(self) -> Convention | None:
        """The convention every matching row shares; ``None`` when no row matched, or
        the rows follow both."""
        return next(iter(self.conventions)) if len(self.conventions) == 1 else None

    @property
    def mixed(self) -> bool:
        return len(self.conventions) > 1

    @property
    def mismatches(self) -> tuple[CrossCheck, ...]:
        return tuple(check for check in self.checks if check.convention is None)


def survey(
    name: str, filings: Iterable[Filing], instants: Mapping[str, datetime]
) -> FileSurvey:
    """Cross-check each of a file's filings whose index page gives an instant."""
    return FileSurvey(
        name=name,
        checks=tuple(
            CrossCheck(
                accession=filing.accession,
                written=filing.accepted_at,
                instant=instants[filing.accession],
                convention=convention_of(
                    filing.accepted_at, instants[filing.accession]
                ),
                pointer=filing.pointer("acceptanceDateTime"),
            )
            for filing in filings
            if filing.accession in instants
        ),
    )
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/acceptance.py`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_acceptance.py -q`

Expected: `16 passed`.

- [x] **Step 5: Write and run the record's script**

Create `tests/integration/regenerate_acceptance_time_record.py`:

```python
"""Regenerate docs/verification/edgar-acceptance-time.md from saved pages (EV10).

    uv run --locked --all-packages python tests/integration/regenerate_acceptance_time_record.py --repo PATH

It cross-checks SEC's submissions ``acceptanceDateTime`` against the index page's
"Accepted" value for every saved row that has both, and rewrites the record. It sends
no request. ``--repo`` is the checkout whose gitignored ``data/raw/`` holds the pages,
by default this one; the record is written in this checkout.

- Leg 1 reads Stage 1's pages, under ``data/raw/discovery/``.
- Leg 2 reads Stage 5's store, under ``data/raw/events/``, once its discovery run has
  saved submissions files and index pages there. It reads no companyfacts file or
  primary document.

pytest never collects this file.
"""

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from earnings_ingestion.events.acceptance import (
    Convention,
    FileSurvey,
    accepted_instant,
    survey,
)
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.sec.data import read_submissions, read_submissions_page
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import submissions_page_url

REPO = Path(__file__).resolve().parents[2]
RECORD = Path("docs/verification/edgar-acceptance-time.md")
GENERATOR = "tests/integration/regenerate_acceptance_time_record.py"
STAGE_1 = Path("data/raw/discovery")
STAGE_5 = Path("data/raw/events/sec-edgar")
SUBMISSIONS = submissions_page_url("")
"""Where submissions files and older pages live: a companyfacts file's name looks
like a submissions file's, so the name alone cannot tell them apart."""
ARCHIVES = "https://www.sec.gov/Archives/"
MAIN_FILE = re.compile(r"CIK\d{10}\.json")
OLDER_PAGE = re.compile(r"CIK\d{10}-submissions-\d{3}\.json")
LABELS = {Convention.UTC: "true UTC", Convention.EASTERN_DIGITS: "Eastern digits and Z"}


@dataclass(frozen=True)
class Saved:
    name: str
    body: bytes
    retrieved: date


@dataclass(frozen=True)
class Leg:
    title: str
    source: str
    surveys: tuple[tuple[FileSurvey, bool, date | None], ...]
    """Each file's survey, whether it is an older page, and a main file's latest
    filing date."""
    index_pages: int
    retrieved: tuple[date, date]


def stage_1(repo: Path) -> tuple[list[Saved], list[Saved]]:
    """Stage 1's submissions files and index pages, each with its meta record."""

    def saved(path: Path, name: str) -> Saved:
        meta = json.loads(Path(f"{path}.meta.json").read_text(encoding="utf-8"))
        return Saved(
            name, path.read_bytes(), date.fromisoformat(meta["retrieved_at"][:10])
        )

    root = repo / STAGE_1
    files = [
        saved(path, path.name)
        for path in sorted((root / "submissions").glob("*.json"))
        if not path.name.endswith(".meta.json")
    ]
    pages = [
        saved(path, path.parent.name)
        for path in sorted((root / "filings").glob("*/index.htm"))
    ]
    return files, pages


def stage_5(repo: Path) -> tuple[list[Saved], list[Saved]]:
    """The newest retrieval of each submissions file, older page, and index page in
    Stage 5's store."""
    root = repo / STAGE_5
    newest: dict[str, Retrieval] = {}
    for path in sorted(root.glob("retrievals/*/*.json")):
        record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
        known = newest.get(record.request_url)
        if known is None or (record.retrieved_at, record.sha256) > (
            known.retrieved_at,
            known.sha256,
        ):
            newest[record.request_url] = record
    files: list[Saved] = []
    pages: list[Saved] = []
    for url, record in sorted(newest.items()):
        name = url.rsplit("/", 1)[-1]
        if url.startswith(SUBMISSIONS) and (
            MAIN_FILE.fullmatch(name) or OLDER_PAGE.fullmatch(name)
        ):
            kind = files
        elif url.startswith(ARCHIVES) and name.endswith("-index.htm"):
            kind = pages
        else:
            continue
        (body_path,) = root.glob(f"{record.sha256}.*")
        kind.append(Saved(name, body_path.read_bytes(), record.retrieved_at.date()))
    return files, pages


def leg(title: str, source: str, files: list[Saved], pages: list[Saved]) -> Leg:
    instants = {}
    for page in pages:
        index = read_filing_index(page.body)
        instants[index.accession] = accepted_instant(index.accepted)
    surveys = []
    for saved in files:
        older = OLDER_PAGE.fullmatch(saved.name) is not None
        filings = (
            read_submissions_page(saved.body)
            if older
            else read_submissions(saved.body).filings
        )
        latest = None if older else max((f.filing_date for f in filings), default=None)
        surveys.append((survey(saved.name, filings, instants), older, latest))
    dates = [saved.retrieved for saved in files + pages]
    return Leg(title, source, tuple(surveys), len(pages), (min(dates), max(dates)))


def span(dates: list[date]) -> str:
    return f"{min(dates)} to {max(dates)}" if dates else "none"


def rows(leg: Leg) -> list[tuple[str, str]]:
    checked = [s for s, _, _ in leg.surveys if s.checks]
    checks = [check for s in checked for check in s.checks]
    lines = [
        ("Retrieved", span(list(leg.retrieved))),
        ("Submissions files read", str(sum(not older for _, older, _ in leg.surveys))),
        ("Older pages read", str(sum(older for _, older, _ in leg.surveys))),
        ("Index pages read", str(leg.index_pages)),
        ("Files with a cross-checked row", str(len(checked))),
        ("Rows cross-checked", str(len(checks))),
    ]
    for convention, label in LABELS.items():
        count = sum(check.convention is convention for check in checks)
        lines.append((f"Rows in {label}", str(count)))
    lines += [
        ("Rows in neither", str(sum(check.convention is None for check in checks))),
        ("Files in both conventions", str(sum(s.mixed for s in checked))),
    ]
    for convention, label in LABELS.items():
        main = [
            latest
            for s, older, latest in leg.surveys
            if not older and s.convention is convention and latest is not None
        ]
        lines.append(
            (
                f"Submissions files in {label}",
                f"{len(main)}, latest filing {span(main)}",
            )
        )
    for convention, label in LABELS.items():
        count = sum(older and s.convention is convention for s, older, _ in leg.surveys)
        lines.append((f"Older pages in {label}", str(count)))
    return lines


def failures(leg: Leg) -> list[str]:
    found = []
    for s, _, _ in leg.surveys:
        found += [
            f"- {leg.title}: `{s.name}` row `{c.accession}` follows neither convention."
            for c in s.mismatches
        ]
        if s.mixed:
            found.append(f"- {leg.title}: `{s.name}` follows both conventions.")
    return found


def render(legs: list[Leg]) -> str:
    table = [
        "| | " + " | ".join(leg.title for leg in legs) + " |",
        "| --- |" + " --- |" * len(legs),
    ]
    columns = [rows(leg) for leg in legs]
    for position, (label, _) in enumerate(columns[0]):
        values = " | ".join(column[position][1] for column in columns)
        table.append(f"| {label} | {values} |")
    found = [line for leg in legs for line in failures(leg)]
    verdict = (
        [
            "Every cross-checked row follows one of the two conventions, and no file",
            "follows both. So Stage 5 reads the index page's Accepted value as the",
            "acceptance time, and the submissions value only cross-checks it.",
        ]
        if not found
        else ["These rows or files break the rule:", "", *found]
    )
    pending = (
        []
        if len(legs) == 2
        else [
            "",
            "Leg 2 reads Stage 5's own pages, which cover the window's filings. It is",
            "added when Stage 5's discovery run has saved them.",
        ]
    )
    sources = [f"- **{leg.title}** reads {leg.source}." for leg in legs]
    return "\n".join(
        [
            "# EDGAR acceptance time",
            "",
            f"<!-- Generated by {GENERATOR} from saved pages; do not edit. -->",
            "",
            "Stage 5 takes a filing's acceptance time from its EDGAR index page's",
            '"Accepted" value, read as America/New_York wall time (EV10 of',
            "`specs/event-discovery-eligibility-and-acquisition.md`). SEC's submissions",
            "`acceptanceDateTime` only cross-checks it. SEC writes that value in one of",
            "two conventions: the true UTC instant, or the instant's Eastern wall-clock",
            "digits followed by `Z`.",
            "",
            "This record recomputes the finding from saved pages, and sends no request.",
            "Each leg reads every saved submissions file and older page, and",
            "cross-checks each row whose filing's index page is also saved. A file's",
            "convention is the one its cross-checked rows share.",
            "",
            *sources,
            *pending,
            "",
            *table,
            "",
            *verdict,
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=REPO)
    repo = parser.parse_args().repo.resolve()
    first = stage_1(repo)
    if not first[0] or not first[1]:
        parser.error(f"no Stage 1 pages under {repo / STAGE_1}")
    legs = [leg("Leg 1", "Stage 1's pages, under `data/raw/discovery/`", *first)]
    second = stage_5(repo)
    if second[0] and second[1]:
        legs.append(leg("Leg 2", "Stage 5's pages, under `data/raw/events/`", *second))
    (REPO / RECORD).write_text(render(legs), encoding="utf-8")
    print(f"wrote {RECORD} with {len(legs)} leg(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Extract it with `python3 /tmp/plan7-extract.py tests/integration/regenerate_acceptance_time_record.py`.

Run: `uv run --locked --all-packages python tests/integration/regenerate_acceptance_time_record.py`

Expected: `wrote docs/verification/edgar-acceptance-time.md with 1 leg(s)`. The
record's table has one column, and its rows read:

| Row | Leg 1 |
| --- | --- |
| Retrieved | 2026-09-22 to 2026-09-25 |
| Submissions files read | 300 |
| Older pages read | 51 |
| Index pages read | 226 |
| Files with a cross-checked row | 221 |
| Rows cross-checked | 227 |
| Rows in true UTC | 143 |
| Rows in Eastern digits and Z | 84 |
| Rows in neither | 0 |
| Files in both conventions | 0 |
| Submissions files in true UTC | 96, latest filing 2026-04-09 to 2026-09-24 |
| Submissions files in Eastern digits and Z | 76, latest filing 2008-02-14 to 2026-04-02 |
| Older pages in true UTC | 43 |
| Older pages in Eastern digits and Z | 6 |

Its verdict reads "Every cross-checked row follows one of the two conventions, and no
file follows both." These are S Finding 1's numbers. If any differs, stop and report
it: the saved pages have changed, or the rule does not hold.

- [x] **Step 6: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py packages/earnings-ingestion/tests/test_events_acceptance.py tests/integration/regenerate_acceptance_time_record.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1010 passed, 24 deselected`; `All checks passed!` and
`222 files already formatted`.

- [x] **Step 7: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events packages/earnings-ingestion/tests/test_events_acceptance.py tests/integration/regenerate_acceptance_time_record.py docs/verification/edgar-acceptance-time.md
git commit -m "feat(events): read acceptance time in Eastern and record both SEC conventions"
```

---

### Task 6: The event records

S §The event manifest, §P's expected-event contract, and §Review overrides. The
records come first, so every later task builds and tests against their validators.

- **`EventRow`** is one slot. Its validator holds the spec's invariants:
  - `event_id` is `<issuer_id>:<period_end>`;
  - the two fiscal labels are known or unknown together, and unknown stays null
    (R1.5, P-A5);
  - a release filing comes with its method and both times, and
    `first_publication_time` equals `filing_acceptance_time` (EV9), stored in UTC;
  - the reason implies the status, only `no_release_filing` and
    `several_release_filings` lack a release filing, and only an `ambiguous` event is
    retained;
  - `membership_assertion_id` is set exactly when check 4 decided, so it is null when
    check 1, 2, or 3 did (P7-11).
- **`EventFinding`** and `event_finding(kind, subject, detail, *, issuer_id)`. The id
  is `<kind>:<subject>`. The digest covers only what the finding says, so an
  acknowledgement goes stale when the finding changes (P6-7). The kind decides
  whether it blocks: every kind but `fiscal_labels_unknown`.
- **`EventOverride`** sets exactly its kind's targets. `set_release_filing` must cite
  the filing, and `retain_unresolved` names a reason that makes an event `ambiguous`.
  `EventOverridesFile` refuses a repeated `override_id`, and a second override of one
  kind for one event. An event may carry one of each kind (P7-14): a `set_release_filing`
  recomputes eligibility, which can leave the event `ambiguous`, so it then needs a
  `retain_unresolved` too (S §Review overrides).
- **`EventManifest`** keeps its rows, findings, and overrides unique and sorted by id.
  `content_hash` hashes the definition without `event_manifest_version`,
  `universe_version`, `content_hash`, and `created_at` (P7-2), together with the
  rows, findings, and overrides.
- **The evidence record.** `EventEvidence`, with `FileEvidence`, `SkippedPage`, and
  `EventCitations`, holds the citations, each file's convention, the older pages
  skipped, and every retrieval time (EV11). It holds no per-candidate reading of the
  Item 2.02 text: no later stage reads one, so `events build` prints them for the
  review instead (P7-15).

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/records.py`.
- Modify: `docs/data-dictionary.md` (appended), and
  `tests/contracts/test_data_dictionary.py` (by exact replacement).
- Test (create): `packages/earnings-ingestion/tests/test_events_records.py`.

**Interfaces:**

- Consumes: `cohort.records.Citation` and `OverrideCitation`;
  `cohort.digests.digest`; `canonical.records.IngestionRecord`; Task 5's
  `Convention`; `sec.identifiers.Cik`.
- Produces, in `events/records.py`:
  - `Accession`, a constrained string, and
    `PeriodicForm = Literal["10-Q", "10-K", "10-QT", "10-KT"]`;
  - the enums `EventStatus`, `EventReason`, `IdentificationMethod`,
    `EventFindingKind`, and `EventOverrideKind`;
  - `STATUS_OF: dict[EventReason, EventStatus]`, `UNIDENTIFIED`,
    `DECIDED_BY_MEMBERSHIP`, `BLOCKING`, and `ACKNOWLEDGEABLE`, frozensets;
  - `EventRow`, `EventFinding` (with `holds_freeze`), `EventOverride`,
    `EventOverridesFile`, `EventManifestDefinition`, `EventManifest`, and `UNHASHED`;
  - `FileEvidence`, `SkippedPage`, `EventCitations`, and `EventEvidence`;
  - `event_finding(kind, subject, detail, *, issuer_id=None) -> EventFinding`;
  - `content_hash(manifest: EventManifest) -> str`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_records.py`:

```python
"""Stage 5's records: event rows, findings, overrides, and the manifest's hash."""

from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.cohort.records import OverrideCitation
from earnings_ingestion.events.records import (
    EventFindingKind,
    EventManifest,
    EventManifestDefinition,
    EventOverride,
    EventOverrideKind,
    EventOverridesFile,
    EventReason,
    EventRow,
    EventStatus,
    IdentificationMethod,
    content_hash,
    event_finding,
)
from pydantic import ValidationError

ACCEPTED = datetime(2024, 10, 24, 20, 5, 12, tzinfo=UTC)
OPENER = "roster-2024-06-28:acme-common:member_at"


def row(**changes: object) -> EventRow:
    values = {
        "event_id": "cik-0009990001:2024-09-30",
        "issuer_id": "cik-0009990001",
        "cik": "0009990001",
        "period_end": date(2024, 9, 30),
        "reported_fiscal_year": 2025,
        "reported_fiscal_quarter": "Q1",
        "periodic_accession": "0009990001-24-000031",
        "periodic_form": "10-Q",
        "release_accession": "0009990001-24-000029",
        "candidate_accessions": ("0009990001-24-000029",),
        "identification_method": IdentificationMethod.STATED_PERIOD,
        "filing_acceptance_time": ACCEPTED,
        "first_publication_time": ACCEPTED,
        "source_timezone": "America/New_York",
        "first_publication_source_id": "sec-edgar",
        "membership_assertion_id": OPENER,
        "eligibility_status": EventStatus.ELIGIBLE,
        "eligibility_reason": EventReason.MEMBER_AT_PUBLICATION,
        "retained": False,
        "override_ids": (),
    }
    return EventRow(**(values | changes))


UNRELEASED = {
    "release_accession": None,
    "identification_method": None,
    "filing_acceptance_time": None,
    "first_publication_time": None,
    "first_publication_source_id": None,
    "membership_assertion_id": None,
    "eligibility_status": EventStatus.AMBIGUOUS,
    "eligibility_reason": EventReason.NO_RELEASE_FILING,
}


def test_an_eligible_row_keeps_every_time_and_label_apart() -> None:
    """R1.5 and P-A5: the period end, the labels, and both times are separate."""
    event = row()
    assert (event.period_end, event.reported_fiscal_quarter) == (
        date(2024, 9, 30),
        "Q1",
    )
    assert event.first_publication_time == event.filing_acceptance_time == ACCEPTED


def test_unknown_labels_stay_null_together() -> None:
    row(reported_fiscal_year=None, reported_fiscal_quarter=None)
    with pytest.raises(ValidationError, match="labels"):
        row(reported_fiscal_year=None)


def test_an_unidentified_release_has_no_times_and_no_assertion() -> None:
    event = row(**UNRELEASED)
    assert event.filing_acceptance_time is None
    with pytest.raises(ValidationError, match="release"):
        row(**(UNRELEASED | {"identification_method": IdentificationMethod.OVERRIDE}))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"event_id": "cik-0009990001:2024-09-29"}, "event_id"),
        ({"first_publication_time": datetime(2024, 10, 24, 20, 6, tzinfo=UTC)}, "EV9"),
        ({"eligibility_status": EventStatus.INELIGIBLE}, "status"),
        ({"retained": True}, "retained"),
        ({"membership_assertion_id": None}, "membership_assertion_id"),
        (
            {
                "eligibility_status": EventStatus.INELIGIBLE,
                "eligibility_reason": EventReason.PUBLISHED_AFTER_CUTOFF,
            },
            "membership_assertion_id",
        ),
        (
            {
                "filing_acceptance_time": datetime.fromisoformat(
                    "2024-10-24T16:05:12-04:00"
                ),
                "first_publication_time": datetime.fromisoformat(
                    "2024-10-24T16:05:12-04:00"
                ),
            },
            "UTC",
        ),
    ],
    ids=[
        "id-not-issuer-and-period",
        "publication-not-acceptance",
        "status-not-the-reasons",
        "retained-but-eligible",
        "member-without-assertion",
        "assertion-after-cutoff",
        "time-not-utc",
    ],
)
def test_an_inconsistent_row_is_refused(changes, message) -> None:
    with pytest.raises(ValidationError, match=message):
        row(**changes)


def test_a_retained_ambiguous_row_keeps_its_reason() -> None:
    event = row(**(UNRELEASED | {"retained": True, "override_ids": ("keep-it",)}))
    assert (event.eligibility_status, event.retained) == (EventStatus.AMBIGUOUS, True)


def test_a_finding_s_id_and_digest_follow_what_it_says() -> None:
    first = event_finding(
        EventFindingKind.PERIOD_GAP,
        "cik-0009990006:2025-03-31:2025-09-30",
        "no period end between 2025-03-31 and 2025-09-30",
        issuer_id="cik-0009990006",
    )
    assert first.finding_id == "period_gap:cik-0009990006:2025-03-31:2025-09-30"
    assert (first.blocking, first.holds_freeze) == (True, True)
    again = event_finding(
        EventFindingKind.PERIOD_GAP,
        "cik-0009990006:2025-03-31:2025-09-30",
        "no period end between 2025-03-31 and 2025-09-30",
        issuer_id="cik-0009990006",
    )
    assert again.digest == first.digest
    changed = event_finding(
        EventFindingKind.PERIOD_GAP,
        "cik-0009990006:2025-03-31:2025-09-30",
        "no period end between 2025-03-31 and 2025-10-01",
        issuer_id="cik-0009990006",
    )
    assert changed.digest != first.digest
    labels = event_finding(
        EventFindingKind.FISCAL_LABELS_UNKNOWN, "cik-0009990003:2024-09-30", "none"
    )
    assert (labels.blocking, labels.holds_freeze) == (False, False)


CITATION = OverrideCitation(
    source_id="sec-edgar",
    url="https://www.sec.gov/Archives/edgar/data/9990001/000999000125000009/0009990001-25-000009-index.htm",
)
SIGNED = {
    "rationale": "Reviewed.",
    "reviewer": "A Reviewer",
    "recorded_on": date(2026, 9, 28),
}


@pytest.mark.parametrize(
    ("fields", "foreign"),
    [
        (
            {
                "kind": EventOverrideKind.SET_RELEASE_FILING,
                "event_id": "cik-0009990001:2025-02-28",
                "accession": "0009990001-25-000009",
                "citations": (CITATION,),
            },
            {"finding_id": "period_gap:cik-0009990006:2024-07-01:2024-10-15"},
        ),
        (
            {
                "kind": EventOverrideKind.RETAIN_UNRESOLVED,
                "event_id": "cik-0009990005:2025-06-27",
                "reason": EventReason.NO_RELEASE_FILING,
            },
            {"accession": "0009990005-25-000020"},
        ),
        (
            {
                "kind": EventOverrideKind.ACKNOWLEDGE,
                "finding_id": "period_gap:cik-0009990006:2025-03-31:2025-09-30",
                "finding_digest": "0" * 64,
            },
            {"event_id": "cik-0009990006:2025-03-31"},
        ),
    ],
    ids=["set-release-filing", "retain-unresolved", "acknowledge"],
)
def test_each_override_sets_exactly_its_targets(fields, foreign) -> None:
    assert (
        EventOverride(override_id="decision-1", **fields, **SIGNED).kind
        is (fields["kind"])
    )
    with pytest.raises(ValidationError, match="exactly"):
        EventOverride(override_id="decision-1", **fields, **foreign, **SIGNED)


def test_setting_a_release_filing_cites_it() -> None:
    with pytest.raises(ValidationError, match="cites"):
        EventOverride(
            override_id="decision-1",
            kind=EventOverrideKind.SET_RELEASE_FILING,
            event_id="cik-0009990001:2025-02-28",
            accession="0009990001-25-000009",
            **SIGNED,
        )


def test_only_an_ambiguous_reason_is_retained() -> None:
    with pytest.raises(ValidationError, match="ambiguous"):
        EventOverride(
            override_id="decision-1",
            kind=EventOverrideKind.RETAIN_UNRESOLVED,
            event_id="cik-0009990005:2025-06-27",
            reason=EventReason.NOT_MEMBER_AT_PUBLICATION,
            **SIGNED,
        )


def test_an_overrides_file_holds_one_override_of_each_kind_per_event() -> None:
    """A set release filing may leave an event ambiguous, so one event may carry a
    ``set_release_filing`` and a ``retain_unresolved``, but never two of either."""
    retain = EventOverride(
        override_id="keep",
        kind=EventOverrideKind.RETAIN_UNRESOLVED,
        event_id="cik-0009990005:2025-06-27",
        reason=EventReason.SAME_DAY_TRANSITION,
        **SIGNED,
    )
    chosen = EventOverride(
        override_id="choose",
        kind=EventOverrideKind.SET_RELEASE_FILING,
        event_id="cik-0009990005:2025-06-27",
        accession="0009990005-25-000031",
        citations=(CITATION,),
        **SIGNED,
    )
    EventOverridesFile(schema_version=1, overrides=(chosen, retain))
    with pytest.raises(ValidationError, match="override_id repeated"):
        EventOverridesFile(schema_version=1, overrides=(retain, retain))
    twice = retain.model_copy(update={"override_id": "keep-again"})
    with pytest.raises(ValidationError, match="event_id repeated in one kind"):
        EventOverridesFile(schema_version=1, overrides=(retain, twice))


def manifest(**changes: object) -> EventManifest:
    definition = {
        "corpus_id": "djia-synthetic",
        "event_manifest_version": 1,
        "universe_id": "djia-synthetic",
        "universe_version": 1,
        "universe_operative_hash": "1" * 64,
        "discovery_policy_version": "release-id/1",
        "eligibility_policy_version": "eligibility/1",
        "public_information_cutoff": date(2026, 9, 22),
        "content_hash": "0" * 64,
        "created_at": datetime(2026, 9, 28, tzinfo=UTC),
    }
    rows = changes.pop("rows", (row(),))
    return EventManifest(
        schema_version=1,
        definition=EventManifestDefinition(**(definition | changes)),
        rows=rows,
        findings=(),
        overrides=(),
    )


def test_the_hash_leaves_out_the_version_the_time_and_the_universe_version() -> None:
    """P7-2: a cohort version with unchanged facts never re-versions the events."""
    first = content_hash(manifest())
    assert first == content_hash(
        manifest(
            event_manifest_version=2,
            universe_version=2,
            content_hash="f" * 64,
            created_at=datetime(2026, 10, 1, tzinfo=UTC),
        )
    )
    assert first != content_hash(manifest(universe_operative_hash="2" * 64))
    assert first != content_hash(manifest(rows=(row(reported_fiscal_year=2024),)))


def test_rows_are_unique_and_sorted_by_event_id() -> None:
    later = row(
        event_id="cik-0009990001:2024-12-31",
        period_end=date(2024, 12, 31),
        periodic_accession="0009990001-25-000003",
    )
    manifest(rows=(row(), later))
    with pytest.raises(ValidationError, match="sorted"):
        manifest(rows=(later, row()))
    with pytest.raises(ValidationError, match="sorted"):
        manifest(rows=(row(), row()))
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_records.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_records.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.records'`.

- [x] **Step 3: Write the records**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/records.py`:

```python
"""Stage 5's records: the event manifest, its evidence record, and the overrides
(the Stage 5 spec, §The event manifest and §Review overrides).

- **Rows.** An ``EventRow`` is one slot: an issuer's period end, the periodic report
  that made it, the release filing that first published its results, and its
  eligibility. One row serves as P's expected event and Stage 15's ledger entry.
- **The manifest.** ``EventManifest`` holds the definition, the rows, the findings,
  and the overrides applied. Its content hash covers them, less the definition's
  version, hash, creation time, and ``universe_version`` (plan 7, P7-2).
- **Evidence.** ``EventEvidence`` sits beside a frozen manifest, outside its hash, and
  cites what each row rests on (EV11). A re-fetch changes it and nothing else.
- **Overrides.** ``EventOverride`` is a reviewer's signed decision, read strictly from
  ``overrides.toml`` like Stage 4's (P6-18).

These are ingestion records and join ingestion schema version 1 (P6-5). A committed
record carries facts, URLs, hashes, and locators, never a source's wording (P6-3).
Rows, findings, and overrides carry facts only, never a retrieval time or a pointer
into one saved file, so a re-fetch never re-versions a manifest.
docs/data-dictionary.md documents every field and value.
"""

from collections import Counter
from datetime import date, timedelta
from enum import StrEnum
from typing import Annotated, Literal, Self

from earnings_core.artifacts import NonBlankStr
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    StringConstraints,
    model_validator,
)

from earnings_ingestion.canonical.records import IngestionRecord
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import Citation, OverrideCitation
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.sec.identifiers import Cik

Accession = Annotated[str, StringConstraints(pattern=r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")]
PeriodicForm = Literal["10-Q", "10-K", "10-QT", "10-KT"]


class _Part(BaseModel):
    """A nested part of an event record: immutable, closed, strictly typed."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class EventStatus(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    AMBIGUOUS = "ambiguous"


class EventReason(StrEnum):
    """Why an event has its status: the first of ``eligibility/1``'s checks that
    applies decides (S §Eligibility)."""

    PERIOD_END_OUTSIDE_WINDOW = "period_end_outside_window"
    NO_RELEASE_FILING = "no_release_filing"
    SEVERAL_RELEASE_FILINGS = "several_release_filings"
    PUBLISHED_AFTER_CUTOFF = "published_after_cutoff"
    MEMBER_AT_PUBLICATION = "member_at_publication"
    NOT_MEMBER_AT_PUBLICATION = "not_member_at_publication"
    SAME_DAY_TRANSITION = "same_day_transition"


STATUS_OF = {
    EventReason.PERIOD_END_OUTSIDE_WINDOW: EventStatus.INELIGIBLE,
    EventReason.NO_RELEASE_FILING: EventStatus.AMBIGUOUS,
    EventReason.SEVERAL_RELEASE_FILINGS: EventStatus.AMBIGUOUS,
    EventReason.PUBLISHED_AFTER_CUTOFF: EventStatus.INELIGIBLE,
    EventReason.MEMBER_AT_PUBLICATION: EventStatus.ELIGIBLE,
    EventReason.NOT_MEMBER_AT_PUBLICATION: EventStatus.INELIGIBLE,
    EventReason.SAME_DAY_TRANSITION: EventStatus.AMBIGUOUS,
}
UNIDENTIFIED = frozenset(
    {EventReason.NO_RELEASE_FILING, EventReason.SEVERAL_RELEASE_FILINGS}
)
DECIDED_BY_MEMBERSHIP = frozenset(
    {
        EventReason.MEMBER_AT_PUBLICATION,
        EventReason.NOT_MEMBER_AT_PUBLICATION,
        EventReason.SAME_DAY_TRANSITION,
    }
)


class IdentificationMethod(StrEnum):
    """How the release filing was identified (``release-id/1``)."""

    STATED_PERIOD = "stated_period"
    """The one candidate left, whose Item 2.02 text states the slot's period."""
    SOLE_CANDIDATE = "sole_candidate"
    """The one candidate left, whose text states no period that is judged."""
    OVERRIDE = "override"
    """A reviewer's ``set_release_filing``."""


class EventFindingKind(StrEnum):
    PERIOD_GAP = "period_gap"
    """An in-window period end may be missing (S §Slots)."""
    NO_SLOTS = "no_slots"
    """A candidate issuer with no slot."""
    FISCAL_LABELS_UNKNOWN = "fiscal_labels_unknown"
    """Companyfacts gives the periodic report no agreeing ``fy`` and ``fp``."""
    ACCEPTANCE_TIME_MISMATCH = "acceptance_time_mismatch"
    """A submissions ``acceptanceDateTime`` follows neither convention (EV10)."""
    ACCEPTANCE_TIME_UNKNOWN = "acceptance_time_unknown"
    """A filing whose side of the cutoff, or whose range, turns on a convention its
    file does not establish, or on a missing value (plan 7, P7-8)."""


BLOCKING = frozenset(
    {
        EventFindingKind.PERIOD_GAP,
        EventFindingKind.NO_SLOTS,
        EventFindingKind.ACCEPTANCE_TIME_MISMATCH,
        EventFindingKind.ACCEPTANCE_TIME_UNKNOWN,
    }
)
ACKNOWLEDGEABLE = frozenset({EventFindingKind.PERIOD_GAP, EventFindingKind.NO_SLOTS})


class EventOverrideKind(StrEnum):
    SET_RELEASE_FILING = "set_release_filing"
    """Name an event's release filing, citing it."""
    RETAIN_UNRESOLVED = "retain_unresolved"
    """Keep an ``ambiguous`` event with its reason, excluded from the pilot."""
    ACKNOWLEDGE = "acknowledge"
    """Accept one ``period_gap`` or ``no_slots`` finding, bound to its digest."""


class EventRow(_Part):
    """One slot: an issuer's period end, its release filing, and its eligibility."""

    event_id: IdPart
    issuer_id: IdPart
    cik: Cik
    period_end: date
    reported_fiscal_year: int | None
    reported_fiscal_quarter: NonBlankStr | None
    periodic_accession: Accession
    periodic_form: PeriodicForm
    release_accession: Accession | None
    candidate_accessions: tuple[Accession, ...]
    identification_method: IdentificationMethod | None
    filing_acceptance_time: AwareDatetime | None
    first_publication_time: AwareDatetime | None
    source_timezone: Literal["America/New_York"]
    first_publication_source_id: Literal["sec-edgar"] | None
    membership_assertion_id: IdPart | None
    eligibility_status: EventStatus
    eligibility_reason: EventReason
    retained: bool
    override_ids: tuple[IdPart, ...]

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.event_id != f"{self.issuer_id}:{self.period_end.isoformat()}":
            raise ValueError("event_id is <issuer_id>:<period_end>")
        labels = (self.reported_fiscal_year, self.reported_fiscal_quarter)
        if (labels[0] is None) != (labels[1] is None):
            raise ValueError("the fiscal labels are known or unknown together")
        release = (
            self.release_accession,
            self.identification_method,
            self.filing_acceptance_time,
            self.first_publication_time,
            self.first_publication_source_id,
        )
        if len({value is None for value in release}) != 1:
            raise ValueError("a release filing comes with its method and its times")
        if self.first_publication_time != self.filing_acceptance_time:
            raise ValueError("first publication is the filing's acceptance (EV9)")
        acceptance = self.filing_acceptance_time
        if acceptance is not None and acceptance.utcoffset() != timedelta(0):
            raise ValueError("times are stored as UTC instants")
        if STATUS_OF[self.eligibility_reason] is not self.eligibility_status:
            raise ValueError(f"{self.eligibility_reason} gives another status")
        if (self.eligibility_reason in UNIDENTIFIED) != (
            self.release_accession is None
            and self.eligibility_reason is not EventReason.PERIOD_END_OUTSIDE_WINDOW
        ):
            raise ValueError("only an unidentified release filing lacks one")
        if self.retained and self.eligibility_status is not EventStatus.AMBIGUOUS:
            raise ValueError("only an ambiguous event is retained")
        decided = self.eligibility_reason in DECIDED_BY_MEMBERSHIP
        if decided != (self.membership_assertion_id is not None):
            raise ValueError(
                "membership_assertion_id names the assertion that decided membership,"
                " and is null when an earlier check decided"
            )
        return self


class EventFinding(_Part):
    """One item of the event build's report."""

    finding_id: IdPart
    kind: EventFindingKind
    blocking: bool
    issuer_id: IdPart | None
    detail: NonBlankStr
    digest: Sha256Hex
    """SHA-256 of what the finding says, to which an acknowledgement is bound."""
    resolved_by: tuple[IdPart, ...]

    @property
    def holds_freeze(self) -> bool:
        return self.blocking and not self.resolved_by


def event_finding(
    kind: EventFindingKind,
    subject: str,
    detail: str,
    *,
    issuer_id: str | None = None,
) -> EventFinding:
    """A finding with id ``<kind>:<subject>`` and the digest of its content."""
    blocking = kind in BLOCKING
    content = {
        "kind": kind.value,
        "subject": subject,
        "detail": detail,
        "blocking": blocking,
        "issuer_id": issuer_id,
    }
    return EventFinding(
        finding_id=f"{kind.value}:{subject}",
        kind=kind,
        blocking=blocking,
        issuer_id=issuer_id,
        detail=detail,
        digest=digest(content),
        resolved_by=(),
    )


_TARGETS = {
    EventOverrideKind.SET_RELEASE_FILING: ("event_id", "accession"),
    EventOverrideKind.RETAIN_UNRESOLVED: ("event_id", "reason"),
    EventOverrideKind.ACKNOWLEDGE: ("finding_id", "finding_digest"),
}
_TARGET_FIELDS = sorted({name for names in _TARGETS.values() for name in names})


class EventOverride(_Part):
    """A reviewer's decision about one event or finding (S §Review overrides)."""

    override_id: IdPart
    kind: EventOverrideKind
    event_id: IdPart | None = None
    accession: Accession | None = None
    reason: EventReason | None = None
    finding_id: IdPart | None = None
    finding_digest: Sha256Hex | None = None
    citations: tuple[OverrideCitation, ...] = ()
    rationale: NonBlankStr
    reviewer: NonBlankStr
    recorded_on: date

    @model_validator(mode="after")
    def _targets(self) -> Self:
        needs = _TARGETS[self.kind]
        present = {name for name in _TARGET_FIELDS if getattr(self, name) is not None}
        if present != set(needs):
            raise ValueError(f"a {self.kind} override sets exactly {list(needs)}")
        if self.kind is EventOverrideKind.SET_RELEASE_FILING and not self.citations:
            raise ValueError("a set_release_filing override cites the filing")
        if (
            self.kind is EventOverrideKind.RETAIN_UNRESOLVED
            and STATUS_OF[self.reason] is not EventStatus.AMBIGUOUS
        ):
            raise ValueError("retain_unresolved keeps an ambiguous reason")
        return self


class EventOverridesFile(_Part):
    """``config/corpus/<corpus_id>/overrides.toml``."""

    schema_version: Literal[1]
    overrides: tuple[EventOverride, ...] = ()

    @model_validator(mode="after")
    def _distinct(self) -> Self:
        ids = Counter(override.override_id for override in self.overrides)
        if repeated := sorted(name for name, count in ids.items() if count > 1):
            raise ValueError(f"override_id repeated: {repeated}")
        events = Counter(
            (override.event_id, override.kind.value)
            for override in self.overrides
            if override.event_id is not None
        )
        repeated = [f"{event} ({kind})" for (event, kind), n in events.items() if n > 1]
        if repeated:
            raise ValueError(f"event_id repeated in one kind: {sorted(repeated)}")
        return self


class EventManifestDefinition(_Part):
    """The event manifest's definition (S §The event manifest)."""

    corpus_id: IdPart
    event_manifest_version: PositiveInt
    universe_id: IdPart
    universe_version: PositiveInt
    universe_operative_hash: Sha256Hex
    discovery_policy_version: NonBlankStr
    eligibility_policy_version: NonBlankStr
    public_information_cutoff: date
    content_hash: Sha256Hex
    created_at: AwareDatetime


UNHASHED = frozenset(
    {"event_manifest_version", "universe_version", "content_hash", "created_at"}
)


class EventManifest(IngestionRecord):
    """The frozen event manifest: P's expected events and Stage 15's ledger."""

    definition: EventManifestDefinition
    rows: tuple[EventRow, ...]
    findings: tuple[EventFinding, ...]
    overrides: tuple[EventOverride, ...]

    @model_validator(mode="after")
    def _sorted(self) -> Self:
        for name, keys in (
            ("rows", [row.event_id for row in self.rows]),
            ("findings", [finding.finding_id for finding in self.findings]),
            ("overrides", [override.override_id for override in self.overrides]),
        ):
            if keys != sorted(set(keys)):
                raise ValueError(f"{name} are unique and sorted by id")
        return self


def content_hash(manifest: EventManifest) -> str:
    """SHA-256 of the canonical JSON of the definition, less ``UNHASHED``, with the
    rows, the findings, and the overrides."""
    definition = manifest.definition.model_dump(mode="json", exclude=set(UNHASHED))
    return digest(
        {
            "definition": definition,
            "rows": [row.model_dump(mode="json") for row in manifest.rows],
            "findings": [f.model_dump(mode="json") for f in manifest.findings],
            "overrides": [o.model_dump(mode="json") for o in manifest.overrides],
        }
    )


class FileEvidence(_Part):
    """A submissions file or older page the build read, and its convention."""

    url: NonBlankStr
    sha256: Sha256Hex
    retrieved_at: AwareDatetime
    convention: Convention | None
    """``None`` when no row was cross-checked, or its rows follow both conventions."""
    rows_cross_checked: NonNegativeInt


class SkippedPage(_Part):
    """An older page the build did not read, and the dates that left it out."""

    url: NonBlankStr
    filing_from: date
    filing_to: date


class EventCitations(_Part):
    """What one event rests on (S §The event manifest, the evidence record)."""

    event_id: IdPart
    periodic_row: Citation
    """The periodic report's submissions row."""
    labels: Citation | None
    """Its companyfacts ``fy`` and ``fp``; ``None`` when unknown."""
    candidates: tuple[Citation, ...]
    """Each candidate's index page, at its Accepted value."""
    amendments: tuple[Citation, ...]
    """Each 8-K/A in the slot's range, recorded and never chosen by the rule."""
    release: Citation | None
    """The release filing's index page, at its Accepted value."""
    item_text: Citation | None
    """The release's Item 2.02 text, in its primary document's walker-1 text."""
    cross_check: Citation | None
    """The release's submissions row, at ``acceptanceDateTime``."""


class EventEvidence(IngestionRecord):
    """``events-v<N>.evidence.json``: the citations beside a frozen manifest (EV11)."""

    corpus_id: IdPart
    event_manifest_version: PositiveInt
    event_manifest_hash: Sha256Hex
    limitations: tuple[NonBlankStr, ...]
    files: tuple[FileEvidence, ...]
    skipped_pages: tuple[SkippedPage, ...]
    events: tuple[EventCitations, ...]
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/records.py`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_records.py -q`

Expected: `20 passed`.

- [x] **Step 5: Document the records**

Register every new model and enum in the drift test:

Create `/tmp/plan7-task6-dictionary.py`:

```python
"""Plan 7: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "tests/contracts/test_data_dictionary.py": [
        (
            "and of the ingestion records: the canonicalizer's, the capture's, layout-1's, the\n"
            "retrieval metadata, and the cohort's records and curated files.\n"
            "\n",
            "and of the ingestion records: the canonicalizer's, the capture's, layout-1's, the\n"
            "retrieval metadata, the cohort's records and curated files, and Stage 5's event\n"
            "records.\n"
            "\n",
        ),
        (
            "from earnings_ingestion.cohort import register as cohort_register\n"
            "from earnings_ingestion.fetch import records as fetch\n",
            "from earnings_ingestion.cohort import register as cohort_register\n"
            "from earnings_ingestion.events import acceptance\n"
            "from earnings_ingestion.events import records as events\n"
            "from earnings_ingestion.fetch import records as fetch\n",
        ),
        (
            "    cohort_register.RegisterEntry,\n"
            "]\n",
            "    cohort_register.RegisterEntry,\n"
            "    events.EventRow,\n"
            "    events.EventFinding,\n"
            "    events.EventOverride,\n"
            "    events.EventOverridesFile,\n"
            "    events.EventManifestDefinition,\n"
            "    events.EventManifest,\n"
            "    events.FileEvidence,\n"
            "    events.SkippedPage,\n"
            "    events.EventCitations,\n"
            "    events.EventEvidence,\n"
            "]\n",
        ),
        (
            "    cohort.FindingKind,\n"
            "]\n",
            "    cohort.FindingKind,\n"
            "    acceptance.Convention,\n"
            "    events.EventStatus,\n"
            "    events.EventReason,\n"
            "    events.IdentificationMethod,\n"
            "    events.EventFindingKind,\n"
            "    events.EventOverrideKind,\n"
            "]\n",
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

Apply `task6-dictionary`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: FAIL: `16 failed, 78 passed`. The dictionary has no section for the ten
models and six enums.

Append to `docs/data-dictionary.md`:

```markdown

## earnings-ingestion event records, schema version 1

- **Package.** `earnings_ingestion.events`, in `packages/earnings-ingestion` (Stage 5,
  plan 7): event discovery, eligibility, and the event and pilot freezes.
- **Schema version.** These records join ingestion schema version `1`, since no
  earlier record's fields changed. `EventManifest` and `EventEvidence` carry it as
  `schema_version`; the nested parts do not.
- **Facts, not incidental evidence** (EV11). An event row, finding, or override holds
  facts only: never a retrieval time, or a pointer into one saved file. Citations and
  retrieval times sit in the evidence record, outside the manifest's hash, so a
  re-fetch never re-versions a manifest.
- **Times.** Every time is a UTC instant. Every date judgment reads the instant's
  date on the America/New_York calendar (EV10).

### `Convention`

How a submissions file writes `acceptanceDateTime` (S Finding 1).

| Value | Meaning |
| --- | --- |
| `utc` | The true UTC instant |
| `eastern_digits` | The instant's Eastern wall-clock digits, followed by `Z` |

### `EventStatus`

| Value | Meaning |
| --- | --- |
| `eligible` | The issuer was a member when the release was first published |
| `ineligible` | Outside the window, published after the cutoff, or not a member |
| `ambiguous` | Unidentified release filing, or membership unordered at publication |

### `EventReason`

The first of `eligibility/1`'s checks that applies decides (S §Eligibility).

| Value | Meaning |
| --- | --- |
| `period_end_outside_window` | Check 1: `period_end` is outside `[2024-07-01, 2026-07-01)`; `ineligible` |
| `no_release_filing` | Check 2: no candidate is left; `ambiguous` |
| `several_release_filings` | Check 2: more than one candidate is left; `ambiguous` |
| `published_after_cutoff` | Check 3: the release's Eastern date is after the cutoff; `ineligible` |
| `member_at_publication` | Check 4: a security's interval holds the publication time; `eligible` |
| `not_member_at_publication` | Check 4: no interval holds it, and none is unordered; `ineligible` |
| `same_day_transition` | Check 4: a bound on the release's date leaves it unordered; `ambiguous` |

### `IdentificationMethod`

| Value | Meaning |
| --- | --- |
| `stated_period` | `release-id/1` left one candidate, whose Item 2.02 text states the slot's period |
| `sole_candidate` | `release-id/1` left one candidate, whose text states no period that is judged |
| `override` | A reviewer's `set_release_filing` named it |

### `EventFindingKind`

| Value | Meaning |
| --- | --- |
| `period_gap` | An in-window period end may be missing; blocking until acknowledged |
| `no_slots` | A candidate issuer has no slot; blocking until acknowledged |
| `fiscal_labels_unknown` | Companyfacts gives the periodic report no agreeing `fy` and `fp`; not blocking |
| `acceptance_time_mismatch` | A cross-checked `acceptanceDateTime` follows neither convention; blocking |
| `acceptance_time_unknown` | A filing's side of the cutoff or range turns on a convention its file does not establish, or on a missing value; blocking until its index page is saved (P7-8) |

### `EventOverrideKind`

| Value | Meaning |
| --- | --- |
| `set_release_filing` | Name an event's release filing, citing it |
| `retain_unresolved` | Keep an `ambiguous` event with its reason, excluded from the pilot |
| `acknowledge` | Accept one `period_gap` or `no_slots` finding, bound to its digest |

### `EventRow`

One slot: an issuer's period end, its release filing, and its eligibility. It serves
as P's expected event and as Stage 15's ledger entry.

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | `<issuer_id>:<period_end>` |
| `issuer_id` | ID part | The cohort's issuer |
| `cik` | 10 digits | The issuer's CIK |
| `period_end` | date | The periodic report's `reportDate` |
| `reported_fiscal_year` | int or null | Companyfacts' `fy` for the periodic report; null when unknown |
| `reported_fiscal_quarter` | string or null | Its `fp` as written, such as `Q1` or `FY`; null when unknown |
| `periodic_accession` | accession | The original 10-Q, 10-K, 10-QT, or 10-KT that made the slot |
| `periodic_form` | `10-Q`, `10-K`, `10-QT`, or `10-KT` | Its form |
| `release_accession` | accession or null | The release filing; null when unidentified |
| `candidate_accessions` | tuple of accession | The slot's candidates, by accession |
| `identification_method` | `IdentificationMethod` or null | How the release filing was identified |
| `filing_acceptance_time` | UTC datetime or null | The release filing's index-page Accepted value, read in America/New_York |
| `first_publication_time` | UTC datetime or null | Equal to `filing_acceptance_time`: an upper bound on first availability (EV9) |
| `source_timezone` | `America/New_York` | The zone the Accepted value is read in |
| `first_publication_source_id` | `sec-edgar` or null | The source of `first_publication_time` |
| `membership_assertion_id` | ID part or null | The assertion that decided check 4; null when an earlier check decided |
| `eligibility_status` | `EventStatus` | The status |
| `eligibility_reason` | `EventReason` | The reason, which implies the status |
| `retained` | bool | An `ambiguous` event kept by `retain_unresolved`, and excluded from the pilot |
| `override_ids` | tuple of ID part | The overrides applied to the event |

### `EventFinding`

| Field | Type | Meaning |
| --- | --- | --- |
| `finding_id` | ID part | `<kind>:<subject>` |
| `kind` | `EventFindingKind` | What was found |
| `blocking` | bool | It holds the freeze until resolved |
| `issuer_id` | ID part or null | The issuer concerned, if one |
| `detail` | string | What it says, in facts only |
| `digest` | 64 lowercase hex | SHA-256 of the canonical JSON of the finding's kind, subject, detail, blocking flag, and issuer |
| `resolved_by` | tuple of ID part | The acknowledgements that resolved it |

### `EventOverride`

A reviewer's decision (S §Review overrides). Exactly the targets its kind needs are
set.

| Field | Type | Meaning |
| --- | --- | --- |
| `override_id` | ID part | A curated slug |
| `kind` | `EventOverrideKind` | The decision |
| `event_id` | ID part or null | The event of `set_release_filing` and `retain_unresolved` |
| `accession` | accession or null | `set_release_filing`'s filing: an 8-K or 8-K/A of the issuer, accepted by the cutoff, whose index page is saved |
| `reason` | `EventReason` or null | `retain_unresolved`'s reason, one that makes the event `ambiguous` |
| `finding_id` | ID part or null | `acknowledge`'s finding |
| `finding_digest` | 64 lowercase hex or null | The digest of the finding as reviewed |
| `citations` | tuple of `OverrideCitation` | The evidence; required for `set_release_filing` |
| `rationale` | string | Why |
| `reviewer` | string | Who decided; the user, never an agent |
| `recorded_on` | date | When |

### `EventOverridesFile`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | The file's version |
| `overrides` | tuple of `EventOverride` | Unique `override_id`s, and at most one override of each kind per `event_id` |

### `EventManifestDefinition`

| Field | Type | Meaning |
| --- | --- | --- |
| `corpus_id` | ID part | `djia-2024q3-2026q2` |
| `event_manifest_version` | int ≥ 1 | The version; a new one only when the content changes |
| `universe_id` | ID part | The cohort read |
| `universe_version` | int ≥ 1 | The cohort version read; outside the content hash (P7-2) |
| `universe_operative_hash` | 64 lowercase hex | That version's `operative_hash` (EV4) |
| `discovery_policy_version` | string | `release-id/1` |
| `eligibility_policy_version` | string | `eligibility/1` |
| `public_information_cutoff` | date | `2026-09-22`, on the Eastern calendar |
| `content_hash` | 64 lowercase hex | See the frozen event manifests, below |
| `created_at` | UTC datetime | When this version was frozen |

### `EventManifest`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `definition` | `EventManifestDefinition` | The definition |
| `rows` | tuple of `EventRow` | One per slot, sorted by `event_id` |
| `findings` | tuple of `EventFinding` | Every finding, sorted by `finding_id` |
| `overrides` | tuple of `EventOverride` | Every override applied, sorted by `override_id` |

### `FileEvidence`

| Field | Type | Meaning |
| --- | --- | --- |
| `url` | string | A submissions file or older page the build read |
| `sha256` | 64 lowercase hex | Its bytes' hash |
| `retrieved_at` | UTC datetime | When they were retrieved |
| `convention` | `Convention` or null | The convention its cross-checked rows share; null when none was cross-checked, or they follow both |
| `rows_cross_checked` | int ≥ 0 | Its rows whose index page is saved |

### `SkippedPage`

| Field | Type | Meaning |
| --- | --- | --- |
| `url` | string | An older page the build did not read |
| `filing_from` | date | Its first filing date |
| `filing_to` | date | Its last. A page is skipped when this range misses `[2024-07-01, 2026-09-22]` |

### `EventCitations`

What one event rests on. Every citation is a Stage 4 `Citation`: an index page or
primary document through `walker-1`'s text, and a JSON file by pointer.

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | The event |
| `periodic_row` | `Citation` | The periodic report's submissions row |
| `labels` | `Citation` or null | Its companyfacts `accn`, `fy`, and `fp`; null when unknown |
| `candidates` | tuple of `Citation` | Each candidate's index page, at its Accepted value |
| `amendments` | tuple of `Citation` | Each 8-K/A in the slot's range, at its Accepted value: recorded, never chosen by the rule |
| `release` | `Citation` or null | The release filing's index page, at its Accepted value |
| `item_text` | `Citation` or null | The release's Item 2.02 text; null when its primary document is not saved or states none |
| `cross_check` | `Citation` or null | The release's submissions row, at `acceptanceDateTime` |

### `EventEvidence`

`events-v<N>.evidence.json`, written beside a frozen manifest and never replaced
(EV11).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `corpus_id` | ID part | The corpus |
| `event_manifest_version` | int ≥ 1 | The manifest it belongs to |
| `event_manifest_hash` | 64 lowercase hex | That manifest's `content_hash` |
| `limitations` | tuple of string | What the evidence cannot show |
| `files` | tuple of `FileEvidence` | Every submissions file and older page read |
| `skipped_pages` | tuple of `SkippedPage` | Every older page skipped by its dates |
| `events` | tuple of `EventCitations` | One per row |
```

Extract it with `python3 /tmp/plan7-extract.py docs/data-dictionary.md`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: `94 passed`.

- [x] **Step 6: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/records.py packages/earnings-ingestion/tests/test_events_records.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1046 passed, 24 deselected`; `All checks passed!` and
`224 files already formatted`.

- [x] **Step 7: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/records.py packages/earnings-ingestion/tests/test_events_records.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(events): define the event manifest, its evidence, and the overrides"
```

---

### Task 7: Saved responses, synthetic formats, and an issuer's placed filings

S §Store, client, and readers, and §Acceptance time. The build reads each candidate
issuer's filings from Stage 5's store, and places each filing it needs on the Eastern
calendar (P7-8).

- **`events/saved.py`.** `SavedResponses(store)` reads the store's retrieval records
  once, keeps the newest retrieval of each URL, and returns each response as a Stage 4
  `CitableArtifact`, cited with the `sec-edgar` source's rights as Stage 4 cites SEC
  (P7-12). `ArtifactStore.latest` rereads every record on each call, which would make
  a build of several hundred responses quadratic.
- **`events/synthetic.py`**, its first part: builders that write submissions files,
  older pages, and index pages in SEC's formats, for invented registrants, and
  `save`, which stores a response with its `Retrieval`, and `SyntheticStore`, which
  saves each response under the URL discovery would fetch it from. Later tasks' tests
  build their cases with them, and the synthetic event layer writes its committed
  fixture through them. Every name and word they write is invented.
- **`events/filings.py`.** `issuer_filings(saved, cik, issuer_id, *, start, cutoff)`:
  - reads the submissions file and each older page whose range meets
    `[start, cutoff]`, reads a page with no range, and records every page it skips
    by its dates (R1.1);
  - reads every saved index page of the issuer's filings, refusing one that names
    another accession (P7-13), and cross-checks each row against it with Task 5's
    `survey`, so each file gets its convention and each mismatch a blocking finding;
  - keeps each original periodic report with a report date that was accepted by the
    cutoff, placed by its index page, else by its file's convention, else by both
    readings when they agree on the side of the cutoff. Otherwise, or with no value,
    the report is `acceptance_time_unknown`;
  - keeps each Item 2.02 8-K or 8-K/A whose index page places it in `[start, cutoff]`.
    One that either convention places in range, with no index page saved, is a
    problem: discovery fetches those pages (P7-9).
  - Anything missing or unreadable is a problem, which the build lists and stops on.

At plan time, `issuer_filings` ran over Stage 4's saved submissions for v1's 33
candidate issuers, where no index page is saved yet. It raised no
`acceptance_time_unknown` and no mismatch: no periodic report lies near the cutoff
with readings on either side. It found 901 visible periodic reports, skipped 153
older pages by their dates, and named the 295 Item 2.02 index pages and 19 older
pages that discovery must fetch, which match S Finding 2 and S §Gates (plan A).

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/saved.py`,
  `events/synthetic.py`, and `events/filings.py`.
- Test (create): `packages/earnings-ingestion/tests/test_events_filings.py`.

**Interfaces:**

- Consumes: Task 4's readers and URLs; Task 5's `accepted_instant`, `eastern_date`,
  `eastern_dates`, `survey`, and `FileSurvey`; Task 6's `event_finding`,
  `EventFindingKind`, and `SkippedPage`; `cohort.locators.ArtifactText` and
  `CitableArtifact`; `cohort.register.SEC_RIGHTS` and `SEC_SOURCE_ID`;
  `fetch.store.ArtifactStore`.
- Produces:
  - `events/saved.py`: `SavedResponses(store)`, with `url in saved`, `len(saved)`,
    and `get(url) -> CitableArtifact | None`;
  - `events/synthetic.py`:
    - `JSON`, `HTML`, and `ITEM_TITLES`;
    - `SyntheticFiling(accession, form, filing_date, accepted, report_date=None, items=(), primary_document="", written=None)`;
    - `sec_timestamp(accepted, convention) -> str`;
    - `submissions_file(cik, name, filings, *, convention, older_pages=(), tickers=()) -> bytes`,
      `older_page_entry(name, filings) -> dict`, and
      `filings_page(filings, *, convention) -> bytes`;
    - `index_page(cik, filing, exhibits=()) -> bytes`, where each exhibit is
      `(description, file name, type)`;
    - `save(store, url, body, media_type, retrieved_at) -> None`;
    - `SyntheticStore(root, repo, retrieved_at)`, with `store`, `put(url, body, media_type)`,
      `submissions(cik, name, filings, *, convention, older_pages=())`,
      `older_page(name, filings, *, convention)`, and `index(cik, filing, exhibits=())`,
      each saving under the URL discovery would fetch it from. Tasks 8 and 9 add
      `companyfacts` and `document`;
  - `events/filings.py`:
    - `PERIODIC_FORMS`, `RELEASE_FORMS`, and `RESULTS_ITEM = "2.02"`;
    - `SavedFile(artifact, filings, survey)`;
    - `Placed(filing, file, index=None, index_artifact=None, instant=None)`, with
      `accepted_on -> date | None`;
    - `IssuerFilings(cik, registrant, files, skipped, periodic, releases, findings, problems)`;
    - `issuer_filings(saved, cik, issuer_id, *, start, cutoff) -> IssuerFilings`.

- [x] **Step 1: Write the failing tests**

The tests keep one issuer's responses in a temporary store, built with the synthetic
formats.

Create `packages/earnings-ingestion/tests/test_events_filings.py`:

```python
"""An issuer's saved filings, placed on the Eastern calendar (plan 7, P7-8)."""

from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.filings import IssuerFilings, issuer_filings
from earnings_ingestion.events.records import EventFindingKind, SkippedPage
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.synthetic import (
    HTML,
    JSON,
    SyntheticFiling,
    SyntheticStore,
    index_page,
    older_page_entry,
    save,
    submissions_file,
)
from earnings_ingestion.sec.data import read_submissions
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import (
    filing_index_url,
    submissions_page_url,
    submissions_url,
)

CIK = "0009990001"
ISSUER = "cik-0009990001"
START, CUTOFF = date(2024, 7, 1), date(2026, 9, 22)
RETRIEVED = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
EXHIBIT = (("PRESS RELEASE", "acme-ex991.htm", "EX-99.1"),)


def periodic(number: int, period: date, accepted: str, **fields) -> SyntheticFiling:
    return SyntheticFiling(
        accession=f"0009990001-{accepted[2:4]}-{number:06d}",
        form="10-Q",
        filing_date=date.fromisoformat(accepted[:10]),
        accepted=accepted,
        report_date=period,
        primary_document=f"acme-{period:%Y%m%d}.htm",
        **fields,
    )


def release(number: int, accepted: str, **fields) -> SyntheticFiling:
    values = {
        "accession": f"0009990001-{accepted[2:4]}-{number:06d}",
        "form": "8-K",
        "filing_date": date.fromisoformat(accepted[:10]),
        "accepted": accepted,
        "report_date": date.fromisoformat(accepted[:10]),
        "items": ("2.02", "9.01"),
        "primary_document": f"acme-8k-{number}.htm",
    }
    return SyntheticFiling(**(values | fields))


class Saved(SyntheticStore):
    """One issuer's synthetic responses, and its filings as the build reads them."""

    def submissions(self, filings, convention=Convention.UTC, pages=()) -> None:
        super().submissions(
            CIK,
            "Acme Industrial Corp",
            filings,
            convention=convention,
            older_pages=pages,
        )

    def page(self, name, filings, convention=Convention.UTC) -> None:
        self.older_page(name, filings, convention=convention)

    def index(self, filing, exhibits=EXHIBIT) -> None:
        super().index(CIK, filing, exhibits)

    def read(self) -> IssuerFilings:
        saved = SavedResponses(self.store)
        return issuer_filings(saved, CIK, ISSUER, start=START, cutoff=CUTOFF)


@pytest.fixture
def saved(tmp_path) -> Saved:
    return Saved(tmp_path / "data" / "raw" / "events", tmp_path, RETRIEVED)


def test_the_synthetic_formats_read_back() -> None:
    filing = release(29, "2024-10-24 16:05:12")
    registrant = read_submissions(
        submissions_file(
            CIK, "Acme Industrial Corp", [filing], convention=Convention.UTC
        )
    )
    (row,) = registrant.filings
    assert (row.accession, row.items) == (filing.accession, ("2.02", "9.01"))
    assert row.accepted_at == datetime(2024, 10, 24, 20, 5, 12, tzinfo=UTC)
    index = read_filing_index(index_page(CIK, filing, EXHIBIT))
    assert (index.accession, index.form, index.accepted) == (
        filing.accession,
        "8-K",
        "2024-10-24 16:05:12",
    )
    assert index.items == ("2.02", "9.01")
    assert [d.filename for d in index.exhibits_99()] == ["acme-ex991.htm"]


def test_older_pages_in_range_are_read_and_the_rest_skipped_by_their_dates(
    saved,
) -> None:
    old = [periodic(3, date(2024, 3, 31), "2024-05-02 16:30:00")]
    recent = [periodic(40, date(2024, 9, 30), "2024-11-04 16:30:00")]
    undated = [periodic(9, date(2023, 12, 31), "2024-02-20 16:30:00")]
    pages = [
        older_page_entry("CIK0009990001-submissions-001.json", recent),
        older_page_entry("CIK0009990001-submissions-002.json", old),
        {"name": "CIK0009990001-submissions-003.json", "filingCount": 1},
    ]
    saved.submissions([], pages=pages)
    saved.page("CIK0009990001-submissions-001.json", recent)
    saved.page("CIK0009990001-submissions-003.json", undated)
    read = saved.read()
    assert [file.artifact.url for file in read.files] == [
        submissions_url(CIK),
        submissions_page_url("CIK0009990001-submissions-001.json"),
        submissions_page_url("CIK0009990001-submissions-003.json"),
    ]
    assert read.skipped == (
        SkippedPage(
            url=submissions_page_url("CIK0009990001-submissions-002.json"),
            filing_from=date(2024, 5, 2),
            filing_to=date(2024, 5, 2),
        ),
    )
    assert [p.filing.report_date for p in read.periodic] == [
        date(2023, 12, 31),
        date(2024, 9, 30),
    ]
    assert read.problems == ()


def test_a_missing_response_is_a_problem(saved) -> None:
    assert saved.read().problems == (
        f"nothing saved from {submissions_url(CIK)}: run events discover",
    )
    recent = [periodic(40, date(2024, 9, 30), "2024-11-04 16:30:00")]
    pages = [older_page_entry("CIK0009990001-submissions-001.json", recent)]
    saved.submissions([], pages=pages)
    url = submissions_page_url("CIK0009990001-submissions-001.json")
    assert saved.read().problems == (f"nothing saved from {url}: run events discover",)


def test_an_index_page_places_a_release_and_cross_checks_its_row(saved) -> None:
    filing = release(29, "2024-10-24 16:05:12")
    saved.submissions([filing])
    saved.index(filing)
    read = saved.read()
    (placed,) = read.releases
    assert placed.instant == datetime(2024, 10, 24, 20, 5, 12, tzinfo=UTC)
    assert placed.accepted_on == date(2024, 10, 24)
    assert read.files[0].survey.convention is Convention.UTC
    assert (read.findings, read.problems) == ((), ())


def test_a_row_in_neither_convention_is_a_blocking_mismatch(saved) -> None:
    filing = release(29, "2024-10-24 16:05:12", written="2024-10-24T17:05:12.000Z")
    saved.submissions([filing])
    saved.index(filing)
    (finding,) = saved.read().findings
    assert finding.finding_id == f"acceptance_time_mismatch:{filing.accession}"
    assert finding.kind is EventFindingKind.ACCEPTANCE_TIME_MISMATCH
    assert finding.holds_freeze
    assert finding.detail == (
        f"{submissions_url(CIK)} gives 2024-10-24T17:05:12+00:00 for"
        f" {filing.accession}, whose index page says 2024-10-24 16:05:12 Eastern"
    )


LATE = "2026-09-23T01:30:00.000Z"
"""Under true UTC, 21:30 Eastern on the cutoff; as Eastern digits, the next day."""


@pytest.mark.parametrize(
    ("convention", "visible"),
    [(Convention.UTC, True), (Convention.EASTERN_DIGITS, False)],
)
def test_a_periodic_report_follows_its_file_s_convention(
    saved, convention, visible
) -> None:
    report = periodic(80, date(2026, 6, 30), "2026-09-22 21:30:00", written=LATE)
    anchor = release(70, "2026-07-23 16:05:00")
    saved.submissions([report, anchor], convention=convention)
    saved.index(anchor)
    read = saved.read()
    assert read.files[0].survey.convention is convention
    assert bool(read.periodic) is visible
    assert read.findings == ()


def test_a_side_of_the_cutoff_that_turns_on_an_unknown_convention_blocks(
    saved,
) -> None:
    report = periodic(80, date(2026, 6, 30), "2026-09-22 21:30:00", written=LATE)
    saved.submissions([report])
    read = saved.read()
    (finding,) = read.findings
    assert finding.finding_id == f"acceptance_time_unknown:{report.accession}"
    assert finding.holds_freeze
    assert finding.detail == (
        f"10-Q {report.accession}, filed 2026-09-22: acceptanceDateTime"
        " 2026-09-23T01:30:00+00:00 falls on 2026-09-22 or 2026-09-23, either side of"
        " the cutoff 2026-09-22, and its file establishes no convention"
    )
    assert read.periodic == ()
    saved.index(report)
    read = saved.read()
    assert (read.findings, len(read.periodic)) == ((), 1)


def test_readings_on_one_side_of_the_cutoff_need_no_convention(saved) -> None:
    before = periodic(80, date(2026, 6, 30), "2026-08-05 16:00:00")
    after = periodic(90, date(2026, 9, 30), "2026-10-05 16:00:00")
    saved.submissions([before, after])
    read = saved.read()
    assert [p.filing.accession for p in read.periodic] == [before.accession]
    assert read.findings == ()


def test_a_release_either_convention_places_in_range_needs_its_index_page(
    saved,
) -> None:
    edge = release(10, "2024-06-30 22:30:00")
    early = release(5, "2024-05-01 16:05:00")
    other = release(12, "2024-08-01 16:05:00", items=("7.01", "9.01"))
    saved.submissions([edge, early, other])
    url = filing_index_url(CIK, edge.accession)
    read = saved.read()
    assert read.problems == (f"nothing saved from {url}: run events discover",)
    saved.index(edge)
    read = saved.read()
    assert (read.problems, read.releases) == ((), ())


def test_a_missing_value_is_unknown_unless_filed_before_the_range(saved) -> None:
    report = periodic(80, date(2026, 6, 30), "2026-08-05 16:00:00", written="")
    unplaced = release(20, "2025-01-28 07:00:00", written="")
    early = release(5, "2024-05-01 16:05:00", written="")
    saved.submissions([report, unplaced, early])
    read = saved.read()
    assert [f.finding_id for f in read.findings] == [
        f"acceptance_time_unknown:{unplaced.accession}",
        f"acceptance_time_unknown:{report.accession}",
    ]
    assert read.findings[1].detail == (
        f"10-Q {report.accession}, filed 2026-08-05: no acceptanceDateTime"
    )


def test_an_index_page_of_another_filing_is_a_problem(saved) -> None:
    filing = release(29, "2024-10-24 16:05:12")
    other = replace(filing, accession="0009990001-24-000030")
    saved.submissions([filing])
    body = index_page(CIK, other, EXHIBIT)
    save(saved.store, filing_index_url(CIK, filing.accession), body, HTML, RETRIEVED)
    url = filing_index_url(CIK, filing.accession)
    assert saved.read().problems == (
        f"{url} is the index page of 0009990001-24-000030",
    )


def test_the_newest_retrieval_of_each_url_is_read(saved) -> None:
    first = [release(29, "2024-10-24 16:05:12")]
    saved.submissions(first)
    later = RETRIEVED.replace(day=29)
    body = submissions_file(CIK, "Acme Industrial Corp", [], convention=Convention.UTC)
    save(saved.store, submissions_url(CIK), body, JSON, later)
    responses = SavedResponses(saved.store)
    assert len(responses) == 1
    assert responses.get(submissions_url(CIK)).retrieved_at == later
    assert responses.get("https://www.sec.gov/nothing") is None
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_filings.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_filings.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.filings'`.

- [x] **Step 3: Write the saved responses, the formats, and the placement**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/saved.py`:

```python
"""Stage 5's saved SEC responses, indexed once per build (plan 7, P7-12).

``ArtifactStore.latest`` reads every retrieval record on each call. That suits
Stage 4's few dozen SEC files, but not the several hundred responses Stage 5 reads.
``SavedResponses`` reads the records once, keeps the newest retrieval of each URL,
and returns each artifact as a ``CitableArtifact``, which the store rechecks against
its name when it is first read.

Every response is cited with the ``sec-edgar`` source's rights, as Stage 4 cites
SEC's records (``cohort.register.SEC_RIGHTS``).
"""

from earnings_ingestion.cohort.locators import ArtifactText, CitableArtifact
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.fetch.store import ArtifactStore


class SavedResponses:
    """The newest saved response of each URL in one store's ``sec-edgar`` source."""

    def __init__(self, store: ArtifactStore) -> None:
        self.store = store
        newest: dict[str, Retrieval] = {}
        folder = store.root / SEC_SOURCE_ID / "retrievals"
        for path in sorted(folder.glob("*/*.json")):
            record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            known = newest.get(record.request_url)
            if known is None or (record.retrieved_at, record.sha256) > (
                known.retrieved_at,
                known.sha256,
            ):
                newest[record.request_url] = record
        self._newest = newest
        self._read: dict[str, CitableArtifact] = {}

    def __contains__(self, url: str) -> bool:
        return url in self._newest

    def __len__(self) -> int:
        return len(self._newest)

    def get(self, url: str) -> CitableArtifact | None:
        """The newest response saved from ``url``, or ``None``. Raises
        ``FileNotFoundError`` or ``ValueError`` if its bytes are gone or changed."""
        if url in self._read:
            return self._read[url]
        record = self._newest.get(url)
        if record is None:
            return None
        stored = self.store.get(
            SEC_SOURCE_ID,
            record.sha256,
            rights_status=SEC_RIGHTS.rights_status,
            rights_basis=SEC_RIGHTS.rights_basis,
        )
        citable = CitableArtifact(
            source_id=SEC_SOURCE_ID,
            url=url,
            artifact=stored.ref,
            retrieved_at=record.retrieved_at,
            text=ArtifactText(stored.body, stored.ref.media_type),
        )
        self._read[url] = citable
        return citable
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/saved.py`.

Create `packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py`:

```python
"""Synthetic SEC responses for Stage 5 (the Stage 5 spec, §The synthetic event layer).

The builders write submissions files, older pages, and index pages in SEC's formats,
as Stage 5's readers read them, for invented registrants. Tests build their cases
with them, and the synthetic event layer writes its committed fixture through them.
Every name and word they write is invented; none is copied from a filing.

Each builder returns bytes that depend on its arguments alone, so a fixture written
through them regenerates byte for byte.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from earnings_core import sha256_hex

from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.acceptance import Convention, accepted_instant
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.identifiers import unpad_cik
from earnings_ingestion.sec.urls import (
    filing_index_url,
    submissions_page_url,
    submissions_url,
)

JSON = "application/json"
HTML = "text/html"
ITEM_TITLES = {
    "2.02": "Results of Operations and Financial Condition",
    "5.02": "Departure of Directors or Certain Officers; Election of Directors",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}


@dataclass(frozen=True)
class SyntheticFiling:
    """One filing, as a submissions row and an index page describe it."""

    accession: str
    form: str
    filing_date: date
    accepted: str
    """The index page's Accepted value: Eastern wall time, ``YYYY-MM-DD HH:MM:SS``."""
    report_date: date | None = None
    items: tuple[str, ...] = ()
    primary_document: str = ""
    written: str | None = None
    """``acceptanceDateTime`` exactly as written; ``None`` writes it by the file's
    convention, and ``""`` leaves it empty."""


def sec_timestamp(accepted: str, convention: Convention) -> str:
    """``acceptanceDateTime`` as SEC writes it under ``convention``."""
    if convention is Convention.UTC:
        return accepted_instant(accepted).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return f"{accepted.replace(' ', 'T')}.000Z"


def _columns(filings: Sequence[SyntheticFiling], convention: Convention) -> dict:
    """SEC's column layout: one array per field, one index per filing."""
    return {
        "accessionNumber": [f.accession for f in filings],
        "filingDate": [f.filing_date.isoformat() for f in filings],
        "reportDate": [
            f.report_date.isoformat() if f.report_date else "" for f in filings
        ],
        "acceptanceDateTime": [
            sec_timestamp(f.accepted, convention) if f.written is None else f.written
            for f in filings
        ],
        "form": [f.form for f in filings],
        "items": [",".join(f.items) for f in filings],
        "primaryDocument": [f.primary_document for f in filings],
    }


def _json(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def older_page_entry(name: str, filings: Sequence[SyntheticFiling]) -> dict:
    """A submissions file's ``filings.files`` entry for an older page."""
    dates = sorted(filing.filing_date for filing in filings)
    return {
        "name": name,
        "filingCount": len(filings),
        "filingFrom": dates[0].isoformat(),
        "filingTo": dates[-1].isoformat(),
    }


def submissions_file(
    cik: str,
    name: str,
    filings: Sequence[SyntheticFiling],
    *,
    convention: Convention,
    older_pages: Sequence[Mapping[str, object]] = (),
    tickers: Sequence[str] = (),
) -> bytes:
    """A registrant's submissions JSON: its recent filings, newest first as SEC
    lists them, and the older pages ``filings.files`` names."""
    recent = sorted(filings, key=lambda f: (f.accepted, f.accession), reverse=True)
    return _json(
        {
            "cik": unpad_cik(cik),
            "name": name,
            "tickers": list(tickers),
            "formerNames": [],
            "filings": {
                "recent": _columns(recent, convention),
                "files": [dict(page) for page in older_pages],
            },
        }
    )


def filings_page(
    filings: Sequence[SyntheticFiling], *, convention: Convention
) -> bytes:
    """An older filings page: the same columns, at the top level."""
    ordered = sorted(filings, key=lambda f: (f.accepted, f.accession), reverse=True)
    return _json(_columns(ordered, convention))


def _row(sequence: str, description: str, href: str, name: str, kind: str) -> str:
    return (
        f'<tr><td scope="row">{sequence}</td><td scope="row">{description}</td>'
        f'<td scope="row"><a href="{href}">{name}</a></td>'
        f'<td scope="row">{kind}</td><td scope="row">1000</td></tr>'
    )


def index_page(
    cik: str,
    filing: SyntheticFiling,
    exhibits: Sequence[tuple[str, str, str]] = (),
) -> bytes:
    """A filing's EDGAR index page, shaped as EDGAR writes them. ``exhibits`` are
    ``(description, file name, type)`` after the primary document, in order."""
    folder = (
        f"/Archives/edgar/data/{unpad_cik(cik)}/{filing.accession.replace('-', '')}"
    )
    documents = [(filing.form, filing.primary_document, filing.form), *exhibits]
    rows = [
        _row(
            str(number),
            description,
            f"/ix?doc={folder}/{name}" if number == 1 else f"{folder}/{name}",
            name,
            kind,
        )
        for number, (description, name, kind) in enumerate(documents, start=1)
    ]
    rows.append(
        _row(
            "&nbsp;",
            "Complete submission text file",
            f"{folder}/{filing.accession}.txt",
            f"{filing.accession}.txt",
            "&nbsp;",
        )
    )
    groups = [
        (
            '<div class="formGrouping"><div class="infoHead">Filing Date</div>'
            f'<div class="info">{filing.filing_date.isoformat()}</div>'
            '<div class="infoHead">Accepted</div>'
            f'<div class="info">{filing.accepted}</div>'
            '<div class="infoHead">Documents</div>'
            f'<div class="info">{len(documents)}</div></div>'
        )
    ]
    if filing.report_date is not None:
        groups.append(
            '<div class="formGrouping"><div class="infoHead">Period of Report</div>'
            f'<div class="info">{filing.report_date.isoformat()}</div></div>'
        )
    if filing.items:
        lines = "".join(
            f"Item {item}: {ITEM_TITLES[item]}<br />" for item in filing.items
        )
        groups.append(
            '<div class="formGrouping"><div class="infoHead">Items</div>'
            f'<div class="info">{lines}</div></div>'
        )
    head = (
        "<tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th>"
        "<th>Size</th></tr>"
    )
    return (
        "<!DOCTYPE html><html><head><title>EDGAR Filing Documents for "
        f"{filing.accession}</title></head><body>"
        '<div class="formDiv"><div id="formHeader"><div id="formName">'
        f"<strong>Form {filing.form}</strong> - Filing</div>"
        '<div id="secNum"><strong>SEC Accession No.</strong> '
        f"{filing.accession}</div></div>"
        f'<div class="formContent">{"".join(groups)}</div></div>'
        '<table class="tableFile" summary="Document Format Files">'
        f"{head}{''.join(rows)}</table></body></html>\n"
    ).encode()


def save(
    store: ArtifactStore,
    url: str,
    body: bytes,
    media_type: str,
    retrieved_at: datetime,
) -> None:
    """Save ``body`` as a retrieval of ``url`` under the ``sec-edgar`` source."""
    retrieval = Retrieval(
        request_url=url,
        final_url=url,
        retrieved_at=retrieved_at,
        retrieval_method=RetrievalMethod.HTTP,
        http_status=200,
        media_type=media_type,
        content_type=media_type,
        byte_count=len(body),
        sha256=sha256_hex(body),
    )
    store.put(
        SEC_SOURCE_ID,
        body,
        retrieval,
        rights_status=SEC_RIGHTS.rights_status,
        rights_basis=SEC_RIGHTS.rights_basis,
    )


class SyntheticStore:
    """Synthetic responses saved into an artifact store, all at one retrieval time,
    each under the URL discovery would fetch it from."""

    def __init__(self, root: Path, repo: Path, retrieved_at: datetime) -> None:
        self.store = ArtifactStore(root, repo)
        self.retrieved_at = retrieved_at

    def put(self, url: str, body: bytes, media_type: str) -> None:
        save(self.store, url, body, media_type, self.retrieved_at)

    def submissions(
        self,
        cik: str,
        name: str,
        filings: Sequence[SyntheticFiling],
        *,
        convention: Convention,
        older_pages: Sequence[Mapping[str, object]] = (),
    ) -> None:
        body = submissions_file(
            cik, name, filings, convention=convention, older_pages=older_pages
        )
        self.put(submissions_url(cik), body, JSON)

    def older_page(
        self, name: str, filings: Sequence[SyntheticFiling], *, convention: Convention
    ) -> None:
        body = filings_page(filings, convention=convention)
        self.put(submissions_page_url(name), body, JSON)

    def index(
        self,
        cik: str,
        filing: SyntheticFiling,
        exhibits: Sequence[tuple[str, str, str]] = (),
    ) -> None:
        self.put(
            filing_index_url(cik, filing.accession),
            index_page(cik, filing, exhibits),
            HTML,
        )
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py`.

Create `packages/earnings-ingestion/src/earnings_ingestion/events/filings.py`:

```python
"""An issuer's filings, read from saved responses and placed on the Eastern calendar
(the Stage 5 spec, §Store, client, and readers, and §Acceptance time).

``issuer_filings`` reads the issuer's saved submissions file, and each older page
whose ``filingFrom``-``filingTo`` range meets ``[start, cutoff]``. A page that states
no range is read. Every other page is skipped by its dates, and the skip is
recorded (R1.1).

It then places each filing the build reads (plan 7, P7-8):

- **With its index page saved**, a filing takes the page's Accepted value as its
  acceptance time, and its submissions row is cross-checked against it. A row that
  follows neither convention is a blocking ``acceptance_time_mismatch``.
- **An original periodic report** without its index page is placed by its file's
  convention, which the file's cross-checked rows establish, or by both conventions
  when they establish none. It is visible when it was accepted by the cutoff. When
  the two readings fall on either side of the cutoff, or the row has no value, it
  is ``acceptance_time_unknown``, which blocks until its index page is saved
  (``earnings-pipeline events discover --filing``).
- **An Item 2.02 8-K or 8-K/A** is read from its index page, which discovery saved
  for every one that either convention places in the range. One without a value,
  filed on or after ``start``, is ``acceptance_time_unknown`` in the same way.

A saved response that is missing, unreadable, or for another accession is a
problem: no review can settle it, so the build stops and lists it.
"""

from dataclasses import dataclass
from datetime import date, datetime

from earnings_ingestion.cohort.locators import CitableArtifact
from earnings_ingestion.events.acceptance import (
    AcceptanceTimeError,
    FileSurvey,
    accepted_instant,
    eastern_date,
    eastern_dates,
    survey,
)
from earnings_ingestion.events.records import (
    EventFinding,
    EventFindingKind,
    SkippedPage,
    event_finding,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.sec.data import (
    Filing,
    Registrant,
    SecDataError,
    read_submissions,
    read_submissions_page,
)
from earnings_ingestion.sec.filing_index import FilingIndex, read_filing_index
from earnings_ingestion.sec.urls import (
    filing_index_url,
    submissions_page_url,
    submissions_url,
)

PERIODIC_FORMS = frozenset({"10-Q", "10-K", "10-QT", "10-KT"})
RELEASE_FORMS = frozenset({"8-K", "8-K/A"})
RESULTS_ITEM = "2.02"


@dataclass(frozen=True)
class SavedFile:
    """A submissions file or older page, as read."""

    artifact: CitableArtifact
    filings: tuple[Filing, ...]
    survey: FileSurvey


@dataclass(frozen=True)
class Placed:
    """A filing the build reads, with the file that lists it and its index page."""

    filing: Filing
    file: SavedFile
    index: FilingIndex | None = None
    index_artifact: CitableArtifact | None = None
    instant: datetime | None = None
    """The index page's Accepted value, as a UTC instant."""

    @property
    def accepted_on(self) -> date | None:
        """The Eastern date of ``instant``."""
        return None if self.instant is None else eastern_date(self.instant)


@dataclass(frozen=True)
class IssuerFilings:
    cik: str
    registrant: Registrant | None
    files: tuple[SavedFile, ...]
    skipped: tuple[SkippedPage, ...]
    periodic: tuple[Placed, ...]
    """Original periodic reports with a report date, accepted by the cutoff."""
    releases: tuple[Placed, ...]
    """Item 2.02 8-Ks and 8-K/As accepted in ``[start, cutoff]``, with index pages."""
    findings: tuple[EventFinding, ...]
    problems: tuple[str, ...]


def _unknown(issuer_id: str, filing: Filing, why: str) -> EventFinding:
    return event_finding(
        EventFindingKind.ACCEPTANCE_TIME_UNKNOWN,
        filing.accession,
        f"{filing.form} {filing.accession}, filed {filing.filing_date}: {why}",
        issuer_id=issuer_id,
    )


class _Reader:
    """Saved responses, read with each failure kept as a problem."""

    def __init__(self, saved: SavedResponses) -> None:
        self.saved = saved
        self.problems: list[str] = []

    def get(self, url: str) -> CitableArtifact | None:
        try:
            artifact = self.saved.get(url)
        except (FileNotFoundError, ValueError) as exc:
            self.problems.append(f"{url}: {exc}")
            return None
        if artifact is None:
            self.problems.append(f"nothing saved from {url}: run events discover")
        return artifact

    def files(
        self, cik: str, start: date, cutoff: date
    ) -> tuple[
        Registrant | None,
        list[tuple[CitableArtifact, tuple[Filing, ...]]],
        list[SkippedPage],
    ]:
        """The submissions file and the older pages in range, with their filings."""
        main = self.get(submissions_url(cik))
        if main is None:
            return None, [], []
        try:
            registrant = read_submissions(main.text.body)
        except SecDataError as exc:
            self.problems.append(f"{main.url}: {exc}")
            return None, [], []
        listed = [(main, registrant.filings)]
        skipped = []
        for page in registrant.older_pages:
            url = submissions_page_url(page.name)
            dated = page.filing_from is not None and page.filing_to is not None
            if dated and (page.filing_to < start or page.filing_from > cutoff):
                skipped.append(
                    SkippedPage(
                        url=url, filing_from=page.filing_from, filing_to=page.filing_to
                    )
                )
                continue
            artifact = self.get(url)
            if artifact is None:
                continue
            try:
                listed.append((artifact, read_submissions_page(artifact.text.body)))
            except SecDataError as exc:
                self.problems.append(f"{url}: {exc}")
        return registrant, listed, skipped

    def indexes(
        self, cik: str, filings: list[Filing]
    ) -> dict[str, tuple[FilingIndex, CitableArtifact, datetime]]:
        """Every saved index page of ``filings``, with its Accepted instant."""
        found = {}
        for filing in filings:
            url = filing_index_url(cik, filing.accession)
            if url not in self.saved or filing.accession in found:
                continue
            artifact = self.get(url)
            if artifact is None:
                continue
            try:
                index = read_filing_index(artifact.text.body)
                instant = accepted_instant(index.accepted)
            except (SecDataError, AcceptanceTimeError) as exc:
                self.problems.append(f"{url}: {exc}")
                continue
            if index.accession != filing.accession:
                self.problems.append(f"{url} is the index page of {index.accession}")
                continue
            found[filing.accession] = (index, artifact, instant)
        return found


def issuer_filings(
    saved: SavedResponses,
    cik: str,
    issuer_id: str,
    *,
    start: date,
    cutoff: date,
) -> IssuerFilings:
    """Read the issuer's saved filings, and place each one the build reads."""
    reader = _Reader(saved)
    registrant, listed, skipped = reader.files(cik, start, cutoff)
    indexes = reader.indexes(cik, [f for _, filings in listed for f in filings])
    instants = {accession: found[2] for accession, found in indexes.items()}
    findings = []
    files = []
    for artifact, filings in listed:
        checked = survey(artifact.url, filings, instants)
        files.append(SavedFile(artifact=artifact, filings=filings, survey=checked))
        for check in checked.mismatches:
            written = "no value" if check.written is None else check.written.isoformat()
            findings.append(
                event_finding(
                    EventFindingKind.ACCEPTANCE_TIME_MISMATCH,
                    check.accession,
                    f"{artifact.url} gives {written} for {check.accession}, whose"
                    f" index page says {indexes[check.accession][0].accepted} Eastern",
                    issuer_id=issuer_id,
                )
            )
    periodic, releases = [], []
    for file in files:
        for filing in file.filings:
            found = indexes.get(filing.accession)
            placed = Placed(filing, file, *found) if found else Placed(filing, file)
            if filing.form in PERIODIC_FORMS and filing.report_date is not None:
                visible = _visible(placed, file.survey, cutoff)
                if visible is None:
                    findings.append(_unknown(issuer_id, filing, _why(filing, cutoff)))
                elif visible:
                    periodic.append(placed)
            elif filing.form in RELEASE_FORMS and RESULTS_ITEM in filing.items:
                if found is not None:
                    if start <= placed.accepted_on <= cutoff:
                        releases.append(placed)
                elif filing.accepted_at is None:
                    if filing.filing_date >= start:
                        findings.append(
                            _unknown(issuer_id, filing, "no acceptanceDateTime")
                        )
                elif any(
                    start <= day <= cutoff
                    for day in eastern_dates(filing.accepted_at).values()
                ):
                    url = filing_index_url(cik, filing.accession)
                    if url not in saved:
                        reader.problems.append(
                            f"nothing saved from {url}: run events discover"
                        )
    return IssuerFilings(
        cik=cik,
        registrant=registrant,
        files=tuple(files),
        skipped=tuple(skipped),
        periodic=tuple(sorted(periodic, key=lambda p: p.filing.accession)),
        releases=tuple(sorted(releases, key=lambda p: p.filing.accession)),
        findings=tuple(sorted(findings, key=lambda f: f.finding_id)),
        problems=tuple(reader.problems),
    )


def _visible(placed: Placed, checked: FileSurvey, cutoff: date) -> bool | None:
    """Whether a periodic report was accepted by the cutoff; ``None`` when that
    turns on a convention its file does not establish, or on a missing value."""
    if placed.accepted_on is not None:
        return placed.accepted_on <= cutoff
    written = placed.filing.accepted_at
    if written is None:
        return None
    dates = eastern_dates(written)
    if checked.convention in dates:
        return dates[checked.convention] <= cutoff
    sides = {day <= cutoff for day in dates.values()}
    return sides.pop() if len(sides) == 1 else None


def _why(filing: Filing, cutoff: date) -> str:
    if filing.accepted_at is None:
        return "no acceptanceDateTime"
    readings = sorted(
        {day.isoformat() for day in eastern_dates(filing.accepted_at).values()}
    )
    return (
        f"acceptanceDateTime {filing.accepted_at.isoformat()} falls on"
        f" {' or '.join(readings)}, either side of the cutoff {cutoff}, and its file"
        " establishes no convention"
    )
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/filings.py`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_filings.py -q`

Expected: `13 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py packages/earnings-ingestion/tests/test_events_filings.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1059 passed, 24 deselected`; `All checks passed!` and
`228 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/saved.py packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py packages/earnings-ingestion/src/earnings_ingestion/events/filings.py packages/earnings-ingestion/tests/test_events_filings.py
git commit -m "feat(events): read an issuer's saved filings and place them on the Eastern calendar"
```

---

### Task 8: Slots, their guards, and their fiscal labels

S §Slots (step 1), EV6, and SV 6. A slot is one issuer's period end, and every later
step works slot by slot.

- **Slots.** `issuer_slots(filings, facts, issuer_id, *, start, stop)` takes Task 7's
  visible periodic reports. Each distinct report date in `[start, stop)` makes one
  slot, from its earliest-filed original report. Amendments never make slots, so no
  period end is inferred. Each slot records P′, the issuer's next visible period end,
  which bounds its candidates in Task 12.
- **Several securities.** Slots are per issuer, keyed by CIK, so an issuer with two
  securities has one slot per period by construction. Task 12's build shows it on
  the synthetic Dynamo (SV 6, P-VF).
- **Labels** come from companyfacts, as written (EV6). Unknown or disagreeing labels
  stay null, with a non-blocking `fiscal_labels_unknown` whose detail says which.
- **Guards.** `period_gap`'s three cases and `no_slots`, as S §Slots states them,
  each a blocking finding that an `acknowledge` answers. The subject names the gap's
  two edges, with the window's own bounds standing in for a missing neighbor:
  `period_gap:<issuer_id>:<since>:<until>`.
- **The tests** cover the half-open window at both ends, a report accepted after the
  cutoff, each gap case, `no_slots`, a Nike-like calendar that trips none, and the
  labels.
- **`companyfacts_file`** joins the synthetic formats, with
  `SyntheticStore.companyfacts`.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/slots.py`.
- Modify, by exact replacement: `packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py`.
- Test (create): `packages/earnings-ingestion/tests/test_events_slots.py`.

**Interfaces:**

- Consumes: Task 7's `IssuerFilings`, `Placed`, `issuer_filings`, `SavedResponses`,
  and `SyntheticStore`; Task 4's `CompanyFacts`, `FiscalLabels`, and
  `read_companyfacts`; Task 6's `event_finding` and `EventFindingKind`.
- Produces:
  - `events/slots.py`:
    - `LONGEST_GAP_DAYS = 105`, `FIRST_EDGE_DAYS = 92`, and `LAST_EDGE_DAYS = 91`;
    - `Slot(issuer_id, cik, period_end, periodic: Placed, next_period_end: date | None, labels: FiscalLabels | None)`,
      with `event_id -> str`;
    - `issuer_slots(filings, facts, issuer_id, *, start, stop) -> tuple[tuple[Slot, ...], tuple[EventFinding, ...]]`,
      each sorted;
  - `events/synthetic.py`: `companyfacts_file(cik, name, facts) -> bytes`, where
    `facts` is a sequence of `(accession, fy, fp)`, one fact each; and
    `SyntheticStore.companyfacts(cik, name, facts)`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_slots.py`:

```python
"""Slots, their guards, and their fiscal labels (the Stage 5 spec, §Slots)."""

from datetime import UTC, date, datetime, timedelta

import pytest
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.filings import issuer_filings
from earnings_ingestion.events.records import EventFindingKind
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import issuer_slots
from earnings_ingestion.events.synthetic import SyntheticFiling, SyntheticStore
from earnings_ingestion.sec.companyfacts import read_companyfacts
from earnings_ingestion.sec.urls import companyfacts_url

CIK = "0009990001"
ISSUER = "cik-0009990001"
START, STOP, CUTOFF = date(2024, 7, 1), date(2026, 7, 1), date(2026, 9, 22)
RETRIEVED = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


def report(period: date, *, form: str = "10-Q", lag: int = 35) -> SyntheticFiling:
    filed = period + timedelta(days=lag)
    return SyntheticFiling(
        accession=f"0009990001-{filed:%y}-{period:%m%d}00",
        form=form,
        filing_date=filed,
        accepted=f"{filed.isoformat()} 16:30:00",
        report_date=period,
        primary_document=f"acme-{period:%Y%m%d}.htm",
    )


QUARTERS = [
    date(2024, 3, 31),
    date(2024, 6, 30),
    date(2024, 9, 30),
    date(2024, 12, 31),
    date(2025, 3, 31),
    date(2025, 6, 30),
    date(2025, 9, 30),
    date(2025, 12, 31),
    date(2026, 3, 31),
    date(2026, 6, 30),
]
"""A calendar-quarter issuer's period ends, one before and eight in the window."""


def slots_of(tmp_path, reports, facts=None):
    """The issuer's slots and findings, from its saved submissions and companyfacts."""
    synthetic = SyntheticStore(tmp_path / "events", tmp_path, RETRIEVED)
    synthetic.submissions(CIK, "Acme", reports, convention=Convention.UTC)
    labels = [(r.accession, 2025, "Q1") for r in reports] if facts is None else facts
    synthetic.companyfacts(CIK, "Acme", labels)
    saved = SavedResponses(synthetic.store)
    filings = issuer_filings(saved, CIK, ISSUER, start=START, cutoff=CUTOFF)
    body = saved.get(companyfacts_url(CIK)).text.body
    return issuer_slots(
        filings, read_companyfacts(body), ISSUER, start=START, stop=STOP
    )


def test_one_slot_per_period_end_in_the_window(tmp_path) -> None:
    reports = [
        report(end, form="10-K" if end.month == 12 else "10-Q", lag=50)
        for end in QUARTERS
    ]
    amendment = SyntheticFiling(
        accession="0009990001-25-000777",
        form="10-Q/A",
        filing_date=date(2025, 6, 1),
        accepted="2025-06-01 12:00:00",
        report_date=date(2025, 3, 31),
    )
    slots, findings = slots_of(tmp_path, [*reports, amendment])
    assert [slot.period_end for slot in slots] == QUARTERS[2:]
    assert slots[0].event_id == "cik-0009990001:2024-09-30"
    assert slots[0].periodic.filing.form == "10-Q"
    assert (slots[0].next_period_end, slots[-1].next_period_end) == (
        date(2024, 12, 31),
        None,
    )
    assert findings == ()


def test_a_periodic_report_after_the_cutoff_makes_no_slot_and_no_successor(
    tmp_path,
) -> None:
    """The window's last quarter, filed after the cutoff, is not visible (P-C4)."""
    reports = [report(end) for end in QUARTERS[:-1]]
    late = report(date(2026, 6, 30), lag=90)
    slots, findings = slots_of(tmp_path, [*reports, late])
    assert slots[-1].period_end == date(2026, 3, 31)
    assert [f.finding_id for f in findings] == [
        "period_gap:cik-0009990001:2026-03-31:2026-07-01"
    ]


def test_a_nike_like_calendar_trips_no_guard(tmp_path) -> None:
    """The last in-window period ends 2026-05-31, and its successor is filed after
    the cutoff: the guards judge the window's edges by quarter length (S §Slots)."""
    ends = [
        date(2024, 5, 31),
        date(2024, 8, 31),
        date(2024, 11, 30),
        date(2025, 2, 28),
        date(2025, 5, 31),
        date(2025, 8, 31),
        date(2025, 11, 30),
        date(2026, 2, 28),
        date(2026, 5, 31),
    ]
    slots, findings = slots_of(tmp_path, [report(end) for end in ends])
    assert len(slots) == 8
    assert findings == ()


@pytest.mark.parametrize(
    ("missing", "finding"),
    [
        (
            date(2025, 6, 30),
            "period_gap:cik-0009990001:2025-03-31:2025-09-30",
        ),
        (None, "period_gap:cik-0009990001:2024-07-01:2024-12-31"),
        (date(2026, 6, 30), "period_gap:cik-0009990001:2026-03-31:2026-07-01"),
    ],
    ids=["between-two-period-ends", "no-predecessor", "no-successor"],
)
def test_each_period_gap_case_blocks(tmp_path, missing, finding) -> None:
    if missing is None:
        ends = QUARTERS[3:]
    else:
        ends = [end for end in QUARTERS if end != missing]
    _, findings = slots_of(tmp_path, [report(end) for end in ends])
    (found,) = findings
    assert found.finding_id == finding
    assert found.kind is EventFindingKind.PERIOD_GAP
    assert found.holds_freeze


def test_the_gap_s_detail_states_the_dates_and_days(tmp_path) -> None:
    ends = [end for end in QUARTERS if end != date(2025, 6, 30)]
    _, (found,) = slots_of(tmp_path, [report(end) for end in ends])
    assert found.detail == (
        "no period end is visible between 2025-03-31 and 2025-09-30, 183 days apart"
    )


def test_an_issuer_without_a_slot_blocks(tmp_path) -> None:
    _, findings = slots_of(tmp_path, [report(date(2024, 3, 31))])
    assert [f.finding_id for f in findings] == ["no_slots:cik-0009990001"]
    assert findings[0].detail == (
        "no original periodic report with a period end in [2024-07-01, 2026-07-01)"
        " was accepted by the cutoff"
    )


def test_labels_come_from_companyfacts_and_unknown_ones_are_reported(
    tmp_path,
) -> None:
    reports = [report(end) for end in QUARTERS]
    facts = [(reports[2].accession, 2024, "Q3"), (reports[3].accession, 2024, "FY")]
    facts += [(reports[4].accession, 2025, "Q1"), (reports[4].accession, 2025, "Q2")]
    slots, findings = slots_of(tmp_path, reports, facts)
    labels = [
        None if s.labels is None else (s.labels.fiscal_year, s.labels.fiscal_period)
        for s in slots
    ]
    assert labels[:3] == [(2024, "Q3"), (2024, "FY"), None]
    unknown = [f for f in findings if f.kind is EventFindingKind.FISCAL_LABELS_UNKNOWN]
    assert len(unknown) == 6
    assert not any(f.blocking for f in unknown)
    assert unknown[0].finding_id == "fiscal_labels_unknown:cik-0009990001:2025-03-31"
    assert unknown[0].detail == (
        f"companyfacts' facts of {reports[4].accession} disagree on fy and fp, or"
        " leave one out"
    )
    assert unknown[1].detail == (
        f"companyfacts holds no fact of {reports[5].accession}"
    )


def test_the_earliest_filed_original_report_of_a_period_makes_its_slot(
    tmp_path,
) -> None:
    first = report(date(2024, 9, 30), lag=35)
    second = SyntheticFiling(
        accession="0009990001-24-000999",
        form="10-Q",
        filing_date=date(2024, 11, 20),
        accepted="2024-11-20 09:00:00",
        report_date=date(2024, 9, 30),
    )
    reports = [first, second, *[report(end) for end in QUARTERS[3:]]]
    reports.insert(0, report(date(2024, 6, 30)))
    slots, _ = slots_of(tmp_path, reports)
    assert slots[0].periodic.filing.accession == first.accession


def test_the_window_is_half_open(tmp_path) -> None:
    """P-VF: period ends on each side of 2024-07-01 and of 2026-07-01."""
    ends = [date(2024, 6, 30), date(2024, 7, 1), date(2026, 6, 30), date(2026, 7, 1)]
    slots, _ = slots_of(tmp_path, [report(end, lag=20) for end in ends])
    assert [slot.period_end for slot in slots] == [date(2024, 7, 1), date(2026, 6, 30)]
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_slots.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_slots.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.slots'`.

- [x] **Step 3: Write the slots, and the companyfacts format**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/slots.py`:

```python
"""Slots, their guards, and their fiscal labels (the Stage 5 spec, §Slots, step 1).

- **Slots.** One per candidate issuer and period end. A period end is a distinct
  ``reportDate`` among the issuer's original 10-Q, 10-K, 10-QT, and 10-KT filings that
  were accepted by the cutoff, and a slot's lies in ``[start, stop)``. Amendments never
  make slots, so period ends are reported by the source, never inferred. When two
  original reports share a period end, the earlier filed makes the slot.
- **Labels** (EV6). A slot's ``reported_fiscal_year`` and ``reported_fiscal_quarter``
  are companyfacts' ``fy`` and ``fp`` for its periodic report, as written. Missing or
  disagreeing labels stay null, with a non-blocking ``fiscal_labels_unknown``.
- **Guards.** Each is a blocking finding that an ``acknowledge`` override answers.
  ``period_gap`` fires when an in-window period end may be missing:
  1. two consecutive visible period ends, at least one inside the window, lie more
     than 105 days apart;
  2. no visible period end precedes the first in-window one, which lies 92 or more
     days after ``start``;
  3. no visible period end follows the last in-window one, which lies more than 91
     days before ``stop``.

  The window's edges are judged by quarter length, never by filing lag, so a
  calendar like Nike's, whose next report is due after the cutoff, trips none.
  ``no_slots`` fires when a candidate issuer has no slot.
"""

from dataclasses import dataclass
from datetime import date
from itertools import pairwise

from earnings_ingestion.events.filings import IssuerFilings, Placed
from earnings_ingestion.events.records import (
    EventFinding,
    EventFindingKind,
    event_finding,
)
from earnings_ingestion.sec.companyfacts import CompanyFacts, FiscalLabels

LONGEST_GAP_DAYS = 105
FIRST_EDGE_DAYS = 92
LAST_EDGE_DAYS = 91


@dataclass(frozen=True)
class Slot:
    """One issuer's period end, the report that made it, and its labels."""

    issuer_id: str
    cik: str
    period_end: date
    periodic: Placed
    next_period_end: date | None
    """P': the issuer's next visible period end, if one is visible."""
    labels: FiscalLabels | None

    @property
    def event_id(self) -> str:
        return f"{self.issuer_id}:{self.period_end.isoformat()}"


def _gap(issuer_id: str, since: date, until: date, detail: str) -> EventFinding:
    return event_finding(
        EventFindingKind.PERIOD_GAP,
        f"{issuer_id}:{since.isoformat()}:{until.isoformat()}",
        detail,
        issuer_id=issuer_id,
    )


def issuer_slots(
    filings: IssuerFilings,
    facts: CompanyFacts,
    issuer_id: str,
    *,
    start: date,
    stop: date,
) -> tuple[tuple[Slot, ...], tuple[EventFinding, ...]]:
    """The issuer's slots, and the findings of its guards and labels."""
    reports: dict[date, Placed] = {}
    for placed in sorted(
        filings.periodic, key=lambda p: (p.filing.filing_date, p.filing.accession)
    ):
        reports.setdefault(placed.filing.report_date, placed)
    ends = sorted(reports)
    inside = [end for end in ends if start <= end < stop]
    findings = []
    if not inside:
        findings.append(
            event_finding(
                EventFindingKind.NO_SLOTS,
                issuer_id,
                "no original periodic report with a period end in"
                f" [{start}, {stop}) was accepted by the cutoff",
                issuer_id=issuer_id,
            )
        )
    for before, after in pairwise(ends):
        days = (after - before).days
        if (start <= before < stop or start <= after < stop) and (
            days > LONGEST_GAP_DAYS
        ):
            findings.append(
                _gap(
                    issuer_id,
                    before,
                    after,
                    f"no period end is visible between {before} and {after},"
                    f" {days} days apart",
                )
            )
    if inside:
        first, last = inside[0], inside[-1]
        if ends[0] == first and (first - start).days >= FIRST_EDGE_DAYS:
            findings.append(
                _gap(
                    issuer_id,
                    start,
                    first,
                    f"no period end is visible before {first},"
                    f" {(first - start).days} days after the window's start {start}",
                )
            )
        if ends[-1] == last and (stop - last).days > LAST_EDGE_DAYS:
            findings.append(
                _gap(
                    issuer_id,
                    last,
                    stop,
                    f"no period end is visible after {last},"
                    f" {(stop - last).days} days before the window's stop {stop}",
                )
            )
    slots = []
    for end in inside:
        placed = reports[end]
        accession = placed.filing.accession
        later = [other for other in ends if other > end]
        slot = Slot(
            issuer_id=issuer_id,
            cik=filings.cik,
            period_end=end,
            periodic=placed,
            next_period_end=later[0] if later else None,
            labels=facts.labels.get(accession),
        )
        if slot.labels is None:
            detail = (
                f"companyfacts' facts of {accession} disagree on fy and fp, or"
                " leave one out"
                if accession in facts.labels
                else f"companyfacts holds no fact of {accession}"
            )
            findings.append(
                event_finding(
                    EventFindingKind.FISCAL_LABELS_UNKNOWN,
                    slot.event_id,
                    detail,
                    issuer_id=issuer_id,
                )
            )
        slots.append(slot)
    return tuple(slots), tuple(sorted(findings, key=lambda f: f.finding_id))
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/slots.py`.

Create `/tmp/plan7-task8-synthetic.py`:

```python
"""Plan 7: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py": [
        (
            "from earnings_ingestion.sec.identifiers import unpad_cik\n"
            "from earnings_ingestion.sec.urls import (\n"
            "    filing_index_url,\n"
            "    submissions_page_url,\n",
            "from earnings_ingestion.sec.identifiers import unpad_cik\n"
            "from earnings_ingestion.sec.urls import (\n"
            "    companyfacts_url,\n"
            "    filing_index_url,\n"
            "    submissions_page_url,\n",
        ),
        (
            "    ordered = sorted(filings, key=lambda f: (f.accepted, f.accession), reverse=True)\n"
            "    return _json(_columns(ordered, convention))\n"
            "\n"
            "\n",
            "    ordered = sorted(filings, key=lambda f: (f.accepted, f.accession), reverse=True)\n"
            "    return _json(_columns(ordered, convention))\n"
            "\n"
            "\n"
            "def companyfacts_file(\n"
            "    cik: str, name: str, facts: Sequence[tuple[str, int | None, str | None]]\n"
            ") -> bytes:\n"
            "    \"\"\"Companyfacts JSON: one revenue fact per ``(accession, fy, fp)``, in order. Two\n"
            "    facts of one accession may state different labels, and ``None`` leaves one out.\"\"\"\n"
            "    entries = [\n"
            "        {\"accn\": accession, \"fp\": period, \"fy\": year, \"val\": 1000 + number}\n"
            "        for number, (accession, year, period) in enumerate(facts)\n"
            "    ]\n"
            "    return _json(\n"
            "        {\n"
            "            \"cik\": int(unpad_cik(cik)),\n"
            "            \"entityName\": name,\n"
            "            \"facts\": {\n"
            "                \"us-gaap\": {\n"
            "                    \"Revenues\": {\n"
            "                        \"label\": \"Revenues\",\n"
            "                        \"description\": \"Invented revenue.\",\n"
            "                        \"units\": {\"USD\": entries},\n"
            "                    }\n"
            "                }\n"
            "            },\n"
            "        }\n"
            "    )\n"
            "\n"
            "\n",
        ),
        (
            "            HTML,\n"
            "        )\n",
            "            HTML,\n"
            "        )\n"
            "\n"
            "    def companyfacts(\n"
            "        self,\n"
            "        cik: str,\n"
            "        name: str,\n"
            "        facts: Sequence[tuple[str, int | None, str | None]],\n"
            "    ) -> None:\n"
            "        self.put(companyfacts_url(cik), companyfacts_file(cik, name, facts), JSON)\n",
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

Apply `task8-synthetic`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_slots.py -q`

Expected: `11 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py packages/earnings-ingestion/tests/test_events_slots.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1070 passed, 24 deselected`; `All checks passed!` and
`230 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/slots.py packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py packages/earnings-ingestion/tests/test_events_slots.py
git commit -m "feat(events): make one slot per issuer and period end, with its guards and labels"
```

---

### Task 9: `release-id/1`, each slot's release filing

This task implements S §Candidates and `release-id/1` (step 2), EV3, and EV7. It picks
the 8-K that first published each slot's results. P7-7 records the readings, and
flags the one that departs from the spec's wording.

- **Candidates.** P′ is the slot's next visible period end, or the cutoff when none
  is visible.
  - **A candidate** is an original 8-K accepted after P and on or before P′, on the
    Eastern calendar. Its submissions items and its index page must both give
    Item 2.02, and the index page must list an exhibit typed `EX-99*`.
  - **An 8-K/A** in that range is an amendment. It is recorded, and the rule never
    chooses it.
  - **Any other Item 2.02 8-K** in the range is passed over, with the reason, so
    that the build's report can show it to the reviewer (P7-15).
- **The reading.** Each candidate's primary document is read in walker-1's text:
  - its Item 2.02 sections;
  - the dates it states after "ended" or "ending";
  - the fiscal periods it names, quarters first;
  - whether it calls its results preliminary.

  A document that walker-1 cannot read, that is not HTML, or that has no Item 2.02
  heading states nothing, and the rule keeps it. A primary document that is not
  saved is a problem, and the build stops on it.
- **The resolution.** Two kinds of candidate are dropped:
  - one whose judged statements all fail to match the slot;
  - one that calls its results preliminary.

  If one candidate is left, it is the release filing. Its method is `stated_period`
  if it has a matching statement, and `sole_candidate` otherwise. If none is left,
  the slot is `no_release_filing`. If several are left, it is
  `several_release_filings`.
- **The item text.** `Candidate.item_text()` cites the release's Item 2.02 sections
  in its document's walker-1 text. Task 12 records that citation in the evidence.
- **`eight_k` and `SyntheticStore.document`** join the synthetic formats. The tests
  build their 8-Ks with them. Every document here is invented. Each takes its shape,
  never its wording, from one of Finding 4's two-filing quarters.

At plan time, the reading and the resolution ran over the 16 primary documents of
Finding 4's eight two-filing quarters, which were fetched in the probe (P7-6). Two
assumptions apply:

- **Every document is taken as a candidate.** No index page is saved yet, so
  whether each page confirms Item 2.02 and lists an `EX-99*` exhibit is unknown
  until discovery.
- **Five issuers' labels are assumed.** The probe saved companyfacts only for IBM,
  Nike, and Coca-Cola. For Boeing, Caterpillar, Honeywell, Goldman Sachs, and
  Chevron, the labels a calendar-year filer's companyfacts gives were used.

The result, as a prediction for Task 20:

- **Five quarters resolve by rule:**
  - Boeing's, Chevron's, Nike's, and IBM's drop a preliminary filing;
  - Honeywell's for 2025-09-30 drops a recast that states other periods.
- **Three go to review as `several_release_filings`:**
  - Caterpillar's, whose other 8-K has no Item 2.02 heading although SEC lists
    the item;
  - Goldman Sachs', whose other 8-K states the quarter a transaction affects;
  - Honeywell's for 2026-03-31, whose recast restates the quarter.
- **With every slot's labels removed,** the split is the same. Only Boeing, Chevron,
  and Honeywell's 2025-09-30 quarter turn from `stated_period` to `sole_candidate`.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/release.py`.
- Modify, by exact replacement: `packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py`.
- Test (create): `packages/earnings-ingestion/tests/test_events_release.py`.

**Interfaces:**

- Consumes:
  - Task 7's `Placed`, `RESULTS_ITEM`, `issuer_filings`, and `SavedResponses`, with
    `SyntheticFiling`, `SyntheticStore`, `index_page`, `ITEM_TITLES`, and `HTML`;
  - Task 8's `Slot`, `issuer_slots`, and `SyntheticStore.companyfacts`;
  - Task 4's `FiscalLabels`, `read_companyfacts`, `archive_url`, `filing_index_url`,
    and `FilingIndex.exhibits_99()`;
  - Task 6's `EventReason` and `IdentificationMethod`;
  - Stage 4's `ArtifactText`, `CitableArtifact`, `LocatorError`, and `Citation`.
- Produces:
  - `events/release.py`:
    - `RELEASE_POLICY = "release-id/1"`;
    - `FiscalPeriod(year, period)`, printed as `Q3 2024` or `FY 2025`;
    - `Reading(sections, dates, periods, preliminary, unread)`;
    - `read_text(text) -> Reading` and `read_document(document) -> Reading`;
    - `Candidate(placed, document, reading, judged, matched)`, with
      `dropped -> str | None` and `item_text() -> Citation | None`;
    - `Identification(candidates, amendments, passed_over, release, method, reason, problems)`;
    - `identify(slot, releases, saved, *, cutoff) -> Identification`, where
      `releases` is `IssuerFilings.releases`. Task 12's build calls it for each
      slot and prints each candidate's reading and each passed-over filing (P7-15).
  - `events/synthetic.py`:
    - `eight_k(registrant, items, *, cover=False, signed=None) -> bytes`, where
      `items` is a sequence of `(item, paragraphs)`;
    - `SyntheticStore.document(cik, filing, body, media_type=HTML)`, which saves
      under `archive_url(cik, accession, primary_document)`. Task 11's layer writes
      its 8-Ks through it.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_release.py`:

```python
"""release-id/1: which candidate 8-K first published a slot's results (the Stage 5
spec, §Candidates and ``release-id/1``; plan 7, P7-7).

Every document here is invented. Each is shaped like one of the two-filing quarters
of the spec's Finding 4, never worded like one: a cover page that lists the items, a
section with no later heading, a preliminary release, a recast, a transaction's
effect on a quarter, and an 8-K with no Item 2.02 heading.
"""

from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.filings import issuer_filings
from earnings_ingestion.events.records import EventReason, IdentificationMethod
from earnings_ingestion.events.release import (
    RELEASE_POLICY,
    FiscalPeriod,
    Identification,
    identify,
    read_text,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import issuer_slots
from earnings_ingestion.events.synthetic import (
    HTML,
    SyntheticFiling,
    SyntheticStore,
    eight_k,
    index_page,
)
from earnings_ingestion.sec.companyfacts import read_companyfacts
from earnings_ingestion.sec.urls import archive_url, companyfacts_url, filing_index_url

CIK = "0009990001"
ISSUER = "cik-0009990001"
NAME = "Acme Industrial Corp"
START, STOP, CUTOFF = date(2024, 7, 1), date(2026, 7, 1), date(2026, 9, 22)
RETRIEVED = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
P = date(2024, 9, 30)
EXHIBIT = (("EARNINGS RELEASE", "ex991.htm", "EX-99.1"),)
NINE_01 = ("9.01", ["Exhibit 99.1 is furnished with this report."])


def text_of(*items, cover: bool = False) -> str:
    """The walker-1 text of an invented 8-K."""
    body = eight_k(NAME, items, cover=cover, signed=date(2024, 10, 24))
    return ArtifactText(body, HTML).canonical[0]


def reading_of(*paragraphs: str):
    return read_text(text_of(("2.02", paragraphs), NINE_01))


def test_the_policy_is_named() -> None:
    assert RELEASE_POLICY == "release-id/1"


def test_item_text_runs_from_each_item_2_02_heading_to_the_next_heading() -> None:
    """A cover page that lists the items gives Item 2.02 a heading with nothing under
    it; the sections are read together."""
    text = text_of(
        ("2.02", ["Acme Industrial Corp posted its third quarter of 2024 figures."]),
        ("8.01", ["Acme Industrial Corp moved its head office."]),
        cover=True,
    )
    reading = read_text(text)
    cover, body = (text[start:end] for start, end in reading.sections)
    assert cover.startswith("Item 2.02\t")
    assert "\n" not in cover
    assert body.startswith("Item 2.02 Results of Operations and Financial Condition")
    assert "head office" not in body
    assert reading.periods == (FiscalPeriod(2024, "Q3"),)


def test_a_section_with_no_later_heading_runs_to_the_end_of_the_text() -> None:
    """A guidance update's section runs through the signature, whose date is read as
    no period."""
    text = text_of(
        (
            "2.02",
            [
                "Acme Industrial Corp revised its outlook for the year.",
                "The revised range appears in the table below.",
            ],
        )
    )
    reading = read_text(text)
    ((start, end),) = reading.sections
    assert end == len(text.rstrip())
    assert "October 24, 2024" in text[start:end]
    assert reading.dates == ()


def test_a_document_with_no_item_2_02_heading_states_nothing() -> None:
    reading = read_text(
        text_of(("5.02", ["The board elected Dana Reyes a director."]), NINE_01)
    )
    assert reading.sections == ()
    assert reading.unread == "it has no Item 2.02 heading"
    assert (reading.dates, reading.periods, reading.preliminary) == ((), (), False)


@pytest.mark.parametrize(
    ("phrase", "dates"),
    [
        ("for the quarter ended September 30, 2024.", (date(2024, 9, 30),)),
        ("for the period ending Sept. 30, 2024.", (date(2024, 9, 30),)),
        ("for the fiscal year ended May 31, 2026.", (date(2026, 5, 31),)),
        ("for the quarter ended Dec. 31, 2024.", (date(2024, 12, 31),)),
        ("on October 24, 2024, for its latest quarter.", ()),
        ("for the quarter ended February 30, 2025.", ()),
        ("for the quarter ended September 30 2024.", ()),
    ],
    ids=[
        "ended",
        "ending-abbreviated",
        "may",
        "dec",
        "announced",
        "no-day",
        "no-comma",
    ],
)
def test_a_date_is_stated_after_ended_or_ending(phrase, dates) -> None:
    """An announcement date states no period (P7-7)."""
    assert reading_of(f"Acme Industrial Corp reported {phrase}").dates == dates


@pytest.mark.parametrize(
    ("phrase", "periods"),
    [
        ("its third quarter of 2024 results", {"Q3 2024"}),
        ("third-quarter 2024 earnings", {"Q3 2024"}),
        ("results for the second fiscal quarter of 2025", {"Q2 2025"}),
        ("the first quarter of fiscal 2026", {"Q1 2026"}),
        ("its fiscal 2025 second quarter", {"Q2 2025"}),
        ("its fiscal year 2025 first quarter", {"Q1 2025"}),
        ("Q3 2024 figures", {"Q3 2024"}),
        ("Q2 fiscal 2025 figures", {"Q2 2025"}),
        ("its 3Q 2024 figures", {"Q3 2024"}),
        ("fiscal 2025 figures", {"FY 2025"}),
        ("fiscal year 2025 figures", {"FY 2025"}),
        ("full year 2024 figures", {"FY 2024"}),
        ("full-year 2024 figures", {"FY 2024"}),
        ("fourth quarter and full year 2025 figures", {"FY 2025"}),
        (
            "the third quarter of 2024 against the third quarter of 2023",
            {"Q3 2024", "Q3 2023"},
        ),
        ("figures for the quarter and year", set()),
    ],
)
def test_fiscal_periods_are_read_quarters_before_years(phrase, periods) -> None:
    reading = reading_of(f"Acme Industrial Corp shared {phrase}.")
    assert {str(period) for period in reading.periods} == periods


@pytest.mark.parametrize(
    ("phrase", "preliminary"),
    [
        ("preliminary figures for the quarter", True),
        ("Preliminary figures for the quarter", True),
        ("its expected results for the quarter", True),
        ("its expected quarterly results", True),
        ("its expected third-quarter operating results", True),
        ("its expected strong and steady results", False),
        ("that the sale is expected to result in a gain", False),
        ("unexpected results for the quarter", False),
        ("results that were as expected", False),
    ],
)
def test_preliminary_results_are_read(phrase, preliminary) -> None:
    reading = reading_of(f"Acme Industrial Corp described {phrase}.")
    assert reading.preliminary is preliminary


def report(period: date, form: str, accepted: str) -> SyntheticFiling:
    return SyntheticFiling(
        accession=f"0009990001-{accepted[2:4]}-{period:%m%d}00",
        form=form,
        filing_date=date.fromisoformat(accepted[:10]),
        accepted=accepted,
        report_date=period,
        primary_document=f"acme-{period:%Y%m%d}.htm",
    )


REPORTS = [
    report(date(2024, 6, 30), "10-Q", "2024-08-01 16:30:00"),
    report(date(2024, 9, 30), "10-Q", "2024-11-01 16:30:00"),
    report(date(2024, 12, 31), "10-K", "2025-02-20 16:30:00"),
]
"""Acme's reports around the slot P = 2024-09-30, whose P' is 2024-12-31."""


class Issuer(SyntheticStore):
    """Acme's saved responses around one slot, and release-id/1's reading of it."""

    def __init__(self, root, repo) -> None:
        super().__init__(root, repo, RETRIEVED)
        self.filings = list(REPORTS)

    def release(
        self,
        number: int,
        accepted: str,
        *items,
        form: str = "8-K",
        exhibits=EXHIBIT,
        listed=("2.02", "9.01"),
        indexed=None,
    ) -> SyntheticFiling:
        """An 8-K that SEC lists with ``listed``, whose index page gives ``indexed``
        (by default ``listed``), and whose document holds ``items``; with no
        ``items``, its document is not saved."""
        filing = SyntheticFiling(
            accession=f"0009990001-{accepted[2:4]}-{number:06d}",
            form=form,
            filing_date=date.fromisoformat(accepted[:10]),
            accepted=accepted,
            report_date=date.fromisoformat(accepted[:10]),
            items=listed,
            primary_document=f"acme-8k-{number}.htm",
        )
        self.filings.append(filing)
        shown = filing if indexed is None else replace(filing, items=indexed)
        self.put(
            filing_index_url(CIK, filing.accession),
            index_page(CIK, shown, exhibits),
            HTML,
        )
        if items:
            body = eight_k(NAME, [*items, NINE_01], signed=filing.filing_date)
            self.document(CIK, filing, body)
        return filing

    def identify(
        self, labels=(2024, "Q3"), labelled=REPORTS[1]
    ) -> dict[date, Identification]:
        """Each slot's identification, by period end; the ``labelled`` report, by
        default P's, has ``labels``."""
        self.submissions(CIK, NAME, self.filings, convention=Convention.UTC)
        facts = [] if labels is None else [(labelled.accession, *labels)]
        self.companyfacts(CIK, NAME, facts)
        saved = SavedResponses(self.store)
        filings = issuer_filings(saved, CIK, ISSUER, start=START, cutoff=CUTOFF)
        body = saved.get(companyfacts_url(CIK)).text.body
        slots, _ = issuer_slots(
            filings, read_companyfacts(body), ISSUER, start=START, stop=STOP
        )
        return {
            slot.period_end: identify(slot, filings.releases, saved, cutoff=CUTOFF)
            for slot in slots
        }


@pytest.fixture
def acme(tmp_path) -> Issuer:
    return Issuer(tmp_path / "data" / "raw" / "events", tmp_path)


def accessions(candidates) -> list[str]:
    return [candidate.placed.filing.accession for candidate in candidates]


def test_the_preliminary_filing_is_dropped_and_the_actual_release_chosen(
    acme,
) -> None:
    early = acme.release(
        31,
        "2024-10-09 07:30:00",
        (
            "2.02",
            ["Acme Industrial Corp gave preliminary third quarter of 2024 sales."],
        ),
    )
    actual = acme.release(
        40,
        "2024-10-24 16:05:00",
        ("2.02", ["Acme Industrial Corp published its third quarter of 2024 results."]),
    )
    found = acme.identify()[P]
    assert accessions(found.candidates) == [early.accession, actual.accession]
    assert found.candidates[0].dropped == "it calls its results preliminary"
    assert found.release.placed.filing.accession == actual.accession
    assert (found.method, found.reason) == (IdentificationMethod.STATED_PERIOD, None)
    assert found.problems == ()


def test_a_recast_that_states_other_periods_is_dropped(acme) -> None:
    actual = acme.release(
        40,
        "2024-10-24 16:05:00",
        ("2.02", ["Acme Industrial Corp published its third-quarter 2024 earnings."]),
    )
    acme.release(
        52,
        "2024-12-10 16:05:00",
        (
            "2.02",
            [
                (
                    "Acme Industrial Corp will report Fluid Systems as its own"
                    " segment starting in the first quarter of 2025."
                ),
                (
                    "Exhibit 99.1 restates its segments for the three months ended"
                    " March 31, 2024."
                ),
            ],
        ),
    )
    found = acme.identify()[P]
    assert [c.dropped for c in found.candidates] == [
        None,
        "it states another period",
    ]
    assert found.release.placed.filing.accession == actual.accession
    assert found.method is IdentificationMethod.STATED_PERIOD


def test_two_candidates_the_rule_cannot_separate_are_ambiguous(acme) -> None:
    """A transaction's effect on the quarter states the quarter, as the release does."""
    acme.release(
        33,
        "2024-10-08 17:00:00",
        (
            "2.02",
            [
                (
                    "Acme Industrial Corp agreed to sell its Tooling division, which"
                    " it estimates will add $0.12 to diluted earnings per share for"
                    " the third quarter of 2024."
                )
            ],
        ),
        ("8.01", ["The sale awaits approval."]),
    )
    acme.release(
        40,
        "2024-10-24 16:05:00",
        (
            "2.02",
            [
                "Acme Industrial Corp posted results for the quarter ended September 30, 2024."
            ],
        ),
    )
    found = acme.identify()[P]
    assert [c.dropped for c in found.candidates] == [None, None]
    assert (found.release, found.method) == (None, None)
    assert found.reason is EventReason.SEVERAL_RELEASE_FILINGS


def test_a_candidate_with_no_item_2_02_heading_stays(acme) -> None:
    """SEC lists Item 2.02 for an 8-K whose document holds none: it states nothing,
    so the rule keeps it, and review decides."""
    director = acme.release(
        29,
        "2024-10-11 08:30:00",
        ("5.02", ["The board elected Dana Reyes a director."]),
        listed=("2.02", "7.01", "9.01"),
    )
    acme.release(
        40,
        "2024-10-24 16:05:00",
        (
            "2.02",
            [
                "Acme Industrial Corp posted results for the quarter ended September 30, 2024."
            ],
        ),
    )
    found = acme.identify()[P]
    assert found.candidates[0].placed.filing.accession == director.accession
    assert found.candidates[0].reading.unread == "it has no Item 2.02 heading"
    assert found.candidates[0].dropped is None
    assert found.reason is EventReason.SEVERAL_RELEASE_FILINGS


@pytest.mark.parametrize(
    ("labels", "paragraph", "method"),
    [
        (
            (2024, "Q3"),
            "Acme Industrial Corp published its third quarter of 2024 results.",
            IdentificationMethod.STATED_PERIOD,
        ),
        (
            None,
            "Acme Industrial Corp published its third quarter of 2024 results.",
            IdentificationMethod.SOLE_CANDIDATE,
        ),
        (
            None,
            (
                "Acme Industrial Corp published results for the quarter ended"
                " September 30, 2024."
            ),
            IdentificationMethod.STATED_PERIOD,
        ),
        (
            (2024, "Q3"),
            (
                "On October 24, 2024, Acme Industrial Corp issued a news release on"
                " its results, furnished as Exhibit 99.1."
            ),
            IdentificationMethod.SOLE_CANDIDATE,
        ),
    ],
    ids=["labels", "no-labels", "date", "narrative-only"],
)
def test_a_sole_candidate_is_stated_period_only_with_a_matching_statement(
    acme, labels, paragraph, method
) -> None:
    """A fiscal period is judged only against labels; an announcement date states no
    period, so a narrative-only release is kept."""
    acme.release(40, "2024-10-24 16:05:00", ("2.02", [paragraph]))
    found = acme.identify(labels)[P]
    assert found.method is method
    assert found.release.dropped is None


@pytest.mark.parametrize(
    ("labels", "statement", "dropped"),
    [
        ((2024, "FY"), "its fourth quarter of 2024 results", None),
        ((2024, "FY"), "its full-year 2024 results", None),
        ((2024, "FY"), "its third quarter of 2024 results", "it states another period"),
        (
            (2024, "FY"),
            "its fourth quarter of 2023 results",
            "it states another period",
        ),
        ((2024, "H2"), "its third quarter of 2024 results", None),
    ],
    ids=["fourth-quarter", "full-year", "another-quarter", "another-year", "unjudged"],
)
def test_fy_labels_match_the_fourth_quarter_or_the_full_year(
    acme, labels, statement, dropped
) -> None:
    """A 10-K's ``FY`` is never renamed ``Q4``; an ``fp`` other than ``Q1``-``Q3``
    or ``FY`` judges nothing."""
    item = ("2.02", [f"Acme Industrial Corp published {statement}."])
    acme.release(70, "2025-01-28 16:05:00", item)
    found = acme.identify(labels, REPORTS[2])[date(2024, 12, 31)]
    assert found.candidates[0].dropped == dropped


def test_candidates_are_accepted_after_p_and_by_p_prime_on_the_eastern_calendar(
    acme,
) -> None:
    """P' is the next visible period end, or the cutoff when none is visible."""
    item = ("2.02", ["Acme Industrial Corp published its quarterly results."])
    late_on_p = acme.release(20, "2024-09-30 23:00:00", item)
    first = acme.release(21, "2024-10-01 00:30:00", item)
    on_p_prime = acme.release(60, "2024-12-31 18:00:00", item)
    next_year = acme.release(61, "2025-01-02 07:00:00", item)
    found = acme.identify()
    assert late_on_p.accession not in accessions(found[P].candidates)
    assert accessions(found[P].candidates) == [first.accession, on_p_prime.accession]
    assert accessions(found[date(2024, 12, 31)].candidates) == [next_year.accession]


def test_the_index_page_decides_candidacy(acme) -> None:
    """Any exhibit typed EX-99*, and Items that confirm 2.02; an 8-K/A is recorded
    and never chosen."""
    item = (
        "2.02",
        ["Acme Industrial Corp published its third quarter of 2024 results."],
    )
    plain = acme.release(
        40, "2024-10-24 16:05:00", item, exhibits=(("NEWS", "a.htm", "EX-99"),)
    )
    padded = acme.release(
        41, "2024-10-25 09:00:00", item, exhibits=(("NEWS", "b.htm", "EX-99.01"),)
    )
    acme.release(
        42, "2024-10-28 09:00:00", item, exhibits=(("PLAN", "c.htm", "EX-10.1"),)
    )
    acme.release(43, "2024-10-29 09:00:00", item, indexed=("7.01", "9.01"))
    amended = acme.release(44, "2024-10-30 09:00:00", item, form="8-K/A")
    found = acme.identify()[P]
    assert accessions(found.candidates) == [plain.accession, padded.accession]
    assert [(p.filing.accession[-2:], why) for p, why in found.passed_over] == [
        ("42", "its index page lists no exhibit typed EX-99*"),
        ("43", "its index page lists no Item 2.02"),
    ]
    assert [p.filing.accession for p in found.amendments] == [amended.accession]
    assert found.reason is EventReason.SEVERAL_RELEASE_FILINGS


def test_an_unsaved_primary_document_is_a_problem(acme) -> None:
    filing = acme.release(40, "2024-10-24 16:05:00")
    url = archive_url(CIK, filing.accession, filing.primary_document)
    found = acme.identify()[P]
    assert found.problems == (f"nothing saved from {url}: run events discover",)
    assert found.candidates[0].reading.unread == "nothing saved"


@pytest.mark.parametrize(
    ("body", "media_type", "unread"),
    [
        (
            b"<html><body></body></html>",
            HTML,
            "walker-1 cannot read it: no text is left after N1",
        ),
        (b"Item 2.02 Results", "text/plain", "it is text/plain, not HTML"),
    ],
    ids=["walker-1-fails", "not-html"],
)
def test_a_document_the_rule_cannot_read_states_nothing(
    acme, body, media_type, unread
) -> None:
    filing = acme.release(40, "2024-10-24 16:05:00")
    acme.document(CIK, filing, body, media_type)
    found = acme.identify()[P]
    assert found.candidates[0].reading.unread == unread
    assert found.method is IdentificationMethod.SOLE_CANDIDATE
    assert found.problems == ()


def test_the_release_cites_its_item_text(acme) -> None:
    acme.release(
        40,
        "2024-10-24 16:05:00",
        ("2.02", ["Acme Industrial Corp published its third quarter of 2024 results."]),
    )
    found = acme.identify()[P]
    citation = found.release.item_text()
    assert citation.url == archive_url(
        CIK, found.release.placed.filing.accession, "acme-8k-40.htm"
    )
    (locator,) = citation.locators
    assert locator.canonicalization_version == "walker-1"
    cited = found.release.document.text.cited(locator)
    assert cited.startswith("Item 2.02 Results of Operations and Financial Condition")
    assert cited.endswith("third quarter of 2024 results.")
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_release.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_release.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.release'`.

- [x] **Step 3: Write the rule, and the 8-K format**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/release.py`:

```python
"""``release-id/1``: which candidate 8-K first published a slot's results (the Stage 5
spec, §Candidates and ``release-id/1``; plan 7, P7-7).

**Candidates.** Take a slot with period end P. P' is the issuer's next visible period
end, or the cutoff when none is visible. A candidate is an original 8-K accepted after
P and on or before P', on the Eastern calendar, whose submissions items and index page
both give Item 2.02, and whose index page lists an exhibit typed ``EX-99*``. An 8-K/A
in that range is an amendment: recorded, and never chosen by the rule. Any other
Item 2.02 8-K in the range is passed over, with the reason, for review.

**The reading.** Each candidate's primary document is read in walker-1's text:

1. *Item text.* Each line that begins "Item 2.02" opens a section, which runs to the
   next line that begins "Item" and a number, or to the end of the text. A cover page
   that lists the items makes a section of its heading alone, and the sections are
   read together. A document walker-1 cannot read, one that is not HTML, and one with
   no such heading state nothing.
2. *Stated dates.* A full date after "ended" or "ending": a month's name or its
   abbreviation, the day, a comma, and the year. An announcement date or a signature
   date states no period (P7-7).
3. *Stated fiscal periods*, read quarters first, so that a year inside a quarter's
   phrase is not read again as a full year:
   - an ordinal quarter with its year: "third quarter of 2024", "third-quarter 2024",
     "second fiscal quarter of 2025", "first quarter of fiscal 2026", and the
     year-first "fiscal 2025 second quarter";
   - a ``Q`` quarter: "Q3 2024", "Q2 fiscal 2025", and "3Q 2024";
   - a full year: "fiscal 2025", "fiscal year 2025", "full year 2024", and
     "full-year 2024".
4. *Preliminary.* "preliminary", or "expected" with "results" among the next three
   words.

**Resolution.** A stated date matches when it equals P. A fiscal period is judged only
when the slot has labels whose ``fp`` is ``Q1``, ``Q2``, ``Q3``, or ``FY``. It then
matches when it names that quarter, or for ``FY`` the fourth quarter or the full year,
of the year ``fy``. The rule drops each candidate whose judged statements all fail to
match, and each that calls its results preliminary. If one candidate is left, it is
the release filing: ``stated_period`` if it has a matching statement, and otherwise
``sole_candidate``. None left is ``ambiguous`` with ``no_release_filing``, and several
are ``ambiguous`` with ``several_release_filings``.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from earnings_ingestion.cohort.locators import CitableArtifact, LocatorError
from earnings_ingestion.cohort.records import Citation
from earnings_ingestion.events.filings import RESULTS_ITEM, Placed
from earnings_ingestion.events.records import EventReason, IdentificationMethod
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import Slot
from earnings_ingestion.sec.companyfacts import FiscalLabels
from earnings_ingestion.sec.urls import archive_url

RELEASE_POLICY = "release-id/1"

_HEADING = re.compile(
    r"^[^\S\n]*item[^\S\n]+(\d+\.\d+)\b", re.IGNORECASE | re.MULTILINE
)
_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan.": 1,
    "feb.": 2,
    "mar.": 3,
    "apr.": 4,
    "jun.": 6,
    "jul.": 7,
    "aug.": 8,
    "sep.": 9,
    "sept.": 9,
    "oct.": 10,
    "nov.": 11,
    "dec.": 12,
}
_MONTH = "|".join(re.escape(name) for name in sorted(_MONTHS, key=len, reverse=True))
_DATE = re.compile(
    rf"\b(?:ended|ending)\s+(?P<month>{_MONTH})\s+(?P<day>\d{{1,2}}),\s+(?P<year>\d{{4}})\b",
    re.IGNORECASE,
)
_ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4}
_ORDINAL = r"(?P<ordinal>first|second|third|fourth)"
_FISCAL = r"(?:fiscal\s+(?:year\s+)?)"
_QUARTERS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        rf"\b{_ORDINAL}[\s-]+(?:fiscal\s+)?quarter(?:\s+of)?\s+{_FISCAL}?(?P<year>\d{{4}})\b",
        rf"\b{_FISCAL}(?P<year>\d{{4}})\s+{_ORDINAL}[\s-]+quarter\b",
        rf"\bQ(?P<number>[1-4])\s+{_FISCAL}?(?P<year>\d{{4}})\b",
        r"\b(?P<number>[1-4])Q\s+(?P<year>\d{4})\b",
    )
)
_YEARS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        rf"\b{_FISCAL}(?P<year>\d{{4}})\b",
        r"\bfull[\s-]year\s+(?P<year>\d{4})\b",
    )
)
_PRELIMINARY = re.compile(
    r"\bpreliminary\b|\bexpected(?:\s+[\w-]+){0,2}\s+results\b", re.IGNORECASE
)
_JUDGED = frozenset({"Q1", "Q2", "Q3", "FY"})


@dataclass(frozen=True, order=True)
class FiscalPeriod:
    """A fiscal period a text names: ``Q1`` to ``Q4``, or ``FY`` for a full year."""

    year: int
    period: str

    def __str__(self) -> str:
        return f"{self.period} {self.year}"


@dataclass(frozen=True)
class Reading:
    """What ``release-id/1`` reads in one primary document."""

    sections: tuple[tuple[int, int], ...] = ()
    """The Item 2.02 sections, as ``[start, end)`` offsets into walker-1's text."""
    dates: tuple[date, ...] = ()
    periods: tuple[FiscalPeriod, ...] = ()
    preliminary: bool = False
    unread: str | None = None
    """Why no Item 2.02 text was read, when none was."""


def _periods(section: str) -> set[FiscalPeriod]:
    found: set[FiscalPeriod] = set()
    taken: list[tuple[int, int]] = []
    for pattern in (*_QUARTERS, *_YEARS):
        for match in pattern.finditer(section):
            if any(start < match.end() and match.start() < end for start, end in taken):
                continue
            taken.append(match.span())
            groups = match.groupdict()
            if groups.get("ordinal"):
                period = f"Q{_ORDINALS[groups['ordinal'].lower()]}"
            elif groups.get("number"):
                period = f"Q{groups['number']}"
            else:
                period = "FY"
            found.add(FiscalPeriod(int(groups["year"]), period))
    return found


def _dates(section: str) -> set[date]:
    found = set()
    for match in _DATE.finditer(section):
        month = _MONTHS[match["month"].lower()]
        try:
            found.add(date(int(match["year"]), month, int(match["day"])))
        except ValueError:
            continue
    return found


def read_text(text: str) -> Reading:
    """Read walker-1's text of a primary document."""
    headings = list(_HEADING.finditer(text))
    sections = []
    for heading, following in zip(headings, [*headings[1:], None], strict=True):
        if heading.group(1) != RESULTS_ITEM:
            continue
        end = len(text) if following is None else following.start()
        body = text[heading.start() : end].rstrip()
        sections.append((heading.start(), heading.start() + len(body)))
    if not sections:
        return Reading(unread="it has no Item 2.02 heading")
    dates: set[date] = set()
    periods: set[FiscalPeriod] = set()
    preliminary = False
    for start, end in sections:
        section = text[start:end]
        dates |= _dates(section)
        periods |= _periods(section)
        preliminary = preliminary or _PRELIMINARY.search(section) is not None
    return Reading(
        sections=tuple(sections),
        dates=tuple(sorted(dates)),
        periods=tuple(sorted(periods)),
        preliminary=preliminary,
    )


def read_document(document: CitableArtifact) -> Reading:
    """Read a saved primary document in walker-1's text."""
    if document.text.media_type != "text/html":
        return Reading(unread=f"it is {document.text.media_type}, not HTML")
    try:
        text, _ = document.text.canonical
    except LocatorError as exc:
        return Reading(unread=str(exc))
    return read_text(text)


def _matches(period: FiscalPeriod, labels: FiscalLabels | None) -> bool | None:
    """Whether a fiscal period matches the slot's labels; ``None`` when unjudged."""
    if labels is None or labels.fiscal_period not in _JUDGED:
        return None
    wanted = {"Q4", "FY"} if labels.fiscal_period == "FY" else {labels.fiscal_period}
    return period.year == labels.fiscal_year and period.period in wanted


@dataclass(frozen=True)
class Candidate:
    """One candidate, as the rule reads and judges it for its slot."""

    placed: Placed
    document: CitableArtifact | None
    reading: Reading
    judged: bool
    """It states a date, or a fiscal period its slot's labels judge."""
    matched: bool
    """One of its statements matches the slot."""

    @property
    def dropped(self) -> str | None:
        """Why the rule drops it; ``None`` when it stays."""
        if self.judged and not self.matched:
            return "it states another period"
        if self.reading.preliminary:
            return "it calls its results preliminary"
        return None

    def item_text(self) -> Citation | None:
        """Its Item 2.02 sections, cited in its primary document's walker-1 text."""
        if self.document is None or not self.reading.sections:
            return None
        return self.document.cite(
            *(
                self.document.text.span(start, end)
                for start, end in self.reading.sections
            )
        )


@dataclass(frozen=True)
class Identification:
    """A slot's candidates, amendments, and release filing under ``release-id/1``."""

    candidates: tuple[Candidate, ...]
    amendments: tuple[Placed, ...]
    passed_over: tuple[tuple[Placed, str], ...]
    """The other Item 2.02 8-Ks in the range, and why each is not a candidate, which
    the build's report prints for review (P7-15)."""
    release: Candidate | None
    method: IdentificationMethod | None
    reason: EventReason | None
    """``no_release_filing`` or ``several_release_filings`` when no release filing is
    identified."""
    problems: tuple[str, ...]


def _passed_over(placed: Placed) -> str | None:
    if RESULTS_ITEM not in placed.index.items:
        return "its index page lists no Item 2.02"
    if not placed.index.exhibits_99():
        return "its index page lists no exhibit typed EX-99*"
    return None


def identify(
    slot: Slot, releases: Sequence[Placed], saved: SavedResponses, *, cutoff: date
) -> Identification:
    """Apply ``release-id/1`` to one slot. ``releases`` are its issuer's placed
    Item 2.02 8-Ks and 8-K/As (``IssuerFilings.releases``)."""
    last = slot.next_period_end or cutoff
    in_range = sorted(
        (p for p in releases if slot.period_end < p.accepted_on <= last),
        key=lambda p: (p.instant, p.filing.accession),
    )
    candidates, amendments, passed_over, problems = [], [], [], []
    for placed in in_range:
        if placed.filing.form != "8-K":
            amendments.append(placed)
            continue
        if why := _passed_over(placed):
            passed_over.append((placed, why))
            continue
        filing = placed.filing
        url = archive_url(slot.cik, filing.accession, filing.primary_document)
        try:
            document = saved.get(url)
        except (FileNotFoundError, ValueError) as exc:
            problems.append(f"{url}: {exc}")
            document = None
        if document is None:
            if not problems or not problems[-1].startswith(url):
                problems.append(f"nothing saved from {url}: run events discover")
            reading = Reading(unread="nothing saved")
        else:
            reading = read_document(document)
        judged = bool(reading.dates) or any(
            _matches(period, slot.labels) is not None for period in reading.periods
        )
        matched = slot.period_end in reading.dates or any(
            _matches(period, slot.labels) for period in reading.periods
        )
        candidates.append(Candidate(placed, document, reading, judged, matched))
    kept = [candidate for candidate in candidates if candidate.dropped is None]
    release = kept[0] if len(kept) == 1 else None
    if release is not None:
        method = (
            IdentificationMethod.STATED_PERIOD
            if release.matched
            else IdentificationMethod.SOLE_CANDIDATE
        )
        reason = None
    else:
        method = None
        reason = (
            EventReason.SEVERAL_RELEASE_FILINGS
            if kept
            else EventReason.NO_RELEASE_FILING
        )
    return Identification(
        candidates=tuple(candidates),
        amendments=tuple(amendments),
        passed_over=tuple(passed_over),
        release=release,
        method=method,
        reason=reason,
        problems=tuple(problems),
    )
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/release.py`.

Create `/tmp/plan7-task9-synthetic.py`:

```python
"""Plan 7: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py": [
        (
            "\n"
            "The builders write submissions files, older pages, and index pages in SEC's formats,\n"
            "as Stage 5's readers read them, for invented registrants. Tests build their cases\n"
            "with them, and the synthetic event layer writes its committed fixture through them.\n",
            "\n"
            "The builders write submissions files, older pages, companyfacts files, index pages,\n"
            "and 8-K primary documents in SEC's formats, as Stage 5's readers read them, for\n"
            "invented registrants. Tests build their cases\n"
            "with them, and the synthetic event layer writes its committed fixture through them.\n",
        ),
        (
            "from datetime import date, datetime\n"
            "from pathlib import Path\n",
            "from datetime import date, datetime\n"
            "from html import escape\n"
            "from pathlib import Path\n",
        ),
        (
            "from earnings_ingestion.sec.urls import (\n"
            "    companyfacts_url,\n",
            "from earnings_ingestion.sec.urls import (\n"
            "    archive_url,\n"
            "    companyfacts_url,\n",
        ),
        (
            "\n"
            "def save(\n",
            "\n"
            "def eight_k(\n"
            "    registrant: str,\n"
            "    items: Sequence[tuple[str, Sequence[str]]],\n"
            "    *,\n"
            "    cover: bool = False,\n"
            "    signed: date | None = None,\n"
            ") -> bytes:\n"
            "    \"\"\"An 8-K's primary document: the registrant, then each ``(item, paragraphs)`` as\n"
            "    a heading and its paragraphs, then a signature dated ``signed``. ``cover`` also\n"
            "    lists the items in a table on the cover page, as some registrants do, which gives\n"
            "    each item a heading with nothing under it.\"\"\"\n"
            "    parts = [\"<p>Form 8-K</p><p>Current Report</p>\", f\"<p>{escape(registrant)}</p>\"]\n"
            "    if cover:\n"
            "        rows = \"\".join(\n"
            "            f\"<tr><td></td><td>Item {item}</td><td>{ITEM_TITLES[item]}</td></tr>\"\n"
            "            for item, _ in items\n"
            "        )\n"
            "        parts.append(f\"<table>{rows}</table>\")\n"
            "    for item, paragraphs in items:\n"
            "        parts.append(f\"<p><b>Item {item} {ITEM_TITLES[item]}</b></p>\")\n"
            "        parts.extend(f\"<p>{escape(paragraph)}</p>\" for paragraph in paragraphs)\n"
            "    parts.append(f\"<p>Signature</p><p>{escape(registrant)}</p>\")\n"
            "    if signed is not None:\n"
            "        parts.append(f\"<p>Date: {signed:%B} {signed.day}, {signed.year}</p>\")\n"
            "    return (\n"
            "        \"<!DOCTYPE html><html><head><title>Form 8-K</title></head><body>\"\n"
            "        f\"{''.join(parts)}</body></html>\\n\"\n"
            "    ).encode()\n"
            "\n"
            "\n"
            "def save(\n",
        ),
        (
            "        self.put(companyfacts_url(cik), companyfacts_file(cik, name, facts), JSON)\n",
            "        self.put(companyfacts_url(cik), companyfacts_file(cik, name, facts), JSON)\n"
            "\n"
            "    def document(\n"
            "        self,\n"
            "        cik: str,\n"
            "        filing: SyntheticFiling,\n"
            "        body: bytes,\n"
            "        media_type: str = HTML,\n"
            "    ) -> None:\n"
            "        \"\"\"Save ``body`` as the filing's primary document.\"\"\"\n"
            "        url = archive_url(cik, filing.accession, filing.primary_document)\n"
            "        self.put(url, body, media_type)\n",
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

Apply `task9-synthetic`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_release.py -q`

Expected: `55 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py packages/earnings-ingestion/tests/test_events_release.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1125 passed, 24 deselected`; `All checks passed!` and
`232 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/release.py packages/earnings-ingestion/src/earnings_ingestion/events/synthetic.py packages/earnings-ingestion/tests/test_events_release.py
git commit -m "feat(events): identify each slot's release filing with release-id/1"
```

---

### Task 10: `eligibility/1`, each event's status and reason

This task implements S §Eligibility (step 3) and EV13. Every event is judged against
the frozen cohort, at the instant its release filing was accepted.

- **Bounds.** `side(day, timing, instant)` places a release against a bound by the
  bound-rule table.
  - Its Eastern date and wall time decide, so daylight saving is handled.
  - 09:30 is the regular open, and 13:00 is NYSE's earliest scheduled close, so no
    trading calendar is needed.
  - An `anchor_snapshot` start is a lower bound: every release on or after its date
    is inside.
- **Membership.** `memberships(manifest)` gathers each issuer's intervals across its
  securities. Each interval's assertions are split between its start (`member_at`,
  `added`) and its end (`removed`), by the manifest's own assertions.
  - `standing(membership, instant)` gives member, not a member, or unordered, in
    three-valued logic over the intervals.
  - `MembershipInterval.contains` is not used, since it ignores timing.
- **Checks.** `decide(...)` runs S's four checks in order, and the first that applies
  decides. Checks 1 and 3 are defensive, since slots lie in the window and
  candidates precede the cutoff by construction, and the tests exercise both.
- **The deciding assertion (P7-11).** `membership_assertion_id` is null when check 1,
  2, or 3 decided. Otherwise it follows S's three rules. One case S leaves open: of
  several intervals holding T, which happens once an issuer's second security joins,
  the interval that opened first decides. It is the membership that held longest,
  and it stays true if the later addition is ever corrected.
- **The tests** read Stage 4's committed synthetic cohort, whose Borealis and Corvid
  change before the open on 2024-11-08. They place releases just before and just
  after each timing's bound, in winter and in summer, and give every reason in S's
  table a case.

At plan time, `memberships` read the frozen v1 cohort. It gave 33 issuers, each with
one interval. At 2024-11-08 07:00 Eastern, Intel and Dow come out unordered as they
leave, and Sherwin-Williams and Nvidia come out unordered as they join. At
2026-06-29 08:00, Verizon and Alphabet do the same, leaving and joining.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/eligibility.py`.
- Test (create): `packages/earnings-ingestion/tests/test_events_eligibility.py`.

**Interfaces:**

- Consumes:
  - Stage 4's `UniverseManifest`, `MembershipInterval`, `AssertedAction`,
    `BoundBasis`, `BoundTiming`, and `cohort.freeze.load_manifest`;
  - Task 5's `EASTERN` and `accepted_instant`;
  - Task 6's `EventReason`, `EventStatus`, `STATUS_OF`, and `UNIDENTIFIED`.
- Produces `events/eligibility.py`:
  - `ELIGIBILITY_POLICY = "eligibility/1"`, `REGULAR_OPEN = time(9, 30)`, and
    `EARLIEST_CLOSE = time(13, 0)`;
  - `Side` (`before`, `after`, `unordered`) and
    `side(day, timing, instant) -> Side`;
  - `Bound(day, timing, assertion_ids)` and `Span(security_id, start, anchor, end)`,
    with `holds(instant) -> bool | None`;
  - `span(interval, actions) -> Span`;
  - `IssuerMembership(issuer_id, spans)` and
    `memberships(manifest) -> dict[str, IssuerMembership]`;
  - `Standing` (`member`, `not_member`, `unordered`) and
    `standing(membership, instant) -> tuple[Standing, str]`;
  - `Decision(status, reason, membership_assertion_id)` and
    `decide(period_end, published, unidentified, membership, *, start, stop, cutoff) -> Decision`.
    Here `published` is the release's UTC acceptance instant, or `None`, and
    `unidentified` is `release-id/1`'s reason when there is no release. Task 12's
    build calls `decide` for each slot, and again after a `set_release_filing`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_eligibility.py`:

```python
"""eligibility/1: each event's status, reason, and deciding assertion (the Stage 5
spec, §Eligibility; plan 7, P7-11).

The membership cases read Stage 4's committed synthetic cohort: Borealis leaves and
Corvid joins before the open on 2024-11-08, Dynamo holds two securities, and
Eastfield leaves before the open on 2026-06-22.
"""

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.records import BoundTiming
from earnings_ingestion.events.acceptance import accepted_instant
from earnings_ingestion.events.eligibility import (
    ELIGIBILITY_POLICY,
    Bound,
    IssuerMembership,
    Side,
    Span,
    Standing,
    decide,
    memberships,
    side,
    standing,
)
from earnings_ingestion.events.records import EventReason, EventStatus

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "tests" / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
START, STOP, CUTOFF = date(2024, 7, 1), date(2026, 7, 1), date(2026, 9, 22)


@pytest.fixture(scope="module")
def issuers() -> dict[str, IssuerMembership]:
    return memberships(load_manifest(COHORT))


def eastern(wall: str) -> datetime:
    """The UTC instant of an Eastern wall time."""
    return accepted_instant(wall)


def test_the_policy_is_named() -> None:
    assert ELIGIBILITY_POLICY == "eligibility/1"


@pytest.mark.parametrize(
    ("timing", "wall", "expected"),
    [
        (BoundTiming.BEFORE_OPEN, "2024-11-07 23:59:59", Side.BEFORE),
        (BoundTiming.BEFORE_OPEN, "2024-11-08 00:00:00", Side.UNORDERED),
        (BoundTiming.BEFORE_OPEN, "2024-11-08 09:29:59", Side.UNORDERED),
        (BoundTiming.BEFORE_OPEN, "2024-11-08 09:30:00", Side.AFTER),
        (BoundTiming.BEFORE_OPEN, "2024-11-09 00:00:00", Side.AFTER),
        (BoundTiming.AFTER_CLOSE, "2024-11-07 16:05:00", Side.BEFORE),
        (BoundTiming.AFTER_CLOSE, "2024-11-08 12:59:59", Side.BEFORE),
        (BoundTiming.AFTER_CLOSE, "2024-11-08 13:00:00", Side.UNORDERED),
        (BoundTiming.AFTER_CLOSE, "2024-11-08 23:59:59", Side.UNORDERED),
        (BoundTiming.AFTER_CLOSE, "2024-11-09 06:00:00", Side.AFTER),
        (BoundTiming.UNSPECIFIED, "2024-11-07 23:59:59", Side.BEFORE),
        (BoundTiming.UNSPECIFIED, "2024-11-08 09:30:00", Side.UNORDERED),
        (BoundTiming.UNSPECIFIED, "2024-11-09 00:00:00", Side.AFTER),
    ],
)
def test_the_bound_rules_in_winter(timing, wall, expected) -> None:
    """2024-11-08 is in Eastern Standard Time."""
    assert side(date(2024, 11, 8), timing, eastern(wall)) is expected


@pytest.mark.parametrize(
    ("timing", "wall", "expected"),
    [
        (BoundTiming.BEFORE_OPEN, "2026-06-22 09:29:59", Side.UNORDERED),
        (BoundTiming.BEFORE_OPEN, "2026-06-22 09:30:00", Side.AFTER),
        (BoundTiming.AFTER_CLOSE, "2026-06-22 12:59:59", Side.BEFORE),
        (BoundTiming.AFTER_CLOSE, "2026-06-22 13:00:00", Side.UNORDERED),
    ],
)
def test_the_bound_rules_in_summer(timing, wall, expected) -> None:
    """2026-06-22 is in Eastern Daylight Time: 09:30 there is 13:30 UTC."""
    instant = eastern(wall)
    assert side(date(2026, 6, 22), timing, instant) is expected
    assert side(date(2026, 6, 22), timing, instant.astimezone(UTC)) is expected


def test_a_naive_instant_is_refused() -> None:
    with pytest.raises(ValueError, match="carries its offset"):
        naive = datetime(2024, 11, 8, 12, tzinfo=UTC).replace(tzinfo=None)
        side(date(2024, 11, 8), BoundTiming.UNSPECIFIED, naive)


@pytest.mark.parametrize(
    ("issuer", "wall", "expected", "assertion"),
    [
        (
            "cik-0009990003",
            "2024-11-07 16:05:00",
            Standing.NOT_MEMBER,
            "index-2024-11-01:corvid-common:added",
        ),
        (
            "cik-0009990003",
            "2024-11-08 07:00:00",
            Standing.UNORDERED,
            "index-2024-11-01:corvid-common:added",
        ),
        (
            "cik-0009990003",
            "2024-11-08 09:30:00",
            Standing.MEMBER,
            "index-2024-11-01:corvid-common:added",
        ),
        (
            "cik-0009990002",
            "2024-10-24 16:05:00",
            Standing.MEMBER,
            "roster-2024-06-28:borealis-common:member_at",
        ),
        (
            "cik-0009990002",
            "2024-11-08 07:00:00",
            Standing.UNORDERED,
            "index-2024-11-01:borealis-common:removed",
        ),
        (
            "cik-0009990002",
            "2024-11-08 09:30:00",
            Standing.NOT_MEMBER,
            "index-2024-11-01:borealis-common:removed",
        ),
        (
            "cik-0009990001",
            "2024-07-25 16:05:00",
            Standing.MEMBER,
            "roster-2024-06-28:acme-common:member_at",
        ),
        (
            "cik-0009990001",
            "2024-06-28 07:00:00",
            Standing.MEMBER,
            "roster-2024-06-28:acme-common:member_at",
        ),
        (
            "cik-0009990005",
            "2026-07-23 16:05:00",
            Standing.MEMBER,
            "roster-2024-06-28:dynamo-class-a:member_at",
        ),
        (
            "cik-0009990005",
            "2026-06-22 07:00:00",
            Standing.MEMBER,
            "roster-2024-06-28:dynamo-class-a:member_at",
        ),
        (
            "cik-0009990006",
            "2026-07-30 16:05:00",
            Standing.NOT_MEMBER,
            "index-2026-06-16:eastfield-common:removed",
        ),
    ],
    ids=[
        "corvid-day-before",
        "corvid-pre-market",
        "corvid-at-open",
        "borealis-member",
        "borealis-pre-market",
        "borealis-at-open",
        "acme-anchor",
        "acme-on-the-anchor-date",
        "dynamo-first-opened",
        "dynamo-one-security-holds",
        "eastfield-removed",
    ],
)
def test_membership_at_publication_and_its_assertion(
    issuers, issuer, wall, expected, assertion
) -> None:
    """An anchor's start is a lower bound, whatever the time on its date. Dynamo is a
    member while one security's interval holds T, though another's start is
    unordered; of two intervals holding T, the one that opened first decides."""
    assert standing(issuers[issuer], eastern(wall)) == (expected, assertion)


def gap(removed: date, added: date) -> IssuerMembership:
    """An invented issuer whose security leaves on ``removed`` and returns on
    ``added``, each before the open."""
    first = Span(
        security_id="gamma-common",
        start=Bound(date(2024, 6, 28), BoundTiming.UNSPECIFIED, ("a-member_at",)),
        anchor=True,
        end=Bound(removed, BoundTiming.BEFORE_OPEN, ("b-removed",)),
    )
    second = Span(
        security_id="gamma-common",
        start=Bound(added, BoundTiming.BEFORE_OPEN, ("c-added",)),
        anchor=False,
        end=None,
    )
    return IssuerMembership("cik-0009990007", (first, second))


@pytest.mark.parametrize(
    ("wall", "assertion"),
    [
        ("2025-03-10 16:05:00", "b-removed"),
        ("2025-03-12 16:05:00", "b-removed"),
        ("2025-03-14 16:05:00", "c-added"),
    ],
    ids=["nearer-removal", "tie", "nearer-addition"],
)
def test_a_non_member_cites_the_nearer_change_and_a_tie_goes_to_the_removal(
    wall, assertion
) -> None:
    membership = gap(date(2025, 3, 3), date(2025, 3, 21))
    assert standing(membership, eastern(wall)) == (Standing.NOT_MEMBER, assertion)


def decision(
    issuers, period_end, published, unidentified=None, issuer="cik-0009990002"
):
    return decide(
        period_end,
        published,
        unidentified,
        issuers[issuer],
        start=START,
        stop=STOP,
        cutoff=CUTOFF,
    )


@pytest.mark.parametrize(
    ("period_end", "wall", "unidentified", "status", "reason", "assertion"),
    [
        (
            date(2024, 6, 30),
            "2024-07-25 16:05:00",
            None,
            EventStatus.INELIGIBLE,
            EventReason.PERIOD_END_OUTSIDE_WINDOW,
            None,
        ),
        (
            date(2026, 7, 1),
            None,
            EventReason.NO_RELEASE_FILING,
            EventStatus.INELIGIBLE,
            EventReason.PERIOD_END_OUTSIDE_WINDOW,
            None,
        ),
        (
            date(2024, 9, 30),
            None,
            EventReason.NO_RELEASE_FILING,
            EventStatus.AMBIGUOUS,
            EventReason.NO_RELEASE_FILING,
            None,
        ),
        (
            date(2024, 9, 30),
            None,
            EventReason.SEVERAL_RELEASE_FILINGS,
            EventStatus.AMBIGUOUS,
            EventReason.SEVERAL_RELEASE_FILINGS,
            None,
        ),
        (
            date(2026, 6, 30),
            "2026-09-23 00:30:00",
            None,
            EventStatus.INELIGIBLE,
            EventReason.PUBLISHED_AFTER_CUTOFF,
            None,
        ),
        (
            date(2024, 9, 30),
            "2024-10-24 16:05:00",
            None,
            EventStatus.ELIGIBLE,
            EventReason.MEMBER_AT_PUBLICATION,
            "roster-2024-06-28:borealis-common:member_at",
        ),
        (
            date(2024, 12, 31),
            "2025-01-28 16:05:00",
            None,
            EventStatus.INELIGIBLE,
            EventReason.NOT_MEMBER_AT_PUBLICATION,
            "index-2024-11-01:borealis-common:removed",
        ),
        (
            date(2024, 9, 30),
            "2024-11-08 07:00:00",
            None,
            EventStatus.AMBIGUOUS,
            EventReason.SAME_DAY_TRANSITION,
            "index-2024-11-01:borealis-common:removed",
        ),
    ],
    ids=[
        "window-before",
        "window-stop",
        "no-release",
        "several",
        "after-cutoff",
        "member",
        "not-member",
        "same-day",
    ],
)
def test_every_reason_and_the_checks_order(
    issuers, period_end, wall, unidentified, status, reason, assertion
) -> None:
    """The first check that applies decides, and only check 4 names an assertion."""
    published = None if wall is None else eastern(wall)
    found = decision(issuers, period_end, published, unidentified)
    assert (found.status, found.reason) == (status, reason)
    assert found.membership_assertion_id == assertion


def test_the_cutoff_is_judged_on_the_eastern_calendar(issuers) -> None:
    """21:30 Eastern on the cutoff is 01:30 UTC the next day, and is not after it."""
    late = datetime(2026, 9, 23, 1, 30, tzinfo=UTC)
    found = decision(issuers, date(2026, 6, 30), late, issuer="cik-0009990001")
    assert found.reason is EventReason.MEMBER_AT_PUBLICATION


def test_an_event_without_a_release_needs_its_identification_reason(issuers) -> None:
    with pytest.raises(ValueError, match="no_release_filing or several"):
        decision(issuers, date(2024, 9, 30), None, None)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_eligibility.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_eligibility.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.eligibility'`.

- [x] **Step 3: Write eligibility**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/eligibility.py`:

```python
"""``eligibility/1``: each event's status, its reason, and the assertion that decided
it (the Stage 5 spec, §Eligibility, step 3; plan 7, P7-11).

**Membership at an instant T**, the release filing's acceptance:

- An interval holds T when T is on or after its start and before its end, each judged
  by the bound rules. An ``anchor_snapshot`` start is a lower bound: every release on
  or after its date is inside.
- The issuer is a member when any of its securities' intervals holds T. It is not a
  member when none holds T and none is unordered at T. Otherwise its membership is
  unordered. ``MembershipInterval.contains`` is not used, since it ignores timing.

**The bound rules.** A release on Eastern date d at time t falls before a bound on
Eastern date D when d < D, and after it when d > D. When d = D, a ``before_open``
bound puts it after if t is 09:30 or later, the regular open; an ``after_close`` bound
puts it before if t is before 13:00, NYSE's earliest scheduled close; any other case
is unordered. So no trading calendar is needed (EV13).

**The checks** run in order, and the first that applies decides:

1. a period end outside ``[start, stop)`` is ``period_end_outside_window``;
2. an event with no release filing keeps its identification's reason,
   ``no_release_filing`` or ``several_release_filings``;
3. a publication whose Eastern date is after the cutoff is ``published_after_cutoff``;
4. membership at T gives ``member_at_publication``, ``not_member_at_publication``, or
   ``same_day_transition``.

**``membership_assertion_id``** names the assertion that decided check 4, and is
``None`` when check 1, 2, or 3 decided (P7-11):

- for a member, the assertion that opens an interval holding T. Of several such
  intervals, the one that opened first decides, and of several assertions, the
  smallest ID (P7-11);
- for a non-member, the nearer in days of the ``removed`` assertion closing the last
  interval before T and the ``added`` assertion opening the first interval after T.
  A tie goes to the removal;
- for an unordered case, the assertion of the unordered bound, the smallest ID if
  there are several.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum

from earnings_ingestion.cohort.records import (
    AssertedAction,
    BoundBasis,
    BoundTiming,
    MembershipInterval,
    UniverseManifest,
)
from earnings_ingestion.events.acceptance import EASTERN
from earnings_ingestion.events.records import (
    STATUS_OF,
    UNIDENTIFIED,
    EventReason,
    EventStatus,
)

ELIGIBILITY_POLICY = "eligibility/1"
REGULAR_OPEN = time(9, 30)
EARLIEST_CLOSE = time(13, 0)


class Side(StrEnum):
    """Where a release falls against a bound."""

    BEFORE = "before"
    AFTER = "after"
    UNORDERED = "unordered"


def side(day: date, timing: BoundTiming, instant: datetime) -> Side:
    """The side of a bound on Eastern date ``day``, with ``timing``, on which a
    release accepted at ``instant`` falls."""
    if instant.utcoffset() is None:
        raise ValueError("an acceptance instant carries its offset")
    local = instant.astimezone(EASTERN)
    if local.date() != day:
        return Side.BEFORE if local.date() < day else Side.AFTER
    if timing is BoundTiming.BEFORE_OPEN and local.time() >= REGULAR_OPEN:
        return Side.AFTER
    if timing is BoundTiming.AFTER_CLOSE and local.time() < EARLIEST_CLOSE:
        return Side.BEFORE
    return Side.UNORDERED


@dataclass(frozen=True)
class Bound:
    day: date
    timing: BoundTiming
    assertion_ids: tuple[str, ...]
    """The assertions that set the bound, smallest first."""


@dataclass(frozen=True)
class Span:
    """One interval of one of the issuer's securities."""

    security_id: str
    start: Bound
    anchor: bool
    """The start is an ``anchor_snapshot``: a lower bound."""
    end: Bound | None

    def start_side(self, instant: datetime) -> Side:
        if self.anchor:
            local = instant.astimezone(EASTERN).date()
            return Side.AFTER if local >= self.start.day else Side.BEFORE
        return side(self.start.day, self.start.timing, instant)

    def holds(self, instant: datetime) -> bool | None:
        """Whether the interval holds ``instant``; ``None`` when that is unordered."""
        started = {Side.AFTER: True, Side.BEFORE: False}.get(self.start_side(instant))
        if self.end is None:
            ended = False
        else:
            where = side(self.end.day, self.end.timing, instant)
            ended = {Side.AFTER: True, Side.BEFORE: False}.get(where)
        if started is False or ended is True:
            return False
        if started is True and ended is False:
            return True
        return None


def span(interval: MembershipInterval, actions: dict[str, AssertedAction]) -> Span:
    """An interval, with its assertions split into its start's and its end's."""
    closing = {
        i for i in interval.assertion_ids if actions[i] is AssertedAction.REMOVED
    }
    opening = tuple(sorted(set(interval.assertion_ids) - closing))
    end = None
    if interval.effective_to is not None:
        end = Bound(
            interval.effective_to, interval.effective_to_timing, tuple(sorted(closing))
        )
    return Span(
        security_id=interval.security_id,
        start=Bound(interval.effective_from, interval.effective_from_timing, opening),
        anchor=interval.effective_from_basis is BoundBasis.ANCHOR_SNAPSHOT,
        end=end,
    )


@dataclass(frozen=True)
class IssuerMembership:
    """Every interval of one issuer's securities."""

    issuer_id: str
    spans: tuple[Span, ...]


def memberships(manifest: UniverseManifest) -> dict[str, IssuerMembership]:
    """Each issuer's intervals, keyed by ``issuer_id``."""
    actions = {
        a.membership_assertion_id: a.asserted_action for a in manifest.assertions
    }
    found = {}
    for issuer in manifest.issuers:
        spans = tuple(
            span(interval, actions)
            for interval in sorted(
                manifest.intervals, key=lambda i: (i.security_id, i.effective_from)
            )
            if interval.security_id in issuer.security_ids
        )
        found[issuer.issuer_id] = IssuerMembership(issuer.issuer_id, spans)
    return found


class Standing(StrEnum):
    MEMBER = "member"
    NOT_MEMBER = "not_member"
    UNORDERED = "unordered"


def standing(membership: IssuerMembership, instant: datetime) -> tuple[Standing, str]:
    """The issuer's membership at ``instant``, and the assertion that decides it."""
    spans = membership.spans
    if not spans:
        raise ValueError(f"{membership.issuer_id} has no membership interval")
    held = [(each, each.holds(instant)) for each in spans]
    members = [each for each, holds in held if holds is True]
    if members:
        first = min(members, key=lambda s: (s.start.day, s.start.assertion_ids[0]))
        return Standing.MEMBER, first.start.assertion_ids[0]
    unordered = []
    for each, holds in held:
        if holds is not None:
            continue
        if each.start_side(instant) is Side.UNORDERED:
            unordered.extend(each.start.assertion_ids)
        if each.end is not None and (
            side(each.end.day, each.end.timing, instant) is Side.UNORDERED
        ):
            unordered.extend(each.end.assertion_ids)
    if unordered:
        return Standing.UNORDERED, min(unordered)
    day = instant.astimezone(EASTERN).date()
    ended = [
        each
        for each in spans
        if each.end is not None
        and side(each.end.day, each.end.timing, instant) is Side.AFTER
    ]
    later = [each for each in spans if each not in ended]
    nearest = []
    if ended:
        last = max(each.end.day for each in ended)
        ids = [
            i for each in ended if each.end.day == last for i in each.end.assertion_ids
        ]
        nearest.append(((day - last).days, 0, min(ids)))
    if later:
        first = min(each.start.day for each in later)
        ids = [
            i
            for each in later
            if each.start.day == first
            for i in each.start.assertion_ids
        ]
        nearest.append(((first - day).days, 1, min(ids)))
    return Standing.NOT_MEMBER, min(nearest)[2]


@dataclass(frozen=True)
class Decision:
    status: EventStatus
    reason: EventReason
    membership_assertion_id: str | None


_BY_STANDING = {
    Standing.MEMBER: EventReason.MEMBER_AT_PUBLICATION,
    Standing.NOT_MEMBER: EventReason.NOT_MEMBER_AT_PUBLICATION,
    Standing.UNORDERED: EventReason.SAME_DAY_TRANSITION,
}


def _by(reason: EventReason, assertion_id: str | None = None) -> Decision:
    return Decision(STATUS_OF[reason], reason, assertion_id)


def decide(
    period_end: date,
    published: datetime | None,
    unidentified: EventReason | None,
    membership: IssuerMembership,
    *,
    start: date,
    stop: date,
    cutoff: date,
) -> Decision:
    """Run the checks in order. ``published`` is the release filing's acceptance,
    and ``unidentified`` the identification's reason when there is no release."""
    if not start <= period_end < stop:
        return _by(EventReason.PERIOD_END_OUTSIDE_WINDOW)
    if published is None:
        if unidentified not in UNIDENTIFIED:
            raise ValueError(
                "an event with no release filing is no_release_filing or"
                " several_release_filings"
            )
        return _by(unidentified)
    if published.utcoffset() is None:
        raise ValueError("an acceptance instant carries its offset")
    if published.astimezone(EASTERN).date() > cutoff:
        return _by(EventReason.PUBLISHED_AFTER_CUTOFF)
    state, assertion_id = standing(membership, published)
    return _by(_BY_STANDING[state], assertion_id)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/eligibility.py`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_eligibility.py -q`

Expected: `43 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py packages/earnings-ingestion/tests/test_events_eligibility.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1168 passed, 24 deselected`; `All checks passed!` and
`234 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/eligibility.py packages/earnings-ingestion/tests/test_events_eligibility.py
git commit -m "feat(events): decide each event's eligibility with eligibility/1"
```

---

### Task 11: The synthetic event layer's saved responses

This task implements S §The synthetic event layer, and the cases of S §Verification
(plan A), items 4, 6, and 7, that need SEC responses. P7-17 records the design.

`events/layer.py` is package code, like Stage 4's `cohort/synthetic.py`, because P-VI
consumes its output.
- **What it writes.** `write_layer(root, repo)` saves what discovery would fetch for
  the synthetic cohort's five candidate issuers:
  - each submissions file, and each older page in range;
  - each companyfacts file;
  - the index page of every Item 2.02 8-K and 8-K/A in range;
  - the primary document of every candidate.

  Every response has one retrieval time. No exhibit is saved (EV2).
- **What it invents.** Every company, filing, and word is invented. Each case takes
  its shape from a real filing that plan 7 read, and never its wording.

Task 15 writes this layer into the committed fixture, with the overrides and the
frozen manifests.

The cases, by issuer:

- **Acme Industrial.**
  - Its fiscal year ends in May, as Nike's does, and it trips no guard.
  - Its submissions give Eastern digits.
  - Its quarter ended 2025-02-28 has two candidates that the rule cannot separate: a
    sale's estimated effect on the quarter, and the release itself.
  - A release and a 10-Q accepted after the cutoff are never read.
- **Borealis Air.**
  - It leaves the index before the open on 2024-11-08, and releases its third
    quarter at 07:00 that day, which is a `same_day_transition`.
  - Its exhibit is typed `EX-99`, and an 8-K/A follows it.
  - It is acquired and files nothing after its report for 2025-03-31. That trips the
    third `period_gap` case.
  - It has no eligible event, so its exit has no event on the member side, which the
    pilot reports.
- **Corvid Systems.**
  - It joins on 2024-11-08, and its first periodic report covers 2024-12-31. That
    trips the second `period_gap` case.
  - Its exhibits are typed `EX-99.01`.
  - Its labels for 2025-06-30 disagree. That quarter's only `EX-99` is a pro forma
    overview, like V2's AMC case, which plan B needs.
- **Dynamo Motors.**
  - It holds two securities, and makes one slot per period.
  - Its calendar ends 2026-07-03, outside the window.
  - Its fourth quarter of 2024 has a preliminary filing, then the release.
  - Its quarter ended 2025-06-27 has no candidate, only a Regulation FD 8-K.
  - Its release for 2025-09-26 is narrative-only.
- **Eastfield Bank.**
  - It leaves the index on 2026-06-22.
  - It has no 10-Q for 2025-06-30, which trips the first `period_gap` case. So the
    next quarter's release is also a candidate for 2025-03-31, and the rule drops it
    because it states another period.
  - Its submissions give true UTC.
  - One of its older pages is read, and the other is skipped by its dates.

Before any override, the layer gives these counts:

- **Slots.** 32 slots, and 26 are `member_at_publication`.
- **Other outcomes.**
  - Acme's quarter ended 2025-02-28 is `several_release_filings`.
  - Borealis' quarter ended 2024-09-30 is `same_day_transition`.
  - Dynamo's quarter ended 2025-06-27 is `no_release_filing`.
  - Three rows are `not_member_at_publication`.
- **Findings.** The three period gaps, and one `fiscal_labels_unknown`.
- **After Task 12's overrides.** 27 events are eligible across four issuers and all
  eight quarters. That is fewer than 40 and at least 20, so P-VI takes the
  underfilled path.

The test runs the per-slot sequence that Task 12's build will run, one function at a
time: filings, slots, `identify`, and `decide`. It checks each event's reason, the
findings, and each case. It also checks that the layer holds exactly the primary
documents of the candidates, and regenerates byte for byte.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/layer.py`.
- Test (create): `packages/earnings-ingestion/tests/test_events_layer.py`.

**Interfaces:**

- Consumes:
  - Task 7's `SyntheticFiling`, `SyntheticStore`, and `older_page_entry`;
  - Task 9's `eight_k` and `SyntheticStore.document`;
  - Tasks 7 to 10's `issuer_filings`, `issuer_slots`, `identify`, `memberships`, and
    `decide`, in the test;
  - Stage 4's committed `tests/fixtures/cohort/manifests/djia-synthetic-v1.json`.
- Produces `events/layer.py`:
  - `RETRIEVED` (2026-09-28 12:00 UTC);
  - `Registrant(cik, name, stem, convention)`, `Report(form, period, accepted, labels)`,
    and `Release(accepted, text, items, form, exhibit, other)`;
  - `ACME`, `BOREALIS`, `CORVID`, `DYNAMO`, `EASTFIELD`, `REGISTRANTS`, `REPORTS`,
    `RELEASES`, and `OLDER_PAGES`;
  - `filings(registrant) -> list[tuple[SyntheticFiling, Report | Release]]`, which
    numbers each filing in acceptance order;
  - `write_layer(root, repo) -> SyntheticStore`, which Task 12's tests read and
    Task 15's generator writes into the fixture.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_layer.py`:

```python
"""The synthetic event layer (the Stage 5 spec, §The synthetic event layer; plan 7,
P7-17), read through the slot, release, and eligibility functions over Stage 4's
synthetic cohort, before any override.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.eligibility import decide, memberships
from earnings_ingestion.events.filings import IssuerFilings, issuer_filings
from earnings_ingestion.events.layer import ACME, filings, write_layer
from earnings_ingestion.events.release import Identification, identify
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import Slot, issuer_slots
from earnings_ingestion.events.synthetic import SyntheticStore
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.sec.companyfacts import read_companyfacts
from earnings_ingestion.sec.urls import (
    archive_url,
    companyfacts_url,
    filing_index_url,
    submissions_page_url,
)

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "tests" / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"


@dataclass(frozen=True)
class Read:
    """What the functions make of one issuer's saved responses."""

    filings: IssuerFilings
    slots: tuple[Slot, ...]
    findings: tuple
    identified: dict[str, Identification]
    reasons: dict[str, str]


def read_issuer(saved, manifest, issuer) -> Read:
    definition = manifest.definition
    start, stop = definition.period_end_start, definition.period_end_stop
    cutoff = definition.public_information_cutoff
    placed = issuer_filings(
        saved, issuer.cik, issuer.issuer_id, start=start, cutoff=cutoff
    )
    facts = read_companyfacts(saved.get(companyfacts_url(issuer.cik)).text.body)
    slots, findings = issuer_slots(
        placed, facts, issuer.issuer_id, start=start, stop=stop
    )
    identified, reasons = {}, {}
    membership = memberships(manifest)[issuer.issuer_id]
    for slot in slots:
        found = identify(slot, placed.releases, saved, cutoff=cutoff)
        published = None if found.release is None else found.release.placed.instant
        decision = decide(
            slot.period_end,
            published,
            found.reason,
            membership,
            start=start,
            stop=stop,
            cutoff=cutoff,
        )
        identified[slot.event_id] = found
        reasons[slot.event_id] = decision.reason.value
    return Read(placed, slots, findings, identified, reasons)


@pytest.fixture(scope="module")
def layer(tmp_path_factory) -> SyntheticStore:
    repo = tmp_path_factory.mktemp("repo")
    return write_layer(repo / "data" / "raw" / "events", repo)


def saved_urls(layer: SyntheticStore) -> set[str]:
    folder = layer.store.root / "sec-edgar" / "retrievals"
    return {
        Retrieval.model_validate_json(path.read_text()).request_url
        for path in folder.glob("*/*.json")
    }


@pytest.fixture(scope="module")
def read(layer) -> dict[str, Read]:
    manifest = load_manifest(COHORT)
    saved = SavedResponses(layer.store)
    return {
        issuer.issuer_id: read_issuer(saved, manifest, issuer)
        for issuer in manifest.issuers
        if issuer.issuer_id in manifest.candidate_issuer_ids
    }


EXCEPTIONS = {
    "cik-0009990001:2025-02-28": "several_release_filings",
    "cik-0009990002:2024-09-30": "same_day_transition",
    "cik-0009990002:2024-12-31": "not_member_at_publication",
    "cik-0009990002:2025-03-31": "not_member_at_publication",
    "cik-0009990005:2025-06-27": "no_release_filing",
    "cik-0009990006:2026-06-30": "not_member_at_publication",
}
"""Every other event is ``member_at_publication``."""


def test_every_event_s_reason_before_any_override(read) -> None:
    reasons = {k: v for issuer in read.values() for k, v in issuer.reasons.items()}
    assert len(reasons) == 32
    assert {k: v for k, v in reasons.items() if k in EXCEPTIONS} == EXCEPTIONS
    others = {v for k, v in reasons.items() if k not in EXCEPTIONS}
    assert others == {"member_at_publication"}
    assert sum(v == "member_at_publication" for v in reasons.values()) == 26


def test_nothing_is_missing_and_the_findings_are_the_layer_s(read) -> None:
    problems = [p for issuer in read.values() for p in issuer.filings.problems]
    problems += [
        p
        for issuer in read.values()
        for found in issuer.identified.values()
        for p in found.problems
    ]
    assert problems == []
    findings = sorted(
        f.finding_id
        for issuer in read.values()
        for f in (*issuer.filings.findings, *issuer.findings)
    )
    assert findings == [
        "fiscal_labels_unknown:cik-0009990003:2025-06-30",
        "period_gap:cik-0009990002:2025-03-31:2026-07-01",
        "period_gap:cik-0009990003:2024-07-01:2024-12-31",
        "period_gap:cik-0009990006:2025-03-31:2025-09-30",
    ]


def test_the_slots_follow_each_calendar(read) -> None:
    """Acme's May fiscal year trips no guard; Dynamo's two securities make one slot
    per period, and its 2026-07-03 period end lies outside the window."""
    ends = {k: [s.period_end for s in v.slots] for k, v in read.items()}
    assert ends["cik-0009990001"][0] == date(2024, 8, 31)
    assert ends["cik-0009990001"][-1] == date(2026, 5, 31)
    assert [len(v) for v in ends.values()] == [8, 3, 7, 7, 7]
    assert ends["cik-0009990005"][-1] == date(2026, 4, 3)
    assert read["cik-0009990005"].slots[-1].next_period_end == date(2026, 7, 3)


def test_each_release_is_identified_by_its_statements(read) -> None:
    methods = {
        event_id: (found.method and found.method.value)
        for issuer in read.values()
        for event_id, found in issuer.identified.items()
    }
    assert methods["cik-0009990005:2025-09-26"] == "sole_candidate"
    assert methods["cik-0009990003:2025-06-30"] == "sole_candidate"
    assert methods["cik-0009990001:2025-02-28"] is None
    assert methods["cik-0009990005:2025-06-27"] is None
    stated = {k for k, v in methods.items() if v == "stated_period"}
    assert len(stated) == 30 - 2


def test_the_preliminary_filing_is_dropped_and_the_gap_s_neighbor_too(read) -> None:
    fourth = read["cik-0009990005"].identified["cik-0009990005:2024-12-31"]
    assert [c.dropped for c in fourth.candidates] == [
        "it calls its results preliminary",
        None,
    ]
    first = read["cik-0009990006"].identified["cik-0009990006:2025-03-31"]
    assert [c.dropped for c in first.candidates] == [None, "it states another period"]


def test_exhibit_numbering_and_the_amendment(read) -> None:
    """Borealis' exhibit is typed EX-99 and Corvid's EX-99.01; Borealis' 8-K/A is
    recorded and never chosen."""
    borealis = read["cik-0009990002"].identified["cik-0009990002:2024-09-30"]
    assert [d.doc_type for d in borealis.release.placed.index.exhibits_99()] == [
        "EX-99"
    ]
    assert [p.filing.form for p in borealis.amendments] == ["8-K/A"]
    corvid = read["cik-0009990003"].identified["cik-0009990003:2024-12-31"]
    assert [d.doc_type for d in corvid.release.placed.index.exhibits_99()] == [
        "EX-99.01"
    ]


def test_the_conventions_and_the_older_pages(read) -> None:
    conventions = {
        k: {file.survey.convention for file in v.filings.files} for k, v in read.items()
    }
    assert conventions == {
        "cik-0009990001": {Convention.EASTERN_DIGITS},
        "cik-0009990002": {Convention.EASTERN_DIGITS},
        "cik-0009990003": {Convention.UTC},
        "cik-0009990005": {Convention.UTC},
        "cik-0009990006": {Convention.UTC},
    }
    eastfield = read["cik-0009990006"].filings
    assert [file.artifact.url for file in eastfield.files][1:] == [
        submissions_page_url("CIK0009990006-submissions-001.json")
    ]
    assert [page.url for page in eastfield.skipped] == [
        submissions_page_url("CIK0009990006-submissions-002.json")
    ]


def test_the_layer_holds_what_discovery_fetches_and_no_filing_after_the_cutoff(
    layer, read
) -> None:
    """Primary documents only of candidates; no exhibit; nothing accepted after the
    cutoff."""
    urls = saved_urls(layer)
    documents = {url for url in urls if "-8k-" in url}
    candidates = {
        archive_url(
            issuer.filings.cik,
            candidate.placed.filing.accession,
            candidate.placed.filing.primary_document,
        )
        for issuer in read.values()
        for found in issuer.identified.values()
        for candidate in found.candidates
    }
    assert documents == candidates
    assert not any("-ex" in url for url in urls)
    (late,) = [f for f, _ in filings(ACME) if f.accepted == "2026-09-24 16:05:00"]
    assert filing_index_url(ACME.cik, late.accession) not in urls
    acme = read["cik-0009990001"]
    assert date(2026, 8, 31) not in [slot.period_end for slot in acme.slots]


def test_the_layer_regenerates_byte_for_byte(layer, tmp_path) -> None:
    again = write_layer(tmp_path / "data" / "raw" / "events", tmp_path)
    first, second = layer.store.root, again.store.root
    files = sorted(p.relative_to(first) for p in first.rglob("*") if p.is_file())
    assert files == sorted(
        p.relative_to(second) for p in second.rglob("*") if p.is_file()
    )
    assert all((first / f).read_bytes() == (second / f).read_bytes() for f in files)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_layer.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_layer.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.layer'`.

- [x] **Step 3: Write the layer**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/layer.py`:

```python
"""The synthetic event layer (the Stage 5 spec, §The synthetic event layer; plan 7,
P7-17).

``write_layer(root, repo)`` saves, under ``root``, every response that discovery would
fetch for the synthetic cohort's five candidate issuers, all retrieved at
``RETRIEVED``:

- each submissions file, and each older page whose dates meet the range;
- each companyfacts file;
- the index page of every Item 2.02 8-K and 8-K/A that either convention places in
  ``[2024-07-01, 2026-09-22]``;
- the primary document of every candidate.

It saves no exhibit (EV2). Every company, filing, and word is invented; each case
takes its shape from the real filings plan 7 read, never their wording.

The cases, by issuer:

- **Acme Industrial**, a fiscal year ending in May like Nike's, which trips no guard.
  Its submissions give Eastern digits. The quarter ended 2025-02-28 has two
  candidates the rule cannot separate, a sale's effect on the quarter and the
  release. A release and a 10-Q accepted after the cutoff are never read.
- **Borealis Air** leaves the index before the open on 2024-11-08, and releases its
  third quarter at 07:00 that day, a ``same_day_transition``. Its exhibit is typed
  ``EX-99``, and an 8-K/A follows. It is acquired and files nothing after its report
  for 2025-03-31, so no period end follows it: the third ``period_gap`` case.
- **Corvid Systems** joins on 2024-11-08, and its first periodic report covers
  2024-12-31: the second ``period_gap`` case. Its exhibits are typed ``EX-99.01``.
  Its labels for 2025-06-30 disagree, and that quarter's only ``EX-99`` is a pro forma
  overview, like V2's AMC case, for plan B.
- **Dynamo Motors** holds two securities and makes one slot per period. Its calendar
  ends 2026-07-03, outside the window. Its fourth quarter of 2024 has a preliminary
  filing and then the release. Its quarter ended 2025-06-27 has no candidate, and its
  release for 2025-09-26 is narrative-only.
- **Eastfield Bank** leaves on 2026-06-22. It has no 10-Q for 2025-06-30, the first
  ``period_gap`` case. Its submissions give true UTC. One older page is read, and one
  is skipped by its dates.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.synthetic import (
    SyntheticFiling,
    SyntheticStore,
    eight_k,
    older_page_entry,
)

RETRIEVED = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class Registrant:
    cik: str
    name: str
    stem: str
    """The prefix of its documents' file names."""
    convention: Convention


@dataclass(frozen=True)
class Report:
    """An original periodic report, and the labels its companyfacts facts state."""

    form: str
    period: date
    accepted: str
    labels: tuple[tuple[int, str], ...]


@dataclass(frozen=True)
class Release:
    """An 8-K. ``text`` is its Item 2.02 section; ``None`` when discovery never
    fetches its document, because it is no candidate."""

    accepted: str
    text: tuple[str, ...] | None
    items: tuple[str, ...] = ("2.02", "9.01")
    form: str = "8-K"
    exhibit: tuple[str, str] = ("EX-99.1", "Earnings release")
    """The index page's only exhibit: its type and description."""
    other: tuple[tuple[str, tuple[str, ...]], ...] = ()
    """The document's other items, before 9.01."""


ACME = Registrant(
    "0009990001", "Acme Industrial Corp", "acme", Convention.EASTERN_DIGITS
)
BOREALIS = Registrant(
    "0009990002", "Borealis Air Inc", "bora", Convention.EASTERN_DIGITS
)
CORVID = Registrant("0009990003", "Corvid Systems Inc", "crvd", Convention.UTC)
DYNAMO = Registrant("0009990005", "Dynamo Motors Co", "dyna", Convention.UTC)
EASTFIELD = Registrant("0009990006", "Eastfield Bank Corp", "efb", Convention.UTC)
REGISTRANTS = (ACME, BOREALIS, CORVID, DYNAMO, EASTFIELD)


def _q(form: str, period: str, accepted: str, *labels: tuple[int, str]) -> Report:
    return Report(form, date.fromisoformat(period), accepted, labels)


def _said(name: str, phrase: str, exhibit: str = "99.1") -> tuple[str, ...]:
    return (
        f"{name} announced {phrase}, in the release furnished as Exhibit {exhibit}.",
    )


REPORTS = {
    ACME: (
        _q("10-K", "2024-05-31", "2024-07-25 16:15:00", (2024, "FY")),
        _q("10-Q", "2024-08-31", "2024-10-08 16:10:00", (2025, "Q1")),
        _q("10-Q", "2024-11-30", "2025-01-07 16:10:00", (2025, "Q2")),
        _q("10-Q", "2025-02-28", "2025-04-08 16:10:00", (2025, "Q3")),
        _q("10-K", "2025-05-31", "2025-07-24 16:15:00", (2025, "FY")),
        _q("10-Q", "2025-08-31", "2025-10-07 16:10:00", (2026, "Q1")),
        _q("10-Q", "2025-11-30", "2026-01-06 16:10:00", (2026, "Q2")),
        _q("10-Q", "2026-02-28", "2026-04-07 16:10:00", (2026, "Q3")),
        _q("10-K", "2026-05-31", "2026-07-23 16:15:00", (2026, "FY")),
        _q("10-Q", "2026-08-31", "2026-09-25 16:10:00", (2027, "Q1")),
    ),
    BOREALIS: (
        _q("10-Q", "2024-06-30", "2024-08-02 16:20:00", (2024, "Q2")),
        _q("10-Q", "2024-09-30", "2024-11-12 16:20:00", (2024, "Q3")),
        _q("10-K", "2024-12-31", "2025-02-20 16:30:00", (2024, "FY")),
        _q("10-Q", "2025-03-31", "2025-05-02 16:20:00", (2025, "Q1")),
    ),
    CORVID: (
        _q("10-K", "2024-12-31", "2025-03-03 16:30:00", (2024, "FY")),
        _q("10-Q", "2025-03-31", "2025-05-06 16:30:00", (2025, "Q1")),
        _q("10-Q", "2025-06-30", "2025-08-05 16:30:00", (2025, "Q2"), (2025, "Q3")),
        _q("10-Q", "2025-09-30", "2025-11-04 16:30:00", (2025, "Q3")),
        _q("10-K", "2025-12-31", "2026-02-24 16:30:00", (2025, "FY")),
        _q("10-Q", "2026-03-31", "2026-05-05 16:30:00", (2026, "Q1")),
        _q("10-Q", "2026-06-30", "2026-08-04 16:30:00", (2026, "Q2")),
    ),
    DYNAMO: (
        _q("10-Q", "2024-06-28", "2024-07-30 16:30:00", (2024, "Q2")),
        _q("10-Q", "2024-09-27", "2024-10-29 16:30:00", (2024, "Q3")),
        _q("10-K", "2024-12-31", "2025-02-24 16:30:00", (2024, "FY")),
        _q("10-Q", "2025-03-28", "2025-04-29 16:30:00", (2025, "Q1")),
        _q("10-Q", "2025-06-27", "2025-07-29 16:30:00", (2025, "Q2")),
        _q("10-Q", "2025-09-26", "2025-10-28 16:30:00", (2025, "Q3")),
        _q("10-K", "2025-12-31", "2026-02-23 16:30:00", (2025, "FY")),
        _q("10-Q", "2026-04-03", "2026-05-05 16:30:00", (2026, "Q1")),
        _q("10-Q", "2026-07-03", "2026-08-04 16:30:00", (2026, "Q2")),
    ),
    EASTFIELD: (
        _q("10-Q", "2024-03-31", "2024-05-03 16:30:00", (2024, "Q1")),
        _q("10-Q", "2024-06-30", "2024-08-02 16:30:00", (2024, "Q2")),
        _q("10-Q", "2024-09-30", "2024-11-01 16:30:00", (2024, "Q3")),
        _q("10-K", "2024-12-31", "2025-02-27 16:30:00", (2024, "FY")),
        _q("10-Q", "2025-03-31", "2025-05-02 16:30:00", (2025, "Q1")),
        _q("10-Q", "2025-09-30", "2025-10-31 16:30:00", (2025, "Q3")),
        _q("10-K", "2025-12-31", "2026-02-26 16:30:00", (2025, "FY")),
        _q("10-Q", "2026-03-31", "2026-05-01 16:30:00", (2026, "Q1")),
        _q("10-Q", "2026-06-30", "2026-07-31 16:30:00", (2026, "Q2")),
    ),
}

_ACME = "Acme Industrial Corp"
_BOREALIS = "Borealis Air Inc"
_CORVID = "Corvid Systems Inc"
_DYNAMO = "Dynamo Motors Co"
_EASTFIELD = "Eastfield Bank Corp"
_BOREALIS_EXHIBIT = ("EX-99", "Earnings release")
_CORVID_EXHIBIT = ("EX-99.01", "Earnings release")

RELEASES = {
    ACME: (
        Release("2024-06-27 16:05:00", None),
        Release(
            "2024-09-26 16:05:00",
            _said(_ACME, "its results for the first quarter of fiscal 2025"),
        ),
        Release(
            "2024-12-19 16:05:00",
            _said(_ACME, "its results for the second quarter of fiscal 2025"),
        ),
        Release(
            "2025-03-11 08:00:00",
            (
                (
                    f"{_ACME} agreed to sell its Tooling division. It estimates that"
                    " the sale will add $0.12 to diluted earnings per share for the"
                    " third quarter of fiscal 2025."
                ),
            ),
            items=("2.02", "8.01", "9.01"),
            exhibit=("EX-99.1", "Press release"),
            other=(("8.01", ("The sale awaits regulatory approval.",)),),
        ),
        Release(
            "2025-03-20 16:05:00",
            _said(_ACME, "its results for the third quarter of fiscal 2025"),
        ),
        Release(
            "2025-06-26 16:05:00",
            _said(_ACME, "its fiscal 2025 fourth quarter and full year results"),
        ),
        Release(
            "2025-09-25 16:05:00",
            _said(_ACME, "its results for the first quarter of fiscal 2026"),
        ),
        Release(
            "2025-12-18 16:05:00",
            _said(_ACME, "its results for the second quarter of fiscal 2026"),
        ),
        Release(
            "2026-03-19 16:05:00",
            _said(_ACME, "its results for the third quarter of fiscal 2026"),
        ),
        Release(
            "2026-06-25 16:05:00",
            _said(_ACME, "its results for the fiscal year ended May 31, 2026"),
        ),
        Release("2026-09-24 16:05:00", None),
    ),
    BOREALIS: (
        Release("2024-07-25 07:00:00", None, exhibit=_BOREALIS_EXHIBIT),
        Release(
            "2024-11-08 07:00:00",
            _said(
                _BOREALIS, "its results for the quarter ended September 30, 2024", "99"
            ),
            exhibit=_BOREALIS_EXHIBIT,
        ),
        Release("2024-11-12 09:00:00", None, form="8-K/A", exhibit=_BOREALIS_EXHIBIT),
        Release(
            "2025-02-06 07:00:00",
            _said(_BOREALIS, "its fourth quarter and full year 2024 results", "99"),
            exhibit=_BOREALIS_EXHIBIT,
        ),
        Release(
            "2025-04-24 07:00:00",
            _said(_BOREALIS, "its results for the first quarter of 2025", "99"),
            exhibit=_BOREALIS_EXHIBIT,
        ),
    ),
    CORVID: (
        Release(
            "2025-02-13 16:05:00",
            _said(_CORVID, "its full-year 2024 results", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
        Release(
            "2025-04-30 16:05:00",
            _said(_CORVID, "its Q1 2025 results", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
        Release(
            "2025-07-30 16:05:00",
            _said(_CORVID, "its second quarter of 2025 results", "99.01"),
            exhibit=("EX-99.01", "Pro forma overview"),
        ),
        Release(
            "2025-10-29 16:05:00",
            _said(_CORVID, "its third-quarter 2025 results", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
        Release(
            "2026-02-12 16:05:00",
            _said(_CORVID, "its fourth quarter and full year 2025 results", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
        Release(
            "2026-04-29 16:05:00",
            _said(_CORVID, "its first quarter of 2026 results", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
        Release(
            "2026-07-29 16:05:00",
            _said(_CORVID, "its results for the quarter ended June 30, 2026", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
    ),
    DYNAMO: (
        Release("2024-07-23 06:45:00", None),
        Release(
            "2024-10-22 06:45:00",
            _said(_DYNAMO, "its third quarter of 2024 earnings"),
        ),
        Release(
            "2025-01-13 08:00:00",
            (
                (
                    f"{_DYNAMO} shared preliminary fourth quarter of 2024 deliveries;"
                    " they appear in Exhibit 99.1."
                ),
            ),
        ),
        Release(
            "2025-02-11 06:45:00",
            _said(_DYNAMO, "its fourth quarter and full year 2024 earnings"),
        ),
        Release(
            "2025-04-22 06:45:00",
            _said(_DYNAMO, "its first quarter of 2025 earnings"),
        ),
        Release("2025-07-22 06:45:00", None, items=("7.01", "9.01")),
        Release(
            "2025-10-21 06:45:00",
            (f"{_DYNAMO} furnished its quarterly earnings release as Exhibit 99.1.",),
        ),
        Release(
            "2026-02-10 06:45:00",
            _said(_DYNAMO, "its fourth quarter and full year 2025 earnings"),
        ),
        Release(
            "2026-04-28 06:45:00",
            _said(_DYNAMO, "its first quarter of 2026 earnings"),
        ),
        Release("2026-07-21 06:45:00", None),
    ),
    EASTFIELD: (
        Release("2024-04-19 07:30:00", None),
        Release("2024-07-19 07:30:00", None),
        Release(
            "2024-10-18 07:30:00",
            _said(_EASTFIELD, "third quarter 2024 earnings"),
        ),
        Release(
            "2025-01-17 07:30:00",
            _said(_EASTFIELD, "fourth quarter and full year 2024 earnings"),
        ),
        Release(
            "2025-04-17 07:30:00",
            _said(_EASTFIELD, "first quarter of 2025 earnings"),
        ),
        Release(
            "2025-07-18 07:30:00",
            _said(_EASTFIELD, "second quarter of 2025 earnings"),
        ),
        Release(
            "2025-10-17 07:30:00",
            _said(_EASTFIELD, "third quarter of 2025 earnings"),
        ),
        Release(
            "2026-01-16 07:30:00",
            _said(_EASTFIELD, "fourth quarter and full year 2025 earnings"),
        ),
        Release(
            "2026-04-17 07:30:00",
            _said(_EASTFIELD, "first quarter 2026 earnings"),
        ),
        Release(
            "2026-07-17 07:30:00",
            _said(_EASTFIELD, "second quarter of 2026 earnings"),
        ),
    ),
}

OLDER_PAGES = {
    EASTFIELD: (
        ("CIK0009990006-submissions-001.json", "2024-07-01", "2025-01-01"),
        ("CIK0009990006-submissions-002.json", "2023-01-01", "2024-07-01"),
    ),
}
"""Each older page's name, and the acceptance dates ``[from, to)`` of its filings;
the rest are in the submissions file."""

START, CUTOFF = date(2024, 7, 1), date(2026, 9, 22)


def filings(
    registrant: Registrant,
) -> list[tuple[SyntheticFiling, Report | Release]]:
    """The registrant's filings, numbered in the order accepted."""
    entries = sorted(
        [*REPORTS[registrant], *RELEASES[registrant]], key=lambda e: e.accepted
    )
    filings = []
    for number, entry in enumerate(entries, start=1):
        day = date.fromisoformat(entry.accepted[:10])
        if isinstance(entry, Report):
            filing = SyntheticFiling(
                accession=f"{registrant.cik}-{day:%y}-{number:06d}",
                form=entry.form,
                filing_date=day,
                accepted=entry.accepted,
                report_date=entry.period,
                primary_document=f"{registrant.stem}-{entry.period:%Y%m%d}.htm",
            )
        else:
            suffix = "a" if entry.form == "8-K/A" else ""
            filing = SyntheticFiling(
                accession=f"{registrant.cik}-{day:%y}-{number:06d}",
                form=entry.form,
                filing_date=day,
                accepted=entry.accepted,
                report_date=day,
                items=entry.items,
                primary_document=f"{registrant.stem}-8k-{day:%Y%m%d}{suffix}.htm",
            )
        filings.append((filing, entry))
    return filings


def _exhibit(registrant: Registrant, filing: SyntheticFiling, release: Release):
    kind, description = release.exhibit
    digits = kind.removeprefix("EX-").replace(".", "")
    name = f"{registrant.stem}-{filing.filing_date:%Y%m%d}-ex{digits}.htm"
    return ((description, name, kind),)


def _in_range(filing: SyntheticFiling) -> bool:
    """Either convention's Eastern date lies in ``[START, CUTOFF]``. Every time here
    lies between 06:00 and 19:00 Eastern, where both readings give its own date."""
    return START <= date.fromisoformat(filing.accepted[:10]) <= CUTOFF


def write_layer(root: Path, repo: Path) -> SyntheticStore:
    """Save the layer's responses under ``root``; ``repo`` holds ``root``."""
    store = SyntheticStore(root, repo, RETRIEVED)
    for registrant in REGISTRANTS:
        listed = filings(registrant)
        pages = OLDER_PAGES.get(registrant, ())
        paged = set()
        entries = []
        for name, since, until in pages:
            inside = [
                filing for filing, _ in listed if since <= filing.accepted[:10] < until
            ]
            paged.update(filing.accession for filing in inside)
            entries.append(older_page_entry(name, inside))
            if START <= date.fromisoformat(entries[-1]["filingTo"]) and (
                date.fromisoformat(entries[-1]["filingFrom"]) <= CUTOFF
            ):
                store.older_page(name, inside, convention=registrant.convention)
        recent = [filing for filing, _ in listed if filing.accession not in paged]
        store.submissions(
            registrant.cik,
            registrant.name,
            recent,
            convention=registrant.convention,
            older_pages=entries,
        )
        facts = [
            (filing.accession, year, period)
            for filing, entry in listed
            if isinstance(entry, Report)
            for year, period in entry.labels
        ]
        store.companyfacts(registrant.cik, registrant.name, facts)
        for filing, entry in listed:
            if isinstance(entry, Report) or "2.02" not in entry.items:
                continue
            if not _in_range(filing):
                continue
            store.index(registrant.cik, filing, _exhibit(registrant, filing, entry))
            if entry.text is None:
                continue
            number = entry.exhibit[0].removeprefix("EX-")
            items = [
                ("2.02", entry.text),
                *entry.other,
                ("9.01", (f"Exhibit {number}: {entry.exhibit[1]}.",)),
            ]
            body = eight_k(registrant.name, items, signed=filing.filing_date)
            store.document(registrant.cik, filing, body)
    return store
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/layer.py`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_layer.py -q`

Expected: `9 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py packages/earnings-ingestion/tests/test_events_layer.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1177 passed, 24 deselected`; `All checks passed!` and
`236 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/layer.py packages/earnings-ingestion/tests/test_events_layer.py
git commit -m "feat(events): write the synthetic event layer's saved responses"
```

---

### Task 12: The event build: rows, findings, and overrides

This task implements S §Review overrides and the assembly of S §The event manifest's
rows. P7-12, P7-15, and P7-16 record its choices.

`build_events(universe, saved, overrides, *, corpus_id)` fetches nothing. For each of
the frozen cohort's candidate issuers, it makes one row per slot:
- it reads the saved filings (Task 7);
- it makes the slots (Task 8);
- it identifies each slot's release filing by `release-id/1` (Task 9);
- it decides the slot's eligibility by `eligibility/1` (Task 10).

Then it applies the overrides:

- **`set_release_filing`** must name a filing of the event's issuer that meets four
  conditions:
  - one of the issuer's read files lists it;
  - it is an 8-K or 8-K/A;
  - its index page is saved and names the same accession;
  - its acceptance time falls on or before the cutoff on the Eastern calendar
    (P-C4).

  It need not give Item 2.02, and no P or P′ bound applies, since S sets neither. One
  citation must lie in the filing's folder, and every stored locator must verify, as
  in Stage 4. The event then takes the filing's acceptance time and the method
  `override`, and its eligibility is decided again. The row keeps the rule's
  `candidate_accessions`.
- **`retain_unresolved`** is judged after any `set_release_filing` of the same
  event, against the row that decision leaves. That is why Task 6 allows one override
  of each kind per event (P7-14).
- **`acknowledge`** answers a `period_gap` or `no_slots` finding whose digest it names.

What happens to an override that does not apply (P7-16):

- **Refused.** An override is refused when it:
  - names no such event, finding, or filing;
  - acknowledges another kind of finding;
  - carries a citation that does not verify.

  A refusal is a problem: the build stops with `EventBuildError`, which lists every
  problem. So does any missing or unreadable response.
- **Stale.** An override is stale in two cases:
  - an acknowledgement whose finding has changed, as S says;
  - a `retain_unresolved` whose event is no longer `ambiguous` with its reason, a
    case S does not settle.

  A stale override holds the freeze, and the report names it.
- **Unlike Stage 4.** Stage 4's `acknowledge` treats a finding that has disappeared
  as stale. Here, S calls it refused.

`review(first)` joins `events/layer.py`. It returns the overrides a reviewer records
against the layer's first build:
- acknowledgements of the three period gaps;
- Acme's release, set by review;
- Borealis' same-day case and Dynamo's quarter with no candidate, both retained.

The tests use it here, and Task 15 writes it into the fixture's `overrides.toml`.

`EventBuild` exposes the freeze's three blockers separately: `blocking` (unanswered
findings), `stale_overrides`, and `unretained` (`ambiguous` rows that no override
keeps). What each row rests on stays on the build, outside the hash, for Task 13's
evidence and for the report. That covers the slot, the identification, the chosen
filing, and each issuer's read files. `report()` gives the lines `events build`
prints: each row with each candidate's reading, then the findings and whatever holds
the freeze (P7-15).

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/build.py`.
- Modify, by exact replacement: `packages/earnings-ingestion/src/earnings_ingestion/events/layer.py`.
- Test (create): `packages/earnings-ingestion/tests/test_events_build.py`.

**Interfaces:**

- Consumes:
  - Tasks 7 to 11: `issuer_filings`, `Placed`, `IssuerFilings`, `issuer_slots`,
    `Slot`, `identify`, `Identification`, `RELEASE_POLICY`, `memberships`,
    `decide`, `Decision`, `ELIGIBILITY_POLICY`, and `write_layer`;
  - Task 6's records;
  - Task 3's `operative_hash`;
  - Task 4's `read_companyfacts`, `read_filing_index`, and URLs;
  - Task 5's `accepted_instant`, `eastern_date`, and `SOURCE_TIMEZONE`;
  - Stage 4's `load_toml`, `ArtifactText`, `LocatorError`, `SEC_RIGHTS`, and
    `SEC_SOURCE_ID`.
- Produces `events/build.py`:
  - `CORPUS_ID = "djia-2024q3-2026q2"`, `CORPUS_DIR` (`config/corpus/<CORPUS_ID>`),
    `EVENTS_STORE` (`data/raw/events`), and `EPOCH`;
  - `EventBuildError(problems)`, with `.problems`;
  - `load_overrides(path) -> EventOverridesFile`, which is empty when the file is
    absent;
  - `EventDetail(slot, identification, release, decision)`;
  - `EventBuild(corpus_id, universe, rows, findings, overrides, stale_overrides, details, issuers)`,
    with `blocking`, `unretained`, `holds_freeze`, `manifest(version, created_at)`,
    `content_hash`, and `report() -> list[str]`;
  - `build_events(universe, saved, overrides, *, corpus_id) -> EventBuild`.
- Produces in `events/layer.py`: `REVIEWER`, `REVIEWED_ON`, `GAPS`, and
  `review(first: EventBuild) -> tuple[EventOverride, ...]`, sorted by
  `override_id`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_build.py`:

```python
"""The event build (the Stage 5 spec, §Slots through §Review overrides; plan 7,
P7-15 and P7-16), over the synthetic event layer and Stage 4's synthetic cohort.
"""

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.records import OverrideCitation
from earnings_ingestion.events.build import (
    EPOCH,
    EventBuild,
    EventBuildError,
    build_events,
)
from earnings_ingestion.events.layer import (
    ACME,
    BOREALIS,
    DYNAMO,
    Registrant,
    filings,
    review,
    write_layer,
)
from earnings_ingestion.events.records import (
    EventOverride,
    EventOverrideKind,
    EventOverridesFile,
    EventReason,
    EventStatus,
    IdentificationMethod,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.synthetic import SyntheticStore
from earnings_ingestion.sec.urls import archive_url, filing_index_url

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "tests" / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
SIGNED = {
    "rationale": "Read in review.",
    "reviewer": "Synthetic Reviewer",
    "recorded_on": date(2026, 9, 28),
}
GAPS = (
    "period_gap:cik-0009990002:2025-03-31:2026-07-01",
    "period_gap:cik-0009990003:2024-07-01:2024-12-31",
    "period_gap:cik-0009990006:2025-03-31:2025-09-30",
)
ACME_SET = "cik-0009990001:2025-02-28"
BOREALIS_SAME_DAY = "cik-0009990002:2024-09-30"
DYNAMO_NONE = "cik-0009990005:2025-06-27"
DYNAMO_ID = "cik-0009990005"


@pytest.fixture(scope="module")
def universe():
    return load_manifest(COHORT)


@pytest.fixture(scope="module")
def layer(tmp_path_factory) -> SyntheticStore:
    repo = tmp_path_factory.mktemp("repo")
    return write_layer(repo / "data" / "raw" / "events", repo)


def run(universe, layer: SyntheticStore, *overrides: EventOverride) -> EventBuild:
    return build_events(
        universe,
        SavedResponses(layer.store),
        EventOverridesFile(schema_version=1, overrides=overrides),
        corpus_id="djia-synthetic",
    )


def accession(registrant: Registrant, accepted: str) -> str:
    (filing,) = [f for f, _ in filings(registrant) if f.accepted == accepted]
    return filing.accession


def acknowledge(override_id: str, finding_id: str, digest: str) -> EventOverride:
    return EventOverride(
        override_id=override_id,
        kind=EventOverrideKind.ACKNOWLEDGE,
        finding_id=finding_id,
        finding_digest=digest,
        **SIGNED,
    )


def retain(override_id: str, event_id: str, reason: EventReason) -> EventOverride:
    return EventOverride(
        override_id=override_id,
        kind=EventOverrideKind.RETAIN_UNRESOLVED,
        event_id=event_id,
        reason=reason,
        **SIGNED,
    )


def choose(
    layer: SyntheticStore, event_id: str, registrant: Registrant, accepted: str
) -> EventOverride:
    """Set a filing as the event's release, citing its index page's Accepted value."""
    number = accession(registrant, accepted)
    url = filing_index_url(registrant.cik, number)
    artifact = SavedResponses(layer.store).get(url)
    return EventOverride(
        override_id=f"release-{event_id.replace(':', '-')}",
        kind=EventOverrideKind.SET_RELEASE_FILING,
        event_id=event_id,
        accession=number,
        citations=(
            OverrideCitation(
                source_id="sec-edgar",
                url=url,
                artifact_sha256=artifact.artifact.content_sha256,
                locator=artifact.text.find(accepted),
            ),
        ),
        **SIGNED,
    )


def test_the_layer_builds_its_rows_with_what_holds_the_freeze(universe, layer) -> None:
    built = run(universe, layer)
    assert len(built.rows) == 32
    assert [f.finding_id for f in built.blocking] == list(GAPS)
    assert [row.event_id for row in built.unretained] == [
        ACME_SET,
        BOREALIS_SAME_DAY,
        DYNAMO_NONE,
    ]
    assert built.stale_overrides == ()
    assert built.holds_freeze
    statuses = [row.eligibility_status for row in built.rows]
    assert statuses.count(EventStatus.ELIGIBLE) == 26


def test_the_reviewed_overrides_settle_everything(universe, layer) -> None:
    built = run(universe, layer, *review(run(universe, layer)))
    assert not built.holds_freeze
    eligible = [r for r in built.rows if r.eligibility_status is EventStatus.ELIGIBLE]
    assert len(eligible) == 27
    assert len({row.issuer_id for row in eligible}) == 4
    rows = {row.event_id: row for row in built.rows}
    acme = rows[ACME_SET]
    assert acme.release_accession == accession(ACME, "2025-03-20 16:05:00")
    assert acme.identification_method is IdentificationMethod.OVERRIDE
    assert acme.override_ids == ("release-acme-2025-02-28",)
    assert acme.first_publication_time == datetime(2025, 3, 20, 20, 5, tzinfo=UTC)
    assert len(acme.candidate_accessions) == 2
    same_day = rows[BOREALIS_SAME_DAY]
    assert (same_day.retained, same_day.eligibility_reason) == (
        True,
        EventReason.SAME_DAY_TRANSITION,
    )
    assert (
        same_day.membership_assertion_id == "index-2024-11-01:borealis-common:removed"
    )
    assert rows[DYNAMO_NONE].override_ids == ("keep-dynamo-no-release",)
    assert [f.resolved_by for f in built.findings if f.finding_id in GAPS] == [
        ("gap-borealis",),
        ("gap-corvid",),
        ("gap-eastfield",),
    ]


def test_record_fields_stay_separate_and_unknown_labels_stay_null(
    universe, layer
) -> None:
    """R1.5 and P-A5: the period end, the labels, and the two times are separate
    fields; Corvid's disagreeing labels stay null, and its release is still read."""
    rows = {row.event_id: row for row in run(universe, layer).rows}
    corvid = rows["cik-0009990003:2025-06-30"]
    assert (corvid.reported_fiscal_year, corvid.reported_fiscal_quarter) == (None, None)
    assert corvid.identification_method is IdentificationMethod.SOLE_CANDIDATE
    acme = rows["cik-0009990001:2024-08-31"]
    assert (acme.period_end, acme.reported_fiscal_year) == (date(2024, 8, 31), 2025)
    assert acme.reported_fiscal_quarter == "Q1"
    assert acme.filing_acceptance_time == datetime(2024, 9, 26, 20, 5, tzinfo=UTC)
    assert acme.first_publication_time == acme.filing_acceptance_time


def test_two_securities_make_one_row_per_period(universe, layer) -> None:
    rows = [row for row in run(universe, layer).rows if row.issuer_id == DYNAMO_ID]
    assert len(rows) == len({row.period_end for row in rows}) == 7


def test_a_changed_finding_makes_its_acknowledgement_stale(universe, layer) -> None:
    built = run(universe, layer, acknowledge("gap-old", GAPS[2], "0" * 64))
    assert built.stale_overrides == ("gap-old",)
    assert GAPS[2] in [f.finding_id for f in built.blocking]
    assert "gap-old: stale, and holds the freeze" in built.report()


@pytest.mark.parametrize(
    ("event_id", "reason"),
    [
        ("cik-0009990001:2024-08-31", EventReason.SEVERAL_RELEASE_FILINGS),
        (DYNAMO_NONE, EventReason.SEVERAL_RELEASE_FILINGS),
    ],
    ids=["eligible-event", "another-reason"],
)
def test_a_retain_that_no_longer_matches_its_event_is_stale(
    universe, layer, event_id, reason
) -> None:
    built = run(universe, layer, retain("keep", event_id, reason))
    assert built.stale_overrides == ("keep",)
    assert not {row.event_id: row for row in built.rows}[event_id].retained


def test_a_set_release_filing_decides_eligibility_again(universe, layer) -> None:
    """The 8-K/A accepted after Borealis left makes the event ineligible; the
    release itself, set by review, stays a same-day case that needs retaining."""
    amended = choose(layer, BOREALIS_SAME_DAY, BOREALIS, "2024-11-12 09:00:00")
    row = {r.event_id: r for r in run(universe, layer, amended).rows}[BOREALIS_SAME_DAY]
    assert row.eligibility_reason is EventReason.NOT_MEMBER_AT_PUBLICATION
    assert row.identification_method is IdentificationMethod.OVERRIDE
    confirmed = choose(layer, BOREALIS_SAME_DAY, BOREALIS, "2024-11-08 07:00:00")
    kept = retain("keep", BOREALIS_SAME_DAY, EventReason.SAME_DAY_TRANSITION)
    row = {r.event_id: r for r in run(universe, layer, confirmed, kept).rows}[
        BOREALIS_SAME_DAY
    ]
    assert row.retained
    assert row.override_ids == ("keep", "release-cik-0009990002-2024-09-30")


def refused(universe, layer, *overrides) -> tuple[str, ...]:
    with pytest.raises(EventBuildError) as raised:
        run(universe, layer, *overrides)
    return raised.value.problems


def test_overrides_that_name_nothing_are_refused(universe, layer) -> None:
    labels = "fiscal_labels_unknown:cik-0009990003:2025-06-30"
    digest = {f.finding_id: f.digest for f in run(universe, layer).findings}[labels]
    problems = refused(
        universe,
        layer,
        retain("keep", "cik-0009990001:2024-09-30", EventReason.NO_RELEASE_FILING),
        acknowledge(
            "gap-none", "period_gap:cik-0009990001:2024-07-01:2024-08-31", "0" * 64
        ),
        acknowledge("labels", labels, digest),
    )
    assert problems == (
        "keep: no event cik-0009990001:2024-09-30",
        "gap-none: no finding period_gap:cik-0009990001:2024-07-01:2024-08-31",
        "labels: a fiscal_labels_unknown finding is never acknowledged",
    )


def test_a_set_release_filing_must_name_a_saved_8_k_of_the_issuer(
    universe, layer
) -> None:
    good = choose(layer, ACME_SET, ACME, "2025-03-20 16:05:00")
    report = accession(ACME, "2025-04-08 16:10:00")
    regulation_fd = accession(DYNAMO, "2025-07-22 06:45:00")
    cases = [
        good.model_copy(update={"accession": "0009990001-25-999999"}),
        good.model_copy(update={"accession": report}),
        good.model_copy(update={"event_id": DYNAMO_NONE, "accession": regulation_fd}),
    ]
    problems = [refused(universe, layer, case)[0] for case in cases]
    who = "release-cik-0009990001-2025-02-28"
    assert problems == [
        f"{who}: the issuer's read filings list no 0009990001-25-999999",
        f"{who}: {report} is a 10-Q, not an 8-K or 8-K/A",
        (
            f"{who}: no index page of {regulation_fd} is saved: run events"
            f" discover --filing 0009990005 {regulation_fd}"
        ),
    ]


def test_a_set_release_filing_must_cite_the_filing_verifiably(universe, layer) -> None:
    good = choose(layer, ACME_SET, ACME, "2025-03-20 16:05:00")
    (citation,) = good.citations
    elsewhere = citation.model_copy(
        update={
            "url": archive_url(ACME.cik, accession(ACME, "2025-03-11 08:00:00"), "")
        }
    )
    changed = citation.model_copy(
        update={
            "locator": citation.locator.model_copy(update={"cited_sha256": "0" * 64})
        }
    )
    folder = archive_url(ACME.cik, good.accession, "")
    assert refused(
        universe, layer, good.model_copy(update={"citations": (elsewhere,)})
    ) == (f"release-cik-0009990001-2025-02-28: no citation is in {folder}",)
    assert refused(
        universe, layer, good.model_copy(update={"citations": (changed,)})
    ) == (
        (
            "release-cik-0009990001-2025-02-28: the cited content no longer hashes"
            " to cited_sha256"
        ),
    )


def test_a_filing_accepted_after_the_cutoff_is_refused(universe, tmp_path) -> None:
    """P-C4. The layer saves no index page for Acme's late release; this test saves
    one, so that the cutoff itself refuses it."""
    layer = write_layer(tmp_path / "data" / "raw" / "events", tmp_path)
    ((late, _),) = [
        (f, e) for f, e in filings(ACME) if f.accepted == "2026-09-24 16:05:00"
    ]
    layer.index(ACME.cik, late, (("Earnings release", "late.htm", "EX-99.1"),))
    override = choose(layer, "cik-0009990001:2026-05-31", ACME, late.accepted)
    assert refused(universe, layer, override) == (
        (
            f"release-cik-0009990001-2026-05-31: {late.accession} was accepted on"
            " 2026-09-24, after the cutoff 2026-09-22 (P-C4)"
        ),
    )


def test_a_missing_response_stops_the_build(universe, tmp_path) -> None:
    empty = SyntheticStore(tmp_path / "data" / "raw" / "events", tmp_path, EPOCH)
    problems = refused(universe, empty)
    assert len(problems) == 10
    submissions = "https://data.sec.gov/submissions/CIK0009990001.json"
    facts = "https://data.sec.gov/api/xbrl/companyfacts/CIK0009990001.json"
    assert problems[:2] == (
        f"nothing saved from {submissions}: run events discover",
        f"nothing saved from {facts}: run events discover",
    )


def test_the_report_prints_each_candidate_s_reading(universe, layer) -> None:
    report = run(universe, layer).report()
    start = report.index(
        "cik-0009990005:2024-12-31  eligible  member_at_publication"
        f"  {accession(DYNAMO, '2025-02-11 06:45:00')} (stated_period)"
    )
    assert report[start + 1] == (
        f"  candidate {accession(DYNAMO, '2025-01-13 08:00:00')} accepted"
        " 2025-01-13 13:00 UTC: dates -; periods Q4 2024; preliminary yes;"
        " it calls its results preliminary"
    )
    assert report[start + 2].endswith("periods FY 2024; preliminary no; kept")
    assert f"{GAPS[0]} [blocks]: " in "\n".join(report)


def test_the_content_hash_leaves_out_the_version_and_time(universe, layer) -> None:
    built = run(universe, layer)
    later = built.manifest(2, datetime(2026, 9, 29, tzinfo=UTC))
    assert later.definition.content_hash == built.content_hash
    assert run(universe, layer).content_hash == built.content_hash
    assert later.definition.discovery_policy_version == "release-id/1"
    assert later.definition.eligibility_policy_version == "eligibility/1"
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_build.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_build.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.build'`.

- [x] **Step 3: Write the build**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/build.py`:

```python
"""Build the event manifest from the frozen cohort and Stage 5's saved responses (the
Stage 5 spec, §Slots through §Review overrides; plan 7, P7-12, P7-15, and P7-16).

``build_events`` fetches nothing. Every fact it uses is in the frozen cohort, the
overrides file, or a response saved under ``data/raw/events/``. For each candidate
issuer, it reads the saved filings, makes the slots, identifies each slot's release
filing by ``release-id/1``, and decides its eligibility by ``eligibility/1``. Then it
applies the overrides:

- ``set_release_filing`` names an 8-K or 8-K/A of the event's issuer, listed in the
  issuer's read files, whose index page is saved and which was accepted by the
  cutoff. One of its citations is in that filing's folder. The event takes the
  filing's acceptance time and the method ``override``, and its eligibility is
  decided again, with any outcome.
- ``retain_unresolved`` keeps an event that is ``ambiguous`` with the override's
  reason. It is judged after any ``set_release_filing`` of the same event.
- ``acknowledge`` answers a ``period_gap`` or ``no_slots`` finding whose digest it
  names.

**Refused or stale** (P7-16). An override that names no such event, finding, or
filing is refused, as S §Review overrides says. So is one that acknowledges another
kind of finding, or whose citation does not verify. A refusal is a problem. An
acknowledgement whose finding has changed is stale, as is a ``retain_unresolved``
whose event is no longer ``ambiguous`` with its reason. A stale override holds the
freeze, and ``events build`` names it.

What no review can settle stops the build with ``EventBuildError``, which lists every
problem: a missing or unreadable response, and a refused override. Everything else
the manifest hashes is a fact: no retrieval time, file hash, or pointer into a saved
file, so a re-fetch never re-versions a manifest. What each row rests on stays on the
build, outside the hash, for the evidence record and the report.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from earnings_ingestion.cohort.config import load_toml
from earnings_ingestion.cohort.identity import operative_hash
from earnings_ingestion.cohort.locators import ArtifactText, LocatorError
from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.acceptance import (
    SOURCE_TIMEZONE,
    AcceptanceTimeError,
    accepted_instant,
    eastern_date,
)
from earnings_ingestion.events.eligibility import (
    ELIGIBILITY_POLICY,
    Decision,
    decide,
    memberships,
)
from earnings_ingestion.events.filings import IssuerFilings, Placed, issuer_filings
from earnings_ingestion.events.records import (
    ACKNOWLEDGEABLE,
    EventFinding,
    EventManifest,
    EventManifestDefinition,
    EventOverride,
    EventOverrideKind,
    EventOverridesFile,
    EventRow,
    EventStatus,
    IdentificationMethod,
    content_hash,
)
from earnings_ingestion.events.release import (
    RELEASE_POLICY,
    Identification,
    identify,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import Slot, issuer_slots
from earnings_ingestion.sec.companyfacts import CompanyFacts, read_companyfacts
from earnings_ingestion.sec.data import SecDataError
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import archive_url, companyfacts_url, filing_index_url

CORPUS_ID = "djia-2024q3-2026q2"
CORPUS_DIR = Path("config") / "corpus" / CORPUS_ID
EVENTS_STORE = Path("data") / "raw" / "events"
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
RELEASE_FORMS = frozenset({"8-K", "8-K/A"})


class EventBuildError(ValueError):
    """Problems no review can settle; the build stops and lists every one."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(problems))


def load_overrides(path: Path) -> EventOverridesFile:
    """The corpus's ``overrides.toml``, read strictly; empty when absent."""
    if not path.exists():
        return EventOverridesFile(schema_version=1)
    return load_toml(path, EventOverridesFile)


@dataclass(frozen=True)
class EventDetail:
    """What one row rests on, kept outside the manifest's hash."""

    slot: Slot
    identification: Identification
    release: Placed | None
    """The rule's release filing, or the one a ``set_release_filing`` names."""
    decision: Decision


@dataclass(frozen=True)
class EventBuild:
    """Everything an event manifest holds except its version, hash, and time."""

    corpus_id: str
    universe: UniverseManifest
    rows: tuple[EventRow, ...]
    findings: tuple[EventFinding, ...]
    overrides: tuple[EventOverride, ...]
    stale_overrides: tuple[str, ...]
    details: dict[str, EventDetail]
    """By ``event_id``."""
    issuers: dict[str, IssuerFilings]
    """By ``issuer_id``."""

    @property
    def blocking(self) -> tuple[EventFinding, ...]:
        """The findings that hold the freeze."""
        return tuple(finding for finding in self.findings if finding.holds_freeze)

    @property
    def unretained(self) -> tuple[EventRow, ...]:
        """The ``ambiguous`` rows no ``retain_unresolved`` keeps."""
        return tuple(
            row
            for row in self.rows
            if row.eligibility_status is EventStatus.AMBIGUOUS and not row.retained
        )

    @property
    def holds_freeze(self) -> bool:
        return bool(self.blocking or self.stale_overrides or self.unretained)

    def manifest(self, version: int, created_at: datetime) -> EventManifest:
        definition = self.universe.definition
        draft = EventManifest(
            definition=EventManifestDefinition(
                corpus_id=self.corpus_id,
                event_manifest_version=version,
                universe_id=definition.universe_id,
                universe_version=definition.universe_version,
                universe_operative_hash=operative_hash(self.universe),
                discovery_policy_version=RELEASE_POLICY,
                eligibility_policy_version=ELIGIBILITY_POLICY,
                public_information_cutoff=definition.public_information_cutoff,
                content_hash="0" * 64,
                created_at=created_at,
            ),
            rows=self.rows,
            findings=self.findings,
            overrides=self.overrides,
        )
        hashed = draft.definition.model_copy(
            update={"content_hash": content_hash(draft)}
        )
        return draft.model_copy(update={"definition": hashed})

    @property
    def content_hash(self) -> str:
        return self.manifest(1, EPOCH).definition.content_hash

    def report(self) -> list[str]:
        """What ``events build`` prints: each row with its candidates' readings, then
        the findings and what holds the freeze (P7-15)."""
        lines = []
        for row in self.rows:
            detail = self.details[row.event_id]
            method = row.identification_method
            release = (
                "no release filing"
                if row.release_accession is None
                else f"{row.release_accession} ({method})"
            )
            lines.append(
                f"{row.event_id}  {row.eligibility_status}"
                f"  {row.eligibility_reason}  {release}"
            )
            found = detail.identification
            for candidate in found.candidates:
                reading = candidate.reading
                said = [
                    f"dates {', '.join(d.isoformat() for d in reading.dates) or '-'}",
                    f"periods {', '.join(map(str, reading.periods)) or '-'}",
                    f"preliminary {'yes' if reading.preliminary else 'no'}",
                ]
                if reading.unread:
                    said.append(f"unread: {reading.unread}")
                lines.append(
                    f"  candidate {candidate.placed.filing.accession}"
                    f" accepted {candidate.placed.instant:%Y-%m-%d %H:%M} UTC:"
                    f" {'; '.join(said)}; {candidate.dropped or 'kept'}"
                )
            for placed in found.amendments:
                lines.append(
                    f"  amendment {placed.filing.accession}, never chosen by the rule"
                )
            for placed, why in found.passed_over:
                lines.append(f"  passed over {placed.filing.accession}: {why}")
        for finding in self.findings:
            if finding.holds_freeze:
                state = "blocks"
            elif finding.resolved_by:
                state = f"acknowledged by {', '.join(finding.resolved_by)}"
            else:
                state = "reported"
            lines.append(f"{finding.finding_id} [{state}]: {finding.detail}")
        for override_id in self.stale_overrides:
            lines.append(f"{override_id}: stale, and holds the freeze")
        for row in self.unretained:
            lines.append(
                f"{row.event_id}: {row.eligibility_reason}, not retained, and holds"
                " the freeze"
            )
        return lines


def _companyfacts(
    saved: SavedResponses, cik: str, problems: list[str]
) -> CompanyFacts | None:
    url = companyfacts_url(cik)
    try:
        artifact = saved.get(url)
        if artifact is None:
            problems.append(f"nothing saved from {url}: run events discover")
            return None
        return read_companyfacts(artifact.text.body)
    except (FileNotFoundError, ValueError) as exc:
        problems.append(f"{url}: {exc}")
        return None


def _named_filing(
    filings: IssuerFilings, saved: SavedResponses, accession: str, cutoff: date
) -> tuple[Placed | None, str | None]:
    """The filing a ``set_release_filing`` names, placed by its index page; or why
    the override is refused."""
    listed = [
        (filing, file)
        for file in filings.files
        for filing in file.filings
        if filing.accession == accession
    ]
    if not listed:
        return None, f"the issuer's read filings list no {accession}"
    filing, file = listed[0]
    if filing.form not in RELEASE_FORMS:
        return None, f"{accession} is a {filing.form}, not an 8-K or 8-K/A"
    url = filing_index_url(filings.cik, accession)
    try:
        artifact = saved.get(url)
        if artifact is None:
            return None, (
                f"no index page of {accession} is saved: run events discover"
                f" --filing {filings.cik} {accession}"
            )
        index = read_filing_index(artifact.text.body)
        instant = accepted_instant(index.accepted)
    except (FileNotFoundError, ValueError, SecDataError, AcceptanceTimeError) as exc:
        return None, f"{url}: {exc}"
    if index.accession != accession:
        return None, f"{url} is the index page of {index.accession}"
    if eastern_date(instant) > cutoff:
        return None, (
            f"{accession} was accepted on {eastern_date(instant)}, after the cutoff"
            f" {cutoff} (P-C4)"
        )
    return Placed(filing, file, index, artifact, instant), None


def _citations_refused(
    override: EventOverride, saved: SavedResponses, folder: str | None
) -> list[str]:
    """Why an override's citations fail: none in the named filing's folder, or a
    stored locator that no longer cites what it hashed."""
    refused = []
    if folder is not None and not any(
        citation.url.startswith(folder) for citation in override.citations
    ):
        refused.append(f"{override.override_id}: no citation is in {folder}")
    for citation in override.citations:
        if citation.artifact_sha256 is None or citation.source_id != SEC_SOURCE_ID:
            continue
        try:
            stored = saved.store.get(
                SEC_SOURCE_ID,
                citation.artifact_sha256,
                rights_status=SEC_RIGHTS.rights_status,
                rights_basis=SEC_RIGHTS.rights_basis,
            )
            if citation.locator is not None:
                ArtifactText(stored.body, stored.ref.media_type).verify(
                    citation.locator
                )
        except (FileNotFoundError, ValueError, LocatorError) as exc:
            refused.append(f"{override.override_id}: {exc}")
    return refused


def build_events(
    universe: UniverseManifest,
    saved: SavedResponses,
    overrides: EventOverridesFile,
    *,
    corpus_id: str,
) -> EventBuild:
    """The event manifest's content that the cohort, overrides, and saved responses
    support; ``EventBuildError`` lists what no review can settle."""
    definition = universe.definition
    start, stop = definition.period_end_start, definition.period_end_stop
    cutoff = definition.public_information_cutoff
    issuers = {issuer.issuer_id: issuer for issuer in universe.issuers}
    problems: list[str] = []
    findings: list[EventFinding] = []
    read: dict[str, IssuerFilings] = {}
    slots: list[tuple[Slot, Identification]] = []
    for issuer_id in sorted(universe.candidate_issuer_ids):
        cik = issuers[issuer_id].cik
        filings = issuer_filings(saved, cik, issuer_id, start=start, cutoff=cutoff)
        read[issuer_id] = filings
        problems.extend(filings.problems)
        findings.extend(filings.findings)
        facts = _companyfacts(saved, cik, problems)
        if filings.registrant is None or facts is None:
            continue
        made, found = issuer_slots(filings, facts, issuer_id, start=start, stop=stop)
        findings.extend(found)
        for slot in made:
            identification = identify(slot, filings.releases, saved, cutoff=cutoff)
            problems.extend(identification.problems)
            slots.append((slot, identification))
    if problems:
        raise EventBuildError(problems)

    by_event = {slot.event_id: (slot, found) for slot, found in slots}
    by_finding = {finding.finding_id: finding for finding in findings}
    sets: dict[str, tuple[EventOverride, Placed]] = {}
    retains: dict[str, EventOverride] = {}
    acknowledged: dict[str, list[str]] = {}
    stale: list[str] = []
    for override in overrides.overrides:
        if override.kind is EventOverrideKind.ACKNOWLEDGE:
            finding = by_finding.get(override.finding_id)
            if finding is None:
                problems.append(
                    f"{override.override_id}: no finding {override.finding_id}"
                )
            elif finding.kind not in ACKNOWLEDGEABLE:
                problems.append(
                    f"{override.override_id}: a {finding.kind} finding is never"
                    " acknowledged"
                )
            elif finding.digest != override.finding_digest:
                stale.append(override.override_id)
            else:
                acknowledged.setdefault(finding.finding_id, []).append(
                    override.override_id
                )
            continue
        if override.event_id not in by_event:
            problems.append(f"{override.override_id}: no event {override.event_id}")
            continue
        if override.kind is EventOverrideKind.RETAIN_UNRESOLVED:
            retains[override.event_id] = override
            continue
        slot, _ = by_event[override.event_id]
        placed, why = _named_filing(
            read[slot.issuer_id], saved, override.accession, cutoff
        )
        if placed is None:
            problems.append(f"{override.override_id}: {why}")
            continue
        folder = archive_url(slot.cik, override.accession, "")
        refused = _citations_refused(override, saved, folder)
        if refused:
            problems.extend(refused)
            continue
        sets[override.event_id] = (override, placed)
    for override in overrides.overrides:
        if override.kind is not EventOverrideKind.SET_RELEASE_FILING:
            problems.extend(_citations_refused(override, saved, None))
    if problems:
        raise EventBuildError(problems)

    members = memberships(universe)
    rows, details = [], {}
    for slot, found in slots:
        applied = []
        if slot.event_id in sets:
            chosen, release = sets[slot.event_id]
            method = IdentificationMethod.OVERRIDE
            applied.append(chosen.override_id)
        elif found.release is not None:
            release, method = found.release.placed, found.method
        else:
            release, method = None, None
        decision = decide(
            slot.period_end,
            None if release is None else release.instant,
            None if release is not None else found.reason,
            members[slot.issuer_id],
            start=start,
            stop=stop,
            cutoff=cutoff,
        )
        retained = False
        if (retain := retains.get(slot.event_id)) is not None:
            if (
                decision.status is EventStatus.AMBIGUOUS
                and decision.reason is retain.reason
            ):
                retained = True
                applied.append(retain.override_id)
            else:
                stale.append(retain.override_id)
        labels = slot.labels
        instant = None if release is None else release.instant
        rows.append(
            EventRow(
                event_id=slot.event_id,
                issuer_id=slot.issuer_id,
                cik=slot.cik,
                period_end=slot.period_end,
                reported_fiscal_year=None if labels is None else labels.fiscal_year,
                reported_fiscal_quarter=(
                    None if labels is None else labels.fiscal_period
                ),
                periodic_accession=slot.periodic.filing.accession,
                periodic_form=slot.periodic.filing.form,
                release_accession=None if release is None else release.filing.accession,
                candidate_accessions=tuple(
                    candidate.placed.filing.accession for candidate in found.candidates
                ),
                identification_method=method,
                filing_acceptance_time=instant,
                first_publication_time=instant,
                source_timezone=SOURCE_TIMEZONE,
                first_publication_source_id=None if release is None else SEC_SOURCE_ID,
                membership_assertion_id=decision.membership_assertion_id,
                eligibility_status=decision.status,
                eligibility_reason=decision.reason,
                retained=retained,
                override_ids=tuple(sorted(applied)),
            )
        )
        details[slot.event_id] = EventDetail(slot, found, release, decision)
    resolved = tuple(
        finding.model_copy(
            update={"resolved_by": tuple(sorted(acknowledged[finding.finding_id]))}
        )
        if finding.finding_id in acknowledged
        else finding
        for finding in sorted(findings, key=lambda f: f.finding_id)
    )
    return EventBuild(
        corpus_id=corpus_id,
        universe=universe,
        rows=tuple(sorted(rows, key=lambda row: row.event_id)),
        findings=resolved,
        overrides=tuple(sorted(overrides.overrides, key=lambda o: o.override_id)),
        stale_overrides=tuple(sorted(stale)),
        details=details,
        issuers=read,
    )
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/build.py`.

Create `/tmp/plan7-task12-layer.py`:

```python
"""Plan 7: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/layer.py": [
        (
            "takes its shape from the real filings plan 7 read, never their wording.\n"
            "\n",
            "takes its shape from the real filings plan 7 read, never their wording.\n"
            "\n"
            "``review(first)`` gives the overrides a reviewer records against the layer's first\n"
            "build: three acknowledged period gaps, Acme's release set by review, and two events\n"
            "retained unresolved.\n"
            "\n",
        ),
        (
            "from pathlib import Path\n"
            "\n"
            "from earnings_ingestion.events.acceptance import Convention\n"
            "from earnings_ingestion.events.synthetic import (\n",
            "from pathlib import Path\n"
            "from typing import TYPE_CHECKING\n"
            "\n"
            "from earnings_ingestion.cohort.records import OverrideCitation\n"
            "from earnings_ingestion.cohort.register import SEC_SOURCE_ID\n"
            "from earnings_ingestion.events.acceptance import Convention\n"
            "from earnings_ingestion.events.records import (\n"
            "    EventOverride,\n"
            "    EventOverrideKind,\n"
            "    EventReason,\n"
            ")\n"
            "from earnings_ingestion.events.synthetic import (\n",
        ),
        (
            "\n"
            "RETRIEVED = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)\n"
            "\n",
            "\n"
            "if TYPE_CHECKING:\n"
            "    from earnings_ingestion.events.build import EventBuild\n"
            "\n"
            "RETRIEVED = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)\n"
            "REVIEWER = \"Synthetic Reviewer\"\n"
            "REVIEWED_ON = date(2026, 9, 28)\n"
            "\n",
        ),
        (
            "    return store\n",
            "    return store\n"
            "\n"
            "\n"
            "def _override(\n"
            "    override_id: str, kind: EventOverrideKind, rationale: str, **fields\n"
            ") -> EventOverride:\n"
            "    return EventOverride(\n"
            "        override_id=override_id,\n"
            "        kind=kind,\n"
            "        **fields,\n"
            "        rationale=rationale,\n"
            "        reviewer=REVIEWER,\n"
            "        recorded_on=REVIEWED_ON,\n"
            "    )\n"
            "\n"
            "\n"
            "GAPS = {\n"
            "    \"gap-borealis\": (\n"
            "        \"period_gap:cik-0009990002:2025-03-31:2026-07-01\",\n"
            "        (\n"
            "            \"Borealis Air was acquired, and files nothing after its report for\"\n"
            "            \" 2025-03-31.\"\n"
            "        ),\n"
            "    ),\n"
            "    \"gap-corvid\": (\n"
            "        \"period_gap:cik-0009990003:2024-07-01:2024-12-31\",\n"
            "        (\n"
            "            \"Corvid Systems registered late in 2024; its first periodic report\"\n"
            "            \" covers 2024-12-31.\"\n"
            "        ),\n"
            "    ),\n"
            "    \"gap-eastfield\": (\n"
            "        \"period_gap:cik-0009990006:2025-03-31:2025-09-30\",\n"
            "        \"Eastfield Bank filed no 10-Q for the quarter ended 2025-06-30.\",\n"
            "    ),\n"
            "}\n"
            "\n"
            "\n"
            "def review(first: \"EventBuild\") -> tuple[EventOverride, ...]:\n"
            "    \"\"\"The overrides a reviewer records against the layer's first build, sorted.\"\"\"\n"
            "    digests = {finding.finding_id: finding.digest for finding in first.findings}\n"
            "    overrides = [\n"
            "        _override(\n"
            "            override_id,\n"
            "            EventOverrideKind.ACKNOWLEDGE,\n"
            "            rationale,\n"
            "            finding_id=finding_id,\n"
            "            finding_digest=digests[finding_id],\n"
            "        )\n"
            "        for override_id, (finding_id, rationale) in GAPS.items()\n"
            "    ]\n"
            "    (release,) = [\n"
            "        placed\n"
            "        for placed in first.issuers[\"cik-0009990001\"].releases\n"
            "        if placed.index.accepted == \"2025-03-20 16:05:00\"\n"
            "    ]\n"
            "    page = release.index_artifact\n"
            "    overrides.append(\n"
            "        _override(\n"
            "            \"release-acme-2025-02-28\",\n"
            "            EventOverrideKind.SET_RELEASE_FILING,\n"
            "            \"The 8-K of 2025-03-11 estimates a sale's effect on the quarter; the\"\n"
            "            \" 8-K of 2025-03-20 furnishes the quarter's results.\",\n"
            "            event_id=\"cik-0009990001:2025-02-28\",\n"
            "            accession=release.filing.accession,\n"
            "            citations=(\n"
            "                OverrideCitation(\n"
            "                    source_id=SEC_SOURCE_ID,\n"
            "                    url=page.url,\n"
            "                    artifact_sha256=page.artifact.content_sha256,\n"
            "                    locator=page.text.find(release.index.accepted),\n"
            "                ),\n"
            "            ),\n"
            "        )\n"
            "    )\n"
            "    overrides.append(\n"
            "        _override(\n"
            "            \"keep-borealis-same-day\",\n"
            "            EventOverrideKind.RETAIN_UNRESOLVED,\n"
            "            \"EDGAR alone cannot order a 07:00 release against a change before the\"\n"
            "            \" open on the same day (EV9).\",\n"
            "            event_id=\"cik-0009990002:2024-09-30\",\n"
            "            reason=EventReason.SAME_DAY_TRANSITION,\n"
            "        )\n"
            "    )\n"
            "    overrides.append(\n"
            "        _override(\n"
            "            \"keep-dynamo-no-release\",\n"
            "            EventOverrideKind.RETAIN_UNRESOLVED,\n"
            "            \"Dynamo Motors furnished no results under Item 2.02 for the quarter\"\n"
            "            \" ended 2025-06-27.\",\n"
            "            event_id=\"cik-0009990005:2025-06-27\",\n"
            "            reason=EventReason.NO_RELEASE_FILING,\n"
            "        )\n"
            "    )\n"
            "    return tuple(sorted(overrides, key=lambda override: override.override_id))\n",
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

Apply `task12-layer`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_build.py -q`

Expected: `15 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py packages/earnings-ingestion/tests/test_events_build.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1192 passed, 24 deselected`; `All checks passed!` and
`238 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/events/build.py packages/earnings-ingestion/src/earnings_ingestion/events/layer.py packages/earnings-ingestion/tests/test_events_build.py
git commit -m "feat(events): build the event manifest's rows, findings, and overrides"
```

---

### Task 13: The evidence record, and the freeze

This task implements S §The event manifest's evidence record and freezing, EV11, and
S §Verification (plan A), items 8, 9, and 11 for the event manifest.

- **The evidence record.** `evidence_of(build, manifest, saved)` cites, for each row:
  - the periodic report's submissions row, by JSON pointer: its accession, form,
    report date, and `acceptanceDateTime`;
  - its companyfacts labels, or `None` when they are unknown;
  - each candidate's and each amendment's index page, at its Accepted value;
  - the release filing's index page and Item 2.02 text. The item text is cited only
    when the release is one of the rule's candidates, because discovery fetches no
    other primary document;
  - the release's submissions row, at `acceptanceDateTime`.

  It also records each file read, with its convention and cross-checked rows, each
  page skipped, and three limitations (EV2, EV9, EV10). `check_evidence` verifies
  every citation again against a store. Task 15 uses it on the committed fixture.
- **The freeze** follows P6-14, as Stage 4's does.
  - It refuses while anything holds the freeze, and names each reason.
  - Identical content is the same version, and nothing is written, whatever the
    evidence says.
  - New content is the next version.
  - The evidence record is written before the manifest, so a manifest never
    appears without it, and neither file is ever replaced.
  - Loading rechecks the hash and the name.
- **The tests** freeze the reviewed layer, which has three acknowledged findings, and
  cover the following:
  - a submissions file fetched again a day later in true UTC changes the evidence
    and writes nothing, as the advisor's note to Task 12 required;
  - a companyfacts file fetched again with agreeing labels writes version 2;
  - a moved interval and a new policy name each change the hash, and a new
    `universe_version` alone does not (P7-2);
  - an unretained row, and a stale override, each hold the freeze on its own.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/evidence.py` and
  `events/freeze.py`.
- Modify, by appending: `docs/data-dictionary.md`, whose new section "Frozen event
  manifests" answers `EventManifestDefinition`'s pointer to it.
- Test (create): `packages/earnings-ingestion/tests/test_events_freeze.py`.

**Interfaces:**

- Consumes:
  - Task 12's `EventBuild`, `EventDetail`, `build_events`, and `review`;
  - Tasks 7 and 11's `Placed`, `SavedFile`, `SavedResponses`, `SyntheticStore`,
    `filings`, and `write_layer`;
  - Task 6's records and `content_hash`;
  - Stage 4's `Citation`, `ArtifactText`, `LocatorError`, `SEC_RIGHTS`, and
    `SEC_SOURCE_ID`;
  - `fetch.store.write_new`.
- Produces:
  - `events/evidence.py`:
    - `LIMITATIONS`;
    - `evidence_of(build, manifest, saved) -> EventEvidence`;
    - `check_evidence(evidence, store) -> tuple[str, ...]`, which returns the
      problems, or none;
  - `events/freeze.py`:
    - `EventFreezeRefused(build)`, with `.reasons`;
    - `FrozenEvents(manifest, path, evidence_path, created)`;
    - `manifest_path(directory, version)` and `evidence_path(directory, version)`;
    - `serialize(record) -> bytes`;
    - `load_event_manifest(path)`, `load_event_evidence(path)`, and
      `frozen_event_manifests(directory)`;
    - `freeze_events(build, saved, directory, *, now) -> FrozenEvents`. Tasks 14,
      15, and 17 call it.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_freeze.py`:

```python
"""The evidence record and the freeze (the Stage 5 spec, §The event manifest; EV11,
P6-14), over the synthetic event layer and Stage 4's synthetic cohort.
"""

import shutil
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.build import EventBuild, build_events
from earnings_ingestion.events.evidence import check_evidence, evidence_of
from earnings_ingestion.events.freeze import (
    EventFreezeRefused,
    freeze_events,
    load_event_evidence,
    load_event_manifest,
)
from earnings_ingestion.events.layer import (
    ACME,
    CORVID,
    REPORTS,
    filings,
    review,
    write_layer,
)
from earnings_ingestion.events.records import (
    EventOverridesFile,
    content_hash,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.synthetic import SyntheticStore
from earnings_ingestion.sec.urls import filing_index_url, submissions_url

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "tests" / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
NOW = datetime(2026, 9, 28, 18, 0, tzinfo=UTC)
LATER = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def universe():
    return load_manifest(COHORT)


@pytest.fixture
def layer(tmp_path) -> SyntheticStore:
    return write_layer(tmp_path / "data" / "raw" / "events", tmp_path)


def build(universe, layer: SyntheticStore, overrides=()) -> EventBuild:
    return build_events(
        universe,
        SavedResponses(layer.store),
        EventOverridesFile(schema_version=1, overrides=overrides),
        corpus_id="djia-synthetic",
    )


def reviewed(universe, layer: SyntheticStore) -> EventBuild:
    return build(universe, layer, review(build(universe, layer)))


def freeze(built: EventBuild, layer: SyntheticStore, directory: Path):
    return freeze_events(built, SavedResponses(layer.store), directory, now=NOW)


def test_the_freeze_refuses_and_names_each_reason(universe, layer, tmp_path) -> None:
    directory = tmp_path / "corpus"
    with pytest.raises(EventFreezeRefused) as refused:
        freeze(build(universe, layer), layer, directory)
    reasons = refused.value.reasons
    assert [reason.split(": ")[0] for reason in reasons] == [
        "period_gap:cik-0009990002:2025-03-31:2026-07-01",
        "period_gap:cik-0009990003:2024-07-01:2024-12-31",
        "period_gap:cik-0009990006:2025-03-31:2025-09-30",
        "cik-0009990001:2025-02-28",
        "cik-0009990002:2024-09-30",
        "cik-0009990005:2025-06-27",
    ]
    assert reasons[3].endswith("several_release_filings, not retained")
    assert not directory.exists()


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("drop", "cik-0009990005:2025-06-27: no_release_filing, not retained"),
        ("stale", "keep-eligible: a stale override"),
    ],
)
def test_an_unretained_row_or_a_stale_override_alone_holds_the_freeze(
    universe, layer, tmp_path, change, reason
) -> None:
    overrides = review(build(universe, layer))
    if change == "drop":
        overrides = tuple(
            o for o in overrides if o.override_id != "keep-dynamo-no-release"
        )
    else:
        (kept,) = [o for o in overrides if o.override_id == "keep-dynamo-no-release"]
        extra = kept.model_copy(
            update={
                "override_id": "keep-eligible",
                "event_id": "cik-0009990001:2024-08-31",
            }
        )
        overrides = (*overrides, extra)
    with pytest.raises(EventFreezeRefused) as refused:
        freeze(build(universe, layer, overrides), layer, tmp_path / "corpus")
    assert refused.value.reasons == (reason,)


def test_a_reviewed_build_freezes_with_evidence_that_verifies(
    universe, layer, tmp_path
) -> None:
    frozen = freeze(reviewed(universe, layer), layer, tmp_path / "corpus")
    assert frozen.created
    assert (frozen.path.name, frozen.evidence_path.name) == (
        "events-v1.json",
        "events-v1.evidence.json",
    )
    assert load_event_manifest(frozen.path) == frozen.manifest
    evidence = load_event_evidence(frozen.evidence_path)
    assert evidence.event_manifest_hash == frozen.manifest.definition.content_hash
    assert check_evidence(evidence, layer.store) == ()
    assert len(evidence.events) == 32
    assert [(f.convention, f.rows_cross_checked) for f in evidence.files][:2] == [
        (Convention.EASTERN_DIGITS, 9),
        (Convention.EASTERN_DIGITS, 5),
    ]
    assert len(evidence.files) == 6
    assert len(evidence.skipped_pages) == 1
    events = {cited.event_id: cited for cited in evidence.events}
    acme = events["cik-0009990001:2025-02-28"]
    (release,) = [f for f, _ in filings(ACME) if f.accepted == "2025-03-20 16:05:00"]
    assert acme.release.url == filing_index_url(ACME.cik, release.accession)
    assert acme.item_text is not None
    assert len(acme.candidates) == 2
    assert events["cik-0009990003:2025-06-30"].labels is None
    none = events["cik-0009990005:2025-06-27"]
    assert (none.release, none.item_text, none.cross_check) == (None, None, None)
    assert events["cik-0009990002:2024-09-30"].amendments[0].url.endswith("-index.htm")


def test_identical_content_is_the_same_version(universe, layer, tmp_path) -> None:
    built = reviewed(universe, layer)
    first = freeze(built, layer, tmp_path / "corpus")
    again = freeze(built, layer, tmp_path / "corpus")
    assert (again.created, again.path) == (False, first.path)
    assert len(list((tmp_path / "corpus").iterdir())) == 2


def test_a_refetch_with_the_same_facts_writes_nothing(
    universe, layer, tmp_path
) -> None:
    """Acme's submissions file, fetched again a day later in true UTC: the evidence
    would change, and the manifest does not (EV11)."""
    before = reviewed(universe, layer)
    frozen = freeze(before, layer, tmp_path / "corpus")
    again = SyntheticStore(layer.store.root, layer.store.repo, LATER)
    again.submissions(
        ACME.cik,
        ACME.name,
        [filing for filing, _ in filings(ACME)],
        convention=Convention.UTC,
    )
    after = build(universe, again, before.overrides)
    assert [f.resolved_by for f in after.findings if f.resolved_by]
    assert after.content_hash == before.content_hash
    evidence = evidence_of(after, frozen.manifest, SavedResponses(again.store))
    (acme,) = [f for f in evidence.files if f.url == submissions_url(ACME.cik)]
    assert (acme.convention, acme.retrieved_at) == (Convention.UTC, LATER)
    assert not freeze(after, again, tmp_path / "corpus").created
    assert len(list((tmp_path / "corpus").iterdir())) == 2


def test_a_changed_fact_writes_the_next_version(universe, layer, tmp_path) -> None:
    """Corvid's companyfacts, fetched again with agreeing labels, changes a row."""
    before = reviewed(universe, layer)
    first = freeze(before, layer, tmp_path / "corpus")
    again = SyntheticStore(layer.store.root, layer.store.repo, LATER)
    listed = filings(CORVID)
    facts = [
        (filing.accession, report.labels[0][0], report.labels[0][1])
        for filing, report in listed
        if report in REPORTS[CORVID]
    ]
    again.companyfacts(CORVID.cik, CORVID.name, facts)
    frozen = freeze(
        build(universe, again, before.overrides), again, tmp_path / "corpus"
    )
    assert frozen.created
    assert frozen.manifest.definition.event_manifest_version == 2
    rows = {row.event_id: row for row in frozen.manifest.rows}
    corvid = rows["cik-0009990003:2025-06-30"]
    assert (corvid.reported_fiscal_year, corvid.reported_fiscal_quarter) == (2025, "Q2")
    assert load_event_manifest(first.path) == first.manifest


def test_loading_rechecks_the_hash_and_the_name(universe, layer, tmp_path) -> None:
    frozen = freeze(reviewed(universe, layer), layer, tmp_path / "corpus")
    renamed = tmp_path / "events-v2.json"
    shutil.copy(frozen.path, renamed)
    with pytest.raises(ValueError, match="holds version 1"):
        load_event_manifest(renamed)
    changed = tmp_path / "events-v1.json"
    text = frozen.path.read_text().replace('"retained": true', '"retained": false', 1)
    changed.write_text(text)
    with pytest.raises(ValueError, match="does not hash"):
        load_event_manifest(changed)


def test_a_changed_interval_or_policy_changes_the_hash_and_a_version_alone_does_not(
    universe, layer
) -> None:
    """P-VF and P7-2: the universe's operative facts and the policies are hashed;
    its version is not."""
    built = reviewed(universe, layer)
    intervals = [
        interval.model_copy(update={"effective_from": date(2024, 11, 9)})
        if interval.security_id == "corvid-common"
        else interval
        for interval in universe.intervals
    ]
    moved = universe.model_copy(update={"intervals": tuple(intervals)})
    renumbered = universe.model_copy(
        update={
            "definition": universe.definition.model_copy(update={"universe_version": 2})
        }
    )
    overrides = built.overrides
    assert build(universe, layer, overrides).content_hash == built.content_hash
    assert build(renumbered, layer, overrides).content_hash == built.content_hash
    assert build(moved, layer, overrides).content_hash != built.content_hash
    manifest = built.manifest(1, NOW)
    policy = manifest.definition.model_copy(
        update={"discovery_policy_version": "release-id/2"}
    )
    assert content_hash(manifest.model_copy(update={"definition": policy})) != (
        manifest.definition.content_hash
    )
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_freeze.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_freeze.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.evidence'`.

- [x] **Step 3: Write the evidence record and the freeze**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/evidence.py`:

```python
"""The evidence record beside a frozen event manifest (the Stage 5 spec, §The event
manifest; EV11).

``events-v<N>.evidence.json`` cites what each row rests on, in Stage 4's
``Citation`` and ``EvidenceLocator``:

- the periodic report's submissions row, and its companyfacts labels;
- each candidate's index page, and each amendment's, at its Accepted value;
- the release filing's index page at its Accepted value, and its Item 2.02 text;
- the release's submissions row at ``acceptanceDateTime``, its cross-check.

It also records each submissions file and older page the build read, with its
convention, and each older page skipped by its dates. Every citation carries its
``retrieved_at``. The record lies outside the manifest's hash, so a re-fetch changes
it and nothing else. It holds URLs, hashes, and locators, never source text (P6-3).

``check_evidence`` verifies every citation again against a store.
"""

from earnings_ingestion.cohort.locators import ArtifactText, LocatorError
from earnings_ingestion.cohort.records import Citation
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.build import EventBuild, EventDetail
from earnings_ingestion.events.filings import Placed, SavedFile
from earnings_ingestion.events.records import (
    EventCitations,
    EventEvidence,
    EventManifest,
    FileEvidence,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.data import Filing
from earnings_ingestion.sec.urls import companyfacts_url

LIMITATIONS = (
    (
        "first_publication_time is the release filing's EDGAR acceptance time, an"
        " upper bound on when its results first became public: a newswire release"
        " can come first (EV9)"
    ),
    (
        "Each acceptance time is its index page's Accepted value, read as Eastern"
        " wall time; submissions' acceptanceDateTime is only a cross-check, in the"
        " convention each file's cross-checked rows establish (EV10)"
    ),
    (
        "release-id/1 reads each candidate's primary document only; no exhibit was"
        " fetched before the freeze (EV2)"
    ),
)


def _row(file: SavedFile, filing: Filing, *columns: str) -> Citation:
    """A submissions row's values, by JSON pointer."""
    text = file.artifact.text
    return file.artifact.cite(*(text.pointer(filing.pointer(c)) for c in columns))


def _accepted(placed: Placed) -> Citation:
    """A filing's index page, at its Accepted value."""
    page = placed.index_artifact
    return page.cite(page.text.find(placed.index.accepted))


def _event(detail: EventDetail, saved: SavedResponses) -> EventCitations:
    slot, found, release = detail.slot, detail.identification, detail.release
    labels = None
    if slot.labels is not None:
        facts = saved.get(companyfacts_url(slot.cik))
        labels = facts.cite(facts.text.pointer(slot.labels.pointer))
    item_text = None
    if release is not None:
        for candidate in found.candidates:
            if candidate.placed.filing.accession == release.filing.accession:
                item_text = candidate.item_text()
    periodic = slot.periodic
    return EventCitations(
        event_id=slot.event_id,
        periodic_row=_row(
            periodic.file,
            periodic.filing,
            "accessionNumber",
            "form",
            "reportDate",
            "acceptanceDateTime",
        ),
        labels=labels,
        candidates=tuple(_accepted(c.placed) for c in found.candidates),
        amendments=tuple(_accepted(placed) for placed in found.amendments),
        release=None if release is None else _accepted(release),
        item_text=item_text,
        cross_check=(
            None
            if release is None
            else _row(release.file, release.filing, "acceptanceDateTime")
        ),
    )


def evidence_of(
    build: EventBuild, manifest: EventManifest, saved: SavedResponses
) -> EventEvidence:
    """The evidence record of ``manifest``, the freeze of ``build``."""
    files, skipped = {}, {}
    for filings in build.issuers.values():
        for file in filings.files:
            artifact = file.artifact
            files[artifact.url] = FileEvidence(
                url=artifact.url,
                sha256=artifact.artifact.content_sha256,
                retrieved_at=artifact.retrieved_at,
                convention=file.survey.convention,
                rows_cross_checked=len(file.survey.checks),
            )
        for page in filings.skipped:
            skipped[page.url] = page
    definition = manifest.definition
    return EventEvidence(
        corpus_id=definition.corpus_id,
        event_manifest_version=definition.event_manifest_version,
        event_manifest_hash=definition.content_hash,
        limitations=LIMITATIONS,
        files=tuple(files[url] for url in sorted(files)),
        skipped_pages=tuple(skipped[url] for url in sorted(skipped)),
        events=tuple(
            _event(build.details[row.event_id], saved) for row in manifest.rows
        ),
    )


def _citations(events: EventCitations) -> list[tuple[str, Citation]]:
    single = [
        ("periodic_row", events.periodic_row),
        ("labels", events.labels),
        ("release", events.release),
        ("item_text", events.item_text),
        ("cross_check", events.cross_check),
    ]
    listed = [("candidates", c) for c in events.candidates]
    listed += [("amendments", c) for c in events.amendments]
    return [(name, c) for name, c in [*single, *listed] if c is not None]


def check_evidence(evidence: EventEvidence, store: ArtifactStore) -> tuple[str, ...]:
    """Every citation, and every file read, checked against ``store``'s saved bytes;
    the problems found, or none."""
    problems = []

    def read(sha256: str) -> ArtifactText | None:
        try:
            stored = store.get(
                SEC_SOURCE_ID,
                sha256,
                rights_status=SEC_RIGHTS.rights_status,
                rights_basis=SEC_RIGHTS.rights_basis,
            )
        except (FileNotFoundError, ValueError) as exc:
            problems.append(str(exc))
            return None
        return ArtifactText(stored.body, stored.ref.media_type)

    for file in evidence.files:
        read(file.sha256)
    for events in evidence.events:
        for name, citation in _citations(events):
            text = read(citation.artifact.content_sha256)
            if text is None:
                continue
            for locator in citation.locators:
                try:
                    text.verify(locator)
                except LocatorError as exc:
                    problems.append(f"{events.event_id} {name}: {exc}")
    return tuple(problems)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/evidence.py`.

Create `packages/earnings-ingestion/src/earnings_ingestion/events/freeze.py`:

```python
"""Freeze the event manifest, with its evidence record beside it (the Stage 5 spec,
§The event manifest; P6-14).

- Freezing refuses while anything holds the freeze, and names each: an unanswered
  blocking finding, a stale override, and an ``ambiguous`` row no override retains.
- Content that matches a frozen manifest *is* that version, and nothing is written,
  whatever the evidence says: a re-fetch with the same facts writes nothing. New
  content is the next version.
- ``events-v<N>.evidence.json`` is written first and ``events-v<N>.json`` second, each
  to a temporary file linked into place: a manifest never appears without its
  evidence, and neither is ever replaced.
- Loading reads the committed JSON alone and rechecks the content hash and the name.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from earnings_ingestion.events.build import EventBuild
from earnings_ingestion.events.evidence import evidence_of
from earnings_ingestion.events.records import (
    EventEvidence,
    EventManifest,
    content_hash,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.store import write_new


class EventFreezeRefused(ValueError):
    """The build still holds the freeze; the message names each reason."""

    def __init__(self, build: EventBuild) -> None:
        self.reasons = tuple(
            [f"{f.finding_id}: {f.detail}" for f in build.blocking]
            + [f"{o}: a stale override" for o in build.stale_overrides]
            + [
                f"{row.event_id}: {row.eligibility_reason}, not retained"
                for row in build.unretained
            ]
        )
        super().__init__("; ".join(self.reasons))


@dataclass(frozen=True)
class FrozenEvents:
    manifest: EventManifest
    path: Path
    evidence_path: Path
    created: bool
    """False when an existing version already held this content."""


def manifest_path(directory: Path, version: int) -> Path:
    return directory / f"events-v{version}.json"


def evidence_path(directory: Path, version: int) -> Path:
    return directory / f"events-v{version}.evidence.json"


def serialize(record: BaseModel) -> bytes:
    """Indented JSON with sorted keys, for a readable diff between versions."""
    data = record.model_dump(mode="json")
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False)
    return f"{text}\n".encode()


def load_event_manifest(path: Path) -> EventManifest:
    """A committed event manifest, refused if its name or content hash disagrees."""
    manifest = EventManifest.model_validate_json(path.read_bytes())
    definition = manifest.definition
    if content_hash(manifest) != definition.content_hash:
        raise ValueError(f"{path} does not hash to its content_hash")
    if path.name != manifest_path(path.parent, definition.event_manifest_version).name:
        raise ValueError(f"{path} holds version {definition.event_manifest_version}")
    return manifest


def load_event_evidence(path: Path) -> EventEvidence:
    """A committed evidence record, refused if its name disagrees."""
    evidence = EventEvidence.model_validate_json(path.read_bytes())
    if path.name != evidence_path(path.parent, evidence.event_manifest_version).name:
        raise ValueError(f"{path} holds version {evidence.event_manifest_version}")
    return evidence


def frozen_event_manifests(directory: Path) -> list[EventManifest]:
    """Every frozen version in ``directory``, oldest first."""
    manifests = [
        load_event_manifest(path)
        for path in directory.glob("events-v*.json")
        if not path.name.endswith(".evidence.json")
    ]
    return sorted(manifests, key=lambda m: m.definition.event_manifest_version)


def freeze_events(
    build: EventBuild, saved: SavedResponses, directory: Path, *, now: datetime
) -> FrozenEvents:
    """Freeze ``build`` into ``directory``, or return the version that holds it."""
    if build.holds_freeze:
        raise EventFreezeRefused(build)
    existing = frozen_event_manifests(directory)
    for manifest in existing:
        if manifest.definition.content_hash == build.content_hash:
            version = manifest.definition.event_manifest_version
            return FrozenEvents(
                manifest=manifest,
                path=manifest_path(directory, version),
                evidence_path=evidence_path(directory, version),
                created=False,
            )
    version = 1 + max(
        (m.definition.event_manifest_version for m in existing), default=0
    )
    manifest = build.manifest(version, now)
    evidence = evidence_of(build, manifest, saved)
    directory.mkdir(parents=True, exist_ok=True)
    write_new(evidence_path(directory, version), serialize(evidence))
    write_new(manifest_path(directory, version), serialize(manifest))
    return FrozenEvents(
        manifest=manifest,
        path=manifest_path(directory, version),
        evidence_path=evidence_path(directory, version),
        created=True,
    )
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/freeze.py`.

Append to `docs/data-dictionary.md`:

```markdown

## Frozen event manifests

- **Where.** `config/corpus/<corpus_id>/events-v<N>.json` holds one `EventManifest`,
  and `events-v<N>.evidence.json` beside it holds that version's `EventEvidence`. Each
  is indented JSON with sorted keys, written once and never replaced, and the evidence
  record is written first. The synthetic corpus's are in `tests/fixtures/events/`.
- **The content hash.** `content_hash` covers the canonical JSON of the definition,
  less `event_manifest_version`, `universe_version`, `content_hash`, and `created_at`,
  with the rows, the findings, and the overrides. Identical content keeps its version,
  whatever its evidence record would say; new content takes the next.
- **Reading.** `earnings_ingestion.events.freeze.load_event_manifest` rechecks that
  hash and the file's name, and `load_event_evidence` the evidence record's name.
  `earnings_ingestion.events.evidence.check_evidence` verifies every citation against
  a store's saved bytes.
- **Saved artifacts.** Discovery's are under `data/raw/events/`, which is never
  committed; the synthetic layer's are under `tests/fixtures/events/raw/`.
```

Extract it with `python3 /tmp/plan7-extract.py docs/data-dictionary.md 2`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_freeze.py -q`

Expected: `9 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py packages/earnings-ingestion/tests/test_events_freeze.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1201 passed, 24 deselected`; `All checks passed!` and
`241 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-ingestion/src/earnings_ingestion/events/evidence.py packages/earnings-ingestion/src/earnings_ingestion/events/freeze.py packages/earnings-ingestion/tests/test_events_freeze.py
git commit -m "feat(events): freeze the event manifest with its evidence record"
```

---

### Task 14: The pilot, `djia-pilot/1`

This task implements S §Pilot selection (step 5), SV10, and SV11 for the pilot, with
the pilot manifest's freeze and its chain. P7-20 records its one reading: the
universe manifest is the policy's second input.

- **The records** join `events/records.py`:
  - `SelectionReason` and `TransitionKind`;
  - `PilotRow`, `MembershipTransition`, `PilotDefinition`, and `PilotManifest`,
    whose rows run in `selection_order` from 1, name each event once, and number
    exactly `target`;
  - `pilot_content_hash`. It leaves out what the event manifest's hash leaves out:
    the record's own version, `universe_version` (P7-2), the hash, and the creation
    time. `event_manifest_version` stays in, because within one corpus directory an
    event manifest's version and content go together, so it re-versions nothing.
- **The inputs.** S says `djia-pilot/1` "reads only a frozen event manifest" (EV8),
  but step 2's transitions live in the universe's intervals, which no event row
  carries. So `select_pilot(events, universe)` also reads the universe manifest the
  event manifest read, and refuses unless `operative_hash(universe)` equals the
  recorded `universe_operative_hash`, and unless the universe names `djia-pilot/1`
  (P7-20). No acquisition, parse, or later outcome is an input.
- **The transitions.** An issuer's membership is the union of its securities'
  intervals, by day (`MembershipInterval.contains`).
  - An entry is a start, not an `anchor_snapshot`, whose day before no interval of
    the issuer holds. An exit is an end whose day no interval holds.
  - So a second security joining a member issuer is neither, and neither is a
    same-day handoff between two of an issuer's securities. A gap makes an exit and
    an entry.
  - Those dated in `[period_end_start, public_information_cutoff]`, both ends
    included, are in scope.
  - The member side of an entry is on or after its date, and of an exit on or before
    it. Eligibility has already placed each release against the bound's timing: an
    `eligible` release on a bound's own date is always on the member side.
- **The steps.** `select(rows, transitions, seed, *, start, stop)` is the pure core.
  It takes the rows in any order, and runs the guards and the five steps exactly as
  S states them. A refusal raises `PilotRefused` with its `PilotRefusal`, and nothing
  is written.
- **The freeze** follows the event manifest's (P6-14): identical content is the same
  version, and new content is the next, `pilot-v<N>.json`, beside the event manifest
  it names.
- **Loading** rechecks the chain, which plan B's `events acquire` gate relies on
  (S §Plan B, Gate). The checks are:
  - the pilot's hash and file name;
  - the event manifest it names, loaded from the same directory, whose content hash
    must be `eligible_event_manifest_hash`;
  - the universe's operative hash, computed again from the universe manifest, which
    must equal the pilot's and the event manifest's;
  - the seed, recomputed from its inputs;
  - that every row is an `eligible` event of that manifest.

  `freeze_pilot` runs the same check before it writes.

**Plan-time check.** Read-only, over the committed v1 manifest, `transitions` gives
exactly S's six, all `before_open`:

- 2024-11-08: Intel's and Dow's exits, and Sherwin-Williams' and NVIDIA's entries;
- 2026-06-29: Verizon's exit and Alphabet's entry.

v1 has no handoff and no issuer with two securities, and its anchor, 2024-06-24, is
out of scope. The synthetic cohort gives three transitions:

- Borealis's exit on 2024-11-08, which has no eligible event and is reported;
- Corvid's entry on 2024-11-08;
- Eastfield's exit on 2026-06-22.

Dynamo's class B, joining a member issuer, is not a transition.

**The tests.**

- **Direct event rows** (S §The synthetic event layer, selection-level fixtures) cover:
  - exactly 40;
  - both sides of each guard, 19/20, 39/40, and 40/41 issuers;
  - `mandatory_overflow`;
  - `quarter_uncovered`;
  - a shuffle that gives byte-identical pilot bytes.

  Their fixture gives two issuers both an entry and an exit, with different targets.
  Step 1 takes one event per issuer, so step 2 must add a `membership_boundary` row
  whatever the seed gives (SV10).
- **`obeys_the_steps`** replays a pilot row by row. It checks that each row of steps
  1, 3, and 5 is the choice its rule makes at that moment, with ties broken by `h`,
  and that the steps come in order.
- **On the synthetic layer:** the transitions, with a handoff, a gap, the cutoff,
  and an anchor moved into scope; the underfilled pilot; the freeze; seven tamperings
  of the chain; and SV11.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py`.
- Modify, by exact replacement: `packages/earnings-ingestion/src/earnings_ingestion/events/records.py`
  and `tests/contracts/test_data_dictionary.py`.
- Modify, by appending: `docs/data-dictionary.md`.
- Test (create): `packages/earnings-ingestion/tests/test_events_pilot.py`.

**Interfaces:**

- Consumes:
  - Task 3's `operative_hash`;
  - Task 5's `EASTERN`;
  - Task 6's records and `content_hash`;
  - Task 10's `span`;
  - Tasks 11 and 12's `write_layer`, `review`, `build_events`, and `EPOCH`;
  - Task 13's `freeze_events`, `load_event_manifest`, `manifest_path`, and
    `serialize`;
  - Stage 4's `digest`, `load_manifest`, `UniverseManifest`, and `write_new`.
- Produces, in `events/records.py`:
  - `SelectionReason` and `TransitionKind`;
  - `PilotRow`, `MembershipTransition`, `PilotDefinition`, and `PilotManifest`;
  - `PILOT_UNHASHED`, and `pilot_content_hash(manifest: PilotManifest) -> str`.
- Produces, in `events/pilot.py`:
  - the constants `PILOT_POLICY = "djia-pilot/1"`, `PILOT_SIZE = 40`, and
    `MINIMUM_EVENTS = 20`;
  - `PilotRefusal`, and `PilotRefused(reason, detail)`, with `.reason` and
    `.detail`;
  - `pilot_seed(event_manifest_hash, universe_operative_hash, policy=PILOT_POLICY) -> str`;
  - `ordering(seed) -> Callable[[str], str]`, which is `h`;
  - `quarter(day) -> str` and `quarters(start, stop) -> tuple[str, ...]`;
  - `transitions(universe) -> tuple[MembershipTransition, ...]`;
  - `Selection(target, underfilled, rows, unmatched_transitions)`, and
    `select(rows, transitions, seed, *, start, stop) -> Selection`;
  - `Pilot(events, universe_version, seed, selection)`, with
    `manifest(version, created_at)` and `content_hash`;
  - `select_pilot(events: EventManifest, universe: UniverseManifest) -> Pilot`;
  - `FrozenPilot(manifest, path, created)` and `pilot_path(directory, version)`;
  - `check_chain(manifest, directory, universe) -> EventManifest`;
  - `load_pilot(path, universe) -> PilotManifest` and
    `frozen_pilots(directory, universe)`;
  - `freeze_pilot(pilot, universe, directory, *, now) -> FrozenPilot`. Tasks 15 and
    17 call it.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_pilot.py`:

```python
"""djia-pilot/1 (the Stage 5 spec, §Pilot selection; SV10 to SV12): the selection
paths on event rows built directly, and the underfilled pilot of the synthetic event
layer, frozen beside its event manifest and loaded with its chain."""

import random
import shutil
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.identity import operative_hash
from earnings_ingestion.cohort.records import BoundTiming, UniverseManifest
from earnings_ingestion.events.build import build_events
from earnings_ingestion.events.freeze import (
    freeze_events,
    load_event_manifest,
    serialize,
)
from earnings_ingestion.events.layer import review, write_layer
from earnings_ingestion.events.pilot import (
    Pilot,
    PilotRefusal,
    PilotRefused,
    freeze_pilot,
    load_pilot,
    ordering,
    pilot_path,
    pilot_seed,
    quarter,
    quarters,
    select,
    select_pilot,
    transitions,
)
from earnings_ingestion.events.records import (
    EventManifest,
    EventManifestDefinition,
    EventOverridesFile,
    EventReason,
    EventRow,
    EventStatus,
    IdentificationMethod,
    MembershipTransition,
    SelectionReason,
    TransitionKind,
    content_hash,
    pilot_content_hash,
)
from earnings_ingestion.events.saved import SavedResponses

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "tests" / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
NOW = datetime(2026, 9, 28, 18, 0, tzinfo=UTC)
START, STOP = date(2024, 7, 1), date(2026, 7, 1)
ENDS = (
    date(2024, 9, 30),
    date(2024, 12, 31),
    date(2025, 3, 31),
    date(2025, 6, 30),
    date(2025, 9, 30),
    date(2025, 12, 31),
    date(2026, 3, 31),
    date(2026, 6, 30),
)
SEED = pilot_seed("a" * 64, "b" * 64)
ENTRY, EXIT = TransitionKind.ENTRY, TransitionKind.EXIT
BOUNDARY = SelectionReason.MEMBERSHIP_BOUNDARY
ELIGIBLE = EventStatus.ELIGIBLE


def event(issuer: int, period_end: date) -> EventRow:
    """An eligible event, published 25 days after its period end."""
    cik = f"{issuer:010d}"
    published = datetime.combine(period_end + timedelta(days=25), time(20, 5), UTC)
    release = f"{cik}-{period_end:%y}-{period_end.month:06d}"
    return EventRow(
        event_id=f"cik-{cik}:{period_end.isoformat()}",
        issuer_id=f"cik-{cik}",
        cik=cik,
        period_end=period_end,
        reported_fiscal_year=None,
        reported_fiscal_quarter=None,
        periodic_accession=f"{cik}-{period_end:%y}-{period_end.month + 100:06d}",
        periodic_form="10-Q",
        release_accession=release,
        candidate_accessions=(release,),
        identification_method=IdentificationMethod.STATED_PERIOD,
        filing_acceptance_time=published,
        first_publication_time=published,
        source_timezone="America/New_York",
        first_publication_source_id="sec-edgar",
        membership_assertion_id=f"added-{issuer}",
        eligibility_status=EventStatus.ELIGIBLE,
        eligibility_reason=EventReason.MEMBER_AT_PUBLICATION,
        retained=False,
        override_ids=(),
    )


def ineligible(issuer: int, period_end: date) -> EventRow:
    return event(issuer, period_end).model_copy(
        update={
            "eligibility_status": EventStatus.INELIGIBLE,
            "eligibility_reason": EventReason.NOT_MEMBER_AT_PUBLICATION,
        }
    )


def transition(issuer: int, kind: TransitionKind, day: date) -> MembershipTransition:
    return MembershipTransition(
        issuer_id=f"cik-{issuer:010d}",
        kind=kind,
        effective_date=day,
        assertion_ids=(f"{kind}-{issuer}",),
    )


def forty() -> tuple[list[EventRow], list[MembershipTransition]]:
    """76 eligible events of ten issuers, and eight ineligible ones of an eleventh.
    Issuers 1 and 2 enter on 2024-10-01 and leave on 2026-03-01, so their events run
    from 2024Q3 through 2025Q4, and each one's two transitions have different
    targets: step 1 takes one event per issuer, so step 2 must add a row."""
    rows = [event(n, end) for n in (1, 2) for end in ENDS[:6]]
    rows += [event(n, end) for n in range(3, 11) for end in ENDS]
    rows += [ineligible(11, end) for end in ENDS]
    moves = [
        transition(n, kind, day)
        for n in (1, 2)
        for kind, day in ((ENTRY, date(2024, 10, 1)), (EXIT, date(2026, 3, 1)))
    ]
    return rows, moves


def run(rows, moves=()):
    return select(rows, moves, SEED, start=START, stop=STOP)


STEPS = list(SelectionReason)


def obeys_the_steps(events: list[EventRow], rows, seed: str) -> None:
    """Replay the pilot: the steps come in order, and each row of steps 1, 3, and 5
    is the choice its rule makes at that moment, with ties broken by ``h``."""
    h = ordering(seed)
    eligible = {e.event_id: e for e in events if e.eligibility_status is ELIGIBLE}
    reasons = [row.selection_reason for row in rows]
    assert reasons == sorted(reasons, key=STEPS.index)
    covered = [
        eligible[row.event_id].issuer_id
        for row in rows
        if row.selection_reason is SelectionReason.ISSUER_COVERAGE
    ]
    assert covered == sorted({e.issuer_id for e in eligible.values()}, key=h)
    taken: list[EventRow] = []
    for row in rows:
        chosen = eligible[row.event_id]
        per_quarter = Counter(quarter(e.period_end) for e in taken)
        per_issuer = Counter(e.issuer_id for e in taken)
        left = [e for e in eligible.values() if e not in taken]

        def distance(event: EventRow) -> int:
            return min(
                abs((event.period_end - e.period_end).days)
                for e in taken
                if e.issuer_id == event.issuer_id
            )

        expected = chosen
        if row.selection_reason is SelectionReason.ISSUER_COVERAGE:
            own = [e for e in left if e.issuer_id == chosen.issuer_id]
            expected = min(
                own, key=lambda e: (per_quarter[quarter(e.period_end)], h(e.event_id))
            )
        elif row.selection_reason is SelectionReason.QUARTER_COVERAGE:
            earlier = [
                q for q in quarters(START, STOP) if q < quarter(chosen.period_end)
            ]
            assert all(per_quarter[q] for q in earlier)
            assert per_quarter[quarter(chosen.period_end)] == 0
            same = [
                e for e in left if quarter(e.period_end) == quarter(chosen.period_end)
            ]
            expected = min(same, key=lambda e: (per_issuer[e.issuer_id], h(e.event_id)))
        elif row.selection_reason is SelectionReason.LONGITUDINAL_FILL:
            fewest = min(per_issuer[e.issuer_id] for e in left)
            pool = [e for e in left if per_issuer[e.issuer_id] == fewest]
            expected = min(pool, key=lambda e: (-distance(e), h(e.event_id)))
        assert chosen == expected
        taken.append(chosen)


def test_the_seed_is_the_hash_of_its_three_inputs() -> None:
    canonical = (
        '{"eligible_event_manifest_hash":"' + "a" * 64 + '",'
        '"selection_policy_version":"djia-pilot/1",'
        '"universe_operative_hash":"' + "b" * 64 + '"}'
    )
    assert SEED == sha256_hex(canonical.encode())
    assert ordering(SEED)("cik-0000000001") == sha256_hex(
        f"{SEED}:cik-0000000001".encode()
    )
    assert quarters(START, STOP) == (
        "2024Q3",
        "2024Q4",
        "2025Q1",
        "2025Q2",
        "2025Q3",
        "2025Q4",
        "2026Q1",
        "2026Q2",
    )


def test_with_40_or_more_eligible_events_the_pilot_holds_exactly_40() -> None:
    rows, moves = forty()
    chosen = run(rows, moves)
    assert (chosen.target, chosen.underfilled, len(chosen.rows)) == (40, False, 40)
    assert [row.selection_order for row in chosen.rows] == list(range(1, 41))
    events = {row.event_id: row for row in rows}
    picked = [events[row.event_id] for row in chosen.rows]
    assert {row.issuer_id for row in picked} == {f"cik-{n:010d}" for n in range(1, 11)}
    assert {quarter(row.period_end) for row in picked} == set(quarters(START, STOP))
    obeys_the_steps(rows, chosen.rows, SEED)
    dates = {
        f"cik-{n:010d}:{end}": day
        for n in (1, 2)
        for end, day in (
            ("2024-09-30", date(2024, 10, 1)),
            ("2025-12-31", date(2026, 3, 1)),
        )
    }
    reasons = {row.event_id: row.selection_reason for row in chosen.rows}
    for n in (1, 2):
        ends = [f"cik-{n:010d}:2024-09-30", f"cik-{n:010d}:2025-12-31"]
        assert BOUNDARY in {reasons[target] for target in ends}
    added = [e for e, reason in reasons.items() if reason is BOUNDARY]
    h = ordering(SEED)
    assert added == sorted(added, key=lambda e: (dates[e], h(e)))
    assert Counter(reasons.values()) == {
        SelectionReason.ISSUER_COVERAGE: 10,
        SelectionReason.MEMBERSHIP_BOUNDARY: 4,
        SelectionReason.LONGITUDINAL_FILL: 26,
    }
    assert set(Counter(row.issuer_id for row in picked).values()) == {4}
    assert chosen.unmatched_transitions == ()


@pytest.mark.parametrize(
    ("count", "target"), [(19, None), (20, 20), (39, 39), (40, 40)]
)
def test_the_event_count_guards(count, target) -> None:
    """Issuer-major, so the first 20 events already span all eight quarters."""
    rows = [event(n, end) for n in range(1, 6) for end in ENDS][:count]
    if target is None:
        with pytest.raises(PilotRefused) as refused:
            run(rows)
        assert refused.value.reason is PilotRefusal.BLOCKED
        assert str(refused.value) == "blocked: 19 eligible events, fewer than 20"
        return
    chosen = run(rows)
    assert (chosen.target, chosen.underfilled) == (target, target < 40)
    assert {row.event_id for row in chosen.rows} == {row.event_id for row in rows}


@pytest.mark.parametrize("issuers", [40, 41])
def test_more_than_40_issuers_needs_a_scope_decision(issuers) -> None:
    rows = [event(n, ENDS[n % 8]) for n in range(1, issuers + 1)]
    if issuers == 40:
        chosen = run(rows)
        reasons = {row.selection_reason for row in chosen.rows}
        assert (len(chosen.rows), reasons) == (40, {SelectionReason.ISSUER_COVERAGE})
        return
    with pytest.raises(PilotRefused) as refused:
        run(rows)
    assert str(refused.value) == (
        "scope_decision_needed: 41 issuers have eligible events, more than 40"
    )


def test_mandatory_cases_beyond_the_target_refuse_before_filling() -> None:
    """Forty issuers, and issuer 1's entry and exit have different targets: step 1
    takes 40 events, and step 2 must add the other."""
    rows = [event(n, ENDS[n % 8]) for n in range(2, 41)]
    rows += [event(1, ENDS[1]), event(1, ENDS[2])]
    moves = [
        transition(1, ENTRY, date(2025, 1, 1)),
        transition(1, EXIT, date(2025, 5, 1)),
    ]
    with pytest.raises(PilotRefused) as refused:
        run(rows, moves)
    assert str(refused.value) == (
        "mandatory_overflow: steps 1 to 3 take 41 events, more than the target 40"
    )


def test_a_quarter_with_no_eligible_event_refuses() -> None:
    kept = [end for n, end in enumerate(ENDS) if n not in (3, 6)]
    rows = [event(n, end) for n in range(1, 6) for end in kept]
    with pytest.raises(PilotRefused) as refused:
        run(rows)
    assert str(refused.value) == (
        "quarter_uncovered: no eligible event in 2025Q2, 2026Q1"
    )


def test_shuffled_input_gives_a_byte_identical_pilot() -> None:
    rows, moves = forty()
    events = EventManifestDefinition(
        corpus_id="djia-direct",
        event_manifest_version=1,
        universe_id="djia-direct",
        universe_version=1,
        universe_operative_hash="b" * 64,
        discovery_policy_version="release-id/1",
        eligibility_policy_version="eligibility/1",
        public_information_cutoff=date(2026, 9, 22),
        content_hash="a" * 64,
        created_at=NOW,
    )

    def pilot(rows, moves) -> bytes:
        return serialize(Pilot(events, 1, SEED, run(rows, moves)).manifest(1, NOW))

    first = pilot(rows, moves)
    for n in range(3):
        shuffled = list(rows)
        random.Random(n).shuffle(shuffled)
        assert pilot(shuffled, list(reversed(moves))) == first


@pytest.fixture(scope="module")
def universe() -> UniverseManifest:
    return load_manifest(COHORT)


@pytest.fixture(scope="module")
def frozen(universe, tmp_path_factory) -> Path:
    """The reviewed layer's event manifest, frozen in a corpus directory."""
    root = tmp_path_factory.mktemp("events")
    layer = write_layer(root / "data" / "raw" / "events", root)
    saved = SavedResponses(layer.store)

    def build(overrides=()):
        return build_events(
            universe,
            saved,
            EventOverridesFile(schema_version=1, overrides=overrides),
            corpus_id="djia-synthetic",
        )

    directory = root / "corpus"
    freeze_events(build(review(build())), saved, directory, now=NOW)
    return directory


@pytest.fixture
def corpus(frozen, tmp_path) -> Path:
    return Path(shutil.copytree(frozen, tmp_path / "corpus"))


def events_of(directory: Path) -> EventManifest:
    return load_event_manifest(directory / "events-v1.json")


def test_the_transitions_are_issuer_level_entries_and_exits_in_scope(universe) -> None:
    """Dynamo's class B joins a member issuer: no transition. Acme's removal is
    withheld, and the anchor starts are lower bounds: none either."""
    assert transitions(universe) == (
        MembershipTransition(
            issuer_id="cik-0009990002",
            kind=EXIT,
            effective_date=date(2024, 11, 8),
            assertion_ids=("index-2024-11-01:borealis-common:removed",),
        ),
        MembershipTransition(
            issuer_id="cik-0009990003",
            kind=ENTRY,
            effective_date=date(2024, 11, 8),
            assertion_ids=("index-2024-11-01:corvid-common:added",),
        ),
        MembershipTransition(
            issuer_id="cik-0009990006",
            kind=EXIT,
            effective_date=date(2026, 6, 22),
            assertion_ids=("index-2026-06-16:eastfield-common:removed",),
        ),
    )


def dynamo(universe: UniverseManifest, a_to: date, b_from: date) -> UniverseManifest:
    """The synthetic universe, with Dynamo's class A leaving on ``a_to`` and its class
    B joining on ``b_from``."""
    (eastfield,) = [
        a
        for a in universe.assertions
        if a.membership_assertion_id == "index-2026-06-16:eastfield-common:removed"
    ]
    removal = eastfield.model_copy(
        update={
            "membership_assertion_id": "index-2026-06-16:dynamo-class-a:removed",
            "security_id": "dynamo-class-a",
        }
    )
    intervals = []
    for interval in universe.intervals:
        if interval.security_id == "dynamo-class-a":
            interval = interval.model_copy(
                update={
                    "effective_to": a_to,
                    "effective_to_timing": BoundTiming.BEFORE_OPEN,
                    "assertion_ids": (
                        removal.membership_assertion_id,
                        *interval.assertion_ids,
                    ),
                }
            )
        elif interval.security_id == "dynamo-class-b":
            interval = interval.model_copy(update={"effective_from": b_from})
        intervals.append(interval)
    return universe.model_copy(
        update={
            "assertions": (*universe.assertions, removal),
            "intervals": tuple(intervals),
        }
    )


@pytest.mark.parametrize(
    ("a_to", "b_from", "expected"),
    [
        (date(2026, 6, 22), date(2026, 6, 22), []),
        (
            date(2026, 6, 22),
            date(2026, 6, 29),
            [(EXIT, date(2026, 6, 22)), (ENTRY, date(2026, 6, 29))],
        ),
        (date(2026, 9, 22), date(2026, 9, 23), [(EXIT, date(2026, 9, 22))]),
    ],
    ids=["handoff", "gap", "cutoff"],
)
def test_a_handoff_is_no_transition_and_a_gap_is_two(
    universe, a_to, b_from, expected
) -> None:
    found = transitions(dynamo(universe, a_to, b_from))
    assert [
        (t.kind, t.effective_date) for t in found if t.issuer_id == "cik-0009990005"
    ] == expected


def test_an_anchor_start_in_scope_is_never_an_entry(universe) -> None:
    """Acme's roster snapshot, moved into scope, is still a lower bound."""
    intervals = tuple(
        interval.model_copy(update={"effective_from": date(2024, 7, 2)})
        if interval.security_id == "acme-common"
        else interval
        for interval in universe.intervals
    )
    found = transitions(universe.model_copy(update={"intervals": intervals}))
    assert found == transitions(universe)


def test_the_synthetic_pilot_is_underfilled_and_takes_every_event(
    corpus, universe
) -> None:
    events = events_of(corpus)
    pilot = select_pilot(events, universe)
    chosen = pilot.selection
    eligible = {
        row.event_id: row
        for row in events.rows
        if row.eligibility_status is EventStatus.ELIGIBLE
    }
    assert (chosen.target, chosen.underfilled, len(eligible)) == (27, True, 27)
    assert {row.event_id for row in chosen.rows} == set(eligible)
    reasons = {row.event_id: row.selection_reason for row in chosen.rows}
    for target in ("cik-0009990003:2024-12-31", "cik-0009990006:2026-03-31"):
        assert reasons[target] in (BOUNDARY, SelectionReason.ISSUER_COVERAGE)
    assert [r.event_id for r in chosen.rows if r.selection_reason is BOUNDARY] == [
        "cik-0009990003:2024-12-31",
        "cik-0009990006:2026-03-31",
    ]
    assert Counter(reasons.values()) == {
        SelectionReason.ISSUER_COVERAGE: 4,
        SelectionReason.MEMBERSHIP_BOUNDARY: 2,
        SelectionReason.QUARTER_COVERAGE: 4,
        SelectionReason.LONGITUDINAL_FILL: 17,
    }
    assert [(t.issuer_id, t.kind) for t in chosen.unmatched_transitions] == [
        ("cik-0009990002", EXIT)
    ]
    obeys_the_steps(list(events.rows), chosen.rows, pilot.seed)
    assert len({row.issuer_id for row in eligible.values()}) == 4
    quartered = {quarter(row.period_end) for row in eligible.values()}
    assert quartered == set(quarters(START, STOP))


def test_the_pilot_freezes_beside_its_event_manifest(corpus, universe) -> None:
    pilot = select_pilot(events_of(corpus), universe)
    first = freeze_pilot(pilot, universe, corpus, now=NOW)
    assert (first.created, first.path.name) == (True, "pilot-v1.json")
    assert first.manifest.definition.pilot_id == "djia-synthetic-pilot"
    assert load_pilot(first.path, universe) == first.manifest
    again = freeze_pilot(pilot, universe, corpus, now=NOW)
    assert (again.created, again.path) == (False, first.path)
    assert sorted(path.name for path in corpus.iterdir()) == [
        "events-v1.evidence.json",
        "events-v1.json",
        "pilot-v1.json",
    ]


def moved(universe: UniverseManifest) -> UniverseManifest:
    intervals = tuple(
        interval.model_copy(update={"effective_from": date(2024, 11, 9)})
        if interval.security_id == "corvid-common"
        else interval
        for interval in universe.intervals
    )
    return universe.model_copy(update={"intervals": intervals})


@pytest.mark.parametrize(
    ("tamper", "message"),
    [
        ("rename", "holds version 1"),
        ("edit", "does not hash to its content_hash"),
        ("no events", "which the pilot names, is not in"),
        ("other events", "is not the event manifest the pilot names"),
        ("universe", "operative hash"),
        ("seed", "selection_seed does not recompute"),
        ("stray", "not eligible events of events-v1.json"),
    ],
)
def test_loading_rechecks_the_chain(
    corpus, universe, tmp_path, tamper, message
) -> None:
    frozen = freeze_pilot(
        select_pilot(events_of(corpus), universe), universe, corpus, now=NOW
    )
    path, reader = frozen.path, universe
    if tamper == "rename":
        path = corpus / "pilot-v2.json"
        shutil.copy(frozen.path, path)
    elif tamper == "edit":
        text = frozen.path.read_text().replace(
            '"underfilled": true', '"underfilled": false'
        )
        path = tmp_path / "pilot-v1.json"
        path.write_text(text)
    elif tamper == "no events":
        (tmp_path / "alone").mkdir()
        path = Path(shutil.copy(frozen.path, tmp_path / "alone" / "pilot-v1.json"))
    elif tamper == "other events":
        other = events_of(corpus)
        rows = tuple(
            row.model_copy(update={"reported_fiscal_quarter": "Q9"})
            if row.event_id == "cik-0009990001:2024-08-31"
            else row
            for row in other.rows
        )
        other = rehashed(other.model_copy(update={"rows": rows}))
        (tmp_path / "other").mkdir()
        (tmp_path / "other" / "events-v1.json").write_bytes(serialize(other))
        path = Path(shutil.copy(frozen.path, tmp_path / "other" / "pilot-v1.json"))
    elif tamper == "universe":
        reader = moved(universe)
    else:
        manifest = frozen.manifest
        if tamper == "seed":
            seed = manifest.definition.model_copy(update={"selection_seed": "c" * 64})
            manifest = manifest.model_copy(update={"definition": seed})
        else:
            first = manifest.rows[0].model_copy(
                update={"event_id": "cik-0009990002:2024-09-30"}
            )
            manifest = manifest.model_copy(update={"rows": (first, *manifest.rows[1:])})
        definition = manifest.definition.model_copy(
            update={"content_hash": pilot_content_hash(manifest)}
        )
        path.write_bytes(
            serialize(manifest.model_copy(update={"definition": definition}))
        )
    with pytest.raises(ValueError, match=message):
        load_pilot(path, reader)


def rehashed(manifest: EventManifest) -> EventManifest:
    definition = manifest.definition.model_copy(
        update={"content_hash": content_hash(manifest)}
    )
    return manifest.model_copy(update={"definition": definition})


def test_select_pilot_reads_only_the_universe_its_event_manifest_read(
    corpus, universe
) -> None:
    """The policy's name is in the operative projection (EV4), so a universe naming
    another policy is refused even when an event manifest was built from it."""
    events = events_of(corpus)
    with pytest.raises(ValueError, match="operative hash"):
        select_pilot(events, moved(universe))
    other = universe.model_copy(
        update={
            "definition": universe.definition.model_copy(
                update={"selection_policy_version": "djia-pilot/2"}
            )
        }
    )
    read = events.definition.model_copy(
        update={"universe_operative_hash": operative_hash(other)}
    )
    built = rehashed(events.model_copy(update={"definition": read}))
    with pytest.raises(ValueError, match="names djia-pilot/2, not djia-pilot/1"):
        select_pilot(built, other)


def test_a_changed_event_fact_or_policy_reseeds_and_a_universe_version_does_not(
    corpus, universe
) -> None:
    """SV11 for the pilot (P7-2)."""
    events = events_of(corpus)
    pilot = select_pilot(events, universe)
    rows = tuple(
        row.model_copy(update={"reported_fiscal_quarter": "Q9"})
        if row.event_id == "cik-0009990001:2024-08-31"
        else row
        for row in events.rows
    )
    changed = select_pilot(rehashed(events.model_copy(update={"rows": rows})), universe)
    assert changed.seed != pilot.seed
    assert changed.content_hash != pilot.content_hash
    renumbered = universe.model_copy(
        update={
            "definition": universe.definition.model_copy(update={"universe_version": 2})
        }
    )
    again = select_pilot(events, renumbered)
    assert (again.seed, again.content_hash) == (pilot.seed, pilot.content_hash)
    assert again.manifest(1, NOW).definition.universe_version == 2
    assert pilot_seed("a" * 64, "b" * 64, "djia-pilot/2") != SEED
    manifest = pilot.manifest(1, NOW)
    policy = manifest.definition.model_copy(
        update={"selection_policy_version": "djia-pilot/2"}
    )
    assert pilot_content_hash(manifest.model_copy(update={"definition": policy})) != (
        manifest.definition.content_hash
    )


def test_a_new_event_manifest_version_gives_the_next_pilot(corpus, universe) -> None:
    first = freeze_pilot(
        select_pilot(events_of(corpus), universe), universe, corpus, now=NOW
    )
    events = events_of(corpus)
    rows = tuple(
        row.model_copy(update={"reported_fiscal_quarter": "Q9"})
        if row.event_id == "cik-0009990001:2024-08-31"
        else row
        for row in events.rows
    )
    definition = events.definition.model_copy(update={"event_manifest_version": 2})
    second = rehashed(
        events.model_copy(update={"rows": rows, "definition": definition})
    )
    (corpus / "events-v2.json").write_bytes(serialize(second))
    frozen = freeze_pilot(select_pilot(second, universe), universe, corpus, now=NOW)
    assert (frozen.created, frozen.path.name) == (True, "pilot-v2.json")
    assert frozen.manifest.definition.event_manifest_version == 2
    assert load_pilot(first.path, universe) == first.manifest
    assert pilot_path(corpus, 2) == frozen.path
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_pilot.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_pilot.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.pilot'`.

- [x] **Step 3: Write the records and the policy**

> Deviation: the final review found that `freeze_pilot` listed earlier versions with `frozen_pilots(directory, universe)`, which checked each one's chain against the caller's universe, so after a cohort refreeze with changed facts every later pilot freeze would refuse. The user chose to fix it before Completion (`17ce98e`): `frozen_pilots(directory)` checks each version's hash and name only, as `frozen_event_manifests` does; `load_pilot` still checks a pilot's whole chain, and `freeze_pilot` checks it for the version it returns or writes. No committed output changed.

Create `/tmp/plan7-task14-records.py`:

```python
"""Plan 7: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/records.py": [
        (
            "\"\"\"Stage 5's records: the event manifest, its evidence record, and the overrides\n"
            "(the Stage 5 spec, §The event manifest and §Review overrides).\n"
            "\n",
            "\"\"\"Stage 5's records: the event manifest, its evidence record, the overrides, and the\n"
            "pilot manifest (the Stage 5 spec, §The event manifest, §Review overrides, and §Pilot\n"
            "selection).\n"
            "\n",
        ),
        (
            "  ``overrides.toml`` like Stage 4's (P6-18).\n"
            "\n",
            "  ``overrides.toml`` like Stage 4's (P6-18).\n"
            "- **The pilot.** ``PilotManifest`` is ``djia-pilot/1``'s frozen selection: its rows in\n"
            "  the order taken, each with its reason, and the transitions it could not cover. Its\n"
            "  content hash leaves out the same fields as the event manifest's.\n"
            "\n",
        ),
        (
            "    events: tuple[EventCitations, ...]\n",
            "    events: tuple[EventCitations, ...]\n"
            "\n"
            "\n"
            "class SelectionReason(StrEnum):\n"
            "    \"\"\"Why ``djia-pilot/1`` took an event (S §Pilot selection).\"\"\"\n"
            "\n"
            "    ISSUER_COVERAGE = \"issuer_coverage\"\n"
            "    \"\"\"Step 1: the issuer's event from the quarter with the fewest selections.\"\"\"\n"
            "    MEMBERSHIP_BOUNDARY = \"membership_boundary\"\n"
            "    \"\"\"Step 2: the nearest eligible event on a transition's member side.\"\"\"\n"
            "    QUARTER_COVERAGE = \"quarter_coverage\"\n"
            "    \"\"\"Step 3: an event of a quarter that had no selection.\"\"\"\n"
            "    LONGITUDINAL_FILL = \"longitudinal_fill\"\n"
            "    \"\"\"Step 5: the event farthest from its issuer's nearest selected period end.\"\"\"\n"
            "\n"
            "\n"
            "class TransitionKind(StrEnum):\n"
            "    ENTRY = \"entry\"\n"
            "    \"\"\"The issuer's membership starts.\"\"\"\n"
            "    EXIT = \"exit\"\n"
            "    \"\"\"The issuer's membership ends.\"\"\"\n"
            "\n"
            "\n"
            "class PilotRow(_Part):\n"
            "    \"\"\"One selected event.\"\"\"\n"
            "\n"
            "    event_id: IdPart\n"
            "    selection_order: PositiveInt\n"
            "    selection_reason: SelectionReason\n"
            "\n"
            "\n"
            "class MembershipTransition(_Part):\n"
            "    \"\"\"An issuer-level entry or exit (S §Pilot selection, step 2).\"\"\"\n"
            "\n"
            "    issuer_id: IdPart\n"
            "    kind: TransitionKind\n"
            "    effective_date: date\n"
            "    assertion_ids: tuple[IdPart, ...]\n"
            "    \"\"\"The assertions that set the bound.\"\"\"\n"
            "\n"
            "\n"
            "class PilotDefinition(_Part):\n"
            "    \"\"\"The pilot manifest's definition (S §Pilot selection).\"\"\"\n"
            "\n"
            "    pilot_id: IdPart\n"
            "    pilot_version: PositiveInt\n"
            "    universe_version: PositiveInt\n"
            "    universe_operative_hash: Sha256Hex\n"
            "    event_manifest_version: PositiveInt\n"
            "    eligible_event_manifest_hash: Sha256Hex\n"
            "    selection_policy_version: NonBlankStr\n"
            "    selection_seed: Sha256Hex\n"
            "    target: PositiveInt\n"
            "    underfilled: bool\n"
            "    content_hash: Sha256Hex\n"
            "    created_at: AwareDatetime\n"
            "\n"
            "\n"
            "PILOT_UNHASHED = frozenset(\n"
            "    {\"pilot_version\", \"universe_version\", \"content_hash\", \"created_at\"}\n"
            ")\n"
            "\n"
            "\n"
            "class PilotManifest(IngestionRecord):\n"
            "    \"\"\"The frozen pilot: the events to acquire, in the order taken.\"\"\"\n"
            "\n"
            "    definition: PilotDefinition\n"
            "    rows: tuple[PilotRow, ...]\n"
            "    unmatched_transitions: tuple[MembershipTransition, ...]\n"
            "    \"\"\"Each transition in scope with no eligible event on its member side.\"\"\"\n"
            "\n"
            "    @model_validator(mode=\"after\")\n"
            "    def _ordered(self) -> Self:\n"
            "        orders = [row.selection_order for row in self.rows]\n"
            "        if orders != list(range(1, len(self.rows) + 1)):\n"
            "            raise ValueError(\"rows are in selection order, from 1\")\n"
            "        if len({row.event_id for row in self.rows}) != len(self.rows):\n"
            "            raise ValueError(\"an event is selected once\")\n"
            "        if len(self.rows) != self.definition.target:\n"
            "            raise ValueError(\"the pilot holds its target\")\n"
            "        keys = [\n"
            "            (t.effective_date, t.issuer_id, t.kind) for t in self.unmatched_transitions\n"
            "        ]\n"
            "        if keys != sorted(set(keys)):\n"
            "            raise ValueError(\n"
            "                \"transitions are unique and sorted by date, issuer, and kind\"\n"
            "            )\n"
            "        return self\n"
            "\n"
            "\n"
            "def pilot_content_hash(manifest: PilotManifest) -> str:\n"
            "    \"\"\"SHA-256 of the canonical JSON of the definition, less ``PILOT_UNHASHED``, with\n"
            "    the rows and the unmatched transitions.\"\"\"\n"
            "    definition = manifest.definition.model_dump(\n"
            "        mode=\"json\", exclude=set(PILOT_UNHASHED)\n"
            "    )\n"
            "    return digest(\n"
            "        {\n"
            "            \"definition\": definition,\n"
            "            \"rows\": [row.model_dump(mode=\"json\") for row in manifest.rows],\n"
            "            \"unmatched_transitions\": [\n"
            "                t.model_dump(mode=\"json\") for t in manifest.unmatched_transitions\n"
            "            ],\n"
            "        }\n"
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

Apply `task14-records`.

Create `packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py`:

```python
"""``djia-pilot/1``: the feasibility pilot, drawn by rule from a frozen event manifest
(the Stage 5 spec, §Pilot selection, step 5; EV4, EV8).

- **Inputs.** ``E`` is the event manifest's ``eligible`` rows, and ``U`` their
  issuers. The membership transitions come from the universe manifest the event
  manifest read, which must have the operative hash it records (plan 7, P7-20). No
  acquisition, parse, or later outcome is an input.
- **Seed and order.** The seed is the SHA-256 of the canonical JSON of the event
  manifest's content hash, the policy's name, and the universe's operative hash.
  ``h(x)`` is the SHA-256 of ``<seed>:<x>``. Every order and tie uses ``h``, so the
  input's row order cannot matter.
- **Guards.** More than 40 issuers refuses with ``scope_decision_needed``, and fewer
  than 20 events with ``blocked``. From 20 to 39 events, the target is every event,
  and the pilot is ``underfilled``. Otherwise the target is 40.
- **Steps.** Issuer coverage; membership boundaries; quarter coverage, which refuses
  with ``quarter_uncovered`` when a quarter has no eligible event; a refusal with
  ``mandatory_overflow`` when those steps take more than the target; and the
  longitudinal fill.
- **Transitions.** An issuer's membership is the union of its securities' intervals,
  by day. An entry is a start, not an ``anchor_snapshot``, whose day before no
  interval of the issuer holds. An exit is an end whose day no interval holds. So a
  second security joining a member issuer is neither, and nor is a same-day handoff.
  Those dated in ``[period_end_start, public_information_cutoff]`` are in scope. The
  member side of an entry is on or after its date, and of an exit on or before it:
  eligibility has already placed each release against the bound's timing.

Freezing follows the event manifest's rules (P6-14). Loading rechecks the chain: the
pilot's hash and name, the event manifest it names, and that manifest's universe,
whose operative hash is computed again.
"""

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from pathlib import Path

from earnings_core import sha256_hex

from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.identity import operative_hash
from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.acceptance import EASTERN
from earnings_ingestion.events.build import EPOCH
from earnings_ingestion.events.eligibility import span
from earnings_ingestion.events.freeze import (
    load_event_manifest,
    manifest_path,
    serialize,
)
from earnings_ingestion.events.records import (
    EventManifest,
    EventManifestDefinition,
    EventRow,
    EventStatus,
    MembershipTransition,
    PilotDefinition,
    PilotManifest,
    PilotRow,
    SelectionReason,
    TransitionKind,
    content_hash,
    pilot_content_hash,
)
from earnings_ingestion.fetch.store import write_new

PILOT_POLICY = "djia-pilot/1"
PILOT_SIZE = 40
MINIMUM_EVENTS = 20


class PilotRefusal(StrEnum):
    SCOPE_DECISION_NEEDED = "scope_decision_needed"
    BLOCKED = "blocked"
    QUARTER_UNCOVERED = "quarter_uncovered"
    MANDATORY_OVERFLOW = "mandatory_overflow"


class PilotRefused(ValueError):
    """``djia-pilot/1`` refuses: nothing is selected, and nothing is written."""

    def __init__(self, reason: PilotRefusal, detail: str) -> None:
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}")


def pilot_seed(
    event_manifest_hash: str, universe_operative_hash: str, policy: str = PILOT_POLICY
) -> str:
    """The seed: SHA-256 of the canonical JSON of the three inputs (EV4)."""
    return digest(
        {
            "eligible_event_manifest_hash": event_manifest_hash,
            "selection_policy_version": policy,
            "universe_operative_hash": universe_operative_hash,
        }
    )


def ordering(seed: str) -> Callable[[str], str]:
    """``h``: SHA-256 of the UTF-8 string ``<seed>:<x>``."""
    return lambda x: sha256_hex(f"{seed}:{x}".encode())


def quarter(day: date) -> str:
    """The calendar quarter of ``day``, such as ``2024Q3``."""
    return f"{day.year}Q{(day.month - 1) // 3 + 1}"


def quarters(start: date, stop: date) -> tuple[str, ...]:
    """The calendar quarters of the period ends in ``[start, stop)``."""
    found = []
    year, number = start.year, (start.month - 1) // 3 + 1
    while date(year, 3 * number - 2, 1) < stop:
        found.append(f"{year}Q{number}")
        year, number = (year + 1, 1) if number == 4 else (year, number + 1)
    return tuple(found)


def transitions(universe: UniverseManifest) -> tuple[MembershipTransition, ...]:
    """The universe's issuer-level entries and exits in scope, sorted by date, issuer,
    and kind."""
    definition = universe.definition
    start, cutoff = definition.period_end_start, definition.public_information_cutoff
    actions = {
        a.membership_assertion_id: a.asserted_action for a in universe.assertions
    }
    found: dict[tuple[date, str, TransitionKind], set[str]] = {}
    for issuer in universe.issuers:
        held = [i for i in universe.intervals if i.security_id in issuer.security_ids]
        for interval in held:
            bounds = span(interval, actions)
            day = interval.effective_from
            if not bounds.anchor and not any(
                other.contains(day - timedelta(days=1)) for other in held
            ):
                key = (day, issuer.issuer_id, TransitionKind.ENTRY)
                found.setdefault(key, set()).update(bounds.start.assertion_ids)
            day = interval.effective_to
            if day is not None and not any(other.contains(day) for other in held):
                key = (day, issuer.issuer_id, TransitionKind.EXIT)
                found.setdefault(key, set()).update(bounds.end.assertion_ids)
    return tuple(
        MembershipTransition(
            issuer_id=issuer_id,
            kind=kind,
            effective_date=day,
            assertion_ids=tuple(sorted(ids)),
        )
        for (day, issuer_id, kind), ids in sorted(found.items())
        if start <= day <= cutoff
    )


def _published(row: EventRow) -> date:
    return row.first_publication_time.astimezone(EASTERN).date()


def _member_side(
    transition: MembershipTransition,
    events: list[EventRow],
    h: Callable[[str], str],
) -> EventRow | None:
    """The transition's nearest eligible event on its member side, if any."""
    day = transition.effective_date
    if transition.kind is TransitionKind.ENTRY:
        after = [row for row in events if _published(row) >= day]
        return min(
            after,
            key=lambda row: (row.first_publication_time, h(row.event_id)),
            default=None,
        )
    before = [row for row in events if _published(row) <= day]
    return min(
        before,
        key=lambda row: (-row.first_publication_time.timestamp(), h(row.event_id)),
        default=None,
    )


@dataclass(frozen=True)
class Selection:
    target: int
    underfilled: bool
    rows: tuple[PilotRow, ...]
    unmatched_transitions: tuple[MembershipTransition, ...]


def select(
    rows: Iterable[EventRow],
    transitions: Iterable[MembershipTransition],
    seed: str,
    *,
    start: date,
    stop: date,
) -> Selection:
    """Run the guards and the five steps over ``rows``' eligible events, whose period
    ends lie in ``[start, stop)``."""
    h = ordering(seed)
    eligible = sorted(
        (row for row in rows if row.eligibility_status is EventStatus.ELIGIBLE),
        key=lambda row: row.event_id,
    )
    by_issuer: dict[str, list[EventRow]] = {}
    for row in eligible:
        by_issuer.setdefault(row.issuer_id, []).append(row)
    if len(by_issuer) > PILOT_SIZE:
        raise PilotRefused(
            PilotRefusal.SCOPE_DECISION_NEEDED,
            f"{len(by_issuer)} issuers have eligible events, more than {PILOT_SIZE}",
        )
    if len(eligible) < MINIMUM_EVENTS:
        raise PilotRefused(
            PilotRefusal.BLOCKED,
            f"{len(eligible)} eligible events, fewer than {MINIMUM_EVENTS}",
        )
    underfilled = len(eligible) < PILOT_SIZE
    target = len(eligible) if underfilled else PILOT_SIZE

    chosen: list[tuple[EventRow, SelectionReason]] = []
    selected: set[str] = set()
    per_quarter: Counter[str] = Counter()
    per_issuer: Counter[str] = Counter()

    def take(row: EventRow, reason: SelectionReason) -> None:
        chosen.append((row, reason))
        selected.add(row.event_id)
        per_quarter[quarter(row.period_end)] += 1
        per_issuer[row.issuer_id] += 1

    for issuer in sorted(by_issuer, key=h):
        row = min(
            by_issuer[issuer],
            key=lambda r: (per_quarter[quarter(r.period_end)], h(r.event_id)),
        )
        take(row, SelectionReason.ISSUER_COVERAGE)

    unmatched, boundary = [], []
    for transition in sorted(
        transitions, key=lambda t: (t.effective_date, t.issuer_id, t.kind)
    ):
        row = _member_side(transition, by_issuer.get(transition.issuer_id, []), h)
        if row is None:
            unmatched.append(transition)
        else:
            boundary.append(((transition.effective_date, h(row.event_id)), row))
    for _, row in sorted(boundary, key=lambda pair: pair[0]):
        if row.event_id not in selected:
            take(row, SelectionReason.MEMBERSHIP_BOUNDARY)

    window = quarters(start, stop)
    held = {quarter(row.period_end) for row in eligible}
    if empty := [q for q in window if q not in held]:
        raise PilotRefused(
            PilotRefusal.QUARTER_UNCOVERED, f"no eligible event in {', '.join(empty)}"
        )
    for each in window:
        if per_quarter[each]:
            continue
        row = min(
            (r for r in eligible if quarter(r.period_end) == each),
            key=lambda r: (per_issuer[r.issuer_id], h(r.event_id)),
        )
        take(row, SelectionReason.QUARTER_COVERAGE)

    if len(chosen) > target:
        raise PilotRefused(
            PilotRefusal.MANDATORY_OVERFLOW,
            f"steps 1 to 3 take {len(chosen)} events, more than the target {target}",
        )

    while len(chosen) < target:
        left = {
            issuer: [r for r in events if r.event_id not in selected]
            for issuer, events in by_issuer.items()
        }
        left = {issuer: events for issuer, events in left.items() if events}
        fewest = min(per_issuer[issuer] for issuer in left)
        pool = [
            r for i, events in left.items() if per_issuer[i] == fewest for r in events
        ]

        def distance(row: EventRow) -> int:
            return min(
                abs((row.period_end - taken.period_end).days)
                for taken, _ in chosen
                if taken.issuer_id == row.issuer_id
            )

        row = min(pool, key=lambda r: (-distance(r), h(r.event_id)))
        take(row, SelectionReason.LONGITUDINAL_FILL)

    return Selection(
        target=target,
        underfilled=underfilled,
        rows=tuple(
            PilotRow(event_id=row.event_id, selection_order=n, selection_reason=reason)
            for n, (row, reason) in enumerate(chosen, 1)
        ),
        unmatched_transitions=tuple(unmatched),
    )


@dataclass(frozen=True)
class Pilot:
    """A selection, and what it was drawn from: ready to freeze."""

    events: EventManifestDefinition
    universe_version: int
    seed: str
    selection: Selection

    def manifest(self, version: int, created_at: datetime) -> PilotManifest:
        events, selection = self.events, self.selection
        draft = PilotManifest(
            definition=PilotDefinition(
                pilot_id=f"{events.corpus_id}-pilot",
                pilot_version=version,
                universe_version=self.universe_version,
                universe_operative_hash=events.universe_operative_hash,
                event_manifest_version=events.event_manifest_version,
                eligible_event_manifest_hash=events.content_hash,
                selection_policy_version=PILOT_POLICY,
                selection_seed=self.seed,
                target=selection.target,
                underfilled=selection.underfilled,
                content_hash="0" * 64,
                created_at=created_at,
            ),
            rows=selection.rows,
            unmatched_transitions=selection.unmatched_transitions,
        )
        hashed = draft.definition.model_copy(
            update={"content_hash": pilot_content_hash(draft)}
        )
        return draft.model_copy(update={"definition": hashed})

    @property
    def content_hash(self) -> str:
        return self.manifest(1, EPOCH).definition.content_hash


def select_pilot(events: EventManifest, universe: UniverseManifest) -> Pilot:
    """``djia-pilot/1`` over a frozen event manifest and the universe it read."""
    definition = events.definition
    if content_hash(events) != definition.content_hash:
        raise ValueError("the event manifest does not hash to its content_hash")
    operative = operative_hash(universe)
    if operative != definition.universe_operative_hash:
        raise ValueError(
            "the universe's operative hash is not the one the event manifest read"
        )
    named = universe.definition.selection_policy_version
    if named != PILOT_POLICY:
        raise ValueError(f"the universe names {named}, not {PILOT_POLICY}")
    seed = pilot_seed(definition.content_hash, operative)
    selection = select(
        events.rows,
        transitions(universe),
        seed,
        start=universe.definition.period_end_start,
        stop=universe.definition.period_end_stop,
    )
    return Pilot(
        events=definition,
        universe_version=universe.definition.universe_version,
        seed=seed,
        selection=selection,
    )


@dataclass(frozen=True)
class FrozenPilot:
    manifest: PilotManifest
    path: Path
    created: bool
    """False when an existing version already held this content."""


def pilot_path(directory: Path, version: int) -> Path:
    return directory / f"pilot-v{version}.json"


def check_chain(
    manifest: PilotManifest, directory: Path, universe: UniverseManifest
) -> EventManifest:
    """The event manifest ``manifest`` names, in ``directory``, once the chain to it
    and to ``universe`` checks."""
    definition = manifest.definition
    path = manifest_path(directory, definition.event_manifest_version)
    if not path.exists():
        raise ValueError(f"{path.name}, which the pilot names, is not in {directory}")
    events = load_event_manifest(path)
    if events.definition.content_hash != definition.eligible_event_manifest_hash:
        raise ValueError(f"{path.name} is not the event manifest the pilot names")
    hashes = {
        operative_hash(universe),
        definition.universe_operative_hash,
        events.definition.universe_operative_hash,
    }
    if len(hashes) != 1:
        raise ValueError(
            "the universe's operative hash is not the one the pilot and its event"
            " manifest read"
        )
    seed = pilot_seed(
        definition.eligible_event_manifest_hash,
        definition.universe_operative_hash,
        definition.selection_policy_version,
    )
    if seed != definition.selection_seed:
        raise ValueError("selection_seed does not recompute from its inputs")
    eligible = {
        row.event_id
        for row in events.rows
        if row.eligibility_status is EventStatus.ELIGIBLE
    }
    if strays := [
        row.event_id for row in manifest.rows if row.event_id not in eligible
    ]:
        raise ValueError(f"not eligible events of {path.name}: {strays}")
    return events


def load_pilot(path: Path, universe: UniverseManifest) -> PilotManifest:
    """A frozen pilot, refused unless its hash, its name, and its chain check."""
    manifest = PilotManifest.model_validate_json(path.read_bytes())
    definition = manifest.definition
    if pilot_content_hash(manifest) != definition.content_hash:
        raise ValueError(f"{path} does not hash to its content_hash")
    if path.name != pilot_path(path.parent, definition.pilot_version).name:
        raise ValueError(f"{path} holds version {definition.pilot_version}")
    check_chain(manifest, path.parent, universe)
    return manifest


def frozen_pilots(directory: Path, universe: UniverseManifest) -> list[PilotManifest]:
    """Every frozen pilot in ``directory``, oldest first."""
    pilots = [load_pilot(path, universe) for path in directory.glob("pilot-v*.json")]
    return sorted(pilots, key=lambda m: m.definition.pilot_version)


def freeze_pilot(
    pilot: Pilot, universe: UniverseManifest, directory: Path, *, now: datetime
) -> FrozenPilot:
    """Freeze ``pilot`` beside the event manifest it names, or return the version
    that holds it."""
    existing = frozen_pilots(directory, universe)
    for manifest in existing:
        if manifest.definition.content_hash == pilot.content_hash:
            version = manifest.definition.pilot_version
            return FrozenPilot(manifest, pilot_path(directory, version), created=False)
    version = 1 + max((m.definition.pilot_version for m in existing), default=0)
    manifest = pilot.manifest(version, now)
    check_chain(manifest, directory, universe)
    write_new(pilot_path(directory, version), serialize(manifest))
    return FrozenPilot(manifest, pilot_path(directory, version), created=True)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_pilot.py -q`

Expected: `28 passed`.

- [x] **Step 5: Document the records**

Register the four models and two enums in the drift test:

Create `/tmp/plan7-task14-dictionary.py`:

```python
"""Plan 7: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "tests/contracts/test_data_dictionary.py": [
        (
            "retrieval metadata, the cohort's records and curated files, and Stage 5's event\n"
            "records.\n"
            "\n",
            "retrieval metadata, the cohort's records and curated files, and Stage 5's event\n"
            "and pilot records.\n"
            "\n",
        ),
        (
            "    events.EventEvidence,\n"
            "]\n",
            "    events.EventEvidence,\n"
            "    events.PilotRow,\n"
            "    events.MembershipTransition,\n"
            "    events.PilotDefinition,\n"
            "    events.PilotManifest,\n"
            "]\n",
        ),
        (
            "    events.EventOverrideKind,\n"
            "]\n",
            "    events.EventOverrideKind,\n"
            "    events.SelectionReason,\n"
            "    events.TransitionKind,\n"
            "]\n",
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

Apply `task14-dictionary`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: FAIL: `6 failed, 94 passed`. The dictionary has no section for the four
models and two enums.

Append to `docs/data-dictionary.md`:

```markdown

## earnings-ingestion pilot records, schema version 1

- **Package.** The records are in `earnings_ingestion.events.records`, and the policy,
  `djia-pilot/1`, in `earnings_ingestion.events.pilot` (Stage 5, plan 7).
- **Schema version.** These records join ingestion schema version `1`.
  `PilotManifest` carries it as `schema_version`; the nested parts do not.
- **Inputs.** The pilot reads a frozen event manifest's `eligible` rows, and the
  membership transitions of the universe manifest that event manifest read (P7-20).
  No acquisition, parse, or later outcome is an input.

### `SelectionReason`

Why `djia-pilot/1` took an event (S §Pilot selection).

| Value | Meaning |
| --- | --- |
| `issuer_coverage` | Step 1: the issuer's event from the quarter with the fewest selections so far |
| `membership_boundary` | Step 2: the nearest eligible event on a transition's member side |
| `quarter_coverage` | Step 3: an event of a quarter with no selection, from the issuer with the fewest |
| `longitudinal_fill` | Step 5: the event farthest, in days, from its issuer's nearest selected `period_end` |

### `TransitionKind`

| Value | Meaning |
| --- | --- |
| `entry` | The issuer's membership starts: a start, not an `anchor_snapshot`, whose day before no interval of the issuer holds |
| `exit` | The issuer's membership ends: an end whose day no interval of the issuer holds |

### `PilotRow`

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | An `eligible` event of the event manifest the pilot names |
| `selection_order` | int ≥ 1 | The order taken, from 1 |
| `selection_reason` | `SelectionReason` | The step that took it |

### `MembershipTransition`

An issuer-level entry or exit dated in `[2024-07-01, 2026-09-22]`, read from the
universe's intervals by day. A second security joining a member issuer is not one,
and nor is a same-day handoff between two of its securities.

| Field | Type | Meaning |
| --- | --- | --- |
| `issuer_id` | ID part | The issuer |
| `kind` | `TransitionKind` | Entry or exit |
| `effective_date` | date | The bound's date |
| `assertion_ids` | tuple of ID part | The assertions that set the bound |

### `PilotDefinition`

| Field | Type | Meaning |
| --- | --- | --- |
| `pilot_id` | ID part | `<corpus_id>-pilot`, such as `djia-2024q3-2026q2-pilot` |
| `pilot_version` | int ≥ 1 | The version; a new one only when the content changes |
| `universe_version` | int ≥ 1 | The cohort version read; outside the content hash (P7-2) |
| `universe_operative_hash` | 64 lowercase hex | Its `operative_hash`, which the event manifest records too (EV4) |
| `event_manifest_version` | int ≥ 1 | The event manifest drawn from |
| `eligible_event_manifest_hash` | 64 lowercase hex | That manifest's `content_hash` |
| `selection_policy_version` | string | `djia-pilot/1` |
| `selection_seed` | 64 lowercase hex | SHA-256 of the canonical JSON of `eligible_event_manifest_hash`, `selection_policy_version`, and `universe_operative_hash` |
| `target` | int ≥ 1 | 40, or every eligible event when there are fewer |
| `underfilled` | bool | Fewer than 40 eligible events, so the target is all of them |
| `content_hash` | 64 lowercase hex | See the frozen pilots, below |
| `created_at` | UTC datetime | When this version was frozen |

### `PilotManifest`

`pilot-v<N>.json`: the frozen selection.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `definition` | `PilotDefinition` | The definition |
| `rows` | tuple of `PilotRow` | The selected events in `selection_order`, as many as `target` |
| `unmatched_transitions` | tuple of `MembershipTransition` | Each transition with no eligible event on its member side: reported, not refused. Sorted by date, issuer, and kind |

## Frozen pilots

- **Where.** `config/corpus/<corpus_id>/pilot-v<N>.json` holds one `PilotManifest`,
  beside the event manifest it names. It is indented JSON with sorted keys, written
  once and never replaced. The synthetic corpus's is in `tests/fixtures/events/`.
- **The content hash.** `content_hash` covers the canonical JSON of the definition,
  less `pilot_version`, `universe_version`, `content_hash`, and `created_at`, with the
  rows and the unmatched transitions. Identical content keeps its version; new
  content takes the next. A new event manifest or a new policy gives a new seed, and
  so a new version.
- **Reading.** `earnings_ingestion.events.pilot.load_pilot` rechecks the chain: the
  pilot's hash and name; the event manifest it names, in the same directory, by its
  content hash; the universe's operative hash, computed again from the universe
  manifest; the seed; and that every row is an eligible event of that manifest.
```

Extract it with `python3 /tmp/plan7-extract.py docs/data-dictionary.md 3`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: `100 passed`.

- [x] **Step 6: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py packages/earnings-ingestion/tests/test_events_pilot.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1235 passed, 24 deselected`; `All checks passed!` and
`243 files already formatted`.

- [x] **Step 7: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-ingestion/src/earnings_ingestion/events/records.py packages/earnings-ingestion/src/earnings_ingestion/events/pilot.py packages/earnings-ingestion/tests/test_events_pilot.py tests/contracts/test_data_dictionary.py
git commit -m "feat(events): select and freeze the pilot with djia-pilot/1"
```

---

### Task 15: The committed synthetic event corpus, and P-VI

This task implements S §The synthetic event layer's committed fixture, SV12 (P-VI),
and P6-3 for the committed records. It follows Stage 4's committed synthetic cohort
(`tests/integration/test_cohort_fixtures.py`).

- **The fixture.** `write_fixture(repo, universe)` writes `tests/fixtures/events/`.
  It reads the synthetic cohort's committed manifest, and never writes under
  `tests/fixtures/cohort/` (EV12). It holds:
  - `raw/`, the layer's saved responses (`write_layer`), with no exhibit (EV2);
  - `overrides.toml`, `review()`'s six decisions. `write_overrides` writes it in the
    shape `load_overrides` reads back, like Stage 4's `overrides.toml`;
  - `events-v1.json` and `events-v1.evidence.json`, frozen from the reviewed build;
  - `pilot-v1.json`, the underfilled pilot.

  It lives in `events/fixture.py`, not in `layer.py`, because it runs the pipeline
  over the layer: the build, the review, both freezes, and the selection. `layer.py`
  stays a generator of saved responses.
- **Regeneration.** `tests/integration/regenerate_event_fixtures.py` replaces the
  directory, and the fixture regenerates byte for byte. `.gitattributes` marks every
  fixture file `-text`, since saved responses are named by their hash.
- **P-VI**, offline, with sockets disabled and no SEC identity set:
  - Stage 4's `build` produces the cohort's intervals and resolution from its saved
    evidence, and the result equals the committed manifest;
  - the event build over the committed responses and `overrides.toml` gives the
    committed manifest's hash, which is eligibility and the frozen event manifest;
  - freezing again writes nothing, and nor does selecting and freezing the pilot;
  - `load_pilot` checks the chain.
- **The evidence** verifies against the committed store with `check_evidence`.
- **P6-3.** No string of 30 characters or more in the three committed records occurs
  in any saved page's `walker-1` text. At plan time, adding one page's longest line
  to the evidence record's limitations made this test fail.

**Plan-time facts:**

- the fixture holds 172 files: 73 HTML and 11 JSON responses, with their 84
  retrieval records, and the four written files;
- `events-v1.json` hashes to `438bfec8…` and `pilot-v1.json` to `71c6ac4f…`, with the
  seed `50d34b31…`;
- the evidence record is 221 KB for 32 events. For the real corpus's roughly 300
  events, expect about 2 MB (Task 20).

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/fixture.py` and
  `tests/integration/regenerate_event_fixtures.py`.
- Create, by running the script: `tests/fixtures/events/`.
- Modify, by appending: `.gitattributes`.
- Test (create): `tests/integration/test_event_fixtures.py`.

**Interfaces:**

- Consumes:
  - Tasks 11 and 12's `write_layer` and `review`;
  - Task 12's `build_events`, `load_overrides`, and `EventBuild`;
  - Task 13's `freeze_events`, `load_event_manifest`, `load_event_evidence`, and
    `check_evidence`;
  - Task 14's `select_pilot`, `freeze_pilot`, `load_pilot`, and `FrozenPilot`;
  - Stage 4's `build`, `build_options`, `load_manifest`, `ArtifactText`, and
    `ArtifactStore`.
- Produces `events/fixture.py`:
  - `FIXTURE_DIR = Path("tests/fixtures/events")`, `COHORT_MANIFEST`,
    `SYNTHETIC_CORPUS = "djia-synthetic"`, and `FROZEN_AT`;
  - `write_overrides(path, overrides) -> None`. Task 20 may reuse it to write the
    signed decisions;
  - `write_fixture(repo, universe, directory=FIXTURE_DIR) -> FrozenPilot`.

- [x] **Step 1: Write the failing tests**

Create `tests/integration/test_event_fixtures.py`:

```python
"""The committed synthetic event corpus: it regenerates byte for byte, and replays
offline from the synthetic cohort's saved evidence and the event layer's saved
responses to its frozen event manifest and pilot (P-VI; SV12).

The replay runs with sockets disabled and no SEC identity set: the cohort's intervals
and resolution, eligibility, and both freezes read committed files alone, and need no
network, credential, proprietary roster, or model call.
"""

import json
import socket
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.cohort.synthetic import build_options
from earnings_ingestion.events.build import build_events, load_overrides
from earnings_ingestion.events.evidence import check_evidence
from earnings_ingestion.events.fixture import (
    COHORT_MANIFEST,
    FIXTURE_DIR,
    SYNTHETIC_CORPUS,
    write_fixture,
)
from earnings_ingestion.events.freeze import (
    freeze_events,
    load_event_evidence,
    load_event_manifest,
)
from earnings_ingestion.events.pilot import freeze_pilot, load_pilot, select_pilot
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.store import ArtifactStore

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / FIXTURE_DIR
REGENERATE = "uv run --locked --all-packages python tests/integration/regenerate_event_fixtures.py"
MANIFESTS = ("events-v1.json", "events-v1.evidence.json", "pilot-v1.json")


def files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_the_fixture_regenerates_byte_for_byte(tmp_path: Path) -> None:
    write_fixture(tmp_path, load_manifest(REPO / COHORT_MANIFEST))
    fresh, committed = files(tmp_path / FIXTURE_DIR), files(ROOT)
    changed = sorted(
        name
        for name in fresh.keys() | committed.keys()
        if fresh.get(name) != committed.get(name)
    )
    assert not changed, f"regenerate with `{REGENERATE}`; differs: {changed[:5]}"
    assert set(MANIFESTS) | {"overrides.toml"} <= set(committed)


@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("the offline event path opened a network connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
    monkeypatch.delenv("SOURCE_IDENTITY", raising=False)


@pytest.mark.usefixtures("offline")
def test_p_vi_replays_offline_to_the_frozen_manifests() -> None:
    committed = load_manifest(REPO / COHORT_MANIFEST)
    definition = committed.definition
    cohort = build(REPO, **build_options())
    universe = cohort.manifest(definition.universe_version, definition.created_at)
    assert universe == committed
    saved = SavedResponses(ArtifactStore(ROOT / "raw", REPO))
    overrides = load_overrides(ROOT / "overrides.toml")
    built = build_events(universe, saved, overrides, corpus_id=SYNTHETIC_CORPUS)
    events = load_event_manifest(ROOT / "events-v1.json")
    assert built.content_hash == events.definition.content_hash
    now = datetime.now(UTC)
    assert not freeze_events(built, saved, ROOT, now=now).created
    pilot = select_pilot(events, universe)
    assert not freeze_pilot(pilot, universe, ROOT, now=now).created
    frozen = load_pilot(ROOT / "pilot-v1.json", universe)
    assert (frozen.definition.target, frozen.definition.underfilled) == (27, True)
    assert [t.issuer_id for t in frozen.unmatched_transitions] == ["cik-0009990002"]


def test_every_citation_verifies_against_the_committed_store() -> None:
    evidence = load_event_evidence(ROOT / "events-v1.evidence.json")
    assert check_evidence(evidence, ArtifactStore(ROOT / "raw", REPO)) == ()
    assert len(evidence.events) == 32


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in strings(item)]
    return []


def test_the_committed_records_quote_no_saved_page() -> None:
    """P6-3: the committed records hold facts, URLs, hashes, and locators, never
    source text, so no string in them of 30 characters or more is in any saved
    page's walker-1 text."""
    written = {
        s
        for name in MANIFESTS
        for s in strings(json.loads((ROOT / name).read_text(encoding="utf-8")))
        if len(s) >= 30
    }
    pages = [
        ArtifactText(path.read_bytes(), "text/html").canonical[0]
        for path in sorted((ROOT / "raw" / "sec-edgar").glob("*.html"))
    ]
    assert written and pages
    assert not [s for s in written if any(s in page for page in pages)]


def ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", path],
        cwd=REPO,
        check=False,
    )
    return result.returncode == 0


def test_saved_responses_stay_local_and_the_fixture_is_committed() -> None:
    assert ignored("data/raw/events/sec-edgar/retrievals/x/y.json")
    committed = files(ROOT)
    assert committed, f"{FIXTURE_DIR} holds no fixture"
    for path in committed:
        assert not ignored(f"{FIXTURE_DIR.as_posix()}/{path}"), path


def test_git_keeps_every_fixture_byte() -> None:
    """Saved responses are named by their hash, so a line-ending conversion on
    checkout would break them: .gitattributes marks every fixture file -text."""
    names = [f"{FIXTURE_DIR.as_posix()}/{path}" for path in files(ROOT)]
    assert names, f"{FIXTURE_DIR} holds no fixture"
    result = subprocess.run(
        ["git", "check-attr", "text", "--", *names],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.splitlines() == [f"{name}: text: unset" for name in names]
```

Extract it with `python3 /tmp/plan7-extract.py tests/integration/test_event_fixtures.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest tests/integration/test_event_fixtures.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.fixture'`.

- [x] **Step 3: Write the fixture writer and its script**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/fixture.py`:

```python
"""The committed synthetic event corpus (the Stage 5 spec, §The synthetic event layer;
P-VI).

``write_fixture(repo, universe)`` writes ``tests/fixtures/events/`` from the synthetic
event layer, reviewed and frozen:

- ``raw/``, the layer's saved responses (``write_layer``);
- ``overrides.toml``, the reviewer's decisions against the first build (``review``);
- ``events-v1.json`` and ``events-v1.evidence.json``, the frozen event manifest and
  its evidence record;
- ``pilot-v1.json``, the frozen pilot, which is underfilled.

``universe`` is the synthetic cohort's committed manifest. Nothing is written under
``tests/fixtures/cohort/``, and every file regenerates byte for byte.
"""

import json
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.build import EventBuild, build_events, load_overrides
from earnings_ingestion.events.freeze import freeze_events
from earnings_ingestion.events.layer import review, write_layer
from earnings_ingestion.events.pilot import FrozenPilot, freeze_pilot, select_pilot
from earnings_ingestion.events.records import EventOverride, EventOverridesFile
from earnings_ingestion.events.saved import SavedResponses

FIXTURE_DIR = Path("tests") / "fixtures" / "events"
COHORT_MANIFEST = (
    Path("tests") / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
)
SYNTHETIC_CORPUS = "djia-synthetic"
FROZEN_AT = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


def _toml(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return json.dumps(str(value))
    raise TypeError(f"no TOML form for {type(value).__name__}")


def write_overrides(path: Path, overrides: Sequence[EventOverride]) -> None:
    """``overrides.toml`` for ``overrides``, as ``load_overrides`` reads it."""
    lines = ["# Synthetic review.", "schema_version = 1"]

    def table(header: str, data: dict) -> None:
        lines.extend(["", header, *(f"{key} = {_toml(v)}" for key, v in data.items())])

    for override in overrides:
        data = override.model_dump(exclude_none=True)
        citations = data.pop("citations")
        table("[[overrides]]", data)
        for citation in citations:
            locator = citation.pop("locator", None)
            table("[[overrides.citations]]", citation)
            if locator is not None:
                table("[overrides.citations.locator]", locator)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fixture(
    repo: Path, universe: UniverseManifest, directory: Path = FIXTURE_DIR
) -> FrozenPilot:
    """Write the committed fixture under ``repo / directory``; return the pilot."""
    root = repo / directory
    saved = SavedResponses(write_layer(root / "raw", repo).store)

    def build(overrides: EventOverridesFile) -> EventBuild:
        return build_events(universe, saved, overrides, corpus_id=SYNTHETIC_CORPUS)

    first = build(EventOverridesFile(schema_version=1))
    write_overrides(root / "overrides.toml", review(first))
    reviewed = build(load_overrides(root / "overrides.toml"))
    frozen = freeze_events(reviewed, saved, root, now=FROZEN_AT)
    pilot = select_pilot(frozen.manifest, universe)
    return freeze_pilot(pilot, universe, root, now=FROZEN_AT)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/fixture.py`.

Create `tests/integration/regenerate_event_fixtures.py`:

```python
"""Regenerate tests/fixtures/events/, the synthetic event corpus (Stage 5, plan 7).

    uv run --locked --all-packages python tests/integration/regenerate_event_fixtures.py

Replaces the whole directory with ``earnings_ingestion.events.fixture``'s output: the
event layer's saved responses, the reviewer's overrides, and the frozen event
manifest, evidence record, and pilot. It reads the synthetic cohort's committed
manifest and writes nothing under tests/fixtures/cohort/. Run it only when
test_event_fixtures.py reports that the committed fixture no longer matches the
generator, and commit the generator change with it. pytest never collects this file.
"""

import shutil
from pathlib import Path

from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.fixture import (
    COHORT_MANIFEST,
    FIXTURE_DIR,
    write_fixture,
)

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    shutil.rmtree(REPO / FIXTURE_DIR, ignore_errors=True)
    frozen = write_fixture(REPO, load_manifest(REPO / COHORT_MANIFEST))
    print(f"wrote {frozen.path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Extract it with `python3 /tmp/plan7-extract.py tests/integration/regenerate_event_fixtures.py`.

Append to `.gitattributes`:

```text
tests/fixtures/events/** -text
```

Extract it with `python3 /tmp/plan7-extract.py .gitattributes`.

- [x] **Step 4: Write the fixture**

```bash
uv run --locked --all-packages python tests/integration/regenerate_event_fixtures.py
find tests/fixtures/events -type f | wc -l
python3 -c "import json; [print(n, json.load(open(f'tests/fixtures/events/{n}'))['definition']['content_hash']) for n in ('events-v1.json', 'pilot-v1.json')]"
```

Expected: `wrote tests/fixtures/events/pilot-v1.json`; `172`;
`events-v1.json 438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58` and
`pilot-v1.json 71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c`.
If a hash differs, stop: an earlier task's code differs from the plan's.

- [x] **Step 5: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest tests/integration/test_event_fixtures.py -q`

Expected: `6 passed`.

- [x] **Step 6: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py tests/integration/test_event_fixtures.py tests/integration/regenerate_event_fixtures.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1241 passed, 24 deselected`; `All checks passed!` and
`246 files already formatted`.

- [x] **Step 7: Commit**

```bash
git log --oneline -3
git add .gitattributes packages/earnings-ingestion/src/earnings_ingestion/events/fixture.py tests/integration/regenerate_event_fixtures.py tests/integration/test_event_fixtures.py tests/fixtures/events
git commit -m "test(events): commit the synthetic event corpus and replay it offline (P-VI)"
```

---

### Task 16: Discovery, and the `sec-edgar` register

This task implements S §Store, client, and readers ("What discovery fetches"), SV5,
and the register edit that S §Inputs asks for. P7-9 and P7-10 record its choices.

- **`discover(universe, fetch, store, *, say)`** saves every response the event build
  reads, through `fetch`, the shared client's `SecClient.fetch`. Only the CLI opens
  the client (P6-22, Task 17). It fetches only what the store lacks, so a rerun
  resumes a stopped run. It runs in three phases, and each reads what the one before
  saved:
  1. each candidate issuer's submissions file and companyfacts file;
  2. what `issuer_filings` reads and finds missing, until nothing is. That is each
     older page in range first, then the index page of every Item 2.02 8-K and 8-K/A
     that either convention places in `[start, cutoff]` (P7-9);
  3. the primary document of every candidate `release-id/1` finds.
     `identify` still lists a candidate whose document is not saved, with the reading
     "nothing saved", so this phase reuses the build's slots and candidacy rather
     than restating them.

  `say` hears each phase's count before anything is fetched (P7-10).
- **`IssuerFilings.missing`** makes phase 2 exact. `issuer_filings` already reported
  each unsaved response as a problem, and now it also lists its URL, so discovery
  fetches what the build reads, and nothing else.
- **A guard.** A response fetched in one round and still missing in the next stops
  discovery, rather than looping. The client's request budget also bounds any loop.
- **`discover_filing(universe, cik, accession, fetch, store)`** saves one filing's
  index page, and an 8-K's or 8-K/A's primary document. It is the remedy that Task
  7's `acceptance_time_unknown` finding and Task 12's `set_release_filing` refusal
  both name: `run events discover --filing CIK ACCESSION`.
- **The tests** run the real `open_sec_client` over a recording `httpx.MockTransport`
  that serves the committed layer (Task 15), so no request leaves the process.
  - A discovery run sends 84 requests, each once. That is exactly the layer's
    responses, and the client's throttle counts every one.
  - No request names a document that a saved index page types `EX-`: no exhibit
    (EV2).
  - The build over what discovery saved gives the committed manifest's hash.
  - A run stopped by a 404 resumes, and fetches only what the store lacks. A third
    run sends nothing.
  - `discover_filing` works for an 8-K and for a 10-Q.
  - Stage 5's modules import no HTTP library and make no throttle of their own
    (R1.3, D5).
- **The register.** `sec-edgar`'s `access_method` gains companyfacts JSON
  (`data.sec.gov/api/xbrl/companyfacts/`), and its `coverage` states Stage 5's reads.
  Its quotes are unchanged, so `fetch_policy_pages.py verify` still passes.
- **The v1 check (P7-3)** runs over Stage 4's saved evidence and sends no request.
  - A rebuild of the real cohort with the edited register has a new content hash,
    `7cb92fe4…`, where v1's is `2d974394…`, because `source_register_version` hashes
    the entry.
  - Its operative hash equals v1's, `c3509234…`.
  - v1 stays the latest version, and nothing is frozen. At plan time, the same
    rebuild with the unedited register reproduced v1's content hash exactly.

**Plan-time facts.** The synthetic run's phases announce 10, 38, 2, 0, and 34 to
fetch. Round 2 of phase 2 fetches the index pages of the filings that Eastfield's
older page lists.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/discover.py`.
- Modify, by exact replacement: `packages/earnings-ingestion/src/earnings_ingestion/events/filings.py`
  and `docs/source-register.toml`.
- Test (create): `packages/earnings-ingestion/tests/test_events_discover.py`.

**Interfaces:**

- Consumes:
  - Tasks 7 to 9's `issuer_filings`, `RELEASE_FORMS`, `issuer_slots`, and
    `identify`;
  - Task 4's `read_companyfacts` and URLs;
  - Task 12's `SavedResponses`;
  - Task 15's committed fixture;
  - Stage 4's `open_sec_client`, `Fetched`, `ArtifactStore`, `SEC_RIGHTS`, and
    `SEC_SOURCE_ID`.
- Produces:
  - `IssuerFilings.missing: tuple[str, ...]`;
  - in `events/discover.py`: `Fetch`, the type of `SecClient.fetch`; `JSON`, `HTML`,
    and `DOCUMENT`, the media types each kind of response may have; and
    `Discovery(fetched)`;
  - `discover(universe, fetch, store, *, say=...) -> Discovery`;
  - `discover_filing(universe, cik, accession, fetch, store, *, say=...) -> Discovery`,
    which raises `ValueError` for a CIK no issuer has, or an accession the saved
    filings do not list.

  Task 17 calls both.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_events_discover.py`:

```python
"""Discovery (the Stage 5 spec, §Store, client, and readers; SV5; EV2).

Every test runs the shared SEC client over a recording transport that serves the
committed synthetic event layer, so no request leaves the process. Discovery must
request exactly the responses the build reads, each once, and never an exhibit.
"""

import re
import shutil
from pathlib import Path

import httpx
import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.build import build_events, load_overrides
from earnings_ingestion.events.discover import discover, discover_filing
from earnings_ingestion.events.filings import issuer_filings
from earnings_ingestion.events.fixture import (
    COHORT_MANIFEST,
    FIXTURE_DIR,
    SYNTHETIC_CORPUS,
)
from earnings_ingestion.events.freeze import load_event_manifest
from earnings_ingestion.events.layer import DYNAMO, Release, filings
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.synthetic import eight_k, index_page
from earnings_ingestion.fetch.client import UnexpectedResponse
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.client import open_sec_client
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import (
    archive_url,
    filing_index_url,
    submissions_url,
)

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / FIXTURE_DIR / "raw"
IDENTITY = {"EDGAR_IDENTITY": "Plan 7 synthetic discovery test@example.com"}
EVENTS_PACKAGE = REPO / "packages/earnings-ingestion/src/earnings_ingestion/events"


def served(root: Path, repo: Path) -> dict[str, tuple[bytes, str]]:
    """Every response saved under ``root``, by URL."""
    store = ArtifactStore(root, repo)
    found = {}
    for path in sorted((root / SEC_SOURCE_ID / "retrievals").glob("*/*.json")):
        record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
        stored = store.get(
            SEC_SOURCE_ID,
            record.sha256,
            rights_status=SEC_RIGHTS.rights_status,
            rights_basis=SEC_RIGHTS.rights_basis,
        )
        found[record.request_url] = (stored.body, record.media_type)
    return found


class Recorder:
    """A transport serving ``responses``, which records every request it sees."""

    def __init__(self, responses: dict[str, tuple[bytes, str]]) -> None:
        self.responses = dict(responses)
        self.requested: list[str] = []

    def transport(self) -> httpx.MockTransport:
        def handle(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            self.requested.append(url)
            if url not in self.responses:
                return httpx.Response(404, text="Not Found")
            body, media_type = self.responses[url]
            return httpx.Response(
                200, content=body, headers={"content-type": media_type}
            )

        return httpx.MockTransport(handle)


@pytest.fixture(scope="module")
def universe():
    return load_manifest(REPO / COHORT_MANIFEST)


@pytest.fixture(scope="module")
def layer() -> dict[str, tuple[bytes, str]]:
    return served(RAW, REPO)


def run(universe, recorder: Recorder, store: ArtifactStore, *, filing=None):
    lines: list[str] = []
    with open_sec_client(
        environ=IDENTITY,
        transport=recorder.transport(),
        sleep=lambda seconds: None,
        max_requests=200,
    ) as sec:
        if filing is None:
            result = discover(universe, sec.fetch, store, say=lines.append)
        else:
            result = discover_filing(universe, *filing, sec.fetch, store)
        sent = sec.throttle.count
    return result, sent, lines


def test_discovery_requests_what_the_build_reads_and_never_an_exhibit(
    universe, layer, tmp_path
) -> None:
    recorder = Recorder(layer)
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    result, sent, lines = run(universe, recorder, store)
    assert sorted(recorder.requested) == sorted(layer)
    assert len(recorder.requested) == len(set(recorder.requested)) == sent == 84
    assert result.fetched == recorder.requested
    assert lines == [
        "submissions and companyfacts: 10 to fetch",
        "older pages and index pages: 38 to fetch",
        "older pages and index pages: 2 to fetch",
        "older pages and index pages: 0 to fetch",
        "primary documents: 34 to fetch",
    ]
    pages = [
        read_filing_index(body)
        for url, (body, _) in layer.items()
        if url.endswith("-index.htm")
    ]
    exhibits = {
        document.filename
        for page in pages
        for document in page.documents
        if document.doc_type.startswith("EX-")
    }
    assert exhibits
    assert not [url for url in recorder.requested if url.rsplit("/", 1)[1] in exhibits]
    built = build_events(
        universe,
        SavedResponses(store),
        load_overrides(REPO / FIXTURE_DIR / "overrides.toml"),
        corpus_id=SYNTHETIC_CORPUS,
    )
    committed = load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json")
    assert built.content_hash == committed.definition.content_hash


def test_a_stopped_run_resumes_and_fetches_only_what_the_store_lacks(
    universe, layer, tmp_path
) -> None:
    gone = sorted(url for url in layer if url.endswith("-index.htm"))[3]
    partial = Recorder({url: r for url, r in layer.items() if url != gone})
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    with pytest.raises(UnexpectedResponse, match="404"):
        run(universe, partial, store)
    first = [url for url in partial.requested if url != gone]
    recorder = Recorder(layer)
    result, sent, _ = run(universe, recorder, store)
    assert sorted(recorder.requested) == sorted(set(layer) - set(first))
    assert gone in recorder.requested and sent == len(recorder.requested)
    again = Recorder(layer)
    result, sent, _ = run(universe, again, store)
    assert (again.requested, sent, result.fetched) == ([], 0, [])


def test_discover_filing_saves_one_filing_and_an_8ks_document(
    universe, layer, tmp_path
) -> None:
    """Dynamo's Item 7.01 8-K was never read; its index page and document are
    served, and discovery saves them on request."""
    (filing,) = [
        filing
        for filing, entry in filings(DYNAMO)
        if isinstance(entry, Release) and "7.01" in entry.items
    ]
    index = filing_index_url(DYNAMO.cik, filing.accession)
    document = archive_url(DYNAMO.cik, filing.accession, filing.primary_document)
    responses = dict(layer)
    responses[index] = (index_page(DYNAMO.cik, filing), "text/html")
    responses[document] = (
        eight_k(DYNAMO.name, [("7.01", ("An invented investor presentation.",))]),
        "text/html",
    )
    root = Path(shutil.copytree(RAW, tmp_path / "data" / "raw" / "events"))
    store = ArtifactStore(root, tmp_path)
    recorder = Recorder(responses)
    run(universe, recorder, store, filing=(DYNAMO.cik, filing.accession))
    assert recorder.requested == [index, document]
    (report, _) = next((f, e) for f, e in filings(DYNAMO) if f.form == "10-Q")
    responses[filing_index_url(DYNAMO.cik, report.accession)] = (
        index_page(DYNAMO.cik, report),
        "text/html",
    )
    recorder = Recorder(responses)
    run(universe, recorder, store, filing=(DYNAMO.cik, report.accession))
    assert recorder.requested == [filing_index_url(DYNAMO.cik, report.accession)]
    with pytest.raises(ValueError, match="list no 0009990005-99-000001"):
        run(universe, recorder, store, filing=(DYNAMO.cik, "0009990005-99-000001"))
    with pytest.raises(ValueError, match="has CIK 0009990004"):
        run(universe, recorder, store, filing=("0009990004", filing.accession))


def test_issuer_filings_lists_what_the_build_reads_and_lacks(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    empty = issuer_filings(
        SavedResponses(store),
        DYNAMO.cik,
        "cik-0009990005",
        start=load_manifest(REPO / COHORT_MANIFEST).definition.period_end_start,
        cutoff=load_manifest(
            REPO / COHORT_MANIFEST
        ).definition.public_information_cutoff,
    )
    assert empty.missing == (submissions_url(DYNAMO.cik),)
    full = issuer_filings(
        SavedResponses(ArtifactStore(RAW, REPO)),
        DYNAMO.cik,
        "cik-0009990005",
        start=load_manifest(REPO / COHORT_MANIFEST).definition.period_end_start,
        cutoff=load_manifest(
            REPO / COHORT_MANIFEST
        ).definition.public_information_cutoff,
    )
    assert (full.missing, full.problems) == ((), ())


def test_stage_5_has_no_client_or_throttle_of_its_own() -> None:
    """R1.3, D5: every request goes through the shared SEC client."""
    own = re.compile(
        r"^\s*(?:import|from)\s+(?:httpx|requests|urllib|socket)\b|Throttle\(|time\.sleep",
        re.MULTILINE,
    )
    found = [
        path.name
        for path in sorted(EVENTS_PACKAGE.glob("*.py"))
        if own.search(path.read_text(encoding="utf-8"))
    ]
    assert not found


def test_a_response_saved_under_another_url_stops_discovery(
    universe, layer, tmp_path
) -> None:
    """A fetched response that is still missing would loop forever: discovery stops."""
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    recorder = Recorder(layer)
    with open_sec_client(
        environ=IDENTITY, transport=recorder.transport(), sleep=lambda seconds: None
    ) as sec:

        def astray(url: str, types: frozenset[str]):
            fetched = sec.fetch(url, types)
            moved = fetched.retrieval.model_copy(update={"request_url": f"{url}?moved"})
            return fetched.__class__(body=fetched.body, retrieval=moved)

        with pytest.raises(RuntimeError, match="was fetched, and is still missing"):
            discover(universe, astray, store)
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/tests/test_events_discover.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_discover.py -q`

Expected: FAIL: `ModuleNotFoundError: No module named 'earnings_ingestion.events.discover'`.

- [x] **Step 3: Write discovery**

Create `/tmp/plan7-task16-filings.py`:

```python
"""Plan 7: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/events/filings.py": [
        (
            "A saved response that is missing, unreadable, or for another accession is a\n"
            "problem: no review can settle it, so the build stops and lists it.\n"
            "\"\"\"\n",
            "A saved response that is missing, unreadable, or for another accession is a\n"
            "problem: no review can settle it, so the build stops and lists it. Each missing\n"
            "response's URL is also listed in ``missing``, which discovery fetches next.\n"
            "\"\"\"\n",
        ),
        (
            "    problems: tuple[str, ...]\n"
            "\n",
            "    problems: tuple[str, ...]\n"
            "    missing: tuple[str, ...]\n"
            "    \"\"\"The URLs of responses the build reads that are not saved.\"\"\"\n"
            "\n",
        ),
        (
            "        self.problems: list[str] = []\n"
            "\n",
            "        self.problems: list[str] = []\n"
            "        self.missing: list[str] = []\n"
            "\n",
        ),
        (
            "            self.problems.append(f\"nothing saved from {url}: run events discover\")\n"
            "        return artifact\n",
            "            self.problems.append(f\"nothing saved from {url}: run events discover\")\n"
            "            self.missing.append(url)\n"
            "        return artifact\n",
        ),
        (
            "                        )\n"
            "    return IssuerFilings(\n",
            "                        )\n"
            "                        reader.missing.append(url)\n"
            "    return IssuerFilings(\n",
        ),
        (
            "        problems=tuple(reader.problems),\n"
            "    )\n",
            "        problems=tuple(reader.problems),\n"
            "        missing=tuple(reader.missing),\n"
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

Apply `task16-filings`.

Create `packages/earnings-ingestion/src/earnings_ingestion/events/discover.py`:

```python
"""Discovery: save every SEC response the event build reads, through the shared SEC
client (the Stage 5 spec, §Store, client, and readers; EV2; plan 7, P7-9, P7-10).

``discover(universe, fetch, store)`` takes ``fetch``, the shared client's
``SecClient.fetch``, and saves each response in ``store`` under ``sec-edgar``. Only
the CLI opens the client (P6-22). It fetches only what ``store`` lacks, so a rerun
resumes where a stopped run left off. Each phase reads what the one before saved:

1. each candidate issuer's submissions file and companyfacts file;
2. what ``issuer_filings`` reads and finds missing, until nothing is: each older page
   whose dates meet ``[start, cutoff]``, then the index page of every Item 2.02 8-K
   and 8-K/A that either convention places in that range (P7-9);
3. the primary document of every candidate that ``release-id/1`` finds.

So discovery fetches exactly what the build reads, and never an exhibit (EV2).

``discover_filing`` saves one filing's index page, and an 8-K's or 8-K/A's primary
document. It is the remedy for an ``acceptance_time_unknown`` finding, and for a
``set_release_filing`` that names a filing discovery did not read.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.filings import RELEASE_FORMS, issuer_filings
from earnings_ingestion.events.release import identify
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import issuer_slots
from earnings_ingestion.fetch.client import Fetched
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.companyfacts import read_companyfacts
from earnings_ingestion.sec.urls import (
    archive_url,
    companyfacts_url,
    filing_index_url,
    submissions_url,
)

type Fetch = Callable[[str, frozenset[str]], Fetched]
JSON = frozenset({"application/json"})
HTML = frozenset({"text/html"})
DOCUMENT = frozenset({"text/html", "text/plain"})
"""A primary document may be plain text; ``release-id/1`` then reports it unread."""


@dataclass
class Discovery:
    """What a discovery run requested, in order."""

    fetched: list[str] = field(default_factory=list)


class _Run:
    def __init__(
        self, fetch: Fetch, store: ArtifactStore, say: Callable[[str], None]
    ) -> None:
        self.fetch, self.store, self.say = fetch, store, say
        self.result = Discovery()

    def phase(self, name: str, wanted: Iterable[tuple[str, frozenset[str]]]) -> int:
        """Fetch what ``wanted`` names and the store lacks; return how many."""
        saved = SavedResponses(self.store)
        todo = {url: types for url, types in wanted if url not in saved}
        self.say(f"{name}: {len(todo)} to fetch")
        for url, types in todo.items():
            if url in self.result.fetched:
                raise RuntimeError(f"{url} was fetched, and is still missing")
            fetched = self.fetch(url, types)
            self.store.put(
                SEC_SOURCE_ID,
                fetched.body,
                fetched.retrieval,
                rights_status=SEC_RIGHTS.rights_status,
                rights_basis=SEC_RIGHTS.rights_basis,
            )
            self.result.fetched.append(url)
        return len(todo)


def discover(
    universe: UniverseManifest,
    fetch: Fetch,
    store: ArtifactStore,
    *,
    say: Callable[[str], None] = lambda line: None,
) -> Discovery:
    """Save every response the event build reads for ``universe``'s candidates.
    ``say`` hears each phase's count before it is fetched."""
    definition = universe.definition
    start, stop = definition.period_end_start, definition.period_end_stop
    cutoff = definition.public_information_cutoff
    ciks = {issuer.issuer_id: issuer.cik for issuer in universe.issuers}
    issuers = [(i, ciks[i]) for i in sorted(universe.candidate_issuer_ids)]
    run = _Run(fetch, store, say)

    run.phase(
        "submissions and companyfacts",
        [
            (url, JSON)
            for _, cik in issuers
            for url in (submissions_url(cik), companyfacts_url(cik))
        ],
    )
    while True:
        saved = SavedResponses(store)
        missing = [
            url
            for issuer_id, cik in issuers
            for url in issuer_filings(
                saved, cik, issuer_id, start=start, cutoff=cutoff
            ).missing
        ]
        wanted = [(url, JSON if url.endswith(".json") else HTML) for url in missing]
        if not run.phase("older pages and index pages", wanted):
            break

    saved = SavedResponses(store)
    documents = []
    for issuer_id, cik in issuers:
        filings = issuer_filings(saved, cik, issuer_id, start=start, cutoff=cutoff)
        facts = saved.get(companyfacts_url(cik))
        if filings.registrant is None or facts is None:
            continue
        made, _ = issuer_slots(
            filings,
            read_companyfacts(facts.text.body),
            issuer_id,
            start=start,
            stop=stop,
        )
        for slot in made:
            found = identify(slot, filings.releases, saved, cutoff=cutoff)
            for candidate in found.candidates:
                filing = candidate.placed.filing
                url = archive_url(cik, filing.accession, filing.primary_document)
                documents.append((url, DOCUMENT))
    run.phase("primary documents", documents)
    return run.result


def discover_filing(
    universe: UniverseManifest,
    cik: str,
    accession: str,
    fetch: Fetch,
    store: ArtifactStore,
    *,
    say: Callable[[str], None] = lambda line: None,
) -> Discovery:
    """Save one filing's index page, and its primary document if it is an 8-K or
    8-K/A. The issuer's saved submissions must list it."""
    named = [issuer.issuer_id for issuer in universe.issuers if issuer.cik == cik]
    if not named:
        raise ValueError(
            f"no issuer of {universe.definition.universe_id} has CIK {cik}"
        )
    definition = universe.definition
    filings = issuer_filings(
        SavedResponses(store),
        cik,
        named[0],
        start=definition.period_end_start,
        cutoff=definition.public_information_cutoff,
    )
    listed = [
        f for file in filings.files for f in file.filings if f.accession == accession
    ]
    if not listed:
        raise ValueError(
            f"the saved filings of CIK {cik} list no {accession}: run events discover"
        )
    filing = listed[0]
    wanted = [(filing_index_url(cik, accession), HTML)]
    if filing.form in RELEASE_FORMS:
        wanted.append((archive_url(cik, accession, filing.primary_document), DOCUMENT))
    run = _Run(fetch, store, say)
    run.phase(f"{filing.form} {accession}", wanted)
    return run.result
```

Extract it with `python3 /tmp/plan7-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/discover.py`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_discover.py -q`

Expected: `6 passed`.

- [x] **Step 5: Name companyfacts in the register, and check v1**

Create `/tmp/plan7-task16-register.py`:

```python
"""Plan 7: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/source-register.toml": [
        (
            "SEC's company ticker list (www.sec.gov/files/company_tickers.json), submissions JSON \\\n"
            "(data.sec.gov/submissions/), filing index pages, and filed documents, N-PORT reports included. \\\n"
            "Every package request goes through the shared SEC client, earnings_ingestion.sec.client (R1.3, \\\n",
            "SEC's company ticker list (www.sec.gov/files/company_tickers.json), submissions JSON \\\n"
            "(data.sec.gov/submissions/), companyfacts JSON (data.sec.gov/api/xbrl/companyfacts/), filing \\\n"
            "index pages, and filed documents, N-PORT reports included. \\\n"
            "Every package request goes through the shared SEC client, earnings_ingestion.sec.client (R1.3, \\\n",
        ),
        (
            "press-release exhibits. Stage 4 reads the company ticker list, which maps current tickers to CIKs, \\\n"
            "registrants' submissions records, and a fund's N-PORT holdings reports.\"\"\"\n"
            "expected_update_pattern = \"\"\"Filings arrive as the SEC accepts them. Amendments and corrections \\\n",
            "press-release exhibits. Stage 4 reads the company ticker list, which maps current tickers to CIKs, \\\n"
            "registrants' submissions records, and a fund's N-PORT holdings reports. Stage 5 reads \\\n"
            "registrants' submissions records and companyfacts, and the index pages and primary documents of \\\n"
            "their Item 2.02 8-Ks, before any release exhibit.\"\"\"\n"
            "expected_update_pattern = \"\"\"Filings arrive as the SEC accepts them. Amendments and corrections \\\n",
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

Apply `task16-register`.

```bash
uv run --locked --all-packages python expirements/parser-fidelity/fetch_policy_pages.py verify
uv run --locked --all-packages python -c "from pathlib import Path; from earnings_ingestion.cohort.build import build; from earnings_ingestion.cohort.freeze import load_manifest; from earnings_ingestion.cohort.identity import operative_hash; v1 = load_manifest(Path('config/universe/djia/manifests/djia-2024q3-2026q2-v1.json')); built = build(Path.cwd()); print(built.content_hash, v1.definition.content_hash); print(operative_hash(built.manifest(1, v1.definition.created_at)) == operative_hash(v1), operative_hash(v1))"
```

Expected: `register quotes verified`; then
`7cb92fe437e6a325c9e3517be07f7b1274876af0c9d9954940e498441f8b1733 2d9743945dc5748fccec4c4963f6fa891a41e8863d56e99841569ff25fa884b4`,
and `True c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573`.

The second command reads `data/raw/cohort/` and sends no request. If the first hash
equals v1's, the register edit did not apply. If the operative hashes differ, stop and
ask: v1's facts would have changed.

- [x] **Step 6: Run the checks**

```bash
python3 /tmp/plan7-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/*.py packages/earnings-ingestion/tests/test_events_discover.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1247 passed, 24 deselected`; `280 passed`;
`All checks passed!` and `248 files already formatted`.

- [x] **Step 7: Commit**

```bash
git log --oneline -3
git add docs/source-register.toml packages/earnings-ingestion/src/earnings_ingestion/events/filings.py packages/earnings-ingestion/src/earnings_ingestion/events/discover.py packages/earnings-ingestion/tests/test_events_discover.py
git commit -m "feat(events): discover through the shared SEC client, fetching what the build reads"
```

---

### Task 17: The `events` commands

This task implements S §Commands, as an `events` group in `apps/earnings-pipeline`
(P6-22). P7-18 records the names and flags the plan settles:

```text
earnings-pipeline events [--repo] [--universe-dir] [--corpus-dir] [--store] [--corpus-id]
    discover --max-requests N            # the shared SEC client
    discover --filing CIK ACCESSION      # at most 2 requests
    build                                # exit 1 while anything holds the freeze
    freeze
    select
```

- **The defaults** are the real corpus's:
  - `--universe-dir` is `config/universe/djia/manifests`, which holds one universe's
    versions, the latest of which is read;
  - `--corpus-dir` is `config/corpus/djia-2024q3-2026q2`;
  - `--store` is `data/raw/events`;
  - `--corpus-id` is `djia-2024q3-2026q2`.

  The tests point them at the synthetic corpus.
- **`discover`** needs `--max-requests`, the count the user approved at Gate 1, and
  opens the shared client with that cap. It states the cap before it sends anything,
  and each phase's count before that phase. It ends with what it fetched and how many
  requests it sent. A stop (a persistent 403, a spent budget, an unexpected response,
  or a refusal) prints the requests sent and that a rerun fetches only what is
  missing, and exits 1. `--filing` caps itself at 2.
- **`build`** prints Task 12's report. Then it prints each blocking finding's digest,
  which an `acknowledge` must name, as `cohort build` does. It ends with a summary,
  and exits 1 while anything holds the freeze. A problem prints `problem:` lines and
  exits 1.
- **`freeze`** prints `froze` or `unchanged:`, the manifest's path and hash, and its
  evidence record's path. A refusal prints each reason as `HOLDS` and exits 1.
- **`select`** reads the latest frozen event manifest, and the universe version it
  read. It prints the rows in order, then each reported transition, then the pilot's
  version, target, and path. A refusal prints `Refused:` and exits 1.

**Files:**

- Create: `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py`.
- Modify, by exact replacement: `apps/earnings-pipeline/src/earnings_pipeline/cli.py`.
- Test (create): `apps/earnings-pipeline/tests/test_events_cli.py`.

**Interfaces:**

- Consumes:
  - Tasks 12 to 16's `build_events`, `load_overrides`, `EventBuildError`,
    `freeze_events`, `EventFreezeRefused`, `frozen_event_manifests`, `select_pilot`,
    `freeze_pilot`, `discover`, and `discover_filing`;
  - Task 15's fixture;
  - Stage 4's `open_sec_client`, `load_manifest`, and `UNIVERSE_DIR`.
- Produces `earnings_pipeline.events_cli.events`, a `typer.Typer` that `cli.app`
  mounts as `events`. Tasks 19, 20, and 21 run its commands.

- [x] **Step 1: Write the failing tests**

Create `apps/earnings-pipeline/tests/test_events_cli.py`:

```python
"""``earnings-pipeline events`` on the committed synthetic event corpus. ``discover``
runs the shared SEC client over a transport that serves the corpus's saved
responses, so no request leaves the process."""

import shutil
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.fixture import COHORT_MANIFEST, FIXTURE_DIR
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec import client as sec_client
from earnings_pipeline import cli, events_cli
from typer.testing import CliRunner

RUNNER = CliRunner()
REPO = Path(__file__).resolve().parents[3]
UNIVERSES = COHORT_MANIFEST.parent
IDENTITY = {"EDGAR_IDENTITY": "Plan 7 synthetic discovery test@example.com"}
EVENTS_HASH = "438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58"
PILOT_HASH = "71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """The synthetic cohort's manifests and the event corpus, at their paths."""
    for directory in (UNIVERSES, FIXTURE_DIR):
        shutil.copytree(REPO / directory, tmp_path / directory)
    return tmp_path


def run(repo: Path, *args: str, store: Path = FIXTURE_DIR / "raw"):
    layout = [
        "events",
        "--repo",
        str(repo),
        "--universe-dir",
        str(UNIVERSES),
        "--corpus-dir",
        str(FIXTURE_DIR),
        "--store",
        str(store),
        "--corpus-id",
        "djia-synthetic",
    ]
    return RUNNER.invoke(cli.app, [*layout, *args])


def test_build_prints_every_event_and_passes_when_nothing_holds(repo) -> None:
    result = run(repo, "build")
    assert result.exit_code == 0, result.output
    assert (
        "cik-0009990001:2025-02-28  eligible  member_at_publication"
        "  0009990001-25-000008 (override)"
    ) in result.stdout
    assert "[acknowledged by gap-corvid]" in result.stdout
    assert result.stdout.splitlines()[-1] == (
        f"32 events, 27 eligible, content {EVENTS_HASH}"
    )


def test_build_fails_and_prints_digests_while_anything_holds(repo) -> None:
    (repo / FIXTURE_DIR / "overrides.toml").unlink()
    result = run(repo, "build")
    assert result.exit_code == 1
    assert (
        "acknowledge period_gap:cik-0009990003:2024-07-01:2024-12-31 with digest"
        " b6787303110f5ad9967e93c6140a79db0425d1ac99e4a67d3a67a82fd77f200e"
    ) in result.stdout
    assert "cik-0009990005:2025-06-27: no_release_filing, not retained" in (
        result.stdout
    )


def test_freeze_names_the_version_that_holds_the_content(repo) -> None:
    result = run(repo, "freeze")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [
        "unchanged: djia-synthetic v1",
        f"tests/fixtures/events/events-v1.json  {EVENTS_HASH}",
        "tests/fixtures/events/events-v1.evidence.json",
    ]


def test_freeze_refuses_and_names_what_holds(repo) -> None:
    (repo / FIXTURE_DIR / "overrides.toml").unlink()
    result = run(repo, "freeze")
    assert result.exit_code == 1
    assert "HOLDS  period_gap:cik-0009990002:2025-03-31:2026-07-01: " in result.stderr
    assert "HOLDS  cik-0009990002:2024-09-30: same_day_transition, not retained" in (
        result.stderr
    )


def test_select_names_the_pilot_that_holds_the_selection(repo) -> None:
    result = run(repo, "select")
    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines[0] == "  1  cik-0009990003:2026-03-31  issuer_coverage"
    assert lines[27] == (
        "reported: cik-0009990002's exit on 2024-11-08 has no eligible event on its"
        " member side"
    )
    assert lines[28:] == [
        "unchanged: djia-synthetic-pilot v1: 27 of target 27, underfilled",
        f"tests/fixtures/events/pilot-v1.json  {PILOT_HASH}",
    ]


def test_select_refuses_without_a_frozen_event_manifest(repo) -> None:
    for name in ("events-v1.json", "events-v1.evidence.json", "pilot-v1.json"):
        (repo / FIXTURE_DIR / name).unlink()
    result = run(repo, "select")
    assert result.exit_code == 1
    assert "Refused: no frozen event manifest in tests/fixtures/events" in (
        result.stderr
    )


def served() -> dict[str, tuple[bytes, str]]:
    root = REPO / FIXTURE_DIR / "raw"
    store = ArtifactStore(root, REPO)
    found = {}
    for path in sorted((root / SEC_SOURCE_ID / "retrievals").glob("*/*.json")):
        record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
        stored = store.get(
            SEC_SOURCE_ID,
            record.sha256,
            rights_status=SEC_RIGHTS.rights_status,
            rights_basis=SEC_RIGHTS.rights_basis,
        )
        found[record.request_url] = (stored.body, record.media_type)
    return found


def client(monkeypatch, responses: dict[str, tuple[bytes, str]], status: int = 200):
    """Replace the CLI's client with the shared client over a serving transport."""
    budgets: list[int] = []

    def handle(request: httpx.Request) -> httpx.Response:
        body, media_type = responses.get(str(request.url), (b"", "text/plain"))
        code = status if str(request.url) in responses else 404
        return httpx.Response(code, content=body, headers={"content-type": media_type})

    @contextmanager
    def opened(*, max_requests: int):
        budgets.append(max_requests)
        with sec_client.open_sec_client(
            environ=IDENTITY,
            transport=httpx.MockTransport(handle),
            sleep=lambda seconds: None,
            max_requests=max_requests,
        ) as sec:
            yield sec

    monkeypatch.setattr(events_cli, "open_sec_client", opened)
    return budgets


def test_discover_states_its_budget_first_and_each_phase(repo, monkeypatch) -> None:
    budgets = client(monkeypatch, served())
    result = run(
        repo, "discover", "--max-requests", "90", store=Path("data/raw/events")
    )
    assert result.exit_code == 0, result.output
    assert budgets == [90]
    assert result.stdout.splitlines() == [
        "at most 90 requests to SEC, through the shared client",
        "submissions and companyfacts: 10 to fetch",
        "older pages and index pages: 38 to fetch",
        "older pages and index pages: 2 to fetch",
        "older pages and index pages: 0 to fetch",
        "primary documents: 34 to fetch",
        "fetched 84; requests sent: 84",
    ]


def test_discover_needs_the_approved_count(repo, monkeypatch) -> None:
    budgets = client(monkeypatch, served())
    result = run(repo, "discover", store=Path("data/raw/events"))
    assert result.exit_code == 1
    assert budgets == []
    assert "Refused: pass --max-requests" in result.stderr


def test_discover_stops_on_a_persistent_403_and_says_how_to_resume(
    repo, monkeypatch
) -> None:
    client(monkeypatch, served(), status=403)
    result = run(
        repo, "discover", "--max-requests", "90", store=Path("data/raw/events")
    )
    assert result.exit_code == 1
    assert "Stopped: " in result.stderr and "403" in result.stderr
    assert "a rerun fetches only what is missing" in result.stdout


def test_discover_filing_spends_at_most_two_requests(repo, monkeypatch) -> None:
    budgets = client(monkeypatch, served())
    result = run(repo, "discover", "--filing", "0009990005", "0009990005-99-000001")
    assert result.exit_code == 1
    assert budgets == [2]
    assert "Stopped: the saved filings of CIK 0009990005 list no" in result.stderr
```

Extract it with `python3 /tmp/plan7-extract.py apps/earnings-pipeline/tests/test_events_cli.py`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_events_cli.py -q`

Expected: FAIL: `ImportError: cannot import name 'events_cli' from 'earnings_pipeline'`.

- [x] **Step 3: Write the commands**

Create `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py`:

```python
"""``earnings-pipeline events``: discover, build, and freeze Stage 5's event manifest,
and select and freeze its pilot (plan 7, P7-18).

    earnings-pipeline events discover --max-requests N    # the shared SEC client
    earnings-pipeline events discover --filing CIK ACCESSION
    earnings-pipeline events build
    earnings-pipeline events freeze
    earnings-pipeline events select

Only ``discover`` uses the network, through the shared SEC client. It states its
request budget before it sends anything, and each phase's count before that phase,
and a rerun fetches only what the store lacks. ``build``, ``freeze``, and ``select``
read committed files and saved responses alone. ``build`` exits 1 while anything
holds the freeze.

The universe is the latest frozen manifest in ``--universe-dir``, which holds one
universe's versions; ``select`` reads the version its event manifest read.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from earnings_ingestion.cohort.config import UNIVERSE_DIR
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.build import (
    CORPUS_DIR,
    CORPUS_ID,
    EVENTS_STORE,
    EventBuild,
    EventBuildError,
    build_events,
    load_overrides,
)
from earnings_ingestion.events.discover import discover, discover_filing
from earnings_ingestion.events.freeze import (
    EventFreezeRefused,
    freeze_events,
    frozen_event_manifests,
)
from earnings_ingestion.events.pilot import freeze_pilot, select_pilot
from earnings_ingestion.events.records import EventStatus
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.client import AccessStop, UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.client import open_sec_client

events = typer.Typer(
    no_args_is_help=True, help="Stage 5's events: discovery, eligibility, the pilot."
)


@dataclass(frozen=True)
class Layout:
    repo: Path
    universe_dir: Path
    corpus_dir: Path
    store_root: Path
    corpus_id: str

    def store(self) -> ArtifactStore:
        return ArtifactStore(self.repo / self.store_root, self.repo)

    def corpus(self) -> Path:
        return self.repo / self.corpus_dir

    def universes(self) -> list[UniverseManifest]:
        """Every frozen version in ``universe_dir``, oldest first."""
        found = [
            load_manifest(path)
            for path in sorted((self.repo / self.universe_dir).glob("*-v*.json"))
        ]
        if len({m.definition.universe_id for m in found}) > 1:
            _fail(f"Refused: {self.universe_dir} holds more than one universe")
        if not found:
            _fail(f"Refused: {self.universe_dir} holds no frozen universe")
        return sorted(found, key=lambda m: m.definition.universe_version)


@events.callback()
def main(
    context: typer.Context,
    repo: Annotated[Path, typer.Option(help="The repository root.")] = Path(),
    universe_dir: Annotated[
        Path, typer.Option(help="The frozen universe's manifests.")
    ] = UNIVERSE_DIR / "manifests",
    corpus_dir: Annotated[
        Path, typer.Option(help="Overrides and frozen manifests.")
    ] = CORPUS_DIR,
    store: Annotated[Path, typer.Option(help="The saved responses.")] = EVENTS_STORE,
    corpus_id: Annotated[str, typer.Option(help="The corpus.")] = CORPUS_ID,
) -> None:
    """Paths are relative to --repo; the defaults are the real corpus's."""
    context.obj = Layout(repo.resolve(), universe_dir, corpus_dir, store, corpus_id)


def _fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(1)


@events.command("discover")
def discover_command(
    context: typer.Context,
    max_requests: Annotated[
        int | None,
        typer.Option(help="The request count approved at the gate; the client's cap."),
    ] = None,
    filing: Annotated[
        tuple[str, str] | None,
        typer.Option(help="CIK ACCESSION: one filing's index page and 8-K document."),
    ] = None,
) -> None:
    """Save what the build reads from SEC, through the shared SEC client."""
    layout: Layout = context.obj
    universe = layout.universes()[-1]
    budget = 2 if filing is not None else max_requests
    if budget is None:
        _fail("Refused: pass --max-requests, the request count the user approved")
    typer.echo(f"at most {budget} requests to SEC, through the shared client")
    sent = 0
    try:
        with open_sec_client(max_requests=budget) as sec:
            try:
                if filing is not None:
                    result = discover_filing(
                        universe, *filing, sec.fetch, layout.store(), say=typer.echo
                    )
                else:
                    result = discover(
                        universe, sec.fetch, layout.store(), say=typer.echo
                    )
            finally:
                sent = sec.throttle.count
    except (AccessStop, UnexpectedResponse, ValueError, RuntimeError) as error:
        typer.echo(f"requests sent: {sent}; a rerun fetches only what is missing")
        _fail(f"Stopped: {error}")
    typer.echo(f"fetched {len(result.fetched)}; requests sent: {sent}")


def _build(layout: Layout) -> tuple[EventBuild, SavedResponses]:
    saved = SavedResponses(layout.store())
    try:
        built = build_events(
            layout.universes()[-1],
            saved,
            load_overrides(layout.corpus() / "overrides.toml"),
            corpus_id=layout.corpus_id,
        )
    except EventBuildError as error:
        for problem in error.problems:
            typer.echo(f"problem: {problem}", err=True)
        raise typer.Exit(1) from error
    return built, saved


@events.command("build")
def build_command(context: typer.Context) -> None:
    """Build offline; print every row, candidate, and finding, and what holds the
    freeze, with each blocking finding's digest."""
    built, _ = _build(context.obj)
    for line in built.report():
        typer.echo(line)
    for finding in built.blocking:
        typer.echo(f"acknowledge {finding.finding_id} with digest {finding.digest}")
    eligible = [r for r in built.rows if r.eligibility_status is EventStatus.ELIGIBLE]
    typer.echo(
        f"{len(built.rows)} events, {len(eligible)} eligible,"
        f" content {built.content_hash}"
    )
    if built.holds_freeze:
        raise typer.Exit(1)


@events.command("freeze")
def freeze_command(context: typer.Context) -> None:
    """Freeze the event manifest and its evidence, or name the version holding it."""
    layout: Layout = context.obj
    built, saved = _build(layout)
    try:
        frozen = freeze_events(built, saved, layout.corpus(), now=datetime.now(UTC))
    except EventFreezeRefused as error:
        for reason in error.reasons:
            typer.echo(f"HOLDS  {reason}", err=True)
        raise typer.Exit(1) from error
    definition = frozen.manifest.definition
    verb = "froze" if frozen.created else "unchanged:"
    typer.echo(f"{verb} {definition.corpus_id} v{definition.event_manifest_version}")
    typer.echo(f"{frozen.path.relative_to(layout.repo)}  {definition.content_hash}")
    typer.echo(f"{frozen.evidence_path.relative_to(layout.repo)}")


@events.command("select")
def select_command(context: typer.Context) -> None:
    """Run djia-pilot/1 on the latest frozen event manifest, and freeze the pilot."""
    layout: Layout = context.obj
    manifests = frozen_event_manifests(layout.corpus())
    if not manifests:
        _fail(f"Refused: no frozen event manifest in {layout.corpus_dir}")
    frozen_events = manifests[-1]
    read = frozen_events.definition
    matching = [
        m
        for m in layout.universes()
        if (m.definition.universe_id, m.definition.universe_version)
        == (read.universe_id, read.universe_version)
    ]
    if not matching:
        _fail(
            f"Refused: {layout.universe_dir} holds no {read.universe_id}"
            f" v{read.universe_version}, which the event manifest read"
        )
    universe = matching[0]
    try:
        pilot = select_pilot(frozen_events, universe)
        frozen = freeze_pilot(pilot, universe, layout.corpus(), now=datetime.now(UTC))
    except ValueError as error:
        _fail(f"Refused: {error}")
    manifest = frozen.manifest
    for row in manifest.rows:
        typer.echo(f"{row.selection_order:>3}  {row.event_id}  {row.selection_reason}")
    for transition in manifest.unmatched_transitions:
        typer.echo(
            f"reported: {transition.issuer_id}'s {transition.kind} on"
            f" {transition.effective_date} has no eligible event on its member side"
        )
    definition = manifest.definition
    verb = "froze" if frozen.created else "unchanged:"
    filled = ", underfilled" if definition.underfilled else ""
    typer.echo(
        f"{verb} {definition.pilot_id} v{definition.pilot_version}:"
        f" {len(manifest.rows)} of target {definition.target}{filled}"
    )
    typer.echo(f"{frozen.path.relative_to(layout.repo)}  {definition.content_hash}")
```

Extract it with `python3 /tmp/plan7-extract.py apps/earnings-pipeline/src/earnings_pipeline/events_cli.py`.

Create `/tmp/plan7-task17-cli.py`:

```python
"""Plan 7: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/src/earnings_pipeline/cli.py": [
        (
            "    uv run --locked --all-packages earnings-pipeline cohort --help\n"
            "\n",
            "    uv run --locked --all-packages earnings-pipeline cohort --help\n"
            "    uv run --locked --all-packages earnings-pipeline events --help\n"
            "\n",
        ),
        (
            "into a cache outside the repository; a capture never downloads anything. ``cohort``\n"
            "holds Stage 4's commands (``earnings_pipeline.cohort_cli``).\n"
            "\"\"\"\n",
            "into a cache outside the repository; a capture never downloads anything. ``cohort``\n"
            "holds Stage 4's commands (``earnings_pipeline.cohort_cli``), and ``events`` Stage 5's\n"
            "(``earnings_pipeline.events_cli``).\n"
            "\"\"\"\n",
        ),
        (
            "from earnings_pipeline.cohort_cli import cohort\n"
            "\n",
            "from earnings_pipeline.cohort_cli import cohort\n"
            "from earnings_pipeline.events_cli import events\n"
            "\n",
        ),
        (
            "app.add_typer(cohort, name=\"cohort\")\n"
            "\n",
            "app.add_typer(cohort, name=\"cohort\")\n"
            "app.add_typer(events, name=\"events\")\n"
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

Apply `task17-cli`.

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_events_cli.py -q`

Expected: `10 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan7-escapes.py apps/earnings-pipeline/src/earnings_pipeline/*.py apps/earnings-pipeline/tests/test_events_cli.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages earnings-pipeline events --help
```

Expected: `escapes intact`; `1257 passed, 24 deselected`; `All checks passed!` and
`250 files already formatted`; the help lists `discover`, `build`, `freeze`, and
`select`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/tests/test_events_cli.py
git commit -m "feat(pipeline): add the events commands: discover, build, freeze, and select"
```

---

### Task 18: The R14.5 import boundary

This task implements S §R14.5 and SV13. Stage 5 uses no acquisition library:
edgartools stays an unused optional extra, and the readers are the package's own. So
no library's output reaches the ingestion boundary, and there is nothing to cast.
Task 22's record says exactly that, and does not call R14.5 vacuous, because V1 found
that edgartools' paths would need casts.

- **At runtime** (`test_import_boundaries.py`), a fresh interpreter imports each of
  Stage 5's modules. None may load `edgar`, `pandas`, or `pyarrow`, or anything the
  file already forbids. Every module but `discover` must also load no network client:
  building, freezing, and selecting read saved responses (A §410). `discover` takes
  the shared client's `fetch`, and loads `fetch.client` for its `Fetched` type.
- **Statically** (`test_import_scan.py`), `ast` reads Stage 5's source, so an import
  inside a function cannot escape. The source covered is `events/*.py`,
  `sec/companyfacts.py`, `sec/filing_index.py`, `cohort/identity.py`, and the app's
  `events_cli.py`.
- **No red run.** The tests guard a property Tasks 3 to 17 already keep, so they pass
  at once. Step 3 shows that they fail when the property breaks: at plan time,
  appending `import pyarrow` to `events/records.py` made the scan name
  `records.py:520`, and failed 12 runtime cases, one for each module that imports the
  records. Of the three libraries, only pyarrow is installed in this environment,
  which is why the scan is the check that cannot be dodged.

**Files:**

- Modify, by exact replacement: `packages/earnings-ingestion/tests/test_import_boundaries.py`
  and `tests/contracts/test_import_scan.py`.

**Interfaces:**

- Consumes: the modules of Tasks 3 to 17.
- Produces: no code. Task 22's record cites these tests for SV 13.

- [x] **Step 1: Write the tests**

Create `/tmp/plan7-task18-boundaries.py`:

```python
"""Plan 7: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/tests/test_import_boundaries.py": [
        (
            "manifest, loads no network client (A §410), and neither does pdftext-1's PDF reader.\n"
            "\"\"\"\n",
            "manifest, loads no network client (A §410), and neither does pdftext-1's PDF reader.\n"
            "\n"
            "Stage 5 loads no acquisition library (R14.5): its readers are the package's own, so\n"
            "no edgartools, pandas, or pyarrow object reaches the ingestion boundary, and there is\n"
            "nothing to cast. Its offline path, from saved responses to the frozen pilot, loads no\n"
            "network client; only discovery, which takes the shared client's ``fetch``, does.\n"
            "\"\"\"\n",
        ),
        (
            "    assert full_modules_loaded_by(module) & NETWORK == set()\n",
            "    assert full_modules_loaded_by(module) & NETWORK == set()\n"
            "\n"
            "\n"
            "ACQUISITION = {\"edgar\", \"pandas\", \"pyarrow\"}\n"
            "EVENTS = [\n"
            "    \"earnings_ingestion.events.acceptance\",\n"
            "    \"earnings_ingestion.events.build\",\n"
            "    \"earnings_ingestion.events.eligibility\",\n"
            "    \"earnings_ingestion.events.evidence\",\n"
            "    \"earnings_ingestion.events.filings\",\n"
            "    \"earnings_ingestion.events.fixture\",\n"
            "    \"earnings_ingestion.events.freeze\",\n"
            "    \"earnings_ingestion.events.layer\",\n"
            "    \"earnings_ingestion.events.pilot\",\n"
            "    \"earnings_ingestion.events.records\",\n"
            "    \"earnings_ingestion.events.release\",\n"
            "    \"earnings_ingestion.events.saved\",\n"
            "    \"earnings_ingestion.events.slots\",\n"
            "    \"earnings_ingestion.events.synthetic\",\n"
            "    \"earnings_ingestion.sec.companyfacts\",\n"
            "    \"earnings_ingestion.sec.filing_index\",\n"
            "    \"earnings_ingestion.cohort.identity\",\n"
            "]\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\"module\", [*EVENTS, \"earnings_ingestion.events.discover\"])\n"
            "def test_stage_5_loads_no_acquisition_library(module: str) -> None:\n"
            "    \"\"\"R14.5: no edgartools, pandas, or pyarrow output crosses the boundary.\"\"\"\n"
            "    assert modules_loaded_by(module) & (ACQUISITION | FORBIDDEN) == set()\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\"module\", EVENTS)\n"
            "def test_the_offline_event_path_loads_no_network_client(module: str) -> None:\n"
            "    \"\"\"Building, freezing, and selecting read saved responses (A §410).\"\"\"\n"
            "    assert full_modules_loaded_by(module) & NETWORK == set()\n",
        ),
    ],
    "tests/contracts/test_import_scan.py": [
        (
            "  ``earnings_ingestion.browser.selenium_capture``, the one adapter behind the\n"
            "  ``browser-capture`` extra.\n"
            "\"\"\"\n",
            "  ``earnings_ingestion.browser.selenium_capture``, the one adapter behind the\n"
            "  ``browser-capture`` extra;\n"
            "- an acquisition library (edgartools, pandas, pyarrow) in any of Stage 5's modules\n"
            "  (R14.5).\n"
            "\"\"\"\n",
        ),
        (
            "    assert any(module.startswith(\"selenium\") for _, module in imported(ADAPTER))\n",
            "    assert any(module.startswith(\"selenium\") for _, module in imported(ADAPTER))\n"
            "\n"
            "\n"
            "ACQUISITION = frozenset({\"edgar\", \"pandas\", \"pyarrow\"})\n"
            "\n"
            "\n"
            "def test_stage_5_imports_no_acquisition_library() -> None:\n"
            "    \"\"\"R14.5: Stage 5's readers are the package's own, so no acquisition library's\n"
            "    output reaches the ingestion boundary, and there is nothing to cast.\"\"\"\n"
            "    ingestion = SOURCES[\"earnings_ingestion\"]\n"
            "    paths = [\n"
            "        *sorted((ingestion / \"events\").glob(\"*.py\")),\n"
            "        ingestion / \"sec\" / \"companyfacts.py\",\n"
            "        ingestion / \"sec\" / \"filing_index.py\",\n"
            "        ingestion / \"cohort\" / \"identity.py\",\n"
            "        SOURCES[\"earnings_pipeline\"] / \"events_cli.py\",\n"
            "    ]\n"
            "    assert len(paths) > 5\n"
            "    found = [\n"
            "        f\"{path.relative_to(ROOT)}:{line} imports {name}\"\n"
            "        for path in paths\n"
            "        for line, name in imported(path)\n"
            "        if name.partition(\".\")[0] in ACQUISITION\n"
            "    ]\n"
            "    assert not found\n",
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

Apply `task18-boundaries`.

- [x] **Step 2: Run the tests**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py -q`

Expected: `64 passed`.

- [x] **Step 3: See them fail when the boundary breaks, then restore**

```bash
printf 'import pyarrow\n' >> packages/earnings-ingestion/src/earnings_ingestion/events/records.py
uv run --locked --all-packages pytest tests/contracts/test_import_scan.py -q -k acquisition
uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_import_boundaries.py -q -k acquisition
git checkout -- packages/earnings-ingestion/src/earnings_ingestion/events/records.py
git status --short
```

Expected: the scan fails with
`assert not ['packages/earnings-ingestion/src/earnings_ingestion/events/records.py:520 imports pyarrow']`;
the runtime check gives `12 failed, 6 passed, 39 deselected`; then the status lists
only the two test files.

- [x] **Step 4: Run the checks**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `1293 passed, 24 deselected`; `All checks passed!` and
`250 files already formatted`.

- [x] **Step 5: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py
git commit -m "test(events): keep acquisition libraries and network clients out of Stage 5 (R14.5)"
```

---

### Task 19: Live discovery, and the acceptance-time record's second leg

This task runs S §Gates (plan A), gate 1: Stage 5's live requests. Then it meets
S §Exit criteria (plan A), item 3: the acceptance-time record, with both legs.

- **Replayed and live.** The live steps could not be replayed at planning, and their
  outputs are predictions. Step 1 runs offline on the synthetic store and was
  replayed, so its output is exact. Each step names its checks.
- **What is committed.** Discovery saves everything under the gitignored
  `data/raw/events/`, and only the record is committed.
- **Keep `discover`'s output.** Task 22's record gives its counts.

**Files:**

- Regenerate: `docs/verification/edgar-acceptance-time.md`.
- Local only: `data/raw/events/`.

**Interfaces:**

- Consumes: Task 17's `events discover`, and Task 5's record script.
- Produces:
  - Stage 5's saved responses in `data/raw/events/sec-edgar/`, which Tasks 20 and 21
    read;
  - the record's second leg.

- [x] **Step 1: Run the record's second leg offline, on the synthetic store**

Before any request, check that the record's script reads a Stage 5 store. A scratch
repository links Stage 1's pages, and the committed synthetic store in place of
`data/raw/events/`:

```bash
rm -rf /tmp/plan7-leg2 && mkdir -p /tmp/plan7-leg2/data/raw
ln -s "$PWD/data/raw/discovery" /tmp/plan7-leg2/data/raw/discovery
ln -s "$PWD/tests/fixtures/events/raw" /tmp/plan7-leg2/data/raw/events
uv run --locked --all-packages python tests/integration/regenerate_acceptance_time_record.py --repo /tmp/plan7-leg2
sed -n '/^| |/,/^$/p' docs/verification/edgar-acceptance-time.md
git checkout -- docs/verification/edgar-acceptance-time.md
rm -rf /tmp/plan7-leg2
git status --short
```

Expected, a check: `wrote docs/verification/edgar-acceptance-time.md with 2 leg(s)`,
then this table, and nothing from `git status`:

```text
| | Leg 1 | Leg 2 |
| --- | --- | --- |
| Retrieved | 2026-09-22 to 2026-09-25 | 2026-09-28 to 2026-09-28 |
| Submissions files read | 300 | 5 |
| Older pages read | 51 | 1 |
| Index pages read | 226 | 39 |
| Files with a cross-checked row | 221 | 6 |
| Rows cross-checked | 227 | 39 |
| Rows in true UTC | 143 | 25 |
| Rows in Eastern digits and Z | 84 | 14 |
| Rows in neither | 0 | 0 |
| Files in both conventions | 0 | 0 |
| Submissions files in true UTC | 96, latest filing 2026-04-09 to 2026-09-24 | 3, latest filing 2026-07-31 to 2026-08-04 |
| Submissions files in Eastern digits and Z | 76, latest filing 2008-02-14 to 2026-04-02 | 2, latest filing 2025-05-02 to 2026-09-25 |
| Older pages in true UTC | 43 | 1 |
| Older pages in Eastern digits and Z | 6 | 0 |
```

Leg 2 here is the synthetic layer's five issuers. At plan time, the script before
its fix stopped on this store with
`SecDataError: the submissions file lacks cik, name, tickers, or filings`. It had read
a companyfacts file as a submissions file, since both are named
`CIK##########.json`. If this step fails, stop: nothing should be requested until the
record can read what discovery saves.

- [x] **Step 2 (gate): Ask the user to approve discovery's requests**

Check the identity without printing it:

```bash
[ -n "$(printenv EDGAR_IDENTITY)" ] && echo "EDGAR_IDENTITY set" || echo "EDGAR_IDENTITY unset"
```

Expected: `EDGAR_IDENTITY set`. If it is unset, ask the user to set it. It is the
user's, and is configured outside Git.

Then put the request to the user, with its count:

> `earnings-pipeline events discover --max-requests 700` sends at most 700 requests
> to SEC, through the shared client, as `EDGAR_IDENTITY`, at 2 per second. That is
> about six minutes. It has three phases:
>
> 1. 63 submissions and companyfacts files: one of each for the 33 candidate
>    issuers, less the three companyfacts files the plan-time probe saved;
> 2. about 19 older pages and about 305 index pages, one for each Item 2.02 8-K and
>    8-K/A in range;
> 3. about 290 primary documents, one for each candidate, less the 16 the probe
>    saved.
>
> That is about 680 in all, and no exhibit is requested (EV2). The cap leaves a
> small margin. A run that reaches it stops, and a rerun fetches only what is
> missing, after you approve its count.

Wait for a clear yes. If the user approves another cap, use it in Step 3.

- [x] **Step 3: Run discovery**

> Deviation: predictions only; every check matched. Discovery sent 642 requests, not the 677 predicted, under the approved cap of 700: its first phase's 63 and the older-page passes' 314, 10, and 0 matched, but it fetched 255 primary documents, not 290. No retry, 403, or rerun was needed.

Run: `uv run --locked --all-packages earnings-pipeline events discover --max-requests 700`

It runs for about six minutes. Expected, a prediction whose counts are plan-time
estimates:

```text
at most 700 requests to SEC, through the shared client
submissions and companyfacts: 63 to fetch
older pages and index pages: 314 to fetch
older pages and index pages: 10 to fetch
older pages and index pages: 0 to fetch
primary documents: 290 to fetch
fetched 677; requests sent: 677
```

- **Checks.** The first line, the first phase's `63 to fetch`, and a last pass of
  phase 2 that has `0 to fetch`.
- **The first pass of phase 2.** At plan time, `issuer_filings` over Stage 4's saved
  submissions found 19 older pages and 295 index pages missing. The live files list
  newer filings, which can move filings in range from the recent block into older
  pages, so expect about 314.
- **The next pass** adds the index pages that the older pages list: Goldman Sachs'
  and JPMorgan's from 2024-07-01 until their recent blocks begin.
- **Requests sent** exceed the fetched count when the client retried a response.

If it stops:

- **A persistent 403.** The run prints `Stopped:` and the requests sent. Report both
  to the user. Never retry with another identity, and do not rerun until the user
  says so (A §404).
- **A spent budget.** The run prints the requests sent, and that a rerun fetches only
  what is missing. Ask the user to approve a rerun, with a new cap. The rerun states
  each phase's count before it sends.
- **An unexpected response,** such as a 404. Report the URL to the user. A rerun would
  request it first again, so do not rerun until the user decides.

Then check what was saved, without printing any body:

```bash
ls data/raw/events/sec-edgar | wc -l
git check-ignore data/raw/events/sec-edgar
git status --short
```

Expected:

- about `700`: the saved files, with the probe's 19, and `retrievals/`. This is a
  prediction.
- `data/raw/events/sec-edgar`, so the store is ignored. This is a check.
- nothing from `git status`. This is a check.

- [x] **Step 4: Regenerate the record with both legs**

```bash
uv run --locked --all-packages python tests/integration/regenerate_acceptance_time_record.py
sed -n '/^| |/,/^$/p' docs/verification/edgar-acceptance-time.md
tail -4 docs/verification/edgar-acceptance-time.md
```

Expected: `wrote docs/verification/edgar-acceptance-time.md with 2 leg(s)`, then the
table and the verdict.

- **Checks:**
  - leg 1's column reads exactly as Task 5's table;
  - leg 2 reads 0 for `Rows in neither` and for `Files in both conventions`;
  - the verdict begins "Every cross-checked row follows one of the two
    conventions".

  If a leg 2 row or file breaks the rule, the verdict names it. Stop, and report it
  to the user. EV10's rule does not hold there, and Task 20's build will block on it
  with `acceptance_time_mismatch`, which no override answers.
- **Predictions for leg 2:**
  - retrieved on the run's date;
  - 33 submissions files, about 19 older pages, and about 305 index pages;
  - about 305 rows cross-checked.

  S Finding 1 infers that SEC writes true UTC in every submissions file it has
  regenerated since early April 2026. Every candidate issuer has filed since then,
  so expect all 33 files in true UTC. The older pages may be in either convention.

- [x] **Step 5: Run the checks**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
git status --short
```

Expected, checks:

- `1293 passed, 24 deselected`;
- `All checks passed!` and `250 files already formatted`;
- only ` M docs/verification/edgar-acceptance-time.md`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/verification/edgar-acceptance-time.md
git commit -m "docs(events): add the acceptance-time record's second leg, from Stage 5's pages"
```

---

### Task 20: The real event manifest: build, review, and freeze

This task runs S §Gates (plan A), gate 2 and the first half of gate 3. The user
reviews what the real build reports, and approves the event manifest's freeze
(S §Review overrides; S §The event manifest).

- **The user decides.** The implementer prepares each decision, and the user makes
  it. The implementer never writes `reviewer`, and a rationale is the user's words.
- **Slots.** The templates below hold `[GATE: …]` slots. Fill each from the named
  output, and never leave one.
- **Public files.** Everything under `config/corpus/djia-2024q3-2026q2/` is
  committed, and the repository is public. The files hold facts, URLs, hashes, and
  locators, never a filing's wording (P6-3). Steps 3 and 6 check it.
- **Predictions.** Task 9's plan-time reading predicts the quarters that go to review,
  and S Finding 3 predicts the counts: about 263 events, about 239 of them eligible.
  The helpers were replayed on the synthetic corpus, and their outputs there are
  exact.

**Files:**

- Create: `config/corpus/djia-2024q3-2026q2/overrides.toml`, unless the review needs
  no override.
- Create (generated): `config/corpus/djia-2024q3-2026q2/events-v1.json` and
  `events-v1.evidence.json`.
- Local only: `data/raw/events/`, if a `--filing` run adds to it.

**Interfaces:**

- Consumes:
  - Task 19's saved responses;
  - Task 17's `events build`, `events freeze`, and `events discover --filing`;
  - Stage 4's `earnings-pipeline cohort cite`;
  - Task 15's `write_overrides`, if the overrides are written from records.
- Produces the real event manifest. Task 21's `events select` reads it, and plan B
  and Stage 15 load it:

  ```python
  from pathlib import Path

  from earnings_ingestion.events.freeze import load_event_manifest

  load_event_manifest(Path("config/corpus/djia-2024q3-2026q2/events-v1.json"))
  ```

- [x] **Step 1: Build, and read the report**

> Deviation: predictions only; no `problem:` line or acceptance-time finding arose, and the 263 events, the 24 ineligible ones, and the absence of `period_gap` matched. The build found 12 `ambiguous` events, not 3, so 227 `eligible`, not 236. Caterpillar's 2024-09-30 and Honeywell's 2026-03-31 were `several_release_filings` as predicted, but Goldman Sachs' 2025-12-31 was not: its other Item 2.02 8-K, `0000886982-26-000004`, lists no `EX-99*` exhibit and was passed over, as was Chevron's `0000093410-26-000108`, which the plan expected the preliminary rule to drop. Ten `no_release_filing` events were not predicted: JPMorgan's eight, 3M's 2024-09-30, and Verizon's 2024-12-31. In each, `release-id/1` dropped the only candidate, the release itself, because every period it read in the Item 2.02 text was another one: its year-first pattern needs "fiscal" before the year, which P7-7's example shows but its prose does not require (deferred as `release-id/2`). Two `fiscal_labels_unknown` findings, Visa's and Dow's for 2026-06-30, were reported only (EV6).

Save the helpers that this task and the next use. Each reads saved responses and
committed files, and sends nothing.

Create `/tmp/plan7-summary.py`:

```python
"""The freeze gate's view of an event build: its events by status and reason, how
their releases were identified, each slot with several candidates, its findings by
kind and state, each override, what holds the freeze, and the content hash. It
reads saved responses and sends nothing; run it from the repository root.

usage: uv run --locked --all-packages python /tmp/plan7-summary.py
           <universe manifest> <store> <corpus directory> <corpus id>
"""

import sys
from collections import Counter
from pathlib import Path

from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.build import build_events, load_overrides
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.store import ArtifactStore

manifest, store, corpus, corpus_id = sys.argv[1:]
repo = Path.cwd()
built = build_events(
    load_manifest(Path(manifest)),
    SavedResponses(ArtifactStore(repo / store, repo)),
    load_overrides(Path(corpus) / "overrides.toml"),
    corpus_id=corpus_id,
)
rows = Counter(
    (row.eligibility_status.value, row.eligibility_reason.value, row.retained)
    for row in built.rows
)
for (status, reason, retained), count in sorted(rows.items()):
    print(f"{count:>4}  {status}  {reason}{'  (retained)' if retained else ''}")
issuers = {row.issuer_id for row in built.rows}
print(f"{len(built.rows)} events of {len(issuers)} issuers")
methods = Counter(
    row.identification_method.value
    for row in built.rows
    if row.identification_method is not None
)
print("identified: " + ", ".join(f"{m} {n}" for m, n in sorted(methods.items())))
for row in built.rows:
    if len(row.candidate_accessions) > 1:
        method = row.identification_method or row.eligibility_reason
        print(
            f"several candidates: {row.event_id}, {len(row.candidate_accessions)},"
            f" {method.value}"
        )
findings = Counter(
    (
        finding.kind.value,
        "blocks"
        if finding.holds_freeze
        else "acknowledged"
        if finding.resolved_by
        else "reported",
    )
    for finding in built.findings
)
for (kind, state), count in sorted(findings.items()):
    print(f"{count:>4}  {kind}  {state}")
for override in built.overrides:
    target = override.event_id or override.finding_id
    print(f"override {override.override_id}  {override.kind.value}  {target}")
print(
    f"blocking {len(built.blocking)}, stale {len(built.stale_overrides)},"
    f" unretained {len(built.unretained)}"
)
print(f"content {built.content_hash}")
```

Create `/tmp/plan7-quotes.py`:

```python
"""P6-3: print each string of 30 characters or more in the named committed files
that occurs in the text of a page saved in the named store, and exit 1; or print
'no saved page is quoted'. HTML is read as walker-1 text, and plain text as written.

usage: uv run --locked --all-packages python /tmp/plan7-quotes.py <store> <file>...
"""

import json
import sys
import tomllib
from pathlib import Path

from earnings_ingestion.cohort.locators import ArtifactText


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


store, *names = sys.argv[1:]
written = {s for name in names for s in strings(load(Path(name))) if len(s) >= 30}
root = Path(store, "sec-edgar")
pages = sorted([*root.glob("*.html"), *root.glob("*.txt")])
quoted = set()
for page in pages:
    body = page.read_bytes()
    if page.suffix == ".html":
        text = ArtifactText(body, "text/html").canonical[0]
    else:
        text = body.decode("utf-8", errors="replace")
    quoted |= {s for s in written if s in text}
print(f"{len(written)} strings checked against {len(pages)} saved pages")
print("\n".join(sorted(quoted)) or "no saved page is quoted")
raise SystemExit(1 if quoted else 0)
```

Create `/tmp/plan7-folder.py`:

```python
"""List what a store saved from one filing's folder, each with its SHA-256, and the
index page's Accepted value as the page writes it. It sends nothing.

usage: uv run --locked --all-packages python /tmp/plan7-folder.py
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
        print(f"  Accepted {read_filing_index(body.read_bytes()).accepted}")
print(f"{len(found)} saved in {folder}")
```

```bash
python3 /tmp/plan7-extract.py /tmp/plan7-summary.py && python3 /tmp/plan7-extract.py /tmp/plan7-quotes.py && python3 /tmp/plan7-extract.py /tmp/plan7-folder.py
uv run --locked --all-packages earnings-pipeline events build > /tmp/plan7-build.txt 2>&1; echo "exit $?"
grep -E 'blocks\]|stale|not retained|^acknowledge |^problem' /tmp/plan7-build.txt
uv run --locked --all-packages python /tmp/plan7-summary.py config/universe/djia/manifests/djia-2024q3-2026q2-v1.json data/raw/events config/corpus/djia-2024q3-2026q2 djia-2024q3-2026q2
```

On the synthetic corpus, whose overrides are in place, the summary printed:

```text
   1  ambiguous  no_release_filing  (retained)
   1  ambiguous  same_day_transition  (retained)
  27  eligible  member_at_publication
   3  ineligible  not_member_at_publication
32 events of 5 issuers
identified: override 1, sole_candidate 2, stated_period 28
several candidates: cik-0009990001:2025-02-28, 2, override
several candidates: cik-0009990005:2024-12-31, 2, stated_period
several candidates: cik-0009990006:2025-03-31, 2, stated_period
   1  fiscal_labels_unknown  reported
   3  period_gap  acknowledged
override gap-borealis  acknowledge  period_gap:cik-0009990002:2025-03-31:2026-07-01
override gap-corvid  acknowledge  period_gap:cik-0009990003:2024-07-01:2024-12-31
override gap-eastfield  acknowledge  period_gap:cik-0009990006:2025-03-31:2025-09-30
override keep-borealis-same-day  retain_unresolved  cik-0009990002:2024-09-30
override keep-dynamo-no-release  retain_unresolved  cik-0009990005:2025-06-27
override release-acme-2025-02-28  set_release_filing  cik-0009990001:2025-02-28
blocking 0, stale 0, unretained 0
content 438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58
```

Expected on the real data, before any override, a prediction:

- `exit 1`, since something holds the freeze;
- `263 events of 33 issuers`: eight period ends for each issuer, and seven for
  Coca-Cola, whose second quarter of 2026 ends 2026-07-03;
- `24  ineligible  not_member_at_publication`:
  - seven each for Intel and Dow, after their exits;
  - seven for Alphabet, before its entry;
  - one each for NVIDIA and Sherwin-Williams, before their entries;
  - one for Verizon, after its exit;
- `3  ambiguous  several_release_filings`, from Task 9: Caterpillar's quarter ended
  2024-09-30, Goldman Sachs' ended 2025-12-31, and Honeywell's ended 2026-03-31;
- `236  eligible  member_at_publication`;
- no `period_gap`. S §Slots found the second case only for Goldman Sachs and
  JPMorgan, whose older pages discovery has now read.

A `problem:` line stops the task. A saved response is missing or unreadable, which no
review settles. Report it to the user.

- [x] **Step 2 (gate): Review each blocking finding and each `ambiguous` event with the user**

> Deviation: the review decided 12 events, not the 3 predicted, each by a `set_release_filing` naming one of the rule's candidates: Caterpillar's `0000018230-24-000050`, Honeywell's `0000773840-26-000055`, and the only candidate of each of the ten `no_release_filing` events. The user gave five rationales in their own words and signed as reviewer. No `--filing` run, `retain_unresolved`, or `acknowledge` was needed: no `acceptance_time_unknown`, `same_day_transition`, `period_gap`, or `no_slots` arose.

Put each to the user, one at a time or in one batch, with its lines from
`/tmp/plan7-build.txt` and the decision it needs. For an `ambiguous` event, show its
row and the candidate lines under it:

```bash
grep -A8 '  ambiguous  ' /tmp/plan7-build.txt
```

Each candidate line gives the reading `release-id/1` made (P7-15): the dates, the
periods, whether the filing is preliminary, and why the rule kept or dropped it. The
user may read the saved documents too.

| What `build` reports | The decision | The override |
| --- | --- | --- |
| `several_release_filings` | Which candidate furnished the quarter's results | `set_release_filing`: `event_id`, `accession`, and a citation in that filing's folder. Or `retain_unresolved`: `event_id` and `reason`, which keeps the event out of the pilot |
| `no_release_filing` | Whether an 8-K/A the rule recorded, or an 8-K it passed over, is the release | `set_release_filing`, or `retain_unresolved` |
| `same_day_transition` | Nothing EDGAR shows can order it (EV9) | `retain_unresolved` |
| `period_gap:` or `no_slots:` | Whether the gap is real, such as a missed or late periodic report, or a change of fiscal year, read in the issuer's filings | `acknowledge`: `finding_id`, and `finding_digest` from `build`'s `acknowledge` line |
| `acceptance_time_unknown:` | The filing's index page is not saved. The user approves at most two requests, and `events discover --filing CIK ACCESSION` saves it | none: rebuild |
| `acceptance_time_mismatch:` | EV10's rule fails for that row: stop, and ask | none |
| `fiscal_labels_unknown:` | Reported only, and the labels stay null (EV6) | none |

**To cite a filing** for `set_release_filing`, list what the store saved from its
folder, then cite its index page at the Accepted value:

```text
uv run --locked --all-packages python /tmp/plan7-folder.py data/raw/events [GATE: the CIK, 10 digits] [GATE: the accession]
uv run --locked --all-packages earnings-pipeline cohort --store data/raw/events cite sec-edgar [GATE: the index page's sha256] --find "[GATE: its Accepted value]"
```

On the synthetic corpus, for Acme's release of 2025-03-20, these printed:

```text
024e830f50ab50e05787eb0889d7b5024052cfdae56a4e06979ca4c53cf53758 https://www.sec.gov/Archives/edgar/data/9990001/000999000125000008/0009990001-25-000008-index.htm
  Accepted 2025-03-20 16:05:00
227452b5862f10f0ecdb13fbec55aa09c69cd5868c2f5e85d55aa0adbcbd8786 https://www.sec.gov/Archives/edgar/data/9990001/000999000125000008/acme-8k-20250320.htm
2 saved in https://www.sec.gov/Archives/edgar/data/9990001/000999000125000008/
canonical_sha256 = "42cd4f1db14dc89bb2ca3f8ccd361c5cbe904e7a923a16cea5d95c4cc6087660"
span = [89, 108]
cited_sha256 = "5a7c7ed15534b4177d2c61c0945821405ac166908b4edc96e99a5b80107174f6"
```

These are the synthetic `overrides.toml`'s citation, and `cite` also prints the cited
text on stderr, which is never committed. If the filing's index page is not saved,
the user approves at most two requests for `events discover --filing` first.

**Write `config/corpus/djia-2024q3-2026q2/overrides.toml`.** Its fields are listed in
`docs/data-dictionary.md`. It begins:

```toml
# Reviewed decisions for the real event corpus (plan 7; the Stage 5 spec, §Review
# overrides). Each records its rationale, reviewer, and date; the reviewer is the user.
schema_version = 1
```

One entry for each decision:

```toml
[[overrides]]
override_id = "[GATE: a short slug, such as release-cat-2024-09-30]"
kind = "set_release_filing"
event_id = "[GATE: the event_id]"
accession = "[GATE: the release filing's accession]"
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

[[overrides]]
override_id = "[GATE: a short slug, such as keep-gs-2025-12-31]"
kind = "retain_unresolved"
event_id = "[GATE: the event_id]"
reason = "[GATE: its reason: several_release_filings, no_release_filing, or same_day_transition]"
rationale = "[GATE: the user's reason]"
reviewer = "[GATE: the user's name, as they sign it]"
recorded_on = [GATE: today's date]

[[overrides]]
override_id = "[GATE: a short slug, such as gap-<ticker>]"
kind = "acknowledge"
finding_id = "[GATE: the finding's ID, as build prints it]"
finding_digest = "[GATE: the digest from build's acknowledge line]"
rationale = "[GATE: the user's reason]"
reviewer = "[GATE: the user's name, as they sign it]"
recorded_on = [GATE: today's date]
```

- **The signature.** The implementer never writes `reviewer`. The user gives the name
  in chat, for each override or once for all.
- **The rationale** is the user's words, never a filing's. Step 3 refuses a phrase of
  30 or more characters copied from a saved page.
- **One of each kind.** An event may carry one override of each kind (P7-14). A
  `set_release_filing` decides eligibility again, and can leave the event `ambiguous`,
  which then needs a `retain_unresolved` too.
- **From records.** Task 15's `write_overrides(path, overrides)` writes this file
  from `EventOverride` records, as the synthetic fixture's is written.

- [x] **Step 3: Rebuild until nothing holds**

```bash
uv run --locked --all-packages earnings-pipeline events build > /tmp/plan7-build.txt 2>&1; echo "exit $?"
grep -E 'blocks\]|stale|not retained|^acknowledge |^problem' /tmp/plan7-build.txt
grep -n 'GATE:' config/corpus/djia-2024q3-2026q2/overrides.toml
uv run --locked --all-packages python /tmp/plan7-quotes.py data/raw/events config/corpus/djia-2024q3-2026q2/overrides.toml
```

Expected, checks:

- `exit 0`;
- nothing from either `grep`;
- `<n> strings checked against <m> saved pages`, then `no saved page is quoted`.

Repeat Steps 2 and 3 until then.

- **Acknowledgements bind to their findings.** If a later fix changes a finding,
  `build` prints its acknowledgement as `stale`, and the user reads the new finding.
- **A quoted string.** If the P6-3 check lists one, the user rewords that rationale.
- **No overrides.** If the review needs none, skip the file: `build` reads a missing
  file as no overrides, and the check then runs on nothing.

- [x] **Step 4 (gate): The user approves the event manifest**

Show the user the approval view:

Run: `uv run --locked --all-packages python /tmp/plan7-summary.py config/universe/djia/manifests/djia-2024q3-2026q2-v1.json data/raw/events config/corpus/djia-2024q3-2026q2 djia-2024q3-2026q2`

Expected:

- **A check:** `blocking 0, stale 0, unretained 0`, then `content <hash>`.
- **A prediction:**
  - `263 events of 33 issuers`, about 239 of them `eligible`;
  - `24  ineligible  not_member_at_publication`;
  - each review decision as an `override` line.

Freeze only after the user's clear yes.

- [x] **Step 5: Freeze**

```bash
uv run --locked --all-packages earnings-pipeline events freeze
uv run --locked --all-packages earnings-pipeline events freeze
```

Expected, checks:

- `froze djia-2024q3-2026q2 v1`;
- `config/corpus/djia-2024q3-2026q2/events-v1.json  <hash>`, whose hash is the
  approval view's;
- `config/corpus/djia-2024q3-2026q2/events-v1.evidence.json`;
- then the same three lines, but the first reads `unchanged: djia-2024q3-2026q2 v1`.

Then check that the manifest loads without the saved responses, and that every
citation in its evidence record verifies against them:

```bash
uv run --locked --all-packages python -c "from pathlib import Path; from earnings_ingestion.events.evidence import check_evidence; from earnings_ingestion.events.freeze import load_event_evidence, load_event_manifest; from earnings_ingestion.fetch.store import ArtifactStore; d = Path('config/corpus/djia-2024q3-2026q2'); m = load_event_manifest(d / 'events-v1.json'); e = load_event_evidence(d / 'events-v1.evidence.json'); print('manifest loads:', len(m.rows), 'events; citations verify:', check_evidence(e, ArtifactStore(Path('data/raw/events'), Path('.'))) == ())"
ls -l config/corpus/djia-2024q3-2026q2
```

Expected:

- **A check:** `manifest loads: <n> events; citations verify: True`. On the synthetic
  corpus, it printed `manifest loads: 32 events; citations verify: True`.
- **A prediction:** the evidence record is about 2 MB. Task 15's held 32 events in
  221 KB.

- [x] **Step 6: Check that nothing committed quotes a saved page (P6-3)**

Run: `uv run --locked --all-packages python /tmp/plan7-quotes.py data/raw/events config/corpus/djia-2024q3-2026q2/overrides.toml config/corpus/djia-2024q3-2026q2/events-v1.json config/corpus/djia-2024q3-2026q2/events-v1.evidence.json`

Expected, a check: `<n> strings checked against <m> saved pages`, then
`no saved page is quoted`.

- **Synthetic run.** On the synthetic corpus's four files, it printed
  `582 strings checked against 73 saved pages` and `no saved page is quoted`.
- **Test run.** A rationale that copied 60 characters of a synthetic 8-K was listed,
  and the check exited 1.
- **If it lists a string,** stop and ask. The repository is public.

- [x] **Step 7: Run the checks**

```bash
git check-ignore data/raw/events/sec-edgar
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
git status --short
```

Expected, checks:

- `data/raw/events/sec-edgar`;
- `1293 passed, 24 deselected`;
- `All checks passed!` and `250 files already formatted`;
- only `?? config/corpus/`.

- [x] **Step 8: Commit**

```bash
git log --oneline -3
git add config/corpus/djia-2024q3-2026q2
git commit -m "feat(events): review and freeze the DJIA event manifest"
```

---

### Task 21: The real pilot

This task runs S §Pilot selection (step 5) and the second half of S §Gates (plan A),
gate 3. `djia-pilot/1` runs on Task 20's frozen event manifest, and the pilot is
frozen before plan B acquires anything (P-C7).

- **The user approves a rule's output.** The selection is a rule. The user can
  refuse its output, but can change no row except through a new policy, which this
  plan does not make.
- **The prediction** is S §Pilot selection's own, "v1, projected":
  - step 1 takes 33 events, one per issuer;
  - step 2 adds at most three: NVIDIA's release of 2024-11-20, after its entry;
    Sherwin-Williams' first release after its entry; and Verizon's last release
    before its exit. Dow, Intel, and Alphabet each have one eligible event, which
    step 1 has already taken;
  - step 3 adds none;
  - step 5 fills the rest, at least four;
  - so 40 of target 40, with no transition reported.
- **A refusal is possible.** After step 1, steps 2 and 3 have only seven places, so
  `mandatory_overflow`, or `quarter_uncovered`, would stop for the user.

**Files:**

- Create (generated): `config/corpus/djia-2024q3-2026q2/pilot-v1.json`.

**Interfaces:**

- Consumes:
  - Task 20's frozen event manifest;
  - Task 17's `events select`;
  - Task 14's `select_pilot` and `load_pilot`;
  - Task 20's `/tmp/plan7-quotes.py`.
- Produces the frozen pilot, which plan B acquires and Stage 6 annotates:

  ```python
  from pathlib import Path

  from earnings_ingestion.cohort.freeze import load_manifest
  from earnings_ingestion.events.pilot import load_pilot

  universe = load_manifest(Path("config/universe/djia/manifests/djia-2024q3-2026q2-v1.json"))
  load_pilot(Path("config/corpus/djia-2024q3-2026q2/pilot-v1.json"), universe)
  ```

- [x] **Step 1 (gate): Preview the pilot, and ask the user to approve its freeze**

Create `/tmp/plan7-preview.py`:

```python
"""The pilot djia-pilot/1 would freeze from the latest frozen event manifest: its
rows by reason and quarter, its target, each reported transition, and its hash. It
writes nothing; run it from the repository root.

usage: uv run --locked --all-packages python /tmp/plan7-preview.py
           <universe manifest> <corpus directory>
"""

import sys
from collections import Counter
from pathlib import Path

from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.freeze import frozen_event_manifests
from earnings_ingestion.events.pilot import quarter, select_pilot
from earnings_ingestion.events.records import EventStatus

manifest, corpus = sys.argv[1:]
events = frozen_event_manifests(Path(corpus))[-1]
try:
    pilot = select_pilot(events, load_manifest(Path(manifest)))
except ValueError as error:
    sys.exit(f"Refused: {error}")
selection = pilot.selection
reasons = Counter(row.selection_reason.value for row in selection.rows)
for reason, count in sorted(reasons.items()):
    print(f"{count:>4}  {reason}")
chosen = {row.event_id for row in selection.rows}
periods = Counter(
    quarter(row.period_end) for row in events.rows if row.event_id in chosen
)
print("quarters: " + ", ".join(f"{q} {n}" for q, n in sorted(periods.items())))
eligible = {
    row.issuer_id
    for row in events.rows
    if row.eligibility_status is EventStatus.ELIGIBLE
}
issuers = {row.issuer_id for row in events.rows if row.event_id in chosen}
filled = ", underfilled" if selection.underfilled else ""
print(
    f"{len(selection.rows)} of target {selection.target}{filled};"
    f" {len(issuers)} of {len(eligible)} eligible issuers"
)
for transition in selection.unmatched_transitions:
    print(
        f"reported: {transition.issuer_id}'s {transition.kind.value} on"
        f" {transition.effective_date}"
    )
print(f"content {pilot.content_hash}")
```

```bash
python3 /tmp/plan7-extract.py /tmp/plan7-preview.py
uv run --locked --all-packages python /tmp/plan7-preview.py config/universe/djia/manifests/djia-2024q3-2026q2-v1.json config/corpus/djia-2024q3-2026q2
```

On the synthetic corpus, it printed:

```text
   4  issuer_coverage
  17  longitudinal_fill
   2  membership_boundary
   4  quarter_coverage
quarters: 2024Q3 3, 2024Q4 4, 2025Q1 4, 2025Q2 2, 2025Q3 4, 2025Q4 4, 2026Q1 3, 2026Q2 3
27 of target 27, underfilled; 4 of 4 eligible issuers
reported: cik-0009990002's exit on 2024-11-08
content 71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c
```

That content hash is the committed synthetic pilot's.

Expected on the real data:

- **Checks:**
  - every quarter from 2024Q3 to 2026Q2 on the `quarters:` line;
  - every eligible issuer taken, as `33 of 33 eligible issuers`.
- **A prediction:**
  - `33  issuer_coverage`;
  - at most `3  membership_boundary`;
  - no `quarter_coverage`;
  - at least `4  longitudinal_fill`;
  - `40 of target 40`, with no `reported:` line.

`Refused: <reason>: <detail>` stops for the user. `mandatory_overflow` and
`quarter_uncovered` each need a decision that this plan cannot make, such as a new
policy.

Show the user the preview, and freeze only after a clear yes.

- [x] **Step 2: Select and freeze**

```bash
uv run --locked --all-packages earnings-pipeline events select
uv run --locked --all-packages earnings-pipeline events select
```

Expected:

- **First run.** The rows in order, as `  1  <event_id>  <reason>`, then any
  `reported:` line, then `froze djia-2024q3-2026q2-pilot v1: 40 of target 40` and
  `config/corpus/djia-2024q3-2026q2/pilot-v1.json  <hash>`.
- **Second run.** The same rows, then
  `unchanged: djia-2024q3-2026q2-pilot v1: 40 of target 40`, with the same path and
  hash.
- **Checks:** the hash is the preview's, and the second run writes nothing. The row
  counts are the prediction.

Then check the chain: the pilot's hash, the event manifest it names, and that
manifest's universe:

Run: `uv run --locked --all-packages python -c "from pathlib import Path; from earnings_ingestion.cohort.freeze import load_manifest; from earnings_ingestion.events.pilot import load_pilot; u = load_manifest(Path('config/universe/djia/manifests/djia-2024q3-2026q2-v1.json')); p = load_pilot(Path('config/corpus/djia-2024q3-2026q2/pilot-v1.json'), u); print('pilot loads, and its chain holds:', len(p.rows), 'rows of target', p.definition.target)"`

Expected: `pilot loads, and its chain holds: 40 rows of target 40`. The load is the
check, and the counts are the prediction. On the synthetic corpus, it printed
`27 rows of target 27`.

- [x] **Step 3: Check that the pilot quotes no saved page (P6-3)**

Run: `uv run --locked --all-packages python /tmp/plan7-quotes.py data/raw/events config/corpus/djia-2024q3-2026q2/pilot-v1.json`

Expected, a check: `<n> strings checked against <m> saved pages`, then
`no saved page is quoted`. If `/tmp/plan7-quotes.py` is gone, extract it again from
Task 20.

- [x] **Step 4: Run the checks**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
git status --short
```

Expected, checks:

- `1293 passed, 24 deselected`;
- `All checks passed!` and `250 files already formatted`;
- only `?? config/corpus/djia-2024q3-2026q2/pilot-v1.json`.

- [x] **Step 5: Commit**

```bash
git log --oneline -3
git add config/corpus/djia-2024q3-2026q2/pilot-v1.json
git commit -m "feat(events): select and freeze the DJIA pilot with djia-pilot/1"
```

---

### Task 22: The verification record, and the current state

This task runs S §Gates (plan A), gate 4, and S §Rollout's refresh of the current
state.

- **The record** gathers what plan A verified, in the house style of
  `docs/verification/djia-cohort.md`. Its numbers come from Tasks 19 to 21, so its
  template holds `[GATE: …]` slots. Fill each from the named step's output, and never
  leave one.
- **The current state.** `CLAUDE.md` and `README.md` describe it. Stage 4's record
  has two bullets that plan A made stale, the `acceptanceDateTime` limitation and the
  note on versions, and this task corrects both.

**Files:**

- Create: `docs/verification/djia-events.md`.
- Modify, by exact replacement: `CLAUDE.md`, `README.md`, and
  `docs/verification/djia-cohort.md`.
- Regenerate, only if Task 20 ran `events discover --filing`:
  `docs/verification/edgar-acceptance-time.md`.

**Interfaces:**

- Consumes: everything this plan built, and the outputs of Tasks 19 to 21.
- Produces: documentation only. The test counts stay at Task 18's.

- [x] **Step 1 (gate): Write the record, and have the user read it**

> Deviation: the user approved the record with four additions beyond its slots: the ineligible events by issuer, the two passed-over 8-Ks, a sentence on the ten `no_release_filing` events, and a limitation on `release-id/1`'s year-first pattern. After the final review, the user approved one more Limitations sentence, added at Completion: the three events whose earlier Item 2.02 8-K the rule dropped as preliminary.

Create `docs/verification/djia-events.md`:

```markdown
# DJIA earnings events and the pilot: verification record

This record verifies plan A of roadmap Stage 5: event discovery, eligibility, and the
freezes, which `specs/event-discovery-eligibility-and-acquisition.md` specifies. Plan 7
(`specs/plans/7-event-discovery-eligibility-and-acquisition-plan-a.md`) built it.
Plan B, which acquires the pilot's releases, adds its own sections.

## What was verified

| Item (S §Verification, plan A) | Evidence |
| --- | --- |
| 1. The prerequisites: machine-wide locks; the operative hash, with v1 loading unchanged; the acceptance-time record; two robustness fixes | `test_two_checkouts_share_one_lock`; `test_a_withheld_notice_changes_the_content_but_not_the_identity`; `test_a_refetched_sec_record_changes_the_content_but_not_the_identity`; `test_v1_loads_unchanged_and_has_an_operative_hash`; [`edgar-acceptance-time.md`](edgar-acceptance-time.md), with both legs; `test_a_malformed_registrant_is_refused_as_sec_data`; `test_retry_after_ignores_non_ascii_digits` |
| 2. Each reader refuses a changed shape | `test_malformed_items_are_refused`; `test_an_older_page_with_a_malformed_date_is_refused`; `test_a_page_of_another_shape_is_refused`; `test_facts_of_another_shape_are_refused` |
| 3. Acceptance time: both conventions, both daylight-saving seasons, and a mismatch that blocks | `test_the_accepted_value_is_eastern_wall_time`; `test_a_row_uses_one_convention_or_mismatches`; `test_a_row_in_neither_convention_is_a_blocking_mismatch` |
| 4. The discovery replay (R1.1, R1.2) | `test_each_release_is_identified_by_its_statements`; `test_the_preliminary_filing_is_dropped_and_the_gap_s_neighbor_too`; `test_exhibit_numbering_and_the_amendment`; `test_every_event_s_reason_before_any_override`; `test_the_layer_holds_what_discovery_fetches_and_no_filing_after_the_cutoff` |
| 5. No exhibit before the freeze (EV2), and only the shared client (R1.3, D5) | `test_discovery_requests_what_the_build_reads_and_never_an_exhibit`; `test_stage_5_has_no_client_or_throttle_of_its_own`; the live run below |
| 6. Slots (P-VF) | `test_two_securities_make_one_row_per_period`; `test_the_window_is_half_open`; `test_each_period_gap_case_blocks`; `test_an_issuer_without_a_slot_blocks`; `test_a_nike_like_calendar_trips_no_guard` |
| 7. Eligibility (P-C2, P-VF) | `test_the_bound_rules_in_winter`; `test_the_bound_rules_in_summer`; `test_every_reason_and_the_checks_order` |
| 8. The times and labels stay separate (R1.5, P-A5) | `test_an_eligible_row_keeps_every_time_and_label_apart`; `test_unknown_labels_stay_null_together`; `test_record_fields_stay_separate_and_unknown_labels_stay_null` |
| 9. The freeze | `test_the_freeze_refuses_and_names_each_reason`; `test_identical_content_is_the_same_version`; `test_a_refetch_with_the_same_facts_writes_nothing`; `test_a_changed_fact_writes_the_next_version` |
| 10. Selection (P-C5, P-VF) | `test_shuffled_input_gives_a_byte_identical_pilot`; `test_with_40_or_more_eligible_events_the_pilot_holds_exactly_40`; `test_the_event_count_guards`; `test_more_than_40_issuers_needs_a_scope_decision`; `test_mandatory_cases_beyond_the_target_refuse_before_filling`; `test_a_quarter_with_no_eligible_event_refuses` |
| 11. Invalidation (P-VF) | `test_a_moved_bound_changes_both`; `test_a_changed_mapping_changes_both`; `test_a_changed_interval_or_policy_changes_the_hash_and_a_version_alone_does_not`; `test_a_changed_event_fact_or_policy_reseeds_and_a_universe_version_does_not` |
| 12. P-VI | `test_p_vi_replays_offline_to_the_frozen_manifests`, under a socket guard with no identity set |
| 13. R14.5 | `test_stage_5_loads_no_acquisition_library`; `test_stage_5_imports_no_acquisition_library`; the R14.5 section below |
| 14. The suites | The default suite, 1293 passed and 24 deselected; the harness suite, 280 passed; Ruff; `uv.lock` unchanged |

## The frozen event manifest

- **The manifest.** `config/corpus/djia-2024q3-2026q2/events-v1.json`, content hash
  [GATE: Task 20, Step 5's hash], created [GATE: its `created_at`]. It read the
  universe `djia-2024q3-2026q2` v1, whose operative hash is
  `c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573`, under
  `release-id/1` and `eligibility/1`.
- **The evidence record.** `events-v1.evidence.json`, [GATE: its size]. For each
  event it cites the periodic report and its labels, the release filing and its
  Accepted value, the Item 2.02 text, and each candidate. It also gives each file's
  convention and every retrieval time.
- **The events.** [GATE: n] events of 33 issuers:
  - [GATE: one line for each status and reason, with its count, from Task 20,
    Step 4's approval view].
- **Identification.** [GATE: the approval view's `identified:` line, and each slot
  with several candidates, with how it was resolved].
- **Findings.** [GATE: each finding kind and state, with its count, from the approval
  view; or "none"].
- **The review.** Signed by [GATE: the reviewer]:
  - [GATE: one line per override: its `override_id`, kind, and target, and the
    rationale in brief; or "no override was needed"].

## The pilot

- **The manifest.** `config/corpus/djia-2024q3-2026q2/pilot-v1.json`, content hash
  [GATE: Task 21, Step 2's hash], created [GATE: its `created_at`], with seed
  [GATE: its `selection_seed`]. It was drawn under `djia-pilot/1` from event manifest
  v1.
- **Its rows.** [GATE: n] of target [GATE: the target][GATE: ", underfilled", if it
  is]: [GATE: each reason, with its count].
- **Coverage.** [GATE: the preview's `quarters:` line], and [GATE: n] of [GATE: n]
  eligible issuers.
- **Transitions.** v1 has six, all before the open: Intel's, Dow's, Sherwin-Williams',
  and NVIDIA's on 2024-11-08, and Verizon's and Alphabet's on 2026-06-29.
  [GATE: each `membership_boundary` row with its transition, and each transition
  reported with no eligible event on its member side; or "step 1 had already taken
  each transition's event"].

## The requests

| Step | Client | Requests |
| --- | --- | --- |
| Planning, the format probe (P7-6), 2026-09-27 | SEC | 19, approved by the user: 16 primary documents and 3 companyfacts files, saved under `data/raw/events/`. They were sent under the per-checkout lock, before Task 1 made it machine-wide |
| Task 19, Step 3, `events discover` | SEC | [GATE: `requests sent`, and each phase's count] |
| Task 19, reruns | SEC | [GATE: each rerun's count; or "none"] |
| Task 20, `events discover --filing` | SEC | [GATE: each filing and its count; or "none"] |

No `-m live` test ran, and no exhibit was requested. No model was called, and no
billable service was used.

## Acceptance time

[`edgar-acceptance-time.md`](edgar-acceptance-time.md) gives both legs.
[GATE: leg 2's rows cross-checked, and how many follow each convention.] Every row
follows one of the two conventions, and no file follows both. So a filing's
acceptance time is its index page's Accepted value, and SEC's `acceptanceDateTime`
only cross-checks it (EV10).

## R14.5

Stage 5 uses no acquisition library. edgartools stays an unused optional extra, and
the readers are the package's own. So no library output reaches the ingestion
boundary, and there is nothing to cast. That is not R14.5 held vacuously: V1 found
that edgartools' table and filing paths return pandas or pyarrow objects, which would
need casts. `test_stage_5_loads_no_acquisition_library` checks each Stage 5 module at
runtime, and `test_stage_5_imports_no_acquisition_library` checks their source.

## Limitations

- **First publication is an upper bound** (EV9). `first_publication_time` is the
  release filing's EDGAR acceptance. A company that put its release on a newswire
  first published it earlier.
- **Same-day ordering.** EDGAR alone cannot order a release against a membership
  change on the same day. [GATE: the count of `same_day_transition` events retained
  unresolved; or "None arose in v1."]
- **`release-id/1` is fixed.** It reads a stated date only after "ended" or "ending"
  (P7-7). A case it gets wrong goes to review, and the rule changes only as
  `release-id/2`.
- **Retrieved after the cutoff.** SEC's records were retrieved after 2026-09-22. The
  cutoff is enforced on each filing's acceptance date, never on its retrieval date
  (P-C4).
- **Cohort v1's content hash.** The `sec-edgar` register entry now names companyfacts
  (Task 16), and v1's content hash covers that entry. So a rebuild of the cohort no
  longer reproduces v1's content hash, and `earnings-pipeline cohort verify-live`
  reports the difference. Its operative hash, which Stage 5 keys on, is unchanged
  (P7-3).
- **One machine.** The SEC and web client locks coordinate one machine's processes.
  Stage 1's harness client keeps its own lock, so it must never run live beside a
  package client.
```

Extract it with `python3 /tmp/plan7-extract.py docs/verification/djia-events.md`. Fill each slot:

- the requests, from Task 19, Step 3, from any rerun, and from each
  `events discover --filing` in Task 20;
- the events, identification, findings, and review, from Task 20, Step 4's approval
  view and `overrides.toml`;
- the evidence record's size, from Task 20, Step 5;
- the pilot's rows and coverage, from Task 21, Step 1's preview and Step 2's output;
- leg 2's rows, from Task 19, Step 4.

The hashes, times, and seed come from the frozen files:

```bash
python3 -c "import json; d = 'config/corpus/djia-2024q3-2026q2/'; e = json.load(open(d + 'events-v1.json'))['definition']; p = json.load(open(d + 'pilot-v1.json'))['definition']; print('events', e['content_hash'], e['created_at']); print('pilot', p['content_hash'], p['created_at'], p['selection_seed'])"
```

Pointed at `tests/fixtures/events/` instead, it printed:

```text
events 438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58 2026-09-29T12:00:00Z
pilot 71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c 2026-09-29T12:00:00Z 50d34b317cb002cae2856c7b7df03a184aca06ec0c04dbc502974d22730945d0
```

If Task 20 ran `events discover --filing`, the acceptance-time record's second leg
now has more pages to read, so regenerate it:

```bash
uv run --locked --all-packages python tests/integration/regenerate_acceptance_time_record.py
```

Expected: `wrote docs/verification/edgar-acceptance-time.md with 2 leg(s)`, and the
same verdict as at Task 19, Step 4. Take leg 2's rows for the record from this run.

Then check that no slot is left:

Run: `grep -n 'GATE:' docs/verification/djia-events.md`

Expected: no output. Show the user the record, and apply their corrections before
Step 2.

- [x] **Step 2: Record the current state**

Create `/tmp/plan7-task22-state.py`:

```python
"""Plan 7: exact replacements for 3 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "CLAUDE.md": [
        (
            "\n"
            "This repo is documentation-first: its working code is the Stage 1 investigation harness in `expirements/parser-fidelity/`, the Stage 2 contracts in `packages/earnings-core`, Stage 3's canonicalizer and browser diagnostic path in `packages/earnings-ingestion`, and Stage 4's point-in-time DJIA cohort and shared SEC client there too; `earnings-themes` is still a `hello()` scaffold, and the rest is instructions.\n"
            "Not all of it is binding.\n",
            "\n"
            "This repo is documentation-first: its working code is the Stage 1 investigation harness in `expirements/parser-fidelity/`, the Stage 2 contracts in `packages/earnings-core`, Stage 3's canonicalizer and browser diagnostic path in `packages/earnings-ingestion`, Stage 4's point-in-time DJIA cohort and shared SEC client there too, and Stage 5's event discovery, eligibility, and pilot selection (its plan A) beside them; `earnings-themes` is still a `hello()` scaffold, and the rest is instructions.\n"
            "Not all of it is binding.\n",
        ),
        (
            "| `specs/point-in-time-djia-cohort.md` | **Amends the theme-extraction spec and its roadmap** (adopted 2026-09-22, plan 2). Adds Stage 4, a versioned point-in-time DJIA cohort frozen before any document is acquired; moves the 40-event feasibility pilot into Stage 5 as a deterministic selection frozen before any acquisition or parse outcome is known; adds Stage 15, the full eight-quarter run. Governs on the firm universe, the event corpus, and pilot selection. Its window is `[2024-07-01, 2026-07-01)` and its public-information cutoff is `2026-09-22`. It is the stage spec for Stages 4 and 15 and binds Stage 5's eligibility and pilot-selection contracts. Stage 4 is complete (plan 6); Stage 15 is not, so the spec stays live. |\n"
            "| `AGENTS-jev-addendum.md`, `specs/jev-integration-spec.md` | **Superseded on the required-path question** by the spec's R14.3; retained only as a proposal for an optional, separately authorized layer. Jev/TypeSafe is not an adopted dependency. Values like `backend = \"disabled\"` or `model = \"jev-1.13.0\"` are sketches, not settings. |\n",
            "| `specs/point-in-time-djia-cohort.md` | **Amends the theme-extraction spec and its roadmap** (adopted 2026-09-22, plan 2). Adds Stage 4, a versioned point-in-time DJIA cohort frozen before any document is acquired; moves the 40-event feasibility pilot into Stage 5 as a deterministic selection frozen before any acquisition or parse outcome is known; adds Stage 15, the full eight-quarter run. Governs on the firm universe, the event corpus, and pilot selection. Its window is `[2024-07-01, 2026-07-01)` and its public-information cutoff is `2026-09-22`. It is the stage spec for Stages 4 and 15 and binds Stage 5's eligibility and pilot-selection contracts. Stage 4 is complete (plan 6); Stage 15 is not, so the spec stays live. |\n"
            "| `specs/event-discovery-eligibility-and-acquisition.md` | **Stage 5's stage spec**, approved 2026-09-27. It splits the stage into two plans (EV1). Plan A (plan 7) discovered the cohort's events and froze the event manifest and the pilot. Plan B, acquisition and processing states, is not written yet, so the spec stays live. |\n"
            "| `AGENTS-jev-addendum.md`, `specs/jev-integration-spec.md` | **Superseded on the required-path question** by the spec's R14.3; retained only as a proposal for an optional, separately authorized layer. Jev/TypeSafe is not an adopted dependency. Values like `backend = \"disabled\"` or `model = \"jev-1.13.0\"` are sketches, not settings. |\n",
        ),
        (
            "\n"
            "## Current state: Stages 1" + chr(0x2013) + "4 complete; `earnings-themes` still a scaffold\n"
            "\n",
            "\n"
            "## Current state: Stages 1" + chr(0x2013) + "4 and Stage 5's plan A complete; `earnings-themes` still a scaffold\n"
            "\n",
        ),
        (
            "\n"
            "`earnings-themes` still contains only a `hello()` stub, as do the top-level modules of `earnings-ingestion` and `apps/earnings-pipeline`; the application's commands are `earnings-pipeline browser setup` and the `earnings-pipeline cohort` group. `data/` is gitignored and holds only local, uncommitted material: fetched pages under `data/raw/`, the cohort's saved evidence under `data/raw/cohort/`, and under `data/runs/` Stage 1's run outputs, the user's rendered copies, the browser capture store, the client locks, and the cohort's live-verification records; `prompts/` and `codebooks/` are empty directories. `origin` is set to https://github.com/lowmason/earnings-themes, which is **public** " + chr(0x2014) + " treat anything committed here as publicly visible.\n"
            "\n",
            "\n"
            "Stage 5's plan A (event discovery, eligibility, and the freezes; plan 7, `specs/event-discovery-eligibility-and-acquisition.md`) is done, and plan B, acquisition, is next:\n"
            "\n"
            "- `packages/earnings-ingestion/src/earnings_ingestion/events/` finds each cohort issuer's quarterly slots and release filings in SEC's filing metadata (`release-id/1`), and judges each event's eligibility by point-in-time membership at its EDGAR acceptance time (`eligibility/1`). It freezes the event manifest with its evidence record, and then the pilot (`djia-pilot/1`). `earnings-pipeline events` holds its commands. Only `events discover` sends requests, through the shared SEC client, and it fetches no exhibit.\n"
            "- The SEC and web client locks are machine-wide, in the user's cache directory (`fetch.client.machine_lock_dir()`, or `$EARNINGS_LOCK_DIR`). `cohort/identity.py`'s `operative_hash` identifies the universe for Stage 5's records, so a cohort version whose facts are unchanged re-versions nothing.\n"
            "- A filing's acceptance time is its index page's Accepted value, read in America/New_York. SEC's `acceptanceDateTime` follows one of two conventions in each file, and only cross-checks it. `docs/verification/edgar-acceptance-time.md` records the finding.\n"
            "- `config/corpus/djia-2024q3-2026q2/` holds the reviewed overrides, the frozen event manifest and its evidence record, and the frozen pilot: facts, URLs, hashes, and locators, never source text. `tests/fixtures/events/` is the synthetic event corpus, which regenerates byte for byte and replays offline (P-VI). `docs/verification/djia-events.md` records the run.\n"
            "\n"
            "`earnings-themes` still contains only a `hello()` stub, as do the top-level modules of `earnings-ingestion` and `apps/earnings-pipeline`; the application's commands are `earnings-pipeline browser setup` and the `earnings-pipeline cohort` and `events` groups. `data/` is gitignored and holds only local, uncommitted material: fetched pages under `data/raw/`, the cohort's saved evidence under `data/raw/cohort/`, Stage 5's saved SEC responses under `data/raw/events/`, and under `data/runs/` Stage 1's run outputs and live lock, the user's rendered copies, the browser capture store, and the cohort's live-verification records; `prompts/` and `codebooks/` are empty directories. `origin` is set to https://github.com/lowmason/earnings-themes, which is **public** " + chr(0x2014) + " treat anything committed here as publicly visible.\n"
            "\n",
        ),
    ],
    "README.md": [
        (
            "> [!IMPORTANT]\n"
            "> **Project status (2026-09-25): Stages 1 and 2 complete.** The `uv` workspace,\n"
            "> package boundaries, specifications, and staged roadmap exist; Stage 1's parser\n"
            "> investigation is finished; and `earnings-core` holds the shared evidence contracts\n"
            "> and exactness checks, with an offline test suite. The other packages still contain\n"
            "> placeholder APIs; there is no operational pipeline, command-line interface,\n"
            "> approved theme codebook, or published dataset yet.\n"
            "\n",
            "> [!IMPORTANT]\n"
            "> **Project status ([GATE: the completion date]): Stages 1 to 4 complete, and the\n"
            "> first of Stage 5's two plans.** The `uv` workspace, package boundaries,\n"
            "> specifications, and staged roadmap exist. `earnings-core` holds the shared\n"
            "> evidence contracts, and `earnings-ingestion` canonicalizes releases, rebuilds the\n"
            "> point-in-time DJIA cohort, and discovers and freezes its earnings events and pilot,\n"
            "> each with offline tests. `earnings-themes` still contains a placeholder API; there\n"
            "> is no theme extraction, approved theme codebook, or published dataset yet.\n"
            "\n",
        ),
        (
            "| `packages/earnings-core/` | Shared contracts, identifiers, hashes, provenance, and pure span helpers | Stage 2 contracts and exactness checks (schema v2) |\n"
            "| `packages/earnings-ingestion/` | Source adapters, raw snapshots, deterministic parsing, canonicalization, and entity resolution | Stage 3's canonicalizer and browser diagnostic path; Stage 4's artifact store, shared SEC client, and point-in-time DJIA cohort |\n"
            "| `packages/earnings-themes/` | Quote-claim extraction, exact-span verification, support assessment, codebooks, and evaluation | Scaffold only |\n"
            "| `apps/earnings-pipeline/` | Thin application layer for configuration, stage coordination, checkpoints, and reporting | `earnings-pipeline browser setup` and the `earnings-pipeline cohort` commands |\n"
            "| `docs/` | Source notes and, as the project develops, methodology, source registers, verification reports, and decisions | Source notes, the release source register, verification records V1 and V2, ADR 0001, and the `earnings-core` data dictionary |\n",
            "| `packages/earnings-core/` | Shared contracts, identifiers, hashes, provenance, and pure span helpers | Stage 2 contracts and exactness checks (schema v2) |\n"
            "| `packages/earnings-ingestion/` | Source adapters, raw snapshots, deterministic parsing, canonicalization, and entity resolution | Stage 3's canonicalizer and browser diagnostic path; Stage 4's artifact store, shared SEC client, and point-in-time DJIA cohort; Stage 5's event discovery, eligibility, and pilot selection |\n"
            "| `packages/earnings-themes/` | Quote-claim extraction, exact-span verification, support assessment, codebooks, and evaluation | Scaffold only |\n"
            "| `apps/earnings-pipeline/` | Thin application layer for configuration, stage coordination, checkpoints, and reporting | `earnings-pipeline browser setup`, and the `earnings-pipeline cohort` and `earnings-pipeline events` commands |\n"
            "| `docs/` | Source notes and, as the project develops, methodology, source registers, verification reports, and decisions | Source notes, the release source register, verification records V1 and V2, ADR 0001, and the `earnings-core` data dictionary |\n",
        ),
        (
            "| `tests/fixtures/cohort/` | The synthetic cohort, which replays offline to its frozen manifest | Present |\n"
            "\n",
            "| `tests/fixtures/cohort/` | The synthetic cohort, which replays offline to its frozen manifest | Present |\n"
            "| `config/corpus/djia-2024q3-2026q2/` | The reviewed event overrides, the frozen event manifest and its evidence record, and the frozen pilot: facts, URLs, hashes, and locators, never source text | Stage 5's frozen event manifest and pilot |\n"
            "| `tests/fixtures/events/` | The synthetic event corpus, which replays offline to its frozen event manifest and pilot | Present |\n"
            "\n",
        ),
        (
            "The implementation is organized as a staged, evidence-first roadmap of sixteen\n"
            "stages. Stages 1 to 4 are complete; Stage 5 is next.\n"
            "\n",
            "The implementation is organized as a staged, evidence-first roadmap of sixteen\n"
            "stages. Stages 1 to 4 are complete, and so is the first of Stage 5's two plans.\n"
            "\n",
        ),
        (
            "second. The [verification record](docs/verification/djia-cohort.md) has the\n"
            "details. The next milestone is **Stage 5: event discovery, eligibility, and\n"
            "acquisition**.\n"
            "\n",
            "second. The [verification record](docs/verification/djia-cohort.md) has the\n"
            "details.\n"
            "\n"
            "**Stage 5: event discovery, eligibility, and acquisition** is half done. Its first\n"
            "plan finds each cohort issuer's quarterly earnings releases in SEC's filing\n"
            "metadata, and judges each one's eligibility by point-in-time membership at its\n"
            "EDGAR acceptance time. It freezes the reviewed event manifest and a deterministic\n"
            "pilot selection in `config/corpus/djia-2024q3-2026q2/` before any release is\n"
            "acquired. The [verification record](docs/verification/djia-events.md) has the\n"
            "details. The next milestone is Stage 5's second plan, which acquires the pilot's\n"
            "releases.\n"
            "\n",
        ),
        (
            "  event-eligibility and pilot-selection design.\n"
            "- [Earnings-theme learning path](docs/earnings-themes.md) " + chr(0x2014) + " the original staged\n",
            "  event-eligibility and pilot-selection design.\n"
            "- [Event discovery, eligibility, and acquisition specification](specs/event-discovery-eligibility-and-acquisition.md)\n"
            "  " + chr(0x2014) + " Stage 5's two plans: discovery, eligibility, and the freezes; then\n"
            "  acquisition and processing states.\n"
            "- [Earnings-theme learning path](docs/earnings-themes.md) " + chr(0x2014) + " the original staged\n",
        ),
    ],
    "docs/verification/djia-cohort.md": [
        (
            "  must never run live beside a package client.\n"
            "- **`acceptanceDateTime`.** The readers take SEC's offset as written. Whether the\n"
            "  time is UTC or Eastern is unverified, and Stage 4 uses it only to order filings\n"
            "  of one fund. Stage 5 must settle it before using it as a filing's acceptance time\n"
            "  (R1.5).\n"
            "- **Secondary anchor.** A Wikipedia revision can lag or err. The official changes\n",
            "  must never run live beside a package client.\n"
            "- **`acceptanceDateTime`.** The readers take SEC's offset as written, and Stage 4\n"
            "  uses it only to order filings of one fund. Stage 5 found that SEC writes it in\n"
            "  two conventions, one per file, and takes a filing's acceptance time from its\n"
            "  index page instead (plan 7; `docs/verification/edgar-acceptance-time.md`).\n"
            "- **Secondary anchor.** A Wikipedia revision can lag or err. The official changes\n",
        ),
        (
            "  newer SEC records, makes a new version whose intervals, mappings, and candidate\n"
            "  issuers are unchanged. Stage 5 should key on those, not on the content hash\n"
            "  (`specs/deferred_items.md`).\n"
            "- **Citation checks.** The build checks that each cited row's name and ticker occur\n",
            "  newer SEC records, makes a new version whose intervals, mappings, and candidate\n"
            "  issuers are unchanged. Stage 5 keys on those, through the universe's operative\n"
            "  hash (plan 7, `cohort/identity.py`). Plan 7's edit of the `sec-edgar` register\n"
            "  entry changes a rebuild's content hash the same way, so `cohort verify-live` now\n"
            "  reports a difference while the operative hash is v1's.\n"
            "- **Citation checks.** The build checks that each cited row's name and ticker occur\n",
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

Apply `task22-state`.

It prints three `edited` lines. The README's status callout then holds one slot,
`[GATE: the completion date]`. Fill it with today's date, written as `YYYY-MM-DD`,
and check:

```bash
grep -n 'GATE:' README.md CLAUDE.md docs/verification/djia-cohort.md
wc -l AGENTS.md
```

Expected: no `grep` output, then `837 AGENTS.md`, since `AGENTS.md` is untouched.

- [x] **Step 3: Final verification**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages python expirements/parser-fidelity/fetch_policy_pages.py verify
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
git diff --stat main -- uv.lock
git grep -n 'GATE:' -- docs config CLAUDE.md README.md
```

Expected:

- `1293 passed, 24 deselected`;
- `280 passed`;
- `All checks passed!` and `250 files already formatted`;
- `register quotes verified`;
- `freeze verified`;
- no output from `git diff`, since `uv.lock` has not changed;
- no `git grep` output.

- [x] **Step 4: Commit**

```bash
git log --oneline -3
git add docs/verification/djia-events.md CLAUDE.md README.md docs/verification/djia-cohort.md
git commit -m "docs: record Stage 5's plan A in its verification record, CLAUDE.md, and the README"
```

If Step 1 regenerated the acceptance-time record, add
`docs/verification/edgar-acceptance-time.md` to the `git add`.

## Handoffs

S §Handoffs to later stages lists what each later stage receives from Stage 5. This
plan hands plan B the following. Plan B is planned only after this plan ships, with
the real manifests frozen (P7-1).

### To plan B (acquisition and processing states)

- **The frozen pilot.**
  - `earnings_ingestion.events.pilot.load_pilot(path, universe)` reads a pilot and
    rechecks its chain: its hash, the event manifest it names, and that manifest's
    universe operative hash.
  - The real pilot is `config/corpus/djia-2024q3-2026q2/pilot-v<N>.json`, and the
    latest version wins. `frozen_pilots(directory, universe)` lists them.
  - The synthetic one, `tests/fixtures/events/pilot-v1.json`, is underfilled at 27
    events.

  > Deviation: after the final review, `frozen_pilots` takes only the directory (`17ce98e`). It lists every version, each checked for its hash and name but not its chain, since versions may have read different universes; plan B reads the one it picks with `load_pilot(path, universe)`, which checks the chain.
- **Each pilot event's facts.** They are in its event manifest row:
  - `release_accession` and `cik`;
  - `period_end` and the fiscal labels;
  - `filing_acceptance_time` and `first_publication_time`.

  `load_event_manifest(path)` reads the manifest.
- **The release filing's exhibits.** Its index page is saved in `data/raw/events/`.
  `sec.filing_index.read_filing_index(body).exhibits_99()` lists its `EX-99*`
  exhibits, whatever their numbering (R1.2).
- **The Item 2.02 text.** `events.release.read_document` reads it in `walker-1`'s
  text, and the evidence record cites its span.
- **The shared SEC client.** `open_sec_client(max_requests=N)` takes the approved
  count as its cap, as `events discover` does. Plan B's `events acquire` joins the
  `events` group.
- **The AMC-like case.** In the synthetic layer, Corvid's only `EX-99` for 2025-06-30
  is a pro forma overview. It is the case for plan B's exhibit choice (V2's finding).
- **The P6-3 check.** Plan B's commits hold no source text either. Task 20's
  `/tmp/plan7-quotes.py` shows how to check that against saved pages.
- **Live requests.** `EDGAR_IDENTITY` is exported, so plan B's acquisition and any
  `-m live` test each need a gate with a stated count.

### Deferred items that stay open

S §Deferred items gives each item's disposition. After this plan, these stay open:

- **From plan 6:**
  - the cohort CLI's tracebacks, which Completion restates as an item of its own;
  - what an override's dates mean;
  - holdings matched by date;
  - the four stale claims;
  - `verify-live`'s other hosts.
- **Plan 7's own:** `verify-live`'s hash difference on v1, which Completion records
  as an item (P7-3).
- **From plans 1, 3, and 5:** every open item, as S §Deferred items gives them.

## Completion

After Task 22, run the final whole-branch review. Then:

1. **Plan Completion Protocol** (writing-plans).
   - Run the resolve-before-defer gate.
   - Mark up this plan: tick the steps, add `> Deviation:` and `> Skipped:` notes, and
     add the status header.
   - A gate whose remedy was not needed is not skipped: note what the real data gave,
     such as "no `--filing` run was needed".
2. **Rollout line.** Append a blank line and this line to the end of
   `specs/event-discovery-eligibility-and-acquisition.md`, putting the completion date
   in place of `YYYY-MM-DD`:

   ```text
   > Plan A: COMPLETE (YYYY-MM-DD) — implemented by plan 7 (specs/plans/completed/7-event-discovery-eligibility-and-acquisition-plan-a.md). Next: write plan B.
   ```

   This is the spec's only edit. The spec stays live, and Stage 5 is not ticked:
   S §Rollout's "plan completion" means plan B's (P7-1).
3. **Deferred items.** In `specs/deferred_items.md`, under
   `## 6-point-in-time-djia-cohort — 2026-09-26`:
   - tick "Give the universe manifest an operative identity", ending it
     `→ done in plan 7`;
   - tick "Hold the SEC and web client locks once per machine", ending it
     `→ done in plan 7`;
   - tick "Three robustness fixes in the cohort path", ending it
     `→ parts 2 and 3 done in plan 7; part 1 restated under plan 7` (S §Deferred
     items).

   Then append a `## 7-event-discovery-eligibility-and-acquisition-plan-a — YYYY-MM-DD`
   section, with the completion date. It holds part 1, restated, the `verify-live`
   item that P7-3 leaves, and any other item of this plan's own:

   ```markdown
   - [ ] Report the cohort CLI's override and terms errors as `problem:` lines
         (plan 6's "Three robustness fixes", part 1, restated by plan 7): `_build`
         in `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py` catches
         only `CohortError`, but a bad override makes `reconstruct`
         (`cohort/intervals.py`), `resolve` (`cohort/resolution.py`), or
         `acknowledge` (`cohort/findings.py`) raise `ValueError`, which prints a
         traceback. `terms_digest` also runs outside any `try` in `cohort_cli.py`'s
         `terms` and in `cohort/live.py`, so a terms page that `walker-1` cannot
         read aborts `verify-live` before its record is written. Paths are under
         `packages/earnings-ingestion/src/earnings_ingestion/` unless given in
         full. Size: quick-fix. Done when: each case has a test, and each ends as a
         `problem:` line or in `verify-live`'s record.
   - [ ] Show the operative hashes in `verify-live` (plan 7, P7-3): plan 7's Task
         16 named companyfacts in the `sec-edgar` entry of
         `docs/source-register.toml`, and a universe manifest's content hash
         covers that entry through `source_register_version`. So a rebuild of
         cohort v1 no longer reproduces v1's content hash, although its operative
         hash (`cohort/identity.py`), on which Stage 5 keys, is unchanged.
         `earnings-pipeline cohort verify-live` prints and records only
         `rebuilt_content_hash` and `frozen_content_hash` (`cohort/live.py`, and
         `LiveVerification` in `cohort/records.py`), so every run from now on shows
         a difference that no fact explains. Record both versions' operative
         hashes beside them. Paths are under
         `packages/earnings-ingestion/src/earnings_ingestion/`. Size: quick-fix.
         Done when: `verify-live`'s output and record tell a register-only change
         from a changed fact, with a test.
   ```

   Commit steps 1 to 3 together as
   `docs(specs): mark up plan 7, record Stage 5's plan A, and tick deferred items`.
4. **Backlog triage.** Run
   `uv run --no-project --python 3.13 python ~/.claude/skills/writing-plans/scripts/deferred_stats.py`,
   and report its summary line. Present the triage rubric if its thresholds trip.
5. **Retire the plan only (P7-1).** The spec stays in `specs/`, since plan B
   implements it too.

   ```bash
   git mv specs/plans/7-event-discovery-eligibility-and-acquisition-plan-a.md specs/plans/completed/
   ```

   `docs/verification/djia-events.md` cites the plan's old path, so re-point it. The
   retired plan keeps its own mentions, as plans 4 to 6 do. Then check that no old
   path is left outside the retired plans:

   ```bash
   python3 - <<'EOF'
   from pathlib import Path

   OLD = "`specs/plans/7-event-discovery-eligibility-and-acquisition-plan-a.md`"
   NEW = "`specs/plans/completed/7-event-discovery-eligibility-and-acquisition-plan-a.md`"
   path = Path("docs/verification/djia-events.md")
   text = path.read_text(encoding="utf-8")
   assert text.count(OLD) == 1, OLD
   path.write_text(text.replace(OLD, NEW), encoding="utf-8")
   print(f"re-pointed {path}")
   EOF
   git grep -n "specs/plans/7-event-discovery" -- . ':!specs/plans/completed'
   ```

   Expected: `re-pointed docs/verification/djia-events.md`, then no `git grep`
   output. Commit as `chore(specs): retire plan 7`.
6. **Roadmap.** Leave `specs/evidence-linked-theme-extraction-roadmap.md` as it is.
   The reconcile that ticks Stage 5 runs at plan B's completion (S §Rollout).
7. **Integrate** with finishing-a-development-branch.
   - Open a pull request from `stage-5-event-discovery-eligibility-and-acquisition`
     to `main`, as Stages 1 to 4 did. Plan B then branches from `main`.
   - The branch was unpushed at planning, so this is its first push, and the
     repository is public.
8. **Report.**
   - State the commands actually run, and their results.
   - State every live request, by gate, with its count.
   - Give the event manifest's and the pilot's versions and content hashes.
   - State that no model was called.
   - Name the four flagged readings, P7-4, P7-7, P7-8, and P7-20, which the user
     accepted before execution.
