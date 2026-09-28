# Pilot codebook, split, and gold-set protocol

> For agentic workers: REQUIRED NEXT SKILL: writing-plans. This is the stage spec
> for Stage 6 of `specs/evidence-linked-theme-extraction-roadmap.md`. Plan it as one
> plan whose last tasks are the gates (§Gates). Never plan a later stage with it.

Stage 6 takes the frozen pilot as given. It splits the pilot's events by issuer and
time, freezes an observed coverage report, and builds the codebook and
gold-annotation contracts. It then runs the human protocol that produces codebook v0
and the first signed gold. It selects nothing, fetches nothing, and calls no model
from code.

It closes R9.2, R9.7, R12.1, R12.3, R12.4 (as observed coverage, D4) and R12.5 (D4)
of `specs/evidence-linked-theme-extraction.md`, and records R12.6's limitation (D2).
It keeps P-C5 and P-C7 of `specs/point-in-time-djia-cohort.md`: no step here can
change a pilot row.

Locators:
- **`A §n`** is `AGENTS.md`, by line.
- **`Rn`** are the theme spec's requirements.
- **`P-Cn`** and **`P §Section`** cite the cohort spec, as the roadmap does.
- **D1, D2, D4** are the roadmap's decisions (its Gap analysis).
- **`EVn`** are the Stage 5 spec's decisions
  (`specs/completed/event-discovery-eligibility-and-acquisition.md`), and **`P8-n`**
  are plan 8's (`specs/plans/completed/8-event-discovery-eligibility-and-acquisition-plan-b.md`).
- **F9** is the Stage 1 spec's gold-drafting decision (`specs/release-parser-fidelity.md`).
- **F20** and **F27** are PR #6's review items (`specs/deferred_items.md`,
  `PR #6 review (plan 7)`). F20's check is `tests/integration/test_corpus_quotes.py`.
- **Pilot v1** is `config/corpus/djia-2024q3-2026q2/pilot-v1.json`, and **events v1**
  is `events-v1.json` beside it.
- **`GSn`** are this spec's decisions.

Designed 2026-09-28 in a brainstorming session, from
`stage-6-pilot-codebook-split-and-gold-set` at `21028a9`.

## Decisions

Taken with the user on 2026-09-28. Rows marked *(design)* were proposed in the design
and approved with it.

