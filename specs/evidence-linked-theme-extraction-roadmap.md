# Roadmap: evidence-linked theme extraction

> For agentic workers: REQUIRED SKILL: derive-roadmap — resume via its
> reconcile step; route each unticked stage per its ROUTING line; never plan
> this document wholesale.

Source spec: `specs/evidence-linked-theme-extraction.md`. Derived 2026-09-22
from `main` at `bdcf0a4`; notes reconciled the same day after instruction-only
edits (no stage shipped).

Amending spec: `specs/point-in-time-djia-cohort.md`, adopted 2026-09-22. It
inserted Stage 4 (point-in-time DJIA cohort) and Stage 15 (full DJIA
eight-quarter run), renumbered former Stages 4–13 to 5–14 and former Stage 14 to
16, and moved pilot-sample selection out of the codebook stage into Stage 5. No
stage shipped. **`P` cites that spec**: `P-C1`–`P-C7` are its Decisions rows,
`P-A4`/`P-A5`/`P-A15` its three Acceptance-criteria groups, `P-VF`/`P-VI`/`P-VL`
its deterministic-fixture, offline-integration, and optional-live verification
groups, and `P §Section` cites a section by name.

Reconciled 2026-09-25 after Stage 1 shipped (plan 1): Stage 1 is ticked, and
Stages 2, 3 and 5 now name the Stage 1 records they consume. Stage 1's fixture
gold was drafted by Codex under the Stage 1 spec's F9 and verified block by block
by the user, rather than hand-marked as its Produces line says.

Reconciled 2026-09-25 after Stage 2 shipped (plan 3): Stage 2 is ticked, and
Stages 3, 4, 7, 10 and 13 now name the Stage 2 contracts they consume and cite
plan 3's Handoffs (`specs/plans/completed/3-core-evidence-spine.md`, §Handoffs).
Stages 3 and 10 also cite `specs/browser-rendering-integration.md`, now that plan
3 has closed the deferred reminder that carried it. Stage 2's element IDs are
derived from type and span (plan 3, D-1): stable across producers, but a moved
span is a new ID. Its pytest configuration deselects `live` tests unless
`-m live` is passed. Five of plan 3's deferred items (`specs/deferred_items.md`,
`3-core-evidence-spine`) close at the latest when Stage 3, 4 or 7 first relies on
the code they name.

Reconciled 2026-09-26 after Stage 3 shipped (plans 4 and 5): Stage 3 is ticked, its
Exit gains its stage spec's plan B criteria, and Stages 4, 5, 6, 7, 10, 13 and 15
now name what they consume from it. They cite both plans' Handoffs
(`specs/plans/completed/4-structure-aware-canonicalization-plan-a.md` and
`specs/plans/completed/5-structure-aware-canonicalization.md`, §Handoffs) and the
table in `specs/completed/structure-aware-canonicalization.md` (§Handoffs to later
stages), since plan 4's handoffs had no carrier while Stage 3 stayed unticked. ADR
0002 (`docs/adr/0002-keep-the-browser-capture-diagnostic-only.md`) kept the browser
capture diagnostic-only: `walker-1` canonicalizes every document, and no stage
needs a browser to canonicalize. The root pytest configuration now deselects
`browser` tests as well as `live` ones, unless `-m browser` or `-m live` is passed.
Of plan 3's deferred items, plans 4 and 5 closed five; the four still open stay
with Stage 7. Plan 5's own deferred items (`5-structure-aware-canonicalization`)
record the capture adapter's known defects and `walker-1`'s words joined across
`<br>` in table cells. Stages 5 and 10, which may capture next, cite the first, and
Stages 7 and 10, which the `<br>` item names, cite the second.

Reconciled again 2026-09-26, on resuming the roadmap before Stage 4. No stage had
shipped since the previous reconcile: `main` at `b7af585` carries the tree of
`08caa0f`. These are corrections to it, found by checking Stage 4's entry against
the code. Stage 4's Consumes line had omitted Stage 1's source register. It now
names the register, whose `sec-edgar` entry covers Stage 4's SEC requests, so
Stage 2 is no longer its only hard dependency. D5 moves R1.3's shared SEC client
from Stage 5 to Stage 4, and Stages 5 and 15 now consume it.

Reconciled 2026-09-26 after Stage 4 shipped (plan 6, with its amendment
`specs/completed/pdf-citation-text.md`): Stage 4 is ticked, and the real cohort,
`djia-2024q3-2026q2` v1, is frozen with 33 intervals and 33 candidate issuers
(`docs/verification/djia-cohort.md`). S&P Dow Jones Indices publishes its notices
as PDFs, so Stage 4 also cites PDF text through `pdftext-1`, pinning pypdf 6.19.0;
like `walker-1` here, it builds no document, and Stage 4's Consumes clause on
artifacts holds. Plan 6's final review found Stage 4's P-C4 Exit clause
overstated: evidence published after the cutoff changes no interval, mapping,
count, or candidate issuer, but it is kept as withheld, and the manifest's content
hash covers it and the SEC files that identities cite. The clause now says what
shipped. It also found that the SEC and web client locks hold per checkout, not
per machine. Stages 5 and 15 now name what they consume from Stage 4 and cite plan
6's Handoffs (`specs/plans/completed/6-point-in-time-djia-cohort.md`, §Handoffs).
Of plan 6's six deferred items (`specs/deferred_items.md`,
`6-point-in-time-djia-cohort`), Stage 5 cites the two it must settle first, the
universe's operative identity and the lock scope, and Stage 15 cites the second. No
other unticked stage consumes Stage 4, and none changes.

Reconciled again 2026-09-26, on resuming the roadmap before Stage 5. No stage has
shipped since the previous reconcile, but PR #5's review added three commits before
its merge at `4cfd101`: an SEC host written with DNS's trailing dot now counts as an
SEC host, so it can no longer reach SEC outside the shared client; a `Cik` must be
ten ASCII digits; and the overrides file refuses two `holding_alias` overrides for
one holding name. The review also extended plan 6's deferred item on what an
override's dates mean, and added a seventh, on matching a fund report's holdings
only by names cited by its date. Rebuilt offline on `main`, the cohort still gives
v1's content hash. Stage 5's Consumes line now cites the two date items, since they
bear on the universe identity Stage 5 decides. No other stage changes.

