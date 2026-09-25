# Point-in-time DJIA cohort and earnings corpus

> For agentic workers: REQUIRED NEXT SKILL: writing-plans. Plan this specification
> as an amendment to `specs/evidence-linked-theme-extraction.md` and
> `specs/evidence-linked-theme-extraction-roadmap.md`, followed by the new cohort
> stage. Do not begin document acquisition before the cohort artifacts described
> here can be frozen.

This specification defines the firm universe and event corpus for the first
longitudinal earnings-theme study. It adds an explicit, point-in-time Dow Jones
Industrial Average (DJIA) cohort before earnings-document acquisition, selects a
40-event feasibility pilot without conditioning on processing success, and adds
a later full-corpus run covering eight calendar period-end quarters.

The design supplements the evidence-linked theme-extraction specification. It
does not make subsidiary, employment, establishment, or general company
enrichment part of the theme-extraction critical path.

## Decisions

The user approved these decisions during design:

| ID | Decision |
| --- | --- |
| C1 | The target universe is the DJIA, resolved point in time rather than treated as one current roster. |
| C2 | Event eligibility uses DJIA membership on the earnings release's first supported public-availability date. |
| C3 | The analytical window is calendar period ends from `2024Q3` through `2026Q2`, represented as the half-open interval `[2024-07-01, 2026-07-01)`. Each issuer's source-reported fiscal year and quarter remain separate fields. |
| C4 | The public-information cutoff is `2026-09-22`. Evidence first published after that date cannot change this corpus version. |
| C5 | The feasibility pilot targets 40 expected issuer-events, includes every eligible issuer at least once, covers all eight period-end quarters, and adds membership-boundary and longitudinal cases. |
| C6 | After pilot calibration and configuration selection, the frozen configuration runs over the complete eligible DJIA event manifest. The observed count is reported; it is not forced to equal `30 × 8`. |
| C7 | Cohort construction is a dedicated stage before acquisition. Event discovery resolves publication time and freezes the full and pilot event manifests before document download or parsing outcomes are known. |

## Problem

The current roadmap first resolves earnings events and only afterward says to fix
the pilot sample. That order leaves the issuer population implicit and permits a
sample to be conditioned accidentally on documents that were easy to acquire or
parse. It also does not stage the eventual eight-quarter panel.

A current list of DJIA constituents is not sufficient. It can introduce
survivorship bias into earlier periods and cannot support the repository's two
historical questions: what was true at a date, and what was publicly knowable by
a cutoff. Membership changes may be sparse, but the design must represent them
without special cases.

## Scope

In scope:

- security-level DJIA membership assertions and effective intervals;
- security-to-issuer resolution, including zero-padded SEC CIKs;
- the fixed calendar period-end window and public-information cutoff;
- discovery of expected earnings events and their first supported publication;
- deterministic event eligibility and pilot selection;
- immutable, versioned universe, full-corpus, and pilot manifests;
- source rights, conflicts, missingness, and coverage reporting;
- a later full-corpus run using the configuration selected by the pilot.

Out of scope:

- a general-purpose historical index-membership product;
- S&P 500 expansion;
- employment, subsidiary, establishment, or facility enrichment;
- using GICS, SIC, or NAICS to alter DJIA eligibility;
- theme extraction, support judgment, or codebook behavior already governed by
  the evidence-linked extraction specification;
- redistribution of proprietary constituent data without documented permission.

## Temporal definitions

The system keeps four times distinct:

| Field | Meaning |
| --- | --- |
| `period_end` | End of the business period discussed by the release; determines inclusion in the eight-quarter analytical window. |
| `reported_fiscal_year` / `reported_fiscal_quarter` | The issuer's source-reported fiscal labels; never replaced by a calendar-quarter guess. |
| `first_publication_time` | Earliest supported public availability of the actual earnings release; determines membership eligibility. |
| `retrieved_at` | When the project acquired the evidence; never used as a substitute for publication or effective time. |

The public-information cutoff is the date `2026-09-22`. Records with date-level
publication evidence qualify only when their supported publication date is on or
before the cutoff. Precise timestamps are stored in UTC with the original source
timezone when available.

For a release and a membership interval `[effective_from, effective_to)`, event
eligibility is:

