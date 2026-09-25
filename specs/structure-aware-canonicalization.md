# Structure-aware canonicalization

> For agentic workers: REQUIRED NEXT SKILL: writing-plans. This is the stage spec
> for Stage 3 of `specs/evidence-linked-theme-extraction-roadmap.md`. Plan it as two
> plans, in order: plan A (§Plan A) first, and plan B (§Plan B) only after plan A
> ships. Never plan both in one plan.

Stage 3 turns saved release bytes into hashed, versioned canonical documents with
typed elements, quarantined tables, and boilerplate masks, on the parser ADR 0001
selected. It closes R3.1, R3.5, R4.1, R4.2 and R4.3 of
`specs/evidence-linked-theme-extraction.md`, and V9's normalization and
sentence-splitting cases. It also carries out the Stage 3 sections of
`specs/browser-rendering-integration.md` (B1–B5, B7–B9).

Locators:
- **`A §n`** is `AGENTS.md`.
- **`Rn` and `Vn`** are the theme spec's requirements and verifications.
- **`Bn`** are the browser spec's decisions.
- **`D-n`** are plan 3's decisions (`specs/plans/completed/3-core-evidence-spine.md`).
- **`Fn`** are the Stage 1 spec's decisions (`specs/release-parser-fidelity.md`).
- **`W0`–`W16`** are the walker's rules (`expirements/parser-fidelity/walker-rules.md`).
- **V2** is `docs/verification/V2-parser-fidelity.md`.
- **ADR 0001** is
  `docs/adr/0001-use-the-bespoke-lxml-walker-as-the-base-parser-for-release-canonicalization.md`.

Designed 2026-09-25 in a brainstorming session, from `main` at `1c27b72`.

## Decisions

Taken with the user on 2026-09-25. Rows marked *(design)* were proposed in the
design and approved with it.

| ID | Decision |
| --- | --- |
| SC1 | One spec, two plans, in order. Plan A builds the canonicalizer and meets the roadmap's Stage 3 Exit. Plan B builds the browser diagnostic path and meets the browser spec's Stage 3 verification. Stage 3 is complete only when both are. Stage 6 annotation waits for plan B's promotion decision (ADR 0002). |
| SC2 | The frozen walker (W0–W16) is ported verbatim and proven equal to the frozen code. A separate, predeclared compensation pass (C1–C5) changes element types only, never text. Development may correct how a rule is implemented. It may not add, remove, or retune a rule, except at the review gate (§Gates (plan A)). Scores measured after compensation are development-set numbers: the fixtures were Stage 1's test set. |
| SC3 | Compensation targets `<pre>` tables (C1, which R4.2 requires) and page artifacts (C2–C5). Styled headings and prose inside data tables are plan B's pre-registered targets. Table-header fixes are recorded limitations. |
| SC4 | Tables are quarantined with minimal cells. No later stage consumes cell evidence, so cells carry only what the walker computes: row, column, spans, the W15 header flag, and column-header references. There are no row headers and no `<pre>` grid rebuild. |
| SC5 | Sentences are split by in-house rules, S1, that prefer under-splitting. |
| SC6 | Boilerplate masks come from predeclared rules, M1–M5 (policy `boilerplate`, version `1`), which the user reviews on the fixture report. |
| SC7 | For OCR, `DocumentElement` gains `text_origin`, and `validate_span` refuses spans that touch OCR text. No OCR engine ships. Image-only input fails with `no_native_text`. |
| SC8 | `canonicalization_version` is one numbered policy name, `walker-1`. Any change to canonical text or elements bumps it. A manifest records each component's version. There is no `parser_version` field. |
| SC9 | One coordinated core change: schema version 2, validator version 2, and four deferred fixes. |
| SC10 | R3.5's rendered source is the committed gold in plan A. Plan B adds full browser captures and the user's local rendered copies. |
| SC11 | *(design)* Normalization N1 is NFC, deletion of named invisible characters, and whitespace collapse. It never applies NFKC and never folds dashes, minus signs, or quotes. |
| SC12 | *(design)* `walker-1` emits no `section` elements. |
| SC13 | *(design)* An alignment failure is an ingestion status carrying an existing core reason. Core gains no alignment reason. |
| SC14 | *(design, surfaced at spec review)* Plan B never changes canonical text. Its comparison evaluates element streams over `walker-1`'s text, so any promotion it supports keeps that text. This narrows the browser spec's outcome 3, "a new primary canonicalization policy", to a new element stream over `walker-1`'s text. A policy that changes canonical text would need its own comparison, outside Stage 3. |

## Scope

In scope: everything in §Plan A and §Plan B, the V2 disposition, and the deferred
items in §Deferred items.

Out of scope:
- Acquisition, EDGAR access, and the processing-state table (Stage 5).
- Any media type but `text/html`.
- Transcripts and speaker metadata (Stage 13).
- Evidence selection, eligibility policy beyond element types, verification stages,
  and support (Stages 7–8).
- The headline exclusion that uses the masks (Stage 10).
- Consumers of cell evidence, row headers, and `<pre>` grid rebuilding (SC4).
- An OCR engine (SC7).
- Any change to Stage 1's frozen files, gold, fixtures, V2 record, or ADR 0001.

## Inputs

- **From Stage 1:**
  - ADR 0001, which selects the walker;
  - V2's "Residual failures (for Stage 3)", "Findings for Stage 3", and "Notes on
    ADR 0001 after acceptance";
  - the walker's Known gaps;
  - the eight fixtures in `tests/fixtures/releases/`, with their `source.html` and
    `gold.toml`.
- **From the local, uncommitted Stage 1 run data:**
  - the three development releases in `data/raw/devset/`;
  - the user's `*.rendered.txt` copies in `data/runs/parser-fidelity/gold-drafts/`,
    made in Chrome with Select All and Copy, with table cells separated by tabs.
    Only plan B uses them.
- **From Stage 2:** the `earnings_core` contracts and checks: `CanonicalDocument`,
  `DocumentElement` with `TableCellContext`, `OverlayMask`, `MaskedDocument` via
  `apply_masks`, `validate_elements`, `validate_span`, `Rejection`, and
  `ArtifactRef`. Also plan 3's Handoffs 1–11, each answered in §Handoffs from plan 3.
- **From the browser spec:** B1–B5 and B7–B9, and its Stage 3 sections.

