# Data dictionary

The shared contracts, their fields, and their versions (AGENTS.md §187–191). Each
table below lists every field or value of one contract;
`tests/contracts/test_data_dictionary.py` fails when a field or value changes without
this file changing too.

## earnings-core contracts, schema version 2

- **Package.** `packages/earnings-core`, imported as `earnings_core`.
- **Schema version.** `2` (`earnings_core.SCHEMA_VERSION`). Every top-level record
  carries it as `schema_version`, and a payload with another version is refused.
- **Validator version.** `"2"` (`earnings_core.VALIDATOR_VERSION`), stamped on every
  `Rejection` and `VerifiedSpan`. Caches key on it (R14.6); bump it whenever a check
  changes.
- **Compatibility.** Version 2 (Stage 3) adds `DocumentElement.text_origin` and the
  `ocr_derived_text` rejection. Its checks also report every crossing pair, recheck
  the element invariants that construction enforces, validate `MaskedDocument`
  itself, and refuse more non-portable `storage_ref` values. Version 1 records are
  refused. None was ever persisted, so nothing migrates and no cache is invalidated
  (A §187).
- **Conventions.**
  - Offsets are zero-based Unicode code points over a half-open `[start, end)`,
    never UTF-8 bytes, UTF-16 code units, or model tokens (R3.2).
  - Every span holds text: `start < end`. An empty table cell is not an element.
  - Hashes are SHA-256, written as 64 lowercase hexadecimal characters. The canonical
    hash covers the canonical text's UTF-8 bytes (R3.1).
  - Records are frozen, refuse unknown fields, and are strictly typed: a bool, float,
    or numeric string is never an offset.

### Identifiers

| Identifier | Derivation | Example |
| --- | --- | --- |
| `doc_id` | `<source_document_id>@<canonicalization_version>#<first 16 hex of canonical_hash>` | `0000007332-09-000032_ex-99@walker-1#<16 hex>` |
| `element_id` | `<type>-<start>-<end>` | `paragraph-120-450` |

Changed canonical text is always a new `doc_id` (R3.3). An `element_id` is unique
within one document version; the pair (`doc_id`, `element_id`) is unique across
versions. Both derivations were chosen on 2026-09-25 (plan 3, Plan decisions).

### `TextSpan`

A half-open range of code points in one canonical text.

| Field | Type | Meaning |
| --- | --- | --- |
| `start` | int ≥ 0 | Offset of the first code point |
| `end` | int > `start` | Offset one past the last code point |

### `ArtifactRef`

A stored artifact, identified by the SHA-256 of its bytes.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `2` | Contract schema version |
| `content_sha256` | 64 lowercase hex | SHA-256 of the artifact's bytes |
| `media_type` | string | Lowercase media type, e.g. `text/plain; charset=utf-8` |
| `storage_ref` | string | Repository-relative path or non-file URI: never absolute, `~`, `file:` in any case, a drive letter, a backslash, or a `..` segment |
| `rights_status` | `RightsStatus` | What may be done with the content |
| `rights_basis` | non-blank string | Why: the register entry or terms that decide the status |

### `RightsStatus`

| Value | Meaning |
| --- | --- |
| `redistributable` | A recorded basis permits committing and exporting the content |
| `local_only` | Retain locally; never commit or export. Unclear rights are recorded this way |
| `restricted` | Terms forbid redistributing the text; keep locators and local features (R2.1) |

### `CanonicalDocument`

One immutable, hashed version of a source document's text (R3.1, R3.3). The
`canonical_documents` dataset of AGENTS.md §359.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `2` | Contract schema version |
| `doc_id` | string | Derived ID of this version (see Identifiers) |
| `source_document_id` | ID part | The source record this text came from |
| `canonicalization_version` | ID part | The whole canonicalization policy, e.g. `walker-1`: parser, rules, normalization, layout, and sentence rules |
| `canonical_text` | non-empty string | The text every offset indexes; never holds a lone surrogate |
| `canonical_hash` | 64 lowercase hex | SHA-256 of `canonical_text` as UTF-8 |
| `text_artifact` | `ArtifactRef` or null | Where the same UTF-8 bytes are stored, if they are |

An ID part is letters, digits, and `. _ : -` only. Parser and library versions are
provenance, recorded in Stage 3's `CanonicalizationManifest` (below), not document
fields.

### `ElementType`

| Value | Meaning |
| --- | --- |
| `section` | A run of content under one heading, or a transcript section |
| `heading` | A heading; may carry a level |
| `paragraph` | A paragraph of body text |
| `list_item` | A list item; its level is the list's nesting depth |
| `sentence` | A sentence within a paragraph, list item, or turn |
| `footnote` | A footnote or note |
| `table` | A table; the parent of its cells |
| `table_cell` | One non-empty cell, with its grid position and headers |
| `speaker_turn` | One speaker's uninterrupted turn in a transcript |
| `page_artifact` | A running header or footer, page number, or filing banner |
| `other` | Anything a parser cannot type more precisely |

### `TextOrigin`

Where an element's text came from (R4.3).

| Value | Meaning |
| --- | --- |
| `native` | Text the source carries as text, extracted without recognition |
| `ocr` | Text recognized from an image: lower-fidelity, and never verified as an original quotation |

### `TableCellContext`

A table cell's position and header context (R4.1, R4.2).

| Field | Type | Meaning |
| --- | --- | --- |
| `row` | int ≥ 0 | Row index in the table's full grid, empty cells counted |
| `column` | int ≥ 0 | Column index in the table's full grid, empty cells counted |
| `row_span` | int ≥ 1 | Rows the cell covers |
| `column_span` | int ≥ 1 | Columns the cell covers |
| `is_header` | bool | Whether the cell is a header cell |
| `header_cell_ids` | tuple of `element_id` | Header cells of the same table that label this cell |

### `DocumentElement`

One typed structural unit of one document version (R4.1). The
`document_sections` / `speaker_turns` datasets of AGENTS.md §360.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `2` | Contract schema version |
| `element_id` | string | Derived from `type` and `span` (see Identifiers) |
| `doc_id` | string | The document version the element belongs to |
| `type` | `ElementType` | What kind of unit it is |
| `span` | `TextSpan` | Where it lies in the canonical text |
| `parent_id` | `element_id` or null | The containing element; parents precede children |
| `level` | int ≥ 1 or null | Outline or nesting depth; `section`, `heading`, and `list_item` only |
| `table_cell` | `TableCellContext` or null | Required on `table_cell` elements, forbidden elsewhere |
| `source_type` | string | The producing parser's own name for the unit, e.g. `lxml:h1` |
| `text_origin` | `TextOrigin` | Where the text came from; `native` unless recognized from an image |

In a valid element set any two spans nest or are disjoint.

### `SpanLocator`

Exact text with the words around it (R5.4). Context grows one whole word at a time
on each side until one occurrence remains.

| Field | Type | Meaning |
| --- | --- | --- |
| `exact` | non-empty string | The text itself |
| `prefix` | string | The words just before it; empty when `exact` occurs once |
| `suffix` | string | The words just after it; empty when `exact` occurs once |

### `TextChunk`

A view of one document handed to a model or parser; local offsets convert back
before evidence is stored (A §508).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `2` | Contract schema version |
| `doc_id` | string | The document version it views |
| `canonical_hash` | 64 lowercase hex | That version's canonical hash |
| `span` | `TextSpan` | The chunk's range in the document |
| `text` | string | Exactly the document's characters over `span` |

### `SpanCandidate`

A proposed evidence span before verification: one contiguous range (R5.5).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `2` | Contract schema version |
| `doc_id` | string | The document version it claims |
| `canonical_hash` | 64 lowercase hex | That version's hash, as the candidate stored it |
| `start` | int ≥ 0 | Offset of the first code point |
| `end` | int > `start` | Offset one past the last code point |
| `quote_text` | string | The text claimed to lie at `[start, end)` |
| `element_id` | string | The element the span is attributed to, which must contain it |
| `prefix` | string | Context before the span (R5.4) |
| `suffix` | string | Context after the span (R5.4) |

### `VerifiedSpan`

A span that passed every check (R6.1). Its `quote_text` is sliced from the canonical
text, never copied from a candidate (A §523).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `2` | Contract schema version |
| `doc_id` | string | The verified document version |
| `canonical_hash` | 64 lowercase hex | Its canonical hash |
| `start` | int ≥ 0 | Offset of the first code point |
| `end` | int > `start` | Offset one past the last code point |
| `quote_text` | string | `canonical_text[start:end]` |
| `element_id` | string | The element that contains the span |
| `prefix` | string | Context before the span |
| `suffix` | string | Context after the span |
| `validator_version` | string | The validator that accepted it |