| ID | Decision |
| --- | --- |
| GS1 | One spec, one plan. The code comes first, and the plan's last tasks are the gates: the split and coverage freeze, codebook v0's approval, and three signed gold bundles (§Gates). No step sends an SEC request or calls a model from code. |
| GS2 | **The pin.** Stage 6 binds to pilot v1 by content hash, `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926`, over events v1, `2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7`. It loads the pilot with `load_pilot`, never `current_pilot`. The split, codebook v0's discovery corpus, and every gold file name the pin, and Stages 11 and 14 evaluate that pilot. A later events or pilot version is a new sample, for Stage 15 or a future validation set, and never replaces it. The rule is fixed here, before any annotation, so it stays outcome-blind (P-C7). F27 is therefore not a precondition for annotation. It, `release-id/2`, and the per-candidate citations stay deferred to the next events version, which re-seeds the pilot under the Stage 5 spec's invalidation rule (§Pilot selection) whenever it comes; settling F27 first would only move that re-seed earlier. |
| GS3 | **The public repository.** Committed files hold IDs, offsets, labels, and hashes, never release text. A quote is committed as its `doc_id`, `[start, end)`, `element_id`, and the SHA-256 of its text and of its locator context. Claims, definitions, rules, and notes are the user's own words, and every committed free-text field passes F20's check (§Wording guard). A codebook example is a pointer, or is labeled synthetic (A §611). Quote text lives only in local drafts and views under `data/`. |
| GS4 | **Gold authorship.** This amends D2 for Stage 6's gold, as F9 did for Stage 1's. A Claude session drafts each bundle's gold under a committed brief. The user verifies every item, reads the whole bundle for omissions, and signs. F9's mechanics carry over: the drafter leaves `annotator` blank, so a draft fails validation until the user signs; the signature reads "Lowell Mason (verified a Claude draft)"; and each original draft is kept, uncommitted. Drafting is outside the required path. It runs in an interactive session, and no model SDK, API key, or call enters the code (R14.1). The limitation, gold anchored to one model family's reading, is recorded. |
| GS5 | **Origins and the omission pass.** Each gold item records its origin: `drafted_accepted`, `drafted_edited`, or `annotator_added`. It is derived by comparing the signed file with its kept draft, and each file counts the drafted items the user rejected. A bundle counts as annotated only after the omission pass. Stage 11 reports the edited, rejected, and added shares. |
| GS6 | **The split**, rule `issuer-time/1` (§The split). Three partitions by period-end quarter, four, two, and two: train 2024Q3–2025Q2, dev 2025Q3–2025Q4, test 2026Q1–2026Q2. An issuer's events belong to the partition of its earliest event, and a later event in another window is excluded. On pilot v1 that gives 20 train, 8 dev, 7 test, and 5 excluded. |
| GS7 | The five excluded events stay unannotated, since no stage consumes gold outside a partition. They stay in every report, with their reason. |
| GS8 | **The D4 report** (§The coverage report). It states pilot v1's zero unavailable, restricted, and failed documents as coverage gaps, never repaired by reselecting, and names Disney's override. Stage 6 adds nothing more for those classes. Abstaining on a missing document is a denominator property, which Stage 10's V10 tests with the synthetic acquisition. Stage 11 adds the no-theme count. |
| GS9 | **Codebook v0.** A Claude session reads only the training bundles and proposes themes with their fields. The user edits, cuts, and approves them in ADR 0003, and v0 freezes by content hash. It is the pilot codebook, not the final taxonomy, which stays unresolved (`CLAUDE.md`). After approval v0 never changes: a claim no theme fits is recorded as unmatched, never as a new theme (R9.3). |
| GS10 | **Curated hard negatives** (R12.5, D4) point into Stage 1's committed canonical fixtures, with claims in the user's words, drafted and verified under GS4. Stage 1's fixture events are `train_or_exclude`, never held out. |
| GS11 | **The workflow** is files, commands, and a rendered view (§Drafting and tools). An anchor step turns each drafted quote into an exact span through Stage 2's checks, or refuses it. No offset comes from a browser. |
| GS12 | The user keeps a backup of `data/` outside the repository before drafting starts. It holds the only copy of pilot v1's saved exhibits and canonical documents. |
| GS13 | *(design)* **Blinding**, after F9. A drafting session starts fresh. It sees only its brief, the contracts and validator, the frozen codebook when it drafts gold, and the text it is given: the 20 training bundles for the codebook, or one bundle for gold. It never sees Stages 7–9's code, prompts, or outputs, or another bundle's gold. No session reads a dev or test bundle before v0 is approved. The session that implements this spec never prints or opens pilot document text. |
| GS14 | *(design)* **Homes.** `evaluation/djia-2024q3-2026q2/pilot-v1/` holds the split, the coverage report, the gold, and the briefs. `codebooks/djia-pilot/` holds codebook v0, and `tests/fixtures/gold/` the curated hard negatives. Drafts and views stay in `data/runs/gold/`, which is gitignored. The briefs stay out of `prompts/`, which is the pipeline's. |
| GS15 | *(design)* A gold quote sits only in an element Stage 7 treats as narrative, never in a `table`, `table_cell`, `page_artifact`, or `other` element (R4.2). A quote under a boilerplate mask is allowed, and its masks are recorded. |
| GS16 | *(design)* `sector_applicability` is `all` or a list of the codebook's own tags, mapped to no issuer. Industry classification stays out of the theme path (`CLAUDE.md`), and D1 leaves sector prevalence descriptive. |
| GS17 | *(design)* **Units.** `earnings-themes` holds the split rule, the codebook, and the gold, and imports only `earnings-core`. `earnings-ingestion` holds the coverage report, over the state table it owns. The application loads the records and passes them on. `earnings-core` is unchanged, and no dependency is added. |

## Scope

In:
- the pin (GS2);
- the split rule and its frozen manifest (R12.1, R12.3);
- the D4 coverage report (R12.4);
- the codebook contract and codebook v0, approved in ADR 0003 (R9.2, R9.7);
- the gold contract, with its anchor, validator, and view, and the release-identification label that R13.1's first metric needs;
- hard-negative claims in the gold, and curated hard negatives outside the pilot (R12.5, D4);
- the drafting briefs and the protocol (GS4, GS5, GS13);
- three signed gold bundles, as the roadmap's Exit asks.