Facts that shape the design:
- **Walker output.** The walker emits typed blocks with collapsed text, not offsets.
  Stage 3 must build the canonical text and assign every span.
- **Encoding.** All eight fixtures are pure ASCII.
- **Superscripts.** Six fixtures hold 49 `<sup>` runs:
  - ordinal suffixes, such as "1st";
  - parenthesized markers, such as "(1)" and "(a)";
  - "®";
  - two empty runs, in Southwestern Energy.

  None is a bare digit.
- **`<pre>`.** One fixture, Pharmacyclics, draws its two data tables in `<pre>`. They
  are fixed-width statements with dot leaders and rule lines.
- **The production corpus.** It is 2024–2026 DJIA releases, while the fixtures run
  from 2007 to 2022. Failure classes common in old filings may be rare in
  production, and the reverse. The R3.5 check therefore reruns on Stage 5's pilot
  releases (§Handoffs to later stages).

## Plan A — the canonicalizer

### Interface

```python
canonicalize(raw: bytes, *, source_document_id: str, media_type: str) -> Canonicalized | CanonicalizationFailure
```

- **Purity.** The function is pure:
  - it has no network client and does no file I/O;
  - it changes no global state, including the recursion limit;
  - it is deterministic.
- **The result.** `Canonicalized` holds:
  - the `CanonicalDocument`;
  - its elements, as a tuple in document order with each parent before its
    children;
  - a `MaskedDocument`;
  - a `CanonicalizationManifest`.
- **Location.** The code lives in `earnings_ingestion.canonical`. It imports only
  `earnings_core`, Pydantic, lxml, and the standard library.
- **Proposed modules:**
  - `decode`;
  - `dom` (the ported `pf_classes` helpers);
  - `walker`;
  - `compensate`;
  - `normalize`;
  - `build`;
  - `sentences`;
  - `boilerplate`;
  - `manifest`;
  - `fidelity` (the R3.5 comparators).

  The plan may rename them.

### Pipeline

```text
saved bytes + source_document_id + media type
  → decode            the ported pf_decode rule
  → walker            W0–W16, ported verbatim
  → normalize         N1, on every block and cell
  → compensate        C1–C5: types only, never text
  → build             layout L1: canonical text, spans, table and cell elements
  → sentences         S1, inside paragraphs, list items, and footnotes
  → validate          validate_elements; any rejection is a hard failure
  → masks             M1–M5 under policy boilerplate/1, through apply_masks
  = Canonicalized | CanonicalizationFailure
```

### Decoding

- **The rule** is the ported `pf_decode`:
  1. a byte-order mark;
  2. a `<meta>` charset in the first 1024 bytes, with the WHATWG mappings of the
     windows-1252 and UTF-8 labels;
  3. UTF-8, when the bytes are valid UTF-8;
  4. windows-1252.
- **Decode before parsing.** The canonicalizer decodes the bytes itself, before
  parsing. V2 found that edgartools' press-release path decodes with
  `errors="replace"`.
- **Records.** The manifest records the decoded encoding and its basis. U+FFFD
  characters are kept, and counted.

### Walker port

- **What is ported.** W0–W16 are ported verbatim, with the helpers they use:
  - from `pf_classes`: parsing, `body_of`, the hidden-content test, visible text, own
    rows and cells, the data-table test, and the bare page-number pattern;
  - from `pf_space`: `primary_space`, which the data-table test uses;
  - from `pf_dump`: the element, row, and cell shapes.
- **Copied, not imported.** A package imports nothing under `expirements/`.
- **One implementation change.** The traversal no longer raises the interpreter's
  recursion limit (`walker.py:388-390`). It is iterative, or otherwise bounded
  without global state. Its output is unchanged.
- **One addition.** Each W5 `<pre>` piece keeps its original lines, as they were
  before W4 collapsed them, for C1. The emitted text is unchanged.

§Verification (plan A), item 1, proves the port equal.

### Compensation rules C1–C5

- **Order.** The rules apply in order, and a block retyped by one rule is not
  considered by a later one. They read each block's normalized text (N1).
- **Effect.** Each changes an element's type, and so its derived ID (D-1), never its
  text.
- **Parameters.** They are fixed here. The 12-word limit is W11's heading limit.

**C1 — `<pre>` tables.** A block the walker emits from a `<pre>` piece (W5) becomes
a `table` with no cells when any of the piece's original lines:
- is a rule line: only `-`, `=`, `_`, and spaces, with at least three rule
  characters;
- holds a dot leader: four or more consecutive `.`;
- ends with a numeric field set off by two or more spaces, ignoring trailing
  whitespace. A numeric field is W15's numeric-looking pattern: digits, commas, and
  periods, optionally with `$`, parentheses, `%`, or a dash.

Its text stays as the walker collapsed it. Limitation: `<pre>` tables yield no cell
evidence.

**C2 — EDGAR header line.** The document's first block becomes `page_artifact` when
its text matches, case-insensitively:

```text
^EX-\d+(\.\d+)*\s+\d+\s+\S+\.(htm|html|txt)\b
```

This matches, for example, "EX-99.1 2 exhibit991.htm EXHIBIT 99.1".

**C3 — Page numbers.** A block the walker typed `other` by W8 becomes
`page_artifact`. A block whose whole text is a year from 1900 to 2099 stays `other`.

**C4 — "Page N of M".** A block whose whole text matches
`^(page\s*)?\d{1,4}\s+of\s+\d{1,4}$`, case-insensitively, becomes `page_artifact`.

**C5 — Running lines.** A block that is not a table, has at most 12 words, and whose
exact text occurs at least three times in the document as a whole block, counting
itself, becomes `page_artifact`.

Page artifacts are typed, not masked. Their type excludes them from analysis
eligibility (plan 3, Handoff 7).

### Normalization N1

N1 applies to every block text and every cell text, after the walker's own
whitespace collapse (W4):

1. NFC.
2. Delete:
   - U+00AD (soft hyphen);
   - U+200B (zero-width space);
   - U+2060 (word joiner);
   - U+FEFF (zero-width no-break space);
   - every control character (category `Cc`) that `str.isspace` does not count as
     whitespace.
3. Collapse every whitespace run (`str.isspace`) to one U+0020, and strip both ends.
4. Drop a block or cell left empty.

