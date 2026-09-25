# Gold marking notes

The annotator writes one section per fixture while marking (specs/release-parser-fidelity.md,
Gold annotation). The V2 record's gold protocol and its element-nesting section, which
Stage 2 needs, are drawn from these notes. No candidate output is consulted while marking.

There are two rounds. The first eight sections are round 1's, kept as the record of that
gold; its drafts and snapshots have moved to `data/runs/parser-fidelity/round1/gold-drafts/`.
At gate D (2026-09-24) the user replaced all eight fixtures, and round 2's sections follow in
the same form. Their validator lines were filled in from the validator's output: every
round-2 fixture is ASCII.

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

- Draft:
- Browser and version:
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000037785-14-000003_ex-99-1

- Draft:
- Browser and version:
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000009389-10-000004_ex-99-1

- Draft:
- Browser and version:
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000010795-22-000014_ex-99-1

- Draft:
- Browser and version:
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000092380-07-000011_ex-99-1

- Draft:
- Browser and version:
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000877860-13-000100_ex-99-1

- Draft:
- Browser and version:
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000706863-16-000110_ex-99-1

- Draft:
- Browser and version:
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000949699-08-000023_ex-99-1

- Draft:
- Browser and version:
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:
