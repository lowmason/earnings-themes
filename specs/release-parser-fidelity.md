# Release parser fidelity

> For agentic workers: REQUIRED NEXT SKILL: writing-plans. This is the stage
> spec for Stage 1 of `specs/evidence-linked-theme-extraction-roadmap.md`.

Stage 1 is an investigation. It measures which HTML parser yields faithful typed
structural elements on real earnings releases, records what the pinned
acquisition library returns, and leaves behind a fixture corpus that later stages
test against. It discharges two open markers in
`specs/evidence-linked-theme-extraction.md`: R4.1's parser choice (via V2) and
R14.5's return types (via V1). Live fetches obey R1.3; fixtures obey A §242 and
A §425. Locators follow that spec: `A §n` is `AGENTS.md`, `Rn`/`Vn` are the
spec's requirements and verifications, and `D1`–`D3` are the roadmap's decisions.

The stage ships no package code. Stage 3 builds the canonicalizer on the parser
selected here.

Designed 2026-09-22 in a brainstorming session, from `main` at `c893b93`.

## Decisions

Taken with the user on 2026-09-22.

| ID | Decision |
| --- | --- |
| F1 | Fixtures are full release exhibits, committed byte-for-byte to the public repository, each at most 1 MiB. The source register quotes the SEC's stated reuse policy with its URL and check date, and states that the policy does not address issuers' copyright. It draws no legal conclusion. |
| F2 | The candidates are edgartools 5.58.0's HTML document parser, a bespoke lxml walker, and sec-parser run in isolation. A naive `get_text()` negative control always runs. `unstructured` was considered and dropped because of its heavy footprint and unlikely adoption. |
| F3 | Two fixtures per class, eight in total. |
| F4 | Fixtures are shortlisted by class criteria; the user approves the eight before any is committed. |
| F5 | Gold structure is recorded as text anchors marked from the browser rendering. Two alternatives were rejected. Full-text gold with sequence alignment costs 3–5× the marking and adds tunable alignment noise. DOM-node gold breaks down on malformed layouts and favors the DOM-based walker. |
| F6 | The selection rule is fixed before any measurement. Each candidate is judged on its worst class, and metrics are compared in priority order: coverage, footnote merging, reading order, header loss. Values within 1/n count as tied. Remaining ties break on dependency footprint, then license, then maintenance. |
| F7 | Three eligibility gates apply before ranking. A candidate must install into the workspace lock on Python 3.14 without a downgrade, produce deterministic output, and use no network while parsing. |
| F8 | The decision is recorded as an ADR under `docs/adr/`, because A §153 places decision records in `docs/`. Measurements go under `docs/verification/`. The harness lives in `expirements/parser-fidelity/`, the repository's existing (misspelled) experiments directory. |
| F9 | Taken 2026-09-23; amends D2 for Stage 1 gold only. Codex drafts each fixture's gold from the browser's rendering, in Chrome, under `expirements/parser-fidelity/codex-gold-brief.md`, and the user verifies every block against the rendering: boundaries, types, levels, order, anchors, and table cells. Codex leaves the header blank, so a draft fails the validator until the user fills it in; that is the sign-off. The verified file is the gold. Its `annotator` reads "Lowell Mason (verified a Codex draft)", and `marked_from` stays "browser rendering", the source of both the draft and the check. Codex sees only the Gold annotation section, the validator, and the rendering (screenshots and the page's rendered text), never the page's HTML structure or a candidate's code, rules, or output. Each draft is kept, uncommitted, so V2 can report how many blocks verification changed. D2 still governs Stages 6 and 11. |

## Scope

In scope: the fixture corpus, the gold annotations, the source register, the
investigation harness, V1, V2, and the parser ADR.

Out of scope:
- pytest configuration and the `live` marker (Stage 2).
- Anything under `packages/`.
- The canonicalizer, sentence splitting, boilerplate masks, and R3.5 text
  fidelity (Stage 3).
- Any change to `uv.lock`: candidates run in environments pinned by their own
  script locks.

Nothing under `expirements/` is imported by a package.

## Deliverables

| Path | Content |
| --- | --- |
| `tests/fixtures/releases/<fixture_id>/source.html` | Eight release exhibits, byte-for-byte as EDGAR served them |
| `tests/fixtures/releases/<fixture_id>/gold.toml` | The user's hand-marked structure |
| `tests/fixtures/releases/manifest.toml` | Provenance for each fixture |
| `.gitattributes` | `tests/fixtures/releases/*/source.html -text`, so Git never rewrites line endings and each sha256 stays valid |
| `docs/source-register.toml` | The A §242 source register; first entry `sec-edgar` |
| `expirements/parser-fidelity/` | Fetcher, discovery, class tests, candidate adapters, walker, control, gold validator, scorer, V1 script, fixture check |
| `docs/verification/V1-edgartools-return-types.md` | V1 findings |
| `docs/verification/V2-parser-fidelity.md` | V2 measurements |
| `docs/adr/0001-<decision-slug>.md` | The parser decision |

`<fixture_id>` is the accession number plus the exhibit type as filed,
lowercased with dots replaced by hyphens. For example, an illustrative
accession gives `0001234567-25-000123_ex-99-1`.

## Fixture corpus

### Classes

A deterministic class-test script computes these from the saved bytes and records
the values for each fixture. *Visible text* is the text of `<body>`, excluding
`<script>`, `<style>`, and elements whose inline style sets `display: none`.
Characters are counted in the matching space (see Gold annotation).

A **data table** is a `<table>` that, counting only its own rows and cells (not
those of nested tables), has at least two rows with non-empty text and at least
one row with two or more non-empty cells.

- **Table-heavy.** Characters inside data tables make up at least 50% of the
  visible characters. When data tables are nested, each character is counted once,
  in its innermost data table.
- **Narrative-only.** The exhibit has no data tables.
- **Malformed layout.** Any one of these tests fires:
  - *Positioned text:* an inline style or `<style>` block sets
    `position: absolute` or `position: fixed`.
  - *Layout-table prose:* a table that is not a data table has a cell with 40 or
    more words.
  - *Page-break debris:* the document uses page-break styling
    (`page-break-before`/`-after`, or `break-before`/`break-after: page`) and
    contains a bare page-number block. A bare page-number block is an element
    whose whole text is a page number, optionally with "Page" or dashes.
  - *Preformatted text:* `<pre>` elements hold at least 50% of the visible
    characters.
- **Clean HTML.** No malformed-layout test fires.

These parameters only sort fixtures into classes. They are not quality
thresholds, and R13.1 is untouched. Each fixture is filed under one primary
class, and all its test values are recorded. Clean fixtures must trip no
malformed-layout test. Where the shortlist allows, table-heavy and
narrative-only fixtures should trip none either, so that malformed-layout effects
stay in their own class.

### Selection

1. A discovery script, bound by the live-fetch policy, samples 8-K filings that
   report Item 2.02. That item dates from August 2004, so no earlier filings are
   sampled. The sample spans filing years and filer agents and is drawn from
   EDGAR's filing indexes and submissions data. For each filing, the script:
   - identifies the press-release exhibit from the filing index, using the
     exhibit type and description;
   - saves the exhibit to `data/raw/`;
   - runs the class tests.
2. The shortlist holds about three candidates per class, chosen by these
   preferences in order:
   - Exhibits must be HTML with native text. Image-only exhibits need OCR (R4.3),
     and plain-text exhibits are not HTML, so both are excluded.
   - A mix of filer agents and years.
   - No issuer contributes more than two fixtures.
   - Issuers that also exercise Stage 4's cases: a narrative-only release, and a
     release filed under an exhibit number other than EX-99.1.
3. The user approves eight fixtures. The user also approves two or three further
   releases as the bespoke walker's **development set**. Development releases
   stay in `data/raw/` and are never committed or scored.

### Storage and provenance

`source.html` holds the response body exactly as EDGAR served it. That means
after any Content-Encoding (such as gzip) is decoded, and before any charset
decoding. There is no re-encoding, newline normalization, or trimming. `sha256`
is computed over these same bytes. `manifest.toml` holds one `[[fixtures]]`
entry per fixture:

| Field | Content |
| --- | --- |
| `fixture_id` | Directory name |
| `primary_class` | `clean_html`, `malformed_layout`, `table_heavy`, or `narrative_only` |
| `class_tests` | Every value from the class-test script |
| `issuer_name`, `cik` | CIK as a zero-padded 10-character string (A §264) |
| `accession`, `form`, `items`, `filing_date` | As EDGAR reports them |
| `exhibit_type`, `exhibit_filename` | As filed |
| `url`, `retrieved_at` | Source URL; UTC ISO 8601 retrieval time |
| `http_status`, `content_type`, `bytes`, `sha256` | From the saved response |
| `source_id` | Register key: `sec-edgar` |
| `redistribution_basis` | Why this file may be committed, citing the register entry |
| `stage4_flags` | Any of `narrative_only_release`, `alternative_exhibit_numbering` |
| `pilot_split` | `train_or_exclude` |

### Source register

`docs/source-register.toml` holds one entry per source with every field A §242
lists: owner, URL, access method, cost, license/terms, redistribution status,
coverage, expected update pattern, known limitations, and last verification date.
The first entry, `sec-edgar`, also records R1.3's access facts: a User-Agent is
required, a missing one gets 403, a breach gets 429, and the project default is
2 requests/second. It also quotes the SEC's stated policy on reuse of website
content, with the URL and the date it was checked. Its redistribution status says
that this policy does not address issuers' copyright in their filings, and draws
no conclusion about it.

### Forward constraint

The annotator reads every fixture closely. Stage 5 must therefore place fixture
events in the training partition or leave them out of the pilot (R12.3). The
manifest's `pilot_split` field records this.

## Gold annotation

The user is the sole annotator (D2). Gold is marked from a browser's rendering
of `source.html`, never from any candidate's output. No candidate output is
shown as a pre-draft. **Amended (F9):** Codex drafts the gold from the browser's rendering (screenshots and the page's rendered text) and the user verifies every block against the rendering; the verified file is the gold, and everything below applies to it.

