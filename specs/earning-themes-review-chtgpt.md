# Evidence-linked earnings document intelligence: a production research design

**Research execution date:** September 22, 2026.

This review recommends an **evidence-first, source-faithful pipeline** rather than a generic retrieval-augmented generation architecture. The central design principle is that extraction, classification, ranking, and synthesis should operate on stable identifiers that ultimately resolve to immutable source spans; generated prose is downstream of those spans, not the source of them. That choice is especially important in financial disclosures because otherwise-plausible evidence can belong to the wrong issuer, period, section, speaker, or version. Recent financial retrieval work finds exactly this provenance problem: the 2026 FinRank preprint reports large degradation when systems must discriminate hand-curated hard negatives from confusable periods, companies, and disclosure contexts, despite apparently relevant text. citeturn17academia37

One material limitation applies to the requested source audit. The requested files `earnings-ingestion.md`, `earnings-themes.md`, and `AGENTS.md` were **not retrievable in this research session**: the file-retrieval interface reported that no uploaded or connected file sources were available. I therefore have **not** represented those documents as read, and I do not attribute any requirement or proposal specifically to them. The audit below treats the detailed requirements in the research prompt as authoritative and separately identifies seed-note claims that still need a line-by-line audit once those files are available. This limitation does not prevent a well-supported architecture recommendation, but it prevents a faithful “retain/revise” audit of the actual prose of those files.

## Executive recommendation and source audit

The recommended production architecture has six defining properties.

First, **SEC discovery should be accession-complete and source-first**. Use SEC submissions data to enumerate candidate filings for each CIK, then traverse each accession's actual filing documents and attachments. The SEC submissions endpoint requires no API key, exposes recent filing history plus pointers to additional historical JSON files, is updated as submissions are disseminated, and is also distributed as a nightly bulk archive; those properties make it suitable for both backfill and incremental discovery. citeturn16view1 The system should never substitute “latest 8-K” for event resolution.

Second, **earnings-release identification must be a document-classification problem, not an exhibit-number heuristic**. Item 2.02 of Form 8-K addresses public announcements or releases concerning material non-public results of operations or financial condition for completed periods and requires the announcement/release text to accompany the report as an exhibit in the circumstances covered by the item. Item 9.01 is the filing's exhibit section. citeturn12view0turn12view1 Thus Item 2.02 and EX-99.1 are excellent discovery signals, but the implementation must inspect the exhibit index, description, linked document, content, dates, and fiscal-period language.

Third, **canonicalization and provenance are first-class data products**. Preserve immutable raw artifacts, create a versioned canonical representation, and keep explicit source mappings. Accepted evidence is never a model-generated quotation: the model selects existing block/sentence/cell identifiers, and deterministic code materializes the quotation from canonical text. Exactness is enforced by an invariant such as `quote_text == canonical_text[start_cp:end_cp]`. Original-source fidelity and semantic support remain separate judgments.

Fourth, **theme analysis should be exhaustive over structure-aware chunks, evidence-first, and hybrid-codebook based**. Retrieval can accelerate focused queries, but it should not be the only candidate-generation path for theme discovery. Long-context availability is not evidence of exhaustive use of context: the TACL “Lost in the Middle” study found substantial sensitivity to the position of relevant information, including significant degradation when relevant material appeared in the middle of long contexts. citeturn16view4 Every eligible block should therefore get a chance to generate a candidate claim before event-level consolidation.

Fifth, **importance should mean business significance**, not frequency, sentiment, model confidence, or legal materiality. Rank at `issuer × earnings event/fiscal period × theme`. Report discourse salience and cross-firm prevalence separately. Use an anchored ordinal rubric initially; validate its provisional weights against expert pairwise comparisons before treating the composite ordering as authoritative.

Sixth, **the initial production stack should be deliberately boring**: Pydantic v2 schemas, Polars transformations, explicit Python orchestration/state transitions, local open-weight inference where an LLM is justified, content-addressed files, Parquet analytical outputs, SQLite or another small transactional metadata store, `uv`, Ruff, and pytest. Pydantic's current documentation describes v2.13.4 and supports type-driven validation plus JSON Schema generation. citeturn22view4 Current vLLM documentation exposes structured-output paths for online and offline inference, making constrained local inference a viable implementation candidate, subject to pinned model/backend compatibility tests. citeturn20view0

**Source-to-requirement audit**

| Area | Retain as a requirement | Revise or test | Defer |
|---|---|---|---|
| Company universe | Configurable universe; CIK-centered issuer identity; separate security/ticker history; point-in-time membership | Test corporate-action and ticker-change cases; do not assume one issuer = one listed security | Subsidiary/establishment/employment graph |
| SEC acquisition | Direct SEC submissions/archive path as source of truth; accession traversal; raw preservation | Benchmark EdgarTools as an adapter, never as sole coverage oracle | Alternative commercial filing feeds |
| Earnings-release selection | Item 2.02 as a strong signal; inspect actual exhibits/content | Test multiple EX-99 documents, non-99.1 releases, narrative-only releases, 8-K/A, corrections | 10-Q/10-K/6-K as core substitutes |
| Transcripts | Issuer IR first; explicit rights register; versions and speakers | Measure issuer-by-issuer coverage and missingness bias | Audio transcription except explicit fallback |
| Canonical text | Immutable raw + versioned canonical + source maps | Validate HTML, tables, PDFs, malformed filings against originals | OCR except unreadable/image-only sources |
| Evidence | Existing evidence IDs, deterministic source slicing, support relation | Compare sentence/block pointers with verified substring extraction | Provider-native citation as authoritative evidence |
| Theme taxonomy | Hybrid codebook, stable IDs, multilabel, unknown/novel queue | Empirically choose local classifier/LLM and chunk strategy | Autonomous codebook mutation |
| Importance | Business significance primary; salience/prevalence separate | Validate rubric and weights with pairwise expert ranking | Price reaction as ground truth |
| Frameworks | Typed schemas and deterministic workflow baseline | PydanticAI, DSPy, LangGraph only if experiments justify them | Multi-agent default |
| Jev/TypeSafe | Evaluate only as an optional extension | Requires task-specific independent comparison and budget authorization | Mandatory dependency or provenance layer |

That last distinction matters. TypeSafe introduced Jev only on September 15, 2026, describes it as an early-access typed-decision system, and publishes strong speed, cost, type-safety, and calibration claims. The vendor itself also acknowledges important evaluation qualifications, including internally constructed workflows and proxy reference probabilities from other models. No independent earnings-document benchmark was found in this review. citeturn22view2turn22view3 It is therefore an interesting future classifier/ranker candidate, not evidence extraction infrastructure and not part of the no-billable-inference required path.

There is also one important correction to a likely EdgarTools-based design. EdgarTools' 8-K documentation provides useful `press_releases`, item access, attachments, and earnings conveniences, but its documented `has_earnings` behavior is intentionally narrower than “contains an earnings release”: the documentation notes that narrative-only earnings releases can be missed because its earnings detection depends on Item 2.02, an earnings exhibit pattern, and parseable financial tables. Its broader press-release detection is also pattern based. citeturn16view2 Therefore `has_earnings` should be a **diagnostic feature**, never the discovery denominator. EdgarTools is attractive as an optional SEC adapter, but its public API/docs also make substantial use of pandas DataFrames, which conflicts with a strict Polars-only analytical application boundary; isolate it behind plain Python/Arrow/record adapters rather than allowing pandas objects into domain code. citeturn3view0turn3view1

## Critical methods review and comparison

No single published benchmark exactly measures the requested composite task: identifying the right 8-K exhibit, faithfully canonicalizing it, discovering decision-useful earnings themes, attaching exact evidence, and ranking those themes by business significance. The sound approach is therefore to use adjacent benchmarks only for the specific capability they actually test, and construct an earnings-specific benchmark for the final decision.

Recent financial benchmarks make two points particularly relevant to this design. FinanceBench contains 10,231 financial questions with answers and evidence strings and, in its original experiments, manually reviewed 2,400 outputs across 150 cases; the authors reported severe limitations in then-current retrieval/LLM configurations. It is useful evidence that “financial RAG” is not automatically reliable, but its documents and task are financial QA rather than event/theme extraction, and its evaluated model generation is now dated. citeturn17academia38 FinRank, a 2026 preprint, is closer to the provenance problem: 1,185 manually authored records over 10-K/10-Q filings for 22 companies include gold passages and hard negatives from confusable sections, periods, and companies. Its reported best evaluated 7B instruction-tuned embedder achieved only 44.8% Recall@10 on the pooled evidence corpus, while replacing random negatives with curated hard negatives reduced pairwise accuracy by 13–20.5 percentage points. Those are authors' benchmark results, not proof about earnings calls, but they strongly argue for explicit issuer/period/source constraints and against assuming semantic similarity is enough. citeturn17academia37