N1 deliberately leaves some things alone:
- **No compatibility mapping (NFKC).** It would turn "¹" into "1" and "½" into
  "1⁄2", hiding exactly what R3.5 checks.
- **No folding** of dashes, minus signs, quotes, apostrophes, digits, or case.
  Numeric signs stay as the source wrote them.

### Canonical text layout L1

- **Blocks.** Blocks appear in the walker's order, one per line: consecutive blocks
  are separated by exactly one `\n`.
- **Tables.** A table's text is its rows in the walker's order (W14), separated by
  `\n`. Each row is its non-empty cells' texts, separated by one `\t`. Empty cells
  contribute nothing; their grid positions live in `TableCellContext` (D-10).
- **List containers** (W7) contribute no text. Each spans from its first item's start
  to its last item's end. A container with no text in any item is dropped.
- **Edges.** The text has no leading or trailing separator.
- **Spans.** Every span covers exactly its unit's text, and separators belong to no
  leaf element.

### Elements

| Type | Produced by | Parent | Level |
| --- | --- | --- | --- |
| `heading` | W6, W11 | none | W6's level; none for W11 |
| `paragraph` | W12 | none | none |
| `list_item` | W7 (`li`), W9 (bullet glyph), W13 (marker table) | its list container (W7), else none | list depth (W7), else none |
| `footnote` | W10, W13 | none | none |
| `table` | W14 (grid), C1 (`<pre>`, no cells) | none | none |
| `table_cell` | each non-empty cell of a W14 grid | its table | none |
| `sentence` | S1, inside `paragraph`, `list_item`, `footnote` | its block | none |
| `page_artifact` | C2–C5 | none | none |
| `other` | W7 list containers; W8 years kept by C3 | outer container, for a nested list | none |

- **Order.** Elements are in document order, with each table followed by its cells in
  row-major order and each block by its sentences.
- **Source types.** Blocks keep the walker's `source_type`. The manifest counts
  retypes by rule.
- **Text origin.** Every element's `text_origin` is `native`.
- **No `section` elements (SC12).** The walker loses 45 headings, so section extents
  derived from headings would misattribute text. Headings remain available as
  context.

### Tables and cells (SC4)

For each W14 grid:

- **`row`** indexes the walker's emitted rows. W14 drops rows with no text.
- **`column`** is the grid column, found by occupancy. A cell starts at the first
  column not occupied by a `rowspan` from an earlier row. It occupies `column_span`
  columns and `row_span` rows, clipped to the grid.
- **Spans.** `row_span` and `column_span` are the walker's `rowspan` and `colspan`.
- **`is_header`** is W15's flag on the cell's row.
- **`header_cell_ids`.** A non-header cell lists, in row order, the non-empty cells of
  header rows above it whose column ranges overlap its own. A header cell lists none.

W15's own limitations pass through to header context:
- stub labels such as "ASSETS:" flagged as header rows;
- a second set of column headers partway down a table, never flagged.

### Sentences S1

- **Where S1 runs.** S1 splits `paragraph`, `list_item`, and `footnote` elements.
  Headings and cells are not split.
- **Leading markers.** A leading W9 bullet glyph, or one of W10's textual footnote
  markers, stays outside the first sentence, with the space after it. The textual
  markers are `(1)`–`(99)`, `(a)`–`(z)`, one to three `*`, `†`, `‡`, and superscript
  digits. A block with nothing after its marker gets no sentence.
- **Candidates.** A candidate boundary follows `.`, `!`, or `?`, plus any closing
  quote or bracket (`"`, `'`, `”`, `’`, `)`, `]`). Whitespace must come next, then
  an uppercase letter, a digit, or an opening quote or bracket (`"`, `'`, `“`, `‘`,
  `(`, `[`). A decimal point is never a candidate, because no whitespace follows it.
- **Not a boundary:**
  - after a listed abbreviation (case-sensitive):
    - Mr. Mrs. Ms. Dr. Prof. Sr. Jr. St.
    - Inc. Corp. Co. Cos. Ltd. Bros. L.P. L.L.C. N.A. N.V. S.A. P.C.
    - U.S. U.K. U.N. E.U. N.Y. D.C.
    - Jan. Feb. Mar. Apr. Jun. Jul. Aug. Sep. Sept. Oct. Nov. Dec.
    - No. Nos. vs. v. approx. est. e.g. i.e. etc. a.m. p.m. Fig. Vol. Ph.D.
      Ave. Blvd.
  - after a single capital letter, which is an initial, as in "J.P. Morgan";
  - when the text so far is only an enumerator at the start of the unit, such as
    "1.", "a.", or "iv.".
- **Under-splitting.** A sentence that really ends in a listed abbreviation merges
  with the next one. This is recorded as a limitation: a longer pointer quote is
  safer than a claim cut in half.
- **Spans.**
  - A sentence spans from its first non-whitespace character to the end of its
    terminal punctuation and closing marks.
  - Whitespace between sentences belongs to no sentence.
  - A unit with no boundary is one sentence.
- **Versions.** Any change to these rules or the abbreviation list is S2, and so a new
  canonicalization version.

### Boilerplate masks M1–M5 (SC6)

- **The policy.** `policy_id = "boilerplate"`, `policy_version = "1"`, built through
  `apply_masks`.
- **What masks cover.** Masks cover whole narrative elements: `heading`, `paragraph`,
  `list_item`, and `footnote`. They never cover cells, tables, page artifacts, or
  `other`. Sentences inside a masked block are covered by overlap
  (`masks_overlapping`).
- **One mask per element.** It takes the category of the first rule, in the order
  below, that matches.
- **Matching** is case-insensitive, over the element's canonical text.

| Rule | Category | Fires on |
| --- | --- | --- |
| M1 | `safe_harbor` | A heading matching "forward-looking statements", "forward-looking information", "safe harbor", "cautionary statement", or "cautionary note". It masks the heading and the paragraphs, list items, and footnotes after it, up to the next heading or table. Page artifacts and `other` elements inside that stretch, such as a list's container, are skipped, not stopped at. |
| M2 | `non_gaap_disclaimer` | A heading containing "non-GAAP". Its extent follows M1. |
| M3 | `safe_harbor` | A block containing "Private Securities Litigation Reform Act", or "forward-looking statements" together with any of "risks", "uncertainties", "undue reliance", or "actual results". |
| M4 | `non_gaap_disclaimer` | A block containing "non-GAAP" together with any of "in accordance with", "substitute for", "in isolation", or "not be considered". |
| M5 | `repeated_legal` | A block containing "registered trademark" or "trademarks of"; "shall not be deemed" together with "filed"; "does not constitute an offer"; "where to find it"; or "participants in the solicitation". |