### Guidelines

- **Blocks.** Every piece of rendered text belongs to exactly one block, and a
  block is what a reader sees as one unit. A paragraph broken by a page break is
  one block. Prose inside a layout table is marked as paragraphs, not as a
  table. `[[blocks]]` entries appear in rendered reading order, and that order
  is the gold reading order.
- **Types.** `heading`, `paragraph`, `list_item`, `footnote`, `table`, and
  `page_artifact` (running headers and footers, page numbers). Headings and list
  items take an optional `level`, where 1 is the most prominent or outermost.
  Page artifacts need only a `start`, which need not be unique. They are recorded
  for Stage 3 and never scored.
- **Anchors.** `start` is the block's first words and `end` its last. Each is
  copied verbatim from the rendering as one contiguous run of text.
  - Length: at least four words or 20 characters, or the whole block if it is
    shorter.
  - An anchor never includes, or skips over, a bullet, list number, or footnote
    marker.
  - Extend an anchor until it is unique in the document.
  - A block that fits on one line may omit `end`, which then defaults to `start`.
  - If a short block's full text is still not unique, add `after`: the words
    immediately following the block. `after` only locates the block; element
    membership is judged on the block's own text. A block with `after` omits
    `end`.
  - If that fails too, set `unanchorable = true` and put the block's full text in
    `start`. Unanchorable blocks are counted and reported, never scored.
