# Deep research prompt: firm-document ingestion and evidence-linked theme analysis

## Role and objective

Act as a principal researcher in document intelligence, financial NLP, information retrieval, and reproducible research systems. Conduct a critical, current literature and engineering review that identifies the best-supported methods for a production-quality Python system that:

1. Ingests firms' 8-K reports, earnings releases, and earnings-call transcripts.
2. Extracts specific, decision-useful themes and classifies them consistently.
3. Ranks themes by explicitly defined importance, rather than merely counting mentions.
4. Links every theme and substantive analytical claim to exact supporting quotations and their precise locations in the original documents.

Deliver an evidence-based methods review and an implementable research design, not a generic RAG overview, an agent-framework catalog, or another learning syllabus. Interpret “state of the art” as demonstrated quality on relevant tasks under the project's constraints, not simply the newest model or largest context window.

## Source documents and project constraints

Read both supplied source documents in full:

- `earnings-ingestion.md`: company universe, issuer identity, source selection, free-access constraints, provenance, and entity-level distinctions.
- `earnings-themes.md`: workflow-first extraction, canonical text, exact quotations, typed outputs, codebooks, speaker roles, and evaluation.

Use `AGENTS.md`, when supplied, as additional monorepo context. Distinguish requirements from proposals, learning exercises, unverified software claims, and unresolved choices. Do not assume the proposed repository structure already exists. Begin with a source-to-requirement audit identifying what to retain, revise, test, or defer.

The implementation should use Python, Polars for analytical transformations, explicit schemas, and modular monorepo boundaries. Do not write pandas-based application pipelines; flag any candidate library's pandas dependency or hidden conversions. Preserve `uv`, Ruff, and pytest conventions where applicable.

The required path must use free-to-access, lawfully usable data and open-source software. Do not make paid datasets, subscriptions, trial credits, or billable inference mandatory. Distinguish software license, model-weight license, data-access rights, redistribution permission, and compute cost. An optional hosted-model comparison may establish a quality ceiling, but requires explicit authorization and a budget; this research request does not authorize charges.

Use a configurable company universe. Preserve issuer/security distinctions and point-in-time membership when relevant. Do not divert this review into building a complete subsidiaries, establishments, or employment database. Treat those capabilities as contextual inputs to document analysis. Keep SIC, NAICS, and other industry classifications separate and provenance-bearing.

The core corpus is 8-K main documents, their actual earnings-release exhibits, and permitted earnings-call transcripts. Make the scope of earnings-linked versus other material-event 8-K analysis explicit. Treat 10-Q, 10-K, and foreign-issuer forms as extensions, not silent substitutes for the requested corpus.

## Research protocol

Search through the date this review is executed and state that date. Prioritize recent work, especially from 2023 onward, while retaining older foundational methods and standards where necessary. Read the linked primary sources in the supplied notes, but independently verify current APIs and compatibility claims.

Use original papers, official documentation, maintained repositories, standards, SEC materials, and original issuer documents. Follow citations beyond the seed notes. For each important method, report the task, evaluation data, baselines, metrics, limitations, reproducibility, and relevance to earnings documents. Separate independently evaluated results from authors' own benchmarks, documentation-only capabilities, and untested proposals. Label preprints and vendor claims appropriately.

Do not invent benchmark results, prices, source coverage, or implementation tests. Do not compare headline scores from incompatible datasets as though they establish a winner. When the evidence does not identify a clear winner, specify the experiment needed to decide. Cite material technical claims and provide verified primary-source links.

## 1. Acquisition, document identification, and event alignment

Design source-specific acquisition and discovery methods, with failure handling and coverage measurement.

### 8-K reports and earnings releases

Start with Item 2.02 and the earnings release commonly attached as EX-99.1, but inspect the actual filing, exhibit index, descriptions, links, and content. Do not hard-code “first exhibit,” “every EX-99.1 is an earnings release,” or “every earnings release uses the same exhibit number.”

