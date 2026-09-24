# V1: edgartools 5.58.0 return types

This record discharges V1, the open marker in R14.5 of
`specs/evidence-linked-theme-extraction.md`, for Stage 1 of
`specs/evidence-linked-theme-extraction-roadmap.md`.

**Conclusion:** R14.5 cast required for: Document.to_dataframe(); EarningsRelease.to_facts_dataframe(); EightK.get_balance_sheet(); EightK.get_cash_flow_statement(); EightK.get_income_statement(); EntityFilings.data; EntityFilings.to_pandas(); FinancialTable.dataframe; FinancialTable.per_share_rows; FinancialTable.scaled_dataframe; TableNode.to_dataframe()

## Run

- Command: `uv run --locked --script expirements/parser-fidelity/v1_return_types.py --live`
- Date (UTC): 2026-09-24
- Library: edgartools 5.58.0, pinned in `expirements/parser-fidelity/v1_return_types.py.lock`;
  Python 3.14.0
- Filings: the eight fixture filings listed in `tests/fixtures/releases/manifest.toml`
- Live requests: 28
- Script: `expirements/parser-fidelity/v1_return_types.py` at commit `9fce0b2`

## Rate-limit mechanism

edgartools 5.58.0 reads `EDGAR_RATE_LIMIT_PER_SEC` once, at import (`edgar/httpclient.py`,
default 9), and builds a per-process pyrate-limiter bucket from it. That bucket averages
the configured rate, but it allows two back-to-back requests and counts nothing. The V1
script therefore sets `EDGAR_RATE_LIMIT_PER_SEC=2`, and it also sends every request
through the Stage 1 fetcher's throttle. The throttle wraps `httpx.HTTPTransport` and
`httpx.AsyncHTTPTransport`, spaces request starts at least 0.5 s apart, caps the run at
500 requests, and counts every request.

The same wrapper applies the live-fetch policy's stops, because edgartools' own client
does not stop on a 403: the second 403 in a run, a 429, or the request cap stops the run.
The stop is sticky, so every later request is refused before it is sent, and the script
reports `STOPPED` with its request count instead of results. The guard was added in
`9fce0b2`, before the live run, and the run met none of these stops.

Each run uses a fresh `EDGAR_LOCAL_DATA_DIR`, so edgartools' HTTP cache cannot hide
requests. The script refuses to report a run in which the throttle saw no request. In
this run the throttle counted 28 requests, and the run's fresh cache holds exactly 28
responses (16 from `data.sec.gov`, 12 from `www.sec.gov`), so no request bypassed the
throttle.

## Paths

The paths were enumerated from the installed 5.58.0 source, not recalled from memory.
There are three families:

- (a) listing an issuer's filings;
- (b) going from a filing to its attachments and to exhibit bytes, HTML, or text,
  including the 8-K and press-release convenience objects;
- (c) extracting tables.

"Declared" is the annotation as written in the source, read with
`annotationlib.Format.STRING`. "Observed" is the module-qualified runtime type.

Each of the 43 paths ran on all eight filings (344 results). The table lists each
distinct outcome of a path once, in the order it first appeared, so a path whose
outcome differs between filings appears more than once.

