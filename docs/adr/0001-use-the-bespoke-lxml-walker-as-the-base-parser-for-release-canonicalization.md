# 0001. Use the bespoke lxml walker as the base parser for release canonicalization

- **Status:** Proposed
- **Date:** 2026-09-24
- **Deciders:**
- **Blast radius:** `earnings-ingestion` (the Stage 3 canonicalizer) and every
  canonical document version.

## Context

What was known on 2026-09-24, when Stage 1 (`specs/release-parser-fidelity.md`)
finished measuring:

- **The open question.** R4.1 of `specs/evidence-linked-theme-extraction.md` leaves the
  release parser open until V2 is discharged. Stage 3 canonicalizes releases on
  whichever parser is chosen here.
- **The fixtures.** Eight EDGAR earnings-release exhibits, two per class:
  - clean HTML: UQM Technologies 2018, AVX 2017;
  - malformed layout: IKON Office Solutions 2005, American Electric Power 2024;
  - table-heavy: Humana 2006, Ruby Tuesday 2005;
  - narrative-only: Establishment Labs 2023, Phillips 66 Partners 2014.
- **The gold.**
  - It is recorded as text anchors marked from a browser rendering.
  - Under F9, Codex drafted seven fixtures' gold and the user verified every block.
    The user marked the eighth by hand.
- **The candidates** (F2):
  - edgartools 5.58.0's HTML document parser (`edgar.documents.parse_html`);
  - sec-parser 0.58.1 (`Edgar10QParser`);
  - a bespoke lxml walker, whose rules W0-W16 the user approved before development.
  - A negative control, BeautifulSoup's `get_text`, also ran.
- **The walker's authorship.**
  - Claude, the assistant that executed the plan, wrote the walker, the harness and
    the scorer.
  - The walker was developed on three separate development releases.
  - Every candidate was frozen at `616721a` before any candidate ran on a fixture.
- **Eligibility gates** (F7):
  - **Lock:** the candidate resolves into the workspace lock on Python 3.14 without
    lowering a locked version, and parses every fixture.
  - **Determinism:** its two runs give byte-identical dumps.
  - **Network:** no guard trip.
- **Selection rule** (F6), fixed at `8c7331a` before any scoring:
  - Each candidate is judged on its worst class for each metric.
  - The metrics are compared in priority order: coverage, footnote merging, reading
    order, header loss. Values within 1/n tie.
  - Ties break on dependency footprint, then license, then release recency.
- **Results.**
  - sec-parser fails the lock gate. edgartools and the walker are eligible.
  - The rule stops at coverage: the walker scores 1.000 (n=27, narrative_only) and
    edgartools 0.939 (n=98, malformed_layout).
- **Caveats, raised at gate D.**
  - The control check flags the fixtures as unable to discriminate between parsers.
  - The coverage margin comes from six American Electric Power footnotes that are
    anchored on page numbers, which edgartools drops.
  - A reading outside the rule sets those six aside. The walker is then still
    selected, at header loss.
- **The measurements.** `docs/verification/V2-parser-fidelity.md` holds them all.

## Decision

We will use the bespoke lxml walker as the base parser for release canonicalization.

## Consequences

- **Positive:**
  - **Worst-class values.** Coverage is from `selection.md`; the other values are
    from `metrics.md`:

    | Metric | Walker's worst class |
    | --- | --- |
    | Coverage | 1.000 in every class (n=27, narrative_only) |
    | Footnote merging | 0.190 (4/21, table_heavy) |
    | Reading order | 0.000 in every class |
    | Header loss | 0.537 (n=157, malformed_layout) |

    Its header loss is the lowest worst-class value of the three candidates. edgartools
    scores 1.000 (n=10, narrative_only) and sec-parser 0.669 (n=157,
    malformed_layout).
  - **No new dependency.** It adds no runtime dependency to `earnings-ingestion`,
    because its imports, lxml and beautifulsoup4, are already declared there. Neither
    pandas nor pyarrow enters the canonicalization path.
  - **Deterministic and offline.** It produced identical output on both runs of all
    eight fixtures, with no network access.
  - **Fast.** Each fixture parsed in at most 0.023 s; edgartools took 0.36-0.93 s.
  - **Table grids.** It exposes table grids, and its cell association beats
    edgartools':

    | Class | Walker | edgartools |
    | --- | --- | --- |
    | clean_html | 12/12 | 12/12 |
    | malformed_layout | 6/6 | 0/6 |
    | table_heavy | 47/60 | 27/60 |
  - **Auditable rules.** Its rules are written down (`walker-rules.md`), so its
    behaviour can be audited rule by rule.