- **Tables.**
  - `headers` lists every header text in the grid: column headers at every level,
    the stub header, and any title or unit line (such as "in millions") drawn
    inside the grid. A title drawn outside the grid is a `heading` block instead.
  - `cells` holds three sample cells in an L:
    - `corner`: a body value cell;
    - `right`: the same row, next data column;
    - `below`: the next body row, same column as `corner`.
  - Choose an L with no spanning cells and no values split across cells (for
    example, a "$" or ")" sitting in its own cell). All three cell texts must be
    unique in the document.
  - Record each cell's `text`, `row_header`, and `col_header`.
- **Footnotes.** A footnote is text set apart and tied to a marker (¹, (1), *).
  The marker is excluded from the anchors.

### Schema

```toml
schema_version = 1
fixture_id = "0001234567-25-000123_ex-99-1"   # illustrative
annotator = "…"
marked_from = "browser rendering"
browser = "…"                                  # name and version
completed = 2026-10-01

[[blocks]]
id = "b001"
type = "heading"
level = 1
start = "…"

[[blocks]]
id = "b012"
type = "footnote"
start = "Excludes the impact of"
end = "…"

[[blocks]]
id = "t003"
type = "table"
headers = ["Three Months Ended", "…", "…"]
cells = [                                      # values illustrative
  { role = "corner", text = "4,321", row_header = "Net sales", col_header = "…" },
  { role = "right",  text = "3,210", row_header = "Net sales", col_header = "…" },
  { role = "below",  text = "2,109", row_header = "Cost of sales", col_header = "…" },
]
```