| Method | What the evidence actually establishes | Transfer limitation for this project | Recommendation |
|---|---|---|---|
| Exact dictionaries / regex | Deterministic and auditable; strong regression baseline for known wording | Low paraphrase recall; weak novelty detection; cannot establish support by itself | **Required baseline** |
| TF-IDF / lexical similarity | Cheap, interpretable ranking of vocabulary overlap | Frequency-biased; synonyms and context difficult | **Required baseline** |
| Classical topic models | Useful unsupervised corpus structure/discovery baseline | Topics are word distributions, not supported claims or stable decision-useful labels | Discovery baseline only |
| BERTopic | Embedding → clustering → class-based TF-IDF; author reports competitive topic-model benchmarks citeturn17academia40 | Benchmark is not earnings-theme classification; cluster identity can drift by corpus/model/hyperparameters | Novel-theme discovery aid only |
| Supervised multilabel classifier | Can become stable, fast and reproducible once labels are sufficiently representative | Requires sizable adjudicated labels and explicit unknown handling | Strong long-run classifier |
| Few-shot/local LLM classification | Flexible codebook interpretation without large initial training set | Run variance, model drift, contextual errors; output validity ≠ semantic correctness | Strong pilot candidate |
| Evidence-first LLM extraction | Can jointly identify granular claims and attributes while returning evidence IDs | Needs local benchmark; model may omit brief themes | **Recommended semantic extraction design** |
| Top-*k* lexical/dense RAG | Efficient for questions about known themes | Can structurally omit rare/single-mention themes before the model sees them | Use for targeted retrieval, not exhaustive discovery |
| Whole-document long context | Simple, preserves remote context | Long-context models can underuse middle content; fitting does not imply recall citeturn16view4 | Ablation, not default |
| Exhaustive structure-aware chunking | Every block is processed and can surface a candidate | Requires consolidation and cross-chunk context recovery | **Default discovery path** |
| Hierarchical consolidation | Controls long event bundles and can preserve local evidence pointers | Consolidator may merge distinct claims or erase contradictions | Use with evidence-preserving merge rules |
| Graph extraction | Potential benefit for explicit claim/contradiction/entity relations | Complexity without proven benefit over normalized relational records | Defer until a graph-specific task wins an ablation |
| Multi-agent workflow | Potential decomposition of roles/checks | Extra calls, nondeterminism, complex debugging; no relevant evidence that agents improve this task | Do not use initially |

The main architectural distinction should be **discovery versus targeted retrieval**. For exhaustive event analysis, scan all analysis-eligible blocks. Hybrid lexical/dense retrieval is still valuable after that: for example, to collect all potential evidence for a known theme, locate a prior-period analogue, challenge a candidate with contradictory passages, or build human-review queues. FinRank's hard-negative results make a strong case that reranking tests should include wrong-period and wrong-issuer confounders rather than only random negatives. citeturn17academia37

The codebook should be **hybrid deductive–inductive**. A purely deductive taxonomy is stable but can suppress emerging issues; a purely inductive topic model is unstable over time. Each `ThemeDefinition` should therefore have a stable identifier, parent identifier, human-readable label, formal definition, inclusion rules, exclusions, positive examples, difficult negatives, sector applicability, allowed attributes, and codebook version. Unknown candidate claims go to a novelty queue; clustering such as BERTopic may organize that queue, but no new production theme ID should appear without review. BERTopic is explicitly a clustering-plus-class-based-TF-IDF approach and is thus well suited to exploratory grouping, not evidence semantics. citeturn17academia40

The core semantic units should remain distinct:

| Unit | Definition |
|---|---|
| **Topic** | Broad subject or distributional cluster such as labor, pricing, AI, demand, or regulation. |
| **Claim** | An attributable proposition: e.g. “management says large customers delayed decisions.” |
| **Theme** | A normalized decision-useful pattern aggregating one or more claims: e.g. “customer decision cycles lengthening.” |
| **Subtheme** | A narrower stable code under a theme, such as “large-enterprise contract delays.” |
| **Sentiment/direction** | Positive/negative/mixed or improving/worsening/stable characterization, independent of theme identity. |
| **Event type** | What happened or what document/disclosure context represents: earnings release, restructuring disclosure, guidance change, etc. |

This distinction prevents the system from producing vacuous labels such as “business” or “customers,” and prevents a negative sentiment score from masquerading as importance.

For evidence, the strongest design is **pointer first**. Segment canonical material deterministically into headings, paragraphs, list items, sentence or clause candidates, transcript turns, and individual table cells. Give each a stable ID. The semantic model returns those IDs and structured claim attributes. Code subsequently slices the text. Generated quotations followed by exact matching can be retained as an ablation, but it is strictly weaker operationally: matching must still resolve to source text, and failure to resolve must reject rather than “repair” the quote.

Provider-native citations should likewise be treated as hints unless they resolve into the local evidence contract. A provider's citation can point to the right document yet remain inadequate for exact canonical offsets, document version, table coordinates, or repeated-text disambiguation.

For passage anchoring, the W3C Web Annotation model is unusually well aligned with the requested contract. Its `TextQuoteSelector` stores exact text plus optional prefix/suffix context, while `TextPositionSelector` represents positions with an inclusive start and exclusive end; the model discusses combining selectors to improve rediscovery robustness. citeturn16view3 I recommend following that conceptual design even if the storage objects are ordinary Pydantic models rather than RDF/JSON-LD.

For model serving, use constrained structured output where possible but keep Pydantic validation after generation. Current vLLM documentation has explicit structured-output support in both server and offline paths. citeturn20view0 PydanticAI can reduce provider-specific plumbing and has a dedicated typed-output layer, but it should remain an optional adapter rather than own domain schemas. citeturn20view1 LangGraph's value proposition is durable stateful graph orchestration; it becomes attractive only if workflow branching, pause/resume, and human checkpoints become substantially harder than the explicit pipeline state machine. citeturn20view2 DSPy is more interesting after a real labeled benchmark exists: its signatures/optimizers are intended to program and optimize LM pipelines, so it can experimentally optimize prompts or demonstrations against the project's metrics rather than hand-tuning indefinitely. The original DSPy work and current project describe precisely that optimization use case. citeturn8search14turn8search3

An initial open-weight semantic baseline can use a locally served instruction model whose exact weight license is pinned in the manifest. Qwen's official Qwen2.5 release, for example, states that most sizes are Apache 2.0 while explicitly identifying exceptions for the 3B and 72B variants; a 7B or 14B Qwen2.5 checkpoint is therefore a reasonable *baseline candidate*, not a claim of 2026 task superiority. citeturn18search27 Newer candidates should enter only through the same benchmark. Open weights remove mandatory API charges, not compute, hardware, or electricity costs.

## End-to-end design

The pipeline should make **source correctness precede semantic sophistication**.

```mermaid
flowchart TD
    U[Point-in-time company universe] --> D[Discover expected earnings events]
    D --> S[SEC submissions and accession enumeration]
    D --> I[Issuer IR source discovery]

    S --> A[Traverse complete 8-K / 8-K-A accession]
    A --> X[Classify main document and every exhibit]
    X --> E[Resolve actual earnings release(s)]

    I --> T[Permitted transcript / webcast discovery]
    T --> R{Rights and access acceptable?}
    R -- no --> RS[Restricted or unavailable state]
    R -- yes --> TA[Acquire transcript source]

    E --> RAW[Immutable raw artifact store]
    A --> RAW
    TA --> RAW

    RAW --> P[Format-aware parsing]
    P --> F{Fidelity checks pass?}
    F -- no --> Q[Quarantine / human review]
    F -- yes --> C[Versioned canonical document + source map]

    C --> B[Stable blocks / sentences / cells / turns]
    B --> EX[Exhaustive evidence-first claim extraction]
    EX --> V{Exact span invariant passes?}
    V -- no --> Q
    V -- yes --> SUP[Semantic support assessment]

    SUP --> TH[Multilabel theme classification]
    TH --> NOV[Unknown / novelty queue]
    TH --> CONS[Event-level consolidation]
    CONS --> IMP[Business-significance rubric]
    CONS --> SAL[Discourse salience diagnostics]
    CONS --> PREV[Cross-firm prevalence]

    IMP --> REV{Review required?}
    SAL --> REV
    REV -- yes --> Q
    REV -- no --> OUT[Evidence-linked analyst output]

    Q --> OUT
```

**Acquisition and event resolution.** Represent the company universe independently of documents. The issuer identity should be CIK-centered for SEC issuers, while ticker, exchange, CUSIP/other security identifiers, share class, and universe membership are versioned relationships. Do not collapse issuer and security. SEC submissions data supplies CIK-oriented filing history and current/former ticker metadata, but those are inputs rather than the complete security master. citeturn16view1 Keep SIC, NAICS, and any vendor sector taxonomy as separate provenance-bearing classifications with `valid_from`, `valid_to`, `source`, and retrieval/version metadata.

For each expected earnings event, derive candidate accessions by CIK and a sufficiently broad time window, then inspect **all candidate 8-K/8-K/A filings**. SEC's submissions JSON contains at least a year or the most recent 1,000 filings in its current portion and links older filing-history JSON when necessary; the SEC also publishes a bulk submissions archive nightly. citeturn16view1 Historical backfill should therefore use bulk/submission histories rather than thousands of avoidable search-page queries; incremental processing can consume per-CIK submissions.