Masks never change canonical text (R3.4). Masked elements stay in extraction's
traversal; excluding them from headline prevalence is Stage 10's job.

### Versions and the manifest (SC8)

- **`canonicalization_version = "walker-1"`.** It names the whole policy:
  - W0–W16 as frozen at `616721a`;
  - C1–C5;
  - N1;
  - L1;
  - S1;
  - the decoding rule.
- **Bumping.** Any change to canonical text or elements makes it `walker-2`, including
  a change caused by upgrading lxml or libxml2. Existing documents are never
  regenerated under the same name.
- **`CanonicalizationManifest`** is an ingestion record with a schema version. It
  holds:
  - the canonicalization version and each component's identifier;
  - the lxml and libxml2 versions (`lxml.etree.LXML_VERSION`, `LIBXML_VERSION`) and
    the Python version;
  - the source document ID, raw SHA-256, and byte count;
  - the decoded encoding and its basis;
  - element counts by type, the `<img>` count, and the U+FFFD count;
  - retype counts by compensation rule;
  - the limitations triggered, such as `pre_table_without_cells`;
  - the mask policy and the mask count.

  It holds no timestamp and no path, so it regenerates byte for byte.
- **The run manifest.** Operational run metadata, as A §412 requires, belongs to the
  application that calls the canonicalizer.

### Canonical fixtures

- **What is committed.** For each of the eight fixtures, `tests/fixtures/canonical/<fixture_id>.json` holds the
  manifest, the document, the elements, and the masks. Serialization is fixed, with
  sorted keys.
- **Location.** The files sit outside `tests/fixtures/releases/`, because Stage 1's
  fixture check requires each release directory to hold exactly `source.html` and
  `gold.toml`.
- **Redistribution.** These are derived from exhibits already committed under the
  `sec-edgar` register entry, so they carry the same redistribution basis.
- **Who uses them.** Stage 7 runs on them, since `earnings-themes` may not import
  `earnings-ingestion`.
- **Regeneration.** A test regenerates each file byte for byte. A difference, whether
  from code or from a dependency upgrade, fails the test and requires a new
  canonicalization version.

### Failures

- **`CanonicalizationFailure`** is an ingestion record. It holds the source document
  ID, the raw SHA-256, the canonicalization version, a reason, and a detail.
- **Reasons:**
  - `unsupported_media_type` — anything but `text/html`;
  - `parse_failed` — lxml raised;
  - `no_native_text` — nothing is left after N1. The failure records the `<img>`
    count, which covers image-only input (SC7);
  - `invalid_elements` — `validate_elements` returned rejections. This is a
    canonicalizer defect, and the failure carries the rejections.
- **Decoding never fails.** It falls back to windows-1252.
- **No partial output.** A failure is never an empty document and never a partial
  element set.

### Core change: schema version 2 (SC7, SC9)

One change, with one update to `docs/data-dictionary.md`. The data dictionary's
drift test must pass.

- **`TextOrigin`** is a `StrEnum` with the values `native` and `ocr`.
  - `DocumentElement.text_origin: TextOrigin = TextOrigin.NATIVE`.
  - `RejectionReason.OCR_DERIVED_TEXT = "ocr_derived_text"`: the span overlaps
    OCR-derived text, which is never an original quotation (R4.3).
  - `validate_span` refuses a span that overlaps any genuine OCR element. This check
    runs after the speaker-turn check.
- **`MaskedDocument`** gains a model validator. It checks document integrity, each
  mask's `doc_id` and hash, each mask's bounds, and that every mask comes from the
  document's own policy version. `apply_masks` relies on it and keeps its
  `ValueError` contract.
- **`validate_elements` rechecks** three invariants that construction checks and
  `model_copy` skips, each reported as `malformed_record`:
  - a level on a non-leveled type;
  - table-cell context present exactly on `table_cell` elements;
  - an element that is its own parent.
- **`validate_elements` reports every crossing pair.** For A = [0, 10), B = [5, 15),
  and C = [12, 20), it reports B crossing A and C crossing B.
- **`ArtifactRef.storage_ref`** refuses a `file:` scheme in any letter case, a
  drive-letter path, and any `..` segment.
- **Versions.** `SCHEMA_VERSION` becomes 2 (`Literal[2]`), and `VALIDATOR_VERSION`
  becomes `"2"`.
- **Compatibility.** Schema 1 records are refused. None has ever been persisted, so
  nothing needs migrating.

Kept out of core:
- **An alignment reason (SC13).** Plan B's `alignment_failed` is an ingestion status.
- **A `parser_version` field (SC8).**

### Verification (plan A)

1. **Port equality.** The ported walker's output equals the frozen walker's, element
   for element (type, text, parent, level, source type, and grid), on:
   - the eight fixtures;
   - the three development releases, when present locally. A missing release shows
     as a visible skip;
   - synthetic HTML for every construct the development set never exercised (V2):
     `pre`, `li`, `h1`–`h6`, `th`, `thead`, `caption`, `display: none`, symbol
     fonts, double `<br>`, and marker tables;
   - nesting deeper than the default recursion limit.

   The test lives beside the frozen harness in `expirements/parser-fidelity/` and runs
   under the harness command. No frozen file changes, and `freeze.py verify` still
   passes.
2. **Re-score.** Project `walker-1`'s elements back to the dump format:
   - `page_artifact` becomes `other`;
   - sentences fold back into their blocks;
   - cells fold back into their grids, rebuilt from cell positions.

   Then score the projection with the frozen `score.py`:
   - **Regressions:** no ranked metric may be worse than the frozen walker's in any
     class, compared on exact counts.
     - C1 is the exception, because R4.2 requires it: a regression it causes is
       accepted with its reason recorded, since R4.2 outranks a ranked metric.
     - A regression caused by C2–C5 is resolved at the review gate.
   - **Changes:** every change is listed by fixture and block.
   - **Page artifacts:** typing is reported against the gold's 97 `page_artifact`
     blocks. Their anchors need not be unique, so they are counted per anchor text,
     as a multiset. For each distinct anchor, the report gives:
     - the number of gold blocks with that anchor;
     - the number of canonical blocks whose text begins with it;
     - how many of those are typed `page_artifact`.

     Page artifacts that match no gold anchor are listed. No gold block is ever
     placed at a first match.

   These are development-set numbers.