Block `id`s are unique within the file.

### Matching space

The **primary space** `m(s)` normalizes to NFKC, then deletes every whitespace
character (`str.isspace`) and every Unicode format character (category `Cf`, such
as soft hyphens and zero-width spaces). Case is kept.

The **fallback space** `m2(s)` normalizes to NFKD, drops combining marks
(category `Mn`), and keeps only letters and digits (categories `L*` and `N*`).
Case is kept.
- It applies only to text-block anchors (`start`, `end`, `after`) that the
  primary space misses.
- A fallback match counts only if the anchor's `m2` form occurs exactly once in
  the document and exactly once in the candidate's text.
- Table cells and header texts are matched in the primary space only. In a space
  of only letters and digits, adjacent numbers run together, and short numeric
  texts would match almost anywhere.

All matching, in both the validator and the scorer, is exact substring search in
one of these spaces. Nothing in Stage 1 scoring is fuzzy.

Both spaces keep R3.5's text-fidelity question out of V2's structural one.
Browsers and the candidates disagree on spacing between inline tags. A candidate
may also fold typography, such as curly quotes, dashes, and accents (edgartools,
for one, depends on `unidecode`). Without the fallback, a folded anchor would be
scored as dropped content. Anchors found only in the fallback space count as
found and are reported separately as altered.

### Validator

The validator is a deterministic script that uses only the standard library. It
extracts the text of `source.html` with the standard library's `html.parser`,
which is independent of every candidate. It takes all text outside `<head>`,
`<script>`, and `<style>`, and applies `m()`. It checks:

- **Schema:**
  - required fields are present;
  - types come from the vocabulary;
  - `id`s are unique;
  - `level` appears only on headings and list items;
  - each table has exactly one cell per role.
- **Uniqueness:**
  - every `start`, `end`, and cell `text` occurs exactly once; for a block with
    `after`, the combined `start` + `after` must occur exactly once instead;
  - every header text occurs at least once;
  - an unanchorable block's `start` (plus `after`, if given) occurs at least twice;
  - a warning, not an error, when a text-block anchor is not unique in the
    fallback space, because the fallback could not then rescue it;
  - page artifacts are exempt.
- **Anchor length:** anchors meet the guideline minimum.
- **Order:** a warning, not an error, when a block's `end` precedes its `start`.

When an anchor is not found, the validator also reports case-insensitive hits,
because CSS `text-transform` can change the rendered case. A fixture must pass
the validator before it is scored.

## Candidate harness

All code lives in `expirements/parser-fidelity/`.

- **Isolation.** Each candidate is a PEP 723 script with pinned inline
  dependencies and a committed script lock (`uv lock --script`).
  - The edgartools adapter pins `edgartools==5.58.0`.
  - The walker and the control pin lxml and beautifulsoup4 to their `uv.lock`
    versions.
  - A candidate that cannot install on Python 3.14 may declare an older
    `requires-python`, and the V2 record states the interpreter used.
- **Element dump.** Each adapter reads the saved bytes and writes to gitignored
  `data/runs/parser-fidelity/` an ordered list of leaf elements, in the
  candidate's document order. Each element carries:
  - a common type: `heading`, `paragraph`, `list_item`, `footnote`, `table`, or
    `other`;
  - its text;
  - a parent index, where the candidate nests elements.

  Container nodes contribute no text beyond their children's. If a candidate
  exposes a table as a grid, the table element's text is that grid read row by
  row, header rows (including column labels) first, and the cells are recorded
  too. Otherwise the text is exactly as the candidate emits it. Cell text is the
  text the candidate extracted, never a converted value such as a parsed number.
  If a candidate exposes only converted values, the table is built from them and
  the V2 record says so. Dumps carry no run metadata.
- **Type mapping.** Each adapter maps the library's public element types to the
  common types. Mappings are published in the V2 record.
- **Freeze.** Adapter, control, and walker source files are frozen, with their
  sha256s recorded, before their first run on any fixture. All debugging happens
  on the development set.
  - After the freeze, a change is allowed only to fix a crash or a network-guard
    trip caused by adapter code. It may never alter a type mapping or a walker
    rule.
  - The V2 record lists each such change with its diff, or states that none
    followed the freeze.
- **Network guard.** Before the candidate is imported, the harness replaces
  socket connection with a function that raises. A tripped guard voids the run.
