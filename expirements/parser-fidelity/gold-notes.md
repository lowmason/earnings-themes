# Gold marking notes

The annotator writes one section per fixture while marking (specs/release-parser-fidelity.md,
Gold annotation). The V2 record's gold protocol and its element-nesting section, which
Stage 2 needs, are drawn from these notes. No candidate output is consulted while marking.

There are two rounds. The first eight sections are round 1's, kept as the record of that
gold; its drafts and snapshots have moved to `data/runs/parser-fidelity/round1/gold-drafts/`.
At gate D (2026-09-24) the user replaced all eight fixtures, and round 2's sections follow in
the same form. Their validator lines were filled in from the validator's output: every
round-2 fixture is ASCII.
As in round 1, Claude wrote the sections from the committed gold files and the gate-B checks, at
the user's request; the times are the user's.

## 0000003370-05-000209_ex-99

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000003370-05-000209_ex-99.codex.toml`
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 1 (60 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: the seven tables are drawn with spaces inside `<pre>`, so each `table` block's headers and L come from text lines, and P7's grid checks cannot apply to them. Conventions: the EDGAR filing header, the "(FIKN)" line and the "_________________" rule are `page_artifact`s.

## 0000004904-24-000080_ex-99

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000004904-24-000080_ex-99.codex.toml`
- Unanchorable tables in the Codex draft: 5 of 7 (t001–t004, t006). The brief's table rule at the time (cells only from rows with no `$` or parentheses) was stricter than the spec's, so each flag was checked against the spec, with grids built from the page's cells and counts from the validator's text. All 5 stand: none has an L of three unique values that are not split across cells.
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 1.5 (90 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: one HTML table holds two visible tables (GAAP and operating earnings), marked as t002 and t003. Titles outside the HTML tables are headings: "AMERICAN ELECTRIC POWER" through "Preliminary, unaudited results" (b017), and "SUMMARY OF RESULTS BY SEGMENT" runs through its "$ in millions" units line (b026). Six of the eight tables are unanchorable: their values recur, so no L of unique cells exists. 13 footnotes are unanchorable: each text recurs in the other reconciliation, and each is followed directly by the next footnote's marker, which no anchor, `after` included, may contain. Six other footnotes are anchored with `after` set to the page number that follows them, so they are found only where a parser keeps page numbers in place. Conventions: the EDGAR filing header and the "---" separator are `page_artifact`s.

## 0000049071-06-000012_ex-99

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000049071-06-000012_ex-99.codex.toml`. This is Codex's second draft; the first, and the user's partial hand-marking from before it, are set aside in `data/runs/parser-fidelity/set-aside/`
- Unanchorable tables in Codex's first draft: 10 of 22. The brief's table rule at the time (cells only from rows with no `$` or parentheses) was stricter than the spec's. Checked against the spec, with grids built from the page's cells and counts from the validator's text, 7 of the 10 have a valid L (t001, t002, t004–t008) and 3 have none (t003, t019, t022). Codex re-drafted Humana under the corrected brief (f61e11e), in the same Codex session as the first draft. The second draft flags only t003, t019 and t022, and every anchored table's L passes the same check.
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 2 (120 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: prose inside table grids (the introductory sentences of t017, t019 and t020, and the DCP paragraph of t021) is marked as `paragraph` blocks placed immediately before their tables. The schema cannot put a paragraph between a table's title rows and its body; reading order uses only the L cells, so this placement is exact for scoring. Several visible tables share one HTML table: t009–t013, t019–t020 and t021–t022. t018's rows are keyed by letters in their own cells ("A"–"F"), so `row_header` records the letter, the row's first cell. Three tables are unanchorable (t003, t019, t022). Conventions: in-grid title and units lines, including "Humana Inc.", are listed in `headers`; the EDGAR filing header is a `page_artifact`.

## 0000068270-05-000104_ex-99

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000068270-05-000104_ex-99.codex.toml`
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.5 (30 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: the title lines above the table are headings (b002, b003), one per `<H1>` on the page. Each date header cell holds two lines ("August 30," and "2005") and is listed as one header. Conventions: the EDGAR filing header is a `page_artifact`.

## 0000315449-18-000009_ex-99-1

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000315449-18-000009_ex-99-1.codex.toml`
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.5 (30 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: the statement titles, with their "(derived from …)" lines, sit outside the HTML tables and are headings (level 3) under the "Source: UQM Technologies, Inc." heading (level 2). The balance sheet (t002) spans two HTML tables. The contact block is a layout table: its label is a heading, each contact is one paragraph, and "or" is a paragraph anchored with `after`. Conventions: the EDGAR filing header, the running page footers, and the end marks "###Tables Attached###", "#End Table" and "# End #" are `page_artifact`s.

## 0000859163-17-000071_ex-99-1

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000859163-17-000071_ex-99-1.codex.toml`
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.5 (30 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: the statement titles, with their "(unaudited)" and units lines, sit outside the HTML tables and are headings (b015, b016). Conventions: the EDGAR filing header is a `page_artifact`.

## 0001104659-23-049001_ex-99-1

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0001104659-23-049001_ex-99-1.codex.toml`
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.5 (30 minutes)
- Tables inside lists or inside other tables: none; the release has no tables
- Structure the gold schema cannot express: none. Conventions: the EDGAR filing header is a `page_artifact`.

## 0001572910-14-000003_ex-99-1

- Draft: none; marked by hand (no Codex draft)
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.25 (15 minutes)
- Tables inside lists or inside other tables: none; its only HTML table is a layout table holding the "Exhibit 99.1" label
- Structure the gold schema cannot express: conventions chosen here: the EDGAR filing header shown at the top of the page is a `page_artifact`; the `- # # # -` end mark is a `page_artifact`; each contact line is its own `paragraph` under a `CONTACTS` heading.

## 0000007332-09-000032_ex-99

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000007332-09-000032_ex-99.codex.toml`; original prompt
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.5 (30 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: the company line "Southwestern Energy Company and Subsidiaries" at the top of each financial-summary page is a `page_artifact` (p015–p023). In the page's text it follows the page number ("Page N of 5"), so a statement heading running through it could not be anchored: an `end` on the company line alone repeats on all five pages, and extending it back would take in the page number, another block's text. The statement titles are level-2 headings (b067, b069, b070, b073, b074). Four tables are unanchorable (t003, t004, t006, t007): their values recur, so no L of unique cells exists. t005's corner and right record the values without the "$ " that shares their cells, while t010's cells include it. Conventions: the EDGAR filing header, the "- MORE -" page breaks, the "Page N of 5" numbers and the "# # #" end mark are `page_artifact`s.

## 0000037785-14-000003_ex-99-1

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000037785-14-000003_ex-99-1.codex.toml`; original prompt
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.5 (30 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: the titles above the financial tables are level-2 headings, most beginning "FMC CORPORATION AND CONSOLIDATED SUBSIDIARIES" (b056, b057, b062, b076, b079, b088, b089). t005's L is in the table's second section (110.3 / 539.0 / 35.6), the only L in the table that meets every rule; the draft's L (492.4 / 2,145.7 / 168.1) had its corner and right split from their `$` cells. Claude identified it at the user's request. Four blocks are unanchorable: b024 (the "2014 Outlook" heading) and b059 (a footnote) are each followed directly by a marker, so no `after` can locate them, and t003 and t004 have no L of unique cells. Conventions: the EDGAR filing header, the "-more-" page breaks, the "Page N/ FMC Corporation Announces Fourth Quarter Results" running headers, the row of asterisks, the "____" rules above footnotes (b058, b063, b077, b080, which keep their `b` ids) and the "# # #" end mark are `page_artifact`s.

## 0000009389-10-000004_ex-99-1

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000009389-10-000004_ex-99-1.codex.toml`; original prompt
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.5 (30 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: t005, the reconciliation of net earnings, has no L that meets every rule: its values that occur once all sit in rows whose `$` has a cell of its own, and its other values recur or have their ")" in a cell of their own. Codex's L (80.3 / 53.4 / 0.84) is kept, so each of its cells is split from its `$`, against the spec's split rule, and the table is scored. The note-2 heading "Business Consolidation Activities and Other Significant Items" (b042) is located with `after`, as Codex drafted it, because its whole text recurs in the "(cont'd)" heading (b056); the "2009" and "2008" subheadings (b043, b052) also use `after`. The note numbers "1.", "2." and "3." are left outside their headings' anchors. The logo's alt text, "Ball Logo", gets no block. Conventions: the EDGAR filing header, the "- more -" page breaks, the "Ball Corp - N" running headers, the Broomfield address footer, the "Condensed Financials (December 2009)" and "Unaudited Notes to Condensed Financials (December 2009)" running headers and the "# # #" end mark are `page_artifact`s.

## 0000010795-22-000014_ex-99-1

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000010795-22-000014_ex-99-1.codex.toml`; original prompt; the snapshot includes the header, which the user filled in while Codex was drafting
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.5 (30 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: the title lines above the nine financial tables sit outside the HTML tables and are level-2 headings (b063–b070, b077), each running from "BECTON DICKINSON AND COMPANY" to the last title line above the grid; Codex had listed them in the tables' `headers`. Period lines drawn inside a grid, as in t004 and t011, stay headers. Three tables keep Codex's L although it breaks the spec's L rules: t005 (corner and right each split from a `$` cell, although 8 L's without split cells exist), t007 (the same split, and no L in the table meets every rule) and t012, the FY 2022 outlook reconciliation. t012 has no row with two values, so no L shape exists: its three cells (20,248, "+5.75% to +6.75%" and 1,956) are unique but do not form an L, and 20,248 is split from its `$`. Every value in t012 occurs once, so `unanchorable` is not available to it. 13 blocks are unanchorable: seven tables whose values recur (t001–t003, t009–t011, t013) and six footnotes (b071–b073, b079–b081), each followed directly by the next footnote's marker. Conventions: the EDGAR filing header, the "***" separator and the "Page N" numbers are `page_artifact`s.

## 0000092380-07-000011_ex-99-1

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000092380-07-000011_ex-99-1.codex.toml`; stricter prompt (read the brief in full before running any other command)
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.5 (30 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: the statement titles are level-2 headings beginning "SOUTHWEST AIRLINES CO." (b024, b025, b029–b032). b024 and b025 run through the units line "(in millions, except per share amounts) (unaudited)", which appears under both, so their `end`s begin inside the statement names. Three tables are unanchorable (t002, t005, t006): no L of unique cells exists; in t006, the 737-700 delivery schedule, no value occurs only once in the document. The delivery-schedule footnotes use "*" and "**" markers. Conventions: the EDGAR filing header, the "/more" page breaks and the "***" end mark are `page_artifact`s.

## 0000877860-13-000100_ex-99-1

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000877860-13-000100_ex-99-1.codex.toml`; stricter prompt (read the brief in full before running any other command)
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.25 (15 minutes)
- Tables inside lists or inside other tables: none
- Structure the gold schema cannot express: the four statement titles are level-2 headings that run through their units lines (b025, b028, b031, b032). In b025 and b028, the FFO and FAD reconciliations, the footnote references "(1)(2)" sit between the title and its units line, and both anchors include them, against the spec's marker rule (no anchor includes or skips a footnote marker). Without them no `end` can reach the units line, which occurs three times. The validator checks markers only at the start of an anchor, so it does not flag these. Three tables are unanchorable (t001–t003): no L of unique cells exists. Conventions: the EDGAR filing header, the second "Exhibit 99" label and, on pages 3–6, the running header ("NHI Reports 17.2% Increase in Third Quarter Normalized FFO"), the date ("November 4, 2013") and the "Page N" numbers are `page_artifact`s.

## 0000706863-16-000110_ex-99-1

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000706863-16-000110_ex-99-1.codex.toml`; stricter prompt (read the brief in full before running any other command)
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.75 (45 minutes)
- Tables inside lists or inside other tables: none; the release has no data tables. Its HTML tables lay out the bullet lists and three paragraphs, which are marked as list items and paragraphs
- Structure the gold schema cannot express: none. Conventions: the EDGAR filing header is a `page_artifact`, and the "Exhibit 99.1" label is a heading (b002).

## 0000949699-08-000023_ex-99-1

- Draft: Codex draft (F9), from the rendered text, verified by the user; snapshot `data/runs/parser-fidelity/gold-drafts/0000949699-08-000023_ex-99-1.codex.toml`; stricter prompt (read the brief in full before running any other command)
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.25 (15 minutes)
- Tables inside lists or inside other tables: none; its only HTML table is a layout table holding the contacts, and its two data tables are drawn with spaces inside `<pre>`
- Structure the gold schema cannot express: the two tables are drawn with spaces inside `<pre>`, so each `table` block's headers and L come from text lines, and P7's grid checks cannot apply to them. The statement titles are headings: b029 runs from "Pharmacyclics, Inc. (a development stage enterprise)" through "(unaudited) (in thousands, except per share data)", and b033 is "Condensed Balance Sheets (unaudited, in thousands)". Conventions: the EDGAR filing header, "---FINANCIALS ATTACHED---" and the "###" end mark are `page_artifact`s.