3. **Golden master.** The canonical fixtures regenerate byte for byte.
4. **R3.1 and R4.1.**
   - Every fixture canonicalizes offline with a network guard installed.
   - `validate_elements` returns nothing.
   - Every element's span slices exactly its unit's text.
   - Hash and offset round trips hold.
5. **R4.2.** On every fixture, no narrative element (`heading`, `paragraph`,
   `list_item`, `footnote`, or `sentence`) overlaps a table's span. Positive
   controls keep this from passing vacuously:
   - the fixtures yield `table_cell` elements;
   - Pharmacyclics' `<pre>` statements yield only `table` pieces;
   - a synthetic prose `<pre>` piece stays a `paragraph`.
6. **R4.3.**
   - A synthetic OCR element makes `validate_span` refuse overlapping spans with
     `ocr_derived_text`.
   - Every fixture element is `native`.
   - Synthetic image-only HTML fails with `no_native_text` and its image count.
7. **V9 normalization.**
   - NFD input composes to NFC.
   - A no-break space becomes a space.
   - The soft hyphen, zero-width space, word joiner, BOM, and a C0 control are
     deleted.
   - "¹", "½", "ﬁ", and full-width digits are preserved.
   - The en dash, em dash, minus sign, and curly quotes are preserved.
   - U+FFFD is preserved and counted.
   - Whitespace collapses after deletion.
8. **V9 sentence splitting.**
   - One case for each abbreviation family.
   - Initials.
   - Decimals and currency ("$0.48.", "6.0%.").
   - a.m. and p.m.
   - Closing quotes and brackets.
   - Leading markers.
   - Enumerators.
   - The deliberate under-split ("… Acme Inc. The …").
   - A unit with no terminal punctuation.

   V9's Unicode inputs are built from code points in the test code, so no tool or
   editor can normalize them.
9. **Rules.** Each of C1–C5, M1–M5, and S1 has unit tests of positive and negative
   cases.
10. **R3.5.** Plan A's part of the report is committed (§R3.5 fidelity check). A test
    asserts that all six categories are present, each with an instance count or "no
    instances in sample".
11. **Suites.**
    - The default suite passes: `uv run --locked --all-packages pytest packages apps
      tests -m "not live"`.
    - The harness suite passes: `uv run --locked --all-packages pytest
      expirements/parser-fidelity --import-mode=prepend -q`.
    - Ruff passes.
    - `uv.lock` is unchanged, because plan A adds no dependency.

### Gates (plan A)

- **Approval.** Approving this spec approves C1–C5, N1, L1, S1, and M1–M5 as written.
- **Review gate.** After the canonical fixtures are first generated, and before they
  are committed, the user reviews:
  - **the mask report:** each fixture's masks, with every unmasked block containing
    "forward-looking" or "non-GAAP" flagged;
  - **the page-artifact report:** C2–C5's retypes against the gold's 97
    `page_artifact` blocks.
- **Amendments.** The user may amend an M or C rule at this gate.
  - Each amendment is recorded with its reason in plan A's verification record.
  - Numbers measured after it are labelled post-hoc.
  - `walker-1` and `boilerplate/1` are not yet published, so their names stay.

## Plan B — the browser diagnostic path

### Principle (SC14)

Plan B never changes canonical text:
- **Mapping.** Its layout extractor maps onto `walker-1`'s text.
- **Comparison.** Its comparison evaluates element streams over that text.
- **Promotion.** A promotion changes elements only. It is a new canonicalization
  version whose text hash is unchanged, so every existing offset carries over to the
  new `doc_id`.

### Dependencies and binaries (B3, B8)

- **The extra.** `earnings-ingestion[browser-capture]` holds Selenium, pinned in
  `uv.lock` at plan time.
- **Browser and driver.** Chrome for Testing and its matching chromedriver, at one
  pinned version. A committed browser manifest records the version, platform,
  download URL, and SHA-256 of each archive. The plan fixes its location.
- **Setup.** A separate setup command downloads and verifies them into a cache
  outside the repository. It never runs during a processing run.
- **No automatic downloads.** Captures pass an explicit driver path, so Selenium
  Manager never downloads anything.
- **Missing binaries.** Without them, a capture is `unavailable` with reason
  `browser_unavailable`.
- **Why Chrome for Testing.** It can be pinned, it has CDP for isolation, and the gold
  and the user's rendered copies came from Chrome. The installed Google Chrome
  auto-updates, which B3 rules out. Safari offers no request-blocking hook.

### Renderer and capture (B1, B2)

- **`BrowserRenderer.capture(saved_html, capture_policy) → RenderedCapture`.** A
  Selenium adapter implements it, and a fake renderer serves default tests.
- **What the capture records:**
  - `document.body.innerText`, and its hash;
  - layout metadata, and its hash. Per block, this is computed display, visibility,
    font weight and size, bounding box, and table-cell position;
  - content-hashed screenshots.
- **The browser spec's field list.** `RenderedCapture` also carries every field that
  list names: identity, raw hash, policy, versions, platform and render
  configuration, reported character set, policies, times, and status.
- **Storage.** Records are written atomically under `data/runs/` and never
  overwritten.
- **Cache key.** It covers:
  - the raw hash;
  - the capture policy version;
  - the browser and driver identities;
  - the platform and render configuration;
  - the extractor version.

  Timestamps are not part of it.
- **`LayoutExtractor.extract(rendered_capture)`** works offline from the saved
  metadata, so default tests can run it on small synthetic captures.
- **No span from a DOM offset.** Plan B builds every span by matching canonical text,
  never from a DOM offset. Stage 3 therefore converts no UTF-16 offsets (D-17); Stage
  10 converts at its highlight boundary.

### Capture policy `isolated/1` (B7)

- **Profile.** A fresh temporary profile, headless.
- **JavaScript.** Document JavaScript is disabled before navigation.
- **Requests.** Every http(s), ws, and ftp request is blocked and recorded.
- **Files.** The saved file is copied alone into an empty temporary directory and
  loaded from there.