Explain how to distinguish the main 8-K, substantive item text, exhibit references, actual release, presentation, supplemental tables, and unrelated exhibits. Address multiple releases, alternative exhibit numbering, narrative-only releases, 8-K/A amendments, corrections, and relevant non-earnings items. Test whether library convenience flags detect all relevant releases or only a narrower class, such as successfully parsed financial tables.

Compare direct SEC submissions/index/archive access with suitable open-source adapters, including EdgarTools. Explain historical backfill, incremental discovery, complete accession traversal, request identification, current access limits, caching, retry/backoff, and resumable acquisition. Do not use the latest 8-K indiscriminately when the target is a particular earnings event.

### Earnings-call transcripts

Assess permitted issuer investor-relations sources and genuinely free transcript sources. Provide a source register covering ownership, access method, historical depth, issuer coverage, versioning, licensing, redistribution, and limitations. Do not assume transcripts are routinely available on EDGAR or that a free scraper confers data rights.

Keep prepared remarks, Q&A, operator text, and participant lists distinct. Resolve speaker names, affiliations, and roles, preserving uncertainty. Separate management from analysts, operators, and unknown speakers. Preserve transcript corrections and competing versions. Label any audio-derived transcription as a separate, explicitly scoped fallback, not an original published transcript.

### Event and entity linkage

Define issuer, filing, document, exhibit, document-version, and earnings-event identifiers. Match documents using issuer identity, fiscal period, period end, earnings-event date, and content—not ticker or calendar quarter alone. Distinguish SEC acceptance time, first public availability, call time, fiscal reporting period, and retrieval time. Preserve timestamp precision and unknown values.

Deduplicate copies of the same release on EDGAR, issuer websites, and other permitted sources without losing their provenance. Separate duplicate source copies from genuinely additional disclosures. Prevent amendments and later transcript revisions from leaking into point-in-time analyses.

Maintain expected, unavailable, restricted, acquired, parsed, partial, failed, and completed processing states. Analyze whether missing transcript coverage creates selection bias.

## 2. Faithful parsing and canonical document representation

Compare HTML/DOM-aware, SGML, inline-XBRL-aware, PDF text/layout, and table-extraction approaches relevant to this corpus. Evaluate document-understanding models only where deterministic parsing is insufficient. Prefer native text; reserve OCR for image-only or otherwise unreadable material and explain its additional validation burden.

Specify an immutable raw artifact, a versioned canonical representation, and mappings between them. Preserve headings, paragraphs, lists, tables, footnotes, speaker turns, and section boundaries. Handle entities, Unicode, whitespace, hyphenation, reading order, hidden or repeated content, and malformed markup without silently changing meaning.

Define content hashes, canonicalizer versions, sentence/block IDs, offset units, and half-open span conventions. Specify whether offsets count Unicode code points, bytes, or another unit and how the viewer uses the same convention. Do not let removing boilerplate invalidate stored offsets; retain it in the source representation and use analysis masks where appropriate.

Preserve numeric signs, units, scale, currencies, reporting periods, column headers, and GAAP/non-GAAP distinctions. Do not turn unrelated table cells into a fabricated prose quotation. Store table-cell evidence and derived calculations separately from verbatim narrative evidence.

Distinguish exactness against canonical text from fidelity to the original source. A hash does not establish that parsing was correct. Require source-map and visual checks where needed. OCR-derived text must not be called a verified original quotation merely because it matches the OCR output.

## 3. Evidence extraction, semantic support, and exact-quote links

Compare sentence/block pointer selection, extractive span prediction, generated quotations followed by deterministic verification, and provider-native citation mechanisms. Verify current structured-output compatibility rather than repeating dated statements from the notes.

Prefer designs in which the model selects existing evidence IDs and code resolves the spans, rather than trusting model-generated character counts. Define separate checks for:

- **Exactness:** the quotation equals the selected canonical source span.
- **Source fidelity:** the span faithfully represents the original document.
- **Semantic support:** the quotation actually supports the associated claim, with correct speaker, entity, period, scope, modality, and qualifications.

