# PDF citation text (`pdftext-1`): an amendment to plan 6

> For agentic workers: REQUIRED NEXT SKILL: writing-plans, to amend
> `specs/plans/6-point-in-time-djia-cohort.md` in place. Insert Task 16b before
> Task 17, and change only what §Plan changes names. Tasks 1–16 are committed (tip
> `b9603b1`): do not plan them again. Plan 6 implements this spec, so retire it
> with plan 6 at plan 6's completion.

The user approved this design on 2026-09-26, in a brainstorming session held while
plan 6's Task 17 was paused at its Step 1 gate. A later addition, PT-9, lets
`cohort terms` hash a terms page saved by hand (§The S&P terms page).

## Why

Task 17 cites S&P Dow Jones Indices' official announcements of DJIA changes, and
every announcement the user supplied is a PDF. Plan 6 cites text only through
`walker-1`, which reads HTML (P6-9), and Task 17 Step 1 says to stop and ask on a
PDF. Asked, the user chose to amend the plan so that a PDF can be cited, rather than
look for HTML versions.

Nothing above the plan changes:

- **The cohort spec** needs no edit. Its evidence hierarchy names S&P DJI's
  addition and removal announcements without restricting their format.
- **Core** needs no edit. `MediaType` already admits `application/pdf`, and
  `EvidenceLocator` already records a `canonicalization_version` beside its text
  hash. `pdftext-1` matches `IdPart`.

The user supplied five notices. Two are cited:

| S&P DJI notice | What it states | Cited |
| --- | --- | --- |
| `1471327`, index announcement, 2024-03-27 | 3M spins off Solventum before the open on 2024-04-01; 3M stays | No: no change, and before the window |
| `1475162`, press release, 2024-11-01 | NVDA replaces INTC and SHW replaces DOW, prior to the open on 2024-11-08; a Utility Average change beside it | **Yes** |
| `1480747`, index announcement, 2025-10-27 | Honeywell spins off Solstice before the open on 2025-10-30; Honeywell stays | No: no change |
| `1483528`, press release, 2026-05-27 | A Transportation Average change | No: another index |
| `1484126`, press release, 2026-06-23 | GOOGL replaces VZ, prior to the open on 2026-06-29; Honeywell stays, renamed Honeywell Technologies Inc. | **Yes** |

### The S&P terms page

The register requires every published source to record its terms' URL and hash
(`cohort/register.py`), and the notices link to no terms page. In the footer of the
S&P DJI site, `www.spglobal.com/spdji/en/`, which the notices name, the user found
S&P Global's site-wide terms: `https://www.spglobal.com/en/terms-of-use`. But
`cohort terms` can only fetch, and the host refuses it. On 2026-09-26, with the
user's approval, it answered `robots.txt` with a persistent 403 (two requests),
and the client stopped before requesting the page. So `cohort terms` gains a way to
hash a copy the user saves in a browser (PT-9), as `cohort register` already
records an evidence page that a site refuses.

## The evidence behind the library

A throwaway spike ran each candidate from uv's cache, outside the lockfile, over
the five notices, twice each. It left `git status` and `uv.lock` unchanged.

| | pypdf 6.19.0, plain mode | pypdf 6.19.0, layout mode | pdfminer.six 20260107 |
| --- | --- | --- | --- |
| Each summary-table row on one line, name and ticker together | yes, every row | yes, but words split apart (`In te l Co rp.`) | no: tickers on lines of their own |
| Reruns byte-identical | yes | yes | yes |
| Non-ASCII characters | U+00AE, U+2019, U+2022; no ligatures | the same | the same |

pypdf's raw lines end in a space, some start with one, and a few hold a doubled
space (`NVIDIA  NVDA`). A hand-built ASCII PDF (Helvetica, WinAnsi) extracts the
same way under pypdf 6.19.0:

- text runs on one baseline come out as one line, joined by single spaces;
- spaces inside a run come out as written;
- an empty page yields no text.

## Decisions

The user made these on 2026-09-26.