Every accession is an indivisible discovery unit. Retrieve and manifest:

`accession → filing index → primary 8-K → exhibit index/attachments → each candidate exhibit`.

Classify each attachment into at least `MAIN_8K`, `EARNINGS_RELEASE`, `PRESENTATION`, `SUPPLEMENTAL_TABLES`, `OTHER_RELEASE`, `OTHER_EXHIBIT`, and `UNKNOWN`. A filing can have zero, one, or multiple earnings releases. Do not assume “first exhibit,” `EX-99.1`, or “press release” in the filename is dispositive.

EdgarTools can simplify this traversal and item parsing, but its convenience indicators cannot define coverage. Its documented earnings convenience specifically has narrower conditions that can miss narrative-only releases, while its press-release detection uses exhibit/description patterns. citeturn16view2 Run an explicit benchmark comparing:

`gold earnings-release exhibits` versus `EdgarTools press_releases`, `has_earnings`, custom deterministic exhibit rules, and a content classifier.

The direct SEC path remains the reference implementation. EdgarTools should be swappable.

SEC automation should send an identifying `User-Agent`, rate-limit globally rather than per worker, cache immutable responses, use exponential backoff with jitter for transient errors, and make each accession idempotently resumable. SEC has stated that traffic exceeding 10 requests per second may be temporarily rate limited; a production client should stay comfortably below that threshold rather than treating 10 as a throughput target. citeturn1search8

**Event identity should not be a quarter string.** A practical `EarningsEvent` record contains:

`issuer_id`, fiscal-year/quarter labels if known, `period_start`, `period_end`, first-public-release timestamp, SEC acceptance timestamp, call timestamp, retrieval timestamp, timestamp precision, and an internal stable event ID.

Match candidate documents on issuer + fiscal period + period end + event date + content. Calendar-quarter equivalence is unsafe for non-calendar fiscal years, and ticker alone is unsafe across corporate actions. SEC itself cautions that fiscal reporting periods need not align with calendar quarters in its XBRL framing discussion. citeturn16view1

For point-in-time analysis, every run has an `as_of` timestamp. A later 8-K/A, corrected IR release, or corrected transcript can be linked to the same logical event but must not be visible to a run whose `as_of` predates the revision. Retrospective “best current version” analysis is a separate mode and should say so.

**Duplicate handling.** A single disclosure may appear on EDGAR, an issuer IR page, and a transcript/release portal. Store these as distinct `SourceDocument` records and associate them with a `disclosure_content_group_id` after exact-hash or reviewed near-duplicate matching. Importance and salience count the underlying disclosure once, while the evidence layer retains all source provenance. Conversely, supplemental slides that add information are not duplicates just because they repeat several earnings-release paragraphs.

**Transcripts require a source register, not a scraper assumption.** The required path should discover issuer-hosted transcripts first. For each issuer/source, record publisher/owner, access method, observed historical depth, current coverage, document/audio format, correction/version behavior, terms review date, redistribution status, and any automation restriction. “Publicly reachable” should not be treated as “freely redistributable.” A third-party scraper does not establish rights to the resulting text.

Where a published transcript exists, represent:

`participants → prepared remarks → Q&A → operator text`

as distinct structures. A speaker turn stores the raw speaker label, normalized person if resolvable, organization, inferred/declared role, role source, and an uncertainty field. `MANAGEMENT`, `ANALYST`, `OPERATOR`, and `UNKNOWN` are mandatory role classes. An analyst asking “are customers delaying orders?” creates evidence of **analyst attention**, not an evidence-backed company claim that customers are delaying orders.

If only a permitted webcast/audio recording is available, local transcription can be a separately scoped fallback with `source_kind=AUDIO_DERIVED_TRANSCRIPT`. It should never masquerade as an issuer-published transcript. Quotations from it need a separate fidelity status and, ideally, timestamped audio verification.

**Processing states should be explicit.** At document and event level, use at least:

`EXPECTED`, `UNAVAILABLE`, `RESTRICTED`, `ACQUIRED`, `PARSED`, `PARTIAL`, `FAILED`, and `COMPLETED`.

A transcript can therefore be legitimately `RESTRICTED` while the 8-K and release are `COMPLETED`. Sector prevalence must use an eligible/observable denominator, not silently treat restricted transcripts as “no theme.”

**Canonical representation.** Keep the raw bytes forever, subject to source rights and retention rules, addressed by SHA-256. Parsing emits a `DocumentVersion` with parser version and a canonicalizer version. The canonical representation comprises one ordered text stream plus typed block metadata. Block kinds include headings, paragraphs, list items, footnotes, transcript turns, table captions, table headers, and table cells.

For HTML:

- Parse the DOM rather than stripping tags with regex.
- Resolve HTML entities deliberately.
- Preserve headings/list/table hierarchy.
- Remove nothing from the canonical source merely because it is boilerplate; add `analysis_included=False` masks instead.
- Preserve hidden-content metadata so a parser does not silently promote invisible navigation text.
- Version every whitespace/line-ending rule.

For inline XBRL, preserve human-rendered text while retaining relevant inline-fact/tag associations separately. SEC describes inline XBRL as XBRL embedded in reporting HTML and notes that custom taxonomies and contexts can differ across companies. citeturn16view1

For tables, never synthesize a sentence by concatenating unrelated cells. A table cell is its own evidence-bearing block with `row`, `column`, header-path, unit, scale, period, currency, and coordinates. A derived ratio stores input cell IDs and an expression separately. That prevents a calculation from later being displayed as though management stated it verbatim.

PDF parsing is secondary for this corpus because HTML should be preferred where available. Store page and bounding-box source coordinates. OCR is last resort. A quote exactly matching OCR output proves **canonical exactness only**, not fidelity to the image.

Use Unicode **code-point** offsets and half-open spans `[start_cp, end_cp)`. This aligns well with the W3C text-position model's start/end semantics, while exact/prefix/suffix fields follow its text-quote approach. citeturn16view3 Do not use UTF-8 byte offsets as the analyst-facing evidence convention; byte offsets can coexist in lower-level source maps.

**Three evidence checks are mandatory and independent.**

| Check | Question | Pass condition |
|---|---|---|
| Exactness | Is this quote exactly in the selected canonical version? | Deterministic equality, correct hash/version, valid block boundaries |
| Source fidelity | Does canonical text faithfully represent the original artifact? | Parser/source-map/visual or native-text validation appropriate to format |
| Semantic support | Does the evidence actually justify the claim? | Correct entity, speaker, period, scope, modality, qualification and relation |

A semantic model never overrides an exactness failure. Fuzzy matching is acceptable for *finding* a candidate after a source changed or a model returned approximate wording; acceptance requires re-slicing the recovered passage from the source and running semantic support again.

The evidence relation should distinguish at least `SUPPORTS`, `QUALIFIES`, `CONTRADICTS`, `ANALYST_ATTENTION`, `DENIES`, `BACKGROUND`, and `NON_ANSWER`. Management assertions remain attributed management assertions unless independently verified from another source.

Every theme summary should be decomposed into atomic claims. That makes “every substantive clause has evidence” enforceable: one `Claim` represents one proposition, and a natural-language theme summary is generated only from accepted claims. Multiple evidence spans may support one claim; one evidence span may support several claims and several theme assignments. No text needs duplication.

**Passage links use two destinations.** Each evidence row stores:

1. `original_url`: SEC/issuer/publisher source.
2. `evidence_url`: a proposed application route such as `/evidence/{evidence_id}`.

The durable application viewer should bind to source hash and version, display surrounding context, and distinguish a publisher original from an internal/permitted immutable snapshot. Store, where applicable, W3C-like exact/prefix/suffix text selectors, start/end positions, DOM selector/native anchor, PDF page/bounding box, speaker-turn ID, and table-cell coordinates. W3C explicitly provides text-quote and text-position selector mechanisms appropriate to such multi-selector rediscovery. citeturn16view3

Native HTML anchors are useful where present. Browser text fragments are a useful best-effort original-site highlight. CSS/XPath locators can aid source mapping. PDF page links plus stored region coordinates can get the analyst close. **None of those should replace the hash-bound application evidence record.** Repeated-text tests must verify that the resolver does not highlight the wrong occurrence.

## Formal ranking specification

The primary ranking key is:

\[
(\text{issuer},\ \text{earnings event/fiscal period},\ \text{theme})
\]

not document, quotation, or mention.

The system should expose three different concepts rather than collapsing them.

**Business significance** asks how consequential the disclosed issue appears for the issuer's performance, operations, strategy, or risk. It is the primary meaning of “importance.” This is an analytical ranking, not a legal conclusion that something is “material.”

**Discourse salience** asks how strongly the event's speakers/documents emphasized the issue: where it appears, how much distinct discussion it receives, whether management returns to it, and whether analysts question it.

**Cross-firm prevalence** asks what fraction of an explicitly eligible, observable population discussed the theme.

