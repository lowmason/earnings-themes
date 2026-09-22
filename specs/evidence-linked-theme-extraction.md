# Evidence-linked theme extraction

> For agentic workers: REQUIRED NEXT SKILL: derive-roadmap — do not plan
> this spec directly and do not split it into per-subsystem plans.

This specification defines the method for extracting decision-useful themes from
firms' earnings disclosures with every theme bound to an exact, locatable span of
source text. It covers seven stages — acquisition and event resolution,
structure-aware canonicalization, evidence selection, deterministic span
verification, semantic support assessment, codebook construction and coding, and
coverage-aware aggregation — plus the evaluation design that decides whether any
of it works. Theme *importance ranking* is deliberately excluded and belongs to a
successor spec (see Out of scope). The required path uses free-to-access data and
open-weight, self-hosted models; no billable inference is required to run, test,
or reproduce any requirement here.

## Design provenance

This spec synthesizes `AGENTS.md` (the repository's binding working instructions)
and `docs/earnings-themes.md` (the supplied source note) with three independent
external reviews commissioned by `specs/earning-themes-prompt.md`.

**Locator scheme.** No decoupled methodology description exists for this system,
so the described method is the repository's own binding text: **`A §n`** cites
`AGENTS.md` by line-section, **`S`** cites `docs/earnings-themes.md`. The three
reviews are cited against the **research prompt's §1–8 spine**, because their own
headings are numbered inconsistently:

| Locator | File | Standing |
| --- | --- | --- |
| **RC** | `specs/earning-themes-review-claude.md` | Read the source files. Separates independently-evaluated results from vendor claims; strongest on rights, licensing, and verification dates. |
| **RX** | `specs/earning-themes-review-chtgpt.md` | **Reports that the source files were not retrievable in its session.** Not citable for what `AGENTS.md` or the source notes say; its ranking math and ablation design are the most rigorous of the three. |
| **RG** | `specs/earning-themes-review-gemini.md` | Most implementation-specific, least evidence-backed. Several load-bearing claims asserted without task evidence. |

**Adjudication status.** None of the three reviews was adjudicated. All are
independent first passes with no interactive push-back, so there are no
reviewer-side rejections to inherit and their absence is not agreement. The
adjudication was carried at synthesis time; every requirement below states its
verdict where it was not a plain accept.

**This spec amends binding instructions.** `CLAUDE.md` labels `AGENTS.md`
binding. Three requirements revise it. Where this spec and `AGENTS.md` conflict
on these three points, this spec governs:

| Amends | Binding text today | Direction |
| --- | --- | --- |
| `A §452` | "Begin with whole in-scope releases/transcripts when they fit the configured context budget." | **Inverted** by R10 — exhaustive structure-aware traversal becomes the default; whole-document becomes a measured ablation. |
| `A §728` | Adopts 20–40 hand-coded documents as the evaluation plan. | **Demoted** by R12 — a feasibility pilot, not a validation set. |
| `A §563` | Boilerplate "tag these spans and exclude them from headline prevalence." | **Mechanism supplied** by R3.4 — overlay masks that never mutate canonical text. |

**This spec supersedes** `AGENTS-jev-addendum.md` and
`specs/jev-integration-spec.md` on the required-path question only (R14.3). Those
documents remain as proposals for an optional, separately-authorized layer.

**Naming.** Filed as `evidence-linked-theme-extraction.md` rather than
`earning-themes.md` to avoid sitting one character from `docs/earnings-themes.md`.

## Problem

The binding instructions and the source note agree on the load-bearing
invariant — exactness is enforced by code, never by prompting and never by a
second model checking the first (`A §518`, `S` Stage 2) — and on the analytical
grain (`A §627`). They do not specify how evidence is selected, how repeated text
is disambiguated, how a reader reaches the quoted passage, how semantic support
is judged, or how exhaustive discovery is achieved. They also set a document-level
processing default that all three reviews independently contradict.

Four gaps make the current instructions unbuildable as written:

- **No evidence-selection mechanism.** `A §518` retains three designs for
  comparison but names no default, so there is nothing to build first.
- **No repeated-text mechanism.** `A §518` requires "a supported location, not an
  arbitrary first-match offset" and supplies no way to produce one.
- **The hash is treated as the integrity guarantee.** `A §480` binds evidence to a
  canonical hash. A hash proves *which* characters were processed; it cannot prove
  the parser read them correctly (RC §2, RX §7).
- **Whole-document processing is the stated default.** `A §452` begins with whole
  documents when they fit the context budget. Fitting in context does not imply
  complete extraction (RC §4, RX §4, RG §4).

## Core principle

**The model proposes; code disposes.** A model may select candidate evidence and
judge whether a span supports a claim. Only code decides whether a span is
exact, and only code materializes quoted text. No model output — however
well-typed, however confident, however cited — may patch wording, promote an
invalid span, waive the span check, or alter the codebook.

This principle already governs exactness (`A §518`). This spec extends it to
localization (R5), support (R8), and the boilerplate mask (R3.4).

## Requirements

### R1 — Acquisition and event resolution

**R1.1** Discover filings by enumerating a firm's full submission history and
traversing each accession's complete document and exhibit list. Never resolve an
earnings event by "most recent filing" or "first exhibit." *(chosen; RX §1, RC §1)*

**R1.2** Identify an earnings release by inspecting the exhibit index, exhibit
descriptions, the item text, and the exhibit content together. Do **not** rely on
a library's convenience flag: RC §1 verifies that the flag in the candidate
acquisition library requires both an Item 2.02 designation **and** a parseable
table in the exhibit, so narrative-only releases and alternative exhibit
numbering are silently missed. *(rejected: flag-based detection; RC §1)*

**R1.3** Retain the project-wide access policy of **2 requests/second shared
across all adapters and workers** (`A §58`). RC §1 and RG §1 report the source
permits up to 10 req/s; the stricter project default stands. Adopt the verified
access behavior: a descriptive User-Agent with a real contact is required,
its absence yields 403, and breach yields 429. Persistent 403 stops the run and
reports; identity is never rotated. *(accept facts, reject the higher rate)*

**R1.4** Maintain explicit per-document processing states — expected,
unavailable, restricted, acquired, parsed, partial, failed, completed,
completed-no-theme — as a table built **before** any aggregation. A table of
successful quotes cannot supply a denominator (`A §627`, RC §1).

**R1.5** Match events on issuer identity, fiscal period, period end, event date,
**and content**; never on ticker or calendar quarter alone. Keep acceptance time,
first public availability, call time, fiscal reporting period, and retrieval time
separately, preserving unknowns (RC §1, `A §480`).

### R2 — Transcripts as a rights-gated extension

**R2.1** Treat transcripts as an explicitly scoped extension, not part of the
core corpus. Free viewability does not confer redistribution rights; RC §1
verifies that a major free transcript source's terms prohibit scraping, and that
transcripts are generally absent from the filing system. Where terms forbid
redistribution, store evidence locators and locally-computed features — not
redistributed text. *(RC §1; serves the cost/rights non-negotiable, `A §58`)*

**R2.2** Any audio-derived transcription is labeled a separate, machine-generated
fallback and never presented as an original published transcript. RG §1's
proposed machine-transcribed dataset is **rejected as a default** because RG
concedes it lacks speaker diarization, which is fatal to the
management-versus-analyst split that `A §563` makes load-bearing. It is retained
as a candidate *(open — resolved by verification, not argument: its license and
its diarization fidelity are facts to check, discharged by V7)*.

**R2.3** Quantify missing-transcript coverage as a potential selection bias.
Absence of a transcript is an explicit `missing_reason`, never an implicit zero
(RC §1, `A §342`).

### R3 — Canonical representation

**R3.1** Canonicalize once — markup to text, Unicode and whitespace
normalization — **before** assigning any offset. Hash the canonical text with
SHA-256 over its UTF-8 bytes and persist the text, the hash, and the
canonicalization version (`A §480`).

**R3.2** Offsets are **Unicode code points**, zero-based, half-open `[start, end)`.
This restates `A §480` in the wording all three reviews converge on (RC §2, RX §2,
RG §2); it is the same convention, made explicit because the coordinate system
must survive the boundary between the analysis runtime and any browser-based
viewer, where a code-point contract is what keeps the two aligned.

**R3.3** A change to canonical text creates a new version. Never mutate text
beneath existing spans (`A §480`).

**R3.4** Boilerplate — safe-harbor language, non-GAAP disclaimers, repeated
legal text — is handled by **overlay masks computed against the canonical text**,
never by deleting or rewriting it. Masked spans are excluded from headline
prevalence and retained for audit. This supplies the mechanism `A §563` requires
but does not specify, and it is the only construction that satisfies both "apply
the same policy across comparison periods" and "do not invalidate offsets."
*(chosen; RC §2, RG §2 — amends `A §563`)*

**R3.5** A canonical hash proves which characters were processed. It does **not**
prove the parser interpreted them correctly. Require an independent fidelity
check on a sample: canonical blocks compared against rendered source, covering
Unicode, numeric signs, scale, superscripts, footnotes, and table headings.
*(chosen; RC §2, RX §7 — closes a gap in `A §480`)*

### R4 — Structure-aware parsing

**R4.1** Parse into typed structural elements — headings, paragraphs, list items,
sentences or clauses, speaker turns, table cells — each carrying a stable
identifier and a span in the canonical coordinate system. Naive text extraction
that flattens the document is insufficient: it destroys hierarchy, merges
footnotes into body text, and corrupts reading order in multi-column financial
tables (RG §2, RC §2). The specific parser is *(open — resolved by verification,
not argument: whether a candidate library's element classification is faithful on
this corpus is measured, discharged by V2)*.

**R4.2** **Quarantine table cells as a distinct evidence type.** Table-derived
figures are stored as cell evidence with their row, column, and header context,
and are never reassembled into a prose passage labeled verbatim. Narrative theme
extraction operates on narrative elements only. *(chosen; RC §2, RX §2, RG §2 —
absent from `AGENTS.md`; prevents a synthesized "quotation" that passes a
substring check but was never a contiguous sentence)*

**R4.3** Prefer native text extraction. Reserve optical character recognition for
image-only material, flag it as lower-fidelity, and never treat OCR-matched text
as a verified original quotation (RC §2, RG §2).

### R5 — Evidence selection

**R5.1** **Pointer selection is the default.** The model returns stable element
identifiers assigned in R4.1; code resolves them to canonical offsets and slices
the text. The model never returns character offsets and never returns the quoted
text as authoritative. *(chosen)*

RG §3 rejects pointer selection on the grounds that language models cannot
reliably compute character offsets in long contexts. That objection is
**adjudicated as not applicable**: it describes a design in which the model emits
integer offsets, which no review proposes and which R5.1 forbids. Under R5.1 the
model emits *enumerated identifiers* and code performs the identifier-to-offset
lookup, so the model's inability to count characters is designed around rather
than relied upon. *(rejected: RG §3's objection, on target-mismatch grounds)*

**R5.2** **Generate-then-verify is retained as a required comparison**, not
discarded. The model proposes text; deterministic code locates it in the
canonical source and materializes the span. Approximate matching may *locate* a
candidate but never *validates* one — a fuzzy score is neither proof of exactness
nor proof of support. Failure to resolve rejects the candidate; it never repairs
the wording. *(chosen as ablation; `A §518`, `S` Stage 2, RG §3, RX §3)*

**R5.3** Provider-native citations remain an optional third design behind an
adapter that maps returned citations into this project's coordinate system and
then passes the same local verifier. Provider citation indices are not assumed to
match this project's offsets. RC §3 verifies that one major provider's citation
feature returns an error when combined with structured output, forcing two
passes. *(open — resolved by verification, not argument: current provider
capability is a fact to re-check at adapter time, discharged by V3; `A §518`
explicitly warns against encoding an unverified permanent limitation)*

**R5.4** **Repeated text is disambiguated by surrounding context.** Where a
candidate string occurs more than once, the record carries a prefix and suffix
drawn from the canonical text sufficient to identify the intended occurrence.
This supplies the mechanism `A §518` requires when it forbids "an arbitrary
first-match offset." *(chosen; RG §3, RX §3)*

**R5.5** Noncontiguous evidence uses separate records. Never stitch spans or
insert ellipses into a record labeled verbatim (`A §518`).

### R6 — The exactness invariant

**R6.1** Before storage, before support judgment, and before export, every
accepted span satisfies:

```
0 <= start < end <= length(canonical_text)
quote_text == canonical_text[start:end]
stored_canonical_hash == sha256(utf8(canonical_text))
```

Validate identifiers, strict integer offsets, and hash equality as well as text
equality. A verbatim string found in the wrong document, speaker turn, or section
fails attribution and is rejected. *(binding already at `A §518`; restated because
R5, R7, and R8 all depend on it)*

**R6.2** Bound retries and usage. On exhaustion, drop the candidate and record the
rejection reason. Never patch, invent, or silently accept. Rejections stay
auditable. Zero retained quotes is not "no themes" and has no defined exactness
rate (`A §518`, `A §728`).

### R7 — Durable passage links

**R7.1** Every accepted span resolves to a link that opens the source document and
highlights the quoted passage, built from the exact text plus the R5.4 prefix and
suffix context. A link to a document's first page is not a citation (RG §3, RC §3,
RX §3).

**R7.2** Pair every such link with a stored immutable snapshot of the source
artifact. RC §3 verifies the highlighting mechanism is a draft standard, not a
ratified one, with uneven support that degrades to page-top on drift; the
snapshot is the fallback that keeps evidence reachable regardless. *(open —
resolved by verification, not argument: current support and degradation behavior
are facts to check, discharged by V5)*

### R8 — Semantic support

**R8.1** Exactness does not establish support. Assess separately whether the
verified span supports the specific claim under the specific theme definition —
the failure mode being a correctly-quoted phrase whose surrounding syntax
attributes it to a competitor, a prior period, or a negation (RG §3, `A §563`).

**R8.2** Use an open-weight entailment scorer as the primary signal with a
calibrated model judge as a second signal. RC §3 supports a 770M-parameter
checker with published results on a factual-consistency benchmark and a 4.3-point
margin over the next open baseline; RG §3 proposes a fine-tuned cross-encoder
with no task evidence. Both fill the same methodological role, so RC's
evidence-backed choice is the default and RG's is a named alternative to
benchmark against it. *(chosen: RC §3; retained as alternative: RG §3)* The
primary scorer's weight license and self-hostability are *(open — resolved by
verification, not argument, discharged by V4)*.