Require a deterministic invariant equivalent to `quote_text == canonical_text[start:end]`, plus document/version/hash and boundary validation. Define bounded retries, abstention, rejection, and quarantine. Fuzzy matching may locate candidate evidence but must never make an approximate quotation pass as exact. Any recovered span must be sliced from the source and reassessed for support.

Do not stitch noncontiguous passages into one quotation, silently repair wording, remove inconvenient qualifications, or present paraphrases as quotes. Store multiple spans separately. Retain enough surrounding context to resolve pronouns, negation, attribution, and question-answer relationships.

An analyst asking about layoffs is evidence of analyst attention, not evidence that layoffs occurred. Management assertions should remain attributed disclosures, not automatically become independently verified facts. Assess entailment/support models and human-calibrated LLM judges without treating either as infallible.

### Passage-level linking contract

Design two links for each evidence record: the original source URL and a durable link that opens the exact passage with highlighting and surrounding context. A company homepage, filing-index page, or unanchored PDF alone is insufficient.

Compare native anchors, DOM selectors, browser text fragments, PDF page/region coordinates, and W3C-style text-quote/text-position selectors. Specify a fallback evidence viewer or permitted immutable snapshot when the publisher cannot support reliable passage links. Store exact text, disambiguating prefix/suffix, offsets, source hash/version, and relevant page, block, table, or speaker coordinates.

Distinguish original-site deep links from application-hosted evidence links. Do not imply a proposed viewer already exists. Test repeated text, source revisions, link resolution, and wrong-occurrence errors; keep originals and snapshots distinguishable. Respect access and redistribution restrictions.

Every substantive clause in a theme summary must map to one or more supporting evidence records. Contradictions, qualifications, and cross-document comparisons need their own evidence links. A theme-level bibliography is not sufficient.

## 4. Theme discovery, classification, and longitudinal consistency

Compare credible alternatives, not just frameworks: keyword/dictionary and TF-IDF baselines; classical topic models; embedding/clustering approaches such as BERTopic; supervised and few-shot multilabel classification; domain-adapted or fine-tuned models; and evidence-first LLM extraction and consolidation.

Evaluate full-document long-context processing against structure-aware chunking and hierarchical consolidation, and against hybrid lexical/dense retrieval with reranking. Measure coverage and omission errors, especially for important themes mentioned briefly. Do not assume fitting in context guarantees complete extraction, or that top-k retrieval is adequate for exhaustive theme discovery. Consider graph-based methods only with a concrete benefit and a competitive simpler baseline.

Define topic, claim, theme, subtheme, sentiment, and event type separately. Prefer specific supported themes such as “customers delaying large contracts” over uninformative labels such as “business.” Do not force every document into a predefined number of themes.

Recommend a deductive, inductive, or hybrid codebook strategy. Include stable IDs, hierarchical definitions, inclusion/exclusion rules, positive and negative examples, multilabel rules, an unknown/novel pathway, human approval, and version history. Cover emerging themes, merges/splits, sector-specific subthemes, and consistent recoding. Separate retrospective harmonized analysis from prospective fixed-codebook evaluation to avoid future-information leakage.

Preserve issuer/entity scope, business segment, geography, time horizon, observed versus forward-looking language, direction, uncertainty, speaker role, and prepared-remarks versus Q&A context. Distinguish analyst concern, management emphasis, agreement, denial, non-answer, and contradiction using explicit evidence. Do not equate silence with denial or absence.

## 5. Theme importance: definition, scoring, and ranking

Make the primary ranking unit **issuer × earnings event/fiscal period × theme**. Provide separate document-level diagnostics and clearly defined sector/quarter aggregation.

Explicitly separate:

1. **Business significance:** disclosed implications for the firm's performance, operations, strategy, or risks; not an unsupported legal-materiality determination.
2. **Discourse salience:** emphasis, discussion share, repetition, and analyst attention.
3. **Cross-firm prevalence:** the share of eligible firms discussing a theme, with an observable denominator.

