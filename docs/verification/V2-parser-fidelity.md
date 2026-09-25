# V2: release parser fidelity

This record discharges V2, the open marker in R4.1 of
`specs/evidence-linked-theme-extraction.md`, for Stage 1 of
`specs/evidence-linked-theme-extraction-roadmap.md`. The decision is recorded in ADR
0001 (`docs/adr/`).

This is the second measurement. The first, on eight other fixtures, is summarized in
"Round 1 and the replacement fixtures"; its full record is commit `8bda724`.

**Outcome:** selected -- **walker**

The rule selected the walker again, with one finding that the spec leaves to the user
at gate D:

- **The control check flags the fixtures again.** On the three metrics the check uses,
  no parser can beat the control on fixtures like these, for a structural reason (see
  "Control check").

Three facts bear on it:

- **The deciding metric.** The rule separated the walker from edgartools only at the
  fourth metric, header loss, in narrative_only. That margin is the typing of 16 gold
  headings in two releases (see "Selection rule, applied").
- **sec-parser.** It is ineligible because it fails the lock gate, but at header loss it
  sits within the tie margin of the walker.
- **The gold exceptions.** Seven scored gold blocks depart from a spec rule. Setting
  them aside leaves the outcome unchanged.

**Gate D, 2026-09-25.** The user accepted the flag, replaced no fixture, and accepted ADR
0001 (`d760d47`). A final code review followed; its corrections are recorded in this
record, under "Notes on ADR 0001 after acceptance" and "Deviations from the plan".

## Round 1 and the replacement fixtures

**Round 1** ran on 2026-09-24. Its V2 record and the first proposal of ADR 0001 are
commit `8bda724`, with ADR corrections at `2d1db04`. Its outputs are archived in
`data/runs/parser-fidelity/round1/`.

- **Fixtures.**
  - clean HTML: UQM Technologies 2018, AVX 2017;
  - malformed layout: IKON Office Solutions 2005, American Electric Power 2024;
  - table-heavy: Humana 2006, Ruby Tuesday 2005;
  - narrative-only: Establishment Labs 2023, Phillips 66 Partners 2014.
- **Outcome.** The rule selected the walker at the first metric, coverage: 1.000 (n=27,
  narrative_only) against edgartools' 0.939 (n=98, malformed_layout).
- **The margin.** All six blocks edgartools missed were American Electric Power
  footnotes, each anchored with `after` on the bare page number that follows it.
  edgartools drops page numbers. A reading outside the rule set those six aside and
  still selected the walker, at header loss.
- **The flag.** The control check raised "the fixtures cannot discriminate between
  parsers".
- **Independent review.** At the user's request, a read-only reviewer reproduced the
  rule's output and argued that the flag is structural, so replacing the fixtures could
  not clear it.
- **Decision.** At gate D the user chose to replace all eight fixtures. The plan's
  route (Task 21 Step 1) went back to gate A for the replacements (Tasks 6, 7 and 10),
  then ran Task 19 again and redid this record.

Both rounds end at the typing of narrative-release headings: round 1 through its reading
outside the rule, round 2 through the rule itself.

**How the replacements were chosen.** The user decided the scope and the supply. At the
user's request, Claude proposed the method, including the filing years, and the user
chose it.

- **Scope.** All eight fixtures.
- **Supply.** A new live discovery run over filing years 2007, 2010, 2013, 2016, 2019
  and 2022 (`discover.py run --live`, default seed, eight filings per year), pooled with
  the saved round-1 candidates. It sent 208 requests between 00:14:32Z and 00:17:49Z on
  2026-09-25, with no stop.
- **Method.** `discover.suggest()` as written, three picks per class, over every eligible
  candidate, minus the round-1 fixtures, the development set, and every release of those
  eleven issuers (matched on CIK). Each class's first two picks became its fixtures and
  the third its spare.
- **Fixed in advance.** The rule and its tests (`round2_fixtures.py`) were committed at
  `cf2a31a`, before the discovery run.
- **Output.** 168 candidates, a pool of 157. Claude filled in `approval.toml` from the
  rule's output, and the user signed it.
- **One pick rejected before gate B.** The rule's second table-heavy pick, AMC
  Entertainment 2024 (`0001104659-24-081453_ex-99-1`), is not a press release. It is a
  pro forma financial overview filed with a refinancing 8-K, and discovery took it as
  the filing's only EX-99 exhibit. The user rejected it, and the table-heavy spare,
  National Health Investors 2013, replaced it. `approval.toml` records this.
- **A table-heavy fixture that trips a malformed-layout test.** National Health
  Investors trips page-break debris. The spec prefers table-heavy fixtures that trip
  none "where the shortlist allows" (lines 101-104). Once AMC was rejected, no such
  candidate remained in the pool: Southwest Airlines and AMC were its only two.
- **Promotion.** `d6d3356` replaced the eight fixture directories and the manifest.

**How blind the choice was.**

- Five fixtures came from the new discovery run, which no one had seen when the rule was
  fixed: Ball, Becton Dickinson, Southwest Airlines, National Health Investors and Union
  Bankshares.
- Three came from the saved round-1 candidates, which Claude had seen: Southwestern
  Energy, FMC and Pharmacyclics.
- Before the rule was fixed, Claude had named AMC and Pharmacyclics to the user as the
  only unused table-heavy and narrative-only candidates in the saved data that trip no
  malformed-layout test.
- Before any gold, Claude read the opening text of Ball, Becton Dickinson, Union
  Bankshares, AMC and the four spares, to check that each was a press release, and every
  pick's exhibit description, 8-K items and class-test values. No candidate ran.

## Corpus

Eight release exhibits sit in `tests/fixtures/releases/`, two per class, each
committed byte-for-byte as EDGAR served it. Their provenance is in `manifest.toml` and
their source-register basis in `docs/source-register.toml` (`sec-edgar`).

The user approved these fixtures on 2026-09-25 (`approved_on` in
`expirements/parser-fidelity/approval.toml`). The development set is unchanged from
round 1, which the user approved on 2026-09-22.

