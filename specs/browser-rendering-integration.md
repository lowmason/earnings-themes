# Browser rendering integration across Stages 2, 3, and 10

Status: Proposed for written-spec review

Approved design direction: 2026-09-24

## Purpose

Integrate browser-rendered capture and an optional DOM/layout-aware extractor
without changing the Stage 1 parser-fidelity experiment, introducing a second
evidence coordinate system, or making browser automation a required dependency
of the core or themes packages.

The integration is limited to three roadmap stages:

- Stage 2 defines browser-neutral evidence and artifact contracts.
- Stage 3 owns browser capture, DOM/layout extraction, fidelity evaluation, and
  any later promotion of browser-derived structure into canonicalization.
- Stage 10 consumes immutable Stage 3 artifacts to build and test cited evidence
  views. It does not re-extract evidence from source HTML.

Stage 1 remains unchanged. Its frozen gold, parser decision, fixtures, and
residual failures are inputs to Stage 3, not artifacts that browser extraction
may revise.

## Decisions

| ID | Decision |
| --- | --- |
| B1 | Browser automation is implemented once, behind a public Stage 3 ingestion interface. Stage 2 and Stage 10 do not contain independent Selenium logic. |
| B2 | `earnings-core` defines only browser-neutral contracts. Browser engine, viewport, layout, and screenshot fields belong to `earnings-ingestion`. |
| B3 | Selenium is the preferred first Stage 3 driver adapter, isolated behind an optional `browser-capture` dependency extra. The Stage 3 plan pins the then-current verified Selenium, browser, and driver artifacts rather than relying on an unreviewed global installation. |
| B4 | Browser capture starts as a diagnostic and fidelity-checking path. DOM/layout-derived structure is not production canonical structure until a separate Stage 3 decision record promotes a fixed policy after evaluation against frozen Stage 1 gold. |
| B5 | A `CanonicalDocument` is the sole evidence coordinate system. Browser-derived elements must map exactly to its code-point, half-open spans or be rejected with an explicit alignment failure. |
| B6 | Stage 10 renders evidence from canonical text and verified spans. It never verifies a quote by re-parsing raw HTML, OCR, a screenshot, or browser-selected text. |
| B7 | Source documents are untrusted. Capture runs with document JavaScript disabled, outbound requests blocked, no broad local-file permission, and a fresh isolated profile. An attempted external request is recorded and blocked. |
| B8 | Runtime capture is offline. Browser or driver installation is a separately controlled setup action; Selenium Manager or another downloader must not fetch binaries during a document-processing run. |
| B9 | A capture-only browser or policy change creates a new capture, not a new canonical document. Once browser output is part of an adopted canonicalization policy, a browser, capture-policy, normalization, or layout-extraction change that changes canonical text or spans creates a new canonicalization version. Existing documents and spans are never mutated in place. |

## Ownership and dependency direction

### Stage 2: core evidence spine

Stage 2 defines the contracts used by every later parser and viewer:

- `TextSpan`, with zero-based Python string indices and half-open `[start, end)`
  semantics;
- `CanonicalDocument`, including immutable canonical text or an artifact
  reference, canonical hash, schema version, and canonicalization version;
- `DocumentElement`, including a stable element identifier, type, document span,
  optional parent identifier, and typed table context where applicable;
- a generic `ArtifactRef`, including content hash, media type, storage reference,
  schema version, and rights/access status;
- exactness and attribution validators that resolve elements and quotes against
  one `CanonicalDocument`.

Stage 2 contains no Selenium import, browser executable configuration, DOM
traversal, screenshot model, or browser-specific persisted schema. It supplies
the seam that lets the selected Stage 1 parser and the Stage 3 browser extractor
emit comparable elements.

### Stage 3: structure-aware canonicalization

Stage 3 owns these public ingestion abstractions:

```text
BrowserRenderer.capture(saved_html, capture_policy) -> RenderedCapture
LayoutExtractor.extract(rendered_capture) -> candidate DocumentElements
```

The initial Selenium adapter implements `BrowserRenderer` behind the optional
`earnings-ingestion[browser-capture]` extra. The deterministic canonicalizer
continues to accept saved bytes and metadata rather than a network client.
Default package imports and offline tests do not require Selenium or a browser.

`RenderedCapture` is browser-specific ingestion provenance, not a core evidence
record. It contains or references:

- a stable capture identifier;
- source-document identifier and raw-content SHA-256;
- capture-policy name and version;
- browser engine, full browser version, driver version, and Selenium version;
- operating system, architecture, viewport, device scale, locale, timezone, and
  controlled font-set identity;
