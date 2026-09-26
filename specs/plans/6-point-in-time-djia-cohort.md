# Point-in-Time DJIA Cohort (Stage 4) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 4 — on plan
> completion, tick the stage and re-validate later stages against what shipped.
>
> This plan is Stage 4's only plan, so its completion completes Stage 4. The cohort
> spec stays live for Stage 15 (P6-1). Completion below says exactly what it does.
>
> **Amended 2026-09-26** by `specs/pdf-citation-text.md`, which this plan also
> implements. Task 16b, before Task 17, cites PDF notices through `pdftext-1` and
> adds `cohort terms --saved` (P6-24). It brings the plan's one new dependency,
> `pypdf==6.19.0`, and every Expected count after it is restated.

**Goal:** Build roadmap Stage 4 in `earnings-ingestion` and freeze the cohort it
defines:

- a versioned, point-in-time DJIA universe over calendar period ends in
  `[2024-07-01, 2026-07-01)`, with public-information cutoff `2026-09-22`;
- security-level membership intervals, reconstructed from a dated anchor snapshot and
  the official changes, and resolved to issuers and zero-padded CIKs;
- a coverage and conflict report;
- all of it frozen before any earnings document is acquired;
- the shared SEC client that closes R1.3 (D5), through which this stage and every
  later adapter send SEC requests;
- PDF citation text, `pdftext-1`, because S&P Dow Jones Indices publishes its index
  notices as PDFs (Task 16b, P6-24).

It ships a synthetic cohort that replays offline, and the real cohort's frozen
manifest, built from locally saved evidence and reviewed and signed by the user.

**Architecture:**

- **Acquisition** (`packages/earnings-ingestion/src/earnings_ingestion/fetch/` and
  `sec/`).
  - A polite client ported from Stage 1's `pf_fetch.py` (D5: port it, never import
    it): one identity, one thread-safe throttle, bounded retries with backoff and
    jitter, `Retry-After`, and a stop on a persistent 403.
  - A robots.txt gate.
  - A content-addressed artifact store under `data/raw/` that never overwrites a
    file.
  - The shared SEC client: 0.5 s between request starts across SEC hosts, the
    identity in `EDGAR_IDENTITY`, and one client per machine, held by a lock.
  - Pure readers of SEC's ticker list, submissions, and N-PORT holdings.
- **The cohort** (`…/cohort/`).
  - Curated TOML files (universe, evidence, overrides) cite saved artifacts by hash
    and locator, and hold no source wording.
  - `build` verifies every citation against the saved bytes. It then:
    - reconstructs half-open intervals from the anchor and the official changes;
    - resolves securities to issuers by SEC ticker and name;
    - reconciles corroborating snapshots and a tracking fund's holdings with the
      reconstruction;
    - reports every conflict, ambiguity, gap, and difference as a finding.
  - `freeze` refuses while a blocking finding stands. Otherwise it writes a
    versioned, content-hashed manifest atomically.
- **Commands** (`apps/earnings-pipeline`): `earnings-pipeline cohort fetch`,
  `register`, `fetch-sec`, `cite`, `build`, `freeze`, `terms`, and `verify-live`.
- **Evidence and rights.**
  - A second register, `docs/membership-source-register.toml`, records the
    index-membership sources.
  - Committed files hold facts and citations, never a source's wording.
  - Saved artifacts stay local under `data/raw/cohort/`.

**Tech Stack:**

- Python 3.14.0 and uv 0.12.15. One new dependency, `pypdf==6.19.0`, pinned exactly
  (P6-24): Task 16b adds it, and `uv.lock` changes there and nowhere else.
- Already declared and locked:
  - httpx 0.28.1, for both clients;
  - lxml 6.1.3, for N-PORT XML, and under `walker-1`;
  - pydantic 2.13.5;
  - typer 0.27.2, for the CLI;
  - pytest 9.1.1 and Ruff 0.16.8.
- Added by Task 16b: pypdf 6.19.0, pure Python, for `pdftext-1`.
- From the standard library: `tomllib`, `fcntl`, `threading`, `email.utils`,
  `json`, `urllib.parse`, and `unicodedata`.

## The spec this plan implements

The roadmap's Stage 4 entry scopes this plan (`specs/evidence-linked-theme-extraction-roadmap.md`,
Stage 4): its Spec, Gap closed, Consumes, Produces, and Exit lines, and decision
D5.

- **The stage spec.** `specs/point-in-time-djia-cohort.md`, cited as `P`, is the spec
  for Stages 4 and 15. Its ROUTING line sends it straight to writing-plans. This
  plan implements these parts of it:
  - the Stage 4 decisions P-C1, P-C3, P-C4, and P-C7's cohort-before-acquisition
    half;
  - P-C2's membership-reference definition, but not its event join, which is
    Stage 5's;
  - §Temporal definitions (the cutoff and the membership reference);
  - §Data contracts: the universe definition and the membership assertion;
  - §Membership evidence and source rights;
  - §Issuer resolution;
  - §Failure handling, its Stage 4 items;
  - §Verification: P-VF's interval, resolution, conflict, and cutoff cases, P-VI's
    membership-interval and issuer-resolution legs, and P-VL;
  - §Acceptance criteria for Stage 4 (P-A4).
- **`AGENTS.md`** (`A`):
  - A §249–269, index membership and identifiers, including the zero-padded CIK at
    A §264;
  - A §429, the entity-resolution rules;
  - A §242, the source register;
  - A §393–408, the access policy that the shared client implements (R1.3).
- **D5.** Stage 4 builds the shared SEC client and closes R1.3. Stage 5's EDGAR
  adapter sends through it. Stage 1's `expirements/parser-fidelity/pf_fetch.py` is
  the reference design: port it, never import it.
- **Out of scope.** Stage 5's expected-event, eligibility, and pilot-selection
  contracts and their P-VF cases. Stage 15.
- **The user's decisions of 2026-09-26.** The planning session put three choices to
  the user, and P6-2, P6-3, and P6-4 record the answers:
  - the anchor and its corroboration;
  - what the repository commits;
  - the selection policy's name.

  A fourth answer, a fixed 30-name roster for every quarter, was withdrawn by the
  user. The point-in-time design stands, so never revive a fixed roster.

## Global Constraints

Every task's requirements include these.

**Locators:**

- `A §n` is `AGENTS.md` at line `n`.
- `Rn` are requirements in `specs/evidence-linked-theme-extraction.md`.
- `P` cites `specs/point-in-time-djia-cohort.md`:
  - `P-C1`–`P-C7` are its Decisions rows;
  - `P-A4` is its Stage 4 acceptance criteria;
  - `P-VF`, `P-VI`, and `P-VL` are its fixture, offline-integration, and live
    verification groups;
  - `P §Section` cites a section by name.
- `Dn` are the roadmap's decisions.
- `P6-n` are this plan's decisions, listed below.

**Versions.**

| Name | Value | Where |
| --- | --- | --- |
| Ingestion record schema | `1`, unchanged: the new records join it (P6-5) | `INGESTION_SCHEMA_VERSION` |
| Core schema | `2`, unchanged | `earnings_core` |
| Canonicalization of cited pages | `walker-1`, unchanged | `canonical/` |
| PDF citation text | `pdftext-1` (pypdf 6.19.0) | `cohort/pdftext.py` (Task 16b) |
| Membership reference | `first_publication_time` | `universe.toml` (Task 17) |
| Selection policy | `djia-pilot/1`, named now, defined by Stage 5 (P6-4) | `universe.toml` (Task 17) |
| SEC client | 0.5 s between request starts (2 req/s), shared across SEC hosts | `sec/client.py` (Task 4) |
| Web client | 1.0 s between request starts | `cohort/web.py` (Task 14) |
| Request budget | 500 per client per run | `fetch/client.py` (Task 2) |

**Offline and no models.**

- Default tests make no network call and no billable call. They need no credential,
  and they use no proprietary roster: every cohort test runs on the synthetic
  cohort.
- Live tests carry the `live` marker. Each skips without its identity and runs only
  with `-m live`, and only at a human gate.
- **`EDGAR_IDENTITY` may already be exported in your shell.** A live test's skip
  guard then does not stop it, and it sends real requests. Never pass `-m live`
  outside a gate. To check collection, use `--collect-only`.
- No step calls a model.

**Network access.** Live requests happen only at the gates in "Human gates" below,
each after the user's clear yes in chat.

- Never bypass robots.txt, authentication, paywalls, or rate limits.
- A persistent 403 stops the run. Report it, and never rotate identity (A §404).
- When robots.txt or a site refuses automated fetching, the user saves the page in
  a browser and `earnings-pipeline cohort register` records it (P6-17).
- Nothing downloads a dependency, and `uv.lock` stays as it is, except at Task 16b's
  gated `uv add` of `pypdf==6.19.0` (Human gates).

**Identities.** `EDGAR_IDENTITY` (the SEC client) and `SOURCE_IDENTITY` (the web
client) belong to the user and are configured outside Git. Never print them, commit
them, or record them anywhere. A `Retrieval` record never carries them.

**Do not touch:**

- Stage 1's frozen harness and records: every file that
  `expirements/parser-fidelity/FROZEN.toml` lists, `tests/fixtures/releases/` and
  its gold, the V1 and V2 records, and ADR 0001. Leave `pf_fetch.py` unchanged: it
  is ported, never imported, and no package imports anything under
  `expirements/`.
- `walker-1`:
  - `packages/earnings-ingestion/src/earnings_ingestion/canonical/`;
  - `tests/fixtures/canonical/`;
  - the golden test.

  Citations use `canonicalize` as it is.
- `AGENTS.md`. Other files cite it by line number (`CLAUDE.md` §Gotchas), and this
  plan needs no change to it.
- `specs/point-in-time-djia-cohort.md`, except the Rollout stamp that Completion
  appends (P6-1).
- `.gitignore`: no edit, and its credentials block stays last. `data/*` already
  ignores `data/raw/cohort/`, `data/runs/sec/`, and `data/runs/cohort/`.
- `.python-version`, which pins 3.14.0.

**Staging discipline.**

- `git add` only the paths a task names, never `git add -A` or `git add .`.
- After each commit, `git status --short` must print nothing, apart from local
  untracked files that predate this plan. So a later task's file never enters an
  earlier commit.
- `tests/fixtures/cohort/` is generated, and only Task 13 commits it.
- `config/universe/djia/` is curated, and only Task 17 commits it.

The user may commit on this branch while the plan runs. Run `git log --oneline -3`
before each commit, and never rewrite a commit you did not make.

**Unicode escapes.** Every new or replaced Python file in this plan is ASCII, except
`§` in citations such as `A §404`.

- Tests build non-ASCII inputs from code points with `chr(0x...)`.
- No file carries a `\u` escape that a tool channel might decode on the way to disk.
- Each task that writes Python runs the escape check below. It prints
  `escapes intact`, or else the name of each file holding another non-ASCII
  character.

**Writing files from this plan.** Every code block that holds a whole file, or text
to append, follows a line of one of three forms:

- ``Create `<path>`:``;
- ``Replace `<path>` with:``;
- ``Append to `<path>`:``.

Extract each such file with the helper below rather than retyping it. Retyping
about 10,000 lines invites silent slips, and a tool channel that decodes an escape
would do it again on a retry. The Preconditions save the two helpers once, as
`/tmp/plan6-extract.py` and `/tmp/plan6-escapes.py`. If `/tmp` has been cleared,
save them again from here.

`/tmp/plan6-extract.py`:

````python
"""Extract one file block from plan 6; run from the repository root.

usage: python3 /tmp/plan6-extract.py <path> [block number, default 1]
"""

import sys
from pathlib import Path

PLAN = Path("specs/plans/6-point-in-time-djia-cohort.md")
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

`/tmp/plan6-escapes.py`:

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

- A step that says **extract** a path runs `python3 /tmp/plan6-extract.py <path>`,
  which prints `extracted <path>: <n> lines`, or `appended to <path>: <n> lines` for
  an append.
- The block number is `1` unless the step names another. A path written twice takes
  `2` the second time.
- If the escape check names a file, extract that file again and rerun the check.

**Lint.** `uv run --locked ruff check .` and `uv run --locked ruff format --check .`
pass after every task, and the code below already passes both.

- The Expected `N files already formatted` counts assume a clean checkout: 157
  before Task 1, growing with each task's new Python files.
- A different count with no `Would reformat` line comes from local untracked Python
  files, and is not a failure.

**Expected outputs.** At plan time this plan was replayed on a clean checkout from
the Preconditions through Task 16, and those Expected outputs are what the replay
printed. Task 16b, added by the amendment of 2026-09-26, was replayed the same way
on Task 16's code, its dependency gate included, and every count after it is
restated from that replay. Three kinds of step could not be replayed, so their
outputs are predictions, marked as such:

- the live steps;
- Task 17's real cohort;
- Task 18's record.

If a count elsewhere differs while nothing fails, stop and report it rather than
editing a test to match.

**Test imports.** Ruff sorts `earnings_core` and `earnings_ingestion` as third-party
imports in test files, in one block with `pytest`, so keep the imports as written.
Inside `earnings_ingestion` they are first-party.

**Public repository.** `origin` (https://github.com/lowmason/earnings-themes) is
public, so everything committed is published.

- The synthetic cohort is invented and redistributable.
- The real cohort's committed files hold facts, URLs, locators, and hashes, never a
  source's wording (P6-3).
- Saved pages, SEC records, and live-verification records stay under the gitignored
  `data/`.
- The real `overrides.toml` names its reviewer, who is the user (P6-18).

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

The spec and the roadmap leave these choices open, so the plan makes them. The user
can overturn any of them before execution. The planning session of 2026-09-26 put
three to the user, and P6-2, P6-3, and P6-4 record the answers. The code records each
decision where it applies. None adds, removes, or retunes a spec rule: where a rule
needed a reading, the reading is stated.

**P6-1 — The cohort spec stays live.** `specs/point-in-time-djia-cohort.md` is the
stage spec for Stages 4 and 15, and Stage 15 has no plan yet.

- The Plan Completion Protocol would retire a spec that no live plan names, and at
  this plan's completion none would. This plan overrides that default.
- Completion appends Stage 4's stamp to the spec's Rollout, retires only this plan,
  and leaves the spec in `specs/`.

**P6-2 — The anchor and its corroboration (the user's answer).**

- **The anchor.** The anchor is the English Wikipedia revision of "Dow Jones
  Industrial Average" that was current at the window's start: the latest revision
  saved before `2024-07-01T00:00:00Z`.
  - It is `secondary` evidence, text under CC BY-SA 4.0.
  - Its `as_of` and `published_on` are both the revision's UTC date. A revision
    states the roster when it was saved, and is never backdated.
- **The changes.** S&P Dow Jones Indices' own announcements are the `official`
  change evidence.
- **Corroboration.** The N-PORT holdings of the SPDR Dow Jones Industrial Average ETF
  Trust (DIA), read from EDGAR, corroborate every quarter. They are labeled
  `etf_proxy` and never add or remove a member.
- **The user's list.** The user's 30-name list, supplied in chat on 2026-09-26, is a
  `user_supplied` check list, compared and reported only. It was published after the
  cutoff, so it is also withheld.

**P6-3 — Facts and citations, never source text (the user's answer).**

- **Committed.** Committed curated files and manifests hold facts (dates, names,
  tickers, CIKs), URLs, the raw artifact's SHA-256, and locators that hash the cited
  text.
- **Never committed.** No source's wording enters Git. `cohort cite` prints the cited
  text to stderr only.
- **Local.** Saved artifacts stay under the gitignored `data/raw/cohort/`.
- **The synthetic cohort** is invented, so its pages are committed as test data.

**P6-4 — `selection_policy_version = "djia-pilot/1"` (the user's answer).** The
universe definition names the pilot-selection policy now. Stage 5 defines the rules
behind that name, from P §Deterministic pilot selection, or else bumps the name.

**P6-5 — Retrieval metadata belongs to ingestion.** Plan 3 left two options. This
plan takes the first:

- `earnings_ingestion.fetch.records.Retrieval` records one retrieval at ingestion's
  own grain;
- core gains no field and keeps schema version 2.

Every new ingestion record joins schema version `1`, since no earlier record's fields
change.

**P6-6 — Reconstruction and assertion status** (`cohort/intervals.py`). This is how a
security's statements become intervals.

- **One sequence.** A security's statements must form one sequence: its anchor row,
  if the anchor lists it, then additions and removals that alternate, each strictly
  after the anchor's date.
- **Merging.** Identical claims from several items, meaning the same action, date,
  and timing, are one transition.
- **Ambiguous.** An addition and a removal on one date are `ambiguous`, whatever
  their timing.
- **Conflicting.** Any other break is `conflicting`:
  - an addition while a member;
  - a removal while not one;
  - a change on or before the anchor's date;
  - one transition stated with two timings.
- **Until review.** A security whose statements break the sequence has every
  statement marked and no interval. Its finding holds the freeze until a
  `reject_assertion` override removes the wrong statement. Only a `conflicting` or
  `ambiguous` statement can be rejected.
- **The rest.** Statements first published after the cutoff are `withheld`. The rest
  are `supported`.
- **Interval bounds.** Starts are inclusive and ends exclusive. An open interval has
  no `effective_to`. An anchored start is a lower bound (basis `anchor_snapshot`),
  never an entry date.

**P6-7 — Findings and acknowledgements** (`cohort/findings.py`).

- **Identity.** A finding's ID is `<kind>:<subject>`, and its `digest` hashes what
  it says.
- **Counts.** A `member_count` finding fires wherever the reconstructed roster's size
  differs from `expected_member_count`: at the anchor's date, and at each interval
  bound up to the cutoff. It is blocking.
- **Acknowledgement.** Only `member_count` and `difference` findings can be
  acknowledged. An `acknowledge` override names the finding and its digest.
  - When the evidence changes what the finding says, the acknowledgement is stale.
  - A stale acknowledgement blocks the freeze until the reviewer reads the new
    finding.
- **Other blocking findings** resolve by evidence or by their own override kinds.

**P6-8 — Issuer resolution by SEC ticker and name** (`cohort/resolution.py`,
`cohort/names.py`).

- **Proposal.** A cited ticker proposes a CIK through SEC's `company_tickers.json`.
- **Confirmation.** The candidate is confirmed only when SEC's submissions for that
  CIK list the ticker and a name, current or former, covers the cited name. The two
  names are compared by one rule, token cover:
  - both names are normalized (NFKD to ASCII, parentheticals dropped, case folded,
    apostrophes dropped, `&` read as "and");
  - legal-form words (`inc`, `corp`, `co`, and the like) are dropped;
  - the remaining tokens of the cited name must all appear in the SEC name.

  There is no fuzzy score (A §429).
- **Outcomes.** One confirmed CIK resolves the security. No candidate leaves it
  `unresolved`, and several leave it `conflicting`.
- **Blocking.** An unresolved or conflicting security blocks only if it is in scope
  (P6-13). A `set_issuer` or `retain_unresolved` override decides it. A retained
  security is excluded from the candidate issuers, with its reason.
- **IDs.** `issuer_id` is `cik-<10-digit CIK>`, and several securities of one CIK
  derive one issuer row.
- **Timeliness.** Only rows from items published on or before the cutoff take part
  (P6-12). SEC's identity records are retrieved after the cutoff. They establish
  identity, never membership, and the report states that limitation.

**P6-9 — Locators** (`cohort/locators.py`). A citation names the source, its URL,
the saved artifact's reference, and one or more locators. There are two kinds:

- `text_span` gives code-point offsets into the `walker-1` canonical text of an HTML
  artifact, with that text's hash;
- `json_pointer` gives an RFC 6901 pointer into a JSON artifact.

The build rechecks every locator against the saved bytes:

- `cited_sha256` hashes the cited text, or the canonical JSON of the value at the
  pointer;
- each curated row's name and ticker must occur in its cited text.

`walker-1` writes a table row as one line of tab-separated cells, so `cite --line`
cites a whole row. **Amended:** text spans also run over `pdftext-1` text for a PDF artifact (P6-24).

**P6-10 — Corroboration** (`cohort/corroboration.py`). Each dated snapshot is
compared with the reconstructed roster on its own date.

- **Secondary snapshots** match by `security_id`.
- **Fund holdings** match differently:
  - only equity holdings count, with `assetCat` `EC` or none;
  - a holding matches the one security whose cited name it covers, or the security a
    `holding_alias` override names;
  - any other holding is listed as unmatched.
- **Which filings.** For each report date, the latest filing filed on or before the
  cutoff is compared, and each earlier one is `superseded` (noted). Filings after the
  cutoff are compared and marked withheld.
- **Differences.** A difference blocks until acknowledged, unless the snapshot is
  withheld or a user-supplied check.
- **Gaps.** A calendar quarter from `period_end_start` through the cutoff with no
  timely corroborating snapshot is a `gap`, which is noted and does not block.

**P6-11 — The anchor's refusals.** An anchor is refused, with a blocking
`missing_anchor` finding that records the reason, if:

- it is not `official` or `secondary` evidence;
- it was published after its `as_of` date (it would be backdated);
- its `as_of` is after `period_end_start`;
- it was published after the cutoff.

Without a usable anchor, only announced intervals exist, and the freeze is refused.

**P6-12 — The cutoff (P-C4).** An item first published after `2026-09-22` is
reported as `withheld` and never applied. None of these ever uses it:

- the intervals;
- issuer identity;
- holdings matching;
- the counts.

A withheld difference never blocks. So evidence published after the cutoff cannot
change the manifest's content, and hence its version.

**P6-13 — Candidate issuers.** A security is in scope when its interval overlaps
`[period_end_start, cutoff + 1 day)`. Membership is judged at
`first_publication_time`, and a release published up to the cutoff can be eligible.
`candidate_issuer_ids` is the sorted union of the in-scope securities' issuers.

**P6-14 — The freeze** (`cohort/freeze.py`).

- **Refusals.** It refuses on a blocking finding or a stale acknowledgement, and
  names each one.
- **The content hash** is SHA-256 over the manifest's canonical JSON without
  `universe_version`, `content_hash`, and `created_at`.
- **Versions.** Content that matches a frozen manifest *is* that version, and nothing
  is written. New content takes the next version.
- **Writing.** The manifest is indented JSON with sorted keys, written through
  `write_new`: a temporary file linked into place, never replacing a file.
- **Reading.** `load_manifest` rechecks the hash and the file name, and needs no
  saved artifact.
- **Format.** The manifest is JSON, not Parquet. It is one small, versioned,
  committed record, like the canonical fixtures. Stage 5 may load its rows into
  Polars.

**P6-15 — The registers.**

- **The membership register.** Index-membership sources get a second register,
  `docs/membership-source-register.toml`, with A §242's fields plus the evidence
  class, the roles, and the rights.
  - It quotes no source.
  - A published source's terms are tracked by `terms_url` and `terms_sha256`, which
    `earnings-pipeline cohort terms` computes: the `walker-1` canonical text's
    SHA-256 for HTML, otherwise the bytes'. **Amended:** it also hashes a copy saved in a browser, with `--saved` (P6-24).
  - A list the user supplied has no terms page.
- **`sec-edgar`** stays in `docs/source-register.toml`. Its `access_method` now names
  the shared client (Task 4).
- **`source_register_version`** hashes the entries a manifest cites, and the whole
  `sec-edgar` table.
- **Rights.** Every cited source's rights are copied into the manifest. Unclear
  rights are `local_only`.

**P6-16 — The shared SEC client (R1.3, D5).** It is `fetch/client.py`'s
`PoliteClient`, ported from `pf_fetch.py`, under `sec/client.py`'s policy.

- **Rate.** Request starts are spaced 0.5 s apart across `www.sec.gov` and
  `data.sec.gov`, redirect hops included. A thread-safe throttle is shared by
  workers, within a budget of 500 requests per run.
- **Identity.** It sends `EDGAR_IDENTITY` as the User-Agent and never records it.
- **Retries.** Timeouts are 30 s, or 10 s to connect. There are four attempts, with
  exponential backoff from 1 s, capped at 60 s, and each delay jittered to between
  50% and 100% of itself.
- **`Retry-After`.** It honours the header, and a request to wait over 300 s stops
  the run.
- **Stops.** A 403 on an attempt and again on its retry stops the run, as does SEC's
  block page. The identity never changes.
- **One per machine.** It holds an `flock` on `data/runs/sec/sec-client.lock` while
  open.
  - A lock coordinates one machine only.
  - Stage 1's harness keeps its own client and lock. The two must never run live at
    the same time.
- **Pure paths.** URL builders live in `sec/urls.py`, which imports no HTTP library,
  so the offline build never loads a network client.

**P6-17 — The web client** (`cohort/web.py`). It fetches non-SEC sources: the roster
revision and the index announcements.

- One request per second, with the identity in `SOURCE_IDENTITY`.
- Only the hosts it is opened for, and never an SEC host.
- Each page is checked against its site's robots.txt (RFC 9309) first.
- A disallowed page raises `RobotsRefusal` and is never requested. The user then
  saves it in a browser, and `cohort register` records it as `saved_by_user` with the
  URL and time it was saved.

**P6-18 — Curated files** (`config/universe/djia/`).

- **The files.** `universe.toml`, `evidence.toml`, and `overrides.toml`.
- **Reading.** Each is read as TOML, converted to canonical JSON, and validated by
  strict models, so an unknown key or a wrong type is refused.
- **Overrides** are version-controlled review decisions (P §Issuer resolution). Each
  records its rationale, reviewer, recording date, and effective dates, and the
  citations it relies on. A `set_issuer` override must cite.
- **The reviewer.** In the real file the reviewer is the user, who signs each
  override. The implementer never fills in a reviewer.

**P6-19 — The synthetic cohort lives in the package** (`cohort/synthetic.py`).

- Stage 5 consumes its frozen manifest as a fixture, so the generator is package
  code, not a test helper.
- It invents a small index that exercises every Stage 4 P-VF case, and its evidence
  is redistributable test data.
- `tests/fixtures/cohort/` must regenerate from it byte for byte.
- `.gitattributes` keeps every fixture byte, because saved artifacts are named by
  their hash.

**P6-20 — The live verification (P-VL)** (`cohort/live.py`). It re-reads every source
the cohort relies on:

- each cited source's terms page, hashed as the register hashes it;
- each curated evidence URL, compared with the saved bytes.

It then rebuilds from the saved artifacts and compares the result with the latest
frozen manifest's content hash.

- **Outcomes.** Each check is `unchanged`, `changed`, `refused`, or `failed`.
- **Refusals.** A robots refusal or a persistent 403 is recorded, never hidden. A
  client that meets a 403 sends nothing more.
- **The record.** A `LiveVerification`, with each check's retrieval metadata, is
  written under the gitignored `data/runs/cohort/live/`.

**P6-21 — The format probe.** SEC's live formats are checked once, before the
synthetic cohort builds on the readers' assumptions: Task 5's gated
`tests/integration/test_sec_formats_live.py`.

- It sends at most eight requests and saves nothing.
- It also confirms the fund's CIK by its name.
- It is not an Exit clause. A failure stops the plan for a reader fix, because the
  synthetic cohort encodes the readers' formats.

**P6-22 — Commands live in the application**
(`apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`).

- The package functions take saved bytes and callables.
- The CLI opens clients, reads identities, and prints.
- `build` exits 1 while anything blocks, and `freeze` refuses the same way.
- `cite` prints the TOML to commit on stdout and the cited text on stderr, so no
  wording is pasted by accident.

**P6-23 — Day precision.** Intervals are dates. Each bound keeps the announced timing
(`before_open`, `after_close`, or `unspecified`) and its basis (`announced` or
`anchor_snapshot`). Stage 4 never orders a change against a release on the same day:
that is Stage 5's eligibility decision (P-C2), and the report states it.

**P6-24 — PDF citation text, `pdftext-1`** (`cohort/pdftext.py`; the amendment
`specs/pdf-citation-text.md`, PT-1 to PT-9). S&P DJI publishes its index notices as
PDFs. So a PDF is cited through a second citation-text policy, which the media type
chooses beside `walker-1` (PT-1). A whole-document hash citation was rejected: it
would drop P6-9's check that a row's name and ticker occur in its cited text.

- **The policy.** Given a saved PDF's bytes, `pdftext-1`:
  1. reads them with pypdf 6.19.0, holding pypdf's logger below ERROR for the call
     and restoring it after, since the text's hash, not pypdf's recovery warnings,
     is the authority (PT-5);
  2. takes each page's plain-mode `extract_text()`, in page order;
  3. normalizes the text to NFC, the repository's convention, never NFKC;
  4. collapses each line's whitespace runs to one space, strips its ends, and drops
     the lines left empty, so a needle reads as the page does (PT-2);
  5. joins every line, across pages, with `\n`.

  The result is the citation text. It is hashed and cited as `walker-1`'s canonical
  text is, by the SHA-256 of its UTF-8 and by half-open code-point offsets, and no
  `CanonicalDocument` is built (PT-8).
- **Refusals.** It refuses three kinds of input: bytes pypdf cannot read; any
  encrypted PDF, even one that an empty password opens; and a PDF with no text
  layer, since OCR is out of scope.
  - `pdf_text` raises its own `PdfTextError`. `ArtifactText` turns it into a
    `LocatorError` that names `pdftext-1`, as it already turns a `walker-1` failure
    into one.
  - The spec has `pdf_text` raise `LocatorError` itself. That would make
    `pdftext.py` import `locators.py`, which imports it, so the conversion lives in
    `ArtifactText`. A citation meets the same refusal.
- **The pin.** pypdf is pinned exactly, `pypdf==6.19.0`, because the version defines
  the policy (PT-3).
  - Another version's output is `pdftext-2`, with new citations, never an edited
    hash.
  - The `browser-capture` extra's exact pins are the precedent.
  - The golden test is the drift alarm.
- **Media types.** `check_media_type` refuses bytes that contradict their declared
  type: a `%PDF-` body declared as anything else, or a declared PDF without that
  signature (PT-4). `cohort register` and `cohort terms --saved` share it.
- **Terms saved by hand (PT-9).** `cohort terms URL --saved FILE [--media-type TYPE]`
  hashes a terms page the user saved in a browser, by the register's own rule
  (P6-15). It sends no request and needs no identity, and the user still reads the
  page before its hash enters the register.
- **Tests** build invented PDFs at test time, and the committed synthetic cohort does
  not change (PT-6).

## Requirement map

The roadmap's Stage 4 Exit line, clause by clause:

| Exit clause | What shows it | Task |
| --- | --- | --- |
| Every membership interval resolves to a source-evidence row, and every resolved CIK is a 10-character zero-padded string (P-A4) | `test_every_interval_rests_on_supported_evidence`; `test_every_resolved_cik_is_ten_digits_and_one_issuer_per_cik`; `test_a_cik_is_ten_zero_padded_digits`; the `Cik` type on every record | 13; 4; 6 |
| Fixture tests build intervals from an anchor plus additions and removals, with inclusive starts, exclusive ends, and an open interval carrying no `effective_to` (P-VF) | `test_anchor_additions_and_removals_make_half_open_intervals`; `test_intervals_are_half_open` | 9; 6 |
| A missing anchor refuses the freeze with the reason recorded | `test_a_missing_anchor_refuses_the_freeze_with_its_reason`; `test_without_an_anchor_only_announced_intervals_exist` | 12; 9 |
| Conflicting effective dates persist as separate assertions and hold the freeze until a recorded review resolves them | `test_conflicting_dates_stay_separate_and_hold_until_one_is_rejected`; `test_before_review_its_findings_hold_the_freeze`; the synthetic `reject-preliminary-date` override | 9; 12; 13 |
| The coverage and conflict report lists every interval conflict and coverage gap (P-A4) | `test_every_break_in_the_sequence_is_a_conflict`; `test_every_uncorroborated_quarter_is_a_gap`; the frozen synthetic report | 9; 11; 13 |
| Evidence first published after 2026-09-22 cannot revise the version (P-C4) | `test_evidence_published_after_the_cutoff_is_withheld`; `test_evidence_published_on_the_cutoff_applies`; `test_a_row_published_after_the_cutoff_never_changes_an_identity`; `test_an_amendment_supersedes_and_a_late_filing_is_kept_apart`; the synthetic `index-2026-09-25` notice | 9; 12; 11; 13 |
| No current snapshot is silently backdated, and no ETF holdings record is treated as the official roster | `test_a_later_snapshot_is_never_backdated_into_the_anchor`; `test_fund_holdings_are_never_the_roster` | 12 |
| Historical ticker changes and multiple securities are preserved, and one issuer's several securities derive one issuer row (P-VF) | `test_a_ticker_change_keeps_both_identities_and_resolves_once`; `test_two_securities_of_one_issuer_derive_one_issuer_row`; the synthetic `acme-common` and `dynamo-class-a`/`-b` | 10; 13 |
| Source access and redistribution status are recorded for every source, and unclear rights keep artifacts local | `test_the_manifest_records_rights_for_every_source_it_cites`; `test_an_entry_gives_the_sources_class_roles_and_rights`; `test_saved_evidence_stays_local_and_the_fixture_is_committed`; `SEC_RIGHTS` is `local_only` | 12; 7; 13 |
| The manifest freezes with a version and content hash, written atomically | `test_identical_content_keeps_its_version`; `test_changed_evidence_is_a_new_version_beside_the_old`; `test_a_tampered_manifest_is_refused`; `test_a_written_file_is_never_replaced` | 12; 1 |
| The freeze refuses unresolved issuer identity unless it is retained as unresolved and excluded with its reason | `test_a_name_that_is_not_covered_leaves_it_unresolved_and_blocking`; `test_overrides_decide_and_resolve_the_finding`; `test_a_retained_unresolved_security_is_excluded_and_the_freeze_proceeds` | 10; 12 |
| The default suite makes no network call, uses no proprietary roster, and needs no credentials | `test_saved_evidence_replays_to_the_frozen_manifest`, under a socket guard; `test_the_offline_cohort_path_loads_no_network_client`; the synthetic cohort | 13; 12 |
| The `live` verification runs only when opted in and records its result with retrieval metadata (P-VL) | `tests/integration/test_cohort_live.py`, marked `live`; `test_changes_and_refusals_are_recorded_not_hidden`; the real run's record | 15; 18 |
| Concurrent workers send through the shared SEC client at or below 2 req/s, and a persistent 403 stops without rotating identity (R1.3, D5) | `test_concurrent_workers_stay_at_or_below_two_requests_per_second`; `test_a_persistent_403_stops_without_rotating_identity`; `test_one_client_per_machine`; `test_concurrent_workers_share_one_allowance` | 4; 2 |

The Gap closed line's decisions, which the Exit clauses above test in part:

| Decision | What shows it | Task |
| --- | --- | --- |
| P-C1: the DJIA is resolved point in time, never as one current roster | Intervals rebuilt from a dated anchor and dated changes; `test_anchor_additions_and_removals_make_half_open_intervals`; `test_a_later_snapshot_is_never_backdated_into_the_anchor` | 9; 12 |
| P-C2, the membership reference only: membership is judged at `first_publication_time` | `UniverseDefinition.membership_reference`, which admits only that value; `MembershipInterval.contains` and `overlaps` for Stage 5's join | 6 |
| P-C3: the window is `[2024-07-01, 2026-07-01)` | `UniverseDefinition.period_end_start` and `period_end_stop`; `test_the_cutoff_cannot_fall_inside_the_window`; `test_the_candidate_issuers_are_the_in_scope_securities_issuers` | 6; 13 |
| P-C7, its cohort-before-acquisition half | The build reads membership and identity evidence only, never an earnings document; `test_the_offline_cohort_path_loads_no_network_client`; Task 17 freezes the cohort before Stage 5 exists | 12; 17 |

The Produces line's other items:

| Produces | Where | Task |
| --- | --- | --- |
| The universe definition at P's grain | `UniverseDefinition`; `universe.toml` | 6; 17 |
| Security-level membership assertions with `status` | `MembershipAssertion`, built by `build` | 6; 12 |
| Security-to-issuer mappings with 10-character CIK evidence | `IssuerMapping` and its `IssuerCandidate` citations | 6; 10 |
| The candidate issuers over intervals overlapping `2024-07-01` through the cutoff | `candidate_issuer_ids` (P6-13); `test_the_candidate_issuers_are_the_in_scope_securities_issuers` | 12; 13 |
| The membership source register | `cohort/register.py`; `docs/membership-source-register.toml` | 7; 17 |
| The coverage and conflict report | `CohortReport` and its findings | 6, 9, 11, 12 |
| Synthetic redistributable fixtures | `cohort/synthetic.py`; `tests/fixtures/cohort/` | 12; 13 |
| Version-controlled override assertions with evidence, rationale, reviewer, and effective dates | `Override`; `overrides.toml` | 6; 17 |
| The opt-in `live` verification (P-VL) | `cohort/live.py`; `earnings-pipeline cohort verify-live` | 15, 16; 18 |
| The shared SEC client (R1.3, D5) | `fetch/client.py`, `sec/client.py` | 2, 4 |

The Consumes line's constraints:

| Constraint | Where | Task |
| --- | --- | --- |
| Retrieval metadata defined at ingestion's grain | `Retrieval` (P6-5) | 1 |
| `sec-edgar`'s `access_method` names the shared client | `docs/source-register.toml`, then `fetch_policy_pages.py verify` | 4 |
| The README records the second register | `README.md` | 18 |
| `pf_fetch.py` ported, never imported | `fetch/client.py`; `tests/contracts/test_import_scan.py` already refuses package imports of `expirements/` | 2 |
| No parser, canonicalizer, document, or model artifact | `walker-1` (HTML) and `pdftext-1` (PDF) produce citation text only (PT-8) | 8, 16b |

## Human gates

| Gate | When | Who | What it unblocks |
| --- | --- | --- | --- |
| The format probe | Task 5, Step 7 | user | At most eight SEC requests through the shared client (P6-21). If the user declines, skip the step and note it: Task 17's `fetch-sec` then meets SEC's formats first. |
| The PDF dependency | Task 16b, Step 3 | user | `uv add --package earnings-ingestion "pypdf==6.19.0"` reaches PyPI and changes `uv.lock`. The wheel is already in uv's cache from the spike. If the user declines, stop: Task 17 cannot cite the PDF notices. |
| The real sources | Task 17, Step 1 | user | The four register entries, the Wikipedia revision (its ID and timestamp), and the list of S&P DJI announcements from the anchor's date through the cutoff |
| Live acquisition | Task 17, Steps 3, 4, and 7 | user | The terms pages (four), the evidence pages (about four, each after its host's robots.txt), and `fetch-sec` (about 50 to 60 SEC requests). Ask before each group of commands, naming the requests. |
| Hand-saving | Task 17, whenever a fetch is refused | user | The user saves the refused page in a browser, and `cohort register` records it. A refused terms page is saved the same way, and `cohort terms --saved` hashes it (PT-9). |
| The review | Task 17, Steps 9–11 | user | The decision for each blocking finding, each override's rationale, and the signature |
| The freeze | Task 17, Step 12 | user | The real cohort's freeze, once the user approves the build's report |
| Live verification | Task 18, Step 1 | user | `cohort verify-live`: the terms pages, each evidence URL, and each host's robots.txt, about ten requests |

In subagent-driven execution, every gate runs in the controller session with the
user, never in a subagent. Each is a hard stop: nothing after it starts until the
user has answered. A subagent that reaches a gate stops and reports back instead.

## File map

`…/fetch/`, `…/sec/`, and `…/cohort/` below are under
`packages/earnings-ingestion/src/earnings_ingestion/`, and `…/tests/` is
`packages/earnings-ingestion/tests/`.

| Path | Responsibility | Task |
| --- | --- | --- |
| `…/fetch/__init__.py`, `records.py`, `store.py`; `…/tests/test_fetch_store.py` | Retrieval metadata; the content-addressed store; `write_new` | 1 |
| `docs/data-dictionary.md`, `tests/contracts/test_data_dictionary.py` | The retrieval records (Task 1); the cohort records (Task 6); the curated files (Task 7); the frozen manifests (Task 12); `pdftext-1` beside `walker-1` (Task 16b) | 1, 6, 7, 12, 16b |
| `…/fetch/client.py`; `…/tests/test_fetch_client.py` | The polite client, ported from `pf_fetch.py` | 2 |
| `…/fetch/robots.py`; `…/tests/test_fetch_robots.py` | The robots.txt gate | 3 |
| `…/sec/__init__.py`, `identifiers.py`, `urls.py`, `client.py`; `…/tests/test_sec_client.py` | CIKs; SEC URLs; the shared SEC client | 4 |
| `…/tests/test_import_boundaries.py` | The runtime import checks: the clients (Task 4), the offline path (Task 12), the web client (Task 14), `pdftext-1` (Task 16b) | 4, 12, 14, 16b |
| `docs/source-register.toml` | `sec-edgar`'s access method and coverage | 4 |
| `…/sec/data.py`; `…/tests/test_sec_data.py` | SEC's record readers | 5 |
| `tests/integration/test_sec_formats_live.py` | The live format probe | 5 |
| `…/cohort/__init__.py`, `records.py`, `digests.py`; `…/tests/test_cohort_records.py`, `test_cohort_digests.py` | The cohort records; canonical JSON | 6 |
| `…/cohort/register.py`, `config.py`; `…/tests/test_cohort_register.py`, `test_cohort_config.py` | The membership register; the curated files | 7 |
| `…/cohort/locators.py`, `names.py`; `…/tests/test_cohort_locators.py`, `test_cohort_names.py` | Citations; token cover | 8 |
| `…/cohort/findings.py`, `intervals.py`; `…/tests/test_cohort_findings.py`, `test_cohort_intervals.py` | Findings; reconstruction | 9 |
| `…/cohort/resolution.py`; `…/tests/test_cohort_resolution.py` | Issuer resolution | 10 |
| `…/cohort/corroboration.py`; `…/tests/test_cohort_corroboration.py` | Corroboration | 11 |
| `…/cohort/build.py`, `freeze.py`, `synthetic.py`; `…/tests/conftest.py`, `test_cohort_build.py` | The build; the freeze; the synthetic cohort | 12 |
| `tests/integration/regenerate_cohort_fixtures.py`, `test_cohort_fixtures.py`; `tests/fixtures/cohort/` (generated); `.gitattributes` (one line appended) | The committed synthetic cohort and its offline replay | 13 |
| `…/cohort/web.py`, `acquire.py`; `…/tests/test_cohort_web.py`, `test_cohort_acquire.py` | The web client; acquisition and citing | 14 |
| `…/cohort/live.py`; `…/tests/test_cohort_live.py`; `tests/integration/test_cohort_live.py` | The live verification | 15 |
| `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`, `cli.py`; `apps/earnings-pipeline/tests/test_cohort_cli.py` | The `cohort` commands | 16 |
| `…/cohort/pdftext.py`; `…/tests/test_cohort_pdftext.py` | PDF citation text, `pdftext-1` (P6-24) | 16b |
| `…/cohort/locators.py`, `build.py`, `acquire.py`, `live.py`; `…/fetch/store.py`; `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`; `…/tests/conftest.py`, `test_cohort_locators.py`, `test_cohort_build.py`, `test_fetch_store.py`, `test_cohort_acquire.py`, `test_cohort_live.py`; `apps/earnings-pipeline/tests/test_cohort_cli.py` | Citing a PDF; refusing a contradicting media type; `cohort terms --saved` (PT-9) | 16b |
| `packages/earnings-ingestion/pyproject.toml`, `uv.lock` | `pypdf==6.19.0`, by the gated `uv add` | 16b |
| `docs/membership-source-register.toml`; `config/universe/djia/universe.toml`, `evidence.toml`, `overrides.toml`; `config/universe/djia/manifests/` (generated) | The real cohort | 17 |
| `docs/verification/djia-cohort.md`; `CLAUDE.md`; `README.md` | The verification record; the current state | 18 |

No other file changes.

## Preconditions — read before Task 1

- **Branch.** Work on `stage-4-point-in-time-djia-cohort` in the main checkout. At
  planning time its commits above `main` (`b7af585`) were the roadmap reconcile
  (`f78e1e8`), the cohort spec's header fix (`5b50b22`), and this plan's commit, and
  the branch was unpushed. Run this and read the result:

  ```bash
  git switch stage-4-point-in-time-djia-cohort && git log --oneline -3 && git status --short
  ```

  Expected: the head is `docs(plan): plan 6, Stage 4: the point-in-time DJIA cohort`,
  or a later commit the user made, and the status is empty.
- **Stay in the main checkout.** Do not execute in a separate worktree. `data/` is
  gitignored, so a worktree lacks what these need:
  - Task 4's register check needs the saved policy pages in `data/raw/register/`;
  - the harness suite needs the development releases in `data/raw/devset/`, and
    the user's rendered copies in `data/runs/parser-fidelity/gold-drafts/`;
  - Task 17 saves the real cohort's evidence under `data/raw/cohort/`.
- **Environment.** Run `uv sync --locked --all-packages`; the `dev` group syncs by
  default.
  - `uv --version` must print uv 0.12.15.
  - The interpreter is Python 3.14.0, pinned by `.python-version`.
- **Helpers.** Save the two helpers from Global Constraints, then check both:

  ```bash
  python3 /tmp/plan6-extract.py docs/no-such-file.md; python3 /tmp/plan6-escapes.py specs/plans/6-point-in-time-djia-cohort.md
  ```

  Expected: `specs/plans/6-point-in-time-djia-cohort.md has no block 1 for docs/no-such-file.md`,
  then the plan's own path. The plan holds non-ASCII characters, so this shows that
  the check works.
- **Baselines:**

  ```bash
  uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
  uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
  uv run --locked ruff check . && uv run --locked ruff format --check .
  uv run --locked --all-packages python expirements/parser-fidelity/fetch_policy_pages.py verify
  ```

  Expected: `644 passed, 22 deselected`; `280 passed`; `All checks passed!` and
  `157 files already formatted`; `register quotes verified`.

  If the harness reports 278 passed and 2 skipped, the rendered copies are missing:
  stop and ask.
- **Local data.** `ls data/raw/register/` lists `access.html` and `reuse.html` with
  their `.meta.json` files. If they are missing, stop and ask: Task 4's register
  check reads them.
- **Identities.** Check them without printing them:

  ```bash
  for v in EDGAR_IDENTITY SOURCE_IDENTITY; do [ -n "$(printenv $v)" ] && echo "$v set" || echo "$v unset"; done
  ```

  Only the gates need them. If `EDGAR_IDENTITY` is set, remember that a `-m live`
  run really reaches SEC (Global Constraints).

---
### Task 1: Retrieval records and the artifact store

Stage 2 left retrieval metadata to this stage (plan 3, "Handoffs to Stage 4"), and
this task records it at ingestion's grain (P6-5).

- **`Retrieval`** records one retrieval of one artifact: the request URL, the final
  URL, the UTC time, the method, and the bytes' media type, length, and SHA-256.
  - A page a person saved is `saved_by_user` and has no HTTP status.
  - The identity sent as the User-Agent is never recorded.
- **The store** keeps each artifact's bytes once, named by their SHA-256, beside a
  record of every retrieval. It never replaces a file: `write_new` links a temporary
  file into place, so writing the same bytes again is a no-op, and different bytes
  raise.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/fetch/__init__.py`
  (empty), `fetch/records.py`, and `fetch/store.py`.
- Modify: `docs/data-dictionary.md` (appended, part 1 of 4), and
  `tests/contracts/test_data_dictionary.py` (replaced whole, block 1 of 3).
- Test (create): `packages/earnings-ingestion/tests/test_fetch_store.py`.

**Interfaces:**

- Consumes:
  - from `earnings_core`: `ArtifactRef.for_bytes`, `RightsStatus`, `sha256_hex`,
    `MediaType`, `NonBlankStr`, and `Sha256Hex`;
  - `earnings_ingestion.canonical.records.IngestionRecord`, at schema version 1.
- Produces:
  - `fetch/records.py`:
    - `SOURCE_ID_PATTERN` and `SourceId`, a lowercase slug;
    - `RetrievalMethod`, with `HTTP` and `SAVED_BY_USER`;
    - `Retrieval(IngestionRecord)`, with fields `request_url`, `final_url`,
      `retrieved_at` (UTC), `retrieval_method`, `http_status` (set exactly for
      HTTP), `media_type`, `content_type`, `byte_count`, and `sha256`.
  - `fetch/store.py`:
    - `ArtifactStore(root: Path, repo: Path)`, with these methods:
      - `put(source_id, body, retrieval, *, rights_status, rights_basis) -> ArtifactRef`;
      - `retrievals(source_id, sha256) -> tuple[Retrieval, ...]`, oldest first;
      - `get(source_id, sha256, *, rights_status, rights_basis) -> StoredArtifact`,
        which raises `FileNotFoundError` or `ValueError`;
      - `latest(source_id, url, *, rights_status, rights_basis) -> StoredArtifact | None`.
    - `StoredArtifact(ref, body, retrievals)`;
    - `write_new(path: Path, data: bytes) -> None`.

  Artifacts are stored at `<root>/<source_id>/<sha256><ext>`, and retrieval records
  at `<root>/<source_id>/retrievals/<sha256>/<stamp>-<12 hex>.json`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_fetch_store.py`:

```python
"""Saved artifacts: content-addressed, never overwritten, every retrieval kept in a
checked retrieval record."""

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore, write_new
from pydantic import ValidationError

BODY = b"<p>An announcement.</p>"
WHEN = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
RIGHTS = {"rights_status": RightsStatus.LOCAL_ONLY, "rights_basis": "unclear terms"}


def retrieval(body: bytes = BODY, when: datetime = WHEN) -> Retrieval:
    return Retrieval(
        request_url="https://press.example.org/a",
        final_url="https://press.example.org/a",
        retrieved_at=when,
        retrieval_method=RetrievalMethod.HTTP,
        http_status=200,
        media_type="text/html",
        content_type="text/html; charset=utf-8",
        byte_count=len(body),
        sha256=sha256_hex(body),
    )


def store_in(tmp_path: Path) -> ArtifactStore:
    return ArtifactStore(tmp_path / "data" / "raw" / "cohort", tmp_path)


def test_an_artifact_is_stored_by_hash_with_a_portable_reference(tmp_path) -> None:
    store = store_in(tmp_path)
    ref = store.put("press", BODY, retrieval(), **RIGHTS)
    digest = sha256_hex(BODY)
    assert ref.storage_ref == f"data/raw/cohort/press/{digest}.html"
    assert ref.rights_status is RightsStatus.LOCAL_ONLY
    stored = store.get("press", digest, **RIGHTS)
    assert stored.body == BODY
    assert stored.ref == ref
    assert stored.retrievals == (retrieval(),)


def test_each_retrieval_is_kept_and_the_bytes_once(tmp_path) -> None:
    store = store_in(tmp_path)
    later = WHEN + timedelta(days=1)
    store.put("press", BODY, retrieval(when=later), **RIGHTS)
    store.put("press", BODY, retrieval(), **RIGHTS)
    stored = store.get("press", sha256_hex(BODY), **RIGHTS)
    assert [r.retrieved_at for r in stored.retrievals] == [WHEN, later]
    assert (
        len(list((tmp_path / "data" / "raw" / "cohort" / "press").glob("*.html"))) == 1
    )


def test_a_record_for_other_bytes_is_refused(tmp_path) -> None:
    with pytest.raises(ValueError, match="other bytes"):
        store_in(tmp_path).put("press", b"other", retrieval(), **RIGHTS)


def test_changed_bytes_on_disk_are_detected(tmp_path) -> None:
    store = store_in(tmp_path)
    ref = store.put("press", BODY, retrieval(), **RIGHTS)
    (tmp_path / ref.storage_ref).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="no longer hashes"):
        store.get("press", sha256_hex(BODY), **RIGHTS)


def test_a_missing_artifact_is_reported_not_empty(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        store_in(tmp_path).get("press", sha256_hex(b"absent"), **RIGHTS)


@pytest.mark.parametrize("source_id", ["../escape", "Press", "", "a/b"])
def test_a_source_id_must_be_a_slug(tmp_path, source_id) -> None:
    with pytest.raises(ValueError, match="slug"):
        store_in(tmp_path).put(source_id, BODY, retrieval(), **RIGHTS)


def test_the_latest_retrieval_of_a_url_names_its_artifact(tmp_path) -> None:
    store = store_in(tmp_path)
    newer = b"<p>A corrected announcement.</p>"
    store.put("press", BODY, retrieval(), **RIGHTS)
    store.put("press", newer, retrieval(newer, WHEN + timedelta(hours=1)), **RIGHTS)
    latest = store.latest("press", "https://press.example.org/a", **RIGHTS)
    assert latest.body == newer
    assert store.latest("press", "https://press.example.org/b", **RIGHTS) is None
    assert store.latest("other", "https://press.example.org/a", **RIGHTS) is None


def test_a_written_file_is_never_replaced(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    write_new(path, b"first")
    write_new(path, b"first")
    with pytest.raises(FileExistsError, match="holds other bytes"):
        write_new(path, b"second")
    assert path.read_bytes() == b"first"
    assert [p.name for p in tmp_path.iterdir()] == ["manifest.json"]


def test_a_retrieval_is_utc_and_records_status_only_for_http() -> None:
    fields = {
        "request_url": "https://www.example.gov/x",
        "final_url": "https://www.example.gov/x",
        "retrieved_at": WHEN,
        "retrieval_method": RetrievalMethod.HTTP,
        "http_status": 200,
        "media_type": "text/html",
        "content_type": "text/html",
        "byte_count": 1,
        "sha256": sha256_hex(b"x"),
    }
    Retrieval(**fields)
    with pytest.raises(ValidationError, match="UTC"):
        Retrieval(
            **fields | {"retrieved_at": WHEN.astimezone(timezone(timedelta(hours=-4)))}
        )
    with pytest.raises(ValidationError, match="http_status"):
        Retrieval(**fields | {"retrieval_method": RetrievalMethod.SAVED_BY_USER})
```

Replace `tests/contracts/test_data_dictionary.py` with:

```python
"""docs/data-dictionary.md documents every field and value of the core contracts
and of the ingestion records: the canonicalizer's, the capture's, layout-1's, and the
retrieval metadata.

AGENTS.md §191: document public interfaces and update the data dictionary in the
same change. A contract that gains, loses, or renames a field fails here.
"""

import re
from enum import StrEnum
from pathlib import Path

import earnings_core as core
import earnings_ingestion.canonical as ingestion
import pytest
from earnings_ingestion import browser, layout
from earnings_ingestion.fetch import records as fetch
from pydantic import BaseModel

DICTIONARY = Path(__file__).resolve().parents[2] / "docs" / "data-dictionary.md"
MODELS = [
    core.TextSpan,
    core.ArtifactRef,
    core.CanonicalDocument,
    core.TableCellContext,
    core.DocumentElement,
    core.SpanLocator,
    core.TextChunk,
    core.SpanCandidate,
    core.VerifiedSpan,
    core.OverlayMask,
    core.MaskedDocument,
    core.Rejection,
    ingestion.CanonicalizationManifest,
    ingestion.CanonicalizationFailure,
    ingestion.Canonicalized,
    browser.RenderedCapture,
    browser.BlockedRequest,
    browser.LayoutMetadata,
    browser.LayoutBlock,
    browser.LayoutRun,
    browser.LayoutTable,
    browser.LayoutRow,
    browser.LayoutCell,
    layout.AlignmentFailure,
    layout.LayoutExtraction,
    fetch.Retrieval,
]
ENUMS = [
    core.RightsStatus,
    core.ElementType,
    core.TextOrigin,
    core.MaskCategory,
    core.RejectionReason,
    ingestion.FailureReason,
    browser.CaptureStatus,
    browser.CaptureReason,
    fetch.RetrievalMethod,
]


def documented(name: str) -> set[str]:
    """The first-column code spans of the table under the heading for ``name``."""
    text = DICTIONARY.read_text(encoding="utf-8")
    heading = f"### `{name}`\n"
    assert heading in text, f"docs/data-dictionary.md has no section for {name}"
    section = text.split(heading, 1)[1].split("\n#", 1)[0]
    return set(re.findall(r"^\| `([^`]+)` \|", section, flags=re.MULTILINE))


@pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__name__)
def test_every_field_is_documented(model: type[BaseModel]) -> None:
    assert documented(model.__name__) == set(model.model_fields)


@pytest.mark.parametrize("enum", ENUMS, ids=lambda enum: enum.__name__)
def test_every_value_is_documented(enum: type[StrEnum]) -> None:
    assert documented(enum.__name__) == {member.value for member in enum}


def test_the_documented_versions_are_the_packages() -> None:
    text = DICTIONARY.read_text(encoding="utf-8")
    assert f"schema version {core.SCHEMA_VERSION}\n" in text
    assert f'`"{core.VALIDATOR_VERSION}"` (`earnings_core.VALIDATOR_VERSION`)' in text
    assert (
        f"## earnings-ingestion records, schema version"
        f" {ingestion.INGESTION_SCHEMA_VERSION}\n" in text
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_store.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL. Collection stops in both files with
`No module named 'earnings_ingestion.fetch'`, and pytest reports `2 errors`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/fetch/__init__.py`:

```python
```

Create `packages/earnings-ingestion/src/earnings_ingestion/fetch/records.py`:

```python
"""Retrieval metadata for one saved source artifact (Stage 4).

Stage 2 left retrieval metadata to Stage 4 (plan 3, Handoffs to Stage 4): core records
no source URL, retrieval time, or request. ``Retrieval`` is ingestion's record of one
retrieval of one artifact. The identity sent as the User-Agent is never recorded.
docs/data-dictionary.md documents every field.
"""

from datetime import timedelta
from enum import StrEnum
from typing import Annotated, Self

from earnings_core.artifacts import MediaType, NonBlankStr
from earnings_core.hashing import Sha256Hex
from pydantic import AwareDatetime, NonNegativeInt, StringConstraints, model_validator

from earnings_ingestion.canonical.records import IngestionRecord

SOURCE_ID_PATTERN = r"^[a-z0-9][a-z0-9-]*$"
SourceId = Annotated[str, StringConstraints(pattern=SOURCE_ID_PATTERN)]
"""A source register key: a lowercase slug, safe as a directory name."""


class RetrievalMethod(StrEnum):
    """How an artifact's bytes reached the store."""

    HTTP = "http"
    """Fetched by this package's client, under its access policy."""
    SAVED_BY_USER = "saved_by_user"
    """Saved by a person in a browser and registered by hash; nothing was fetched."""


class Retrieval(IngestionRecord):
    """One retrieval: where the bytes came from, when, and what they hash to."""

    request_url: NonBlankStr
    final_url: NonBlankStr
    retrieved_at: AwareDatetime
    retrieval_method: RetrievalMethod
    http_status: int | None
    media_type: MediaType
    content_type: str
    byte_count: NonNegativeInt
    sha256: Sha256Hex

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.retrieved_at.utcoffset() != timedelta(0):
            raise ValueError("retrieved_at must be in UTC")
        if (self.retrieval_method is RetrievalMethod.HTTP) != (
            self.http_status is not None
        ):
            raise ValueError("http_status is recorded exactly for an HTTP retrieval")
        return self
```

Create `packages/earnings-ingestion/src/earnings_ingestion/fetch/store.py`:

```python
"""Saved source artifacts under ``data/raw/``: content-addressed, never overwritten.

Each source has a directory, named by its register ``source_id``. An artifact's bytes
are stored once, named by their SHA-256, with one ``Retrieval`` record for each time
they were fetched or registered, named by its time and its own hash. Every write goes to a temporary file and is
hard-linked into place, which fails rather than replace an existing file: writing the
same bytes again is a no-op, and different bytes raise ``FileExistsError`` (the capture
store's rule, plan 5). Reprocessing reads these files and never fetches (A §410).
"""

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from earnings_core import ArtifactRef, RightsStatus, sha256_hex

from earnings_ingestion.fetch.records import SOURCE_ID_PATTERN, Retrieval

EXTENSIONS = {
    "application/json": ".json",
    "application/xml": ".xml",
    "text/html": ".html",
    "text/plain": ".txt",
    "text/xml": ".xml",
}
_SOURCE_ID = re.compile(SOURCE_ID_PATTERN)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class StoredArtifact:
    """An artifact's bytes, its reference, and every retrieval of it, oldest first."""

    ref: ArtifactRef
    body: bytes
    retrievals: tuple[Retrieval, ...]


class ArtifactStore:
    """``root`` lies under ``repo``'s ``data/raw/``; references are repo-relative."""

    def __init__(self, root: Path, repo: Path) -> None:
        self.root = root
        self.repo = repo

    def put(
        self,
        source_id: str,
        body: bytes,
        retrieval: Retrieval,
        *,
        rights_status: RightsStatus,
        rights_basis: str,
    ) -> ArtifactRef:
        """Store ``body`` and its retrieval record; return the artifact's reference."""
        if retrieval.sha256 != sha256_hex(body) or retrieval.byte_count != len(body):
            raise ValueError("the retrieval record describes other bytes")
        path = self._artifact_path(source_id, retrieval.sha256, retrieval.media_type)
        write_new(path, body)
        data = retrieval.model_dump_json().encode("utf-8")
        stamp = retrieval.retrieved_at.strftime("%Y%m%dT%H%M%S%fZ")
        name = f"{stamp}-{sha256_hex(data)[:12]}.json"
        write_new(self._retrieval_dir(source_id, retrieval.sha256) / name, data)
        return self._ref(path, body, retrieval, rights_status, rights_basis)

    def retrievals(self, source_id: str, sha256: str) -> tuple[Retrieval, ...]:
        """Every retrieval of the artifact, oldest first; empty if none is stored."""
        folder = self._retrieval_dir(source_id, sha256)
        if not folder.is_dir():
            return ()
        records = [
            Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            for path in folder.glob("*.json")
        ]
        return tuple(sorted(records, key=lambda record: record.retrieved_at))

    def get(
        self,
        source_id: str,
        sha256: str,
        *,
        rights_status: RightsStatus,
        rights_basis: str,
    ) -> StoredArtifact:
        """The stored artifact; ``FileNotFoundError`` if absent, ``ValueError`` if its
        bytes no longer hash to its name."""
        retrievals = self.retrievals(source_id, sha256)
        if not retrievals:
            raise FileNotFoundError(
                f"no artifact {sha256} for source {source_id!r} under {self.root}"
            )
        path = self._artifact_path(source_id, sha256, retrievals[0].media_type)
        if not path.is_file():
            raise FileNotFoundError(
                f"no artifact {sha256} for source {source_id!r}: its retrieval records"
                " remain, but its bytes are gone"
            )
        body = path.read_bytes()
        if sha256_hex(body) != sha256:
            raise ValueError(f"{path} no longer hashes to its name")
        ref = self._ref(path, body, retrievals[0], rights_status, rights_basis)
        return StoredArtifact(ref=ref, body=body, retrievals=retrievals)

    def latest(
        self,
        source_id: str,
        url: str,
        *,
        rights_status: RightsStatus,
        rights_basis: str,
    ) -> StoredArtifact | None:
        """The artifact most recently retrieved from ``url``, or ``None``."""
        self._check(source_id, "0" * 64)
        folder = self.root / source_id / "retrievals"
        records = [
            Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(folder.glob("*/*.json"))
        ]
        matching = [record for record in records if record.request_url == url]
        if not matching:
            return None
        newest = max(matching, key=lambda record: (record.retrieved_at, record.sha256))
        return self.get(
            source_id,
            newest.sha256,
            rights_status=rights_status,
            rights_basis=rights_basis,
        )

    def _ref(
        self,
        path: Path,
        body: bytes,
        retrieval: Retrieval,
        rights_status: RightsStatus,
        rights_basis: str,
    ) -> ArtifactRef:
        return ArtifactRef.for_bytes(
            body,
            media_type=retrieval.media_type,
            storage_ref=path.relative_to(self.repo).as_posix(),
            rights_status=rights_status,
            rights_basis=rights_basis,
        )

    def _artifact_path(self, source_id: str, sha256: str, media_type: str) -> Path:
        self._check(source_id, sha256)
        return self.root / source_id / f"{sha256}{EXTENSIONS.get(media_type, '.bin')}"

    def _retrieval_dir(self, source_id: str, sha256: str) -> Path:
        self._check(source_id, sha256)
        return self.root / source_id / "retrievals" / sha256

    @staticmethod
    def _check(source_id: str, sha256: str) -> None:
        if not _SOURCE_ID.match(source_id):
            raise ValueError(f"source_id {source_id!r} is not a register slug")
        if not _SHA256.match(sha256):
            raise ValueError(f"{sha256!r} is not a SHA-256 digest")


def write_new(path: Path, data: bytes) -> None:
    """Write ``data`` to a new file at ``path``, atomically; the same bytes again are
    a no-op, and other bytes raise ``FileExistsError``."""
    if path.exists():
        if path.read_bytes() == data:
            return
        raise FileExistsError(f"{path} holds other bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
```

- [ ] **Step 4: Run the store's tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_store.py -q`

Expected: `12 passed`.

- [ ] **Step 5: Document the records**

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: FAIL: `2 failed, 34 passed`. The dictionary has no section for
`Retrieval` or `RetrievalMethod`.

Append to `docs/data-dictionary.md`:

```markdown

## earnings-ingestion retrieval records, schema version 1

- **Package.** `earnings_ingestion.fetch`, in `packages/earnings-ingestion` (Stage 4,
  plan 6): retrieval metadata and the artifact store.
- **Schema version.** `Retrieval` joins ingestion schema version `1`, since no
  earlier record's fields changed, and carries it as `schema_version`.
- **Saved artifacts.** An `ArtifactStore` rooted at a directory under `data/raw/`
  stores an artifact as `<root>/<source_id>/<sha256><ext>`. Each retrieval of it gets
  a record at
  `<root>/<source_id>/retrievals/<sha256>/<UTC stamp>-<first 12 hex of the record's hash>.json`.
  `data/raw/` is never committed.

### `Retrieval`

One retrieval of one saved artifact. The identity sent as the User-Agent is never
recorded.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `request_url` | string | The URL requested; for a page a person saved, the URL it was saved from |
| `final_url` | string | The URL after any redirects |
| `retrieved_at` | UTC datetime | When the bytes arrived, or when a person saved them |
| `retrieval_method` | `RetrievalMethod` | How the bytes reached the store |
| `http_status` | int or null | The response's status; null exactly when a person saved the page |
| `media_type` | media type | The Content-Type's lowercase media type, without parameters |
| `content_type` | string | The Content-Type header as received |
| `byte_count` | int ≥ 0 | The body's length, after any Content-Encoding is decoded |
| `sha256` | 64 lowercase hex | SHA-256 of the body |

### `RetrievalMethod`

| Value | Meaning |
| --- | --- |
| `http` | Fetched by a package client, under its access policy |
| `saved_by_user` | Saved by a person in a browser and registered by hash; nothing was fetched |
```

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: `36 passed`.

- [ ] **Step 6: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/fetch/*.py packages/earnings-ingestion/tests/test_fetch_store.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `658 passed, 22 deselected`;
`All checks passed!` and `161 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/fetch packages/earnings-ingestion/tests/test_fetch_store.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(ingestion): record retrievals and store source artifacts by hash"
```

---
### Task 2: The polite client, ported from `pf_fetch.py`

D5 makes Stage 1's live-fetch client the reference design for the shared SEC client:
port it, never import it. `PoliteClient` carries the access policy of A §393–408,
and each source's client configures it.

- **What it enforces.**
  - One identity, sent as the User-Agent and never recorded.
  - One throttle, which spaces every request start, redirect hops included.
  - Explicit timeouts and bounded retries with backoff and jitter.
  - `Retry-After` is honoured.
  - A 403 that persists stops the run.
- **What changed from `pf_fetch.py`.**
  - The throttle is thread-safe, so workers share one client and one allowance.
  - A host filter refuses any request outside the client's hosts, redirect hops
    included.
  - A block page stops the run even where JSON was expected.
  - `fetch` returns the bytes and a `Retrieval` and writes nothing.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py`.
- Test (create): `packages/earnings-ingestion/tests/test_fetch_client.py`.

**Interfaces:**

- Consumes: Task 1's `Retrieval` and `RetrievalMethod`, and `earnings_core.sha256_hex`.
- Produces, in `fetch/client.py`:
  - `AccessStop(RuntimeError)`, which means the run must stop and be reported, and
    `UnexpectedResponse(RuntimeError)`, a response the caller may skip;
  - `require_identity(variable: str, environ: Mapping[str, str] | None = None) -> str`;
  - `retry_after_seconds(value: str | None, now: datetime) -> float | None`;
  - `Throttle(*, min_interval, max_requests=DEFAULT_MAX_REQUESTS, clock=time.monotonic, sleep=time.sleep)`,
    with `acquire()` and the `count` property;
  - `ProcessLock(path)`, a non-blocking `flock` used as a context manager;
  - `Fetched(body: bytes, retrieval: Retrieval)`;
  - `PoliteClient(identity, *, throttle, host_allowed=..., block_markers=(), transport=None, sleep=time.sleep, rng=None, now=...)`.
    It has `get(url) -> httpx.Response`,
    `fetch(url, expected_types) -> Fetched`, `close()`, the context-manager
    protocol, and the attribute `throttle`;
  - the constants `DEFAULT_MAX_REQUESTS = 500`, `MAX_ATTEMPTS = 4`, and
    `FORBIDDEN_LIMIT = 2`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_fetch_client.py`:

```python
"""The polite client: the access policy of A §393-408, ported from pf_fetch (D5)."""

import gzip
import random
import threading
from datetime import UTC, datetime
from itertools import pairwise

import httpx
import pytest
from earnings_core import sha256_hex
from earnings_ingestion.fetch.client import (
    AccessStop,
    PoliteClient,
    ProcessLock,
    Throttle,
    UnexpectedResponse,
    require_identity,
    retry_after_seconds,
)
from earnings_ingestion.fetch.records import RetrievalMethod

IDENTITY = "Jane Doe earnings-themes research jane@example.org"
NOW = datetime(2026, 9, 22, 12, 0, 0, tzinfo=UTC)
MARKERS = (b"undeclared automated tool",)


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def make_client(handler, *, clock=None, max_requests=500, host_allowed=None):
    clock = clock or FakeClock()
    throttle = Throttle(
        min_interval=0.5,
        max_requests=max_requests,
        clock=clock.clock,
        sleep=clock.sleep,
    )
    client = PoliteClient(
        IDENTITY,
        throttle=throttle,
        host_allowed=host_allowed or (lambda host: host.endswith("example.gov")),
        block_markers=MARKERS,
        transport=httpx.MockTransport(handler),
        sleep=clock.sleep,
        rng=random.Random(0),
        now=lambda: NOW,
    )
    return client, clock


def test_identity_must_be_descriptive_with_a_contact() -> None:
    assert require_identity("X_IDENTITY", {"X_IDENTITY": IDENTITY}) == IDENTITY
    for bad in ({}, {"X_IDENTITY": "jane@example.org"}, {"X_IDENTITY": "Jane Doe"}):
        with pytest.raises(AccessStop, match="X_IDENTITY"):
            require_identity("X_IDENTITY", bad)


def test_throttle_spaces_request_starts_and_enforces_the_budget() -> None:
    clock = FakeClock()
    throttle = Throttle(
        min_interval=0.5, max_requests=2, clock=clock.clock, sleep=clock.sleep
    )
    throttle.acquire()
    clock.now += 0.1
    throttle.acquire()
    assert clock.sleeps == [pytest.approx(0.4)]
    with pytest.raises(AccessStop, match="budget"):
        throttle.acquire()
    assert throttle.count == 2
    assert throttle.starts == [100.0, pytest.approx(100.5)]


def test_the_user_agent_is_the_identity() -> None:
    seen = []

    def handler(request):
        seen.append(request.headers["user-agent"])
        return httpx.Response(200, text="ok")

    client, _ = make_client(handler)
    client.get("https://www.example.gov/x")
    assert seen == [IDENTITY]


def test_redirect_hops_are_spaced_and_counted() -> None:
    def handler(request):
        if request.url.path == "/old":
            return httpx.Response(
                301, headers={"Location": "https://www.example.gov/new"}
            )
        return httpx.Response(200, text="ok")

    client, clock = make_client(handler)
    response = client.get("https://www.example.gov/old")
    assert str(response.url) == "https://www.example.gov/new"
    assert client.throttle.count == 2
    assert clock.sleeps == [pytest.approx(0.5)]


def test_a_redirect_off_the_allowed_hosts_stops_the_run() -> None:
    def handler(request):
        return httpx.Response(301, headers={"Location": "https://elsewhere.org/x"})

    client, _ = make_client(handler)
    with pytest.raises(AccessStop, match="outside this client's hosts"):
        client.get("https://www.example.gov/x")
    with pytest.raises(AccessStop, match="outside this client's hosts"):
        client.get("https://elsewhere.org/y")
    assert client.throttle.count == 1


def test_429_honours_retry_after_then_succeeds() -> None:
    responses = [
        httpx.Response(429, headers={"Retry-After": "7"}),
        httpx.Response(200, text="ok"),
    ]
    client, clock = make_client(lambda request: responses.pop(0))
    assert client.get("https://www.example.gov/x").status_code == 200
    assert client.throttle.count == 2
    assert max(clock.sleeps) >= 7


def test_a_persistent_403_stops_without_changing_identity() -> None:
    once = [httpx.Response(403), httpx.Response(200, text="ok")]
    client, _ = make_client(lambda request: once.pop(0))
    assert client.get("https://www.example.gov/x").status_code == 200

    agents = []

    def forbidden(request):
        agents.append(request.headers["user-agent"])
        return httpx.Response(403)

    client, _ = make_client(forbidden)
    with pytest.raises(AccessStop, match="403 persisted"):
        client.get("https://www.example.gov/x")
    assert client.throttle.count == 2
    assert agents == [IDENTITY, IDENTITY]


def test_server_errors_are_retried_a_bounded_number_of_times() -> None:
    client, _ = make_client(lambda request: httpx.Response(503))
    with pytest.raises(AccessStop, match="503"):
        client.get("https://www.example.gov/x")
    assert client.throttle.count == 4


def test_retry_after_accepts_seconds_and_http_dates() -> None:
    assert retry_after_seconds("12", NOW) == 12.0
    assert retry_after_seconds("Tue, 22 Sep 2026 12:00:30 GMT", NOW) == 30.0
    assert retry_after_seconds("soon", NOW) is None


def test_fetch_returns_decoded_bytes_and_a_retrieval() -> None:
    body = b'{"a": 1}'

    def handler(request):
        return httpx.Response(
            200,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Content-Encoding": "gzip",
            },
            content=gzip.compress(body),
        )

    client, _ = make_client(handler)
    fetched = client.fetch("https://www.example.gov/a.json", {"application/json"})
    assert fetched.body == body
    retrieval = fetched.retrieval
    assert retrieval.sha256 == sha256_hex(body)
    assert retrieval.byte_count == len(body)
    assert retrieval.media_type == "application/json"
    assert retrieval.content_type == "application/json; charset=utf-8"
    assert retrieval.retrieved_at == NOW
    assert retrieval.retrieval_method is RetrievalMethod.HTTP
    assert IDENTITY not in retrieval.model_dump_json()


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, headers={"Content-Type": "text/plain"}, text="{}"),
        httpx.Response(404, headers={"Content-Type": "application/json"}, text="{}"),
    ],
)
def test_unexpected_responses_are_refused(response) -> None:
    client, _ = make_client(lambda request: response)
    with pytest.raises(UnexpectedResponse):
        client.fetch("https://www.example.gov/a.json", {"application/json"})


def test_a_block_page_stops_the_run_even_where_json_was_expected() -> None:
    block = httpx.Response(
        200,
        headers={"Content-Type": "text/html"},
        text="Your Request Originates from an Undeclared Automated Tool",
    )
    client, _ = make_client(lambda request: block)
    with pytest.raises(AccessStop, match="block or rate-limit page"):
        client.fetch("https://www.example.gov/a.json", {"application/json"})


def test_only_one_lock_holder_at_a_time(tmp_path) -> None:
    path = tmp_path / "client.lock"
    with ProcessLock(path), pytest.raises(AccessStop), ProcessLock(path):
        pass
    with ProcessLock(path):
        pass


def test_concurrent_workers_share_one_allowance() -> None:
    """Eight threads through one client: starts at least 0.5 s apart, so no more
    than two start in any second (R1.3's 2 requests per second)."""
    client, _ = make_client(lambda request: httpx.Response(200, text="ok"))
    barrier = threading.Barrier(8)

    def worker(n: int) -> None:
        barrier.wait()
        client.get(f"https://www.example.gov/{n}")

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    starts = client.throttle.starts
    assert len(starts) == 8
    assert all(b - a >= 0.5 - 1e-9 for a, b in pairwise(starts))
    assert all(
        sum(start <= other < start + 1.0 for other in starts) <= 2 for start in starts
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_client.py -q`

Expected: FAIL. Collection stops with
`No module named 'earnings_ingestion.fetch.client'`, and pytest reports `1 error`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py`:

```python
"""A polite HTTP client for source adapters: one identity, one throttle, bounded retries.

Ported from Stage 1's live-fetch client, ``expirements/parser-fidelity/pf_fetch.py``
(D5: port it, never import it). What changed:

- The throttle is thread-safe, so workers share one client and one allowance.
- A host filter refuses any request, redirect hops included, outside the client's
  hosts.
- A text/html body carrying a block page stops the run before the content type is
  checked, so a block page served where JSON was expected also stops it.
- ``fetch`` returns the bytes and a ``Retrieval`` and writes nothing. The artifact
  store decides where bytes live.

A §393-408 govern every client. Each request start, redirect hops included, passes
the throttle. Timeouts are explicit, retries are bounded, with exponential backoff and
jitter, and ``Retry-After`` is honoured. A 403 that persists stops the run and the
identity is never changed. The identity is sent as the User-Agent and never recorded.
"""

import email.utils
import fcntl
import os
import random
import re
import threading
import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Self
from urllib.parse import urlsplit

import httpx
from earnings_core import sha256_hex

from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod

DEFAULT_MAX_REQUESTS = 500
MAX_ATTEMPTS = 4
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_CAP_SECONDS = 60.0
MAX_RETRY_AFTER_SECONDS = 300.0
TIMEOUT = httpx.Timeout(30.0, connect=10.0)
FORBIDDEN_LIMIT = 2  # a 403 on an attempt and again on its retry is "persistent"
BLOCK_SCAN_BYTES = 20_000

_CONTACT = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class AccessStop(RuntimeError):
    """The run must stop and be reported.

    Raised for a missing identity, a spent budget, a held lock, a persistent 403,
    exhausted retries, a block page, or a host outside the client's filter.
    """


class UnexpectedResponse(RuntimeError):
    """A response that must not be kept; the caller may skip the item and go on."""


def require_identity(variable: str, environ: Mapping[str, str] | None = None) -> str:
    """The descriptive User-Agent in ``variable``, which lives outside Git."""
    value = (os.environ if environ is None else environ).get(variable, "").strip()
    if len(value.split()) < 2 or not _CONTACT.search(value):
        raise AccessStop(
            f"{variable} must be set outside Git to a descriptive User-Agent with a"
            " real contact, such as 'Jane Doe earnings-themes research"
            " jane@example.org'"
        )
    return value


def retry_after_seconds(value: str | None, now: datetime) -> float | None:
    """The wait a ``Retry-After`` header asks for, in seconds, or None if unreadable."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, (when - now).total_seconds())


class Throttle:
    """Spaces request starts ``min_interval`` apart across threads, within a budget.

    The lock is held while waiting, so starts are serialised. ``starts`` records each
    start's clock reading, taken under the lock.
    """

    def __init__(
        self,
        *,
        min_interval: float,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.min_interval = min_interval
        self.max_requests = max_requests
        self.starts: list[float] = []
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()

    @property
    def count(self) -> int:
        """Requests started so far."""
        return len(self.starts)

    def acquire(self) -> None:
        with self._lock:
            if len(self.starts) >= self.max_requests:
                raise AccessStop(
                    f"request budget of {self.max_requests} reached; rerun to continue"
                )
            now = self._clock()
            if self.starts and now < self.starts[-1] + self.min_interval:
                self._sleep(self.starts[-1] + self.min_interval - now)
                now = self._clock()
            self.starts.append(now)


class ProcessLock:
    """An exclusive, non-blocking ``flock``: one holder per path on this machine.

    A second lock on the same path fails, in this process or another.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle: IO[str] | None = None

    def __enter__(self) -> Self:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("w")
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            raise AccessStop(f"another client holds {self.path}") from None
        self._handle = handle
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._handle is not None:
            fcntl.flock(self._handle, fcntl.LOCK_UN)
            self._handle.close()
            self._handle = None


@dataclass(frozen=True)
class Fetched:
    """A validated response body and the record of its retrieval."""

    body: bytes
    retrieval: Retrieval


class PoliteClient:
    """GET under the access policy of A §393-408. Share one instance across workers.

    ``host_allowed`` decides which hosts the client may reach; ``block_markers`` are
    lowercase byte strings whose presence in an HTML body means the server refused
    automated access.
    """

    def __init__(
        self,
        identity: str,
        *,
        throttle: Throttle,
        host_allowed: Callable[[str], bool] = lambda host: True,
        block_markers: Collection[bytes] = (),
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.throttle = throttle
        self._host_allowed = host_allowed
        self._markers = tuple(block_markers)
        self._sleep = sleep
        self._rng = rng or random.Random()
        self._now = now
        self._client = httpx.Client(
            headers={"User-Agent": identity, "Accept-Encoding": "gzip, deflate"},
            timeout=TIMEOUT,
            follow_redirects=True,
            transport=transport,
            event_hooks={"request": [self._before_request]},
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _check_host(self, url: str) -> None:
        host = (urlsplit(url).hostname or "").lower()
        if not self._host_allowed(host):
            raise AccessStop(f"{url} is outside this client's hosts")

    def _before_request(self, request: httpx.Request) -> None:
        """httpx calls this for every request it sends, redirect hops included."""
        self._check_host(str(request.url))
        self.throttle.acquire()

    def get(self, url: str) -> httpx.Response:
        """The response to one GET, after bounded retries on 403, 429, 5xx, and
        transport errors."""
        self._check_host(url)
        forbidden = 0
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self._client.get(url)
            except httpx.TransportError as exc:
                if attempt == MAX_ATTEMPTS:
                    raise AccessStop(
                        f"{type(exc).__name__} after {attempt} attempts: {url}"
                    ) from exc
                self._backoff(attempt, None)
                continue
            if response.status_code == 403:
                forbidden += 1
                if forbidden >= FORBIDDEN_LIMIT:
                    raise AccessStop(
                        f"403 persisted for {url}; stopping without changing identity"
                    )
                self._backoff(attempt, response)
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == MAX_ATTEMPTS:
                    raise AccessStop(
                        f"HTTP {response.status_code} after {attempt} attempts: {url}"
                    )
                self._backoff(attempt, response)
                continue
            return response
        raise AccessStop(f"no response for {url}")

    def fetch(self, url: str, expected_types: Collection[str]) -> Fetched:
        """A 200 response of an expected media type, or ``UnexpectedResponse``.

        A text/html body with a block marker raises ``AccessStop`` whatever was
        expected.
        """
        response = self.get(url)
        content_type = response.headers.get("content-type", "")
        media_type = content_type.split(";")[0].strip().lower()
        body = response.content  # Content-Encoding already decoded; charset untouched
        head = body[:BLOCK_SCAN_BYTES].lower()
        if media_type == "text/html" and any(mark in head for mark in self._markers):
            raise AccessStop(
                f"block or rate-limit page for {url}; stopping without changing"
                " identity"
            )
        if response.status_code != 200:
            raise UnexpectedResponse(f"HTTP {response.status_code} for {url}")
        if media_type not in expected_types:
            raise UnexpectedResponse(
                f"content type {content_type!r} for {url};"
                f" expected {sorted(expected_types)}"
            )
        retrieval = Retrieval(
            request_url=url,
            final_url=str(response.url),
            retrieved_at=self._now(),
            retrieval_method=RetrievalMethod.HTTP,
            http_status=response.status_code,
            media_type=media_type,
            content_type=content_type,
            byte_count=len(body),
            sha256=sha256_hex(body),
        )
        return Fetched(body=body, retrieval=retrieval)

    def _backoff(self, attempt: int, response: httpx.Response | None) -> None:
        delay = min(BACKOFF_CAP_SECONDS, BACKOFF_BASE_SECONDS * 2 ** (attempt - 1))
        delay *= self._rng.uniform(0.5, 1.0)
        header = response.headers.get("retry-after") if response is not None else None
        requested = retry_after_seconds(header, self._now())
        if requested is not None:
            if requested > MAX_RETRY_AFTER_SECONDS:
                raise AccessStop(
                    f"server asked to wait {requested:.0f}s; stopping the run"
                )
            delay = max(delay, requested)
        self._sleep(delay)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_client.py -q`

Expected: `15 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py packages/earnings-ingestion/tests/test_fetch_client.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `673 passed, 22 deselected`;
`All checks passed!` and `163 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/fetch/client.py packages/earnings-ingestion/tests/test_fetch_client.py
git commit -m "feat(ingestion): port pf_fetch's access policy into a shared polite client"
```

---
### Task 3: The robots.txt gate

Live acquisition must not bypass robots restrictions (P §Membership evidence and
source rights). The gate reads the `*` group's rules under RFC 9309:

- the longest matching rule wins, and an allow rule wins a tie;
- `*` matches any run of characters, and a trailing `$` anchors the end.

A robots.txt that answers 404 or 410 allows everything, and any other failure
disallows everything. It fetches each origin's robots.txt once, through the client
it is given, so the fetch counts against the same throttle. CPython's
`urllib.robotparser` applies the first matching rule and knows no wildcards, so it is
not used.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/fetch/robots.py`.
- Test (create): `packages/earnings-ingestion/tests/test_fetch_robots.py`.

**Interfaces:**

- Consumes: Task 2's `PoliteClient` and `AccessStop`.
- Produces, in `fetch/robots.py`:
  - `Rule(allow: bool, pattern: str)`;
  - `RobotsVerdict(url, allowed, robots_status, rule)`, where `rule` is the deciding
    rule as written, such as `Disallow: /w/`, or `None`;
  - `parse_robots(text) -> tuple[Rule, ...]`;
  - `decide(rules, target) -> tuple[bool, Rule | None]`;
  - `RobotsGate(client: PoliteClient)`, with `verdict(url) -> RobotsVerdict`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_fetch_robots.py`:

```python
"""The robots gate: RFC 9309 longest match for the ``*`` group."""

import random
from datetime import UTC, datetime

import httpx
import pytest
from earnings_ingestion.fetch.client import AccessStop, PoliteClient, Throttle
from earnings_ingestion.fetch.robots import RobotsGate, decide, parse_robots

ROBOTS = """
User-agent: SomeBot
Disallow: /

User-agent: *
Allow: /w/api.php?action=mobileview&
Disallow: /w/
Disallow: /api/
Disallow: /*.pdf$
Allow: /wiki/Special:Export
Disallow: /wiki/Special:
Disallow:
"""


def gate_for(handler) -> tuple[RobotsGate, PoliteClient]:
    client = PoliteClient(
        "Jane Doe earnings-themes research jane@example.org",
        throttle=Throttle(min_interval=0.0),
        transport=httpx.MockTransport(handler),
        sleep=lambda seconds: None,
        rng=random.Random(0),
        now=lambda: datetime(2026, 9, 27, tzinfo=UTC),
    )
    return RobotsGate(client), client


@pytest.mark.parametrize(
    ("target", "allowed"),
    [
        ("/wiki/Dow_Jones_Industrial_Average?oldid=123", True),
        ("/w/index.php?oldid=123&action=raw", False),
        ("/w/api.php?action=mobileview&page=X", True),
        ("/api/rest_v1/page/html/X", False),
        ("/files/release.pdf", False),
        ("/files/release.pdf?download=1", True),
        ("/wiki/Special:Export/X", True),
        ("/wiki/Special:History", False),
    ],
)
def test_the_longest_matching_rule_decides(target, allowed) -> None:
    assert decide(parse_robots(ROBOTS), target)[0] is allowed


def test_other_agents_groups_are_ignored_and_an_empty_disallow_adds_nothing() -> None:
    rules = parse_robots(ROBOTS)
    assert all(rule.pattern != "/" for rule in rules)
    assert len(rules) == 6


def test_an_allow_rule_wins_a_tie() -> None:
    rules = parse_robots("User-agent: *\nDisallow: /a\nAllow: /a\n")
    assert decide(rules, "/a")[0] is True


def test_the_gate_reads_robots_once_per_origin() -> None:
    fetched = []

    def handler(request):
        fetched.append(str(request.url))
        return httpx.Response(200, text=ROBOTS)

    gate, _ = gate_for(handler)
    first = gate.verdict("https://en.example.org/w/index.php?title=X")
    second = gate.verdict("https://en.example.org/wiki/X?oldid=9")
    assert (first.allowed, first.rule) == (False, "Disallow: /w/")
    assert (second.allowed, second.rule) == (True, None)
    assert fetched == ["https://en.example.org/robots.txt"]


@pytest.mark.parametrize(
    ("status", "allowed"), [(404, True), (410, True), (401, False)]
)
def test_a_missing_robots_allows_and_a_refused_one_disallows(status, allowed) -> None:
    gate, _ = gate_for(lambda request: httpx.Response(status))
    verdict = gate.verdict("https://en.example.org/wiki/X")
    assert (verdict.allowed, verdict.robots_status) == (allowed, status)


def test_a_persistent_403_on_robots_stops_the_source() -> None:
    gate, _ = gate_for(lambda request: httpx.Response(403))
    with pytest.raises(AccessStop, match="403 persisted"):
        gate.verdict("https://www.example.com/terms")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_robots.py -q`

Expected: FAIL. Collection stops with
`No module named 'earnings_ingestion.fetch.robots'`, and pytest reports `1 error`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/fetch/robots.py`:

```python
"""A robots.txt gate for every source but SEC (P §Membership evidence and source rights).

Live acquisition must not bypass robots restrictions. The gate reads the rules of the
``*`` group under RFC 9309:

- the longest matching rule wins, and an allow rule wins a tie;
- ``*`` matches any run of characters, and a trailing ``$`` anchors the end;
- rules match the URL's path and query, compared as written.

A robots.txt answering 404 or 410 allows everything. Any other failure disallows
everything, which is stricter than RFC 9309: a 401 or another 4xx, or a response the
client gives up on. A 403 that persists stops the client itself (A §404).
CPython's ``urllib.robotparser`` is not used, because it applies the first matching
rule and knows no wildcards.
"""

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from earnings_ingestion.fetch.client import PoliteClient


@dataclass(frozen=True)
class Rule:
    allow: bool
    pattern: str


@dataclass(frozen=True)
class RobotsVerdict:
    """Whether ``url`` may be fetched, and why."""

    url: str
    allowed: bool
    robots_status: int
    rule: str | None
    """The deciding rule, e.g. ``Disallow: /w/``; None when no rule matched."""


def parse_robots(text: str) -> tuple[Rule, ...]:
    """The allow and disallow rules of every group whose user-agent is ``*``."""
    rules: list[Rule] = []
    agents: list[str] = []
    in_rules = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        field, colon, value = line.partition(":")
        if not colon:
            continue
        field, value = field.strip().lower(), value.strip()
        if field == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(value.lower())
        elif field in ("allow", "disallow"):
            in_rules = True
            if "*" in agents and value:
                rules.append(Rule(allow=field == "allow", pattern=value))
    return tuple(rules)


def _matches(pattern: str, target: str) -> bool:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    regex = "".join(".*" if char == "*" else re.escape(char) for char in body)
    return re.match(regex + (r"\Z" if anchored else ""), target, re.DOTALL) is not None


def decide(rules: tuple[Rule, ...], target: str) -> tuple[bool, Rule | None]:
    """RFC 9309's verdict for ``target``, a path with its query."""
    best: Rule | None = None
    for rule in rules:
        if not _matches(rule.pattern, target):
            continue
        if (
            best is None
            or len(rule.pattern) > len(best.pattern)
            or (len(rule.pattern) == len(best.pattern) and rule.allow)
        ):
            best = rule
    return (True if best is None else best.allow), best


class RobotsGate:
    """Reads each origin's robots.txt once, through the client, and answers per URL."""

    def __init__(self, client: PoliteClient) -> None:
        self._client = client
        self._origins: dict[str, tuple[int, tuple[Rule, ...] | None]] = {}

    def verdict(self, url: str) -> RobotsVerdict:
        parts = urlsplit(url)
        status, rules = self._rules(f"{parts.scheme}://{parts.netloc}")
        if rules is None:
            return RobotsVerdict(
                url=url, allowed=False, robots_status=status, rule=None
            )
        target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        allowed, rule = decide(rules, target)
        written = None
        if rule is not None:
            written = f"{'Allow' if rule.allow else 'Disallow'}: {rule.pattern}"
        return RobotsVerdict(
            url=url, allowed=allowed, robots_status=status, rule=written
        )

    def _rules(self, origin: str) -> tuple[int, tuple[Rule, ...] | None]:
        if origin not in self._origins:
            response = self._client.get(f"{origin}/robots.txt")
            if response.status_code == 200:
                rules: tuple[Rule, ...] | None = parse_robots(response.text)
            elif response.status_code in (404, 410):
                rules = ()
            else:
                rules = None
            self._origins[origin] = (response.status_code, rules)
        return self._origins[origin]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_robots.py -q`

Expected: `15 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/fetch/robots.py packages/earnings-ingestion/tests/test_fetch_robots.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `688 passed, 22 deselected`;
`All checks passed!` and `165 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/fetch/robots.py packages/earnings-ingestion/tests/test_fetch_robots.py
git commit -m "feat(ingestion): gate web fetches on robots.txt"
```

---
### Task 4: The shared SEC client (R1.3, D5)

Every SEC request in the monorepo goes through this client (P6-16):

- request starts are spaced 0.5 s apart across `www.sec.gov` and `data.sec.gov`;
- the identity in `EDGAR_IDENTITY` is sent as the User-Agent;
- SEC's block page or a persistent 403 stops the run;
- one client per machine, held by an `flock` on `data/runs/sec/sec-client.lock`.

CIKs are 10-character zero-padded text in every record, and each URL builder
converts one to the form its endpoint uses (A §264).

- **The URL builders** live in `sec/urls.py`, which imports no HTTP library. The
  offline build (Task 12) uses them without loading a network client.
- **The register.** `sec-edgar`'s entry in `docs/source-register.toml` still names
  Stage 1's harness client. This task names the shared client and Stage 4's reads,
  then reruns the register's quote check. The check reads the saved policy pages in
  `data/raw/register/`.
- **Import checks.** The runtime import check gains the new clients: none may load a
  browser library or another package.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/sec/__init__.py`
  (empty), `sec/identifiers.py`, `sec/urls.py`, and `sec/client.py`.
- Modify: `packages/earnings-ingestion/tests/test_import_boundaries.py` (replaced
  whole, block 1 of 3), and `docs/source-register.toml` (replaced whole).
- Test (create): `packages/earnings-ingestion/tests/test_sec_client.py`.

**Interfaces:**

- Consumes: Task 2's `PoliteClient`, `Throttle`, `ProcessLock`, `require_identity`,
  `AccessStop`, and `DEFAULT_MAX_REQUESTS`.
- Produces:
  - `sec/identifiers.py`:
    - `Cik`, a string of exactly 10 digits;
    - `pad_cik(value: int | str) -> str`, which raises `ValueError` for a non-CIK;
    - `unpad_cik(cik: str) -> str`.
  - `sec/urls.py`:
    - `SEC_HOSTS` and `COMPANY_TICKERS_URL`;
    - `is_sec_host(host) -> bool`;
    - `submissions_url(cik) -> str`, which gives
      `https://data.sec.gov/submissions/CIK<10 digits>.json`;
    - `submissions_page_url(name) -> str`;
    - `archive_url(cik, accession, filename) -> str`, which uses the unpadded CIK
      and the accession without dashes.
  - `sec/client.py`:
    - `IDENTITY_ENV = "EDGAR_IDENTITY"`, `MIN_INTERVAL_SECONDS = 0.5`,
      `BLOCK_MARKERS`, and `LOCK_PATH`;
    - `SecClient(PoliteClient)`;
    - the context manager `open_sec_client(repo, *, environ=None, max_requests=500, transport=None, clock=..., sleep=..., rng=None, now=...)`,
      which yields a `SecClient`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_sec_client.py`:

```python
"""The shared SEC client (R1.3, D5): one per machine, 2 requests per second across SEC
hosts, and a stop on a persistent 403 without changing identity."""

import random
import threading
from datetime import UTC, datetime
from itertools import pairwise

import httpx
import pytest
from earnings_ingestion.fetch.client import AccessStop
from earnings_ingestion.sec.client import MIN_INTERVAL_SECONDS, open_sec_client
from earnings_ingestion.sec.identifiers import pad_cik, unpad_cik
from earnings_ingestion.sec.urls import archive_url, is_sec_host, submissions_url

IDENTITY = "Jane Doe earnings-themes research jane@example.org"
ENVIRON = {"EDGAR_IDENTITY": IDENTITY}


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def opened(tmp_path, handler, clock=None):
    clock = clock or FakeClock()
    return open_sec_client(
        tmp_path,
        environ=ENVIRON,
        transport=httpx.MockTransport(handler),
        clock=clock.clock,
        sleep=clock.sleep,
        rng=random.Random(0),
        now=lambda: datetime(2026, 9, 27, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    ("value", "padded"),
    [(320193, "0000320193"), ("320193", "0000320193"), ("0000320193", "0000320193")],
    ids=["int", "unpadded", "padded"],
)
def test_a_cik_is_ten_zero_padded_digits(value, padded) -> None:
    assert pad_cik(value) == padded
    assert unpad_cik(padded) == "320193"


@pytest.mark.parametrize("value", ["", "0", "12345678901", "32O193", True, -5])
def test_a_non_cik_is_refused(value) -> None:
    with pytest.raises(ValueError, match="not a CIK"):
        pad_cik(value)


def test_urls_use_each_endpoints_cik_form() -> None:
    assert (
        submissions_url("320193")
        == "https://data.sec.gov/submissions/CIK0000320193.json"
    )
    assert archive_url("0001041130", "0001752724-24-212345", "primary_doc.xml") == (
        "https://www.sec.gov/Archives/edgar/data/1041130/000175272424212345/"
        "primary_doc.xml"
    )


def test_only_sec_hosts_are_sec_hosts() -> None:
    assert is_sec_host("www.sec.gov") and is_sec_host("DATA.SEC.GOV")
    assert not is_sec_host("sec.gov.example.org")


def test_the_client_needs_an_identity(tmp_path) -> None:
    with (
        pytest.raises(AccessStop, match="EDGAR_IDENTITY"),
        open_sec_client(tmp_path, environ={}),
    ):
        pass


def test_one_client_per_machine(tmp_path) -> None:
    def ok(request):
        return httpx.Response(200, text="ok")

    with (
        opened(tmp_path, ok),
        pytest.raises(AccessStop, match="another client holds"),
        opened(tmp_path, ok),
    ):
        pass
    with opened(tmp_path, ok):
        pass


def test_the_client_reaches_sec_hosts_only(tmp_path) -> None:
    with (
        opened(tmp_path, lambda request: httpx.Response(200)) as client,
        pytest.raises(AccessStop, match="outside this client's hosts"),
    ):
        client.get("https://www.example.org/x")


def test_concurrent_workers_stay_at_or_below_two_requests_per_second(tmp_path) -> None:
    """Twelve workers alternate between www.sec.gov and data.sec.gov through the one
    client; every start is at least 0.5 s after the last."""
    seen_agents = []

    def handler(request):
        seen_agents.append(request.headers["user-agent"])
        return httpx.Response(200, headers={"Content-Type": "application/json"})

    with opened(tmp_path, handler) as client:
        barrier = threading.Barrier(12)

        def worker(n: int) -> None:
            host = "www.sec.gov" if n % 2 else "data.sec.gov"
            barrier.wait()
            client.get(f"https://{host}/{n}")

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        starts = client.throttle.starts
    assert client.throttle.min_interval == MIN_INTERVAL_SECONDS == 0.5
    assert len(starts) == 12
    assert all(b - a >= 0.5 - 1e-9 for a, b in pairwise(starts))
    assert all(sum(s <= t < s + 1.0 for t in starts) <= 2 for s in starts)
    assert set(seen_agents) == {IDENTITY}


def test_a_persistent_403_stops_without_rotating_identity(tmp_path) -> None:
    agents = []

    def handler(request):
        agents.append(request.headers["user-agent"])
        return httpx.Response(403)

    with (
        opened(tmp_path, handler) as client,
        pytest.raises(AccessStop, match="403 persisted"),
    ):
        client.get(submissions_url("320193"))
    assert agents == [IDENTITY, IDENTITY]


def test_sec_block_page_stops_the_run(tmp_path) -> None:
    def handler(request):
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text="Request Rate Threshold Exceeded",
        )

    with (
        opened(tmp_path, handler) as client,
        pytest.raises(AccessStop, match="block or rate-limit page"),
    ):
        client.fetch(submissions_url("320193"), {"application/json"})
```

Replace `packages/earnings-ingestion/tests/test_import_boundaries.py` with:

```python
"""earnings-ingestion imports neither earnings-themes nor the application, and no
browser: browser capture stays behind an optional extra (A §173; B3).

Only ``earnings_ingestion.browser.selenium_capture`` may load a browser library, and
only when something imports it; tests/contracts/test_import_scan.py checks the source
statically as well.
"""

import json
import subprocess
import sys

import pytest

FORBIDDEN = {
    "earnings_themes",
    "earnings_pipeline",
    "selenium",
    "websocket",
    "playwright",
    "pyppeteer",
}


def modules_loaded_by(module: str) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing ``module``."""
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return {name.partition(".")[0] for name in json.loads(result.stdout)}


@pytest.mark.parametrize(
    "module",
    [
        "earnings_ingestion",
        "earnings_ingestion.browser",
        "earnings_ingestion.browser.install",
        "earnings_ingestion.browser.renderer",
        "earnings_ingestion.browser.serialize",
        "earnings_ingestion.browser.store",
        "earnings_ingestion.layout",
        "earnings_ingestion.layout.extract",
        "earnings_ingestion.fetch.client",
        "earnings_ingestion.fetch.robots",
        "earnings_ingestion.sec.client",
    ],
)
def test_importing_ingestion_loads_nothing_forbidden(module: str) -> None:
    assert modules_loaded_by(module) & FORBIDDEN == set()

```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_sec_client.py packages/earnings-ingestion/tests/test_import_boundaries.py -q`

Expected: FAIL. `test_sec_client.py` stops at collection with
`No module named 'earnings_ingestion.sec'`, and pytest reports `1 error`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/sec/__init__.py`:

```python
```

Create `packages/earnings-ingestion/src/earnings_ingestion/sec/identifiers.py`:

```python
"""SEC Central Index Keys: 10-character zero-padded text in every record (A §264).

``pad_cik`` makes the canonical form from any representation SEC serves, and
``unpad_cik`` makes the unpadded form that EDGAR's archive paths use.
"""

import re
from typing import Annotated

from pydantic import StringConstraints

Cik = Annotated[str, StringConstraints(pattern=r"^\d{10}$")]
"""A CIK written as exactly 10 decimal digits, zero-padded."""

_DIGITS = re.compile(r"^\d{1,10}$")


def pad_cik(value: int | str) -> str:
    """The 10-character zero-padded form; ``ValueError`` if ``value`` is no CIK."""
    text = "" if isinstance(value, bool) else str(value).strip()
    if not _DIGITS.match(text) or int(text) == 0:
        raise ValueError(f"not a CIK: {value!r}")
    return text.zfill(10)


def unpad_cik(cik: str) -> str:
    """The unpadded form, for EDGAR archive paths."""
    return str(int(pad_cik(cik)))
```

Create `packages/earnings-ingestion/src/earnings_ingestion/sec/urls.py`:

```python
"""SEC hosts and URLs, with no network client: parsers and builders import these.

A module that reads saved SEC bytes needs the URLs they came from, to find them in
the artifact store and to cite them, but must never import the client that fetches
them (A §410); ``sec.client`` imports this module, never the reverse.
"""

from earnings_ingestion.sec.identifiers import pad_cik, unpad_cik

SEC_HOSTS = frozenset({"www.sec.gov", "data.sec.gov"})
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def is_sec_host(host: str) -> bool:
    """True for sec.gov and every host under it: only the SEC client may reach them."""
    host = host.lower()
    return host == "sec.gov" or host.endswith(".sec.gov")


def submissions_url(cik: str | int) -> str:
    return f"https://data.sec.gov/submissions/CIK{pad_cik(cik)}.json"


def submissions_page_url(name: str) -> str:
    """An older filings page named in a submissions file's ``filings.files``."""
    return f"https://data.sec.gov/submissions/{name}"


def archive_url(cik: str | int, accession: str, filename: str) -> str:
    """A filed document under EDGAR's archive, which uses the unpadded CIK."""
    folder = accession.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{unpad_cik(cik)}/{folder}/{filename}"
    )
```

Create `packages/earnings-ingestion/src/earnings_ingestion/sec/client.py`:

```python
"""The shared SEC client (R1.3, D5): every SEC request in the monorepo goes through it.

- **One per machine.** ``open_sec_client`` holds the SEC lock while the client is open,
  so a second client stops instead of opening, in this process or another. Share the
  one instance across workers: its throttle is thread-safe.
- **2 requests per second.** Request starts are spaced 0.5 s apart across every SEC
  host, redirect hops included (A §397), within a per-run budget.
- **Identity.** The User-Agent is the descriptive identity in ``EDGAR_IDENTITY``,
  configured outside Git and never recorded (A §393).
- **Refusals.** A 403 that persists, or SEC's block page, stops the run without
  changing identity (A §404).

Two limits remain, because A §398 asks for coordination across the outbound network.
The lock coordinates the processes of one machine only. Stage 1's frozen harness keeps
its own client and lock, so it must never run live at the same time.
"""

import random
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import httpx

from earnings_ingestion.fetch.client import (
    DEFAULT_MAX_REQUESTS,
    PoliteClient,
    ProcessLock,
    Throttle,
    require_identity,
)
from earnings_ingestion.sec.urls import SEC_HOSTS

IDENTITY_ENV = "EDGAR_IDENTITY"
MIN_INTERVAL_SECONDS = 0.5  # the project default of 2 requests per second (A §397)
BLOCK_MARKERS = (b"undeclared automated tool", b"request rate threshold exceeded")
LOCK_PATH = Path("data") / "runs" / "sec" / "sec-client.lock"
"""Relative to the repository root. Every package client uses this one path."""


class SecClient(PoliteClient):
    """The shared SEC client. Open it with ``open_sec_client``, never directly."""

    def __init__(
        self,
        identity: str,
        *,
        throttle: Throttle,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        super().__init__(
            identity,
            throttle=throttle,
            host_allowed=SEC_HOSTS.__contains__,
            block_markers=BLOCK_MARKERS,
            transport=transport,
            sleep=sleep,
            rng=rng,
            now=now,
        )


@contextmanager
def open_sec_client(
    repo: Path,
    *,
    environ: Mapping[str, str] | None = None,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    transport: httpx.BaseTransport | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Iterator[SecClient]:
    """The machine's one SEC client, holding the SEC lock under ``repo`` while open."""
    identity = require_identity(IDENTITY_ENV, environ)
    with ProcessLock(repo / LOCK_PATH):
        throttle = Throttle(
            min_interval=MIN_INTERVAL_SECONDS,
            max_requests=max_requests,
            clock=clock,
            sleep=sleep,
        )
        client = SecClient(
            identity,
            throttle=throttle,
            transport=transport,
            sleep=sleep,
            rng=rng,
            now=now,
        )
        try:
            yield client
        finally:
            client.close()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_sec_client.py packages/earnings-ingestion/tests/test_import_boundaries.py -q`

Expected: `28 passed`.

- [ ] **Step 5: Name the shared client in the release register**

Replace `docs/source-register.toml` with:

```toml
# Source register (AGENTS.md §242): one table per source under [sources], keyed by the
# source_id that tests/fixtures/releases/manifest.toml cites. Every quote is copied
# verbatim from a page saved by expirements/parser-fidelity/fetch_policy_pages.py, and
# `fetch_policy_pages.py verify` checks each quote, URL, and date against that page.
schema_version = 1

[sources.sec-edgar]
owner = "U.S. Securities and Exchange Commission (SEC)"
url = "https://www.sec.gov/edgar"
access_method = """HTTPS GET of EDGAR quarterly full-index files (www.sec.gov/Archives/edgar/full-index/), \
SEC's company ticker list (www.sec.gov/files/company_tickers.json), submissions JSON \
(data.sec.gov/submissions/), filing index pages, and filed documents, N-PORT reports included. \
Every package request goes through the shared SEC client, earnings_ingestion.sec.client (R1.3, \
decision D5 of the roadmap), with a descriptive User-Agent read from EDGAR_IDENTITY, which is \
configured outside Git. Stage 1's frozen harness keeps its own client, \
expirements/parser-fidelity/pf_fetch.py; the two never run live at the same time."""
cost = "Free; no account or API key."
license_terms = """The SEC's statement on reuse of its website content is quoted in \
[sources.sec-edgar.reuse_policy]. Filed documents are authored by the filers."""
redistribution_status = """The SEC's reuse statement is quoted in [sources.sec-edgar.reuse_policy]. \
That statement does not address issuers' copyright in their filings, and this register draws no \
conclusion about it. Stage 1 commits eight release exhibits byte-for-byte under decision F1 of \
specs/release-parser-fidelity.md."""
coverage = """EDGAR electronic filings. Stage 1 samples Form 8-K filings that report Item 2.02 \
(Results of Operations and Financial Condition), which dates from August 2004, and their \
press-release exhibits. Stage 4 reads the company ticker list, which maps current tickers to CIKs, \
registrants' submissions records, and a fund's N-PORT holdings reports."""
expected_update_pattern = """Filings arrive as the SEC accepts them. Amendments and corrections \
arrive as new accessions rather than edits to filed documents. A quarter's full-index files grow \
until the quarter ends."""
known_limitations = [
    "Exhibit numbering and descriptions vary by filer; a press release is not always EX-99.1.",
    "Some exhibits are image-only or plain text; Stage 1 excludes them (R4.3).",
    "Exhibit HTML is generated by filers and filing agents and is often malformed.",
    "Charsets are often undeclared; Stage 1 decodes with browser rules (pf_decode.py).",
]
last_verified = 2026-09-22

[sources.sec-edgar.access]
# R1.3 of specs/evidence-linked-theme-extraction.md (verified access behavior, RC §1).
user_agent_required = true
missing_user_agent_status = 403
rate_limit_breach_status = 429
project_max_requests_per_second = 2
url = "https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data"
checked_on = 2026-09-22
access_quote = "Please declare your user agent in request headers:"

[sources.sec-edgar.reuse_policy]
url = "https://www.sec.gov/about/privacy-information"
checked_on = 2026-09-22
quote = "Information presented on sec.gov is considered public information and may be copied or further distributed by users of the web site without the SEC’s permission."
```

Only `access_method` and `coverage` change. `last_verified` stays `2026-09-22`,
because no policy page was reread.

Run: `uv run --locked --all-packages python expirements/parser-fidelity/fetch_policy_pages.py verify`

Expected: `register quotes verified`.

- [ ] **Step 6: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/sec/*.py packages/earnings-ingestion/tests/test_sec_client.py packages/earnings-ingestion/tests/test_import_boundaries.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `708 passed, 22 deselected`;
`All checks passed!` and `169 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/sec packages/earnings-ingestion/tests/test_sec_client.py packages/earnings-ingestion/tests/test_import_boundaries.py docs/source-register.toml
git commit -m "feat(ingestion): add the shared SEC client (R1.3, D5)"
```

---
### Task 5: SEC's record readers, and the live format probe

Three SEC records serve Stage 4, and each reader is a pure function of saved bytes
(A §410):

- **The ticker list**, `company_tickers.json`, maps current tickers to CIKs. Its
  tickers only propose candidates (A §268).
- **A registrant's submissions** hold its conformed name, former names, current
  tickers, and filings. The filings sit in column arrays, with older ones on
  separate pages.
- **An N-PORT primary document** holds a fund's holdings on its report date.
  EDGAR's `primaryDocument` for an XML form can name its rendered view, such as
  `xslFormNPORT-P_X01/primary_doc.xml`, so `raw_document_name` recovers the filed
  file.

Each reader checks the shape it relies on and raises `SecDataError` on any other
shape. So an HTML block page or a changed format never reads as empty data (A §407).
Every record carries the JSON pointer of its value, so evidence can cite it.

The readers encode assumptions about SEC's formats, and the synthetic cohort (Task
12) encodes them again. The last step therefore checks them once against live SEC
data, at a gate (P6-21). The probe also confirms the fund's CIK, `0001041130`, by the
fund's name. That CIK was a lead found at planning, and Task 17 names it in
`universe.toml`.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/sec/data.py`.
- Test (create): `packages/earnings-ingestion/tests/test_sec_data.py`, and
  `tests/integration/test_sec_formats_live.py` (marked `live`).

**Interfaces:**

- Consumes: Task 4's `pad_cik`, and the URL builders, which only the probe uses.
- Produces, in `sec/data.py`:
  - `SecDataError(ValueError)` and `FILING_COLUMNS`;
  - `TickerEntry(ticker, cik, title, pointer)`;
  - `FormerName(name, valid_from, valid_to, pointer)`;
  - `Filing(accession, form, filing_date, report_date, accepted_at, primary_document, columns, index)`,
    with `pointer(column) -> str`;
  - `Registrant(cik, name, tickers, former_names, filings, older_pages)`;
  - `Holding(name, title, asset_category, position)` and
    `HoldingsReport(report_date, holdings)`;
  - `read_company_tickers(body) -> tuple[TickerEntry, ...]`;
  - `read_submissions(body) -> Registrant`;
  - `read_submissions_page(body) -> tuple[Filing, ...]`;
  - `read_filing_columns(columns, pointer) -> tuple[Filing, ...]`;
  - `raw_document_name(primary_document) -> str`;
  - `read_nport_holdings(body) -> HoldingsReport`;
  - `json_pointer_token(key) -> str`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_sec_data.py`:

```python
"""The SEC data readers: ticker list, submissions, and N-PORT holdings."""

import json
from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.sec.data import (
    SecDataError,
    raw_document_name,
    read_company_tickers,
    read_nport_holdings,
    read_submissions,
    read_submissions_page,
)


def submissions(**overrides) -> bytes:
    data = {
        "cik": "9990001",
        "name": "Acme Industrial Corp",
        "tickers": ["ACME"],
        "formerNames": [
            {
                "name": "ACME WIDGETS INC",
                "from": "2001-01-01T00:00:00.000Z",
                "to": "2025-03-01T00:00:00.000Z",
            }
        ],
        "filings": {
            "recent": {
                "accessionNumber": ["0009990001-25-000002", "0009990001-24-000001"],
                "filingDate": ["2025-02-01", "2024-08-01"],
                "reportDate": ["2024-12-31", ""],
                "acceptanceDateTime": [
                    "2025-02-01T16:05:00.000Z",
                    "2024-08-01T09:00:00.000Z",
                ],
                "form": ["10-K", "8-K"],
                "primaryDocument": ["acme-10k.htm", "acme-8k.htm"],
            },
            "files": [{"name": "CIK0009990001-submissions-001.json"}],
        },
    }
    return json.dumps(data | overrides).encode()


NPORT = b"""<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport"
                 xmlns:com="http://www.sec.gov/edgar/common">
  <headerData><submissionType>NPORT-P</submissionType></headerData>
  <formData>
    <genInfo><repPdEnd>2024-10-31</repPdEnd><repPdDate>2024-07-31</repPdDate></genInfo>
    <invstOrSecs>
      <invstOrSec><name>Acme Industrial Corp</name><title>Acme Industrial Corp</title>
        <assetCat>EC</assetCat></invstOrSec>
      <invstOrSec><name>Borealis Air Inc/The</name><assetCat>EC</assetCat></invstOrSec>
    </invstOrSecs>
  </formData>
</edgarSubmission>
"""


def test_the_ticker_list_pads_ciks_and_cites_each_entry() -> None:
    body = json.dumps(
        {"0": {"cik_str": 9990001, "ticker": "ACME", "title": "Acme Industrial Corp"}}
    ).encode()
    (entry,) = read_company_tickers(body)
    assert (entry.ticker, entry.cik, entry.pointer) == ("ACME", "0009990001", "/0")


@pytest.mark.parametrize(
    "body",
    [
        b"<html>Undeclared Automated Tool</html>",
        b"{}",
        b'{"0": {"ticker": "ACME"}}',
    ],
    ids=["block-page", "empty", "no-cik"],
)
def test_a_ticker_list_of_another_shape_is_refused(body) -> None:
    with pytest.raises(SecDataError):
        read_company_tickers(body)


def test_submissions_give_name_former_names_tickers_and_filings() -> None:
    registrant = read_submissions(submissions())
    assert registrant.cik == "0009990001"
    assert registrant.name == "Acme Industrial Corp"
    assert registrant.tickers == ("ACME",)
    assert registrant.former_names[0].name == "ACME WIDGETS INC"
    assert registrant.former_names[0].pointer == "/formerNames/0"
    first, second = registrant.filings
    assert first.accepted_at == datetime(2025, 2, 1, 16, 5, tzinfo=UTC)
    assert (first.report_date, second.report_date) == (date(2024, 12, 31), None)
    assert second.pointer("form") == "/filings/recent/form/1"
    assert registrant.older_pages == ("CIK0009990001-submissions-001.json",)


def test_ragged_filing_columns_are_refused() -> None:
    body = json.loads(submissions())
    body["filings"]["recent"]["form"] = ["10-K"]
    with pytest.raises(SecDataError, match="one length"):
        read_submissions(json.dumps(body).encode())


def test_an_older_page_has_the_columns_at_the_top_level() -> None:
    page = json.loads(submissions())["filings"]["recent"]
    filings = read_submissions_page(json.dumps(page).encode())
    assert [filing.form for filing in filings] == ["10-K", "8-K"]
    assert filings[0].pointer("form") == "/form/0"


def test_the_rendered_view_is_not_the_filed_document() -> None:
    assert raw_document_name("xslFormNPORT-P_X01/primary_doc.xml") == "primary_doc.xml"
    assert raw_document_name("primary_doc.xml") == "primary_doc.xml"


def test_nport_holdings_are_read_in_order_with_their_report_date() -> None:
    report = read_nport_holdings(NPORT)
    assert report.report_date == date(2024, 7, 31)
    assert [(h.name, h.asset_category, h.position) for h in report.holdings] == [
        ("Acme Industrial Corp", "EC", 1),
        ("Borealis Air Inc/The", "EC", 2),
    ]


@pytest.mark.parametrize(
    "body",
    [
        b"<html><body>Request Rate Threshold Exceeded</body></html>",
        NPORT.replace(b"<repPdDate>2024-07-31</repPdDate>", b""),
        NPORT.replace(b"<name>Acme Industrial Corp</name>", b""),
        b"not xml",
    ],
    ids=["html", "no-report-date", "unnamed-holding", "not-xml"],
)
def test_an_nport_document_of_another_shape_is_refused(body) -> None:
    with pytest.raises(SecDataError):
        read_nport_holdings(body)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_sec_data.py -q`

Expected: FAIL. Collection stops with
`No module named 'earnings_ingestion.sec.data'`, and pytest reports `1 error`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/sec/data.py`:

```python
"""Readers for the SEC data Stage 4 uses: pure functions of saved bytes (A §410).

- ``company_tickers.json`` is SEC's current ticker list. Its tickers only propose
  candidates; they never establish identity (A §268).
- A registrant's submissions JSON holds its conformed name, former names, current
  tickers, and filings. Older filings sit in separate pages that ``filings.files``
  names.
- An N-PORT primary document holds a fund's holdings on its report date.

Each reader checks the shape it relies on and raises ``SecDataError`` on any other, so
an HTML block page or a changed format never reads as empty data (A §407). Every
record carries the JSON pointer of the value it came from, so evidence can cite it.
"""

import json
from dataclasses import dataclass
from datetime import date, datetime

from lxml import etree

from earnings_ingestion.sec.identifiers import pad_cik

FILING_COLUMNS = (
    "accessionNumber",
    "filingDate",
    "reportDate",
    "acceptanceDateTime",
    "form",
    "primaryDocument",
)


class SecDataError(ValueError):
    """SEC bytes that do not have the shape a reader relies on."""


@dataclass(frozen=True)
class TickerEntry:
    ticker: str
    cik: str
    title: str
    pointer: str
    """The entry's JSON pointer in ``company_tickers.json``, e.g. ``/12``."""


@dataclass(frozen=True)
class FormerName:
    name: str
    valid_from: str | None
    valid_to: str | None
    pointer: str


@dataclass(frozen=True)
class Filing:
    accession: str
    form: str
    filing_date: date
    report_date: date | None
    accepted_at: datetime | None
    primary_document: str
    columns: str
    """The JSON pointer of the column arrays holding this filing, e.g. ``/filings/recent``."""
    index: int

    def pointer(self, column: str) -> str:
        """The JSON pointer of one of this filing's values."""
        return f"{self.columns}/{json_pointer_token(column)}/{self.index}"


@dataclass(frozen=True)
class Registrant:
    cik: str
    name: str
    tickers: tuple[str, ...]
    former_names: tuple[FormerName, ...]
    filings: tuple[Filing, ...]
    older_pages: tuple[str, ...]
    """Names of the older filing pages, fetched separately when needed."""


@dataclass(frozen=True)
class Holding:
    name: str
    title: str | None
    asset_category: str | None
    position: int
    """1-based order in the filing."""


@dataclass(frozen=True)
class HoldingsReport:
    report_date: date
    holdings: tuple[Holding, ...]


def json_pointer_token(key: str) -> str:
    """RFC 6901 escaping of one reference token."""
    return key.replace("~", "~0").replace("/", "~1")


def _load(body: bytes, what: str) -> object:
    try:
        return json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SecDataError(f"{what} is not JSON: {exc}") from exc


def read_company_tickers(body: bytes) -> tuple[TickerEntry, ...]:
    data = _load(body, "company_tickers.json")
    if not isinstance(data, dict) or not data:
        raise SecDataError("company_tickers.json is not a non-empty object")
    entries = []
    for key, entry in data.items():
        if not isinstance(entry, dict) or not {"cik_str", "ticker", "title"} <= set(
            entry
        ):
            raise SecDataError(f"entry {key!r} lacks cik_str, ticker, or title")
        entries.append(
            TickerEntry(
                ticker=str(entry["ticker"]),
                cik=pad_cik(entry["cik_str"]),
                title=str(entry["title"]),
                pointer=f"/{json_pointer_token(key)}",
            )
        )
    return tuple(entries)


def _date(value: object, where: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise SecDataError(f"{where}: {value!r} is not a date") from exc


def _datetime(value: object, where: str) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise SecDataError(f"{where}: {value!r} is not a timestamp") from exc
    if parsed.tzinfo is None:
        raise SecDataError(f"{where}: {value!r} has no time zone")
    return parsed


def read_filing_columns(columns: object, pointer: str) -> tuple[Filing, ...]:
    """Filings from SEC's column layout: one array per field, one index per filing."""
    if not isinstance(columns, dict) or not set(FILING_COLUMNS) <= set(columns):
        raise SecDataError(f"{pointer} lacks the columns {list(FILING_COLUMNS)}")
    arrays = [columns[name] for name in FILING_COLUMNS]
    if (
        not all(isinstance(array, list) for array in arrays)
        or len({len(array) for array in arrays}) != 1
    ):
        raise SecDataError(f"{pointer}'s columns are not arrays of one length")
    filings = []
    for index, row in enumerate(zip(*arrays, strict=True)):
        accession, filed, reported, accepted, form, document = row
        where = f"{pointer} index {index}"
        filing_date = _date(filed, where)
        if filing_date is None:
            raise SecDataError(f"{where} has no filing date")
        filings.append(
            Filing(
                accession=str(accession),
                form=str(form),
                filing_date=filing_date,
                report_date=_date(reported, where),
                accepted_at=_datetime(accepted, where),
                primary_document=str(document),
                columns=pointer,
                index=index,
            )
        )
    return tuple(filings)


def read_submissions(body: bytes) -> Registrant:
    data = _load(body, "the submissions file")
    if not isinstance(data, dict) or not {"cik", "name", "tickers", "filings"} <= set(
        data
    ):
        raise SecDataError("the submissions file lacks cik, name, tickers, or filings")
    filings = data["filings"]
    if not isinstance(filings, dict) or "recent" not in filings:
        raise SecDataError("the submissions file has no filings.recent")
    former = data.get("formerNames") or []
    if not isinstance(former, list):
        raise SecDataError("formerNames is not a list")
    older = filings.get("files") or []
    if not isinstance(older, list):
        raise SecDataError("filings.files is not a list")
    return Registrant(
        cik=pad_cik(data["cik"]),
        name=str(data["name"]),
        tickers=tuple(str(ticker) for ticker in data["tickers"]),
        former_names=tuple(
            FormerName(
                name=str(entry["name"]),
                valid_from=entry.get("from"),
                valid_to=entry.get("to"),
                pointer=f"/formerNames/{index}",
            )
            for index, entry in enumerate(former)
        ),
        filings=read_filing_columns(filings["recent"], "/filings/recent"),
        older_pages=tuple(str(page["name"]) for page in older),
    )


def read_submissions_page(body: bytes) -> tuple[Filing, ...]:
    """An older filings page: the same columns, at the top level."""
    return read_filing_columns(_load(body, "the filings page"), "")


def raw_document_name(primary_document: str) -> str:
    """The filed file itself: EDGAR's ``primaryDocument`` for an XML form can name
    its rendered view, such as ``xslFormNPORT-P_X01/primary_doc.xml``."""
    return primary_document.rsplit("/", 1)[-1]


def _local(element: etree._Element) -> str:
    return etree.QName(element).localname


def _child_text(element: etree._Element, name: str) -> str | None:
    for child in element:
        if isinstance(child.tag, str) and _local(child) == name:
            text = (child.text or "").strip()
            return text or None
    return None


def read_nport_holdings(body: bytes) -> HoldingsReport:
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    try:
        root = etree.fromstring(body, parser=parser)
    except etree.XMLSyntaxError as exc:
        raise SecDataError(f"the N-PORT document is not XML: {exc}") from exc
    if _local(root) != "edgarSubmission":
        raise SecDataError(f"the root element is {_local(root)!r}, not edgarSubmission")
    report_dates = [
        element.text
        for element in root.iter()
        if isinstance(element.tag, str) and _local(element) == "repPdDate"
    ]
    if len(report_dates) != 1:
        raise SecDataError(f"expected one repPdDate, found {len(report_dates)}")
    report_date = _date((report_dates[0] or "").strip(), "repPdDate")
    if report_date is None:
        raise SecDataError("repPdDate is empty")
    holdings = []
    positions = (
        element
        for element in root.iter()
        if isinstance(element.tag, str) and _local(element) == "invstOrSec"
    )
    for position, element in enumerate(positions, start=1):
        name = _child_text(element, "name")
        if name is None:
            raise SecDataError(f"holding {position} has no name")
        holdings.append(
            Holding(
                name=name,
                title=_child_text(element, "title"),
                asset_category=_child_text(element, "assetCat"),
                position=position,
            )
        )
    if not holdings:
        raise SecDataError("the N-PORT document lists no holdings")
    return HoldingsReport(report_date=report_date, holdings=tuple(holdings))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_sec_data.py -q`

Expected: `13 passed`.

- [ ] **Step 5: Write the live format probe**

Create `tests/integration/test_sec_formats_live.py`:

```python
"""SEC's live formats still match what the readers rely on; run with ``-m live``.

It needs EDGAR_IDENTITY, set outside Git, and sends at most eight requests through
the shared SEC client. It saves nothing: ``earnings-pipeline cohort fetch-sec`` saves
what a build reads. Run it with ``-rP`` to see what it read, including the fund's
name, which must be the SPDR Dow Jones Industrial Average ETF Trust before any
curated file names its CIK. It never runs by default.
"""

import os
from pathlib import Path

import pytest
from earnings_ingestion.sec.client import open_sec_client
from earnings_ingestion.sec.data import (
    raw_document_name,
    read_company_tickers,
    read_nport_holdings,
    read_submissions,
    read_submissions_page,
)
from earnings_ingestion.sec.urls import (
    COMPANY_TICKERS_URL,
    archive_url,
    submissions_page_url,
    submissions_url,
)

pytestmark = pytest.mark.live
REPO = Path(__file__).resolve().parents[2]
JSON = frozenset({"application/json"})
XML = frozenset({"application/xml", "text/xml"})
NPORT = frozenset({"NPORT-P", "NPORT-P/A"})
MAX_REQUESTS = 8

FUND_CIK = "0001041130"
"""The fund's CIK, a lead from planning that this check confirms by the fund's name."""
FUND_NAME = "Dow Jones Industrial Average"
COMPANY = ("AAPL", "0000320193", "Apple")
"""A ticker, its CIK, and a name the ticker list and submissions must agree on."""
HOLDINGS = range(25, 36)
"""The equity holdings a fund tracking the 30-stock average should report."""


def test_sec_formats_match_the_readers() -> None:
    if not os.environ.get("EDGAR_IDENTITY"):
        pytest.skip("set EDGAR_IDENTITY outside Git to run this check")
    ticker, cik, name = COMPANY
    with open_sec_client(REPO, max_requests=MAX_REQUESTS) as client:
        entries = read_company_tickers(client.fetch(COMPANY_TICKERS_URL, JSON).body)
        company = read_submissions(client.fetch(submissions_url(cik), JSON).body)
        fund = read_submissions(client.fetch(submissions_url(FUND_CIK), JSON).body)
        older = [
            filing
            for page in fund.older_pages[:1]
            for filing in read_submissions_page(
                client.fetch(submissions_page_url(page), JSON).body
            )
        ]
        reports = [f for f in fund.filings if f.form in NPORT]
        assert reports, "the fund's recent filings hold no N-PORT report"
        latest = max(reports, key=lambda f: (f.filing_date, f.accession))
        document = raw_document_name(latest.primary_document)
        holdings = read_nport_holdings(
            client.fetch(archive_url(FUND_CIK, latest.accession, document), XML).body
        )
        requests = client.throttle.count
    equities = [h for h in holdings.holdings if h.asset_category in (None, "EC")]
    print(f"requests: {requests}")
    print(f"ticker list: {len(entries)} entries")
    print(f"{ticker}: {company.cik} {company.name}; tickers {list(company.tickers)}")
    print(f"fund: {fund.cik} {fund.name}")
    print(
        f"fund former names: {[(n.name, n.valid_from, n.valid_to) for n in fund.former_names]}"
    )
    print(
        f"fund recent filings: {len(fund.filings)}, from"
        f" {min(f.filing_date for f in fund.filings)}; older pages:"
        f" {list(fund.older_pages)}; first older page: {len(older)} filings"
    )
    print(
        f"latest N-PORT: {latest.accession} {latest.form} filed {latest.filing_date},"
        f" accepted {latest.accepted_at}, primaryDocument {latest.primary_document}"
    )
    print(
        f"its report date {holdings.report_date}: {len(holdings.holdings)} holdings,"
        f" {len(equities)} equity; categories"
        f" {sorted({str(h.asset_category) for h in holdings.holdings})}"
    )
    assert [e.cik for e in entries if e.ticker == ticker] == [cik]
    assert company.cik == cik and ticker in company.tickers
    assert name.casefold() in company.name.casefold()
    assert fund.cik == FUND_CIK
    assert FUND_NAME.casefold() in fund.name.casefold(), (
        f"CIK {FUND_CIK} is {fund.name!r}"
    )
    assert holdings.report_date == latest.report_date
    assert len(equities) in HOLDINGS
    assert requests <= MAX_REQUESTS
```

Check that the default suite deselects it, and never run it with `-m live` here:

Run: `uv run --locked --all-packages pytest tests/integration/test_sec_formats_live.py -m "not live and not browser" -q`

Expected: `1 deselected`.

- [ ] **Step 6: Run the checks, and commit**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/sec/data.py packages/earnings-ingestion/tests/test_sec_data.py tests/integration/test_sec_formats_live.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `721 passed, 23 deselected`;
`All checks passed!` and `172 files already formatted`.

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/sec/data.py packages/earnings-ingestion/tests/test_sec_data.py tests/integration/test_sec_formats_live.py
git commit -m "feat(ingestion): read SEC's ticker list, submissions, and N-PORT holdings"
```

- [ ] **Step 7 (gate): Probe SEC's live formats**

Ask the user in chat, and wait for a clear yes. For example:

> Task 5's format probe sends at most eight requests to www.sec.gov and
> data.sec.gov through the shared SEC client, as `EDGAR_IDENTITY`:
>
> - the ticker list;
> - Apple's submissions and the DIA trust's submissions;
> - at most one older filings page;
> - one N-PORT document.
>
> It saves nothing. May I run it?

If the user declines, skip this step, and note it for the plan's markup. Task 17's
`fetch-sec` then meets SEC's formats first.

On a yes, run: `uv run --locked --all-packages pytest tests/integration/test_sec_formats_live.py -m live -rP -q`

Expected, a prediction that was not replayed: `1 passed`. The captured output then
shows:

- the request count, at most 8;
- Apple's CIK `0000320193` with its name and tickers;
- the fund's CIK and a name containing "Dow Jones Industrial Average";
- its former names;
- how far `filings.recent` reaches back, and its older pages;
- the latest N-PORT's accession, form, dates, and `primaryDocument`;
- that report's holdings count, equity count, and asset categories.

Read the output with the user. Stop and report, and never patch past it, if:

- the test fails with a `SecDataError`;
- the fund's name is not the SPDR Dow Jones Industrial Average ETF Trust;
- the equity holdings fall outside 25–35.

A reader fix changes the synthetic cohort too (P6-21), so it is a deviation for the
user to approve.

This check's exit is the passing test. It adds no file, so there is nothing to
commit.

---
### Task 6: The cohort records and canonical JSON

These are P §Data contracts' records, with what the build needs around them. They
are ingestion records, not core contracts, and they join ingestion schema version 1
(P6-5).

- **The universe.** `UniverseDefinition` is P's universe definition, plus
  `expected_member_count`.
- **Membership.**
  - `MembershipAssertion` is P's membership assertion: one per security and
    evidence item, with its `status`.
  - `MembershipInterval` is a derived, half-open effective interval.
- **Identity.** `IssuerMapping`, `IssuerCandidate`, and `Issuer` carry each security
  to its issuer and 10-character CIK, with the SEC citations behind them.
- **Review.** `Override` is a reviewed decision. `Finding` and `CohortReport` are
  the coverage and conflict report.
- **The whole.** `UniverseManifest` is the frozen cohort, and `LiveVerification` is
  P-VL's record.

Every record is strict and frozen. The validators refuse the shapes the spec rules
out:

- an interval on any assertion that is not `supported`;
- an issuer without its CIK;
- a candidate called confirmed without a listed ticker and a matched name;
- an override that sets any target but its kind's;
- a cutoff inside the window.

`digests.py` is the one serialization every cohort hash uses: canonical JSON, with
sorted keys, no whitespace, UTF-8 as itself, and ISO dates.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/__init__.py`
  (empty), `cohort/records.py`, and `cohort/digests.py`.
- Modify: `docs/data-dictionary.md` (appended, part 2 of 4), and
  `tests/contracts/test_data_dictionary.py` (replaced whole, block 2 of 3).
- Test (create): `packages/earnings-ingestion/tests/test_cohort_records.py` and
  `test_cohort_digests.py`.

**Interfaces:**

- Consumes:
  - Task 1's `Retrieval` and `SourceId`;
  - Task 4's `Cik`;
  - `earnings_core`'s `ArtifactRef`, `RightsStatus`, `IdPart`, `NonBlankStr`, and
    `Sha256Hex`.
- Produces:
  - In `cohort/records.py`, these enums:
    - `EvidenceClass`: `official`, `secondary`, `etf_proxy`, `user_supplied`;
    - `SourceRole`: `anchor`, `change`, `corroboration`, `check`;
    - `LocatorKind`: `text_span`, `json_pointer`;
    - `BoundTiming`: `before_open`, `after_close`, `unspecified`;
    - `BoundBasis`: `announced`, `anchor_snapshot`;
    - `AssertedAction`: `member_at`, `added`, `removed`;
    - `AssertionStatus`: `supported`, `conflicting`, `ambiguous`, `withheld`;
    - `ResolutionStatus`: `resolved`, `unresolved`, `conflicting`,
      `retained_unresolved`;
    - `ResolutionMethod`: `sec_ticker_and_name`, `override`;
    - `OverrideKind`: `reject_assertion`, `set_issuer`, `retain_unresolved`,
      `acknowledge`, `holding_alias`;
    - `FindingKind`: `missing_anchor`, `membership_conflict`,
      `membership_ambiguity`, `identity`, `member_count`, `difference`, `gap`,
      `withheld`, `superseded`.
  - In `cohort/records.py`, these models; `docs/data-dictionary.md` lists each
    one's fields:
    - `EvidenceLocator`, `Citation`, and `SourceRights`;
    - `CitedIdentity` and `SecurityRecord`;
    - `MembershipAssertion` and `MembershipInterval`, the latter with
      `contains(day)` and `overlaps(start, stop)`;
    - `IssuerCandidate`, `IssuerMapping`, and `Issuer`;
    - `OverrideCitation` and `Override`;
    - `Finding`, with the `holds_freeze` property;
    - `SnapshotReconciliation`, with the `agrees` property;
    - `CohortReport`, with the `blocking` property;
    - `UniverseDefinition`, `UniverseManifest`, `LiveCheck`, and
      `LiveVerification`.
  - `cohort/digests.py`: `canonical_json(value) -> bytes`, which dumps a model in
    JSON mode first, and `digest(value) -> str`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_cohort_records.py`:

```python
"""The cohort records refuse every shape their docstrings rule out."""

from datetime import UTC, date, datetime

import pytest
from earnings_core import RightsStatus
from earnings_ingestion.cohort.records import (
    AssertedAction,
    AssertionStatus,
    BoundBasis,
    BoundTiming,
    EvidenceLocator,
    Finding,
    FindingKind,
    IssuerCandidate,
    IssuerMapping,
    LocatorKind,
    MembershipAssertion,
    MembershipInterval,
    Override,
    OverrideCitation,
    OverrideKind,
    ResolutionMethod,
    ResolutionStatus,
    UniverseDefinition,
)
from pydantic import ValidationError

HASH = "a" * 64
SPAN = {
    "kind": LocatorKind.TEXT_SPAN,
    "canonicalization_version": "walker-1",
    "canonical_sha256": HASH,
    "start": 3,
    "end": 9,
    "cited_sha256": HASH,
}


def assertion(**changes) -> MembershipAssertion:
    fields = {
        "membership_assertion_id": "anchor:acme-common:member_at",
        "universe_id": "djia-test",
        "security_id": "acme-common",
        "issuer_id": None,
        "cik": None,
        "asserted_action": AssertedAction.MEMBER_AT,
        "asserted_date": date(2024, 6, 28),
        "asserted_timing": BoundTiming.UNSPECIFIED,
        "effective_from": date(2024, 6, 28),
        "effective_from_basis": BoundBasis.ANCHOR_SNAPSHOT,
        "effective_from_timing": BoundTiming.UNSPECIFIED,
        "effective_to": None,
        "effective_to_timing": None,
        "announcement_date": None,
        "source_snapshot_date": date(2024, 6, 28),
        "publication_date": date(2024, 6, 20),
        "publication_time": None,
        "retrieved_at": datetime(2026, 9, 27, tzinfo=UTC),
        "source_id": "synthetic-roster",
        "evidence_id": "anchor",
        "url": "https://roster.example/djia?rev=1",
        "evidence_locators": (EvidenceLocator(**SPAN),),
        "raw_content_hash": HASH,
        "rights_status": RightsStatus.REDISTRIBUTABLE,
        "status": AssertionStatus.SUPPORTED,
        "resolved_by": None,
    }
    return MembershipAssertion(**(fields | changes))


def test_a_text_span_locator_needs_offsets_and_a_text_hash() -> None:
    assert EvidenceLocator(**SPAN).end == 9
    with pytest.raises(ValidationError, match="start < end"):
        EvidenceLocator(**(SPAN | {"end": 3}))
    with pytest.raises(ValidationError, match="offsets"):
        EvidenceLocator(**(SPAN | {"canonical_sha256": None}))


def test_a_json_pointer_locator_has_only_its_pointer() -> None:
    whole = EvidenceLocator(
        kind=LocatorKind.JSON_POINTER, pointer="", cited_sha256=HASH
    )
    assert whole.pointer == ""
    with pytest.raises(ValidationError, match="starts with"):
        EvidenceLocator(kind=LocatorKind.JSON_POINTER, pointer="a", cited_sha256=HASH)
    with pytest.raises(ValidationError, match="nothing else"):
        EvidenceLocator(
            kind=LocatorKind.JSON_POINTER, pointer="/0", start=1, cited_sha256=HASH
        )


def test_only_a_supported_assertion_carries_an_interval() -> None:
    assert assertion().effective_to is None
    with pytest.raises(ValidationError, match="only a supported"):
        assertion(status=AssertionStatus.CONFLICTING)
    held = assertion(
        status=AssertionStatus.WITHHELD,
        effective_from=None,
        effective_from_basis=None,
        effective_from_timing=None,
    )
    assert held.effective_from is None


def test_an_interval_ends_after_it_starts_and_ends_with_its_timing() -> None:
    with pytest.raises(ValidationError, match="after effective_from"):
        assertion(
            effective_to=date(2024, 6, 28), effective_to_timing=BoundTiming.BEFORE_OPEN
        )
    with pytest.raises(ValidationError, match="come together"):
        assertion(effective_to=date(2024, 11, 8))


def test_an_issuer_and_its_cik_come_together() -> None:
    assert assertion(issuer_id="cik-0009990001", cik="0009990001").cik == "0009990001"
    with pytest.raises(ValidationError, match="come together"):
        assertion(issuer_id="cik-0009990001")
    with pytest.raises(ValidationError):
        assertion(issuer_id="cik-9990001", cik="9990001")


def test_intervals_are_half_open() -> None:
    interval = MembershipInterval(
        security_id="acme-common",
        effective_from=date(2024, 11, 8),
        effective_from_basis=BoundBasis.ANNOUNCED,
        effective_from_timing=BoundTiming.BEFORE_OPEN,
        effective_to=date(2025, 3, 3),
        effective_to_timing=BoundTiming.BEFORE_OPEN,
        assertion_ids=("a",),
    )
    assert interval.contains(date(2024, 11, 8))
    assert not interval.contains(date(2025, 3, 3))
    assert interval.overlaps(date(2025, 3, 2), date(2025, 3, 3))
    assert not interval.overlaps(date(2025, 3, 3), date(2025, 4, 1))


def test_a_candidate_is_confirmed_exactly_by_a_listed_ticker_and_a_name() -> None:
    fields = {
        "evidence_id": "anchor",
        "cited_name": "Acme Industrial",
        "ticker": "ACME",
        "cik": "0009990001",
        "sec_name": "Acme Industrial Corp",
        "ticker_listed": True,
        "matched_name": "Acme Industrial Corp",
        "confirmed": True,
        "citations": (),
    }
    assert IssuerCandidate(**fields).confirmed
    with pytest.raises(ValidationError, match="confirmed means"):
        IssuerCandidate(**(fields | {"matched_name": None}))


def test_a_mapping_is_resolved_exactly_when_it_has_an_issuer() -> None:
    resolved = IssuerMapping(
        security_id="acme-common",
        status=ResolutionStatus.RESOLVED,
        method=ResolutionMethod.SEC_TICKER_AND_NAME,
        issuer_id="cik-0009990001",
        cik="0009990001",
        candidates=(),
        override_id=None,
        reason=None,
    )
    assert resolved.cik == "0009990001"
    with pytest.raises(ValidationError, match="only a resolved"):
        IssuerMapping(
            **(resolved.model_dump() | {"status": ResolutionStatus.UNRESOLVED})
        )
    with pytest.raises(ValidationError, match="override_id"):
        IssuerMapping(**(resolved.model_dump() | {"override_id": "x"}))
    with pytest.raises(ValidationError, match="reason"):
        IssuerMapping(
            security_id="acme-common",
            status=ResolutionStatus.RETAINED_UNRESOLVED,
            method=None,
            issuer_id=None,
            cik=None,
            candidates=(),
            override_id="keep-acme",
            reason=None,
        )


def test_an_override_sets_exactly_its_kinds_targets() -> None:
    common = {
        "citations": (OverrideCitation(source_id="sec-edgar", url="https://x.test/"),),
        "rationale": "Reviewed.",
        "reviewer": "Reviewer Name",
        "recorded_on": date(2026, 9, 28),
        "effective_from": date(2024, 7, 1),
    }
    issuer = Override(
        override_id="acme-issuer",
        kind=OverrideKind.SET_ISSUER,
        security_id="acme-common",
        cik="0009990001",
        **common,
    )
    assert issuer.cik == "0009990001"
    with pytest.raises(ValidationError, match="sets exactly"):
        Override(
            override_id="acme-issuer",
            kind=OverrideKind.SET_ISSUER,
            security_id="acme-common",
            **common,
        )
    with pytest.raises(ValidationError, match="cites its evidence"):
        Override(**(issuer.model_dump() | {"citations": ()}))
    with pytest.raises(ValidationError, match="after effective_from"):
        Override(**(issuer.model_dump() | {"effective_to": date(2024, 7, 1)}))


def test_a_blocking_finding_holds_the_freeze_until_resolved() -> None:
    finding = Finding(
        finding_id="difference:x",
        kind=FindingKind.DIFFERENCE,
        blocking=True,
        security_id=None,
        detail="A snapshot disagrees.",
        evidence_ids=("x",),
        digest=HASH,
        resolved_by=(),
    )
    assert finding.holds_freeze
    assert not finding.model_copy(update={"resolved_by": ("ack-x",)}).holds_freeze


def test_the_cutoff_cannot_fall_inside_the_window() -> None:
    fields = {
        "universe_id": "djia-test",
        "universe_version": 1,
        "universe_name": "djia",
        "period_end_start": date(2024, 7, 1),
        "period_end_stop": date(2026, 7, 1),
        "public_information_cutoff": date(2026, 9, 22),
        "membership_reference": "first_publication_time",
        "expected_member_count": 30,
        "source_register_version": HASH,
        "selection_policy_version": "djia-pilot/1",
        "content_hash": HASH,
        "created_at": datetime(2026, 9, 28, tzinfo=UTC),
    }
    assert UniverseDefinition(**fields).universe_version == 1
    with pytest.raises(ValidationError, match="inside the window"):
        UniverseDefinition(
            **(fields | {"public_information_cutoff": date(2026, 6, 30)})
        )
```

Create `packages/earnings-ingestion/tests/test_cohort_digests.py`:

```python
"""Canonical JSON: the one serialization every cohort hash is computed over."""

from datetime import UTC, date, datetime

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.digests import canonical_json, digest
from earnings_ingestion.cohort.records import (
    AssertedAction,
    EvidenceLocator,
    LocatorKind,
)


def test_keys_are_sorted_without_whitespace_and_text_stays_utf8() -> None:
    value = {"b": [1, 2], "a": "Soci" + chr(0xE9) + "t" + chr(0xE9)}
    expected = '{"a":"Soci' + chr(0xE9) + "t" + chr(0xE9) + '","b":[1,2]}'
    assert canonical_json(value) == expected.encode("utf-8")
    assert digest(value) == sha256_hex(expected.encode("utf-8"))


def test_dates_and_enums_are_written_as_iso_text_and_values() -> None:
    value = {
        "on": date(2024, 11, 8),
        "at": datetime(2024, 11, 1, 21, 0, tzinfo=UTC),
        "action": AssertedAction.ADDED,
    }
    assert canonical_json(value) == (
        b'{"action":"added","at":"2024-11-01T21:00:00+00:00","on":"2024-11-08"}'
    )


def test_a_model_is_dumped_in_json_mode_first() -> None:
    locator = EvidenceLocator(
        kind=LocatorKind.JSON_POINTER, pointer="/0", cited_sha256="a" * 64
    )
    assert canonical_json(locator) == canonical_json(locator.model_dump(mode="json"))


def test_a_value_without_a_json_form_is_refused() -> None:
    with pytest.raises(TypeError, match="no canonical JSON form"):
        canonical_json({"x": {1, 2}})
```

Replace `tests/contracts/test_data_dictionary.py` with:

```python
"""docs/data-dictionary.md documents every field and value of the core contracts
and of the ingestion records: the canonicalizer's, the capture's, layout-1's, the
retrieval metadata, and the cohort's records.

AGENTS.md §191: document public interfaces and update the data dictionary in the
same change. A contract that gains, loses, or renames a field fails here.
"""

import re
from enum import StrEnum
from pathlib import Path

import earnings_core as core
import earnings_ingestion.canonical as ingestion
import pytest
from earnings_ingestion import browser, layout
from earnings_ingestion.cohort import records as cohort
from earnings_ingestion.fetch import records as fetch
from pydantic import BaseModel

DICTIONARY = Path(__file__).resolve().parents[2] / "docs" / "data-dictionary.md"
MODELS = [
    core.TextSpan,
    core.ArtifactRef,
    core.CanonicalDocument,
    core.TableCellContext,
    core.DocumentElement,
    core.SpanLocator,
    core.TextChunk,
    core.SpanCandidate,
    core.VerifiedSpan,
    core.OverlayMask,
    core.MaskedDocument,
    core.Rejection,
    ingestion.CanonicalizationManifest,
    ingestion.CanonicalizationFailure,
    ingestion.Canonicalized,
    browser.RenderedCapture,
    browser.BlockedRequest,
    browser.LayoutMetadata,
    browser.LayoutBlock,
    browser.LayoutRun,
    browser.LayoutTable,
    browser.LayoutRow,
    browser.LayoutCell,
    layout.AlignmentFailure,
    layout.LayoutExtraction,
    fetch.Retrieval,
    cohort.EvidenceLocator,
    cohort.Citation,
    cohort.SourceRights,
    cohort.CitedIdentity,
    cohort.SecurityRecord,
    cohort.MembershipAssertion,
    cohort.MembershipInterval,
    cohort.IssuerCandidate,
    cohort.IssuerMapping,
    cohort.Issuer,
    cohort.OverrideCitation,
    cohort.Override,
    cohort.Finding,
    cohort.SnapshotReconciliation,
    cohort.CohortReport,
    cohort.UniverseDefinition,
    cohort.UniverseManifest,
    cohort.LiveCheck,
    cohort.LiveVerification,
]
ENUMS = [
    core.RightsStatus,
    core.ElementType,
    core.TextOrigin,
    core.MaskCategory,
    core.RejectionReason,
    ingestion.FailureReason,
    browser.CaptureStatus,
    browser.CaptureReason,
    fetch.RetrievalMethod,
    cohort.EvidenceClass,
    cohort.SourceRole,
    cohort.LocatorKind,
    cohort.BoundTiming,
    cohort.BoundBasis,
    cohort.AssertedAction,
    cohort.AssertionStatus,
    cohort.ResolutionStatus,
    cohort.ResolutionMethod,
    cohort.OverrideKind,
    cohort.FindingKind,
]


def documented(name: str) -> set[str]:
    """The first-column code spans of the table under the heading for ``name``."""
    text = DICTIONARY.read_text(encoding="utf-8")
    heading = f"### `{name}`\n"
    assert heading in text, f"docs/data-dictionary.md has no section for {name}"
    section = text.split(heading, 1)[1].split("\n#", 1)[0]
    return set(re.findall(r"^\| `([^`]+)` \|", section, flags=re.MULTILINE))


@pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__name__)
def test_every_field_is_documented(model: type[BaseModel]) -> None:
    assert documented(model.__name__) == set(model.model_fields)


@pytest.mark.parametrize("enum", ENUMS, ids=lambda enum: enum.__name__)
def test_every_value_is_documented(enum: type[StrEnum]) -> None:
    assert documented(enum.__name__) == {member.value for member in enum}


def test_the_documented_versions_are_the_packages() -> None:
    text = DICTIONARY.read_text(encoding="utf-8")
    assert f"schema version {core.SCHEMA_VERSION}\n" in text
    assert f'`"{core.VALIDATOR_VERSION}"` (`earnings_core.VALIDATOR_VERSION`)' in text
    assert (
        f"## earnings-ingestion records, schema version"
        f" {ingestion.INGESTION_SCHEMA_VERSION}\n" in text
    )
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py tests/contracts/test_data_dictionary.py 2`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_records.py packages/earnings-ingestion/tests/test_cohort_digests.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL. Collection stops in all three files with
`No module named 'earnings_ingestion.cohort'`, and pytest reports `3 errors`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/__init__.py`:

```python
```

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/records.py`:

```python
"""The point-in-time DJIA cohort's records (Stage 4; P §Data contracts).

- **The universe.** ``UniverseDefinition`` is P's universe definition.
- **Membership.** ``MembershipAssertion`` is P's membership assertion, one per
  security and evidence item, and ``MembershipInterval`` is a derived effective
  interval.
- **Identity.** ``IssuerMapping`` and ``Issuer`` carry each security to its issuer and
  a 10-character CIK.
- **The whole.** ``UniverseManifest`` is the frozen cohort, with its
  ``CohortReport``.

These are ingestion records, not core contracts, and they join ingestion schema
version 1. Committed records carry facts and citations, never source wording: a
citation is a URL, the raw bytes' hash, and locators that hash the cited text (the
user's decision, 2026-09-26). docs/data-dictionary.md documents every field and value.
"""

from datetime import date
from enum import StrEnum
from typing import Literal, Self

from earnings_core import ArtifactRef, RightsStatus
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

from earnings_ingestion.canonical.records import IngestionRecord
from earnings_ingestion.fetch.records import Retrieval, SourceId
from earnings_ingestion.sec.identifiers import Cik


class _Part(BaseModel):
    """A nested part of a cohort record: immutable, closed, strictly typed."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class EvidenceClass(StrEnum):
    """What kind of source an item comes from (P §Membership evidence)."""

    OFFICIAL = "official"
    """The index provider's own statement."""
    SECONDARY = "secondary"
    """A dated third-party roster, labeled as secondary evidence."""
    ETF_PROXY = "etf_proxy"
    """A tracking fund's holdings: corroboration only, never the roster."""
    USER_SUPPLIED = "user_supplied"
    """A list the user supplied: a check, never evidence."""


class SourceRole(StrEnum):
    """What a registered source may be used for."""

    ANCHOR = "anchor"
    """The dated snapshot that the intervals start from."""
    CHANGE = "change"
    """Addition and removal announcements."""
    CORROBORATION = "corroboration"
    """A dated snapshot that the reconstruction must reproduce."""
    CHECK = "check"
    """A snapshot compared and reported, never holding the freeze."""


class LocatorKind(StrEnum):
    TEXT_SPAN = "text_span"
    """Half-open code-point offsets into an HTML artifact's canonical text."""
    JSON_POINTER = "json_pointer"
    """An RFC 6901 pointer into a JSON artifact."""


class BoundTiming(StrEnum):
    """When on its date a change takes effect, as the evidence states it."""

    BEFORE_OPEN = "before_open"
    AFTER_CLOSE = "after_close"
    UNSPECIFIED = "unspecified"


class BoundBasis(StrEnum):
    """What establishes an interval's start."""

    ANNOUNCED = "announced"
    """An official effective date."""
    ANCHOR_SNAPSHOT = "anchor_snapshot"
    """The anchor's date: a lower bound, never an entry date."""


class AssertedAction(StrEnum):
    """What one evidence item says about one security."""

    MEMBER_AT = "member_at"
    """A snapshot lists it as a member on the snapshot's date."""
    ADDED = "added"
    REMOVED = "removed"


class AssertionStatus(StrEnum):
    """An assertion's standing (plan 6, P6-6)."""

    SUPPORTED = "supported"
    """Consistent with the security's other evidence, and part of an interval."""
    CONFLICTING = "conflicting"
    """The security's evidence does not form one consistent sequence."""
    AMBIGUOUS = "ambiguous"
    """An addition and a removal of the security share an effective date."""
    WITHHELD = "withheld"
    """First published after the cutoff: kept, never applied (P-C4)."""


class ResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    """No SEC candidate is confirmed."""
    CONFLICTING = "conflicting"
    """More than one CIK is confirmed."""
    RETAINED_UNRESOLVED = "retained_unresolved"
    """A reviewer kept it unresolved and excluded it, with a reason."""


class ResolutionMethod(StrEnum):
    SEC_TICKER_AND_NAME = "sec_ticker_and_name"
    """SEC's ticker list proposed the CIK, and SEC's record for it lists the cited
    ticker under a name that covers the cited name (P6-8)."""
    OVERRIDE = "override"


class OverrideKind(StrEnum):
    REJECT_ASSERTION = "reject_assertion"
    """Set aside one conflicting or ambiguous assertion; it stays, marked."""
    SET_ISSUER = "set_issuer"
    """Name a security's CIK."""
    RETAIN_UNRESOLVED = "retain_unresolved"
    """Keep a security unresolved, excluded from the candidate issuers."""
    ACKNOWLEDGE = "acknowledge"
    """Accept one reviewed finding, bound to its digest."""
    HOLDING_ALIAS = "holding_alias"
    """Match a fund holding's name to a security."""


class FindingKind(StrEnum):
    MISSING_ANCHOR = "missing_anchor"
    MEMBERSHIP_CONFLICT = "membership_conflict"
    MEMBERSHIP_AMBIGUITY = "membership_ambiguity"
    IDENTITY = "identity"
    """An in-scope security without exactly one confirmed CIK."""
    MEMBER_COUNT = "member_count"
    """The reconstructed roster's size differs from the expected count."""
    DIFFERENCE = "difference"
    """A snapshot disagrees with the reconstruction on its date."""
    GAP = "gap"
    """A calendar quarter with no corroborating snapshot."""
    WITHHELD = "withheld"
    SUPERSEDED = "superseded"
    """A fund filing replaced by a later filing for the same report date."""


class EvidenceLocator(_Part):
    """Where cited evidence sits in an artifact, and the hash of what it says."""

    kind: LocatorKind
    canonicalization_version: IdPart | None = None
    canonical_sha256: Sha256Hex | None = None
    start: NonNegativeInt | None = None
    end: NonNegativeInt | None = None
    pointer: str | None = None
    cited_sha256: Sha256Hex

    @model_validator(mode="after")
    def _shape(self) -> Self:
        text = (self.canonicalization_version, self.canonical_sha256, self.start)
        if self.kind is LocatorKind.TEXT_SPAN:
            if None in (*text, self.end) or self.pointer is not None:
                raise ValueError("a text span has a version, a text hash, and offsets")
            if self.end <= self.start:
                raise ValueError("a text span needs start < end")
        elif self.pointer is None or any(v is not None for v in (*text, self.end)):
            raise ValueError("a JSON pointer locator has a pointer and nothing else")
        elif self.pointer and not self.pointer.startswith("/"):
            raise ValueError("a JSON pointer is empty or starts with '/'")
        return self


class Citation(_Part):
    """Evidence in one stored artifact: its source, bytes, and the places in it."""

    source_id: SourceId
    url: NonBlankStr
    artifact: ArtifactRef
    retrieved_at: AwareDatetime
    locators: tuple[EvidenceLocator, ...]


class SourceRights(_Part):
    """A source's class and rights, copied from its register entry."""

    source_id: SourceId
    evidence_class: EvidenceClass | None
    rights_status: RightsStatus
    rights_basis: NonBlankStr


class CitedIdentity(_Part):
    """A security's name and ticker as one evidence row states them, on its date."""

    evidence_id: IdPart
    observed_on: date
    name: NonBlankStr
    ticker: NonBlankStr


class SecurityRecord(_Part):
    """One security, with every name and ticker the evidence gives it, by date."""

    security_id: IdPart
    identities: tuple[CitedIdentity, ...]


class MembershipAssertion(_Part):
    """One evidence item's statement about one security (P §Data contracts).

    ``effective_from`` and ``effective_to`` are the interval the item supports; they
    are null unless ``status`` is ``supported``.
    """

    membership_assertion_id: IdPart
    universe_id: IdPart
    security_id: IdPart
    issuer_id: IdPart | None
    cik: Cik | None
    asserted_action: AssertedAction
    asserted_date: date
    asserted_timing: BoundTiming
    effective_from: date | None
    effective_from_basis: BoundBasis | None
    effective_from_timing: BoundTiming | None
    effective_to: date | None
    effective_to_timing: BoundTiming | None
    announcement_date: date | None
    source_snapshot_date: date | None
    publication_date: date
    publication_time: AwareDatetime | None
    retrieved_at: AwareDatetime
    source_id: SourceId
    evidence_id: IdPart
    url: NonBlankStr
    evidence_locators: tuple[EvidenceLocator, ...]
    raw_content_hash: Sha256Hex
    rights_status: RightsStatus
    status: AssertionStatus
    resolved_by: IdPart | None

    @model_validator(mode="after")
    def _interval(self) -> Self:
        start = (
            self.effective_from,
            self.effective_from_basis,
            self.effective_from_timing,
        )
        if self.status is AssertionStatus.SUPPORTED:
            if None in start:
                raise ValueError("a supported assertion has its interval's start")
            if self.effective_to is not None and self.effective_to <= start[0]:
                raise ValueError("effective_to must be after effective_from")
            if (self.effective_to is None) != (self.effective_to_timing is None):
                raise ValueError("effective_to and its timing come together")
        elif any(v is not None for v in (*start, self.effective_to)):
            raise ValueError("only a supported assertion carries an interval")
        if (self.issuer_id is None) != (self.cik is None):
            raise ValueError("issuer_id and cik come together")
        return self


class MembershipInterval(_Part):
    """A derived effective interval, ``[effective_from, effective_to)``."""

    security_id: IdPart
    effective_from: date
    effective_from_basis: BoundBasis
    effective_from_timing: BoundTiming
    effective_to: date | None
    effective_to_timing: BoundTiming | None
    assertion_ids: tuple[IdPart, ...]

    def contains(self, day: date) -> bool:
        """Membership on ``day`` at day precision; bound timings decide nothing here."""
        return self.effective_from <= day and (
            self.effective_to is None or day < self.effective_to
        )

    def overlaps(self, start: date, stop: date) -> bool:
        """True if the interval meets ``[start, stop)``."""
        return self.effective_from < stop and (
            self.effective_to is None or self.effective_to > start
        )


class IssuerCandidate(_Part):
    """A CIK that SEC's ticker list proposed for one cited ticker, and its check."""

    evidence_id: IdPart
    cited_name: NonBlankStr
    ticker: NonBlankStr
    cik: Cik
    sec_name: NonBlankStr
    ticker_listed: bool
    matched_name: str | None
    confirmed: bool
    citations: tuple[Citation, ...]

    @model_validator(mode="after")
    def _confirmed(self) -> Self:
        if self.confirmed != (self.ticker_listed and self.matched_name is not None):
            raise ValueError("confirmed means the ticker is listed and a name matched")
        return self


class IssuerMapping(_Part):
    """One security's issuer and CIK, or why it has none."""

    security_id: IdPart
    status: ResolutionStatus
    method: ResolutionMethod | None
    issuer_id: IdPart | None
    cik: Cik | None
    candidates: tuple[IssuerCandidate, ...]
    override_id: IdPart | None
    reason: str | None

    @model_validator(mode="after")
    def _resolved(self) -> Self:
        resolved = self.status is ResolutionStatus.RESOLVED
        fields = (self.method, self.issuer_id, self.cik)
        if resolved and None in fields:
            raise ValueError("a resolved mapping has a method, an issuer, and a CIK")
        if not resolved and any(v is not None for v in fields):
            raise ValueError("only a resolved mapping has an issuer and a CIK")
        by_override = self.method is ResolutionMethod.OVERRIDE or (
            self.status is ResolutionStatus.RETAINED_UNRESOLVED
        )
        if by_override != (self.override_id is not None):
            raise ValueError("an override_id is recorded exactly when one decided")
        if self.status is ResolutionStatus.RETAINED_UNRESOLVED and not self.reason:
            raise ValueError("a retained mapping records its reason")
        return self


class Issuer(_Part):
    """The derived issuer view: one row per CIK, however many securities it has."""

    issuer_id: IdPart
    cik: Cik
    sec_name: NonBlankStr
    former_names: tuple[str, ...]
    security_ids: tuple[IdPart, ...]


class OverrideCitation(_Part):
    """Evidence an override relies on; an artifact and locator when one is stored."""

    source_id: NonBlankStr
    url: NonBlankStr
    artifact_sha256: Sha256Hex | None = None
    locator: EvidenceLocator | None = None

    @model_validator(mode="after")
    def _artifact(self) -> Self:
        if self.locator is not None and self.artifact_sha256 is None:
            raise ValueError("a locator needs the artifact it points into")
        return self


_TARGETS = {
    OverrideKind.REJECT_ASSERTION: ("membership_assertion_id",),
    OverrideKind.SET_ISSUER: ("security_id", "cik"),
    OverrideKind.RETAIN_UNRESOLVED: ("security_id",),
    OverrideKind.ACKNOWLEDGE: ("finding_id", "finding_digest"),
    OverrideKind.HOLDING_ALIAS: ("security_id", "holding_name"),
}
_TARGET_FIELDS = sorted({name for names in _TARGETS.values() for name in names})


class Override(_Part):
    """A reviewed manual decision: evidence, rationale, reviewer, and effective
    dates (P §Issuer resolution). Never a parser branch."""

    override_id: IdPart
    kind: OverrideKind
    membership_assertion_id: IdPart | None = None
    security_id: IdPart | None = None
    cik: Cik | None = None
    finding_id: IdPart | None = None
    finding_digest: Sha256Hex | None = None
    holding_name: NonBlankStr | None = None
    citations: tuple[OverrideCitation, ...]
    rationale: NonBlankStr
    reviewer: NonBlankStr
    recorded_on: date
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def _targets(self) -> Self:
        needs = _TARGETS[self.kind]
        present = {name for name in _TARGET_FIELDS if getattr(self, name) is not None}
        if present != set(needs):
            raise ValueError(f"a {self.kind} override sets exactly {list(needs)}")
        if self.kind is OverrideKind.SET_ISSUER and not self.citations:
            raise ValueError("a set_issuer override cites its evidence")
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self


class Finding(_Part):
    """One item of the coverage and conflict report."""

    finding_id: IdPart
    kind: FindingKind
    blocking: bool
    security_id: IdPart | None
    detail: NonBlankStr
    evidence_ids: tuple[str, ...]
    digest: Sha256Hex
    """SHA-256 of what the finding says, to which an acknowledgement is bound."""
    resolved_by: tuple[IdPart, ...]

    @property
    def holds_freeze(self) -> bool:
        return self.blocking and not self.resolved_by


class SnapshotReconciliation(_Part):
    """A dated snapshot compared with the reconstructed roster on its date."""

    snapshot_id: IdPart
    source_id: SourceId
    evidence_class: EvidenceClass
    as_of: date
    published_on: date
    withheld: bool
    matched: tuple[IdPart, ...]
    reconstructed_only: tuple[IdPart, ...]
    snapshot_only: tuple[IdPart, ...]
    unmatched: tuple[str, ...]
    citation: Citation | None

    @property
    def agrees(self) -> bool:
        return not (self.reconstructed_only or self.snapshot_only or self.unmatched)


class CohortReport(_Part):
    """The coverage and conflict report (P-A4)."""

    universe_id: IdPart
    anchor_evidence_id: IdPart | None
    limitations: tuple[str, ...]
    findings: tuple[Finding, ...]
    reconciliations: tuple[SnapshotReconciliation, ...]

    @property
    def blocking(self) -> tuple[Finding, ...]:
        """The findings that hold the freeze."""
        return tuple(finding for finding in self.findings if finding.holds_freeze)


class UniverseDefinition(_Part):
    """P §Data contracts, universe definition."""

    universe_id: IdPart
    universe_version: PositiveInt
    universe_name: IdPart
    period_end_start: date
    period_end_stop: date
    public_information_cutoff: date
    membership_reference: Literal["first_publication_time"]
    expected_member_count: PositiveInt
    source_register_version: Sha256Hex
    selection_policy_version: NonBlankStr
    content_hash: Sha256Hex
    created_at: AwareDatetime

    @model_validator(mode="after")
    def _window(self) -> Self:
        if not self.period_end_start < self.period_end_stop:
            raise ValueError("the window is empty")
        if self.public_information_cutoff < self.period_end_stop:
            raise ValueError("the cutoff falls inside the window")
        return self


class UniverseManifest(IngestionRecord):
    """The frozen cohort: everything Stage 5 joins against, with its report."""

    definition: UniverseDefinition
    sources: tuple[SourceRights, ...]
    securities: tuple[SecurityRecord, ...]
    assertions: tuple[MembershipAssertion, ...]
    intervals: tuple[MembershipInterval, ...]
    mappings: tuple[IssuerMapping, ...]
    issuers: tuple[Issuer, ...]
    candidate_issuer_ids: tuple[IdPart, ...]
    overrides: tuple[Override, ...]
    report: CohortReport


class LiveCheck(_Part):
    """One request of the opt-in live verification, and what it found."""

    source_id: SourceId
    purpose: Literal["terms", "evidence"]
    url: NonBlankStr
    outcome: Literal["unchanged", "changed", "refused", "failed"]
    detail: NonBlankStr
    retrieval: Retrieval | None


class LiveVerification(IngestionRecord):
    """The opt-in live verification's result (P-VL)."""

    checked_at: AwareDatetime
    checks: tuple[LiveCheck, ...]
    build_problems: tuple[str, ...]
    rebuilt_content_hash: Sha256Hex | None
    frozen_content_hash: Sha256Hex | None
    blocking_finding_ids: tuple[IdPart, ...]
```

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/digests.py`:

```python
"""Canonical JSON and its SHA-256, the one serialization every cohort hash uses.

Keys are sorted, separators carry no whitespace, and non-ASCII characters are
written as themselves in UTF-8. Dates and datetimes are ISO 8601 strings. A hash
computed here is reproducible from the committed values alone.
"""

import json
from datetime import date

from earnings_core import sha256_hex
from pydantic import BaseModel


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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_records.py packages/earnings-ingestion/tests/test_cohort_digests.py -q`

Expected: `15 passed`.

- [ ] **Step 5: Document the records**

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: FAIL: `30 failed, 36 passed`. The dictionary has no section for
the 19 models and 11 enums.

Append to `docs/data-dictionary.md`:

```markdown

## earnings-ingestion cohort records, schema version 1

- **Packages.** In `packages/earnings-ingestion` (Stage 4, plan 6):
  - `earnings_ingestion.sec`: the shared SEC client and SEC's record readers;
  - `earnings_ingestion.cohort`: the point-in-time DJIA cohort.
- **Schema version.** These records join ingestion schema version `1`, since no
  earlier record's fields changed. `UniverseManifest` and `LiveVerification` carry
  it as `schema_version`; the nested parts do not.
- **Facts and citations only.** A committed cohort record or curated file carries
  facts, URLs, locators, and hashes, and never a source's wording (the user's
  decision, 2026-09-26). The saved artifacts stay local.
- **Canonical JSON.** Every cohort hash is SHA-256 over canonical JSON
  (`earnings_ingestion.cohort.digests`): sorted keys, separators without whitespace,
  UTF-8 with non-ASCII characters written as themselves, and dates in ISO 8601.

### `EvidenceClass`

What kind of source an item comes from (P §Membership evidence and source rights).

| Value | Meaning |
| --- | --- |
| `official` | The index provider's own statement |
| `secondary` | A dated third-party roster, labeled as secondary evidence |
| `etf_proxy` | A tracking fund's holdings: corroboration only, never the roster |
| `user_supplied` | A list the user supplied: a check, never evidence |

### `SourceRole`

| Value | Meaning |
| --- | --- |
| `anchor` | The dated snapshot the intervals start from |
| `change` | Addition and removal announcements |
| `corroboration` | A dated snapshot the reconstruction must reproduce |
| `check` | A snapshot compared and reported, never holding the freeze |

### `LocatorKind`

| Value | Meaning |
| --- | --- |
| `text_span` | Half-open code-point offsets into an HTML artifact's walker-1 canonical text |
| `json_pointer` | An RFC 6901 pointer into a JSON artifact |

### `BoundTiming`

When on its date a change takes effect, as the evidence states it.

| Value | Meaning |
| --- | --- |
| `before_open` | Before the open of trading on the date |
| `after_close` | After the close of trading on the date |
| `unspecified` | The evidence gives no time of day; always the anchor's timing |

### `BoundBasis`

| Value | Meaning |
| --- | --- |
| `announced` | An official effective date |
| `anchor_snapshot` | The anchor's date: a lower bound on the start, never an entry date |

### `AssertedAction`

| Value | Meaning |
| --- | --- |
| `member_at` | The anchor lists the security as a member on its date |
| `added` | A change adds the security |
| `removed` | A change removes the security |

### `AssertionStatus`

| Value | Meaning |
| --- | --- |
| `supported` | Consistent with the security's other evidence, and part of an interval |
| `conflicting` | The security's evidence does not form one alternating sequence after the anchor; holds the freeze until a reviewer rejects the wrong assertion |
| `ambiguous` | An addition and a removal of the security share an effective date; holds the freeze the same way |
| `withheld` | First published after the cutoff: kept, never applied (P-C4) |

### `ResolutionStatus`

| Value | Meaning |
| --- | --- |
| `resolved` | One CIK, confirmed by SEC's records or named by an override |
| `unresolved` | No candidate confirmed |
| `conflicting` | More than one CIK confirmed |
| `retained_unresolved` | A reviewer kept it unresolved and excluded it, with a reason |

### `ResolutionMethod`

| Value | Meaning |
| --- | --- |
| `sec_ticker_and_name` | SEC's ticker list proposed the CIK, and SEC's record for it lists the cited ticker under a name, current or former, that covers the cited name |
| `override` | A `set_issuer` override named it |

### `OverrideKind`

| Value | Meaning |
| --- | --- |
| `reject_assertion` | Set aside one conflicting or ambiguous assertion; it stays in the manifest, marked |
| `set_issuer` | Name a security's CIK, citing the evidence |
| `retain_unresolved` | Keep a security unresolved and exclude it from the candidate issuers |
| `acknowledge` | Accept one `member_count` or `difference` finding, bound to its digest |
| `holding_alias` | Match a fund holding's name to a security |

### `FindingKind`

| Value | Meaning |
| --- | --- |
| `missing_anchor` | No usable anchor; blocking, and no override resolves it |
| `membership_conflict` | A security's evidence conflicts; blocking until assertions are rejected |
| `membership_ambiguity` | A security is added and removed on one date; blocking until an assertion is rejected |
| `identity` | An in-scope security without exactly one confirmed CIK; blocking until `set_issuer` or `retain_unresolved` decides it |
| `member_count` | The roster's size differs from the expected count on a date; blocking until acknowledged |
| `difference` | A snapshot disagrees with the reconstruction on its date; blocking until acknowledged, unless it is a check list or was published after the cutoff |
| `gap` | A calendar quarter with no corroborating snapshot; reported |
| `withheld` | Evidence first published after the cutoff; reported |
| `superseded` | A fund filing replaced by a later one for its report date; reported |

### `EvidenceLocator`

Where cited evidence sits in an artifact, and the hash of what it says there.

| Field | Type | Meaning |
| --- | --- | --- |
| `kind` | `LocatorKind` | Which kind of locator |
| `canonicalization_version` | ID part or null | `walker-1` for a text span; null for a pointer |
| `canonical_sha256` | 64 lowercase hex or null | The hash of the artifact's canonical text, for a text span |
| `start` | int ≥ 0 or null | A text span's first code point |
| `end` | int ≥ 0 or null | A text span's end, exclusive; `start < end` |
| `pointer` | string or null | A JSON pointer: empty, or starting with `/` |
| `cited_sha256` | 64 lowercase hex | SHA-256 of the cited content: the span's UTF-8 text, or the canonical JSON of the pointer's value |

### `Citation`

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | register slug | The source's key in a register |
| `url` | string | Where the artifact came from |
| `artifact` | `ArtifactRef` | The saved bytes: hash, media type, storage path, and rights |
| `retrieved_at` | UTC datetime | The artifact's first retrieval |
| `locators` | tuple of `EvidenceLocator` | The places cited; empty when the whole artifact is the evidence |

### `SourceRights`

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | register slug | The source |
| `evidence_class` | `EvidenceClass` or null | Its class; null for `sec-edgar`, which is identity evidence |
| `rights_status` | `RightsStatus` | What may be done with its content |
| `rights_basis` | string | Why |

### `CitedIdentity`

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_id` | ID part | The curated item whose row states it |
| `observed_on` | date | The row's date: a snapshot's as-of date, or a change's effective date |
| `name` | string | The company name as the row prints it |
| `ticker` | string | The ticker as the row prints it |

### `SecurityRecord`

| Field | Type | Meaning |
| --- | --- | --- |
| `security_id` | ID part | A curated slug for the security, never a ticker |
| `identities` | tuple of `CitedIdentity` | Every row that names it, by date then item; ticker changes stay visible |

### `MembershipAssertion`

One evidence item's statement about one security (P §Data contracts). A change item's
locators are the row's and then the effective date's.

| Field | Type | Meaning |
| --- | --- | --- |
| `membership_assertion_id` | ID part | `<evidence_id>:<security_id>:<asserted_action>` |
| `universe_id` | ID part | The universe |
| `security_id` | ID part | The security |
| `issuer_id` | ID part or null | `cik-<cik>` once resolved |
| `cik` | 10 digits or null | The zero-padded CIK once resolved |
| `asserted_action` | `AssertedAction` | What the item says |
| `asserted_date` | date | The date it says it for |
| `asserted_timing` | `BoundTiming` | The time of day it says |
| `effective_from` | date or null | The start of the interval it supports; null unless `supported` |
| `effective_from_basis` | `BoundBasis` or null | What establishes that start |
| `effective_from_timing` | `BoundTiming` or null | The start's timing |
| `effective_to` | date or null | The interval's exclusive end; null while open |
| `effective_to_timing` | `BoundTiming` or null | The end's timing |
| `announcement_date` | date or null | A change's announcement date |
| `source_snapshot_date` | date or null | A snapshot's as-of date |
| `publication_date` | date | When the item was first published, at date precision |
| `publication_time` | UTC datetime or null | When, if the evidence gives a time |
| `retrieved_at` | UTC datetime | The artifact's first retrieval; never a publication time |
| `source_id` | register slug | The source |
| `evidence_id` | ID part | The curated item |
| `url` | string | Where the artifact came from |
| `evidence_locators` | tuple of `EvidenceLocator` | Where the item states it |
| `raw_content_hash` | 64 lowercase hex | SHA-256 of the saved artifact |
| `rights_status` | `RightsStatus` | The source's rights |
| `status` | `AssertionStatus` | The assertion's standing |
| `resolved_by` | ID part or null | The `reject_assertion` override that set it aside |

### `MembershipInterval`

| Field | Type | Meaning |
| --- | --- | --- |
| `security_id` | ID part | The security |
| `effective_from` | date | Inclusive start |
| `effective_from_basis` | `BoundBasis` | What establishes it |
| `effective_from_timing` | `BoundTiming` | Its timing |
| `effective_to` | date or null | Exclusive end; null when open |
| `effective_to_timing` | `BoundTiming` or null | Its timing |
| `assertion_ids` | tuple of ID part | The supported assertions behind the start and the end |

### `IssuerCandidate`

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_id` | ID part | The row whose ticker proposed it |
| `cited_name` | string | The name on that row |
| `ticker` | string | The ticker on that row |
| `cik` | 10 digits | The CIK SEC's ticker list gives that ticker |
| `sec_name` | string | SEC's current name for the CIK |
| `ticker_listed` | bool | SEC's record for the CIK lists the ticker |
| `matched_name` | string or null | The SEC name, current or former, that covers the cited name |
| `confirmed` | bool | `ticker_listed` and a matched name |
| `citations` | tuple of `Citation` | The ticker-list entry, and the submissions record's name, tickers, and any matched former name |

### `IssuerMapping`

| Field | Type | Meaning |
| --- | --- | --- |
| `security_id` | ID part | The security |
| `status` | `ResolutionStatus` | The outcome |
| `method` | `ResolutionMethod` or null | How it resolved; null unless `resolved` |
| `issuer_id` | ID part or null | `cik-<cik>` when resolved |
| `cik` | 10 digits or null | The CIK when resolved |
| `candidates` | tuple of `IssuerCandidate` | Every candidate checked, confirmed or not |
| `override_id` | ID part or null | The override that decided it |
| `reason` | string or null | Why it is unresolved, or the override's rationale |

### `Issuer`

| Field | Type | Meaning |
| --- | --- | --- |
| `issuer_id` | ID part | `cik-<cik>` |
| `cik` | 10 digits | The zero-padded CIK |
| `sec_name` | string | SEC's current name |
| `former_names` | tuple of string | SEC's former names |
| `security_ids` | tuple of ID part | Its securities; several securities still make one issuer |

### `OverrideCitation`

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | string | The source cited |
| `url` | string | Where the evidence is |
| `artifact_sha256` | 64 lowercase hex or null | A saved artifact the build verifies, when there is one |
| `locator` | `EvidenceLocator` or null | A place in that artifact |

### `Override`

A reviewed manual decision, never a parser branch (P §Issuer resolution). Exactly the
targets its kind needs are set.

| Field | Type | Meaning |
| --- | --- | --- |
| `override_id` | ID part | A curated slug |
| `kind` | `OverrideKind` | The decision |
| `membership_assertion_id` | ID part or null | `reject_assertion`'s target |
| `security_id` | ID part or null | The target of `set_issuer`, `retain_unresolved`, and `holding_alias` |
| `cik` | 10 digits or null | `set_issuer`'s CIK |
| `finding_id` | ID part or null | `acknowledge`'s finding |
| `finding_digest` | 64 lowercase hex or null | The digest of the finding as reviewed |
| `holding_name` | string or null | `holding_alias`'s holding name, exactly as filed |
| `citations` | tuple of `OverrideCitation` | The evidence; required for `set_issuer` |
| `rationale` | string | Why |
| `reviewer` | string | Who decided; the user, never an agent |
| `recorded_on` | date | When |
| `effective_from` | date | The start of the period the decision covers |
| `effective_to` | date or null | Its exclusive end; null when open |

### `Finding`

| Field | Type | Meaning |
| --- | --- | --- |
| `finding_id` | ID part | `<kind>:<subject>` |
| `kind` | `FindingKind` | What was found |
| `blocking` | bool | It holds the freeze until resolved |
| `security_id` | ID part or null | The security concerned, if one |
| `detail` | string | What it says |
| `evidence_ids` | tuple of string | The evidence items concerned |
| `digest` | 64 lowercase hex | SHA-256 of the canonical JSON of the finding's kind, subject, detail, blocking flag, security, and evidence ids |
| `resolved_by` | tuple of ID part | The overrides that resolved it |

### `SnapshotReconciliation`

| Field | Type | Meaning |
| --- | --- | --- |
| `snapshot_id` | ID part | The evidence id, or `<source_id>:<accession>` for a fund filing |
| `source_id` | register slug | The source |
| `evidence_class` | `EvidenceClass` | Its class |
| `as_of` | date | The date it describes |
| `published_on` | date | When it was first published |
| `withheld` | bool | Published after the cutoff: reported only |
| `matched` | tuple of ID part | Securities in both the snapshot and the reconstruction |
| `reconstructed_only` | tuple of ID part | Members the snapshot lacks |
| `snapshot_only` | tuple of ID part | Securities it lists that the reconstruction does not |
| `unmatched` | tuple of string | Holding names or tickers that match no single security |
| `citation` | `Citation` or null | The snapshot's artifact; null for a check list |

### `CohortReport`

The coverage and conflict report (P-A4).

| Field | Type | Meaning |
| --- | --- | --- |
| `universe_id` | ID part | The universe |
| `anchor_evidence_id` | ID part or null | The anchor used; null when none is usable |
| `limitations` | tuple of string | What the evidence cannot show |
| `findings` | tuple of `Finding` | Every finding, by id |
| `reconciliations` | tuple of `SnapshotReconciliation` | Every snapshot compared, by date |

### `UniverseDefinition`

P §Data contracts, universe definition.

| Field | Type | Meaning |
| --- | --- | --- |
| `universe_id` | ID part | The universe across its versions |
| `universe_version` | int ≥ 1 | The version; a new one only when the content changes |
| `universe_name` | ID part | `djia` |
| `period_end_start` | date | `2024-07-01`, inclusive |
| `period_end_stop` | date | `2026-07-01`, exclusive |
| `public_information_cutoff` | date | `2026-09-22` |
| `membership_reference` | `first_publication_time` | The time membership is judged at |
| `expected_member_count` | int ≥ 1 | `30`: the roster's size at every date |
| `source_register_version` | 64 lowercase hex | SHA-256 of the canonical JSON of the register entries the manifest cites, `sec-edgar` always among them |
| `selection_policy_version` | string | `djia-pilot/1`, the rules of P §Deterministic pilot selection |
| `content_hash` | 64 lowercase hex | See the frozen manifest, above |
| `created_at` | UTC datetime | When this version was frozen |

### `UniverseManifest`

The frozen cohort, which Stage 5 joins against.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `definition` | `UniverseDefinition` | The universe |
| `sources` | tuple of `SourceRights` | Every source cited |
| `securities` | tuple of `SecurityRecord` | Every security the evidence names |
| `assertions` | tuple of `MembershipAssertion` | Every assertion, whatever its status |
| `intervals` | tuple of `MembershipInterval` | The derived intervals |
| `mappings` | tuple of `IssuerMapping` | One per security |
| `issuers` | tuple of `Issuer` | One per resolved CIK |
| `candidate_issuer_ids` | tuple of ID part | Issuers of the securities whose intervals meet `[period_end_start, cutoff]` |
| `overrides` | tuple of `Override` | Every reviewed decision applied |
| `report` | `CohortReport` | The coverage and conflict report |

### `LiveCheck`

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | register slug | The source |
| `purpose` | `terms` or `evidence` | A terms page, or a curated evidence page |
| `url` | string | What was requested |
| `outcome` | `unchanged`, `changed`, `refused`, or `failed` | What it found |
| `detail` | string | The hashes compared, or the refusal or error |
| `retrieval` | `Retrieval` or null | The request's metadata; null when nothing was received |

### `LiveVerification`

The opt-in live verification's result (P-VL), saved under `data/runs/cohort/live/`.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `checked_at` | UTC datetime | When it ran |
| `checks` | tuple of `LiveCheck` | Every live request |
| `build_problems` | tuple of string | Why the rebuild stopped, if it did |
| `rebuilt_content_hash` | 64 lowercase hex or null | The rebuilt cohort's content hash |
| `frozen_content_hash` | 64 lowercase hex or null | The latest frozen version's |
| `blocking_finding_ids` | tuple of ID part | Findings that would hold a freeze now |
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py docs/data-dictionary.md 2`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: `66 passed`.

- [ ] **Step 6: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/*.py packages/earnings-ingestion/tests/test_cohort_records.py packages/earnings-ingestion/tests/test_cohort_digests.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `766 passed, 23 deselected`;
`All checks passed!` and `177 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/cohort packages/earnings-ingestion/tests/test_cohort_records.py packages/earnings-ingestion/tests/test_cohort_digests.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(ingestion): define the cohort records and canonical JSON"
```

---
### Task 7: The membership register and the curated files

- **The register** (`docs/membership-source-register.toml`) is a second register for
  index-membership sources (P6-15).
  - It records A §242's fields for each source, plus its evidence class, its roles,
    and its rights.
  - A published source must record its terms' URL and hash.
  - `Registers` joins it to the release register's `sec-edgar` table, which the build
    cites for SEC records.
  - `version(source_ids)` hashes just the cited entries, so an edit to another
    source leaves a manifest's `source_register_version` alone.
- **The curated files** are read as TOML, converted to canonical JSON, and validated
  by strict models (P6-18):
  - `universe.toml` is a `UniverseConfig`;
  - `evidence.toml` is an `EvidenceFile`, with the anchor, corroborating snapshots,
    changes, and check lists;
  - `overrides.toml` is an `OverridesFile`, and it is optional.

  `EvidenceFile` refuses a repeated `evidence_id`, a second anchor, and an item that
  states one security twice.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/register.py`
  and `cohort/config.py`.
- Modify: `docs/data-dictionary.md` (appended, part 3 of 4), and
  `tests/contracts/test_data_dictionary.py` (replaced whole, block 3 of 3).
- Test (create): `packages/earnings-ingestion/tests/test_cohort_register.py` and
  `test_cohort_config.py`.

**Interfaces:**

- Consumes:
  - Task 6's `EvidenceClass`, `SourceRole`, `SourceRights`, `BoundTiming`,
    `Override`, and `canonical_json`/`digest`;
  - Task 1's `SourceId`, and Task 4's `Cik`.
- Produces:
  - `cohort/register.py`:
    - the paths `MEMBERSHIP_REGISTER` (`docs/membership-source-register.toml`) and
      `SEC_REGISTER` (`docs/source-register.toml`);
    - `SEC_SOURCE_ID = "sec-edgar"`, and `SEC_RIGHTS`, which is `local_only`;
    - `RegisterEntry` and `MembershipRegister`;
    - `Registers`, with `entry(source_id) -> RegisterEntry`, which raises
      `ValueError` for an unregistered source, `rights(source_id) -> SourceRights`,
      and `version(source_ids) -> str`;
    - `load_registers(repo, membership=MEMBERSHIP_REGISTER, sec=SEC_REGISTER) -> Registers`.
  - `cohort/config.py`:
    - `UNIVERSE_DIR`, which is `config/universe/djia`;
    - `EtfProxy(source_id, cik, forms)` and `UniverseConfig`;
    - `Row` and `ChangeRow`;
    - `SnapshotEvidence` (`role`, `as_of`, `members`) and `ChangeEvidence`
      (`announced_on`, `effective_on`, `timing`, `date_span`, `date_cited_sha256`,
      `entries`);
    - `CheckMember` and `CheckList`;
    - `EvidenceFile` and `OverridesFile`;
    - `CohortConfig(universe, evidence, overrides)`;
    - `load_toml(path, model)` and `load_cohort_config(directory) -> CohortConfig`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_cohort_register.py`:

```python
"""The membership source register loads strictly and versions what a manifest cites."""

from pathlib import Path

import pytest
from earnings_core import RightsStatus
from earnings_ingestion.cohort.records import EvidenceClass, SourceRole
from earnings_ingestion.cohort.register import SEC_RIGHTS, load_registers
from pydantic import ValidationError

ENTRY = """
[sources.{source_id}]
owner = "Synthetic Index Co."
url = "https://roster.example/djia"
access_method = "HTTPS GET of a fixed revision through the cohort web client."
cost = "Free."
license_terms = "Synthetic terms for tests."
terms_url = "https://roster.example/terms"
terms_sha256 = "{terms}"
redistribution_status = "Synthetic; redistributable."
coverage = "A synthetic roster."
expected_update_pattern = "Never updated."
known_limitations = ["Synthetic."]
last_verified = 2026-09-26
evidence_class = "secondary"
roles = ["anchor", "corroboration"]
rights_status = "redistributable"
rights_basis = "Synthetic test data."
"""
SEC = """
[sources.sec-edgar]
owner = "SEC"
last_verified = 2026-09-22
[sources.sec-edgar.access]
project_max_requests_per_second = 2
"""


def write(tmp_path: Path, *entries: str, sec: str = SEC) -> Path:
    (tmp_path / "docs").mkdir()
    body = "schema_version = 1\n" + "".join(entries)
    (tmp_path / "docs" / "membership-source-register.toml").write_text(body)
    (tmp_path / "docs" / "source-register.toml").write_text(sec)
    return tmp_path


def entry(source_id: str, terms: str = "a" * 64) -> str:
    return ENTRY.format(source_id=source_id, terms=terms)


def test_an_entry_gives_the_sources_class_roles_and_rights(tmp_path) -> None:
    registers = load_registers(write(tmp_path, entry("synthetic-roster")))
    found = registers.entry("synthetic-roster")
    assert found.evidence_class is EvidenceClass.SECONDARY
    assert found.roles == (SourceRole.ANCHOR, SourceRole.CORROBORATION)
    rights = registers.rights("synthetic-roster")
    assert rights.rights_status is RightsStatus.REDISTRIBUTABLE
    assert registers.rights("sec-edgar") == SEC_RIGHTS


def test_an_unregistered_source_is_refused(tmp_path) -> None:
    registers = load_registers(write(tmp_path, entry("synthetic-roster")))
    with pytest.raises(ValueError, match="not in the membership source register"):
        registers.entry("elsewhere")


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('evidence_class = "secondary"', 'evidence_class = "unknown"'),
        ('cost = "Free."', 'cost = "Free."\nquote = "Copied text."'),
        ('terms_sha256 = "' + "a" * 64 + '"', 'terms_sha256 = "abc"'),
    ],
    ids=["unknown-class", "extra-field", "short-hash"],
)
def test_a_malformed_entry_is_refused(tmp_path, old, new) -> None:
    with pytest.raises(ValidationError):
        load_registers(write(tmp_path, entry("synthetic-roster").replace(old, new)))


def test_only_a_user_supplied_list_may_omit_its_terms(tmp_path) -> None:
    terms = f'terms_url = "https://roster.example/terms"\nterms_sha256 = "{"a" * 64}"\n'
    bare = entry("synthetic-roster").replace(terms, "")
    with pytest.raises(ValidationError, match="records its terms"):
        load_registers(write(tmp_path, bare))
    user = bare.replace(
        'evidence_class = "secondary"', 'evidence_class = "user_supplied"'
    )
    user = user.replace('roles = ["anchor", "corroboration"]', 'roles = ["check"]')
    (tmp_path / "docs" / "membership-source-register.toml").write_text(
        "schema_version = 1\n" + user
    )
    assert load_registers(tmp_path).entry("synthetic-roster").terms_url is None


def test_the_release_register_must_hold_sec_edgar(tmp_path) -> None:
    with pytest.raises(ValueError, match="no sec-edgar entry"):
        load_registers(write(tmp_path, entry("synthetic-roster"), sec="[sources]\n"))


def test_the_version_changes_only_with_a_cited_entry(tmp_path) -> None:
    root = write(tmp_path, entry("synthetic-roster"), entry("other-roster"))
    before = load_registers(root).version(["synthetic-roster", "sec-edgar"])
    path = root / "docs" / "membership-source-register.toml"
    path.write_text(
        "schema_version = 1\n"
        + entry("synthetic-roster")
        + entry("other-roster", terms="b" * 64)
    )
    assert load_registers(root).version(["synthetic-roster"]) == before
    path.write_text(
        "schema_version = 1\n"
        + entry("synthetic-roster", terms="b" * 64)
        + entry("other-roster")
    )
    assert load_registers(root).version(["synthetic-roster"]) != before
```

Create `packages/earnings-ingestion/tests/test_cohort_config.py`:

```python
"""The curated cohort files load strictly: facts and citations, nothing else."""

from datetime import date

import pytest
from earnings_ingestion.cohort.config import load_cohort_config
from earnings_ingestion.cohort.records import BoundTiming, OverrideKind
from pydantic import ValidationError

UNIVERSE = """
universe_id = "djia-test"
universe_name = "djia"
period_end_start = 2024-07-01
period_end_stop = 2026-07-01
public_information_cutoff = 2026-09-22
membership_reference = "first_publication_time"
selection_policy_version = "djia-pilot/1"
expected_member_count = 2

[etf_proxy]
source_id = "synthetic-fund"
cik = "0009990009"
"""
H = "a" * 64
EVIDENCE = f"""
schema_version = 1

[[snapshots]]
evidence_id = "anchor"
source_id = "synthetic-roster"
role = "anchor"
url = "https://roster.example/djia?rev=1"
artifact_sha256 = "{H}"
canonical_sha256 = "{H}"
as_of = 2024-06-28
published_on = 2024-06-20

  [[snapshots.members]]
  security_id = "acme-common"
  name = "Acme Industrial"
  ticker = "ACME"
  span = [10, 25]
  cited_sha256 = "{H}"

[[changes]]
evidence_id = "change-1"
source_id = "synthetic-index"
url = "https://index.example/news/1"
artifact_sha256 = "{H}"
canonical_sha256 = "{H}"
announced_on = 2024-11-01
published_on = 2024-11-01
published_at = 2024-11-01T21:15:00Z
effective_on = 2024-11-08
timing = "before_open"
date_span = [40, 90]
date_cited_sha256 = "{H}"

  [[changes.entries]]
  action = "added"
  security_id = "corvid-common"
  name = "Corvid Systems"
  ticker = "CRVD"
  span = [5, 19]
  cited_sha256 = "{H}"

[[checks]]
evidence_id = "user-list"
source_id = "user-list"
as_of = 2026-09-22
published_on = 2026-09-26
members = [{{ name = "Acme Industrial", ticker = "ACME" }}]
"""
OVERRIDES = f"""
schema_version = 1

[[overrides]]
override_id = "acme-issuer"
kind = "set_issuer"
security_id = "acme-common"
cik = "0009990001"
rationale = "Reviewed."
reviewer = "Reviewer Name"
recorded_on = 2026-09-28
effective_from = 2024-07-01
citations = [{{ source_id = "sec-edgar", url = "https://data.sec.gov/x.json", artifact_sha256 = "{H}" }}]
"""


def write(tmp_path, evidence=EVIDENCE, overrides=OVERRIDES):
    (tmp_path / "universe.toml").write_text(UNIVERSE)
    (tmp_path / "evidence.toml").write_text(evidence)
    if overrides is not None:
        (tmp_path / "overrides.toml").write_text(overrides)
    return tmp_path


def test_the_curated_files_load_into_strict_models(tmp_path) -> None:
    config = load_cohort_config(write(tmp_path))
    assert config.universe.etf_proxy.forms == ("NPORT-P", "NPORT-P/A")
    (anchor,) = config.evidence.snapshots
    assert (anchor.as_of, anchor.members[0].span) == (date(2024, 6, 28), (10, 25))
    (change,) = config.evidence.changes
    assert change.timing is BoundTiming.BEFORE_OPEN
    assert change.published_at.utcoffset().total_seconds() == 0
    (override,) = config.overrides.overrides
    assert override.kind is OverrideKind.SET_ISSUER


def test_overrides_are_optional(tmp_path) -> None:
    assert load_cohort_config(write(tmp_path, overrides=None)).overrides.overrides == ()


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('evidence_id = "change-1"', 'evidence_id = "anchor"', "repeated"),
        ("span = [10, 25]", "span = [25, 10]", "empty or reversed"),
        ('ticker = "ACME"\n  span', 'ticker = "ACME"\n  quote = "x"\n  span', "Extra"),
        ('timing = "before_open"', 'timing = "at_noon"', "timing"),
        ("as_of = 2024-06-28", 'as_of = "June 28"', "as_of"),
    ],
    ids=["repeated-id", "reversed-span", "wording", "unknown-timing", "not-a-date"],
)
def test_a_malformed_evidence_file_is_refused(tmp_path, old, new, message) -> None:
    assert old in EVIDENCE
    with pytest.raises(ValidationError, match=message):
        load_cohort_config(write(tmp_path, evidence=EVIDENCE.replace(old, new)))


def test_two_anchors_are_refused(tmp_path) -> None:
    second = EVIDENCE.split("[[changes]]")[0].replace(
        '"anchor"\nsource', '"anchor-2"\nsource'
    )
    evidence = EVIDENCE + second.replace("schema_version = 1\n", "")
    with pytest.raises(ValidationError, match="at most one snapshot"):
        load_cohort_config(write(tmp_path, evidence=evidence))
```

Replace `tests/contracts/test_data_dictionary.py` with:

```python
"""docs/data-dictionary.md documents every field and value of the core contracts
and of the ingestion records: the canonicalizer's, the capture's, layout-1's, the
retrieval metadata, and the cohort's records and curated files.

AGENTS.md §191: document public interfaces and update the data dictionary in the
same change. A contract that gains, loses, or renames a field fails here.
"""

import re
from enum import StrEnum
from pathlib import Path

import earnings_core as core
import earnings_ingestion.canonical as ingestion
import pytest
from earnings_ingestion import browser, layout
from earnings_ingestion.cohort import config as cohort_config
from earnings_ingestion.cohort import records as cohort
from earnings_ingestion.cohort import register as cohort_register
from earnings_ingestion.fetch import records as fetch
from pydantic import BaseModel

DICTIONARY = Path(__file__).resolve().parents[2] / "docs" / "data-dictionary.md"
MODELS = [
    core.TextSpan,
    core.ArtifactRef,
    core.CanonicalDocument,
    core.TableCellContext,
    core.DocumentElement,
    core.SpanLocator,
    core.TextChunk,
    core.SpanCandidate,
    core.VerifiedSpan,
    core.OverlayMask,
    core.MaskedDocument,
    core.Rejection,
    ingestion.CanonicalizationManifest,
    ingestion.CanonicalizationFailure,
    ingestion.Canonicalized,
    browser.RenderedCapture,
    browser.BlockedRequest,
    browser.LayoutMetadata,
    browser.LayoutBlock,
    browser.LayoutRun,
    browser.LayoutTable,
    browser.LayoutRow,
    browser.LayoutCell,
    layout.AlignmentFailure,
    layout.LayoutExtraction,
    fetch.Retrieval,
    cohort.EvidenceLocator,
    cohort.Citation,
    cohort.SourceRights,
    cohort.CitedIdentity,
    cohort.SecurityRecord,
    cohort.MembershipAssertion,
    cohort.MembershipInterval,
    cohort.IssuerCandidate,
    cohort.IssuerMapping,
    cohort.Issuer,
    cohort.OverrideCitation,
    cohort.Override,
    cohort.Finding,
    cohort.SnapshotReconciliation,
    cohort.CohortReport,
    cohort.UniverseDefinition,
    cohort.UniverseManifest,
    cohort.LiveCheck,
    cohort.LiveVerification,
    cohort_config.UniverseConfig,
    cohort_config.EtfProxy,
    cohort_config.EvidenceFile,
    cohort_config.SnapshotEvidence,
    cohort_config.ChangeEvidence,
    cohort_config.Row,
    cohort_config.ChangeRow,
    cohort_config.CheckList,
    cohort_config.CheckMember,
    cohort_config.OverridesFile,
    cohort_register.MembershipRegister,
    cohort_register.RegisterEntry,
]
ENUMS = [
    core.RightsStatus,
    core.ElementType,
    core.TextOrigin,
    core.MaskCategory,
    core.RejectionReason,
    ingestion.FailureReason,
    browser.CaptureStatus,
    browser.CaptureReason,
    fetch.RetrievalMethod,
    cohort.EvidenceClass,
    cohort.SourceRole,
    cohort.LocatorKind,
    cohort.BoundTiming,
    cohort.BoundBasis,
    cohort.AssertedAction,
    cohort.AssertionStatus,
    cohort.ResolutionStatus,
    cohort.ResolutionMethod,
    cohort.OverrideKind,
    cohort.FindingKind,
]


def documented(name: str) -> set[str]:
    """The first-column code spans of the table under the heading for ``name``."""
    text = DICTIONARY.read_text(encoding="utf-8")
    heading = f"### `{name}`\n"
    assert heading in text, f"docs/data-dictionary.md has no section for {name}"
    section = text.split(heading, 1)[1].split("\n#", 1)[0]
    return set(re.findall(r"^\| `([^`]+)` \|", section, flags=re.MULTILINE))


@pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__name__)
def test_every_field_is_documented(model: type[BaseModel]) -> None:
    assert documented(model.__name__) == set(model.model_fields)


@pytest.mark.parametrize("enum", ENUMS, ids=lambda enum: enum.__name__)
def test_every_value_is_documented(enum: type[StrEnum]) -> None:
    assert documented(enum.__name__) == {member.value for member in enum}


def test_the_documented_versions_are_the_packages() -> None:
    text = DICTIONARY.read_text(encoding="utf-8")
    assert f"schema version {core.SCHEMA_VERSION}\n" in text
    assert f'`"{core.VALIDATOR_VERSION}"` (`earnings_core.VALIDATOR_VERSION`)' in text
    assert (
        f"## earnings-ingestion records, schema version"
        f" {ingestion.INGESTION_SCHEMA_VERSION}\n" in text
    )
```

This is block 3 for that path: extract it with
`python3 /tmp/plan6-extract.py tests/contracts/test_data_dictionary.py 3`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_register.py packages/earnings-ingestion/tests/test_cohort_config.py tests/contracts/test_data_dictionary.py -q`

Expected: FAIL. Collection stops in all three files, first with
`No module named 'earnings_ingestion.cohort.register'`, and pytest reports
`3 errors`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/register.py`:

```python
"""The membership source register: A §242's fields for index-membership sources.

It is a second register beside docs/source-register.toml, which holds the release
sources and the ``sec-edgar`` entry that the shared SEC client implements. It quotes
no source. A published source's terms are tracked by ``terms_url`` and
``terms_sha256``, the hash of their canonical text when a person last read them: a
different hash asks for a new reading, never an automatic decision. A list the user
supplied has no terms page.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal, Self

import tomllib
from earnings_core import RightsStatus
from earnings_core.artifacts import NonBlankStr
from earnings_core.hashing import Sha256Hex
from pydantic import BaseModel, ConfigDict, model_validator

from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import EvidenceClass, SourceRights, SourceRole
from earnings_ingestion.fetch.records import SourceId

MEMBERSHIP_REGISTER = Path("docs") / "membership-source-register.toml"
SEC_REGISTER = Path("docs") / "source-register.toml"
SEC_SOURCE_ID = "sec-edgar"
SEC_RIGHTS = SourceRights(
    source_id=SEC_SOURCE_ID,
    evidence_class=None,
    rights_status=RightsStatus.LOCAL_ONLY,
    rights_basis=(
        "docs/source-register.toml entry sec-edgar;"
        " SEC records are kept local under data/raw/"
    ),
)


class RegisterEntry(BaseModel):
    """One membership source; shared field names follow docs/source-register.toml."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    owner: NonBlankStr
    url: NonBlankStr
    access_method: NonBlankStr
    cost: NonBlankStr
    license_terms: NonBlankStr
    terms_url: NonBlankStr | None = None
    terms_sha256: Sha256Hex | None = None
    redistribution_status: NonBlankStr
    coverage: NonBlankStr
    expected_update_pattern: NonBlankStr
    known_limitations: tuple[NonBlankStr, ...]
    last_verified: date
    evidence_class: EvidenceClass
    roles: tuple[SourceRole, ...]
    rights_status: RightsStatus
    rights_basis: NonBlankStr

    @model_validator(mode="after")
    def _terms(self) -> Self:
        user = self.evidence_class is EvidenceClass.USER_SUPPLIED
        if not user and (self.terms_url is None or self.terms_sha256 is None):
            raise ValueError("a published source records its terms' URL and hash")
        return self


class MembershipRegister(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    sources: dict[SourceId, RegisterEntry]


@dataclass(frozen=True)
class Registers:
    """The membership register and the ``sec-edgar`` entry of the release register."""

    membership: MembershipRegister
    sec_entry: dict[str, Any]

    def entry(self, source_id: str) -> RegisterEntry:
        try:
            return self.membership.sources[source_id]
        except KeyError:
            raise ValueError(
                f"source {source_id!r} is not in the membership source register"
            ) from None

    def rights(self, source_id: str) -> SourceRights:
        if source_id == SEC_SOURCE_ID:
            return SEC_RIGHTS
        entry = self.entry(source_id)
        return SourceRights(
            source_id=source_id,
            evidence_class=entry.evidence_class,
            rights_status=entry.rights_status,
            rights_basis=entry.rights_basis,
        )

    def version(self, source_ids: Iterable[str]) -> str:
        """SHA-256 of the canonical JSON of every register entry a manifest cites,
        ``sec-edgar`` always among them."""
        cited = {
            source_id: self.entry(source_id).model_dump(mode="json")
            for source_id in set(source_ids) - {SEC_SOURCE_ID}
        }
        return digest(cited | {SEC_SOURCE_ID: self.sec_entry})


def load_registers(
    repo: Path,
    membership: Path = MEMBERSHIP_REGISTER,
    sec: Path = SEC_REGISTER,
) -> Registers:
    """Both registers, from paths relative to ``repo``."""
    text = (repo / membership).read_text(encoding="utf-8")
    register = MembershipRegister.model_validate(tomllib.loads(text))
    sources = tomllib.loads((repo / sec).read_text(encoding="utf-8"))["sources"]
    if SEC_SOURCE_ID not in sources:
        raise ValueError(f"{sec} has no {SEC_SOURCE_ID} entry")
    return Registers(membership=register, sec_entry=sources[SEC_SOURCE_ID])
```

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/config.py`:

```python
"""The curated cohort files, committed under ``config/universe/<name>/``.

- ``universe.toml``: the universe's definition, and the fund whose holdings
  corroborate it.
- ``evidence.toml``: every snapshot, change, and check list, as facts plus citations.
  A snapshot or change names its artifact by hash, and each fact by the offsets and
  hash of the canonical text that states it; no source wording is written here.
- ``overrides.toml``: the reviewer's decisions (``Override`` records).

Each file is read through canonical JSON into strict models, so a TOML date, string,
or array means exactly what the model says, and an unknown key is refused.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal, Self

import tomllib
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

from earnings_ingestion.cohort.digests import canonical_json
from earnings_ingestion.cohort.records import BoundTiming, Override
from earnings_ingestion.fetch.records import SourceId
from earnings_ingestion.sec.identifiers import Cik

UNIVERSE_DIR = Path("config") / "universe" / "djia"


class _Curated(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class EtfProxy(_Curated):
    """The fund whose N-PORT holdings corroborate the roster (an ETF proxy)."""

    source_id: SourceId
    cik: Cik
    forms: tuple[NonBlankStr, ...] = ("NPORT-P", "NPORT-P/A")


class UniverseConfig(_Curated):
    universe_id: IdPart
    universe_name: IdPart
    period_end_start: date
    period_end_stop: date
    public_information_cutoff: date
    membership_reference: Literal["first_publication_time"]
    selection_policy_version: NonBlankStr
    expected_member_count: PositiveInt
    etf_proxy: EtfProxy | None = None


class Row(_Curated):
    """One security as a snapshot or change states it, and where it says so."""

    security_id: IdPart
    name: NonBlankStr
    ticker: NonBlankStr
    span: tuple[NonNegativeInt, NonNegativeInt]
    cited_sha256: Sha256Hex

    @model_validator(mode="after")
    def _span(self) -> Self:
        if self.span[0] >= self.span[1]:
            raise ValueError(f"span {list(self.span)} is empty or reversed")
        return self


class ChangeRow(Row):
    action: Literal["added", "removed"]


class _Cited(_Curated):
    evidence_id: IdPart
    source_id: SourceId
    url: NonBlankStr
    artifact_sha256: Sha256Hex
    canonical_sha256: Sha256Hex
    published_on: date
    published_at: AwareDatetime | None = None


class SnapshotEvidence(_Cited):
    """A dated roster: the anchor, or a corroborating snapshot."""

    role: Literal["anchor", "corroboration"]
    as_of: date
    members: tuple[Row, ...]


class ChangeEvidence(_Cited):
    """An announcement of additions and removals, with where it states its date."""

    announced_on: date
    effective_on: date
    timing: BoundTiming
    date_span: tuple[NonNegativeInt, NonNegativeInt]
    date_cited_sha256: Sha256Hex
    entries: tuple[ChangeRow, ...]

    @model_validator(mode="after")
    def _span(self) -> Self:
        if self.date_span[0] >= self.date_span[1]:
            raise ValueError(f"date_span {list(self.date_span)} is empty or reversed")
        return self


class CheckMember(_Curated):
    name: NonBlankStr
    ticker: NonBlankStr


class CheckList(_Curated):
    """A list compared with the reconstruction and reported; it decides nothing."""

    evidence_id: IdPart
    source_id: SourceId
    as_of: date
    published_on: date
    members: tuple[CheckMember, ...]


class EvidenceFile(_Curated):
    schema_version: Literal[1]
    snapshots: tuple[SnapshotEvidence, ...] = ()
    changes: tuple[ChangeEvidence, ...] = ()
    checks: tuple[CheckList, ...] = ()

    @model_validator(mode="after")
    def _distinct(self) -> Self:
        ids = [item.evidence_id for item in (*self.snapshots, *self.changes)]
        ids += [check.evidence_id for check in self.checks]
        repeated = sorted(key for key, count in Counter(ids).items() if count > 1)
        if repeated:
            raise ValueError(f"evidence_id repeated: {repeated}")
        if sum(snapshot.role == "anchor" for snapshot in self.snapshots) > 1:
            raise ValueError("at most one snapshot is the anchor")
        for item in (*self.snapshots, *self.changes):
            rows = item.members if isinstance(item, SnapshotEvidence) else item.entries
            keys = [(row.security_id, getattr(row, "action", "")) for row in rows]
            if len(set(keys)) != len(keys):
                raise ValueError(f"{item.evidence_id} states a security twice")
        return self


class OverridesFile(_Curated):
    schema_version: Literal[1]
    overrides: tuple[Override, ...] = ()

    @model_validator(mode="after")
    def _distinct(self) -> Self:
        ids = [override.override_id for override in self.overrides]
        if len(set(ids)) != len(ids):
            raise ValueError("override_id repeated")
        return self


@dataclass(frozen=True)
class CohortConfig:
    universe: UniverseConfig
    evidence: EvidenceFile
    overrides: OverridesFile


def load_toml[M: BaseModel](path: Path, model: type[M]) -> M:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return model.model_validate_json(canonical_json(data))


def load_cohort_config(directory: Path) -> CohortConfig:
    """The three curated files in ``directory``; ``overrides.toml`` may be absent."""
    overrides = directory / "overrides.toml"
    return CohortConfig(
        universe=load_toml(directory / "universe.toml", UniverseConfig),
        evidence=load_toml(directory / "evidence.toml", EvidenceFile),
        overrides=(
            load_toml(overrides, OverridesFile)
            if overrides.exists()
            else OverridesFile(schema_version=1)
        ),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_register.py packages/earnings-ingestion/tests/test_cohort_config.py -q`

Expected: `16 passed`.

- [ ] **Step 5: Document the curated files**

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: FAIL: `12 failed, 66 passed`. The dictionary has no section for
the ten curated-file models or the two register models.

Append to `docs/data-dictionary.md`:

```markdown

## Curated cohort files

`config/universe/<name>/` holds three curated files, and
`docs/membership-source-register.toml` holds the register. Each file is read as TOML,
then canonical JSON, into strict models, so an unknown key is refused.

- `universe.toml` is one `UniverseConfig`.
- `evidence.toml` is an `EvidenceFile`.
- `overrides.toml` is an `OverridesFile` of `Override` records.

### `UniverseConfig`

| Field | Type | Meaning |
| --- | --- | --- |
| `universe_id` | ID part | Copied to the definition |
| `universe_name` | ID part | `djia` |
| `period_end_start` | date | Copied to the definition |
| `period_end_stop` | date | Copied to the definition |
| `public_information_cutoff` | date | Copied to the definition |
| `membership_reference` | `first_publication_time` | Copied to the definition |
| `selection_policy_version` | string | Copied to the definition |
| `expected_member_count` | int ≥ 1 | Copied to the definition |
| `etf_proxy` | `EtfProxy` or null | The corroborating fund |

### `EtfProxy`

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | register slug | The fund's membership-register source |
| `cik` | 10 digits | The fund's CIK |
| `forms` | tuple of string | The forms read, `NPORT-P` and `NPORT-P/A` |

### `EvidenceFile`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | The file's version |
| `snapshots` | tuple of `SnapshotEvidence` | At most one is the anchor |
| `changes` | tuple of `ChangeEvidence` | Official announcements |
| `checks` | tuple of `CheckList` | Lists compared and reported only |

### `SnapshotEvidence`

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_id` | ID part | A curated slug, unique in the file |
| `source_id` | register slug | Registered for the role |
| `url` | string | A URL the artifact was retrieved or saved from |
| `artifact_sha256` | 64 lowercase hex | The saved artifact |
| `canonical_sha256` | 64 lowercase hex | Its walker-1 canonical text's hash |
| `published_on` | date | First publication, as the source states it |
| `published_at` | UTC datetime or null | The time, if stated |
| `role` | `anchor` or `corroboration` | Its use |
| `as_of` | date | The date it describes |
| `members` | tuple of `Row` | Each listed security, with where it is listed |

### `ChangeEvidence`

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_id` | ID part | A curated slug, unique in the file |
| `source_id` | register slug | An official source registered for `change` |
| `url` | string | A URL the artifact was retrieved or saved from |
| `artifact_sha256` | 64 lowercase hex | The saved artifact |
| `canonical_sha256` | 64 lowercase hex | Its walker-1 canonical text's hash |
| `published_on` | date | First publication |
| `published_at` | UTC datetime or null | The time, if stated |
| `announced_on` | date | The announcement's date |
| `effective_on` | date | The effective date it states |
| `timing` | `BoundTiming` | The time of day it states |
| `date_span` | two ints | Where it states the date: `[start, end)` in the canonical text |
| `date_cited_sha256` | 64 lowercase hex | SHA-256 of that text |
| `entries` | tuple of `ChangeRow` | Each addition and removal |

### `Row`

| Field | Type | Meaning |
| --- | --- | --- |
| `security_id` | ID part | The security |
| `name` | string | The name exactly as the cited text prints it |
| `ticker` | string | The ticker exactly as the cited text prints it |
| `span` | two ints | Where the text states both: `[start, end)` in the canonical text |
| `cited_sha256` | 64 lowercase hex | SHA-256 of that text |

### `ChangeRow`

| Field | Type | Meaning |
| --- | --- | --- |
| `security_id` | ID part | The security |
| `name` | string | The name exactly as the cited text prints it |
| `ticker` | string | The ticker exactly as the cited text prints it |
| `span` | two ints | Where the text states both |
| `cited_sha256` | 64 lowercase hex | SHA-256 of that text |
| `action` | `added` or `removed` | The change |

### `CheckList`

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_id` | ID part | A curated slug |
| `source_id` | register slug | Registered for `check` |
| `as_of` | date | The date the list describes |
| `published_on` | date | When it was supplied |
| `members` | tuple of `CheckMember` | Its entries, compared by ticker |

### `CheckMember`

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | As supplied |
| `ticker` | string | As supplied |

### `OverridesFile`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | The file's version |
| `overrides` | tuple of `Override` | Unique `override_id`s |

### `MembershipRegister`

`docs/membership-source-register.toml`: A §242's fields for index-membership sources.
It is the second register, beside `docs/source-register.toml`, and it quotes no
source.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | The file's version |
| `sources` | map of register slug to `RegisterEntry` | One entry per source |

### `RegisterEntry`

| Field | Type | Meaning |
| --- | --- | --- |
| `owner` | string | Who publishes it |
| `url` | string | Its home |
| `access_method` | string | How the project reaches it, and through which client |
| `cost` | string | What access costs |
| `license_terms` | string | The terms, summarized in the project's words |
| `terms_url` | string or null | The terms page; null only for a user-supplied list |
| `terms_sha256` | 64 lowercase hex or null | The terms page's hash when a person last read it: SHA-256 of its `walker-1` canonical text for an HTML page, of its bytes otherwise |
| `redistribution_status` | string | What may be redistributed |
| `coverage` | string | What it covers |
| `expected_update_pattern` | string | How it changes |
| `known_limitations` | tuple of string | What it cannot show |
| `last_verified` | date | When a person last checked the entry |
| `evidence_class` | `EvidenceClass` | Its class |
| `roles` | tuple of `SourceRole` | Its permitted uses |
| `rights_status` | `RightsStatus` | Unclear rights are `local_only` |
| `rights_basis` | string | Why |
```

This is block 3 for that path: extract it with
`python3 /tmp/plan6-extract.py docs/data-dictionary.md 3`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: `78 passed`.

- [ ] **Step 6: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/register.py packages/earnings-ingestion/src/earnings_ingestion/cohort/config.py packages/earnings-ingestion/tests/test_cohort_register.py packages/earnings-ingestion/tests/test_cohort_config.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `794 passed, 23 deselected`;
`All checks passed!` and `181 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/cohort/register.py packages/earnings-ingestion/src/earnings_ingestion/cohort/config.py packages/earnings-ingestion/tests/test_cohort_register.py packages/earnings-ingestion/tests/test_cohort_config.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(ingestion): read the membership source register and the curated cohort files"
```

---
### Task 8: Citations, and name matching by token cover

- **Citations (P6-9).** `ArtifactText` reads one saved artifact once:
  - `walker-1`'s canonical text and hash for HTML, with no change to `walker-1`;
  - the parsed data for JSON.

  From it come the locators:
  - `span`, `find`, and `line` give text spans;
  - `pointer` gives a JSON pointer;
  - `verify` recomputes a locator's `cited_sha256` from the saved bytes;
  - `cited` returns the cited text, for a person's terminal only.

  `CitableArtifact` pairs an artifact with what a citation records.
- **Names (P6-8).** `tokens` normalizes a company name. `covered(cited, other)` is the
  one matching rule: every significant token of the cited name appears in the other.
  There is no fuzzy score, and legal-form words don't count.

This task uses `walker-1` to read pages, and nothing else from Stage 3: the stage
makes no parser, canonicalizer, document, or model artifact (the roadmap's Consumes
line).

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py`
  and `cohort/names.py`.
- Test (create): `packages/earnings-ingestion/tests/test_cohort_locators.py` and
  `test_cohort_names.py`.

**Interfaces:**

- Consumes:
  - Task 6's `EvidenceLocator`, `LocatorKind`, `Citation`, and `canonical_json`;
  - `earnings_ingestion.canonical`'s `canonicalize`, `CanonicalizationFailure`, and
    `CANONICALIZATION_VERSION`;
  - `earnings_core`'s `ArtifactRef` and `sha256_hex`.
- Produces:
  - `cohort/locators.py`:
    - `LocatorError(ValueError)`;
    - `resolve_json_pointer(document, pointer) -> object`;
    - `ArtifactText(body, media_type)`, with:
      - the cached properties `canonical -> (text, hash)` and `data`;
      - the locator makers `span(start, end)`, `find(needle, occurrence=1)`,
        `line(needle, occurrence=1)`, and `pointer(p)`, each returning an
        `EvidenceLocator`;
      - `cited(locator) -> str` and `verify(locator) -> None`.
    - `CitableArtifact(source_id, url, artifact, retrieved_at, text)`, with
      `cite(*locators) -> Citation`.
  - `cohort/names.py`: `DROPPED`, `tokens(name) -> frozenset[str]`, and
    `covered(cited, other) -> bool`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_cohort_locators.py`:

```python
"""Locators cite saved evidence by position and hash, and catch any change."""

import json

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.locators import (
    ArtifactText,
    LocatorError,
    resolve_json_pointer,
)
from earnings_ingestion.cohort.records import LocatorKind

PAGE = (
    b"<html><body><h1>Synthetic roster</h1><table>"
    b"<tr><th>Company</th><th>Symbol</th></tr>"
    b"<tr><td>Acme Industrial</td><td>ACME</td></tr>"
    b"<tr><td>Borealis Air</td><td>BORA</td></tr>"
    b"</table></body></html>"
)
DATA = json.dumps({"0": {"ticker": "ACME", "cik_str": 9990001}, "a/b": [1, 2]}).encode()


def test_a_found_span_cites_its_text_by_hash() -> None:
    page = ArtifactText(PAGE, "text/html; charset=utf-8")
    locator = page.find("Acme Industrial")
    assert locator.kind is LocatorKind.TEXT_SPAN
    assert locator.canonicalization_version == "walker-1"
    assert locator.cited_sha256 == sha256_hex(b"Acme Industrial")
    assert page.cited(locator) == "Acme Industrial"


def test_a_table_row_is_one_tab_separated_line() -> None:
    page = ArtifactText(PAGE, "text/html")
    row = page.find("Borealis Air\tBORA")
    assert page.cited(row) == "Borealis Air\tBORA"


def test_a_line_cites_the_whole_row_holding_the_text() -> None:
    page = ArtifactText(PAGE, "text/html")
    row = page.line("BORA")
    assert page.cited(row) == "Borealis Air\tBORA"
    assert page.cited(page.line("Synthetic")) == "Synthetic roster"
    with pytest.raises(LocatorError, match="does not occur"):
        page.line("CRVD")


def test_the_nth_occurrence_is_found() -> None:
    page = ArtifactText(
        PAGE.replace(b"</body>", b"<p>ACME again</p></body>"), "text/html"
    )
    first, second = page.find("ACME"), page.find("ACME", occurrence=2)
    assert first.start < second.start
    with pytest.raises(LocatorError, match="does not occur 3 times"):
        page.find("ACME", occurrence=3)


def test_changed_bytes_or_a_changed_hash_fail_verification() -> None:
    locator = ArtifactText(PAGE, "text/html").find("Acme Industrial")
    edited = ArtifactText(
        PAGE.replace(b"Acme Industrial", b"Acme Industries"), "text/html"
    )
    with pytest.raises(LocatorError, match="canonical text is not the one cited"):
        edited.verify(locator)
    forged = locator.model_copy(update={"cited_sha256": "0" * 64})
    with pytest.raises(LocatorError, match="no longer hashes"):
        ArtifactText(PAGE, "text/html").verify(forged)


def test_a_span_outside_the_text_is_refused() -> None:
    page = ArtifactText(PAGE, "text/html")
    with pytest.raises(LocatorError, match="outside"):
        page.span(0, 10_000)


def test_a_pointer_cites_the_canonical_json_of_its_value() -> None:
    data = ArtifactText(DATA, "application/json")
    locator = data.pointer("/0")
    assert data.cited(locator) == '{"cik_str":9990001,"ticker":"ACME"}'
    assert data.cited(data.pointer("/a~1b/1")) == "2"


@pytest.mark.parametrize("pointer", ["/1", "/a~1b/2", "/a~1b/01", "0"])
def test_a_pointer_to_nothing_is_refused(pointer) -> None:
    with pytest.raises(LocatorError):
        resolve_json_pointer(json.loads(DATA), pointer)


def test_each_kind_needs_its_media_type() -> None:
    with pytest.raises(LocatorError, match="needs HTML"):
        ArtifactText(DATA, "application/json").find("ACME")
    with pytest.raises(LocatorError, match="needs JSON"):
        ArtifactText(PAGE, "text/html").pointer("/0")
```

Create `packages/earnings-ingestion/tests/test_cohort_names.py`:

```python
"""Name coverage: every significant cited token appears; nothing fuzzy."""

import pytest
from earnings_ingestion.cohort.names import covered, tokens


def test_tokens_fold_case_accents_apostrophes_and_parentheticals() -> None:
    assert tokens("Caf" + chr(0xE9) + " Holdings (Class A) Inc.") == {
        "cafe",
        "holdings",
        "inc",
    }
    assert tokens("O'Brien & Sons/The") == {"obrien", "and", "sons", "the"}
    assert tokens("Acme-Widget Co") == {"acme", "widget", "co"}


@pytest.mark.parametrize(
    ("cited", "other"),
    [
        ("Acme Industrial", "ACME INDUSTRIAL CORP"),
        ("The Acme Companies, Inc.", "Acme Cos Inc/The"),
        ("Acme-Widget", "ACME WIDGET CO"),
        ("Borealis Air (Class A)", "Borealis Air Inc"),
        ("Crane & Sons", "CRANE AND SONS LTD"),
    ],
)
def test_a_cited_name_is_covered_by_a_longer_legal_name(cited, other) -> None:
    assert covered(cited, other)


@pytest.mark.parametrize(
    ("cited", "other"),
    [
        ("ACI", "Acme Commercial Industries"),
        ("Acme Industrial", "Acme Corp"),
        ("Inc.", "Acme Inc"),
        ("Acme Air", "Acme Airlines Corp"),
    ],
    ids=["initials", "missing-word", "only-legal-form", "prefix-is-not-a-token"],
)
def test_anything_less_is_not_covered(cited, other) -> None:
    assert not covered(cited, other)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_locators.py packages/earnings-ingestion/tests/test_cohort_names.py -q`

Expected: FAIL. Collection stops in both files, first with
`No module named 'earnings_ingestion.cohort.locators'`, and pytest reports
`2 errors`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py`:

```python
"""Cite evidence in a saved artifact, and verify a citation, without its wording.

Two locator kinds exist (plan 6, P6-9):

- ``text_span``: code-point offsets into the walker-1 canonical text of an HTML
  artifact. The locator records the canonicalization version and the canonical text's
  hash, so a different text can never silently move the span.
- ``json_pointer``: an RFC 6901 pointer into a JSON artifact.

``cited_sha256`` hashes the cited content: the span's text as UTF-8, or the canonical
JSON of the value at the pointer. Verification recomputes it from the saved bytes.
The cited content itself never enters a committed file; ``ArtifactText.cited`` returns
it for a person's terminal.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property

from earnings_core import ArtifactRef, sha256_hex

from earnings_ingestion.canonical import (
    CANONICALIZATION_VERSION,
    CanonicalizationFailure,
    canonicalize,
)
from earnings_ingestion.cohort.digests import canonical_json
from earnings_ingestion.cohort.records import Citation, EvidenceLocator, LocatorKind


class LocatorError(ValueError):
    """A locator that does not identify the content it claims to."""


def _essence(media_type: str) -> str:
    return media_type.partition(";")[0].strip().lower()


def resolve_json_pointer(document: object, pointer: str) -> object:
    """The value at an RFC 6901 pointer; ``LocatorError`` if there is none."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise LocatorError(f"{pointer!r} is not a JSON pointer")
    value = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and token in value:
            value = value[token]
        elif (
            isinstance(value, list)
            and token.isdigit()
            and (token == "0" or not token.startswith("0"))
            and int(token) < len(value)
        ):
            value = value[int(token)]
        else:
            raise LocatorError(f"{pointer!r} names nothing in the document")
    return value


class ArtifactText:
    """One saved artifact, read once: canonical text if HTML, parsed data if JSON."""

    def __init__(self, body: bytes, media_type: str) -> None:
        self.body = body
        self.media_type = _essence(media_type)

    @cached_property
    def canonical(self) -> tuple[str, str]:
        """walker-1's canonical text and its hash."""
        if self.media_type != "text/html":
            raise LocatorError(f"a text span needs HTML, not {self.media_type}")
        result = canonicalize(
            self.body, source_document_id="cohort-evidence", media_type="text/html"
        )
        if isinstance(result, CanonicalizationFailure):
            raise LocatorError(f"walker-1 cannot read it: {result.detail}")
        return result.document.canonical_text, result.document.canonical_hash

    @cached_property
    def data(self) -> object:
        if self.media_type != "application/json":
            raise LocatorError(f"a JSON pointer needs JSON, not {self.media_type}")
        try:
            return json.loads(self.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LocatorError(f"it is not JSON: {exc}") from exc

    def span(self, start: int, end: int) -> EvidenceLocator:
        text, text_hash = self.canonical
        if not 0 <= start < end <= len(text):
            raise LocatorError(f"[{start}, {end}) is outside [0, {len(text)})")
        return EvidenceLocator(
            kind=LocatorKind.TEXT_SPAN,
            canonicalization_version=CANONICALIZATION_VERSION,
            canonical_sha256=text_hash,
            start=start,
            end=end,
            cited_sha256=sha256_hex(text[start:end].encode("utf-8")),
        )

    def find(self, needle: str, occurrence: int = 1) -> EvidenceLocator:
        """The span of the ``occurrence``-th (1-based) appearance of ``needle``."""
        text, _ = self.canonical
        start = -1
        for _ in range(occurrence):
            start = text.find(needle, start + 1)
            if start == -1:
                count = "" if occurrence == 1 else f" {occurrence} times"
                raise LocatorError(f"{needle!r} does not occur{count}")
        return self.span(start, start + len(needle))

    def line(self, needle: str, occurrence: int = 1) -> EvidenceLocator:
        """The span of the whole line holding the ``occurrence``-th ``needle``.
        walker-1 writes a table row as one line of tab-separated cells, so this
        cites a roster row with every cell in it."""
        found = self.find(needle, occurrence)
        text, _ = self.canonical
        start = text.rfind("\n", 0, found.start) + 1
        end = text.find("\n", found.end)
        return self.span(start, len(text) if end == -1 else end)

    def pointer(self, pointer: str) -> EvidenceLocator:
        value = resolve_json_pointer(self.data, pointer)
        return EvidenceLocator(
            kind=LocatorKind.JSON_POINTER,
            pointer=pointer,
            cited_sha256=sha256_hex(canonical_json(value)),
        )

    def cited(self, locator: EvidenceLocator) -> str:
        """The content ``locator`` cites, once it has been verified."""
        self.verify(locator)
        if locator.kind is LocatorKind.TEXT_SPAN:
            return self.canonical[0][locator.start : locator.end]
        value = resolve_json_pointer(self.data, locator.pointer)
        return canonical_json(value).decode("utf-8")

    def verify(self, locator: EvidenceLocator) -> None:
        """Raise ``LocatorError`` unless ``locator`` still cites what it hashed."""
        if locator.kind is LocatorKind.TEXT_SPAN:
            if locator.canonicalization_version != CANONICALIZATION_VERSION:
                raise LocatorError(
                    f"the span was made under {locator.canonicalization_version},"
                    f" not {CANONICALIZATION_VERSION}"
                )
            if self.canonical[1] != locator.canonical_sha256:
                raise LocatorError("the artifact's canonical text is not the one cited")
            fresh = self.span(locator.start, locator.end)
        else:
            fresh = self.pointer(locator.pointer)
        if fresh.cited_sha256 != locator.cited_sha256:
            raise LocatorError("the cited content no longer hashes to cited_sha256")


@dataclass(frozen=True)
class CitableArtifact:
    """A stored artifact with what a citation of it records."""

    source_id: str
    url: str
    artifact: ArtifactRef
    retrieved_at: datetime
    text: ArtifactText

    def cite(self, *locators: EvidenceLocator) -> Citation:
        return Citation(
            source_id=self.source_id,
            url=self.url,
            artifact=self.artifact,
            retrieved_at=self.retrieved_at,
            locators=locators,
        )
```

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/names.py`:

```python
"""Company-name tokens, and the one matching rule the cohort uses (plan 6, P6-8).

A cited name is *covered* by another name when every token of the cited name,
legal forms and connectives dropped, is a token of the other. There is no fuzzy
score: a name either is covered or is not, and anything else is a reviewer's call,
recorded as an override.
"""

import re
import unicodedata

DROPPED = frozenset(
    {
        "and",
        "co",
        "companies",
        "company",
        "corp",
        "corporation",
        "inc",
        "incorporated",
        "limited",
        "llc",
        "ltd",
        "plc",
        "the",
    }
)
_PARENTHETICAL = re.compile(r"\([^)]*\)")
_TOKEN = re.compile(r"[a-z0-9]+")


def tokens(name: str) -> frozenset[str]:
    """``name``'s tokens: case-folded ASCII words, parentheticals and apostrophes
    removed, split at any other non-alphanumeric character."""
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    folded = _PARENTHETICAL.sub(" ", folded).casefold()
    folded = folded.replace("'", "").replace("&", " and ")
    return frozenset(_TOKEN.findall(folded))


def covered(cited: str, other: str) -> bool:
    """True when every significant token of ``cited`` is a token of ``other``."""
    significant = tokens(cited) - DROPPED
    return bool(significant) and significant <= tokens(other)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_locators.py packages/earnings-ingestion/tests/test_cohort_names.py -q`

Expected: `22 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py packages/earnings-ingestion/src/earnings_ingestion/cohort/names.py packages/earnings-ingestion/tests/test_cohort_locators.py packages/earnings-ingestion/tests/test_cohort_names.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `816 passed, 23 deselected`;
`All checks passed!` and `185 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py packages/earnings-ingestion/src/earnings_ingestion/cohort/names.py packages/earnings-ingestion/tests/test_cohort_locators.py packages/earnings-ingestion/tests/test_cohort_names.py
git commit -m "feat(ingestion): cite saved artifacts by locator and match names by token cover"
```

---
### Task 9: Findings, and interval reconstruction

- **Findings (P6-7).** `make_finding` names a finding `<kind>:<subject>` and hashes
  what it says.
  - `acknowledge` applies each `acknowledge` override whose digest still matches,
    and returns the stale ones.
  - Acknowledging any kind but `member_count` or `difference` raises, because those
    resolve by evidence or by their own override kinds.
- **Reconstruction (P6-6, P6-12).**
  - `reconstruct` turns each security's statements into intervals. The statements
    are its anchor row and its changes, each with its date, timing, and first
    publication date.
  - A break in the add/remove sequence is `conflicting` or `ambiguous`. The
    security's statements are then all marked, and it has no interval until a
    rejection removes the wrong one.
  - Statements first published after the cutoff are `withheld`.
  - `count_findings` compares the roster's size with the expected count at the
    anchor and at every bound up to the cutoff.
  - `roster(intervals, day)` gives the members on a day.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/findings.py`
  and `cohort/intervals.py`.
- Test (create): `packages/earnings-ingestion/tests/test_cohort_findings.py` and
  `test_cohort_intervals.py`.

**Interfaces:**

- Consumes: Task 6's `Finding`, `FindingKind`, `Override`, `OverrideKind`,
  `AssertedAction`, `AssertionStatus`, `BoundBasis`, `BoundTiming`, and
  `MembershipInterval`, and `digest`.
- Produces:
  - `cohort/findings.py`:
    - `ACKNOWLEDGEABLE`;
    - `make_finding(kind, subject, detail, *, blocking, security_id=None, evidence_ids=(), resolved_by=()) -> Finding`;
    - `acknowledge(findings, overrides) -> tuple[tuple[Finding, ...], tuple[str, ...]]`.
  - `cohort/intervals.py`:
    - `Statement(assertion_id, security_id, action, on, timing, evidence_id, published_on)`;
    - `Membership(statuses, rejected_by, intervals, supports, findings)`;
    - `reconstruct(statements, *, anchor_date, cutoff, rejections) -> Membership`,
      where `rejections` maps an assertion ID to the override that rejects it. It
      raises `ValueError` for an unknown or supported assertion;
    - `roster(intervals, day) -> frozenset[str]`;
    - `count_findings(intervals, *, anchor_date, cutoff, expected) -> tuple[Finding, ...]`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_cohort_findings.py`:

```python
"""Findings hash what they say, and an acknowledgement accepts only what it read."""

from datetime import date

import pytest
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.findings import acknowledge, make_finding
from earnings_ingestion.cohort.records import FindingKind, Override, OverrideKind


def difference(detail: str = "roster-x on 2025-01-31: snapshot only: acme-common"):
    return make_finding(
        FindingKind.DIFFERENCE,
        "roster-x",
        detail,
        blocking=True,
        evidence_ids=["roster-x", "anchor", "roster-x"],
    )


def ack(finding_id: str, finding_digest: str, override_id: str = "ack-x") -> Override:
    return Override(
        override_id=override_id,
        kind=OverrideKind.ACKNOWLEDGE,
        finding_id=finding_id,
        finding_digest=finding_digest,
        citations=(),
        rationale="The roster lagged the announced change by one day.",
        reviewer="Reviewer Name",
        recorded_on=date(2026, 9, 28),
        effective_from=date(2024, 7, 1),
    )


def test_a_finding_is_named_by_kind_and_subject_and_hashes_what_it_says() -> None:
    finding = difference()
    assert finding.finding_id == "difference:roster-x"
    assert finding.evidence_ids == ("anchor", "roster-x")
    assert finding.digest == digest(
        {
            "kind": "difference",
            "subject": "roster-x",
            "detail": finding.detail,
            "blocking": True,
            "security_id": None,
            "evidence_ids": ["anchor", "roster-x"],
        }
    )
    assert difference("another detail").digest != finding.digest
    resolved = make_finding(
        FindingKind.DIFFERENCE,
        "roster-x",
        finding.detail,
        blocking=True,
        evidence_ids=["anchor", "roster-x"],
        resolved_by=["ack-x"],
    )
    assert (resolved.digest, resolved.resolved_by) == (finding.digest, ("ack-x",))


def test_an_acknowledgement_resolves_only_the_finding_it_read() -> None:
    finding = difference()
    (resolved,), stale = acknowledge(
        [finding], [ack(finding.finding_id, finding.digest)]
    )
    assert (resolved.resolved_by, stale) == (("ack-x",), ())
    assert not resolved.holds_freeze
    changed = difference("roster-x on 2025-01-31: snapshot only: corvid-common")
    (held,), stale = acknowledge([changed], [ack(finding.finding_id, finding.digest)])
    assert (held.holds_freeze, stale) == (True, ("ack-x",))
    _, stale = acknowledge([], [ack("difference:gone", finding.digest, "ack-gone")])
    assert stale == ("ack-gone",)


def test_only_counts_and_differences_can_be_acknowledged() -> None:
    gap = make_finding(FindingKind.GAP, "2025q1", "no snapshot", blocking=False)
    with pytest.raises(ValueError, match="never acknowledged"):
        acknowledge([gap], [ack(gap.finding_id, gap.digest)])
```

Create `packages/earnings-ingestion/tests/test_cohort_intervals.py`:

```python
"""Interval reconstruction: P-VF's interval, conflict, and cutoff cases."""

from datetime import date

import pytest
from earnings_ingestion.cohort.intervals import (
    Statement,
    count_findings,
    reconstruct,
    roster,
)
from earnings_ingestion.cohort.records import (
    AssertedAction,
    AssertionStatus,
    BoundBasis,
    BoundTiming,
    FindingKind,
)

ANCHOR = date(2024, 6, 28)
CUTOFF = date(2026, 9, 22)
ADDED, REMOVED, MEMBER = (
    AssertedAction.ADDED,
    AssertedAction.REMOVED,
    AssertedAction.MEMBER_AT,
)


def say(
    security: str,
    action: AssertedAction,
    on: date,
    evidence: str,
    *,
    timing: BoundTiming = BoundTiming.BEFORE_OPEN,
    published: date | None = None,
) -> Statement:
    return Statement(
        assertion_id=f"{evidence}:{security}:{action}",
        security_id=security,
        action=action,
        on=on,
        timing=BoundTiming.UNSPECIFIED if action is MEMBER else timing,
        evidence_id=evidence,
        published_on=published or on,
    )


def anchor(*securities: str) -> list[Statement]:
    return [
        say(s, MEMBER, ANCHOR, "anchor", published=date(2024, 6, 20))
        for s in securities
    ]


def run(statements, rejections=None, anchor_date=ANCHOR):
    return reconstruct(
        statements,
        anchor_date=anchor_date,
        cutoff=CUTOFF,
        rejections=rejections or {},
    )


def test_anchor_additions_and_removals_make_half_open_intervals() -> None:
    result = run(
        [
            *anchor("acme", "borealis"),
            say("borealis", REMOVED, date(2024, 11, 8), "change-1"),
            say("corvid", ADDED, date(2024, 11, 8), "change-1"),
        ]
    )
    by_security = {i.security_id: i for i in result.intervals}
    acme, borealis, corvid = (by_security[s] for s in ("acme", "borealis", "corvid"))
    assert (acme.effective_from, acme.effective_to) == (ANCHOR, None)
    assert acme.effective_from_basis is BoundBasis.ANCHOR_SNAPSHOT
    assert acme.effective_to_timing is None
    assert (borealis.effective_to, borealis.effective_to_timing) == (
        date(2024, 11, 8),
        BoundTiming.BEFORE_OPEN,
    )
    assert corvid.effective_from_basis is BoundBasis.ANNOUNCED
    assert roster(result.intervals, date(2024, 11, 7)) == {"acme", "borealis"}
    assert roster(result.intervals, date(2024, 11, 8)) == {"acme", "corvid"}
    assert set(result.statuses.values()) == {AssertionStatus.SUPPORTED}
    assert result.findings == ()


def test_identical_claims_from_two_items_are_one_transition() -> None:
    result = run(
        [
            *anchor("acme"),
            say("corvid", ADDED, date(2024, 11, 8), "change-1"),
            say("corvid", ADDED, date(2024, 11, 8), "change-1-wire"),
        ]
    )
    (corvid,) = [i for i in result.intervals if i.security_id == "corvid"]
    assert corvid.assertion_ids == (
        "change-1-wire:corvid:added",
        "change-1:corvid:added",
    )


def test_conflicting_dates_stay_separate_and_hold_until_one_is_rejected() -> None:
    statements = [
        *anchor("acme"),
        say("corvid", ADDED, date(2024, 11, 7), "wire-report"),
        say("corvid", ADDED, date(2024, 11, 8), "change-1"),
    ]
    held = run(statements)
    assert [i.security_id for i in held.intervals] == ["acme"]
    assert held.statuses["wire-report:corvid:added"] is AssertionStatus.CONFLICTING
    assert held.statuses["change-1:corvid:added"] is AssertionStatus.CONFLICTING
    (finding,) = held.findings
    assert (finding.kind, finding.holds_freeze) == (
        FindingKind.MEMBERSHIP_CONFLICT,
        True,
    )

    reviewed = run(statements, {"wire-report:corvid:added": "reject-wire"})
    assert reviewed.statuses["wire-report:corvid:added"] is AssertionStatus.CONFLICTING
    assert reviewed.rejected_by == {"wire-report:corvid:added": "reject-wire"}
    assert reviewed.statuses["change-1:corvid:added"] is AssertionStatus.SUPPORTED
    (resolved,) = reviewed.findings
    assert resolved.resolved_by == ("reject-wire",)
    assert not resolved.holds_freeze


@pytest.mark.parametrize(
    ("statements", "detail"),
    [
        ([say("acme", ADDED, date(2024, 11, 8), "c")], "added on 2024-11-08 while a"),
        ([say("zeta", REMOVED, date(2024, 11, 8), "c")], "removed on 2024-11-08"),
        ([say("acme", REMOVED, ANCHOR, "c")], "on or before the anchor's date"),
        (
            [
                say("zeta", ADDED, date(2024, 11, 8), "c"),
                say(
                    "zeta",
                    ADDED,
                    date(2024, 11, 8),
                    "d",
                    timing=BoundTiming.AFTER_CLOSE,
                ),
            ],
            "with timings",
        ),
    ],
    ids=["added-while-member", "removed-while-not", "before-anchor", "two-timings"],
)
def test_every_break_in_the_sequence_is_a_conflict(statements, detail) -> None:
    result = run([*anchor("acme"), *statements])
    (finding,) = result.findings
    assert finding.kind is FindingKind.MEMBERSHIP_CONFLICT
    assert detail in finding.detail


def test_an_addition_and_a_removal_on_one_date_are_ambiguous() -> None:
    result = run(
        [
            *anchor("acme"),
            say("acme", REMOVED, date(2025, 3, 3), "c"),
            say("acme", ADDED, date(2025, 3, 3), "d", timing=BoundTiming.AFTER_CLOSE),
        ]
    )
    assert result.statuses["c:acme:removed"] is AssertionStatus.AMBIGUOUS
    assert result.statuses["anchor:acme:member_at"] is AssertionStatus.AMBIGUOUS
    assert result.findings[0].kind is FindingKind.MEMBERSHIP_AMBIGUITY
    assert result.intervals == ()


def test_evidence_published_after_the_cutoff_is_withheld() -> None:
    late = say("corvid", ADDED, date(2026, 9, 30), "late", published=date(2026, 9, 23))
    result = run([*anchor("acme"), late])
    assert result.statuses["late:corvid:added"] is AssertionStatus.WITHHELD
    assert [i.security_id for i in result.intervals] == ["acme"]


def test_evidence_published_on_the_cutoff_applies() -> None:
    change = say("corvid", ADDED, date(2026, 9, 30), "c", published=CUTOFF)
    result = run([*anchor("acme"), change])
    assert result.statuses["c:corvid:added"] is AssertionStatus.SUPPORTED


def test_only_a_conflicting_or_ambiguous_assertion_can_be_rejected() -> None:
    with pytest.raises(ValueError, match="only a conflicting or ambiguous"):
        run(anchor("acme"), {"anchor:acme:member_at": "reject"})
    with pytest.raises(ValueError, match="name no assertion"):
        run(anchor("acme"), {"nowhere": "reject"})


def test_without_an_anchor_only_announced_intervals_exist() -> None:
    result = run(
        [
            say("corvid", ADDED, date(2024, 11, 8), "c"),
            say("borealis", REMOVED, date(2024, 11, 8), "c"),
        ],
        anchor_date=None,
    )
    assert [i.security_id for i in result.intervals] == ["corvid"]
    assert result.statuses["c:borealis:removed"] is AssertionStatus.CONFLICTING


def test_a_roster_of_the_wrong_size_is_a_blocking_finding() -> None:
    result = run(
        [
            *anchor("acme", "borealis"),
            say("corvid", ADDED, date(2024, 11, 8), "c"),
        ]
    )
    (finding,) = count_findings(
        result.intervals, anchor_date=ANCHOR, cutoff=CUTOFF, expected=2
    )
    assert finding.finding_id == "member_count:2024-11-08"
    assert (
        finding.detail == "3 members on 2024-11-08, expected 2: acme, borealis, corvid"
    )
    assert finding.holds_freeze
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_findings.py packages/earnings-ingestion/tests/test_cohort_intervals.py -q`

Expected: FAIL. Collection stops in both files, first with
`No module named 'earnings_ingestion.cohort.findings'`, and pytest reports
`2 errors`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/findings.py`:

```python
"""Findings of the coverage and conflict report, and reviewed acknowledgements.

A finding's ``digest`` hashes what it says. An ``acknowledge`` override names a
finding and that digest, so it accepts exactly the finding a reviewer read: when the
evidence changes what a finding says, the acknowledgement no longer applies and the
finding holds the freeze again.
"""

from collections.abc import Iterable

from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import (
    Finding,
    FindingKind,
    Override,
    OverrideKind,
)

ACKNOWLEDGEABLE = frozenset({FindingKind.MEMBER_COUNT, FindingKind.DIFFERENCE})


def make_finding(
    kind: FindingKind,
    subject: str,
    detail: str,
    *,
    blocking: bool,
    security_id: str | None = None,
    evidence_ids: Iterable[str] = (),
    resolved_by: Iterable[str] = (),
) -> Finding:
    """A finding with id ``<kind>:<subject>`` and the digest of its content."""
    evidence = tuple(sorted(set(evidence_ids)))
    content = {
        "kind": kind.value,
        "subject": subject,
        "detail": detail,
        "blocking": blocking,
        "security_id": security_id,
        "evidence_ids": evidence,
    }
    return Finding(
        finding_id=f"{kind.value}:{subject}",
        kind=kind,
        blocking=blocking,
        security_id=security_id,
        detail=detail,
        evidence_ids=evidence,
        digest=digest(content),
        resolved_by=tuple(sorted(set(resolved_by))),
    )


def acknowledge(
    findings: Iterable[Finding], overrides: Iterable[Override]
) -> tuple[tuple[Finding, ...], tuple[str, ...]]:
    """The findings with current acknowledgements applied, and the ids of the
    acknowledgements that no longer match any finding's digest."""
    findings = tuple(findings)
    by_id = {finding.finding_id: finding for finding in findings}
    accepted: dict[str, list[str]] = {}
    stale: list[str] = []
    for override in overrides:
        if override.kind is not OverrideKind.ACKNOWLEDGE:
            continue
        finding = by_id.get(override.finding_id)
        if finding is not None and finding.kind not in ACKNOWLEDGEABLE:
            raise ValueError(
                f"{override.override_id}: a {finding.kind} finding is resolved by"
                " evidence or its own override kind, never acknowledged"
            )
        if finding is None or finding.digest != override.finding_digest:
            stale.append(override.override_id)
            continue
        accepted.setdefault(finding.finding_id, []).append(override.override_id)
    resolved = tuple(
        finding.model_copy(
            update={
                "resolved_by": tuple(
                    sorted({*finding.resolved_by, *accepted[finding.finding_id]})
                )
            }
        )
        if finding.finding_id in accepted
        else finding
        for finding in findings
    )
    return resolved, tuple(sorted(stale))
```

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/intervals.py`:

```python
"""Effective membership intervals from the anchor and the announced changes.

Each security's statements, its anchor row and its changes, must form one sequence.
It starts from the anchor, a member if the anchor lists it; additions and removals
then alternate, each strictly after the anchor's date. Identical claims from several
items are one transition. Otherwise:

- an addition and a removal on one date are ``ambiguous``: the evidence cannot say
  whether the security was a member that day;
- any other break is ``conflicting``: an addition while a member, a removal while not
  one, a change on or before the anchor's date, or one transition stated with two
  timings.

A security whose statements break the sequence has every statement marked and no
interval until a reviewer rejects the wrong ones (``reject_assertion``); its finding
holds the freeze meanwhile. Statements first published after the cutoff are
``withheld`` and never applied (P-C4). Conflicting statements are never merged.
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import NamedTuple

from earnings_ingestion.cohort.findings import make_finding
from earnings_ingestion.cohort.records import (
    AssertedAction,
    AssertionStatus,
    BoundBasis,
    BoundTiming,
    Finding,
    FindingKind,
    MembershipInterval,
)


@dataclass(frozen=True)
class Statement:
    """What one evidence item says about one security, before any judgement."""

    assertion_id: str
    security_id: str
    action: AssertedAction
    on: date
    timing: BoundTiming
    evidence_id: str
    published_on: date


@dataclass(frozen=True)
class Membership:
    statuses: dict[str, AssertionStatus]
    rejected_by: dict[str, str]
    """Each rejected assertion's ``reject_assertion`` override."""
    intervals: tuple[MembershipInterval, ...]
    supports: dict[str, MembershipInterval]
    """The interval each supported assertion belongs to."""
    findings: tuple[Finding, ...]


class _Break(NamedTuple):
    status: AssertionStatus
    detail: str


def _sequence(
    security_id: str, statements: list[Statement], anchor_date: date | None
) -> list[MembershipInterval] | _Break:
    anchored = [s for s in statements if s.action is AssertedAction.MEMBER_AT]
    days: dict[date, dict[AssertedAction, list[Statement]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for statement in statements:
        if statement.action is not AssertedAction.MEMBER_AT:
            days[statement.on][statement.action].append(statement)
    transitions = []
    for day in sorted(days):
        actions = days[day]
        if len(actions) > 1:
            return _Break(AssertionStatus.AMBIGUOUS, f"added and removed on {day}")
        ((action, group),) = actions.items()
        timings = sorted({statement.timing.value for statement in group})
        if len(timings) > 1:
            return _Break(
                AssertionStatus.CONFLICTING, f"{action} on {day} with timings {timings}"
            )
        if anchor_date is not None and day <= anchor_date:
            return _Break(
                AssertionStatus.CONFLICTING,
                f"{action} on {day}, on or before the anchor's date {anchor_date}",
            )
        transitions.append((day, action, group[0].timing, group))

    intervals: list[MembershipInterval] = []
    start = None
    if anchored:
        ids = [statement.assertion_id for statement in anchored]
        start = (anchor_date, BoundBasis.ANCHOR_SNAPSHOT, BoundTiming.UNSPECIFIED, ids)
    for day, action, timing, group in transitions:
        ids = [statement.assertion_id for statement in group]
        if action is AssertedAction.ADDED:
            if start is not None:
                return _Break(
                    AssertionStatus.CONFLICTING, f"added on {day} while a member"
                )
            start = (day, BoundBasis.ANNOUNCED, timing, ids)
            continue
        if start is None:
            return _Break(
                AssertionStatus.CONFLICTING, f"removed on {day} while not a member"
            )
        intervals.append(_interval(security_id, start, day, timing, ids))
        start = None
    if start is not None:
        intervals.append(_interval(security_id, start, None, None, []))
    return intervals


def _interval(security_id, start, end, end_timing, end_ids) -> MembershipInterval:
    day, basis, timing, ids = start
    return MembershipInterval(
        security_id=security_id,
        effective_from=day,
        effective_from_basis=basis,
        effective_from_timing=timing,
        effective_to=end,
        effective_to_timing=end_timing,
        assertion_ids=tuple(sorted([*ids, *end_ids])),
    )


def _finding(security_id: str, flaw: _Break, statements, resolved_by) -> Finding:
    kind = (
        FindingKind.MEMBERSHIP_AMBIGUITY
        if flaw.status is AssertionStatus.AMBIGUOUS
        else FindingKind.MEMBERSHIP_CONFLICT
    )
    return make_finding(
        kind,
        security_id,
        f"{security_id}: {flaw.detail}",
        blocking=True,
        security_id=security_id,
        evidence_ids=[statement.evidence_id for statement in statements],
        resolved_by=resolved_by,
    )


def reconstruct(
    statements: Iterable[Statement],
    *,
    anchor_date: date | None,
    cutoff: date,
    rejections: Mapping[str, str],
) -> Membership:
    """Statuses, intervals, and findings; ``rejections`` maps an assertion id to the
    ``reject_assertion`` override that sets it aside."""
    statements = tuple(statements)
    unknown = set(rejections) - {statement.assertion_id for statement in statements}
    if unknown:
        raise ValueError(f"rejections name no assertion: {sorted(unknown)}")
    by_security: dict[str, list[Statement]] = defaultdict(list)
    for statement in statements:
        by_security[statement.security_id].append(statement)

    statuses: dict[str, AssertionStatus] = {}
    rejected_by: dict[str, str] = {}
    intervals: list[MembershipInterval] = []
    findings: list[Finding] = []
    for security_id in sorted(by_security):
        live = []
        for statement in by_security[security_id]:
            if statement.published_on > cutoff:
                statuses[statement.assertion_id] = AssertionStatus.WITHHELD
            else:
                live.append(statement)
        rejected = [s for s in live if s.assertion_id in rejections]
        withheld = set(rejections) & {
            s.assertion_id for s in by_security[security_id] if s not in live
        }
        first = _sequence(security_id, live, anchor_date)
        if withheld or (rejected and not isinstance(first, _Break)):
            ids = sorted(withheld | {s.assertion_id for s in rejected})
            raise ValueError(
                f"{ids}: only a conflicting or ambiguous assertion can be rejected"
            )
        kept = [s for s in live if s.assertion_id not in rejections]
        result = first if not rejected else _sequence(security_id, kept, anchor_date)
        for statement in rejected:
            statuses[statement.assertion_id] = first.status
            rejected_by[statement.assertion_id] = rejections[statement.assertion_id]
        if isinstance(result, _Break):
            for statement in kept:
                statuses[statement.assertion_id] = result.status
            findings.append(_finding(security_id, result, live, ()))
            continue
        if isinstance(first, _Break):
            overrides = [rejected_by[s.assertion_id] for s in rejected]
            findings.append(_finding(security_id, first, live, overrides))
        for statement in kept:
            statuses[statement.assertion_id] = AssertionStatus.SUPPORTED
        intervals.extend(result)

    supports = {
        assertion_id: interval
        for interval in intervals
        for assertion_id in interval.assertion_ids
    }
    return Membership(
        statuses=statuses,
        rejected_by=rejected_by,
        intervals=tuple(intervals),
        supports=supports,
        findings=tuple(findings),
    )


def roster(intervals: Iterable[MembershipInterval], day: date) -> frozenset[str]:
    """The securities whose intervals contain ``day``."""
    return frozenset(i.security_id for i in intervals if i.contains(day))


def count_findings(
    intervals: tuple[MembershipInterval, ...],
    *,
    anchor_date: date | None,
    cutoff: date,
    expected: int,
) -> tuple[Finding, ...]:
    """A blocking finding for each date, from the anchor's to the cutoff, on which
    the roster changes to a size other than ``expected``."""
    if anchor_date is None:
        return ()
    bounds = {
        bound
        for interval in intervals
        for bound in (interval.effective_from, interval.effective_to)
        if bound is not None and anchor_date < bound <= cutoff
    }
    findings = []
    for day in sorted({anchor_date, *bounds}):
        members = sorted(roster(intervals, day))
        if len(members) != expected:
            findings.append(
                make_finding(
                    FindingKind.MEMBER_COUNT,
                    day.isoformat(),
                    f"{len(members)} members on {day}, expected {expected}:"
                    f" {', '.join(members) or 'none'}",
                    blocking=True,
                )
            )
    return tuple(findings)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_findings.py packages/earnings-ingestion/tests/test_cohort_intervals.py -q`

Expected: `16 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/findings.py packages/earnings-ingestion/src/earnings_ingestion/cohort/intervals.py packages/earnings-ingestion/tests/test_cohort_findings.py packages/earnings-ingestion/tests/test_cohort_intervals.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `832 passed, 23 deselected`;
`All checks passed!` and `189 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/cohort/findings.py packages/earnings-ingestion/src/earnings_ingestion/cohort/intervals.py packages/earnings-ingestion/tests/test_cohort_findings.py packages/earnings-ingestion/tests/test_cohort_intervals.py
git commit -m "feat(ingestion): reconstruct membership intervals and report findings"
```

---
### Task 10: Security-to-issuer resolution

P §Issuer resolution, as P6-8 reads it.

- **Candidates.** Each cited identity, a name and a ticker from one evidence row,
  proposes the CIKs that SEC's ticker list maps its ticker to.
- **Confirmation.** A candidate is confirmed when SEC's submissions for the CIK list
  the ticker, and a current or former SEC name covers the cited name. One confirmed
  CIK resolves the security.
- **Conflicts.** Distinct confirmed CIKs conflict, and a security confirmed nowhere
  is unresolved.
- **Blocking.** An in-scope security in either state holds the freeze until a
  `set_issuer` or `retain_unresolved` override decides it. An out-of-scope one is
  recorded and blocks nothing.
- **Issuers.** Several securities of one CIK derive one `Issuer` row.
- **Citations.** Each candidate cites:
  - the ticker list's entry;
  - the submissions' `/name` and `/tickers`;
  - the `/formerNames/<i>` that matched, if a former name did.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/resolution.py`.
- Test (create): `packages/earnings-ingestion/tests/test_cohort_resolution.py`.

**Interfaces:**

- Consumes:
  - Task 5's `TickerEntry` and `Registrant`;
  - Task 8's `CitableArtifact` and `covered`;
  - Task 9's `make_finding`;
  - Task 6's `SecurityRecord`, `IssuerCandidate`, `IssuerMapping`, `Issuer`,
    `Override`, `ResolutionStatus`, and `ResolutionMethod`.
- Produces, in `cohort/resolution.py`:
  - `issuer_id_for(cik) -> str`, which gives `cik-<10 digits>`;
  - `SecEvidence(tickers: CitableArtifact, ticker_entries, registrants)`, where
    `registrants` maps a CIK to `(Registrant, CitableArtifact)`. Its
    `registrant(cik)` raises `ValueError` when no submissions were saved for the
    CIK;
  - `Resolution(mappings, issuers, findings)`;
  - `resolve(securities, sec, overrides, in_scope: frozenset[str]) -> Resolution`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_cohort_resolution.py`:

```python
"""Issuer resolution: P-VF's ticker-history, multiple-security, and CIK cases."""

import json
from datetime import UTC, date, datetime

import pytest
from earnings_core import ArtifactRef, RightsStatus
from earnings_ingestion.cohort.locators import ArtifactText, CitableArtifact
from earnings_ingestion.cohort.records import (
    CitedIdentity,
    FindingKind,
    Override,
    OverrideCitation,
    OverrideKind,
    ResolutionMethod,
    ResolutionStatus,
    SecurityRecord,
)
from earnings_ingestion.cohort.resolution import SecEvidence, resolve
from earnings_ingestion.sec.data import read_company_tickers, read_submissions

TICKERS = {
    "0": {"cik_str": 9990001, "ticker": "ACME", "title": "Acme Industrial Corp"},
    "1": {"cik_str": 9990002, "ticker": "BORA", "title": "Borealis Air Inc"},
    "2": {"cik_str": 9990003, "ticker": "CRVD", "title": "Corvid Systems Inc"},
    "3": {"cik_str": 9990004, "ticker": "CRVD", "title": "Corvid Holdings"},
    "4": {"cik_str": 9990005, "ticker": "DYNA", "title": "Dynamo Motors"},
    "5": {"cik_str": 9990005, "ticker": "DYNB", "title": "Dynamo Motors"},
}
REGISTRANTS = {
    "9990001": ("Acme Industrial Corp", ["ACME"], []),
    "9990002": ("Borealis Air Inc", ["BORA"], ["Northern Airways Inc"]),
    "9990003": ("Corvid Systems Inc", ["CRVD"], []),
    "9990004": ("Corvid Systems Holdings", ["CRVD"], []),
    "9990005": ("Dynamo Motors Co", ["DYNA", "DYNB"], []),
    "9990006": ("Eastfield Bank Corp", ["EFB"], []),
}


def citable(body: bytes, url: str) -> CitableArtifact:
    return CitableArtifact(
        source_id="sec-edgar",
        url=url,
        artifact=ArtifactRef.for_bytes(
            body,
            media_type="application/json",
            storage_ref="data/raw/sec-edgar/x.json",
            rights_status=RightsStatus.LOCAL_ONLY,
            rights_basis="test",
        ),
        retrieved_at=datetime(2026, 9, 27, tzinfo=UTC),
        text=ArtifactText(body, "application/json"),
    )


def submissions(cik: str, name: str, tickers: list[str], former: list[str]) -> bytes:
    columns = ("accessionNumber", "filingDate", "reportDate", "acceptanceDateTime")
    recent = {column: [] for column in (*columns, "form", "primaryDocument")}
    data = {
        "cik": cik,
        "name": name,
        "tickers": tickers,
        "formerNames": [
            {
                "name": n,
                "from": "2001-01-01T00:00:00.000Z",
                "to": "2024-01-01T00:00:00.000Z",
            }
            for n in former
        ],
        "filings": {"recent": recent, "files": []},
    }
    return json.dumps(data).encode()


def sec_evidence() -> SecEvidence:
    body = json.dumps(TICKERS).encode()
    registrants = {}
    for cik, (name, tickers, former) in REGISTRANTS.items():
        raw = submissions(cik, name, tickers, former)
        registrants[f"{int(cik):010d}"] = (
            read_submissions(raw),
            citable(raw, f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"),
        )
    return SecEvidence(
        tickers=citable(body, "https://www.sec.gov/files/company_tickers.json"),
        ticker_entries=read_company_tickers(body),
        registrants=registrants,
    )


def security(security_id: str, *identities: tuple[str, str]) -> SecurityRecord:
    return SecurityRecord(
        security_id=security_id,
        identities=tuple(
            CitedIdentity(
                evidence_id=f"item-{index}",
                observed_on=date(2024, 6, 28 - index),
                name=name,
                ticker=ticker,
            )
            for index, (name, ticker) in enumerate(identities)
        ),
    )


def override(override_id: str, kind: OverrideKind, **targets) -> Override:
    return Override(
        override_id=override_id,
        kind=kind,
        citations=(OverrideCitation(source_id="sec-edgar", url="https://x.test/"),),
        rationale="Reviewed against the filings.",
        reviewer="Reviewer Name",
        recorded_on=date(2026, 9, 28),
        effective_from=date(2024, 7, 1),
        **targets,
    )


def run(securities, overrides=(), scope=None):
    scope = frozenset(s.security_id for s in securities) if scope is None else scope
    return resolve(securities, sec_evidence(), overrides, scope)


def test_a_listed_ticker_under_a_covering_name_resolves_to_a_padded_cik() -> None:
    result = run([security("acme-common", ("Acme Industrial", "ACME"))])
    (mapping,) = result.mappings
    assert (mapping.status, mapping.method) == (
        ResolutionStatus.RESOLVED,
        ResolutionMethod.SEC_TICKER_AND_NAME,
    )
    assert (mapping.cik, mapping.issuer_id) == ("0009990001", "cik-0009990001")
    tickers, filings = mapping.candidates[0].citations
    assert [locator.pointer for locator in tickers.locators] == ["/0"]
    assert [locator.pointer for locator in filings.locators] == ["/name", "/tickers"]
    assert result.findings == ()


def test_a_former_name_confirms_and_is_cited() -> None:
    result = run([security("borealis-common", ("Northern Airways", "BORA"))])
    (mapping,) = result.mappings
    assert mapping.cik == "0009990002"
    assert mapping.candidates[0].matched_name == "Northern Airways Inc"
    pointers = [loc.pointer for loc in mapping.candidates[0].citations[1].locators]
    assert pointers == ["/name", "/tickers", "/formerNames/0"]


def test_a_ticker_change_keeps_both_identities_and_resolves_once() -> None:
    record = security(
        "acme-common", ("Acme Industrial", "ACMX"), ("Acme Industrial", "ACME")
    )
    result = run([record])
    (mapping,) = result.mappings
    assert mapping.cik == "0009990001"
    assert [i.ticker for i in record.identities] == ["ACMX", "ACME"]


def test_two_securities_of_one_issuer_derive_one_issuer_row() -> None:
    result = run(
        [
            security("dynamo-class-a", ("Dynamo Motors", "DYNA")),
            security("dynamo-class-b", ("Dynamo Motors", "DYNB")),
        ]
    )
    (issuer,) = result.issuers
    assert issuer.cik == "0009990005"
    assert issuer.security_ids == ("dynamo-class-a", "dynamo-class-b")


def test_a_name_that_is_not_covered_leaves_it_unresolved_and_blocking() -> None:
    result = run([security("acme-common", ("ACI", "ACME"))])
    (mapping,) = result.mappings
    assert mapping.status is ResolutionStatus.UNRESOLVED
    assert mapping.cik is None
    (finding,) = result.findings
    assert (finding.kind, finding.holds_freeze) == (FindingKind.IDENTITY, True)


def test_an_unknown_ticker_is_unresolved_with_its_reason() -> None:
    (mapping,) = run([security("zeta-common", ("Zeta", "ZETA"))]).mappings
    assert mapping.reason == "SEC's ticker list has none of ZETA"


def test_two_confirmed_ciks_conflict() -> None:
    result = run([security("corvid-common", ("Corvid Systems", "CRVD"))])
    (mapping,) = result.mappings
    assert mapping.status is ResolutionStatus.CONFLICTING
    assert mapping.reason == "SEC confirms several CIKs: 0009990003, 0009990004"


def test_overrides_decide_and_resolve_the_finding() -> None:
    unresolved = security("acme-common", ("ACI", "ACME"))
    set_issuer = override(
        "acme-issuer",
        OverrideKind.SET_ISSUER,
        security_id="acme-common",
        cik="0009990001",
    )
    result = run([unresolved], [set_issuer])
    (mapping,) = result.mappings
    assert (mapping.method, mapping.override_id) == (
        ResolutionMethod.OVERRIDE,
        "acme-issuer",
    )
    assert result.findings[0].resolved_by == ("acme-issuer",)
    assert not result.findings[0].holds_freeze

    keep = override(
        "keep-zeta", OverrideKind.RETAIN_UNRESOLVED, security_id="zeta-common"
    )
    (kept,) = run([security("zeta-common", ("Zeta", "ZETA"))], [keep]).mappings
    assert kept.status is ResolutionStatus.RETAINED_UNRESOLVED
    assert kept.reason == "Reviewed against the filings."


def test_an_out_of_scope_security_does_not_block() -> None:
    result = run([security("zeta-common", ("Zeta", "ZETA"))], scope=frozenset())
    assert result.findings == ()


def test_a_proposed_cik_without_saved_submissions_stops_the_build() -> None:
    evidence = sec_evidence()
    evidence = SecEvidence(
        tickers=evidence.tickers,
        ticker_entries=evidence.ticker_entries,
        registrants={},
    )
    with pytest.raises(ValueError, match="run the SEC fetch"):
        resolve(
            [security("acme-common", ("Acme Industrial", "ACME"))],
            evidence,
            (),
            frozenset({"acme-common"}),
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_resolution.py -q`

Expected: FAIL. Collection stops with
`No module named 'earnings_ingestion.cohort.resolution'`, and pytest reports
`1 error`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/resolution.py`:

```python
"""Security-to-issuer resolution to a zero-padded CIK (P §Issuer resolution).

A cited ticker only proposes candidates: SEC's ticker list maps it to a CIK. The
candidate is confirmed when SEC's own record for that CIK lists the same ticker and
a name, current or former, that covers the name cited beside the ticker (plan 6,
P6-8). One confirmed CIK resolves the security. None, or several, leave it
``unresolved`` or ``conflicting``; an in-scope security in that state holds the
freeze until a reviewer's ``set_issuer`` or ``retain_unresolved`` override decides
it. Nothing is guessed, and no ticker alone establishes identity (A §268).
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from earnings_ingestion.cohort.findings import make_finding
from earnings_ingestion.cohort.locators import CitableArtifact
from earnings_ingestion.cohort.names import covered
from earnings_ingestion.cohort.records import (
    Finding,
    FindingKind,
    Issuer,
    IssuerCandidate,
    IssuerMapping,
    Override,
    OverrideKind,
    ResolutionMethod,
    ResolutionStatus,
    SecurityRecord,
)
from earnings_ingestion.sec.data import Registrant, TickerEntry


def issuer_id_for(cik: str) -> str:
    return f"cik-{cik}"


@dataclass(frozen=True)
class SecEvidence:
    """SEC's ticker list and the submissions of every CIK it proposed or a
    reviewer named, each with what is needed to cite it."""

    tickers: CitableArtifact
    ticker_entries: tuple[TickerEntry, ...]
    registrants: Mapping[str, tuple[Registrant, CitableArtifact]]

    def registrant(self, cik: str) -> tuple[Registrant, CitableArtifact]:
        try:
            return self.registrants[cik]
        except KeyError:
            raise ValueError(
                f"no saved submissions for CIK {cik}; run the SEC fetch first"
            ) from None


@dataclass(frozen=True)
class Resolution:
    mappings: tuple[IssuerMapping, ...]
    issuers: tuple[Issuer, ...]
    findings: tuple[Finding, ...]


def _candidates(security: SecurityRecord, sec: SecEvidence) -> list[IssuerCandidate]:
    by_ticker: dict[str, list[TickerEntry]] = defaultdict(list)
    for entry in sec.ticker_entries:
        by_ticker[entry.ticker].append(entry)
    candidates = []
    for identity in security.identities:
        for entry in by_ticker.get(identity.ticker, []):
            registrant, submissions = sec.registrant(entry.cik)
            names = [(registrant.name, "/name")] + [
                (former.name, former.pointer) for former in registrant.former_names
            ]
            matched = next(
                (
                    (name, pointer)
                    for name, pointer in names
                    if covered(identity.name, name)
                ),
                None,
            )
            pointers = ["/name", "/tickers"]
            if matched is not None and matched[1] != "/name":
                pointers.append(matched[1])
            listed = identity.ticker in registrant.tickers
            candidates.append(
                IssuerCandidate(
                    evidence_id=identity.evidence_id,
                    cited_name=identity.name,
                    ticker=identity.ticker,
                    cik=entry.cik,
                    sec_name=registrant.name,
                    ticker_listed=listed,
                    matched_name=None if matched is None else matched[0],
                    confirmed=listed and matched is not None,
                    citations=(
                        sec.tickers.cite(sec.tickers.text.pointer(entry.pointer)),
                        submissions.cite(
                            *(submissions.text.pointer(p) for p in pointers)
                        ),
                    ),
                )
            )
    return candidates


def resolve(
    securities: Iterable[SecurityRecord],
    sec: SecEvidence,
    overrides: Iterable[Override],
    in_scope: frozenset[str],
) -> Resolution:
    """A mapping for every security; a blocking finding for each in-scope security
    that SEC's evidence does not resolve, settled when an override decides it."""
    decided: dict[str, Override] = {}
    for override in overrides:
        if override.kind in (OverrideKind.SET_ISSUER, OverrideKind.RETAIN_UNRESOLVED):
            if override.security_id in decided:
                raise ValueError(f"{override.security_id} has two identity overrides")
            decided[override.security_id] = override
    securities = tuple(securities)
    unknown = set(decided) - {security.security_id for security in securities}
    if unknown:
        raise ValueError(f"identity overrides name no security: {sorted(unknown)}")

    mappings, findings = [], []
    for security in sorted(securities, key=lambda s: s.security_id):
        candidates = tuple(_candidates(security, sec))
        confirmed = sorted({c.cik for c in candidates if c.confirmed})
        if not security.identities:
            status = ResolutionStatus.UNRESOLVED
            reason = "no name or ticker was published for it by the cutoff"
        elif len(confirmed) == 1:
            status, reason = ResolutionStatus.RESOLVED, None
        elif confirmed:
            status = ResolutionStatus.CONFLICTING
            reason = f"SEC confirms several CIKs: {', '.join(confirmed)}"
        elif candidates:
            status = ResolutionStatus.UNRESOLVED
            reason = "no candidate lists the cited ticker under a covering name"
        else:
            status = ResolutionStatus.UNRESOLVED
            tickers = sorted({i.ticker for i in security.identities})
            reason = f"SEC's ticker list has none of {', '.join(tickers)}"
        override = decided.get(security.security_id)
        if status is not ResolutionStatus.RESOLVED and security.security_id in in_scope:
            findings.append(
                make_finding(
                    FindingKind.IDENTITY,
                    security.security_id,
                    f"{security.security_id}: {status}: {reason}",
                    blocking=True,
                    security_id=security.security_id,
                    evidence_ids=[i.evidence_id for i in security.identities],
                    resolved_by=() if override is None else (override.override_id,),
                )
            )
        mappings.append(
            _mapping(security, candidates, confirmed, status, reason, override)
        )

    issuers = _issuers(mappings, sec)
    return Resolution(tuple(mappings), issuers, tuple(findings))


def _mapping(
    security, candidates, confirmed, status, reason, override
) -> IssuerMapping:
    common = {"security_id": security.security_id, "candidates": candidates}
    if override is not None and override.kind is OverrideKind.SET_ISSUER:
        return IssuerMapping(
            **common,
            status=ResolutionStatus.RESOLVED,
            method=ResolutionMethod.OVERRIDE,
            issuer_id=issuer_id_for(override.cik),
            cik=override.cik,
            override_id=override.override_id,
            reason=override.rationale,
        )
    if override is not None:
        return IssuerMapping(
            **common,
            status=ResolutionStatus.RETAINED_UNRESOLVED,
            method=None,
            issuer_id=None,
            cik=None,
            override_id=override.override_id,
            reason=override.rationale,
        )
    resolved = status is ResolutionStatus.RESOLVED
    return IssuerMapping(
        **common,
        status=status,
        method=ResolutionMethod.SEC_TICKER_AND_NAME if resolved else None,
        issuer_id=issuer_id_for(confirmed[0]) if resolved else None,
        cik=confirmed[0] if resolved else None,
        override_id=None,
        reason=reason,
    )


def _issuers(mappings: list[IssuerMapping], sec: SecEvidence) -> tuple[Issuer, ...]:
    securities: dict[str, list[str]] = defaultdict(list)
    for mapping in mappings:
        if mapping.cik is not None:
            securities[mapping.cik].append(mapping.security_id)
    issuers = []
    for cik in sorted(securities):
        registrant, _ = sec.registrant(cik)
        issuers.append(
            Issuer(
                issuer_id=issuer_id_for(cik),
                cik=cik,
                sec_name=registrant.name,
                former_names=tuple(former.name for former in registrant.former_names),
                security_ids=tuple(sorted(securities[cik])),
            )
        )
    return tuple(issuers)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_resolution.py -q`

Expected: `10 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/resolution.py packages/earnings-ingestion/tests/test_cohort_resolution.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `842 passed, 23 deselected`;
`All checks passed!` and `191 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/cohort/resolution.py packages/earnings-ingestion/tests/test_cohort_resolution.py
git commit -m "feat(ingestion): resolve securities to issuers by SEC ticker and name"
```

---
### Task 11: Corroboration

A corroborating snapshot never adds or removes a member (P §Membership evidence and
source rights; P6-10). It is compared with the reconstructed roster on its own date,
and the difference is reported.

- **`reconcile`** lists the matched securities, those only in the reconstruction,
  those only in the snapshot, and the snapshot's unmatched names. A snapshot first
  published after the cutoff is marked withheld.
- **`match_holdings`** reads a fund's equity holdings:
  - a holding matches the one security whose cited name it covers, or the security a
    `holding_alias` override names;
  - anything else is unmatched, and so is a holding that several securities cover.
- **`current_filings`** keeps, for each report date, the latest filing filed on or
  before the cutoff, and supersedes the earlier ones. Later filings are kept apart.
- **`difference_findings`** blocks on a disagreement, unless the snapshot is withheld
  or a check list.
- **`gap_findings`** notes each calendar quarter with no timely corroboration.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/corroboration.py`.
- Test (create): `packages/earnings-ingestion/tests/test_cohort_corroboration.py`.

**Interfaces:**

- Consumes:
  - Task 5's `Filing` and `HoldingsReport`;
  - Task 8's `CitableArtifact` and `covered`;
  - Task 9's `make_finding` and `roster`;
  - Task 6's `SnapshotReconciliation`, `Citation`, `EvidenceClass`, `Finding`,
    `FindingKind`, `MembershipInterval`, `Override`, `OverrideKind`, and
    `SecurityRecord`.
- Produces, in `cohort/corroboration.py`:
  - `EQUITY_COMMON = "EC"`;
  - `FundFiling(filing, report, artifact: CitableArtifact)`;
  - `reconcile(snapshot_id, *, source_id, evidence_class, as_of, published_on, cutoff, listed, unmatched, intervals, citation) -> SnapshotReconciliation`;
  - `match_holdings(report, securities, overrides) -> tuple[set[str], list[str]]`;
  - `current_filings(filings, cutoff) -> tuple[list[FundFiling], list[Finding]]`;
  - `difference_findings(reconciliations) -> tuple[Finding, ...]`;
  - `gap_findings(reconciliations, *, start, cutoff) -> tuple[Finding, ...]`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_cohort_corroboration.py`:

```python
"""Corroboration: snapshots compared on their dates, never used as the roster."""

from datetime import UTC, date, datetime

from earnings_ingestion.cohort.corroboration import (
    FundFiling,
    current_filings,
    difference_findings,
    gap_findings,
    match_holdings,
    reconcile,
)
from earnings_ingestion.cohort.records import (
    BoundBasis,
    BoundTiming,
    CitedIdentity,
    EvidenceClass,
    FindingKind,
    MembershipInterval,
    Override,
    OverrideKind,
    SecurityRecord,
)
from earnings_ingestion.sec.data import Filing, Holding, HoldingsReport

CUTOFF = date(2026, 9, 22)


def interval(security_id: str, start: date, end: date | None = None):
    return MembershipInterval(
        security_id=security_id,
        effective_from=start,
        effective_from_basis=BoundBasis.ANNOUNCED,
        effective_from_timing=BoundTiming.BEFORE_OPEN,
        effective_to=end,
        effective_to_timing=None if end is None else BoundTiming.BEFORE_OPEN,
        assertion_ids=("a",),
    )


INTERVALS = (
    interval("acme-common", date(2024, 6, 28)),
    interval("borealis-common", date(2024, 6, 28), date(2024, 11, 8)),
    interval("corvid-common", date(2024, 11, 8)),
)
SECURITIES = tuple(
    SecurityRecord(
        security_id=security_id,
        identities=(
            CitedIdentity(
                evidence_id="anchor",
                observed_on=date(2024, 6, 28),
                name=name,
                ticker=ticker,
            ),
        ),
    )
    for security_id, name, ticker in [
        ("acme-common", "Acme Industrial", "ACME"),
        ("borealis-common", "Borealis Air", "BORA"),
        ("corvid-common", "Corvid Systems", "CRVD"),
    ]
)


def compare(listed, as_of, *, published=None, cls=EvidenceClass.SECONDARY):
    return reconcile(
        "snapshot",
        source_id="synthetic-roster",
        evidence_class=cls,
        as_of=as_of,
        published_on=published or as_of,
        cutoff=CUTOFF,
        listed=listed,
        unmatched=(),
        intervals=INTERVALS,
        citation=None,
    )


def test_an_agreeing_snapshot_raises_nothing() -> None:
    result = compare({"acme-common", "corvid-common"}, date(2025, 1, 31))
    assert result.agrees
    assert difference_findings([result]) == ()


def test_a_disagreeing_snapshot_blocks_until_acknowledged() -> None:
    result = compare({"acme-common", "borealis-common"}, date(2025, 1, 31))
    assert (result.reconstructed_only, result.snapshot_only) == (
        ("corvid-common",),
        ("borealis-common",),
    )
    (finding,) = difference_findings([result])
    assert finding.kind is FindingKind.DIFFERENCE
    assert finding.holds_freeze


def test_late_snapshots_and_check_lists_are_reported_only() -> None:
    late = compare({"acme-common"}, date(2026, 9, 1), published=date(2026, 9, 26))
    check = compare({"acme-common"}, date(2026, 9, 1), cls=EvidenceClass.USER_SUPPLIED)
    assert late.withheld
    assert [f.blocking for f in difference_findings([late, check])] == [False, False]


def report(*names: str, category: str | None = "EC") -> HoldingsReport:
    return HoldingsReport(
        report_date=date(2025, 1, 31),
        holdings=tuple(
            Holding(name=n, title=None, asset_category=category, position=i)
            for i, n in enumerate(names, start=1)
        ),
    )


def test_holdings_match_by_covering_name_or_a_reviewed_alias() -> None:
    alias = Override(
        override_id="corvid-alias",
        kind=OverrideKind.HOLDING_ALIAS,
        security_id="corvid-common",
        holding_name="CSI Holdings",
        citations=(),
        rationale="The fund's name for Corvid Systems.",
        reviewer="Reviewer Name",
        recorded_on=date(2026, 9, 28),
        effective_from=date(2024, 7, 1),
    )
    holdings = report("Acme Industrial Corp", "CSI Holdings", "Unknown Co")
    matched, unmatched = match_holdings(holdings, SECURITIES, [alias])
    assert matched == {"acme-common", "corvid-common"}
    assert unmatched == ["Unknown Co"]


def test_non_equity_holdings_are_not_members() -> None:
    matched, unmatched = match_holdings(report("Cash", category="STIV"), SECURITIES, [])
    assert (matched, unmatched) == (set(), [])


def filing(accession: str, filed: date, form: str = "NPORT-P") -> FundFiling:
    return FundFiling(
        filing=Filing(
            accession=accession,
            form=form,
            filing_date=filed,
            report_date=date(2025, 1, 31),
            accepted_at=datetime.combine(filed, datetime.min.time(), tzinfo=UTC),
            primary_document="primary_doc.xml",
            columns="/filings/recent",
            index=0,
        ),
        report=report("Acme Industrial Corp"),
        artifact=None,
    )


def test_an_amendment_supersedes_and_a_late_filing_is_kept_apart() -> None:
    original = filing("0009990009-25-000001", date(2025, 3, 28))
    amended = filing("0009990009-25-000002", date(2025, 4, 2), "NPORT-P/A")
    late = filing("0009990009-26-000009", date(2026, 9, 30), "NPORT-P/A")
    current, findings = current_filings([late, original, amended], CUTOFF)
    assert [f.filing.accession for f in current] == [
        "0009990009-25-000002",
        "0009990009-26-000009",
    ]
    (superseded,) = findings
    assert superseded.finding_id == "superseded:0009990009-25-000001"
    assert not superseded.blocking


def test_every_uncorroborated_quarter_is_a_gap() -> None:
    covered = [compare({"acme-common", "corvid-common"}, date(2025, 1, 31))]
    gaps = gap_findings(covered, start=date(2024, 7, 1), cutoff=date(2025, 6, 30))
    assert [f.finding_id for f in gaps] == ["gap:2024q3", "gap:2024q4", "gap:2025q2"]
    assert not any(f.blocking for f in gaps)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_corroboration.py -q`

Expected: FAIL. Collection stops with
`No module named 'earnings_ingestion.cohort.corroboration'`, and pytest reports
`1 error`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/corroboration.py`:

```python
"""Dated snapshots compared with the reconstructed roster (P §Membership evidence).

A corroborating snapshot, a secondary roster or a fund's holdings, never adds or
removes a member: it is compared on its own date, and a disagreement is a blocking
``difference`` until a reviewer acknowledges that exact finding. A check list, or any
snapshot first published after the cutoff, is compared and reported only.

Fund holdings name companies, not securities. A holding matches the one security
whose cited name its name covers, or the security a ``holding_alias`` override names
(plan 6, P6-10); any other holding is listed as unmatched. For each report date, the
latest filing filed on or before the cutoff is compared, and earlier ones are
``superseded``.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from earnings_ingestion.cohort.findings import make_finding
from earnings_ingestion.cohort.intervals import roster
from earnings_ingestion.cohort.locators import CitableArtifact
from earnings_ingestion.cohort.names import covered
from earnings_ingestion.cohort.records import (
    Citation,
    EvidenceClass,
    Finding,
    FindingKind,
    MembershipInterval,
    Override,
    OverrideKind,
    SecurityRecord,
    SnapshotReconciliation,
)
from earnings_ingestion.sec.data import Filing, HoldingsReport

EQUITY_COMMON = "EC"


@dataclass(frozen=True)
class FundFiling:
    """One saved N-PORT filing of the corroborating fund."""

    filing: Filing
    report: HoldingsReport
    artifact: CitableArtifact


def reconcile(
    snapshot_id: str,
    *,
    source_id: str,
    evidence_class: EvidenceClass,
    as_of: date,
    published_on: date,
    cutoff: date,
    listed: Iterable[str],
    unmatched: Iterable[str],
    intervals: Iterable[MembershipInterval],
    citation: Citation | None,
) -> SnapshotReconciliation:
    """``listed`` security ids compared with the roster on ``as_of``."""
    listed = set(listed)
    reconstructed = roster(intervals, as_of)
    return SnapshotReconciliation(
        snapshot_id=snapshot_id,
        source_id=source_id,
        evidence_class=evidence_class,
        as_of=as_of,
        published_on=published_on,
        withheld=published_on > cutoff,
        matched=tuple(sorted(listed & reconstructed)),
        reconstructed_only=tuple(sorted(reconstructed - listed)),
        snapshot_only=tuple(sorted(listed - reconstructed)),
        unmatched=tuple(sorted(set(unmatched))),
        citation=citation,
    )


def match_holdings(
    report: HoldingsReport,
    securities: Iterable[SecurityRecord],
    overrides: Iterable[Override],
) -> tuple[set[str], list[str]]:
    """The security ids a fund's common-equity holdings match, and the names of
    holdings that match no single security."""
    securities = tuple(securities)
    aliases = {
        o.holding_name: o.security_id
        for o in overrides
        if o.kind is OverrideKind.HOLDING_ALIAS
    }
    matched: set[str] = set()
    unmatched: list[str] = []
    for holding in report.holdings:
        if holding.asset_category not in (None, EQUITY_COMMON):
            continue
        if holding.name in aliases:
            matched.add(aliases[holding.name])
            continue
        found = {
            security.security_id
            for security in securities
            if any(covered(i.name, holding.name) for i in security.identities)
        }
        if len(found) == 1:
            matched |= found
        else:
            unmatched.append(holding.name)
    return matched, unmatched


def _order(fund: FundFiling) -> tuple[date, float, str]:
    accepted = fund.filing.accepted_at
    return (
        fund.filing.filing_date,
        accepted.timestamp() if accepted else 0.0,
        fund.filing.accession,
    )


def current_filings(
    filings: Iterable[FundFiling], cutoff: date
) -> tuple[list[FundFiling], list[Finding]]:
    """The filings to compare, and a ``superseded`` finding for each replaced one.

    Per report date, the latest filing filed on or before the cutoff is compared;
    filings after the cutoff are compared too, and reported as withheld.
    """
    by_date: dict[date, list[FundFiling]] = defaultdict(list)
    for filing in filings:
        by_date[filing.report.report_date].append(filing)
    current, findings = [], []
    for report_date in sorted(by_date):
        group = sorted(by_date[report_date], key=_order)
        timely = [f for f in group if f.filing.filing_date <= cutoff]
        current.extend(timely[-1:])
        current.extend(f for f in group if f.filing.filing_date > cutoff)
        for replaced in timely[:-1]:
            findings.append(
                make_finding(
                    FindingKind.SUPERSEDED,
                    replaced.filing.accession,
                    f"{replaced.filing.accession} ({replaced.filing.form}) for"
                    f" {report_date} is replaced by {timely[-1].filing.accession}",
                    blocking=False,
                )
            )
    return current, findings


def difference_findings(
    reconciliations: Iterable[SnapshotReconciliation],
) -> tuple[Finding, ...]:
    """A finding for each disagreeing snapshot; blocking unless it is a check list
    or was first published after the cutoff."""
    findings = []
    for r in reconciliations:
        if r.agrees:
            continue
        parts = [
            f"reconstruction only: {', '.join(r.reconstructed_only) or 'none'}",
            f"snapshot only: {', '.join(r.snapshot_only) or 'none'}",
            f"unmatched: {', '.join(r.unmatched) or 'none'}",
        ]
        findings.append(
            make_finding(
                FindingKind.DIFFERENCE,
                r.snapshot_id,
                f"{r.snapshot_id} on {r.as_of}: {'; '.join(parts)}",
                blocking=not r.withheld
                and r.evidence_class is not EvidenceClass.USER_SUPPLIED,
                evidence_ids=[r.snapshot_id],
            )
        )
    return tuple(findings)


def _quarter(day: date) -> tuple[int, int]:
    return day.year, (day.month - 1) // 3 + 1


def gap_findings(
    reconciliations: Iterable[SnapshotReconciliation], *, start: date, cutoff: date
) -> tuple[Finding, ...]:
    """A ``gap`` for each calendar quarter from ``start`` through ``cutoff`` with no
    timely corroborating snapshot."""
    covered_quarters = {
        _quarter(r.as_of)
        for r in reconciliations
        if not r.withheld and r.evidence_class is not EvidenceClass.USER_SUPPLIED
    }
    findings = []
    year, quarter = _quarter(start)
    while (year, quarter) <= _quarter(cutoff):
        if (year, quarter) not in covered_quarters:
            findings.append(
                make_finding(
                    FindingKind.GAP,
                    f"{year}q{quarter}",
                    f"no corroborating snapshot is dated in {year}Q{quarter}",
                    blocking=False,
                )
            )
        year, quarter = (year + 1, 1) if quarter == 4 else (year, quarter + 1)
    return tuple(findings)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_corroboration.py -q`

Expected: `7 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/corroboration.py packages/earnings-ingestion/tests/test_cohort_corroboration.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `849 passed, 23 deselected`;
`All checks passed!` and `193 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/cohort/corroboration.py packages/earnings-ingestion/tests/test_cohort_corroboration.py
git commit -m "feat(ingestion): reconcile snapshots and fund holdings with the reconstruction"
```

---
### Task 12: The build, the freeze, and the synthetic cohort

**`build`** fetches nothing (A §410). Every fact it uses sits in a committed file or
a saved artifact, and it runs in five steps:

1. **Verify every citation.** It checks each item's register role and its stored
   artifact, and that the item's URL is where the artifact came from. It checks each
   row's locator, and that the row's name and ticker occur in the cited text, and
   the change date's locator. A change must be `official`. It checks every stored
   override citation too. What no review can settle raises `CohortError`, listing
   every problem.
2. **Reconstruct.** It chooses the anchor, or records why none can serve (P6-11),
   turns the anchor and the changes into statements, and reconstructs and counts
   (P6-6, P6-7).
3. **Resolve.** It reads SEC's saved ticker list and submissions, and resolves the
   securities, from rows published by the cutoff only (P6-8, P6-12).
4. **Corroborate.** It compares each corroborating snapshot, each current fund
   filing, and each check list with the reconstruction (P6-10).
5. **Report.** It collects the findings, applies acknowledgements, and assembles
   the assertions, the report, the candidate issuers (P6-13), and every used
   source's rights (P6-15).

**`freeze`** refuses on a blocking finding or a stale acknowledgement. It keeps an
identical build's version, and writes new content as the next version, through
`write_new` (P6-14). `load_manifest` reads a manifest back without any saved
artifact, and rechecks its hash.

**The synthetic cohort** (P6-19) is an invented four-member index. Its evidence
exercises every Stage 4 P-VF case:

- **Sources.** `synthetic-roster` is `secondary`, serving as anchor and
  corroboration; `synthetic-index` is `official`; `synthetic-fund` is `etf_proxy`,
  whose N-PORT documents sit at SEC paths; and `user-list` is `user_supplied`.
- **Securities:**
  - `acme-common` changes ticker from ACMX to ACME;
  - `borealis-common` is cited by a former SEC name, and is removed in November
    2024;
  - `corvid-common` has two notices with conflicting dates, and a
    `reject_assertion` settles them;
  - `dynamo-class-a` and `dynamo-class-b` are two securities of one CIK;
  - `eastfield-common` is resolved by a `set_issuer` override, and removed in June
    2026;
  - `fenwick-common` is added only by a notice published after the cutoff, so it
    is withheld.
- **Evidence.**
  - A roster that lags a change by one day draws a `difference`, which is
    acknowledged.
  - An amended N-PORT supersedes its original.
  - A filing after the cutoff is withheld.
  - The user list, published after the cutoff, is reported only.
- **Generation.** `write_synthetic_cohort` writes the registers, the saved artifacts,
  and the curated files. It builds once to read the lagging roster's finding digest,
  appends the acknowledgement, and freezes. The conftest's session fixture
  `synthetic_cohort` generates it once per test session. `cohort_repo` gives each
  test a private copy.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py`,
  `cohort/freeze.py`, and `cohort/synthetic.py`.
- Modify:
  - `packages/earnings-ingestion/tests/conftest.py` (replaced whole);
  - `packages/earnings-ingestion/tests/test_import_boundaries.py` (replaced whole,
    block 2 of 3);
  - `docs/data-dictionary.md` (appended, part 4 of 4).
- Test (create): `packages/earnings-ingestion/tests/test_cohort_build.py`.

**Interfaces:**

- Consumes: Tasks 1 and 4–11: the store, the SEC readers and URL builders, and the
  records, register, config, locators, findings, intervals, resolution, and
  corroboration.
- Produces:
  - `cohort/build.py`:
    - `COHORT_STORE`, which is `data/raw/cohort`, and `LIMITATIONS`;
    - `CohortError(problems: list[str])`;
    - `content_hash(manifest) -> str`;
    - `CohortBuild`, with `manifest(version, created_at) -> UniverseManifest`, the
      `content_hash` property, and `report` and `stale_acknowledgements`;
    - `build(repo, *, config_dir=UNIVERSE_DIR, store_root=COHORT_STORE, register=MEMBERSHIP_REGISTER, sec_register=SEC_REGISTER) -> CohortBuild`.
  - `cohort/freeze.py`:
    - `MANIFESTS`;
    - `FreezeRefused(blocking, stale)` and `Frozen(manifest, path, created)`;
    - `manifest_path(directory, universe_id, version) -> Path`;
    - `serialize(manifest) -> bytes`;
    - `load_manifest(path) -> UniverseManifest`;
    - `frozen_manifests(directory, universe_id) -> list[UniverseManifest]`;
    - `freeze(build, directory, *, now) -> Frozen`.
  - `cohort/synthetic.py`:
    - `FIXTURE_DIR`, which is `tests/fixtures/cohort`;
    - `UNIVERSE_ID = "djia-synthetic"`;
    - `build_options(directory=FIXTURE_DIR) -> dict[str, Path]`, the keyword
      arguments `build` takes for the synthetic cohort;
    - `write_synthetic_cohort(repo, directory=FIXTURE_DIR) -> Path`, which returns
      the frozen manifest's path.
  - `conftest.py`: the fixtures `synthetic_cohort`, per session, and `cohort_repo`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_cohort_build.py`:

```python
"""The build and the freeze, on copies of the synthetic cohort (P §Failure handling)."""

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.cohort.build import CohortError, build
from earnings_ingestion.cohort.freeze import (
    FreezeRefused,
    freeze,
    frozen_manifests,
    load_manifest,
)
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, build_options
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.data import FILING_COLUMNS
from earnings_ingestion.sec.urls import COMPANY_TICKERS_URL, submissions_url

DIRECTORY = FIXTURE_DIR
OPTIONS = build_options()
LATER = datetime(2026, 10, 1, tzinfo=UTC)
SYNTHETIC = {
    "rights_status": RightsStatus.REDISTRIBUTABLE,
    "rights_basis": "synthetic test data, invented for this repository",
}


def save(
    store: ArtifactStore, source_id: str, url: str, body: bytes, media: str
) -> str:
    """Save ``body`` as retrieved a day after the synthetic cohort's artifacts."""
    retrieval = Retrieval(
        request_url=url,
        final_url=url,
        retrieved_at=datetime(2026, 9, 28, 12, 0, tzinfo=UTC),
        retrieval_method=RetrievalMethod.HTTP,
        http_status=200,
        media_type=media,
        content_type=media,
        byte_count=len(body),
        sha256=sha256_hex(body),
    )
    return store.put(source_id, body, retrieval, **SYNTHETIC).content_sha256


@pytest.fixture
def repo(cohort_repo: Path) -> Path:
    return cohort_repo


def edit(repo: Path, name: str, old: str, new: str) -> None:
    path = repo / DIRECTORY / name
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def blocking_ids(repo: Path) -> set[str]:
    return {finding.finding_id for finding in build(repo, **OPTIONS).report.blocking}


def test_the_reviewed_cohort_holds_no_blocking_finding(repo) -> None:
    assert blocking_ids(repo) == set()


def test_before_review_its_findings_hold_the_freeze(repo) -> None:
    (repo / DIRECTORY / "overrides.toml").unlink()
    held = build(repo, **OPTIONS)
    ids = {finding.finding_id for finding in held.report.blocking}
    assert {
        "membership_conflict:corvid-common",
        "member_count:2024-11-08",
        "identity:eastfield-common",
        "difference:roster-2024-11-08",
    } <= ids
    with pytest.raises(FreezeRefused, match="membership_conflict:corvid-common"):
        freeze(held, repo / DIRECTORY / "manifests", now=LATER)


def test_a_missing_anchor_refuses_the_freeze_with_its_reason(repo) -> None:
    edit(repo, "evidence.toml", 'role = "anchor"', 'role = "corroboration"')
    held = build(repo, **OPTIONS)
    missing = [f for f in held.report.blocking if f.kind == "missing_anchor"]
    assert [f.detail for f in missing] == ["no anchor snapshot is curated"]
    with pytest.raises(FreezeRefused, match="missing_anchor:anchor"):
        freeze(held, repo / DIRECTORY / "manifests", now=LATER)


def test_a_later_snapshot_is_never_backdated_into_the_anchor(repo) -> None:
    edit(
        repo, "evidence.toml", "published_on = 2024-06-20", "published_on = 2024-07-15"
    )
    (missing,) = [
        f for f in build(repo, **OPTIONS).report.blocking if f.kind == "missing_anchor"
    ]
    assert "a later snapshot is never backdated" in missing.detail


def test_fund_holdings_are_never_the_roster(repo) -> None:
    register = "membership-source-register.toml"
    edit(repo, register, 'evidence_class = "secondary"', 'evidence_class = "etf_proxy"')
    (missing,) = [
        f for f in build(repo, **OPTIONS).report.blocking if f.kind == "missing_anchor"
    ]
    assert "etf_proxy evidence is not a roster" in missing.detail


def test_a_missing_artifact_stops_the_build(repo) -> None:
    for path in (repo / DIRECTORY / "raw" / "synthetic-roster").glob("*.html"):
        path.unlink()
    with pytest.raises(CohortError, match="no artifact"):
        build(repo, **OPTIONS)


def test_edited_bytes_stop_the_build(repo) -> None:
    page = next((repo / DIRECTORY / "raw" / "synthetic-index").glob("*.html"))
    page.write_bytes(page.read_bytes().replace(b"synthetic", b"edited"))
    with pytest.raises(CohortError, match="no longer hashes to its name"):
        build(repo, **OPTIONS)


def test_a_fact_the_cited_text_does_not_state_stops_the_build(repo) -> None:
    edit(repo, "evidence.toml", 'ticker = "ACMX"', 'ticker = "ACMQ"')
    with pytest.raises(CohortError, match="does not state 'ACMQ'"):
        build(repo, **OPTIONS)


def test_an_unregistered_source_stops_the_build(repo) -> None:
    edit(
        repo, "evidence.toml", 'source_id = "synthetic-index"', 'source_id = "nowhere"'
    )
    with pytest.raises(CohortError, match="not in the membership source register"):
        build(repo, **OPTIONS)


def test_an_acknowledgement_binds_to_what_the_reviewer_read(repo) -> None:
    path = repo / DIRECTORY / "overrides.toml"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'finding_digest = "[0-9a-f]{64}"', f'finding_digest = "{"0" * 64}"', text
    )
    path.write_text(text, encoding="utf-8")
    stale = build(repo, **OPTIONS)
    assert stale.stale_acknowledgements == ("ack-lagging-revision",)
    assert "difference:roster-2024-11-08" in {
        f.finding_id for f in stale.report.blocking
    }
    with pytest.raises(FreezeRefused, match="acknowledges a finding that has changed"):
        freeze(stale, repo / DIRECTORY / "manifests", now=LATER)


def test_identical_content_keeps_its_version(repo) -> None:
    manifests = repo / DIRECTORY / "manifests"
    again = freeze(build(repo, **OPTIONS), manifests, now=LATER)
    assert (again.created, again.manifest.definition.universe_version) == (False, 1)
    assert [path.name for path in manifests.iterdir()] == ["djia-synthetic-v1.json"]


def test_changed_evidence_is_a_new_version_beside_the_old(repo) -> None:
    manifests = repo / DIRECTORY / "manifests"
    first = (manifests / "djia-synthetic-v1.json").read_bytes()
    edit(
        repo,
        "universe.toml",
        'selection_policy_version = "djia-pilot/1"',
        'selection_policy_version = "djia-pilot/2"',
    )
    second = freeze(build(repo, **OPTIONS), manifests, now=LATER)
    assert (second.created, second.path.name) == (True, "djia-synthetic-v2.json")
    assert (manifests / "djia-synthetic-v1.json").read_bytes() == first
    versions = [
        m.definition.universe_version
        for m in frozen_manifests(manifests, "djia-synthetic")
    ]
    assert versions == [1, 2]


def test_a_frozen_manifest_loads_without_any_saved_artifact(repo) -> None:
    shutil.rmtree(repo / DIRECTORY / "raw")
    manifest = load_manifest(repo / DIRECTORY / "manifests" / "djia-synthetic-v1.json")
    assert manifest.definition.selection_policy_version == "djia-pilot/1"
    assert all(len(issuer.cik) == 10 for issuer in manifest.issuers)


def test_a_tampered_manifest_is_refused(repo) -> None:
    path = repo / DIRECTORY / "manifests" / "djia-synthetic-v1.json"
    path.write_text(path.read_text().replace('"2024-11-08"', '"2024-11-09"', 1))
    with pytest.raises(ValueError, match="does not hash to its content_hash"):
        load_manifest(path)


def test_a_retained_unresolved_security_is_excluded_and_the_freeze_proceeds(
    repo,
) -> None:
    edit(repo, "overrides.toml", 'kind = "set_issuer"', 'kind = "retain_unresolved"')
    edit(repo, "overrides.toml", 'cik = "0009990006"\n', "")
    kept = build(repo, **OPTIONS)
    (mapping,) = [m for m in kept.mappings if m.security_id == "eastfield-common"]
    assert (mapping.status, mapping.override_id) == (
        "retained_unresolved",
        "eastfield-issuer",
    )
    assert "cik-0009990006" not in kept.candidate_issuer_ids
    (finding,) = [f for f in kept.report.findings if f.kind == "identity"]
    assert finding.resolved_by == ("eastfield-issuer",)
    frozen = freeze(kept, repo / DIRECTORY / "manifests", now=LATER)
    assert frozen.manifest.definition.universe_version == 2


def test_a_row_published_after_the_cutoff_never_changes_an_identity(repo) -> None:
    root = repo / DIRECTORY
    store = ArtifactStore(root / "raw", repo)
    tickers = store.latest("sec-edgar", COMPANY_TICKERS_URL, **SYNTHETIC)
    rival = json.loads(tickers.body) | {
        "99": {"cik_str": 9990008, "ticker": "ACMR", "title": "Acme Industrial Rival"}
    }
    save(
        store,
        "sec-edgar",
        COMPANY_TICKERS_URL,
        json.dumps(rival).encode(),
        "application/json",
    )
    filings = {column: [] for column in FILING_COLUMNS}
    rival_record = {
        "cik": "9990008",
        "name": "Acme Industrial Rival Inc",
        "tickers": ["ACMR"],
        "filings": {"recent": filings, "files": []},
    }
    save(
        store,
        "sec-edgar",
        submissions_url(9990008),
        json.dumps(rival_record).encode(),
        "application/json",
    )
    page = b"<html><body><p>Acme Industrial (ACMR) will join on October 9, 2026.</p></body></html>"
    url = "https://index.example/notices/index-2026-09-30"
    sha = save(store, "synthetic-index", url, page, "text/html")
    text = ArtifactText(page, "text/html")
    row, when = text.find("Acme Industrial (ACMR)"), text.find("October 9, 2026")
    with (root / "evidence.toml").open("a", encoding="utf-8") as out:
        out.write(
            f'\n[[changes]]\nevidence_id = "index-2026-09-30"\nsource_id = "synthetic-index"\n'
            f'url = "{url}"\nartifact_sha256 = "{sha}"\n'
            f'canonical_sha256 = "{text.canonical[1]}"\nannounced_on = 2026-09-30\n'
            f"published_on = 2026-09-30\neffective_on = 2026-10-09\n"
            f'timing = "unspecified"\ndate_span = [{when.start}, {when.end}]\n'
            f'date_cited_sha256 = "{when.cited_sha256}"\n\n[[changes.entries]]\n'
            f'action = "added"\nsecurity_id = "acme-common"\nname = "Acme Industrial"\n'
            f'ticker = "ACMR"\nspan = [{row.start}, {row.end}]\n'
            f'cited_sha256 = "{row.cited_sha256}"\n'
        )
    later = build(repo, **OPTIONS)
    (acme,) = [m for m in later.mappings if m.security_id == "acme-common"]
    assert (acme.status, acme.cik) == ("resolved", "0009990001")
    assert "ACMR" in {i.ticker for s in later.securities for i in s.identities}
    assert not later.report.blocking


def test_the_manifest_records_rights_for_every_source_it_cites(repo) -> None:
    manifest = load_manifest(repo / DIRECTORY / "manifests" / "djia-synthetic-v1.json")
    cited = {a.source_id for a in manifest.assertions}
    cited |= {r.source_id for r in manifest.report.reconciliations}
    cited |= {
        c.source_id
        for m in manifest.mappings
        for candidate in m.candidates
        for c in candidate.citations
    }
    assert {s.source_id for s in manifest.sources} == cited
    assert {s.source_id: s.rights_status for s in manifest.sources}["sec-edgar"] == (
        "local_only"
    )
```

Replace `packages/earnings-ingestion/tests/conftest.py` with:

```python
"""Shared test data. Plan 5: a small completed capture, its layout payload, and
builders for synthetic layout metadata. Plan 6: the synthetic cohort."""

import copy
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.browser.metadata import METADATA_VERSION, parse_metadata
from earnings_ingestion.browser.policy import ISOLATED_1
from earnings_ingestion.browser.records import (
    CaptureStatus,
    RenderedCapture,
    layout_hash,
)
from earnings_ingestion.browser.renderer import (
    CaptureEnvironment,
    cache_key,
    capture_id,
)
from earnings_ingestion.cohort.synthetic import write_synthetic_cohort

ENVIRONMENT = CaptureEnvironment(
    browser_engine="Chrome for Testing",
    browser_version="154.0.8037.57",
    driver_version="154.0.8037.57",
    selenium_version="4.49.0",
    os_name="Darwin",
    os_version="26.6.2",
    architecture="arm64",
)
PAYLOAD = {
    "blocks": [
        {
            "tag": "p",
            "display": "block",
            "heading_level": None,
            "list_item": False,
            "list_depth": 0,
            "table": None,
            "row": None,
            "cell": None,
            "x": 8,
            "y": 16,
            "width": 1264,
            "height": 18,
            "runs": [
                {
                    "text": "Revenue rose.",
                    "br": False,
                    "visible": True,
                    "bold": False,
                    "underline": False,
                    "superscript": False,
                    "symbol_font": False,
                    "font_size": 16,
                }
            ],
        }
    ],
    "tables": [],
}


def build_capture(**changes: object) -> RenderedCapture:
    layout = changes.pop("layout", parse_metadata(PAYLOAD))
    text = changes.pop("rendered_text", "Revenue rose.")
    raw = b"<p>Revenue rose.</p>"
    key = cache_key(sha256_hex(raw), ISOLATED_1, ENVIRONMENT)
    fields = {
        "capture_id": capture_id("release", ISOLATED_1, key),
        "cache_key": key,
        "source_document_id": "release",
        "raw_sha256": sha256_hex(raw),
        "capture_policy": "isolated",
        "capture_policy_version": "1",
        "metadata_version": METADATA_VERSION,
        "browser_engine": "Chrome for Testing",
        "browser_version": "154.0.8037.57",
        "driver_version": "154.0.8037.57",
        "selenium_version": "4.49.0",
        "os_name": "Darwin",
        "os_version": "26.6.2",
        "architecture": "arm64",
        "viewport_width": 1280,
        "viewport_height": 1024,
        "device_scale_factor": 1,
        "locale": "en-US",
        "timezone": "UTC",
        "font_set": "Darwin 26.6.2 system fonts",
        "document_charset": "UTF-8",
        "script_policy": "disabled",
        "network_policy": "blocked",
        "image_policy": "blocked",
        "missing_resource_policy": "recorded",
        "rendered_text": text,
        "rendered_text_sha256": sha256_hex(text.encode("utf-8")),
        "layout": layout,
        "layout_sha256": layout_hash(layout),
        "screenshots": (),
        "blocked_requests": (),
        "captured_at": datetime(2026, 9, 26, 12, 0, tzinfo=UTC),
        "duration_seconds": 0.8,
        "status": CaptureStatus.COMPLETED,
        "reason": None,
        "detail": "",
    }
    fields.update(changes)
    return RenderedCapture(**fields)


@pytest.fixture
def make_capture() -> Callable[..., RenderedCapture]:
    """A factory: a completed capture of one paragraph, with any field replaced."""
    return build_capture


@pytest.fixture
def payload() -> dict:
    """The layout-metadata script's result for that paragraph, safe to change."""
    return copy.deepcopy(PAYLOAD)


class LayoutParts:
    """Builders for the layout-metadata script's output: runs, blocks, and tables."""

    @staticmethod
    def run(text: str, **style: object) -> dict:
        base = {
            "text": text,
            "br": False,
            "visible": True,
            "bold": False,
            "underline": False,
            "superscript": False,
            "symbol_font": False,
            "font_size": 16,
        }
        return {**base, **style}

    @staticmethod
    def br() -> dict:
        return LayoutParts.run("\n", br=True)

    @staticmethod
    def block(
        *runs: dict,
        tag: str = "p",
        cell: tuple[int, int, int] | None = None,
        **context: object,
    ) -> dict:
        base = {
            "tag": tag,
            "display": "block",
            "heading_level": None,
            "list_item": False,
            "list_depth": 0,
            "table": None if cell is None else cell[0],
            "row": None if cell is None else cell[1],
            "cell": None if cell is None else cell[2],
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 10,
            "runs": list(runs),
        }
        return {**base, **context}

    @staticmethod
    def table(
        *rows: list[int],
        parent: tuple[int, int, int] | None = None,
        head: int = 0,
        th: bool = False,
    ) -> dict:
        """Rows as colspans, one per rendered cell; the first ``head`` rows in thead."""
        return {
            "parent_table": None if parent is None else parent[0],
            "parent_row": None if parent is None else parent[1],
            "parent_cell": None if parent is None else parent[2],
            "rows": [
                {
                    "head": index < head,
                    "cells": [
                        {"header": th, "colspan": span, "rowspan": 1} for span in row
                    ],
                }
                for index, row in enumerate(rows)
            ],
        }

    @staticmethod
    def cells(rows: list[list[str]], table_index: int = 0) -> list[dict]:
        """One ``td`` block per non-empty cell text, in row-major order."""
        return [
            LayoutParts.block(LayoutParts.run(text), tag="td", cell=(table_index, r, c))
            for r, row in enumerate(rows)
            for c, text in enumerate(row)
            if text
        ]


@pytest.fixture
def parts() -> type[LayoutParts]:
    return LayoutParts


@pytest.fixture(scope="session")
def synthetic_cohort(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A repository holding the synthetic cohort, generated once; never change it."""
    repo = tmp_path_factory.mktemp("synthetic-cohort")
    write_synthetic_cohort(repo)
    return repo


@pytest.fixture
def cohort_repo(synthetic_cohort: Path, tmp_path: Path) -> Path:
    """A private copy of the synthetic cohort's repository, safe to change."""
    shutil.copytree(synthetic_cohort, tmp_path, dirs_exist_ok=True)
    return tmp_path
```

Replace `packages/earnings-ingestion/tests/test_import_boundaries.py` with:

```python
"""earnings-ingestion imports neither earnings-themes nor the application, and no
browser: browser capture stays behind an optional extra (A §173; B3).

Only ``earnings_ingestion.browser.selenium_capture`` may load a browser library, and
only when something imports it; tests/contracts/test_import_scan.py checks the source
statically as well. The cohort's offline path, from saved artifacts to a frozen
manifest, loads no network client (A §410).
"""

import json
import subprocess
import sys

import pytest

FORBIDDEN = {
    "earnings_themes",
    "earnings_pipeline",
    "selenium",
    "websocket",
    "playwright",
    "pyppeteer",
}


def modules_loaded_by(module: str) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing ``module``."""
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return {name.partition(".")[0] for name in json.loads(result.stdout)}


@pytest.mark.parametrize(
    "module",
    [
        "earnings_ingestion",
        "earnings_ingestion.browser",
        "earnings_ingestion.browser.install",
        "earnings_ingestion.browser.renderer",
        "earnings_ingestion.browser.serialize",
        "earnings_ingestion.browser.store",
        "earnings_ingestion.layout",
        "earnings_ingestion.layout.extract",
        "earnings_ingestion.fetch.client",
        "earnings_ingestion.fetch.robots",
        "earnings_ingestion.sec.client",
        "earnings_ingestion.cohort.build",
    ],
)
def test_importing_ingestion_loads_nothing_forbidden(module: str) -> None:
    assert modules_loaded_by(module) & FORBIDDEN == set()


NETWORK = {
    "httpx",
    "earnings_ingestion.fetch.client",
    "earnings_ingestion.sec.client",
    "earnings_ingestion.cohort.web",
}


def full_modules_loaded_by(module: str) -> set[str]:
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return set(json.loads(result.stdout))


@pytest.mark.parametrize(
    "module",
    [
        "earnings_ingestion.cohort.build",
        "earnings_ingestion.cohort.freeze",
        "earnings_ingestion.cohort.synthetic",
        "earnings_ingestion.sec.data",
        "earnings_ingestion.sec.urls",
        "earnings_ingestion.fetch.store",
    ],
)
def test_the_offline_cohort_path_loads_no_network_client(module: str) -> None:
    """Building and freezing read saved bytes; they cannot reach the network (A §410)."""
    assert full_modules_loaded_by(module) & NETWORK == set()
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py packages/earnings-ingestion/tests/test_import_boundaries.py 2`.
It adds `cohort.build` to the modules that load nothing forbidden. It also checks
that the offline path loads no network client: `build`, `freeze`, `synthetic`, the
SEC readers and URL builders, and the store.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_import_boundaries.py -q`

Expected: FAIL. Every test module in `packages/earnings-ingestion/tests/` shares the
conftest, so none loads: pytest reports `ImportError while loading conftest` with
`No module named 'earnings_ingestion.cohort.synthetic'`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py`:

```python
"""Build the cohort from the curated files, the registers, and saved artifacts.

``build`` fetches nothing (A §410): every fact it uses is in a committed file or an
artifact saved under ``data/raw/cohort/``. It stops with ``CohortError`` on what no
review can settle: an unregistered source, a missing artifact, or a citation that no
longer cites what it hashed. Everything a reviewer can decide becomes a finding.

1. Verify every citation in ``evidence.toml`` and every stored override citation.
2. Turn the anchor's rows and the changes into statements and reconstruct intervals.
3. Resolve every security to an issuer from SEC's saved records.
4. Compare each snapshot, fund filing, and check list with the reconstruction.
5. Collect the findings, apply acknowledgements, and assemble the report.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from earnings_ingestion.canonical import CANONICALIZATION_VERSION
from earnings_ingestion.cohort.config import (
    UNIVERSE_DIR,
    ChangeEvidence,
    CohortConfig,
    Row,
    SnapshotEvidence,
    load_cohort_config,
)
from earnings_ingestion.cohort.corroboration import (
    FundFiling,
    current_filings,
    difference_findings,
    gap_findings,
    match_holdings,
    reconcile,
)
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.findings import acknowledge, make_finding
from earnings_ingestion.cohort.intervals import Statement, count_findings, reconstruct
from earnings_ingestion.cohort.locators import (
    ArtifactText,
    CitableArtifact,
    LocatorError,
)
from earnings_ingestion.cohort.records import (
    AssertedAction,
    BoundTiming,
    CitedIdentity,
    CohortReport,
    EvidenceClass,
    EvidenceLocator,
    Finding,
    FindingKind,
    Issuer,
    IssuerMapping,
    LocatorKind,
    MembershipAssertion,
    MembershipInterval,
    Override,
    OverrideKind,
    SecurityRecord,
    SnapshotReconciliation,
    SourceRights,
    SourceRole,
    UniverseDefinition,
    UniverseManifest,
)
from earnings_ingestion.cohort.register import (
    MEMBERSHIP_REGISTER,
    SEC_REGISTER,
    SEC_SOURCE_ID,
    RegisterEntry,
    Registers,
    load_registers,
)
from earnings_ingestion.cohort.resolution import SecEvidence, resolve
from earnings_ingestion.fetch.store import ArtifactStore, StoredArtifact
from earnings_ingestion.sec.data import (
    SecDataError,
    raw_document_name,
    read_company_tickers,
    read_nport_holdings,
    read_submissions,
    read_submissions_page,
)
from earnings_ingestion.sec.urls import (
    COMPANY_TICKERS_URL,
    archive_url,
    submissions_page_url,
    submissions_url,
)

COHORT_STORE = Path("data") / "raw" / "cohort"
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
LIMITATIONS = (
    (
        "Fund holdings are an ETF proxy: they corroborate the reconstruction and"
        " never add or remove a member."
    ),
    (
        "SEC identity records were retrieved after the cutoff: they establish issuer"
        " identity, never membership."
    ),
    (
        "Intervals are resolved to the day; ordering a change and a release on one"
        " day is Stage 5's eligibility decision."
    ),
)


class CohortError(ValueError):
    """Problems no review can settle; the build stops and lists every one."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("; ".join(problems))


@dataclass(frozen=True)
class _Item:
    """A verified snapshot or change, with its artifact and row locators."""

    config: SnapshotEvidence | ChangeEvidence
    entry: RegisterEntry
    stored: StoredArtifact
    rows: dict[tuple[str, str], EvidenceLocator]
    date_locator: EvidenceLocator | None

    @property
    def retrieved_at(self) -> datetime:
        return self.stored.retrievals[0].retrieved_at

    def citation(self) -> CitableArtifact:
        return CitableArtifact(
            source_id=self.config.source_id,
            url=self.config.url,
            artifact=self.stored.ref,
            retrieved_at=self.retrieved_at,
            text=ArtifactText(self.stored.body, self.stored.ref.media_type),
        )


def _is_anchor(item: _Item) -> bool:
    return isinstance(item.config, SnapshotEvidence) and item.config.role == "anchor"


def _members(item: SnapshotEvidence | ChangeEvidence) -> tuple[Row, ...]:
    return item.members if isinstance(item, SnapshotEvidence) else item.entries


def _action(row: Row) -> str:
    return getattr(row, "action", AssertedAction.MEMBER_AT.value)


def content_hash(manifest: UniverseManifest) -> str:
    """SHA-256 of a manifest's canonical JSON without its version, hash, and time."""
    data = manifest.model_dump(mode="json")
    for key in ("universe_version", "content_hash", "created_at"):
        del data["definition"][key]
    return digest(data)


@dataclass(frozen=True)
class CohortBuild:
    """Everything a manifest holds except its version, content hash, and time."""

    config: CohortConfig
    source_register_version: str
    sources: tuple[SourceRights, ...]
    securities: tuple[SecurityRecord, ...]
    assertions: tuple[MembershipAssertion, ...]
    intervals: tuple[MembershipInterval, ...]
    mappings: tuple[IssuerMapping, ...]
    issuers: tuple[Issuer, ...]
    candidate_issuer_ids: tuple[str, ...]
    overrides: tuple[Override, ...]
    report: CohortReport
    stale_acknowledgements: tuple[str, ...] = field(default=())

    def manifest(self, version: int, created_at: datetime) -> UniverseManifest:
        universe = self.config.universe
        draft = UniverseManifest(
            definition=UniverseDefinition(
                universe_id=universe.universe_id,
                universe_version=version,
                universe_name=universe.universe_name,
                period_end_start=universe.period_end_start,
                period_end_stop=universe.period_end_stop,
                public_information_cutoff=universe.public_information_cutoff,
                membership_reference=universe.membership_reference,
                expected_member_count=universe.expected_member_count,
                source_register_version=self.source_register_version,
                selection_policy_version=universe.selection_policy_version,
                content_hash="0" * 64,
                created_at=created_at,
            ),
            sources=self.sources,
            securities=self.securities,
            assertions=self.assertions,
            intervals=self.intervals,
            mappings=self.mappings,
            issuers=self.issuers,
            candidate_issuer_ids=self.candidate_issuer_ids,
            overrides=self.overrides,
            report=self.report,
        )
        definition = draft.definition.model_copy(
            update={"content_hash": content_hash(draft)}
        )
        return draft.model_copy(update={"definition": definition})

    @property
    def content_hash(self) -> str:
        return self.manifest(1, EPOCH).definition.content_hash


def build(
    repo: Path,
    *,
    config_dir: Path = UNIVERSE_DIR,
    store_root: Path = COHORT_STORE,
    register: Path = MEMBERSHIP_REGISTER,
    sec_register: Path = SEC_REGISTER,
) -> CohortBuild:
    """The cohort that ``repo``'s committed files and saved artifacts support."""
    config = load_cohort_config(repo / config_dir)
    registers = load_registers(repo, register, sec_register)
    return _Builder(config, registers, ArtifactStore(repo / store_root, repo)).run()


class _Builder:
    def __init__(
        self, config: CohortConfig, registers: Registers, store: ArtifactStore
    ):
        self.config = config
        self.universe = config.universe
        self.cutoff = config.universe.public_information_cutoff
        self.registers = registers
        self.store = store
        self.problems: list[str] = []
        self.used = {SEC_SOURCE_ID}
        self.overrides = config.overrides.overrides

    # -- step 1: citations ---------------------------------------------------

    def _entry(self, source_id: str, role: SourceRole) -> RegisterEntry | None:
        try:
            entry = self.registers.entry(source_id)
        except ValueError as exc:
            self.problems.append(str(exc))
            return None
        if role not in entry.roles:
            self.problems.append(f"source {source_id!r} is not registered for {role}")
            return None
        self.used.add(source_id)
        return entry

    def _stored(self, source_id: str, sha256: str) -> StoredArtifact | None:
        try:
            rights = self.registers.rights(source_id)
            stored = self.store.get(
                source_id,
                sha256,
                rights_status=rights.rights_status,
                rights_basis=rights.rights_basis,
            )
        except (FileNotFoundError, ValueError) as exc:
            self.problems.append(str(exc))
            return None
        self.used.add(source_id)
        return stored

    def _latest(self, source_id: str, url: str) -> StoredArtifact | None:
        try:
            rights = self.registers.rights(source_id)
            stored = self.store.latest(
                source_id,
                url,
                rights_status=rights.rights_status,
                rights_basis=rights.rights_basis,
            )
        except (FileNotFoundError, ValueError) as exc:
            self.problems.append(str(exc))
            return None
        if stored is None:
            self.problems.append(f"nothing saved from {url} for {source_id}")
            return None
        self.used.add(source_id)
        return stored

    def _item(self, item: SnapshotEvidence | ChangeEvidence) -> _Item | None:
        if isinstance(item, ChangeEvidence):
            role = SourceRole.CHANGE
        else:
            role = SourceRole(item.role)
        entry = self._entry(item.source_id, role)
        stored = (
            None
            if entry is None
            else self._stored(item.source_id, item.artifact_sha256)
        )
        if entry is None or stored is None:
            return None
        where = item.evidence_id
        if (
            role is SourceRole.CHANGE
            and entry.evidence_class is not EvidenceClass.OFFICIAL
        ):
            self.problems.append(f"{where}: a change must be official evidence")
        if item.url not in {r.request_url for r in stored.retrievals}:
            self.problems.append(
                f"{where}: {item.url} is not where its artifact came from"
            )
        text = ArtifactText(stored.body, stored.ref.media_type)

        def span(start: int, end: int, cited: str) -> EvidenceLocator:
            return EvidenceLocator(
                kind=LocatorKind.TEXT_SPAN,
                canonicalization_version=CANONICALIZATION_VERSION,
                canonical_sha256=item.canonical_sha256,
                start=start,
                end=end,
                cited_sha256=cited,
            )

        rows: dict[tuple[str, str], EvidenceLocator] = {}
        date_locator = None
        try:
            for row in _members(item):
                locator = span(*row.span, row.cited_sha256)
                cited = text.cited(locator)
                for fact in (row.name, row.ticker):
                    if fact not in cited:
                        self.problems.append(
                            f"{where}: the text cited for {row.security_id}"
                            f" does not state {fact!r}"
                        )
                rows[(row.security_id, _action(row))] = locator
            if isinstance(item, ChangeEvidence):
                date_locator = span(*item.date_span, item.date_cited_sha256)
                text.verify(date_locator)
        except LocatorError as exc:
            self.problems.append(f"{where}: {exc}")
            return None
        return _Item(item, entry, stored, rows, date_locator)

    def _override_citations(self) -> None:
        for override in self.overrides:
            for citation in override.citations:
                if citation.artifact_sha256 is None:
                    continue
                stored = self._stored(citation.source_id, citation.artifact_sha256)
                if stored is None or citation.locator is None:
                    continue
                try:
                    ArtifactText(stored.body, stored.ref.media_type).verify(
                        citation.locator
                    )
                except LocatorError as exc:
                    self.problems.append(f"{override.override_id}: {exc}")

    # -- step 2: membership ----------------------------------------------------

    def _anchor(self, items: list[_Item]) -> tuple[_Item | None, Finding | None]:
        anchors = [i for i in items if _is_anchor(i)]
        if not anchors:
            return None, self._missing_anchor("no anchor snapshot is curated", [])
        (anchor,) = anchors
        snapshot = anchor.config
        reasons = []
        if anchor.entry.evidence_class not in (
            EvidenceClass.OFFICIAL,
            EvidenceClass.SECONDARY,
        ):
            reasons.append(f"{anchor.entry.evidence_class} evidence is not a roster")
        if snapshot.published_on > snapshot.as_of:
            reasons.append(
                f"published {snapshot.published_on}, after its as-of date"
                f" {snapshot.as_of}: a later snapshot is never backdated"
            )
        if snapshot.as_of > self.universe.period_end_start:
            reasons.append(f"dated after the window's start, {snapshot.as_of}")
        if snapshot.published_on > self.cutoff:
            reasons.append("first published after the cutoff")
        if reasons:
            detail = f"{snapshot.evidence_id} cannot anchor: {'; '.join(reasons)}"
            return None, self._missing_anchor(detail, [snapshot.evidence_id])
        return anchor, None

    @staticmethod
    def _missing_anchor(detail: str, evidence_ids: list[str]) -> Finding:
        return make_finding(
            FindingKind.MISSING_ANCHOR,
            "anchor",
            detail,
            blocking=True,
            evidence_ids=evidence_ids,
        )

    @staticmethod
    def _statements(anchor: _Item | None, changes: list[_Item]) -> list[Statement]:
        statements = []
        for item in ([anchor] if anchor else []) + changes:
            config = item.config
            is_change = isinstance(config, ChangeEvidence)
            for row in _members(config):
                action = AssertedAction(_action(row))
                statements.append(
                    Statement(
                        assertion_id=f"{config.evidence_id}:{row.security_id}:{action}",
                        security_id=row.security_id,
                        action=action,
                        on=config.effective_on if is_change else config.as_of,
                        timing=config.timing if is_change else BoundTiming.UNSPECIFIED,
                        evidence_id=config.evidence_id,
                        published_on=config.published_on,
                    )
                )
        return statements

    # -- step 3: identity ------------------------------------------------------

    def _sec(self, securities: tuple[SecurityRecord, ...]) -> SecEvidence | None:
        tickers = self._latest(SEC_SOURCE_ID, COMPANY_TICKERS_URL)
        if tickers is None:
            return None
        try:
            entries = read_company_tickers(tickers.body)
        except (SecDataError, ValueError) as exc:
            self.problems.append(f"company_tickers.json: {exc}")
            return None
        cited = {i.ticker for s in securities for i in s.identities}
        ciks = {e.cik for e in entries if e.ticker in cited}
        ciks |= {o.cik for o in self.overrides if o.kind is OverrideKind.SET_ISSUER}
        registrants = {}
        for cik in sorted(ciks):
            url = submissions_url(cik)
            stored = self._latest(SEC_SOURCE_ID, url)
            if stored is None:
                continue
            try:
                registrant = read_submissions(stored.body)
            except (SecDataError, ValueError) as exc:
                self.problems.append(f"{url}: {exc}")
                continue
            registrants[cik] = (registrant, self._citable(SEC_SOURCE_ID, url, stored))
        return SecEvidence(
            tickers=self._citable(SEC_SOURCE_ID, COMPANY_TICKERS_URL, tickers),
            ticker_entries=entries,
            registrants=registrants,
        )

    @staticmethod
    def _citable(source_id: str, url: str, stored: StoredArtifact) -> CitableArtifact:
        return CitableArtifact(
            source_id=source_id,
            url=url,
            artifact=stored.ref,
            retrieved_at=stored.retrievals[0].retrieved_at,
            text=ArtifactText(stored.body, stored.ref.media_type),
        )

    # -- step 4: corroboration ------------------------------------------------

    def _fund_filings(self) -> list[FundFiling]:
        proxy = self.universe.etf_proxy
        if proxy is None:
            return []
        self._entry(proxy.source_id, SourceRole.CORROBORATION)
        url = submissions_url(proxy.cik)
        stored = self._latest(SEC_SOURCE_ID, url)
        if stored is None:
            return []
        try:
            registrant = read_submissions(stored.body)
            filings = list(registrant.filings)
            for page in registrant.older_pages:
                older = self._latest(SEC_SOURCE_ID, submissions_page_url(page))
                if older is not None:
                    filings.extend(read_submissions_page(older.body))
        except (SecDataError, ValueError) as exc:
            self.problems.append(f"{url}: {exc}")
            return []
        funds = []
        for filing in filings:
            if filing.form not in proxy.forms or filing.report_date is None:
                continue
            if not (
                self.universe.period_end_start <= filing.report_date <= self.cutoff
            ):
                continue
            document = archive_url(
                proxy.cik, filing.accession, raw_document_name(filing.primary_document)
            )
            saved = self._latest(proxy.source_id, document)
            if saved is None:
                continue
            try:
                report = read_nport_holdings(saved.body)
            except SecDataError as exc:
                self.problems.append(f"{document}: {exc}")
                continue
            if report.report_date != filing.report_date:
                self.problems.append(
                    f"{document}: reports {report.report_date}, but EDGAR lists"
                    f" {filing.report_date}"
                )
                continue
            funds.append(
                FundFiling(
                    filing, report, self._citable(proxy.source_id, document, saved)
                )
            )
        return funds

    # -- the whole ------------------------------------------------------------

    def run(self) -> CohortBuild:
        evidence = self.config.evidence
        items = [self._item(item) for item in (*evidence.snapshots, *evidence.changes)]
        for check in evidence.checks:
            self._entry(check.source_id, SourceRole.CHECK)
        self._override_citations()
        if self.problems:
            raise CohortError(self.problems)
        items = [item for item in items if item is not None]

        anchor, missing = self._anchor(items)
        changes = [i for i in items if isinstance(i.config, ChangeEvidence)]
        statements = self._statements(anchor, changes)
        rejections = {
            o.membership_assertion_id: o.override_id
            for o in self.overrides
            if o.kind is OverrideKind.REJECT_ASSERTION
        }
        membership = reconstruct(
            statements,
            anchor_date=None if anchor is None else anchor.config.as_of,
            cutoff=self.cutoff,
            rejections=rejections,
        )
        counts = count_findings(
            membership.intervals,
            anchor_date=None if anchor is None else anchor.config.as_of,
            cutoff=self.cutoff,
            expected=self.universe.expected_member_count,
        )

        usable = [i for i in items if not _is_anchor(i) or i is anchor]
        securities = self._securities(usable)
        timely = self._timely(securities, usable)
        known = {s.security_id for s in securities}
        for o in self.overrides:
            if o.kind is OverrideKind.HOLDING_ALIAS and o.security_id not in known:
                self.problems.append(f"{o.override_id}: no security {o.security_id}")
        stop = self.cutoff + timedelta(days=1)
        in_scope = frozenset(
            i.security_id
            for i in membership.intervals
            if i.overlaps(self.universe.period_end_start, stop)
        )
        sec = self._sec(timely)
        funds = self._fund_filings()
        if self.problems or sec is None:
            raise CohortError(self.problems)
        resolution = resolve(timely, sec, self.overrides, in_scope)

        reconciliations, fund_findings = self._reconciliations(
            items, funds, timely, securities, membership.intervals
        )
        findings = [
            *([missing] if missing else []),
            *membership.findings,
            *counts,
            *resolution.findings,
            *fund_findings,
            *difference_findings(reconciliations),
            *gap_findings(
                reconciliations,
                start=self.universe.period_end_start,
                cutoff=self.cutoff,
            ),
            *self._withheld(items, funds),
        ]
        findings, stale = acknowledge(findings, self.overrides)

        mappings = {m.security_id: m for m in resolution.mappings}
        assertions = self._assertions(statements, items, membership, mappings)
        candidates = sorted(
            {
                mappings[s].issuer_id
                for s in in_scope
                if s in mappings and mappings[s].issuer_id is not None
            }
        )
        report = CohortReport(
            universe_id=self.universe.universe_id,
            anchor_evidence_id=None if anchor is None else anchor.config.evidence_id,
            limitations=self._limitations(anchor),
            findings=tuple(sorted(findings, key=lambda f: f.finding_id)),
            reconciliations=tuple(
                sorted(reconciliations, key=lambda r: (r.as_of, r.snapshot_id))
            ),
        )
        return CohortBuild(
            config=self.config,
            source_register_version=self.registers.version(self.used),
            sources=tuple(self.registers.rights(s) for s in sorted(self.used)),
            securities=securities,
            assertions=assertions,
            intervals=tuple(
                sorted(
                    membership.intervals,
                    key=lambda i: (i.security_id, i.effective_from),
                )
            ),
            mappings=resolution.mappings,
            issuers=resolution.issuers,
            candidate_issuer_ids=tuple(candidates),
            overrides=tuple(sorted(self.overrides, key=lambda o: o.override_id)),
            report=report,
            stale_acknowledgements=stale,
        )

    def _securities(self, items: list[_Item]) -> tuple[SecurityRecord, ...]:
        identities: dict[str, list[CitedIdentity]] = defaultdict(list)
        for item in items:
            config = item.config
            observed = (
                config.effective_on
                if isinstance(config, ChangeEvidence)
                else config.as_of
            )
            for row in _members(config):
                identities[row.security_id].append(
                    CitedIdentity(
                        evidence_id=config.evidence_id,
                        observed_on=observed,
                        name=row.name,
                        ticker=row.ticker,
                    )
                )
        return tuple(
            SecurityRecord(
                security_id=security_id,
                identities=tuple(
                    sorted(found, key=lambda i: (i.observed_on, i.evidence_id))
                ),
            )
            for security_id, found in sorted(identities.items())
        )

    def _timely(
        self, securities: tuple[SecurityRecord, ...], items: list[_Item]
    ) -> tuple[SecurityRecord, ...]:
        """The records with only rows published by the cutoff: what identity and
        holdings matching may use (P-C4)."""
        published = {i.config.evidence_id: i.config.published_on for i in items}
        return tuple(
            s.model_copy(
                update={
                    "identities": tuple(
                        i
                        for i in s.identities
                        if published[i.evidence_id] <= self.cutoff
                    )
                }
            )
            for s in securities
        )

    def _reconciliations(self, items, funds, timely, securities, intervals):
        reconciliations: list[SnapshotReconciliation] = []
        for item in items:
            config = item.config
            if (
                not isinstance(config, SnapshotEvidence)
                or config.role != "corroboration"
            ):
                continue
            reconciliations.append(
                reconcile(
                    config.evidence_id,
                    source_id=config.source_id,
                    evidence_class=item.entry.evidence_class,
                    as_of=config.as_of,
                    published_on=config.published_on,
                    cutoff=self.cutoff,
                    listed=[row.security_id for row in config.members],
                    unmatched=(),
                    intervals=intervals,
                    citation=item.citation().cite(*item.rows.values()),
                )
            )
        current, findings = current_filings(funds, self.cutoff)
        proxy = self.universe.etf_proxy
        for fund in current:
            matched, unmatched = match_holdings(fund.report, timely, self.overrides)
            reconciliations.append(
                reconcile(
                    f"{proxy.source_id}:{fund.filing.accession}",
                    source_id=proxy.source_id,
                    evidence_class=EvidenceClass.ETF_PROXY,
                    as_of=fund.report.report_date,
                    published_on=fund.filing.filing_date,
                    cutoff=self.cutoff,
                    listed=matched,
                    unmatched=unmatched,
                    intervals=intervals,
                    citation=fund.artifact.cite(),
                )
            )
        tickers = defaultdict(set)
        for security in securities:
            for identity in security.identities:
                tickers[identity.ticker].add(security.security_id)
        for check in self.config.evidence.checks:
            listed = set().union(*(tickers.get(m.ticker, set()) for m in check.members))
            reconciliations.append(
                reconcile(
                    check.evidence_id,
                    source_id=check.source_id,
                    evidence_class=self.registers.entry(check.source_id).evidence_class,
                    as_of=check.as_of,
                    published_on=check.published_on,
                    cutoff=self.cutoff,
                    listed=listed,
                    unmatched=[
                        m.ticker for m in check.members if m.ticker not in tickers
                    ],
                    intervals=intervals,
                    citation=None,
                )
            )
        return reconciliations, findings

    def _withheld(self, items: list[_Item], funds: list[FundFiling]) -> list[Finding]:
        late = [
            (i.config.evidence_id, i.config.published_on)
            for i in items
            if i.config.published_on > self.cutoff
        ]
        late += [
            (c.evidence_id, c.published_on)
            for c in self.config.evidence.checks
            if c.published_on > self.cutoff
        ]
        late += [
            (f.filing.accession, f.filing.filing_date)
            for f in funds
            if f.filing.filing_date > self.cutoff
        ]
        return [
            make_finding(
                FindingKind.WITHHELD,
                subject,
                f"{subject} was first published {published}, after the cutoff"
                f" {self.cutoff}; it is reported and never applied",
                blocking=False,
                evidence_ids=[subject],
            )
            for subject, published in sorted(late)
        ]

    def _assertions(self, statements, items, membership, mappings):
        by_id = {i.config.evidence_id: i for i in items}
        assertions = []
        for s in sorted(statements, key=lambda s: s.assertion_id):
            item = by_id[s.evidence_id]
            config = item.config
            is_change = isinstance(config, ChangeEvidence)
            interval = membership.supports.get(s.assertion_id)
            mapping = mappings.get(s.security_id)
            locators = [item.rows[(s.security_id, s.action.value)]]
            if item.date_locator is not None:
                locators.append(item.date_locator)
            assertions.append(
                MembershipAssertion(
                    membership_assertion_id=s.assertion_id,
                    universe_id=self.universe.universe_id,
                    security_id=s.security_id,
                    issuer_id=None if mapping is None else mapping.issuer_id,
                    cik=None if mapping is None else mapping.cik,
                    asserted_action=s.action,
                    asserted_date=s.on,
                    asserted_timing=s.timing,
                    effective_from=None
                    if interval is None
                    else interval.effective_from,
                    effective_from_basis=None
                    if interval is None
                    else interval.effective_from_basis,
                    effective_from_timing=None
                    if interval is None
                    else interval.effective_from_timing,
                    effective_to=None if interval is None else interval.effective_to,
                    effective_to_timing=None
                    if interval is None
                    else interval.effective_to_timing,
                    announcement_date=config.announced_on if is_change else None,
                    source_snapshot_date=None if is_change else config.as_of,
                    publication_date=config.published_on,
                    publication_time=config.published_at,
                    retrieved_at=item.retrieved_at,
                    source_id=config.source_id,
                    evidence_id=config.evidence_id,
                    url=config.url,
                    evidence_locators=tuple(locators),
                    raw_content_hash=config.artifact_sha256,
                    rights_status=item.entry.rights_status,
                    status=membership.statuses[s.assertion_id],
                    resolved_by=membership.rejected_by.get(s.assertion_id),
                )
            )
        return tuple(assertions)

    @staticmethod
    def _limitations(anchor: _Item | None) -> tuple[str, ...]:
        if anchor is None:
            return LIMITATIONS
        first = (
            f"The anchor, {anchor.config.evidence_id}, is {anchor.entry.evidence_class}"
            f" evidence dated {anchor.config.as_of}: that date bounds each anchored"
            " start from below."
        )
        return (first, *LIMITATIONS)
```

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py`:

```python
"""Freeze a cohort build into a versioned, content-hashed manifest (P-A4).

- Freezing refuses while any blocking finding is unresolved, or any
  acknowledgement no longer matches its finding, and names each one.
- The content hash covers everything except the version, the hash itself, and the
  creation time. A build whose content matches a frozen manifest *is* that version,
  and nothing is written; different content is the next version.
- The manifest is written to a temporary file and linked into place, so a partial
  manifest never appears and an existing one is never replaced.
- Loading reads the committed JSON alone, with no saved artifact, and rechecks the
  content hash.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from earnings_ingestion.cohort.build import CohortBuild, content_hash
from earnings_ingestion.cohort.config import UNIVERSE_DIR
from earnings_ingestion.cohort.records import Finding, UniverseManifest
from earnings_ingestion.fetch.store import write_new

MANIFESTS = UNIVERSE_DIR / "manifests"


class FreezeRefused(ValueError):
    """The build still holds blocking findings or stale acknowledgements."""

    def __init__(self, blocking: tuple[Finding, ...], stale: tuple[str, ...]) -> None:
        self.blocking = blocking
        self.stale = stale
        reasons = [f"{f.finding_id}: {f.detail}" for f in blocking]
        reasons += [f"{o}: acknowledges a finding that has changed" for o in stale]
        super().__init__("; ".join(reasons))


@dataclass(frozen=True)
class Frozen:
    manifest: UniverseManifest
    path: Path
    created: bool
    """False when an existing version already held this content."""


def manifest_path(directory: Path, universe_id: str, version: int) -> Path:
    return directory / f"{universe_id}-v{version}.json"


def serialize(manifest: UniverseManifest) -> bytes:
    """Indented JSON with sorted keys, for a readable diff between versions."""
    data = manifest.model_dump(mode="json")
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False)
    return f"{text}\n".encode()


def load_manifest(path: Path) -> UniverseManifest:
    """A committed manifest, refused if its name or content hash disagrees."""
    manifest = UniverseManifest.model_validate_json(path.read_bytes())
    definition = manifest.definition
    if content_hash(manifest) != definition.content_hash:
        raise ValueError(f"{path} does not hash to its content_hash")
    expected = manifest_path(
        path.parent, definition.universe_id, definition.universe_version
    )
    if path.name != expected.name:
        raise ValueError(f"{path} holds version {definition.universe_version}")
    return manifest


def frozen_manifests(directory: Path, universe_id: str) -> list[UniverseManifest]:
    """Every frozen version of ``universe_id``, oldest first."""
    manifests = [
        load_manifest(path) for path in sorted(directory.glob(f"{universe_id}-v*.json"))
    ]
    return sorted(manifests, key=lambda m: m.definition.universe_version)


def freeze(build: CohortBuild, directory: Path, *, now: datetime) -> Frozen:
    blocking = build.report.blocking
    if blocking or build.stale_acknowledgements:
        raise FreezeRefused(blocking, build.stale_acknowledgements)
    universe_id = build.config.universe.universe_id
    existing = frozen_manifests(directory, universe_id)
    target = build.content_hash
    for manifest in existing:
        if manifest.definition.content_hash == target:
            path = manifest_path(
                directory, universe_id, manifest.definition.universe_version
            )
            return Frozen(manifest=manifest, path=path, created=False)
    version = 1 + max((m.definition.universe_version for m in existing), default=0)
    manifest = build.manifest(version, now)
    path = manifest_path(directory, universe_id, version)
    write_new(path, serialize(manifest))
    return Frozen(manifest=manifest, path=path, created=True)
```

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/synthetic.py`:

```python
"""A synthetic, redistributable cohort (P §Verification): every company, page,
record, and filing here is invented, so all of it may be committed.

``write_synthetic_cohort(repo, directory)`` writes under ``repo / directory``:

- ``membership-source-register.toml`` and ``source-register.toml``: the registers;
- ``raw/``: an artifact store holding the roster revisions, the index notices, SEC's
  ticker list and submissions, and the fund's N-PORT filings;
- ``universe.toml`` and ``evidence.toml``: the curated files;
- ``overrides.toml``: the decisions a reviewer makes against the build's findings;
- ``manifests/``: the frozen manifest, which Stage 5's offline tests consume.

The scenario exercises P-VF's Stage 4 cases: an anchor with additions and removals,
a date conflict settled by review, a change published after the cutoff, a ticker
change, a former name, two share classes of one issuer, an identity override, an
amended fund filing, a lagging secondary snapshot, and an uncorroborated quarter.
"""

import json
from datetime import UTC, date, datetime
from pathlib import Path

from earnings_core import RightsStatus, sha256_hex

from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.digests import canonical_json
from earnings_ingestion.cohort.freeze import freeze
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.identifiers import pad_cik
from earnings_ingestion.sec.urls import (
    COMPANY_TICKERS_URL,
    archive_url,
    submissions_url,
)

FIXTURE_DIR = Path("tests") / "fixtures" / "cohort"
UNIVERSE_ID = "djia-synthetic"
CUTOFF = date(2026, 9, 22)
RETRIEVED = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
FROZEN_AT = datetime(2026, 9, 28, 0, 0, tzinfo=UTC)
REVIEWER = "Synthetic Reviewer"
FUND_CIK = pad_cik(9990900)
NPORT_DOCUMENT = "xslFormNPORT-P_X01/primary_doc.xml"
RIGHTS = {
    "rights_status": RightsStatus.REDISTRIBUTABLE,
    "rights_basis": "synthetic test data, invented for this repository",
}

COMPANIES = {
    # cik: (SEC name, tickers, former names)
    9990001: ("Acme Industrial Corp", ["ACME"], []),
    9990002: ("Borealis Air Inc", ["BORA"], ["Northern Airways Inc"]),
    9990003: ("Corvid Systems Inc", ["CRVD"], []),
    9990005: ("Dynamo Motors Co", ["DYNA", "DYNB"], []),
    9990006: ("Eastfield Bank Corp", ["EFB"], []),
    9990007: ("Fenwick Laboratories Inc", ["FNWK"], []),
    9990900: ("Synthetic Industrial Average Fund Trust", ["SIAF"], []),
}
ROW = {
    # security_id: (name, ticker) as the rosters and notices print them
    "acme-old": ("Acme Industrial", "ACMX"),
    "acme": ("Acme Industrial", "ACME"),
    "borealis-old": ("Northern Airways", "BORA"),
    "borealis": ("Borealis Air", "BORA"),
    "corvid": ("Corvid Systems", "CRVD"),
    "dynamo-a": ("Dynamo Motors (Class A)", "DYNA"),
    "dynamo-b": ("Dynamo Motors (Class B)", "DYNB"),
    "eastfield": ("EFB Financial", "EFB"),
    "fenwick": ("Fenwick Labs", "FNWK"),
}
SECURITY = {
    "acme-old": "acme-common",
    "acme": "acme-common",
    "borealis-old": "borealis-common",
    "borealis": "borealis-common",
    "corvid": "corvid-common",
    "dynamo-a": "dynamo-class-a",
    "dynamo-b": "dynamo-class-b",
    "eastfield": "eastfield-common",
    "fenwick": "fenwick-common",
}
ROSTERS = [
    # evidence_id, revision, role, as_of, published_on, rows
    (
        "roster-2024-06-28",
        1001,
        "anchor",
        date(2024, 6, 28),
        date(2024, 6, 20),
        ["acme-old", "borealis-old", "dynamo-a", "eastfield"],
    ),
    (
        "roster-2024-11-08",
        1002,
        "corroboration",
        date(2024, 11, 8),
        date(2024, 11, 8),
        ["acme-old", "borealis", "dynamo-a", "eastfield"],
    ),
    (
        "roster-2025-06-30",
        1003,
        "corroboration",
        date(2025, 6, 30),
        date(2025, 6, 30),
        ["acme", "corvid", "dynamo-a", "eastfield"],
    ),
]
NOTICES = [
    # evidence_id, announced, published_at, effective, date phrase, added, removed
    (
        "index-2024-10-31",
        date(2024, 10, 31),
        datetime(2024, 10, 31, 21, 0, tzinfo=UTC),
        date(2024, 11, 7),
        "prior to the open of trading on Thursday, November 7, 2024",
        ["corvid"],
        [],
    ),
    (
        "index-2024-11-01",
        date(2024, 11, 1),
        datetime(2024, 11, 1, 21, 15, tzinfo=UTC),
        date(2024, 11, 8),
        "prior to the open of trading on Friday, November 8, 2024",
        ["corvid"],
        ["borealis"],
    ),
    (
        "index-2026-06-16",
        date(2026, 6, 16),
        datetime(2026, 6, 16, 21, 0, tzinfo=UTC),
        date(2026, 6, 22),
        "prior to the open of trading on Monday, June 22, 2026",
        ["dynamo-b"],
        ["eastfield"],
    ),
    (
        "index-2026-09-25",
        date(2026, 9, 25),
        datetime(2026, 9, 25, 21, 0, tzinfo=UTC),
        date(2026, 10, 5),
        "prior to the open of trading on Monday, October 5, 2026",
        ["fenwick"],
        ["acme"],
    ),
]
BEFORE = ["Acme Industrial Corp", "Borealis Air Inc", "Dynamo Motors Co Class A"]
MIDDLE = ["Acme Industrial Corp", "Corvid Systems Inc", "Dynamo Motors Co Class A"]
AFTER = [*MIDDLE, "Dynamo Motors Co Class B"]
FILINGS = [
    # accession suffix, form, filed, report date, holdings
    (
        "24-000001",
        "NPORT-P",
        date(2024, 11, 26),
        date(2024, 9, 30),
        [*BEFORE, "Eastfield Bank Corp"],
    ),
    (
        "25-000001",
        "NPORT-P",
        date(2025, 2, 26),
        date(2024, 12, 31),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    (
        "25-000002",
        "NPORT-P",
        date(2025, 5, 28),
        date(2025, 3, 31),
        [*BEFORE, "Eastfield Bank Corp"],
    ),
    (
        "25-000003",
        "NPORT-P/A",
        date(2025, 6, 10),
        date(2025, 3, 31),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    (
        "25-000004",
        "NPORT-P",
        date(2025, 8, 27),
        date(2025, 6, 30),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    (
        "25-000005",
        "NPORT-P",
        date(2025, 11, 25),
        date(2025, 9, 30),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    (
        "26-000001",
        "NPORT-P",
        date(2026, 2, 25),
        date(2025, 12, 31),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    (
        "26-000002",
        "NPORT-P",
        date(2026, 5, 27),
        date(2026, 3, 31),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    ("26-000003", "NPORT-P", date(2026, 8, 26), date(2026, 6, 30), AFTER),
    ("26-000004", "NPORT-P/A", date(2026, 9, 24), date(2026, 6, 30), AFTER),
]
USER_LIST = ["acme", "corvid", "dynamo-a", "dynamo-b", "fenwick"]


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, date)):
        return value.isoformat() if isinstance(value, date) else str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    raise TypeError(f"no TOML form for {type(value).__name__}")


def _toml(data: dict, prefix: str = "") -> list[str]:
    """TOML for ``data``: scalars, tables, and arrays of tables, in key order."""
    lines = []
    for key, value in data.items():
        if isinstance(value, dict) or (
            isinstance(value, list) and value and isinstance(value[0], dict)
        ):
            continue
        if value is not None:
            lines.append(f"{key} = {_toml_value(value)}")
    for key, value in data.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            lines += ["", f"[{name}]", *_toml(value, f"{name}.")]
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            for entry in value:
                lines += ["", f"[[{name}]]", *_toml(entry, f"{name}.")]
    return lines


def _write_toml(path: Path, header: str, data: dict) -> None:
    body = "\n".join(_toml(data)).strip("\n")
    path.write_text(f"# {header}\n{body}\n", encoding="utf-8")


def _save(
    store: ArtifactStore, source_id: str, url: str, body: bytes, media: str
) -> str:
    retrieval = Retrieval(
        request_url=url,
        final_url=url,
        retrieved_at=RETRIEVED,
        retrieval_method=RetrievalMethod.HTTP,
        http_status=200,
        media_type=media,
        content_type=media,
        byte_count=len(body),
        sha256=sha256_hex(body),
    )
    return store.put(source_id, body, retrieval, **RIGHTS).content_sha256


def _roster_page(revision: int, as_of: date, rows: list[str]) -> bytes:
    cells = "".join(
        f"<tr><td>{ROW[key][0]}</td><td>{ROW[key][1]}</td><td>Industrials</td></tr>"
        for key in rows
    )
    return (
        "<html><head><title>Synthetic Industrial Average</title></head><body>"
        "<h1>Synthetic Industrial Average</h1>"
        f"<p>Revision {revision}. Components as of {as_of:%B} {as_of.day}, {as_of.year}:</p>"
        "<table><tr><th>Company</th><th>Symbol</th><th>Sector</th></tr>"
        f"{cells}</table></body></html>"
    ).encode()


def _named(key: str) -> str:
    name, ticker = ROW[key]
    return f"{name} ({ticker})"


def _notice_page(phrase: str, added: list[str], removed: list[str]) -> bytes:
    joined = " and ".join(_named(key) for key in added)
    if removed:
        replaced = " and ".join(_named(key) for key in removed)
        sentence = f"{joined} will replace {replaced} in the Synthetic Industrial Average {phrase}."
    else:
        sentence = f"{joined} will join the Synthetic Industrial Average {phrase}."
    return (
        "<html><head><title>Synthetic Index Notice</title></head><body>"
        "<h1>Synthetic Index Services announces a change</h1>"
        f"<p>{sentence}</p><p>This notice is synthetic test data.</p></body></html>"
    ).encode()


def _submissions(cik: int, filings: list[tuple] = ()) -> bytes:
    name, tickers, former = COMPANIES[cik]
    columns = {
        "accessionNumber": [],
        "filingDate": [],
        "reportDate": [],
        "acceptanceDateTime": [],
        "form": [],
        "primaryDocument": [],
    }
    for suffix, form, filed, report, _ in sorted(
        filings, reverse=True, key=lambda f: f[2]
    ):
        columns["accessionNumber"].append(f"{FUND_CIK}-{suffix}")
        columns["filingDate"].append(filed.isoformat())
        columns["reportDate"].append(report.isoformat())
        columns["acceptanceDateTime"].append(f"{filed.isoformat()}T16:05:00.000Z")
        columns["form"].append(form)
        columns["primaryDocument"].append(NPORT_DOCUMENT)
    data = {
        "cik": str(cik),
        "name": name,
        "tickers": tickers,
        "formerNames": [
            {
                "name": n,
                "from": "2001-01-01T00:00:00.000Z",
                "to": "2019-12-31T00:00:00.000Z",
            }
            for n in former
        ],
        "filings": {"recent": columns, "files": []},
    }
    return canonical_json(data)


def _nport(report: date, holdings: list[str]) -> bytes:
    positions = "".join(
        f"<invstOrSec><name>{name}</name><title>{name}</title>"
        "<assetCat>EC</assetCat></invstOrSec>"
        for name in holdings
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">'
        "<formData><genInfo>"
        f"<repPdDate>{report.isoformat()}</repPdDate></genInfo><invstOrSecs>"
        f"{positions}<invstOrSec><name>Synthetic Treasury Money Fund</name>"
        "<assetCat>STIV</assetCat></invstOrSec></invstOrSecs></formData>"
        "</edgarSubmission>"
    ).encode()


def _cite(text: ArtifactText, needle: str) -> dict:
    locator = text.find(needle)
    return {"span": [locator.start, locator.end], "cited_sha256": locator.cited_sha256}


def _registers(root: Path) -> None:
    common = {
        "cost": "Free; synthetic.",
        "license_terms": "Invented for this repository's tests.",
        "redistribution_status": "Synthetic; committed as test data.",
        "expected_update_pattern": "Never updated.",
        "known_limitations": ["Synthetic: it describes no real index."],
        "last_verified": date(2026, 9, 27),
        "rights_status": "redistributable",
        "rights_basis": "synthetic test data, invented for this repository",
        "terms_sha256": sha256_hex(b"synthetic terms"),
    }
    sources = {
        "synthetic-roster": {
            "owner": "Synthetic Encyclopedia",
            "url": "https://roster.example/index",
            "access_method": "Fixed revisions through the cohort web client.",
            "terms_url": "https://roster.example/terms",
            "coverage": "Dated revisions of the roster.",
            "evidence_class": "secondary",
            "roles": ["anchor", "corroboration"],
        },
        "synthetic-index": {
            "owner": "Synthetic Index Services",
            "url": "https://index.example/notices",
            "access_method": "Notices through the cohort web client.",
            "terms_url": "https://index.example/terms",
            "coverage": "Every addition and removal.",
            "evidence_class": "official",
            "roles": ["change"],
        },
        "synthetic-fund": {
            "owner": "Synthetic Industrial Average Fund Trust",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?CIK=0009990900",
            "access_method": "N-PORT filings through the shared SEC client.",
            "terms_url": "https://www.sec.gov/privacy",
            "coverage": "Quarterly holdings.",
            "evidence_class": "etf_proxy",
            "roles": ["corroboration"],
        },
        "user-list": {
            "owner": "The user",
            "url": "https://user.example/list",
            "access_method": "Supplied in conversation.",
            "terms_url": "https://user.example/terms",
            "coverage": "One list, as of the cutoff.",
            "evidence_class": "user_supplied",
            "roles": ["check"],
        },
    }
    register = {
        "schema_version": 1,
        "sources": {key: value | common for key, value in sources.items()},
    }
    _write_toml(
        root / "membership-source-register.toml", "Synthetic register.", register
    )
    sec = {
        "sources": {
            "sec-edgar": {"owner": "Synthetic SEC", "last_verified": date(2026, 9, 27)}
        }
    }
    _write_toml(root / "source-register.toml", "Synthetic sec-edgar entry.", sec)


def _evidence(store: ArtifactStore) -> dict:
    snapshots, changes = [], []
    for evidence_id, revision, role, as_of, published, rows in ROSTERS:
        url = f"https://roster.example/index?rev={revision}"
        body = _roster_page(revision, as_of, rows)
        sha = _save(store, "synthetic-roster", url, body, "text/html")
        text = ArtifactText(body, "text/html")
        members = [
            {
                "security_id": SECURITY[key],
                "name": ROW[key][0],
                "ticker": ROW[key][1],
                **_cite(text, f"{ROW[key][0]}\t{ROW[key][1]}"),
            }
            for key in rows
        ]
        snapshots.append(
            {
                "evidence_id": evidence_id,
                "source_id": "synthetic-roster",
                "role": role,
                "url": url,
                "artifact_sha256": sha,
                "canonical_sha256": text.canonical[1],
                "as_of": as_of,
                "published_on": published,
                "members": members,
            }
        )
    for (
        evidence_id,
        announced,
        published_at,
        effective,
        phrase,
        added,
        removed,
    ) in NOTICES:
        url = f"https://index.example/notices/{evidence_id}"
        body = _notice_page(phrase, added, removed)
        sha = _save(store, "synthetic-index", url, body, "text/html")
        text = ArtifactText(body, "text/html")
        dated = _cite(text, phrase)
        entries = [
            {
                "action": action,
                "security_id": SECURITY[key],
                "name": ROW[key][0],
                "ticker": ROW[key][1],
                **_cite(text, _named(key)),
            }
            for action, keys in (("added", added), ("removed", removed))
            for key in keys
        ]
        changes.append(
            {
                "evidence_id": evidence_id,
                "source_id": "synthetic-index",
                "url": url,
                "artifact_sha256": sha,
                "canonical_sha256": text.canonical[1],
                "announced_on": announced,
                "published_on": published_at.date(),
                "published_at": published_at.isoformat().replace("+00:00", "Z"),
                "effective_on": effective,
                "timing": "before_open",
                "date_span": dated["span"],
                "date_cited_sha256": dated["cited_sha256"],
                "entries": entries,
            }
        )
    check = {
        "evidence_id": "user-list-2026-09-26",
        "source_id": "user-list",
        "as_of": CUTOFF,
        "published_on": date(2026, 9, 26),
        "members": [{"name": ROW[k][0], "ticker": ROW[k][1]} for k in USER_LIST],
    }
    return {
        "schema_version": 1,
        "snapshots": snapshots,
        "changes": changes,
        "checks": [check],
    }


def _sec(store: ArtifactStore) -> dict[str, str]:
    """Save SEC's records; return the submissions hash of each CIK."""
    tickers = {
        str(index): {"cik_str": cik, "ticker": ticker, "title": name}
        for index, (cik, ticker, name) in enumerate(
            (cik, ticker, name)
            for cik, (name, symbols, _) in COMPANIES.items()
            for ticker in symbols
        )
    }
    _save(
        store,
        "sec-edgar",
        COMPANY_TICKERS_URL,
        canonical_json(tickers),
        "application/json",
    )
    hashes = {}
    for cik in COMPANIES:
        body = _submissions(cik, FILINGS if pad_cik(cik) == FUND_CIK else [])
        hashes[pad_cik(cik)] = _save(
            store, "sec-edgar", submissions_url(cik), body, "application/json"
        )
    for suffix, _, _, report, holdings in FILINGS:
        url = archive_url(FUND_CIK, f"{FUND_CIK}-{suffix}", "primary_doc.xml")
        _save(store, "synthetic-fund", url, _nport(report, holdings), "application/xml")
    return hashes


def _override(override_id: str, kind: str, rationale: str, **fields) -> dict:
    return {
        "override_id": override_id,
        "kind": kind,
        **fields,
        "rationale": rationale,
        "reviewer": REVIEWER,
        "recorded_on": date(2026, 9, 28),
        "effective_from": date(2024, 7, 1),
    }


def build_options(directory: Path = FIXTURE_DIR) -> dict[str, Path]:
    """``build``'s keywords for a synthetic cohort written under ``directory``."""
    return {
        "config_dir": directory,
        "store_root": directory / "raw",
        "register": directory / "membership-source-register.toml",
        "sec_register": directory / "source-register.toml",
    }


def write_synthetic_cohort(repo: Path, directory: Path = FIXTURE_DIR) -> Path:
    """Write the synthetic cohort and freeze it; return the manifest's path."""
    root = repo / directory
    root.mkdir(parents=True, exist_ok=True)
    store = ArtifactStore(root / "raw", repo)
    _registers(root)
    universe = {
        "universe_id": UNIVERSE_ID,
        "universe_name": "djia",
        "period_end_start": date(2024, 7, 1),
        "period_end_stop": date(2026, 7, 1),
        "public_information_cutoff": CUTOFF,
        "membership_reference": "first_publication_time",
        "selection_policy_version": "djia-pilot/1",
        "expected_member_count": 4,
        "etf_proxy": {"source_id": "synthetic-fund", "cik": FUND_CIK},
    }
    _write_toml(root / "universe.toml", "Synthetic universe.", universe)
    _write_toml(root / "evidence.toml", "Synthetic evidence.", _evidence(store))
    hashes = _sec(store)

    fund_document = archive_url(FUND_CIK, f"{FUND_CIK}-25-000001", "primary_doc.xml")
    fund_citation = [{"source_id": "synthetic-fund", "url": fund_document}]
    submissions = submissions_url(9990006)
    submissions_text = ArtifactText(
        store.get("sec-edgar", hashes[pad_cik(9990006)], **RIGHTS).body,
        "application/json",
    )
    overrides = [
        _override(
            "reject-preliminary-date",
            "reject_assertion",
            "index-2024-11-01 sets November 8, replacing the preliminary November 7.",
            membership_assertion_id="index-2024-10-31:corvid-common:added",
            citations=[
                {
                    "source_id": "synthetic-index",
                    "url": "https://index.example/notices/index-2024-11-01",
                }
            ],
        ),
        _override(
            "eastfield-issuer",
            "set_issuer",
            "SEC's record for this CIK lists EFB; EFB Financial is its trade name.",
            security_id="eastfield-common",
            cik=pad_cik(9990006),
            citations=[
                {
                    "source_id": "sec-edgar",
                    "url": submissions,
                    "artifact_sha256": hashes[pad_cik(9990006)],
                    "locator": submissions_text.pointer("/tickers").model_dump(
                        mode="json", exclude_none=True
                    ),
                }
            ],
        ),
        _override(
            "alias-dynamo-a",
            "holding_alias",
            "The fund lists the Class A shares under this name.",
            security_id="dynamo-class-a",
            holding_name="Dynamo Motors Co Class A",
            citations=fund_citation,
        ),
        _override(
            "alias-dynamo-b",
            "holding_alias",
            "The fund lists the Class B shares under this name.",
            security_id="dynamo-class-b",
            holding_name="Dynamo Motors Co Class B",
            citations=fund_citation,
        ),
        _override(
            "alias-eastfield",
            "holding_alias",
            "The fund lists EFB Financial under its legal name.",
            security_id="eastfield-common",
            holding_name="Eastfield Bank Corp",
            citations=fund_citation,
        ),
    ]
    path = root / "overrides.toml"
    _write_toml(
        path, "Synthetic review.", {"schema_version": 1, "overrides": overrides}
    )
    options = build_options(directory)
    lagging = next(
        f
        for f in build(repo, **options).report.findings
        if f.finding_id == "difference:roster-2024-11-08"
    )
    overrides.append(
        _override(
            "ack-lagging-revision",
            "acknowledge",
            "The revision was saved on the change date, before editors updated it;"
            " the next revision agrees.",
            finding_id=lagging.finding_id,
            finding_digest=lagging.digest,
            citations=[
                {
                    "source_id": "synthetic-roster",
                    "url": "https://roster.example/index?rev=1003",
                }
            ],
        )
    )
    _write_toml(
        path, "Synthetic review.", {"schema_version": 1, "overrides": overrides}
    )
    frozen = freeze(build(repo, **options), root / "manifests", now=FROZEN_AT)
    return frozen.path
```

Append to `docs/data-dictionary.md`:

```markdown

## Frozen cohort manifests

- **Where.** `config/universe/<name>/manifests/<universe_id>-v<version>.json` holds
  one `UniverseManifest` as indented JSON with sorted keys, written once and never
  replaced. The synthetic cohort's is under `tests/fixtures/cohort/manifests/`.
- **The content hash.** `content_hash` covers the manifest's canonical JSON without
  `universe_version`, `content_hash`, and `created_at`. Identical content keeps its
  version; new content takes the next.
- **Reading.** `earnings_ingestion.cohort.freeze.load_manifest` rechecks that hash
  and the file's name, and needs no saved artifact.
- **Saved artifacts.** The cohort's are under `data/raw/cohort/`, which is never
  committed; the synthetic cohort's are under `tests/fixtures/cohort/raw/`.
```

This is block 4 for that path: extract it with
`python3 /tmp/plan6-extract.py docs/data-dictionary.md 4`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_import_boundaries.py -q`

Expected: `35 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py packages/earnings-ingestion/src/earnings_ingestion/cohort/synthetic.py packages/earnings-ingestion/tests/conftest.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_import_boundaries.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `873 passed, 23 deselected`;
`All checks passed!` and `198 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py packages/earnings-ingestion/src/earnings_ingestion/cohort/freeze.py packages/earnings-ingestion/src/earnings_ingestion/cohort/synthetic.py packages/earnings-ingestion/tests/conftest.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_import_boundaries.py docs/data-dictionary.md
git commit -m "feat(ingestion): build, freeze, and synthesize the point-in-time cohort"
```

---
### Task 13: The committed synthetic cohort, replayed offline

The synthetic cohort is committed under `tests/fixtures/cohort/`, where Stage 5 will
find it, and it replays offline to its frozen manifest. That replay is P-VI's
membership-interval and issuer-resolution legs.

- **The replay** runs with sockets refused, so building and freezing provably read
  only committed files and saved artifacts.
- **Regeneration.** The fixture must regenerate byte for byte, so a generator change
  cannot silently drift from the committed files.
- **Byte-exact checkout.** Saved artifacts are named by their hash, so
  `.gitattributes` marks every fixture file `-text`, and a line-ending conversion on
  checkout cannot break one.
- **Local evidence.** The real cohort's evidence under `data/raw/cohort/` stays
  ignored.

**Files:**

- Create: `tests/integration/regenerate_cohort_fixtures.py`, which pytest never
  collects, and `tests/integration/test_cohort_fixtures.py`.
- Create (generated): `tests/fixtures/cohort/`, 55 files.
- Modify: `.gitattributes` (one line appended).

**Interfaces:**

- Consumes: Task 12's `build`, `freeze`, `load_manifest`, `FIXTURE_DIR`,
  `build_options`, and `write_synthetic_cohort`.
- Produces:
  - `tests/fixtures/cohort/`:
    - `universe.toml`, `evidence.toml`, and `overrides.toml`;
    - `membership-source-register.toml` and `source-register.toml`;
    - `raw/<source_id>/`, the saved artifacts and their retrieval records;
    - `manifests/djia-synthetic-v1.json`, the frozen manifest Stage 5 consumes.
  - The command
    `uv run --locked --all-packages python tests/integration/regenerate_cohort_fixtures.py`.

- [ ] **Step 1: Write the failing tests**

Create `tests/integration/test_cohort_fixtures.py`:

```python
"""The committed synthetic cohort: it regenerates byte for byte, and replays offline
from saved evidence to its frozen manifest (P-VI's membership and issuer legs).

The replay runs with sockets disabled: building and freezing read committed files and
saved artifacts, never the network, and need no credential (P §Verification).
"""

import socket
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.freeze import freeze, load_manifest
from earnings_ingestion.cohort.synthetic import (
    FIXTURE_DIR,
    build_options,
    write_synthetic_cohort,
)

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / FIXTURE_DIR / "manifests" / "djia-synthetic-v1.json"
REGENERATE = "uv run --locked --all-packages python tests/integration/regenerate_cohort_fixtures.py"


def files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_the_fixture_regenerates_byte_for_byte(tmp_path: Path) -> None:
    write_synthetic_cohort(tmp_path, FIXTURE_DIR)
    fresh, committed = files(tmp_path / FIXTURE_DIR), files(REPO / FIXTURE_DIR)
    changed = sorted(
        name
        for name in fresh.keys() | committed.keys()
        if fresh.get(name) != committed.get(name)
    )
    assert not changed, f"regenerate with `{REGENERATE}`; differs: {changed[:5]}"


@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("the offline cohort path opened a network connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


@pytest.mark.usefixtures("offline")
def test_saved_evidence_replays_to_the_frozen_manifest(tmp_path: Path) -> None:
    built = build(REPO, **build_options())
    committed = load_manifest(MANIFEST)
    assert built.content_hash == committed.definition.content_hash
    again = freeze(built, REPO / FIXTURE_DIR / "manifests", now=datetime.now(UTC))
    assert (again.created, again.path) == (False, MANIFEST)


def test_every_interval_rests_on_supported_evidence() -> None:
    manifest = load_manifest(MANIFEST)
    assertions = {a.membership_assertion_id: a for a in manifest.assertions}
    for interval in manifest.intervals:
        assert interval.assertion_ids
        for assertion_id in interval.assertion_ids:
            assertion = assertions[assertion_id]
            assert assertion.status == "supported"
            assert assertion.evidence_locators
            assert (assertion.effective_from, assertion.effective_to) == (
                interval.effective_from,
                interval.effective_to,
            )


def test_every_resolved_cik_is_ten_digits_and_one_issuer_per_cik() -> None:
    manifest = load_manifest(MANIFEST)
    ciks = [m.cik for m in manifest.mappings if m.cik is not None]
    assert ciks and all(len(cik) == 10 and cik.isdigit() for cik in ciks)
    assert len({i.cik for i in manifest.issuers}) == len(manifest.issuers)
    in_issuers = {s for i in manifest.issuers for s in i.security_ids}
    assert in_issuers == {m.security_id for m in manifest.mappings if m.cik}


def test_the_candidate_issuers_are_the_in_scope_securities_issuers() -> None:
    manifest = load_manifest(MANIFEST)
    definition = manifest.definition
    stop = definition.public_information_cutoff.toordinal() + 1
    in_scope = {
        i.security_id
        for i in manifest.intervals
        if i.overlaps(definition.period_end_start, datetime.fromordinal(stop).date())
    }
    mappings = {m.security_id: m for m in manifest.mappings}
    assert manifest.candidate_issuer_ids == tuple(
        sorted({mappings[s].issuer_id for s in in_scope if mappings[s].issuer_id})
    )


def ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", path],
        cwd=REPO,
        check=False,
    )
    return result.returncode == 0


def test_saved_evidence_stays_local_and_the_fixture_is_committed() -> None:
    assert ignored("data/raw/cohort/wikipedia-djia/page.html")
    assert ignored("data/runs/cohort/live/20261001T000000Z.json")
    committed = files(REPO / FIXTURE_DIR)
    assert committed, f"{FIXTURE_DIR} holds no fixture"
    for path in committed:
        assert not ignored(f"{FIXTURE_DIR.as_posix()}/{path}"), path


def test_git_keeps_every_fixture_byte() -> None:
    """Saved artifacts are named by their hash, so a line-ending conversion on checkout
    would break them: .gitattributes marks every fixture file -text."""
    names = [f"{FIXTURE_DIR.as_posix()}/{path}" for path in files(REPO / FIXTURE_DIR)]
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

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest tests/integration/test_cohort_fixtures.py -q`

Expected: FAIL: `7 failed`, because `tests/fixtures/cohort/` does not exist yet.

- [ ] **Step 3: Generate the fixture, and keep its bytes**

Create `tests/integration/regenerate_cohort_fixtures.py`:

```python
"""Regenerate tests/fixtures/cohort/, the synthetic cohort (Stage 4, plan 6).

    uv run --locked --all-packages python tests/integration/regenerate_cohort_fixtures.py

Replaces the whole directory with ``earnings_ingestion.cohort.synthetic``'s output:
registers, saved artifacts, curated files, overrides, and the frozen manifest. Run it
only when test_cohort_fixtures.py reports that the committed fixture no longer matches
the generator, and commit the generator change with it. pytest never collects this
file.
"""

import shutil
from pathlib import Path

from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, write_synthetic_cohort

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    shutil.rmtree(REPO / FIXTURE_DIR, ignore_errors=True)
    manifest = write_synthetic_cohort(REPO, FIXTURE_DIR)
    print(f"wrote {manifest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Append to `.gitattributes`:

```text
tests/fixtures/cohort/** -text
```

Run: `uv run --locked --all-packages python tests/integration/regenerate_cohort_fixtures.py`

Expected: `wrote tests/fixtures/cohort/manifests/djia-synthetic-v1.json`.

Run: `find tests/fixtures/cohort -type f | wc -l`

Expected: `55`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest tests/integration/test_cohort_fixtures.py -q`

Expected: `7 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan6-escapes.py tests/integration/regenerate_cohort_fixtures.py tests/integration/test_cohort_fixtures.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `880 passed, 23 deselected`;
`All checks passed!` and `200 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add .gitattributes tests/integration/regenerate_cohort_fixtures.py tests/integration/test_cohort_fixtures.py tests/fixtures/cohort
git commit -m "test(cohort): commit the synthetic cohort and replay it offline"
```

---
### Task 14: The web client, acquisition, and citing

This is every network step of Stage 4 except the live verification.

- **The web client** (P6-17) fetches non-SEC pages at one request per second.
  - It uses the identity in `SOURCE_IDENTITY`.
  - It reaches only the hosts it is opened for, and never an SEC host.
  - It checks each page against its site's robots.txt first. A disallowed page
    raises `RobotsRefusal`, whose message tells the user to save the page and
    register it. It names `earnings-pipeline cohort register`, which Task 16 adds.
- **`acquire.py`:**
  - `fetch_page` saves a registered source's page;
  - `register_saved` records a page a person saved, as `saved_by_user`;
  - `fetch_sec` saves every SEC record the build reads:
    - the ticker list;
    - the submissions of each CIK that a cited ticker proposes or an override
      names;
    - the fund's submissions and older pages;
    - the fund's N-PORT documents over the window, each fetched once.
  - `cite` returns a locator and the cited text, and `--line` takes a whole table
    row;
  - `terms_digest` hashes a terms page the way the register does.
- **Import check.** `cohort.web` joins the modules that load nothing forbidden.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/web.py` and
  `cohort/acquire.py`.
- Modify: `packages/earnings-ingestion/tests/test_import_boundaries.py` (replaced
  whole, block 3 of 3).
- Test (create): `packages/earnings-ingestion/tests/test_cohort_web.py` and
  `test_cohort_acquire.py`.

**Interfaces:**

- Consumes:
  - Tasks 2 and 3's `PoliteClient`, `ProcessLock`, `Throttle`, `require_identity`,
    `AccessStop`, `Fetched`, and `RobotsGate`;
  - Task 4's `is_sec_host` and URL builders, and Task 5's readers;
  - Task 1's store;
  - Task 7's `Registers` and `CohortConfig`;
  - Task 8's `ArtifactText`;
  - Task 12's synthetic cohort, in the tests.
- Produces:
  - `cohort/web.py`:
    - `IDENTITY_ENV = "SOURCE_IDENTITY"`, `MIN_INTERVAL_SECONDS = 1.0`, and
      `LOCK_PATH`;
    - `RobotsRefusal(AccessStop)`;
    - `WebFetcher(client, gate)`, with `fetch(url, expected_types) -> Fetched`;
    - `hosts_of(urls) -> frozenset[str]`;
    - the context manager
      `open_web_client(repo, hosts, *, environ=None, max_requests=500, transport=None, clock=..., sleep=..., rng=None, now=...)`,
      which yields a `WebFetcher`, and raises `ValueError` for an SEC host.
  - `cohort/acquire.py`:
    - the media-type sets `JSON`, `HTML`, and `XML`;
    - `fetch_page(fetch, store, registers, source_id, url) -> ArtifactRef`;
    - `register_saved(store, registers, source_id, body, *, url, media_type, saved_at) -> ArtifactRef`;
    - `SecFetch(fetched, kept)`;
    - `fetch_sec(fetch, store, registers, config) -> SecFetch`;
    - `cite(store, registers, source_id, sha256, *, find=None, occurrence=1, span=None, pointer=None, line=False) -> tuple[EvidenceLocator, str]`;
    - `terms_digest(body, media_type) -> str`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_cohort_web.py`:

```python
"""The cohort web client: registered hosts only, never SEC, robots.txt first."""

import httpx
import pytest
from earnings_ingestion.cohort.web import (
    RobotsRefusal,
    hosts_of,
    open_web_client,
)
from earnings_ingestion.fetch.client import AccessStop

ENVIRON = {"SOURCE_IDENTITY": "Jane Doe earnings-themes research jane@example.org"}
ROBOTS = b"User-agent: *\nDisallow: /w/\n"


def opened(tmp_path, handler, hosts=("roster.example",)):
    return open_web_client(
        tmp_path,
        hosts,
        environ=ENVIRON,
        transport=httpx.MockTransport(handler),
        sleep=lambda seconds: None,
    )


def site(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/robots.txt":
        return httpx.Response(200, content=ROBOTS)
    return httpx.Response(
        200, content=b"<p>A roster.</p>", headers={"Content-Type": "text/html"}
    )


def test_an_allowed_page_is_fetched_after_robots(tmp_path) -> None:
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return site(request)

    with opened(tmp_path, handler) as web:
        fetched = web.fetch("https://roster.example/wiki/Roster?oldid=1", {"text/html"})
    assert fetched.body == b"<p>A roster.</p>"
    assert seen == ["/robots.txt", "/wiki/Roster"]


def test_a_disallowed_page_is_refused_unrequested(tmp_path) -> None:
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return site(request)

    with (
        opened(tmp_path, handler) as web,
        pytest.raises(RobotsRefusal, match="Disallow: /w/"),
    ):
        web.fetch("https://roster.example/w/index.php?oldid=1", {"text/html"})
    assert seen == ["/robots.txt"]


def test_an_unregistered_host_is_refused(tmp_path) -> None:
    with opened(tmp_path, site) as web, pytest.raises(AccessStop, match="outside"):
        web.fetch("https://elsewhere.example/page", {"text/html"})


def test_sec_hosts_belong_to_the_sec_client(tmp_path) -> None:
    with (
        pytest.raises(ValueError, match="shared SEC client"),
        opened(tmp_path, site, hosts=("roster.example", "www.sec.gov")),
    ):
        pass


def test_an_identity_is_required(tmp_path) -> None:
    with (
        pytest.raises(AccessStop, match="SOURCE_IDENTITY"),
        open_web_client(tmp_path, ["roster.example"], environ={}),
    ):
        pass


def test_hosts_come_from_urls() -> None:
    urls = ["https://roster.example/a", "https://index.example/b?x=1"]
    assert hosts_of(urls) == {"roster.example", "index.example"}
```

Create `packages/earnings-ingestion/tests/test_cohort_acquire.py`:

```python
"""Acquisition, offline: a fake fetch serves the synthetic cohort's SEC records."""

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.cohort.acquire import (
    cite,
    fetch_page,
    fetch_sec,
    register_saved,
    terms_digest,
)
from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.config import load_cohort_config
from earnings_ingestion.cohort.register import load_registers
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, build_options
from earnings_ingestion.fetch.client import Fetched
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore

RAW = FIXTURE_DIR / "raw"
SYNTHETIC = {
    "rights_status": RightsStatus.REDISTRIBUTABLE,
    "rights_basis": "synthetic test data, invented for this repository",
}
NOW = datetime(2026, 9, 30, 9, 0, tzinfo=UTC)


def served(repo: Path, *sources: str) -> dict[str, tuple[bytes, str]]:
    """Every saved artifact of ``sources``, by the URL it came from."""
    store = ArtifactStore(repo / RAW, repo)
    pages = {}
    for source_id in sources:
        for path in (repo / RAW / source_id / "retrievals").glob("*/*.json"):
            record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            body = store.get(source_id, record.sha256, **SYNTHETIC).body
            pages[record.request_url] = (body, record.media_type)
    return pages


def fake(pages: dict[str, tuple[bytes, str]], requested: list[str]):
    def fetch(url: str, types: frozenset[str]) -> Fetched:
        requested.append(url)
        body, media = pages[url]
        assert media in types
        return Fetched(
            body=body,
            retrieval=Retrieval(
                request_url=url,
                final_url=url,
                retrieved_at=NOW,
                retrieval_method=RetrievalMethod.HTTP,
                http_status=200,
                media_type=media,
                content_type=media,
                byte_count=len(body),
                sha256=sha256_hex(body),
            ),
        )

    return fetch


def test_fetch_sec_saves_every_record_the_build_reads(cohort_repo) -> None:
    pages = served(cohort_repo, "sec-edgar", "synthetic-fund")
    for source_id in ("sec-edgar", "synthetic-fund"):
        shutil.rmtree(cohort_repo / RAW / source_id)
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    options = build_options()
    registers = load_registers(
        cohort_repo, options["register"], options["sec_register"]
    )
    config = load_cohort_config(cohort_repo / FIXTURE_DIR)
    requested: list[str] = []

    first = fetch_sec(fake(pages, requested), store, registers, config)
    assert sorted(first.fetched) == sorted(pages)
    assert first.kept == []
    rebuilt = build(cohort_repo, **options)
    assert rebuilt.report.blocking == ()
    assert rebuilt.candidate_issuer_ids == (
        "cik-0009990001",
        "cik-0009990002",
        "cik-0009990003",
        "cik-0009990005",
        "cik-0009990006",
    )

    again = fetch_sec(fake(pages, requested), store, registers, config)
    assert len(again.kept) == 10
    assert all("/Archives/" not in url for url in again.fetched)


def registers_of(repo: Path):
    options = build_options()
    return load_registers(repo, options["register"], options["sec_register"])


def test_a_hand_saved_page_records_that_nothing_was_fetched(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    ref = register_saved(
        store,
        registers_of(cohort_repo),
        "synthetic-index",
        b"<p>Saved in a browser.</p>",
        url="https://index.example/notices/saved",
        media_type="text/html",
        saved_at=NOW,
    )
    (retrieval,) = store.get(
        "synthetic-index", ref.content_sha256, **SYNTHETIC
    ).retrievals
    assert retrieval.retrieval_method is RetrievalMethod.SAVED_BY_USER
    assert retrieval.http_status is None


def test_a_page_is_saved_only_for_a_registered_source(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    pages = {"https://index.example/a": (b"<p>A notice.</p>", "text/html")}
    fetch = fake(pages, [])
    ref = fetch_page(
        fetch,
        store,
        registers_of(cohort_repo),
        "synthetic-index",
        "https://index.example/a",
    )
    assert ref.storage_ref.startswith("tests/fixtures/cohort/raw/synthetic-index/")
    with pytest.raises(ValueError, match="not in the membership source register"):
        fetch_page(
            fetch,
            store,
            registers_of(cohort_repo),
            "elsewhere",
            "https://index.example/a",
        )


def test_cite_finds_a_span_or_a_pointer_and_shows_its_text(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    registers = registers_of(cohort_repo)
    page = next(iter(served(cohort_repo, "synthetic-index").values()))[0]
    locator, text = cite(
        store,
        registers,
        "synthetic-index",
        sha256_hex(page),
        find="Synthetic Industrial Average",
    )
    assert text == "Synthetic Industrial Average"
    assert locator.canonicalization_version == "walker-1"
    again, same = cite(
        store,
        registers,
        "synthetic-index",
        sha256_hex(page),
        span=(locator.start, locator.end),
    )
    assert (again, same) == (locator, text)
    tickers = next(
        body
        for url, (body, _) in served(cohort_repo, "sec-edgar").items()
        if url.endswith("company_tickers.json")
    )
    pointed, value = cite(
        store, registers, "sec-edgar", sha256_hex(tickers), pointer="/0/ticker"
    )
    assert (pointed.pointer, value) == ("/0/ticker", '"ACME"')
    with pytest.raises(ValueError, match="exactly one"):
        cite(store, registers, "sec-edgar", sha256_hex(tickers))


def test_cite_can_take_the_whole_line_holding_a_row(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    registers = registers_of(cohort_repo)
    page = next(iter(served(cohort_repo, "synthetic-roster").values()))[0]
    locator, text = cite(
        store, registers, "synthetic-roster", sha256_hex(page), find="ACM", line=True
    )
    assert "\t" in text and "ACM" in text and "\n" not in text
    found, _ = cite(store, registers, "synthetic-roster", sha256_hex(page), find="ACM")
    assert locator.start <= found.start < found.end <= locator.end
    with pytest.raises(ValueError, match="line needs find"):
        cite(
            store,
            registers,
            "synthetic-roster",
            sha256_hex(page),
            span=(0, 3),
            line=True,
        )


def test_a_terms_page_is_hashed_by_its_canonical_text() -> None:
    page = b"<html><body><p>Terms.</p></body></html>"
    assert terms_digest(page, "text/html") == terms_digest(
        page.replace(b"<p>", b"<p class='x'>"), "text/html"
    )
    assert terms_digest(b"plain", "text/plain") == sha256_hex(b"plain")
```

Replace `packages/earnings-ingestion/tests/test_import_boundaries.py` with:

```python
"""earnings-ingestion imports neither earnings-themes nor the application, and no
browser: browser capture stays behind an optional extra (A §173; B3).

Only ``earnings_ingestion.browser.selenium_capture`` may load a browser library, and
only when something imports it; tests/contracts/test_import_scan.py checks the source
statically as well. The cohort's offline path, from saved artifacts to a frozen
manifest, loads no network client (A §410).
"""

import json
import subprocess
import sys

import pytest

FORBIDDEN = {
    "earnings_themes",
    "earnings_pipeline",
    "selenium",
    "websocket",
    "playwright",
    "pyppeteer",
}


def modules_loaded_by(module: str) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing ``module``."""
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return {name.partition(".")[0] for name in json.loads(result.stdout)}


@pytest.mark.parametrize(
    "module",
    [
        "earnings_ingestion",
        "earnings_ingestion.browser",
        "earnings_ingestion.browser.install",
        "earnings_ingestion.browser.renderer",
        "earnings_ingestion.browser.serialize",
        "earnings_ingestion.browser.store",
        "earnings_ingestion.layout",
        "earnings_ingestion.layout.extract",
        "earnings_ingestion.fetch.client",
        "earnings_ingestion.fetch.robots",
        "earnings_ingestion.sec.client",
        "earnings_ingestion.cohort.build",
        "earnings_ingestion.cohort.web",
    ],
)
def test_importing_ingestion_loads_nothing_forbidden(module: str) -> None:
    assert modules_loaded_by(module) & FORBIDDEN == set()


NETWORK = {
    "httpx",
    "earnings_ingestion.fetch.client",
    "earnings_ingestion.sec.client",
    "earnings_ingestion.cohort.web",
}


def full_modules_loaded_by(module: str) -> set[str]:
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return set(json.loads(result.stdout))


@pytest.mark.parametrize(
    "module",
    [
        "earnings_ingestion.cohort.build",
        "earnings_ingestion.cohort.freeze",
        "earnings_ingestion.cohort.synthetic",
        "earnings_ingestion.sec.data",
        "earnings_ingestion.sec.urls",
        "earnings_ingestion.fetch.store",
    ],
)
def test_the_offline_cohort_path_loads_no_network_client(module: str) -> None:
    """Building and freezing read saved bytes; they cannot reach the network (A §410)."""
    assert full_modules_loaded_by(module) & NETWORK == set()
```

This is block 3 for that path: extract it with
`python3 /tmp/plan6-extract.py packages/earnings-ingestion/tests/test_import_boundaries.py 3`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_web.py packages/earnings-ingestion/tests/test_cohort_acquire.py packages/earnings-ingestion/tests/test_import_boundaries.py -q`

Expected: FAIL. Collection stops in the two new files, first with
`No module named 'earnings_ingestion.cohort.web'`, and pytest reports `2 errors`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/web.py`:

```python
"""The cohort's client for sources outside SEC: roster revisions and index notices.

- **Polite.** One request per second across these hosts, within a per-run budget,
  with the SEC client's retries, ``Retry-After`` handling, and stop on a persistent
  403. The User-Agent is the identity in ``SOURCE_IDENTITY``, configured outside Git
  and never recorded.
- **Registered hosts only.** It reaches only the hosts it is opened for, the hosts of
  registered sources, and never an SEC host: SEC requests go through the shared SEC
  client alone (D5).
- **Robots first.** Each page is checked against its site's robots.txt (RFC 9309)
  before it is requested. A disallowed page is refused, never fetched: a person saves
  it in a browser and registers it instead (P §Membership evidence: live acquisition
  never bypasses robots restrictions).
"""

import random
import time
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from earnings_ingestion.fetch.client import (
    DEFAULT_MAX_REQUESTS,
    AccessStop,
    Fetched,
    PoliteClient,
    ProcessLock,
    Throttle,
    require_identity,
)
from earnings_ingestion.fetch.robots import RobotsGate
from earnings_ingestion.sec.urls import is_sec_host

IDENTITY_ENV = "SOURCE_IDENTITY"
MIN_INTERVAL_SECONDS = 1.0
LOCK_PATH = Path("data") / "runs" / "cohort" / "web-client.lock"


class RobotsRefusal(AccessStop):
    """robots.txt disallows the page; save it in a browser and register it."""


class WebFetcher:
    """Fetches a page only after its site's robots.txt allows it."""

    def __init__(self, client: PoliteClient, gate: RobotsGate) -> None:
        self.client = client
        self.gate = gate

    def fetch(self, url: str, expected_types: Collection[str]) -> Fetched:
        verdict = self.gate.verdict(url)
        if not verdict.allowed:
            reason = verdict.rule or f"robots.txt answered {verdict.robots_status}"
            raise RobotsRefusal(
                f"{url} is refused by robots.txt ({reason}); save it in a browser"
                " and register it with `earnings-pipeline cohort register`"
            )
        return self.client.fetch(url, expected_types)


def hosts_of(urls: Iterable[str]) -> frozenset[str]:
    return frozenset(urlsplit(url).hostname or "" for url in urls) - {""}


@contextmanager
def open_web_client(
    repo: Path,
    hosts: Iterable[str],
    *,
    environ: Mapping[str, str] | None = None,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    transport: httpx.BaseTransport | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Iterator[WebFetcher]:
    """The machine's one cohort web client, for ``hosts`` only."""
    allowed = frozenset(host.lower() for host in hosts)
    sec = sorted(host for host in allowed if is_sec_host(host))
    if sec:
        raise ValueError(f"SEC hosts go through the shared SEC client: {sec}")
    identity = require_identity(IDENTITY_ENV, environ)
    with ProcessLock(repo / LOCK_PATH):
        throttle = Throttle(
            min_interval=MIN_INTERVAL_SECONDS,
            max_requests=max_requests,
            clock=clock,
            sleep=sleep,
        )
        client = PoliteClient(
            identity,
            throttle=throttle,
            host_allowed=allowed.__contains__,
            transport=transport,
            sleep=sleep,
            rng=rng,
            now=now,
        )
        try:
            yield WebFetcher(client, RobotsGate(client))
        finally:
            client.close()
```

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/acquire.py`:

```python
"""Acquire and cite cohort evidence: every network step of Stage 4 lives here.

- ``fetch_page`` saves a roster revision or index notice through the web client.
- ``register_saved`` saves a page a person saved in a browser, for a source whose
  robots.txt or access refuses automated fetching; it records that nothing was
  fetched (``saved_by_user``).
- ``fetch_sec`` saves, through the shared SEC client, SEC's ticker list, the
  submissions of every CIK a cited ticker proposes or an override names, and the
  fund's N-PORT filings over the window. Filed documents are fetched once; the
  ticker list and submissions are fetched fresh, and the build uses the latest.
- ``cite`` finds evidence in a saved artifact and returns its locator, with the cited
  text for a person's terminal; that text never goes into a committed file.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from earnings_core import ArtifactRef, sha256_hex

from earnings_ingestion.cohort.config import CohortConfig
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.cohort.records import EvidenceLocator, OverrideKind
from earnings_ingestion.cohort.register import Registers
from earnings_ingestion.fetch.client import Fetched
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.data import (
    raw_document_name,
    read_company_tickers,
    read_submissions,
    read_submissions_page,
)
from earnings_ingestion.sec.urls import (
    COMPANY_TICKERS_URL,
    archive_url,
    submissions_page_url,
    submissions_url,
)

JSON = frozenset({"application/json"})
HTML = frozenset({"text/html"})
XML = frozenset({"application/xml", "text/xml"})


def _put(
    store: ArtifactStore,
    registers: Registers,
    source_id: str,
    body: bytes,
    retrieval: Retrieval,
) -> ArtifactRef:
    rights = registers.rights(source_id)
    return store.put(
        source_id,
        body,
        retrieval,
        rights_status=rights.rights_status,
        rights_basis=rights.rights_basis,
    )


def fetch_page(
    fetch: Callable[[str, frozenset[str]], Fetched],
    store: ArtifactStore,
    registers: Registers,
    source_id: str,
    url: str,
) -> ArtifactRef:
    """Fetch one HTML page of a registered source and save it."""
    registers.entry(source_id)
    fetched = fetch(url, HTML)
    return _put(store, registers, source_id, fetched.body, fetched.retrieval)


def register_saved(
    store: ArtifactStore,
    registers: Registers,
    source_id: str,
    body: bytes,
    *,
    url: str,
    media_type: str,
    saved_at: datetime,
) -> ArtifactRef:
    """Save a page a person saved in a browser from ``url`` at ``saved_at``."""
    registers.entry(source_id)
    retrieval = Retrieval(
        request_url=url,
        final_url=url,
        retrieved_at=saved_at,
        retrieval_method=RetrievalMethod.SAVED_BY_USER,
        http_status=None,
        media_type=media_type,
        content_type=media_type,
        byte_count=len(body),
        sha256=sha256_hex(body),
    )
    return _put(store, registers, source_id, body, retrieval)


@dataclass
class SecFetch:
    """What ``fetch_sec`` requested, and what it found already saved."""

    fetched: list[str]
    kept: list[str]


def fetch_sec(
    fetch: Callable[[str, frozenset[str]], Fetched],
    store: ArtifactStore,
    registers: Registers,
    config: CohortConfig,
) -> SecFetch:
    """Save every SEC record the build reads for ``config``."""
    result = SecFetch(fetched=[], kept=[])

    def get(source_id: str, url: str, types: frozenset[str]) -> bytes:
        fetched = fetch(url, types)
        _put(store, registers, source_id, fetched.body, fetched.retrieval)
        result.fetched.append(url)
        return fetched.body

    entries = read_company_tickers(get("sec-edgar", COMPANY_TICKERS_URL, JSON))
    evidence = config.evidence
    rows = [
        *(row for item in evidence.snapshots for row in item.members),
        *(row for item in evidence.changes for row in item.entries),
    ]
    cited = {row.ticker for row in rows}
    ciks = {entry.cik for entry in entries if entry.ticker in cited}
    ciks |= {
        o.cik for o in config.overrides.overrides if o.kind is OverrideKind.SET_ISSUER
    }
    for cik in sorted(ciks):
        get("sec-edgar", submissions_url(cik), JSON)

    universe = config.universe
    proxy = universe.etf_proxy
    if proxy is None:
        return result
    registrant = read_submissions(get("sec-edgar", submissions_url(proxy.cik), JSON))
    filings = list(registrant.filings)
    for page in registrant.older_pages:
        filings += read_submissions_page(
            get("sec-edgar", submissions_page_url(page), JSON)
        )
    rights = registers.rights(proxy.source_id)
    for filing in filings:
        if filing.form not in proxy.forms or filing.report_date is None:
            continue
        if (
            not universe.period_end_start
            <= filing.report_date
            <= universe.public_information_cutoff
        ):
            continue
        url = archive_url(
            proxy.cik, filing.accession, raw_document_name(filing.primary_document)
        )
        saved = store.latest(
            proxy.source_id,
            url,
            rights_status=rights.rights_status,
            rights_basis=rights.rights_basis,
        )
        if saved is not None:
            result.kept.append(url)
            continue
        get(proxy.source_id, url, XML)
    return result


def cite(
    store: ArtifactStore,
    registers: Registers,
    source_id: str,
    sha256: str,
    *,
    find: str | None = None,
    occurrence: int = 1,
    span: tuple[int, int] | None = None,
    pointer: str | None = None,
    line: bool = False,
) -> tuple[EvidenceLocator, str]:
    """A locator into a saved artifact, and the text it cites (for the terminal).
    With ``line``, the locator spans the whole line holding the found text."""
    if sum(option is not None for option in (find, span, pointer)) != 1:
        raise ValueError("give exactly one of find, span, or pointer")
    if line and find is None:
        raise ValueError("line needs find")
    rights = registers.rights(source_id)
    stored = store.get(
        source_id,
        sha256,
        rights_status=rights.rights_status,
        rights_basis=rights.rights_basis,
    )
    text = ArtifactText(stored.body, stored.ref.media_type)
    if find is not None:
        locator = (text.line if line else text.find)(find, occurrence)
    elif span is not None:
        locator = text.span(*span)
    else:
        locator = text.pointer(pointer)
    return locator, text.cited(locator)


def terms_digest(body: bytes, media_type: str) -> str:
    """The hash a register records for a terms page: its canonical text's, if HTML."""
    if media_type.partition(";")[0].strip().lower() == "text/html":
        return ArtifactText(body, media_type).canonical[1]
    return sha256_hex(body)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_web.py packages/earnings-ingestion/tests/test_cohort_acquire.py packages/earnings-ingestion/tests/test_import_boundaries.py -q`

Expected: `31 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/web.py packages/earnings-ingestion/src/earnings_ingestion/cohort/acquire.py packages/earnings-ingestion/tests/test_cohort_web.py packages/earnings-ingestion/tests/test_cohort_acquire.py packages/earnings-ingestion/tests/test_import_boundaries.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `893 passed, 23 deselected`;
`All checks passed!` and `204 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/cohort/web.py packages/earnings-ingestion/src/earnings_ingestion/cohort/acquire.py packages/earnings-ingestion/tests/test_cohort_web.py packages/earnings-ingestion/tests/test_cohort_acquire.py packages/earnings-ingestion/tests/test_import_boundaries.py
git commit -m "feat(ingestion): acquire and cite cohort evidence through the web and SEC clients"
```

---
### Task 15: The live verification (P-VL)

`verify_live` re-reads every source the frozen cohort relies on (P6-20).

- **Terms.** Each cited source's terms page is fetched and hashed as the register
  hashes it.
- **Evidence.** Each curated snapshot and change URL is fetched again, and compared
  with the saved bytes.
- **Rebuild.** The cohort is rebuilt from the saved artifacts, and compared with the
  latest frozen manifest's content hash.
- **Routing.** SEC hosts go through the shared SEC client, and every other host
  through the web client.
- **Refusals.** A robots refusal is `refused`, and the client goes on. A persistent
  403 or block page is `refused` too, and that client sends nothing more: its later
  checks are `failed`, never requested.
- **Recording.** `run_live` opens both clients and writes the `LiveVerification`
  record, with each check's retrieval, under the gitignored
  `data/runs/cohort/live/`.

The unit tests drive `verify_live` with fake fetchers over the synthetic cohort. The
integration test runs the real verification, and is `live`: it never runs by default.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py`.
- Test (create): `packages/earnings-ingestion/tests/test_cohort_live.py`, and
  `tests/integration/test_cohort_live.py`, marked `live`.

**Interfaces:**

- Consumes:
  - Task 14's `terms_digest`, `HTML`, `RobotsRefusal`, and `open_web_client`;
  - Task 12's `build`, `CohortError`, and `frozen_manifests`;
  - Task 4's `open_sec_client` and `is_sec_host`;
  - Task 6's `LiveCheck` and `LiveVerification`;
  - Task 1's `write_new`.
- Produces, in `cohort/live.py`:
  - `Fetch`, the fetcher type;
  - `LIVE_RUNS`, which is `data/runs/cohort/live`;
  - `ANY`, the media types a terms page may have;
  - `verify_live(repo, *, fetch_web, fetch_sec, now, options=None) -> LiveVerification`;
  - `default_options() -> dict[str, Path]`;
  - `run_live(repo, *, environ=None) -> tuple[LiveVerification, Path]`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_cohort_live.py`:

```python
"""The live verification's logic, offline: fake fetches stand in for the clients."""

from datetime import UTC, datetime

from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.cohort.live import verify_live
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, build_options
from earnings_ingestion.cohort.web import RobotsRefusal
from earnings_ingestion.fetch.client import AccessStop, Fetched
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore

NOW = datetime(2026, 10, 2, 9, 0, tzinfo=UTC)
RIGHTS = {
    "rights_status": RightsStatus.REDISTRIBUTABLE,
    "rights_basis": "synthetic test data, invented for this repository",
}


def pages(repo) -> dict[str, tuple[bytes, str]]:
    store = ArtifactStore(repo / FIXTURE_DIR / "raw", repo)
    served = {}
    for source_id in ("synthetic-roster", "synthetic-index"):
        for path in (repo / FIXTURE_DIR / "raw" / source_id / "retrievals").glob(
            "*/*.json"
        ):
            record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            body = store.get(source_id, record.sha256, **RIGHTS).body
            served[record.request_url] = (body, "text/html")
    return served


def fake(served, refuse=frozenset(), block=frozenset()):
    def fetch(url, types):
        if url in refuse:
            raise RobotsRefusal(f"{url} is refused by robots.txt (Disallow: /)")
        if url in block:
            raise AccessStop(
                f"403 persisted for {url}; stopping without changing identity"
            )
        body, media = served.get(url, (b"synthetic terms", "text/plain"))
        return Fetched(
            body=body,
            retrieval=Retrieval(
                request_url=url,
                final_url=url,
                retrieved_at=NOW,
                retrieval_method=RetrievalMethod.HTTP,
                http_status=200,
                media_type=media,
                content_type=media,
                byte_count=len(body),
                sha256=sha256_hex(body),
            ),
        )

    return fetch


def test_an_unchanged_world_rebuilds_the_frozen_manifest(cohort_repo) -> None:
    served = pages(cohort_repo)
    result = verify_live(
        cohort_repo,
        fetch_web=fake(served),
        fetch_sec=fake(served),
        now=NOW,
        options=build_options(),
    )
    assert {check.outcome for check in result.checks} == {"unchanged"}
    assert {check.purpose for check in result.checks} == {"terms", "evidence"}
    assert all(check.retrieval is not None for check in result.checks)
    assert result.rebuilt_content_hash == result.frozen_content_hash
    assert result.blocking_finding_ids == ()
    assert result.build_problems == ()


def test_changes_and_refusals_are_recorded_not_hidden(cohort_repo) -> None:
    served = pages(cohort_repo)
    changed = "https://roster.example/index?rev=1001"
    served[changed] = (b"<p>A newer revision.</p>", "text/html")
    refused = "https://index.example/notices/index-2024-11-01"
    blocked = "https://www.sec.gov/privacy"
    result = verify_live(
        cohort_repo,
        fetch_web=fake(served, refuse={refused}),
        fetch_sec=fake(served, block={blocked}),
        now=NOW,
        options=build_options(),
    )
    outcomes = {check.url: check.outcome for check in result.checks}
    assert outcomes[changed] == "changed"
    assert outcomes[refused] == "refused"
    assert outcomes[blocked] == "refused"
    assert result.rebuilt_content_hash == result.frozen_content_hash
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_live.py -q`

Expected: FAIL. Collection stops with
`No module named 'earnings_ingestion.cohort.live'`, and pytest reports `1 error`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py`:

```python
"""The opt-in live verification (P-VL): re-read every source the cohort relies on.

- **Terms.** Each cited source's terms page is fetched and hashed the way the
  register hashes it. A different hash is ``changed``: a person rereads the terms,
  then records it in the register's ``terms_sha256`` and ``last_verified``.
- **Evidence.** Each curated snapshot and change page is fetched again. A page whose
  bytes differ from the saved artifact is ``changed``; the saved bytes remain the
  evidence, and the difference is for a person to read. A page that robots.txt
  disallows is ``refused``. A persistent 403 or block page is ``refused`` too, and the
  client that met it sends nothing more (A §404).
- **Rebuild.** The cohort is rebuilt from the saved artifacts, which parses the dated
  evidence and reconciles the official changes against the corroborating snapshots,
  and its content hash is compared with the latest frozen manifest's.

SEC hosts go through the shared SEC client and every other host through the web
client, and each check keeps its retrieval metadata. Nothing here runs in the
default suite.
"""

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from earnings_ingestion.cohort.acquire import HTML, terms_digest
from earnings_ingestion.cohort.build import COHORT_STORE, CohortError, build
from earnings_ingestion.cohort.config import UNIVERSE_DIR, load_cohort_config
from earnings_ingestion.cohort.freeze import frozen_manifests
from earnings_ingestion.cohort.records import LiveCheck, LiveVerification
from earnings_ingestion.cohort.register import (
    MEMBERSHIP_REGISTER,
    SEC_REGISTER,
    load_registers,
)
from earnings_ingestion.cohort.web import RobotsRefusal, open_web_client
from earnings_ingestion.fetch.client import AccessStop, Fetched, UnexpectedResponse
from earnings_ingestion.fetch.store import write_new
from earnings_ingestion.sec.client import open_sec_client
from earnings_ingestion.sec.urls import is_sec_host

Fetch = Callable[[str, frozenset[str]], Fetched]
LIVE_RUNS = Path("data") / "runs" / "cohort" / "live"
ANY = frozenset({"text/html", "text/plain", "application/json", "application/pdf"})


def _targets(
    repo: Path, options: Mapping[str, Path]
) -> list[tuple[str, str, str, str | None]]:
    """(source_id, purpose, url, expected hash) for every live request, in order."""
    config = load_cohort_config(repo / options["config_dir"])
    registers = load_registers(repo, options["register"], options["sec_register"])
    evidence = [*config.evidence.snapshots, *config.evidence.changes]
    sources = {item.source_id for item in evidence}
    sources |= {check.source_id for check in config.evidence.checks}
    if config.universe.etf_proxy is not None:
        sources.add(config.universe.etf_proxy.source_id)
    targets = []
    for source_id in sorted(sources):
        entry = registers.entry(source_id)
        if entry.terms_url is not None:
            targets.append((source_id, "terms", entry.terms_url, entry.terms_sha256))
    for item in sorted(evidence, key=lambda item: item.evidence_id):
        targets.append((item.source_id, "evidence", item.url, item.artifact_sha256))
    return targets


def verify_live(
    repo: Path,
    *,
    fetch_web: Fetch,
    fetch_sec: Fetch,
    now: datetime,
    options: Mapping[str, Path] | None = None,
) -> LiveVerification:
    """Run every live check, then rebuild; ``fetch_*`` carry the access policy."""
    options = options or default_options()
    checks = []
    stopped: set[str] = set()
    for source_id, purpose, url, expected in _targets(repo, options):
        client = "sec" if is_sec_host(urlsplit(url).hostname or "") else "web"
        fetch = fetch_sec if client == "sec" else fetch_web
        if client in stopped:
            checks.append(
                LiveCheck(
                    source_id=source_id,
                    purpose=purpose,
                    url=url,
                    outcome="failed",
                    detail="not requested: an earlier refusal stopped this client",
                    retrieval=None,
                )
            )
            continue
        try:
            fetched = fetch(url, ANY if purpose == "terms" else HTML)
        except RobotsRefusal as exc:
            outcome, detail, retrieval = "refused", str(exc), None
        except AccessStop as exc:
            stopped.add(client)
            outcome, detail, retrieval = "refused", str(exc), None
        except (UnexpectedResponse, httpx.HTTPError) as exc:
            outcome, detail, retrieval = "failed", str(exc), None
        else:
            retrieval = fetched.retrieval
            found = (
                terms_digest(fetched.body, retrieval.media_type)
                if purpose == "terms"
                else retrieval.sha256
            )
            outcome = "unchanged" if found == expected else "changed"
            detail = f"{purpose} hash {found}; recorded {expected}"
        checks.append(
            LiveCheck(
                source_id=source_id,
                purpose=purpose,
                url=url,
                outcome=outcome,
                detail=detail,
                retrieval=retrieval,
            )
        )

    config = load_cohort_config(repo / options["config_dir"])
    manifests = frozen_manifests(
        repo / options["config_dir"] / "manifests", config.universe.universe_id
    )
    frozen = manifests[-1].definition.content_hash if manifests else None
    try:
        rebuilt = build(repo, **options)
    except CohortError as exc:
        problems, content, blocking = tuple(exc.problems), None, ()
    else:
        problems, content = (), rebuilt.content_hash
        blocking = tuple(f.finding_id for f in rebuilt.report.blocking)
    return LiveVerification(
        checked_at=now,
        checks=tuple(checks),
        build_problems=problems,
        rebuilt_content_hash=content,
        frozen_content_hash=frozen,
        blocking_finding_ids=blocking,
    )


def default_options() -> dict[str, Path]:
    return {
        "config_dir": UNIVERSE_DIR,
        "store_root": COHORT_STORE,
        "register": MEMBERSHIP_REGISTER,
        "sec_register": SEC_REGISTER,
    }


def run_live(
    repo: Path, *, environ: Mapping[str, str] | None = None
) -> tuple[LiveVerification, Path]:
    """Open both clients, verify, and save the result under data/runs/cohort/live/."""
    options = default_options()
    hosts = {urlsplit(url).hostname or "" for _, _, url, _ in _targets(repo, options)}
    web_hosts = sorted(host for host in hosts if host and not is_sec_host(host))
    with (
        open_web_client(repo, web_hosts, environ=environ) as web,
        open_sec_client(repo, environ=environ) as sec,
    ):
        result = verify_live(
            repo,
            fetch_web=web.fetch,
            fetch_sec=sec.fetch,
            now=datetime.now(UTC),
            options=options,
        )
    stamp = result.checked_at.strftime("%Y%m%dT%H%M%SZ")
    path = repo / LIVE_RUNS / f"{stamp}.json"
    write_new(path, result.model_dump_json(indent=1).encode("utf-8") + b"\n")
    return result, path
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_live.py -q`

Expected: `2 passed`.

- [ ] **Step 5: Add the opt-in live test**

Create `tests/integration/test_cohort_live.py`:

```python
"""The opt-in live verification of the real cohort (P-VL); run with ``-m live``.

It needs EDGAR_IDENTITY and SOURCE_IDENTITY, the curated files under
config/universe/djia/, and the saved artifacts under data/raw/cohort/, and it sends
live requests under both clients' access policies. It never runs by default.
"""

import os
from pathlib import Path

import pytest
from earnings_ingestion.cohort.live import run_live

pytestmark = pytest.mark.live
REPO = Path(__file__).resolve().parents[2]


def test_the_real_cohort_verifies_live() -> None:
    missing = [
        v for v in ("EDGAR_IDENTITY", "SOURCE_IDENTITY") if not os.environ.get(v)
    ]
    if missing:
        pytest.skip(f"set {' and '.join(missing)} outside Git to run this check")
    if not (REPO / "config" / "universe" / "djia" / "evidence.toml").exists():
        pytest.skip("the real cohort is not curated yet")
    result, path = run_live(REPO)
    assert path.is_file()
    assert result.build_problems == ()
    assert [c.url for c in result.checks if c.outcome == "failed"] == []
    assert result.blocking_finding_ids == ()
    assert result.rebuilt_content_hash == result.frozen_content_hash
```

It skips without both identities, or until Task 17 curates the real cohort. Never
run it with `-m live` before Task 18's gate.

Run: `uv run --locked --all-packages pytest tests/integration/test_cohort_live.py -m "not live and not browser" -q`

Expected: `1 deselected`.

- [ ] **Step 6: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py packages/earnings-ingestion/tests/test_cohort_live.py tests/integration/test_cohort_live.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `895 passed, 24 deselected`;
`All checks passed!` and `207 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py packages/earnings-ingestion/tests/test_cohort_live.py tests/integration/test_cohort_live.py
git commit -m "feat(ingestion): verify the frozen cohort live, opt-in (P-VL)"
```

---
### Task 16: The `earnings-pipeline cohort` commands

The application owns configuration and commands (P6-22). The package functions take
saved bytes and callables, and the CLI opens the clients, reads the identities, and
prints.

| Command | What it does | Network |
| --- | --- | --- |
| `cohort fetch SOURCE_ID URL...` | Saves pages of a registered source, each after its robots.txt | web client |
| `cohort register SOURCE_ID FILE --url URL [--saved-at T]` | Records a page a person saved | none |
| `cohort fetch-sec` | Saves every SEC record the build reads | SEC client |
| `cohort cite SOURCE_ID SHA256 --find TEXT [--line]`, or `--span START END`, or `--pointer P` | Prints the TOML to commit on stdout, and the cited text on stderr | none |
| `cohort build` | Builds and lists every finding as `BLOCKING`, `resolved`, or `noted`, with its digest. It exits 1 while anything blocks. | none |
| `cohort freeze` | Freezes a new version, or names the version that already holds the build | none |
| `cohort terms URL` | Prints a terms page's `terms_sha256` | web or SEC client |
| `cohort verify-live` | Runs P-VL, and names its record | both |

`--repo`, `--config-dir`, `--store`, `--register`, and `--sec-register` default to
the real cohort's paths. The tests point them at a copy of the synthetic cohort.

**Files:**

- Create: `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`.
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/cli.py` (replaced whole).
- Test (create): `apps/earnings-pipeline/tests/test_cohort_cli.py`.

**Interfaces:**

- Consumes: Tasks 12, 14, and 15's package functions, and Tasks 4 and 14's clients.
- Produces:
  - `earnings_pipeline.cohort_cli.cohort`, a `typer.Typer` group;
  - `Layout(repo, config_dir, store_root, register, sec_register)`;
  - `cli.app` gains the `cohort` group, beside `browser`.

- [ ] **Step 1: Write the failing tests**

Create `apps/earnings-pipeline/tests/test_cohort_cli.py`:

```python
"""``earnings-pipeline cohort`` on the synthetic cohort; the clients are replaced."""

import shutil
from contextlib import contextmanager
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, write_synthetic_cohort
from earnings_ingestion.fetch.client import Fetched
from earnings_ingestion.fetch.records import Retrieval
from earnings_pipeline import cli, cohort_cli
from typer.testing import CliRunner

RUNNER = CliRunner()


@pytest.fixture(scope="module")
def generated(tmp_path_factory) -> Path:
    repo = tmp_path_factory.mktemp("generated")
    write_synthetic_cohort(repo)
    return repo


@pytest.fixture
def repo(generated: Path, tmp_path: Path) -> Path:
    shutil.copytree(generated, tmp_path, dirs_exist_ok=True)
    return tmp_path


def run(repo: Path, *args: str):
    layout = [
        "cohort",
        "--repo",
        str(repo),
        "--config-dir",
        str(FIXTURE_DIR),
        "--store",
        str(FIXTURE_DIR / "raw"),
        "--register",
        str(FIXTURE_DIR / "membership-source-register.toml"),
        "--sec-register",
        str(FIXTURE_DIR / "source-register.toml"),
    ]
    return RUNNER.invoke(cli.app, [*layout, *args])


def test_build_reports_every_finding_and_no_blocking_one(repo) -> None:
    result = run(repo, "build")
    assert result.exit_code == 0, result.output
    assert "resolved  membership_conflict:corvid-common" in result.stdout
    assert "noted  gap:2026q3" in result.stdout
    assert "0 blocking findings" in result.stdout


def test_build_fails_while_a_finding_holds_the_freeze(repo) -> None:
    (repo / FIXTURE_DIR / "overrides.toml").unlink()
    result = run(repo, "build")
    assert result.exit_code == 1
    assert "BLOCKING  identity:eastfield-common  digest " in result.stdout


def test_freeze_names_the_version_that_holds_the_content(repo) -> None:
    result = run(repo, "freeze")
    assert result.exit_code == 0, result.output
    assert "unchanged: djia-synthetic v1" in result.stdout


def test_freeze_refuses_with_the_blocking_findings(repo) -> None:
    (repo / FIXTURE_DIR / "overrides.toml").unlink()
    result = run(repo, "freeze")
    assert result.exit_code == 1
    assert "BLOCKING  membership_conflict:corvid-common" in result.stderr


def test_cite_keeps_the_cited_text_off_stdout(repo) -> None:
    page = next(
        path
        for path in (repo / FIXTURE_DIR / "raw" / "synthetic-index").glob("*.html")
        if b"Corvid Systems (CRVD) will replace" in path.read_bytes()
    )
    result = run(
        repo, "cite", "synthetic-index", page.stem, "--find", "Corvid Systems (CRVD)"
    )
    assert result.exit_code == 0, result.output
    assert "span = [" in result.stdout
    assert f'cited_sha256 = "{sha256_hex(b"Corvid Systems (CRVD)")}"' in result.stdout
    assert "Corvid" not in result.stdout
    assert "Corvid Systems (CRVD)" in result.stderr


def test_cite_line_takes_the_whole_row(repo) -> None:
    page = next((repo / FIXTURE_DIR / "raw" / "synthetic-roster").glob("*.html"))
    result = run(repo, "cite", "synthetic-roster", page.stem, "--find", "ACM", "--line")
    assert result.exit_code == 0, result.output
    assert "span = [" in result.stdout
    assert "\\t" in result.stderr


def test_register_saves_a_hand_saved_page(repo, tmp_path_factory) -> None:
    saved = tmp_path_factory.mktemp("browser") / "notice.html"
    saved.write_bytes(b"<p>Saved by hand.</p>")
    result = run(
        repo,
        "register",
        "synthetic-index",
        str(saved),
        "--url",
        "https://index.example/notices/by-hand",
        "--saved-at",
        "2026-09-29T10:00:00",
    )
    assert result.exit_code == 0, result.output
    assert result.stdout.startswith(sha256_hex(b"<p>Saved by hand.</p>"))


def test_fetch_sec_goes_through_the_shared_client(repo, monkeypatch) -> None:
    requested = []

    class FakeSec:
        class throttle:
            count = 0

        def fetch(self, url, types):
            requested.append(url)
            FakeSec.throttle.count += 1
            raise cohort_cli.AccessStop(f"403 persisted for {url}")

    @contextmanager
    def fake_open(repo_path):
        yield FakeSec()

    monkeypatch.setattr(cohort_cli, "open_sec_client", fake_open)
    result = run(repo, "fetch-sec")
    assert result.exit_code == 1
    assert "Stopped: 403 persisted" in result.stderr
    assert requested == ["https://www.sec.gov/files/company_tickers.json"]


def test_fetch_saves_pages_through_the_web_client(repo, monkeypatch) -> None:
    body = b"<p>A notice.</p>"

    class FakeWeb:
        def fetch(self, url, types):
            return Fetched(
                body=body,
                retrieval=Retrieval.model_validate(
                    {
                        "request_url": url,
                        "final_url": url,
                        "retrieved_at": "2026-09-29T10:00:00Z",
                        "retrieval_method": "http",
                        "http_status": 200,
                        "media_type": "text/html",
                        "content_type": "text/html",
                        "byte_count": len(body),
                        "sha256": sha256_hex(body),
                    },
                    strict=False,
                ),
            )

    @contextmanager
    def fake_open(repo_path, hosts):
        assert hosts == ["index.example"]
        yield FakeWeb()

    monkeypatch.setattr(cohort_cli, "open_web_client", fake_open)
    result = run(repo, "fetch", "synthetic-index", "https://index.example/notices/new")
    assert result.exit_code == 0, result.output
    assert sha256_hex(body) in result.stdout
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_cohort_cli.py -q`

Expected: FAIL. Collection stops with `cannot import name 'cohort_cli'`, and pytest
reports `1 error`.

- [ ] **Step 3: Write the implementation**

Create `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`:

```python
"""``earnings-pipeline cohort``: acquire, cite, build, and freeze the DJIA cohort.

    earnings-pipeline cohort fetch SOURCE_ID URL...        # through robots.txt
    earnings-pipeline cohort register SOURCE_ID FILE --url URL
    earnings-pipeline cohort fetch-sec                      # the shared SEC client
    earnings-pipeline cohort cite SOURCE_ID SHA256 --find TEXT [--line]
    earnings-pipeline cohort build
    earnings-pipeline cohort freeze
    earnings-pipeline cohort terms URL
    earnings-pipeline cohort verify-live

Only ``fetch``, ``fetch-sec``, ``terms``, and ``verify-live`` use the network, each
through its client's access policy; ``build`` and ``freeze`` read committed files and
saved artifacts alone. ``cite`` prints the TOML to commit on stdout and the cited text
on stderr only, so no source wording is pasted into a committed file by accident.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, NoReturn
from urllib.parse import urlsplit

import typer
from earnings_ingestion.cohort.acquire import (
    cite,
    fetch_page,
    fetch_sec,
    register_saved,
    terms_digest,
)
from earnings_ingestion.cohort.build import (
    COHORT_STORE,
    CohortBuild,
    CohortError,
    build,
)
from earnings_ingestion.cohort.config import UNIVERSE_DIR, load_cohort_config
from earnings_ingestion.cohort.freeze import FreezeRefused, freeze
from earnings_ingestion.cohort.live import ANY, run_live
from earnings_ingestion.cohort.records import LocatorKind
from earnings_ingestion.cohort.register import (
    MEMBERSHIP_REGISTER,
    SEC_REGISTER,
    Registers,
    load_registers,
)
from earnings_ingestion.cohort.web import open_web_client
from earnings_ingestion.fetch.client import AccessStop, UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.client import open_sec_client
from earnings_ingestion.sec.urls import is_sec_host

cohort = typer.Typer(no_args_is_help=True, help="Stage 4's point-in-time DJIA cohort.")


@dataclass(frozen=True)
class Layout:
    repo: Path
    config_dir: Path
    store_root: Path
    register: Path
    sec_register: Path

    def options(self) -> dict[str, Path]:
        return {
            "config_dir": self.config_dir,
            "store_root": self.store_root,
            "register": self.register,
            "sec_register": self.sec_register,
        }

    def store(self) -> ArtifactStore:
        return ArtifactStore(self.repo / self.store_root, self.repo)

    def registers(self) -> Registers:
        return load_registers(self.repo, self.register, self.sec_register)


@cohort.callback()
def main(
    context: typer.Context,
    repo: Annotated[Path, typer.Option(help="The repository root.")] = Path(),
    config_dir: Annotated[Path, typer.Option(help="The curated files.")] = UNIVERSE_DIR,
    store: Annotated[Path, typer.Option(help="The artifact store.")] = COHORT_STORE,
    register: Annotated[
        Path, typer.Option(help="The membership source register.")
    ] = MEMBERSHIP_REGISTER,
    sec_register: Annotated[
        Path, typer.Option(help="The register holding sec-edgar.")
    ] = SEC_REGISTER,
) -> None:
    """Paths are relative to --repo; the defaults are the real cohort's."""
    context.obj = Layout(repo.resolve(), config_dir, store, register, sec_register)


def _fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(1)


@cohort.command("fetch")
def fetch_command(
    context: typer.Context,
    source_id: str,
    urls: Annotated[list[str], typer.Argument(help="Pages of that source.")],
) -> None:
    """Save pages of a registered source, each after its robots.txt allows it."""
    layout: Layout = context.obj
    registers = layout.registers()
    hosts = sorted({urlsplit(url).hostname or "" for url in urls})
    try:
        with open_web_client(layout.repo, hosts) as web:
            for url in urls:
                ref = fetch_page(web.fetch, layout.store(), registers, source_id, url)
                typer.echo(f"{ref.content_sha256}  {ref.storage_ref}  {url}")
    except (AccessStop, UnexpectedResponse, ValueError) as error:
        _fail(f"Stopped: {error}")


@cohort.command("register")
def register_command(
    context: typer.Context,
    source_id: str,
    path: Path,
    url: Annotated[str, typer.Option(help="Where the page was saved from.")],
    media_type: Annotated[str, typer.Option()] = "text/html",
    saved_at: Annotated[
        datetime | None,
        typer.Option(help="When it was saved, in UTC; default the file's time."),
    ] = None,
) -> None:
    """Save a page a person saved in a browser, recording that nothing was fetched."""
    layout: Layout = context.obj
    when = saved_at or datetime.fromtimestamp(path.stat().st_mtime, UTC)
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    try:
        ref = register_saved(
            layout.store(),
            layout.registers(),
            source_id,
            path.read_bytes(),
            url=url,
            media_type=media_type,
            saved_at=when.astimezone(UTC),
        )
    except ValueError as error:
        _fail(f"Refused: {error}")
    typer.echo(f"{ref.content_sha256}  {ref.storage_ref}  {url}")


@cohort.command("fetch-sec")
def fetch_sec_command(context: typer.Context) -> None:
    """Save the SEC records the build reads, through the shared SEC client."""
    layout: Layout = context.obj
    config = load_cohort_config(layout.repo / layout.config_dir)
    try:
        with open_sec_client(layout.repo) as sec:
            result = fetch_sec(sec.fetch, layout.store(), layout.registers(), config)
            requests = sec.throttle.count
    except (AccessStop, UnexpectedResponse, ValueError) as error:
        _fail(f"Stopped: {error}")
    typer.echo(f"fetched {len(result.fetched)}, already saved {len(result.kept)}")
    typer.echo(f"requests sent: {requests}")


@cohort.command("cite")
def cite_command(
    context: typer.Context,
    source_id: str,
    sha256: str,
    find: Annotated[str | None, typer.Option(help="Text to find.")] = None,
    occurrence: Annotated[int, typer.Option(help="Which occurrence, from 1.")] = 1,
    span: Annotated[
        tuple[int, int] | None, typer.Option(help="START END offsets.")
    ] = None,
    pointer: Annotated[str | None, typer.Option(help="A JSON pointer.")] = None,
    line: Annotated[
        bool, typer.Option(help="Cite the whole line holding --find: a table row.")
    ] = False,
) -> None:
    """Print the locator to commit (stdout) and the cited text (stderr only)."""
    layout: Layout = context.obj
    try:
        locator, text = cite(
            layout.store(),
            layout.registers(),
            source_id,
            sha256,
            find=find,
            occurrence=occurrence,
            span=span,
            pointer=pointer,
            line=line,
        )
    except (FileNotFoundError, ValueError) as error:
        _fail(f"Refused: {error}")
    if locator.kind is LocatorKind.TEXT_SPAN:
        typer.echo(f'canonical_sha256 = "{locator.canonical_sha256}"')
        typer.echo(f"span = [{locator.start}, {locator.end}]")
    else:
        typer.echo(f'pointer = "{locator.pointer}"')
    typer.echo(f'cited_sha256 = "{locator.cited_sha256}"')
    typer.echo(f"cited text, not for committing: {text!r}", err=True)


def _build(layout: Layout) -> CohortBuild:
    try:
        return build(layout.repo, **layout.options())
    except CohortError as error:
        for problem in error.problems:
            typer.echo(f"problem: {problem}", err=True)
        raise typer.Exit(1) from error


@cohort.command("build")
def build_command(context: typer.Context) -> None:
    """Build from committed files and saved artifacts; print what holds the freeze."""
    built = _build(context.obj)
    for finding in built.report.findings:
        state = (
            "BLOCKING"
            if finding.holds_freeze
            else "resolved"
            if finding.resolved_by
            else "noted"
        )
        typer.echo(f"{state}  {finding.finding_id}  digest {finding.digest}")
        typer.echo(f"    {finding.detail}")
    for override_id in built.stale_acknowledgements:
        typer.echo(f"STALE  {override_id} acknowledges a finding that has changed")
    typer.echo(
        f"{len(built.intervals)} intervals, {len(built.candidate_issuer_ids)} candidate"
        f" issuers, {len(built.report.blocking)} blocking findings,"
        f" content {built.content_hash}"
    )
    if built.report.blocking or built.stale_acknowledgements:
        raise typer.Exit(1)


@cohort.command("freeze")
def freeze_command(context: typer.Context) -> None:
    """Freeze the build as a new version, or name the version that already holds it."""
    layout: Layout = context.obj
    built = _build(layout)
    try:
        frozen = freeze(
            built,
            layout.repo / layout.config_dir / "manifests",
            now=datetime.now(UTC),
        )
    except FreezeRefused as error:
        for finding in error.blocking:
            typer.echo(f"BLOCKING  {finding.finding_id}: {finding.detail}", err=True)
        for override_id in error.stale:
            typer.echo(f"STALE  {override_id}", err=True)
        raise typer.Exit(1) from error
    verb = "froze" if frozen.created else "unchanged:"
    definition = frozen.manifest.definition
    typer.echo(f"{verb} {definition.universe_id} v{definition.universe_version}")
    typer.echo(f"{frozen.path.relative_to(layout.repo)}  {definition.content_hash}")


@cohort.command("terms")
def terms_command(context: typer.Context, url: str) -> None:
    """Print the hash a register records for a terms page."""
    layout: Layout = context.obj
    host = urlsplit(url).hostname or ""
    try:
        if is_sec_host(host):
            with open_sec_client(layout.repo) as sec:
                fetched = sec.fetch(url, ANY)
        else:
            with open_web_client(layout.repo, [host]) as web:
                fetched = web.fetch(url, ANY)
    except (AccessStop, UnexpectedResponse, ValueError) as error:
        _fail(f"Stopped: {error}")
    digest = terms_digest(fetched.body, fetched.retrieval.media_type)
    typer.echo(f'terms_sha256 = "{digest}"')


@cohort.command("verify-live")
def verify_live_command(context: typer.Context) -> None:
    """The opt-in live verification (P-VL); saves its record under data/runs/."""
    layout: Layout = context.obj
    try:
        result, path = run_live(layout.repo)
    except (AccessStop, ValueError) as error:
        _fail(f"Stopped: {error}")
    for check in result.checks:
        typer.echo(
            f"{check.outcome:9}  {check.purpose:8}  {check.source_id}  {check.url}"
        )
    typer.echo(
        f"rebuilt {result.rebuilt_content_hash}; frozen {result.frozen_content_hash}"
    )
    typer.echo(f"record: {path.relative_to(layout.repo)}")
```

Replace `apps/earnings-pipeline/src/earnings_pipeline/cli.py` with:

```python
"""The ``earnings-pipeline`` command line.

    uv run --locked --all-packages earnings-pipeline browser setup
    uv run --locked --all-packages earnings-pipeline cohort --help

``browser setup`` is the only command that downloads the pinned Chrome for Testing and
chromedriver (B8). It checks each archive against the committed manifest and installs
into a cache outside the repository; a capture never downloads anything. ``cohort``
holds Stage 4's commands (``earnings_pipeline.cohort_cli``).
"""

from pathlib import Path
from typing import Annotated

import typer
from earnings_ingestion.browser.install import (
    default_cache,
    download,
    install,
    load_pin,
)

from earnings_pipeline.cohort_cli import cohort

app = typer.Typer(no_args_is_help=True, help="The earnings pipeline.")
browser = typer.Typer(
    no_args_is_help=True, help="The pinned browser for Stage 3's diagnostic path."
)
app.add_typer(browser, name="browser")
app.add_typer(cohort, name="cohort")


@browser.command()
def setup(
    cache: Annotated[
        Path | None,
        typer.Option(help="Install here instead of the default cache directory."),
    ] = None,
) -> None:
    """Download, check, and install the pinned Chrome for Testing and chromedriver."""
    pin = load_pin()
    if pin is None:
        typer.echo("No Chrome for Testing build is pinned for this platform.", err=True)
        raise typer.Exit(1)
    try:
        binaries = install(pin, cache or default_cache(), download)
    except ValueError as error:
        typer.echo(f"Refused: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(f"Chrome for Testing {pin.version} ({pin.platform})")
    typer.echo(f"browser: {binaries.browser}")
    typer.echo(f"driver: {binaries.driver}")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_cohort_cli.py -q`

Expected: `9 passed`.

Run: `uv run --locked --all-packages earnings-pipeline cohort --help`

Expected: the help lists `fetch`, `register`, `fetch-sec`, `cite`, `build`,
`freeze`, `terms`, and `verify-live`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan6-escapes.py apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/tests/test_cohort_cli.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `904 passed, 24 deselected`; `280 passed`;
`All checks passed!` and `209 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/tests/test_cohort_cli.py
git commit -m "feat(pipeline): add the earnings-pipeline cohort commands"
```

---
### Task 16b: PDF citations (`pdftext-1`)

This task implements `specs/pdf-citation-text.md`, the amendment of 2026-09-26
(P6-24). Every S&P DJI notice that Task 17 cites is a PDF, and `walker-1` reads HTML
only (P6-9). So a second citation-text policy, `pdftext-1`, joins `walker-1`, and the
media type chooses between them.

- **`cohort/pdftext.py`** holds the policy: pypdf 6.19.0's plain text, normalized to
  NFC, with whitespace collapsed, blank lines dropped, and lines joined by `\n`.
- **`ArtifactText`** sends HTML to `walker-1` and a PDF to `pdftext-1`. Its new
  `version` property names the policy that each span records, and `verify` refuses a
  span made under another. `build` records the artifact's policy, not the `walker-1`
  constant.
- **Acquisition.**
  - The store names a PDF `<sha256>.pdf`.
  - `fetch_page` and the live refetch accept a PDF.
  - `check_media_type` refuses bytes that contradict their declared type.
    `cohort register` uses it, and so does `cohort terms --saved`, which hashes a
    terms page saved by hand (PT-9).
- **The dependency.** `pypdf==6.19.0`, the plan's one new dependency, arrives at its
  own gate (Step 3).
- **Tests** build invented PDFs at test time. No binary enters Git, and the committed
  synthetic cohort does not change.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/cohort/pdftext.py`.
- Modify: `packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py`
  (replaced whole, block 2 of 2).
- Modify, by exact replacement:
  - `cohort/build.py`, `cohort/acquire.py`, `cohort/live.py`, and `fetch/store.py`,
    under `packages/earnings-ingestion/src/earnings_ingestion/`;
  - `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`;
  - `docs/data-dictionary.md`.
- Modify, by `uv add`: `packages/earnings-ingestion/pyproject.toml` and `uv.lock`.
- Test (create): `packages/earnings-ingestion/tests/test_cohort_pdftext.py`.
- Test (replaced whole), under `packages/earnings-ingestion/tests/`: `conftest.py`
  (block 2 of 2), `test_cohort_acquire.py` (block 2 of 2), and
  `test_import_boundaries.py` (block 4 of 4).
- Test (appended, block 2 of 2 each):
  - under `packages/earnings-ingestion/tests/`: `test_cohort_locators.py`,
    `test_cohort_build.py`, `test_fetch_store.py`, and `test_cohort_live.py`;
  - `apps/earnings-pipeline/tests/test_cohort_cli.py`.

**Interfaces:**

- Consumes:
  - Task 8's `ArtifactText` and `LocatorError`;
  - Task 12's `build`, the synthetic cohort, and the `cohort_repo` fixture;
  - Task 14's `fetch_page`, `register_saved`, `cite`, and `terms_digest`;
  - Task 15's `verify_live`;
  - Task 16's `cohort register` and `cohort terms`.
- Produces:
  - `cohort/pdftext.py`: `PDFTEXT_VERSION = "pdftext-1"`,
    `pdf_text(body: bytes) -> str`, and `PdfTextError(ValueError)`;
  - `ArtifactText.version -> str`: `"walker-1"` for HTML, `"pdftext-1"` for a PDF,
    and a `LocatorError` for any other type;
  - `cohort/acquire.py`: `PDF = frozenset({"application/pdf"})`, and
    `check_media_type(body: bytes, media_type: str) -> None`, which raises
    `ValueError`;
  - `fetch/store.py`: `EXTENSIONS["application/pdf"] == ".pdf"`;
  - `earnings-pipeline cohort terms URL --saved FILE [--media-type TYPE]`;
  - two test fixtures:
    - `make_pdf`, a factory `make_pdf(*pages) -> bytes`, each page a list of
      `(x, y, text)` runs;
    - `pdf_cohort`, the synthetic cohort with its notice `index-2024-11-01`
      replaced by an invented PDF.

  Task 17 registers and cites the real notices with these.

- [ ] **Step 1: Write the failing tests**

The conftest gains `make_pdf`, which builds a small PDF from text runs as ASCII
bytes with a computed cross-reference table, and `pdf_cohort`. That fixture
registers an invented PDF notice, and cites its rows and date through `pdftext-1`,
as Task 17 does for a real notice.

Replace `packages/earnings-ingestion/tests/conftest.py` with:

```python
"""Shared test data. Plan 5: a small completed capture, its layout payload, and
builders for synthetic layout metadata. Plan 6: the synthetic cohort, and for
pdftext-1 a PDF builder and the cohort with a PDF notice (Task 16b)."""

import copy
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.browser.metadata import METADATA_VERSION, parse_metadata
from earnings_ingestion.browser.policy import ISOLATED_1
from earnings_ingestion.browser.records import (
    CaptureStatus,
    RenderedCapture,
    layout_hash,
)
from earnings_ingestion.browser.renderer import (
    CaptureEnvironment,
    cache_key,
    capture_id,
)
from earnings_ingestion.cohort.acquire import cite, register_saved
from earnings_ingestion.cohort.register import load_registers
from earnings_ingestion.cohort.synthetic import (
    FIXTURE_DIR,
    build_options,
    write_synthetic_cohort,
)
from earnings_ingestion.fetch.store import ArtifactStore

ENVIRONMENT = CaptureEnvironment(
    browser_engine="Chrome for Testing",
    browser_version="154.0.8037.57",
    driver_version="154.0.8037.57",
    selenium_version="4.49.0",
    os_name="Darwin",
    os_version="26.6.2",
    architecture="arm64",
)
PAYLOAD = {
    "blocks": [
        {
            "tag": "p",
            "display": "block",
            "heading_level": None,
            "list_item": False,
            "list_depth": 0,
            "table": None,
            "row": None,
            "cell": None,
            "x": 8,
            "y": 16,
            "width": 1264,
            "height": 18,
            "runs": [
                {
                    "text": "Revenue rose.",
                    "br": False,
                    "visible": True,
                    "bold": False,
                    "underline": False,
                    "superscript": False,
                    "symbol_font": False,
                    "font_size": 16,
                }
            ],
        }
    ],
    "tables": [],
}


def build_capture(**changes: object) -> RenderedCapture:
    layout = changes.pop("layout", parse_metadata(PAYLOAD))
    text = changes.pop("rendered_text", "Revenue rose.")
    raw = b"<p>Revenue rose.</p>"
    key = cache_key(sha256_hex(raw), ISOLATED_1, ENVIRONMENT)
    fields = {
        "capture_id": capture_id("release", ISOLATED_1, key),
        "cache_key": key,
        "source_document_id": "release",
        "raw_sha256": sha256_hex(raw),
        "capture_policy": "isolated",
        "capture_policy_version": "1",
        "metadata_version": METADATA_VERSION,
        "browser_engine": "Chrome for Testing",
        "browser_version": "154.0.8037.57",
        "driver_version": "154.0.8037.57",
        "selenium_version": "4.49.0",
        "os_name": "Darwin",
        "os_version": "26.6.2",
        "architecture": "arm64",
        "viewport_width": 1280,
        "viewport_height": 1024,
        "device_scale_factor": 1,
        "locale": "en-US",
        "timezone": "UTC",
        "font_set": "Darwin 26.6.2 system fonts",
        "document_charset": "UTF-8",
        "script_policy": "disabled",
        "network_policy": "blocked",
        "image_policy": "blocked",
        "missing_resource_policy": "recorded",
        "rendered_text": text,
        "rendered_text_sha256": sha256_hex(text.encode("utf-8")),
        "layout": layout,
        "layout_sha256": layout_hash(layout),
        "screenshots": (),
        "blocked_requests": (),
        "captured_at": datetime(2026, 9, 26, 12, 0, tzinfo=UTC),
        "duration_seconds": 0.8,
        "status": CaptureStatus.COMPLETED,
        "reason": None,
        "detail": "",
    }
    fields.update(changes)
    return RenderedCapture(**fields)


@pytest.fixture
def make_capture() -> Callable[..., RenderedCapture]:
    """A factory: a completed capture of one paragraph, with any field replaced."""
    return build_capture


@pytest.fixture
def payload() -> dict:
    """The layout-metadata script's result for that paragraph, safe to change."""
    return copy.deepcopy(PAYLOAD)


class LayoutParts:
    """Builders for the layout-metadata script's output: runs, blocks, and tables."""

    @staticmethod
    def run(text: str, **style: object) -> dict:
        base = {
            "text": text,
            "br": False,
            "visible": True,
            "bold": False,
            "underline": False,
            "superscript": False,
            "symbol_font": False,
            "font_size": 16,
        }
        return {**base, **style}

    @staticmethod
    def br() -> dict:
        return LayoutParts.run("\n", br=True)

    @staticmethod
    def block(
        *runs: dict,
        tag: str = "p",
        cell: tuple[int, int, int] | None = None,
        **context: object,
    ) -> dict:
        base = {
            "tag": tag,
            "display": "block",
            "heading_level": None,
            "list_item": False,
            "list_depth": 0,
            "table": None if cell is None else cell[0],
            "row": None if cell is None else cell[1],
            "cell": None if cell is None else cell[2],
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 10,
            "runs": list(runs),
        }
        return {**base, **context}

    @staticmethod
    def table(
        *rows: list[int],
        parent: tuple[int, int, int] | None = None,
        head: int = 0,
        th: bool = False,
    ) -> dict:
        """Rows as colspans, one per rendered cell; the first ``head`` rows in thead."""
        return {
            "parent_table": None if parent is None else parent[0],
            "parent_row": None if parent is None else parent[1],
            "parent_cell": None if parent is None else parent[2],
            "rows": [
                {
                    "head": index < head,
                    "cells": [
                        {"header": th, "colspan": span, "rowspan": 1} for span in row
                    ],
                }
                for index, row in enumerate(rows)
            ],
        }

    @staticmethod
    def cells(rows: list[list[str]], table_index: int = 0) -> list[dict]:
        """One ``td`` block per non-empty cell text, in row-major order."""
        return [
            LayoutParts.block(LayoutParts.run(text), tag="td", cell=(table_index, r, c))
            for r, row in enumerate(rows)
            for c, text in enumerate(row)
            if text
        ]


@pytest.fixture
def parts() -> type[LayoutParts]:
    return LayoutParts


@pytest.fixture(scope="session")
def synthetic_cohort(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A repository holding the synthetic cohort, generated once; never change it."""
    repo = tmp_path_factory.mktemp("synthetic-cohort")
    write_synthetic_cohort(repo)
    return repo


@pytest.fixture
def cohort_repo(synthetic_cohort: Path, tmp_path: Path) -> Path:
    """A private copy of the synthetic cohort's repository, safe to change."""
    shutil.copytree(synthetic_cohort, tmp_path, dirs_exist_ok=True)
    return tmp_path


def _pdf_string(text: str) -> str:
    """``text`` as an ASCII PDF literal string: a WinAnsi character as an octal
    escape, and U+0301 as code 0x81, which the font's /Differences names /acutecomb."""
    out = []
    for char in text:
        if char in "\\()":
            out.append("\\" + char)
        elif " " <= char <= "~":
            out.append(char)
        else:
            code = 0x81 if char == chr(0x301) else char.encode("cp1252")[0]
            out.append(f"\\{code:03o}")
    return "".join(out)


def build_pdf(*pages: list[tuple[int, int, str]]) -> bytes:
    """A PDF with one page per argument, each a list of (x, y, text) runs in 12-point
    Helvetica: ASCII bytes, no compressed stream, and a computed cross-reference
    table. Runs on one baseline extract as one line, joined by single spaces."""
    count = len(pages)
    kids = " ".join(f"{3 + 2 * index} 0 R" for index in range(count))
    font = 3 + 2 * count
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {count} >>",
    ]
    for index, runs in enumerate(pages):
        content = "\n".join(
            f"BT /F1 12 Tf {x} {y} Td ({_pdf_string(text)}) Tj ET"
            for x, y, text in runs
        )
        objects.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources"
            f" << /Font << /F1 {font} 0 R >> >> /Contents {4 + 2 * index} 0 R >>"
        )
        objects.append(f"<< /Length {len(content)} >>\nstream\n{content}\nendstream")
    objects.append(
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding << /Type"
        " /Encoding /BaseEncoding /WinAnsiEncoding /Differences [129 /acutecomb] >> >>"
    )
    pdf = "%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{number} 0 obj\n{body}\nendobj\n"
    xref = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    pdf += "".join(f"{offset:010d} 00000 n \n" for offset in offsets)
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
    pdf += f"startxref\n{xref}\n%%EOF\n"
    return pdf.encode("ascii")


@pytest.fixture
def make_pdf() -> Callable[..., bytes]:
    """A factory: a small PDF built from text runs, one argument per page."""
    return build_pdf


PDF_NOTICE = [
    (72, 720, "Synthetic Index Services announces a change"),
    (72, 690, "Corvid Systems will replace Borealis Air in the Synthetic Industrial"),
    (72, 675, "Average prior to"),
    (72, 660, "the open of trading on Friday, November 8, 2024."),
    (72, 630, "Company"),
    (250, 630, "Ticker"),
    (330, 630, "Action"),
    (72, 612, "Corvid Systems"),
    (250, 612, "CRVD"),
    (330, 612, "Added"),
    (72, 594, "Borealis Air"),
    (250, 594, "BORA"),
    (330, 594, "Removed"),
]
PDF_NOTICE_URL = "https://index.example/notices/index-2024-11-01"


@pytest.fixture
def pdf_cohort(cohort_repo: Path) -> Path:
    """The private copy, its official notice index-2024-11-01 replaced by an invented
    PDF that states the same facts. The PDF is registered as Task 17 registers a
    saved notice, and its rows and effective date are cited through pdftext-1."""
    store = ArtifactStore(cohort_repo / FIXTURE_DIR / "raw", cohort_repo)
    options = build_options()
    registers = load_registers(
        cohort_repo, options["register"], options["sec_register"]
    )
    ref = register_saved(
        store,
        registers,
        "synthetic-index",
        build_pdf(PDF_NOTICE),
        url=PDF_NOTICE_URL,
        media_type="application/pdf",
        saved_at=datetime(2026, 9, 28, 12, 0, tzinfo=UTC),
    )

    def locate(needle: str, line: bool = False):
        sha = ref.content_sha256
        return cite(store, registers, "synthetic-index", sha, find=needle, line=line)[0]

    when = locate("prior to\nthe open of trading on Friday, November 8, 2024")
    added = locate("Corvid Systems CRVD", line=True)
    removed = locate("Borealis Air BORA", line=True)
    block = (
        '[[changes]]\nevidence_id = "index-2024-11-01"\nsource_id = "synthetic-index"\n'
        f'url = "{PDF_NOTICE_URL}"\nartifact_sha256 = "{ref.content_sha256}"\n'
        f'canonical_sha256 = "{when.canonical_sha256}"\nannounced_on = 2024-11-01\n'
        'published_on = 2024-11-01\npublished_at = "2024-11-01T21:15:00Z"\n'
        'effective_on = 2024-11-08\ntiming = "before_open"\n'
        f"date_span = [{when.start}, {when.end}]\n"
        f'date_cited_sha256 = "{when.cited_sha256}"\n\n'
        '[[changes.entries]]\naction = "added"\nsecurity_id = "corvid-common"\n'
        'name = "Corvid Systems"\nticker = "CRVD"\n'
        f"span = [{added.start}, {added.end}]\n"
        f'cited_sha256 = "{added.cited_sha256}"\n\n'
        '[[changes.entries]]\naction = "removed"\nsecurity_id = "borealis-common"\n'
        'name = "Borealis Air"\nticker = "BORA"\n'
        f"span = [{removed.start}, {removed.end}]\n"
        f'cited_sha256 = "{removed.cited_sha256}"\n\n'
    )
    path = cohort_repo / FIXTURE_DIR / "evidence.toml"
    evidence = path.read_text(encoding="utf-8")
    start = evidence.index('[[changes]]\nevidence_id = "index-2024-11-01"\n')
    end = evidence.index("[[changes]]\n", start + 1)
    path.write_text(evidence[:start] + block + evidence[end:], encoding="utf-8")
    return cohort_repo
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py packages/earnings-ingestion/tests/conftest.py 2`.

The policy's own tests pin an invented two-page notice's text and its golden hash,
which are the drift alarm.

Create `packages/earnings-ingestion/tests/test_cohort_pdftext.py`:

```python
"""pdftext-1, the citation text of a saved PDF (plan 6, P6-24).

The invented notice's text and its golden hash are the drift alarm, as walker-1's
golden test is. If pypdf's output changes, the remedy is pdftext-2 and new citations,
never an edited hash.
"""

import io
import logging

import pytest
from earnings_core import hash_canonical_text
from earnings_ingestion.cohort.pdftext import PDFTEXT_VERSION, PdfTextError, pdf_text
from pypdf import PdfReader, PdfWriter

TM = chr(0x2122)  # the trade mark sign: NFC keeps it, NFKC would spell it out
NOTICE = [
    [
        (72, 740, "Synthetic Index Services"),
        (72, 722, "Corvid Systems Set to Join the Synthetic Industrial Average"),
        (72, 692, "NEW YORK, Nov. 1, 2024: Corvid Systems will replace Borealis Air"),
        (72, 677, f"in the Synthetic Industrial Average{TM} prior to the open of"),
        (72, 662, "trading on Friday, November 8, 2024."),
        (72, 632, "Effective Date"),
        (170, 632, "Action"),
        (240, 632, "Company"),
        (400, 632, "Ticker"),
        (72, 614, "Nov 8, 2024"),
        (170, 614, "Adding"),
        (240, 614, "Corvid Systems"),
        (400, 614, "CRVD"),
        (170, 596, "Dropping"),
        (240, 596, "Borealis Air"),
        (400, 596, "BORA"),
        (72, 566, "   "),
        (72, 548, "  For more information,   contact the index team. "),
    ],
    [
        (72, 740, "About Synthetic Index Services"),
        (72, 722, "This notice is synthetic test data, invented for this repository."),
    ],
]
TEXT = "\n".join(
    [
        "Synthetic Index Services",
        "Corvid Systems Set to Join the Synthetic Industrial Average",
        "NEW YORK, Nov. 1, 2024: Corvid Systems will replace Borealis Air",
        f"in the Synthetic Industrial Average{TM} prior to the open of",
        "trading on Friday, November 8, 2024.",
        "Effective Date Action Company Ticker",
        "Nov 8, 2024 Adding Corvid Systems CRVD",
        "Dropping Borealis Air BORA",
        "For more information, contact the index team.",
        "About Synthetic Index Services",
        "This notice is synthetic test data, invented for this repository.",
    ]
)
GOLDEN = "4fe6134c599aec03e11250e8ff4e6f3010876d7cf6b061ac3248a4a152f3fd08"


def test_the_notice_extracts_to_its_golden_text(make_pdf) -> None:
    """Runs on one baseline join with single spaces, whitespace collapses, blank
    lines drop, pages join with a newline, and NFC keeps the trade mark sign."""
    text = pdf_text(make_pdf(*NOTICE))
    assert (PDFTEXT_VERSION, text) == ("pdftext-1", TEXT)
    assert hash_canonical_text(text) == GOLDEN


def test_a_rerun_is_identical(make_pdf) -> None:
    body = make_pdf(*NOTICE)
    assert pdf_text(body) == pdf_text(body)


def test_decomposed_text_is_normalized_to_nfc(make_pdf) -> None:
    body = make_pdf([(72, 720, "Cafe" + chr(0x301) + " au lait")])
    assert chr(0x301) in PdfReader(io.BytesIO(body)).pages[0].extract_text()
    assert pdf_text(body) == "Caf" + chr(0xE9) + " au lait"


@pytest.mark.parametrize("damage", ["garbage", "truncated", "empty"])
def test_bytes_pypdf_cannot_read_are_refused(make_pdf, damage) -> None:
    whole = make_pdf(*NOTICE)
    body = {
        "garbage": b"not a pdf at all",
        "truncated": whole[: len(whole) // 2],
        "empty": b"",
    }[damage]
    with pytest.raises(PdfTextError, match="pdftext-1 cannot read it"):
        pdf_text(body)


@pytest.mark.parametrize("user_password", ["", "secret"])
def test_an_encrypted_pdf_is_refused_even_one_that_opens(
    make_pdf, user_password
) -> None:
    """RC4, which pypdf writes with no extra dependency; an empty user password
    opens the file, and it is still refused."""
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(make_pdf(*NOTICE))))
    writer.encrypt(
        user_password=user_password, owner_password="owner", algorithm="RC4-128"
    )
    out = io.BytesIO()
    writer.write(out)
    with pytest.raises(PdfTextError, match="pdftext-1 refuses an encrypted PDF"):
        pdf_text(out.getvalue())


def test_a_pdf_without_a_text_layer_is_refused(make_pdf) -> None:
    with pytest.raises(PdfTextError, match="pdftext-1 found no text layer"):
        pdf_text(make_pdf([]))


def test_recovery_warnings_are_silenced_and_the_logger_restored(
    make_pdf, caplog
) -> None:
    whole = make_pdf(*NOTICE)
    # Object 1 starts at byte 9; point its entry at byte 17, inside the object.
    damaged = whole.replace(b"0000000009 00000 n \n", b"0000000017 00000 n \n")
    caplog.set_level(logging.DEBUG, logger="pypdf")
    PdfReader(io.BytesIO(damaged))
    assert "Ignoring wrong pointing object 1 0" in caplog.text
    caplog.clear()
    assert pdf_text(damaged) == TEXT
    assert caplog.records == []
    assert logging.getLogger("pypdf").level == logging.DEBUG
    with pytest.raises(PdfTextError):
        pdf_text(b"not a pdf at all")
    assert logging.getLogger("pypdf").level == logging.DEBUG
```

Append to `packages/earnings-ingestion/tests/test_cohort_locators.py`:

```python


PDF_ROWS = [
    (72, 720, "Synthetic roster"),
    (72, 700, "Acme Industrial"),
    (250, 700, "ACME"),
    (72, 682, "Borealis Air  "),
    (250, 682, "BORA"),
]


def test_a_pdf_is_cited_through_pdftext_1(make_pdf) -> None:
    page = ArtifactText(make_pdf(PDF_ROWS), "application/pdf")
    text, text_hash = page.canonical
    assert page.version == "pdftext-1"
    assert text == "Synthetic roster\nAcme Industrial ACME\nBorealis Air BORA"
    assert text_hash == sha256_hex(text.encode("utf-8"))
    for locator in (page.find("ACME"), page.line("BORA"), page.span(0, 9)):
        assert locator.canonicalization_version == "pdftext-1"
        page.verify(locator)
    assert page.cited(page.line("BORA")) == "Borealis Air BORA"


def test_a_span_is_verified_only_under_its_own_policy(make_pdf) -> None:
    pdf = ArtifactText(make_pdf(PDF_ROWS), "application/pdf")
    html = ArtifactText(PAGE, "text/html")
    with pytest.raises(LocatorError, match="made under walker-1, not pdftext-1"):
        pdf.verify(html.find("Acme Industrial"))
    with pytest.raises(LocatorError, match="made under pdftext-1, not walker-1"):
        html.verify(pdf.find("Acme Industrial"))


def test_only_html_and_pdf_have_citation_text() -> None:
    with pytest.raises(LocatorError, match="needs HTML or PDF, not text/plain"):
        ArtifactText(b"plain", "text/plain").find("plain")
    with pytest.raises(LocatorError, match="pdftext-1 cannot read it"):
        ArtifactText(b"not a pdf", "application/pdf").find("pdf")
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py packages/earnings-ingestion/tests/test_cohort_locators.py 2`.

Append to `packages/earnings-ingestion/tests/test_cohort_build.py`:

```python


def test_a_pdf_notice_keeps_the_intervals_and_cites_through_pdftext_1(
    pdf_cohort,
) -> None:
    frozen = load_manifest(
        pdf_cohort / DIRECTORY / "manifests" / "djia-synthetic-v1.json"
    )
    built = build(pdf_cohort, **OPTIONS)
    assert built.intervals == frozen.intervals
    assert built.report.blocking == ()
    pdf = next((pdf_cohort / DIRECTORY / "raw" / "synthetic-index").glob("*.pdf"))
    notice = [a for a in built.assertions if a.evidence_id == "index-2024-11-01"]
    assert {a.security_id for a in notice} == {"corvid-common", "borealis-common"}
    assert {a.raw_content_hash for a in notice} == {pdf.stem}
    assert {
        locator.canonicalization_version
        for assertion in notice
        for locator in assertion.evidence_locators
    } == {"pdftext-1"}
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py packages/earnings-ingestion/tests/test_cohort_build.py 2`.

Append to `packages/earnings-ingestion/tests/test_fetch_store.py`:

```python


def test_a_pdf_is_stored_as_a_pdf(tmp_path) -> None:
    body = b"%PDF-1.4\n%%EOF\n"
    record = retrieval(body).model_copy(
        update={"media_type": "application/pdf", "content_type": "application/pdf"}
    )
    ref = store_in(tmp_path).put("press", body, record, **RIGHTS)
    assert ref.storage_ref == f"data/raw/cohort/press/{sha256_hex(body)}.pdf"
    assert (tmp_path / ref.storage_ref).read_bytes() == body
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py packages/earnings-ingestion/tests/test_fetch_store.py 2`.

Replace `packages/earnings-ingestion/tests/test_cohort_acquire.py` with:

```python
"""Acquisition, offline: a fake fetch serves the synthetic cohort's SEC records."""

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.cohort.acquire import (
    check_media_type,
    cite,
    fetch_page,
    fetch_sec,
    register_saved,
    terms_digest,
)
from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.config import load_cohort_config
from earnings_ingestion.cohort.register import load_registers
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, build_options
from earnings_ingestion.fetch.client import Fetched
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore

RAW = FIXTURE_DIR / "raw"
SYNTHETIC = {
    "rights_status": RightsStatus.REDISTRIBUTABLE,
    "rights_basis": "synthetic test data, invented for this repository",
}
NOW = datetime(2026, 9, 30, 9, 0, tzinfo=UTC)


def served(repo: Path, *sources: str) -> dict[str, tuple[bytes, str]]:
    """Every saved artifact of ``sources``, by the URL it came from."""
    store = ArtifactStore(repo / RAW, repo)
    pages = {}
    for source_id in sources:
        for path in (repo / RAW / source_id / "retrievals").glob("*/*.json"):
            record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            body = store.get(source_id, record.sha256, **SYNTHETIC).body
            pages[record.request_url] = (body, record.media_type)
    return pages


def fake(pages: dict[str, tuple[bytes, str]], requested: list[str]):
    def fetch(url: str, types: frozenset[str]) -> Fetched:
        requested.append(url)
        body, media = pages[url]
        assert media in types
        return Fetched(
            body=body,
            retrieval=Retrieval(
                request_url=url,
                final_url=url,
                retrieved_at=NOW,
                retrieval_method=RetrievalMethod.HTTP,
                http_status=200,
                media_type=media,
                content_type=media,
                byte_count=len(body),
                sha256=sha256_hex(body),
            ),
        )

    return fetch


def test_fetch_sec_saves_every_record_the_build_reads(cohort_repo) -> None:
    pages = served(cohort_repo, "sec-edgar", "synthetic-fund")
    for source_id in ("sec-edgar", "synthetic-fund"):
        shutil.rmtree(cohort_repo / RAW / source_id)
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    options = build_options()
    registers = load_registers(
        cohort_repo, options["register"], options["sec_register"]
    )
    config = load_cohort_config(cohort_repo / FIXTURE_DIR)
    requested: list[str] = []

    first = fetch_sec(fake(pages, requested), store, registers, config)
    assert sorted(first.fetched) == sorted(pages)
    assert first.kept == []
    rebuilt = build(cohort_repo, **options)
    assert rebuilt.report.blocking == ()
    assert rebuilt.candidate_issuer_ids == (
        "cik-0009990001",
        "cik-0009990002",
        "cik-0009990003",
        "cik-0009990005",
        "cik-0009990006",
    )

    again = fetch_sec(fake(pages, requested), store, registers, config)
    assert len(again.kept) == 10
    assert all("/Archives/" not in url for url in again.fetched)


def registers_of(repo: Path):
    options = build_options()
    return load_registers(repo, options["register"], options["sec_register"])


def test_a_hand_saved_page_records_that_nothing_was_fetched(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    ref = register_saved(
        store,
        registers_of(cohort_repo),
        "synthetic-index",
        b"<p>Saved in a browser.</p>",
        url="https://index.example/notices/saved",
        media_type="text/html",
        saved_at=NOW,
    )
    (retrieval,) = store.get(
        "synthetic-index", ref.content_sha256, **SYNTHETIC
    ).retrievals
    assert retrieval.retrieval_method is RetrievalMethod.SAVED_BY_USER
    assert retrieval.http_status is None


def test_a_page_is_saved_only_for_a_registered_source(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    pages = {"https://index.example/a": (b"<p>A notice.</p>", "text/html")}
    fetch = fake(pages, [])
    ref = fetch_page(
        fetch,
        store,
        registers_of(cohort_repo),
        "synthetic-index",
        "https://index.example/a",
    )
    assert ref.storage_ref.startswith("tests/fixtures/cohort/raw/synthetic-index/")
    with pytest.raises(ValueError, match="not in the membership source register"):
        fetch_page(
            fetch,
            store,
            registers_of(cohort_repo),
            "elsewhere",
            "https://index.example/a",
        )


def test_cite_finds_a_span_or_a_pointer_and_shows_its_text(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    registers = registers_of(cohort_repo)
    page = next(iter(served(cohort_repo, "synthetic-index").values()))[0]
    locator, text = cite(
        store,
        registers,
        "synthetic-index",
        sha256_hex(page),
        find="Synthetic Industrial Average",
    )
    assert text == "Synthetic Industrial Average"
    assert locator.canonicalization_version == "walker-1"
    again, same = cite(
        store,
        registers,
        "synthetic-index",
        sha256_hex(page),
        span=(locator.start, locator.end),
    )
    assert (again, same) == (locator, text)
    tickers = next(
        body
        for url, (body, _) in served(cohort_repo, "sec-edgar").items()
        if url.endswith("company_tickers.json")
    )
    pointed, value = cite(
        store, registers, "sec-edgar", sha256_hex(tickers), pointer="/0/ticker"
    )
    assert (pointed.pointer, value) == ("/0/ticker", '"ACME"')
    with pytest.raises(ValueError, match="exactly one"):
        cite(store, registers, "sec-edgar", sha256_hex(tickers))


def test_cite_can_take_the_whole_line_holding_a_row(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    registers = registers_of(cohort_repo)
    page = next(iter(served(cohort_repo, "synthetic-roster").values()))[0]
    locator, text = cite(
        store, registers, "synthetic-roster", sha256_hex(page), find="ACM", line=True
    )
    assert "\t" in text and "ACM" in text and "\n" not in text
    found, _ = cite(store, registers, "synthetic-roster", sha256_hex(page), find="ACM")
    assert locator.start <= found.start < found.end <= locator.end
    with pytest.raises(ValueError, match="line needs find"):
        cite(
            store,
            registers,
            "synthetic-roster",
            sha256_hex(page),
            span=(0, 3),
            line=True,
        )


def test_a_terms_page_is_hashed_by_its_canonical_text() -> None:
    page = b"<html><body><p>Terms.</p></body></html>"
    assert terms_digest(page, "text/html") == terms_digest(
        page.replace(b"<p>", b"<p class='x'>"), "text/html"
    )
    assert terms_digest(b"plain", "text/plain") == sha256_hex(b"plain")


@pytest.mark.parametrize(
    ("body", "media_type", "found"),
    [
        (b"%PDF-1.4\n%%EOF\n", "text/html", "which are a PDF"),
        (b"<p>A notice.</p>", "application/pdf", "which are not a PDF"),
    ],
)
def test_bytes_that_contradict_their_type_are_refused(
    cohort_repo, body, media_type, found
) -> None:
    refusal = f"{media_type} contradicts the bytes, {found}"
    with pytest.raises(ValueError, match=refusal):
        check_media_type(body, media_type)
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    with pytest.raises(ValueError, match=refusal):
        register_saved(
            store,
            registers_of(cohort_repo),
            "synthetic-index",
            body,
            url="https://index.example/notices/saved",
            media_type=media_type,
            saved_at=NOW,
        )
    assert not list(
        (cohort_repo / RAW / "synthetic-index").glob(f"{sha256_hex(body)}.*")
    )


def test_bytes_that_match_their_type_pass() -> None:
    check_media_type(b"%PDF-1.7\n", "application/pdf")
    check_media_type(b"<p>A notice.</p>", "text/html")
    check_media_type(b"Terms.", "text/plain; charset=utf-8")


def test_a_pdf_page_is_fetched_and_saved_as_a_pdf(cohort_repo, make_pdf) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    pdf = make_pdf([(72, 720, "A notice.")])
    url = "https://index.example/notices/a.pdf"
    fetch = fake({url: (pdf, "application/pdf")}, [])
    ref = fetch_page(fetch, store, registers_of(cohort_repo), "synthetic-index", url)
    assert ref.media_type == "application/pdf"
    assert ref.storage_ref.endswith(f"/synthetic-index/{sha256_hex(pdf)}.pdf")
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py packages/earnings-ingestion/tests/test_cohort_acquire.py 2`.

Append to `packages/earnings-ingestion/tests/test_cohort_live.py`:

```python


def test_the_evidence_refetch_accepts_an_unchanged_pdf(pdf_cohort) -> None:
    served = pages(pdf_cohort)
    notice = "https://index.example/notices/index-2024-11-01"
    pdf = next((pdf_cohort / FIXTURE_DIR / "raw" / "synthetic-index").glob("*.pdf"))
    served[notice] = (pdf.read_bytes(), "application/pdf")
    serve = fake(served)

    def fetch(url, types):
        """The clients refuse a response whose media type was not asked for."""
        fetched = serve(url, types)
        assert fetched.retrieval.media_type in types
        return fetched

    result = verify_live(
        pdf_cohort,
        fetch_web=fetch,
        fetch_sec=fake(served),
        now=NOW,
        options=build_options(),
    )
    (check,) = [check for check in result.checks if check.url == notice]
    assert (check.outcome, check.retrieval.media_type) == (
        "unchanged",
        "application/pdf",
    )
    assert result.build_problems == ()
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py packages/earnings-ingestion/tests/test_cohort_live.py 2`.

Append to `apps/earnings-pipeline/tests/test_cohort_cli.py`:

```python


def test_register_saves_a_pdf_and_refuses_a_contradicting_type(
    repo, tmp_path_factory
) -> None:
    body = b"%PDF-1.4\n%%EOF\n"
    saved = tmp_path_factory.mktemp("browser") / "notice.pdf"
    saved.write_bytes(body)
    register = [
        "register",
        "synthetic-index",
        str(saved),
        "--url",
        "https://index.example/notices/by-hand.pdf",
        "--saved-at",
        "2026-09-29T10:00:00",
    ]
    stored = run(repo, *register, "--media-type", "application/pdf")
    assert stored.exit_code == 0, stored.output
    assert f"/synthetic-index/{sha256_hex(body)}.pdf" in stored.stdout
    refused = run(repo, *register, "--media-type", "text/html")
    assert refused.exit_code == 1
    assert "Refused: text/html contradicts the bytes" in refused.stderr


def test_terms_hashes_a_saved_copy_without_a_client(
    repo, monkeypatch, tmp_path_factory
) -> None:
    page = b"<html><body><p>Terms of use.</p></body></html>"
    saved = tmp_path_factory.mktemp("browser") / "terms.html"
    saved.write_bytes(page)
    for name in ("EDGAR_IDENTITY", "SOURCE_IDENTITY"):
        monkeypatch.delenv(name, raising=False)

    def no_client(*args, **kwargs):
        raise AssertionError("a saved copy needs no client")

    monkeypatch.setattr(cohort_cli, "open_web_client", no_client)
    monkeypatch.setattr(cohort_cli, "open_sec_client", no_client)
    terms = ["terms", "https://terms.example/terms-of-use", "--saved", str(saved)]
    hashed = run(repo, *terms)
    assert hashed.exit_code == 0, hashed.output
    digest = cohort_cli.terms_digest(page, "text/html")
    assert hashed.stdout == f'terms_sha256 = "{digest}"\n'
    refused = run(repo, *terms, "--media-type", "application/pdf")
    assert refused.exit_code == 1
    assert "Refused: application/pdf contradicts the bytes" in refused.stderr
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py apps/earnings-pipeline/tests/test_cohort_cli.py 2`.

Replace `packages/earnings-ingestion/tests/test_import_boundaries.py` with:

```python
"""earnings-ingestion imports neither earnings-themes nor the application, and no
browser: browser capture stays behind an optional extra (A §173; B3).

Only ``earnings_ingestion.browser.selenium_capture`` may load a browser library, and
only when something imports it; tests/contracts/test_import_scan.py checks the source
statically as well. The cohort's offline path, from saved artifacts to a frozen
manifest, loads no network client (A §410), and neither does pdftext-1's PDF reader.
"""

import json
import subprocess
import sys

import pytest

FORBIDDEN = {
    "earnings_themes",
    "earnings_pipeline",
    "selenium",
    "websocket",
    "playwright",
    "pyppeteer",
}


def modules_loaded_by(module: str) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing ``module``."""
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return {name.partition(".")[0] for name in json.loads(result.stdout)}


@pytest.mark.parametrize(
    "module",
    [
        "earnings_ingestion",
        "earnings_ingestion.browser",
        "earnings_ingestion.browser.install",
        "earnings_ingestion.browser.renderer",
        "earnings_ingestion.browser.serialize",
        "earnings_ingestion.browser.store",
        "earnings_ingestion.layout",
        "earnings_ingestion.layout.extract",
        "earnings_ingestion.fetch.client",
        "earnings_ingestion.fetch.robots",
        "earnings_ingestion.sec.client",
        "earnings_ingestion.cohort.build",
        "earnings_ingestion.cohort.pdftext",
        "earnings_ingestion.cohort.web",
    ],
)
def test_importing_ingestion_loads_nothing_forbidden(module: str) -> None:
    assert modules_loaded_by(module) & FORBIDDEN == set()


NETWORK = {
    "httpx",
    "earnings_ingestion.fetch.client",
    "earnings_ingestion.sec.client",
    "earnings_ingestion.cohort.web",
}


def full_modules_loaded_by(module: str) -> set[str]:
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return set(json.loads(result.stdout))


@pytest.mark.parametrize(
    "module",
    [
        "earnings_ingestion.cohort.build",
        "earnings_ingestion.cohort.freeze",
        "earnings_ingestion.cohort.locators",
        "earnings_ingestion.cohort.pdftext",
        "earnings_ingestion.cohort.synthetic",
        "earnings_ingestion.sec.data",
        "earnings_ingestion.sec.urls",
        "earnings_ingestion.fetch.store",
    ],
)
def test_the_offline_cohort_path_loads_no_network_client(module: str) -> None:
    """Building and freezing read saved bytes; they cannot reach the network (A §410)."""
    assert full_modules_loaded_by(module) & NETWORK == set()
```

This is block 4 for that path: extract it with
`python3 /tmp/plan6-extract.py packages/earnings-ingestion/tests/test_import_boundaries.py 4`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_pdftext.py packages/earnings-ingestion/tests/test_cohort_locators.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_fetch_store.py packages/earnings-ingestion/tests/test_cohort_acquire.py packages/earnings-ingestion/tests/test_cohort_live.py packages/earnings-ingestion/tests/test_import_boundaries.py apps/earnings-pipeline/tests/test_cohort_cli.py -q`

Expected: FAIL. Collection stops in two files, first with
`No module named 'earnings_ingestion.cohort.pdftext'`, then with
`cannot import name 'check_media_type'`, and pytest reports `2 errors`.

- [ ] **Step 3 (gate): Add the dependency**

Ask the user. `uv add` reaches PyPI to resolve, changes `uv.lock`, and installs
pypdf 6.19.0. The spike left its wheel in uv's cache. If the user declines, stop:
Task 17 cannot cite the PDF notices. On a yes:

```bash
uv add --package earnings-ingestion "pypdf==6.19.0"
```

Expected: `Resolved 152 packages`, and `+ pypdf==6.19.0` among the packages it installs.

Then confirm the lock and the environment offline, and that nothing else changed:

```bash
uv lock --check --offline
uv sync --locked --all-packages --offline
git diff --stat -- '*pyproject.toml' uv.lock
git diff -- packages/earnings-ingestion/pyproject.toml | grep '^[-+] '
```

Expected: `Resolved 152 packages`; then `Resolved 152 packages` and `Checked 41 packages`;
then `2 files changed`, `packages/earnings-ingestion/pyproject.toml` and `uv.lock`; then
the one added line, `+    "pypdf==6.19.0",`.

- [ ] **Step 4: Write the implementation**

Create `packages/earnings-ingestion/src/earnings_ingestion/cohort/pdftext.py`:

```python
"""pdftext-1: the citation text of a saved PDF (plan 6, P6-24).

S&P Dow Jones Indices publishes its index notices as PDFs, and a citation needs text
to point into. Given a PDF's bytes, the policy:

1. reads them with pypdf 6.19.0, holding pypdf's logger below ERROR for the call;
2. takes each page's plain-mode text, in page order;
3. normalizes the text to NFC, never NFKC;
4. collapses each line's whitespace runs to one space and strips its ends, dropping
   the lines left empty;
5. joins every line, across pages, with a newline.

The result is hashed and cited as walker-1's canonical text is: the SHA-256 of its
UTF-8, and half-open code-point offsets into it. pypdf is pinned exactly because its
version defines the policy, so another version's text is ``pdftext-2``. Like this
stage's use of walker-1, the policy produces citation text only, never a
``CanonicalDocument``.

A PDF is data: pypdf runs no script, follows no link, and reaches no network. Its
recovery warnings are silenced, since the text's hash, not the warnings, is the
authority. The policy refuses bytes pypdf cannot read; any encrypted PDF, even one
that an empty password opens, so the text never depends on a decryption attempt; and
a PDF with no text layer, since OCR is out of scope.
"""

import io
import logging
import re
import unicodedata

from pypdf import PdfReader

PDFTEXT_VERSION = "pdftext-1"
_WHITESPACE = re.compile(r"\s+")


class PdfTextError(ValueError):
    """A PDF that has no pdftext-1 text."""


def _pages(body: bytes) -> list[str]:
    """Each page's plain-mode text, with pypdf's logger held below ERROR."""
    logger = logging.getLogger("pypdf")
    level = logger.level
    logger.setLevel(logging.ERROR)
    try:
        reader = PdfReader(io.BytesIO(body))
        if reader.is_encrypted:
            raise PdfTextError(f"{PDFTEXT_VERSION} refuses an encrypted PDF")
        return [page.extract_text(extraction_mode="plain") for page in reader.pages]
    except PdfTextError:
        raise
    except Exception as exc:  # pypdf raises many exception types on malformed bytes
        raise PdfTextError(f"{PDFTEXT_VERSION} cannot read it: {exc}") from exc
    finally:
        logger.setLevel(level)


def pdf_text(body: bytes) -> str:
    """pdftext-1's text of a PDF; ``PdfTextError`` if it has none."""
    text = unicodedata.normalize("NFC", "\n".join(_pages(body)))
    lines = (_WHITESPACE.sub(" ", line).strip() for line in text.splitlines())
    joined = "\n".join(line for line in lines if line)
    if not joined:
        raise PdfTextError(
            f"{PDFTEXT_VERSION} found no text layer; OCR is out of scope"
        )
    return joined
```

Replace `packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py` with:

```python
"""Cite evidence in a saved artifact, and verify a citation, without its wording.

Two locator kinds exist (plan 6, P6-9):

- ``text_span``: code-point offsets into an artifact's citation text. The media type
  chooses the policy (P6-24): an HTML artifact's walker-1 canonical text, or a PDF's
  pdftext-1 text. The locator records the policy and the text's hash, so a different
  text can never silently move the span.
- ``json_pointer``: an RFC 6901 pointer into a JSON artifact.

``cited_sha256`` hashes the cited content: the span's text as UTF-8, or the canonical
JSON of the value at the pointer. Verification recomputes it from the saved bytes.
The cited content itself never enters a committed file; ``ArtifactText.cited`` returns
it for a person's terminal.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property

from earnings_core import ArtifactRef, hash_canonical_text, sha256_hex

from earnings_ingestion.canonical import (
    CANONICALIZATION_VERSION,
    CanonicalizationFailure,
    canonicalize,
)
from earnings_ingestion.cohort.digests import canonical_json
from earnings_ingestion.cohort.pdftext import PDFTEXT_VERSION, PdfTextError, pdf_text
from earnings_ingestion.cohort.records import Citation, EvidenceLocator, LocatorKind

_POLICIES = {"text/html": CANONICALIZATION_VERSION, "application/pdf": PDFTEXT_VERSION}


class LocatorError(ValueError):
    """A locator that does not identify the content it claims to."""


def _essence(media_type: str) -> str:
    return media_type.partition(";")[0].strip().lower()


def resolve_json_pointer(document: object, pointer: str) -> object:
    """The value at an RFC 6901 pointer; ``LocatorError`` if there is none."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise LocatorError(f"{pointer!r} is not a JSON pointer")
    value = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and token in value:
            value = value[token]
        elif (
            isinstance(value, list)
            and token.isdigit()
            and (token == "0" or not token.startswith("0"))
            and int(token) < len(value)
        ):
            value = value[int(token)]
        else:
            raise LocatorError(f"{pointer!r} names nothing in the document")
    return value


class ArtifactText:
    """One saved artifact, read once: citation text if HTML or PDF, data if JSON."""

    def __init__(self, body: bytes, media_type: str) -> None:
        self.body = body
        self.media_type = _essence(media_type)

    @property
    def version(self) -> str:
        """The citation-text policy the media type chooses: walker-1 for HTML,
        pdftext-1 for a PDF."""
        if self.media_type not in _POLICIES:
            raise LocatorError(f"a text span needs HTML or PDF, not {self.media_type}")
        return _POLICIES[self.media_type]

    @cached_property
    def canonical(self) -> tuple[str, str]:
        """The citation text, under ``version``, and its hash."""
        if self.version == PDFTEXT_VERSION:
            try:
                text = pdf_text(self.body)
            except PdfTextError as exc:
                raise LocatorError(str(exc)) from exc
            return text, hash_canonical_text(text)
        result = canonicalize(
            self.body, source_document_id="cohort-evidence", media_type="text/html"
        )
        if isinstance(result, CanonicalizationFailure):
            raise LocatorError(f"walker-1 cannot read it: {result.detail}")
        return result.document.canonical_text, result.document.canonical_hash

    @cached_property
    def data(self) -> object:
        if self.media_type != "application/json":
            raise LocatorError(f"a JSON pointer needs JSON, not {self.media_type}")
        try:
            return json.loads(self.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LocatorError(f"it is not JSON: {exc}") from exc

    def span(self, start: int, end: int) -> EvidenceLocator:
        text, text_hash = self.canonical
        if not 0 <= start < end <= len(text):
            raise LocatorError(f"[{start}, {end}) is outside [0, {len(text)})")
        return EvidenceLocator(
            kind=LocatorKind.TEXT_SPAN,
            canonicalization_version=self.version,
            canonical_sha256=text_hash,
            start=start,
            end=end,
            cited_sha256=sha256_hex(text[start:end].encode("utf-8")),
        )

    def find(self, needle: str, occurrence: int = 1) -> EvidenceLocator:
        """The span of the ``occurrence``-th (1-based) appearance of ``needle``."""
        text, _ = self.canonical
        start = -1
        for _ in range(occurrence):
            start = text.find(needle, start + 1)
            if start == -1:
                count = "" if occurrence == 1 else f" {occurrence} times"
                raise LocatorError(f"{needle!r} does not occur{count}")
        return self.span(start, start + len(needle))

    def line(self, needle: str, occurrence: int = 1) -> EvidenceLocator:
        """The span of the whole line holding the ``occurrence``-th ``needle``.
        walker-1 writes a table row as one line of tab-separated cells, and
        pdftext-1 a PDF table's row as one line of space-separated cells, so this
        cites a roster row with every cell in it."""
        found = self.find(needle, occurrence)
        text, _ = self.canonical
        start = text.rfind("\n", 0, found.start) + 1
        end = text.find("\n", found.end)
        return self.span(start, len(text) if end == -1 else end)

    def pointer(self, pointer: str) -> EvidenceLocator:
        value = resolve_json_pointer(self.data, pointer)
        return EvidenceLocator(
            kind=LocatorKind.JSON_POINTER,
            pointer=pointer,
            cited_sha256=sha256_hex(canonical_json(value)),
        )

    def cited(self, locator: EvidenceLocator) -> str:
        """The content ``locator`` cites, once it has been verified."""
        self.verify(locator)
        if locator.kind is LocatorKind.TEXT_SPAN:
            return self.canonical[0][locator.start : locator.end]
        value = resolve_json_pointer(self.data, locator.pointer)
        return canonical_json(value).decode("utf-8")

    def verify(self, locator: EvidenceLocator) -> None:
        """Raise ``LocatorError`` unless ``locator`` still cites what it hashed. A
        span made under another policy than this artifact's is refused before any
        text is extracted."""
        if locator.kind is LocatorKind.TEXT_SPAN:
            if locator.canonicalization_version != self.version:
                raise LocatorError(
                    f"the span was made under {locator.canonicalization_version},"
                    f" not {self.version}"
                )
            if self.canonical[1] != locator.canonical_sha256:
                raise LocatorError("the artifact's canonical text is not the one cited")
            fresh = self.span(locator.start, locator.end)
        else:
            fresh = self.pointer(locator.pointer)
        if fresh.cited_sha256 != locator.cited_sha256:
            raise LocatorError("the cited content no longer hashes to cited_sha256")


@dataclass(frozen=True)
class CitableArtifact:
    """A stored artifact with what a citation of it records."""

    source_id: str
    url: str
    artifact: ArtifactRef
    retrieved_at: datetime
    text: ArtifactText

    def cite(self, *locators: EvidenceLocator) -> Citation:
        return Citation(
            source_id=self.source_id,
            url=self.url,
            artifact=self.artifact,
            retrieved_at=self.retrieved_at,
            locators=locators,
        )
```

This is block 2 for that path: extract it with
`python3 /tmp/plan6-extract.py packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py 2`.

The other five files change by exact replacement. Each old text must match once, so
a file that has drifted from Task 16's stops the script before anything is written
to it:

- `build.py` records the artifact's policy, `text.version`, and drops the
  `walker-1` constant's import;
- `store.py` names a PDF `.pdf`;
- `acquire.py` gains `PDF` and `check_media_type`, `fetch_page` accepts a PDF, and
  `register_saved` checks the declared type;
- `live.py` refetches a PDF;
- `cohort_cli.py`'s `terms` gains `--saved` and `--media-type` (PT-9).

Create `/tmp/plan6-16b-edits.py`:

```python
from pathlib import Path

INGESTION = "packages/earnings-ingestion/src/earnings_ingestion/"
EDITS = {
    INGESTION + "cohort/build.py": [
        ("from earnings_ingestion.canonical import CANONICALIZATION_VERSION\n", ""),
        (
            "                canonicalization_version=CANONICALIZATION_VERSION,\n",
            "                canonicalization_version=text.version,\n",
        ),
    ],
    INGESTION + "fetch/store.py": [
        (
            '    "application/json": ".json",\n',
            '    "application/json": ".json",\n    "application/pdf": ".pdf",\n',
        ),
    ],
    INGESTION + "cohort/acquire.py": [
        (
            'HTML = frozenset({"text/html"})\n',
            'HTML = frozenset({"text/html"})\nPDF = frozenset({"application/pdf"})\n',
        ),
        (
            '    """Fetch one HTML page of a registered source and save it."""\n'
            "    registers.entry(source_id)\n"
            "    fetched = fetch(url, HTML)\n",
            '    """Fetch one HTML or PDF page of a registered source and save it."""\n'
            "    registers.entry(source_id)\n"
            "    fetched = fetch(url, HTML | PDF)\n",
        ),
        (
            "def register_saved(\n",
            "def check_media_type(body: bytes, media_type: str) -> None:\n"
            '    """Refuse bytes that contradict ``media_type`` (plan 6, P6-24): a PDF\n'
            "    declared as anything else, or a declared PDF without the %PDF- signature.\n"
            '    """\n'
            '    declared_pdf = media_type.partition(";")[0].strip().lower() in PDF\n'
            '    if body.startswith(b"%PDF-") != declared_pdf:\n'
            '        found = "not a PDF" if declared_pdf else "a PDF"\n'
            '        raise ValueError(f"{media_type} contradicts the bytes, which are {found}")\n'
            "\n"
            "\n"
            "def register_saved(\n",
        ),
        (
            '    """Save a page a person saved in a browser from ``url`` at ``saved_at``."""\n'
            "    registers.entry(source_id)\n",
            '    """Save a page a person saved in a browser from ``url`` at ``saved_at``."""\n'
            "    registers.entry(source_id)\n"
            "    check_media_type(body, media_type)\n",
        ),
    ],
    INGESTION + "cohort/live.py": [
        (
            "from earnings_ingestion.cohort.acquire import HTML, terms_digest\n",
            "from earnings_ingestion.cohort.acquire import HTML, PDF, terms_digest\n",
        ),
        (
            '            fetched = fetch(url, ANY if purpose == "terms" else HTML)\n',
            '            fetched = fetch(url, ANY if purpose == "terms" else HTML | PDF)\n',
        ),
    ],
    "apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py": [
        (
            "    earnings-pipeline cohort terms URL\n",
            "    earnings-pipeline cohort terms URL [--saved FILE]\n",
        ),
        (
            "Only ``fetch``, ``fetch-sec``, ``terms``, and ``verify-live`` use the network, each\n"
            "through its client's access policy; ``build`` and ``freeze`` read committed files and\n"
            "saved artifacts alone.",
            "Only ``fetch``, ``fetch-sec``, ``terms``, and ``verify-live`` use the network, each\n"
            "through its client's access policy, and ``terms --saved`` hashes a copy saved in a\n"
            "browser without it; ``build`` and ``freeze`` read committed files and saved\n"
            "artifacts alone.",
        ),
        (
            "from earnings_ingestion.cohort.acquire import (\n    cite,\n",
            "from earnings_ingestion.cohort.acquire import (\n    check_media_type,\n    cite,\n",
        ),
        (
            '@cohort.command("terms")\n'
            "def terms_command(context: typer.Context, url: str) -> None:\n"
            '    """Print the hash a register records for a terms page."""\n'
            "    layout: Layout = context.obj\n",
            '@cohort.command("terms")\n'
            "def terms_command(\n"
            "    context: typer.Context,\n"
            "    url: str,\n"
            "    saved: Annotated[\n"
            "        Path | None,\n"
            '        typer.Option(help="A copy saved in a browser: hash it, and send nothing."),\n'
            "    ] = None,\n"
            '    media_type: Annotated[str, typer.Option(help="The saved copy\'s type.")] = (\n'
            '        "text/html"\n'
            "    ),\n"
            ") -> None:\n"
            '    """Print the hash a register records for a terms page: fetched from URL, or\n'
            '    read from a copy that a person saved in a browser (plan 6, P6-24)."""\n'
            "    if saved is not None:\n"
            "        body = saved.read_bytes()\n"
            "        try:\n"
            "            check_media_type(body, media_type)\n"
            "            digest = terms_digest(body, media_type)\n"
            "        except ValueError as error:\n"
            '            _fail(f"Refused: {error}")\n'
            "        typer.echo(f'terms_sha256 = \"{digest}\"')\n"
            "        return\n"
            "    layout: Layout = context.obj\n",
        ),
    ],
}
for name, pairs in EDITS.items():
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert text.count(old) == 1, (name, old[:60])
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
print("code edits applied")
```

Extract it, then run it from the repository root:

```bash
python3 /tmp/plan6-extract.py /tmp/plan6-16b-edits.py && python3 /tmp/plan6-16b-edits.py
```

Expected: `extracted /tmp/plan6-16b-edits.py: 120 lines`, then `code edits applied`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_cohort_pdftext.py packages/earnings-ingestion/tests/test_cohort_locators.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_fetch_store.py packages/earnings-ingestion/tests/test_cohort_acquire.py packages/earnings-ingestion/tests/test_cohort_live.py packages/earnings-ingestion/tests/test_import_boundaries.py apps/earnings-pipeline/tests/test_cohort_cli.py -q`

Expected: `102 passed`.

- [ ] **Step 6: Record `pdftext-1` in the data dictionary**

No field or value changes, so the dictionary's test already passes. Three
descriptions name `walker-1` alone: the `text_span` value,
`EvidenceLocator.canonicalization_version`, and the curated files'
`canonical_sha256`, in two tables. Each now names `pdftext-1` beside it.

Create `/tmp/plan6-16b-dictionary.py`:

```python
from pathlib import Path

path = Path("docs/data-dictionary.md")
text = path.read_text(encoding="utf-8")
EDITS = [
    (
        "| `text_span` | Half-open code-point offsets into an HTML artifact's walker-1 canonical text |",
        "| `text_span` | Half-open code-point offsets into an artifact's citation text: walker-1's canonical text for HTML, pdftext-1's text for a PDF |",
        1,
    ),
    (
        "| `canonicalization_version` | ID part or null | `walker-1` for a text span; null for a pointer |",
        "| `canonicalization_version` | ID part or null | A text span's citation-text policy: `walker-1` for HTML, `pdftext-1` for a PDF; null for a pointer |",
        1,
    ),
    (
        "| `canonical_sha256` | 64 lowercase hex | Its walker-1 canonical text's hash |",
        "| `canonical_sha256` | 64 lowercase hex | Its citation text's hash: walker-1's for HTML, pdftext-1's for a PDF |",
        2,
    ),
]
for old, new, count in EDITS:
    assert text.count(old) == count, (old[:60], text.count(old))
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
print("data dictionary updated")
```

```bash
python3 /tmp/plan6-extract.py /tmp/plan6-16b-dictionary.py && python3 /tmp/plan6-16b-dictionary.py
uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q
```

Expected: `extracted /tmp/plan6-16b-dictionary.py: 26 lines`, then
`data dictionary updated`, then `78 passed`.

- [ ] **Step 7: Run the checks**

```bash
python3 /tmp/plan6-escapes.py packages/earnings-ingestion/src/earnings_ingestion/cohort/pdftext.py packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py packages/earnings-ingestion/src/earnings_ingestion/cohort/acquire.py packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py packages/earnings-ingestion/src/earnings_ingestion/fetch/store.py apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py packages/earnings-ingestion/tests/conftest.py packages/earnings-ingestion/tests/test_cohort_pdftext.py packages/earnings-ingestion/tests/test_cohort_locators.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_fetch_store.py packages/earnings-ingestion/tests/test_cohort_acquire.py packages/earnings-ingestion/tests/test_cohort_live.py packages/earnings-ingestion/tests/test_import_boundaries.py apps/earnings-pipeline/tests/test_cohort_cli.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
git status --short -- tests/fixtures
```

Expected: `escapes intact`; `929 passed, 24 deselected`; `280 passed`; `All checks passed!` and
`211 files already formatted`; no `git status` output, since the synthetic cohort is unchanged.

- [ ] **Step 8: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/pyproject.toml uv.lock packages/earnings-ingestion/src/earnings_ingestion/cohort/pdftext.py packages/earnings-ingestion/src/earnings_ingestion/cohort/locators.py packages/earnings-ingestion/src/earnings_ingestion/cohort/build.py packages/earnings-ingestion/src/earnings_ingestion/cohort/acquire.py packages/earnings-ingestion/src/earnings_ingestion/cohort/live.py packages/earnings-ingestion/src/earnings_ingestion/fetch/store.py apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py packages/earnings-ingestion/tests/conftest.py packages/earnings-ingestion/tests/test_cohort_pdftext.py packages/earnings-ingestion/tests/test_cohort_locators.py packages/earnings-ingestion/tests/test_cohort_build.py packages/earnings-ingestion/tests/test_fetch_store.py packages/earnings-ingestion/tests/test_cohort_acquire.py packages/earnings-ingestion/tests/test_cohort_live.py packages/earnings-ingestion/tests/test_import_boundaries.py apps/earnings-pipeline/tests/test_cohort_cli.py docs/data-dictionary.md
git commit -m "feat(ingestion): cite PDF notices through pdftext-1, and hash saved terms pages"
git status --short
```

Expected: no `git status` output after the commit.

---
### Task 17: The real DJIA cohort — curate, review, and freeze

This task builds the real cohort from evidence saved at execution, under the user's
decisions (P6-2, P6-3). It cannot be replayed at planning: every fact comes from an
artifact saved here. The files below hold `[GATE: …]` slots. Fill each from the
named step's output, and never leave one.

- **Hard stops.** Each gate is a hard stop: ask in chat, and wait for a clear yes.
- **Raw artifacts** stay under the gitignored `data/raw/cohort/`.
- **What is committed:** the register, the three curated files, and the frozen
  manifest. They hold facts, URLs, locators, and hashes only.
- **The saved notices.** The user saved five S&P DJI notices, all PDFs, which are
  cited through `pdftext-1` (P6-24). Two state DJIA changes in the window:
  - `1475162`, a press release of 2024-11-01: NVIDIA and Sherwin-Williams replace
    Intel and Dow Inc., prior to the open on 2024-11-08;
  - `1484126`, a press release of 2026-06-23: Alphabet (Class A) replaces Verizon,
    prior to the open on 2026-06-29.

  The other three are not curated: `1471327` (3M's spin-off, before the window),
  `1480747` (Honeywell's spin-off, which leaves Honeywell in the index), and
  `1483528` (a Transportation Average change). Only the saved notices decide,
  through the rows that Step 6 cites.
- **Facts already supplied.** Task 17 paused at Step 1 on 2026-09-26 for this
  plan's amendment. `specs/pdf-citation-text.md`, §State when this was written,
  records what the user supplied then:
  - each cited PDF's URL, saved-at time, and SHA-256;
  - the anchor revision;
  - S&P DJI's terms URL and its hand-saved copy;
  - two of the three terms hashes.

  Take those from there, and ask only for what is missing.

**Security IDs.** A security ID is a stable internal ID (A §264). It is the company's
short name as a lowercase slug, with words joined by hyphens, followed by `-common`,
or by `-class-<letter>` when the cited evidence names the share class. Examples:
`3m-common`, `american-express-common`, `alphabet-class-a`. The ID never changes
with a ticker or name, and a security that leaves and rejoins keeps it.

**Files:**

- Create: `docs/membership-source-register.toml`.
- Create: `config/universe/djia/universe.toml`, `evidence.toml`, and
  `overrides.toml`.
- Create (generated): `config/universe/djia/manifests/djia-2024q3-2026q2-v1.json`.
- Local only: `data/raw/cohort/`.

**Interfaces:**

- Consumes: every command of Task 16, and Task 5's confirmation of the fund's CIK.
- Produces the real cohort's frozen manifest, which Stage 5 reads with
  `load_manifest`:

  ```python
  from pathlib import Path

  from earnings_ingestion.cohort.freeze import load_manifest

  load_manifest(Path("config/universe/djia/manifests/djia-2024q3-2026q2-v1.json"))
  ```

- [ ] **Step 1 (gate): Settle the sources with the user**

Put these to the user, in one batch of questions:

1. **The register's four entries,** in Step 3's block. That covers:
   - their evidence classes and roles;
   - the rights the plan proposes: `redistributable` for Wikipedia's CC BY-SA 4.0
     text, `restricted` for S&P DJI, `local_only` for the fund's filings, and
     `redistributable` for the user's own list.
2. **The anchor revision.** Ask for the ID and timestamp of the latest revision of
   English Wikipedia's "Dow Jones Industrial Average" saved before
   `2024-07-01T00:00:00Z`. The user reads them from the page's history in a
   browser. The agent does not fetch `/w/` pages, which robots.txt disallows.
3. **The announcements.** Ask for the list of S&P DJI announcements of DJIA
   constituent changes, from the anchor's date through `2026-09-22`, with each
   one's URL, and for S&P DJI's terms-of-use page (Step 2).
   - A change announced after the cutoff is still curated: the build withholds it
     (P6-12).
   - A PDF is cited under `pdftext-1` (P6-24). For a PDF saved by hand, also ask
     when it was saved, in UTC, and never derive a URL from a file name. Only a
     PDF without a text layer, which `pdftext-1` refuses, stops for the user.

- [ ] **Step 2 (gate): Record the terms pages' hashes**

Ask the user, naming the requests. There are three terms pages:

- one at `foundation.wikimedia.org`, through the web client, after its robots.txt;
- S&P DJI's, the same way. The notices link no terms page, so its URL comes from
  the footer of the S&P DJI site;
- `https://www.sec.gov/about/privacy-information`, through the SEC client.

That is about five requests, sent with `SOURCE_IDENTITY` and `EDGAR_IDENTITY`. On a
yes, run each and keep its output:

```text
uv run --locked --all-packages earnings-pipeline cohort terms https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use
uv run --locked --all-packages earnings-pipeline cohort terms [GATE: S&P DJI's terms_url]
uv run --locked --all-packages earnings-pipeline cohort terms https://www.sec.gov/about/privacy-information
```

Expected: each prints `terms_sha256 = "<64 hex>"`.

- A `Stopped:` line means a refusal. Report it to the user, who may save the page
  in a browser and read it. The saved copy is hashed with no request and no
  identity (PT-9):

  ```text
  uv run --locked --all-packages earnings-pipeline cohort terms [GATE: the terms_url] --saved "[GATE: the saved file]"
  ```

  Expected: `terms_sha256 = "<64 hex>"`. A terms page that can be neither fetched
  nor saved leaves that source unregistered.
- The user reads each terms page before its hash goes into the register, because a
  hash records a reading.

- [ ] **Step 3: Write the register and the curated files**

Create `docs/membership-source-register.toml`:

```toml
# Membership source register (AGENTS.md §242; plan 6, P6-15): the index-membership
# sources that config/universe/djia/evidence.toml cites, keyed by source_id. It quotes
# no source. A published source's terms are tracked by terms_url and terms_sha256,
# which `earnings-pipeline cohort terms <terms_url>` computes; a different hash asks
# for a new reading. Release sources and sec-edgar stay in docs/source-register.toml.
schema_version = 1

[sources.wikipedia-djia]
owner = "Wikipedia contributors; hosted by the Wikimedia Foundation"
url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
access_method = """One fixed revision, requested as \
https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average?oldid=<revision> through the cohort \
web client after robots.txt allows it, with the identity in SOURCE_IDENTITY. If robots.txt or \
the site refuses, a person saves the revision in a browser, and `earnings-pipeline cohort \
register` records it as saved_by_user."""
cost = "Free; no account."
license_terms = """Text under the Creative Commons Attribution-ShareAlike 4.0 license, under the \
Wikimedia Foundation's Terms of Use at terms_url."""
terms_url = "https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use"
terms_sha256 = "[GATE: Step 2's terms_sha256 for this terms_url]"
redistribution_status = """Reuse needs attribution and share-alike. This repository commits \
facts and citations only (plan 6, P6-3), and the saved revision stays under data/raw/cohort/."""
coverage = "A dated secondary roster: a revision states the constituents when it was saved."
expected_update_pattern = "Edited at any time; a saved revision never changes."
known_limitations = [
    "Secondary evidence written by volunteers: it can lag or err, so official changes decide.",
    "A revision's date is when it was saved, not when the roster changed.",
]
last_verified = "[GATE: Step 2's date]"
evidence_class = "secondary"
roles = ["anchor", "corroboration"]
rights_status = "redistributable"
rights_basis = "CC BY-SA 4.0: reuse needs attribution and share-alike"

[sources.spdji-announcements]
owner = "S&P Dow Jones Indices LLC"
url = "https://www.spglobal.com/spdji/en/"
access_method = """Each Dow Jones Industrial Average change notice is a PDF that a person saves \
in a browser, and `earnings-pipeline cohort register --media-type application/pdf` records it \
as saved_by_user, with its URL and the time it was saved. S&P DJI's site refuses automated \
requests (HTTP 403), so no notice is fetched."""
cost = "Free to read; no account."
license_terms = "S&P Dow Jones Indices' terms of use, at terms_url, govern the announcements."
terms_url = "[GATE: Step 2's S&P DJI terms URL]"
terms_sha256 = "[GATE: Step 2's terms_sha256 for this terms_url]"
redistribution_status = """S&P DJI materials carry redistribution restrictions. This repository \
commits facts and citations only (plan 6, P6-3), and the saved announcements stay under \
data/raw/cohort/."""
coverage = "Official additions to and removals from the index, with their announced and effective dates."
expected_update_pattern = "A new announcement for each change; announcements are not revised in place."
known_limitations = [
    "An effective date is stated as a trading day, before the open or after the close, with no time.",
    "The site refused automated requests at planning, so announcements may be saved by hand.",
    "Notices are PDFs, cited through pdftext-1 (pypdf 6.19.0); a notice without a text layer cannot be cited.",
]
last_verified = "[GATE: Step 2's date]"
evidence_class = "official"
roles = ["change"]
rights_status = "restricted"
rights_basis = "S&P DJI's terms restrict redistribution; only locators and facts are kept (R2.1)"

[sources.dia-nport]
owner = "SPDR Dow Jones Industrial Average ETF Trust, the filer; hosted by SEC EDGAR"
url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001041130"
access_method = """The fund's N-PORT filings (NPORT-P and NPORT-P/A), listed in its submissions \
JSON and fetched through the shared SEC client by `earnings-pipeline cohort fetch-sec`, with the \
identity in EDGAR_IDENTITY (docs/source-register.toml, sec-edgar)."""
cost = "Free; no account or API key."
license_terms = """SEC's statement on reuse of its website content, at terms_url. The filings are \
authored by the filer."""
terms_url = "https://www.sec.gov/about/privacy-information"
terms_sha256 = "[GATE: Step 2's terms_sha256 for this terms_url]"
redistribution_status = """SEC's reuse statement does not address the filer's rights in its \
filings, and this register draws no conclusion about them. The filings stay under \
data/raw/cohort/, and only facts and citations are committed."""
coverage = "The fund's holdings on each report date: a public ETF proxy for the index roster."
expected_update_pattern = "A report for each period; amendments arrive as new accessions."
known_limitations = [
    "An ETF proxy: holdings corroborate the roster and never establish membership (A §261).",
    "Holdings name issuers, not securities, and may lag an index change.",
]
last_verified = "[GATE: Step 2's date]"
evidence_class = "etf_proxy"
roles = ["corroboration"]
rights_status = "local_only"
rights_basis = "SEC-hosted filings whose filer rights are unaddressed; kept local, like sec-edgar"

[sources.user-djia-list]
owner = "The project owner"
url = "https://github.com/lowmason/earnings-themes/blob/main/config/universe/djia/evidence.toml"
access_method = """Supplied in plan 6's planning session on 2026-09-26, and transcribed into \
config/universe/djia/evidence.toml as a check list."""
cost = "Free."
license_terms = "Supplied by the project owner for this repository."
redistribution_status = "The owner's own list of names and tickers, committed in evidence.toml."
coverage = "One list of 30 names and tickers, after the index's June 2026 change."
expected_update_pattern = "Never updated; another list would be another check."
known_limitations = [
    "Supplied after the cutoff and cites no source: a check only, compared and reported, never evidence.",
]
last_verified = 2026-09-26
evidence_class = "user_supplied"
roles = ["check"]
rights_status = "redistributable"
rights_basis = "the project owner's own list, supplied for this repository"
```

Fill each `[GATE: …]` from Steps 1 and 2:

- each `terms_sha256` with its hash, quoted;
- `spdji-announcements`'s `terms_url`, quoted;
- each `last_verified` with Step 2's date, bare, such as `2026-10-01`.

Create `config/universe/djia/universe.toml`:

```toml
# The point-in-time DJIA cohort (plan 6): P's universe definition, which each frozen
# manifest copies. Task 5's probe, or Task 17's fetch-sec, confirms the fund's CIK.
universe_id = "djia-2024q3-2026q2"
universe_name = "djia"
period_end_start = 2024-07-01
period_end_stop = 2026-07-01
public_information_cutoff = 2026-09-22
membership_reference = "first_publication_time"
selection_policy_version = "djia-pilot/1"
expected_member_count = 30

[etf_proxy]
source_id = "dia-nport"
cik = "0001041130"
```

If Task 5's probe was declined, the fund's CIK is still a lead: Step 7 confirms it.

Create `config/universe/djia/overrides.toml`:

```toml
# Reviewed decisions for the real cohort (plan 6, P6-18). Each override records its
# evidence, rationale, reviewer, and effective dates; the reviewer is the user.
schema_version = 1
```

Create `config/universe/djia/evidence.toml`. For now it holds only the user's check
list, which is the user's own list from chat, transcribed:

```toml
# The point-in-time DJIA cohort's evidence (plan 6, P6-3): facts and citations only.
schema_version = 1

[[checks]]
evidence_id = "user-list-2026-09-26"
source_id = "user-djia-list"
as_of = 2026-09-22
published_on = 2026-09-26

[[checks.members]]
name = "Goldman Sachs Group Inc."
ticker = "GS"

[[checks.members]]
name = "Caterpillar Inc."
ticker = "CAT"

[[checks.members]]
name = "Microsoft Corp"
ticker = "MSFT"

[[checks.members]]
name = "Amgen Inc"
ticker = "AMGN"

[[checks.members]]
name = "UnitedHealth Group Incorporated"
ticker = "UNH"

[[checks.members]]
name = "Visa Inc."
ticker = "V"

[[checks.members]]
name = "The Travelers Companies, Inc."
ticker = "TRV"

[[checks.members]]
name = "Alphabet Inc. (Class A)"
ticker = "GOOGL"

[[checks.members]]
name = "JPMorgan Chase & Co."
ticker = "JPM"

[[checks.members]]
name = "Apple Inc."
ticker = "AAPL"

[[checks.members]]
name = "The Sherwin-Williams Company"
ticker = "SHW"

[[checks.members]]
name = "American Express Company"
ticker = "AXP"

[[checks.members]]
name = "Home Depot, Inc."
ticker = "HD"

[[checks.members]]
name = "Johnson & Johnson"
ticker = "JNJ"

[[checks.members]]
name = "Amazon.com Inc"
ticker = "AMZN"

[[checks.members]]
name = "McDonald's Corporation"
ticker = "MCD"

[[checks.members]]
name = "Salesforce, Inc."
ticker = "CRM"

[[checks.members]]
name = "International Business Machines Corporation"
ticker = "IBM"

[[checks.members]]
name = "Nvidia Corp"
ticker = "NVDA"

[[checks.members]]
name = "Honeywell International, Inc."
ticker = "HON"

[[checks.members]]
name = "Chevron Corporation"
ticker = "CVX"

[[checks.members]]
name = "Boeing Company"
ticker = "BA"

[[checks.members]]
name = "3M Company"
ticker = "MMM"

[[checks.members]]
name = "Merck & Co., Inc."
ticker = "MRK"

[[checks.members]]
name = "Procter & Gamble Company"
ticker = "PG"

[[checks.members]]
name = "Walmart Inc."
ticker = "WMT"

[[checks.members]]
name = "Cisco Systems, Inc."
ticker = "CSCO"

[[checks.members]]
name = "The Walt Disney Company"
ticker = "DIS"

[[checks.members]]
name = "Coca-Cola Company"
ticker = "KO"

[[checks.members]]
name = "Nike, Inc."
ticker = "NKE"
```

Then check that the four files load:

```bash
grep -n 'GATE:' docs/membership-source-register.toml
uv run --locked --all-packages python -c "from pathlib import Path; from earnings_ingestion.cohort.register import load_registers; from earnings_ingestion.cohort.config import load_cohort_config; load_registers(Path('.')); c = load_cohort_config(Path('config/universe/djia')); print('curated files load:', c.universe.universe_id, len(c.evidence.checks[0].members))"
```

Expected, a prediction that was replayed with dummy hashes: no `grep` output, then
`curated files load: djia-2024q3-2026q2 30`.

- [ ] **Step 4 (gate): Save the anchor, and register the notices**

**The anchor** is fetched. Ask the user, naming the requests: the revision's page and
`en.wikipedia.org`'s robots.txt, through the web client at one request per second.
On a yes:

```text
uv run --locked --all-packages earnings-pipeline cohort fetch wikipedia-djia "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average?oldid=[GATE: the revision ID]"
```

Expected: `<sha256>  data/raw/cohort/wikipedia-djia/<sha256>.html  <url>`. Keep the
SHA-256.

**If it is refused,** the command prints `Stopped:` and a reason:

- a robots.txt refusal names the rule;
- a persistent 403 stops that client.

Neither is retried with another identity. Ask the user to save the revision in a
browser, as "Webpage, HTML only", and record it with:

```text
uv run --locked --all-packages earnings-pipeline cohort register wikipedia-djia [GATE: the saved file] --url "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average?oldid=[GATE: the revision ID]" --saved-at [GATE: when it was saved, in UTC, as 2026-10-01T14:30:00]
```

Expected: the same one-line output, and the retrieval records `saved_by_user`.

**The notices** are PDFs the user saved in a browser, so none is fetched and this
sends no request. Register each cited notice with its original URL and the time it
was saved, in UTC. The user supplies both, and a URL is never derived from a file
name:

```text
uv run --locked --all-packages earnings-pipeline cohort register spdji-announcements "[GATE: the saved PDF]" --url "[GATE: its original URL]" --saved-at [GATE: when it was saved, in UTC] --media-type application/pdf
```

Expected: `<sha256>  data/raw/cohort/spdji-announcements/<sha256>.pdf  <url>`, with
the saved file's SHA-256. The retrieval records `saved_by_user`. Keep each SHA-256.

- `Refused:` means the bytes contradict the declared type (P6-24): stop and ask.
- A notice with no text layer is refused later, by `cite`: stop and ask then.

- [ ] **Step 5: Cite the anchor's rows**

`walker-1` writes each row of the components table as one line of tab-separated
cells, so cite each constituent's whole row by its symbol cell:

```text
uv run --locked --all-packages earnings-pipeline cohort cite wikipedia-djia [GATE: the anchor's sha256] --find $'\t[GATE: ticker]\t' --line
```

- **The output.** stdout prints `canonical_sha256`, `span`, and `cited_sha256`, and
  stderr prints the cited row.
- **Check each row.** Read the row on stderr, and never paste it into a file. It must
  be the components table's row, with the company and the symbol. If the needle
  first matches elsewhere, add `--occurrence N`.
- **Coverage.** Cite all 30 rows. If the table does not list 30 companies, stop and
  ask.

Insert the anchor into `evidence.toml`, before `[[checks]]`: one `[[snapshots]]` and
one `[[snapshots.members]]` for each row. Take `name` as the row writes the company,
and `ticker` as it writes the symbol. `as_of` and `published_on` are both the
revision's UTC date (P6-2).

```toml
[[snapshots]]
evidence_id = "wikipedia-rev-[GATE: revision ID]"
source_id = "wikipedia-djia"
role = "anchor"
url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average?oldid=[GATE: revision ID]"
artifact_sha256 = "[GATE: Step 4's sha256]"
canonical_sha256 = "[GATE: cite's canonical_sha256]"
as_of = [GATE: the revision's UTC date]
published_on = [GATE: the revision's UTC date]

[[snapshots.members]]
security_id = "[GATE: the security ID]"
name = "[GATE: the company, as the row writes it]"
ticker = "[GATE: the symbol]"
span = [GATE: cite's span]
cited_sha256 = "[GATE: cite's cited_sha256]"
```

- [ ] **Step 6: Cite each announcement**

For each notice, cite through `pdftext-1` (P6-24), which writes each row of a table
as one line, its cells joined by single spaces:

- each company it adds or removes, by its row in the notice's summary table: use
  `--find "<name> <ticker>" --line`, with the name and ticker as the row writes
  them.
  - Read the row on stderr: it must be that company's row, with its ticker.
  - If the needle first matches elsewhere, add `--occurrence N`.
- the effective date, by one of two routes:
  - a row that states it, cited with `--line`;
  - a span across lines, found without `--line` by a needle that holds a newline
    (`$'…\n…'`), since `pdftext-1` joins lines with `\n`.

```text
uv run --locked --all-packages earnings-pipeline cohort cite spdji-announcements [GATE: sha256] --find "[GATE: the company's name and ticker, as its row writes them]" --line
uv run --locked --all-packages earnings-pipeline cohort cite spdji-announcements [GATE: sha256] --find "[GATE: text in the row that states the effective date]" --line
```

Insert one `[[changes]]` for each announcement, before `[[checks]]`, with its
entries. `timing` is `before_open` when the announcement says "prior to the open",
`after_close` when it says the change takes effect after the close, and
`unspecified` otherwise. Omit `published_at` unless the page states a publication
time, which must be converted to UTC.

```toml
[[changes]]
evidence_id = "spdji-[GATE: the announcement date, YYYY-MM-DD]"
source_id = "spdji-announcements"
url = "[GATE: the announcement's URL]"
artifact_sha256 = "[GATE: Step 4's sha256]"
canonical_sha256 = "[GATE: cite's canonical_sha256]"
announced_on = [GATE: the announcement date]
published_on = [GATE: the date it was first published]
published_at = "[GATE: its stated publication time in UTC, such as 2024-11-01T21:15:00Z]"
effective_on = [GATE: the effective date]
timing = "[GATE: before_open, after_close, or unspecified]"
date_span = [GATE: cite's span for the effective-date statement]
date_cited_sha256 = "[GATE: its cited_sha256]"

[[changes.entries]]
action = "[GATE: added or removed]"
security_id = "[GATE: the security ID, the anchor's for a removal]"
name = "[GATE: the company, as the announcement writes it]"
ticker = "[GATE: the ticker, as the announcement writes it]"
span = [GATE: cite's span]
cited_sha256 = "[GATE: cite's cited_sha256]"
```

Check that no slot is left, and that the evidence loads:

```bash
grep -n 'GATE:' config/universe/djia/evidence.toml
uv run --locked --all-packages python -c "from pathlib import Path; from earnings_ingestion.cohort.config import load_cohort_config; e = load_cohort_config(Path('config/universe/djia')).evidence; print('evidence loads:', len(e.snapshots[0].members), 'anchor rows,', len(e.changes), 'changes')"
```

Expected, a prediction: no `grep` output, then
`evidence loads: 30 anchor rows, [GATE: the count of announcements] changes`.

- [ ] **Step 7 (gate): Save SEC's records**

Ask the user. `fetch-sec` sends, through the shared SEC client:

- the ticker list;
- the submissions of about 35 CIKs, one for each cited ticker;
- the fund's submissions and older pages;
- the fund's N-PORT documents from 2024-07-01 through the cutoff.

That is about 50 to 60 requests, at 2 per second, as `EDGAR_IDENTITY`. On a yes:

Run: `uv run --locked --all-packages earnings-pipeline cohort fetch-sec`

Expected, a prediction: `fetched <n>, already saved 0` and `requests sent: <n>`,
with `<n>` between 40 and 70.

- `Stopped:` means a persistent 403, a block page, or a spent budget. Report it, and
  never rotate identity.
- If Task 5's probe was declined, confirm the fund's CIK now:

  ```bash
  uv run --locked --all-packages python -c "import json, pathlib; from earnings_core import RightsStatus; from earnings_ingestion.fetch.store import ArtifactStore; s = ArtifactStore(pathlib.Path('data/raw/cohort'), pathlib.Path('.')).latest('sec-edgar', 'https://data.sec.gov/submissions/CIK0001041130.json', rights_status=RightsStatus.LOCAL_ONLY, rights_basis='local'); print(json.loads(s.body)['name'])"
  ```

  The name must be the SPDR Dow Jones Industrial Average ETF Trust. If it isn't,
  stop and ask.

- [ ] **Step 8: Build, and read the report**

Run: `uv run --locked --all-packages earnings-pipeline cohort build`

- **Expected,** a prediction: every finding printed as `BLOCKING`, `resolved`, or
  `noted`, each with its digest and detail, then
  `<n> intervals, <n> candidate issuers, <n> blocking findings, content <hash>`.
- **Exit status.** It exits 1 while anything blocks.
- **Problems.** `problem:` lines on stderr mean a citation failed, which no review
  can settle. Examples: an artifact is missing, bytes changed, a name or ticker is
  not in the cited text, or a source is unregistered. Fix the curated fact from the
  saved artifact, and rebuild.

Likely findings, which are predictions:

- `identity:` for a security whose cited name SEC's record does not cover, such as a
  row that writes "IBM";
- fund `difference:` findings for holdings whose names cover no cited name;
- `gap:2026q3`, noted, because the quarter's N-PORT is filed after the cutoff;
- the user list's `difference:` and `withheld:`, both noted.

- [ ] **Step 9 (gate): Review each blocking finding with the user**

Put every `BLOCKING` finding to the user, with its detail and the decision it needs.
Each decision becomes an override in `config/universe/djia/overrides.toml`, with a
rationale in the user's words, signed by the user (P6-18):

| Finding | Decision | Override |
| --- | --- | --- |
| `membership_conflict:` or `membership_ambiguity:` | Which statement is wrong, after rechecking the transcription against the saved page. A transcription error is fixed in `evidence.toml`, never overridden. | `reject_assertion`, naming `membership_assertion_id` (`<evidence_id>:<security_id>:<action>`) |
| `identity:` | The CIK SEC's record supports, or that the security stays unresolved and excluded | `set_issuer` (`security_id`, `cik`, and a citation), or `retain_unresolved` (`security_id`) |
| A fund `difference:` whose unmatched holding names a member differently | Which security the holding is | `holding_alias` (`security_id`, `holding_name`) |
| Any other `difference:` or a `member_count:` | Whether the stated detail is explained, for example a holding's lag. If so, the finding is accepted as read. | `acknowledge` (`finding_id`, `finding_digest` from `build`'s output) |
| `missing_anchor:` | Fix the anchor from the saved revision, or stop and ask | none |

To cite SEC's record in a `set_issuer`, find the saved submissions' SHA-256, then
cite its `/tickers`:

```text
uv run --locked --all-packages python -c "from pathlib import Path; from earnings_core import RightsStatus; from earnings_ingestion.fetch.store import ArtifactStore; print(ArtifactStore(Path('data/raw/cohort'), Path('.')).latest('sec-edgar', 'https://data.sec.gov/submissions/CIK[GATE: 10 digits].json', rights_status=RightsStatus.LOCAL_ONLY, rights_basis='local').ref.content_sha256)"
uv run --locked --all-packages earnings-pipeline cohort cite sec-edgar [GATE: that sha256] --pointer /tickers
```

An override looks like this; its fields are listed in `docs/data-dictionary.md`:

```toml
[[overrides]]
override_id = "[GATE: a short slug, such as ibm-issuer]"
kind = "set_issuer"
security_id = "[GATE: the security ID]"
cik = "[GATE: 10 digits]"
rationale = "[GATE: the user's reason]"
reviewer = "[GATE: the user's name, as they sign it]"
recorded_on = [GATE: today's date]
effective_from = 2024-07-01

[[overrides.citations]]
source_id = "sec-edgar"
url = "https://data.sec.gov/submissions/CIK[GATE: 10 digits].json"
artifact_sha256 = "[GATE: that sha256]"

[overrides.citations.locator]
kind = "json_pointer"
pointer = "/tickers"
cited_sha256 = "[GATE: cite's cited_sha256]"
```

The implementer never writes `reviewer`: the user supplies the name in chat, for
each override or once for all.

- [ ] **Step 10: Rebuild until nothing blocks**

Run: `uv run --locked --all-packages earnings-pipeline cohort build`

Repeat Steps 9 and 10 until `build` exits 0, printing no `BLOCKING` and no `STALE`
line.

- An acknowledgement binds to what its finding said. If a later fix changes that
  finding, `build` prints `STALE`, and the user reads the new finding.
- Then check that no slot is left:

  ```bash
  grep -n 'GATE:' config/universe/djia/overrides.toml
  ```

  Expected: no output.

- [ ] **Step 11 (gate): The user approves the report**

Show the user the final `build` output:

- each `resolved` finding with its override;
- each `noted` finding;
- the interval, candidate-issuer, and content-hash line.

Freeze only after a clear yes.

- [ ] **Step 12: Freeze**

```bash
uv run --locked --all-packages earnings-pipeline cohort freeze
uv run --locked --all-packages earnings-pipeline cohort freeze
```

Expected, a prediction:

- first `froze djia-2024q3-2026q2 v1`, then its path and content hash;
- then `unchanged: djia-2024q3-2026q2 v1`, with the same path and hash.

Then check that the frozen manifest loads without the saved artifacts, and that
every CIK in it is padded:

```bash
uv run --locked --all-packages python -c "from pathlib import Path; from earnings_ingestion.cohort.freeze import load_manifest; m = load_manifest(Path('config/universe/djia/manifests/djia-2024q3-2026q2-v1.json')); ciks = [x.cik for x in m.mappings if x.cik]; assert all(len(c) == 10 and c.isdigit() for c in ciks); print('manifest loads:', len(m.intervals), 'intervals,', len(m.candidate_issuer_ids), 'candidate issuers,', len(m.report.blocking), 'blocking')"
```

Expected: `manifest loads: <n> intervals, <n> candidate issuers, 0 blocking`.

- [ ] **Step 13: Run the checks**

```bash
git check-ignore data/raw/cohort/wikipedia-djia
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
git status --short
```

Expected:

- `data/raw/cohort/wikipedia-djia`, so the raw evidence is ignored;
- `929 passed, 24 deselected`, and no test changed;
- `All checks passed!` and `211 files already formatted`;
- only `docs/membership-source-register.toml` and `config/`, as untracked.

- [ ] **Step 14: Commit**

```bash
git log --oneline -3
git add docs/membership-source-register.toml config/universe/djia
git commit -m "feat(cohort): curate, review, and freeze the point-in-time DJIA cohort"
```

---
### Task 18: Live verification, the verification record, and the current state

P-VL runs once on the frozen real cohort. The record gathers what Stage 4 verified,
in the house style of `docs/verification/layout-1.md`. `CLAUDE.md` and `README.md`
then describe the current state. The record's numbers were not known at planning, so
its template holds `[GATE: …]` slots. Fill each from the named step or file, and
never leave one.

**Files:**

- Create: `docs/verification/djia-cohort.md`.
- Modify: `CLAUDE.md` and `README.md`, by exact replacement.

**Interfaces:**

- Consumes: everything this plan built; Task 17's frozen manifest; Task 5's and Task
  17's outputs.
- Produces: documentation only. Test counts stay at Task 16b's.

- [ ] **Step 1 (gate): Verify the real cohort live**

Ask the user. `verify-live` sends about ten requests, with both identities:

- each cited source's terms page;
- each anchor and notice URL, the PDF notices included;
- each host's robots.txt.

Its rebuild reads saved artifacts only. On a yes:

Run: `uv run --locked --all-packages earnings-pipeline cohort verify-live`

Expected, a prediction:

- one line per check, as `<outcome>  <purpose>  <source_id>  <url>`;
- `rebuilt <hash>; frozen <hash>`, with the two hashes equal;
- `record: data/runs/cohort/live/<stamp>.json`.

Read each outcome with the user:

- **`changed` on a terms page:** the user rereads the terms. If they still hold,
  record the new `terms_sha256` and `last_verified` in the register, in a commit of
  its own, `docs(cohort): record the reread terms of <source>`.
- **`changed` on an evidence page:** the saved bytes stay the evidence. Report the
  difference to the user, and change nothing.
- **`refused`:** record it as a limitation. Never retry with another identity.
  - A prediction: S&P DJI's host refused Task 17's requests with a persistent 403,
    so expect its checks `refused`.
  - A client that meets a 403 sends nothing more (P6-20). So each later check
    through the web client then reads `failed`, as not requested.
- **Unequal hashes, or build problems:** stop and report. The frozen manifest no
  longer reproduces.

- [ ] **Step 2: Write the verification record**

Create `docs/verification/djia-cohort.md`:

````markdown
# The point-in-time DJIA cohort: verification record

This record verifies roadmap Stage 4, the point-in-time DJIA cohort, which
`specs/point-in-time-djia-cohort.md` specifies. Plan 6
(`specs/plans/6-point-in-time-djia-cohort.md`) built it.

## What was verified

| Exit clause | Evidence |
| --- | --- |
| Every interval rests on source evidence; every CIK is 10 characters (P-A4) | `test_every_interval_rests_on_supported_evidence`; `test_every_resolved_cik_is_ten_digits_and_one_issuer_per_cik`; the real manifest's load check (Task 17, Step 12) |
| Intervals from an anchor plus changes; inclusive starts, exclusive ends, open intervals (P-VF) | `test_anchor_additions_and_removals_make_half_open_intervals`; `test_intervals_are_half_open` |
| A missing anchor refuses the freeze with its reason; conflicts stay separate and hold it until review | `test_a_missing_anchor_refuses_the_freeze_with_its_reason`; `test_conflicting_dates_stay_separate_and_hold_until_one_is_rejected`; `test_before_review_its_findings_hold_the_freeze` |
| The report lists every conflict and gap (P-A4) | `test_every_break_in_the_sequence_is_a_conflict`; `test_every_uncorroborated_quarter_is_a_gap`; the real report below |
| Evidence published after the cutoff cannot revise the version (P-C4) | `test_evidence_published_after_the_cutoff_is_withheld`; `test_a_row_published_after_the_cutoff_never_changes_an_identity` |
| No snapshot backdated; no ETF holdings treated as the roster | `test_a_later_snapshot_is_never_backdated_into_the_anchor`; `test_fund_holdings_are_never_the_roster` |
| Ticker changes and multiple securities preserved; one issuer row per issuer (P-VF) | `test_a_ticker_change_keeps_both_identities_and_resolves_once`; `test_two_securities_of_one_issuer_derive_one_issuer_row` |
| Access and redistribution recorded for every source; unclear rights stay local | `docs/membership-source-register.toml`; `test_the_manifest_records_rights_for_every_source_it_cites`; `test_saved_evidence_stays_local_and_the_fixture_is_committed` |
| Frozen with a version and hash, atomically; refused on unresolved identity unless retained and excluded | `test_identical_content_keeps_its_version`; `test_a_tampered_manifest_is_refused`; `test_a_written_file_is_never_replaced`; `test_a_retained_unresolved_security_is_excluded_and_the_freeze_proceeds` |
| No network, proprietary roster, or credential by default; `live` opt-in and recorded (P-VL) | `test_saved_evidence_replays_to_the_frozen_manifest`, under a socket guard; `test_the_offline_cohort_path_loads_no_network_client`; the live run below |
| Workers share 2 req/s through the SEC client; a persistent 403 stops without a new identity (R1.3, D5) | `test_concurrent_workers_stay_at_or_below_two_requests_per_second`; `test_a_persistent_403_stops_without_rotating_identity`; `test_one_client_per_machine` |

## The frozen cohort

- **The manifest.** `config/universe/djia/manifests/djia-2024q3-2026q2-v1.json`,
  content hash [GATE: Task 17, Step 12's hash], created [GATE: its `created_at`].
- **The anchor.** [GATE: its `evidence_id`], Wikipedia revision [GATE: ID], saved
  [GATE: date]. It was [GATE: "fetched through the web client" or "saved by hand
  and registered, because <the refusal>"].
- **The changes.** One line each:
  - [GATE: `evidence_id`, announced [date], effective [date] [timing]: added
    [securities]; removed [securities]; fetched or saved by hand].
- **Size.** [GATE: n] intervals over [GATE: n] securities, and [GATE: n] candidate
  issuers.
- **Corroboration.** [GATE: the N-PORT report dates compared; the superseded and
  withheld filings; the gaps].
- **The review.** Signed by [GATE: the reviewer]:
  - [GATE: one line per override: `override_id`, kind, target, and the rationale in
    brief].
- **At the freeze.** [GATE: each `resolved` and `noted` finding's ID].

## The format probe and the requests

| Step | Client | Requests |
| --- | --- | --- |
| Task 5, the format probe | SEC | [GATE: the count it printed, or "declined"] |
| The PDF spike, while `specs/pdf-citation-text.md` was designed | uv, outside the lockfile | pypdf 6.19.0 and pdfminer.six 20260107, run from uv's cache; no project file changed |
| Task 16b, Step 3, the `uv add` of `pypdf==6.19.0` | uv, to PyPI | [GATE: what `uv add` printed: packages resolved, and pypdf installed] |
| Task 17, Step 2, the terms pages | web and SEC | [GATE] |
| Task 17, Step 4, the evidence pages | web | [GATE; name any page saved by hand] |
| Task 17, Step 7, `fetch-sec` | SEC | [GATE: `requests sent`] |
| Task 18, Step 1, `verify-live` | web and SEC | [GATE] |

At planning, before this plan existed, one run of the probe reached SEC by accident.
`EDGAR_IDENTITY` was set, and a `-m live` run meant to confirm the skip sent about
five requests before failing on a bug. It saved nothing.

## The live verification

[GATE: the date]: [GATE: the count of each outcome, and each `changed` or `refused`
check with its URL and what was done]. The rebuilt content hash
[GATE: "equals" or "differs from"] the frozen one. The record is under
`data/runs/cohort/live/`, local and uncommitted.

## Limitations

- **The report's own.** The manifest's `report.limitations`:
  - the anchor's date bounds each anchored start from below;
  - fund holdings are an ETF proxy;
  - SEC's identity records were retrieved after the cutoff;
  - intervals are resolved to the day.
- **One machine.** The SEC lock coordinates one machine. Stage 1's harness client
  must never run live beside a package client.
- **`acceptanceDateTime`.** The readers take SEC's offset as written. Whether the
  time is UTC or Eastern is unverified, and Stage 4 uses it only to order filings
  of one fund. Stage 5 must settle it before using it as a filing's acceptance time
  (R1.5).
- **Secondary anchor.** A Wikipedia revision can lag or err. The official changes
  and the fund's holdings check it, and each disagreement was reviewed.
- **`pdftext-1`.** It has no OCR, so a PDF without a text layer cannot be cited. It
  is bound to pypdf 6.19.0: another version's text is `pdftext-2`, and every PDF
  citation must then be made again.
````

Then check that no slot is left:

Run: `grep -n 'GATE:' docs/verification/djia-cohort.md`

Expected: no output.

- [ ] **Step 3: Record the current state in `CLAUDE.md` and `README.md`**

The lock and sync counts that `CLAUDE.md` records are Task 16b's. Confirm them
first, offline:

```bash
uv lock --check --offline
uv sync --locked --all-packages --offline
```

Expected: `Resolved 152 packages`, then `Resolved 152 packages` and
`Checked 41 packages`, as Task 16b's Step 3 printed. If a count differs, stop and
report, since the script below records these counts.

Apply the exact replacements, each of which must match once:

```bash
python3 - <<'EOF'
from pathlib import Path

EDITS = {
    "CLAUDE.md": [
        (
            "and Stage 3's canonicalizer and browser diagnostic path in `packages/earnings-ingestion`; `earnings-themes` is still a `hello()` scaffold",
            "Stage 3's canonicalizer and browser diagnostic path in `packages/earnings-ingestion`, and Stage 4's point-in-time DJIA cohort and shared SEC client there too; `earnings-themes` is still a `hello()` scaffold",
        ),
        (
            "It is the stage spec for Stages 4 and 15 and binds Stage 5's eligibility and pilot-selection contracts; no stage is complete. |",
            "It is the stage spec for Stages 4 and 15 and binds Stage 5's eligibility and pilot-selection contracts. Stage 4 is complete (plan 6); Stage 15 is not, so the spec stays live. |",
        ),
        (
            "## Current state: Stages 1–3 complete; `earnings-themes` still a scaffold",
            "## Current state: Stages 1–4 complete; `earnings-themes` still a scaffold",
        ),
        (
            "\n`earnings-themes` still contains only a `hello()` stub, as do the top-level modules of `earnings-ingestion` and `apps/earnings-pipeline`; the application's one command is `earnings-pipeline browser setup`. `data/` is gitignored and holds only local, uncommitted material: fetched pages under `data/raw/`, and under `data/runs/` Stage 1's run outputs, the user's rendered copies, and the browser capture store; `config/`, `prompts/` and `codebooks/` are empty directories.",
            "\nStage 4 (point-in-time DJIA cohort, plan 6, `specs/point-in-time-djia-cohort.md`) is done:\n\n"
            "- `packages/earnings-ingestion/src/earnings_ingestion/fetch/` holds the retrieval record, the polite client ported from `pf_fetch.py`, the robots gate, and the content-addressed artifact store; `sec/` holds the shared SEC client, through which every SEC request goes (R1.3, D5), and SEC's record readers.\n"
            "- `packages/earnings-ingestion/src/earnings_ingestion/cohort/` builds the cohort from curated files and saved artifacts, fetching nothing, and freezes it as a versioned, content-hashed manifest. It cites an HTML page through `walker-1` and a PDF through `pdftext-1` (`cohort/pdftext.py`, with pypdf 6.19.0 pinned exactly). `earnings-pipeline cohort` holds its commands.\n"
            "- `docs/membership-source-register.toml` is the second source register, for index-membership sources. `config/universe/djia/` holds the curated files and the frozen manifests, which hold facts and citations, never source text. `tests/fixtures/cohort/` is the synthetic cohort, which regenerates byte for byte and replays offline. `docs/verification/djia-cohort.md` records the stage.\n\n"
            "`earnings-themes` still contains only a `hello()` stub, as do the top-level modules of `earnings-ingestion` and `apps/earnings-pipeline`; the application's commands are `earnings-pipeline browser setup` and the `earnings-pipeline cohort` group. `data/` is gitignored and holds only local, uncommitted material: fetched pages under `data/raw/`, the cohort's saved evidence under `data/raw/cohort/`, and under `data/runs/` Stage 1's run outputs, the user's rendered copies, the browser capture store, the client locks, and the cohort's live-verification records; `prompts/` and `codebooks/` are empty directories.",
        ),
        (
            "- The root-level `src/earnings_themes/` orphan from `uv init` has been deleted.",
            "- `EDGAR_IDENTITY` may be exported in your shell, so a `live` test's skip guard does not stop it: `-m live` really sends requests. Run live checks only with the user's go-ahead; check collection with `--collect-only`.\n"
            "- The root-level `src/earnings_themes/` orphan from `uv init` has been deleted.",
        ),
        (
            "lock and sync counts refreshed at\n`1fe96c3` via `uv lock --check` and `uv sync`:",
            "lock and sync counts refreshed at\nplan 6's Task 16b, which added `pypdf==6.19.0`, via `uv lock --check` and `uv sync`:",
        ),
        ("# Resolved 151 packages\n", "# Resolved 152 packages\n"),
        ("      # 40 packages incl.", "      # 41 packages incl."),
    ],
    "README.md": [
        (
            "| Stage 2 contracts and exactness checks (schema v1) |",
            "| Stage 2 contracts and exactness checks (schema v2) |",
        ),
        (
            "| `packages/earnings-ingestion/` | Source adapters, raw snapshots, deterministic parsing, canonicalization, and entity resolution | Scaffold only |",
            "| `packages/earnings-ingestion/` | Source adapters, raw snapshots, deterministic parsing, canonicalization, and entity resolution | Stage 3's canonicalizer and browser diagnostic path; Stage 4's artifact store, shared SEC client, and point-in-time DJIA cohort |",
        ),
        (
            "| `apps/earnings-pipeline/` | Thin application layer for configuration, stage coordination, checkpoints, and reporting | Scaffold only |",
            "| `apps/earnings-pipeline/` | Thin application layer for configuration, stage coordination, checkpoints, and reporting | `earnings-pipeline browser setup` and the `earnings-pipeline cohort` commands |",
        ),
        (
            "| `tests/fixtures/releases/` | Stage 1's eight release fixtures, with gold annotations and a provenance manifest | Present |",
            "| `tests/fixtures/releases/` | Stage 1's eight release fixtures, with gold annotations and a provenance manifest | Present |\n"
            "| `config/universe/djia/` | The cohort's curated files and frozen universe manifests: facts and citations, never source text | Stage 4's frozen cohort |\n"
            "| `tests/fixtures/cohort/` | The synthetic cohort, which replays offline to its frozen manifest | Present |",
        ),
        (
            "stages. Stages 1 and 2 are complete; Stage 3 is next.",
            "stages. Stages 1 to 4 are complete; Stage 5 is next.",
        ),
        (
            "[data dictionary](docs/data-dictionary.md) documents every field. The next\nmilestone is **Stage 3: structure-aware canonicalization**.",
            "[data dictionary](docs/data-dictionary.md) documents every field.\n\n"
            "**Stage 3: structure-aware canonicalization** is complete. `earnings-ingestion`\n"
            "turns a saved release into a hashed `walker-1` canonical document with typed\n"
            "elements, tables, sentences, and boilerplate masks.\n"
            "[ADR 0002](docs/adr/0002-keep-the-browser-capture-diagnostic-only.md) keeps its\n"
            "pinned-browser capture diagnostic-only.\n\n"
            "**Stage 4: point-in-time DJIA cohort** is complete. `earnings-ingestion` rebuilds\n"
            "the index's membership security by security, from a dated anchor snapshot and\n"
            "S&P Dow Jones Indices' announcements. It resolves each security to an issuer and\n"
            "a zero-padded CIK from SEC's records, and reports every conflict, gap, and\n"
            "difference. The reviewed cohort is frozen as a versioned, content-hashed\n"
            "manifest in `config/universe/djia/manifests/` before any earnings document is\n"
            "acquired. Every SEC request goes through one shared client at 2 requests per\n"
            "second. The [verification record](docs/verification/djia-cohort.md) has the\n"
            "details. The next milestone is **Stage 5: event discovery, eligibility, and\n"
            "acquisition**.",
        ),
        (
            "a Stage 1 deliverable. Stage 4 adds a second register for\n  index-membership sources, which does not exist yet. A free or open-source",
            "a Stage 1 deliverable. Stage 4 added a second register for\n  index-membership sources,\n  [`docs/membership-source-register.toml`](docs/membership-source-register.toml),\n  which quotes no source. A free or open-source",
        ),
    ],
}
for name, pairs in EDITS.items():
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert text.count(old) == 1, (name, old[:60])
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
print("current state recorded")
EOF
wc -l AGENTS.md
```

Expected: `current state recorded`, then `837 AGENTS.md`, because `AGENTS.md` is
untouched.

- [ ] **Step 4: Final verification**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages python expirements/parser-fidelity/fetch_policy_pages.py verify
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
git grep -n 'GATE:' -- docs config CLAUDE.md README.md
```

Expected:

- `929 passed, 24 deselected`;
- `280 passed`;
- `All checks passed!` and `211 files already formatted`;
- `register quotes verified`;
- `freeze verified`;
- no `git grep` output.

- [ ] **Step 5: Commit**

```bash
git log --oneline -3
git add docs/verification/djia-cohort.md CLAUDE.md README.md
git commit -m "docs: record Stage 4 in its verification record, CLAUDE.md, and the README"
```

## Handoffs

Completion's reconcile carries each block below into the named stage's entry, so a
later session finds it without this plan.

### To Stage 5 (event discovery, eligibility, and acquisition)

- **The frozen cohort.**
  - `earnings_ingestion.cohort.freeze.load_manifest(path)` reads a manifest without
    any saved artifact, and rechecks its hash.
  - The real one is `config/universe/djia/manifests/djia-2024q3-2026q2-v<N>.json`,
    and the latest version wins.
  - The synthetic one, `tests/fixtures/cohort/manifests/djia-synthetic-v1.json`, is
    the offline fixture for Stage 5's P-VI replay. `write_synthetic_cohort`
    regenerates it.
- **Intervals.** Intervals are half-open dates (P6-23).
  - Each bound keeps its announced timing (`before_open`, `after_close`, or
    `unspecified`) and its basis. An `anchor_snapshot` start is a lower bound, never
    an entry date.
  - `MembershipInterval.contains(day)` and `overlaps(start, stop)` answer
    date-level questions, and `cohort.intervals.roster(intervals, day)` gives the
    members on a day.
  - Ordering a same-day change against a release is Stage 5's eligibility decision
    (P-C2). Stage 4 invents no time.
- **Issuers.**
  - `manifest.issuers` holds one row per CIK, with its securities, so several
    securities of one issuer derive one expected event per period.
  - `candidate_issuer_ids` is the union over intervals overlapping the eligible
    publication range (P6-13).
  - A `retained_unresolved` mapping is excluded with its reason.
- **The shared SEC client (D5).** Every SEC request goes through
  `earnings_ingestion.sec.client.open_sec_client`. The EDGAR adapter adds no
  throttle of its own.
  - `SecClient.fetch(url, expected_types)` returns `Fetched(body, retrieval)`.
  - `fetch.store.ArtifactStore` keeps raw snapshots with their `Retrieval` records.
  - `sec.data`'s readers parse submissions and filing pages.
- **`acceptanceDateTime` is unverified.** `Filing.accepted_at` carries SEC's offset
  as written. Whether the time is UTC or Eastern must be settled before it serves as
  `filing_acceptance_time` (R1.5).
- **The selection policy.** `selection_policy_version = "djia-pilot/1"` is recorded
  and not yet defined. Stage 5 defines it from P §Deterministic pilot selection, or
  bumps the name (P6-4).
- **Live tests.** `EDGAR_IDENTITY` may be exported, so `-m live` really sends
  requests. Stage 5's live checks need the same gate.

### To Stage 15 (full DJIA eight-quarter run)

- The frozen manifest's intervals and candidate issuers define the run's universe,
  and Stage 15 reselects nothing.
- The cohort spec stays live for Stage 15's plan (P6-1). Its Rollout carries the
  Stage 15 Roadmap line for that plan's header.

### Deferred items that stay open

- **`1-release-parser-fidelity`:** "Keep `EDGAR_IDENTITY` out of the lock gate's
  adapter processes". The shared client doesn't touch the harness's lock gate.
- **Planned elsewhere:** Stage 5's EDGAR adapter and its processing-state table,
  both on the new client.

## Completion

After Task 18, run the final whole-branch review. Then:

1. **Plan Completion Protocol** (writing-plans).
   - Run the resolve-before-defer gate.
   - Mark up this plan: tick the steps, add `> Deviation:` and `> Skipped:` notes, and
     add the status header. A declined Task 5 probe is a `> Skipped:` note, not a
     deferred item: Task 17's `fetch-sec` met SEC's formats instead.
   - Record two deviations, each as a `> Deviation:` note:
     - at Task 4, Step 6, block 1 of `test_import_boundaries.py` ended in a stray
       blank line, which the user approved stripping;
     - the amendment by `specs/pdf-citation-text.md`, which inserted Task 16b and
       changed P6-9, P6-15, the counts after Task 16b, and Tasks 17 and 18.
2. **Rollout stamp.** Append a blank line and these two lines to the end of
   `specs/point-in-time-djia-cohort.md`, putting the completion date in place of
   `YYYY-MM-DD`:

   ```text
   > Stage 4: COMPLETE (YYYY-MM-DD) — implemented by plan 6 (specs/plans/completed/6-point-in-time-djia-cohort.md).
   > Next: resume the roadmap. This spec stays live for Stage 15 (plan 6, P6-1).
   ```

   This is the spec's only edit.
3. **Deferred items.** In `specs/deferred_items.md`:
   - run the ticking pass over earlier items, although none is expected to close;
   - append this plan's own deferred items, if any, under a
     `## 6-point-in-time-djia-cohort — YYYY-MM-DD` heading with the completion date;
   - commit steps 1–3 together as
     `docs(specs): mark up plan 6, record Stage 4's rollout, and tick deferred items`.
4. **Backlog triage.** Run
   `uv run --no-project --python 3.13 python ~/.claude/skills/writing-plans/scripts/deferred_stats.py`,
   and report its summary line. Present the triage rubric if its thresholds trip.
5. **Retire the plan and the amendment's spec (P6-1).** The cohort spec stays in
   `specs/`.
   - `specs/pdf-citation-text.md` retires with this plan, which implements it. The
     protocol would not match it, because its name is not the plan's.
   - Move both:

     ```bash
     git mv specs/plans/6-point-in-time-djia-cohort.md specs/plans/completed/
     git mv specs/pdf-citation-text.md specs/completed/
     ```

   - Neither holds a relative Markdown link. `docs/verification/djia-cohort.md`
     cites both old paths, and the retired spec cites the plan's, so re-point each,
     as plan 5 re-pointed the Stage 3 records when their spec retired. The retired
     plan keeps its own mentions, as plans 4 and 5 do. Then mark the spec complete
     at its top, and check that no old path is left outside the retired plans:

     ```bash
     python3 - <<'EOF'
     from pathlib import Path

     PLAN = ("`specs/plans/6-point-in-time-djia-cohort.md`", "`specs/plans/completed/6-point-in-time-djia-cohort.md`")
     SPEC = ("`specs/pdf-citation-text.md`", "`specs/completed/pdf-citation-text.md`")
     for name, pairs in (
         ("docs/verification/djia-cohort.md", (PLAN, SPEC)),
         ("specs/completed/pdf-citation-text.md", (PLAN,)),
     ):
         path = Path(name)
         text = path.read_text(encoding="utf-8")
         for old, new in pairs:
             assert text.count(old) == 1, (name, old)
             text = text.replace(old, new)
         path.write_text(text, encoding="utf-8")
         print(f"re-pointed {name}")
     path = Path("specs/completed/pdf-citation-text.md")
     title, rest = path.read_text(encoding="utf-8").split("\n", 1)
     status = "**Status: COMPLETE (YYYY-MM-DD)** — implemented by plan 6, Task 16b; retired to specs/completed/ with plan 6."
     path.write_text(f"{title}\n\n{status}\n{rest}", encoding="utf-8")
     print("marked specs/completed/pdf-citation-text.md complete")
     EOF
     git grep -n -e "specs/plans/6-point-in-time" -e "specs/pdf-citation-text" -- . ':!specs/plans/completed'
     ```

     Put the completion date in place of `YYYY-MM-DD` before running it. Expected:
     the two `re-pointed` lines and the `marked` line, then no `git grep` output.
   - Commit as `chore(specs): retire plan 6 and the pdftext-1 spec`.
6. **Roadmap.** Run derive-roadmap's reconcile step on
   `specs/evidence-linked-theme-extraction-roadmap.md`. The spec's Stage 4 stamp is
   authoritative. The reconcile:
   - ticks Stage 4;
   - carries the Handoffs above into Stages 5 and 15;
   - re-validates every unticked stage against what shipped.

   Commit as `docs(roadmap): tick Stage 4 and reconcile the later stages`.
7. **Integrate** with finishing-a-development-branch. Open a pull request from
   `stage-4-point-in-time-djia-cohort` to `main`, as Stages 1–3 did. The branch was
   unpushed at planning time, so this is its first push, and the repository is
   public.
8. **Report.**
   - State the commands actually run, and their results.
   - State every live request, by gate, with its count.
   - State the real cohort's version and content hash.
   - State that no model was called.