| family | call | declared | observed | elements | foreign |
|---|---|---|---|---|---|
| a | `Company(cik).get_filings(form='8-K', accession_number=...)` | `EntityFilings` | `edgar.entity.filings.EntityFilings` | - | no |
| a | `EntityFilings.data` | `__init__ parameter: pa.Table` | `pyarrow.lib.Table` | - | yes |
| a | `EntityFilings.to_pandas()` | `pd.DataFrame` | `pandas.DataFrame` | - | yes |
| a | `iterating EntityFilings` | `(none)` | `edgar.entity.filings.EntityFiling` | - | no |
| b | `Filing.attachments` | `(none)` | `edgar.attachments.Attachments` | - | no |
| b | `Attachments.exhibits` | `(none)` | `edgar.attachments.Attachments` | - | no |
| b | `iterating Attachments` | `(none)` | `edgar.attachments.Attachment` | - | no |
| b | `Attachment.content` | `(none)` | `builtins.str` | - | no |
| b | `Attachment.download()` | `Optional[Union[str, bytes]]` | `builtins.str` | - | no |
| b | `Attachment.text()` | `(none)` | `builtins.str` | - | no |
| b | `Attachment.markdown()` | `Optional[str]` | `builtins.str` | - | no |
| b | `Filing.html()` | `Optional[str]` | `builtins.str` | - | no |
| b | `Filing.obj()` | `(none)` | `edgar.company_reports.current_report.CurrentReport` | - | no |
| b | `EightK.press_releases` | `(none)` | `edgar.company_reports.press_release.PressReleases` | - | no |
| b | `PressRelease.html()` | `Optional[str]` | `builtins.str` | - | no |
| b | `PressRelease.text()` | `Optional[str]` | `builtins.str` | - | no |
| b | `EightK.earnings` | `(none)` | `NoneType` | - | no |
| b | `Filing.text()` | `str` | `builtins.str` | - | no |
| b | `Filing.markdown()` | `str` | `builtins.str` | - | no |
| b | `Attachments.markdown()` | `Dict[str, str]` | `builtins.dict` | `builtins.str` | no |
| b | `EightK.get_exhibits()` | `(none)` | `builtins.list` | `edgar.attachments.Attachment` | no |
| b | `EightK.text()` | `(none)` | `builtins.str` | - | no |
| b | `EarningsRelease.from_filing(filing)` | `Optional['EarningsRelease']` | `NoneType` | - | no |
| c | `parse_html(html).tables` | `Optional[List[TableNode]]` | `builtins.list` | `edgar.documents.table_nodes.TableNode` | no |
| c | `TableNode.to_dataframe()` | `pd.DataFrame` | `pandas.DataFrame` | - | yes |
| c | `EarningsRelease.tables` | `List[FinancialTable]` | `raised AttributeError: 'NoneType' object has no attribute 'tables'` | - | no |
| c | `FinancialTable.dataframe` | `attribute: pd.DataFrame` | `raised AttributeError: 'NoneType' object has no attribute 'tables'` | - | no |
| c | `EarningsRelease.to_facts_dataframe()` | `pd.DataFrame` | `raised AttributeError: 'NoneType' object has no attribute 'to_facts_dataframe'` | - | no |
| c | `Document.to_dataframe()` | `'pd.DataFrame'` | `pandas.DataFrame` | - | yes |
| c | `FinancialTable.per_share_rows` | `pd.DataFrame` | `raised AttributeError: 'NoneType' object has no attribute 'tables'` | - | no |
| c | `FinancialTable.scaled_dataframe` | `pd.DataFrame` | `raised AttributeError: 'NoneType' object has no attribute 'tables'` | - | no |
| c | `EightK.get_income_statement()` | `(none)` | `pandas.DataFrame` | - | yes |
| c | `EightK.get_balance_sheet()` | `(none)` | `pandas.DataFrame` | - | yes |
| c | `EightK.get_cash_flow_statement()` | `(none)` | `pandas.DataFrame` | - | yes |
| c | `EightK.income_statement` | `(none)` | `NoneType` | - | no |
| c | `EightK.balance_sheet` | `(none)` | `NoneType` | - | no |
| c | `EightK.cash_flow_statement` | `(none)` | `NoneType` | - | no |
| c | `EarningsRelease.income_statement` | `Optional[FinancialTable]` | `raised AttributeError: 'NoneType' object has no attribute 'income_statement'` | - | no |
| c | `EarningsRelease.balance_sheet` | `Optional[FinancialTable]` | `raised AttributeError: 'NoneType' object has no attribute 'balance_sheet'` | - | no |
| c | `EarningsRelease.cash_flow_statement` | `Optional[FinancialTable]` | `raised AttributeError: 'NoneType' object has no attribute 'cash_flow_statement'` | - | no |
| c | `EarningsRelease.segment_data` | `Optional[FinancialTable]` | `raised AttributeError: 'NoneType' object has no attribute 'segment_data'` | - | no |
| c | `EarningsRelease.eps_reconciliation` | `Optional[FinancialTable]` | `raised AttributeError: 'NoneType' object has no attribute 'eps_reconciliation'` | - | no |
| c | `EarningsRelease.guidance` | `Optional[FinancialTable]` | `raised AttributeError: 'NoneType' object has no attribute 'guidance'` | - | no |
| b | `EightK.earnings` | `(none)` | `edgar.earnings.EarningsRelease` | - | no |
| b | `EarningsRelease.from_filing(filing)` | `Optional['EarningsRelease']` | `edgar.earnings.EarningsRelease` | - | no |
| c | `EarningsRelease.tables` | `List[FinancialTable]` | `builtins.list` | `edgar.earnings.FinancialTable` | no |
| c | `FinancialTable.dataframe` | `attribute: pd.DataFrame` | `pandas.DataFrame` | - | yes |
| c | `EarningsRelease.to_facts_dataframe()` | `pd.DataFrame` | `pandas.DataFrame` | - | yes |
| c | `FinancialTable.per_share_rows` | `pd.DataFrame` | `pandas.DataFrame` | - | yes |
| c | `FinancialTable.scaled_dataframe` | `pd.DataFrame` | `pandas.DataFrame` | - | yes |
| c | `EarningsRelease.income_statement` | `Optional[FinancialTable]` | `NoneType` | - | no |
| c | `EarningsRelease.balance_sheet` | `Optional[FinancialTable]` | `NoneType` | - | no |
| c | `EarningsRelease.cash_flow_statement` | `Optional[FinancialTable]` | `NoneType` | - | no |
| c | `EarningsRelease.segment_data` | `Optional[FinancialTable]` | `NoneType` | - | no |
| c | `EarningsRelease.eps_reconciliation` | `Optional[FinancialTable]` | `NoneType` | - | no |
| c | `EarningsRelease.guidance` | `Optional[FinancialTable]` | `NoneType` | - | no |
| c | `EightK.income_statement` | `(none)` | `edgar.earnings.FinancialTable` | - | no |
| c | `EightK.balance_sheet` | `(none)` | `edgar.earnings.FinancialTable` | - | no |
| c | `EarningsRelease.income_statement` | `Optional[FinancialTable]` | `edgar.earnings.FinancialTable` | - | no |
| c | `EarningsRelease.balance_sheet` | `Optional[FinancialTable]` | `edgar.earnings.FinancialTable` | - | no |
| c | `parse_html(html).tables` | `Optional[List[TableNode]]` | `builtins.list` | - | no |
| c | `TableNode.to_dataframe()` | `pd.DataFrame` | `raised IndexError: list index out of range` | - | no |
| c | `EarningsRelease.tables` | `List[FinancialTable]` | `builtins.list` | - | no |
| c | `FinancialTable.dataframe` | `attribute: pd.DataFrame` | `raised IndexError: list index out of range` | - | no |
| c | `FinancialTable.per_share_rows` | `pd.DataFrame` | `raised IndexError: list index out of range` | - | no |
| c | `FinancialTable.scaled_dataframe` | `pd.DataFrame` | `raised IndexError: list index out of range` | - | no |