```text
2024-07-01 <= period_end < 2026-07-01
and first_publication_date <= 2026-09-22
and effective_from <= first_publication_time < effective_to
```

An open membership interval has no `effective_to`. When an official membership
change and a release share a date but the available evidence cannot order them,
eligibility is `ambiguous`; the system does not invent a time.

## Architecture and revised stages

Insert a dedicated cohort stage after structure-aware canonicalization. Renumber
the current Stages 4–14 and add the full-corpus run before the optional hosted
ceiling:

```text
Stage 1   Acquisition-library and parser fidelity
Stage 2   Core evidence spine
Stage 3   Structure-aware canonicalization
Stage 4   Point-in-time DJIA cohort
Stage 5   Event discovery, eligibility, and acquisition
Stage 6   Pilot codebook, split, and gold-set protocol
Stage 7   Evidence selection and verification
Stage 8   Semantic support assessment
Stage 9   Deductive coding
Stage 10  Coverage-aware aggregation and cited export
Stage 11  Feasibility pilot and threshold calibration
Stage 12  Inductive and hybrid codebook
Stage 13  Transcript extension
Stage 14  Configuration comparison and held-out evaluation
Stage 15  Full DJIA eight-quarter run
Stage 16  Hosted quality ceiling (optional)
```

### Stage 4 — Point-in-time DJIA cohort

Stage 4 belongs to `earnings-ingestion`. It acquires and interprets index
membership evidence, resolves securities to issuers, and produces:

- a versioned DJIA universe definition;
- security-level membership assertions and derived effective intervals;
- security-to-issuer mappings with CIK evidence;
- the union of candidate issuers over the study window;
- a source register and coverage/conflict report.

It does not download earnings documents or decide final event eligibility.

### Stage 5 — Event discovery, eligibility, and acquisition

Stage 5 consumes the frozen Stage 4 cohort and proceeds in this order:

1. Enumerate expected issuer-period event slots.
2. Discover candidate releases and resolve their period end and first supported
   public-availability time.
3. Join each event to the Stage 4 membership intervals.
4. Freeze the complete eligible-event manifest.
5. Run the deterministic pilot selector and freeze its 40-event manifest.
6. Only then acquire the selected release artifacts and record every acquisition
   and parsing outcome.

The ordering is binding. Pilot membership cannot depend on download success,
parser success, quote retention, theme output, or human preference after results
are seen.

### Stage 6 — Pilot codebook, split, and gold-set protocol

Stage 6 consumes the frozen pilot manifest. It no longer chooses the sample. It
creates issuer-and-time splits, the codebook contract and approved pilot
codebook, and validated annotations.

### Stage 15 — Full DJIA eight-quarter run

After Stage 14 freezes a selected configuration, Stage 15 consumes both the
frozen expected-event ledger and its eligible-event manifest. It processes every
eligible event, reuses compatible cached pilot artifacts, does not reselect
events, and produces the full analytical outputs and coverage report. Ineligible
and ambiguous ledger rows are not processed as eligible, but remain visible
alongside failed, unavailable, partial, and completed-no-theme cases in coverage
and status outputs.

## Data contracts

### Universe definition

```text
universe_id
universe_version
universe_name                 # djia
period_end_start              # 2024-07-01, inclusive
period_end_stop               # 2026-07-01, exclusive
public_information_cutoff     # 2026-09-22
membership_reference          # first_publication_time
source_register_version
selection_policy_version
content_hash
created_at
```

### Membership assertion

The persisted grain is one assertion per index, security, effective interval,
and source evidence item:

```text
membership_assertion_id
universe_id
security_id
issuer_id                     # nullable until resolved
cik                           # nullable; otherwise 10-character zero-padded text
effective_from
effective_to                  # exclusive; null when open
announcement_date
source_snapshot_date
publication_time
retrieved_at
source_id
evidence_locator
raw_content_hash
status                        # supported, conflicting, ambiguous, withheld
```

Membership remains a security-level fact. An issuer view is derived explicitly;
multiple securities from one issuer do not multiply expected earnings events.

### Expected event