**R8.3** **No support scorer is ground truth.** RC §3 reports these metrics are
gameable — appending innocuous text materially inflated one published scorer —
and that they degrade on evidence distributed across a document. Treat every
score as a calibrated signal paired with human spot-checks, never a verdict
*(RC §3)*.

**R8.4** Calibrate any model judge against at least 50 expert labels (`A §728`),
report judge-to-human agreement, and set a pre-registered agreement floor before
use. Mitigate known judge biases — position, verbosity, self-preference — with
cross-family judges and order-swapping. Expect κ in the 0.3–0.6 range for
subjective coding and do not over-promise agreement *(RC §7)*. The floor value
itself is covered by R13.

**R8.5** A judge may reject or flag an assignment. A judge may never modify
evidence, promote an invalid span, or alter a theme definition (`A §563`, Core
principle).

**R8.6** Report support-scorer quality as AUC-ROC against binary human judgments,
alongside precision on accepted claims *(RG §7, RC §7)*.

### R9 — Codebook

**R9.1** Support both regimes (`A §594`). Deductive: a fixed approved codebook
with multi-label assignment. Inductive: consolidate verified quote-claim pairs
into a candidate codebook, obtain human approval, freeze and version it, then
re-code the declared corpus.

**R9.2** Each theme definition carries a stable identifier, a **parent
identifier**, a label, a formal definition, inclusion rules, exclusion rules,
positive examples, **hard negatives**, and sector applicability. Hierarchy and
hard negatives are additions to `A §594`'s field list and are required for stable
multi-label coding *(RX §4)*.