A row that begins "raised" records the script's chain failing before it reached the
named path, not a type the library returned:

- `EightK.earnings` is `None` for four filings (0000003370-05-000209,
  0000049071-06-000012, 0000068270-05-000104 and 0001572910-14-000003), so every
  `EarningsRelease` and `FinancialTable` path raises `AttributeError` on those.
- For 0001104659-23-049001, `parse_html(html).tables` and `EarningsRelease.tables` are
  empty lists, so the paths that take the first table raise `IndexError`.

## Declared versus observed

No observed type contradicts a declaration. Where a path is declared, every observed
type is the declared type or one arm of its `Optional` or `Union`. These paths have no
declaration:

- `iterating EntityFilings`: no declaration; observed `edgar.entity.filings.EntityFiling`.
- `Filing.attachments`: no declaration; observed `edgar.attachments.Attachments`.
- `Attachments.exhibits`: no declaration; observed `edgar.attachments.Attachments`.
- `iterating Attachments`: no declaration; observed `edgar.attachments.Attachment`.
- `Attachment.content`: no declaration; observed `builtins.str`.
- `Attachment.text()`: no declaration; observed `builtins.str`.
- `Filing.obj()`: no declaration; observed
  `edgar.company_reports.current_report.CurrentReport`.
- `EightK.press_releases`: no declaration; observed
  `edgar.company_reports.press_release.PressReleases`.
- `EightK.earnings`: no declaration; observed `edgar.earnings.EarningsRelease` for four
  filings and `NoneType` for four.
- `EightK.get_exhibits()`: no declaration; observed `builtins.list` of
  `edgar.attachments.Attachment`.
- `EightK.text()`: no declaration; observed `builtins.str`.
- `EightK.get_income_statement()`: no declaration; observed `pandas.DataFrame`.
- `EightK.get_balance_sheet()`: no declaration; observed `pandas.DataFrame`.
- `EightK.get_cash_flow_statement()`: no declaration; observed `pandas.DataFrame`.
- `EightK.income_statement`: no declaration; observed `edgar.earnings.FinancialTable` for
  two filings and `NoneType` for six.
- `EightK.balance_sheet`: no declaration; observed `edgar.earnings.FinancialTable` for
  two filings and `NoneType` for six.
- `EightK.cash_flow_statement`: no declaration; observed `NoneType` for all eight.

## For Stage 5

Stage 5 is the roadmap's "Event discovery, eligibility, and acquisition". It was Stage 4
before the point-in-time DJIA cohort amendment (`specs/point-in-time-djia-cohort.md`)
renumbered the stages.

These paths return a foreign dataframe:

- family (a): `EntityFilings.data` returns a `pyarrow.lib.Table`, and
  `EntityFilings.to_pandas()` returns a `pandas.DataFrame`;
- family (c): `TableNode.to_dataframe()`, `Document.to_dataframe()`,
  `FinancialTable.dataframe`, `FinancialTable.per_share_rows`,
  `FinancialTable.scaled_dataframe`, `EarningsRelease.to_facts_dataframe()`,
  `EightK.get_income_statement()`, `EightK.get_balance_sheet()`, and
  `EightK.get_cash_flow_statement()` each return a `pandas.DataFrame`.

R14.5 therefore requires a cast at the ingestion boundary. Any of these outputs that
Stage 5 uses is converted to Polars there, for example with `polars.from_arrow` for the
pyarrow table and `polars.from_pandas` for the pandas frames. A test shows that no
pandas or pyarrow object crosses the boundary. The family (b) paths, which fetch exhibit
bytes, HTML, and text, return only built-in types and edgartools' own objects, so they
need no cast.
