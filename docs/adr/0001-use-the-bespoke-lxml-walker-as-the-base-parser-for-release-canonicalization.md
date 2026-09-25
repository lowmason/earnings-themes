# 0001. Use the bespoke lxml walker as the base parser for release canonicalization

- **Status:** Proposed
- **Date:** 2026-09-25
- **Deciders:**
- **Blast radius:** `earnings-ingestion` (the Stage 3 canonicalizer) and every
  canonical document version.

## Context

What was known on 2026-09-25, when Stage 1 (`specs/release-parser-fidelity.md`)
finished its second measurement:

- **The open question.** R4.1 of `specs/evidence-linked-theme-extraction.md` leaves the
  release parser open until V2 is discharged. Stage 3 canonicalizes releases on
  whichever parser is chosen here.
- **Round 1.** A first measurement, on eight other fixtures, selected the walker at
  coverage.
  - Its margin rested on six American Electric Power footnotes anchored on page
    numbers, which edgartools drops.
  - Its control check flagged the fixtures as unable to discriminate between parsers.
  - At gate D the user replaced all eight fixtures. Round 1's proposal of this ADR is
    commit `8bda724`.
- **The fixtures.** Eight EDGAR earnings-release exhibits, two per class, chosen by a
  rule fixed before a new discovery run. Five of the eight come from that run.
  - clean HTML: Southwestern Energy 2009, FMC 2014;
  - malformed layout: Ball 2010, Becton Dickinson 2022;
  - table-heavy: Southwest Airlines 2007, National Health Investors 2013;
  - narrative-only: Union Bankshares 2016, Pharmacyclics 2008.
- **The gold.**
  - It is recorded as text anchors marked from a browser rendering.
  - Under F9, Codex drafted all eight fixtures' gold and the user verified every block.
- **The candidates** (F2):
  - edgartools 5.58.0's HTML document parser (`edgar.documents.parse_html`);
  - sec-parser 0.58.1 (`Edgar10QParser`);
  - a bespoke lxml walker, whose rules W0-W16 the user approved before development.
  - A negative control, BeautifulSoup's `get_text`, also ran.
- **The walker's authorship.**
  - Claude, the assistant that executed the plan, wrote the walker, the harness and
    the scorer.
  - The walker was developed on three separate development releases.
  - Every candidate was frozen at `616721a` before any candidate ran on a fixture, and
    stayed frozen through both rounds.
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
  - They tie on coverage (1.000), footnote merging (1.000, 6 of 6 in table_heavy) and
    reading order (0.006, 1 of 167 in malformed_layout, a pair the gold produces).
  - Header loss decides: the walker scores 0.781 (n=28, narrative_only) and edgartools
    1.000 (n=28, narrative_only).
- **Caveats, raised at gate D.**
  - The control check flags the fixtures again. On its three metrics a line-level
    control cannot be beaten on fixtures like these. Round 1's independent review
    argued this, and round 2 bears it out.
  - The deciding margin is the typing of 16 gold headings in two narrative releases.
    Header loss does not count body text typed as headings, where the walker does worst
    of the three parsers.
  - sec-parser, which is ineligible, is within the tie margin at header loss (0.812).
  - Setting aside the seven gold blocks that depart from a spec rule leaves the
    outcome unchanged.
- **The measurements.** `docs/verification/V2-parser-fidelity.md` holds them all.

## Decision

We will use the bespoke lxml walker as the base parser for release canonicalization.

## Consequences

- **Positive:**
  - **Header loss.** Its worst class, 0.781 (n=28, narrative_only), is the lowest of the
    three parsers': edgartools scores 1.000 and sec-parser 0.812 in the same class. By
    class, from `metrics.md`:

    | Class | Walker | edgartools | sec-parser |
    | --- | --- | --- | --- |
    | clean_html | 0.126 | 0.492 | 0.292 |
    | malformed_layout | 0.184 | 0.500 | 0.368 |
    | narrative_only | 0.781 | 1.000 | 0.812 |
    | table_heavy | 0.341 | 0.500 | 0.295 |

  - **No new dependency.** It adds no runtime dependency to `earnings-ingestion`,
    because its imports, lxml and beautifulsoup4, are already declared there. Neither
    pandas nor pyarrow enters the canonicalization path.
  - **Deterministic and offline.** It produced identical output on both runs of every
    fixture, in both rounds, with no network access.
  - **Fast.** Each fixture parsed in at most 0.031 s; edgartools took 0.38-1.17 s.
  - **Table grids.** It exposes table grids, and its cell association matches or beats
    edgartools':

    | Class | Walker | edgartools |
    | --- | --- | --- |
    | clean_html | 24/39 | 24/39 |
    | malformed_layout | 33/33 | 18/33 |
    | table_heavy | 15/15 | 0/15 |
  - **Auditable rules.** Its rules are written down (`walker-rules.md`), so its
    behaviour can be audited rule by rule.
  - **Not strengths.** Its coverage (1.000) and reading order (0.006) equal the
    control's and edgartools'. Its footnote merging (1.000, 6 of 6 in table_heavy)
    equals both other parsers', against the control's 0 of 6.
