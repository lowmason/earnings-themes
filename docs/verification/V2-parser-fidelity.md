# V2: release parser fidelity

This record discharges V2, the open marker in R4.1 of
`specs/evidence-linked-theme-extraction.md`, for Stage 1 of
`specs/evidence-linked-theme-extraction-roadmap.md`. The decision is recorded in ADR
0001 (`docs/adr/`).

**Outcome:** selected -- **walker**

The rule selected the walker, but two findings need the user's decision at gate D
before the ADR is accepted:

- **The control check flags the fixtures.** They cannot tell the parsers apart (see
  "Control check").
- **The deciding margin rests on six AEP footnotes.** Their anchors depend on where
  a parser puts page numbers (see "Selection rule, applied").

## Corpus

Eight release exhibits sit in `tests/fixtures/releases/`, two per class, each
committed byte-for-byte as EDGAR served it. Their provenance is in `manifest.toml` and
their source-register basis in `docs/source-register.toml` (`sec-edgar`).

The user approved the fixtures and the development set on
2026-09-22.

| `fixture_id` | `primary_class` | issuer | filing date | exhibit | bytes | `data_table_share` | `pre_share` | positioned text | layout-table prose (longest layout cell, words) | page-break debris (styling; bare page-number blocks) | preformatted text | `stage4_flags` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `0000003370-05-000209_ex-99` | `malformed_layout` | IKON OFFICE SOLUTIONS INC | 2005-10-27 | EX-99 | 51,121 | 0.0 | 0.5871 | no | yes (184) | no (no; 0) | yes | `narrative_only_release`, `alternative_exhibit_numbering` |
| `0000004904-24-000080_ex-99` | `malformed_layout` | AMERICAN ELECTRIC POWER CO INC | 2024-07-30 | EX-99 | 337,242 | 0.2831 | 0.0 | yes | no (3) | yes (yes; 36) | no | `alternative_exhibit_numbering` |
| `0000049071-06-000012_ex-99` | `table_heavy` | HUMANA INC | 2006-02-06 | EX-99 | 193,207 | 0.5754 | 0.0 | no | no (0) | no (no; 0) | no | `alternative_exhibit_numbering` |
| `0000068270-05-000104_ex-99` | `table_heavy` | RUBY TUESDAY INC | 2005-10-05 | EX-99 | 16,146 | 0.8457 | 0.0 | no | no (0) | no (no; 0) | no | `alternative_exhibit_numbering` |
| `0000315449-18-000009_ex-99-1` | `clean_html` | UQM TECHNOLOGIES INC | 2018-03-20 | EX-99.1 | 330,031 | 0.4211 | 0.0 | no | no (0) | no (yes; 0) | no | none |
| `0000859163-17-000071_ex-99-1` | `clean_html` | AVX Corp | 2017-10-25 | EX-99.1 | 199,923 | 0.1605 | 0.0 | no | no (0) | no (yes; 0) | no | none |
| `0001104659-23-049001_ex-99-1` | `narrative_only` | ESTABLISHMENT LABS HOLDINGS INC. | 2023-04-24 | EX-99.1 | 9,569 | 0.0 | 0.0 | no | no (0) | no (yes; 0) | no | `narrative_only_release` |
| `0001572910-14-000003_ex-99-1` | `narrative_only` | PHILLIPS 66 PARTNERS LP | 2014-01-22 | EX-99.1 | 7,739 | 0.0 | 0.0 | no | no (2) | no (no; 0) | no | `narrative_only_release` |

A malformed-layout test's value is shown with the measurement behind it in
parentheses. Page-break debris fires only when a document has both page-break styling
and at least one bare page-number block.

These class-test values only sort fixtures into classes. They are not quality
thresholds, and R13.1 is untouched.

## Gold protocol

- **Annotator and source.**
  - The user was the sole annotator.
  - F9, which amends D2 for Stage 1 gold only, let Codex draft seven fixtures' gold
    from the browser's rendered text. The user verified every block of each draft
    against the rendering.
  - The user marked Phillips 66 Partners (`0001572910-14-000003_ex-99-1`) by hand.
  - Gold was marked, and every draft was checked, from a browser rendering of each
    `source.html`.
  - No candidate output was shown or consulted, and every candidate ran on the
    fixtures only after all gold passed the validator.
  - The gold as scored is the eight `gold.toml` files as last committed, at
    `e79d477`.
- **F9 and the Codex brief.**
  - **The brief.** Codex worked under
    `expirements/parser-fidelity/codex-gold-brief.md`.
  - **What Codex saw.** Only the spec's Gold annotation section, the validator, and
    the text the user copied from the rendered page. It never saw a candidate's code,
    rules, or output.
  - **Sign-off.** Codex left the gold header blank, so a draft failed the validator
    until the user filled the header in. Filling it in was the user's sign-off, and
    the verified file is the gold. Its `annotator` reads "Lowell Mason (verified a
    Codex draft)".
  - **Revisions.** The brief was revised while drafting was under way:
    - `dfcd414` adopted F9.
    - `c12699b` reverted two revisions, `12b2236` and `e645d8e`, and restored the
      brief.
    - `980beb9` allowed hand-marking and stops Codex on a fixture that is already
      marked.
    - `0c97ca3` added the image and unanchorable-table policies.
    - `f61e11e` corrected the rule for table values split across cells.

    Humana's second draft is the only draft made under `f61e11e`.