### `MaskCategory`

| Value | Meaning |
| --- | --- |
| `safe_harbor` | Forward-looking-statement safe-harbor language |
| `non_gaap_disclaimer` | A non-GAAP measure disclaimer |
| `repeated_legal` | Other repeated legal text |

### `OverlayMask`

One boilerplate span marked by one boilerplate policy version (R3.4). It never
changes the text or its offsets.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `2` | Contract schema version |
| `doc_id` | string | The document version it overlays |
| `canonical_hash` | 64 lowercase hex | That version's canonical hash |
| `span` | `TextSpan` | The masked range |
| `category` | `MaskCategory` | The kind of boilerplate |
| `policy_id` | ID part | The boilerplate policy that marked it |
| `policy_version` | ID part | That policy's version |

### `MaskedDocument`

A document with the masks one policy version computed over it. An in-memory view,
not a persisted record. Construction refuses a tampered document, a mask of another
document or version, a mask past the text, and a mask from another policy.

| Field | Type | Meaning |
| --- | --- | --- |
| `document` | `CanonicalDocument` | The unchanged document |
| `policy_id` | ID part | The policy that ran, even if it found nothing |
| `policy_version` | ID part | That policy's version |
| `masks` | tuple of `OverlayMask` | Every mask the policy found |

### `Rejection`

Why a check refused a record (R6.2: rejections stay auditable).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `2` | Contract schema version |
| `reason` | `RejectionReason` | The failure class |
| `detail` | string | What failed, naming the record or element |
| `validator_version` | string | The validator that refused it |

### `RejectionReason`

`parse_span_candidate` records `malformed_record`. `validate_span` then runs its checks
in the order of the next eleven rows and records the first failure.

| Value | Meaning |
| --- | --- |
| `malformed_record` | Wrong types, missing or extra fields, a non-integer offset, or an element breaking an invariant construction enforces (R3.2, R5.5, R4.1) |
| `document_integrity` | The document's own hash or `doc_id` disagrees with its text (R6.1, R3.3) |
| `wrong_document` | The record names another document or version (R6.1, R3.3) |
| `canonical_hash_mismatch` | The record's stored hash is not the document's (R6.1) |
| `span_out_of_bounds` | The span runs past the canonical text (R6.1) |
| `quote_text_mismatch` | `quote_text` is not exactly `canonical_text[start:end]` (R6.1, R5.5, R13.2) |
| `unknown_element` | A pointer or attribution names no element of the document (R5.1, V9) |
| `outside_element` | The span is not inside its attributed element (R6.1) |
| `crosses_speaker_turn` | The span runs across a speaker-turn boundary (A §585, V9) |
| `ocr_derived_text` | The span overlaps OCR-derived text, never an original quotation (R4.3) |
| `locator_mismatch` | The stored prefix or suffix is not the text around the span (R5.4) |
| `ambiguous_occurrence` | Repeated text whose context does not single out one occurrence (R5.4) |
| `locator_not_found` | No occurrence matches a locator (R5.4) |
| `outside_chunk` | A chunk-local span runs past its chunk (A §508, V9) |
| `element_id_mismatch` | An element's ID is not derived from its type and span (R4.1) |
| `duplicate_element` | Two elements share an ID (R4.1) |
| `unknown_parent` | A parent ID names no element of the set (R4.1) |
| `parent_order` | A child precedes its parent (R4.1) |
| `outside_parent` | A child's span is not inside its parent's (R4.1) |
| `crossing_elements` | Two spans overlap without nesting (R4.1) |
| `table_cell_parent` | A table cell's parent is not a table (R4.1, R4.2) |
| `invalid_header_reference` | A header reference names no header cell of the same table (R4.2) |

## earnings-ingestion records, schema version 1

- **Package.** `packages/earnings-ingestion`, imported as `earnings_ingestion.canonical`
  (Stage 3, plan 4).
- **Schema version.** `1` (`earnings_ingestion.canonical.INGESTION_SCHEMA_VERSION`).
  The manifest and the failure carry it as `schema_version`, and a payload with
  another version is refused.
- **Not core contracts.** `earnings-themes` never imports ingestion (A §173): Stage 7
  reads the committed canonical fixtures through the core contracts.
- **Canonical fixtures.** `tests/fixtures/canonical/<fixture_id>.json` is one JSON
  object with the keys `document` (a `CanonicalDocument`), `elements` (the
  `DocumentElement` records), `manifest` (the `CanonicalizationManifest`), and `masks`
  (the `OverlayMask` records). Keys are sorted, non-ASCII characters are escaped, and
  each record is one line. Read each record with its contract's `model_validate_json`.

### `CanonicalizationManifest`

How one canonical document version was made. It holds no timestamp and no path, so it
regenerates byte for byte.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `canonicalization_version` | ID part | The whole policy, e.g. `walker-1` |
| `components` | map of string to string | Each component's identifier: `decoding`, `walker`, `normalization`, `compensation`, `layout`, `sentences` |
| `lxml_version` | string | `lxml.etree.LXML_VERSION`, dotted |
| `libxml2_version` | string | `lxml.etree.LIBXML_VERSION`, dotted |
| `python_version` | string | The interpreter's version |
| `source_document_id` | ID part | The saved source document |
| `raw_sha256` | 64 lowercase hex | SHA-256 of the saved bytes |
| `raw_bytes` | int ≥ 0 | Their byte count |
| `encoding` | string | The decoded encoding |
| `encoding_basis` | string | Why: `bom`, `meta`, `valid-utf-8`, or `default` |
| `element_counts` | map of type to int | Elements by `ElementType` value; absent types are omitted |
| `image_count` | int ≥ 0 | `<img>` elements in the parsed document |
| `replacement_characters` | int ≥ 0 | U+FFFD characters in the canonical text, which decoding keeps |
| `retypes` | map of rule to int | Blocks retyped by each of `C1`–`C5`, zeros included |
| `limitations` | tuple of string | Limitations triggered: `pre_table_without_cells` when C1 fired |
| `mask_policy_id` | ID part | The boilerplate policy, `boilerplate` |
| `mask_policy_version` | ID part | Its version, `1` |
| `mask_count` | int ≥ 0 | Masks the policy found |

### `FailureReason`

| Value | Meaning |
| --- | --- |
| `unsupported_media_type` | The media type's essence is not `text/html` |
| `parse_failed` | Decoding, lxml, or the walker raised on input it cannot read, such as a charset label naming a codec that is not a text encoding; or libxml2 logged a fatal error, such as nesting past its depth limit |
| `no_native_text` | Nothing is left after N1; image-only input lands here (R4.3) |
| `invalid_elements` | `validate_elements` found problems: a canonicalizer defect, never the input's |

### `CanonicalizationFailure`

A document the canonicalizer refused. A failure is never an empty document and never
a partial element set, and `canonicalize` never raises on input: only an invalid
`source_document_id`, the caller's error, raises.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `source_document_id` | ID part | The saved source document |
| `raw_sha256` | 64 lowercase hex | SHA-256 of the saved bytes |
| `canonicalization_version` | ID part | The policy that refused it |
| `reason` | `FailureReason` | The failure class |
| `detail` | string | What failed |
| `image_count` | int ≥ 0, or null | `<img>` elements: recorded exactly for `no_native_text` |
| `rejections` | tuple of `Rejection` | `validate_elements`' findings: recorded exactly for `invalid_elements` |

### `Canonicalized`

`canonicalize`'s result: an in-memory bundle, not a persisted record. Construction
refuses parts that describe different documents.

| Field | Type | Meaning |
| --- | --- | --- |
| `document` | `CanonicalDocument` | The canonical document |
| `elements` | tuple of `DocumentElement` | Document order, each parent before its children, each table followed by its cells and each block by its sentences |
| `masked` | `MaskedDocument` | The masks of policy `boilerplate` version `1` |
| `manifest` | `CanonicalizationManifest` | How the document was made |

## earnings-ingestion browser and layout records, schema version 1

- **Packages.** `earnings_ingestion.browser` (the capture) and
  `earnings_ingestion.layout` (layout-1 and its mapping), in
  `packages/earnings-ingestion` (Stage 3, plan 5).
- **Schema version.** These records join ingestion schema version `1`: no earlier
  record's fields changed. `RenderedCapture`, `AlignmentFailure`, and
  `LayoutExtraction` carry it as `schema_version`; the nested parts do not.
- **Diagnostic provenance.** A capture establishes what the pinned browser displayed
  under a recorded policy. It is never a canonical span and never evidence of a quote
  (B2): every layout-1 span comes from matching canonical text, never from a DOM
  offset.