Use business significance as the proposed primary meaning of “importance,” but report salience and prevalence separately. Explain any alternative choice. Do not confuse sentiment, frequency, classification confidence, and importance.

Design an interpretable baseline and compare it with expert pairwise ranking, calibrated model-assisted ranking, and supervised learning-to-rank where labels justify it. Propose feature definitions, anchored scoring rubrics, aggregation rules or equations, missing-value treatment, tie handling, and sensitivity analysis. Mark hand-selected weights as provisional—not empirically optimal. Do not give ordinal scores unjustified numerical precision.

Evaluate factors such as disclosed financial or operational magnitude; relevance to guidance and strategic change; persistence and time horizon; novelty relative to available prior periods; specificity; explicit management prioritization; and distinct analyst attention. Keep severe, infrequently mentioned risks eligible for high importance. Missing quantified impact is unknown, not zero.

Prevent duplicated releases, repeated prepared remarks, long documents, verbose speakers, and multiple share classes from inflating importance. Cross-document consistency is not necessarily independent corroboration. Explain how dissenting evidence changes the interpretation or uncertainty without automatically making the underlying issue unimportant.

Keep evidence adequacy and confidence visible separately from importance; justify any gating or adjustment. Provide an evidence-linked rationale for each material score component. Compare rankings across prompt/model runs and reasonable weights, reporting ties or rank bands when warranted.

For sector summaries, define the eligible population, missingness, coverage, weighting, and denominators. Do not infer economic magnitude from quote counts, weight by employment by default, or claim population-wide effects from a selected company sample. Treat stock-price reactions as an optional, confounded external validation—not ground-truth importance or proof of causality.

## 6. Architecture and data contracts

Map the recommendation to proposed monorepo responsibilities without requiring unnecessary reorganization:

- `earnings-core`: identifiers, schemas, provenance, hashes, and pure evidence/span primitives.
- `earnings-ingestion`: acquisition, event/entity resolution, raw storage, parsing, canonicalization, and source maps.
- `earnings-themes`: evidence selection, support assessment, codebooks, classification, ranking, and evaluation.
- `earnings-pipeline`: configuration, CLI/workflows, resumability, human review, and reporting.

Compare a typed Python baseline with optional structured-extraction, workflow, and optimization tools from the notes. Assess Pydantic/PydanticAI, LangGraph, DSPy, and multi-agent alternatives only for the specific problem they solve. Do not make all learning-stage libraries production dependencies. Evaluate the previously discussed Jev/TypeSafe option only as a candidate extension, with verified capabilities, rights, costs, and measured value; do not assume it replaces extraction or provenance.

Provide explicit contracts for `Issuer`, `EarningsEvent`, `SourceDocument`, `DocumentVersion`, `DocumentBlock`, `EvidenceSpan`, `Claim`, `ClaimEvidenceLink`, `ThemeDefinition`, `ThemeAssignment`, `ThemeScore`, and `ProcessingCoverage`. Explain relationships, nullable fields, invariants, and schema evolution. Support multiple quotes per claim and multiple claims/themes per quote without duplicating the source record.

At minimum, retain issuer/CIK; fiscal period/event; document role; accession/exhibit identity where applicable; original and evidence URLs; public-availability and retrieval timestamps; raw/canonical hashes; parser/canonicalizer versions; exact quote and offsets; section/speaker/coordinates; support relation; theme/codebook version; ranking components and rationale; model/prompt/run versions; and rights/coverage status.

Explain storage choices, immutable manifests, idempotency, selective reprocessing, caches keyed by all material inputs, offline replay, bounded retries, budget controls, and local-first observability. Treat downloaded documents as untrusted data, not instructions. Keep restricted text and credentials out of inappropriate logs or external services. Default CI must not require network or billable calls.

## 7. Evaluation and experimental design

Design an expert-annotated benchmark spanning firms, sectors, periods, document types, layouts, Q&A structures, common themes, and rare high-importance events. Include valid documents with no qualifying themes, unavailable sources, and parser failures. Assess what a 20–40-document pilot can establish and what requires a larger validation set.

