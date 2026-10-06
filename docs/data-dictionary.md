# Data dictionary

The shared contracts, their fields, and their versions (AGENTS.md §187–191). Each
table below lists every field or value of one contract;
`tests/contracts/test_data_dictionary.py` fails when a field or value changes without
this file changing too.

## earnings-core contracts, schema version 2

- **Package.** `packages/earnings-core`, imported as `earnings_core`.
- **Schema version.** `2` (`earnings_core.SCHEMA_VERSION`). Every top-level record
  carries it as `schema_version`, and a payload with another version is refused.
- **Validator version.** `"3"` (`earnings_core.VALIDATOR_VERSION`), stamped on every
  `Rejection` and `VerifiedSpan`. Caches key on it (R14.6); bump it whenever a check
  changes. Version 3 (Stage 7) refuses an unvalidated offset that is not exactly an
  `int`, or is a `bool`, as `malformed_record`, where version 2 raised, returned
  another check's reason, or, for an `int` subclass, accepted the span, since the
  offset check now runs first; and it resolves a pointer to the document version's
  genuine element wherever it sits in the list. No committed record stores it.
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
text, never copied from a candidate (A §523). A stored one is verified again with
`reverify_span` at each later gate, since its type alone is not proof.

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

`parse_span_candidate` records `malformed_record`, and so does `validate_span` for an
offset that is not exactly an `int`, or is a `bool`, on a candidate that skipped
parsing. `validate_span` then runs its checks in the order of the next eleven rows
and records the first failure.

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
  (`earnings_core.canonical_json` and `earnings_core.digest`, which every record
  hash uses): sorted keys, separators without whitespace, UTF-8 with non-ASCII
  characters written as themselves, and dates in ISO 8601.

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
| `requests_sent` | non-negative integer or null | The requests both clients sent, each capped at the approved `--max-requests`; null in a record saved before plan 8 kept it |

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
  version; new content takes the next. Every consumer reads the latest version, so
  `freeze` refuses a build that holds an older version's content, and
  `frozen_manifests` refuses two versions of one content (PR #6's review, F4, F22).
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
| `accession` | accession or null | `set_release_filing`'s filing: an 8-K or 8-K/A of the issuer, accepted, on the Eastern calendar, after the event's period end and by the issuer's next period end (by the cutoff when none is visible), whose index page is saved, and the release of no other event |
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

### `AcquisitionOverride`

A reviewer's choice of an event's release document (S §What acquisition can change;
plan 8, P8-11). `events acquire` applies it; no manifest hashes it.

| Field | Type | Meaning |
| --- | --- | --- |
| `override_id` | ID part | A curated slug |
| `kind` | `"set_release_document"` | The decision |
| `event_id` | ID part | A pilot event |
| `accession` | accession | The filing: the event's frozen release filing, or another filing by the issuer, whose index page is saved |
| `exhibit` | string | The document's file name on that filing's index page |
| `citations` | tuple of `OverrideCitation` | At least one; one cites an SEC artifact in the filing's folder, retrieved from its own URL, at a locator that verifies |
| `rationale` | string | Why |
| `reviewer` | string | Who decided; the user, never an agent |
| `recorded_on` | date | When |

### `AcquisitionOverridesFile`

`config/corpus/<corpus_id>/acquisition-overrides.toml`.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | The file's version |
| `overrides` | tuple of `AcquisitionOverride` | Unique `override_id`s and `event_id`s |

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
  the directory holds. Listing the versions also refuses two that hold one content,
  and a manifest whose evidence record is missing (PR #6's review, F22).
- **The current version.** The build decides it: `current_events(build, directory)`
  is the version that holds the build's content, which a revert makes an earlier
  one. It refuses while the build holds the freeze, and when no version holds the
  content. `events select` and `events acquire` read it, and print its version and
  hash (PR #6's review, F4; plan 8, P8-4).
- **The content hash.** `content_hash` covers the canonical JSON of the definition,
  less `event_manifest_version`, `universe_version`, `content_hash`, and `created_at`,
  with the rows, the findings, and the overrides. Identical content keeps its version,
  whatever its evidence record would say; new content takes the next.
- **Reading.** `earnings_ingestion.events.freeze.load_event_manifest` rechecks that
  hash and the file's name. `load_event_evidence(path, manifest)` rechecks the
  evidence record's name and the manifest's content hash, and refuses the record,
  naming the field, unless its `corpus_id`,
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
  whose pilots name more than one `pilot_id`, or two versions of one content (F22),
  and `freeze_pilot` refuses a pilot of a corpus other than the one the directory
  holds.
- **The content hash.** `content_hash` covers the canonical JSON of the definition,
  less `pilot_version`, `universe_version`, `content_hash`, and `created_at`, with the
  rows and the unmatched transitions. Identical content keeps its version; new
  content takes the next. A new event manifest or a new policy gives a new seed, and
  so a new version.
- **Reading.** `earnings_ingestion.events.pilot.load_pilot` rechecks the chain: the
  pilot's hash and name; the event manifest it names, in the same directory, by its
  content hash; the universe's operative hash, computed again from the universe
  manifest; the seed; and that every row is an eligible event of that manifest. It
  then selects again: the pilot must name `djia-pilot/1`, and the policy run over
  its event manifest and universe must reproduce its `content_hash` (PR #6's review,
  F10).
- **The current pilot.** `current_pilot(directory, events, universe)` is the pilot
  frozen over the current event manifest, loaded by `load_pilot` (F4).

## earnings-ingestion processing-state records, schema version 1

- **Package.** The records, and the transitions R1.4 allows, are in
  `earnings_ingestion.events.states`; the table's Parquet schema is in
  `earnings_ingestion.events.state_table` (Stage 5, plan 8).
- **Schema version.** These records join ingestion schema version `1`.
  `StateTransition` carries it as `schema_version`; `ExhibitAttempt` does not.
- **Documents.** Each pilot event expects one document, its release, whose
  `document_id` is `<event_id>:release`.

### `DocumentState`

R1.4's processing states. A §644's `available` is `acquired`, and its `processed` is
`completed` or `completed-no-theme`.

| Value | Meaning |
| --- | --- |
| `expected` | A pilot event's release, before it is attempted |
| `acquired` | A candidate exhibit's bytes are saved |
| `parsed` | A candidate canonicalized, and `release-content/1` confirmed it or an acquisition override named it |
| `failed` | No candidate was confirmed, and one failed to canonicalize |
| `unavailable` | No candidate could be fetched, or every one fetched canonicalized and none was confirmed |
| `restricted` | The source's rights forbid local processing; fixtures only, since SEC documents are public |
| `partial` | Set by a later stage; fixtures only in Stage 5 |
| `completed` | Set by a later stage; fixtures only in Stage 5 |
| `completed-no-theme` | Set by a later stage, which found no theme; fixtures only in Stage 5 |

### `MissingReason`

| Value | Meaning |
| --- | --- |
| `not_yet_checked` | `expected`: not attempted yet |
| `not_found` | `unavailable`: no candidate exhibit could be fetched |
| `no_confirmed_release` | `unavailable`: every candidate fetched canonicalized, and none was confirmed |
| `rights_restricted` | `restricted`: the source's rights forbid local processing |
| `parse_failed` | `failed`: `failure_reason` gives Stage 3's reason |

### `ExhibitChoice`

Why an exhibit was tried, in R1.2's order.

| Value | Meaning |
| --- | --- |
| `named` | The Item 2.02 text names its number, such as "Exhibit 99.1" |
| `described` | Its description on the index page names a release |
| `lowest_sequence` | Neither: the rest, lowest sequence first |
| `override` | A `set_release_document` override names it |

### `AttemptOutcome`

| Value | Meaning |
| --- | --- |
| `confirmed` | It canonicalized, and `release-content/1` confirmed it |
| `not_confirmed` | It canonicalized, and `release-content/1` did not confirm it |
| `canonicalization_failed` | `walker-1` refused it, with a `FailureReason` |
| `not_fetched` | The client refused its response: a status other than 200, an unexpected media type, or a redirect |

### `ExhibitAttempt`

| Field | Type | Meaning |
| --- | --- | --- |
| `accession` | accession | The filing that lists the exhibit |
| `filename` | string | The exhibit's file name on the index page |
| `exhibit_type` | string | Its type on the index page, such as `EX-99.1` |
| `choice` | `ExhibitChoice` | Why it was tried |
| `outcome` | `AttemptOutcome` | What the attempt came to |
| `artifact_sha256` | 64 lowercase hex or null | The saved bytes' SHA-256; exactly when it was fetched |
| `failure_reason` | `FailureReason` or null | Exactly when canonicalization failed |
| `detail` | string or null | What confirmation lacked, `walker-1`'s failure detail, or the client's refusal |

### `StateTransition`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `document_id` | ID part | `<event_id>:release` |
| `event_id` | ID part | The pilot event |
| `run_id` | ID part | The run that recorded it, and its file's name |
| `sequence` | int ≥ 0 | Its position in its run |
| `recorded_at` | UTC datetime | When it was recorded |
| `from_state` | `DocumentState` or null | The state before; null at the start |
| `to_state` | `DocumentState` | The state after; `NEXT` allows it from `from_state` |
| `missing_reason` | `MissingReason` or null | Exactly for `expected`, `unavailable`, `restricted`, and `failed` |
| `failure_reason` | `FailureReason` or null | Exactly for `failed` |
| `pilot_id` | ID part | The pilot the run read |
| `pilot_version` | int ≥ 1 | Its version |
| `pilot_hash` | 64 lowercase hex | Its `content_hash`, which scopes the current state |
| `frozen_accession` | accession | The event manifest's `release_accession` for the event |
| `accession` | accession or null | The filing whose exhibit was acquired: the frozen one, or an override's |
| `exhibit` | string or null | The acquired exhibit's file name |
| `artifact_sha256` | 64 lowercase hex or null | Its saved bytes' SHA-256 |
| `retrieved_at` | UTC datetime or null | When those bytes were retrieved |
| `doc_id` | string or null | Its `walker-1` canonical document, for `parsed` |
| `override_id` | ID part or null | The acquisition override applied; needed to leave `failed` or `unavailable` |
| `corpus_error` | string or null | Set when the override's filing would change the event's eligibility, for the next corpus version |
| `attempts` | tuple of `ExhibitAttempt` | Every exhibit tried, in order, on the transition that concludes them |

## Processing-state runs

- **Where.** `data/runs/events/states/<run_id>.parquet` holds one run's transitions
  as a Polars frame of `state_table.SCHEMA`. It is written once, atomically, and
  never replaced or committed.
- **Order.** Runs are ordered by their earliest `recorded_at`, then `run_id`, and
  each run's transitions by `sequence`, so a clock that steps back during a run
  cannot reorder it. A document's transitions must chain from `expected`.
- **The current state.** A document's current state is its latest transition among
  those recorded under the current pilot's `pilot_hash`, so a revert to an earlier
  pilot never inherits a later pilot's history.
- **Canonical documents.** `data/runs/events/canonical/<doc_id>.json` holds each
  parsed release's `walker-1` document in the canonical fixture format. It is
  written once; a later run keeps one that differs only in the Python, lxml, and
  libxml2 versions its manifest records, as another environment writes it, and
  reports any other difference as a problem.
## earnings-ingestion coverage records, schema version 1

`earnings_ingestion.events.coverage` builds Stage 6's D4 coverage report from the
state table: the observed state of each pinned pilot document, read only from the
runs the report names (the Stage 6 spec, §The coverage report; GS8).

### `PilotPin`

GS2's pin: the pilot, its event manifest, and its universe, each by version and hash.

| Field | Type | Meaning |
| --- | --- | --- |
| `pilot_id` | ID part | The pilot's ID |
| `pilot_version` | int ≥ 1 | Its version |
| `pilot_hash` | 64 lowercase hex | Its `content_hash` |
| `events_version` | int ≥ 1 | The event manifest it selected from |
| `events_hash` | 64 lowercase hex | That manifest's `content_hash` |
| `universe_version` | int ≥ 1 | The universe the pilot was selected over |
| `universe_operative_hash` | 64 lowercase hex | That universe's `operative_hash` |

### `StateCount`

| Field | Type | Meaning |
| --- | --- | --- |
| `state` | `DocumentState` | A processing state |
| `count` | int ≥ 0 | The pilot documents whose current state it is |

### `CoverageGap`

| Field | Type | Meaning |
| --- | --- | --- |
| `state` | `DocumentState` | `unavailable`, `restricted`, or `failed`, with a count of zero |
| `basis` | `"D4"` | A missing class is a gap, never repaired by reselecting |

### `AppliedOverride`

| Field | Type | Meaning |
| --- | --- | --- |
| `override_id` | ID part | The acquisition override applied to a pilot document |
| `document_id` | ID part | `<event_id>:release` |
| `verdict` | `AttemptOutcome` | The verdict the override's attempt kept |

### `NoThemeCount`

| Field | Type | Meaning |
| --- | --- | --- |
| `partition` | `"train"`, `"dev"`, or `"test"` | The partition counted |
| `bundles` | int ≥ 0 | Its bundles with signed gold |
| `no_theme` | int ≥ 0 | Those whose gold has `no_theme` true |

### `CoverageReport`

`evaluation/<corpus>/pilot-v<N>/coverage-v<M>.json`, written once.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Ingestion record schema version |
| `coverage_version` | int ≥ 1 | The report's version |
| `pin` | `PilotPin` | The pilot it covers |
| `run_ids` | tuple of ID part | The runs it read; a rebuild reads only these |
| `documents` | int ≥ 0 | The pilot's documents |
| `states` | tuple of `StateCount` | Every `DocumentState`, in order, summing to `documents` |
| `gaps` | tuple of `CoverageGap` | Each failure class with no document |
| `overrides` | tuple of `AppliedOverride` | Each override applied to a pilot document |
| `no_theme` | tuple of `NoThemeCount` | Empty until Stage 11 adds train and dev, and Stage 14 test (R12.4, GS18) |
| `content_hash` | 64 lowercase hex | SHA-256 of the canonical JSON of every other field |

## earnings-themes records, schema version 1

`earnings_themes` holds Stage 6's split, codebook, and gold contracts (the Stage 6
spec, specs/completed/pilot-codebook-split-and-gold-set-protocol.md). Every model is strict,
frozen, and refuses unknown fields. A committed record holds IDs, hashes, pointers,
and the user's words, never a release's wording: a quote is a pointer, and the
wording guard refuses any 40-character window, dates masked, shared with a pilot
document or a Stage 1 fixture.

### `Problem`

Stage 6's own refusal reasons; a span check's reason is earnings-core's
`RejectionReason`. A refusal names its item by ID or field path, never by text.

| Value | Meaning |
| --- | --- |
| `malformed` | A draft item is inconsistent, such as a synthetic example with an event |
| `not_narrative` | A quote overlaps a table, cell, page artifact, or other non-narrative element (GS15), other than a transparent container: an `other` element with at least one child, whose children hold every non-space character of its span (ES9) |
| `element_mismatch` | A pointer names a narrative element that holds its span but is not the most specific one (P9-19) |
| `quote_hash_mismatch` | A pointer's slice does not hash to its `quote_sha256` |
| `context_hash_mismatch` | Its context does not hash to its `context_sha256` |
| `masks_mismatch` | Its `mask_ids` are not the masks over it |
| `wrong_pin` | The record names another pin |
| `wrong_split` | It names another split |
| `wrong_partition` | Its partition is not its event's |
| `excluded_event` | Its event is excluded |
| `wrong_codebook` | It names another codebook version |
| `codebook_not_approved` | Its codebook is not approved |
| `unsigned` | Its `annotator` is blank |
| `no_theme_mismatch` | Its `no_theme` disagrees with its assignments |
| `counts_mismatch` | Its origin counts disagree with its items |
| `duplicate_id` | An ID repeats, or a theme takes the reserved `unmatched` |
| `unknown_quote` | A claim names a quote the record lacks |
| `unknown_claim` | An assignment names a claim the record lacks |
| `unknown_theme` | An assignment, hard negative, or parent names a theme the codebook lacks |
| `unknown_document` | The event or fixture has no document here, or is not in the split |
| `unreferenced` | The record holds an item nothing in it names: a claim with no assignment row, or a quote no claim or hard negative cites (R9.9) |
| `tie_group` | A tie group holds rows of more than one claim, or only one row |
| `source_wording` | A string shares a 40-character window with a document's text |
| `outside_training` | A codebook example is not from a training bundle |
| `synthetic_unflagged` | An example names no event and is not marked synthetic |
| `parent_cycle` | Themes' parents form a cycle |
| `discovery_corpus` | The codebook's discovery corpus is not the split's parsed training bundles |
| `content_hash_mismatch` | A record's `content_hash` is not its content's |
| `negative_kinds` | The curated hard negatives lack a kind |
| `adr_not_cited` | ADR 0003 does not cite the codebook's content hash |

### `Pin`

`PilotPin`, as earnings-themes reads it: the same fields and values.

| Field | Type | Meaning |
| --- | --- | --- |
| `pilot_id` | ID part | The pilot's ID |
| `pilot_version` | int ≥ 1 | Its version |
| `pilot_hash` | 64 lowercase hex | Its `content_hash` |
| `events_version` | int ≥ 1 | The event manifest it selected from |
| `events_hash` | 64 lowercase hex | That manifest's `content_hash` |
| `universe_version` | int ≥ 1 | The universe the pilot was selected over |
| `universe_operative_hash` | 64 lowercase hex | That universe's `operative_hash` |

### `Partition`

| Value | Meaning |
| --- | --- |
| `train` | Codebook discovery and training gold: calendar quarters 2024Q3 to 2025Q2 |
| `dev` | Tuning: 2025Q3 to 2025Q4 |
| `test` | Held out until Stage 14 freezes: 2026Q1 to 2026Q2 |
| `excluded` | In no partition, for its `ExclusionReason` |

### `ExclusionReason`

| Value | Meaning |
| --- | --- |
| `issuer_in_earlier_partition` | Its issuer's home partition, that of its earliest pilot event, is an earlier one |
| `fixture_train_or_exclude` | Its release is a Stage 1 fixture outside train (GS10) |

### `SplitWindow`

| Field | Type | Meaning |
| --- | --- | --- |
| `partition` | `Partition` | `train`, `dev`, or `test` |
| `first` | `YYYYQn` | Its first calendar quarter |
| `last` | `YYYYQn` | Its last, inclusive |

### `SplitEvent`

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | A pilot event |
| `issuer_id` | ID part | Its issuer |
| `period_end` | date | Its fiscal period's end, which places it in a quarter |

### `SplitRow`

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | A pilot event |
| `issuer_id` | ID part | Its issuer |
| `period_end` | date | Its fiscal period's end |
| `partition` | `Partition` | Where `issuer-time/1` puts it |
| `reason` | `ExclusionReason` or null | Exactly for `excluded` |

### `SplitManifest`

`evaluation/<corpus>/pilot-v<N>/split-v<M>.json`, written once.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Themes record schema version |
| `split_policy` | `"issuer-time/1"` | The rule: each issuer's events go to its home partition, or are excluded |
| `split_version` | int ≥ 1 | The split's version |
| `windows` | tuple of `SplitWindow` | The policy's fixed windows |
| `pin` | `Pin` | The pilot it splits |
| `rows` | tuple of `SplitRow` | One per pilot event, sorted by `event_id` |
| `content_hash` | 64 lowercase hex | SHA-256 of the canonical JSON of every other field |

### `SpanPointer`

A quote, by position: the committed form of evidence.

| Field | Type | Meaning |
| --- | --- | --- |
| `start` | int ≥ 0 | Half-open start in the canonical text |
| `end` | int > `start` | Half-open end |
| `element_id` | string | The most specific narrative element that contains it |
| `quote_sha256` | 64 lowercase hex | SHA-256 of the slice's UTF-8 bytes |
| `context_sha256` | 64 lowercase hex or null | When the text repeats: SHA-256 of `make_locator`'s prefix and suffix as a compact JSON pair in UTF-8, `json.dumps([prefix, suffix], ensure_ascii=False, separators=(",", ":"))` |
| `mask_ids` | tuple of string | The boilerplate masks over it, each `<category>-<start>-<end>` |

### `CodebookStatus`

| Value | Meaning |
| --- | --- |
| `draft` | Frozen by the build but not approved; never written |
| `approved` | Approved, with its `Approval`; the only status committed |

### `ExamplePointer`

A `SpanPointer` into a training bundle, with its document.

| Field | Type | Meaning |
| --- | --- | --- |
| `start` | int ≥ 0 | As `SpanPointer` |
| `end` | int > `start` | As `SpanPointer` |
| `element_id` | string | As `SpanPointer` |
| `quote_sha256` | 64 lowercase hex | As `SpanPointer` |
| `context_sha256` | 64 lowercase hex or null | As `SpanPointer` |
| `mask_ids` | tuple of string | As `SpanPointer` |
| `event_id` | ID part | The training event |
| `doc_id` | string | Its canonical document |

### `Example`

Exactly one kind: a pointer, or synthetic with its text.

| Field | Type | Meaning |
| --- | --- | --- |
| `synthetic` | bool | True for an example in the user's words |
| `text` | string or null | The synthetic example's text |
| `pointer` | `ExamplePointer` or null | The quoted example |

### `Theme`

One theme (R9.2). Every list has at least one item.

| Field | Type | Meaning |
| --- | --- | --- |
| `theme_id` | `^[a-z][a-z0-9_.-]*$` | Its ID; `unmatched` is reserved |
| `parent_id` | theme ID or null | Its parent theme |
| `label` | string | Its short name |
| `definition` | string | Its definition |
| `inclusion_rules` | tuple of string | What it covers |
| `exclusion_rules` | tuple of string | What it does not |
| `positive_examples` | tuple of `Example` | Examples it covers |
| `hard_negatives` | tuple of `Example` | Confusable examples it does not |
| `sector_applicability` | `"all"` or tuple of sector tag | Where it applies |

### `DiscoveryCorpus`

| Field | Type | Meaning |
| --- | --- | --- |
| `pin` | `Pin` | The pilot |
| `split_hash` | 64 lowercase hex | The split's `content_hash` |
| `event_ids` | tuple of ID part | The training events with a parsed document |
| `doc_ids` | tuple of string | Their canonical documents, in the same order |

### `CodebookRules`

| Field | Type | Meaning |
| --- | --- | --- |
| `multi_label` | string | How a claim takes more than one theme |
| `boilerplate` | string | How masked text is treated (R3.4) |

### `Approval`

| Field | Type | Meaning |
| --- | --- | --- |
| `approver` | string | Who approved the codebook |
| `approved_on` | date | When |
| `adr` | path | ADR 0003, which cites the content hash |

### `DraftingAid`

| Field | Type | Meaning |
| --- | --- | --- |
| `model_id` | string | The Claude model that drafted, in an interactive session outside the required path (GS4) |
| `drafted_on` | date | When |

### `Codebook`

`codebooks/djia-pilot/codebook-v<N>.toml`, written once, approved.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Themes record schema version |
| `codebook_id` | ID part | `djia-pilot` |
| `codebook_version` | int ≥ 0 | `0` for Stage 6 |
| `status` | `CodebookStatus` | `approved` exactly when `approval` is set |
| `content_hash` | 64 lowercase hex | SHA-256 of the canonical JSON of every field but `status`, `approval`, and itself, so an ADR can cite it before approval |
| `discovery_corpus` | `DiscoveryCorpus` | What it was discovered from |
| `rules` | `CodebookRules` | Its rules |
| `approval` | `Approval` or null | The approval |
| `drafting_aid` | `DraftingAid` | The drafting session |
| `themes` | tuple of `Theme` | Its themes |

### `ExampleDraft`

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part or null | The training event quoted; null for a synthetic example |
| `text` | string | The exact text, or the synthetic example |
| `prefix` | string | Text just before it, when it repeats |
| `suffix` | string | Text just after it, when it repeats |
| `synthetic` | bool | True for an example in the user's words |

### `ThemeDraft`

| Field | Type | Meaning |
| --- | --- | --- |
| `theme_id` | theme ID | As `Theme` |
| `parent_id` | theme ID or null | As `Theme` |
| `label` | string | As `Theme` |
| `definition` | string | As `Theme` |
| `inclusion_rules` | tuple of string | As `Theme` |
| `exclusion_rules` | tuple of string | As `Theme` |
| `sector_applicability` | `"all"` or tuple of sector tag | As `Theme` |
| `positive_examples` | tuple of `ExampleDraft` | Anchored into `ExamplePointer`s |
| `hard_negatives` | tuple of `ExampleDraft` | Anchored likewise |

### `CodebookDraft`

`data/runs/gold/drafts/codebook.draft.toml` and its working copy; never committed.

| Field | Type | Meaning |
| --- | --- | --- |
| `codebook_id` | ID part | As `Codebook` |
| `codebook_version` | int ≥ 0 | As `Codebook` |
| `drafting_aid` | `DraftingAid` | The drafting session |
| `rules` | `CodebookRules` | As `Codebook` |
| `themes` | tuple of `ThemeDraft` | At least one |

### `Origin`

| Value | Meaning |
| --- | --- |
| `drafted_accepted` | In the draft, and unchanged in the working copy |
| `drafted_edited` | In the draft, and changed in the working copy |
| `annotator_added` | Only in the working copy |

### `Support`

| Value | Meaning |
| --- | --- |
| `supports` | The claim's quotes support it under the theme |
| `does_not_support` | They do not |
| `uncertain` | The annotator cannot tell |

### `ReleaseLabel`

| Value | Meaning |
| --- | --- |
| `release` | The document is the event's earnings release (R13.1) |
| `not_release` | It is not; `true_accession` and `true_exhibit` may name the release |
| `ambiguous` | The annotator cannot tell |

### `NegativeKind`

| Value | Meaning |
| --- | --- |
| `period` | Confusable by its period: another quarter's result |
| `issuer` | Confusable by its issuer: another company's result |
| `section` | Confusable by its section: boilerplate or a forward-looking statement that reports no result |

### `GoldQuote`

| Field | Type | Meaning |
| --- | --- | --- |
| `start` | int ≥ 0 | As `SpanPointer` |
| `end` | int > `start` | As `SpanPointer` |
| `element_id` | string | As `SpanPointer` |
| `quote_sha256` | 64 lowercase hex | As `SpanPointer` |
| `context_sha256` | 64 lowercase hex or null | As `SpanPointer` |
| `mask_ids` | tuple of string | As `SpanPointer` |
| `quote_id` | ID part | Its ID in the record |
| `origin` | `Origin` | Where it came from |

### `GoldClaim`

| Field | Type | Meaning |
| --- | --- | --- |
| `claim_id` | ID part | Its ID in the record |
| `quote_ids` | tuple of ID part | The quotes it rests on; at least one |
| `claim` | string | The claim, in the user's words |
| `origin` | `Origin` | Where it came from |

### `GoldAssignment`

One row per claim and theme (R9.9).

| Field | Type | Meaning |
| --- | --- | --- |
| `claim_id` | ID part | The claim |
| `theme_id` | theme ID | A codebook theme, or `unmatched` |
| `support` | `Support` | Whether the claim's quotes support it under the theme |
| `tie_group` | ID part or null | Marks rows that are alternatives for one claim (R12.6) |
| `origin` | `Origin` | Where it came from |

### `HardNegative`

A hard-negative claim (D4); its expected support is `does_not_support`.

| Field | Type | Meaning |
| --- | --- | --- |
| `claim_id` | ID part | Its ID in the record |
| `quote_ids` | tuple of ID part | Its quotes; at least one |
| `claim` | string | The claim, in the user's words |
| `negative_kind` | `NegativeKind` | What makes it confusable |
| `theme_id` | theme ID or null | The theme it would wrongly support |
| `origin` | `Origin` | Where it came from |

### `ReleaseIdentification`

| Field | Type | Meaning |
| --- | --- | --- |
| `label` | `ReleaseLabel` | R13.1's label |
| `note` | string | The annotator's reason, in their words |
| `true_accession` | accession or null | Only with `not_release`: the release's filing |
| `true_exhibit` | string or null | Only with `not_release`: its exhibit |

### `DraftCounts`

| Field | Type | Meaning |
| --- | --- | --- |
| `accepted` | int ≥ 0 | Drafted items kept unchanged |
| `edited` | int ≥ 0 | Drafted items changed |
| `rejected` | int ≥ 0 | Drafted items removed |
| `added` | int ≥ 0 | Items the annotator added |

### `CodebookRef`

| Field | Type | Meaning |
| --- | --- | --- |
| `codebook_id` | ID part | The codebook coded against |
| `codebook_version` | int ≥ 0 | Its version |
| `content_hash` | 64 lowercase hex | Its `content_hash` |

### `Gold`

`evaluation/<corpus>/pilot-v<N>/gold/<event>.toml`, written once, signed.
`<event>` is the event ID with its colon as an underscore, such as
`cik-0000051143_2024-12-31`, since Git on Windows cannot check out a path with a colon.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Themes record schema version |
| `event_id` | ID part | The bundle's event |
| `document_id` | ID part | `<event_id>:release` |
| `doc_id` | string | Its canonical document |
| `canonical_hash` | 64 lowercase hex | That document's `canonical_hash` |
| `pin` | `Pin` | The pilot |
| `split_hash` | 64 lowercase hex | The split's `content_hash` |
| `partition` | `Partition` | The event's partition; never `excluded` |
| `codebook` | `CodebookRef` | The approved codebook coded against |
| `annotator` | string | The signature; blank until the user signs (GS4) |
| `drafting_aid` | `DraftingAid` | The drafting session, from the kept draft (GS5) |
| `counts` | `DraftCounts` | The origins, counted against the kept draft (GS5) |
| `no_theme` | bool | True exactly when no row pairs a claim with a codebook theme under `supports` |
| `release_identification` | `ReleaseIdentification` | Whether the document is the release |
| `quotes` | tuple of `GoldQuote` | Its quotes |
| `claims` | tuple of `GoldClaim` | Its claims |
| `assignments` | tuple of `GoldAssignment` | Its assignments |
| `hard_negatives` | tuple of `HardNegative` | Its hard-negative claims |

### `FixtureNegatives`

| Field | Type | Meaning |
| --- | --- | --- |
| `fixture_id` | ID part | A Stage 1 fixture |
| `doc_id` | string | Its canonical document |
| `canonical_hash` | 64 lowercase hex | That document's `canonical_hash` |
| `quotes` | tuple of `GoldQuote` | The quotes; at least one |
| `hard_negatives` | tuple of `HardNegative` | The hard-negative claims; at least one |

### `HardNegativeSet`

`tests/fixtures/gold/hard-negatives.toml`, written once, signed: outside the pilot,
in no partition (GS10), though it carries the pin, as every Stage 6 record does.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Themes record schema version |
| `pin` | `Pin` | The pilot |
| `annotator` | string | The signature |
| `drafting_aid` | `DraftingAid` | The drafting session, from the kept draft (GS5) |
| `counts` | `DraftCounts` | The origins, over every fixture |
| `codebook` | `CodebookRef` | The approved codebook |
| `documents` | tuple of `FixtureNegatives` | At least one; with every `NegativeKind` among them |

### `QuoteDraft`

| Field | Type | Meaning |
| --- | --- | --- |
| `quote_id` | ID part | Its ID |
| `text` | string | The exact text |
| `prefix` | string | Text just before it, when it repeats |
| `suffix` | string | Text just after it, when it repeats |

### `ClaimDraft`

| Field | Type | Meaning |
| --- | --- | --- |
| `claim_id` | ID part | As `GoldClaim` |
| `quote_ids` | tuple of ID part | As `GoldClaim` |
| `claim` | string | As `GoldClaim` |

### `AssignmentDraft`

| Field | Type | Meaning |
| --- | --- | --- |
| `claim_id` | ID part | As `GoldAssignment` |
| `theme_id` | theme ID | As `GoldAssignment` |
| `support` | `Support` | As `GoldAssignment` |
| `tie_group` | ID part or null | As `GoldAssignment` |

### `HardNegativeDraft`

| Field | Type | Meaning |
| --- | --- | --- |
| `claim_id` | ID part | As `HardNegative` |
| `quote_ids` | tuple of ID part | As `HardNegative` |
| `claim` | string | As `HardNegative` |
| `negative_kind` | `NegativeKind` | As `HardNegative` |
| `theme_id` | theme ID or null | As `HardNegative` |

### `GoldDraft`

`data/runs/gold/drafts/<event>.draft.toml` and its working copy; never committed.

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | ID part | The bundle's event |
| `annotator` | string | Blank in the draft; the user signs the working copy |
| `drafting_aid` | `DraftingAid` | The drafting session; the record takes the kept draft's, never the working copy's (GS5) |
| `no_theme` | bool | As `Gold` |
| `release_identification` | `ReleaseIdentification` | As `Gold` |
| `quotes` | tuple of `QuoteDraft` | Quotes, by text |
| `claims` | tuple of `ClaimDraft` | Claims |
| `assignments` | tuple of `AssignmentDraft` | Assignments |
| `hard_negatives` | tuple of `HardNegativeDraft` | Hard-negative claims |

### `FixtureDraft`

| Field | Type | Meaning |
| --- | --- | --- |
| `fixture_id` | ID part | A Stage 1 fixture |
| `quotes` | tuple of `QuoteDraft` | At least one |
| `hard_negatives` | tuple of `HardNegativeDraft` | At least one |

### `CuratedDraft`

`data/runs/gold/drafts/hard-negatives.draft.toml` and its working copy.

| Field | Type | Meaning |
| --- | --- | --- |
| `annotator` | string | Blank in the draft; the user signs the working copy |
| `drafting_aid` | `DraftingAid` | The drafting session; the record takes the kept draft's, never the working copy's (GS5) |
| `documents` | tuple of `FixtureDraft` | At least one |

## Stage 6 files

- **Committed, written once.** `evaluation/<corpus>/pilot-v<N>/split-v<M>.json`,
  `coverage-v<M>.json`, and `gold/<event>.toml`; `codebooks/djia-pilot/
  codebook-v<N>.toml`; and `tests/fixtures/gold/hard-negatives.toml`. A changed
  record is a new version, never an edit.
- **Local, never committed.** Under `data/runs/gold/`: `drafts/`, each draft kept
  unchanged beside the user's working copy; `anchored/`, the latest build of each;
  `views/`, the text with each quote marked, which the user verifies against; and
  `texts/`, the text alone, which a drafting session reads. No command prints a
  document's text (GS13).
- **File names.** A file named for an event takes the event ID with its colon as an
  underscore, `<event>`; the ID inside the file is unchanged.

## earnings-themes extraction records, schema version 1

`earnings_themes.extraction` holds Stage 7's extractor (the Stage 7 spec,
specs/completed/evidence-selection-and-verification.md). Every model is strict, frozen, and
refuses unknown fields. Each stored record carries `schema_version`
(`earnings_themes.extraction.records.EXTRACTION_SCHEMA_VERSION`), apart from the
themes records' version, so an extraction change never re-versions the gold or the
codebook (ES22). A run is written only to a directory its caller supplies, never to
a committed file. A rejection's `detail` and the reply's labels may quote a
document, so they stay local, and a refusal prints as its reason and IDs alone
(GS13).

`write_run` (`earnings_themes.extraction.store`) stores a run in a new directory:
`run.json`, the `RunRecord`, and one Parquet file per record kind, written through
Polars under an explicit schema: `documents.parquet` (`DocumentRecord`),
`windows.parquet` (`WindowRecord`), `visits.parquet` (`Visit`), `quotes.parquet`
(`Quote`), `claims.parquet` (`Claim`), and `rejections.parquet`
(`ExtractionRejection`). Each column is a field, in the model's order: an enum is
its value, a tuple a list, and a nested `VerifiedSpan` or `Rejection` a struct of
its fields.

### `ExtractionProblem`

The extractor's own refusal reasons; a span check's reason is earnings-core's
`RejectionReason`.

| Value | Meaning |
| --- | --- |
| `malformed_reply` | The reply is not JSON, or breaks the reply's schema |
| `tool_call_refused` | The reply carries a tool call, though no tool exists (R14.7) |
| `model_mismatch` | The reply names a model other than the configured one, or none |
| `transport_error` | The reply never arrived |
| `replay_miss` | Replay found no stored reply, and called nothing |
| `budget_exhausted` | A ceiling stopped the dispatch (ES21) |
| `unknown_label` | A label names no unit of the window |
| `duplicate_label` | A candidate repeats a label |
| `blank_claim` | A claim holds no non-space character |
| `claim_too_long` | A claim is longer than the policy's claim limit |

### `WindowOutcome`

| Value | Meaning |
| --- | --- |
| `completed` | At least one attempt brought a usable reply |
| `failed` | No attempt did |

### `DocumentOutcome`

R1.4's words for a document's extraction.

| Value | Meaning |
| --- | --- |
| `completed` | Every window completed, or the document has none |
| `partial` | Some windows failed |
| `failed` | Every window failed, or `bundle_problems` refused the document |

### `Parameters`

A request's parameters. The defaults are provisional.

| Field | Type | Meaning |
| --- | --- | --- |
| `temperature` | float | Sampling temperature; default 0 |
| `seed` | int | The sampling seed; default 0 |
| `max_tokens` | int ≥ 1 | The reply's token limit; default 2048 |
| `structured` | bool | Whether to ask for a JSON-schema response format (ES19); default true |

### `AdapterIdentity`

Who answers a request, as the cache key and the run record name it (R14.6).

| Field | Type | Meaning |
| --- | --- | --- |
| `adapter_kind` | string | `scripted` for the fake, `local` for the local adapter |
| `model_id` | string | The model, as its server names it |
| `weights_sha256` | 64 lowercase hex or null | The weights file's SHA-256; null for a fake |
| `runtime` | string or null | The serving runtime's name |
| `runtime_version` | string or null | Its version |

### `ExtractionPolicy`

How a run extracts. Each value is provisional, not a quality threshold.

| Field | Type | Meaning |
| --- | --- | --- |
| `parameters` | `Parameters` | Every request's parameters |
| `window_budget` | int ≥ 1 or null | Characters of unit text per window, default 4000; null packs one window per document (ES13) |
| `claim_limit` | int ≥ 1 | The longest claim, in characters; default 500 |

### `Ceilings`

A run's ceilings, each passed explicitly, none with a default (ES21; A §691).

| Field | Type | Meaning |
| --- | --- | --- |
| `requests_per_document` | int ≥ 1 | Requests one document may send |
| `requests_per_run` | int ≥ 1 | Requests the run may send |
| `tokens_per_run` | int ≥ 1 | Reported tokens the run may spend |

### `RunConfiguration`

What every request of a run shares: the key components common to the run (R14.6).

| Field | Type | Meaning |
| --- | --- | --- |
| `identity` | `AdapterIdentity` | Who answers |
| `policy` | `ExtractionPolicy` | How the run extracts |
| `ceilings` | `Ceilings` | What it may spend |
| `prompt_sha256` | 64 lowercase hex | SHA-256 of the prompt template's UTF-8 bytes |
| `reply_schema_sha256` | 64 lowercase hex | SHA-256 of the reply schema's canonical JSON |
| `extractor_version` | string | `pointer-traversal/1`: the unit rule, the planner, the labels, the reply contract, and the retry policy |
| `validator_version` | string | earnings-core's `VALIDATOR_VERSION` |
| `codebook_hash` | 64 lowercase hex or null | Null under codebook-free extraction (ES11) |

### `Quote`

One cited unit, verified exactly (R6.1): `quotes.parquet`.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Extraction record schema version |
| `quote_id` | string | `q-<start>-<end>`, unique together with the span's `doc_id`; the same unit keeps it in every run on the same document version (R9.9) |
| `span` | `VerifiedSpan` | The unit's span and text, as `validate_span` returned it |
| `mask_ids` | tuple of string | The boilerplate masks over it, each `<category>-<start>-<end>` |

### `Claim`

A candidate that verified: `claims.parquet`. It carries no theme (ES11).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Extraction record schema version |
| `claim_id` | string | `c-<window start>-<window end>-<attempt>-<index>`, from its window, attempt, and index in the reply; unique together with `doc_id` |
| `doc_id` | string | Its document |
| `window_id` | string | Its window |
| `attempt` | int ≥ 1 | The attempt whose reply held it |
| `claim` | string | The model's words |
| `quote_ids` | tuple of string, at least one | The quotes it rests on, in its labels' order |

### `ExtractionRejection`

A refusal and its subject: `rejections.parquet`. It holds exactly one of
`rejection` and `problem` (ES6).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Extraction record schema version |
| `doc_id` | string | Its document |
| `window_id` | string or null | Its window; null for a document `bundle_problems` refused |
| `attempt` | int ≥ 1 or null | Its attempt |
| `candidate_index` | int ≥ 0 or null | Its candidate's index in the reply; null for a reply or a dispatch |
| `labels` | tuple of string | The candidate's labels, as the reply gave them |
| `element_ids` | tuple of string | The elements its known labels name |
| `rejection` | `Rejection` or null | From verification, or one per reason `bundle_problems` reported |
| `problem` | `ExtractionProblem` or null | The extractor's own reason |
| `detail` | string | A problem's field paths, never a value |

### `Visit`

One unit's visit, R10.1's coverage evidence: `visits.parquet`.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Extraction record schema version |
| `doc_id` | string | Its document |
| `element_id` | string | The unit |
| `window_id` | string | The window it lies in |
| `outcome` | `WindowOutcome` | Its window's outcome |
| `reason` | `ExtractionProblem` or null | Why its window failed; exactly for `failed` |

### `WindowRecord`

One window, its attempts, and what it spent: `windows.parquet`.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Extraction record schema version |
| `doc_id` | string | Its document |
| `window_id` | string | `w-<start>-<end>` |
| `start` | int ≥ 0 | Its first unit's start |
| `end` | int > `start` | Its last unit's end |
| `unit_ids` | tuple of string | Its units in label order: `U1` names the first |
| `context_id` | string or null | The heading shown before it, unlabeled and not quotable |
| `attempts` | int ≥ 0 | Dispatched attempts: requests, cache hits, and replay misses |
| `outcome` | `WindowOutcome` | Whether an attempt brought a usable reply |
| `reason` | `ExtractionProblem` or null | Its last attempt's problem; exactly for `failed` |
| `requests` | int ≥ 0 | Requests sent; a cache hit or a replay miss is none |
| `cache_hits` | int ≥ 0 | Replies the cache returned |
| `prompt_tokens` | int ≥ 0 | Prompt tokens its requests' replies reported |
| `completion_tokens` | int ≥ 0 | Completion tokens they reported |
| `unreported` | int ≥ 0 | Requests whose reply reported no usage |
| `latency_ms` | int ≥ 0 | Its requests' latency, summed |
| `exhausted` | bool | Whether a ceiling stopped one of its dispatches |

### `DocumentRecord`

One document's outcome and counts: `documents.parquet`.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Extraction record schema version |
| `doc_id` | string | The document |
| `canonical_hash` | 64 lowercase hex | Its canonical hash |
| `outcome` | `DocumentOutcome` | R1.4's word for it |
| `units` | int ≥ 0 | Its units |
| `windows` | int ≥ 0 | Its windows |
| `windows_failed` | int ≥ 0 | Its failed windows |
| `candidates` | int ≥ 0 | Candidates its replies held |
| `quotes` | int ≥ 0 | Quotes retained |
| `claims` | int ≥ 0 | Claims retained |
| `rejections` | int ≥ 0 | Its rejections |

### `RunRecord`

One run: `run.json`.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Extraction record schema version |
| `run_id` | ID part | The caller's ID for the run |
| `started_at` | aware datetime | When the caller started it |
| `configuration` | `RunConfiguration` | What every request shared |
| `configuration_hash` | 64 lowercase hex | SHA-256 of the configuration's canonical JSON |
| `documents` | map of `doc_id` to 64 lowercase hex | Each document and its canonical hash |
| `units` | int ≥ 0 | Units over every document |
| `windows` | int ≥ 0 | Windows |
| `candidates` | int ≥ 0 | Candidates the replies held |
| `quotes` | int ≥ 0 | Quotes retained |
| `claims` | int ≥ 0 | Claims retained |
| `rejections_by_reason` | map of reason to int ≥ 1 | Rejections, by `RejectionReason` or `ExtractionProblem` value |
| `requests` | int ≥ 0 | Requests sent |
| `cache_hits` | int ≥ 0 | Replies the cache returned |
| `prompt_tokens` | int ≥ 0 | Prompt tokens reported |
| `completion_tokens` | int ≥ 0 | Completion tokens reported |
| `unreported` | int ≥ 0 | Requests whose reply reported no usage, which only the request ceilings bind |
| `exhausted` | bool | Whether any ceiling stopped a dispatch |
| `software` | map of string to string | The software identity the caller passes |
| `billable_cost` | `"none, self-hosted"` | No billable inference (R14.1) |
| `exactness_rate` | float or null | 1.0 over the retained quotes, each verified; null when no quote is retained (R6.2, R12.8) |

### `Usage`

The token usage a server reports.

| Field | Type | Meaning |
| --- | --- | --- |
| `prompt_tokens` | int ≥ 0 | Prompt tokens |
| `completion_tokens` | int ≥ 0 | Completion tokens |

### `ModelReply`

An adapter's reply, stored raw in the cache.

| Field | Type | Meaning |
| --- | --- | --- |
| `text` | string | The reply's text, which the extractor parses and verifies again on every use |
| `usage` | `Usage` or null | Null when the server reports none |
| `model` | string or null | The model the server names |
| `tool_calls` | bool | Whether it carries tool calls; such a reply is refused and never stored |
| `latency_ms` | int ≥ 0 | The request's latency |
| `cached` | bool | Whether the cache returned it; false in the stored entry |

### `CacheKey`

One field per R14.6 component; the cache file is named by its SHA-256.

| Field | Type | Meaning |
| --- | --- | --- |
| `doc_id` | string | The window's document |
| `canonical_hash` | 64 lowercase hex | Its canonical hash |
| `window_id` | string | The window |
| `unit_ids` | tuple of string | Its units' element IDs, in label order |
| `adapter_kind` | string | From `AdapterIdentity` |
| `model_id` | string | From `AdapterIdentity` |
| `weights_sha256` | 64 lowercase hex or null | From `AdapterIdentity` |
| `runtime` | string or null | From `AdapterIdentity` |
| `runtime_version` | string or null | From `AdapterIdentity` |
| `structured` | bool | From `Parameters` |
| `temperature` | float | From `Parameters` |
| `seed` | int | From `Parameters` |
| `max_tokens` | int ≥ 1 | From `Parameters` |
| `window_budget` | int ≥ 1 or null | From `ExtractionPolicy` |
| `claim_limit` | int ≥ 1 | From `ExtractionPolicy` |
| `prompt_sha256` | 64 lowercase hex | SHA-256 of the template's UTF-8 bytes |
| `reply_schema_sha256` | 64 lowercase hex | SHA-256 of the reply schema's canonical JSON |
| `request_sha256` | 64 lowercase hex | SHA-256 of the request's messages, the exact text the model is sent: the window's text, any feedback, and so the attempt |
| `extractor_version` | string | `pointer-traversal/1` |
| `validator_version` | string | earnings-core's `VALIDATOR_VERSION` |
| `codebook_hash` | 64 lowercase hex or null | Null under codebook-free extraction (ES11) |

### `CacheEntry`

One cache file, `<SHA-256 of the key>.json`, written atomically in `live` mode under
a directory the caller supplies.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Extraction record schema version |
| `key` | `CacheKey` | Its key, which a hit must equal |
| `reply` | `ModelReply` | The raw reply |

### `LocalModelConfig`

The local adapter's endpoint and identity (`earnings_themes.extraction.local`), read
from `config/models/local-model.toml`, which ADR 0004 records at plan B's gate.

| Field | Type | Meaning |
| --- | --- | --- |
| `base_url` | string | The server's OpenAI-compatible root; the adapter refuses any scheme but http or https and any host but 127.0.0.1, ::1, or localhost (R14.1), and a URL with credentials, a port that is not a number from 0 to 65535, surrounding whitespace or an ASCII control character, or one that does not parse; no refusal names any part of the URL |
| `model_id` | string | The model the server names in each reply |
| `weights_sha256` | 64 lowercase hex | The weights file's SHA-256 |
| `runtime` | string | The serving runtime's name |
| `runtime_version` | string | Its version |
| `structured` | bool | Whether the runtime honors a strict JSON-schema `response_format`; a run sets `Parameters.structured` from it (ES19); default true |
| `timeout_s` | float > 0 | Seconds per request; default 300 |

## earnings-themes support records, schema version 1

The Stage 8 contracts (`earnings_themes.support.records`) implement SS1–SS22.
Support policy version is `"semantic-support/1"` (`earnings_themes.support.records.SUPPORT_VERSION`).
Core, Stage 6, extraction and verifier versions are unchanged. Persisted records
carry schema_version 1; request/reply parts and identities are nonpersisted parts.
All models are frozen, closed, strict Pydantic contracts. Counts and offsets never
accept bools, floats or numeric strings. Tuple fields and tuple bindings are immutable;
JSON-mode parsing revalidates model data instead of trusting prior construction.

`parse_support(data, model)` converts validation failures to the fixed
`SupportError("malformed_record")`, suppressing source-bearing exception chaining.
Unknown refusal values become `unexpected_error`; core rejection reason values
are allowed but core Rejection.detail is never copied. Printable records expose
only class name and content SHA-256. Source-bearing fields also set repr=False.
Explicit local JSON/disk serialization intentionally retains source-bearing data;
logging must never serialize those records. Raw requests, replies and rationales
remain local and uncommitted. No record or import opens a file or concrete adapter.

### `CodebookReference`

One explicit frozen codebook identity. Version is a strict nonnegative integer.

| Field | Type | Meaning |
| --- | --- | --- |
| `codebook_id` | nonblank string | Expected frozen codebook ID |
| `codebook_version` | strict int ≥ 0 | Expected nonnegative codebook version |
| `content_hash` | SHA-256 | Codebook content SHA-256 |

### `Target`

One caller-selected source-run/document/claim/theme pairing. Callers supply no alternative evidence or replacement text.

| Field | Type | Meaning |
| --- | --- | --- |
| `source_run_id` | nonblank string | Source extraction run ID |
| `doc_id` | nonblank string | Immutable canonical document ID |
| `claim_id` | nonblank string | Document-scoped source claim ID |
| `theme_id` | nonblank string | Explicit selected theme ID |
| `codebook` | CodebookReference | Frozen CodebookReference |

### `ThemeSnapshot`

One copied selected theme definition and its rules. Examples are excluded and parent rules are not inherited.

| Field | Type | Meaning |
| --- | --- | --- |
| `codebook` | CodebookReference | Frozen CodebookReference |
| `theme_id` | nonblank string | Explicit selected theme ID |
| `label` | nonblank string | Source-supported theme label, local |
| `definition` | nonblank string | Unchanged selected theme definition, local |
| `parent_id` | string or null | Selected theme parent ID or null |
| `inclusion_rules` | tuple[nonblank string, …] | Unchanged local inclusion rules |
| `exclusion_rules` | tuple[nonblank string, …] | Unchanged local exclusion rules |

### `EvidenceReference`

One exact quote reference for a target. Character offsets are strict integers in a nonempty half-open span; quote text is not duplicated.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Support record schema version, fixed at 1 |
| `target_id` | nonblank string | Derived assessment target identity |
| `quote_id` | nonblank string | Source quote ID |
| `doc_id` | nonblank string | Immutable canonical document ID |
| `canonical_hash` | SHA-256 | Immutable canonical-text SHA-256 |
| `element_id` | nonblank string | Canonical element ID |
| `start` | strict int ≥ 0 | First Python character offset, nonnegative |
| `end` | strict int ≥ 0 | Exclusive character offset, greater than start |
| `text_hash` | SHA-256 | SHA-256 of the canonical slice |
| `validator_version` | nonblank string | Exact-span validator version |
| `mask_ids` | tuple[nonblank string, …] | Distinct current overlay mask IDs |

### `ContextReference`

One attribution context span for a target. It is explicitly a block or heading and carries no evidence status.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Support record schema version, fixed at 1 |
| `target_id` | nonblank string | Derived assessment target identity |
| `doc_id` | nonblank string | Immutable canonical document ID |
| `canonical_hash` | SHA-256 | Immutable canonical-text SHA-256 |
| `element_id` | nonblank string | Canonical element ID |
| `start` | strict int ≥ 0 | First Python character offset, nonnegative |
| `end` | strict int ≥ 0 | Exclusive character offset, greater than start |
| `text_hash` | SHA-256 | SHA-256 of the canonical slice |
| `kind` | block, heading | Declared context, scorer, or operation kind |

### `TargetRecord`

One resolved target identity with source/claim/input hashes and original versus resolved evidence IDs. Refused targets retain provenance but no accepted evidence.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Support record schema version, fixed at 1 |
| `target_id` | nonblank string | Derived assessment target identity |
| `target` | Target | Caller Target identity |
| `source_run_hash` | SHA-256 | Canonical source-run provenance hash |
| `claim_hash` | SHA-256 | Hash of the unchanged source claim |
| `input_hash` | SHA-256 | Hash binding the full assessment or evaluation input |
| `original_quote_ids` | tuple[string, …] | Distinct source claim quote IDs in original order |
| `evidence_ids` | tuple[string, …] | Distinct resolved evidence reference IDs |
| `theme` | ThemeSnapshot or null | Resolved ThemeSnapshot, null for refusals where unresolved |

### `FileHash`

One pinned local inference file. Paths are relative POSIX paths with no absolute root, drive, backslash, dot or parent component; adapters enforce actual filesystem confinement.

| Field | Type | Meaning |
| --- | --- | --- |
| `relative_path` | nonblank string | Confined local model-relative inference filename |
| `sha256` | SHA-256 | Inference-file byte SHA-256 |

### `RuntimeIdentity`

One complete model/checkpoint/runtime identity; file paths are unique and inference files carry hashes.

| Field | Type | Meaning |
| --- | --- | --- |
| `model_id` | nonblank string | Explicit model identity |
| `revision` | nonblank string | Pinned checkpoint revision |
| `files` | tuple[FileHash, …] | Immutable tuple of FileHash records |
| `runtime` | nonblank string | Inference runtime name |
| `runtime_version` | nonblank string | Pinned runtime version |
| `device` | nonblank string | Explicit inference device |
| `precision` | nonblank string | Explicit inference numeric precision |
| `encoding_version` | nonblank string | Version of the complete-input rendering/encoding |

### `WeightLicense`

One verified weight-license assertion for the stated research use. Permission must be the literal boolean true.

| Field | Type | Meaning |
| --- | --- | --- |
| `source_url` | nonblank string | Weight-license source URL, local |
| `terms_reference` | nonblank string | Verified terms reference, local |
| `intended_use` | nonblank string | Verified intended research use, local |
| `verified_on` | date | Actual license verification date |
| `permits_use` | True | Literal boolean true |

### `ScorerIdentity`

One explicitly selected scorer and full runtime identity; input limit is positive.

| Field | Type | Meaning |
| --- | --- | --- |
| `kind` | scripted, minicheck, deberta | Declared context, scorer, or operation kind |
| `runtime` | RuntimeIdentity | Inference runtime name |
| `input_limit` | strict int ≥ 1 | Positive complete-input token ceiling |

### `JudgeIdentity`

One configured judge family and runtime; local hosting requires a WeightLicense. Both limits are positive.

| Field | Type | Meaning |
| --- | --- | --- |
| `family` | nonblank string | Explicit family lineage, never inferred from model alias |
| `runtime` | RuntimeIdentity | Inference runtime name |
| `input_limit` | strict int ≥ 1 | Positive complete-input token ceiling |
| `output_limit` | strict int ≥ 1 | Positive completion-token ceiling |
| `hosting` | scripted, local | scripted or local; local requires license evidence |
| `weight_license` | WeightLicense or null | Verified WeightLicense or null for scripted identity |

### `EntailmentSignal`

One per-quote or joint signal. Available means a finite score in [0,1] and no reason; unavailable means no score and a fixed refusal reason. Quote scope requires quote_id; joint scope has none.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Support record schema version, fixed at 1 |
| `signal_id` | nonblank string | Unique signal ID |
| `target_id` | nonblank string | Derived assessment target identity |
| `scope` | quote, joint | quote or joint; evidence remains separate canonical spans |
| `quote_id` | string or null | Source quote ID (null only for joint signals) |
| `evaluation_id` | nonblank string | Raw scorer evaluation identity; aliases may reuse it |
| `identity` | ScorerIdentity | Complete configured scorer or judge identity |
| `input_hash` | SHA-256 | Hash binding the full assessment or evaluation input |
| `status` | SignalStatus | Signal availability or review processing status |
| `score` | finite float in [0,1] or null | Finite raw uncalibrated score in [0,1], otherwise null |
| `reason` | string or null | Fixed support/core refusal reason or null |
| `input_tokens` | strict int ≥ 0 or null | Complete input token count; nullable when unavailable and unknown |
| `latency_ms` | strict int ≥ 0 | Nonnegative operation latency in milliseconds |
| `cached` | bool | Whether served from the raw-signal cache |

### `QuoteAssessment`

One contribution classification for one supplied quote. Reference completeness is checked against the assessment input downstream.

| Field | Type | Meaning |
| --- | --- | --- |
| `quote_id` | nonblank string | Source quote ID |
| `contribution` | supporting, contextual, irrelevant, contradicting, uncertain | supporting, contextual, irrelevant, contradicting, or uncertain |

### `JudgeAnswer`

One closed model answer with separate claim-support/theme-fit axes and finite joint score. Quote IDs and reasons are distinct. Local rationale is nonblank and at most 500 characters.

| Field | Type | Meaning |
| --- | --- | --- |
| `claim_support` | supported, unsupported, uncertain | supported, unsupported, or uncertain |
| `theme_fit` | fits, does_not_fit, uncertain | fits, does_not_fit, or uncertain |
| `joint_support_score` | finite float in [0,1] | Finite uncalibrated joint score in [0,1] |
| `quote_assessments` | tuple[QuoteAssessment, …] | Immutable tuple of distinct QuoteAssessment records |
| `reason_codes` | tuple[ReasonCode, …] | Distinct fixed ReasonCode values |
| `summary` | nonblank string | Nonblank local rationale, at most 500 characters, excluded from printable output |

### `JudgeAttempt`

One bounded attempt (strict integer 1 or 2) for a trial, preserving request hashes, local reply reference, answer/problem, and usage.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Support record schema version, fixed at 1 |
| `attempt_id` | nonblank string | Attempt identity |
| `trial_id` | nonblank string | Independent judge trial identity |
| `attempt` | 1, 2 | Strict integer 1 or 2 |
| `request_hash` | SHA-256 | Complete rendered request SHA-256 |
| `prompt_hash` | SHA-256 | Prompt content hash |
| `schema_hash` | SHA-256 | Closed reply schema hash |
| `input_tokens` | strict int ≥ 0 | Complete input token count; nullable when unavailable and unknown |
| `reserved_tokens` | strict int ≥ 0 | Nonnegative complete-input plus output reservation |
| `actual_prompt_tokens` | strict int ≥ 0 or null | Reported nonnegative prompt tokens, otherwise null |
| `actual_completion_tokens` | strict int ≥ 0 or null | Reported nonnegative completion tokens, otherwise null |
| `latency_ms` | strict int ≥ 0 | Nonnegative operation latency in milliseconds |
| `cached` | bool | Whether served from the raw-signal cache |
| `raw_ref` | string or null | Local raw-reply reference, excluded from printable output |
| `problem` | string or null | Fixed unusable-reply problem or null |
| `answer` | JudgeAnswer or null | JudgeAnswer or null when unusable/unavailable |

### `JudgeTrial`

One independent family/presentation trial. Available means an answer and no reason; unavailable means no answer and a fixed reason.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Support record schema version, fixed at 1 |
| `trial_id` | nonblank string | Independent judge trial identity |
| `target_id` | nonblank string | Derived assessment target identity |
| `identity` | JudgeIdentity | Complete configured scorer or judge identity |
| `presentation` | Presentation | Independent evidence_first or claim_theme_first order |
| `attempt_ids` | tuple[nonblank string, …] | Distinct attempt IDs in attempt order |
| `status` | SignalStatus | Signal availability or review processing status |
| `answer` | JudgeAnswer or null | JudgeAnswer or null when unusable/unavailable |
| `reason` | string or null | Fixed support/core refusal reason or null |

### `ReviewOutcome`

One processing outcome and its diagnostic flags, missing reasons, and contributing references. It has no acceptance or assignment field.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Support record schema version, fixed at 1 |
| `target_id` | nonblank string | Derived assessment target identity |
| `status` | ReviewStatus | Signal availability or review processing status |
| `flags` | tuple[nonblank string, …] | Distinct semantic/diagnostic flags; no acceptance rule |
| `missing` | tuple[nonblank string, …] | Distinct fixed reasons for missing signals |
| `signal_ids` | tuple[nonblank string, …] | Distinct contributing entailment signal IDs |
| `trial_ids` | tuple[nonblank string, …] | Distinct contributing judge trial IDs |

### `SupportCeilings`

One explicit allowance configuration; every field is a required strict nonnegative integer. Cache hits spend no dispatch allowance.

| Field | Type | Meaning |
| --- | --- | --- |
| `scorer_per_target` | strict int ≥ 0 | Required nonnegative scorer per target ceiling |
| `scorer_per_document` | strict int ≥ 0 | Required nonnegative scorer per document ceiling |
| `scorer_per_run` | strict int ≥ 0 | Required nonnegative scorer per run ceiling |
| `judge_per_target` | strict int ≥ 0 | Required nonnegative judge per target ceiling |
| `judge_per_document` | strict int ≥ 0 | Required nonnegative judge per document ceiling |
| `judge_per_run` | strict int ≥ 0 | Required nonnegative judge per run ceiling |
| `tokens_per_document` | strict int ≥ 0 | Required nonnegative tokens per document ceiling |
| `tokens_per_run` | strict int ≥ 0 | Required nonnegative tokens per run ceiling |

### `UsageRecord`

One operation usage observation. Counts are strict nonnegative integers; unknown reported usage remains null and unreported is explicit.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Support record schema version, fixed at 1 |
| `target_id` | nonblank string | Derived assessment target identity |
| `doc_id` | nonblank string | Immutable canonical document ID |
| `operation_id` | nonblank string | Scorer evaluation or judge dispatch identity |
| `kind` | scorer, judge | Declared context, scorer, or operation kind |
| `reserved_tokens` | strict int ≥ 0 | Nonnegative complete-input plus output reservation |
| `actual_prompt_tokens` | strict int ≥ 0 or null | Reported nonnegative prompt tokens, otherwise null |
| `actual_completion_tokens` | strict int ≥ 0 or null | Reported nonnegative completion tokens, otherwise null |
| `unreported` | bool | Whether actual usage was unreported (run manifest stores its count) |
| `cached` | bool | Whether served from the raw-signal cache |
| `latency_ms` | strict int ≥ 0 | Nonnegative operation latency in milliseconds |

### `SupportPolicy`

One versioned prompt and generation policy; exactly two attempts are permitted. No threshold or pooling policy exists.

| Field | Type | Meaning |
| --- | --- | --- |
| `support_version` | semantic-support/1 | Literal semantic-support/1 policy version |
| `prompt_text` | nonblank string | Caller-supplied local prompt, excluded from printable output |
| `prompt_hash` | SHA-256 | Prompt content hash |
| `parameters` | Parameters | Existing frozen extraction Parameters, with unchanged schema |
| `max_attempts` | 2 | Strict literal integer 2, provisional retry ceiling |

### `SupportRunRecord`

One immutable support run manifest. Binding tuples are sorted with unique keys. Two judge identities retain caller order; panel lineage checks happen before dispatch. started_at is UTC aware and software includes a valid lock_hash.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Support record schema version, fixed at 1 |
| `run_id` | nonblank string | Unique support run identity |
| `started_at` | UTC-aware datetime | UTC-aware support run start timestamp |
| `source_run_id` | nonblank string | Source extraction run ID |
| `source_run_hash` | SHA-256 | Canonical source-run provenance hash |
| `documents` | tuple[tuple[nonblank string, SHA-256], …] | Sorted immutable (document ID, canonical SHA-256) bindings |
| `codebook` | CodebookReference | Frozen CodebookReference |
| `configuration_hash` | SHA-256 | Complete support configuration content hash |
| `extractor_family` | nonblank string | Caller-supplied source extractor lineage |
| `scorer_identity` | ScorerIdentity | Configured ScorerIdentity |
| `judge_identities` | tuple[JudgeIdentity, JudgeIdentity] | Ordered pair of JudgeIdentity records |
| `support_version` | semantic-support/1 | Literal semantic-support/1 policy version |
| `validator_version` | nonblank string | Exact-span validator version |
| `software` | tuple[tuple[nonblank string, nonblank string], …] | Sorted immutable software name/version bindings, including lock_hash SHA-256 |
| `ceilings` | SupportCeilings | Explicit SupportCeilings |
| `counts_by_status` | tuple[tuple[ReviewStatus, strict int ≥ 0], …] | Sorted immutable (ReviewStatus, strict nonnegative count) bindings |
| `counts_by_reason` | tuple[tuple[nonblank string, strict int ≥ 0], …] | Sorted immutable (fixed support/core refusal or semantic ReasonCode, strict nonnegative count) bindings |
| `evaluations` | strict int ≥ 0 | Nonnegative dispatched scorer evaluation count |
| `requests` | strict int ≥ 0 | Nonnegative dispatched judge request count |
| `prompt_tokens` | strict int ≥ 0 | Nonnegative recorded prompt token total |
| `completion_tokens` | strict int ≥ 0 | Nonnegative recorded completion token total |
| `reserved_tokens` | strict int ≥ 0 | Nonnegative complete-input plus output reservation |
| `unreported` | strict int ≥ 0 | Whether actual usage was unreported (run manifest stores its count) |
| `cache_hits` | strict int ≥ 0 | Nonnegative raw-signal cache-hit count |
| `billable_cost` | none, self-hosted | Literal none, self-hosted; no billable inference |
| `artifact_hashes` | tuple[tuple[nonblank string, SHA-256], …] | Sorted immutable (artifact name, byte SHA-256) bindings |

### `SupportProblem`

| Value | Meaning |
| --- | --- |
| `malformed_record` | malformed record |
| `wrong_source_run` | wrong source run |
| `wrong_document` | wrong document |
| `unknown_claim` | unknown claim |
| `duplicate_claim` | duplicate claim |
| `unknown_quote` | unknown quote |
| `duplicate_quote` | duplicate quote |
| `invalid_quote` | invalid quote |
| `masks_mismatch` | masks mismatch |
| `invalid_bundle` | invalid bundle |
| `wrong_codebook` | wrong codebook |
| `codebook_not_approved` | codebook not approved |
| `unknown_theme` | unknown theme |
| `duplicate_theme` | duplicate theme |
| `parent_cycle` | parent cycle |
| `unknown_parent` | unknown parent |
| `input_changed` | input changed |
| `invalid_panel` | invalid panel |
| `input_too_long` | input too long |
| `replay_miss` | replay miss |
| `cache_corrupt` | cache corrupt |
| `transport_error` | transport error |
| `model_mismatch` | model mismatch |
| `tool_call_refused` | tool call refused |
| `malformed_reply` | malformed reply |
| `invalid_references` | invalid references |
| `scorer_failed` | scorer failed |
| `scorer_exhausted` | scorer exhausted |
| `judge_exhausted` | judge exhausted |
| `tokens_exhausted` | tokens exhausted |
| `storage_corrupt` | storage corrupt |
| `unexpected_error` | unexpected error |

### `SignalStatus`

| Value | Meaning |
| --- | --- |
| `available` | available |
| `unavailable` | unavailable |

### `Presentation`

| Value | Meaning |
| --- | --- |
| `evidence_first` | evidence first |
| `claim_theme_first` | claim theme first |

### `ReviewStatus`

| Value | Meaning |
| --- | --- |
| `refused` | refused |
| `incomplete` | incomplete |
| `flagged` | flagged |
| `assessed` | assessed |

### `ReasonCode`

| Value | Meaning |
| --- | --- |
| `wrong_attribution` | wrong attribution |
| `wrong_period` | wrong period |
| `negation` | negation |
| `scope_mismatch` | scope mismatch |
| `partial_support` | partial support |
| `theme_mismatch` | theme mismatch |
| `exclusion_conflict` | exclusion conflict |
| `context_only_support` | context only support |
| `insufficient_evidence` | insufficient evidence |
| `compound_claim` | compound claim |

The in-memory containers SupportSources, ResolvedInput, RefusedTarget,
AssessmentResult, SupportRunResult and StoredSupportRun are frozen dataclasses
with repr=False. They retain supplied typed records and tuples; ResolvedInput's
unchanged claim and SupportSources' artifacts never appear in printable output.
They do not dereference codebook examples or resolve repository paths.

### Public support library boundary

`earnings_themes.support` exports `Target`, `SupportSources`, `ResolvedInput`,
`resolve_target`, `assess_target`, `assess_run`, `write_support_run`,
`read_support_run`, and `reverify_support_run`. It also exports the pure metric
functions `auc_roc` and `accepted_claim_precision` and their closed typed parts
`HumanLabel`, `ContinuousSignal`, `Acceptance`, and `MetricReport`. These are the
implemented objects, with no wrapper that discovers artifacts or changes policy.
Neither the themes root initializer nor the support initializer imports a concrete
NLI or chat adapter. `support-nli` is an explicitly selected optional extra.

`resolve_target(stored_run, bundles, codebook, target, *, provenance_hash)`
returns `ResolvedInput` or `RefusedTarget`. The required provenance hash binds
the supplied source provenance, including curated fixture provenance.
`assess_target` requires keyword-only
`cache` and `extractor_family`; `assess_run` requires those plus `started_at` and
`software`. Extractor family is an explicit lineage input, never inferred from a
model alias. The complete assessment and storage signatures are documented below.

These shipped contracts describe raw signals and processing outcomes. The
[verification record](verification/semantic-support.md) records Stage 8 completion:
actual primary V4 inference, the user-only full root and both wording gates passed,
and the final whole-branch review cleared its findings. Stage 9 decides assignments;
Stage 11 supplies expert labels, calibration, view/pooling selection, agreement
floors, thresholds and fresh-call stability across extraction/scorer/judge caches.

### `ScoreRequest`

One nonpersisted evidence-only raw scoring request (`support.scorers`). Strict,
closed and frozen, with safe digest-only representations. The hypothesis is the
unchanged claim. A premise is one exact canonical quote slice or the versioned
rendering of individually bounded passages; attribution context and theme rules
are excluded.

| Field | Type | Meaning |
| --- | --- | --- |
| `premise` | string | Complete evidence premise, local and excluded from printable fields |
| `hypothesis` | string | Original unchanged claim, local and excluded from printable fields |
| `input_hash` | SHA-256 | Digest of support encoding version, premise and hypothesis |

### `ScoreReply`

One nonpersisted raw response (`support.scorers`), revalidated before consumption.
A score is finite in `[0,1]` and remains uncalibrated. Available replies require
no reason and a reported input count. Failures have a fixed reason and null score,
never a zero stand-in. Identity and input hash must match the request/adapter.

| Field | Type | Meaning |
| --- | --- | --- |
| `score` | finite float in [0,1] or null | Raw support signal; no pooling or acceptance policy |
| `reason` | fixed reason or null | Support/core failure reason; absent exactly when score exists |
| `input_tokens` | strict nonnegative integer or null | Adapter input count, required for an available reply |
| `latency_ms` | strict nonnegative integer | Reported operation latency; pre-dispatch refusals use zero |
| `identity` | ScorerIdentity | Bound checkpoint/runtime and full-input limit |
| `input_hash` | SHA-256 | Binding to complete premise/hypothesis request |

`score_requests(input)` re-verifies all linked quotes and retained source bindings
before rendering. For one quote it returns one evaluation to alias downstream as
both quote and joint signal rows. For several quotes it returns every quote request
plus one separate joint request (`None` scope). `evaluate_score(scorer, request)`
counts the complete request before dispatch, refuses over-limit inputs without
clipping, and checks strict counts, score validity and reply bindings. Expected
scorer/transport failures remain unavailable; unexpected adapter exceptions abort
with a safe fixed reason. `ScriptedScorer(script, token_counter, identity)` accepts
injected callables and retains requests locally with a safe count-only repr.

### `JudgeSubject`

Support's nonpersisted, strict, closed, frozen request identity. This has no
extraction-window subject. Its printable representation contains a digest only.

| Field | Meaning |
| --- | --- |
| `target_id` | Explicit resolved claim/theme target identity. |
| `input_hash` | Hash of the immutable resolved evidence, attribution context, claim and frozen theme. |
| `codebook_hash` | Selected frozen codebook content hash. |
| `presentation` | `evidence_first` or `claim_theme_first`. |
| `prompt_hash` | SHA-256 of the caller-supplied complete UTF-8 system text. |
| `schema_hash` | Canonical digest of the closed judge answer JSON schema. |
| `support_version` | Literal `semantic-support/1`. |
| `validator_version` | Exact-span validator version. |

### `JudgeRequest`

Support's nonpersisted local chat request, deriving from `SafePart`. Source-bearing
fields are excluded from printable representations; JSON serialization retains the
local request. Neither scorer outputs nor extractor rationale nor previous trials
appear. `render_judge(input, policy, presentation)` re-verifies all evidence and
checks the caller-supplied prompt hash. The two independent orders use identical
content/roles and document-order quotes, in separately tagged JSON blocks.

| Field | Meaning |
| --- | --- |
| `messages` | System instructions and one user message holding quoted evidence/context and claim/frozen-theme JSON blocks. |
| `reply_schema` | Strict closed `JudgeAnswer` JSON schema, including nested quote assessments. |
| `parameters` | Existing extraction `Parameters`, unchanged. |
| `subject` | `JudgeSubject`; never sent by the transport. |

`Judge` exposes `identity`, `count_tokens(request)` and `complete(request)`.
`JudgeBinding(identity, transport, token_counter)` uses a caller-supplied complete
local tokenizer/chat-template counter bound to the same runtime, covering all
messages and schema framing, without a character heuristic. Before dispatch it
checks the transport's local model, weights and runtime identity. For a single
weight file, Stage 7's `weights_sha256` equals that file's SHA-256; for multiple
files, it equals the canonical digest of path/hash records sorted by relative path.
An empty local manifest refuses. `input_limit` is the total context ceiling:
complete input tokens plus reserved `max_tokens` must fit; `max_tokens` must also
fit `output_limit`. Over-limit requests refuse `input_too_long` without dispatch,
clipping or hidden chunking. Token counts reject booleans and negative values.

`validate_panel(extractor_family, identities)` requires two distinct explicitly
configured judge families, at least one different from the extractor. Aliases
never establish lineage. `parse_answer(reply, input, identity)` checks tool/model
refusals, closed schema and exactly one assessment for each supplied quote ID.
`SupportTransportError.reply` retains a refused transport reply and its usage
locally; only a fixed reason prints and its exception chain is suppressed.
`ScriptedJudge(script, token_counter, identity)` is test-only, retains requests
locally and exposes a count-only representation. No retry, cache or budget policy
is implemented by these transport seams.


### `SupportCacheEntry`

One support raw-response artifact, a closed frozen `SupportRecord`. Source-bearing
fields serialize locally; printable forms contain only its digest. The cache never
stores review outcomes, verdicts or quote-verification decisions.

| Field | Meaning |
| --- | --- |
| `schema_version` | Support schema version 1. |
| `key` | SHA-256 of the full canonical key material. |
| `kind` | `scorer` or `judge`; selects typed request, identity and reply validation. |
| `material` | Canonical JSON covering the original source run, claim, quote locators, canonical documents, structure/masks, evidence/context bounds, provenance, theme/codebook, request, runtime identity and policy. No codebook examples are dereferenced. |
| `request` | Typed `ScoreRequest` or `JudgeRequest`, checked against material on reuse. |
| `identity` | Typed `ScorerIdentity` or `JudgeIdentity`, including limits and runtime/checkpoint metadata. |
| `reply_hash` | Integrity digest of raw reply JSON plus fixed transport refusal metadata. |
| `reply` | Raw `ScoreReply` or `ModelReply`; never a derived assessment. |
| `refusal_reason` | Optional fixed transport/schema refusal for a judge reply: `transport_error`, `model_mismatch`, `tool_call_refused`, `malformed_reply`, or `invalid_references`. Scorer entries require null. This is not a semantic review decision. |

`scorer_key(input, request, identity, policy)` and `judge_key(...)` return
`SupportCacheKey`, a SHA-256 `str` subclass with immutable canonical local binding
material. Its string/repr are ordinary safe digest text. Bare digest strings cannot
recover expected typed bindings and are refused. Bound material is rehashed and
checked on every boundary; no mutable registry is used. `SupportCache(directory,
mode)` supports `live` and `replay`, typed `lookup(key, kind)` returning a raw reply
or `None`, `put(key, raw, *, refusal_reason=None)` returning a relative artifact reference,
`refusal_reason(key)` returning integrity-checked judge refusal metadata, and
`raw_ref(key)`. Neither mode dispatches itself; the coordinator treats replay
misses as `replay_miss` and live misses as dispatch candidates. Writes use a
temporary sibling and atomic replacement; incompatible existing content and
corruption refuse. Raw model failures stay explicit unavailable responses or local
attempt artifacts. Scorer model/input mismatches refuse cache publication; judge
wrong-model replies are retained under the expected request/identity binding and
always reparsed as unusable attempts. A cached transport-refused reply remains
unusable even if its answer body otherwise validates. Metadata changes alter the
integrity digest and cannot overwrite an existing entry. Earlier Stage 8 development
cache envelopes without the combined integrity digest are invalidated as corrupt;
no core, extraction, Stage 6, or support schema version changes. Evidence
must be reverified outside the cache on every reuse. No bypass or concurrent-writer
guarantee is provided.

`Allowance(ceilings)` reserves one scorer evaluation per actual request and one
judge request plus full input/allowed completion tokens per attempt. The caller
checks complete tokenizer counts and runtime context/output limits before reserving.
`reserve_scorer(target_id, doc_id)` and `reserve_judge(target_id, doc_id,
input_tokens, completion_limit)` return safe reservation digest IDs.
`settle(reservation_id, usage)` is once-only: known usage replaces charged tokens
with actual usage, retaining original reservation and any overspend; unknown usage
retains the full reservation and marks `unreported`. Scorer counts are never
released. `snapshot()` returns immutable safe `UsageRecord` tuples. All applicable
target/document/run ceilings are checked before changing state; exhaustion uses
fixed codes. Cache hits and the one-quote joint alias make no extra reservation.


### Assessment orchestration and review outcomes

`assess_target(input, scorer, judges, policy, allowance, *, cache,
extractor_family)` requires explicitly supplied extractor lineage. The Stage 7
model alias cannot establish it. Policy hashes, typed scorer/judge identities,
lineage/panel requirements and bound transport preflight validate before dispatch.
Current exact evidence gates run before scoring and before result publication.
Initial integrity failures return a refused result with zero dispatch. A source
change after dispatch aborts publication with fixed `input_changed`, preserving
completed raw cache artifacts and settled accounting locally; it never fabricates
a zero-dispatch refusal record after calls occurred.
The assessor evaluates each quote and a separate joint premise; a one-quote joint
signal aliases its sole evaluation. Raw cache hits spend no allowance, replay misses
remain unavailable, and live misses count complete input before reservation.
Judge context limits include reserved output and a separate output limit applies.

Two supplied families each receive `evidence_first` and `claim_theme_first`, in
that order. Four independent trials retain at most two attempts each. Only
unusable replies retry, with the original trial messages plus fixed reason and
trusted field feedback. Raw replies/rationales never enter retry feedback or another
trial. Every dispatched request is settled once, including unavailable requests and
usage attached to refused raw replies. Cache hits have explicit cached usage rows
with zero reservation; live result rows preserve reported latency.

`derive_outcome(target_id, entailment, trials, evidence_ids)` consumes quote IDs in
`evidence_ids`, validates required signal/trial coverage and compares quote
contributions by ID. Unavailable required signals yield `incomplete`, preserving
all semantic flags. Complete targets are `flagged` for any reason code,
`claim_support_unsupported`, `claim_support_uncertain`,
`theme_fit_does_not_fit`, `theme_fit_uncertain`, `quote_irrelevant`,
`quote_contradicting`, `quote_uncertain`, or `category_disagreement`.
Contextual quote contribution alone is permitted; `context_only_support` flags
assertion support found only in context. Numeric differences and low NLI scores
never determine a flag or threshold. Complete unflagged targets are `assessed`;
integrity failures are `refused`. These processing outcomes confer no acceptance.

Unexpected adapter errors abort as `SupportError("unexpected_error")` with no
printed chain. `unexpected_error(error)` attaches only a safe `diagnostic`:
an exact trusted builtin exception type name, or fixed `Exception` for custom
or untrusted class identities. `str` and `repr` remain the fixed reason; exception
messages, raw replies and source text never enter diagnostics. Completed raw calls
remain cached; there is no durable process recovery.

### Support run coordination and immutable storage

`assess_run(run_id, sources, targets, scorer, judges, policy, ceilings, *,
extractor_family, cache, started_at, software)` preflights UTC time, nonblank
software identities including `lock_hash`, policy hash, typed identities, explicit
family lineage and all ceilings before resolving any target. Duplicate requested
identities and mixed source-run/codebook references refuse the run without dispatch.
Targets are resolved and assessed sequentially in caller order under one shared
`Allowance`. Refused rows retain IDs/hashes/fixed reasons without evidence links or
calls. Post-dispatch input mutation aborts the run, retaining completed cache data
and accounting; it never becomes a zero-dispatch refusal.

The manifest counts each processing status and each missing or semantic reason code
once per target. Categorical flags remain fully available in outcomes. Evaluation,
request, reservation, actual token, unreported and cache totals reconcile to usage
rows. Cache-hit usage is auditable but contributes no dispatch count or reserved
allowance. Reported overspend remains visible; later reservations still obey the
ceilings. No processing-status or no-theme observation is invented.

`write_support_run(directory, result, sources)` validates all derived references
and re-resolves each non-refused target against the supplied extraction records,
canonical bundles, current masks and frozen codebook before creating a temporary
sibling. It writes eight explicit Polars schemas (`targets`, `evidence`, `contexts`,
`entailment`, `trials`, `attempts`, `usage`, `outcomes`) as Parquet plus `run.json`.
Empty tables retain their declared schemas. Nested identity, theme and answer parts
use declared structs/lists; nullable scores, reasons, answers and usage remain null.
No support field duplicates canonical quote/context text. Rationales remain local.
A complete sibling is renamed into a new destination; failed/interrupted writes
remove the sibling. Existing destinations are never overwritten.

`SupportRunRecord.artifact_hashes` reserves two namespaces: `<table>.parquet` binds
the bytes published in the run directory, and `raw/<64-hex-digest>.json` binds the
bytes of caller-owned raw cache artifacts. `JudgeAttempt.raw_ref` remains the confined
`<64-hex-digest>.json` cache filename. `SupportCache.artifact_hash(reference)` validates
the closed envelope, canonical key/request/identity bindings and reply/refusal
integrity before hashing bytes. It rejects malformed names, symlinks, missing files
and corrupt entries. No raw request/reply is copied into a support run directory.

`read_support_run(directory)` verifies each Parquet hash/schema, strict closed models,
unique keys/foreign keys, exact evidence sets, required quote/joint signal slots,
four family/presentation trials, ordered attempt ownership, identities/hashes,
recomputed outcomes/counts and dispatch ceilings. Raw-reference manifest bindings
must be complete and confined. The reader cannot check external cache bytes without
that cache and does not claim to do so. Inconsistency raises fixed `storage_corrupt`.

Loading establishes structural consistency. Before consuming outcomes, call
`reverify_support_run(stored, sources)` to repeat exact-span/source/theme/context
resolution and compare all retained input and scorer hashes. A mismatch refuses
reuse. Auditable refused rows remain refused; usable results are returned as
processing outcomes and are never promoted to accepted theme assignments.
No new persisted models or schema versions are introduced by these seams.

## Explicit support metric parts

These nonpersisted closed, strict, frozen `SafePart` models contain no source
text. Their printable forms expose only class and content hash. `LabelTask` is
`Literal["claim_support", "joint_support"]`; each call selects one task.

`auc_roc(population, labels, signals, *, task, view)` requires unique population
IDs and unique IDs per input, with all inputs in the supplied population and
matching task/view. It joins labeled targets with finite scores in the selected
view. Pairwise ranking gives ties half credit. No joined labels yields
`no_scored_labels`; a joined set lacking either class yields `one_class`.
Per-quote observations require their own IDs and human labels; joint labels are
never broadcast. Four judge views reuse the same labels in four separate calls.

`accepted_claim_precision(population, labels, decisions, *, task)` uses only
external acceptance decisions. The denominator is human-labeled accepted
targets; no such targets yields `no_labeled_accepted`. Missing acceptance
decisions are omitted, never inferred. No score join is requested, so score
counts are zero. These functions establish semantics, not observed quality;
Stage 11 owns view selection, calibration, pooling, and thresholds.

### `HumanLabel`

| Field | Meaning |
| --- | --- |
| `target_id` | Explicit nonblank observation ID, unique within the supplied labels. |
| `task` | `claim_support` or `joint_support`, matching the selected task. |
| `supported` | Strict integer `0` or `1`, supplied by a human; booleans refused. |

### `ContinuousSignal`

| Field | Meaning |
| --- | --- |
| `target_id` | Explicit nonblank observation ID in the supplied population. |
| `task` | `claim_support` or `joint_support`, matching the selected task. |
| `view` | Explicit nonblank score-view name, matching the selected view. |
| `score` | Finite float in `[0,1]`, or `None` for an unavailable score. |

### `Acceptance`

| Field | Meaning |
| --- | --- |
| `target_id` | Explicit nonblank observation ID in the supplied population. |
| `task` | `claim_support` or `joint_support`, matching the selected task. |
| `accepted` | Strict bool external decision; never derived by support metrics. |

### `MetricReport`

| Field | Meaning |
| --- | --- |
| `value` | Finite metric in `[0,1]`, or `None` when undefined. |
| `reason` | `None` for a defined value; otherwise `no_scored_labels`, `one_class`, or `no_labeled_accepted`. |
| `task` | Explicit selected label task. |
| `view` | Selected score view for AUC, or `external_acceptance` for precision. |
| `population_count` | Number of unique supplied population IDs. |
| `labeled_count` | Number of human labels supplied in the population. |
| `scored_count` | Number of nonmissing selected-view scores; zero for precision. |
| `joined_count` | Labeled scored targets for AUC; labeled accepted targets for precision. |
| `accepted_count` | Number of external true decisions, including unlabeled cases; zero for AUC. |
| `missing_score_count` | Population count minus scored count for AUC, including absent and `None` scores; zero for precision. |
| `missing_label_count` | Population count minus labeled count, independently of scores/decisions. |
| `accepted_without_label_count` | External true decisions lacking a human label; zero for AUC. |

All counts are strict nonnegative integers. Input models are revalidated at each
metric boundary; invalid joins raise only fixed `invalid_references`, and
malformed records raise fixed `malformed_record`. No artifact is discovered.

### `LocalScorerConfig`

Closed, frozen, safe configuration for an explicitly selected local NLI adapter.
It is supplied by the caller, never discovered from repository paths. Revisions,
complete runtime tuple, encoding and mappings are pinned. Primary input limit is
at most 512, an explicit tokenizer-metadata policy rather than a T5 architectural
limit. Hashes are checked before heavyweight imports; all local files must appear
in the manifest and symlink files are refused. Every inference file is confined to
the absolute directory. No file is downloaded by the adapter.

| Field | Type | Meaning |
| --- | --- | --- |
| `kind` | minicheck, deberta | Explicit primary or named alternative selection; no fallback |
| `local_directory` | string | Absolute supplied checkpoint directory, excluded from repr |
| `revision` | string | Exact immutable repository revision |
| `files` | tuple[FileHash, …] | All local file checksums; config, tokenizer and checkpoint required |
| `runtime_versions` | tuple[tuple[string, string], …] | Ordered exact torch/transformers/sentencepiece/tokenizers/safetensors versions |
| `device` | cpu, mps | Explicit device bound to scorer identity |
| `precision` | float32 | Explicit inference precision bound to scorer identity |
| `input_limit` | strict int > 0 | Complete encoded input budget; primary ≤512, alternative capped by model positions |
| `encoding_version` | minicheck-first-step/1, deberta-pair/1 | Fixed rendering/kernel version; runtime identity appends checkpoint serialization |
| `label_mapping` | tuple[strict int, …] | Primary vocabulary IDs (3,209) or alternative ordered NLI indices (0,1,2) |
| `weight_license` | WeightLicense | Verified weight terms, date and intended use required before dispatch |

`MiniCheckScorer(config)` and `DebertaScorer(config)` implement `EntailmentScorer`.
Only their constructors import the optional runtime. The primary loads the pinned
PyTorch checkpoint with `weights_only=True`, `use_safetensors=False`; the alternative
loads native safetensors. Both use `local_files_only=True`, `trust_remote_code=False`,
evaluation and inference mode. `count_tokens` counts the complete nontruncated
encoding; `score` returns raw finite probabilities with identity/hash/latency/tokens
or fixed unavailable reasons. There is no class decision, generation, aggregation,
cutoff, wrapper chunking or alternative fallback. Configuration/runtime setup errors
have fixed `model_mismatch`; inference errors return fixed `scorer_failed`.

## earnings-themes coding records, schema version 1

The Stage 9 deductive contracts (`earnings_themes.coding.records`) have coding
policy version `"deductive-coding/1"` (`earnings_themes.coding.records.CODING_VERSION`).
Core schema 2, validator `"3"`, Stage 6 records, extraction schema 1 and
`"pointer-traversal/1"`, support schema 1 and `"semantic-support/1"` are unchanged.
All coding parts are frozen, closed, strict Pydantic contracts. Integer literals,
attempts, offsets, ceilings and counts reject bools, floats and numeric strings.
`CodingRecord` is the separate base for persisted coding schema 1 records.

`checked(value, model)` reparses JSON mode at untrusted boundaries. For a supplied
Part, it first validates the Python-mode data, because JSON serialization can
coerce an invalid copied boolean to an integer. Both dumps suppress serializer
warnings, which can contain input text. Copied and constructed instances receive
the same invariant checks as fresh inputs. Boundary errors are fixed
`CodingError("malformed_record")` with source-bearing exception chaining suppressed.
`CodingError` admits only exact string values in the union of support/core reasons
and CodingProblem; unknown values become `unexpected_error` without printing the
value. The reusable reason-field guard enforces that same vocabulary.

Printable coding parts expose only their class and content SHA-256. Local JSON
intentionally retains local attributes and prompt data and must not be logged.
Tests use invented text and identifiers; these contracts do not open pilot text,
gold, codebook examples or source artifacts. The contracts introduce no numeric
acceptance policy. Topic, sentiment, direction and event type are optional
model-derived attributes beside the unchanged claim, with no quality evaluation
implied. Theme IDs alone represent themes and subthemes; hierarchy is resolved
from the approved definition's parent_id during reply parsing and target resolution.

### `CodingPart`

Fieldless strict immutable base for new coding parts, with hash-only diagnostics,
strict integer-literal guards and fixed reason validation. It inherits Part,
separately from support SafePart so coding reasons retain their own vocabulary.

| Field | Type | Meaning |
| --- | --- | --- |

### `CodingRecord`

Base for persisted coding records. Integer schema literals receive validation
before Pydantic can accept boolean or floating-point equivalents.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Strict literal integer coding schema version, default 1 |

### `CodingAttributes`

Optional semantic annotations, separate from closed theme identifiers. No
importance, rank, cluster label, acceptance, claim or replacement evidence field
exists. Null means no supplied annotation, and the default for every field is null.

| Field | Type | Meaning |
| --- | --- | --- |
| `topic` | nonblank string or null | Local model-derived topic, excluded from printable field output |
| `sentiment` | positive, negative, neutral, mixed, unknown or null | Optional categorical sentiment; never an importance score |
| `direction` | increase, decrease, unchanged, mixed, unknown or null | Optional categorical direction beside the claim |
| `event_type` | nonblank string or null | Local model-derived event type, excluded from printable field output |

### `CodingReply`

Typed multi-label classifier response. Theme IDs must be distinct and nonblank;
an empty tuple is allowed. Reply parsing and target resolution check frozen-codebook
membership and hierarchy. Extra fields cannot request tools, rewrite
definitions or evidence, create themes, or declare acceptance.

| Field | Type | Meaning |
| --- | --- | --- |
| `theme_ids` | tuple[nonblank string, …] | Distinct proposed theme identifiers, preserving caller order |
| `attributes` | CodingAttributes | Separate optional semantic annotations |

### `CodingPolicy`

Versioned classifier prompt and generation settings. Exactly two attempts are
permitted provisionally; this retry ceiling does not decide semantic acceptance.

| Field | Type | Meaning |
| --- | --- | --- |
| `coding_version` | deductive-coding/1 | Literal coding policy version, default deductive-coding/1 |
| `prompt_text` | nonblank string | Caller-supplied local prompt, excluded from printable field output |
| `prompt_hash` | SHA-256 | Prompt content hash |
| `parameters` | Parameters | Existing frozen extraction generation Parameters, unchanged |
| `max_attempts` | 2 | Strict literal integer 2, provisional retry ceiling |

### `CodingCeilings`

Explicit caller-supplied nonnegative ceilings, with no numeric defaults. Zero is
allowed. No ceiling is an acceptance threshold or production inference budget.

| Field | Type | Meaning |
| --- | --- | --- |
| `requests_per_claim` | strict int ≥ 0 | Classifier request ceiling for one claim, including retries |
| `requests_per_document` | strict int ≥ 0 | Classifier request ceiling for one document |
| `requests_per_run` | strict int ≥ 0 | Classifier request ceiling for one run |
| `tokens_per_document` | strict int ≥ 0 | Classifier token ceiling for one document |
| `tokens_per_run` | strict int ≥ 0 | Classifier token ceiling for one run |

### `PolicyReference`

Explicit acceptance-policy provenance bound to codebook ID, version and content
hash, and the complete classifier and support configurations. A calibrated policy requires a
calibration reference; a fixture policy requires null. No reference implements a
threshold or approves a production policy.

| Field | Type | Meaning |
| --- | --- | --- |
| `policy_id` | nonblank string | Explicit external acceptance-policy identifier |
| `policy_hash` | SHA-256 | External policy content hash |
| `kind` | fixture, calibrated | Fixture-only or externally calibrated policy provenance |
| `codebook` | CodebookReference | Frozen codebook identifier, version and content hash |
| `classifier_configuration_hash` | SHA-256 | Exact classifier proposal configuration to which the policy applies; required before first coding release |
| `support_configuration_hash` | SHA-256 | Exact support configuration to which the policy applies |
| `calibration_reference` | SHA-256 or null | Calibration artifact hash, present exactly for calibrated kind |

### `PolicyVote`

External policy decision and supporting quote identifiers. Accept requires at
least one distinct quote ID; reject and review require an empty tuple. Subsequent
consuming gates establish evidence validity and supporting contributions; a
well-formed vote alone cannot establish acceptance.

| Field | Type | Meaning |
| --- | --- | --- |
| `action` | accept, reject, review | Explicit external policy decision |
| `supporting_quote_ids` | tuple[nonblank string, …] | Distinct original document-scoped quote IDs for accept; otherwise empty, default empty |

### `CodingProblem`

Fixed coding reason vocabulary. It also supplies permitted persisted reason
strings alongside the unchanged support/core reason vocabulary.

| Value | Meaning |
| --- | --- |
| `malformed_record` | Record fails the closed typed coding contract |
| `malformed_reply` | Classifier response fails its closed reply contract |
| `invalid_references` | Response or decision contains unusable identifiers |
| `hierarchy_conflict` | Proposal contains an incompatible ancestor/descendant combination |
| `input_changed` | Current input differs from its recorded binding |
| `input_too_long` | Complete rendered input exceeds the explicit adapter limit |
| `model_mismatch` | Model identity differs from the configured runtime |
| `tool_call_refused` | Model response requests a tool that coding does not supply |
| `transport_error` | Classifier transport fails without a usable response |
| `cache_corrupt` | Cached artifact fails integrity or parsing checks |
| `replay_miss` | Offline replay has no matching stored response |
| `requests_exhausted` | Explicit classifier request ceiling prevents dispatch |
| `tokens_exhausted` | Explicit token ceiling prevents dispatch |
| `calibration_required` | No externally calibrated acceptance policy is supplied |
| `policy_mismatch` | External policy bindings differ from the current inputs |
| `policy_accept` | Explicit external policy requests acceptance, subject to consuming gates |
| `policy_reject` | Explicit external policy rejects the target |
| `policy_review` | Explicit external policy requests review |
| `assessment_refused` | Stage 8 assessment processing refused the target |
| `assessment_incomplete` | Stage 8 assessment processing lacks required signals |
| `assessment_flagged` | Stage 8 assessment processing records review flags |
| `missing_assessment` | Required support assessment is unavailable |
| `invalid_contribution` | Selected quote lacks the required supporting contribution |
| `no_theme_fit` | Valid empty proposal finds no theme fit, eligible for novelty review |
| `mixed_codebook` | Inputs combine incompatible codebook identities or versions |
| `fixture_policy` | Result uses an explicitly fixture-only acceptance policy |
| `storage_corrupt` | Stored coding artifact fails integrity or parsing checks |
| `unexpected_error` | Unknown caller reason or unexpected failure is redacted |

### `CodingInput`

`earnings_themes.coding.input.CodingInput` is a frozen transient dataclass,
outside the persisted coding schema. Its `repr` and `str` omit all fields,
including source text, claim wording, definitions, and prompts.

| Field | Type | Meaning |
| --- | --- | --- |
| `sources` | SupportSources | Caller-supplied saved extraction records, immutable canonical bundles, approved codebook, and provenance hash |
| `doc_id` | str | Immutable canonical document identity for the requested claim |
| `claim_id` | str | Original Stage 7 claim identity, resolved within doc_id |
| `probes` | tuple[ResolvedInput, …] | Complete integrity probes, ordered by theme_id, for every frozen theme; no proposals, assessments, or assignment decisions |
| `input_hash` | SHA-256 | Digest of deductive-coding/1, document and claim identities, and the ordered Stage 8 input hashes |

`resolve_coding_input(sources: SupportSources, doc_id: str, claim_id: str) ->
CodingInput` resolves every theme through Stage 8's public `resolve_target`.
The gate requires exact source dataclass and tuple container types, a nonempty
approved codebook, its identifier/version/content hash, a valid theme graph,
the original claim and every original quote link, strict offsets, current masks,
and source-run/configuration bindings. A bad original link refuses the whole
input even when another link is good. Each snapshot contains definition and
inclusion/exclusion rules without example fields. Supplied example metadata
participates in the frozen codebook hash; examples, discovery bundles, signed
records, and files are never dereferenced or opened by this boundary.

`reverify_coding_input(input: CodingInput) -> CodingInput` first revalidates each
retained probe through Stage 8's public `reverify_input`, then resolves the
complete current input anew. Equal-valued copied booleans or floats cannot
stand in for strict offsets. The input hash, ordered target records, evidence,
contexts, and unchanged claim must agree with the new resolution. Valid source
changes still refuse with `input_changed`; integrity failures retain the first
closed Stage 8/core reason from flags and missing reasons, with
`invalid_references` as the fallback. Other malformed inputs produce the fixed
`malformed_record` error with source-bearing exception chaining suppressed.
No classifier, scorer, judge, acceptance policy, or filesystem operation is
dispatched here. These checks establish integrity only, never semantic support
or acceptance.

### `CodingSubject`

The classification request's integrity subject, kept separate from transported
messages. It binds the original document and claim, complete coding input, frozen
codebook reference, prompt and reply schema, and coding/verifier versions. It has
no extraction-window or support-trial fields.

| Field | Type | Meaning |
| --- | --- | --- |
| `doc_id` | nonblank string | Original immutable canonical document identity |
| `claim_id` | nonblank string | Original Stage 7 claim identity within doc_id |
| `input_hash` | SHA-256 | Complete ordered CodingInput digest |
| `codebook` | CodebookReference | Frozen approved codebook identifier, version and content hash |
| `prompt_hash` | SHA-256 | Hash of exact caller-supplied prompt UTF-8 bytes |
| `schema_hash` | SHA-256 | Digest of the generated CodingReply JSON schema |
| `coding_version` | deductive-coding/1 | Literal coding policy version, default deductive-coding/1 |
| `validator_version` | nonblank string | Current exact-evidence validator version |

### `CodingRequest`

A structural Stage 7 ChatRequest with a coding subject. Printable representations
expose only the coding part's content hash. Local JSON contains supplied data and
must not be logged. The request has no alternative source text or evidence repair.

| Field | Type | Meaning |
| --- | --- | --- |
| `messages` | tuple[Message, …], length ≥ 2 | System prompt and one bounded JSON user payload; excluded from printable field output |
| `reply_schema` | dict[str, Any] | Generated closed CodingReply JSON schema; recursively accepts only JSON primitives, finite numbers, lists and dictionaries with string keys; excluded from printable field output |
| `parameters` | Parameters | Existing frozen extraction generation settings, unchanged |
| `subject` | CodingSubject | Non-transported coding integrity bindings |

### `ProposalRecord`

One explicit proposed claim–theme target, before assessment or acceptance. Several
proposals may share the same original document and claim; evidence remains linked
through the unchanged source claim rather than copied into each proposal.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Strict literal integer coding schema version, default 1 |
| `proposal_id` | nonblank string | Proposal identity |
| `coding_run_id` | nonblank string | Coding run that produced the proposal |
| `classification_id` | nonblank string | Classification result that selected this target |
| `target` | Target | Original source run, document, claim, selected theme and frozen codebook reference |
| `input_hash` | SHA-256 | Complete ordered CodingInput digest |

### `AttributeRecord`

Separate optional model-derived annotations beside the unchanged Stage 7 claim.
They cannot change evidence, supply theme identifiers or confer acceptance.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Strict literal integer coding schema version, default 1 |
| `coding_run_id` | nonblank string | Coding run that produced the annotations |
| `doc_id` | nonblank string | Original immutable canonical document identity |
| `claim_id` | nonblank string | Original Stage 7 claim identity within doc_id |
| `input_hash` | SHA-256 | Complete ordered CodingInput digest |
| `attributes` | CodingAttributes | Separate nullable topic, sentiment, direction and event_type |

### `NoveltyItem`

A valid empty classification's pointer-only human-review item. It creates no
production theme identifier, inferred definition, copied quote, or annotation.
The novelty identity binds coding run, classification, input hash and no_theme_fit.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | 1 | Strict literal integer coding schema version, default 1 |
| `novelty_id` | nonblank string | novelty- followed by the digest of coding_run_id, classification_id, input_hash and reason |
| `coding_run_id` | nonblank string | Coding run that produced the unmatched result |
| `classification_id` | nonblank string | Valid empty classification result |
| `source_run_id` | nonblank string | Original Stage 7 extraction run identity |
| `doc_id` | nonblank string | Original immutable canonical document identity |
| `claim_id` | nonblank string | Original Stage 7 claim identity within doc_id |
| `codebook` | CodebookReference | Frozen approved codebook identifier, version and content hash |
| `input_hash` | SHA-256 | Complete ordered CodingInput digest |
| `original_quote_ids` | tuple[nonblank string, …] | Original claim links in their original order; scoped by doc_id |
| `reason` | no_theme_fit | Literal unmatched reason, default no_theme_fit |

`render_coding(input: CodingInput, policy: CodingPolicy) -> CodingRequest` first
reverifies the complete input through the public coding input gate and validates
the policy and exact prompt hash. It renders the unchanged claim, individually
bounded exact quoted slices, separately labeled attribution-context slices, every
ordered ThemeSnapshot, and exact frozen multi-label/boilerplate strings in one
JSON user message. Offsets remain canonical Python character spans; no text is
normalized, stitched or clipped. Examples are not opened or rendered, parent
rules are not inherited, sector tags are not inferred issuer classifications,
and no extractor rationale or accepted status enters the payload. Unstructured
generation appends the generated closed reply schema to the system prompt while
preserving the separate exact prompt and schema hashes.

`parse_coding_reply(reply: ModelReply, input: CodingInput, model_id: str) ->
CodingReply` repeats input verification, validates the reply, refuses tool calls
or model mismatch, then parses the closed JSON response. Malformed JSON, extra
keys and invalid attribute values produce fixed malformed_reply; unknown theme
IDs produce invalid_references. It considers the complete frozen snapshot and
refuses any selected ancestor together with its descendant as hierarchy_conflict.
Sibling selections, child-only selections, and parent-only selections remain
possible under each theme's own definition; there is no automatic parent target
or candidate pruning. A valid empty tuple remains a valid unmatched result.

`targets_for(input: CodingInput, reply: CodingReply) -> tuple[Target, ...]` repeats
input/reply validation and frozen membership/hierarchy checks, returning only
explicit selected original targets sorted by theme ID. `novelty_for(input,
reply, *, coding_run_id, classification_id) -> NoveltyItem | None` repeats input
and reply validation and returns the original evidence pointers exactly when
the supplied valid reply is empty. Nonempty parsed proposals return None.
`unusable_feedback(reason: str) -> str` formats a closed reason as
`Unusable reply: <closed reason>. Return the closed JSON response only.` Unknown
caller reasons become unexpected_error, without source or model wording.

These seams render and parse only; they dispatch no inference and perform no
retry. Classifier transports and raw caches below enforce structural request and
runtime bindings. Bounded attempts and comparison with the current complete
source/policy/generated schema belong to subsequent coding orchestration.

### Classifier protocol and local binding

`earnings_themes.coding.adapters.Classifier` exposes `identity: JudgeIdentity`,
`count_tokens(request: CodingRequest) -> int`, and `complete(request:
CodingRequest) -> ModelReply`. The reused JudgeIdentity represents the classifier
here; its explicit family, runtime file manifest, input/output ceilings and local
weight license are retained without choosing or loading weights.

`ScriptedClassifier(script, token_counter, identity)` is an invented-reply fake
with a safe request-count-only representation and a local requests list. It
requires scripted hosting. Counts must be nonnegative exact integers; bools,
floats and numeric strings are refused. Completion enforces full input plus
reserved-output and separate output limits before dispatch.

`earnings_themes.coding.local.ClassifierBinding(identity, transport,
token_counter)` repeats identity preflight before dispatch and after the callback.
Local transport identity must match hosting, model ID, full manifest-derived
weights hash, runtime and runtime version. Missing licensed local weights or an
empty local file manifest is refused. Scripted transports must match the explicit
scripted hosting/model identity. Public protocol imports never import this
concrete binding or construct a client. Neither coding module imports httpx;
caller-supplied Stage 7 LocalAdapter owns loopback HTTP, credentials refusal,
tool-free requests and redirect refusal.

Both classifier seams detach and strictly reparse full requests and identities.
Full request fingerprints before/after counters and transport callbacks detect
schema, message, parameter and subject mutation; identity changes are also
refused. Limits include the full request and reserved output, with no clipping.
The caller must supply a complete runtime tokenizer/chat-template/schema counter;
no heuristic or production tokenizer is introduced. Unexpected diagnostics use
fixed unexpected_error; CodingTransportError retains a supplied raw refused
ModelReply and usage with only the fixed transport reason printable. This guard
does not establish semantic support or current source/policy correspondence.

### `CodingCacheEntry`

One local raw classifier response, including refused attempts and usage, with no
accepted decision or assessment verdict. Its strict shape has an independent
coding schema 1 and a content-hash-only representation.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | literal 1 | Separate persisted coding schema |
| `key` | SHA-256 | Digest of coding schema/version and complete strictly reparsed request/identity |
| `request` | CodingRequest | Full rendered messages, closed schema, generation parameters and integrity subject |
| `identity` | JudgeIdentity | Explicit classifier family, runtime, ceilings, hosting and local license bindings |
| `input_tokens` | integer ≥ 0 | Caller-counted full request tokens; retained for tokenizer-free replay accounting and bound in raw hash |
| `reply` | ModelReply | Unmodified raw response, transport-reported usage, model, tool indicator and latency |
| `reply_hash` | SHA-256 | Digest of the raw reply, fixed refusal reason and counted input tokens |
| `refusal_reason` | transport_error, model_mismatch, tool_call_refused or null | Raw transport refusal only; unknown, semantic and acceptance reasons are refused |

`CodingCache(directory: Path, mode: Literal["live", "replay"])` selects a local
raw-artifact directory without startup I/O. Mode strings are exact; neither mode
provides fresh-call bypass, and lookup performs no inference. The coding cache
namespace is separate from extraction/support; callers choose its directory.
`get(request, identity) -> CodingCacheEntry | None` reads only the complete key's
`<64 lowercase hex>.json` file, returning None only when it is absent. It rechecks
the entry's key, request, identity and raw reply/count/refusal hash; malformed,
mismatched, renamed or symlinked entries yield fixed cache_corrupt.

`put(request, identity, reply, *, input_tokens, refusal_reason=None) -> str`
strictly validates a complete snapshot and writes canonical JSON through a unique
tempfile sibling. Publication creates a hard link without replacing an existing
entry, followed by temporary-file cleanup. An identical existing entry is reused;
different content is refused and preserved. Write/publication/cleanup failures
use storage_corrupt and source/path text never enters errors. This is sequential
immutable publication, with no claim of concurrent-writer safety. Files remain
local and must not be logged or committed.

`artifact_hash(reference: str) -> str` accepts only the exact digest filename,
revalidates the complete entry and hashes the artifact bytes. `coding_key` includes
`coding_schema=1`, `coding_version="deductive-coding/1"`, the complete request and
identity. `raw_reply_hash` binds reply, refusal_reason and input_tokens. A
structurally valid changed request or identity yields a cache miss; the subsequent
classification boundary must independently compare current sources, policy and
generated closed schema before dispatch/publication. Evidence still passes
current deterministic gates at every consuming boundary. A cached response/count
does not establish evidence quality, thematic support or acceptance. Stage 11
owns production model selection, calibration and future fresh-call bypass.

### `CodingPolicySnapshot`

Hash-only manifest policy. Unlike the transient CodingPolicy, this snapshot
contains no source-bearing prompt text. Its hash binds the same generation
parameters and provisional two-attempt validation ceiling.

| Field | Type | Meaning |
| --- | --- | --- |
| `coding_version` | deductive-coding/1 | Literal coding version |
| `prompt_hash` | SHA-256 | Hash of the caller-supplied local prompt |
| `parameters` | Parameters | Exact generation settings |
| `max_attempts` | strict literal 2 | Provisional validation retry ceiling |

### `ClassificationRecord`

One requested document-qualified claim per coding run. Completed means a usable
closed proposal reply, including a valid empty reply. It establishes neither
thematic support nor acceptance. Refused source inputs have no attempts or
semantic rows; incomplete classifications never become novelty.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | strict literal 1 | Separate coding schema |
| `classification_id` | nonblank string | classification- plus digest of coding_run_id, doc_id, claim_id and input_hash |
| `coding_run_id` | nonblank string | Caller-selected coding run identity |
| `doc_id` | nonblank string | Immutable canonical document identity |
| `claim_id` | nonblank string | Original document-qualified claim identity |
| `input_hash` | SHA-256 | Resolved CodingInput digest, or explicitly refused-only provenance fingerprint |
| `codebook` | CodebookReference | Exact frozen ID/version/content hash |
| `status` | completed, refused, incomplete | Classification processing outcome |
| `reason` | closed fixed reason or null | Null exactly for completed; no source or model wording |
| `attempt_ids` | tuple[nonblank string, …] | At most two distinct attempts in ordinal order; empty for refused |
| `theme_ids` | tuple[nonblank string, …] | Sorted distinct explicit proposals; empty for refused/incomplete |

For a preflight source refusal only, input_hash is
`digest({"kind": "refused-coding-input/1", "coding_version": CODING_VERSION,
"source_run_hash": source_run_hash, "doc_id": doc_id, "claim_id": claim_id,
"codebook": reference.model_dump(mode="json")})`. This identifies an unresolved
boundary; it is never presented as verified evidence. The source-run hash is
`digest({"record": source_run_record JSON, "provenance_hash": provenance_hash})`,
matching the Stage 8 source binding. The source run retains extractor identity,
configuration and document processing outcomes.

### `CodingAttempt`

One complete transmitted request or visible blocked attempt, preserving bounded
ordinal order. Actual usage is retained even for unusable/refused replies. Cached
actual counts describe the earlier operation and charge no new allowance.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | strict literal 1 | Separate coding schema |
| `attempt_id` | nonblank string | Classification ID plus literal -attempt-1 or -attempt-2 |
| `classification_id` | nonblank string | Owning classification |
| `doc_id` | nonblank string | Original canonical document identity |
| `claim_id` | nonblank string | Original document-qualified claim identity |
| `attempt` | strict literal 1 or 2 | Validation attempt ordinal |
| `request_hash` | SHA-256 | Digest of the full transmitted messages/schema/parameters/subject |
| `prompt_hash` | SHA-256 | Base prompt content hash |
| `schema_hash` | SHA-256 | Exact generated closed CodingReply schema hash |
| `input_hash` | SHA-256 | Complete current CodingInput digest |
| `input_tokens` | strict int ≥ 0 | Counted full request including schema/template; retained on cache hits; zero on replay miss |
| `reserved_tokens` | strict int ≥ 0 | Counted input plus configured maximum output for a fresh dispatch; zero on blocked/cache attempts |
| `actual_prompt_tokens` | strict int ≥ 0 or null | Transport-reported prompt usage; unknown remains null |
| `actual_completion_tokens` | strict int ≥ 0 or null | Transport-reported completion usage; unknown remains null |
| `unreported` | bool | True for a dispatched/cached operation lacking actual usage |
| `cached` | bool | Raw local response reuse, with zero new reservation |
| `latency_ms` | strict int ≥ 0 | Original transport latency; zero when no reply exists |
| `raw_ref` | confined digest.json or null | Separate local cache reference; no paths or raw wording |
| `raw_hash` | SHA-256 or null | Raw reply/refusal/input-count digest, distinct from artifact byte hash |
| `reason` | closed fixed reason or null | Attempt failure, null for a usable closed reply |

### `ProposalRunRecord`

Pre-assessment coding manifest, distinct from extraction and support manifests.
Prompt text, requests and replies stay in the separate local cache. No support
manifest, acceptance policy, decisions or assignments exist at this boundary.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | strict literal 1 | Separate coding schema |
| `run_id` | nonblank string | Caller-selected coding-run ID |
| `started_at` | aware UTC datetime | Caller-supplied zero-offset run time |
| `source_run_id` | nonblank string | Explicit source extraction-run identity |
| `source_run_hash` | SHA-256 | Source extraction manifest plus provenance hash |
| `documents` | sorted tuple[(doc_id, SHA-256), …] | Complete source-run document/canonical-hash mapping |
| `codebook` | CodebookReference | Frozen codebook ID/version/content hash |
| `classifier_identity` | JudgeIdentity | Explicit family/runtime/hosting/license and input/output limits |
| `coding_policy` | CodingPolicySnapshot | Hash-only prompt/generation/version/retry policy |
| `ceilings` | CodingCeilings | Explicit shared request/token ceilings |
| `cache_mode` | live, replay | Explicit raw-cache operation mode; no fresh-call bypass |
| `configuration_hash` | SHA-256 | Exact configuration recipe described below |
| `requested_claim_order` | tuple[(doc_id, claim_id), …] | Distinct caller-requested order, including refused/incomplete claims |
| `schema_hash` | SHA-256 | Exact generated closed CodingReply schema |
| `coding_version` | deductive-coding/1 | Literal coding implementation/policy version |
| `validator_version` | nonblank string | Current deterministic exactness verifier version |
| `software` | sorted tuple[(nonblank name, nonblank value), …] | Caller-supplied software identity with lowercase 64-hex lock_hash |
| `counts_by_status` | sorted tuple[(classification status, strict int ≥ 0), …] | Requested classifications by final processing status |
| `counts_by_reason` | sorted tuple[(closed fixed reason, strict int ≥ 0), …] | Final classification reasons; no invented no-theme reason on incomplete |
| `requests` | strict int ≥ 0 | Fresh reservations including retries; excludes cache hits |
| `prompt_tokens` | strict int ≥ 0 | Sum of known actual fresh prompt usage; unreported counts remain explicit |
| `completion_tokens` | strict int ≥ 0 | Sum of known actual fresh completion usage |
| `reserved_tokens` | strict int ≥ 0 | Sum of original fresh full input/output reservations |
| `charged_tokens` | strict int ≥ 0 | Reconciled actual usage plus intact reservations for unknown usage; overspend is not clamped |
| `unreported` | strict int ≥ 0 | Fresh dispatched operations with unknown actual usage |
| `cache_hits` | strict int ≥ 0 | Reused raw attempts, including cached transport refusals |
| `latency_ms` | strict int ≥ 0 | Sum of fresh original transport latency |
| `billable_cost` | none, self-hosted | Literal; no hosted inference in the required path |
| `artifact_hashes` | sorted tuple[(raw/digest.json, SHA-256), …] | Validated external raw-cache artifact byte hashes; table hashes arrive at storage |

The configuration hash digests source_run_id, source_run_hash, documents,
codebook reference JSON, classifier_identity JSON, coding_policy snapshot JSON,
ceilings JSON, requested_claim_order, schema_hash, coding_version,
validator_version and the explicit cache_mode. Run time and run ID are operational
metadata, outside this configuration digest; software/lock identity is retained
separately. Cache mode may change the configuration hash between live and replay,
while reconstructed proposals keep the same coding-run/input identity.

`CodingAllowance(ceilings, *, run_id)` shares strict nonnegative claim/document/run
request counts and document/run charged token totals. reserve checks request
ceilings before token ceilings and dispatch; reconcile adds actual minus reserved
usage, without clamping truthful overspend. Unknown usage retains the full
reservation and increments unreported. Cache hits spend no allowance.

`classify_claim(input, classifier, policy, allowance, *, cache) -> ClassificationResult`
returns a frozen transient container for record, attempts, proposals, optional
attribute and optional novelty. It validates complete generated/transmitted
request correspondence with current source, prompt, schema, parameters, subject
and runtime before dispatch, after cache reuse/callbacks and before publication.
Only malformed_reply, invalid_references, hierarchy_conflict, tool_call_refused,
model_mismatch and transport_error retry, at most twice. Feedback is one bounded
fixed-reason message appended to the original request. A valid empty proposal is
final and enters pointer-only novelty; corruption and unexpected errors abort
publication with fixed reasons and keep prior raw/accounting local.

`propose_run(run_id, sources, claim_order, classifier, policy, ceilings, *, cache,
started_at, software) -> ProposalRun` preflights run metadata and every requested
claim before any dispatch, then preserves caller order with one shared allowance.
ProposalRun is a frozen transient container for record, classifications, attempts,
proposals, attributes and novelty; its targets property returns explicit valid
Stage 8 targets. All original quote links remain source-owned. Final publication
reconstructs request hashes and raw bindings and repeats current evidence gates.
The runner performs no support inference, acceptance decision, command discovery
or processing-state write.

### `AssignmentDecision`

One row per explicit proposal target, separate from the raw support processing
outcome. An `assessed` outcome without an externally bound policy is
`review/calibration_required`. Refused, incomplete and flagged assessments bypass
policy evaluation and retain their flags and missing reasons. Missing target
assessments are visible `review/missing_assessment`, with null support status;
they never enter novelty. Fixture-policy accepted rows retain fixture provenance
and require explicit fixture scope at downstream production consumption.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | strict literal 1 | Separate coding schema |
| `coding_run_id` | nonblank string | Original proposal-run identity |
| `decision_id` | nonblank string | Content-derived decision identity; recipe below is revalidated |
| `doc_id` | nonblank string | Original immutable document identity, qualifying claim and quote IDs |
| `claim_id` | nonblank string | Unchanged original claim identifier |
| `theme_id` | nonblank string | Explicit proposed frozen theme identifier |
| `codebook` | CodebookReference | Frozen codebook ID/version/content hash |
| `target_id` | nonblank string | Matching stored Stage 8 target identity; currently resolved identity when assessment is missing |
| `support_run_hash` | SHA-256 | Exact support-run manifest digest, including published table and external raw artifact hashes |
| `support_status` | ReviewStatus or null | Raw refused/incomplete/flagged/assessed processing result; null for missing assessment |
| `flags` | sorted distinct tuple[nonblank string, …] | Raw support semantic flags, never votes or numeric cutoffs |
| `missing` | sorted distinct tuple[fixed reason, …] | Raw unavailable-signal/refusal reasons, or missing_assessment |
| `status` | accepted, rejected, review, refused | Separate assignment-policy decision |
| `reason` | fixed reason | policy_accept/reject/review, calibration_required, assessment_refused/incomplete/flagged, or missing_assessment; checked against statuses |
| `policy` | PolicyReference or null | Exact external policy provenance, null for no-policy decisions |
| `supporting_quote_ids` | sorted distinct tuple[nonblank string, …] | Nonempty original eligible document-scoped quote IDs only for accepted decisions; otherwise empty |
| `proposal_hash` | SHA-256 | Complete proposal-run content digest described below |
| `input_hash` | SHA-256 | Original complete CodingInput hash, re-resolved at consumption |

`DecisionInput` is a frozen dataclass with disabled transient repr and fields
`target: TargetRecord`, `evidence: tuple[EvidenceReference, ...]`,
`entailment: tuple[EntailmentSignal, ...]`, `trials: tuple[JudgeTrial, ...]`,
`outcome: ReviewOutcome`, and `eligible_quote_ids: tuple[str, ...]`. It retains
all original evidence and raw per-quote/joint/family/presentation views. The
eligible set includes a quote only when all four complete independent trials
label it `supporting`. This is an eligibility restriction, never sufficient
acceptance; contextual companions remain raw provenance.

`AssignmentPolicy.reference: PolicyReference` and
`evaluate(view: DecisionInput) -> PolicyVote` form a pure deterministic external
policy seam. No accepting implementation is shipped in the package. Tests supply
an explicit fixture-only policy. Calibrated references require an artifact hash,
but this declaration is not independent evidence of calibration or approval;
Stage 11 must produce and approve that artifact and its production configuration.
Stage 9 loads no labels, sets no cutoff, pools no score and approves no model.

`decide_assignments(proposals: ProposalRun, support: StoredSupportRun,
sources: SupportSources, policy: AssignmentPolicy | None) -> DecisionSet` first
calls public `reverify_support_run` for complete support graph/accounting and
current evidence/theme/context hashes, then recomputes proposed inputs through
public `resolve_coding_input`. Full frozen Target identities must match exactly;
unknown extra or duplicate assessments refuse. Raw outcomes are independently
derived by Stage 8's stored validation. The policy codebook and both configuration
hashes are rebound before evaluation. After reference-property access and policy
callbacks, the gate checks the complete proposal and support contents, raw view,
reference and current source resolution again. External exceptions render only
`unexpected_error`, with suppressed causes. Policies cannot alter evidence,
claims, themes or safety outcomes.

`DecisionSet` is a frozen dataclass with disabled transient repr and fields
`decisions`, `proposals`, `support`, `sources`, `policy`, `proposal_hash`,
`support_run_hash`, and `source_run_hash`. The retained ProposalRun,
StoredSupportRun and SupportSources preserve all original raw signals and
source/codebook/context provenance; hashes are common bindings across decisions.
These transient references require reverification at downstream consumption.

All digests use core's SHA-256 over UTF-8 canonical JSON. The exact recipes are:

- `proposal_run_hash(proposals)`: digest of `record` JSON and ordered JSON arrays
  `classifications`, `attempts`, `proposals`, `attributes`, and `novelty`.
- `support_run_hash(support)`: digest of `support.record` JSON. Its artifact hashes
  bind published Parquet and external raw cache bytes. This seam does not reread
  those external bytes; the Stage 8 reader already validates published tables.
- `source_run_hash`: the inherited digest of extraction `record` JSON and
  `provenance_hash`, required to agree across proposal and support manifests.
- `decision_id`: `"decision-" + digest({"target_id": target_id,
  "proposal_hash": proposal_hash, "support_run_hash": support_run_hash,
  "policy": policy_reference_json_or_null})`.

The decision module writes no state or files and runs no classifier, scorer,
judge or inference callback. Its saved policy provenance is consumed by the
assignment projection below. Coverage/state/export belong to Stage 10,
calibration/thresholds and fresh-call stability to Stage 11.

### `Assignment`

One accepted quote–theme association at document-qualified grain
`(coding_run_id, codebook_id, codebook_version, doc_id, theme_id, quote_id)`.
Multiple themes share the original quote ID; multiple supporting claims link
to this row through `AssignmentClaimLink`. There is no copied quote text or
implicit parent/family roll-up. Boilerplate mask IDs remain audit references.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | strict literal 1 | Separate coding schema |
| `assignment_id` | nonblank string | `"assignment-" + digest(assignment_key)`, using the grain tuple above |
| `coding_run_id` | nonblank string | Original proposal-run identity |
| `doc_id` | nonblank string | Immutable document identity qualifying the original quote ID |
| `quote_id` | nonblank string | Unchanged original document-scoped quote identifier |
| `theme_id` | nonblank string | Explicit frozen theme identifier, including a subtheme when proposed |
| `codebook` | CodebookReference | Frozen codebook identifier, version and content hash |
| `canonical_hash` | SHA-256 | Saved canonical hash from the matching Stage 8 EvidenceReference |
| `start` | strict nonnegative integer | Saved zero-based Python character start offset |
| `end` | strict positive integer | Saved half-open end offset; greater than start |
| `validator_version` | nonblank string | Saved evidence verifier version, rebound at current evidence consumption |
| `mask_ids` | distinct tuple[nonblank string, …] | Saved overlay-mask identities; never a headline filter at this stage |
| `support_run_hash` | SHA-256 | Matching support-run manifest digest |
| `policy_hash` | SHA-256 | Exact retained common external policy hash |
| `policy_kind` | fixture or calibrated | Scope provenance; fixture rows refuse default production frame selection |

### `AssignmentClaimLink`

One supporting source claim/decision link to an assignment. Links deduplicate at
`(assignment_id, doc_id, claim_id, decision_id)` and keep contradictory claim
interpretations and their separate AttributeRecords reachable.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | strict literal 1 | Separate coding schema |
| `assignment_id` | nonblank string | Projected quote–theme row identity |
| `doc_id` | nonblank string | Original document identity qualifying the claim |
| `claim_id` | nonblank string | Unchanged original source claim identifier |
| `decision_id` | nonblank string | Accepted saved assignment decision identity |
| `target_id` | nonblank string | Matching Stage 8 target identity |

`project_assignments(decisions: DecisionSet, support: StoredSupportRun) ->
tuple[tuple[Assignment, ...], tuple[AssignmentClaimLink, ...]]` validates strict
transient containers, the matching retained support run, common proposal/support/
source hashes, and the frozen policy codebook and classifier/support configuration
references. Public `reverify_support_run` checks the complete stored support graph
and current canonical evidence. Public `resolve_coding_input` rebinds all proposed
claim/theme inputs. Each saved decision must correspond uniquely to one proposal
and the actual support outcome, flags and missing reasons. Accepted references
must be nonempty and remain eligible under public `eligible_quote_ids`; contextual,
irrelevant, contradicting or uncertain quotes cannot be promoted. The matching
`(target_id, doc_id, quote_id)` EvidenceReference supplies the unchanged span,
hash, masks and verifier version. Rows and links are sorted for stable output;
conflicting rows at the same assignment key refuse with `invalid_references`.

These are structural provenance and current evidence/safety checks. Projection
does not call or manufacture an accepting policy, reproduce an external policy's
vote, or establish that a declared calibrated artifact is approved. Full decision
recomputation with the actual external pure policy belongs to the coding store
consuming gate. Empty projection preserves its original decision audit and does
not establish no themes or a perfect exactness rate.

`assignment_frame(rows: Sequence[Assignment], *, scope="production") ->
pl.DataFrame` reparses rows, refuses mixed `(codebook_id, codebook_version,
content_hash)` with `mixed_codebook`, and requires calibrated rows for production
or exclusively fixture rows for fixture scope. Invalid/mixed scopes refuse with
`fixture_policy`; duplicate assignment keys or IDs refuse with
`invalid_references`. Its explicit `ASSIGNMENT_SCHEMA` has exactly the Assignment
fields: integer fields use Polars Int64, strings use String, masks use List(String),
and codebook uses a Struct of ID/version/hash with Int64 version. Empty sequences
keep this same schema. Nonsequences and unrepresentable frame values refuse with
fixed `malformed_record`, without a pandas intermediary or input-bearing errors.
Frame construction validates supplied records and scope; it does not replace the
source-aware projection or downstream consuming gate.

### `CodingRunRecord`

Immutable coding-publication manifest, distinct from the original proposal and
support manifests. The eight explicit analytical tables are `classifications`,
`attempts`, `proposals`, `attributes`, `decisions`, `assignments`,
`assignment_claims`, and `novelty`, each published as its named Parquet file.
Each schema has exactly its row-model fields with explicit Int64, Boolean,
String, list and named struct dtypes, including nullable and empty tables.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | strict literal 1 | Separate coding schema |
| `run_id` | nonblank string | Original caller-selected coding-run ID |
| `started_at` | aware UTC datetime | Original zero-offset run time |
| `source_run_id` | nonblank string | Bound extraction-run identity |
| `source_run_hash` | SHA-256 | Extraction manifest JSON plus source provenance hash |
| `documents` | sorted tuple[(doc_id, SHA-256), …] | Complete original source-run document/canonical-hash mapping |
| `codebook` | CodebookReference | Frozen codebook ID/version/content hash |
| `classifier_identity` | JudgeIdentity | Original classifier family/runtime/hosting/license and limits |
| `coding_policy` | CodingPolicySnapshot | Hash-only coding prompt/parameters/version/retry snapshot |
| `ceilings` | CodingCeilings | Original explicit shared request/token ceilings |
| `cache_mode` | live, replay | Original cache operation, including empty/refused runs |
| `configuration_hash` | SHA-256 | Unchanged Task 5 coding configuration hash |
| `requested_claim_order` | tuple[(doc_id, claim_id), …] | Original distinct requested order, including refused/incomplete claims |
| `schema_hash` | SHA-256 | Exact closed generated CodingReply schema hash |
| `coding_version` | deductive-coding/1 | Literal coding implementation version |
| `validator_version` | nonblank string | Current deterministic exactness verifier version |
| `software` | sorted tuple[(name, value), …] | Original software identity including SHA-256 lock_hash |
| `counts_by_status` | sorted tuple[(classification status, strict int ≥ 0), …] | Recomputed final classification counts |
| `counts_by_reason` | sorted tuple[(closed fixed reason, strict int ≥ 0), …] | Recomputed final classification reason counts |
| `requests` | strict int ≥ 0 | Fresh dispatch reservations, excluding cache hits |
| `prompt_tokens` | strict int ≥ 0 | Known actual fresh prompt tokens |
| `completion_tokens` | strict int ≥ 0 | Known actual fresh completion tokens |
| `reserved_tokens` | strict int ≥ 0 | Original fresh input/output reservations |
| `charged_tokens` | strict int ≥ 0 | Actual known usage plus preserved unknown-usage reservations |
| `unreported` | strict int ≥ 0 | Fresh operations whose actual usage remains unknown |
| `cache_hits` | strict int ≥ 0 | Reused raw attempts; historical usage creates no new charge |
| `latency_ms` | strict int ≥ 0 | Original fresh transport latency total |
| `billable_cost` | none, self-hosted | Literal required-path cost provenance |
| `artifact_hashes` | sorted tuple[(confined filename, SHA-256), …] | Exact eight published table-byte hashes plus external raw/digest.json bindings |
| `proposal_hash` | SHA-256 | Original ProposalRunRecord plus ordered five proposal row arrays |
| `support_run_id` | nonblank string | Consumed support-run identity, checked against supplied support at consumption |
| `support_run_hash` | SHA-256 | Complete published support manifest JSON hash |
| `support_configuration_hash` | SHA-256 | Consumed support configuration, checked at consumption and against policy |
| `policy` | PolicyReference or null | Explicit acceptance-policy/configuration/calibration reference; null requires review |
| `counts_by_decision` | sorted tuple[(accepted/rejected/review/refused, strict int ≥ 0), …] | Recomputed decision status counts |
| `counts_by_decision_reason` | sorted tuple[(closed fixed reason, strict int ≥ 0), …] | Recomputed decision reason counts |

`CodingRun` is a frozen, non-rendering dataclass containing `record` and those
eight row tuples. The original `ProposalRunRecord` is reconstructed using exactly
its original field registry, with `artifact_hashes` restricted to the exact
allowed `raw/<ref>` subset. Its original metadata/configuration/counts are
preserved. `proposal_run_hash` then binds that reconstructed manifest plus the
ordered classifications, attempts, proposals, attributes and novelty JSON arrays;
publication's new table hashes never replace the original proposal identity.
The unchanged configuration recipe is documented under `ProposalRunRecord`.

`write_coding_run(directory: Path, result: CodingRun, sources: SupportSources,
support: StoredSupportRun, policy: AssignmentPolicy | None) -> Path` validates
structure and repeats current evidence/policy checks before any output I/O. It
publishes through a unique sibling and rename, cleans failed partials and refuses
an existing destination with fixed `coding_destination_exists`. Other public
read/write errors use fixed `storage_corrupt`. Sequential publication does not
claim coordinated concurrent-writer safety; Stage 15 owns that work.

`read_coding_run(directory: Path) -> CodingRun` reads only `run.json` and those
eight named files, rejects symlinks, verifies table byte hashes, exact schemas,
closed JSON-mode records, row relationships, original proposal identity and
dispatch/reservation accounting. It checks complete raw-reference/hash bindings
without opening external raw-cache bytes. Those bindings are provenance, not a
claim of external byte verification. Structural reading does not verify current
source text, masks, support identity or policy approval.

`reverify_coding_run(stored: CodingRun, sources: SupportSources,
support: StoredSupportRun, policy: AssignmentPolicy | None) -> DecisionSet`
repeats the public support and full coding-input evidence gates, including
unmatched/incomplete/refused classifications. Refused-only fingerprints must
repeat the same unresolved reason; repairing their evidence refuses the saved
boundary. It repeats frozen IDs/hierarchy and pointer-only novelty bindings,
checks the supplied support and policy configuration, and calls the actual pure
`decide_assignments` with the supplied policy. It compares decisions and Task 7
assignment/link projection in canonical JSON bytes and repeats all requested
input gates after external policy callbacks. Changed/absent policy visibly
refuses a saved accepting run. No inference, cache loading or reclassification
occurs. Stage 11 still owns calibration, production policy approval and quality.