- **Negative:**
  - **Residual failures.** Stage 3 must compensate for these or record them. V2 lists
    each one by fixture and block:
    - **Split:** 25 text blocks, in six fixtures.
    - **Merged:** 49 blocks, in six fixtures. Most are titles, contact blocks, notes
      and footnotes that the page sets inside tables passing the data-table test.
    - **Header lost:** 45 headings:
      - 23 fall through W8-W11 to `paragraph` (W12);
      - 19 sit inside table elements;
      - 2 year subheadings match W8's page-number pattern;
      - 1 is typed `list_item` by W9.

      14 table header texts are lost too, 12 of them in Pharmacyclics' `<pre>` tables,
      which no candidate exposes.
    - No block is missed and no anchor is altered. The one misordered pair comes from
      the gold.
  - **Body text typed as headings.** Header loss does not count it. An in-memory check
    found that the walker typed 12 of the 313 body blocks it found as headings, against
    sec-parser's 7 and edgartools' 0. In round 1 the walker typed 3 of 210.
  - **Known gaps.** The development set left eight documented gaps. The rules as
    written also have two side effects: W11 types short bold sentences as headings,
    and W15 flags stub labels as header rows.
  - **Maintenance.** The walker is project code. The project owns its maintenance,
    and any change to a rule changes canonical text.
  - **Page numbers.** It keeps page numbers in place as `other` elements, and its
    page-number pattern also takes four-digit years. The canonicalizer must decide what
    to do with them.
  - **Added dependencies:** none (the lock-gate result).
- **Neutral / follow-on:**
  - **Stage 3** builds the canonicalizer on the walker and owns R3.5's text-fidelity
    check, which Stage 1 did not measure.
  - **Where the code lives.** The measured code stays frozen in the Stage 1 harness
    (`expirements/parser-fidelity/walker.py`). Stage 3 decides how it enters
    `earnings-ingestion`.
  - **Gate D.** Before this ADR is accepted, the user decides on the control check's
    "cannot discriminate" flag, raised in both rounds.

## Alternatives considered

- **edgartools 5.58.0** (`edgar.documents.parse_html`, default `ParserConfig`):
  eligible, but it fell outside the tie margin at the fourth metric, header loss.
  - **The values.** In its worst class, narrative_only, it scored 1.000 (n=28) against
    the walker's 0.781. The gap of 0.219 exceeds the 1/28 margin.
  - **Why it lost.** It types all six of Union Bankshares' headings as paragraphs. It
    emits Pharmacyclics' 30 scored blocks, the ten headings among them, in one `other`
    element.
  - **Round 1.** There it lost at coverage, on six footnotes anchored on the page
    numbers it drops. With those set aside, it lost at header loss.
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
  - **On the rule.** Had it been eligible, it would have tied the walker: its worst
    header loss, 0.812 (n=28, narrative_only), is within 1/28 of the walker's 0.781. A
    replay outside the rule shows the first tie-break, dependency footprint, keeping the
    walker (no added distributions, against 23).
  - **Dependencies.** It would add 23 runtime distributions, pandas among them.
- **The control** (BeautifulSoup `get_text`): not selectable. It is a negative control
  with no element types, so its header loss is 1.000 in every class. In both rounds it
  matched the walker on coverage and reading order in every class, and led on footnote
  merging in table_heavy. That is why the fixtures are flagged as unable to
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
  - a sec-parser release that clears the lock gate. On round 2 it came within the tie
    margin of the walker, and only the lock gate, then the dependency tie-break,
    separate them;
  - an edgartools release that changes the measured failures: headings typed as
    paragraphs or emitted inside one `other` element, and dropped page numbers;
  - Stage 3 finding the walker's residual failures or Known gaps too costly to
    compensate for.