- **Blocks changed by verification.**
  - **Method.** Each fixture's kept Codex draft
    (`data/runs/parser-fidelity/gold-drafts/<id>.codex.toml`) was compared with its
    gold:
    - A gold block is **unchanged** when a draft block matches it in every field but
      its ID.
    - Of the remaining blocks, a gold block and a draft block with the same `start`
      count as one **edited** block. For a table, the test is the same L cells.
    - Every other gold block counts as **added**, and every other draft block as
      **removed**.
  - **Humana.** Its count is against Codex's second draft. The first draft (164
    blocks) and the user's partial hand-marking from before it are set aside in
    `data/runs/parser-fidelity/set-aside/`.

| fixture | drafted by | draft blocks | gold blocks | unchanged | edited | added | removed |
|---|---|---|---|---|---|---|---|
| `0000003370-05-000209_ex-99` (IKON) | Codex, verified by the user | 44 | 44 | 40 | 4 | 0 | 0 |
| `0000004904-24-000080_ex-99` (AEP) | Codex, verified by the user | 88 | 90 | 65 | 19 | 6 | 4 |
| `0000049071-06-000012_ex-99` (Humana) | Codex (second draft), verified by the user | 174 | 153 | 129 | 22 | 2 | 23 |
| `0000068270-05-000104_ex-99` (Ruby Tuesday) | Codex, verified by the user | 2 | 4 | 0 | 2 | 2 | 0 |
| `0000315449-18-000009_ex-99-1` (UQM) | Codex, verified by the user | 37 | 29 | 15 | 8 | 6 | 14 |
| `0000859163-17-000071_ex-99-1` (AVX) | Codex, verified by the user | 23 | 22 | 15 | 3 | 4 | 5 |
| `0001104659-23-049001_ex-99-1` (Establishment Labs) | Codex, verified by the user | 14 | 14 | 12 | 2 | 0 | 0 |
| `0001572910-14-000003_ex-99-1` (Phillips 66 Partners) | the user, by hand | - | 16 | - | - | - | - |

- **Claude's part.** Claude, the assistant that executed the plan, wrote the walker,
  the adapters, the harness, the scorer, and this record. While the gold was being
  marked:
  - It showed no candidate output. The user made every decision on block boundaries
    and types.
  - It reported objective problems: validator errors, text covered twice or not at
    all, and anchors not found.
  - For some problems it proposed a fix, which the user applied:
    - the end anchor of AEP's b026;
    - the L cells of UQM's and AVX's t001 and t002, picked by a stated rule: the
      first L in reading order whose cells all meet the spec and whose rows all have
      labels;
    - in answer to the user's question, four paragraphs that took Humana's in-grid
      sentences out of table headers.
  - Its review found that six AEP footnotes (b051, b053, b055, b058, b068 and b070)
    could be anchored with `after` set to the page number that follows them. The user
    chose that anchoring.
  - Those six footnotes are the blocks on which the fixed rule separated the walker
    from edgartools. See "Selection rule, applied".
- **Guidelines.**
  - The guidelines, schema, and matching spaces are those of the spec's Gold
    annotation section.
  - They include two policies adopted on 2026-09-23 (`0c97ca3`):
    - an image's alt text gets no block;
    - a table whose values recur, so that no L of three unique cells exists, is marked
      `unanchorable`. It is counted and never scored.
  - 22 blocks are unanchorable:
    - AEP: 6 tables and 13 footnotes;
    - Humana: 3 tables.
- **Encoding check.** The protocol compares the validator's decoding with the
  browser's `document.characterSet`. For all eight fixtures, the validator reports
  UTF-8 (basis: `valid-utf-8`) with every byte ASCII, so any browser encoding agrees.
  The comparison was therefore skipped, as `gold-notes.md` records.
- **Effort.**
  - **Browser.** Google Chrome Version 154.0.8037.58 (Official Build) (arm64), for
    all eight fixtures.
  - **Time spent** verifying a draft, or marking by hand (6.75 hours in total):

    | Fixture | Hours |
    | --- | --- |
    | IKON | 1 |
    | AEP | 1.5 |
    | Humana | 2 |
    | Ruby Tuesday | 0.5 |
    | UQM | 0.5 |
    | AVX | 0.5 |
    | Establishment Labs | 0.5 |
    | Phillips 66 Partners (by hand) | 0.25 |

## Candidates

Common setup:

- **Decoding.** Every candidate received the same decoded text from `pf_decode.py`,
  which follows browser rules. Charset detection is therefore outside this
  measurement; see "Findings for Stage 3".
- **Freeze.** The candidate sources were frozen at commit
  `616721ab6eed46e0b72905e1c94ac93c7f2337db` before any fixture run. `cec29b7` recorded
  the freeze.

| Candidate | Version | Interpreter | Lock | Parse path |
| --- | --- | --- | --- | --- |
| edgartools | 5.58.0 | 3.14.0 | `adapter_edgartools.py.lock` | `edgar.documents.parse_html(html)`, default `ParserConfig` |
| sec-parser | 0.58.1 | 3.13.8 | `adapter_secparser.py.lock` | `sec_parser.Edgar10QParser().parse(html)` |
| walker | project code | 3.14.0 | `walker.py.lock` | `walker.parse(html)`, rules W0-W16 in `walker-rules.md` |
| control | beautifulsoup4 4.15.0 | 3.14.0 | `control.py.lock` | `BeautifulSoup(html, "lxml").get_text("\n", strip=True)` |

sec-parser ran on Python 3.13. Its 0.58.1 release requires `lxml<6`, and no CPython
3.14 wheel satisfies that:

```text
error: No solution found when resolving dependencies
  cause: Because lxml>=5.2.2,<=5.4.0 has no usable wheels and only the following versions of lxml are available:
             lxml<=5.4.0
             lxml>=6.0.0
         we can conclude that lxml>=5.2.2,<6.0.0 cannot be used.
         And because sec-parser>=0.58.1 depends on lxml>=5.2.2,<6.0.0 and you require sec-parser==0.58.1, we can conclude that your requirements are unsatisfiable.

hint: Wheels are required for `lxml` because building from source is disabled for `lxml` (i.e., with `--no-build-package lxml`)
```

The walker is this project's own code, written by Claude:

- The user approved its rules, W0-W16, at gate C (`b871314`), before development.
- Its code was committed at `c782712`, before any development-set work.
- It was developed on the three development releases only, which are the `[[devset]]`
  entries of `approval.toml`.
- On all three development releases, its text matched a Chromium browser pane's
  rendered text (`innerText`), compared after NFKC normalization with whitespace
  ignored.
- `616721a` recorded eight Known gaps from that work and changed no rule.

### Type mappings

**edgartools** (`adapter_edgartools.py`):

| `NodeType` | Common type |
| --- | --- |
| `DOCUMENT`, `SECTION`, `CONTAINER`, `LIST` (`CONTAINER_NODE_TYPES`) | a parent with no text, type `other` |
| `HEADING` | `heading`, with the node's level |
| `PARAGRAPH` | `paragraph`; `footnote` when the node carries `SemanticType.FOOTNOTE` |
| `LIST_ITEM` | `list_item` |
| `TABLE` | `table`, with its grid; a caption is emitted before it as `other` |
| `TEXT`, `LINK`, `IMAGE`, `XBRL_FACT` | `other` |

A leaf that holds a nested list or table is split around it (`STRUCTURAL_NODE_TYPES`).
The text before the nested block is the leaf's element. The nested block becomes that
element's child. Any later text is a further element of the leaf's type.