A severe issue mentioned once can therefore be `high importance / low salience / low prevalence`. That is a feature, not an inconsistency.

For the initial interpretable baseline, score five business-significance components on an anchored ordinal scale `0–3`, with `unknown` distinct from zero.

| Component | Zero | One | Two | Three |
|---|---|---|---|---|
| **Magnitude / consequence** | Explicitly negligible/no consequence | Limited/localized consequence | Meaningful financial/operational scope | Major firm-level/severe consequence |
| **Guidance / strategy relevance** | No stated connection | Contextual relevance | Changes an important assumption or priority | Explicit major guidance/strategy change |
| **Persistence / horizon** | Transitory | Near-term | Multi-quarter | Structural/long-lived or difficult to reverse |
| **Novelty / change** | Continuation | Intensity changed modestly | New or substantially changed | Major discontinuity/new event |
| **Specificity / commitment** | Generic | Directional | Concrete action, amount, driver, or timeline | Multiple concrete commitments/quantifications tied to outcomes |

“Unknown quantified magnitude” is **not** magnitude zero. A company can disclose a severe unquantified plant shutdown, cyber incident, regulatory constraint, or supply interruption and receive a high magnitude judgment based on explicit qualitative consequences. Specificity may be lower, but the missing number must not erase severity.

A provisional aggregate can be calculated for experiments as:

\[
I_{\text{obs}}
=
\frac{
\sum_{j \in O} w_j(s_j/3)
}{
\sum_{j \in O} w_j
}
\]

where \(O\) is the set of observed components and an initial **provisional** weight vector is:

\[
w =
(0.35_{\text{magnitude}},
0.25_{\text{guidance/strategy}},
0.15_{\text{persistence}},
0.15_{\text{novelty}},
0.10_{\text{specificity}})
\]

These weights are not empirically optimal and must be labeled as such.

More importantly, compute a missingness interval:

\[
I_{\min}
=
\sum_{j\in O} w_j(s_j/3)
\]

\[
I_{\max}
=
I_{\min} + \sum_{j\notin O}w_j
\]

and retain:

\[
C_w = \sum_{j\in O} w_j
\]

as **component coverage**. This prevents missing data from becoming a false zero and makes underdetermined rankings visible. If two themes' plausible intervals substantially overlap, output a tie/rank band rather than manufacturing precision.

The production analyst interface should primarily show `HIGH`, `MEDIUM`, `LOW`, or `UNRESOLVED` importance bands plus the component vector and supporting evidence. The numeric composite is useful for controlled experiments and deterministic sorting, not as a pseudo-precise economic magnitude.

Each component must carry its own rationale and evidence IDs:

```text
magnitude = 3
evidence = [ev_0412, ev_0419]
rationale = "Management disclosed a firm-level operational impact affecting..."
```

A theme with no accepted evidence is **not rankable**. That is a gating rule. Evidence adequacy thereafter remains a separate field and should not simply be multiplied into importance; `high importance / moderate evidence adequacy` communicates more useful uncertainty than silently downgrading the business issue.

Classification/support confidence is also separate. Unless a confidence score has been calibrated on held-out annotations, call it a model score or confidence category, not a probability of correctness.

Salience should initially be reported as an interpretable vector rather than another opaque weighted score:

- management prepared-remarks share,
- number of distinct management turns,
- number of distinct Q&A turns,
- number of analyst questions raising the issue,
- number of distinct sections/documents where it appears,
- headline/guidance prominence.

Repeated copies of the same release do not create additional salience. Prepared remarks copied nearly verbatim into a release should not create two independent “mentions” for importance. A single verbose speaker should not dominate solely through word count. Analyst questions add **analyst attention**, but the question does not create evidence for the underlying factual claim.

Cross-firm prevalence for sector \(g\), period \(t\), theme \(k\) is:

\[
P_{gtk}
=
\frac{
\sum_i \mathbf{1}[\text{eligible}_{igt}]
\mathbf{1}[\text{observable}_{igt}]
\mathbf{1}[\text{theme}_{igtk}]
}{
\sum_i
\mathbf{1}[\text{eligible}_{igt}]
\mathbf{1}[\text{observable}_{igt}]
}
\]

with numerator and denominator always displayed. “Observable” must reflect source scope: a transcript-only theme cannot use firms with unavailable/restricted transcripts in the denominator unless the metric is explicitly redefined as whole-event observable.

Do not default to employment weighting or market-cap weighting. An equal-issuer measure answers “share of eligible issuers discussing this,” while revenue-weighted or employment-weighted measures answer materially different questions and require their own provenance and rationale.

The path from rubric to a learned ranker should be deliberate:

1. Annotators independently score components and make pairwise “which theme is more consequential for this event?” judgments.
2. Adjudicate disagreements and quantify ambiguity.
3. Test whether the rubric's ordering predicts adjudicated pairs.
4. Tune or learn component weights **only on training issuers/time periods**.
5. Compare a simple ordinal/linear ranker with a supervised learning-to-rank model when label volume justifies it.
6. Report pairwise agreement, nDCG, critical-theme recall, rank correlations across runs, and rank sensitivity across reasonable weight vectors.

A sophisticated ranker only wins if it improves those metrics without destroying interpretability.

## Implementation contracts and representative Python

The monorepo boundary should express ownership of truth rather than framework choice:

| Package | Responsibility |
|---|---|
| `earnings-core` | IDs, Pydantic schemas, hashes, rights/provenance types, span invariants, enums |
| `earnings-ingestion` | SEC/IR acquisition, source registry, event linkage, raw storage, parsing, canonicalization, source maps |
| `earnings-themes` | evidence candidate selection, support relations, codebook, theme assignment, novelty detection, ranking/evaluation |
| `earnings-pipeline` | configuration, CLI, state transitions, resumability, review queues, reporting/export |

No repository reorganization should occur merely to match those names if equivalent package boundaries already exist. Because the requested repository was not inspectable here, they should be treated as **responsibility boundaries**, not claims about existing directories.

Relationships are normalized:

```text
Issuer
  └── EarningsEvent
       ├── SourceDocument
       │    └── DocumentVersion
       │         └── DocumentBlock
       │              └── EvidenceSpan
       │
       ├── Claim ──< ClaimEvidenceLink >── EvidenceSpan
       │
       └── ThemeAssignment >── ThemeDefinition
                └── ThemeScore
```

A quote is therefore stored once even when it supports several claims/themes.

The following is **representative runnable baseline code** for Python 3.12, Pydantic v2, and Polars. It deliberately contains no LLM framework dependency.