| ID | Decision |
| --- | --- |
| PT-1 | A PDF is cited through a second citation-text policy, `pdftext-1`, chosen by media type beside `walker-1`. Rejected: a whole-document hash citation, which would drop P6-9's check that a row's name and ticker occur in its cited text. |
| PT-2 | `pdftext-1` normalizes whitespace (§The policy) rather than keeping pypdf's, so a needle reads as the page does. |
| PT-3 | pypdf is pinned exactly, `pypdf==6.19.0`: the version defines the policy, so a bump is `pdftext-2`. The `browser-capture` extra's exact pins (`selenium==4.49.0`, `websocket-client==1.9.2`) are the precedent. |
| PT-4 | `cohort register` refuses bytes that contradict the declared media type: a `%PDF-` body declared as HTML, or a declared PDF without that signature. |
| PT-5 | pypdf's recovery warnings are silenced below ERROR during extraction. The text hash, not the warnings, is the authority. |
| PT-6 | Tests build invented PDFs at test time. The committed synthetic fixture does not change. |
| PT-7 | Plan 6 gains Task 16b, before Task 17, with its own dependency gate. Tasks 17 and 18 keep their numbers. |
| PT-8 | The roadmap's Stage 4 Consumes clause, "No parser, canonicalizer, document, or model artifact", still holds. `pdftext-1`, like this stage's use of `walker-1`, produces citation text and no document artifact. The user signed this reading. |
| PT-9 | `cohort terms URL --saved FILE [--media-type TYPE]` hashes a terms page the user saved in a browser, by the register's own rule: the `walker-1` canonical text's SHA-256 for HTML, the bytes' otherwise. It sends no request and needs no identity. It refuses bytes that contradict the media type, by PT-4's check. The user still reads the page before its hash enters the register. |

## The policy: `pdftext-1`

Given a saved PDF's bytes:

1. Read them with `pypdf.PdfReader`, pypdf 6.19.0, with pypdf's logger held below
   ERROR for the call and restored after it.
2. Take each page's plain-mode `extract_text()`, in page order.
3. Normalize the text to NFC, the repository's convention, never NFKC.
4. Collapse each line's whitespace runs to one space, and strip its ends. Drop the
   lines left empty.
5. Join every line, across pages, with `\n`.

The result is the canonical text. Its hash is the SHA-256 of its UTF-8, as
`walker-1`'s is, and offsets are half-open code-point indices into it. The policy
lives in `cohort/pdftext.py`, outside `canonical/`, and never builds a
`CanonicalDocument`.

It refuses, with a `LocatorError` that names `pdftext-1`:

- bytes pypdf cannot read, such as garbage or a truncated file;
- any PDF that pypdf reports as encrypted, even one that would open with an empty
  password, so the result never depends on a decryption attempt;
- a PDF with no text layer, whose normalized text is empty. OCR is out of scope.

## Components

Paths are under `packages/earnings-ingestion/src/earnings_ingestion/` unless given
in full.

| Where | Change |
| --- | --- |
| `cohort/pdftext.py` (new) | `PDFTEXT_VERSION = "pdftext-1"` and `pdf_text(body) -> str` |
| `cohort/locators.py` | `ArtifactText.canonical` sends `text/html` to `walker-1` and `application/pdf` to `pdftext-1`, and refuses any other type. A new `version` property names the policy, which `span`, `find`, and `line` record. `verify` refuses a locator whose version is not the artifact's. |
| `cohort/build.py` | `span()` records `text.version`, not the `walker-1` constant (`build.py:319`) |
| `fetch/store.py` | `EXTENSIONS` gains `application/pdf` as `.pdf`; a PDF would otherwise be stored as `.bin` |
| `cohort/acquire.py` | a `PDF` media-type set; `fetch_page` accepts HTML or PDF; `check_media_type(body, media_type)`, PT-4's one check, which `register_saved` and `cohort terms --saved` share |
| `cohort/live.py` | the evidence refetch accepts HTML or PDF |
| `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py` | `register --media-type application/pdf` works as it stands. A contradicting type now exits 1 with the refusal. `terms` gains `--saved FILE` and `--media-type` (PT-9). |
| `packages/earnings-ingestion/pyproject.toml`, `uv.lock` | `pypdf==6.19.0` |
| `docs/data-dictionary.md` | The `text_span` value and `EvidenceLocator.canonicalization_version` now name `pdftext-1` beside `walker-1`. No field or value is added. |

In Task 17, a saved PDF moves through three steps:

1. `cohort register spdji-announcements <file> --url <its original URL> --saved-at <UTC> --media-type application/pdf`
   stores it as `<sha256>.pdf`, with a `saved_by_user` retrieval.
2. `cohort cite … --find "NVIDIA NVDA" --line` cites one summary-table row. Its
   locator records `canonicalization_version = "pdftext-1"`.
3. `build` extracts the text again, and verifies every hash and every row's name and
   ticker.

## Errors and safety