- **Negative:**
  - **Residual failures.** Stage 3 must compensate for these or record them. V2 lists
    each one by fixture and block:
    - **Split:** 15 text blocks, in AEP, UQM, AVX and Phillips 66 Partners.
    - **Merged:** 59 blocks, in AEP, Humana and UQM. Most come from text sections set
      in tables that pass the class tests' data-table definition, such as contact
      blocks and Humana's earnings guidance. The rest come from Humana's HTML tables
      that each hold several visible tables.
    - **Header lost:** 37 headings. 25 are typed as paragraphs by W11's bold or
      underline test, and 12 sit inside table elements. All 112 header texts of IKON's
      `<pre>` tables are lost too; no candidate exposes those tables.
    - No block is missed or misordered, and no anchor is altered.
  - **Known gaps.** The development set left eight documented gaps. The rules as
    written also have two side effects: W11 types short bold sentences as headings,
    and W15 flags stub labels as header rows.
  - **Paragraphs typed as headings.** Header loss does not count them. An in-memory
    check found that the walker typed 3 of the 210 body blocks it found as headings.
  - **Maintenance.** The walker is project code. The project owns its maintenance,
    and any change to a rule changes canonical text.
  - **Page numbers.** It keeps page numbers in place as `other` elements. The
    canonicalizer must decide what to do with them.
  - **Added dependencies:** none (the lock-gate result).
- **Neutral / follow-on:**
  - **Stage 3** builds the canonicalizer on the walker and owns R3.5's text-fidelity
    check, which Stage 1 did not measure.
  - **Where the code lives.** The measured code stays frozen in the Stage 1 harness
    (`expirements/parser-fidelity/walker.py`). Stage 3 decides how it enters
    `earnings-ingestion`.
  - **Gate D.** Before this ADR is accepted, the user decides whether to replace any
    fixture. Two things bear on it: the control check's "cannot discriminate" flag,
    and the page-number basis of the deciding margin.

## Alternatives considered

- **edgartools 5.58.0** (`edgar.documents.parse_html`, default `ParserConfig`):
  eligible, but it fell outside the tie margin at the first metric, coverage.
  - **The values.** Its worst class, malformed_layout, scored 0.939 (92/98) against
    the walker's 1.000 (n=27). The gap of 0.061 exceeds the 1/27 margin.
  - **Why it lost.** All six misses are American Electric Power footnotes anchored on
    the page numbers that follow them. edgartools emits the footnotes' text but drops
    the page numbers.
  - **Outside the rule.** With those six set aside, it would have lost at header
    loss: 1.000 (n=10, narrative_only) against 0.537 (n=157). It types the narrative
    releases' headings as paragraphs.
  - **Dependencies.** It would add 29 runtime distributions to `earnings-ingestion`,
    pandas and pyarrow among them.
- **sec-parser 0.58.1** (`Edgar10QParser().parse`): ineligible, because it fails the
  lock gate.
  - **The lock.** `uv lock` resolves only by lowering four locked versions:
    - lxml 6.1.3 to 5.4.0;
    - pandas 3.0.6 to 2.3.3;
    - tabulate 0.10.0 to 0.9.0;
    - xxhash 4.0.1 to 3.8.1.
  - **The interpreter.** No CPython 3.14 wheel satisfies its `lxml<6`, so it was
    measured on Python 3.13.8.
  - **On the rule.** It would not have survived step 3 either: its worst coverage is
    0.959 (n=98, malformed_layout).
  - **Dependencies.** It would add 23 runtime distributions, pandas among them.
- **The control** (BeautifulSoup `get_text`): not selectable. It is a negative control
  with no element types, so its header loss is 1.000 in every class. It matched the
  walker on coverage, footnote merging and reading order in every class, and led on
  footnote merging in table_heavy. That is why the fixtures are flagged as unable to
  discriminate.

## Trade-offs & reversibility

- **Canonical text.** Switching parsers changes canonical text, and so creates a new
  version of every document (R3.3). A reversal is cheap before Stage 3 canonicalizes
  the corpus and costly afterwards.
- **Owning the parser.** Owning it trades an upstream project's maintenance for
  explicit, auditable rules. Any later rule change is a canonical-text change, and so
  a new version.
- **What would trigger a superseding ADR:**
  - a larger validation set (R12.2) whose results contradict these;
  - a sec-parser release that clears the lock gate;
  - an edgartools release that changes the measured failures: dropped page numbers
    and headings typed as paragraphs;
  - Stage 3 finding the walker's residual failures or Known gaps too costly to
    compensate for.