```python
from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Cik = Annotated[str, Field(pattern=r"^\d{10}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
    )


class DocumentRole(StrEnum):
    MAIN_8K = "main_8k"
    EARNINGS_RELEASE = "earnings_release"
    PRESENTATION = "presentation"
    SUPPLEMENTAL_TABLES = "supplemental_tables"
    TRANSCRIPT = "transcript"
    AUDIO_DERIVED_TRANSCRIPT = "audio_derived_transcript"
    OTHER_EXHIBIT = "other_exhibit"
    UNKNOWN = "unknown"


class ProcessingState(StrEnum):
    EXPECTED = "expected"
    UNAVAILABLE = "unavailable"
    RESTRICTED = "restricted"
    ACQUIRED = "acquired"
    PARSED = "parsed"
    PARTIAL = "partial"
    FAILED = "failed"
    COMPLETED = "completed"


class BlockKind(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    FOOTNOTE = "footnote"
    SPEAKER_TURN = "speaker_turn"
    TABLE_CAPTION = "table_caption"
    TABLE_HEADER = "table_header"
    TABLE_CELL = "table_cell"
    OTHER = "other"


class SpeakerRole(StrEnum):
    MANAGEMENT = "management"
    ANALYST = "analyst"
    OPERATOR = "operator"
    UNKNOWN = "unknown"


class SupportRelation(StrEnum):
    SUPPORTS = "supports"
    QUALIFIES = "qualifies"
    CONTRADICTS = "contradicts"
    ANALYST_ATTENTION = "analyst_attention"
    DENIES = "denies"
    BACKGROUND = "background"
    NON_ANSWER = "non_answer"


class ImportanceBand(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNRESOLVED = "unresolved"


class RightsStatus(StrEnum):
    ALLOWED = "allowed"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class SourceFidelity(StrEnum):
    NATIVE_TEXT = "native_text"
    VERIFIED_RENDER = "verified_render"
    VISUAL_CHECK_REQUIRED = "visual_check_required"
    OCR_UNVERIFIED = "ocr_unverified"


class Issuer(StrictModel):
    issuer_id: UUID
    cik: Cik
    legal_name: str
    valid_from: date | None = None
    valid_to: date | None = None


class EarningsEvent(StrictModel):
    event_id: UUID
    issuer_id: UUID

    fiscal_year: int | None = None
    fiscal_quarter: int | None = Field(default=None, ge=1, le=4)
    period_start: date | None = None
    period_end: date | None = None

    first_public_at: datetime | None = None
    sec_accepted_at: datetime | None = None
    call_at: datetime | None = None

    # The analysis must not see later corrections/revisions.
    as_of: datetime


class SourceDocument(StrictModel):
    document_id: UUID
    event_id: UUID
    issuer_id: UUID
    role: DocumentRole

    original_url: HttpUrl
    evidence_url: HttpUrl | None = None

    accession: str | None = None
    sec_document_name: str | None = None
    exhibit_number: str | None = None
    exhibit_description: str | None = None

    public_available_at: datetime | None = None
    retrieved_at: datetime

    redistribution_status: RightsStatus = RightsStatus.UNKNOWN
    rights_basis: str | None = None
    rights_checked_at: datetime | None = None


class DocumentVersion(StrictModel):
    version_id: UUID
    document_id: UUID

    raw_sha256: Sha256
    canonical_sha256: Sha256

    parser_name: str
    parser_version: str
    canonicalizer_version: str

    fidelity: SourceFidelity
    supersedes_version_id: UUID | None = None


class DocumentBlock(StrictModel):
    block_id: UUID
    version_id: UUID
    ordinal: int = Field(ge=0)
    kind: BlockKind

    # Unicode code-point offsets into the document canonical text.
    start_cp: int = Field(ge=0)
    end_cp: int = Field(gt=0)
    text: str

    section_path: tuple[str, ...] = ()
    analysis_included: bool = True

    speaker_name_raw: str | None = None
    speaker_name_normalized: str | None = None
    speaker_role: SpeakerRole | None = None
    speaker_affiliation: str | None = None

    page: int | None = Field(default=None, ge=1)
    bbox: tuple[float, float, float, float] | None = None

    table_id: str | None = None
    table_row: int | None = None
    table_column: int | None = None
    table_header_path: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_offsets(self) -> "DocumentBlock":
        if self.end_cp <= self.start_cp:
            raise ValueError("block end_cp must be greater than start_cp")
        return self


class EvidenceSpan(StrictModel):
    evidence_id: UUID
    version_id: UUID
    block_id: UUID

    start_cp: int = Field(ge=0)
    end_cp: int = Field(gt=0)
    quote_text: str

    prefix: str = ""
    suffix: str = ""

    source_hash: Sha256

    page: int | None = Field(default=None, ge=1)
    bbox: tuple[float, float, float, float] | None = None

    original_url: HttpUrl
    evidence_url: HttpUrl | None = None


class Claim(StrictModel):
    claim_id: UUID
    event_id: UUID

    # Analytical paraphrase; never presented as a quotation.
    claim_text: str

    issuer_scope: str | None = None
    business_segment: str | None = None
    geography: str | None = None
    time_horizon: str | None = None

    observed_vs_forward: Literal[
        "observed", "forward_looking", "mixed", "unknown"
    ] = "unknown"

    direction: Literal[
        "positive", "negative", "mixed", "neutral", "unknown"
    ] = "unknown"


class ClaimEvidenceLink(StrictModel):
    claim_id: UUID
    evidence_id: UUID
    relation: SupportRelation

    # This is a review/model label, not automatically a calibrated probability.
    support_label: Literal[
        "accepted", "rejected", "needs_review"
    ]

    rationale: str | None = None


class ThemeDefinition(StrictModel):
    theme_id: str
    codebook_version: str
    parent_theme_id: str | None = None

    label: str
    definition: str

    inclusion_rules: tuple[str, ...] = ()
    exclusion_rules: tuple[str, ...] = ()
    positive_examples: tuple[str, ...] = ()
    negative_examples: tuple[str, ...] = ()


class ThemeAssignment(StrictModel):
    assignment_id: UUID
    event_id: UUID
    claim_id: UUID
    theme_id: str
    codebook_version: str

    assignment_status: Literal[
        "accepted", "rejected", "unknown_novel", "needs_review"
    ]

    run_id: UUID
    model_id: str | None = None
    prompt_version: str | None = None


class ImportanceComponent(StrictModel):
    name: Literal[
        "magnitude",
        "guidance_strategy",
        "persistence",
        "novelty",
        "specificity",
    ]
    value: int | None = Field(default=None, ge=0, le=3)
    evidence_ids: tuple[UUID, ...] = ()
    rationale: str


class ThemeScore(StrictModel):
    score_id: UUID
    event_id: UUID
    theme_id: str
    codebook_version: str

    components: tuple[ImportanceComponent, ...]
    importance_band: ImportanceBand

    # Optional machine-computed diagnostics; do not over-display precision.
    importance_observed: float | None = Field(default=None, ge=0, le=1)
    importance_min: float = Field(ge=0, le=1)
    importance_max: float = Field(ge=0, le=1)
    observed_weight: float = Field(ge=0, le=1)

    management_turns: int = Field(ge=0)
    qa_turns: int = Field(ge=0)
    analyst_questions: int = Field(ge=0)

    evidence_adequacy: Literal[
        "adequate", "partial", "inadequate"
    ]

    run_id: UUID


class ProcessingCoverage(StrictModel):
    event_id: UUID
    document_id: UUID | None = None
    state: ProcessingState

    expected_sources: int = Field(ge=0)
    acquired_sources: int = Field(ge=0)
    parsed_sources: int = Field(ge=0)
    completed_sources: int = Field(ge=0)

    unavailable_sources: int = Field(ge=0)
    restricted_sources: int = Field(ge=0)
    failed_sources: int = Field(ge=0)

    reason: str | None = None


def sha256_text(text: str) -> str:
    """SHA-256 over the exact UTF-8 encoding of canonical text."""
    return sha256(text.encode("utf-8")).hexdigest()


def validate_evidence_span(
    *,
    canonical_text: str,
    version: DocumentVersion,
    block: DocumentBlock,
    span: EvidenceSpan,
) -> None:
    """
    Deterministic acceptance checks for a canonical evidence quotation.

    Semantic support and source fidelity are intentionally checked elsewhere.
    """
    actual_hash = sha256_text(canonical_text)

    if actual_hash != version.canonical_sha256:
        raise ValueError("canonical document hash mismatch")

    if actual_hash != span.source_hash:
        raise ValueError("evidence source hash mismatch")

    if span.version_id != version.version_id:
        raise ValueError("evidence points at wrong document version")

    if span.block_id != block.block_id:
        raise ValueError("evidence points at wrong block")

    if not (
        block.start_cp
        <= span.start_cp
        < span.end_cp
        <= block.end_cp
    ):
        raise ValueError("evidence span crosses its block boundary")

    exact_slice = canonical_text[span.start_cp:span.end_cp]

    if exact_slice != span.quote_text:
        raise ValueError(
            "quotation is not an exact canonical source slice"
        )

    if canonical_text[block.start_cp:block.end_cp] != block.text:
        raise ValueError("block text does not match canonical source")


IMPORTANCE_WEIGHTS: dict[str, float] = {
    "magnitude": 0.35,
    "guidance_strategy": 0.25,
    "persistence": 0.15,
    "novelty": 0.15,
    "specificity": 0.10,
}


def calculate_importance(
    components: tuple[ImportanceComponent, ...],
) -> tuple[float | None, float, float, float]:
    """
    Return:
      observed-renormalized score,
      lower bound with unknowns=0,
      upper bound with unknowns=1,
      observed weight.
    """
    by_name = {component.name: component for component in components}

    weighted_observed = 0.0
    observed_weight = 0.0
    unknown_weight = 0.0

    for name, weight in IMPORTANCE_WEIGHTS.items():
        component = by_name.get(name)

        if component is None or component.value is None:
            unknown_weight += weight
            continue

        normalized = component.value / 3.0
        weighted_observed += weight * normalized
        observed_weight += weight

    observed_score = (
        weighted_observed / observed_weight
        if observed_weight > 0
        else None
    )

    lower = weighted_observed
    upper = weighted_observed + unknown_weight

    return observed_score, lower, upper, observed_weight


def evidence_route(
    base_url: str,
    evidence_id: UUID,
) -> str:
    """
    Runnable URL construction for the *proposed* application viewer.
    This does not claim that the viewer is already deployed.
    """
    return f"{base_url.rstrip('/')}/evidence/{evidence_id}"


def export_theme_scores(
    scores: list[ThemeScore],
    output_path: Path,
) -> None:
    """
    Polars-only analytical export. No pandas conversion.
    """
    rows: list[dict[str, object]] = []

    for score in scores:
        rows.append(
            {
                "event_id": str(score.event_id),
                "theme_id": score.theme_id,
                "codebook_version": score.codebook_version,
                "importance_band": score.importance_band.value,
                "importance_observed": score.importance_observed,
                "importance_min": score.importance_min,
                "importance_max": score.importance_max,
                "observed_weight": score.observed_weight,
                "management_turns": score.management_turns,
                "qa_turns": score.qa_turns,
                "analyst_questions": score.analyst_questions,
                "evidence_adequacy": score.evidence_adequacy,
                "run_id": str(score.run_id),
            }
        )

    (
        pl.DataFrame(rows)
        .sort(["event_id", "theme_id"])
        .write_parquet(output_path)
    )
```