- **Fixture captures.** `tests/fixtures/browser/<name>.capture.json` is one JSON
  object with the keys `blocks` (the layout's `LayoutBlock` records), `capture` (the
  `RenderedCapture` without its layout), and `tables` (the `LayoutTable` records).
  Keys are sorted, non-ASCII characters are escaped, and each record is one line.
  `earnings_ingestion.browser.serialize.from_capture_json` reads one back and
  rechecks both hashes. Screenshots are never committed.

### `RenderedCapture`

One capture of one saved source under one capture policy (B1, B2, B7). A `failed` or
`unavailable` capture holds no text, layout, or screenshot.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `capture_id` | string | `<source_document_id>@<policy>-<version>#<first 16 hex of cache_key>` |
| `cache_key` | 64 lowercase hex | SHA-256 over the raw hash, the policy and its version, the metadata script's version and text, the render configuration, and the browser, driver, Selenium, and platform; never a timestamp |
| `source_document_id` | ID part | The saved source document |
| `raw_sha256` | 64 lowercase hex | SHA-256 of the saved bytes |
| `capture_policy` | ID part | The capture policy's name, `isolated` |
| `capture_policy_version` | ID part | Its version, `1` |
| `metadata_version` | ID part | The layout-metadata script, `layout-metadata-1` |
| `browser_engine` | string | `Chrome for Testing` |
| `browser_version` | string | The pinned browser version, or `none` when none is installed |
| `driver_version` | string | The pinned chromedriver version, or `none` |
| `selenium_version` | string | Selenium's version |
| `os_name` | string | `platform.system()`, such as `Darwin` |
| `os_version` | string | The operating system's release |
| `architecture` | string | `platform.machine()`, such as `arm64` |
| `viewport_width` | int > 0 | Window width in CSS pixels |
| `viewport_height` | int > 0 | Window height in CSS pixels |
| `device_scale_factor` | int > 0 | Device pixels per CSS pixel |
| `locale` | string | The browser's language, `en-US` |
| `timezone` | string | The emulated time zone, `UTC` |
| `font_set` | string | The platform's system fonts, named by its release |
| `document_charset` | string | `document.characterSet`: the encoding the browser used; empty when nothing rendered |
| `script_policy` | string | `disabled`: document JavaScript never runs |
| `network_policy` | string | `blocked`: every request but the saved file is refused and recorded |
| `image_policy` | string | `blocked`: images are refused like any request |
| `missing_resource_policy` | string | `recorded`: a blocked resource is listed, and a required one makes the capture `partial` |
| `rendered_text` | string | `document.body.innerText`, exactly as returned |
| `rendered_text_sha256` | 64 lowercase hex | SHA-256 of its UTF-8 bytes |
| `layout` | `LayoutMetadata` | The layout-metadata script's result |
| `layout_sha256` | 64 lowercase hex | SHA-256 of the layout as ASCII JSON with sorted keys and no spaces |
| `screenshots` | tuple of `ArtifactRef` | Content-hashed PNG tiles, `local_only` under `data/runs/` |
| `blocked_requests` | tuple of `BlockedRequest` | Each distinct refused request once, sorted by URL and type |
| `captured_at` | aware datetime | When the capture started; never part of the cache key |
| `duration_seconds` | float ≥ 0 | How long it took |
| `status` | `CaptureStatus` | The outcome |
| `reason` | `CaptureReason`, or null | Why it is not `completed`: null exactly when `completed` |
| `detail` | string | What failed, or which required resources were blocked |

### `CaptureStatus`

| Value | Meaning |
| --- | --- |
| `completed` | Every resource the rendering needs was present |
| `partial` | Rendered, but a blocked stylesheet, font, or frame may have changed it; the reason is `blocked_required_resource` |
| `failed` | The browser ran, and no usable rendering came back |
| `unavailable` | No pinned browser could run here |

### `CaptureReason`

| Value | Meaning |
| --- | --- |
| `browser_unavailable` | The pinned browser or driver is not installed, or none is pinned for this platform |
| `startup_failure` | The browser or driver did not start, or is not the pinned version |
| `timeout` | Startup, navigation, or capture ran past its bound |
| `blocked_required_resource` | A stylesheet, font, or frame the page asked for was blocked |
| `document_load_failure` | The saved file did not load, or the page left it |
| `capture_failure` | Reading text, layout, or a screenshot failed, or request interception stopped |

### `BlockedRequest`

| Field | Type | Meaning |
| --- | --- | --- |
| `url` | string | The requested URL |
| `resource_type` | string | CDP's resource type, such as `Image`, `Stylesheet`, or `Document` |
| `required` | bool | A stylesheet, font, or subframe document: its absence makes the capture `partial` |

### `LayoutMetadata`

| Field | Type | Meaning |
| --- | --- | --- |
| `blocks` | tuple of `LayoutBlock` | Every block of the rendered body, in document order |
| `tables` | tuple of `LayoutTable` | Every rendered table, in document order; blocks and tables refer to tables by index here |

### `LayoutBlock`

The runs one block element holds directly, split where a nested block starts (W2's
analog). Content with computed `display: none`, and `noscript`, is left out.

| Field | Type | Meaning |
| --- | --- | --- |
| `tag` | string | The block element's tag, lowercase |
| `display` | string | Its computed `display` |
| `heading_level` | int > 0, or null | 1–6 when the nearest heading or list-item ancestor is `h1`–`h6` |
| `list_item` | bool | The nearest such ancestor is an `li` |
| `list_depth` | int ≥ 0 | How many `ul` and `ol` elements enclose it |
| `table` | int ≥ 0, or null | The table holding its nearest enclosing cell |
| `row` | int ≥ 0, or null | That cell's row among the table's own rendered rows |
| `cell` | int ≥ 0, or null | That cell's position among the row's rendered cells |
| `x` | int | Left edge in CSS pixels, from the page's origin |
| `y` | int | Top edge in CSS pixels, from the page's origin |
| `width` | int ≥ 0 | Width in CSS pixels |
| `height` | int ≥ 0 | Height in CSS pixels |
| `runs` | tuple of `LayoutRun` | Its text runs and line breaks, in document order |

### `LayoutRun`

One text node's raw DOM text with its computed style, or one `<br>`. The text is the
node's own, so a CSS `text-transform` never alters it.

| Field | Type | Meaning |
| --- | --- | --- |
| `text` | string | The node's text, or `"\n"` for a `<br>` |
| `br` | bool | A `<br>` outside `<pre>`; inside `<pre>` a `<br>` is a text run of `"\n"` |
| `visible` | bool | Computed `visibility: visible` and at least one rendered box |
| `bold` | bool | Computed `font-weight` of 600 or more |
| `underline` | bool | An underline decoration on it or any ancestor |
| `superscript` | bool | `vertical-align: super` on it or an ancestor inside its block |
| `symbol_font` | bool | A Wingdings or Symbol `font-family` |
| `font_size` | float ≥ 0 | Computed `font-size` in CSS pixels |

### `LayoutTable`

A rendered table's own rows, and the cell of another table that holds it.

| Field | Type | Meaning |
| --- | --- | --- |
| `parent_table` | int ≥ 0, or null | The table of the nearest enclosing cell; null for a table in no cell |
| `parent_row` | int ≥ 0, or null | That cell's row |
| `parent_cell` | int ≥ 0, or null | That cell's position in its row |
| `rows` | tuple of `LayoutRow` | The table's own rendered rows, in document order |

### `LayoutRow`

| Field | Type | Meaning |
| --- | --- | --- |
| `head` | bool | The row sits in a `thead` |
| `cells` | tuple of `LayoutCell` | Its rendered cells, in document order |

### `LayoutCell`

| Field | Type | Meaning |
| --- | --- | --- |
| `header` | bool | The cell is a `th` |
| `colspan` | int > 0 | Its `colSpan`, at least 1 |
| `rowspan` | int > 0 | Its `rowSpan`, at least 1 |

### `AlignmentFailure`

One layout-1 unit that maps onto no single canonical span (SC13). It carries an
existing core reason; core has no alignment reason.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `status` | `alignment_failed` | Always this value |
| `reason` | `RejectionReason` | `locator_not_found` when the text occurs nowhere; `ambiguous_occurrence` when it occurs more than once and no neighbour decides, or its one place is out of order or overlaps another unit's |
| `unit_type` | string | The unit's layout-1 type, or `table_cell` |
| `text` | string | The unit's text after N1 |
| `detail` | string | Which of the above, in words |

### `LayoutExtraction`