Reconciled 2026-09-28, on resuming the roadmap before Stage 5's plan B. Plan A
(plan 7, `specs/plans/completed/7-event-discovery-eligibility-and-acquisition-plan-a.md`)
shipped in PR #6, merged at `0379fd5`, and the stage spec,
`specs/completed/event-discovery-eligibility-and-acquisition.md`, carries its Plan A stamp.
Stage 5 stays unticked until plan B completes (that spec's EV1 and Rollout). The
real event manifest, `events-v1` (263 events, 239 eligible), and the 40-event
pilot, `pilot-v1`, are frozen under `config/corpus/djia-2024q3-2026q2/`
(`docs/verification/djia-events.md`). Stage 5's brainstorming pass produced that
approved spec, so plan B routes to writing-plans, as the spec's header says. Plan
7 made the SEC and web client locks machine-wide, so Stage 15's Consumes line no
longer says they hold per checkout. Stage 5's Consumes line now names what plan A
settled, plan 7's Handoffs to plan B, and the deferred items from PR #6's review
of plan 7 that plan B must settle first, since the stage spec's §Deferred items
table predates them. The Open question and the re-validation of Stages 6, 10, 11
and 15 wait for Stage 5's tick, as the stage spec's Rollout says. No other stage
changes.

Reconciled 2026-09-28 after Stage 5 shipped (plans 7 and 8): Stage 5 is ticked, and
its stage spec, `specs/completed/event-discovery-eligibility-and-acquisition.md`,
carries its stamp. Plan 8
(`specs/plans/completed/8-event-discovery-eligibility-and-acquisition-plan-b.md`)
acquired pilot v1's 40 releases through the shared SEC client: 40 requests, under an
approved cap of 56, parsed 39, and one reviewed `set_release_document` override
parsed the last, Disney's for 2026-03-28, with no request
(`config/corpus/djia-2024q3-2026q2/acquisition-overrides.toml`;
`docs/verification/djia-events.md`). The stage spec's EV2 and EV3 answer the Open
question, so that section is gone: discovery evidence is not acquisition under P-C7,
and a frozen event names its release filing, never an exhibit (EV2); an event whose
release filing cannot be identified is `ambiguous` until a signed override sets or
retains it (EV3). Stages 6, 10, 13 and 15 now name what they consume from plan 8.
Stages 7 and 11 are re-validated unchanged: Stage 7 reads Stage 3's committed
fixtures only, and Stage 11 takes the pilot through Stage 6. Plan 8's final review
ordered the state table's runs by their start and each run by its sequence, held each
document to `<event_id>:release`, and locked the runs directory (`55ea811`); Stages
6, 13 and 15 carry what that changes. Stage 15's Exit now says how live acquisition
runs: at a request count approved at a gate. Plan 8 deferred nothing; the recovery of
a saved response that cannot be read (P2.1, P2.2) stays open, and Stage 15 cites it.

Reconciled again 2026-09-28, on resuming the roadmap before Stage 6. No stage has
shipped since the previous reconcile. PR #7's review changed two things before its
merge at `eb729d8`: `c7e41fa` made Stage 15's approved count the client's cap,
against which each retry counts, and `17faa75` finds an override's application under
any pilot, so its ID keeps its meaning under a later one. Neither changes another
stage. Stage 6's Consumes line now names Stage 1's handoff to it, which the
reconcile after Stage 1 missed: each fixture event carries
`pilot_split = "train_or_exclude"`, and no fixture issuer is in pilot v1.

Amended 2026-09-28 by Stage 6's spec,
`specs/completed/pilot-codebook-split-and-gold-set-protocol.md`, approved the same day. It
amends D2 for Stage 6's gold (GS4), and its test partition's gold waits until Stage
14 freezes its configuration (GS18). Stage 6's Exit and Stages 11 and 14 now say
which partitions each annotates.

Reconciled 2026-10-03 after Stage 6 shipped (plan 9,
`specs/plans/completed/9-pilot-codebook-split-and-gold-set-protocol.md`): Stage 6 is
ticked, and its stage spec, `specs/completed/pilot-codebook-split-and-gold-set-protocol.md`,
carries its stamp. Stage 6 pins pilot v1 by content hash (GS2) and splits it by
`issuer-time/1` into 20 train, 8 dev and 7 test events, with 5 excluded; all 40
documents are `parsed`, so the D4 report records the three failure classes as coverage
gaps. Codebook v0, `codebooks/djia-pilot/codebook-v0.toml`, holds 22 themes in two
levels and is approved in ADR 0003. Three train bundles are signed, each drafted by
Claude Opus 5.5 and verified by the user, who accepted every item as drafted
(`docs/verification/pilot-v1-gold-set.md`). Two of plan 9's decisions amend what later
stages read: a gold file is named for its event with the colon as an underscore
(P9-3), and `no_theme` stays true unless an assignment pairs a claim with a theme under
`supports` (P9-4). Plan 9's final review added an offline integrity test of the
committed records, and the root pytest configuration now passes `--tb=short`, since
pytest's default traceback prints a failing frame's arguments, which in Stage 6's local
legs may hold pilot text. Stages 7, 8, 9, 11, 12, 14 and 16 now name what they consume
from plan 9 (§Handoffs), and Stages 9 to 12 carry the questions the user raised while
v0 was drafted: a parent roll-up rule, hierarchy-aware scoring, deeper levels or a
scope attribute, and fields beyond theme. Stage 8's Exit names negation, which no
Stage 6 hard negative covers: they are `issuer`, `period` and `section` kinds. Of plan
9's eight deferred items (`specs/deferred_items.md`, `9-pilot-codebook-split-and-gold-set-protocol`), Stage 11 needs the other 17 train
and 8 dev bundles and the gold hardening due before the next of them, Stage 7 the two
anchoring questions, and Stage 14 the refusal of test gold at validation. Stages 13 and
15 consume nothing from Stage 6 and do not change.

Reconciled 2026-10-04, on resuming the roadmap before Stage 7. No stage has shipped
since the previous reconcile. Plan 10
(`specs/plans/completed/10-harden-the-gold-before-bundle-4.md`), merged at `c5719f8`,
implemented one of plan 9's deferred items, not a stage: the gold validator refuses a
claim no assignment row codes, or a quote nothing cites, as `unreferenced` (M1); each
record's drafting aid comes from its kept draft (T8-M1); and no pilot sentence sits in
a list item under an `other` element (M5). Its own edit to Stage 11's Consumes line
landed with it. Stage 7 now carries M5's count, which its deferred anchoring item
names; Stage 11, the deferred refusal of a kept draft that repeats an ID, due before it
counts GS5's shares; and Stage 12, the deferred fix to `codebook freeze`'s drafting
aid, due before codebook v1 is frozen (`specs/deferred_items.md`,
`10-harden-the-gold-before-bundle-4`). Four corrections to the previous reconcile:
Stages 7, 8 and 9 now carry GS13, under which no drafting session sees their code,
prompts, or outputs while any bundle remains to be drafted, Stage 14's test bundles
included; Stage 12 carries T11-M1, which shares P10-7's trigger; Stage 7 carries the
deferred move of `canonical_json` into `earnings-core`, should its spec change core;
and Stage 7's "only — not Stage 5" now covers its tests and Exit alone, since train
gold reaches it through Stage 5's pilot documents. Stages 10 and 13 to 16 are
re-validated unchanged.

Amended 2026-10-04 by Stage 7's spec, `specs/completed/evidence-selection-and-verification.md`,
approved the same day. It amends the handoff Stage 7 receives from Stages 3 and 6 at
two points, and Stage 7's Consumes line now names both. ES9 excepts a transparent
container from the rule that no `other` element is narrative: one with children and no
non-space character outside them, which walker-1 makes from a `<ul>` or `<ol>`. This
amends the Stage 3 spec's handoff, GS15, and P9-19, and changes no pilot verdict (M5).
ES12 makes the pointer units S1's sentences together with the narrative elements S1
never splits, such as headings.

Reconciled 2026-10-05 after Stage 7 shipped in PR #11, merged at `f4081c9`.
Its stage spec, `specs/completed/evidence-selection-and-verification.md`, carries
the authoritative Stage 7 stamp for plans 11 and 12, so Stage 7 is ticked. Plan 11
closed the core and anchoring items: `reverify_span`, `VALIDATOR_VERSION = "3"`,
the shared `canonical_json`/`digest`, and transparent containers. Plan 12 shipped
`pointer-traversal/1`, extraction schema 1, and stored codebook-free claims;
`docs/verification/evidence-selection.md` records its accepted deviations and
ADR 0004's fixture-test model, which selects no production model. Stage 7 read no
pilot text or gold, added no command, and wrote no Stage 5 processing state.

Stages 8–16 were re-validated against those contracts and the Stage 7 spec's
§Handoffs to later stages. Stages 8–11 and 13–16 now name the shipped interfaces
and their deferred triggers; Stage 12 is unchanged. Stage 8's theme-definition
input remains a question for brainstorming because the extractor supplies no
theme. Stage 10 owns the first extraction command and state-table mapping; Stage
11 owns the first pilot extraction and fresh-call cache bypass; Stage 13 checks
transcript blocks; Stage 14 takes the existing no-budget planner and adapter seam;
Stage 15 settles concurrent cache/store writes if it adds workers; Stage 16 adapts
the self-hosted-only cost record before hosted dispatch. The plan 12 deferred
items remain in `specs/deferred_items.md`, with conditional triggers preserved.
No stage order or ROUTING changes, and the initial gap table remains the dated
entry analysis. Next: Stage 8 via brainstorming in a fresh session.


Reconciled 2026-10-05 after Stage 8 completion (plan 13). The authoritative stamp
in `specs/completed/semantic-support-assessment.md` records the actual primary V4
pass, the user’s full root/wording gates and cleared final review; Stage 8 is
therefore ticked. Its support schema 1 and `semantic-support/1` preserve raw signals
and processing outcomes, with repeated exact-span gates, four separately identified
family/presentation trials, bounded retries/ceilings, raw caches and immutable typed
storage. No accepted assignments, calibration, command, pilot extraction or
concurrent workers shipped. ADR 0005 adopts the verified MiniCheck CPU float32
path with complete input limit 512; alternative real inference remains unrun.

All remaining stages were checked against this stamp and the shipped library seams.
Stages 9/10/11/13/15 now name their specific support obligations; Stages 12/14/16
retain their prior routing and dependencies. Stage 9 proposes explicit targets then
assesses them before its assignment decision; Stage 10 re-verifies stored support
before export and distinguishes incomplete/flagged/refused results from no themes;
Stage 11 owns expert labels, production panel/policy, view/pooling selection,
preregistered floors/V6 and bypass across extraction/scorer/judge caches; Stage 13
adapts release context; Stage 15 settles writer/worker safety. GS13 and every prior
deferred trigger remain binding. No Stage 8 item was deferred and no unrelated
backlog item was closed. Integration remains the user’s choice; this reconciliation
does not start another stage. The dated initial gap table is preserved.

Reconciled 2026-10-06 after Stage 9 completion (plan 14). The authoritative
Stage 9 stamp is in the live shared specification's Rollout. Coding schema 1 /
`deductive-coding/1` preserves core 2 / validator `"3"`, extraction 1 /
`pointer-traversal/1`, support 1 / `semantic-support/1`, Stage 6 records and v0.
`docs/verification/deductive-coding.md` records actual controller checks, the
user-only full-root and both wording passes, and the cleared whole-branch review.
GS13 remains verbatim through Stage 14's final gold drafting; no implementing or
reviewing session opened pilot text, gold, drafts or views, or dereferenced
codebook examples.

Stages 10–16 were revalidated against the shipped contracts. Stage 10 receives
`CodingRun`, its eight tables, `read_coding_run` and `reverify_coding_run`, and
must rebind current source/support/policy before aggregation/export; refused,
incomplete, review, rejected and valid-unmatched remain distinct. Stage 11 owns
production policy/calibration, thresholds, model/panel and view/pooling choices,
agreement floors and fresh-call stability across all four caches. The annotations
are unevaluated model interpretations, not gold fields or support decisions.
Stage 12 receives pointer-only novelty for human adjudication and versioned new
codebooks. Stages 13/14 retain transcript adaptation and frozen-configuration test
gold; Stage 15 must settle worker/allowance coordination and classifier-cache/
coding-store safety together with extraction/support before introducing workers;
Stage 16 retains its separate optional hosted ceiling and authorization.
No stage order or ROUTING changed, no later stage began, and no unrelated deferred
item was closed. Integration remains the user's choice. Next: Stage 10 via
writing-plans in a fresh session.

## Stage 10 reconciliation — 2026-10-08

The shared specification Rollout stamps Stage 10 COMPLETE through completed plan 15. Only Stage 10 is newly ticked; stages 11–16 retain their order, ROUTING, requirements and ownership, revalidated below against the shipped seams. `read_analysis_run(directory: Path) -> StoredAnalysisRun` checks structural published byte bindings; `reverify_analysis_run(stored, inputs, policy, families) -> None` checks current inputs before consumption/export. Fourteen table schemas and analysis/report/workflow schema 1 shipped; processing schema 2 retains legacy schema 1; core schema 2 is unchanged. V8/V10 prove fixture machinery/arithmetic only. Human V5 native/manual outcomes are observed, capture/HTTPS unverified. Technical review and human counts/SHAs appear in `docs/verification/theme-vertical-slice.md`; completion documentation review and integration remain pending. Next: Stage 11 planning through derive-roadmap/brainstorming, with no later execution here.

## Gap analysis

¹ Searched `packages/*/src`, `apps/*/src`, `tests/{contracts,fixtures,integration}`,
`config/`, `codebooks/`, `prompts/`, and `expirements/` at `bdcf0a4`: each
`__init__.py` is a two-line `hello()` stub; every other listed directory is empty.

² Searched the same paths at `6021323` for index-membership, cohort, or
security-to-issuer resolution code: none. `expirements/parser-fidelity/` and
`tests/fixtures/releases/` now hold Stage 1's harness and release fixtures, whose
CIK fields serve EDGAR discovery and fixture provenance only.

Decisions taken by the user on 2026-09-22, resolving the batched questions:
**D1** — V6 gates only metrics the pilot can estimate (R12.2 conflicts with
V6 as written); **D2** — the user is the sole annotator (R12.6, R8.4; for Stage 1 gold, amended 2026-09-23 by `specs/release-parser-fidelity.md` F9: Codex drafts, the user verifies every block; for Stage 6's gold, amended 2026-09-28 by `specs/completed/pilot-codebook-split-and-gold-set-protocol.md` GS4: a Claude session drafts, the user verifies every item and reads each bundle for omissions);
**D3** — R14.2's hosted ceiling is an optional stage; R5.3/V3 are unstaged.

**D4** — taken 2026-09-22 with the cohort amendment, resolving R12.4/R12.5
against `P-C7`. R12.4 required the pilot manifest to *hold* unavailable,
restricted, and parser-failure bundles; `P-C7` forbids selection from depending
on acquisition, parse, or theme outcomes. Selection stays outcome-blind, and
failure-class coverage becomes an **observed report over the frozen manifest**: a
class absent from the 40 selected events is reported as a coverage gap and is
never repaired by reselecting. R12.5's curated hard negatives move to fixtures
held outside the pilot manifest, exercised by contract tests rather than by event
selection. Widened at review the same day: hard-negative claims drawn from
confusable periods, issuers, and sections of the frozen pilot documents are also
annotated with the gold set and scored with the pilot metrics, which changes no
pilot row.

**D5** — taken 2026-09-26 on resuming the roadmap, resolving R1.3 against `P-VL`.
R1.3's 2 req/s limit is one allowance for every adapter and worker (A §393–400),
yet the roadmap built the shared client in Stage 5. Stage 4 comes first and must
fetch CIK evidence from SEC under the same policy (`P §Issuer resolution`,
`P §Optional live verification`). Stage 4 now builds the shared SEC client and
closes R1.3, and Stage 5's EDGAR adapter sends through that client. Stage 1's
live-fetch client, `expirements/parser-fidelity/pf_fetch.py`, is the reference
design: port it, never import it.

Counting note: `P` counts **issuer-events** and targets exactly 40 (`P-C5`),
while R12.2 counts hand-coded documents or bundles at 20–40. The two are
compatible — 40 sits inside 20–40 — but one event may yield several bundles
(a release plus its transcript, copies, or revisions), so the bundle count can
exceed the event count. Never treat the two numbers as the same quantity.

| Req | Verdict | Evidence | Note |
|---|---|---|---|
| R1.1 | missing | none found¹ | |
| R1.2 | missing | none found¹ | Candidate library only as optional `edgar` extra (`packages/earnings-ingestion/pyproject.toml:21`) |
| R1.3 | missing | none found¹ | `tenacity` declared (`packages/earnings-ingestion/pyproject.toml:14`); no limiter. Moved to Stage 4 by D5 |
| R1.4 | missing | none found¹ | State list differs from A §644 (adds restricted/acquired/completed; A has available/processed); spec is the later text — reconcile in-stage |
| R1.5 | missing | none found¹ | |
| R2.1 | missing | none found¹ | |
| R2.2 | missing | none found¹ | Open → V7 |
| R2.3 | missing | none found¹ | |
| R3.1 | missing | none found¹ | |
| R3.2 | missing | none found¹ | Python `str` indices are already code points; the hazard is the browser boundary (R7) |
| R3.3 | missing | none found¹ | |
| R3.4 | missing | none found¹ | Amends A §563; `AGENTS.md:592` points at the spec |
| R3.5 | missing | none found¹ | |
| R4.1 | missing | none found¹ | Open → V2 |
| R4.2 | missing | none found¹ | |
| R4.3 | missing | none found¹ | |
| R5.1 | missing | none found¹ | |
| R5.2 | missing | none found¹ | `rapidfuzz` in optional `fuzzy-localization` extra (`packages/earnings-themes/pyproject.toml:45`) |
| R5.3 | missing | none found¹ | Unstaged (D3) — see Completion |
| R5.4 | missing | none found¹ | |
| R5.5 | missing | none found¹ | |
| R6.1 | missing | none found¹ | |
| R6.2 | missing | none found¹ | |
| R7.1 | missing | none found¹ | |
| R7.2 | missing | none found¹ | Open → V5 |
| R8.1 | missing | none found¹ | |
| R8.2 | missing | none found¹ | Open → V4; no scorer dependency declared |
| R8.3 | missing | none found¹ | |
| R8.4 | missing | none found¹ | ≥50 labels supplied by the user (D2) |
| R8.5 | missing | none found¹ | |
| R8.6 | missing | none found¹ | |
| R9.1 | missing | none found¹ | |
| R9.2 | missing | none found¹ | |
| R9.3 | missing | none found¹ | |
| R9.4 | missing | none found¹ | |
| R9.5 | missing | none found¹ | See `embeddings` extra row |
| R9.6 | missing | none found¹ | |
| R9.7 | missing | `codebooks/` empty | No invented taxonomy (compliant); decision-record mechanism absent |
| R9.8 | missing | none found¹ | |
| R9.9 | missing | none found¹ | |
| R10.1 | missing | none found¹ | Amends A §452; `AGENTS.md:478` points at the spec |
| R10.2 | missing | none found¹ | |
| R10.3 | missing | none found¹ | |
| R11.1 | missing | none found¹ | |
| R11.2 | missing | none found¹ | |
| R11.3 | missing | none found¹ | |
| R11.4 | missing | none found¹ | |
| R11.5 | missing | none found¹ | |
| R11.6 | missing | none found¹ | |
| R12.1 | missing | none found¹ | |
| R12.2 | missing | none found¹ | Amends A §728; `AGENTS.md:748` points at the spec |
| R12.3 | missing | none found¹ | |
| R12.4 | missing | none found¹ | Reframed by D4: observed coverage over the frozen pilot manifest |
| R12.5 | missing | none found¹ | Reframed by D4: out-of-manifest fixtures plus hard-negative claims in pilot documents |
| R12.6 | missing | none found¹ | Single annotator (D2): agreement not measurable — see Completion |
| R12.7 | missing | none found¹ | |
| R12.8 | missing | none found¹ | |
| R12.9 | missing | none found¹ | |
| R12.10 | missing | none found¹ | |
| R13.1 | missing | none found¹ | Conflicts with R12.2; resolved by D1 — see Completion |
| R13.2 | missing | none found¹ | Binding with R6.1 |
| R13.3 | missing | none found¹ | Held-out result is feasibility-level (D1) |
| R14.1 | missing | none found¹ | Required dependencies carry no provider SDK (compliant surface); no fake adapter or replay |
| R14.2 | missing | none found¹ | Optional Stage 16 (D3) |
| R14.3 | implemented-as-specified | `packages/earnings-themes/pyproject.toml:33,50` (optional extras only); `AGENTS-jev-addendum.md:4-14`; `specs/jev-integration-spec.md:3-24` | Benchmark-against-R8.2 clause applies only under separate authorization |
| R14.4 | implemented-as-specified | `apps/earnings-pipeline/pyproject.toml:23` (`langgraph` optional only); no optimizer or multi-agent dependency declared | Standing constraint; "usable without frameworks" becomes testable once domain code exists |
| R14.5 | missing | `uv.lock`: edgartools 5.58.0 depends on `pandas` | V1 very likely non-vacuous |
| R14.6 | missing | none found¹ | |
| R14.7 | missing | none found¹ | |
| V1 | missing | none found¹ | |
| V2 | missing | none found¹ | |
| V3 | missing | none found¹ | Needs a billable call outside R14.2 and against R14.1; unstaged (D3) |
| V4 | missing | none found¹ | |
| V5 | missing | none found¹ | |
| V6 | missing | none found¹ | Scope narrowed by D1 |
| V7 | missing | none found¹ | |
| V8 | missing | none found¹ | |
| V9 | missing | none found¹ | |
| V10 | missing | none found¹ | |
| V11 | missing | none found¹ | |
| `extraction`/`openai`/`anthropic` extras | in-code-but-not-in-spec | `packages/earnings-themes/pyproject.toml:19,23-28` | Spec names no framework (A §664 proposes PydanticAI); hosted SDKs serve only R14.2/R5.3 — flag, not defect |
| `embeddings` extra | in-code-but-not-in-spec | `packages/earnings-themes/pyproject.toml:39` | Sits on the themes package; R9.5 places clustering outside the pipeline |
| `entity-matching` extra | in-code-but-not-in-spec | `packages/earnings-ingestion/pyproject.toml:25` | Serves company enrichment, which is out of this spec's scope; Stage 4 may use it only to generate issuer-resolution candidates, since fuzzy similarity is a candidate score, never proof of identity (A §429) |
| Dev tooling | in-code-but-not-in-spec | `pyproject.toml:22-35` | `dev` group and Ruff config exist; no pytest config, `live` marker, or import mode (A §193) |
| P-C1 | missing | none found² | DJIA resolved point in time, not as one current roster; Stage 4 |
| P-C2 | missing | none found² | Eligibility keyed to `first_publication_time`; defined in Stage 4, joined in Stage 5 |
| P-C3 | missing | none found² | Window `[2024-07-01, 2026-07-01)`; reported fiscal labels stay separate fields |
| P-C4 | missing | none found² | Public-information cutoff `2026-09-22` |
| P-C5 | missing | none found² | Deterministic 40-event pilot; supersedes the codebook stage's former sample choice (D4) |
| P-C6 | missing | none found² | Full eight-quarter run is Stage 15; observed count never forced to `30 × 8` |
| P-C7 | missing | none found² | Cohort-before-acquisition order is binding; split across Stages 4 and 5 |
| P-A4 | missing | none found² | Stage 4 acceptance criteria |
| P-A5 | missing | none found² | Stage 5 acceptance criteria |
| P-A15 | missing | none found² | Stage 15 acceptance criteria |
| P-VF | missing | none found² | 19 deterministic fixture cases; split across Stages 4 and 5 |
| P-VI | missing | none found² | Offline integration replay, anchor evidence through frozen pilot manifest |
| P-VL | missing | none found² | Optional `live` verification of the real roster — source access and terms, dated-evidence parsing, reconciliation against the corroborating snapshot; never in default CI; Stage 4 |

Totals: 91 missing · 2 implemented-as-specified · 4 in-code-but-not-in-spec ·
0 implemented-differently · 0 out-of-repo. The 91 comprises 78 rows from
`specs/evidence-linked-theme-extraction.md` and 13 from
`specs/point-in-time-djia-cohort.md` (the `P-*` rows).

## Stages

- [x] Stage 1: Acquisition-library and parser fidelity (investigation)
      Objective: Establish by measurement which parser yields faithful typed elements on real releases, and what the pinned acquisition library returns.
      Spec: V1, V2 (discharging the open markers in R14.5 and R4.1); R1.3 for live fetches; A §242, A §425 for fixtures.
      Gap closed: V1, V2.
      Consumes: nothing.
      Produces: a decision record naming the parser, with V2 rates per candidate and fixture class; V1 return types for edgartools 5.58.0; a fixture corpus spanning V2's four release classes, with hand-marked structure, under `tests/fixtures/`.
      Exit: the decision record reports reading-order corruption, footnote merging, and header loss for every candidate on every class (V2); V1 lists the concrete return type of each exhibit and table path (V1); every committed fixture has a source-register entry recording its redistribution basis.
      ROUTING: brainstorming

- [x] Stage 2: Core evidence spine
      Objective: Give `earnings-core` the contracts and exactness validator that every later stage builds on.
      Spec: R3.1–R3.4 (contracts), R4.1 (element contract), R5.4, R5.5, R6.1, R13.2, V9; A §193.
      Gap closed: R3.2, R3.3, R5.4, R5.5, R6.1, R13.2; V9 (all cases except normalization and sentence splitting); Dev tooling row.
      Consumes: Stage 1's decision record, ADR 0001, and V2's element types and nesting observed in the fixtures' gold.
      Produces: `earnings-core` contracts for a hashed, versioned canonical document, typed elements with stable IDs and code-point spans, overlay masks, and prefix/suffix span locators; an R6.1 validator with no tolerance parameter; root pytest configuration with a registered `live` marker and collision-safe test imports.
      Exit: `uv run --locked --all-packages pytest packages apps tests -m "not live"` passes the Stage 2 V9 cases, each failure class rejected with a recorded reason (R3.2/R3.3/R5.4/R5.5/R6.1/R13.2); a test shows applying a mask leaves the canonical hash unchanged; the pytest configuration registers `live` (Dev tooling row).
      ROUTING: writing-plans

- [x] Stage 3: Structure-aware canonicalization
      Objective: Turn saved release bytes into hashed, versioned canonical documents with typed elements, quarantined table cells, and boilerplate masks.
      Spec: R3.1, R3.4 (versioned policy), R3.5, R4.1–R4.3, V9; A §498–516; `specs/browser-rendering-integration.md` (B1–B5, B7–B9, and its Stage 3 sections).
      Gap closed: R3.1, R3.5, R4.1, R4.2, R4.3; V9 (normalization, sentence splitting).
      Consumes: Stage 1 parser decision (ADR 0001), V2's residual failures and findings for Stage 3, and the fixtures with their gold; Stage 2's `earnings_core` contracts and checks (`CanonicalDocument`, `DocumentElement` with `TableCellContext`, `OverlayMask` via `apply_masks`, `validate_elements`) and plan 3's handoffs to Stage 3 (`specs/plans/completed/3-core-evidence-spine.md` §Handoffs): rerun the two-parser element contract with the ported walker and the DOM/layout extractor, alignment-failure reasons, table grids, version naming, the boilerplate policy, page artifacts, and UTF-16 conversion at the browser boundary.
      Produces: an ingestion canonicalizer from saved bytes plus metadata to a canonical document version, with no network client; table cells stored as cell evidence with header context; OCR-derived elements flagged; masks from a versioned boilerplate policy; a repeatable R3.5 fidelity check.
      Exit: every Stage 1 fixture canonicalizes offline and passes the Stage 2 validator (R3.1/R4.1); a test shows no narrative element contains table-cell text (R4.2); a test shows OCR-derived text flagged and never verified as an original quotation (R4.3); V9 normalization and financial-abbreviation/decimal splitting cases pass; an R3.5 fidelity report on a sample covers all six named categories (R3.5). For the browser spec's Stage 3 verification (`specs/completed/structure-aware-canonicalization.md` §Exit criteria, plan B): the `browser-capture` extra, the pinned binaries, and the setup command exist, and no processing run downloads anything (B3/B8); calibration on the three named fixture categories publishes classified differences and alters no gold; a network guard shows capture makes no external request and runs no document JavaScript (B7); two captures in the pinned environment share one rendered-text hash; every `layout-1` candidate is an exact canonical span or carries `alignment_failed`, and the two-parser contract reruns with the real pair (B5); the pre-registered comparison reports every named metric and targeted class for the three configurations; ADR 0002 is accepted (B4); the R3.5 report is final; the AST scan and the runtime import-boundary checks pass; the default suite needs no browser and makes no network request, while browser checks run only with `-m browser`, skip visibly without the pinned binaries, and record the exact environment.
      ROUTING: brainstorming

- [x] Stage 4: Point-in-time DJIA cohort
      Objective: Freeze a versioned, point-in-time DJIA universe — security-level membership intervals resolved to issuers and zero-padded CIKs — before any earnings document is acquired.
      Spec: P-C1, P-C2, P-C3, P-C4, P-C7, P-A4; P §Temporal definitions, §Data contracts (universe definition, membership assertion), §Membership evidence and source rights, §Issuer resolution, §Failure handling, §Verification; A §249–269 (index membership and identifiers, including the zero-padded CIK at A §264), A §429 (entity-resolution rules this stage follows); A §242 (the source register); R1.3 and A §393–400 (the shared SEC client, D5).
      Gap closed: P-C1, P-C2 (the membership-reference definition only; the event join is Stage 5), P-C3, P-C4, P-C7 (the cohort-before-acquisition half), P-A4; P-VF (interval, resolution, conflict, and cutoff cases), P-VI (its membership-interval and issuer-resolution legs), P-VL; R1.3 (D5).
      Consumes: Stage 2's provenance primitives `sha256_hex` and `ArtifactRef` (content hash, media type, portable `storage_ref`, and `RightsStatus` with its `rights_basis`), whose `storage_ref` has refused a `file:` scheme in any case, a drive letter, and a `..` segment since Stage 3's schema version 2 (plan 4 §Handoffs); and the root pytest configuration, whose registered `live` and `browser` markers are deselected unless `-m live` or `-m browser` is passed. Retrieval metadata (source URL, `retrieved_at`, request parameters) is not in core: this stage defines it at its own grain or proposes a core schema bump (plan 3 §Handoffs). Stage 1's source register, `docs/source-register.toml`, holds A §242's fields for release sources. The README records that Stage 4 adds a second register for index-membership sources. The `sec-edgar` entry records R1.3's verified access behavior, which the shared SEC client must implement and which covers this stage's CIK requests; that entry's `access_method` still names Stage 1's harness client. `fetch_policy_pages.py verify` checks the register's quotes against saved pages, a harness command that no package imports. Stage 1's `expirements/parser-fidelity/pf_fetch.py` is the reference design for the shared SEC client (D5): port it, never import it. No parser, canonicalizer, document, or model artifact — the stage is placed after Stage 3 so that acquisition follows it immediately, but its hard dependencies are Stage 2's contracts and Stage 1's `sec-edgar` register entry.
      Produces: in `earnings-ingestion`, a versioned DJIA universe definition at P's universe grain (`universe_name = "djia"`, `period_end_start = 2024-07-01`, `period_end_stop = 2026-07-01`, `public_information_cutoff = 2026-09-22`, `membership_reference = first_publication_time`); security-level membership assertions at one row per index, security, effective interval, and source-evidence item, with half-open `[effective_from, effective_to)` intervals and a `status` of `supported`, `conflicting`, `ambiguous`, or `withheld`; security-to-issuer mappings carrying 10-character zero-padded CIK evidence; the derived union of candidate issuers over every membership interval that overlaps the eligible-publication range, `2024-07-01` through the `2026-09-22` cutoff (membership is judged at `first_publication_time`, so an issuer added after `2026-07-01` can still carry an eligible event); a membership source register with owner, URL, access method, cost, terms, redistribution status, coverage, update behavior, known limitations, and last verification date; a coverage and conflict report; synthetic redistributable fixtures; version-controlled manual override assertions with evidence, rationale, reviewer, and effective dates; an opt-in `live` verification that checks source accessibility and current terms, parses the dated evidence behind the real manifest, and reconciles official changes against the corroborating snapshot, recording retrieval metadata under the shared rate and identification policies (P-VL); the shared SEC client of R1.3 (D5), through which this stage and every later adapter send SEC requests.
      Exit: every membership interval resolves to a source-evidence row and every resolved CIK is a 10-character zero-padded string (P-A4); fixture tests build intervals from an anchor plus additions and removals, with inclusive starts and exclusive ends, and an open interval carrying no `effective_to` (P-VF); a missing anchor snapshot refuses to freeze the manifest with the reason recorded, and conflicting effective dates persist as separate assertions rather than being merged and hold the freeze until a recorded review resolves them (P §Failure handling); the coverage and conflict report lists every interval conflict and coverage gap (P-A4); evidence first published after 2026-09-22 changes no interval, mapping, count, or candidate issuer, and is reported as withheld (P-C4); a test shows no current snapshot silently backdated and no ETF holdings record treated as the official roster; a test shows historical ticker changes and multiple securities preserved, and one issuer's several securities deriving one issuer row (P-VF); source access and redistribution status are recorded for every source, with unclear rights keeping artifacts local; the universe manifest freezes with a version and content hash written atomically, and refuses to freeze on unresolved issuer identity unless the record is explicitly retained as unresolved and excluded with its reason; the default suite makes no network call, uses no proprietary roster, and needs no credentials, while the `live` verification runs only when opted in and records its result with retrieval metadata (P-VL); tests hold concurrent workers sending through the shared SEC client at or below 2 req/s and stop on a persistent 403 without rotating identity (R1.3, D5).
      ROUTING: writing-plans — `specs/point-in-time-djia-cohort.md` is this stage's spec; it needs no brainstorming pass.

- [x] Stage 5: Event discovery, eligibility, and acquisition
      Objective: Resolve expected earnings events and their first supported publication, freeze the eligible-event and 40-event pilot manifests, and only then acquire the selected releases from EDGAR.
      Spec: R1.1–R1.5, R14.5; A §391–427; P-C2, P-C5, P-C7, P-A5; P §Stage 5 — Event discovery, eligibility, and acquisition, §Temporal definitions, §Data contracts (expected event, pilot selection), §Deterministic pilot selection, §Failure handling.
      Gap closed: R1.1, R1.2, R1.4, R1.5, R14.5; P-C2 (the event join), P-C5, P-C7 (the freeze-before-outcomes half), P-A5; P-VF (period-window, eligibility-reason, and selection cases), P-VI.
      Consumes: the frozen Stage 4 cohort — universe manifest, membership intervals, and security-to-issuer resolution with CIK evidence (plan 6 §Handoffs): `cohort.freeze.load_manifest(path)` reads a manifest with no saved artifact and rechecks its hash; the real one is `config/universe/djia/manifests/djia-2024q3-2026q2-v<N>.json`, the latest version winning, and the synthetic `tests/fixtures/cohort/manifests/djia-synthetic-v1.json`, which `write_synthetic_cohort` regenerates, is the offline fixture for P-VI; intervals are half-open dates whose bounds keep their announced timing and basis, an `anchor_snapshot` start being a lower bound and never an entry date (P6-23), with `MembershipInterval.contains`/`overlaps` and `cohort.intervals.roster(intervals, day)` for date questions, and Stage 4 invents no time; `manifest.issuers` holds one row per CIK with its securities, `candidate_issuer_ids` is the union over intervals overlapping the eligible-publication range (P6-13), and a `retained_unresolved` mapping is excluded with its reason; the manifest's `content_hash` also covers withheld evidence and the SEC files its identities cite, so this stage keys its manifests on the intervals, mappings, and candidate issuers, never on that hash (`specs/deferred_items.md`, `6-point-in-time-djia-cohort`); the build records each override's dates but applies the override on every date, so an `IssuerMapping` carries no dates, and two deferred design items, what an override's dates mean and whether a fund report's holdings match only names cited by its date, stay undecided: that key takes the mappings as they stand or settles the pair first (`specs/deferred_items.md`, `6-point-in-time-djia-cohort`); `selection_policy_version = "djia-pilot/1"` is recorded but undefined, and this stage defines it from `P §Deterministic pilot selection` or bumps the name (P6-4). Stage 4's shared SEC client (R1.3, D5): `earnings_ingestion.sec.client.open_sec_client`, whose `SecClient.fetch(url, expected_types)` returns `Fetched(body, retrieval)`, with `fetch.store.ArtifactStore` for raw snapshots and their `Retrieval` records and `sec.data`'s readers for submissions and filing pages; `Filing.accepted_at` carries SEC's `acceptanceDateTime` offset as written, and whether it is UTC or Eastern is settled before it serves as `filing_acceptance_time` (R1.5); its lock holds per checkout, not per machine, so SEC requests run from one checkout at a time until the deferred fix lands (`specs/deferred_items.md`, `6-point-in-time-djia-cohort`); `EDGAR_IDENTITY` may be exported, so `-m live` sends real requests and needs the same gate; Stage 1 V1 findings and V2's finding for Stage 5 (a filing's only EX-99 is not necessarily its press release); Stage 2 contracts; Stage 3's `canonicalize(raw, *, source_document_id, media_type)` under `walker-1`, which needs no browser (ADR 0002), for content inspection (R1.2/R1.5): its `CanonicalizationFailure` reasons are processing states (R1.4), `manifest.raw_sha256` is the raw hash, C2 types EDGAR's header line as `page_artifact`, and a release nested past libxml2's depth limit of 255 fails as `parse_failed`; the R3.5 check (`canonical/fidelity.py`), which reruns on the pilot releases without gold, its second leg only with a capture of each; and `layout1_report.py`'s rules with `preregister.py`, should the layout comparison be repeated on the pilot releases under a new pre-registration, with a new record file and new units (plans 4 and 5 §Handoffs). Plan 5's deferred items on the capture adapter record its known defects (`specs/deferred_items.md`, `5-structure-aware-canonicalization`). Of the inputs above, plan A (plan 7) settled four, superseding their clauses: the SEC and web client locks are held once per machine (`fetch.client.machine_lock_dir()`, or `$EARNINGS_LOCK_DIR`), the acceptance time is the filing index page's Accepted value in America/New_York (EV10), `operative_hash` identifies the universe for Stage 5's records (EV4), and `djia-pilot/1` is defined (EV8). Plan B consumes plan 7's Handoffs to plan B (`specs/plans/completed/7-event-discovery-eligibility-and-acquisition-plan-a.md`, §Handoffs), with its `frozen_pilots` deviation (`17ce98e`). Before its first acquisition or live request, it settles the deferred items whose triggers name it (`specs/deferred_items.md`, `PR #6 review (plan 7)`): two design choices, "Decide which frozen version is current after a revert" (F4) and "Decide whether loading a pilot re-derives its selection" (F10); and "Refuse a redirected response" (F13), "Print the request count on every stop, and take an approved count in every live cohort command" (F31, F35), "Check the CLIs' store and corpus paths before anything runs" (F19, F38), "Refuse a relative `EARNINGS_LOCK_DIR`" (F29), and "Commit the check that the real frozen records hold no source wording" (F20). Three more sit in the code plan B reads, the index page's exhibit table, the Item 2.02 reader, and the store, without naming it: "Cross-check an index page against its submissions row beyond the accession" (F12), "Read a primary document with no Item line as unread", and "Recover a saved response that is present but unusable" (P2.1, P2.2).
      Produces: an expected issuer-period event ledger over the eight period-end quarters in `[2024-07-01, 2026-07-01)`; release discovery that keeps `period_end`, the issuer's `reported_fiscal_year`/`reported_fiscal_quarter`, `first_publication_time`, `filing_acceptance_time`, and `retrieved_at` as separate fields; a per-event eligibility decision of `eligible`, `ineligible`, or `ambiguous` with its `eligibility_reason`; a frozen eligible-event manifest with a content hash; a frozen 40-event pilot manifest whose rows each record `issuer_coverage`, `membership_boundary`, `quarter_coverage`, or `longitudinal_fill`, plus the selection seed, policy version, and eligible-event manifest hash; an opt-in live EDGAR adapter that sends through Stage 4's shared SEC client (D5); immutable raw snapshots with retrieval metadata; a per-document processing-state table including expected-but-absent documents with a `missing_reason`; offline replay from saved responses.
      Exit: the six-step order in `P §Stage 5` is enforced and tested — both manifests freeze before any acquisition, parse, retention, or theme outcome exists, and a test shows the pilot manifest unchanged after acquisition and parser statuses change (P-C7); a selected event stays selected when acquisition, parsing, extraction, or support assessment fails; releases immediately before and after a membership transition resolve to the correct side, and a same-day transition without sufficient ordering precision stays `ambiguous` with no invented time (P-C2); an issuer with several securities yields one expected event per period (P-VF); both period-window boundaries and all three eligibility reasons are covered by fixtures (P-VF); shuffled input order yields a byte-identical pilot manifest that represents every eligible issuer and all eight quarters, and the underfilled, blocked, and mandatory-coverage-overflow cases each stop or mark the pilot as `P §Deterministic pilot selection` requires (P-C5); with at least 40 eligible events the pilot holds exactly 40, every row records its `selection_reason`, and fixtures cover the membership-boundary and repeated-issuer reasons (P-VF); changing membership evidence, issuer resolution, the event corpus, or the selection policy invalidates the manifest and produces a new version and hash (P-VF); freezing the eligible-event manifest refuses unresolved issuer identity or event eligibility unless the record is retained as unresolved and excluded with its reason (P §Failure handling); event records keep `period_end`, the reported fiscal labels, `first_publication_time`, `filing_acceptance_time`, and `retrieved_at` as separate fields, and EDGAR acceptance time establishes first publication only when no earlier supported public source exists, with an unknown time staying unknown (R1.5, P-A5); offline replay of saved EDGAR responses identifies the fixture issuers' releases, including a narrative-only release and alternative exhibit numbering (R1.1/R1.2); a test shows the EDGAR adapter sending only through Stage 4's shared SEC client, with no throttle of its own (R1.3, D5); the state table represents every R1.4 state from fixtures (R1.4); library output is Polars at the boundary, or V1's vacuity is recorded (R14.5).
      ROUTING: brainstorming

- [x] Stage 6: Pilot codebook, split, and gold-set protocol
      Objective: Take the frozen pilot manifest as given, split it by issuer and time, approve codebook v0, and validate annotations, so hand-coding runs while Stages 7–10 are built.
      Spec: R9.2, R9.7, R12.1–R12.6; R13.1 (release-identification labels); D2, D4; P-C5, P-C7.
      Gap closed: R9.2, R9.7, R12.1, R12.3, R12.4 (acquisition-outcome classes as observed coverage, D4), R12.5 (out-of-manifest fixtures and in-document hard-negative claims, D4); R12.6 (limitation, D2).
      Consumes: the frozen Stage 5 pilot manifest — this stage no longer selects the sample: `current_pilot(directory, events, universe)` gives the pilot frozen over the current event manifest, and `load_pilot(path, universe)` rechecks its chain and reselects it; the real one is pilot v1, 40 events, each with its issuer, period end, and fiscal labels in its event manifest row (plan 8 §Handoffs); Stage 3 canonical documents, whose `walker-1` `doc_id`s gold spans bind to: ADR 0002 is decided and no longer holds annotation back, and a later promotion that keeps `walker-1`'s text carries their offsets to its `doc_id` unchanged (plans 4 and 5 §Handoffs). Each pilot event expects one document, its release, `<event_id>:release`; a `parsed` document's state names its `doc_id`, whose canonical document, `data/runs/events/canonical/<doc_id>.json`, is local, never committed, and regenerates offline from the saved exhibit through `canonicalize`. Stage 5's processing states come from `read_runs(data/runs/events/states)` and `current_states(transitions, pilot_hash)`, runs ordered by their start and each by its sequence, and an expected but absent document carries its `missing_reason`. All 40 of pilot v1's are `parsed`, one through a reviewed override whose attempt keeps `release-content/1`'s `not_confirmed` verdict, so the D4 report finds no unavailable, restricted, or failed release and reports each class as a coverage gap. Later states (`partial`, `completed`, `completed-no-theme`) are set through new runs, never by editing a run file, under the runs directory's lock that `events acquire` takes (plan 8 §Handoffs, with its final review's deviation, `55ea811`). Stage 1's fixture manifest, `tests/fixtures/releases/manifest.toml`, marks each of its eight events `pilot_split = "train_or_exclude"`, so a fixture event Stage 6 uses goes to training or is left out, never held out (`specs/release-parser-fidelity.md`, Handoffs).
      Produces: a codebook contract with R9.2's fields; codebook v0 drafted from training-partition bundles only and approved in a decision record; a gold-annotation contract and validator, the contract also carrying hard-negative claims drawn from confusable periods, issuers, and sections of the frozen pilot documents (R12.5, D4); an issuer-and-time split over the frozen manifest; an observed failure-class coverage report over that manifest; curated hard negatives held as fixtures outside the manifest. Gold spans name their canonical version; a later version re-anchors them before reuse, never mutates them.
      Exit: a test places each bundle, with all copies and revisions, in exactly one issuer-and-time split (R12.1/R12.3); the coverage report states the observed count of unavailable, restricted, and parser-failure bundles in the frozen manifest, and a missing class is reported as a coverage gap, never repaired by reselecting; the no-theme count joins the report at Stage 11 for the train and dev partitions, and at Stage 14 for test (R12.4, D4); a test shows the split and the report changing no row of the pilot manifest (P-C7); curated hard negatives exist as fixtures outside the pilot manifest, and the annotation validator accepts hard-negative claims (R12.5, D4); codebook v0's decision record names its training-partition discovery corpus (R9.2/R9.7); annotations on at least three bundles, including release-identification labels, pass the validator; the single-annotator limitation is recorded (R12.6, D2).
      ROUTING: brainstorming

- [x] Stage 7: Evidence selection and verification
      Objective: Extract quote-claim candidates by pointer selection over every analysis-eligible element, keeping only code-verified spans.
      Spec: R5.1, R6.1 (before storage), R6.2, R10.1, R10.2, R14.1, R14.6, R14.7, V11.
      Gap closed: R5.1, R6.2, R10.1 (default path), R10.2, R14.1, R14.6; R14.7/V11 (tool-call and verification-bypass cases).
      Consumes: Stage 2's checks from the `earnings_core` root (plan 3 §Handoffs): `resolve_pointer` for pointers, `parse_span_candidate` then `validate_span`, `validate_elements` once per document, `TextChunk` conversion before storage, `make_locator` for repeated text, `Rejection`, and `VALIDATOR_VERSION` in the R14.6 key, with a stored `VerifiedSpan` re-run through `validate_span` at each later R6.1 gate, since the type alone is not proof; plan 3's four open deferred items, on `VerifiedSpan`, `resolve_pointer`, unvalidated offsets, and `Rejection`'s subject (`specs/deferred_items.md`, `3-core-evidence-spine`); Stage 3's eight `walker-1` canonical fixtures in `tests/fixtures/canonical/` — the only documents its tests and Exit read, never Stage 5's — where element type decides eligibility (`table`, `table_cell`, `page_artifact`, and `other` are never narrative, except a transparent `other` container, by Stage 7's ES9), S1 sentences are the pointer unit, with the narrative elements S1 never splits, such as headings (ES12), masked elements stay in traversal with `MaskedDocument.masks_overlapping` reporting the masks over a span, and `validate_span` refuses OCR text with `ocr_derived_text` (plans 4 and 5 §Handoffs). The review gate's findings stand as limitations of `walker-1` and `boilerplate/1` (`docs/verification/layout-1.md`, "The review gate's findings"): National Health Investors' headline, typed `page_artifact`, is never narrative. `walker-1` also joins words split by `<br>` in table cells (`specs/deferred_items.md`, `5-structure-aware-canonicalization`). From Stage 6 (plan 9 §Handoffs): train gold may inform its prompts, dev and test gold never (A §749), through `load_split(path).events_in(Partition.TRAIN)` and `load_gold(path)`; a pilot document's canonical form is read by `from_fixture_json` from `data/runs/events/canonical/<doc_id>.json`, its `doc_id` named by `parsed_documents(transitions, pilot_hash)` (P9-17); a gold quote sits in the most specific narrative element that holds it, and a narrative set that differs from P9-19's is a finding to report; the gold builds every span through `parse_span_candidate` and stores no `VerifiedSpan`. Before it recomputes context hashes or fixes its narrative set, this stage settles the deferred anchoring item: `context_hash`'s byte format, and whether a list item under an `other` element becomes quotable (`specs/deferred_items.md`, `9-pilot-codebook-split-and-gold-set-protocol`). Plan 10 recorded the count that item names: no pilot v1 sentence sits in such a list item (0 of 5139), and 10 fixture sentences do, in 7 list items in one of the eight fixtures (of 686), so making them quotable changes no pilot verdict, only those 10 fixture sentences' verdicts, which `test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors` pins beside 650 anchored and 26 repeated (`docs/verification/pilot-v1-gold-set.md`, M5). If this stage's spec changes `earnings-core`, as plan 3's four items would, the deferred move of `canonical_json` and its digest into core lands with it, and every committed record must still reproduce byte for byte (`specs/deferred_items.md`, `9-pilot-codebook-split-and-gold-set-protocol`). GS13 binds this stage until the last gold bundle is drafted, Stage 14's test bundles included: no drafting session sees its code, prompts, or outputs, and the gold brief already bars a drafting session from `prompts/` (`specs/completed/pilot-codebook-split-and-gold-set-protocol.md`, GS13; `evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md`).
      Produces: a themes extractor visiting every eligible element; a model-adapter interface with a fake adapter, response replay, and an R14.6-keyed cache; one open-weight local adapter behind the `live` marker, its weight license recorded; stored, auditable rejections built on Stage 2's `Rejection` (R6.2). The shipped `pointer-traversal/1` records have extraction schema 1: `Quote` and codebook-free `Claim` records, with mask IDs and document-scoped quote links, read through `earnings_themes.extraction.store.read_run`; `write_run` re-verifies quotes with core's `reverify_span` before storage (Stage 7 spec, §Records, §Storage, §Handoffs to later stages).
      Exit: offline fake-model runs over Stage 3 fixtures retain only R6.1-valid quotes, and every rejection records a reason after bounded retries (R5.1/R6.2); a coverage test shows every eligible element visited and no top-k discovery path (R10.1/R10.2); a test shows changing any R14.6 key component misses the cache (R14.6); the default suite makes no network or billable call (R14.1); the V11 fixture triggers no tool call and cannot bypass R6.1 (R14.7/V11).
      ROUTING: brainstorming

- [x] Stage 8: Semantic support assessment
      Objective: Assess explicit claim–theme targets against re-verified evidence, retaining raw signals and review outcomes.
      Spec: `specs/completed/semantic-support-assessment.md` SS1–SS22; R8.1–R8.6, V4; R6.1.
      Gap closed: R8.1, R8.3, R8.5, V4; R8.2 scorer implementation (primary verified; alternative wired); R8.4/R8.6 machinery. Calibration and observed quality remain Stage 11.
      Consumes: Stage 7 `StoredRun` and matching canonical `Bundle` objects, supplied approved `Codebook` and explicit document-scoped `Target` references. `resolve_target(..., provenance_hash=...)` validates all original claim–quote links and frozen theme hashes without opening examples. Exact spans re-verify before scoring/publication/consumption. Tests use 29 curated fixture negatives with original partial spans (4 issuer, 13 period, 12 section), plus invented negation/positive/distributed/injection cases; no pilot extraction or signed-gold read. GS13 binds through Stage 14’s final test-gold drafting.
      Produces: `assess_target(..., cache=..., extractor_family=...)` and sequential `assess_run`; per-quote/joint raw scores, two families × two independent presentations, bounded attempts and explicit usage/ceilings; `refused`/`incomplete`/`flagged`/`assessed` outcomes; `write_support_run`/`read_support_run` and `reverify_support_run`; pure explicit-label `auc_roc` and externally accepted-claim precision. Support schema 1 and `semantic-support/1`. No accepted assignment or numeric policy.
      Exit: `docs/verification/semantic-support.md` records the actual pinned MiniCheck primary smoke (1 passed, 12.84s) with matched eight-file hashes, confirmed weight/base terms, CPU float32/512 input limit, process-wide network denial, offline flags and manifest binding; user full root 2651 passed and both wording gates passed; final whole-branch review/fix loops cleared. Scripted fixtures establish routing/exactness, never model quality. The optional alternative smoke is unrun.
      ROUTING: completed via subagent-driven-development, plan 13 (`specs/plans/completed/13-semantic-support-assessment.md`).

- [x] Stage 9: Deductive coding
      Objective: Assign verified, supported spans to themes of a frozen approved codebook as versioned multi-label rows, routing non-matches to a novelty queue.
      Spec: R9.1 (deductive), R9.3, R9.4, R9.6, R9.8, R9.9, R14.7, V11.
      Gap closed: R9.1 (deductive), R9.3 (queue), R9.4, R9.6, R9.8, R9.9; R14.7/V11 (codebook case).
      Consumes: Stage 6's codebook contract (`Codebook`, `Theme`, `Example`, `load_codebook`, and `validate_codebook` in `earnings_themes/codebook.py`) and v0, `codebooks/djia-pilot/codebook-v0.toml`, approved in ADR 0003: 22 themes in two levels, never changed after approval, a claim no theme fits being `unmatched` (R9.3); `codebook_hash` excludes `status`, `approval`, and `content_hash`, so a later version's record cites its hash before approval (P9-13; plan 9 §Handoffs). Raised by the user while v0 was drafted (plan 9, 2026-10-03): no stage records R9.4's direction, nor time orientation, scope, metric, or decision versus condition, and the gold has no field for them, so each is a claim or assignment attribute and a contract change; and exclusion rules name other themes in free text that nothing validates, so structured routing is a contract change too. Stage 7's codebook-free claims linked to one or more verified quotes, whose IDs are scoped by document, and `earnings_themes.synthetic.injection_bundle().bundle` for V11's codebook case (Stage 7 spec, §Records, §Handoffs to later stages; plan 12's F4, `docs/verification/evidence-selection.md`); Stage 8 `Target`, `resolve_target` and `assess_target` with explicit extractor family, frozen references, raw per-quote/joint views, quote contributions and review outcomes. Stage 9 proposes a target first, assesses it, then decides assignments under the calibrated policy supplied by Stage 11; `assessed` alone never means accepted, and contextual/irrelevant contributions are not promoted into theme evidence. GS13 binds this stage until the last gold bundle is drafted, Stage 14's test bundles included: no drafting session sees its code, prompts, or outputs (`specs/completed/pilot-codebook-split-and-gold-set-protocol.md`, GS13).
      Produces: an open-weight classifier emitting typed multi-label output with bounded retries against a frozen codebook version; assignment rows carrying codebook identifier and version; a novelty queue for human adjudication.
      Exit: fake-model replay exercises typed multi-label output with bounded retries against frozen v0 (R9.1/R9.8); one quote supporting two themes yields two rows sharing its quote identifier (R9.9); an unmatched candidate enters the novelty queue and no new theme identifier appears (R9.3); rows carry codebook identifier and version, and a mixed-version comparison is refused (R9.6); cluster labels and sentiment never populate theme fields (R9.4); the V11 fixture leaves the codebook unchanged (R14.7/V11).
      Shipped: plan 14 (`specs/plans/completed/14-evidence-linked-theme-extraction.md`), coding schema 1 / `deductive-coding/1`; complete frozen-theme proposals, bounded two-attempt classification and replay, explicit external-policy decisions, default calibration-required review, fixture-scoped acceptance, document-qualified quote–theme assignments and all supporting claim links, pointer-only valid-unmatched novelty, eight typed Parquet tables and current-evidence/policy consuming gates. Nullable topic/sentiment/direction/event-type annotations remain separate and unevaluated. Controller scoped gate 1110 passed; user full root 3532 passed and both protected wording nodes passed; final whole-branch review approved with no implementation findings. No pilot coding, calibration, production model/policy, command, state write or concurrent runtime workers.
      ROUTING: writing-plans

- [x] Stage 10: Coverage-aware aggregation and cited export (theme vertical slice)
      Objective: Produce analytical rows, coverage-aware prevalence, and a source-linked report that carry one release end to end.
      Spec: R2.3, R3.4 (headline exclusion), R6.1 (before export), R7.1, R7.2, R11.1–R11.6, V5, V8, V10; `specs/browser-rendering-integration.md` (B1, B5, B6, and its Stage 10 sections).
      Gap closed: R2.3, R3.4, R7.1, R7.2, R11.1, R11.2, R11.3, R11.4, R11.5; R11.6 (release roles); V5, V8, V10.
      Consumes: Stage 3 canonical documents and masks; Stage 5's processing-state table, read through `read_runs` and `current_states` with every document's `missing_reason`, and the event manifest's issuer-period rows, which name every expected event; the synthetic acquisition, `tests/fixtures/events/acquisition.json` (24 `parsed`, 2 `unavailable`, and 1 `failed` over the synthetic pilot), which gives V10 mixed denominators offline, `restricted` coming from fixtures only (plan 8 §Handoffs); Stages 7–9 verified evidence and Stage 9 assignment decisions; Stage 9 `read_coding_run`/`reverify_coding_run` with current source, support and explicit policy bindings before aggregation/export; Stage 8 `read_support_run` and `reverify_support_run` with matching `SupportSources`, current masks and source/codebook bindings before export. Raw cache reference/hash bindings do not establish verification of external cache bytes without the cache. Preserve refused/flagged/incomplete/assessed outcomes and coverage; zero accepted targets never implies no themes; Stage 7's `StoredRun` from `read_run`, carrying document outcomes (`completed`, `partial`, `failed`), offsets, hashes, run/model/prompt provenance, and mask IDs (Stage 7 spec, §Handoffs to later stages). Before reading a stored run, the extraction-record invariant hardening lands (`specs/deferred_items.md`, `12-evidence-selection-and-verification-plan-b`). This stage inherits reason-and-ID-only refusal rendering from plan 12, never printing source text or rejection detail (`specs/deferred_items.md`, `11-evidence-selection-and-verification-plan-a`). An error other than `AdapterError` currently ends extraction without a `RunRecord`; if the command needs a partial record after it, the plan 12 deferred design item is revisited; Stage 2's `VerifiedSpan` offsets and `make_locator` context for every highlight, `MaskedDocument.masks_overlapping` for the headline exclusion, and `RightsStatus` with `rights_basis` for retaining or exporting rendered artifacts, with offsets converted to UTF-16 only at the browser boundary, a stored `VerifiedSpan` re-verified through `reverify_span` before export, and no quote verified from rendered output (plan 3 §Handoffs; B6); Stage 3's masks under `boilerplate/1`, with the misses the review gate recorded (`docs/verification/layout-1.md`, "The review gate's findings"); Stage 3's public `BrowserRenderer` for V5's target-browser checks and the screenshot fallback, whose `capture(saved_html, capture_policy, *, source_document_id)` renders saved HTML rather than resolving a link, with `SeleniumRenderer` behind the `browser-capture` extra driving one pinned browser, Chrome for Testing 154.0.8037.57 on mac-arm64, under capture policy `isolated/1`; anywhere else a capture is `unavailable`, and screenshots are stored by content hash as `local_only` (plans 4 and 5 §Handoffs). Plan 5's deferred items record the capture adapter's known defects and `walker-1`'s words joined across `<br>` in table cells (`specs/deferred_items.md`, `5-structure-aware-canonicalization`). Raised by the user while Stage 6's v0 was drafted (plan 9, 2026-10-03): a sub-theme is coded instead of its parent, so a parent's prevalence needs a roll-up rule saying whether a firm-quarter has the parent when it has an assignment to the parent or any descendant (R11.2 counts distinct firm-quarters); and overlapping theme families suit versioned analysis-time views from `theme_id` to family, with no codebook change.
      Produces: Polars/Parquet rows at the R11.1 grain; prevalence tables printing numerator, denominator, unit, and restrictions; passage links paired with immutable snapshots; a cited report; the V8 offline end-to-end test. It adds the first extraction command and maps each document outcome into a new Stage 5 state-table run under R1.4 (Stage 7 spec, §Handoffs to later stages); zero retained quotes alone never becomes `completed-no-theme` (R6.2).
      Exit: V8 passes with no network or credentials, from raw fixture to cited report (V8/R11.1); V10 reproduces hand-computed numerators and denominators across unavailable, restricted, failed, and no-theme documents, and reports missing-transcript coverage (V10/R11.2/R11.3/R2.3); a test shows masked spans absent from headline prevalence yet present in audit output (R3.4); tests show a disclosure's copies counted once and issuers weighted equally (R11.5/R11.4); release rows carry `not_applicable` speaker roles (R11.6); V5 records each target browser's highlight behavior, and the snapshot renders the span wherever the link fails (V5/R7.1/R7.2).
      ROUTING: writing-plans

- [ ] Stage 11: Feasibility pilot and threshold calibration
      Objective: Run the pipeline against the hand-coded pilot, calibrate the judge, and gate the metrics the pilot can estimate.
      Spec: R8.2, R8.4, R8.6, R12.2, R12.4, R12.5, R12.7, R12.8, R12.10, R13.1, R13.3, V6; D1, D2, D4.
      Gap closed: R8.2, R8.4, R8.6, R12.2, R12.7, R12.8, R12.10; R13.1/V6 (per D1); R12.4 (no-theme count) and R12.5 (hard-negative scoring), per D4.
      Consumes: the frozen Stage 5 pilot manifest, split by Stage 6, its train and dev partitions annotated by the user, while test gold waits for Stage 14's frozen configuration; the Stage 6 D4 coverage report; at least 50 expert support labels on Stage 8 outputs (D2), with an explicit label task and signal view for its pure `auc_roc`/`accepted_claim_precision` joins. Stage 8 supplies primary/alternative raw score interfaces, four separate family/presentation views and full provenance/usage, with no pooling, numeric tolerance, cutoff or acceptance. Stage 9 supplies the pure `AssignmentPolicy`/`PolicyReference` seam bound to classifier/support configuration and codebook; absent policy remains review, fixture acceptance remains fixture-scoped, and annotations have no gold or quality claim. Stage 11 selects view/pooling, production panel/policy, preregistered agreement floor and numeric quality gates; four panel trials are bias diagnostics, never fresh-call stability; the Stage 10 pipeline. From Stage 6 (plan 9 §Handoffs): `load_pinned(layout)`, `load_split(path)`, and `load_coverage(path)`; coverage v1's `no_theme` is empty, and this stage writes coverage v2 with `NoThemeCount` rows for train and dev from each signed file's `no_theme` (P9-4), through `build_coverage(..., version=2)` extended to take them; the signed gold of all 28 train and dev events, one file per event under `evaluation/djia-2024q3-2026q2/pilot-v1/gold/`, named with the event's colon as an underscore (P9-3), of which three are signed and the other 25 are deferred items (`specs/deferred_items.md`, `9-pilot-codebook-split-and-gold-set-protocol`), each anchored under the gold that plan 10 hardened (`specs/plans/completed/10-harden-the-gold-before-bundle-4.md`); the kept drafts under `data/runs/gold/drafts/`, for GS5's edited, rejected, and added shares, each zero so far, which this stage counts only once the deferred refusal of a kept draft that repeats an ID lands (`specs/deferred_items.md`, `10-harden-the-gold-before-bundle-4`); each file's `release_identification.label`, for R13.1's precision; who writes R8.4's labels, which this stage decides; and the limitations of one annotator and one drafting model family. R13.1 names micro and macro F1 but no hierarchy rule, so whether a predicted parent earns credit against a gold child, or a sibling, is decided before V6 sets gates (raised by the user, plan 9). Stage 7's `extract_run`/`read_run` records and explicit request/token ceilings; its whole-unit quotes differ from gold's partial-unit or multi-unit passages, which this stage compares with the span-overlap metric (Stage 7 spec, §The difference from P9-19). Stage 7's extractor has no fresh-call mode: both `CacheMode.LIVE` and `REPLAY` serve hits, so R12.10 needs a bypass, not merely `LIVE`. This is the first extraction over pilot documents, and only here may train gold inform prompts (Stage 7 spec, §Handoffs to later stages). If a live test is extended to pilot text, the plan 12 failure-output guard lands first; if it needs a partial record after a non-`AdapterError`, the plan 12 deferred design item is revisited (`specs/deferred_items.md`, `12-evidence-selection-and-verification-plan-b`).
      Produces: implementations of every R13.1 metric plus retention, stability, and AUC-ROC; a pilot report with issuer- or event-level uncertainty; a judge-calibration report with its pre-registered floor; the V6 decision record of gates. Fresh-call cache bypass across all four extraction, classifier, scorer and judge response caches for k-run stability (Stage 7 and Stage 8 specs, §Handoffs); current live modes, including classifier mode, serve hits.
      Exit: the pilot report gives every R13.1 metric's observed distribution with event-level intervals, labeled feasibility-only (R12.2/R12.7); the V6 record gates only pilot-estimable metrics, marks rare-theme recall, sector prevalence, and source-selection bias descriptive-only, and is committed before any configuration comparison (V6/R13.1, D1); judge agreement with the user's labels is reported against its pre-registered floor, with AUC-ROC for both scorers (R8.4/R8.6/R8.2); a reject-everything configuration fails the suite (R12.8); k-run stability is computed with extraction, classifier, scorer and judge response-cache hits bypassed (R12.10); the D4 coverage report gains the observed no-theme count over the annotated train and dev partitions (R12.4, D4); pilot metrics include the annotated hard-negative claims (R12.5, D4).
      ROUTING: brainstorming

      Stage 10 handoff (plan 15, 2026-10-08): First pilot extraction; `load_workflow_config(Path, *, repo) -> WorkflowConfig` and `run_theme_workflow(config, runtime, *, now) -> WorkflowResult` provide explicit replay/current-gate composition. Schema-2 processing preserves schema-1 acquisition, expected coverage and fixture scope. Own production adapters/panel/policy, at least 50 expert labels, calibration/views/pooling/agreement floors/V6 and bypass of all four extraction/classifier/scorer/judge caches. Terminal/partial reprocessing requires an explicit policy; assessed and fixture V8 make no acceptance-quality claim.

- [ ] Stage 12: Inductive and hybrid codebook
      Objective: Discover candidate themes offline from training-partition evidence, approve them as a new codebook version, and re-code the declared corpus.
      Spec: R9.1 (inductive, hybrid), R9.3 (approval), R9.5, R10.3, R12.3.
      Gap closed: R9.1, R9.3, R9.5, R10.3; `embeddings` extra row.
      Consumes: Stage 9 coding and novelty queue; Stage 11 splits and metrics; Stage 6's training partition only, `split.events_in(Partition.TRAIN)` and its bundles (R12.3; plan 9 §Handoffs). Raised by the user while v0 was drafted (plan 9, 2026-10-03): deeper theme levels, such as `macro` above `demand` and `supply`. The freeze accepts any depth, but every theme needs a positive example and a hard negative, so a grouping-only node is a contract change; that example crosses two axes, driver and scope, and a scope attribute per assignment is the alternative to a tree; a level added above existing themes remaps mechanically, but a split by scope changes meaning and needs the gold re-judged. Stage 9's fields beyond theme and structured exclusion routing bear on this stage too. Before it freezes codebook v1, two deferred quick-fixes land: `codebook freeze` takes the drafting aid from the kept draft (P10-7, `10-harden-the-gold-before-bundle-4`), and holds `--adr` to a repo-relative path under `docs/adr/` (T11-M1, `9-pilot-codebook-split-and-gold-set-protocol`; both `specs/deferred_items.md`).
      Produces: an offline clustering aid outside the application pipeline; consolidation preserving evidence pointers and contradictory claims; an approval path from candidate codebook to a new frozen version; a hybrid mode; re-coding under the new version.
      Exit: a test shows candidate themes derive from training-partition data only (R12.3); a test shows consolidation keeps every evidence pointer and contradictory claim (R10.3); approval is recorded in a decision record and re-coded rows carry the new version (R9.1/R9.3); an import check shows no clustering dependency reachable from the application pipeline (R9.5, `embeddings` row).
      ROUTING: brainstorming

      Stage 10 handoff (plan 15, 2026-10-08): Versioned analytical family mappings and self-or-descendant parent counts are views over unchanged v0. New taxonomy/hierarchy or inductive/hybrid book requires training-only discovery, approval, new version and re-coding; mappings do not create themes.

- [ ] Stage 13: Transcript extension (conditional on V7)
      Objective: Add lawfully usable transcripts with speaker roles, or record that no candidate corpus qualifies.
      Spec: R2.1, R2.2, R4.1 (speaker turns), R11.6, V7; D2.
      Gap closed: R2.1, R2.2, V7; R11.6 (management/analyst split).
      Consumes: Stages 3 and 5, whose state table holds one document per event, `<event_id>:release`, which `StateTransition` enforces since plan 8's final review, so a transcript document is a schema change there; Stage 10 aggregation; Stage 11 metrics; Stage 8’s release-only attribution context requires an explicit speaker/section adaptation, retaining separately labeled context and evidence and never inferring a spoken management role for releases; Stage 2's `speaker_turn` element type and `crosses_speaker_turn` check, and Stage 3's schema version 2 with its `text_origin`, still with no speaker role, name, or attribution status — adding them is a schema bump (plan 3 §Handoffs, D-16; plan 4 §Handoffs). Stage 7's unit and window planner, whose `block_of` accepts any non-sentence narrative ancestor and assumes each block's units are contiguous; the plan 12 deferred block-rule check is revisited when transcripts add speaker turns or sections (`specs/deferred_items.md`, `12-evidence-selection-and-verification-plan-b`).
      Produces: a V7 record per candidate corpus; if one qualifies, a rights-gated transcript adapter storing locators and local features where terms forbid redistribution, and speaker turns with role and attribution status.
      Exit: V7 records each candidate's license, redistribution terms, and diarization accuracy against a user-labeled sample (V7); if none supports the management/analyst split, R2.2 is recorded as failed and the stage parks; otherwise fixture transcripts yield role-attributed turns, unresolved roles stay `other`/`unknown`, and restricted text is never redistributed (R2.1/R2.2/R11.6).
      ROUTING: brainstorming

      Stage 10 handoff (plan 15, 2026-10-08): Release roles remain not_applicable and absent transcripts explicitly not in scope. Conditional V7 owns lawful transcripts, transcript identity/speaker attribution/context and producer-consumer changes to Stage 5 release-only IDs and speaker schemas. Missing transcript coverage is no negative signal.

- [ ] Stage 14: Configuration comparison and held-out evaluation
      Objective: Run R12.9's ablations against the V6 gates, freeze one selected configuration, and evaluate it once on the held-out split.
      Spec: R5.2, R10.1 (whole-document arm), R10.2 (retrieval-only arm), R11.5 (dedup arm), R12.9, R13.3; D1.
      Gap closed: R5.2, R12.9, R13.3.
      Consumes: Stage 11 gates, metrics, and splits; the test partition's gold, drafted and verified only after the selected configuration is frozen (Stage 6's spec, GS18), by plan 9's Task 19, the commit that freezes it relaxing `readable()`'s refusal of test text and never earlier, with the deferred refusal of test gold at validation closing there at the latest (`specs/deferred_items.md`, `9-pilot-codebook-split-and-gold-set-protocol`); the dev gold, for the comparisons (plan 9 §Handoffs); Stage 12 inductive and hybrid codebooks; Stage 13 transcripts if shipped, else that arm is recorded as not run. Stage 7's `plan_windows(bundle, budget=None)` for the whole-document arm, and `ModelAdapter` (`identity` property, `complete(request) -> reply`) for an optional PydanticAI-backed generate-then-verify comparator; changing reply contracts still goes through core verification (Stage 7 spec, §Seams, §Handoffs to later stages).
      Produces: a generate-then-verify comparator; whole-document and retrieval-only modes; an ablation report with quality, latency, tokens, and cost per arm; a selection decision record; one held-out evaluation report.
      Exit: a test shows generate-then-verify rejects every unresolvable candidate and never repairs wording (R5.2); the ablation report covers every available R12.9 arm and adjudicates against V6's gates (R12.9); the selected configuration is frozen by hash and evaluated on the held-out split once, a second run under the same protocol is refused, and the report is labeled feasibility-level (R13.3, D1).
      ROUTING: writing-plans

      Stage 10 handoff (plan 15, 2026-10-08): Stable analytical/coverage/export artifacts and explicit copy/mask/book/policy/family controls support required ablations. GS18 configuration freeze precedes test text/gold; GS13 remains unchanged through final test-gold drafting. Stage 10 ran no held-out extraction or fresh-call stability.

- [ ] Stage 15: Full DJIA eight-quarter run
      Objective: Run the configuration frozen by Stage 14 over every eligible event in the complete DJIA manifest, reporting the observed corpus shape rather than forcing it to a target.
      Spec: P-C6, P-A15; P §Stage 15 — Full DJIA eight-quarter run; R1.3, R1.4 (access policy, processing states); R11.1–R11.3 (grain, denominators, coverage), R12.10 (replay bypass), R14.6 (cache keys), R14.1 (no billable call on the required path).
      Gap closed: P-C6, P-A15.
      Consumes: the frozen Stage 5 event manifest, which is its expected-event ledger: events v1 holds 263 events, 239 eligible, keyed to the universe by `operative_hash`; the frozen Stage 4 cohort manifest, whose intervals and candidate issuers define the run's universe (plan 6 §Handoffs); Stage 4's shared SEC client (D5), whose lock has been held once per machine since Stage 5's plan A (`fetch.client.machine_lock_dir()`, or `$EARNINGS_LOCK_DIR`; plan 7); the Stage 5 EDGAR adapter and processing-state table (plan 8 §Handoffs): `acquire` takes a pilot manifest today, so this stage passes a manifest of every eligible event or generalizes the document list, reusing `exhibit_order`, `release-content/1`'s `confirm`, the states, `set_release_document` overrides with their `corpus_error` guard, and `planned_requests` for its gate's count, the approved count being the client's cap, against which each retry counts; states are scoped by the manifest's content hash, so a new document list starts at `expected`, while saved exhibits and canonical files are reused with no request; the build decides which event manifest is current, and a universe is never reverted (F4, P8-4); a saved response that cannot be read is repaired by hand (`docs/verification/djia-events.md`, "Repairing the store") until the deferred recovery lands (P2.1, P2.2; `specs/deferred_items.md`, `PR #6 review (plan 7)`), which a run of this size makes worth landing first; the Stage 3 canonicalizer, `walker-1`, which needs no browser capture (ADR 0002; plan 5 §Handoffs); the Stage 14 selected configuration, frozen by hash; Stage 11 metrics and the Stage 10 export path; cached pilot artifacts whose R14.6 cache key still matches. It reselects nothing. Stage 7's `extract_window` and cached raw replies, re-verified on each reuse, behind `ModelAdapter`; optional LangGraph may wrap this seam for backfill (Stage 7 spec, §Handoffs to later stages). Stage 8’s sequential scorer/judge raw caches, support store/consuming gate and versioned manifests are additional seams; concurrent support writers/allowance coordination and extraction `AdapterError` pickling/cache/store safety must be fixed or ruled out before workers. Its extraction outcomes (`completed`, `partial`, `failed`) stay distinct from Stage 10's downstream no-theme state; stored quotes reused through `read_run` pass `reverify_span` at the consuming gate. A non-`AdapterError` currently ends extraction without a `RunRecord`, so only accepted replies remain cached; if workers are introduced, the plan 12 concurrency items for `AdapterError`, cache writes and store publication must be fixed or ruled out (`specs/deferred_items.md`, `12-evidence-selection-and-verification-plan-b`).
      Produces: acquisition and canonicalization of every eligible release not already acquired for the pilot, under the shared 2 req/s limiter, each outcome recorded in the processing-state table; analytical outputs over every eligible event at the R11.1 grain, each row carrying universe, corpus, codebook, schema, and run versions; a coverage report giving expected, eligible, acquired, parsed, processed, failed, partial, and completed-no-theme counts by issuer and period; a reconciliation of the observed event count against the approximate `30 × 8` shape that attributes every departure to a membership transition or a missing event.
      Exit: every expected-event ledger row carries an eligibility and coverage status, and every eligible event a terminal or resumable processing status (P-A15); ineligible and ambiguous rows appear in coverage and status output without being processed as eligible, alongside the failed, unavailable, partial, and completed-no-theme cases; a test shows compatible pilot artifacts reused without producing duplicate accepted rows; a test shows the run performing no reselection, and the reported count is the observed count, never forced to equal `30 × 8` (P-C6); the coverage report names the transitions and missing events behind any departure from that shape; the default suite makes no network or billable call, live acquisition runs only at a request count approved at a gate (`--max-requests`), and live tests only behind the `live` marker (R1.3, R14.1).
      ROUTING: writing-plans — `specs/point-in-time-djia-cohort.md` is this stage's spec; it needs no brainstorming pass.

      Stage 10 handoff (plan 15, 2026-10-08): Immutable append/read schemas, expected-event selection and current gates feed the full cohort. Own recovery/reprocessing, concurrent worker/cache/store/pickle/allowance safety and coordinated SEC/source traffic. Sequential .acquire.lock append reuse supplies no concurrency/backfill proof.

- [ ] Stage 16: Hosted quality ceiling (optional)
      Objective: Measure a hosted frontier model's quality ceiling on a frozen subset within the $100 authorization.
      Spec: R14.2; D3.
      Gap closed: R14.2.
      Consumes: Stage 14 frozen configuration; Stage 11 metrics; Stage 6's drafting conflict: Claude Opus 5.5 drafted every gold item and the user accepted each unchanged, so a Claude ceiling records that conflict (GS4; `docs/verification/pilot-v1-gold-set.md`, Limitations; plan 9 §Handoffs). Stage 7's `ModelAdapter` protocol for the hosted adapter, outside the required path (Stage 7 spec, §Handoffs to later stages); its current `RunRecord.billable_cost` is fixed to `"none, self-hosted"`, so that contract needs a versioned change before it records hosted dispatch.
      Produces: a hosted adapter behind per-document and per-run ceilings enforced before dispatch; a ceiling report.
      Exit: an offline budget-exhaustion test yields a visible partial or failed status, never silent truncation; recorded spend stays within $100 with a pricing basis; no required-path module imports the hosted adapter; the report is labeled an ablation ceiling (R14.2).
      ROUTING: writing-plans

      Stage 10 handoff (plan 15, 2026-10-08): Pure policy/evidence/export seam remains available. Optional hosted calls, budget and privacy review are separate and unimplemented.

## Stage-spec stamp

Every stage spec's Rollout note carries this line, which writing-plans copies
verbatim into the stage plan's header:

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage N — on plan
> completion, tick the stage and re-validate later stages against what shipped.

On completion the stamp becomes authoritative:

> Stage N: COMPLETE (YYYY-MM-DD) — implemented by plan <id> (path).
> Next: resume the roadmap.

A stage routed straight to writing-plans (Stages 2, 9, 10, 14, 16) has no stage
spec of its own: its plan header carries the Roadmap line directly, and its
COMPLETE line is appended to the Rollout section of
`specs/evidence-linked-theme-extraction.md`, which is the stamp a resume reads
for those stages. Stages 4 and 15 are also routed to writing-plans but do have a
stage spec — `specs/point-in-time-djia-cohort.md` — so their COMPLETE lines
follow the normal stamp convention against that file.

## Completion

Retire this roadmap only after a conformance audit of the accumulated system:
re-run the gap rubric over every row above — including the 13 `P-*` rows from
`specs/point-in-time-djia-cohort.md` — with evidence per verdict (implementing
stage and plan, `> Deviation:` notes, deferred entries). Each
requirement still unmet exits one of two ways: a new stage (the roadmap stays
live), or conscious deferral with a written why. Deferrals already decided on
2026-09-22:

- **R5.3, V3** (D3) — V3 needs a billable call outside R14.2's authorization and
  at odds with R14.1; revisit only under a separate authorization.
- **R13.1 gates for rare-theme recall, sector prevalence, and source-selection
  bias** (D1) — R12.2 says the pilot cannot estimate them; they await a larger
  event-level validation set that this roadmap does not build.
- **R12.6 agreement** (D2) — single annotator; agreement is not measurable and is
  recorded as a limitation, not met.
- **Stage 13** parks if V7 finds no qualifying corpus; **Stage 16** is optional.

Not staged because no requirement asks for them: the learning path's LangGraph,
DSPy, and CrewAI exercises (R14.4). Out of scope per the spec: importance
ranking, taxonomy content, company enrichment, and prompt-optimizer compilation.