Out:
- the rest of the annotation: the other 32 partitioned bundles continue alongside Stages 7–10, and Stage 11 needs all 35;
- R8.4's support labels, which Stage 11 collects; who writes them is decided there;
- any metric, threshold, or model (Stages 7–11);
- sector classification (GS16);
- settling F27, `release-id/2`, or the per-candidate citations (GS2);
- any edit to a frozen record under `config/`.

## Inputs

- **Pilot v1 and events v1.** `load_pilot(path, universe)`, against the current
  universe, rechecks the pilot's chain and reselects it (P8-3), whichever events
  version is current. Pilot v1 holds 40 events over 33 issuers and all eight
  quarters.
- **The processing states.** `read_runs(data/runs/events/states)` gives the
  transitions, and `current_states(transitions, pilot_hash)` each document's state,
  with runs in `in_order`'s order. All 40 of pilot v1's documents are `parsed`. One,
  Disney's for 2026-03-28, is parsed through the reviewed override
  `release-doc-dis-2026-03-28`, whose attempt keeps `release-content/1`'s
  `not_confirmed` verdict.
- **The canonical documents.** Each `parsed` document's state names its `doc_id`, and
  its `walker-1` document is `data/runs/events/canonical/<doc_id>.json`, holding
  `document`, `elements`, `manifest`, and `masks`. It is local. A missing one
  regenerates offline from the saved exhibit through `canonicalize` (plan 8
  §Handoffs). A later promotion that keeps `walker-1`'s text carries offsets to its
  new `doc_id` unchanged (plans 4 and 5 §Handoffs).
- **Stage 2's checks:** `parse_span_candidate`, `validate_span`, `make_locator`, and
  `Rejection`.
- **Stage 1's fixtures.** The eight canonical fixtures in `tests/fixtures/canonical/`
  are committed with their source-register basis, and
  `tests/fixtures/releases/manifest.toml` marks each event
  `pilot_split = "train_or_exclude"`. No fixture issuer is in pilot v1.
- **The synthetic corpus,** `tests/fixtures/events/`: a synthetic pilot, and the
  synthetic acquisition, whose failure classes are not empty.
- **F20's check,** `tests/integration/test_corpus_quotes.py`.

## The pin

Every Stage 6 record carries the pin: `pilot_id`, `pilot_version` 1, the pilot's
content hash, and events v1's version and content hash. Each command loads pilot v1
by its path, and refuses to run if the pilot's content hash is not the pin's. None
calls `current_pilot`. A later pilot version under
`config/corpus/djia-2024q3-2026q2/` changes nothing here.

## Order of work

1. Freeze the split and the coverage report. Neither reads a document.
2. The user confirms the backup (GS12).
3. Codebook v0. A fresh session, under the codebook brief, reads the 20 training
   bundles and writes a local draft. The user edits it. `codebook freeze` anchors its
   example quotes and freezes it, and ADR 0003 records the approval.
4. The curated hard negatives, over Stage 1's fixtures, under the gold brief. They
   come after v0, since they name its themes.
5. Gold, one bundle at a time: draft, anchor, verify, omission pass, sign, validate.

The steps run in that order. No session reads a pilot document before the split is
frozen, and none reads a dev or test bundle before step 3 ends (R12.3). Stage 6 is
complete once three bundles, from any partition, pass step 5. Annotation of the rest
continues after it.

## The split

Rule `issuer-time/1`:
- **Inputs.** Each pinned pilot row's `event_id`, with its event's `issuer_id` and
  `period_end` from events v1. Nothing else: no document, state, or outcome (P-C7).
- **Windows.** The calendar quarter of `period_end`. Train holds 2024Q3–2025Q2, dev
  2025Q3–2025Q4, and test 2026Q1–2026Q2.
- **Issuers.** An issuer's events go to the partition of its earliest event. A later
  event whose window is another partition is `excluded`, with the reason
  `issuer_in_earlier_partition`.