**R9.3** An unmatched candidate enters a **novelty queue** for periodic human
adjudication. No new production theme identifier appears without review. Approved
themes enter the codebook as a new version; definitions are never silently
extended mid-analysis *(RX §4, RG §4, RC §4; sharpens `A §594`)*.

**R9.4** Keep the semantic units distinct — topic, claim, theme, subtheme,
sentiment/direction, event type — extending `A §563`'s quote/claim/theme/
assignment vocabulary. A sentiment score must never stand in for importance, and
a cluster label must never become a theme. This is what blocks vacuous codes like
"business" *(RX §4)*.

**R9.5** Inductive clustering runs **offline only**, outside the application
pipeline, as a codebook-discovery aid. RC §4 and RX §4 note the usual toolchain is
pandas-based; keeping it offline enforces the no-hidden-pandas convention at a
named boundary. Exploratory clusters stay separate from approved longitudinal
assignments *(`A §594`)*.

**R9.6** Every assignment records its codebook identifier and version.
Comparisons default to a single approved version. Retrospective harmonized
analysis is kept strictly separate from prospective fixed-codebook evaluation
*(`A §594`, RG §4)*.

**R9.7** Taxonomy *content* is out of scope for this spec. It is produced by the
approval process in R9.3 and recorded in a decision record, never invented here
(`CLAUDE.md` lists the final taxonomy as deliberately unresolved).