layout-1's element stream over one canonical document, under mapping policy
`anchored-1`, with every alignment failure.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `layout_version` | ID part | `layout-1` |
| `mapping_policy` | ID part | `anchored-1` |
| `capture_id` | string | The capture it read |
| `doc_id` | string | The canonical document it maps onto |
| `units` | int ≥ 0 | Units aligned: each block, and each cell of a table |
| `retypes` | map of rule to int | Blocks retyped by each of `C1`–`C5`, zeros included |
| `elements` | tuple of `DocumentElement` | Document order, each table followed by its cells; canonical text no element covers is `other`, one element per line |
| `failures` | tuple of `AlignmentFailure` | Every unit that did not map |

## earnings-ingestion retrieval records, schema version 1

- **Package.** `earnings_ingestion.fetch`, in `packages/earnings-ingestion` (Stage 4,
  plan 6): retrieval metadata and the artifact store.
- **Schema version.** `Retrieval` joins ingestion schema version `1`, since no
  earlier record's fields changed, and carries it as `schema_version`.
- **Saved artifacts.** An `ArtifactStore` rooted at a directory under `data/raw/`
  stores an artifact as `<root>/<source_id>/<sha256><ext>`. Each retrieval of it gets
  a record at
  `<root>/<source_id>/retrievals/<sha256>/<UTC stamp>-<first 12 hex of the record's hash>.json`.
  `data/raw/` is never committed.

### `Retrieval`

One retrieval of one saved artifact. The identity sent as the User-Agent is never
recorded.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `request_url` | string | The URL requested; for a page a person saved, the URL it was saved from |
| `final_url` | string | The URL after any redirects |
| `retrieved_at` | UTC datetime | When the bytes arrived, or when a person saved them |
| `retrieval_method` | `RetrievalMethod` | How the bytes reached the store |
| `http_status` | int or null | The response's status; null exactly when a person saved the page |
| `media_type` | media type | The Content-Type's lowercase media type, without parameters |
| `content_type` | string | The Content-Type header as received |
| `byte_count` | int ≥ 0 | The body's length, after any Content-Encoding is decoded |
| `sha256` | 64 lowercase hex | SHA-256 of the body |

### `RetrievalMethod`

| Value | Meaning |
| --- | --- |
| `http` | Fetched by a package client, under its access policy |
| `saved_by_user` | Saved by a person in a browser and registered by hash; nothing was fetched |

## earnings-ingestion cohort records, schema version 1

- **Packages.** In `packages/earnings-ingestion` (Stage 4, plan 6):
  - `earnings_ingestion.sec`: the shared SEC client and SEC's record readers;
  - `earnings_ingestion.cohort`: the point-in-time DJIA cohort.
- **Schema version.** These records join ingestion schema version `1`, since no
  earlier record's fields changed. `UniverseManifest` and `LiveVerification` carry
  it as `schema_version`; the nested parts do not.
- **Facts and citations only.** A committed cohort record or curated file carries
  facts, URLs, locators, and hashes, and never a source's wording (the user's
  decision, 2026-09-26). The saved artifacts stay local.
- **Canonical JSON.** Every cohort hash is SHA-256 over canonical JSON
  (`earnings_ingestion.cohort.digests`): sorted keys, separators without whitespace,
  UTF-8 with non-ASCII characters written as themselves, and dates in ISO 8601.

### `EvidenceClass`

What kind of source an item comes from (P §Membership evidence and source rights).

| Value | Meaning |
| --- | --- |
| `official` | The index provider's own statement |
| `secondary` | A dated third-party roster, labeled as secondary evidence |
| `etf_proxy` | A tracking fund's holdings: corroboration only, never the roster |
| `user_supplied` | A list the user supplied: a check, never evidence |

### `SourceRole`

| Value | Meaning |
| --- | --- |
| `anchor` | The dated snapshot the intervals start from |
| `change` | Addition and removal announcements |
| `corroboration` | A dated snapshot the reconstruction must reproduce |
| `check` | A snapshot compared and reported, never holding the freeze |

### `LocatorKind`

| Value | Meaning |
| --- | --- |
| `text_span` | Half-open code-point offsets into an artifact's citation text: walker-1's canonical text for HTML, pdftext-1's text for a PDF |
| `json_pointer` | An RFC 6901 pointer into a JSON artifact |

### `BoundTiming`

When on its date a change takes effect, as the evidence states it.

| Value | Meaning |
| --- | --- |
| `before_open` | Before the open of trading on the date |
| `after_close` | After the close of trading on the date |
| `unspecified` | The evidence gives no time of day; always the anchor's timing |

### `BoundBasis`

| Value | Meaning |
| --- | --- |
| `announced` | An official effective date |
| `anchor_snapshot` | The anchor's date: a lower bound on the start, never an entry date |

### `AssertedAction`

| Value | Meaning |
| --- | --- |
| `member_at` | The anchor lists the security as a member on its date |
| `added` | A change adds the security |
| `removed` | A change removes the security |

### `AssertionStatus`

| Value | Meaning |
| --- | --- |
| `supported` | Consistent with the security's other evidence, and part of an interval |
| `conflicting` | The security's evidence does not form one alternating sequence after the anchor; holds the freeze until a reviewer rejects the wrong assertion |
| `ambiguous` | An addition and a removal of the security share an effective date; holds the freeze the same way |
| `withheld` | First published after the cutoff: kept, never applied (P-C4) |

### `ResolutionStatus`

| Value | Meaning |
| --- | --- |
| `resolved` | One CIK, confirmed by SEC's records or named by an override |
| `unresolved` | No candidate confirmed |
| `conflicting` | More than one CIK confirmed |
| `retained_unresolved` | A reviewer kept it unresolved and excluded it, with a reason |

### `ResolutionMethod`

| Value | Meaning |
| --- | --- |
| `sec_ticker_and_name` | SEC's ticker list proposed the CIK, and SEC's record for it lists the cited ticker under a name, current or former, that covers the cited name |
| `override` | A `set_issuer` override named it |

### `OverrideKind`

| Value | Meaning |
| --- | --- |
| `reject_assertion` | Set aside one conflicting or ambiguous assertion; it stays in the manifest, marked |
| `set_issuer` | Name a security's CIK, citing the evidence |
| `retain_unresolved` | Keep a security unresolved and exclude it from the candidate issuers |
| `acknowledge` | Accept one `member_count` or `difference` finding, bound to its digest |
| `holding_alias` | Match a fund holding's name to a security |

### `FindingKind`

| Value | Meaning |
| --- | --- |
| `missing_anchor` | No usable anchor; blocking, and no override resolves it |
| `membership_conflict` | A security's evidence conflicts; blocking until assertions are rejected |
| `membership_ambiguity` | A security is added and removed on one date; blocking until an assertion is rejected |
| `identity` | An in-scope security without exactly one confirmed CIK; blocking until `set_issuer` or `retain_unresolved` decides it |
| `member_count` | The roster's size differs from the expected count on a date; blocking until acknowledged |
| `difference` | A snapshot disagrees with the reconstruction on its date; blocking until acknowledged, unless it is a check list or was published after the cutoff |
| `gap` | A calendar quarter with no corroborating snapshot; reported |
| `withheld` | Evidence first published after the cutoff; reported |
| `superseded` | A fund filing replaced by a later one for its report date; reported |

### `EvidenceLocator`

Where cited evidence sits in an artifact, and the hash of what it says there.

| Field | Type | Meaning |
| --- | --- | --- |
| `kind` | `LocatorKind` | Which kind of locator |
| `canonicalization_version` | ID part or null | A text span's citation-text policy: `walker-1` for HTML, `pdftext-1` for a PDF; null for a pointer |
| `canonical_sha256` | 64 lowercase hex or null | The hash of the artifact's canonical text, for a text span |
| `start` | int ≥ 0 or null | A text span's first code point |
| `end` | int ≥ 0 or null | A text span's end, exclusive; `start < end` |
| `pointer` | string or null | A JSON pointer: empty, or starting with `/` |
| `cited_sha256` | 64 lowercase hex | SHA-256 of the cited content: the span's UTF-8 text, or the canonical JSON of the pointer's value |

### `Citation`

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | register slug | The source's key in a register |
| `url` | string | Where the artifact came from |
| `artifact` | `ArtifactRef` | The saved bytes: hash, media type, storage path, and rights |
| `retrieved_at` | UTC datetime | The artifact's first retrieval |
| `locators` | tuple of `EvidenceLocator` | The places cited; empty when the whole artifact is the evidence |