```text
event_id
issuer_id
period_end
reported_fiscal_year
reported_fiscal_quarter
first_publication_time
first_publication_source_id
filing_acceptance_time
membership_assertion_id
eligibility_status            # eligible, ineligible, ambiguous
eligibility_reason
processing_status
missing_reason
```

EDGAR acceptance time is retained separately. It establishes first publication
only when no earlier supported public release source exists. Unknown time remains
unknown.

### Pilot selection

```text
pilot_id
pilot_version
universe_version
eligible_event_manifest_hash
selection_policy_version
selection_seed
event_id
selection_order
selection_reason
content_hash
created_at
```

The manifest records one row per selected event plus run-level metadata. Changing
membership evidence, issuer resolution, the event corpus, or the selection policy
creates a new version and hash.

## Membership evidence and source rights

Use this evidence hierarchy:

1. a dated constituent snapshot at or before the earliest possible eligible
   release;
2. official S&P Dow Jones Indices addition/removal announcements and their stated
   effective dates through the cutoff;
3. an accessible dated secondary constituent snapshot or DIA holdings record as
   corroboration, labeled explicitly as secondary evidence or an ETF proxy.

Reconstruct intervals from the anchor and every supported change. Do not use a
current list as evidence for prior membership, and do not treat ETF holdings as
the official index roster.

Every source has a source-register entry with owner, URL, access method, cost,
terms, redistribution status, coverage, expected update behavior, known
limitations, and last verification date. Raw rosters and snapshots remain local
unless redistribution is explicitly permitted. Default tests use synthetic
fixtures; a free or open-source acquisition tool does not confer rights to the
underlying index data.

Live acquisition must not bypass authentication, paywalls, robots restrictions,
or rate limits. Persistent access failures stop the stage and remain visible.

## Issuer resolution

Resolve in this order:

```text
DJIA security
    -> security/share-class identity
    -> issuing legal entity
    -> zero-padded SEC CIK
```

Use exact identifiers and dated evidence first. Ticker strings generate
candidates but never establish permanent identity. Preserve historical ticker
changes and multiple securities. Unresolved or conflicting matches remain
exportable and block event-manifest freezing for the affected records until a
documented manual decision resolves them or retains them as unresolved.

Manual overrides are version-controlled assertions with evidence, rationale,
reviewer, and effective dates. They are not parser branches.

## Deterministic pilot selection

Selection operates only on the frozen eligible-event metadata. Let `U` be the
set of eligible issuers and `E` the set of eligible events.

- If `|U| > 40`, stop for a new scope decision; never silently omit an issuer.
- If `|E| < 20`, block the feasibility pilot.
- If `20 <= |E| < 40`, select all eligible events and mark the pilot underfilled.
  It may freeze only if those events represent every eligible issuer and all
  eight required quarters; otherwise the coverage requirement blocks it.
- Otherwise target exactly 40 events.

For the normal `|E| >= 40` case:

1. Derive a stable seed from the universe version, eligible-event manifest hash,
   and selection-policy version.
2. Order issuers by a hash of the seed and `issuer_id`.
3. Select one event per issuer. For each issuer, prefer a currently
   least-represented period-end quarter; break ties by a hash of the seed and
   `event_id`.
4. For each issuer with a membership transition in scope, add the nearest
   eligible event on the member side of the transition when that boundary is not
   already represented. Order competing additions by transition time and stable
   event hash.
5. Add events from any uncovered period-end quarter, preferring issuers with the
   fewest selections and then stable event hash. If the full eligible manifest
   contains no event for a required quarter, block freezing rather than claim
   eight-quarter coverage.
6. Fill remaining slots to 40. Prefer issuers with the fewest selections, then
   the event that maximizes temporal distance from that issuer's selected events,
   then stable event hash.

If the issuer, membership-boundary, and quarter-coverage requirements together
need more than 40 distinct events, stop for a scope decision before filling; do
not discard a mandatory case to preserve the cap.

Input row order cannot affect the result. Each selected row records one of:
`issuer_coverage`, `membership_boundary`, `quarter_coverage`, or
`longitudinal_fill`.

## Failure handling

- A missing anchor snapshot prevents the membership manifest from freezing.
- Conflicting effective dates remain separate assertions and require review.
- Same-day membership and release events without sufficient ordering precision
  remain `ambiguous`.