**sec-parser** (`TYPE_BY_CLASS` in `adapter_secparser.py`, resolved through each
element's class hierarchy):

| Element class | Common type |
| --- | --- |
| `TopSectionTitle`, `TitleElement` | `heading`, with the element's level |
| `TableElement`, `TableOfContentsElement` | `table` |
| `TextElement`, `SupplementaryText` | `paragraph` |
| `HighlightedTextElement`, `ImageElement`, `PageHeaderElement`, `PageNumberElement`, `EmptyElement`, `IntroductorySectionElement`, `IrrelevantElement`, `NotYetClassifiedElement`, `ErrorWhileProcessingElement`, `CompositeSemanticElement`, `AbstractSemanticElement` | `other` |

The adapter emits no `list_item` or `footnote`, because sec-parser has no such
classes. It exposes no table grid.

**Walker** (`walker-rules.md`):

| Rule | Block | Common type |
| --- | --- | --- |
| W6 | `h1`-`h6` | `heading`, level 1-6 |
| W7 | `ul`, `ol` | a container, type `other`, with no text |
| W7 | `li` | `list_item`; its level is the list's nesting depth |
| W8 | a bare page number | `other` |
| W9 | a leading bullet glyph, a dash and a space, or a Symbol or Wingdings run of at most 4 characters | `list_item` |
| W10 | a leading footnote marker followed by text | `footnote` |
| W11 | at most 12 words, every character bold or underlined | `heading`, with no level |
| W12 | anything else | `paragraph` |
| W13 | a marker-table row | `list_item` for a bullet or enumerator; `footnote` for a footnote marker |

Data tables (W14) are `table` elements carrying their grids, with header rows by W15.
Layout tables (W16) are walked as ordinary content.

**Control:** every line of `get_text` output is a `paragraph`.

### Gates

| candidate | lock gate | locked versions lowered | runtime distributions added to `earnings-ingestion` | determinism | network | eligible |
|---|---|---|---|---|---|---|
| edgartools | pass: resolves, lowers nothing, parses all 8 fixtures under Python 3.14 | none | 29, pandas among them | 8/8 fixtures byte-identical (16/16 runs `ok`) | 0 guard trips | yes |
| secparser | fail: `uv lock` resolves but lowers 4 locked versions, so the parse check did not run | lxml 6.1.3 -> 5.4.0; pandas 3.0.6 -> 2.3.3; tabulate 0.10.0 -> 0.9.0; xxhash 4.0.1 -> 3.8.1 | 23, pandas among them | 8/8 fixtures byte-identical (16/16 runs `ok`) | 0 guard trips | no |
| walker | pass: adds no dependency; its imports are already `earnings-ingestion` dependencies; parses all 8 fixtures under Python 3.14 | none | 0 | 8/8 fixtures byte-identical (16/16 runs `ok`) | 0 guard trips | yes |
| control | not run: not selectable | - | - | 8/8 fixtures byte-identical (16/16 runs `ok`) | 0 guard trips | not selectable |

- **edgartools adds:** `aiofiles`, `colorama`, `edgartools`, `filelock`, `httpxthrottlecache`, `humanize`, `jinja2`, `markdown-it-py`, `markupsafe`, `mdurl`, `nest-asyncio`, `numpy`, `orjson`, `pandas`, `pyarrow`, `pygments`, `pyrate-limiter`, `python-dateutil`, `rank-bm25`, `rapidfuzz`, `rich`, `six`, `stamina`, `tabulate`, `textdistance`, `tqdm`, `truststore`, `tzdata`, `unidecode`.
- **secparser adds:** `chardet`, `charset-normalizer`, `colorama`, `cssutils`, `encutils`, `frozendict`, `loguru`, `more-itertools`, `numpy`, `pandas`, `pyrate-limiter`, `python-dateutil`, `pytz`, `requests`, `sec-downloader`, `sec-edgar-downloader`, `sec-parser`, `six`, `tabulate`, `tzdata`, `urllib3`, `win32-setctime`, `xxhash`.

- **Lock-gate results.** From `data/runs/parser-fidelity/gates/lock-*.json`.
- **Determinism and network.** From `data/runs/parser-fidelity/fixtures/gates.json`:
  - 64 runs, each candidate twice per fixture in a fresh process with default hash
    randomization;
  - the two dumps were compared byte for byte.
- **Repository.** After the lock gates, `git status --short uv.lock packages/` printed
  nothing.

### Changes before the freeze

A whole-branch code review ran before the freeze and before any fixture run. Its
fixes, all committed before the freeze:

- **Walker:**
  - `3f5fb45`: W11 applies row and row-group styles to layout cells.
  - `89b1772`: W9 symbol fonts and W10 `sup` mark W13 marker cells.
  - `08da41f`: W5 keeps inline styles and line breaks in `pre` pieces.
  - `db9b15d`: plain blocks nested in headings and list items take their type. This
    is the user's reading of W6 and W7.
- **edgartools adapter:**
  - `1513f7d`: nested lists and tables are kept out of leaf text.
  - `913390b`: a comment was moved.
- **Harness:**
  - `e4bac05`: lock gates refuse to run until the freeze and the gold are ready.
  - `f2a644e`: `EDGAR_IDENTITY` is kept out of candidate processes.
  - `3c56834`: an SEC block page served with status 200 stops a live run.
- **Selection rule:** `9a75074` makes tied worst classes use the smallest denominator.
  This was the user's decision.

The development-set work changed no frozen file.

### Post-freeze changes

No change followed the freeze. `FROZEN.toml` has no `[[changes]]` entry, and
`freeze.py verify` passed before the fixture runs.

One harness file outside the freeze changed afterwards:

- **What changed.** `9fce0b2` added the live-fetch policy's stops to the V1 probe,
  `v1_return_types.py`, before V1's live run. The stops are a persistent 403, a 429,
  and the request cap.
- **Scope.** It touches no candidate and no scoring code.
- **Record.** `docs/verification/V1-edgartools-return-types.md` describes it.

## Metrics

Generated by `score.py`, unchanged since `743a486`. Every candidate was scored on its
first dump of each fixture.

### Block coverage (higher is better)

| class | edgartools | secparser | walker | control |
|---|---|---|---|---|
| clean_html | 1.000 (42/42) | 1.000 (42/42) | 1.000 (42/42) | 1.000 (42/42) |
| malformed_layout | 0.939 (92/98) | 0.959 (94/98) | 1.000 (98/98) | 1.000 (98/98) |
| narrative_only | 1.000 (27/27) | 1.000 (27/27) | 1.000 (27/27) | 1.000 (27/27) |
| table_heavy | 1.000 (152/152) | 1.000 (152/152) | 1.000 (152/152) | 1.000 (152/152) |

### Footnote merging (lower is better)

| class | edgartools | secparser | walker | control |
|---|---|---|---|---|
| clean_html | n/a (0/0) | n/a (0/0) | n/a (0/0) | n/a (0/0) |
| malformed_layout | 0.000 (0/17) | 0.053 (1/19) | 0.000 (0/23) | 0.000 (0/23) |
| narrative_only | n/a (0/0) | n/a (0/0) | n/a (0/0) | n/a (0/0) |
| table_heavy | 0.190 (4/21) | 0.619 (13/21) | 0.190 (4/21) | 0.000 (0/21) |

### Reading-order corruption (lower is better)

| class | edgartools | secparser | walker | control |
|---|---|---|---|---|
| clean_html | 0.000 (0/48) | 0.000 (0/48) | 0.000 (0/48) | 0.000 (0/48) |
| malformed_layout | 0.000 (0/108) | 0.000 (0/110) | 0.000 (0/114) | 0.000 (0/114) |
| narrative_only | 0.000 (0/25) | 0.000 (0/25) | 0.000 (0/25) | 0.000 (0/25) |
| table_heavy | 0.000 (0/190) | 0.000 (0/190) | 0.000 (0/190) | 0.000 (0/190) |

### Header loss (lower is better)

| class | edgartools | secparser | walker | control |
|---|---|---|---|---|
| clean_html | 0.500 (n=36) | 0.154 (n=36) | 0.115 (n=36) | 1.000 (n=36) |
| malformed_layout | 0.774 (n=157) | 0.669 (n=157) | 0.537 (n=157) | 1.000 (n=157) |
| narrative_only | 1.000 (n=10) | 0.500 (n=10) | 0.000 (n=10) | 1.000 (n=10) |
| table_heavy | 0.441 (n=239) | 0.639 (n=239) | 0.426 (n=239) | 1.000 (n=239) |

### Diagnostics by class

#### clean_html

| candidate | altered | split | other merges | duplication | footnotes in tables | cell association | unanchorable |
|---|---|---|---|---|---|---|---|
| edgartools | 0 | 9/38 | 4/42 | 0/78 | 0/0 | 12/12 | 0 |
| secparser | 0 | 6/38 | 28/42 | 0/78 | 0/0 | no cells exposed | 0 |
| walker | 0 | 9/38 | 4/42 | 0/78 | 0/0 | 12/12 | 0 |
| control | 0 | 20/38 | 0/42 | 0/78 | 0/0 | no cells exposed | 0 |

#### malformed_layout

| candidate | altered | split | other merges | duplication | footnotes in tables | cell association | unanchorable |
|---|---|---|---|---|---|---|---|
| edgartools | 0 | 5/83 | 17/75 | 0/167 | 0/17 | 0/6 | 19 |
| secparser | 13 | 2/85 | 60/75 | 0/169 | 0/19 | no cells exposed | 19 |
| walker | 0 | 5/89 | 8/75 | 0/173 | 0/23 | 6/6 | 19 |
| control | 0 | 41/89 | 0/75 | 0/173 | 0/23 | no cells exposed | 19 |

#### narrative_only

| candidate | altered | split | other merges | duplication | footnotes in tables | cell association | unanchorable |
|---|---|---|---|---|---|---|---|
| edgartools | 0 | 1/27 | 0/27 | 0/36 | 0/0 | 0/0 | 0 |
| secparser | 0 | 1/27 | 17/27 | 0/36 | 0/0 | no cells exposed | 0 |
| walker | 0 | 1/27 | 0/27 | 0/36 | 0/0 | no cells exposed | 0 |
| control | 0 | 11/27 | 0/27 | 0/36 | 0/0 | no cells exposed | 0 |

#### table_heavy

| candidate | altered | split | other merges | duplication | footnotes in tables | cell association | unanchorable |
|---|---|---|---|---|---|---|---|
| edgartools | 0 | 0/132 | 43/131 | 0/257 | 14/21 | 27/60 | 3 |
| secparser | 0 | 0/132 | 118/131 | 0/257 | 9/21 | no cells exposed | 3 |
| walker | 0 | 0/132 | 43/131 | 0/257 | 14/21 | 47/60 | 3 |
| control | 0 | 9/132 | 0/131 | 0/257 | 0/21 | no cells exposed | 3 |

### Per-fixture detail

#### `0000003370-05-000209_ex-99` (malformed_layout)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 41/41 | 0/3 | 0/54 | 2/7 | 112/112 | 0.9318 | - |
| secparser | 41/41 | 0/3 | 0/54 | 6/7 | 112/112 | 0.6257 | b005:start, b007:end, b007:start, b009:end, b009:start, b010:end, b022:end, b023:start, b025:end, b025:start, b026:end, b026:start, b029:start |
| walker | 41/41 | 0/3 | 0/54 | 1/7 | 112/112 | 0.0029 | - |
| control | 41/41 | 0/3 | 0/54 | 7/7 | 112/112 | 0.0325 | - |

#### `0000004904-24-000080_ex-99` (malformed_layout)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 51/57 | 0/14 | 0/54 | 12/12 | 0/26 | 0.4442 | - |
| secparser | 53/57 | 1/16 | 0/56 | 4/12 | 0/26 | 0.2229 | - |
| walker | 57/57 | 0/20 | 0/60 | 4/12 | 0/26 | 0.0194 | - |
| control | 57/57 | 0/20 | 0/60 | 12/12 | 26/26 | 0.0267 | - |

#### `0000049071-06-000012_ex-99` (table_heavy)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 149/149 | 4/21 | 0/186 | 30/32 | 0/202 | 0.4002 | - |
| secparser | 149/149 | 13/21 | 0/186 | 32/32 | 60/202 | 0.2582 | - |
| walker | 149/149 | 4/21 | 0/186 | 29/32 | 0/202 | 0.0225 | - |
| control | 149/149 | 0/21 | 0/186 | 32/32 | 202/202 | 0.039 | - |

#### `0000068270-05-000104_ex-99` (table_heavy)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 3/3 | 0/0 | 0/4 | 0/2 | 0/3 | 0.3585 | - |
| secparser | 3/3 | 0/0 | 0/4 | 1/2 | 3/3 | 0.1948 | - |
| walker | 3/3 | 0/0 | 0/4 | 0/2 | 0/3 | 0.0018 | - |
| control | 3/3 | 0/0 | 0/4 | 2/2 | 3/3 | 0.0134 | - |

#### `0000315449-18-000009_ex-99-1` (clean_html)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 21/21 | 0/0 | 0/24 | 8/8 | 0/11 | 0.3965 | - |
| secparser | 21/21 | 0/0 | 0/24 | 3/8 | 0/11 | 0.2251 | - |
| walker | 21/21 | 0/0 | 0/24 | 2/8 | 0/11 | 0.0158 | - |
| control | 21/21 | 0/0 | 0/24 | 8/8 | 11/11 | 0.0275 | - |

#### `0000859163-17-000071_ex-99-1` (clean_html)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 21/21 | 0/0 | 0/24 | 5/5 | 0/12 | 0.381 | - |
| secparser | 21/21 | 0/0 | 0/24 | 1/5 | 0/12 | 0.2064 | - |
| walker | 21/21 | 0/0 | 0/24 | 1/5 | 0/12 | 0.0096 | - |
| control | 21/21 | 0/0 | 0/24 | 5/5 | 12/12 | 0.0197 | - |

#### `0001104659-23-049001_ex-99-1` (narrative_only)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 13/13 | 0/0 | 0/12 | 5/5 | 0/0 | 0.3576 | - |
| secparser | 13/13 | 0/0 | 0/12 | 5/5 | 0/0 | 0.1856 | - |
| walker | 13/13 | 0/0 | 0/12 | 0/5 | 0/0 | 0.0005 | - |
| control | 13/13 | 0/0 | 0/12 | 5/5 | 0/0 | 0.0118 | - |

#### `0001572910-14-000003_ex-99-1` (narrative_only)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 14/14 | 0/0 | 0/13 | 5/5 | 0/0 | 0.3634 | - |
| secparser | 14/14 | 0/0 | 0/13 | 0/5 | 0/0 | 0.1882 | - |
| walker | 14/14 | 0/0 | 0/13 | 0/5 | 0/0 | 0.0005 | - |
| control | 14/14 | 0/0 | 0/13 | 5/5 | 0/0 | 0.012 | - |

## Selection rule, applied

Generated by `select_parser.py`:

1. eligibility: {'edgartools': {'lock': True, 'determinism': True, 'network': True}, 'secparser': {'lock': False, 'determinism': True, 'network': True}, 'walker': {'lock': True, 'determinism': True, 'network': True}}; eligible: ['edgartools', 'walker']
2. coverage: edgartools=0.939 (n=98, worst class malformed_layout), walker=1.000 (n=27, worst class narrative_only); best 1.000; within 1/n of best: walker

**Outcome:** selected -- **walker**
**Control check:** beats the control by more than the tie margin in: {'clean_html': False, 'malformed_layout': False, 'narrative_only': False, 'table_heavy': False}
**Flag:** the fixtures cannot discriminate between parsers; the user decides whether to replace any.

**When the rule was fixed.**

- The rule was fixed at commit `8c7331a`, before any fixture was scored.
- Two later commits changed the rule's code, both before any scoring:
  - `9a75074`, the user's decision that tied worst classes use the smallest
    denominator;
  - `e4bac05`, which makes the lock gate refuse to run until the freeze and the gold
    are ready.
- Under the code before `9a75074`, the walker's coverage n would have been 42. That is
  clean_html, the first class in order, instead of 27. Any n from 27 to 152 gives a
  margin below edgartools' gap of 0.061, so the outcome is the same.

**Ineligible candidates.** None would have survived step 3. sec-parser's worst
coverage is 0.959 (n=98, malformed_layout), outside 1/27 of the walker's 1.000.

**What decided it.**

- **The misses.** The rule stopped at coverage, on one fixture, AEP
  (`0000004904-24-000080_ex-99`). There, edgartools missed six blocks: b051, b053,
  b055, b058, b068 and b070. It missed nothing else on any fixture.
- **Why these six have page-number anchors.** Each footnote's text recurs in AEP's
  other reconciliation. Each is therefore anchored with `after` set to the bare page
  number that follows it.
- **The footnote text is present.** edgartools emits both copies of each footnote's
  text, so the text was not lost.
- **edgartools misses them** because it drops all twelve of AEP's bare page numbers.
  In its output the text on either side of each one joins directly, so every `after`
  anchor fails.
- **sec-parser misses four of them** (b051, b053, b058 and b068). It emits the page
  numbers as elements, but only three of the twelve sit where the page shows them.
- **So the margin measures page-number placement.** The coverage gap between the
  walker and edgartools measures where page numbers land, not lost footnote text.

**Robustness reading (outside the rule).**

- **Status.** This is not part of the fixed rule. It was computed in memory, and
  `scores.json` and `selection.md` are unchanged.
- **Assumption.** The six footnotes are treated as unanchorable.
- **Ties.** edgartools and the walker then tie on coverage (1.000), footnote merging
  (0.190, n=21, table_heavy) and reading order (0.000). sec-parser, which is
  ineligible, would drop out at footnote merging (0.619, n=21).
- **Header loss decides.** edgartools scores 1.000 (n=10, narrative_only) against the
  walker's 0.537 (n=157, malformed_layout), outside the 1/10 margin.
- **Why edgartools loses the narrative headings.** It types nine of the ten gold
  headings in the two narrative releases as paragraphs. The tenth, Phillips 66
  Partners' "Exhibit 99.1" (b002), lands in a table element.
- **Result.** The walker would still be selected, but at the fourth ranked metric
  rather than the first.

## Control check

**Control check:** beats the control by more than the tie margin in: {'clean_html': False, 'malformed_layout': False, 'narrative_only': False, 'table_heavy': False}

- **clean_html.** The walker and the control both find 42 of 42 blocks and reverse
  0 of 48 pairs. The class has no footnotes.
- **malformed_layout.** Both find 98 of 98 blocks, merge 0 of 23 footnotes, and
  reverse 0 of 114 pairs.
- **narrative_only.** Both find 27 of 27 blocks and reverse 0 of 25 pairs. The class
  has no footnotes.
- **table_heavy.** Both find 152 of 152 blocks and reverse 0 of 190 pairs. On
  footnote merging the control leads: the walker merges 4 of 21 footnotes into body
  elements, and the control merges none.

Why the control cannot be beaten here:

- **Coverage.** It found every block on every fixture.
- **Footnote merging.** It emits each line as its own element, and no footnote shared
  an element with body text.
- **Reading order.** No candidate reversed any pair of blocks on any fixture.

So on these fixtures the check's three metrics cannot separate any parser from the
control. The spec excludes header loss, the metric that does separate them, because
the control has no element types.

The spec gives the next step to the user. Before accepting the ADR, the user decides
whether to replace any fixture.

## Residual failures (for Stage 3)

The walker's residual lists, from `data/runs/parser-fidelity/scores/scores.json`:

| fixture | missed | split | merged | misordered | header lost |
|---|---|---|---|---|---|
| `0000003370-05-000209_ex-99` (IKON) | none | none | none | none | b002; all 112 header texts of t001-t007 |
| `0000004904-24-000080_ex-99` (AEP) | none | b017, b025, b026, b039, b043 | b004, b005, b006, b007, b008, b009, b010, b011 | none | b002, b003, b004, b005 |
| `0000049071-06-000012_ex-99` (Humana) | none | none | b082, b083, b084, b085, b086, b087, b088, b089, b090, b091, b092, b093, b094, b095, b096, b097, b098, b099, b100, b101, b102, b103, b104, b105, b106, b107, b108, b109, b110, b111, b112, b118, b120, b121, b129, b131, b132, b133, b136, t009, t010, t011, t012, t013, t017, t020, t021 | none | b003, b004, b021, b022, b024, b028, b032, b034, b036, b037, b039, b042, b045, b048, b054, b057, b065, b069, b071, b081, b082, b085, b091, b097, b099, b105, b107, b109, b111 |
| `0000068270-05-000104_ex-99` (Ruby Tuesday) | none | none | none | none | none |
| `0000315449-18-000009_ex-99-1` (UQM) | none | b008, b014, b019, b020 | b004, b005, b006, b007 | none | b004, b018 |
| `0000859163-17-000071_ex-99-1` (AVX) | none | b012, b015, b016, b017, b020 | none | none | b019 |
| `0001104659-23-049001_ex-99-1` (Establishment Labs) | none | none | none | none | none |
| `0001572910-14-000003_ex-99-1` (Phillips 66 Partners) | none | b003 | none | none | none |

- **Merged** joins two groups:
  - footnotes that share an element with body text;
  - text blocks and tables that share an element with another block.
- **Header lost** joins two groups:
  - headings whose element is not a heading, or is shared;
  - table header texts absent from the table's elements.

The walker loses 37 headings in all:

- 25 of them it types `paragraph`;
- 12 sit inside table elements:
  - AEP b004 and b005;
  - Humana b082, b085, b091, b097, b099, b105, b107, b109 and b111;
  - UQM b004.

**Altered anchors: none.** Every anchor the walker matched, it matched in the primary
space. Stage 3's R3.5 check therefore inherits no altered anchor from the walker.
sec-parser is the only candidate with altered anchors: 13, all on IKON.

## Element types and nesting observed in the gold (for Stage 2)

From the gold structure in `scores.json`. A footnote's placement is the type of the
nearest block before it that is neither a footnote nor a `page_artifact`.

| fixture | block types | heading levels | list-item levels | footnotes, by the nearest block before them |
|---|---|---|---|---|
| `0000003370-05-000209_ex-99` (IKON) | footnote: 3, heading: 7, page_artifact: 3, paragraph: 24, table: 7 | 1: 2, 2: 5 | none | after table: 3 |
| `0000004904-24-000080_ex-99` (AEP) | footnote: 33, heading: 12, list_item: 3, page_artifact: 14, paragraph: 20, table: 8 | 1: 2, 2: 10 | 1: 3 | after table: 33 |
| `0000049071-06-000012_ex-99` (Humana) | footnote: 21, heading: 32, list_item: 19, page_artifact: 1, paragraph: 58, table: 22 | 1: 3, 2: 19, 3: 10 | 1: 19 | after heading: 8, after table: 13 |
| `0000068270-05-000104_ex-99` (Ruby Tuesday) | heading: 2, page_artifact: 1, table: 1 | 1: 1, 2: 1 | none | none |
| `0000315449-18-000009_ex-99-1` (UQM) | heading: 8, page_artifact: 8, paragraph: 11, table: 2 | 1: 2, 2: 4, 3: 2 | none | none |
| `0000859163-17-000071_ex-99-1` (AVX) | heading: 5, page_artifact: 1, paragraph: 14, table: 2 | 1: 4, no level: 1 | none | none |
| `0001104659-23-049001_ex-99-1` (Establishment Labs) | heading: 5, page_artifact: 1, paragraph: 8 | 1: 2, 2: 3 | none | none |
| `0001572910-14-000003_ex-99-1` (Phillips 66 Partners) | heading: 5, page_artifact: 2, paragraph: 9 | 1: 2, 2: 3 | none | none |

From `gold-notes.md`:

- **Nested tables.** No fixture has a table inside a list or inside another table.
  Phillips 66 Partners' only HTML table is a layout table holding the "Exhibit 99.1"
  label.
- **Several visible tables in one HTML table.**
  - AEP: one HTML table holds two visible tables (t002 and t003).
  - Humana: t009-t013 share one HTML table, t019-t020 another, and t021-t022 a third.
    Its in-grid prose is marked as paragraphs placed immediately before the tables.
- **One visible table across two HTML tables.** UQM's balance sheet (t002) spans two
  HTML tables.
- **Tables drawn in `<pre>`.** IKON's seven tables are drawn with spaces inside
  `<pre>`. Their headers and L come from text lines, so P7's grid checks cannot apply
  to them.

## Findings for Stage 3

- **edgartools' press-release decoding.** edgartools' own press-release path,
  `PressRelease.html()` in `edgar/company_reports/press_release.py`, decodes exhibit
  bytes as UTF-8 with `errors="replace"`. A windows-1252 exhibit would lose characters
  on that path. Stage 3's canonicalizer should decode before it parses.
- **Encoding coverage.** All eight fixtures and all three development releases are
  pure ASCII. The shared browser-rules decoding (`pf_decode.py`) was never exercised
  on a non-ASCII byte.
- **Page numbers.** AEP prints bare page numbers, 1 to 12:
  - edgartools 5.58.0 drops all twelve;
  - the walker keeps each one in place as an `other` element (W8);
  - sec-parser emits them as elements, but only three sit where the page shows them.

  The gold marks page numbers as `page_artifact`, so they are never scored
  themselves. But a footnote whose text recurs can be anchored only by what follows
  it. Stage 3 decides whether canonical text keeps page numbers.
- **Tables drawn in `<pre>`.** No candidate exposes IKON's seven `<pre>` tables as
  tables, so every candidate loses all 112 of their header texts. The walker emits
  them as text blocks split at blank lines (W5). Stage 3 must either rebuild such
  tables or record them as a limitation.
- **Text set in tables that pass the data-table test.** A table with at least two
  rows of text and one row of two or more non-empty cells is a data table under the
  class tests' definition, which W14 uses. The walker therefore emits three text
  sections set in such tables as single table elements. Their blocks merge, and their
  headings count as lost:
  - AEP's contacts (b004-b011);
  - UQM's contact block (b004-b007);
  - Humana's GAAP earnings guidance (b082-b112: 9 headings, 21 paragraphs and a
    footnote).

  Humana's other merges come from HTML tables that hold several visible tables, or a
  table together with the prose around it. For example, t009-t013 share one element.