- **Limits.** Startup, navigation, capture, and shutdown are bounded. The browser is
  killed after every batch, and processes are always cleaned up.
- **Status.**
  - A missing image, such as a logo, is recorded and does not downgrade the capture.
  - A missing stylesheet or font makes the capture `partial`.
  - Statuses are `completed`, `partial`, `failed`, and `unavailable`, with the
    browser spec's reasons.
  - A failure is never an empty successful capture.

### Checks

- **Markers.** Browser checks are opt-in, under a new `browser` marker. Plan B
  registers it in the root pytest configuration and deselects it by default beside
  `live`, as `-m "not live and not browser"`.
- **The documented command.** pytest keeps the last `-m` it is given, so the
  documented default command, with its `-m "not live"`, would override that setting
  and select the browser checks.
  - Plan B changes the documented command to `-m "not live and not browser"`
    wherever it appears: `CLAUDE.md`, `README.md`, and `AGENTS.md` line 206.
    `AGENTS.md` is edited in place, because it is cited by line number.
  - Every browser check also skips visibly when the pinned binaries are absent.
- **Network guard.** A synthetic page that requests an external image, stylesheet, and
  script shows every request blocked and recorded. An inline script that would
  rewrite text never runs, and its text is absent from the capture.
- **Determinism.** Two captures in the pinned environment have the same rendered-text
  hash.
- **Calibration.** Compare `innerText` with the user's `rendered.txt` copies:
  - Union Bankshares (narrative-only);
  - National Health Investors (table-bearing);
  - Ball (malformed layout).

  Differences are classified into the browser spec's eight kinds:
  - visible characters;
  - whitespace;
  - bullets;
  - CSS text transformation;
  - hidden content;
  - image alternative text;
  - table-cell separation;
  - reading order.

  The rendered copies are calibration observations, not gold, and no gold changes.

### Layout extractor `layout-1` and alignment (B5, SC13)

- **What it types.** `layout-1` types candidate blocks from computed style and
  geometry. For example:
  - a short block whose every character is bold becomes a `heading`;
  - a table row whose single non-empty cell spans the table and holds prose becomes a
    `paragraph`, `heading`, or `footnote`, as W8–W12 would type it;
  - text with no visible counterpart becomes `other`.
- **Mapping.** Each candidate maps onto `walker-1`'s canonical text:
  - exactly, after N1, through a deterministic, reversible whitespace map;
  - disambiguated by the text of neighbouring blocks;
  - never by first match, and never by a fuzzy score.
- **Failure.** A missing mapping is `alignment_failed` carrying the core reason
  `locator_not_found`. An ambiguous one is `alignment_failed` carrying
  `ambiguous_occurrence`.
- **The two-parser contract** in `tests/contracts/test_element_schema_parsers.py`
  (D-15) reruns with the real pair: `walker-1` as the canonicalizing parser and
  `layout-1` as the mapping reader.

### Pre-registered comparison

This section fixes, before any measurement, what the browser spec's promotion rule
requires.

- **Versions.** The Selenium, Chrome for Testing, and chromedriver versions pinned at
  plan time; capture policy `isolated/1`; the mapping policy above; and `layout-1`.
- **Targeted residual classes:**
  1. headings typed `paragraph` by W12 (23 in V2), including W11's blind spots: the
     `font` shorthand, stylesheet classes, and `th`;
  2. prose inside data tables: titles, contacts, notes, and footnotes (49 merged
     blocks and 19 lost headings in V2);
  3. content hidden by stylesheets.
- **Metrics.** Reported for each of the four fixture classes, on the frozen gold, with
  the frozen scorer's definitions:
  - block coverage;
  - reading order;
  - heading loss;
  - footnote merging;
  - table-header retention;
  - cell association;
  - altered anchors;
  - alignment failures.
- **Configurations.** Three are compared:
  1. `walker-1`, with C1–C5;
  2. `layout-1` for every document;
  3. the fallback below.
- **Exact comparison.** All comparisons use exact integer counts. Plan B does not
  reuse `select_parser.py`.
- **Repair and regression.**
  - A class is repaired when a configuration loses strictly fewer of its gold units
    than `walker-1`.
  - A regression is any metric worse than `walker-1`'s by more than 1/n in any class,
    where n is that class's count.
- **Fallback activation.** This is outcome 2 of the promotion rule. A document switches
  to the `layout-1` element stream when `walker-1`'s output shows either trigger:
  1. no `heading` element at all;
  2. a data-table row whose only non-empty cell holds more than 12 words.

  The triggers are read from `walker-1`'s recorded output, and the manifest records
  which one fired.

### Promotion decision

- **ADR 0002** records one outcome of the browser spec's promotion rule:
  1. diagnostic-only capture;
  2. the fallback above, as `walker-2`;
  3. `layout-1` for every document, as a new version.

  It names the activation policy, the versions, the measured benefit, the regressions,
  and the consequence for the canonicalization version.
- **Condition for promotion.** Outcome 2 or 3 requires repairing at least one targeted
  class with no regression.
- **Cost of promotion.** Any promotion makes a browser capture an input to
  canonicalization for every document the new version covers, including Stage 5's
  and Stage 15's releases. `layout-1`'s geometry also needs the pinned platform and
  font set.
  - ADR 0002 weighs that cost beside the metrics.
  - It states how the promoted canonicalizer receives each document's capture.
  - The promoted canonicalizer fails explicitly without a capture. It never falls
    back to `walker-1` under the new version's name (the browser spec's
    §Reproducibility and failure handling).
- **After promotion.** The fixtures are re-canonicalized under the new version before
  Stage 6 annotation. `walker-1` documents and fixtures are never rewritten.

### Import boundaries

The static scan deferred from plan 3 lands with the extra.

- **What it scans.** An AST scan of every package's `src/`, including imports inside
  functions.
- **What it refuses:**
  - sibling-package imports that break the dependency table in `CLAUDE.md`;
  - browser imports (Selenium, Playwright, pyppeteer) everywhere except
    `earnings_ingestion`'s browser module.
- **The runtime check stays.** `import earnings_ingestion` must still load no browser
  package.

### Verify at plan time