| Situation | Behavior |
| --- | --- |
| An unreadable or encrypted PDF, or one with no text layer | `LocatorError` (§The policy). In `build`, a `problem:` line, which no review can settle. |
| A locator whose version is not the artifact's policy | refused by `verify` |
| pypdf's output drifts, under another version | every PDF citation's `canonical_sha256` stops matching, and `build` refuses. The remedy is `pdftext-2` and new citations, never an edited hash. The exact pin and the golden test make a silent drift unlikely. |
| pypdf's recovery warnings, such as `Ignoring wrong pointing object`, which the real notices raise | silenced during extraction (PT-5) |

These stand as plan 6 has them:

- A PDF is data. pypdf runs no script and follows no link, and nothing in this path
  reaches the network.
- Saved PDFs stay under the gitignored `data/raw/cohort/`. S&P DJI's rights stay
  `restricted`, and only facts, locators, and hashes are committed (P6-3). `cite`
  prints the cited text to stderr only.
- At Task 18, `verify-live` refetches each PDF's URL. A refusal is recorded as
  `refused` (P6-20).

pypdf is pure Python, so a pathological PDF could be slow to read. The inputs are a
handful of two-page notices the user chose, so there is no page cap.

## Tests

A `make_pdf` fixture in `packages/earnings-ingestion/tests/conftest.py` builds a
small PDF from text runs, as pure-ASCII bytes with a computed cross-reference
table. It follows the conftest's `make_capture` pattern, and no binary enters Git.

| File | What it shows |
| --- | --- |
| `test_cohort_pdftext.py` (new) | An invented two-page notice's exact `pdftext-1` text and its golden SHA-256, the drift alarm, as `walker-1`'s golden test is. Also: identical reruns; NFC applied to decomposed input built with `chr()`; garbage, truncated, and encrypted input refused, the encrypted input being RC4, which pypdf's own writer produces with no extra dependency (AES would need `cryptography`); an empty page refused as having no text layer; pypdf's logger restored after the call. |
| `test_cohort_locators.py` | `ArtifactText` over a PDF: version `pdftext-1`; `span`, `find`, and `line` record it; `verify` passes. A `walker-1` locator on a PDF, a `pdftext-1` locator on HTML, and any other media type are refused. |
| `test_cohort_build.py` | In a private copy of the synthetic cohort, the official index notice is replaced by an invented PDF stating the same facts, and its rows are cited again. `build` gives the same intervals, and the change citations record `pdftext-1`. |
| `test_fetch_store.py` | a PDF is stored as `<sha256>.pdf` |
| `test_cohort_acquire.py` | `check_media_type`, and so `register_saved`, refuses a contradicting type in both directions. `fetch_page` accepts an `application/pdf` response through a mock transport. |
| `test_cohort_live.py` | the evidence refetch accepts an unchanged PDF |
| `apps/earnings-pipeline/tests/test_cohort_cli.py` | `cohort register --media-type application/pdf` stores a `.pdf`, and a contradicting type exits 1. `cohort terms URL --saved FILE` prints `terms_digest` of the file's bytes without opening a client, even with no identity set, and a contradicting type exits 1. |
| `test_import_boundaries.py` | `cohort.pdftext` loads nothing forbidden, and the offline path still loads no network client |

The committed synthetic fixture, `tests/fixtures/cohort/`, and its byte-for-byte
test do not change. The default suite stays offline and needs no credential.

## Plan changes

Amend plan 6 in place:

1. **Header, Goal, and Tech Stack.** One new dependency, `pypdf==6.19.0`, added by
   Task 16b. `uv.lock` changes there and nowhere else.
2. **Global Constraints.**
   - The Versions table gains a row: PDF citation text, `pdftext-1` (pypdf
     6.19.0), in `cohort/pdftext.py` (Task 16b).
   - "Nothing downloads a dependency, and `uv.lock` stays as it is" gains an
     exception: Task 16b's gated `uv add`.
   - Every Expected count after Task 16b is restated: the default suite grows by
     Task 16b's tests, and the formatted-file count by its new files.
3. **Plan decisions.**
   - Add P6-24, which records PT-1 to PT-6 and §The policy.
   - Append an **Amended:** pointer to P6-9: text spans also run over `pdftext-1`
     text for a PDF artifact (P6-24).
4. **Requirement map.** The Consumes row "No parser, canonicalizer, document, or
   model artifact" reads: `walker-1` (HTML) and `pdftext-1` (PDF) produce citation
   text only (PT-8), Tasks 8 and 16b.