| `fixture_id` | `primary_class` | issuer | filing date | exhibit | bytes | `data_table_share` | `pre_share` | positioned text | layout-table prose (longest layout cell, words) | page-break debris (styling; bare page-number blocks) | preformatted text | `acquisition_flags` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `0000007332-09-000032_ex-99` | `clean_html` | SOUTHWESTERN ENERGY CO | 2009-10-29 | EX-99 | 213,887 | 0.2805 | 0.0 | no | no (0) | no (no; 0) | no | `alternative_exhibit_numbering` |
| `0000009389-10-000004_ex-99-1` | `malformed_layout` | BALL CORP | 2010-01-28 | EX-99.1 | 477,997 | 0.3036 | 0.0 | no | no (9) | yes (yes; 2) | no | none |
| `0000010795-22-000014_ex-99-1` | `malformed_layout` | BECTON DICKINSON & CO | 2022-02-03 | EX-99.1 | 509,858 | 0.2633 | 0.0 | yes | no (0) | yes (yes; 27) | no | none |
| `0000037785-14-000003_ex-99-1` | `clean_html` | FMC CORP | 2014-02-05 | EX-99.1 | 483,337 | 0.3039 | 0.0 | no | no (25) | no (yes; 0) | no | none |
| `0000092380-07-000011_ex-99-1` | `table_heavy` | SOUTHWEST AIRLINES CO | 2007-04-19 | EX-99.1 | 473,486 | 0.5284 | 0.0 | no | no (11) | no (yes; 0) | no | none |
| `0000706863-16-000110_ex-99-1` | `narrative_only` | UNION BANKSHARES INC | 2016-07-20 | EX-99.1 | 21,130 | 0.0 | 0.0 | no | no (19) | no (yes; 0) | no | `narrative_only_release` |
| `0000877860-13-000100_ex-99-1` | `table_heavy` | NATIONAL HEALTH INVESTORS INC | 2013-11-04 | EX-99.1 | 344,043 | 0.575 | 0.0 | no | no (24) | yes (yes; 4) | no | none |
| `0000949699-08-000023_ex-99-1` | `narrative_only` | PHARMACYCLICS INC | 2008-08-14 | EX-99.1 | 14,007 | 0.0 | 0.1717 | no | no (12) | no (no; 0) | no | `narrative_only_release` |

A malformed-layout test's value is shown with the measurement behind it in
parentheses. Page-break debris fires only when a document has both page-break styling
and at least one bare page-number block.

These class-test values only sort fixtures into classes. They are not quality
thresholds, and R13.1 is untouched.

The last column's field was `stage4_flags` in the manifest as scored (`d6d3356`). At
Stage 1's close it was renamed `acquisition_flags`, when the Stage 1 documents took up
the cohort amendment's numbering, under which acquisition is Stage 5. No score reads
it.

## Gold protocol

- **Annotator and source.**
  - The user was the sole annotator.
  - Under F9, which amends D2 for Stage 1 gold only, Codex drafted all eight fixtures'
    gold from the browser's rendered text. The user verified every block of each draft
    against the rendering.
  - No candidate output was shown or consulted, and every candidate ran on the
    fixtures only after all gold passed the validator.
  - The gold as scored is the eight `gold.toml` files as last committed, at `02e3e3f`.
- **Rendered text.**
  - For each fixture the user selected and copied the whole page in Chrome, then saved
    the clipboard to `data/runs/parser-fidelity/gold-drafts/<id>.rendered.txt` with
    `LANG=en_US.UTF-8 pbpaste`.
  - Each copy's length in the primary matching space equals the class tests' count of
    visible characters, with two exceptions: Ball's copy is 8 characters longer and
    Becton Dickinson's 9. The difference is the alt text of a missing image ("Ball
    Logo", "image.jpg"), which gets no block.