- reported document character set;
- script, network, image, and missing-resource policies;
- rendered text plus its hash;
- layout metadata plus its hash;
- zero or more screenshot artifact references;
- UTC capture time, duration, status, and explicit failure or partial reason.

Generated capture artifacts remain under `data/runs/` unless a later rights
review explicitly permits a small sanitized fixture in Git. Writes are atomic,
and an existing capture is never overwritten. A new run either reuses an exact
cache key or writes a new capture.

The cache key includes at least the raw-content hash, capture-policy version,
browser and driver identities, platform/render configuration, and extractor
version. Operational timestamps do not affect deterministic identity.

### Stage 10: cited export

Stage 10 receives canonical documents, verified quote spans, and artifact
references through the application layer. It generates a safe static evidence
view by escaping canonical content and inserting highlights from verified
`[start, end)` spans.

The Stage 10 application may call the public Stage 3 `BrowserRenderer` to test
the generated view in target browsers and create a screenshot fallback. It does
not import Stage 3 internals, run the layout extractor, or create a second
canonical document. `earnings-themes` continues to depend only on
`earnings-core`; the application composes ingestion artifacts with theme output.

The source-rendered capture and cited evidence view remain distinct:

| Artifact | Establishes | Does not establish |
| --- | --- | --- |
| Stage 3 source-rendered capture | What the controlled browser displayed for a saved source under a recorded policy | Quote exactness, thematic support, or a new canonical span |
| Stage 10 cited evidence view | How an already-verified canonical span is presented to a researcher | That re-rendered text can replace the canonical source |

## Stage 3 data flow

```text
immutable saved HTML
    |-- selected Stage 1 parser -----------|
    |-- isolated browser capture ----------|--> fidelity evaluation
    `-- DOM/layout extractor candidate ----|          |
                                                       v
                                            decision record, if promotion
                                                       |
                                                       v
                                  versioned CanonicalDocument + elements