- **Determinism.** Each candidate runs twice per fixture, in separate processes
  with default hash randomization, and the two dumps are compared byte for byte.
- **Bespoke walker.** Its rules come from the meaning of HTML tags (`h1`–`h6`,
  `p`, `div`, `li`, `table`/`tr`/`td`/`th`, `br`) plus generic EDGAR idioms
  written down before development begins. For example, a short block whose text
  is entirely bold or underlined is a heading. It is developed only on the
  development set, no rule may name or target a fixture, and it is frozen under
  the rule above.
- **Control.** `BeautifulSoup(html, "lxml").get_text("\n", strip=True)`, with
  each non-empty line as a `paragraph`. The control is scored and reported like
  any candidate, but it can never be selected.

## Metrics

### Scoring mechanics

The scorer joins a dump's element texts in order, in each matching space, and
records where each element starts.
- An anchor is **found** when it occurs in the primary-space text. Its position
  is its first occurrence, and a second occurrence marks it **duplicated**.
- A text-block anchor the primary space misses is still found, and marked
  **altered**, when it matches under the fallback rule.
- Positions are compared as (element index, offset within the element), mapped
  back from whichever space found the match.
- An anchor's **elements** are the elements its match overlaps.
- A block with `after` is matched as the single string `start` + `after`, and
  its `end` is taken to be its `start`. Only the block's own portion of the match
  counts toward its elements.
- A block's **home element** holds the first character of its `start`.

Unanchorable blocks and page artifacts are excluded from every metric.

### Ranked metrics

Each metric is computed per fixture, then pooled per class by summing numerators
and denominators over the class's two fixtures.

| Metric | Definition |
| --- | --- |
| Block coverage | Gold blocks found ÷ gold blocks. A text block counts as found when both `start` and `end` are found, altered anchors included. A table counts as found when all three cells are. |
| Footnote merging | Found footnotes that have an anchor in an element also holding an anchor of a gold heading, paragraph, or list item ÷ found footnotes |
| Reading order | The gold sequence lists each text block whose `start` is found, and each found table cell in the order corner, right, below. Corruption is the share of adjacent pairs in that sequence whose positions are reversed in the joined text. |
| Header loss | The mean of whichever sub-rates have a nonzero denominator in the class. **Section:** found headings whose home element is not typed `heading`, or also holds another gold block's anchor ÷ found headings. **Table:** header texts of found tables that are absent from the union of `table`-typed elements holding any of that table's cells ÷ header texts of found tables. |

In the reading-order sequence, the L-shaped cells catch a parser that emits a
table column by column. The pairs entering and leaving a table catch tables moved
out of place, such as all tables appended at the end.

### Diagnostics

These are reported for every candidate but not ranked:
- **Altered anchors:** text-block anchors found only in the fallback space,
  reported prominently for each candidate and class. They are flagged for Stage
  3's R3.5 check.
- **Split rate:** text blocks whose `start` and `end` fall in different elements,
  or whose anchor straddles an element boundary.
- **Other merges:** merges that don't involve footnotes, meaning elements holding
  anchors of two or more gold blocks.
- **Duplication rate.**
- **Footnotes absorbed into tables:** footnotes whose text sits inside a `table`
  element.
- **Cell-to-header association:** for candidates that expose cells, the share of
  sample cells whose row and column headers match the gold. This informs R4.2.
- **Unanchorable blocks** per fixture.
- **Runtime.**

## Selection rule

The rule is fixed before any fixture is scored (F6, F7).

1. **Eligibility gates.** A candidate is eligible only if it passes all three.
   Ineligible candidates are still scored and reported.
   - **Lock gate.** It resolves into the workspace lock: added as a dependency
     of `earnings-ingestion` in a scratch copy of the repository, `uv lock`
     succeeds and lowers no locked version. It also imports and parses every
     fixture under Python 3.14. A candidate that adds no dependency, such as the
     walker, passes the lock part of this gate by construction.
   - **Determinism gate.** Its two dumps for every fixture are byte-identical.
   - **Network gate.** Its documented parse path runs without tripping the
     network guard. If the guard trips because of an adapter defect, the adapter
     is fixed and the run repeated.
2. **Worst class.** For each eligible candidate and each ranked metric, take its
   worst class: the lowest coverage, or the highest error rate. A class where a
   metric has no denominator is skipped for that metric.