- **Fixture events.** A Stage 1 fixture's event is never dev or test
  (`train_or_exclude`): one whose window is dev or test is `excluded`, with the
  reason `fixture_train_or_exclude`. Pilot v1 has none.
- **Bundles.** A bundle is an event. Every document of the event, with its copies and
  revisions, takes the event's partition (R12.1, R12.3). Each pilot v1 event has one
  document, `<event_id>:release`.

The manifest, `split-v1.json`, records the rule, its windows, the pin, one row per
pilot event (`event_id`, `issuer_id`, `period_end`, `partition`, and `reason` when
excluded), and a content hash over the rest, as the corpus records do. It is written
once, atomically. A changed rule is a new version, never an edit.

On pilot v1 it gives 20 train, 8 dev, 7 test, and 5 excluded. The excluded five are
the later event of each issuer that the pilot holds twice across windows:
- `cik-0000320187:2026-05-31`, `cik-0001403161:2026-06-30`, and
  `cik-0000004962:2026-06-30`, each a `longitudinal_fill` row;
- `cik-0000731766:2026-06-30`, an `issuer_coverage` row, whose issuer's
  `longitudinal_fill` row, `2024-09-30`, stays in train;
- `cik-0000732712:2026-03-31`, a `membership_boundary` row (Verizon's last release
  before its exit), whose issuer's other event is in dev.

So the partitions keep two of the pilot's three membership-boundary events. A
different outcome stops the gate.

## The coverage report

`coverage-v1.json` covers the pinned pilot's 40 documents and their states under the
pin. It holds:
- the count in each state;
- for each of `unavailable`, `restricted`, and `failed`, its count, and, when the
  count is zero, a coverage-gap entry citing D4: a missing class is never repaired by
  reselecting;
- each override applied to a pilot document, by ID, with the verdict its attempt
  kept: `release-doc-dis-2026-03-28`, `not_confirmed`;
- the run IDs it read, so that it reproduces;
- `no_theme`, empty until Stage 11 adds it (R12.4);
- the pin, and a content hash.

On pilot v1 it gives 40 `parsed` and three gaps. The synthetic acquisition's report
counts each of its non-zero classes, which tests the counting.

## The codebook

A codebook file holds (A §608, R9.2):
- `codebook_id` (`djia-pilot`), `codebook_version` (0), `status` (`draft` or
  `approved`), and a content hash;
- the discovery corpus: the pin, the split's content hash, and the training
  partition's `event_id`s and `doc_id`s;
- the multi-label and boilerplate rules, in the user's words;
- the approval, empty while `draft`: approver, date, and ADR 0003's path;
- the drafting aid: the model's ID and the date;
- one entry per theme: a stable `theme_id`, `parent_id` (empty at the top), `label`,
  `definition`, `inclusion_rules`, `exclusion_rules`, `positive_examples`,
  `hard_negatives`, and `sector_applicability` (GS16).

An example is a pointer into a training bundle, in the form of a gold quote (§The
gold), or is synthetic, with its flag set and its text written by the user. No
example points outside the training partition. `codebook freeze` checks every field
and pointer, and writes `status = "approved"` only once ADR 0003 is named. A theme ID
is never reused.

ADR 0003 records the codebook file and its content hash, the discovery corpus, the
drafting aid, and the user's approval with its date. It also records that v0 is the
pilot codebook, not the final taxonomy.

## The gold

One file per annotated bundle, `gold/<event_id>.toml`.

**Header:**
- `event_id`, `document_id` (`<event_id>:release`), `doc_id`, and the canonical hash;
- the pin, the split's content hash and the event's partition, and the codebook's ID,
  version, and content hash;
- `annotator`: blank in a draft, and the user's signature once signed (GS4);
- the drafting aid's model ID and date, the counts of drafted items accepted, edited,
  and rejected, and the count of items added;
- `no_theme`: true exactly when no assignment names a codebook theme. The validator
  checks it against the assignments, so a bundle with no theme is affirmed by the
  user, never inferred from an empty file.

**The release-identification label:** `release`, `not_release`, or `ambiguous`, with
a note in the user's words. `release` means the document is this event's earnings
release, for its issuer and its period. With `not_release`, the true release's
accession and exhibit may be given, as facts.

