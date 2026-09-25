# Bespoke walker rules

Status: approved by Lowell Mason on 2026-09-22, before development began.

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

- A paragraph that a page break interrupts is two blocks, one on each side of the
  break, so it is emitted as two paragraphs (seen in the development releases
  0000079958-12-000020_ex-99-1 and 0001045150-09-000060_ex-99-1)
- A "Page N of M" footer is a `paragraph`: W8's bare page-number pattern has no
  "of M" form (seen in the development release 0001045150-09-000060_ex-99-1)
- The EDGAR filing header line at the top of the page ("EX-99.1 2 <file>.htm PRESS
  RELEASE") is a `paragraph` (seen in the development releases
  0000019149-11-000022_ex-99-1, 0000079958-12-000020_ex-99-1 and
  0001045150-09-000060_ex-99-1)
- A centred "##" mark closing a section is a `paragraph` (seen in the development
  release 0000079958-12-000020_ex-99-1)
- A title or exhibit label set apart only by position, alignment, or capitals, with
  no bold or underline, is a `paragraph`: the centred release title and the
  right-aligned "Exhibit 99.1" (seen in the development release
  0000019149-11-000022_ex-99-1), and "EXHIBIT 99.1" above the address block (seen in
  the development release 0001045150-09-000060_ex-99-1)
- A heading whose text runs over two lines, each line its own block, is emitted as
  two headings: "PRECISION CASTPARTS CORP. REPORTS" and "FISCAL 2013, FIRST QUARTER
  RESULTS" (seen in the development release 0000079958-12-000020_ex-99-1)
- A second set of column headers partway down a data table is not flagged as header
  rows, because W15 flags only `thead` rows, all-`th` rows, and leading rows (seen in
  both data tables of the development release 0000079958-12-000020_ex-99-1)
- A footnote set as the last row of a data table stays in the table's grid (seen in
  both data tables of the development release 0000079958-12-000020_ex-99-1)
