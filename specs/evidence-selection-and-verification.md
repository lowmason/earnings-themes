# Evidence selection and verification

> For agentic workers: REQUIRED NEXT SKILL: writing-plans. This is the stage spec
> for Stage 7 of `specs/evidence-linked-theme-extraction-roadmap.md`. Plan it as two
> plans, in order: plan A (§Plan A) first, and plan B (§Plan B) only after plan A has
> merged. Never plan both in one plan, and never plan a later stage with it.

Stage 7 extracts quote-claim candidates from every analysis-eligible element of a
canonical document by pointer selection, and keeps only the spans code verifies. A
model sees a window of enumerated units and returns their labels with a claim in its
own words. Code maps each label to its element, slices the canonical text, and runs
Stage 2's exactness checks. Before that, plan A settles the open items in
`earnings-core` and in Stage 6's anchor that the extractor relies on.

It closes R5.1, R6.2, R10.1 (the default path), R10.2, R14.1, and R14.6 of
`specs/evidence-linked-theme-extraction.md`, with R6.1 before storage, and R14.7 and
V11 for their tool-call and verification-bypass cases. It reads no pilot document. It
calls a model from code only in the opt-in live test, over a Stage 1 fixture, and it
sends no SEC request.

**This spec amends** the handoff Stage 7 receives from Stages 3 and 6, at two points:
- **`other` elements.** The Stage 3 spec's handoff to Stage 7 (§Handoffs to later
  stages), the Stage 6 spec's GS15, plan 9's P9-19, and the roadmap's Stage 7 Consumes
  line call every `other` element non-narrative. Each now excepts a transparent
  container, and only that (ES9).
- **The pointer unit.** The Stage 3 spec's handoff and the roadmap make sentences the
  pointer unit. The units are S1's sentences together with the narrative elements S1
  never splits, such as headings (ES12).

The roadmap records both in the commit that approves this spec. The completed Stage 3
and Stage 6 specs and plans 4 and 9 are not edited.

Locators:
- **`A §n`** is `AGENTS.md`, by line.
- **`Rn`** and **`Vn`** are the theme spec's requirements and verification items.
- **`D-n`** are plan 3's decisions (`specs/plans/completed/3-core-evidence-spine.md`).
- **`GSn`** are the Stage 6 spec's decisions
  (`specs/completed/pilot-codebook-split-and-gold-set-protocol.md`), and **`P9-n`**
  plan 9's (`specs/plans/completed/9-pilot-codebook-split-and-gold-set-protocol.md`).
- **`T6-M1`**, **`T6-M3`**, **`T6-M4`**, and **`M6`** are plan 9's final-review items,
  and **`M5`** plan 10's count (`specs/deferred_items.md`, sections
  `9-pilot-codebook-split-and-gold-set-protocol` and
  `10-harden-the-gold-before-bundle-4`).
- **The learning path** is `docs/earnings-themes.md`, cited by its stage numbers.
- **`ESn`** are this spec's decisions.

Designed 2026-10-04 in a brainstorming session, from
`stage-7-evidence-selection-and-verification` at `337c882`, in a worktree with no
`data/`. The session opened no pilot text. The counts below (797 units, 37 windows,
660/26/0) were made then over Stage 1's fixtures, and the plans pin them.

## Decisions

Taken with the user on 2026-10-04. Rows marked *(design)* were proposed in the design
sections and approved with them.