**Quotes:** `quote_id`, `start`, `end`, `element_id`, `quote_sha256`, and, when the
text occurs more than once, `context_sha256`, over `make_locator`'s prefix and
suffix. Each quote also has its origin (GS5) and the IDs of any boilerplate masks
over it.

**Claims:** `claim_id`, the quote IDs it rests on, the claim in the user's words, and
its origin.

**Assignments,** one row per claim and theme (R9.9): `claim_id`, `theme_id` or
`unmatched`, and `support`: `supports`, `does_not_support`, or `uncertain`. An
optional `tie_group` marks rows that are alternatives for one claim (R12.6). Each row
has its origin.

**Hard-negative claims** (D4): `claim_id`, the quote IDs, the claim, `negative_kind`
(`period`, `issuer`, or `section`), the theme it would wrongly support, if any, and
its origin. Its expected support is `does_not_support`.

### Anchoring and validation

- **Anchor.** A local draft names each quote by its text, with context when the text
  repeats. The anchor finds the text in the canonical document, and it must occur
  exactly once, or exactly once with the given context. The anchor builds a
  `SpanCandidate` through `parse_span_candidate` and checks it with `validate_span`.
  A `Rejection` is reported against its draft item, and nothing is written for the
  bundle. A quote outside a narrative element is refused (GS15).
- **Validate.** For each committed pointer, the validator slices the text from the
  local canonical document, compares `quote_sha256`, and reruns
  `parse_span_candidate` and `validate_span`. Every candidate passes
  `parse_span_candidate` first, so plan 3's open item on unvalidated offsets cannot
  arise here. The validator also checks the header (the pin, the codebook, the
  signature, and `no_theme`), the IDs, and the wording guard.
- **View.** `gold show` writes `data/runs/gold/views/<event_id>.md`: the canonical
  text with each quote marked, and its claims, themes, and support listed. The user
  verifies, and does the omission pass, against it.

## Curated hard negatives

`tests/fixtures/gold/hard-negatives.toml` holds hard-negative claims, in the gold
contract's form, over Stage 1's canonical fixtures, with at least one each of
`period`, `issuer`, and `section`. They sit outside the pilot and belong to no
partition. They are drafted and verified under GS4, after v0 is frozen. Their
canonical text is committed, so their checks run in the default suite.

## Drafting and tools

- **Briefs.** `briefs/codebook.md` and `briefs/gold.md` state the task, the fields,
  the form of a local draft, and the blinding rules (GS13). The codebook brief lists
  the 20 training bundles' paths, taken from the split. Neither brief quotes a
  release, and both are committed before any drafting.
- **Drafts.** A drafting session writes its draft under `data/runs/gold/drafts/`,
  one file for the codebook or per bundle, which is kept unchanged. The user edits a working copy beside it, and the anchor
  compares the two to derive each item's origin.
- **Commands,** in the application: `pilot split`, `pilot coverage`,
  `codebook freeze`, `codebook validate`, `gold anchor`, `gold show`, and
  `gold validate`. They print IDs, counts, and reasons, never document text; text
  appears only in the view, which the user opens. Each refusal names its reason and
  writes nothing.

## Wording guard

A sibling of `test_corpus_quotes.py` applies F20's rule to every committed Stage 6
file: the split, the coverage report, codebook v0, ADR 0003, the gold, the briefs,
and the curated hard negatives. No 40-character window of any string, with dates
masked, may occur in the canonical text of a pilot document or of a Stage 1 fixture.
A Markdown file is read a paragraph at a time, its line breaks joined, so a copied
phrase cannot hide across a wrapped line.
The pilot leg needs the local store and skips visibly without it, so each gate runs
it with `-rs` and reads "passed". The fixture leg always runs.

## Refusals

Each refusal names its reason, writes nothing, and names a draft item by its ID,
never by its text:
- a quote that is missing, repeated without disambiguating context, outside a
  narrative element, or refused by `validate_span` (OCR text among its reasons);
- a `doc_id` that is not the pinned pilot's document, or whose canonical hash does
  not match;
- a gold file with no signature, or whose `no_theme` disagrees with its assignments;
- a codebook example outside the training partition, or a synthetic one without its
  flag;