### R10 — Discovery paradigm *(amends `A §452`)*

**R10.1** **Exhaustive structure-aware traversal is the default discovery path.**
Every analysis-eligible element is processed and can surface a candidate.
Whole-document processing becomes a measured ablation, not the starting point.

This inverts `A §452`. All three reviews independently reach the same conclusion
citing the same positional-attention literature: model recall degrades for
mid-context material, and a document fitting inside the context window does not
imply complete extraction (RC §4, RX §4, RG §4). Since exhaustive discovery is the
actual requirement — a briefly-mentioned severe disclosure must not be missed —
the default must guarantee coverage rather than assume it. *(chosen; amends
`A §452`)*

**R10.2** Top-*k* retrieval is **not** a discovery mechanism. It structurally
favors repetitive themes and can omit single-mention material before the model
sees it. Retrieval remains valid for targeted lookup — collecting all evidence
for a known theme, locating a prior-period analogue, building review queues
*(RC §4, RX §4)*. This is consistent with `A §452`'s existing prohibition on
introducing retrieval merely to read a known document.

**R10.3** Hierarchical consolidation across elements must preserve evidence
pointers and must not erase contradictory claims (`A §594`, RX §4).

### R11 — Coverage-aware aggregation

**R11.1** The analytical grain is
`firm × quarter × doc_type × speaker_role × theme × quote_id` (`A §627`).
Deduplicate the accepted assignment grain within a run.