Pydantic's current v2 documentation explicitly supports strict versus coercive modes and JSON Schema generation, which makes it a good fit for stable contracts shared with structured inference. citeturn22view4 Strict domain models are preferable here because silently coercing IDs, dates, or scores makes provenance failures harder to diagnose.

For inference, define a much smaller model-facing schema than the database schema. For example:

```python
class CandidateClaimOutput(StrictModel):
    claim_text: str
    evidence_candidate_ids: tuple[str, ...]
    candidate_theme_ids: tuple[str, ...]
    observed_vs_forward: Literal[
        "observed", "forward_looking", "mixed", "unknown"
    ]
    uncertainty: Literal["low", "medium", "high"]
```

The prompt receives only untrusted source content plus immutable candidate IDs. The model cannot invent offsets and should have no filesystem/network/tool authority. Document text is explicitly delimited as **data, not instructions**. Current vLLM structured-output support makes local constrained inference technically feasible; nevertheless, every returned object still goes through Pydantic and evidence resolution. citeturn20view0

PydanticAI can wrap this interaction if provider portability materially reduces code, but the models above should remain in `earnings-core`, not depend on the agent library. citeturn20view1 DSPy should be introduced only after the benchmark exists, so its optimizers have a meaningful objective. citeturn8search14 LangGraph should be introduced only if explicit Python state transitions become insufficient for pause/resume or human checkpoints. citeturn20view2

The persistence layout should be simple:

```text
data/
  raw/
    sha256/ab/cd/<raw_hash>
  canonical/
    <document_version_id>.txt
  manifests/
    acquisitions.parquet
    documents.parquet
    versions.parquet
    blocks.parquet
    evidence.parquet
  analytics/
    claims.parquet
    theme_assignments.parquet
    theme_scores.parquet
```

A transactional SQLite database can own state-machine transitions and uniqueness constraints locally, while Parquet remains the analytical interchange format consumed with Polars. A larger deployment can replace the state database without changing the domain contracts.

Each computational cache key should include every material input:

```text
raw_hash
parser_version
canonicalizer_version
analysis_mask_version
codebook_version
model/checkpoint identifier or hash
inference-engine version
prompt hash
decoding parameters
retrieval/index version
ranking-rubric version
```

Changing only the codebook should not force re-download or re-parse. Changing only the ranker should not force re-inference of exact evidence. This is the practical payoff of modular provenance.

Default CI should run entirely from checked-in or locally generated fixtures. It should have no network dependency and no API keys. Tests should cover byte/hash reproducibility, canonicalization golden files, evidence invariants, wrong-version rejection, repeated-text resolution, table-cell boundaries, point-in-time filtering, and idempotent resumability.

## Evaluation plan and staged roadmap

The benchmark should be **event-bundle based**, not a random sample of paragraphs. Each benchmark unit contains the expected source manifest for one issuer/event, its main 8-K, relevant earnings-release exhibit(s), transcript where lawfully available, revisions, and annotation.

Sampling should deliberately span:

- several sectors and issuer sizes,
- calendar and non-calendar fiscal years,
- HTML and awkward/malformed layouts,
- table-heavy and narrative releases,
- prepared remarks plus complicated Q&A,
- common themes and rare severe themes,
- no-theme documents,
- multiple EX-99 attachments,
- 8-K/A/corrections,
- inaccessible/restricted transcript cases,
- parsing failures.

A **20–40-document pilot** is enough to expose taxonomy ambiguity, source-discovery mistakes, parser defects, speaker-role problems, schema deficiencies, prompt failures, and gross differences between model/chunk strategies. It is not enough to estimate stable rare-theme recall, sector prevalence, source-selection bias, or reliable ranker generalization. Those require a larger event-level validation set.

Annotation should be independent before adjudication. Annotators label:

`event linkage → document role → exact evidence → atomic claim → speaker/entity/period → support relation → theme(s) → importance components → pairwise ranking`.

Measure agreement rather than adjudicating silently. Some importance differences will be genuinely ambiguous; the benchmark should preserve that information as ties/distributions where appropriate.

Split by **issuer and time**, with all copies/revisions and the full event bundle assigned to the same split. A repeated release appearing on both EDGAR and the issuer site may never straddle train/test. A corrected future transcript must not leak into a prospective test instance. Codebook discovery must occur only on the training/discovery partition when evaluating a prospective fixed-codebook system.

Recent benchmarks reinforce the importance of hard negative design. FinRank deliberately includes confusable passages from other periods and issuers and reports substantial accuracy degradation compared with random negatives; an earnings benchmark should do the same. citeturn17academia37

The following are **proposed acceptance gates, not validated results**:

| Layer | Metric | Proposed gate |
|---|---|---:|
| Expected-source accounting | Accessible expected event bundles with a terminal state | ≥ 99% |
| Earnings-release identification | Precision | ≥ 99.5% |
| Earnings-release identification | Recall | ≥ 98% |
| Accepted quote exactness | Deterministic canonical invariant | **100%** |
| Native-source fidelity | Audited exact/faithful blocks | ≥ 99.5% |
| Critical numeric/table cells | Sign/unit/scale/header correctness | ≥ 99.9% |
| Known speaker-role attribution | Macro F1 | ≥ 0.97 |
| Evidence extraction | Span/evidence recall | ≥ 0.95 |
| Semantic support | Precision on accepted material claims | ≥ 0.97 |
| Citation completeness | Substantive claims with accepted evidence | ≥ 0.98 |
| Theme classification | Micro F1 | ≥ 0.90 |
| Theme classification | Macro F1 | ≥ 0.85 |
| Rare critical theme detection | Recall | ≥ 0.95 |
| Passage resolver | Correct exact occurrence | ≥ 99% |
| Passage resolver | Wrong-occurrence rate | **0 on release gate set** |
| Ranking | Expert pairwise agreement | ≥ 0.80 |
| Ranking | nDCG@5 | ≥ 0.90 |
| Abstaining system | Retained useful coverage at quality target | ≥ 0.80 |
| Run stability | Material-theme/rank changes across repeated runs | Report and gate after pilot |

The 100% accepted-quote exactness target is realistic because it is a deterministic invariant, not a model metric. The system can reject malformed evidence. But rejection is not a complete solution: retained coverage and theme recall ensure that “reject everything” fails the benchmark.

Source fidelity needs a different metric. For native HTML, sample rendered source against canonical blocks, including Unicode, signs, superscripts, footnotes, and table headings. For PDF, perform page/region visual checks. For OCR fallback, report character/word error and audited factual/numeric correctness separately. A SHA-256 hash proves which bytes or canonical text were processed; it does **not** prove that the parser interpreted them correctly.

Theme performance should report micro-F1, macro-F1, per-theme precision/recall, hierarchical consistency, unknown/novel detection, and recall of rare high-importance themes. Exact multilabel subset accuracy is useful but too harsh to stand alone.

Support evaluation needs difficult cases:

> analyst question → no management confirmation  
> management denial → do not convert to positive event  
> qualified statement → qualification required  
> wrong fiscal year → reject  
> right sentence, wrong issuer → reject  
> right issuer, corrected future version → reject in point-in-time mode  
> causal paraphrase unsupported by source → reject

For ranking, ordinary accuracy is inadequate. Collect adjudicated pairwise preferences, ties, and importance components; report pairwise agreement, nDCG, critical-theme recall, and cluster-bootstrap confidence intervals with **issuer/event** rather than individual quotation as the sampling unit.

The experimental matrix should include controlled ablations:

| Experiment | Question |
|---|---|
| Whole event vs exhaustive chunking | Does long context improve or harm theme recall? |
| Exhaustive chunking vs retrieval-only | How many themes, especially single mentions, does top-*k* lose? |
| BM25/TF-IDF vs dense vs hybrid/reranked | Which retrieval method works on hard issuer/period negatives? |
| Pointer evidence vs generated-then-verified quote | Does pointer selection improve exactness/support/latency? |
| Deductive vs inductive vs hybrid codebook | Which best balances stability and novelty? |
| Release only vs release + transcript | What incremental themes and bias does transcript coverage create? |
| No dedup vs disclosure-level dedup | How badly do duplicate source copies inflate salience? |
| Equal components vs provisional importance weights | How rank-sensitive are conclusions? |
| Rubric vs pairwise model vs supervised LTR | Does complexity actually improve expert agreement? |
| Explicit Python workflow vs LangGraph | Is framework durability worth added surface area? |
| Single structured model vs multi-agent | Does agent decomposition improve quality enough to justify cost/variance? |
| Local baseline checkpoints | Which local model actually wins this task? |
| Optional hosted ceiling | Only after explicit budget/authorization |

The long-context experiment is important rather than ceremonial: controlled research has demonstrated position-dependent degradation even in models nominally supporting long contexts. citeturn16view4

A staged roadmap follows naturally.

**Foundation stage:** implement source manifests, identifiers, direct SEC traversal, rights states, immutable raw storage, canonical HTML parsing, exact evidence primitives, and a basic evidence viewer. No LLM is required to prove this layer.