```

The browser capture is an independent observation used by the R3.5 fidelity
check. It does not automatically become canonical text. The selected parser
remains the initial canonicalization path chosen by Stage 1.

The DOM/layout extractor may use rendered visibility, computed display, element
geometry, table-cell position, and reader-visible order. It emits candidate
`DocumentElement` records conforming to the Stage 2 contract. HTML tag names or
DOM ancestry may be retained as provenance, but Stage 3 evaluation must report
whether those signals improve reader-visible structure rather than assume they
do.

Every candidate element must map to an exact canonical span. Mapping may use a
deterministic, reversible normalization map constructed during canonicalization.
It may not silently choose the first occurrence of duplicated text, use a fuzzy
score as proof, or synthesize a contiguous quotation from separate cells. A
missing or ambiguous mapping produces `alignment_failed` and remains visible in
the fidelity report.

## Diagnostic-first promotion rule

Stage 3 evaluates the DOM/layout extractor only after Stage 1 is complete. The
evaluation uses the frozen Stage 1 fixtures and gold without changing the Stage
1 V2 record, candidate set, scorer semantics, or parser ADR.

Before running the comparison, the Stage 3 design fixes:

- the extractor and browser versions;
- the capture and mapping policies;
- the residual failure classes it is intended to repair;
- metrics and non-regression conditions;
- the deterministic activation rule for any proposed fallback.

The comparison reports the selected parser and browser candidate separately on
the same gold: block coverage, reading order, heading loss, footnote merging,
table-header retention, cell association, altered anchors, and alignment
failures. It also reports results by the four Stage 1 fixture classes.

Browser-derived structure remains diagnostic unless a Stage 3 decision record
shows that it repairs named residual failures under the predeclared rule without
violating the Stage 2 element/span invariants. Promotion selects one of these
explicit outcomes:

1. diagnostic-only capture;
2. a deterministic fallback activated by recorded parser or source conditions;
3. a new primary canonicalization policy and version.

There is no per-document manual selection and no silent reconciliation of two
element streams. Outcome 3 requires recanonicalization under a new version and
cannot rewrite prior document versions.

## Rendered-text calibration

The first capture method evaluated is `document.body.innerText`, because the
intended observation is reader-visible text rather than raw `textContent` or
WebDriver's separately normalized element text. This choice is not accepted by
assumption.

Stage 3 compares the automated capture with the existing manually copied
`*.rendered.txt` observations for at least:

- a narrative-only release;
- a conventional table-bearing release;
- a complex or malformed-layout release.

The report classifies differences in visible characters, whitespace, bullets,
CSS text transformation, hidden content, image alternative text, table-cell
separation, and reading order. Manual copied text remains a calibration
observation, not gold structure. Flat text cannot establish visual table
geometry, so screenshots and the existing human-marked table gold remain
necessary for that evaluation.

## Security and isolation

The browser process handles each saved filing as untrusted data:

- use a new temporary profile with no user cookies, credentials, extensions,
  clipboard access, or persisted session state;
- disable document JavaScript before navigation;
- block HTTP, HTTPS, and other external requests before loading the saved file;
- do not grant the document access to arbitrary local files;
- load only the explicitly resolved saved artifact;
- bound startup, navigation, capture, and shutdown times;
- terminate the browser after each bounded batch and always clean up processes;
- record blocked requests, missing resources, browser crashes, and timeouts;
- never treat an error page or partial load as a successful empty document.

A source whose meaningful rendering depends on blocked external resources is
`partial`, with the missing resources recorded. Policy does not permit fetching
those resources during capture merely to make the page look complete.

## Reproducibility and failure handling

Repeated capture in the same pinned environment must produce the same rendered
text hash. Layout metadata must be stable under the fields used for extraction.
Screenshots are content-hashed for provenance but are not required to be
byte-identical across unsupported platforms; production use of geometry requires
the pinned platform and font set.

At minimum, capture distinguishes `completed`, `partial`, `failed`, and
`unavailable`. Reasons include browser unavailable, startup failure, timeout,
blocked required resource, document load failure, capture failure, and layout
alignment failure. A failed optional diagnostic capture does not turn a
successfully parsed document into an empty document. If a promoted
canonicalization policy requires browser output, its failure makes that
canonicalization attempt fail explicitly rather than silently falling back to a
different policy under the same version.

Default tests use saved, permitted capture artifacts or fake renderer adapters.
They make no network request, install no browser, and modify no global browser
profile. Browser integration checks are opt-in and record the exact environment.

## Verification by stage

### Stage 2

- Unit tests enforce span bounds, canonical hashes, stable element identifiers,
  parent references, table context, and artifact hashes.
- Contract tests show two different parser implementations can emit the same
  browser-neutral element schema.
- No core or themes import resolves Selenium or a browser package.

### Stage 3

- Every Stage 1 fixture canonicalizes offline through the selected parser.
- Automated rendered-text calibration covers the three named fixture categories
  and publishes classified differences without altering gold.
- A network guard proves document capture makes no external request and source
  JavaScript cannot execute.
- Two captures in the pinned environment have the same rendered-text hash.
- DOM/layout candidate elements either resolve to exact canonical spans or carry
  an explicit alignment failure.
- The diagnostic comparison uses frozen Stage 1 gold and records every named
  metric and residual failure class.
- Any promotion decision names its fixed activation policy, versions, measured
  benefit, regressions, and canonicalization-version consequence.

### Stage 10

- A verified span highlights exactly the corresponding canonical substring.
- Duplicated text highlights the specified occurrence, not the first matching
  string.
- Source content containing scripts or markup renders inert in the evidence
  view.
- The evidence view works from a saved `CanonicalDocument` when source capture,
  Selenium, and network access are unavailable.
- Target-browser checks record highlight, page-top degradation, or failure, and
  a permitted immutable snapshot renders the span when the source link fails.
- Rights/access status controls whether source-rendered or screenshot artifacts
  may be retained or exported.

## Non-goals

- No change to Stage 1 gold, its frozen candidate set, or its parser selection
  rule.
- No Selenium dependency in `earnings-core` or `earnings-themes`.
- No browser requirement for ordinary quote extraction, verification, or theme
  coding from saved canonical documents.
- No claim that DOM tags equal reader-visible semantics.
- No use of screenshots or OCR as exact-quote authority.
- No runtime retrieval of scripts, stylesheets, images, browser binaries, or
  drivers while processing a saved filing.
- No second canonical coordinate system in Stage 10.

## Roadmap handoff

When Stage 2 is planned, include only the browser-neutral contracts and tests in
this spec. When Stage 3 is brainstormed, use this spec to design the renderer,
capture schema, calibration experiment, layout extractor, and diagnostic-first
promotion decision. When Stage 10 is planned, reuse the public renderer and
artifact references while deriving every highlight from canonical spans.

This design does not itself complete or amend the status of any roadmap stage.
Implementation remains deferred to the corresponding stage plans.