Stop and report if any of these fails:
- WebDriver can still read `innerText` and layout metadata with document JavaScript
  disabled;
- CDP request blocking covers every scheme a saved page can reach;
- the pinned Chrome for Testing build exists for macOS arm64.

## R3.5 fidelity check

- **Independence.** The check does not depend on the canonicalizer. Its references
  come from the Chrome rendering and from the standard library's `html.parser`,
  never from lxml or the walker.
- **Comparison space.** It compares in NFC with whitespace runs collapsed, not in
  NFKC, which would hide the Unicode and superscript differences the check exists to
  find.
- **No thresholds.** It counts and lists, and sets no threshold (R13.1).

| Category | Plan A reference (committed) | What is counted |
| --- | --- | --- |
| Unicode | gold anchors and table header texts | Non-ASCII characters in the references, found identically in the canonical text, and the manifest's U+FFFD count. The fixtures are pure ASCII, so the report says "no instances in sample" and cites V9's synthetic cases. |
| Numeric signs | gold anchors | Figures with a sign (parentheses, a leading hyphen, en dash, or minus sign, or a plus) found with the sign intact. |
| Scale | gold anchors and table header texts | Scale phrases ("in millions", "in thousands", "in billions", "except per share"), counted per phrase: occurrences in the references against occurrences in the canonical text. |
| Superscripts | `<sup>` runs read by `html.parser` from `source.html` | Each run is located in the canonical text by the fewest surrounding words of source text that make its occurrence unique, as `make_locator` grows context (D-4). A run that no context singles out is reported as unlocatable, never placed at a first match. Each located run is classed as an ordinal suffix, a parenthesized marker, a symbol, empty, or bare digits. A bare-digit run joined to a number, such as "million" plus a raised "1", is a fidelity hazard. The fixtures have none, so it is tested synthetically and watched on the pilot releases. |
| Footnotes | gold footnote blocks | The frozen scorer's footnote-merging count on the item-2 projection: footnotes typed `footnote`, against footnotes merged into another element. |
| Table headings | gold table header texts | The frozen scorer's table-header count on the item-2 projection. It locates gold tables by their anchors, and an unanchorable gold table is counted as unlocated, as in V2. For each located table, the report adds whether each found header text sits in a header cell; C1 tables have none. |

The report is built in two legs:
- **Plan A** commits it as `docs/verification/R3.5-text-fidelity.md`.
- **Plan B** adds a second leg. It compares canonical text with full `innerText`
  captures and with the user's `rendered.txt` copies, through a whitespace-insensitive
  token diff, and classes each differing hunk into the six categories or `other`. The
  report is then final.

## V2 disposition

This table records, for Stage 3, every finding from V2's "Residual failures (for
Stage 3)", "Findings for Stage 3", and "Notes on ADR 0001 after acceptance". It also
covers ADR 0001's negative consequences, the walker's Known gaps and side effects,
and the final code review's items. Every row is compensated, targeted, recorded as a
limitation of `walker-1`, or needs no action.

| Finding | Disposition |
| --- | --- |
| Split: 25 text blocks in six fixtures (page-break paragraphs, two-line headings, others) | Limitation |
| Merged: titles, contacts, notes, and footnotes set inside data tables (49 blocks) | Plan B target 2 |
| Misordered: Becton Dickinson t012's pair | No action: the gold produces it, and every candidate has it |
| 23 headings typed `paragraph` by W12, including W11's blind spots (`font` shorthand, stylesheet classes, `th`) | Plan B target 1 |
| 19 headings inside table elements | Plan B target 2 |
| 2 year subheadings typed `other` by W8 (Ball) | Limitation: C3 keeps them `other` |
| 1 heading typed `list_item` by W9 (Pharmacyclics b007) | Limitation |
| 12 table header texts in Pharmacyclics' `<pre>` tables | C1: typed `table`, with their text kept and no header cells (limitation) |
| 2 of Southwestern Energy t012's 10 header texts | Limitation |
| Body text typed as headings (12 of 313), and W11's short bold sentences and underlined URLs | Limitation |
| Tables drawn in `<pre>` are not exposed as tables | C1 |
| edgartools' press-release path decodes with `errors="replace"` | Compensated: the canonicalizer decodes bytes itself, before parsing |
| Encoding coverage: every fixture is ASCII | V9 synthetic cases; R3.5 reports "no instances in sample" |
| Hidden content detected only from hidden tags and inline `display: none` | Plan B target 3; a limitation of `walker-1` |
| `walker.parse` raises the global recursion limit | Compensated by the port (proven equal) |
| `tfoot` rows read in source order | Limitation |
| Encoding labels outside the short list use `codecs.lookup`, not WHATWG | Limitation, documented by a synthetic test |
| The class tests count a nested page-number block twice | No action: the class tests are not ported |
| Known gap: a paragraph split by a page break | Limitation |
| Known gap: "Page N of M" is a paragraph | C4 |
| Known gap: the EDGAR header line is a paragraph | C2 |
| Known gap: a centred "##" end mark is a paragraph | Limitation |
| Known gap: a title set apart only by position, alignment, or capitals | Plan B target 1, from computed style; a limitation of `walker-1` |
| Known gap: a two-line heading becomes two headings | Limitation |
| Known gap: a second set of column headers partway down a table | Limitation; it affects cells' header references |
| Known gap: a footnote set as a data table's last row | Limitation |
| W15 flags stub labels such as "ASSETS:" as header rows | Limitation; it affects cells' header references |
| The development set never exercised `pre`, `li`, `h1`–`h6`, `th`, `thead`, `caption`, `display: none`, symbol fonts, double `<br>`, or marker tables | Exercised by the port-equality synthetic cases |
| Page numbers kept as `other`, and W8's pattern also takes four-digit years | C3 |
| The walker's script header lists beautifulsoup4, which it never imports | No action: the port imports only lxml |
| ADR 0001's "Fast." includes library import time | The deferred item stays open (§Deferred items) |
| Altered anchors: none | Nothing inherited |

## Deferred items