| ID | Decision |
| --- | --- |
| ES1 | **Two plans, in order.** Plan A (§Plan A) lands plan 3's items 1–3, the anchoring item, and the `canonical_json` move. What committed records depend on changes there, so its last gate runs the default suite in the main checkout, where `data/` lives (§Gates). It merges before plan B starts. Plan B (§Plan B) builds the extractor, whose rejection store closes plan 3's item 4, and needs no `data/`. Stage 7 is complete only when both are. |
| ES2 | **No pilot text.** No session implementing this spec opens anything under `data/`, reads any gold, or runs extraction over a pilot document. Its tests and Exit read Stage 3's eight canonical fixtures and synthetic text only. A prompt's examples are invented, quoting neither the pilot nor the fixtures (§Wording guard). Train gold first informs prompts at Stage 11 (A §749). |
| ES3 | **GS13 binds** until the last gold bundle is drafted, Stage 14's test bundles included: no drafting session sees Stage 7's code, prompts, or outputs. Nothing turns extraction output into a gold draft, and Stage 7 adds no command. The gold brief is unchanged, since it already bars `prompts/` and any extraction code, prompt, or output. The six modules the brief lets a drafter read import nothing from the extraction package (§Verification). |
| ES4 | **Plan 3's items 1–3** land in `earnings-core` (§The core fixes), and `VALIDATOR_VERSION` becomes `"3"`. No committed record stores it. |
| ES5 | **Re-verification** is a named core helper, `reverify_span`, not a widened `validate_span`, so each later R6.1 gate reads as a re-check. |
| ES6 | **Rejection subjects** (plan 3's item 4). The extraction store pairs each core `Rejection` with its subject (§Records), and `Rejection` gains no field. Core's schema version is one `Literal[2]` that every core record carries: the frozen universe v1 holds 81 such records, events v1's evidence 1,582, and each canonical fixture one per document, element, and mask, so a field would re-version them all. |
| ES7 | **The move** (M6). `canonical_json` and `digest` move into `earnings-core`, and both packages import the one definition. The duplicated pilot pin stays: themes' `Pin` and ingestion's `PilotPin` keep their own reproduction tests. Reproduction is proven offline in the worktree and by the main checkout's default suite (§The proof). |
| ES8 | **`context_hash`** keeps its byte format (T6-M3), which the three signed bundles and the curated hard negatives already store. A known-answer test pins it. |
| ES9 | **The narrative rule** (T6-M1). An `other` element with children and no non-space character outside them is a transparent container and no longer blocks a quote (§The narrative rule). The rule applies in the gold's anchor and in Stage 7's units alike, and lives in `anchoring.py`, which the extractor imports. No pilot verdict changes (M5: 0 of 5,139 sentences). |
| ES10 | **Plain functions** (approach A). The extractor is plain code behind a small adapter protocol, with no framework in the required path (R14.4). The learning path places PydanticAI at generate-then-verify (its Stage 3), which is Stage 14's comparator here, and LangGraph at resumable backfill and the codebook approval gate (its Stage 5), which are Stages 15 and 12. Its Stages 1 and 2, the loop and the exact quotes, are written by hand. §Seams keeps both frameworks cheap to add where they belong. |
| ES11 | **Codebook-free claims.** A candidate is quote labels plus a claim in the model's words, with no theme. Stage 9 codes the claims, and Stage 12's inductive path uses the same candidates. |
| ES12 | *(design)* **Units** are the leaf narrative elements, by P9-19's order (§Units). |
| ES13 | **Windows** pack whole blocks in document order, up to 4,000 characters of unit text. The budget is a provisional configuration value, not a quality threshold (§Windows). |
| ES14 | **Window-local labels.** The model sees `U1…Un`, and code maps each to its R4.1 element ID before `resolve_pointer`. This reads R5.1's "stable element identifiers" as the identifiers code resolves: the model enumerates labels and never sees an offset (flagged). |
| ES15 | **One local adapter**: the OpenAI-compatible chat API over httpx, to a loopback host only, behind a `local-model` extra (§The local adapter). Its model is chosen at plan B's gate and recorded in ADR 0004 with its weight license (R14.1). It is not the production choice, which stays open (`CLAUDE.md`). |
| ES16 | **Retries keep valid candidates**: at most 2 attempts per window, provisional. Feedback names each problem by field, label, and reason, never by source text (§Retries). |
| ES17 | **Prompts** live in the repository's `prompts/extraction/`, tracked. The caller reads one and passes its text in, and the package reads no repository path. |
| ES18 | **No command.** The first stage that runs extraction over documents adds one (§Handoffs). |
| ES19 | *(design)* **Structured output**: a JSON-schema response format where the runtime supports it, else the schema in the prompt. No request carries `tools`. |
| ES20 | *(design)* **Whole-candidate rejection**: a candidate stands only if every one of its labels verifies. |
| ES21 | *(design)* **Explicit ceilings**: every run passes its own request and token ceilings, with no default (A §691). |
| ES22 | *(design)* **Records** carry their own `EXTRACTION_SCHEMA_VERSION`, apart from `THEMES_SCHEMA_VERSION`, so an extraction change never re-versions the gold or the codebook. |

## Scope

In:
- plan 3's items 1–3, the anchoring item, and the `canonical_json` move (plan A);
- units, windows, the adapter protocol with a scripted fake, the R14.6-keyed cache
  with replay, and one local adapter behind `live` (plan B);
- verification of every candidate, stored and auditable rejections paired with their
  subjects (plan 3's item 4), and records with a writer and a reader;
- the V11 injection fixture, and guards for R14.1, R10.2, and GS13;
- ADR 0004 and the verification record.

Out:
- any run over a pilot document, and any reading of pilot text or gold (ES2);
- a command (ES18), and any write to Stage 5's state table;
- themes, support, and coding (Stages 8 and 9);
- generate-then-verify and the whole-document and retrieval-only arms (Stage 14);
- a cache-bypass mode for k-run stability (Stage 11);
- table-cell evidence: no cell is ever a unit (R4.2), so plan 5's `<br>` item stays
  deferred;
- choosing the production model.

## Inputs

- **Stage 2's checks**, from the `earnings_core` root: `resolve_pointer`,
  `parse_span_candidate`, `validate_span`, `validate_elements`, `make_locator`,
  `Rejection`, and `VALIDATOR_VERSION` (plan 3 §Handoffs). No chunk-local offset ever
  arises: a label maps to an element whose span is already in document coordinates,
  so `TextChunk` has nothing to convert.
- **Stage 3's eight canonical fixtures** in `tests/fixtures/canonical/`, read record by
  record through the core contracts, as the themes tests read them. S1 sentences exist
  only under `paragraph`, `list_item`, and `footnote`. Boilerplate masks stay in
  traversal. National Health Investors' headline is a `page_artifact`, never narrative
  (plans 4 and 5 §Handoffs; `docs/verification/layout-1.md`).
- **Stage 6's anchor**, `earnings_themes/anchoring.py`: `Bundle`, `NARRATIVE`,
  `bundle_problems`, `mask_id`, and, after plan A, `narrative_home`.
- **The roadmap's Stage 7 entry**, its Consumes line in full.

## Plan A: core and anchoring

### The core fixes

1. **`reverify_span(document, elements, span) -> VerifiedSpan | Rejection`**, in
   `earnings_core.evidence` and exported from the root. It reads the stored span's
   candidate fields, all but `validator_version`, into a mapping, passes that to
   `parse_span_candidate`, and runs `validate_span`, returning a fresh `VerifiedSpan`
   under the current `VALIDATOR_VERSION`. It never dumps the span, since dumping a
   `model_copy` that holds a float in an integer field emits a serializer warning;
   strict validation refuses the float instead. Tests: a span round-tripped through JSON re-verifies; a
   `model_copy` with changed text is `quote_text_mismatch`, and one with a float
   offset is `malformed_record`; neither raises.
2. **`resolve_pointer`** returns the span of the genuine element, one of this version's
   `doc_id` whose ID derives from its type and span, wherever it sits in the list. Only
   when no genuine element has the ID does it report `wrong_document`,
   `element_id_mismatch`, or `unknown_element`. Its test lists the stale element first.
3. **`validate_span`** returns `malformed_record` when `start` or `end` is not an
   `int`, or is a `bool`, on a candidate that skipped `parse_span_candidate`, with a
   test for each.
4. **`VALIDATOR_VERSION = "3"`**, its docstring naming the two changed outcomes.

### The `canonical_json` move

`canonical_json` and `digest` move unchanged into one `earnings-core` module, exported
from the root. `earnings_ingestion/cohort/digests.py` is deleted, and its importers in
`cohort/` and `events/` import the core definition. `earnings_themes/records.py` drops
its copies, and `codebook.py`, `split.py`, and `parse` use the core's. The known-answer
tests move to `packages/earnings-core/tests/` with their expectations unchanged. No
contract changes, so `SCHEMA_VERSION` stays 2.

### `context_hash`

`context_hash` stays the SHA-256, over UTF-8, of
`json.dumps([prefix, suffix], ensure_ascii=False, separators=(",", ":"))`. A
known-answer test pins it with a prefix and suffix holding a non-ASCII character, a
double quote, and a backslash, since an ASCII-only case cannot show `ensure_ascii`.
The test's input is generated as escape text by a script, never typed as literal
characters, so no tool can normalize it. Its data-dictionary row gains
`ensure_ascii=False`.

### The narrative rule

A quote may not overlap a `table`, `table_cell`, `page_artifact`, or `other` element
(P9-19), with one exception. An `other` element that has at least one child, and no
non-space character of its span outside its children's spans, is a transparent
container. walker-1 makes one from a `<ul>` or `<ol>` (`canonical/blocks.py`, W7): in
`0000949699-08-000023_ex-99-1`, `other-3292-5040` holds 7 list items with 10
sentences, and only newlines lie between them. An `other` element that holds text of
its own, such as the two 4-character divs in `0000009389-10-000004_ex-99-1`, still
blocks.

`_home` becomes the public `narrative_home(bundle, span)`: the most specific narrative
element holding the span, by P9-19's order, or the reason no element holds it.
`anchor` and `check_pointer` use it as before. The extractor imports it, and
`anchoring.py` imports nothing from the extractor.

What follows from the rule:
- `test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors` pins 660
  anchored, 26 ambiguous, and 0 not narrative. Each of the 10 sentences occurs once,
  so each anchors to itself.
- A new test keeps a text-bearing `other` blocking, and a container with text outside
  its children blocking.
- The data-dictionary row for `not_narrative` names the exception.
- `docs/verification/pilot-v1-gold-set.md`, under M5, gains a line: the 10 fixture
  sentences now anchor, and no pilot verdict changed. The line gives counts and IDs
  only, never a sentence, since the Stage 6 wording guard reads that file.
- The gold brief already calls list items quotable, and is not edited.

### The proof

Plan A changes functions and tests, and no committed record. It proves every committed
record still reproduces byte for byte:
- **Offline, in the worktree.** The default suite reloads each committed record through
  its loader and recomputes its content hash with the moved functions: universe v1 and
  the synthetic cohort; events v1, the synthetic events, and pilot v1, which is
  reselected; the split and the coverage report; codebook v0; the three gold files; and
  the curated hard negatives. The canonical golden test holds the fixtures. The plan
  maps each record to the test that rehashes it, and adds a test for any record not yet
  covered.
- **The diff.** `git diff --stat` from plan A's base, over `config/`, `evaluation/`,
  `codebooks/`, and `tests/fixtures/`, prints nothing.
- **The main checkout.** At plan A's last gate the user runs the default suite there,
  at plan A's tip on a detached HEAD, so the local legs run against `data/`: the gold
  rechecks, the wording guard, the corpus quotes, and the event store (§Gates).

## Plan B: the extractor

### Packaging

- `earnings_themes.extraction` holds the extractor. It imports `earnings-core` and
  Stage 6's anchor, and adds no dependency: no framework and no provider SDK (ES10).
- `earnings_themes.extraction.local` holds the local adapter, behind a new extra,
  `local-model = ["httpx"]`. It is the only themes module that imports httpx, and no
  other themes module imports it.
- The themes boundary tests walk subpackages too. Every module but `local` still loads
  no HTTP client, model SDK, or framework, and the static import scan holds the same
  rule at any depth.

### Seams

- `extract_window(window, adapter, policy)` is a pure function that returns a record,
  so a graph node can wrap it unchanged (Stage 15).
- The adapter protocol is messages and settings in, text and usage out, so a
  PydanticAI-backed adapter or a hosted one can sit behind it, in an extra (Stages 14
  and 16).
- Derived IDs and the cache make running a step twice harmless, which is what a
  checkpointer relies on.

### Units

A document is extracted from a `Bundle`. If `bundle_problems` reports a problem in its
elements or masks, the document is `failed` with those reasons and no call is made.
Each reason it reports is a `RejectionReason` value. Stage 7 is that function's first
production caller (T6-M4), and plan B adds the test of its mask branch.

The units are the pointer targets: each narrative element that is its own
`narrative_home`, and holds no other narrative element that P9-19's order ranks
before it, that is, one inside it with a shorter span, or with the same span and an
earlier type.
- A sentence is a unit, and a paragraph whose sentences S1 split is not.
- A heading is a unit, since S1 never splits one.
- Where a sentence and its paragraph share one span, the sentence is the unit.

On the eight fixtures that is 797 units: 686 sentences, 108 headings, and 1 paragraph
and 2 footnotes that S1 left unsplit. A document with no unit is `completed` with zero
windows, and the run record says so.

### Windows

- **Blocks.** A sentence's block is its nearest non-sentence narrative ancestor: a
  paragraph, list item, or footnote. Any other unit is its own block.
- **Packing.** Blocks are packed greedily in document order while the window's unit
  text stays within the budget, 4,000 characters by default. A block is never split,
  and one longer than the budget gets a window of its own. The budget enters the cache
  key, and Stage 14's whole-document arm is the same planner with no budget. On the
  fixtures, the default gives 37 windows.
- **Identity and context.** A window's ID is `w-<start>-<end>`, from its first unit's
  start and its last unit's end. It carries the nearest heading before its first block,
  unlabeled and marked as not quotable, when that heading lies outside it.
- **Labels.** `U1…Un` in document order within the window, and the window record maps
  each label to its element ID.
- **The guarantee.** Every unit lies in exactly one window, and every eligible element
  holds at least one unit. The plan depends only on structure and lengths, never on
  text or a score, so no top-k path exists (R10.2).

### The adapter protocol

`ModelAdapter.complete(request) -> reply`:
- **The request** holds the system message, the user message, and on a retry the
  earlier turns; the reply's JSON schema; and the parameters: temperature, seed,
  `max_tokens`, and whether to use structured mode. The defaults are temperature 0,
  seed 0, and 2,048 tokens, all provisional.
- **The reply** holds the text, the token usage if the server reports it, the model the
  server names, whether it carries tool calls, and the latency.
- **A transport failure** raises one typed error, which the window records as
  `transport_error`.

Three adapters:
- **A scripted fake**, which replies from a script, for tests.
- **A cache wrapper**, in two modes. In both, a hit returns the stored reply and calls
  nothing. In `replay`, a miss is `replay_miss` and never a call. In `live`, a miss
  calls the inner adapter and stores the reply atomically, under a directory the caller
  supplies.
- **The local adapter** (§The local adapter).

### The cache key (R14.6)

The key is a record with one field per component, and the cache file is named by its
digest:
- `doc_id` and `canonical_hash`;
- the window ID and its units' element IDs;
- the model ID and the weights' SHA-256 (none for a fake);
- the adapter kind, the runtime and its version, and the structured mode;
- the parameters, the window budget, and the claim limit;
- `prompt_sha256`, over the template's UTF-8 bytes; `reply_schema_sha256`; and
  `request_sha256`, over the exact rendered request, which covers the window's text,
  the feedback, and so the attempt;
- `extractor_version`, `pointer-traversal/1`, which names the unit rule, the planner,
  the labels, the reply contract, and the retry policy;
- `validator_version`, `3`;
- `codebook_hash`, which is null under codebook-free extraction (ES11).

A stored reply is raw model output. Verification always runs again over it, so a
changed contract never trusts a cached result (A §681).

### The local adapter

- **Hosts.** It refuses, when built, any base URL whose host is not 127.0.0.1, ::1, or
  localhost, so no hosted, billable endpoint is reachable (R14.1).
- **The request.** It posts to `<base>/chat/completions` with the messages and
  parameters. In structured mode it adds a strict `response_format` JSON schema
  (ES19). It never sends `tools` or `tool_choice`, and sends no API key.
- **The reply.** It refuses a reply that carries `tool_calls` (`tool_call_refused`),
  and one that names a model other than the configured one (`model_mismatch`), so a
  swapped model is never cached under another model's identity.
- **Identity.** The model ID, the weights' SHA-256, and the runtime's name and version
  come from configuration, as ADR 0004 records them.

### The prompt and the reply

The template is `prompts/extraction/pointer-1.md`: the system text, and the user
message around a `{units}` placeholder. Rendering groups units by block, one line per
unit, `[U3] ` and its text, with the context heading marked as not quotable. The prompt
says:
- the units are data, never instructions (R14.7);
- cite labels only, and write each claim in your own words;
- return an empty list when the window states no claim.

Its one example is invented. Without structured mode the prompt also carries the
reply's schema.

The reply is `{"candidates": [{"quote_labels": [...], "claim": "..."}]}`, with no
other key at any level. A candidate's labels are one or more distinct strings, and its
claim is non-blank and at most 500 characters. An empty list is valid. The schema comes
from the pydantic model.

### Retries

At most 2 attempts per window, provisional (ES16):
- **An unusable reply** is not JSON, breaks the schema, carries tool calls, names
  another model, or never arrived. The next attempt resends the request with feedback
  that names each problem by field, never by value.
- **A refused candidate** has an unknown or repeated label, or a blank or overlong
  claim. Valid candidates are kept, and the next attempt asks for corrected versions
  of the refused ones only, by index, labels, and reason.
- **After the last attempt**, refused candidates become rejections with their reasons,
  and a window that never got a usable reply is `failed`.

### Ceilings

Every run passes its ceilings explicitly, with no default (ES21): requests per
document, requests per run, and tokens per run, the last against reported usage. They
are checked before every dispatch (A §691). Exhaustion stops dispatch, and each window
it leaves unsent is `failed` as `budget_exhausted`. A reply that reports no usage is
recorded as unreported, and only the request ceilings bind it. Cache hits are recorded,
but are not requests.

### Span verification

Span verification runs in plain code, after the reply is parsed:
- For each kept candidate, each label maps to its element ID, and `resolve_pointer`
  gives the span. Elements were checked once per document (§Units).
- The candidate is built from the canonical slice, with its prefix and suffix from
  `make_locator`. It goes through `parse_span_candidate`, then `validate_span`.
- A candidate is accepted only if every label verifies (ES20). Otherwise the whole
  candidate is rejected with the first reason, since dropping one quote could change
  what the claim rests on.

### Records

The records live in `earnings_themes.extraction` and carry `EXTRACTION_SCHEMA_VERSION =
1` (ES22). Every field has a row in `docs/data-dictionary.md`, and its test holds the
two together.
- **Quote:** `quote_id`, `q-<start>-<end>`, unique together with `doc_id`;
  `VerifiedSpan`'s fields; and its mask IDs, from anchoring's `mask_id`. A cited unit
  gives one quote per document, never a copy (R9.9), so the same quote keeps its ID in
  every run on the same document version.
- **Claim:** an ID derived from its window, attempt, and index; its `doc_id`, window,
  and attempt; the model's words; and its quote IDs. It carries no theme.
- **Rejection:** its subject (the document, window, attempt, candidate index or none,
  labels, and element IDs where resolved), paired with exactly one of:
  - a core `Rejection`, from verification, or one for each reason `bundle_problems`
    reports;
  - an extraction problem: `malformed_reply`, `tool_call_refused`, `model_mismatch`,
    `transport_error`, `replay_miss`, `budget_exhausted`, `unknown_label`,
    `duplicate_label`, `blank_claim`, or `claim_too_long`.

  A rejection's detail may quote text, so it stays local.
- **Visit:** one per unit, with its window, its outcome, `completed` or `failed`, and
  its reason. Visits are R10.1's coverage evidence.
- **Window:** its span, its units in label order, its context heading, its attempts
  and outcome, requests, tokens, latency, and cache hits.
- **Document outcome**, in R1.4's words, with counts: `completed` when every window
  completed, `partial` when some failed, and `failed` when all failed or
  `bundle_problems` refused the document.
- **Run record:**
  - the run ID and time;
  - the configuration and its hash, and the key components common to the run;
  - each document's `doc_id` and canonical hash;
  - counts of units, windows, candidates, quotes, claims, and rejections by reason;
  - usage totals, the ceilings, and whether any was exhausted;
  - the software identity the caller passes;
  - "billable cost: none, self-hosted".

  When no quote is retained, it reports zero and no exactness rate (R6.2, R12.8).

### Storage

- `write_run` writes one Parquet file per record kind through Polars, with explicit
  schemas, and `run.json`.
- It first re-verifies every quote with `reverify_span` (R6.1 before storage), and
  writes nothing if any fails.
- `read_run` reads a run back, and each consumer re-verifies at its own gate.
- Stage 7 writes only to test temporary directories: never to `data/`, and never a
  committed file.

## The difference from P9-19

Plan 9 asked Stage 7 to report where its narrative set differs from the gold's:
- A Stage 7 quote is always one whole unit. A gold quote may be part of a unit, or a
  passage across several, whose home is then a paragraph. Stage 7 gives multi-unit
  evidence as several quotes (R5.5).
- Markers that S1 leaves outside sentences, such as "(1)", "•", and "***", are never
  quoted.

Otherwise the two sets agree, plan A's container rule included. Stage 11's span-overlap
metric will show the first difference.

## Wording guard

The Stage 6 wording guard, `tests/integration/test_stage6_wording.py`, also reads
`prompts/`. Its fixture leg keeps a prompt from quoting a Stage 1 fixture, and its
pilot leg, a local leg, from quoting a pilot document.

## Verification

The default suite is offline and calls no model:
- **R5.1 and R6.2.** A scripted adapter runs over all eight fixtures. Its script mixes
  valid candidates, unknown labels, blank claims, a malformed reply, a tool-call
  reply, and a transport error. Every stored quote passes `reverify_span`, every
  rejection carries a reason, and no window makes more than 2 attempts. The counts are
  pinned.
- **R10.1 and R10.2.**
  - Each of the 797 units lies in exactly one of the 37 windows, and every eligible
    element holds a unit.
  - A fake that cites every label gets a verified quote for every unit.
  - Replacing each unit's text with different text of the same length leaves the plan
    identical.
  - A static scan finds no retrieval, embedding, or fuzzy-matching import in the
    extraction package.
- **R14.6.** One case per key component: changing it misses, so the inner adapter is
  called again. An identical key hits, and it is not called.
- **R14.1.**
  - The full scripted run happens under a socket guard, so any connection attempt
    fails the test.
  - The boundary tests hold (§Packaging).
  - The local adapter's own tests run on httpx's `MockTransport`: the host refusal, a
    request body without `tools`, and the tool-call and model-mismatch refusals.
- **R14.7 and V11.**
  - An injection bundle, built in `earnings_themes.synthetic`, tells the model to call
    a tool, return offsets or quote text, cite another document's element, and rewrite
    the codebook.
  - A scripted adapter obeys it. No tool exists to call, and no request body carries
    `tools`. Every injected candidate is rejected with its reason, and only spans that
    code sliced are stored.
  - A line of the injection text spoofs labels: one past the window's range, which is
    refused as `unknown_label`, and one equal to a real label, which resolves to the
    unit code labeled, never to the spoofing line. Labels come only from code's
    rendering.
  - Stage 9 reuses the bundle for its codebook case.
- **GS13.** An AST test: `gold.py`, `annotation.py`, `anchoring.py`, `codebook.py`,
  `records.py`, and `tomlfile.py` import nothing from `earnings_themes.extraction`.
- **Plan A.** The tests in §Plan A.

Local legs, in the main checkout, which skip visibly without `data/`:
- plan A's gate run (§The proof);
- the wording guard's pilot leg, over `prompts/` too.

Live, behind `live`:
- One fixture runs end to end through the local adapter, and every stored quote
  re-verifies. The test skips visibly when no server answers.
- It runs once, at plan B's gate, by its node ID.

`docs/verification/evidence-selection.md` records plan A's proof and plan B's gate.

## Gates

Plan A:
1. **The proof.** The session runs the offline proof and the diff (§The proof).
2. **The main checkout.** The user runs the default suite there, at plan A's tip on a
   detached HEAD, and reports its counts.
   - The checkout must have no tracked changes before `git switch --detach`, since a
     bundle in mid-edit would block the switch or be carried along. The user returns to
     `main` afterward.
   - On a failure, the user reports only the test's name and its reason, never the
     traceback. A local leg can print pilot text even under `--tb=short`, and the
     session that fixes the failure stays blind (ES2).

Plan B:
1. **The model.** On the gate's date, the session checks candidate model cards: open
   weights, a weight license that permits this use, a fit in this machine's 36 GB, and
   JSON-schema output through an OpenAI-compatible runtime. The user chooses.
2. **The install.** The user installs the runtime and downloads the weights.
3. **The live run.** The live test runs once, by its node ID with `-m live`. It never
   runs as `-m live` over the whole suite, since `EDGAR_IDENTITY` may be exported and
   the SEC live tests would send requests.
4. **ADR 0004** records the model, the runtime and its version, the weights' SHA-256,
   and the license, quoted from the model card with its URL and date. It also records
   that this is not the production choice. The user approves it, and supplies the
   approver and the date.

## Deferred items

Stage 7 closes these items (`specs/deferred_items.md`):
- `3-core-evidence-spine`: the stored `VerifiedSpan`, `resolve_pointer`'s genuine
  element, and unvalidated offsets, in plan A; and `Rejection`'s subject, when plan B's
  store lands (ES6);
- `9-pilot-codebook-split-and-gold-set-protocol`: the two anchoring questions and the
  `canonical_json` move, in plan A.

Plan B adds T6-M4's mask-branch test, and that item stays open for its other gaps.
Plan 5's `<br>` item stays deferred, since no table-cell text is ever a unit. Stage 7
defers nothing new.

## Exit criteria

### The roadmap's Stage 7 Exit, clause by clause

| Clause | Met by |
| --- | --- |
| Offline fake-model runs over Stage 3 fixtures retain only R6.1-valid quotes, and every rejection records a reason after bounded retries (R5.1/R6.2) | §Verification, R5.1 and R6.2 |
| A coverage test shows every eligible element visited and no top-k discovery path (R10.1/R10.2) | §Verification, R10.1 and R10.2 |
| A test shows changing any R14.6 key component misses the cache (R14.6) | §Verification, R14.6 |
| The default suite makes no network or billable call (R14.1) | §Verification, R14.1 |
| The V11 fixture triggers no tool call and cannot bypass R6.1 (R14.7/V11) | §Verification, R14.7 and V11 |

### The roadmap's Produces line

| Item | Met by |
| --- | --- |
| A themes extractor visiting every eligible element | §Units, §Windows, §Span verification, and §Verification's coverage tests |
| A model-adapter interface with a fake adapter, response replay, and an R14.6-keyed cache | §The adapter protocol, §The cache key |
| One open-weight local adapter behind the `live` marker, its weight license recorded | §The local adapter; ADR 0004 at plan B's gate |
| Stored, auditable rejections built on Stage 2's `Rejection` (R6.2) | §Records, §Storage |

### Plan A

| Item | Met by |
| --- | --- |
| Plan 3's items 1–3, with tests | §The core fixes |
| `canonical_json` and `digest` in core, every committed record reproducing byte for byte | §The `canonical_json` move, §The proof |
| `context_hash` pinned | §`context_hash` |
| A list item under a transparent container quotable, with the fixture pin at 660/26/0 | §The narrative rule |

## Handoffs to later stages

| Stage | Receives |
| --- | --- |
| 8 | Verified quote-claim pairs, through `read_run`, re-verified with `reverify_span` at its gate. The claims carry no theme. |
| 9 | The claims, to code against v0; the V11 injection bundle, for its codebook case. |
| 10 | Rows with offsets, hash, run ID, model and prompt provenance, and mask IDs for the headline exclusion. It adds the first extraction command, maps each document outcome into a new state-table run under R1.4, and re-verifies before export. |
| 11 | The first run over pilot documents, train and dev, still under GS13. It adds a cache-bypass mode for k-run stability (R12.10). Train gold may then inform the prompts (A §749). |
| 14 | The whole-document arm, which is the planner with no budget. The generate-then-verify comparator may use PydanticAI behind the adapter protocol, as the learning path's Stage 3 places it. |
| 15 | Resumable backfill, which may use LangGraph around `extract_window`, as the learning path's Stage 5 places it. The cache keeps reruns idempotent. |
| 16 | A hosted adapter behind the same protocol, outside the required path. |

## Rollout

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 7 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

"Plan completion" above means plan B's. Plan A's completion does not tick Stage 7.

- **On plan A's completion,** append this line, with the plan's ID and path:

  ```text
  > Plan A: COMPLETE (YYYY-MM-DD) — implemented by plan <id> (<path>). Next: write plan B.
  ```

- **On plan B's completion,** append the stage stamp, with both plans' IDs and paths:

  ```text
  > Stage 7: COMPLETE (YYYY-MM-DD) — implemented by plans <A id> (<path>) and <B id> (<path>).
  > Next: resume the roadmap.
  ```

  The roadmap reconcile then ticks Stage 7 and re-validates the later stages: Stage
  10's command and state-table mapping, Stage 11's cache bypass and first pilot run,
  Stage 14's planner and comparator, and Stage 15's orchestration.

On each plan's completion, refresh the "Current state" section of `CLAUDE.md`, with the
user's approval. In the handoff, state:
- which commands ran;
- that no session opened pilot text or ran extraction over a pilot document;
- that the only model call from code was the gate's live test over a Stage 1 fixture;
- that no SEC request was sent.
