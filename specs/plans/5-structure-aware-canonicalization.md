# Structure-Aware Canonicalization, Plan B (Stage 3): the Browser Diagnostic Path — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 3 — on
> plan completion, tick the stage and re-validate later stages against what
> shipped.
>
> This stamp fires: plan B's completion completes Stage 3, which plan 4 began (the
> spec's §Rollout). Completion below says exactly what it does.

**Goal:** Build Stage 3's browser diagnostic path and decide what it is worth:

- a pinned, isolated Chrome for Testing capture behind the `browser-capture` extra;
- `layout-1`, a layout extractor whose elements map onto `walker-1`'s canonical text
  as exact spans;
- a comparison of `walker-1`, `layout-1` and the fallback, fixed before any release
  is captured;
- R3.5's second leg, which makes that report final;
- ADR 0002, which decides whether any of it is promoted.

This meets the spec's plan B exit criteria 1–10 and completes Stage 3.

**Architecture:**

- **Capture** (`packages/earnings-ingestion/src/earnings_ingestion/browser/`).
  - `BrowserRenderer.capture(saved_html, capture_policy)` returns a `RenderedCapture`:
    `innerText`, per-block layout metadata, and content-hashed screenshots, with every
    field the browser spec lists.
  - A Selenium adapter drives the pinned Chrome for Testing under capture policy
    `isolated/1`:
    - document JavaScript is off;
    - CDP Fetch interception blocks and records every request;
    - a dead proxy and a null host resolver sit behind it;
    - one browser runs per capture, killed with its process group.
  - A `FakeRenderer` serves the default tests.
  - A store under `data/runs/` writes captures atomically and never overwrites one.
  - `earnings-pipeline browser setup` is the only code that downloads the binaries.
- **layout-1** (`…/layout/`).
  - An independent reader: the walker's rules, re-read from computed style and
    geometry.
  - Its blocks pass through the same C1–C5.
  - Mapping policy `anchored-1` places each block on `walker-1`'s canonical text by
    exact, token-bounded matches that the neighbouring blocks disambiguate. A block
    that cannot be placed is an `alignment_failed` record, never a guess.
- **The comparison** (`expirements/parser-fidelity/`).
  - Before any release is captured, the units of the three targeted classes and the
    comparison's rules are committed, then hash-frozen with every file that decides
    the numbers.
  - The eight release captures are then committed as fixtures.
  - The frozen scorer measures the three configurations, and a generated report
    applies the pre-registered repair and regression rules.
  - The user decides ADR 0002 at a gate, among the outcomes the rule allows.
- **Promotion** (`…/promoted/`, only on outcome 2 or 3). `walker-2` keeps
  `walker-1`'s text and hash and takes `layout-1`'s elements where it switches. Its
  eight fixtures are generated beside `walker-1`'s, which never change.

**Tech Stack:**

- Python 3.14.0 and uv 0.12.15.
- New, only in `earnings-ingestion`'s `browser-capture` extra:
  - Selenium 4.49.0;
  - websocket-client 1.9.2, which carries CDP to the page, because Selenium 4.49.0
    bundles CDP bindings only up to Chrome 153.

  `uv.lock` grows from 140 to 151 packages.
- Chrome for Testing and chromedriver 154.0.8037.57 for mac-arm64. They are pinned in
  a committed manifest and installed outside the repository.
- Already locked: lxml 6.1.3, pydantic 2.13.5, httpx (the setup command's download),
  typer 0.27.2 (the application's CLI), pytest 9.1.1 and Ruff 0.16.8.
- From the standard library: `ast`, `difflib`, `html.parser`, `zipfile`,
  `subprocess`, `tomllib`, `fractions`.

## The spec this plan implements

`specs/structure-aware-canonicalization.md`, approved 2026-09-25, is the stage spec.
It governs this plan, and it has not changed since plan 4 (PA-1).

- **Two plans (SC1).** This plan is §Plan B, the browser diagnostic path. Plan A, the
  canonicalizer, shipped as plan 4 (`specs/plans/completed/4-structure-aware-canonicalization-plan-a.md`,
  merged to `main` at `0938b66`). Approval covered plan B too, so this plan skipped
  brainstorming, although the roadmap's Stage 3 ROUTING line says brainstorming.
- **Sections this plan implements:**
  - §Plan B: §Principle (SC14), §Dependencies and binaries (B3, B8), §Renderer and
    capture (B1, B2), §Capture policy `isolated/1` (B7), §Checks, §Layout extractor
    `layout-1` and alignment (B5, SC13), §Pre-registered comparison, §Promotion
    decision, §Import boundaries, and §Verify at plan time;
  - plan B's leg of §R3.5 fidelity check, which makes the report final;
  - §Exit criteria, plan B's list, items 1–10.
- **The browser spec.** `specs/browser-rendering-integration.md` supplies what the
  Stage 3 spec cites it for:
  - the `RenderedCapture` field list;
  - the eight calibration kinds;
  - §Security and isolation;
  - §Reproducibility and failure handling;
  - the diagnostic-first promotion rule and its three outcomes.
- **Also closed here.** Plan 4's inputs to plan B, each settled by a task or by ADR
  0002:
  - plan 4's Handoffs "To plan B";
  - the review gate's open findings, in `docs/verification/walker-1.md` ("The review
    gate");
  - the deferred items "Check import boundaries statically as well"
    (`3-core-evidence-spine`) and "Settle the review gate's open page-artifact and
    mask findings" (`4-structure-aware-canonicalization-plan-a`).
- **What approval fixed (§Gates, SC14).** Plan B never changes canonical text.
  - `walker-1`, C1–C5, N1, L1, S1, M1–M5, and the eight canonical fixtures stay as
    plan 4 committed them.
  - Any change to canonical text or elements is a new policy, `walker-2`, built only
    if ADR 0002 promotes (Task 14).
  - The spec names the targeted classes, the metrics, the configurations, the
    repair and regression rule, and the fallback's two triggers. This plan fixes only
    what the spec leaves to it, and says so in each decision below.

## Global Constraints

Every task's requirements include these.

**Locators:**

- `A §n` is `AGENTS.md` at line `n`.
- `Rn` and `Vn` are `specs/evidence-linked-theme-extraction.md`.
- `SCn` are the Stage 3 spec's decisions, and `§Name` is one of its sections.
- `Bn` are the browser spec's decisions (`specs/browser-rendering-integration.md`).
- `W0`–`W16` are the walker's rules in `expirements/parser-fidelity/walker-rules.md`.
  `C1`–`C5`, `N1`, `L1`, `S1` and `M1`–`M5` are the Stage 3 spec's rules.
- `L1`–`L17` in `layout-1`'s context are its rules, listed in
  `layout/blocks.py`'s docstring (PB-9). The canonical-text layout rule is always
  written "the spec's L1".
- `PA-n` are plan 4's decisions, and `PB-n` are this plan's, listed below.

**Plan B never changes canonical text (SC14).** `walker-1` and its eight fixtures are
frozen:

- `tests/integration/test_canonical_golden.py` must pass after every task;
- nothing in this plan edits a module that `canonicalize` runs;
- a changed element or text is `walker-2`, in its own package and fixtures (Task 14).

**Purity.** The parts that compute are pure: `LayoutExtractor.extract` and `map_onto`,
`fired`, `canonicalize_promoted`, and the serializers. Each has no network client,
does no file I/O, changes no global state, and is deterministic. Only the adapter, the
store, and the setup command touch processes, files, or the network.

**Imports (§Import boundaries, B3).**

- Only `earnings_ingestion.browser.selenium_capture` imports a browser library:
  Selenium, websocket-client (`websocket`), Playwright, or pyppeteer.
- `import earnings_ingestion`, and every other module of the package, loads none of
  them.
- Packages import nothing under `expirements/`. Harness scripts may import
  `earnings_ingestion`; no package imports the harness.
- `earnings-ingestion` and `earnings-themes` never import each other. The
  application may import both.

**The span invariant (R6.1, SC13).** Every element span satisfies
`0 <= start < end <= len(canonical_text)`. The canonical hash is SHA-256 over the
canonical text's UTF-8 bytes. Offsets are code points, half-open.

- `layout-1` builds every span by matching canonical text. It never takes one from a
  DOM offset, so no UTF-16 offset is converted.
- A block that matches nowhere, or ambiguously, is an `AlignmentFailure`. It is never
  placed at a first match or by a score.

**Versions.**

| Name | Value | Where |
| --- | --- | --- |
| Capture policy | `isolated`, version `1` | `browser/policy.py` (Task 2) |
| Layout-metadata script | `layout-metadata-1` | `browser/metadata.py` (Task 2) |
| Chrome for Testing and chromedriver | `154.0.8037.57`, `mac-arm64` | `browser/chrome-for-testing.toml` (Task 4) |
| Selenium; websocket-client | `4.49.0`; `1.9.2` | the `browser-capture` extra and `uv.lock` (Task 5) |
| Layout extractor | `layout-1` | `layout/blocks.py` (Task 6) |
| Mapping policy | `anchored-1` | `layout/align.py` (Task 7) |
| Promoted policy, only on promotion | `walker-2` | `promoted/pipeline.py` (Task 14) |
| Ingestion records | `1`, unchanged | `INGESTION_SCHEMA_VERSION` (PB-20) |
| Canonicalization, masks, core schema | `walker-1`, `boilerplate/1`, `2`, all unchanged | plan 4 |

A change to capture policy, metadata script, extractor, or mapping policy after the
pre-registration is an amendment under PB-13, never a silent edit.

**Offline and no models.**

- Default tests make no network call and no billable call, need no credentials, and
  start no browser.
- Browser tests carry the `browser` marker, run only with `-m browser`, and skip
  visibly when the extra or the pinned binaries are absent.
- No test in this plan carries `live`, and no step calls a model.

**Downloads.** Apart from uv fetching the extra's eleven packages from PyPI in Task 5,
exactly one step downloads anything: Task 5, Step 7, which runs
`earnings-pipeline browser setup`.

- **Permission.** It runs only after the user explicitly permits that download in
  chat. The request names both archives with their source and size: `chrome-mac-arm64.zip` (191,429,663 bytes) and
  `chromedriver-mac-arm64.zip` (9,302,980 bytes), from
  `https://storage.googleapis.com/chrome-for-testing-public/154.0.8037.57/mac-arm64/`.
- **Reuse.** Once installed, the binaries are reused.
- **Missing binaries.** If they are missing at any later step, stop and ask. Never
  download from another step, and never let Selenium Manager fetch a driver.

**Dependencies.**

- The only new dependencies are the extra's two pins, and `uv.lock` changes only in
  Task 5, from 140 to 151 packages.
- The application gains a `[project.scripts]` entry and no dependency: typer is
  already declared.
- The root `pyproject.toml` stays a virtual workspace root with no `[project]` table.
  Task 1 adds only a marker and the default deselection.

**The pre-registration (PB-13).** Until Task 10 commits
`expirements/parser-fidelity/layout1-preregistered.toml`, no step may capture a
release fixture or run `layout-1` on one. No step may read a release fixture's
computed styles or rendered layout either. Development uses only:

- the three development releases in `data/raw/devset/`;
- synthetic pages;
- the contract release of Task 9.

After the freeze, a frozen file changes only through `preregister.py amend`, for a
`crash` or `invalid-elements` fix, and every such change is disclosed.

**Do not touch:**

- Stage 1's frozen files, gold, fixtures, V2 record, and ADR 0001:
  - every file `expirements/parser-fidelity/FROZEN.toml` lists;
  - `tests/fixtures/releases/` and its `gold.toml` files;
  - `docs/verification/V2-parser-fidelity.md`;
  - `docs/adr/0001-use-the-bespoke-lxml-walker-as-the-base-parser-for-release-canonicalization.md`.

  `freeze.py verify` must print `freeze verified` after every task that touches the
  harness.
- `walker-1`:
  - `packages/earnings-ingestion/src/earnings_ingestion/canonical/`, every module
    except `fidelity.py` (Task 12 adds to it) and the new `triggers.py` (Task 8);
  - `tests/fixtures/canonical/`;
  - `tests/integration/test_canonical_golden.py` and
    `regenerate_canonical_fixtures.py`;
  - `docs/verification/walker-1.md`, apart from the one spec path that Completion
    re-points, and `walker-1-report.md`;
  - `expirements/parser-fidelity/port_walker.py` and `walker1_report.py`.
- `AGENTS.md`, except line 206, which Task 1 edits in place without changing the line
  count: other files cite `AGENTS.md` by line number (`CLAUDE.md` §Gotchas).
- `specs/structure-aware-canonicalization.md`, except the Rollout stamp that
  Completion appends. Findings that contradict the spec go in the verification
  records.
- `.gitignore`: no edit, and its credentials block stays last. `data/*` already
  ignores the capture store under `data/runs/`.
- `.python-version`, which pins 3.14.0: the canonical fixtures record the Python
  version (PA-14).

**Staging discipline.** `git add` only the paths a task names, never `git add -A` or
`git add .`. Before each commit, `git status --short` must list the task's files and
nothing else of this plan's: a later task's file never enters an earlier commit.

These artifacts are generated, and each is committed only in its own task:

| Artifact | Task |
| --- | --- |
| `tests/fixtures/browser/contract-release.capture.json` | 9 |
| `expirements/parser-fidelity/layout1-units.toml` | 10 |
| `expirements/parser-fidelity/layout1-preregistered.toml`, in a commit of its own | 10 |
| The eight `tests/fixtures/browser/<fixture>.capture.json` and `docs/verification/browser-calibration.md` | 11 |
| `docs/verification/R3.5-text-fidelity.md`, regenerated | 12 |
| `docs/verification/layout-1-comparison.md` | 13 |
| `tests/fixtures/walker-2/*.json`, only on promotion | 14 |

The user may commit on this branch while the plan runs. Run `git log --oneline -3`
before each commit, and never rewrite a commit you did not make.

**Unicode escapes.** Every new or replaced Python file in this plan is ASCII, except
`§` in citations such as `A §173`.

- Tests build non-ASCII inputs from code points with `chr(0x...)`, and regular
  expressions use `\N{...}` names. No editor or tool channel can then normalize an
  input, and no file carries a `\u` escape that a tool channel might decode on the
  way to disk.
- Each task that writes Python runs the escape check below. It prints
  `escapes intact`, or else the name of each file holding another non-ASCII
  character.

**Writing files from this plan.** Every code block that holds a whole file, or text to
append, follows a line of one of three forms:

- ``Create `<path>`:``;
- ``Replace `<path>` with:``;
- ``Append to `<path>`:``.

Extract each such file with the helper below rather than retyping it. Retyping about
9,000 lines invites silent slips, and a tool channel that decodes an escape would do
it again on a retry. The Preconditions save the two helpers once, as
`/tmp/plan5-extract.py` and `/tmp/plan5-escapes.py`. If `/tmp` has been cleared, save
them again from here.

`/tmp/plan5-extract.py`:

````python
"""Extract one file block from plan 5; run from the repository root.

usage: python3 /tmp/plan5-extract.py <path> [block number, default 1]
"""

import sys
from pathlib import Path

PLAN = Path("specs/plans/5-structure-aware-canonicalization.md")
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

`/tmp/plan5-escapes.py`:

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

A step that says **extract** a path runs `python3 /tmp/plan5-extract.py <path>`, which
prints `extracted <path>: <n> lines`. The block number is `1` unless the step names
another: a path written twice takes `2` the second time. If the escape check names a
file, extract that file again and rerun the check.

**Lint.** `uv run --locked ruff check .` and `uv run --locked ruff format --check .`
pass after every task, and the code below already passes both. The Expected
`N files already formatted` counts were measured on a clean checkout: 116 before
Task 1, growing with each task's new Python files. A different count with no
`Would reformat` line comes from local untracked Python files and is not a failure.

**Test imports.** Ruff sorts `earnings_core` and `earnings_ingestion` as third-party
imports in test files, in one block with `pytest`, so keep the imports as written.
Inside `earnings_ingestion` they are first-party.

**Public repository.** `origin` (https://github.com/lowmason/earnings-themes) is
public, so everything committed is published.

- The browser fixtures hold rendered text and layout metadata derived from exhibits
  already committed under the `sec-edgar` register entry, with the same
  redistribution basis (PB-7).
- Screenshots and the capture store stay under the gitignored `data/runs/`.
- The user's `rendered.txt` copies stay under `data/runs/parser-fidelity/gold-drafts/`
  and are never committed.

**Commit attribution.** End each commit message with the attribution line your
session's instructions specify. The commit blocks below omit it deliberately: the
right line names the model actually executing the work.

**Commands.** These recur:

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
uv run --locked --all-packages --extra browser-capture pytest packages apps tests -m browser -rs -q
```

- The first is the **default suite**. From Task 1 on it is the documented command.
  Before Task 1 it is `-m "not live"`.
- The second is the **harness suite**.
- The third is **lint**.
- The fifth is the **browser checks**. `-rs` prints each skip's reason, which is how
  the checks skip visibly.

`uv run --extra browser-capture` leaves the extra installed in `.venv`. That is
harmless: the default suite deselects every browser test, and nothing but the
adapter imports Selenium. `uv sync --locked --all-packages` removes the extra again.

## Plan decisions

The spec leaves these choices open, so the plan makes them. The user can overturn any
of them before execution. The planning session of 2026-09-26 put six to the user,
and PB-2, PB-7, PB-9 and PB-14 record the answers. The code records each decision
where it applies. None adds, removes, or retunes a spec rule: where a rule needed a
reading, the reading is stated.

**PB-1 — The file name retires the spec.** This file carries the spec's own name,
`5-structure-aware-canonicalization.md`. Plan 4 took a `-plan-a` suffix so that its
completion would not retire the spec (PA-1). This plan is the spec's last, so
Completion retires the plan and the spec in one commit.

**PB-2 — The plan-time checks passed (§Verify at plan time).** All three ran on
2026-09-26, in a scratch tree, against the pinned build.

1. **innerText and layout metadata with document JavaScript disabled: passed.**
   CDP's `Emulation.setScriptExecutionDisabled` stops the page's own scripts, inline
   and external. WebDriver's `execute_script`, which reads `document.body.innerText`
   and runs the layout-metadata script, still runs.
2. **Request blocking covers every scheme a saved page can reach: passed, with the
   reading the user accepted on 2026-09-26.**
   - **What blocks.** CDP Fetch interception (`Fetch.enable`, pattern `*`, request
     stage) pauses every request the page makes. The adapter fails every request but
     the saved file itself, and records it. That covers:
     - stylesheets, fonts and images;
     - frame, `<object>` and `<embed>` documents;
     - a meta refresh.
   - **What does not.** `Network.setBlockedURLs`, the obvious alternative, failed
     the check: frame, object and embed documents and a meta refresh reached a local
     server.
   - **WebSockets.** No CDP domain sees a WebSocket handshake. With document
     JavaScript disabled, a saved page cannot open one.
   - **Defense in depth.** `isolated/1` adds the following, and with them even a
     JavaScript-enabled WebSocket and a speculative preconnect made no connection:
     - it sends every non-loopback connection to a dead proxy
       (`--proxy-server=http://127.0.0.1:9`, `--proxy-bypass-list=<-loopback>`);
     - it resolves no host name (`--host-resolver-rules=MAP * ~NOTFOUND`);
     - it turns network prediction off (`net.network_prediction_options: 2`).
   - **Other schemes.** The check's page also asked for an `ftp:` image, and for a
     `file:` image and frame outside the saved file. Fetch interception paused and
     failed each one, and no local file's text reached the capture.
3. **The pinned build exists: passed.** Chrome for Testing 154.0.8037.57, the Stable
   channel's version on 2026-09-26, is published for mac-arm64, and PB-3 records
   both archives. The user's own Chrome, which rendered the gold and the
   `rendered.txt` copies, was 154.0.8037.58: the same build line, one patch later.

**PB-3 — The pin, the manifest, and the install (§Dependencies and binaries; B3,
B8).**

- **The manifest.** `packages/earnings-ingestion/src/earnings_ingestion/browser/chrome-for-testing.toml`
  is package data beside `install.py`, which reads it at run time. For each archive
  it records the version, platform, URL, size, SHA-256, and executable path.
- **The setup command.** `earnings-pipeline browser setup` is the only code that
  downloads (PB-22).
  - It checks each archive's size and hash before extracting it.
  - Extraction keeps symlinks and executable bits. The browser archive holds five
    symlinks, and `zipfile`'s own extraction breaks the app bundle.
  - Extraction refuses an absolute path, a `..` segment, or a symlink that leaves the
    tree.
  - It checks that both executables report the pinned version, then moves the tree
    into place in one rename, so a half-installed tree never looks installed.
- **The cache.** `~/Library/Caches/earnings-themes/chrome-for-testing/<version>/<platform>/`,
  or `$EARNINGS_BROWSER_CACHE` in its place. Either way it is outside the repository.
- **No automatic download.** A capture only calls `installed()`, which never
  downloads. The adapter passes chromedriver's path explicitly, so Selenium Manager
  never runs; a browser test points `SE_MANAGER_PATH` at a missing file to prove it.
- **Missing binaries.** Without them a capture is `unavailable` with reason
  `browser_unavailable`.
- **Other platforms.** A platform with no pin gets `None` from `load_pin()` and the
  same `unavailable` capture.

**PB-4 — What the network guard proves (§Checks, "Network guard").** The spec's
guard page requests an external image, stylesheet and script, and adds an inline
script that would rewrite text. The guard test also adds a frame.

- **The script.** With document JavaScript disabled, Chrome never requests the
  external script at all.
- **What the test asserts.**
  - The stylesheet, the image and the frame are each blocked and recorded.
  - A local counting server stands in for the network and accepts no connection.
  - The inline script's text never appears in the capture.
- **Two policies.** The test runs under `isolated/1` and again under a copy without
  the proxy and resolver flags. That proves Fetch interception blocks on its own.

**PB-5 — What makes a capture partial (§Capture policy).**

- **Partial.** A blocked stylesheet or font, the policy's required types, makes a
  capture `partial` with reason `blocked_required_resource`. So does a blocked
  subframe document, because a frame's content is part of what a reader sees.
- **Not partial.** A blocked image is recorded and never downgrades a capture.
- **Never empty.** A failure is `failed` or `unavailable`, never an empty successful
  capture.

**PB-6 — One browser per capture, and cleanup (§Capture policy, "Limits").**

- **A batch is one capture.** chromedriver starts in a process group of its own,
  which Chrome and all its helpers join. After each capture the whole group is
  killed, even when shutdown hangs. A browser test lists processes afterwards and
  finds none.
- **Bounds.** Startup, navigation, capture, and shutdown are each bounded.
- **The interceptor.** It outlives the browser, because Chrome would let a paused
  request through once its CDP client had gone.
- **One limitation.** Chrome's crash handler keeps its database under
  `~/Library/Application Support/Google/Chrome for Testing/Crashpad`, outside the
  temporary profile. It holds crash reports only, and the handler exits with the
  browser.

**PB-7 — What is committed (the user's decision, 2026-09-26).**

- **Committed.** The eight release captures and the contract capture, under
  `tests/fixtures/browser/`, in the capture-fixture format: every `RenderedCapture`
  field, and no screenshot. They hold rendered text and layout metadata derived from
  exhibits already committed under the `sec-edgar` register entry.
- **Never committed.** Screenshots and the store stay under the gitignored
  `data/runs/browser-capture/`, and the user's `rendered.txt` copies stay under
  `data/runs/parser-fidelity/gold-drafts/`.
- **Why commit.** Committed captures let the comparison, the two-parser contract, and
  R3.5's leg 2 rerun offline, with no browser. The default suite needs exactly that.

**PB-8 — The capture store (§Renderer and capture, "Storage").**

- **Usable captures.** `CaptureStore` keeps a `completed` or `partial` capture at
  `captures/<cache key>.json` and reuses it for that key.
- **Failed captures.** A failed or unavailable capture is kept for the record under
  `failures/<cache key>/<time>.json`, and never reused.
- **Screenshots** are stored by content hash.
- **Writes.** Every write goes to a temporary file and is hard-linked into place.
  That fails rather than replace a file: the same bytes again are a no-op, and
  different bytes raise `FileExistsError`.

**PB-9 — layout-1 is an independent reader (§Layout extractor; the user's decisions,
2026-09-26).** layout-1 reads only the capture's layout metadata, never
`walker-1`'s elements.

- **Its rules.** Each L-rule is the walker rule of the same number with a rendered
  signal in place of a tag or an inline style. `layout/blocks.py`'s docstring lists
  them.
  - L1 hides what the capture did not render.
  - L6–L16 reuse the walker's `classify` and its marker-table, data-table,
    header-row and layout-table tests over the rendered runs and tables.
- **Heading (the user's choice).** A block of at most 12 words is a heading when
  every visible character is bold or underlined. It is also a heading when every
  visible non-space character is larger than the body size, which is the size that
  carries the most visible characters. Centring and capitals do not count.
- **L17.** In a data table, a row whose only non-empty cell spans every column and
  holds a letter leaves the table as a block of its own, typed by L8–L12. This is the
  spec's "table row whose single non-empty cell spans the table and holds prose".
- **C1–C5 (the user's choice).** layout-1's blocks pass through the same C1–C5 as
  `walker-1`'s, so the comparison isolates the reader, not the compensation.
- **Uncovered text.** Canonical text that no element covers becomes `other`, one
  element per line, with source type `layout:uncovered`. This is the spec's "text
  with no visible counterpart".
- **What layout-1 does not emit.** No sentences and no list containers. Nothing the
  comparison scores reads them; `walker-2` adds S1 sentences itself (PB-19).
- **Source types** publish the mapping (plan 4's Handoffs, "What it reuses"):
  `layout:<tag>`, `layout:marker-table`, `layout:table`, `layout:row`, `layout:cell`,
  and `layout:uncovered`.
- **Text origin.** Browser text is `native`.

**PB-10 — Mapping policy `anchored-1` (§Layout extractor, "Mapping"; SC13).**
`layout/align.py`'s docstring states the policy.

- **The space.** Matching runs in a collapsed-whitespace copy of the canonical text
  that remembers each character's offset. The map is deterministic and reversible.
- **Occurrences** are exact and token-bounded.
- **Anchors.** A unit with exactly one occurrence is an anchor.
- **Order.** Placements that overlap are refused together. A unit is kept only if
  it lies on every longest in-order chain of placements, so one misplaced unit costs
  only itself.
- **Neighbours.** Between kept units, a text whose units there number exactly its
  occurrences there maps in order. Rounds repeat until nothing more maps.
- **Failures.** No occurrence is `locator_not_found`. Several that the neighbours
  never settle, or a refused place, is `ambiguous_occurrence`. Nothing is placed at
  a first match or by a score.
- **Development.** The policy was developed on the three development releases in
  `data/raw/devset/` and synthetic cases, never on a fixture. Over 1,292 units there,
  it placed every unit and failed none.

**PB-11 — The import scan (§Import boundaries).**

- **The scan.** `tests/contracts/test_import_scan.py` reads every module under each
  member's `src/` with `ast`, including imports inside functions.
- **What it refuses.**
  - An import that breaks `CLAUDE.md`'s dependency table.
  - A browser import anywhere but `earnings_ingestion.browser.selenium_capture`.
    websocket-client (`websocket`) counts as a browser library because it carries
    CDP.
- **The runtime checks stay.** Importing each non-adapter module of the package loads
  no browser library.

**PB-12 — The targeted units, and when one is lost (§Pre-registered comparison).**
`expirements/parser-fidelity/layout1_units.py` derives the units from the gold and
the frozen Stage 1 walker's output, never from a capture, and writes
`layout1-units.toml`.

| Class | Unit | Count |
| --- | --- | --- |
| 1. `styled_headings` | A gold heading that the frozen walker found and typed `paragraph`: V2's 23 | 23 |
| 2. `prose_in_tables` | A gold text block that the frozen walker found inside a data table: V2's 49 merged blocks, less the 11 tables among them (19 headings, 13 paragraphs, 6 footnotes) | 38 |
| 3. `stylesheet_hidden` | Content a stylesheet hides | 0 |

- **Class 1 under walker-1.** Of the 23, 13 are still `paragraph` in `walker-1`. The
  other 10 are `page_artifact` through C5: Becton Dickinson's nine "BECTON DICKINSON
  AND COMPANY" statement titles, and National Health Investors' headline, block
  b004. The review gate's first findings are therefore class 1 units (PB-21).
- **Class 3.** No fixture carries a `<style>` element or a stylesheet link, so the
  class is empty. The script stops on any fixture that does, because this plan
  pre-registers no definition for one. Becton Dickinson's 1,394 hidden elements use
  inline `display: none`, which `walker-1` already handles.
- **A class 1 unit is lost** when it is missed or the frozen scorer counts it in
  `header_lost`.
- **A class 2 unit is lost** when it is missed or any element it matches is a
  `table`.
- **Repair (the spec's rule).** A class is repaired when a configuration loses
  strictly fewer of its units than `walker-1`.

**PB-13 — The freeze, its order, and what the planner saw (§Pre-registered
comparison).**

- **Order.**
  1. The units (Task 10).
  2. The code that decides the numbers: the capture adapter, its metadata script,
     its policy and records, and the fixture format; layout-1 and every canonical
     module it runs; the triggers; the units and their loader; the comparison; and
     the frozen scorer it calls.
  3. The freeze record: `preregister.py record` hashes those 23 files into
     `layout1-preregistered.toml`, committed on its own.
  4. The release captures (Task 11). The capture script refuses to run until
     `preregister.py verify` passes.
  5. The comparison (Task 13).
- **Amendments.** After the freeze, a frozen file changes only to fix a `crash`, or
  an element set `validate_elements` refuses (`invalid-elements`), on a fixture
  capture. `preregister.py amend` records each change with its reason. A change
  never alters a type decision, a mapping rule, a unit, or a metric. Every amendment
  makes the numbers post-hoc, and the verification record says so.
- **What the planner saw before the freeze.** Disclosed here, and again in
  `docs/verification/layout-1.md`:
  - **The development releases.** The three in `data/raw/devset/` were captured, and
    layout-1 was developed and aligned on them.
  - **The units** come from the gold and the frozen walker's output (PB-12).
  - **Structural greps of the fixture sources.** No `<style>` element or stylesheet
    link, no `class` attribute, no `<th>`, and no bold `font` shorthand. Becton
    Dickinson has 1,394 inline `display: none`.
  - **One text load.** A plan-time determinism check loaded National Health
    Investors' `innerText` twice: 20,731 characters from windows-1252 bytes, with the
    same hash both times. No layout was read, and layout-1 did not run.
  - **The review gate's finding texts** were looked up in the committed `walker-1`
    fixtures, to set PB-21's probes:
    - NHI's headline: `page_artifact` ×5.
    - Becton Dickinson's statement titles: `page_artifact` ×9.
    - Becton Dickinson's "1Represents a non-GAAP…" footnotes: `paragraph` ×3.
    - "Ball Corp - 2/3/4": `paragraph`.
    - FMC's "Page 2–6/ FMC Corporation Announces Fourth Quarter Results": `heading`
      ×5.
    - The end marks:
      - "# # #" is a paragraph in Southwestern Energy, Ball and FMC;
      - "***" is a footnote in Becton Dickinson and Southwest Airlines;
      - FMC's row of asterisks is a footnote;
      - Pharmacyclics' "###" is a paragraph.
  - **The triggers,** computed on `walker-1`'s committed output, with no capture.
    `prose_row` fires on Southwest Airlines and National Health Investors, both
    table-heavy. `no_heading` fires on none. The fallback therefore switches exactly
    those two documents.
  - **The rendered copies.** It is known that the eight exist, are UTF-8, and put
    bullets on their own lines, and that Union Bankshares' copy has no tab.

**PB-14 — The comparison's rules (§Pre-registered comparison; the user's decision,
2026-09-26).** `expirements/parser-fidelity/layout1_report.py` applies them, and
Task 10 unit-tests them on synthetic scores.

- **Configurations.**
  1. `walker-1`, with C1–C5.
  2. `layout-1`, for every document.
  3. The fallback: layout-1 where `walker-1`'s output fires a trigger, and `walker-1`
     elsewhere.

  Each is projected to Stage 1's dump format by `walker1_report.project` and scored
  by the frozen `score.py`.
- **Metrics.** For each of the four fixture classes: block coverage, reading order,
  heading loss, footnote merging, table-header retention, cell association, altered
  anchors, and alignment failures.
  - **Altered anchors** count over the coverage denominator.
  - **Alignment failures (the user's decision).** They count as a metric: layout-1's
    failures over its units in the class. `walker-1` scores 0 over the same
    denominator, and the fallback counts failures only in the documents it switches.
    More than one failure in a class is a regression, which blocks promotion.
- **Exactness.** Every comparison is an exact count or an exact `Fraction`.
  `select_parser.py` is not reused, so the deferred item "Compare exactly if the
  selection rule is reused" stays open.
- **Regression (the spec's rule, with its n read).** A metric is a regression when
  it is worse than `walker-1`'s by more than 1/n in a fixture class. Here n is
  `walker-1`'s denominator for that metric in that class.
  - Coverage and cell association are better higher; the rest are better lower.
  - A denominator that is zero on one side only is "not comparable", which counts
    as a regression.
- **Promotion eligibility.** A configuration may be promoted only when it repairs at
  least one targeted class with no regression. The report says which outcomes the
  rule allows. Outcome 1 is always allowed.
- **Probes.** Beside the pre-registered metrics, the report lists the element types
  each configuration gives each review-gate finding's text (PB-21). The probes are
  reporting only, and no rule reads them.

**PB-15 — The calibration classifier (§Checks, "Calibration").**
`expirements/parser-fidelity/calibrate.py` compares each calibrated capture's
`innerText` with the user's copy. It covers Union Bankshares (narrative-only),
National Health Investors (table-bearing) and Ball (malformed layout), and aligns
the tokens with `difflib`. Each difference goes to the first of the browser spec's
eight kinds that fits:

| Kind | When |
| --- | --- |
| Table-cell separation | A differing separator between aligned tokens, or at the text's edges, where a side holds a tab |
| Whitespace | The same, with no tab |
| Reading order | One-sided hunks whose tokens reappear as a one-sided hunk on the other side (both are counted) |
| Bullets | Bullet glyphs only |
| CSS text transformation | Tokens that differ only in case |
| Image alternative text | A one-sided hunk equal to one of the source's `alt` texts |
| Hidden content | A one-sided hunk inside the source's hidden text: `display: none`, `visibility: hidden`, or the `hidden` attribute, read by `html.parser` |
| Visible characters | Anything else |

The report counts every difference and shows up to five per kind and fixture. The
copies are calibration observations, not gold, and no gold changes.

**PB-16 — R3.5's second leg (§R3.5 fidelity check).**

- **The diff.** `token_hunks` is a whitespace-insensitive token diff in comparison
  space (NFC, collapsed whitespace), with `difflib`'s junk heuristic off.
- **The classes.** `hunk_category` classes each differing hunk into the six
  categories or `other`. It takes the first test the hunk passes: Unicode, scale,
  superscripts, footnotes, numeric signs, table headings. Unicode and scale come
  first because they are the most specific. A raised marker glued to a number is
  superscripts before it is numeric signs.
- **Both references.** The leg compares the canonical text with each committed
  capture's `innerText` and with each local copy. Every hunk is counted and listed.
- **The copies go last.** They are local, so the section built from them is the
  report's last. `test_r35_report_current.py` always checks the report up to that
  section, and checks the whole report only where the eight copies exist.
- **Final.** With both legs the report is final (exit criterion 8).

**PB-17 — The `browser` marker and the documented command (§Checks, "Markers").**

- **The default.** The root pytest configuration registers `browser` and deselects
  it beside `live`: `-m "not live and not browser"`.
- **The documented command.** pytest keeps the last `-m`, so every documented
  default command changes to `-m "not live and not browser"`:
  - `CLAUDE.md`, both commands;
  - `README.md`;
  - `AGENTS.md` line 206, edited in place with the same line count.

  The roadmap's Stage 2 Exit line quotes the old command as history, so it stays.
- **Skipping.** Every browser test also skips visibly without the extra
  (`pytest.importorskip`) or the pinned binaries (`skipif`, naming the setup
  command).

**PB-18 — ADR 0002's gate (§Promotion decision).**

- **A hard stop.** Task 13 ends at a hard stop, run by the controller with the user
  and never in a subagent.
- **The choice.** The user reads `docs/verification/layout-1-comparison.md` and
  chooses one outcome among those its Verdict says the rule allows. Outcome 1 is
  always among them, and choosing it is never a failure of the plan.
- **What the ADR records.** The outcome, the activation policy, the versions, the
  measured benefit, the regressions, and the consequence for the canonicalization
  version. It also records the cost of promotion: a capture becomes an input to
  canonicalization for every document the new version covers, Stage 5's and Stage
  15's releases included, on the pinned platform and fonts.
- **How a capture arrives.** Under promotion, the pipeline captures each document
  once, through the store, and passes the capture to `canonicalize_promoted` as an
  argument (PB-19).

**PB-19 — walker-2 (§Promotion decision; SC8, SC14), built only on outcome 2 or 3.**
`earnings_ingestion.promoted` holds it.

- **The entry point.** `canonicalize_promoted(raw, capture, *, source_document_id, media_type, activation=ACTIVATION)`
  first runs `walker-1`. It then builds a new `CanonicalDocument` from the same text
  under `walker-2`, so the hash is unchanged and only `doc_id` changes.
- **Every document needs a capture.** It needs a usable capture of the same bytes,
  whether or not it switches, because the spec makes the capture an input for every
  document the version covers. Without one it returns a `PromotionFailure`, and it
  never falls back to `walker-1` under `walker-2`'s name.
- **One stream, never a mix.**
  - It uses layout-1's elements, with S1 sentences added, where it switches:
    - under `Activation.FALLBACK` (outcome 2), when a trigger fires;
    - under `EVERY_DOCUMENT` (outcome 3), always.
  - It uses `walker-1`'s elements, re-keyed, where it does not switch.
- **Alignment failures** keep the document. The unit's text is `other`, never
  narrative, and the manifest records the failure and the limitation. A switched
  document has no list containers, which the manifest records too.
- **Masks** are `boilerplate/1`, recomputed over the new elements.
- **One name for both outcomes.** The version is `walker-2` under either, and the
  manifest's `activation` tells them apart.
- **Fixtures.** Its eight fixtures go to `tests/fixtures/walker-2/`, and
  `walker-1`'s are never rewritten.

**PB-20 — New records join ingestion schema 1.** `walker-1`'s committed fixtures pin
every manifest byte, `schema_version` included. A schema bump, or a new field even
with a default, would fail `walker-1`'s golden test. The capture, layout and
`walker-2` records are therefore new record types at ingestion schema version 1, and
the data dictionary documents each. `walker-2` has its own manifest record, which
embeds `walker-1`'s manifest.

**PB-21 — Each review-gate finding gets a disposition.** The deferred item "Settle
the review gate's open page-artifact and mask findings" closes when plan B's
verification record or ADR 0002 gives each finding a disposition: fixed under a new
policy version, a plan B target, or a recorded limitation. The report's probes give
the facts, and Task 15 records the disposition for each outcome:

| Finding | Plan B's handle | Disposition on outcome 1 | On outcome 2 or 3 |
| --- | --- | --- | --- |
| NHI's headline, `page_artifact` via C5 | Class 1 unit b004; probe | Limitation of `walker-1`, excluded from narrative eligibility | Fixed under `walker-2` if walker-2 types it `heading` in the switched document; otherwise a limitation of both |
| Becton Dickinson's statement titles | Class 1 units; probe | Limitation | As NHI's headline, for the documents walker-2 switches |
| End marks ("# # #", "***", "###", FMC's asterisks) | Probe | Limitation: no rule types them, and C5 is not amended | Limitation, unless the probe shows walker-2 types them `page_artifact` |
| Numbered running heads (Ball, FMC) | Probe | Limitation | Limitation, unless the probe shows otherwise |
| Becton Dickinson's non-GAAP footnotes, unmasked | Probe (their types) | Limitation of `boilerplate/1`: a mask change needs `boilerplate/2`, which no stage plans | The same |
| Southwestern Energy's forward-looking continuation, unmasked | None: a mask finding | Limitation of `boilerplate/1`; at the gate the user declined a rule fitted to one instance | The same |

**PB-22 — The setup command lives in the application.** `CLAUDE.md` puts CLI entry
points in `apps/earnings-pipeline`. The command is
`uv run --locked --all-packages earnings-pipeline browser setup`, from
`earnings_pipeline.cli`, registered by `[project.scripts]`. typer is already a
declared dependency. The command adds no domain logic: it calls `load_pin`,
`default_cache`, `install` and `download` from `earnings_ingestion.browser.install`.

**PB-23 — Execute in the main checkout.** `data/` is gitignored, and this plan needs
local data that a worktree lacks:

- the three development releases in `data/raw/devset/`, which the harness suite runs;
- the user's eight `rendered.txt` copies, which calibration and R3.5's leg 2 need.

Work on `stage-3-browser-diagnostic-path` in `/Users/lowell/Projects/earnings-themes`.

**PB-24 — The metadata script is part of the cache key.** The key hashes the raw
bytes, the policy, the metadata version, the metadata script's own SHA-256, the render
configuration, the browser, driver and Selenium versions, and the platform. It never
hashes a timestamp. An edited script therefore never reuses a stored capture, even
if someone forgets to bump `METADATA_VERSION`.

**PB-25 — The public API.** `earnings_ingestion.browser` exports:

- `ISOLATED_1` and `CapturePolicy`;
- the capture records;
- `BrowserRenderer`, `CaptureEnvironment` and `FakeRenderer`;
- `CaptureStore` and `capture_once`.

`earnings_ingestion.layout` exports `LayoutExtractor`, its records, and its two
version names. Stage 10 receives `BrowserRenderer` for V5's target-browser checks
and the screenshot fallback. `SeleniumRenderer` is imported from its own module, so
that `import earnings_ingestion.browser` never loads Selenium.

## Requirement map

| Requirement | What closes it | Task |
| --- | --- | --- |
| §Principle (SC14) | No task edits `walker-1`; the golden test after every task; `walker-2` keeps the text and hash | all; 14 |
| §Dependencies and binaries (B3, B8) | The pin manifest, `install.py`, `earnings-pipeline browser setup`; the extra and `uv.lock` | 4, 5 |
| §Renderer and capture (B1, B2) | `records.py`, `metadata.py`, `renderer.py` (`BrowserRenderer`, `FakeRenderer`, the cache key), `store.py`, `serialize.py`, `selenium_capture.py` | 2, 3, 5 |
| §Capture policy `isolated/1` (B7) | `policy.py`; the adapter; the browser tests | 2, 5 |
| §Checks: markers and the documented command | The root pytest configuration; `CLAUDE.md`, `README.md`, `AGENTS.md:206` | 1 |
| §Checks: network guard and determinism | `test_selenium_capture.py`; the recapture checks | 5, 9, 11 |
| §Checks: calibration | `calibrate.py`, `docs/verification/browser-calibration.md` | 11 |
| §Layout extractor `layout-1` and alignment (B5, SC13) | `layout/blocks.py`, `align.py`, `records.py`, `extract.py` | 6, 7, 8 |
| The two-parser contract (plan 3's Handoff 1) | `tests/contracts/test_element_schema_parsers.py`, with the contract release and its capture | 9 |
| §Pre-registered comparison | `triggers.py`, `layout1_units.py`, `layout1_report.py`, `preregister.py`, the captures, the report | 8, 10, 11, 13 |
| §Promotion decision | ADR 0002; `walker-2` and its fixtures on promotion | 13, 14 |
| §Import boundaries | `test_import_scan.py`; `test_import_boundaries.py` | 5, 8, 14 |
| §Verify at plan time | PB-2, run at planning | — |
| §R3.5 fidelity check, plan B's leg | `fidelity.py`'s `token_hunks` and `hunk_category`; `r35_report.py`; the report | 12 |
| Plan 4's Handoffs "To plan B" | Source types and text origin (PB-9); the contract (Task 9); R3.5 (Task 12); the findings (PB-21) | 8, 9, 12, 15 |
| The review gate's findings; their deferred item | The probes; ADR 0002; `docs/verification/layout-1.md` | 10, 13, 15 |
| Deferred item: "Check import boundaries statically as well" | The import scan | 5 |

The spec's plan B exit criteria map onto this plan's tasks as follows:

| Exit criterion | Tasks |
| --- | --- |
| 1: the extra, the pinned binaries, and the setup command; no processing run downloads | 4, 5 |
| 2: calibration on the three categories, classified, with no gold change | 11 |
| 3: the network guard; no source JavaScript runs | 5 |
| 4: two captures, one rendered-text hash | 5, 9, 11 |
| 5: every layout-1 unit an exact span or `alignment_failed`; the contract with the real pair | 7, 8, 9, 11 |
| 6: every metric and class for the three configurations | 10, 13 |
| 7: ADR 0002 accepted; on promotion, the fixtures re-canonicalized | 13, 14 |
| 8: R3.5 final | 12 |
| 9: the AST scan and the runtime boundary checks | 5, 8, 14 |
| 10: the default suite needs no browser; browser checks only with `-m browser`, skipping visibly and recording the environment | 1, 5, 15 |

## Human gates

| Gate | When | Who | What it unblocks |
| --- | --- | --- | --- |
| The download | Task 5, Step 7 | user | `browser setup` downloads two archives: `chrome-mac-arm64.zip` (191,429,663 bytes) and `chromedriver-mac-arm64.zip` (9,302,980 bytes), from `https://storage.googleapis.com/chrome-for-testing-public/154.0.8037.57/mac-arm64/`. Ask in chat, naming both with their source and size, and wait for a clear yes. |
| ADR 0002 | Task 13, Step 5 | user | Which outcome the ADR records, among those the report's Verdict allows. Task 14 runs only on outcome 2 or 3. |

In subagent-driven execution, both gates run in the controller session with the
user, never in a subagent. Each is a hard stop: nothing after it starts until the
user has answered. A subagent that reaches Task 5, Step 7 stops and reports back
instead.

## File map

`…/browser/`, `…/layout/`, `…/canonical/` and `…/promoted/` below are under
`packages/earnings-ingestion/src/earnings_ingestion/`, and `…/tests/` is
`packages/earnings-ingestion/tests/`.

| Path | Responsibility | Task |
| --- | --- | --- |
| `pyproject.toml`, `tests/test_pytest_configuration.py` | The `browser` marker, deselected by default | 1 |
| `CLAUDE.md`, `README.md`, `AGENTS.md` (line 206 only) | The documented command (Task 1); the extra's row (Task 5); the current state (Task 15) | 1, 5, 15 |
| `…/browser/__init__.py` | The public API: capture contract (Task 2), then the store (Task 3) | 2, 3 |
| `…/browser/records.py`, `policy.py`, `metadata.py`, `renderer.py` | Capture records; `isolated/1`; the layout-metadata script; `BrowserRenderer`, `FakeRenderer`, the cache key | 2 |
| `…/tests/conftest.py` | Shared capture and layout builders: the capture (Task 2), the layout parts (Task 6) | 2, 6 |
| `…/tests/test_browser_records.py`, `test_browser_renderer.py` | Their tests | 2 |
| `docs/data-dictionary.md`, `tests/contracts/test_data_dictionary.py` | The capture records (Task 2), layout-1's (Task 8), walker-2's (Task 14) | 2, 8, 14 |
| `…/browser/store.py`, `serialize.py`, `…/tests/test_browser_store.py`, `test_browser_serialize.py` | The capture store; the capture-fixture format | 3 |
| `…/browser/install.py`, `chrome-for-testing.toml`, `…/tests/test_browser_install.py` | The pin and its install | 4 |
| `apps/earnings-pipeline/src/earnings_pipeline/cli.py`, `apps/earnings-pipeline/pyproject.toml`, `apps/earnings-pipeline/tests/test_cli.py` | `earnings-pipeline browser setup` | 4 |
| `packages/earnings-ingestion/pyproject.toml`, `uv.lock` | The `browser-capture` extra | 5 |
| `…/browser/selenium_capture.py`, `…/tests/test_selenium_capture.py` | The Selenium adapter and its browser tests | 5 |
| `tests/contracts/test_import_scan.py`, `…/tests/test_import_boundaries.py` | The static scan; the runtime checks, extended in Tasks 8 and 14 | 5, 8, 14 |
| `…/layout/__init__.py` | A docstring (Task 6); the public API (Task 8) | 6, 8 |
| `…/layout/blocks.py`, `…/tests/test_layout_blocks.py` | layout-1's L-rules | 6 |
| `…/layout/align.py`, `…/tests/test_layout_align.py` | `anchored-1` | 7 |
| `…/layout/records.py`, `extract.py`, `…/canonical/triggers.py`, `…/tests/test_layout_extract.py`, `test_triggers.py` | The layout records; `LayoutExtractor`; the fallback's triggers | 8 |
| `tests/fixtures/browser/contract-release.html`, `contract-release.capture.json` (generated) | The two-parser contract's release and capture | 9 |
| `tests/integration/capture_browser_fixtures.py` | Captures the committed browser fixtures (never collected) | 9 |
| `.gitattributes` (one line appended per task) | The browser fixtures (Task 9) and walker-2's (Task 14) keep their bytes | 9, 14 |
| `tests/contracts/test_element_schema_parsers.py` | The contract with the real pair | 9 |
| `expirements/parser-fidelity/layout1_units.py`, `layout1-units.toml` (generated), `test_layout1_units.py` | The targeted units | 10 |
| `expirements/parser-fidelity/layout1_report.py`, `test_layout1_report.py` | The comparison and its rules | 10 |
| `expirements/parser-fidelity/preregister.py`, `test_preregister.py`, `layout1-preregistered.toml` (generated) | The freeze | 10 |
| `tests/fixtures/browser/<fixture>.capture.json` (eight, generated), `tests/integration/test_browser_fixtures.py` | The release captures and their checks | 11 |
| `expirements/parser-fidelity/calibrate.py`, `test_calibrate.py`, `test_calibrate_current.py`, `docs/verification/browser-calibration.md` (generated) | Calibration | 11 |
| `…/canonical/fidelity.py`, `…/tests/test_fidelity.py` | R3.5's leg-2 comparators | 12 |
| `expirements/parser-fidelity/r35_report.py`, `test_r35_report.py`, `test_r35_report_current.py`, `tests/integration/test_r35_report.py`, `docs/verification/R3.5-text-fidelity.md` (regenerated) | R3.5's final report | 12 |
| `expirements/parser-fidelity/test_layout1_report_current.py`, `docs/verification/layout-1-comparison.md` (generated) | The comparison's report | 13 |
| `docs/adr/0002-<outcome>.md` | ADR 0002 | 13 |
| `…/promoted/{__init__,records,pipeline,serialize}.py`, `…/tests/test_promoted.py` | walker-2 (outcome 2 or 3 only) | 14 |
| `tests/integration/regenerate_walker2_fixtures.py`, `test_walker2_golden.py`, `tests/fixtures/walker-2/*.json` (generated) | walker-2's fixtures (outcome 2 or 3 only) | 14 |
| `docs/verification/layout-1.md` | The verification record | 15 |
| `expirements/parser-fidelity/README.md` | The harness's plan B scripts | 15 |

No other file changes. The frozen harness files stay byte for byte as `FROZEN.toml`
records them, and `walker-1`'s files as plan 4 committed them.

## Preconditions — read before Task 1

- **Branch.** Work on `stage-3-browser-diagnostic-path` in the main checkout (PB-23).
  At planning time its only commit above `main` (`0938b66`) was this plan, and the
  branch was unpushed. Run this and read the result:

  ```bash
  git switch stage-3-browser-diagnostic-path && git log --oneline -3 && git status --short
  ```

  Expected: the head is `docs(plan): plan 5, Stage 3 plan B: the browser diagnostic path`,
  or a later commit the user made, and the status is empty.
- **Stay in the main checkout.** Do not execute in a separate worktree. `data/` is
  gitignored, so a worktree lacks:
  - the development releases, which the harness suite runs;
  - the user's `rendered.txt` copies, without which Tasks 11 and 12 cannot finish.
- **Environment.** Run `uv sync --locked --all-packages`; the `dev` group syncs by
  default.
  - `uv --version` must print uv 0.12.15.
  - The interpreter is Python 3.14.0, pinned by `.python-version`.
  - `uname -sm` must print `Darwin arm64`: the pin is for mac-arm64.
- **Helpers.** Save the two helpers from Global Constraints, then check both:

  ```bash
  python3 /tmp/plan5-extract.py docs/no-such-file.md; python3 /tmp/plan5-escapes.py specs/plans/5-structure-aware-canonicalization.md
  ```

  Expected: `specs/plans/5-structure-aware-canonicalization.md has no block 1 for docs/no-such-file.md`,
  then the plan's own path. The plan holds non-ASCII characters, so this shows that
  the check works.
- **Baselines.** Before Task 1 the documented default command is still
  `-m "not live"`:

  ```bash
  uv run --locked --all-packages pytest packages apps tests -m "not live" -q
  uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
  uv run --locked ruff check . && uv run --locked ruff format --check .
  uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
  ```

  Expected: `491 passed`; `222 passed`; `All checks passed!` and
  `116 files already formatted`; `freeze verified`.
- **Local data.**
  - `ls data/raw/devset/` lists `0000019149-11-000022_ex-99-1`,
    `0000079958-12-000020_ex-99-1` and `0001045150-09-000060_ex-99-1`.
  - `ls data/runs/parser-fidelity/gold-drafts/*.rendered.txt | wc -l` prints `8`.

  If a copy is missing, stop and ask: calibration and R3.5's leg 2 need all eight.
  Never open a release's copy before Task 11.
- **The pinned browser** is not installed yet. Task 5 installs it, with the user's
  permission. If `EARNINGS_BROWSER_CACHE` is set in your shell, unset it unless the
  user set it on purpose.

---
### Task 1: The `browser` marker and the documented command

pytest keeps the last `-m` it is given. Once the configuration deselects `browser`
tests by default, the documented command's own `-m "not live"` would override that
and select them. So the configuration and every documented default command change
together (PB-17).

**Files:**

- Modify: `pyproject.toml` (replaced whole: one comment, `addopts`, one marker).
- Test (modify): `tests/test_pytest_configuration.py` (replaced whole: four tests
  added).
- Modify: `CLAUDE.md`, `README.md`, and `AGENTS.md` line 206, by exact replacement.

**Interfaces:**

- Consumes: nothing from this plan.
- Produces:
  - the registered marker `browser`;
  - the default `-m "not live and not browser"`;
  - the documented default command
    `uv run --locked --all-packages pytest packages apps tests -m "not live and not browser"`.

  Every later task uses them.

- [ ] **Step 1: Write the failing tests**

Replace `tests/test_pytest_configuration.py` with:

```python
"""The root pytest configuration: registered markers and collision-safe imports (A §193)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "pyproject.toml"


def run_pytest(*args: str) -> subprocess.CompletedProcess[str]:
    """Run pytest under the root configuration, without touching the repo's cache."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-c", str(CONFIG), "-p", "no:cacheprovider"]
        + list(args),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_live_marker_is_registered() -> None:
    result = run_pytest("--markers")
    assert result.returncode == 0, result.stderr
    assert "@pytest.mark.live:" in result.stdout


def test_not_live_deselects_live_tests(tmp_path: Path) -> None:
    (tmp_path / "test_marks.py").write_text(
        "import pytest\n"
        "\n"
        "def test_offline():\n"
        "    pass\n"
        "\n"
        "@pytest.mark.live\n"
        "def test_online():\n"
        "    raise AssertionError('a live test ran by default')\n",
        encoding="utf-8",
    )
    result = run_pytest(str(tmp_path), "-m", "not live", "-q")
    assert result.returncode == 0, result.stdout
    assert "1 passed, 1 deselected" in result.stdout


def test_a_bare_run_deselects_live_tests(tmp_path: Path) -> None:
    (tmp_path / "test_marks.py").write_text(
        "import pytest\n"
        "\n"
        "def test_offline():\n"
        "    pass\n"
        "\n"
        "@pytest.mark.live\n"
        "def test_online():\n"
        "    raise AssertionError('a live test ran by default')\n",
        encoding="utf-8",
    )
    result = run_pytest(str(tmp_path), "-q")
    assert result.returncode == 0, result.stdout
    assert "1 passed, 1 deselected" in result.stdout


MARKED = (
    "import pytest\n"
    "\n"
    "def test_offline():\n"
    "    pass\n"
    "\n"
    "@pytest.mark.live\n"
    "def test_online():\n"
    "    raise AssertionError('a live test ran by default')\n"
    "\n"
    "@pytest.mark.browser\n"
    "def test_in_a_browser():\n"
    "    raise AssertionError('a browser test ran by default')\n"
)


def test_browser_marker_is_registered() -> None:
    result = run_pytest("--markers")
    assert result.returncode == 0, result.stderr
    assert "@pytest.mark.browser:" in result.stdout


def test_a_bare_run_deselects_live_and_browser_tests(tmp_path: Path) -> None:
    (tmp_path / "test_marks.py").write_text(MARKED, encoding="utf-8")
    result = run_pytest(str(tmp_path), "-q")
    assert result.returncode == 0, result.stdout
    assert "1 passed, 2 deselected" in result.stdout


def test_the_documented_command_deselects_live_and_browser_tests(
    tmp_path: Path,
) -> None:
    (tmp_path / "test_marks.py").write_text(MARKED, encoding="utf-8")
    result = run_pytest(str(tmp_path), "-m", "not live and not browser", "-q")
    assert result.returncode == 0, result.stdout
    assert "1 passed, 2 deselected" in result.stdout


def test_minus_m_browser_selects_only_browser_tests(tmp_path: Path) -> None:
    (tmp_path / "test_marks.py").write_text(MARKED, encoding="utf-8")
    result = run_pytest(str(tmp_path), "-m", "browser", "-q")
    assert result.returncode == 1, result.stdout
    assert "1 failed, 2 deselected" in result.stdout
    assert "a browser test ran by default" in result.stdout


def test_unregistered_marker_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "test_typo.py").write_text(
        "import pytest\n\n@pytest.mark.lvie\ndef test_typo():\n    pass\n",
        encoding="utf-8",
    )
    result = run_pytest(str(tmp_path), "-q")
    assert result.returncode != 0
    assert "'lvie' not found in `markers`" in result.stdout


def test_same_named_test_modules_do_not_collide(tmp_path: Path) -> None:
    for member in ("first", "second"):
        tests = tmp_path / member / "tests"
        tests.mkdir(parents=True)
        (tests / "test_same_name.py").write_text(
            f"def test_{member}():\n    pass\n", encoding="utf-8"
        )
    result = run_pytest(str(tmp_path), "-q")
    assert result.returncode == 0, result.stdout
    assert "2 passed" in result.stdout
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --locked --all-packages pytest tests/test_pytest_configuration.py -q`

Expected: `4 failed, 5 passed`. The four new tests fail because `browser` is not yet a registered marker, and strict mode refuses an unregistered one.

- [ ] **Step 3: Register the marker and deselect it by default**

Replace `pyproject.toml` with:

```toml
# Virtual workspace root: intentionally has no [project] table.
# The `earnings-themes` distribution name belongs to packages/earnings-themes;
# a root [project] with that name would collide (uv requires unique member names).
# `[tool.uv] package = false` does NOT avoid this: uv enforces name uniqueness for
# non-package members too. Only the absence of [project] removes the root from the
# member set.
# Application CLI entry points belong in apps/earnings-pipeline, not here.

[tool.uv.workspace]
members = [
    "packages/earnings-core",
    "packages/earnings-ingestion",
    "packages/earnings-themes",
    "apps/earnings-pipeline",
]

[tool.uv.sources]
earnings-core = { workspace = true }
earnings-ingestion = { workspace = true }
earnings-themes = { workspace = true }

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "ruff",
]

[tool.ruff]
# Ruff governs Python source only. Ruff >=0.16 formats Python code blocks embedded
# in Markdown; this repo's Markdown is documentation and quoted third-party review
# material (specs/earning-themes-review-*.md, docs/*.md) that CLAUDE.md requires be
# preserved verbatim. Formatting those blocks would rewrite supplied text.
extend-exclude = ["*.md"]

[tool.pytest]
# A §193: collect package, application, and shared tests; keep same-named test modules
# in different members from colliding; make live checks opt-in.
# importlib mode imports each test file by its path, so packages/*/tests/test_x.py can
# repeat a basename. The frozen Stage 1 harness imports its modules by bare name and
# still needs prepend mode: its documented command passes --import-mode=prepend, which
# overrides this default.
# -m "not live and not browser" deselects live and browser tests unless the command line
# passes its own -m, such as -m live or -m browser: pytest keeps the last -m it is given
# (A §217: live checks are opt-in; Stage 3 spec, Checks: so are browser checks).
addopts = ["--import-mode=importlib", "-m", "not live and not browser"]
testpaths = ["packages", "apps", "tests"]
# strict: unknown config keys, unregistered markers, non-strict xfail, and duplicate
# parametrize IDs are errors.
strict = true
markers = [
    "live: needs the network, credentials, or a billable service; run only with -m live",
    "browser: needs the pinned Chrome for Testing and the browser-capture extra; run only with -m browser",
]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest tests/test_pytest_configuration.py -q`

Expected: `9 passed`.

- [ ] **Step 5: Change the documented command**

`AGENTS.md` is cited by line number, so its line 206 changes in place and the file
keeps 837 lines. Apply the replacements below. Each must match exactly once. If one
does not match, because the user edited that passage, stop and ask rather than guess:

```bash
python3 - <<'EOF'
from pathlib import Path

OLD = 'pytest packages apps tests -m "not live"\n'
NEW = 'pytest packages apps tests -m "not live and not browser"\n'
edits = {
    "AGENTS.md": [(OLD, NEW)],
    "CLAUDE.md": [
        (OLD, NEW),
        (
            'pytest path/to/test_x.py::test_name -m "not live"\n',
            'pytest path/to/test_x.py::test_name -m "not live and not browser"\n',
        ),
        (
            "`strict = true`; a registered `live` marker; and\n",
            "`strict = true`; registered `live` and `browser` markers, both deselected by\n"
            "default; and\n",
        ),
    ],
    "README.md": [
        (OLD, NEW),
        (
            "carries the `live` marker and runs only with `-m live`. The Stage 1 harness keeps\n"
            "its own command, given under \"Current roadmap\". There is no CI configuration yet.\n",
            "carries the `live` marker and runs only with `-m live`. A test that needs the\n"
            "pinned Chrome for Testing carries the `browser` marker and runs only with\n"
            "`-m browser`; without the browser or the `browser-capture` extra it skips and\n"
            "says why. The Stage 1 harness keeps its own command, given under \"Current\n"
            "roadmap\". There is no CI configuration yet.\n",
        ),
    ],
}
for name, pairs in edits.items():
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"{name}: expected one match, found {count}: {old[:60]}")
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
print("documented command updated")
EOF
wc -l AGENTS.md && git diff --stat
```

Expected: `documented command updated`, then `837 AGENTS.md`. `git diff --stat` lists
the five files of this task, `5 files changed, 62 insertions(+), 10 deletions(-)`:
`AGENTS.md` 2, `CLAUDE.md` 7, `README.md` 9, `pyproject.toml` 8, and
`tests/test_pytest_configuration.py` 46.

- [ ] **Step 6: Run the checks**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `495 passed`, then `All checks passed!` and `116 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git log --oneline -3
git add pyproject.toml tests/test_pytest_configuration.py AGENTS.md CLAUDE.md README.md
git commit -m "test(config): register the browser marker and deselect it by default"
```

---
### Task 2: The capture contract — records, policy, layout metadata, and the renderer

The capture's data model comes first, with no browser in sight. The fake renderer and
the tests stand on it, and so does every later task. `RenderedCapture` carries every
field the browser spec's list names, and its validator refuses a capture whose
status, reason and content disagree.

The layout-metadata script is JavaScript held as a Python string. It runs in the
page through WebDriver while document JavaScript stays disabled (PB-2, check 1).
`parse_metadata` reads its result into the records. That split lets the default
tests exercise every record without a browser.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/browser/__init__.py`
  (block 1 of 2), `records.py`, `policy.py`, `metadata.py`, `renderer.py`.
- Test (create): `packages/earnings-ingestion/tests/conftest.py` (block 1 of 2),
  `test_browser_records.py`, `test_browser_renderer.py`.
- Modify: `docs/data-dictionary.md` (appended); test:
  `tests/contracts/test_data_dictionary.py` (replaced whole, block 1 of 3).

**Interfaces:**

- Consumes:
  - `earnings_core`: `ArtifactRef`, `sha256_hex`, `IdPart`, `Sha256Hex`;
  - `earnings_ingestion.canonical.records.IngestionRecord`, the base of every
    ingestion record, whose `schema_version` is `1`.
- Produces, in `earnings_ingestion.browser`:
  - **`records.py`.**
    - `CaptureStatus`: `completed`, `partial`, `failed`, `unavailable`.
    - `CaptureReason`: `browser_unavailable`, `startup_failure`, `timeout`,
      `blocked_required_resource`, `document_load_failure`, `capture_failure`.
    - `BlockedRequest(url, resource_type, required)`.
    - The layout records: `LayoutRun`, `LayoutBlock`, `LayoutCell`, `LayoutRow`,
      `LayoutTable`, and `LayoutMetadata(blocks, tables)`.
    - `RenderedCapture`.
    - `layout_hash(layout: LayoutMetadata) -> str`.
  - **`policy.py`.**
    - `CapturePolicy`, a frozen dataclass.
    - `ISOLATED_1`.
    - `CAPTURE_POLICY = "isolated"`, `CAPTURE_POLICY_VERSION = "1"`, and
      `SAVED_NAME = "document.html"`.
  - **`metadata.py`.**
    - `METADATA_VERSION = "layout-metadata-1"`.
    - `METADATA_SCRIPT: str`.
    - `parse_metadata(payload: Mapping[str, Any]) -> LayoutMetadata`.
  - **`renderer.py`.**
    - `CaptureEnvironment`, with seven fields and a `font_set` property.
    - `this_platform() -> tuple[str, str, str]`.
    - `cache_key(raw_sha256, policy, environment) -> str`.
    - `capture_id(source_document_id, policy, key) -> str`, of the form
      `<source>@isolated-1#<16 hex>`.
    - `BrowserRenderer`, a `Protocol` with `environment` and
      `capture(saved_html, capture_policy, *, source_document_id) -> RenderedCapture`.
    - `unrendered(saved_html, capture_policy, environment, *, source_document_id, status, reason, detail, captured_at=None, duration_seconds=0.0) -> RenderedCapture`.
    - `FakeRenderer(captures: Mapping[str, RenderedCapture], environment)`, keyed by
      raw SHA-256.
    - `EMPTY_LAYOUT`.
  - **`tests/conftest.py`.**
    - `ENVIRONMENT` and `PAYLOAD`.
    - `build_capture(**changes) -> RenderedCapture`, a completed capture of
      `<p>Revenue rose.</p>` with any field replaced.
    - The fixtures `make_capture` (returns `build_capture`) and `payload` (a deep copy
      of `PAYLOAD`).

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/conftest.py`:

```python
"""Shared test data (plan 5): a small completed capture and its layout payload."""

import copy
from collections.abc import Callable
from datetime import UTC, datetime

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
```

Create `packages/earnings-ingestion/tests/test_browser_records.py`:

```python
"""RenderedCapture and its parts: hashes, statuses, and strict closed records (B2)."""

import json
from collections.abc import Callable

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.browser.metadata import parse_metadata
from earnings_ingestion.browser.records import (
    CaptureReason,
    CaptureStatus,
    LayoutMetadata,
    RenderedCapture,
    layout_hash,
)
from earnings_ingestion.browser.renderer import EMPTY_LAYOUT
from pydantic import ValidationError

Make = Callable[..., RenderedCapture]


def test_a_completed_capture_round_trips_through_json(make_capture: Make) -> None:
    record = make_capture()
    assert RenderedCapture.model_validate_json(record.model_dump_json()) == record


def test_the_text_hash_must_be_the_texts(make_capture: Make) -> None:
    with pytest.raises(ValidationError, match="rendered_text_sha256"):
        make_capture(rendered_text_sha256=sha256_hex(b"something else"))


def test_the_layout_hash_must_be_the_layouts(make_capture: Make) -> None:
    with pytest.raises(ValidationError, match="layout_sha256"):
        make_capture(layout_sha256=layout_hash(EMPTY_LAYOUT))


def test_the_layout_hash_ignores_field_order_but_not_values(payload: dict) -> None:
    layout = parse_metadata(payload)
    again = parse_metadata(json.loads(json.dumps(payload, sort_keys=True)))
    assert layout_hash(layout) == layout_hash(again)
    payload["blocks"][0]["runs"][0]["bold"] = True
    assert layout_hash(parse_metadata(payload)) != layout_hash(layout)


def test_a_reason_is_recorded_exactly_when_not_completed(make_capture: Make) -> None:
    with pytest.raises(ValidationError, match="reason"):
        make_capture(reason=CaptureReason.TIMEOUT)
    with pytest.raises(ValidationError, match="reason"):
        make_capture(status=CaptureStatus.FAILED, rendered_text="", layout=EMPTY_LAYOUT)


def test_a_partial_capture_names_a_blocked_required_resource(
    make_capture: Make,
) -> None:
    partial = make_capture(
        status=CaptureStatus.PARTIAL, reason=CaptureReason.BLOCKED_REQUIRED_RESOURCE
    )
    assert partial.status is CaptureStatus.PARTIAL
    with pytest.raises(ValidationError, match="partial"):
        make_capture(status=CaptureStatus.PARTIAL, reason=CaptureReason.TIMEOUT)


@pytest.mark.parametrize("status", [CaptureStatus.FAILED, CaptureStatus.UNAVAILABLE])
def test_a_failure_is_never_an_empty_successful_capture(
    status: CaptureStatus, make_capture: Make
) -> None:
    with pytest.raises(ValidationError, match="holds no rendering"):
        make_capture(status=status, reason=CaptureReason.CAPTURE_FAILURE)
    empty = make_capture(
        status=status,
        reason=CaptureReason.CAPTURE_FAILURE,
        rendered_text="",
        layout=EMPTY_LAYOUT,
    )
    assert empty.layout.blocks == ()


def test_records_are_closed_and_strict(make_capture: Make) -> None:
    with pytest.raises(ValidationError):
        make_capture(unexpected="field")
    with pytest.raises(ValidationError):
        make_capture(viewport_width="1280")


def test_malformed_metadata_is_a_value_error(payload: dict) -> None:
    with pytest.raises(ValueError, match="malformed layout metadata"):
        parse_metadata({"blocks": [{"tag": "p"}], "tables": []})
    with pytest.raises(ValidationError):
        parse_metadata({"blocks": [{**payload["blocks"][0], "x": "8"}], "tables": []})


def test_the_empty_layout_is_empty() -> None:
    assert EMPTY_LAYOUT == LayoutMetadata(blocks=(), tables=())
```

Create `packages/earnings-ingestion/tests/test_browser_renderer.py`:

```python
"""The renderer interface without a browser: cache keys, identifiers, and the fake."""

import dataclasses

from earnings_core import sha256_hex
from earnings_ingestion.browser import renderer
from earnings_ingestion.browser.policy import ISOLATED_1
from earnings_ingestion.browser.records import CaptureReason, CaptureStatus
from earnings_ingestion.browser.renderer import (
    CaptureEnvironment,
    FakeRenderer,
    cache_key,
    capture_id,
    unrendered,
)

ENVIRONMENT = CaptureEnvironment(
    browser_engine="Chrome for Testing",
    browser_version="154.0.8037.57",
    driver_version="154.0.8037.57",
    selenium_version="4.49.0",
    os_name="Darwin",
    os_version="26.6.2",
    architecture="arm64",
)
RAW = b"<p>Revenue rose.</p>"


def test_the_cache_key_is_stable_and_has_no_timestamp() -> None:
    key = cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT)
    assert key == cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT)
    assert len(key) == 64


def test_every_input_that_can_change_a_capture_changes_the_key() -> None:
    key = cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT)
    changed = [
        cache_key(sha256_hex(b"<p>Other.</p>"), ISOLATED_1, ENVIRONMENT),
        cache_key(
            sha256_hex(RAW), dataclasses.replace(ISOLATED_1, version="2"), ENVIRONMENT
        ),
        cache_key(
            sha256_hex(RAW),
            dataclasses.replace(ISOLATED_1, viewport_width=800),
            ENVIRONMENT,
        ),
        cache_key(
            sha256_hex(RAW),
            ISOLATED_1,
            dataclasses.replace(ENVIRONMENT, browser_version="155.0.0.0"),
        ),
        cache_key(
            sha256_hex(RAW),
            ISOLATED_1,
            dataclasses.replace(ENVIRONMENT, os_version="27.0"),
        ),
    ]
    assert key not in changed
    assert len(set(changed)) == len(changed)


def test_the_metadata_scripts_text_is_part_of_the_key(monkeypatch) -> None:
    key = cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT)
    monkeypatch.setattr(renderer, "METADATA_SCRIPT", renderer.METADATA_SCRIPT + "\n")
    assert cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT) != key


def test_the_capture_id_names_the_source_the_policy_and_the_key() -> None:
    key = cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT)
    assert capture_id("release", ISOLATED_1, key) == f"release@isolated-1#{key[:16]}"


def test_the_font_set_is_the_platform_release() -> None:
    assert ENVIRONMENT.font_set == "Darwin 26.6.2 system fonts"


def test_an_unrendered_capture_records_its_reason_and_nothing_else() -> None:
    record = unrendered(
        RAW,
        ISOLATED_1,
        ENVIRONMENT,
        source_document_id="release",
        status=CaptureStatus.FAILED,
        reason=CaptureReason.TIMEOUT,
        detail="navigation ran past 30 s",
    )
    assert record.status is CaptureStatus.FAILED
    assert record.reason is CaptureReason.TIMEOUT
    assert (record.rendered_text, record.layout.blocks, record.screenshots) == (
        "",
        (),
        (),
    )
    assert record.raw_sha256 == sha256_hex(RAW)


def test_the_fake_returns_saved_captures_by_raw_hash() -> None:
    saved = unrendered(
        RAW,
        ISOLATED_1,
        ENVIRONMENT,
        source_document_id="release",
        status=CaptureStatus.FAILED,
        reason=CaptureReason.CAPTURE_FAILURE,
        detail="saved",
    )
    fake = FakeRenderer({sha256_hex(RAW): saved}, ENVIRONMENT)
    assert fake.capture(RAW, ISOLATED_1, source_document_id="release") is saved


def test_the_fake_is_unavailable_for_anything_else() -> None:
    fake = FakeRenderer({}, ENVIRONMENT)
    record = fake.capture(b"<p>New.</p>", ISOLATED_1, source_document_id="other")
    assert record.status is CaptureStatus.UNAVAILABLE
    assert record.reason is CaptureReason.BROWSER_UNAVAILABLE
    assert fake.environment is ENVIRONMENT
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_browser_records.py packages/earnings-ingestion/tests/test_browser_renderer.py -q`

Expected: an error while loading `conftest.py`: `ModuleNotFoundError: No module named 'earnings_ingestion.browser'`.

- [ ] **Step 3: Write the records, the policy, the metadata script, and the renderer**

Create `packages/earnings-ingestion/src/earnings_ingestion/browser/records.py`:

```python
"""What the controlled browser displayed for one saved source (Stage 3, plan B).

``RenderedCapture`` is browser-specific ingestion provenance, never a core contract
(B2): it establishes what the browser displayed under a recorded policy, not quote
exactness or a canonical span. docs/data-dictionary.md documents every field.
"""

import json
from enum import StrEnum
from typing import Self

from earnings_core import ArtifactRef
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex, sha256_hex
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)

from earnings_ingestion.canonical.records import IngestionRecord


class CaptureStatus(StrEnum):
    """The browser spec's four capture outcomes."""

    COMPLETED = "completed"
    """Every resource the rendering needs was present."""
    PARTIAL = "partial"
    """Rendered, but a blocked or missing stylesheet, font, or frame may change it."""
    FAILED = "failed"
    """The browser ran, and no usable rendering came back."""
    UNAVAILABLE = "unavailable"
    """No pinned browser could run here."""


class CaptureReason(StrEnum):
    """Why a capture is not ``completed``."""

    BROWSER_UNAVAILABLE = "browser_unavailable"
    """The pinned browser or driver is not installed, or none is pinned here."""
    STARTUP_FAILURE = "startup_failure"
    """The browser or driver did not start, or is not the pinned version."""
    TIMEOUT = "timeout"
    """Navigation or capture ran past its bound."""
    BLOCKED_REQUIRED_RESOURCE = "blocked_required_resource"
    """A stylesheet, font, or frame the page asked for was blocked or missing."""
    DOCUMENT_LOAD_FAILURE = "document_load_failure"
    """The saved file did not load, or the page left it."""
    CAPTURE_FAILURE = "capture_failure"
    """Reading text, layout, or a screenshot failed, or request interception stopped."""


class _Part(BaseModel):
    """A nested part of a capture: immutable, closed, and strictly typed."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class BlockedRequest(_Part):
    """One request the page made and the capture refused (B7: recorded and blocked)."""

    url: str
    resource_type: str
    """CDP's resource type, such as ``Image``, ``Stylesheet``, or ``Document``."""
    required: bool
    """A stylesheet, font, or subframe document: its absence makes the capture partial."""


class LayoutRun(_Part):
    """One text node's raw DOM text and computed style, or a ``<br>``."""

    text: str
    br: bool
    visible: bool
    bold: bool
    underline: bool
    superscript: bool
    symbol_font: bool
    font_size: NonNegativeFloat


class LayoutBlock(_Part):
    """The runs one block element holds directly, split where a nested block starts.

    ``heading_level`` and ``list_item`` come from the nearest heading or list item
    around it; ``table``, ``row``, and ``cell`` locate its nearest table cell.
    """

    tag: str
    display: str
    heading_level: PositiveInt | None
    list_item: bool
    list_depth: NonNegativeInt
    table: NonNegativeInt | None
    row: NonNegativeInt | None
    cell: NonNegativeInt | None
    x: int
    y: int
    width: NonNegativeInt
    height: NonNegativeInt
    runs: tuple[LayoutRun, ...]


class LayoutCell(_Part):
    """A rendered cell: whether it is a ``th``, and its spans."""

    header: bool
    colspan: PositiveInt
    rowspan: PositiveInt


class LayoutRow(_Part):
    """A rendered row of a table's own: whether it sits in ``thead``, and its cells."""

    head: bool
    cells: tuple[LayoutCell, ...]


class LayoutTable(_Part):
    """A rendered table's own rows in document order, and the cell holding the table.

    ``parent_table``, ``parent_row`` and ``parent_cell`` locate the nearest cell of
    another table that holds this one; all three are ``None`` for a table in no cell.
    """

    parent_table: NonNegativeInt | None
    parent_row: NonNegativeInt | None
    parent_cell: NonNegativeInt | None
    rows: tuple[LayoutRow, ...]


class LayoutMetadata(_Part):
    """Every block and table of the rendered body, in document order."""

    blocks: tuple[LayoutBlock, ...]
    tables: tuple[LayoutTable, ...]


class RenderedCapture(IngestionRecord):
    """One capture of one saved source under one capture policy (B1, B2, B7).

    ``cache_key`` covers the raw hash, the policy, the browser, driver, and Selenium,
    the platform and render configuration, and the metadata script's version and
    text; never a timestamp. A failed or unavailable capture holds no text, layout, or screenshot:
    a failure is never an empty successful capture.
    """

    capture_id: str
    cache_key: Sha256Hex
    source_document_id: IdPart
    raw_sha256: Sha256Hex
    capture_policy: IdPart
    capture_policy_version: IdPart
    metadata_version: IdPart
    browser_engine: str
    browser_version: str
    driver_version: str
    selenium_version: str
    os_name: str
    os_version: str
    architecture: str
    viewport_width: PositiveInt
    viewport_height: PositiveInt
    device_scale_factor: PositiveInt
    locale: str
    timezone: str
    font_set: str
    document_charset: str
    script_policy: str
    network_policy: str
    image_policy: str
    missing_resource_policy: str
    rendered_text: str
    rendered_text_sha256: Sha256Hex
    layout: LayoutMetadata
    layout_sha256: Sha256Hex
    screenshots: tuple[ArtifactRef, ...]
    blocked_requests: tuple[BlockedRequest, ...]
    captured_at: AwareDatetime
    duration_seconds: NonNegativeFloat
    status: CaptureStatus
    reason: CaptureReason | None
    detail: str

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.rendered_text_sha256 != sha256_hex(self.rendered_text.encode("utf-8")):
            raise ValueError("rendered_text_sha256 is not the rendered text's hash")
        if self.layout_sha256 != layout_hash(self.layout):
            raise ValueError("layout_sha256 is not the layout's hash")
        if (self.reason is None) != (self.status is CaptureStatus.COMPLETED):
            raise ValueError("a reason is recorded exactly when not completed")
        if self.status is CaptureStatus.PARTIAL and (
            self.reason is not CaptureReason.BLOCKED_REQUIRED_RESOURCE
        ):
            raise ValueError("a partial capture's reason is blocked_required_resource")
        if self.status in (CaptureStatus.FAILED, CaptureStatus.UNAVAILABLE) and (
            self.rendered_text or self.layout.blocks or self.screenshots
        ):
            raise ValueError("a failed or unavailable capture holds no rendering")
        return self


def layout_hash(layout: LayoutMetadata) -> str:
    """SHA-256 of the layout as ASCII JSON with sorted keys and no spaces."""
    payload = json.dumps(
        layout.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256_hex(payload.encode("ascii"))
```

Create `packages/earnings-ingestion/src/earnings_ingestion/browser/policy.py`:

```python
"""Capture policy ``isolated/1`` (B7): a saved filing is untrusted data.

- **Profile.** chromedriver's fresh temporary profile, headless, with no extension,
  sync, or first-run state.
- **JavaScript.** Document JavaScript is disabled through CDP before navigation.
  WebDriver's own scripts, which read text and layout, still run.
- **Requests.** CDP Fetch interception pauses every request. It lets through only
  the saved file itself; everything else fails and is recorded, navigations
  included. CDP's ``Network.setBlockedURLs`` is not enough: frame and object
  documents and a meta refresh escape it (plan 5, PB-2).
- **Defense in depth.** Every connection goes to a dead proxy and every host name
  fails to resolve, and network prediction is off, so a WebSocket or a speculative
  preconnect, which CDP cannot see, never leaves the machine.
- **Files.** The saved bytes are copied alone into an empty temporary directory and
  loaded from there.
- **Bounds.** Startup, navigation, capture, and shutdown are each bounded.

One limitation: Chrome's crash handler keeps its database in the user's
``Library/Application Support/Google/Chrome for Testing/Crashpad``, outside the
temporary profile. It holds crash reports only, and it exits with the browser.
"""

from dataclasses import dataclass

CAPTURE_POLICY = "isolated"
CAPTURE_POLICY_VERSION = "1"

SAVED_NAME = "document.html"
"""The saved file's name in its temporary directory."""


@dataclass(frozen=True)
class CapturePolicy:
    """Everything a capture under one policy version fixes."""

    name: str
    version: str
    arguments: tuple[str, ...]
    preferences: tuple[tuple[str, int], ...]
    viewport_width: int
    viewport_height: int
    device_scale_factor: int
    locale: str
    timezone: str
    startup_seconds: float
    navigation_seconds: float
    capture_seconds: float
    shutdown_seconds: float
    required_resource_types: frozenset[str]
    """CDP resource types whose absence makes a capture ``partial``."""


ISOLATED_1 = CapturePolicy(
    name=CAPTURE_POLICY,
    version=CAPTURE_POLICY_VERSION,
    arguments=(
        "--headless",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-sync",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-default-apps",
        "--mute-audio",
        "--hide-scrollbars",
        "--proxy-server=http://127.0.0.1:9",
        "--proxy-bypass-list=<-loopback>",
        "--host-resolver-rules=MAP * ~NOTFOUND",
        "--window-size=1280,1024",
        "--force-device-scale-factor=1",
        "--lang=en-US",
    ),
    preferences=(("net.network_prediction_options", 2),),
    viewport_width=1280,
    viewport_height=1024,
    device_scale_factor=1,
    locale="en-US",
    timezone="UTC",
    startup_seconds=30.0,
    navigation_seconds=30.0,
    capture_seconds=60.0,
    shutdown_seconds=10.0,
    required_resource_types=frozenset({"Stylesheet", "Font"}),
)
```

Create `packages/earnings-ingestion/src/earnings_ingestion/browser/metadata.py`:

```python
"""The layout-metadata script: the capture's own extractor (metadata version 1).

The script runs in the page through WebDriver while document JavaScript stays
disabled; it only reads the DOM and computed style. It emits one block for the runs a
block element holds directly, flushing where a nested block starts, as the walker
does (W2). A ``<pre>`` element's whole content is one block, tables left out, as the
walker's W5 reads it. Each run is one text node's raw DOM text with its computed
style, so text-transform never alters it; a ``<br>`` is a run of its own. A block
outside every table cell whose runs hold only whitespace is not emitted: it has no
text for layout-1. Inside a cell such a block stays, because it separates the words
of the cell's other blocks.

Content with computed ``display: none`` is skipped, and so is ``noscript``: it
renders only because the capture disables scripts, and a reader's browser hides it.
Each table records its own rendered rows (whether each sits in ``thead``), their
rendered cells (whether each is a ``th``, and its spans), and the cell of another
table that holds it, if any.

Any change to the script, or to how ``parse_metadata`` reads it, is a new
``METADATA_VERSION``: captures made by different scripts never share a cache key.
"""

from collections.abc import Mapping
from typing import Any

from earnings_ingestion.browser.records import (
    LayoutBlock,
    LayoutCell,
    LayoutMetadata,
    LayoutRow,
    LayoutRun,
    LayoutTable,
)

METADATA_VERSION = "layout-metadata-1"

METADATA_SCRIPT = r"""
const BLOCK_DISPLAYS = new Set([
  "block", "list-item", "table", "table-row-group", "table-header-group",
  "table-footer-group", "table-row", "table-cell", "table-caption", "flex", "grid",
  "flow-root",
]);
const RESETS = new Set(["td", "th", "caption", "table", "ul", "ol", "pre"]);
const styles = new Map();
function style(el) {
  let s = styles.get(el);
  if (s === undefined) {
    s = getComputedStyle(el);
    styles.set(el, s);
  }
  return s;
}
function rendered(el) {
  return el.getClientRects().length > 0;
}
const tables = [];
const cells = new Map();
function enclosing(node) {
  for (let up = node.parentElement; up !== null; up = up.parentElement) {
    if (cells.has(up)) return cells.get(up);
    if (up === document.body) break;
  }
  return null;
}
for (const table of document.body.querySelectorAll("table")) {
  if (!rendered(table)) continue;
  const index = tables.length;
  const parent = enclosing(table);
  const rows = [];
  for (const tr of table.querySelectorAll("tr")) {
    if (tr.closest("table") !== table || !rendered(tr)) continue;
    const row = [];
    for (const cell of tr.cells) {
      if (!rendered(cell)) continue;
      cells.set(cell, [index, rows.length, row.length]);
      row.push({
        header: cell.tagName === "TH",
        colspan: Math.max(1, cell.colSpan),
        rowspan: Math.max(1, cell.rowSpan),
      });
    }
    const head = tr.parentElement !== null && tr.parentElement.tagName === "THEAD";
    rows.push({head: head, cells: row});
  }
  tables.push({
    parent_table: parent === null ? null : parent[0],
    parent_row: parent === null ? null : parent[1],
    parent_cell: parent === null ? null : parent[2],
    rows: rows,
  });
}
function context(owner) {
  let heading = null;
  let listItem = false;
  let decided = false;
  let depth = 0;
  let cell = null;
  for (let node = owner; node !== null; node = node.parentElement) {
    const tag = node.tagName.toLowerCase();
    if (!decided) {
      if (/^h[1-6]$/.test(tag)) {
        heading = Number(tag[1]);
        decided = true;
      } else if (tag === "li") {
        listItem = true;
        decided = true;
      } else if (RESETS.has(tag)) {
        decided = true;
      }
    }
    if (tag === "ul" || tag === "ol") depth += 1;
    if (cell === null && cells.has(node)) cell = cells.get(node);
    if (node === document.body) break;
  }
  return {heading, listItem, depth, cell};
}
function underlined(el) {
  for (let node = el; node !== null; node = node.parentElement) {
    if (style(node).textDecorationLine.includes("underline")) return true;
    if (node === document.body) break;
  }
  return false;
}
function raised(el, owner) {
  for (let node = el; node !== null; node = node.parentElement) {
    if (style(node).verticalAlign === "super") return true;
    if (node === owner || node === document.body) break;
  }
  return false;
}
function textRun(node, owner) {
  const el = node.parentElement;
  const s = style(el);
  const range = document.createRange();
  range.selectNodeContents(node);
  return {
    text: node.data,
    br: false,
    visible: s.visibility === "visible" && range.getClientRects().length > 0,
    bold: Number.parseInt(s.fontWeight, 10) >= 600,
    underline: underlined(el),
    superscript: raised(el, owner),
    symbol_font: /wingdings|symbol/i.test(s.fontFamily),
    font_size: Number.parseFloat(s.fontSize),
  };
}
function breakRun(el) {
  const s = style(el);
  return {
    text: "\n", br: true, visible: rendered(el), bold: false, underline: false,
    superscript: false, symbol_font: false, font_size: Number.parseFloat(s.fontSize),
  };
}
const blocks = [];
function flush(owner, runs) {
  if (runs.length === 0) return;
  const ctx = context(owner);
  if (ctx.cell === null && runs.every((run) => !/\S/.test(run.text))) {
    runs.length = 0;
    return;
  }
  const box = owner.getBoundingClientRect();
  blocks.push({
    tag: owner.tagName.toLowerCase(),
    display: style(owner).display,
    heading_level: ctx.heading,
    list_item: ctx.listItem,
    list_depth: ctx.depth,
    table: ctx.cell === null ? null : ctx.cell[0],
    row: ctx.cell === null ? null : ctx.cell[1],
    cell: ctx.cell === null ? null : ctx.cell[2],
    x: Math.round(box.x + window.scrollX),
    y: Math.round(box.y + window.scrollY),
    width: Math.round(box.width),
    height: Math.round(box.height),
    runs: runs.splice(0),
  });
}
function preRuns(el, owner, runs) {
  for (const child of el.childNodes) {
    if (child.nodeType === Node.TEXT_NODE) {
      if (child.data) runs.push(textRun(child, owner));
    } else if (child.nodeType === Node.ELEMENT_NODE) {
      const tag = child.tagName.toLowerCase();
      if (tag === "br") {
        const run = breakRun(child);
        run.br = false;
        runs.push(run);
      } else if (tag !== "table" && style(child).display !== "none") {
        preRuns(child, owner, runs);
      }
    }
  }
}
function walkBlock(el) {
  const runs = [];
  if (el.tagName.toLowerCase() === "pre") {
    preRuns(el, el, runs);
    flush(el, runs);
    return;
  }
  walkContent(el, el, runs);
  flush(el, runs);
}
function walkContent(el, owner, runs) {
  for (const child of el.childNodes) {
    if (child.nodeType === Node.TEXT_NODE) {
      if (child.data) runs.push(textRun(child, owner));
      continue;
    }
    if (child.nodeType !== Node.ELEMENT_NODE) continue;
    const tag = child.tagName.toLowerCase();
    if (tag === "br") {
      runs.push(breakRun(child));
      continue;
    }
    const display = style(child).display;
    if (display === "none" || tag === "noscript") continue;
    if (BLOCK_DISPLAYS.has(display) || tag === "pre") {
      flush(owner, runs);
      walkBlock(child);
      continue;
    }
    walkContent(child, owner, runs);
  }
}
walkBlock(document.body);
return {blocks: blocks, tables: tables};
"""
"""Returns ``{"blocks": [...], "tables": [...]}`` for ``parse_metadata``."""


def parse_metadata(payload: Mapping[str, Any]) -> LayoutMetadata:
    """The script's result as records; malformed output raises ``ValueError``."""
    try:
        blocks = tuple(
            LayoutBlock(
                **{key: value for key, value in block.items() if key != "runs"},
                runs=tuple(LayoutRun(**run) for run in block["runs"]),
            )
            for block in payload["blocks"]
        )
        tables = tuple(
            LayoutTable(
                **{key: value for key, value in table.items() if key != "rows"},
                rows=tuple(
                    LayoutRow(
                        head=row["head"],
                        cells=tuple(LayoutCell(**cell) for cell in row["cells"]),
                    )
                    for row in table["rows"]
                ),
            )
            for table in payload["tables"]
        )
    except (KeyError, TypeError) as error:
        raise ValueError(f"malformed layout metadata: {error!r}") from error
    return LayoutMetadata(blocks=blocks, tables=tables)
```

Create `packages/earnings-ingestion/src/earnings_ingestion/browser/renderer.py`:

```python
"""The public capture interface (B1), with no browser import.

``BrowserRenderer.capture(saved_html, capture_policy, *, source_document_id)``
returns a ``RenderedCapture``. The Selenium adapter in ``selenium_capture``
implements it behind the ``browser-capture`` extra; ``FakeRenderer`` serves default
tests. The cache key covers the raw hash, the policy, the browser, driver, and
Selenium, the platform and render configuration, and the metadata script's version
and text, and never a timestamp, so an exact key can be reused without starting a
browser, and a changed script can never reuse an old capture.
"""

import json
import platform
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Protocol

from earnings_core import sha256_hex

from earnings_ingestion.browser.metadata import METADATA_SCRIPT, METADATA_VERSION
from earnings_ingestion.browser.policy import CapturePolicy
from earnings_ingestion.browser.records import (
    CaptureReason,
    CaptureStatus,
    LayoutMetadata,
    RenderedCapture,
    layout_hash,
)

EMPTY_LAYOUT = LayoutMetadata(blocks=(), tables=())


@dataclass(frozen=True)
class CaptureEnvironment:
    """The browser, driver, library, and platform a capture runs under."""

    browser_engine: str
    browser_version: str
    driver_version: str
    selenium_version: str
    os_name: str
    os_version: str
    architecture: str

    @property
    def font_set(self) -> str:
        """Fonts are the platform's own; its release identifies them."""
        return f"{self.os_name} {self.os_version} system fonts"


def this_platform() -> tuple[str, str, str]:
    """(os_name, os_version, architecture) of the running machine."""
    name = platform.system()
    version = platform.mac_ver()[0] if name == "Darwin" else platform.release()
    return name, version, platform.machine()


def cache_key(
    raw_sha256: str, policy: CapturePolicy, environment: CaptureEnvironment
) -> str:
    """SHA-256 of every input that can change a capture; never a timestamp."""
    fields = {
        "raw_sha256": raw_sha256,
        "capture_policy": policy.name,
        "capture_policy_version": policy.version,
        "metadata_version": METADATA_VERSION,
        "metadata_script_sha256": sha256_hex(METADATA_SCRIPT.encode("utf-8")),
        "viewport_width": policy.viewport_width,
        "viewport_height": policy.viewport_height,
        "device_scale_factor": policy.device_scale_factor,
        "locale": policy.locale,
        "timezone": policy.timezone,
        **asdict(environment),
    }
    payload = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return sha256_hex(payload.encode("ascii"))


def capture_id(source_document_id: str, policy: CapturePolicy, key: str) -> str:
    """A readable, stable identifier: ``<source>@<policy>-<version>#<key prefix>``."""
    return f"{source_document_id}@{policy.name}-{policy.version}#{key[:16]}"


class BrowserRenderer(Protocol):
    """Renders a saved source under a capture policy (B1).

    ``environment`` is known before any capture, so a cache key can be looked up
    without starting a browser.
    """

    environment: CaptureEnvironment

    def capture(
        self,
        saved_html: bytes,
        capture_policy: CapturePolicy,
        *,
        source_document_id: str,
    ) -> RenderedCapture: ...


def unrendered(
    saved_html: bytes,
    capture_policy: CapturePolicy,
    environment: CaptureEnvironment,
    *,
    source_document_id: str,
    status: CaptureStatus,
    reason: CaptureReason,
    detail: str,
    captured_at: datetime | None = None,
    duration_seconds: float = 0.0,
) -> RenderedCapture:
    """A failed or unavailable capture: it holds no text, layout, or screenshot."""
    raw_sha256 = sha256_hex(saved_html)
    key = cache_key(raw_sha256, capture_policy, environment)
    return RenderedCapture(
        capture_id=capture_id(source_document_id, capture_policy, key),
        cache_key=key,
        source_document_id=source_document_id,
        raw_sha256=raw_sha256,
        capture_policy=capture_policy.name,
        capture_policy_version=capture_policy.version,
        metadata_version=METADATA_VERSION,
        browser_engine=environment.browser_engine,
        browser_version=environment.browser_version,
        driver_version=environment.driver_version,
        selenium_version=environment.selenium_version,
        os_name=environment.os_name,
        os_version=environment.os_version,
        architecture=environment.architecture,
        viewport_width=capture_policy.viewport_width,
        viewport_height=capture_policy.viewport_height,
        device_scale_factor=capture_policy.device_scale_factor,
        locale=capture_policy.locale,
        timezone=capture_policy.timezone,
        font_set=environment.font_set,
        document_charset="",
        script_policy="disabled",
        network_policy="blocked",
        image_policy="blocked",
        missing_resource_policy="recorded",
        rendered_text="",
        rendered_text_sha256=sha256_hex(b""),
        layout=EMPTY_LAYOUT,
        layout_sha256=layout_hash(EMPTY_LAYOUT),
        screenshots=(),
        blocked_requests=(),
        captured_at=captured_at or datetime.now(UTC),
        duration_seconds=duration_seconds,
        status=status,
        reason=reason,
        detail=detail,
    )


class FakeRenderer:
    """Returns saved captures by raw hash, and ``unavailable`` for anything else.

    It starts no browser and touches no network: default tests use it wherever code
    takes a ``BrowserRenderer``.
    """

    def __init__(
        self, captures: Mapping[str, RenderedCapture], environment: CaptureEnvironment
    ) -> None:
        self._captures = dict(captures)
        self.environment = environment

    def capture(
        self,
        saved_html: bytes,
        capture_policy: CapturePolicy,
        *,
        source_document_id: str,
    ) -> RenderedCapture:
        found = self._captures.get(sha256_hex(saved_html))
        if found is not None:
            return found
        return unrendered(
            saved_html,
            capture_policy,
            self.environment,
            source_document_id=source_document_id,
            status=CaptureStatus.UNAVAILABLE,
            reason=CaptureReason.BROWSER_UNAVAILABLE,
            detail="the fake renderer holds no capture of these bytes",
        )
```

Create `packages/earnings-ingestion/src/earnings_ingestion/browser/__init__.py`:

```python
"""The browser diagnostic path's capture side (Stage 3, plan B).

Importing this package loads no browser library: only ``selenium_capture`` imports
Selenium, and only the ``browser-capture`` extra installs it.
"""

from earnings_ingestion.browser.policy import ISOLATED_1, CapturePolicy
from earnings_ingestion.browser.records import (
    BlockedRequest,
    CaptureReason,
    CaptureStatus,
    LayoutBlock,
    LayoutCell,
    LayoutMetadata,
    LayoutRow,
    LayoutRun,
    LayoutTable,
    RenderedCapture,
)
from earnings_ingestion.browser.renderer import (
    BrowserRenderer,
    CaptureEnvironment,
    FakeRenderer,
)

__all__ = [
    "ISOLATED_1",
    "BlockedRequest",
    "BrowserRenderer",
    "CaptureEnvironment",
    "CapturePolicy",
    "CaptureReason",
    "CaptureStatus",
    "FakeRenderer",
    "LayoutBlock",
    "LayoutCell",
    "LayoutMetadata",
    "LayoutRow",
    "LayoutRun",
    "LayoutTable",
    "RenderedCapture",
]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_browser_records.py packages/earnings-ingestion/tests/test_browser_renderer.py -q`

Expected: `19 passed`.

- [ ] **Step 5: Extend the drift test to the capture records**

Replace `tests/contracts/test_data_dictionary.py` with:

```python
"""docs/data-dictionary.md documents every field and value of the core contracts
and of the ingestion records: the canonicalizer's and the capture's.

AGENTS.md §191: document public interfaces and update the data dictionary in the
same change. A contract that gains, loses, or renames a field fails here.
"""

import re
from enum import StrEnum
from pathlib import Path

import earnings_core as core
import earnings_ingestion.canonical as ingestion
import pytest
from earnings_ingestion import browser
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

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: `10 failed, 22 passed`: the eight new models' fields and the two new enums' values are not documented yet.

- [ ] **Step 6: Document the capture records**

Append to `docs/data-dictionary.md`:

```markdown

## earnings-ingestion browser and layout records, schema version 1

- **Packages.** `earnings_ingestion.browser` (the capture) and
  `earnings_ingestion.layout` (layout-1 and its mapping), in
  `packages/earnings-ingestion` (Stage 3, plan 5).
- **Schema version.** These records join ingestion schema version `1`: no earlier
  record's fields changed. `RenderedCapture`, `AlignmentFailure`, and
  `LayoutExtraction` carry it as `schema_version`; the nested parts do not.
- **Diagnostic provenance.** A capture establishes what the pinned browser displayed
  under a recorded policy. It is never a canonical span and never evidence of a quote
  (B2): every layout-1 span comes from matching canonical text, never from a DOM
  offset.
- **Fixture captures.** `tests/fixtures/browser/<name>.capture.json` is one JSON
  object with the keys `blocks` (the layout's `LayoutBlock` records), `capture` (the
  `RenderedCapture` without its layout), and `tables` (the `LayoutTable` records).
  Keys are sorted, non-ASCII characters are escaped, and each record is one line.
  `earnings_ingestion.browser.serialize.from_capture_json` reads one back and
  rechecks both hashes. Screenshots are never committed.

### `RenderedCapture`

One capture of one saved source under one capture policy (B1, B2, B7). A `failed` or
`unavailable` capture holds no text, layout, or screenshot.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `capture_id` | string | `<source_document_id>@<policy>-<version>#<first 16 hex of cache_key>` |
| `cache_key` | 64 lowercase hex | SHA-256 over the raw hash, the policy and its version, the metadata script's version and text, the render configuration, and the browser, driver, Selenium, and platform; never a timestamp |
| `source_document_id` | ID part | The saved source document |
| `raw_sha256` | 64 lowercase hex | SHA-256 of the saved bytes |
| `capture_policy` | ID part | The capture policy's name, `isolated` |
| `capture_policy_version` | ID part | Its version, `1` |
| `metadata_version` | ID part | The layout-metadata script, `layout-metadata-1` |
| `browser_engine` | string | `Chrome for Testing` |
| `browser_version` | string | The pinned browser version, or `none` when none is installed |
| `driver_version` | string | The pinned chromedriver version, or `none` |
| `selenium_version` | string | Selenium's version |
| `os_name` | string | `platform.system()`, such as `Darwin` |
| `os_version` | string | The operating system's release |
| `architecture` | string | `platform.machine()`, such as `arm64` |
| `viewport_width` | int > 0 | Window width in CSS pixels |
| `viewport_height` | int > 0 | Window height in CSS pixels |
| `device_scale_factor` | int > 0 | Device pixels per CSS pixel |
| `locale` | string | The browser's language, `en-US` |
| `timezone` | string | The emulated time zone, `UTC` |
| `font_set` | string | The platform's system fonts, named by its release |
| `document_charset` | string | `document.characterSet`: the encoding the browser used; empty when nothing rendered |
| `script_policy` | string | `disabled`: document JavaScript never runs |
| `network_policy` | string | `blocked`: every request but the saved file is refused and recorded |
| `image_policy` | string | `blocked`: images are refused like any request |
| `missing_resource_policy` | string | `recorded`: a blocked resource is listed, and a required one makes the capture `partial` |
| `rendered_text` | string | `document.body.innerText`, exactly as returned |
| `rendered_text_sha256` | 64 lowercase hex | SHA-256 of its UTF-8 bytes |
| `layout` | `LayoutMetadata` | The layout-metadata script's result |
| `layout_sha256` | 64 lowercase hex | SHA-256 of the layout as ASCII JSON with sorted keys and no spaces |
| `screenshots` | tuple of `ArtifactRef` | Content-hashed PNG tiles, `local_only` under `data/runs/` |
| `blocked_requests` | tuple of `BlockedRequest` | Each distinct refused request once, sorted by URL and type |
| `captured_at` | aware datetime | When the capture started; never part of the cache key |
| `duration_seconds` | float ≥ 0 | How long it took |
| `status` | `CaptureStatus` | The outcome |
| `reason` | `CaptureReason`, or null | Why it is not `completed`: null exactly when `completed` |
| `detail` | string | What failed, or which required resources were blocked |

### `CaptureStatus`

| Value | Meaning |
| --- | --- |
| `completed` | Every resource the rendering needs was present |
| `partial` | Rendered, but a blocked stylesheet, font, or frame may have changed it; the reason is `blocked_required_resource` |
| `failed` | The browser ran, and no usable rendering came back |
| `unavailable` | No pinned browser could run here |

### `CaptureReason`

| Value | Meaning |
| --- | --- |
| `browser_unavailable` | The pinned browser or driver is not installed, or none is pinned for this platform |
| `startup_failure` | The browser or driver did not start, or is not the pinned version |
| `timeout` | Startup, navigation, or capture ran past its bound |
| `blocked_required_resource` | A stylesheet, font, or frame the page asked for was blocked |
| `document_load_failure` | The saved file did not load, or the page left it |
| `capture_failure` | Reading text, layout, or a screenshot failed, or request interception stopped |

### `BlockedRequest`

| Field | Type | Meaning |
| --- | --- | --- |
| `url` | string | The requested URL |
| `resource_type` | string | CDP's resource type, such as `Image`, `Stylesheet`, or `Document` |
| `required` | bool | A stylesheet, font, or subframe document: its absence makes the capture `partial` |

### `LayoutMetadata`

| Field | Type | Meaning |
| --- | --- | --- |
| `blocks` | tuple of `LayoutBlock` | Every block of the rendered body, in document order |
| `tables` | tuple of `LayoutTable` | Every rendered table, in document order; blocks and tables refer to tables by index here |

### `LayoutBlock`

The runs one block element holds directly, split where a nested block starts (W2's
analog). Content with computed `display: none`, and `noscript`, is left out.

| Field | Type | Meaning |
| --- | --- | --- |
| `tag` | string | The block element's tag, lowercase |
| `display` | string | Its computed `display` |
| `heading_level` | int > 0, or null | 1–6 when the nearest heading or list-item ancestor is `h1`–`h6` |
| `list_item` | bool | The nearest such ancestor is an `li` |
| `list_depth` | int ≥ 0 | How many `ul` and `ol` elements enclose it |
| `table` | int ≥ 0, or null | The table holding its nearest enclosing cell |
| `row` | int ≥ 0, or null | That cell's row among the table's own rendered rows |
| `cell` | int ≥ 0, or null | That cell's position among the row's rendered cells |
| `x` | int | Left edge in CSS pixels, from the page's origin |
| `y` | int | Top edge in CSS pixels, from the page's origin |
| `width` | int ≥ 0 | Width in CSS pixels |
| `height` | int ≥ 0 | Height in CSS pixels |
| `runs` | tuple of `LayoutRun` | Its text runs and line breaks, in document order |

### `LayoutRun`

One text node's raw DOM text with its computed style, or one `<br>`. The text is the
node's own, so a CSS `text-transform` never alters it.

| Field | Type | Meaning |
| --- | --- | --- |
| `text` | string | The node's text, or `"\n"` for a `<br>` |
| `br` | bool | A `<br>` outside `<pre>`; inside `<pre>` a `<br>` is a text run of `"\n"` |
| `visible` | bool | Computed `visibility: visible` and at least one rendered box |
| `bold` | bool | Computed `font-weight` of 600 or more |
| `underline` | bool | An underline decoration on it or any ancestor |
| `superscript` | bool | `vertical-align: super` on it or an ancestor inside its block |
| `symbol_font` | bool | A Wingdings or Symbol `font-family` |
| `font_size` | float ≥ 0 | Computed `font-size` in CSS pixels |

### `LayoutTable`

A rendered table's own rows, and the cell of another table that holds it.

| Field | Type | Meaning |
| --- | --- | --- |
| `parent_table` | int ≥ 0, or null | The table of the nearest enclosing cell; null for a table in no cell |
| `parent_row` | int ≥ 0, or null | That cell's row |
| `parent_cell` | int ≥ 0, or null | That cell's position in its row |
| `rows` | tuple of `LayoutRow` | The table's own rendered rows, in document order |

### `LayoutRow`

| Field | Type | Meaning |
| --- | --- | --- |
| `head` | bool | The row sits in a `thead` |
| `cells` | tuple of `LayoutCell` | Its rendered cells, in document order |

### `LayoutCell`

| Field | Type | Meaning |
| --- | --- | --- |
| `header` | bool | The cell is a `th` |
| `colspan` | int > 0 | Its `colSpan`, at least 1 |
| `rowspan` | int > 0 | Its `rowSpan`, at least 1 |
```

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: `32 passed`.

- [ ] **Step 7: Run the checks**

```bash
python3 /tmp/plan5-escapes.py packages/earnings-ingestion/src/earnings_ingestion/browser/*.py packages/earnings-ingestion/tests/conftest.py packages/earnings-ingestion/tests/test_browser_*.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `524 passed`; `All checks passed!` and `124 files already formatted`.

- [ ] **Step 8: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/browser packages/earnings-ingestion/tests/conftest.py packages/earnings-ingestion/tests/test_browser_records.py packages/earnings-ingestion/tests/test_browser_renderer.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(ingestion): add the capture records, isolated/1, and the renderer interface"
```

---
### Task 3: The capture store and the fixture format

Two ways to keep a capture:

- **The store.** Under the gitignored `data/runs/browser-capture/`, captures are
  written atomically and never overwritten, with screenshots (PB-8).
  `capture_once` asks the store before it asks a renderer, so an exact cache key
  never starts a browser twice.
- **The fixture format.** The committed captures in `tests/fixtures/browser/` use it
  (PB-7). It puts one layout block or table per line and escapes everything
  non-ASCII, so a diff shows which blocks changed and no tool can alter a character.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/browser/store.py`,
  `serialize.py`.
- Modify: `packages/earnings-ingestion/src/earnings_ingestion/browser/__init__.py`
  (replaced whole, block 2 of 2: the store joins the public API).
- Test (create): `packages/earnings-ingestion/tests/test_browser_store.py`,
  `test_browser_serialize.py`.

**Interfaces:**

- Consumes: Task 2's records, `cache_key`, `BrowserRenderer`, `FakeRenderer` and
  `unrendered`; `earnings_core.ArtifactRef` and `RightsStatus`.
- Produces:
  - `store.py`:
    - `CaptureStore(root: Path, repo: Path)`, with `reuse(key) -> RenderedCapture | None`,
      `put(capture) -> Path`, and `screenshot(png: bytes) -> ArtifactRef` (rights
      `local_only`);
    - `capture_once(renderer, store, saved_html, policy, *, source_document_id) -> RenderedCapture`;
    - `USABLE`.
  - `serialize.py`: `to_capture_json(capture) -> str` and
    `from_capture_json(text) -> RenderedCapture`.
  - `earnings_ingestion.browser` also exports `CaptureStore` and `capture_once`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_browser_store.py`:

```python
"""Captures on disk: atomic, never overwritten, and reused only by an exact key."""

from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.browser.policy import ISOLATED_1
from earnings_ingestion.browser.records import CaptureReason, CaptureStatus
from earnings_ingestion.browser.renderer import (
    CaptureEnvironment,
    FakeRenderer,
    unrendered,
)
from earnings_ingestion.browser.store import CaptureStore, capture_once

ENVIRONMENT = CaptureEnvironment(
    browser_engine="Chrome for Testing",
    browser_version="154.0.8037.57",
    driver_version="154.0.8037.57",
    selenium_version="4.49.0",
    os_name="Darwin",
    os_version="26.6.2",
    architecture="arm64",
)
RAW = b"<p>Revenue rose.</p>"


def store_in(tmp_path: Path) -> CaptureStore:
    return CaptureStore(tmp_path / "data" / "runs" / "browser-capture", tmp_path)


def failed(status: CaptureStatus = CaptureStatus.FAILED):
    return unrendered(
        RAW,
        ISOLATED_1,
        ENVIRONMENT,
        source_document_id="release",
        status=status,
        reason=CaptureReason.TIMEOUT,
        detail="navigation ran past 30 s",
    )


class Counting(FakeRenderer):
    def __init__(self, record) -> None:
        super().__init__({sha256_hex(RAW): record}, ENVIRONMENT)
        self.calls = 0

    def capture(self, saved_html, capture_policy, *, source_document_id):
        self.calls += 1
        return super().capture(
            saved_html, capture_policy, source_document_id=source_document_id
        )


def test_a_failed_capture_is_kept_but_never_reused(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    record = failed()
    path = store.put(record)
    assert path.parent == store.root / "failures" / record.cache_key
    assert store.reuse(record.cache_key) is None


def test_a_usable_capture_is_reused_by_its_key(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    record = failed().model_copy(
        update={"status": CaptureStatus.COMPLETED, "reason": None, "detail": ""}
    )
    path = store.put(record)
    assert path == store.root / "captures" / f"{record.cache_key}.json"
    assert store.reuse(record.cache_key) == record


def test_a_stored_capture_is_never_overwritten(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    record = failed().model_copy(
        update={"status": CaptureStatus.COMPLETED, "reason": None, "detail": ""}
    )
    path = store.put(record)
    before = path.read_bytes()
    assert store.put(record) == path
    later = record.model_copy(update={"duration_seconds": 9.0})
    with pytest.raises(FileExistsError, match="holds another record"):
        store.put(later)
    assert path.read_bytes() == before
    assert not list(path.parent.glob(".tmp-*"))


def test_screenshots_are_stored_by_content_hash(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    png = b"\x89PNG\r\n\x1a\n not really"
    reference = store.screenshot(png)
    assert reference == store.screenshot(png)
    assert reference.storage_ref == (
        f"data/runs/browser-capture/screenshots/{sha256_hex(png)}.png"
    )
    assert reference.rights_status is RightsStatus.LOCAL_ONLY
    assert (tmp_path / reference.storage_ref).read_bytes() == png


def test_capture_once_reuses_an_exact_key_without_rendering(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    record = failed().model_copy(
        update={"status": CaptureStatus.COMPLETED, "reason": None, "detail": ""}
    )
    renderer = Counting(record)
    first = capture_once(renderer, store, RAW, ISOLATED_1, source_document_id="release")
    second = capture_once(
        renderer, store, RAW, ISOLATED_1, source_document_id="release"
    )
    assert first == second == record
    assert renderer.calls == 1


def test_capture_once_renders_again_after_a_failure(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    renderer = Counting(failed())
    capture_once(renderer, store, RAW, ISOLATED_1, source_document_id="release")
    capture_once(renderer, store, RAW, ISOLATED_1, source_document_id="release")
    assert renderer.calls == 2
```

Create `packages/earnings-ingestion/tests/test_browser_serialize.py`:

```python
"""The fixture-capture format: one block per line, sorted keys, ASCII, exact round trip."""

import json
from collections.abc import Callable

from earnings_ingestion.browser.metadata import parse_metadata
from earnings_ingestion.browser.records import RenderedCapture
from earnings_ingestion.browser.serialize import from_capture_json, to_capture_json

Make = Callable[..., RenderedCapture]


def test_a_capture_round_trips_exactly(make_capture: Make) -> None:
    record = make_capture()
    assert from_capture_json(to_capture_json(record)) == record


def test_the_format_puts_each_block_on_its_own_line(
    make_capture: Make, payload: dict
) -> None:
    text = to_capture_json(make_capture())
    lines = text.splitlines()
    assert lines[0] == "{" and lines[-1] == "}"
    assert lines[1] == '"blocks": ['
    assert json.loads(lines[2]) == payload["blocks"][0]
    assert text.endswith("}\n")
    assert text.isascii()
    assert list(json.loads(text)) == ["blocks", "capture", "tables"]


def test_non_ascii_text_is_escaped(make_capture: Make, payload: dict) -> None:
    payload["blocks"][0]["runs"][0]["text"] = "Caf" + chr(0xE9)
    record = make_capture(
        layout=parse_metadata(payload), rendered_text="Caf" + chr(0xE9)
    )
    text = to_capture_json(record)
    assert text.isascii()
    assert from_capture_json(text) == record
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_browser_store.py packages/earnings-ingestion/tests/test_browser_serialize.py -q`

Expected: `2 errors during collection`, each a `ModuleNotFoundError`: no module named `earnings_ingestion.browser.store`, and none named `earnings_ingestion.browser.serialize`.

- [ ] **Step 3: Write the store, the format, and the public API**

Create `packages/earnings-ingestion/src/earnings_ingestion/browser/store.py`:

```python
"""Captures on disk under ``data/runs/``: written atomically, never overwritten (B2).

- A usable capture, ``completed`` or ``partial``, is stored by its cache key and
  reused for that key: a new run either reuses an exact key or writes a new capture.
- A failed or unavailable capture is kept for the record, under its key and time, and
  never reused.
- Screenshots are stored by content hash, so writing one twice is harmless.

Every write goes to a temporary file first. A hard link then puts it in place, which
fails rather than replace an existing file: writing the same bytes again is a no-op,
and different bytes raise ``FileExistsError``.
"""

import os
import tempfile
from pathlib import Path

from earnings_core import ArtifactRef, RightsStatus, sha256_hex

from earnings_ingestion.browser.policy import CapturePolicy
from earnings_ingestion.browser.records import CaptureStatus, RenderedCapture
from earnings_ingestion.browser.renderer import BrowserRenderer, cache_key

USABLE = frozenset({CaptureStatus.COMPLETED, CaptureStatus.PARTIAL})
SCREENSHOT_RIGHTS = "a rendering of a saved filing, kept local under data/runs/"


class CaptureStore:
    """``root`` lies under ``repo``'s ``data/runs/``; references are repo-relative."""

    def __init__(self, root: Path, repo: Path) -> None:
        self.root = root
        self.repo = repo

    def reuse(self, key: str) -> RenderedCapture | None:
        path = self.root / "captures" / f"{key}.json"
        if not path.is_file():
            return None
        return RenderedCapture.model_validate_json(path.read_text(encoding="utf-8"))

    def put(self, capture: RenderedCapture) -> Path:
        """Write ``capture``; ``FileExistsError`` if another record holds its file."""
        if capture.status in USABLE:
            path = self.root / "captures" / f"{capture.cache_key}.json"
        else:
            stamp = capture.captured_at.strftime("%Y%m%dT%H%M%S%fZ")
            path = self.root / "failures" / capture.cache_key / f"{stamp}.json"
        _write_new(path, capture.model_dump_json().encode("utf-8"))
        return path

    def screenshot(self, png: bytes) -> ArtifactRef:
        """Store one screenshot tile by its hash and return its reference."""
        digest = sha256_hex(png)
        path = self.root / "screenshots" / f"{digest}.png"
        _write_new(path, png)
        return ArtifactRef.for_bytes(
            png,
            media_type="image/png",
            storage_ref=path.relative_to(self.repo).as_posix(),
            rights_status=RightsStatus.LOCAL_ONLY,
            rights_basis=SCREENSHOT_RIGHTS,
        )


def capture_once(
    renderer: BrowserRenderer,
    store: CaptureStore,
    saved_html: bytes,
    policy: CapturePolicy,
    *,
    source_document_id: str,
) -> RenderedCapture:
    """The stored capture for this exact cache key, or a new one, stored."""
    key = cache_key(sha256_hex(saved_html), policy, renderer.environment)
    found = store.reuse(key)
    if found is not None:
        return found
    capture = renderer.capture(
        saved_html, policy, source_document_id=source_document_id
    )
    store.put(capture)
    return capture


def _write_new(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() == data:
            return
        raise FileExistsError(f"{path} holds another record")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
```

Create `packages/earnings-ingestion/src/earnings_ingestion/browser/serialize.py`:

```python
"""The committed fixture-capture format (plan 5, PB-7).

One JSON object with sorted keys: ``blocks``, ``capture``, and ``tables``. ``capture``
is the record without its layout; each layout block and table is one line. Every line
has sorted keys and ASCII escapes, so a diff shows which blocks changed and no editor
or tool can alter a character.
"""

import json

from earnings_ingestion.browser.records import RenderedCapture


def to_capture_json(capture: RenderedCapture) -> str:
    """``capture`` in the fixture format, ending with a newline."""
    record = capture.model_dump(mode="json")
    layout = record.pop("layout")
    lines = [
        "{",
        f'"blocks": {_rows(layout["blocks"])},',
        f'"capture": {_line(record)},',
        f'"tables": {_rows(layout["tables"])}',
        "}",
    ]
    return "\n".join(lines) + "\n"


def from_capture_json(text: str) -> RenderedCapture:
    """The capture a fixture file holds; its validators recheck both hashes."""
    data = json.loads(text)
    layout = {"blocks": data["blocks"], "tables": data["tables"]}
    return RenderedCapture.model_validate_json(
        json.dumps({**data["capture"], "layout": layout})
    )


def _line(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def _rows(values: list) -> str:
    if not values:
        return "[]"
    return "[\n" + ",\n".join(_line(value) for value in values) + "\n]"
```

Replace `packages/earnings-ingestion/src/earnings_ingestion/browser/__init__.py` with:

```python
"""The browser diagnostic path's capture side (Stage 3, plan B).

Importing this package loads no browser library: only ``selenium_capture`` imports
Selenium, and only the ``browser-capture`` extra installs it.
"""

from earnings_ingestion.browser.policy import ISOLATED_1, CapturePolicy
from earnings_ingestion.browser.records import (
    BlockedRequest,
    CaptureReason,
    CaptureStatus,
    LayoutBlock,
    LayoutCell,
    LayoutMetadata,
    LayoutRow,
    LayoutRun,
    LayoutTable,
    RenderedCapture,
)
from earnings_ingestion.browser.renderer import (
    BrowserRenderer,
    CaptureEnvironment,
    FakeRenderer,
)
from earnings_ingestion.browser.store import CaptureStore, capture_once

__all__ = [
    "ISOLATED_1",
    "BlockedRequest",
    "BrowserRenderer",
    "CaptureEnvironment",
    "CapturePolicy",
    "CaptureReason",
    "CaptureStatus",
    "CaptureStore",
    "FakeRenderer",
    "LayoutBlock",
    "LayoutCell",
    "LayoutMetadata",
    "LayoutRow",
    "LayoutRun",
    "LayoutTable",
    "RenderedCapture",
    "capture_once",
]
```

This is block 2 for that path: extract it with
`python3 /tmp/plan5-extract.py packages/earnings-ingestion/src/earnings_ingestion/browser/__init__.py 2`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_browser_store.py packages/earnings-ingestion/tests/test_browser_serialize.py -q`

Expected: `9 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan5-escapes.py packages/earnings-ingestion/src/earnings_ingestion/browser/*.py packages/earnings-ingestion/tests/test_browser_store.py packages/earnings-ingestion/tests/test_browser_serialize.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `533 passed`; `All checks passed!` and `128 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/browser/store.py packages/earnings-ingestion/src/earnings_ingestion/browser/serialize.py packages/earnings-ingestion/src/earnings_ingestion/browser/__init__.py packages/earnings-ingestion/tests/test_browser_store.py packages/earnings-ingestion/tests/test_browser_serialize.py
git commit -m "feat(ingestion): store captures atomically and define the capture-fixture format"
```

---
### Task 4: The pinned browser and `earnings-pipeline browser setup`

The pin is a committed manifest. The install is the one code path that downloads,
and it checks every byte before trusting it (PB-3). The application's CLI exposes it
as `earnings-pipeline browser setup` (PB-22). The tests install from local archives
that they build themselves: no test downloads anything.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/browser/install.py`,
  `chrome-for-testing.toml`.
- Create: `apps/earnings-pipeline/src/earnings_pipeline/cli.py`.
- Modify: `apps/earnings-pipeline/pyproject.toml` (replaced whole: a
  `[project.scripts]` table).
- Test (create): `packages/earnings-ingestion/tests/test_browser_install.py`,
  `apps/earnings-pipeline/tests/test_cli.py`.

**Interfaces:**

- Consumes: `httpx` (already a dependency of `earnings-ingestion`) and `typer`
  (already a dependency of `earnings-pipeline`).
- Produces, in `earnings_ingestion.browser.install`:
  - `MANIFEST = "chrome-for-testing.toml"` and
    `CACHE_VARIABLE = "EARNINGS_BROWSER_CACHE"`;
  - `Archive(name, url, size, sha256, executable)`, `Pin(version, platform, browser, driver)`,
    and `Binaries(browser: Path, driver: Path, version: str)` with `present()`;
  - `platform_name() -> str | None`;
  - `load_pin(name=None, text=None) -> Pin | None`;
  - `default_cache() -> Path`;
  - `installed(cache=None, pin=None) -> Binaries | None`, which never downloads;
  - `install(pin, cache, fetch) -> Binaries`, which raises `ValueError` on a wrong
    size, hash, or reported version;
  - `safe_extract(archive, destination)`, `reported_version(executable) -> str`, and
    `download(archive, path)`, the real `fetch`.
- Produces, in the application: `earnings_pipeline.cli.app`, a typer app with the
  command `browser setup [--cache PATH]`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_browser_install.py`:

```python
"""The pinned manifest, the setup command's install, and lookup, with no download.

The archives here are tiny zips whose "browser" and "driver" are shell scripts that
print a version, so every path runs offline in milliseconds.
"""

import hashlib
import stat
import zipfile
from pathlib import Path

import pytest
from earnings_ingestion.browser.install import (
    Archive,
    Pin,
    install,
    installed,
    load_pin,
    safe_extract,
)

BROWSER = "chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
DRIVER = "chromedriver-mac-arm64/chromedriver"


def script(version_line: str) -> bytes:
    return f"#!/bin/sh\necho '{version_line}'\n".encode("ascii")


def make_zip(path: Path, files: dict[str, bytes], links: dict[str, str] = {}) -> Path:  # noqa: B006
    with zipfile.ZipFile(path, "w") as zipped:
        for name, data in files.items():
            info = zipfile.ZipInfo(name)
            info.external_attr = (stat.S_IFREG | 0o755) << 16
            zipped.writestr(info, data)
        for name, target in links.items():
            info = zipfile.ZipInfo(name)
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zipped.writestr(info, target)
    return path


def archive_for(path: Path, name: str, executable: str) -> Archive:
    data = path.read_bytes()
    return Archive(
        name=name,
        url=f"https://example.invalid/{path.name}",
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        executable=executable,
    )


def pinned(tmp_path: Path, browser_says: str = "154.0.8037.57") -> tuple[Pin, dict]:
    browser_zip = make_zip(
        tmp_path / "chrome.zip",
        {BROWSER: script(f"Google Chrome for Testing {browser_says}")},
        {"chrome-mac-arm64/Google Chrome for Testing.app/Contents/Current": "MacOS"},
    )
    driver_zip = make_zip(
        tmp_path / "chromedriver.zip",
        {
            DRIVER: script(
                "ChromeDriver 154.0.8037.57 (abc-refs/branch-heads/8037@{#1})"
            )
        },
    )
    pin = Pin(
        version="154.0.8037.57",
        platform="mac-arm64",
        browser=archive_for(browser_zip, "chrome", BROWSER),
        driver=archive_for(driver_zip, "chromedriver", DRIVER),
    )
    return pin, {"chrome": browser_zip, "chromedriver": driver_zip}


def test_the_committed_manifest_pins_one_version_for_mac_arm64() -> None:
    pin = load_pin("mac-arm64")
    assert pin is not None
    assert pin.version == "154.0.8037.57"
    assert pin.browser.url.endswith("/154.0.8037.57/mac-arm64/chrome-mac-arm64.zip")
    assert pin.driver.url.endswith(
        "/154.0.8037.57/mac-arm64/chromedriver-mac-arm64.zip"
    )
    assert (pin.browser.size, pin.driver.size) == (191429663, 9302980)


def test_no_build_is_pinned_for_other_platforms() -> None:
    assert load_pin("linux64") is None


def test_nothing_is_installed_in_an_empty_cache(tmp_path: Path) -> None:
    pin, _ = pinned(tmp_path)
    assert installed(tmp_path / "cache", pin) is None


def test_install_checks_extracts_and_finds_the_binaries(tmp_path: Path) -> None:
    pin, zips = pinned(tmp_path)
    fetched: list[str] = []

    def fetch(archive: Archive, path: Path) -> None:
        fetched.append(archive.name)
        path.write_bytes(zips[archive.name].read_bytes())

    cache = tmp_path / "cache"
    binaries = install(pin, cache, fetch)
    assert binaries == installed(cache, pin)
    assert binaries.browser == cache / "154.0.8037.57" / "mac-arm64" / BROWSER
    link = binaries.browser.parents[1] / "Current"
    assert link.is_symlink() and link.readlink() == Path("MacOS")
    assert install(pin, cache, fetch) == binaries
    assert fetched == ["chrome", "chromedriver"]


def test_an_archive_that_is_not_the_pinned_one_is_refused(tmp_path: Path) -> None:
    pin, zips = pinned(tmp_path)

    def fetch(archive: Archive, path: Path) -> None:
        path.write_bytes(zips[archive.name].read_bytes() + b"tampered")

    with pytest.raises(ValueError, match="the manifest pins"):
        install(pin, tmp_path / "cache", fetch)
    assert installed(tmp_path / "cache", pin) is None


def test_a_binary_reporting_another_version_is_refused(tmp_path: Path) -> None:
    pin, zips = pinned(tmp_path, browser_says="153.0.0.0")

    def fetch(archive: Archive, path: Path) -> None:
        path.write_bytes(zips[archive.name].read_bytes())

    with pytest.raises(ValueError, match="reports '153.0.0.0'"):
        install(pin, tmp_path / "cache", fetch)
    assert installed(tmp_path / "cache", pin) is None


@pytest.mark.parametrize(
    ("files", "links", "message"),
    [
        ({"../escape": b"x"}, {}, "unsafe entry"),
        ({"/absolute": b"x"}, {}, "unsafe entry"),
        ({}, {"inside/link": "../../outside"}, "unsafe link"),
        ({}, {"inside/link": "/etc/passwd"}, "unsafe link"),
    ],
)
def test_extraction_never_writes_outside_its_directory(
    tmp_path: Path, files: dict, links: dict, message: str
) -> None:
    archive = make_zip(tmp_path / "bad.zip", files, links)
    destination = tmp_path / "out"
    destination.mkdir()
    with pytest.raises(ValueError, match=message):
        safe_extract(archive, destination)
```

Create `apps/earnings-pipeline/tests/test_cli.py`:

```python
"""The command line's browser setup, with the install replaced: no download here."""

from pathlib import Path

from earnings_ingestion.browser.install import Binaries, load_pin
from earnings_pipeline import cli
from typer.testing import CliRunner

RUNNER = CliRunner()


def test_setup_installs_the_pin_into_the_cache(monkeypatch, tmp_path: Path) -> None:
    calls = []

    def fake_install(pin, cache, fetch):
        calls.append((pin.version, cache, fetch))
        return Binaries(
            browser=cache / "chrome", driver=cache / "chromedriver", version=pin.version
        )

    monkeypatch.setattr(cli, "load_pin", lambda: load_pin("mac-arm64"))
    monkeypatch.setattr(cli, "install", fake_install)
    result = RUNNER.invoke(cli.app, ["browser", "setup", "--cache", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert calls == [("154.0.8037.57", tmp_path, cli.download)]
    assert "Chrome for Testing 154.0.8037.57 (mac-arm64)" in result.output
    assert f"driver: {tmp_path / 'chromedriver'}" in result.output


def test_setup_refuses_a_platform_with_no_pin(monkeypatch) -> None:
    monkeypatch.setattr(cli, "load_pin", lambda: None)
    result = RUNNER.invoke(cli.app, ["browser", "setup"])
    assert result.exit_code == 1
    assert "No Chrome for Testing build is pinned" in result.output


def test_setup_reports_a_refused_archive(monkeypatch, tmp_path: Path) -> None:
    def refuse(pin, cache, fetch):
        raise ValueError("chrome: got 3 bytes; the manifest pins 191429663")

    monkeypatch.setattr(cli, "load_pin", lambda: load_pin("mac-arm64"))
    monkeypatch.setattr(cli, "install", refuse)
    result = RUNNER.invoke(cli.app, ["browser", "setup", "--cache", str(tmp_path)])
    assert result.exit_code == 1
    assert "Refused: chrome: got 3 bytes" in result.output
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_browser_install.py apps/earnings-pipeline/tests/test_cli.py -q`

Expected: `2 errors during collection`: `ModuleNotFoundError: No module named 'earnings_ingestion.browser.install'`.

- [ ] **Step 3: Write the manifest and the install**

Create `packages/earnings-ingestion/src/earnings_ingestion/browser/chrome-for-testing.toml`:

```toml
# Chrome for Testing, pinned for the browser diagnostic path (plan 5, PB-3).
# `earnings-pipeline browser setup` downloads each archive, checks its size and
# SHA-256 against this file, and extracts it into a cache outside the repository.
# Checked at plan time on 2026-09-26: the Stable channel's version for mac-arm64.
version = "154.0.8037.57"

[[archives]]
platform = "mac-arm64"
name = "chrome"
url = "https://storage.googleapis.com/chrome-for-testing-public/154.0.8037.57/mac-arm64/chrome-mac-arm64.zip"
size = 191429663
sha256 = "0e6b3439469c1b8b95b2e89c72ea29f7af00fb2c28a8878358a0b6002b6d3a64"
executable = "chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

[[archives]]
platform = "mac-arm64"
name = "chromedriver"
url = "https://storage.googleapis.com/chrome-for-testing-public/154.0.8037.57/mac-arm64/chromedriver-mac-arm64.zip"
size = 9302980
sha256 = "97a96253f407512086744a953a3def997461fc7c37882b4f9cca297bab5f644e"
executable = "chromedriver-mac-arm64/chromedriver"
```

Create `packages/earnings-ingestion/src/earnings_ingestion/browser/install.py`:

```python
"""The pinned Chrome for Testing: its manifest, the setup command's install, and lookup.

``chrome-for-testing.toml`` beside this module pins one version, and for each platform
the URL, size, and SHA-256 of the browser and driver archives (B3, B8). ``install``
is the setup command's work and the only code in the project that downloads a
binary: it checks each archive's size and hash before extracting it, keeps the
archive's symlinks and executable bits, and moves the finished tree into place in one
rename, so a half-installed tree never looks installed. A capture only ever calls
``installed``, which downloads nothing.
"""

import hashlib
import os
import platform
import shutil
import stat
import subprocess
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from importlib import resources
from pathlib import Path, PurePosixPath

import httpx
import tomllib

MANIFEST = "chrome-for-testing.toml"
CACHE_VARIABLE = "EARNINGS_BROWSER_CACHE"


@dataclass(frozen=True)
class Archive:
    """One archive of the pinned build for one platform."""

    name: str
    url: str
    size: int
    sha256: str
    executable: str
    """The executable's path inside the extracted archive."""


@dataclass(frozen=True)
class Pin:
    """The pinned version and, for one platform, its two archives."""

    version: str
    platform: str
    browser: Archive
    driver: Archive


@dataclass(frozen=True)
class Binaries:
    """The pinned browser and driver executables, and the version both must report."""

    browser: Path
    driver: Path
    version: str

    def present(self) -> bool:
        return self.browser.is_file() and self.driver.is_file()


def platform_name() -> str | None:
    """Chrome for Testing's name for this machine, where the manifest may pin one."""
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return "mac-arm64"
    return None


def load_pin(name: str | None = None, text: str | None = None) -> Pin | None:
    """The manifest's pin for platform ``name`` (this machine's by default), or
    ``None`` when the manifest pins no build for it."""
    name = platform_name() if name is None else name
    if text is None:
        text = (
            resources.files(__package__).joinpath(MANIFEST).read_text(encoding="utf-8")
        )
    manifest = tomllib.loads(text)
    archives = {
        entry["name"]: Archive(
            name=entry["name"],
            url=entry["url"],
            size=entry["size"],
            sha256=entry["sha256"],
            executable=entry["executable"],
        )
        for entry in manifest["archives"]
        if entry["platform"] == name
    }
    if name is None or set(archives) != {"chrome", "chromedriver"}:
        return None
    return Pin(manifest["version"], name, archives["chrome"], archives["chromedriver"])


def default_cache() -> Path:
    """``$EARNINGS_BROWSER_CACHE`` if set, else the user's cache directory; either way
    outside the repository. The version check still applies to whatever it holds."""
    override = os.environ.get(CACHE_VARIABLE)
    if override:
        return Path(override)
    return Path.home() / "Library" / "Caches" / "earnings-themes" / "chrome-for-testing"


def installed(cache: Path | None = None, pin: Pin | None = None) -> Binaries | None:
    """The installed pinned binaries, or ``None``; never downloads anything."""
    pin = load_pin() if pin is None else pin
    if pin is None:
        return None
    root = (default_cache() if cache is None else cache) / pin.version / pin.platform
    binaries = Binaries(
        browser=root / pin.browser.executable,
        driver=root / pin.driver.executable,
        version=pin.version,
    )
    return binaries if binaries.present() else None


Fetch = Callable[[Archive, Path], None]
"""Writes one archive's bytes to a path; ``download`` in the setup command, a local
copy in tests."""


def install(pin: Pin, cache: Path, fetch: Fetch) -> Binaries:
    """Download, check, and extract both archives; return the installed binaries.

    Raises ``ValueError`` when an archive's size or hash is not the manifest's, or an
    extracted executable does not report the pinned version.
    """
    done = installed(cache, pin)
    if done is not None:
        return done
    target = cache / pin.version / pin.platform
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent, prefix=".install-") as scratch:
        staging = Path(scratch) / "tree"
        staging.mkdir()
        for archive in (pin.browser, pin.driver):
            path = Path(scratch) / f"{archive.name}.zip"
            fetch(archive, path)
            _check(archive, path)
            safe_extract(path, staging)
        binaries = Binaries(
            browser=staging / pin.browser.executable,
            driver=staging / pin.driver.executable,
            version=pin.version,
        )
        for executable in (binaries.browser, binaries.driver):
            reported = reported_version(executable)
            if reported != pin.version:
                raise ValueError(
                    f"{executable.name} reports {reported!r}, not {pin.version}"
                )
        if target.exists():
            shutil.rmtree(target)
        os.rename(staging, target)
    done = installed(cache, pin)
    assert done is not None
    return done


def _check(archive: Archive, path: Path) -> None:
    size = path.stat().st_size
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1 << 20):
            digest.update(chunk)
    if size != archive.size or digest.hexdigest() != archive.sha256:
        raise ValueError(
            f"{archive.name}: got {size} bytes with SHA-256 {digest.hexdigest()};"
            f" the manifest pins {archive.size} bytes with {archive.sha256}"
        )


def safe_extract(archive: Path, destination: Path) -> None:
    """Extract ``archive`` into ``destination``, keeping symlinks and executable bits.

    An absolute entry, a ``..`` segment, or a symlink that leaves ``destination``
    raises ``ValueError``: the hash already vouches for the archive, and this is the
    second line of defence.
    """
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        for info in zipped.infolist():
            name = PurePosixPath(info.filename)
            if name.is_absolute() or ".." in name.parts:
                raise ValueError(f"unsafe entry {info.filename!r}")
            target = destination.joinpath(*name.parts)
            mode = info.external_attr >> 16
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if stat.S_ISLNK(mode):
                link = zipped.read(info).decode("utf-8")
                resolved = (target.parent / link).resolve()
                if PurePosixPath(link).is_absolute() or not resolved.is_relative_to(
                    destination
                ):
                    raise ValueError(f"unsafe link {info.filename!r} -> {link!r}")
                os.symlink(link, target)
                continue
            with zipped.open(info) as source, target.open("wb") as out:
                shutil.copyfileobj(source, out, 1 << 20)
            os.chmod(target, 0o755 if mode & 0o111 else 0o644)


def reported_version(executable: Path) -> str:
    """The version an executable prints for ``--version``: its first word that starts
    with a digit, such as ``154.0.8037.57``."""
    completed = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    words = [word for word in completed.stdout.split() if word[:1].isdigit()]
    return words[0] if words else ""


def download(archive: Archive, path: Path) -> None:
    """Stream one archive over HTTPS; the setup command's ``Fetch``."""
    with httpx.stream(
        "GET", archive.url, timeout=60.0, follow_redirects=False
    ) as reply:
        reply.raise_for_status()
        with path.open("wb") as out:
            for chunk in reply.iter_bytes(1 << 20):
                out.write(chunk)
```

- [ ] **Step 4: Write the command**

Create `apps/earnings-pipeline/src/earnings_pipeline/cli.py`:

```python
"""The ``earnings-pipeline`` command line.

    uv run --locked --all-packages earnings-pipeline browser setup

``browser setup`` is the only command that downloads the pinned Chrome for Testing and
chromedriver (B8). It checks each archive against the committed manifest and installs
into a cache outside the repository; a capture never downloads anything.
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

app = typer.Typer(no_args_is_help=True, help="The earnings pipeline.")
browser = typer.Typer(
    no_args_is_help=True, help="The pinned browser for Stage 3's diagnostic path."
)
app.add_typer(browser, name="browser")


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

Replace `apps/earnings-pipeline/pyproject.toml` with:

```toml
[project]
name = "earnings-pipeline"
version = "0.1.0"
description = "Earnings pipeline application"
authors = [
    { name = "Lowell Mason", email = "mason.lowell@mac.com" }
]
requires-python = ">=3.14"
dependencies = [
    "earnings-core",
    "earnings-ingestion",
    "earnings-themes",
    "pydantic-settings",             # import pydantic_settings
    "polars",
    "duckdb",
    "pyarrow",
    "typer",
    "rich",
]

[project.scripts]
earnings-pipeline = "earnings_pipeline.cli:app"

[project.optional-dependencies]
orchestration = [
    "langgraph",
]

[build-system]
requires = ["uv_build>=0.12.15,<0.13.0"]
build-backend = "uv_build"
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_browser_install.py apps/earnings-pipeline/tests/test_cli.py -q
uv run --locked --all-packages earnings-pipeline browser --help
```

Expected: uv rebuilds `earnings-pipeline` once, for its new script. Then `13 passed`, then typer's help for `earnings-pipeline browser`, which lists one command, `setup`.

- [ ] **Step 6: Run the checks**

```bash
python3 /tmp/plan5-escapes.py packages/earnings-ingestion/src/earnings_ingestion/browser/install.py packages/earnings-ingestion/tests/test_browser_install.py apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/tests/test_cli.py
uv lock --check
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `uv lock --check` prints `Resolved 140 packages` and exits 0; `546 passed`; `All checks passed!` and `132 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/browser/install.py packages/earnings-ingestion/src/earnings_ingestion/browser/chrome-for-testing.toml packages/earnings-ingestion/tests/test_browser_install.py apps/earnings-pipeline/src/earnings_pipeline/cli.py apps/earnings-pipeline/pyproject.toml apps/earnings-pipeline/tests/test_cli.py
git commit -m "feat: pin Chrome for Testing and add earnings-pipeline browser setup"
```

---
### Task 5: The Selenium adapter, the `browser-capture` extra, and the import scan

This task introduces the only module that imports a browser library, and the checks
that keep it the only one. A static scan reads every package's source, imports inside
functions included. The runtime checks import each non-adapter module in a fresh
interpreter. The deferred item "Check import boundaries statically as well" closes
here (PB-11).

The adapter speaks CDP over the page's own DevTools socket with websocket-client,
because Selenium 4.49.0 bundles CDP bindings only up to Chrome 153. The browser tests
are the spec's network guard, determinism check, and environment record (PB-4, PB-5,
PB-6). They need the pinned browser, which Step 7 installs, with the user's
permission.

**Files:**

- Modify: `packages/earnings-ingestion/pyproject.toml` (replaced whole: the
  `browser-capture` extra); `uv.lock` (by `uv lock`).
- Create: `packages/earnings-ingestion/src/earnings_ingestion/browser/selenium_capture.py`.
- Test (create): `packages/earnings-ingestion/tests/test_selenium_capture.py`
  (browser-marked), `tests/contracts/test_import_scan.py`.
- Test (modify): `packages/earnings-ingestion/tests/test_import_boundaries.py`
  (replaced whole, block 1 of 3).
- Modify: `README.md` (one row in "Optional dependencies").

**Interfaces:**

- Consumes:
  - Task 2's records, `CapturePolicy`, `ISOLATED_1`, `METADATA_SCRIPT`,
    `parse_metadata`, `cache_key`, `capture_id`, `unrendered`, `this_platform` and
    `CaptureEnvironment`;
  - Task 3's `CaptureStore`, for the screenshot test;
  - Task 4's `Binaries` and `installed()`.
- Produces, in `earnings_ingestion.browser.selenium_capture`, importable only with
  the extra:
  - `SeleniumRenderer(binaries: Binaries | None, screenshots: Callable[[bytes], ArtifactRef] | None = None)`,
    a `BrowserRenderer`. Its `environment` names Chrome for Testing, the pinned
    versions, Selenium's version, and the platform.
  - `BROWSER_ENGINE = "Chrome for Testing"` and `TILE_HEIGHT = 4096`, the height of
    one screenshot tile.

- [ ] **Step 1: Add the extra and lock it**

Replace `packages/earnings-ingestion/pyproject.toml` with:

```toml
[project]
name = "earnings-ingestion"
version = "0.1.0"
description = "Earnings ingestion package"
authors = [
    { name = "Lowell Mason", email = "mason.lowell@mac.com" }
]
requires-python = ">=3.14"
dependencies = [
    "earnings-core",
    "pydantic",
    "polars",
    "httpx",
    "tenacity",
    "beautifulsoup4",  # import bs4
    "lxml",
]

[project.optional-dependencies]
edgar = [
    "edgartools",      # import edgar
]

entity-matching = [
    "rapidfuzz",
]

browser-capture = [
    "selenium==4.49.0",  # import selenium
    "websocket-client==1.9.2",  # import websocket
]

[build-system]
requires = ["uv_build>=0.12.15,<0.13.0"]
build-backend = "uv_build"
```

```bash
uv lock
git diff --stat uv.lock
```

Expected: 

- `Resolved 151 packages`, then eleven `Added` lines: attrs v26.1.0, cffi v2.1.1,
  outcome v1.3.0.post0, pycparser v3.0, pysocks v1.7.1, selenium v4.49.0,
  sortedcontainers v2.4.0, trio v0.34.0, trio-websocket v0.12.2, websocket-client
  v1.9.2, and wsproto v1.3.2;
- `uv.lock | 157` and `1 file changed, 156 insertions(+), 1 deletion(-)`.

No other locked version may change. If `uv lock` moves any other package, stop and
report.

- [ ] **Step 2: Write the failing tests**

Create `tests/contracts/test_import_scan.py`:

```python
"""A static scan of every package's imports, alongside the runtime checks (A §173; B3).

The runtime checks in ``packages/*/tests/test_import_boundaries.py`` see only what a
top-level import loads, so an import inside a function escapes them. This scan reads
every module under each member's ``src/`` with ``ast`` and refuses:

- a sibling import the dependency table in ``CLAUDE.md`` forbids;
- a browser import (Selenium, websocket-client, Playwright, pyppeteer) anywhere but
  ``earnings_ingestion.browser.selenium_capture``, the one adapter behind the
  ``browser-capture`` extra.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "earnings_core": ROOT / "packages" / "earnings-core" / "src" / "earnings_core",
    "earnings_ingestion": ROOT
    / "packages"
    / "earnings-ingestion"
    / "src"
    / "earnings_ingestion",
    "earnings_themes": ROOT
    / "packages"
    / "earnings-themes"
    / "src"
    / "earnings_themes",
    "earnings_pipeline": ROOT
    / "apps"
    / "earnings-pipeline"
    / "src"
    / "earnings_pipeline",
}
ALLOWED = {
    "earnings_core": set(),
    "earnings_ingestion": {"earnings_core"},
    "earnings_themes": {"earnings_core"},
    "earnings_pipeline": {"earnings_core", "earnings_ingestion", "earnings_themes"},
}
BROWSERS = frozenset({"selenium", "websocket", "playwright", "pyppeteer"})
ADAPTER = SOURCES["earnings_ingestion"] / "browser" / "selenium_capture.py"


def imported(path: Path) -> list[tuple[int, str]]:
    """Every absolute module a file imports, at any depth, with its line."""
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), str(path))):
        if isinstance(node, ast.Import):
            found += [(node.lineno, alias.name) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.append((node.lineno, node.module))
    return found


def violations(package: str) -> list[str]:
    members = set(SOURCES) - {package}
    out: list[str] = []
    for path in sorted(SOURCES[package].rglob("*.py")):
        for line, module in imported(path):
            top = module.partition(".")[0]
            where = f"{path.relative_to(ROOT)}:{line}"
            if top in members and top not in ALLOWED[package]:
                out.append(f"{where} imports {module}")
            if top in BROWSERS and path != ADAPTER:
                out.append(f"{where} imports the browser module {module}")
    return out


@pytest.mark.parametrize("package", sorted(SOURCES))
def test_no_package_imports_what_its_boundary_forbids(package: str) -> None:
    assert violations(package) == []


def test_the_scan_sees_imports_inside_functions(tmp_path: Path) -> None:
    module = tmp_path / "late.py"
    module.write_text(
        "def later():\n    import selenium.webdriver\n    from earnings_themes import x\n",
        encoding="utf-8",
    )
    assert imported(module) == [(2, "selenium.webdriver"), (3, "earnings_themes")]


def test_the_adapter_is_the_one_module_that_imports_a_browser() -> None:
    assert any(module.startswith("selenium") for _, module in imported(ADAPTER))
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
    ],
)
def test_importing_ingestion_loads_nothing_forbidden(module: str) -> None:
    assert modules_loaded_by(module) & FORBIDDEN == set()
```

Create `packages/earnings-ingestion/tests/test_selenium_capture.py`:

```python
"""The Selenium adapter in the pinned browser: opt-in with ``-m browser`` (Stage 3 spec,
Checks; plan B exit criteria 3, 4, and 10).

Every test here skips visibly without the ``browser-capture`` extra or the pinned
Chrome for Testing. The adapter is imported by a fixture, not at collection, so the
default suite deselects these tests whether or not the extra is installed. The guard
pages point at a local HTTP server that counts every connection it accepts: none may
arrive.
"""

import dataclasses
import http.server
import socketserver
import subprocess
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from earnings_ingestion.browser.install import installed
from earnings_ingestion.browser.policy import ISOLATED_1
from earnings_ingestion.browser.records import CaptureReason, CaptureStatus
from earnings_ingestion.browser.store import CaptureStore

pytestmark = pytest.mark.browser
BINARIES = installed()
pinned = pytest.mark.skipif(
    BINARIES is None,
    reason="the pinned Chrome for Testing is not installed: run"
    " uv run --locked --all-packages earnings-pipeline browser setup",
)
WITHOUT_DEFENCE = dataclasses.replace(
    ISOLATED_1,
    arguments=tuple(
        argument
        for argument in ISOLATED_1.arguments
        if not argument.startswith(("--proxy", "--host-resolver"))
    ),
)


class _Counter(socketserver.ThreadingTCPServer):
    daemon_threads = True
    connections = 0

    def verify_request(self, request, client_address) -> bool:
        type(self).connections += 1
        return True


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def adapter():
    """The adapter module, which imports Selenium; skips without the extra."""
    return pytest.importorskip(
        "earnings_ingestion.browser.selenium_capture",
        reason="needs the browser-capture extra: uv sync --locked --all-packages"
        " --extra browser-capture",
    )


@pytest.fixture
def server() -> Iterator[str]:
    """A local origin standing in for the network; yields its base URL."""
    _Counter.connections = 0
    counter = _Counter(("127.0.0.1", 0), _Handler)
    threading.Thread(target=counter.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{counter.server_address[1]}"
    finally:
        counter.shutdown()
        counter.server_close()


def guard_page(origin: str) -> bytes:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{origin}/sheet.css">
<script src="{origin}/external.js"></script>
</head><body>
<p id="target">ORIGINAL TEXT</p>
<script>document.getElementById("target").textContent = "REWRITTEN BY SCRIPT";</script>
<img src="{origin}/logo.png" alt="logo">
<iframe src="{origin}/frame.html"></iframe>
</body></html>""".encode()


def renderer(adapter, **options: object):
    return adapter.SeleniumRenderer(BINARIES, **options)


@pinned
@pytest.mark.parametrize(
    "policy", [ISOLATED_1, WITHOUT_DEFENCE], ids=["isolated-1", "fetch-alone"]
)
def test_every_request_is_blocked_recorded_and_never_made(
    adapter, server: str, policy
) -> None:
    """The stylesheet, image, and frame are refused and recorded. With document
    JavaScript disabled, Chrome never asks for the external script at all (PB-4)."""
    capture = renderer(adapter).capture(
        guard_page(server), policy, source_document_id="guard"
    )
    blocked = {
        (request.url, request.resource_type) for request in capture.blocked_requests
    }
    assert blocked == {
        (f"{server}/sheet.css", "Stylesheet"),
        (f"{server}/logo.png", "Image"),
        (f"{server}/frame.html", "Document"),
    }
    time.sleep(0.5)
    assert _Counter.connections == 0


@pinned
def test_document_javascript_never_runs(adapter, server: str) -> None:
    capture = renderer(adapter).capture(
        guard_page(server), ISOLATED_1, source_document_id="guard"
    )
    assert "ORIGINAL TEXT" in capture.rendered_text
    assert "REWRITTEN" not in capture.rendered_text


@pinned
def test_a_blocked_stylesheet_or_frame_makes_the_capture_partial(
    adapter, server: str
) -> None:
    capture = renderer(adapter).capture(
        guard_page(server), ISOLATED_1, source_document_id="guard"
    )
    assert capture.status is CaptureStatus.PARTIAL
    assert capture.reason is CaptureReason.BLOCKED_REQUIRED_RESOURCE
    required = {r.resource_type for r in capture.blocked_requests if r.required}
    assert required == {"Stylesheet", "Document"}


@pinned
def test_a_missing_image_does_not_downgrade_the_capture(adapter, server: str) -> None:
    page = f'<p>Logo below.</p><img src="{server}/logo.png" alt="logo">'.encode()
    capture = renderer(adapter).capture(page, ISOLATED_1, source_document_id="logo")
    assert capture.status is CaptureStatus.COMPLETED
    assert [r.resource_type for r in capture.blocked_requests] == ["Image"]


@pinned
def test_two_captures_have_the_same_text_and_layout_hashes(
    adapter, server: str
) -> None:
    page = guard_page(server)
    first = renderer(adapter).capture(page, ISOLATED_1, source_document_id="guard")
    second = renderer(adapter).capture(page, ISOLATED_1, source_document_id="guard")
    assert first.rendered_text_sha256 == second.rendered_text_sha256
    assert first.layout_sha256 == second.layout_sha256
    assert first.cache_key == second.cache_key


@pinned
def test_the_capture_records_the_pinned_environment(adapter) -> None:
    capture = renderer(adapter).capture(
        b"<p>Hello</p>", ISOLATED_1, source_document_id="hello"
    )
    assert (capture.browser_version, capture.driver_version) == (
        BINARIES.version,
        BINARIES.version,
    )
    assert capture.browser_engine == "Chrome for Testing"
    assert capture.os_name and capture.os_version and capture.architecture
    print(
        f"environment: {capture.browser_engine} {capture.browser_version},"
        f" chromedriver {capture.driver_version}, Selenium {capture.selenium_version},"
        f" {capture.os_name} {capture.os_version} {capture.architecture}"
    )


@pinned
def test_a_tall_page_is_screenshotted_in_tiles(adapter, tmp_path: Path) -> None:
    store = CaptureStore(tmp_path / "data" / "runs" / "browser-capture", tmp_path)
    page = ("<html><body>" + "<p>line</p>" * 400 + "</body></html>").encode()
    capture = renderer(adapter, screenshots=store.screenshot).capture(
        page, ISOLATED_1, source_document_id="tall"
    )
    assert len(capture.screenshots) > 1
    for reference in capture.screenshots:
        assert reference.matches((tmp_path / reference.storage_ref).read_bytes())


@pinned
def test_a_capture_never_runs_selenium_manager(adapter, monkeypatch) -> None:
    """Selenium Manager would download a driver; the explicit paths never call it."""
    monkeypatch.setenv("SE_MANAGER_PATH", "/nonexistent/selenium-manager")
    capture = renderer(adapter).capture(
        b"<p>Hello</p>", ISOLATED_1, source_document_id="hello"
    )
    assert capture.status is CaptureStatus.COMPLETED


@pinned
def test_a_browser_that_is_not_the_pinned_one_fails_at_startup(adapter) -> None:
    wrong = dataclasses.replace(BINARIES, version="1.0.0.0")
    capture = adapter.SeleniumRenderer(wrong).capture(
        b"<p>Hello</p>", ISOLATED_1, source_document_id="hello"
    )
    assert capture.status is CaptureStatus.FAILED
    assert capture.reason is CaptureReason.STARTUP_FAILURE


@pinned
def test_a_navigation_past_its_bound_is_a_timeout(adapter) -> None:
    policy = dataclasses.replace(ISOLATED_1, navigation_seconds=0.001)
    capture = renderer(adapter).capture(
        b"<p>Hello</p>", policy, source_document_id="hello"
    )
    assert capture.status is CaptureStatus.FAILED
    assert capture.reason is CaptureReason.TIMEOUT


@pinned
def test_no_browser_process_outlives_a_capture(adapter) -> None:
    renderer(adapter).capture(b"<p>Hello</p>", ISOLATED_1, source_document_id="hello")
    install_root = str(BINARIES.browser.parents[4])
    for _ in range(50):
        listing = subprocess.run(
            ["ps", "-A", "-o", "command="], capture_output=True, text=True, check=True
        ).stdout
        left = [line for line in listing.splitlines() if install_root in line]
        if not left:
            break
        time.sleep(0.1)
    assert left == []


def test_without_binaries_every_capture_is_unavailable(adapter) -> None:
    capture = adapter.SeleniumRenderer(None).capture(
        b"<p>Hello</p>", ISOLATED_1, source_document_id="hello"
    )
    assert capture.status is CaptureStatus.UNAVAILABLE
    assert capture.reason is CaptureReason.BROWSER_UNAVAILABLE
```

- [ ] **Step 3: Run the scan to verify it fails**

Run: `uv run --locked --all-packages pytest tests/contracts/test_import_scan.py packages/earnings-ingestion/tests/test_import_boundaries.py -q`

Expected: `1 failed, 11 passed`. `test_the_adapter_is_the_one_module_that_imports_a_browser` fails with `FileNotFoundError`, because the adapter does not exist yet.

- [ ] **Step 4: Write the adapter**

Create `packages/earnings-ingestion/src/earnings_ingestion/browser/selenium_capture.py`:

```python
"""The Selenium adapter: captures a saved page in the pinned Chrome for Testing (B1, B7).

Only this module imports Selenium or websocket-client (the import scan in
tests/contracts/test_import_scan.py holds every other module to that), and only the
``browser-capture`` extra installs them.

Every capture starts its own browser, in a fresh profile, and kills it afterwards:
chromedriver runs in a process group of its own, which Chrome and every helper it
starts share, so one signal reaches them all even when shutdown hangs. Chrome's crash
handler alone detaches, and exits with the browser. Requests are intercepted with CDP
Fetch over the page's DevTools socket, which Selenium's bundled CDP bindings do not
cover for this Chrome, and the interceptor outlives the browser: Chrome would let a
paused request through once its client had gone.
"""

import base64
import contextlib
import json
import os
import signal
import subprocess
import tempfile
import threading
import time
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import selenium
import websocket
from earnings_core import ArtifactRef, sha256_hex
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service

from earnings_ingestion.browser.install import Binaries
from earnings_ingestion.browser.metadata import (
    METADATA_SCRIPT,
    METADATA_VERSION,
    parse_metadata,
)
from earnings_ingestion.browser.policy import SAVED_NAME, CapturePolicy
from earnings_ingestion.browser.records import (
    BlockedRequest,
    CaptureReason,
    CaptureStatus,
    RenderedCapture,
    layout_hash,
)
from earnings_ingestion.browser.renderer import (
    CaptureEnvironment,
    cache_key,
    capture_id,
    this_platform,
    unrendered,
)

BROWSER_ENGINE = "Chrome for Testing"
TILE_HEIGHT = 4096
"""The tallest screenshot tile, in CSS pixels: long releases are captured in tiles."""


class _Failure(Exception):
    """A capture that cannot complete, with the reason it records."""

    def __init__(self, reason: CaptureReason, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


class _Watchdog:
    """Kills the browser when a bounded phase runs over, and remembers which one."""

    def __init__(self, kill: Callable[[], None]) -> None:
        self._kill = kill
        self._timer: threading.Timer | None = None
        self.expired: str | None = None

    def arm(self, phase: str, seconds: float) -> None:
        self.disarm()
        self._timer = threading.Timer(seconds, self._fire, args=(phase, seconds))
        self._timer.daemon = True
        self._timer.start()

    def disarm(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _fire(self, phase: str, seconds: float) -> None:
        self.expired = f"{phase} ran past {seconds:g} s"
        self._kill()


class _Interceptor:
    """Pauses every request of the page and lets through only the saved file.

    It speaks CDP over the page target's own DevTools socket, on a thread of its own.
    A required resource is a stylesheet or font (the policy's types) or a subframe's
    document; the main frame's own navigations away are refused and kept on the page.
    """

    def __init__(
        self, debugger_address: str, allowed_url: str, required: frozenset[str]
    ):
        with urllib.request.urlopen(
            f"http://{debugger_address}/json", timeout=10
        ) as reply:
            targets = json.load(reply)
        page = next(target for target in targets if target["type"] == "page")
        self._socket = websocket.create_connection(
            page["webSocketDebuggerUrl"], suppress_origin=True, timeout=10
        )
        self._allowed = allowed_url
        self._required = required
        self._next_id = 0
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self.blocked: list[BlockedRequest] = []
        self.error: str | None = None
        self._main_frame = self._call("Page.getFrameTree", {})["frameTree"]["frame"][
            "id"
        ]
        self._call(
            "Fetch.enable",
            {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]},
        )
        self._socket.settimeout(0.2)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    @property
    def alive(self) -> bool:
        return self._thread.is_alive() and self.error is None

    def _send(self, method: str, params: dict) -> int:
        self._next_id += 1
        self._socket.send(
            json.dumps({"id": self._next_id, "method": method, "params": params})
        )
        return self._next_id

    def _call(self, method: str, params: dict) -> dict:
        wanted = self._send(method, params)
        while True:
            message = json.loads(self._socket.recv())
            if message.get("id") == wanted:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message["result"]

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                message = json.loads(self._socket.recv())
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as error:  # noqa: BLE001 - any loss of the socket fails closed
                if not self._stop.is_set():
                    self.error = f"request interception stopped: {error!r}"
                return
            if message.get("method") != "Fetch.requestPaused":
                continue
            params = message["params"]
            url = params["request"]["url"]
            if url == self._allowed:
                self._send("Fetch.continueRequest", {"requestId": params["requestId"]})
                continue
            kind = params.get("resourceType", "Other")
            subframe = kind == "Document" and params.get("frameId") != self._main_frame
            with self._lock:
                self.blocked.append(
                    BlockedRequest(
                        url=url,
                        resource_type=kind,
                        required=kind in self._required or subframe,
                    )
                )
            reason = "Aborted" if kind == "Document" else "BlockedByClient"
            self._send(
                "Fetch.failRequest",
                {"requestId": params["requestId"], "errorReason": reason},
            )

    def recorded(self) -> tuple[BlockedRequest, ...]:
        """Each distinct blocked request once, sorted, so records compare stably."""
        with self._lock:
            unique = set(self.blocked)
        return tuple(sorted(unique, key=lambda item: (item.url, item.resource_type)))

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)
        self._socket.close()


class _Browser:
    """One chromedriver session in a process group of its own."""

    def __init__(
        self, binaries: Binaries, policy: CapturePolicy, scratch: Path
    ) -> None:
        options = webdriver.ChromeOptions()
        options.binary_location = str(binaries.browser)
        for argument in policy.arguments:
            options.add_argument(argument)
        options.add_argument(f"--user-data-dir={scratch / 'profile'}")
        options.add_experimental_option("prefs", dict(policy.preferences))
        self._service = Service(
            executable_path=str(binaries.driver),
            log_output=subprocess.DEVNULL,
            env={
                "HOME": str(scratch),
                "LANG": "en_US.UTF-8",
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "TZ": policy.timezone,
            },
            popen_kw={"start_new_session": True},
        )
        self._options = options
        self.driver: webdriver.Chrome | None = None

    def start(self) -> webdriver.Chrome:
        self.driver = webdriver.Chrome(options=self._options, service=self._service)
        return self.driver

    def kill(self) -> None:
        """SIGKILL chromedriver's whole process group; safe to repeat."""
        process = getattr(self._service, "process", None)
        if process is None:
            return
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass  # the group is gone, or only unreaped processes are left in it
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass

    def close(self, seconds: float) -> None:
        """Quit within ``seconds``, then kill whatever is left. A driver the watchdog
        already killed is not asked to quit: nothing would answer."""
        process = getattr(self._service, "process", None)
        running = process is not None and process.poll() is None
        if self.driver is not None and running:
            closer = threading.Thread(target=self._quit, daemon=True)
            closer.start()
            closer.join(seconds)
        self.kill()

    def _quit(self) -> None:
        # Any error is moot: the kill that follows cleans up regardless.
        with contextlib.suppress(Exception):
            self.driver.quit()


class SeleniumRenderer:
    """``BrowserRenderer`` over the pinned Chrome for Testing and chromedriver.

    ``binaries`` is ``None`` where none are installed: every capture is then
    ``unavailable``. ``screenshots`` stores each screenshot tile and returns its
    reference, as ``CaptureStore.screenshot`` does; without it a capture takes none.
    """

    def __init__(
        self,
        binaries: Binaries | None,
        screenshots: Callable[[bytes], ArtifactRef] | None = None,
    ) -> None:
        self._binaries = binaries
        self._store_screenshot = screenshots
        name, version, architecture = this_platform()
        pinned = binaries.version if binaries is not None else "none"
        self.environment = CaptureEnvironment(
            browser_engine=BROWSER_ENGINE,
            browser_version=pinned,
            driver_version=pinned,
            selenium_version=selenium.__version__,
            os_name=name,
            os_version=version,
            architecture=architecture,
        )

    def capture(
        self,
        saved_html: bytes,
        capture_policy: CapturePolicy,
        *,
        source_document_id: str,
    ) -> RenderedCapture:
        captured_at = datetime.now(UTC)
        started = time.monotonic()
        if self._binaries is None or not self._binaries.present():
            return self._unrendered(
                saved_html,
                capture_policy,
                source_document_id,
                CaptureStatus.UNAVAILABLE,
                CaptureReason.BROWSER_UNAVAILABLE,
                "the pinned browser and driver are not installed; run the browser setup",
                captured_at,
                started,
            )
        with tempfile.TemporaryDirectory(
            prefix="earnings-capture-", ignore_cleanup_errors=True
        ) as scratch_name:
            scratch = Path(scratch_name).resolve()
            try:
                return self._render(
                    saved_html,
                    capture_policy,
                    source_document_id,
                    scratch,
                    captured_at,
                    started,
                )
            except _Failure as failure:
                return self._unrendered(
                    saved_html,
                    capture_policy,
                    source_document_id,
                    CaptureStatus.FAILED,
                    failure.reason,
                    failure.detail,
                    captured_at,
                    started,
                )

    def _render(
        self,
        saved_html: bytes,
        policy: CapturePolicy,
        source_document_id: str,
        scratch: Path,
        captured_at: datetime,
        started: float,
    ) -> RenderedCapture:
        page = scratch / "page"
        page.mkdir()
        saved = page / SAVED_NAME
        saved.write_bytes(saved_html)
        url = saved.as_uri()
        browser = _Browser(self._binaries, policy, scratch)
        watchdog = _Watchdog(browser.kill)
        interceptor: _Interceptor | None = None
        try:
            watchdog.arm("startup", policy.startup_seconds)
            driver = _step(watchdog, CaptureReason.STARTUP_FAILURE, browser.start)
            self._check_versions(driver.capabilities)
            interceptor = _step(
                watchdog,
                CaptureReason.STARTUP_FAILURE,
                lambda: _Interceptor(
                    driver.capabilities["goog:chromeOptions"]["debuggerAddress"],
                    url,
                    policy.required_resource_types,
                ),
            )

            def configure() -> None:
                driver.execute_cdp_cmd(
                    "Emulation.setScriptExecutionDisabled", {"value": True}
                )
                driver.execute_cdp_cmd(
                    "Emulation.setTimezoneOverride", {"timezoneId": policy.timezone}
                )
                driver.set_page_load_timeout(policy.navigation_seconds)
                driver.set_script_timeout(policy.capture_seconds)

            _step(watchdog, CaptureReason.STARTUP_FAILURE, configure)
            watchdog.arm("navigation", policy.navigation_seconds)
            _step(
                watchdog, CaptureReason.DOCUMENT_LOAD_FAILURE, lambda: driver.get(url)
            )
            if driver.current_url.partition("#")[0] != url:
                raise _Failure(
                    CaptureReason.DOCUMENT_LOAD_FAILURE,
                    "the browser did not stay on the saved file",
                )
            watchdog.arm("capture", policy.capture_seconds)
            text, payload, charset = _step(
                watchdog,
                CaptureReason.CAPTURE_FAILURE,
                lambda: (
                    driver.execute_script("return document.body.innerText"),
                    driver.execute_script(METADATA_SCRIPT),
                    driver.execute_script("return document.characterSet"),
                ),
            )
            try:
                layout = parse_metadata(payload)
            except ValueError as error:
                raise _Failure(CaptureReason.CAPTURE_FAILURE, str(error)) from error
            screenshots = _step(
                watchdog,
                CaptureReason.CAPTURE_FAILURE,
                lambda: self._screenshots(driver),
            )
            watchdog.disarm()
            if not interceptor.alive:
                raise _Failure(
                    CaptureReason.CAPTURE_FAILURE,
                    interceptor.error or "request interception stopped",
                )
            blocked = interceptor.recorded()
        finally:
            watchdog.disarm()
            browser.close(policy.shutdown_seconds)
            if interceptor is not None:
                interceptor.close()
        required = [request for request in blocked if request.required]
        status = CaptureStatus.PARTIAL if required else CaptureStatus.COMPLETED
        raw_sha256 = sha256_hex(saved_html)
        key = cache_key(raw_sha256, policy, self.environment)
        return RenderedCapture(
            capture_id=capture_id(source_document_id, policy, key),
            cache_key=key,
            source_document_id=source_document_id,
            raw_sha256=raw_sha256,
            capture_policy=policy.name,
            capture_policy_version=policy.version,
            metadata_version=METADATA_VERSION,
            browser_engine=self.environment.browser_engine,
            browser_version=self.environment.browser_version,
            driver_version=self.environment.driver_version,
            selenium_version=self.environment.selenium_version,
            os_name=self.environment.os_name,
            os_version=self.environment.os_version,
            architecture=self.environment.architecture,
            viewport_width=policy.viewport_width,
            viewport_height=policy.viewport_height,
            device_scale_factor=policy.device_scale_factor,
            locale=policy.locale,
            timezone=policy.timezone,
            font_set=self.environment.font_set,
            document_charset=charset,
            script_policy="disabled",
            network_policy="blocked",
            image_policy="blocked",
            missing_resource_policy="recorded",
            rendered_text=text,
            rendered_text_sha256=sha256_hex(text.encode("utf-8")),
            layout=layout,
            layout_sha256=layout_hash(layout),
            screenshots=screenshots,
            blocked_requests=blocked,
            captured_at=captured_at,
            duration_seconds=round(time.monotonic() - started, 3),
            status=status,
            reason=None if not required else CaptureReason.BLOCKED_REQUIRED_RESOURCE,
            detail=(
                ""
                if not required
                else f"{len(required)} required resource(s) blocked: "
                + ", ".join(sorted({request.resource_type for request in required}))
            ),
        )

    def _check_versions(self, capabilities: dict) -> None:
        browser = capabilities.get("browserVersion", "")
        driver = (
            capabilities.get("chrome", {}).get("chromedriverVersion", "").split(" ")[0]
        )
        pinned = self._binaries.version
        if browser != pinned or driver != pinned:
            raise _Failure(
                CaptureReason.STARTUP_FAILURE,
                f"browser {browser!r} and driver {driver!r} are not the pinned {pinned!r}",
            )

    def _screenshots(self, driver: webdriver.Chrome) -> tuple[ArtifactRef, ...]:
        if self._store_screenshot is None:
            return ()
        size = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})["cssContentSize"]
        width = max(1, int(size["width"]))
        height = max(1, int(size["height"]))
        tiles = []
        for top in range(0, height, TILE_HEIGHT):
            shot = driver.execute_cdp_cmd(
                "Page.captureScreenshot",
                {
                    "format": "png",
                    "captureBeyondViewport": True,
                    "clip": {
                        "x": 0,
                        "y": top,
                        "width": width,
                        "height": min(TILE_HEIGHT, height - top),
                        "scale": 1,
                    },
                },
            )
            tiles.append(self._store_screenshot(base64.b64decode(shot["data"])))
        return tuple(tiles)

    def _unrendered(
        self,
        saved_html: bytes,
        policy: CapturePolicy,
        source_document_id: str,
        status: CaptureStatus,
        reason: CaptureReason,
        detail: str,
        captured_at: datetime,
        started: float,
    ) -> RenderedCapture:
        return unrendered(
            saved_html,
            policy,
            self.environment,
            source_document_id=source_document_id,
            status=status,
            reason=reason,
            detail=detail,
            captured_at=captured_at,
            duration_seconds=round(time.monotonic() - started, 3),
        )


def _step[T](watchdog: _Watchdog, reason: CaptureReason, action: Callable[[], T]) -> T:
    """Run one step; a timeout or any error becomes a ``_Failure``."""
    try:
        return action()
    except _Failure:
        raise
    except TimeoutException as error:
        raise _Failure(CaptureReason.TIMEOUT, _first_line(error)) from error
    except Exception as error:
        if watchdog.expired is not None:
            raise _Failure(CaptureReason.TIMEOUT, watchdog.expired) from error
        raise _Failure(reason, _first_line(error)) from error


def _first_line(error: Exception) -> str:
    text = str(error).strip().splitlines()
    return f"{type(error).__name__}: {text[0] if text else ''}"[:300]
```

- [ ] **Step 5: Run the boundary checks and the default suite**

```bash
python3 /tmp/plan5-escapes.py packages/earnings-ingestion/src/earnings_ingestion/browser/selenium_capture.py packages/earnings-ingestion/tests/test_selenium_capture.py packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py
uv run --locked --all-packages pytest tests/contracts/test_import_scan.py packages/earnings-ingestion/tests/test_import_boundaries.py -q
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `12 passed`; `557 passed, 13 deselected`; `All checks passed!` and `135 files already formatted`. The 13 deselected tests are the browser tests. The adapter is imported by a fixture, not at collection, so they are deselected whether or not the extra is installed.

- [ ] **Step 6: Name the extra in the README**

```bash
python3 - <<'EOF'
from pathlib import Path

path = Path("README.md")
text = path.read_text(encoding="utf-8")
old = "| `earnings-ingestion` | `edgar`, `entity-matching` | EDGAR-library experiments and fuzzy candidate generation |\n"
new = old + (
    "| `earnings-ingestion` | `browser-capture` | Stage 3's browser diagnostic path: Selenium"
    " and websocket-client drive the pinned Chrome for Testing, which"
    " `earnings-pipeline browser setup` installs |\n"
)
if text.count(old) != 1:
    raise SystemExit(f"expected one match, found {text.count(old)}")
path.write_text(text.replace(old, new), encoding="utf-8")
print("README.md updated")
EOF
```

Expected: `README.md updated`.

- [ ] **Step 7: Install the pinned browser (human gate)**

This step downloads, so it waits for the user (Human gates). In subagent-driven
execution a subagent stops here and reports back, and the controller asks. Ask in
chat, in these words or close to them:

> May I download Chrome for Testing 154.0.8037.57 for mac-arm64?
> `earnings-pipeline browser setup` fetches two archives from
> `https://storage.googleapis.com/chrome-for-testing-public/154.0.8037.57/mac-arm64/`:
> `chrome-mac-arm64.zip` (191,429,663 bytes) and `chromedriver-mac-arm64.zip`
> (9,302,980 bytes). It checks each against the committed size and SHA-256, and
> installs both into `~/Library/Caches/earnings-themes/chrome-for-testing/`, outside
> the repository.

Wait for a clear yes. On a no, stop and report: Tasks 9 and 11 cannot capture
without the browser. Then run:

```bash
uv run --locked --all-packages earnings-pipeline browser setup
```

Expected, with your home directory in place of `~`:

```text
Chrome for Testing 154.0.8037.57 (mac-arm64)
browser: ~/Library/Caches/earnings-themes/chrome-for-testing/154.0.8037.57/mac-arm64/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing
driver: ~/Library/Caches/earnings-themes/chrome-for-testing/154.0.8037.57/mac-arm64/chromedriver-mac-arm64/chromedriver
```

`Refused: ...` means an archive's size or hash is not the manifest's. Stop and
report it: never edit the manifest to match.

- [ ] **Step 8: Run the browser checks**

```bash
uv run --locked --all-packages --extra browser-capture pytest packages/earnings-ingestion/tests/test_selenium_capture.py -m browser -q -rsP
```

Expected: uv installs the extra's 11 packages on the first run. The PASSES section then
prints one line, of this form:

```text
environment: Chrome for Testing 154.0.8037.57, chromedriver 154.0.8037.57, Selenium 4.49.0, Darwin <macOS version> arm64
```

The run ends `13 passed`. A skip means the extra or the browser is missing, and its
reason says which.

Record the printed environment line; Task 15's verification record quotes it.

- [ ] **Step 9: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/pyproject.toml uv.lock packages/earnings-ingestion/src/earnings_ingestion/browser/selenium_capture.py packages/earnings-ingestion/tests/test_selenium_capture.py packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_import_scan.py README.md
git commit -m "feat(ingestion): capture in the pinned browser behind the browser-capture extra"
```

---
### Task 6: layout-1's blocks (L1–L17)

layout-1 reads a capture's layout metadata into the walker's own `Block` records, so
C1–C5 apply unchanged (PB-9). Each L-rule is the walker rule of the same number, with
a rendered signal in place of a tag or an inline style.

It imports the walker's patterns and tests themselves, including a few private names
such as `_FOOTNOTE_CELL`, so that each L-rule tests exactly what its W-rule tests.
`canonical/walker.py` is generated and frozen (PA-2), so those names cannot drift.
Nothing here maps onto canonical text yet: Task 7 does that.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/layout/__init__.py`
  (block 1 of 2: the package docstring), `layout/blocks.py`.
- Test (modify): `packages/earnings-ingestion/tests/conftest.py` (replaced whole,
  block 2 of 2: `LayoutParts` and the `parts` fixture added).
- Test (create): `packages/earnings-ingestion/tests/test_layout_blocks.py`.

**Interfaces:**

- Consumes:
  - Task 2's `LayoutMetadata`, `LayoutBlock`, `LayoutRun`, `LayoutTable` and
    `parse_metadata`;
  - from `walker-1`, read only:
    - `canonical.blocks`: `Block`, `GridCell` and `grid_columns`;
    - `canonical.dom.primary_space` and `canonical.normalize.normalize`;
    - `canonical.walker`: `classify`, `collapse`, `Cell`, `Row`, `Run`, `Style`,
      `MAX_HEADING_WORDS`, `MAX_MARKER_CHARS`, `_FOOTNOTE_CELL`, `_LIST_CELL`,
      `_NUMERIC_CELL` and `_YEAR`.
- Produces, in `earnings_ingestion.layout.blocks`:
  - `LAYOUT_VERSION = "layout-1"` and `SOURCE = "layout"`, the prefix of every
    layout-1 `source_type`;
  - `body_size(layout) -> float | None`;
  - `LayoutBlocks(layout: LayoutMetadata)`, whose `.blocks: list[Block]` are
    layout-1's blocks in reading order, before C1–C5;
  - the helpers `counts(run)`, `split_breaks(runs)`, `split_pre(runs)`,
    `type_block(runs, text, block, body)` and `larger(runs, body)`.
- Produces, in `tests/conftest.py`: `LayoutParts`, with `run(text, **style)`, `br()`,
  `block(*runs, tag="p", cell=None, **context)`, `table(*rows, parent=None, head=0, th=False)`
  and `cells(rows, table_index=0)`, and the fixture `parts`.

- [ ] **Step 1: Write the failing tests**

Replace `packages/earnings-ingestion/tests/conftest.py` with:

```python
"""Shared test data (plan 5): a small completed capture, its layout payload, and
builders for synthetic layout metadata."""

import copy
from collections.abc import Callable
from datetime import UTC, datetime

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
```

This is block 2 for that path: extract it with
`python3 /tmp/plan5-extract.py packages/earnings-ingestion/tests/conftest.py 2`.

Create `packages/earnings-ingestion/tests/test_layout_blocks.py`:

```python
"""layout-1's blocks from synthetic layout metadata: the L-rules, one by one."""

import pytest
from earnings_ingestion.browser.metadata import parse_metadata
from earnings_ingestion.browser.records import LayoutMetadata
from earnings_ingestion.layout.blocks import LayoutBlocks, body_size

BULLET = chr(0x2022)


def layout(blocks: list[dict], tables: list[dict] = ()) -> LayoutMetadata:
    return parse_metadata({"blocks": blocks, "tables": list(tables)})


def typed(metadata: LayoutMetadata) -> list[tuple[str, str, int | None]]:
    return [(b.type, b.text, b.level) for b in LayoutBlocks(metadata).blocks]


def body(parts, *extra: dict) -> list[dict]:
    """Enough body-size text that the body size is 16."""
    sentence = "The quarter's results were in line with the outlook we gave."
    return [parts.block(parts.run(sentence)), *extra]


def test_two_breaks_end_a_block_and_one_is_a_space(parts) -> None:
    blocks = [
        parts.block(
            parts.run("One"),
            parts.br(),
            parts.run("two"),
            parts.br(),
            parts.run(" "),
            parts.br(),
            parts.run("Three"),
        )
    ]
    assert typed(layout(blocks)) == [
        ("paragraph", "One two", None),
        ("paragraph", "Three", None),
    ]


@pytest.mark.parametrize("style", [{"bold": True}, {"underline": True}])
def test_a_short_emphasized_block_is_a_heading(style: dict, parts) -> None:
    blocks = body(parts, parts.block(parts.run("Outlook", **style)))
    assert typed(layout(blocks))[-1] == ("heading", "Outlook", None)


def test_a_long_emphasized_block_is_a_paragraph(parts) -> None:
    words = " ".join(["word"] * 13)
    blocks = body(parts, parts.block(parts.run(words, bold=True)))
    assert typed(layout(blocks))[-1][0] == "paragraph"


def test_a_short_block_set_larger_than_the_body_is_a_heading(parts) -> None:
    blocks = body(parts, parts.block(parts.run("Third Quarter Results", font_size=20)))
    assert typed(layout(blocks))[-1] == ("heading", "Third Quarter Results", None)


def test_a_block_partly_at_the_body_size_is_a_paragraph(parts) -> None:
    blocks = body(
        parts,
        parts.block(parts.run("Third Quarter", font_size=20), parts.run(" Results")),
    )
    assert typed(layout(blocks))[-1][0] == "paragraph"


def test_the_body_size_carries_the_most_visible_characters(parts) -> None:
    metadata = layout(
        [
            parts.block(parts.run("abcd", font_size=12)),
            parts.block(parts.run("abcd", font_size=14)),
            parts.block(
                parts.run("ab", font_size=20), parts.run("      ", font_size=30)
            ),
            parts.block(parts.run("hidden text here", font_size=40, visible=False)),
        ]
    )
    assert body_size(metadata) == 12


def test_tags_decide_headings_and_list_items(parts) -> None:
    blocks = body(
        parts,
        parts.block(parts.run("Results"), tag="h2", heading_level=2),
        parts.block(parts.run("Nested point"), tag="li", list_item=True, list_depth=2),
        parts.block(parts.run("Loose item"), tag="li", list_item=True, list_depth=0),
    )
    assert typed(layout(blocks))[1:] == [
        ("heading", "Results", 2),
        ("list_item", "Nested point", 2),
        ("list_item", "Loose item", None),
    ]


def test_the_walker_markers_type_page_numbers_bullets_and_footnotes(parts) -> None:
    blocks = body(
        parts,
        parts.block(parts.run("- 3 -")),
        parts.block(parts.run(f"{BULLET} Revenue grew")),
        parts.block(parts.run("l", symbol_font=True), parts.run(" Margins held")),
        parts.block(parts.run("(1) Excludes charges")),
        parts.block(parts.run("2", superscript=True), parts.run("Adjusted figure")),
    )
    assert [kind for kind, _, _ in typed(layout(blocks))[1:]] == [
        "other",
        "list_item",
        "list_item",
        "footnote",
        "footnote",
    ]


def test_hidden_runs_add_nothing_but_whitespace_always_separates(parts) -> None:
    blocks = body(
        parts,
        parts.block(
            parts.run("Visible"),
            parts.run(" secret", visible=False),
            parts.run(" text"),
        ),
        parts.block(
            parts.run("4,579;"),
            parts.run("\n    ", visible=False),
            parts.run("no shares"),
        ),
    )
    assert [text for _, text, _ in typed(layout(blocks))[1:]] == [
        "Visible text",
        "4,579; no shares",
    ]


def test_a_pre_block_splits_at_blank_lines_and_keeps_its_lines(parts) -> None:
    blocks = body(
        parts,
        parts.block(
            parts.run("Revenue     9.8\nCost        7.1\n\nNote text"), tag="pre"
        ),
    )
    produced = LayoutBlocks(layout(blocks)).blocks[1:]
    assert [(b.text, b.pre_lines) for b in produced] == [
        ("Revenue 9.8 Cost 7.1", ("Revenue     9.8", "Cost        7.1")),
        ("Note text", ("Note text",)),
    ]


def test_a_marker_table_makes_list_items_and_footnotes(parts) -> None:
    rows = [[BULLET, "First point"], ["(1)", "A note"]]
    metadata = layout(body(parts, *parts.cells(rows)), [parts.table([1, 1], [1, 1])])
    assert typed(metadata)[1:] == [
        ("list_item", "First point", None),
        ("footnote", "A note", None),
    ]


def test_a_data_table_is_one_block_with_header_rows(parts) -> None:
    rows = [["", "2026", "2025"], ["Revenue", "$9.8", "$9.1"], ["Cost", "7.1", "6.9"]]
    metadata = layout(
        body(parts, *parts.cells(rows)), [parts.table([1, 1, 1], [1, 1, 1], [1, 1, 1])]
    )
    (grid,) = LayoutBlocks(metadata).blocks[1:]
    assert grid.type == "table"
    assert [(c.text, c.row, c.column, c.is_header) for c in grid.cells] == [
        ("2026", 0, 1, True),
        ("2025", 0, 2, True),
        ("Revenue", 1, 0, False),
        ("$9.8", 1, 1, False),
        ("$9.1", 1, 2, False),
        ("Cost", 2, 0, False),
        ("7.1", 2, 1, False),
        ("6.9", 2, 2, False),
    ]


def test_thead_and_all_th_rows_are_header_rows(parts) -> None:
    rows = [["Metric", "Value"], ["Revenue", "9.8"], ["Cost", "7.1"]]
    metadata = layout(
        body(parts, *parts.cells(rows)), [parts.table([1, 1], [1, 1], [1, 1], head=3)]
    )
    (grid,) = LayoutBlocks(metadata).blocks[1:]
    assert all(c.is_header for c in grid.cells)


def test_a_spanning_prose_row_leaves_the_table(parts) -> None:
    rows = [
        ["Consolidated Statements of Income"],
        ["", "2026", "2025"],
        ["Revenue", "9.8", "9.1"],
        ["Amounts in millions, except where noted otherwise below."],
        ["Cost", "7.1", "6.9"],
    ]
    blocks = body(parts, *parts.cells(rows))
    blocks[1]["runs"][0]["bold"] = True
    metadata = layout(blocks, [parts.table([3], [1, 1, 1], [1, 1, 1], [3], [1, 1, 1])])
    produced = LayoutBlocks(metadata).blocks[1:]
    assert [(b.type, b.text) for b in produced if b.cells is None] == [
        ("heading", "Consolidated Statements of Income"),
        ("paragraph", "Amounts in millions, except where noted otherwise below."),
    ]
    assert [b.type for b in produced] == ["heading", "table", "paragraph", "table"]
    first, second = produced[1], produced[3]
    assert [(c.text, c.row) for c in first.cells] == [
        ("2026", 0),
        ("2025", 0),
        ("Revenue", 1),
        ("9.8", 1),
        ("9.1", 1),
    ]
    assert [(c.text, c.row) for c in second.cells] == [
        ("Cost", 0),
        ("7.1", 0),
        ("6.9", 0),
    ]


@pytest.mark.parametrize(
    ("row", "spans"),
    [(["Costs and expenses:", "", ""], [1, 1, 1]), (["12.5"], [3])],
)
def test_other_single_cell_rows_stay_in_the_table(
    row: list[str], spans: list[int], parts
) -> None:
    rows = [["", "2026", "2025"], ["Revenue", "9.8", "9.1"], row]
    metadata = layout(
        body(parts, *parts.cells(rows)), [parts.table([1, 1, 1], [1, 1, 1], spans)]
    )
    assert [b.type for b in LayoutBlocks(metadata).blocks[1:]] == ["table"]


def test_a_layout_table_is_walked_as_ordinary_blocks(parts) -> None:
    rows = [["Media contact", "Investor contact"]]
    metadata = layout(body(parts, *parts.cells(rows)), [parts.table([1, 1])])
    assert [text for _, text, _ in typed(metadata)[1:]] == [
        "Media contact",
        "Investor contact",
    ]


def test_a_nested_data_table_is_read_in_place(parts) -> None:
    outer = [parts.block(parts.run("Before"), tag="td", cell=(0, 0, 0))]
    inner = parts.cells([["", "2026"], ["Revenue", "9.8"]], table_index=1)
    after = [parts.block(parts.run("After"), tag="td", cell=(0, 0, 0))]
    metadata = layout(
        body(parts, *outer, *inner, *after),
        [parts.table([1]), parts.table([1, 1], [1, 1], parent=(0, 0, 0))],
    )
    assert [b.type for b in LayoutBlocks(metadata).blocks[1:]] == [
        "paragraph",
        "table",
        "paragraph",
    ]
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_layout_blocks.py -q`

Expected: `1 error during collection`: `ModuleNotFoundError: No module named 'earnings_ingestion.layout'`.

- [ ] **Step 3: Write layout-1's blocks**

Create `packages/earnings-ingestion/src/earnings_ingestion/layout/__init__.py`:

```python
"""layout-1, the layout extractor, and its mapping onto walker-1's text (Stage 3, plan B)."""
```

Create `packages/earnings-ingestion/src/earnings_ingestion/layout/blocks.py`:

```python
"""layout-1's blocks: the walker's rules read from the rendering (Stage 3, plan B).

Each L-rule is the walker rule of the same number with a rendered signal in place of
a tag or an inline style (plan 5, PB-9):

- **L1.** Hidden content is what the capture did not render: computed
  ``display: none``, ``noscript``, and runs whose computed visibility is not
  ``visible``.
- **L2, L3.** A block is what the capture recorded as one: the runs one element with a
  block display holds directly. Two or more ``<br>`` in a row, with only whitespace
  between them, end it.
- **L5.** A ``<pre>`` block splits at blank lines; each piece keeps its lines for C1.
- **L6, L7.** A heading or list item by its nearest ``h1``-``h6`` or ``li``, as the
  capture recorded; a list item's level is its list depth.
- **L8-L12.** The walker's ``classify``, over runs styled by computed weight,
  decoration, vertical alignment, and font family. W11 gains one clause: a block of at
  most 12 words whose every visible character is larger than the body size is a
  heading.
- **L13-L16.** The walker's marker-table, data-table, header-row, and layout-table
  tests, over each rendered table's own rows and cells, with their texts built as the
  walker builds them.
- **L17.** In a data table, a row whose only non-empty cell spans every column and
  holds a letter leaves the table: it is a block typed by L8-L12, and the table
  splits around it.

The blocks are the walker's ``Block`` records, so C1-C5 apply to them unchanged.
"""

import re
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field

from earnings_ingestion.browser.records import (
    LayoutBlock,
    LayoutMetadata,
    LayoutRun,
    LayoutTable,
)
from earnings_ingestion.canonical.blocks import Block, GridCell, grid_columns
from earnings_ingestion.canonical.dom import primary_space
from earnings_ingestion.canonical.normalize import normalize
from earnings_ingestion.canonical.walker import (
    _FOOTNOTE_CELL,
    _LIST_CELL,
    _NUMERIC_CELL,
    _YEAR,
    MAX_HEADING_WORDS,
    MAX_MARKER_CHARS,
    Cell,
    Row,
    Run,
    Style,
    classify,
    collapse,
)

LAYOUT_VERSION = "layout-1"
SOURCE = "layout"
"""The prefix of every layout-1 ``source_type``: ``layout:<tag>``."""

_BLANK_LINE = re.compile(r"\n[ \t\r\f\v]*\n")


def body_size(layout: LayoutMetadata) -> float | None:
    """The font size that carries the most visible non-whitespace characters.

    A tie goes to the smaller size; ``None`` when nothing visible has text.
    """
    counts: Counter[float] = Counter()
    for block in layout.blocks:
        for run in block.runs:
            if run.visible and not run.br:
                counts[run.font_size] += sum(not char.isspace() for char in run.text)
    counts = Counter({size: count for size, count in counts.items() if count})
    if not counts:
        return None
    return min(counts, key=lambda size: (-counts[size], size))


def counts(run: LayoutRun) -> bool:
    """L1: a run's text counts when it rendered. Whitespace always counts: it
    separates words whether or not it drew a box, as the walker's text keeps it."""
    return run.visible or (not run.br and not run.text.strip())


def _style(run: LayoutRun) -> Style:
    return Style(
        bold=run.bold,
        underline=run.underline,
        sup=run.superscript,
        symbol_font=run.symbol_font,
    )


def _walker_runs(runs: Sequence[LayoutRun]) -> list[Run]:
    """Visible runs as the walker's runs; a ``<br>`` is a newline (W3)."""
    return [
        Run("\n" if run.br else run.text, _style(run)) for run in runs if counts(run)
    ]


def split_breaks(runs: Sequence[LayoutRun]) -> list[list[LayoutRun]]:
    """L3: two or more ``<br>`` in a row, with only whitespace between, end a block."""
    pieces: list[list[LayoutRun]] = []
    segment: list[LayoutRun] = []
    breaks = 0
    for run in runs:
        if run.br and run.visible:
            breaks += 1
            if breaks >= 2:
                pieces.append(segment)
                segment = []
                continue
        elif run.visible and run.text.strip():
            breaks = 0
        segment.append(run)
    pieces.append(segment)
    return pieces


def split_pre(runs: Sequence[LayoutRun]) -> list[list[LayoutRun]]:
    """L5: a ``<pre>`` block's visible runs, split at blank lines."""
    visible = [run for run in runs if counts(run)]
    text = "".join(run.text for run in visible)
    gaps = [(gap.start(), gap.end()) for gap in _BLANK_LINE.finditer(text)]
    starts = [0] + [end for _, end in gaps]
    ends = [start for start, _ in gaps] + [len(text)]
    pieces = []
    for start, end in zip(starts, ends, strict=True):
        piece, offset = [], 0
        for run in visible:
            low, high = max(start, offset), min(end, offset + len(run.text))
            if low < high:
                piece.append(
                    run.model_copy(
                        update={"text": run.text[low - offset : high - offset]}
                    )
                )
            offset += len(run.text)
        pieces.append(piece)
    return pieces


def type_block(
    runs: Sequence[LayoutRun], text: str, block: LayoutBlock, body: float | None
) -> tuple[str, int | None]:
    """L6-L12: the type and level of one block's text."""
    if block.heading_level is not None:
        return "heading", block.heading_level
    if block.list_item:
        return "list_item", block.list_depth or None
    kind = classify(_walker_runs(runs), text)
    if (
        kind == "paragraph"
        and larger(runs, body)
        and len(text.split()) <= MAX_HEADING_WORDS
    ):
        return "heading", None
    return kind, None


def larger(runs: Sequence[LayoutRun], body: float | None) -> bool:
    """Every visible non-whitespace character is set larger than the body size."""
    sizes = [
        run.font_size for run in runs if run.visible and not run.br and run.text.strip()
    ]
    return body is not None and bool(sizes) and all(size > body for size in sizes)


@dataclass
class _Cell:
    items: list["LayoutBlock | _Table"] = field(default_factory=list)


@dataclass
class _Table:
    index: int
    table: LayoutTable
    cells: list[list[_Cell]]


def _tree(layout: LayoutMetadata) -> list["LayoutBlock | _Table"]:
    """The blocks in document order, each table in place as a tree of its cells."""
    top: list[LayoutBlock | _Table] = []
    made: dict[int, _Table] = {}

    def table_node(index: int) -> _Table:
        if index not in made:
            table = layout.tables[index]
            made[index] = _Table(
                index, table, [[_Cell() for _ in row.cells] for row in table.rows]
            )
            if table.parent_table is None:
                top.append(made[index])
            else:
                parent = table_node(table.parent_table)
                parent.cells[table.parent_row][table.parent_cell].items.append(
                    made[index]
                )
        return made[index]

    for block in layout.blocks:
        if block.table is None:
            top.append(block)
        else:
            table_node(block.table).cells[block.row][block.cell].items.append(block)
    return top


def _text_runs(item: "LayoutBlock | _Table", nested: bool) -> Iterator[LayoutRun]:
    """A cell item's visible text runs in document order, as ``visible_text`` reads
    them: a ``<br>`` adds nothing, and nested tables only when ``nested``."""
    if isinstance(item, _Table):
        if nested:
            for row in item.cells:
                for cell in row:
                    for inner in cell.items:
                        yield from _text_runs(inner, nested)
        return
    for run in item.runs:
        if counts(run) and not run.br:
            yield run


def _cell_text(cell: _Cell, *, nested: bool) -> str:
    return collapse(
        "".join(run.text for item in cell.items for run in _text_runs(item, nested))
    )


class LayoutBlocks:
    """layout-1 over one capture: its blocks, in document order, before C1-C5."""

    def __init__(self, layout: LayoutMetadata) -> None:
        self.body = body_size(layout)
        self.blocks: list[Block] = []
        for item in _tree(layout):
            self._item(item)

    # -- blocks -----------------------------------------------------------------
    def _item(self, item: "LayoutBlock | _Table") -> None:
        if isinstance(item, _Table):
            self._table(item)
        else:
            self._block(item)

    def _block(self, block: LayoutBlock) -> None:
        if block.tag == "pre":
            for piece in split_pre(block.runs):
                self._emit(piece, block, pre=True)
            return
        for piece in split_breaks(block.runs):
            self._emit(piece, block, pre=False)

    def _emit(
        self, runs: Sequence[LayoutRun], block: LayoutBlock, *, pre: bool
    ) -> None:
        raw = "".join("\n" if run.br else run.text for run in runs if counts(run))
        text = normalize(collapse(raw))
        if not text:
            return
        kind, level = type_block(runs, text, block, self.body)
        self.blocks.append(
            Block(
                type=kind,
                text=text,
                source_type=f"{SOURCE}:{block.tag}",
                level=level,
                pre_lines=tuple(raw.split("\n")) if pre else None,
            )
        )

    # -- tables -----------------------------------------------------------------
    def _table(self, table: _Table) -> None:
        rows = [
            index
            for index, cells in enumerate(table.cells)
            if any(_cell_text(cell, nested=True) for cell in cells)
        ]
        markers = [self._marker_row(table.cells[index]) for index in rows]
        if rows and all(markers):
            for kind, text in markers:
                if text := normalize(text):
                    self.blocks.append(
                        Block(
                            type=kind, text=text, source_type=f"{SOURCE}:marker-table"
                        )
                    )
            return
        if _is_data_table(table):
            self._data_table(table, rows)
            return
        for cells in table.cells:
            for cell in cells:
                for item in cell.items:
                    self._item(item)

    def _marker_row(self, cells: Sequence[_Cell]) -> tuple[str, str] | None:
        """L13: (type, text) when the row's first non-empty cell holds only a marker."""
        texts = [_cell_text(cell, nested=True) for cell in cells]
        filled = [(cell, text) for cell, text in zip(cells, texts, strict=True) if text]
        if len(filled) < 2 or len(filled[0][1]) > MAX_MARKER_CHARS:
            return None
        (marker_cell, marker), rest = (
            filled[0],
            " ".join(text for _, text in filled[1:]),
        )
        first = next(
            (
                run
                for item in marker_cell.items
                for run in _text_runs(item, nested=False)
                if run.text.strip()
            ),
            None,
        )
        if _FOOTNOTE_CELL.match(marker) or (first is not None and first.superscript):
            return "footnote", rest
        if _LIST_CELL.match(marker) or (first is not None and first.symbol_font):
            return "list_item", rest
        return None

    def _data_table(self, table: _Table, rows: Sequence[int]) -> None:
        """L14, L15 and L17: the grid, its header rows, and the rows that leave it."""
        grid: list[Row] = []
        numeric_seen = False
        for index in rows:
            own = table.table.rows[index]
            texts = [_cell_text(cell, nested=True) for cell in table.cells[index]]
            numeric = any(
                _NUMERIC_CELL.match(text) and not _YEAR.match(text)
                for text in texts[1:]
                if text
            )
            numeric_seen = numeric_seen or numeric
            all_th = bool(own.cells) and all(cell.header for cell in own.cells)
            header = own.head or all_th or not numeric_seen
            grid.append(
                Row(
                    header,
                    tuple(
                        Cell(text, cell.colspan, cell.rowspan)
                        for cell, text in zip(own.cells, texts, strict=True)
                    ),
                )
            )
        starts = grid_columns(grid)
        width = max(
            (
                start + cell.colspan
                for row, row_starts in zip(grid, starts, strict=True)
                for cell, start in zip(row.cells, row_starts, strict=True)
            ),
            default=0,
        )
        piece: list[GridCell] = []
        piece_row = 0
        for index, row, row_starts in zip(rows, grid, starts, strict=True):
            filled = [
                (k, cell) for k, cell in enumerate(row.cells) if normalize(cell.text)
            ]
            spanning = (
                len(filled) == 1
                and row_starts[filled[0][0]] == 0
                and filled[0][1].colspan >= width
                and any(char.isalpha() for char in filled[0][1].text)
            )
            if spanning:
                self._close(piece)
                piece, piece_row = [], 0
                self._lift(table.cells[index][filled[0][0]])
                continue
            for cell, start in zip(row.cells, row_starts, strict=True):
                if text := normalize(cell.text):
                    piece.append(
                        GridCell(
                            text,
                            piece_row,
                            start,
                            cell.rowspan,
                            cell.colspan,
                            row.header,
                        )
                    )
            piece_row += 1
        self._close(piece)

    def _close(self, cells: Sequence[GridCell]) -> None:
        if cells:
            self.blocks.append(
                Block(
                    type="table",
                    text="",
                    source_type=f"{SOURCE}:table",
                    cells=tuple(cells),
                )
            )

    def _lift(self, cell: _Cell) -> None:
        """L17: the spanning cell's text as one block, typed by L8-L12."""
        runs = [run for item in cell.items for run in _text_runs(item, nested=True)]
        text = normalize(collapse("".join(run.text for run in runs)))
        if not text:
            return
        kind = classify(_walker_runs(runs), text)
        if (
            kind == "paragraph"
            and larger(runs, self.body)
            and len(text.split()) <= MAX_HEADING_WORDS
        ):
            kind = "heading"
        self.blocks.append(Block(type=kind, text=text, source_type=f"{SOURCE}:row"))


def _is_data_table(table: _Table) -> bool:
    """L14: at least two rows with text and one row with two or more non-empty cells,
    counting the table's own cells' text without nested tables."""
    rows_with_text = 0
    has_multi_cell_row = False
    for cells in table.cells:
        filled = sum(
            1 for cell in cells if primary_space(_cell_text(cell, nested=False))
        )
        rows_with_text += filled > 0
        has_multi_cell_row = has_multi_cell_row or filled >= 2
    return rows_with_text >= 2 and has_multi_cell_row
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_layout_blocks.py -q`

Expected: `19 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan5-escapes.py packages/earnings-ingestion/src/earnings_ingestion/layout/*.py packages/earnings-ingestion/tests/conftest.py packages/earnings-ingestion/tests/test_layout_blocks.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `576 passed, 13 deselected`; `All checks passed!` and `138 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/layout/__init__.py packages/earnings-ingestion/src/earnings_ingestion/layout/blocks.py packages/earnings-ingestion/tests/conftest.py packages/earnings-ingestion/tests/test_layout_blocks.py
git commit -m "feat(ingestion): read layout-1's blocks from rendered style and geometry"
```

---
### Task 7: Mapping policy `anchored-1`

`anchored-1` decides where each layout-1 unit sits in `walker-1`'s canonical text, or
records why it cannot (PB-10, SC13). It works on text alone: a collapsed-whitespace
copy that remembers each character's canonical offset, so every match maps back to
exactly one canonical span. Units that occur once anchor the rest. Order checks drop
anything out of place. Repeated texts are placed only when their neighbours leave
exactly one reading.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/layout/align.py`.
- Test (create): `packages/earnings-ingestion/tests/test_layout_align.py`.

**Interfaces:**

- Consumes: `earnings_core.RejectionReason` and `TextSpan`.
- Produces, in `earnings_ingestion.layout.align`:
  - `MAPPING_POLICY = "anchored-1"`.
  - `CollapsedText`, a frozen dataclass:
    - `CollapsedText.of(canonical_text)` builds it;
    - `.text` and `.origins` are its fields;
    - `span(start, end) -> TextSpan` maps a collapsed range back to canonical
      offsets;
    - `occurrences(unit) -> list[int]` lists every token-bounded start of `unit`'s
      collapsed text.
  - `Placed(start: int | None, reason: RejectionReason | None, detail: str)`.
  - `align(collapsed, units: Sequence[str]) -> list[Placed]`, one per unit, in order.
    A placed unit has `start` and no reason. An unplaced one has
    `LOCATOR_NOT_FOUND` or `AMBIGUOUS_OCCURRENCE`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_layout_align.py`:

```python
"""Mapping policy anchored-1: exact, reversible, never a first match (SC13)."""

import pytest
from earnings_core import RejectionReason, TextSpan
from earnings_ingestion.layout.align import CollapsedText, align

NOT_FOUND = RejectionReason.LOCATOR_NOT_FOUND
AMBIGUOUS = RejectionReason.AMBIGUOUS_OCCURRENCE


def places(text: str, units: list[str]) -> list[int | RejectionReason]:
    collapsed = CollapsedText.of(text)
    return [
        placed.start if placed.start is not None else placed.reason
        for placed in align(collapsed, units)
    ]


def test_the_collapsed_text_maps_back_to_exact_canonical_spans() -> None:
    canonical = "Net sales\t$\t9.8\nCost  of sales\n"
    collapsed = CollapsedText.of(canonical)
    assert collapsed.text == "Net sales $ 9.8 Cost of sales"
    start = collapsed.text.index("9.8 Cost")
    span = collapsed.span(start, start + len("9.8 Cost"))
    assert span == TextSpan(start=12, end=20)
    assert canonical[span.start : span.end] == "9.8\nCost"


def test_occurrences_are_token_bounded_and_may_overlap() -> None:
    collapsed = CollapsedText.of("2019 1 a a a")
    assert collapsed.occurrences("1") == [5]
    assert collapsed.occurrences("a a") == [7, 9]
    assert collapsed.occurrences("") == []


def test_unique_units_map_and_missing_ones_are_not_found() -> None:
    assert places(
        "Revenue rose. Margins held.", ["Revenue rose.", "Guidance", "Margins held."]
    ) == [
        0,
        NOT_FOUND,
        14,
    ]


def test_neighbours_settle_repeated_cells() -> None:
    text = "Net sales $ 9.8 Cost $ 7.1"
    assert places(text, ["Net sales", "$", "9.8", "Cost", "$", "7.1"]) == [
        0,
        10,
        12,
        16,
        21,
        23,
    ]


def test_equal_counts_between_neighbours_map_in_order() -> None:
    text = "Shares 9,988 9,988 9,988 Total 9,988"
    units = ["Shares", "9,988", "9,988", "9,988", "Total", "9,988"]
    assert places(text, units) == [0, 7, 13, 19, 25, 31]


def test_a_repeat_the_neighbours_cannot_settle_stays_ambiguous() -> None:
    assert places("x y x", ["x"]) == [AMBIGUOUS]
    assert places("A x x B", ["A", "x", "B"]) == [0, AMBIGUOUS, 6]


def test_one_unit_far_out_of_place_costs_only_itself() -> None:
    text = "Intro Middle End Late"
    assert places(text, ["Intro", "Late", "Middle", "End"]) == [0, AMBIGUOUS, 6, 13]


def test_neither_unit_of_a_swapped_pair_is_kept() -> None:
    assert places("A B C", ["B", "A", "C"]) == [AMBIGUOUS, AMBIGUOUS, 4]


def test_overlapping_places_are_both_refused() -> None:
    assert places("A B C", ["A B", "B C"]) == [AMBIGUOUS, AMBIGUOUS]


def test_every_unit_inside_a_longer_one_is_refused_with_it() -> None:
    assert places("A B C D", ["A B C", "A", "C", "D"]) == [
        AMBIGUOUS,
        AMBIGUOUS,
        AMBIGUOUS,
        6,
    ]


@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_an_empty_text_holds_nothing(text: str) -> None:
    assert CollapsedText.of(text).text == ""
    assert places(text, ["A"]) == [NOT_FOUND]
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_layout_align.py -q`

Expected: `1 error during collection`: `ModuleNotFoundError: No module named 'earnings_ingestion.layout.align'`.

- [ ] **Step 3: Write the policy**

Create `packages/earnings-ingestion/src/earnings_ingestion/layout/align.py`:

```python
"""Mapping policy ``anchored-1``: layout-1's units onto walker-1's canonical text (SC13).

- **Space.** The canonical text with every whitespace run collapsed to one space. Each
  collapsed character keeps the canonical offset it came from, so a match maps back
  to exactly one canonical span: the map is deterministic and reversible.
- **Occurrences.** A unit's N1 text occurs where it matches exactly, starting and
  ending at a token boundary: the text's edge or a space. Overlapping occurrences
  count.
- **Anchors.** A unit with exactly one occurrence maps there.
- **Order.** Mapped units are kept only when they are consistent: a unit whose span
  overlaps another mapped unit's is dropped with it, and a unit is kept only when it
  belongs to every longest sequence of mapped units whose spans follow document order.
  One unit far out of place therefore costs only itself, and neither unit of a
  swapped pair is kept.
- **Neighbours.** Between two kept units, a text whose units there number exactly as
  many as its occurrences there maps in order: the first such unit to the first
  occurrence, and so on. With one unit and one occurrence, that is the neighbours
  deciding. Each round's new units pass the order check with the kept ones, and
  rounds repeat until none maps.
- **Failures.** No occurrence is ``locator_not_found``. Several occurrences that the
  neighbours never settle, or a place the order check refuses, is
  ``ambiguous_occurrence``. Nothing is placed at a first match or by a score.
"""

import bisect
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from earnings_core import RejectionReason, TextSpan

MAPPING_POLICY = "anchored-1"


@dataclass(frozen=True)
class CollapsedText:
    """The canonical text with whitespace runs collapsed, and each character's origin."""

    text: str
    origins: tuple[int, ...]

    @classmethod
    def of(cls, canonical_text: str) -> "CollapsedText":
        chars: list[str] = []
        origins: list[int] = []
        previous_space = True
        for offset, char in enumerate(canonical_text):
            if char.isspace():
                if not previous_space:
                    chars.append(" ")
                    origins.append(offset)
                previous_space = True
                continue
            chars.append(char)
            origins.append(offset)
            previous_space = False
        if chars and chars[-1] == " ":
            chars.pop()
            origins.pop()
        return cls("".join(chars), tuple(origins))

    def span(self, start: int, end: int) -> TextSpan:
        """The canonical span of collapsed characters ``[start, end)``."""
        return TextSpan(start=self.origins[start], end=self.origins[end - 1] + 1)

    def occurrences(self, unit: str) -> list[int]:
        """Every token-bounded start of ``unit``, overlapping ones included."""
        found: list[int] = []
        if not unit:
            return found
        width = len(unit)
        position = self.text.find(unit)
        while position != -1:
            before = position == 0 or self.text[position - 1] == " "
            end = position + width
            after = end == len(self.text) or self.text[end] == " "
            if before and after:
                found.append(position)
            position = self.text.find(unit, position + 1)
        return found


@dataclass(frozen=True)
class Placed:
    """Where one unit maps: a collapsed start, or the reason it maps nowhere."""

    start: int | None
    reason: RejectionReason | None
    detail: str


def align(collapsed: CollapsedText, units: Sequence[str]) -> list[Placed]:
    """Each unit's placement under ``anchored-1``, in the units' order."""
    found = [collapsed.occurrences(unit) for unit in units]
    widths = [len(unit) for unit in units]
    kept: dict[int, int] = {}
    refused: set[int] = set()
    proposed = {index: hits[0] for index, hits in enumerate(found) if len(hits) == 1}
    while proposed:
        merged = {**kept, **proposed}
        consistent = _consistent(merged, widths)
        refused |= set(proposed) - consistent
        kept = {index: merged[index] for index in consistent}
        proposed = _by_neighbours(units, found, kept, refused, len(collapsed.text))
    out: list[Placed] = []
    for index, hits in enumerate(found):
        if index in kept:
            out.append(Placed(kept[index], None, ""))
        elif not hits:
            out.append(Placed(None, RejectionReason.LOCATOR_NOT_FOUND, "no occurrence"))
        elif index in refused:
            out.append(
                Placed(
                    None,
                    RejectionReason.AMBIGUOUS_OCCURRENCE,
                    "its place is out of order with, or overlaps, other mapped units",
                )
            )
        else:
            out.append(
                Placed(
                    None,
                    RejectionReason.AMBIGUOUS_OCCURRENCE,
                    f"{len(hits)} occurrences, and its neighbours do not settle which",
                )
            )
    return out


def _by_neighbours(
    units: Sequence[str],
    found: Sequence[list[int]],
    kept: dict[int, int],
    refused: set[int],
    length: int,
) -> dict[int, int]:
    """New places from the windows between kept units: equal counts map in order."""
    proposed: dict[int, int] = {}
    index = 0
    while index < len(units):
        if index in kept:
            index += 1
            continue
        first = index
        while index < len(units) and index not in kept:
            index += 1
        low = next(
            (kept[i] + len(units[i]) for i in range(first - 1, -1, -1) if i in kept), 0
        )
        high = kept[index] if index < len(units) else length
        members: dict[str, list[int]] = defaultdict(list)
        for unit in range(first, index):
            if unit not in refused and found[unit]:
                members[units[unit]].append(unit)
        for text, group in members.items():
            inside = [
                start
                for start in found[group[0]]
                if low <= start and start + len(text) <= high
            ]
            if inside and len(inside) == len(group):
                proposed.update(zip(group, inside, strict=True))
    return proposed


def _consistent(places: dict[int, int], widths: Sequence[int]) -> set[int]:
    """The units that overlap no other and lie on every longest in-order sequence."""
    overlapping: set[int] = set()
    reach, holder = 0, -1
    for unit in sorted(places, key=lambda unit: places[unit]):
        if places[unit] < reach:
            overlapping.update((unit, holder))
        if places[unit] + widths[unit] > reach:
            reach, holder = places[unit] + widths[unit], unit
    units = sorted(unit for unit in places if unit not in overlapping)
    starts = [places[unit] for unit in units]
    ending = _longest_ending(starts)
    starting = _longest_ending([-start for start in reversed(starts)])[::-1]
    longest = max(ending, default=0)
    on_some = [
        position
        for position in range(len(units))
        if ending[position] + starting[position] - 1 == longest
    ]
    per_level: dict[int, list[int]] = defaultdict(list)
    for position in on_some:
        per_level[ending[position]].append(position)
    return {units[members[0]] for members in per_level.values() if len(members) == 1}


def _longest_ending(values: Sequence[int]) -> list[int]:
    """For each position, the length of the longest strictly increasing run of values
    that ends there, taken in order (patience sorting)."""
    tails: list[int] = []
    lengths: list[int] = []
    for value in values:
        position = bisect.bisect_left(tails, value)
        if position == len(tails):
            tails.append(value)
        else:
            tails[position] = value
        lengths.append(position + 1)
    return lengths
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_layout_align.py -q`

Expected: `12 passed`.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan5-escapes.py packages/earnings-ingestion/src/earnings_ingestion/layout/align.py packages/earnings-ingestion/tests/test_layout_align.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `588 passed, 13 deselected`; `All checks passed!` and `140 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/layout/align.py packages/earnings-ingestion/tests/test_layout_align.py
git commit -m "feat(ingestion): map layout units onto canonical text under anchored-1"
```

---
### Task 8: The extractor, the fallback's triggers, and the layout records

`LayoutExtractor` joins Tasks 6 and 7:

- `extract(capture)` returns layout-1's blocks after C1–C5;
- `map_onto(capture, document)` places them on a `walker-1` document and returns a
  `LayoutExtraction`: valid elements over the canonical text, every alignment
  failure, and the retype counts.

Canonical text that no element covers becomes `other`, one element per line (PB-9).
`canonical/triggers.py` reads the fallback's two triggers from `walker-1`'s output,
as the spec's pre-registered comparison defines them. It is the only new module in
`canonical/`, and it changes nothing `canonicalize` runs.

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/layout/records.py`,
  `layout/extract.py`, `canonical/triggers.py`.
- Modify: `packages/earnings-ingestion/src/earnings_ingestion/layout/__init__.py`
  (replaced whole, block 2 of 2: the public API).
- Test (create): `packages/earnings-ingestion/tests/test_layout_extract.py`,
  `test_triggers.py`.
- Modify: `docs/data-dictionary.md` (appended); test:
  `tests/contracts/test_data_dictionary.py` (block 2 of 3).
- Test (modify): `packages/earnings-ingestion/tests/test_import_boundaries.py`
  (block 2 of 3: the layout modules join).

**Interfaces:**

- Consumes:
  - Task 6's `LayoutBlocks`, `LAYOUT_VERSION` and `SOURCE`;
  - Task 7's `CollapsedText`, `align` and `MAPPING_POLICY`;
  - `walker-1`'s `compensate`, `Block` and `MAX_HEADING_WORDS`;
  - core's `CanonicalDocument`, `DocumentElement`, `ElementType`,
    `TableCellContext`, `TextSpan` and `validate_elements`.
- Produces:
  - **`earnings_ingestion.layout.records`.**
    - `AlignmentFailure(status="alignment_failed", reason, unit_type, text, detail)`,
      whose `reason` must be `locator_not_found` or `ambiguous_occurrence`.
    - `LayoutExtraction(layout_version, mapping_policy, capture_id, doc_id, units, retypes, elements, failures)`.
    - `ALIGNMENT_REASONS`.
  - **`earnings_ingestion.layout.extract.LayoutExtractor`.**
    - `version` and `mapping_policy`.
    - `extract(capture) -> tuple[list[Block], dict[str, int]]`, which raises
      `ValueError` on a failed or unavailable capture.
    - `map_onto(capture, document) -> LayoutExtraction`.
    - `place(capture, document, blocks, retypes) -> LayoutExtraction`, the module
      function it calls.
  - **`earnings_ingestion.layout`** exports `LAYOUT_VERSION`, `MAPPING_POLICY`,
    `AlignmentFailure`, `LayoutExtraction` and `LayoutExtractor`.
  - **`earnings_ingestion.canonical.triggers`.** `NO_HEADING = "no_heading"`,
    `PROSE_ROW = "prose_row"`, and
    `fired(document, elements) -> tuple[str, ...]`, in that order.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_layout_extract.py`:

```python
"""LayoutExtractor end to end: walker-1's text, a synthetic capture, layout-1's stream."""

from collections.abc import Callable

import pytest
from earnings_core import ElementType, RejectionReason, validate_elements
from earnings_ingestion.browser.metadata import parse_metadata
from earnings_ingestion.browser.records import (
    CaptureReason,
    CaptureStatus,
    RenderedCapture,
)
from earnings_ingestion.browser.renderer import EMPTY_LAYOUT
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.layout.extract import LayoutExtractor

Make = Callable[..., RenderedCapture]

SOURCE = b"""<html><head><style>.gone { display: none }</style></head><body>
<p><b>Acme Reports Results</b></p>
<p>Revenue rose 5% to $2.1 billion in the third quarter of the year.</p>
<p class="gone">Hidden by the stylesheet</p>
<table>
<tr><td></td><td>2026</td><td>2025</td></tr>
<tr><td>Revenue</td><td>$9.8</td><td>$9.1</td></tr>
<tr><td colspan="3">Amounts in millions, except where noted otherwise below.</td></tr>
</table>
<p>Page 2</p>
</body></html>"""


def walker1() -> Canonicalized:
    result = canonicalize(SOURCE, source_document_id="release", media_type="text/html")
    assert isinstance(result, Canonicalized)
    return result


def rendered(parts, extra: list[dict] = ()) -> dict:
    """What the browser shows: everything but the stylesheet-hidden paragraph."""
    rows = [
        ["", "2026", "2025"],
        ["Revenue", "$9.8", "$9.1"],
        ["Amounts in millions, except where noted otherwise below."],
    ]
    return {
        "blocks": [
            parts.block(parts.run("Acme Reports Results", bold=True)),
            parts.block(
                parts.run(
                    "Revenue rose 5% to $2.1 billion in the third quarter of the year."
                )
            ),
            *parts.cells(rows),
            parts.block(parts.run("Page 2")),
            *extra,
        ],
        "tables": [parts.table([1, 1, 1], [1, 1, 1], [3])],
    }


def extract(make_capture: Make, payload: dict):
    result = walker1()
    capture = make_capture(layout=parse_metadata(payload))
    return result, LayoutExtractor().map_onto(capture, result.document)


def test_layout1_types_the_rendering_over_walker1s_text(
    make_capture: Make, parts
) -> None:
    result, extraction = extract(make_capture, rendered(parts))
    text = result.document.canonical_text
    blocks = [
        (e.type.value, e.span.slice_of(text))
        for e in extraction.elements
        if e.type is not ElementType.TABLE_CELL
    ]
    assert blocks == [
        ("heading", "Acme Reports Results"),
        (
            "paragraph",
            "Revenue rose 5% to $2.1 billion in the third quarter of the year.",
        ),
        ("other", "Hidden by the stylesheet"),
        ("table", "2026\t2025\nRevenue\t$9.8\t$9.1"),
        ("paragraph", "Amounts in millions, except where noted otherwise below."),
        ("page_artifact", "Page 2"),
    ]
    assert extraction.failures == ()
    assert extraction.retypes["C3"] == 1
    assert validate_elements(result.document, extraction.elements) == ()


def test_cells_carry_their_grid_and_header_references(
    make_capture: Make, parts
) -> None:
    result, extraction = extract(make_capture, rendered(parts))
    text = result.document.canonical_text
    cells_found = [e for e in extraction.elements if e.type is ElementType.TABLE_CELL]
    headers = {
        e.element_id: e.span.slice_of(text)
        for e in cells_found
        if e.table_cell.is_header
    }
    assert sorted(headers.values()) == ["2025", "2026"]
    nine_eight = next(e for e in cells_found if e.span.slice_of(text) == "$9.8")
    assert (nine_eight.table_cell.row, nine_eight.table_cell.column) == (1, 1)
    assert [headers[h] for h in nine_eight.table_cell.header_cell_ids] == ["2026"]


def test_every_element_is_layout1s_own(make_capture: Make, parts) -> None:
    _, extraction = extract(make_capture, rendered(parts))
    assert {e.source_type.partition(":")[0] for e in extraction.elements} == {"layout"}
    assert extraction.layout_version == "layout-1"
    assert extraction.mapping_policy == "anchored-1"


def test_text_the_canonical_document_lacks_is_a_recorded_failure(
    make_capture: Make, parts
) -> None:
    extra = [parts.block(parts.run("Shown only because scripts are off"))]
    result, extraction = extract(make_capture, rendered(parts, extra))
    assert [(f.reason, f.text) for f in extraction.failures] == [
        (RejectionReason.LOCATOR_NOT_FOUND, "Shown only because scripts are off")
    ]
    assert extraction.units == 10
    assert validate_elements(result.document, extraction.elements) == ()


@pytest.mark.parametrize("status", [CaptureStatus.FAILED, CaptureStatus.UNAVAILABLE])
def test_a_capture_without_a_rendering_cannot_be_extracted(
    make_capture: Make, status: CaptureStatus
) -> None:
    capture = make_capture(
        status=status,
        reason=CaptureReason.CAPTURE_FAILURE,
        rendered_text="",
        layout=EMPTY_LAYOUT,
    )
    with pytest.raises(ValueError, match=status.value):
        LayoutExtractor().extract(capture)
```

Create `packages/earnings-ingestion/tests/test_triggers.py`:

```python
"""The fallback's two triggers, read from walker-1's output."""

import pytest
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.canonical.triggers import NO_HEADING, PROSE_ROW, fired

HEADING = "<h1>Acme Reports Results</h1>"
PARAGRAPH = "<p>Revenue rose.</p>"
TABLE = (
    "<table><tr><td></td><td>2026</td></tr><tr><td>Revenue</td><td>9.8</td></tr>{row}"
    "</table>"
)
LONG = '<tr><td colspan="2">' + " ".join(["word"] * 13) + "</td></tr>"
SHORT = '<tr><td colspan="2">' + " ".join(["word"] * 12) + "</td></tr>"


def triggers(body: str) -> tuple[str, ...]:
    html = f"<html><body>{body}</body></html>".encode()
    result = canonicalize(html, source_document_id="release", media_type="text/html")
    assert isinstance(result, Canonicalized)
    return fired(result.document, result.elements)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (HEADING + PARAGRAPH, ()),
        (PARAGRAPH, (NO_HEADING,)),
        (HEADING + TABLE.format(row=LONG), (PROSE_ROW,)),
        (HEADING + TABLE.format(row=SHORT), ()),
        (PARAGRAPH + TABLE.format(row=LONG), (NO_HEADING, PROSE_ROW)),
    ],
)
def test_each_trigger_fires_exactly_when_its_condition_holds(
    body: str, expected: tuple[str, ...]
) -> None:
    assert triggers(body) == expected
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_layout_extract.py packages/earnings-ingestion/tests/test_triggers.py -q`

Expected: `2 errors during collection`, each a `ModuleNotFoundError`: no module named `earnings_ingestion.layout.extract`, and none named `earnings_ingestion.canonical.triggers`.

- [ ] **Step 3: Write the records, the extractor, the triggers, and the public API**

Create `packages/earnings-ingestion/src/earnings_ingestion/layout/records.py`:

```python
"""layout-1's records: its element stream over one document, and each alignment failure.

These are ingestion records, not core contracts. docs/data-dictionary.md documents
every field.
"""

from typing import Literal, Self

from earnings_core import DocumentElement, RejectionReason
from earnings_core.documents import IdPart
from pydantic import NonNegativeInt, model_validator

from earnings_ingestion.canonical.records import IngestionRecord

ALIGNMENT_REASONS = frozenset(
    {RejectionReason.LOCATOR_NOT_FOUND, RejectionReason.AMBIGUOUS_OCCURRENCE}
)


class AlignmentFailure(IngestionRecord):
    """One layout-1 unit that maps onto no single canonical span (SC13).

    ``reason`` is core's ``locator_not_found`` when the unit's text occurs nowhere,
    and ``ambiguous_occurrence`` when it occurs more than once and no neighbour
    decides, or when its one place is out of order.
    """

    status: Literal["alignment_failed"] = "alignment_failed"
    reason: RejectionReason
    unit_type: str
    text: str
    detail: str

    @model_validator(mode="after")
    def _reason(self) -> Self:
        if self.reason not in ALIGNMENT_REASONS:
            raise ValueError(f"{self.reason.value} is not an alignment reason")
        return self


class LayoutExtraction(IngestionRecord):
    """layout-1's element stream over one canonical document, and every failure.

    ``units`` counts what was aligned: each block, and each cell of a table.
    """

    layout_version: IdPart
    mapping_policy: IdPart
    capture_id: str
    doc_id: str
    units: NonNegativeInt
    retypes: dict[str, NonNegativeInt]
    elements: tuple[DocumentElement, ...]
    failures: tuple[AlignmentFailure, ...]
```

Create `packages/earnings-ingestion/src/earnings_ingestion/layout/extract.py`:

```python
"""``LayoutExtractor``: layout-1's element stream over walker-1's canonical text (B5).

``extract(capture)`` works offline from the capture's saved layout metadata and
returns layout-1's blocks, after C1-C5. ``map_onto(capture, document)`` places them
on one canonical document under ``anchored-1`` and returns the elements with every
alignment failure. Canonical text that no element covers becomes ``other``, one
element per line (the spec's "text with no visible counterpart"). layout-1 emits no
sentences and no list containers: nothing downstream of the comparison reads them.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TableCellContext,
    TextSpan,
    validate_elements,
)

from earnings_ingestion.browser.records import CaptureStatus, RenderedCapture
from earnings_ingestion.canonical.blocks import Block
from earnings_ingestion.canonical.compensate import compensate
from earnings_ingestion.layout.align import MAPPING_POLICY, CollapsedText, align
from earnings_ingestion.layout.blocks import LAYOUT_VERSION, SOURCE, LayoutBlocks
from earnings_ingestion.layout.records import AlignmentFailure, LayoutExtraction

USABLE = frozenset({CaptureStatus.COMPLETED, CaptureStatus.PARTIAL})


class LayoutExtractor:
    """layout-1 (B5): candidate elements from a capture's layout metadata."""

    version = LAYOUT_VERSION
    mapping_policy = MAPPING_POLICY

    def extract(self, capture: RenderedCapture) -> tuple[list[Block], dict[str, int]]:
        """layout-1's blocks after C1-C5, and C1-C5's retype counts.

        A failed or unavailable capture has no layout to read: ``ValueError``.
        """
        if capture.status not in USABLE:
            raise ValueError(f"capture {capture.capture_id} is {capture.status.value}")
        return compensate(LayoutBlocks(capture.layout).blocks)

    def map_onto(
        self, capture: RenderedCapture, document: CanonicalDocument
    ) -> LayoutExtraction:
        """The capture's blocks placed on ``document``, with every alignment failure."""
        blocks, retypes = self.extract(capture)
        return place(capture, document, blocks, retypes)


@dataclass(frozen=True)
class _Unit:
    block: int
    cell: int | None
    text: str


def place(
    capture: RenderedCapture,
    document: CanonicalDocument,
    blocks: Sequence[Block],
    retypes: dict[str, int],
) -> LayoutExtraction:
    units = [
        _Unit(index, None, block.text)
        if block.cells is None
        else _Unit(index, position, cell.text)
        for index, block in enumerate(blocks)
        for position, cell in (
            [(None, None)] if block.cells is None else enumerate(block.cells)
        )
    ]
    collapsed = CollapsedText.of(document.canonical_text)
    placements = align(collapsed, [unit.text for unit in units])
    failures: list[AlignmentFailure] = []
    spans: dict[tuple[int, int | None], TextSpan] = {}
    for unit, placement in zip(units, placements, strict=True):
        if placement.start is None:
            failures.append(
                AlignmentFailure(
                    reason=placement.reason,
                    unit_type="table_cell"
                    if unit.cell is not None
                    else blocks[unit.block].type,
                    text=unit.text,
                    detail=placement.detail,
                )
            )
        else:
            spans[unit.block, unit.cell] = collapsed.span(
                placement.start, placement.start + len(unit.text)
            )
    elements: list[DocumentElement] = []
    for index, block in enumerate(blocks):
        if block.cells is None:
            if (index, None) in spans:
                elements.append(
                    DocumentElement.create(
                        document,
                        ElementType(block.type),
                        spans[index, None],
                        level=block.level,
                        source_type=block.source_type,
                    )
                )
        else:
            elements.extend(_table(document, block, index, spans))
    elements = _with_uncovered(document, elements)
    rejections = validate_elements(document, elements)
    if rejections:
        raise AssertionError(f"layout-1 built an invalid element set: {rejections}")
    return LayoutExtraction(
        layout_version=LAYOUT_VERSION,
        mapping_policy=MAPPING_POLICY,
        capture_id=capture.capture_id,
        doc_id=document.doc_id,
        units=len(units),
        retypes=retypes,
        elements=tuple(elements),
        failures=tuple(failures),
    )


def _table(
    document: CanonicalDocument,
    block: Block,
    index: int,
    spans: dict[tuple[int, int | None], TextSpan],
) -> list[DocumentElement]:
    placed = [
        (cell, spans[index, position])
        for position, cell in enumerate(block.cells)
        if (index, position) in spans
    ]
    if not placed:
        return []
    table = DocumentElement.create(
        document,
        ElementType.TABLE,
        TextSpan(start=placed[0][1].start, end=placed[-1][1].end),
        source_type=block.source_type,
    )
    out = [table]
    headers: list[tuple[int, int, int, str]] = []  # row, first column, end column, id
    for cell, span in placed:
        references = (
            ()
            if cell.is_header
            else tuple(
                element_id
                for row, start, end, element_id in headers
                if row < cell.row
                and start < cell.column + cell.column_span
                and end > cell.column
            )
        )
        element = DocumentElement.create(
            document,
            ElementType.TABLE_CELL,
            span,
            parent_id=table.element_id,
            table_cell=TableCellContext(
                row=cell.row,
                column=cell.column,
                row_span=cell.row_span,
                column_span=cell.column_span,
                is_header=cell.is_header,
                header_cell_ids=references,
            ),
            source_type=f"{SOURCE}:cell",
        )
        if cell.is_header:
            headers.append(
                (
                    cell.row,
                    cell.column,
                    cell.column + cell.column_span,
                    element.element_id,
                )
            )
        out.append(element)
    return out


def _with_uncovered(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> list[DocumentElement]:
    """Every element, plus one ``other`` per line of canonical text none covers."""
    text = document.canonical_text
    tops = sorted(
        (e for e in elements if e.parent_id is None), key=lambda e: e.span.start
    )
    gaps: list[tuple[int, int]] = []
    cursor = 0
    for element in tops:
        if element.span.start > cursor:
            gaps.append((cursor, element.span.start))
        cursor = max(cursor, element.span.end)
    if cursor < len(text):
        gaps.append((cursor, len(text)))
    others: list[DocumentElement] = []
    for low, high in gaps:
        line_start = low
        for position in range(low, high + 1):
            if position == high or text[position] == "\n":
                start, end = line_start, position
                while start < end and text[start].isspace():
                    start += 1
                while end > start and text[end - 1].isspace():
                    end -= 1
                if start < end:
                    others.append(
                        DocumentElement.create(
                            document,
                            ElementType.OTHER,
                            TextSpan(start=start, end=end),
                            source_type=f"{SOURCE}:uncovered",
                        )
                    )
                line_start = position + 1
    order = {id(e): n for n, e in enumerate(elements)}
    merged = sorted(
        [*elements, *others],
        key=lambda e: (e.span.start, -e.span.end, order.get(id(e), -1)),
    )
    return _parents_first(merged)


def _parents_first(elements: list[DocumentElement]) -> list[DocumentElement]:
    """Document order with each table directly before its cells."""
    cells: dict[str, list[DocumentElement]] = {}
    for element in elements:
        if element.parent_id is not None:
            cells.setdefault(element.parent_id, []).append(element)
    out: list[DocumentElement] = []
    for element in elements:
        if element.parent_id is None:
            out.append(element)
            out.extend(cells.get(element.element_id, []))
    return out
```

Create `packages/earnings-ingestion/src/earnings_ingestion/canonical/triggers.py`:

```python
"""The fallback's activation triggers, read from walker-1's recorded output.

The Stage 3 spec's pre-registered comparison names two (§Pre-registered comparison,
"Fallback activation"). A document switches to layout-1's element stream when either
fires:

1. ``no_heading``: walker-1 emitted no ``heading`` element at all;
2. ``prose_row``: a row of a data table whose only non-empty cell holds more than 12
   words (``MAX_HEADING_WORDS``).
"""

from collections import defaultdict
from collections.abc import Sequence

from earnings_core import CanonicalDocument, DocumentElement, ElementType

from earnings_ingestion.canonical.walker import MAX_HEADING_WORDS

NO_HEADING = "no_heading"
PROSE_ROW = "prose_row"


def fired(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> tuple[str, ...]:
    """The triggers walker-1's elements fire, in the spec's order."""
    found: list[str] = []
    if not any(element.type is ElementType.HEADING for element in elements):
        found.append(NO_HEADING)
    rows: dict[tuple[str, int], list[DocumentElement]] = defaultdict(list)
    for element in elements:
        if element.type is ElementType.TABLE_CELL and element.table_cell is not None:
            rows[element.parent_id or "", element.table_cell.row].append(element)
    if any(
        len(cells) == 1
        and len(cells[0].span.slice_of(document.canonical_text).split())
        > MAX_HEADING_WORDS
        for cells in rows.values()
    ):
        found.append(PROSE_ROW)
    return tuple(found)
```

Replace `packages/earnings-ingestion/src/earnings_ingestion/layout/__init__.py` with:

```python
"""layout-1, the layout extractor, and its mapping onto walker-1's text (Stage 3, plan B)."""

from earnings_ingestion.layout.align import MAPPING_POLICY
from earnings_ingestion.layout.blocks import LAYOUT_VERSION
from earnings_ingestion.layout.extract import LayoutExtractor
from earnings_ingestion.layout.records import AlignmentFailure, LayoutExtraction

__all__ = [
    "LAYOUT_VERSION",
    "MAPPING_POLICY",
    "AlignmentFailure",
    "LayoutExtraction",
    "LayoutExtractor",
]
```

This is block 2 for that path: extract it with
`python3 /tmp/plan5-extract.py packages/earnings-ingestion/src/earnings_ingestion/layout/__init__.py 2`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_layout_extract.py packages/earnings-ingestion/tests/test_triggers.py -q`

Expected: `11 passed`.

- [ ] **Step 5: Extend the drift test to the layout records, and document them**

Replace `tests/contracts/test_data_dictionary.py` with:

```python
"""docs/data-dictionary.md documents every field and value of the core contracts
and of the ingestion records: the canonicalizer's, the capture's, and layout-1's.

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
`python3 /tmp/plan5-extract.py tests/contracts/test_data_dictionary.py 2`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: `2 failed, 32 passed`: `AlignmentFailure` and `LayoutExtraction` are not documented yet.

Append to `docs/data-dictionary.md`:

```markdown

### `AlignmentFailure`

One layout-1 unit that maps onto no single canonical span (SC13). It carries an
existing core reason; core has no alignment reason.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `status` | `alignment_failed` | Always this value |
| `reason` | `RejectionReason` | `locator_not_found` when the text occurs nowhere; `ambiguous_occurrence` when it occurs more than once and no neighbour decides, or its one place is out of order or overlaps another unit's |
| `unit_type` | string | The unit's layout-1 type, or `table_cell` |
| `text` | string | The unit's text after N1 |
| `detail` | string | Which of the above, in words |

### `LayoutExtraction`

layout-1's element stream over one canonical document, under mapping policy
`anchored-1`, with every alignment failure.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `layout_version` | ID part | `layout-1` |
| `mapping_policy` | ID part | `anchored-1` |
| `capture_id` | string | The capture it read |
| `doc_id` | string | The canonical document it maps onto |
| `units` | int ≥ 0 | Units aligned: each block, and each cell of a table |
| `retypes` | map of rule to int | Blocks retyped by each of `C1`–`C5`, zeros included |
| `elements` | tuple of `DocumentElement` | Document order, each table followed by its cells; canonical text no element covers is `other`, one element per line |
| `failures` | tuple of `AlignmentFailure` | Every unit that did not map |
```

This is block 2 for that path: extract it with
`python3 /tmp/plan5-extract.py docs/data-dictionary.md 2`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`

Expected: `34 passed`.

- [ ] **Step 6: Extend the runtime boundary checks to the layout modules**

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
    ],
)
def test_importing_ingestion_loads_nothing_forbidden(module: str) -> None:
    assert modules_loaded_by(module) & FORBIDDEN == set()
```

This is block 2 for that path: extract it with
`python3 /tmp/plan5-extract.py packages/earnings-ingestion/tests/test_import_boundaries.py 2`.

- [ ] **Step 7: Run the checks**

```bash
python3 /tmp/plan5-escapes.py packages/earnings-ingestion/src/earnings_ingestion/layout/*.py packages/earnings-ingestion/src/earnings_ingestion/canonical/triggers.py packages/earnings-ingestion/tests/test_layout_extract.py packages/earnings-ingestion/tests/test_triggers.py packages/earnings-ingestion/tests/test_import_boundaries.py tests/contracts/test_data_dictionary.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `escapes intact`; `603 passed, 13 deselected`; `All checks passed!` and `145 files already formatted`.

- [ ] **Step 8: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/layout packages/earnings-ingestion/src/earnings_ingestion/canonical/triggers.py packages/earnings-ingestion/tests/test_layout_extract.py packages/earnings-ingestion/tests/test_triggers.py packages/earnings-ingestion/tests/test_import_boundaries.py docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(ingestion): extract layout-1's elements onto walker-1's text"
```

---
### Task 9: The two-parser contract with the real pair

Plan 3's contract ran on stand-ins: `html.parser` as the canonicalizing parser, and
an lxml reader as the second extractor. It now runs on the real pair (§Layout
extractor; plan 3's Handoff 1). `walker-1` canonicalizes the contract release, and
layout-1 maps a real capture of the same bytes onto `walker-1`'s document.

The capture is committed, so the default suite runs the pair with no browser. A
browser-marked test checks that the pinned browser still renders exactly that
capture. The contract release is plan 3's synthetic page, not a Stage 1 fixture, so
capturing it before the freeze is allowed (Global Constraints).

The capture script written here also captures the releases in Task 11. It refuses
to until the pre-registration verifies.

**Files:**

- Create: `tests/fixtures/browser/contract-release.html`,
  `tests/integration/capture_browser_fixtures.py`.
- Modify: `.gitattributes` (one line appended, block 1 of 2).
- Generate: `tests/fixtures/browser/contract-release.capture.json`.
- Test (modify): `tests/contracts/test_element_schema_parsers.py` (replaced whole).

**Interfaces:**

- Consumes:
  - `canonicalize`, from plan 4;
  - `LayoutExtractor.map_onto`, from Task 8;
  - `CaptureStore` and `capture_once`, from Task 3;
  - `to_capture_json` and `from_capture_json`, from Task 3;
  - `installed()`, from Task 4;
  - `SeleniumRenderer`, from Task 5.
- Produces:
  - **The capture script,** `capture_browser_fixtures.py contract|releases`.
    - Each capture goes through the store under `data/runs/browser-capture/`.
    - It writes `tests/fixtures/browser/<name>.capture.json`.
    - A capture that is neither `completed` nor `partial` stops the run.
    - `releases` refuses unless `preregister.py verify` passes (Task 10).
  - **The committed contract capture.**

- [ ] **Step 1: Write the failing test**

Replace `tests/contracts/test_element_schema_parsers.py` with:

```python
"""Two parser implementations emit one browser-neutral element schema (D-15, B5).

The real pair (Stage 3 spec, Layout extractor): walker-1 canonicalizes the contract
release, and layout-1 maps a real capture of the same bytes onto walker-1's document,
the sole coordinate system. The capture is committed
(tests/fixtures/browser/contract-release.capture.json), so the default suite runs the
pair with no browser; the last test, opt-in with ``-m browser``, checks that the
pinned browser still renders exactly that capture.
"""

import json
from pathlib import Path

import pytest
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    RejectionReason,
    sha256_hex,
    validate_elements,
)
from earnings_ingestion.browser import ISOLATED_1, CaptureStatus
from earnings_ingestion.browser.install import installed
from earnings_ingestion.browser.serialize import from_capture_json
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.layout import LayoutExtraction, LayoutExtractor

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "browser"
SOURCE = (FIXTURES / "contract-release.html").read_bytes()
CAPTURE = from_capture_json(
    (FIXTURES / "contract-release.capture.json").read_text(encoding="utf-8")
)
REPEATED = "Results are preliminary."


def walker1(source: bytes = SOURCE) -> Canonicalized:
    result = canonicalize(
        source, source_document_id="contract-release", media_type="text/html"
    )
    assert isinstance(result, Canonicalized)
    return result


def layout1(document: CanonicalDocument) -> LayoutExtraction:
    return LayoutExtractor().map_onto(CAPTURE, document)


def comparable(element: DocumentElement) -> dict:
    """Everything but provenance; layout-1 emits no list containers, so a list item's
    parent is left out too."""
    exclude = {"source_type"}
    if element.type is ElementType.LIST_ITEM:
        exclude.add("parent_id")
    return element.model_dump(exclude=exclude)


def test_the_committed_capture_is_of_the_contract_release() -> None:
    assert CAPTURE.raw_sha256 == sha256_hex(SOURCE)
    assert CAPTURE.status is CaptureStatus.COMPLETED
    assert (CAPTURE.capture_policy, CAPTURE.capture_policy_version) == ("isolated", "1")


def test_walker1_emits_a_valid_element_set() -> None:
    result = walker1()
    assert validate_elements(result.document, result.elements) == ()
    assert not any(e.source_type.startswith("layout:") for e in result.elements)


def test_layout1_maps_valid_elements_onto_the_same_document() -> None:
    document = walker1().document
    extraction = layout1(document)
    assert extraction.doc_id == document.doc_id
    assert extraction.failures == ()
    assert validate_elements(document, extraction.elements) == ()
    assert all(e.source_type.startswith("layout:") for e in extraction.elements)


def test_elements_both_readers_place_agree_in_everything_but_provenance() -> None:
    result = walker1()
    containers = {
        e.parent_id for e in result.elements if e.type is ElementType.LIST_ITEM
    }
    expected = [
        comparable(e)
        for e in result.elements
        if e.type is not ElementType.SENTENCE and e.element_id not in containers
    ]
    assert [comparable(e) for e in layout1(result.document).elements] == expected


def test_repeated_text_is_placed_by_its_neighbours_never_by_a_first_match() -> None:
    result = walker1()
    text = result.document.canonical_text
    assert text.count(REPEATED) == 2

    def placed(elements) -> list[tuple[ElementType, int]]:
        return [
            (e.type, e.span.start)
            for e in elements
            if e.span.slice_of(text) == REPEATED and e.type is not ElementType.SENTENCE
        ]

    expected = [(ElementType.PARAGRAPH, 68), (ElementType.LIST_ITEM, 111)]
    assert placed(result.elements) == expected
    assert placed(layout1(result.document).elements) == expected


def test_text_the_document_lacks_is_not_found_and_stays_uncovered() -> None:
    changed = walker1(SOURCE.replace(b"rose 5%", b"rose 6%")).document
    extraction = layout1(changed)
    assert [(f.reason, f.unit_type, f.text) for f in extraction.failures] == [
        (
            RejectionReason.LOCATOR_NOT_FOUND,
            "paragraph",
            "Revenue rose 5% to $2.1 billion.",
        )
    ]
    uncovered = [
        e.span.slice_of(changed.canonical_text)
        for e in extraction.elements
        if e.source_type == "layout:uncovered"
    ]
    assert uncovered == ["Revenue rose 6% to $2.1 billion."]


def test_a_repeat_its_neighbours_cannot_settle_is_ambiguous() -> None:
    doubled = walker1(
        SOURCE.replace(b"<ul>", b"<p>Margins expanded.</p><ul>", 1)
    ).document
    extraction = layout1(doubled)
    assert [(f.reason, f.text) for f in extraction.failures] == [
        (RejectionReason.AMBIGUOUS_OCCURRENCE, "Margins expanded.")
    ]
    uncovered = [
        e.span.slice_of(doubled.canonical_text)
        for e in extraction.elements
        if e.source_type == "layout:uncovered"
    ]
    assert uncovered == ["Margins expanded.", "Margins expanded."]


def test_both_readers_emit_records_of_the_one_schema() -> None:
    result = walker1()
    fields = set(DocumentElement.model_fields)
    for element in [*result.elements, *layout1(result.document).elements]:
        payload = element.model_dump_json()
        assert set(json.loads(payload)) == fields
        assert DocumentElement.model_validate_json(payload) == element


@pytest.mark.browser
def test_the_pinned_browser_still_renders_the_committed_capture() -> None:
    selenium_capture = pytest.importorskip(
        "earnings_ingestion.browser.selenium_capture",
        reason="needs the browser-capture extra",
    )
    binaries = installed()
    if binaries is None:
        pytest.skip("the pinned Chrome for Testing is not installed")
    fresh = selenium_capture.SeleniumRenderer(binaries).capture(
        SOURCE, ISOLATED_1, source_document_id="contract-release"
    )
    assert (fresh.rendered_text_sha256, fresh.layout_sha256) == (
        CAPTURE.rendered_text_sha256,
        CAPTURE.layout_sha256,
    )
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run --locked --all-packages pytest tests/contracts/test_element_schema_parsers.py -q`

Expected: `1 error during collection`: `FileNotFoundError` for `tests/fixtures/browser/contract-release.html`.

- [ ] **Step 3: Write the contract release, the capture script, and the attribute**

Create `tests/fixtures/browser/contract-release.html`:

```html
<html><body>
<h1>Acme Reports Third Quarter Results</h1>
<p>Revenue rose 5% to $2.1 billion.</p>
<p>Results are preliminary.</p>
<ul><li>Margins expanded.</li><li>Results are preliminary.</li></ul>
<table>
<tr><th>Metric</th><th>Q3 2026</th></tr>
<tr><td>Net sales</td><td>$9.8</td></tr>
</table>
</body></html>
```

Create `tests/integration/capture_browser_fixtures.py`:

```python
"""Capture the committed browser fixtures with the pinned browser (Stage 3, plan B).

    uv run --locked --all-packages --extra browser-capture python tests/integration/capture_browser_fixtures.py contract
    uv run --locked --all-packages --extra browser-capture python tests/integration/capture_browser_fixtures.py releases

``contract`` captures tests/fixtures/browser/contract-release.html, the two-parser
contract's source. ``releases`` captures the eight Stage 1 releases, and refuses to
run until layout-1's pre-registration is committed and intact: no fixture is captured
before the comparison is fixed (plan 5, PB-13).

Each capture goes through the capture store under data/runs/browser-capture/, which
reuses a stored capture with the same cache key and never overwrites one, and is then
written to tests/fixtures/browser/<name>.capture.json without screenshots. A capture
that is not completed or partial stops the run. pytest never collects this file.
"""

import subprocess
import sys
from pathlib import Path

from earnings_ingestion.browser import ISOLATED_1, CaptureStatus, CaptureStore
from earnings_ingestion.browser import capture_once as capture_stored
from earnings_ingestion.browser.install import installed
from earnings_ingestion.browser.selenium_capture import SeleniumRenderer
from earnings_ingestion.browser.serialize import to_capture_json

REPO = Path(__file__).resolve().parents[2]
BROWSER = REPO / "tests" / "fixtures" / "browser"
RELEASES = REPO / "tests" / "fixtures" / "releases"
STORE = REPO / "data" / "runs" / "browser-capture"
PREREGISTER = REPO / "expirements" / "parser-fidelity" / "preregister.py"
USABLE = {CaptureStatus.COMPLETED, CaptureStatus.PARTIAL}


def preregistration_intact() -> str | None:
    """``None`` when ``preregister.py verify`` passes, else what it reported."""
    if not PREREGISTER.is_file():
        return "layout-1 is not pre-registered: preregister.py does not exist yet"
    result = subprocess.run(
        [sys.executable, str(PREREGISTER), "verify"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return None
    return (result.stdout + result.stderr).strip() or "verification failed"


def capture_one(renderer: SeleniumRenderer, source: Path, name: str) -> bool:
    store = CaptureStore(STORE, REPO)
    capture = capture_stored(
        renderer, store, source.read_bytes(), ISOLATED_1, source_document_id=name
    )
    if capture.status not in USABLE:
        print(
            f"{name}: {capture.status.value}: {capture.reason.value}: {capture.detail}"
        )
        return False
    target = BROWSER / f"{name}.capture.json"
    target.write_text(to_capture_json(capture), encoding="utf-8", newline="\n")
    print(f"wrote {target.relative_to(REPO)} ({capture.status.value})")
    return True


def main(argv: list[str]) -> int:
    if argv not in (["contract"], ["releases"]):
        print(__doc__)
        return 2
    binaries = installed()
    if binaries is None:
        print(
            "the pinned browser is not installed: run earnings-pipeline browser setup"
        )
        return 1
    renderer = SeleniumRenderer(binaries)
    if argv == ["contract"]:
        source = BROWSER / "contract-release.html"
        return 0 if capture_one(renderer, source, "contract-release") else 1
    refused = preregistration_intact()
    if refused is not None:
        print(f"refused: {refused}")
        return 1
    sources = sorted(RELEASES.glob("*/source.html"))
    captured = [capture_one(renderer, s, s.parent.name) for s in sources]
    return 0 if all(captured) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

Append to `.gitattributes`:

```text
tests/fixtures/browser/* -text
```

The attribute keeps Git from converting line endings in the fixtures, as it already
does for the release sources and the canonical fixtures.

- [ ] **Step 4: Capture the contract release**

```bash
uv run --locked --all-packages --extra browser-capture python tests/integration/capture_browser_fixtures.py contract
uv run --locked --all-packages --extra browser-capture python tests/integration/capture_browser_fixtures.py releases
```

Expected: `wrote tests/fixtures/browser/contract-release.capture.json (completed)`, then `refused: layout-1 is not pre-registered: preregister.py does not exist yet`, with exit status 1. The refusal is the point: no release can be captured before Task 10's freeze.

- [ ] **Step 5: Run the contract**

```bash
uv run --locked --all-packages pytest tests/contracts/test_element_schema_parsers.py -q
uv run --locked --all-packages --extra browser-capture pytest tests/contracts/test_element_schema_parsers.py -m browser -q -rs
```

Expected: `8 passed, 1 deselected`, then `1 passed, 8 deselected`: the pinned browser still renders the committed capture's text and layout.

- [ ] **Step 6: Run the checks**

```bash
python3 /tmp/plan5-escapes.py tests/contracts/test_element_schema_parsers.py tests/integration/capture_browser_fixtures.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
git status --short
```

Expected: `escapes intact`; `605 passed, 14 deselected`; `All checks passed!` and `146 files already formatted`. The status lists ` M .gitattributes`, ` M tests/contracts/test_element_schema_parsers.py`, `?? tests/fixtures/browser/`, and `?? tests/integration/capture_browser_fixtures.py`.

- [ ] **Step 7: Commit**

```bash
git log --oneline -3
git add tests/fixtures/browser/contract-release.html tests/fixtures/browser/contract-release.capture.json tests/integration/capture_browser_fixtures.py tests/contracts/test_element_schema_parsers.py .gitattributes
git commit -m "test(contracts): rerun the two-parser contract with walker-1 and layout-1"
```

---
### Task 10: The pre-registration — units, comparison, and freeze

This task fixes the comparison before any release is captured (PB-12, PB-13, PB-14).
It commits three things:

- **The targeted units.** They are derived from the gold and the frozen Stage 1
  walker's output. No capture is involved, so they exist before any capture does.
- **The comparison.** Its rules are unit-tested on synthetic scores.
- **The freeze.** It hashes every file that decides the comparison's numbers.

The freeze record is committed on its own, after the code it hashes. From then on,
`capture_browser_fixtures.py releases` runs, and a change to a frozen file needs a
recorded, permitted reason.

Do not capture a release or run `layout1_report.py` in this task. Its tests use
synthetic scores and never read a release capture.

**Files:**

- Create: `expirements/parser-fidelity/layout1_units.py`, `test_layout1_units.py`.
- Generate: `expirements/parser-fidelity/layout1-units.toml`.
- Create: `expirements/parser-fidelity/layout1_report.py`, `test_layout1_report.py`.
- Create: `expirements/parser-fidelity/preregister.py`, `test_preregister.py`.
- Generate: `expirements/parser-fidelity/layout1-preregistered.toml`, committed on its
  own.

**Interfaces:**

- Consumes:
  - from the frozen harness, never modified:
    - the frozen walker (`walker.parse`);
    - `score.py`: `CandidateText`, `match_block`, `scored_blocks`, `score_fixture`
      and `FixtureScore`;
    - `validate_gold.py`: `SourceText`, `TEXT_TYPES` and `load_gold`;
    - `pf_dump.Element`, `pf_decode.decode_html_bytes`, `pf_paths` and
      `pf_toml.toml_value`;
  - from plan 4: `walker1_report.project` and `excerpt`;
  - Task 8's `LayoutExtractor` and `fired`, and Task 3's `from_capture_json`.
- Produces:
  - **`layout1_units.py`.** `UNITS`, `CLASSES`,
    `Unit(klass, fixture, block, type)`, `stylesheets(text) -> int`,
    `fixture_units(fixture, raw, gold)`, `derive()`, `render(units)` and
    `load_units() -> list[Unit]`.
  - **`layout1_report.py`.**
    - Constants: `REPORT` (`docs/verification/layout-1-comparison.md`), `CAPTURES`,
      `CONFIGURATIONS`, `METRICS`, `HIGHER_BETTER` and `PROBES`.
    - Records: `Probe(finding, fixture, pattern)` and `Fixture`.
    - Functions: `load_fixture`, `load_fixtures()`, `metric_pairs`, `pooled`,
      `regression(metric, baseline, other) -> str | None`, `unit_lost`,
      `class_losses`, `repaired(losses, name) -> bool`, `regressions`,
      `probe_types` and `render(fixtures, units) -> str`.
  - **`preregister.py`.**
    - `PREREGISTERED_FILES`, the 23 paths.
    - `PREREGISTERED`, the record path.
    - `ALLOWED_REASONS = ("crash", "invalid-elements")`.
    - `record`, `verify` and `amend`.
    - The commands `record`, `verify`, and `amend PATH --reason R --note N`.

- [ ] **Step 1: Write the failing unit tests**

Create `expirements/parser-fidelity/test_layout1_units.py`:

```python
from collections import Counter

import pytest
from layout1_units import (
    CLASSES,
    UNITS,
    derive,
    fixture_units,
    load_units,
    render,
    stylesheets,
)


def test_the_committed_units_are_what_the_script_derives() -> None:
    assert UNITS.read_text(encoding="utf-8") == render(derive()), (
        "regenerate: uv run --locked --all-packages python"
        " expirements/parser-fidelity/layout1_units.py"
    )


def test_the_classes_hold_v2s_counts() -> None:
    units = load_units()
    assert Counter(unit.klass for unit in units) == {CLASSES[0]: 23, CLASSES[1]: 38}
    in_tables = Counter(unit.type for unit in units if unit.klass == CLASSES[1])
    assert in_tables == {"heading": 19, "paragraph": 13, "footnote": 6}
    assert len({(unit.klass, unit.fixture, unit.block) for unit in units}) == 61


@pytest.mark.parametrize(
    ("html", "count"),
    [
        ("<p>plain</p>", 0),
        ("<style>p { display: none }</style><p>x</p>", 1),
        ('<link rel="Stylesheet" href="a.css"><p>x</p>', 1),
        ('<link rel="icon" href="a.ico"><p>x</p>', 0),
    ],
)
def test_stylesheets_are_counted(html: str, count: int) -> None:
    assert stylesheets(html) == count


def test_a_fixture_with_a_stylesheet_stops_the_derivation() -> None:
    raw = b"<html><head><style>.x{}</style></head><body><p>x</p></body></html>"
    with pytest.raises(SystemExit, match="stop and report"):
        fixture_units("synthetic", raw, {"blocks": []})
```

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_layout1_units.py --import-mode=prepend -q`

Expected: `1 error during collection`: `ModuleNotFoundError: No module named 'layout1_units'`.

- [ ] **Step 2: Write the units script and derive the units**

Create `expirements/parser-fidelity/layout1_units.py`:

```python
"""layout-1's pre-registered targets: each targeted class's gold units (plan 5, PB-12).

    uv run --locked --all-packages python expirements/parser-fidelity/layout1_units.py

Writes layout1-units.toml from the gold and the frozen walker's output, never from a
browser capture, so the units are fixed before any capture exists. The classes are
the Stage 3 spec's three targeted residual classes:

1. ``styled_headings``: gold headings the frozen walker found and typed ``paragraph``
   (V2's 23);
2. ``prose_in_tables``: gold text blocks the frozen walker found inside a data table
   (V2's 49 merged blocks, less the 11 tables they merged with);
3. ``stylesheet_hidden``: content a stylesheet hides. The script refuses a fixture
   with a ``<style>`` element or a stylesheet link, since this plan pre-registers no
   definition for one; the eight fixtures have none, so the class is empty.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser

import tomllib
import walker as frozen
from pf_decode import decode_html_bytes
from pf_paths import FIXTURES, HARNESS, MANIFEST
from pf_toml import toml_value
from score import CandidateText, match_block, scored_blocks
from validate_gold import TEXT_TYPES, SourceText, load_gold

UNITS = HARNESS / "layout1-units.toml"
CLASSES = ("styled_headings", "prose_in_tables", "stylesheet_hidden")
HEADER = (
    "# layout-1's pre-registered targets (plan 5, PB-12). Generated by"
    " layout1_units.py; do not edit."
)


@dataclass(frozen=True)
class Unit:
    klass: str
    fixture: str
    block: str
    type: str


class _Stylesheets(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.count = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        rel = (dict(attrs).get("rel") or "").lower().split()
        if tag == "style" or (tag == "link" and "stylesheet" in rel):
            self.count += 1


def stylesheets(text: str) -> int:
    """``<style>`` elements and stylesheet links in a decoded source."""
    parser = _Stylesheets()
    parser.feed(text)
    parser.close()
    return parser.count


def fixture_units(fixture: str, raw: bytes, gold: dict) -> list[Unit]:
    """One fixture's units of classes 1 and 2, in gold order."""
    text = decode_html_bytes(raw).text
    if stylesheets(text):
        raise SystemExit(
            f"{fixture} carries a stylesheet, and class 3 has no pre-registered"
            " definition for one: stop and report"
        )
    elements = frozen.parse(text)
    candidate, source = CandidateText(elements), SourceText(raw)
    units = []
    for block in scored_blocks(gold):
        result = match_block(block, candidate, source)
        if not result.found:
            continue
        if (
            result.kind == "heading"
            and elements[result.start.position[0]].type == "paragraph"
        ):
            units.append(Unit(CLASSES[0], fixture, result.id, result.kind))
        if result.kind in TEXT_TYPES and any(
            elements[index].type == "table" for index in result.elements
        ):
            units.append(Unit(CLASSES[1], fixture, result.id, result.kind))
    return units


def derive() -> list[Unit]:
    """Every fixture's units, by class, then fixture, then gold order."""
    manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    units = []
    for entry in sorted(manifest["fixtures"], key=lambda e: e["fixture_id"]):
        directory = FIXTURES / entry["fixture_id"]
        raw = (directory / "source.html").read_bytes()
        units += fixture_units(entry["fixture_id"], raw, load_gold(directory))
    return sorted(units, key=lambda unit: CLASSES.index(unit.klass))


def render(units: list[Unit]) -> str:
    lines = [
        HEADER,
        "# From the gold and the frozen walker's output, never from a browser capture.",
        "",
        "[counts]",
    ]
    lines += [f"{name} = {sum(u.klass == name for u in units)}" for name in CLASSES]
    for unit in units:
        lines += [
            "",
            "[[units]]",
            f"class = {toml_value(unit.klass)}",
            f"fixture = {toml_value(unit.fixture)}",
            f"block = {toml_value(unit.block)}",
            f"type = {toml_value(unit.type)}",
        ]
    return "\n".join(lines) + "\n"


def load_units() -> list[Unit]:
    """The committed units."""
    data = tomllib.loads(UNITS.read_text(encoding="utf-8"))
    return [
        Unit(entry["class"], entry["fixture"], entry["block"], entry["type"])
        for entry in data["units"]
    ]


def main() -> int:
    UNITS.write_text(render(derive()), encoding="utf-8", newline="\n")
    print(f"wrote {UNITS.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```bash
uv run --locked --all-packages python expirements/parser-fidelity/layout1_units.py
head -7 expirements/parser-fidelity/layout1-units.toml
grep -c '^\[\[units\]\]' expirements/parser-fidelity/layout1-units.toml
uv run --locked --all-packages pytest expirements/parser-fidelity/test_layout1_units.py --import-mode=prepend -q
```

Expected: 

- `wrote layout1-units.toml`;
- the file's first seven lines: two comment lines, a blank line, `[counts]`,
  `styled_headings = 23`, `prose_in_tables = 38`, and `stylesheet_hidden = 0`;
- `61`, the number of units;
- `7 passed`.

Other counts mean the gold, the frozen walker, or the scorer has changed. Stop and
report.

- [ ] **Step 3: Write the comparison's failing tests**

Create `expirements/parser-fidelity/test_layout1_report.py`:

```python
"""The comparison's pre-registered rules, on synthetic scores: no capture needed."""

import re

import pytest
from earnings_core import RejectionReason
from earnings_ingestion.layout import AlignmentFailure, LayoutExtraction
from layout1_report import (
    PROBES,
    Fixture,
    metric_pairs,
    regression,
    repaired,
    unit_lost,
)
from layout1_units import Unit
from pf_dump import Cell, Element, Row
from score import score_fixture
from validate_gold import SourceText

HEADING = "Quarterly Results Overview"
PROSE = "Revenue rose five percent in the quarter."
RAW = f"<p>{HEADING}</p><p>{PROSE}</p>".encode()
GOLD = {
    "blocks": [
        {"id": "b001", "type": "heading", "level": 1, "start": HEADING},
        {"id": "b002", "type": "paragraph", "start": PROSE},
    ]
}
BLOCKS = {block["id"]: block for block in GOLD["blocks"]}


@pytest.mark.parametrize(
    ("metric", "baseline", "other", "found"),
    [
        ("header_section", (5, 23), (6, 23), None),
        ("header_section", (5, 23), (7, 23), "worse by 2/23, more than 1/23"),
        ("header_section", (5, 23), (0, 23), None),
        ("header_section", (7, 30), (7, 29), None),
        ("coverage", (70, 70), (69, 70), None),
        ("coverage", (70, 70), (68, 70), "worse by 1/35, more than 1/70"),
        ("cell_association", (10, 12), (11, 12), None),
        ("footnote_merging", (0, 0), (0, 0), None),
        ("footnote_merging", (0, 0), (0, 1), "not comparable: one denominator is zero"),
        ("header_section", (3, 30), (0, 0), "not comparable: one denominator is zero"),
        ("alignment", (0, 937), (1, 937), None),
        ("alignment", (0, 937), (2, 937), "worse by 2/937, more than 1/937"),
    ],
)
def test_a_regression_is_worse_by_more_than_one_nth(
    metric: str, baseline: tuple, other: tuple, found: str | None
) -> None:
    assert regression(metric, baseline, other) == found


def test_a_class_is_repaired_by_strictly_fewer_losses() -> None:
    unit = Unit("styled_headings", "f", "b001", "heading")
    losses = {"walker-1": [unit], "layout-1": [], "fallback": [unit]}
    assert repaired(losses, "layout-1")
    assert not repaired(losses, "fallback")
    assert not repaired({"walker-1": [], "layout-1": []}, "layout-1")


def fixture(projections: dict[str, list[Element]], triggers=()) -> Fixture:
    source = SourceText(RAW)
    failure = AlignmentFailure(
        reason=RejectionReason.LOCATOR_NOT_FOUND,
        unit_type="paragraph",
        text="gone",
        detail="no occurrence",
    )
    extraction = LayoutExtraction(
        layout_version="layout-1",
        mapping_policy="anchored-1",
        capture_id="c",
        doc_id="d",
        units=3,
        retypes={},
        elements=(),
        failures=(failure,),
    )
    return Fixture(
        fixture="f",
        klass="clean_html",
        gold=GOLD,
        source=source,
        result=None,
        capture=None,
        extraction=extraction,
        triggers=triggers,
        elements={},
        projections=projections,
        scores={
            name: score_fixture(GOLD, source, projection)
            for name, projection in projections.items()
        },
    )


def paragraph(text: str) -> Element:
    return Element("paragraph", text, source_type="p")


def heading(text: str) -> Element:
    return Element("heading", text, level=1, source_type="h1")


def in_table(text: str) -> Element:
    return Element(
        "table", text, source_type="table", rows=(Row(False, (Cell(text),)),)
    )


def test_a_heading_unit_is_lost_unless_its_home_is_a_heading() -> None:
    unit = Unit("styled_headings", "f", "b001", "heading")
    typed = {
        "walker-1": [paragraph(HEADING), paragraph(PROSE)],
        "layout-1": [heading(HEADING), paragraph(PROSE)],
        "fallback": [paragraph(HEADING), paragraph(PROSE)],
    }
    measured = fixture(typed)
    assert [unit_lost(measured, name, unit, BLOCKS) for name in typed] == [
        True,
        False,
        True,
    ]


def test_a_prose_unit_is_lost_while_any_of_its_elements_is_a_table() -> None:
    unit = Unit("prose_in_tables", "f", "b002", "paragraph")
    typed = {
        "walker-1": [heading(HEADING), in_table(PROSE)],
        "layout-1": [heading(HEADING), paragraph(PROSE)],
        "fallback": [heading(HEADING)],
    }
    measured = fixture(typed)
    assert [unit_lost(measured, name, unit, BLOCKS) for name in typed] == [
        True,
        False,
        True,
    ]


@pytest.mark.parametrize("triggers", [(), ("no_heading",)])
def test_the_fallback_counts_alignment_failures_only_where_it_switches(
    triggers: tuple,
) -> None:
    typed = {
        name: [heading(HEADING), paragraph(PROSE)]
        for name in ("walker-1", "layout-1", "fallback")
    }
    pairs = metric_pairs(fixture(typed, triggers))
    assert pairs["walker-1"]["alignment"] == (0, 3)
    assert pairs["layout-1"]["alignment"] == (1, 3)
    assert pairs["fallback"]["alignment"] == ((1, 3) if triggers else (0, 3))
    assert pairs["walker-1"]["coverage"] == (2, 2)
    assert pairs["walker-1"]["altered"] == (0, 2)


def test_every_metric_is_reported_for_every_configuration() -> None:
    typed = {
        name: [heading(HEADING), paragraph(PROSE)]
        for name in ("walker-1", "layout-1", "fallback")
    }
    pairs = metric_pairs(fixture(typed))
    wanted = {
        "coverage",
        "reading_order",
        "header_section",
        "footnote_merging",
        "header_table",
        "cell_association",
        "altered",
        "alignment",
    }
    assert all(set(by_metric) == wanted for by_metric in pairs.values())


@pytest.mark.parametrize(
    ("finding", "text"),
    [
        (
            "NHI's headline",
            "NHI Reports 17.2% Increase in Third Quarter Normalized FFO",
        ),
        ("Becton Dickinson's statement titles", "BECTON DICKINSON AND COMPANY"),
        ("End marks", "# # #"),
        ("End marks", "***"),
        ("End marks", "###"),
        ("End marks", "***** ***** *****"),
        ("Ball's numbered running heads", "Ball Corp - 4"),
        (
            "FMC's numbered running heads",
            "Page 6/ FMC Corporation Announces Fourth Quarter Results",
        ),
        (
            "Becton Dickinson's non-GAAP footnotes",
            "1Represents a non-GAAP financial measure; refer to reconciliations.",
        ),
        (
            "Southwestern Energy's forward-looking-statements continuation",
            "rates and the ability of the company" + chr(0x2019) + "s lenders to act",
        ),
    ],
)
def test_each_probe_matches_its_findings_text(finding: str, text: str) -> None:
    [probe] = [probe for probe in PROBES if probe.finding == finding]
    assert re.fullmatch(probe.pattern, text, re.DOTALL)


def test_end_marks_never_match_prose() -> None:
    [probe] = [probe for probe in PROBES if probe.finding == "End marks"]
    assert not re.fullmatch(probe.pattern, "# of shares", re.DOTALL)
```

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_layout1_report.py --import-mode=prepend -q`

Expected: `1 error during collection`: `ModuleNotFoundError: No module named 'layout1_report'`.

- [ ] **Step 4: Write the comparison**

Create `expirements/parser-fidelity/layout1_report.py`:

```python
"""layout-1's pre-registered comparison (Stage 3 spec, Pre-registered comparison).

    uv run --locked --all-packages python expirements/parser-fidelity/layout1_report.py

Writes docs/verification/layout-1-comparison.md from the gold, walker-1's output, the
committed fixture captures in tests/fixtures/browser/, and layout1-units.toml. Three
configurations are projected to the dump format by walker1_report.project and scored
by the frozen score.py:

1. ``walker-1``: walker-1, with C1-C5;
2. ``layout-1``: layout-1's element stream, mapped onto walker-1's text, for every
   document;
3. ``fallback``: layout-1's stream for exactly the documents where walker-1's output
   fires a trigger (canonical/triggers.py), and walker-1's elsewhere.

The rules were fixed before any release was captured (plan 5, PB-14), and every
comparison is an exact count or an exact fraction:

- A targeted class is repaired when a configuration loses strictly fewer of its units
  than walker-1. A heading unit is lost when it is missed or in the scorer's
  header_lost; a prose unit, when it is missed or any element it matches is a table.
- A regression is a metric worse than walker-1's by more than 1/n in a fixture class,
  n being walker-1's denominator there. A metric whose denominator is zero on one side
  only is not comparable, and counts as a regression.
- The promotion rule allows a configuration only when it repairs a targeted class
  with no regression.

These are development-set numbers: the fixtures were Stage 1's test set (SC2).
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

import tomllib
from earnings_core import DocumentElement, ElementType
from earnings_ingestion.browser.records import RenderedCapture
from earnings_ingestion.browser.serialize import from_capture_json
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.canonical.triggers import fired
from earnings_ingestion.layout import LayoutExtraction, LayoutExtractor
from layout1_units import CLASSES, Unit, load_units
from pf_dump import Element
from pf_paths import FIXTURES, HARNESS, MANIFEST, REPO_ROOT
from score import CandidateText, FixtureScore, match_block, score_fixture
from validate_gold import SourceText, load_gold
from walker1_report import excerpt, project

REPORT = REPO_ROOT / "docs" / "verification" / "layout-1-comparison.md"
CAPTURES = REPO_ROOT / "tests" / "fixtures" / "browser"
PREREGISTERED = HARNESS / "layout1-preregistered.toml"
CONFIGURATIONS = ("walker-1", "layout-1", "fallback")
CANDIDATES = CONFIGURATIONS[1:]
METRICS = (
    ("block coverage", "coverage"),
    ("reading order", "reading_order"),
    ("heading loss", "header_section"),
    ("footnote merging", "footnote_merging"),
    ("table-header retention", "header_table"),
    ("cell association", "cell_association"),
    ("altered anchors", "altered"),
    ("alignment failures", "alignment"),
)
"""The spec's eight metrics: its name, and the count it reads. Table-header retention
counts header texts lost; altered anchors count over the scored gold blocks;
alignment failures count over layout-1's units, and walker-1 aligns nothing."""
HIGHER_BETTER = frozenset({"coverage", "cell_association"})
CLASS_NAMES = {
    "styled_headings": "1. headings typed paragraph by W12",
    "prose_in_tables": "2. prose inside data tables",
    "stylesheet_hidden": "3. content hidden by stylesheets",
}


@dataclass(frozen=True)
class Probe:
    """One of plan 4's open review-gate findings, found by its elements' text."""

    finding: str
    fixture: str | None
    """``None``: every fixture."""
    pattern: str
    """Matched against a whole element's text."""


PROBES = (
    Probe(
        "NHI's headline",
        "0000877860-13-000100_ex-99-1",
        r"NHI Reports 17\.2% Increase in Third Quarter Normalized FFO",
    ),
    Probe(
        "Becton Dickinson's statement titles",
        "0000010795-22-000014_ex-99-1",
        r"BECTON DICKINSON AND COMPANY",
    ),
    Probe("End marks", None, r"[#*]+(?: [#*]+)*"),
    Probe(
        "Ball's numbered running heads",
        "0000009389-10-000004_ex-99-1",
        r"Ball Corp - \d+",
    ),
    Probe(
        "FMC's numbered running heads",
        "0000037785-14-000003_ex-99-1",
        r"Page \d+/ FMC Corporation Announces Fourth Quarter Results",
    ),
    Probe(
        "Becton Dickinson's non-GAAP footnotes",
        "0000010795-22-000014_ex-99-1",
        r"1 ?Represents a non-GAAP financial measure.*",
    ),
    Probe(
        "Southwestern Energy's forward-looking-statements continuation",
        "0000007332-09-000032_ex-99",
        r"rates and the ability of the company.s lenders.*",
    ),
)


@dataclass
class Fixture:
    """One release under the three configurations."""

    fixture: str
    klass: str
    gold: dict
    source: SourceText
    result: Canonicalized
    capture: RenderedCapture
    extraction: LayoutExtraction
    triggers: tuple[str, ...]
    elements: dict[str, tuple[DocumentElement, ...]]
    projections: dict[str, list[Element]]
    scores: dict[str, FixtureScore]


def load_fixture(fixture: str, klass: str) -> Fixture:
    directory = FIXTURES / fixture
    raw = (directory / "source.html").read_bytes()
    result = canonicalize(raw, source_document_id=fixture, media_type="text/html")
    if not isinstance(result, Canonicalized):
        raise SystemExit(f"{fixture}: {result.reason.value}: {result.detail}")
    path = CAPTURES / f"{fixture}.capture.json"
    if not path.is_file():
        raise SystemExit(f"{path.relative_to(REPO_ROOT)} is missing: capture first")
    capture = from_capture_json(path.read_text(encoding="utf-8"))
    extraction = LayoutExtractor().map_onto(capture, result.document)
    triggers = fired(result.document, result.elements)
    elements = {
        "walker-1": result.elements,
        "layout-1": extraction.elements,
        "fallback": extraction.elements if triggers else result.elements,
    }
    text = result.document.canonical_text
    projections = {name: project(text, elements[name])[0] for name in CONFIGURATIONS}
    gold, source = load_gold(directory), SourceText(raw)
    return Fixture(
        fixture=fixture,
        klass=klass,
        gold=gold,
        source=source,
        result=result,
        capture=capture,
        extraction=extraction,
        triggers=triggers,
        elements=elements,
        projections=projections,
        scores={
            name: score_fixture(gold, source, projections[name])
            for name in CONFIGURATIONS
        },
    )


def load_fixtures() -> list[Fixture]:
    manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    return [
        load_fixture(entry["fixture_id"], entry["primary_class"])
        for entry in sorted(manifest["fixtures"], key=lambda e: e["fixture_id"])
    ]


def metric_pairs(fixture: Fixture) -> dict[str, dict[str, tuple[int, int]]]:
    """Each configuration's (numerator, denominator) for each metric."""
    units = fixture.extraction.units
    failures = {
        "walker-1": 0,
        "layout-1": len(fixture.extraction.failures),
        "fallback": len(fixture.extraction.failures) if fixture.triggers else 0,
    }
    out: dict[str, dict[str, tuple[int, int]]] = {}
    for name in CONFIGURATIONS:
        score = fixture.scores[name]
        pairs = {
            metric: (score.counts[metric][0], score.counts[metric][1])
            for _, metric in METRICS
            if metric in score.counts
        }
        pairs["altered"] = (len(score.altered), score.counts["coverage"][1])
        pairs["alignment"] = (failures[name], units)
        out[name] = pairs
    return out


def pooled(fixtures: Sequence[Fixture], name: str, metric: str) -> tuple[int, int]:
    pairs = [metric_pairs(fixture)[name][metric] for fixture in fixtures]
    return sum(pair[0] for pair in pairs), sum(pair[1] for pair in pairs)


def regression(
    metric: str, baseline: tuple[int, int], other: tuple[int, int]
) -> str | None:
    """Why ``other`` regresses from walker-1's ``baseline``, or ``None``: worse by more
    than 1/n, n being walker-1's denominator, as exact fractions."""
    (a, n), (b, m) = baseline, other
    if n == 0 and m == 0:
        return None
    if n == 0 or m == 0:
        return "not comparable: one denominator is zero"
    worse = Fraction(a, n) - Fraction(b, m)
    if metric not in HIGHER_BETTER:
        worse = -worse
    if worse > Fraction(1, n):
        return f"worse by {worse}, more than 1/{n}"
    return None


def unit_lost(fixture: Fixture, name: str, unit: Unit, blocks: dict) -> bool:
    """The pre-registered loss of one targeted unit under one configuration."""
    score = fixture.scores[name]
    if unit.block in score.residual["missed"]:
        return True
    if unit.klass == CLASSES[0]:
        return unit.block in score.residual["header_lost"]
    projection = fixture.projections[name]
    result = match_block(blocks[unit.block], CandidateText(projection), fixture.source)
    return any(projection[index].type == "table" for index in result.elements)


def class_losses(
    fixtures: Sequence[Fixture], units: Sequence[Unit]
) -> dict[str, dict[str, list[Unit]]]:
    """For each class and configuration, the units lost."""
    by_id = {fixture.fixture: fixture for fixture in fixtures}
    blocks = {
        fixture.fixture: {block["id"]: block for block in fixture.gold["blocks"]}
        for fixture in fixtures
    }
    return {
        klass: {
            name: [
                unit
                for unit in units
                if unit.klass == klass
                and unit_lost(by_id[unit.fixture], name, unit, blocks[unit.fixture])
            ]
            for name in CONFIGURATIONS
        }
        for klass in CLASSES
    }


def repaired(losses: dict[str, list[Unit]], name: str) -> bool:
    return len(losses[name]) < len(losses["walker-1"])


def regressions(fixtures: Sequence[Fixture], name: str) -> list[str]:
    """Every regression of one configuration, as ``class, metric: why``."""
    found = []
    for klass in sorted({fixture.klass for fixture in fixtures}):
        members = [fixture for fixture in fixtures if fixture.klass == klass]
        for label, metric in METRICS:
            why = regression(
                metric,
                pooled(members, "walker-1", metric),
                pooled(members, name, metric),
            )
            if why is not None:
                found.append(f"{klass}, {label}: {why}")
    return found


def probe_types(fixture: Fixture, probe: Probe, name: str) -> Counter[str]:
    """The types of the elements whose whole text the probe matches."""
    pattern = re.compile(probe.pattern, re.DOTALL)
    text = fixture.result.document.canonical_text
    return Counter(
        element.type.value
        for element in fixture.elements[name]
        if element.type not in (ElementType.SENTENCE, ElementType.TABLE_CELL)
        and pattern.fullmatch(element.span.slice_of(text))
    )


def render(fixtures: Sequence[Fixture], units: Sequence[Unit]) -> str:
    losses = class_losses(fixtures, units)
    lines = [
        "# layout-1: the pre-registered comparison",
        "",
        "Generated by `expirements/parser-fidelity/layout1_report.py`; do not edit.",
        "Development-set numbers: the fixtures were Stage 1's test set (SC2).",
        "",
        *_preregistration(),
        "",
        "## Versions",
        "",
        *_versions(fixtures),
        "",
        "## Captures",
        "",
        (
            "| Fixture | Class | Status | Blocked (required) | Units"
            " | Alignment failures | Triggers | layout-1 retypes |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for fixture in fixtures:
        capture, extraction = fixture.capture, fixture.extraction
        required = sum(request.required for request in capture.blocked_requests)
        retypes = ", ".join(
            f"{rule} {count}" for rule, count in extraction.retypes.items() if count
        )
        lines.append(
            f"| `{fixture.fixture}` | {fixture.klass} | {capture.status.value}"
            f" | {len(capture.blocked_requests)} ({required}) | {extraction.units}"
            f" | {len(extraction.failures)} | {', '.join(fixture.triggers) or 'none'}"
            f" | {retypes or 'none'} |"
        )
    lines += [
        "",
        "## Targeted classes",
        "",
        "Units lost out of each class's pre-registered units (layout1-units.toml).",
        "",
        "| Class | Units | walker-1 | layout-1 | fallback | Repaired by |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for klass in CLASSES:
        total = sum(unit.klass == klass for unit in units)
        by = [name for name in CANDIDATES if repaired(losses[klass], name)]
        lines.append(
            f"| {CLASS_NAMES[klass]} | {total}"
            + "".join(f" | {len(losses[klass][name])}" for name in CONFIGURATIONS)
            + f" | {', '.join(by) or 'none'} |"
        )
    lines += [
        "",
        "## Metrics by fixture class",
        "",
        "Exact counts pooled over each class's fixtures, as numerator/denominator.",
        "Block coverage and cell association count successes; every other metric",
        "counts losses. A mark is the pre-registered regression rule's finding.",
        "",
        "| Class | Metric | walker-1 | layout-1 | fallback |",
        "| --- | --- | --- | --- | --- |",
    ]
    for klass in sorted({fixture.klass for fixture in fixtures}):
        members = [fixture for fixture in fixtures if fixture.klass == klass]
        for label, metric in METRICS:
            baseline = pooled(members, "walker-1", metric)
            cells = [_pair(baseline)]
            for name in CANDIDATES:
                pair = pooled(members, name, metric)
                why = regression(metric, baseline, pair)
                cells.append(_pair(pair) + (" (regression)" if why else ""))
            lines.append(f"| {klass} | {label} | " + " | ".join(cells) + " |")
    lines += ["", "## Verdict", ""]
    allowed = ["1 (diagnostic-only capture)"]
    for name, outcome in zip(
        CANDIDATES,
        ("3 (layout-1 for every document)", "2 (the fallback, as walker-2)"),
        strict=True,
    ):
        fixed = [CLASS_NAMES[k] for k in CLASSES if repaired(losses[k], name)]
        worse = regressions(fixtures, name)
        eligible = bool(fixed) and not worse
        lines += [
            f"### {name}",
            "",
            f"- Repaired classes: {'; '.join(fixed) or 'none'}.",
            f"- Regressions: {len(worse)}.",
            *(f"  - {why}" for why in worse),
            (
                f"- The promotion rule {'allows' if eligible else 'does not allow'}"
                f" outcome {outcome}."
            ),
            "",
        ]
        if eligible:
            allowed.append(outcome)
    lines.append(
        "ADR 0002 chooses among the outcomes the rule allows: "
        + "; ".join(sorted(allowed))
        + "."
    )
    lines += ["", "## Units", ""]
    for klass in CLASSES:
        members = [unit for unit in units if unit.klass == klass]
        lines += [f"### {CLASS_NAMES[klass]}", ""]
        if not members:
            empty = "No units."
            if klass == CLASSES[2]:
                empty = "No units: no fixture carries a stylesheet."
            lines += [empty, ""]
            continue
        lines += [
            "| Fixture | Block | Type | walker-1 | layout-1 | fallback |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for unit in members:
            marks = [
                "lost" if unit in losses[klass][name] else "kept"
                for name in CONFIGURATIONS
            ]
            lines.append(
                f"| `{unit.fixture}` | {unit.block} | {unit.type} | "
                + " | ".join(marks)
                + " |"
            )
        lines.append("")
    lines += ["## Alignment failures", ""]
    failures = [
        (fixture.fixture, failure)
        for fixture in fixtures
        for failure in fixture.extraction.failures
    ]
    if not failures:
        lines.append("None.")
    else:
        lines += ["| Fixture | Reason | Unit | Text |", "| --- | --- | --- | --- |"]
        lines += [
            f"| `{fixture}` | {failure.reason.value} | {failure.unit_type}"
            f" | {excerpt(failure.text)} |"
            for fixture, failure in failures
        ]
    lines += [
        "",
        "## Review-gate findings",
        "",
        "Plan 4's open findings (docs/verification/walker-1.md, The review gate): the",
        "elements whose whole text each finding's pattern matches, by type.",
        "",
        "| Finding | Fixture | walker-1 | layout-1 | fallback |",
        "| --- | --- | --- | --- | --- |",
    ]
    for probe in PROBES:
        for fixture in fixtures:
            if probe.fixture not in (None, fixture.fixture):
                continue
            counts = [probe_types(fixture, probe, name) for name in CONFIGURATIONS]
            if not any(counts):
                continue
            lines.append(
                f"| {probe.finding} | `{fixture.fixture}` | "
                + " | ".join(_types(count) for count in counts)
                + " |"
            )
    return "\n".join(lines) + "\n"


def _preregistration() -> list[str]:
    record = tomllib.loads(PREREGISTERED.read_text(encoding="utf-8"))
    changes = record.get("changes", [])
    lines = [
        (
            f"Pre-registered on {record['frozen_on']} at commit"
            f" `{record['commit'][:12]}`, before any release was captured;"
            f" {len(changes)} recorded post-freeze fixes."
        )
    ]
    lines += [
        f"- {change['date']}: `{change['file']}`, {change['reason']}: {change['note']}"
        for change in changes
    ]
    return lines


def _versions(fixtures: Sequence[Fixture]) -> list[str]:
    environments = Counter(
        (
            c.browser_engine,
            c.browser_version,
            c.driver_version,
            c.selenium_version,
            c.os_name,
            c.os_version,
            c.architecture,
            c.capture_policy,
            c.capture_policy_version,
            c.metadata_version,
        )
        for c in (fixture.capture for fixture in fixtures)
    )
    lines = [
        (
            f"- walker-1 (C1-C5); {fixtures[0].extraction.layout_version}, mapped by"
            f" {fixtures[0].extraction.mapping_policy}."
        ),
    ]
    for environment, count in sorted(environments.items()):
        engine, browser, driver, selenium, os_name, os_version, arch = environment[:7]
        policy, policy_version, metadata = environment[7:]
        lines.append(
            f"- {count} captures: {engine} {browser}, chromedriver {driver},"
            f" Selenium {selenium}, {os_name} {os_version} {arch};"
            f" capture policy {policy}/{policy_version}, {metadata}."
        )
    return lines


def _pair(pair: tuple[int, int]) -> str:
    return f"{pair[0]}/{pair[1]}"


def _types(counts: Counter[str]) -> str:
    return ", ".join(f"{kind} {n}" for kind, n in sorted(counts.items())) or "none"


def main() -> int:
    REPORT.write_text(
        render(load_fixtures(), load_units()), encoding="utf-8", newline="\n"
    )
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_layout1_report.py --import-mode=prepend -q`

Expected: `29 passed`.

- [ ] **Step 5: Write the freeze's failing tests**

Create `expirements/parser-fidelity/test_preregister.py`:

```python
import datetime as dt

import pytest
from pf_paths import REPO_ROOT
from preregister import (
    PREREGISTERED,
    PREREGISTERED_FILES,
    amend,
    load,
    record,
    verify,
)

TODAY = dt.date(2026, 10, 2)
LAYOUT = "packages/earnings-ingestion/src/earnings_ingestion/layout/blocks.py"


@pytest.fixture
def root(tmp_path):
    for name in PREREGISTERED_FILES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {name}\n")
    return tmp_path


def test_every_preregistered_file_exists() -> None:
    assert [
        name for name in PREREGISTERED_FILES if not (REPO_ROOT / name).is_file()
    ] == []


def test_the_committed_record_verifies_once_it_exists() -> None:
    if not PREREGISTERED.exists():
        pytest.skip("layout-1 is not pre-registered yet (plan 5, Task 10)")
    assert verify(REPO_ROOT, PREREGISTERED) == []


def test_record_then_verify_passes(root) -> None:
    record_file = root / "layout1-preregistered.toml"
    record(root, record_file, "abc123", TODAY)
    assert verify(root, record_file) == []
    assert load(record_file)["commit"] == "abc123"
    with pytest.raises(FileExistsError):
        record(root, record_file, "def456", TODAY)


def test_a_change_after_the_freeze_fails_verification(root) -> None:
    record_file = root / "layout1-preregistered.toml"
    record(root, record_file, "abc123", TODAY)
    (root / LAYOUT).write_text("# a retuned heading rule\n")
    assert verify(root, record_file) == [
        f"{LAYOUT} changed after the pre-registration without a recorded fix"
    ]


def test_amend_records_a_crash_fix_and_refuses_tuning(root) -> None:
    record_file = root / "layout1-preregistered.toml"
    record(root, record_file, "abc123", TODAY)
    with pytest.raises(ValueError, match="reason must be one of"):
        amend(root, record_file, LAYOUT, "tuning", "better headings", TODAY)
    with pytest.raises(ValueError, match="unchanged"):
        amend(root, record_file, LAYOUT, "crash", "nothing", TODAY)
    (root / LAYOUT).write_text("# a crash fix\n")
    amend(root, record_file, LAYOUT, "crash", "an empty cell crashed", TODAY)
    assert verify(root, record_file) == []
    [change] = load(record_file)["changes"]
    assert change["reason"] == "crash" and change["previous_sha256"] != change["sha256"]
```

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_preregister.py --import-mode=prepend -q`

Expected: `1 error during collection`: `ModuleNotFoundError: No module named 'preregister'`.

- [ ] **Step 6: Write the freeze**

Create `expirements/parser-fidelity/preregister.py`:

```python
"""Freeze layout-1 and its comparison before any fixture is captured (plan 5, PB-13).

    uv run --locked --all-packages python expirements/parser-fidelity/preregister.py record
    uv run --locked --all-packages python expirements/parser-fidelity/preregister.py verify
    uv run --locked --all-packages python expirements/parser-fidelity/preregister.py amend PATH --reason crash --note "..."

``record`` writes layout1-preregistered.toml with the SHA-256 of every file that
decides the pre-registered comparison's numbers: the capture adapter, its extractor,
policy, records, and fixture format; layout-1 and the modules it runs; the fallback's
triggers; the units and their loader; the comparison; and the frozen scorer it calls.
The files must be committed first, and the record is committed before
tests/integration/capture_browser_fixtures.py captures any release.

After the freeze a file may change only to fix a crash, or an element set that
``validate_elements`` refuses, on a fixture capture; ``amend`` records such a change,
and ``verify`` fails on any change that is not recorded. A change may never alter a
type decision, a mapping rule, a unit, or a metric, and every amendment makes the
comparison's numbers post-hoc, which the verification record says.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path

import tomllib
from pf_paths import HARNESS, REPO_ROOT
from pf_toml import Bare, toml_value

_SOURCE = "packages/earnings-ingestion/src/earnings_ingestion"
_HARNESS = "expirements/parser-fidelity"
PREREGISTERED_FILES = (
    f"{_SOURCE}/browser/metadata.py",
    f"{_SOURCE}/browser/policy.py",
    f"{_SOURCE}/browser/records.py",
    f"{_SOURCE}/browser/selenium_capture.py",
    f"{_SOURCE}/browser/serialize.py",
    f"{_SOURCE}/canonical/blocks.py",
    f"{_SOURCE}/canonical/compensate.py",
    f"{_SOURCE}/canonical/dom.py",
    f"{_SOURCE}/canonical/normalize.py",
    f"{_SOURCE}/canonical/triggers.py",
    f"{_SOURCE}/canonical/walker.py",
    f"{_SOURCE}/layout/__init__.py",
    f"{_SOURCE}/layout/align.py",
    f"{_SOURCE}/layout/blocks.py",
    f"{_SOURCE}/layout/extract.py",
    f"{_SOURCE}/layout/records.py",
    f"{_HARNESS}/layout1-units.toml",
    f"{_HARNESS}/layout1_report.py",
    f"{_HARNESS}/layout1_units.py",
    f"{_HARNESS}/pf_text.py",
    f"{_HARNESS}/score.py",
    f"{_HARNESS}/validate_gold.py",
    f"{_HARNESS}/walker1_report.py",
)
PREREGISTERED = HARNESS / "layout1-preregistered.toml"
ALLOWED_REASONS = ("crash", "invalid-elements")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(record_file: Path) -> dict:
    return tomllib.loads(record_file.read_text(encoding="utf-8"))


def expected_hashes(record: dict) -> dict[str, str]:
    expected = dict(record["files"])
    for change in record.get("changes", []):
        expected[change["file"]] = change["sha256"]
    return expected


def render(record: dict) -> str:
    lines = [
        "# Pre-registered before any release capture. Generated by preregister.py.",
        f"frozen_on = {toml_value(Bare(str(record['frozen_on'])))}",
        f"commit = {toml_value(record['commit'])}",
        "",
        "[files]",
    ]
    lines += [
        f"{toml_value(name)} = {toml_value(sha)}"
        for name, sha in record["files"].items()
    ]
    for change in record.get("changes", []):
        lines += ["", "[[changes]]"]
        lines += [
            f"{key} = {toml_value(Bare(str(change[key])) if key == 'date' else change[key])}"
            for key in ("file", "reason", "previous_sha256", "sha256", "date", "note")
        ]
    return "\n".join(lines) + "\n"


def record(root: Path, record_file: Path, commit: str, today: dt.date) -> dict:
    if record_file.exists():
        raise FileExistsError(
            f"{record_file.name} exists; use amend for a permitted post-freeze fix"
        )
    frozen = {
        "frozen_on": today,
        "commit": commit,
        "files": {name: sha256_of(root / name) for name in PREREGISTERED_FILES},
    }
    record_file.write_text(render(frozen), encoding="utf-8")
    return frozen


def verify(root: Path, record_file: Path) -> list[str]:
    if not record_file.exists():
        return [f"{record_file.name} is missing: run `preregister.py record` first"]
    return [
        f"{name} changed after the pre-registration without a recorded fix"
        for name, sha in expected_hashes(load(record_file)).items()
        if not (root / name).is_file() or sha256_of(root / name) != sha
    ]


def amend(
    root: Path, record_file: Path, name: str, reason: str, note: str, today: dt.date
) -> dict:
    if reason not in ALLOWED_REASONS:
        raise ValueError(
            f"reason must be one of {ALLOWED_REASONS}; type decisions, mapping rules,"
            " units, and metrics never change"
        )
    frozen = load(record_file)
    previous = expected_hashes(frozen)[name]
    current = sha256_of(root / name)
    if current == previous:
        raise ValueError(f"{name} is unchanged; nothing to amend")
    change = {
        "file": name,
        "reason": reason,
        "previous_sha256": previous,
        "sha256": current,
        "date": today,
        "note": note,
    }
    frozen.setdefault("changes", []).append(change)
    record_file.write_text(render(frozen), encoding="utf-8")
    return frozen


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("record")
    sub.add_parser("verify")
    fix = sub.add_parser("amend")
    fix.add_argument("file", choices=PREREGISTERED_FILES)
    fix.add_argument("--reason", required=True, choices=ALLOWED_REASONS)
    fix.add_argument("--note", required=True)
    args = parser.parse_args(argv)
    today = dt.datetime.now(dt.UTC).date()

    if args.command == "verify":
        problems = verify(REPO_ROOT, PREREGISTERED)
        print("\n".join(problems) or "pre-registration verified")
        return 1 if problems else 0
    if (
        _git("diff", "--quiet", "HEAD", "--", *PREREGISTERED_FILES).returncode != 0
        or _git("ls-files", "--error-unmatch", *PREREGISTERED_FILES).returncode != 0
    ):
        print(
            "commit every pre-registered file first; the record must name a commit"
            " that contains them",
            file=sys.stderr,
        )
        return 1
    if args.command == "record":
        commit = _git("rev-parse", "HEAD").stdout.strip()
        record(REPO_ROOT, PREREGISTERED, commit, today)
        print(
            f"pre-registered {len(PREREGISTERED_FILES)} files at {commit};"
            f" commit {PREREGISTERED.name} now"
        )
        return 0
    amend(REPO_ROOT, PREREGISTERED, args.file, args.reason, args.note, today)
    print(
        f"recorded a post-freeze {args.reason} fix to {args.file};"
        f" commit it with {PREREGISTERED.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_preregister.py --import-mode=prepend -rs -q`

Expected: `4 passed, 1 skipped`. The skip reads `layout-1 is not pre-registered yet (plan 5, Task 10)`, and Step 9 removes it.

- [ ] **Step 7: Run the checks**

```bash
python3 /tmp/plan5-escapes.py expirements/parser-fidelity/layout1_units.py expirements/parser-fidelity/test_layout1_units.py expirements/parser-fidelity/layout1_report.py expirements/parser-fidelity/test_layout1_report.py expirements/parser-fidelity/preregister.py expirements/parser-fidelity/test_preregister.py
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
```

Expected: `escapes intact`; `262 passed, 1 skipped`; `605 passed, 14 deselected`; `All checks passed!` and `152 files already formatted`; `freeze verified`.

- [ ] **Step 8: Commit the units and the comparison**

```bash
git log --oneline -3
git add expirements/parser-fidelity/layout1_units.py expirements/parser-fidelity/test_layout1_units.py expirements/parser-fidelity/layout1-units.toml expirements/parser-fidelity/layout1_report.py expirements/parser-fidelity/test_layout1_report.py expirements/parser-fidelity/preregister.py expirements/parser-fidelity/test_preregister.py
git commit -m "feat(harness): pre-register layout-1's targeted units and comparison rules"
```

- [ ] **Step 9: Freeze, and commit the record on its own**

```bash
git status --short
uv run --locked --all-packages python expirements/parser-fidelity/preregister.py record
uv run --locked --all-packages python expirements/parser-fidelity/preregister.py verify
uv run --locked --all-packages pytest expirements/parser-fidelity/test_preregister.py --import-mode=prepend -q
git log --oneline -3
git add expirements/parser-fidelity/layout1-preregistered.toml
git commit -m "chore(harness): freeze layout-1 and its comparison before any release capture"
```

Expected:

- `git status --short` prints nothing: `record` refuses while a frozen file differs
  from `HEAD`;
- `pre-registered 23 files at <the Step 8 commit>; commit layout1-preregistered.toml now`;
- `pre-registration verified`;
- `5 passed`: the committed record now verifies.

From this commit on, every file in `PREREGISTERED_FILES` is frozen (PB-13).

---
### Task 11: The release captures and calibration

With the comparison frozen, the eight Stage 1 releases are captured once, in the
pinned environment, and committed as fixtures (PB-7). Their checks run offline:

- each capture is usable and of its own bytes;
- each round-trips byte for byte;
- all share one environment;
- every layout-1 unit is an exact span or a recorded alignment failure (exit
  criterion 5).

A browser-marked test recaptures each release and requires the same text and layout
hashes (exit criterion 4).

Calibration then compares three captures' `innerText` with the user's copies, and
classes every difference (PB-15, exit criterion 2). This task is the first to open a
release's copy.

**If a release breaks frozen code.** Suppose a capture makes layout-1 crash, or
`validate_elements` refuses its elements. That is the one case PB-13 permits:

1. fix the code;
2. run `preregister.py amend <path> --reason crash` (or `--reason invalid-elements`)
   with a `--note` saying what failed;
3. commit the fix with the updated `layout1-preregistered.toml`;
4. disclose it in Task 15's record.

Never change a type decision, a mapping rule, a unit, or a metric. An alignment
failure is not a crash: it is recorded, and it counts in the comparison.

**Files:**

- Generate: `tests/fixtures/browser/<fixture>.capture.json`, one per release (eight).
- Test (create): `tests/integration/test_browser_fixtures.py`.
- Create: `expirements/parser-fidelity/calibrate.py`, `test_calibrate.py`,
  `test_calibrate_current.py`.
- Generate: `docs/verification/browser-calibration.md`.

**Interfaces:**

- Consumes:
  - Task 9's capture script and Task 10's freeze;
  - `LayoutExtractor` and `canonicalize`;
  - the walker's `BULLETS`, and the frozen `pf_decode.decode_html_bytes`;
  - the user's copies in `data/runs/parser-fidelity/gold-drafts/`.
- Produces:
  - **The committed release captures,** which Tasks 12–14 read.
  - **`calibrate.py`.**
    - Constants: `REPORT`, `CALIBRATED` and `KINDS`.
    - Records: `Difference(kind, captured, copied)` and `SourceFacts`.
    - Functions: `source_facts(html)`,
      `differences(captured, copied, facts) -> list[Difference]`,
      `missing_inputs()`, `calibrate()` and `render(results)`.

- [ ] **Step 1: Check the freeze, then capture the releases**

```bash
uv run --locked --all-packages python expirements/parser-fidelity/preregister.py verify
uv run --locked --all-packages --extra browser-capture python tests/integration/capture_browser_fixtures.py releases
ls tests/fixtures/browser/
```

Expected:

- `pre-registration verified`;
- eight lines `wrote tests/fixtures/browser/<fixture>.capture.json (<status>)`, each
  status `completed` or `partial`;
- the listing adds the eight `<fixture>.capture.json` files to the contract release's
  two.

A capture that is neither completed nor partial stops the script with its status,
reason and detail. Stop and report it: never commit a partial set, and never retry
under another policy.

- [ ] **Step 2: Write the capture checks, and run them**

Create `tests/integration/test_browser_fixtures.py`:

```python
"""The committed release captures: usable, exact, and mapped (Stage 3 spec, plan B
exit criteria 4 and 5).

Each Stage 1 release has a capture made by the pinned browser under ``isolated/1``
(tests/integration/capture_browser_fixtures.py). These tests read the captures
offline. The last, opt-in with ``-m browser``, recaptures each release and checks
that the pinned environment still renders the same text and layout.
"""

from pathlib import Path

import pytest
from earnings_core import ElementType, sha256_hex, validate_elements
from earnings_ingestion.browser import ISOLATED_1, CaptureStatus
from earnings_ingestion.browser.install import installed
from earnings_ingestion.browser.serialize import from_capture_json, to_capture_json
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.layout import LayoutExtractor

ROOT = Path(__file__).resolve().parents[2]
RELEASES = ROOT / "tests" / "fixtures" / "releases"
CAPTURES = ROOT / "tests" / "fixtures" / "browser"
FIXTURES = sorted(path.parent.name for path in RELEASES.glob("*/source.html"))


def source(fixture: str) -> bytes:
    return (RELEASES / fixture / "source.html").read_bytes()


def capture_text(fixture: str) -> str:
    return (CAPTURES / f"{fixture}.capture.json").read_text(encoding="utf-8")


@pytest.mark.parametrize("fixture", FIXTURES)
def test_each_release_has_a_usable_capture_of_its_own_bytes(fixture: str) -> None:
    capture = from_capture_json(capture_text(fixture))
    assert capture.raw_sha256 == sha256_hex(source(fixture))
    assert capture.source_document_id == fixture
    assert capture.status in (CaptureStatus.COMPLETED, CaptureStatus.PARTIAL)
    assert (capture.capture_policy, capture.capture_policy_version) == ("isolated", "1")
    assert capture.screenshots == ()


@pytest.mark.parametrize("fixture", FIXTURES)
def test_each_capture_round_trips_byte_for_byte(fixture: str) -> None:
    text = capture_text(fixture)
    assert to_capture_json(from_capture_json(text)) == text


def test_every_capture_shares_one_pinned_environment() -> None:
    captures = [from_capture_json(capture_text(fixture)) for fixture in FIXTURES]
    environments = {
        (
            capture.browser_version,
            capture.driver_version,
            capture.selenium_version,
            capture.os_name,
            capture.os_version,
            capture.architecture,
            capture.metadata_version,
        )
        for capture in captures
    }
    assert len(environments) == 1


@pytest.mark.parametrize("fixture", FIXTURES)
def test_every_layout1_unit_is_an_exact_span_or_an_alignment_failure(
    fixture: str,
) -> None:
    result = canonicalize(
        source(fixture), source_document_id=fixture, media_type="text/html"
    )
    assert isinstance(result, Canonicalized)
    extraction = LayoutExtractor().map_onto(
        from_capture_json(capture_text(fixture)), result.document
    )
    assert extraction.doc_id == result.document.doc_id
    assert validate_elements(result.document, extraction.elements) == ()
    placed = [
        element
        for element in extraction.elements
        if element.type is not ElementType.TABLE
        and element.source_type != "layout:uncovered"
    ]
    assert len(placed) + len(extraction.failures) == extraction.units


@pytest.mark.browser
@pytest.mark.parametrize("fixture", FIXTURES)
def test_the_pinned_browser_still_renders_each_committed_capture(fixture: str) -> None:
    selenium_capture = pytest.importorskip(
        "earnings_ingestion.browser.selenium_capture",
        reason="needs the browser-capture extra",
    )
    binaries = installed()
    if binaries is None:
        pytest.skip("the pinned Chrome for Testing is not installed")
    committed = from_capture_json(capture_text(fixture))
    fresh = selenium_capture.SeleniumRenderer(binaries).capture(
        source(fixture), ISOLATED_1, source_document_id=fixture
    )
    assert (fresh.rendered_text_sha256, fresh.layout_sha256) == (
        committed.rendered_text_sha256,
        committed.layout_sha256,
    )
```

```bash
uv run --locked --all-packages pytest tests/integration/test_browser_fixtures.py -q
uv run --locked --all-packages --extra browser-capture pytest tests/integration/test_browser_fixtures.py -m browser -q -rs
```

Expected: `25 passed, 8 deselected`, then `8 passed, 25 deselected`.

- A failure in `test_every_layout1_unit_is_an_exact_span_or_an_alignment_failure` is
  PB-13's `invalid-elements` case: follow "If a release breaks frozen code" above.
- A recapture whose hashes differ means the environment is not the pinned one. Stop
  and report.

- [ ] **Step 3: Write calibration's failing tests**

Create `expirements/parser-fidelity/test_calibrate.py`:

```python
"""The calibration's eight kinds, on synthetic pairs: no capture or copy needed."""

import pytest
from calibrate import CALIBRATED, KINDS, differences, source_facts

SOURCE = (
    '<p>Visible text.</p><img src="logo.png" alt="Company Logo">'
    '<div style="display: none">Secret note</div>'
    '<p hidden>Old draft</p><span style="Visibility : Hidden">Tucked away</span>'
)
FACTS = source_facts(SOURCE)
BULLET = chr(0x2022)


def kinds(captured: str, copied: str) -> list[str]:
    return [difference.kind for difference in differences(captured, copied, FACTS)]


def test_the_source_facts_come_from_html_parser() -> None:
    assert FACTS.alternatives == {"Company Logo"}
    assert FACTS.hidden == "Secret note Old draft Tucked away"


def test_identical_texts_have_no_differences() -> None:
    assert kinds("Net sales\t$9.8\nTotal", "Net sales\t$9.8\nTotal") == []


@pytest.mark.parametrize(
    ("captured", "copied", "kind"),
    [
        ("Net sales rose", "Net sales fell", "visible characters"),
        ("One.\n\nTwo.", "One.\nTwo.", "whitespace"),
        ("One.", "One.\n", "whitespace"),
        (f"Items {BULLET} Margins", "Items Margins", "bullets"),
        ("FIRST QUARTER results", "First Quarter results", "CSS text transformation"),
        ("Hidden? Secret note here", "Hidden? here", "hidden content"),
        ("Logo: Company Logo here", "Logo: here", "image alternative text"),
        ("Net sales\t$9.8", "Net sales $9.8", "table-cell separation"),
    ],
)
def test_each_kind_is_recognized(captured: str, copied: str, kind: str) -> None:
    assert kinds(captured, copied) == [kind]


def test_a_moved_block_is_reading_order_on_both_sides() -> None:
    captured = "Alpha beta gamma. Delta epsilon zeta. Eta theta iota."
    copied = "Alpha beta gamma. Eta theta iota. Delta epsilon zeta."
    assert set(kinds(captured, copied)) == {"reading order"}
    assert len(kinds(captured, copied)) == 2


def test_hidden_text_counts_only_at_token_boundaries() -> None:
    assert kinds("Secret notes here", "here") == ["visible characters"]


def test_the_three_named_categories_are_calibrated() -> None:
    assert [category for category, _ in CALIBRATED] == [
        "narrative-only",
        "table-bearing",
        "malformed layout",
    ]
    assert len(KINDS) == 8
```

Create `expirements/parser-fidelity/test_calibrate_current.py`:

```python
"""The committed calibration report is what calibrate.py writes today.

It needs the user's local rendered copies, which are never committed, so it skips
visibly without them.
"""

import pytest
from calibrate import REPORT, calibrate, missing_inputs, render


def test_the_committed_calibration_report_is_current() -> None:
    missing = missing_inputs()
    if missing:
        pytest.skip(f"calibration inputs absent: {', '.join(missing)}")
    assert REPORT.read_text(encoding="utf-8") == render(calibrate()), (
        "regenerate: uv run --locked --all-packages python"
        " expirements/parser-fidelity/calibrate.py"
    )
```

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_calibrate.py expirements/parser-fidelity/test_calibrate_current.py --import-mode=prepend -q`

Expected: `2 errors during collection`: `ModuleNotFoundError: No module named 'calibrate'`.

- [ ] **Step 4: Write calibration, and publish its report**

Create `expirements/parser-fidelity/calibrate.py`:

```python
"""Rendered-text calibration: the capture's innerText against the user's copies.

    uv run --locked --all-packages python expirements/parser-fidelity/calibrate.py

(Stage 3 spec, Checks; the browser spec, Rendered-text calibration.) For one release
of each named category, compares the committed capture's text
(``document.body.innerText``) with the user's copy, made in Chrome by Select All and
Copy (data/runs/parser-fidelity/gold-drafts/<fixture>.rendered.txt, local and never
committed), and writes docs/verification/browser-calibration.md. The copies are
calibration observations, not gold, and no gold changes.

Both texts are split into tokens, the maximal runs of non-whitespace, and aligned by
difflib with its junk heuristic off. Each difference is classed into one of the
browser spec's eight kinds by the first rule that fits (plan 5, PB-15):

- a separator between two aligned tokens that differs, or differing leading or
  trailing whitespace, is ``table-cell separation`` when either side holds a tab, and
  ``whitespace`` otherwise;
- a hunk present on one side only whose tokens appear, in order, as a one-sided hunk
  on the other side is ``reading order``, and so is its partner;
- a hunk of bullet glyphs only is ``bullets``;
- a hunk whose tokens differ only in case is ``CSS text transformation``;
- a one-sided hunk that is one of the source's image alternative texts is ``image
  alternative text``;
- a one-sided hunk inside the source's hidden text is ``hidden content``: text under
  ``display: none``, ``visibility: hidden``, or the ``hidden`` attribute, read by
  ``html.parser``;
- anything else is ``visible characters``.
"""

from __future__ import annotations

import difflib
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from html.parser import HTMLParser

from earnings_ingestion.browser.serialize import from_capture_json
from earnings_ingestion.canonical.walker import BULLETS
from pf_decode import decode_html_bytes
from pf_paths import FIXTURES, REPO_ROOT, RUNS

REPORT = REPO_ROOT / "docs" / "verification" / "browser-calibration.md"
CAPTURES = REPO_ROOT / "tests" / "fixtures" / "browser"
COPIES = RUNS / "gold-drafts"
CALIBRATED = (
    ("narrative-only", "0000706863-16-000110_ex-99-1"),
    ("table-bearing", "0000877860-13-000100_ex-99-1"),
    ("malformed layout", "0000009389-10-000004_ex-99-1"),
)
"""The browser spec's three categories: Union Bankshares, National Health Investors,
and Ball."""
KINDS = (
    "visible characters",
    "whitespace",
    "bullets",
    "CSS text transformation",
    "hidden content",
    "image alternative text",
    "table-cell separation",
    "reading order",
)
EXAMPLES = 5
"""Hunks shown per kind and fixture; every hunk is counted."""
_TOKEN = re.compile(r"\S+")
_HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden")
_VOID = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
     "param", "source", "track", "wbr"}
)  # fmt: skip


@dataclass(frozen=True)
class Difference:
    kind: str
    captured: str
    copied: str


class _Source(HTMLParser):
    """Alternative texts and hidden text, from ``html.parser`` alone."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.alternatives: list[str] = []
        self.hidden: list[str] = []
        self._stack: list[bool] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        values = {name: value or "" for name, value in attrs}
        if tag == "img" and values.get("alt", "").strip():
            self.alternatives.append(" ".join(values["alt"].split()))
        if tag in _VOID:
            return
        hidden = "hidden" in values or bool(
            _HIDDEN_STYLE.search(values.get("style", "").lower())
        )
        self._stack.append(hidden or (bool(self._stack) and self._stack[-1]))

    def handle_endtag(self, tag: str) -> None:
        if tag not in _VOID and self._stack:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if self._stack and self._stack[-1]:
            self.hidden.append(data)


@dataclass(frozen=True)
class SourceFacts:
    alternatives: frozenset[str]
    hidden: str
    """The hidden text, whitespace runs collapsed."""


def source_facts(html: str) -> SourceFacts:
    reader = _Source()
    reader.feed(html)
    reader.close()
    return SourceFacts(
        frozenset(reader.alternatives), " ".join(" ".join(reader.hidden).split())
    )


@dataclass
class _Side:
    tokens: list[str]
    separators: list[str]
    """Whitespace before each token, then after the last: one more than tokens."""


def _split(text: str) -> _Side:
    tokens, separators, cursor = [], [], 0
    for match in _TOKEN.finditer(text):
        separators.append(text[cursor : match.start()])
        tokens.append(match.group())
        cursor = match.end()
    separators.append(text[cursor:])
    return _Side(tokens, separators)


def differences(captured: str, copied: str, facts: SourceFacts) -> list[Difference]:
    """Every difference between the two texts, classed into the eight kinds."""
    left, right = _split(captured), _split(copied)
    matcher = difflib.SequenceMatcher(None, left.tokens, right.tokens, autojunk=False)
    found: list[Difference] = []
    hunks: list[tuple[list[str], list[str]]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            hunks.append((left.tokens[i1:i2], right.tokens[j1:j2]))
            continue
        for offset in range(i2 - i1 + 1):
            a, b = left.separators[i1 + offset], right.separators[j1 + offset]
            inner = 0 < offset < i2 - i1
            edge = (i1 + offset in (0, len(left.tokens))) and (
                j1 + offset in (0, len(right.tokens))
            )
            if (inner or edge) and a != b:
                kind = "table-cell separation" if "\t" in a + b else "whitespace"
                found.append(Difference(kind, repr(a), repr(b)))
    moved = _moved(hunks)
    for index, (a, b) in enumerate(hunks):
        found.append(
            Difference(
                "reading order" if index in moved else _kind(a, b, facts),
                " ".join(a),
                " ".join(b),
            )
        )
    return found


def _moved(hunks: Sequence[tuple[list[str], list[str]]]) -> set[int]:
    """One-sided hunks whose tokens appear as a one-sided hunk on the other side."""
    only_left = {i: tuple(a) for i, (a, b) in enumerate(hunks) if a and not b}
    only_right = {i: tuple(b) for i, (a, b) in enumerate(hunks) if b and not a}
    moved: set[int] = set()
    for i, tokens in only_left.items():
        partner = next(
            (
                j
                for j, other in only_right.items()
                if other == tokens and j not in moved
            ),
            None,
        )
        if partner is not None:
            moved.update((i, partner))
    return moved


def _kind(left: list[str], right: list[str], facts: SourceFacts) -> str:
    if all(set(token) <= set(BULLETS) for token in left + right):
        return "bullets"
    if (
        len(left) == len(right)
        and left != right
        and all(a.casefold() == b.casefold() for a, b in zip(left, right, strict=True))
    ):
        return "CSS text transformation"
    extra = " ".join(left or right)
    if not (left and right):
        if extra in facts.alternatives:
            return "image alternative text"
        if f" {extra} " in f" {facts.hidden} ":
            return "hidden content"
    return "visible characters"


@dataclass
class Calibrated:
    category: str
    fixture: str
    differences: list[Difference] = field(default_factory=list)


def missing_inputs() -> list[str]:
    """The captures and local copies the report needs that are not present."""
    wanted = [CAPTURES / f"{fixture}.capture.json" for _, fixture in CALIBRATED]
    wanted += [COPIES / f"{fixture}.rendered.txt" for _, fixture in CALIBRATED]
    return [str(path.relative_to(REPO_ROOT)) for path in wanted if not path.is_file()]


def calibrate() -> list[Calibrated]:
    out = []
    for category, fixture in CALIBRATED:
        capture = from_capture_json(
            (CAPTURES / f"{fixture}.capture.json").read_text(encoding="utf-8")
        )
        copied = (COPIES / f"{fixture}.rendered.txt").read_text(encoding="utf-8")
        raw = (FIXTURES / fixture / "source.html").read_bytes()
        facts = source_facts(decode_html_bytes(raw).text)
        out.append(
            Calibrated(
                category, fixture, differences(capture.rendered_text, copied, facts)
            )
        )
    return out


def render(results: Sequence[Calibrated]) -> str:
    lines = [
        "# Rendered-text calibration: innerText against the user's copies",
        "",
        "Generated by `expirements/parser-fidelity/calibrate.py`; do not edit. It needs",
        "the user's local copies in `data/runs/parser-fidelity/gold-drafts/`, which are",
        "never committed. The copies are calibration observations, not gold, and no",
        "gold changed (Stage 3 spec, Checks).",
        "",
        "Each capture's `document.body.innerText`, under capture policy `isolated/1`,",
        "is compared with the user's copy of the same release, made in Chrome by",
        "Select All and Copy. Tokens are aligned by difflib; every difference is",
        "counted in one of the browser spec's eight kinds, by the rules in",
        "`calibrate.py`'s docstring.",
        "",
        "| Kind | " + " | ".join(r.fixture for r in results) + " |",
        "| --- |" + " --- |" * len(results),
    ]
    counts = [Counter(d.kind for d in r.differences) for r in results]
    for kind in KINDS:
        lines.append(f"| {kind} | " + " | ".join(str(c[kind]) for c in counts) + " |")
    for result, count in zip(results, counts, strict=True):
        lines += [
            "",
            f"## `{result.fixture}` ({result.category})",
            "",
            f"Differences: {sum(count.values())}.",
        ]
        for kind in KINDS:
            shown = [d for d in result.differences if d.kind == kind][:EXAMPLES]
            if not shown:
                continue
            lines += [
                "",
                f"### {kind}: {count[kind]}",
                "",
                "| innerText | Copy |",
                "| --- | --- |",
            ]
            lines += [f"| {_cell(d.captured)} | {_cell(d.copied)} |" for d in shown]
    return "\n".join(lines) + "\n"


def _cell(text: str) -> str:
    text = text.replace("|", "\\|")
    return (text[:77] + "...") if len(text) > 80 else (text or "(nothing)")


def main() -> int:
    missing = missing_inputs()
    if missing:
        print("missing: " + ", ".join(missing))
        return 1
    REPORT.write_text(render(calibrate()), encoding="utf-8", newline="\n")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```bash
uv run --locked --all-packages python expirements/parser-fidelity/calibrate.py
uv run --locked --all-packages pytest expirements/parser-fidelity/test_calibrate.py expirements/parser-fidelity/test_calibrate_current.py --import-mode=prepend -q
```

Expected: `wrote docs/verification/browser-calibration.md`, then `14 passed`.

Read `docs/verification/browser-calibration.md`. Task 15's record summarizes its
counts per kind.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan5-escapes.py tests/integration/test_browser_fixtures.py expirements/parser-fidelity/calibrate.py expirements/parser-fidelity/test_calibrate.py expirements/parser-fidelity/test_calibrate_current.py
uv run --locked --all-packages python expirements/parser-fidelity/preregister.py verify
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
git status --short
```

Expected: 

- `escapes intact`;
- `pre-registration verified`;
- `630 passed, 22 deselected`;
- `277 passed`;
- `All checks passed!` and `156 files already formatted`;
- `freeze verified`;
- a status listing only this task's files: the eight new captures, the four new
  Python files, and the calibration report.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add tests/fixtures/browser tests/integration/test_browser_fixtures.py expirements/parser-fidelity/calibrate.py expirements/parser-fidelity/test_calibrate.py expirements/parser-fidelity/test_calibrate_current.py docs/verification/browser-calibration.md
git commit -m "test(fixtures): capture the eight releases and calibrate innerText against the copies"
```

---
### Task 12: R3.5's second leg, and the final report

Plan A's leg compared the canonical text with the gold and `html.parser`. The second
leg compares it with each committed capture's `innerText` and with each of the user's
copies (PB-16). It uses a whitespace-insensitive token diff in the same comparison
space, and classes every differing hunk into R3.5's six categories or `other`. With
both legs the report is final (exit criterion 8).

**Files:**

- Modify: `packages/earnings-ingestion/src/earnings_ingestion/canonical/fidelity.py`
  (replaced whole: `token_hunks`, `hunk_category`, `HUNK_CATEGORIES`).
- Test (modify): `packages/earnings-ingestion/tests/test_fidelity.py` (replaced whole:
  two tests added).
- Modify: `expirements/parser-fidelity/r35_report.py` (replaced whole: leg 2).
- Test (modify): `expirements/parser-fidelity/test_r35_report.py`,
  `test_r35_report_current.py`, and `tests/integration/test_r35_report.py` (each
  replaced whole).
- Regenerate: `docs/verification/R3.5-text-fidelity.md`.

**Interfaces:**

- Consumes:
  - plan 4's `comparison_space`, `non_ascii`, `scale_counts`, `signed_figures` and
    `read_source`;
  - Task 11's committed captures;
  - the user's local copies.
- Produces:
  - **In `earnings_ingestion.canonical.fidelity`.**
    - `HUNK_CATEGORIES`: `unicode`, `numeric_signs`, `scale`, `superscripts`,
      `footnotes`, `table_headings`, `other`.
    - `token_hunks(canonical, rendered) -> list[tuple[str, str]]`.
    - `hunk_category(canonical, rendered, sup_runs, headers) -> str`.
  - **In `r35_report.py`.**
    - Constants: `CAPTURES`, `COPIES`, `LEG2`, `CAPTURED`, `COPIED` and
      `HUNK_NAMES`.
    - `Leg2(fixture, captured, copied)`.
    - `leg2(fixture) -> Leg2`.
    - `render(counts, legs) -> str` and `render_leg2(legs)`.

- [ ] **Step 1: Write the comparators' failing tests**

Replace `packages/earnings-ingestion/tests/test_fidelity.py` with:

```python
"""R3.5's comparators, with the synthetic cases the fixtures cannot supply.

Non-ASCII inputs are built from code points, so no tool can normalize them.
"""

import pytest
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.canonical.fidelity import (
    HUNK_CATEGORIES,
    SCALE_PHRASES,
    classify_run,
    comparison_space,
    hunk_category,
    joined_to_text,
    locate_run,
    non_ascii,
    read_source,
    scale_counts,
    signed_figures,
    token_hunks,
)

EN_DASH, MINUS, NBSP = chr(0x2013), chr(0x2212), chr(0x00A0)
REGISTERED, E_ACUTE = chr(0x00AE), chr(0x00E9)


def test_the_comparison_space_is_nfc_with_collapsed_whitespace() -> None:
    assert comparison_space(f" caf{'e' + chr(0x0301)}\n\t{NBSP}bar ") == (
        f"caf{E_ACUTE} bar"
    )


def test_the_comparison_space_keeps_compatibility_forms() -> None:
    superscript_one, one_half = chr(0x00B9), chr(0x00BD)
    assert comparison_space(f"x{superscript_one} {one_half}") == (
        f"x{superscript_one} {one_half}"
    )


def test_non_ascii_lists_every_non_ascii_character() -> None:
    assert non_ascii(f"Acme{REGISTERED} {EN_DASH} caf{E_ACUTE}{REGISTERED}") == [
        REGISTERED,
        EN_DASH,
        E_ACUTE,
        REGISTERED,
    ]


def test_signed_figures_cover_parentheses_and_leading_signs() -> None:
    text = (
        f"Loss of (1,234) and ($5.2) and (3.1%); -4% and {EN_DASH}7 and {MINUS}0.5"
        " and +12%"
    )
    assert signed_figures(text) == [
        "(1,234)",
        "($5.2)",
        "(3.1%)",
        "-4%",
        f"{EN_DASH}7",
        f"{MINUS}0.5",
        "+12%",
    ]


def test_footnote_markers_and_ranges_are_not_signed_figures() -> None:
    assert signed_figures("See note (1) for 2020-2021 and pages 3-4.") == []


def test_scale_phrases_are_counted_case_insensitively() -> None:
    counts = scale_counts("(In millions, except per share data) in MILLIONS")
    assert counts == {
        "in millions": 2,
        "in thousands": 0,
        "in billions": 0,
        "except per share": 1,
    }
    assert tuple(counts) == SCALE_PHRASES


def test_read_source_skips_hidden_tags_and_spaces_block_boundaries() -> None:
    source = read_source(
        "<html><head><title>T</title><style>p {}</style></head><body>"
        "<p>Revenue</p><p>rose<br>sharply</p><script>x()</script></body></html>"
    )
    assert source.text == "Revenue rose sharply"


def test_read_source_marks_outermost_sup_runs() -> None:
    source = read_source(
        "<p>1<sup>st</sup> quarter, net income<sup> (a)</sup>"
        f" and Acme<sup><sup>{REGISTERED}</sup></sup></p>"
    )
    assert [source.text[start:end] for start, end in source.sup_runs] == [
        "st",
        "(a)",
        REGISTERED,
    ]


@pytest.mark.parametrize(
    ("run", "expected"),
    [
        ("st", "ordinal_suffix"),
        ("TH", "ordinal_suffix"),
        ("(1)", "parenthesized_marker"),
        ("( a )", "parenthesized_marker"),
        ("(1)(2)", "parenthesized_marker"),
        (REGISTERED, "symbol"),
        ("*", "symbol"),
        ("  ", "empty"),
        ("12", "bare_digits"),
        ("TM", "other"),
        (chr(0x00B2), "other"),
    ],
)
def test_runs_are_classed(run: str, expected: str) -> None:
    assert classify_run(run) == expected


def canonical_text(html: str) -> str:
    result = canonicalize(
        html.encode(), source_document_id="sup", media_type="text/html"
    )
    assert isinstance(result, Canonicalized)
    return comparison_space(result.document.canonical_text)


def test_a_run_is_located_by_the_fewest_words_that_make_it_unique() -> None:
    html = "<p>Revenue rose in the first half and the 1<sup>st</sup> quarter.</p>"
    source = read_source(html)
    canonical = canonical_text(html)
    [(start, end)] = source.sup_runs
    position = locate_run(canonical, source, start, end)
    assert position == canonical.index("1st") + 1


def test_a_run_no_context_singles_out_is_unlocatable() -> None:
    source = read_source("<p>A 1<sup>st</sup> B</p>")
    [(start, end)] = source.sup_runs
    assert source.text == "A 1st B"
    assert locate_run("A 1st B A 1st B", source, start, end) is None


def test_a_run_whose_context_does_not_match_is_unlocatable() -> None:
    source = read_source("<p>Net income<sup>(1)</sup> rose.</p>")
    [(start, end)] = source.sup_runs
    canonical = "Net earnings (1) and costs (1) rose."
    assert locate_run(canonical, source, start, end) is None


def test_a_run_missing_from_the_canonical_text_is_unlocatable() -> None:
    source = read_source("<p>Net income<sup>(1)</sup> rose.</p>")
    [(start, end)] = source.sup_runs
    assert locate_run("Net income rose.", source, start, end) is None


def test_an_empty_run_has_nothing_to_locate() -> None:
    source = read_source("<p>Net income<sup> </sup> rose.</p>")
    [(start, end)] = source.sup_runs
    assert start == end
    assert locate_run("Net income rose.", source, start, end) is None


def test_a_bare_digit_run_joined_to_a_number_is_a_hazard() -> None:
    html = "<p>Revenue was $4.5 million<sup>1</sup> in 2024.</p>"
    source = read_source(html)
    canonical = canonical_text(html)
    [(start, end)] = source.sup_runs
    run = source.text[start:end]
    position = locate_run(canonical, source, start, end)
    assert (classify_run(run), canonical) == (
        "bare_digits",
        "Revenue was $4.5 million1 in 2024.",
    )
    assert position is not None and joined_to_text(canonical, position)


def test_a_marker_after_a_space_is_not_joined() -> None:
    canonical = "Net income (1) rose."
    assert not joined_to_text(canonical, canonical.index("(1)"))


def test_token_hunks_ignore_whitespace_and_pair_the_sides() -> None:
    assert token_hunks("Same\ttext.", f"Same{NBSP}text.\n") == []
    assert token_hunks("Net  sales rose 5%", "Net sales rose 5 %") == [("5%", "5 %")]
    assert token_hunks("A B C", "A C") == [("B", "")]
    assert token_hunks("A C", "A B C") == [("", "B")]


@pytest.mark.parametrize(
    ("canonical", "rendered", "category"),
    [
        (f"caf{E_ACUTE}", "cafe", "unicode"),
        ("(in millions)", "", "scale"),
        ("1Represents", "1 Represents", "superscripts"),
        ("(a)", "", "superscripts"),
        ("(2) Excludes", "", "footnotes"),
        ("(1.2)", "1.2", "numeric_signs"),
        (f"{MINUS}4", "-4", "unicode"),
        ("-", "", "numeric_signs"),
        ("Three Months", "", "table_headings"),
        ("Net", "Gross", "other"),
    ],
)
def test_a_hunk_takes_the_first_category_it_passes(
    canonical: str, rendered: str, category: str
) -> None:
    runs, headers = {"(a)", "1"}, ["Three Months Ended"]
    assert hunk_category(canonical, rendered, runs, headers) == category
    assert category in HUNK_CATEGORIES
```

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fidelity.py -q`

Expected: `1 error during collection`: `ImportError: cannot import name 'HUNK_CATEGORIES' from 'earnings_ingestion.canonical.fidelity'`.

- [ ] **Step 2: Write the comparators**

Replace `packages/earnings-ingestion/src/earnings_ingestion/canonical/fidelity.py` with:

```python
"""R3.5's comparators: canonical text checked against independent references.

The references come from the rendered source and from the standard library's
``html.parser``, never from lxml or the walker. Every comparison runs in NFC with
whitespace runs collapsed, never in NFKC, which would hide the Unicode and superscript
differences the check exists to find. The comparators count and list; they set no
threshold (R13.1). Stage 5 reruns them on its pilot releases.
"""

import difflib
import re
import unicodedata
from collections.abc import Collection
from dataclasses import dataclass
from html.parser import HTMLParser

from earnings_core import SpanLocator, occurrences

SCALE_PHRASES = ("in millions", "in thousands", "in billions", "except per share")
SUP_CLASSES = (
    "ordinal_suffix",
    "parenthesized_marker",
    "symbol",
    "empty",
    "bare_digits",
    "other",
)
"""R3.5's five classes, and ``other`` for a run that fits none of them."""

_PARENTHESIZED = re.compile(r"\(\$?\d[\d,]*(?:\.\d+)?%?\)")
_W10_MARKER = re.compile(r"\(\d{1,2}\)")
_LEADING_SIGN = re.compile(
    r"(?<![\w.,)])[-+\N{EN DASH}\N{MINUS SIGN}]\$?\d[\d,]*(?:\.\d+)?%?"
)
_ORDINAL = re.compile(r"st|nd|rd|th", re.IGNORECASE)
_MARKER = re.compile(r"(?:\(\s*[0-9A-Za-z]{1,3}\s*\))+")
_ASCII_DIGITS = re.compile(r"[0-9]+")
_WORD = re.compile(r"\S+")


def comparison_space(text: str) -> str:
    """NFC, with every whitespace run collapsed to one space and the ends stripped."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def non_ascii(text: str) -> list[str]:
    """``text``'s non-ASCII characters, in order, repeats included."""
    return [char for char in text if not char.isascii()]


def signed_figures(text: str) -> list[str]:
    """Figures written with a sign: parentheses, or a leading hyphen, en dash, minus
    sign, or plus.

    ``(1)`` to ``(99)`` are W10's footnote markers, so they are not figures. A hyphen
    after a letter, digit, or closing parenthesis joins a range, not a sign.
    """
    parenthesized = [
        figure
        for figure in _PARENTHESIZED.findall(text)
        if not _W10_MARKER.fullmatch(figure)
    ]
    return parenthesized + _LEADING_SIGN.findall(text)


def scale_counts(text: str) -> dict[str, int]:
    """How often each scale phrase occurs in ``text``, case-insensitively."""
    folded = text.casefold()
    return {phrase: folded.count(phrase) for phrase in SCALE_PHRASES}


@dataclass(frozen=True)
class SourceText:
    """A source's visible text as ``html.parser`` reads it, in comparison space, with
    the ``[start, end)`` extent of every outermost ``<sup>`` run."""

    text: str
    sup_runs: tuple[tuple[int, int], ...]


class _Reader(HTMLParser):
    _SKIPPED = frozenset({"script", "style", "title"})
    _BREAKS = frozenset(
        {
            "address", "article", "blockquote", "br", "caption", "center", "dd",
            "div", "dl", "dt", "footer", "h1", "h2", "h3", "h4", "h5", "h6",
            "header", "hr", "li", "ol", "p", "pre", "section", "table", "td", "th",
            "tr", "ul",
        }
    )  # fmt: skip

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chars: list[str] = []
        self.runs: list[tuple[int, int]] = []
        self._space = False
        self._skip = 0
        self._sup = 0
        self._sup_start = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._SKIPPED:
            self._skip += 1
        elif tag in self._BREAKS:
            self._space = True
        elif tag == "sup" and not self._skip:
            if not self._sup:
                self._sup_start = len(self.chars)
            self._sup += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIPPED:
            self._skip = max(0, self._skip - 1)
        elif tag in self._BREAKS:
            self._space = True
        elif tag == "sup" and self._sup:
            self._sup -= 1
            if not self._sup:
                self.runs.append((self._sup_start, len(self.chars)))

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        for char in unicodedata.normalize("NFC", data):
            if char.isspace():
                self._space = True
                continue
            if self._space and self.chars:
                self.chars.append(" ")
            self._space = False
            self.chars.append(char)


def read_source(html: str) -> SourceText:
    """The visible text of decoded HTML, outside ``<script>``, ``<style>``, and
    ``<title>``, with a space at every block boundary, as the canonical text has."""
    reader = _Reader()
    reader.feed(html)
    reader.close()
    text = "".join(reader.chars)
    runs = []
    for start, end in reader.runs:
        while start < end and text[start] == " ":
            start += 1
        runs.append((start, end))
    return SourceText(text=text, sup_runs=tuple(runs))


def classify_run(run: str) -> str:
    """A ``<sup>`` run's class: one of ``SUP_CLASSES``.

    A run of consecutive markers, such as ``(1)(2)``, is a parenthesized marker.
    """
    run = run.strip()
    if not run:
        return "empty"
    if _ORDINAL.fullmatch(run):
        return "ordinal_suffix"
    if _MARKER.fullmatch(run):
        return "parenthesized_marker"
    if _ASCII_DIGITS.fullmatch(run):
        return "bare_digits"
    if not any(char.isalnum() for char in run):
        return "symbol"
    return "other"


def locate_run(canonical: str, source: SourceText, start: int, end: int) -> int | None:
    """Where ``source.text[start:end]`` sits in ``canonical``, or None.

    Both texts are in comparison space. Context from the source grows by one
    whitespace-delimited word on each side at a time, as ``make_locator``'s does (D-4),
    until exactly one occurrence remains; a word cut by the run's edge counts as one
    word. A run that no context singles out is None, never a first match.
    """
    text = source.text
    exact = text[start:end]
    if not exact:
        return None
    word_starts = [match.start() for match in _WORD.finditer(text, 0, start)]
    word_ends = [match.end() for match in _WORD.finditer(text, end)]
    words = 0
    while True:
        prefix, suffix = _context(text, start, end, word_starts, word_ends, words)
        found = occurrences(
            canonical, SpanLocator(exact=exact, prefix=prefix, suffix=suffix)
        )
        if len(found) == 1:
            return found[0]
        if not found or (words > len(word_starts) and words > len(word_ends)):
            return None
        words += 1


def _context(
    text: str,
    start: int,
    end: int,
    word_starts: list[int],
    word_ends: list[int],
    words: int,
) -> tuple[str, str]:
    if words == 0:
        return "", ""
    prefix = (
        text[:start] if words > len(word_starts) else text[word_starts[-words] : start]
    )
    suffix = text[end:] if words > len(word_ends) else text[end : word_ends[words - 1]]
    return prefix, suffix


def joined_to_text(canonical: str, position: int) -> bool:
    """True when a run located at ``position`` directly follows a letter or digit, as
    a raised "1" after "million" does."""
    return position > 0 and canonical[position - 1].isalnum()


HUNK_CATEGORIES = (
    "unicode",
    "numeric_signs",
    "scale",
    "superscripts",
    "footnotes",
    "table_headings",
    "other",
)
"""R3.5's six categories, in the report's order, and ``other`` (plan 5's leg)."""
_SIGN_CHARACTERS = "()+-\N{EN DASH}\N{MINUS SIGN}"
_LEADING_FOOTNOTE = re.compile(
    r"(?:\(\d{1,2}\)|\([a-z]\)|\*{1,3}|[\N{DAGGER}\N{DOUBLE DAGGER}])(?:\s|$)"
)


def token_hunks(canonical: str, rendered: str) -> list[tuple[str, str]]:
    """Each differing hunk of a whitespace-insensitive token diff between the canonical
    text and a browser's text of the same source, both in comparison space, as
    ``(canonical side, rendered side)``; either side may be empty. difflib aligns the
    tokens with its junk heuristic off."""
    left = comparison_space(canonical).split()
    right = comparison_space(rendered).split()
    matcher = difflib.SequenceMatcher(None, left, right, autojunk=False)
    return [
        (" ".join(left[i1:i2]), " ".join(right[j1:j2]))
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]


def hunk_category(
    canonical: str,
    rendered: str,
    sup_runs: Collection[str],
    headers: Collection[str],
) -> str:
    """The category of a differing hunk: the first of these tests it passes.

    ``sup_runs`` are the source's non-empty ``<sup>`` run texts and ``headers`` the
    gold's table header texts, all in comparison space.

    1. unicode: a non-ASCII character on either side;
    2. scale: a scale phrase on either side;
    3. superscripts: a side that is a run, or sides equal without spaces where a side
       starts or ends with a run: a raised marker joined or split;
    4. footnotes: a side that starts with a W10 marker;
    5. numeric_signs: a signed figure on either side, or sides equal once
       parentheses, plus, hyphen, en dash, and minus sign are removed;
    6. table_headings: a side inside a header text;
    7. other.
    """
    sides = [side for side in (canonical, rendered) if side]
    if any(non_ascii(side) for side in sides):
        return "unicode"
    if any(any(scale_counts(side).values()) for side in sides):
        return "scale"
    joined = _strip(canonical, " ") == _strip(rendered, " ")
    bare = [side.replace(" ", "") for side in sides]
    if any(side in sup_runs for side in sides) or (
        joined
        and any(
            side.startswith(run) or side.endswith(run)
            for side in bare
            for run in sup_runs
        )
    ):
        return "superscripts"
    if any(_LEADING_FOOTNOTE.match(side) for side in sides):
        return "footnotes"
    if any(signed_figures(side) for side in sides) or _strip(
        canonical, _SIGN_CHARACTERS
    ) == _strip(rendered, _SIGN_CHARACTERS):
        return "numeric_signs"
    if any(side in header for side in sides for header in headers):
        return "table_headings"
    return "other"


def _strip(text: str, characters: str) -> str:
    return "".join(char for char in text if char not in characters)
```

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fidelity.py -q`

Expected: `37 passed`.

- [ ] **Step 3: Write the report's failing tests**

Replace `expirements/parser-fidelity/test_r35_report.py` with:

```python
"""The R3.5 generator's references and header placement, on synthetic input."""

from __future__ import annotations

from earnings_core import ElementType
from earnings_ingestion.canonical import Canonicalized, canonicalize
from r35_report import (
    COPIED,
    LEG2,
    NO_INSTANCES,
    Leg2,
    header_placement,
    instances,
    references,
    render_leg2,
)


def test_references_are_anchors_and_header_texts_of_anchorable_blocks() -> None:
    gold = {
        "blocks": [
            {"type": "paragraph", "start": "Revenue rose", "end": "in May."},
            {"type": "heading", "start": "Segment Results", "after": "The BD"},
            {
                "type": "table",
                "headers": ["2024", "2023"],
                "cells": [
                    {"role": "corner", "text": "1,234"},
                    {"role": "right", "text": "1,100"},
                ],
            },
            {"type": "paragraph", "start": "Hidden", "unanchorable": True},
        ]
    }
    anchors, headers = references(gold)
    assert anchors == [
        "Revenue rose",
        "in May.",
        "Segment Results",
        "The BD",
        "1,234",
        "1,100",
    ]
    assert headers == ["2024", "2023"]


def canonical(html: str) -> Canonicalized:
    result = canonicalize(html.encode(), source_document_id="t", media_type="text/html")
    assert isinstance(result, Canonicalized), result
    return result


def test_header_texts_are_placed_in_header_cells_other_cells_or_none() -> None:
    result = canonical(
        "<table><tr><th>Item</th><th>2024</th></tr>"
        "<tr><td>Net sales (in millions)</td><td>1,234</td></tr></table>"
    )
    tables = [e for e in result.elements if e.type is ElementType.TABLE]
    assert header_placement("2024", tables, result) == "header cell"
    assert header_placement("in millions", tables, result) == "other cell"
    assert header_placement("Three Months Ended", tables, result) == "no cell"


def test_a_c1_table_has_no_cells_to_place_headers_in() -> None:
    result = canonical(
        "<pre>Item          2024\n----------------\nSales    1,234</pre>"
    )
    tables = [e for e in result.elements if e.type is ElementType.TABLE]
    assert len(tables) == 1
    assert header_placement("2024", tables, result) == "no cell"


def test_zero_instances_reads_as_no_instances_in_sample() -> None:
    assert instances(0) == f"**Instances:** {NO_INSTANCES}"
    assert instances(3) == "**Instances:** 3"


def test_leg2_counts_and_lists_every_hunk_and_marks_missing_copies() -> None:
    legs = [
        Leg2("f1", [("other", "Net", "Gross"), ("scale", "(in millions)", "")], None),
        Leg2("f2", [], [("footnotes", "(1) Excludes", "")]),
    ]
    lines = render_leg2(legs)
    assert lines.index(LEG2) < lines.index(COPIED)
    captured = lines[: lines.index(COPIED)]
    copied = lines[lines.index(COPIED) :]
    assert "| `f1` | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 1 |" in captured
    assert "| `f1` | other | Net | Gross |" in captured
    assert "| `f1` | Scale | (in millions) | (nothing) |" in captured
    assert "| `f1` | no local copy |" + " |" * 7 in copied
    assert "| `f2` | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |" in copied
    assert "| `f2` | Footnotes | (1) Excludes | (nothing) |" in copied
```

Replace `expirements/parser-fidelity/test_r35_report_current.py` with:

```python
"""The committed R3.5 report is what r35_report.py writes today.

The last section needs the user's local rendered copies, which are never committed:
the first test checks everything before it, and the second, which skips visibly
without the copies, checks the whole report.
"""

import pytest
from r35_report import COPIED, COPIES, REPORT, count, leg2, render
from walker1_report import load_fixtures

REGENERATE = (
    "regenerate: uv run --locked --all-packages python"
    " expirements/parser-fidelity/r35_report.py"
)


def fresh() -> str:
    fixtures = load_fixtures()
    return render([count(f) for f in fixtures], [leg2(f) for f in fixtures])


def test_the_committed_report_is_current_up_to_the_rendered_copies() -> None:
    committed = REPORT.read_text(encoding="utf-8")
    assert committed.split(COPIED)[0] == fresh().split(COPIED)[0], REGENERATE


def test_the_whole_committed_report_is_current_with_the_local_copies() -> None:
    missing = [
        fixture.fixture
        for fixture in load_fixtures()
        if not (COPIES / f"{fixture.fixture}.rendered.txt").is_file()
    ]
    if missing:
        pytest.skip(f"{len(missing)} of the user's local rendered copies are absent")
    assert REPORT.read_text(encoding="utf-8") == fresh(), REGENERATE
```

Replace `tests/integration/test_r35_report.py` with:

```python
"""R3.5's committed report covers all six categories (Stage 3 spec: Verification
(plan A), item 10), and both legs, which makes it final (plan B)."""

import re
from pathlib import Path

import pytest

REPORT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "verification"
    / "R3.5-text-fidelity.md"
)
CATEGORIES = (
    "Unicode",
    "Numeric signs",
    "Scale",
    "Superscripts",
    "Footnotes",
    "Table headings",
)
INSTANCES = re.compile(
    r"^\*\*Instances:\*\* (?:[1-9][0-9]*|no instances in sample)$", re.MULTILINE
)


def sections() -> dict[str, str]:
    parts = re.split(r"^## ", REPORT.read_text(encoding="utf-8"), flags=re.MULTILINE)
    return {part.split("\n", 1)[0]: part for part in parts[1:]}


@pytest.mark.parametrize("category", CATEGORIES)
def test_every_category_reports_its_instances(category: str) -> None:
    section = sections().get(category)
    assert section is not None, f"the R3.5 report has no {category} section"
    assert INSTANCES.search(section), f"{category} reports no instance count"


def test_the_report_is_final_with_both_legs() -> None:
    leg2 = sections().get("Leg 2: canonical text against the browser's text")
    assert leg2 is not None, "the R3.5 report has no second leg"
    assert "### Against innerText" in leg2
    assert "### Against the user's rendered copies" in leg2
```

```bash
uv run --locked --all-packages pytest expirements/parser-fidelity/test_r35_report.py expirements/parser-fidelity/test_r35_report_current.py --import-mode=prepend -q
uv run --locked --all-packages pytest tests/integration/test_r35_report.py -q
```

Expected: `2 errors during collection`: `ImportError: cannot import name 'COPIED' from 'r35_report'`. Then `1 failed, 6 passed`: `test_the_report_is_final_with_both_legs` fails, because the committed report has no second leg yet.

- [ ] **Step 4: Write leg 2, and regenerate the report**

Replace `expirements/parser-fidelity/r35_report.py` with:

```python
"""R3.5's text-fidelity report, both legs (Stage 3 spec: R3.5 fidelity check).

    uv run --locked --all-packages python expirements/parser-fidelity/r35_report.py

Writes docs/verification/R3.5-text-fidelity.md. Leg 1's references are the committed
gold, marked from the browser rendering (anchors and table header texts), and the
<sup> runs html.parser reads from each source.html; never lxml or the walker. Leg 2
compares the canonical text with the committed captures' innerText and with the
user's rendered copies, which are local and never committed, through a
whitespace-insensitive token diff, and classes every differing hunk. Comparisons run
in NFC with whitespace runs collapsed (earnings_ingestion.canonical.fidelity). The
report counts and lists, and sets no threshold (R13.1).
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from earnings_core import DocumentElement, ElementType
from earnings_ingestion.browser.serialize import from_capture_json
from earnings_ingestion.canonical import Canonicalized
from earnings_ingestion.canonical.fidelity import (
    HUNK_CATEGORIES,
    SCALE_PHRASES,
    SUP_CLASSES,
    classify_run,
    comparison_space,
    hunk_category,
    joined_to_text,
    locate_run,
    non_ascii,
    read_source,
    scale_counts,
    signed_figures,
    token_hunks,
)
from pf_decode import decode_html_bytes
from pf_paths import FIXTURES, REPO_ROOT, RUNS
from pf_space import primary_space
from score import CandidateText, match_block, scored_blocks
from validate_gold import SourceText
from walker1_report import Fixture, load_fixtures, project

REPORT = REPO_ROOT / "docs" / "verification" / "R3.5-text-fidelity.md"
CATEGORIES = (
    "Unicode",
    "Numeric signs",
    "Scale",
    "Superscripts",
    "Footnotes",
    "Table headings",
)
NO_INSTANCES = "no instances in sample"
CAPTURES = REPO_ROOT / "tests" / "fixtures" / "browser"
COPIES = RUNS / "gold-drafts"
LEG2 = "## Leg 2: canonical text against the browser's text"
CAPTURED = "### Against innerText"
COPIED = "### Against the user's rendered copies"
"""Leg 2's last section: it needs the user's local copies, so it comes last."""
HUNK_NAMES = dict(zip(HUNK_CATEGORIES, (*CATEGORIES, "other"), strict=True))


def references(gold: dict) -> tuple[list[str], list[str]]:
    """The gold's anchors (start, end, after, and table cell texts) and its table
    header texts, from anchorable blocks only."""
    anchors: list[str] = []
    headers: list[str] = []
    for block in gold["blocks"]:
        if block.get("unanchorable"):
            continue
        anchors += [block[key] for key in ("start", "end", "after") if key in block]
        anchors += [cell["text"] for cell in block.get("cells", [])]
        headers += block.get("headers", [])
    return anchors, headers


@dataclass
class Counts:
    """One fixture's counts in every category."""

    fixture: str
    non_ascii: Counter
    non_ascii_found: Counter
    replacement_characters: int
    signed: int
    signed_found: int
    signed_missing: list[str]
    scale_references: Counter
    scale_canonical: Counter
    sup_classes: Counter
    sup_other: list[str]
    sup_located: int
    sup_unlocatable: list[str]
    sup_hazards: list[str]
    footnotes: int
    footnotes_found: int
    footnotes_typed: int
    footnotes_merged: int
    gold_tables: int
    tables_located: int
    headers: int
    headers_lost: int
    headers_in_header_cell: int
    headers_in_other_cell: int
    headers_in_no_cell: int


def count(fixture: Fixture) -> Counts:
    raw = (FIXTURES / fixture.fixture / "source.html").read_bytes()
    canonical = comparison_space(fixture.result.document.canonical_text)
    anchors, headers = references(fixture.gold)

    characters, found = Counter(), Counter()
    for reference in (comparison_space(text) for text in anchors + headers):
        chars = non_ascii(reference)
        characters.update(chars)
        if chars and reference in canonical:
            found.update(chars)

    figures = [f for a in anchors for f in signed_figures(comparison_space(a))]
    missing = [figure for figure in figures if figure not in canonical]

    scale_references = Counter()
    for reference in anchors + headers:
        scale_references.update(scale_counts(comparison_space(reference)))

    source = read_source(decode_html_bytes(raw).text)
    classes, other, unlocatable, hazards, located = Counter(), [], [], [], 0
    for start, end in source.sup_runs:
        run = source.text[start:end]
        run_class = classify_run(run)
        classes[run_class] += 1
        if run_class == "other":
            other.append(run)
        if run_class == "empty":
            continue
        position = locate_run(canonical, source, start, end)
        if position is None:
            unlocatable.append(run)
            continue
        located += 1
        if run_class == "bare_digits" and joined_to_text(canonical, position):
            hazards.append(canonical[max(0, position - 20) : position + len(run)])

    dump, sources = project(
        fixture.result.document.canonical_text, fixture.result.elements
    )
    text = CandidateText(dump)
    gold_source = SourceText(raw)
    blocks = scored_blocks(fixture.gold)
    footnote_results = [
        match_block(block, text, gold_source)
        for block in blocks
        if block["type"] == "footnote"
    ]
    typed = sum(
        1
        for result in footnote_results
        if result.found and dump[result.start.position[0]].type == "footnote"
    )
    table_results = [
        match_block(block, text, gold_source)
        for block in blocks
        if block["type"] == "table"
    ]
    placement = Counter()
    for result in table_results:
        if not result.found:
            continue
        tables = [
            sources[i] for i in sorted(result.elements) if dump[i].type == "table"
        ]
        for header in result.block["headers"]:
            placement[header_placement(header, tables, fixture.result)] += 1

    merged, footnotes_found = fixture.walker1.counts["footnote_merging"]
    headers_lost, header_total = fixture.walker1.counts["header_table"]
    return Counts(
        fixture=fixture.fixture,
        non_ascii=characters,
        non_ascii_found=found,
        replacement_characters=fixture.result.manifest.replacement_characters,
        signed=len(figures),
        signed_found=len(figures) - len(missing),
        signed_missing=missing,
        scale_references=scale_references,
        scale_canonical=Counter(scale_counts(canonical)),
        sup_classes=classes,
        sup_other=other,
        sup_located=located,
        sup_unlocatable=unlocatable,
        sup_hazards=hazards,
        footnotes=sum(1 for b in fixture.gold["blocks"] if b["type"] == "footnote"),
        footnotes_found=footnotes_found,
        footnotes_typed=typed,
        footnotes_merged=merged,
        gold_tables=sum(1 for b in fixture.gold["blocks"] if b["type"] == "table"),
        tables_located=sum(1 for result in table_results if result.found),
        headers=header_total,
        headers_lost=headers_lost,
        headers_in_header_cell=placement["header cell"],
        headers_in_other_cell=placement["other cell"],
        headers_in_no_cell=placement["no cell"],
    )


def header_placement(
    header: str, tables: Sequence[DocumentElement], result: Canonicalized
) -> str:
    """Where a found table's header text sits: in a header cell, in another cell, or in
    no cell (a C1 table has none)."""
    text = result.document.canonical_text
    ids = {table.element_id for table in tables}
    key = primary_space(header)
    cells = [
        e
        for e in result.elements
        if e.type is ElementType.TABLE_CELL
        and e.parent_id in ids
        and key in primary_space(e.span.slice_of(text))
    ]
    if any(cell.table_cell and cell.table_cell.is_header for cell in cells):
        return "header cell"
    return "other cell" if cells else "no cell"


Hunk = tuple[str, str, str]
"""(category, canonical side, browser side)."""


@dataclass
class Leg2:
    """One fixture's classed hunks against innerText, and against the user's copy;
    ``copied`` is None where the copy is not present."""

    fixture: str
    captured: list[Hunk]
    copied: list[Hunk] | None


def leg2(fixture: Fixture) -> Leg2:
    raw = (FIXTURES / fixture.fixture / "source.html").read_bytes()
    source = read_source(decode_html_bytes(raw).text)
    runs = {source.text[start:end] for start, end in source.sup_runs if end > start}
    headers = [comparison_space(header) for header in references(fixture.gold)[1]]
    canonical = fixture.result.document.canonical_text

    def classed(rendered: str) -> list[Hunk]:
        return [
            (hunk_category(left, right, runs, headers), left, right)
            for left, right in token_hunks(canonical, rendered)
        ]

    capture = from_capture_json(
        (CAPTURES / f"{fixture.fixture}.capture.json").read_text(encoding="utf-8")
    )
    copy = COPIES / f"{fixture.fixture}.rendered.txt"
    copied = classed(copy.read_text(encoding="utf-8")) if copy.is_file() else None
    return Leg2(fixture.fixture, classed(capture.rendered_text), copied)


def instances(value: int) -> str:
    return f"**Instances:** {value if value else NO_INSTANCES}"


def render(counts: Sequence[Counts], legs: Sequence[Leg2]) -> str:
    total = Counter()
    for c in counts:
        total.update(
            non_ascii=sum(c.non_ascii.values()),
            non_ascii_found=sum(c.non_ascii_found.values()),
            replacement=c.replacement_characters,
            signed=c.signed,
            signed_found=c.signed_found,
            sup=sum(c.sup_classes.values()),
            sup_located=c.sup_located,
            footnotes=c.footnotes,
            footnotes_found=c.footnotes_found,
            footnotes_typed=c.footnotes_typed,
            footnotes_merged=c.footnotes_merged,
            gold_tables=c.gold_tables,
            tables_located=c.tables_located,
            headers=c.headers,
            headers_lost=c.headers_lost,
            header_cell=c.headers_in_header_cell,
            other_cell=c.headers_in_other_cell,
            no_cell=c.headers_in_no_cell,
        )
    characters = Counter()
    characters_found = Counter()
    for c in counts:
        characters.update(c.non_ascii)
        characters_found.update(c.non_ascii_found)
    lines = [
        "# R3.5 text fidelity",
        "",
        "Generated by `expirements/parser-fidelity/r35_report.py`; do not edit. Leg 1,",
        "below, compares the canonical text with the gold and `html.parser`; leg 2, at",
        "the end, with full browser captures and the user's rendered copies. With both",
        "legs the report is final (Stage 3 spec: R3.5 fidelity check).",
        "",
        "- **References.** The committed gold, marked from the browser rendering: its",
        "  anchors (start, end, after, and table cell texts) and table header texts,",
        "  from anchorable blocks; and the `<sup>` runs `html.parser` reads from each",
        "  `source.html`. Never lxml or the walker.",
        "- **Comparison space.** NFC with whitespace runs collapsed, never NFKC.",
        "- **No thresholds.** The report counts and lists (R13.1). These are",
        "  development-set numbers: the fixtures were Stage 1's test set.",
        "",
        "## Unicode",
        "",
        instances(total["non_ascii"]),
        "",
        f"- Non-ASCII characters in the references: {total['non_ascii']}.",
        (
            "- Of those, in references the canonical text contains verbatim:"
            f" {total['non_ascii_found']}."
        ),
        (
            "- U+FFFD characters in the canonical text, from the manifests:"
            f" {total['replacement']}."
        ),
        "",
        "The spec expected no instances, because the fixtures' bytes are ASCII. Their",
        "character references decode to non-ASCII characters, so the gold has real",
        "instances. V9's synthetic cases, in",
        "`packages/earnings-ingestion/tests/test_normalize.py`, still cover what the",
        "sample lacks.",
    ]
    if characters:
        lines += [
            "",
            "| Character | Name | In references | Found |",
            "| --- | --- | --- | --- |",
        ]
        for char, number in sorted(characters.items()):
            name = unicodedata.name(char, "UNNAMED")
            lines.append(
                f"| U+{ord(char):04X} | {name} | {number} | {characters_found[char]} |"
            )
    lines += [
        "",
        "## Numeric signs",
        "",
        instances(total["signed"]),
        "",
        f"- Signed figures in the gold anchors: {total['signed']}.",
        f"- Found with the sign intact: {total['signed_found']}.",
    ]
    missing = [(c.fixture, figure) for c in counts for figure in c.signed_missing]
    if missing:
        lines += ["", "| Fixture | Figure not found |", "| --- | --- |"]
        lines += [f"| `{fixture}` | {figure} |" for fixture, figure in missing]
    scale_total = sum(sum(c.scale_references.values()) for c in counts)
    lines += [
        "",
        "## Scale",
        "",
        instances(scale_total),
        "",
        "| Phrase | In references | In canonical text |",
        "| --- | --- | --- |",
    ]
    for phrase in SCALE_PHRASES:
        in_references = sum(c.scale_references[phrase] for c in counts)
        in_canonical = sum(c.scale_canonical[phrase] for c in counts)
        lines.append(f"| {phrase} | {in_references} | {in_canonical} |")
    hazards = [(c.fixture, h) for c in counts for h in c.sup_hazards]
    unlocatable = [(c.fixture, run) for c in counts for run in c.sup_unlocatable]
    lines += [
        "",
        "## Superscripts",
        "",
        instances(total["sup"]),
        "",
        f"- `<sup>` runs: {total['sup']}.",
        f"- Located: {total['sup_located']}. Empty runs have nothing to locate.",
        f"- Unlocatable: {len(unlocatable)}.",
        f"- Bare-digit runs joined to text, the fidelity hazard: {len(hazards)}.",
        "",
        "The hazard is tested synthetically, in",
        "`packages/earnings-ingestion/tests/test_fidelity.py`, and watched on Stage 5's",
        "pilot releases.",
        "",
        "| Class | Runs |",
        "| --- | --- |",
    ]
    for run_class in SUP_CLASSES:
        lines.append(
            f"| {run_class} | {sum(c.sup_classes[run_class] for c in counts)} |"
        )
    other = [(c.fixture, run) for c in counts for run in c.sup_other]
    if other:
        lines += ["", "| Fixture | Run classed other |", "| --- | --- |"]
        lines += [f"| `{fixture}` | {run!r} |" for fixture, run in other]
    if unlocatable:
        lines += ["", "| Fixture | Unlocatable run |", "| --- | --- |"]
        lines += [f"| `{fixture}` | {run!r} |" for fixture, run in unlocatable]
    if hazards:
        lines += ["", "| Fixture | Hazard |", "| --- | --- |"]
        lines += [f"| `{fixture}` | {text!r} |" for fixture, text in hazards]
    lines += [
        "",
        "## Footnotes",
        "",
        instances(total["footnotes"]),
        "",
        f"- Gold footnote blocks: {total['footnotes']}.",
        (
            "- Found by the frozen scorer on the re-score's projection:"
            f" {total['footnotes_found']}."
        ),
        f"- Typed `footnote`: {total['footnotes_typed']}.",
        (
            "- Merged into another element, the scorer's footnote-merging count:"
            f" {total['footnotes_merged']}."
        ),
        "",
        "## Table headings",
        "",
        instances(total["headers"]),
        "",
        f"- Gold tables: {total['gold_tables']}.",
        f"- Located by their anchors: {total['tables_located']}. The rest are",
        "  unlocated, as in V2.",
        f"- Header texts of located tables: {total['headers']}.",
        f"  - In a header cell: {total['header_cell']}.",
        f"  - In another cell: {total['other_cell']}.",
        f"  - In no cell of its table: {total['no_cell']}. Every header text of a C1",
        "    table lands here, since a C1 table has no cells.",
        f"- Lost, the scorer's table-header count: {total['headers_lost']}.",
        "",
        "## By fixture",
        "",
        "Each entry is a count out of a total:",
        "",
        "- **Non-ASCII:** characters found identically, out of those in the",
        "  references.",
        "- **Signed:** figures found with the sign intact.",
        "- **Sup runs:** runs located.",
        "- **Footnotes:** gold footnotes typed `footnote`.",
        "- **Header texts:** header texts of located tables that sit in a header cell.",
        "",
        "| Fixture | Non-ASCII | Signed | Sup runs | Footnotes | Header texts |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in counts:
        lines.append(
            f"| `{c.fixture}` | {sum(c.non_ascii_found.values())}/"
            f"{sum(c.non_ascii.values())} | {c.signed_found}/{c.signed}"
            f" | {c.sup_located}/{sum(c.sup_classes.values())}"
            f" | {c.footnotes_typed}/{c.footnotes}"
            f" | {c.headers_in_header_cell}/{c.headers} |"
        )
    return "\n".join(lines + render_leg2(legs)) + "\n"


def render_leg2(legs: Sequence[Leg2]) -> list[str]:
    lines = [
        "",
        LEG2,
        "",
        "- **References.** Each committed capture's `document.body.innerText`, under",
        "  capture policy `isolated/1` (`tests/fixtures/browser/`), and the user's",
        "  copies, made in Chrome by Select All and Copy, which stay local.",
        "- **Comparison.** A whitespace-insensitive token diff in comparison space.",
        "  `hunk_category` in `earnings_ingestion.canonical.fidelity` classes each",
        "  differing hunk into the six categories above, or other, by the first of its",
        "  tests the hunk passes. Every hunk is counted and listed.",
    ]
    for heading, label, pick in (
        (CAPTURED, "innerText", lambda leg: leg.captured),
        (COPIED, "Copy", lambda leg: leg.copied),
    ):
        names = list(HUNK_NAMES.values())
        lines += [
            "",
            heading,
            "",
            "| Fixture | Hunks | " + " | ".join(names) + " |",
            "| --- | --- |" + " --- |" * len(names),
        ]
        listed: list[tuple[str, Hunk]] = []
        for leg in legs:
            hunks = pick(leg)
            if hunks is None:
                lines.append(f"| `{leg.fixture}` | no local copy |" + " |" * len(names))
                continue
            counted = Counter(HUNK_NAMES[category] for category, _, _ in hunks)
            lines.append(
                f"| `{leg.fixture}` | {len(hunks)} | "
                + " | ".join(str(counted[name]) for name in names)
                + " |"
            )
            listed += [(leg.fixture, hunk) for hunk in hunks]
        if listed:
            lines += [
                "",
                f"| Fixture | Category | Canonical | {label} |",
                "| --- | --- | --- | --- |",
            ]
            lines += [
                f"| `{fixture}` | {HUNK_NAMES[category]} | {_side(left)} | {_side(right)} |"
                for fixture, (category, left, right) in listed
            ]
    return lines


def _side(text: str) -> str:
    text = text.replace("|", "\\|")
    return (text[:77] + "...") if len(text) > 80 else (text or "(nothing)")


def main() -> int:
    fixtures = load_fixtures()
    counts = [count(fixture) for fixture in fixtures]
    legs = [leg2(fixture) for fixture in fixtures]
    REPORT.write_text(render(counts, legs), encoding="utf-8", newline="\n")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```bash
uv run --locked --all-packages python expirements/parser-fidelity/r35_report.py
uv run --locked --all-packages pytest expirements/parser-fidelity/test_r35_report.py expirements/parser-fidelity/test_r35_report_current.py --import-mode=prepend -rs -q
uv run --locked --all-packages pytest tests/integration/test_r35_report.py -q
git diff --stat docs/verification/R3.5-text-fidelity.md
```

Expected: 

- `wrote docs/verification/R3.5-text-fidelity.md`;
- `7 passed`, with no skip, since the eight copies are present;
- `7 passed`;
- a `git diff --stat` line for the report. Plan A's leg keeps its numbers: only the
  title and introduction change above the new leg 2.

Read the new leg. Task 15's record summarizes its hunk counts per category.

- [ ] **Step 5: Run the checks**

```bash
python3 /tmp/plan5-escapes.py packages/earnings-ingestion/src/earnings_ingestion/canonical/fidelity.py packages/earnings-ingestion/tests/test_fidelity.py expirements/parser-fidelity/r35_report.py expirements/parser-fidelity/test_r35_report.py expirements/parser-fidelity/test_r35_report_current.py tests/integration/test_r35_report.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
```

Expected: `escapes intact`; `642 passed, 22 deselected`; `279 passed`; `All checks passed!` and `156 files already formatted`; `freeze verified`.

- [ ] **Step 6: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/canonical/fidelity.py packages/earnings-ingestion/tests/test_fidelity.py expirements/parser-fidelity/r35_report.py expirements/parser-fidelity/test_r35_report.py expirements/parser-fidelity/test_r35_report_current.py tests/integration/test_r35_report.py docs/verification/R3.5-text-fidelity.md
git commit -m "feat(fidelity): add R3.5's second leg and finalize the report"
```

---
### Task 13: The comparison, and ADR 0002

The frozen comparison runs once on the committed captures, and its report is
committed before anyone decides anything. The user then chooses ADR 0002's outcome,
among those the pre-registered rule allows (PB-14, PB-18). Nothing here tunes
anything: a number you dislike is a finding, not a bug, unless it comes from a
`crash` or `invalid-elements` failure (PB-13).

**Files:**

- Create: `expirements/parser-fidelity/test_layout1_report_current.py`.
- Generate: `docs/verification/layout-1-comparison.md`.
- Create: `docs/adr/0002-<outcome>.md`, named for the chosen outcome in Step 6.

**Interfaces:**

- Consumes: Task 10's `layout1_report.py`, units and freeze; Task 11's captures.
- Produces:
  - **The committed comparison.**
  - **ADR 0002 and its outcome.** Task 14 reads the outcome. It runs on 2 or 3 and is
    skipped on 1.

- [ ] **Step 1: Write the failing currency test**

Create `expirements/parser-fidelity/test_layout1_report_current.py`:

```python
"""The committed comparison is what layout1_report.py writes today."""

from layout1_report import REPORT, load_fixtures, render
from layout1_units import load_units


def test_the_committed_comparison_is_current() -> None:
    assert REPORT.read_text(encoding="utf-8") == render(
        load_fixtures(), load_units()
    ), (
        "regenerate: uv run --locked --all-packages python"
        " expirements/parser-fidelity/layout1_report.py"
    )
```

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_layout1_report_current.py --import-mode=prepend -q`

Expected: `1 failed`: `FileNotFoundError` for `docs/verification/layout-1-comparison.md`.

- [ ] **Step 2: Run the comparison**

```bash
uv run --locked --all-packages python expirements/parser-fidelity/preregister.py verify
uv run --locked --all-packages python expirements/parser-fidelity/layout1_report.py
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
```

Expected: `pre-registration verified`; `wrote docs/verification/layout-1-comparison.md`; `280 passed`; `All checks passed!` and `157 files already formatted`; `freeze verified`.

- [ ] **Step 3: Commit the comparison before the decision**

```bash
git log --oneline -3
git add expirements/parser-fidelity/test_layout1_report_current.py docs/verification/layout-1-comparison.md
git commit -m "docs(verification): run layout-1's pre-registered comparison"
```

- [ ] **Step 4: Read the report**

Read all of `docs/verification/layout-1-comparison.md`. Its sections are:

- **Versions.**
- **Captures,** with statuses, units, alignment failures, triggers, and retypes.
- **Targeted classes,** the units each configuration loses.
- **Metrics by fixture class,** with each regression marked.
- **Verdict.** For each candidate, the repaired classes, the regressions, and whether
  the rule allows its outcome. Its last line lists the outcomes ADR 0002 may choose.
- **Units,** kept or lost per configuration.
- **Alignment failures.**
- **Review-gate findings,** the probes.

Check the Captures table against Task 11: eight fixtures, each `completed` or
`partial`. Check the triggers against PB-13: `prose_row` on Southwest Airlines and
National Health Investors, and nothing elsewhere. A mismatch means the frozen code
or the captures changed. Stop and report it.

- [ ] **Step 5: ADR 0002's gate (human gate, hard stop)**

This step runs in the controller session with the user, never in a subagent.

1. **Summarize the report for the user.**
   - The Targeted classes table.
   - Each candidate's Verdict: repaired classes, regressions, and allowed or not.
   - The alignment failures, with their count per fixture class.
   - The probes' types for NHI's headline and Becton Dickinson's statement titles.
2. **State the cost of promotion (PB-18).** A capture becomes an input to
   canonicalization for every document the new version covers, Stage 5's and Stage
   15's releases included. Every such capture needs the pinned Chrome for Testing on
   macOS arm64 with its system fonts. A document without a usable capture fails
   rather than fall back.
3. **Ask with AskUserQuestion.** Offer only the outcomes the Verdict's last line
   allows. Put outcome 1 first as the default: it is always allowed and costs
   nothing. Give each option:
   - its measured benefit, as units lost under `walker-1` against units lost under
     the candidate, per repaired class;
   - its regressions;
   - its cost.

   Let the user add a reason in the notes.

Wait for the answer. Record it and the user's reason; Step 6 and Task 15 quote both.

- [ ] **Step 6: Write ADR 0002**

The file name follows the outcome:

| Outcome | File | Title |
| --- | --- | --- |
| 1 | `docs/adr/0002-keep-the-browser-capture-diagnostic-only.md` | 0002. Keep the browser capture diagnostic-only |
| 2 | `docs/adr/0002-promote-the-layout-1-fallback-as-walker-2.md` | 0002. Promote the layout-1 fallback as walker-2 |
| 3 | `docs/adr/0002-promote-layout-1-for-every-document-as-walker-2.md` | 0002. Promote layout-1 for every document as walker-2 |

Extract the template, copy it to the outcome's file, and then edit that file:

- fill every `[GATE: …]` slot from the report and the user's answer;
- keep only the chosen outcome's paragraph in Decision and its block in
  Consequences;
- delete every bracketed instruction.

```bash
python3 /tmp/plan5-extract.py /tmp/plan5-adr-0002.md
cp /tmp/plan5-adr-0002.md docs/adr/<the outcome's file>
```

Create `/tmp/plan5-adr-0002.md`:

````markdown
# [GATE: the outcome's title, from the table in Task 13, Step 6]

- **Status:** Accepted
- **Date:** [GATE: the date of the user's answer, YYYY-MM-DD]
- **Deciders:** Lowell Mason
- **Blast radius:** the canonicalization version of every release document, and every
  stage that binds to a `doc_id`: Stages 5, 6, 7, 10 and 15.

## Context

What was known on [GATE: the same date], when Stage 3's plan B
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
  [GATE: `commit` in `expirements/parser-fidelity/layout1-preregistered.toml`, 12
  characters] fixed the units, the rules, and the 23 files that decide the numbers.
  [GATE: "No post-freeze fix was needed.", or each `[[changes]]` entry with its reason
  and note.] Plan 5's PB-13 discloses what the planner saw before the freeze.
- **The targeted classes.** Units lost, for `walker-1`, `layout-1` and the fallback,
  from the report's "Targeted classes":
  1. headings typed `paragraph` by W12: [GATE: of 23 units, the three losses];
  2. prose inside data tables: [GATE: of 38 units, the three losses];
  3. content hidden by stylesheets: no units, because no fixture carries a
     stylesheet.
- **Regressions,** from the report's Verdict:
  - `layout-1`: [GATE: the count, and each regression as listed];
  - the fallback: [GATE: the count, and each regression as listed].
- **Alignment.** [GATE: layout-1's units and alignment failures over the eight
  fixtures, from the Captures table.]
- **What the rule allows.** [GATE: the Verdict's last line.]
- **Development-set numbers.** The fixtures were Stage 1's test set, and the classes
  were named from V2's residual failures on them (SC2). The comparison is not an
  independent validation (R12.2).
- **The cost of promotion.** Any promotion makes a browser capture an input to
  canonicalization for every document the new version covers, Stage 5's and Stage
  15's releases included. layout-1's geometry needs the pinned platform and font set.

## Decision

[Keep exactly one of the three paragraphs below.]

**Outcome 1: diagnostic-only capture.** `walker-1` stays the canonicalization policy
for every document. The browser capture, `layout-1` and `anchored-1` stay diagnostic:
nothing they produce enters a canonical document. [GATE: the user's reason.]

**Outcome 2: the fallback, as `walker-2`.** A new canonicalization version,
`walker-2`, keeps `walker-1`'s text and hash for every document. It takes
`layout-1`'s element stream exactly where `walker-1`'s recorded output fires a
trigger (`no_heading` or `prose_row`), and keeps `walker-1`'s elements elsewhere.
The activation is `fallback`. [GATE: the user's reason.]

**Outcome 3: `layout-1` for every document, as `walker-2`.** A new canonicalization
version, `walker-2`, keeps `walker-1`'s text and hash, and takes `layout-1`'s element
stream for every document. The activation is `every-document`.
[GATE: the user's reason.]

## Consequences

[Keep the block for the chosen outcome.]

On outcome 1:

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

On outcome 2 or 3:

- **Positive.** [GATE: each repaired class, with units lost under `walker-1` against
  under `walker-2`.]
- **Negative.**
  - Every `walker-2` document needs a usable capture of its own bytes, made once
    through the capture store in the pinned environment: Chrome for Testing
    154.0.8037.57 on macOS arm64, with its system fonts.
  - A missing or unusable capture fails the document, as `capture_unavailable` or
    `capture_unusable`. It never falls back to `walker-1` under `walker-2`'s name.
  - Switched documents have no list containers.
  - [GATE: the alignment failures in the switched documents, each recorded in its
    manifest, or "No switched document has an alignment failure."]
- **Neutral / follow-on.**
  - The eight fixtures are re-canonicalized under `walker-2` in
    `tests/fixtures/walker-2/` (plan 5, Task 14).
  - `walker-1`'s documents and fixtures are never rewritten, and offsets carry over,
    because the text hash is unchanged.
  - Stage 6 binds gold spans to `walker-2`'s `doc_id`s, and annotation may begin.
  - Stages 5 and 15 capture each release through the store before canonicalizing it.

## Alternatives considered

- [GATE: one bullet for each outcome not chosen. Give its configuration's repaired
  classes and regressions from the report. Where the rule did not allow the outcome,
  say so, with the reason.]

## Trade-offs & reversibility

- **Canonical text never changed.** Every outcome keeps `walker-1`'s text, so offsets
  and hashes carry over. A later reversal changes elements only, under a new version.
- **What would trigger a superseding ADR:**
  - the R12.2 validation set, or Stage 5's pilot releases, showing different results;
  - a change of browser, platform or font set, which needs a new capture policy
    version and a new comparison;
  - [GATE: on outcome 1, "a layout extractor that repairs a targeted class with no
    regression under a new pre-registration"; on 2 or 3, "a pilot release on which
    `walker-2` fails or regresses".]
````

Then:

```bash
grep -n 'GATE:\|\[Keep' docs/adr/0002-*.md
```

Expected: no output.

- [ ] **Step 7: Commit**

```bash
git log --oneline -3
git add docs/adr/0002-*.md
git commit -m "docs(adr): 0002, record the promotion decision for the browser path"
```

---
### Task 14: walker-2 (only on promotion)

**Run this task only if ADR 0002 chose outcome 2 or 3.** On outcome 1, mark every
step below `> Skipped: ADR 0002 chose outcome 1 (diagnostic-only); nothing is
promoted` and go to Task 15. Skipping it is the plan working as designed: there is
nothing to defer.

`walker-2` is the promoted canonicalization version (PB-19). It canonicalizes with
`walker-1`, then builds a new document from the same text, so the hash is unchanged
and offsets carry over. It takes one element stream, never a mix:

- `layout-1`'s, with S1 sentences, where it switches;
- `walker-1`'s, re-keyed, where it does not.

Every document needs a usable capture of its own bytes, and a document without one
fails. The eight fixtures are re-canonicalized into `tests/fixtures/walker-2/`, beside
`walker-1`'s, which never change (the spec's §Promotion decision, "After promotion").

**Files:**

- Create: `packages/earnings-ingestion/src/earnings_ingestion/promoted/__init__.py`,
  `records.py`, `pipeline.py`, `serialize.py`.
- Test (create): `packages/earnings-ingestion/tests/test_promoted.py`.
- Create: `tests/integration/regenerate_walker2_fixtures.py`,
  `tests/integration/test_walker2_golden.py`.
- Generate: `tests/fixtures/walker-2/<fixture>.json` (eight).
- Modify:
  - `.gitattributes` (block 2 of 2);
  - `docs/data-dictionary.md` (block 3);
  - `tests/contracts/test_data_dictionary.py` (block 3 of 3);
  - `packages/earnings-ingestion/tests/test_import_boundaries.py` (block 3 of 3).

**Interfaces:**

- Consumes:
  - `canonicalize`, `CanonicalizationManifest` and `IngestionRecord`;
  - `boilerplate_masks`, `POLICY_ID`, `POLICY_VERSION` and `with_sentences`, all
    from `walker-1`, read only;
  - Task 8's `LayoutExtractor`, `AlignmentFailure` and `fired`;
  - Task 11's captures;
  - ADR 0002's outcome.
- Produces, in `earnings_ingestion.promoted`:
  - `PROMOTED_VERSION = "walker-2"`.
  - `ACTIVATION`: `Activation.FALLBACK` on outcome 2, `Activation.EVERY_DOCUMENT` on
    outcome 3.
  - `Activation` and `PromotionFailureReason`.
  - The records `PromotedManifest`, `PromotionFailure` and `Promoted`.
  - `canonicalize_promoted(raw, capture, *, source_document_id, media_type, activation=ACTIVATION) -> Promoted | PromotionFailure`.
  - `promoted.serialize.to_promoted_json(result) -> str`, in the canonical-fixture
    format with walker-2's manifest.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-ingestion/tests/test_promoted.py`:

```python
"""walker-2 on synthetic captures: one stream or the other, never walker-1 under its
name, and never a changed text (SC14; plan 5, PB-19)."""

from collections.abc import Callable

import pytest
from earnings_core import ElementType, sha256_hex, validate_elements
from earnings_ingestion.browser.metadata import parse_metadata
from earnings_ingestion.browser.records import (
    CaptureReason,
    CaptureStatus,
    RenderedCapture,
)
from earnings_ingestion.browser.renderer import EMPTY_LAYOUT
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.promoted import (
    Activation,
    Promoted,
    PromotionFailure,
    PromotionFailureReason,
    canonicalize_promoted,
)

Make = Callable[..., RenderedCapture]
TITLED = (
    b"<h1>Acme Reports Results</h1><p>Revenue rose 5% in the quarter. Margins held.</p>"
)
UNTITLED = (
    b"<p>Acme Reports Results</p><p>Revenue rose 5% in the quarter. Margins held.</p>"
)


def promoted(raw: bytes, capture, **options) -> Promoted | PromotionFailure:
    return canonicalize_promoted(
        raw, capture, source_document_id="release", media_type="text/html", **options
    )


def walker1(raw: bytes) -> Canonicalized:
    result = canonicalize(raw, source_document_id="release", media_type="text/html")
    assert isinstance(result, Canonicalized)
    return result


def capture_of(make: Make, parts, raw: bytes, *texts: str, bold_first: bool = True):
    """A capture of ``raw`` whose blocks are ``texts``, the first bold."""
    blocks = [
        parts.block(parts.run(text, bold=bold_first and index == 0))
        for index, text in enumerate(texts)
    ]
    return make(
        layout=parse_metadata({"blocks": blocks, "tables": []}),
        rendered_text="\n".join(texts),
        raw_sha256=sha256_hex(raw),
    )


def test_without_a_trigger_the_fallback_keeps_walker1s_elements(
    make_capture: Make, parts
) -> None:
    capture = capture_of(
        make_capture,
        parts,
        TITLED,
        "Acme Reports Results",
        "Revenue rose 5% in the quarter. Margins held.",
    )
    base = walker1(TITLED)
    result = promoted(TITLED, capture, activation=Activation.FALLBACK)
    assert isinstance(result, Promoted)
    assert result.document.canonical_text == base.document.canonical_text
    assert result.document.canonical_hash == base.document.canonical_hash
    assert result.document.doc_id != base.document.doc_id
    assert result.document.canonicalization_version == "walker-2"
    assert [e.model_dump(exclude={"doc_id"}) for e in result.elements] == [
        e.model_dump(exclude={"doc_id"}) for e in base.elements
    ]
    assert [m.span for m in result.masked.masks] == [m.span for m in base.masked.masks]
    manifest = result.manifest
    assert (manifest.switched, manifest.triggers, manifest.capture_id) == (
        False,
        (),
        capture.capture_id,
    )
    assert (manifest.layout_version, manifest.mapping_policy) == (None, None)
    assert manifest.base == base.manifest
    assert manifest.limitations == ()


@pytest.mark.parametrize("raw", [TITLED, UNTITLED], ids=["no-trigger", "trigger"])
def test_without_a_capture_every_document_fails_explicitly(raw: bytes) -> None:
    """A capture is an input for every document, whether or not it switches."""
    result = promoted(raw, None)
    assert isinstance(result, PromotionFailure)
    assert result.reason is PromotionFailureReason.CAPTURE_UNAVAILABLE
    assert result.canonicalization_version == "walker-2"


def test_a_capture_of_other_bytes_or_a_failed_one_is_unusable(
    make_capture: Make, parts
) -> None:
    other = capture_of(make_capture, parts, b"<p>other</p>", "Acme Reports Results")
    failed = make_capture(
        layout=EMPTY_LAYOUT,
        rendered_text="",
        raw_sha256=sha256_hex(UNTITLED),
        status=CaptureStatus.FAILED,
        reason=CaptureReason.TIMEOUT,
    )
    for raw in (TITLED, UNTITLED):
        for capture in (other, failed):
            result = promoted(raw, capture)
            assert isinstance(result, PromotionFailure)
            assert result.reason is PromotionFailureReason.CAPTURE_UNUSABLE


def test_a_trigger_switches_to_layout1_with_sentences(
    make_capture: Make, parts
) -> None:
    capture = capture_of(
        make_capture,
        parts,
        UNTITLED,
        "Acme Reports Results",
        "Revenue rose 5% in the quarter. Margins held.",
    )
    base = walker1(UNTITLED)
    result = promoted(UNTITLED, capture)
    assert isinstance(result, Promoted)
    assert result.document.canonical_hash == base.document.canonical_hash
    assert validate_elements(result.document, result.elements) == ()
    assert [e.type for e in result.elements] == [
        ElementType.HEADING,
        ElementType.PARAGRAPH,
        ElementType.SENTENCE,
        ElementType.SENTENCE,
    ]
    manifest = result.manifest
    assert manifest.switched and manifest.triggers == ("no_heading",)
    assert manifest.capture_id == capture.capture_id
    assert (manifest.layout_version, manifest.mapping_policy) == (
        "layout-1",
        "anchored-1",
    )
    assert manifest.limitations == ("no_list_containers",)


def test_every_document_activation_switches_without_a_trigger(
    make_capture: Make, parts
) -> None:
    missing = promoted(TITLED, None, activation=Activation.EVERY_DOCUMENT)
    assert isinstance(missing, PromotionFailure)
    capture = capture_of(
        make_capture,
        parts,
        TITLED,
        "Acme Reports Results",
        "Revenue rose 5% in the quarter. Margins held.",
    )
    result = promoted(TITLED, capture, activation=Activation.EVERY_DOCUMENT)
    assert isinstance(result, Promoted)
    assert result.manifest.switched and result.manifest.triggers == ()


def test_an_alignment_failure_keeps_the_document_and_is_recorded(
    make_capture: Make, parts
) -> None:
    capture = capture_of(
        make_capture,
        parts,
        UNTITLED,
        "Acme Reports Results",
        "Revenue fell 5% in the quarter. Margins held.",
    )
    result = promoted(UNTITLED, capture)
    assert isinstance(result, Promoted)
    manifest = result.manifest
    assert [f.text for f in manifest.alignment_failures] == [
        "Revenue fell 5% in the quarter. Margins held."
    ]
    assert manifest.limitations == ("no_list_containers", "alignment_failed")
    uncovered = [e for e in result.elements if e.source_type == "layout:uncovered"]
    assert [e.type for e in uncovered] == [ElementType.OTHER]


def test_a_source_walker1_refuses_is_refused_with_its_reason() -> None:
    result = canonicalize_promoted(
        TITLED, None, source_document_id="release", media_type="application/pdf"
    )
    assert isinstance(result, PromotionFailure)
    assert result.reason is PromotionFailureReason.CANONICALIZATION_FAILED
    assert "unsupported_media_type" in result.detail


@pytest.mark.parametrize("activation", list(Activation))
def test_the_activation_is_recorded(
    activation: Activation, make_capture: Make, parts
) -> None:
    capture = capture_of(
        make_capture,
        parts,
        TITLED,
        "Acme Reports Results",
        "Revenue rose 5% in the quarter. Margins held.",
    )
    result = promoted(TITLED, capture, activation=activation)
    assert isinstance(result, Promoted)
    assert result.manifest.activation is activation
```

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_promoted.py -q`

Expected: `1 error during collection`: `ModuleNotFoundError: No module named 'earnings_ingestion.promoted'`.

- [ ] **Step 2: Write walker-2**

Create `packages/earnings-ingestion/src/earnings_ingestion/promoted/records.py`:

```python
"""walker-2's records: its manifest, its failure, and its result (plan 5, PB-19).

walker-1's records cannot change: its committed fixtures pin every manifest byte,
``schema_version`` included, so a new field, even with a default, or a schema bump
would fail walker-1's golden test. walker-2's records are therefore new ingestion
records, at ingestion schema version 1. docs/data-dictionary.md documents every field.
"""

from enum import StrEnum
from typing import Self

from earnings_core import CanonicalDocument, DocumentElement, MaskedDocument
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import BaseModel, ConfigDict, NonNegativeInt, model_validator

from earnings_ingestion.canonical.records import (
    CanonicalizationManifest,
    IngestionRecord,
)
from earnings_ingestion.layout.records import AlignmentFailure


class Activation(StrEnum):
    """Where walker-2 uses layout-1's element stream: ADR 0002's outcome."""

    FALLBACK = "fallback"
    """Outcome 2: only where walker-1's output fires a trigger."""
    EVERY_DOCUMENT = "every-document"
    """Outcome 3: every document."""


class PromotedManifest(IngestionRecord):
    """How one walker-2 document was made. Like walker-1's, it holds no timestamp and
    no path, so it regenerates byte for byte."""

    canonicalization_version: IdPart
    activation: Activation
    base: CanonicalizationManifest
    """walker-1's manifest for the same bytes: decoding, versions, and raw hash."""
    switched: bool
    """layout-1's element stream, not walker-1's, gives the elements."""
    triggers: tuple[str, ...]
    capture_id: str
    """The capture of the same bytes that walker-2 received: every document needs one."""
    layout_version: IdPart | None
    mapping_policy: IdPart | None
    retypes: dict[str, NonNegativeInt]
    alignment_failures: tuple[AlignmentFailure, ...]
    element_counts: dict[str, NonNegativeInt]
    limitations: tuple[str, ...]
    mask_policy_id: IdPart
    mask_policy_version: IdPart
    mask_count: NonNegativeInt

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        used = (self.layout_version, self.mapping_policy)
        if self.switched != all(value is not None for value in used):
            raise ValueError("layout-1's versions are named exactly when switched")
        if not self.switched and self.alignment_failures:
            raise ValueError("only a switched document has alignment failures")
        return self


class PromotionFailureReason(StrEnum):
    """Why walker-2 made no document. It never falls back to walker-1 under its name."""

    CANONICALIZATION_FAILED = "canonicalization_failed"
    """walker-1's pass refused the bytes; ``detail`` carries its reason."""
    CAPTURE_UNAVAILABLE = "capture_unavailable"
    """No capture was given: walker-2 needs one for every document."""
    CAPTURE_UNUSABLE = "capture_unusable"
    """The capture given is failed or unavailable, or is of other bytes."""


class PromotionFailure(IngestionRecord):
    """A document walker-2 refused, with nothing partial."""

    source_document_id: IdPart
    raw_sha256: Sha256Hex
    canonicalization_version: IdPart
    reason: PromotionFailureReason
    detail: str


class Promoted(BaseModel):
    """walker-2's result: an in-memory bundle, not a persisted record."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    document: CanonicalDocument
    elements: tuple[DocumentElement, ...]
    masked: MaskedDocument
    manifest: PromotedManifest

    @model_validator(mode="after")
    def _parts_agree(self) -> Self:
        if self.masked.document != self.document:
            raise ValueError("the masks belong to another document")
        if any(element.doc_id != self.document.doc_id for element in self.elements):
            raise ValueError("an element belongs to another document")
        if (
            self.manifest.base.source_document_id,
            self.manifest.canonicalization_version,
        ) != (
            self.document.source_document_id,
            self.document.canonicalization_version,
        ):
            raise ValueError("the manifest describes another document")
        return self
```

Create `packages/earnings-ingestion/src/earnings_ingestion/promoted/pipeline.py`:

```python
"""``canonicalize_promoted``: walker-2 over walker-1's text (plan 5, PB-19).

Built only when ADR 0002 chooses outcome 2 or 3. walker-2 never changes canonical
text (SC14): it canonicalizes with walker-1, then builds a new document version from
the same text, so every offset carries over and only ``doc_id`` changes. Its elements
come from one of two streams, never a mix of the two:

- **walker-1's**, re-keyed to the new document, where it does not switch;
- **layout-1's**, mapped onto the text under ``anchored-1``, with S1 sentences added,
  where it switches: under ``Activation.FALLBACK`` when walker-1's output fires a
  trigger, and under ``Activation.EVERY_DOCUMENT`` always.

Every document needs a usable capture of the same bytes, whether or not it switches:
a promotion makes the capture an input to canonicalization for every document the
version covers (Stage 3 spec, Promotion decision). Without one walker-2 fails
explicitly, and it never falls back to walker-1 under walker-2's name (the browser
spec's Reproducibility and failure handling). An alignment failure keeps the
document: the unit's text is ``other``, never narrative, and the manifest records the
failure and the limitation. A switched document has no list containers, which the
manifest records too. Masks are boilerplate/1, recomputed over the new elements.
"""

from collections import Counter

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    sha256_hex,
    validate_elements,
)

from earnings_ingestion.browser.records import CaptureStatus, RenderedCapture
from earnings_ingestion.canonical import CanonicalizationFailure, canonicalize
from earnings_ingestion.canonical.boilerplate import (
    POLICY_ID,
    POLICY_VERSION,
    boilerplate_masks,
)
from earnings_ingestion.canonical.sentences import with_sentences
from earnings_ingestion.canonical.triggers import fired
from earnings_ingestion.layout import LayoutExtractor
from earnings_ingestion.promoted.records import (
    Activation,
    Promoted,
    PromotedManifest,
    PromotionFailure,
    PromotionFailureReason,
)

PROMOTED_VERSION = "walker-2"
ACTIVATION = Activation.FALLBACK
"""ADR 0002's outcome: ``FALLBACK`` for outcome 2, ``EVERY_DOCUMENT`` for outcome 3."""
USABLE = frozenset({CaptureStatus.COMPLETED, CaptureStatus.PARTIAL})
NO_LIST_CONTAINERS = "no_list_containers"
"""Limitation: a switched document's list items have no container."""
ALIGNMENT_FAILED = "alignment_failed"
"""Limitation: some layout-1 units did not map, and their text is ``other``."""


def canonicalize_promoted(
    raw: bytes,
    capture: RenderedCapture | None,
    *,
    source_document_id: str,
    media_type: str,
    activation: Activation = ACTIVATION,
) -> Promoted | PromotionFailure:
    """walker-2's document for ``raw``, or the reason there is none."""
    raw_sha256 = sha256_hex(raw)

    def failure(reason: PromotionFailureReason, detail: str) -> PromotionFailure:
        return PromotionFailure(
            source_document_id=source_document_id,
            raw_sha256=raw_sha256,
            canonicalization_version=PROMOTED_VERSION,
            reason=reason,
            detail=detail,
        )

    base = canonicalize(
        raw, source_document_id=source_document_id, media_type=media_type
    )
    if isinstance(base, CanonicalizationFailure):
        return failure(
            PromotionFailureReason.CANONICALIZATION_FAILED,
            f"walker-1: {base.reason.value}: {base.detail}",
        )
    if capture is None:
        return failure(
            PromotionFailureReason.CAPTURE_UNAVAILABLE,
            "walker-2 needs a capture of every document, and none was given",
        )
    if capture.status not in USABLE or capture.raw_sha256 != raw_sha256:
        return failure(
            PromotionFailureReason.CAPTURE_UNUSABLE,
            f"capture {capture.capture_id} is {capture.status.value}"
            + ("" if capture.raw_sha256 == raw_sha256 else ", of other bytes"),
        )
    triggers = fired(base.document, base.elements)
    switched = activation is Activation.EVERY_DOCUMENT or bool(triggers)
    document = CanonicalDocument.create(
        source_document_id=source_document_id,
        canonicalization_version=PROMOTED_VERSION,
        canonical_text=base.document.canonical_text,
    )
    if not switched:
        elements = [
            DocumentElement.model_validate(
                {**e.model_dump(), "doc_id": document.doc_id}
            )
            for e in base.elements
        ]
        extraction = None
    else:
        extraction = LayoutExtractor().map_onto(capture, document)
        elements = with_sentences(document, extraction.elements)
    rejections = validate_elements(document, elements)
    if rejections:
        raise AssertionError(f"walker-2 built an invalid element set: {rejections}")
    masked = boilerplate_masks(document, elements)
    limitations = [] if extraction is None else [NO_LIST_CONTAINERS]
    if extraction is not None and extraction.failures:
        limitations.append(ALIGNMENT_FAILED)
    counts = Counter(element.type.value for element in elements)
    manifest = PromotedManifest(
        canonicalization_version=PROMOTED_VERSION,
        activation=activation,
        base=base.manifest,
        switched=switched,
        triggers=triggers,
        capture_id=capture.capture_id,
        layout_version=None if extraction is None else extraction.layout_version,
        mapping_policy=None if extraction is None else extraction.mapping_policy,
        retypes=base.manifest.retypes if extraction is None else extraction.retypes,
        alignment_failures=() if extraction is None else extraction.failures,
        element_counts=dict(sorted(counts.items())),
        limitations=tuple(limitations),
        mask_policy_id=POLICY_ID,
        mask_policy_version=POLICY_VERSION,
        mask_count=len(masked.masks),
    )
    return Promoted(
        document=document, elements=tuple(elements), masked=masked, manifest=manifest
    )
```

Create `packages/earnings-ingestion/src/earnings_ingestion/promoted/serialize.py`:

```python
"""walker-2's fixture format: walker-1's, with walker-2's manifest (plan 5, PB-19).

One JSON object with sorted keys: ``document``, ``elements``, ``manifest``, and
``masks``. Each record is one line with sorted keys and ASCII escapes.
"""

import json
from collections.abc import Iterable

from pydantic import BaseModel

from earnings_ingestion.promoted.records import Promoted


def to_promoted_json(result: Promoted) -> str:
    """``result`` in the fixture format, ending with a newline."""
    lines = [
        "{",
        f'"document": {_record(result.document)},',
        f'"elements": {_records(result.elements)},',
        f'"manifest": {_record(result.manifest)},',
        f'"masks": {_records(result.masked.masks)}',
        "}",
    ]
    return "\n".join(lines) + "\n"


def _record(model: BaseModel) -> str:
    return json.dumps(model.model_dump(mode="json"), sort_keys=True, ensure_ascii=True)


def _records(models: Iterable[BaseModel]) -> str:
    rows = [_record(model) for model in models]
    if not rows:
        return "[]"
    return "[\n" + ",\n".join(rows) + "\n]"
```

Create `packages/earnings-ingestion/src/earnings_ingestion/promoted/__init__.py`:

```python
"""walker-2, the promoted canonicalization policy, built only on ADR 0002's outcome 2
or 3 (Stage 3, plan B).

``canonicalize_promoted`` is the entry point.
"""

from earnings_ingestion.promoted.pipeline import (
    ACTIVATION,
    PROMOTED_VERSION,
    canonicalize_promoted,
)
from earnings_ingestion.promoted.records import (
    Activation,
    Promoted,
    PromotedManifest,
    PromotionFailure,
    PromotionFailureReason,
)

__all__ = [
    "ACTIVATION",
    "PROMOTED_VERSION",
    "Activation",
    "Promoted",
    "PromotedManifest",
    "PromotionFailure",
    "PromotionFailureReason",
    "canonicalize_promoted",
]
```

- [ ] **Step 3: Set the activation from ADR 0002**

On outcome 2, change nothing: `ACTIVATION = Activation.FALLBACK` is already the
default. On outcome 3 only, run:

```bash
python3 - <<'EOF'
from pathlib import Path

path = Path("packages/earnings-ingestion/src/earnings_ingestion/promoted/pipeline.py")
text = path.read_text(encoding="utf-8")
old = "ACTIVATION = Activation.FALLBACK\n"
if text.count(old) != 1:
    raise SystemExit(f"expected one match, found {text.count(old)}")
path.write_text(text.replace(old, "ACTIVATION = Activation.EVERY_DOCUMENT\n"), encoding="utf-8")
print("activation: every-document")
EOF
```

The tests pass under either activation: each one that depends on it names it.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_promoted.py -q`

Expected: `10 passed`.

- [ ] **Step 5: Document walker-2's records, and extend the boundary checks**

Replace `tests/contracts/test_data_dictionary.py` with:

```python
"""docs/data-dictionary.md documents every field and value of the core contracts
and of the ingestion records: the canonicalizer's, the capture's, layout-1's, and
walker-2's.

AGENTS.md §191: document public interfaces and update the data dictionary in the
same change. A contract that gains, loses, or renames a field fails here.
"""

import re
from enum import StrEnum
from pathlib import Path

import earnings_core as core
import earnings_ingestion.canonical as ingestion
import pytest
from earnings_ingestion import browser, layout, promoted
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
    promoted.PromotedManifest,
    promoted.PromotionFailure,
    promoted.Promoted,
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
    promoted.Activation,
    promoted.PromotionFailureReason,
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
`python3 /tmp/plan5-extract.py tests/contracts/test_data_dictionary.py 3`.

Append to `docs/data-dictionary.md`:

```markdown

## walker-2 records, schema version 1

- **Package.** `earnings_ingestion.promoted`, in `packages/earnings-ingestion`, built
  because ADR 0002 promoted (plan 5).
- **Schema version.** These records join ingestion schema version `1`: walker-1's
  records cannot change, because its committed fixtures pin every manifest byte.
- **walker-2 fixtures.** `tests/fixtures/walker-2/<fixture_id>.json` has walker-1's
  fixture format, with a `PromotedManifest` as its `manifest`.

### `Activation`

| Value | Meaning |
| --- | --- |
| `fallback` | Outcome 2: layout-1's stream only where walker-1's output fires a trigger |
| `every-document` | Outcome 3: layout-1's stream for every document |

### `PromotedManifest`

How one walker-2 document was made. It holds no timestamp and no path.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `canonicalization_version` | ID part | `walker-2` |
| `activation` | `Activation` | ADR 0002's outcome |
| `base` | `CanonicalizationManifest` | walker-1's manifest for the same bytes |
| `switched` | bool | layout-1's element stream, not walker-1's, gives the elements |
| `triggers` | tuple of string | The triggers walker-1's output fired: `no_heading`, `prose_row` |
| `capture_id` | string | The capture of the same bytes that walker-2 received; every document needs one |
| `layout_version` | ID part, or null | `layout-1`; null exactly when not switched |
| `mapping_policy` | ID part, or null | `anchored-1`; null exactly when not switched |
| `retypes` | map of rule to int | C1–C5's retypes in the stream used |
| `alignment_failures` | tuple of `AlignmentFailure` | layout-1's unmapped units; their text is `other` |
| `element_counts` | map of type to int | Elements by `ElementType` value |
| `limitations` | tuple of string | `no_list_containers` when switched; `alignment_failed` when a unit did not map |
| `mask_policy_id` | ID part | `boilerplate` |
| `mask_policy_version` | ID part | `1` |
| `mask_count` | int ≥ 0 | Masks the policy found |

### `PromotionFailureReason`

| Value | Meaning |
| --- | --- |
| `canonicalization_failed` | walker-1's pass refused the bytes; the detail carries its reason |
| `capture_unavailable` | No capture was given; walker-2 needs one for every document |
| `capture_unusable` | The capture given is failed or unavailable, or is of other bytes |

### `PromotionFailure`

A document walker-2 refused, with nothing partial. walker-2 never falls back to
walker-1 under its own name.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `source_document_id` | ID part | The saved source document |
| `raw_sha256` | 64 lowercase hex | SHA-256 of the saved bytes |
| `canonicalization_version` | ID part | `walker-2` |
| `reason` | `PromotionFailureReason` | The failure class |
| `detail` | string | What failed |

### `Promoted`

`canonicalize_promoted`'s result: an in-memory bundle, not a persisted record.

| Field | Type | Meaning |
| --- | --- | --- |
| `document` | `CanonicalDocument` | walker-2's document: walker-1's text, a new `doc_id` |
| `elements` | tuple of `DocumentElement` | One stream: walker-1's re-keyed, or layout-1's with S1 sentences |
| `masked` | `MaskedDocument` | boilerplate/1's masks over those elements |
| `manifest` | `PromotedManifest` | How the document was made |
```

This is block 3 for that path: extract it with
`python3 /tmp/plan5-extract.py docs/data-dictionary.md 3`.

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
        "earnings_ingestion.promoted",
    ],
)
def test_importing_ingestion_loads_nothing_forbidden(module: str) -> None:
    assert modules_loaded_by(module) & FORBIDDEN == set()
```

This is block 3 for that path: extract it with
`python3 /tmp/plan5-extract.py packages/earnings-ingestion/tests/test_import_boundaries.py 3`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py packages/earnings-ingestion/tests/test_import_boundaries.py -q`

Expected: `48 passed`.

- [ ] **Step 6: Re-canonicalize the fixtures under walker-2**

Create `tests/integration/regenerate_walker2_fixtures.py`:

```python
"""Write tests/fixtures/walker-2/ from the releases and their committed captures.

    uv run --locked --all-packages python tests/integration/regenerate_walker2_fixtures.py

Run only after ADR 0002 promotes (plan 5, Task 14). Each release is canonicalized by
walker-2 with its committed capture from tests/fixtures/browser/. A failure stops the
run: a promoted version never falls back to walker-1. pytest never collects this file.
"""

from pathlib import Path

from earnings_ingestion.browser.serialize import from_capture_json
from earnings_ingestion.promoted import Promoted, canonicalize_promoted
from earnings_ingestion.promoted.serialize import to_promoted_json

REPO = Path(__file__).resolve().parents[2]
RELEASES = REPO / "tests" / "fixtures" / "releases"
CAPTURES = REPO / "tests" / "fixtures" / "browser"
WALKER2 = REPO / "tests" / "fixtures" / "walker-2"


def main() -> int:
    WALKER2.mkdir(exist_ok=True)
    for source in sorted(RELEASES.glob("*/source.html")):
        fixture = source.parent.name
        capture = from_capture_json(
            (CAPTURES / f"{fixture}.capture.json").read_text(encoding="utf-8")
        )
        result = canonicalize_promoted(
            source.read_bytes(),
            capture,
            source_document_id=fixture,
            media_type="text/html",
        )
        if not isinstance(result, Promoted):
            raise SystemExit(f"{fixture}: {result.reason.value}: {result.detail}")
        target = WALKER2 / f"{fixture}.json"
        target.write_text(to_promoted_json(result), encoding="utf-8", newline="\n")
        print(
            f"wrote {target.relative_to(REPO)} (switched: {result.manifest.switched})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `tests/integration/test_walker2_golden.py`:

```python
"""walker-2's fixtures regenerate byte for byte and keep walker-1's text (SC14).

Offsets carry over: each walker-2 document's canonical hash is walker-1's, and only
``doc_id`` differs. Where walker-2 does not switch, its elements are walker-1's.
"""

import json
from pathlib import Path

import pytest
from earnings_ingestion.browser.serialize import from_capture_json
from earnings_ingestion.promoted import Promoted, canonicalize_promoted
from earnings_ingestion.promoted.serialize import to_promoted_json

ROOT = Path(__file__).resolve().parents[2]
RELEASES = ROOT / "tests" / "fixtures" / "releases"
CAPTURES = ROOT / "tests" / "fixtures" / "browser"
WALKER1 = ROOT / "tests" / "fixtures" / "canonical"
WALKER2 = ROOT / "tests" / "fixtures" / "walker-2"
FIXTURES = sorted(path.parent.name for path in RELEASES.glob("*/source.html"))


def regenerate(fixture: str) -> Promoted:
    capture = from_capture_json(
        (CAPTURES / f"{fixture}.capture.json").read_text(encoding="utf-8")
    )
    result = canonicalize_promoted(
        (RELEASES / fixture / "source.html").read_bytes(),
        capture,
        source_document_id=fixture,
        media_type="text/html",
    )
    assert isinstance(result, Promoted), result
    return result


@pytest.mark.parametrize("fixture", FIXTURES)
def test_each_walker2_fixture_regenerates_byte_for_byte(fixture: str) -> None:
    committed = (WALKER2 / f"{fixture}.json").read_text(encoding="utf-8")
    assert to_promoted_json(regenerate(fixture)) == committed, (
        "walker-2's output changed: that needs walker-3, never regenerated walker-2"
        " files"
    )


@pytest.mark.parametrize("fixture", FIXTURES)
def test_walker2_keeps_walker1s_text_and_offsets(fixture: str) -> None:
    walker1 = json.loads((WALKER1 / f"{fixture}.json").read_text(encoding="utf-8"))
    walker2 = json.loads((WALKER2 / f"{fixture}.json").read_text(encoding="utf-8"))
    assert (
        walker2["document"]["canonical_hash"] == walker1["document"]["canonical_hash"]
    )
    assert walker2["document"]["doc_id"] != walker1["document"]["doc_id"]
    if not walker2["manifest"]["switched"]:
        strip = [{**e, "doc_id": None} for e in walker1["elements"]]
        assert [{**e, "doc_id": None} for e in walker2["elements"]] == strip
```

Append to `.gitattributes`:

```text
tests/fixtures/walker-2/*.json -text
```

This is block 2 for that path: extract it with
`python3 /tmp/plan5-extract.py .gitattributes 2`.

```bash
uv run --locked --all-packages python tests/integration/regenerate_walker2_fixtures.py
uv run --locked --all-packages pytest tests/integration/test_walker2_golden.py tests/integration/test_canonical_golden.py -q
```

Expected:

- eight lines `wrote tests/fixtures/walker-2/<fixture>.json (switched: <bool>)`;
- on outcome 2, `switched: True` exactly for `0000092380-07-000011_ex-99-1` and
  `0000877860-13-000100_ex-99-1`, the two documents whose triggers fire (PB-13);
- on outcome 3, `switched: True` for all eight;
- `25 passed`: walker-2's 16 tests and walker-1's 9, which still pass unchanged.

A `SystemExit` naming a fixture means `walker-2` refused it. Stop and report: a
promoted version never falls back.

- [ ] **Step 7: Run the checks**

```bash
python3 /tmp/plan5-escapes.py packages/earnings-ingestion/src/earnings_ingestion/promoted/*.py packages/earnings-ingestion/tests/test_promoted.py tests/integration/regenerate_walker2_fixtures.py tests/integration/test_walker2_golden.py tests/contracts/test_data_dictionary.py packages/earnings-ingestion/tests/test_import_boundaries.py
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
git status --short
```

Expected: `escapes intact`; `674 passed, 22 deselected`; `All checks passed!` and `164 files already formatted`. The status lists only this task's files.

- [ ] **Step 8: Commit**

```bash
git log --oneline -3
git add packages/earnings-ingestion/src/earnings_ingestion/promoted packages/earnings-ingestion/tests/test_promoted.py tests/integration/regenerate_walker2_fixtures.py tests/integration/test_walker2_golden.py tests/fixtures/walker-2 .gitattributes docs/data-dictionary.md tests/contracts/test_data_dictionary.py packages/earnings-ingestion/tests/test_import_boundaries.py
git commit -m "feat(ingestion): promote layout-1 as walker-2 and re-canonicalize the fixtures"
```

---
### Task 15: The verification record, the harness README, the current state, and final verification

The record gathers what plan B verified, in the house style of
`docs/verification/walker-1.md`. It also gives each review-gate finding its
disposition, which closes plan 4's open deferred item (PB-21). Its numbers were not
known at planning time, so the template holds `[GATE: …]` slots. Fill each from the
named report or step, and never leave one.

**Files:**

- Create: `docs/verification/layout-1.md`.
- Modify: `expirements/parser-fidelity/README.md` (four rows, one row reworded, and
  the Stage 3 section, by exact replacement).
- Modify: `CLAUDE.md` (six passages about the current state, by exact replacement).

**Interfaces:**

- Consumes:
  - everything this plan built;
  - Task 5's environment line;
  - the three generated reports;
  - ADR 0002.
- Produces: documentation only. Test counts stay at the previous task's.

- [ ] **Step 1: Write the verification record**

```bash
python3 /tmp/plan5-extract.py docs/verification/layout-1.md
```

Create `docs/verification/layout-1.md`:

````markdown
# layout-1 and the browser diagnostic path: verification record

This record verifies plan B of `specs/structure-aware-canonicalization.md`, the
browser diagnostic path. Plan 5 (`specs/plans/5-structure-aware-canonicalization.md`)
built it. With plan A, whose record is `docs/verification/walker-1.md`, it completes
Stage 3.

## What was verified

| Plan B exit criterion | Evidence |
| --- | --- |
| 1. The extra, the pinned binaries and the setup command; no processing run downloads | The `browser-capture` extra and `uv.lock`; `browser/chrome-for-testing.toml`; `earnings-pipeline browser setup`; `test_a_capture_never_runs_selenium_manager` |
| 2. Calibration, classified, with no gold change | `docs/verification/browser-calibration.md` |
| 3. The network guard | `test_every_request_is_blocked_recorded_and_never_made`, under `isolated/1` and under Fetch interception alone; `test_document_javascript_never_runs` |
| 4. One rendered-text hash | `test_two_captures_have_the_same_text_and_layout_hashes`; the recapture of every committed capture |
| 5. Exact spans or `alignment_failed`; the contract with the real pair | `test_every_layout1_unit_is_an_exact_span_or_an_alignment_failure`; `tests/contracts/test_element_schema_parsers.py` |
| 6. The comparison | `docs/verification/layout-1-comparison.md` |
| 7. ADR 0002 | [GATE: the ADR's path and outcome]; [GATE: on outcome 2 or 3, "the eight fixtures are re-canonicalized under `walker-2` in `tests/fixtures/walker-2/`"; on outcome 1, "nothing is promoted, so nothing is re-canonicalized"] |
| 8. R3.5 final | `docs/verification/R3.5-text-fidelity.md`, with both legs |
| 9. The import scan and the runtime checks | `tests/contracts/test_import_scan.py`; `packages/earnings-ingestion/tests/test_import_boundaries.py` |
| 10. No browser by default; browser checks opt-in, skipping visibly, recording the environment | The documented command, `-m "not live and not browser"`; the browser checks, run with `-m browser -rs` |

## The environment

[GATE: the environment line that Task 5, Step 8 printed.] The eight release captures
share it (`test_every_capture_shares_one_pinned_environment`).

The final browser checks ran on [GATE: the date of Task 15, Step 4]:
[GATE: their result line].

## The pre-registration

- **The freeze.** Commit [GATE: `commit` in
  `expirements/parser-fidelity/layout1-preregistered.toml`, 12 characters] froze 23
  files on [GATE: `frozen_on`], before any release was captured.
- **Post-freeze fixes.** [GATE: "None.", or each `[[changes]]` entry with its file,
  reason and note, followed by "The comparison's numbers are therefore post-hoc."]
- **What the planner saw before the freeze** (plan 5, PB-13):
  - the three development releases, which layout-1 and `anchored-1` were developed
    on;
  - the units, derived from the gold and the frozen walker's output;
  - structural greps of the fixture sources: no stylesheet, no `class` attribute, no
    `<th>`, no bold `font` shorthand, and Becton Dickinson's 1,394 inline
    `display: none`;
  - one load of National Health Investors' `innerText`, twice, for a determinism
    check, with no layout read;
  - the review-gate findings' element types in the committed `walker-1` fixtures;
  - the triggers on `walker-1`'s output: `prose_row` on Southwest Airlines and
    National Health Investors.

## Calibration

[GATE: for each calibrated fixture, from `docs/verification/browser-calibration.md`,
its total and its non-zero kinds.] The copies are calibration observations, not
gold, and no gold changed.

## R3.5's second leg

[GATE: from `docs/verification/R3.5-text-fidelity.md`, the hunks against `innerText`
and against the copies, totalled per category.]

## The comparison and ADR 0002

- **Targeted classes.** [GATE: the report's "Targeted classes" rows, as units lost
  for walker-1, layout-1 and the fallback.]
- **Regressions.** [GATE: each candidate's count, from the Verdict.]
- **The decision.** [GATE: the ADR's path] records outcome [GATE: 1, 2 or 3],
  chosen by the user on [GATE: date], because [GATE: the user's reason].

## The review gate's findings

Plan 4's review gate left these open (`docs/verification/walker-1.md`, "The review
gate"). Each now has a disposition (plan 5, PB-21). This closes the deferred item
"Settle the review gate's open page-artifact and mask findings".

| Finding | Types: walker-1 / layout-1 / fallback | Disposition |
| --- | --- | --- |
| National Health Investors' headline | [GATE: the probe's row] | [GATE: PB-21's entry for the chosen outcome] |
| Becton Dickinson's statement titles | [GATE] | [GATE] |
| End marks | [GATE] | [GATE] |
| Ball's numbered running heads | [GATE] | [GATE] |
| FMC's numbered running heads | [GATE] | [GATE] |
| Becton Dickinson's non-GAAP footnotes, unmasked | [GATE] | A limitation of `boilerplate/1`: a mask change needs `boilerplate/2`, which no stage plans |
| Southwestern Energy's forward-looking continuation, unmasked | [GATE] | A limitation of `boilerplate/1`: at the gate the user declined a rule fitted to one test-set instance |

## Limitations

- **Platform.** The pin covers mac-arm64 only. Anywhere else a capture is
  `unavailable`.
- **The crash database.** Chrome's crash handler keeps its database in
  `~/Library/Application Support/Google/Chrome for Testing/Crashpad`, outside the
  temporary profile (PB-6).
- **layout-1's output.** layout-1 emits no sentences and no list containers.
  `walker-2` adds S1 sentences where it switches, and records `no_list_containers`.
- **Class 3.** It has no units: no fixture carries a stylesheet, so content that a
  stylesheet hides was never measured on a release.
- **Development-set numbers.** The fixtures were Stage 1's test set, and the classes
  were named from its failures (SC2). R12.2's validation set is the independent test.
````

Then:

```bash
grep -n 'GATE:' docs/verification/layout-1.md
```

Expected: no output.

- [ ] **Step 2: Update the harness README**

Apply the replacements below. Each must match exactly once. If one does not match,
stop and ask:

```bash
python3 - <<'EOF'
from pathlib import Path

path = Path("expirements/parser-fidelity/README.md")
text = path.read_text(encoding="utf-8")
edits = [
    (
        "| `r35_report.py` | Stage 3: R3.5's text-fidelity report, plan A's leg | workspace |\n",
        "| `r35_report.py` | Stage 3: R3.5's text-fidelity report, both legs | workspace |\n"
        "| `layout1_units.py` | Stage 3: layout-1's pre-registered targeted units | workspace |\n"
        "| `layout1_report.py` | Stage 3: the pre-registered comparison of walker-1, layout-1 and the fallback | workspace |\n"
        "| `preregister.py` | Stage 3: records and verifies layout-1's freeze (`layout1-preregistered.toml`) | stdlib + git |\n"
        "| `calibrate.py` | Stage 3: innerText against the user's rendered copies | workspace |\n",
    ),
    (
        "Stage 3 (`specs/structure-aware-canonicalization.md`, plan 4) reuses the frozen code\n"
        "without changing it. Its three scripts import `earnings_ingestion`, so they run in the\n"
        "workspace environment with `uv run --locked --all-packages python`.\n",
        "Stage 3 (`specs/structure-aware-canonicalization.md`, plans 4 and 5) reuses the frozen\n"
        "code without changing it. Its scripts import `earnings_ingestion`, so they run in the\n"
        "workspace environment with `uv run --locked --all-packages python`.\n",
    ),
    (
        "  `r35_report.py` writes `docs/verification/R3.5-text-fidelity.md`. Their tests check\n"
        "  that the committed reports are current.\n",
        "  `r35_report.py` writes `docs/verification/R3.5-text-fidelity.md`. Their tests check\n"
        "  that the committed reports are current. R3.5's second leg needs the user's local\n"
        "  rendered copies, so its last section is checked only where they exist.\n"
        "- `layout1_units.py` writes `layout1-units.toml`, the targeted units, from the gold and\n"
        "  the frozen walker's output. `layout1_report.py` writes\n"
        "  `docs/verification/layout-1-comparison.md` from the committed browser captures.\n"
        "- `preregister.py` froze both, with every file that decides the comparison's numbers,\n"
        "  before any release was captured. After `preregister.py record`, a frozen file\n"
        "  changes only to fix a crash or an invalid element set, and `preregister.py amend`\n"
        "  records each such change. A change never alters a type decision, a mapping rule, a\n"
        "  unit, or a metric.\n"
        "- `calibrate.py` writes `docs/verification/browser-calibration.md`. It needs the\n"
        "  user's local copies, and its currency test skips visibly without them.\n",
    ),
]
for old, new in edits:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one match, found {count}: {old[:60]}")
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
print("harness README updated")
EOF
```

Expected: `harness README updated`.

- [ ] **Step 3: Update CLAUDE.md's current state**

Nothing cites `CLAUDE.md` by line number, so it may change length. Apply the
replacements below. Each must match exactly once. If one does not match, because the
user edited that passage, stop and ask rather than guess.

One sentence depends on ADR 0002. Before running the script, replace the `OUTCOME`
string's `[GATE: …]` with the sentence for the chosen outcome:

- **Outcome 1:** "ADR 0002 keeps the capture diagnostic-only: `walker-1` stays the
  canonicalization policy."
- **Outcome 2 or 3:** "ADR 0002 promotes layout-1 as `walker-2`, whose eight
  fixtures are in `tests/fixtures/walker-2/`; `walker-1` and its fixtures are
  unchanged."

```bash
python3 - <<'EOF'
from pathlib import Path

OUTCOME = "[GATE: the sentence for ADR 0002's outcome, from Task 15, Step 3]"
path = Path("CLAUDE.md")
text = path.read_text(encoding="utf-8")
edits = [
    (
        "its working code is the Stage 1 investigation harness in `expirements/parser-fidelity/` and the Stage 2 contracts in `packages/earnings-core`; the other packages are still `hello()` scaffolds, and the rest is instructions.",
        "its working code is the Stage 1 investigation harness in `expirements/parser-fidelity/`, the Stage 2 contracts in `packages/earnings-core`, and Stage 3's canonicalizer and browser diagnostic path in `packages/earnings-ingestion`; `earnings-themes` is still a `hello()` scaffold, and the rest is instructions.",
    ),
    (
        "## Current state: Stages 1 and 2 complete, with Stage 3's plan A; two packages still scaffold",
        "## Current state: Stages 1–3 complete; `earnings-themes` still a scaffold",
    ),
    (
        "Stage 3's plan A (structure-aware canonicalization, plan 4, `specs/structure-aware-canonicalization.md`) is done; plan B, the browser diagnostic path, comes next and completes Stage 3:",
        "Stage 3 (structure-aware canonicalization, `specs/structure-aware-canonicalization.md`) is done: plan A (plan 4) built the canonicalizer, and plan B (plan 5) the browser diagnostic path:",
    ),
    (
        "beside it are generated, and harness tests keep them current.\n"
        "\n"
        "`earnings-themes` and `apps/earnings-pipeline` still contain only `hello()` stubs, as does `earnings-ingestion`'s top-level module.",
        "beside it are generated, and harness tests keep them current.\n"
        "- `packages/earnings-ingestion/src/earnings_ingestion/browser/` captures a saved page in the pinned Chrome for Testing under capture policy `isolated/1`, behind the `browser-capture` extra. Only `browser/selenium_capture.py` imports a browser library, and `tests/contracts/test_import_scan.py` holds every other module to that. `earnings-pipeline browser setup` is the only command that downloads the browser, and browser tests carry the `browser` marker and run only with `-m browser`.\n"
        "- `packages/earnings-ingestion/src/earnings_ingestion/layout/` holds `layout-1`, which reads a capture's rendered layout and maps its elements onto `walker-1`'s text under `anchored-1`; `tests/fixtures/browser/` holds the committed captures. The comparison with `walker-1` was pre-registered (`expirements/parser-fidelity/layout1-preregistered.toml`) before any release was captured, and `docs/verification/layout-1.md` records it. "
        + OUTCOME
        + "\n"
        "\n"
        "`earnings-themes` still contains only a `hello()` stub, as do the top-level modules of `earnings-ingestion` and `apps/earnings-pipeline`; the application's one command is `earnings-pipeline browser setup`.",
    ),
    (
        "fetched pages under `data/raw/` and Stage 1 run outputs under `data/runs/`;",
        "fetched pages under `data/raw/`, and under `data/runs/` Stage 1's run outputs, the user's rendered copies, and the browser capture store;",
    ),
    (
        'pytest path/to/test_x.py::test_name -m "not live and not browser"\n',
        'pytest path/to/test_x.py::test_name -m "not live and not browser"\n'
        "# browser checks, opt-in, once `earnings-pipeline browser setup` has run:\n"
        "uv run --locked --all-packages --extra browser-capture pytest packages apps tests -m browser -rs\n",
    ),
]
for old, new in edits:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one match, found {count}: {old[:60]}")
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
print("CLAUDE.md updated")
EOF
grep -n 'GATE:' CLAUDE.md
```

Expected: `CLAUDE.md updated`, and `grep` prints nothing. Then run
`git diff --stat CLAUDE.md`, and read the diff: six passages change and nothing else.

- [ ] **Step 4: Final verification**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q -rs
uv run --locked --all-packages --extra browser-capture pytest packages apps tests -m browser -q -rs
uv run --locked ruff check . && uv run --locked ruff format --check .
uv lock --check
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
uv run --locked --all-packages python expirements/parser-fidelity/preregister.py verify
git status --short
```

Expected: 

- `674 passed, 22 deselected` on outcome 2 or 3, or `642 passed, 22 deselected` on
  outcome 1;
- `280 passed`, with no skip;
- `22 passed, 674 deselected`, or `22 passed, 642 deselected` on outcome 1;
- `All checks passed!` and `164 files already formatted`, or `157` on outcome 1;
- `Resolved 151 packages`, with exit status 0;
- `freeze verified`;
- `pre-registration verified`;
- a status listing only ` M CLAUDE.md`, ` M expirements/parser-fidelity/README.md`
  and `?? docs/verification/layout-1.md`.

Put the browser checks' result line and today's date into the record's Environment
section (Step 1's slots), if you have not already.

- [ ] **Step 5: Commit**

```bash
git log --oneline -3
git add docs/verification/layout-1.md expirements/parser-fidelity/README.md CLAUDE.md
git commit -m "docs: record Stage 3 plan B in its verification record, the harness README, and CLAUDE.md"
```

---
## Handoffs

Completion's reconcile carries each block below into the named stage's entry, so a
later session finds it without this plan. The spec's "Handoffs to later stages" table
is the source. This section names what plan B actually shipped. Where the answer
depends on ADR 0002, both branches are given.

### To Stage 5 (event corpus and pilot selection)

- **Canonicalization.**
  - On outcome 1: `canonicalize`, as plan 4 left it; no browser is needed.
  - On outcome 2 or 3: `canonicalize_promoted(raw, capture, ...)`. Capture each
    release once through `CaptureStore` and `capture_once`, in the pinned
    environment, and pass the capture in.
  - A `PromotionFailure` is a processing state, and nothing falls back.
- **R3.5 on the pilot releases.** `canonical/fidelity.py` reruns both legs without
  gold. Leg 2 needs a capture of each pilot release.
- **The comparison can be repeated.** `layout1_report.py`'s rules and `preregister.py`
  serve a new pre-registration on the pilot releases, if one is wanted. A new
  pre-registration needs a new record file and new units.

### To Stage 6 (codebook, split, and annotation)

- **ADR 0002 is decided, so annotation may begin.**
- **Gold spans bind** to `walker-1`'s `doc_id`s on outcome 1, or to `walker-2`'s on
  outcome 2 or 3. The canonical text and its hash are the same either way, so a span
  moves between them unchanged.

### To Stage 7 (extraction and verification)

- **The fixtures.** On outcome 1, `tests/fixtures/canonical/`; on outcome 2 or 3,
  `tests/fixtures/walker-2/`.
- **Eligibility.** A `walker-2` document that switched may carry `alignment_failed`
  text typed `other`, which is never narrative. It has no list containers.

### To Stage 10 (headline outputs and evidence views)

- **The renderer.** `earnings_ingestion.browser`'s `BrowserRenderer`, with
  `SeleniumRenderer` behind the `browser-capture` extra, serves V5's target-browser
  checks and the screenshot fallback.
  - Screenshots are stored by content hash with rights `local_only` (PB-8).
  - Never verify a quote from rendered output (B6).
  - Offsets are code points, so Stage 10 converts to UTF-16 at its own highlight
    boundary.
- **The pinned environment.** Chrome for Testing 154.0.8037.57, on mac-arm64, under
  capture policy `isolated/1`.

### To Stage 15 (full DJIA eight-quarter run)

- **On outcome 2 or 3,** every release needs a usable capture in the pinned
  environment before canonicalization: the cost ADR 0002 weighed.
- **On outcome 1,** nothing changes.

### Deferred items that stay open

- **`1-release-parser-fidelity`.** "Time parsers without their imports",
  "Compare exactly if the selection rule is reused" (plan B compared exactly itself,
  PB-14), and "Keep `EDGAR_IDENTITY` out of the lock gate's adapter processes".
- **`3-core-evidence-spine`.** The `VerifiedSpan`, `resolve_pointer`,
  unvalidated-offset, and `Rejection`-subject items stay with Stage 7.

## Completion

After Task 15, run the final whole-branch review. Then:

1. **Plan Completion Protocol** (writing-plans).
   - Run the resolve-before-defer gate. On outcome 1, Task 14's skipped steps are not
     deferred: ADR 0002 decided them.
   - Mark up this plan: tick the steps, add `> Deviation:` and `> Skipped:` notes, and
     add the status header.
2. **Rollout stamp.** Append a blank line and these two lines to the end of
   `specs/structure-aware-canonicalization.md`, putting the completion date in place
   of `YYYY-MM-DD`:

   ```text
   > Stage 3: COMPLETE (YYYY-MM-DD) — implemented by plans 4 (specs/plans/completed/4-structure-aware-canonicalization-plan-a.md) and 5 (specs/plans/completed/5-structure-aware-canonicalization.md).
   > Next: resume the roadmap.
   ```

   This is the spec's only edit apart from the retirement's status line.
3. **Deferred items.** In `specs/deferred_items.md`:
   - **Tick two items**, ending each with ` → done in plan 5`:
     - under `## 3-core-evidence-spine — 2026-09-25`: "Check import boundaries
       statically as well" (`tests/contracts/test_import_scan.py`);
     - under `## 4-structure-aware-canonicalization-plan-a — 2026-09-25`: "Settle the
       review gate's open page-artifact and mask findings" (see
       `docs/verification/layout-1.md`, "The review gate's findings").
   - **Append this plan's own deferred items,** if any, under a
     `## 5-structure-aware-canonicalization — YYYY-MM-DD` heading with the completion
     date.
   - **Commit** steps 1–3 together as
     `docs(specs): mark up plan 5, record Stage 3's rollout, and tick deferred items`.
4. **Backlog triage.** Run
   `uv run --no-project --python 3.13 python ~/.claude/skills/writing-plans/scripts/deferred_stats.py`
   and report its summary line. Present the triage rubric if its thresholds trip.
5. **Retire the plan and the spec together.** This plan is the spec's last (PB-1).
   - Move both files:

     ```bash
     git mv specs/plans/5-structure-aware-canonicalization.md specs/plans/completed/
     git mv specs/structure-aware-canonicalization.md specs/completed/
     ```

   - Mark the spec complete at its top. Insert this line, with the date, after its
     title line and a blank line:
     `**Status: COMPLETE (YYYY-MM-DD)** — Stage 3; implemented by plans 4 and 5; retired to specs/completed/.`
   - Neither file holds a relative Markdown link, so nothing inside them needs
     re-pointing.
   - Five live files cite the old paths: `CLAUDE.md`,
     `expirements/parser-fidelity/README.md`, `docs/verification/walker-1.md` (line
     3), `docs/verification/layout-1.md`, and ADR 0002. Re-point them, and then check
     that none is left:

     ```bash
     python3 - <<'EOF'
     from pathlib import Path

     moves = {
         "`specs/structure-aware-canonicalization.md`": "`specs/completed/structure-aware-canonicalization.md`",
         "`specs/plans/5-structure-aware-canonicalization.md`": "`specs/plans/completed/5-structure-aware-canonicalization.md`",
     }
     names = [
         "CLAUDE.md",
         "expirements/parser-fidelity/README.md",
         "docs/verification/walker-1.md",
         "docs/verification/layout-1.md",
         *sorted(str(p) for p in Path("docs/adr").glob("0002-*.md")),
     ]
     for name in names:
         path = Path(name)
         text = path.read_text(encoding="utf-8")
         for old, new in moves.items():
             text = text.replace(old, new)
         path.write_text(text, encoding="utf-8")
     print("re-pointed", len(names), "files")
     EOF
     git grep -n "specs/structure-aware-canonicalization.md\|specs/plans/5-structure-aware" -- . ':!specs/plans/completed' ':!specs/completed'
     ```

     Expected: `re-pointed 5 files`, then no `git grep` output. The one edit to
     `walker-1.md` is this path. Completed plans keep their paths as history.
   - Commit as `chore(specs): retire plan 5 and the Stage 3 spec`.
6. **Roadmap.** Run derive-roadmap's reconcile step on
   `specs/evidence-linked-theme-extraction-roadmap.md`. The spec's Stage 3 stamp is
   authoritative. The reconcile:
   - ticks Stage 3;
   - adds the spec's plan B exit criteria to Stage 3's Exit;
   - carries the Handoffs above into Stages 5, 6, 7, 10 and 15;
   - re-validates every unticked stage against what shipped.

   Commit as `docs(roadmap): tick Stage 3 and reconcile the later stages`.
7. **Integrate** with finishing-a-development-branch. Open a pull request from
   `stage-3-browser-diagnostic-path` to `main`, as Stages 1–3 did. The branch was
   unpushed at planning time, so this is its first push. The repository is public.
8. **Report.**
   - State the commands actually run and their results.
   - State ADR 0002's outcome and the user's reason.
   - State that no model was called.
   - State that the browser checks ran, with their environment line and result, and
     that no live test ran.
