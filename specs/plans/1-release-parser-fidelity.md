# Release Parser Fidelity (Stage 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 1 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

**Goal:** Build and run the Stage 1 investigation in `specs/release-parser-fidelity.md`. It
produces the eight-fixture release corpus with hand-marked gold, the source register, the
parser-fidelity harness, the V1 and V2 records, and ADR 0001, which names the base parser
for release canonicalization.

**Architecture:** Everything executable lives in `expirements/parser-fidelity/`, a flat
directory of small modules, and no package imports it.

- **Standard-library modules** (paths, decoding, matching spaces, validator, scorer,
  selection rule) run in the workspace environment.
- **Third-party scripts** (fetcher users, the candidate adapters, the lock gate, V1) are
  PEP 723 scripts with committed script locks.
- **Candidates** each run in their own locked environment, behind a network guard,
  twice per release. They emit canonical JSON dumps.
- **Scoring** matches the user's hand-marked text anchors exactly in two matching
  spaces.
- **Selection** is a fixed, pre-registered rule that reads the scores and the gates.

**Tech Stack:**

- Python 3.14 (uv-managed) and uv 0.12.15: PEP 723 scripts and `uv lock --script`.
- lxml 6.1.3, beautifulsoup4 4.15.0, and httpx 0.28.1.
- edgartools 5.58.0, and sec-parser 0.58.1 on Python 3.13.
- packaging 26.3.
- pytest 9.1.1 and Ruff 0.16.8, from the workspace `dev` group.
- Standard library: `tomllib`, `html.parser`, `unicodedata`, and `annotationlib`.

## Global Constraints

Every task's requirements include these. Locators follow the spec: `A §n` is
`AGENTS.md`, `Rn`/`Vn` are `specs/evidence-linked-theme-extraction.md`, and `F1`–`F8`
are the stage spec's decisions.

- **No package code.** "The stage ships no package code." Nothing under `packages/`
  changes, and `uv.lock` is unchanged. Candidates run in environments pinned by their
  own script locks.
- **No imports from the harness.** "Nothing under `expirements/` is imported by a
  package."
- **Candidate pins.**
  - The edgartools adapter pins `edgartools==5.58.0`.
  - The walker and the control pin lxml and beautifulsoup4 to their `uv.lock`
    versions: `lxml==6.1.3` and `beautifulsoup4==4.15.0`.
  - sec-parser is pinned at `sec-parser==0.58.1`.
- **Fixtures.** Each is a full release exhibit, committed byte-for-byte, "each at most
  1 MiB" (F1). `.gitattributes` holds
  `tests/fixtures/releases/*/source.html -text`.
- **Fixture IDs.** A `<fixture_id>` is "the accession number plus the exhibit type as
  filed, lowercased with dots replaced by hyphens", for example
  `0001234567-25-000123_ex-99-1`.
- **CIK.** "CIK as a zero-padded 10-character string (A §264)."
- **Pilot split.** Every manifest entry has `pilot_split = "train_or_exclude"` and
  `source_id = "sec-edgar"`.
- **Live-fetch policy.** It applies to "every network call in Stage 1".
  - `EDGAR_IDENTITY` must hold "a descriptive User-Agent with a real contact". The
    user sets it outside Git, and it is never written to a file, log, or record.
  - "Only one live process runs at a time, at no more than 2 requests/second."
  - Request starts are "at least 0.5 s apart".
  - "Each run stops at 500 requests by default (configurable) and reports its request
    count."
  - Every call has explicit timeouts and bounded retries with exponential backoff and
    jitter. `Retry-After` is honored.
  - "A 403 that persists stops the run and is reported. The identity is never
    rotated."
  - "Only 200 responses with the expected content type are saved. An SEC block or
    rate-limit page is a failure."
- **Gold.** "Gold is marked from a browser's rendering of `source.html`, never from any
  candidate's output. No candidate output is shown as a pre-draft."
- **Freeze.** Adapter, control, and walker sources are frozen "before their first run
  on any fixture". Afterwards, a change is allowed "only to fix a crash or a
  network-guard trip caused by adapter code. It may never alter a type mapping or a
  walker rule."
- **Selection rule.** "The rule is fixed before any fixture is scored (F6, F7)."
- **Workspace.**
  - `requires-python = ">=3.14"` and uv 0.12.15.
  - The root `pyproject.toml` stays a virtual workspace root with no `[project]`
    table.
  - Do not edit `AGENTS.md`: other files cite it by line number.
  - The `.gitignore` credentials block stays last.
- **Public repository.** `origin` is public, so anything committed is public.
- **Lint.** `uv run --locked ruff check .` and `uv run --locked ruff format --check .`
  pass. Ruff 0.16's default rule set includes bugbear, comprehensions, `DTZ`,
  `BLE001`, `SIM`, and isort.

## Plan decisions

The spec does not make these choices. The plan makes them, and the user can overturn
any of them before execution. Each is implemented in the named task and recorded in V2.

**P1 — One shared decoding** (Tasks 1, 11).

- **Decision.** Every consumer decodes the saved bytes once, with
  `pf_decode.decode_html_bytes`, and every candidate receives the same `str`. That
  covers the class tests, the validator, the scorer, and every adapter. The rule is:
  1. byte-order mark;
  2. a `<meta>` charset in the first 1024 bytes, with WHATWG label mapping;
  3. UTF-8 if the bytes are valid UTF-8;
  4. windows-1252.
- **Why.** V2 measures structure; charset handling belongs to canonicalization (R3.1,
  R3.5). The rule mirrors a browser opening a local file, which is what the annotator
  sees. The annotator checks `document.characterSet` for each fixture. edgartools' own
  press-release path decodes with UTF-8 and `errors="replace"`
  (`edgar/company_reports/press_release.py`); V2 records that as a Stage 3 finding.

**P2 — sec-parser runs on Python 3.13** (Task 12).

- **Decision.** The sec-parser adapter declares `requires-python = ">=3.13,<3.14"`.
- **Why.** sec-parser 0.58.1 requires `lxml<6`. On 2026-09-22,
  `uv pip compile --python-version 3.14 --only-binary lxml` found no wheel for it,
  while 3.13 resolves lxml 5.4.0 and pandas 2.3.3. A source build would compile
  against this machine's libxml2 and leave the environment unreproducible. The spec
  allows an older `requires-python`.

**P3 — The edgartools parse path** (Task 12).

- **Decision.** The edgartools candidate is `edgar.documents.parse_html(html)` with
  the default `ParserConfig`, the call edgartools' own `PressRelease.text()` makes.
  The legacy `edgar.files.html` parser is not measured.
- **Why.** 5.58.0 deprecates `edgar.files` and removes it in 6.0
  (`edgar/files/_deprecation.py`).

**P4 — The dump format** (Task 11).

- **Decision.**
  - Containers are `other` elements with empty text.
  - `parent` is an index into the dump.
  - No library identifier is ever written.
  - JSON is canonical: sorted keys, fixed separators, and `ensure_ascii=False`.
  - Timing and status go to a separate sidecar.
- **Why.** Joining element texts must not duplicate content. edgartools node IDs are
  fresh `uuid4()` values, which would fail the determinism gate for a reason that has
  nothing to do with parsing.

**P5 — Tie-break (a)** (Task 18).

- **Decision.** First compare whether pandas is in the added runtime tree; a candidate
  without it wins. Then compare the count of added runtime distributions. That count is
  the `earnings-ingestion` dependency closure in the scratch lock minus the one in
  `uv.lock`, following requested extras and ignoring markers.
- **Why.** This makes "fewer runtime dependencies … (pandas anywhere in the added tree
  counts against a candidate)" checkable.

**P6 — A "persistent" 403** (Task 2).

- **Decision.** A 403 persists when an attempt and its retry after backoff both return
  403.
- **Why.** R1.3 requires a stop but sets no count.

**P7 — Cell-to-header association**, a diagnostic only (Task 17).

- **Decision.** One geometric rule applies to every candidate that exposes a grid:
  - colspan and rowspan are expanded;
  - the row header is the first non-empty cell to the cell's left;
  - the column header is the non-empty header-row cells overlapping the cell's
    columns, read top to bottom;
  - a match needs the gold header text, in the primary space, inside the candidate's
    header text.
- **Why.** The spec names the diagnostic but not the rule.

**P8 — Discovery sources and defaults** (Tasks 5, 6).

- **Decision.**
  - **Sources.** Quarterly `master.idx` files are the sampling frame across years and
    filer agents. Submissions JSON supplies each filing's Item list, which is also the
    manifest's `items`. The filing index page supplies the exhibit type and
    description.
  - **Defaults.** Years 2005, 2008, 2011, 2014, 2017, 2020, 2023, and 2025; eight
    candidates per year; seed 20260922; quarter `1 + (seed + year) % 4`.
  - **Exclusions.** The shortlist drops exhibits over 1 MiB and exhibits with under 500
    visible characters of native text. An `.htm` that only wraps images needs OCR
    (R4.3), which the spec excludes.
- **Why.** This uses both sources the spec names. 2005 is the first full year of
  Item 2.02.

**P9 — Walker rules** (Tasks 13, 14).

- **Decision.** The rules are fixed in `walker-rules.md` and approved by the user
  before development. Development may correct how a rule is implemented, but it never
  adds or retunes a rule. Uncovered patterns go under Known gaps.
- **Why.** The spec says the rules are "written down before development begins".

**P10 — Harness tests** (all tasks).

- **Decision.** Tests sit beside the modules and run with
  `pytest --import-mode=prepend` in the workspace environment. No pytest configuration
  is added.
- **Why.** Stage 2 owns pytest configuration.

**P11 — The order of fixture runs** (Tasks 15, 19).

- **Decision.** No candidate parses a fixture until the freeze verifies and all gold
  validates. That covers smoke runs and the lock gate's parse step too, and
  `run_candidates.py fixtures` enforces it.
- **Why.** No candidate output can reach the annotator, and the freeze precedes
  "their first run on any fixture".

**P12 — Class-test parameters** (Task 4).

- **Decision.**
  - **Page-break styling** is `page-break-before/after: always|left|right` or
    `break-before/after: page`.
  - **A bare page-number block** is a `p`, `div`, `center`, `td`, `th`, `li`, or
    `h1`–`h6` element outside data tables whose whole text matches
    `(Page)? dashes digits dashes`.
  - **Words** are whitespace-separated tokens.
  - **A cell's own text** excludes nested tables.
- **Why.** The spec defines the tests but not these details. The parameters only sort
  fixtures and are not quality thresholds.

**P13 — Anchor length** (Task 8).

- **Decision.** Words are whitespace-separated tokens, and characters are the raw
  anchor's length. A short anchor is allowed only on a block with no `end`.
- **Why.** This is the checkable form of "or the whole block if it is shorter".

**P14 — Footnote merging** (Task 17).

- **Decision.** It counts every found anchor of a gold heading, paragraph, or list
  item, whether or not that block is fully found.
- **Why.** The spec's wording is "…an element also holding an anchor of…".

**P15 — Undefined metrics and ties** (Task 18).

- **Decision.** A candidate whose metric has no denominator in any class stays in at
  that step. A tie that survives every tie-break returns the decision to the user.
- **Why.** The spec leaves both cases open.

**P16 — Runtime** (Task 11).

- **Decision.** Runtime is the in-process parse time, excluding interpreter start-up
  and imports.
- **Why.** It is comparable across candidates.

**P17 — One live process** (Task 2).

- **Decision.** An exclusive lock on `data/runs/parser-fidelity/live.lock` enforces
  it.
- **Why.** That makes the rule enforceable.

**P18 — Register quotes** (Task 3).

- **Decision.** The register's quotes, URLs, and dates are copied from pages fetched
  by `fetch_policy_pages.py`, and `verify` rejects any mismatch.
- **Why.** The plan must not assert the SEC's wording from memory.

**P19 — V1 rate limiting** (Task 16).

- **Decision.** The V1 run sets `EDGAR_RATE_LIMIT_PER_SEC=2`, edgartools' own
  mechanism, which it reads at import. It also routes every httpx transport request
  through the fetcher's throttle.
- **Why.** edgartools' in-memory bucket allows back-to-back requests and counts
  nothing, but the spec requires a request count.

A planning-time probe (2026-09-22, in a `git archive` scratch copy; the repository was
untouched) matched the spec's expectation. The lock gate itself remains authoritative
at Task 19.

- Adding `edgartools==5.58.0` to `earnings-ingestion` resolves, lowers no version, and
  adds 29 runtime distributions, pandas among them.
- Adding `sec-parser==0.58.1` lowers lxml 6.1.3→5.4.0, pandas 3.0.6→2.3.3,
  tabulate 0.10.0→0.9.0, and xxhash 4.0.1→3.8.1.

## Human gates

| Gate | Task | Who | What it unblocks |
| --- | --- | --- | --- |
| Identity | before Task 3 | user | Sets `EDGAR_IDENTITY` in their shell profile, outside the repository. Every live step needs it. |
| A — fixtures | Task 6 | user | Approves eight fixtures and two or three development releases in `approval.toml`. |
| B — gold | Task 10 | user | Marks gold for all eight fixtures, an estimated 1–2.5 hours each. |
| C — walker rules | Task 13 | user | Approves `walker-rules.md` before any walker development. |
| D — decision | Task 21 | user | Accepts ADR 0001, and decides any outcome the rule returns to them. |

While gate B is open, the agent works through Tasks 11–18. Task 16 includes the live V1
run. Task 19 waits for gate B.

The gate steps run in the controller session with the user, never in a subagent:

- the identity check before Task 3;
- Task 6 Step 4;
- Task 10;
- Task 13 Step 2;
- Task 21.

Task 10 stays open while Tasks 11–18 proceed.

## File map

| Path | Responsibility | Task |
| --- | --- | --- |
| `expirements/parser-fidelity/README.md` | Harness map, commands, policies | 1 |
| `…/pf_paths.py` | Repository paths, `fixture_id()` | 1 |
| `…/pf_decode.py` | Browser-equivalent decoding (P1) | 1 |
| `…/pf_space.py` | `primary_space` (m), `fallback_space` (m2), `find_all` | 1 |
| `…/pf_text.py` | `build_space_text` (position-mapped spaces), `extract_document_text` (validator text) | 1 |
| `…/pf_fetch.py` | Live-fetch client and policy | 2 |
| `…/fetch_policy_pages.py` (+ `.lock`) | Fetches and verifies the register's SEC quotes | 3 |
| `docs/source-register.toml` | The A §242 source register, entry `sec-edgar` | 3 |
| `…/pf_classes.py` | Class tests and data-table helpers | 4 |
| `…/discover.py` (+ `.lock`) | Discovery and shortlist | 5 |
| `…/approval.toml` | The user's fixture and dev-set approval | 6 |
| `…/pf_toml.py` | Minimal TOML writer | 7 |
| `…/promote_fixtures.py` | Copies approved exhibits into the corpus; writes the manifest | 7 |
| `.gitattributes` | `-text` on fixture sources | 7 |
| `tests/fixtures/releases/<id>/source.html`, `manifest.toml` | The corpus | 7 |
| `…/validate_gold.py` | Gold validator | 8 |
| `…/check_fixtures.py` | Harness check (exit criterion 4) | 9 |
| `tests/fixtures/releases/<id>/gold.toml`, `…/gold-notes.md` | The user's gold and marking notes | 10 |
| `…/pf_dump.py` | Dump schema, network guard, adapter entry point | 11 |
| `…/control.py`, `…/adapter_edgartools.py`, `…/adapter_secparser.py` (+ `.lock`s) | Control and library adapters | 12 |
| `…/walker-rules.md` | Walker rules W0–W16 | 13 |
| `…/walker.py` (+ `.lock`) | The bespoke walker | 14 |
| `…/run_candidates.py`, `…/freeze.py`, `…/FROZEN.toml` | Runner, gates, freeze | 15 |
| `…/v1_return_types.py` (+ `.lock`), `docs/verification/V1-edgartools-return-types.md` | V1 | 16 |
| `…/score.py` | Metrics, diagnostics, residuals | 17 |
| `…/lock_gate.py` (+ `.lock`), `…/select_parser.py` | Lock gate and selection rule | 18 |
| `docs/verification/V2-parser-fidelity.md`, `docs/adr/0001-<slug>.md` | V2 record and ADR | 20 |
| `CLAUDE.md` ("Current state") | Refreshed on completion | 22 |

Every `…/` is `expirements/parser-fidelity/`. Every test file `test_<module>.py` sits
beside its module.

Two commands recur:

```bash
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Before each commit, run `uv run --locked ruff format expirements/parser-fidelity` and
then the lint command. The code below already passes both.

Outputs:

- Generated outputs go to gitignored `data/raw/` (fetched bytes) and
  `data/runs/parser-fidelity/` (dumps, gates, scores).
- Never `git add` anything under `data/`.
- Before each commit, `git status --short` must show only the files that task names.
  `README.md` may carry the user's own uncommitted edits; leave them alone.

---

### Task 1: Harness foundation — paths, decoding, matching spaces, validator text

**Files:**
- Create: `expirements/parser-fidelity/README.md`
- Create: `expirements/parser-fidelity/pf_paths.py`
- Create: `expirements/parser-fidelity/pf_decode.py`
- Create: `expirements/parser-fidelity/pf_space.py`
- Create: `expirements/parser-fidelity/pf_text.py`
- Test: `expirements/parser-fidelity/test_pf_decode.py`, `expirements/parser-fidelity/test_pf_text.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `pf_paths`: `HARNESS`, `REPO_ROOT`, `FIXTURES`, `MANIFEST`, `REGISTER`,
    `DATA_RAW`, `DISCOVERY`, `DEVSET`, `RUNS`, `EDGAR_HOME`, `LIVE_LOCK` (all
    `Path`), `MAX_FIXTURE_BYTES = 1048576`, and
    `fixture_id(accession: str, exhibit_type: str) -> str`.
  - `pf_decode`: `decode_html_bytes(raw: bytes) -> DecodedHtml`, where `DecodedHtml`
    is a frozen dataclass of `text: str`, `encoding: str`, `basis: str`, and
    `ascii_only: bool`. Also `decode_windows_1252(raw: bytes) -> str`.
  - `pf_space`: `primary_space(s: str) -> str` (the spec's m),
    `fallback_space(s: str) -> str` (m2), and
    `find_all(haystack: str, needle: str) -> list[int]`, which counts overlapping
    occurrences and raises on an empty needle.
  - `pf_text`: `SpaceText(text: str, origins: tuple[tuple[int, int], ...])`,
    `build_space_text(pieces: Sequence[str], space: "primary" | "fallback") -> SpaceText`,
    and `extract_document_text(html: str, joiner: str = "") -> str`.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_pf_decode.py`:

```python
import codecs

import pytest
from pf_decode import decode_html_bytes
from pf_paths import fixture_id


def test_utf8_bom_wins_and_is_stripped():
    decoded = decode_html_bytes(codecs.BOM_UTF8 + "<p>caf\xe9</p>".encode())
    assert (decoded.text, decoded.encoding, decoded.basis) == (
        "<p>caf\xe9</p>",
        "UTF-8",
        "bom",
    )


def test_meta_latin1_label_means_windows_1252():
    raw = b'<html><head><meta charset="iso-8859-1"></head><body>\x93quoted\x94 \x92</body></html>'
    decoded = decode_html_bytes(raw)
    assert decoded.encoding == "windows-1252"
    assert decoded.basis == "meta"
    assert "\u201cquoted\u201d \u2019" in decoded.text


def test_meta_http_equiv_utf8():
    raw = '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><p>\u2014</p>'.encode()
    decoded = decode_html_bytes(raw)
    assert (decoded.encoding, decoded.basis) == ("UTF-8", "meta")
    assert "\u2014" in decoded.text


def test_meta_beyond_prescan_window_is_ignored():
    raw = b"<!--" + b" " * 1100 + b'--><meta charset="iso-8859-1"><p>\xc3\xa9</p>'
    decoded = decode_html_bytes(raw)
    assert (decoded.encoding, decoded.basis) == ("UTF-8", "valid-utf-8")
    assert "\xe9" in decoded.text


def test_unlabeled_invalid_utf8_falls_back_to_windows_1252():
    decoded = decode_html_bytes(b"<p>\x93Hi\x94 \x81</p>")
    assert (decoded.encoding, decoded.basis) == ("windows-1252", "default")
    assert decoded.text == "<p>\u201cHi\u201d \x81</p>"


def test_unknown_label_is_ignored():
    decoded = decode_html_bytes(b'<meta charset="no-such-charset"><p>plain</p>')
    assert decoded.basis == "valid-utf-8"
    assert decoded.ascii_only is True


def test_fixture_id_lowercases_and_replaces_dots():
    assert (
        fixture_id("0001234567-25-000123", "EX-99.1") == "0001234567-25-000123_ex-99-1"
    )


@pytest.mark.parametrize(
    ("accession", "exhibit"),
    [("123-25-1", "EX-99.1"), ("0001234567-25-000123", "EX 99(a)")],
)
def test_fixture_id_rejects_bad_input(accession, exhibit):
    with pytest.raises(ValueError):
        fixture_id(accession, exhibit)
```

`expirements/parser-fidelity/test_pf_text.py`:

```python
import pytest
from pf_space import fallback_space, find_all, primary_space
from pf_text import build_space_text, extract_document_text


def test_primary_space_deletes_whitespace_and_format_characters_and_keeps_case():
    assert primary_space("Net\xa0Sales \xadrose\u200b 5%") == "NetSalesrose5%"


def test_primary_space_applies_nfkc():
    assert primary_space("\ufb01scal \xbd") == "fiscal1\u20442"


def test_fallback_space_keeps_only_letters_and_digits_without_accents():
    assert (
        fallback_space("Soci\xe9t\xe9 \u201cGr\xe9n\u201d \u2014 Q3\u20192025")
        == "SocieteGrenQ32025"
    )


def test_find_all_counts_overlapping_occurrences():
    assert find_all("aaa", "aa") == [0, 1]
    with pytest.raises(ValueError):
        find_all("abc", "")


def test_build_space_text_maps_every_character_back_to_its_piece_and_offset():
    joined = build_space_text(["A b", "", "cd"], "primary")
    assert joined.text == "Abcd"
    assert joined.origins == ((0, 0), (0, 2), (2, 0), (2, 1))


def test_build_space_text_keeps_combining_marks_with_their_base():
    joined = build_space_text(["xe\u0301y"], "primary")
    assert joined.text == "x\xe9y"
    assert joined.origins == ((0, 0), (0, 1), (0, 3))


def test_build_space_text_fallback_space_maps_expansions():
    joined = build_space_text(["\xe9-\ufb01"], "fallback")
    assert joined.text == "efi"
    assert joined.origins == ((0, 0), (0, 2), (0, 2))


def test_extract_document_text_skips_head_script_and_style():
    html = (
        "<html><head><title>T</title><style>p{}</style></head>"
        "<body><p>One &amp; two</p><script>var x = 1;</script><p>three</p></body></html>"
    )
    assert extract_document_text(html) == "One & twothree"


def test_extract_document_text_recovers_from_an_unclosed_head():
    assert (
        extract_document_text("<head><title>T</title><p>Body text</p>") == "Body text"
    )
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_pf_decode.py expirements/parser-fidelity/test_pf_text.py --import-mode=prepend -q`
Expected: 2 collection errors, `ModuleNotFoundError: No module named 'pf_decode'` and `No module named 'pf_space'`.

- [x] **Step 3: Write the implementation**

`expirements/parser-fidelity/pf_paths.py`:

```python
"""Repository paths and fixture identifiers for the Stage 1 parser-fidelity harness.

Nothing here touches the filesystem at import time; the constants are plain paths.
"""

from __future__ import annotations

import re
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
REPO_ROOT = HARNESS.parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "releases"
MANIFEST = FIXTURES / "manifest.toml"
REGISTER = REPO_ROOT / "docs" / "source-register.toml"
DATA_RAW = REPO_ROOT / "data" / "raw"
DISCOVERY = DATA_RAW / "discovery"
DEVSET = DATA_RAW / "devset"
RUNS = REPO_ROOT / "data" / "runs" / "parser-fidelity"
EDGAR_HOME = RUNS / "edgar-home"
LIVE_LOCK = RUNS / "live.lock"

MAX_FIXTURE_BYTES = 1024 * 1024  # F1: each fixture is at most 1 MiB

_ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_FIXTURE_ID = re.compile(r"^\d{10}-\d{2}-\d{6}_[a-z0-9-]+$")


def fixture_id(accession: str, exhibit_type: str) -> str:
    """Accession plus the exhibit type as filed, lowercased, dots replaced by hyphens."""
    if not _ACCESSION.match(accession):
        raise ValueError(f"not an accession number: {accession!r}")
    candidate = f"{accession}_{exhibit_type.strip().lower().replace('.', '-')}"
    if not _FIXTURE_ID.match(candidate):
        raise ValueError(
            f"exhibit type {exhibit_type!r} does not give a valid fixture id"
        )
    return candidate
```

`expirements/parser-fidelity/pf_decode.py`:

```python
"""Browser-equivalent decoding of saved release bytes.

Every consumer of a fixture's text -- the class tests, the gold validator, the
scorer, and every candidate adapter -- decodes the saved bytes with this one
function, so V2 compares structure rather than charset guessing. The rule follows
what a browser does with a local file, where no HTTP header is available:

1. a byte-order mark;
2. a ``<meta>`` charset declared in the first 1024 bytes (WHATWG label mapping:
   ``iso-8859-1`` and ``us-ascii`` mean windows-1252, a UTF-16 label means UTF-8);
3. UTF-8, when the bytes are valid UTF-8;
4. windows-1252 otherwise.

The annotator confirms per fixture that the browser agreed (``document.characterSet``).
"""

from __future__ import annotations

import codecs
import re
from dataclasses import dataclass

PRESCAN_BYTES = 1024

_META_CHARSET = re.compile(
    rb"""<meta[^>]*?charset\s*=\s*["']?\s*([A-Za-z0-9._:\-]+)""", re.IGNORECASE
)
_WINDOWS_1252_LABELS = frozenset(
    {
        "ansi_x3.4-1968",
        "ascii",
        "cp1252",
        "cp819",
        "csisolatin1",
        "ibm819",
        "iso-8859-1",
        "iso-ir-100",
        "iso8859-1",
        "iso88591",
        "iso_8859-1",
        "iso_8859-1:1987",
        "l1",
        "latin1",
        "us-ascii",
        "windows-1252",
        "x-cp1252",
    }
)
_UTF8_LABELS = frozenset(
    {
        "unicode-1-1-utf-8",
        "unicode11utf8",
        "unicode20utf8",
        "utf-8",
        "utf8",
        "x-unicode20utf8",
        "utf-16",
        "utf-16le",
        "utf-16be",
        "unicode",
        "ucs-2",
        "csunicode",
        "iso-10646-ucs-2",
        "unicodefeff",
        "unicodefffe",
    }
)
_BOMS = (
    (codecs.BOM_UTF8, "utf-8", "UTF-8"),
    (codecs.BOM_UTF16_LE, "utf-16-le", "UTF-16LE"),
    (codecs.BOM_UTF16_BE, "utf-16-be", "UTF-16BE"),
)
# WHATWG windows-1252 is cp1252 plus five bytes Python leaves undefined, which map
# to the C1 controls of the same value.
_CP1252_UNDEFINED = frozenset({0x81, 0x8D, 0x8F, 0x90, 0x9D})
_LATIN1_TO_WINDOWS_1252 = {
    code: bytes([code]).decode("cp1252")
    for code in range(0x80, 0xA0)
    if code not in _CP1252_UNDEFINED
}


@dataclass(frozen=True)
class DecodedHtml:
    text: str
    encoding: str  # the name a browser reports, e.g. "UTF-8" or "windows-1252"
    basis: str  # "bom", "meta", "valid-utf-8", or "default"
    ascii_only: bool  # True when every byte is ASCII, so every encoding agrees


def decode_html_bytes(raw: bytes) -> DecodedHtml:
    ascii_only = raw.isascii()
    for bom, codec, name in _BOMS:
        if raw.startswith(bom):
            text = raw[len(bom) :].decode(codec, errors="replace")
            return DecodedHtml(text, name, "bom", ascii_only)
    match = _META_CHARSET.search(raw[:PRESCAN_BYTES])
    if match is not None:
        decoded = _decode_label(
            raw, match.group(1).decode("ascii").strip().lower(), ascii_only
        )
        if decoded is not None:
            return decoded
    try:
        return DecodedHtml(raw.decode("utf-8"), "UTF-8", "valid-utf-8", ascii_only)
    except UnicodeDecodeError:
        return DecodedHtml(
            decode_windows_1252(raw), "windows-1252", "default", ascii_only
        )


def decode_windows_1252(raw: bytes) -> str:
    return raw.decode("latin-1").translate(_LATIN1_TO_WINDOWS_1252)


def _decode_label(raw: bytes, label: str, ascii_only: bool) -> DecodedHtml | None:
    if label in _WINDOWS_1252_LABELS:
        return DecodedHtml(decode_windows_1252(raw), "windows-1252", "meta", ascii_only)
    if label in _UTF8_LABELS:
        return DecodedHtml(
            raw.decode("utf-8", errors="replace"), "UTF-8", "meta", ascii_only
        )
    try:
        info = codecs.lookup(label)
    except LookupError:
        return None  # a browser ignores an unknown label too
    return DecodedHtml(
        raw.decode(info.name, errors="replace"), info.name, "meta", ascii_only
    )
```

`expirements/parser-fidelity/pf_space.py`:

```python
"""The two matching spaces for gold anchors (spec: Gold annotation > Matching space).

``primary_space`` is the spec's m(s); ``fallback_space`` is its m2(s). All Stage 1
matching is exact substring search in one of these spaces; nothing is fuzzy.
"""

from __future__ import annotations

import unicodedata


def primary_space(s: str) -> str:
    """m(s): NFKC, then delete whitespace (``str.isspace``) and format characters (Cf)."""
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKC", s)
        if not ch.isspace() and unicodedata.category(ch) != "Cf"
    )


def fallback_space(s: str) -> str:
    """m2(s): NFKD, then keep only letters and digits (L*, N*), which drops combining marks."""
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKD", s)
        if unicodedata.category(ch)[0] in "LN"
    )


def find_all(haystack: str, needle: str) -> list[int]:
    """Start offsets of every occurrence of ``needle``, overlapping occurrences included."""
    if not needle:
        raise ValueError("cannot search for an empty string")
    hits: list[int] = []
    start = haystack.find(needle)
    while start != -1:
        hits.append(start)
        start = haystack.find(needle, start + 1)
    return hits
```

`expirements/parser-fidelity/pf_text.py`:

```python
"""Position-mapped matching-space text, and the validator's independent document text.

``build_space_text`` joins a dump's element texts in one matching space and remembers,
for every character of the result, which element and which offset it came from, so
the scorer can compare positions as (element index, offset within the element).

``extract_document_text`` is the gold validator's own extraction: the standard
library's ``html.parser``, independent of every candidate.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Literal

from pf_space import fallback_space, primary_space

Space = Literal["primary", "fallback"]
_SPACES: dict[str, Callable[[str], str]] = {
    "primary": primary_space,
    "fallback": fallback_space,
}


@dataclass(frozen=True)
class SpaceText:
    text: str
    origins: tuple[
        tuple[int, int], ...
    ]  # per character: (piece index, offset in piece)


def build_space_text(pieces: Sequence[str], space: Space) -> SpaceText:
    to_space = _SPACES[space]
    chars: list[str] = []
    origins: list[tuple[int, int]] = []
    for index, piece in enumerate(pieces):
        for offset, form in _map_piece(piece, to_space):
            chars.append(form)
            origins.extend((index, offset) for _ in form)
    return SpaceText("".join(chars), tuple(origins))


def _clusters(piece: str) -> Iterator[tuple[int, str]]:
    """Split before every character with canonical combining class 0."""
    start = 0
    for index in range(1, len(piece) + 1):
        if index == len(piece) or unicodedata.combining(piece[index]) == 0:
            yield start, piece[start:index]
            start = index


def _map_piece(piece: str, to_space: Callable[[str], str]) -> list[tuple[int, str]]:
    mapped = [(offset, to_space(cluster)) for offset, cluster in _clusters(piece)]
    whole = to_space(piece)
    if "".join(form for _, form in mapped) != whole:
        # Normalization composed across a cluster boundary (Hangul jamo, some Indic
        # vowel signs). Matching stays exact; positions fall back to the piece start.
        return [(0, whole)]
    return mapped


class _DocumentText(HTMLParser):
    _SKIPPED = frozenset({"script", "style", "title"})
    _HEAD_CONTENT = frozenset(
        {"base", "link", "meta", "noscript", "script", "style", "template", "title"}
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self._in_head = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "head":
            self._in_head = True
        elif tag == "body" or (self._in_head and tag not in self._HEAD_CONTENT):
            self._in_head = (
                False  # a body tag, or body content, closes an unclosed head
            )
        if tag in self._SKIPPED:
            self._skip_depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "body" or (self._in_head and tag not in self._HEAD_CONTENT):
            self._in_head = False

    def handle_endtag(self, tag: str) -> None:
        if tag == "head":
            self._in_head = False
        elif tag in self._SKIPPED and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_head and data.strip():
            self._in_head = False  # text in an unclosed head starts the body
        if not self._in_head:
            self.parts.append(data)


def extract_document_text(html: str, joiner: str = "") -> str:
    """All text outside ``<head>``, ``<script>``, and ``<style>``, entities decoded.

    ``joiner`` goes between text chunks; the validator keeps the default, which adds nothing.
    """
    parser = _DocumentText()
    parser.feed(html)
    parser.close()
    return joiner.join(parser.parts)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_pf_decode.py expirements/parser-fidelity/test_pf_text.py --import-mode=prepend -q`
Expected: `18 passed`.

- [x] **Step 5: Write the harness README**

`expirements/parser-fidelity/README.md`:

````markdown
# Parser-fidelity harness (Stage 1)

This harness measures which HTML parser yields faithful typed structural elements on
real earnings releases (V2), records what edgartools 5.58.0 returns (V1), and keeps
the fixture corpus in `tests/fixtures/releases/` checkable. The spec is
`specs/release-parser-fidelity.md`, and the plan is
`specs/plans/1-release-parser-fidelity.md`.

No package imports anything here. Scripts that declare dependencies are PEP 723 scripts
with committed locks (`<script>.py.lock`). Run them with `uv run --locked --script`.
Standard-library modules run in the workspace environment with
`uv run --locked --all-packages python`.

## Modules

| File | Role | Environment |
| --- | --- | --- |
| `pf_paths.py` | Repository paths and fixture identifiers | stdlib |
| `pf_decode.py` | Browser-equivalent decoding of saved bytes (frozen) | stdlib |
| `pf_space.py` | The primary and fallback matching spaces (frozen) | stdlib |
| `pf_text.py` | Position-mapped space text; the validator's `html.parser` text | stdlib |
| `pf_toml.py` | A minimal TOML writer for generated files | stdlib |
| `pf_fetch.py` | The live-fetch client: identity, throttle, retries, saving | httpx |
| `pf_classes.py` | Class tests and data-table helpers (frozen) | lxml |
| `pf_dump.py` | Element dumps, the network guard, the adapter entry point (frozen) | stdlib |
| `fetch_policy_pages.py` | Fetches and verifies the source register's SEC quotes | script lock |
| `discover.py` | Samples Item 2.02 exhibits and writes the shortlist | script lock |
| `promote_fixtures.py` | Copies approved exhibits into the corpus; writes the manifest | stdlib |
| `validate_gold.py` | Validates hand-marked gold | stdlib |
| `check_fixtures.py` | The exit-criterion-4 harness check | stdlib + git |
| `adapter_edgartools.py` | Candidate: edgartools 5.58.0 `edgar.documents.parse_html` (frozen) | script lock |
| `adapter_secparser.py` | Candidate: sec-parser 0.58.1 on Python 3.13 (frozen) | script lock |
| `walker.py` | Candidate: the bespoke lxml walker; rules in `walker-rules.md` (frozen) | script lock |
| `control.py` | Negative control: `get_text` lines as paragraphs (frozen) | script lock |
| `run_candidates.py` | Runs each candidate twice per release; determinism and network gates | stdlib + uv |
| `freeze.py` | Records and verifies the freeze (`FROZEN.toml`) | stdlib + git |
| `score.py` | Ranked metrics, diagnostics, and residual failures | stdlib |
| `lock_gate.py` | The lock gate, run in a `git archive` scratch copy | script lock |
| `select_parser.py` | Applies the fixed selection rule step by step | stdlib |
| `v1_return_types.py` | V1: declared and observed return types (live) | script lock |

## Tests

```bash
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
```

The tests sit beside the modules and make no network calls. `--import-mode=prepend`
puts this directory on `sys.path` for the tests. Root pytest configuration belongs to
Stage 2.

## Policies

- **Live access.** Every network call goes through `pf_fetch.py`, or, for V1, through
  httpx transports wrapped by the same throttle:
  - `EDGAR_IDENTITY` must be set outside Git;
  - request starts are at least 0.5 s apart;
  - each run is capped at 500 requests by default;
  - only one live process runs at a time (`data/runs/parser-fidelity/live.lock`);
  - a 403 that persists stops the run.

  The identity is never written to disk.
- **Order.** No candidate parses a fixture until `FROZEN.toml` verifies and every
  `gold.toml` passes the validator. `run_candidates.py fixtures` enforces this.
- **Freeze.** After `freeze.py record`, a frozen file changes only to fix a crash or a
  network-guard trip caused by harness code. `freeze.py amend` records each such
  change. A change never alters a type mapping or a walker rule.
- **Outputs.** Everything generated goes to gitignored `data/raw/` and `data/runs/`.
````

- [x] **Step 6: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/README.md expirements/parser-fidelity/pf_paths.py expirements/parser-fidelity/pf_decode.py expirements/parser-fidelity/pf_space.py expirements/parser-fidelity/pf_text.py expirements/parser-fidelity/test_pf_decode.py expirements/parser-fidelity/test_pf_text.py
git commit -m "feat(parser-fidelity): add decoding, matching spaces, and validator text"
```

---

### Task 2: Live-fetch client

**Files:**
- Create: `expirements/parser-fidelity/pf_fetch.py`
- Test: `expirements/parser-fidelity/test_pf_fetch.py`

**Interfaces:**
- Consumes: nothing from earlier tasks. It needs httpx, which is in the workspace
  environment and pinned in every script that imports this module.
- Produces:
  - **Errors.** `LivePolicyStop(RuntimeError)` means the run must stop and be
    reported. `UnexpectedResponse(RuntimeError)` means the response must not be saved,
    and the caller may skip it.
  - **Identity.** `require_identity(environ: dict | None = None) -> str` reads
    `EDGAR_IDENTITY`.
  - **Throttle.** `Throttle(*, min_interval=0.5, max_requests=500, clock=..., sleep=...)`
    has `.acquire()` and `.count`.
  - **Live lock.** `LiveLock(path: Path)` is a context manager holding an exclusive
    flock.
  - **Saved responses.** `SavedResponse(url, retrieved_at, http_status, content_type,
    bytes, sha256)`, `meta_path(dest: Path) -> Path` (which is
    `<dest>.meta.json`), `read_meta(dest: Path) -> SavedResponse`, and
    `retry_after_seconds(value, now) -> float | None`.
  - **Fetcher.** `EdgarFetcher(identity, *, throttle, transport=None, sleep=...,
    rng=None, now=...)` provides:
    - `.get(url) -> httpx.Response`;
    - `.fetch_and_save(url, dest: Path, expected_types: Collection[str]) -> SavedResponse`;
    - `.close()`;
    - `.throttle`.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_pf_fetch.py`:

```python
import gzip
import hashlib
import json
import random
from datetime import UTC, datetime

import httpx
import pytest
from pf_fetch import (
    EdgarFetcher,
    LiveLock,
    LivePolicyStop,
    Throttle,
    UnexpectedResponse,
    meta_path,
    require_identity,
    retry_after_seconds,
)

IDENTITY = "Jane Doe earnings-themes research jane@example.org"
NOW = datetime(2026, 9, 22, 12, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def make_fetcher(handler, clock=None, max_requests=500):
    clock = clock or FakeClock()
    throttle = Throttle(max_requests=max_requests, clock=clock.clock, sleep=clock.sleep)
    fetcher = EdgarFetcher(
        IDENTITY,
        throttle=throttle,
        transport=httpx.MockTransport(handler),
        sleep=clock.sleep,
        rng=random.Random(0),
        now=lambda: NOW,
    )
    return fetcher, clock


def test_identity_must_be_descriptive_with_a_contact():
    assert require_identity({"EDGAR_IDENTITY": IDENTITY}) == IDENTITY
    for bad in (
        {},
        {"EDGAR_IDENTITY": "jane@example.org"},
        {"EDGAR_IDENTITY": "Jane Doe"},
    ):
        with pytest.raises(LivePolicyStop):
            require_identity(bad)


def test_throttle_spaces_request_starts_and_enforces_the_budget():
    clock = FakeClock()
    throttle = Throttle(max_requests=2, clock=clock.clock, sleep=clock.sleep)
    throttle.acquire()
    clock.now += 0.1
    throttle.acquire()
    assert clock.sleeps == [pytest.approx(0.4)]
    with pytest.raises(LivePolicyStop):
        throttle.acquire()
    assert throttle.count == 2


def test_user_agent_is_the_identity():
    seen = []

    def handler(request):
        seen.append(request.headers["user-agent"])
        return httpx.Response(200, text="ok")

    fetcher, _ = make_fetcher(handler)
    fetcher.get("https://www.sec.gov/x")
    assert seen == [IDENTITY]


def test_429_honours_retry_after_then_succeeds():
    responses = [
        httpx.Response(429, headers={"Retry-After": "7"}),
        httpx.Response(200, text="ok"),
    ]
    fetcher, clock = make_fetcher(lambda request: responses.pop(0))
    assert fetcher.get("https://www.sec.gov/x").status_code == 200
    assert fetcher.throttle.count == 2
    assert max(clock.sleeps) >= 7


def test_a_single_403_is_retried_but_a_persistent_403_stops_the_run():
    once = [httpx.Response(403), httpx.Response(200, text="ok")]
    fetcher, _ = make_fetcher(lambda request: once.pop(0))
    assert fetcher.get("https://www.sec.gov/x").status_code == 200

    fetcher, _ = make_fetcher(lambda request: httpx.Response(403))
    with pytest.raises(LivePolicyStop, match="403 persisted"):
        fetcher.get("https://www.sec.gov/x")
    assert fetcher.throttle.count == 2


def test_server_errors_are_retried_a_bounded_number_of_times():
    fetcher, _ = make_fetcher(lambda request: httpx.Response(503))
    with pytest.raises(LivePolicyStop, match="503"):
        fetcher.get("https://www.sec.gov/x")
    assert fetcher.throttle.count == 4


def test_retry_after_accepts_seconds_and_http_dates():
    assert retry_after_seconds("12", NOW) == 12.0
    assert retry_after_seconds("Tue, 22 Sep 2026 12:00:30 GMT", NOW) == 30.0
    assert retry_after_seconds("soon", NOW) is None


def test_fetch_and_save_writes_decoded_bytes_and_metadata(tmp_path):
    body = b"<html><body>\x93Release\x94</body></html>"

    def handler(request):
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html", "Content-Encoding": "gzip"},
            content=gzip.compress(body),
        )

    fetcher, _ = make_fetcher(handler)
    dest = tmp_path / "x" / "source.html"
    saved = fetcher.fetch_and_save(
        "https://www.sec.gov/Archives/x.htm", dest, {"text/html"}
    )
    assert dest.read_bytes() == body
    assert saved.sha256 == hashlib.sha256(body).hexdigest()
    assert saved.bytes == len(body)
    assert saved.retrieved_at == "2026-09-22T12:00:00Z"
    meta = json.loads(meta_path(dest).read_text())
    assert meta["url"] == "https://www.sec.gov/Archives/x.htm"
    assert IDENTITY not in meta_path(dest).read_text()


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, headers={"Content-Type": "application/json"}, text="{}"),
        httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text="Your Request Originates from an Undeclared Automated Tool",
        ),
        httpx.Response(404, headers={"Content-Type": "text/html"}, text="missing"),
    ],
)
def test_unexpected_responses_are_not_saved(tmp_path, response):
    fetcher, _ = make_fetcher(lambda request: response)
    dest = tmp_path / "source.html"
    with pytest.raises(UnexpectedResponse):
        fetcher.fetch_and_save("https://www.sec.gov/x.htm", dest, {"text/html"})
    assert not dest.exists()


def test_only_one_live_process_at_a_time(tmp_path):
    lock_path = tmp_path / "live.lock"
    with LiveLock(lock_path), pytest.raises(LivePolicyStop), LiveLock(lock_path):
        pass
    with LiveLock(lock_path):
        pass
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_pf_fetch.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'pf_fetch'`.

- [x] **Step 3: Write the implementation**

`expirements/parser-fidelity/pf_fetch.py`:

```python
"""The Stage 1 live-fetch client (spec: Live-fetch policy).

Every network call in Stage 1 goes through this module: one identity, one throttle
(request starts at least 0.5 s apart, at most ``max_requests`` per run), explicit
timeouts, bounded retries with exponential backoff and jitter, ``Retry-After``
honoured, and a stop on a 403 that persists. Only 200 responses of the expected
content type are saved; an SEC block or rate-limit page is a failure. The identity
is sent as the User-Agent and never written to disk.
"""

from __future__ import annotations

import email.utils
import fcntl
import hashlib
import json
import os
import random
import re
import time
from collections.abc import Callable, Collection
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Self

import httpx

IDENTITY_ENV = "EDGAR_IDENTITY"
MIN_INTERVAL_SECONDS = 0.5  # the project default of 2 requests/second (A §397)
DEFAULT_MAX_REQUESTS = 500
MAX_ATTEMPTS = 4
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_CAP_SECONDS = 60.0
MAX_RETRY_AFTER_SECONDS = 300.0
TIMEOUT = httpx.Timeout(30.0, connect=10.0)
FORBIDDEN_LIMIT = 2  # a 403 on an attempt and again on its retry is "persistent"

_CONTACT = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
_BLOCK_MARKERS = (b"undeclared automated tool", b"request rate threshold exceeded")


class LivePolicyStop(RuntimeError):
    """The run must stop and be reported (identity, budget, persistent 403, retries)."""


class UnexpectedResponse(RuntimeError):
    """A response that must not be saved; the caller may skip the item and continue."""


def require_identity(environ: dict[str, str] | None = None) -> str:
    value = (os.environ if environ is None else environ).get(IDENTITY_ENV, "").strip()
    if len(value.split()) < 2 or not _CONTACT.search(value):
        raise LivePolicyStop(
            f"{IDENTITY_ENV} must be set outside Git to a descriptive User-Agent with a real "
            "contact, such as 'Jane Doe earnings-themes research jane@example.org'"
        )
    return value


class Throttle:
    """Spaces request starts and enforces the per-run request budget."""

    def __init__(
        self,
        *,
        min_interval: float = MIN_INTERVAL_SECONDS,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.min_interval = min_interval
        self.max_requests = max_requests
        self.count = 0
        self._clock = clock
        self._sleep = sleep
        self._last_start: float | None = None

    def acquire(self) -> None:
        if self.count >= self.max_requests:
            raise LivePolicyStop(
                f"request budget of {self.max_requests} reached; rerun to continue"
            )
        now = self._clock()
        if self._last_start is not None and now < self._last_start + self.min_interval:
            self._sleep(self._last_start + self.min_interval - now)
            now = self._clock()
        self._last_start = now
        self.count += 1


class LiveLock:
    """Only one live Stage 1 process runs at a time (an exclusive, non-blocking flock)."""

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
            raise LivePolicyStop(f"another live process holds {self.path}") from None
        self._handle = handle
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._handle is not None:
            fcntl.flock(self._handle, fcntl.LOCK_UN)
            self._handle.close()
            self._handle = None


@dataclass(frozen=True)
class SavedResponse:
    url: str
    retrieved_at: str
    http_status: int
    content_type: str
    bytes: int
    sha256: str


def meta_path(dest: Path) -> Path:
    return dest.with_name(dest.name + ".meta.json")


def read_meta(dest: Path) -> SavedResponse:
    return SavedResponse(**json.loads(meta_path(dest).read_text(encoding="utf-8")))


def retry_after_seconds(value: str | None, now: datetime) -> float | None:
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


class EdgarFetcher:
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
        self.throttle = throttle
        self._sleep = sleep
        self._rng = rng or random.Random()
        self._now = now
        self._client = httpx.Client(
            headers={"User-Agent": identity, "Accept-Encoding": "gzip, deflate"},
            timeout=TIMEOUT,
            follow_redirects=True,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def get(self, url: str) -> httpx.Response:
        forbidden = 0
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.throttle.acquire()
            try:
                response = self._client.get(url)
            except httpx.TransportError as exc:
                if attempt == MAX_ATTEMPTS:
                    raise LivePolicyStop(
                        f"{type(exc).__name__} after {attempt} attempts: {url}"
                    ) from exc
                self._backoff(attempt, None)
                continue
            if response.status_code == 403:
                forbidden += 1
                if forbidden >= FORBIDDEN_LIMIT:
                    raise LivePolicyStop(
                        f"403 persisted for {url}; stopping without changing identity"
                    )
                self._backoff(attempt, response)
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == MAX_ATTEMPTS:
                    raise LivePolicyStop(
                        f"HTTP {response.status_code} after {attempt} attempts: {url}"
                    )
                self._backoff(attempt, response)
                continue
            return response
        raise LivePolicyStop(f"no response for {url}")

    def fetch_and_save(
        self, url: str, dest: Path, expected_types: Collection[str]
    ) -> SavedResponse:
        response = self.get(url)
        content_type = response.headers.get("content-type", "")
        media_type = content_type.split(";")[0].strip().lower()
        if response.status_code != 200:
            raise UnexpectedResponse(f"HTTP {response.status_code} for {url}")
        if media_type not in expected_types:
            raise UnexpectedResponse(
                f"content type {content_type!r} for {url}; expected {sorted(expected_types)}"
            )
        body = response.content  # Content-Encoding already decoded; charset untouched
        if media_type == "text/html" and any(
            marker in body[:20000].lower() for marker in _BLOCK_MARKERS
        ):
            raise UnexpectedResponse(f"SEC block or rate-limit page for {url}")
        saved = SavedResponse(
            url=str(response.url),
            retrieved_at=self._now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            http_status=response.status_code,
            content_type=content_type,
            bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
        )
        _write_atomic(dest, body)
        _write_atomic(
            meta_path(dest),
            (json.dumps(asdict(saved), indent=2, sort_keys=True) + "\n").encode(),
        )
        return saved

    def _backoff(self, attempt: int, response: httpx.Response | None) -> None:
        delay = min(BACKOFF_CAP_SECONDS, BACKOFF_BASE_SECONDS * 2 ** (attempt - 1))
        delay *= self._rng.uniform(0.5, 1.0)
        header = response.headers.get("retry-after") if response is not None else None
        requested = retry_after_seconds(header, self._now())
        if requested is not None:
            if requested > MAX_RETRY_AFTER_SECONDS:
                raise LivePolicyStop(
                    f"server asked to wait {requested:.0f}s; stopping the run"
                )
            delay = max(delay, requested)
        self._sleep(delay)


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_pf_fetch.py --import-mode=prepend -q`
Expected: `12 passed`.

- [x] **Step 5: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/pf_fetch.py expirements/parser-fidelity/test_pf_fetch.py
git commit -m "feat(parser-fidelity): add the rate-limited EDGAR fetch client"
```

---

### Task 3: Source register and its SEC policy check

**Prerequisite, identity gate.** The user sets `EDGAR_IDENTITY` in a shell profile
outside the repository, such as `~/.zshenv`. The value is a descriptive User-Agent with
a real contact, for example `Jane Doe earnings-themes research jane@example.org`. Check
that it is present without printing it:
`test -n "$EDGAR_IDENTITY" && echo set`. Stop and ask the user if the check prints
nothing. Never write the value into any file, commit, log, or record.

**Files:**
- Create: `expirements/parser-fidelity/fetch_policy_pages.py`,
  `expirements/parser-fidelity/fetch_policy_pages.py.lock`
- Create: `docs/source-register.toml`
- Test: `expirements/parser-fidelity/test_fetch_policy_pages.py`

**Interfaces:**
- Consumes: `pf_decode.decode_html_bytes`, `pf_space.primary_space`, and
  `pf_text.extract_document_text` (Task 1); `pf_fetch.*` (Task 2).
- Produces:
  - `docs/source-register.toml`, whose table `[sources.sec-edgar]` holds every A §242
    field:
    - `owner`, `url`, `access_method`, `cost`, `license_terms`;
    - `redistribution_status`, `coverage`, `expected_update_pattern`,
      `known_limitations`, `last_verified`.
  - The subtables `access` (R1.3 facts plus `url`, `checked_on`, `access_quote`) and
    `reuse_policy` (`url`, `checked_on`, `quote`).
  - `fetch_policy_pages.verify(register_path, pages) -> list[str]`.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_fetch_policy_pages.py`:

```python
import json

from fetch_policy_pages import PAGES, page_text, policy_sentences, quote_found, verify

PAGE = b"""<html><head><title>Policies</title></head><body>
<h2>Dissemination</h2><p>Information on this site is public information and may be
copied.  Credit is requested.</p><p>Unrelated text.</p></body></html>"""


def test_policy_sentences_pick_the_reuse_statement():
    text = page_text(PAGE)
    assert policy_sentences(text, PAGES["reuse"][1]) == [
        "Dissemination Information on this site is public information and may be copied."
    ]


def test_quote_found_ignores_whitespace_differences():
    text = page_text(PAGE)
    assert quote_found("public information and may be\n copied.", text)
    assert not quote_found("public information and may not be copied.", text)


def _register(tmp_path, reuse_quote, checked_on="2026-09-23"):
    register = tmp_path / "register.toml"
    register.write_text(
        f"[sources.sec-edgar]\nlast_verified = {checked_on}\n"
        f'[sources.sec-edgar.reuse_policy]\nurl = "https://www.sec.gov/p"\n'
        f'checked_on = {checked_on}\nquote = "{reuse_quote}"\n'
        f'[sources.sec-edgar.access]\nurl = "https://www.sec.gov/a"\n'
        f'checked_on = {checked_on}\naccess_quote = "Declare your user agent."\n'
    )
    return register


def _save(pages, key, url, body):
    pages.mkdir(exist_ok=True)
    (pages / f"{key}.html").write_bytes(body)
    meta = {
        "url": url,
        "retrieved_at": "2026-09-23T10:00:00Z",
        "http_status": 200,
        "content_type": "text/html",
        "bytes": len(body),
        "sha256": "x",
    }
    (pages / f"{key}.html.meta.json").write_text(json.dumps(meta))


def test_verify_accepts_matching_quotes_urls_and_dates(tmp_path):
    pages = tmp_path / "pages"
    _save(pages, "reuse", "https://www.sec.gov/p", PAGE)
    _save(pages, "access", "https://www.sec.gov/a", b"<p>Declare your user agent.</p>")
    register = _register(tmp_path, "public information and may be copied.")
    assert verify(register, pages) == []


def test_verify_reports_missing_pages_wrong_quotes_and_dates(tmp_path):
    pages = tmp_path / "pages"
    _save(pages, "reuse", "https://www.sec.gov/p", PAGE)
    register = _register(tmp_path, "may never be copied.", checked_on="2026-09-24")
    problems = verify(register, pages)
    assert any("access.html is missing" in p for p in problems)
    assert any("reuse_policy.quote does not occur" in p for p in problems)
    assert any("checked_on differs" in p for p in problems)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_fetch_policy_pages.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'fetch_policy_pages'`.

- [x] **Step 3: Write the script**

`expirements/parser-fidelity/fetch_policy_pages.py`:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["httpx==0.28.1"]
# ///
"""Fetch the SEC pages that docs/source-register.toml quotes, and verify the quotes.

    uv run --locked --script expirements/parser-fidelity/fetch_policy_pages.py fetch --live
    uv run --locked --script expirements/parser-fidelity/fetch_policy_pages.py verify

``fetch`` saves each page under data/raw/register/ and prints the sentences that state
the SEC's reuse and access policies. Copy the sentences verbatim into the register.
``verify`` checks that every register quote occurs in its saved page.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import tomllib
from pf_decode import decode_html_bytes
from pf_fetch import (
    EdgarFetcher,
    LiveLock,
    LivePolicyStop,
    Throttle,
    UnexpectedResponse,
    read_meta,
    require_identity,
)
from pf_paths import DATA_RAW, LIVE_LOCK, REGISTER
from pf_space import primary_space
from pf_text import extract_document_text

REGISTER_PAGES = DATA_RAW / "register"
PAGES = {
    "reuse": (
        (
            "https://www.sec.gov/privacy.htm",
            "https://www.sec.gov/about/privacy-information",
        ),
        re.compile(
            r"public information|further distribut|copied|reproduc", re.IGNORECASE
        ),
    ),
    "access": (
        ("https://www.sec.gov/os/accessing-edgar-data",),
        re.compile(r"user[- ]agent|requests? per second|automated tool", re.IGNORECASE),
    ),
}
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def page_text(raw: bytes) -> str:
    return " ".join(
        extract_document_text(decode_html_bytes(raw).text, joiner=" ").split()
    )


def policy_sentences(text: str, pattern: re.Pattern[str]) -> list[str]:
    return [
        sentence for sentence in _SENTENCE_END.split(text) if pattern.search(sentence)
    ]


def quote_found(quote: str, text: str) -> bool:
    """Whitespace-insensitive: the primary matching space deletes whitespace."""
    return bool(primary_space(quote)) and primary_space(quote) in primary_space(text)


def fetch(fetcher: EdgarFetcher) -> None:
    for key, (urls, pattern) in PAGES.items():
        for url in urls:
            dest = REGISTER_PAGES / f"{key}.html"
            try:
                saved = fetcher.fetch_and_save(url, dest, {"text/html"})
            except UnexpectedResponse as exc:
                print(f"[{key}] {exc}")
                continue
            print(f"[{key}] saved {saved.url} ({saved.retrieved_at})")
            for sentence in policy_sentences(page_text(dest.read_bytes()), pattern):
                print(f"  - {sentence}")
            break
        else:
            print(
                f"[{key}] no candidate URL answered; locate the page from sec.gov's footer links"
            )


def verify(register_path: Path = REGISTER, pages: Path = REGISTER_PAGES) -> list[str]:
    entry = tomllib.loads(register_path.read_text(encoding="utf-8"))["sources"][
        "sec-edgar"
    ]
    problems = []
    checked = []
    for key, table, field in (
        ("reuse", "reuse_policy", "quote"),
        ("access", "access", "access_quote"),
    ):
        saved = pages / f"{key}.html"
        if not saved.exists():
            problems.append(f"{saved} is missing; run `fetch --live` first")
            continue
        meta = read_meta(saved)
        if meta.url != entry[table]["url"]:
            problems.append(f"{table}.url differs from the saved page's URL {meta.url}")
        if str(entry[table]["checked_on"]) != meta.retrieved_at[:10]:
            problems.append(
                f"{table}.checked_on differs from the retrieval date {meta.retrieved_at[:10]}"
            )
        if not quote_found(entry[table][field], page_text(saved.read_bytes())):
            problems.append(f"{table}.{field} does not occur verbatim in {saved}")
        checked.append(str(entry[table]["checked_on"]))
    if checked and str(entry["last_verified"]) != max(checked):
        problems.append("last_verified must equal the latest checked_on date")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch").add_argument("--live", action="store_true")
    sub.add_parser("verify")
    args = parser.parse_args(argv)
    if args.command == "verify":
        problems = verify()
        for problem in problems:
            print(problem)
        print(
            "register quotes verified"
            if not problems
            else f"{len(problems)} problem(s)"
        )
        return 1 if problems else 0
    if not args.live:
        parser.error("fetch makes live requests; pass --live to confirm")
    throttle = Throttle(max_requests=10)
    fetcher = EdgarFetcher(require_identity(), throttle=throttle)
    try:
        with LiveLock(LIVE_LOCK):
            fetch(fetcher)
    except LivePolicyStop as exc:
        print(f"STOPPED: {exc}", file=sys.stderr)
        return 1
    finally:
        fetcher.close()
        print(f"requests made: {throttle.count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_fetch_policy_pages.py --import-mode=prepend -q`
Expected: `4 passed`.

- [x] **Step 5: Lock the script**

Run: `uv lock --script expirements/parser-fidelity/fetch_policy_pages.py`
Expected: `Resolved … packages`, and `expirements/parser-fidelity/fetch_policy_pages.py.lock` now exists.

- [x] **Step 6: Fetch the SEC policy pages (live, at most 10 requests)**

Run: `uv run --locked --script expirements/parser-fidelity/fetch_policy_pages.py fetch --live`

Expected output:

- a `[reuse] saved <url> (<UTC time>)` line and an `[access] saved <url> (<UTC
  time>)` line, each followed by the matching sentences;
- `requests made: N`, with N at most 10.

Record N; the Task 22 handoff reports it. If a key prints `no candidate URL answered`:

- open https://www.sec.gov in the built-in browser;
- find the page that states the website's reuse (dissemination) policy, or the page
  that states EDGAR's access policy, by following the site's footer links;
- add its URL as the first entry of that key's tuple in `PAGES`;
- rerun Step 4 and this step.

- [x] **Step 7: Write the register from the fetched pages**

Create `docs/source-register.toml` with exactly this content:

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
submissions JSON (data.sec.gov/submissions/), filing index pages, and filed documents, through \
expirements/parser-fidelity/pf_fetch.py with a descriptive User-Agent read from EDGAR_IDENTITY, \
which is configured outside Git."""
cost = "Free; no account or API key."
license_terms = """The SEC's statement on reuse of its website content is quoted in \
[sources.sec-edgar.reuse_policy]. Filed documents are authored by the filers."""
redistribution_status = """The SEC's reuse statement is quoted in [sources.sec-edgar.reuse_policy]. \
That statement does not address issuers' copyright in their filings, and this register draws no \
conclusion about it. Stage 1 commits eight release exhibits byte-for-byte under decision F1 of \
specs/release-parser-fidelity.md."""
coverage = """EDGAR electronic filings. Stage 1 samples Form 8-K filings that report Item 2.02 \
(Results of Operations and Financial Condition), which dates from August 2004, and their \
press-release exhibits."""
expected_update_pattern = """Filings arrive as the SEC accepts them. Amendments and corrections \
arrive as new accessions rather than edits to filed documents. A quarter's full-index files grow \
until the quarter ends."""
known_limitations = [
    "Exhibit numbering and descriptions vary by filer; a press release is not always EX-99.1.",
    "Some exhibits are image-only or plain text; Stage 1 excludes them (R4.3).",
    "Exhibit HTML is generated by filers and filing agents and is often malformed.",
    "Charsets are often undeclared; Stage 1 decodes with browser rules (pf_decode.py).",
]
last_verified = FILL_DATE_FROM_FETCH

[sources.sec-edgar.access]
# R1.3 of specs/evidence-linked-theme-extraction.md (verified access behavior, RC §1).
user_agent_required = true
missing_user_agent_status = 403
rate_limit_breach_status = 429
project_max_requests_per_second = 2
url = "FILL_URL_FROM_FETCH"
checked_on = FILL_DATE_FROM_FETCH
access_quote = "FILL_QUOTE_FROM_FETCH"

[sources.sec-edgar.reuse_policy]
url = "FILL_URL_FROM_FETCH"
checked_on = FILL_DATE_FROM_FETCH
quote = "FILL_QUOTE_FROM_FETCH"
```

Then replace every `FILL_*` marker:

- **`url`:** the URL printed after `saved`. For `reuse_policy.url` use the `[reuse]`
  line; for `access.url` use the `[access]` line.
- **`checked_on` and `last_verified`:** the `YYYY-MM-DD` part of the printed UTC
  time.
- **`reuse_policy.quote`:** the single printed `[reuse]` sentence that states whether
  the site's content may be copied or distributed.
- **`access.access_quote`:** the printed `[access]` sentence that states the
  User-Agent requirement.

Copy each sentence exactly, and escape any `"` as `\"`. The unfilled template does not
parse as TOML, so no marker can survive the next step.

- [x] **Step 8: Verify the register**

Run: `uv run --locked --script expirements/parser-fidelity/fetch_policy_pages.py verify`
Expected: `register quotes verified`.

- [x] **Step 9: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add docs/source-register.toml expirements/parser-fidelity/fetch_policy_pages.py expirements/parser-fidelity/fetch_policy_pages.py.lock expirements/parser-fidelity/test_fetch_policy_pages.py
git commit -m "docs: add the source register with the verified SEC policy quotes"
```

---

### Task 4: Class tests

**Files:**
- Create: `expirements/parser-fidelity/pf_classes.py`
- Test: `expirements/parser-fidelity/test_pf_classes.py`

**Interfaces:**
- Consumes: `pf_decode.decode_html_bytes` and `pf_space.primary_space` (Task 1).
- Produces:
  - **Parsing.** `parse_document(text: str) -> HtmlElement` and
    `body_of(root) -> HtmlElement`.
  - **Visibility.** `is_hidden(el) -> bool`, `visible_elements(root)`, and
    `visible_text(el, *, skip_tables=False) -> str`.
  - **Tables.** `own_rows(table)`, `own_cells(row)`, `cell_text(cell) -> str`, and
    `is_data_table(table) -> bool`.
  - **Page numbers.** `BARE_PAGE_NUMBER`, a compiled regex.
  - **Class tests.** `ClassTests`, a frozen dataclass with fields `visible_chars`,
    `data_tables`, `data_table_chars`, `data_table_share`, `pre_chars`, `pre_share`,
    `positioned_text`, `layout_table_prose`, `max_layout_cell_words`,
    `page_break_styling`, `bare_page_number_blocks`, `page_break_debris`,
    `preformatted_text`, `table_heavy`, `narrative_only`, `malformed_layout`, and
    `clean_html`, plus `.as_dict()`. The entry point is
    `run_class_tests(raw: bytes) -> ClassTests`.

The walker (Task 14) imports these helpers, so this module is frozen in Task 15. It
must not change after discovery either: the manifest records the values it computed.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_pf_classes.py`:

```python
from pf_classes import is_data_table, parse_document, run_class_tests

DATA_TABLE = (
    "<table><tr><td></td><td>2025</td><td>2024</td></tr>"
    "<tr><td>Net sales</td><td>4,321</td><td>3,210</td></tr></table>"
)
PROSE = "<p>" + " ".join(["word"] * 30) + "</p>"


def page(body: str, head: str = "") -> bytes:
    return f"<html><head>{head}</head><body>{body}</body></html>".encode()


def first_table(html: str):
    return parse_document(html).find(".//table")


def test_data_table_needs_two_rows_with_text_and_a_multi_cell_row():
    assert is_data_table(first_table(DATA_TABLE))
    assert not is_data_table(
        first_table("<table><tr><td>Only</td><td>row</td></tr></table>")
    )
    assert not is_data_table(
        first_table("<table><tr><td>a</td></tr><tr><td>b</td></tr></table>")
    )


def test_nested_table_rows_do_not_count_for_the_outer_table():
    wrapper = f"<table><tr><td>{DATA_TABLE}</td></tr></table>"
    root = parse_document(wrapper)
    outer, inner = root.findall(".//table")
    assert not is_data_table(outer)
    assert is_data_table(inner)


def test_narrative_only_release_is_clean():
    tests = run_class_tests(page(PROSE))
    assert tests.narrative_only and tests.clean_html and not tests.table_heavy
    assert tests.visible_chars == len("word") * 30


def test_table_heavy_counts_characters_inside_data_tables():
    tests = run_class_tests(page("<p>Intro</p>" + DATA_TABLE))
    assert tests.data_tables == 1
    assert tests.table_heavy
    assert tests.data_table_chars == len("20252024Netsales4,3213,210")


def test_hidden_text_is_not_visible():
    tests = run_class_tests(
        page('<div style="display: none">hidden words</div><p>shown</p>')
    )
    assert tests.visible_chars == len("shown")


def test_positioned_text_fires_from_inline_style_or_style_block():
    assert run_class_tests(
        page('<p style="position:absolute;top:5px">x</p>')
    ).positioned_text
    assert run_class_tests(
        page("<p>x</p>", head="<style>.a{position: fixed}</style>")
    ).positioned_text


def test_layout_table_prose_fires_on_a_40_word_cell_in_a_non_data_table():
    long_cell = "<table><tr><td>" + " ".join(["w"] * 40) + "</td></tr></table>"
    tests = run_class_tests(page(long_cell))
    assert tests.layout_table_prose and tests.malformed_layout
    assert tests.max_layout_cell_words == 40


def test_page_break_debris_needs_page_break_styling_and_a_bare_page_number():
    debris = '<p>Text</p><p style="text-align:center">- 2 -</p><hr style="page-break-after: always">'
    assert run_class_tests(page(debris)).page_break_debris
    assert not run_class_tests(
        page('<p>Text</p><p style="text-align:center">- 2 -</p>')
    ).page_break_debris
    assert run_class_tests(
        page('<p>Text</p><p>Page 3</p><div style="break-before: page"></div>')
    ).page_break_debris


def test_preformatted_text_fires_when_pre_holds_half_the_characters():
    tests = run_class_tests(
        page("<pre>Revenue rose five percent in the quarter.</pre><p>x</p>")
    )
    assert tests.preformatted_text and tests.malformed_layout
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_pf_classes.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'pf_classes'`.

- [x] **Step 3: Write the implementation**

`expirements/parser-fidelity/pf_classes.py`:

```python
"""Deterministic class tests for release exhibits (spec: Fixture corpus > Classes).

These values only sort fixtures into classes; they are not quality thresholds (R13.1
is untouched). The walker imports the data-table helpers, so this module is frozen
with it. Characters are counted in the primary matching space.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import asdict, dataclass

import lxml.html
from lxml.html import HtmlElement
from pf_decode import decode_html_bytes
from pf_space import primary_space

SHARE_THRESHOLD = 0.5
LAYOUT_PROSE_WORDS = 40
HIDDEN_TAGS = frozenset({"script", "style", "head", "title", "noscript", "template"})
BLOCK_TAGS = frozenset(
    {"p", "div", "center", "td", "th", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
)

_DISPLAY_NONE = re.compile(r"display\s*:\s*none", re.IGNORECASE)
_POSITIONED = re.compile(r"position\s*:\s*(?:absolute|fixed)", re.IGNORECASE)
_PAGE_BREAK = re.compile(
    r"page-break-(?:before|after)\s*:\s*(?:always|left|right)|(?<![-\w])break-(?:before|after)\s*:\s*page",
    re.IGNORECASE,
)
BARE_PAGE_NUMBER = re.compile(
    r"(?:page\s*)?[-\u2013\u2014\s]*\d{1,4}[-\u2013\u2014\s]*", re.IGNORECASE
)


@dataclass(frozen=True)
class ClassTests:
    visible_chars: int
    data_tables: int
    data_table_chars: int
    data_table_share: float
    pre_chars: int
    pre_share: float
    positioned_text: bool
    layout_table_prose: bool
    max_layout_cell_words: int
    page_break_styling: bool
    bare_page_number_blocks: int
    page_break_debris: bool
    preformatted_text: bool
    table_heavy: bool
    narrative_only: bool
    malformed_layout: bool
    clean_html: bool

    def as_dict(self) -> dict[str, int | float | bool]:
        return asdict(self)


def parse_document(text: str) -> HtmlElement:
    """Parse decoded text with libxml2's HTML parser; the explicit encoding overrides declarations."""
    parser = lxml.html.HTMLParser(encoding="utf-8")
    return lxml.html.document_fromstring(text.encode("utf-8"), parser=parser)


def body_of(root: HtmlElement) -> HtmlElement:
    body = root.find("body")
    return body if body is not None else root


def is_hidden(el: HtmlElement) -> bool:
    """Comments, processing instructions, hidden tags, and inline ``display: none``."""
    if not isinstance(el.tag, str):
        return True
    return el.tag.lower() in HIDDEN_TAGS or bool(
        _DISPLAY_NONE.search(el.get("style") or "")
    )


def visible_elements(root: HtmlElement) -> Iterator[HtmlElement]:
    stack = [root]
    while stack:
        el = stack.pop()
        if is_hidden(el):
            continue
        yield el
        stack.extend(reversed(list(el)))


def visible_text(el: HtmlElement, *, skip_tables: bool = False) -> str:
    """Visible text of ``el``; with ``skip_tables``, text of nested tables is left out."""
    parts: list[str] = []
    stack: list[HtmlElement | str] = [el]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            parts.append(item)
            continue
        if is_hidden(item) or (skip_tables and item is not el and item.tag == "table"):
            continue
        pending: list[HtmlElement | str] = [item.text] if item.text else []
        for child in item:
            pending.append(child)
            if child.tail:
                pending.append(child.tail)
        stack.extend(reversed(pending))
    return "".join(parts)


def _nearest(el: HtmlElement, tag: str) -> HtmlElement | None:
    parent = el.getparent()
    while parent is not None and parent.tag != tag:
        parent = parent.getparent()
    return parent


def own_rows(table: HtmlElement) -> list[HtmlElement]:
    """The table's own visible rows, not those of nested tables."""
    return [
        tr
        for tr in table.iter("tr")
        if _nearest(tr, "table") is table and not is_hidden(tr)
    ]


def own_cells(row: HtmlElement) -> list[HtmlElement]:
    return [
        cell
        for cell in row.iter("td", "th")
        if _nearest(cell, "tr") is row and not is_hidden(cell)
    ]


def cell_text(cell: HtmlElement) -> str:
    return visible_text(cell, skip_tables=True)


def is_data_table(table: HtmlElement) -> bool:
    """At least two rows with text and one row with two or more non-empty cells (own rows and cells)."""
    rows_with_text = 0
    has_multi_cell_row = False
    for row in own_rows(table):
        filled = sum(1 for cell in own_cells(row) if primary_space(cell_text(cell)))
        rows_with_text += filled > 0
        has_multi_cell_row = has_multi_cell_row or filled >= 2
    return rows_with_text >= 2 and has_multi_cell_row


def _text_segments(
    body: HtmlElement, data_tables: set[HtmlElement]
) -> list[tuple[str, bool, bool]]:
    """Visible text segments with (inside a data table, inside <pre>) flags."""
    out: list[tuple[str, bool, bool]] = []
    stack: list[tuple[HtmlElement | str, bool, bool]] = [(body, False, False)]
    while stack:
        item, in_data, in_pre = stack.pop()
        if isinstance(item, str):
            out.append((item, in_data, in_pre))
            continue
        if is_hidden(item):
            continue
        in_data = in_data or item in data_tables
        in_pre = in_pre or item.tag == "pre"
        pending: list[tuple[HtmlElement | str, bool, bool]] = []
        if item.text:
            pending.append((item.text, in_data, in_pre))
        for child in item:
            pending.append((child, in_data, in_pre))
            if child.tail:
                pending.append((child.tail, in_data, in_pre))
        stack.extend(reversed(pending))
    return out


def _style_sources(root: HtmlElement) -> list[str]:
    inline = [el.get("style") or "" for el in root.iter() if isinstance(el.tag, str)]
    sheets = [el.text or "" for el in root.iter("style")]
    return inline + sheets


def run_class_tests(raw: bytes) -> ClassTests:
    root = parse_document(decode_html_bytes(raw).text)
    body = body_of(root)
    elements = list(visible_elements(body))
    tables = [el for el in elements if el.tag == "table"]
    data_tables = {table for table in tables if is_data_table(table)}

    segments = _text_segments(body, data_tables)
    visible_chars = sum(len(primary_space(text)) for text, _, _ in segments)
    data_chars = sum(
        len(primary_space(text)) for text, in_data, _ in segments if in_data
    )
    pre_chars = sum(len(primary_space(text)) for text, _, in_pre in segments if in_pre)
    data_share = data_chars / visible_chars if visible_chars else 0.0
    pre_share = pre_chars / visible_chars if visible_chars else 0.0

    styles = _style_sources(root)
    positioned = any(_POSITIONED.search(style) for style in styles)
    page_break_styling = any(_PAGE_BREAK.search(style) for style in styles)

    layout_words = [
        len(cell_text(cell).split())
        for table in tables
        if table not in data_tables
        for row in own_rows(table)
        for cell in own_cells(row)
    ]
    max_layout_words = max(layout_words, default=0)

    bare_page_numbers = sum(
        1
        for el in elements
        if el.tag in BLOCK_TAGS
        and not any(ancestor in data_tables for ancestor in el.iterancestors("table"))
        and BARE_PAGE_NUMBER.fullmatch(visible_text(el).strip())
    )

    layout_table_prose = max_layout_words >= LAYOUT_PROSE_WORDS
    page_break_debris = page_break_styling and bare_page_numbers > 0
    preformatted = pre_share >= SHARE_THRESHOLD
    malformed = positioned or layout_table_prose or page_break_debris or preformatted
    return ClassTests(
        visible_chars=visible_chars,
        data_tables=len(data_tables),
        data_table_chars=data_chars,
        data_table_share=round(data_share, 4),
        pre_chars=pre_chars,
        pre_share=round(pre_share, 4),
        positioned_text=positioned,
        layout_table_prose=layout_table_prose,
        max_layout_cell_words=max_layout_words,
        page_break_styling=page_break_styling,
        bare_page_number_blocks=bare_page_numbers,
        page_break_debris=page_break_debris,
        preformatted_text=preformatted,
        table_heavy=data_share >= SHARE_THRESHOLD,
        narrative_only=not data_tables,
        malformed_layout=malformed,
        clean_html=not malformed,
    )
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_pf_classes.py --import-mode=prepend -q`
Expected: `9 passed`.

- [x] **Step 5: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/pf_classes.py expirements/parser-fidelity/test_pf_classes.py
git commit -m "feat(parser-fidelity): add deterministic release class tests"
```

---

### Task 5: Discovery script

**Files:**
- Create: `expirements/parser-fidelity/discover.py`, `expirements/parser-fidelity/discover.py.lock`
- Test: `expirements/parser-fidelity/test_discover.py`

**Interfaces:**
- Consumes:
  - `pf_classes.run_class_tests` (Task 4);
  - `pf_fetch.EdgarFetcher`, `LiveLock`, `LivePolicyStop`, `Throttle`,
    `UnexpectedResponse`, `read_meta`, `require_identity`, and
    `DEFAULT_MAX_REQUESTS` (Task 2);
  - `pf_paths.DISCOVERY`, `LIVE_LOCK`, `MAX_FIXTURE_BYTES`, and `fixture_id`
    (Task 1).
- Produces:
  - **Records.** `data/raw/discovery/candidates.jsonl`, one `Candidate` per line,
    with fields `fixture_id`, `cik`, `issuer_name`, `accession`, `agent`, `form`,
    `items`, `filing_date`, `exhibit_type`, `exhibit_filename`,
    `exhibit_description`, `url`, `year`, `quarter`, `within_size_cap`, and
    `class_tests`. Task 7 reads this file.
  - **Saved responses.** `data/raw/discovery/<fixture_id>/source.html` plus
    `source.html.meta.json`.
  - **Shortlist.** `data/raw/discovery/shortlist.md`.
  - **Python API.** `load_candidates()`, `suggest(candidates)`, and
    `render_shortlist(candidates)`.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_discover.py`:

```python
import json
import random

import httpx
import pytest
from discover import (
    Candidate,
    Discovery,
    IndexDocument,
    SubmissionFiling,
    older_pages_covering,
    parse_filing_index,
    parse_master_index,
    parse_submission_filings,
    pick_earnings_filing,
    pick_press_release,
    quarter_bounds,
    render_shortlist,
    sample_ciks,
    suggest,
)
from pf_fetch import EdgarFetcher, Throttle

MASTER_IDX = """Description:           Master Index of EDGAR Dissemination Feed
Last Data Received:    March 31, 2025

CIK|Company Name|Form Type|Date Filed|Filename
--------------------------------------------------------------------------------
320193|Apple Inc.|8-K|2025-01-30|edgar/data/320193/0000320193-25-000007.txt
320193|Apple Inc.|10-Q|2025-01-31|edgar/data/320193/0000320193-25-000008.txt
789019|MICROSOFT CORP|8-K|2025-01-29|edgar/data/789019/0001193125-25-012345.txt
1018724|AMAZON COM INC|8-K|2025-02-06|edgar/data/1018724/0001018724-25-000004.txt
"""

INDEX_PAGE = """<html><body>
<table class="tableFile" summary="Document Format Files">
<tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th><th>Size</th></tr>
<tr><td>1</td><td>8-K</td><td><a href="/ix?doc=/Archives/edgar/data/320193/000032019325000007/a8-k.htm">a8-k.htm</a> iXBRL</td><td>8-K</td><td>40000</td></tr>
<tr><td>2</td><td>PRESS RELEASE DATED JANUARY 30, 2025</td><td><a href="/Archives/edgar/data/320193/000032019325000007/a8-kex991q1.htm">a8-kex991q1.htm</a></td><td>EX-99.1</td><td>90000</td></tr>
<tr><td>3</td><td>DATA SUPPLEMENT</td><td><a href="/Archives/edgar/data/320193/000032019325000007/a8-kex992.htm">a8-kex992.htm</a></td><td>EX-99.2</td><td>9000</td></tr>
</table></body></html>"""


def recent_block(rows):
    return {
        "accessionNumber": [r[0] for r in rows],
        "form": [r[1] for r in rows],
        "filingDate": [r[2] for r in rows],
        "items": [r[3] for r in rows],
    }


def test_parse_master_index_skips_headers_and_pads_cik():
    rows = parse_master_index(MASTER_IDX)
    assert [r.form for r in rows] == ["8-K", "10-Q", "8-K", "8-K"]
    assert rows[0].cik == "0000320193"
    assert rows[2].accession == "0001193125-25-012345"
    assert rows[2].agent == "0001193125"


def test_sample_ciks_is_deterministic_distinct_and_only_8k():
    rows = parse_master_index(MASTER_IDX)
    first = sample_ciks(rows, count=5, rng=random.Random(1))
    again = sample_ciks(rows, count=5, rng=random.Random(1))
    assert first == again
    assert {r.form for r in first} == {"8-K"}
    assert len({r.cik for r in first}) == len(first) == 3


def test_quarter_bounds_end_on_the_last_day():
    assert quarter_bounds(2024, 1) == ("2024-01-01", "2024-03-31")
    assert quarter_bounds(2024, 4) == ("2024-10-01", "2024-12-31")


def test_pick_earnings_filing_needs_item_202_in_the_quarter():
    filings = parse_submission_filings(
        recent_block(
            [
                ("0000320193-25-000009", "8-K", "2025-02-20", "5.07"),
                ("0000320193-25-000007", "8-K", "2025-01-30", "2.02,9.01"),
                ("0000320193-25-000001", "8-K/A", "2025-01-10", "2.02"),
                ("0000320193-24-000090", "8-K", "2024-10-31", "2.02,9.01"),
            ]
        )
    )
    chosen = pick_earnings_filing(filings, 2025, 1)
    assert chosen == SubmissionFiling(
        "0000320193-25-000007", "8-K", "2025-01-30", "2.02,9.01"
    )
    assert pick_earnings_filing(filings, 2025, 2) is None


def test_older_pages_are_selected_by_date_overlap():
    document = {
        "filings": {
            "files": [
                {
                    "name": "CIK0000320193-submissions-001.json",
                    "filingFrom": "1994-01-26",
                    "filingTo": "2010-03-30",
                },
                {
                    "name": "CIK0000320193-submissions-002.json",
                    "filingFrom": "2010-03-31",
                    "filingTo": "2016-12-31",
                },
            ]
        }
    }
    assert older_pages_covering(document, 2010, 1) == [
        "CIK0000320193-submissions-001.json",
        "CIK0000320193-submissions-002.json",
    ]
    assert older_pages_covering(document, 2005, 3) == [
        "CIK0000320193-submissions-001.json"
    ]


def test_parse_filing_index_reads_types_descriptions_and_ixbrl_links():
    documents = parse_filing_index(INDEX_PAGE)
    assert [d.doc_type for d in documents] == ["8-K", "EX-99.1", "EX-99.2"]
    assert documents[0].filename == "a8-k.htm"
    assert documents[1].description == "PRESS RELEASE DATED JANUARY 30, 2025"


def test_pick_press_release_prefers_the_described_exhibit():
    chosen, reason = pick_press_release(parse_filing_index(INDEX_PAGE))
    assert reason == "ok" and chosen.doc_type == "EX-99.1"
    single = [IndexDocument("2", "EXHIBIT 99", "ex99.htm", "EX-99")]
    assert pick_press_release(single)[0].filename == "ex99.htm"
    ambiguous = [
        IndexDocument("2", "A", "a.htm", "EX-99.1"),
        IndexDocument("3", "B", "b.htm", "EX-99.2"),
    ]
    assert pick_press_release(ambiguous)[0] is None
    text_only = [IndexDocument("2", "PRESS RELEASE", "ex99.txt", "EX-99.1")]
    assert pick_press_release(text_only) == (None, "exhibit is not HTML (ex99.txt)")


def _candidate(fid, cik, agent, year, **tests):
    class_tests = {
        "narrative_only": False,
        "malformed_layout": False,
        "table_heavy": False,
        "clean_html": True,
    }
    class_tests.update(tests)
    class_tests["data_table_share"] = 0.6 if class_tests["table_heavy"] else 0.0
    class_tests.setdefault("visible_chars", 5000)
    return Candidate(
        fid,
        cik,
        "Issuer",
        "acc",
        agent,
        "8-K",
        "2.02",
        "2025-01-30",
        "EX-99.1",
        "x.htm",
        "",
        "u",
        year,
        1,
        True,
        class_tests,
    )


def test_suggest_caps_issuers_and_spreads_agents():
    pool = [
        _candidate("a", "c1", "g1", 2005, narrative_only=True),
        _candidate("b", "c1", "g1", 2008, narrative_only=True),
        _candidate("c", "c1", "g2", 2011, narrative_only=True),
        _candidate("d", "c2", "g2", 2014, narrative_only=True),
    ]
    picks = suggest(pool)["narrative_only"]
    assert len(picks) == 3
    assert sum(p.cik == "c1" for p in picks) == 2
    assert "## narrative_only (4 eligible)" in render_shortlist(pool)


def test_discovery_end_to_end_saves_one_candidate_and_reruns_without_requests(tmp_path):
    exhibit = b"<html><body><p>" + b"Revenue rose. " * 10 + b"</p></body></html>"
    routes = {
        "https://www.sec.gov/Archives/edgar/full-index/2025/QTR1/master.idx": (
            "text/plain",
            MASTER_IDX.encode(),
        ),
        "https://data.sec.gov/submissions/CIK0000320193.json": (
            "application/json",
            json.dumps(
                {
                    "filings": {
                        "recent": recent_block(
                            [("0000320193-25-000007", "8-K", "2025-01-30", "2.02,9.01")]
                        ),
                        "files": [],
                    }
                }
            ).encode(),
        ),
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000007/0000320193-25-000007-index.htm": (
            "text/html",
            INDEX_PAGE.encode(),
        ),
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000007/a8-kex991q1.htm": (
            "text/html",
            exhibit,
        ),
    }

    def handler(request):
        url = str(request.url)
        if url in routes:
            content_type, body = routes[url]
            return httpx.Response(
                200, headers={"Content-Type": content_type}, content=body
            )
        if "submissions" in url:
            return httpx.Response(
                200,
                headers={"Content-Type": "application/json"},
                content=json.dumps(
                    {"filings": {"recent": recent_block([]), "files": []}}
                ).encode(),
            )
        return httpx.Response(404)

    def fetcher():
        throttle = Throttle(min_interval=0.0)
        return EdgarFetcher(
            "Jane Doe research jane@example.org",
            throttle=throttle,
            transport=httpx.MockTransport(handler),
            sleep=lambda s: None,
        )

    first = fetcher()
    Discovery(first, root=tmp_path).run_year(2025, 1, per_year=1, rng=random.Random(3))
    lines = (tmp_path / "candidates.jsonl").read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["fixture_id"] == "0000320193-25-000007_ex-99-1"
    assert record["items"] == "2.02,9.01"
    assert record["class_tests"]["narrative_only"] is True
    assert (tmp_path / record["fixture_id"] / "source.html").read_bytes() == exhibit

    second = fetcher()
    Discovery(second, root=tmp_path).run_year(2025, 1, per_year=1, rng=random.Random(3))
    assert second.throttle.count == 0
    assert len((tmp_path / "candidates.jsonl").read_text().splitlines()) == 1


@pytest.mark.parametrize("years", [[2004], [2003, 2010]])
def test_run_refuses_years_before_item_202(years):
    from discover import main

    with pytest.raises(SystemExit):
        main(["run", "--live", "--years", *map(str, years)])


def test_image_only_exhibits_are_excluded_from_the_shortlist():
    pool = [
        _candidate("a", "c1", "g1", 2005, narrative_only=True, visible_chars=40),
        _candidate("b", "c2", "g2", 2008, narrative_only=True),
    ]
    assert [c.fixture_id for c in suggest(pool)["narrative_only"]] == ["b"]
    shortlist = render_shortlist(pool)
    assert "## narrative_only (1 eligible)" in shortlist
    assert "1 have under 500 characters of native text" in shortlist
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_discover.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'discover'`.

- [x] **Step 3: Write the script**

`expirements/parser-fidelity/discover.py`:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["httpx==0.28.1", "lxml==6.1.3"]
# ///
"""Discover Item 2.02 press-release exhibits for the Stage 1 fixture shortlist.

Sources: EDGAR's quarterly filing index (``master.idx``) is the sampling frame across
years and filer agents; the submissions data supplies each filing's Item list; the
filing index page supplies the exhibit type and description. Every response is saved
under ``data/raw/discovery/`` and reused on rerun, so no exhibit is fetched twice.

Usage (live, opt-in; ``EDGAR_IDENTITY`` must be set outside Git):
    uv run --locked --script expirements/parser-fidelity/discover.py run --live
    uv run --locked --script expirements/parser-fidelity/discover.py shortlist
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import lxml.html
from pf_classes import run_class_tests
from pf_fetch import (
    DEFAULT_MAX_REQUESTS,
    EdgarFetcher,
    LiveLock,
    LivePolicyStop,
    Throttle,
    UnexpectedResponse,
    read_meta,
    require_identity,
)
from pf_paths import DISCOVERY, LIVE_LOCK, MAX_FIXTURE_BYTES, fixture_id

FIRST_SAMPLED_YEAR = (
    2005  # Item 2.02 dates from August 2004; 2005 is its first full year
)
DEFAULT_YEARS = (2005, 2008, 2011, 2014, 2017, 2020, 2023, 2025)
DEFAULT_PER_YEAR = 8
DEFAULT_SEED = 20260922
CANDIDATES_FILE = DISCOVERY / "candidates.jsonl"
SHORTLIST_FILE = DISCOVERY / "shortlist.md"
PRESS_RELEASE_WORDS = re.compile(
    r"press release|news release|earnings|results", re.IGNORECASE
)
HTML_SUFFIXES = (".htm", ".html")
CLASSES = ("narrative_only", "malformed_layout", "table_heavy", "clean_html")
# Image-only exhibits need OCR (R4.3) and are excluded; a release with native text has
# thousands of visible characters. This only sorts candidates; it is not a quality threshold.
MIN_NATIVE_TEXT_CHARS = 500


@dataclass(frozen=True)
class IndexRow:
    cik: str  # zero-padded, 10 characters (A §264)
    company: str
    form: str
    filed: str
    accession: str

    @property
    def agent(self) -> str:
        """The accession prefix: the CIK of whoever submitted the filing."""
        return self.accession[:10]


@dataclass(frozen=True)
class SubmissionFiling:
    accession: str
    form: str
    filing_date: str
    items: str


@dataclass(frozen=True)
class IndexDocument:
    seq: str
    description: str
    filename: str
    doc_type: str


def master_index_url(year: int, quarter: int) -> str:
    return (
        f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"
    )


def submissions_url(cik: str) -> str:
    return f"https://data.sec.gov/submissions/CIK{cik}.json"


def submissions_page_url(name: str) -> str:
    return f"https://data.sec.gov/submissions/{name}"


def filing_folder(cik: str, accession: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}"


def filing_index_url(cik: str, accession: str) -> str:
    return f"{filing_folder(cik, accession)}/{accession}-index.htm"


def quarter_of(day: str) -> tuple[int, int]:
    parsed = date.fromisoformat(day)
    return parsed.year, (parsed.month - 1) // 3 + 1


def quarter_bounds(year: int, quarter: int) -> tuple[str, str]:
    first = date(year, 3 * quarter - 2, 1)
    after = date(year + 1, 1, 1) if quarter == 4 else date(year, 3 * quarter + 1, 1)
    return first.isoformat(), (after - timedelta(days=1)).isoformat()


def parse_master_index(text: str) -> list[IndexRow]:
    """Rows of a ``master.idx`` file: ``CIK|Company Name|Form Type|Date Filed|Filename``."""
    rows = []
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) != 5 or not parts[0].strip().isdigit():
            continue
        cik, company, form, filed, filename = (part.strip() for part in parts)
        accession = filename.rsplit("/", 1)[-1].removesuffix(".txt")
        rows.append(IndexRow(cik.zfill(10), company, form, filed, accession))
    return rows


def sample_ciks(
    rows: list[IndexRow], *, count: int, rng: random.Random
) -> list[IndexRow]:
    """One 8-K per CIK, spread across filer agents: shuffle agents, then take round-robin."""
    by_agent: dict[str, list[IndexRow]] = defaultdict(list)
    for row in sorted(rows, key=lambda r: (r.agent, r.cik, r.accession)):
        if row.form == "8-K":
            by_agent[row.agent].append(row)
    agents = sorted(by_agent)
    rng.shuffle(agents)
    for agent in agents:
        rng.shuffle(by_agent[agent])
    picked: list[IndexRow] = []
    seen: set[str] = set()
    while len(picked) < count and any(by_agent[agent] for agent in agents):
        for agent in agents:
            while by_agent[agent]:
                row = by_agent[agent].pop()
                if row.cik not in seen:
                    seen.add(row.cik)
                    picked.append(row)
                    break
            if len(picked) == count:
                break
    return picked


def parse_submission_filings(block: dict) -> list[SubmissionFiling]:
    """Rows of a submissions ``filings.recent`` block or an older submissions page."""
    accessions = block["accessionNumber"]
    items = block.get("items") or [""] * len(accessions)
    return [
        SubmissionFiling(accession, form, filing_date, item or "")
        for accession, form, filing_date, item in zip(
            accessions, block["form"], block["filingDate"], items, strict=True
        )
    ]


def older_pages_covering(document: dict, year: int, quarter: int) -> list[str]:
    start, end = quarter_bounds(year, quarter)
    return [
        page["name"]
        for page in document.get("filings", {}).get("files", [])
        if page["filingFrom"] <= end and page["filingTo"] >= start
    ]


def pick_earnings_filing(
    filings: list[SubmissionFiling], year: int, quarter: int
) -> SubmissionFiling | None:
    """The quarter's earliest 8-K whose Items include 2.02."""
    matches = [
        filing
        for filing in filings
        if filing.form == "8-K"
        and "2.02" in [item.strip() for item in filing.items.split(",")]
        and quarter_of(filing.filing_date) == (year, quarter)
    ]
    return min(matches, key=lambda f: (f.filing_date, f.accession), default=None)


def parse_filing_index(html: str) -> list[IndexDocument]:
    """The 'Document Format Files' table of a filing index page."""
    root = lxml.html.document_fromstring(
        html.encode("utf-8"), parser=lxml.html.HTMLParser(encoding="utf-8")
    )
    tables = [
        t
        for t in root.iter("table")
        if "document format files" in (t.get("summary") or "").lower()
    ]
    if not tables:
        tables = [
            t
            for t in root.iter("table")
            if "tablefile" in (t.get("class") or "").lower()
        ]
    documents = []
    for row in tables[0].iter("tr") if tables else []:
        cells = row.findall("td")
        if len(cells) < 4:
            continue
        link = cells[2].find(".//a")
        href = link.get("href", "") if link is not None else ""
        documents.append(
            IndexDocument(
                seq=cells[0].text_content().strip(),
                description=cells[1].text_content().strip(),
                filename=_filename_from_href(href)
                or cells[2].text_content().split()[0],
                doc_type=cells[3].text_content().strip(),
            )
        )
    return documents


def _filename_from_href(href: str) -> str:
    parsed = urlparse(href)
    target = parse_qs(parsed.query).get("doc", [parsed.path])[0]
    return target.rsplit("/", 1)[-1]


def pick_press_release(
    documents: list[IndexDocument],
) -> tuple[IndexDocument | None, str]:
    """Choose the press-release exhibit by exhibit type and description."""
    exhibits = [d for d in documents if d.doc_type.upper().startswith("EX-99")]
    if not exhibits:
        return None, "no EX-99 exhibit"
    described = [d for d in exhibits if PRESS_RELEASE_WORDS.search(d.description)]
    chosen = (
        described[0] if described else (exhibits[0] if len(exhibits) == 1 else None)
    )
    if chosen is None:
        return None, "several EX-99 exhibits and none described as a release"
    if not chosen.filename.lower().endswith(HTML_SUFFIXES):
        return None, f"exhibit is not HTML ({chosen.filename})"
    return chosen, "ok"


@dataclass
class Candidate:
    fixture_id: str
    cik: str
    issuer_name: str
    accession: str
    agent: str
    form: str
    items: str
    filing_date: str
    exhibit_type: str
    exhibit_filename: str
    exhibit_description: str
    url: str
    year: int
    quarter: int
    within_size_cap: bool
    class_tests: dict


class Discovery:
    def __init__(self, fetcher: EdgarFetcher, root: Path = DISCOVERY) -> None:
        self.fetcher = fetcher
        self.root = root
        self.candidates_file = root / "candidates.jsonl"

    def _cached(self, url: str, dest: Path, expected: set[str]) -> bytes:
        if not dest.exists():
            self.fetcher.fetch_and_save(url, dest, expected)
        return dest.read_bytes()

    def known_accessions(self) -> set[str]:
        if not self.candidates_file.exists():
            return set()
        lines = self.candidates_file.read_text(encoding="utf-8").splitlines()
        return {json.loads(line)["accession"] for line in lines if line.strip()}

    def run_year(
        self, year: int, quarter: int, per_year: int, rng: random.Random
    ) -> list[str]:
        """Collect up to ``per_year`` candidates from one quarter; returns skip reasons."""
        index_text = self._cached(
            master_index_url(year, quarter),
            self.root / "index" / f"{year}-QTR{quarter}-master.idx",
            {"text/plain", "application/octet-stream"},
        ).decode("latin-1")
        rows = parse_master_index(index_text)
        known = self.known_accessions()
        skips: list[str] = []
        found = 0
        for row in sample_ciks(rows, count=per_year * 4, rng=rng):
            if found == per_year:
                break
            try:
                reason = self._try_issuer(row, year, quarter, known)
            except UnexpectedResponse as exc:
                reason = f"skipped: {exc}"
            if reason in ("ok", "already recorded"):
                found += 1
            else:
                skips.append(f"{row.cik} {year}Q{quarter}: {reason}")
        return skips

    def _try_issuer(
        self, row: IndexRow, year: int, quarter: int, known: set[str]
    ) -> str:
        sub_dir = self.root / "submissions"
        document = json.loads(
            self._cached(
                submissions_url(row.cik),
                sub_dir / f"CIK{row.cik}.json",
                {"application/json"},
            )
        )
        filings = parse_submission_filings(document["filings"]["recent"])
        filing = pick_earnings_filing(filings, year, quarter)
        if filing is None:
            for name in older_pages_covering(document, year, quarter):
                page = json.loads(
                    self._cached(
                        submissions_page_url(name), sub_dir / name, {"application/json"}
                    )
                )
                filing = pick_earnings_filing(
                    parse_submission_filings(page), year, quarter
                )
                if filing is not None:
                    break
        if filing is None:
            return "no 8-K reporting Item 2.02 in the quarter"
        if filing.accession in known:
            return "already recorded"
        index_dest = self.root / "filings" / filing.accession / "index.htm"
        index_html = self._cached(
            filing_index_url(row.cik, filing.accession), index_dest, {"text/html"}
        )
        exhibit, reason = pick_press_release(
            parse_filing_index(index_html.decode("utf-8", errors="replace"))
        )
        if exhibit is None:
            return reason
        try:
            fid = fixture_id(filing.accession, exhibit.doc_type)
        except ValueError:
            return f"exhibit type {exhibit.doc_type!r} gives no valid fixture id"
        dest = self.root / fid / "source.html"
        url = f"{filing_folder(row.cik, filing.accession)}/{exhibit.filename}"
        raw = self._cached(url, dest, {"text/html"})
        candidate = Candidate(
            fixture_id=fid,
            cik=row.cik,
            issuer_name=row.company,
            accession=filing.accession,
            agent=filing.accession[:10],
            form=filing.form,
            items=filing.items,
            filing_date=filing.filing_date,
            exhibit_type=exhibit.doc_type,
            exhibit_filename=exhibit.filename,
            exhibit_description=exhibit.description,
            url=read_meta(dest).url,
            year=year,
            quarter=quarter,
            within_size_cap=len(raw) <= MAX_FIXTURE_BYTES,
            class_tests=run_class_tests(raw).as_dict(),
        )
        with self.candidates_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(candidate), sort_keys=True) + "\n")
        known.add(filing.accession)
        return "ok"


def load_candidates(path: Path = CANDIDATES_FILE) -> list[Candidate]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Candidate(**json.loads(line)) for line in lines if line.strip()]


def eligible_for_shortlist(candidate: Candidate) -> bool:
    """Within the 1 MiB cap and carrying native text (not an image-only exhibit)."""
    return (
        candidate.within_size_cap
        and candidate.class_tests["visible_chars"] >= MIN_NATIVE_TEXT_CHARS
    )


def suggest(
    candidates: list[Candidate], per_class: int = 3
) -> dict[str, list[Candidate]]:
    """About three per class: mixed agents and years, at most two per issuer, scarcest class first.

    Table-heavy and narrative-only suggestions prefer exhibits that trip no malformed test.
    """
    eligible = [c for c in candidates if eligible_for_shortlist(c)]
    per_issuer: Counter[str] = Counter()
    used: set[str] = set()
    agents: Counter[str] = Counter()
    years: Counter[int] = Counter()
    chosen: dict[str, list[Candidate]] = {}
    for cls in CLASSES:
        pool = [c for c in eligible if c.class_tests[cls] and c.fixture_id not in used]
        picks: list[Candidate] = []
        while len(picks) < per_class:
            options = [c for c in pool if c not in picks and per_issuer[c.cik] < 2]
            if not options:
                break
            prefer_clean = cls in ("table_heavy", "narrative_only")
            best = min(
                options,
                key=lambda c: (
                    prefer_clean and c.class_tests["malformed_layout"],
                    agents[c.agent],
                    years[c.year],
                    c.fixture_id,
                ),
            )
            picks.append(best)
            used.add(best.fixture_id)
            per_issuer[best.cik] += 1
            agents[best.agent] += 1
            years[best.year] += 1
        chosen[cls] = picks
    return chosen


def render_shortlist(candidates: list[Candidate]) -> str:
    suggested = suggest(candidates)
    lines = [
        "# Stage 1 fixture shortlist",
        "",
        (
            f"{len(candidates)} candidates discovered; "
            f"{sum(not c.within_size_cap for c in candidates)} exceed the 1 MiB cap and "
            f"{sum(c.within_size_cap and not eligible_for_shortlist(c) for c in candidates)} "
            f"have under {MIN_NATIVE_TEXT_CHARS} characters of native text; both are excluded."
        ),
        "",
        "Approve eight fixtures (two per class) and two or three development releases in",
        "`expirements/parser-fidelity/approval.toml`. Suggested picks are marked **S**.",
        "",
    ]
    for cls in CLASSES:
        pool = sorted(
            (c for c in candidates if c.class_tests[cls] and eligible_for_shortlist(c)),
            key=lambda c: c.fixture_id,
        )
        lines += [f"## {cls} ({len(pool)} eligible)", ""]
        lines.append(
            "| | fixture_id | issuer | year | agent | exhibit | data share | malformed | stage 4 |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|")
        picks = {c.fixture_id for c in suggested[cls]}
        for c in pool:
            flags = []
            if c.class_tests["narrative_only"]:
                flags.append("narrative-only")
            if c.exhibit_type.upper() != "EX-99.1":
                flags.append("alt numbering")
            lines.append(
                f"| {'**S**' if c.fixture_id in picks else ''} | `{c.fixture_id}` | {c.issuer_name} | {c.year} "
                f"| {c.agent} | {c.exhibit_type} | {c.class_tests['data_table_share']:.2f} "
                f"| {'yes' if c.class_tests['malformed_layout'] else 'no'} | {', '.join(flags)} |"
            )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="live discovery (opt-in)")
    run.add_argument(
        "--live",
        action="store_true",
        help="required: confirms a live, rate-limited run",
    )
    run.add_argument("--years", type=int, nargs="+", default=list(DEFAULT_YEARS))
    run.add_argument("--per-year", type=int, default=DEFAULT_PER_YEAR)
    run.add_argument("--seed", type=int, default=DEFAULT_SEED)
    run.add_argument("--max-requests", type=int, default=DEFAULT_MAX_REQUESTS)
    sub.add_parser(
        "shortlist", help="write data/raw/discovery/shortlist.md from saved candidates"
    )
    args = parser.parse_args(argv)

    if args.command == "shortlist":
        SHORTLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        SHORTLIST_FILE.write_text(
            render_shortlist(load_candidates()) + "\n", encoding="utf-8"
        )
        print(f"wrote {SHORTLIST_FILE}")
        return 0

    if not args.live:
        parser.error("discovery makes live requests; pass --live to confirm")
    if min(args.years) < FIRST_SAMPLED_YEAR:
        parser.error(
            f"Item 2.02 dates from August 2004; sample {FIRST_SAMPLED_YEAR} or later"
        )
    identity = require_identity()
    throttle = Throttle(max_requests=args.max_requests)
    fetcher = EdgarFetcher(identity, throttle=throttle)
    rng = random.Random(args.seed)
    status = 0
    try:
        with LiveLock(LIVE_LOCK):
            discovery = Discovery(fetcher)
            for year in args.years:
                quarter = 1 + (args.seed + year) % 4
                for skip in discovery.run_year(year, quarter, args.per_year, rng):
                    print(skip)
    except LivePolicyStop as exc:
        print(f"STOPPED: {exc}", file=sys.stderr)
        status = 1
    finally:
        fetcher.close()
        print(f"requests made: {throttle.count}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_discover.py --import-mode=prepend -q`
Expected: `12 passed`.

- [x] **Step 5: Lock, lint, and commit**

```bash
uv lock --script expirements/parser-fidelity/discover.py
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/discover.py expirements/parser-fidelity/discover.py.lock expirements/parser-fidelity/test_discover.py
git commit -m "feat(parser-fidelity): add Item 2.02 exhibit discovery and shortlist"
```

---

### Task 6: Live discovery, shortlist, and gate A (fixture approval)

**Files:**
- Create: `expirements/parser-fidelity/approval.toml` (written by the user; committed in Task 7)

**Interfaces:**
- Consumes: `discover.py` (Task 5) and `EDGAR_IDENTITY` (the identity gate).
- Produces: `approval.toml`, holding eight `[[fixtures]]` entries (`fixture_id`,
  `primary_class`), two or three `[[devset]]` entries, `approved_by`, `approved_on`,
  and `short_classes`.

- [x] **Step 1: Smoke-test discovery live (at most 20 requests)**

Run: `uv run --locked --script expirements/parser-fidelity/discover.py run --live --years 2025 --per-year 1 --max-requests 20`

Expected:

- zero or more skip lines, then `requests made: N` with N at most 20;
- `data/raw/discovery/candidates.jsonl` holds one line;
- `data/raw/discovery/index/2025-QTR*-master.idx` exists.

The parsers were written against synthetic copies of EDGAR's formats, so if this step
fails, adapt them to the saved response:

1. On a `KeyError` or `TypeError` while reading submissions, open the saved JSON
   under `data/raw/discovery/submissions/`.
2. If an index page yields no documents, open
   `data/raw/discovery/filings/<accession>/index.htm`.
3. Reproduce the failure in `test_discover.py` with a synthetic snippet of the real
   structure. Do not copy the saved file into the test.
4. Fix the parser and rerun Step 4 of Task 5 and this step.

Commit any fix with `fix(parser-fidelity): …`.

- [x] **Step 2: Run the full discovery**

Run: `uv run --locked --script expirements/parser-fidelity/discover.py run --live`

Expected: `requests made: N`. N is at most 500 per run; record it.

If the run prints `STOPPED: request budget of 500 reached`, rerun the same command.
Saved responses are reused and recorded accessions are skipped, so each rerun only
continues. Stop rerunning when a run finds nothing new. Each run's request count goes
into the handoff.

- [x] **Step 3: Build the shortlist**

Run: `uv run --locked --script expirements/parser-fidelity/discover.py shortlist`

Expected: `wrote …/data/raw/discovery/shortlist.md`, with one section per class listing
eligible candidates and suggested picks marked **S**.

If a class has fewer than two eligible candidates, apply the spec's contingency:

1. Widen the sample, for example
   `discover.py run --live --years 2006 2009 2012 2015 2018 2021 2024`, and rebuild
   the shortlist.
2. If the class is still short, ask the user to choose between one fixture for that
   class, recorded as a limitation through `short_classes`, and relaxing a shortlist
   preference.

- [x] **Step 4: Gate A — the user approves the fixtures and the development set**

Give the user `data/raw/discovery/shortlist.md` and this template for
`expirements/parser-fidelity/approval.toml`:

```toml
# Stage 1 fixture approval (specs/release-parser-fidelity.md: Selection; decisions F3, F4).
# Written by the user from data/raw/discovery/shortlist.md. promote_fixtures.py enforces
# two fixtures per class (one only for a class listed in short_classes), a class-test
# match for each primary_class, at most two fixtures per issuer, the 1 MiB cap, and a
# development set of two or three releases disjoint from the fixtures.
approved_by = "Your Name"
approved_on = 2026-09-24
short_classes = []

[[fixtures]]
fixture_id = "<accession>_<exhibit type>, copied from the shortlist"
primary_class = "clean_html"

[[fixtures]]
fixture_id = "..."
primary_class = "clean_html"

[[fixtures]]
fixture_id = "..."
primary_class = "malformed_layout"

[[fixtures]]
fixture_id = "..."
primary_class = "malformed_layout"

[[fixtures]]
fixture_id = "..."
primary_class = "table_heavy"

[[fixtures]]
fixture_id = "..."
primary_class = "table_heavy"

[[fixtures]]
fixture_id = "..."
primary_class = "narrative_only"

[[fixtures]]
fixture_id = "..."
primary_class = "narrative_only"

[[devset]]
fixture_id = "..."

[[devset]]
fixture_id = "..."
```

The user approves eight fixtures, two per class, and two or three development releases.
The spec's preferences apply:

- HTML with native text only;
- a mix of filer agents and years;
- no issuer with more than two fixtures;
- where possible, a narrative-only release and a release filed under an exhibit number
  other than EX-99.1, for Stage 4;
- clean fixtures trip no malformed-layout test, and table-heavy and narrative-only
  fixtures should trip none either.

Wait for the user to write the file, or to dictate the IDs for you to write verbatim.
Do not choose fixtures on the user's behalf.

- [x] **Step 5: Check the approval parses**

Run: `uv run --locked --all-packages python -c "import tomllib, pathlib; a = tomllib.loads(pathlib.Path('expirements/parser-fidelity/approval.toml').read_text()); print(len(a['fixtures']), len(a['devset']))"`
Expected: `8 2` or `8 3`. With a short class, the first number is 7 or fewer.
Task 7 checks the rest.

---

### Task 7: Fixture promotion, `.gitattributes`, and the manifest

**Files:**
- Create: `expirements/parser-fidelity/pf_toml.py`
- Create: `expirements/parser-fidelity/promote_fixtures.py`
- Create: `.gitattributes`
- Create (generated): `tests/fixtures/releases/<fixture_id>/source.html` ×8,
  `tests/fixtures/releases/manifest.toml`
- Commit: `expirements/parser-fidelity/approval.toml` (from Task 6)
- Test: `expirements/parser-fidelity/test_promote_fixtures.py`

**Interfaces:**
- Consumes:
  - `data/raw/discovery/candidates.jsonl`, and each
    `data/raw/discovery/<id>/source.html` with its `.meta.json` (Task 6);
  - `approval.toml` (Task 6);
  - `pf_paths` (Task 1).
- Produces:
  - `pf_toml.Bare(text)` and `pf_toml.toml_value(value) -> str`;
  - `promote_fixtures.promote(approval_path, discovery, fixtures_root, devset_root) -> list[str]`;
  - `PromotionError`;
  - the corpus and its `manifest.toml`. Each `[[fixtures]]` entry carries:
    - `fixture_id`, `primary_class`, `issuer_name`, `cik`, `accession`, `form`,
      `items`, `filing_date`;
    - `exhibit_type`, `exhibit_filename`, `url`, `retrieved_at`, `http_status`,
      `content_type`, `bytes`, `sha256`;
    - `source_id`, `redistribution_basis`, `stage4_flags`, `pilot_split`;
    - a `[fixtures.class_tests]` table.
  - `data/raw/devset/<id>/source.html` for each development release (never committed).

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_promote_fixtures.py`:

```python
import hashlib
import json

import pytest
import tomllib
from pf_toml import toml_value
from promote_fixtures import PromotionError, promote

CLASSES = ("clean_html", "malformed_layout", "table_heavy", "narrative_only")


def write_candidate(discovery, fid, cik, cls, exhibit_type="EX-99.1"):
    body = f"<html><body><p>{fid}</p></body></html>".encode()
    folder = discovery / fid
    folder.mkdir(parents=True)
    (folder / "source.html").write_bytes(body)
    meta = {
        "url": f"https://www.sec.gov/Archives/{fid}.htm",
        "retrieved_at": "2026-09-23T10:00:00Z",
        "http_status": 200,
        "content_type": "text/html",
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    (folder / "source.html.meta.json").write_text(json.dumps(meta))
    tests = {name: name == cls for name in CLASSES}
    tests["clean_html"] = cls != "malformed_layout"
    tests["malformed_layout"] = cls == "malformed_layout"
    tests["data_table_share"] = 0.61
    return {
        "fixture_id": fid,
        "cik": cik,
        "issuer_name": f"Issuer {cik}",
        "accession": fid.split("_")[0],
        "agent": fid[:10],
        "form": "8-K",
        "items": "2.02,9.01",
        "filing_date": "2025-01-30",
        "exhibit_type": exhibit_type,
        "exhibit_filename": "ex99.htm",
        "exhibit_description": "PRESS RELEASE",
        "url": meta["url"],
        "year": 2025,
        "quarter": 1,
        "within_size_cap": True,
        "class_tests": tests,
    }


@pytest.fixture
def layout(tmp_path):
    discovery = tmp_path / "discovery"
    records, approval = [], ['approved_by = "Tester"', "approved_on = 2026-09-24", ""]
    for number in range(10):
        cls = CLASSES[number % 4]
        fid = f"000000000{number}-25-00000{number}_ex-99-1"
        records.append(write_candidate(discovery, fid, cik=f"{number:010d}", cls=cls))
        if number < 8:
            approval += [
                "[[fixtures]]",
                f'fixture_id = "{fid}"',
                f'primary_class = "{cls}"',
                "",
            ]
        else:
            approval += ["[[devset]]", f'fixture_id = "{fid}"', ""]
    (discovery / "candidates.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in records)
    )
    approval_path = tmp_path / "approval.toml"
    approval_path.write_text("\n".join(approval))
    return tmp_path, discovery, approval_path


def run(layout):
    root, discovery, approval_path = layout
    return promote(approval_path, discovery, root / "fixtures", root / "devset")


def test_promote_copies_bytes_and_writes_a_parsable_manifest(layout):
    root, discovery, _ = layout
    promoted = run(layout)
    assert len(promoted) == 8
    manifest = tomllib.loads((root / "fixtures" / "manifest.toml").read_text())
    entry = manifest["fixtures"][0]
    fid = entry["fixture_id"]
    assert (root / "fixtures" / fid / "source.html").read_bytes() == (
        discovery / fid / "source.html"
    ).read_bytes()
    assert entry["cik"] == "0000000000"
    assert entry["source_id"] == "sec-edgar"
    assert entry["pilot_split"] == "train_or_exclude"
    assert str(entry["filing_date"]) == "2025-01-30"
    assert entry["retrieved_at"].tzinfo is not None
    assert entry["class_tests"]["data_table_share"] == 0.61
    assert sorted(p.name for p in (root / "devset").iterdir()) == sorted(
        f"000000000{n}-25-00000{n}_ex-99-1" for n in (8, 9)
    )


def test_promote_is_idempotent(layout):
    assert run(layout) == run(layout)


def test_stage4_flags(layout):
    root = layout[0]
    run(layout)
    flags = {
        e["primary_class"]: e["stage4_flags"]
        for e in tomllib.loads((root / "fixtures" / "manifest.toml").read_text())[
            "fixtures"
        ]
    }
    assert flags["narrative_only"] == ["narrative_only_release"]
    assert flags["table_heavy"] == []


def test_wrong_class_count_and_mismatched_class_are_rejected(layout):
    approval_path = layout[2]
    text = approval_path.read_text().replace(
        'primary_class = "table_heavy"', 'primary_class = "clean_html"', 1
    )
    approval_path.write_text(text)
    with pytest.raises(PromotionError) as excinfo:
        run(layout)
    message = str(excinfo.value)
    assert "class table_heavy: 1 fixtures approved, expected 2" in message
    assert (
        "class tests do not support primary_class 'clean_html'" not in message
    )  # table-heavy fixtures here are clean


def test_tampered_bytes_are_rejected(layout):
    _, discovery, _ = layout
    victim = discovery / "0000000000-25-000000_ex-99-1" / "source.html"
    victim.write_bytes(victim.read_bytes() + b" ")
    with pytest.raises(PromotionError, match="do not match"):
        run(layout)


def test_toml_value_escapes_strings():
    assert (
        tomllib.loads("x = " + toml_value('A "quoted" \\ name\n'))["x"]
        == 'A "quoted" \\ name\n'
    )
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_promote_fixtures.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'pf_toml'`.

- [x] **Step 3: Write the implementation**

`expirements/parser-fidelity/pf_toml.py`:

```python
"""A minimal TOML writer for the harness's generated files (the standard library only reads TOML)."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Bare:
    """A TOML value written without quotes (dates and datetimes)."""

    text: str


def toml_value(value: object) -> str:
    if isinstance(value, Bare):
        return value.text
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)  # a valid TOML basic string
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    raise TypeError(f"cannot write {type(value).__name__} as TOML")
```

`expirements/parser-fidelity/promote_fixtures.py`:

```python
"""Copy approved discovery responses into the fixture corpus and write its manifest.

    uv run --locked --all-packages python expirements/parser-fidelity/promote_fixtures.py

Reads the user's approval (expirements/parser-fidelity/approval.toml) and the discovery
records (data/raw/discovery/candidates.jsonl). Each approved exhibit is copied
byte-for-byte into tests/fixtures/releases/<fixture_id>/source.html after its sha256 is
checked against the saved response metadata, so the recorded class tests ran on exactly
the committed bytes. Development releases are copied to data/raw/devset/ and never
committed. Standard library only.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import tomllib
from pf_paths import DEVSET, DISCOVERY, FIXTURES, HARNESS, MAX_FIXTURE_BYTES
from pf_toml import Bare, toml_value

APPROVAL = HARNESS / "approval.toml"
PRIMARY_CLASSES = ("clean_html", "malformed_layout", "table_heavy", "narrative_only")
FIXTURES_PER_CLASS = 2
SOURCE_ID = "sec-edgar"
REDISTRIBUTION_BASIS = (
    "docs/source-register.toml entry sec-edgar: the SEC's quoted website reuse policy. That policy "
    "does not address issuers' copyright in their filings; the register draws no conclusion about it."
)
PILOT_SPLIT = "train_or_exclude"


class PromotionError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _meta(source: Path) -> dict:
    return json.loads(
        source.with_name(source.name + ".meta.json").read_text(encoding="utf-8")
    )


def check_approval(approval: dict, candidates: dict[str, dict]) -> None:
    fixtures = approval.get("fixtures", [])
    devset = [entry["fixture_id"] for entry in approval.get("devset", [])]
    short = set(approval.get("short_classes", []))
    problems = []
    for entry in fixtures:
        fid, cls = entry["fixture_id"], entry["primary_class"]
        record = candidates.get(fid)
        if record is None:
            problems.append(f"{fid}: not among the discovery candidates")
            continue
        if cls not in PRIMARY_CLASSES:
            problems.append(f"{fid}: unknown primary_class {cls!r}")
        elif not record["class_tests"][cls]:
            problems.append(f"{fid}: class tests do not support primary_class {cls!r}")
        if not record["within_size_cap"]:
            problems.append(f"{fid}: exceeds the 1 MiB cap")
    per_class = Counter(entry["primary_class"] for entry in fixtures)
    for cls in PRIMARY_CLASSES:
        expected = 1 if cls in short else FIXTURES_PER_CLASS
        if per_class[cls] != expected:
            problems.append(
                f"class {cls}: {per_class[cls]} fixtures approved, expected {expected}"
            )
    per_issuer = Counter(
        candidates[e["fixture_id"]]["cik"]
        for e in fixtures
        if e["fixture_id"] in candidates
    )
    problems += [
        f"issuer {cik}: {n} fixtures (at most 2)"
        for cik, n in per_issuer.items()
        if n > 2
    ]
    if not 2 <= len(devset) <= 3:
        problems.append(
            f"development set has {len(devset)} releases; approve two or three"
        )
    overlap = set(devset) & {entry["fixture_id"] for entry in fixtures}
    problems += [
        f"{fid}: in both the fixtures and the development set"
        for fid in sorted(overlap)
    ]
    problems += [
        f"{fid}: development release not among the discovery candidates"
        for fid in devset
        if fid not in candidates
    ]
    if problems:
        raise PromotionError("\n".join(problems))


def _copy_verified(source: Path, dest: Path) -> dict:
    meta = _meta(source)
    if _sha256(source) != meta["sha256"] or source.stat().st_size != meta["bytes"]:
        raise PromotionError(
            f"{source}: bytes do not match the saved response metadata"
        )
    if dest.exists():
        if _sha256(dest) != meta["sha256"]:
            raise PromotionError(
                f"{dest} exists with different bytes; refusing to overwrite"
            )
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    if _sha256(dest) != meta["sha256"]:
        raise PromotionError(f"{dest}: copy does not match the saved response")
    return meta


def manifest_entry(record: dict, primary_class: str, meta: dict) -> list[str]:
    flags = []
    if record["class_tests"]["narrative_only"]:
        flags.append("narrative_only_release")
    if record["exhibit_type"].strip().upper() != "EX-99.1":
        flags.append("alternative_exhibit_numbering")
    fields: list[tuple[str, object]] = [
        ("fixture_id", record["fixture_id"]),
        ("primary_class", primary_class),
        ("issuer_name", record["issuer_name"]),
        ("cik", record["cik"]),
        ("accession", record["accession"]),
        ("form", record["form"]),
        ("items", record["items"]),
        ("filing_date", Bare(record["filing_date"])),
        ("exhibit_type", record["exhibit_type"]),
        ("exhibit_filename", record["exhibit_filename"]),
        ("url", meta["url"]),
        ("retrieved_at", Bare(meta["retrieved_at"])),
        ("http_status", meta["http_status"]),
        ("content_type", meta["content_type"]),
        ("bytes", meta["bytes"]),
        ("sha256", meta["sha256"]),
        ("source_id", SOURCE_ID),
        ("redistribution_basis", REDISTRIBUTION_BASIS),
        ("stage4_flags", flags),
        ("pilot_split", PILOT_SPLIT),
    ]
    lines = ["[[fixtures]]"] + [f"{key} = {toml_value(value)}" for key, value in fields]
    lines += ["", "[fixtures.class_tests]"]
    lines += [
        f"{key} = {toml_value(value)}" for key, value in record["class_tests"].items()
    ]
    return lines


def promote(
    approval_path: Path = APPROVAL,
    discovery: Path = DISCOVERY,
    fixtures_root: Path = FIXTURES,
    devset_root: Path = DEVSET,
) -> list[str]:
    approval = tomllib.loads(approval_path.read_text(encoding="utf-8"))
    lines = (discovery / "candidates.jsonl").read_text(encoding="utf-8").splitlines()
    candidates = {
        record["fixture_id"]: record
        for record in map(json.loads, filter(str.strip, lines))
    }
    check_approval(approval, candidates)

    manifest = [
        "# Provenance for the Stage 1 release fixtures (specs/release-parser-fidelity.md).",
        "# Generated by expirements/parser-fidelity/promote_fixtures.py from approval.toml.",
        "schema_version = 1",
        "",
    ]
    for entry in sorted(approval["fixtures"], key=lambda e: e["fixture_id"]):
        fid = entry["fixture_id"]
        meta = _copy_verified(
            discovery / fid / "source.html", fixtures_root / fid / "source.html"
        )
        if meta["bytes"] > MAX_FIXTURE_BYTES:
            raise PromotionError(f"{fid}: {meta['bytes']} bytes exceeds the 1 MiB cap")
        manifest += manifest_entry(candidates[fid], entry["primary_class"], meta) + [""]
    for entry in approval.get("devset", []):
        fid = entry["fixture_id"]
        source = discovery / fid / "source.html"
        dest = devset_root / fid / "source.html"
        _copy_verified(source, dest)
        shutil.copyfile(
            source.with_name("source.html.meta.json"),
            dest.with_name("source.html.meta.json"),
        )
    text = "\n".join(manifest).rstrip("\n") + "\n"
    tomllib.loads(text)  # the generated manifest must parse
    (fixtures_root / "manifest.toml").write_text(text, encoding="utf-8")
    return sorted(entry["fixture_id"] for entry in approval["fixtures"])


def main() -> int:
    try:
        promoted = promote()
    except PromotionError as exc:
        print(f"approval rejected:\n{exc}", file=sys.stderr)
        return 1
    print(f"promoted {len(promoted)} fixtures: {', '.join(promoted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_promote_fixtures.py --import-mode=prepend -q`
Expected: `6 passed`.

- [x] **Step 5: Put `.gitattributes` in place before any fixture is staged**

Create `.gitattributes` at the repository root with exactly this line:

```text
tests/fixtures/releases/*/source.html -text
```

Git reads attributes when a file is added, so this must exist before Step 7 stages the
sources. With `-text`, Git never rewrites line endings, so each committed sha256 stays
valid.

- [x] **Step 6: Promote the approved releases**

Run: `uv run --locked --all-packages python expirements/parser-fidelity/promote_fixtures.py`

Expected: `promoted 8 fixtures: …` (fewer with a short class). If it prints
`approval rejected:`, show the listed problems to the user; the approval is theirs to
change. Then check the attribute and the byte counts:

```bash
git check-attr text -- tests/fixtures/releases/*/source.html
```

Expected: every line ends `: text: unset`.

```bash
ls -l tests/fixtures/releases/*/source.html
```

Expected: every size is at most 1048576 bytes.

- [x] **Step 7: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add .gitattributes
git add expirements/parser-fidelity/pf_toml.py expirements/parser-fidelity/promote_fixtures.py expirements/parser-fidelity/test_promote_fixtures.py expirements/parser-fidelity/approval.toml tests/fixtures/releases
git status --short
git commit -m "test(fixtures): add the approved Stage 1 release corpus and manifest"
```

In `git status --short`, the staged files must be exactly `.gitattributes`, the three
harness files, `approval.toml`, `manifest.toml`, and the eight `source.html` files.
Nothing under `data/` may appear.

---

### Task 8: Gold validator

**Files:**
- Create: `expirements/parser-fidelity/validate_gold.py`
- Test: `expirements/parser-fidelity/test_validate_gold.py`

**Interfaces:**
- Consumes: `pf_decode.decode_html_bytes`, `pf_space.*`, and
  `pf_text.extract_document_text` (Task 1).
- Produces:
  - **Block types.** `TEXT_TYPES` is `{"heading", "paragraph", "list_item",
    "footnote"}`.
  - **Source text.** `SourceText(raw: bytes)` has `.decoded`, `.primary`,
    `.fallback`, `.count(form)`, `.count_fallback(form)`, and `.count_casefold(form)`.
  - **Gold loading.** `load_gold(fixture_dir) -> dict`.
  - **Checks.** `check_schema(gold, fixture_id) -> list[str]`, `text_anchors(block)`,
    and `check_anchors(gold, source) -> (errors, warnings, unanchorable)`.
  - **Entry points.** `validate_fixture(fixture_dir) -> Report`, where `Report` has
    `.errors`, `.warnings`, `.unanchorable`, `.encoding`, `.encoding_basis`,
    `.ascii_only`, and `.ok`. Also `init_skeleton(fixture_dir) -> Path`.
  - **CLI.** `validate_gold.py DIR [DIR ...]` and `validate_gold.py --init DIR`.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_validate_gold.py`:

```python
import pytest
from validate_gold import init_skeleton, main, validate_fixture

FID = "0001234567-25-000123_ex-99-1"
SOURCE = """<html><head><title>Acme</title></head><body>
<p><b>ACME REPORTS THIRD QUARTER RESULTS</b></p>
<p>Acme Corp. today reported net sales of $4.3 billion for the quarter, up 5 percent.</p>
<p>Outlook</p>
<p style="text-transform: uppercase">guidance is unchanged for the year.</p>
<table>
<tr><td></td><td>Three Months Ended</td><td></td></tr>
<tr><td></td><td>2025</td><td>2024</td></tr>
<tr><td>Net sales</td><td>4,321</td><td>3,210</td></tr>
<tr><td>Cost of sales</td><td>2,109</td><td>1,987</td></tr>
</table>
<p>(1) Excludes the impact of the divestiture completed in the second quarter.</p>
<p>Outlook</p>
</body></html>"""

HEADER = f"""schema_version = 1
fixture_id = "{FID}"
annotator = "Tester"
marked_from = "browser rendering"
browser = "Firefox 140"
completed = 2026-10-01
"""

GOOD_BLOCKS = """
[[blocks]]
id = "b001"
type = "heading"
level = 1
start = "ACME REPORTS THIRD QUARTER RESULTS"

[[blocks]]
id = "b002"
type = "paragraph"
start = "Acme Corp. today reported"
end = "for the quarter, up 5 percent."

[[blocks]]
id = "t001"
type = "table"
headers = ["Three Months Ended", "2025", "2024"]
cells = [
  { role = "corner", text = "4,321", row_header = "Net sales", col_header = "2025" },
  { role = "right", text = "3,210", row_header = "Net sales", col_header = "2024" },
  { role = "below", text = "2,109", row_header = "Cost of sales", col_header = "2025" },
]

[[blocks]]
id = "b003"
type = "footnote"
start = "Excludes the impact of the divestiture"
end = "completed in the second quarter."
"""


def fixture(tmp_path, blocks, header=HEADER):
    folder = tmp_path / FID
    folder.mkdir()
    (folder / "source.html").write_text(SOURCE, encoding="utf-8")
    (folder / "gold.toml").write_text(header + blocks, encoding="utf-8")
    return folder


def test_valid_gold_passes(tmp_path):
    report = validate_fixture(fixture(tmp_path, GOOD_BLOCKS))
    assert report.errors == []
    assert report.encoding == "UTF-8" and report.ascii_only


def test_schema_errors_are_reported(tmp_path):
    blocks = """
[[blocks]]
id = "b1"
type = "sidebar"
start = "x"

[[blocks]]
id = "b1"
type = "paragraph"
level = 2
strat = "typo"
"""
    errors = validate_fixture(fixture(tmp_path, blocks)).errors
    assert any("type must be one of" in e for e in errors)
    assert any("duplicate id" in e for e in errors)
    assert any("level must be a positive integer" in e for e in errors)
    assert any("key 'strat' is not allowed" in e for e in errors)


def test_table_needs_one_cell_per_role(tmp_path):
    blocks = GOOD_BLOCKS.replace('role = "right"', 'role = "corner"')
    errors = validate_fixture(fixture(tmp_path, blocks)).errors
    assert any("exactly one each of roles" in e for e in errors)


def test_duplicate_and_missing_anchors_are_errors_with_case_hints(tmp_path):
    blocks = """
[[blocks]]
id = "b001"
type = "heading"
start = "Outlook"

[[blocks]]
id = "b002"
type = "paragraph"
start = "GUIDANCE IS UNCHANGED FOR THE YEAR."
"""
    errors = validate_fixture(fixture(tmp_path, blocks)).errors
    assert any("b001: start: occurs 2 times" in e for e in errors)
    assert any("b002: start: not found (case-insensitive hits: 1" in e for e in errors)


def test_after_disambiguates_a_short_repeated_block(tmp_path):
    blocks = """
[[blocks]]
id = "b001"
type = "heading"
start = "Outlook"
after = "guidance is unchanged"
"""
    assert validate_fixture(fixture(tmp_path, blocks)).errors == []


def test_short_anchor_with_an_end_is_an_error(tmp_path):
    blocks = """
[[blocks]]
id = "b001"
type = "paragraph"
start = "Acme Corp."
end = "for the quarter, up 5 percent."
"""
    errors = validate_fixture(fixture(tmp_path, blocks)).errors
    assert any("start is shorter than four words" in e for e in errors)


def test_order_and_marker_warnings(tmp_path):
    blocks = """
[[blocks]]
id = "b001"
type = "paragraph"
start = "for the quarter, up 5 percent."
end = "Acme Corp. today reported net sales"

[[blocks]]
id = "b002"
type = "footnote"
start = "(1) Excludes the impact of"
end = "completed in the second quarter."
"""
    report = validate_fixture(fixture(tmp_path, blocks))
    assert report.errors == []
    assert any("b001: end precedes start" in w for w in report.warnings)
    assert any(
        "b002: start may begin with a bullet or marker" in w for w in report.warnings
    )


def test_unanchorable_block_must_repeat(tmp_path):
    blocks = """
[[blocks]]
id = "b001"
type = "heading"
start = "Outlook"
unanchorable = true

[[blocks]]
id = "b002"
type = "heading"
start = "ACME REPORTS THIRD QUARTER RESULTS"
unanchorable = true
"""
    report = validate_fixture(fixture(tmp_path, blocks))
    assert report.unanchorable == 2
    assert report.errors == ["block b002: unanchorable text must occur at least twice"]


def test_init_writes_a_skeleton_that_fails_until_filled(tmp_path):
    folder = tmp_path / FID
    folder.mkdir()
    (folder / "source.html").write_text(SOURCE, encoding="utf-8")
    init_skeleton(folder)
    with pytest.raises(FileExistsError):
        init_skeleton(folder)
    errors = validate_fixture(folder).errors
    assert "missing top-level key 'blocks'" in errors
    assert main([str(folder)]) == 1
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_validate_gold.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'validate_gold'`.

- [x] **Step 3: Write the implementation**

`expirements/parser-fidelity/validate_gold.py`:

```python
"""Validate hand-marked gold structure (spec: Gold annotation > Validator). Standard library only.

    uv run --locked --all-packages python expirements/parser-fidelity/validate_gold.py tests/fixtures/releases/<id> [...]
    uv run --locked --all-packages python expirements/parser-fidelity/validate_gold.py --init tests/fixtures/releases/<id>

The source text comes from the standard library's ``html.parser`` (pf_text), which is
independent of every candidate. Errors block scoring; warnings do not.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import tomllib
from pf_decode import decode_html_bytes
from pf_space import fallback_space, find_all, primary_space
from pf_text import extract_document_text

TEXT_TYPES = frozenset({"heading", "paragraph", "list_item", "footnote"})
BLOCK_TYPES = TEXT_TYPES | {"table", "page_artifact"}
LEVEL_TYPES = frozenset({"heading", "list_item"})
CELL_ROLES = ("corner", "right", "below")
TOP_KEYS = frozenset(
    {
        "schema_version",
        "fixture_id",
        "annotator",
        "marked_from",
        "browser",
        "completed",
        "blocks",
    }
)
TEXT_KEYS = frozenset({"id", "type", "level", "start", "end", "after", "unanchorable"})
TABLE_KEYS = frozenset({"id", "type", "headers", "cells"})
ARTIFACT_KEYS = frozenset({"id", "type", "start"})
CELL_KEYS = frozenset({"role", "text", "row_header", "col_header"})
MIN_ANCHOR_WORDS = 4
MIN_ANCHOR_CHARS = 20
_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_LEADING_MARKER = re.compile(
    r"^\s*(?:[\u2022\u25cf\u25e6\u25aa\u25a0\xb7*\u2020\u2021\xa7]|\(?\d{1,2}\)|\([a-z]\))\s"
)

SKELETON = """schema_version = 1
fixture_id = "{fixture_id}"
annotator = ""
marked_from = "browser rendering"
browser = ""
# completed = YYYY-MM-DD   (add when the file is finished)

# One [[blocks]] entry per rendered block, in rendered reading order. Example:
# [[blocks]]
# id = "b001"
# type = "heading"
# level = 1
# start = "first words of the block"
"""


@dataclass
class Report:
    fixture_id: str
    encoding: str = ""
    encoding_basis: str = ""
    ascii_only: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unanchorable: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


class SourceText:
    """A fixture's validator text in both matching spaces."""

    def __init__(self, raw: bytes) -> None:
        decoded = decode_html_bytes(raw)
        self.decoded = decoded
        text = extract_document_text(decoded.text)
        self.primary = primary_space(text)
        self.fallback = fallback_space(text)
        self.casefolded = self.primary.casefold()

    def count(self, anchor: str) -> int:
        return len(find_all(self.primary, anchor)) if anchor else 0

    def count_fallback(self, anchor: str) -> int:
        return len(find_all(self.fallback, anchor)) if anchor else 0

    def count_casefold(self, anchor: str) -> int:
        return len(find_all(self.casefolded, anchor.casefold())) if anchor else 0


def load_gold(fixture_dir: Path) -> dict:
    return tomllib.loads((fixture_dir / "gold.toml").read_text(encoding="utf-8"))


def _short(anchor: str) -> bool:
    return len(anchor.split()) < MIN_ANCHOR_WORDS and len(anchor) < MIN_ANCHOR_CHARS


def _nonempty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check_schema(gold: dict, fixture_id: str) -> list[str]:
    errors = [f"unknown top-level key {key!r}" for key in sorted(set(gold) - TOP_KEYS)]
    errors += [f"missing top-level key {key!r}" for key in sorted(TOP_KEYS - set(gold))]
    if gold.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if gold.get("fixture_id") != fixture_id:
        errors.append(f"fixture_id must be {fixture_id!r}")
    for key in ("annotator", "browser"):
        if key in gold and not _nonempty_str(gold[key]):
            errors.append(f"{key} must be a non-empty string")
    if gold.get("marked_from", "browser rendering") != "browser rendering":
        errors.append('marked_from must be "browser rendering"')
    if "completed" in gold and not isinstance(gold["completed"], dt.date):
        errors.append("completed must be a date such as 2026-10-01")
    blocks = gold.get("blocks", [])
    if not isinstance(blocks, list) or not blocks:
        return errors + ["blocks must be a non-empty array of tables"]
    seen: set[str] = set()
    for position, block in enumerate(blocks, start=1):
        errors += [
            f"block {block.get('id', f'#{position}')}: {e}"
            for e in _check_block(block, seen)
        ]
    return errors


def _check_block(block: dict, seen: set[str]) -> list[str]:
    errors = []
    block_id, kind = block.get("id"), block.get("type")
    if not isinstance(block_id, str) or not _ID.match(block_id):
        errors.append("id must be letters, digits, '-' or '_'")
    elif block_id in seen:
        errors.append("duplicate id")
    else:
        seen.add(block_id)
    if kind not in BLOCK_TYPES:
        return errors + [f"type must be one of {sorted(BLOCK_TYPES)}"]
    allowed = (
        TEXT_KEYS
        if kind in TEXT_TYPES
        else TABLE_KEYS
        if kind == "table"
        else ARTIFACT_KEYS
    )
    errors += [
        f"key {key!r} is not allowed on a {kind}"
        for key in sorted(set(block) - allowed)
    ]
    if "level" in block and (
        kind not in LEVEL_TYPES
        or not isinstance(block["level"], int)
        or block["level"] < 1
    ):
        errors.append(
            "level must be a positive integer, and only on headings and list items"
        )
    if kind == "table":
        return errors + _check_table(block)
    if not _nonempty_str(block.get("start")):
        errors.append("start must be a non-empty string")
    for key in ("end", "after"):
        if key in block and not _nonempty_str(block[key]):
            errors.append(f"{key} must be a non-empty string")
    if "unanchorable" in block and not isinstance(block["unanchorable"], bool):
        errors.append("unanchorable must be true or false")
    if "after" in block and "end" in block:
        errors.append("a block with after omits end")
    if block.get("unanchorable") and "end" in block:
        errors.append("an unanchorable block puts its full text in start and omits end")
    if kind in TEXT_TYPES and not block.get("unanchorable") and not errors:
        if "end" in block and _short(block["start"]):
            errors.append(
                "start is shorter than four words and 20 characters but the block has an end"
            )
        if "end" in block and _short(block["end"]):
            errors.append("end is shorter than four words and 20 characters")
    return errors


def _check_table(block: dict) -> list[str]:
    errors = []
    headers = block.get("headers")
    if not isinstance(headers, list) or not all(_nonempty_str(h) for h in headers):
        errors.append("headers must be an array of non-empty strings")
    cells = block.get("cells")
    if not isinstance(cells, list) or len(cells) != 3:
        return errors + ["cells must hold exactly three cells"]
    roles = []
    for cell in cells:
        if (
            not isinstance(cell, dict)
            or set(cell) != CELL_KEYS
            or not all(_nonempty_str(cell[k]) for k in CELL_KEYS)
        ):
            errors.append(
                "each cell needs non-empty role, text, row_header, and col_header"
            )
            continue
        roles.append(cell["role"])
    if sorted(roles) != sorted(CELL_ROLES) and len(roles) == 3:
        errors.append("cells must have exactly one each of roles corner, right, below")
    return errors


def text_anchors(block: dict) -> list[tuple[str, str]]:
    """(label, raw anchor) pairs a text block is matched by; a block with after matches start+after."""
    if "after" in block:
        return [("start+after", block["start"] + block["after"])]
    anchors = [("start", block["start"])]
    if "end" in block:
        anchors.append(("end", block["end"]))
    return anchors


def check_anchors(gold: dict, source: SourceText) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    unanchorable = 0
    for block in gold["blocks"]:
        block_id, kind = block["id"], block["type"]
        if kind == "page_artifact":
            continue
        if kind == "table":
            for cell in block["cells"]:
                errors += _unique(
                    source, f"block {block_id}: cell {cell['role']}", cell["text"]
                )
            for header in block["headers"]:
                if source.count(primary_space(header)) == 0:
                    errors.append(
                        f"block {block_id}: header {header!r} not found{_case_hint(source, header)}"
                    )
            continue
        if block.get("unanchorable"):
            unanchorable += 1
            probe = block["start"] + block.get("after", "")
            if source.count(primary_space(probe)) < 2:
                errors.append(
                    f"block {block_id}: unanchorable text must occur at least twice"
                )
            continue
        for label, anchor in text_anchors(block):
            errors += _unique(source, f"block {block_id}: {label}", anchor)
            if source.count_fallback(fallback_space(anchor)) != 1:
                warnings.append(
                    f"block {block_id}: {label} is not unique in the fallback space"
                )
            if _LEADING_MARKER.match(anchor):
                warnings.append(
                    f"block {block_id}: {label} may begin with a bullet or marker"
                )
        if "end" in block:
            start_hits = (
                find_all(source.primary, primary_space(block["start"]))
                if primary_space(block["start"])
                else []
            )
            end_hits = (
                find_all(source.primary, primary_space(block["end"]))
                if primary_space(block["end"])
                else []
            )
            if (
                len(start_hits) == 1
                and len(end_hits) == 1
                and end_hits[0] < start_hits[0]
            ):
                warnings.append(f"block {block_id}: end precedes start")
    return errors, warnings, unanchorable


def _unique(source: SourceText, label: str, anchor: str) -> list[str]:
    form = primary_space(anchor)
    if not form:
        return [f"{label}: anchor has no characters in the matching space"]
    hits = source.count(form)
    if hits == 1:
        return []
    if hits == 0:
        return [f"{label}: not found{_case_hint(source, anchor)}"]
    return [f"{label}: occurs {hits} times; extend it until it is unique"]


def _case_hint(source: SourceText, anchor: str) -> str:
    hits = source.count_casefold(primary_space(anchor))
    return (
        f" (case-insensitive hits: {hits}; CSS text-transform may have changed the case)"
        if hits
        else ""
    )


def validate_fixture(fixture_dir: Path) -> Report:
    report = Report(fixture_id=fixture_dir.name)
    source = SourceText((fixture_dir / "source.html").read_bytes())
    report.encoding = source.decoded.encoding
    report.encoding_basis = source.decoded.basis
    report.ascii_only = source.decoded.ascii_only
    gold_path = fixture_dir / "gold.toml"
    if not gold_path.exists():
        report.errors.append("gold.toml is missing")
        return report
    try:
        gold = load_gold(fixture_dir)
    except tomllib.TOMLDecodeError as exc:
        report.errors.append(f"gold.toml is not valid TOML: {exc}")
        return report
    report.errors += check_schema(gold, fixture_dir.name)
    if report.errors:
        return report
    errors, warnings, unanchorable = check_anchors(gold, source)
    report.errors += errors
    report.warnings += warnings
    report.unanchorable = unanchorable
    return report


def init_skeleton(fixture_dir: Path) -> Path:
    path = fixture_dir / "gold.toml"
    if path.exists():
        raise FileExistsError(f"{path} exists; refusing to overwrite")
    path.write_text(SKELETON.format(fixture_id=fixture_dir.name), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("fixture_dirs", nargs="+", type=Path)
    parser.add_argument(
        "--init",
        action="store_true",
        help="write a gold.toml skeleton (header fields only)",
    )
    args = parser.parse_args(argv)
    if args.init:
        for fixture_dir in args.fixture_dirs:
            print(f"wrote {init_skeleton(fixture_dir)}")
        return 0
    status = 0
    for fixture_dir in args.fixture_dirs:
        report = validate_fixture(fixture_dir)
        ascii_note = (
            "; every byte is ASCII, so any browser encoding agrees"
            if report.ascii_only
            else ""
        )
        print(
            f"{report.fixture_id}: decoded as {report.encoding} (basis: {report.encoding_basis}{ascii_note})"
        )
        for error in report.errors:
            print(f"  ERROR   {error}")
        for warning in report.warnings:
            print(f"  warning {warning}")
        print(
            f"  {len(report.errors)} errors, {len(report.warnings)} warnings, {report.unanchorable} unanchorable"
        )
        status |= 0 if report.ok else 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_validate_gold.py --import-mode=prepend -q`
Expected: `9 passed`.

- [x] **Step 5: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/validate_gold.py expirements/parser-fidelity/test_validate_gold.py
git commit -m "feat(parser-fidelity): add the standard-library gold validator"
```

---

### Task 9: Harness check (exit criterion 4)

**Files:**
- Create: `expirements/parser-fidelity/check_fixtures.py`
- Test: `expirements/parser-fidelity/test_check_fixtures.py`

**Interfaces:**
- Consumes: `validate_gold.validate_fixture` (Task 8) and `pf_paths` (Task 1).
- Produces:
  - `check_fixtures(fixtures, register, repo) -> list[str]`;
  - `check_locks(harness, repo) -> list[str]`;
  - `committable_files(repo, folder) -> set[str]`, the files Git tracks or would add
    under a folder. Ignored files such as Finder's `.DS_Store` drop out, while a stray
    untracked file still counts.
  - `declared_dependencies(script) -> list[str]`;
  - the CLI, which exits 0 only when there are no problems.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_check_fixtures.py`:

```python
import hashlib
import subprocess

import pytest
from check_fixtures import check_fixtures, check_locks, declared_dependencies
from test_validate_gold import FID, GOOD_BLOCKS, HEADER, SOURCE

REGISTER = '[sources.sec-edgar]\nredistribution_status = "SEC reuse policy quoted; issuers\' copyright not addressed."\n'


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    fixtures = tmp_path / "tests" / "fixtures" / "releases"
    folder = fixtures / FID
    folder.mkdir(parents=True)
    (folder / "source.html").write_text(SOURCE, encoding="utf-8")
    (folder / "gold.toml").write_text(HEADER + GOOD_BLOCKS, encoding="utf-8")
    sha = hashlib.sha256(SOURCE.encode()).hexdigest()
    (fixtures / "manifest.toml").write_text(
        f'[[fixtures]]\nfixture_id = "{FID}"\nsha256 = "{sha}"\nsource_id = "sec-edgar"\n'
    )
    (tmp_path / ".gitattributes").write_text(
        "tests/fixtures/releases/*/source.html -text\n"
    )
    (tmp_path / ".gitignore").write_text(".DS_Store\n")
    (tmp_path / "register.toml").write_text(REGISTER)
    return tmp_path


def run(repo):
    return check_fixtures(
        repo / "tests" / "fixtures" / "releases", repo / "register.toml", repo
    )


def test_a_complete_fixture_passes(repo):
    assert run(repo) == []


def test_ignored_files_such_as_ds_store_do_not_count(repo):
    folder = repo / "tests" / "fixtures" / "releases" / FID
    (folder / ".DS_Store").write_bytes(b"finder")
    assert run(repo) == []


def test_missing_attribute_extra_file_and_bad_hash_are_reported(repo):
    (repo / ".gitattributes").write_text("")
    folder = repo / "tests" / "fixtures" / "releases" / FID
    (folder / "notes.txt").write_text("x")
    (folder / "source.html").write_text(SOURCE + " ", encoding="utf-8")
    problems = run(repo)
    assert any("does not mark source.html -text" in p for p in problems)
    assert any("expected exactly" in p for p in problems)
    assert any("does not match its manifest sha256" in p for p in problems)


def test_unknown_source_and_orphan_entries_are_reported(repo):
    (repo / "register.toml").write_text(
        "[sources.other]\nredistribution_status = 'x'\n"
    )
    (repo / "tests" / "fixtures" / "releases" / "0009999999-25-000001_ex-99").mkdir()
    problems = run(repo)
    assert any("has no register entry" in p for p in problems)
    assert any("directory has no manifest entry" in p for p in problems)


def test_locks_must_be_committed_for_scripts_with_dependencies(tmp_path):
    git(tmp_path, "init", "-q")
    harness = tmp_path / "h"
    harness.mkdir()
    (harness / "tool.py").write_text(
        '# /// script\n# requires-python = ">=3.14"\n# dependencies = ["httpx==0.28.1"]\n# ///\n'
    )
    (harness / "plain.py").write_text("import json\n")
    assert declared_dependencies(harness / "tool.py") == ["httpx==0.28.1"]
    assert check_locks(harness, tmp_path) == [
        "tool.py: declares dependencies but tool.py.lock is not committed"
    ]
    (harness / "tool.py.lock").write_text("version = 1\n")
    git(tmp_path, "add", "h/tool.py.lock")
    assert check_locks(harness, tmp_path) == []
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_check_fixtures.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'check_fixtures'`.

- [x] **Step 3: Write the implementation**

`expirements/parser-fidelity/check_fixtures.py`:

```python
"""Stage 1 harness check (spec: Exit criteria 4). Standard library plus the git CLI.

    uv run --locked --all-packages python expirements/parser-fidelity/check_fixtures.py

Confirms that each fixture directory holds exactly source.html and gold.toml and has a
manifest entry (and the reverse); each source.html matches its sha256 and is at most
1 MiB; .gitattributes marks source.html -text; every source_id resolves to a register
entry with a recorded redistribution status; every gold.toml passes the validator; and
every harness script that declares dependencies has a committed lock.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

import tomllib
from pf_paths import FIXTURES, HARNESS, MAX_FIXTURE_BYTES, REGISTER, REPO_ROOT
from validate_gold import validate_fixture

FIXTURE_FILES = {"gold.toml", "source.html"}
_SCRIPT_BLOCK = re.compile(
    r"^# /// script\s*$(.*?)^# ///\s*$", re.MULTILINE | re.DOTALL
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )


def declared_dependencies(script: Path) -> list[str]:
    match = _SCRIPT_BLOCK.search(script.read_text(encoding="utf-8"))
    if match is None:
        return []
    body = "\n".join(
        line.removeprefix("#").removeprefix(" ") for line in match.group(1).splitlines()
    )
    return list(tomllib.loads(body).get("dependencies", []))


def committable_files(repo: Path, folder: Path) -> set[str]:
    """Files under ``folder`` that Git tracks or would add; ignored files such as .DS_Store drop out."""
    relative = folder.relative_to(repo).as_posix()
    listed = _git(
        repo, "ls-files", "--cached", "--others", "--exclude-standard", "--", relative
    )
    return {
        line.removeprefix(relative + "/") for line in listed.stdout.splitlines() if line
    }


def check_fixtures(fixtures: Path, register: Path, repo: Path) -> list[str]:
    problems: list[str] = []
    manifest = tomllib.loads((fixtures / "manifest.toml").read_text(encoding="utf-8"))
    entries = {entry["fixture_id"]: entry for entry in manifest.get("fixtures", [])}
    directories = {path.name for path in fixtures.iterdir() if path.is_dir()}
    problems += [
        f"{fid}: directory has no manifest entry"
        for fid in sorted(directories - set(entries))
    ]
    problems += [
        f"{fid}: manifest entry has no directory"
        for fid in sorted(set(entries) - directories)
    ]
    sources = tomllib.loads(register.read_text(encoding="utf-8")).get("sources", {})
    for fid in sorted(directories & set(entries)):
        folder, entry = fixtures / fid, entries[fid]
        files = committable_files(repo, folder)
        if files != FIXTURE_FILES:
            problems.append(
                f"{fid}: holds {sorted(files)}, expected exactly {sorted(FIXTURE_FILES)}"
            )
        source = folder / "source.html"
        if source.exists():
            raw = source.read_bytes()
            if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                problems.append(
                    f"{fid}: source.html does not match its manifest sha256"
                )
            if len(raw) > MAX_FIXTURE_BYTES:
                problems.append(f"{fid}: source.html is {len(raw)} bytes, over 1 MiB")
            attribute = _git(
                repo, "check-attr", "text", "--", str(source.relative_to(repo))
            ).stdout.strip()
            if not attribute.endswith(": text: unset"):
                problems.append(
                    f"{fid}: .gitattributes does not mark source.html -text ({attribute or 'no output'})"
                )
        status = sources.get(entry.get("source_id"), {}).get(
            "redistribution_status", ""
        )
        if not status.strip():
            problems.append(
                f"{fid}: source_id {entry.get('source_id')!r} has no register entry with a redistribution status"
            )
        if (folder / "gold.toml").exists():
            report = validate_fixture(folder)
            problems += [f"{fid}: gold: {error}" for error in report.errors]
    return problems


def check_locks(harness: Path, repo: Path) -> list[str]:
    problems = []
    for script in sorted(harness.glob("*.py")):
        if not declared_dependencies(script):
            continue
        lock = script.with_name(script.name + ".lock")
        tracked = (
            _git(
                repo, "ls-files", "--error-unmatch", str(lock.relative_to(repo))
            ).returncode
            == 0
        )
        if not tracked:
            problems.append(
                f"{script.name}: declares dependencies but {lock.name} is not committed"
            )
    return problems


def main() -> int:
    problems = check_fixtures(FIXTURES, REGISTER, REPO_ROOT) + check_locks(
        HARNESS, REPO_ROOT
    )
    for problem in problems:
        print(problem)
    print(
        "fixture check passed"
        if not problems
        else f"fixture check failed: {len(problems)} problem(s)"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_check_fixtures.py --import-mode=prepend -q`
Expected: `5 passed`.

- [x] **Step 5: Run the check on the real corpus**

Run: `uv run --locked --all-packages python expirements/parser-fidelity/check_fixtures.py`

Expected, because no gold exists yet: exit 1, with exactly two problems per fixture:

- `<id>: holds ['source.html'], expected exactly ['gold.toml', 'source.html']`;
- `<id>: gold: gold.toml is missing`.

No sha256, attribute, register, or lock problem may appear; if one does, fix it before
committing.

- [x] **Step 6: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/check_fixtures.py expirements/parser-fidelity/test_check_fixtures.py
git commit -m "feat(parser-fidelity): add the fixture and harness check"
```

---

### Task 10: Gate B — the user marks the gold

This task is the user's (D2: sole annotator). The agent prepares the files and then
continues with Tasks 11–18. Throughout this task the agent must not run any candidate
on a fixture, and must never show candidate output to the user. `run_candidates.py
fixtures` also refuses to run until every gold file validates.

**Files:**
- Create (user): `tests/fixtures/releases/<fixture_id>/gold.toml` ×8
- Create (user): `expirements/parser-fidelity/gold-notes.md`

**Interfaces:**
- Consumes: the corpus (Task 7) and `validate_gold.py` (Task 8).
- Produces: eight `gold.toml` files that pass the validator, and `gold-notes.md`. V2
  (Task 20) reads both.

- [x] **Step 1: Prepare the skeletons and the notes file**

Run: `uv run --locked --all-packages python expirements/parser-fidelity/validate_gold.py --init tests/fixtures/releases/*/`
Expected: one `wrote …/gold.toml` line per fixture.

Create `expirements/parser-fidelity/gold-notes.md` from this template, with one
section per fixture ID:

```markdown
# Gold marking notes

The annotator writes one section per fixture while marking (specs/release-parser-fidelity.md,
Gold annotation). The V2 record's gold protocol and its element-nesting section, which
Stage 2 needs, are drawn from these notes. No candidate output is consulted while marking.

## <fixture_id>

- Browser and version:
- Validator encoding and basis:
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII):
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:
```

- [x] **Step 2: Hand the marking protocol to the user**

Tell the user, in these words:

> For each fixture:
>
> 1. **Open the file.** Open `tests/fixtures/releases/<id>/source.html` in your
>    browser as a local file.
> 2. **Check the encoding.** Run
>    `uv run --locked --all-packages python expirements/parser-fidelity/validate_gold.py tests/fixtures/releases/<id>`.
>    Compare the encoding it prints with `document.characterSet` in the browser's
>    developer console. You can skip this if it reports that every byte is ASCII. If
>    the two differ, stop and tell me.
> 3. **Mark the blocks.** Follow the guidelines in the Gold annotation section of
>    `specs/release-parser-fidelity.md`:
>    - one `[[blocks]]` entry per rendered block, in rendered reading order;
>    - `start` and `end` anchors copied verbatim, never including a bullet, list
>      number, or footnote marker;
>    - tables get `headers` and three L-shaped `cells`;
>    - page artifacts need only `start`.
>
>    Work only from the browser rendering.
> 4. **Validate as you go.** Rerun the validator after every few blocks; errors block
>    scoring, warnings do not. In TOML, write a copied `"` as `\"` and a `\` as `\\`.
>    Alternatively, put an anchor that contains `"` but no `'` in single quotes
>    (`'…'`), which TOML reads literally.
> 5. **Finish.** Fill in `annotator`, `browser`, and `completed`, then complete this
>    fixture's section of `gold-notes.md`: browser and version, the encoding check,
>    time spent, and any table inside a list or another table.
>
> Tell me when a fixture validates, and I will commit it.

If the user reports that the encodings differ for a fixture with non-ASCII bytes, the
fixture cannot be marked faithfully against the validator's text.

- **One fixture.** Replace it: return to gate A for one replacement of the same class,
  then rerun Task 7 (`promote_fixtures.py`) and this task for the replacement.
- **Several fixtures.** The decoding rule is wrong for this corpus. Revise
  `pf_decode.py` with a failing test first, before the Task 15 freeze, record the
  change for V2, and revalidate every gold file already marked.

- [x] **Step 3: Commit each fixture's gold as it validates**

For each fixture the user reports complete:

```bash
uv run --locked --all-packages python expirements/parser-fidelity/validate_gold.py tests/fixtures/releases/<id>
```

Expected: `0 errors` for that fixture. Then commit it:

```bash
git add tests/fixtures/releases/<id>/gold.toml expirements/parser-fidelity/gold-notes.md
git commit -m "test(fixtures): add gold structure for <id>"
```

- [x] **Step 4: Confirm the gate is complete**

Run: `uv run --locked --all-packages python expirements/parser-fidelity/check_fixtures.py`
Expected: `fixture check passed`. The gate is complete only when that line prints; Task
19 depends on it.

---

### Task 11: Element dumps, the network guard, and the adapter entry point

**Files:**
- Create: `expirements/parser-fidelity/pf_dump.py`
- Test: `expirements/parser-fidelity/test_pf_dump.py`

**Interfaces:**
- Consumes: `pf_decode.decode_html_bytes` (Task 1).
- Produces:
  - **Types.** `COMMON_TYPES`, a frozenset of `heading`, `paragraph`, `list_item`,
    `footnote`, `table`, and `other`.
  - **Dump schema.**
    - `Cell(text: str, colspan: int = 1, rowspan: int = 1)`;
    - `Row(header: bool, cells: tuple[Cell, ...])`;
    - `Element(type: str, text: str, parent: int | None = None, level: int | None = None, source_type: str = "", rows: tuple[Row, ...] | None = None)`.
  - **Dump helpers.** `grid_text(rows) -> str`, `validate_elements(elements)`,
    `dump_bytes(elements) -> bytes`, and `read_dump(path) -> list[Element]`.
  - **Network guard.** `NetworkGuardTripped`, and
    `install_network_guard() -> NetworkGuard`, which records every trip in `.trips`
    and restores the original functions with `.restore()`.
  - **Adapter entry point.**
    `run_adapter(parse: Callable[[str], list[Element]], *, library: str | None, argv=None) -> int`.
    - It takes the CLI arguments `--input`, `--output`, and `--sidecar`.
    - It exits with `EXIT_OK = 0`, `EXIT_CRASH = 2`, or `EXIT_NETWORK = 3`.
    - Its sidecar JSON holds `status` (`ok`, `crash`, or `void_network`), `python`,
      `encoding`, `encoding_basis`, `library`, `library_version`, `parse_seconds`,
      and either `elements`, `error`, or `guard_trips`.

This module shapes every dump, so Task 15 freezes it.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_pf_dump.py`:

```python
import contextlib
import json
import socket

import pytest
from pf_dump import (
    EXIT_CRASH,
    EXIT_NETWORK,
    EXIT_OK,
    Cell,
    Element,
    NetworkGuardTripped,
    Row,
    dump_bytes,
    grid_text,
    install_network_guard,
    read_dump,
    run_adapter,
    validate_elements,
)

ROWS = (
    Row(True, (Cell(""), Cell("Three Months Ended", colspan=2))),
    Row(False, (Cell("Net sales"), Cell("4,321"), Cell("3,210"))),
)


def test_grid_text_reads_rows_in_order():
    assert grid_text(ROWS) == " Three Months Ended\nNet sales 4,321 3,210"


def test_dump_round_trips_and_is_canonical(tmp_path):
    elements = [
        Element("other", "", None, None, "DocumentNode"),
        Element("heading", "Results", 0, 1, "HeadingNode"),
        Element("table", grid_text(ROWS), 0, None, "TableNode", ROWS),
    ]
    data = dump_bytes(elements)
    assert data == dump_bytes(list(elements))
    assert data.endswith(b"\n") and b": " not in data
    path = tmp_path / "dump.json"
    path.write_bytes(data)
    assert read_dump(path) == elements


def test_validate_elements_rejects_bad_types_parents_and_grids():
    with pytest.raises(ValueError, match="common type"):
        validate_elements([Element("sidebar", "x")])
    with pytest.raises(ValueError, match="must precede"):
        validate_elements([Element("paragraph", "x", parent=0)])
    with pytest.raises(ValueError, match="only tables"):
        validate_elements([Element("paragraph", "x", rows=ROWS)])
    with pytest.raises(ValueError, match="grid read row by row"):
        validate_elements([Element("table", "wrong", rows=ROWS)])


def test_network_guard_records_trips_and_restores():
    original = socket.getaddrinfo
    guard = install_network_guard()
    try:
        with pytest.raises(NetworkGuardTripped):
            socket.getaddrinfo("example.com", 80)
        with pytest.raises(NetworkGuardTripped):
            socket.create_connection(("example.com", 80))
        with contextlib.suppress(
            NetworkGuardTripped
        ):  # a swallowed trip is still recorded
            socket.gethostbyname("example.com")
    finally:
        guard.restore()
    assert guard.trips == [
        "socket.getaddrinfo",
        "socket.create_connection",
        "socket.gethostbyname",
    ]
    assert socket.getaddrinfo is original


def _args(tmp_path):
    source = tmp_path / "source.html"
    source.write_bytes(b"<p>\x93Hi\x94</p>")
    return source, [
        "--input",
        str(source),
        "--output",
        str(tmp_path / "d.json"),
        "--sidecar",
        str(tmp_path / "s.json"),
    ]


def test_run_adapter_decodes_once_and_writes_dump_and_sidecar(tmp_path):
    _, argv = _args(tmp_path)
    seen = []

    def parse(text):
        seen.append(text)
        return [Element("paragraph", text)]

    assert run_adapter(parse, library=None, argv=argv) == EXIT_OK
    assert seen == ["<p>\u201cHi\u201d</p>"]
    sidecar = json.loads((tmp_path / "s.json").read_text())
    assert sidecar["status"] == "ok" and sidecar["encoding"] == "windows-1252"
    assert read_dump(tmp_path / "d.json") == [
        Element("paragraph", "<p>\u201cHi\u201d</p>")
    ]


def test_run_adapter_voids_a_run_whose_parse_touched_the_network(tmp_path):
    _, argv = _args(tmp_path)

    def parse(text):
        with contextlib.suppress(NetworkGuardTripped):  # a library that swallows it
            socket.create_connection(("example.com", 443))
        return [Element("paragraph", text)]

    assert run_adapter(parse, library=None, argv=argv) == EXIT_NETWORK
    assert not (tmp_path / "d.json").exists()
    assert json.loads((tmp_path / "s.json").read_text())["status"] == "void_network"


def test_run_adapter_records_a_crash(tmp_path):
    _, argv = _args(tmp_path)

    def parse(text):
        raise RuntimeError("boom")

    assert run_adapter(parse, library=None, argv=argv) == EXIT_CRASH
    assert (
        json.loads((tmp_path / "s.json").read_text())["error"] == "RuntimeError: boom"
    )
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_pf_dump.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'pf_dump'`.

- [x] **Step 3: Write the implementation**

`expirements/parser-fidelity/pf_dump.py`:

```python
"""Element dumps, the network guard, and the adapter entry point (spec: Candidate harness).

A dump is the ordered list of elements a candidate emits for one release, in the
candidate's document order. Containers carry empty text (their children carry it), so
joining element texts never duplicates content. ``parent`` is an index into the same
list; no library identifier is ever written, so two runs can be compared byte for
byte. Dumps carry no run metadata: timing and status go to a separate sidecar.

This module shapes every dump, so it is frozen with the adapters (freeze.py).
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import socket
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from pf_decode import decode_html_bytes

COMMON_TYPES = frozenset(
    {"heading", "paragraph", "list_item", "footnote", "table", "other"}
)
DUMP_SCHEMA_VERSION = 1
EXIT_OK, EXIT_CRASH, EXIT_NETWORK = 0, 2, 3


@dataclass(frozen=True)
class Cell:
    text: str
    colspan: int = 1
    rowspan: int = 1


@dataclass(frozen=True)
class Row:
    header: bool
    cells: tuple[Cell, ...]


@dataclass(frozen=True)
class Element:
    type: str
    text: str
    parent: int | None = None
    level: int | None = None
    source_type: str = ""  # the library's own type name, for the published type mapping
    rows: tuple[Row, ...] | None = (
        None  # the grid, when the candidate exposes table cells
    )


def grid_text(rows: Sequence[Row]) -> str:
    """A grid read row by row in the given order: cells joined by spaces, rows by newlines."""
    return "\n".join(" ".join(cell.text for cell in row.cells) for row in rows)


def validate_elements(elements: Sequence[Element]) -> None:
    for index, element in enumerate(elements):
        if element.type not in COMMON_TYPES:
            raise ValueError(
                f"element {index}: type {element.type!r} is not a common type"
            )
        if element.parent is not None and not 0 <= element.parent < index:
            raise ValueError(
                f"element {index}: parent {element.parent} must precede it"
            )
        if element.rows is not None and element.type != "table":
            raise ValueError(f"element {index}: only tables carry rows")
        if element.rows is not None and element.text != grid_text(element.rows):
            raise ValueError(
                f"element {index}: a grid table's text must be its grid read row by row"
            )


def _element_json(element: Element) -> dict:
    data: dict = {
        "type": element.type,
        "text": element.text,
        "parent": element.parent,
        "source_type": element.source_type,
    }
    if element.level is not None:
        data["level"] = element.level
    if element.rows is not None:
        data["rows"] = [
            {
                "header": row.header,
                "cells": [[c.text, c.colspan, c.rowspan] for c in row.cells],
            }
            for row in element.rows
        ]
    return data


def dump_bytes(elements: Sequence[Element]) -> bytes:
    document = {
        "schema_version": DUMP_SCHEMA_VERSION,
        "elements": [_element_json(e) for e in elements],
    }
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def read_dump(path: Path) -> list[Element]:
    document = json.loads(path.read_text(encoding="utf-8"))
    elements = []
    for data in document["elements"]:
        rows = None
        if "rows" in data:
            rows = tuple(
                Row(r["header"], tuple(Cell(t, cs, rs) for t, cs, rs in r["cells"]))
                for r in data["rows"]
            )
        elements.append(
            Element(
                data["type"],
                data["text"],
                data["parent"],
                data.get("level"),
                data["source_type"],
                rows,
            )
        )
    return elements


class NetworkGuardTripped(RuntimeError):
    pass


@dataclass
class NetworkGuard:
    trips: list[str] = field(default_factory=list)
    _saved: dict[tuple[object, str], object] = field(default_factory=dict)

    def restore(self) -> None:
        for (owner, name), original in self._saved.items():
            setattr(owner, name, original)
        self._saved.clear()


_GUARDED = (
    (socket.socket, "connect"),
    (socket.socket, "connect_ex"),
    (socket, "create_connection"),
    (socket, "getaddrinfo"),
    (socket, "gethostbyname"),
    (socket, "gethostbyname_ex"),
)


def install_network_guard() -> NetworkGuard:
    """Make every socket connection or name lookup raise, and record it.

    Libraries sometimes swallow exceptions, so a trip is recorded before raising and the
    runner checks ``trips`` after parsing: any trip voids the run.
    """
    guard = NetworkGuard()

    def blocked(name: str) -> Callable[..., object]:
        def _raise(*args: object, **kwargs: object) -> object:
            guard.trips.append(name)
            raise NetworkGuardTripped(f"network use blocked during parsing: {name}")

        return _raise

    for owner, name in _GUARDED:
        guard._saved[(owner, name)] = getattr(owner, name)
        setattr(owner, name, blocked(f"{getattr(owner, '__name__', owner)}.{name}"))
    return guard


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def run_adapter(
    parse: Callable[[str], list[Element]],
    *,
    library: str | None,
    argv: list[str] | None = None,
) -> int:
    """Shared adapter entry point: guard, decode, parse, validate, write dump and sidecar.

    ``parse`` imports its library inside the function, so the guard is in place first.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    args = parser.parse_args(argv)

    guard = install_network_guard()
    decoded = decode_html_bytes(args.input.read_bytes())
    sidecar: dict = {
        "python": platform.python_version(),
        "encoding": decoded.encoding,
        "encoding_basis": decoded.basis,
        "library": library,
        "library_version": importlib.metadata.version(library) if library else None,
    }
    status, code = "ok", EXIT_OK
    started = time.perf_counter()
    try:
        elements = parse(decoded.text)
        validate_elements(elements)
    except Exception as exc:  # noqa: BLE001 - a crash is a result to record
        status, code = "crash", EXIT_CRASH
        sidecar["error"] = f"{type(exc).__name__}: {exc}"
    sidecar["parse_seconds"] = round(time.perf_counter() - started, 4)
    guard.restore()
    if guard.trips:
        status, code = "void_network", EXIT_NETWORK
        sidecar["guard_trips"] = guard.trips
    sidecar["status"] = status
    if code == EXIT_OK:
        sidecar["elements"] = len(elements)
        _write_atomic(args.output, dump_bytes(elements))
    _write_atomic(
        args.sidecar, (json.dumps(sidecar, indent=2, sort_keys=True) + "\n").encode()
    )
    return code
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_pf_dump.py --import-mode=prepend -q`
Expected: `7 passed`.

- [x] **Step 5: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/pf_dump.py expirements/parser-fidelity/test_pf_dump.py
git commit -m "feat(parser-fidelity): add element dumps, network guard, and adapter entry point"
```

---

### Task 12: Control and library adapters

**Files:**
- Create: `expirements/parser-fidelity/control.py`, `control.py.lock`
- Create: `expirements/parser-fidelity/adapter_edgartools.py`, `adapter_edgartools.py.lock`
- Create: `expirements/parser-fidelity/adapter_secparser.py`, `adapter_secparser.py.lock`
- Test: `expirements/parser-fidelity/test_adapters.py`

**Interfaces:**
- Consumes: `pf_dump` (Task 11), `pf_paths.EDGAR_HOME` (Task 1), and the development
  set in `data/raw/devset/` (Task 7).
- Produces:
  - Three adapter scripts that share `run_adapter`'s CLI.
  - `adapter_edgartools.flatten(root) -> list[Element]`, with the mapping constants
    `CONTAINER_NODE_TYPES` and `LEAF_NODE_TYPES` and the footnote constant
    `FOOTNOTE_SEMANTIC_TYPE`.
  - `adapter_secparser.convert(elements) -> list[Element]`, with the mapping constant
    `TYPE_BY_CLASS`.
  - `control.parse(html) -> list[Element]`.
  - Both library adapters take a `--self-check` flag.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_adapters.py`:

```python
"""Adapter logic with stand-in objects; the real libraries run only in each script's own env."""

from enum import Enum, auto
from types import SimpleNamespace

import adapter_edgartools
import adapter_secparser
import control
import pytest
from pf_dump import Cell, Element, Row, validate_elements


class NodeType(Enum):
    DOCUMENT = auto()
    HEADING = auto()
    PARAGRAPH = auto()
    TABLE = auto()
    LIST = auto()
    LIST_ITEM = auto()
    TEXT = auto()


class FakeNode:
    def __init__(self, kind, text="", children=(), **attrs):
        self.type = NodeType[kind]
        self._text = text
        self.children = list(children)
        self.__dict__.update(attrs)

    def text(self):
        return self._text


def cell(text, colspan=1):
    return SimpleNamespace(text=lambda: text, colspan=colspan, rowspan=1)


def test_edgartools_flatten_keeps_order_parents_and_types():
    table = FakeNode(
        "TABLE",
        headers=[[cell(""), cell("Three Months Ended", 2)]],
        rows=[
            SimpleNamespace(
                is_header=False, cells=[cell("Net sales"), cell("4,321"), cell("3,210")]
            )
        ],
        footer=[],
        caption=None,
    )
    footnote = FakeNode(
        "PARAGRAPH", "Excludes items", semantic_type=SimpleNamespace(name="FOOTNOTE")
    )
    root = FakeNode(
        "DOCUMENT",
        children=[
            FakeNode("HEADING", "Results", level=1),
            FakeNode(
                "LIST",
                children=[
                    FakeNode("LIST_ITEM", "First"),
                    FakeNode("LIST_ITEM", "Second"),
                ],
            ),
            table,
            footnote,
            FakeNode("TEXT", "loose text"),
        ],
    )
    elements = adapter_edgartools.flatten(root)
    validate_elements(elements)
    assert [(e.type, e.text, e.parent) for e in elements] == [
        ("other", "", None),
        ("heading", "Results", 0),
        ("other", "", 0),
        ("list_item", "First", 2),
        ("list_item", "Second", 2),
        ("table", " Three Months Ended\nNet sales 4,321 3,210", 0),
        ("footnote", "Excludes items", 0),
        ("other", "loose text", 0),
    ]
    assert elements[1].level == 1
    assert elements[5].rows[0] == Row(
        True, (Cell(""), Cell("Three Months Ended", 2, 1))
    )


def test_edgartools_mapping_covers_the_5_58_0_node_types():
    members = {
        "DOCUMENT",
        "SECTION",
        "HEADING",
        "PARAGRAPH",
        "TABLE",
        "LIST",
        "LIST_ITEM",
        "LINK",
        "IMAGE",
        "XBRL_FACT",
        "TEXT",
        "CONTAINER",
    }
    assert members == adapter_edgartools.CONTAINER_NODE_TYPES | set(
        adapter_edgartools.LEAF_NODE_TYPES
    )


def test_secparser_types_follow_the_most_specific_class():
    class AbstractSemanticElement:
        text = "x"

    class TableElement(AbstractSemanticElement):
        pass

    class TableOfContentsElement(TableElement):
        pass

    class TitleElement(AbstractSemanticElement):
        level = 2

    class Mystery:
        text = "y"

    converted = adapter_secparser.convert(
        [TableOfContentsElement(), TitleElement(), AbstractSemanticElement()]
    )
    assert [(e.type, e.level, e.source_type) for e in converted] == [
        ("table", None, "TableOfContentsElement"),
        ("heading", 2, "TitleElement"),
        ("other", None, "AbstractSemanticElement"),
    ]
    with pytest.raises(TypeError):
        adapter_secparser.convert([Mystery()])


def test_control_emits_one_paragraph_per_line():
    html = "<html><head><title>T</title></head><body><p>First line</p><table><tr><td>A</td><td>B</td></tr></table></body></html>"
    assert control.parse(html) == [
        Element("paragraph", "T", None, None, "line"),
        Element("paragraph", "First line", None, None, "line"),
        Element("paragraph", "A", None, None, "line"),
        Element("paragraph", "B", None, None, "line"),
    ]
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_adapters.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'adapter_edgartools'`.

- [x] **Step 3: Write the three adapters**

`expirements/parser-fidelity/control.py`:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["beautifulsoup4==4.15.0", "lxml==6.1.3"]
# ///
"""Negative control: naive text extraction, scored like a candidate but never selectable.

``BeautifulSoup(html, "lxml").get_text("\\n", strip=True)``, with each non-empty line
as a paragraph.

    uv run --locked --script expirements/parser-fidelity/control.py --input S --output D --sidecar C
"""

from __future__ import annotations

from pf_dump import Element, run_adapter


def parse(html: str) -> list[Element]:
    from bs4 import BeautifulSoup

    text = BeautifulSoup(html, "lxml").get_text("\n", strip=True)
    return [
        Element("paragraph", line, None, None, "line")
        for line in text.split("\n")
        if line.strip()
    ]


if __name__ == "__main__":
    raise SystemExit(run_adapter(parse, library="beautifulsoup4"))
```

`expirements/parser-fidelity/adapter_edgartools.py`:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["edgartools==5.58.0"]
# ///
"""Candidate adapter: edgartools 5.58.0's HTML document parser (edgar.documents).

The parse path is ``edgar.documents.parse_html(html)`` with the default ParserConfig,
the call edgartools' own ``PressRelease.text()`` makes. The legacy ``edgar.files.html``
parser is deprecated (removed in edgartools 6.0) and is not measured.

    uv run --locked --script expirements/parser-fidelity/adapter_edgartools.py --input S --output D --sidecar C
    uv run --locked --script expirements/parser-fidelity/adapter_edgartools.py --self-check

Type mapping (NodeType name -> common type). Containers carry no text.
"""

from __future__ import annotations

import os
import sys

from pf_dump import Cell, Element, Row, grid_text, run_adapter
from pf_paths import EDGAR_HOME

CONTAINER_NODE_TYPES = frozenset({"DOCUMENT", "SECTION", "CONTAINER", "LIST"})
LEAF_NODE_TYPES = {
    "HEADING": "heading",
    "PARAGRAPH": "paragraph",
    "LIST_ITEM": "list_item",
    "TABLE": "table",
    "TEXT": "other",
    "LINK": "other",
    "IMAGE": "other",
    "XBRL_FACT": "other",
}
FOOTNOTE_SEMANTIC_TYPE = (
    "FOOTNOTE"  # a paragraph carrying SemanticType.FOOTNOTE is a footnote
)


def table_rows(table: object) -> tuple[Row, ...]:
    """Header rows first, then body rows, then footer rows, as TableNode holds them."""
    rows = [Row(True, tuple(_cell(c) for c in header)) for header in table.headers]
    for row in [*table.rows, *table.footer]:
        rows.append(Row(bool(row.is_header), tuple(_cell(c) for c in row.cells)))
    return tuple(rows)


def _cell(cell: object) -> Cell:
    return Cell(
        cell.text() or "",
        max(1, int(cell.colspan or 1)),
        max(1, int(cell.rowspan or 1)),
    )


def leaf_type(node: object) -> str:
    name = node.type.name
    semantic = getattr(node, "semantic_type", None)
    if (
        name == "PARAGRAPH"
        and getattr(semantic, "name", None) == FOOTNOTE_SEMANTIC_TYPE
    ):
        return "footnote"
    return LEAF_NODE_TYPES[name]


def flatten(root: object) -> list[Element]:
    """Pre-order walk: containers become text-less parents; every other node is a leaf."""
    elements: list[Element] = []
    stack: list[tuple[object, int | None]] = [(root, None)]
    while stack:
        node, parent = stack.pop()
        name = node.type.name
        source_type = type(node).__name__
        if name in CONTAINER_NODE_TYPES:
            elements.append(Element("other", "", parent, None, source_type))
            index = len(elements) - 1
            stack.extend((child, index) for child in reversed(node.children))
        elif name == "TABLE":
            if getattr(node, "caption", None):
                elements.append(
                    Element("other", node.caption, parent, None, "TableNode.caption")
                )
            rows = table_rows(node)
            elements.append(
                Element("table", grid_text(rows), parent, None, source_type, rows)
            )
        else:
            level = getattr(node, "level", None) if name == "HEADING" else None
            elements.append(
                Element(leaf_type(node), node.text() or "", parent, level, source_type)
            )
    return elements


def parse(html: str) -> list[Element]:
    os.environ.setdefault("EDGAR_LOCAL_DATA_DIR", str(EDGAR_HOME))
    from edgar.documents import (
        parse_html,
    )  # imported after the network guard is installed

    return flatten(parse_html(html).root)


def self_check() -> int:
    """Every public NodeType must be mapped; run before the freeze."""
    os.environ.setdefault("EDGAR_LOCAL_DATA_DIR", str(EDGAR_HOME))
    from edgar.documents.types import NodeType, SemanticType

    unmapped = set(NodeType.__members__) - CONTAINER_NODE_TYPES - set(LEAF_NODE_TYPES)
    stale = (CONTAINER_NODE_TYPES | set(LEAF_NODE_TYPES)) - set(NodeType.__members__)
    missing_semantic = FOOTNOTE_SEMANTIC_TYPE not in SemanticType.__members__
    print(f"NodeType members: {sorted(NodeType.__members__)}")
    print(
        f"unmapped: {sorted(unmapped)}; stale: {sorted(stale)}; FOOTNOTE missing: {missing_semantic}"
    )
    return 1 if unmapped or stale or missing_semantic else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        raise SystemExit(self_check())
    raise SystemExit(run_adapter(parse, library="edgartools"))
```

`expirements/parser-fidelity/adapter_secparser.py`:

```python
# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = ["sec-parser==0.58.1"]
# ///
"""Candidate adapter: sec-parser 0.58.1, run in isolation.

Python 3.13, because sec-parser 0.58.1 requires lxml<6, which publishes no CPython
3.14 wheel (checked 2026-09-22 with ``uv pip compile --python-version 3.14
--only-binary lxml``). The parse path is the library's documented default:
``Edgar10QParser().parse(html)``, which returns a flat list (no nesting) and drops
IrrelevantElement subclasses. A table's text is exactly what the element emits; the
library exposes no cell grid.

    uv run --locked --script expirements/parser-fidelity/adapter_secparser.py --input S --output D --sidecar C
    uv run --locked --script expirements/parser-fidelity/adapter_secparser.py --self-check

Type mapping (class name, most specific first in the element's MRO -> common type).
"""

from __future__ import annotations

import sys

from pf_dump import Element, run_adapter

TYPE_BY_CLASS = {
    "TopSectionTitle": "heading",
    "TitleElement": "heading",
    "TableOfContentsElement": "table",
    "TableElement": "table",
    "TextElement": "paragraph",
    "SupplementaryText": "paragraph",
    "HighlightedTextElement": "other",
    "ImageElement": "other",
    "PageHeaderElement": "other",
    "PageNumberElement": "other",
    "EmptyElement": "other",
    "IntroductorySectionElement": "other",
    "IrrelevantElement": "other",
    "NotYetClassifiedElement": "other",
    "ErrorWhileProcessingElement": "other",
    "CompositeSemanticElement": "other",
    "AbstractSemanticElement": "other",
}


def common_type(element: object) -> str:
    for cls in type(element).__mro__:
        if cls.__name__ in TYPE_BY_CLASS:
            return TYPE_BY_CLASS[cls.__name__]
    raise TypeError(f"unmapped sec-parser element type {type(element).__name__}")


def convert(elements: list[object]) -> list[Element]:
    out = []
    for element in elements:
        kind = common_type(element)
        level = getattr(element, "level", None) if kind == "heading" else None
        out.append(
            Element(kind, element.text or "", None, level, type(element).__name__)
        )
    return out


def parse(html: str) -> list[Element]:
    import sec_parser  # imported after the network guard is installed

    return convert(sec_parser.Edgar10QParser().parse(html))


def self_check() -> int:
    """Every exported semantic element class must be mapped; run before the freeze."""
    import inspect

    import sec_parser
    from sec_parser.semantic_elements.abstract_semantic_element import (
        AbstractSemanticElement,
    )

    exported = {
        name
        for name, obj in inspect.getmembers(sec_parser, inspect.isclass)
        if issubclass(obj, AbstractSemanticElement)
    }
    unmapped = sorted(exported - set(TYPE_BY_CLASS))
    print(f"exported element classes: {sorted(exported)}")
    print(f"unmapped: {unmapped}")
    return 1 if unmapped else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        raise SystemExit(self_check())
    raise SystemExit(run_adapter(parse, library="sec-parser"))
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_adapters.py --import-mode=prepend -q`
Expected: `4 passed`.

- [x] **Step 5: Lock the three scripts**

```bash
uv lock --script expirements/parser-fidelity/control.py
uv lock --script expirements/parser-fidelity/adapter_edgartools.py
uv lock --script expirements/parser-fidelity/adapter_secparser.py
```

Expected: three `Resolved … packages` lines. The sec-parser lock resolves for Python
3.13; uv uses an installed 3.13 or downloads a managed one on first run.

If `uv lock --script` for `adapter_secparser.py` fails, or its self-check in Step 7
cannot install on Python 3.13 either, apply the spec's contingency: record sec-parser as
unmeasurable.

- Keep its adapter committed.
- Run the other candidates in Task 15 Step 6 and Task 19 Step 2 with
  `--candidates edgartools walker control`.
- sec-parser then has no runs, fails the determinism and network gates, and is never
  selected.
- V2 states that it was unmeasurable and that RG §2's claim stays untested.

- [x] **Step 6: Save the Python 3.14 evidence for sec-parser (P2)**

```bash
mkdir -p data/runs/parser-fidelity/evidence
printf 'sec-parser==0.58.1\n' > data/runs/parser-fidelity/evidence/secparser.in
uv pip compile data/runs/parser-fidelity/evidence/secparser.in --python-version 3.14 --only-binary lxml --quiet > data/runs/parser-fidelity/evidence/secparser-py314.txt 2>&1 || true
cat data/runs/parser-fidelity/evidence/secparser-py314.txt
```

Expected: `No solution found when resolving dependencies`, because `lxml>=5.2.2,<6.0.0`
has no usable wheels. V2 quotes this file.

- [x] **Step 7: Run the self-checks**

```bash
uv run --locked --script expirements/parser-fidelity/adapter_edgartools.py --self-check
uv run --locked --script expirements/parser-fidelity/adapter_secparser.py --self-check
```

Expected:

- edgartools: `unmapped: []; stale: []; FOOTNOTE missing: False`;
- sec-parser: `unmapped: []`.

Both exit 0. If a type is unmapped, the installed library has a public type this plan
did not see. Add it to the mapping by the library's documented meaning, add it to the
test in Step 1, and record the addition for V2. The mapping may still change here,
before the freeze.

- [x] **Step 8: Smoke-run every adapter on the development set only**

For each development release, and for each of `control.py`, `adapter_edgartools.py`,
and `adapter_secparser.py`:

```bash
for dev in data/raw/devset/*/source.html; do
  for script in control.py adapter_edgartools.py adapter_secparser.py; do
    uv run --locked --script expirements/parser-fidelity/$script --input "$dev" --output /tmp/pf-smoke.json --sidecar /tmp/pf-smoke.sidecar.json
    echo "$script $(basename "$(dirname "$dev")") exit=$?"
  done
done
```

Expected: every line ends `exit=0`.

- If a run exits 2 (crash), read `/tmp/pf-smoke.sidecar.json` and fix the adapter.
  All debugging happens on the development set.
- If a run exits 3 (`void_network`), the listed `guard_trips` show that the parse path
  touched the network. If adapter code caused it, fix the adapter. If the library
  itself did, record the finding for V2; that candidate will fail the network gate.

Never run an adapter on `tests/fixtures/` in this task.

- [x] **Step 9: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/control.py expirements/parser-fidelity/control.py.lock expirements/parser-fidelity/adapter_edgartools.py expirements/parser-fidelity/adapter_edgartools.py.lock expirements/parser-fidelity/adapter_secparser.py expirements/parser-fidelity/adapter_secparser.py.lock expirements/parser-fidelity/test_adapters.py
git commit -m "feat(parser-fidelity): add the control and the edgartools and sec-parser adapters"
```

---

### Task 13: Walker rules and gate C

**Files:**
- Create: `expirements/parser-fidelity/walker-rules.md`

**Interfaces:**
- Consumes: the data-table definition in `pf_classes` (Task 4).
- Produces: the approved rules W0–W16 that Task 14 implements. The walker's
  parameters are fixed here: at most 12 words for a styled heading, and at most 4
  characters for a marker.

- [x] **Step 1: Write the rules file**

`expirements/parser-fidelity/walker-rules.md`:

```markdown
# Bespoke walker rules

Status: draft, awaiting the user's approval (plan Task 13). Development starts only after
approval.

Written before development begins (spec: Candidate harness > Bespoke walker). The
walker is built only on the development set; no rule may name or target a fixture.
Development may correct how a rule below is implemented. It may not add, remove, or
retune a rule. A pattern the development set exposes that no rule covers goes under
**Known gaps**, with the release it came from, and stays unhandled.

Every numeric parameter is fixed here: a heading has at most **12** words; a list or
footnote marker cell holds at most **4** characters.

## Input

- **W0 — Parse.** The walker receives the shared decoded text (`pf_decode`) and parses
  it with lxml's HTML parser (`pf_classes.parse_document`), walking `<body>` in
  document order.
- **W1 — Invisible content.** Skip comments, processing instructions, `script`,
  `style`, `head`, `title`, `noscript`, `template`, and any element whose inline
  style sets `display: none`, with everything inside it. Text that follows a skipped
  element inside its parent is kept.

## Blocks

- **W2 — Tag meaning.** These tags start a block: `address`, `article`,
  `blockquote`, `center`, `dd`, `div`, `dl`, `dt`, `footer`, `h1`–`h6`, `header`,
  `hr`, `li`, `ol`, `p`, `pre`, `section`, `table`, `ul`. Text inside any other tag
  (`span`, `font`, `b`, `i`, `u`, `a`, `sup`, `sub`, inline XBRL tags, and so on) joins
  the enclosing block. Text before and after a nested block forms separate blocks.
- **W3 — Line breaks.** One `<br>` is a line break inside the block. Two or more in
  a row, with only whitespace between them, end the block.
- **W4 — Whitespace.** Runs of whitespace collapse to one space, and block text is
  stripped. A block with no text is dropped. `hr` emits nothing.
- **W5 — Preformatted text.** The text of a `pre` element splits into blocks at blank
  lines. Each piece is typed by W8–W12.

## Types

- **W6 — HTML headings.** `h1`–`h6` is a `heading` with level 1–6.
- **W7 — HTML lists.** `ul` and `ol` are containers (type `other`, no text), and each
  `li` is a `list_item` whose parent is its list and whose level is the list's
  nesting depth (1 is outermost). An `li` outside a list is a `list_item` with no
  parent.
- **W8 — Page numbers.** A block whose whole text is a page number, optionally with
  "Page" or dashes (the class tests' bare page-number pattern), is `other`.
- **W9 — Bullet glyphs.** A block that begins with a bullet glyph (• ● ◦ ▪ ■ ‣ ⁃ · ∙),
  with a hyphen or dash followed by a space, or with a run of at most 4 characters
  set in a Symbol or Wingdings font, is a `list_item` with no parent.
- **W10 — Footnote markers.** A block that begins with a footnote marker followed
  by text is a `footnote`. The markers are `(1)`–`(99)`, `(a)`–`(z)`, one to three
  `*`, `†`, `‡`, superscript digits, or a leading `sup` element of at most 4
  characters.
- **W11 — Styled headings.** A block of at most 12 words in which every character
  is bold or underlined is a `heading`, with no level. Bold means inside `b` or
  `strong`, or an inline `font-weight` of `bold`, `bolder`, or 600–900, with the
  nearest declaration winning. Underlined means inside `u` or `ins`, or an inline
  `text-decoration` that includes `underline`.
- **W12 — Otherwise** a block is a `paragraph`.

Rules W8–W11 apply in that order, and only to blocks that are not headings or list
items by W6 or W7.

## Tables

- **W13 — Marker tables.** A table is a marker table when every row with text has a
  first non-empty cell that holds only a marker (at most 4 characters) and has text
  in another cell. W9 bullets and enumerators such as `1.`, `a.`, and `iv.` make the
  row a `list_item`. W10 footnote markers make it a `footnote`. The element text is
  the row's other cells, joined by spaces. Marker tables are checked before W14.
- **W14 — Data tables.** A table that meets the class tests' data-table definition
  (`pf_classes.is_data_table`) is one `table` element carrying its grid.
  - Rows are its own visible rows, in document order, without rows that have no
    text.
  - Cells carry their visible text, including nested tables, and their `colspan` and
    `rowspan`.
  - A caption is emitted before the table as its own block, typed by W8–W12.
- **W15 — Header rows.** In a data table, header rows are these:
  - rows inside `thead`;
  - rows whose cells are all `th`;
  - leading rows before the first row that has a numeric-looking cell after its
    first cell (digits, commas, and periods, optionally with `$`, parentheses, `%`,
    or a dash). A bare four-digit year from 1900 to 2099 is a column label, not a
    number.
- **W16 — Layout tables.** Any other table is layout. Its cells are walked as
  ordinary content, row by row and cell by cell, and each cell ends a block.

## Known gaps

None yet.
```

- [x] **Step 2: Gate C — the user approves the rules**

Ask the user to review `walker-rules.md`. The rules shape the walker candidate, and the
spec requires them in writing before development begins. The user may edit any rule or
parameter now; after approval, no rule changes (P9). When the user approves, replace
the status paragraph with:

```markdown
Status: approved by <user's name> on <YYYY-MM-DD>, before development began.
```

Use the name and date the user gives.

- [x] **Step 3: Commit**

```bash
git add expirements/parser-fidelity/walker-rules.md
git commit -m "docs(parser-fidelity): approve the walker rules before development"
```

---

### Task 14: The bespoke walker

**Files:**
- Create: `expirements/parser-fidelity/walker.py`, `walker.py.lock`
- Test: `expirements/parser-fidelity/test_walker.py`
- Modify (Known gaps only): `expirements/parser-fidelity/walker-rules.md`

**Interfaces:**
- Consumes:
  - `pf_classes`: `BARE_PAGE_NUMBER`, `body_of`, `cell_text`, `is_data_table`,
    `is_hidden`, `own_cells`, `own_rows`, `parse_document`, and `visible_text`
    (Task 4);
  - `pf_dump` (Task 11);
  - the approved rules (Task 13).
- Produces:
  - `walker.parse(html: str) -> list[Element]`;
  - `walker.classify(runs, text) -> str`, `walker.marker_row(row)`, and
    `walker.data_grid(table, rows)`;
  - the script's CLI, which is `run_adapter`'s.

If the user changed any rule or parameter at gate C, edit the matching test below and
the matching constant or branch in `walker.py` before Step 1. The tests encode the
rules as drafted.

- [x] **Step 1: Write the failing tests (one per rule)**

`expirements/parser-fidelity/test_walker.py`:

```python
"""One test per walker rule (walker-rules.md)."""

from walker import parse


def kinds(html):
    return [(e.type, e.text) for e in parse(f"<html><body>{html}</body></html>")]


def test_w1_hidden_content_is_skipped_but_following_text_is_kept():
    assert kinds(
        '<p>Shown <span style="display:none">secret</span>tail</p><script>x()</script>'
    ) == [("paragraph", "Shown tail")]


def test_w2_block_tags_split_and_inline_tags_join():
    assert kinds("<div>Intro <b>bold</b> text<p>Inner block</p>after</div>") == [
        ("paragraph", "Intro bold text"),
        ("paragraph", "Inner block"),
        ("paragraph", "after"),
    ]


def test_w3_one_break_joins_two_breaks_split():
    assert kinds("<p>Line one<br>line two<br><br>Next block</p>") == [
        ("paragraph", "Line one line two"),
        ("paragraph", "Next block"),
    ]


def test_w4_whitespace_collapses_and_empty_blocks_drop():
    assert kinds("<p>  Net\n   sales  </p><p> </p><hr>") == [("paragraph", "Net sales")]


def test_w5_pre_splits_at_blank_lines():
    assert kinds("<pre>First paragraph\ncontinues.\n\n  \nSecond paragraph.</pre>") == [
        ("paragraph", "First paragraph continues."),
        ("paragraph", "Second paragraph."),
    ]


def test_w6_html_headings_carry_their_level():
    [heading] = parse("<html><body><h2>Outlook</h2></body></html>")
    assert (heading.type, heading.level) == ("heading", 2)


def test_w7_lists_are_containers_with_levelled_items():
    elements = parse(
        "<html><body><ul><li>One<ol><li>Nested</li></ol></li><li>Two</li></ul></body></html>"
    )
    assert [(e.type, e.text, e.parent, e.level) for e in elements] == [
        ("other", "", None, None),
        ("list_item", "One", 0, 1),
        ("other", "", 0, None),
        ("list_item", "Nested", 2, 2),
        ("list_item", "Two", 0, 1),
    ]


def test_w8_bare_page_numbers_are_other():
    assert kinds("<p>- 12 -</p><p>Page 3</p>") == [
        ("other", "- 12 -"),
        ("other", "Page 3"),
    ]


def test_w9_bullet_glyphs_and_symbol_fonts_make_list_items():
    html = (
        "<p>\u2022 Revenue grew</p><p>- Margin expanded</p>"
        '<p><font face="Wingdings">\xa7</font> Cash rose</p>'
    )
    assert kinds(html) == [
        ("list_item", "\u2022 Revenue grew"),
        ("list_item", "- Margin expanded"),
        ("list_item", "\xa7 Cash rose"),
    ]


def test_w10_footnote_markers():
    assert kinds(
        "<p>(1) Excludes charges.</p><p>* Non-GAAP.</p><p><sup>2</sup> Restated.</p>"
    ) == [
        ("footnote", "(1) Excludes charges."),
        ("footnote", "* Non-GAAP."),
        ("footnote", "2 Restated."),
    ]


def test_w11_short_fully_bold_or_underlined_blocks_are_headings():
    html = (
        "<p><b>Business Highlights</b></p>"
        '<p style="font-weight:700">About Acme Corp.</p>'
        "<p><u>Outlook</u></p>"
        "<p><b>Revenue:</b> rose five percent.</p>"
        '<p style="font-weight:bold"><span style="font-weight:normal">Not bold</span></p>'
    )
    assert kinds(html) == [
        ("heading", "Business Highlights"),
        ("heading", "About Acme Corp."),
        ("heading", "Outlook"),
        ("paragraph", "Revenue: rose five percent."),
        ("paragraph", "Not bold"),
    ]


def test_w11_long_bold_blocks_stay_paragraphs():
    words = " ".join(["word"] * 13)
    assert kinds(f"<p><b>{words}</b></p>") == [("paragraph", words)]


def test_w13_marker_tables_become_list_items_or_footnotes():
    html = (
        "<table><tr><td>\u2022</td><td>Opened three plants</td></tr>"
        "<tr><td>\u2022</td><td>Cut costs</td></tr></table>"
        "<table><tr><td>(1)</td><td>Excludes the divestiture.</td></tr></table>"
    )
    assert kinds(html) == [
        ("list_item", "Opened three plants"),
        ("list_item", "Cut costs"),
        ("footnote", "Excludes the divestiture."),
    ]


def test_w14_w15_data_tables_carry_their_grid_and_header_rows():
    html = (
        "<table><caption>Summary</caption>"
        '<tr><td></td><td colspan="2">Three Months Ended</td></tr>'
        "<tr><td></td><td>2025</td><td>2024</td></tr>"
        "<tr><td></td><td></td><td></td></tr>"
        "<tr><td>Net sales</td><td>$ 4,321</td><td>(3,210)</td></tr></table>"
    )
    elements = parse(f"<html><body>{html}</body></html>")
    assert [(e.type, e.text) for e in elements] == [
        ("paragraph", "Summary"),
        ("table", " Three Months Ended\n 2025 2024\nNet sales $ 4,321 (3,210)"),
    ]
    rows = elements[1].rows
    assert [row.header for row in rows] == [True, True, False]
    assert rows[0].cells[1].colspan == 2


def test_w16_layout_tables_are_walked_cell_by_cell():
    html = "<table><tr><td><p><b>Outlook</b></p><p>We expect growth.</p></td><td>Contact: IR</td></tr></table>"
    assert kinds(html) == [
        ("heading", "Outlook"),
        ("paragraph", "We expect growth."),
        ("paragraph", "Contact: IR"),
    ]


def test_parse_is_deterministic():
    html = "<html><body><h1>T</h1><p>x</p><table><tr><td>a</td><td>1</td></tr><tr><td>b</td><td>2</td></tr></table></body></html>"
    assert parse(html) == parse(html)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_walker.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'walker'`.

- [x] **Step 3: Write the walker**

`expirements/parser-fidelity/walker.py`:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["lxml==6.1.3", "beautifulsoup4==4.15.0"]
# ///
"""Candidate: the bespoke lxml walker. Its rules are in walker-rules.md (W0-W16).

Developed only on the development set; frozen before its first fixture run.

    uv run --locked --script expirements/parser-fidelity/walker.py --input S --output D --sidecar C
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

from lxml.html import HtmlElement
from pf_classes import (
    BARE_PAGE_NUMBER,
    body_of,
    cell_text,
    is_data_table,
    is_hidden,
    own_cells,
    own_rows,
    parse_document,
    visible_text,
)
from pf_dump import Cell, Element, Row, grid_text, run_adapter

BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "blockquote",
        "center",
        "dd",
        "div",
        "dl",
        "dt",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "ul",
    }
)
HEADING_TAGS = {f"h{n}": n for n in range(1, 7)}
MAX_HEADING_WORDS = 12
MAX_MARKER_CHARS = 4
BULLETS = "\u2022\u25cf\u25e6\u25aa\u25a0\u2023\u2043\xb7\u2219"
_BULLET_START = re.compile(rf"^(?:[{BULLETS}]|[-\u2013\u2014]\s)")
_FOOTNOTE_MARKER = (
    r"\(\d{1,2}\)|\([a-z]\)|\*{1,3}|[\u2020\u2021]|[\xb9\xb2\xb3\u2070-\u2079]+"
)
_FOOTNOTE_START = re.compile(rf"^(?:{_FOOTNOTE_MARKER})\s*\S")
_FOOTNOTE_CELL = re.compile(rf"^(?:{_FOOTNOTE_MARKER})$")
_LIST_CELL = re.compile(
    rf"^(?:[{BULLETS}\u2013\u2014-]|\d{{1,2}}\.|[a-z]\.|[ivx]{{1,4}}\.)$", re.IGNORECASE
)
_NUMERIC_CELL = re.compile(r"^[\$\(\-\u2013\u2014]*\s*[\d.,]*\d[\d.,]*\s*%?\)?$")
_YEAR = re.compile(r"^(?:19|20)\d{2}$")
_FONT_WEIGHT = re.compile(r"font-weight\s*:\s*([a-z0-9]+)", re.IGNORECASE)
_DECORATION = re.compile(
    r"text-decoration(?:-line)?\s*:\s*[^;]*underline", re.IGNORECASE
)
_SYMBOL_FONT = re.compile(r"wingdings|symbol", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class Style:
    bold: bool = False
    underline: bool = False
    sup: bool = False
    symbol_font: bool = False


@dataclass(frozen=True)
class Run:
    text: str
    style: Style


BREAK = Run("\n", Style())  # a <br>; two in a row end the block (W3)


def child_style(el: HtmlElement, style: Style) -> Style:
    tag = el.tag
    css = el.get("style") or ""
    bold = style.bold or tag in ("b", "strong")
    weight = _FONT_WEIGHT.search(css)
    if weight:
        value = weight.group(1).lower()
        bold = value in ("bold", "bolder") or (value.isdigit() and int(value) >= 600)
    underline = style.underline or tag in ("u", "ins") or bool(_DECORATION.search(css))
    face = f"{el.get('face') or ''} {css}"
    symbol = style.symbol_font or bool(_SYMBOL_FONT.search(face))
    return Style(bold, underline, style.sup or tag == "sup", symbol)


def collapse(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


class Walker:
    def __init__(self) -> None:
        self.elements: list[Element] = []
        self.lists: list[int] = []  # indices of the open ul/ol containers (W7)

    def emit(
        self,
        kind: str,
        text: str,
        *,
        parent: int | None = None,
        level: int | None = None,
        source: str,
    ) -> None:
        self.elements.append(Element(kind, text, parent, level, source))

    # -- blocks ---------------------------------------------------------------
    def walk_block(self, el: HtmlElement, style: Style, kind: str) -> None:
        runs: list[Run] = []
        self.walk_content(el, style, runs, kind)
        self.flush(runs, kind, el.tag)

    def walk_content(
        self, el: HtmlElement, style: Style, runs: list[Run], kind: str
    ) -> None:
        if el.text:
            runs.append(Run(el.text, style))
        for child in el:
            self.walk_node(child, style, runs, kind, el.tag)
            if child.tail:
                runs.append(Run(child.tail, style))

    def walk_node(
        self, el: HtmlElement, style: Style, runs: list[Run], kind: str, owner: str
    ) -> None:
        if is_hidden(el):
            return
        tag = el.tag
        if tag == "br":
            runs.append(BREAK)
        elif tag in BLOCK_TAGS:
            self.flush(runs, kind, owner)
            runs.clear()
            self.walk_block_element(el, child_style(el, style))
        else:
            self.walk_content(el, child_style(el, style), runs, kind)

    def walk_block_element(self, el: HtmlElement, style: Style) -> None:
        tag = el.tag
        if tag in HEADING_TAGS:
            self.walk_block(el, style, f"heading{HEADING_TAGS[tag]}")
        elif tag in ("ul", "ol"):
            self.walk_list(el, style)
        elif tag == "li":
            self.walk_block(el, style, "list_item")
        elif tag == "table":
            self.walk_table(el, style)
        elif tag == "pre":
            self.walk_pre(el, style)
        elif tag != "hr":
            self.walk_block(el, style, "block")

    def walk_list(self, el: HtmlElement, style: Style) -> None:
        parent = self.lists[-1] if self.lists else None
        self.emit("other", "", parent=parent, source=el.tag)
        self.lists.append(len(self.elements) - 1)
        self.walk_block(el, style, "block")
        self.lists.pop()

    def walk_pre(self, el: HtmlElement, style: Style) -> None:
        text = cell_text(el)
        for piece in re.split(r"\n[ \t\r\f\v]*\n", text):
            self.flush([Run(piece, style)], "block", "pre")

    # -- typing ---------------------------------------------------------------
    def flush(self, runs: list[Run], kind: str, source: str) -> None:
        segment: list[Run] = []
        breaks = 0
        for run in runs:
            if run is BREAK:
                breaks += 1
                if breaks >= 2:
                    self.emit_block(segment, kind, source)
                    segment = []
                    continue
            elif run.text.strip():
                breaks = 0
            segment.append(run)
        self.emit_block(segment, kind, source)

    def emit_block(self, runs: list[Run], kind: str, source: str) -> None:
        text = collapse("".join(run.text for run in runs))
        if not text:
            return
        if kind.startswith("heading"):
            self.emit(
                "heading", text, level=int(kind.removeprefix("heading")), source=source
            )
        elif kind == "list_item":
            parent = self.lists[-1] if self.lists else None
            self.emit(
                "list_item",
                text,
                parent=parent,
                level=len(self.lists) or None,
                source=source,
            )
        else:
            self.emit(classify(runs, text), text, source=source)

    # -- tables ---------------------------------------------------------------
    def walk_table(self, table: HtmlElement, style: Style) -> None:
        caption = table.find("caption")
        if caption is not None and not is_hidden(caption):
            self.walk_block(caption, child_style(caption, style), "block")
        rows = [
            row
            for row in own_rows(table)
            if any(collapse(visible_text(c)) for c in own_cells(row))
        ]
        marker_rows = [marker_row(row) for row in rows]
        if rows and all(marker_rows):
            for kind, text in marker_rows:
                self.emit(kind, text, source="marker-table")
        elif is_data_table(table):
            grid = data_grid(table, rows)
            self.emit_table(grid)
        else:
            for row in own_rows(table):
                for cell in own_cells(row):
                    self.walk_block(cell, child_style(cell, style), "block")

    def emit_table(self, grid: tuple[Row, ...]) -> None:
        self.elements.append(
            Element("table", grid_text(grid), None, None, "table", grid)
        )


def classify(runs: list[Run], text: str) -> str:
    """W8-W12 for a block that is not a heading or list item by tag."""
    if BARE_PAGE_NUMBER.fullmatch(text):
        return "other"
    first = next((run for run in runs if run.text.strip()), None)
    if _BULLET_START.match(text) or (
        first
        and first.style.symbol_font
        and len(first.text.strip()) <= MAX_MARKER_CHARS
    ):
        return "list_item"
    if _FOOTNOTE_START.match(text) or (
        first
        and first.style.sup
        and len(first.text.strip()) <= MAX_MARKER_CHARS
        and len(text) > len(first.text.strip())
    ):
        return "footnote"
    styled = all(
        run.style.bold or run.style.underline for run in runs if run.text.strip()
    )
    if styled and len(text.split()) <= MAX_HEADING_WORDS:
        return "heading"
    return "paragraph"


def marker_row(row: HtmlElement) -> tuple[str, str] | None:
    """W13: (type, text) when the row's first non-empty cell holds only a marker."""
    texts = [collapse(visible_text(cell)) for cell in own_cells(row)]
    filled = [text for text in texts if text]
    if len(filled) < 2 or len(filled[0]) > MAX_MARKER_CHARS:
        return None
    marker, rest = filled[0], " ".join(filled[1:])
    if _FOOTNOTE_CELL.match(marker):
        return "footnote", rest
    if _LIST_CELL.match(marker):
        return "list_item", rest
    return None


def data_grid(table: HtmlElement, rows: list[HtmlElement]) -> tuple[Row, ...]:
    """W14-W15: the grid with header flags."""
    cells = [own_cells(row) for row in rows]
    numeric_seen = False
    grid = []
    for row, row_cells in zip(rows, cells, strict=True):
        texts = [collapse(visible_text(cell)) for cell in row_cells]
        numeric = any(
            _NUMERIC_CELL.match(text) and not _YEAR.match(text)
            for text in texts[1:]
            if text
        )
        numeric_seen = numeric_seen or numeric
        all_th = bool(row_cells) and all(cell.tag == "th" for cell in row_cells)
        header = _in_thead(row, table) or all_th or not numeric_seen
        spans = [
            Cell(text, _span(cell, "colspan"), _span(cell, "rowspan"))
            for cell, text in zip(row_cells, texts, strict=True)
        ]
        grid.append(Row(header, tuple(spans)))
    return tuple(grid)


def _in_thead(row: HtmlElement, table: HtmlElement) -> bool:
    parent = row.getparent()
    while parent is not None and parent is not table:
        if parent.tag == "thead":
            return True
        parent = parent.getparent()
    return False


def _span(cell: HtmlElement, name: str) -> int:
    value = (cell.get(name) or "1").strip()
    return max(1, int(value)) if value.isdigit() else 1


def parse(html: str) -> list[Element]:
    sys.setrecursionlimit(
        max(sys.getrecursionlimit(), 20000)
    )  # deeply nested font soup
    walker = Walker()
    walker.walk_block(body_of(parse_document(html)), Style(), "block")
    return walker.elements


if __name__ == "__main__":
    raise SystemExit(run_adapter(parse, library="lxml"))
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_walker.py --import-mode=prepend -q`
Expected: `16 passed`.

- [x] **Step 5: Lock the script**

Run: `uv lock --script expirements/parser-fidelity/walker.py`
Expected: `Resolved … packages`.

- [x] **Step 6: Develop on the development set**

Run the walker on each development release, print its dump, and compare the dump
with the release's browser rendering:

```bash
for dev in data/raw/devset/*/source.html; do
  uv run --locked --script expirements/parser-fidelity/walker.py --input "$dev" --output /tmp/pf-walker.json --sidecar /tmp/pf-walker.sidecar.json
  uv run --locked --all-packages python -c "import json; [print(i, e['type'], repr(e['text'][:90])) for i, e in enumerate(json.load(open('/tmp/pf-walker.json'))['elements'])]"
done
```

For each mismatch with the rendering, decide:

- **A written rule is implemented wrongly.** Add a failing test that reproduces it on
  a synthetic snippet, fix `walker.py`, and rerun Step 4.
- **No written rule covers it.** Append it under Known gaps in `walker-rules.md`, as
  `- <pattern> (seen in the development release <id>)`, and leave it unhandled.
  Never add, remove, or retune a rule, and never name or target a fixture.

- [x] **Step 7: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/walker.py expirements/parser-fidelity/walker.py.lock expirements/parser-fidelity/test_walker.py expirements/parser-fidelity/walker-rules.md
git commit -m "feat(parser-fidelity): add the bespoke lxml walker"
```

---

### Task 15: Runner, gates, and the freeze

**Files:**
- Create: `expirements/parser-fidelity/run_candidates.py`
- Create: `expirements/parser-fidelity/freeze.py`
- Create (generated): `expirements/parser-fidelity/FROZEN.toml`
- Test: `expirements/parser-fidelity/test_run_candidates.py`, `expirements/parser-fidelity/test_freeze.py`

**Interfaces:**
- Consumes: `validate_gold.validate_fixture` (Task 8), `pf_toml` (Task 7), and every
  adapter script (Tasks 12 and 14).
- Produces:
  - `run_candidates`:
    - `CANDIDATES`, keyed `edgartools`, `secparser`, `walker`, and `control`, whose
      values are `Candidate(script, selectable)`;
    - `run_pair(candidate, source, out_dir, runner) -> dict`;
    - `fixture_preconditions() -> list[str]`;
    - `child_env()`.
  - `data/runs/parser-fidelity/<set>/<candidate>/<id>/run{1,2}.json`, with
    `.sidecar.json` and `.log`.
  - `data/runs/parser-fidelity/<set>/gates.json`, holding per candidate and release:
    `status`, `deterministic`, `guard_trips`, `python`, `library_version`,
    `parse_seconds`, and `error`.
  - `freeze`:
    - `FROZEN_FILES`;
    - `record(...)`, `verify(harness, freeze_file) -> list[str]`, and `amend(...)`;
    - `ALLOWED_REASONS = ("crash", "network-guard")`.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_freeze.py`:

```python
import datetime as dt

import pytest
from freeze import FROZEN_FILES, amend, load, record, verify

TODAY = dt.date(2026, 10, 2)


@pytest.fixture
def harness(tmp_path):
    for name in FROZEN_FILES:
        (tmp_path / name).write_text(f"# {name}\n")
    return tmp_path


def test_record_then_verify_passes(harness):
    freeze_file = harness / "FROZEN.toml"
    record(harness, freeze_file, "abc123", TODAY)
    assert verify(harness, freeze_file) == []
    frozen = load(freeze_file)
    assert frozen["commit"] == "abc123" and frozen["frozen_on"] == TODAY
    with pytest.raises(FileExistsError):
        record(harness, freeze_file, "def456", TODAY)


def test_unrecorded_change_fails_verification(harness):
    freeze_file = harness / "FROZEN.toml"
    record(harness, freeze_file, "abc123", TODAY)
    (harness / "walker.py").write_text("# retuned\n")
    assert verify(harness, freeze_file) == [
        "walker.py changed after the freeze without a recorded crash or network-guard fix"
    ]


def test_amend_records_a_permitted_fix(harness):
    freeze_file = harness / "FROZEN.toml"
    record(harness, freeze_file, "abc123", TODAY)
    (harness / "adapter_edgartools.py").write_text("# crash fix\n")
    amend(
        harness,
        freeze_file,
        "adapter_edgartools.py",
        "crash",
        "None caption crashed",
        TODAY,
    )
    assert verify(harness, freeze_file) == []
    [change] = load(freeze_file)["changes"]
    assert change["reason"] == "crash" and change["previous_sha256"] != change["sha256"]


def test_amend_refuses_other_reasons_and_no_ops(harness):
    freeze_file = harness / "FROZEN.toml"
    record(harness, freeze_file, "abc123", TODAY)
    with pytest.raises(ValueError, match="reason must be one of"):
        amend(harness, freeze_file, "walker.py", "tuning", "better headings", TODAY)
    with pytest.raises(ValueError, match="unchanged"):
        amend(harness, freeze_file, "walker.py", "crash", "nothing", TODAY)


def test_verify_without_a_freeze_file_fails(harness):
    assert "is missing" in verify(harness, harness / "FROZEN.toml")[0]
```

`expirements/parser-fidelity/test_run_candidates.py`:

```python
import json
import subprocess
from pathlib import Path

import run_candidates
from run_candidates import Candidate, child_env, run_pair


def fake_runner(outputs):
    """Stand-in for subprocess.run: writes the dump and sidecar an adapter would write."""
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        dump = command[command.index("--output") + 1]
        sidecar = command[command.index("--sidecar") + 1]
        status, body = outputs[len(calls) - 1]
        if body is not None:
            Path(dump).write_bytes(body)
        side = {"status": status, "python": "3.14.0", "parse_seconds": 0.1}
        if status == "void_network":
            side["guard_trips"] = ["socket.getaddrinfo"]
        Path(sidecar).write_text(json.dumps(side))
        return subprocess.CompletedProcess(command, 0, "", "")

    return runner, calls


def test_identical_dumps_are_deterministic(tmp_path):
    runner, calls = fake_runner([("ok", b"A"), ("ok", b"A")])
    outcome = run_pair(
        Candidate("walker.py", True), tmp_path / "s.html", tmp_path / "out", runner
    )
    assert outcome["deterministic"] is True and outcome["status"] == ["ok", "ok"]
    command, kwargs = calls[0]
    assert command[:4] == ["uv", "run", "--locked", "--script"]
    assert "PYTHONHASHSEED" not in kwargs["env"]


def test_different_dumps_fail_the_determinism_gate(tmp_path):
    runner, _ = fake_runner([("ok", b"A"), ("ok", b"B")])
    assert (
        run_pair(
            Candidate("walker.py", True), tmp_path / "s.html", tmp_path / "out", runner
        )["deterministic"]
        is False
    )


def test_a_guard_trip_is_reported_and_voids_determinism(tmp_path):
    runner, _ = fake_runner([("void_network", None), ("ok", b"A")])
    outcome = run_pair(
        Candidate("adapter_edgartools.py", True),
        tmp_path / "s.html",
        tmp_path / "out",
        runner,
    )
    assert outcome["guard_trips"] == ["socket.getaddrinfo"]
    assert outcome["deterministic"] is False


def test_child_env_drops_pythonhashseed_and_points_edgar_home(monkeypatch):
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    env = child_env()
    assert "PYTHONHASHSEED" not in env
    assert env["EDGAR_LOCAL_DATA_DIR"].endswith("edgar-home")


def test_fixture_runs_refuse_until_freeze_and_gold_are_ready(tmp_path, monkeypatch):
    folder = tmp_path / "0001234567-25-000123_ex-99-1"
    folder.mkdir()
    (folder / "source.html").write_text("<p>x</p>")
    monkeypatch.setattr(
        run_candidates,
        "verify",
        lambda harness, freeze_file: ["FROZEN.toml is missing"],
    )
    problems = run_candidates.fixture_preconditions(tmp_path)
    assert "FROZEN.toml is missing" in problems
    assert any("gold.toml is missing" in p for p in problems)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_freeze.py expirements/parser-fidelity/test_run_candidates.py --import-mode=prepend -q`
Expected: 2 collection errors, `No module named 'freeze'` and `No module named 'run_candidates'`.

- [x] **Step 3: Write the implementation**

`expirements/parser-fidelity/freeze.py`:

```python
"""Freeze the files that shape candidate dumps (spec: Candidate harness > Freeze).

    uv run --locked --all-packages python expirements/parser-fidelity/freeze.py record
    uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
    uv run --locked --all-packages python expirements/parser-fidelity/freeze.py amend FILE --reason crash --note "..."

``record`` writes FROZEN.toml with the sha256 of every frozen file; the files must be
committed first, and FROZEN.toml is committed before any candidate runs on a fixture.
After the freeze a frozen file may change only to fix a crash or a network-guard trip
caused by harness code; ``amend`` records such a change, and ``verify`` fails on any
change that is not recorded. A change may never alter a type mapping or a walker rule.
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

FROZEN_FILES = (
    "adapter_edgartools.py",
    "adapter_edgartools.py.lock",
    "adapter_secparser.py",
    "adapter_secparser.py.lock",
    "control.py",
    "control.py.lock",
    "walker.py",
    "walker.py.lock",
    "pf_classes.py",
    "pf_decode.py",
    "pf_dump.py",
    "pf_paths.py",
    "pf_space.py",
)
FREEZE_FILE = HARNESS / "FROZEN.toml"
ALLOWED_REASONS = ("crash", "network-guard")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(freeze_file: Path) -> dict:
    return tomllib.loads(freeze_file.read_text(encoding="utf-8"))


def expected_hashes(freeze: dict) -> dict[str, str]:
    expected = dict(freeze["files"])
    for change in freeze.get("changes", []):
        expected[change["file"]] = change["sha256"]
    return expected


def render(freeze: dict) -> str:
    lines = [
        "# Frozen before the first candidate run on any fixture. Generated by freeze.py; do not edit.",
        f"frozen_on = {toml_value(Bare(str(freeze['frozen_on'])))}",
        f"commit = {toml_value(freeze['commit'])}",
        "",
        "[files]",
    ]
    lines += [
        f"{toml_value(name)} = {toml_value(sha)}"
        for name, sha in freeze["files"].items()
    ]
    for change in freeze.get("changes", []):
        lines += ["", "[[changes]]"]
        lines += [
            f"{key} = {toml_value(Bare(str(change[key])) if key == 'date' else change[key])}"
            for key in ("file", "reason", "previous_sha256", "sha256", "date", "note")
        ]
    return "\n".join(lines) + "\n"


def record(harness: Path, freeze_file: Path, commit: str, today: dt.date) -> dict:
    if freeze_file.exists():
        raise FileExistsError(
            f"{freeze_file} exists; use amend for a permitted post-freeze change"
        )
    freeze = {
        "frozen_on": today,
        "commit": commit,
        "files": {name: sha256_of(harness / name) for name in FROZEN_FILES},
    }
    freeze_file.write_text(render(freeze), encoding="utf-8")
    return freeze


def verify(harness: Path, freeze_file: Path) -> list[str]:
    if not freeze_file.exists():
        return [
            f"{freeze_file.name} is missing: run `freeze.py record` before any fixture run"
        ]
    expected = expected_hashes(load(freeze_file))
    return [
        f"{name} changed after the freeze without a recorded crash or network-guard fix"
        for name, sha in expected.items()
        if sha256_of(harness / name) != sha
    ]


def amend(
    harness: Path, freeze_file: Path, name: str, reason: str, note: str, today: dt.date
) -> dict:
    if reason not in ALLOWED_REASONS:
        raise ValueError(
            f"reason must be one of {ALLOWED_REASONS}; type mappings and walker rules never change"
        )
    freeze = load(freeze_file)
    previous = expected_hashes(freeze)[name]
    current = sha256_of(harness / name)
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
    freeze.setdefault("changes", []).append(change)
    freeze_file.write_text(render(freeze), encoding="utf-8")
    return freeze


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
    fix.add_argument("file", choices=FROZEN_FILES)
    fix.add_argument("--reason", required=True, choices=ALLOWED_REASONS)
    fix.add_argument("--note", required=True)
    args = parser.parse_args(argv)
    today = dt.datetime.now(dt.UTC).date()

    if args.command == "verify":
        problems = verify(HARNESS, FREEZE_FILE)
        print("\n".join(problems) or "freeze verified")
        return 1 if problems else 0
    paths = [str((HARNESS / name).relative_to(REPO_ROOT)) for name in FROZEN_FILES]
    if (
        _git("diff", "--quiet", "HEAD", "--", *paths).returncode != 0
        or _git("ls-files", "--error-unmatch", *paths).returncode != 0
    ):
        print(
            "commit every frozen file first; the freeze must name a commit that contains them",
            file=sys.stderr,
        )
        return 1
    if args.command == "record":
        commit = _git("rev-parse", "HEAD").stdout.strip()
        record(HARNESS, FREEZE_FILE, commit, today)
        print(
            f"froze {len(FROZEN_FILES)} files at {commit}; commit {FREEZE_FILE.name} now"
        )
        return 0
    amend(HARNESS, FREEZE_FILE, args.file, args.reason, args.note, today)
    print(
        f"recorded a post-freeze {args.reason} fix to {args.file}; commit it with {FREEZE_FILE.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`expirements/parser-fidelity/run_candidates.py`:

```python
"""Run every candidate twice per release, in separate processes (spec: Candidate harness).

    uv run --locked --all-packages python expirements/parser-fidelity/run_candidates.py dev
    uv run --locked --all-packages python expirements/parser-fidelity/run_candidates.py fixtures [--candidates walker ...]

Each run is ``uv run --locked --script <adapter>`` in a fresh process with default hash
randomization (PYTHONHASHSEED is removed from the child environment). The two dumps are
compared byte for byte (determinism gate); any network-guard trip voids the run (network
gate). Fixture runs refuse to start until the freeze verifies and every gold file passes
the validator, so no candidate output exists before the gold is complete.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from freeze import FREEZE_FILE, verify
from pf_paths import DEVSET, EDGAR_HOME, FIXTURES, HARNESS, REPO_ROOT, RUNS
from validate_gold import validate_fixture

RUN_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class Candidate:
    script: str
    selectable: bool


CANDIDATES = {
    "edgartools": Candidate("adapter_edgartools.py", True),
    "secparser": Candidate("adapter_secparser.py", True),
    "walker": Candidate("walker.py", True),
    "control": Candidate("control.py", False),
}


def release_inputs(
    set_name: str, fixtures: Path = FIXTURES, devset: Path = DEVSET
) -> dict[str, Path]:
    root = fixtures if set_name == "fixtures" else devset
    return {path.parent.name: path for path in sorted(root.glob("*/source.html"))}


def fixture_preconditions(fixtures: Path = FIXTURES) -> list[str]:
    problems = verify(HARNESS, FREEZE_FILE)
    for folder in sorted(path.parent for path in fixtures.glob("*/source.html")):
        report = validate_fixture(folder)
        problems += [f"{folder.name}: gold: {error}" for error in report.errors]
    return problems


def child_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key != "PYTHONHASHSEED"}
    env["EDGAR_LOCAL_DATA_DIR"] = str(EDGAR_HOME)
    return env


def run_once(
    candidate: Candidate,
    source: Path,
    out_dir: Path,
    number: int,
    runner: Callable = subprocess.run,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    dump, sidecar = out_dir / f"run{number}.json", out_dir / f"run{number}.sidecar.json"
    for stale in (dump, sidecar):
        stale.unlink(missing_ok=True)
    command = [
        "uv", "run", "--locked", "--script", str(HARNESS / candidate.script),
        "--input", str(source), "--output", str(dump), "--sidecar", str(sidecar),
    ]  # fmt: skip
    try:
        completed = runner(
            command,
            cwd=REPO_ROOT,
            env=child_env(),
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
        )
        log = f"exit {completed.returncode}\n--- stdout\n{completed.stdout}\n--- stderr\n{completed.stderr}"
    except subprocess.TimeoutExpired:
        log = f"timed out after {RUN_TIMEOUT_SECONDS}s"
    (out_dir / f"run{number}.log").write_text(log, encoding="utf-8")
    if not sidecar.exists():
        return {"status": "no_sidecar", "dump": None}
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["dump"] = str(dump) if dump.exists() else None
    return data


def run_pair(
    candidate: Candidate, source: Path, out_dir: Path, runner: Callable = subprocess.run
) -> dict:
    first = run_once(candidate, source, out_dir, 1, runner)
    second = run_once(candidate, source, out_dir, 2, runner)
    both_ok = first["status"] == second["status"] == "ok"
    deterministic = (
        both_ok
        and Path(first["dump"]).read_bytes() == Path(second["dump"]).read_bytes()
    )
    return {
        "status": [first["status"], second["status"]],
        "deterministic": deterministic,
        "guard_trips": first.get("guard_trips", []) + second.get("guard_trips", []),
        "python": first.get("python"),
        "library_version": first.get("library_version"),
        "parse_seconds": [first.get("parse_seconds"), second.get("parse_seconds")],
        "error": first.get("error") or second.get("error"),
    }


def run_set(set_name: str, names: list[str], runner: Callable = subprocess.run) -> dict:
    results: dict = {}
    gates_path = RUNS / set_name / "gates.json"
    if gates_path.exists():
        results = json.loads(gates_path.read_text(encoding="utf-8"))
    for name in names:
        results[name] = {}
        for fid, source in release_inputs(set_name).items():
            outcome = run_pair(
                CANDIDATES[name], source, RUNS / set_name / name / fid, runner
            )
            results[name][fid] = outcome
            print(
                f"{name:10} {fid}  status={outcome['status']}  deterministic={outcome['deterministic']}"
            )
    gates_path.parent.mkdir(parents=True, exist_ok=True)
    gates_path.write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("set", choices=("dev", "fixtures"))
    parser.add_argument(
        "--candidates", nargs="+", choices=sorted(CANDIDATES), default=list(CANDIDATES)
    )
    args = parser.parse_args(argv)
    if args.set == "fixtures":
        problems = fixture_preconditions()
        if problems:
            print(
                "refusing to run candidates on fixtures:\n" + "\n".join(problems),
                file=sys.stderr,
            )
            return 1
    if not release_inputs(args.set):
        print(f"no releases found for the {args.set} set", file=sys.stderr)
        return 1
    run_set(args.set, args.candidates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_freeze.py expirements/parser-fidelity/test_run_candidates.py --import-mode=prepend -q`
Expected: `10 passed`.

- [x] **Step 5: Commit the runner and freeze tool**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/run_candidates.py expirements/parser-fidelity/freeze.py expirements/parser-fidelity/test_run_candidates.py expirements/parser-fidelity/test_freeze.py
git commit -m "feat(parser-fidelity): add the candidate runner, gates, and freeze tool"
```

- [x] **Step 6: Dry-run every candidate on the development set**

Run: `uv run --locked --all-packages python expirements/parser-fidelity/run_candidates.py dev`

Expected: one line per candidate and development release, each
`status=['ok', 'ok']  deterministic=True`. This also warms each script's environment.

- If a candidate is nondeterministic on the development set, find the cause before
  freezing. The usual causes are an unordered set or dict in adapter code, or
  run-varying content leaking into the dump. Fix it only in adapter or harness code.
- If the library itself is nondeterministic, record it for V2; that candidate will
  fail the determinism gate.

- [x] **Step 7: Freeze**

Every frozen file must be committed and unchanged. Then:

```bash
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py record
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
git add expirements/parser-fidelity/FROZEN.toml
git commit -m "chore(parser-fidelity): freeze candidate sources before any fixture run"
```

Expected:

- `record` prints `froze 13 files at <commit>; commit FROZEN.toml now`;
- `verify` prints `freeze verified`.

From here on, a frozen file changes only to fix a crash or a network-guard trip that
harness code caused, and each such fix is recorded with `freeze.py amend <file>
--reason crash|network-guard --note "<what and why>"`. V2 lists every entry with its
diff.

---

### Task 16: V1 — edgartools 5.58.0 return types (live)

This task can run while gate B is open: it uses the fixture filings' identifiers from
the manifest, not the gold.

**Files:**
- Create: `expirements/parser-fidelity/v1_return_types.py`, `v1_return_types.py.lock`
- Create: `docs/verification/V1-edgartools-return-types.md`
- Test: `expirements/parser-fidelity/test_v1_return_types.py`

**Interfaces:**
- Consumes: `pf_fetch` (`LiveLock`, `LivePolicyStop`, `Throttle`, `require_identity`,
  `DEFAULT_MAX_REQUESTS`), `pf_paths` (`EDGAR_HOME`, `LIVE_LOCK`, `MANIFEST`, `RUNS`), and
  `tests/fixtures/releases/manifest.toml` (Task 7).
- Produces:
  - `data/runs/parser-fidelity/v1/v1-results.json` and `v1-results.md`, the latter a
    table plus the conclusion line and the request count;
  - `declared(owner, member) -> str`, `describe(obj) -> dict`,
    `conclusion(records) -> str`, and `install_transport_throttle(throttle)`;
  - the V1 record.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_v1_return_types.py`:

```python
from dataclasses import dataclass

import httpx
import pytest
from pf_fetch import LivePolicyStop, Throttle
from v1_return_types import (
    PATHS,
    conclusion,
    declared,
    describe,
    install_transport_throttle,
    render,
)


class Sample:
    def method(self) -> "dict[str, int]":
        return {}

    @property
    def prop(self) -> "list[str]":
        return []

    def bare(self):
        return None

    def __init__(self, data: "pa.Table") -> None:  # noqa: F821 - a string annotation, as in edgartools
        self.data = data


@dataclass
class Record:
    frame: "pd.DataFrame"  # noqa: F821


def test_declared_reads_annotations_as_written():
    assert declared(Sample, "method") == "dict[str, int]"
    assert declared(Sample, "prop") == "list[str]"
    assert declared(Sample, "bare") == "(none)"
    assert declared(Sample, "data") == "__init__ parameter: pa.Table"
    assert declared(Record, "frame") == "attribute: pd.DataFrame"


def test_describe_flags_foreign_dataframes_in_containers():
    class FakeFrame:
        pass

    FakeFrame.__module__ = "pandas.core.frame"
    assert describe([FakeFrame()])["foreign_dataframe"] is True
    assert describe({"a": 1}) == {
        "observed": "builtins.dict",
        "elements": ["builtins.int"],
        "foreign_dataframe": False,
    }


def test_conclusion_names_every_foreign_path_or_says_vacuous():
    records = [
        {"call": "b", "foreign_dataframe": True},
        {"call": "a", "foreign_dataframe": True},
        {"call": "c", "foreign_dataframe": False},
    ]
    assert conclusion(records) == "R14.5 cast required for: a; b"
    assert (
        conclusion([{"call": "c", "foreign_dataframe": False}])
        == "R14.5 vacuous: no path returns a foreign dataframe."
    )


def test_render_collapses_identical_rows_and_reports_requests():
    record = {
        "fixture_id": "f",
        "family": "a",
        "call": "x()",
        "declared": "int",
        "observed": "builtins.int",
        "elements": [],
        "foreign_dataframe": False,
    }
    text = render([record, dict(record, fixture_id="g")], requests=7)
    assert text.count("`x()`") == 1 and "Live requests made: 7." in text


def test_paths_cover_all_three_families():
    assert {spec.family for spec in PATHS} == {"a", "b", "c"}


def test_transport_throttle_counts_and_caps_requests(monkeypatch):
    monkeypatch.setattr(
        httpx.HTTPTransport, "handle_request", lambda self, request: httpx.Response(200)
    )
    monkeypatch.setattr(
        httpx.AsyncHTTPTransport,
        "handle_async_request",
        httpx.AsyncHTTPTransport.handle_async_request,
    )
    throttle = Throttle(min_interval=0.0, max_requests=2)
    install_transport_throttle(throttle)
    transport = httpx.HTTPTransport()
    request = httpx.Request("GET", "https://www.sec.gov/x")
    transport.handle_request(request)
    transport.handle_request(request)
    assert throttle.count == 2
    with pytest.raises(LivePolicyStop):
        transport.handle_request(request)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_v1_return_types.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'v1_return_types'`.

- [x] **Step 3: Write the script**

The paths in `PATHS` were enumerated from the installed 5.58.0 wheel on 2026-09-22. They
cover:

- `Entity.get_filings` → `EntityFilings`, with `.data` and `.to_pandas()`;
- `Filing.attachments` / `.html()` / `.obj()`;
- `Attachments.exhibits`;
- `Attachment.content` / `.download()` / `.text()` / `.markdown()`;
- `CurrentReport.press_releases` / `.earnings`;
- `PressRelease.html()` / `.text()`;
- `Document.tables`;
- `TableNode.to_dataframe()`;
- `EarningsRelease.tables` / `.to_facts_dataframe()`;
- `FinancialTable.dataframe`.

`expirements/parser-fidelity/v1_return_types.py`:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["edgartools==5.58.0"]
# ///
"""V1: declared and observed return types of edgartools 5.58.0's acquisition paths (live, opt-in).

    uv run --locked --script expirements/parser-fidelity/v1_return_types.py --live

Paths were enumerated from the installed 5.58.0 source (see PATHS). For each fixture
filing in the manifest, every path is called and its declared return annotation (read
with ``annotationlib.Format.STRING``) and observed runtime type are recorded, with
element types for containers and a foreign-dataframe flag (pandas or pyarrow).

Rate limit: edgartools 5.58.0 reads EDGAR_RATE_LIMIT_PER_SEC at import (httpclient.py,
default 9) into a per-process pyrate-limiter bucket, which allows two back-to-back
requests and counts nothing. This script sets it to 2 and also routes every httpx
transport request through the fetcher's throttle (0.5 s spacing, request cap, count).
A fresh EDGAR_LOCAL_DATA_DIR per run keeps edgartools' HTTP cache from hiding requests.
"""

from __future__ import annotations

import argparse
import functools
import inspect
import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import annotationlib
import tomllib
from pf_fetch import (
    DEFAULT_MAX_REQUESTS,
    LiveLock,
    LivePolicyStop,
    Throttle,
    require_identity,
)
from pf_paths import EDGAR_HOME, LIVE_LOCK, MANIFEST, RUNS

FOREIGN_PREFIXES = ("pandas.", "pyarrow.")


@dataclass(frozen=True)
class PathSpec:
    family: str  # a: list filings; b: filing -> attachments -> exhibit; c: tables
    call: str
    owner: str  # dotted path of the class that declares the member
    member: str
    run: Callable[[dict], object]


def qualname(obj: object) -> str:
    kind = type(obj)
    return f"{kind.__module__}.{kind.__qualname__}"


def describe(obj: object) -> dict:
    observed = qualname(obj)
    elements: list[str] = []
    if isinstance(obj, (list, tuple, set, frozenset)):
        elements = sorted({qualname(item) for item in obj})
    elif isinstance(obj, dict):
        elements = sorted({qualname(value) for value in obj.values()})
    foreign = [t for t in [observed, *elements] if t.startswith(FOREIGN_PREFIXES)]
    return {
        "observed": observed,
        "elements": elements,
        "foreign_dataframe": bool(foreign),
    }


def declared(owner: type, member: str) -> str:
    """The return annotation as written in the source, or '(none)'."""
    attribute = inspect.getattr_static(owner, member, None)
    if (
        attribute is None
    ):  # an instance attribute: a class-level annotation, else the __init__ parameter
        for klass in owner.__mro__:
            annotations = annotationlib.get_annotations(
                klass, format=annotationlib.Format.STRING
            )
            if member in annotations:
                return f"attribute: {annotations[member]}"
        parameter = inspect.signature(
            owner.__init__, annotation_format=annotationlib.Format.STRING
        ).parameters.get(member)
        if parameter is None or parameter.annotation is inspect.Parameter.empty:
            return "(none)"
        return f"__init__ parameter: {parameter.annotation}"
    if isinstance(attribute, property):
        function = attribute.fget
    elif isinstance(attribute, functools.cached_property):
        function = attribute.func
    elif isinstance(attribute, (staticmethod, classmethod)):
        function = attribute.__func__
    else:
        function = attribute
    function = inspect.unwrap(function)
    annotation = inspect.signature(
        function, annotation_format=annotationlib.Format.STRING
    ).return_annotation
    return "(none)" if annotation is inspect.Signature.empty else str(annotation)


def _owner(dotted: str) -> type:
    module, _, name = dotted.rpartition(".")
    return getattr(__import__(module, fromlist=[name]), name)


def _filing(ctx: dict) -> object:
    if "filing" not in ctx:
        ctx["filing"] = next(
            iter(
                ctx["company"].get_filings(
                    form="8-K", accession_number=ctx["accession"]
                )
            )
        )
    return ctx["filing"]


def _exhibit(ctx: dict) -> object:
    return next(
        a for a in _filing(ctx).attachments if a.document == ctx["exhibit_filename"]
    )


def _html(ctx: dict) -> str:
    content = _exhibit(ctx).content
    return (
        content.decode("utf-8", errors="replace")
        if isinstance(content, bytes)
        else content
    )


PATHS = [
    PathSpec("a", "Company(cik).get_filings(form='8-K', accession_number=...)", "edgar.entity.core.Entity", "get_filings",
             lambda c: c["company"].get_filings(form="8-K", accession_number=c["accession"])),
    PathSpec("a", "EntityFilings.data", "edgar.entity.filings.EntityFilings", "data",
             lambda c: c["company"].get_filings(form="8-K", accession_number=c["accession"]).data),
    PathSpec("a", "EntityFilings.to_pandas()", "edgar.entity.filings.EntityFilings", "to_pandas",
             lambda c: c["company"].get_filings(form="8-K", accession_number=c["accession"]).to_pandas()),
    PathSpec("a", "iterating EntityFilings", "edgar.entity.filings.EntityFilings", "__iter__", _filing),
    PathSpec("b", "Filing.attachments", "edgar._filings.Filing", "attachments", lambda c: _filing(c).attachments),
    PathSpec("b", "Attachments.exhibits", "edgar.attachments.Attachments", "exhibits", lambda c: _filing(c).attachments.exhibits),
    PathSpec("b", "iterating Attachments", "edgar.attachments.Attachments", "__iter__", _exhibit),
    PathSpec("b", "Attachment.content", "edgar.attachments.Attachment", "content", lambda c: _exhibit(c).content),
    PathSpec("b", "Attachment.download()", "edgar.attachments.Attachment", "download", lambda c: _exhibit(c).download()),
    PathSpec("b", "Attachment.text()", "edgar.attachments.Attachment", "text", lambda c: _exhibit(c).text()),
    PathSpec("b", "Attachment.markdown()", "edgar.attachments.Attachment", "markdown", lambda c: _exhibit(c).markdown()),
    PathSpec("b", "Filing.html()", "edgar._filings.Filing", "html", lambda c: _filing(c).html()),
    PathSpec("b", "Filing.obj()", "edgar._filings.Filing", "obj", lambda c: _filing(c).obj()),
    PathSpec("b", "EightK.press_releases", "edgar.company_reports.current_report.CurrentReport", "press_releases",
             lambda c: _filing(c).obj().press_releases),
    PathSpec("b", "PressRelease.html()", "edgar.company_reports.press_release.PressRelease", "html",
             lambda c: _filing(c).obj().press_releases[0].html()),
    PathSpec("b", "PressRelease.text()", "edgar.company_reports.press_release.PressRelease", "text",
             lambda c: _filing(c).obj().press_releases[0].text()),
    PathSpec("b", "EightK.earnings", "edgar.company_reports.current_report.CurrentReport", "earnings",
             lambda c: _filing(c).obj().earnings),
    PathSpec("c", "parse_html(html).tables", "edgar.documents.document.Document", "tables",
             lambda c: __import__("edgar.documents", fromlist=["parse_html"]).parse_html(_html(c)).tables),
    PathSpec("c", "TableNode.to_dataframe()", "edgar.documents.table_nodes.TableNode", "to_dataframe",
             lambda c: __import__("edgar.documents", fromlist=["parse_html"]).parse_html(_html(c)).tables[0].to_dataframe()),
    PathSpec("c", "EarningsRelease.tables", "edgar.earnings.EarningsRelease", "tables",
             lambda c: _filing(c).obj().earnings.tables),
    PathSpec("c", "FinancialTable.dataframe", "edgar.earnings.FinancialTable", "dataframe",
             lambda c: _filing(c).obj().earnings.tables[0].dataframe),
    PathSpec("c", "EarningsRelease.to_facts_dataframe()", "edgar.earnings.EarningsRelease", "to_facts_dataframe",
             lambda c: _filing(c).obj().earnings.to_facts_dataframe()),
]  # fmt: skip


def install_transport_throttle(throttle: Throttle) -> None:
    """Route every sync and async httpx transport request through the fetcher's throttle."""
    import httpx

    sync_send = httpx.HTTPTransport.handle_request
    async_send = httpx.AsyncHTTPTransport.handle_async_request

    def handle_request(
        self: httpx.HTTPTransport, request: httpx.Request
    ) -> httpx.Response:
        throttle.acquire()
        return sync_send(self, request)

    async def handle_async_request(
        self: httpx.AsyncHTTPTransport, request: httpx.Request
    ) -> httpx.Response:
        throttle.acquire()
        return await async_send(self, request)

    httpx.HTTPTransport.handle_request = handle_request
    httpx.AsyncHTTPTransport.handle_async_request = handle_async_request


def run_paths(fixtures: list[dict]) -> list[dict]:
    import edgar

    records = []
    for fixture in fixtures:
        ctx = {
            "company": edgar.Company(int(fixture["cik"])),
            "accession": fixture["accession"],
            "exhibit_filename": fixture["exhibit_filename"],
        }
        for spec in PATHS:
            record = {
                "fixture_id": fixture["fixture_id"],
                "family": spec.family,
                "call": spec.call,
            }
            record["declared"] = declared(_owner(spec.owner), spec.member)
            try:
                value = spec.run(ctx)
                record.update(
                    describe(value)
                    if value is not None
                    else {
                        "observed": "NoneType",
                        "elements": [],
                        "foreign_dataframe": False,
                    }
                )
            except LivePolicyStop:
                raise
            except Exception as exc:  # noqa: BLE001 - a failing path is a V1 finding
                record.update(
                    observed=f"raised {type(exc).__name__}: {exc}",
                    elements=[],
                    foreign_dataframe=False,
                )
            records.append(record)
    return records


def conclusion(records: list[dict]) -> str:
    foreign = sorted({r["call"] for r in records if r["foreign_dataframe"]})
    if foreign:
        return "R14.5 cast required for: " + "; ".join(foreign)
    return "R14.5 vacuous: no path returns a foreign dataframe."


def render(records: list[dict], requests: int) -> str:
    lines = [
        "| family | call | declared | observed | elements | foreign |",
        "|---|---|---|---|---|---|",
    ]
    seen = set()
    for r in records:
        key = (r["call"], r["observed"], tuple(r["elements"]))
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"| {r['family']} | `{r['call']}` | `{r['declared']}` | `{r['observed']}` "
            f"| {', '.join(f'`{e}`' for e in r['elements']) or '-'} | {'yes' if r['foreign_dataframe'] else 'no'} |"
        )
    return "\n".join(
        lines + ["", conclusion(records), "", f"Live requests made: {requests}."]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="required: confirms a live, rate-limited run",
    )
    parser.add_argument("--max-requests", type=int, default=DEFAULT_MAX_REQUESTS)
    parser.add_argument(
        "--list-paths",
        action="store_true",
        help="offline: print the edgartools source directory and each path's declared annotation",
    )
    args = parser.parse_args(argv)
    if args.list_paths:
        os.environ.setdefault("EDGAR_LOCAL_DATA_DIR", str(EDGAR_HOME))
        import edgar

        print(f"edgartools source: {os.path.dirname(edgar.__file__)}")
        for spec in PATHS:
            print(
                f"{spec.family} {spec.call}: {declared(_owner(spec.owner), spec.member)}"
            )
        return 0
    if not args.live:
        parser.error("V1 makes live requests; pass --live to confirm")
    require_identity()  # edgartools reads the same EDGAR_IDENTITY variable
    fixtures = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))["fixtures"]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = "2"
    os.environ["EDGAR_LOCAL_DATA_DIR"] = str(RUNS / f"edgar-home-v1-{stamp}")
    throttle = Throttle(max_requests=args.max_requests)
    out = RUNS / "v1"
    try:
        with LiveLock(LIVE_LOCK):
            install_transport_throttle(throttle)
            records = run_paths(fixtures)
    except LivePolicyStop as exc:
        print(f"STOPPED: {exc}; requests made: {throttle.count}", file=sys.stderr)
        return 1
    if throttle.count == 0:
        print(
            "no request passed through the transport throttle; the wrapper missed edgartools' client",
            file=sys.stderr,
        )
        return 1
    out.mkdir(parents=True, exist_ok=True)
    (out / "v1-results.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8"
    )
    (out / "v1-results.md").write_text(
        render(records, throttle.count) + "\n", encoding="utf-8"
    )
    print(render(records, throttle.count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_v1_return_types.py --import-mode=prepend -q`
Expected: `6 passed`.

- [x] **Step 5: Lock the script and confirm the paths against the installed source**

```bash
uv lock --script expirements/parser-fidelity/v1_return_types.py
uv run --locked --script expirements/parser-fidelity/v1_return_types.py --list-paths
```

Expected: the lock resolves, then offline output with no network:

- an `edgartools source: <dir>` line;
- 22 lines of `<family> <call>: <declared>`;
- no traceback.

A traceback means a `PathSpec` names an owner or member that 5.58.0 lacks; fix it.

Then read these files under the printed directory for public paths in families
(a)–(c) that `PATHS` misses:

- `entity/core.py`, `entity/filings.py`, `_filings.py`, `attachments.py`;
- `company_reports/current_report.py`, `company_reports/press_release.py`;
- `earnings.py`, `documents/document.py`, `documents/table_nodes.py`.

Add a `PathSpec` for each missing path and rerun Step 4. Missing paths are ones that
list an issuer's filings, return attachments or exhibit content, or extract tables.

- [x] **Step 6: Run V1 live**

Run: `uv run --locked --script expirements/parser-fidelity/v1_return_types.py --live`

Expected: the results table, a conclusion line, and `Live requests made: N` with N at
most 500. Record N. If the script prints `no request passed through the transport
throttle`, the wrapper missed edgartools' HTTP client, and the run does not count.
Inspect how `edgar.httpclient` builds its transport, route it through the throttle,
add a test, and rerun.

- [x] **Step 7: Write the V1 record**

Create `docs/verification/V1-edgartools-return-types.md` from this template. Replace
every `_(replace with …)_` instruction with the named content:

```markdown
# V1: edgartools 5.58.0 return types

This record discharges V1, the open marker in R14.5 of
`specs/evidence-linked-theme-extraction.md`, for Stage 1 of
`specs/evidence-linked-theme-extraction-roadmap.md`.

**Conclusion:** _(replace with the conclusion line printed at the end of `data/runs/parser-fidelity/v1/v1-results.md`)_

## Run

- Command: `uv run --locked --script expirements/parser-fidelity/v1_return_types.py --live`
- Date (UTC): _(replace with the date of the run)_
- Library: edgartools 5.58.0, pinned in `expirements/parser-fidelity/v1_return_types.py.lock`;
  Python _(replace with the interpreter version uv used)_
- Filings: the eight fixture filings listed in `tests/fixtures/releases/manifest.toml`
- Live requests: _(replace with the count printed by the script)_

## Rate-limit mechanism

edgartools 5.58.0 reads `EDGAR_RATE_LIMIT_PER_SEC` once, at import (`edgar/httpclient.py`,
default 9), and builds a per-process pyrate-limiter bucket from it. That bucket averages
the configured rate, but it allows two back-to-back requests and counts nothing. The V1
script therefore sets `EDGAR_RATE_LIMIT_PER_SEC=2`, and it also sends every request
through the Stage 1 fetcher's throttle. The throttle wraps `httpx.HTTPTransport` and
`httpx.AsyncHTTPTransport`, spaces request starts at least 0.5 s apart, caps the run at
500 requests, and counts every request.

Each run uses a fresh `EDGAR_LOCAL_DATA_DIR`, so edgartools' HTTP cache cannot hide
requests. The script refuses to report a run in which the throttle saw no request.

## Paths

The paths were enumerated from the installed 5.58.0 source, not recalled from memory.
There are three families:

- (a) listing an issuer's filings;
- (b) going from a filing to its attachments and to exhibit bytes, HTML, or text,
  including the 8-K and press-release convenience objects;
- (c) extracting tables.

"Declared" is the annotation as written in the source, read with
`annotationlib.Format.STRING`. "Observed" is the module-qualified runtime type.

_(replace with the table from `data/runs/parser-fidelity/v1/v1-results.md`)_

## Declared versus observed

_(replace with one bullet per path whose observed type differs from its declaration or
that has no declaration, naming both types)_

## For Stage 4

_(replace with the paths that return a foreign dataframe and the cast R14.5 requires at
the ingestion boundary, or with "None: R14.5 is vacuous")_
```

Check that no instruction remains:

```bash
grep -n "_(" docs/verification/V1-edgartools-return-types.md
```

Expected: no output.

- [x] **Step 8: Lint and commit**

Before committing anything public, check that the identity leaked nowhere. This lists
file names only, never the value:

```bash
grep -rlF -- "$EDGAR_IDENTITY" docs tests expirements
```

Expected: no output.

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/v1_return_types.py expirements/parser-fidelity/v1_return_types.py.lock expirements/parser-fidelity/test_v1_return_types.py docs/verification/V1-edgartools-return-types.md
git commit -m "docs(verification): record V1, edgartools 5.58.0 return types"
```

---

### Task 17: The scorer

**Files:**
- Create: `expirements/parser-fidelity/score.py`
- Test: `expirements/parser-fidelity/test_score.py`

**Interfaces:**
- Consumes:
  - `pf_dump.Element`, `Row`, and `read_dump` (Task 11);
  - `pf_space` and `pf_text.build_space_text` (Task 1);
  - `validate_gold.SourceText`, `TEXT_TYPES`, and `load_gold` (Task 8);
  - `run_candidates.CANDIDATES` (Task 15).
- Produces:
  - **Constants.** `RANKED = ("coverage", "footnote_merging", "reading_order",
    "header_loss")` and `COUNTED`.
  - **Matching.** `Match` and `match_anchor(...)`.
  - **Scoring.** `score_fixture(gold, source, elements | None) -> FixtureScore`, where
    `FixtureScore` has `.counts[metric] = [numerator, denominator]`, `.altered`,
    `.residual`, `.unanchorable`, and `.exposes_cells`.
  - **Pooling.** `pool(scores) -> dict`, with `counts`, `rates`, `altered`,
    `unanchorable`, and `exposes_cells`. `rates(counts)` adds `header_loss` and
    `header_loss_n`.
  - **Headers and gold.** `cell_headers(rows, cell_text) -> (row header, column path) | None`
    and `gold_structure(gold) -> dict`.
  - **Outputs.** `data/runs/parser-fidelity/scores/scores.json` (keys `fixtures`,
    `classes`, and `gold`) and `metrics.md`.

The rule is fixed before scoring (F6), so this task and Task 18 are committed before
Task 19 runs anything on a fixture. If Task 19 exposes a scorer bug, fix it with a
failing test first, and list the fix in V2.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_score.py`:

```python
"""Scorer behaviour on hand-built gold and dumps, with hand-computed expectations."""

from pf_dump import Cell, Element, Row, grid_text
from score import cell_headers, gold_structure, pool, score_fixture
from validate_gold import SourceText

SOURCE = SourceText(
    b"<html><body>"
    b"<p><b>Acme Reports Record Third Quarter</b></p>"
    b"<p>Acme Corp. today reported net sales of $4.3 billion, up 5 percent.</p>"
    b"<p>Outlook</p><p>The company expects growth to continue next year.</p>"
    b"<table><tr><td></td><td>2025</td><td>2024</td></tr>"
    b"<tr><td>Net sales</td><td>4,321</td><td>3,210</td></tr>"
    b"<tr><td>Cost of sales</td><td>2,109</td><td>1,987</td></tr></table>"
    b"<p>(1) Excludes the impact of the divestiture completed in May.</p>"
    b"<p>Outlook</p>"
    b"</body></html>"
)

GOLD = {
    "blocks": [
        {"id": "h1", "type": "heading", "start": "Acme Reports Record Third Quarter"},
        {
            "id": "p1",
            "type": "paragraph",
            "start": "Acme Corp. today reported",
            "end": "billion, up 5 percent.",
        },
        {
            "id": "h2",
            "type": "heading",
            "start": "Outlook",
            "after": "The company expects",
        },
        {
            "id": "p2",
            "type": "paragraph",
            "start": "The company expects growth",
            "end": "to continue next year.",
        },
        {
            "id": "t1",
            "type": "table",
            "headers": ["2025", "2024"],
            "cells": [
                {
                    "role": "corner",
                    "text": "4,321",
                    "row_header": "Net sales",
                    "col_header": "2025",
                },
                {
                    "role": "right",
                    "text": "3,210",
                    "row_header": "Net sales",
                    "col_header": "2024",
                },
                {
                    "role": "below",
                    "text": "2,109",
                    "row_header": "Cost of sales",
                    "col_header": "2025",
                },
            ],
        },
        {
            "id": "f1",
            "type": "footnote",
            "start": "Excludes the impact of the",
            "end": "divestiture completed in May.",
        },
        {"id": "x1", "type": "page_artifact", "start": "- 2 -"},
        {"id": "u1", "type": "heading", "start": "Outlook", "unanchorable": True},
    ]
}

ROWS = (
    Row(True, (Cell(""), Cell("2025"), Cell("2024"))),
    Row(False, (Cell("Net sales"), Cell("4,321"), Cell("3,210"))),
    Row(False, (Cell("Cost of sales"), Cell("2,109"), Cell("1,987"))),
)
PERFECT = [
    Element("heading", "Acme Reports Record Third Quarter"),
    Element(
        "paragraph",
        "Acme Corp. today reported net sales of $4.3 billion, up 5 percent.",
    ),
    Element("heading", "Outlook"),
    Element("paragraph", "The company expects growth to continue next year."),
    Element("table", grid_text(ROWS), rows=ROWS),
    Element("footnote", "(1) Excludes the impact of the divestiture completed in May."),
]


def counts(elements):
    return score_fixture(GOLD, SOURCE, elements).counts


def test_a_perfect_dump_scores_perfectly():
    score = score_fixture(GOLD, SOURCE, PERFECT)
    assert score.counts["coverage"] == [6, 6]
    assert score.counts["footnote_merging"] == [0, 1]
    assert score.counts["reading_order"] == [
        0,
        7,
    ]  # h1 p1 h2 p2 corner right below f1 -> 8 items
    assert score.counts["header_section"] == [0, 2]
    assert score.counts["header_table"] == [0, 2]
    assert score.counts["cell_association"] == [3, 3]
    assert score.unanchorable == 1
    assert score.residual["missed"] == []


def test_missing_output_scores_zero_coverage():
    score = score_fixture(GOLD, SOURCE, None)
    assert score.counts["coverage"] == [0, 6]
    assert score.residual["missed"] == ["h1", "p1", "h2", "p2", "t1", "f1"]


def test_footnote_merged_into_a_paragraph():
    merged = PERFECT[:3] + [
        Element("paragraph", PERFECT[3].text + " " + PERFECT[5].text),
        PERFECT[4],
    ]
    result = counts(merged)
    assert result["footnote_merging"] == [1, 1]
    assert result["coverage"] == [6, 6]


def test_tables_appended_at_the_end_corrupt_reading_order():
    moved = PERFECT[:4] + [PERFECT[5], PERFECT[4]]
    score = score_fixture(GOLD, SOURCE, moved)
    assert score.counts["reading_order"] == [1, 7]
    assert score.residual["misordered"] == ["t1:below>f1"]


def test_heading_typed_as_paragraph_or_merged_is_header_loss():
    untyped = [Element("paragraph", PERFECT[0].text)] + PERFECT[1:]
    assert counts(untyped)["header_section"] == [1, 2]
    merged = [Element("paragraph", PERFECT[0].text + " " + PERFECT[1].text)] + PERFECT[
        2:
    ]
    assert counts(merged)["header_section"] == [1, 2]


def test_table_headers_outside_table_elements_are_lost():
    flat = PERFECT[:4] + [
        Element("paragraph", "2025 2024"),
        Element("paragraph", "Net sales 4,321 3,210 Cost of sales 2,109 1,987"),
        PERFECT[5],
    ]
    result = counts(flat)
    assert result["header_table"] == [2, 2]
    assert result["cell_association"] == [0, 0]


def test_folded_typography_is_found_and_marked_altered():
    folded = [
        Element("heading", "Acme Reports Record Third Quarter"),
        Element(
            "paragraph",
            "Acme Corp. today reported net sales of $4.3 billion, up 5 percent",
        ),
    ] + PERFECT[2:]
    score = score_fixture(GOLD, SOURCE, folded)
    assert score.counts["coverage"] == [6, 6]
    assert score.altered == ["p1:end"]


def test_split_blocks_and_duplicates_are_diagnosed():
    split = (
        [
            PERFECT[0],
            Element("paragraph", "Acme Corp. today reported net sales"),
            Element("paragraph", "of $4.3 billion, up 5 percent."),
        ]
        + PERFECT[2:]
        + [PERFECT[0]]
    )
    score = score_fixture(GOLD, SOURCE, split)
    assert score.counts["split"][0] == 1
    assert score.residual["split"] == ["p1"]
    assert score.counts["duplication"][0] == 1


def test_cell_headers_follow_grid_geometry_with_spans():
    rows = (
        Row(True, (Cell(""), Cell("Three Months Ended", 2))),
        Row(True, (Cell(""), Cell("2025"), Cell("2024"))),
        Row(False, (Cell("Net sales"), Cell("4,321"), Cell("3,210"))),
    )
    assert cell_headers(rows, "3,210") == ("Net sales", "Three Months Ended 2024")
    assert cell_headers(rows, "9,999") is None


def test_pool_sums_numerators_and_denominators_and_means_header_subrates():
    first = score_fixture(GOLD, SOURCE, PERFECT)
    second = score_fixture(
        GOLD, SOURCE, [Element("paragraph", PERFECT[0].text)] + PERFECT[1:]
    )
    pooled = pool([first, second])
    assert pooled["counts"]["coverage"] == [12, 12]
    assert pooled["counts"]["header_section"] == [1, 4]
    assert pooled["rates"]["header_loss"] == (0.25 + 0.0) / 2
    assert pooled["rates"]["header_loss_n"] == 8


def test_gold_structure_reports_levels_and_footnote_placement():
    structure = gold_structure(GOLD)
    assert structure["types"]["heading"] == 3
    assert structure["footnote_placement"] == {"after table": 1}
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_score.py --import-mode=prepend -q`
Expected: collection error `ModuleNotFoundError: No module named 'score'`.

- [x] **Step 3: Write the scorer**

`expirements/parser-fidelity/score.py`:

```python
"""Score candidate dumps against the gold (spec: Metrics). Standard library only.

    uv run --locked --all-packages python expirements/parser-fidelity/score.py

Reads each candidate's first fixture dump (data/runs/parser-fidelity/fixtures/), the gold,
and the manifest; writes data/runs/parser-fidelity/scores/scores.json and metrics.md.
All matching is exact substring search in the primary space, or, for text-block anchors
only, the fallback space when the anchor's fallback form occurs exactly once in the
document and exactly once in the candidate's text.
"""

from __future__ import annotations

import itertools
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import tomllib
from pf_dump import Element, Row, read_dump
from pf_paths import FIXTURES, RUNS
from pf_space import fallback_space, find_all, primary_space
from pf_text import SpaceText, build_space_text
from run_candidates import CANDIDATES
from validate_gold import TEXT_TYPES, SourceText, load_gold

RANKED = ("coverage", "footnote_merging", "reading_order", "header_loss")
COUNTED = ("coverage", "footnote_merging", "reading_order", "header_section", "header_table", "split", "other_merges",
           "duplication", "footnotes_in_tables", "cell_association")  # fmt: skip
BODY_TYPES = frozenset({"heading", "paragraph", "list_item"})
ROLES = ("corner", "right", "below")


@dataclass(frozen=True)
class Match:
    found: bool
    altered: bool = False
    duplicated: bool = False
    position: tuple[int, int] | None = (
        None  # (element index, offset in element) of the first character
    )
    elements: frozenset[int] = (
        frozenset()
    )  # elements the block's own portion of the match overlaps


NOT_FOUND = Match(False)


class CandidateText:
    def __init__(self, elements: list[Element]) -> None:
        pieces = [element.text for element in elements]
        self.elements = elements
        self.primary: SpaceText = build_space_text(pieces, "primary")
        self.fallback: SpaceText = build_space_text(pieces, "fallback")


def _located(
    space: SpaceText, start: int, length: int, own: int, **flags: bool
) -> Match:
    covered = space.origins[start : start + (own or length)]
    return Match(
        True,
        position=space.origins[start],
        elements=frozenset(o[0] for o in covered),
        **flags,
    )


def match_anchor(
    text: CandidateText,
    source: SourceText,
    anchor: str,
    own: str | None = None,
    fallback: bool = True,
) -> Match:
    """Find ``anchor``; ``own`` is the leading part that belongs to the block (for ``after`` blocks)."""
    form = primary_space(anchor)
    if not form:
        return NOT_FOUND
    hits = find_all(text.primary.text, form)
    if hits:
        own_length = len(primary_space(own)) if own is not None else len(form)
        return _located(
            text.primary, hits[0], len(form), own_length, duplicated=len(hits) > 1
        )
    if not fallback:
        return NOT_FOUND
    form2 = fallback_space(anchor)
    if not form2 or source.count_fallback(form2) != 1:
        return NOT_FOUND
    hits2 = find_all(text.fallback.text, form2)
    if len(hits2) != 1:
        return NOT_FOUND
    own_length = len(fallback_space(own)) if own is not None else len(form2)
    return _located(text.fallback, hits2[0], len(form2), own_length, altered=True)


@dataclass
class BlockResult:
    block: dict
    anchors: dict[
        str, Match
    ]  # the block's own anchors: start[, end] or start+after; roles for tables

    @property
    def id(self) -> str:
        return self.block["id"]

    @property
    def start(self) -> Match:
        return (
            self.anchors["start"]
            if "start" in self.anchors
            else self.anchors["start+after"]
        )

    @property
    def kind(self) -> str:
        return self.block["type"]

    @property
    def found(self) -> bool:
        return all(match.found for match in self.anchors.values())

    @property
    def elements(self) -> frozenset[int]:
        return frozenset().union(
            *(m.elements for m in self.anchors.values() if m.found)
        )


def match_block(block: dict, text: CandidateText, source: SourceText) -> BlockResult:
    if block["type"] == "table":
        cells = {cell["role"]: cell["text"] for cell in block["cells"]}
        return BlockResult(
            block,
            {
                role: match_anchor(text, source, cells[role], fallback=False)
                for role in ROLES
            },
        )
    if "after" in block:
        combined = match_anchor(
            text, source, block["start"] + block["after"], own=block["start"]
        )
        return BlockResult(block, {"start+after": combined})  # its end is its start
    anchors = {"start": match_anchor(text, source, block["start"])}
    if "end" in block:
        anchors["end"] = match_anchor(text, source, block["end"])
    return BlockResult(block, anchors)


def scored_blocks(gold: dict) -> list[dict]:
    return [
        b
        for b in gold["blocks"]
        if b["type"] != "page_artifact" and not b.get("unanchorable")
    ]


@dataclass
class FixtureScore:
    counts: dict[str, list[int]] = field(
        default_factory=dict
    )  # metric -> [numerator, denominator]
    altered: list[str] = field(default_factory=list)
    residual: dict[str, list[str]] = field(default_factory=dict)
    unanchorable: int = 0
    exposes_cells: bool = False


def _grid_positions(rows: tuple[Row, ...]) -> list[list[tuple[int, int]]]:
    """Column span [start, end) of every cell, with colspan and rowspan expanded."""
    occupied: set[tuple[int, int]] = set()
    positions = []
    for r, row in enumerate(rows):
        column, spans = 0, []
        for cell in row.cells:
            while (r, column) in occupied:
                column += 1
            spans.append((column, column + cell.colspan))
            occupied.update(
                (r + dr, column + dc)
                for dr in range(cell.rowspan)
                for dc in range(cell.colspan)
            )
            column += cell.colspan
        positions.append(spans)
    return positions


def cell_headers(rows: tuple[Row, ...], cell_text: str) -> tuple[str, str] | None:
    """(row header, column header path) of the grid cell holding ``cell_text``, by grid geometry.

    The row header is the first non-empty cell to its left in its row; the column header path
    joins, top to bottom, the non-empty header-row cells whose columns overlap the cell's.
    """
    target = primary_space(cell_text)
    positions = _grid_positions(rows)
    located = [
        (r, k)
        for r, row in enumerate(rows)
        for k, cell in enumerate(row.cells)
        if primary_space(cell.text) == target
    ]
    located = located or [
        (r, k)
        for r, row in enumerate(rows)
        for k, cell in enumerate(row.cells)
        if target in primary_space(cell.text)
    ]
    if not located:
        return None
    r, k = located[0]
    start, end = positions[r][k]
    row_header = next(
        (
            c.text
            for c, (s, _) in zip(rows[r].cells, positions[r], strict=True)
            if s < start and c.text.strip()
        ),
        "",
    )
    path = [
        cell.text
        for rr, row in enumerate(rows)
        if row.header and rr != r
        for cell, (s, e) in zip(row.cells, positions[rr], strict=True)
        if s < end and e > start and cell.text.strip()
    ]
    return row_header, " ".join(path)


def _count(score: FixtureScore, metric: str, numerator: int, denominator: int) -> None:
    score.counts[metric] = [numerator, denominator]


def score_fixture(
    gold: dict, source: SourceText, elements: list[Element] | None
) -> FixtureScore:
    elements = elements or []
    text = CandidateText(elements)
    results = [match_block(block, text, source) for block in scored_blocks(gold)]
    score = FixtureScore(
        unanchorable=sum(1 for b in gold["blocks"] if b.get("unanchorable"))
    )
    score.exposes_cells = any(e.rows is not None for e in elements)
    text_results = [r for r in results if r.kind in TEXT_TYPES]
    found = [r for r in results if r.found]

    _count(score, "coverage", len(found), len(results))
    score.residual["missed"] = [r.id for r in results if not r.found]

    body_elements = frozenset().union(
        *(r.elements for r in results if r.kind in BODY_TYPES)
    )
    footnotes = [r for r in found if r.kind == "footnote"]
    merged_notes = [r for r in footnotes if r.elements & body_elements]
    _count(score, "footnote_merging", len(merged_notes), len(footnotes))
    in_tables = [
        r for r in footnotes if any(elements[i].type == "table" for i in r.elements)
    ]
    _count(score, "footnotes_in_tables", len(in_tables), len(footnotes))

    sequence: list[tuple[str, tuple[int, int]]] = []
    for r in results:
        if r.kind == "table":
            sequence += [
                (f"{r.id}:{role}", r.anchors[role].position)
                for role in ROLES
                if r.anchors[role].found
            ]
        elif r.start.found:
            sequence.append((r.id, r.start.position))
    reversed_pairs = [
        f"{a}>{b}" for (a, pa), (b, pb) in itertools.pairwise(sequence) if pa > pb
    ]
    _count(score, "reading_order", len(reversed_pairs), max(len(sequence) - 1, 0))
    score.residual["misordered"] = reversed_pairs

    headings = [r for r in found if r.kind == "heading"]
    lost_headings = []
    for r in headings:
        home = r.start.position[0]
        shared = any(home in other.elements for other in results if other is not r)
        if elements[home].type != "heading" or shared:
            lost_headings.append(r.id)
    _count(score, "header_section", len(lost_headings), len(headings))
    lost_headers, header_total = [], 0
    for r in (r for r in found if r.kind == "table"):
        table_elements = sorted(i for i in r.elements if elements[i].type == "table")
        table_text = primary_space("".join(elements[i].text for i in table_elements))
        for header in r.block["headers"]:
            header_total += 1
            if not table_elements or primary_space(header) not in table_text:
                lost_headers.append(f"{r.id}:{header}")
    _count(score, "header_table", len(lost_headers), header_total)
    score.residual["header_lost"] = lost_headings + lost_headers

    found_text = [r for r in text_results if r.found]
    split = [r.id for r in found_text if len(r.elements) > 1]
    _count(score, "split", len(split), len(found_text))
    score.residual["split"] = split

    holders: dict[int, set[str]] = {}
    for r in results:
        if r.kind != "footnote":
            for index in r.elements:
                holders.setdefault(index, set()).add(r.id)
    merged_blocks = sorted(
        {block for ids in holders.values() if len(ids) > 1 for block in ids}
    )
    non_footnote_found = [r for r in found if r.kind != "footnote"]
    _count(score, "other_merges", len(merged_blocks), len(non_footnote_found))
    score.residual["merged"] = sorted({r.id for r in merged_notes} | set(merged_blocks))

    anchors = [m for r in results for m in r.anchors.values() if m.found]
    _count(score, "duplication", sum(m.duplicated for m in anchors), len(anchors))
    score.altered = sorted(
        f"{r.id}:{label}"
        for r in text_results
        for label, m in r.anchors.items()
        if m.found and m.altered
    )

    matched, cells_seen = 0, 0
    for r in (r for r in found if r.kind == "table"):
        for cell in r.block["cells"]:
            grids = [
                elements[i]
                for i in sorted(r.anchors[cell["role"]].elements)
                if elements[i].rows is not None
            ]
            if not grids:
                continue
            cells_seen += 1
            headers = cell_headers(grids[0].rows, cell["text"])
            if (
                headers
                and primary_space(cell["row_header"]) in primary_space(headers[0])
                and primary_space(cell["col_header"]) in primary_space(headers[1])
            ):
                matched += 1
    _count(score, "cell_association", matched, cells_seen)
    return score


def pool(scores: Iterable[FixtureScore]) -> dict:
    scores = list(scores)
    counts = {
        metric: [sum(s.counts[metric][i] for s in scores) for i in (0, 1)]
        for metric in COUNTED
    }
    pooled: dict = {"counts": counts, "altered": sum(len(s.altered) for s in scores)}
    pooled["unanchorable"] = sum(s.unanchorable for s in scores)
    pooled["exposes_cells"] = any(s.exposes_cells for s in scores)
    pooled["rates"] = rates(counts)
    return pooled


def _rate(pair: list[int]) -> float | None:
    return pair[0] / pair[1] if pair[1] else None


def rates(counts: dict[str, list[int]]) -> dict:
    out = {metric: _rate(counts[metric]) for metric in COUNTED}
    subrates = [
        out[m] for m in ("header_section", "header_table") if out[m] is not None
    ]
    out["header_loss"] = sum(subrates) / len(subrates) if subrates else None
    out["header_loss_n"] = counts["header_section"][1] + counts["header_table"][1]
    return out


def gold_structure(gold: dict) -> dict:
    """Element types and nesting observed in the gold (for Stage 2)."""
    blocks = gold["blocks"]
    placement = Counter()
    for index, block in enumerate(blocks):
        if block["type"] == "footnote":
            previous = next(
                (
                    b["type"]
                    for b in reversed(blocks[:index])
                    if b["type"] not in ("footnote", "page_artifact")
                ),
                "start",
            )
            placement[f"after {previous}"] += 1
    return {
        "types": dict(Counter(b["type"] for b in blocks)),
        "heading_levels": dict(
            Counter(
                str(b.get("level", "none")) for b in blocks if b["type"] == "heading"
            )
        ),
        "list_levels": dict(
            Counter(
                str(b.get("level", "none")) for b in blocks if b["type"] == "list_item"
            )
        ),
        "footnote_placement": dict(placement),
    }


def score_all(fixtures: Path = FIXTURES, runs: Path = RUNS) -> dict:
    manifest = tomllib.loads((fixtures / "manifest.toml").read_text(encoding="utf-8"))
    classes = {
        entry["fixture_id"]: entry["primary_class"] for entry in manifest["fixtures"]
    }
    report: dict = {"fixtures": {}, "classes": {}, "gold": {}}
    per_class: dict[str, dict[str, list[FixtureScore]]] = {}
    for fid, cls in sorted(classes.items()):
        gold = load_gold(fixtures / fid)
        source = SourceText((fixtures / fid / "source.html").read_bytes())
        report["gold"][fid] = gold_structure(gold)
        for name in CANDIDATES:
            dump = runs / "fixtures" / name / fid / "run1.json"
            score = score_fixture(
                gold, source, read_dump(dump) if dump.exists() else None
            )
            sidecar = dump.with_name("run1.sidecar.json")
            runtime = (
                json.loads(sidecar.read_text())["parse_seconds"]
                if sidecar.exists()
                else None
            )
            report["fixtures"].setdefault(fid, {})[name] = {
                "class": cls,
                "dump_present": dump.exists(),
                "counts": score.counts,
                "rates": rates(score.counts),
                "altered": score.altered,
                "residual": score.residual,
                "unanchorable": score.unanchorable,
                "exposes_cells": score.exposes_cells,
                "parse_seconds": runtime,
            }
            per_class.setdefault(cls, {}).setdefault(name, []).append(score)
    for cls, by_candidate in per_class.items():
        report["classes"][cls] = {
            name: pool(scores) for name, scores in by_candidate.items()
        }
    return report


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def render_markdown(report: dict) -> str:
    lines = ["# V2 metric tables (generated by score.py)", ""]
    for title, metric in (
        ("Block coverage (higher is better)", "coverage"),
        ("Footnote merging (lower is better)", "footnote_merging"),
        ("Reading-order corruption (lower is better)", "reading_order"),
        ("Header loss (lower is better)", "header_loss"),
    ):
        names = list(CANDIDATES)
        lines += [
            f"## {title}",
            "",
            "| class | " + " | ".join(names) + " |",
            "|---" * (len(names) + 1) + "|",
        ]
        for cls, by_candidate in sorted(report["classes"].items()):
            cells = []
            for name in names:
                pooled = by_candidate[name]
                if metric == "header_loss":
                    cells.append(
                        f"{_pct(pooled['rates']['header_loss'])} (n={pooled['rates']['header_loss_n']})"
                    )
                else:
                    num, den = pooled["counts"][metric]
                    cells.append(f"{_pct(pooled['rates'][metric])} ({num}/{den})")
            lines.append(f"| {cls} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## Diagnostics by class", ""]
    for cls, by_candidate in sorted(report["classes"].items()):
        lines += [
            f"### {cls}",
            "",
            "| candidate | altered | split | other merges | duplication | footnotes in tables | cell association | unanchorable |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for name, pooled in by_candidate.items():
            c = pooled["counts"]
            association = (
                f"{c['cell_association'][0]}/{c['cell_association'][1]}"
                if pooled["exposes_cells"]
                else "no cells exposed"
            )
            lines.append(
                f"| {name} | {pooled['altered']} | {c['split'][0]}/{c['split'][1]} | {c['other_merges'][0]}/{c['other_merges'][1]} "
                f"| {c['duplication'][0]}/{c['duplication'][1]} | {c['footnotes_in_tables'][0]}/{c['footnotes_in_tables'][1]} "
                f"| {association} | {pooled['unanchorable']} |"
            )
        lines.append("")
    lines += ["## Per-fixture detail", ""]
    for fid, by_candidate in sorted(report["fixtures"].items()):
        lines += [f"### `{fid}` ({next(iter(by_candidate.values()))['class']})", ""]
        lines += [
            "| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for name, result in by_candidate.items():
            c = result["counts"]
            cells = [
                f"{c[m][0]}/{c[m][1]}"
                for m in (
                    "coverage",
                    "footnote_merging",
                    "reading_order",
                    "header_section",
                    "header_table",
                )
            ]
            lines.append(
                f"| {name} | "
                + " | ".join(cells)
                + f" | {result['parse_seconds']} | {', '.join(result['altered']) or '-'} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = score_all()
    out = RUNS / "scores"
    out.mkdir(parents=True, exist_ok=True)
    (out / "scores.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "metrics.md").write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"wrote {out / 'scores.json'} and {out / 'metrics.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_score.py --import-mode=prepend -q`
Expected: `11 passed`.

- [x] **Step 5: Lint and commit**

```bash
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/score.py expirements/parser-fidelity/test_score.py
git commit -m "feat(parser-fidelity): add the V2 scorer"
```

---

### Task 18: The lock gate and the selection rule

**Files:**
- Create: `expirements/parser-fidelity/lock_gate.py`, `lock_gate.py.lock`
- Create: `expirements/parser-fidelity/select_parser.py`
- Test: `expirements/parser-fidelity/test_lock_gate.py`, `expirements/parser-fidelity/test_select_parser.py`

**Interfaces:**
- Consumes: `score.RANKED` and `score.rates` (Task 17), `run_candidates.CANDIDATES`
  (Task 15), and the script locks of the adapters (Task 12).
- Produces:
  - `lock_gate`:
    - `add_dependency`, `locked_versions`, `lowered_versions`, `runtime_closure`,
      `library_gate(name)`, and `walker_gate()`;
    - `data/runs/parser-fidelity/gates/lock-<name>.json`, with `resolved`,
      `lowered`, `added_runtime`, `pandas_added`, `parse_ok`, `parse_problems`,
      and `passed`.
  - `select_parser`:
    - `select(scores, run_gates, lock_gates) -> dict`, with `gates`, `eligible`,
      `selected`, `status`, `trace`, `ineligible_would_have_won`, and
      `control_check`;
    - `worst_class`, `tie`, `priority_comparison`, `tie_breaks`, and
      `control_check`;
    - `data/runs/parser-fidelity/selection.json` and `selection.md`.

- [x] **Step 1: Write the failing tests**

`expirements/parser-fidelity/test_lock_gate.py`:

```python
from lock_gate import add_dependency, locked_versions, lowered_versions, runtime_closure

PYPROJECT = '[project]\nname = "earnings-ingestion"\ndependencies = [\n    "earnings-core",\n    "lxml",\n]\n'

LOCK = {
    "package": [
        {
            "name": "earnings-ingestion",
            "version": "0.1.0",
            "dependencies": [{"name": "lxml"}, {"name": "edgartools"}],
        },
        {"name": "lxml", "version": "6.1.3"},
        {
            "name": "edgartools",
            "version": "5.58.0",
            "dependencies": [
                {"name": "pandas"},
                {"name": "httpxthrottlecache", "extra": ["httpx"]},
            ],
        },
        {"name": "pandas", "version": "3.0.6", "dependencies": [{"name": "numpy"}]},
        {"name": "numpy", "version": "2.3.0"},
        {
            "name": "httpxthrottlecache",
            "version": "0.6.1",
            "dependencies": [{"name": "filelock"}],
            "optional-dependencies": {"httpx": [{"name": "httpx"}]},
        },
        {"name": "filelock", "version": "3.0"},
        {"name": "httpx", "version": "0.28.1"},
        {"name": "rapidfuzz", "version": "3.0"},
    ]
}


def test_add_dependency_inserts_into_runtime_dependencies():
    text = add_dependency(PYPROJECT, "edgartools==5.58.0")
    assert '    "edgartools==5.58.0",\n    "earnings-core",' in text


def test_lowered_versions_compare_as_versions():
    old = {"lxml": "6.1.3", "pandas": "3.0.6", "numpy": "2.10.0"}
    new = {"lxml": "5.4.0", "pandas": "3.0.6", "numpy": "2.9.9"}
    assert lowered_versions(old, new) == [
        "lxml 6.1.3 -> 5.4.0",
        "numpy 2.10.0 -> 2.9.9",
    ]
    assert locked_versions(LOCK)["pandas"] == "3.0.6"


def test_runtime_closure_follows_requested_extras_only():
    closure = runtime_closure(LOCK)
    assert closure == {
        "lxml",
        "edgartools",
        "pandas",
        "numpy",
        "httpxthrottlecache",
        "filelock",
        "httpx",
    }
    assert "rapidfuzz" not in closure
```

`expirements/parser-fidelity/test_select_parser.py`:

```python
from score import rates
from select_parser import (
    control_check,
    priority_comparison,
    render,
    select,
    tie,
    worst_class,
)

NAMES = ("edgartools", "secparser", "walker", "control")


def pooled(coverage, footnotes=(0, 4), order=(0, 20), section=(0, 5), table=(0, 6)):
    counts = {
        "coverage": list(coverage),
        "footnote_merging": list(footnotes),
        "reading_order": list(order),
        "header_section": list(section),
        "header_table": list(table),
    }
    for extra in (
        "split",
        "other_merges",
        "duplication",
        "footnotes_in_tables",
        "cell_association",
    ):
        counts[extra] = [0, 0]
    return {"counts": counts, "rates": rates(counts)}


def classes(**by_candidate):
    """Two classes; each candidate gets (class A pooled, class B pooled)."""
    return {
        "clean_html": {name: values[0] for name, values in by_candidate.items()},
        "table_heavy": {name: values[1] for name, values in by_candidate.items()},
    }


def gates(nondeterministic=(), tripped=()):
    return {
        name: {
            "f1": {
                "deterministic": name not in nondeterministic,
                "guard_trips": ["socket.getaddrinfo"] if name in tripped else [],
            }
        }
        for name in NAMES
    }


LOCKS = {
    "edgartools": {
        "resolved": True,
        "lowered": [],
        "parse_ok": True,
        "pandas_added": True,
        "added_runtime": ["pandas", "pyarrow"],
    },
    "secparser": {
        "resolved": True,
        "lowered": ["lxml 6.1.3 -> 5.4.0"],
        "parse_ok": False,
        "pandas_added": True,
        "added_runtime": ["pandas"],
    },
    "walker": {
        "resolved": True,
        "lowered": [],
        "parse_ok": True,
        "pandas_added": False,
        "added_runtime": [],
    },
}


def test_worst_class_skips_classes_without_a_denominator():
    data = classes(
        walker=(pooled((9, 10), footnotes=(0, 0)), pooled((5, 10), footnotes=(1, 4)))
    )
    assert worst_class(data, "walker", "coverage") == (0.5, 10, "table_heavy")
    assert worst_class(data, "walker", "footnote_merging") == (0.25, 4, "table_heavy")


def test_tie_margin_uses_the_smaller_denominator():
    assert tie((0.80, 10, "a"), (0.75, 40, "b"))  # |0.05| <= 1/10
    assert not tie((0.80, 40, "a"), (0.70, 40, "b"))  # |0.10| > 1/40


def test_coverage_ranks_first():
    data = classes(
        edgartools=(pooled((95, 100)), pooled((60, 100), footnotes=(0, 4))),
        walker=(pooled((90, 100)), pooled((80, 100), footnotes=(3, 4))),
    )
    remaining, trace = priority_comparison(data, ["edgartools", "walker"])
    assert remaining == ["walker"]
    assert trace[0].startswith("coverage:")


def test_ties_fall_through_to_the_next_metric_then_tie_breaks():
    same = pooled((90, 100))
    data = classes(
        edgartools=(same, same),
        walker=(same, same),
        secparser=(same, same),
        control=(pooled((50, 100)), same),
    )
    outcome = select({"classes": data}, gates(), LOCKS)
    assert outcome["eligible"] == ["edgartools", "walker"]
    assert (
        outcome["selected"] == "walker"
    )  # tied on every metric; walker adds no dependency
    assert any(step.startswith("dependencies") for step in outcome["trace"])


def test_gates_exclude_ineligible_candidates_but_they_are_still_reported():
    strong, weak = pooled((99, 100)), pooled((70, 100))
    data = classes(
        edgartools=(weak, weak),
        secparser=(strong, strong),
        walker=(weak, weak),
        control=(weak, weak),
    )
    outcome = select({"classes": data}, gates(nondeterministic=("walker",)), LOCKS)
    assert outcome["eligible"] == ["edgartools"]
    assert outcome["selected"] == "edgartools"
    assert outcome["ineligible_would_have_won"] == ["secparser"]
    gains = outcome["ineligible_gains"]["secparser"]["coverage"]
    assert gains["ineligible"][0] == 0.99 and gains["selected"][0] == 0.70
    assert "secparser is ineligible but would have survived step 3" in render(outcome)


def test_no_eligible_candidate_returns_the_decision():
    data = classes(**{name: (pooled((90, 100)), pooled((90, 100))) for name in NAMES})
    outcome = select({"classes": data}, gates(tripped=("edgartools", "walker")), LOCKS)
    assert outcome["selected"] is None and "returns to the user" in outcome["status"]


def test_control_check_flags_fixtures_that_cannot_discriminate():
    same = pooled((90, 100))
    data = classes(walker=(same, same), control=(same, same))
    beats, discriminates = control_check(data, "walker")
    assert beats == {"clean_html": False, "table_heavy": False} and not discriminates
    data = classes(walker=(same, same), control=(pooled((60, 100)), same))
    assert control_check(data, "walker") == (
        {"clean_html": True, "table_heavy": False},
        True,
    )
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_lock_gate.py expirements/parser-fidelity/test_select_parser.py --import-mode=prepend -q`
Expected: 2 collection errors, `No module named 'lock_gate'` and `No module named 'select_parser'`.

- [x] **Step 3: Write the implementation**

`expirements/parser-fidelity/lock_gate.py`:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["packaging==26.3"]
# ///
"""The lock gate (spec: Selection rule, step 1; decision F7).

    uv run --locked --script expirements/parser-fidelity/lock_gate.py edgartools
    uv run --locked --script expirements/parser-fidelity/lock_gate.py secparser
    uv run --locked --script expirements/parser-fidelity/lock_gate.py walker

For a library candidate: extract HEAD into a scratch directory with ``git archive``, add
the pinned requirement to earnings-ingestion's runtime dependencies there, and run
``uv lock``. The gate passes when the lock resolves, lowers no locked version, and the
adapter imports and parses every fixture under Python 3.14 in the scratch workspace.
The repository itself is never modified. The walker adds no dependency: the gate checks
that its imports are already earnings-ingestion runtime dependencies and that it parses
every fixture in the workspace environment. Run only after the freeze and gold completion.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import tomllib
from packaging.requirements import Requirement
from packaging.version import Version
from pf_paths import FIXTURES, HARNESS, REPO_ROOT, RUNS

INGESTION = "earnings-ingestion"
INGESTION_PYPROJECT = Path("packages") / "earnings-ingestion" / "pyproject.toml"
LIBRARY_CANDIDATES = {
    "edgartools": ("edgartools==5.58.0", "adapter_edgartools.py"),
    "secparser": ("sec-parser==0.58.1", "adapter_secparser.py"),
}
WALKER_IMPORTS = ("lxml", "beautifulsoup4")


def add_dependency(pyproject_text: str, requirement: str) -> str:
    marker = "dependencies = [\n"
    at = pyproject_text.index(marker) + len(marker)
    return pyproject_text[:at] + f'    "{requirement}",\n' + pyproject_text[at:]


def locked_versions(lock: dict) -> dict[str, str]:
    return {p["name"]: p["version"] for p in lock["package"] if "version" in p}


def lowered_versions(old: dict[str, str], new: dict[str, str]) -> list[str]:
    return sorted(
        f"{n} {old[n]} -> {new[n]}"
        for n in old
        if n in new and Version(new[n]) < Version(old[n])
    )


def runtime_closure(lock: dict, root: str = INGESTION) -> set[str]:
    """Distributions ``root`` needs at run time, following requested extras (markers ignored: an upper bound)."""
    packages = {p["name"]: p for p in lock["package"]}
    visited: set[tuple[str, tuple[str, ...]]] = set()
    stack: list[tuple[str, tuple[str, ...]]] = [(root, ())]
    while stack:
        item = stack.pop()
        if item in visited:
            continue
        visited.add(item)
        name, extras = item
        entry = packages.get(name, {})
        deps = list(entry.get("dependencies", []))
        for extra in extras:
            deps += entry.get("optional-dependencies", {}).get(extra, [])
        stack.extend((dep["name"], tuple(dep.get("extra", ()))) for dep in deps)
    return {name for name, _ in visited} - {root}


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def parse_fixtures(
    workspace: Path, adapter: str, python_prefix: str = "3.14"
) -> tuple[bool, list[str]]:
    problems = []
    with tempfile.TemporaryDirectory() as out:
        for source in sorted(FIXTURES.glob("*/source.html")):
            dump, sidecar = Path(out) / "d.json", Path(out) / "s.json"
            command = ["uv", "run", "--directory", str(workspace), "--locked", "--all-packages", "python",
                       str(HARNESS / adapter), "--input", str(source), "--output", str(dump), "--sidecar", str(sidecar)]  # fmt: skip
            completed = _run(command, REPO_ROOT)
            status = (
                json.loads(sidecar.read_text())["status"]
                if sidecar.exists()
                else "no sidecar"
            )
            python = (
                json.loads(sidecar.read_text()).get("python", "")
                if sidecar.exists()
                else ""
            )
            if (
                completed.returncode != 0
                or status != "ok"
                or not python.startswith(python_prefix)
            ):
                problems.append(
                    f"{source.parent.name}: exit {completed.returncode}, status {status}, python {python}"
                )
    return not problems, problems


def library_gate(name: str) -> dict:
    requirement, adapter = LIBRARY_CANDIDATES[name]
    result: dict = {"candidate": name, "requirement": requirement}
    with tempfile.TemporaryDirectory() as scratch_dir:
        scratch = Path(scratch_dir)
        archive = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        )
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            tar.extractall(scratch, filter="data")
        pyproject = scratch / INGESTION_PYPROJECT
        pyproject.write_text(
            add_dependency(pyproject.read_text(encoding="utf-8"), requirement),
            encoding="utf-8",
        )
        old = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
        locked = _run(["uv", "lock"], scratch)
        result["resolved"] = locked.returncode == 0
        result["uv_lock_output"] = (locked.stdout + locked.stderr)[-4000:]
        if not result["resolved"]:
            result.update(
                lowered=[],
                added_runtime=[],
                pandas_added=False,
                parse_ok=False,
                parse_problems=["not run: uv lock failed"],
            )
            return result
        new = tomllib.loads((scratch / "uv.lock").read_text(encoding="utf-8"))
        result["lowered"] = lowered_versions(locked_versions(old), locked_versions(new))
        added = sorted(runtime_closure(new) - runtime_closure(old))
        result["added_runtime"] = added
        result["pandas_added"] = "pandas" in added
        if result["lowered"]:
            result.update(
                parse_ok=False,
                parse_problems=["not run: the lock lowers a locked version"],
            )
            return result
        synced = _run(["uv", "sync", "--locked", "--all-packages"], scratch)
        if synced.returncode != 0:
            result.update(
                parse_ok=False,
                parse_problems=[f"uv sync failed: {synced.stderr[-2000:]}"],
            )
            return result
        result["parse_ok"], result["parse_problems"] = parse_fixtures(scratch, adapter)
    return result


def walker_gate() -> dict:
    ingestion = tomllib.loads(
        (REPO_ROOT / INGESTION_PYPROJECT).read_text(encoding="utf-8")
    )
    declared = {Requirement(dep).name for dep in ingestion["project"]["dependencies"]}
    missing = [name for name in WALKER_IMPORTS if name not in declared]
    result: dict = {
        "candidate": "walker",
        "requirement": None,
        "resolved": not missing,
        "lowered": [],
        "added_runtime": missing,
    }
    result["pandas_added"] = False
    result["parse_ok"], result["parse_problems"] = parse_fixtures(
        REPO_ROOT, "walker.py"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or args[0] not in (*LIBRARY_CANDIDATES, "walker"):
        print(
            f"usage: lock_gate.py {{{','.join((*LIBRARY_CANDIDATES, 'walker'))}}}",
            file=sys.stderr,
        )
        return 2
    name = args[0]
    result = walker_gate() if name == "walker" else library_gate(name)
    result["passed"] = (
        bool(result["resolved"]) and not result["lowered"] and bool(result["parse_ok"])
    )
    out = RUNS / "gates" / f"lock-{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "uv_lock_output"},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`expirements/parser-fidelity/select_parser.py`:

```python
"""Apply the fixed selection rule (spec: Selection rule; decisions F6 and F7). Standard library only.

    uv run --locked --all-packages python expirements/parser-fidelity/select_parser.py

Reads scores.json, the fixture run gates, and the lock-gate results; writes
data/runs/parser-fidelity/selection.json and selection.md with the rule applied step by
step. The rule was fixed before any fixture was scored and this script must not change
after scoring begins.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import tomllib
from pf_paths import HARNESS, RUNS
from run_candidates import CANDIDATES
from score import RANKED

WORST = {
    "coverage": min,
    "footnote_merging": max,
    "reading_order": max,
    "header_loss": max,
}
BEST = {
    "coverage": max,
    "footnote_merging": min,
    "reading_order": min,
    "header_loss": min,
}


@dataclass(frozen=True)
class Meta:
    license: str
    permissive: bool
    package: str | None  # distribution name in the adapter's script lock
    lock: str | None


# Licenses read from the wheels' METADATA on 2026-09-22 (edgartools: License-Expression MIT;
# sec-parser: License MIT, OSI classifier). The walker is this project's own code.
META = {
    "edgartools": Meta("MIT", True, "edgartools", "adapter_edgartools.py.lock"),
    "secparser": Meta("MIT", True, "sec-parser", "adapter_secparser.py.lock"),
    "walker": Meta("project code", True, None, None),
}


def release_date(meta: Meta, harness: Path = HARNESS) -> str | None:
    if meta.lock is None:
        return None
    lock = tomllib.loads((harness / meta.lock).read_text(encoding="utf-8"))
    package = next(p for p in lock["package"] if p["name"] == meta.package)
    upload = (
        package.get("sdist", {}).get("upload-time")
        or package["wheels"][0]["upload-time"]
    )
    return str(upload)[:10]


def worst_class(
    classes: dict, candidate: str, metric: str
) -> tuple[float, int, str] | None:
    """(value, denominator, class) of the candidate's worst class; classes without a denominator are skipped."""
    values = []
    for cls, by_candidate in classes.items():
        rates = by_candidate[candidate]["rates"]
        if metric == "header_loss":
            if rates["header_loss"] is not None:
                values.append((rates["header_loss"], rates["header_loss_n"], cls))
        elif by_candidate[candidate]["counts"][metric][1]:
            values.append(
                (rates[metric], by_candidate[candidate]["counts"][metric][1], cls)
            )
    return WORST[metric](values, key=lambda v: v[0]) if values else None


def tie(a: tuple[float, int, str], b: tuple[float, int, str]) -> bool:
    return abs(a[0] - b[0]) <= 1 / min(a[1], b[1])


def priority_comparison(
    classes: dict, candidates: list[str]
) -> tuple[list[str], list[str]]:
    remaining, trace = list(candidates), []
    for metric in RANKED:
        if len(remaining) <= 1:
            break
        values = {c: worst_class(classes, c, metric) for c in remaining}
        defined = {c: v for c, v in values.items() if v is not None}
        if not defined:
            trace.append(f"{metric}: no candidate has a denominator; all remain")
            continue
        best = BEST[metric](defined.values(), key=lambda v: v[0])
        remaining = [c for c in remaining if values[c] is None or tie(values[c], best)]
        shown = ", ".join(
            f"{c}={v[0]:.3f} (n={v[1]}, worst class {v[2]})" if v else f"{c}=n/a"
            for c, v in values.items()
        )
        trace.append(
            f"{metric}: {shown}; best {best[0]:.3f}; within 1/n of best: {', '.join(remaining)}"
        )
    return remaining, trace


def tie_breaks(remaining: list[str], lock_gates: dict) -> tuple[list[str], list[str]]:
    trace = []
    if len(remaining) > 1:
        cost = {
            c: (lock_gates[c]["pandas_added"], len(lock_gates[c]["added_runtime"]))
            for c in remaining
        }
        low = min(cost.values())
        remaining = [c for c in remaining if cost[c] == low]
        trace.append(
            f"dependencies (pandas added, count added): {cost}; kept {remaining}"
        )
    if len(remaining) > 1:
        remaining = [c for c in remaining if META[c].permissive] or remaining
        trace.append(f"license: kept {remaining}")
    if len(remaining) > 1:
        dates = {c: release_date(META[c]) or "0000-00-00" for c in remaining}
        latest = max(dates.values())
        remaining = [c for c in remaining if dates[c] == latest]
        trace.append(f"most recent release: {dates}; kept {remaining}")
    return remaining, trace


def gate_results(run_gates: dict, lock_gates: dict) -> dict[str, dict[str, bool]]:
    results = {}
    for name in META:
        runs = run_gates.get(name, {})
        lock = lock_gates.get(name, {})
        results[name] = {
            "lock": bool(lock.get("resolved"))
            and not lock.get("lowered")
            and bool(lock.get("parse_ok")),
            "determinism": bool(runs)
            and all(r["deterministic"] for r in runs.values()),
            "network": bool(runs) and not any(r["guard_trips"] for r in runs.values()),
        }
    return results


def control_check(classes: dict, selected: str) -> tuple[dict[str, bool], bool]:
    beats = {}
    for cls, by_candidate in classes.items():
        wins = []
        for metric in ("coverage", "footnote_merging", "reading_order"):
            sel, ctl = (
                by_candidate[selected]["counts"][metric],
                by_candidate["control"]["counts"][metric],
            )
            if not sel[1] or not ctl[1]:
                continue
            diff = sel[0] / sel[1] - ctl[0] / ctl[1]
            margin = 1 / min(sel[1], ctl[1])
            wins.append(diff > margin if metric == "coverage" else -diff > margin)
        beats[cls] = any(wins)
    return beats, any(beats.values())


def select(scores: dict, run_gates: dict, lock_gates: dict) -> dict:
    classes = scores["classes"]
    gates = gate_results(run_gates, lock_gates)
    eligible = [name for name in META if all(gates[name].values())]
    trace = [f"eligibility: {gates}; eligible: {eligible or 'none'}"]
    outcome: dict = {
        "gates": gates,
        "eligible": eligible,
        "selected": None,
        "trace": trace,
    }
    if not eligible:
        outcome["status"] = "no eligible candidate: the decision returns to the user"
        return outcome
    remaining, steps = priority_comparison(classes, eligible)
    trace += steps
    remaining, steps = tie_breaks(remaining, lock_gates)
    trace += steps
    if len(remaining) == 1:
        outcome["selected"] = remaining[0]
        outcome["status"] = "selected"
    else:
        outcome["status"] = (
            f"tie after every tie-break ({', '.join(remaining)}): the decision returns to the user"
        )
        return outcome
    unrestricted, _ = priority_comparison(classes, list(META))
    outcome["ineligible_would_have_won"] = [
        c for c in unrestricted if c not in eligible
    ]
    outcome["ineligible_gains"] = {
        c: {
            metric: {
                "ineligible": worst_class(classes, c, metric),
                "selected": worst_class(classes, outcome["selected"], metric),
            }
            for metric in RANKED
        }
        for c in outcome["ineligible_would_have_won"]
    }
    beats, discriminates = control_check(classes, outcome["selected"])
    outcome["control_check"] = {
        "beats_control_by_class": beats,
        "fixtures_discriminate": discriminates,
    }
    return outcome


def render(outcome: dict) -> str:
    lines = ["# Selection rule applied (generated by select_parser.py)", ""]
    lines += [
        f"{number}. {step}" for number, step in enumerate(outcome["trace"], start=1)
    ]
    lines += [
        "",
        f"**Outcome:** {outcome['status']}"
        + (f" -- **{outcome['selected']}**" if outcome["selected"] else ""),
    ]
    for name, gains in outcome.get("ineligible_gains", {}).items():
        lines.append(
            f"**{name} is ineligible but would have survived step 3.** Worst-class values:"
        )
        for metric, pair in gains.items():
            ours, theirs = pair["selected"], pair["ineligible"]
            shown = [
                f"{v[0]:.3f} (n={v[1]}, {v[2]})" if v else "n/a" for v in (theirs, ours)
            ]
            lines.append(
                f"- {metric}: {name} {shown[0]} vs {outcome['selected']} {shown[1]}"
            )
    if "control_check" in outcome:
        check = outcome["control_check"]
        lines.append(
            f"**Control check:** beats the control by more than the tie margin in: {check['beats_control_by_class']}"
        )
        if not check["fixtures_discriminate"]:
            lines.append(
                "**Flag:** the fixtures cannot discriminate between parsers; the user decides whether to replace any."
            )
    return "\n".join(lines)


def main() -> int:
    scores = json.loads((RUNS / "scores" / "scores.json").read_text(encoding="utf-8"))
    run_gates = json.loads(
        (RUNS / "fixtures" / "gates.json").read_text(encoding="utf-8")
    )
    lock_gates = {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name in META
        if (path := RUNS / "gates" / f"lock-{name}.json").exists()
    }
    missing = [name for name in META if name not in lock_gates]
    if missing:
        print(f"lock gate results missing for {missing}; run lock_gate.py first")
        return 1
    outcome = select(scores, run_gates, lock_gates)
    (RUNS / "selection.json").write_text(
        json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (RUNS / "selection.md").write_text(render(outcome) + "\n", encoding="utf-8")
    print(render(outcome))
    return 0


if __name__ == "__main__":
    assert set(META) | {"control"} == set(CANDIDATES)
    raise SystemExit(main())
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `uv run --locked --all-packages pytest expirements/parser-fidelity/test_lock_gate.py expirements/parser-fidelity/test_select_parser.py --import-mode=prepend -q`
Expected: `10 passed`.

- [x] **Step 5: Lock, lint, and commit, before any scoring**

```bash
uv lock --script expirements/parser-fidelity/lock_gate.py
uv run --locked ruff format expirements/parser-fidelity
uv run --locked ruff check . && uv run --locked ruff format --check .
git add expirements/parser-fidelity/lock_gate.py expirements/parser-fidelity/lock_gate.py.lock expirements/parser-fidelity/select_parser.py expirements/parser-fidelity/test_lock_gate.py expirements/parser-fidelity/test_select_parser.py
git commit -m "feat(parser-fidelity): fix the lock gate and selection rule before scoring"
```

Record this commit's hash. V2 cites it as proof that the rule was fixed before any
fixture was scored.

---

### Task 19: Measure — fixture runs, gates, scores, selection

**Precondition:** gate B is complete (`check_fixtures.py` prints `fixture check
passed`), and Tasks 15, 17, and 18 are committed.

**Files:** none committed. Every output goes to `data/runs/parser-fidelity/`.

**Interfaces:**
- Consumes: everything above.
- Produces: `fixtures/gates.json`, `gates/lock-{edgartools,secparser,walker}.json`,
  `scores/scores.json`, `scores/metrics.md`, `selection.json`, and `selection.md`.
  Task 20 reads them.

- [ ] **Step 1: Verify the preconditions**

```bash
uv run --locked --all-packages python expirements/parser-fidelity/check_fixtures.py
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
```

Expected: `fixture check passed` and `freeze verified`.

- [ ] **Step 2: Run every candidate twice on every fixture**

Run: `uv run --locked --all-packages python expirements/parser-fidelity/run_candidates.py fixtures`

Expected: 32 lines, one per candidate and fixture, each with a `status` and
`deterministic` value; they write `data/runs/parser-fidelity/fixtures/gates.json`.
Nonzero statuses are results, not errors, with one exception:

- **An adapter-code crash or guard trip.** Read the sidecar and log in
  `data/runs/parser-fidelity/fixtures/<candidate>/<id>/`. If adapter or harness code
  caused the problem, not the library, make the minimal fix and record it:
  `freeze.py amend <file> --reason crash|network-guard --note "…"`. Commit the fix
  with `FROZEN.toml` (`fix(parser-fidelity): post-freeze <reason> fix in <file>`),
  then rerun that candidate with `--candidates <name>`.
- **A library crash, guard trip, or nondeterminism** stays as measured.

- [ ] **Step 3: Run the lock gates**

```bash
uv run --locked --script expirements/parser-fidelity/lock_gate.py edgartools
uv run --locked --script expirements/parser-fidelity/lock_gate.py secparser
uv run --locked --script expirements/parser-fidelity/lock_gate.py walker
```

Expected: each prints its JSON result, and all three have `"passed"`.

- **Expected outcomes.** The spec expects `secparser` to fail with lowered lxml and
  pandas. `edgartools` and `walker` pass if every fixture parses under Python 3.14.
- **Repository safety.** Each library gate works in a temporary `git archive` copy.
- Check that the repository is untouched:
  `git status --short uv.lock packages/`.
  Expected: no output.

- [ ] **Step 4: Score**

Run: `uv run --locked --all-packages python expirements/parser-fidelity/score.py`
Expected: `wrote …/scores/scores.json and …/scores/metrics.md`.

Open `metrics.md` and check it:

- every class has a row for every candidate;
- every ranked metric has a value or `n/a` with a reason.

- [ ] **Step 5: Apply the selection rule**

Run: `uv run --locked --all-packages python expirements/parser-fidelity/select_parser.py`

Expected: the step-by-step trace and an `**Outcome:**` line. Then:

- **`selected`:** go on to Task 20.
- **`no eligible candidate` or `tie after every tie-break`:** the spec returns the
  decision to the user. Present `selection.md` and wait. Stage 1 does not close until
  the ADR records a decision.
- **`Flag: the fixtures cannot discriminate`:** present it to the user at gate D
  (Task 21) before the ADR is accepted.

---

### Task 20: The V2 record and ADR 0001

**Files:**
- Create: `docs/verification/V2-parser-fidelity.md`
- Create: `docs/adr/0001-<decision-slug>.md`

**Interfaces:**
- Consumes: every Task 19 output, `approval.toml`, `gold-notes.md`, `FROZEN.toml`,
  and `data/runs/parser-fidelity/evidence/secparser-py314.txt`.
- Produces: the records that Stage 2 (element types and nesting), Stage 3 (ADR 0001,
  residual failures, altered anchors), and Stage 4 (the V1 record, `stage4_flags`)
  consume.

- [ ] **Step 1: Write the V2 record**

Create `docs/verification/V2-parser-fidelity.md` from this template. Replace every
`_(` instruction with the named content, copying generated tables verbatim:

```markdown
# V2: release parser fidelity

This record discharges V2, the open marker in R4.1 of
`specs/evidence-linked-theme-extraction.md`, for Stage 1 of
`specs/evidence-linked-theme-extraction-roadmap.md`. The decision is recorded in ADR
0001 (`docs/adr/`).

**Outcome:** _(replace with the outcome line from `data/runs/parser-fidelity/selection.md`)_

## Corpus

Eight release exhibits sit in `tests/fixtures/releases/`, two per class, each
committed byte-for-byte as EDGAR served it. Their provenance is in `manifest.toml` and
their source-register basis in `docs/source-register.toml` (`sec-edgar`).

The user approved the fixtures and the development set on
_(replace with `approved_on` from `expirements/parser-fidelity/approval.toml`)_.

_(replace with a table with one row per fixture:)_

- `fixture_id`
- `primary_class`
- issuer
- filing date
- exhibit type
- bytes
- `data_table_share`
- `pre_share`
- each malformed-layout test value
- `stage4_flags`

These class-test values only sort fixtures into classes. They are not quality
thresholds, and R13.1 is untouched.

## Gold protocol

- **Annotator and source.** The user was the sole annotator (D2). Gold was marked
  from a browser rendering of each `source.html`. No candidate output was shown or
  consulted, and every candidate ran on the fixtures only after all gold passed the
  validator.
- **Guidelines.** The guidelines, schema, and matching spaces are those of the spec's
  Gold annotation section.
- **Encoding check.** For each fixture, the annotator compared the validator's
  decoding with the browser's `document.characterSet`. _(replace with the per-fixture
  results from `expirements/parser-fidelity/gold-notes.md`)_
- **Effort.** Browsers and time spent: _(replace from `gold-notes.md`)_

## Candidates

Common setup:

- **Decoding.** Every candidate received the same decoded text from `pf_decode.py`,
  which follows browser rules. Charset detection is therefore outside this
  measurement; see "Findings for Stage 3".
- **Freeze.** The candidate sources were frozen at commit _(replace with `commit`
  from `expirements/parser-fidelity/FROZEN.toml`)_ before any fixture run.

| Candidate | Version | Interpreter | Lock | Parse path |
| --- | --- | --- | --- | --- |
| edgartools | 5.58.0 | _(replace with the sidecar `python`)_ | `adapter_edgartools.py.lock` | `edgar.documents.parse_html(html)`, default `ParserConfig` |
| sec-parser | 0.58.1 | _(replace with the sidecar `python`)_ | `adapter_secparser.py.lock` | `sec_parser.Edgar10QParser().parse(html)` |
| walker | project code | _(replace with the sidecar `python`)_ | `walker.py.lock` | `walker.parse(html)`, rules W0-W16 in `walker-rules.md` |
| control | beautifulsoup4 4.15.0 | _(replace with the sidecar `python`)_ | `control.py.lock` | `BeautifulSoup(html, "lxml").get_text("\n", strip=True)` |

sec-parser ran on Python 3.13. Its 0.58.1 release requires `lxml<6`, and no CPython
3.14 wheel satisfies that. _(replace with the output saved in
`data/runs/parser-fidelity/evidence/secparser-py314.txt`)_

### Type mappings

_(replace with each adapter's mapping table, copied from the adapter's constants:)_

- `CONTAINER_NODE_TYPES`, `LEAF_NODE_TYPES`, and the FOOTNOTE rule in
  `adapter_edgartools.py`;
- `TYPE_BY_CLASS` in `adapter_secparser.py`;
- W6-W13 for the walker;
- every line is a `paragraph` for the control.

### Gates

_(replace with a table of lock, determinism, and network results per candidate, from:)_

- `data/runs/parser-fidelity/gates/lock-*.json`, including lowered versions and the
  added runtime dependencies;
- `data/runs/parser-fidelity/fixtures/gates.json`.

### Post-freeze changes

_(replace with each `[[changes]]` entry in `FROZEN.toml` and its `git diff`, or with
"No change followed the freeze.")_

## Metrics

_(replace with the class tables, diagnostics, and per-fixture detail from
`data/runs/parser-fidelity/scores/metrics.md`)_

## Selection rule, applied

_(replace with `data/runs/parser-fidelity/selection.md`)_

## Control check

_(replace with the control-check line from `selection.md` and a sentence per class)_

## Residual failures (for Stage 3)

_(replace with the selected parser's residual lists from
`data/runs/parser-fidelity/scores/scores.json`, by fixture and block ID. Cover:)_

- missed;
- split;
- merged;
- misordered;
- header lost.

_(Then list its altered anchors, which Stage 3's R3.5 check must cover.)_

## Element types and nesting observed in the gold (for Stage 2)

_(replace with the gold structure from `scores.json`, fixture by fixture:)_

- block types;
- heading levels;
- list-item levels;
- where footnotes sit.

_(Then add the observations recorded in `gold-notes.md` about tables inside lists or
tables.)_

## Findings for Stage 3

- edgartools' own press-release path, `PressRelease.html()` in
  `edgar/company_reports/press_release.py`, decodes exhibit bytes as UTF-8 with
  `errors="replace"`. A windows-1252 exhibit would lose characters on that path.
  Stage 3's canonicalizer should decode before it parses.
- _(replace with any further finding the runs exposed)_

## Limitations

- **Sample.** There are only eight fixtures and one annotator, so agreement is not
  measurable (D2).
- **Rendering.** The gold was marked from a browser rendering.
- **Coverage.** Coverage checks each block's first and last words, not its middle.
- **Text fidelity** is not measured here. R3.5 belongs to Stage 3.
- **Interpreter.** sec-parser ran on Python 3.13, not 3.14.
- **Control.** The control is the spec's literal `get_text` call, so it also emits
  the document `<title>`.
- _(replace with any further limitation the runs exposed)_
```

In the Selection rule section, add one sentence citing the Task 18 commit hash: the
rule was fixed at that commit, before any fixture was scored. Check that no
instruction remains:

```bash
grep -n "_(" docs/verification/V2-parser-fidelity.md
```

Expected: no output.

- [ ] **Step 2: Scaffold the ADR**

With `<X>` as the selected parser (`edgartools`, `sec-parser`, or `the bespoke lxml
walker`), run:

```bash
python3 ~/.claude/skills/design-architecture/scripts/new_adr.py "Use <X> as the base parser for release canonicalization" --dir docs/adr --status Proposed
```

Expected: `docs/adr/0001-use-…-as-the-base-parser-for-release-canonicalization.md`
is created.

- [ ] **Step 3: Fill in the ADR**

Fill every section of the scaffold, keeping its headings:

- **Status:** `Proposed`, until the user accepts it.
- **Deciders:** leave empty; Task 21 fills it.
- **Blast radius:** `earnings-ingestion` (the Stage 3 canonicalizer) and every
  canonical document version.
- **Context:** a frozen snapshot of what was known at decision time:
  - R4.1's open marker;
  - the four classes and the eight fixtures;
  - the three candidates and the control;
  - the eligibility gates;
  - the fixed selection rule;
  - a pointer to `docs/verification/V2-parser-fidelity.md`.
- **Decision:** exactly "We will use <X> as the base parser for release
  canonicalization."
- **Consequences:**
  - positive: its measured strengths, with worst-class values from `selection.md`;
  - negative: its residual failures by type, which Stage 3 must compensate for or
    record, and its added dependencies from its lock-gate result;
  - neutral / follow-on: Stage 3 builds the canonicalizer on it and owns R3.5's text
    fidelity check.
- **Alternatives considered:** one bullet per losing candidate, and one for the
  control, each with its measured losing reason:
  - the gate it failed, with the reason from its lock-gate or run-gate JSON;
  - or the metric and worst-class values at which it fell outside the tie margin;
  - or the tie-break that separated it.
- **Trade-offs & reversibility:**
  - switching parsers changes canonical text, and so creates a new version of every
    document (R3.3);
  - name what would trigger a superseding ADR, such as a larger validation set
    (R12.2) or a candidate release that clears the lock gate.

- [ ] **Step 4: Commit**

Before committing anything public, check that the identity leaked nowhere. This lists
file names only, never the value:

```bash
grep -rlF -- "$EDGAR_IDENTITY" docs tests expirements
```

Expected: no output.

```bash
git add docs/verification/V2-parser-fidelity.md docs/adr/
git commit -m "docs(verification): record V2 parser fidelity and propose ADR 0001"
```

---

### Task 21: Gate D — the user accepts the decision

- [ ] **Step 1: Present the decision**

Give the user:

- `docs/verification/V2-parser-fidelity.md`, which covers the outcome, the control
  check, and the residual failures;
- `docs/adr/0001-….md`.

Raise explicitly any flag from Task 19 Step 5 (fixtures that cannot discriminate, no
eligible candidate, or an unresolved tie). Each is the user's decision. If they replace
fixtures, return to gate A for the replacements (Tasks 6, 7, 10), then rerun Task 19
and redo Task 20.

- [ ] **Step 2: Record the acceptance**

When the user accepts, edit the ADR:

- set `**Status:** Accepted`;
- set `**Deciders:**` to the name the user gives.

Once accepted, the ADR is immutable except for its status line.

```bash
git add docs/adr/
git commit -m "docs(adr): accept ADR 0001, the release base parser"
```

---

### Task 22: Final verification, CLAUDE.md, and handoff

**Files:**
- Modify: `CLAUDE.md` (the "Current state" section only)

- [ ] **Step 1: Run every check**

```bash
uv run --locked --all-packages python expirements/parser-fidelity/check_fixtures.py
uv run --locked --all-packages python expirements/parser-fidelity/freeze.py verify
uv run --locked --script expirements/parser-fidelity/fetch_policy_pages.py verify
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check .
uv run --locked ruff format --check .
git diff --exit-code main -- uv.lock packages/
grep -rn "_(" docs/verification docs/adr
grep -rlF -- "$EDGAR_IDENTITY" docs tests expirements
```

Expected, in order:

1. `fixture check passed`;
2. `freeze verified`;
3. `register quotes verified`;
4. `139 passed`, or more if Tasks 6, 12, 14, 17, or 19 added regression tests;
5. `All checks passed!`;
6. `… files already formatted`;
7. no diff and exit 0;
8. no output;
9. no output: the identity appears in no file.

- [ ] **Step 2: Refresh CLAUDE.md "Current state"**

In `CLAUDE.md`, update the "Current state: pre-implementation scaffold" section to say
that:

- `tests/fixtures/releases/` holds the eight Stage 1 fixtures with gold and
  `manifest.toml`;
- `docs/source-register.toml` exists;
- `expirements/parser-fidelity/` holds the harness, with its tests run by
  `uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q`;
- `docs/verification/` holds V1 and V2;
- `docs/adr/0001-….md` records the base parser;
- packages are still `hello()` stubs, and pytest configuration is still Stage 2's.

Leave every other section of `CLAUDE.md` unchanged, and do not edit `AGENTS.md`.

```bash
git add CLAUDE.md
git commit -m "docs: refresh CLAUDE.md current state after Stage 1"
```

- [ ] **Step 3: Write the handoff**

Report to the user:

- **Changes:** fixtures, register, harness, V1, V2, and ADR 0001, with its status.
- **Commands actually run,** with outcomes, including every live run and its request
  count:
  - policy pages (Task 3);
  - the discovery smoke run and each full run (Task 6);
  - V1 (Task 16).
- **Remaining blockers,** if any.
- **Two explicit statements:** no package tests exist yet, and no model was called.

Then run the Plan Completion Protocol, which the writing-plans skill defines. It ticks
Stage 1 in `specs/evidence-linked-theme-extraction-roadmap.md` through the roadmap's
reconcile step.