**Pilot stage:** annotate 20–40 diverse documents/event bundles. Add dictionary/TF-IDF theme baselines and a local structured-output model. Keep event consolidation human-reviewable. Compare pointer evidence against generated-then-verified evidence.

**Validation stage:** enlarge the benchmark sufficiently for rare-theme and ranking judgments; freeze train/test by issuer/time; calibrate codebook and ranking; add transcript coverage analysis; benchmark local checkpoints. Only here should DSPy optimization or a learned ranker become plausible.

**Production stage:** lock versions, activate selective reprocessing, coverage dashboards, review queues, run-to-run stability reports, and offline replay. Promotion of any model/parser requires the full acceptance suite.

**Optional quality ceiling:** a hosted frontier model may be run on a frozen subset only after explicit authorization and a budget cap. The present research does **not** authorize it. The hosted result is a ceiling/ablation, never a production dependency.

## Worked example

A small real example can be constructed from NVIDIA's second-quarter fiscal 2027 earnings release dated August 26, 2026. NVIDIA's issuer-hosted release reports that the quarter ended July 26, 2026 and headlines total revenue and Data Center revenue. citeturn23search0turn23search8 More importantly for acquisition validation, the same release is directly accessible in EDGAR as an **EX-99.1** document at accession-path `000104581026000073`, giving an actual SEC exhibit rather than merely an issuer press page. citeturn23search12

Verified primary sources:

- SEC EX-99.1: `https://www.sec.gov/Archives/edgar/data/1045810/000104581026000073/q2fy27pr.htm` citeturn23search12
- NVIDIA issuer release: `https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-second-quarter-fiscal-2027` citeturn23search0

The two URLs represent separate source copies of substantially the same published release. In production they should retain separate provenance and likely resolve to one disclosure-content group after content comparison, rather than being counted twice.

I did **not** canonicalize these pages through the proposed implementation during this research session, so the example does not invent character offsets or application-viewer links. Locations below use verifiable document structure: the EX-99.1 headline bullet list. No matched issuer-published transcript with sufficiently reviewed access/rights was established for this worked example, so no transcript evidence is added.

**Normalized evidence records**

| Evidence ID | Exact short quotation | Source/location | Speaker | Exactness status | Passage-link status |
|---|---|---|---|---|---|
| `E1` | “Revenue of $96.2 billion, up 106% from a year ago” | SEC EX-99.1, title-area first bullet | Issuer-written release; no individual speaker | Exact against retrieved SEC HTML text | Original source verified; no durable app viewer claimed |
| `E2` | “Data Center revenue of $89.0 billion, up 117% from a year ago” | SEC EX-99.1, title-area second bullet | Issuer-written release; no individual speaker | Exact against retrieved SEC HTML text | Original source verified; no durable app viewer claimed |

Both quotations appear in the SEC-indexed exhibit and are corroborated by NVIDIA's issuer-hosted release. citeturn23search12turn23search0 Cross-site duplication here is provenance corroboration that the same release was published in two locations; it should not be interpreted as two independent business disclosures.

A derived calculation can be stored separately:

\[
89.0 / 96.2 \approx 92.5\%
\]

Thus, using the two disclosed headline revenue figures, Data Center revenue is approximately 92.5% of total reported quarterly revenue. That number is a **derived calculation**, not a quotation and not wording attributed to NVIDIA. The operands come from `E1` and `E2`. citeturn23search12turn23search0

**Illustrative analyst-facing view**

The rankings below demonstrate how the proposed rubric would represent the evidence. They are **illustrative applications of an unvalidated ranking rubric**, not model outputs, benchmark results, or claims that the proposed weights are optimal.

| Rank | Theme / hierarchy | Supported claim | Importance | Why | Salience | Confidence / coverage | Evidence | Source location / links |
|---:|---|---|---|---|---|---|---|---|
| 1 | Growth → Data Center expansion | NVIDIA disclosed $89.0B of quarterly Data Center revenue and 117% YoY growth. | **High, illustrative** | Very large disclosed scale and growth; derived share of total revenue ≈92.5% reinforces firm-level relevance, but is stored as calculation, not quote. | Very high headline prominence; no full-document mention count calculated | Evidence exact for release; event coverage partial because transcript not included; classification judgment not probabilistically calibrated | `E2` | SEC EX-99.1, second headline bullet; original link verified; app deep-link not built |
| 2 | Financial performance → Company-wide revenue growth | NVIDIA disclosed $96.2B quarterly revenue, 106% above the prior year. | **High, illustrative** | Firm-wide financial magnitude and exceptional disclosed year-over-year change | Very high headline prominence; no numeric salience score calculated | Evidence exact for release; partial event-source coverage | `E1` | SEC EX-99.1, first headline bullet; original link verified; app deep-link not built |

The source describes both figures as headline results for the quarter ended July 26, 2026. citeturn23search0turn23search8 The example intentionally does **not** infer legal materiality, causality, future growth, customer demand, or a strategic decision from those two quotations.

A machine-readable representation would remain normalized rather than copying the quote into every theme row:

```json
{
  "claims": [
    {
      "claim_id": "C1",
      "claim_text": "NVIDIA disclosed $89.0B of Data Center revenue, up 117% year over year.",
      "evidence_ids": ["E2"],
      "theme_ids": ["growth.data_center"]
    },
    {
      "claim_id": "C2",
      "claim_text": "NVIDIA disclosed $96.2B of total quarterly revenue, up 106% year over year.",
      "evidence_ids": ["E1"],
      "theme_ids": ["financial_performance.revenue_growth"]
    }
  ],
  "derived_values": [
    {
      "name": "data_center_share_of_total_revenue",
      "expression": "89.0 / 96.2",
      "value": 0.925156,
      "input_evidence_ids": ["E1", "E2"],
      "is_quote": false
    }
  ]
}
```

This tiny example also illustrates why exhibit discovery should use content rather than heuristics. In this event the actual SEC earnings release **does** happen to be EX-99.1. citeturn23search12 The implementation must not generalize from that success to “EX-99.1 always equals earnings release”—precisely the kind of rule that should be tested on the benchmark.

## Reproducibility appendix and final recommendation

The literature and engineering search was conducted through **September 22, 2026**, emphasizing primary sources, official documentation, maintained project documentation, original research papers/preprints, SEC materials, and original issuer documents. Post-2023 work was prioritized where it bears directly on evidence retrieval, long-context reliability, financial QA, and structured inference; older standards such as W3C Web Annotation remain relevant because the passage-linking problem is fundamentally a provenance/selector problem rather than a model-generation problem.

Important evidence-strength distinctions are:

| Source / result | Status | What it can support |
|---|---|---|
| SEC EDGAR API documentation | Official primary documentation | Current access/discovery architecture, submissions history and bulk data citeturn16view1 |
| SEC Form 8-K | Official primary form | Item 2.02 and exhibit obligations; Item 9.01 context citeturn12view0turn12view1 |
| EdgarTools docs | Maintainer documentation | API behavior/capability claims, including narrower earnings-detection semantics; **not independent accuracy validation** citeturn16view2 |
| W3C Web Annotation Recommendation | Standards primary source | Text quote/position selector semantics citeturn16view3 |
| Lost in the Middle, TACL 2024 | Peer-reviewed research | Long-context position-sensitivity on its evaluated QA/retrieval tasks, not earnings extraction directly citeturn16view4 |
| FinanceBench 2023 | Authors' benchmark/preprint | Financial QA/evidence failure modes; models/results are not theme-ranking results citeturn17academia38 |
| FinRank 2026 | Recent preprint | Provenance-sensitive financial retrieval and hard-negative results; not yet evidence of earnings-theme extraction quality citeturn17academia37 |
| BERTopic paper | Authors' topic-model benchmark | Topic-discovery method; no earnings codebook validation citeturn17academia40 |
| vLLM docs | Maintainer documentation | Current structured-output implementation capabilities, not semantic accuracy citeturn20view0 |
| Pydantic docs | Maintainer documentation | Current schema/validation capabilities citeturn22view4 |
| DSPy paper/docs | Research + maintainer docs | Program optimization concept; no demonstrated earnings advantage here citeturn8search14turn8search3 |
| TypeSafe/Jev | Vendor documentation/benchmarks | Candidate capabilities and vendor claims only; launched Sept. 15, 2026 and not independently validated on this task citeturn22view3 |
| NVIDIA EX-99.1 / issuer release | Original disclosure | Worked-example evidence citeturn23search12turn23search0 |

**Source register for the production corpus**