3. **Priority comparison.** Take the metrics in order: coverage, footnote
   merging, reading order, header loss. At each metric, keep only candidates
   within the tie margin of the best value, and stop when one remains.
   - Two values tie when they differ by at most 1/n, where n is the smaller of
     the two denominators behind them.
   - For header loss, each candidate's denominator is its worst class's
     combined count of found headings and header texts.
   - The margin keeps a single block from deciding the choice.
4. **Tie-breaks,** in this order:
   - fewer runtime dependencies added to `earnings-ingestion` (pandas anywhere in
     the added tree counts against a candidate);
   - a permissive OSI license over a copyleft one;
   - the more recent release.

Coverage ranks first because the other three metrics only count what the parser
found. A parser that drops a hard footnote or table would otherwise improve on
them by dropping it.

Outcomes:
- **One eligible candidate:** it is selected.
- **No eligible candidate:** the V2 record says so, and the decision returns to
  the user. Stage 1 does not close until the ADR records one.
- **An ineligible candidate would have won step 3:** the V2 record states what it
  would have gained. Vendoring it, or pinning around it, needs its own ADR and is
  not a Stage 1 outcome.

Expected, to be confirmed: the lock gate excludes sec-parser. Its 0.58.1 release
requires `lxml<6` and `pandas<3`, while the lock holds lxml 6.1.3 and pandas
3.0.6. That leaves
edgartools and the walker as the candidates that could be adopted. Measuring
sec-parser still answers whether RG §2's recommendation holds.

**Control check.** For each class, the V2 record states whether the selected
parser beats the control by more than the tie margin on coverage, footnote
merging, or reading order. The control has no element types, so header loss
cannot tell it apart from a real parser. If the parser beats the control in no
class, the fixtures are flagged as unable to discriminate between parsers.
Before accepting the ADR, the user then decides whether to replace any of them.

**Residual failures.** The V2 record lists, by fixture and block ID, every gold
unit the selected parser misses, splits, merges, misorders, or loses a header on.
Stage 3 either compensates for each one or records it as a limitation.

## V1: edgartools 5.58.0 return types

- **Paths.** The paths are enumerated from the installed 5.58.0 source, not
  recalled from memory. There are three families:
  - (a) listing an issuer's filings (Stage 4, R1.1);
  - (b) going from a filing to its attachments, then to exhibit bytes, HTML, or
    text, including the 8-K and press-release convenience objects;
  - (c) extracting tables from an exhibit.
- **Recorded for each path:**
  - the call;
  - the return type declared in the source;
  - the concrete type observed at run time, module-qualified, with element types
    for containers;
  - whether it is a foreign dataframe: pandas, pyarrow, or anything other than
    Polars.
- **Run.** Live and opt-in, against the fixture filings, in a PEP 723 script
  pinned to `edgartools==5.58.0`.
- **Conclusion.** One line: either "R14.5 cast required for: …" or "R14.5 vacuous:
  no path returns a foreign dataframe."

The record keeps both the declared and the observed type because they can
differ. A method annotated `-> Any`, or one that returns different types in
different cases, may show a pandas frame only at run time.

## Live-fetch policy

This policy applies to every network call in Stage 1: discovery, the fixture and
development-set fetches, the register's policy check, and V1.

- **Identity.** Live scripts refuse to start unless `EDGAR_IDENTITY` is set to a
  descriptive User-Agent with a real contact. This is the variable edgartools
  reads, to be confirmed in its 5.58.0 source. The user sets it outside Git. The
  fetcher sends the same value, so both clients share one identity and one rate
  budget (A §400).
- **Rate.**
  - Only one live process runs at a time, at no more than 2 requests/second.
  - The fetcher spaces request starts at least 0.5 s apart.
  - edgartools is capped by whatever mechanism its 5.58.0 source provides, and
    the V1 record says which. If none is reliable, V1 routes edgartools' HTTP
    transport through the fetcher's throttle.
  - Each run stops at 500 requests by default (configurable) and reports its
    request count.
- **Failure handling.**
  - Explicit timeouts.
  - Bounded retries with exponential backoff and jitter.
  - `Retry-After` is honored, and a 429 means back off.
  - A 403 that persists stops the run and is reported. The identity is never
    rotated.