### `SourceRights`

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | register slug | The source |
| `evidence_class` | `EvidenceClass` or null | Its class; null for `sec-edgar`, which is identity evidence |
| `rights_status` | `RightsStatus` | What may be done with its content |
| `rights_basis` | string | Why |

### `CitedIdentity`

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_id` | ID part | The curated item whose row states it |
| `observed_on` | date | The row's date: a snapshot's as-of date, or a change's effective date |
| `name` | string | The company name as the row prints it |
| `ticker` | string | The ticker as the row prints it |

### `SecurityRecord`

| Field | Type | Meaning |
| --- | --- | --- |
| `security_id` | ID part | A curated slug for the security, never a ticker |
| `identities` | tuple of `CitedIdentity` | Every row that names it, by date then item; ticker changes stay visible |

### `MembershipAssertion`

One evidence item's statement about one security (P §Data contracts). A change item's
locators are the row's and then the effective date's.

| Field | Type | Meaning |
| --- | --- | --- |
| `membership_assertion_id` | ID part | `<evidence_id>:<security_id>:<asserted_action>` |
| `universe_id` | ID part | The universe |
| `security_id` | ID part | The security |
| `issuer_id` | ID part or null | `cik-<cik>` once resolved |
| `cik` | 10 digits or null | The zero-padded CIK once resolved |
| `asserted_action` | `AssertedAction` | What the item says |
| `asserted_date` | date | The date it says it for |
| `asserted_timing` | `BoundTiming` | The time of day it says |
| `effective_from` | date or null | The start of the interval it supports; null unless `supported` |
| `effective_from_basis` | `BoundBasis` or null | What establishes that start |
| `effective_from_timing` | `BoundTiming` or null | The start's timing |
| `effective_to` | date or null | The interval's exclusive end; null while open |
| `effective_to_timing` | `BoundTiming` or null | The end's timing |
| `announcement_date` | date or null | A change's announcement date |
| `source_snapshot_date` | date or null | A snapshot's as-of date |
| `publication_date` | date | When the item was first published, at date precision |
| `publication_time` | UTC datetime or null | When, if the evidence gives a time |
| `retrieved_at` | UTC datetime | The artifact's first retrieval; never a publication time |
| `source_id` | register slug | The source |
| `evidence_id` | ID part | The curated item |
| `url` | string | Where the artifact came from |
| `evidence_locators` | tuple of `EvidenceLocator` | Where the item states it |
| `raw_content_hash` | 64 lowercase hex | SHA-256 of the saved artifact |
| `rights_status` | `RightsStatus` | The source's rights |
| `status` | `AssertionStatus` | The assertion's standing |
| `resolved_by` | ID part or null | The `reject_assertion` override that set it aside |

### `MembershipInterval`

| Field | Type | Meaning |
| --- | --- | --- |
| `security_id` | ID part | The security |
| `effective_from` | date | Inclusive start |
| `effective_from_basis` | `BoundBasis` | What establishes it |
| `effective_from_timing` | `BoundTiming` | Its timing |
| `effective_to` | date or null | Exclusive end; null when open |
| `effective_to_timing` | `BoundTiming` or null | Its timing |
| `assertion_ids` | tuple of ID part | The supported assertions behind the start and the end |

### `IssuerCandidate`

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_id` | ID part | The row whose ticker proposed it |
| `cited_name` | string | The name on that row |
| `ticker` | string | The ticker on that row |
| `cik` | 10 digits | The CIK SEC's ticker list gives that ticker |
| `sec_name` | string | SEC's current name for the CIK |
| `ticker_listed` | bool | SEC's record for the CIK lists the ticker |
| `matched_name` | string or null | The SEC name, current or former, that covers the cited name |
| `confirmed` | bool | `ticker_listed` and a matched name |
| `citations` | tuple of `Citation` | The ticker-list entry, and the submissions record's name, tickers, and any matched former name |

### `IssuerMapping`

| Field | Type | Meaning |
| --- | --- | --- |
| `security_id` | ID part | The security |
| `status` | `ResolutionStatus` | The outcome |
| `method` | `ResolutionMethod` or null | How it resolved; null unless `resolved` |
| `issuer_id` | ID part or null | `cik-<cik>` when resolved |
| `cik` | 10 digits or null | The CIK when resolved |
| `candidates` | tuple of `IssuerCandidate` | Every candidate checked, confirmed or not |
| `override_id` | ID part or null | The override that decided it |
| `reason` | string or null | Why it is unresolved, or the override's rationale |

### `Issuer`

| Field | Type | Meaning |
| --- | --- | --- |
| `issuer_id` | ID part | `cik-<cik>` |
| `cik` | 10 digits | The zero-padded CIK |
| `sec_name` | string | SEC's current name |
| `former_names` | tuple of string | SEC's former names |
| `security_ids` | tuple of ID part | Its securities; several securities still make one issuer |

### `OverrideCitation`

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | string | The source cited |
| `url` | string | Where the evidence is |
| `artifact_sha256` | 64 lowercase hex or null | A saved artifact the build verifies, when there is one |
| `locator` | `EvidenceLocator` or null | A place in that artifact |

### `Override`

A reviewed manual decision, never a parser branch (P §Issuer resolution). Exactly the
targets its kind needs are set.

| Field | Type | Meaning |
| --- | --- | --- |
| `override_id` | ID part | A curated slug |
| `kind` | `OverrideKind` | The decision |
| `membership_assertion_id` | ID part or null | `reject_assertion`'s target |
| `security_id` | ID part or null | The target of `set_issuer`, `retain_unresolved`, and `holding_alias` |
| `cik` | 10 digits or null | `set_issuer`'s CIK |
| `finding_id` | ID part or null | `acknowledge`'s finding |
| `finding_digest` | 64 lowercase hex or null | The digest of the finding as reviewed |
| `holding_name` | string or null | `holding_alias`'s holding name, exactly as filed |
| `citations` | tuple of `OverrideCitation` | The evidence; required for `set_issuer` |
| `rationale` | string | Why |
| `reviewer` | string | Who decided; the user, never an agent |
| `recorded_on` | date | When |
| `effective_from` | date | The start of the period the decision covers |
| `effective_to` | date or null | Its exclusive end; null when open |

### `Finding`

| Field | Type | Meaning |
| --- | --- | --- |
| `finding_id` | ID part | `<kind>:<subject>` |
| `kind` | `FindingKind` | What was found |
| `blocking` | bool | It holds the freeze until resolved |
| `security_id` | ID part or null | The security concerned, if one |
| `detail` | string | What it says |
| `evidence_ids` | tuple of string | The evidence items concerned |
| `digest` | 64 lowercase hex | SHA-256 of the canonical JSON of the finding's kind, subject, detail, blocking flag, security, and evidence ids |
| `resolved_by` | tuple of ID part | The overrides that resolved it |

### `SnapshotReconciliation`

| Field | Type | Meaning |
| --- | --- | --- |
| `snapshot_id` | ID part | The evidence id, or `<source_id>:<accession>` for a fund filing |
| `source_id` | register slug | The source |
| `evidence_class` | `EvidenceClass` | Its class |
| `as_of` | date | The date it describes |
| `published_on` | date | When it was first published |
| `withheld` | bool | Published after the cutoff: reported only |
| `matched` | tuple of ID part | Securities in both the snapshot and the reconstruction |
| `reconstructed_only` | tuple of ID part | Members the snapshot lacks |
| `snapshot_only` | tuple of ID part | Securities it lists that the reconstruction does not |
| `unmatched` | tuple of string | Holding names or tickers that match no single security |
| `citation` | `Citation` or null | The snapshot's artifact; null for a check list |

### `CohortReport`

The coverage and conflict report (P-A4).

| Field | Type | Meaning |
| --- | --- | --- |
| `universe_id` | ID part | The universe |
| `anchor_evidence_id` | ID part or null | The anchor used; null when none is usable |
| `limitations` | tuple of string | What the evidence cannot show |
| `findings` | tuple of `Finding` | Every finding, by id |
| `reconciliations` | tuple of `SnapshotReconciliation` | Every snapshot compared, by date |

### `UniverseDefinition`

P §Data contracts, universe definition.

| Field | Type | Meaning |
| --- | --- | --- |
| `universe_id` | ID part | The universe across its versions |
| `universe_version` | int ≥ 1 | The version; a new one only when the content changes |
| `universe_name` | ID part | `djia` |
| `period_end_start` | date | `2024-07-01`, inclusive |
| `period_end_stop` | date | `2026-07-01`, exclusive |
| `public_information_cutoff` | date | `2026-09-22` |
| `membership_reference` | `first_publication_time` | The time membership is judged at |
| `expected_member_count` | int ≥ 1 | `30`: the roster's size at every date |
| `source_register_version` | 64 lowercase hex | SHA-256 of the canonical JSON of the register entries the manifest cites, `sec-edgar` always among them |
| `selection_policy_version` | string | `djia-pilot/1`, the rules of P §Deterministic pilot selection |
| `content_hash` | 64 lowercase hex | See the frozen manifest, above |
| `created_at` | UTC datetime | When this version was frozen |