- a committed free-text field that shares a 40-character window with the text;
- a gold file naming another pin, split, or codebook version;
- an event in two partitions, or a pilot whose content hash is not the pin's;
- `status = "approved"` unless ADR 0003 exists and cites the codebook's content
  hash.

## Verification

The default suite is offline and calls no model:
- the split over the synthetic pilot, and over pilot v1 and events v1, which are
  committed, reproducing `split-v1.json`'s content hash;
- a test that the split and the report leave the pilot's content hash unchanged
  (P-C7);
- the coverage report over the synthetic acquisition, with its non-zero classes;
- the codebook and gold contracts, the anchor, and the validator over Stage 1's
  fixtures and the curated hard negatives, with a tamper test for each refusal;
- the wording guard's fixture leg.

Local legs, which skip visibly without `data/`:
- the real coverage report reproduces `coverage-v1.json`'s content hash;
- every committed gold file validates;
- the wording guard's pilot leg.

`docs/verification/pilot-v1-gold-set.md` records the split, the report, codebook v0's
approval, the drafting sessions and their model, the signed bundles with their origin
counts, and the limitations: one annotator, whose agreement is not measurable (R12.6,
D2), verifying drafts from one model family (GS4).

## Gates

1. **The split and the report.** The user reads the split's counts and excluded
   events and the report's gaps. Both are committed.
2. **The backup.** The user confirms it (GS12).
3. **Codebook v0.** The user edits the draft and approves it. ADR 0003 and the frozen
   codebook are committed.
4. **The curated hard negatives,** verified and committed.
5. **Three bundles,** each drafted, verified, read for omissions, signed, validated,
   and committed.

## Deferred items

- Stage 6 settles none of the open items. F27, `release-id/2`, and the per-candidate
  citations wait for the next events version (GS2).
- Plan 3's four open items stay with Stage 7. The gold builds every candidate through
  `parse_span_candidate` and never stores a `VerifiedSpan`, so none of them bites
  here.

## Exit criteria

### The roadmap's Stage 6 Exit, clause by clause

| Clause | Met by |
| --- | --- |
| A test places each bundle, with all copies and revisions, in exactly one issuer-and-time split (R12.1/R12.3) | §The split, and its tests |
| The coverage report states the observed count of unavailable, restricted, and parser-failure bundles, and reports a missing class as a coverage gap, never repaired by reselecting; the no-theme count joins at Stage 11 (R12.4, D4) | §The coverage report |
| A test shows the split and the report changing no row of the pilot manifest (P-C7) | §Verification |
| Curated hard negatives exist as fixtures outside the pilot manifest, and the annotation validator accepts hard-negative claims (R12.5, D4) | §Curated hard negatives |
| Codebook v0's decision record names its training-partition discovery corpus (R9.2/R9.7) | ADR 0003 (§The codebook) |
| Annotations on at least three bundles, including release-identification labels, pass the validator | Gate 5 |
| The single-annotator limitation is recorded (R12.6, D2) | The verification record, with GS4's drafting limitation |

## Handoffs to later stages

| Stage | Receives |
| --- | --- |
| 7 | Train gold may inform its prompts; dev and test gold never may (A §749) |
| 8 | The curated hard negatives, for R8.1's misattribution fixtures |
| 9 | The codebook contract and the frozen v0 |
| 11 | The pin, the split, and the coverage report; the signed gold for all 35 partitioned events, once complete; the kept drafts, for GS5's shares; and the limitations. Its release-identification labels give precision over the annotated events. Who writes R8.4's labels is decided there. |
| 12 | The training partition only (R12.3) |
| 14 | Dev for the comparisons, and test scored once (R13.3) |
| 16 | The gold was drafted by a Claude model, so a Claude ceiling records that conflict |

## Rollout

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 6 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

On the plan's completion, append the stage stamp, with the plan's ID and path:

```text
> Stage 6: COMPLETE (YYYY-MM-DD) — implemented by plan <id> (<path>).
> Next: resume the roadmap.
```

This spec amends D2 for Stage 6's gold (GS4). The roadmap's D2 note records the
amendment, in the commit that adds this spec.

On completion, refresh the "Current state" section of `CLAUDE.md`. In the handoff,
state which commands ran, that no model was called from code and no SEC request was
sent, which drafting sessions ran and with which model, and how many bundles are
signed.