5. **Human gates.** A new row: the PDF dependency, at Task 16b.
   `uv add --package earnings-ingestion "pypdf==6.19.0"` reaches PyPI and changes
   `uv.lock`. The wheel is already in uv's cache from the spike. The hand-saving
   row gains the terms page: the user saves it, and `cohort terms --saved` hashes it
   (PT-9).
6. **File map.** Task 16b's rows.
7. **Task 16b**, "PDF citations (`pdftext-1`)". It follows the plan's usual shape:
   failing tests, the gated dependency, the implementation, the dictionary, the
   checks, and one commit. It also adds `cohort terms --saved` (PT-9). Every new
   Python file is ASCII and passes the escape check.
8. **Task 17.**
   - The planning-time leads give way to the saved notices above.
   - Step 1's "If an announcement exists only as a PDF, stop and ask" becomes: a
     PDF is cited under `pdftext-1` (P6-24), and only a PDF without a text layer
     stops for the user.
   - Step 2: S&P DJI's terms URL comes from the S&P DJI site's footer, since the
     notices link none. If `cohort terms <url>` stops, the user saves the page in
     a browser and reads it, and `cohort terms <url> --saved <file>` hashes it
     (PT-9).
   - Step 3: `spdji-announcements`' `access_method` names the PDF notices, saved by
     hand and recorded by `cohort register --media-type application/pdf`. Its
     `known_limitations` adds: notices are PDFs cited through `pdftext-1` (pypdf
     6.19.0), and a notice without a text layer cannot be cited.
   - Step 4 registers each cited PDF with `--media-type application/pdf`, its
     original URL, and its saved-at time in UTC. The user supplies both, and a URL
     is never derived from a file name.
   - Step 6 cites each company by its summary-table row, with
     `--find "<name> <ticker>" --line`. It cites the effective date by a dated row,
     or by a span across lines found with a needle that holds `\n`, since
     `pdftext-1` joins lines with `\n`.
   - Step 13's Expected counts are restated.
9. **Task 18.**
   - `verify-live` refetches the PDF URLs, and a refusal is recorded.
   - The verification record's section on the probe and requests names the spike
     and the dependency download. Its Limitations section names `pdftext-1`'s: no
     OCR, and a policy bound to one pypdf version.
   - The CLAUDE.md update restates the lock and sync counts from the real output of
     `uv lock` and `uv sync`, which were 151 resolved and 40 synced before, and
     names `pdftext-1`.
10. **Completion.** The deviations to record are two:
    - Task 4's stray blank line, which the user approved stripping;
    - this amendment.

    This spec retires with plan 6.

## State when this was written

- Tasks 1–16 are committed on `stage-4-point-in-time-djia-cohort` at `b9603b1`,
  unpushed. Task 5's format probe ran, with the user's approval, and sent 4 SEC
  requests.
- **Task 17, Step 1.** The user approved the four register entries as the plan
  proposes them, and supplied the notices above. For each cited PDF, the user gave
  its original URL. Its saved-at time is the file's modification time, which the
  user chose over a recalled "4 pm". Task 17 Step 4 registers each one once Task 16b
  has landed:

  | Notice | URL | `--saved-at` (UTC) | SHA-256 of the saved file |
  | --- | --- | --- | --- |
  | `1475162` | `https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20241101-1475162/1475162_djiadjuaintcdowaes.pdf` | `2026-09-26T21:12:22` | `fd02c23edb53c87d5e478646a008d0971d9ffe7fa9a569158db64657a85d8d2a` |
  | `1484126` | `https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20260623-1484126/1484126_djiavzjune2026.pdf` | `2026-09-26T21:08:05` | `c022ddf1cc80472b66f32eca0f6c14dd404f4db3e49af0d2a244c0fa5d1b622c` |

  Still pending from the user: the anchor revision's ID and UTC timestamp.
- **Task 17, Step 2.** Two of the three terms hashes are taken:
  - `wikipedia-djia`:
    `581ce13c873fabdd2648e56752f889cd5e4384604ccaaeca27e8ed777c8224cd`;
  - `dia-nport`:
    `b11d9ecd3bcd0d86ccd1a3301e90ccf66b307c5f5f3709a00e26a55a6246e076`.

  The third, `spdji-announcements`' terms at `https://www.spglobal.com/en/terms-of-use`,
  was refused live (§The S&P terms page). The user saves that page by hand, and
  `cohort terms --saved` hashes it once Task 16b has landed.
- **The identity.** The user set `SOURCE_IDENTITY` equal to `EDGAR_IDENTITY`. Each
  web-client command carries the prefix `SOURCE_IDENTITY="$EDGAR_IDENTITY"`, and
  neither value is ever printed.