| Item in `specs/deferred_items.md` | Disposition |
| --- | --- |
| `3-core-evidence-spine`: Validate `MaskedDocument` itself | Closed by plan A's core change |
| `3-core-evidence-spine`: Recheck construction-only invariants in `validate_elements` | Closed by plan A's core change |
| `3-core-evidence-spine`: Report every crossing in `validate_elements` | Closed by plan A's core change |
| `3-core-evidence-spine`: Close D-12's portability gaps in `ArtifactRef.storage_ref` | Closed by plan A's core change, before Stage 4 persists an `ArtifactRef` |
| `3-core-evidence-spine`: Check import boundaries statically as well | Closed by plan B, with the `browser-capture` extra |
| `1-release-parser-fidelity`: Carry V2's findings into Stage 3 | Recorded by §V2 disposition; ticked at plan A's completion |
| `1-release-parser-fidelity`: Time parsers without their imports | Stays open: no Stage 3 design choice relies on parser speed |
| `1-release-parser-fidelity`: Compare exactly if the selection rule is reused | Stays open: plan B compares exact counts itself and does not reuse `select_parser.py` |
| `1-release-parser-fidelity`: Keep `EDGAR_IDENTITY` out of the lock gate's adapter processes | Stays open: Stage 3 does not rerun the lock gate |
| `3-core-evidence-spine`: the `VerifiedSpan`, `resolve_pointer`, unvalidated-offset, and `Rejection`-subject items | Stay with Stage 7 |

## Handoffs from plan 3, answered

| Plan 3 Handoff to Stage 3 | Answer |
| --- | --- |
| 1. Rerun the two-parser contract with the real pair | Plan B, §Layout extractor |
| 2. Alignment failures | SC13: an ingestion status carrying `locator_not_found` or `ambiguous_occurrence` |
| 3. R4.2's narrative and cell rule as the exit test | §Verification (plan A), item 5 |
| 4. Table grids | §Tables and cells; `<pre>` tables have no grid (C1) |
| 5. Version naming | SC8, §Versions and the manifest |
| 6. Boilerplate policy | §Boilerplate masks M1–M5 |
| 7. Page artifacts | C2–C5: typed, excluded from eligibility by type, never masked |
| 8. UTF-16 conversion at the browser boundary | Not needed in Stage 3: no span comes from a DOM offset. Stage 10 converts at its highlight boundary. |
| 9. Browser records stay in ingestion | Plan B, §Renderer and capture |
| 10. V9's remaining cases | §Verification (plan A), items 7–8 |
| 11. Plan 1's deferred item | §V2 disposition |

## Exit criteria

### Plan A — the roadmap's Stage 3 Exit

1. The ported walker equals the frozen walker (§Verification (plan A), item 1).
   `walker-1`'s re-score shows no regression on exact counts, apart from any recorded
   C1 regression, and page-artifact typing is reported (item 2).
2. Every Stage 1 fixture canonicalizes offline and passes `validate_elements`, and the
   canonical fixtures regenerate byte for byte (R3.1, R4.1).
3. The R4.2 test passes with its positive controls.
4. The R4.3 test passes.
5. V9's normalization and sentence-splitting cases pass.
6. The R3.5 report covers all six categories and is committed.
7. The schema 2 core change lands, closing four deferred items with tests, and the data
   dictionary's drift test passes.
8. The review gate is passed, with any amendments recorded.
9. The default suite, the harness suite, and Ruff pass, and `uv.lock` is unchanged.

### Plan B — the browser spec's Stage 3 verification

1. The browser extra, the pinned binaries, and the setup command exist, and no
   processing run downloads anything.
2. Automated calibration covers the three named fixture categories and publishes
   classified differences, without altering gold.
3. A network guard proves that capture makes no external request and that source
   JavaScript cannot execute.
4. Two captures in the pinned environment have the same rendered-text hash.
5. `layout-1` candidates resolve to exact canonical spans or carry
   `alignment_failed`, and the two-parser contract reruns with the real pair.
6. The pre-registered comparison reports every named metric and targeted class for
   the three configurations.
7. ADR 0002 is accepted. On promotion, the fixtures are re-canonicalized under the new
   version.
8. The R3.5 report is final.
9. The AST scan and the runtime boundary checks pass.
10. The default suite, run by the updated documented command, needs no browser and
    makes no network request. Browser checks run only with `-m browser`, skip visibly
    without the pinned binaries, and record the exact environment.

## Handoffs to later stages

| Stage | Receives |
| --- | --- |
| 4 | The schema 2 contracts, with `storage_ref` portability closed |
| 5 | `canonicalize` for content inspection (R1.2, R1.5); its failures as processing states (R1.4); the manifest's raw hash; the R3.5 check, to rerun on the pilot releases; C2's recognition of EDGAR's header line |
| 6 | Canonical versions to bind gold spans to; annotation waits for ADR 0002; a promotion keeps `walker-1`'s text, so offsets carry over to the new `doc_id` unchanged |
| 7 | The committed canonical fixtures; element types to decide eligibility from, where `table`, `table_cell`, `page_artifact`, and `other` are never narrative; sentences as the pointer unit; masked elements stay in traversal; `validate_span` refuses OCR text |
| 10 | `MaskedDocument` for the headline exclusion; plan B's public `BrowserRenderer` for V5's target-browser checks and screenshot fallback; UTF-16 conversion at its own boundary |
| 13 | `text_origin` and schema 2; speaker metadata still waits (D-16) |

## Rollout

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 3 — on
> plan completion, tick the stage and re-validate later stages against what
> shipped.

"Plan completion" above means plan B's. Plan A's completion does not tick Stage 3.

- **On plan A's completion,** append this line, with the plan's ID and path:

  ```text
  > Plan A: COMPLETE (YYYY-MM-DD) — implemented by plan <id> (<path>). Next: write plan B.
  ```

- **On plan B's completion,** append the stage stamp, with both plans' IDs and paths:

  ```text
  > Stage 3: COMPLETE (YYYY-MM-DD) — implemented by plans <A id> (<path>) and <B id> (<path>).
  > Next: resume the roadmap.
  ```

  The roadmap reconcile then:
  - ticks Stage 3;
  - adds §Exit criteria's plan B list to the roadmap's Stage 3 Exit;
  - re-validates the later stages.

Sequencing:
- Stage 4 depends only on Stage 2, and may be planned after plan A.
- Stage 5 needs plan A.
- Stage 6 annotation waits for ADR 0002.

On each plan's completion, refresh the "Current state" section of `CLAUDE.md`. In the
handoff, state which commands ran, that no model was called, and whether any
`browser` or `live` check ran.