- **Saving.** Only 200 responses with the expected content type are saved. An
  SEC block or rate-limit page is a failure, not an exhibit, whatever its status.
  Every saved response records its URL, UTC retrieval time, status, content type,
  byte count, and sha256, with the bytes defined as under Storage and provenance.
  Responses are saved to gitignored `data/raw/`. Approved
  fixtures are then copied byte-for-byte into `tests/fixtures/` with their
  retrieval metadata, so the class tests ran on exactly the committed bytes and
  no fixture is fetched twice.

## Records

- **`docs/verification/V2-parser-fidelity.md`:**
  - the corpus and its class-test values;
  - the gold protocol, including F9's Codex brief and, per fixture, how many blocks verification changed;
  - for each candidate: version, interpreter, lock, type mapping, and gate
    results;
  - metric tables by class and candidate, per-fixture detail, and the
    diagnostics;
  - the selection rule applied step by step;
  - the control check;
  - residual failures and altered anchors (for Stage 3);
  - element types and nesting observed in the gold (for Stage 2): heading and
    list depths, where footnotes sit, and tables inside lists or tables;
  - limitations:
    - only eight fixtures and one annotator, who verified Codex drafts rather than marking from scratch (F9);
    - the gold was marked from a browser rendering;
    - coverage checks a block's ends, not its middle;
    - text fidelity is not measured here (R3.5, Stage 3);
    - any candidate run on a different interpreter.
- **`docs/adr/0001-<decision-slug>.md`:**
  - follows the design-architecture template;
  - holds one decision: "We will use X as the base parser for release
    canonicalization";
  - lists alternatives with their measured losing reasons;
  - its reversibility section notes that switching parsers changes canonical
    text, and so creates a new version of every document (R3.3).

  Its status stays Proposed until the user accepts it.
- **`docs/verification/V1-edgartools-return-types.md`:** everything V1 lists
  above, plus the rate-limit mechanism.

## Order of work

1. Write the register entry, the fetcher, and the class tests.
2. Run discovery and build the shortlist. The user approves the fixtures and the
   development set.
3. Copy the approved fixtures from their saved discovery responses into
   `tests/fixtures/`, with `.gitattributes` in place. The development set stays
   in `data/raw/`.
4. In parallel:
   - the user marks the gold, validating as they go (an estimated 1–2.5 hours
     per fixture);
   - the adapters are written and their mappings fixed;
   - the walker is built on the development set and frozen;
   - V1 runs.
5. Score, then apply the rule.
6. Write the V2 record, the V1 record, and the ADR.
7. The user accepts the ADR.

## Contingencies

- **edgartools 5.58.0 exposes no typed HTML document parser.** Record this; the
  comparison proceeds without it.
- **sec-parser installs on no available interpreter.** Record it as
  unmeasurable. RG §2's claim then stays untested, and the V2 record says so.
- **A class has fewer than two qualifying fixtures within the size cap.**
  Discovery widens its sample. If the class is still short, the user chooses
  between one fixture for that class, recorded as a limitation, and relaxing a
  shortlist preference.

## Exit criteria

1. The V2 record reports every ranked metric and diagnostic for every candidate
   and the control, on every class, with per-fixture detail (V2).
2. ADR 0001 names the parser selected by the fixed rule, and its status is
   Accepted.
3. The V1 record gives the concrete type of every enumerated path and states
   whether R14.5's cast is required or vacuous (V1).
4. A harness check script confirms that:
   - each fixture directory holds exactly `source.html` and `gold.toml` and has
     a manifest entry, and each manifest entry has a directory;
   - each `source.html` matches its sha256 and is at most 1 MiB;
   - `.gitattributes` marks `source.html` files `-text`;
   - every `source_id` resolves to a register entry with a recorded
     redistribution status;
   - every `gold.toml` passes the validator;
   - every harness script that declares dependencies has a committed lock.
5. `uv run --locked ruff check .` and `uv run --locked ruff format --check .`
   pass, and `uv.lock` and `packages/` are unchanged.

## Handoffs

| Stage | Receives |
| --- | --- |
| 2 | Element types and nesting observed in the gold |
| 3 | ADR 0001, the residual failures, and the fixtures with their gold; R3.5 remains open |
| 4 | The V1 record; the manifest's `stage4_flags` |
| 5 | `pilot_split = "train_or_exclude"` on every fixture event |

## Rollout

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 1 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

On completion, also refresh the "Current state" section of `CLAUDE.md`: the
fixtures, source register, harness, and records now exist. In the handoff, state
which commands ran, including every live run and its request count. Also state
that no package tests exist yet and that no model was called.
