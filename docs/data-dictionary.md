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
| `parse_failed` | lxml raised, or libxml2 logged a fatal error, such as nesting past its depth limit |
| `no_native_text` | Nothing is left after N1; image-only input lands here (R4.3) |
| `invalid_elements` | `validate_elements` found problems: a canonicalizer defect, never the input's |

### `CanonicalizationFailure`

A document the canonicalizer refused. A failure is never an empty document and never
a partial element set; decoding never fails.

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