**R11.2** Prevalence counts **distinct eligible firms or firm-quarters**, never
quote counts, and always displays its numerator, denominator, unit, and
document/role restrictions (`A §627`).

**R11.3** **Denominators reflect source observability.** A theme observable only
in transcripts cannot use transcript-less firms in its denominator unless the
metric is explicitly redefined and relabeled. This makes `A §627`'s coverage
requirement computable *(RX §5)*.

**R11.4** Equal-issuer weighting is the default. Do not weight by employment or
market capitalization; those answer different questions and need their own
rationale and provenance *(`A §627`, RC §5, RX §5)*.

**R11.5** Deduplicate copies of the same disclosure across sources, and do not
treat near-verbatim prepared remarks reproduced in two documents as independent
corroboration *(RC §5, RX §5; extends `A §480`'s dedup rule into aggregation)*.

**R11.6** Separate management remarks and answers from analyst questions
throughout. Analyst attention is its own signal and never evidence for the
underlying factual claim. Unresolved roles are `other`/`unknown` with an
attribution status, never forced (`A §563`).

### R12 — Evaluation design

**R12.1** The evaluation unit is the **event bundle** — one issuer-event with its
main filing, its release exhibits, any lawfully available transcript, and its
revisions — not a random sample of passages *(RX §7, RC §7)*.

**R12.2** **A 20–40 document hand-coded set is a feasibility pilot, not a
validation set.** It is sufficient to expose taxonomy ambiguity, parser defects,
speaker-role problems, schema deficiencies, and gross differences between
strategies. It is **not** sufficient to estimate rare-theme recall, sector
prevalence, source-selection bias, or ranker generalization; those require a
larger event-level validation set. *(chosen; RC §7, RX §7, RG §7 — amends
`A §728`, which adopts the number from the source note's learning plan without
this limitation)*

**R12.3** Split by **issuer and time**. All copies, revisions, and the complete
event bundle stay within one split. Codebook discovery occurs only on the
training partition when evaluating a prospective fixed-codebook system. A
corrected later transcript must not leak into a point-in-time test instance
*(RX §7, RC §7; operationalizes `A §728`)*.

**R12.4** The benchmark deliberately includes valid documents with **no**
qualifying themes, unavailable sources, restricted transcripts, and parser
failures, so abstention is measurable *(RC §7, RX §7)*.

**R12.5** Negative examples are drawn from confusable periods, issuers, and
sections — not sampled at random. RX §7 reports a 13–20.5 point accuracy drop when
random negatives are replaced by curated hard ones, which is the difference
between a benchmark that discriminates and one that flatters *(RX §7)*.

**R12.6** Annotate independently before adjudication; report agreement rather than
adjudicating silently; preserve genuine ambiguity as ties or distributions
*(RX §7, RC §7)*.

**R12.7** Report uncertainty with the **issuer or event as the sampling unit**,
not the quotation. Quotations within an event are not independent, and treating
them as such understates uncertainty *(RX §7, RC §7)*.

**R12.8** **Pair exactness with retained coverage.** Exactness is 1.0 by
construction over retained quotes (R6.1), so it carries no information about
recall and cannot rank candidate designs. A system that rejects everything scores
1.0 and must fail the suite. Report retention rate, support precision, theme
recall, span overlap, and run-to-run stability alongside it *(RC §7, RX §7;
makes `A §728`'s warning an explicit gate)*.

**R12.9** Run the controlled ablations: pointer versus generate-then-verify
(R5.1/R5.2); exhaustive traversal versus whole-document versus retrieval-only
(R10.1); deductive versus inductive versus hybrid codebook (R9.1); release-only
versus release-plus-transcript (R2.1); dedup on/off (R11.5). Report quality,
latency, token usage, and cost for each. Planned experiments are never described
as completed results *(RC §7, RX §7, RG §7, `A §728`)*.

**R12.10** Treat the model as a noisy coder: run the pipeline *k* times and
compute inter-rater agreement across runs, bypassing response replay when
measuring fresh-call variability (`A §728`, `S` Stage 6).

### R13 — Acceptance thresholds

**R13.1** Every non-exactness acceptance threshold — release-identification
precision and recall, theme micro/macro F1, support precision, rare-theme recall,
span overlap, judge agreement floor, retained coverage — is *(open — resolved by
measurement, not argument, discharged by V6)*. The spec names each metric and its
measurement protocol; the numeric gate is set after the R12.2 pilot reports
baseline distributions.

`CLAUDE.md` lists non-exactness quality thresholds as deliberately unresolved and
directs that none be silently picked. RX §7 proposes a full table of gates; those
are recorded as one reviewer's untested proposal — and that reviewer could not
read the source files — not as adopted values. A gate cannot be calibrated before
the first measurement exists.

**R13.2** The deterministic exactness invariant (R6.1) is **not** a threshold and
is not open. It is binding at 100% over retained quotes by construction.

**R13.3** Set thresholds before comparing candidate configurations. Evaluate the
frozen selected configuration on the held-out split **once**; further test-guided
changes require a new protocol (`A §728`).

### R14 — Models, cost, and untrusted input

**R14.1** **The required path runs on open-weight, self-hosted models only.** No
billable inference is required to run, test, or reproduce any requirement in this
spec. Offline replay with saved fixtures and fake model adapters is the default
for development and CI (`A §58`, `A §657`). Each model's weight license is
verified at adoption; a software license is not a weight license *(RC §6)*.

**R14.2** An optional hosted-frontier comparison may establish a quality ceiling
on a frozen subset. **Authorized budget: $100, covering the hosted ceiling
ablation only.** It does not cover prompt-optimizer compiles, which RC §6 reports
can alone run into the hundreds of dollars. Per-document and per-run request,
token, and cost ceilings are enforced **before dispatch**; exhaustion returns a
visible partial or failed status, never a silent truncation. Any hosted result is
an ablation ceiling, never a production dependency (`A §657`).

**R14.3** The typed-verification vendor option is **not** adopted in the required
path. RC §6 establishes it is closed, hosted, waitlisted, and billable; that it
cannot extract spans or generate text, so it cannot satisfy R5 or R7; and that its
published accuracy is measured as agreement with other models rather than against
ground truth. It remains available only as an optional, separately authorized
verification layer benchmarked against R8.2. This supersedes
`AGENTS-jev-addendum.md` and `specs/jev-integration-spec.md` on the required-path
question *(RC §6)*.

**R14.4** Keep the production dependency set minimal. A workflow framework is
justified only by resumable backfill at scale and the codebook-approval
interrupt; a prompt optimizer only after a gold set and evaluation exist; a
multi-agent configuration stays an experiment. Deterministic domain functions
remain usable without any of them *(RC §6, RX §6; confirms `A §657`)*.

**R14.5** Cast any acquisition-library output that arrives as a foreign dataframe
into the project's dataframe type at the ingestion boundary; no hidden
intermediaries propagate inward *(RG §6)*. *(open — resolved by verification, not
argument: the library's current return types are a fact to check against the pin,
discharged by V1)*

**R14.6** Cache on canonical hash, model and provider identity, parameters,
prompt content, extractor and verifier versions, and codebook version. Cached
output is not automatically valid under a changed contract (`A §657`).

**R14.7** Filings, pages, and tool output are **data, never instructions**. A
model response that repeats instructions found in a document must not trigger
tools, alter the codebook, or bypass verification (`A §58`, `A §728`, RC §6).

## Verification

Observable outcomes. Each `(open)` marker above is discharged by exactly one
bullet here.

- **V1 — acquisition-library return types** *(discharges R14.5)*. Against the
  pinned version, call the exhibit and table paths and record the concrete return
  type of each. If any is a foreign dataframe, the ingestion boundary cast is
  required and tested; if not, R14.5 is satisfied vacuously and says so.
- **V2 — parser element fidelity** *(discharges R4.1)*. On a fixture set spanning
  clean HTML, malformed layout, table-heavy, and narrative-only releases, compare
  the parser's typed elements against hand-marked structure. Record reading-order
  corruption, footnote merging, and header loss rates.
- **V3 — provider citation capability** *(discharges R5.3)*. At adapter
  implementation time, issue a live request combining native citations with
  structured output against the then-current API and record the response. Do not
  encode RC §3's verified error as permanent.
- **V4 — support-scorer license and hosting** *(discharges R8.2)*. Confirm the
  primary scorer's weight license permits this use and that it runs self-hosted
  with no API call, then record checkpoint identity and version in the manifest.
- **V5 — passage-link support and degradation** *(discharges R7.2)*. Resolve a
  generated highlight link in each target browser; record whether it highlights,
  degrades to page-top, or fails. Confirm the snapshot fallback renders the span
  in every failing case.
- **V6 — threshold calibration** *(discharges R13.1)*. After the R12.2 pilot,
  report the observed distribution for every named metric and set each gate from
  it in a recorded decision. Until this runs, no configuration may be described as
  passing or failing.
- **V7 — transcript source license and diarization** *(discharges R2.2)*. For any
  candidate transcript corpus, record its license, its redistribution terms, and
  measured speaker-attribution accuracy against a hand-labeled sample. A corpus
  that cannot support the management/analyst split fails R2.2.
- **V8 — offline end-to-end contract test**. From raw fixture through canonical
  text, fake model response, verification, approved codebook, analytical rows, and
  cited report — with no network and no credentials. Ingestion runs without model
  credentials; themes run from saved canonical documents without fetching
  sources (`A §728`).
- **V9 — invariant round-trips**. Deterministic tests for hash and offset round
  trips, Unicode and whitespace normalization, sentence splitting around financial
  abbreviations and decimals, duplicated passages, invalid pointers, stitched
  spans, wrong-document matches, chunk-to-document coordinate conversion, speaker
  boundaries, and canonical version changes (`A §728`).
- **V10 — denominator construction**. Given a corpus with known unavailable,
  restricted, failed, and no-theme documents, confirm reported prevalence
  reproduces hand-computed numerators and denominators under R11.2 and R11.3.
- **V11 — prompt-injection resistance**. A fixture whose text contains
  instructions must not trigger a tool call, alter the codebook, or bypass R6.1
  *(R14.7)*.

## Out of scope

- **Theme importance ranking.** The business-significance / discourse-salience /
  cross-firm-prevalence separation, the anchored ordinal rubric with
  unknown-is-not-zero, rank bands with missingness intervals, the
  not-rankable-without-evidence gate, and the rubric-to-learned-ranker ladder are
  a distinct subsystem with no basis in `AGENTS.md`. Nine adjudicated review
  points support it (RC §5, RX §5, RG §5, adjudicated at triage: the immediate
  learning-to-rank proposal was **rejected** for requiring expert pairwise labels
  that do not exist; the staged ladder was accepted). **Successor spec required
  before implementation.** R11 delivers the coverage-aware prevalence such a spec
  would consume.
- **Theme taxonomy content** — produced by R9.3's approval process (R9.7).
- **Company enrichment** — membership, identifiers, subsidiaries, employment,
  locations, industry classification. These supply optional dated context through
  joins, never evidence for words absent from a document (`A §445`). `AGENTS.md`
  governs them unchanged.
- **Numeric acceptance gates** — R13.1, deferred to V6 by user decision.
- **Prompt-optimizer compilation** — outside the R14.2 authorization; requires
  separate approval and a gold set that does not yet exist.

## Rollout

**V6 blocks the most.** Until the pilot calibrates thresholds, no configuration
can be described as passing, and R12.9's ablations can be run and reported but not
adjudicated. Sequence the pilot early.

The two tracks stay connected but independently testable; do not complete company
enrichment before the theme vertical slice runs (`A §780`). The slice that proves
this spec is one earnings release passing through acquisition, canonicalization,
pointer evidence, deterministic verification, support assessment, an explicitly
approved small codebook, and a typed analytical export with source-linked quotes.

Three requirements amend binding instructions (R3.4, R10.1, R12.2). `AGENTS.md`
should be updated to point at this spec at those three sections rather than left
to contradict it; a reader who consults only `A §452` would otherwise build the
wrong default.

For instruction-only changes downstream, state that application tests and live
extraction were not run. Never claim a full-universe run or a completed stage from
a fixture (`A §769`).
