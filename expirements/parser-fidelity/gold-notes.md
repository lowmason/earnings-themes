# Gold marking notes

The annotator writes one section per fixture while marking (specs/release-parser-fidelity.md,
Gold annotation). The V2 record's gold protocol and its element-nesting section, which
Stage 2 needs, are drawn from these notes. No candidate output is consulted while marking.

## 0000003370-05-000209_ex-99

- Draft:
- Browser and version:
- Validator encoding and basis:
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII):
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000004904-24-000080_ex-99

- Draft:
- Unanchorable tables in the Codex draft: 5 of 7 (t001–t004, t006). The brief's table rule at the time (cells only from rows with no `$` or parentheses) was stricter than the spec's, so each flag was checked against the spec, with grids built from the page's cells and counts from the validator's text. All 5 stand: none has an L of three unique values that are not split across cells.
- Browser and version:
- Validator encoding and basis:
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII):
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000049071-06-000012_ex-99

- Draft:
- Unanchorable tables in Codex's first draft: 10 of 22. The brief's table rule at the time (cells only from rows with no `$` or parentheses) was stricter than the spec's. Checked against the spec, with grids built from the page's cells and counts from the validator's text, 7 of the 10 have a valid L (t001, t002, t004–t008) and 3 have none (t003, t019, t022). Codex re-drafted Humana under the corrected brief (f61e11e), in the same Codex session as the first draft. The second draft flags only t003, t019 and t022, and every anchored table's L passes the same check.
- Browser and version:
- Validator encoding and basis:
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII):
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000068270-05-000104_ex-99

- Draft:
- Browser and version:
- Validator encoding and basis:
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII):
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000315449-18-000009_ex-99-1

- Draft:
- Browser and version:
- Validator encoding and basis:
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII):
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0000859163-17-000071_ex-99-1

- Draft:
- Browser and version:
- Validator encoding and basis:
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII):
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0001104659-23-049001_ex-99-1

- Draft:
- Browser and version:
- Validator encoding and basis:
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII):
- Time spent (hours):
- Tables inside lists or inside other tables:
- Structure the gold schema cannot express:

## 0001572910-14-000003_ex-99-1

- Draft: none; marked by hand (no Codex draft)
- Browser and version: Google Chrome Version 154.0.8037.58 (Official Build) (arm64)
- Validator encoding and basis: UTF-8 (basis: valid-utf-8; every byte is ASCII, so any browser encoding agrees)
- `document.characterSet` in the browser (skip if the validator says every byte is ASCII): skipped; every byte is ASCII
- Time spent (hours): 0.25 (15 minutes)
- Tables inside lists or inside other tables: none; the release has no tables
- Structure the gold schema cannot express: conventions chosen here: the EDGAR filing header shown at the top of the page is a `heading`; the `- # # # -` end mark is a `page_artifact`; both contacts form one `paragraph` under a `CONTACTS` heading.
