# The Pilot Codebook, Split, and Gold-Set Protocol (Stage 6) — Implementation Plan

**Status: COMPLETE (2026-10-03)** — executed via subagent-driven-development; deferred items in specs/deferred_items.md

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 6 — on plan
> completion, tick the stage and re-validate later stages against what shipped.
>
> This is Stage 6's only plan (GS1). Its last tasks are the spec's gates, in its
> order, and its completion ticks Stage 6, appends the spec's stage stamp, and retires
> the spec with the plan.

**Goal:** Implement `specs/pilot-codebook-split-and-gold-set-protocol.md`, and run
its gates:

- the canonical reader and the D4 coverage report, in `earnings-ingestion`;
- the split rule, the codebook and gold contracts, the anchor, the validator, the
  views, and the wording guard, in `earnings-themes`;
- `earnings-pipeline pilot`, `codebook`, and `gold`, in the application;
- the two drafting briefs, and the tests over pilot v1;
- then the gates: the split and the coverage report, the backup, the brief review,
  codebook v0 with ADR 0003, the curated hard negatives, and three signed train
  bundles.

It ends when three train bundles pass the validator and Stage 6 is ticked. No step
sends an SEC request, and no code calls a model.

**Architecture:**

- **Ingestion** (`packages/earnings-ingestion`). `canonical/serialize.py` gains
  `from_fixture_json`, which reads a canonical document back from the fixture format
  that Stage 5 writes under `data/runs/events/canonical/`. `events/coverage.py`
  builds the D4 coverage report over the state table, from the runs it names.
- **Themes** (`packages/earnings-themes`), which imports only `earnings-core`:
  - `records.py`, `tomlfile.py`, and `problems.py`: the record base, a minimal TOML
    writer and reader, and the refusal reasons;
  - `split.py`: `issuer-time/1`;
  - `wording.py`: F20's 40-character rule, reporting labels and IDs only;
  - `anchoring.py`: a drafted quote becomes an exact narrative span through
    `parse_span_candidate` and `validate_span`, or is refused;
  - `codebook.py`, `gold.py`, and `annotation.py`: the contracts, the codebook's
    freeze, and the gold's build and validator, with each item's origin;
  - `view.py`: the local views and texts;
  - `synthetic.py`: the tests' invented document and drafts.
- **The application** (`apps/earnings-pipeline`). `stage6.py` loads the pin and the
  local documents, and prints IDs, counts, reasons, and hashes, never text.
  `pilot_cli.py`, `codebook_cli.py`, and `gold_cli.py` hold the seven commands.
- **The gates.** Drafting happens in fresh sessions the user starts with the
  committed briefs, never in the executing session (P9-5). The executing session
  prepares each drafting session's text, hands off, and resumes when the user
  returns, then anchors, validates, and commits.

**Tech Stack:**

- Python 3.14.0 and uv 0.12.15. No new dependency: `uv.lock` does not change (GS17).
- Already declared and locked: pydantic 2.13.5, typer 0.27.2, Polars 1.44.2 (which
  reads the state table), pytest 9.1.1, and Ruff 0.16.8.
- From the standard library: `tomllib`, which reads TOML; `json`, `re`, `pkgutil`,
  and `functools`. Hashes go through `earnings_core.sha256_hex`.

## The spec this plan implements

The roadmap's Stage 6 entry scopes the stage
(`specs/evidence-linked-theme-extraction-roadmap.md`, Stage 6). Its Consumes line,
reconciled on 2026-09-28 (`21028a9`), names plan 8's Handoffs to Stage 6.

- **The stage spec.** `specs/pilot-codebook-split-and-gold-set-protocol.md`, cited as
  `S`, was approved on 2026-09-28 (`b33caab`, `4c08f07`, `6e3666e`). Its decisions
  GS1–GS18 are settled. This plan implements all of it:
  - S §The pin, §Order of work, §The split, §The coverage report, §The codebook,
    §The gold, §Anchoring and validation, §Curated hard negatives, §Drafting and
    tools, §Wording guard, §Refusals, §Verification, and §Gates;
  - S §Exit criteria, clause by clause;
  - S §Rollout, on completion.
- **Two amendments.** The user decided two points on 2026-09-28 that change S's
  words, and Tasks 8 and 12 amend S to match: `no_theme` is supports-only (P9-4), and
  a file named for an event writes its colon as an underscore (P9-3).
- **Plan 8's handoff.** `specs/plans/completed/8-event-discovery-eligibility-and-acquisition-plan-b.md`
  §Handoffs, "To Stage 6": `load_pilot(path, universe)`, `read_runs`,
  `current_states`, and each `parsed` document's canonical file.
- **`AGENTS.md`** (`A`): A §191, which asks the data dictionary to change with each
  public contract; A §608–611, the codebook's fields; and A §749, which keeps dev and
  test gold out of prompt design.
- **Out of scope** (S §Scope): the other 25 train and dev bundles, which continue
  after this plan with Task 19's procedure; the 7 test bundles, which wait for Stage
  14 (GS18); R8.4's support labels; any metric, threshold, or model; sector
  classification; F27, `release-id/2`, and the per-candidate citations; and any edit
  to a frozen record under `config/`.
- **The user's decisions of 2026-09-28.** The planning session put seven choices to
  the user. P9-1 through P9-7 record the answers.

## Global Constraints

Every task's requirements include these.

**Locators:**

- `A §n` is `AGENTS.md` at line `n`.
- `Rn` are requirements in `specs/evidence-linked-theme-extraction.md`.
- `S` cites `specs/pilot-codebook-split-and-gold-set-protocol.md`, the stage spec:
  `GS1`–`GS18` are its decisions, and `S §Section` cites a section by name.
- `P` cites `specs/point-in-time-djia-cohort.md`: `P-C7` (freeze before outcomes)
  and `P-VI` (offline replay).
- `Dn` are the roadmap's decisions, `P8-n` are plan 8's, and `P9-n` are this plan's,
  listed below. `F20` is PR #6's finding that no committed record may quote a saved
  page (plan 8, P8-5).
- **The pin** (GS2): **pilot v1**, `config/corpus/djia-2024q3-2026q2/pilot-v1.json`,
  over **events v1**, `events-v1.json` beside it, against **universe v1**,
  `config/universe/djia/manifests/djia-2024q3-2026q2-v1.json`.

**Versions and constants.**

| Name | Value | Where |
| --- | --- | --- |
| Themes record schema | `1`, new | `THEMES_SCHEMA_VERSION` in `earnings_themes/records.py` (Task 3) |
| Ingestion record schema | `1`, unchanged: the coverage report joins it | `INGESTION_SCHEMA_VERSION` |
| Core schema | `2`, unchanged; `earnings-core` does not change (GS17) | `earnings_core` |
| Canonicalization | `walker-1`, unchanged | `canonical/` |
| pilot v1 | `djia-2024q3-2026q2-pilot`, content hash `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926`, 40 events over 33 issuers | `PILOT_V1_HASH` in `earnings_pipeline/stage6.py` (Task 10) |
| events v1 | content hash `2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7` | `events-v1.json` |
| universe v1 | operative hash `c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573` | `UNIVERSE_V1` in `stage6.py` |
| Split rule | `issuer-time/1`: train 2024Q3–2025Q2, dev 2025Q3–2025Q4, test 2026Q1–2026Q2 | `SPLIT_POLICY` in `earnings_themes/split.py` (Task 4) |
| Codebook | `djia-pilot`, version `0` | `CODEBOOK_ID`, `CODEBOOK_VERSION` in `earnings_themes/codebook.py` (Task 7) |
| Wording window | 40 characters, full dates masked | `WIDTH` in `earnings_themes/wording.py` (Task 5) |
| Committed homes (GS14) | `evaluation/djia-2024q3-2026q2/pilot-v1/` (split, coverage report, gold, briefs); `codebooks/djia-pilot/`; `tests/fixtures/gold/`; `docs/adr/0003-…` | `Pinned`, `CODEBOOK_FILE`, `HARD_NEGATIVES` in `stage6.py` |
| Local, gitignored | `data/runs/events/` (Stage 5's states and canonical documents, read only); `data/runs/gold/` (drafts, anchored files, views, texts) | `EVENT_RUNS`, `GOLD_RUNS` in `stage6.py` |
| Drafting sessions' model | Claude Opus 5.5, `claude-opus-5-5` (P9-5) | each draft's `drafting_aid.model_id` |

**Offline, no SEC, and no models.**

- No step sends an SEC request: Stage 6 needs none. No task opens the SEC client.
- No code calls a model, and no model SDK, API key, or HTTP client enters
  `earnings-themes` (R14.1). Task 9's import test holds that.
- Default tests make no network call and no billable call, and need no credential.
- **`EDGAR_IDENTITY` is exported in this shell.** A `live` test's skip guard does not
  stop it, and it sends real requests. Never pass `-m live`. To check collection,
  use `--collect-only`. Never print, commit, or record `EDGAR_IDENTITY`.

**Blinding (GS13, and the user's instruction of 2026-09-28).** These bind the
executing session, every subagent it dispatches, and every reviewer:

- **Never open, `cat`, print, `grep`, or paste pilot document text.** That text is in
  `data/runs/events/canonical/`, `data/raw/events/`, and everything under
  `data/runs/gold/`: the drafts, working copies, anchored files, views, and texts.
  Never search under `data/`, and never read a file there with a tool that shows
  its contents. Listing file names under `data/runs/gold/drafts/`, which are IDs,
  is allowed.
- **Programs print IDs, counts, reasons, paths, and hashes.** A programmatic check
  may read pilot text, as the commands and the local legs do. What it prints is
  never text: a refusal names its item by ID or field path, and an unforeseen error
  by its type alone (`guarded`, Task 10).
- **Tests use synthetic text and Stage 1's fixtures only.** A test over pilot
  documents asserts on IDs, counts, labels, and hashes, and binds any result before
  asserting on it, since pytest's report of a failed assert shows each call's
  arguments.
- **Never run a local leg with `-l`, `--showlocals`, `--pdb`, `--tb=long`, or
  `-vv`.** Each prints local values, which may hold pilot text, on a failure.
- **No release wording in this session's own words.** Commit messages, deviation
  notes, the verification record, and chat hold IDs, counts, and hashes, never a
  release's wording or a paraphrase of its content.
- **Drafting happens elsewhere.** The codebook and gold are drafted in fresh
  sessions the user starts with a committed brief, never in the executing session
  or a subagent (P9-5). The executing session never reads a draft, a working copy,
  or a view.
- **Subagents.** Every subagent dispatch, whether implementer, task reviewer, or
  the final code reviewer, carries this Blinding section verbatim. Gates run only
  in the controller session, with the user (Human gates).
- **Codex.** A Codex review takes no prompt, so it cannot carry this section, and
  it can read `data/`. It runs only as the user decides at Completion (P9-22).

> Deviation: the final review showed that pytest's default `--tb=auto` already prints a failing frame's arguments, so the list of flags above was not enough on its own; by the user's choice of 2026-10-03, the root `addopts` sets `--tb=short`, and the wording guard catches every exception by type (`c77824a`; Task 13).

> Deviation: at Gate 3 the user authorized two exceptions to "Drafting happens elsewhere": the executing session read the codebook draft once, and edited the codebook's working copy by script (Task 17). Implementer subagents on Tasks 5, 6, 8, 11, and 12 searched beyond the search rule, by finds, greps, or a listing of directory names, and the final review's fixer passed `--tb=long` once, to a collect-only run over synthetic tests; none exposed pilot text.

**Do not touch:**

- `AGENTS.md`. Other files cite it by line number (`CLAUDE.md` §Gotchas).
- `.gitignore`, whose credentials block stays last, and `.python-version`, which
  pins 3.14.0. `data/*` already ignores `data/runs/gold/`.
- `walker-1`'s generated files, `canonical/decode.py`, `dom.py`, and `walker.py`;
  `tests/fixtures/canonical/`; and the golden test. Task 1 adds a reader to
  `canonical/serialize.py`, which is not generated, and changes no output.
- Stage 1's frozen harness and records: every file that
  `expirements/parser-fidelity/FROZEN.toml` lists, `tests/fixtures/releases/` and its
  gold, and ADRs 0001 and 0002.
- The frozen records: everything under `config/`, and `tests/fixtures/cohort/` and
  `tests/fixtures/events/`, which stay byte-identical. Stage 6 reads them only
  (P-C7).
- `specs/pilot-codebook-split-and-gold-set-protocol.md`, except Tasks 8 and 12's
  amendments (P9-3, P9-4) and Completion's stage stamp.

**Stay in the main checkout.** Execute every task in the main checkout, on this
branch, never in a separate worktree. `data/` is gitignored, so a worktree lacks what
these read: Stage 5's states and canonical documents under `data/runs/events/`,
which the local legs and every gate read, and `data/raw/`, which the existing local
tests read. A drafting session starts in the main checkout too (P9-5).

**Staging discipline.**

- `git add` only the paths a task names, never `git add -A` or `git add .`.
- After each commit, `git status --short` must print nothing, apart from local
  untracked files that predate this plan. So a later task's file never enters an
  earlier commit.
- The user may commit on this branch while the plan runs. Run `git log --oneline -3`
  before each commit, and never rewrite a commit you did not make.

**Unicode escapes.** Every new or replaced Python file in this plan is ASCII, except
`§` in citations such as `A §191`.

- Tests build non-ASCII inputs from code points with `chr(0x...)`, and `tomlfile.py`
  writes TOML's escape for DEL as `chr(0x5C) + "u007f"`.
- No file carries a backslash-u escape that a tool channel might decode on the way
  to disk.
- Each task that writes Python runs the escape check below. It prints
  `escapes intact`, or else the name of each file holding another non-ASCII
  character.

**Writing files from this plan.** Every code block that holds a whole file, or a
section to append to one, follows a line of one of three forms:

- ``Create `<path>`:``;
- ``Replace `<path>` with:``;
- ``Append to `<path>`:``, which only the verification record uses.

Extract each such file with the helper below rather than retyping it. Retyping
thousands of lines invites silent slips, and a tool channel that decodes an escape
would do it again on a retry. The Preconditions save the two helpers once, as
`/tmp/plan9-extract.py` and `/tmp/plan9-escapes.py`. If `/tmp` has been cleared,
save them again from here.

`/tmp/plan9-extract.py`:

````python
"""Extract one file block from plan 9; run from the repository root.

usage: python3 /tmp/plan9-extract.py <path> [block number, default 1]
"""

import sys
from pathlib import Path

PLAN = Path("specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md")
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
held = path.read_text(encoding="utf-8").splitlines(True) if path.is_file() else []
heading = next((x for x in lines[start + 1 : end] if x.startswith("## ")), None)
if mode == "a" and heading in held:
    print(f"unchanged: {target} already holds {heading.strip()}")
    sys.exit()
path.parent.mkdir(parents=True, exist_ok=True)
with path.open(mode, encoding="utf-8", newline="\n") as out:
    out.write("".join(lines[start + 1 : end]))
verb = "appended to" if mode == "a" else "extracted"
print(f"{verb} {target}: {end - start - 1} lines")
````

`/tmp/plan9-escapes.py`:

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

- A step that says **extract** a path runs `python3 /tmp/plan9-extract.py <path>`,
  which prints `extracted <path>: <n> lines`. The block number is `1` for every
  path but one. `docs/verification/pilot-v1-gold-set.md` has six blocks: Task 14
  creates it from block 1, and Tasks 15 to 19 append blocks 2 to 6, each extracted
  with its number, which prints `appended to <path>: <n> lines`. A block is never
  appended twice: if the file already holds the block's `## ` heading, the helper
  prints `unchanged: <path> already holds <heading>` and writes nothing, and a
  resumed session fills whatever slot is left in the section that is there.
- **Edits to existing files.** Existing files change by exact replacement, never
  whole, but for one: Task 9 replaces `test_import_boundaries.py` from a
  ``Replace `<path>` with:`` block. The plan gives each change as a script,
  ``Create `/tmp/plan9-<name>.py`:``, that holds every old and new text, one line to
  a string. A step that says
  **apply** `<name>` runs:

  ```bash
  python3 /tmp/plan9-extract.py /tmp/plan9-<name>.py && python3 /tmp/plan9-<name>.py
  ```

  Each old text must match exactly once, and nothing is written unless every
  replacement in the script applies. A file that has drifted from the plan stops the
  script with its path. The script prints `edited <path>: <n> replacement(s)` for
  each file. Task 19's `task19-state` alone may run again: a file that holds its
  `DONE` line and none of its old texts was edited by an earlier run, prints
  `unchanged: <path>`, and is left as it is; a file that holds neither stops the
  script.
- The scripts that edit Markdown files hold those files' non-ASCII characters, such
  as `≥`, `–`, and `—`, as the files do. The escape check reads only the
  repository's Python files.
- If the escape check names a file, extract or apply it again and rerun the check.

**Lint.** `uv run --locked ruff check .` and `uv run --locked ruff format --check .`
pass after every task, and the code below already passes both.

- The Expected `N files already formatted` counts assume a clean checkout: 267
  before Task 1, growing with each task's new Python files.
- A different count with no `Would reformat` line comes from local untracked Python
  files, and is not a failure.

**Expected outputs.** At plan time this plan was replayed twice on a scratch
worktree cut from `6e3666e`, as the user chose (P9-2): once from the verified code,
and once from this plan's own blocks, through the two helpers, task by task. Both
replays printed the Expected outputs below. The scratch worktree read the main
checkout's `data/` through links, so its counts are the main checkout's, with one
exception: two existing tests call `git check-ignore`, which does not look past a
link, and failed there alone; the counts below add them back as passes. The replays
sent no request and wrote nothing under the main checkout's `data/` or `config/`.
The scratch worktrees and branches were deleted once this plan was written.

Tasks 14 to 19 are gates, and act on the user's decisions and the real documents.

- **Checks** are outputs that hold whatever the user and the drafts decide, such as
  the split's hash or the default suite's count. A check that differs stops the task.
- **Gate 1 was replayed.** Its commands ran on the replay's worktree over the real
  state table, printing IDs, counts, and hashes, and its checks are what they
  printed.
- **Gates 3 to 5 were not**, since no codebook or gold existed at plan time. Their
  counts are gate 1's, with one skipped local leg turned to a pass for each record a
  gate commits: codebook v0, the curated hard negatives, and the gold. They are
  checks too.
- **The drafts' own numbers,** such as a theme count, appear as `<t>` and are
  never predicted.

Anywhere else, if a count differs while nothing fails, stop and report it rather than
editing a test to match.

**Test imports.** Ruff sorts `earnings_core`, `earnings_ingestion`,
`earnings_themes`, and `earnings_pipeline` as third-party imports in test files, in
one block with `pytest`, and sorts `tomllib` among them, since the virtual root
declares no `requires-python`. Keep the imports as written.

**Public repository.** `origin` (https://github.com/lowmason/earnings-themes) is
public, so everything committed is published.

- Committed files hold IDs, offsets, labels, hashes, and the user's words, never a
  release's text (GS3). A quote is a pointer.
- Task 13's wording guard checks every committed Stage 6 file against Stage 1's
  fixtures always, and against the pilot's documents locally; each gate runs it with
  `-rs` and reads `passed`.
- The synthetic documents are invented. Stage 1's fixtures are committed with their
  source-register basis, and tests take their quotes from them when they run, never
  typed into a file.

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
- The **local legs** are `tests/integration/test_stage6_pilot_v1.py` and
  `tests/integration/test_stage6_wording.py`, run with `-q -rs`.

## Plan decisions

The spec leaves these choices open, so the plan makes them. The user can overturn any
of them before execution. The planning session of 2026-09-28 put seven choices to the
user, and P9-1 through P9-7 record the answers. The code records each decision where
it applies. Where a rule needed a reading, the reading is stated, and eight readings
are **flagged for the user**, because each narrows the spec's words or adds to them:
P9-12 through P9-19.

**P9-1 — Execution (the user's answer).** Subagent-driven, as the header says: a
fresh implementer per code task, with a task review between tasks, and a final
whole-branch review.

- **Gates run in the controller.** Tasks 14 to 19 are gates. The controller runs
  them itself, with the user, and never dispatches one. A subagent that reaches a
  gate stops and reports back.
- **Blinding travels.** Every dispatch carries Global Constraints' Blinding section
  verbatim, reviewers' included. A reviewer checks code and tests, never data.

**P9-2 — The plan-time replay (the user's answer).** The plan was replayed on a
scratch worktree, not in the main checkout: once from the verified code and once
from the plan's own blocks (Global Constraints, Expected outputs).

**P9-3 — File names without a colon (the user's answer; amends S §The gold and
§Anchoring and validation).** Event IDs hold a colon, such as
`cik-0000051143:2024-12-31`, and Git on Windows cannot check out a path that holds
one. The repository is public and gold is written once, so a later rename would mean
new versions. Every Stage 6 file named for an event takes `file_stem(event_id)`, the
ID with its colon as an underscore: `gold/cik-0000051143_2024-12-31.toml`, and the
local drafts, anchored files, views, and texts alike. The ID inside each file is
unchanged, and `gold validate` refuses a file whose name is not its event's. Task 12
amends S's two paths.

**P9-4 — `no_theme` is supports-only (the user's answer; amends S §The gold).**
`no_theme` is true exactly when no assignment pairs a claim with a codebook theme
under `supports`. An `unmatched` row, or a theme row that is `does_not_support` or
`uncertain`, leaves it true. S's bullet said "no assignment names a codebook theme";
Task 8 amends it, and `no_theme_of` enforces it.

**P9-5 — Drafting sessions (the user's answer).** The codebook, the curated hard
negatives, and each bundle's gold are drafted in fresh sessions the user starts,
never in the executing session.

- **Where.** In the main checkout, `/Users/lowell/Projects/earnings-themes`, on this
  branch, since the texts and the local documents are in its `data/`. Not in a
  worktree the app creates.
- **Which model.** Claude Opus 5.5 (`claude-opus-5-5`), chosen in the app's model
  picker before the first message. Each draft records it in `drafting_aid`.
- **One task a session.** One session drafts the codebook; one the curated hard
  negatives; and one each bundle, so no session sees another bundle's gold (GS13).
- **The handoff.** The executing session writes the texts the drafting session may
  read, gives the user the exact first message, and ends its turn. The drafting
  session reads its brief and writes one draft under `data/runs/gold/drafts/`.
- **The resume.** The user returns to the executing session, or starts a fresh one
  on this plan, and says the draft is written. Every gate task opens with a state
  probe, so a fresh session can resume mid-gate from the plan and the repository
  alone.

**P9-6 — The brief review is a gate of its own (the user's answer).** The user reads
both committed briefs at Task 16, before any drafting session starts, and may edit
them; the edits are committed before drafting.

**P9-7 — The exit's three bundles (the user's answer).** The first three train events
in the pilot's selection order: #1 `cik-0000051143:2024-12-31`, #3
`cik-0000093410:2025-03-31`, and #5 `cik-0000310158:2025-06-30`. The choice is by
order alone, fixed before any text is read.

**P9-8 — What the executing session may do (GS13).** Global Constraints' Blinding
section is the rule. The code backs it three ways:

- every command prints IDs, counts, reasons, paths, and hashes, and a refusal names
  its item by ID or field path (Task 3's `Refusal`), never by `Rejection.detail` or
  a validation error's input;
- `guarded` names an unforeseen error by its type alone, since its message may quote
  a document (Task 10);
- the CLI tests assert that no command prints any 20-character window of a canonical
  text they read (Task 10's canary), and the local legs bind every result before
  asserting.

**P9-9 — Reading a canonical document (a plan-made decision).** Stage 5 writes each
parsed document in Stage 3's fixture format, and nothing reads it back.
`from_fixture_json` does: each record through its `earnings-core` contract, and the
masks rebuilt through `apply_masks` under the manifest's policy, so a tampered file
is refused as the canonicalizer's own output would be. It lives beside
`to_fixture_json` in `canonical/serialize.py`, and changes no output.

**P9-10 — A TOML writer (a plan-made decision).** Drafts, codebook v0, and the gold
are TOML, which the user edits by hand. No TOML writer is locked, and GS17 adds no
dependency, so `tomlfile.dumps` writes the subset the records need: strings, integers,
booleans, dates, lists, tables, and arrays of tables, with bare keys only and `None`
left out. Strings are JSON-escaped, which TOML's basic strings accept, and DEL is
escaped, which JSON leaves raw. `tomllib` reads everything back.

**P9-11 — Local files (a plan-made decision).** Under `data/runs/gold/`:

| Path | Written by | Holds |
| --- | --- | --- |
| `texts/<event>.md`, `texts/fixtures/<fixture_id>.md` | `gold show --text` | one document's canonical text, for a drafting session |
| `drafts/<name>.draft.toml` | the drafting session | its draft, kept unchanged (GS4) |
| `drafts/<name>.working.toml` | the user, from a copy of the draft | the user's edits and signature |
| `anchored/<name>.toml` | `gold anchor` | the latest build of the working copy, signed or not |
| `views/<event>.md`, `views/hard-negatives/<fixture_id>.md` | `gold show` | the text with each quote marked, and the items listed |

`<name>` is an event's `file_stem`, or `codebook`, or `hard-negatives`. `gold anchor`
writes the committed record, once, only when the working copy is signed.
`gold anchor --check` writes nothing, and checks a draft alone when there is no
working copy yet, as a drafting session checks its own.

**P9-12 — Mask IDs (a reading; flagged).** S asks each quote to record "the IDs of
any boilerplate masks over it", and `OverlayMask` has no ID. A mask's ID is derived as
an element's is: `<category>-<start>-<end>`, such as `safe_harbor-1200-1650`.

**P9-13 — The codebook's content hash (a reading of S §The codebook; flagged).** S
asks ADR 0003 to cite the content hash, and asks `codebook freeze` to write
`approved` only once the ADR cites it. So the hash is taken over every field except
`status`, `approval`, and `content_hash` itself: the ADR can cite it before the
approval exists, and approving changes no hashed byte.

**P9-14 — The context hash (a reading of S §The gold; flagged).** A quote whose text
repeats records `context_sha256`: the SHA-256 of the UTF-8 bytes of
`json.dumps([prefix, suffix], ensure_ascii=False, separators=(",", ":"))`, where
`prefix` and `suffix` are `make_locator`'s context for the span.

**P9-15 — Fixture events (a reading of S §The split; flagged).** Stage 1's fixtures'
manifest names accessions, not events. An event is a fixture's when its
`release_accession` is an accession the manifest marks `train_or_exclude`. The issuer
rule applies first, so a fixture event already excluded keeps
`issuer_in_earlier_partition`. Pilot v1 holds no fixture event, so this reading
changes nothing today.

**P9-16 — The discovery corpus (a reading of S §The codebook; flagged).** The
training partition's events that have a parsed document. On pilot v1 that is all 20;
an event without one would be named by `codebook freeze`, never read.

**P9-17 — A document's `doc_id` (a reading of S §Inputs; flagged).** The `doc_id` the
document's last transition into `parsed` names, under the pin's pilot hash
(`parsed_documents`). A later stage's `partial` or `completed` transition carries no
`doc_id`, and keeps the document's.

**P9-18 — The signature (a reading of GS4; flagged).** A file is signed when its
`annotator` is not blank. GS4's form, "Lowell Mason (verified a Claude draft)", is
the convention the user writes, and the validator does not parse it.

**P9-19 — Narrative elements (a reading of GS15; flagged).** A quote sits in the most
specific narrative element that contains it, in this order: `sentence`, `list_item`,
`footnote`, `heading`, `paragraph`, `speaker_turn`, `section`; its `element_id` names
that element. A quote that overlaps a `table`, `table_cell`, `page_artifact`, or
`other` element is refused as `not_narrative`, and one no narrative element contains
as `outside_element`.

**P9-20 — ADR 0003 (a plan-made decision).** The executing session writes ADR 0003
from the codebook's IDs and hashes, with no theme's wording; the user reads it, may
edit it, and approves it at Task 17. The approver and the date are the user's.

**P9-21 — The wording check before a write (a plan-made decision).** S's wording
guard is a test over committed files, so it runs after a record is written, and a
committed record is written once. So every command that writes or rechecks a record
first checks it against every text the guard reads: each parsed pilot document and
each Stage 1 fixture (`wording_texts`, Task 10). It names each copy by its field and
the text's ID, never by text. The contracts' own checks cover less: the codebook's
covers the training releases, and a bundle's gold its own release.

- **One exception keeps the default suite offline.** `gold validate
  --hard-negatives` checks the curated set against the committed fixtures alone.
  `gold anchor --hard-negatives` checked it against the pilot's documents too, and
  the guard's local leg does so at each gate.
- **A refusal writes nothing.** `gold anchor` refuses a signed record that differs
  from one already written before it replaces the anchored copy, so a view never
  shows a record that was refused.

**P9-22 — Codex (a plan-made decision; the user decides at Completion).** The final
review (subagent-driven-development, or executing-plans) and
finishing-a-development-branch's Step 4b each run a Codex second opinion,
`codex exec review --base <BASE>`. That command takes no prompt, so the Blinding
section cannot reach it, and its read-only sandbox reads files as any reviewer
does, `data/` included, where the pilot's text is, the held-out test bundles' too.
So before the final review the executing session asks the user, in one question
with the recommended option first:

- **Skip Codex on this branch (recommended).** Both places state the reason, and
  no `Codex reviewed` line is written. The code-reviewer seat still runs, with the
  Blinding section.
- **Run Codex from a detached worktree without `data/`.** This lowers the risk
  without removing it: an absolute path still reaches the main checkout's `data/`.

## Requirement map

S §Verification, item by item:

| Item | What shows it | Task |
| --- | --- | --- |
| The split over the synthetic pilot | `test_each_issuer_keeps_the_partition_of_its_earliest_event`; `test_a_fixture_event_is_never_held_out`; `test_the_issuer_rule_comes_before_the_fixture_rule`; `test_split_freezes_once_and_prints_only_ids_and_counts` | 4, 10 |
| The split over pilot v1 and events v1, reproducing `split-v1.json`'s content hash | `test_the_split_gives_the_spec_s_counts_and_exclusions`; `test_the_committed_split_reproduces_byte_for_byte`, which runs once gate 1 commits the split | 13, 14 |
| The split and the report leave the pilot unchanged (P-C7) | `test_the_split_changes_no_frozen_record`; `test_coverage_counts_each_state_and_rereads_only_its_runs`; `test_gold_commits_only_once_signed_and_then_validates` | 10, 12, 13 |
| The coverage report over the synthetic acquisition, with its non-zero classes | `test_the_synthetic_acquisition_is_counted_by_state`; `test_a_rebuild_reads_only_the_runs_it_names`; `test_coverage_counts_each_state_and_rereads_only_its_runs` | 2, 10 |
| The codebook and gold contracts, the anchor, and the validator over Stage 1's fixtures, with a tamper test for each refusal | `test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors`; `test_a_tampered_pointer_is_refused`; `test_a_tampered_version_is_refused`; `test_another_document_pin_split_codebook_or_partition_is_refused`; `test_curated_hard_negatives_over_stage_1_fixtures_validate`; and the §Refusals rows below | 6, 7, 8 |
| The curated hard negatives, in the default suite | `test_the_curated_hard_negatives_validate_offline`, which runs once gate 4 commits them | 13, 18 |
| The wording guard's fixture leg | `test_no_stage_6_file_quotes_a_stage_1_fixture`; `test_a_copy_across_a_wrapped_line_is_caught` | 13 |
| Local: the real coverage report reproduces its hash | `test_the_committed_coverage_report_reproduces_from_its_runs` | 13, 14 |
| Local: every committed gold file validates | `test_committed_records_validate_against_the_local_store` | 13, 17, 19 |
| Local: the wording guard's pilot leg | `test_no_stage_6_file_quotes_a_pilot_document` | 13 |
| `docs/verification/pilot-v1-gold-set.md` | written section by section at each gate | 14–19 |

S §Refusals, each by a named test:

| Refusal | What shows it | Task |
| --- | --- | --- |
| A quote missing, repeated without context, outside a narrative element, or refused by `validate_span` (OCR text among its reasons) | `test_text_that_is_not_there_is_not_found`; `test_repeated_text_needs_context_and_records_its_hash`; `test_a_quote_outside_native_narrative_is_refused`; `test_a_quote_across_two_elements_is_outside_every_element`; `test_a_pointer_into_a_table_cell_is_not_narrative`; `test_a_bad_draft_is_refused_by_item`; `test_a_bad_gold_draft_is_refused_by_item_and_writes_nothing` | 6, 8, 12 |
| A `doc_id` that is not the pinned pilot's document, or whose canonical hash does not match | `test_another_document_pin_split_codebook_or_partition_is_refused`; `test_an_element_of_another_document_is_refused` | 1, 8 |
| A gold file with no signature, or whose `no_theme` disagrees with its assignments | `test_an_accepted_draft_builds_unsigned_and_fails_only_on_its_signature`; `test_a_blank_signature_is_not_a_signature`; `test_a_bad_draft_is_refused_by_item`; `test_gold_commits_only_once_signed_and_then_validates`; `test_a_blank_signature_commits_nothing` | 8, 12 |
| A codebook example outside the training partition, or a synthetic one without its flag | `test_an_example_that_cannot_stand_is_refused` | 7 |
| A committed free-text field sharing a 40-character window with the text | `test_wording_copied_from_a_training_bundle_is_refused`; `test_a_claim_that_copies_the_release_is_refused`; `test_a_codebook_that_copies_a_training_release_is_refused`; before any write, against every text the guard reads (P9-21): `test_a_record_is_checked_against_every_text_the_wording_guard_reads`, `test_a_codebook_that_copies_any_pilot_release_is_refused_before_its_hash`, `test_codebook_validate_checks_every_text_the_guard_reads`, `test_gold_that_copies_another_release_is_refused_before_anything_is_written`, `test_gold_validate_checks_every_text_the_guard_reads`, and `test_curated_hard_negatives_are_checked_against_the_pilot_before_a_write`; the wording guard | 7, 8, 10, 11, 12, 13 |
| A gold file naming another pin, split, or codebook version | `test_another_document_pin_split_codebook_or_partition_is_refused`; for the curated hard negatives, `test_curated_hard_negatives_carry_the_pin` | 8 |
| An event in two partitions; a pilot whose content hash is not the pin's; a universe whose operative hash is not the pin's | `test_an_event_in_two_partitions_is_refused`; `test_another_pilot_hash_is_refused`; `test_a_universe_that_is_not_the_pin_s_is_refused` | 4, 10 |
| `approved` unless ADR 0003 exists and cites the content hash | `test_a_frozen_version_validates_and_needs_its_adr`; `test_codebook_v0_is_written_only_once_its_adr_cites_it` | 7, 11 |

S §Exit criteria, the roadmap's Stage 6 Exit, clause by clause:

| Clause | Where | Task |
| --- | --- | --- |
| A test places each bundle, with all copies and revisions, in exactly one issuer-and-time split (R12.1/R12.3) | `split.py`; `test_an_event_in_two_partitions_is_refused`; `test_the_split_gives_the_spec_s_counts_and_exclusions` | 4, 13 |
| The coverage report states the observed counts, and reports a missing class as a gap, never repaired by reselecting (R12.4, D4) | `coverage.py`; `coverage-v1.json` | 2, 14 |
| A test shows the split and the report changing no row of the pilot manifest (P-C7) | the P-C7 row above | 10, 13 |
| Curated hard negatives exist as fixtures outside the pilot manifest, and the validator accepts hard-negative claims (R12.5, D4) | `tests/fixtures/gold/hard-negatives.toml`; `test_the_curated_hard_negatives_validate_offline` | 18 |
| Codebook v0's decision record names its training-partition discovery corpus (R9.2/R9.7) | ADR 0003 | 17 |
| Annotations on at least three bundles, including release-identification labels, pass the validator | three signed train bundles (P9-7) | 19 |
| The single-annotator limitation is recorded (R12.6, D2) | `docs/verification/pilot-v1-gold-set.md` | 19 |

## Human gates

S §Gates, with the brief review the user added (P9-6):

| Gate | When | Who | What it unblocks |
| --- | --- | --- | --- |
| 1: the split and the report | Task 14, Step 4 | user | Committing `split-v1.json` and `coverage-v1.json`, after reading the partition counts, the excluded events, and the gaps |
| 2: the backup | Task 15, Step 2 | user | Any drafting: the user confirms a backup of `data/` outside the repository (GS12) |
| The brief review | Task 16, Step 2 | user | Any drafting: the user reads both briefs, and any edit is committed first (P9-6) |
| 3: codebook v0 | Task 17: the drafting session (Step 3), the user's edits (Step 4), and the approval (Step 7) | user | ADR 0003 and codebook v0, frozen and committed |
| 4: the curated hard negatives | Task 18: the drafting session (Step 3), and the verification and signature (Step 5) | user | `tests/fixtures/gold/hard-negatives.toml` |
| 5: three train bundles | Task 19, once per bundle: the drafting session, the verification, the omission pass, and the signature | user | Three signed gold files, and Stage 6's exit |

- **Hard stops.** In subagent-driven execution, every gate runs in the controller
  session with the user, never in a subagent (P9-1). Each gate is a hard stop:
  nothing after it starts until the user has answered.
- **Drafting is the user's.** At gates 3, 4, and 5 the executing session hands off
  to a drafting session the user starts, and waits. It never drafts, and never reads
  a draft, a working copy, or a view (P9-5).
- **What a gate record holds, and where it comes from.** Every value a gate
  records comes from a command's output, a committed file, a commit message, or the
  user's answer. A value the repository does not hold is asked of the user, never
  guessed, and never read from a draft, a working copy, a view, or a text.
- **Resuming.** Each gate task opens with a state probe, and its table names the
  step to resume at. A record a command wrote but no commit holds yet is resumed,
  never rewritten by hand: rerunning the command prints `unchanged:` in place of
  `froze`, and every other line is the same. If an uncommitted record must change,
  delete that uncommitted file, never a committed one, and rerun its step. A section
  of the verification record is never appended twice: extracting it again prints
  `unchanged:`, and the slots already filled stay.
- **No `-m live` test, and no SEC request.** No task runs either.

## File map

Path abbreviations: `…/ingestion/` is `packages/earnings-ingestion/src/earnings_ingestion/`;
`…/themes/` is `packages/earnings-themes/src/earnings_themes/`; `…/pipeline/` is
`apps/earnings-pipeline/src/earnings_pipeline/`; and `…/pilot-v1/` is
`evaluation/djia-2024q3-2026q2/pilot-v1/`.

| Path | Responsibility | Task |
| --- | --- | --- |
| `…/ingestion/canonical/serialize.py` | modify: `from_fixture_json`, the fixture format read back | 1 |
| `packages/earnings-ingestion/tests/test_serialize_reader.py` | the reader's tests | 1 |
| `…/ingestion/events/coverage.py` | the pin, the D4 coverage report, and `parsed_documents` | 2 |
| `packages/earnings-ingestion/tests/test_events_coverage.py` | its tests | 2 |
| `…/themes/records.py`, `tomlfile.py`, `problems.py` | the record base and pin; TOML; refusal reasons | 3 |
| `…/themes/split.py` | `issuer-time/1` and the split manifest | 4 |
| `…/themes/wording.py` | F20's rule, labels and IDs only | 5 |
| `…/themes/anchoring.py` | bundles, span pointers, the anchor and its check | 6 |
| `…/themes/synthetic.py` | the tests' invented document, pin, split, and drafts | 6 |
| `…/themes/codebook.py` | the codebook contract, its drafts, freeze, and validator | 7 |
| `…/themes/gold.py`, `annotation.py` | the gold contract; drafts, origins, the build, and the validator | 8 |
| `…/themes/view.py` | the local texts and views | 9 |
| `packages/earnings-themes/tests/` | `conftest.py` and `test_*.py` for each module; `test_import_boundaries.py` replaced | 3–9 |
| `…/pipeline/stage6.py` | the pin, paths, loading, and output shared by Stage 6's commands | 10 |
| `…/pipeline/pilot_cli.py`, `codebook_cli.py`, `gold_cli.py` | `pilot split` and `coverage`; `codebook freeze` and `validate`; `gold anchor`, `show`, and `validate` | 10, 11, 12 |
| `…/pipeline/cli.py` | modify: registers the three groups | 10–12 |
| `apps/earnings-pipeline/tests/test_stage6_cli.py` | the commands over the synthetic pilot, with GS13's canary | 10–12 |
| `docs/data-dictionary.md` | modify: every new model and value, in the task that adds it (A §191), and Task 12's list of Stage 6 files | 2–4, 6–8, 12 |
| `tests/contracts/test_data_dictionary.py` | modify: each new model and enum, in the task that adds it | 2–4, 6–8 |
| `specs/pilot-codebook-split-and-gold-set-protocol.md` | modify: the amendments P9-4 and P9-3, and Completion's stamp | 8, 12 |
| `tests/integration/test_stage6_pilot_v1.py`, `test_stage6_wording.py` | pilot v1's split, the local legs, and the wording guard | 13 |
| `…/pilot-v1/briefs/codebook.md`, `gold.md` | the drafting briefs | 13 |
| `…/pilot-v1/split-v1.json`, `coverage-v1.json` | frozen at gate 1 | 14 |
| `docs/verification/pilot-v1-gold-set.md` | the record, a section per gate | 14–19 |
| `docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md`, `codebooks/djia-pilot/codebook-v0.toml` | frozen at gate 3 | 17 |
| `tests/fixtures/gold/hard-negatives.toml` | frozen at gate 4 | 18 |
| `…/pilot-v1/gold/<event>.toml` | three signed bundles, at gate 5 | 19 |
| `CLAUDE.md`, `README.md` | modify: the current state | 19 |

No other file changes, and `uv.lock` does not change.

## Preconditions — read before Task 1

- **Branch.** Work on `stage-6-pilot-codebook-split-and-gold-set` in the main
  checkout. At planning time its commits above `main` (`eb729d8`) were the roadmap
  reconcile (`21028a9`), the spec's three commits (`b33caab`, `4c08f07`, `6e3666e`),
  and this plan's commit, and the branch was unpushed. Run this and read the result:

  ```bash
  git switch stage-6-pilot-codebook-split-and-gold-set && git log --oneline -3 && git status --short
  ```

  Expected: the head is `docs(plan): plan 9, Stage 6: the pilot codebook, split, and gold-set protocol`,
  or a later commit the user made, and the status is empty.
- **Stay in the main checkout** (Global Constraints). Do not execute in a separate
  worktree.
- **Blinding.** Read Global Constraints' Blinding section before anything else, and
  give it verbatim to every subagent (P9-1).
- **Environment.** Run `uv sync --locked --all-packages`; the `dev` group syncs by
  default.
  - `uv --version` must print uv 0.12.15.
  - The interpreter is Python 3.14.0, pinned by `.python-version`.
- **Helpers.** Save the two helpers from Global Constraints, then check both:

  ```bash
  python3 /tmp/plan9-extract.py docs/no-such-file.md; python3 /tmp/plan9-escapes.py specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md
  ```

  Expected: `specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md has no block 1 for docs/no-such-file.md`,
  then the plan's own path. The plan holds non-ASCII characters, so this shows that
  the check works.
- **Resuming mid-plan.** A session that resumes after Task 1 has run skips the
  branch head and the baselines below: those hold only before Task 1. It saves the
  helpers again if `/tmp` was cleared, reads the Blinding section, and starts at the
  first unticked task, whose tests, or whose probe at a gate, check the state.
- **Baselines.** Re-measure them; do not trust these:

  ```bash
  uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
  uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
  uv run --locked ruff check . && uv run --locked ruff format --check .
  uv run --locked --all-packages python expirements/parser-fidelity/fetch_policy_pages.py verify
  ```

  Expected: `1544 passed, 1 skipped, 24 deselected`; `280 passed`;
  `All checks passed!` and `267 files already formatted`; `register quotes verified`.
  The skip reads `the first acquisition has run: docs/verification/djia-events.md
  records its count`.

  If the harness reports 278 passed and 2 skipped, the rendered copies are missing:
  stop and ask. If any other count differs, stop and report it.
- **Local data.** Stage 5's states and canonical documents must be here. Check them
  without reading a document's text:

  ```bash
  uv run --locked --all-packages python -c "
  from pathlib import Path
  from earnings_ingestion.events.state_table import read_runs
  from earnings_ingestion.events.states import DocumentState, current_states
  runs = Path('data/runs/events/states')
  now = current_states(read_runs(runs), '3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926')
  parsed = [t for t in now.values() if t.to_state is DocumentState.PARSED]
  here = [t for t in parsed if Path('data/runs/events/canonical', f'{t.doc_id}.json').is_file()]
  print(len(list(runs.glob('*.parquet'))), 'runs;', len(now), 'documents;', len(parsed), 'parsed;', len(here), 'canonical files')
  "
  ```

  Expected: `2 runs; 40 documents; 40 parsed; 40 canonical files`. If any differs,
  stop and ask: a missing canonical document regenerates offline from its saved
  exhibit through `canonicalize` (plan 8 §Handoffs), and the user decides whether
  to regenerate it.
- **No SEC, no model, no `-m live`** (Global Constraints). `EDGAR_IDENTITY` is
  exported, and nothing here needs it.

---

### Task 1: The canonical reader

S §Inputs, and P9-9. Stage 5 writes each parsed document to
`data/runs/events/canonical/<doc_id>.json` in Stage 3's fixture format, and nothing
reads it back. `from_fixture_json(text)` does: each record through its
`earnings-core` contract, the masks rebuilt through `apply_masks` under the
manifest's policy, and exactly the four parts, so a file that is not a canonical
document is refused rather than half-read. Every Stage 1 fixture reads back to the
same bytes.

**Files:**

- Modify, by exact replacement:
  `packages/earnings-ingestion/src/earnings_ingestion/canonical/serialize.py`.
- Test: create `packages/earnings-ingestion/tests/test_serialize_reader.py`.

**Interfaces:**

- Consumes: `to_fixture_json(result: Canonicalized) -> str` and `Canonicalized`
  (`document`, `elements`, `manifest`, `masked`) in `canonical/`; `apply_masks` and
  the core contracts.
- Produces: `PARTS = ("document", "elements", "manifest", "masks")`, and
  `from_fixture_json(text: str) -> Canonicalized`, which raises `ValueError` on a
  missing or extra part, and a pydantic `ValidationError` (a `ValueError`) on a
  record its contract refuses.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_serialize_reader.py`:

```python
"""The canonical-fixture format reads back losslessly (plan 9): Stage 6 loads each
pilot document from ``data/runs/events/canonical/<doc_id>.json`` this way."""

import json
from pathlib import Path

import pytest
from earnings_ingestion.canonical.serialize import from_fixture_json, to_fixture_json

REPO = Path(__file__).resolve().parents[3]
FIXTURES = sorted((REPO / "tests" / "fixtures" / "canonical").glob("*.json"))


def test_the_eight_stage_1_fixtures_are_read() -> None:
    assert len(FIXTURES) == 8


@pytest.mark.parametrize("path", FIXTURES, ids=lambda path: path.stem)
def test_a_committed_fixture_reads_back_to_the_same_bytes(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    result = from_fixture_json(text)
    assert result.document.source_document_id == path.stem
    assert to_fixture_json(result) == text


def test_the_masks_keep_the_manifests_policy() -> None:
    result = from_fixture_json(FIXTURES[0].read_text(encoding="utf-8"))
    assert result.masked.policy_id == result.manifest.mask_policy_id
    assert result.masked.policy_version == result.manifest.mask_policy_version


def test_a_missing_part_is_refused() -> None:
    data = json.loads(FIXTURES[0].read_text(encoding="utf-8"))
    del data["masks"]
    with pytest.raises(ValueError, match="exactly document, elements, manifest"):
        from_fixture_json(json.dumps(data))


def test_an_element_of_another_document_is_refused() -> None:
    data = json.loads(FIXTURES[0].read_text(encoding="utf-8"))
    data["elements"][0]["doc_id"] = "other@walker-1#0000000000000000"
    with pytest.raises(ValueError, match="another document"):
        from_fixture_json(json.dumps(data))
```

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-ingestion/tests/test_serialize_reader.py
```

Expected:

```text
extracted packages/earnings-ingestion/tests/test_serialize_reader.py: 43 lines
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_serialize_reader.py -q`

Expected: FAIL, `1 error`, with:

```text
ImportError: cannot import name 'from_fixture_json' from 'earnings_ingestion.canonical.serialize'
ERROR packages/earnings-ingestion/tests/test_serialize_reader.py
```

- [x] **Step 3: Read the fixture format back**

Create `/tmp/plan9-task1-impl.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "packages/earnings-ingestion/src/earnings_ingestion/canonical/serialize.py": [
        (
            "which elements changed and no editor or tool can alter a character.\n"
            "\"\"\"\n",
            "which elements changed and no editor or tool can alter a character.\n"
            "``from_fixture_json`` reads the format back, as Stage 6 reads a pilot document's\n"
            "``data/runs/events/canonical/<doc_id>.json`` (plan 9).\n"
            "\"\"\"\n",
        ),
        (
            "\n"
            "from pydantic import BaseModel\n",
            "\n"
            "from earnings_core import CanonicalDocument, DocumentElement, OverlayMask, apply_masks\n"
            "from pydantic import BaseModel\n",
        ),
        (
            "from earnings_ingestion.canonical.records import Canonicalized\n",
            "from earnings_ingestion.canonical.records import (\n"
            "    CanonicalizationManifest,\n"
            "    Canonicalized,\n"
            ")\n"
            "\n"
            "PARTS = (\"document\", \"elements\", \"manifest\", \"masks\")\n",
        ),
        (
            "    return \"[\\n\" + \",\\n\".join(rows) + \"\\n]\"\n",
            "    return \"[\\n\" + \",\\n\".join(rows) + \"\\n]\"\n"
            "\n"
            "\n"
            "def from_fixture_json(text: str) -> Canonicalized:\n"
            "    \"\"\"The ``Canonicalized`` that ``to_fixture_json`` wrote as ``text``.\n"
            "\n"
            "    Each record is read through its own contract from its own JSON, since the\n"
            "    contracts are strict. The masks' policy is the one the manifest records. Any\n"
            "    refusal is a ``ValueError``; a pydantic error's message holds the input, so a\n"
            "    caller that reads a pilot document never prints it (plan 9, GS13).\n"
            "    \"\"\"\n"
            "    data = json.loads(text)\n"
            "    if not isinstance(data, dict) or tuple(sorted(data)) != PARTS:\n"
            "        raise ValueError(f\"a canonical document holds exactly {', '.join(PARTS)}\")\n"
            "    document = CanonicalDocument.model_validate_json(json.dumps(data[\"document\"]))\n"
            "    manifest = CanonicalizationManifest.model_validate_json(\n"
            "        json.dumps(data[\"manifest\"])\n"
            "    )\n"
            "    masks = tuple(\n"
            "        OverlayMask.model_validate_json(json.dumps(record)) for record in data[\"masks\"]\n"
            "    )\n"
            "    return Canonicalized(\n"
            "        document=document,\n"
            "        elements=tuple(\n"
            "            DocumentElement.model_validate_json(json.dumps(record))\n"
            "            for record in data[\"elements\"]\n"
            "        ),\n"
            "        masked=apply_masks(\n"
            "            document,\n"
            "            masks,\n"
            "            policy_id=manifest.mask_policy_id,\n"
            "            policy_version=manifest.mask_policy_version,\n"
            "        ),\n"
            "        manifest=manifest,\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py /tmp/plan9-task1-impl.py && python3 /tmp/plan9-task1-impl.py
```

Expected:

```text
extracted /tmp/plan9-task1-impl.py: 84 lines
edited packages/earnings-ingestion/src/earnings_ingestion/canonical/serialize.py: 4 replacement(s)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_serialize_reader.py -q`

Expected: `12 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py packages/earnings-ingestion/src/earnings_ingestion/canonical/serialize.py packages/earnings-ingestion/tests/test_serialize_reader.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1556 passed, 1 skipped, 24 deselected`; `All checks passed!` and `268 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/canonical/serialize.py packages/earnings-ingestion/tests/test_serialize_reader.py
git commit -m "feat(canonical): read a canonical document back from its fixture format (plan 9)"
```

---

### Task 2: The D4 coverage report

S §The coverage report, GS8, and P9-17. The report counts the pinned pilot's
documents by their current state under the pin, reads only the runs it names, and
states each missing failure class as a gap citing D4. `parsed_documents` gives each
parsed document's `doc_id`, which the later tasks load.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py`.
- Test: create `packages/earnings-ingestion/tests/test_events_coverage.py`.
- Modify, by exact replacement: `tests/contracts/test_data_dictionary.py` (the test
  step) and `docs/data-dictionary.md` (the implementation step).

**Interfaces:**

- Consumes: `PilotManifest`, `EventManifest`, `UniverseManifest`;
  `StateTransition`, `DocumentState`, `AttemptOutcome`, `ExhibitChoice`,
  `current_states`, and `in_order` in `events/states.py`; `IngestionRecord` and
  `serialize`; and `events/fixture.py`'s synthetic acquisition, through
  `load_transitions`.
- Produces:
  - `PilotPin(pilot_id, pilot_version, pilot_hash, events_version, events_hash,
    universe_version, universe_operative_hash)`, and `pilot_pin(pilot, events,
    universe) -> PilotPin`, which raises `ValueError` if the chain does not hold;
  - `StateCount(state, count)`, `CoverageGap(state, basis="D4")`,
    `AppliedOverride(override_id, document_id, verdict)`, `NoThemeCount(partition,
    bundles, no_theme)`, and `CoverageReport(coverage_version, pin, run_ids,
    documents, states, gaps, overrides, no_theme=(), content_hash)` with
    `count(state) -> int`;
  - `build_coverage(pilot, pin, transitions, *, run_ids=None, version=1) ->
    CoverageReport`, `coverage_hash(report) -> str`, and `load_coverage(path) ->
    CoverageReport`;
  - `parsed_documents(transitions, pilot_hash) -> dict[str, str]`, event ID to
    `doc_id`.

- [x] **Step 1: Write the failing tests**

> Deviation: by the user's choice of 2026-09-28, `test_a_pilot_holding_no_failure_class_reports_three_gaps` also builds a pilot that holds no failure class, so the default suite reaches the three-gap case (`dcf65cf`); counts unchanged.

Create `packages/earnings-ingestion/tests/test_events_coverage.py`:

```python
"""The D4 coverage report (the Stage 6 spec, §The coverage report; plan 9): the
observed count of each state over the pilot's documents, each missing failure class
as a gap, the overrides applied, and only the runs it names."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.coverage import (
    AppliedOverride,
    CoverageGap,
    build_coverage,
    load_coverage,
    parsed_documents,
    pilot_pin,
)
from earnings_ingestion.events.fixture import (
    ACQUISITION,
    ACQUISITION_RUN,
    COHORT_MANIFEST,
    FIXTURE_DIR,
    load_transitions,
)
from earnings_ingestion.events.freeze import load_event_manifest, serialize
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitAttempt,
    ExhibitChoice,
    StateTransition,
)

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / FIXTURE_DIR
LATER = datetime(2026, 9, 30, 9, 0, tzinfo=UTC)
UNAVAILABLE = "cik-0009990003:2025-06-30:release"


@pytest.fixture(scope="module")
def synthetic():
    universe = load_manifest(REPO / COHORT_MANIFEST)
    pilot = load_pilot(ROOT / "pilot-v1.json", universe)
    events = load_event_manifest(ROOT / "events-v1.json")
    return (
        pilot,
        pilot_pin(pilot, events, universe),
        load_transitions(ROOT / ACQUISITION),
    )


def test_the_synthetic_acquisition_is_counted_by_state(synthetic) -> None:
    pilot, pin, transitions = synthetic
    report = build_coverage(pilot, pin, transitions)
    assert report.documents == len(pilot.rows) == 27
    assert {c.state: c.count for c in report.states if c.count} == {
        DocumentState.PARSED: 24,
        DocumentState.UNAVAILABLE: 2,
        DocumentState.FAILED: 1,
    }
    assert report.gaps == (CoverageGap(state=DocumentState.RESTRICTED),)
    assert report.overrides == ()
    assert report.run_ids == (ACQUISITION_RUN,)
    assert report.no_theme == ()


def test_a_pilot_holding_no_failure_class_reports_three_gaps(synthetic) -> None:
    pilot, pin, transitions = synthetic
    report = build_coverage(pilot, pin, [*transitions, *_override_run(transitions)])
    assert report.count(DocumentState.UNAVAILABLE) == 1
    assert [gap.state for gap in report.gaps] == [DocumentState.RESTRICTED]
    assert report.overrides == (
        AppliedOverride(
            override_id="release-doc-crvd-2025-06-30",
            document_id=UNAVAILABLE,
            verdict=AttemptOutcome.NOT_CONFIRMED,
        ),
    )
    assert report.run_ids == (ACQUISITION_RUN, "acquire-override")


def test_a_rebuild_reads_only_the_runs_it_names(synthetic) -> None:
    pilot, pin, transitions = synthetic
    first = build_coverage(pilot, pin, transitions)
    later = [*transitions, *_later_run(transitions)]
    assert build_coverage(pilot, pin, later, run_ids=first.run_ids) == first
    assert build_coverage(pilot, pin, later).count(DocumentState.PARTIAL) == 1


def test_an_unknown_run_and_another_pilot_are_refused(synthetic) -> None:
    pilot, pin, transitions = synthetic
    with pytest.raises(ValueError, match="no transition under the pilot in run x"):
        build_coverage(pilot, pin, transitions, run_ids=["x"])
    other = pin.model_copy(update={"pilot_hash": "0" * 64})
    with pytest.raises(ValueError, match="the pin names another pilot"):
        build_coverage(pilot, other, transitions)


def test_a_document_with_no_state_is_refused(synthetic) -> None:
    pilot, pin, transitions = synthetic
    kept = [t for t in transitions if t.document_id != UNAVAILABLE]
    with pytest.raises(ValueError, match=f"{UNAVAILABLE} has no state"):
        build_coverage(pilot, pin, kept)


def test_a_frozen_report_loads_and_a_tampered_one_is_refused(
    synthetic, tmp_path
) -> None:
    pilot, pin, transitions = synthetic
    report = build_coverage(pilot, pin, transitions)
    path = tmp_path / "coverage-v1.json"
    path.write_bytes(serialize(report))
    assert load_coverage(path) == report
    data = json.loads(path.read_text(encoding="utf-8"))
    data["gaps"] = []
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="does not hash to its content_hash"):
        load_coverage(path)


def test_the_pin_holds_the_chain(synthetic) -> None:
    _, pin, _ = synthetic
    assert pin.pilot_id == "djia-synthetic-pilot"
    assert pin.pilot_hash == (
        "71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c"
    )
    assert pin.events_hash == (
        "438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58"
    )


def _last(transitions, document_id: str) -> StateTransition:
    return [t for t in transitions if t.document_id == document_id][-1]


def _override_run(transitions) -> list[StateTransition]:
    """The unavailable document taken to parsed by an override whose attempt keeps
    ``not_confirmed``, as Disney's was in the real acquisition."""
    last = _last(transitions, UNAVAILABLE)
    common = {
        "document_id": last.document_id,
        "event_id": last.event_id,
        "run_id": "acquire-override",
        "recorded_at": LATER,
        "pilot_id": last.pilot_id,
        "pilot_version": last.pilot_version,
        "pilot_hash": last.pilot_hash,
        "frozen_accession": last.frozen_accession,
        "accession": last.frozen_accession,
        "exhibit": "crvd-ex992.htm",
        "artifact_sha256": "a" * 64,
        "retrieved_at": LATER,
        "override_id": "release-doc-crvd-2025-06-30",
    }
    attempt = ExhibitAttempt(
        accession=last.frozen_accession,
        filename="crvd-ex992.htm",
        exhibit_type="EX-99.2",
        choice=ExhibitChoice.OVERRIDE,
        outcome=AttemptOutcome.NOT_CONFIRMED,
        artifact_sha256="a" * 64,
    )
    return [
        StateTransition(
            **common,
            sequence=0,
            from_state=DocumentState.UNAVAILABLE,
            to_state=DocumentState.ACQUIRED,
        ),
        StateTransition(
            **common,
            sequence=1,
            from_state=DocumentState.ACQUIRED,
            to_state=DocumentState.PARSED,
            doc_id="0009990003-25-000005_crvd-ex992.htm@walker-1#0123456789abcdef",
            attempts=(attempt,),
        ),
    ]


def _later_run(transitions) -> list[StateTransition]:
    """A later stage's run under the same pilot: one document goes on to partial."""
    parsed = next(t for t in transitions if t.to_state is DocumentState.PARSED)
    return [
        StateTransition(
            **{
                **parsed.model_dump(),
                "run_id": "stage-7",
                "sequence": 0,
                "recorded_at": LATER,
                "from_state": DocumentState.PARSED,
                "to_state": DocumentState.PARTIAL,
                "doc_id": None,
                "attempts": (),
            }
        )
    ]


def test_parsed_documents_keep_their_doc_id_through_later_states(synthetic) -> None:
    _, pin, transitions = synthetic
    found = parsed_documents(transitions, pin.pilot_hash)
    assert len(found) == 24
    assert UNAVAILABLE.removesuffix(":release") not in found
    later = [*transitions, *_later_run(transitions)]
    (moved,) = [t.event_id for t in _later_run(transitions)]
    assert parsed_documents(later, pin.pilot_hash)[moved] == found[moved]
    overridden = parsed_documents(
        [*transitions, *_override_run(transitions)], pin.pilot_hash
    )
    assert overridden[UNAVAILABLE.removesuffix(":release")].startswith(
        "0009990003-25-000005_crvd-ex992.htm@walker-1#"
    )
    assert parsed_documents(transitions, "0" * 64) == {}
```

Create `/tmp/plan9-task2-tests.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "tests/contracts/test_data_dictionary.py": [
        (
            "pilot, and processing-state records.\n",
            "pilot, processing-state, and coverage records.\n",
        ),
        (
            "from earnings_ingestion.events import acceptance, states\n",
            "from earnings_ingestion.events import acceptance, coverage, states\n",
        ),
        (
            "    states.StateTransition,\n"
            "]\n",
            "    states.StateTransition,\n"
            "    coverage.PilotPin,\n"
            "    coverage.StateCount,\n"
            "    coverage.CoverageGap,\n"
            "    coverage.AppliedOverride,\n"
            "    coverage.NoThemeCount,\n"
            "    coverage.CoverageReport,\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-ingestion/tests/test_events_coverage.py
python3 /tmp/plan9-extract.py /tmp/plan9-task2-tests.py && python3 /tmp/plan9-task2-tests.py
```

Expected:

```text
extracted packages/earnings-ingestion/tests/test_events_coverage.py: 216 lines
extracted /tmp/plan9-task2-tests.py: 42 lines
edited tests/contracts/test_data_dictionary.py: 3 replacement(s)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_coverage.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL, `2 errors`, with:

```text
ModuleNotFoundError: No module named 'earnings_ingestion.events.coverage'
ImportError: cannot import name 'coverage' from 'earnings_ingestion.events'
ERROR packages/earnings-ingestion/tests/test_events_coverage.py
ERROR tests/contracts/test_data_dictionary.py
```

- [x] **Step 3: Build the report**

Create `packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py`:

```python
"""The D4 coverage report over the pinned pilot (the Stage 6 spec, §The coverage
report; GS8; plan 9).

- **What it counts.** Each pilot document's current state, read from the runs it
  names, and so each of ``unavailable``, ``restricted``, and ``failed``. A failure
  class the pilot does not hold is a coverage gap (D4): the pilot is never reselected
  to fill it (P-C7).
- **Overrides.** Each acquisition override applied to a pilot document, with the
  verdict its attempt kept, such as ``release-content/1``'s ``not_confirmed``.
- **Its runs.** The report names the runs it read, and a rebuild reads only those.
  So later runs under the same pilot, which move documents on to ``partial`` or
  ``completed``, never change it.
- **No text.** It holds IDs, states, counts, and hashes. An attempt's ``detail`` and
  a transition's ``corpus_error`` are free text, and it copies neither.
- **No theme.** ``no_theme`` stays empty until Stage 11 counts it over train and
  dev, and Stage 14 over test (R12.4, GS18).
"""

from collections import Counter
from collections.abc import Collection, Iterable
from pathlib import Path
from typing import Literal, Self

from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)

from earnings_ingestion.canonical.records import IngestionRecord
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.identity import operative_hash
from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.records import EventManifest, PilotManifest
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitChoice,
    StateTransition,
    current_states,
    in_order,
)

FAILURE_CLASSES = (
    DocumentState.UNAVAILABLE,
    DocumentState.RESTRICTED,
    DocumentState.FAILED,
)
"""R12.4's classes, which D4 reports as observed coverage."""


class _Part(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class PilotPin(_Part):
    """The pilot a Stage 6 record binds to (GS2); earnings-themes' ``Pin`` has the
    same fields, and the application builds both from one loaded pilot."""

    pilot_id: IdPart
    pilot_version: PositiveInt
    pilot_hash: Sha256Hex
    events_version: PositiveInt
    events_hash: Sha256Hex
    universe_version: PositiveInt
    universe_operative_hash: Sha256Hex


class StateCount(_Part):
    """How many pilot documents are in one state."""

    state: DocumentState
    count: NonNegativeInt


class CoverageGap(_Part):
    """A failure class the pilot does not hold (D4)."""

    state: DocumentState
    basis: Literal["D4"] = "D4"

    @model_validator(mode="after")
    def _a_failure_class(self) -> Self:
        if self.state not in FAILURE_CLASSES:
            raise ValueError(f"{self.state} is not one of R12.4's failure classes")
        return self


class AppliedOverride(_Part):
    """An acquisition override applied to a pilot document, and its verdict."""

    override_id: IdPart
    document_id: IdPart
    verdict: AttemptOutcome


class NoThemeCount(_Part):
    """Stage 11's and Stage 14's count of annotated bundles with no theme."""

    partition: Literal["train", "dev", "test"]
    bundles: NonNegativeInt
    no_theme: NonNegativeInt


class CoverageReport(IngestionRecord):
    """``coverage-v<N>.json``: the observed coverage of one pinned pilot."""

    coverage_version: PositiveInt
    pin: PilotPin
    run_ids: tuple[IdPart, ...]
    documents: NonNegativeInt
    states: tuple[StateCount, ...]
    gaps: tuple[CoverageGap, ...]
    overrides: tuple[AppliedOverride, ...]
    no_theme: tuple[NoThemeCount, ...] = ()
    content_hash: Sha256Hex

    @model_validator(mode="after")
    def _counts_agree(self) -> Self:
        if tuple(count.state for count in self.states) != tuple(DocumentState):
            raise ValueError("states lists every DocumentState once, in order")
        if sum(count.count for count in self.states) != self.documents:
            raise ValueError("the state counts sum to the documents")
        return self

    def count(self, state: DocumentState) -> int:
        """How many pilot documents are in ``state``."""
        return next(c.count for c in self.states if c.state is state)


def pilot_pin(
    pilot: PilotManifest, events: EventManifest, universe: UniverseManifest
) -> PilotPin:
    """The pin of a pilot loaded with its chain: its events and its universe."""
    definition = pilot.definition
    if events.definition.content_hash != definition.eligible_event_manifest_hash:
        raise ValueError("the event manifest is not the one the pilot names")
    if operative_hash(universe) != definition.universe_operative_hash:
        raise ValueError("the universe is not the one the pilot names")
    return PilotPin(
        pilot_id=definition.pilot_id,
        pilot_version=definition.pilot_version,
        pilot_hash=definition.content_hash,
        events_version=events.definition.event_manifest_version,
        events_hash=events.definition.content_hash,
        universe_version=universe.definition.universe_version,
        universe_operative_hash=definition.universe_operative_hash,
    )


def coverage_hash(report: CoverageReport) -> str:
    """The content hash: every field but ``content_hash`` itself."""
    return digest(report.model_dump(mode="json", exclude={"content_hash"}))


def _runs(transitions: Iterable[StateTransition]) -> list[str]:
    seen: list[str] = []
    for transition in in_order(transitions):
        if transition.run_id not in seen:
            seen.append(transition.run_id)
    return seen


def _overrides(
    transitions: Iterable[StateTransition], documents: Collection[str]
) -> tuple[AppliedOverride, ...]:
    kept: dict[tuple[str, str], AttemptOutcome] = {}
    for transition in in_order(transitions):
        if transition.override_id is None or transition.document_id not in documents:
            continue
        for attempt in transition.attempts:
            if attempt.choice is ExhibitChoice.OVERRIDE:
                key = (transition.override_id, transition.document_id)
                kept[key] = attempt.outcome
    return tuple(
        AppliedOverride(override_id=override, document_id=document, verdict=verdict)
        for (override, document), verdict in sorted(kept.items())
    )


def build_coverage(
    pilot: PilotManifest,
    pin: PilotPin,
    transitions: Iterable[StateTransition],
    *,
    run_ids: Collection[str] | None = None,
    version: int = 1,
) -> CoverageReport:
    """The coverage report over ``pilot``'s documents, from ``run_ids`` or, when
    none is named, from every run recorded under the pilot."""
    pilot_hash = pilot.definition.content_hash
    if pin.pilot_hash != pilot_hash:
        raise ValueError("the pin names another pilot")
    under = [t for t in transitions if t.pilot_hash == pilot_hash]
    recorded = _runs(under)
    if run_ids is not None:
        if unknown := sorted(set(run_ids) - set(recorded)):
            raise ValueError(f"no transition under the pilot in run {unknown[0]}")
        under = [t for t in under if t.run_id in run_ids]
    current = current_states(under, pilot_hash)
    documents = [f"{row.event_id}:release" for row in pilot.rows]
    if missing := [document for document in documents if document not in current]:
        raise ValueError(f"{missing[0]} has no state in these runs")
    counts = Counter(current[document].to_state for document in documents)
    draft = CoverageReport(
        coverage_version=version,
        pin=pin,
        run_ids=tuple(_runs(under)),
        documents=len(documents),
        states=tuple(
            StateCount(state=state, count=counts[state]) for state in DocumentState
        ),
        gaps=tuple(
            CoverageGap(state=state) for state in FAILURE_CLASSES if not counts[state]
        ),
        overrides=_overrides(under, set(documents)),
        content_hash="0" * 64,
    )
    return draft.model_copy(update={"content_hash": coverage_hash(draft)})


AFTER_PARSED = frozenset(
    {
        DocumentState.PARSED,
        DocumentState.PARTIAL,
        DocumentState.COMPLETED,
        DocumentState.COMPLETED_NO_THEME,
    }
)
"""The states of a document whose canonical document exists."""


def parsed_documents(
    transitions: Iterable[StateTransition], pilot_hash: str
) -> dict[str, str]:
    """Each pilot event whose document is ``parsed`` or later, with the ``doc_id``
    its ``parsed`` transition named: later stages' runs need not repeat it."""
    under = [t for t in in_order(transitions) if t.pilot_hash == pilot_hash]
    doc_ids = {
        t.event_id: t.doc_id
        for t in under
        if t.to_state is DocumentState.PARSED and t.doc_id is not None
    }
    current = current_states(under, pilot_hash)
    return {
        state.event_id: doc_ids[state.event_id]
        for state in current.values()
        if state.to_state in AFTER_PARSED and state.event_id in doc_ids
    }


def load_coverage(path: Path) -> CoverageReport:
    """A frozen report, refused unless it hashes to its ``content_hash``."""
    report = CoverageReport.model_validate_json(path.read_bytes())
    if coverage_hash(report) != report.content_hash:
        raise ValueError(f"{path} does not hash to its content_hash")
    return report
```

Create `/tmp/plan9-task2-impl.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/data-dictionary.md": [
        (
            "  reports any other difference as a problem.\n",
            "  reports any other difference as a problem.\n"
            "## earnings-ingestion coverage records, schema version 1\n"
            "\n"
            "`earnings_ingestion.events.coverage` builds Stage 6's D4 coverage report from the\n"
            "state table: the observed state of each pinned pilot document, read only from the\n"
            "runs the report names (the Stage 6 spec, §The coverage report; GS8).\n"
            "\n"
            "### `PilotPin`\n"
            "\n"
            "GS2's pin: the pilot, its event manifest, and its universe, each by version and hash.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `pilot_id` | ID part | The pilot's ID |\n"
            "| `pilot_version` | int ≥ 1 | Its version |\n"
            "| `pilot_hash` | 64 lowercase hex | Its `content_hash` |\n"
            "| `events_version` | int ≥ 1 | The event manifest it selected from |\n"
            "| `events_hash` | 64 lowercase hex | That manifest's `content_hash` |\n"
            "| `universe_version` | int ≥ 1 | The universe the pilot was selected over |\n"
            "| `universe_operative_hash` | 64 lowercase hex | That universe's `operative_hash` |\n"
            "\n"
            "### `StateCount`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `state` | `DocumentState` | A processing state |\n"
            "| `count` | int ≥ 0 | The pilot documents whose current state it is |\n"
            "\n"
            "### `CoverageGap`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `state` | `DocumentState` | `unavailable`, `restricted`, or `failed`, with a count of zero |\n"
            "| `basis` | `\"D4\"` | A missing class is a gap, never repaired by reselecting |\n"
            "\n"
            "### `AppliedOverride`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `override_id` | ID part | The acquisition override applied to a pilot document |\n"
            "| `document_id` | ID part | `<event_id>:release` |\n"
            "| `verdict` | `AttemptOutcome` | The verdict the override's attempt kept |\n"
            "\n"
            "### `NoThemeCount`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `partition` | `\"train\"`, `\"dev\"`, or `\"test\"` | The partition counted |\n"
            "| `bundles` | int ≥ 0 | Its bundles with signed gold |\n"
            "| `no_theme` | int ≥ 0 | Those whose gold has `no_theme` true |\n"
            "\n"
            "### `CoverageReport`\n"
            "\n"
            "`evaluation/<corpus>/pilot-v<N>/coverage-v<M>.json`, written once.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `schema_version` | `1` | Ingestion record schema version |\n"
            "| `coverage_version` | int ≥ 1 | The report's version |\n"
            "| `pin` | `PilotPin` | The pilot it covers |\n"
            "| `run_ids` | tuple of ID part | The runs it read; a rebuild reads only these |\n"
            "| `documents` | int ≥ 0 | The pilot's documents |\n"
            "| `states` | tuple of `StateCount` | Every `DocumentState`, in order, summing to `documents` |\n"
            "| `gaps` | tuple of `CoverageGap` | Each failure class with no document |\n"
            "| `overrides` | tuple of `AppliedOverride` | Each override applied to a pilot document |\n"
            "| `no_theme` | tuple of `NoThemeCount` | Empty until Stage 11 adds train and dev, and Stage 14 test (R12.4, GS18) |\n"
            "| `content_hash` | 64 lowercase hex | SHA-256 of the canonical JSON of every other field |\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py
python3 /tmp/plan9-extract.py /tmp/plan9-task2-impl.py && python3 /tmp/plan9-task2-impl.py
```

Expected:

```text
extracted packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py: 261 lines
extracted /tmp/plan9-task2-impl.py: 93 lines
edited docs/data-dictionary.md: 1 replacement(s)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_events_coverage.py tests/contracts/test_data_dictionary.py -q`

Expected: `122 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py packages/earnings-ingestion/tests/test_events_coverage.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1570 passed, 1 skipped, 24 deselected`; `All checks passed!` and `270 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-ingestion/src/earnings_ingestion/events/coverage.py packages/earnings-ingestion/tests/test_events_coverage.py tests/contracts/test_data_dictionary.py
git commit -m "feat(events): the D4 coverage report over the state table (GS8)"
```

---

### Task 3: Records, TOML files, and refusals

GS3, GS17, and P9-10. `earnings-themes` gains its record base: the pin as Stage 6
records carry it, canonical JSON and its digest, and a loader that names a file and
its problems without quoting its input. `tomlfile` writes and reads the TOML the
user edits. `problems` holds Stage 6's refusal reasons and `Refusal`, which names an
item and a reason and nothing else.

**Files:**

- Create: `packages/earnings-themes/src/earnings_themes/records.py`, `problems.py`,
  and `tomlfile.py`.
- Test: create `packages/earnings-themes/tests/test_tomlfile.py`.
- Modify, by exact replacement: `tests/contracts/test_data_dictionary.py` and
  `docs/data-dictionary.md`.

**Interfaces:**

- Consumes: `earnings_core`'s `IdPart`, `Sha256Hex`, and `sha256_hex`.
- Produces:
  - `THEMES_SCHEMA_VERSION = 1`; `Part`, the strict, frozen base that forbids
    unknown fields; `ThemesRecord(Part)` with `schema_version`; `NonBlank`; and
    `Pin`, with `PilotPin`'s seven fields;
  - `RecordError(name, problems)`; `canonical_json(value) -> bytes`,
    `digest(value) -> str`, and `record_json(record) -> bytes`;
    `describe(error) -> tuple[str, ...]`, a validation error's locations and
    messages without its input; `read_json(path) -> object`; and
    `parse(data, model, name) -> M`;
  - `Problem`, a `StrEnum`, and `Refusal(subject: str, reason: str)`, ordered, whose
    `str` is `"<subject>: <reason>"`;
  - `tomlfile.dumps(data, header="") -> str` and `tomlfile.read(path) -> dict`,
    which raises `RecordError` naming the file with `not found`, `not UTF-8`, or
    `not TOML at line L, column C`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/test_tomlfile.py`:

```python
"""Stage 6's TOML writer: whatever it writes, tomllib reads back unchanged."""

from datetime import date

import pytest
import tomllib
from earnings_themes.records import RecordError
from earnings_themes.tomlfile import dumps, read

AWKWARD = "".join(
    ['quote " and backslash \\ ', "tab\t", "newline\n", chr(0x7F), chr(0xE9)]
) + chr(0x1F600)


def test_scalars_tables_and_arrays_of_tables_round_trip() -> None:
    data = {
        "event_id": "cik-0009990001:2025-03-31",
        "no_theme": False,
        "count": 3,
        "drafted_on": date(2026, 10, 1),
        "tags": ["a", "b"],
        "empty": [],
        "aid": {"model_id": "m", "drafted_on": date(2026, 10, 2)},
        "themes": [
            {
                "theme_id": "t1",
                "examples": [{"text": "x"}, {"pointer": {"start": 1, "end": 2}}],
            },
            {"theme_id": "t2", "examples": []},
        ],
    }
    assert tomllib.loads(dumps(data)) == data


def test_a_string_round_trips_whatever_it_holds() -> None:
    assert tomllib.loads(dumps({"text": AWKWARD})) == {"text": AWKWARD}


def test_none_is_left_out_and_the_header_is_comments() -> None:
    text = dumps({"a": 1, "b": None}, header="Local draft.\nNever commit.")
    assert text.startswith("# Local draft.\n# Never commit.\n")
    assert tomllib.loads(text) == {"a": 1}


def test_a_key_that_is_not_bare_is_refused() -> None:
    with pytest.raises(ValueError, match="not a bare TOML key"):
        dumps({"a b": 1})


def test_a_file_that_is_not_toml_is_refused_by_position_only(tmp_path) -> None:
    path = tmp_path / "draft.toml"
    path.write_text("claim = 'Revenue rose sharply\n", encoding="utf-8")
    with pytest.raises(RecordError) as refused:
        read(path)
    assert refused.value.problems == ("not TOML at line 2, column 1",)
    assert "Revenue" not in str(refused.value)


def test_a_missing_file_is_refused_by_name(tmp_path) -> None:
    with pytest.raises(RecordError) as caught:
        read(tmp_path / "codebook.working.toml")
    assert (caught.value.name, caught.value.problems) == (
        "codebook.working.toml",
        ("not found",),
    )
```

Create `/tmp/plan9-task3-tests.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "tests/contracts/test_data_dictionary.py": [
        (
            "pilot, processing-state, and coverage records.\n",
            "pilot, processing-state, and coverage records; and earnings-themes' Stage 6 records.\n",
        ),
        (
            "from earnings_ingestion.fetch import records as fetch\n"
            "from pydantic import BaseModel\n",
            "from earnings_ingestion.fetch import records as fetch\n"
            "from earnings_themes import problems\n"
            "from earnings_themes import records as themes\n"
            "from pydantic import BaseModel\n",
        ),
        (
            "    coverage.CoverageReport,\n"
            "]\n",
            "    coverage.CoverageReport,\n"
            "    themes.Pin,\n"
            "]\n",
        ),
        (
            "    states.AttemptOutcome,\n"
            "]\n",
            "    states.AttemptOutcome,\n"
            "    problems.Problem,\n"
            "]\n",
        ),
        (
            "    )\n",
            "    )\n"
            "    assert (\n"
            "        f\"## earnings-themes records, schema version {themes.THEMES_SCHEMA_VERSION}\\n\"\n"
            "        in text\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/tests/test_tomlfile.py
python3 /tmp/plan9-extract.py /tmp/plan9-task3-tests.py && python3 /tmp/plan9-task3-tests.py
```

Expected:

```text
extracted packages/earnings-themes/tests/test_tomlfile.py: 65 lines
extracted /tmp/plan9-task3-tests.py: 56 lines
edited tests/contracts/test_data_dictionary.py: 5 replacement(s)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_tomlfile.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL, `2 errors`, with:

```text
ModuleNotFoundError: No module named 'earnings_themes.records'
ImportError: cannot import name 'problems' from 'earnings_themes'
ERROR packages/earnings-themes/tests/test_tomlfile.py
ERROR tests/contracts/test_data_dictionary.py
```

- [x] **Step 3: Write the three modules**

> Deviation: by the user's choices of 2026-09-28, `describe` prints `<key>` for an extra or refused key at any position, its check folded into `test_tomlfile.py`'s no-echo refusal test (`ed6a39f`, `672f48c`); and `records.py` keeps its copy of ingestion's `canonical_json` and digest, which a deferred item moves into earnings-core.

Create `packages/earnings-themes/src/earnings_themes/records.py`:

```python
"""What every earnings-themes record shares (Stage 6 spec, GS17).

- **The base.** Records are immutable, closed, and strictly typed, as earnings-core's
  contracts are. A top-level record carries ``schema_version``.
- **Hashing.** A frozen record's content hash is the SHA-256 of its canonical JSON:
  sorted keys, no whitespace, UTF-8. earnings-themes imports only earnings-core, so
  ``canonical_json`` repeats ``earnings_ingestion.cohort.digests``'s form rather than
  importing it.
- **Errors.** A pydantic error's message quotes its input, which may be a release's
  text. ``RecordError`` keeps each problem's field path and message only, never the
  input, so no command prints pilot text (GS13).
"""

import json
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from earnings_core import sha256_hex
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    BaseModel,
    ConfigDict,
    PositiveInt,
    StringConstraints,
    ValidationError,
)

THEMES_SCHEMA_VERSION = 1

NonBlank = Annotated[str, StringConstraints(pattern=r"\S")]
"""A string holding at least one non-space character."""


class Part(BaseModel):
    """A record or a part of one: immutable, closed, strictly typed."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class ThemesRecord(Part):
    """A top-level record, which carries its schema version."""

    schema_version: Literal[1] = THEMES_SCHEMA_VERSION


class Pin(Part):
    """The pilot every Stage 6 record binds to, by content hash (GS2)."""

    pilot_id: IdPart
    pilot_version: PositiveInt
    pilot_hash: Sha256Hex
    events_version: PositiveInt
    events_hash: Sha256Hex
    universe_version: PositiveInt
    universe_operative_hash: Sha256Hex


class RecordError(ValueError):
    """A file that does not read as its record; ``problems`` never quote input."""

    def __init__(self, name: str, problems: tuple[str, ...]) -> None:
        super().__init__(f"{name}: {'; '.join(problems)}")
        self.name = name
        self.problems = problems


def _default(value: object) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"{type(value).__name__} has no canonical JSON form")


def canonical_json(value: object) -> bytes:
    """``value`` as canonical JSON bytes; a model is dumped in JSON mode first."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    text = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_default,
    )
    return text.encode("utf-8")


def digest(value: object) -> str:
    """SHA-256 of ``value``'s canonical JSON."""
    return sha256_hex(canonical_json(value))


def record_json(record: BaseModel) -> bytes:
    """Indented JSON with sorted keys, as the corpus records are written."""
    text = json.dumps(
        record.model_dump(mode="json"), indent=1, sort_keys=True, ensure_ascii=False
    )
    return f"{text}\n".encode()


def describe(error: ValidationError) -> tuple[str, ...]:
    """Each problem as its field path and message, without the input."""
    return tuple(
        f"{'.'.join(str(part) for part in item['loc']) or 'record'}: {item['msg']}"
        for item in error.errors(include_input=False, include_url=False)
    )


def read_json(path: Path) -> object:
    """``path`` as JSON; a refusal names the line, never the text."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RecordError(path.name, ("not found",)) from None
    except json.JSONDecodeError as error:
        raise RecordError(path.name, (f"not JSON at line {error.lineno}",)) from None


def parse[M: BaseModel](data: object, model: type[M], name: str) -> M:
    """``data`` read as ``model``; a refusal is a ``RecordError`` named ``name``."""
    try:
        return model.model_validate_json(canonical_json(data))
    except ValidationError as error:
        raise RecordError(name, describe(error)) from None


__all__ = [
    "THEMES_SCHEMA_VERSION",
    "IdPart",
    "NonBlank",
    "Part",
    "Pin",
    "RecordError",
    "Sha256Hex",
    "ThemesRecord",
    "canonical_json",
    "describe",
    "digest",
    "parse",
    "read_json",
    "record_json",
]
```

Create `packages/earnings-themes/src/earnings_themes/problems.py`:

```python
"""Why a Stage 6 check refused something, as an item and a reason (the Stage 6 spec,
§Refusals).

A refusal names its subject by ID or field path and gives its reason, which is a
``Problem`` or one of earnings-core's ``RejectionReason`` values. It never carries a
quote, a claim, or a detail, since a detail may quote a release (GS13).
"""

from dataclasses import dataclass
from enum import StrEnum


class Problem(StrEnum):
    """Stage 6's own reasons; span checks give earnings-core's ``RejectionReason``."""

    MALFORMED = "malformed"
    NOT_NARRATIVE = "not_narrative"
    QUOTE_HASH_MISMATCH = "quote_hash_mismatch"
    CONTEXT_HASH_MISMATCH = "context_hash_mismatch"
    MASKS_MISMATCH = "masks_mismatch"
    WRONG_PIN = "wrong_pin"
    WRONG_SPLIT = "wrong_split"
    WRONG_PARTITION = "wrong_partition"
    EXCLUDED_EVENT = "excluded_event"
    WRONG_CODEBOOK = "wrong_codebook"
    CODEBOOK_NOT_APPROVED = "codebook_not_approved"
    UNSIGNED = "unsigned"
    NO_THEME_MISMATCH = "no_theme_mismatch"
    COUNTS_MISMATCH = "counts_mismatch"
    DUPLICATE_ID = "duplicate_id"
    UNKNOWN_QUOTE = "unknown_quote"
    UNKNOWN_CLAIM = "unknown_claim"
    UNKNOWN_THEME = "unknown_theme"
    UNKNOWN_DOCUMENT = "unknown_document"
    TIE_GROUP = "tie_group"
    SOURCE_WORDING = "source_wording"
    OUTSIDE_TRAINING = "outside_training"
    SYNTHETIC_UNFLAGGED = "synthetic_unflagged"
    PARENT_CYCLE = "parent_cycle"
    DISCOVERY_CORPUS = "discovery_corpus"
    CONTENT_HASH_MISMATCH = "content_hash_mismatch"
    NEGATIVE_KINDS = "negative_kinds"
    ADR_NOT_CITED = "adr_not_cited"


@dataclass(frozen=True, order=True)
class Refusal:
    """One refused item: its ID or field path, and the reason."""

    subject: str
    reason: str

    def __str__(self) -> str:
        return f"{self.subject}: {self.reason}"
```

Create `packages/earnings-themes/src/earnings_themes/tomlfile.py`:

```python
"""TOML for Stage 6's records and drafts: written here, read with ``tomllib``.

No TOML writer is locked, and GS17 adds no dependency, so ``dumps`` writes the one
shape these records need: scalars, arrays of scalars, tables, and arrays of tables,
in key order. A string is a TOML basic string, written as JSON writes one, which TOML
reads the same way, with DEL escaped as TOML requires.
"""

import json
import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import tomllib

from earnings_themes.records import RecordError

_BARE_KEY = re.compile(r"^[A-Za-z0-9_-]+$")


def _string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False).replace(chr(0x7F), chr(0x5C) + "u007f")


def _value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, list | tuple):
        return "[" + ", ".join(_value(item) for item in value) + "]"
    raise TypeError(f"no TOML form for {type(value).__name__}")


def _is_table_array(value: object) -> bool:
    return (
        isinstance(value, list | tuple)
        and bool(value)
        and all(isinstance(item, Mapping) for item in value)
    )


def _lines(data: Mapping[str, object], prefix: str) -> list[str]:
    lines = []
    for key, value in data.items():
        if not _BARE_KEY.match(key):
            raise ValueError(f"{key!r} is not a bare TOML key")
        if value is None or isinstance(value, Mapping) or _is_table_array(value):
            continue
        lines.append(f"{key} = {_value(value)}")
    for key, value in data.items():
        name = f"{prefix}{key}"
        if isinstance(value, Mapping):
            lines += ["", f"[{name}]", *_lines(value, f"{name}.")]
        elif _is_table_array(value):
            for entry in value:
                lines += ["", f"[[{name}]]", *_lines(entry, f"{name}.")]
    return lines


def dumps(data: Mapping[str, object], header: str = "") -> str:
    """``data`` as TOML, after ``header``'s lines as comments; ``None`` is left out."""
    comments = [f"# {line}".rstrip() for line in header.splitlines()]
    body = "\n".join(_lines(data, "")).strip("\n")
    return "\n".join([*comments, body]) + "\n"


def read(path: Path) -> dict:
    """``path`` as TOML; a refusal names the line and column, never the text."""
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        where = f"line {error.lineno}, column {error.colno}"
        raise RecordError(path.name, (f"not TOML at {where}",)) from None
    except UnicodeDecodeError:
        raise RecordError(path.name, ("not UTF-8",)) from None
    except FileNotFoundError:
        raise RecordError(path.name, ("not found",)) from None
```

Create `/tmp/plan9-task3-impl.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/data-dictionary.md": [
        (
            "| `content_hash` | 64 lowercase hex | SHA-256 of the canonical JSON of every other field |\n"
            "\n",
            "| `content_hash` | 64 lowercase hex | SHA-256 of the canonical JSON of every other field |\n"
            "\n"
            "## earnings-themes records, schema version 1\n"
            "\n"
            "`earnings_themes` holds Stage 6's split, codebook, and gold contracts (the Stage 6\n"
            "spec, specs/pilot-codebook-split-and-gold-set-protocol.md). Every model is strict,\n"
            "frozen, and refuses unknown fields. A committed record holds IDs, hashes, pointers,\n"
            "and the user's words, never a release's wording: a quote is a pointer, and the\n"
            "wording guard refuses any 40-character window, dates masked, shared with a pilot\n"
            "document or a Stage 1 fixture.\n"
            "\n"
            "### `Problem`\n"
            "\n"
            "Stage 6's own refusal reasons; a span check's reason is earnings-core's\n"
            "`RejectionReason`. A refusal names its item by ID or field path, never by text.\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `malformed` | A draft item is inconsistent, such as a synthetic example with an event |\n"
            "| `not_narrative` | A quote overlaps a table, cell, page artifact, or other non-narrative element (GS15) |\n"
            "| `quote_hash_mismatch` | A pointer's slice does not hash to its `quote_sha256` |\n"
            "| `context_hash_mismatch` | Its context does not hash to its `context_sha256` |\n"
            "| `masks_mismatch` | Its `mask_ids` are not the masks over it |\n"
            "| `wrong_pin` | The record names another pin |\n"
            "| `wrong_split` | It names another split |\n"
            "| `wrong_partition` | Its partition is not its event's |\n"
            "| `excluded_event` | Its event is excluded |\n"
            "| `wrong_codebook` | It names another codebook version |\n"
            "| `codebook_not_approved` | Its codebook is not approved |\n"
            "| `unsigned` | Its `annotator` is blank |\n"
            "| `no_theme_mismatch` | Its `no_theme` disagrees with its assignments |\n"
            "| `counts_mismatch` | Its origin counts disagree with its items |\n"
            "| `duplicate_id` | An ID repeats, or a theme takes the reserved `unmatched` |\n"
            "| `unknown_quote` | A claim names a quote the record lacks |\n"
            "| `unknown_claim` | An assignment names a claim the record lacks |\n"
            "| `unknown_theme` | An assignment, hard negative, or parent names a theme the codebook lacks |\n"
            "| `unknown_document` | The event or fixture has no document here, or is not in the split |\n"
            "| `tie_group` | A tie group holds rows of more than one claim, or only one row |\n"
            "| `source_wording` | A string shares a 40-character window with a document's text |\n"
            "| `outside_training` | A codebook example is not from a training bundle |\n"
            "| `synthetic_unflagged` | An example names no event and is not marked synthetic |\n"
            "| `parent_cycle` | Themes' parents form a cycle |\n"
            "| `discovery_corpus` | The codebook's discovery corpus is not the split's parsed training bundles |\n"
            "| `content_hash_mismatch` | A record's `content_hash` is not its content's |\n"
            "| `negative_kinds` | The curated hard negatives lack a kind |\n"
            "| `adr_not_cited` | ADR 0003 does not cite the codebook's content hash |\n"
            "\n"
            "### `Pin`\n"
            "\n"
            "`PilotPin`, as earnings-themes reads it: the same fields and values.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `pilot_id` | ID part | The pilot's ID |\n"
            "| `pilot_version` | int ≥ 1 | Its version |\n"
            "| `pilot_hash` | 64 lowercase hex | Its `content_hash` |\n"
            "| `events_version` | int ≥ 1 | The event manifest it selected from |\n"
            "| `events_hash` | 64 lowercase hex | That manifest's `content_hash` |\n"
            "| `universe_version` | int ≥ 1 | The universe the pilot was selected over |\n"
            "| `universe_operative_hash` | 64 lowercase hex | That universe's `operative_hash` |\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/records.py
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/problems.py
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/tomlfile.py
python3 /tmp/plan9-extract.py /tmp/plan9-task3-impl.py && python3 /tmp/plan9-task3-impl.py
```

Expected:

```text
extracted packages/earnings-themes/src/earnings_themes/records.py: 143 lines
extracted packages/earnings-themes/src/earnings_themes/problems.py: 54 lines
extracted packages/earnings-themes/src/earnings_themes/tomlfile.py: 83 lines
extracted /tmp/plan9-task3-impl.py: 87 lines
edited docs/data-dictionary.md: 1 replacement(s)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_tomlfile.py tests/contracts/test_data_dictionary.py -q`

Expected: `122 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py packages/earnings-themes/src/earnings_themes/problems.py packages/earnings-themes/src/earnings_themes/records.py packages/earnings-themes/src/earnings_themes/tomlfile.py packages/earnings-themes/tests/test_tomlfile.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1578 passed, 1 skipped, 24 deselected`; `All checks passed!` and `274 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-themes/src/earnings_themes/problems.py packages/earnings-themes/src/earnings_themes/records.py packages/earnings-themes/src/earnings_themes/tomlfile.py packages/earnings-themes/tests/test_tomlfile.py tests/contracts/test_data_dictionary.py
git commit -m "feat(themes): Stage 6's records, TOML files, and refusals"
```

---

### Task 4: The split

S §The split, GS6, GS7, GS10, and P9-15. `issuer-time/1` places each pinned event by
the calendar quarter of its period end, keeps each issuer in the partition of its
earliest event, and excludes the rest with a reason. The manifest is sorted, holds
each event once, and is hashed as the corpus records are.

**Files:**

- Create: `packages/earnings-themes/src/earnings_themes/split.py`.
- Test: create `packages/earnings-themes/tests/test_split.py`.
- Modify, by exact replacement: `tests/contracts/test_data_dictionary.py` and
  `docs/data-dictionary.md`.

**Interfaces:**

- Consumes: Task 3's `Pin`, `ThemesRecord`, `Part`, `digest`, `read_json`, and
  `parse`.
- Produces: `SPLIT_POLICY = "issuer-time/1"`; `Partition` (`train`, `dev`, `test`,
  `excluded`) and `ExclusionReason`; `SplitWindow`, `WINDOWS`, `SplitEvent(event_id,
  issuer_id, period_end)`, `SplitRow`, and `SplitManifest` with
  `partition_of(event_id) -> Partition`, which raises `KeyError`, and
  `events_in(partition) -> tuple[str, ...]`; `quarter(day) -> str`,
  `window_of(day) -> Partition`; `split_events(events, pin, *, fixture_event_ids=
  frozenset(), version=1) -> SplitManifest`; `split_hash(manifest) -> str`; and
  `load_split(path) -> SplitManifest`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/test_split.py`:

```python
"""issuer-time/1 (Stage 6 spec, §The split): each event in exactly one partition,
an issuer's events with its earliest, and fixtures never held out."""

import json
from datetime import date

import pytest
from earnings_themes.records import Pin, RecordError, record_json
from earnings_themes.split import (
    SPLIT_POLICY,
    WINDOWS,
    ExclusionReason,
    Partition,
    SplitEvent,
    load_split,
    quarter,
    split_events,
    split_hash,
    window_of,
)

PIN = Pin(
    pilot_id="synthetic-pilot",
    pilot_version=1,
    pilot_hash="1" * 64,
    events_version=1,
    events_hash="2" * 64,
    universe_version=1,
    universe_operative_hash="3" * 64,
)


def event(issuer: str, period_end: str) -> SplitEvent:
    return SplitEvent(
        event_id=f"cik-{issuer}:{period_end}",
        issuer_id=f"cik-{issuer}",
        period_end=date.fromisoformat(period_end),
    )


def placed(events: list[SplitEvent], **options: object) -> dict[str, tuple]:
    manifest = split_events(events, PIN, **options)
    return {row.event_id: (row.partition, row.reason) for row in manifest.rows}


@pytest.mark.parametrize(
    ("day", "partition"),
    [
        ("2024-07-01", Partition.TRAIN),
        ("2025-06-30", Partition.TRAIN),
        ("2025-07-01", Partition.DEV),
        ("2025-12-31", Partition.DEV),
        ("2026-01-01", Partition.TEST),
        ("2026-06-30", Partition.TEST),
    ],
)
def test_the_window_is_the_quarter_of_the_period_end(day: str, partition) -> None:
    assert window_of(date.fromisoformat(day)) is partition


@pytest.mark.parametrize("day", ["2024-06-30", "2026-07-01"])
def test_a_period_end_outside_the_windows_is_refused(day: str) -> None:
    with pytest.raises(ValueError, match="in no window of issuer-time/1"):
        window_of(date.fromisoformat(day))


def test_a_quarter_is_named_by_its_year_and_number() -> None:
    assert quarter(date(2024, 8, 31)) == "2024Q3"
    assert quarter(date(2026, 2, 1)) == "2026Q1"


def test_each_issuer_keeps_the_partition_of_its_earliest_event() -> None:
    events = [
        event("0000000001", "2024-09-30"),
        event("0000000001", "2025-03-31"),
        event("0000000001", "2026-06-30"),
        event("0000000002", "2025-09-30"),
        event("0000000002", "2025-12-31"),
        event("0000000002", "2026-03-31"),
        event("0000000003", "2026-03-31"),
    ]
    later = (Partition.EXCLUDED, ExclusionReason.ISSUER_IN_EARLIER_PARTITION)
    assert placed(events) == {
        "cik-0000000001:2024-09-30": (Partition.TRAIN, None),
        "cik-0000000001:2025-03-31": (Partition.TRAIN, None),
        "cik-0000000001:2026-06-30": later,
        "cik-0000000002:2025-09-30": (Partition.DEV, None),
        "cik-0000000002:2025-12-31": (Partition.DEV, None),
        "cik-0000000002:2026-03-31": later,
        "cik-0000000003:2026-03-31": (Partition.TEST, None),
    }


def test_a_fixture_event_is_never_held_out() -> None:
    events = [
        event("0000000004", "2024-12-31"),
        event("0000000005", "2025-09-30"),
        event("0000000006", "2026-03-31"),
    ]
    fixtures = {event.event_id for event in events}
    held = (Partition.EXCLUDED, ExclusionReason.FIXTURE_TRAIN_OR_EXCLUDE)
    assert placed(events, fixture_event_ids=fixtures) == {
        "cik-0000000004:2024-12-31": (Partition.TRAIN, None),
        "cik-0000000005:2025-09-30": held,
        "cik-0000000006:2026-03-31": held,
    }


def test_the_issuer_rule_comes_before_the_fixture_rule() -> None:
    events = [event("0000000007", "2024-12-31"), event("0000000007", "2025-09-30")]
    assert placed(events, fixture_event_ids={events[1].event_id})[
        events[1].event_id
    ] == (Partition.EXCLUDED, ExclusionReason.ISSUER_IN_EARLIER_PARTITION)


def test_the_manifest_records_the_rule_the_windows_and_the_pin() -> None:
    manifest = split_events([event("0000000001", "2024-09-30")], PIN)
    assert manifest.split_policy == SPLIT_POLICY == "issuer-time/1"
    assert manifest.split_version == 1
    assert manifest.windows == WINDOWS
    assert manifest.pin == PIN
    assert manifest.content_hash == split_hash(manifest)


def test_the_order_of_the_input_changes_nothing() -> None:
    events = [event("0000000001", "2025-03-31"), event("0000000001", "2024-09-30")]
    assert split_events(events, PIN) == split_events(events[::-1], PIN)


def test_an_event_listed_twice_is_refused() -> None:
    with pytest.raises(ValueError, match="listed twice"):
        split_events([event("0000000001", "2024-09-30")] * 2, PIN)


def test_a_frozen_split_loads_and_a_tampered_one_is_refused(tmp_path) -> None:
    manifest = split_events(
        [event("0000000001", "2024-09-30"), event("0000000002", "2025-09-30")], PIN
    )
    path = tmp_path / "split-v1.json"
    path.write_bytes(record_json(manifest))
    assert load_split(path) == manifest
    data = json.loads(path.read_text(encoding="utf-8"))
    data["rows"][1]["partition"] = "train"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RecordError, match="does not hash to its content_hash"):
        load_split(path)


def test_an_event_in_two_partitions_is_refused(tmp_path) -> None:
    manifest = split_events([event("0000000001", "2024-09-30")], PIN)
    data = json.loads(record_json(manifest))
    data["rows"].append({**data["rows"][0], "partition": "dev"})
    path = tmp_path / "split-v1.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RecordError, match="each event is in one"):
        load_split(path)
```

Create `/tmp/plan9-task4-tests.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "tests/contracts/test_data_dictionary.py": [
        (
            "from earnings_themes import problems\n",
            "from earnings_themes import problems, split\n",
        ),
        (
            "    themes.Pin,\n"
            "]\n",
            "    themes.Pin,\n"
            "    split.SplitWindow,\n"
            "    split.SplitEvent,\n"
            "    split.SplitRow,\n"
            "    split.SplitManifest,\n"
            "]\n",
        ),
        (
            "    problems.Problem,\n"
            "]\n",
            "    problems.Problem,\n"
            "    split.Partition,\n"
            "    split.ExclusionReason,\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/tests/test_split.py
python3 /tmp/plan9-extract.py /tmp/plan9-task4-tests.py && python3 /tmp/plan9-task4-tests.py
```

Expected:

```text
extracted packages/earnings-themes/tests/test_split.py: 156 lines
extracted /tmp/plan9-task4-tests.py: 44 lines
edited tests/contracts/test_data_dictionary.py: 3 replacement(s)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_split.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL, `2 errors`, with:

```text
ModuleNotFoundError: No module named 'earnings_themes.split'
ImportError: cannot import name 'split' from 'earnings_themes'
ERROR packages/earnings-themes/tests/test_split.py
ERROR tests/contracts/test_data_dictionary.py
```

- [x] **Step 3: Write the rule**

> Deviation: after the final review (`c77824a`), `events_in` compares with `==`, so `events_in("train")` finds the train events (T4-M1).

Create `packages/earnings-themes/src/earnings_themes/split.py`:

```python
"""``issuer-time/1``: the pinned pilot's split by issuer and time (Stage 6 spec, §The
split; GS6, GS7).

- **Inputs.** Each pilot event's ``event_id``, ``issuer_id``, and ``period_end``, and
  the events that are Stage 1 fixtures. No document, state, or outcome (P-C7).
- **Windows.** The calendar quarter of ``period_end``: train 2024Q3-2025Q2, dev
  2025Q3-2025Q4, test 2026Q1-2026Q2.
- **Issuers.** An issuer's events go to the partition of its earliest event. A later
  event whose window is another partition is ``excluded``,
  ``issuer_in_earlier_partition``.
- **Fixtures.** A Stage 1 fixture's event whose window is dev or test is
  ``excluded``, ``fixture_train_or_exclude``: fixtures are never held out. The issuer
  check comes first.
- **Bundles.** A bundle is an event, so every document of an event, with its copies
  and revisions, takes the event's partition (R12.1, R12.3).

The manifest is written once. A changed rule is a new version, never an edit.
"""

from collections.abc import Collection, Iterable
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import PositiveInt, StringConstraints, model_validator

from earnings_themes.records import (
    IdPart,
    Part,
    Pin,
    RecordError,
    Sha256Hex,
    ThemesRecord,
    digest,
    parse,
    read_json,
)

SPLIT_POLICY = "issuer-time/1"

Quarter = Annotated[str, StringConstraints(pattern=r"^[0-9]{4}Q[1-4]$")]


class Partition(StrEnum):
    """Where ``issuer-time/1`` puts an event."""

    TRAIN = "train"
    DEV = "dev"
    TEST = "test"
    EXCLUDED = "excluded"


class ExclusionReason(StrEnum):
    """Why an event is in no partition."""

    ISSUER_IN_EARLIER_PARTITION = "issuer_in_earlier_partition"
    FIXTURE_TRAIN_OR_EXCLUDE = "fixture_train_or_exclude"


class SplitWindow(Part):
    """One partition's quarters, first and last inclusive."""

    partition: Partition
    first: Quarter
    last: Quarter


WINDOWS = (
    SplitWindow(partition=Partition.TRAIN, first="2024Q3", last="2025Q2"),
    SplitWindow(partition=Partition.DEV, first="2025Q3", last="2025Q4"),
    SplitWindow(partition=Partition.TEST, first="2026Q1", last="2026Q2"),
)


class SplitEvent(Part):
    """One pilot event, as the rule reads it."""

    event_id: IdPart
    issuer_id: IdPart
    period_end: date


class SplitRow(Part):
    """One pilot event and its partition."""

    event_id: IdPart
    issuer_id: IdPart
    period_end: date
    partition: Partition
    reason: ExclusionReason | None = None

    @model_validator(mode="after")
    def _reason_exactly_when_excluded(self) -> Self:
        if (self.partition is Partition.EXCLUDED) != (self.reason is not None):
            raise ValueError("an excluded event has a reason, and only it")
        return self


class SplitManifest(ThemesRecord):
    """``split-v<N>.json``: the frozen split of one pinned pilot."""

    split_policy: Literal["issuer-time/1"]
    split_version: PositiveInt
    windows: tuple[SplitWindow, ...]
    pin: Pin
    rows: tuple[SplitRow, ...]
    content_hash: Sha256Hex

    @model_validator(mode="after")
    def _one_row_per_event(self) -> Self:
        ids = [row.event_id for row in self.rows]
        if ids != sorted(set(ids)):
            raise ValueError("rows are sorted by event_id, and each event is in one")
        if self.windows != WINDOWS:
            raise ValueError(f"{SPLIT_POLICY}'s windows are fixed")
        return self

    def partition_of(self, event_id: str) -> Partition:
        """The partition of one pilot event; ``KeyError`` for any other."""
        for row in self.rows:
            if row.event_id == event_id:
                return row.partition
        raise KeyError(event_id)

    def events_in(self, partition: Partition) -> tuple[str, ...]:
        """The events of one partition, by ``event_id``."""
        return tuple(row.event_id for row in self.rows if row.partition is partition)


def quarter(day: date) -> str:
    """The calendar quarter of ``day``, such as ``2024Q3``."""
    return f"{day.year}Q{(day.month - 1) // 3 + 1}"


def window_of(day: date) -> Partition:
    """The partition whose window holds ``day``'s quarter."""
    named = quarter(day)
    for window in WINDOWS:
        if window.first <= named <= window.last:
            return window.partition
    raise ValueError(f"{named} is in no window of {SPLIT_POLICY}")


def split_hash(manifest: SplitManifest) -> str:
    """The content hash: every field but ``content_hash`` itself."""
    return digest(manifest.model_dump(mode="json", exclude={"content_hash"}))


def split_events(
    events: Iterable[SplitEvent],
    pin: Pin,
    *,
    fixture_event_ids: Collection[str] = frozenset(),
    version: int = 1,
) -> SplitManifest:
    """Split ``events`` by ``issuer-time/1``."""
    events = sorted(events, key=lambda event: event.event_id)
    if len({event.event_id for event in events}) != len(events):
        raise ValueError("an event is listed twice")
    home: dict[str, Partition] = {}
    for event in sorted(events, key=lambda event: (event.period_end, event.event_id)):
        home.setdefault(event.issuer_id, window_of(event.period_end))
    rows = []
    for event in events:
        window = window_of(event.period_end)
        reason = None
        if window is not home[event.issuer_id]:
            reason = ExclusionReason.ISSUER_IN_EARLIER_PARTITION
        elif event.event_id in fixture_event_ids and window is not Partition.TRAIN:
            reason = ExclusionReason.FIXTURE_TRAIN_OR_EXCLUDE
        rows.append(
            SplitRow(
                event_id=event.event_id,
                issuer_id=event.issuer_id,
                period_end=event.period_end,
                partition=Partition.EXCLUDED if reason else window,
                reason=reason,
            )
        )
    draft = SplitManifest(
        split_policy=SPLIT_POLICY,
        split_version=version,
        windows=WINDOWS,
        pin=pin,
        rows=tuple(rows),
        content_hash="0" * 64,
    )
    return draft.model_copy(update={"content_hash": split_hash(draft)})


def load_split(path: Path) -> SplitManifest:
    """A frozen split, refused unless it hashes to its ``content_hash``."""
    manifest = parse(read_json(path), SplitManifest, path.name)
    if split_hash(manifest) != manifest.content_hash:
        raise RecordError(path.name, ("does not hash to its content_hash",))
    return manifest
```

Create `/tmp/plan9-task4-impl.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/data-dictionary.md": [
        (
            "`PilotPin`, as earnings-themes reads it: the same fields and values.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `pilot_id` | ID part | The pilot's ID |\n"
            "| `pilot_version` | int ≥ 1 | Its version |\n"
            "| `pilot_hash` | 64 lowercase hex | Its `content_hash` |\n"
            "| `events_version` | int ≥ 1 | The event manifest it selected from |\n"
            "| `events_hash` | 64 lowercase hex | That manifest's `content_hash` |\n"
            "| `universe_version` | int ≥ 1 | The universe the pilot was selected over |\n"
            "| `universe_operative_hash` | 64 lowercase hex | That universe's `operative_hash` |\n"
            "\n",
            "`PilotPin`, as earnings-themes reads it: the same fields and values.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `pilot_id` | ID part | The pilot's ID |\n"
            "| `pilot_version` | int ≥ 1 | Its version |\n"
            "| `pilot_hash` | 64 lowercase hex | Its `content_hash` |\n"
            "| `events_version` | int ≥ 1 | The event manifest it selected from |\n"
            "| `events_hash` | 64 lowercase hex | That manifest's `content_hash` |\n"
            "| `universe_version` | int ≥ 1 | The universe the pilot was selected over |\n"
            "| `universe_operative_hash` | 64 lowercase hex | That universe's `operative_hash` |\n"
            "\n"
            "### `Partition`\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `train` | Codebook discovery and training gold: calendar quarters 2024Q3 to 2025Q2 |\n"
            "| `dev` | Tuning: 2025Q3 to 2025Q4 |\n"
            "| `test` | Held out until Stage 14 freezes: 2026Q1 to 2026Q2 |\n"
            "| `excluded` | In no partition, for its `ExclusionReason` |\n"
            "\n"
            "### `ExclusionReason`\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `issuer_in_earlier_partition` | Its issuer's home partition, that of its earliest pilot event, is an earlier one |\n"
            "| `fixture_train_or_exclude` | Its release is a Stage 1 fixture outside train (GS10) |\n"
            "\n"
            "### `SplitWindow`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `partition` | `Partition` | `train`, `dev`, or `test` |\n"
            "| `first` | `YYYYQn` | Its first calendar quarter |\n"
            "| `last` | `YYYYQn` | Its last, inclusive |\n"
            "\n"
            "### `SplitEvent`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `event_id` | ID part | A pilot event |\n"
            "| `issuer_id` | ID part | Its issuer |\n"
            "| `period_end` | date | Its fiscal period's end, which places it in a quarter |\n"
            "\n"
            "### `SplitRow`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `event_id` | ID part | A pilot event |\n"
            "| `issuer_id` | ID part | Its issuer |\n"
            "| `period_end` | date | Its fiscal period's end |\n"
            "| `partition` | `Partition` | Where `issuer-time/1` puts it |\n"
            "| `reason` | `ExclusionReason` or null | Exactly for `excluded` |\n"
            "\n"
            "### `SplitManifest`\n"
            "\n"
            "`evaluation/<corpus>/pilot-v<N>/split-v<M>.json`, written once.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `schema_version` | `1` | Themes record schema version |\n"
            "| `split_policy` | `\"issuer-time/1\"` | The rule: each issuer's events go to its home partition, or are excluded |\n"
            "| `split_version` | int ≥ 1 | The split's version |\n"
            "| `windows` | tuple of `SplitWindow` | The policy's fixed windows |\n"
            "| `pin` | `Pin` | The pilot it splits |\n"
            "| `rows` | tuple of `SplitRow` | One per pilot event, sorted by `event_id` |\n"
            "| `content_hash` | 64 lowercase hex | SHA-256 of the canonical JSON of every other field |\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/split.py
python3 /tmp/plan9-extract.py /tmp/plan9-task4-impl.py && python3 /tmp/plan9-task4-impl.py
```

Expected:

```text
extracted packages/earnings-themes/src/earnings_themes/split.py: 197 lines
extracted /tmp/plan9-task4-impl.py: 104 lines
edited docs/data-dictionary.md: 1 replacement(s)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_split.py tests/contracts/test_data_dictionary.py -q`

Expected: `139 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py packages/earnings-themes/src/earnings_themes/split.py packages/earnings-themes/tests/test_split.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1601 passed, 1 skipped, 24 deselected`; `All checks passed!` and `276 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-themes/src/earnings_themes/split.py packages/earnings-themes/tests/test_split.py tests/contracts/test_data_dictionary.py
git commit -m "feat(themes): the issuer-time/1 split (GS6, GS10)"
```

---

### Task 5: The wording guard

S §Wording guard, GS3, and F20. No 40-character window of a committed string, with
full dates masked, may occur in a release's canonical text. The rule and its date
mask are `test_corpus_quotes.py`'s. `shared` returns only pairs of a string's label
and a text's ID, never the strings or the texts, so a check over pilot documents
cannot print their text (GS13).

**Files:**

- Create: `packages/earnings-themes/src/earnings_themes/wording.py`.
- Test: create `packages/earnings-themes/tests/test_wording.py`.

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: `WIDTH = 40`, `MONTH`, and `DATE`, as `test_corpus_quotes.py` has them;
  `masked(text) -> str`; `labelled_strings(value, label="") -> list[tuple[str,
  str]]`, each string leaf of parsed JSON or TOML labelled by its path, such as
  `claims[0].claim`; `markdown_paragraphs(text, label) -> list[tuple[str, str]]`;
  and `shared(strings, texts) -> set[tuple[str, str]]`, each (label, text ID) that
  shares a window.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/test_wording.py`:

```python
"""F20's rule over Stage 6's files (the Stage 6 spec, §Wording guard): 40 characters
copied from a text are caught, 39 are not, dates are facts, and a Markdown phrase
wrapped across lines is still caught."""

import pytest
from earnings_themes.wording import (
    WIDTH,
    labelled_strings,
    markdown_paragraphs,
    masked,
    shared,
)

TEXT = (
    "Net sales for the quarter ended September 30, 2025 grew in every region, "
    "led by strong demand for the company's industrial filtration products."
)


def copied(width: int) -> str:
    start = TEXT.index("led by")
    return f"The user noted [{TEXT[start : start + width]}] in passing."


@pytest.mark.parametrize(("width", "caught"), [(WIDTH, True), (WIDTH - 1, False)])
def test_the_window_is_40_characters(width: int, caught: bool) -> None:
    found = shared([("claim c1", copied(width))], [("doc-1", TEXT)])
    assert found == ({("claim c1", "doc-1")} if caught else set())


def test_a_date_is_a_fact_not_wording() -> None:
    fact = "for the quarter ended September 30, 2025 grew in every region"
    assert len(fact) > WIDTH
    assert shared([("note", fact)], [("doc-1", TEXT)]) == {("note", "doc-1")}
    assert masked("ended Sept. 30, 2025 and") == "ended \0 and"
    short = "the quarter ended September 30, 2025"
    assert len(masked(short)) < WIDTH
    assert shared([("note", short)], [("doc-1", TEXT)]) == set()


def test_only_labels_and_ids_come_back() -> None:
    found = shared([("a", copied(WIDTH)), ("b", "own words")], [("doc-1", TEXT)])
    assert found == {("a", "doc-1")}
    assert all(TEXT not in label and "led by" not in label for label, _ in found)


def test_every_string_leaf_is_labelled_by_its_path() -> None:
    data = {"claims": [{"claim_id": "c1", "claim": "x"}], "no_theme": False, "n": 1}
    assert labelled_strings(data) == [
        ("claims[0].claim_id", "c1"),
        ("claims[0].claim", "x"),
    ]


def test_a_phrase_wrapped_across_markdown_lines_is_caught() -> None:
    start = TEXT.index("led by")
    phrase = TEXT[start : start + WIDTH + 10]
    head, tail = phrase[:20].rstrip(), phrase[20:].lstrip()
    markdown = f"# Brief\n\nSome words, {head}\n{tail}, more.\n\n- another\n"
    paragraphs = markdown_paragraphs(markdown, "brief.md")
    assert [label for label, _ in paragraphs] == [
        "brief.md paragraph 1",
        "brief.md paragraph 2",
        "brief.md paragraph 3",
    ]
    assert shared(paragraphs, [("doc-1", TEXT)]) == {("brief.md paragraph 2", "doc-1")}
```

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/tests/test_wording.py
```

Expected:

```text
extracted packages/earnings-themes/tests/test_wording.py: 66 lines
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_wording.py -q`

Expected: FAIL, `1 error`, with:

```text
ModuleNotFoundError: No module named 'earnings_themes.wording'
ERROR packages/earnings-themes/tests/test_wording.py
```

- [x] **Step 3: Write the guard**

Create `packages/earnings-themes/src/earnings_themes/wording.py`:

```python
"""F20's rule for Stage 6's committed files (the Stage 6 spec, §Wording guard; GS3).

No 40-character window of a committed string, with dates masked, may occur in a
release's canonical text, also with dates masked. The rule and its date mask are
``tests/integration/test_corpus_quotes.py``'s. A Markdown file is read a paragraph
at a time, its lines joined, so a phrase copied across a wrapped line is still
caught.

``shared`` names each string by its label and each text by its ID, and returns
those pairs only, never the strings or the texts: a check over pilot documents
must never print their text (GS13).
"""

import re
from collections.abc import Iterable

WIDTH = 40
MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?"
    r"|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
DATE = re.compile(rf"\b{MONTH}\.?\s+\d{{1,2}},?\s+\d{{4}}\b")
_BLANK_LINE = re.compile(r"\n\s*\n")


def masked(text: str) -> str:
    """``text`` with each full date replaced by a NUL, which no release holds."""
    return DATE.sub("\0", text)


def labelled_strings(value: object, label: str = "") -> list[tuple[str, str]]:
    """Every string leaf of parsed JSON or TOML, with its path as its label."""
    if isinstance(value, str):
        return [(label or "value", value)]
    if isinstance(value, dict):
        return [
            pair
            for key, item in value.items()
            for pair in labelled_strings(item, f"{label}.{key}" if label else key)
        ]
    if isinstance(value, list | tuple):
        return [
            pair
            for index, item in enumerate(value)
            for pair in labelled_strings(item, f"{label}[{index}]")
        ]
    return []


def markdown_paragraphs(text: str, label: str) -> list[tuple[str, str]]:
    """Each paragraph of a Markdown file, its lines stripped and joined by a space."""
    paragraphs = []
    for number, block in enumerate(_BLANK_LINE.split(text), start=1):
        joined = " ".join(line.strip() for line in block.splitlines() if line.strip())
        if joined:
            paragraphs.append((f"{label} paragraph {number}", joined))
    return paragraphs


def shared(
    strings: Iterable[tuple[str, str]], texts: Iterable[tuple[str, str]]
) -> set[tuple[str, str]]:
    """Each ``(label, text_id)`` where a window of the labelled string occurs in the
    text, both with dates masked."""
    windows: dict[str, set[str]] = {}
    for label, string in strings:
        text = masked(string)
        for start in range(len(text) - WIDTH + 1):
            windows.setdefault(text[start : start + WIDTH], set()).add(label)
    found: set[tuple[str, str]] = set()
    if not windows:
        return found
    for text_id, text in texts:
        text = masked(text)
        for start in range(len(text) - WIDTH + 1):
            labels = windows.get(text[start : start + WIDTH])
            if labels:
                found.update((label, text_id) for label in labels)
    return found
```

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/wording.py
```

Expected:

```text
extracted packages/earnings-themes/src/earnings_themes/wording.py: 79 lines
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_wording.py -q`

Expected: `6 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py packages/earnings-themes/src/earnings_themes/wording.py packages/earnings-themes/tests/test_wording.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1607 passed, 1 skipped, 24 deselected`; `All checks passed!` and `278 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-themes/src/earnings_themes/wording.py packages/earnings-themes/tests/test_wording.py
git commit -m "feat(themes): F20's wording guard for Stage 6's committed files (GS3)"
```

---

### Task 6: The anchor

S §Anchoring and validation, GS11, GS15, and P9-12, P9-14, P9-19. A drafted quote is
named by its text, with context when it repeats. The anchor finds it exactly once,
attributes it to the most specific narrative element that holds it, builds the span
through `parse_span_candidate`, and checks it with `validate_span`, or refuses it by
reason. `check_pointer` rechecks a committed pointer against the local document.
`synthetic.py` holds the tests' invented document and drafts, as ingestion's
`events/fixture.py` holds its builders, since tests cannot import one another under
`--import-mode=importlib`; its `codebook_draft`, `gold_draft`, and `curated_draft`
serve Tasks 7, 8, and 12.

**Files:**

- Create: `packages/earnings-themes/src/earnings_themes/anchoring.py` and
  `synthetic.py`.
- Test: create `packages/earnings-themes/tests/conftest.py` and `test_anchoring.py`.
- Modify, by exact replacement: `tests/contracts/test_data_dictionary.py` and
  `docs/data-dictionary.md`.

**Interfaces:**

- Consumes: `earnings_core`'s `CanonicalDocument`, `DocumentElement`, `ElementType`,
  `OverlayMask`, `Rejection`, `RejectionReason`, `SpanLocator`, `TextSpan`,
  `VerifiedSpan`, `make_locator`, `occurrences`, `parse_span_candidate`,
  `sha256_hex`, `validate_elements`, and `validate_span`; Task 3's `Problem`,
  `Part`, `NonBlank`, `Sha256Hex`, and `Pin`; Task 4's `split_events`.
- Produces:
  - `NARRATIVE`, the narrative element types, most specific first;
    `Bundle(name, document, elements, masks)`;
  - `SpanPointer(start, end, element_id, quote_sha256, context_sha256=None,
    mask_ids=())`; `mask_id(mask) -> str`, `quote_hash(text) -> str`, and
    `context_hash(prefix, suffix) -> str`;
  - `bundle_problems(bundle) -> list[str]`; `anchor(bundle, exact, prefix="",
    suffix="") -> SpanPointer | str`, the string being a refusal reason; and
    `check_pointer(bundle, pointer) -> list[str]`;
  - in `synthetic.py`: `LINES`, `TEXT`, `Synthetic(bundle, spans)`,
    `build_synthetic(name=...) -> Synthetic`, `PIN`, `TRAIN`, `DEV`, `TEST`,
    `LATER`, `AID`, `synthetic_split() -> SplitManifest`,
    `codebook_draft(**changes) -> dict`, `gold_draft(event_id=TRAIN, **changes) ->
    dict`, and `curated_draft(bundles, annotator="") -> dict`;
  - in `conftest.py`: the fixtures `synthetic`, and `fixtures`, Stage 1's eight
    canonical fixtures as bundles.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/conftest.py`:

```python
"""Shared inputs for earnings-themes' tests: Stage 1's committed canonical fixtures,
read through earnings-core's contracts, and the synthetic document. Tests hold only
synthetic text and Stage 1's fixtures (GS13)."""

import json
from pathlib import Path

import pytest
from earnings_core import CanonicalDocument, DocumentElement, OverlayMask
from earnings_themes.anchoring import Bundle
from earnings_themes.synthetic import Synthetic, build_synthetic

REPO = Path(__file__).resolve().parents[3]
CANONICAL = REPO / "tests" / "fixtures" / "canonical"
FIXTURE_IDS = sorted(path.stem for path in CANONICAL.glob("*.json"))


def fixture_bundle(fixture_id: str) -> Bundle:
    """A Stage 1 canonical fixture, read record by record through the contracts."""
    data = json.loads((CANONICAL / f"{fixture_id}.json").read_text(encoding="utf-8"))

    def read(model, record):
        return model.model_validate_json(json.dumps(record))

    return Bundle(
        name=fixture_id,
        document=read(CanonicalDocument, data["document"]),
        elements=tuple(read(DocumentElement, r) for r in data["elements"]),
        masks=tuple(read(OverlayMask, r) for r in data["masks"]),
    )


@pytest.fixture
def synthetic() -> Synthetic:
    return build_synthetic()


@pytest.fixture(scope="session")
def fixtures() -> dict[str, Bundle]:
    return {fixture_id: fixture_bundle(fixture_id) for fixture_id in FIXTURE_IDS}
```

Create `packages/earnings-themes/tests/test_anchoring.py`:

```python
"""The anchor and the pointer check (the Stage 6 spec, §Anchoring and validation):
a quote occurs once, sits in narrative, passes Stage 2's checks, and is committed as
offsets and hashes that the local document reproduces."""

import pytest
from earnings_core import RejectionReason, TextSpan, make_locator
from earnings_themes.anchoring import (
    SpanPointer,
    anchor,
    bundle_problems,
    check_pointer,
    context_hash,
    mask_id,
    quote_hash,
)
from earnings_themes.problems import Problem


def test_a_unique_sentence_is_anchored_to_its_sentence(synthetic) -> None:
    pointer = anchor(synthetic.bundle, "Margins held steady.")
    assert isinstance(pointer, SpanPointer)
    span = synthetic.spans["sentence 2"]
    assert (pointer.start, pointer.end) == (span.start, span.end)
    assert pointer.element_id == f"sentence-{span.start}-{span.end}"
    assert pointer.quote_sha256 == quote_hash("Margins held steady.")
    assert pointer.context_sha256 is None
    assert pointer.mask_ids == ()
    assert check_pointer(synthetic.bundle, pointer) == []


def test_repeated_text_needs_context_and_records_its_hash(synthetic) -> None:
    repeated = synthetic.text("repeat")
    assert anchor(synthetic.bundle, repeated) == "ambiguous_occurrence"
    pointer = anchor(synthetic.bundle, repeated, prefix="steady.\n")
    assert isinstance(pointer, SpanPointer)
    assert pointer.start == synthetic.spans["repeat"].start
    locator = make_locator(
        synthetic.bundle.document, TextSpan(start=pointer.start, end=pointer.end)
    )
    assert locator.prefix or locator.suffix
    assert pointer.context_sha256 == context_hash(locator.prefix, locator.suffix)
    assert check_pointer(synthetic.bundle, pointer) == []


def test_text_that_is_not_there_is_not_found(synthetic) -> None:
    assert anchor(synthetic.bundle, "Revenue fell.") == "locator_not_found"
    assert anchor(synthetic.bundle, "") == "malformed"


@pytest.mark.parametrize(
    ("name", "reason"),
    [
        ("cell 1", Problem.NOT_NARRATIVE),
        ("table", Problem.NOT_NARRATIVE),
        ("artifact", Problem.NOT_NARRATIVE),
        ("scanned", RejectionReason.OCR_DERIVED_TEXT),
    ],
)
def test_a_quote_outside_native_narrative_is_refused(synthetic, name, reason) -> None:
    assert anchor(synthetic.bundle, synthetic.text(name)) == reason.value


def test_a_quote_across_two_elements_is_outside_every_element(synthetic) -> None:
    across = synthetic.bundle.document.canonical_text[
        synthetic.spans["heading"].start : synthetic.spans["sentence 1"].end
    ]
    assert anchor(synthetic.bundle, across) == "outside_element"


def test_a_masked_quote_is_allowed_and_its_masks_are_recorded(synthetic) -> None:
    pointer = anchor(synthetic.bundle, synthetic.text("harbor"))
    assert isinstance(pointer, SpanPointer)
    (mask,) = synthetic.bundle.masks
    assert pointer.mask_ids == (mask_id(mask),)
    assert mask_id(mask) == f"safe_harbor-{mask.span.start}-{mask.span.end}"


@pytest.mark.parametrize(
    ("change", "reasons"),
    [
        ({"start": 1}, ["quote_hash_mismatch", "outside_element"]),
        ({"quote_sha256": "0" * 64}, ["quote_hash_mismatch"]),
        ({"context_sha256": "0" * 64}, ["context_hash_mismatch"]),
        ({"mask_ids": ("safe_harbor-0-1",)}, ["masks_mismatch"]),
        ({"element_id": "paragraph-0-1"}, ["unknown_element"]),
        ({"end": 10_000}, ["span_out_of_bounds"]),
    ],
)
def test_a_tampered_pointer_is_refused(synthetic, change, reasons) -> None:
    pointer = anchor(synthetic.bundle, "Margins held steady.")
    assert isinstance(pointer, SpanPointer)
    tampered = SpanPointer(**{**pointer.model_dump(), **change})
    assert check_pointer(synthetic.bundle, tampered) == reasons


def test_a_pointer_into_a_table_cell_is_not_narrative(synthetic) -> None:
    span = synthetic.spans["cell 1"]
    pointer = SpanPointer(
        start=span.start,
        end=span.end,
        element_id=f"table_cell-{span.start}-{span.end}",
        quote_sha256=quote_hash(synthetic.text("cell 1")),
    )
    assert check_pointer(synthetic.bundle, pointer) == ["not_narrative"]


def test_the_synthetic_bundle_is_sound(synthetic) -> None:
    assert bundle_problems(synthetic.bundle) == []


def test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors(
    fixtures,
) -> None:
    anchored = 0
    for bundle in fixtures.values():
        assert bundle_problems(bundle) == []
        text = bundle.document.canonical_text
        for element in bundle.elements:
            if element.type.value != "sentence":
                continue
            exact = text[element.span.start : element.span.end]
            pointer = anchor(bundle, exact)
            if isinstance(pointer, str):
                assert pointer in {"ambiguous_occurrence", "not_narrative"}
                continue
            assert pointer.element_id == element.element_id
            assert check_pointer(bundle, pointer) == []
            anchored += 1
    assert anchored > 500
```

Create `/tmp/plan9-task6-tests.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "tests/contracts/test_data_dictionary.py": [
        (
            "from earnings_themes import records as themes\n"
            "from pydantic import BaseModel\n",
            "from earnings_themes import records as themes\n"
            "from earnings_themes.anchoring import SpanPointer\n"
            "from pydantic import BaseModel\n",
        ),
        (
            "    split.SplitManifest,\n"
            "]\n",
            "    split.SplitManifest,\n"
            "    SpanPointer,\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/tests/conftest.py
python3 /tmp/plan9-extract.py packages/earnings-themes/tests/test_anchoring.py
python3 /tmp/plan9-extract.py /tmp/plan9-task6-tests.py && python3 /tmp/plan9-task6-tests.py
```

Expected:

```text
extracted packages/earnings-themes/tests/conftest.py: 40 lines
extracted packages/earnings-themes/tests/test_anchoring.py: 129 lines
extracted /tmp/plan9-task6-tests.py: 36 lines
edited tests/contracts/test_data_dictionary.py: 2 replacement(s)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_anchoring.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL before any test runs, since `conftest.py` imports what this task writes:

```text
ModuleNotFoundError: No module named 'earnings_themes.anchoring'
```

- [x] **Step 3: Write the anchor and the synthetic inputs**

> Deviation: by the user's choice of 2026-09-28, `check_pointer` also refuses a pointer whose narrative element holds the span but is not the most specific one (P9-19), as `Problem.ELEMENT_MISMATCH` with its dictionary row, its test folded into `test_a_pointer_into_a_table_cell_is_not_narrative` (`1b40799`).

Create `packages/earnings-themes/src/earnings_themes/anchoring.py`:

```python
"""Exact spans for Stage 6's quotes and codebook examples (the Stage 6 spec,
§Anchoring and validation; GS11, GS15).

- **The anchor.** A draft names a quote by its text, with the words around it when
  the text repeats. The text must occur exactly once with that context. Its span is
  attributed to the most specific narrative element that holds it, and the span is
  then built through ``parse_span_candidate`` and checked by ``validate_span``: code
  is the authority on exactness, and no offset comes from a browser.
- **Narrative only.** A quote never overlaps a ``table``, ``table_cell``,
  ``page_artifact``, or ``other`` element (R4.2, GS15). A quote under a boilerplate
  mask is allowed, and its masks are recorded.
- **The committed pointer.** Offsets, the element, and hashes, never text: the
  quote's SHA-256, and, when the text repeats, the SHA-256 of ``make_locator``'s
  prefix and suffix (GS3). The check recomputes each from the local document.

Every refusal is a reason, never a detail: ``Rejection.detail`` may quote the text.
"""

import json
from dataclasses import dataclass
from typing import Self

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    OverlayMask,
    Rejection,
    RejectionReason,
    SpanLocator,
    TextSpan,
    VerifiedSpan,
    make_locator,
    occurrences,
    parse_span_candidate,
    sha256_hex,
    validate_elements,
    validate_span,
)
from pydantic import NonNegativeInt, model_validator

from earnings_themes.problems import Problem
from earnings_themes.records import NonBlank, Part, Sha256Hex

NARRATIVE = (
    ElementType.SENTENCE,
    ElementType.LIST_ITEM,
    ElementType.FOOTNOTE,
    ElementType.HEADING,
    ElementType.PARAGRAPH,
    ElementType.SPEAKER_TURN,
    ElementType.SECTION,
)
"""The elements a quote may sit in, most specific first (R4.2, GS15)."""


@dataclass(frozen=True)
class Bundle:
    """One document to annotate: a pilot event's release, or a Stage 1 fixture."""

    name: str
    document: CanonicalDocument
    elements: tuple[DocumentElement, ...]
    masks: tuple[OverlayMask, ...]


class SpanPointer(Part):
    """Where a quote is, and hashes that recheck it, without its text."""

    start: NonNegativeInt
    end: NonNegativeInt
    element_id: NonBlank
    quote_sha256: Sha256Hex
    context_sha256: Sha256Hex | None = None
    mask_ids: tuple[NonBlank, ...] = ()

    @model_validator(mode="after")
    def _start_before_end(self) -> Self:
        if self.start >= self.end:
            raise ValueError(f"span [{self.start}, {self.end}) is empty or reversed")
        return self


def mask_id(mask: OverlayMask) -> str:
    """A mask's ID, derived as an element's is: its category and span."""
    return f"{mask.category.value}-{mask.span.start}-{mask.span.end}"


def quote_hash(text: str) -> str:
    """The SHA-256 of a quote's UTF-8 text."""
    return sha256_hex(text.encode("utf-8"))


def context_hash(prefix: str, suffix: str) -> str:
    """The SHA-256 of a locator's prefix and suffix, as a two-item JSON array."""
    pair = json.dumps([prefix, suffix], ensure_ascii=False, separators=(",", ":"))
    return sha256_hex(pair.encode("utf-8"))


def bundle_problems(bundle: Bundle) -> list[str]:
    """Why a bundle's elements or masks cannot anchor anything, once per reason."""
    reasons = [
        r.reason.value for r in validate_elements(bundle.document, bundle.elements)
    ]
    document = bundle.document
    for mask in bundle.masks:
        if (mask.doc_id, mask.canonical_hash) != (
            document.doc_id,
            document.canonical_hash,
        ) or mask.span.end > len(document.canonical_text):
            reasons.append(RejectionReason.WRONG_DOCUMENT.value)
    return list(dict.fromkeys(reasons))


def _genuine(bundle: Bundle) -> list[DocumentElement]:
    return [e for e in bundle.elements if e.doc_id == bundle.document.doc_id]


def _outside_narrative(elements: list[DocumentElement], span: TextSpan) -> bool:
    return any(e.type not in NARRATIVE and e.span.overlaps(span) for e in elements)


def _home(bundle: Bundle, span: TextSpan) -> DocumentElement | str:
    elements = _genuine(bundle)
    if _outside_narrative(elements, span):
        return Problem.NOT_NARRATIVE.value
    holding = [e for e in elements if e.type in NARRATIVE and e.span.contains(span)]
    if not holding:
        return RejectionReason.OUTSIDE_ELEMENT.value
    return min(holding, key=lambda e: (e.span.length, NARRATIVE.index(e.type)))


def _verify(
    bundle: Bundle, span: TextSpan, element_id: str, locator: SpanLocator
) -> VerifiedSpan | Rejection:
    document = bundle.document
    candidate = parse_span_candidate(
        {
            "doc_id": document.doc_id,
            "canonical_hash": document.canonical_hash,
            "start": span.start,
            "end": span.end,
            "quote_text": document.canonical_text[span.start : span.end],
            "element_id": element_id,
            "prefix": locator.prefix,
            "suffix": locator.suffix,
        }
    )
    if isinstance(candidate, Rejection):
        return candidate
    return validate_span(document, bundle.elements, candidate)


def _masks_over(bundle: Bundle, span: TextSpan) -> tuple[str, ...]:
    return tuple(sorted(mask_id(m) for m in bundle.masks if m.span.overlaps(span)))


def _context(locator: SpanLocator) -> str | None:
    if not locator.prefix and not locator.suffix:
        return None
    return context_hash(locator.prefix, locator.suffix)


def anchor(
    bundle: Bundle, exact: str, prefix: str = "", suffix: str = ""
) -> SpanPointer | str:
    """The pointer for the one occurrence of ``exact`` with this context, or why not."""
    if not exact:
        return Problem.MALFORMED.value
    text = bundle.document.canonical_text
    starts = occurrences(text, SpanLocator(exact=exact, prefix=prefix, suffix=suffix))
    if not starts:
        return RejectionReason.LOCATOR_NOT_FOUND.value
    if len(starts) > 1:
        return RejectionReason.AMBIGUOUS_OCCURRENCE.value
    span = TextSpan(start=starts[0], end=starts[0] + len(exact))
    home = _home(bundle, span)
    if isinstance(home, str):
        return home
    locator = make_locator(bundle.document, span)
    verdict = _verify(bundle, span, home.element_id, locator)
    if isinstance(verdict, Rejection):
        return verdict.reason.value
    return SpanPointer(
        start=span.start,
        end=span.end,
        element_id=home.element_id,
        quote_sha256=quote_hash(verdict.quote_text),
        context_sha256=_context(locator),
        mask_ids=_masks_over(bundle, span),
    )


def check_pointer(bundle: Bundle, pointer: SpanPointer) -> list[str]:
    """Why a committed pointer does not hold in its local document; empty when it
    does. Each hash and mask is recomputed, and the span checked again."""
    text = bundle.document.canonical_text
    if pointer.end > len(text):
        return [RejectionReason.SPAN_OUT_OF_BOUNDS.value]
    span = TextSpan(start=pointer.start, end=pointer.end)
    reasons = []
    if quote_hash(text[span.start : span.end]) != pointer.quote_sha256:
        reasons.append(Problem.QUOTE_HASH_MISMATCH.value)
    locator = make_locator(bundle.document, span)
    if pointer.context_sha256 != _context(locator):
        reasons.append(Problem.CONTEXT_HASH_MISMATCH.value)
    elements = _genuine(bundle)
    named = [e for e in elements if e.element_id == pointer.element_id]
    if any(e.type not in NARRATIVE for e in named) or _outside_narrative(
        elements, span
    ):
        reasons.append(Problem.NOT_NARRATIVE.value)
    verdict = _verify(bundle, span, pointer.element_id, locator)
    if isinstance(verdict, Rejection):
        reasons.append(verdict.reason.value)
    if pointer.mask_ids != _masks_over(bundle, span):
        reasons.append(Problem.MASKS_MISMATCH.value)
    return list(dict.fromkeys(reasons))
```

Create `packages/earnings-themes/src/earnings_themes/synthetic.py`:

```python
"""Synthetic inputs for Stage 6's tests: a small canonical document, a pin, a
split, and drafts. Every word here is invented, and none comes from a release
(GS13); ingestion's ``events/fixture.py`` is the precedent for keeping them here.
``curated_draft`` takes its quotes from the Stage 1 fixtures it is given, when it
runs, so no fixture's wording is typed here either.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    MaskCategory,
    OverlayMask,
    TableCellContext,
    TextOrigin,
    TextSpan,
)

from earnings_themes.anchoring import Bundle
from earnings_themes.records import Pin
from earnings_themes.split import SplitEvent, SplitManifest, split_events

LINES = {
    "heading": "Quarterly results",
    "paragraph": "Revenue grew in every region. Margins held steady.",
    "repeat": "Revenue grew in every region.",
    "table": "Region Sales",
    "artifact": "Page 2 of 9",
    "scanned": "Scanned text from an image.",
    "harbor": "Safe harbor: results may differ.",
}
TEXT = "\n".join(LINES.values()) + "\n"


@dataclass(frozen=True)
class Synthetic:
    bundle: Bundle
    spans: dict[str, TextSpan]

    def text(self, name: str) -> str:
        span = self.spans[name]
        return TEXT[span.start : span.end]


def build_synthetic(name: str = "cik-0009990001:2025-03-31") -> Synthetic:
    document = CanonicalDocument.create(
        source_document_id="0009990001-25-000001_ex991.htm",
        canonicalization_version="walker-1",
        canonical_text=TEXT,
    )
    spans = {}
    position = 0
    for key, line in LINES.items():
        spans[key] = TextSpan(start=position, end=position + len(line))
        position += len(line) + 1
    first = TEXT.index(". ") + 1
    spans["sentence 1"] = TextSpan(start=spans["paragraph"].start, end=first)
    spans["sentence 2"] = TextSpan(start=first + 1, end=spans["paragraph"].end)
    spans["cell 1"] = TextSpan(start=spans["table"].start, end=spans["table"].start + 6)
    spans["cell 2"] = TextSpan(start=spans["table"].start + 7, end=spans["table"].end)

    def element(kind, key, **options):
        return DocumentElement.create(document, kind, spans[key], **options)

    paragraph = element(ElementType.PARAGRAPH, "paragraph")
    table = element(ElementType.TABLE, "table")
    elements = (
        element(ElementType.HEADING, "heading", level=1),
        paragraph,
        element(ElementType.SENTENCE, "sentence 1", parent_id=paragraph.element_id),
        element(ElementType.SENTENCE, "sentence 2", parent_id=paragraph.element_id),
        element(ElementType.PARAGRAPH, "repeat"),
        table,
        *(
            element(
                ElementType.TABLE_CELL,
                key,
                parent_id=table.element_id,
                table_cell=TableCellContext(row=0, column=column, is_header=False),
            )
            for column, key in enumerate(["cell 1", "cell 2"])
        ),
        element(ElementType.PAGE_ARTIFACT, "artifact"),
        element(ElementType.PARAGRAPH, "scanned", text_origin=TextOrigin.OCR),
        element(ElementType.PARAGRAPH, "harbor"),
    )
    masks = (
        OverlayMask(
            doc_id=document.doc_id,
            canonical_hash=document.canonical_hash,
            span=spans["harbor"],
            category=MaskCategory.SAFE_HARBOR,
            policy_id="boilerplate",
            policy_version="1",
        ),
    )
    return Synthetic(Bundle(name, document, elements, masks), spans)


PIN = Pin(
    pilot_id="synthetic-pilot",
    pilot_version=1,
    pilot_hash="1" * 64,
    events_version=1,
    events_hash="2" * 64,
    universe_version=1,
    universe_operative_hash="3" * 64,
)
TRAIN = "cik-0009990001:2025-03-31"
DEV = "cik-0009990002:2025-09-30"
TEST = "cik-0009990003:2026-03-31"
LATER = "cik-0009990001:2026-03-31"
AID = {"model_id": "claude-opus-5-5", "drafted_on": date(2026, 10, 1)}


def synthetic_split() -> SplitManifest:
    events = [
        SplitEvent(
            event_id=event_id,
            issuer_id=event_id.split(":")[0],
            period_end=date.fromisoformat(event_id.split(":")[1]),
        )
        for event_id in (TRAIN, DEV, TEST, LATER)
    ]
    return split_events(events, PIN)


def codebook_draft(**changes) -> dict:
    theme = {
        "theme_id": "demand",
        "label": "Demand",
        "definition": "The user's definition of demand as a theme.",
        "inclusion_rules": ["Statements about customer demand."],
        "exclusion_rules": ["Pricing alone."],
        "sector_applicability": "all",
        "positive_examples": [
            {"event_id": TRAIN, "text": "Revenue grew in every region.", "prefix": ""}
        ],
        "hard_negatives": [
            {"synthetic": True, "text": "A synthetic sentence about prices only."}
        ],
    }
    draft = {
        "codebook_id": "djia-pilot",
        "codebook_version": 0,
        "drafting_aid": AID,
        "rules": {
            "multi_label": "A claim may take several themes.",
            "boilerplate": "Masked text may be quoted; its masks are recorded.",
        },
        "themes": [theme],
    }
    draft["themes"][0]["positive_examples"][0]["suffix"] = " Margins"
    draft.update(changes)
    return draft


def gold_draft(event_id: str = TRAIN, **changes) -> dict:
    """A gold draft over ``build_synthetic(event_id)``, coded against
    ``codebook_draft``'s one theme."""
    draft = {
        "event_id": event_id,
        "annotator": "",
        "drafting_aid": AID,
        "no_theme": False,
        "release_identification": {
            "label": "release",
            "note": "The issuer's results for its quarter.",
        },
        "quotes": [
            {"quote_id": "q1", "text": "Margins held steady."},
            {
                "quote_id": "q2",
                "text": "Revenue grew in every region.",
                "suffix": " Margins",
            },
            {"quote_id": "q3", "text": "Safe harbor: results may differ."},
        ],
        "claims": [
            {"claim_id": "c1", "quote_ids": ["q2"], "claim": "Demand rose widely."},
            {"claim_id": "c2", "quote_ids": ["q1"], "claim": "Profitability held."},
        ],
        "assignments": [
            {"claim_id": "c1", "theme_id": "demand", "support": "supports"},
            {"claim_id": "c2", "theme_id": "unmatched", "support": "uncertain"},
        ],
        "hard_negatives": [
            {
                "claim_id": "n1",
                "quote_ids": ["q3"],
                "claim": "Legal boilerplate is no evidence of demand.",
                "negative_kind": "section",
                "theme_id": "demand",
            }
        ],
    }
    draft.update(changes)
    return draft


def curated_draft(bundles: Mapping[str, Bundle], annotator: str = "") -> dict:
    """Curated hard negatives over the first two of ``bundles``, one of each kind:
    each quote is a narrative sentence that occurs once in its fixture."""
    documents = []
    kinds = iter(["period", "issuer", "section"])
    for fixture_id in sorted(bundles)[:2]:
        bundle = bundles[fixture_id]
        text = bundle.document.canonical_text
        quotes = []
        for element in bundle.elements:
            exact = text[element.span.start : element.span.end]
            if element.type.value == "sentence" and text.count(exact) == 1:
                quotes.append({"quote_id": f"q{len(quotes) + 1}", "text": exact})
            if len(quotes) == 2:
                break
        negatives = [
            {
                "claim_id": f"n{index}",
                "quote_ids": [quote["quote_id"]],
                "claim": "The user's claim that this quote does not support.",
                "negative_kind": next(kinds, "period"),
                "theme_id": "demand",
            }
            for index, quote in enumerate(quotes, start=1)
        ]
        documents.append(
            {"fixture_id": fixture_id, "quotes": quotes, "hard_negatives": negatives}
        )
    return {"annotator": annotator, "drafting_aid": AID, "documents": documents}
```

Create `/tmp/plan9-task6-impl.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/data-dictionary.md": [
        (
            "| `rows` | tuple of `SplitRow` | One per pilot event, sorted by `event_id` |\n"
            "| `content_hash` | 64 lowercase hex | SHA-256 of the canonical JSON of every other field |\n"
            "\n",
            "| `rows` | tuple of `SplitRow` | One per pilot event, sorted by `event_id` |\n"
            "| `content_hash` | 64 lowercase hex | SHA-256 of the canonical JSON of every other field |\n"
            "\n"
            "### `SpanPointer`\n"
            "\n"
            "A quote, by position: the committed form of evidence.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `start` | int ≥ 0 | Half-open start in the canonical text |\n"
            "| `end` | int > `start` | Half-open end |\n"
            "| `element_id` | string | The most specific narrative element that contains it |\n"
            "| `quote_sha256` | 64 lowercase hex | SHA-256 of the slice's UTF-8 bytes |\n"
            "| `context_sha256` | 64 lowercase hex or null | When the text repeats: SHA-256 of `make_locator`'s prefix and suffix, as a compact JSON pair |\n"
            "| `mask_ids` | tuple of string | The boilerplate masks over it, each `<category>-<start>-<end>` |\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/anchoring.py
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/synthetic.py
python3 /tmp/plan9-extract.py /tmp/plan9-task6-impl.py && python3 /tmp/plan9-task6-impl.py
```

Expected:

```text
extracted packages/earnings-themes/src/earnings_themes/anchoring.py: 218 lines
extracted packages/earnings-themes/src/earnings_themes/synthetic.py: 233 lines
extracted /tmp/plan9-task6-impl.py: 43 lines
edited docs/data-dictionary.md: 1 replacement(s)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_anchoring.py tests/contracts/test_data_dictionary.py -q`

Expected: `141 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py packages/earnings-themes/src/earnings_themes/anchoring.py packages/earnings-themes/src/earnings_themes/synthetic.py packages/earnings-themes/tests/conftest.py packages/earnings-themes/tests/test_anchoring.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1626 passed, 1 skipped, 24 deselected`; `All checks passed!` and `282 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-themes/src/earnings_themes/anchoring.py packages/earnings-themes/src/earnings_themes/synthetic.py packages/earnings-themes/tests/conftest.py packages/earnings-themes/tests/test_anchoring.py tests/contracts/test_data_dictionary.py
git commit -m "feat(themes): anchor a drafted quote to an exact narrative span (GS11, GS15)"
```

---

### Task 7: The codebook

S §The codebook, GS9, GS16, and P9-13, P9-16. A draft names its examples by text;
`freeze_codebook` anchors each in a training bundle, checks every field, the theme
structure, and the wording guard, and returns the frozen version or every refusal.
The content hash leaves out `status` and `approval`, so ADR 0003 can cite it before
the approval exists.

**Files:**

- Create: `packages/earnings-themes/src/earnings_themes/codebook.py`.
- Test: create `packages/earnings-themes/tests/test_codebook.py`.
- Modify, by exact replacement: `tests/contracts/test_data_dictionary.py` and
  `docs/data-dictionary.md`.

**Interfaces:**

- Consumes: Tasks 3 to 6: `tomlfile`, `parse`, `digest`, `Pin`, `Refusal`,
  `Problem`, `SplitManifest`, `Partition`, `labelled_strings`, `shared`, `Bundle`,
  `SpanPointer`, `anchor`, and `check_pointer`.
- Produces: `CODEBOOK_ID = "djia-pilot"`, `CODEBOOK_VERSION = 0`, and
  `UNMATCHED = "unmatched"`; `CodebookStatus`; `ExamplePointer`, `Example`, `Theme`,
  `DiscoveryCorpus`, `CodebookRules`, `Approval(approver, approved_on, adr)`,
  `DraftingAid(model_id, drafted_on)`, and `Codebook` with `theme_ids() ->
  frozenset[str]`; the drafts `ExampleDraft`, `ThemeDraft`, and `CodebookDraft`;
  `codebook_hash(codebook) -> str`; `freeze_codebook(draft, *, pin, split, bundles,
  approval=None) -> Codebook | list[Refusal]`; `validate_codebook(codebook, *, pin,
  split, bundles, adr_text) -> list[Refusal]`; `codebook_toml(codebook) -> str`; and
  `load_codebook(path)` and `load_codebook_draft(path)`.

- [x] **Step 1: Write the failing tests**

> Deviation: by the user's choice, `test_a_tampered_version_is_refused` also reaches the `wrong_document` and `discovery_corpus` refusals (`365738e`); counts unchanged.

Create `packages/earnings-themes/tests/test_codebook.py`:

```python
"""The codebook contract and its freeze (the Stage 6 spec, §The codebook): R9.2's
fields, examples only from training bundles or flagged synthetic, a content hash
that ADR 0003 can cite before approval, and one refusal per problem."""

from datetime import date

import pytest
from earnings_themes.codebook import (
    Approval,
    Codebook,
    CodebookDraft,
    CodebookStatus,
    codebook_hash,
    codebook_toml,
    freeze_codebook,
    load_codebook,
    validate_codebook,
)
from earnings_themes.problems import Refusal
from earnings_themes.records import RecordError, parse
from earnings_themes.synthetic import (
    DEV,
    PIN,
    TEST,
    TRAIN,
    build_synthetic,
    codebook_draft,
    synthetic_split,
)

APPROVAL = Approval(
    approver="Lowell Mason",
    approved_on=date(2026, 10, 2),
    adr="docs/adr/0003-approve-pilot-codebook-v0.md",
)


@pytest.fixture
def bundles():
    return {e: build_synthetic(e).bundle for e in (TRAIN, DEV, TEST)}


def freeze(draft: dict, bundles, approval=None):
    return freeze_codebook(
        parse(draft, CodebookDraft, "draft"),
        pin=PIN,
        split=synthetic_split(),
        bundles=bundles,
        approval=approval,
    )


def test_a_draft_freezes_with_its_examples_anchored(bundles) -> None:
    codebook = freeze(codebook_draft(), bundles)
    assert isinstance(codebook, Codebook)
    assert codebook.status is CodebookStatus.DRAFT
    assert codebook.approval is None
    corpus = codebook.discovery_corpus
    assert corpus.event_ids == (TRAIN,)
    assert corpus.doc_ids == (bundles[TRAIN].document.doc_id,)
    assert corpus.split_hash == synthetic_split().content_hash
    (theme,) = codebook.themes
    (positive,) = theme.positive_examples
    assert positive.pointer is not None
    assert positive.pointer.event_id == TRAIN
    assert positive.pointer.context_sha256 is not None
    (negative,) = theme.hard_negatives
    assert negative.synthetic
    assert codebook.content_hash == codebook_hash(codebook)


def test_approval_leaves_the_content_hash_unchanged(bundles) -> None:
    draft = freeze(codebook_draft(), bundles)
    approved = freeze(codebook_draft(), bundles, APPROVAL)
    assert isinstance(draft, Codebook)
    assert isinstance(approved, Codebook)
    assert approved.status is CodebookStatus.APPROVED
    assert approved.content_hash == draft.content_hash


def test_the_committed_file_round_trips_and_holds_no_quote(bundles, tmp_path) -> None:
    codebook = freeze(codebook_draft(), bundles, APPROVAL)
    assert isinstance(codebook, Codebook)
    path = tmp_path / "codebook-v0.toml"
    path.write_text(codebook_toml(codebook), encoding="utf-8")
    assert load_codebook(path) == codebook
    assert "Revenue grew" not in path.read_text(encoding="utf-8")


def example(**fields) -> dict:
    return codebook_draft(
        themes=[
            {
                **codebook_draft()["themes"][0],
                "positive_examples": [fields],
            }
        ]
    )


@pytest.mark.parametrize(
    ("fields", "reason"),
    [
        ({"event_id": DEV, "text": "Margins held steady."}, "outside_training"),
        ({"event_id": TEST, "text": "Margins held steady."}, "outside_training"),
        ({"text": "Margins held steady."}, "synthetic_unflagged"),
        (
            {"event_id": TRAIN, "text": "Revenue grew in every region."},
            "ambiguous_occurrence",
        ),
        ({"event_id": TRAIN, "text": "Region Sales"}, "not_narrative"),
        ({"event_id": TRAIN, "text": "Nothing like this."}, "locator_not_found"),
        (
            {"synthetic": True, "event_id": TRAIN, "text": "Margins held steady."},
            "malformed",
        ),
    ],
)
def test_an_example_that_cannot_stand_is_refused(bundles, fields, reason) -> None:
    assert freeze(example(**fields), bundles) == [
        Refusal("theme demand.positive_examples[0]", reason)
    ]


def test_theme_structure_is_checked(bundles) -> None:
    base = codebook_draft()["themes"][0]
    themes = [
        {**base, "theme_id": "a", "parent_id": "b"},
        {**base, "theme_id": "b", "parent_id": "a"},
        {**base, "theme_id": "c", "parent_id": "missing"},
        {**base, "theme_id": "c"},
    ]
    assert freeze(codebook_draft(themes=themes), bundles) == [
        Refusal("theme c", "duplicate_id"),
        Refusal("theme c", "unknown_theme"),
        Refusal("theme a", "parent_cycle"),
        Refusal("theme b", "parent_cycle"),
    ]


def test_wording_copied_from_a_training_bundle_is_refused(bundles) -> None:
    copied = "The user wrote: Revenue grew in every region. Margins held steady."
    draft = codebook_draft()
    draft["themes"][0]["definition"] = copied
    assert freeze(draft, bundles) == [
        Refusal(f"themes[0].definition ({TRAIN})", "source_wording")
    ]


def test_another_codebook_and_a_missing_bundle_are_refused(bundles) -> None:
    assert freeze(codebook_draft(codebook_version=1), bundles) == [
        Refusal("codebook", "wrong_codebook")
    ]
    del bundles[TRAIN]
    assert freeze(codebook_draft(), bundles) == [
        Refusal("discovery_corpus", "unknown_document")
    ]


def test_a_draft_without_its_fields_does_not_parse() -> None:
    draft = codebook_draft()
    draft["themes"][0]["exclusion_rules"] = []
    with pytest.raises(RecordError) as refused:
        parse(draft, CodebookDraft, "codebook.working.toml")
    assert refused.value.problems == (
        (
            "themes.0.exclusion_rules: Tuple should have at least 1 item after"
            " validation, not 0"
        ),
        "themes: Tuple should have at least 1 item after validation, not 0",
    )


def test_a_frozen_version_validates_and_needs_its_adr(bundles) -> None:
    codebook = freeze(codebook_draft(), bundles, APPROVAL)
    assert isinstance(codebook, Codebook)
    check = {"pin": PIN, "split": synthetic_split(), "bundles": bundles}
    adr = f"The codebook's content hash is {codebook.content_hash}."
    assert validate_codebook(codebook, adr_text=adr, **check) == []
    assert validate_codebook(codebook, adr_text="no hash", **check) == [
        Refusal("codebook.approval.adr", "adr_not_cited")
    ]
    draft = freeze(codebook_draft(), bundles)
    assert isinstance(draft, Codebook)
    assert validate_codebook(draft, adr_text=adr, **check) == [
        Refusal("codebook.status", "codebook_not_approved")
    ]


def test_a_tampered_version_is_refused(bundles) -> None:
    codebook = freeze(codebook_draft(), bundles, APPROVAL)
    assert isinstance(codebook, Codebook)
    adr = codebook.content_hash
    check = {"pin": PIN, "split": synthetic_split(), "bundles": bundles}
    theme = codebook.themes[0]
    (positive,) = theme.positive_examples
    moved = positive.pointer.model_copy(update={"event_id": DEV})
    tampered = codebook.model_copy(
        update={
            "themes": (
                theme.model_copy(
                    update={
                        "positive_examples": (
                            positive.model_copy(update={"pointer": moved}),
                        )
                    }
                ),
            )
        }
    )
    assert validate_codebook(tampered, adr_text=adr, **check) == [
        Refusal("codebook.content_hash", "content_hash_mismatch"),
        Refusal("theme demand.positive_examples[0]", "outside_training"),
    ]
```

Create `/tmp/plan9-task7-tests.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "tests/contracts/test_data_dictionary.py": [
        (
            "from earnings_themes import problems, split\n",
            "from earnings_themes import codebook, problems, split\n",
        ),
        (
            "    SpanPointer,\n"
            "]\n",
            "    SpanPointer,\n"
            "    codebook.ExamplePointer,\n"
            "    codebook.Example,\n"
            "    codebook.Theme,\n"
            "    codebook.DiscoveryCorpus,\n"
            "    codebook.CodebookRules,\n"
            "    codebook.Approval,\n"
            "    codebook.DraftingAid,\n"
            "    codebook.Codebook,\n"
            "    codebook.ExampleDraft,\n"
            "    codebook.ThemeDraft,\n"
            "    codebook.CodebookDraft,\n"
            "]\n",
        ),
        (
            "    split.ExclusionReason,\n"
            "]\n",
            "    split.ExclusionReason,\n"
            "    codebook.CodebookStatus,\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/tests/test_codebook.py
python3 /tmp/plan9-extract.py /tmp/plan9-task7-tests.py && python3 /tmp/plan9-task7-tests.py
```

Expected:

```text
extracted packages/earnings-themes/tests/test_codebook.py: 214 lines
extracted /tmp/plan9-task7-tests.py: 50 lines
edited tests/contracts/test_data_dictionary.py: 3 replacement(s)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_codebook.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL, `2 errors`, with:

```text
ModuleNotFoundError: No module named 'earnings_themes.codebook'
ImportError: cannot import name 'codebook' from 'earnings_themes'
ERROR packages/earnings-themes/tests/test_codebook.py
ERROR tests/contracts/test_data_dictionary.py
```

- [x] **Step 3: Write the codebook contract**

Create `packages/earnings-themes/src/earnings_themes/codebook.py`:

```python
"""The codebook contract, and the freeze that approves a version (the Stage 6 spec,
§The codebook; A §608-611; R9.2, R9.3, R9.7; GS9, GS16).

- **Fields.** A version records its ID, version, status, content hash, discovery
  corpus, multi-label and boilerplate rules, approval, and drafting aid, and one
  entry per theme with R9.2's fields.
- **Examples.** An example points into a training bundle, in the form of a gold
  quote, or is synthetic, flagged, and in the user's words (A §611). None points
  outside the training partition (R12.3).
- **The hash.** The content hash covers everything but ``status``, ``approval``, and
  itself, so ADR 0003 can cite it before the approval is written (plan 9).
- **Frozen.** An approved version never changes. A claim no theme fits is recorded
  as ``unmatched``, never as a new theme (R9.3).
- ``sector_applicability`` is ``all`` or the codebook's own tags, mapped to no
  issuer (GS16).
"""

from collections.abc import Mapping, Sequence
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

from earnings_core import RejectionReason
from pydantic import Field, NonNegativeInt, StringConstraints, model_validator

from earnings_themes import tomlfile
from earnings_themes.anchoring import Bundle, SpanPointer, anchor, check_pointer
from earnings_themes.problems import Problem, Refusal
from earnings_themes.records import (
    IdPart,
    NonBlank,
    Part,
    Pin,
    Sha256Hex,
    ThemesRecord,
    digest,
    parse,
)
from earnings_themes.split import Partition, SplitManifest
from earnings_themes.wording import labelled_strings, shared

CODEBOOK_ID = "djia-pilot"
CODEBOOK_VERSION = 0
UNMATCHED = "unmatched"
"""What an assignment names when no theme fits its claim (R9.3)."""

ThemeId = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_.-]*$")]
SectorTag = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$")]
Some = Field(min_length=1)


class CodebookStatus(StrEnum):
    """Whether a version is approved."""

    DRAFT = "draft"
    APPROVED = "approved"


class ExamplePointer(SpanPointer):
    """A training bundle's quote, as a gold quote points at one."""

    event_id: IdPart
    doc_id: NonBlank


class Example(Part):
    """A pointer into a training bundle, or a synthetic example in the user's words."""

    synthetic: bool = False
    text: NonBlank | None = None
    pointer: ExamplePointer | None = None

    @model_validator(mode="after")
    def _one_kind(self) -> Self:
        if self.synthetic != (self.text is not None) or self.synthetic == (
            self.pointer is not None
        ):
            raise ValueError("an example is a pointer, or synthetic with its text")
        return self


class Theme(Part):
    """One theme's definition (R9.2)."""

    theme_id: ThemeId
    parent_id: ThemeId | None = None
    label: NonBlank
    definition: NonBlank
    inclusion_rules: Annotated[tuple[NonBlank, ...], Some]
    exclusion_rules: Annotated[tuple[NonBlank, ...], Some]
    positive_examples: Annotated[tuple[Example, ...], Some]
    hard_negatives: Annotated[tuple[Example, ...], Some]
    sector_applicability: Literal["all"] | Annotated[tuple[SectorTag, ...], Some]


class DiscoveryCorpus(Part):
    """The training bundles the codebook was discovered from (R12.3)."""

    pin: Pin
    split_hash: Sha256Hex
    event_ids: tuple[IdPart, ...]
    doc_ids: tuple[NonBlank, ...]


class CodebookRules(Part):
    """The multi-label and boilerplate rules, in the user's words."""

    multi_label: NonBlank
    boilerplate: NonBlank


class Approval(Part):
    """Who approved the version, when, and the decision record that says so."""

    approver: NonBlank
    approved_on: date
    adr: NonBlank


class DraftingAid(Part):
    """The model that drafted, and when (GS4, GS9)."""

    model_id: NonBlank
    drafted_on: date


class Codebook(ThemesRecord):
    """``codebook-v<N>.toml``: one codebook version."""

    codebook_id: IdPart
    codebook_version: NonNegativeInt
    status: CodebookStatus
    content_hash: Sha256Hex
    discovery_corpus: DiscoveryCorpus
    rules: CodebookRules
    approval: Approval | None = None
    drafting_aid: DraftingAid
    themes: Annotated[tuple[Theme, ...], Some]

    @model_validator(mode="after")
    def _approved_with_its_approval(self) -> Self:
        if (self.status is CodebookStatus.APPROVED) != (self.approval is not None):
            raise ValueError("an approved version has its approval, and only it")
        return self

    def theme_ids(self) -> frozenset[str]:
        return frozenset(theme.theme_id for theme in self.themes)


class ExampleDraft(Part):
    """An example as a draft names it: by its text, in one training bundle."""

    event_id: IdPart | None = None
    text: NonBlank
    prefix: str = ""
    suffix: str = ""
    synthetic: bool = False


class ThemeDraft(Part):
    """A theme as a draft proposes it."""

    theme_id: ThemeId
    parent_id: ThemeId | None = None
    label: NonBlank
    definition: NonBlank
    inclusion_rules: Annotated[tuple[NonBlank, ...], Some]
    exclusion_rules: Annotated[tuple[NonBlank, ...], Some]
    sector_applicability: Literal["all"] | Annotated[tuple[SectorTag, ...], Some]
    positive_examples: Annotated[tuple[ExampleDraft, ...], Some]
    hard_negatives: Annotated[tuple[ExampleDraft, ...], Some]


class CodebookDraft(Part):
    """``codebook.draft.toml`` and its working copy (the codebook brief)."""

    codebook_id: IdPart
    codebook_version: NonNegativeInt
    drafting_aid: DraftingAid
    rules: CodebookRules
    themes: Annotated[tuple[ThemeDraft, ...], Some]


def codebook_hash(codebook: Codebook) -> str:
    """The content hash: every field but ``status``, ``approval``, and itself."""
    return digest(
        codebook.model_dump(mode="json", exclude={"status", "approval", "content_hash"})
    )


def _structure(themes: Sequence[ThemeDraft | Theme]) -> list[Refusal]:
    refusals = []
    ids = [theme.theme_id for theme in themes]
    for theme_id in sorted({i for i in ids if ids.count(i) > 1}):
        refusals.append(Refusal(f"theme {theme_id}", Problem.DUPLICATE_ID))
    if UNMATCHED in ids:
        refusals.append(Refusal(f"theme {UNMATCHED}", Problem.DUPLICATE_ID))
    parents = {theme.theme_id: theme.parent_id for theme in themes}
    for theme in themes:
        if theme.parent_id is not None and theme.parent_id not in parents:
            refusals.append(Refusal(f"theme {theme.theme_id}", Problem.UNKNOWN_THEME))
    for theme_id in parents:
        seen, current = set(), theme_id
        while current is not None and current in parents and current not in seen:
            seen.add(current)
            current = parents[current]
        if current is not None and current in seen:
            refusals.append(Refusal(f"theme {theme_id}", Problem.PARENT_CYCLE))
    return refusals


def _training(split: SplitManifest, bundles: Mapping[str, Bundle]) -> dict[str, Bundle]:
    """The discovery corpus: each training event with a parsed document. An event
    whose release is unavailable has no text to discover from (D4)."""
    return {e: bundles[e] for e in split.events_in(Partition.TRAIN) if e in bundles}


def _wording(record: object, bundles: Mapping[str, Bundle]) -> list[Refusal]:
    found = shared(
        labelled_strings(record),
        ((name, b.document.canonical_text) for name, b in bundles.items()),
    )
    return [
        Refusal(f"{label} ({name})", Problem.SOURCE_WORDING)
        for label, name in sorted(found)
    ]


def _example(
    draft: ExampleDraft, subject: str, train: set[str], bundles: Mapping[str, Bundle]
) -> Example | Refusal:
    if draft.synthetic:
        if draft.event_id is not None or draft.prefix or draft.suffix:
            return Refusal(subject, Problem.MALFORMED)
        return Example(synthetic=True, text=draft.text)
    if draft.event_id is None:
        return Refusal(subject, Problem.SYNTHETIC_UNFLAGGED)
    if draft.event_id not in train:
        return Refusal(subject, Problem.OUTSIDE_TRAINING)
    bundle = bundles.get(draft.event_id)
    if bundle is None:
        return Refusal(subject, Problem.UNKNOWN_DOCUMENT)
    pointer = anchor(bundle, draft.text, draft.prefix, draft.suffix)
    if isinstance(pointer, str):
        return Refusal(subject, pointer)
    return Example(
        pointer=ExamplePointer(
            **pointer.model_dump(),
            event_id=draft.event_id,
            doc_id=bundle.document.doc_id,
        )
    )


def _theme(
    draft: ThemeDraft, train: set[str], bundles: Mapping[str, Bundle]
) -> Theme | list[Refusal]:
    subject = f"theme {draft.theme_id}"
    lists: dict[str, list[Example]] = {"positive_examples": [], "hard_negatives": []}
    refusals = []
    for field, kept in lists.items():
        for index, example in enumerate(getattr(draft, field)):
            made = _example(example, f"{subject}.{field}[{index}]", train, bundles)
            if isinstance(made, Refusal):
                refusals.append(made)
            else:
                kept.append(made)
    if refusals:
        return refusals
    fields = draft.model_dump(exclude={"positive_examples", "hard_negatives"})
    return Theme(**fields, **{field: tuple(made) for field, made in lists.items()})


def freeze_codebook(
    draft: CodebookDraft,
    *,
    pin: Pin,
    split: SplitManifest,
    bundles: Mapping[str, Bundle],
    approval: Approval | None = None,
) -> Codebook | list[Refusal]:
    """The version ``draft`` defines, with its examples anchored in the training
    bundles, or every reason it cannot be frozen. ``bundles`` holds each pilot
    event with a parsed document; only the training partition's are read."""
    refusals = []
    if (draft.codebook_id, draft.codebook_version) != (CODEBOOK_ID, CODEBOOK_VERSION):
        refusals.append(Refusal("codebook", Problem.WRONG_CODEBOOK))
    if split.pin != pin:
        refusals.append(Refusal("split", Problem.WRONG_PIN))
    training = _training(split, bundles)
    if not training:
        refusals.append(Refusal("discovery_corpus", Problem.UNKNOWN_DOCUMENT))
    if refusals:
        return refusals
    refusals += _structure(draft.themes)
    themes = []
    for theme_draft in draft.themes:
        made = _theme(theme_draft, set(split.events_in(Partition.TRAIN)), training)
        if isinstance(made, list):
            refusals += made
        else:
            themes.append(made)
    if refusals:
        return refusals
    codebook = Codebook(
        codebook_id=draft.codebook_id,
        codebook_version=draft.codebook_version,
        status=CodebookStatus.APPROVED if approval else CodebookStatus.DRAFT,
        content_hash="0" * 64,
        discovery_corpus=DiscoveryCorpus(
            pin=pin,
            split_hash=split.content_hash,
            event_ids=tuple(training),
            doc_ids=tuple(bundle.document.doc_id for bundle in training.values()),
        ),
        rules=draft.rules,
        approval=approval,
        drafting_aid=draft.drafting_aid,
        themes=tuple(themes),
    )
    if refusals := _wording(codebook.model_dump(mode="json"), training):
        return refusals
    return codebook.model_copy(update={"content_hash": codebook_hash(codebook)})


def validate_codebook(
    codebook: Codebook,
    *,
    pin: Pin,
    split: SplitManifest,
    bundles: Mapping[str, Bundle],
    adr_text: str | None,
) -> list[Refusal]:
    """Every reason a frozen version does not hold; empty when it does."""
    refusals = []
    if (codebook.codebook_id, codebook.codebook_version) != (
        CODEBOOK_ID,
        CODEBOOK_VERSION,
    ):
        refusals.append(Refusal("codebook", Problem.WRONG_CODEBOOK))
    if codebook_hash(codebook) != codebook.content_hash:
        refusals.append(Refusal("codebook.content_hash", Problem.CONTENT_HASH_MISMATCH))
    if codebook.status is not CodebookStatus.APPROVED:
        refusals.append(Refusal("codebook.status", Problem.CODEBOOK_NOT_APPROVED))
    elif adr_text is None or codebook.content_hash not in adr_text:
        refusals.append(Refusal("codebook.approval.adr", Problem.ADR_NOT_CITED))
    corpus = codebook.discovery_corpus
    if corpus.pin != pin:
        refusals.append(Refusal("discovery_corpus.pin", Problem.WRONG_PIN))
    if corpus.split_hash != split.content_hash:
        refusals.append(Refusal("discovery_corpus.split_hash", Problem.WRONG_SPLIT))
    training = _training(split, bundles)
    doc_ids = tuple(bundle.document.doc_id for bundle in training.values())
    if (corpus.event_ids, corpus.doc_ids) != (tuple(training), doc_ids):
        refusals.append(Refusal("discovery_corpus", Problem.DISCOVERY_CORPUS))
    refusals += _structure(codebook.themes)
    train = set(split.events_in(Partition.TRAIN))
    for theme in codebook.themes:
        for field in ("positive_examples", "hard_negatives"):
            for index, example in enumerate(getattr(theme, field)):
                subject = f"theme {theme.theme_id}.{field}[{index}]"
                refusals += _pointer_refusals(example, subject, training, train)
    return refusals + _wording(codebook.model_dump(mode="json"), training)


def _pointer_refusals(
    example: Example, subject: str, bundles: Mapping[str, Bundle], train: set[str]
) -> list[Refusal]:
    pointer = example.pointer
    if pointer is None:
        return []
    if pointer.event_id not in train:
        return [Refusal(subject, Problem.OUTSIDE_TRAINING)]
    bundle = bundles.get(pointer.event_id)
    if bundle is None:
        return [Refusal(subject, Problem.UNKNOWN_DOCUMENT)]
    if pointer.doc_id != bundle.document.doc_id:
        return [Refusal(subject, RejectionReason.WRONG_DOCUMENT)]
    span = SpanPointer(**pointer.model_dump(exclude={"event_id", "doc_id"}))
    return [Refusal(subject, reason) for reason in check_pointer(bundle, span)]


def codebook_toml(codebook: Codebook) -> str:
    """The committed file: pointers, hashes, and the user's words, never a quote."""
    header = (
        f"Codebook {codebook.codebook_id} v{codebook.codebook_version}"
        " (Stage 6, GS9). Written by `earnings-pipeline codebook freeze`;"
        " never edited. Examples are pointers or synthetic."
    )
    return tomlfile.dumps(codebook.model_dump(mode="python"), header=header)


def load_codebook(path: Path) -> Codebook:
    """A committed codebook version, read through its contract."""
    return parse(tomlfile.read(path), Codebook, path.name)


def load_codebook_draft(path: Path) -> CodebookDraft:
    """A local codebook draft or working copy, read through its contract."""
    return parse(tomlfile.read(path), CodebookDraft, path.name)
```

Create `/tmp/plan9-task7-impl.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/data-dictionary.md": [
        (
            "| `mask_ids` | tuple of string | The boilerplate masks over it, each `<category>-<start>-<end>` |\n"
            "\n",
            "| `mask_ids` | tuple of string | The boilerplate masks over it, each `<category>-<start>-<end>` |\n"
            "\n"
            "### `CodebookStatus`\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `draft` | Frozen by the build but not approved; never written |\n"
            "| `approved` | Approved, with its `Approval`; the only status committed |\n"
            "\n"
            "### `ExamplePointer`\n"
            "\n"
            "A `SpanPointer` into a training bundle, with its document.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `start` | int ≥ 0 | As `SpanPointer` |\n"
            "| `end` | int > `start` | As `SpanPointer` |\n"
            "| `element_id` | string | As `SpanPointer` |\n"
            "| `quote_sha256` | 64 lowercase hex | As `SpanPointer` |\n"
            "| `context_sha256` | 64 lowercase hex or null | As `SpanPointer` |\n"
            "| `mask_ids` | tuple of string | As `SpanPointer` |\n"
            "| `event_id` | ID part | The training event |\n"
            "| `doc_id` | string | Its canonical document |\n"
            "\n"
            "### `Example`\n"
            "\n"
            "Exactly one kind: a pointer, or synthetic with its text.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `synthetic` | bool | True for an example in the user's words |\n"
            "| `text` | string or null | The synthetic example's text |\n"
            "| `pointer` | `ExamplePointer` or null | The quoted example |\n"
            "\n"
            "### `Theme`\n"
            "\n"
            "One theme (R9.2). Every list has at least one item.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `theme_id` | `^[a-z][a-z0-9_.-]*$` | Its ID; `unmatched` is reserved |\n"
            "| `parent_id` | theme ID or null | Its parent theme |\n"
            "| `label` | string | Its short name |\n"
            "| `definition` | string | Its definition |\n"
            "| `inclusion_rules` | tuple of string | What it covers |\n"
            "| `exclusion_rules` | tuple of string | What it does not |\n"
            "| `positive_examples` | tuple of `Example` | Examples it covers |\n"
            "| `hard_negatives` | tuple of `Example` | Confusable examples it does not |\n"
            "| `sector_applicability` | `\"all\"` or tuple of sector tag | Where it applies |\n"
            "\n"
            "### `DiscoveryCorpus`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `pin` | `Pin` | The pilot |\n"
            "| `split_hash` | 64 lowercase hex | The split's `content_hash` |\n"
            "| `event_ids` | tuple of ID part | The training events with a parsed document |\n"
            "| `doc_ids` | tuple of string | Their canonical documents, in the same order |\n"
            "\n"
            "### `CodebookRules`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `multi_label` | string | How a claim takes more than one theme |\n"
            "| `boilerplate` | string | How masked text is treated (R3.4) |\n"
            "\n"
            "### `Approval`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `approver` | string | Who approved the codebook |\n"
            "| `approved_on` | date | When |\n"
            "| `adr` | path | ADR 0003, which cites the content hash |\n"
            "\n"
            "### `DraftingAid`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `model_id` | string | The Claude model that drafted, in an interactive session outside the required path (GS4) |\n"
            "| `drafted_on` | date | When |\n"
            "\n"
            "### `Codebook`\n"
            "\n"
            "`codebooks/djia-pilot/codebook-v<N>.toml`, written once, approved.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `schema_version` | `1` | Themes record schema version |\n"
            "| `codebook_id` | ID part | `djia-pilot` |\n"
            "| `codebook_version` | int ≥ 0 | `0` for Stage 6 |\n"
            "| `status` | `CodebookStatus` | `approved` exactly when `approval` is set |\n"
            "| `content_hash` | 64 lowercase hex | SHA-256 of the canonical JSON of every field but `status`, `approval`, and itself, so an ADR can cite it before approval |\n"
            "| `discovery_corpus` | `DiscoveryCorpus` | What it was discovered from |\n"
            "| `rules` | `CodebookRules` | Its rules |\n"
            "| `approval` | `Approval` or null | The approval |\n"
            "| `drafting_aid` | `DraftingAid` | The drafting session |\n"
            "| `themes` | tuple of `Theme` | Its themes |\n"
            "\n"
            "### `ExampleDraft`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `event_id` | ID part or null | The training event quoted; null for a synthetic example |\n"
            "| `text` | string | The exact text, or the synthetic example |\n"
            "| `prefix` | string | Text just before it, when it repeats |\n"
            "| `suffix` | string | Text just after it, when it repeats |\n"
            "| `synthetic` | bool | True for an example in the user's words |\n"
            "\n"
            "### `ThemeDraft`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `theme_id` | theme ID | As `Theme` |\n"
            "| `parent_id` | theme ID or null | As `Theme` |\n"
            "| `label` | string | As `Theme` |\n"
            "| `definition` | string | As `Theme` |\n"
            "| `inclusion_rules` | tuple of string | As `Theme` |\n"
            "| `exclusion_rules` | tuple of string | As `Theme` |\n"
            "| `sector_applicability` | `\"all\"` or tuple of sector tag | As `Theme` |\n"
            "| `positive_examples` | tuple of `ExampleDraft` | Anchored into `ExamplePointer`s |\n"
            "| `hard_negatives` | tuple of `ExampleDraft` | Anchored likewise |\n"
            "\n"
            "### `CodebookDraft`\n"
            "\n"
            "`data/runs/gold/drafts/codebook.draft.toml` and its working copy; never committed.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `codebook_id` | ID part | As `Codebook` |\n"
            "| `codebook_version` | int ≥ 0 | As `Codebook` |\n"
            "| `drafting_aid` | `DraftingAid` | The drafting session |\n"
            "| `rules` | `CodebookRules` | As `Codebook` |\n"
            "| `themes` | tuple of `ThemeDraft` | At least one |\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/codebook.py
python3 /tmp/plan9-extract.py /tmp/plan9-task7-impl.py && python3 /tmp/plan9-task7-impl.py
```

Expected:

```text
extracted packages/earnings-themes/src/earnings_themes/codebook.py: 401 lines
extracted /tmp/plan9-task7-impl.py: 160 lines
edited docs/data-dictionary.md: 1 replacement(s)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_codebook.py tests/contracts/test_data_dictionary.py -q`

Expected: `151 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py packages/earnings-themes/src/earnings_themes/codebook.py packages/earnings-themes/tests/test_codebook.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1654 passed, 1 skipped, 24 deselected`; `All checks passed!` and `284 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-themes/src/earnings_themes/codebook.py packages/earnings-themes/tests/test_codebook.py tests/contracts/test_data_dictionary.py
git commit -m "feat(themes): the codebook contract and its freeze (GS9, GS16)"
```

---

### Task 8: The gold contract, its anchor, and its validator

S §The gold, §Curated hard negatives, GS4, GS5, GS10, and P9-4, P9-18. `build_gold`
anchors every quote in a working copy, derives each item's origin by comparing it
with the kept draft, counts the rejected items, and validates the result.
`validate_gold` rechecks a committed file against its local document: the pin, the
split and partition, the codebook, the signature, `no_theme`, the IDs, every
pointer, the origin counts, and the wording guard over its own release. The curated
hard negatives take the same form over Stage 1's fixtures, carry the pin as every
Stage 6 record does (S §The pin), need all three kinds, and have their wording
checked against every fixture. A `theme_id` is an ID, so a refusal that names one
never echoes a phrase (GS13), and `signed` is P9-18's one test of a signature. The
step also amends S's `no_theme` bullet (P9-4).

**Files:**

- Create: `packages/earnings-themes/src/earnings_themes/gold.py` and
  `annotation.py`.
- Test: create `packages/earnings-themes/tests/test_gold.py`.
- Modify, by exact replacement: `tests/contracts/test_data_dictionary.py`,
  `docs/data-dictionary.md`, and `specs/pilot-codebook-split-and-gold-set-protocol.md`.

**Interfaces:**

- Consumes: Tasks 3 to 7, and `synthetic.py`'s `gold_draft` and `curated_draft`.
- Produces:
  - in `gold.py`: `Origin`, `Support`, `ReleaseLabel`, and `NegativeKind`;
    `GoldQuote`, `GoldClaim`, `GoldAssignment`, `HardNegative`,
    `ReleaseIdentification`, `DraftCounts`, `CodebookRef`, `Gold`,
    `FixtureNegatives`, and `HardNegativeSet`; `no_theme_of(assignments) -> bool`;
    `HEADER`; `gold_toml(record) -> str`; and `load_gold(path)` and
    `load_hard_negatives(path)`;
  - in `annotation.py`: the drafts `QuoteDraft`, `ClaimDraft`, `AssignmentDraft`,
    `HardNegativeDraft`, `GoldDraft`, `FixtureDraft`, and `CuratedDraft`, with
    `load_gold_draft(path)` and `load_curated_draft(path)`; `signed(annotator) ->
    bool`; `build_gold(drafted, working, *, bundle, pin, split, codebook) -> Gold |
    list[Refusal]`; `validate_gold(gold, *, bundle, pin, split, codebook,
    require_signature=True) -> list[Refusal]`; `build_curated(drafted, working, *,
    bundles, pin, codebook) -> HardNegativeSet | list[Refusal]`; and
    `validate_curated(record, *, bundles, pin, codebook, require_signature=True) ->
    list[Refusal]`;
  - `theme_id` fields typed as `codebook.ThemeId`, and `HardNegativeSet.pin`.

- [x] **Step 1: Write the failing tests**

> Deviation: after the final review (`c77824a`), `test_a_tampered_pointer_is_refused` also checks tampered pointers through `validate_gold` and `validate_curated` (T8-M3); counts unchanged.

Create `packages/earnings-themes/tests/test_gold.py`:

```python
"""The gold contract (the Stage 6 spec, §The gold): the build anchors every quote
and derives every origin, and the validator refuses each problem by item and
reason, never by text."""

from datetime import date

import pytest
from earnings_themes.annotation import (
    CuratedDraft,
    GoldDraft,
    build_curated,
    build_gold,
    signed,
    validate_curated,
    validate_gold,
)
from earnings_themes.codebook import (
    Approval,
    Codebook,
    CodebookDraft,
    freeze_codebook,
)
from earnings_themes.gold import (
    Gold,
    HardNegativeSet,
    Origin,
    gold_toml,
    load_gold,
    load_hard_negatives,
)
from earnings_themes.problems import Refusal
from earnings_themes.records import RecordError, parse
from earnings_themes.split import Partition
from earnings_themes.synthetic import (
    DEV,
    LATER,
    PIN,
    TEST,
    TRAIN,
    build_synthetic,
    codebook_draft,
    curated_draft,
    gold_draft,
    synthetic_split,
)

SIGNED = "Lowell Mason (verified a Claude draft)"


@pytest.fixture(scope="module")
def bundles():
    return {e: build_synthetic(e).bundle for e in (TRAIN, DEV, TEST, LATER)}


@pytest.fixture(scope="module")
def codebook(bundles) -> Codebook:
    approval = Approval(
        approver="Lowell Mason",
        approved_on=date(2026, 10, 2),
        adr="docs/adr/0003-approve-pilot-codebook-v0.md",
    )
    made = freeze_codebook(
        parse(codebook_draft(), CodebookDraft, "draft"),
        pin=PIN,
        split=synthetic_split(),
        bundles=bundles,
        approval=approval,
    )
    assert isinstance(made, Codebook)
    return made


def build(bundles, codebook, drafted: dict, working: dict | None = None):
    return build_gold(
        parse(drafted, GoldDraft, "draft"),
        parse(working or drafted, GoldDraft, "working"),
        bundle=bundles[drafted["event_id"]],
        pin=PIN,
        split=synthetic_split(),
        codebook=codebook,
    )


def check(gold: Gold, bundles, codebook, **options):
    return validate_gold(
        gold,
        bundle=bundles[gold.event_id],
        pin=PIN,
        split=synthetic_split(),
        codebook=codebook,
        **options,
    )


def test_an_accepted_draft_builds_unsigned_and_fails_only_on_its_signature(
    bundles, codebook
) -> None:
    gold = build(bundles, codebook, gold_draft())
    assert isinstance(gold, Gold)
    assert gold.partition is Partition.TRAIN
    assert gold.document_id == f"{TRAIN}:release"
    assert gold.annotator == ""
    assert {item.origin for item in (*gold.quotes, *gold.claims)} == {
        Origin.DRAFTED_ACCEPTED
    }
    assert gold.counts.model_dump() == {
        "accepted": 8,
        "edited": 0,
        "rejected": 0,
        "added": 0,
    }
    assert check(gold, bundles, codebook) == [Refusal("annotator", "unsigned")]


def test_origins_come_from_comparing_the_working_copy_with_the_draft(
    bundles, codebook
) -> None:
    drafted = gold_draft()
    working = gold_draft(annotator=SIGNED)
    working["claims"][1]["claim"] = "Margins were flat, in the user's words."
    del working["hard_negatives"][0]
    working["quotes"].append({"quote_id": "q4", "text": "Quarterly results"})
    working["claims"].append(
        {"claim_id": "c3", "quote_ids": ["q4"], "claim": "A heading."}
    )
    working["assignments"].append(
        {"claim_id": "c3", "theme_id": "unmatched", "support": "uncertain"}
    )
    gold = build(bundles, codebook, drafted, working)
    assert isinstance(gold, Gold)
    assert gold.counts.model_dump() == {
        "accepted": 6,
        "edited": 1,
        "rejected": 1,
        "added": 3,
    }
    assert gold.claims[1].origin is Origin.DRAFTED_EDITED
    assert gold.quotes[3].origin is Origin.ANNOTATOR_ADDED
    assert check(gold, bundles, codebook) == []


def test_a_signed_file_round_trips_and_holds_no_quote(
    bundles, codebook, tmp_path
) -> None:
    gold = build(bundles, codebook, gold_draft(annotator=SIGNED))
    assert isinstance(gold, Gold)
    path = tmp_path / f"{TRAIN}.toml"
    path.write_text(gold_toml(gold), encoding="utf-8")
    assert load_gold(path) == gold
    text = path.read_text(encoding="utf-8")
    assert "Margins held steady" not in text
    assert "Revenue grew" not in text


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ({"no_theme": True}, Refusal("no_theme", "no_theme_mismatch")),
        (
            {"quotes": [{"quote_id": "q1", "text": "Region Sales"}]},
            Refusal("quote q1", "not_narrative"),
        ),
        (
            {"quotes": [{"quote_id": "q1", "text": "Revenue grew in every region."}]},
            Refusal("quote q1", "ambiguous_occurrence"),
        ),
        (
            {"quotes": [{"quote_id": "q1", "text": "Scanned text from an image."}]},
            Refusal("quote q1", "ocr_derived_text"),
        ),
    ],
)
def test_a_bad_draft_is_refused_by_item(bundles, codebook, change, refusal) -> None:
    draft = gold_draft(**change)
    if "quotes" in change:
        draft.update(claims=[], assignments=[], hard_negatives=[], no_theme=True)
    assert build(bundles, codebook, draft) == [refusal]


def test_ids_themes_and_ties_are_checked(bundles, codebook) -> None:
    draft = gold_draft(no_theme=True)
    draft["claims"].append({"claim_id": "c1", "quote_ids": ["q9"], "claim": "Again."})
    draft["assignments"] = [
        {
            "claim_id": "c1",
            "theme_id": "pricing",
            "support": "uncertain",
            "tie_group": "t1",
        },
        {
            "claim_id": "c2",
            "theme_id": "unmatched",
            "support": "uncertain",
            "tie_group": "t1",
        },
        {"claim_id": "c9", "theme_id": "unmatched", "support": "uncertain"},
    ]
    assert build(bundles, codebook, draft) == [
        Refusal("claim c1", "duplicate_id"),
        Refusal("claim c1", "unknown_quote"),
        Refusal("assignment c1/pricing", "unknown_theme"),
        Refusal("assignment c9/unmatched", "unknown_claim"),
        Refusal("tie_group t1", "tie_group"),
    ]


def test_a_claim_that_copies_the_release_is_refused(bundles, codebook) -> None:
    draft = gold_draft()
    draft["claims"][0]["claim"] = (
        "Per the release, Revenue grew in every region. Margins held steady."
    )
    assert build(bundles, codebook, draft) == [
        Refusal(f"claims[0].claim ({TRAIN})", "source_wording")
    ]


def test_another_document_pin_split_codebook_or_partition_is_refused(
    bundles, codebook
) -> None:
    gold = build(bundles, codebook, gold_draft(annotator=SIGNED))
    assert isinstance(gold, Gold)
    tampered = gold.model_copy(
        update={
            "pin": PIN.model_copy(update={"pilot_hash": "4" * 64}),
            "split_hash": "5" * 64,
            "partition": Partition.DEV,
            "codebook": gold.codebook.model_copy(update={"codebook_version": 1}),
            "doc_id": "other@walker-1#0000000000000000",
            "canonical_hash": "6" * 64,
        }
    )
    assert check(tampered, bundles, codebook) == [
        Refusal("doc_id", "wrong_document"),
        Refusal("canonical_hash", "canonical_hash_mismatch"),
        Refusal("pin", "wrong_pin"),
        Refusal("split_hash", "wrong_split"),
        Refusal("partition", "wrong_partition"),
        Refusal("codebook", "wrong_codebook"),
    ]


def test_an_excluded_event_takes_no_gold(bundles, codebook) -> None:
    assert build(bundles, codebook, gold_draft(LATER)) == [
        Refusal("partition", "excluded_event")
    ]


def test_counts_that_disagree_with_the_origins_are_refused(bundles, codebook) -> None:
    gold = build(bundles, codebook, gold_draft(annotator=SIGNED))
    assert isinstance(gold, Gold)
    tampered = gold.model_copy(
        update={"counts": gold.counts.model_copy(update={"accepted": 7})}
    )
    assert check(tampered, bundles, codebook) == [Refusal("counts", "counts_mismatch")]


def curated(fixtures, signed: bool = True) -> CuratedDraft:
    """Hard negatives over two Stage 1 fixtures, their quotes taken from each
    fixture's own unique narrative sentences, never typed here."""
    draft = curated_draft(fixtures, SIGNED if signed else "")
    return parse(draft, CuratedDraft, "curated")


def test_curated_hard_negatives_over_stage_1_fixtures_validate(
    fixtures, codebook, tmp_path
) -> None:
    draft = curated(fixtures)
    record = build_curated(draft, draft, bundles=fixtures, pin=PIN, codebook=codebook)
    assert isinstance(record, HardNegativeSet)
    assert record.pin == PIN
    assert validate_curated(record, bundles=fixtures, pin=PIN, codebook=codebook) == []
    path = tmp_path / "hard-negatives.toml"
    path.write_text(gold_toml(record), encoding="utf-8")
    assert load_hard_negatives(path) == record


def test_curated_hard_negatives_need_every_kind_and_a_signature(
    fixtures, codebook
) -> None:
    draft = curated(fixtures, signed=False)
    record = build_curated(draft, draft, bundles=fixtures, pin=PIN, codebook=codebook)
    assert isinstance(record, HardNegativeSet)
    assert validate_curated(record, bundles=fixtures, pin=PIN, codebook=codebook) == [
        Refusal("annotator", "unsigned")
    ]
    narrowed = record.model_copy(update={"documents": record.documents[:1]})
    assert Refusal("hard_negatives", "negative_kinds") in validate_curated(
        narrowed,
        bundles=fixtures,
        pin=PIN,
        codebook=codebook,
        require_signature=False,
    )


def test_curated_hard_negatives_carry_the_pin(fixtures, codebook) -> None:
    """The Stage 6 spec, §The pin: every Stage 6 record carries it, the curated
    hard negatives too, though they belong to no partition."""
    draft = curated(fixtures)
    record = build_curated(draft, draft, bundles=fixtures, pin=PIN, codebook=codebook)
    assert isinstance(record, HardNegativeSet)
    other = PIN.model_copy(update={"pilot_hash": "4" * 64})
    assert validate_curated(record, bundles=fixtures, pin=other, codebook=codebook) == [
        Refusal("pin", "wrong_pin")
    ]


def test_a_blank_signature_is_not_a_signature(bundles, codebook) -> None:
    """P9-18: signed means not blank, whitespace included, wherever it is asked."""
    assert [signed(name) for name in ("", "   ", SIGNED)] == [False, False, True]
    gold = build(bundles, codebook, gold_draft(annotator="   "))
    assert isinstance(gold, Gold)
    assert check(gold, bundles, codebook) == [Refusal("annotator", "unsigned")]


def test_a_theme_id_that_is_not_an_id_is_refused_by_its_field() -> None:
    """A refusal names a theme by its ID, so a theme_id is an ID: a phrase in
    its place is refused by field path, never echoed (GS13)."""
    draft = gold_draft()
    draft["assignments"][0]["theme_id"] = "Demand rose in every region"
    with pytest.raises(RecordError) as caught:
        parse(draft, GoldDraft, "draft")
    assert caught.value.problems[0].startswith("assignments.0.theme_id: ")
    assert "Demand" not in str(caught.value)
```

Create `/tmp/plan9-task8-tests.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "tests/contracts/test_data_dictionary.py": [
        (
            "from earnings_themes import codebook, problems, split\n",
            "from earnings_themes import annotation, codebook, gold, problems, split\n",
        ),
        (
            "    codebook.CodebookDraft,\n"
            "]\n",
            "    codebook.CodebookDraft,\n"
            "    gold.GoldQuote,\n"
            "    gold.GoldClaim,\n"
            "    gold.GoldAssignment,\n"
            "    gold.HardNegative,\n"
            "    gold.ReleaseIdentification,\n"
            "    gold.DraftCounts,\n"
            "    gold.CodebookRef,\n"
            "    gold.Gold,\n"
            "    gold.FixtureNegatives,\n"
            "    gold.HardNegativeSet,\n"
            "    annotation.QuoteDraft,\n"
            "    annotation.ClaimDraft,\n"
            "    annotation.AssignmentDraft,\n"
            "    annotation.HardNegativeDraft,\n"
            "    annotation.GoldDraft,\n"
            "    annotation.FixtureDraft,\n"
            "    annotation.CuratedDraft,\n"
            "]\n",
        ),
        (
            "    codebook.CodebookStatus,\n"
            "]\n",
            "    codebook.CodebookStatus,\n"
            "    gold.Origin,\n"
            "    gold.Support,\n"
            "    gold.ReleaseLabel,\n"
            "    gold.NegativeKind,\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/tests/test_gold.py
python3 /tmp/plan9-extract.py /tmp/plan9-task8-tests.py && python3 /tmp/plan9-task8-tests.py
```

Expected:

```text
extracted packages/earnings-themes/tests/test_gold.py: 324 lines
extracted /tmp/plan9-task8-tests.py: 59 lines
edited tests/contracts/test_data_dictionary.py: 3 replacement(s)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL, `2 errors`, with:

```text
ModuleNotFoundError: No module named 'earnings_themes.annotation'
ImportError: cannot import name 'annotation' from 'earnings_themes'
ERROR packages/earnings-themes/tests/test_gold.py
ERROR tests/contracts/test_data_dictionary.py
```

- [x] **Step 3: Write the gold contract and the annotation build**

Create `packages/earnings-themes/src/earnings_themes/gold.py`:

```python
"""The gold contract (the Stage 6 spec, §The gold and §Curated hard negatives; R9.9,
R12.5, R12.6, R13.1; GS3, GS4, GS5, GS10).

- **One file per annotated bundle,** ``gold/<event>.toml``: the document, the
  pin, the split and partition, the codebook version, the signature, the drafting
  aid, the origin counts, ``no_theme``, and the release-identification label.
- **Quotes** are pointers, never text (GS3). **Claims** are the user's words.
  **Assignments** are one row per claim and theme, or ``unmatched``, each with its
  support; rows sharing a ``tie_group`` are alternatives for one claim (R12.6).
  **Hard-negative claims** are expected ``does_not_support`` (D4).
- **Origins.** Each item is ``drafted_accepted``, ``drafted_edited``, or
  ``annotator_added``, derived from the kept draft (GS5).
- **No theme.** ``no_theme`` is true exactly when no assignment pairs a claim with a
  codebook theme under ``supports`` (R12.4; plan 9, the user's answer).
- **Curated hard negatives** point into Stage 1's canonical fixtures and belong to
  no partition (GS10).
"""

from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Self

from pydantic import Field, NonNegativeInt, StringConstraints, model_validator

from earnings_themes import tomlfile
from earnings_themes.anchoring import SpanPointer
from earnings_themes.codebook import UNMATCHED, DraftingAid, ThemeId
from earnings_themes.records import (
    IdPart,
    NonBlank,
    Part,
    Pin,
    Sha256Hex,
    ThemesRecord,
    parse,
)
from earnings_themes.split import Partition

Accession = Annotated[str, StringConstraints(pattern=r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")]
Some = Field(min_length=1)


class Origin(StrEnum):
    """Where a gold item came from, against the kept draft (GS5)."""

    DRAFTED_ACCEPTED = "drafted_accepted"
    DRAFTED_EDITED = "drafted_edited"
    ANNOTATOR_ADDED = "annotator_added"


class Support(StrEnum):
    """Whether a claim's quotes support it under a theme (R8.1)."""

    SUPPORTS = "supports"
    DOES_NOT_SUPPORT = "does_not_support"
    UNCERTAIN = "uncertain"


class ReleaseLabel(StrEnum):
    """R13.1's release-identification label."""

    RELEASE = "release"
    NOT_RELEASE = "not_release"
    AMBIGUOUS = "ambiguous"


class NegativeKind(StrEnum):
    """What makes a hard negative confusable (R12.5)."""

    PERIOD = "period"
    ISSUER = "issuer"
    SECTION = "section"


class GoldQuote(SpanPointer):
    """One quote: a pointer into the bundle's canonical text."""

    quote_id: IdPart
    origin: Origin


class GoldClaim(Part):
    """One claim, in the user's words, resting on quotes."""

    claim_id: IdPart
    quote_ids: Annotated[tuple[IdPart, ...], Some]
    claim: NonBlank
    origin: Origin


class GoldAssignment(Part):
    """One claim and one theme, or ``unmatched`` (R9.9)."""

    claim_id: IdPart
    theme_id: ThemeId
    support: Support
    tie_group: IdPart | None = None
    origin: Origin


class HardNegative(Part):
    """A claim its quotes do not support: from a confusable period, issuer, or
    section (R12.5, D4)."""

    claim_id: IdPart
    quote_ids: Annotated[tuple[IdPart, ...], Some]
    claim: NonBlank
    negative_kind: NegativeKind
    theme_id: ThemeId | None = None
    origin: Origin


class ReleaseIdentification(Part):
    """Whether the document is this event's earnings release, for its issuer and
    period; with ``not_release``, the true release may be given, as facts."""

    label: ReleaseLabel
    note: NonBlank
    true_accession: Accession | None = None
    true_exhibit: NonBlank | None = None

    @model_validator(mode="after")
    def _facts_only_for_not_release(self) -> Self:
        named = self.true_accession is not None or self.true_exhibit is not None
        if named and self.label is not ReleaseLabel.NOT_RELEASE:
            raise ValueError("only not_release names the true release")
        return self


class DraftCounts(Part):
    """The drafted items accepted, edited, and rejected, and the items added."""

    accepted: NonNegativeInt
    edited: NonNegativeInt
    rejected: NonNegativeInt
    added: NonNegativeInt


class CodebookRef(Part):
    """The codebook version an annotation codes against."""

    codebook_id: IdPart
    codebook_version: NonNegativeInt
    content_hash: Sha256Hex


class Gold(ThemesRecord):
    """``gold/<event>.toml``: one bundle's signed gold; ``<event>`` is the event
    ID with its colon as an underscore."""

    event_id: IdPart
    document_id: IdPart
    doc_id: NonBlank
    canonical_hash: Sha256Hex
    pin: Pin
    split_hash: Sha256Hex
    partition: Partition
    codebook: CodebookRef
    annotator: str
    drafting_aid: DraftingAid
    counts: DraftCounts
    no_theme: bool
    release_identification: ReleaseIdentification
    quotes: tuple[GoldQuote, ...] = ()
    claims: tuple[GoldClaim, ...] = ()
    assignments: tuple[GoldAssignment, ...] = ()
    hard_negatives: tuple[HardNegative, ...] = ()


class FixtureNegatives(Part):
    """The curated hard negatives over one Stage 1 fixture."""

    fixture_id: IdPart
    doc_id: NonBlank
    canonical_hash: Sha256Hex
    quotes: Annotated[tuple[GoldQuote, ...], Some]
    hard_negatives: Annotated[tuple[HardNegative, ...], Some]


class HardNegativeSet(ThemesRecord):
    """``tests/fixtures/gold/hard-negatives.toml``: outside the pilot and in no
    partition (D4, GS10), though it carries the pin, as every Stage 6 record does."""

    pin: Pin
    annotator: str
    drafting_aid: DraftingAid
    counts: DraftCounts
    codebook: CodebookRef
    documents: Annotated[tuple[FixtureNegatives, ...], Some]


def no_theme_of(assignments: Iterable[GoldAssignment]) -> bool:
    """True exactly when no row pairs a claim with a theme under ``supports``."""
    return not any(
        a.theme_id != UNMATCHED and a.support is Support.SUPPORTS for a in assignments
    )


HEADER = (
    "Stage 6 gold (the pilot codebook, split, and gold-set protocol). Written by"
    " `earnings-pipeline gold anchor`; quotes are pointers, and every other word is"
    " the annotator's."
)


def gold_toml(record: Gold | HardNegativeSet) -> str:
    """The committed file: pointers, hashes, and the user's words, never a quote."""
    return tomlfile.dumps(record.model_dump(mode="python"), header=HEADER)


def load_gold(path: Path) -> Gold:
    """One bundle's gold file, read through its contract."""
    return parse(tomlfile.read(path), Gold, path.name)


def load_hard_negatives(path: Path) -> HardNegativeSet:
    """The curated hard negatives, read through their contract."""
    return parse(tomlfile.read(path), HardNegativeSet, path.name)
```

Create `packages/earnings-themes/src/earnings_themes/annotation.py`:

```python
"""Drafts, origins, the build that anchors a working copy, and the validator (the
Stage 6 spec, §Anchoring and validation and §Drafting and tools; GS4, GS5).

- **Drafts.** A drafting session writes ``<name>.draft.toml``, which is kept
  unchanged, and the user edits ``<name>.working.toml`` beside it. Both name quotes
  by their text, with context when the text repeats.
- **The build.** Every working quote is anchored, every item's origin derived by
  comparing the working copy with the draft, and the result validated. Any refusal
  writes nothing, and names its item by ID, never by text.
- **The validator** rechecks a committed file against its local document: the pin,
  split, partition, and codebook, the signature, ``no_theme``, the IDs, every
  pointer, the origin counts, and the wording guard.
"""

from collections.abc import Callable, Hashable, Mapping, Sequence
from pathlib import Path
from typing import Annotated

from earnings_core import RejectionReason
from pydantic import BaseModel

from earnings_themes import tomlfile
from earnings_themes.anchoring import Bundle, SpanPointer, anchor, check_pointer
from earnings_themes.codebook import (
    UNMATCHED,
    Codebook,
    CodebookStatus,
    DraftingAid,
    ThemeId,
)
from earnings_themes.gold import (
    CodebookRef,
    DraftCounts,
    FixtureNegatives,
    Gold,
    GoldAssignment,
    GoldClaim,
    GoldQuote,
    HardNegative,
    HardNegativeSet,
    NegativeKind,
    Origin,
    ReleaseIdentification,
    Some,
    Support,
    no_theme_of,
)
from earnings_themes.problems import Problem, Refusal
from earnings_themes.records import IdPart, NonBlank, Part, Pin, parse
from earnings_themes.split import Partition, SplitManifest
from earnings_themes.wording import labelled_strings, shared


class QuoteDraft(Part):
    """A quote as a draft names it: its exact text, and context when it repeats."""

    quote_id: IdPart
    text: NonBlank
    prefix: str = ""
    suffix: str = ""


class ClaimDraft(Part):
    claim_id: IdPart
    quote_ids: Annotated[tuple[IdPart, ...], Some]
    claim: NonBlank


class AssignmentDraft(Part):
    claim_id: IdPart
    theme_id: ThemeId
    support: Support
    tie_group: IdPart | None = None


class HardNegativeDraft(Part):
    claim_id: IdPart
    quote_ids: Annotated[tuple[IdPart, ...], Some]
    claim: NonBlank
    negative_kind: NegativeKind
    theme_id: ThemeId | None = None


class GoldDraft(Part):
    """``<event>.draft.toml`` and its working copy (the gold brief)."""

    event_id: IdPart
    annotator: str = ""
    drafting_aid: DraftingAid
    no_theme: bool
    release_identification: ReleaseIdentification
    quotes: tuple[QuoteDraft, ...] = ()
    claims: tuple[ClaimDraft, ...] = ()
    assignments: tuple[AssignmentDraft, ...] = ()
    hard_negatives: tuple[HardNegativeDraft, ...] = ()


class FixtureDraft(Part):
    fixture_id: IdPart
    quotes: Annotated[tuple[QuoteDraft, ...], Some]
    hard_negatives: Annotated[tuple[HardNegativeDraft, ...], Some]


class CuratedDraft(Part):
    """``hard-negatives.draft.toml`` and its working copy (the gold brief)."""

    annotator: str = ""
    drafting_aid: DraftingAid
    documents: Annotated[tuple[FixtureDraft, ...], Some]


def signed(annotator: str) -> bool:
    """P9-18: a file is signed when its ``annotator`` is not blank."""
    return bool(annotator.strip())


def load_gold_draft(path: Path) -> GoldDraft:
    return parse(tomlfile.read(path), GoldDraft, path.name)


def load_curated_draft(path: Path) -> CuratedDraft:
    return parse(tomlfile.read(path), CuratedDraft, path.name)


class _Origins:
    """Each working item's origin against the draft, and the counts (GS5)."""

    def __init__(self) -> None:
        self.counts = {origin: 0 for origin in Origin}
        self.rejected = 0

    def compare[T: BaseModel](
        self, drafted: Sequence[T], working: Sequence[T], key: Callable[[T], Hashable]
    ) -> list[Origin]:
        before = {key(item): item for item in drafted}
        kept = {key(item) for item in working}
        self.rejected += sum(1 for k in before if k not in kept)
        origins = []
        for item in working:
            if key(item) not in before:
                origin = Origin.ANNOTATOR_ADDED
            elif before[key(item)] == item:
                origin = Origin.DRAFTED_ACCEPTED
            else:
                origin = Origin.DRAFTED_EDITED
            self.counts[origin] += 1
            origins.append(origin)
        return origins

    def tally(self) -> DraftCounts:
        return DraftCounts(
            accepted=self.counts[Origin.DRAFTED_ACCEPTED],
            edited=self.counts[Origin.DRAFTED_EDITED],
            rejected=self.rejected,
            added=self.counts[Origin.ANNOTATOR_ADDED],
        )


def _by_id(item: BaseModel) -> Hashable:
    return getattr(item, "quote_id", None) or item.claim_id


def _by_row(item: AssignmentDraft) -> Hashable:
    return (item.claim_id, item.theme_id)


def _items(
    drafted: GoldDraft | FixtureDraft,
    working: GoldDraft | FixtureDraft,
    bundle: Bundle,
    origins: _Origins,
    prefix: str,
) -> tuple[dict[str, tuple], list[Refusal]]:
    refusals: list[Refusal] = []
    quotes = []
    marks = origins.compare(drafted.quotes, working.quotes, _by_id)
    for quote, origin in zip(working.quotes, marks, strict=True):
        pointer = anchor(bundle, quote.text, quote.prefix, quote.suffix)
        if isinstance(pointer, str):
            refusals.append(Refusal(f"{prefix}quote {quote.quote_id}", pointer))
            continue
        quotes.append(
            GoldQuote(**pointer.model_dump(), quote_id=quote.quote_id, origin=origin)
        )
    made: dict[str, tuple] = {"quotes": tuple(quotes)}
    kinds = [("hard_negatives", HardNegative, _by_id)]
    if isinstance(working, GoldDraft) and isinstance(drafted, GoldDraft):
        kinds = [
            ("claims", GoldClaim, _by_id),
            ("assignments", GoldAssignment, _by_row),
            *kinds,
        ]
    for field, model, key in kinds:
        items = getattr(working, field)
        marks = origins.compare(getattr(drafted, field), items, key)
        made[field] = tuple(
            model(**item.model_dump(), origin=origin)
            for item, origin in zip(items, marks, strict=True)
        )
    return made, refusals


def _codebook_ref(codebook: Codebook) -> CodebookRef:
    return CodebookRef(
        codebook_id=codebook.codebook_id,
        codebook_version=codebook.codebook_version,
        content_hash=codebook.content_hash,
    )


def build_gold(
    drafted: GoldDraft,
    working: GoldDraft,
    *,
    bundle: Bundle,
    pin: Pin,
    split: SplitManifest,
    codebook: Codebook,
) -> Gold | list[Refusal]:
    """The gold ``working`` defines over ``bundle``, or every reason it cannot be."""
    if {drafted.event_id, working.event_id} != {bundle.name}:
        return [Refusal("event_id", Problem.UNKNOWN_DOCUMENT)]
    origins = _Origins()
    made, refusals = _items(drafted, working, bundle, origins, "")
    if refusals:
        return refusals
    try:
        partition = split.partition_of(bundle.name)
    except KeyError:
        return [Refusal("event_id", Problem.UNKNOWN_DOCUMENT)]
    gold = Gold(
        event_id=bundle.name,
        document_id=f"{bundle.name}:release",
        doc_id=bundle.document.doc_id,
        canonical_hash=bundle.document.canonical_hash,
        pin=pin,
        split_hash=split.content_hash,
        partition=partition,
        codebook=_codebook_ref(codebook),
        annotator=working.annotator,
        drafting_aid=working.drafting_aid,
        counts=origins.tally(),
        no_theme=working.no_theme,
        release_identification=working.release_identification,
        **made,
    )
    refusals = validate_gold(
        gold,
        bundle=bundle,
        pin=pin,
        split=split,
        codebook=codebook,
        require_signature=False,
    )
    return refusals or gold


def _ids(
    quotes: Sequence[GoldQuote],
    claims: Sequence[GoldClaim],
    assignments: Sequence[GoldAssignment],
    negatives: Sequence[HardNegative],
    themes: frozenset[str],
    prefix: str,
) -> list[Refusal]:
    refusals = []
    quote_ids = [q.quote_id for q in quotes]
    claim_ids = [c.claim_id for c in (*claims, *negatives)]
    for name, ids in (("quote", quote_ids), ("claim", claim_ids)):
        for repeated in sorted({i for i in ids if ids.count(i) > 1}):
            refusals.append(Refusal(f"{prefix}{name} {repeated}", Problem.DUPLICATE_ID))
    for claim in (*claims, *negatives):
        for quote_id in claim.quote_ids:
            if quote_id not in quote_ids:
                subject = f"{prefix}claim {claim.claim_id}"
                refusals.append(Refusal(subject, Problem.UNKNOWN_QUOTE))
    rows = [(a.claim_id, a.theme_id) for a in assignments]
    for row in sorted({r for r in rows if rows.count(r) > 1}):
        refusals.append(Refusal(f"assignment {row[0]}/{row[1]}", Problem.DUPLICATE_ID))
    plain = {c.claim_id for c in claims}
    for a in assignments:
        subject = f"assignment {a.claim_id}/{a.theme_id}"
        if a.claim_id not in plain:
            refusals.append(Refusal(subject, Problem.UNKNOWN_CLAIM))
        if a.theme_id != UNMATCHED and a.theme_id not in themes:
            refusals.append(Refusal(subject, Problem.UNKNOWN_THEME))
    groups: dict[str, list[GoldAssignment]] = {}
    for a in assignments:
        if a.tie_group is not None:
            groups.setdefault(a.tie_group, []).append(a)
    for group, members in sorted(groups.items()):
        if len(members) == 1 or len({a.claim_id for a in members}) > 1:
            refusals.append(Refusal(f"tie_group {group}", Problem.TIE_GROUP))
    for negative in negatives:
        if negative.theme_id is not None and negative.theme_id not in themes:
            subject = f"{prefix}claim {negative.claim_id}"
            refusals.append(Refusal(subject, Problem.UNKNOWN_THEME))
    return refusals


def _pointers(
    quotes: Sequence[GoldQuote], bundle: Bundle, prefix: str
) -> list[Refusal]:
    return [
        Refusal(f"{prefix}quote {quote.quote_id}", reason)
        for quote in quotes
        for reason in check_pointer(
            bundle, SpanPointer(**quote.model_dump(exclude={"quote_id", "origin"}))
        )
    ]


def _counts(counts: DraftCounts, items: Sequence[BaseModel]) -> list[Refusal]:
    tally = {origin: 0 for origin in Origin}
    for item in items:
        tally[item.origin] += 1
    if (counts.accepted, counts.edited, counts.added) != (
        tally[Origin.DRAFTED_ACCEPTED],
        tally[Origin.DRAFTED_EDITED],
        tally[Origin.ANNOTATOR_ADDED],
    ):
        return [Refusal("counts", Problem.COUNTS_MISMATCH)]
    return []


def _wording(record: BaseModel, bundles: Mapping[str, Bundle]) -> list[Refusal]:
    found = shared(
        labelled_strings(record.model_dump(mode="json")),
        ((name, b.document.canonical_text) for name, b in bundles.items()),
    )
    return [
        Refusal(f"{label} ({name})", Problem.SOURCE_WORDING)
        for label, name in sorted(found)
    ]


def _codebook(ref: CodebookRef, codebook: Codebook) -> list[Refusal]:
    if ref != _codebook_ref(codebook):
        return [Refusal("codebook", Problem.WRONG_CODEBOOK)]
    if codebook.status is not CodebookStatus.APPROVED:
        return [Refusal("codebook", Problem.CODEBOOK_NOT_APPROVED)]
    return []


def validate_gold(
    gold: Gold,
    *,
    bundle: Bundle,
    pin: Pin,
    split: SplitManifest,
    codebook: Codebook,
    require_signature: bool = True,
) -> list[Refusal]:
    """Every reason a gold file does not hold over its bundle; empty when it does."""
    refusals = []
    document = bundle.document
    if (gold.event_id, gold.document_id) != (bundle.name, f"{bundle.name}:release"):
        refusals.append(Refusal("event_id", Problem.UNKNOWN_DOCUMENT))
    if gold.doc_id != document.doc_id:
        refusals.append(Refusal("doc_id", RejectionReason.WRONG_DOCUMENT))
    if gold.canonical_hash != document.canonical_hash:
        refusals.append(
            Refusal("canonical_hash", RejectionReason.CANONICAL_HASH_MISMATCH)
        )
    if gold.pin != pin:
        refusals.append(Refusal("pin", Problem.WRONG_PIN))
    if gold.split_hash != split.content_hash:
        refusals.append(Refusal("split_hash", Problem.WRONG_SPLIT))
    try:
        partition = split.partition_of(gold.event_id)
    except KeyError:
        partition = None
    if partition is Partition.EXCLUDED:
        refusals.append(Refusal("partition", Problem.EXCLUDED_EVENT))
    elif gold.partition != partition:
        refusals.append(Refusal("partition", Problem.WRONG_PARTITION))
    refusals += _codebook(gold.codebook, codebook)
    if require_signature and not signed(gold.annotator):
        refusals.append(Refusal("annotator", Problem.UNSIGNED))
    if gold.no_theme != no_theme_of(gold.assignments):
        refusals.append(Refusal("no_theme", Problem.NO_THEME_MISMATCH))
    refusals += _ids(
        gold.quotes,
        gold.claims,
        gold.assignments,
        gold.hard_negatives,
        codebook.theme_ids(),
        "",
    )
    refusals += _pointers(gold.quotes, bundle, "")
    items = [*gold.quotes, *gold.claims, *gold.assignments, *gold.hard_negatives]
    refusals += _counts(gold.counts, items)
    return refusals + _wording(gold, {bundle.name: bundle})


def build_curated(
    drafted: CuratedDraft,
    working: CuratedDraft,
    *,
    bundles: Mapping[str, Bundle],
    pin: Pin,
    codebook: Codebook,
) -> HardNegativeSet | list[Refusal]:
    """The curated hard negatives ``working`` defines over Stage 1's fixtures."""
    origins = _Origins()
    before = {d.fixture_id: d for d in drafted.documents}
    documents, refusals = [], []
    for document in working.documents:
        bundle = bundles.get(document.fixture_id)
        if bundle is None:
            refusals.append(
                Refusal(f"fixture {document.fixture_id}", Problem.UNKNOWN_DOCUMENT)
            )
            continue
        empty = FixtureDraft.model_construct(
            fixture_id=document.fixture_id, quotes=(), hard_negatives=()
        )
        made, found = _items(
            before.get(document.fixture_id, empty),
            document,
            bundle,
            origins,
            f"{document.fixture_id} ",
        )
        refusals += found
        if not found:
            documents.append(
                FixtureNegatives(
                    fixture_id=document.fixture_id,
                    doc_id=bundle.document.doc_id,
                    canonical_hash=bundle.document.canonical_hash,
                    **made,
                )
            )
    kept = {d.fixture_id for d in working.documents}
    for fixture_id, gone in before.items():
        if fixture_id not in kept:
            origins.rejected += len(gone.quotes) + len(gone.hard_negatives)
    if refusals:
        return refusals
    record = HardNegativeSet(
        pin=pin,
        annotator=working.annotator,
        drafting_aid=working.drafting_aid,
        counts=origins.tally(),
        codebook=_codebook_ref(codebook),
        documents=tuple(documents),
    )
    refusals = validate_curated(
        record, bundles=bundles, pin=pin, codebook=codebook, require_signature=False
    )
    return refusals or record


def validate_curated(
    record: HardNegativeSet,
    *,
    bundles: Mapping[str, Bundle],
    pin: Pin,
    codebook: Codebook,
    require_signature: bool = True,
) -> list[Refusal]:
    """Every reason the curated hard negatives do not hold; empty when they do.
    Their wording is checked against every fixture in ``bundles``, as the committed
    guard checks it, not only the fixtures they quote."""
    refusals = []
    if record.pin != pin:
        refusals.append(Refusal("pin", Problem.WRONG_PIN))
    refusals += _codebook(record.codebook, codebook)
    if require_signature and not signed(record.annotator):
        refusals.append(Refusal("annotator", Problem.UNSIGNED))
    kinds = {n.negative_kind for d in record.documents for n in d.hard_negatives}
    if kinds != set(NegativeKind):
        refusals.append(Refusal("hard_negatives", Problem.NEGATIVE_KINDS))
    items: list[BaseModel] = []
    for document in record.documents:
        prefix = f"{document.fixture_id} "
        bundle = bundles.get(document.fixture_id)
        if bundle is None:
            refusals.append(Refusal(prefix.strip(), Problem.UNKNOWN_DOCUMENT))
            continue
        if (document.doc_id, document.canonical_hash) != (
            bundle.document.doc_id,
            bundle.document.canonical_hash,
        ):
            refusals.append(Refusal(f"{prefix}doc_id", RejectionReason.WRONG_DOCUMENT))
            continue
        refusals += _ids(
            document.quotes,
            (),
            (),
            document.hard_negatives,
            codebook.theme_ids(),
            prefix,
        )
        refusals += _pointers(document.quotes, bundle, prefix)
        items += [*document.quotes, *document.hard_negatives]
    refusals += _counts(record.counts, items)
    return refusals + _wording(record, bundles)
```

Create `/tmp/plan9-task8-impl.py`:

```python
"""Plan 9: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "docs/data-dictionary.md": [
        (
            "| `themes` | tuple of `ThemeDraft` | At least one |\n"
            "\n",
            "| `themes` | tuple of `ThemeDraft` | At least one |\n"
            "\n"
            "### `Origin`\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `drafted_accepted` | In the draft, and unchanged in the working copy |\n"
            "| `drafted_edited` | In the draft, and changed in the working copy |\n"
            "| `annotator_added` | Only in the working copy |\n"
            "\n"
            "### `Support`\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `supports` | The claim's quotes support it under the theme |\n"
            "| `does_not_support` | They do not |\n"
            "| `uncertain` | The annotator cannot tell |\n"
            "\n"
            "### `ReleaseLabel`\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `release` | The document is the event's earnings release (R13.1) |\n"
            "| `not_release` | It is not; `true_accession` and `true_exhibit` may name the release |\n"
            "| `ambiguous` | The annotator cannot tell |\n"
            "\n"
            "### `NegativeKind`\n"
            "\n"
            "| Value | Meaning |\n"
            "| --- | --- |\n"
            "| `period` | Confusable by its period: another quarter's result |\n"
            "| `issuer` | Confusable by its issuer: another company's result |\n"
            "| `section` | Confusable by its section: boilerplate or a forward-looking statement that reports no result |\n"
            "\n"
            "### `GoldQuote`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `start` | int ≥ 0 | As `SpanPointer` |\n"
            "| `end` | int > `start` | As `SpanPointer` |\n"
            "| `element_id` | string | As `SpanPointer` |\n"
            "| `quote_sha256` | 64 lowercase hex | As `SpanPointer` |\n"
            "| `context_sha256` | 64 lowercase hex or null | As `SpanPointer` |\n"
            "| `mask_ids` | tuple of string | As `SpanPointer` |\n"
            "| `quote_id` | ID part | Its ID in the record |\n"
            "| `origin` | `Origin` | Where it came from |\n"
            "\n"
            "### `GoldClaim`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `claim_id` | ID part | Its ID in the record |\n"
            "| `quote_ids` | tuple of ID part | The quotes it rests on; at least one |\n"
            "| `claim` | string | The claim, in the user's words |\n"
            "| `origin` | `Origin` | Where it came from |\n"
            "\n"
            "### `GoldAssignment`\n"
            "\n"
            "One row per claim and theme (R9.9).\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `claim_id` | ID part | The claim |\n"
            "| `theme_id` | theme ID | A codebook theme, or `unmatched` |\n"
            "| `support` | `Support` | Whether the claim's quotes support it under the theme |\n"
            "| `tie_group` | ID part or null | Marks rows that are alternatives for one claim (R12.6) |\n"
            "| `origin` | `Origin` | Where it came from |\n"
            "\n"
            "### `HardNegative`\n"
            "\n"
            "A hard-negative claim (D4); its expected support is `does_not_support`.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `claim_id` | ID part | Its ID in the record |\n"
            "| `quote_ids` | tuple of ID part | Its quotes; at least one |\n"
            "| `claim` | string | The claim, in the user's words |\n"
            "| `negative_kind` | `NegativeKind` | What makes it confusable |\n"
            "| `theme_id` | theme ID or null | The theme it would wrongly support |\n"
            "| `origin` | `Origin` | Where it came from |\n"
            "\n"
            "### `ReleaseIdentification`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `label` | `ReleaseLabel` | R13.1's label |\n"
            "| `note` | string | The annotator's reason, in their words |\n"
            "| `true_accession` | accession or null | Only with `not_release`: the release's filing |\n"
            "| `true_exhibit` | string or null | Only with `not_release`: its exhibit |\n"
            "\n"
            "### `DraftCounts`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `accepted` | int ≥ 0 | Drafted items kept unchanged |\n"
            "| `edited` | int ≥ 0 | Drafted items changed |\n"
            "| `rejected` | int ≥ 0 | Drafted items removed |\n"
            "| `added` | int ≥ 0 | Items the annotator added |\n"
            "\n"
            "### `CodebookRef`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `codebook_id` | ID part | The codebook coded against |\n"
            "| `codebook_version` | int ≥ 0 | Its version |\n"
            "| `content_hash` | 64 lowercase hex | Its `content_hash` |\n"
            "\n"
            "### `Gold`\n"
            "\n"
            "`evaluation/<corpus>/pilot-v<N>/gold/<event>.toml`, written once, signed.\n"
            "`<event>` is the event ID with its colon as an underscore, such as\n"
            "`cik-0000051143_2024-12-31`, since Git on Windows cannot check out a path with a colon.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `schema_version` | `1` | Themes record schema version |\n"
            "| `event_id` | ID part | The bundle's event |\n"
            "| `document_id` | ID part | `<event_id>:release` |\n"
            "| `doc_id` | string | Its canonical document |\n"
            "| `canonical_hash` | 64 lowercase hex | That document's `canonical_hash` |\n"
            "| `pin` | `Pin` | The pilot |\n"
            "| `split_hash` | 64 lowercase hex | The split's `content_hash` |\n"
            "| `partition` | `Partition` | The event's partition; never `excluded` |\n"
            "| `codebook` | `CodebookRef` | The approved codebook coded against |\n"
            "| `annotator` | string | The signature; blank until the user signs (GS4) |\n"
            "| `drafting_aid` | `DraftingAid` | The drafting session |\n"
            "| `counts` | `DraftCounts` | The origins, counted against the kept draft (GS5) |\n"
            "| `no_theme` | bool | True exactly when no row pairs a claim with a codebook theme under `supports` |\n"
            "| `release_identification` | `ReleaseIdentification` | Whether the document is the release |\n"
            "| `quotes` | tuple of `GoldQuote` | Its quotes |\n"
            "| `claims` | tuple of `GoldClaim` | Its claims |\n"
            "| `assignments` | tuple of `GoldAssignment` | Its assignments |\n"
            "| `hard_negatives` | tuple of `HardNegative` | Its hard-negative claims |\n"
            "\n"
            "### `FixtureNegatives`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `fixture_id` | ID part | A Stage 1 fixture |\n"
            "| `doc_id` | string | Its canonical document |\n"
            "| `canonical_hash` | 64 lowercase hex | That document's `canonical_hash` |\n"
            "| `quotes` | tuple of `GoldQuote` | The quotes; at least one |\n"
            "| `hard_negatives` | tuple of `HardNegative` | The hard-negative claims; at least one |\n"
            "\n"
            "### `HardNegativeSet`\n"
            "\n"
            "`tests/fixtures/gold/hard-negatives.toml`, written once, signed: outside the pilot,\n"
            "in no partition (GS10), though it carries the pin, as every Stage 6 record does.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `schema_version` | `1` | Themes record schema version |\n"
            "| `pin` | `Pin` | The pilot |\n"
            "| `annotator` | string | The signature |\n"
            "| `drafting_aid` | `DraftingAid` | The drafting session |\n"
            "| `counts` | `DraftCounts` | The origins, over every fixture |\n"
            "| `codebook` | `CodebookRef` | The approved codebook |\n"
            "| `documents` | tuple of `FixtureNegatives` | At least one; with every `NegativeKind` among them |\n"
            "\n"
            "### `QuoteDraft`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `quote_id` | ID part | Its ID |\n"
            "| `text` | string | The exact text |\n"
            "| `prefix` | string | Text just before it, when it repeats |\n"
            "| `suffix` | string | Text just after it, when it repeats |\n"
            "\n"
            "### `ClaimDraft`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `claim_id` | ID part | As `GoldClaim` |\n"
            "| `quote_ids` | tuple of ID part | As `GoldClaim` |\n"
            "| `claim` | string | As `GoldClaim` |\n"
            "\n"
            "### `AssignmentDraft`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `claim_id` | ID part | As `GoldAssignment` |\n"
            "| `theme_id` | theme ID | As `GoldAssignment` |\n"
            "| `support` | `Support` | As `GoldAssignment` |\n"
            "| `tie_group` | ID part or null | As `GoldAssignment` |\n"
            "\n"
            "### `HardNegativeDraft`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `claim_id` | ID part | As `HardNegative` |\n"
            "| `quote_ids` | tuple of ID part | As `HardNegative` |\n"
            "| `claim` | string | As `HardNegative` |\n"
            "| `negative_kind` | `NegativeKind` | As `HardNegative` |\n"
            "| `theme_id` | theme ID or null | As `HardNegative` |\n"
            "\n"
            "### `GoldDraft`\n"
            "\n"
            "`data/runs/gold/drafts/<event>.draft.toml` and its working copy; never committed.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `event_id` | ID part | The bundle's event |\n"
            "| `annotator` | string | Blank in the draft; the user signs the working copy |\n"
            "| `drafting_aid` | `DraftingAid` | The drafting session |\n"
            "| `no_theme` | bool | As `Gold` |\n"
            "| `release_identification` | `ReleaseIdentification` | As `Gold` |\n"
            "| `quotes` | tuple of `QuoteDraft` | Quotes, by text |\n"
            "| `claims` | tuple of `ClaimDraft` | Claims |\n"
            "| `assignments` | tuple of `AssignmentDraft` | Assignments |\n"
            "| `hard_negatives` | tuple of `HardNegativeDraft` | Hard-negative claims |\n"
            "\n"
            "### `FixtureDraft`\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `fixture_id` | ID part | A Stage 1 fixture |\n"
            "| `quotes` | tuple of `QuoteDraft` | At least one |\n"
            "| `hard_negatives` | tuple of `HardNegativeDraft` | At least one |\n"
            "\n"
            "### `CuratedDraft`\n"
            "\n"
            "`data/runs/gold/drafts/hard-negatives.draft.toml` and its working copy.\n"
            "\n"
            "| Field | Type | Meaning |\n"
            "| --- | --- | --- |\n"
            "| `annotator` | string | Blank in the draft; the user signs the working copy |\n"
            "| `drafting_aid` | `DraftingAid` | The drafting session |\n"
            "| `documents` | tuple of `FixtureDraft` | At least one |\n"
            "\n",
        ),
    ],
    "specs/pilot-codebook-split-and-gold-set-protocol.md": [
        (
            "- `no_theme`: true exactly when no assignment names a codebook theme. The validator\n"
            "  checks it against the assignments, so a bundle with no theme is affirmed by the\n"
            "  user, never inferred from an empty file.\n",
            "- `no_theme`: true exactly when no assignment pairs a claim with a codebook theme\n"
            "  under `supports` (amended by plan 9, P9-4). The validator checks it against the\n"
            "  assignments, so a bundle with no theme is affirmed by the user, never inferred\n"
            "  from an empty file.\n",
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

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/gold.py
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/annotation.py
python3 /tmp/plan9-extract.py /tmp/plan9-task8-impl.py && python3 /tmp/plan9-task8-impl.py
```

Expected:

```text
extracted packages/earnings-themes/src/earnings_themes/gold.py: 219 lines
extracted packages/earnings-themes/src/earnings_themes/annotation.py: 499 lines
extracted /tmp/plan9-task8-impl.py: 266 lines
edited docs/data-dictionary.md: 1 replacement(s)
edited specs/pilot-codebook-split-and-gold-set-protocol.md: 1 replacement(s)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_gold.py tests/contracts/test_data_dictionary.py -q`

Expected: `173 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/src/earnings_themes/gold.py packages/earnings-themes/tests/test_gold.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1692 passed, 1 skipped, 24 deselected`; `All checks passed!` and `287 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add docs/data-dictionary.md packages/earnings-themes/src/earnings_themes/annotation.py packages/earnings-themes/src/earnings_themes/gold.py packages/earnings-themes/tests/test_gold.py specs/pilot-codebook-split-and-gold-set-protocol.md tests/contracts/test_data_dictionary.py
git commit -m "feat(themes): the gold contract, its anchor, and its validator (GS4, GS5, P9-4)"
```

---

### Task 9: The views, and the import boundary

S §Anchoring and validation (View), GS11, GS13, and R14.1. `render_text` is one
document's text for a drafting session; `render_view` marks each quote in place and
lists the items, for the user's verification and omission pass. Both are written
only under `data/runs/gold/`. The import test now imports every `earnings_themes`
module, and refuses the model SDKs and `httpx` besides ingestion, the application,
and the browsers.

**Files:**

- Create: `packages/earnings-themes/src/earnings_themes/view.py`.
- Test: create `packages/earnings-themes/tests/test_view.py`; replace
  `packages/earnings-themes/tests/test_import_boundaries.py`.

**Interfaces:**

- Consumes: `Bundle`, `Gold`, `GoldQuote`, `HardNegative`, and `FixtureNegatives`.
- Produces: `render_text(bundle) -> str`; `marked(text, quotes) -> str`, each quote
  marked `[[q1>>` … `<<q1]]`; `render_view(bundle, gold) -> str`; and
  `render_curated_view(bundle, document) -> str`.

- [x] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/test_view.py`:

``````python
"""Local views (the Stage 6 spec, §Anchoring and validation): the drafter's text
alone, and the verification view with every quote marked in place."""

from earnings_themes.anchoring import SpanPointer, anchor
from earnings_themes.gold import GoldQuote, Origin
from earnings_themes.synthetic import TEXT
from earnings_themes.view import marked, render_text


def quote(synthetic, quote_id: str, text: str, **context) -> GoldQuote:
    pointer = anchor(synthetic.bundle, text, **context)
    assert isinstance(pointer, SpanPointer)
    return GoldQuote(
        **pointer.model_dump(), quote_id=quote_id, origin=Origin.DRAFTED_ACCEPTED
    )


def test_the_text_view_holds_the_text_in_a_fence(synthetic) -> None:
    view = render_text(synthetic.bundle)
    assert view.startswith(f"# {synthetic.bundle.name}\n")
    assert f"```text\n{TEXT.rstrip()}\n```\n" in view


def test_a_fence_is_longer_than_any_backticks_in_the_text(synthetic) -> None:
    bundle = synthetic.bundle
    document = bundle.document.model_copy(update={"canonical_text": "Code ```` here"})
    view = render_text(type(bundle)(bundle.name, document, (), ()))
    assert "`````text\nCode ```` here\n`````" in view


def test_each_quote_is_marked_in_place_and_nested_marks_close_inside_out(
    synthetic,
) -> None:
    outer = quote(synthetic, "q1", "Revenue grew in every region. Margins held steady.")
    inner = quote(synthetic, "q2", "Margins held steady.")
    text = marked(TEXT, (inner, outer))
    assert (
        "[[q1>>Revenue grew in every region. [[q2>>Margins held steady.<<q2]]<<q1]]"
        in text
    )
    assert (
        text.replace("[[q1>>", "")
        .replace("[[q2>>", "")
        .replace("<<q2]]", "")
        .replace("<<q1]]", "")
        == TEXT
    )
``````

Replace `packages/earnings-themes/tests/test_import_boundaries.py` with:

```python
"""earnings-themes imports neither earnings-ingestion nor the application, no
browser, and no model SDK or HTTP client (A §173; browser-rendering spec, Stage 2
verification; the Stage 6 spec, R14.1: drafting stays outside the code)."""

import json
import pkgutil
import subprocess
import sys

import earnings_themes

FORBIDDEN = {
    "earnings_ingestion",
    "earnings_pipeline",
    "selenium",
    "playwright",
    "pyppeteer",
    "pydantic_ai",
    "openai",
    "anthropic",
    "typesafe_sdk",
    "langchain_typesafe",
    "httpx",
}
MODULES = [
    "earnings_themes",
    *(
        f"earnings_themes.{module.name}"
        for module in pkgutil.iter_modules(earnings_themes.__path__)
    ),
]


def modules_loaded_by(modules: list[str]) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing ``modules``."""
    code = (
        f"import json, sys, {', '.join(modules)};"
        " print(json.dumps(sorted(sys.modules)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return {name.partition(".")[0] for name in json.loads(result.stdout)}


def test_every_module_is_imported() -> None:
    assert "earnings_themes.annotation" in MODULES
    assert len(MODULES) >= 12


def test_importing_earnings_themes_loads_nothing_forbidden() -> None:
    assert modules_loaded_by(MODULES) & FORBIDDEN == set()
```

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/tests/test_view.py
python3 /tmp/plan9-extract.py packages/earnings-themes/tests/test_import_boundaries.py
```

Expected:

```text
extracted packages/earnings-themes/tests/test_view.py: 47 lines
extracted packages/earnings-themes/tests/test_import_boundaries.py: 52 lines
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_view.py packages/earnings-themes/tests/test_import_boundaries.py -q`

Expected: FAIL, `1 error`, with:

```text
ModuleNotFoundError: No module named 'earnings_themes.view'
ERROR packages/earnings-themes/tests/test_view.py
```

- [x] **Step 3: Write the views**

Create `packages/earnings-themes/src/earnings_themes/view.py`:

```python
"""Local views, for drafting and for verification (the Stage 6 spec, §Anchoring and
validation; GS11, GS13).

A view holds a release's text, so the application writes it only under
``data/runs/gold/``, which is never committed, and no command prints it.

- ``render_text`` is one bundle's text alone: the only text a drafting session is
  given (GS13).
- ``render_view`` marks each quote in the text as ``[[q1>>`` ... ``<<q1]]`` and
  lists the claims, their themes and support, the hard negatives, and the
  release-identification label: the user verifies, and does the omission pass,
  against it.
"""

import re

from earnings_themes.anchoring import Bundle
from earnings_themes.gold import FixtureNegatives, Gold, GoldQuote, HardNegative

_TICKS = re.compile(r"`+")


def _fenced(text: str) -> list[str]:
    longest = max((len(run) for run in _TICKS.findall(text)), default=0)
    fence = "`" * max(3, longest + 1)
    return [f"{fence}text", text.rstrip("\n"), fence]


def _head(bundle: Bundle) -> list[str]:
    return [
        f"# {bundle.name}",
        "",
        (
            f"`{bundle.document.doc_id}`. A local view of a release's text: never"
            " commit it, and never paste from it into a committed file."
        ),
        "",
    ]


def render_text(bundle: Bundle) -> str:
    """The bundle's canonical text, for a drafting session."""
    return "\n".join([*_head(bundle), *_fenced(bundle.document.canonical_text)]) + "\n"


def marked(text: str, quotes: tuple[GoldQuote, ...]) -> str:
    """``text`` with each quote's start and end marked by its ID."""
    marks = []
    for quote in quotes:
        marks.append((quote.start, 1, -quote.end, f"[[{quote.quote_id}>>"))
        marks.append((quote.end, 0, -quote.start, f"<<{quote.quote_id}]]"))
    pieces, position = [], 0
    for at, _, _, mark in sorted(marks):
        pieces += [text[position:at], mark]
        position = at
    return "".join([*pieces, text[position:]])


def _negatives(negatives: tuple[HardNegative, ...]) -> list[str]:
    lines = ["", "## Hard negatives", ""]
    if not negatives:
        lines.append("(none)")
    for n in negatives:
        wrongly = f"; would wrongly support {n.theme_id}" if n.theme_id else ""
        quotes = ", ".join(n.quote_ids)
        lines.append(
            f"- {n.claim_id} ({n.negative_kind}{wrongly}; {n.origin}), quotes"
            f" {quotes}: {n.claim}"
        )
    return lines


def _quotes(quotes: tuple[GoldQuote, ...]) -> list[str]:
    lines = ["", "## Quotes", ""]
    for q in quotes:
        masks = f"; masks {', '.join(q.mask_ids)}" if q.mask_ids else ""
        lines.append(f"- {q.quote_id} ({q.origin}) in {q.element_id}{masks}")
    return lines


def render_view(bundle: Bundle, gold: Gold) -> str:
    """The bundle's text with its gold marked, for verification."""
    release = gold.release_identification
    lines = [
        *_head(bundle),
        (
            f"Partition {gold.partition}; codebook {gold.codebook.codebook_id}"
            f" v{gold.codebook.codebook_version}; signed: {gold.annotator or '(no)'};"
            f" no_theme: {str(gold.no_theme).lower()}."
        ),
        "",
        f"Release identification: {release.label}. {release.note}",
        "",
        *_fenced(marked(bundle.document.canonical_text, gold.quotes)),
        "",
        "## Claims",
        "",
    ]
    for claim in gold.claims:
        lines.append(
            f"- {claim.claim_id} ({claim.origin}), quotes"
            f" {', '.join(claim.quote_ids)}: {claim.claim}"
        )
        for a in gold.assignments:
            if a.claim_id == claim.claim_id:
                tie = f", tie {a.tie_group}" if a.tie_group else ""
                lines.append(f"  - {a.theme_id}: {a.support}{tie} ({a.origin})")
    lines += _negatives(gold.hard_negatives) + _quotes(gold.quotes)
    return "\n".join(lines) + "\n"


def render_curated_view(bundle: Bundle, document: FixtureNegatives) -> str:
    """One Stage 1 fixture's text with its curated hard negatives marked."""
    lines = [
        *_head(bundle),
        *_fenced(marked(bundle.document.canonical_text, document.quotes)),
        *_negatives(document.hard_negatives),
        *_quotes(document.quotes),
    ]
    return "\n".join(lines) + "\n"
```

Write them:

```bash
python3 /tmp/plan9-extract.py packages/earnings-themes/src/earnings_themes/view.py
```

Expected:

```text
extracted packages/earnings-themes/src/earnings_themes/view.py: 120 lines
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_view.py packages/earnings-themes/tests/test_import_boundaries.py -q`

Expected: `5 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py packages/earnings-themes/src/earnings_themes/view.py packages/earnings-themes/tests/test_import_boundaries.py packages/earnings-themes/tests/test_view.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1696 passed, 1 skipped, 24 deselected`; `All checks passed!` and `289 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-themes/src/earnings_themes/view.py packages/earnings-themes/tests/test_import_boundaries.py packages/earnings-themes/tests/test_view.py
git commit -m "feat(themes): local views for drafting and verification (GS11, GS13)"
```

---

### Task 10: The pin, and pilot split and coverage

S §The pin, §The split, §The coverage report, §Drafting and tools, GS2, GS13, GS14,
and P9-8. `stage6.py` is what every Stage 6 command shares: `--repo` and the pin's
three paths and hash, the pinned pilot loaded by path and checked, the local bundles
loaded by `doc_id`, write-once records, and output that is IDs, counts, reasons,
paths, and hashes. `pilot split` and `pilot coverage` write their records once.
Tasks 11 and 12 use the bundle loaders, and `wording_texts` and `wording_refusals`,
which check a record against every text the committed wording guard reads before
it is written (P9-21).

The test module replays the synthetic acquisition offline once, and its canary,
`quiet`, fails any command that prints a 20-character window of a canonical text
it could read.

**Files:**

- Create: `apps/earnings-pipeline/src/earnings_pipeline/stage6.py` and
  `pilot_cli.py`.
- Modify, by exact replacement: `apps/earnings-pipeline/src/earnings_pipeline/cli.py`.
- Test: create `apps/earnings-pipeline/tests/test_stage6_cli.py`.

**Interfaces:**

- Consumes: Tasks 1 to 9; `load_manifest`, `load_pilot`, `load_event_manifest`,
  `manifest_path`, `read_runs`, `write_new`, `serialize`, `UNIVERSE_DIR`,
  `CORPUS_DIR`, and `earnings_pipeline.paths.shown`.
- Produces:
  - `PILOT_V1_HASH`, `UNIVERSE_V1`, `PILOT_V1`, `EVENT_RUNS`, `GOLD_RUNS`,
    `CODEBOOK_FILE`, `FIXTURE_MANIFEST`, `CANONICAL_FIXTURES`, and `HARD_NEGATIVES`;
  - `Layout(repo, universe, pilot, pilot_hash)` with `shown(path)`, `drafts`, and
    `gold_runs`; `Pinned(pilot, events, pin, coverage_pin, evaluation)` with
    `split_path`, `coverage_path`, and `gold_dir`;
  - `file_stem(event_id) -> str` (P9-3); `fail(message)`; `guarded(command)`;
    `refuse(refusals, verb="written")`; `record_error(error)`; `options(...)`, the
    groups' callback; `load_pinned(layout) -> Pinned`; `transitions(layout)`;
    `documents(layout, pinned) -> dict[str, str]`; `load_bundle(layout, doc_ids,
    event_id) -> Bundle`; `load_fixture(layout, fixture_id) -> Bundle`;
    `fixture_event_ids(layout, events) -> frozenset[str]`; `wording_texts(layout,
    pinned) -> dict[str, str]`, each parsed pilot document's text by event ID and
    each Stage 1 fixture's by fixture ID; `wording_refusals(record, texts) ->
    list[Refusal]`; `write_once(path, data, layout) -> bool`; and `replace(path,
    text)`;
  - `earnings-pipeline pilot split` and `earnings-pipeline pilot coverage`.

- [x] **Step 1: Write the failing tests**

Create `apps/earnings-pipeline/tests/test_stage6_cli.py`:

```python
"""Stage 6's commands over the synthetic pilot (plan 9): the split and the coverage
report freeze once, over the pin; every refusal names its item and reason; and no
command prints a document's text (GS13) or changes a frozen record (P-C7).

The synthetic acquisition is replayed offline once, into ``data/runs/events/``, as
Stage 5's replay test does; its documents are the synthetic layer's invented text.
"""

import shutil
from pathlib import Path

import pytest
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.acquire import acquire
from earnings_ingestion.events.coverage import load_coverage
from earnings_ingestion.events.fixture import (
    ACQUIRED_AT,
    ACQUISITION_RUN,
    COHORT_MANIFEST,
    FIXTURE_DIR,
)
from earnings_ingestion.events.freeze import load_event_manifest
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.events.records import AcquisitionOverridesFile
from earnings_ingestion.events.state_table import read_runs, write_run
from earnings_ingestion.events.states import DocumentState
from earnings_ingestion.fetch.responses import UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_pipeline import cli
from earnings_pipeline.stage6 import (
    Layout,
    documents,
    load_pinned,
    wording_refusals,
    wording_texts,
)
from earnings_themes.gold import ReleaseIdentification, ReleaseLabel
from earnings_themes.split import load_split
from earnings_themes.wording import WIDTH, masked
from typer.testing import CliRunner

RUNNER = CliRunner()
REPO = Path(__file__).resolve().parents[3]
PILOT_HASH = "71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c"
EVENT_RUNS = Path("data") / "runs" / "events"
EVALUATION = Path("evaluation") / "djia-synthetic" / "pilot-v1"
CANONICAL = Path("tests") / "fixtures" / "canonical"
RELEASES = Path("tests") / "fixtures" / "releases" / "manifest.toml"
EXCLUDED = "cik-0009990001:2025-08-31"
WINDOW = 20


@pytest.fixture(scope="module")
def acquired(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The synthetic acquisition's run file and canonical documents, replayed
    offline: the one exhibit SEC never served stays unavailable."""
    root = tmp_path_factory.mktemp("acquired")
    store = tmp_path_factory.mktemp("store")
    shutil.copytree(REPO / FIXTURE_DIR / "raw", store / "raw")
    universe = load_manifest(REPO / COHORT_MANIFEST)

    def sec(url: str, types) -> None:
        raise UnexpectedResponse(f"HTTP 404 for {url}")

    acquire(
        load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json"),
        load_pilot(REPO / FIXTURE_DIR / "pilot-v1.json", universe),
        universe,
        ArtifactStore(store / "raw", store),
        sec,
        overrides=AcquisitionOverridesFile(schema_version=1),
        states_dir=root / EVENT_RUNS / "states",
        canonical_dir=root / EVENT_RUNS / "canonical",
        run_id=ACQUISITION_RUN,
        now=lambda: ACQUIRED_AT,
    )
    return root


@pytest.fixture
def repo(tmp_path: Path, acquired: Path) -> Path:
    """The synthetic cohort and pilot, Stage 1's fixtures, and the acquisition."""
    ignore = shutil.ignore_patterns("raw")
    for directory in (COHORT_MANIFEST.parent, FIXTURE_DIR, CANONICAL):
        shutil.copytree(REPO / directory, tmp_path / directory, ignore=ignore)
    (tmp_path / RELEASES).parent.mkdir(parents=True)
    shutil.copy2(REPO / RELEASES, tmp_path / RELEASES)
    shutil.copytree(acquired / "data", tmp_path / "data")
    return tmp_path


def texts(repo: Path) -> list[str]:
    """Every canonical text a command could read: the pilot's and Stage 1's."""
    paths = [
        *(repo / EVENT_RUNS / "canonical").glob("*.json"),
        *(repo / CANONICAL).glob("*.json"),
    ]
    return [
        from_fixture_json(path.read_text(encoding="utf-8")).document.canonical_text
        for path in paths
    ]


def quiet(repo: Path, output: str) -> None:
    """GS13: no 20-character window of any canonical text is printed. The
    assertion names a count, never the window."""
    windows = {
        text[i : i + WINDOW]
        for text in texts(repo)
        for i in range(len(text) - WINDOW + 1)
    }
    leaked = sum(
        1 for i in range(len(output) - WINDOW + 1) if output[i : i + WINDOW] in windows
    )
    assert leaked == 0, f"{leaked} printed windows of document text"


def run(repo: Path, group: str, *args: str):
    layout = [
        "--repo",
        str(repo),
        "--universe",
        str(COHORT_MANIFEST),
        "--pilot",
        str(FIXTURE_DIR / "pilot-v1.json"),
        "--pilot-hash",
        PILOT_HASH,
    ]
    result = RUNNER.invoke(cli.app, [group, *layout, *args])
    quiet(repo, result.output)
    return result


def lines(result) -> list[str]:
    return result.output.splitlines()


def pilot_bytes(repo: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in (repo / FIXTURE_DIR).glob("*.json")}


def guarded_texts(repo: Path) -> dict[str, str]:
    """What the wording guard reads over the synthetic pilot, by text ID."""
    layout = Layout(repo, COHORT_MANIFEST, FIXTURE_DIR / "pilot-v1.json", PILOT_HASH)
    return wording_texts(layout, load_pinned(layout))


def first_fixture(repo: Path) -> str:
    return min(path.stem for path in (repo / CANONICAL).glob("*.json"))


def unique_window(found: dict[str, str], name: str) -> str:
    """One window of the named text, with no date and four spaces or more, that no
    other text holds once dates are masked, as the guard compares them; taken when
    the test runs, never typed here."""
    others = [masked(text) for key, text in found.items() if key != name]
    text = masked(found[name])
    for start in range(len(text) - WIDTH + 1):
        window = text[start : start + WIDTH]
        if "\n" in window or "\0" in window or window.count(" ") < 4:
            continue
        if not any(window in other for other in others):
            return window
    raise AssertionError(f"{name} has no window of its own")


def test_split_freezes_once_and_prints_only_ids_and_counts(repo) -> None:
    result = run(repo, "pilot", "split")
    assert result.exit_code == 0, result.output
    assert lines(result)[:5] == [
        f"pilot djia-synthetic-pilot v1  {PILOT_HASH}",
        "train  13",
        "dev  0",
        "test  0",
        "excluded  14",
    ]
    assert f"excluded  {EXCLUDED}  issuer_in_earlier_partition" in lines(result)
    assert lines(result)[-2] == "froze split v1 by issuer-time/1"
    split = load_split(repo / EVALUATION / "split-v1.json")
    assert lines(result)[-1] == (
        f"evaluation/djia-synthetic/pilot-v1/split-v1.json  {split.content_hash}"
    )
    again = run(repo, "pilot", "split")
    assert lines(again)[-2] == "unchanged: split v1 by issuer-time/1"


def test_a_changed_split_is_refused_and_never_edited(repo) -> None:
    path = repo / EVALUATION / "split-v1.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}\n", encoding="utf-8")
    result = run(repo, "pilot", "split")
    assert result.exit_code == 1
    assert lines(result)[-1] == (
        "Refused: evaluation/djia-synthetic/pilot-v1/split-v1.json holds other"
        " content; a changed record is a new version, never an edit"
    )
    assert path.read_text(encoding="utf-8") == "{}\n"


def test_another_pilot_hash_is_refused(repo) -> None:
    result = RUNNER.invoke(
        cli.app,
        [
            "pilot",
            "--repo",
            str(repo),
            "--universe",
            str(COHORT_MANIFEST),
            "--pilot",
            str(FIXTURE_DIR / "pilot-v1.json"),
            "--pilot-hash",
            "0" * 64,
            "split",
        ],
    )
    assert result.exit_code == 1
    assert lines(result) == [
        (
            f"Refused: tests/fixtures/events/pilot-v1.json holds pilot {PILOT_HASH},"
            f" not the pin's {'0' * 64}"
        )
    ]
    assert not (repo / EVALUATION).exists()


def test_a_universe_that_is_not_the_pin_s_is_refused(repo) -> None:
    other = Path("config") / "universe" / "djia" / "manifests"
    other = other / "djia-2024q3-2026q2-v1.json"
    (repo / other).parent.mkdir(parents=True)
    shutil.copy2(REPO / other, repo / other)
    result = RUNNER.invoke(
        cli.app,
        [
            "pilot",
            "--repo",
            str(repo),
            "--universe",
            str(other),
            "--pilot",
            str(FIXTURE_DIR / "pilot-v1.json"),
            "--pilot-hash",
            PILOT_HASH,
            "split",
        ],
    )
    assert result.exit_code == 1
    assert lines(result) == [
        (
            "Refused: the universe's operative hash is not the one the pilot and its"
            " event manifest read"
        )
    ]


def test_coverage_counts_each_state_and_rereads_only_its_runs(repo) -> None:
    before = pilot_bytes(repo)
    result = run(repo, "pilot", "coverage")
    assert result.exit_code == 0, result.output
    assert lines(result)[1:7] == [
        "parsed  24",
        "failed  1",
        "unavailable  2",
        "gap  restricted  (D4: never repaired by reselecting)",
        f"runs  {ACQUISITION_RUN}",
        "froze coverage v1: 27 documents",
    ]
    report = load_coverage(repo / EVALUATION / "coverage-v1.json")
    states = repo / EVENT_RUNS / "states"
    parsed = next(t for t in read_runs(states) if t.to_state is DocumentState.PARSED)
    later = parsed.model_copy(
        update={
            "run_id": "stage-7",
            "sequence": 0,
            "recorded_at": ACQUIRED_AT.replace(hour=14),
            "from_state": DocumentState.PARSED,
            "to_state": DocumentState.PARTIAL,
            "attempts": (),
        }
    )
    write_run(states, [later])
    again = run(repo, "pilot", "coverage")
    assert again.exit_code == 0, again.output
    assert lines(again)[-2] == "unchanged: coverage v1: 27 documents"
    assert load_coverage(repo / EVALUATION / "coverage-v1.json") == report
    assert pilot_bytes(repo) == before


def test_a_record_is_checked_against_every_text_the_wording_guard_reads(
    repo,
) -> None:
    """GS3: before a command writes a record, it checks the record's strings against
    each parsed pilot document and each Stage 1 fixture, as the committed guard
    does; a copy is named by its field and the text's ID, never quoted."""
    layout = Layout(repo, COHORT_MANIFEST, FIXTURE_DIR / "pilot-v1.json", PILOT_HASH)
    pinned = load_pinned(layout)
    found = wording_texts(layout, pinned)
    fixture_ids = [path.stem for path in sorted((repo / CANONICAL).glob("*.json"))]
    assert sorted(found) == sorted([*documents(layout, pinned), *fixture_ids])
    last = fixture_ids[-1]
    copied = unique_window(found, last)
    record = ReleaseIdentification(label=ReleaseLabel.RELEASE, note=f"Ours: {copied}")
    refusals = [str(refusal) for refusal in wording_refusals(record, found)]
    assert refusals == [f"note ({last}): source_wording"]
```

Write them:

```bash
python3 /tmp/plan9-extract.py apps/earnings-pipeline/tests/test_stage6_cli.py
```

Expected:

```text
extracted apps/earnings-pipeline/tests/test_stage6_cli.py: 304 lines
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q`

Expected: FAIL, `1 error`, with:

```text
ModuleNotFoundError: No module named 'earnings_pipeline.stage6'
ERROR apps/earnings-pipeline/tests/test_stage6_cli.py
```

- [x] **Step 3: Write the shared layer and the pilot commands**

Create `apps/earnings-pipeline/src/earnings_pipeline/stage6.py`:

```python
"""What Stage 6's commands share: the pin, the paths, and loading (the Stage 6
spec, §The pin and §Drafting and tools; GS2, GS13, GS14; plan 9).

- **The pin.** Every command loads pilot v1 and universe v1 by path, never the
  current version, and refuses a pilot whose content hash is not the pin's.
  ``load_pilot`` rechecks the chain, the universe's operative hash included, and
  selects the pilot again (P8-3).
- **Where things are.** Paths are relative to ``--repo``, and a file named for an
  event takes ``file_stem(event_id)``, its colon as an underscore. Committed:
  ``evaluation/<corpus>/pilot-v<N>/`` holds the split, the coverage report, the
  gold, and the briefs; ``codebooks/djia-pilot/`` codebook v0; and
  ``tests/fixtures/gold/`` the curated hard negatives. Local only:
  ``data/runs/events/`` holds the states and canonical documents, and
  ``data/runs/gold/`` the drafts, anchored files, views, and texts.
- **Before a record is written.** A command checks it against every text the
  committed wording guard reads, each parsed pilot document and each Stage 1
  fixture, so no record it writes fails the guard later (GS3).
- **What they print.** IDs, counts, reasons, paths, and hashes, never a document's
  text. A refusal names its item and reason; a file that does not load is named,
  never quoted; and an unforeseen error is named by its type alone (``guarded``).
  Text is written only to views and texts under ``data/runs/gold/``, which the user
  opens (GS13).
"""

import functools
import os
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, NoReturn

import tomllib
import typer
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_ingestion.cohort.config import UNIVERSE_DIR
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.build import CORPUS_DIR
from earnings_ingestion.events.coverage import PilotPin, parsed_documents, pilot_pin
from earnings_ingestion.events.freeze import load_event_manifest, manifest_path
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.events.records import EventManifest, PilotManifest
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import StateTransition
from earnings_ingestion.fetch.store import write_new
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import CODEBOOK_ID, CODEBOOK_VERSION
from earnings_themes.problems import Problem, Refusal
from earnings_themes.records import Pin, RecordError
from earnings_themes.wording import labelled_strings, shared
from pydantic import BaseModel

from earnings_pipeline.paths import shown

PILOT_V1_HASH = "3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926"
"""GS2: the pin, pilot v1's content hash."""
UNIVERSE_V1 = UNIVERSE_DIR / "manifests" / "djia-2024q3-2026q2-v1.json"
PILOT_V1 = CORPUS_DIR / "pilot-v1.json"
EVENT_RUNS = Path("data") / "runs" / "events"
GOLD_RUNS = Path("data") / "runs" / "gold"
CODEBOOK_FILE = Path("codebooks") / CODEBOOK_ID / f"codebook-v{CODEBOOK_VERSION}.toml"
FIXTURE_MANIFEST = Path("tests") / "fixtures" / "releases" / "manifest.toml"
CANONICAL_FIXTURES = Path("tests") / "fixtures" / "canonical"
HARD_NEGATIVES = Path("tests") / "fixtures" / "gold" / "hard-negatives.toml"


@dataclass(frozen=True)
class Layout:
    repo: Path
    universe: Path
    pilot: Path
    pilot_hash: str

    def shown(self, path: Path) -> str:
        return shown(path, self.repo)

    @property
    def drafts(self) -> Path:
        return self.repo / GOLD_RUNS / "drafts"

    @property
    def gold_runs(self) -> Path:
        return self.repo / GOLD_RUNS


@dataclass(frozen=True)
class Pinned:
    """Pilot v1 with its chain, and where its evaluation records live."""

    pilot: PilotManifest
    events: EventManifest
    pin: Pin
    coverage_pin: PilotPin
    evaluation: Path

    @property
    def split_path(self) -> Path:
        return self.evaluation / "split-v1.json"

    @property
    def coverage_path(self) -> Path:
        return self.evaluation / "coverage-v1.json"

    @property
    def gold_dir(self) -> Path:
        return self.evaluation / "gold"


def file_stem(event_id: str) -> str:
    """An event's Stage 6 file name: its ID with the colon as an underscore, since
    Git on Windows cannot check out a path with a colon (P9-3). The ID inside each
    file is unchanged."""
    return event_id.replace(":", "_")


def fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(1)


def guarded[**P](command: Callable[P, None]) -> Callable[P, None]:
    """``command``, with an unforeseen error named by its type alone: a message,
    such as a validation error's, may quote a document (GS13)."""

    @functools.wraps(command)
    def run(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            command(*args, **kwargs)
        except typer.Exit:
            raise
        except Exception as error:  # noqa: BLE001 - withheld by design (GS13)
            fail(
                f"Refused: an unforeseen {type(error).__name__}; its message is"
                " withheld, since it may quote a document (GS13)"
            )

    return run


def refuse(refusals: list[Refusal], verb: str = "written") -> NoReturn:
    """Print each refusal by item and reason, and stop with nothing written."""
    for refusal in refusals:
        typer.echo(f"refused: {refusal}", err=True)
    fail(f"Refused: {len(refusals)} problem(s); nothing {verb}")


def record_error(error: RecordError) -> NoReturn:
    for problem in error.problems:
        typer.echo(f"problem: {error.name}: {problem}", err=True)
    fail(f"Refused: {error.name} does not read as its record")


def options(
    context: typer.Context,
    repo: Annotated[Path, typer.Option(help="The repository root.")] = Path(),
    universe: Annotated[
        Path, typer.Option(help="The pinned universe, by path.")
    ] = UNIVERSE_V1,
    pilot: Annotated[Path, typer.Option(help="The pinned pilot, by path.")] = PILOT_V1,
    pilot_hash: Annotated[
        str, typer.Option(help="The pin: the pilot's content hash.")
    ] = PILOT_V1_HASH,
) -> None:
    """Paths are relative to --repo; the defaults are GS2's pin, pilot v1."""
    context.obj = Layout(repo.resolve(), universe, pilot, pilot_hash)


def load_pinned(layout: Layout) -> Pinned:
    """The pinned pilot, with its chain checked, or a refusal."""
    path = layout.repo / layout.pilot
    try:
        universe = load_manifest(layout.repo / layout.universe)
        pilot = load_pilot(path, universe)
        version = pilot.definition.event_manifest_version
        events = load_event_manifest(manifest_path(path.parent, version))
        coverage_pin = pilot_pin(pilot, events, universe)
    except (OSError, ValueError) as error:
        fail(f"Refused: {error}")
    if pilot.definition.content_hash != layout.pilot_hash:
        fail(
            f"Refused: {layout.shown(path)} holds pilot"
            f" {pilot.definition.content_hash}, not the pin's {layout.pilot_hash}"
        )
    definition = pilot.definition
    evaluation = (
        layout.repo
        / "evaluation"
        / events.definition.corpus_id
        / f"pilot-v{definition.pilot_version}"
    )
    pin = Pin.model_validate_json(coverage_pin.model_dump_json())
    return Pinned(pilot, events, pin, coverage_pin, evaluation)


def transitions(layout: Layout) -> list[StateTransition]:
    try:
        return read_runs(layout.repo / EVENT_RUNS / "states")
    except (OSError, ValueError) as error:
        fail(f"Refused: {error}")


def documents(layout: Layout, pinned: Pinned) -> dict[str, str]:
    """Each pilot event with a parsed document, and its ``doc_id``."""
    return parsed_documents(transitions(layout), pinned.pin.pilot_hash)


def _bundle(path: Path, name: str, layout: Layout, doc_id: str | None) -> Bundle:
    try:
        result = from_fixture_json(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(
            f"Refused: {name}: {layout.shown(path)} is not here; it regenerates"
            " offline from the saved exhibit through canonicalize"
        )
    except (ValueError, UnicodeDecodeError):
        fail(f"Refused: {name}: {path.name} does not load as a canonical document")
    if doc_id is not None and result.document.doc_id != doc_id:
        fail(f"Refused: {name}: {path.name} holds another document")
    return Bundle(name, result.document, result.elements, result.masked.masks)


def load_bundle(layout: Layout, doc_ids: dict[str, str], event_id: str) -> Bundle:
    """One pilot event's canonical document, by the ``doc_id`` its state names."""
    doc_id = doc_ids.get(event_id)
    if doc_id is None:
        fail(f"Refused: {event_id} is not a pilot event with a parsed document")
    path = layout.repo / EVENT_RUNS / "canonical" / f"{doc_id}.json"
    return _bundle(path, event_id, layout, doc_id)


def load_fixture(layout: Layout, fixture_id: str) -> Bundle:
    """One of Stage 1's committed canonical fixtures."""
    path = layout.repo / CANONICAL_FIXTURES / f"{fixture_id}.json"
    return _bundle(path, fixture_id, layout, None)


def wording_texts(layout: Layout, pinned: Pinned) -> dict[str, str]:
    """Every text the committed wording guard reads (the Stage 6 spec, §Wording
    guard): each parsed pilot document's, by event ID, and each Stage 1 fixture's,
    by fixture ID."""
    doc_ids = documents(layout, pinned)
    found = {
        event_id: load_bundle(layout, doc_ids, event_id).document.canonical_text
        for event_id in sorted(doc_ids)
    }
    for path in sorted((layout.repo / CANONICAL_FIXTURES).glob("*.json")):
        found[path.stem] = load_fixture(layout, path.stem).document.canonical_text
    return found


def wording_refusals(record: BaseModel, texts: Mapping[str, str]) -> list[Refusal]:
    """Each string of ``record`` that shares F20's window with one of ``texts``,
    named by its field and the text's ID, never quoted (GS3, GS13)."""
    found = shared(labelled_strings(record.model_dump(mode="json")), texts.items())
    return [
        Refusal(f"{label} ({name})", Problem.SOURCE_WORDING)
        for label, name in sorted(found)
    ]


def fixture_event_ids(layout: Layout, events: EventManifest) -> frozenset[str]:
    """The events whose release is a Stage 1 fixture, matched by accession: each is
    ``train_or_exclude`` (GS10). The fixtures' manifest names no event."""
    path = layout.repo / FIXTURE_MANIFEST
    try:
        fixtures = tomllib.loads(path.read_text(encoding="utf-8"))["fixtures"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        fail(f"Refused: {layout.shown(path)} does not list Stage 1's fixtures")
    accessions = {
        fixture["accession"]
        for fixture in fixtures
        if fixture.get("pilot_split") == "train_or_exclude"
    }
    return frozenset(
        row.event_id for row in events.rows if row.release_accession in accessions
    )


def write_once(path: Path, data: bytes, layout: Layout) -> bool:
    """A committed record, written once: the same bytes again change nothing."""
    existed = path.exists()
    try:
        write_new(path, data)
    except FileExistsError:
        fail(
            f"Refused: {layout.shown(path)} holds other content; a changed record is"
            " a new version, never an edit"
        )
    return not existed


def replace(path: Path, text: str) -> None:
    """A local file under ``data/runs/gold/``, replaced atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    with os.fdopen(handle, "w", encoding="utf-8") as out:
        out.write(text)
    Path(temporary).replace(path)
```

Create `apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py`:

```python
"""``earnings-pipeline pilot``: Stage 6's split and coverage report (the Stage 6
spec, §The split and §The coverage report; plan 9).

    uv run --locked earnings-pipeline pilot split
    uv run --locked earnings-pipeline pilot coverage

Both read the pinned pilot by path and write a frozen record under
``evaluation/<corpus>/pilot-v<N>/``, once: running either again with the same result
changes nothing, and a different result is refused. Neither reads a document,
selects anything, or sends a request (P-C7). ``coverage`` reads the state table; a
rebuild reads only the runs the report names.
"""

import typer
from earnings_ingestion.events.coverage import build_coverage, load_coverage
from earnings_ingestion.events.freeze import serialize
from earnings_themes.records import record_json
from earnings_themes.split import (
    SPLIT_POLICY,
    Partition,
    SplitEvent,
    split_events,
)

from earnings_pipeline.stage6 import (
    Layout,
    Pinned,
    fail,
    fixture_event_ids,
    guarded,
    load_pinned,
    options,
    transitions,
    write_once,
)

pilot = typer.Typer(
    no_args_is_help=True, help="Stage 6's split and coverage report, over the pin."
)
pilot.callback()(options)


def _said(pinned: Pinned, layout: Layout) -> None:
    pin = pinned.pin
    typer.echo(f"pilot {pin.pilot_id} v{pin.pilot_version}  {pin.pilot_hash}")


@pilot.command("split")
@guarded
def split_command(context: typer.Context) -> None:
    """Split the pinned pilot by issuer-time/1, and freeze split-v1.json."""
    layout: Layout = context.obj
    pinned = load_pinned(layout)
    rows = {row.event_id: row for row in pinned.events.rows}
    events = [
        SplitEvent(
            event_id=row.event_id,
            issuer_id=rows[row.event_id].issuer_id,
            period_end=rows[row.event_id].period_end,
        )
        for row in pinned.pilot.rows
    ]
    try:
        manifest = split_events(
            events,
            pinned.pin,
            fixture_event_ids=fixture_event_ids(layout, pinned.events),
        )
    except ValueError as error:
        fail(f"Refused: {error}")
    created = write_once(pinned.split_path, record_json(manifest), layout)
    _said(pinned, layout)
    for partition in Partition:
        typer.echo(f"{partition}  {len(manifest.events_in(partition))}")
    for row in manifest.rows:
        if row.reason is not None:
            typer.echo(f"excluded  {row.event_id}  {row.reason}")
    verb = "froze" if created else "unchanged:"
    typer.echo(f"{verb} split v{manifest.split_version} by {SPLIT_POLICY}")
    typer.echo(f"{layout.shown(pinned.split_path)}  {manifest.content_hash}")


@pilot.command("coverage")
@guarded
def coverage_command(context: typer.Context) -> None:
    """Count the pinned pilot's documents by state, and freeze coverage-v1.json."""
    layout: Layout = context.obj
    pinned = load_pinned(layout)
    path = pinned.coverage_path
    try:
        run_ids = load_coverage(path).run_ids if path.exists() else None
        report = build_coverage(
            pinned.pilot, pinned.coverage_pin, transitions(layout), run_ids=run_ids
        )
    except ValueError as error:
        fail(f"Refused: {error}")
    created = write_once(path, serialize(report), layout)
    _said(pinned, layout)
    for count in report.states:
        if count.count:
            typer.echo(f"{count.state}  {count.count}")
    for gap in report.gaps:
        typer.echo(f"gap  {gap.state}  ({gap.basis}: never repaired by reselecting)")
    for override in report.overrides:
        typer.echo(
            f"override  {override.override_id}  {override.document_id}"
            f"  {override.verdict}"
        )
    typer.echo(f"runs  {', '.join(report.run_ids)}")
    verb = "froze" if created else "unchanged:"
    typer.echo(
        f"{verb} coverage v{report.coverage_version}: {report.documents} documents"
    )
    typer.echo(f"{layout.shown(path)}  {report.content_hash}")
```

Create `/tmp/plan9-task10-impl.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/src/earnings_pipeline/cli.py": [
        (
            "    uv run --locked --all-packages earnings-pipeline events --help\n"
            "\n",
            "    uv run --locked --all-packages earnings-pipeline events --help\n"
            "    uv run --locked --all-packages earnings-pipeline pilot --help\n"
            "\n",
        ),
        (
            "(``earnings_pipeline.events_cli``).\n",
            "(``earnings_pipeline.events_cli``). ``pilot`` holds Stage 6's split and coverage report (``pilot_cli``).\n",
        ),
        (
            "from earnings_pipeline.events_cli import events\n"
            "\n",
            "from earnings_pipeline.events_cli import events\n"
            "from earnings_pipeline.pilot_cli import pilot\n"
            "\n",
        ),
        (
            "app.add_typer(events, name=\"events\")\n"
            "\n",
            "app.add_typer(events, name=\"events\")\n"
            "app.add_typer(pilot, name=\"pilot\")\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py apps/earnings-pipeline/src/earnings_pipeline/stage6.py
python3 /tmp/plan9-extract.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py
python3 /tmp/plan9-extract.py /tmp/plan9-task10-impl.py && python3 /tmp/plan9-task10-impl.py
```

Expected:

```text
extracted apps/earnings-pipeline/src/earnings_pipeline/stage6.py: 298 lines
extracted apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py: 114 lines
extracted /tmp/plan9-task10-impl.py: 47 lines
edited apps/earnings-pipeline/src/earnings_pipeline/cli.py: 4 replacement(s)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q`

Expected: `6 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/src/earnings_pipeline/stage6.py apps/earnings-pipeline/tests/test_stage6_cli.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1702 passed, 1 skipped, 24 deselected`; `All checks passed!` and `292 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/src/earnings_pipeline/pilot_cli.py apps/earnings-pipeline/src/earnings_pipeline/stage6.py apps/earnings-pipeline/tests/test_stage6_cli.py
git commit -m "feat(pipeline): pilot split and pilot coverage, over the pin (GS2, GS8)"
```

---

### Task 11: codebook freeze and validate

S §The codebook, §Drafting and tools, GS9, and P9-13, P9-20. `codebook freeze` reads
the user's working copy, anchors every example in the training bundles, checks its
wording against every text the committed guard reads (P9-21), and only then prints
the content hash; it writes `codebooks/djia-pilot/codebook-v0.toml`, approved, only
when `--adr` names a file that cites that hash. `codebook validate` rechecks the
committed version against the local bundles and the same texts.

**Files:**

- Create: `apps/earnings-pipeline/src/earnings_pipeline/codebook_cli.py`.
- Modify, by exact replacement: `cli.py`, and the test module
  `apps/earnings-pipeline/tests/test_stage6_cli.py`.

**Interfaces:**

- Consumes: Task 7's codebook functions; Task 10's `Layout`, `Pinned`,
  `load_pinned`, `documents`, `load_bundle`, `wording_texts`, `wording_refusals`,
  `write_once`, `guarded`, and the output helpers.
- Produces: `WORKING`, the default working copy's path;
  `pinned_split(layout, pinned) -> SplitManifest`; `training(layout, pinned, split)
  -> dict[str, Bundle]`; `pinned_codebook(layout) -> Codebook`; and
  `earnings-pipeline codebook freeze [--working PATH] [--adr PATH --approver NAME
  --approved-on DATE]` and `earnings-pipeline codebook validate`.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan9-task11-tests.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/tests/test_stage6_cli.py": [
        (
            "report freeze once, over the pin; every refusal names its item and reason; and no\n"
            "command prints a document's text (GS13) or changes a frozen record (P-C7).\n",
            "report freeze once, over the pin; codebook v0 freezes only once its ADR cites it;\n"
            "every refusal names its item and reason; and no command prints a document's text\n"
            "(GS13) or changes a frozen record (P-C7).\n",
        ),
        (
            ")\n"
            "from earnings_themes.gold import ReleaseIdentification, ReleaseLabel\n",
            ")\n"
            "from earnings_themes import tomlfile\n"
            "from earnings_themes.codebook import load_codebook\n"
            "from earnings_themes.gold import ReleaseIdentification, ReleaseLabel\n",
        ),
        (
            "from earnings_themes.split import load_split\n"
            "from earnings_themes.wording import WIDTH, masked\n",
            "from earnings_themes.split import load_split\n"
            "from earnings_themes.synthetic import codebook_draft\n"
            "from earnings_themes.wording import WIDTH, masked\n",
        ),
        (
            "EVENT_RUNS = Path(\"data\") / \"runs\" / \"events\"\n"
            "EVALUATION = Path(\"evaluation\") / \"djia-synthetic\" / \"pilot-v1\"\n",
            "EVENT_RUNS = Path(\"data\") / \"runs\" / \"events\"\n"
            "DRAFTS = Path(\"data\") / \"runs\" / \"gold\" / \"drafts\"\n"
            "EVALUATION = Path(\"evaluation\") / \"djia-synthetic\" / \"pilot-v1\"\n",
        ),
        (
            "RELEASES = Path(\"tests\") / \"fixtures\" / \"releases\" / \"manifest.toml\"\n"
            "EXCLUDED = \"cik-0009990001:2025-08-31\"\n",
            "RELEASES = Path(\"tests\") / \"fixtures\" / \"releases\" / \"manifest.toml\"\n"
            "CODEBOOK = Path(\"codebooks\") / \"djia-pilot\" / \"codebook-v0.toml\"\n"
            "ADR = Path(\"docs\") / \"adr\" / \"0003-codebook-v0.md\"\n"
            "FIRST = \"cik-0009990001:2024-08-31\"\n"
            "UNPARSED = (\"cik-0009990003:2025-06-30\", \"cik-0009990005:2025-03-28\")\n"
            "EXCLUDED = \"cik-0009990001:2025-08-31\"\n",
        ),
        (
            "EXCLUDED = \"cik-0009990001:2025-08-31\"\n"
            "WINDOW = 20\n",
            "EXCLUDED = \"cik-0009990001:2025-08-31\"\n"
            "SENTENCE = \"today reported net sales of $1,000 million\"\n"
            "WINDOW = 20\n",
        ),
        (
            "    return result.output.splitlines()\n"
            "\n",
            "    return result.output.splitlines()\n"
            "\n"
            "\n"
            "def write_drafts(repo: Path, name: str, drafted: dict, working: dict | None = None):\n"
            "    folder = repo / DRAFTS\n"
            "    folder.mkdir(parents=True, exist_ok=True)\n"
            "    for kind, data in ((\"draft\", drafted), (\"working\", working or drafted)):\n"
            "        text = tomlfile.dumps(data)\n"
            "        path = folder / f\"{name.replace(':', '_')}.{kind}.toml\"\n"
            "        path.write_text(text, encoding=\"utf-8\")\n"
            "\n"
            "\n"
            "def the_codebook(**changes) -> dict:\n"
            "    draft = codebook_draft(**changes)\n"
            "    draft[\"themes\"][0][\"positive_examples\"] = [{\"event_id\": FIRST, \"text\": SENTENCE}]\n"
            "    return draft\n"
            "\n"
            "\n"
            "def frozen(repo: Path) -> Path:\n"
            "    \"\"\"The split frozen and codebook v0 approved, as gate 3 leaves them.\"\"\"\n"
            "    assert run(repo, \"pilot\", \"split\").exit_code == 0\n"
            "    write_drafts(repo, \"codebook\", the_codebook())\n"
            "    first = run(repo, \"codebook\", \"freeze\")\n"
            "    content_hash = lines(first)[-2].split()[-1]\n"
            "    (repo / ADR).parent.mkdir(parents=True)\n"
            "    (repo / ADR).write_text(f\"Codebook v0 is {content_hash}.\\n\", encoding=\"utf-8\")\n"
            "    approved = run(\n"
            "        repo,\n"
            "        \"codebook\",\n"
            "        \"freeze\",\n"
            "        \"--adr\",\n"
            "        str(ADR),\n"
            "        \"--approver\",\n"
            "        \"Lowell Mason\",\n"
            "        \"--approved-on\",\n"
            "        \"2026-10-02\",\n"
            "    )\n"
            "    assert approved.exit_code == 0, approved.output\n"
            "    return repo / CODEBOOK\n"
            "\n",
        ),
        (
            "    assert refusals == [f\"note ({last}): source_wording\"]\n",
            "    assert refusals == [f\"note ({last}): source_wording\"]\n"
            "\n"
            "\n"
            "def test_codebook_v0_is_written_only_once_its_adr_cites_it(repo) -> None:\n"
            "    assert run(repo, \"pilot\", \"split\").exit_code == 0\n"
            "    write_drafts(repo, \"codebook\", the_codebook())\n"
            "    first = run(repo, \"codebook\", \"freeze\")\n"
            "    assert first.exit_code == 0, first.output\n"
            "    assert lines(first)[:3] == [\n"
            "        f\"no parsed document  {UNPARSED[0]}\",\n"
            "        f\"no parsed document  {UNPARSED[1]}\",\n"
            "        \"codebook djia-pilot v0: 1 themes, 2 examples, from 11 training bundles\",\n"
            "    ]\n"
            "    assert lines(first)[-1].startswith(\"not written: ADR 0003 cites this hash\")\n"
            "    assert not (repo / CODEBOOK).exists()\n"
            "    content_hash = lines(first)[-2].split()[-1]\n"
            "    (repo / ADR).parent.mkdir(parents=True)\n"
            "    (repo / ADR).write_text(\"Codebook v0.\\n\", encoding=\"utf-8\")\n"
            "    approve = [\"--adr\", str(ADR), \"--approver\", \"Lowell Mason\"]\n"
            "    uncited = run(repo, \"codebook\", \"freeze\", *approve, \"--approved-on\", \"2026-10-02\")\n"
            "    assert lines(uncited)[-1] == f\"Refused: {ADR} does not cite {content_hash}\"\n"
            "    assert not (repo / CODEBOOK).exists()\n"
            "    (repo / ADR).write_text(f\"Codebook v0 is {content_hash}.\\n\", encoding=\"utf-8\")\n"
            "    cited = run(repo, \"codebook\", \"freeze\", *approve, \"--approved-on\", \"2026-10-02\")\n"
            "    assert cited.exit_code == 0, cited.output\n"
            "    assert lines(cited)[-2:] == [\n"
            "        \"froze djia-pilot v0, approved\",\n"
            "        f\"{CODEBOOK}  {content_hash}\",\n"
            "    ]\n"
            "    codebook = load_codebook(repo / CODEBOOK)\n"
            "    assert codebook.content_hash == content_hash\n"
            "    assert codebook.discovery_corpus.event_ids[0] == FIRST\n"
            "    assert (\n"
            "        FIRST\n"
            "        not in (repo / CODEBOOK)\n"
            "        .read_text(encoding=\"utf-8\")\n"
            "        .split(\"[[themes]]\")[1]\n"
            "        .split(\"event_id\")[0]\n"
            "    )\n"
            "    valid = run(repo, \"codebook\", \"validate\")\n"
            "    assert valid.exit_code == 0, valid.output\n"
            "    assert lines(valid)[-2] == (\n"
            "        \"valid: djia-pilot v0, 1 themes, approved by Lowell Mason on 2026-10-02\"\n"
            "    )\n"
            "\n"
            "\n"
            "def test_a_codebook_that_copies_a_training_release_is_refused(repo) -> None:\n"
            "    assert run(repo, \"pilot\", \"split\").exit_code == 0\n"
            "    copied = the_codebook()\n"
            "    copied[\"themes\"][0][\"definition\"] = (\n"
            "        f\"Acme Industrial Corp {SENTENCE} for the quarter.\"\n"
            "    )\n"
            "    write_drafts(repo, \"codebook\", copied)\n"
            "    result = run(repo, \"codebook\", \"freeze\")\n"
            "    assert result.exit_code == 1\n"
            "    refusals = [line for line in lines(result) if line.startswith(\"refused: \")]\n"
            "    assert f\"refused: themes[0].definition ({FIRST}): source_wording\" in refusals\n"
            "    assert all(line.endswith(\"): source_wording\") for line in refusals)\n"
            "    assert lines(result)[-1] == (\n"
            "        f\"Refused: {len(refusals)} problem(s); nothing written\"\n"
            "    )\n"
            "\n"
            "\n"
            "def test_a_codebook_that_copies_any_pilot_release_is_refused_before_its_hash(\n"
            "    repo,\n"
            ") -> None:\n"
            "    \"\"\"GS3: codebook freeze checks v0 against every text the committed guard reads,\n"
            "    not only the training releases, so a codebook the guard would refuse gets no\n"
            "    content hash, and nothing is written. The synthetic releases share one template,\n"
            "    so the copy is taken from a Stage 1 fixture, which the guard also reads.\"\"\"\n"
            "    assert run(repo, \"pilot\", \"split\").exit_code == 0\n"
            "    found = guarded_texts(repo)\n"
            "    other = first_fixture(repo)\n"
            "    changed = the_codebook()\n"
            "    changed[\"themes\"][0][\"definition\"] = f\"Ours: {unique_window(found, other)}\"\n"
            "    write_drafts(repo, \"codebook\", changed)\n"
            "    result = run(repo, \"codebook\", \"freeze\")\n"
            "    assert result.exit_code == 1\n"
            "    assert [line for line in lines(result) if line.startswith(\"refused: \")] == [\n"
            "        f\"refused: themes[0].definition ({other}): source_wording\"\n"
            "    ]\n"
            "    assert not any(line.startswith(\"content_hash\") for line in lines(result))\n"
            "    assert not (repo / CODEBOOK).exists()\n"
            "\n"
            "\n"
            "def test_codebook_validate_checks_every_text_the_guard_reads(repo) -> None:\n"
            "    \"\"\"P9-21: codebook validate rechecks the committed v0 against every text the\n"
            "    committed guard reads, as freeze does.\"\"\"\n"
            "    path = frozen(repo)\n"
            "    other = first_fixture(repo)\n"
            "    record = tomlfile.read(path)\n"
            "    copied = unique_window(guarded_texts(repo), other)\n"
            "    record[\"themes\"][0][\"definition\"] = f\"Ours: {copied}\"\n"
            "    path.write_text(tomlfile.dumps(record), encoding=\"utf-8\")\n"
            "    result = run(repo, \"codebook\", \"validate\")\n"
            "    assert result.exit_code == 1\n"
            "    assert f\"refused: themes[0].definition ({other}): source_wording\" in lines(result)\n",
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

Write them:

```bash
python3 /tmp/plan9-extract.py /tmp/plan9-task11-tests.py && python3 /tmp/plan9-task11-tests.py
```

Expected:

```text
extracted /tmp/plan9-task11-tests.py: 212 lines
edited apps/earnings-pipeline/tests/test_stage6_cli.py: 8 replacement(s)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q`

Expected: FAIL, `4 failed, 6 passed`, with:

```text
AssertionError: Usage: root [OPTIONS] COMMAND [ARGS]...
assert 2 == 0
assert 2 == 1
FAILED apps/earnings-pipeline/tests/test_stage6_cli.py::test_codebook_v0_is_written_only_once_its_adr_cites_it
FAILED apps/earnings-pipeline/tests/test_stage6_cli.py::test_a_codebook_that_copies_a_training_release_is_refused
FAILED apps/earnings-pipeline/tests/test_stage6_cli.py::test_a_codebook_that_copies_any_pilot_release_is_refused_before_its_hash
FAILED apps/earnings-pipeline/tests/test_stage6_cli.py::test_codebook_validate_checks_every_text_the_guard_reads
```

- [x] **Step 3: Write the codebook commands**

Create `apps/earnings-pipeline/src/earnings_pipeline/codebook_cli.py`:

```python
"""``earnings-pipeline codebook``: codebook v0's freeze and check (the Stage 6 spec,
§The codebook; GS9; plan 9).

    uv run --locked earnings-pipeline codebook freeze
    uv run --locked earnings-pipeline codebook freeze --adr docs/adr/0003-...md \\
        --approver "Lowell Mason" --approved-on 2026-10-02
    uv run --locked earnings-pipeline codebook validate

``freeze`` reads the user's working copy, ``data/runs/gold/drafts/
codebook.working.toml``, anchors each example in the training bundles, and prints
the content hash. It writes nothing until ADR 0003 is named: then it checks that
the ADR cites that hash, and writes ``codebooks/djia-pilot/codebook-v0.toml`` once,
approved. Before printing the hash, it checks the codebook against every text the
committed wording guard reads. ``validate`` rechecks the committed version against
the local documents. Neither prints a document's text.
"""

from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import (
    Approval,
    Codebook,
    codebook_toml,
    freeze_codebook,
    load_codebook,
    load_codebook_draft,
    validate_codebook,
)
from earnings_themes.records import RecordError
from earnings_themes.split import Partition, SplitManifest, load_split

from earnings_pipeline.stage6 import (
    CODEBOOK_FILE,
    GOLD_RUNS,
    Layout,
    Pinned,
    documents,
    fail,
    guarded,
    load_bundle,
    load_pinned,
    options,
    record_error,
    refuse,
    wording_refusals,
    wording_texts,
    write_once,
)

codebook = typer.Typer(no_args_is_help=True, help="Stage 6's codebook v0.")
codebook.callback()(options)
WORKING = GOLD_RUNS / "drafts" / "codebook.working.toml"


def pinned_split(layout: Layout, pinned: Pinned) -> SplitManifest:
    """The frozen split of the pinned pilot, or a refusal."""
    try:
        split = load_split(pinned.split_path)
    except RecordError as error:
        typer.echo(f"problem: {error}", err=True)
        fail(
            f"Refused: {layout.shown(pinned.split_path)} is not frozen: run pilot split"
        )
    if split.pin != pinned.pin:
        fail(f"Refused: {layout.shown(pinned.split_path)} names another pin")
    return split


def training(layout: Layout, pinned: Pinned, split: SplitManifest) -> dict[str, Bundle]:
    """Each training event with a parsed document; an event without one is named."""
    doc_ids = documents(layout, pinned)
    bundles = {}
    for event_id in split.events_in(Partition.TRAIN):
        if event_id in doc_ids:
            bundles[event_id] = load_bundle(layout, doc_ids, event_id)
        else:
            typer.echo(f"no parsed document  {event_id}")
    return bundles


def _examples(made: Codebook) -> int:
    return sum(len(t.positive_examples) + len(t.hard_negatives) for t in made.themes)


@codebook.command("freeze")
@guarded
def freeze_command(
    context: typer.Context,
    working: Annotated[Path, typer.Option(help="The user's working copy.")] = WORKING,
    adr: Annotated[
        Path | None, typer.Option(help="ADR 0003, which cites the content hash.")
    ] = None,
    approver: Annotated[str | None, typer.Option(help="Who approved.")] = None,
    approved_on: Annotated[
        str | None, typer.Option(help="The approval's date, YYYY-MM-DD.")
    ] = None,
) -> None:
    """Anchor and check the working copy; with --adr, write the approved v0."""
    layout: Layout = context.obj
    pinned = load_pinned(layout)
    split = pinned_split(layout, pinned)
    bundles = training(layout, pinned, split)
    try:
        draft = load_codebook_draft(layout.repo / working)
    except RecordError as error:
        record_error(error)
    approval = None
    if adr is not None:
        if approver is None or approved_on is None:
            fail("Refused: --adr needs --approver and --approved-on")
        try:
            day = date.fromisoformat(approved_on)
        except ValueError:
            fail(f"Refused: {approved_on} is not a date such as 2026-10-02")
        approval = Approval(approver=approver, approved_on=day, adr=adr.as_posix())
    made = freeze_codebook(
        draft, pin=pinned.pin, split=split, bundles=bundles, approval=approval
    )
    if isinstance(made, list):
        refuse(made)
    if found := wording_refusals(made, wording_texts(layout, pinned)):
        refuse(found)
    typer.echo(
        f"codebook {made.codebook_id} v{made.codebook_version}: {len(made.themes)}"
        f" themes, {_examples(made)} examples, from {len(bundles)} training bundles"
    )
    typer.echo(f"content_hash  {made.content_hash}")
    if approval is None:
        typer.echo(
            "not written: ADR 0003 cites this hash; then run freeze again with --adr,"
            " --approver, and --approved-on"
        )
        return
    adr_path = layout.repo / adr
    if not adr_path.is_file() or made.content_hash not in adr_path.read_text(
        encoding="utf-8"
    ):
        fail(f"Refused: {adr} does not cite {made.content_hash}")
    path = layout.repo / CODEBOOK_FILE
    created = write_once(path, codebook_toml(made).encode(), layout)
    verb = "froze" if created else "unchanged:"
    typer.echo(f"{verb} {made.codebook_id} v{made.codebook_version}, approved")
    typer.echo(f"{layout.shown(path)}  {made.content_hash}")


def pinned_codebook(layout: Layout) -> Codebook:
    """The committed codebook version, or a refusal."""
    path = layout.repo / CODEBOOK_FILE
    if not path.is_file():
        fail(f"Refused: {layout.shown(path)} is not frozen: run codebook freeze")
    try:
        return load_codebook(path)
    except RecordError as error:
        record_error(error)


@codebook.command("validate")
@guarded
def validate_command(context: typer.Context) -> None:
    """Recheck the committed version against the local training bundles."""
    layout: Layout = context.obj
    pinned = load_pinned(layout)
    split = pinned_split(layout, pinned)
    made = pinned_codebook(layout)
    bundles = training(layout, pinned, split)
    adr_text = None
    if made.approval is not None and (layout.repo / made.approval.adr).is_file():
        adr_text = (layout.repo / made.approval.adr).read_text(encoding="utf-8")
    refusals = validate_codebook(
        made, pin=pinned.pin, split=split, bundles=bundles, adr_text=adr_text
    )
    found = wording_refusals(made, wording_texts(layout, pinned))
    refusals += [refusal for refusal in found if refusal not in refusals]
    if refusals:
        refuse(refusals, "changed")
    approval = made.approval
    assert approval is not None
    typer.echo(
        f"valid: {made.codebook_id} v{made.codebook_version}, {len(made.themes)}"
        f" themes, approved by {approval.approver} on {approval.approved_on}"
    )
    typer.echo(f"{layout.shown(layout.repo / CODEBOOK_FILE)}  {made.content_hash}")
```

Create `/tmp/plan9-task11-impl.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/src/earnings_pipeline/cli.py": [
        (
            "(``earnings_pipeline.events_cli``). ``pilot`` holds Stage 6's split and coverage report (``pilot_cli``).\n",
            "(``earnings_pipeline.events_cli``). ``pilot`` and ``codebook`` hold Stage 6's (``pilot_cli`` and\n"
            "``codebook_cli``).\n",
        ),
        (
            "\n"
            "from earnings_pipeline.cohort_cli import cohort\n",
            "\n"
            "from earnings_pipeline.codebook_cli import codebook\n"
            "from earnings_pipeline.cohort_cli import cohort\n",
        ),
        (
            "app.add_typer(pilot, name=\"pilot\")\n"
            "\n",
            "app.add_typer(pilot, name=\"pilot\")\n"
            "app.add_typer(codebook, name=\"codebook\")\n"
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

Write them:

```bash
python3 /tmp/plan9-extract.py apps/earnings-pipeline/src/earnings_pipeline/codebook_cli.py
python3 /tmp/plan9-extract.py /tmp/plan9-task11-impl.py && python3 /tmp/plan9-task11-impl.py
```

Expected:

```text
extracted apps/earnings-pipeline/src/earnings_pipeline/codebook_cli.py: 186 lines
extracted /tmp/plan9-task11-impl.py: 41 lines
edited apps/earnings-pipeline/src/earnings_pipeline/cli.py: 3 replacement(s)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q`

Expected: `10 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/src/earnings_pipeline/codebook_cli.py apps/earnings-pipeline/tests/test_stage6_cli.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1706 passed, 1 skipped, 24 deselected`; `All checks passed!` and `293 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/src/earnings_pipeline/codebook_cli.py apps/earnings-pipeline/tests/test_stage6_cli.py
git commit -m "feat(pipeline): codebook freeze and codebook validate (GS9)"
```

---

### Task 12: gold anchor, show, and validate

S §The gold, §Anchoring and validation, §Curated hard negatives, §Drafting and
tools, GS4, GS5, GS13, and P9-3, P9-11, P9-21. `gold anchor` builds each working
copy, checks its wording against every text the committed guard reads, and writes
the result under `data/runs/gold/anchored/`, then the committed record, once, when
the working copy is signed. A signed record that differs from the one already
written is refused before anything changes. `gold show` writes the texts a drafting
session reads and the views the user verifies against. `gold validate` rechecks
committed records, a bundle's against the same texts; for the curated hard negatives
it runs offline, against Stage 1's committed fixtures, so the default suite runs it. Every command loads the pin, the
curated ones too. Files named for an event take `file_stem` (P9-3), and the step
amends S's two paths and adds the dictionary's file list.

**Files:**

- Create: `apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py`.
- Modify, by exact replacement: `cli.py`, `docs/data-dictionary.md`,
  `specs/pilot-codebook-split-and-gold-set-protocol.md`, and the test module.

**Interfaces:**

- Consumes: Task 8's build and validators; Task 9's views; Task 10's layer; Task
  11's `pinned_split` and `pinned_codebook`.
- Produces: `CURATED = "hard-negatives"`; `fixture_bundles(layout) -> dict[str,
  Bundle]`; `readable(partition, codebook_frozen) -> str | None`, the reason a
  bundle may not be read yet (GS13, GS18), or `None`; and the commands:
  - `gold anchor [EVENT ...] [--hard-negatives] [--check]`;
  - `gold show [EVENT ...] [--text] [--training] [--hard-negatives]`;
  - `gold validate [EVENT ...] [--hard-negatives]`.

- [x] **Step 1: Write the failing tests**

Create `/tmp/plan9-task12-tests.py`:

```python
"""Plan 9: exact replacements for 1 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/tests/test_stage6_cli.py": [
        (
            "\"\"\"Stage 6's commands over the synthetic pilot (plan 9): the split and the coverage\n"
            "report freeze once, over the pin; codebook v0 freezes only once its ADR cites it;\n"
            "every refusal names its item and reason; and no command prints a document's text\n"
            "(GS13) or changes a frozen record (P-C7).\n",
            "\"\"\"Stage 6's commands over the synthetic pilot (plan 9): the split and coverage\n"
            "report freeze once, codebook v0 freezes only once its ADR cites it, gold commits\n"
            "only once signed, every refusal names its item and reason, and no command prints a\n"
            "document's text (GS13) or changes a frozen record (P-C7).\n",
        ),
        (
            "Stage 5's replay test does; its documents are the synthetic layer's invented text.\n"
            "\"\"\"\n",
            "Stage 5's replay test does; its documents are the synthetic layer's invented text.\n"
            "Curated hard negatives take their quotes from Stage 1's fixtures when a test runs.\n"
            "\"\"\"\n",
        ),
        (
            "from earnings_pipeline import cli\n",
            "from earnings_pipeline import cli, gold_cli\n",
        ),
        (
            "from earnings_themes import tomlfile\n"
            "from earnings_themes.codebook import load_codebook\n",
            "from earnings_themes import tomlfile\n"
            "from earnings_themes.anchoring import Bundle\n"
            "from earnings_themes.codebook import load_codebook\n",
        ),
        (
            "from earnings_themes.gold import ReleaseIdentification, ReleaseLabel\n"
            "from earnings_themes.split import load_split\n"
            "from earnings_themes.synthetic import codebook_draft\n",
            "from earnings_themes.gold import (\n"
            "    ReleaseIdentification,\n"
            "    ReleaseLabel,\n"
            "    load_gold,\n"
            "    load_hard_negatives,\n"
            ")\n"
            "from earnings_themes.split import Partition, load_split\n"
            "from earnings_themes.synthetic import AID, codebook_draft, curated_draft\n",
        ),
        (
            "FIRST = \"cik-0009990001:2024-08-31\"\n"
            "UNPARSED = (\"cik-0009990003:2025-06-30\", \"cik-0009990005:2025-03-28\")\n",
            "FIRST = \"cik-0009990001:2024-08-31\"\n"
            "FIRST_FILE = \"cik-0009990001_2024-08-31\"\n"
            "SECOND = \"cik-0009990001:2024-11-30\"\n"
            "UNPARSED = (\"cik-0009990003:2025-06-30\", \"cik-0009990005:2025-03-28\")\n",
        ),
        (
            "SENTENCE = \"today reported net sales of $1,000 million\"\n"
            "WINDOW = 20\n",
            "SENTENCE = \"today reported net sales of $1,000 million\"\n"
            "SIGNED = \"Lowell Mason (verified a Claude draft)\"\n"
            "WINDOW = 20\n",
        ),
        (
            "\n"
            "def pilot_bytes(repo: Path) -> dict[str, bytes]:\n",
            "\n"
            "def gold_draft(event_id: str = FIRST, annotator: str = \"\", **changes) -> dict:\n"
            "    draft = {\n"
            "        \"event_id\": event_id,\n"
            "        \"annotator\": annotator,\n"
            "        \"drafting_aid\": AID,\n"
            "        \"no_theme\": False,\n"
            "        \"release_identification\": {\"label\": \"release\", \"note\": \"Its own results.\"},\n"
            "        \"quotes\": [{\"quote_id\": \"q1\", \"text\": SENTENCE}],\n"
            "        \"claims\": [{\"claim_id\": \"c1\", \"quote_ids\": [\"q1\"], \"claim\": \"Sales rose.\"}],\n"
            "        \"assignments\": [\n"
            "            {\"claim_id\": \"c1\", \"theme_id\": \"demand\", \"support\": \"supports\"}\n"
            "        ],\n"
            "    }\n"
            "    draft.update(changes)\n"
            "    return draft\n"
            "\n"
            "\n"
            "def fixtures(repo: Path) -> dict[str, Bundle]:\n"
            "    bundles = {}\n"
            "    for path in sorted((repo / CANONICAL).glob(\"*.json\")):\n"
            "        result = from_fixture_json(path.read_text(encoding=\"utf-8\"))\n"
            "        bundles[path.stem] = Bundle(\n"
            "            path.stem, result.document, result.elements, result.masked.masks\n"
            "        )\n"
            "    return bundles\n"
            "\n"
            "\n"
            "def pilot_bytes(repo: Path) -> dict[str, bytes]:\n",
        ),
        (
            "    raise AssertionError(f\"{name} has no window of its own\")\n"
            "\n",
            "    raise AssertionError(f\"{name} has no window of its own\")\n"
            "\n"
            "\n"
            "def a_pilot_window(found: dict[str, str]) -> tuple[str, str]:\n"
            "    \"\"\"The first synthetic pilot release with a window of its own, and that window.\n"
            "    Most share one template, so each is tried in turn.\"\"\"\n"
            "    for name in sorted(key for key in found if \":\" in key):\n"
            "        try:\n"
            "            return name, unique_window(found, name)\n"
            "        except AssertionError:\n"
            "            continue\n"
            "    raise AssertionError(\"no pilot release has a window of its own\")\n"
            "\n",
        ),
        (
            "    assert f\"refused: themes[0].definition ({other}): source_wording\" in lines(result)\n",
            "    assert f\"refused: themes[0].definition ({other}): source_wording\" in lines(result)\n"
            "\n"
            "\n"
            "def test_gold_commits_only_once_signed_and_then_validates(repo) -> None:\n"
            "    frozen(repo)\n"
            "    before = pilot_bytes(repo)\n"
            "    write_drafts(repo, FIRST, gold_draft())\n"
            "    unsigned = run(repo, \"gold\", \"anchor\", FIRST)\n"
            "    assert unsigned.exit_code == 0, unsigned.output\n"
            "    assert lines(unsigned) == [\n"
            "        (\n"
            "            f\"{FIRST} (train): 1 quotes, 1 claims, 1 assignments, 0 hard negatives;\"\n"
            "            \" no_theme false\"\n"
            "        ),\n"
            "        \"origins: accepted 3, edited 0, rejected 0, added 0\",\n"
            "        f\"anchored  data/runs/gold/anchored/{FIRST_FILE}.toml\",\n"
            "        (\n"
            "            f\"unsigned: {FIRST} is not committed until the working copy's annotator\"\n"
            "            \" is signed\"\n"
            "        ),\n"
            "    ]\n"
            "    committed = repo / EVALUATION / \"gold\" / f\"{FIRST_FILE}.toml\"\n"
            "    assert not committed.exists()\n"
            "    shown = run(repo, \"gold\", \"show\", FIRST)\n"
            "    assert lines(shown) == [f\"view  data/runs/gold/views/{FIRST_FILE}.md\"]\n"
            "    view = (repo / \"data\" / \"runs\" / \"gold\" / \"views\" / f\"{FIRST_FILE}.md\").read_text(\n"
            "        encoding=\"utf-8\"\n"
            "    )\n"
            "    assert f\"[[q1>>{SENTENCE}<<q1]]\" in view\n"
            "    write_drafts(repo, FIRST, gold_draft(), gold_draft(annotator=SIGNED))\n"
            "    signed = run(repo, \"gold\", \"anchor\", FIRST)\n"
            "    assert lines(signed)[-1] == f\"froze {EVALUATION}/gold/{FIRST_FILE}.toml\"\n"
            "    assert lines(run(repo, \"gold\", \"anchor\", FIRST))[-1] == (\n"
            "        f\"unchanged: {EVALUATION}/gold/{FIRST_FILE}.toml\"\n"
            "    )\n"
            "    record = load_gold(committed)\n"
            "    assert (record.annotator, record.partition, record.no_theme) == (\n"
            "        SIGNED,\n"
            "        \"train\",\n"
            "        False,\n"
            "    )\n"
            "    assert SENTENCE not in committed.read_text(encoding=\"utf-8\")\n"
            "    valid = run(repo, \"gold\", \"validate\")\n"
            "    assert valid.exit_code == 0, valid.output\n"
            "    assert lines(valid) == [f\"valid: {FIRST} (train), 1 quotes, 1 claims, signed\"]\n"
            "    assert pilot_bytes(repo) == before\n"
            "\n"
            "\n"
            "def test_gold_that_copies_another_release_is_refused_before_anything_is_written(\n"
            "    repo,\n"
            ") -> None:\n"
            "    \"\"\"GS3: gold anchor checks a bundle's gold against every text the committed\n"
            "    guard reads, not only its own release, with --check too, and writes nothing.\n"
            "    The copy is taken from a Stage 1 fixture, since the synthetic releases share one\n"
            "    template.\"\"\"\n"
            "    frozen(repo)\n"
            "    other = first_fixture(repo)\n"
            "    copied = unique_window(guarded_texts(repo), other)\n"
            "    claims = [{\"claim_id\": \"c1\", \"quote_ids\": [\"q1\"], \"claim\": f\"Ours: {copied}\"}]\n"
            "    write_drafts(\n"
            "        repo,\n"
            "        FIRST,\n"
            "        gold_draft(claims=claims),\n"
            "        gold_draft(annotator=SIGNED, claims=claims),\n"
            "    )\n"
            "    for args in ((FIRST, \"--check\"), (FIRST,)):\n"
            "        result = run(repo, \"gold\", \"anchor\", *args)\n"
            "        assert result.exit_code == 1\n"
            "        assert [line for line in lines(result) if line.startswith(\"refused: \")] == [\n"
            "            f\"refused: claims[0].claim ({other}): source_wording\"\n"
            "        ]\n"
            "    assert not (repo / \"data\" / \"runs\" / \"gold\" / \"anchored\").exists()\n"
            "    assert not (repo / EVALUATION / \"gold\").exists()\n"
            "\n"
            "\n"
            "def test_a_changed_signed_copy_is_refused_before_its_anchored_file_changes(\n"
            "    repo,\n"
            ") -> None:\n"
            "    \"\"\"A refusal writes nothing: once a bundle's record is written, a changed signed\n"
            "    working copy is refused before the anchored file is replaced, so the view still\n"
            "    shows the record as written.\"\"\"\n"
            "    frozen(repo)\n"
            "    write_drafts(repo, FIRST, gold_draft(), gold_draft(annotator=SIGNED))\n"
            "    assert run(repo, \"gold\", \"anchor\", FIRST).exit_code == 0\n"
            "    anchored = repo / \"data\" / \"runs\" / \"gold\" / \"anchored\" / f\"{FIRST_FILE}.toml\"\n"
            "    committed = repo / EVALUATION / \"gold\" / f\"{FIRST_FILE}.toml\"\n"
            "    claims = [{\"claim_id\": \"c1\", \"quote_ids\": [\"q1\"], \"claim\": \"Sales grew.\"}]\n"
            "    write_drafts(repo, FIRST, gold_draft(), gold_draft(annotator=SIGNED, claims=claims))\n"
            "    result = run(repo, \"gold\", \"anchor\", FIRST)\n"
            "    assert result.exit_code == 1\n"
            "    assert lines(result)[-1] == (\n"
            "        f\"Refused: {EVALUATION}/gold/{FIRST_FILE}.toml holds other content; a\"\n"
            "        \" changed record is a new version, never an edit\"\n"
            "    )\n"
            "    assert anchored.read_bytes() == committed.read_bytes()\n"
            "\n"
            "\n"
            "def test_gold_validate_checks_every_text_the_guard_reads(repo) -> None:\n"
            "    \"\"\"P9-21: gold validate rechecks committed gold against every text the committed\n"
            "    guard reads, not only its own release.\"\"\"\n"
            "    frozen(repo)\n"
            "    write_drafts(repo, FIRST, gold_draft(), gold_draft(annotator=SIGNED))\n"
            "    assert run(repo, \"gold\", \"anchor\", FIRST).exit_code == 0\n"
            "    committed = repo / EVALUATION / \"gold\" / f\"{FIRST_FILE}.toml\"\n"
            "    other = first_fixture(repo)\n"
            "    record = tomlfile.read(committed)\n"
            "    copied = unique_window(guarded_texts(repo), other)\n"
            "    record[\"claims\"][0][\"claim\"] = f\"Ours: {copied}\"\n"
            "    committed.write_text(tomlfile.dumps(record), encoding=\"utf-8\")\n"
            "    result = run(repo, \"gold\", \"validate\", FIRST)\n"
            "    assert result.exit_code == 1\n"
            "    assert f\"refused: {FIRST} claims[0].claim ({other}): source_wording\" in lines(\n"
            "        result\n"
            "    )\n"
            "\n"
            "\n"
            "def test_a_blank_signature_commits_nothing(repo) -> None:\n"
            "    \"\"\"P9-18: whitespace is not a signature, to the anchor as to the validator.\"\"\"\n"
            "    frozen(repo)\n"
            "    write_drafts(repo, FIRST, gold_draft(), gold_draft(annotator=\"   \"))\n"
            "    result = run(repo, \"gold\", \"anchor\", FIRST)\n"
            "    assert result.exit_code == 0, result.output\n"
            "    assert lines(result)[-1] == (\n"
            "        f\"unsigned: {FIRST} is not committed until the working copy's annotator\"\n"
            "        \" is signed\"\n"
            "    )\n"
            "    assert not (repo / EVALUATION / \"gold\").exists()\n"
            "\n"
            "\n"
            "def test_a_draft_origin_is_derived_from_the_working_copy(repo) -> None:\n"
            "    frozen(repo)\n"
            "    working = gold_draft(\n"
            "        claims=[{\"claim_id\": \"c1\", \"quote_ids\": [\"q1\"], \"claim\": \"Sales grew.\"}],\n"
            "    )\n"
            "    write_drafts(repo, FIRST, gold_draft(), working)\n"
            "    result = run(repo, \"gold\", \"anchor\", FIRST, \"--check\")\n"
            "    assert result.exit_code == 0, result.output\n"
            "    assert lines(result)[1:] == [\n"
            "        \"origins: accepted 2, edited 1, rejected 0, added 0\",\n"
            "        f\"checked {FIRST}: nothing written\",\n"
            "    ]\n"
            "    assert not (repo / \"data\" / \"runs\" / \"gold\" / \"anchored\").exists()\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\n"
            "    (\"change\", \"refusals\"),\n"
            "    [\n"
            "        (\n"
            "            {\n"
            "                \"quotes\": [\n"
            "                    {\"quote_id\": \"q1\", \"text\": SENTENCE},\n"
            "                    {\"quote_id\": \"q2\", \"text\": \"Net sales\\t1,000\"},\n"
            "                    {\"quote_id\": \"q3\", \"text\": \"An invented sentence found nowhere.\"},\n"
            "                ]\n"
            "            },\n"
            "            [\n"
            "                \"refused: quote q2: not_narrative\",\n"
            "                \"refused: quote q3: locator_not_found\",\n"
            "            ],\n"
            "        ),\n"
            "        (\n"
            "            {\n"
            "                \"claims\": [\n"
            "                    {\n"
            "                        \"claim_id\": \"c1\",\n"
            "                        \"quote_ids\": [\"q1\"],\n"
            "                        \"claim\": f\"Acme Industrial Corp {SENTENCE} for the quarter.\",\n"
            "                    }\n"
            "                ]\n"
            "            },\n"
            "            [f\"refused: claims[0].claim ({SECOND}): source_wording\"],\n"
            "        ),\n"
            "        (\n"
            "            {\"no_theme\": True},\n"
            "            [\"refused: no_theme: no_theme_mismatch\"],\n"
            "        ),\n"
            "    ],\n"
            ")\n"
            "def test_a_bad_gold_draft_is_refused_by_item_and_writes_nothing(\n"
            "    repo, change, refusals\n"
            ") -> None:\n"
            "    frozen(repo)\n"
            "    write_drafts(repo, SECOND, gold_draft(SECOND, **change))\n"
            "    result = run(repo, \"gold\", \"anchor\", SECOND)\n"
            "    assert result.exit_code == 1\n"
            "    assert lines(result) == [\n"
            "        *refusals,\n"
            "        f\"Refused: {len(refusals)} problem(s); nothing written\",\n"
            "    ]\n"
            "    assert not (repo / \"data\" / \"runs\" / \"gold\" / \"anchored\").exists()\n"
            "\n"
            "\n"
            "def test_gold_is_refused_for_an_excluded_or_unparsed_event(repo) -> None:\n"
            "    frozen(repo)\n"
            "    excluded = run(repo, \"gold\", \"anchor\", EXCLUDED)\n"
            "    assert lines(excluded) == [f\"Refused: {EXCLUDED} is excluded, so it has no gold\"]\n"
            "    unparsed = run(repo, \"gold\", \"anchor\", UNPARSED[0])\n"
            "    assert lines(unparsed) == [\n"
            "        f\"Refused: {UNPARSED[0]} is not a pilot event with a parsed document\"\n"
            "    ]\n"
            "\n"
            "\n"
            "def test_a_draft_that_is_not_toml_is_named_never_quoted(repo) -> None:\n"
            "    frozen(repo)\n"
            "    folder = repo / DRAFTS\n"
            "    for kind in (\"draft\", \"working\"):\n"
            "        (folder / f\"{FIRST_FILE}.{kind}.toml\").write_text(\n"
            "            \"quotes = [\\n\", encoding=\"utf-8\"\n"
            "        )\n"
            "    result = run(repo, \"gold\", \"anchor\", FIRST)\n"
            "    assert lines(result) == [\n"
            "        f\"problem: {FIRST_FILE}.draft.toml: not TOML at line 2, column 1\",\n"
            "        f\"Refused: {FIRST_FILE}.draft.toml does not read as its record\",\n"
            "    ]\n"
            "\n"
            "\n"
            "def test_curated_hard_negatives_commit_once_signed(repo) -> None:\n"
            "    frozen(repo)\n"
            "    bundles = fixtures(repo)\n"
            "    write_drafts(\n"
            "        repo,\n"
            "        \"hard-negatives\",\n"
            "        curated_draft(bundles),\n"
            "        curated_draft(bundles, SIGNED),\n"
            "    )\n"
            "    result = run(repo, \"gold\", \"anchor\", \"--hard-negatives\")\n"
            "    assert result.exit_code == 0, result.output\n"
            "    assert lines(result) == [\n"
            "        \"hard-negatives: 2 fixtures, 4 hard negatives (issuer 1, period 2, section 1)\",\n"
            "        \"origins: accepted 8, edited 0, rejected 0, added 0\",\n"
            "        \"anchored  data/runs/gold/anchored/hard-negatives.toml\",\n"
            "        \"froze tests/fixtures/gold/hard-negatives.toml\",\n"
            "    ]\n"
            "    record = load_hard_negatives(\n"
            "        repo / \"tests\" / \"fixtures\" / \"gold\" / \"hard-negatives.toml\"\n"
            "    )\n"
            "    assert record.annotator == SIGNED\n"
            "    valid = run(repo, \"gold\", \"validate\", \"--hard-negatives\")\n"
            "    assert lines(valid) == [\n"
            "        \"valid: hard-negatives, 2 fixtures, 4 hard negatives, signed\"\n"
            "    ]\n"
            "    views = run(repo, \"gold\", \"show\", \"--hard-negatives\")\n"
            "    assert len(lines(views)) == 2\n"
            "\n"
            "\n"
            "def test_curated_hard_negatives_are_checked_against_the_pilot_before_a_write(\n"
            "    repo,\n"
            ") -> None:\n"
            "    \"\"\"P9-21: the builder checks the curated set against the Stage 1 fixtures, and\n"
            "    the anchor checks it against every pilot release as well, before it writes\n"
            "    anything. Only a pilot ID in the refusal shows that the second check ran.\"\"\"\n"
            "    frozen(repo)\n"
            "    bundles = fixtures(repo)\n"
            "    name, copied = a_pilot_window(guarded_texts(repo))\n"
            "    drafted, working = curated_draft(bundles), curated_draft(bundles, SIGNED)\n"
            "    for draft in (drafted, working):\n"
            "        draft[\"documents\"][0][\"hard_negatives\"][0][\"claim\"] = f\"Ours: {copied}\"\n"
            "    write_drafts(repo, \"hard-negatives\", drafted, working)\n"
            "    result = run(repo, \"gold\", \"anchor\", \"--hard-negatives\")\n"
            "    assert result.exit_code == 1\n"
            "    assert [line for line in lines(result) if line.startswith(\"refused: \")] == [\n"
            "        f\"refused: documents[0].hard_negatives[0].claim ({name}): source_wording\"\n"
            "    ]\n"
            "    assert not (repo / \"tests\" / \"fixtures\" / \"gold\").exists()\n"
            "    assert not (repo / \"data\" / \"runs\" / \"gold\" / \"anchored\").exists()\n"
            "\n"
            "\n"
            "def test_texts_for_drafting_are_written_only_under_data_runs_gold(repo) -> None:\n"
            "    assert run(repo, \"pilot\", \"split\").exit_code == 0\n"
            "    result = run(repo, \"gold\", \"show\", \"--text\", \"--training\", \"--hard-negatives\")\n"
            "    assert lines(result) == [\"wrote 19 texts under data/runs/gold/texts\"]\n"
            "    folder = repo / \"data\" / \"runs\" / \"gold\" / \"texts\"\n"
            "    assert len(list(folder.glob(\"*.md\"))) == 11\n"
            "    assert len(list((folder / \"fixtures\").glob(\"*.md\"))) == 8\n"
            "    assert f\"{FIRST_FILE}.md\" in {p.name for p in folder.glob(\"*.md\")}\n"
            "    refused = run(repo, \"gold\", \"show\", \"--training\")\n"
            "    assert lines(refused) == [\"Refused: --training writes texts; add --text\"]\n"
            "\n"
            "\n"
            "def test_an_unforeseen_error_is_named_by_type_never_by_message(\n"
            "    repo, monkeypatch\n"
            ") -> None:\n"
            "    \"\"\"GS13: an exception's message may quote a document, so it is withheld.\"\"\"\n"
            "    frozen(repo)\n"
            "    write_drafts(repo, FIRST, gold_draft())\n"
            "\n"
            "    def broken(*args, **kwargs):\n"
            "        raise ValueError(f\"Acme Industrial Corp {SENTENCE} for the quarter\")\n"
            "\n"
            "    monkeypatch.setattr(gold_cli, \"build_gold\", broken)\n"
            "    result = run(repo, \"gold\", \"anchor\", FIRST)\n"
            "    assert result.exit_code == 1\n"
            "    assert lines(result) == [\n"
            "        (\n"
            "            \"Refused: an unforeseen ValueError; its message is withheld, since it\"\n"
            "            \" may quote a document (GS13)\"\n"
            "        )\n"
            "    ]\n"
            "\n"
            "\n"
            "def test_a_drafting_session_checks_its_draft_alone(repo) -> None:\n"
            "    frozen(repo)\n"
            "    folder = repo / DRAFTS\n"
            "    (folder / f\"{FIRST_FILE}.draft.toml\").write_text(\n"
            "        tomlfile.dumps(gold_draft()), encoding=\"utf-8\"\n"
            "    )\n"
            "    result = run(repo, \"gold\", \"anchor\", FIRST, \"--check\")\n"
            "    assert result.exit_code == 0, result.output\n"
            "    assert lines(result)[0] == (\n"
            "        f\"checking the draft alone: {FIRST} has no working copy yet\"\n"
            "    )\n"
            "    assert lines(result)[-1] == f\"checked {FIRST}: nothing written\"\n"
            "    assert not (folder / f\"{FIRST_FILE}.working.toml\").exists()\n"
            "    unchecked = run(repo, \"gold\", \"anchor\", FIRST)\n"
            "    assert unchecked.exit_code == 1\n"
            "    assert lines(unchecked)[-1].startswith(f\"Refused: {FIRST}: data/runs/gold/drafts/\")\n"
            "\n"
            "\n"
            "def test_committed_gold_is_named_for_its_event_without_a_colon(repo) -> None:\n"
            "    \"\"\"P9-3: Git on Windows cannot check out a path with a colon, so each file\n"
            "    named for an event writes it as an underscore; the ID inside is unchanged, and\n"
            "    a file named for another event is refused.\"\"\"\n"
            "    frozen(repo)\n"
            "    write_drafts(repo, FIRST, gold_draft(), gold_draft(annotator=SIGNED))\n"
            "    assert run(repo, \"gold\", \"anchor\", FIRST).exit_code == 0\n"
            "    folder = repo / EVALUATION / \"gold\"\n"
            "    assert [p.name for p in folder.iterdir()] == [f\"{FIRST_FILE}.toml\"]\n"
            "    assert not any(\":\" in p.name for p in (repo / \"data\" / \"runs\" / \"gold\").rglob(\"*\"))\n"
            "    (folder / f\"{FIRST_FILE}.toml\").rename(folder / \"cik-0009990001_2024-11-30.toml\")\n"
            "    result = run(repo, \"gold\", \"validate\")\n"
            "    assert lines(result) == [\n"
            "        (\n"
            "            \"Refused: evaluation/djia-synthetic/pilot-v1/gold/\"\n"
            "            f\"cik-0009990001_2024-11-30.toml holds the gold of {FIRST}\"\n"
            "        )\n"
            "    ]\n"
            "\n"
            "\n"
            "@pytest.mark.parametrize(\n"
            "    (\"partition\", \"frozen\", \"reason\"),\n"
            "    [\n"
            "        (Partition.TRAIN, False, None),\n"
            "        (\n"
            "            Partition.DEV,\n"
            "            False,\n"
            "            \"is a dev bundle, which waits for codebook v0's approval (GS13)\",\n"
            "        ),\n"
            "        (Partition.DEV, True, None),\n"
            "        (Partition.TEST, True, \"is a test bundle, which waits for Stage 14 (GS18)\"),\n"
            "        (Partition.EXCLUDED, True, \"is excluded, so it has no gold\"),\n"
            "    ],\n"
            ")\n"
            "def test_a_dev_or_test_bundle_waits_its_turn(partition, frozen, reason) -> None:\n"
            "    \"\"\"GS13 and GS18 in code: no text of a dev bundle before codebook v0, and none\n"
            "    of a test bundle in Stage 6.\"\"\"\n"
            "    assert gold_cli.readable(partition, frozen) == reason\n"
            "\n"
            "\n"
            "def test_no_text_is_written_for_an_excluded_event(repo) -> None:\n"
            "    assert run(repo, \"pilot\", \"split\").exit_code == 0\n"
            "    result = run(repo, \"gold\", \"show\", \"--text\", EXCLUDED)\n"
            "    assert lines(result) == [f\"Refused: {EXCLUDED} is excluded, so it has no gold\"]\n"
            "    assert not (repo / \"data\" / \"runs\" / \"gold\" / \"texts\").exists()\n",
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

Write them:

```bash
python3 /tmp/plan9-extract.py /tmp/plan9-task12-tests.py && python3 /tmp/plan9-task12-tests.py
```

Expected:

```text
extracted /tmp/plan9-task12-tests.py: 494 lines
edited apps/earnings-pipeline/tests/test_stage6_cli.py: 10 replacement(s)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q`

Expected: FAIL, `1 error`, with:

```text
ImportError: cannot import name 'gold_cli' from 'earnings_pipeline'
ERROR apps/earnings-pipeline/tests/test_stage6_cli.py
```

- [x] **Step 3: Write the gold commands**

Create `apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py`:

```python
"""``earnings-pipeline gold``: anchoring, views, and validation of Stage 6's gold
(the Stage 6 spec, §Anchoring and validation and §Drafting and tools; GS4, GS5,
GS13; plan 9).

    uv run --locked earnings-pipeline gold show --text --training
    uv run --locked earnings-pipeline gold anchor cik-0000051143:2024-12-31
    uv run --locked earnings-pipeline gold show cik-0000051143:2024-12-31
    uv run --locked earnings-pipeline gold validate

A drafting session writes ``data/runs/gold/drafts/<name>.draft.toml``, which stays
unchanged, and the user edits ``<name>.working.toml`` beside it; ``<name>`` is an
event's ``file_stem``, such as ``cik-0000051143_2024-12-31``, or ``hard-negatives``
for the curated set. ``anchor`` anchors the working copy and writes the result to
``data/runs/gold/anchored/<name>.toml``; once the
working copy is signed, it also writes the committed record, once. Before either
write it checks the record against every text the committed wording guard reads,
and a signed record that differs from the one already written is refused before
anything changes. ``show`` writes
the local views and texts the user and the drafting sessions open. ``validate``
rechecks committed records against their local documents. No command prints a
document's text (GS13).
"""

from pathlib import Path
from typing import Annotated

import tomllib
import typer
from earnings_themes.anchoring import Bundle
from earnings_themes.annotation import (
    build_curated,
    build_gold,
    load_curated_draft,
    load_gold_draft,
    signed,
    validate_curated,
    validate_gold,
)
from earnings_themes.codebook import Codebook
from earnings_themes.gold import (
    DraftCounts,
    Gold,
    HardNegativeSet,
    gold_toml,
    load_gold,
    load_hard_negatives,
)
from earnings_themes.records import RecordError
from earnings_themes.split import Partition, SplitManifest
from earnings_themes.view import render_curated_view, render_text, render_view

from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
from earnings_pipeline.stage6 import (
    CODEBOOK_FILE,
    FIXTURE_MANIFEST,
    HARD_NEGATIVES,
    Layout,
    Pinned,
    documents,
    fail,
    file_stem,
    guarded,
    load_bundle,
    load_fixture,
    load_pinned,
    options,
    record_error,
    refuse,
    replace,
    wording_refusals,
    wording_texts,
    write_once,
)

gold = typer.Typer(no_args_is_help=True, help="Stage 6's gold set.")
gold.callback()(options)
CURATED = "hard-negatives"

Events = Annotated[list[str] | None, typer.Argument(help="Event IDs.")]
Curated = Annotated[
    bool, typer.Option("--hard-negatives", help="The curated hard negatives.")
]


def fixture_bundles(layout: Layout) -> dict[str, Bundle]:
    """Stage 1's canonical fixtures, by the IDs the fixtures' manifest lists."""
    path = layout.repo / FIXTURE_MANIFEST
    try:
        fixtures = tomllib.loads(path.read_text(encoding="utf-8"))["fixtures"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        fail(f"Refused: {layout.shown(path)} does not list Stage 1's fixtures")
    ids = sorted(fixture["fixture_id"] for fixture in fixtures)
    return {fixture_id: load_fixture(layout, fixture_id) for fixture_id in ids}


def readable(partition: Partition, codebook_frozen: bool) -> str | None:
    """Why an event's text or gold may not be touched yet, or ``None``. No session
    reads a dev bundle before codebook v0 is approved, or a test bundle before Stage
    14 freezes its configuration (GS13, GS18); an excluded event has no gold (GS7)."""
    if partition is Partition.EXCLUDED:
        return "is excluded, so it has no gold"
    if partition is Partition.TEST:
        return "is a test bundle, which waits for Stage 14 (GS18)"
    if partition is Partition.DEV and not codebook_frozen:
        return "is a dev bundle, which waits for codebook v0's approval (GS13)"
    return None


def _open(layout: Layout, split: SplitManifest, event_id: str) -> None:
    """Refuse an event outside the split, or one ``readable`` holds back."""
    try:
        partition = split.partition_of(event_id)
    except KeyError:
        fail(f"Refused: {event_id} is not in the split")
    reason = readable(partition, (layout.repo / CODEBOOK_FILE).is_file())
    if reason is not None:
        fail(f"Refused: {event_id} {reason}")


def _drafts(layout: Layout, name: str, check: bool) -> tuple[Path, Path]:
    """The kept draft and the working copy. ``--check`` without a working copy
    checks the draft alone, as a drafting session checks its own."""
    drafted = layout.drafts / f"{file_stem(name)}.draft.toml"
    working = layout.drafts / f"{file_stem(name)}.working.toml"
    if check and drafted.is_file() and not working.is_file():
        typer.echo(f"checking the draft alone: {name} has no working copy yet")
        working = drafted
    for path in (drafted, working):
        if not path.is_file():
            fail(
                f"Refused: {name}: {layout.shown(path)} is not here; a drafting"
                " session writes the draft, and the working copy starts as a copy"
                " of it"
            )
    return drafted, working


def _counts(counts: DraftCounts) -> str:
    return (
        f"accepted {counts.accepted}, edited {counts.edited}, rejected"
        f" {counts.rejected}, added {counts.added}"
    )


def _write(
    layout: Layout, name: str, text: str, committed: Path, is_signed: bool, check: bool
) -> None:
    if check:
        typer.echo(f"checked {name}: nothing written")
        return
    if is_signed and committed.is_file() and committed.read_bytes() != text.encode():
        fail(
            f"Refused: {layout.shown(committed)} holds other content; a changed"
            " record is a new version, never an edit"
        )
    anchored = layout.gold_runs / "anchored" / f"{file_stem(name)}.toml"
    replace(anchored, text)
    typer.echo(f"anchored  {layout.shown(anchored)}")
    if not is_signed:
        typer.echo(
            f"unsigned: {name} is not committed until the working copy's annotator"
            " is signed"
        )
        return
    created = write_once(committed, text.encode(), layout)
    typer.echo(f"{'froze' if created else 'unchanged:'} {layout.shown(committed)}")


def _anchor_event(
    layout: Layout,
    pinned: Pinned,
    codebook: Codebook,
    doc_ids: dict[str, str],
    texts: dict[str, str],
    event_id: str,
    check: bool,
) -> None:
    split = pinned_split(layout, pinned)
    _open(layout, split, event_id)
    bundle = load_bundle(layout, doc_ids, event_id)
    drafted_path, working_path = _drafts(layout, event_id, check)
    try:
        drafted = load_gold_draft(drafted_path)
        working = load_gold_draft(working_path)
    except RecordError as error:
        record_error(error)
    made = build_gold(
        drafted, working, bundle=bundle, pin=pinned.pin, split=split, codebook=codebook
    )
    if isinstance(made, list):
        refuse(made)
    if found := wording_refusals(made, texts):
        refuse(found)
    typer.echo(
        f"{event_id} ({made.partition}): {len(made.quotes)} quotes, {len(made.claims)}"
        f" claims, {len(made.assignments)} assignments, {len(made.hard_negatives)}"
        f" hard negatives; no_theme {str(made.no_theme).lower()}"
    )
    typer.echo(f"origins: {_counts(made.counts)}")
    committed = pinned.gold_dir / f"{file_stem(event_id)}.toml"
    _write(layout, event_id, gold_toml(made), committed, signed(made.annotator), check)


def _anchor_curated(
    layout: Layout,
    pinned: Pinned,
    codebook: Codebook,
    texts: dict[str, str],
    check: bool,
) -> None:
    drafted_path, working_path = _drafts(layout, CURATED, check)
    try:
        drafted = load_curated_draft(drafted_path)
        working = load_curated_draft(working_path)
    except RecordError as error:
        record_error(error)
    bundles = fixture_bundles(layout)
    made = build_curated(
        drafted, working, bundles=bundles, pin=pinned.pin, codebook=codebook
    )
    if isinstance(made, list):
        refuse(made)
    if found := wording_refusals(made, texts):
        refuse(found)
    negatives = [n for d in made.documents for n in d.hard_negatives]
    kinds = ", ".join(
        f"{kind} {sum(1 for n in negatives if n.negative_kind == kind)}"
        for kind in sorted({n.negative_kind for n in negatives})
    )
    typer.echo(
        f"{CURATED}: {len(made.documents)} fixtures, {len(negatives)} hard negatives"
        f" ({kinds})"
    )
    typer.echo(f"origins: {_counts(made.counts)}")
    committed = layout.repo / HARD_NEGATIVES
    _write(layout, CURATED, gold_toml(made), committed, signed(made.annotator), check)


@gold.command("anchor")
@guarded
def anchor_command(
    context: typer.Context,
    event_ids: Events = None,
    hard_negatives: Curated = False,
    check: Annotated[
        bool, typer.Option("--check", help="Anchor and check; write nothing.")
    ] = False,
) -> None:
    """Anchor each working copy; commit the record once it is signed."""
    layout: Layout = context.obj
    if not event_ids and not hard_negatives:
        fail("Refused: name the events to anchor, or --hard-negatives")
    codebook = pinned_codebook(layout)
    pinned = load_pinned(layout)
    texts = wording_texts(layout, pinned)
    if hard_negatives:
        _anchor_curated(layout, pinned, codebook, texts, check)
    if event_ids:
        doc_ids = documents(layout, pinned)
        for event_id in event_ids:
            _anchor_event(layout, pinned, codebook, doc_ids, texts, event_id, check)


def _latest(layout: Layout, name: str, committed: Path) -> Path:
    anchored = layout.gold_runs / "anchored" / f"{file_stem(name)}.toml"
    for path in (anchored, committed):
        if path.is_file():
            return path
    fail(f"Refused: {name} is not anchored: run gold anchor")


def _show_texts(
    layout: Layout,
    pinned: Pinned,
    event_ids: list[str],
    training: bool,
    hard_negatives: bool,
) -> None:
    written = 0
    if event_ids or training:
        doc_ids = documents(layout, pinned)
        split = pinned_split(layout, pinned)
        if training:
            event_ids = [
                e for e in split.events_in(Partition.TRAIN) if e in doc_ids
            ] + event_ids
        for event_id in dict.fromkeys(event_ids):
            _open(layout, split, event_id)
            bundle = load_bundle(layout, doc_ids, event_id)
            path = layout.gold_runs / "texts" / f"{file_stem(event_id)}.md"
            replace(path, render_text(bundle))
            written += 1
    if hard_negatives:
        for fixture_id, bundle in fixture_bundles(layout).items():
            path = layout.gold_runs / "texts" / "fixtures" / f"{fixture_id}.md"
            replace(path, render_text(bundle))
            written += 1
    texts = "text" if written == 1 else "texts"
    typer.echo(
        f"wrote {written} {texts} under {layout.shown(layout.gold_runs / 'texts')}"
    )


@gold.command("show")
@guarded
def show_command(
    context: typer.Context,
    event_ids: Events = None,
    text: Annotated[
        bool, typer.Option("--text", help="Write texts for drafting, not views.")
    ] = False,
    training: Annotated[
        bool, typer.Option("--training", help="With --text: every training event.")
    ] = False,
    hard_negatives: Curated = False,
) -> None:
    """Write local views (or, with --text, texts) under data/runs/gold/."""
    layout: Layout = context.obj
    event_ids = event_ids or []
    if training and not text:
        fail("Refused: --training writes texts; add --text")
    if not event_ids and not training and not hard_negatives:
        fail("Refused: name the events to show, or --training, or --hard-negatives")
    pinned = load_pinned(layout)
    if text:
        _show_texts(layout, pinned, event_ids, training, hard_negatives)
        return
    views = layout.gold_runs / "views"
    if hard_negatives:
        path = _latest(layout, CURATED, layout.repo / HARD_NEGATIVES)
        try:
            curated = load_hard_negatives(path)
        except RecordError as error:
            record_error(error)
        bundles = fixture_bundles(layout)
        for document in curated.documents:
            bundle = bundles.get(document.fixture_id)
            if bundle is None:
                fail(f"Refused: {document.fixture_id} is not a Stage 1 fixture")
            out = views / CURATED / f"{document.fixture_id}.md"
            replace(out, render_curated_view(bundle, document))
            typer.echo(f"view  {layout.shown(out)}")
    if event_ids:
        doc_ids = documents(layout, pinned)
        split = pinned_split(layout, pinned)
        for event_id in event_ids:
            _open(layout, split, event_id)
            committed = pinned.gold_dir / f"{file_stem(event_id)}.toml"
            path = _latest(layout, event_id, committed)
            try:
                record = load_gold(path)
            except RecordError as error:
                record_error(error)
            bundle = load_bundle(layout, doc_ids, event_id)
            out = views / f"{file_stem(event_id)}.md"
            replace(out, render_view(bundle, record))
            typer.echo(f"view  {layout.shown(out)}")


def _validate_event(
    layout: Layout,
    pinned: Pinned,
    codebook: Codebook,
    doc_ids: dict[str, str],
    texts: dict[str, str],
    path: Path,
) -> int:
    try:
        record: Gold = load_gold(path)
    except RecordError as error:
        record_error(error)
    if path.stem != file_stem(record.event_id):
        fail(f"Refused: {layout.shown(path)} holds the gold of {record.event_id}")
    split = pinned_split(layout, pinned)
    bundle = load_bundle(layout, doc_ids, record.event_id)
    refusals = validate_gold(
        record, bundle=bundle, pin=pinned.pin, split=split, codebook=codebook
    )
    found = wording_refusals(record, texts)
    refusals += [refusal for refusal in found if refusal not in refusals]
    for refusal in refusals:
        typer.echo(f"refused: {record.event_id} {refusal}", err=True)
    if not refusals:
        typer.echo(
            f"valid: {record.event_id} ({record.partition}), {len(record.quotes)}"
            f" quotes, {len(record.claims)} claims, signed"
        )
    return len(refusals)


def _validate_curated(layout: Layout, pinned: Pinned, codebook: Codebook) -> int:
    """Offline, so the default suite runs it: the wording is checked against Stage
    1's fixtures, which are committed; ``gold anchor`` checked it against the
    pilot's documents too, and the wording guard's local leg does."""
    path = layout.repo / HARD_NEGATIVES
    if not path.is_file():
        fail(f"Refused: {layout.shown(path)} is not committed")
    try:
        record: HardNegativeSet = load_hard_negatives(path)
    except RecordError as error:
        record_error(error)
    refusals = validate_curated(
        record, bundles=fixture_bundles(layout), pin=pinned.pin, codebook=codebook
    )
    for refusal in refusals:
        typer.echo(f"refused: {CURATED} {refusal}", err=True)
    if not refusals:
        negatives = sum(len(d.hard_negatives) for d in record.documents)
        typer.echo(
            f"valid: {CURATED}, {len(record.documents)} fixtures, {negatives} hard"
            " negatives, signed"
        )
    return len(refusals)


@gold.command("validate")
@guarded
def validate_command(
    context: typer.Context, event_ids: Events = None, hard_negatives: Curated = False
) -> None:
    """Recheck committed gold (every file, unless events are named)."""
    layout: Layout = context.obj
    codebook = pinned_codebook(layout)
    pinned = load_pinned(layout)
    problems = 0
    if hard_negatives:
        problems += _validate_curated(layout, pinned, codebook)
    if event_ids or not hard_negatives:
        if event_ids:
            paths = [pinned.gold_dir / f"{file_stem(e)}.toml" for e in event_ids]
            missing = [p for p in paths if not p.is_file()]
            if missing:
                fail(f"Refused: {layout.shown(missing[0])} is not committed")
        else:
            paths = sorted(pinned.gold_dir.glob("*.toml"))
            if not paths:
                typer.echo(f"no gold committed under {layout.shown(pinned.gold_dir)}")
        doc_ids = documents(layout, pinned) if paths else {}
        texts = wording_texts(layout, pinned) if paths else {}
        for path in paths:
            problems += _validate_event(layout, pinned, codebook, doc_ids, texts, path)
    if problems:
        fail(f"Refused: {problems} problem(s)")
```

Create `/tmp/plan9-task12-impl.py`:

```python
"""Plan 9: exact replacements for 3 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
"""

from pathlib import Path

EDITS = {
    "apps/earnings-pipeline/src/earnings_pipeline/cli.py": [
        (
            "(``earnings_pipeline.events_cli``). ``pilot`` and ``codebook`` hold Stage 6's (``pilot_cli`` and\n"
            "``codebook_cli``).\n",
            "(``earnings_pipeline.events_cli``). ``pilot``, ``codebook``, and ``gold`` hold Stage 6's\n"
            "(``pilot_cli``, ``codebook_cli``, and ``gold_cli``).\n",
        ),
        (
            "from earnings_pipeline.events_cli import events\n"
            "from earnings_pipeline.pilot_cli import pilot\n",
            "from earnings_pipeline.events_cli import events\n"
            "from earnings_pipeline.gold_cli import gold\n"
            "from earnings_pipeline.pilot_cli import pilot\n",
        ),
        (
            "app.add_typer(codebook, name=\"codebook\")\n"
            "\n",
            "app.add_typer(codebook, name=\"codebook\")\n"
            "app.add_typer(gold, name=\"gold\")\n"
            "\n",
        ),
    ],
    "docs/data-dictionary.md": [
        (
            "| `documents` | tuple of `FixtureDraft` | At least one |\n"
            "\n",
            "| `documents` | tuple of `FixtureDraft` | At least one |\n"
            "\n"
            "## Stage 6 files\n"
            "\n"
            "- **Committed, written once.** `evaluation/<corpus>/pilot-v<N>/split-v<M>.json`,\n"
            "  `coverage-v<M>.json`, and `gold/<event>.toml`; `codebooks/djia-pilot/\n"
            "  codebook-v<N>.toml`; and `tests/fixtures/gold/hard-negatives.toml`. A changed\n"
            "  record is a new version, never an edit.\n"
            "- **Local, never committed.** Under `data/runs/gold/`: `drafts/`, each draft kept\n"
            "  unchanged beside the user's working copy; `anchored/`, the latest build of each;\n"
            "  `views/`, the text with each quote marked, which the user verifies against; and\n"
            "  `texts/`, the text alone, which a drafting session reads. No command prints a\n"
            "  document's text (GS13).\n"
            "- **File names.** A file named for an event takes the event ID with its colon as an\n"
            "  underscore, `<event>`; the ID inside the file is unchanged.\n",
        ),
    ],
    "specs/pilot-codebook-split-and-gold-set-protocol.md": [
        (
            "One file per annotated bundle, `gold/<event_id>.toml`.\n",
            "One file per annotated bundle, `gold/<event>.toml`, where `<event>` is the event\n"
            "ID with its colon as an underscore, since Git on Windows cannot check out a path\n"
            "with a colon (amended by plan 9, P9-3).\n",
        ),
        (
            "- **View.** `gold show` writes `data/runs/gold/views/<event_id>.md`: the canonical\n",
            "- **View.** `gold show` writes `data/runs/gold/views/<event>.md`: the canonical\n",
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

Write them:

```bash
python3 /tmp/plan9-extract.py apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py
python3 /tmp/plan9-extract.py /tmp/plan9-task12-impl.py && python3 /tmp/plan9-task12-impl.py
```

Expected:

```text
extracted apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py: 443 lines
extracted /tmp/plan9-task12-impl.py: 75 lines
edited apps/earnings-pipeline/src/earnings_pipeline/cli.py: 3 replacement(s)
edited docs/data-dictionary.md: 1 replacement(s)
edited specs/pilot-codebook-split-and-gold-set-protocol.md: 2 replacement(s)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_stage6_cli.py -q`

Expected: `33 passed`.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py apps/earnings-pipeline/tests/test_stage6_cli.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1729 passed, 1 skipped, 24 deselected`; `All checks passed!` and `294 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/src/earnings_pipeline/gold_cli.py apps/earnings-pipeline/tests/test_stage6_cli.py docs/data-dictionary.md specs/pilot-codebook-split-and-gold-set-protocol.md
git commit -m "feat(pipeline): gold anchor, show, and validate, with colon-free names (GS4, P9-3)"
```

---

### Task 13: Pilot v1, the wording guard, and the briefs

S §The split, §Verification, §Wording guard, §Drafting and tools, GS3, GS13, and
P9-5. The integration tests check pilot v1's split through the command, and the
local legs, which skip visibly until a gate commits what they check. The wording
guard reads every committed Stage 6 file. The briefs are what a drafting session is
given: its task, what it may read, the draft's form, the rules, and how it checks
its own draft. Neither quotes a release, and the codebook brief lists the 20
training texts, from the split.

**Files:**

- Create: `evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md` and
  `gold.md`.
- Test: create `tests/integration/test_stage6_pilot_v1.py` and
  `tests/integration/test_stage6_wording.py`.

**Interfaces:**

- Consumes: Tasks 1 to 12, and the local store under `data/runs/events/`.
- Produces: the local legs that gates 1, 3, 4, and 5 run; and the two briefs, which
  Task 16 puts to the user and Tasks 17 to 19 hand to drafting sessions.

- [x] **Step 1: Write the failing tests**

> Deviation: by the user's choice of 2026-09-29, the wording guard's pilot leg loads each document in a guard that keeps only its event ID (`99e12f0`). After the final review, by the user's choice of 2026-10-03, it catches every exception rather than only `ValueError`, and guards its matching call the same way (`c77824a`).

Create `tests/integration/test_stage6_pilot_v1.py`:

```python
"""Stage 6 over the committed pilot v1 (the Stage 6 spec, §The pin, §The split, and
§The coverage report; GS2, GS10, P-C7): the pin's values, the split's counts and
exclusions, and that neither command changes a frozen record.

The split needs only committed files, so it runs everywhere; once gate 1 commits
it, the rebuild must reproduce it byte for byte. The coverage report, codebook v0,
and the gold are checked against the local store: those legs skip visibly without
it, and each gate runs this module with ``-rs``. Every assertion compares IDs,
counts, and hashes; none prints a document's text (GS13).
"""

import re
import shutil
from collections import Counter
from pathlib import Path

import pytest
from earnings_ingestion.events.coverage import build_coverage, load_coverage
from earnings_ingestion.events.freeze import serialize
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import DocumentState
from earnings_pipeline import cli
from earnings_pipeline.stage6 import (
    FIXTURE_MANIFEST,
    PILOT_V1,
    PILOT_V1_HASH,
    UNIVERSE_V1,
    Layout,
    file_stem,
    load_pinned,
)
from earnings_themes.split import Partition, load_split
from typer.testing import CliRunner

RUNNER = CliRunner()
REPO = Path(__file__).resolve().parents[2]
EVALUATION = REPO / "evaluation" / "djia-2024q3-2026q2" / "pilot-v1"
STATES = REPO / "data" / "runs" / "events" / "states"
EXCLUDED = [
    "cik-0000004962:2026-06-30",
    "cik-0000320187:2026-05-31",
    "cik-0000731766:2026-06-30",
    "cik-0000732712:2026-03-31",
    "cik-0001403161:2026-06-30",
]


def frozen_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted((root / "config").rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def split_run(tmp_path_factory: pytest.TempPathFactory):
    """``pilot split`` over a copy of the committed records."""
    root = tmp_path_factory.mktemp("repo")
    shutil.copytree(REPO / "config", root / "config")
    (root / FIXTURE_MANIFEST).parent.mkdir(parents=True)
    shutil.copy2(REPO / FIXTURE_MANIFEST, root / FIXTURE_MANIFEST)
    before = frozen_bytes(root)
    result = RUNNER.invoke(cli.app, ["pilot", "--repo", str(root), "split"])
    return root, before, result


def test_the_pin_is_pilot_v1_and_its_chain() -> None:
    pinned = load_pinned(Layout(REPO, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH))
    assert pinned.pin.model_dump() == {
        "pilot_id": "djia-2024q3-2026q2-pilot",
        "pilot_version": 1,
        "pilot_hash": PILOT_V1_HASH,
        "events_version": 1,
        "events_hash": (
            "2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7"
        ),
        "universe_version": 1,
        "universe_operative_hash": (
            "c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573"
        ),
    }
    assert pinned.evaluation == EVALUATION


def test_the_split_gives_the_spec_s_counts_and_exclusions(split_run) -> None:
    root, _, result = split_run
    assert result.exit_code == 0, result.output
    split = load_split(root / EVALUATION.relative_to(REPO) / "split-v1.json")
    counts = Counter(row.partition for row in split.rows)
    assert counts == {
        Partition.TRAIN: 20,
        Partition.DEV: 8,
        Partition.TEST: 7,
        Partition.EXCLUDED: 5,
    }
    assert split.events_in(Partition.EXCLUDED) == tuple(EXCLUDED)
    assert {row.reason for row in split.rows if row.reason} == {
        "issuer_in_earlier_partition"
    }
    pinned = load_pinned(Layout(REPO, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH))
    boundary = [
        row.event_id
        for row in pinned.pilot.rows
        if row.selection_reason == "membership_boundary"
    ]
    assert Counter(split.partition_of(e) for e in boundary) == {
        Partition.TRAIN: 2,
        Partition.EXCLUDED: 1,
    }


def test_the_split_changes_no_frozen_record(split_run) -> None:
    """P-C7: the split reads the pilot by path and writes only under evaluation/."""
    root, before, _ = split_run
    assert frozen_bytes(root) == before


def test_the_committed_split_reproduces_byte_for_byte(split_run) -> None:
    committed = EVALUATION / "split-v1.json"
    if not committed.is_file():
        pytest.skip("split-v1.json is frozen at gate 1")
    root, _, _ = split_run
    rebuilt = root / EVALUATION.relative_to(REPO) / "split-v1.json"
    assert rebuilt.read_bytes() == committed.read_bytes()


def test_the_committed_coverage_report_reproduces_from_its_runs() -> None:
    committed = EVALUATION / "coverage-v1.json"
    if not committed.is_file():
        pytest.skip("coverage-v1.json is frozen at gate 1")
    if not STATES.is_dir():
        pytest.skip("data/runs/events/ is not here: each Stage 6 gate runs this test")
    report = load_coverage(committed)
    pinned = load_pinned(Layout(REPO, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH))
    rebuilt = build_coverage(
        pinned.pilot,
        pinned.coverage_pin,
        read_runs(STATES),
        run_ids=report.run_ids,
    )
    assert serialize(rebuilt) == committed.read_bytes()
    assert report.documents == 40
    assert report.count(DocumentState.PARSED) == 40
    assert [gap.state for gap in report.gaps] == ["unavailable", "restricted", "failed"]
    assert [(o.override_id, o.verdict) for o in report.overrides] == [
        ("release-doc-dis-2026-03-28", "not_confirmed")
    ]


@pytest.mark.parametrize(
    ("group", "args", "needs"),
    [
        ("codebook", ["validate"], "codebooks/djia-pilot/codebook-v0.toml"),
        ("gold", ["validate"], "evaluation/djia-2024q3-2026q2/pilot-v1/gold"),
    ],
)
def test_committed_records_validate_against_the_local_store(
    group: str, args: list[str], needs: str
) -> None:
    if not (REPO / needs).exists():
        pytest.skip(f"{needs} is committed at a later gate")
    if not STATES.is_dir():
        pytest.skip("data/runs/events/ is not here: each Stage 6 gate runs this test")
    result = RUNNER.invoke(cli.app, [group, "--repo", str(REPO), *args])
    assert result.exit_code == 0, result.output
    assert result.output.startswith("valid: ") or "\nvalid: " in result.output


def test_the_codebook_brief_lists_exactly_the_training_releases(split_run) -> None:
    """The spec, §Drafting and tools: the brief lists the 20 training bundles'
    paths, taken from the split."""
    root, _, _ = split_run
    split = load_split(root / EVALUATION.relative_to(REPO) / "split-v1.json")
    brief = (EVALUATION / "briefs" / "codebook.md").read_text(encoding="utf-8")
    listed = re.findall(r"^- `data/runs/gold/texts/([^`/]+)\.md`$", brief, re.MULTILINE)
    assert listed == [file_stem(e) for e in split.events_in(Partition.TRAIN)]
    assert len(listed) == 20


def test_the_curated_hard_negatives_validate_offline() -> None:
    """Their fixtures' canonical text and codebook v0 are committed, so they are
    checked in the default suite, with no local store."""
    if not (REPO / "tests" / "fixtures" / "gold" / "hard-negatives.toml").is_file():
        pytest.skip("the curated hard negatives are committed at gate 4")
    result = RUNNER.invoke(
        cli.app, ["gold", "--repo", str(REPO), "validate", "--hard-negatives"]
    )
    assert result.exit_code == 0, result.output
    assert result.output.startswith("valid: hard-negatives, ")
```

Create `tests/integration/test_stage6_wording.py`:

```python
"""The Stage 6 wording guard (the Stage 6 spec, §Wording guard; F20's rule, as
``test_corpus_quotes.py`` applies it): no 40-character window of any string in a
committed Stage 6 file, dates masked, occurs in the canonical text of a pilot
document or of a Stage 1 fixture.

- **The files.** Under ``evaluation/``: the split, the coverage report, the gold,
  and the briefs; codebook v0 and ADR 0003; and the curated hard negatives:
  whichever are committed yet. A Markdown file is read a paragraph at a time, its
  lines joined, so a phrase copied across a wrapped line is still caught.
- **What a failure prints.** Each finding is a pair: the file with its field or
  paragraph, and the event or fixture. Never the window or the string, since either
  may quote a release (GS13).
- **Where it runs.** The fixture leg always runs. The pilot leg reads the pilot's
  canonical documents from the local store and skips visibly without it, so each
  gate runs this module with ``-rs`` and reads "passed". Never run it with ``-l``,
  ``--showlocals``, ``--pdb``, or ``-vv``, which print pilot text on a failure.
"""

import json
from pathlib import Path

import pytest
import tomllib
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_ingestion.events.coverage import parsed_documents
from earnings_ingestion.events.state_table import read_runs
from earnings_themes.wording import WIDTH, labelled_strings, markdown_paragraphs, shared

REPO = Path(__file__).resolve().parents[2]
PILOT_V1_HASH = "3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926"
EVENT_RUNS = REPO / "data" / "runs" / "events"
FIXTURES = REPO / "tests" / "fixtures" / "canonical"
STAGE6 = (
    "evaluation/*/pilot-v*/*.json",
    "evaluation/*/pilot-v*/gold/*.toml",
    "evaluation/*/pilot-v*/briefs/*.md",
    "codebooks/*/codebook-v*.toml",
    "docs/adr/0003-*.md",
    "tests/fixtures/gold/*.toml",
)
BRIEFS = (
    "evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md",
    "evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md",
)


def committed() -> list[Path]:
    return sorted({path for pattern in STAGE6 for path in REPO.glob(pattern)})


def strings(paths: list[Path]) -> list[tuple[str, str]]:
    """Each string of each file, labelled by the file and its field or paragraph."""
    found = []
    for path in paths:
        name = path.relative_to(REPO).as_posix()
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".md":
            found += markdown_paragraphs(text, name)
        elif path.suffix == ".toml":
            found += labelled_strings(tomllib.loads(text), name)
        else:
            found += labelled_strings(json.loads(text), name)
    return found


def fixture_texts() -> list[tuple[str, str]]:
    return [
        (
            path.stem,
            from_fixture_json(path.read_text(encoding="utf-8")).document.canonical_text,
        )
        for path in sorted(FIXTURES.glob("*.json"))
    ]


def test_the_briefs_are_among_the_files_checked() -> None:
    names = {path.relative_to(REPO).as_posix() for path in committed()}
    assert set(BRIEFS) <= names


def test_no_stage_6_file_quotes_a_stage_1_fixture() -> None:
    found = shared(strings(committed()), fixture_texts())
    assert found == set()


def test_no_stage_6_file_quotes_a_pilot_document() -> None:
    states = EVENT_RUNS / "states"
    if not states.is_dir():
        pytest.skip(
            "data/runs/events/ is not here: each Stage 6 gate runs this test with -rs"
        )
    doc_ids = parsed_documents(read_runs(states), PILOT_V1_HASH)
    assert len(doc_ids) == 40
    paths = {e: EVENT_RUNS / "canonical" / f"{d}.json" for e, d in doc_ids.items()}
    assert sorted(e for e, path in paths.items() if not path.is_file()) == []
    texts = [
        (e, from_fixture_json(path.read_text(encoding="utf-8")).document.canonical_text)
        for e, path in sorted(paths.items())
    ]
    found = shared(strings(committed()), texts)
    # Bound first: pytest's report of a failed assert shows each call's arguments,
    # and ``texts`` holds pilot text (GS13). ``found`` holds labels and IDs only.
    assert found == set()


@pytest.mark.parametrize(("width", "caught"), [(WIDTH, True), (WIDTH - 1, False)])
def test_a_copy_across_a_wrapped_line_is_caught(
    tmp_path: Path, width: int, caught: bool
) -> None:
    """A brief paragraph that copies 40 characters of a fixture, wrapped across two
    lines, is caught, and one that copies 39 is not. The copy is taken when the test
    runs, never typed here."""
    fixture_id, text = fixture_texts()[0]
    start = next(i for i in range(len(text)) if text[i : i + width].count(" ") >= 4)
    copied = text[start : start + width]
    assert "\n" not in copied
    cut = copied.index(" ", width // 2)
    brief = tmp_path / "brief.md"
    brief.write_text(
        f"# Brief\n\nOur words [{copied[:cut]}\n{copied[cut + 1 :]}] end here.\n",
        encoding="utf-8",
    )
    found = shared(
        markdown_paragraphs(brief.read_text(encoding="utf-8"), "brief"),
        [(fixture_id, text)],
    )
    assert found == ({("brief paragraph 2", fixture_id)} if caught else set())
```

Write them:

```bash
python3 /tmp/plan9-extract.py tests/integration/test_stage6_pilot_v1.py
python3 /tmp/plan9-extract.py tests/integration/test_stage6_wording.py
```

Expected:

```text
extracted tests/integration/test_stage6_pilot_v1.py: 190 lines
extracted tests/integration/test_stage6_wording.py: 127 lines
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py -q -rs`

Expected: FAIL, `2 failed, 7 passed, 5 skipped`, with:

```text
FileNotFoundError: [Errno 2] No such file or directory: 'evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md'
AssertionError: assert {'evaluation/...iefs/gold.md'} <= set()
```

- [x] **Step 3: Write the two briefs**

Create `evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md`:

````markdown
# Brief: drafting codebook v0

Stage 6 of the evidence-linked theme-extraction roadmap, under its spec's GS9 and
GS13. This brief carries all of the spec a drafting session needs. The user starts
this session fresh, with this brief. You draft; the user edits, cuts, and approves.
Nothing you write is committed.

## Your task

Read the 20 training releases listed at the end, and propose the themes a reader
would use to code what these releases say about the business: the subjects that
recur across issuers and quarters. Write one file,
`data/runs/gold/drafts/codebook.draft.toml`, in the form below. It is the pilot
codebook, not the final taxonomy, which stays open.

## What you may read

- This brief.
- The contracts and checks: `packages/earnings-themes/src/earnings_themes/`
  `codebook.py`, `anchoring.py`, `records.py`, and `tomlfile.py`.
- The 20 texts listed at the end, under `data/runs/gold/texts/`, which the user
  prepared.

Nothing else. Open no other file under `data/`, apart from your own draft: no
other draft, and no view, saved exhibit, or canonical document. Read no dev or test release, no gold, and nothing
under `prompts/`, and no code, prompt, or output of an extraction stage. Open no
spec, plan, roadmap, or decision record.

## The draft's form

TOML. The values below are invented, to show the form; none comes from a release.

```toml
codebook_id = "djia-pilot"
codebook_version = 0

[drafting_aid]
model_id = "claude-opus-5-5"
drafted_on = 2026-10-01

[rules]
multi_label = "A claim may take several themes, one assignment row for each."
boilerplate = "Text under a boilerplate mask may be quoted; its masks are recorded."

[[themes]]
theme_id = "demand.volume"
label = "Unit demand"
definition = "Statements about how many units customers bought or ordered."
inclusion_rules = ["Order, shipment, or unit growth or decline."]
exclusion_rules = ["Price changes alone."]
sector_applicability = "all"

[[themes.positive_examples]]
event_id = "cik-0000000000:2024-12-31"
text = "The exact words of one sentence in that release."

[[themes.hard_negatives]]
synthetic = true
text = "Average selling prices rose while volumes held flat."
```

- `theme_id` matches `^[a-z][a-z0-9_.-]*$` and is never reused. `unmatched` is
  reserved. A sub-theme names its parent in `parent_id`; a top-level theme omits it.
- `label`, `definition`, and each rule are your own words.
- Each theme has at least one inclusion rule, exclusion rule, positive example, and
  hard negative.
- `sector_applicability` is `"all"` or a list of your own tags, such as
  `["retail", "energy"]`, each matching `^[a-z][a-z0-9-]*$`. A tag names a kind of
  business, never an issuer (GS16).
- An example is either a pointer or synthetic:
  - A **pointer** gives `event_id` and `text`: the exact words of a narrative
    passage in that training release: a sentence, list item, footnote, heading, or
    paragraph, or part of one, never a table, a table cell, or a page header or
    footer. The text must occur exactly once in the release. When it repeats, add
    `prefix` and `suffix`, the exact text just before and just after it, so that the
    three together occur once.
  - A **synthetic** example sets `synthetic = true` and gives `text` in your own
    words, with no `event_id`. Use one where no training release has a clear case,
    as hard negatives often need.
- The draft has no `approval`. The user approves v0 in ADR 0003.

## Rules

- **No copying.** Apart from a pointer's `text`, `prefix`, and `suffix`, no string
  may share 40 characters, dates masked, with any release in the pilot or any Stage
  1 fixture, including releases you are not given. The freeze refuses one that does,
  by its field and the text's ID (`source_wording`). Pointer text never reaches a
  committed file: the freeze turns it into offsets and hashes.
- **Scope.** A theme describes what a release says, not what an issuer is: no
  industry classification, no issuer's name, no ticker.
- **Sizing.** Propose the themes the 20 releases support, and no theme for a subject
  only one release mentions. Say in your summary which themes you were least sure
  of. The user cuts freely, so prefer a clear, small set to a long one.

## Checking your draft

Run, from the repository root:

```bash
uv run --locked --all-packages earnings-pipeline codebook freeze --working data/runs/gold/drafts/codebook.draft.toml
```

It anchors every example in the training releases, checks every field, and prints
counts, the content hash, and each refusal by item and reason. It writes nothing.
Fix the draft until it prints no refusal. Never print a release's text into this
session's output; the command never does.

## When you finish

Tell the user the draft's path, how many themes and examples it has, and the check's
last lines. Do not create the working copy, write any other file, or commit.

## The 20 training releases

Taken from the frozen split, `split-v1.json`; each is one release's canonical text,
named by its event ID with the colon as an underscore.

- `data/runs/gold/texts/cik-0000004962_2024-09-30.md`
- `data/runs/gold/texts/cik-0000018230_2024-12-31.md`
- `data/runs/gold/texts/cik-0000050863_2024-09-28.md`
- `data/runs/gold/texts/cik-0000051143_2024-12-31.md`
- `data/runs/gold/texts/cik-0000066740_2025-03-31.md`
- `data/runs/gold/texts/cik-0000080424_2025-06-30.md`
- `data/runs/gold/texts/cik-0000089800_2024-12-31.md`
- `data/runs/gold/texts/cik-0000089800_2025-03-31.md`
- `data/runs/gold/texts/cik-0000093410_2025-03-31.md`
- `data/runs/gold/texts/cik-0000104169_2025-04-30.md`
- `data/runs/gold/texts/cik-0000200406_2024-12-29.md`
- `data/runs/gold/texts/cik-0000310158_2025-06-30.md`
- `data/runs/gold/texts/cik-0000320187_2024-08-31.md`
- `data/runs/gold/texts/cik-0000731766_2024-09-30.md`
- `data/runs/gold/texts/cik-0000886982_2024-12-31.md`
- `data/runs/gold/texts/cik-0001018724_2025-03-31.md`
- `data/runs/gold/texts/cik-0001045810_2024-10-27.md`
- `data/runs/gold/texts/cik-0001045810_2025-04-27.md`
- `data/runs/gold/texts/cik-0001403161_2024-09-30.md`
- `data/runs/gold/texts/cik-0001751788_2024-09-30.md`
````

Create `evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md`:

````markdown
# Brief: drafting gold

Stage 6 of the evidence-linked theme-extraction roadmap, under its spec's GS4, GS5,
GS13, and GS15. This brief carries all of the spec a drafting session needs. The
user starts this session fresh, with this brief, and names one task: one
bundle's gold, by its event ID, or the curated hard negatives. You draft; the user
verifies every item, adds what you missed, and signs. Nothing you write is
committed.

## Your task

- **One bundle's gold.** Read the one release the user names by its event ID, such
  as `cik-0000000000:2024-12-31`, whose text is
  `data/runs/gold/texts/cik-0000000000_2024-12-31.md`: file names write the colon as
  an underscore. Code what it says against codebook v0, and write
  `data/runs/gold/drafts/cik-0000000000_2024-12-31.draft.toml`.
- **The curated hard negatives.** Read Stage 1's fixture releases,
  `data/runs/gold/texts/fixtures/*.md`, and draft hard-negative claims over them, at
  least one each of `period`, `issuer`, and `section`. Write
  `data/runs/gold/drafts/hard-negatives.draft.toml`.

A test bundle is never drafted before Stage 14 freezes its configuration (GS18).
For one bundle's gold, before you open the release's text, find its row in the split,
`evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json`. If its `partition` is not
`train` or `dev`, say so and stop.

## What you may read

- This brief.
- The contracts and checks: `packages/earnings-themes/src/earnings_themes/`
  `gold.py`, `annotation.py`, `anchoring.py`, `codebook.py`, `records.py`, and
  `tomlfile.py`.
- The split, `evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json`, for the named
  event's partition.
- Codebook v0: `codebooks/djia-pilot/codebook-v0.toml`.
- The text your task names: the one release, for one bundle's gold, or
  `data/runs/gold/texts/fixtures/*.md`, for the curated hard negatives; and your own
  draft under `data/runs/gold/drafts/`.

Nothing else. Open no other file under `data/`: no other release, and no other
draft, working copy, anchored file, view, saved exhibit, or canonical document. Read
no gold, committed or local: nothing under
`evaluation/djia-2024q3-2026q2/pilot-v1/gold/` or `tests/fixtures/gold/`. From
`evaluation/djia-2024q3-2026q2/pilot-v1/`, open only `split-v1.json` and this brief.
Read nothing under `prompts/`, and no code, prompt, or output of an extraction stage.
Open no spec, plan, roadmap, or decision record.

## Terms

- A **quote** is evidence: the exact words of a passage in the release.
- A **claim** is interpretation: what the quotes say, in your own words.
- A **theme** is a codebook definition. An **assignment** connects a claim to a
  theme, with whether the claim's quotes support it under that theme.

## The draft's form

TOML. The values below are invented, to show the form; none comes from a release.

```toml
event_id = "cik-0000000000:2024-12-31"
annotator = ""
no_theme = false

[drafting_aid]
model_id = "claude-opus-5-5"
drafted_on = 2026-10-03

[release_identification]
label = "release"
note = "The issuer's own results for the named quarter."

[[quotes]]
quote_id = "q1"
text = "The exact words of one sentence in the release."

[[quotes]]
quote_id = "q2"
text = "Words that occur twice"
prefix = "Exact text just before "
suffix = " and just after."

[[claims]]
claim_id = "c1"
quote_ids = ["q1"]
claim = "Unit orders grew over the year before."

[[assignments]]
claim_id = "c1"
theme_id = "demand.volume"
support = "supports"

[[hard_negatives]]
claim_id = "n1"
quote_ids = ["q2"]
claim = "Orders grew in the quarter being reported."
negative_kind = "period"
theme_id = "demand.volume"
```

For the curated hard negatives the file lists fixtures instead:

```toml
annotator = ""

[drafting_aid]
model_id = "claude-opus-5-5"
drafted_on = 2026-10-03

[[documents]]
fixture_id = "0000000000-00-000000_ex-99-1"

[[documents.quotes]]
quote_id = "q1"
text = "The exact words of one sentence in that fixture."

[[documents.hard_negatives]]
claim_id = "n1"
quote_ids = ["q1"]
claim = "A claim these words seem to support, but do not."
negative_kind = "section"
theme_id = "demand.volume"
```

A fixture's ID is its text file's name, without `.md`.

## Rules

- **`annotator` stays blank.** The user signs after verifying; an unsigned file is
  never committed (GS4).
- **Quotes.** A quote's `text` is the exact words of a narrative passage: a sentence,
  list item, footnote, heading, or paragraph, or part of one; never a table, a table
  cell, or a page header or footer (GS15). Text under a boilerplate notice may be
  quoted. It must occur exactly once in the release, or exactly once with the
  `prefix` and `suffix` you give, the exact text just before and after it.
- **Claims** are your own words and rest on at least one quote. No claim or note may
  share 40 characters, dates masked, with any release in the pilot or any Stage 1
  fixture, including those you are not given; the anchor refuses one that does, by
  its field and the text's ID (`source_wording`).
- **Assignments.** One row per claim and theme. `theme_id` is a codebook v0 theme,
  or `unmatched` when none fits: never propose a new theme (R9.3). `support` is
  `supports`, `does_not_support`, or `uncertain`. When a claim could take one of
  several themes and you cannot choose, give each a row with the same `tie_group`.
- **`no_theme`** is true exactly when no row pairs a claim with a codebook theme
  under `supports`. The anchor checks it.
- **Hard negatives** are claims the quotes seem to support but do not, each with its
  `negative_kind`: `period`, another quarter's result; `issuer`, another company's;
  or `section`, a passage such as boilerplate or a forward-looking statement that
  reports no result. `theme_id` names the theme it would wrongly support, if any.
- **Release identification.** `release` when the document is this event's earnings
  release, for its issuer and its period; `not_release` when it is not, optionally
  with `true_accession` and `true_exhibit`, as facts; `ambiguous` when you cannot
  tell. The note is your reason, in your words.
- **Coverage.** Code every claim a careful reader would, not only the clearest. The
  user adds what you miss, and the count of added items is reported.

## Checking your draft

Run, from the repository root, with the event ID the user named:

```bash
uv run --locked --all-packages earnings-pipeline gold anchor <event_id> --check
```

or, for the curated hard negatives:

```bash
uv run --locked --all-packages earnings-pipeline gold anchor --hard-negatives --check
```

It anchors every quote, checks every item, and prints counts and each refusal by
item and reason. It writes nothing. Fix the draft until it prints no refusal. Never
print the release's text into this session's output; the command never does.

## When you finish

Tell the user the draft's path, its counts, and the check's last lines. Do not create
the working copy, write any other file, or commit.
````

Write them:

```bash
python3 /tmp/plan9-extract.py evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md
python3 /tmp/plan9-extract.py evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md
```

Expected:

```text
extracted evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md: 137 lines
extracted evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md: 177 lines
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py -q -rs`

Expected: `9 passed, 5 skipped`, the skips reading:

```text
SKIPPED [1] tests/integration/test_stage6_pilot_v1.py:122: split-v1.json is frozen at gate 1
SKIPPED [1] tests/integration/test_stage6_pilot_v1.py:131: coverage-v1.json is frozen at gate 1
SKIPPED [1] tests/integration/test_stage6_pilot_v1.py:162: codebooks/djia-pilot/codebook-v0.toml is committed at a later gate
SKIPPED [1] tests/integration/test_stage6_pilot_v1.py:162: evaluation/djia-2024q3-2026q2/pilot-v1/gold is committed at a later gate
SKIPPED [1] tests/integration/test_stage6_pilot_v1.py:185: the curated hard negatives are committed at gate 4
```

Each skip names the gate that commits what it checks.

- [x] **Step 5: Run the checks**

```bash
python3 /tmp/plan9-escapes.py tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `1738 passed, 6 skipped, 24 deselected`; `All checks passed!` and `296 files already formatted`.

- [x] **Step 6: Commit**

```bash
git log --oneline -3
git add evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py
git commit -m "test(stage6): pilot v1's split, the wording guard, and the drafting briefs"
```

---

### Task 14: Gate 1 — the split and the coverage report (gate)

S §Gates 1, §Order of work step 1, GS6, GS7, and GS8. Both records are built from
committed files and the state table; neither reads a document. The user reads the
counts, the excluded events, and the gaps before either is committed. The record,
`docs/verification/pilot-v1-gold-set.md`, starts here and gains a section at each
gate.

**Files:**

- Written by the commands: `evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json`
  and `coverage-v1.json`.
- Create: `docs/verification/pilot-v1-gold-set.md`.

**Interfaces:**

- Consumes: `pilot split` and `pilot coverage` (Task 10); the local legs (Task 13).
- Produces: the frozen split, which every later gate reads, and the frozen coverage
  report.

- [x] **Step 1: Probe the state**

```bash
git log --oneline -3 && git status --short
ls evaluation/djia-2024q3-2026q2/pilot-v1
```

Expected: the head is Task 13's commit, or a later one the user made; the status is
empty; and the listing shows `briefs` alone. Otherwise, resume from what exists:

| What exists | Go to |
| --- | --- |
| `split-v1.json` and `coverage-v1.json`, committed | Task 15 |
| either of them, uncommitted | Step 2. Steps 2 and 3 print `unchanged:` in place of `froze`; every other line is the same, and still a check. Then Step 4: nothing is committed before the user's yes. |
| neither | Step 2 |

- [x] **Step 2: Freeze the split**

```bash
uv run --locked earnings-pipeline pilot split; echo "exit $?"
```

Expected, checks, as the plan-time replay printed them:

```text
pilot djia-2024q3-2026q2-pilot v1  3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926
train  20
dev  8
test  7
excluded  5
excluded  cik-0000004962:2026-06-30  issuer_in_earlier_partition
excluded  cik-0000320187:2026-05-31  issuer_in_earlier_partition
excluded  cik-0000731766:2026-06-30  issuer_in_earlier_partition
excluded  cik-0000732712:2026-03-31  issuer_in_earlier_partition
excluded  cik-0001403161:2026-06-30  issuer_in_earlier_partition
froze split v1 by issuer-time/1
evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json  5c4a2f3c5ed9ffc2cf0065658ec4e75311220338cf9b3fe07802c0db9fcd0e53
exit 0
```

The rule and pilot v1 fix every line, so these are checks, the hash included. A
different count or excluded event stops the gate (S §The split).

- [x] **Step 3: Freeze the coverage report**

```bash
uv run --locked earnings-pipeline pilot coverage; echo "exit $?"
```

Expected, checks:

```text
pilot djia-2024q3-2026q2-pilot v1  3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926
parsed  40
gap  unavailable  (D4: never repaired by reselecting)
gap  restricted  (D4: never repaired by reselecting)
gap  failed  (D4: never repaired by reselecting)
override  release-doc-dis-2026-03-28  cik-0001744489:2026-03-28:release  not_confirmed
runs  acquire-20260928T153046989675Z, acquire-20260928T153714715420Z
froze coverage v1: 40 documents
evaluation/djia-2024q3-2026q2/pilot-v1/coverage-v1.json  7b1d8b8a10fa837e686addc6a60d43803782cc418f377efeb24e215d903f4060
exit 0
```

The report's hash depends on the two runs' IDs as well, which the state table fixes.

- [x] **Step 4 (gate): Put the split and the report to the user**

Put this to the user in chat, and wait for a clear yes:

> Gate 1. `pilot split` froze pilot v1's split under `issuer-time/1`: 20 train,
> 8 dev, 7 test, and 5 excluded, each excluded event the later event of an issuer
> the pilot holds twice across windows (`issuer_in_earlier_partition`):
> `cik-0000004962:2026-06-30`, `cik-0000320187:2026-05-31`,
> `cik-0000731766:2026-06-30`, `cik-0000732712:2026-03-31`, and
> `cik-0001403161:2026-06-30`. Two of the pilot's three membership-boundary events
> stay in train, and the third is excluded. `pilot coverage` counts all 40 documents `parsed`, states
> `unavailable`, `restricted`, and `failed` as coverage gaps citing D4, never
> repaired by reselecting, and names Disney's override,
> `release-doc-dis-2026-03-28`, with its `not_confirmed` verdict. Both files hold
> IDs, counts, and hashes only. May I commit them?

A no stops the task: the rule is GS6's, and a different outcome is a finding to
report, never a reason to edit the files. Keep the date of the user's yes for Step 6.
A session that resumes past this step without it asks the user for it.

- [x] **Step 5: Run the local legs**

```bash
uv run --locked --all-packages pytest tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py -q -rs
```

Expected, checks: `11 passed, 3 skipped`, and the skips read, in order:

```text
SKIPPED [1] tests/integration/test_stage6_pilot_v1.py:162: codebooks/djia-pilot/codebook-v0.toml is committed at a later gate
SKIPPED [1] tests/integration/test_stage6_pilot_v1.py:162: evaluation/djia-2024q3-2026q2/pilot-v1/gold is committed at a later gate
SKIPPED [1] tests/integration/test_stage6_pilot_v1.py:185: the curated hard negatives are committed at gate 4
```

The committed split reproduces byte for byte, and the coverage report from its runs.

- [x] **Step 6: Start the record**

Create `docs/verification/pilot-v1-gold-set.md`:

```markdown
# Pilot v1's codebook, split, and gold set: verification record

This record verifies roadmap Stage 6, which
`specs/pilot-codebook-split-and-gold-set-protocol.md` specifies and plan 9
(`specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md`) built. Each gate
appends its section as it closes. The record holds IDs, counts, hashes, and dates,
never a release's wording or a paraphrase of it (GS3, GS13).

## The pin

- **The pilot.** Pilot v1, `config/corpus/djia-2024q3-2026q2/pilot-v1.json`,
  `djia-2024q3-2026q2-pilot`, content hash
  `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926`: 40 events over
  33 issuers.
- **The events.** Events v1, `events-v1.json` beside it, content hash
  `2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7`.
- **The universe.** Universe v1,
  `config/universe/djia/manifests/djia-2024q3-2026q2-v1.json`, operative hash
  `c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573`.
- **What Stage 6 sent.** No SEC request, and no model call from code. The drafting
  sessions are listed at the end.

## Gate 1: the split and the coverage report

- **The split.** `evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json`, split v1 by
  `issuer-time/1`, content hash
  `5c4a2f3c5ed9ffc2cf0065658ec4e75311220338cf9b3fe07802c0db9fcd0e53`.
  - 20 train, 8 dev, 7 test, and 5 excluded.
  - Each excluded event is the later event of an issuer the pilot holds in an
    earlier partition (`issuer_in_earlier_partition`): `cik-0000004962:2026-06-30`,
    `cik-0000320187:2026-05-31`, `cik-0000731766:2026-06-30`,
    `cik-0000732712:2026-03-31`, and `cik-0001403161:2026-06-30`.
  - Two of the pilot's three `membership_boundary` events are in train, and the
    third is excluded. No event is a Stage 1 fixture's (P9-15).
- **The coverage report.** `coverage-v1.json`, coverage v1, content hash
  `7b1d8b8a10fa837e686addc6a60d43803782cc418f377efeb24e215d903f4060`.
  - It reads runs `acquire-20260928T153046989675Z` and
    `acquire-20260928T153714715420Z`.
  - All 40 documents are `parsed`.
  - `unavailable`, `restricted`, and `failed` are coverage gaps (D4), never
    repaired by reselecting.
  - One override applies: `release-doc-dis-2026-03-28`, on
    `cik-0001744489:2026-03-28:release`, with the verdict `not_confirmed`.
  - The no-theme count joins at Stage 11 for train and dev, and at Stage 14 for
    test.
- **The user's review.** The user read both on [GATE: date of Task 14's Step 4,
  YYYY-MM-DD], and approved them.
- **Checks.** The rebuilt split and report reproduce both files byte for byte. The
  local legs printed `11 passed, 3 skipped`, and the wording guard `5 passed`.
```

Extract it with `python3 /tmp/plan9-extract.py docs/verification/pilot-v1-gold-set.md`,
then fill its one slot, the date of Step 4's yes, and check:

```bash
grep -n '\[GATE' docs/verification/pilot-v1-gold-set.md
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs
```

Expected: nothing from `grep`, and `5 passed`.

- [x] **Step 7: Run the checks**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected, checks: `1740 passed, 4 skipped, 24 deselected`; `All checks passed!` and
`296 files already formatted`.

- [x] **Step 8: Commit**

```bash
git log --oneline -3
git add evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json evaluation/djia-2024q3-2026q2/pilot-v1/coverage-v1.json docs/verification/pilot-v1-gold-set.md
git commit -m "feat(evaluation): freeze pilot v1's split and coverage report (gate 1)"
```

---

### Task 15: Gate 2 — the backup (gate)

S §Gates 2, and GS12. `data/` holds the only copy of pilot v1's saved exhibits and
canonical documents, and every drafting session reads from it. The user keeps a
backup outside the repository before any drafting starts. Its location is the
user's, and is not recorded.

**Files:**

- Modify: `docs/verification/pilot-v1-gold-set.md`, by appending its section.

**Interfaces:**

- Consumes: Task 14's record.
- Produces: the backup's confirmation, which Tasks 16 to 19 require.

- [x] **Step 1: Probe the state**

```bash
git log --oneline -3 && git status --short
grep -n '^## ' docs/verification/pilot-v1-gold-set.md
```

Expected: Task 14's commit at or near the head, and the record's headings through
`## Gate 1: the split and the coverage report`. If `## Gate 2: the backup` is
already there, and `git status --short` does not list the record, go to Task 16. If
it is there but uncommitted, go to Step 3: its extract prints `unchanged:` and leaves
the section as it is.

- [x] **Step 2 (gate): Ask the user to confirm the backup**

Put this to the user in chat, and wait for a clear confirmation:

> Gate 2 (GS12). `data/` holds the only copy of pilot v1's saved exhibits and
> canonical documents, and the drafting sessions read from it. Please back up
> `data/` outside the repository, and tell me when it is done. I do not need to know
> where it is.

No drafting starts until the user confirms.

- [x] **Step 3: Record it**

Append to `docs/verification/pilot-v1-gold-set.md`:

```markdown

## Gate 2: the backup

On [GATE: date, YYYY-MM-DD], the user confirmed that `data/` is backed up outside the
repository (GS12). The backup's location is the user's, and is not recorded. No
drafting session had started.
```

Extract it with `python3 /tmp/plan9-extract.py docs/verification/pilot-v1-gold-set.md 2`,
which prints `appended to docs/verification/pilot-v1-gold-set.md: <n> lines`. Fill its
slot, then:

```bash
grep -n '\[GATE' docs/verification/pilot-v1-gold-set.md
git log --oneline -3
git add docs/verification/pilot-v1-gold-set.md
git commit -m "docs(evaluation): record the backup of data/ (gate 2)"
```

Expected: nothing from `grep`.

---

### Task 16: The brief review (gate)

P9-6. The user reads both committed briefs before any drafting session starts, since
a drafting session sees only its brief, the contracts, and its text (GS13). The user
may change either brief; a changed brief is committed before drafting, and passes
the wording guard and the codebook brief's test.

**Files:**

- Modify, only if the user changes them:
  `evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md` and `gold.md`.
- Modify: `docs/verification/pilot-v1-gold-set.md`, by appending its section.

**Interfaces:**

- Consumes: Task 13's briefs; Task 15's record.
- Produces: the briefs the drafting sessions of Tasks 17 to 19 read.

- [x] **Step 1: Probe the state**

```bash
git log --oneline -3 && git status --short
grep -n '^## ' docs/verification/pilot-v1-gold-set.md
```

Expected: the record's headings through `## Gate 2: the backup`. If
`## The brief review` is already there, and `git status --short` lists neither the
record nor a brief, go to Task 17. If it is there but uncommitted, run Step 3, then
only Step 4's commands from `grep` on.

- [x] **Step 2 (gate): Ask the user to review the briefs**

Put this to the user in chat, and wait:

> The brief review (P9-6). Before any drafting session starts, please read the two
> briefs a drafting session is given:
> `evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md` and `gold.md`. Each
> states the task, what the session may read, the draft's form, the rules, and how
> it checks its draft. Tell me any change you want, or edit them yourself, and say
> when they are ready.

Make any change the user asks for, in the user's words where the user gives them.
A drafting session must still find its task, its reading list, the form, and the
check in its brief; if a change removes one, say so to the user before making it.

- [x] **Step 3: Check the briefs**

```bash
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py "tests/integration/test_stage6_pilot_v1.py::test_the_codebook_brief_lists_exactly_the_training_releases" -q -rs
git diff --stat -- evaluation/djia-2024q3-2026q2/pilot-v1/briefs
```

Expected: `6 passed`; and the `git diff` lists the briefs the user changed,
or nothing.

- [x] **Step 4: Record it, and commit**

Append to `docs/verification/pilot-v1-gold-set.md`:

```markdown

## The brief review

On [GATE: date, YYYY-MM-DD], the user reviewed both briefs before any drafting session
started (P9-6): `evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md` and
`gold.md`. [GATE: "Neither changed.", or which brief changed and which of its
sections, named by heading]. After the review, the wording guard and the codebook
brief's test printed `6 passed`.
```

Extract it with `python3 /tmp/plan9-extract.py docs/verification/pilot-v1-gold-set.md 3`,
fill its slots, then:

```bash
grep -n '\[GATE' docs/verification/pilot-v1-gold-set.md
git log --oneline -3
git add docs/verification/pilot-v1-gold-set.md evaluation/djia-2024q3-2026q2/pilot-v1/briefs
git commit -m "docs(evaluation): the drafting briefs, as the user reviewed them (P9-6)"
```

Expected: nothing from `grep`.

---

### Task 17: Gate 3 — codebook v0, approved in ADR 0003 (gate)

S §Gates 3, §The codebook, GS9, GS13, and P9-5, P9-13, P9-20. A fresh session drafts
the themes from the 20 training texts alone. The user edits the working copy.
`codebook freeze` anchors the examples and prints the content hash; ADR 0003 cites
it; the user approves; and the freeze writes v0. No dev or test bundle is read
before this task ends (R12.3).

**Files:**

- Local, never committed: `data/runs/gold/texts/<event>.md` for the 20 training
  events; `data/runs/gold/drafts/codebook.draft.toml` and `codebook.working.toml`.
- Create: `docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md`.
- Written by the command: `codebooks/djia-pilot/codebook-v0.toml`.
- Modify: `docs/verification/pilot-v1-gold-set.md`, by appending its section.

**Interfaces:**

- Consumes: `gold show --text --training` (Task 12); `codebook freeze` and
  `codebook validate` (Task 11); the codebook brief (Task 13).
- Produces: codebook v0, which Tasks 18 and 19 code against, and ADR 0003.

- [x] **Step 1: Probe the state**

```bash
git log --oneline -3 && git status --short
ls codebooks/djia-pilot docs/adr data/runs/gold/drafts 2>&1
```

Resume from what exists:

| What exists | Go to |
| --- | --- |
| `codebooks/djia-pilot/codebook-v0.toml`, committed | Task 18 |
| `codebook-v0.toml`, uncommitted | Step 8's `codebook validate`, then Step 9 |
| ADR 0003, uncommitted, and `grep -n '\[GATE' docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md` prints nothing | Step 8 |
| ADR 0003, uncommitted, with a slot left | Step 4. Never extract the ADR again, since it may hold the user's edits: edit it in place. Fill or correct the counts and the hash from Step 4, and any other slot but `Date` and `Deciders` from Step 5's list, asking the user for the draft's date and the edits if this session did not hear them. Then Steps 6 and 7. |
| `codebook.working.toml`, and no ADR 0003 | Step 4 |
| `codebook.draft.toml` alone | Step 3's last paragraph: the user makes the working copy |
| none of these | Step 2 |

Read the first row that matches.

- [x] **Step 2: Write the training texts**

```bash
uv run --locked earnings-pipeline gold show --text --training; echo "exit $?"
```

Expected, checks: `wrote 20 texts under data/runs/gold/texts`, and `exit 0`. Do not
open them.

- [x] **Step 3 (gate): Hand off to the drafting session**

> Deviation: the drafting session ran on 2026-10-02. On 2026-10-03, with the user's authorization, the executing session read the draft once, its example quotes from 18 training releases included, and edited the working copy by script per the user's choices; a fresh revision session, on a prompt the user reviewed in chat rather than at Task 16, edited the working copy instead of writing a draft; and a review session made two edits the user authorized. ADR 0003 and the record give the account.

Put this to the user in chat, fill the date, and end your turn:

> Gate 3, codebook v0, is ready to draft (P9-5). Please start a fresh Claude Code
> session in the main checkout, `/Users/lowell/Projects/earnings-themes`, on the
> branch `stage-6-pilot-codebook-split-and-gold-set`, not in a worktree, and choose
> Claude Opus 5.5 in the model picker before its first message. Send it exactly:
>
> ```text
> Read evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md and follow it exactly. Today is [GATE: today's date, YYYY-MM-DD].
> ```
>
> When it has written `data/runs/gold/drafts/codebook.draft.toml`, copy that file to
> `data/runs/gold/drafts/codebook.working.toml`, and make the working copy yours:
> edit, cut, merge, and rename themes, and rewrite any wording you want in your own
> words. Keep the draft unchanged. Then come back to this session, or start a fresh
> one on plan 9. Tell me the working copy is ready, and, for ADR 0003, what you
> changed from the draft: which themes you cut, merged, renamed, or added, named by
> `theme_id`, in your own words and never a release's.

Keep the date you put in the first message: it is the draft's date, for Step 5.

- [x] **Step 4: Check the working copy**

> Deviation: the executing session checked the revision and review sessions' reported results itself, by an item-by-item compare, the all-texts wording check (642 strings, no refusal), and the content hash.

```bash
ls data/runs/gold/drafts
uv run --locked earnings-pipeline codebook freeze; echo "exit $?"
```

Expected, checks: the listing holds `codebook.draft.toml` and
`codebook.working.toml`, and the command prints no `no parsed document` line, then

```text
codebook djia-pilot v0: <t> themes, <e> examples, from 20 training bundles
content_hash  <64 hex>
not written: ADR 0003 cites this hash; then run freeze again with --adr, --approver, and --approved-on
exit 0
```

or each problem as `refused: <item>: <reason>` and `exit 1`. Put every refusal to
the user by item and reason, such as
`refused: theme demand.positive_examples[0]: ambiguous_occurrence`, and wait while
the user changes the working copy; then run this step again. Never open the working
copy to find the item. `source_wording` means a string in the user's words shares 40
characters with the release or fixture the refusal names by ID; the user rewords it.
The content hash is printed only once every check passes (P9-21).

Keep the content hash for Steps 5 and 8. A change to the working copy after this step
changes the hash: run this step again, and change the ADR to match.

- [x] **Step 5: Write ADR 0003**

> Deviation: ADR 0003 departs from the template: its Context gives the four-session history, the user's confirmed account, the blinding exceptions, and the checks, and its Alternatives add hand edits and deeper levels (deferred to Stage 12). After the final review, its `legal` bullet names the session that wrote the one synthetic hard negative, which the spec's §The codebook says the user writes (`c77824a`).

Create `docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md`:

```markdown
# 0003. Adopt codebook v0 as the pilot codebook

- **Status:** Accepted
- **Date:** [GATE: the approval's date, YYYY-MM-DD]
- **Deciders:** [GATE: the approver, as the user gives it]
- **Blast radius:** every theme assignment coded against `djia-pilot` v0: the
  pilot's gold and curated hard negatives (Stage 6), the codebook contract (Stage 9),
  and the evaluations that score against it (Stages 11, 12, and 14).

## Context

What was known on [GATE: the codebook draft's date], when Stage 6 drafted its
codebook (`specs/pilot-codebook-split-and-gold-set-protocol.md`, §The codebook;
`specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md`, Task 17):

- **The question.** A codebook version names its discovery corpus and is approved in
  a decision record before it codes anything (R9.2, R9.7). GS9 makes v0 the pilot
  codebook, frozen before any dev or test bundle is read (R12.3, GS13).
- **The discovery corpus.** The training partition of pilot v1's split,
  `evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json` (`issuer-time/1`, content
  hash `5c4a2f3c5ed9ffc2cf0065658ec4e75311220338cf9b3fe07802c0db9fcd0e53`): the 20 training
  events' parsed documents, which
  `evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md` lists. The pilot is
  pinned by content hash
  `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926` (GS2). No dev or
  test document was read.
- **The drafting aid.** A fresh Claude Code session running Claude Opus 5.5
  (`claude-opus-5-5`) read the brief and the 20 training texts, and drafted themes
  with their fields (GS9, P9-5). The draft is kept, unchanged and uncommitted, under
  `data/runs/gold/drafts/`.
- **The user's working copy.** The user edited the draft into the working copy:
  [GATE: what the user did, in the user's words, such as which themes were cut,
  merged, or renamed, named by `theme_id`]. `codebook freeze` anchored every example
  to an exact narrative span of a training document, and refused any string that
  shares 40 characters with a training release (GS3).

## Decision

Adopt `codebooks/djia-pilot/codebook-v0.toml` as codebook `djia-pilot`, version 0:
the pilot codebook.

- It holds [GATE: t] themes and [GATE: e] examples.
- Its content hash is `[GATE: the content hash that codebook freeze printed]`. The
  hash covers every field but `status`, `approval`, and `content_hash`, so this
  record cites it before the approval exists, and approving changes no hashed byte
  (P9-13).
- Its discovery corpus is the training partition alone.

v0 is the pilot codebook, not the final taxonomy, which stays deliberately
unresolved (`AGENTS.md`, §Source basis and unresolved choices; GS9).

## Consequences

- **v0 never changes.** A claim no v0 theme fits is coded `unmatched`, never as a new
  theme (R9.3). A later codebook is a new version with its own decision record, and
  gold coded against v0 stays coded against v0.
- **Stage 6's records cite it.** Every gold file and the curated hard negatives name
  v0 by ID, version, and content hash, and the validator refuses any other.
- **Reading order.** Dev bundles may be read for gold from this approval on; test
  bundles only after Stage 14 freezes its configuration (GS13, GS18).
- **Later stages.** Stage 9 takes v0 as its codebook contract's first frozen version,
  and Stages 11, 12, and 14 score against it.

## Alternatives considered

- **Discover over every partition.** Rejected: dev and test documents would shape
  the themes they later score (R12.3).
- **Adopt the model's draft unchanged.** Rejected: the codebook is the user's
  decision, and the draft only an aid (GS9).
- **Draft from blank, with no model.** Not chosen: GS4 has the user verify drafts,
  and records the limitation that the gold follows one model family's reading.

## Trade-offs & reversibility

- **What it costs.** v0 starts from one model's framing of 20 releases, as the user
  edited it, and one annotator approved it. The verification record,
  `docs/verification/pilot-v1-gold-set.md`, states both limitations.
- **Reversibility.** v0 itself cannot change. A v1 needs its own decision record and
  a recoding of any gold scored against it, and the v0 gold stays traceable to v0.
```

Extract it with
`python3 /tmp/plan9-extract.py docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md`,
then fill these slots, and leave the approval's two for Step 7:

- the theme count, the example count, and the content hash, from Step 4;
- the draft's date, from Step 3's first message;
- the user's edits, from the user's answer at Step 3, in the user's words.

A session that did not run Step 3 asks the user for the date and the edits. Never
derive either by opening, listing the contents of, or comparing the draft or the
working copy. If the ADR already exists, do not extract it again: that would
overwrite the user's edits. Correct its values in place.

- [x] **Step 6: Check the ADR offline**

```bash
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs
```

Expected, checks: `5 passed`. The guard now reads ADR 0003.

- [x] **Step 7 (gate): Ask the user to approve codebook v0**

Put this to the user in chat, and wait for a clear approval:

> Gate 3. Codebook v0 is your working copy: `<t>` themes and `<e>` examples, content
> hash `<hash>`, discovered from the 20 training bundles alone. ADR 0003,
> `docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md`, records the file, the
> hash, the discovery corpus, and the drafting aid, and that v0 is the pilot
> codebook, not the final taxonomy. Please read the ADR, change anything you want,
> the account of your edits included, and, if you approve v0, give me the
> approver's name as it should be recorded and the approval's date. After this, v0 never changes: a claim no theme fits is coded
> `unmatched`.

Fill the ADR's approval slots from the user's answer. The implementer never writes
the approver's name unprompted.

```bash
grep -n '\[GATE' docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md
```

Expected: nothing.

- [x] **Step 8: Freeze v0**

With the approver and the date the user gave at Step 7, as ADR 0003's `Deciders`
and `Date` lines record them:

```bash
uv run --locked earnings-pipeline codebook freeze --adr docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md --approver "<approver>" --approved-on <YYYY-MM-DD>; echo "exit $?"
uv run --locked earnings-pipeline codebook validate; echo "exit $?"
```

Expected, checks: the freeze prints Step 4's first two lines, then
`froze djia-pilot v0, approved` (or, on a rerun, `unchanged: djia-pilot v0,
approved`),
`codebooks/djia-pilot/codebook-v0.toml  <the same hash>`, and `exit 0`; the
validation prints `valid: djia-pilot v0, <t> themes, approved by <approver> on
<date>`, the path with the hash, and `exit 0`. A refusal
`Refused: docs/adr/… does not cite <hash>` means the working copy changed after the
ADR was written: go back to Step 4.

- [x] **Step 9: Run the local legs and the checks**

```bash
uv run --locked --all-packages pytest tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py -q -rs
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected, checks: `12 passed, 2 skipped`, the committed codebook now validating against
the local bundles; `1741 passed, 3 skipped, 24 deselected`; `All checks passed!` and `296 files already formatted`.

- [x] **Step 10: Record it, and commit**

> Deviation: the record's Gate 3 section adds the revisions and blinding bullets and dates the drafting session 2026-10-02. At the user's choice, the Gate 3 commit was amended once, so ADR 0003 and the record say "no training text under `data/runs/gold/texts/`" (`2432434`, was `00723cb`).

Append to `docs/verification/pilot-v1-gold-set.md`:

```markdown

## Gate 3: codebook v0

- **The discovery corpus.** The 20 training events' parsed documents, which
  `briefs/codebook.md` lists, and no dev or test document (R9.2, R12.3, P9-16).
- **The drafting session.** On [GATE: date, YYYY-MM-DD], a fresh Claude Code session
  in the main checkout, running Claude Opus 5.5 (`claude-opus-5-5`), read
  `briefs/codebook.md`, the contracts it names, and the 20 training texts. It wrote
  `data/runs/gold/drafts/codebook.draft.toml`, which is kept, unchanged and
  uncommitted.
- **The user's edits.** The user made the working copy theirs, and ADR 0003's
  Context gives the account of them in the user's words. `codebook freeze` was run
  again until its checks passed; each refusal named an item and a reason, and the
  user changed the working copy.
- **The freeze.** `codebooks/djia-pilot/codebook-v0.toml`: [GATE: t] themes and
  [GATE: e] examples, content hash `[GATE: the content hash]`.
- **The approval.** [GATE: approver] approved v0 on [GATE: date] in
  `docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md`, which cites the hash.
  `codebook validate` printed `valid:`.
- **Checks.** The local legs printed `12 passed, 2 skipped`, and the wording guard
  `5 passed`.
```

Extract it with `python3 /tmp/plan9-extract.py docs/verification/pilot-v1-gold-set.md 4`,
fill its slots from ADR 0003 and Step 8's output, then run the commands below. On a
resume the extract prints `unchanged:`, and the section already there keeps its
values: fill only what `grep` still lists.

```bash
grep -n '\[GATE' docs/verification/pilot-v1-gold-set.md
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs
git log --oneline -3
git add codebooks/djia-pilot/codebook-v0.toml docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md docs/verification/pilot-v1-gold-set.md
git commit -m "feat(codebooks): codebook v0, approved in ADR 0003 (gate 3)"
```

Expected: nothing from `grep`, and `5 passed`.

---

### Task 18: Gate 4 — the curated hard negatives (gate)

S §Gates 4, §Curated hard negatives, GS4, GS10, and P9-5, P9-18. They come after v0,
since they name its themes. A fresh session drafts hard-negative claims over Stage
1's eight committed fixtures, whose text is public and committed; the user verifies
every item and signs. The record sits outside the pilot, in no partition, and its
checks run in the default suite.

**Files:**

- Local, never committed: `data/runs/gold/texts/fixtures/*.md`;
  `data/runs/gold/drafts/hard-negatives.draft.toml` and `.working.toml`;
  `data/runs/gold/anchored/hard-negatives.toml`; and
  `data/runs/gold/views/hard-negatives/`.
- Written by the command: `tests/fixtures/gold/hard-negatives.toml`.
- Modify: `docs/verification/pilot-v1-gold-set.md`, by appending its section.

**Interfaces:**

- Consumes: `gold show --text --hard-negatives`, `gold anchor --hard-negatives`,
  `gold show --hard-negatives`, and `gold validate --hard-negatives` (Task 12); the
  gold brief; codebook v0.
- Produces: the curated hard negatives, for Stage 8's misattribution fixtures.

- [x] **Step 1: Probe the state**

```bash
git log --oneline -3 && git status --short
ls tests/fixtures/gold data/runs/gold/drafts 2>&1
```

Resume from what exists:

| What exists | Go to |
| --- | --- |
| `tests/fixtures/gold/hard-negatives.toml`, committed | Task 19 |
| `hard-negatives.toml`, uncommitted | Step 6, whose anchor prints `unchanged:` in place of `froze` |
| `hard-negatives.working.toml` | Step 4 |
| `hard-negatives.draft.toml` alone | Step 3's last paragraph |
| neither | Step 2 |

Read the first row that matches.

- [x] **Step 2: Write the fixtures' texts**

```bash
uv run --locked earnings-pipeline gold show --text --hard-negatives; echo "exit $?"
```

Expected, checks: `wrote 8 texts under data/runs/gold/texts`, and `exit 0`.

- [x] **Step 3 (gate): Hand off to the drafting session**

Put this to the user in chat, fill the date, and end your turn:

> Gate 4, the curated hard negatives, is ready to draft (P9-5). Please start a fresh
> Claude Code session in the main checkout, `/Users/lowell/Projects/earnings-themes`,
> on the branch `stage-6-pilot-codebook-split-and-gold-set`, not in a worktree, and
> choose Claude Opus 5.5 in the model picker before its first message. Send it
> exactly:
>
> ```text
> Read evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md and follow it exactly. Your task is the curated hard negatives. Today is [GATE: today's date, YYYY-MM-DD].
> ```
>
> When it has written `data/runs/gold/drafts/hard-negatives.draft.toml`, copy that
> file to `data/runs/gold/drafts/hard-negatives.working.toml`, leaving the draft
> unchanged, and tell me the working copy is ready. You verify it in the next steps.

- [x] **Step 4: Anchor the working copy, and write the views**

```bash
uv run --locked earnings-pipeline gold anchor --hard-negatives; echo "exit $?"
uv run --locked earnings-pipeline gold show --hard-negatives; echo "exit $?"
```

Expected, checks: the anchor prints
`hard-negatives: <d> fixtures, <n> hard negatives (<kind> <count>, ...)`, the
origins line, `anchored  data/runs/gold/anchored/hard-negatives.toml`, the unsigned
line, and `exit 0`; or each problem as `refused: <item>: <reason>` and `exit 1`,
which goes to the user by item and reason, as Task 17, Step 4 does. A missing kind
is `refused: hard_negatives: negative_kinds`: at least one each of `period`,
`issuer`, and `section`. The anchor also checks the wording against every pilot
release and fixture before it writes anything (P9-21). Then `gold show` prints one
`view  …` line per fixture.

- [x] **Step 5 (gate): The user verifies and signs**

> Deviation: process only: the user's first signature did not reach the file, so the user signed by `sed`; all 58 items were accepted as drafted.

Put this to the user in chat, and wait:

> Gate 4. The views are under `data/runs/gold/views/hard-negatives/`, one per
> fixture: each quote marked in place as `[[q1>> … <<q1]]`, with its hard-negative
> claims listed. Please verify every item in
> `data/runs/gold/drafts/hard-negatives.working.toml`: edit, delete, or add claims
> and quotes in your own words, and ask me to anchor again whenever you want fresh
> views. When you are satisfied, set
> `annotator = "Lowell Mason (verified a Claude draft)"` in the working copy, and
> tell me it is signed.

Rerun Step 4 whenever the user asks, and relay its refusals by item and reason.
Keep the date the user signs for Step 8's commit message; a session that did not
hear it asks.

- [x] **Step 6: Commit the signed record**

```bash
uv run --locked earnings-pipeline gold anchor --hard-negatives; echo "exit $?"
uv run --locked earnings-pipeline gold validate --hard-negatives; echo "exit $?"
```

Expected, checks: the anchor's last line is
`froze tests/fixtures/gold/hard-negatives.toml` (or, on a rerun, `unchanged:`),
and `exit 0`; then `valid: hard-negatives, <d> fixtures, <n> hard negatives,
signed`, and `exit 0`. If the anchor prints the unsigned line instead, the working
copy is not signed: go back to Step 5.

- [x] **Step 7: Run the local legs and the checks**

```bash
uv run --locked --all-packages pytest tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py -q -rs
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected, checks: `13 passed, 1 skipped`; `1742 passed, 2 skipped, 24 deselected`, the curated hard negatives
now checked in the default suite; `All checks passed!` and `296 files already formatted`.

- [x] **Step 8: Record it, and commit**

Append to `docs/verification/pilot-v1-gold-set.md`:

```markdown

## Gate 4: the curated hard negatives

- **The drafting session.** On [GATE: date, YYYY-MM-DD], a fresh session running
  Claude Opus 5.5 read `briefs/gold.md` and the texts of Stage 1's eight fixtures,
  and wrote `data/runs/gold/drafts/hard-negatives.draft.toml`.
- **The record.** `tests/fixtures/gold/hard-negatives.toml`, outside the pilot and in
  no partition (R12.5):
  - [GATE: d] fixtures and [GATE: n] hard negatives: `issuer` [GATE], `period`
    [GATE], and `section` [GATE];
  - origins: accepted [GATE], edited [GATE], rejected [GATE], and added [GATE];
  - signed on [GATE: date], as `annotator = "[GATE: the file's annotator]"`.
- **Checks.** `gold validate --hard-negatives` printed `valid:`, and the default suite
  now checks the record offline: `1742 passed, 2 skipped, 24 deselected`.
```

Extract it with `python3 /tmp/plan9-extract.py docs/verification/pilot-v1-gold-set.md 5`;
on a resume it prints `unchanged:`, and only the slots left need filling. Fill its
slots from Step 6's anchor output (the counts and the origins), the
signing date from Step 5, and the committed file itself, which holds the drafting
date and the signature and no release text:

```bash
grep -n -e '^annotator' -e '^drafted_on' tests/fixtures/gold/hard-negatives.toml
```

Then, with the signing date:

```bash
grep -n '\[GATE' docs/verification/pilot-v1-gold-set.md
git log --oneline -3
git add tests/fixtures/gold/hard-negatives.toml docs/verification/pilot-v1-gold-set.md
git commit -m "feat(fixtures): the curated hard negatives, verified and signed (gate 4)" -m "Signed: <YYYY-MM-DD>."
```

Expected: nothing from `grep`.

---

### Task 19: Gate 5 — three signed train bundles (gate)

S §Gates 5, §Order of work step 5, GS4, GS5, GS13, and P9-5, P9-7. Three train
bundles, in the pilot's selection order: #1 `cik-0000051143:2024-12-31`, #3
`cik-0000093410:2025-03-31`, and #5 `cik-0000310158:2025-06-30`. Each is drafted in
its own fresh session, anchored, verified item by item, read whole for omissions,
signed, validated, and committed on its own. Then the record closes, and `CLAUDE.md`
and `README.md` describe Stage 6 as complete.

**Files:**

- Local, never committed: for each bundle, `data/runs/gold/texts/<event>.md`, its
  draft and working copy, its anchored file, and its view.
- Written by the command: `evaluation/djia-2024q3-2026q2/pilot-v1/gold/<event>.toml`,
  three files.
- Modify: `docs/verification/pilot-v1-gold-set.md`, by appending its last section;
  and `CLAUDE.md` and `README.md`, by exact replacement.

**Interfaces:**

- Consumes: `gold show --text`, `gold anchor`, `gold show`, and `gold validate`
  (Task 12); the gold brief; codebook v0.
- Produces: three signed gold files, which pass the validator: Stage 6's exit.

Steps 1 to 7 run once for each bundle, in order: `cik-0000051143:2024-12-31`, then
`cik-0000093410:2025-03-31`, then `cik-0000310158:2025-06-30`. `<event>` is its ID,
and `<file>` its `file_stem`, such as `cik-0000051143_2024-12-31`. `<partition>` is
`train` for this plan's three bundles, and `train` or `dev` for the bundles that
follow it (Handoffs).

- [x] **Step 1: Probe the state**

```bash
git log --oneline -3 && git status --short
ls evaluation/djia-2024q3-2026q2/pilot-v1/gold data/runs/gold/drafts 2>&1
grep -n '^## Gate 5' docs/verification/pilot-v1-gold-set.md
```

For this plan's three bundles only: if the `grep` prints a line, Step 9 has run. If
`git status --short` then lists none of the record, `CLAUDE.md`, and `README.md`,
Step 11 has too: go to Completion. Otherwise go to Step 8, then Step 9. A bundle
after this plan (Handoffs) skips this paragraph.

If the `grep` prints nothing, or for a bundle after this plan, resume from what
exists for the next bundle in order:

| What exists | Go to |
| --- | --- |
| `gold/<file>.toml`, committed | the next bundle, or Step 8 after the third |
| `gold/<file>.toml`, uncommitted | Step 6, whose anchor prints `unchanged:` in place of `froze`; then Step 7 |
| `<file>.working.toml` | Step 4, then Step 5 |
| `<file>.draft.toml` alone | Step 3's last paragraph |
| neither | Step 2 |

Read the first row that matches.

- [x] **Step 2: Write the bundle's text**

```bash
uv run --locked earnings-pipeline gold show --text <event>; echo "exit $?"
```

Expected, checks: `wrote 1 text under data/runs/gold/texts`, and `exit 0`.

- [x] **Step 3 (gate): Hand off to the bundle's drafting session**

Put this to the user in chat, fill the event and the date, and end your turn:

> Gate 5, bundle `<event>`, is ready to draft (P9-5). Please start a fresh Claude
> Code session in the main checkout, `/Users/lowell/Projects/earnings-themes`, on the
> branch `stage-6-pilot-codebook-split-and-gold-set`, not in a worktree, and choose
> Claude Opus 5.5 in the model picker before its first message. Send it exactly:
>
> ```text
> Read evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md and follow it exactly. Your task is the gold for <event>. Today is [GATE: today's date, YYYY-MM-DD].
> ```
>
> When it has written `data/runs/gold/drafts/<file>.draft.toml`, copy that file to
> `data/runs/gold/drafts/<file>.working.toml`, leaving the draft unchanged, and tell
> me the working copy is ready.

- [x] **Step 4: Anchor the working copy, and write the view**

```bash
uv run --locked earnings-pipeline gold anchor <event>; echo "exit $?"
uv run --locked earnings-pipeline gold show <event>; echo "exit $?"
```

Expected, checks: the anchor prints
`<event> (<partition>): <q> quotes, <c> claims, <a> assignments, <n> hard negatives; no_theme <true|false>`,
the origins line, `anchored  data/runs/gold/anchored/<file>.toml`, the unsigned
line, and `exit 0`; or each problem as `refused: <item>: <reason>` and `exit 1`,
which goes to the user by item and reason. Then `view  data/runs/gold/views/<file>.md`.

- [x] **Step 5 (gate): The user verifies, reads for omissions, and signs**

> Deviation: process only: in all three bundles every item was accepted as drafted, and no omission pass added one; bundle 1's first signature did not reach the file, and the user signed bundles 1 and 2 by `sed`.

Put this to the user in chat, and wait for both confirmations:

> Gate 5, `<event>`. The view is `data/runs/gold/views/<file>.md`: the release's
> text with each quote marked as `[[q1>> … <<q1]]`, and every claim, theme, support
> label, hard negative, and the release-identification label listed. Please:
>
> 1. **Verify every item** in `data/runs/gold/drafts/<file>.working.toml`: edit or
>    delete what is wrong, in your own words, and ask me to anchor again whenever
>    you want a fresh view.
> 2. **The omission pass** (GS5): read the whole release in the view for claims the
>    draft missed, and add them to the working copy. Tell me when it is done; I
>    record its date.
> 3. **Sign**: set `annotator = "Lowell Mason (verified a Claude draft)"` in the
>    working copy, and tell me it is signed.

Rerun Step 4 whenever the user asks. Keep the omission pass's date and the
signing date, as the user gives them, for Step 7's commit message, which is where
the record takes them from; a session that did not hear them asks the user. The
bundle counts as annotated only after that pass (GS5).

- [x] **Step 6: Commit the signed bundle**

```bash
uv run --locked earnings-pipeline gold anchor <event>; echo "exit $?"
uv run --locked earnings-pipeline gold validate <event>; echo "exit $?"
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs
```

Expected, checks: the anchor's last line is
`froze evaluation/djia-2024q3-2026q2/pilot-v1/gold/<file>.toml` (or, on a rerun,
`unchanged:`), and `exit 0`;
`valid: <event> (<partition>), <q> quotes, <c> claims, signed`, and `exit 0`; and
`5 passed`. If the anchor prints the unsigned line, go back to Step 5.

- [x] **Step 7: Commit the bundle**

```bash
git log --oneline -3
git add evaluation/djia-2024q3-2026q2/pilot-v1/gold/<file>.toml
git commit -m "feat(evaluation): signed gold for <event> (gate 5)" -m "Omission pass: <YYYY-MM-DD>. Signed: <YYYY-MM-DD>."
```

Then return to Step 1 for the next bundle. After this plan's third bundle, go on to
Step 8. A bundle after this plan ends here.

- [x] **Step 8: Count the three bundles from their committed files**

Create `/tmp/plan9-gold-counts.py`:

```python
"""Count plan 9's committed gold for the verification record (Task 19, Step 8).

Reads only the committed gold files, and prints IDs, labels, and counts: never a
claim, a note, or a rule, which are the annotator's words about a release (GS13).

usage: python /tmp/plan9-gold-counts.py [gold directory]
"""

import sys
from collections import Counter
from pathlib import Path

from earnings_themes.gold import load_gold

GOLD = Path("evaluation/djia-2024q3-2026q2/pilot-v1/gold")
ITEMS = ("quotes", "claims", "assignments", "hard negatives")
ORIGINS = ("accepted", "edited", "rejected", "added")


def counted(counts: Counter[str]) -> str:
    items = ", ".join(f"{counts[name]} {name}" for name in ITEMS)
    return items + "; " + ", ".join(f"{name} {counts[name]}" for name in ORIGINS)


directory = Path(sys.argv[1]) if len(sys.argv) > 1 else GOLD
totals: Counter[str] = Counter()
for path in sorted(directory.glob("*.toml")):
    gold = load_gold(path)
    counts = Counter(gold.counts.model_dump())
    counts.update(
        {
            "quotes": len(gold.quotes),
            "claims": len(gold.claims),
            "assignments": len(gold.assignments),
            "hard negatives": len(gold.hard_negatives),
        }
    )
    totals.update(counts)
    totals["bundles"] += 1
    label = gold.release_identification.label
    no_theme = str(gold.no_theme).lower()
    signed = "signed" if gold.annotator.strip() else "NOT SIGNED"
    print(
        f"{gold.event_id}  {gold.partition}  release {label}; {counted(counts)};"
        f" no_theme {no_theme}; drafted {gold.drafting_aid.drafted_on}; {signed}"
    )
print(f"total: {totals['bundles']} bundles; {counted(totals)}")
```

```bash
python3 /tmp/plan9-extract.py /tmp/plan9-gold-counts.py && uv run --locked --all-packages python /tmp/plan9-gold-counts.py
git log --format='%h %ad %s%n%b' --date=short -- evaluation/djia-2024q3-2026q2/pilot-v1/gold
```

The script reads only the committed gold files, which hold pointers, hashes, and
the user's words, and prints one line per bundle, with its drafting date, and the
totals. On the plan-time synthetic bundle it printed:

```text
cik-0009990001:2024-08-31  train  release release; 1 quotes, 1 claims, 1 assignments, 0 hard negatives; accepted 3, edited 0, rejected 0, added 0; no_theme false; drafted 2026-10-01; signed
total: 1 bundles; 1 quotes, 1 claims, 1 assignments, 0 hard negatives; accepted 3, edited 0, rejected 0, added 0
```

Expected, checks: three lines, each `train` and `signed`, with the release label,
the counts, and the drafting date, and the totals; then the three Step 7 commits,
each with its omission-pass and signing dates.

- [x] **Step 9: Close the record, and refresh the current state**

> Deviation: with the user's approval, the record's "What never drafted" bullet is narrowed to the two Gate 3 exceptions and the implementers' search slips, "Where they ran" names Gate 3's revision and review sessions, "The drafts" cites a write-nothing `gold anchor --check`, and the user added the "Accepted as drafted" limitation.

Append to `docs/verification/pilot-v1-gold-set.md`:

```markdown

## Gate 5: three signed train bundles

The first three train events in the pilot's selection order (P9-7), chosen by order
before any text was read. Each was drafted in its own fresh session, anchored,
verified item by item, read whole for omissions, signed, validated, and committed
as `evaluation/djia-2024q3-2026q2/pilot-v1/gold/<event>.toml`, the event's ID with
its colon as an underscore (P9-3). The counting script in plan 9's Task 19, Step 8
counted them from the committed files, and each bundle's commit holds its
omission-pass and signing dates:

| Event | Release label | Quotes | Claims | Assignments | Hard negatives | `no_theme` | Accepted | Edited | Rejected | Added | Omission pass | Signed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cik-0000051143:2024-12-31` | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE: date] | [GATE: date] |
| `cik-0000093410:2025-03-31` | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE: date] | [GATE: date] |
| `cik-0000310158:2025-06-30` | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE] | [GATE: date] | [GATE: date] |
| **Total** | | [GATE] | [GATE] | [GATE] | [GATE] | | [GATE] | [GATE] | [GATE] | [GATE] | | |

Each is `train` and signed by the user; `gold validate` printed `valid:` for each,
and the gold leg passes. The accepted, edited, rejected, and added counts compare
each signed file with its kept draft (GS5).

## Drafting sessions

| Gate | Draft, under `data/runs/gold/drafts/` | Brief | Model | Date |
| --- | --- | --- | --- | --- |
| 3 | `codebook.draft.toml` | `codebook.md` | Claude Opus 5.5 (`claude-opus-5-5`) | [GATE] |
| 4 | `hard-negatives.draft.toml` | `gold.md` | Claude Opus 5.5 (`claude-opus-5-5`) | [GATE] |
| 5 | `cik-0000051143_2024-12-31.draft.toml` | `gold.md` | Claude Opus 5.5 (`claude-opus-5-5`) | [GATE] |
| 5 | `cik-0000093410_2025-03-31.draft.toml` | `gold.md` | Claude Opus 5.5 (`claude-opus-5-5`) | [GATE] |
| 5 | `cik-0000310158_2025-06-30.draft.toml` | `gold.md` | Claude Opus 5.5 (`claude-opus-5-5`) | [GATE] |

- **Where they ran.** Each session was fresh, started by the user in the main
  checkout with its committed brief, and drafted one thing (P9-5).
- **What never drafted.** The executing session and its subagents drafted nothing,
  and never read a draft, a working copy, a view, or a text.
- **The drafts.** They stay under `data/runs/gold/drafts/`, unchanged and
  uncommitted, for GS5's shares at Stage 11.

## What was verified

| Item (S §Verification; 7 and 8 are plan 9's) | Evidence |
| --- | --- |
| 1. The split over the synthetic pilot and over pilot v1, reproducing `split-v1.json` | `test_each_issuer_keeps_the_partition_of_its_earliest_event`; `test_a_fixture_event_is_never_held_out`; `test_the_issuer_rule_comes_before_the_fixture_rule`; `test_the_order_of_the_input_changes_nothing`; `test_the_split_gives_the_spec_s_counts_and_exclusions`; `test_the_committed_split_reproduces_byte_for_byte` |
| 2. The split and the report leave the pilot unchanged (P-C7) | `test_the_split_changes_no_frozen_record`; `test_split_freezes_once_and_prints_only_ids_and_counts`; `test_coverage_counts_each_state_and_rereads_only_its_runs` |
| 3. The coverage report over the synthetic acquisition, with its non-zero classes | `test_the_synthetic_acquisition_is_counted_by_state`; `test_a_pilot_holding_no_failure_class_reports_three_gaps`; `test_a_rebuild_reads_only_the_runs_it_names` |
| 4. The codebook and gold contracts, the anchor, and the validator, with a tamper test for each refusal | `test_codebook.py`, `test_gold.py`, and `test_anchoring.py`, among them `test_a_tampered_version_is_refused`, `test_another_document_pin_split_codebook_or_partition_is_refused`, and `test_a_tampered_pointer_is_refused`; `test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors`; `test_curated_hard_negatives_over_stage_1_fixtures_validate`; `test_the_curated_hard_negatives_validate_offline` |
| 5. The wording guard's fixture leg | `test_no_stage_6_file_quotes_a_stage_1_fixture`; `test_a_copy_across_a_wrapped_line_is_caught` |
| 6. The local legs | `test_the_committed_coverage_report_reproduces_from_its_runs`; `test_committed_records_validate_against_the_local_store`; `test_no_stage_6_file_quotes_a_pilot_document`: `14 passed` |
| 7. Blinding (GS13) | `test_an_unforeseen_error_is_named_by_type_never_by_message`; `test_a_draft_that_is_not_toml_is_named_never_quoted`; `test_a_dev_or_test_bundle_waits_its_turn`; `test_no_text_is_written_for_an_excluded_event`; `test_a_file_that_is_not_toml_is_refused_by_position_only`; the CLI tests' `quiet` canary |
| 8. No model and no network in `earnings-themes` (R14.1) | `test_importing_earnings_themes_loads_nothing_forbidden`; `test_every_module_is_imported` |
| 9. The suites | The default suite, `1743 passed, 1 skipped, 24 deselected`; the harness suite, 280 passed; Ruff; `uv.lock` unchanged |

## Limitations

- **One annotator.** One person verified and signed every item, so inter-annotator
  agreement is not measurable (R12.6, D2).
- **One drafting model.** Every draft came from Claude Opus 5.5, and the user
  verified drafts rather than annotating from blank (GS4). A Claude model scored
  against this gold shares its drafter's family, and Stage 16 records that conflict
  for any Claude ceiling.
- **Three of 28.** Three train bundles are signed. The other 17 train and 8 dev
  bundles follow Task 19's procedure after this plan, and the 7 test bundles wait
  for Stage 14 (GS18).
- **No observed failure class.** All 40 documents are parsed, so `unavailable`,
  `restricted`, and `failed` are coverage gaps, not observed counts (D4).
- [GATE: any limitation the user adds, or delete this line]
```

Extract it with `python3 /tmp/plan9-extract.py docs/verification/pilot-v1-gold-set.md 6`.
Then refresh the current state in `CLAUDE.md` and `README.md` (S §Rollout), by exact
replacement:

Create `/tmp/plan9-task19-state.py`:

```python
"""Plan 9: exact replacements for 2 file(s). Each old text must
match once, and nothing is written unless every file's replacements apply.
A file that holds its DONE line and none of its old texts was edited by an
earlier run, and is left as it is.
"""

from pathlib import Path

EDITS = {
    "CLAUDE.md": [
        (
            "This repo is documentation-first: its working code is the Stage 1 investigation harness in `expirements/parser-fidelity/`, the Stage 2 contracts in `packages/earnings-core`, Stage 3's canonicalizer and browser diagnostic path in `packages/earnings-ingestion`, Stage 4's point-in-time DJIA cohort and shared SEC client there too, and Stage 5's event discovery, eligibility, pilot selection, and acquisition beside them; `earnings-themes` is still a `hello()` scaffold, and the rest is instructions.\n",
            "This repo is documentation-first: its working code is the Stage 1 investigation harness in `expirements/parser-fidelity/`, the Stage 2 contracts in `packages/earnings-core`, Stage 3's canonicalizer and browser diagnostic path in `packages/earnings-ingestion`, Stage 4's point-in-time DJIA cohort and shared SEC client there too, and Stage 5's event discovery, eligibility, pilot selection, and acquisition and Stage 6's coverage report beside them; `earnings-themes` holds Stage 6's split, codebook, and gold contracts, and the rest is instructions.\n",
        ),
        (
            "| `specs/completed/event-discovery-eligibility-and-acquisition.md` | **Stage 5's stage spec**, approved 2026-09-27, and complete. It split the stage into two plans (EV1): plan A (plan 7) discovered the cohort's events and froze the event manifest and the pilot, and plan B (plan 8) acquired the pilot's releases and records their processing states. Its §Commands amendment (plan 8, P8-4) makes the build decide which frozen version is current. |\n"
            "| `AGENTS-jev-addendum.md`, `specs/jev-integration-spec.md` | **Superseded on the required-path question** by the spec's R14.3; retained only as a proposal for an optional, separately authorized layer. Jev/TypeSafe is not an adopted dependency. Values like `backend = \"disabled\"` or `model = \"jev-1.13.0\"` are sketches, not settings. |\n",
            "| `specs/completed/event-discovery-eligibility-and-acquisition.md` | **Stage 5's stage spec**, approved 2026-09-27, and complete. It split the stage into two plans (EV1): plan A (plan 7) discovered the cohort's events and froze the event manifest and the pilot, and plan B (plan 8) acquired the pilot's releases and records their processing states. Its §Commands amendment (plan 8, P8-4) makes the build decide which frozen version is current. |\n"
            "| `specs/pilot-codebook-split-and-gold-set-protocol.md` | **Stage 6's stage spec**, approved 2026-09-28, and complete (plan 9). It pins Stage 6 to pilot v1 by content hash (GS2), splits it by `issuer-time/1`, and sets the protocol for codebook v0 and the gold: drafted by a Claude session under a committed brief, and verified and signed by the user (GS4), in committed files that hold pointers and hashes, never release text (GS3). It amends D2 for Stage 6's gold, and, through plan 9, its gold file names (P9-3) and `no_theme` (P9-4). |\n"
            "| `AGENTS-jev-addendum.md`, `specs/jev-integration-spec.md` | **Superseded on the required-path question** by the spec's R14.3; retained only as a proposal for an optional, separately authorized layer. Jev/TypeSafe is not an adopted dependency. Values like `backend = \"disabled\"` or `model = \"jev-1.13.0\"` are sketches, not settings. |\n",
        ),
        (
            "## Current state: Stages 1–5 complete; `earnings-themes` still a scaffold\n",
            "## Current state: Stages 1–6 complete\n",
        ),
        (
            "`earnings-themes` still contains only a `hello()` stub, as do the top-level modules of `earnings-ingestion` and `apps/earnings-pipeline`; the application's commands are `earnings-pipeline browser setup` and the `earnings-pipeline cohort` and `events` groups. `data/` is gitignored and holds only local, uncommitted material: fetched pages under `data/raw/`, the cohort's saved evidence under `data/raw/cohort/`, Stage 5's saved SEC responses, the pilot's exhibits among them, under `data/raw/events/`, and under `data/runs/` Stage 1's run outputs and live lock, the user's rendered copies, the browser capture store, the cohort's live-verification records, and Stage 5's processing states and canonical documents under `data/runs/events/`; `prompts/` and `codebooks/` are empty directories. `origin` is set to https://github.com/lowmason/earnings-themes, which is **public** — treat anything committed here as publicly visible.\n",
            "Stage 6 (the pilot codebook, split, and gold-set protocol; plan 9, `specs/pilot-codebook-split-and-gold-set-protocol.md`) is done:\n"
            "\n"
            "- Stage 6 is pinned to pilot v1 over events v1 and universe v1, by content hash (GS2). `apps/earnings-pipeline/src/earnings_pipeline/stage6.py` loads the pilot by path, never `current_pilot`; a later pilot is a new sample and never replaces it. `earnings-pipeline pilot`, `codebook`, and `gold` hold the commands, and none sends a request or calls a model.\n"
            "- `packages/earnings-themes/src/earnings_themes/` holds the `issuer-time/1` split (`split.py`), the codebook contract (`codebook.py`), the gold contract, its anchor, and its validator (`gold.py`, `anchoring.py`, `annotation.py`), F20's wording guard (`wording.py`), and the local views (`view.py`); it imports only `earnings-core`. `earnings-ingestion`'s `events/coverage.py` holds the D4 coverage report, and `canonical/serialize.py`'s `from_fixture_json` reads a canonical document back.\n"
            "- `evaluation/djia-2024q3-2026q2/pilot-v1/` holds the frozen split (20 train, 8 dev, 7 test, and 5 excluded), the coverage report, the two drafting briefs, and the signed gold, one file per event, named with the event's colon as an underscore (P9-3). `codebooks/djia-pilot/codebook-v0.toml` is codebook v0, with [GATE: t] themes, approved in ADR 0003; it is the pilot codebook, not the final taxonomy. `tests/fixtures/gold/hard-negatives.toml` holds the curated hard negatives, over Stage 1's fixtures.\n"
            "- Committed Stage 6 files hold IDs, offsets, labels, hashes, and the user's words, never release text (GS3); `tests/integration/test_stage6_wording.py` holds them to that. The session that runs the commands never opens pilot text (GS13), and a refusal names its item and reason only.\n"
            "- The gold is drafted by Claude Opus 5.5 in fresh sessions the user starts with a committed brief, then verified, read for omissions, and signed by the user (GS4, GS5). [GATE: 3] train bundles are signed. The other 17 train and 8 dev bundles follow plan 9's Task 19, and the 7 test bundles wait for Stage 14 (GS18). `docs/verification/pilot-v1-gold-set.md` records the stage.\n"
            "\n"
            "The top-level modules of `earnings-themes`, `earnings-ingestion`, and `apps/earnings-pipeline` still hold only a `hello()` stub; the application's commands are `earnings-pipeline browser setup` and the `earnings-pipeline cohort`, `events`, `pilot`, `codebook`, and `gold` groups. `data/` is gitignored and holds only local, uncommitted material: fetched pages under `data/raw/`, the cohort's saved evidence under `data/raw/cohort/`, Stage 5's saved SEC responses, the pilot's exhibits among them, under `data/raw/events/`, and under `data/runs/` Stage 1's run outputs and live lock, the user's rendered copies, the browser capture store, the cohort's live-verification records, Stage 5's processing states and canonical documents under `data/runs/events/`, and Stage 6's texts, drafts, working copies, anchored files, and views under `data/runs/gold/`; `prompts/` is an empty directory. `origin` is set to https://github.com/lowmason/earnings-themes, which is **public** — treat anything committed here as publicly visible.\n",
        ),
    ],
    "README.md": [
        (
            "> **Project status (2026-09-28): Stages 1 to 5 complete.**\n",
            "> **Project status ([GATE: date, YYYY-MM-DD]): Stages 1 to 6 complete.**\n",
        ),
        (
            "> offline tests. `earnings-themes` still contains a placeholder API; there is no theme\n"
            "> extraction, approved theme codebook, or published dataset yet.\n",
            "> offline tests. `earnings-themes` holds the pilot's split and its codebook and gold\n"
            "> contracts. Codebook v0, the pilot codebook, is approved, and [GATE: 3] gold bundles are\n"
            "> signed; there is no theme extraction or published dataset yet.\n",
        ),
        (
            "| `packages/earnings-ingestion/` | Source adapters, raw snapshots, deterministic parsing, canonicalization, and entity resolution | Stage 3's canonicalizer and browser diagnostic path; Stage 4's artifact store, shared SEC client, and point-in-time DJIA cohort; Stage 5's event discovery, eligibility, and pilot selection |\n"
            "| `packages/earnings-themes/` | Quote-claim extraction, exact-span verification, support assessment, codebooks, and evaluation | Scaffold only |\n"
            "| `apps/earnings-pipeline/` | Thin application layer for configuration, stage coordination, checkpoints, and reporting | `earnings-pipeline browser setup`, and the `earnings-pipeline cohort` and `earnings-pipeline events` commands |\n",
            "| `packages/earnings-ingestion/` | Source adapters, raw snapshots, deterministic parsing, canonicalization, and entity resolution | Stage 3's canonicalizer and browser diagnostic path; Stage 4's artifact store, shared SEC client, and point-in-time DJIA cohort; Stage 5's event discovery, eligibility, and pilot selection; Stage 6's coverage report |\n"
            "| `packages/earnings-themes/` | Quote-claim extraction, exact-span verification, support assessment, codebooks, and evaluation | Stage 6's split, codebook, and gold contracts, with their anchor, validator, and wording guard |\n"
            "| `apps/earnings-pipeline/` | Thin application layer for configuration, stage coordination, checkpoints, and reporting | `earnings-pipeline browser setup`, and the `earnings-pipeline cohort`, `events`, `pilot`, `codebook`, and `gold` commands |\n",
        ),
        (
            "| `tests/fixtures/events/` | The synthetic event corpus, which replays offline to its frozen event manifest and pilot | Present |\n"
            "\n",
            "| `tests/fixtures/events/` | The synthetic event corpus, which replays offline to its frozen event manifest and pilot | Present |\n"
            "| `evaluation/djia-2024q3-2026q2/pilot-v1/` | The pilot's split, coverage report, drafting briefs, and signed gold: IDs, offsets, labels, hashes, and the maintainer's words, never release text | Stage 6's frozen split and report, and [GATE: 3] signed bundles |\n"
            "| `codebooks/djia-pilot/` | The pilot codebook | Codebook v0, approved in ADR 0003 |\n"
            "| `tests/fixtures/gold/` | The curated hard negatives, over Stage 1's fixtures | Present |\n"
            "\n",
        ),
        (
            "stages. Stages 1 to 5 are complete.\n",
            "stages. Stages 1 to 6 are complete.\n",
        ),
        (
            "the details. The roadmap resumes with Stage 6: the pilot codebook, split, and\n"
            "gold-set protocol.\n",
            "the details.\n"
            "\n"
            "**Stage 6: the pilot codebook, split, and gold-set protocol** is complete. It\n"
            "pins the pilot by content hash, splits it by issuer and time into 20 train, 8\n"
            "dev, and 7 test events, with 5 excluded, and reports its coverage. Codebook v0,\n"
            "discovered from the training partition alone, is approved in\n"
            "[ADR 0003](docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md). A Claude\n"
            "session drafts each bundle's gold under a committed brief, and the maintainer\n"
            "verifies every item, reads the release for omissions, and signs; committed\n"
            "files hold pointers, labels, and hashes, never release text. [GATE: 3] train\n"
            "bundles are signed. The [verification record](docs/verification/pilot-v1-gold-set.md)\n"
            "has the details.\n",
        ),
        (
            "  acquisition and processing states.\n"
            "- [Earnings-theme learning path](docs/earnings-themes.md) — the original staged\n",
            "  acquisition and processing states.\n"
            "- [Pilot codebook, split, and gold-set protocol specification](specs/pilot-codebook-split-and-gold-set-protocol.md)\n"
            "  — Stage 6: the pin, the issuer-and-time split, codebook v0, and the gold-set\n"
            "  protocol, with Claude-drafted, user-verified gold.\n"
            "- [Earnings-theme learning path](docs/earnings-themes.md) — the original staged\n",
        ),
    ],
}

DONE = {
    "CLAUDE.md": "## Current state: Stages 1–6 complete\n",
    "README.md": "stages. Stages 1 to 6 are complete.\n",
}

written = {}
for path, replacements in EDITS.items():
    text = Path(path).read_text(encoding="utf-8")
    if not any(old in text for old, _ in replacements):
        if DONE[path] not in text:
            raise SystemExit(f"{path}: holds neither its old texts nor its edit")
        print(f"unchanged: {path}")
        continue
    for old, new in replacements:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: an old text matches {text.count(old)} times")
        text = text.replace(old, new)
    written[path] = (text, len(replacements))
for path, (text, count) in written.items():
    Path(path).write_text(text, encoding="utf-8")
    print(f"edited {path}: {count} replacement(s)")
```

Apply `task19-state`, which prints `edited CLAUDE.md: 4 replacement(s)` and
`edited README.md: 7 replacement(s)`. On a resume, the extract prints `unchanged:`
and the script `unchanged: CLAUDE.md` and `unchanged: README.md`, and the values
already filled stay. Fill every `[GATE…]` slot left in the three files:

- the Gate 5 table, from Step 8's two outputs: the counts, labels, and drafting
  dates from the script, and the omission-pass and signing dates from each commit's
  body;
- the Drafting sessions table: Gate 3's and Gate 4's dates from the record's own
  sections, and Gate 5's from the script;
- the theme count, from the record's Gate 3 section, and the date of this step, for
  the README's status line;
- any limitation the user adds, which Step 9 asks for below, or delete that line.

Then:

```bash
grep -n '\[GATE' docs/verification/pilot-v1-gold-set.md CLAUDE.md README.md
```

Expected: nothing. Ask the user to read the record and the two current-state edits,
and whether to add a limitation, and wait for their approval before Step 11. A
resumed session asks again, since it cannot know whether the user approved. Make
any change the user asks for, and rerun the `grep`.

- [x] **Step 10: Final verification**

> Deviation: every check matched at `0aa7345`. After the final review's new offline test (`c77824a`), the default suite gives `1744 passed, 1 skipped, 24 deselected`, which the record's row 9 states.

```bash
uv run --locked --all-packages pytest tests/integration/test_stage6_pilot_v1.py tests/integration/test_stage6_wording.py -q -rs
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages python expirements/parser-fidelity/fetch_policy_pages.py verify
uv lock --check
git diff --stat 6e3666e -- uv.lock AGENTS.md .gitignore .python-version config tests/fixtures/cohort tests/fixtures/events tests/fixtures/canonical tests/fixtures/releases
```

Expected, checks: `14 passed`, with no skip; `1743 passed, 1 skipped, 24 deselected`; `280 passed`;
`All checks passed!` and `296 files already formatted`; `register quotes verified`; `uv lock --check`
passes; and the `git diff` prints nothing.

- [x] **Step 11: Commit**

```bash
git log --oneline -3
git add docs/verification/pilot-v1-gold-set.md CLAUDE.md README.md
git commit -m "docs(evaluation): record Stage 6's gold set, and refresh the current state"
```

---

## Handoffs

S §Handoffs to later stages lists what each later stage receives from Stage 6. Plan 9
gives each item its interface. Each later stage binds to the pin, pilot v1, by
content hash (GS2).

### The remaining 25 train and dev bundles

- **The rule.** Stage 11 uses the signed gold of all 28 train and dev events (S
  §Handoffs). Stage 6's exit needs three, so the other 17 train and 8 dev bundles
  follow Task 19, Steps 1 to 7, one bundle at a time, after this plan.
- **The order.** The pilot's selection order.
- **Dev.** A dev bundle may be drafted now that v0 is approved (GS13): `gold show
  --text` and `gold anchor` accept it, and refuse it before `codebook-v0.toml` is
  committed.
- **Test.** The 7 test bundles wait for Stage 14 (GS18). `gold show --text` and
  `gold anchor` refuse them (`readable`, Task 12). Stage 14 relaxes that guard in the
  commit that freezes its configuration, and never earlier.
- **The record.** Each bundle keeps its own commit, and the verification record's
  Gate 5 table gains a row.

### To Stage 7 (evidence selection and verification)

- **Train gold only.** Train gold may inform Stage 7's prompts; dev and test gold
  never may (A §749). `load_split(path).events_in(Partition.TRAIN)` names the train
  events, and `load_gold(path)` reads a signed file.
- **The canonical documents.** `from_fixture_json(text)` reads each parsed document
  under `data/runs/events/canonical/<doc_id>.json`, and `parsed_documents(transitions,
  pilot_hash)` names each event's `doc_id` (P9-17).
- **Narrative elements.** A gold quote sits in the most specific narrative element
  that holds it (P9-19). Stage 7 decides its own narrative set, and a difference
  from P9-19's is a finding to report.
- **Plan 3's four open items.** They stay with Stage 7. The gold builds every
  candidate through `parse_span_candidate`, and never stores a `VerifiedSpan`.

### To Stage 8 (semantic support assessment)

- **The curated hard negatives.** `load_hard_negatives(Path("tests/fixtures/gold/hard-negatives.toml"))`
  gives a `HardNegativeSet`: per fixture, its quotes as pointers, and its
  hard-negative claims with their `negative_kind`, `period`, `issuer`, or `section`,
  and the v0 theme each is confusable with. These are R8.1's misattribution fixtures.
- **In the pilot's gold.** Each signed bundle's `hard_negatives` hold more of them.

### To Stage 9 (deductive coding)

- **The contract.** `Codebook`, `Theme`, and `Example`, with `load_codebook` and
  `validate_codebook` in `earnings_themes/codebook.py`.
- **The frozen v0.** `codebooks/djia-pilot/codebook-v0.toml`, approved in ADR 0003.
  After approval, v0 never changes: a claim no theme fits is `unmatched` (R9.3).
- **Hash and approval.** `codebook_hash` excludes `status`, `approval`, and
  `content_hash` (P9-13). A later version keeps that rule, so its record can cite the
  hash before approval.

### To Stage 11 (feasibility pilot and threshold calibration)

- **The pin, the split, and the report.** `load_pinned(layout)`, `load_split(path)`,
  and `load_coverage(path)`.
- **The no-theme count.** `CoverageReport.no_theme` is empty in coverage v1. Stage 11
  writes coverage v2 with `NoThemeCount(partition, bundles, no_theme)` rows for train
  and dev, from each signed file's `no_theme` (P9-4), through `build_coverage(...,
  version=2)` extended to take them. Stage 14 adds test.
- **The gold and its drafts.**
  - The signed gold of the 28 train and dev events, once complete.
  - The kept drafts under `data/runs/gold/drafts/`, for GS5's edited, rejected,
    and added shares. Each signed file's `counts` holds them against its draft.
- **Release identification.** Each file's `release_identification.label` gives
  precision over the annotated events (R13.1). Who writes R8.4's labels is decided
  at Stage 11.
- **The limitations.** One annotator, and one drafting model family (the verification
  record).

### To Stage 12 (inductive and hybrid codebook)

- **The training partition only** (R12.3):
  `split.events_in(Partition.TRAIN)`, and their bundles.

### To Stage 14 (configuration comparison and held-out evaluation)

- **Dev.** The dev gold, for the comparisons.
- **Test.** The 7 test bundles are drafted and verified only after Stage 14 freezes
  its selected configuration, then scored once (R13.3, GS18). That commit relaxes
  `readable`'s test refusal, and Task 19's procedure drafts them.

### To Stage 16 (hosted quality ceiling)

- **The drafting conflict.** Claude Opus 5.5 drafted every item, so a Claude ceiling
  records that conflict (GS4), and the verification record's limitations state it.

### Deferred items that stay open

- **Stage 5's.** F27, `release-id/2`, and the per-candidate citations wait for the
  next events version (GS2; S §Deferred items).
- **Plan 3's four.** They stay with Stage 7.
- **The rest.** Every other open item in `specs/deferred_items.md`.

## Completion

After Task 19, run the final whole-branch review, with Global Constraints' Blinding
section in its dispatch. First put P9-22 to the user, in one question with the
recommended option first:

- **Skip Codex on this branch (recommended).** Write no `Codex reviewed` line. At
  the final review and at finishing-a-development-branch's Step 4b, state the
  reason: "GS13: a Codex review cannot carry the Blinding section, and the main
  checkout's `data/` holds pilot text, the held-out test bundles' included."
- **Run Codex from a detached worktree without `data/`.** From the main checkout,
  with a clean tree, note the two values, then run the review from the worktree:

  ```bash
  git merge-base HEAD main
  git rev-parse --short HEAD
  git worktree add --detach /tmp/plan9-codex <sha>
  mkdir -p /tmp/codex-review
  cd /tmp/plan9-codex && codex exec review -c sandbox_mode=read-only --base <merge base> -o /tmp/codex-review/<sha>.md > /tmp/codex-review/<sha>.log 2>&1; cd -
  git worktree remove --force /tmp/plan9-codex
  ```

  Read only the `.md`, never the `.log`, which may hold what Codex read. On exit 0
  with a non-empty `.md`, write `Codex reviewed <sha>`. Step 4b's rerun, if it needs
  one, takes that sha as its `--base`.

> Deviation: the user had answered P9-22 before Task 1 (2026-09-28): skip Codex, for the GS13 reason above, so it was not asked again and no `Codex reviewed` line was written. The final review (code-reviewer, Opus) found nothing Critical and three Important issues; `c77824a` lands them, with M2 and M3, by the user's choices of 2026-10-03; a scoped re-review found all seven items addressed, and `7f0359f` adds CLAUDE.md's `--tb=short` sentence, which the user approved, and the re-review's two docs Minors. The rest are deferred (specs/deferred_items.md) or dropped.

Then:

1. **Plan Completion Protocol** (writing-plans).
   - Run the resolve-before-defer gate.
   - Mark up this plan: tick the steps, add `> Deviation:` and `> Skipped:` notes,
     and add the status header. Notes hold IDs, counts, and hashes only
     (Blinding).
   - A gate whose remedy was not needed is not skipped: note what happened, such as
     "no refusal at the first freeze".
2. **The stage stamp.** Append a blank line and these two lines to the end of
   `specs/pilot-codebook-split-and-gold-set-protocol.md`, with the completion date in
   place of `YYYY-MM-DD` (S §Rollout):

   ```text
   > Stage 6: COMPLETE (YYYY-MM-DD) — implemented by plan 9 (specs/plans/completed/9-pilot-codebook-split-and-gold-set-protocol.md).
   > Next: resume the roadmap.
   ```

3. **Deferred items.** This plan closes no earlier item (S §Deferred items). Append a
   `## 9-pilot-codebook-split-and-gold-set-protocol — YYYY-MM-DD` section to
   `specs/deferred_items.md`, with the completion date. It holds at least this item,
   and any other the gate deferred, in the schema of `references/deferred-backlog.md`:

   ```markdown
   - [ ] Draft, verify, and sign the other 17 train and 8 dev bundles of pilot v1
         (plan 9, Handoffs). Stage 6's exit needed three; Stage 11 uses all 28.
         Each follows plan 9's Task 19, Steps 1 to 7
         (specs/plans/completed/9-pilot-codebook-split-and-gold-set-protocol.md):
         a fresh Claude Opus 5.5 session per bundle under
         evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md, then the user's
         verification, omission pass, and signature. Size: plan. Done when: all 28
         train and dev gold files under evaluation/djia-2024q3-2026q2/pilot-v1/gold/
         are committed and `earnings-pipeline gold validate` passes.
   ```

   Commit steps 1 to 3 together:

   ```bash
   git log --oneline -3
   git add specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md specs/pilot-codebook-split-and-gold-set-protocol.md specs/deferred_items.md
   git commit -m "docs(specs): mark up plan 9, record Stage 6's completion, and defer the other bundles"
   ```

4. **Backlog triage.** Run
   `uv run --no-project --python 3.13 python ~/.claude/skills/writing-plans/scripts/deferred_stats.py`,
   and report its summary line. Present the triage rubric if its thresholds trip.
5. **Retire the plan and the spec.** No other live plan implements the spec. The
   extract helper reads the plan at its live path, so save the retire script before
   the plan moves:

Create `/tmp/plan9-retire.py`:

```python
"""After the git mv: re-point the retired plan's and spec's paths, and mark the spec
complete under its title.

usage: python3 /tmp/plan9-retire.py <completion date, YYYY-MM-DD>
"""

import sys
from pathlib import Path

day = sys.argv[1]
MOVED = {
    "specs/pilot-codebook-split-and-gold-set-protocol.md": (
        "specs/completed/pilot-codebook-split-and-gold-set-protocol.md"
    ),
    "specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md": (
        "specs/plans/completed/9-pilot-codebook-split-and-gold-set-protocol.md"
    ),
}
FILES = [
    "CLAUDE.md",
    "README.md",
    "docs/data-dictionary.md",
    "docs/verification/pilot-v1-gold-set.md",
    "docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md",
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
spec = Path(MOVED["specs/pilot-codebook-split-and-gold-set-protocol.md"])
title = "# Pilot codebook, split, and gold-set protocol\n"
text = spec.read_text(encoding="utf-8")
assert text.startswith(title), "the spec's title moved"
status = (
    f"\n**Status: COMPLETE ({day})** — Stage 6; implemented by plan 9;"
    " retired to specs/completed/.\n"
)
spec.write_text(title + status + text[len(title) :], encoding="utf-8")
print(f"marked {spec} complete")
```

   ```bash
   python3 /tmp/plan9-extract.py /tmp/plan9-retire.py
   git mv specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md specs/plans/completed/
   git mv specs/pilot-codebook-split-and-gold-set-protocol.md specs/completed/
   python3 /tmp/plan9-retire.py [GATE: the completion date, YYYY-MM-DD]
   git grep -n -e "specs/pilot-codebook-split-and-gold-set-protocol.md" -e "specs/plans/9-pilot" -- . ':!specs/plans/completed' ':!specs/completed'
   uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py tests/contracts/test_data_dictionary.py -q -rs
   ```

   The script re-points every path to the two files outside the retired plans, and
   marks the spec complete under its title.

   Expected: `extracted /tmp/plan9-retire.py: 44 lines`; then
   `re-pointed CLAUDE.md: 2`, `re-pointed README.md: 1`,
   `re-pointed docs/data-dictionary.md: 1`,
   `re-pointed docs/verification/pilot-v1-gold-set.md: 2`,
   `re-pointed docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md: 2`,
   `re-pointed specs/evidence-linked-theme-extraction-roadmap.md: 2`, and
   `marked specs/completed/pilot-codebook-split-and-gold-set-protocol.md complete`;
   no `git grep` output; and the tests pass. Then commit:

   ```bash
   git log --oneline -3
   git add specs/plans/completed/9-pilot-codebook-split-and-gold-set-protocol.md specs/completed/pilot-codebook-split-and-gold-set-protocol.md CLAUDE.md README.md docs/data-dictionary.md docs/verification/pilot-v1-gold-set.md docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md specs/evidence-linked-theme-extraction-roadmap.md
   git commit -m "chore(specs): retire plan 9 and the Stage 6 spec"
   ```

6. **The roadmap.** Run the derive-roadmap skill's reconcile step on
   `specs/evidence-linked-theme-extraction-roadmap.md`, as S §Rollout asks:
   - tick Stage 6;
   - re-validate Stages 7, 8, 9, 11, 12, 14, and 16 against what shipped
     (Handoffs above), including P9-3's file names, P9-4's `no_theme`, and P9-19's
     narrative elements.

   Then commit:

   ```bash
   git log --oneline -3
   git add specs/evidence-linked-theme-extraction-roadmap.md
   git commit -m "docs(roadmap): tick Stage 6 and reconcile the later stages"
   ```

7. **Integrate** with finishing-a-development-branch. Its Step 4b follows the user's
   P9-22 answer: skipped with the stated reason, or run as above.
   - Open a pull request from `stage-6-pilot-codebook-split-and-gold-set` to `main`,
     as Stages 1 to 5 did.
   - The branch was unpushed at planning, so this is its first push, and the
     repository is public. `data/` stays local. Before the push, check every commit
     the push publishes, and the tree at its tip, by count, so no path is printed:

     ```bash
     git fetch origin main
     git rev-list --count origin/main..HEAD -- data/
     git ls-tree -r --name-only HEAD -- data/ | awk 'END { print NR }'
     ```

     Expected: `0` and `0`. Otherwise stop and report to the user: do not push, and
     do not rewrite history without the user's go-ahead. After the pull request
     opens, check its file list too:
     `gh pr view --json files --jq '[.files[].path | select(startswith("data/"))] | length'`
     prints `0`.
8. **Report** (S §Rollout).
   - State the commands actually run, and their results.
   - State that no model was called from code and no SEC request was sent.
   - Name the drafting sessions: which ran, on which dates, and with which model.
   - State how many bundles are signed, and give the split's, the coverage
     report's, and codebook v0's content hashes.
   - Name the eight flagged readings, P9-12 to P9-19, and whether the user accepted
     each as written before execution.
   - State the user's P9-22 answer, and whether Codex ran.