- **Styled headings.** W11 types a heading only when every character is bold or
  underlined and it has at most 12 words. 25 gold headings that the walker found are
  typed `paragraph`.
- **The walker's Known gaps.** `walker-rules.md` (`616721a`) lists eight patterns
  from the development set that no rule covers. Stage 3 inherits them:
  - a paragraph interrupted by a page break becomes two;
  - a "Page N of M" footer is a paragraph;
  - the EDGAR filing header line is a paragraph;
  - a centred "##" end mark is a paragraph;
  - a title or exhibit label set apart only by position, alignment or capitals is a
    paragraph;
  - a heading that runs over two lines becomes two headings;
  - a second set of column headers partway down a data table is not flagged;
  - a footnote set as a data table's last row stays in its grid.
- **Rules as written, on the development set.** `616721a`'s commit body records two
  outcomes:
  - W11 types short all-bold or all-underlined sentences, and underlined URLs, as
    headings;
  - W15's leading-rows clause flags stub labels such as "ASSETS:" and "Current
    assets:" as header rows.

  The development set never exercised:
  - `pre`, `li`, `h1`-`h6`, `th`, `thead` and `caption`;
  - `display: none`, symbol fonts and double `<br>`;
  - marker tables.

## Limitations

- **Sample.** There are only eight fixtures and one annotator, who verified Codex
  drafts where a fixture was not marked by hand (F9). Agreement is therefore not
  measurable (D2).