### `UniverseManifest`

The frozen cohort, which Stage 5 joins against.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `definition` | `UniverseDefinition` | The universe |
| `sources` | tuple of `SourceRights` | Every source cited |
| `securities` | tuple of `SecurityRecord` | Every security the evidence names |
| `assertions` | tuple of `MembershipAssertion` | Every assertion, whatever its status |
| `intervals` | tuple of `MembershipInterval` | The derived intervals |
| `mappings` | tuple of `IssuerMapping` | One per security |
| `issuers` | tuple of `Issuer` | One per resolved CIK |
| `candidate_issuer_ids` | tuple of ID part | Issuers of the securities whose intervals meet `[period_end_start, cutoff]` |
| `overrides` | tuple of `Override` | Every reviewed decision applied |
| `report` | `CohortReport` | The coverage and conflict report |

### `LiveCheck`

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | register slug | The source |
| `purpose` | `terms` or `evidence` | A terms page, or a curated evidence page |
| `url` | string | What was requested |
| `outcome` | `unchanged`, `changed`, `refused`, or `failed` | What it found |
| `detail` | string | The hashes compared, or the refusal or error |
| `retrieval` | `Retrieval` or null | The request's metadata; null when nothing was received |

### `LiveVerification`

The opt-in live verification's result (P-VL), saved under `data/runs/cohort/live/`.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `checked_at` | UTC datetime | When it ran |
| `checks` | tuple of `LiveCheck` | Every live request |
| `build_problems` | tuple of string | Why the rebuild stopped, if it did |
| `rebuilt_content_hash` | 64 lowercase hex or null | The rebuilt cohort's content hash |
| `frozen_content_hash` | 64 lowercase hex or null | The latest frozen version's |
| `blocking_finding_ids` | tuple of ID part | Findings that would hold a freeze now |

## Curated cohort files

`config/universe/<name>/` holds three curated files, and
`docs/membership-source-register.toml` holds the register. Each file is read as TOML,
then canonical JSON, into strict models, so an unknown key is refused.

- `universe.toml` is one `UniverseConfig`.
- `evidence.toml` is an `EvidenceFile`.
- `overrides.toml` is an `OverridesFile` of `Override` records.

### `UniverseConfig`

| Field | Type | Meaning |
| --- | --- | --- |
| `universe_id` | ID part | Copied to the definition |
| `universe_name` | ID part | `djia` |
| `period_end_start` | date | Copied to the definition |
| `period_end_stop` | date | Copied to the definition |
| `public_information_cutoff` | date | Copied to the definition |
| `membership_reference` | `first_publication_time` | Copied to the definition |
| `selection_policy_version` | string | Copied to the definition |
| `expected_member_count` | int ≥ 1 | Copied to the definition |
| `etf_proxy` | `EtfProxy` or null | The corroborating fund |

### `EtfProxy`

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | register slug | The fund's membership-register source |
| `cik` | 10 digits | The fund's CIK |
| `forms` | tuple of string | The forms read, `NPORT-P` and `NPORT-P/A` |

### `EvidenceFile`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | The file's version |
| `snapshots` | tuple of `SnapshotEvidence` | At most one is the anchor |
| `changes` | tuple of `ChangeEvidence` | Official announcements |
| `checks` | tuple of `CheckList` | Lists compared and reported only |

### `SnapshotEvidence`

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_id` | ID part | A curated slug, unique in the file |
| `source_id` | register slug | Registered for the role |
| `url` | string | A URL the artifact was retrieved or saved from |
| `artifact_sha256` | 64 lowercase hex | The saved artifact |
| `canonical_sha256` | 64 lowercase hex | Its citation text's hash: walker-1's for HTML, pdftext-1's for a PDF |
| `published_on` | date | First publication, as the source states it |
| `published_at` | UTC datetime or null | The time, if stated |
| `role` | `anchor` or `corroboration` | Its use |
| `as_of` | date | The date it describes |
| `members` | tuple of `Row` | Each listed security, with where it is listed |

### `ChangeEvidence`

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_id` | ID part | A curated slug, unique in the file |
| `source_id` | register slug | An official source registered for `change` |
| `url` | string | A URL the artifact was retrieved or saved from |
| `artifact_sha256` | 64 lowercase hex | The saved artifact |
| `canonical_sha256` | 64 lowercase hex | Its citation text's hash: walker-1's for HTML, pdftext-1's for a PDF |
| `published_on` | date | First publication |
| `published_at` | UTC datetime or null | The time, if stated |
| `announced_on` | date | The announcement's date |
| `effective_on` | date | The effective date it states |
| `timing` | `BoundTiming` | The time of day it states |
| `date_span` | two ints | Where it states the date: `[start, end)` in the canonical text |
| `date_cited_sha256` | 64 lowercase hex | SHA-256 of that text |
| `entries` | tuple of `ChangeRow` | Each addition and removal |

### `Row`

| Field | Type | Meaning |
| --- | --- | --- |
| `security_id` | ID part | The security |
| `name` | string | The name exactly as the cited text prints it |
| `ticker` | string | The ticker exactly as the cited text prints it |
| `span` | two ints | Where the text states both: `[start, end)` in the canonical text |
| `cited_sha256` | 64 lowercase hex | SHA-256 of that text |

### `ChangeRow`

| Field | Type | Meaning |
| --- | --- | --- |
| `security_id` | ID part | The security |
| `name` | string | The name exactly as the cited text prints it |
| `ticker` | string | The ticker exactly as the cited text prints it |
| `span` | two ints | Where the text states both |
| `cited_sha256` | 64 lowercase hex | SHA-256 of that text |
| `action` | `added` or `removed` | The change |