| Source family | Access and expected role | Historical depth / coverage | Rights/redistribution treatment | Production decision |
|---|---|---|---|---|
| SEC `data.sec.gov` submissions | No-key filer-history discovery; current plus linked historical records; bulk archive available citeturn16view1 | Broad SEC history through referenced submission files; exact document availability still accession-specific | Public access does not justify assuming every issuer-authored exhibit is unrestricted for arbitrary redistribution | **Required** |
| SEC Archives accession documents | Primary 8-K and actual exhibits | Filing-specific | Preserve source; short evidence display under applicable policy; review redistribution separately | **Required** |
| EdgarTools | Open-source convenience adapter around SEC workflows; documented 8-K item/press-release/earnings helpers citeturn16view2 | Project documentation describes broad historical SEC access | Software rights separate from underlying filing content | **Optional adapter** |
| Issuer IR releases | Useful source copy and sometimes earliest public release | Varies by issuer | Terms/redistribution status stored per source | **Preferred secondary provenance** |
| Issuer IR transcripts | Best free transcript source where actually published | Highly issuer-dependent | Must review access/redistribution terms; public visibility alone is not enough | **Conditional** |
| Free third-party transcript sites | Potential gap filler | Variable | Do not assume scraper availability confers rights | **Not required path; rights review first** |
| Issuer webcast/audio | Fallback where access/use permits | Variable | Audio and derived transcript rights reviewed separately | **Explicit fallback only** |

SEC primary links used in the design are the [EDGAR Application Programming Interfaces documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) and the [official Form 8-K](https://www.sec.gov/files/form8-k.pdf). citeturn16view1turn23search1 EdgarTools' relevant maintained documentation is its [8-K guide](https://edgartools.readthedocs.io/en/latest/eightk-filings/). citeturn16view2 Passage-selection semantics come from the [W3C Web Annotation Data Model](https://www.w3.org/TR/annotation-model/). citeturn16view3

The current structured-output baseline should use [Pydantic](https://pydantic.dev/docs/validation/dev/get-started/) and, when local LLM serving is required, evaluate [vLLM structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/). citeturn22view4turn20view0 PydanticAI, LangGraph, and DSPy are optional integration/optimization layers rather than domain dependencies. citeturn20view1turn20view2turn8search14

License verification should occur at the **exact lockfile/model revision**, not at family-name level. This research verified that Qwen's official Qwen2.5 release identifies most models as Apache 2.0 while calling out exceptions; that is enough to shortlist specific Apache-licensed sizes, not enough to assume any future Qwen checkpoint has identical terms. citeturn18search27 EdgarTools documentation describes the project as free/open source but, independently of its software license, its pandas-centric interfaces should remain behind the ingestion adapter boundary. citeturn3view1turn3view0 vLLM/Pydantic/framework licenses should be rechecked directly against the exact repository tags used before a production software bill of materials is frozen.

Five different rights/cost concepts should remain separate in the manifest:

| Dimension | Example |
|---|---|
| Software license | License governing parser/inference/workflow code |
| Model-weight license | Terms governing a downloaded checkpoint |
| Data-access right | Whether the system may retrieve a filing/transcript/audio source |
| Redistribution permission | Whether raw/canonical source material may be redistributed or exposed outside the permitted application context |
| Compute cost | Local hardware/energy or optional hosted inference charge |

“Free to download” in one column never fills in the others.

The largest unresolved empirical choices are consequently **not architectural mysteries**. They are testable questions: which local checkpoint achieves acceptable evidence/theme performance; whether sentence or clause pointer granularity gives the best precision/recall; how much transcript inclusion changes conclusions; how much retrieval-only extraction misses; and whether expert pairwise rankings justify a learned ranker.

The most important outstanding research limitation is the absent seed-note content. Because `earnings-ingestion.md`, `earnings-themes.md`, and `AGENTS.md` were unavailable to the file-retrieval layer, this report cannot identify contradictions between their exact wording and this recommendation, cannot verify their linked citations beyond those independently surfaced here, and cannot determine whether proposed repository structures or experiments in those files have already been implemented. No claim above relies on pretending otherwise.

**Recommended first implementation**

Build the first implementation in this order:

**SEC event bundle first.** Start from a configurable, point-in-time CIK universe; enumerate complete 8-K/8-K/A accessions; download primary documents and every relevant attachment with an identifying SEC client, caching and resumability; explicitly classify exhibits. Use EdgarTools only as a side-by-side adapter/diagnostic. SEC's no-key submissions APIs, historical file pointers, and bulk data make the direct path viable without a paid filing feed. citeturn16view1

**Canonical evidence second.** Implement immutable raw objects, HTML/DOM canonicalization, typed blocks/cells, source maps, SHA-256 versions, Unicode code-point half-open spans, exact/prefix/suffix selectors, and the application evidence-viewer contract. A theme pipeline should not go into production before accepted quotes can be deterministically resolved and highlighted. The W3C selector model provides a mature conceptual foundation for this layer. citeturn16view3

**Human-coded baseline third.** On 20–40 deliberately difficult event documents, annotate release identity, claims, evidence, themes, and importance components. Build keyword/regex/TF-IDF baselines and manual ranking before introducing model complexity.

**Evidence-first local semantic extraction fourth.** Exhaustively process structure-aware chunks using a pinned locally runnable instruction model with constrained structured outputs. Make it return evidence IDs and typed attributes, not quotations or character counts. Consolidate at event level. Keep retrieval as a supporting capability, not the gate through which every theme must pass. Long-context research and recent provenance-sensitive finance benchmarks both argue against assuming one large prompt or top-*k* retrieval is exhaustive. citeturn16view4turn17academia37

**Hybrid codebook fifth.** Freeze stable human-approved theme IDs for prospective evaluation; route unmatched supported claims to a novelty queue, optionally grouped using embeddings/BERTopic. Do not let clustering rename historical themes automatically. citeturn17academia40

**Interpretable ranking sixth.** Start with anchored business-significance components and provisional transparent weights; report salience and prevalence separately; collect expert pairs and learn/tune ranking only if held-out performance supports doing so.

**Transcripts seventh.** Add issuer-by-issuer transcript ingestion only after the rights/source register and speaker model are working. Quantify transcript availability and compare release-only versus release-plus-transcript results before publishing sector prevalence based on calls.

**Framework optimization last.** Add DSPy only when there is a frozen objective to optimize, LangGraph only when explicit orchestration demonstrably becomes inadequate, and a multi-agent design only if a controlled ablation beats the simpler system on quality enough to offset latency, inference use, reproducibility, and maintenance. citeturn8search14turn20view2 Jev should remain an optional future benchmark for structured classification/ranking after independent validation and explicit spending authorization; its present evidence is vendor-generated and the product was only released into early access on September 15, 2026. citeturn22view3

That sequence prioritizes the failure modes that can silently invalidate an otherwise impressive NLP system: wrong accession, wrong exhibit, wrong period, parser corruption, fabricated or unresolvable evidence, and unsupported ranking.

**Evidence that would change this recommendation**

The recommendation should change if controlled experiments show any of the following.

A full-document local model achieves statistically and operationally equivalent or better **rare-theme recall, semantic support, and citation completeness** than exhaustive structure-aware chunking across the held-out event benchmark, with acceptable latency/memory. That would justify simplifying the extraction hierarchy. Current long-context evidence gives no basis for assuming that result in advance. citeturn16view4

A retrieval-only pipeline attains essentially complete critical-theme recall—including important single mentions—and passes issuer/period hard-negative tests while materially lowering inference cost. That would justify replacing exhaustive scanning. FinRank's current evidence makes this an empirical hurdle rather than the default assumption. citeturn17academia37

A supervised domain classifier trained on the project's own adjudicated corpus materially exceeds evidence-first few-shot/local-LLM classification in macro-F1, novel-theme handling, stability, and maintenance burden. Once sufficient labels exist, this is quite plausible and would favor a smaller discriminative model for stable themes.

Expert pairwise rankings show that the proposed business-significance rubric is systematically misordered, or learned weights generalize substantially better across held-out issuers and time. In that case the rubric should be revised or replaced. The provisional weights should never be defended merely because they were written down first.

Transcript ablation shows that calls contribute little unique theme information or introduce unacceptable selection bias for the intended population. In that case transcripts should become a specialized secondary corpus rather than part of the default event bundle. Conversely, if they materially improve critical-theme recall, transcript acquisition deserves higher priority.

A parser/document-understanding model demonstrably improves source fidelity on a clearly defined difficult subset—such as malformed tables or inaccessible PDF layouts—without degrading exact source mapping. That would justify model-based document understanding for that subset. It would not justify replacing reliable native HTML parsing wholesale.

EdgarTools, after benchmark testing, proves complete for the target filing/exhibit cases and can provide a clean non-pandas boundary without hidden conversions. That would justify giving it more acquisition responsibility. Its current documented convenience semantics are too narrow to presume this. citeturn16view2turn3view0

Independent task-specific evidence shows Jev or another specialized structured-decision model materially improves classification/ranking quality, calibrated abstention, latency, and cost—and its access/licensing terms fit the project—with explicit authorization for any billable service. That would justify an optional adapter. Current Jev evidence is too new and too vendor-controlled to do so. citeturn22view2turn22view3

Most importantly, the recommendation should change wherever the project's **own adjudicated earnings benchmark** contradicts adjacent literature. FinanceBench, FinRank, BERTopic, and long-context studies are valuable priors, not substitutes for evaluating the actual unit of concern: an issuer's earnings event, its correct source bundle, its supported themes, and the evidence-linked ranking delivered to an analyst. citeturn17academia38turn17academia37turn17academia40turn16view4