- **Codex.**
  - **The brief.** `expirements/parser-fidelity/codex-gold-brief.md`, unchanged since
    round 1 (`f61e11e`).
  - **The runs.** codex-cli 0.154.0, model gpt-5.6-sol at reasoning effort max (the
    user's Codex configuration), one run per fixture:
    `codex exec -C <repo> -s workspace-write --add-dir ~/.cache/uv -o data/runs/parser-fidelity/gold-drafts/<id>.codex-report.md "<prompt>"`.
    The added directory lets the validator's `uv` write its cache inside the sandbox.
    Network access stayed denied.
  - **Two prompts.**
    - Southwestern Energy, FMC, Ball and Becton Dickinson ran with "Follow
      expirements/parser-fidelity/codex-gold-brief.md exactly. FIXTURE=<id>".
    - Southwestern Energy's report disclosed reads made before the brief, so Claude
      offered a stricter prompt, and the user chose one for each later run.
    - Southwest Airlines, National Health Investors, Union Bankshares and Pharmacyclics
      ran with "Before running any other command, read
      expirements/parser-fidelity/codex-gold-brief.md in full; then follow it exactly.
      FIXTURE=<id>".
  - **What Codex saw.** With the user's approval, Claude read the eight Codex session
    logs afterwards. `data/runs/parser-fidelity/round2-analysis/codex_reads_summary.md`
    summarizes them, and `codex_sessions.md` lists every command. In every run, Codex:
    - read the spec's Gold annotation section, its fixture's rendered text and
      `gold.toml`, and ran the validator;
    - read no candidate code, `walker-rules.md`, candidate output, validator source, or
      other fixture's files;
    - wrote nothing outside its own `gold.toml` and snapshot, and made no network call
      and no git write.
  - **Reads outside the brief's inputs.**
    - The four original-prompt runs listed or read files before the brief.
      Southwestern Energy read the harness README, the root README, the root and
      package `pyproject.toml` files, and the diff of `gold-notes.md` (round 2's
      then-blank sections). Becton Dickinson read the harness README. FMC and Ball
      listed file names, and FMC counted the lines of seven files, among them
      `AGENTS.md`, the spec and the plan.
    - None of the four stricter-prompt runs read anything before the brief.
    - Five runs printed the spec's heading lines. Seven read some of the user's global
      skill files, which lie outside the repository and hold process instructions.
    - Southwestern Energy opened `source.html` twice to resolve a validator message on
      its own anchor, as the brief allows.
    - The reports were incomplete: FMC's, Ball's and Union Bankshares' did not mention
      their skill reads or listings. The logs are the record.
  - **Round 1.** Round 1's statement of what Codex saw rested on the brief alone. No
    round-1 session log was checked.
- **Sign-off.**
  - Codex left the header blank, so a draft failed the validator until the user filled
    it in. Filling it in was the user's sign-off, and the verified file is the gold. Its
    `annotator` reads "Lowell Mason (verified a Codex draft)".
  - The user filled in Becton Dickinson's header while Codex was still drafting, and
    Codex kept it. That snapshot therefore holds the user's header fields; its blocks
    are Codex's.
- **Commits.**
  - The user committed the eight drafts, with the empty `gold-notes.md` sections, at
    `368c2f6`. They differ from the kept snapshots only in header lines, some of which
    the user had already filled in. So `git diff 368c2f6 02e3e3f -- tests/fixtures/releases`
    shows every block edit the user made in verification.
  - The user then committed the verified files in 29 further commits, through
    `02e3e3f`. Claude checked the committed files whenever the user asked (see
    "Claude's part").
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

| fixture | drafted by | draft blocks | gold blocks | unchanged | edited | added | removed |
|---|---|---|---|---|---|---|---|
| `0000007332-09-000032_ex-99` (Southwestern Energy) | Codex, verified by the user | 110 | 110 | 104 | 6 | 0 | 0 |
| `0000009389-10-000004_ex-99-1` (Ball) | Codex, verified by the user | 83 | 82 | 76 | 5 | 1 | 2 |
| `0000010795-22-000014_ex-99-1` (Becton Dickinson) | Codex, verified by the user | 98 | 107 | 86 | 12 | 9 | 0 |
| `0000037785-14-000003_ex-99-1` (FMC) | Codex, verified by the user | 99 | 106 | 84 | 14 | 8 | 1 |
| `0000092380-07-000011_ex-99-1` (Southwest Airlines) | Codex, verified by the user | 43 | 49 | 35 | 8 | 6 | 0 |
| `0000706863-16-000110_ex-99-1` (Union Bankshares) | Codex, verified by the user | 36 | 36 | 33 | 2 | 1 | 1 |
| `0000877860-13-000100_ex-99-1` (National Health Investors) | Codex, verified by the user | 51 | 51 | 43 | 2 | 6 | 6 |
| `0000949699-08-000023_ex-99-1` (Pharmacyclics) | Codex, verified by the user | 37 | 33 | 28 | 3 | 2 | 6 |

- **Claude's part.** Claude, the assistant that executed the plan, wrote the walker,
  the adapters, the harness, the scorer, and this record.
  - **During gate B.** No candidate had run on these fixtures, and Claude showed no
    candidate output. Whenever the user asked, it ran the validator and objective
    checks on the committed files, and reported the problems it found: validator
    errors, text covered twice or not at all, anchors not found, and table cells that
    break the L rules. It proposed no boundary, type or anchor on its own.
  - **At the user's request,** it:
    - gave a table of what the spec implies under five readings of Southwestern
      Energy's company line, with no preference. The user chose page artifacts, the
      reading Codex had drafted;
    - pointed to Codex's own `after` anchor for Ball's b042, which the user kept;
    - supplied FMC t005's L (110.3 / 539.0 / 35.6), the only L in the table that meets
      every rule;
    - listed the options the spec allows, with their consequences and no preference, for
      Ball t005, Becton Dickinson t007 and t012, and National Health Investors b025 and
      b028;
    - wrote the round-2 sections of `gold-notes.md` from the committed gold and the
      gate-B checks. The times in them are the user's.
  - **Before scoring,** it defined the two sensitivity readings in "Selection rule,
    applied".
  - **Fixture choice.** It proposed the method that chose the round-2 fixtures. See "How
    the replacements were chosen" and "How blind the choice was".
- **Gold exceptions.** Seven scored blocks depart from a spec rule. Each is recorded in
  `gold-notes.md` (`808f0e4`), committed before any candidate ran:
  - **Ball t005.** Every cell of its L is split from a `$` cell. No L in the table meets
    every rule.
  - **Becton Dickinson t005.** Its corner and right are split from `$` cells, although
    8 L's without split cells exist.
  - **Becton Dickinson t007.** The same split, and no L in the table meets every rule.
  - **Becton Dickinson t012.** Its three cells are unique but do not form an L: no row
    has two values, so no L shape exists. Every value occurs once, so `unanchorable` is
    not available either. Its `right` cell sits in a later row than its `below` cell.
  - **National Health Investors b025 and b028.** Their anchors include the footnote
    references "(1)(2)", against the rule that no anchor includes a marker.
  - **Southwestern Energy t005.** Its corner and right omit the "$ " that shares their
    cells.
- **Guidelines.**
  - The guidelines, schema, and matching spaces are those of the spec's Gold
    annotation section.
  - They include two policies adopted on 2026-09-23 (`0c97ca3`):
    - an image's alt text gets no block;
    - a table whose values recur, so that no L of three unique cells exists, is marked
      `unanchorable`. It is counted and never scored.
  - 27 blocks are unanchorable:
    - Southwestern Energy: 4 tables;
    - FMC: 2 tables, a heading and a footnote;
    - Becton Dickinson: 7 tables and 6 footnotes;
    - Southwest Airlines: 3 tables;
    - National Health Investors: 3 tables.
- **Encoding check.** The protocol compares the validator's decoding with the
  browser's `document.characterSet`. For all eight fixtures, the validator reports
  UTF-8 (basis: `valid-utf-8`) with every byte ASCII, so any browser encoding agrees.
  The comparison was therefore skipped, as `gold-notes.md` records.
- **Effort.**
  - **Browser.** Google Chrome Version 154.0.8037.58 (Official Build) (arm64), for
    all eight fixtures.
  - **Time spent** verifying a draft (3.75 hours in total; round 1 took 6.75):

    | Fixture | Hours |
    | --- | --- |
    | Southwestern Energy | 0.5 |
    | FMC | 0.5 |
    | Ball | 0.5 |
    | Becton Dickinson | 0.5 |
    | Southwest Airlines | 0.5 |
    | National Health Investors | 0.25 |
    | Union Bankshares | 0.75 |
    | Pharmacyclics | 0.25 |

- **Gate B.** It closed at `808f0e4`. In the final checks, every gold file passed the
  validator with no error, the only text in no block was list and footnote markers, and
  `check_fixtures.py` printed `fixture check passed`.

## Candidates

Common setup:

- **Decoding.** Every candidate received the same decoded text from `pf_decode.py`,
  which follows browser rules. Charset detection is therefore outside this
  measurement; see "Findings for Stage 3".
- **Freeze.** The candidate sources were frozen at commit
  `616721ab6eed46e0b72905e1c94ac93c7f2337db` before any fixture run. `cec29b7` recorded
  the freeze, and `freeze.py verify` passed again before the round-2 runs.

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

- **Lock-gate results.** From `data/runs/parser-fidelity/gates/lock-*.json`, run between
  18:05:34Z and 18:05:53Z on 2026-09-25. Each result is identical to round 1's except
  for `uv`'s timing line, so the PyPI resolution had not drifted.
- **Determinism and network.** From `data/runs/parser-fidelity/fixtures/gates.json`:
  - 64 runs between 18:02:29Z and 18:02:48Z, each candidate twice per fixture in a
    fresh process with default hash randomization;
  - the two dumps were compared byte for byte.
- **Repository.** After the lock gates, `git status --short` printed nothing for the
  whole working tree.

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
`freeze.py verify` passed before each round's fixture runs.

Harness code outside the freeze changed twice afterwards:

- **The V1 probe.** `9fce0b2` added the live-fetch policy's stops to
  `v1_return_types.py` before V1's live run: a persistent 403, a 429, and the request
  cap. `docs/verification/V1-edgartools-return-types.md` describes it.
- **The round-2 fixture rule.** `cf2a31a` added `round2_fixtures.py` and its tests,
  and described them in the harness README.

Neither touches a candidate or the scoring code. Before the round-2 scoring,
`git diff --exit-code 2d1db04` found no change to `score.py`, `select_parser.py`,
`validate_gold.py`, `check_fixtures.py`, the Codex brief or the spec.

## Metrics

Generated by `score.py`, unchanged since `743a486`. Every candidate was scored on its
first dump of each fixture. The runtime column is the harness's `parse_seconds`, which
for three candidates includes importing their library (see "Notes on ADR 0001 after
acceptance").

**The one reversed pair.** Reading-order corruption is 1 of 167 pairs in
malformed_layout for every candidate, the control included. The pair is Becton
Dickinson t012's `right` cell after its `below` cell. The gold's cells for t012 put
`right` in a later row (see "Gold exceptions"), so the pair is not a parser failure.

### Block coverage (higher is better)

| class | edgartools | secparser | walker | control |
|---|---|---|---|---|
| clean_html | 1.000 (168/168) | 1.000 (168/168) | 1.000 (168/168) | 1.000 (168/168) |
| malformed_layout | 1.000 (147/147) | 1.000 (147/147) | 1.000 (147/147) | 1.000 (147/147) |
| narrative_only | 1.000 (65/65) | 1.000 (65/65) | 1.000 (65/65) | 1.000 (65/65) |
| table_heavy | 1.000 (70/70) | 1.000 (70/70) | 1.000 (70/70) | 1.000 (70/70) |

### Footnote merging (lower is better)

| class | edgartools | secparser | walker | control |
|---|---|---|---|---|
| clean_html | 0.000 (0/30) | 0.167 (5/30) | 0.000 (0/30) | 0.000 (0/30) |
| malformed_layout | 0.000 (0/9) | 0.111 (1/9) | 0.000 (0/9) | 0.000 (0/9) |
| narrative_only | n/a (0/0) | n/a (0/0) | n/a (0/0) | n/a (0/0) |
| table_heavy | 1.000 (6/6) | 1.000 (6/6) | 1.000 (6/6) | 0.000 (0/6) |

### Reading-order corruption (lower is better)

| class | edgartools | secparser | walker | control |
|---|---|---|---|---|
| clean_html | 0.000 (0/192) | 0.000 (0/192) | 0.000 (0/192) | 0.000 (0/192) |
| malformed_layout | 0.006 (1/167) | 0.006 (1/167) | 0.006 (1/167) | 0.006 (1/167) |
| narrative_only | 0.000 (0/67) | 0.000 (0/67) | 0.000 (0/67) | 0.000 (0/67) |
| table_heavy | 0.000 (0/78) | 0.000 (0/78) | 0.000 (0/78) | 0.000 (0/78) |

### Header loss (lower is better)

| class | edgartools | secparser | walker | control |
|---|---|---|---|---|
| clean_html | 0.492 (n=141) | 0.292 (n=141) | 0.126 (n=141) | 1.000 (n=141) |
| malformed_layout | 0.500 (n=136) | 0.368 (n=136) | 0.184 (n=136) | 1.000 (n=136) |
| narrative_only | 1.000 (n=28) | 0.812 (n=28) | 0.781 (n=28) | 1.000 (n=28) |
| table_heavy | 0.500 (n=56) | 0.295 (n=56) | 0.341 (n=56) | 1.000 (n=56) |

### Diagnostics by class

#### clean_html

| candidate | altered | split | other merges | duplication | footnotes in tables | cell association | unanchorable |
|---|---|---|---|---|---|---|---|
| edgartools | 0 | 11/155 | 18/138 | 1/298 | 0/30 | 24/39 | 8 |
| secparser | 28 | 8/155 | 109/138 | 1/298 | 0/30 | no cells exposed | 8 |
| walker | 0 | 11/155 | 18/138 | 0/298 | 0/30 | 24/39 | 8 |
| control | 0 | 78/155 | 0/138 | 1/298 | 0/30 | no cells exposed | 8 |

#### malformed_layout

| candidate | altered | split | other merges | duplication | footnotes in tables | cell association | unanchorable |
|---|---|---|---|---|---|---|---|
| edgartools | 0 | 10/136 | 12/138 | 0/249 | 0/9 | 18/33 | 13 |
| secparser | 0 | 9/136 | 98/138 | 0/249 | 0/9 | no cells exposed | 13 |
| walker | 0 | 10/136 | 9/138 | 0/249 | 0/9 | 33/33 | 13 |
| control | 0 | 94/136 | 0/138 | 0/249 | 0/9 | no cells exposed | 13 |

#### narrative_only

| candidate | altered | split | other merges | duplication | footnotes in tables | cell association | unanchorable |
|---|---|---|---|---|---|---|---|
| edgartools | 0 | 1/63 | 33/65 | 0/115 | 0/0 | 0/0 | 0 |
| secparser | 0 | 1/63 | 56/65 | 0/115 | 0/0 | no cells exposed | 0 |
| walker | 0 | 3/63 | 2/65 | 0/115 | 0/0 | no cells exposed | 0 |
| control | 0 | 26/63 | 0/65 | 0/115 | 0/0 | no cells exposed | 0 |

#### table_heavy

| candidate | altered | split | other merges | duplication | footnotes in tables | cell association | unanchorable |
|---|---|---|---|---|---|---|---|
| edgartools | 0 | 1/65 | 14/64 | 2/121 | 6/6 | 0/15 | 6 |
| secparser | 0 | 1/65 | 43/64 | 0/121 | 6/6 | no cells exposed | 6 |
| walker | 0 | 1/65 | 14/64 | 0/121 | 6/6 | 15/15 | 6 |
| control | 0 | 48/65 | 0/64 | 0/121 | 0/6 | no cells exposed | 6 |

### Per-fixture detail

#### `0000007332-09-000032_ex-99` (clean_html)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 83/83 | 0/9 | 0/98 | 13/13 | 2/75 | 1.1676 | - |
| secparser | 83/83 | 5/9 | 0/98 | 11/13 | 2/75 | 0.852 | b003:start, b009:end, b009:start, b011:start, b013:end, b014:start, b016:start, b017:end, b018:end, b019:start, b020:end, b020:start, b026:start, b027:start, b029:end, b030:start, b031:start, b035:end, b035:start, b036:start, b037:end, b037:start, b039:start, b040:start, b041:start, b044:end, b055:end, b072:end |
| walker | 83/83 | 0/9 | 0/98 | 6/13 | 2/75 | 0.0204 | - |
| control | 83/83 | 0/9 | 0/98 | 13/13 | 75/75 | 0.0599 | - |

#### `0000009389-10-000004_ex-99-1` (malformed_layout)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 64/64 | 0/0 | 0/73 | 19/19 | 0/53 | 0.4408 | - |
| secparser | 64/64 | 0/0 | 0/73 | 19/19 | 0/53 | 0.2692 | - |
| walker | 64/64 | 0/0 | 0/73 | 5/19 | 0/53 | 0.026 | - |
| control | 64/64 | 0/0 | 0/73 | 19/19 | 53/53 | 0.0422 | - |

#### `0000010795-22-000014_ex-99-1` (malformed_layout)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 83/83 | 0/9 | 1/94 | 19/19 | 0/45 | 0.4601 | - |
| secparser | 83/83 | 1/9 | 1/94 | 9/19 | 0/45 | 0.2652 | - |
| walker | 83/83 | 0/9 | 1/94 | 9/19 | 0/45 | 0.031 | - |
| control | 83/83 | 0/9 | 1/94 | 19/19 | 45/45 | 0.0366 | - |

#### `0000037785-14-000003_ex-99-1` (clean_html)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 85/85 | 0/21 | 0/94 | 16/17 | 0/36 | 0.4561 | - |
| secparser | 85/85 | 0/21 | 0/94 | 6/17 | 0/36 | 0.2674 | - |
| walker | 85/85 | 0/21 | 0/94 | 1/17 | 0/36 | 0.0292 | - |
| control | 85/85 | 0/21 | 0/94 | 17/17 | 36/36 | 0.0365 | - |

#### `0000092380-07-000011_ex-99-1` (table_heavy)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 36/36 | 2/2 | 0/41 | 10/10 | 0/15 | 0.4424 | - |
| secparser | 36/36 | 2/2 | 0/41 | 9/10 | 0/15 | 0.2615 | - |
| walker | 36/36 | 2/2 | 0/41 | 9/10 | 0/15 | 0.0258 | - |
| control | 36/36 | 0/2 | 0/41 | 10/10 | 15/15 | 0.0428 | - |

#### `0000706863-16-000110_ex-99-1` (narrative_only)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 35/35 | 0/0 | 0/34 | 6/6 | 0/0 | 0.3829 | - |
| secparser | 35/35 | 0/0 | 0/34 | 1/6 | 0/0 | 0.2006 | - |
| walker | 35/35 | 0/0 | 0/34 | 1/6 | 0/0 | 0.0013 | - |
| control | 35/35 | 0/0 | 0/34 | 6/6 | 0/0 | 0.0132 | - |

#### `0000877860-13-000100_ex-99-1` (table_heavy)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 34/34 | 4/4 | 0/37 | 12/12 | 0/19 | 0.4253 | - |
| secparser | 34/34 | 4/4 | 0/37 | 4/12 | 0/19 | 0.2482 | - |
| walker | 34/34 | 4/4 | 0/37 | 6/12 | 0/19 | 0.0226 | - |
| control | 34/34 | 0/4 | 0/37 | 12/12 | 19/19 | 0.033 | - |

#### `0000949699-08-000023_ex-99-1` (narrative_only)

| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |
|---|---|---|---|---|---|---|---|
| edgartools | 30/30 | 0/0 | 0/33 | 10/10 | 12/12 | 0.3938 | - |
| secparser | 30/30 | 0/0 | 0/33 | 9/10 | 12/12 | 0.1935 | - |
| walker | 30/30 | 0/0 | 0/33 | 8/10 | 12/12 | 0.0008 | - |
| control | 30/30 | 0/0 | 0/33 | 10/10 | 12/12 | 0.0132 | - |

## Selection rule, applied

Generated by `select_parser.py`:

1. eligibility: {'edgartools': {'lock': True, 'determinism': True, 'network': True}, 'secparser': {'lock': False, 'determinism': True, 'network': True}, 'walker': {'lock': True, 'determinism': True, 'network': True}}; eligible: ['edgartools', 'walker']
2. coverage: edgartools=1.000 (n=65, worst class narrative_only), walker=1.000 (n=65, worst class narrative_only); best 1.000; within 1/n of best: edgartools, walker
3. footnote_merging: edgartools=1.000 (n=6, worst class table_heavy), walker=1.000 (n=6, worst class table_heavy); best 1.000; within 1/n of best: edgartools, walker
4. reading_order: edgartools=0.006 (n=167, worst class malformed_layout), walker=0.006 (n=167, worst class malformed_layout); best 0.006; within 1/n of best: edgartools, walker
5. header_loss: edgartools=1.000 (n=28, worst class narrative_only), walker=0.781 (n=28, worst class narrative_only); best 0.781; within 1/n of best: walker

**Outcome:** selected -- **walker**
**secparser is ineligible but would have survived step 3.** Worst-class values:
- coverage: secparser 1.000 (n=65, narrative_only) vs walker 1.000 (n=65, narrative_only)
- footnote_merging: secparser 1.000 (n=6, table_heavy) vs walker 1.000 (n=6, table_heavy)
- reading_order: secparser 0.006 (n=167, malformed_layout) vs walker 0.006 (n=167, malformed_layout)
- header_loss: secparser 0.812 (n=28, narrative_only) vs walker 0.781 (n=28, narrative_only)
**Control check:** beats the control by more than the tie margin in: {'clean_html': False, 'malformed_layout': False, 'narrative_only': False, 'table_heavy': False}
**Flag:** the fixtures cannot discriminate between parsers; the user decides whether to replace any.

**When the rule was fixed.**

- The rule was fixed at commit `8c7331a`, before any fixture was scored.
- Two later commits changed the rule's code, both before round 1's scoring:
  - `9a75074`, the user's decision that tied worst classes use the smallest
    denominator;
  - `e4bac05`, which makes the lock gate refuse to run until the freeze and the gold
    are ready.
- Neither the rule nor the scorer changed between the rounds (see "Post-freeze
  changes").
- The code before `9a75074` would give the same outcome. The only tie between worst
  classes is at coverage, where every candidate scores 1.000 in every class.

**The sec-parser line.** sec-parser is ineligible, but it would have survived the
priority comparison: its worst header loss, 0.812 (n=28, narrative_only), is within 1/28
of the walker's 0.781. The rule's first tie-break is the dependency footprint. A replay
outside the rule with the tie-breaks applied keeps the walker, which adds no runtime
dependency; sec-parser adds 23, pandas among them.

**What decided it.**

- **Three ties.**
  - Coverage is 1.000 for every candidate in every class.
  - Footnote merging's worst class is table_heavy, where all three parsers merge all
    6 footnotes.
  - Reading order's worst class is malformed_layout, where every candidate has the one
    reversed pair that the gold produces.
- **Header loss.** A class's header loss is the mean of two rates: the share of gold
  headings lost, and the share of table header texts lost. Its n counts both. In
  narrative_only:

  | Candidate | Headings lost | Table header texts lost | Header loss |
  | --- | --- | --- | --- |
  | walker | 9 of 16 | 12 of 12 | 0.781 |
  | sec-parser | 10 of 16 | 12 of 12 | 0.812 |
  | edgartools | 16 of 16 | 12 of 12 | 1.000 |
  | control | 16 of 16 | 12 of 12 | 1.000 |

  - The table half is the same for every candidate. Pharmacyclics' two tables are drawn
    with spaces inside `<pre>`, and no candidate exposes them as tables.
  - So the whole margin between the walker and edgartools, 0.219 against a tie margin of
    1/28 (0.036), is the typing of 16 gold headings in two releases.
- **Union Bankshares.** edgartools types all six headings as paragraphs. The walker and
  sec-parser each lose one, the "Exhibit 99.1" label (b002), typed as a paragraph.
- **Pharmacyclics.**
  - edgartools emits the release as 14 elements. One `other` element of 10,837
    characters holds all 30 scored blocks, the ten headings among them.
  - The walker types seven headings as paragraphs. It types one, "- Company to Host
    Conference Call at 4:30 p.m. EST Today -" (b007), as a list item.
  - sec-parser puts nine headings in paragraph elements that it shares with other
    blocks.
- **What header loss does not count.** It penalizes gold headings a parser fails to
  type as headings. It does not penalize body text a parser types as a heading. An
  in-memory check outside the scorer compared each gold paragraph, footnote and list
  item a parser found with the element that holds its start:

  | Parser | Body blocks typed as headings, round 2 | Round 1 |
  | --- | --- | --- |
  | walker | 12 of 313 | 3 of 210 |
  | sec-parser | 7 of 313 | 6 of 206 |
  | edgartools | 0 of 313 | 0 of 204 |

  The walker's twelve are:
  - Southwestern Energy's contact names, titles and telephone numbers (b058-b064);
  - FMC's footnote labels "Three Months Ended December 31, 2012:", "Twelve Months Ended
    December 31, 2013:" and "Twelve Months Ended December 31, 2012:" (b067, b069,
    b071);
  - Becton Dickinson's "Exhibit 99.1" (b001);
  - Union Bankshares' "For Immediate Release" (b003).

  The rule rewards typing headings and ignores over-typing them. The walker leads on the
  first and trails on the second.

**Sensitivity readings (outside the rule).**

- **Status.**
  - Neither reading is part of the fixed rule. Both were computed in memory by
    `data/runs/parser-fidelity/round2-analysis/outside_rule.py`, and `scores.json` and
    `selection.md` are unchanged.
  - The page-artifact rule was defined after the candidate runs ended (18:02:48Z) and
    before scoring began (18:06:08Z). Its saved list carries its generation time
    (18:04:57Z) and a hash.
  - The exceptions reading sets aside the exceptions committed in `gold-notes.md` at
    `808f0e4`, before any candidate ran. Claude recorded the reading in its own notes
    before scoring began. The script that computes it, `outside_rule.py`, was written
    after scoring (18:08Z).
  - Nothing about either reading was committed before scoring, so their timing rests on
    Claude's own records.
- **Page-artifact anchors.**
  - Round 1's reading set aside the six footnotes whose `after` ran into a page number.
    The general rule, in `round2-analysis/artifact_anchors.py`, sets aside every scored
    block whose `after` runs into a `page_artifact` in reading order.
  - Applied to round 1's gold, the rule gives exactly those six footnotes. Applied to
    round 2's, it gives none, so this reading is the rule's own.
  - A first version listed every anchor that overlaps any occurrence of an artifact's
    text. On round 1's gold, where page numbers are bare digits, it flagged 41 American
    Electric Power strings, most of them only because they contain a digit. It was
    replaced before scoring.
  - The list also names, without setting them aside, three National Health Investors
    blocks whose own text also occurs elsewhere as a page artifact's text: b001, b004
    and b006.
- **Gold exceptions.** The seven exceptions in "Gold protocol" are set aside as if
  unanchorable.
  - The walker is still selected at header loss, with the same values: 1.000 against
    0.781 (n=28).
  - Footnote merging falls to 0.333 (2 of 6) for all three parsers. National Health
    Investors' four footnotes no longer share their elements with a scored block,
    because b025 and b028 are set aside.
  - Reading order falls to 0.000.
  - sec-parser again stays within the margin at header loss and loses the dependency
    tie-break.
  - The control check still fails in every class.

## Control check

**Control check:** beats the control by more than the tie margin in: {'clean_html': False, 'malformed_layout': False, 'narrative_only': False, 'table_heavy': False}

- **clean_html.** The walker and the control both find 168 of 168 blocks, merge 0 of
  30 footnotes, and reverse 0 of 192 pairs.
- **malformed_layout.** Both find 147 of 147 blocks, merge 0 of 9 footnotes, and
  reverse 1 of 167 pairs, the gold's pair in Becton Dickinson t012.
- **narrative_only.** Both find 65 of 65 blocks and reverse 0 of 67 pairs. The class
  has no footnotes.
- **table_heavy.** Both find 70 of 70 blocks and reverse 0 of 78 pairs. On footnote
  merging the control leads: the walker merges all 6 footnotes, which the page sets
  inside data tables, and the control merges none.

Why the control cannot be beaten on these three metrics:

- **Its elements are lines.** The control emits every line of `get_text` output as its
  own element, in document order, and anchors are matched with whitespace removed.
- **Coverage.** It found every block on every fixture, in both rounds. A parser could
  beat it only where the control's text differs from the page's, for example hidden
  text inside an anchored run.
- **Footnote merging.** A control element holds one line, so a footnote merges only if
  it shares a line with body text. None did, in either round.
- **Reading order.** Every candidate walks document order, so none can reverse fewer
  pairs than the control.

Round 1's independent review made this argument before the fixtures were replaced, and
round 2 bears it out on eight new fixtures. On fixtures like these, the check's three
metrics cannot separate any parser from the control. The spec excludes header loss, the
metric that does separate them, because the control has no element types.

The spec gives the next step to the user. At gate D on 2026-09-25 the user accepted the
flag and replaced no fixture.

## Residual failures (for Stage 3)

The walker's residual lists, from `data/runs/parser-fidelity/scores/scores.json`:

| fixture | missed | split | merged | misordered | header lost |
|---|---|---|---|---|---|
| `0000007332-09-000032_ex-99` (Southwestern Energy) | none | b002, b015, b028, b065 | b067, b069, b070, b073, b074, t008, t009, t010, t011, t012 | none | b066, b067, b069, b070, b073, b074; header texts: t012 2 of 10 |
| `0000009389-10-000004_ex-99-1` (Ball) | none | none | b003, b004, b005, b038, b039, b040, t001, t002, t003 | none | b038, b039, b040, b043, b052 |
| `0000010795-22-000014_ex-99-1` (Becton Dickinson) | none | b002, b063, b064, b065, b066, b067, b068, b069, b070, b077 | none | t012:right>t012:below | b063, b064, b065, b066, b067, b068, b069, b070, b077 |
| `0000037785-14-000003_ex-99-1` (FMC) | none | b056, b057, b062, b076, b079, b088, b089 | b003, b004, b005, b006, b007, b008, b009, b010 | none | b011 |
| `0000092380-07-000011_ex-99-1` (Southwest Airlines) | none | b003 | b024, b025, b026, b027, b028, b029, b030, b033, b034, t001, t003, t004 | none | b005, b018, b024, b025, b026, b029, b030, b031, b032 |
| `0000706863-16-000110_ex-99-1` (Union Bankshares) | none | b006 | none | none | b002 |
| `0000877860-13-000100_ex-99-1` (National Health Investors) | none | none | b026, b027, b029, b030, b031, b032, t004, t005 | none | b004, b005, b025, b028, b031, b032 |
| `0000949699-08-000023_ex-99-1` (Pharmacyclics) | none | b029, b033 | b004, b005 | none | b002, b006, b007, b012, b015, b023, b025, b033; header texts: t001 8 of 8, t002 4 of 4 |

- **Merged** joins two groups:
  - footnotes that share an element with body text;
  - text blocks and tables that share an element with another block.
- **Header lost** joins two groups:
  - headings whose element is not a heading, or is shared;
  - table header texts absent from the table's elements.
- **Misordered.** The one pair, in Becton Dickinson t012, comes from the gold (see
  "Metrics"). Every candidate has it.

The walker loses 45 headings in all:

- 23 fall through W8-W11 and are typed `paragraph` (W12).
- 19 sit inside table elements, 18 of them in an element shared with other blocks:
  - Southwestern Energy b067, b069, b070, b073 and b074;
  - Ball b038, b039 and b040;
  - Southwest Airlines b024, b025, b026, b029, b030, b031 and b032 (b031 alone in its
    element);
  - National Health Investors b025, b028, b031 and b032.
- 2 are typed `other`: Ball's year subheadings "2009" and "2008" (b043, b052) match
  W8's bare page-number pattern, which allows up to four digits.
- 1 is typed `list_item`: Pharmacyclics' b007 begins with a hyphen and a space (W9).

It also loses 14 table header texts: 2 of Southwestern Energy t012's 10, and all 12 of
Pharmacyclics' two `<pre>` tables.

**Altered anchors: none.** Every anchor the walker matched, it matched in the primary
space. Stage 3's R3.5 check therefore inherits no altered anchor from the walker.
sec-parser is the only candidate with altered anchors: 28, all on Southwestern Energy.

## Element types and nesting observed in the gold (for Stage 2)

From the gold structure in `scores.json`. A footnote's placement is the type of the
nearest block before it that is neither a footnote nor a `page_artifact`.

| fixture | block types | heading levels | list-item levels | footnotes, by the nearest block before them |
|---|---|---|---|---|
| `0000007332-09-000032_ex-99` (Southwestern Energy) | footnote: 9, heading: 13, list_item: 4, page_artifact: 23, paragraph: 49, table: 12 | 1: 1, 2: 11, no level: 1 | 1: 4 | after table: 9 |
| `0000009389-10-000004_ex-99-1` (Ball) | heading: 19, list_item: 3, page_artifact: 18, paragraph: 37, table: 5 | 1: 9, 2: 10 | 1: 3 | none |
| `0000010795-22-000014_ex-99-1` (Becton Dickinson) | footnote: 15, heading: 19, list_item: 27, page_artifact: 11, paragraph: 22, table: 13 | 1: 1, 2: 17, no level: 1 | 1: 27 | after paragraph: 6, after table: 9 |
| `0000037785-14-000003_ex-99-1` (FMC) | footnote: 22, heading: 18, list_item: 14, page_artifact: 17, paragraph: 28, table: 7 | 1: 1, 2: 12, 3: 4, no level: 1 | 1: 14 | after table: 22 |
| `0000092380-07-000011_ex-99-1` (Southwest Airlines) | footnote: 2, heading: 10, list_item: 4, page_artifact: 10, paragraph: 17, table: 6 | 1: 1, 2: 8, no level: 1 | 1: 4 | after table: 2 |
| `0000706863-16-000110_ex-99-1` (Union Bankshares) | heading: 6, list_item: 15, page_artifact: 1, paragraph: 14 | 1: 1, 2: 4, no level: 1 | 1: 15 | none |
| `0000877860-13-000100_ex-99-1` (National Health Investors) | footnote: 4, heading: 12, list_item: 3, page_artifact: 14, paragraph: 13, table: 5 | 1: 1, 2: 10, no level: 1 | 1: 3 | after table: 4 |
| `0000949699-08-000023_ex-99-1` (Pharmacyclics) | heading: 10, list_item: 7, page_artifact: 3, paragraph: 11, table: 2 | 1: 1, 2: 1, no level: 8 | 1: 7 | none |

From `gold-notes.md`:

- **Nested tables.** No fixture has a table inside a list or inside another table.
- **Layout tables.** Union Bankshares has no data tables. Its HTML tables lay out its
  bullet lists and three paragraphs, which are marked as list items and paragraphs.
  Pharmacyclics' only HTML table is a layout table holding the contacts.
- **Tables drawn in `<pre>`.** Pharmacyclics' two data tables are drawn with spaces
  inside `<pre>`. Their headers and L come from text lines, so P7's grid checks cannot
  apply to them.
- **Statement titles.** In Southwestern Energy, FMC, Becton Dickinson, Southwest
  Airlines and National Health Investors, the titles above the financial tables are
  level-2 headings. Becton Dickinson's sit outside the HTML tables, and period lines
  drawn inside a grid stay table headers.
- **Running headers and footers.** Southwestern Energy's company line on each
  financial-summary page, the running headers of Ball, FMC and National Health
  Investors, and National Health Investors' date line on pages 3-6 are
  `page_artifact`s.

## Findings for Stage 3

- **edgartools' press-release decoding.** edgartools' own press-release path,
  `PressRelease.html()` in `edgar/company_reports/press_release.py`, decodes exhibit
  bytes as UTF-8 with `errors="replace"`. A windows-1252 exhibit would lose characters
  on that path. Stage 3's canonicalizer should decode before it parses.
- **Encoding coverage.** All sixteen fixtures of both rounds and all three development
  releases are pure ASCII. The shared browser-rules decoding (`pf_decode.py`) was never
  exercised on a non-ASCII byte.
- **Tables drawn in `<pre>`.** In neither round did any candidate expose a `<pre>`
  table as a table: IKON's seven in round 1, Pharmacyclics' two here. Every candidate
  loses all of their header texts. The walker emits them as text blocks split at blank
  lines (W5). Stage 3 must either rebuild such tables or record them as a limitation.
- **Titles, contacts, notes and footnotes set in data tables.** A table that passes
  the data-table test (W14) becomes one element with its grid. Text the page sets
  inside it therefore merges with the table, and headings there count as lost:
  - statement titles: Southwestern Energy b067, b069, b070, b073 and b074 (with
    t008-t012), Ball b038-b040 (with t001-t003), Southwest Airlines b024, b025, b029,
    b030 and b032, and National Health Investors b025, b028, b031 and b032;
  - letterhead and contact blocks: Ball b003-b005 and FMC b003-b010, as with American
    Electric Power's and UQM's contacts in round 1;
  - Southwest Airlines' note on non-GAAP measures, a heading and two paragraphs
    (b026-b028), in one element with the b025 title;
  - footnotes: Southwest Airlines b033 and b034, and National Health Investors b026,
    b027, b029 and b030. Every parser merges these six into table elements that also
    hold body text. The control merges none.
- **Year headings.** W8's bare page-number pattern allows up to four digits, so the
  walker types Ball's subheadings "2009" and "2008" as `other`, like page numbers.
- **Styled headings.** W11 types a heading only when every character is bold or
  underlined and it has at most 12 words. 23 gold headings that the walker found are
  typed `paragraph`.
- **Body text typed as headings.** The walker types 12 of the 313 body blocks it found
  as headings, among them contact lines and footnote labels (see "Selection rule,
  applied").
- **From the final code review.** The review found these in frozen code, so they stay
  as they are here, and Stage 3 inherits them:
  - W11 sees bold only in `b`, `strong` and an inline `font-weight`
    (`walker.py:100-111`). It misses the `font` shorthand, stylesheet classes and the
    default bold of `th`. Some of the 23 headings typed `paragraph` may come from this.
  - Hidden content is detected only from hidden tags and an inline `display: none`
    (`pf_classes.py:72-78`).
  - `walker.parse` raises the interpreter's recursion limit, a global setting
    (`walker.py:388-390`). An iterative walk would avoid it.
  - `tfoot` rows are read in source order (`pf_classes.own_rows`).
  - For an encoding label outside its short list, `pf_decode.py:123-129` falls back on
    Python's `codecs.lookup`, not the WHATWG label table. No fixture exercised it: every
    byte is ASCII.
  - The class tests' count of bare page-number blocks counts a nested block and its
    parent twice (`pf_classes.py:211-217`). It is a diagnostic, not a gate.
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

## Finding for Stage 5

- **Exhibit choice.** Discovery's `pick_press_release` takes a filing's only EX-99
  exhibit as its press release. In round 2 it took AMC Entertainment's pro forma
  financial overview, filed with a refinancing 8-K. Stage 5's acquisition should
  confirm that an exhibit is a press release, not rely on its being the filing's only
  EX-99.

## Notes on ADR 0001 after acceptance

The final code review ran after the user accepted ADR 0001. The ADR is immutable except
for its status line, so this record qualifies three of its statements instead. None
changes the decision.

- **"Fast."** The ADR compares the walker's at most 0.031 s per fixture with edgartools'
  0.38-1.17 s. Those are the harness's `parse_seconds`, and they measure different
  things:
  - edgartools, sec-parser and the control import their library inside `parse()`,
    after the network guard, so their timer includes the import;
  - the walker imports lxml when its module loads, before the timer starts.

  The gap is therefore overstated by the libraries' import time, which was not
  measured. Plan P16 defines runtime without imports (see "Deviations from the plan").
  Runtime is neither ranked nor a tie-break, so the selection is unaffected. Stage 3
  should time candidates without imports before relying on any speed claim.
- **"No new dependency."** The ADR says the walker's "imports, lxml and beautifulsoup4,"
  are already declared in `earnings-ingestion`. Both are declared there, but the walker
  imports only lxml; beautifulsoup4 is listed in its script header and never imported.
  The conclusion holds.
- **"Gate D."** The ADR's gate-D bullet reads as pending. The decision is recorded under
  the outcome above.

## Limitations

- **Sample.** Each round had eight fixtures and one annotator, who verified Codex
  drafts (F9) and in round 1 marked one fixture by hand. Agreement is therefore not
  measurable (D2).
- **Rendering.** The gold was marked, and Codex's drafts were checked, from a browser
  rendering.
- **Coverage.** Coverage checks each block's first and last words, not its middle.
- **Text fidelity** is not measured here. R3.5 belongs to Stage 3.
- **Interpreter.** sec-parser ran on Python 3.13.8, not 3.14.
- **Control.** The control is the spec's literal `get_text` call, so it also emits
  the document `<title>`.
- **The control check** cannot be passed on these fixtures, in either round. See
  "Control check".
- **The deciding margin** is the typing of 16 gold headings in two narrative releases.
  See "Selection rule, applied".
- **Body text typed as headings goes uncounted** by header loss. See "Selection rule,
  applied".
- **Gold exceptions.** Seven scored blocks depart from a spec rule. Setting them aside
  leaves the outcome unchanged.
- **Fixture choice.** Only five of the eight fixtures were chosen blind. See "Round 1
  and the replacement fixtures".
- **Authorship.** Claude wrote the walker, the other adapters, the harness and the
  scorer. It also proposed the round-2 fixture method, answered the user's gold
  questions listed in "Gold protocol", and defined the sensitivity readings. The user
  approved the walker's rules, the fixtures, the selection rule and every gold block.
- **Unanchorable blocks.** 27 blocks are unanchorable, so they are never scored.
- **Exact ties.** The rule compares floating-point rates. At a difference of exactly
  1/n, rounding can break a tie the spec defines (in floating point, 0.8 - 0.7 is more
  than 0.1), and the control check can count a spurious win. No difference in either
  round sits at exactly 1/n: round 2's are 0.219 and 0.031 against 1/28, round 1's 0.061
  against 1/27. So no number or outcome changes. A reused rule should compare exactly.

## Deviations from the plan

Round 1:

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

Round 2:

- **The replacement rule.** The plan's gate A has the user pick fixtures from a
  shortlist. In round 2 a rule chose them instead: Claude proposed it and the user
  chose it. With the user's consent, the rule and its discovery command were committed
  (`cf2a31a`) before the live run.
- **`approval.toml`.** With the user's consent, Claude filled it in from the rule's
  output, and the user signed it.
- **AMC.** The user replaced it with the table-heavy spare before gate B.
- **Gold commits.** The user committed the drafts and the verified gold files
  (`368c2f6` and 29 further commits, through `02e3e3f`), instead of one commit per
  validated fixture with its notes. `gold-notes.md` was committed once, at `808f0e4`,
  which closed gate B.

Harness, in both rounds (found by the final code review):

- **Runtime (P16).** P16 defines runtime as parse time without imports. The plan's own
  adapter code imports each library inside `parse()`, after the network guard, where the
  harness's timer runs. The timer therefore includes the import for edgartools,
  sec-parser and the control, and not for the walker.
- **Guard before import.** The spec installs the network guard before the candidate is
  imported. The walker imports lxml when its module loads, before the guard. Its parsing
  runs under the guard, and importing lxml under the guard trips nothing
  (`data/runs/parser-fidelity/evidence/walker-import-guard.txt`).
- **The lock gate's environment.** `lock_gate.parse_fixtures` passes the whole
  environment, including `EDGAR_IDENTITY`, to the adapters, unlike the candidate runner
  (`f2a644e`). Adapter output is not logged there, and no file holds the identity.

V1:

- **Not re-run for round 2.** V1 ran on 2026-09-24 against round 1's fixture filings
  (the manifest at `6021323`), and was not re-run against round 2's. The spec runs V1
  against the fixture filings. Its conclusions about edgartools 5.58.0's return types
  are judged to carry over, because they describe the library's paths rather than the
  filings. Its filing-specific observations, such as the four filings where
  `EightK.earnings` is `None`, are round 1's.

Template changes. This record adds to the plan's V2 template:

- the gate-D notes under the outcome;
- "Round 1 and the replacement fixtures" and "Finding for Stage 5";
- F9's protocol, the Codex session-log audit, and the per-fixture count of blocks
  changed, which the spec's Records section requires;
- Claude's part in the gold, the gold exceptions, and the walker's development
  history;
- the changes before the freeze;
- the analysis of the deciding metric and the sensitivity readings;
- the gate-D decision and "Notes on ADR 0001 after acceptance";
- this section.