- A source or match failure is not evidence of non-membership.
- Evidence first published after `2026-09-22` cannot revise this corpus version.
- A selected event stays selected when acquisition, parsing, extraction, or
  support assessment fails.
- Freezing refuses unresolved issuer identity or event eligibility unless the
  record is explicitly retained as unresolved and excluded with its reason.
- Unclear redistribution rights keep source artifacts local and mark downstream
  export restrictions.
- Atomic writes and content hashes prevent partial manifests from appearing
  frozen.

## Verification

### Deterministic fixture tests

Use synthetic, redistributable fixtures to test:

- interval construction from an anchor plus additions and removals;
- inclusive starts and exclusive ends;
- releases immediately before and after a membership transition;
- same-day transitions with insufficient time precision;
- conflicting dates and a missing anchor;
- evidence first published after the cutoff;
- historical ticker changes, multiple securities, and CIK formatting;
- issuer derivation without duplicate events from multiple securities;
- both period-window boundaries;
- exact eligibility reasons for eligible, ineligible, and ambiguous events;
- deterministic pilot selection under shuffled input order;
- representation of every eligible issuer and all eight quarters;
- transition and repeated-issuer selection reasons;
- exactly 40 events when at least 40 are eligible;
- underfilled and blocked pilot cases;
- mandatory-coverage overflow beyond 40 events;
- unchanged selection after acquisition/parser statuses change;
- manifest invalidation after membership evidence or policy changes;
- refusal to freeze with unresolved blocking records.

### Offline integration test

Replay saved synthetic membership evidence and event metadata through:

```text
anchor + change evidence
    -> membership intervals
    -> security-to-issuer resolution
    -> event eligibility
    -> frozen eligible-event manifest
    -> frozen pilot manifest
```

The test uses no network, credentials, proprietary roster, or model call.

### Optional live verification

An opt-in `live` check verifies source accessibility and current terms, parses
the dated evidence used for the real manifest, and reconciles official changes
against the corroborating snapshot. It records retrieval metadata and respects
the repository's shared rate and identification policies. Live checks never run
in default CI.

## Acceptance criteria

Stage 4 exits only when:

- every membership interval resolves to source evidence;
- every resolved CIK is a zero-padded 10-character string;
- interval conflicts and coverage gaps are reported;
- no current snapshot is silently backdated;
- source access and redistribution status are recorded;
- the universe manifest is frozen with a version and content hash.

Stage 5 exits only when:

- publication time and period end remain separate;
- each event has an auditable eligibility decision;
- the full eligible-event manifest freezes before content outcomes are known;
- the pilot selection satisfies the deterministic rules above;
- selected failures remain in processing-status outputs.

Stage 15 exits only when:

- every expected-event ledger row has an eligibility and coverage status, and
  every eligible event has a terminal or resumable processing status;
- compatible pilot artifacts are reused without duplicate accepted rows;
- expected, eligible, acquired, parsed, processed, failed, partial, and
  completed-no-theme counts are reported by issuer and period;
- membership transitions and missing events explain any departure from the
  approximate `30 × 8` shape;
- analytical outputs carry universe, corpus, codebook, schema, and run versions.

## Roadmap amendment

When this specification is planned, update the parent evidence-linked extraction
specification so point-in-time cohort selection is in scope while general company
enrichment remains out of scope. Reconcile and renumber the roadmap exactly as
listed under Architecture and revised stages. Update all stage references,
`Consumes`/`Produces` edges, completion stamps, and the README roadmap summary in
the same change.

No stage is marked complete by adopting this specification. No real DJIA roster,
event corpus, parser result, or theme result is established until the applicable
stage runs and its verification evidence is recorded.

## Rollout

This specification is the stage spec for roadmap Stages 4 and 15. Each stage's
plan copies its own line below into its header, and that stage's COMPLETE stamp
is appended here:

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 4 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 15 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

Stage 5 is routed to brainstorming. Its own stage spec carries its Roadmap line
and must keep this specification's Stage 5 contracts and ordering. The roadmap
amendment itself was carried out on 2026-09-22 by plan 2
(`specs/plans/completed/2-point-in-time-djia-cohort.md`); it completed no stage.