- **Rendering.** The gold was marked, and Codex's drafts were checked, from a browser
  rendering.
- **Coverage.** Coverage checks each block's first and last words, not its middle.
- **Text fidelity** is not measured here. R3.5 belongs to Stage 3.
- **Interpreter.** sec-parser ran on Python 3.13.8, not 3.14.
- **Control.** The control is the spec's literal `get_text` call, so it also emits
  the document `<title>`.
- **The deciding margin.** It rests on six AEP footnotes whose only unique anchors are
  the page numbers after them. See "Selection rule, applied".
- **The control check** cannot be passed on these fixtures. See "Control check".
- **False headings go uncounted.** Header loss counts gold headings that a parser
  fails to type as headings. It does not count paragraphs a parser types as headings.
  An in-memory check outside the scorer compared each gold paragraph, footnote and
  list item a parser found with the element that holds its start:

  | Parser | Typed as headings |
  | --- | --- |
  | walker | 3 of 210 (UQM b003; Phillips 66 Partners b011 and b014) |
  | sec-parser | 6 of 206 |
  | edgartools | 0 of 204 |
- **Authorship.** Claude wrote the walker, the other adapters, the harness and the
  scorer, and proposed mechanical gold fixes (see "Gold protocol"). The user approved
  the walker's rules, the fixtures, the selection rule and every gold block.
- **Unanchorable blocks.** 22 blocks are unanchorable, so they are never scored.

## Deviations from the plan

- **Discovery.** The default sample held only one clean table-heavy candidate. The
  plan's contingency sample (filing years 2006, 2009, 2012, 2015, 2018, 2021 and 2024)
  was therefore run before the fixtures were chosen. The user approved this at gate A.
- **Task 9 Step 5** printed one problem per fixture, not two:
  - `check_fixtures.py` validates gold only when `gold.toml` exists, so the "gold.toml
    is missing" line cannot print.
  - The "holds ['source.html']" line reports the missing gold instead.
  - `run_candidates.fixture_preconditions` still lists every missing gold.
- **Task 12 Step 8.** The smoke loop prints `exit=$?` after `$(basename …)` on the same
  line, so it always prints 0. Each run's exit code was instead captured directly
  after it; all were 0.
- **Template changes.** This record adds to the plan's V2 template:
  - the two gate-D notes under the outcome;
  - F9's protocol and the per-fixture count of blocks changed, which the spec's
    Records section requires;
  - Claude's part in the gold and the walker's development history;
  - the changes before the freeze;
  - the analysis of the deciding margin;
  - this section.