Use independent annotation and adjudication for theme definitions, supporting spans, speaker/entity attribution, support relationships, and importance judgments. Report agreement and genuine ambiguity. Split by issuer and time as appropriate; keep duplicate documents and complete event bundles within one split. Prevent leakage through codebook discovery, prompt optimization, repeated releases, and corrected future versions.

Specify metrics and proposed acceptance criteria for acquisition coverage; correct exhibit selection; parsing and table fidelity; speaker attribution; span precision/recall; theme micro/macro and hierarchical performance; semantic support; citation completeness; exact-link resolution; abstention and retained coverage; and run-to-run stability. For ranking, include expert pairwise agreement, nDCG or suitable alternatives, and recall of rare critical themes. Report uncertainty with sampling units that respect within-firm/event dependence.

Accepted canonical quotations must satisfy exactness deterministically, but separately measure original-source fidelity and support. A system rejecting everything must fail usefulness evaluation. Do not present unvalidated model confidence as a calibrated probability.

Provide controlled baselines and ablations for whole-document versus chunked/retrieved extraction; pointer versus generated-then-verified quotes; codebook strategies; deduplication; transcript inclusion; ranking factors; and workflow versus multi-agent designs. Measure quality, latency, memory, inference usage, total cost, and maintenance burden on comparable inputs.

Include adversarial tests for wrong exhibits, duplicate passages, modified documents, negation, units, wrong fiscal periods, analyst questions, unsupported causal claims, prompt injection, omitted qualifiers, and important single mentions. Label thresholds as proposed unless validated. Do not describe planned experiments as completed results.

## 8. Required deliverables

Return a self-contained GitHub-Flavored Markdown report with:

1. **Executive recommendation and source audit:** recommended approach, critical changes to the notes, unresolved choices, and evidence strength.
2. **Critical methods review and comparison matrix:** task-specific results, transfer limitations, primary citations, and a reasoned shortlist—not a catalog.
3. **End-to-end design:** ingestion, event linkage, canonicalization, evidence, classification, ranking, and reporting; include a pipeline diagram and failure/review paths.
4. **Formal ranking specification:** definitions, rubric/formula, duplicate and missing-data treatment, uncertainty, and evidence-linked explanations.
5. **Implementation contracts and representative Python:** typed schemas, deterministic span validation, citation resolution, ranking interfaces, and a Polars export. Distinguish runnable code, pseudocode, and untested integrations.
6. **Evaluation plan and staged roadmap:** simplest defensible baseline, strongest justified open-source design, and optional explicitly authorized hosted-model comparison. Define acceptance gates and experiments that could overturn the recommendation.
7. **A small worked example:** use actual accessible source documents, with short permitted quotations and verified original URLs. Include a matched transcript only when accessible and permitted. Show ranked themes, classifications, importance versus salience, score rationale, exact evidence, speaker/section, and link status. Do not invent offsets, quotations, computed scores, or functioning viewer links; label illustrative calculations and proposed routes. Synthetic edge cases may be added only when clearly separated from real evidence.
8. **Reproducibility appendix:** source register, literature-search scope, bibliography, software/model/license verification dates, and outstanding limitations.

The example's analyst-facing view should expose: rank; theme and hierarchy; supported claim; importance and rationale; salience; confidence/coverage; exact quotation; speaker/document/section; and passage/source links. Keep machine-readable evidence normalized rather than forcing every field into one oversized table.

End with “Recommended first implementation” and “Evidence that would change this recommendation.” Prioritize acquisition correctness, source fidelity, exact evidence links, defensible classification, and validated ranking over framework breadth. When evidence or tool access is insufficient, state precisely what remains unverified and provide the best supported design without fabricating completion.

### Primary-source starting points to verify during the review

- SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- EdgarTools 8-K documentation: https://edgartools.readthedocs.io/en/latest/eightk-filings/
- W3C Web Annotation Data Model: https://www.w3.org/TR/annotation-model/
- Original papers, repositories, and documentation linked in the two supplied notes.