### `CheckList`

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_id` | ID part | A curated slug |
| `source_id` | register slug | Registered for `check` |
| `as_of` | date | The date the list describes |
| `published_on` | date | When it was supplied |
| `members` | tuple of `CheckMember` | Its entries, compared by ticker |

### `CheckMember`

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | As supplied |
| `ticker` | string | As supplied |

### `OverridesFile`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | The file's version |
| `overrides` | tuple of `Override` | Unique `override_id`s, and at most one `holding_alias` per `holding_name` |

### `MembershipRegister`

`docs/membership-source-register.toml`: A §242's fields for index-membership sources.
It is the second register, beside `docs/source-register.toml`, and it quotes no
source.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | The file's version |
| `sources` | map of register slug to `RegisterEntry` | One entry per source |

### `RegisterEntry`

| Field | Type | Meaning |
| --- | --- | --- |
| `owner` | string | Who publishes it |
| `url` | string | Its home |
| `access_method` | string | How the project reaches it, and through which client |
| `cost` | string | What access costs |
| `license_terms` | string | The terms, summarized in the project's words |
| `terms_url` | string or null | The terms page; null only for a user-supplied list |
| `terms_sha256` | 64 lowercase hex or null | The terms page's hash when a person last read it: SHA-256 of its `walker-1` canonical text for an HTML page, of its bytes otherwise |
| `redistribution_status` | string | What may be redistributed |
| `coverage` | string | What it covers |
| `expected_update_pattern` | string | How it changes |
| `known_limitations` | tuple of string | What it cannot show |
| `last_verified` | date | When a person last checked the entry |
| `evidence_class` | `EvidenceClass` | Its class |
| `roles` | tuple of `SourceRole` | Its permitted uses |
| `rights_status` | `RightsStatus` | Unclear rights are `local_only` |
| `rights_basis` | string | Why |

## Frozen cohort manifests

- **Where.** `config/universe/<name>/manifests/<universe_id>-v<version>.json` holds
  one `UniverseManifest` as indented JSON with sorted keys, written once and never
  replaced. The synthetic cohort's is under `tests/fixtures/cohort/manifests/`.
- **The content hash.** `content_hash` covers the manifest's canonical JSON without
  `universe_version`, `content_hash`, and `created_at`. Identical content keeps its
  version; new content takes the next.
- **Reading.** `earnings_ingestion.cohort.freeze.load_manifest` rechecks that hash
  and the file's name, and needs no saved artifact.
- **Saved artifacts.** The cohort's are under `data/raw/cohort/`, which is never
  committed; the synthetic cohort's are under `tests/fixtures/cohort/raw/`.

## earnings-ingestion event records, schema version 1

- **Package.** `earnings_ingestion.events`, in `packages/earnings-ingestion` (Stage 5,
  plan 7): event discovery, eligibility, and the event and pilot freezes.
- **Schema version.** These records join ingestion schema version `1`, since no
  earlier record's fields changed. `EventManifest` and `EventEvidence` carry it as
  `schema_version`; the nested parts do not.
- **Facts, not incidental evidence** (EV11). An event row or finding holds facts
  only: never a retrieval time, or a pointer into one saved file. What each row rests
  on, cited with its retrieval time, sits in the evidence record, outside the
  manifest's hash. An override is hashed whole, and its citations carry the cited
  artifact's hash and a locator. So a re-fetch re-versions no manifest while the store
  keeps each cited artifact; in a fresh store, a cited page served with other bytes
  must be re-cited, which re-versions the manifest and re-seeds the pilot.
- **Times.** Every time is a UTC instant. Every date judgment reads the instant's
  date on the America/New_York calendar (EV10).

### `Convention`

How a submissions file writes `acceptanceDateTime` (S Finding 1).

| Value | Meaning |
| --- | --- |
| `utc` | The true UTC instant |
| `eastern_digits` | The instant's Eastern wall-clock digits, followed by `Z` |

### `EventStatus`

| Value | Meaning |
| --- | --- |
| `eligible` | The issuer was a member when the release was first published |
| `ineligible` | Outside the window, published after the cutoff, or not a member |
| `ambiguous` | Unidentified release filing, or membership unordered at publication |

### `EventReason`

The first of `eligibility/1`'s checks that applies decides (S §Eligibility).

| Value | Meaning |
| --- | --- |
| `period_end_outside_window` | Check 1: `period_end` is outside `[2024-07-01, 2026-07-01)`; `ineligible` |
| `no_release_filing` | Check 2: no candidate is left; `ambiguous` |
| `several_release_filings` | Check 2: more than one candidate is left; `ambiguous` |
| `published_after_cutoff` | Check 3: the release's Eastern date is after the cutoff; `ineligible` |
| `member_at_publication` | Check 4: a security's interval holds the publication time; `eligible` |
| `not_member_at_publication` | Check 4: no interval holds it, and none is unordered; `ineligible` |
| `same_day_transition` | Check 4: a bound on the release's date leaves it unordered; `ambiguous` |

### `IdentificationMethod`

| Value | Meaning |
| --- | --- |
| `stated_period` | `release-id/1` left one candidate, whose Item 2.02 text states the slot's period |
| `sole_candidate` | `release-id/1` left one candidate, whose text states no period that is judged |
| `override` | A reviewer's `set_release_filing` named it |

### `EventFindingKind`

| Value | Meaning |
| --- | --- |
| `period_gap` | An in-window period end may be missing; blocking until acknowledged |
| `no_slots` | A candidate issuer has no slot; blocking until acknowledged |
| `fiscal_labels_unknown` | Companyfacts gives the periodic report no agreeing `fy` and `fp`, where a blank `fp` or an `fy` below 1 states none; not blocking |
| `acceptance_time_mismatch` | A cross-checked `acceptanceDateTime` follows neither convention; blocking |
| `acceptance_time_unknown` | A filing's side of the cutoff or range turns on a convention its file does not establish, or on a missing value; blocking until its index page is saved (P7-8) |

### `EventOverrideKind`

| Value | Meaning |
| --- | --- |
| `set_release_filing` | Name an event's release filing, citing it |
| `retain_unresolved` | Keep an `ambiguous` event with its reason, excluded from the pilot |
| `acknowledge` | Accept one `period_gap` or `no_slots` finding, bound to its digest |

### `EventRow`

One slot: an issuer's period end, its release filing, and its eligibility. It serves
as P's expected event and as Stage 15's ledger entry.

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | `<issuer_id>:<period_end>` |
| `issuer_id` | ID part | The cohort's issuer |
| `cik` | 10 digits | The issuer's CIK |
| `period_end` | date | The periodic report's `reportDate` |
| `reported_fiscal_year` | int or null | Companyfacts' `fy` for the periodic report; null when unknown |
| `reported_fiscal_quarter` | string or null | Its `fp` as written, such as `Q1` or `FY`; null when unknown |
| `periodic_accession` | accession | The original 10-Q, 10-K, 10-QT, or 10-KT that made the slot |
| `periodic_form` | `10-Q`, `10-K`, `10-QT`, or `10-KT` | Its form |
| `release_accession` | accession or null | The release filing; null when unidentified |
| `candidate_accessions` | tuple of accession | The slot's candidates, by accession, each once |
| `identification_method` | `IdentificationMethod` or null | How the release filing was identified |
| `filing_acceptance_time` | UTC datetime or null | The release filing's index-page Accepted value, read in America/New_York |
| `first_publication_time` | UTC datetime or null | Equal to `filing_acceptance_time`: an upper bound on first availability (EV9) |
| `source_timezone` | `America/New_York` | The zone the Accepted value is read in |
| `first_publication_source_id` | `sec-edgar` or null | The source of `first_publication_time` |
| `membership_assertion_id` | ID part or null | The assertion that decided check 4; null when an earlier check decided |
| `eligibility_status` | `EventStatus` | The status |
| `eligibility_reason` | `EventReason` | The reason, which implies the status |
| `retained` | bool | An `ambiguous` event kept by `retain_unresolved`, and excluded from the pilot |
| `override_ids` | tuple of ID part | The overrides applied to the event |

### `EventFinding`

| Field | Type | Meaning |
| --- | --- | --- |
| `finding_id` | ID part | `<kind>:<subject>` |
| `kind` | `EventFindingKind` | What was found |
| `blocking` | bool | It holds the freeze until resolved |
| `issuer_id` | ID part or null | The issuer concerned, if one |
| `detail` | string | What it says, in facts only |
| `digest` | 64 lowercase hex | SHA-256 of the canonical JSON of the finding's kind, subject, detail, blocking flag, and issuer |
| `resolved_by` | tuple of ID part | The acknowledgements that resolved it |

### `EventOverride`

A reviewer's decision (S §Review overrides). Exactly the targets its kind needs are
set.

| Field | Type | Meaning |
| --- | --- | --- |
| `override_id` | ID part | A curated slug |
| `kind` | `EventOverrideKind` | The decision |
| `event_id` | ID part or null | The event of `set_release_filing` and `retain_unresolved` |
| `accession` | accession or null | `set_release_filing`'s filing: an 8-K or 8-K/A of the issuer, accepted after the event's period end and by the cutoff, whose index page is saved, and the release of no other event |
| `reason` | `EventReason` or null | `retain_unresolved`'s reason, one that makes the event `ambiguous` |
| `finding_id` | ID part or null | `acknowledge`'s finding |
| `finding_digest` | 64 lowercase hex or null | The digest of the finding as reviewed |
| `citations` | tuple of `OverrideCitation` | The evidence; required for `set_release_filing`, where at least one cites an SEC artifact in the filing's folder, retrieved from its own URL, at a locator that verifies |
| `rationale` | string | Why |
| `reviewer` | string | Who decided; the user, never an agent |
| `recorded_on` | date | When |

### `EventOverridesFile`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | The file's version |
| `overrides` | tuple of `EventOverride` | Unique `override_id`s, and at most one override of each kind per `event_id` |

### `EventManifestDefinition`

| Field | Type | Meaning |
| --- | --- | --- |
| `corpus_id` | ID part | `djia-2024q3-2026q2` |
| `event_manifest_version` | int ≥ 1 | The version; a new one only when the content changes |
| `universe_id` | ID part | The cohort read |
| `universe_version` | int ≥ 1 | The cohort version read; outside the content hash (P7-2) |
| `universe_operative_hash` | 64 lowercase hex | That version's `operative_hash` (EV4) |
| `discovery_policy_version` | string | `release-id/1` |
| `eligibility_policy_version` | string | `eligibility/1` |
| `public_information_cutoff` | date | `2026-09-22`, on the Eastern calendar |
| `content_hash` | 64 lowercase hex | See the frozen event manifests, below |
| `created_at` | UTC datetime | When this version was frozen |

### `EventManifest`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `definition` | `EventManifestDefinition` | The definition |
| `rows` | tuple of `EventRow` | One per slot, sorted by `event_id` |
| `findings` | tuple of `EventFinding` | Every finding, sorted by `finding_id` |
| `overrides` | tuple of `EventOverride` | Every override applied, sorted by `override_id` |

### `FileEvidence`

| Field | Type | Meaning |
| --- | --- | --- |
| `url` | string | A submissions file or older page the build read |
| `sha256` | 64 lowercase hex | Its bytes' hash |
| `retrieved_at` | UTC datetime | When they were retrieved |
| `convention` | `Convention` or null | The convention its cross-checked rows share; null when none was cross-checked, or they follow both |
| `rows_cross_checked` | int ≥ 0 | Its rows whose index page is saved |

### `SkippedPage`

| Field | Type | Meaning |
| --- | --- | --- |
| `url` | string | An older page the build did not read |
| `filing_from` | date | Its first filing date |
| `filing_to` | date | Its last. A page is skipped when this range misses `[2024-07-01, 2026-09-22]` |

### `EventCitations`

What one event rests on. Every citation is a Stage 4 `Citation`: an index page or
primary document through `walker-1`'s text, and a JSON file by pointer.

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | The event |
| `periodic_row` | `Citation` | The periodic report's submissions row |
| `labels` | `Citation` or null | Its companyfacts `accn`, `fy`, and `fp`; null when unknown |
| `candidates` | tuple of `Citation` | Each candidate's index page, at its Accepted value |
| `amendments` | tuple of `Citation` | Each 8-K/A in the slot's range, at its Accepted value: recorded, never chosen by the rule |
| `release` | `Citation` or null | The release filing's index page, at its Accepted value |
| `item_text` | `Citation` or null | The release's Item 2.02 text; null when its primary document is not saved or states none |
| `cross_check` | `Citation` or null | The release's submissions row, at `acceptanceDateTime` |

### `EventEvidence`

`events-v<N>.evidence.json`, written beside a frozen manifest and never replaced
(EV11).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `corpus_id` | ID part | The corpus |
| `event_manifest_version` | int ≥ 1 | The manifest it belongs to |
| `event_manifest_hash` | 64 lowercase hex | That manifest's `content_hash` |
| `limitations` | tuple of string | What the evidence cannot show |
| `files` | tuple of `FileEvidence` | Every submissions file and older page read |
| `skipped_pages` | tuple of `SkippedPage` | Every older page skipped by its dates |
| `events` | tuple of `EventCitations` | One per row |

## Frozen event manifests

- **Where.** `config/corpus/<corpus_id>/events-v<N>.json` holds one `EventManifest`,
  and `events-v<N>.evidence.json` beside it holds that version's `EventEvidence`. Each
  is indented JSON with sorted keys, written once and never replaced, and the evidence
  record is written first. The synthetic corpus's are in `tests/fixtures/events/`.
- **One corpus a directory.** A file names its version, not its corpus, so
  `frozen_event_manifests` refuses a directory whose manifests name more than one
  `corpus_id`, and `freeze_events` refuses a build of a corpus other than the one
  the directory holds.
- **The content hash.** `content_hash` covers the canonical JSON of the definition,
  less `event_manifest_version`, `universe_version`, `content_hash`, and `created_at`,
  with the rows, the findings, and the overrides. Identical content keeps its version,
  whatever its evidence record would say; new content takes the next.
- **Reading.** `earnings_ingestion.events.freeze.load_event_manifest` rechecks that
  hash and the file's name. `load_event_evidence(path, manifest)` rechecks the
  evidence record's name, and refuses it, naming the field, unless its `corpus_id`,
  `event_manifest_version`, and `event_manifest_hash` are the manifest's `corpus_id`,
  version, and `content_hash`, and its events' `event_id`s are the manifest's rows in
  order. `earnings_ingestion.events.evidence.check_evidence` verifies every citation
  against a store's saved bytes.
- **Saved artifacts.** Discovery's are under `data/raw/events/`, which is never
  committed; the synthetic layer's are under `tests/fixtures/events/raw/`.

## earnings-ingestion pilot records, schema version 1

- **Package.** The records are in `earnings_ingestion.events.records`, and the policy,
  `djia-pilot/1`, in `earnings_ingestion.events.pilot` (Stage 5, plan 7).
- **Schema version.** These records join ingestion schema version `1`.
  `PilotManifest` carries it as `schema_version`; the nested parts do not.
- **Inputs.** The pilot reads a frozen event manifest's `eligible` rows, and the
  membership transitions of the universe manifest that event manifest read (P7-20).
  No acquisition, parse, or later outcome is an input.

### `SelectionReason`

Why `djia-pilot/1` took an event (S §Pilot selection).

| Value | Meaning |
| --- | --- |
| `issuer_coverage` | Step 1: the issuer's event from the quarter with the fewest selections so far |
| `membership_boundary` | Step 2: the nearest eligible event on a transition's member side |
| `quarter_coverage` | Step 3: an event of a quarter with no selection, from the issuer with the fewest |
| `longitudinal_fill` | Step 5: the event farthest, in days, from its issuer's nearest selected `period_end` |

### `TransitionKind`

| Value | Meaning |
| --- | --- |
| `entry` | The issuer's membership starts: a start, not an `anchor_snapshot`, whose day before no interval of the issuer holds |
| `exit` | The issuer's membership ends: an end whose day no interval of the issuer holds |

### `PilotRow`

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | An `eligible` event of the event manifest the pilot names |
| `selection_order` | int ≥ 1 | The order taken, from 1 |
| `selection_reason` | `SelectionReason` | The step that took it |

### `MembershipTransition`

An issuer-level entry or exit dated in `[2024-07-01, 2026-09-22]`, read from the
universe's intervals by day. A second security joining a member issuer is not one,
and nor is a same-day handoff between two of its securities.

| Field | Type | Meaning |
| --- | --- | --- |
| `issuer_id` | ID part | The issuer |
| `kind` | `TransitionKind` | Entry or exit |
| `effective_date` | date | The bound's date |
| `assertion_ids` | tuple of ID part | The assertions that set the bound |

### `PilotDefinition`

| Field | Type | Meaning |
| --- | --- | --- |
| `pilot_id` | ID part | `<corpus_id>-pilot`, such as `djia-2024q3-2026q2-pilot` |
| `pilot_version` | int ≥ 1 | The version; a new one only when the content changes |
| `universe_version` | int ≥ 1 | The cohort version read; outside the content hash (P7-2) |
| `universe_operative_hash` | 64 lowercase hex | Its `operative_hash`, which the event manifest records too (EV4) |
| `event_manifest_version` | int ≥ 1 | The event manifest drawn from |
| `eligible_event_manifest_hash` | 64 lowercase hex | That manifest's `content_hash` |
| `selection_policy_version` | string | `djia-pilot/1` |
| `selection_seed` | 64 lowercase hex | SHA-256 of the canonical JSON of `eligible_event_manifest_hash`, `selection_policy_version`, and `universe_operative_hash` |
| `target` | int ≥ 1 | 40, or every eligible event when there are fewer |
| `underfilled` | bool | Fewer than 40 eligible events, so the target is all of them |
| `content_hash` | 64 lowercase hex | See the frozen pilots, below |
| `created_at` | UTC datetime | When this version was frozen |

### `PilotManifest`

`pilot-v<N>.json`: the frozen selection.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `definition` | `PilotDefinition` | The definition |
| `rows` | tuple of `PilotRow` | The selected events in `selection_order`, as many as `target` |
| `unmatched_transitions` | tuple of `MembershipTransition` | Each transition with no eligible event on its member side, within the membership spell it opens or closes (a clarification under `djia-pilot/1`, 2026-09-27): reported, not refused. Sorted by date, issuer, and kind |

## Frozen pilots

- **Where.** `config/corpus/<corpus_id>/pilot-v<N>.json` holds one `PilotManifest`,
  beside the event manifest it names. It is indented JSON with sorted keys, written
  once and never replaced. The synthetic corpus's is in `tests/fixtures/events/`.
- **One corpus a directory.** `pilot_id` names the corpus alone, whatever the
  policy, so a later policy's pilot shares it. `frozen_pilots` refuses a directory
  whose pilots name more than one `pilot_id`, and `freeze_pilot` refuses a pilot of
  a corpus other than the one the directory holds.
- **The content hash.** `content_hash` covers the canonical JSON of the definition,
  less `pilot_version`, `universe_version`, `content_hash`, and `created_at`, with the
  rows and the unmatched transitions. Identical content keeps its version; new
  content takes the next. A new event manifest or a new policy gives a new seed, and
  so a new version.
- **Reading.** `earnings_ingestion.events.pilot.load_pilot` rechecks the chain: the
  pilot's hash and name; the event manifest it names, in the same directory, by its
  content hash; the universe's operative hash, computed again from the universe
  manifest; the seed; and that every row is an eligible event of that manifest.
