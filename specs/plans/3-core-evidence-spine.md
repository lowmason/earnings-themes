# Core Evidence Spine (Stage 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 2 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

**Goal:** Give `earnings-core` the browser-neutral contracts and the exactness
validator that every later stage builds on:

- a hashed, versioned canonical document;
- typed elements with derived IDs and code-point spans;
- overlay masks and prefix/suffix span locators;
- an R6.1 validator with no tolerance parameter.

Also add the root pytest configuration, with a registered `live` marker and
collision-safe test imports.

**Architecture:**

- **Modules.** Twelve small modules live in
  `packages/earnings-core/src/earnings_core/`, one responsibility each. Every record
  type is built on one frozen, closed, strictly typed Pydantic base model.
- **Checks.** The checks are pure functions of one `CanonicalDocument` and its
  elements. They never raise on bad evidence: each refusal is a `Rejection` record
  naming one `RejectionReason`, so rejections stay auditable (R6.2). Each check
  recomputes stored hashes and IDs rather than trusting construction.
- **Tests.** Nothing touches the network, a model, or a browser. The tests run on:
  - an in-memory sample call transcript;
  - synthetic HTML;
  - the Stage 1 fixtures' committed `gold.toml` files.

**Tech Stack:**

- Python 3.14.0 and uv 0.12.15.
- pydantic 2.13.5, already a declared dependency of `earnings-core`.
- pytest 9.1.1 and Ruff 0.16.8, from the workspace `dev` group.
- lxml 6.1.3, in one contract test only. The environment already has it because
  `earnings-ingestion` declares it.
- From the standard library: `hashlib`, `re`, `enum`, `html.parser`, `tomllib`,
  `unicodedata`, `subprocess`.

There is no new dependency: `uv.lock` does not change.

## The roadmap entry this plan implements

Stage 2 has no stage spec of its own. The roadmap entry is its specification,
quoted verbatim:

> - [ ] Stage 2: Core evidence spine
>       Objective: Give `earnings-core` the contracts and exactness validator that every later stage builds on.
>       Spec: R3.1–R3.4 (contracts), R4.1 (element contract), R5.4, R5.5, R6.1, R13.2, V9; A §193.
>       Gap closed: R3.2, R3.3, R5.4, R5.5, R6.1, R13.2; V9 (all cases except normalization and sentence splitting); Dev tooling row.
>       Consumes: Stage 1's decision record, ADR 0001, and V2's element types and nesting observed in the fixtures' gold.
>       Produces: `earnings-core` contracts for a hashed, versioned canonical document, typed elements with stable IDs and code-point spans, overlay masks, and prefix/suffix span locators; an R6.1 validator with no tolerance parameter; root pytest configuration with a registered `live` marker and collision-safe test imports.
>       Exit: `uv run --locked --all-packages pytest packages apps tests -m "not live"` passes the Stage 2 V9 cases, each failure class rejected with a recorded reason (R3.2/R3.3/R5.4/R5.5/R6.1/R13.2); a test shows applying a mask leaves the canonical hash unchanged; the pytest configuration registers `live` (Dev tooling row).
>       ROUTING: writing-plans

`specs/browser-rendering-integration.md` (approved 2026-09-24) also binds Stage 2. It
limits Stage 2 to browser-neutral contracts: `TextSpan`, `CanonicalDocument`,
`DocumentElement`, `ArtifactRef`, and "exactness and attribution validators that
resolve elements and quotes against one `CanonicalDocument`". Its Stage 2
verification asks for three things:

- unit tests for span bounds, canonical hashes, stable element identifiers, parent
  references, table context, and artifact hashes;
- a contract test that "two different parser implementations can emit the same
  browser-neutral element schema";
- a check that "no core or themes import resolves Selenium or a browser package".

What this plan uses from Stage 1:

- **ADR 0001**
  (`docs/adr/0001-use-the-bespoke-lxml-walker-as-the-base-parser-for-release-canonicalization.md`).
  The bespoke lxml walker is the base parser, frozen in
  `expirements/parser-fidelity/` until Stage 3 ports it. This plan does not port it.
- **V2's section "Element types and nesting observed in the gold (for Stage 2)"**
  (`docs/verification/V2-parser-fidelity.md`):
  - the gold uses the block types footnote, heading, list_item, page_artifact,
    paragraph, and table;
  - headings have levels 1, 2, 3 or none, and list items level 1;
  - no fixture nests a table.
- **The eight fixtures** in `tests/fixtures/releases/`. Their `gold.toml` files hold
  574 gold blocks, which Task 12 reads.

## Global Constraints

Every task's requirements include these.

**Locators:**

- `A §n` is `AGENTS.md` at line `n`.
- `Rn` and `Vn` are `specs/evidence-linked-theme-extraction.md`.
- `Bn` are the decisions of `specs/browser-rendering-integration.md`.
- `D-n` are this plan's decisions, listed below.

**The invariant, verbatim (R6.1).** "Before storage, before support judgment, and
before export, every accepted span satisfies:

```
0 <= start < end <= length(canonical_text)
quote_text == canonical_text[start:end]
stored_canonical_hash == sha256(utf8(canonical_text))
```

Validate identifiers, strict integer offsets, and hash equality as well as text
equality. A verbatim string found in the wrong document, speaker turn, or section
fails attribution and is rejected."

R13.2 adds that the invariant "is **not** a threshold and is not open". So no check
takes a tolerance, a similarity score, or a normalization step: text is compared with
`==`.

**Offsets (R3.2, A §505).** "Offsets are **Unicode code points**, zero-based,
half-open `[start, end)`." They index a Python `str`: not UTF-8 bytes, not UTF-16
code units, and not model tokens.

**Hash (R3.1).** SHA-256 over the canonical text's UTF-8 bytes, written as 64
lowercase hexadecimal characters.

**Versions (R3.3).** "A change to canonical text creates a new version. Never mutate
text beneath existing spans." Every contract is frozen, and changed text is always a
new `doc_id` (D-2).

**Code decides exactness (A §518, R5.1).** No model, fuzzy match, or repair step may
accept, patch, or promote a span.

**Browser-neutral (B1, B2).** This plan adds none of the following, anywhere:

- a Selenium or Playwright import;
- browser executable configuration;
- DOM traversal;
- a screenshot model;
- a browser-specific field.

`earnings-core` imports no sibling package and no browser package. Task 1's
import-boundary tests enforce this for core, ingestion, and themes.

**Offline.** Default tests make no network call and no billable call, and need no
credentials. No test in this plan carries the `live` marker.

**Dependencies.**

- Add no dependency to any `pyproject.toml`; `uv.lock` stays unchanged, which Task 13
  checks.
- Dependencies point from ingestion and themes to core (A §173). Core imports
  neither.

**Do not touch:**

- `AGENTS.md`: other files cite it by line number (`CLAUDE.md` §Gotchas).
- Anything under `expirements/`: the Stage 1 harness stays frozen until Stage 3
  (ADR 0001).
- Anything under `tests/fixtures/`: those are read-only inputs.
- The root `pyproject.toml`'s workspace role: it stays a virtual workspace root with
  no `[project]` table.
- `.gitignore`: this plan does not edit it, and its credentials block stays last.

**Unicode escapes.** Six test files spell their non-ASCII test characters as Python
escape sequences:

| Character | Spelled as |
| --- | --- |
| é | `\u00e9` |
| a combining acute accent | `\u0301` |
| € | `\u20ac` |
| a chart emoji | `\U0001f4c8` |
| an ellipsis | `\u2026` |
| a curly apostrophe | `\u2019` |
| a lone surrogate | `\ud800` |

The six files are `conftest.py`, `test_hashing.py`, `test_spans.py`,
`test_documents.py`, `test_locators.py` and `test_failure_classes.py`, all in
`packages/earnings-core/tests/`. Copy them exactly as written.

Some tool channels decode an escape into its literal character as they write a file.
A literal composed é and a literal decomposed é look identical but are different
strings, and a literal lone surrogate cannot be written as UTF-8 at all. So each task
that writes one of these files runs an escape check, which prints `escapes intact`.
The check flags any non-ASCII character other than `§` and `€`: citations such as
`A §193` use `§`, and two tests use a literal €.

**Writing files from this plan.** Every code block that holds a whole file follows
a line of the form ``Create `<path>`:`` or ``Replace `<path>` with:``. Once Task 1
has committed this plan, extract each file from it rather than retyping it, for two
reasons:

- Retyping about 4,000 lines of code invites silent slips.
- A tool channel that decodes escapes once will decode them again on a retry.

Run the command below from the repository root, with `<path>` replaced by the
file's path. The final argument picks which block for that path to use. It is `1`
for every file except Task 9's `conftest.py`, which is the second block for its path
and so takes `2`.

````bash
python3 - specs/plans/3-core-evidence-spine.md <path> 1 <<'PY'
import sys
from pathlib import Path

plan, target, wanted = sys.argv[1], sys.argv[2], int(sys.argv[3])
intros = (f"Create `{target}`:", f"Replace `{target}` with:")
lines = Path(plan).read_text(encoding="utf-8").splitlines(keepends=True)
found = [number for number, line in enumerate(lines) if line.strip() in intros]
if len(found) < wanted:
    sys.exit(f"{plan} has no block {wanted} for {target}")
start = next(i for i in range(found[wanted - 1] + 1, len(lines)) if lines[i].startswith("```"))
ticks = "`" * (len(lines[start]) - len(lines[start].lstrip("`")))
end = next(i for i in range(start + 1, len(lines)) if lines[i].rstrip() == ticks)
Path(target).parent.mkdir(parents=True, exist_ok=True)
Path(target).write_text("".join(lines[start + 1 : end]), encoding="utf-8")
print(f"extracted {target}: {end - start - 1} lines")
PY
````

It prints `extracted <path>: <n> lines`, and exits with an error if the plan has no
such block. If an escape check prints a file name, re-extract that file and rerun
the check. Task 1's `[tool.pytest]` table is the one block this does not cover,
because it is appended rather than written whole. It is short and has no escapes, so
type it.

**Lint.** `uv run --locked ruff check .` and `uv run --locked ruff format --check .`
pass after every task, and the code below already passes both. The Expected lines' `N files
already formatted` counts were measured on a clean checkout: 47 Python files before
Task 1, growing with each task's new files. A different count with no
`Would reformat` line comes from local untracked Python files, and is not a
failure. In test files, Ruff
sorts `earnings_core` as a third-party import, in one block with `pytest` and
`pydantic`, so keep the imports as written.

**Public repository.** `origin` (https://github.com/lowmason/earnings-themes) is
public, so everything committed is published. The tests use only synthetic text and
the already-committed fixtures.

**Commit attribution.** End each commit message with the attribution line your
session's instructions specify. The commit blocks below omit it deliberately: the
right line names the model actually executing the work.

**Commands.** Two recur:

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Before each commit, `git status --short` must list exactly the files the task names.

## Plan decisions

The roadmap entry and the specs leave these choices open, so the plan makes them.

- D-1 to D-4 are the user's decisions of 2026-09-25.
- The rest are the plan's, and the user can overturn any of them before execution.
- The code records each decision where it applies.

**D-1 — Element IDs are derived: `<type>-<start>-<end>`** (user, 2026-09-25;
Task 5).

- **Example.** `paragraph-120-450`.
- **Why.** Two producers that agree on an element's type and span give it the same
  ID, and that is what the two-parser contract test (Task 12) compares.
- **Uniqueness.** An ID is unique within one document version, and the pair
  `(doc_id, element_id)` is unique across versions.
- **Stale pointers.** A changed span is a changed ID. A stale pointer therefore
  never resolves to moved text: it is `unknown_element`.

**D-2 — Doc IDs are derived and readable** (user, 2026-09-25; Task 4).

- **Form.** `<source_document_id>@<canonicalization_version>#<first 16 hex of
  canonical_hash>`.
- **Why.** Changed text always yields a new `doc_id` (R3.3).
- **Readability.** Both named components are restricted to `[A-Za-z0-9._:-]`, so
  the derived ID reads back unambiguously.
- **Enforcement.** `document_integrity_problem` recomputes the ID on every check.

**D-3 — Rights: three statuses plus a required basis** (user, 2026-09-25; Task 3).

- **Statuses.** `RightsStatus` is one of `redistributable`, `local_only`, or
  `restricted`.
- **Basis.** `rights_basis` is a required, non-blank string naming the terms relied
  on.
- **Unclear rights.** They are recorded as `local_only`.
  `specs/point-in-time-djia-cohort.md` §Failure handling: unclear rights keep
  artifacts local and restrict export.

**D-4 — Locator context: the fewest whole words** (user, 2026-09-25; Task 7).

- **Rule.** `make_locator` grows the prefix and suffix by one whitespace-delimited
  word per side at a time, until the occurrence is unique.
- **Why.** It works like a text-quote selector, so Stage 10's text-fragment links
  can reuse it (R7.1).
- **Edges.** A word cut by the span's edge counts as one word. Text that occurs once
  gets empty context.

**D-5 — `canonicalization_version` names the whole canonicalization policy**
(Task 4).

- **The two sources.** A §490 lists "canonicalization version, schema version,
  parser version" for canonical text. A §412 records "parser version, and relevant
  configuration in a run manifest".
- **The plan's reading.** `CanonicalDocument` carries `schema_version` and
  `canonicalization_version`. The latter names the parser, rules, and normalization
  together, for example `walker-1`. The exact parser and library versions go in
  Stage 3's run manifest.
- **Left to Stage 3.** Stage 3's brainstorming chooses the naming scheme. If it wants
  a separate `parser_version` field, adding one is a schema bump.

**D-6 — The document always holds its text** (Task 4).

- **The spec's options.** The browser spec's Stage 2 section allows "immutable
  canonical text or an artifact reference".
- **The choice.** Every check is a pure function of the text, so `canonical_text` is
  required.
- **The artifact.** `text_artifact: ArtifactRef | None` optionally records where the
  same UTF-8 bytes are stored. The integrity check refuses an artifact whose hash
  differs from the text's.

**D-7 — Checks recompute; they never trust construction** (Tasks 4–9).

- **The gap.** Pydantic's `model_copy(update=...)` skips validation, so a record can
  hold a stale hash or ID.
- **The rule.** `document_integrity_problem` and the element checks recompute hashes
  and derived IDs on every call.

**D-8 — Two reporting styles** (Tasks 6, 9).

- **`validate_span`.** It runs ordered checks, each presupposing the ones before it,
  and records the first failure: one candidate, one reason.
- **`validate_elements`.** It reports every structural problem in a set at once,
  because whoever fixes a parser fixes them together.
- **Order of use.** Run `validate_elements` once before checking spans against a
  set.

**D-9 — Stage 2 enforces speaker-turn boundaries only** (Task 9).

- **Speaker turns.** A span that overlaps a speaker turn without lying inside it is
  `crosses_speaker_turn` (A §585).
- **Table cells.** R4.2's rule, that narrative evidence never contains table-cell
  text, needs Stage 3's narrative and cell classification. It is Stage 3's exit test.

**D-10 — Empty table cells are not elements** (Task 5).

- **Why.** Every element span holds text, so an empty cell has no span.
- **Grid position.** `TableCellContext.row` and `column` still count every grid
  position, including empty ones.

**D-11 — One schema version for every contract** (Task 2).

- **The version.** `SCHEMA_VERSION = 1`, typed `Literal[1]`, so a record from a newer
  version is refused, never coerced.
- **Changing it.** Any field change bumps the version, together with a compatibility
  decision and a data-dictionary update in the same change (A §187–191).

**D-12 — `storage_ref` is portable** (Task 3).

- **Accepted.** A repository-relative path or a non-file URI.
- **Refused.** An absolute path, a `~` path, a `file:` URI, or a backslash.
- **Why.** These would make identical records differ between machines (A §412–415),
  and would publish a home directory from this public repository.

**D-13 — Strict typing at every boundary** (Task 2).

- **Closed records.** Every contract is frozen and rejects extra fields.
- **Offsets.** Contracts are strict: an offset that is a bool, a float, or a numeric
  string is `malformed_record` (R3.2, A §532).
- **Python versus JSON input.** Python callers pass enum members and tuples. JSON
  input carries their values and arrays.

**D-14 — pytest configuration** (Task 1). It is a native `[tool.pytest]` table
(pytest 9):

- `--import-mode=importlib`, so members may repeat a test module's name;
- `testpaths = ["packages", "apps", "tests"]`;
- `strict = true`, which makes these errors: unknown configuration keys, unregistered
  markers, non-strict xfail, and duplicate parametrize IDs;
- the registered `live` marker.

The frozen Stage 1 harness keeps its documented `--import-mode=prepend`, which
overrides the default from the command line.

**D-15 — Stand-in parsers for the two-parser contract** (Task 12).

- **Why stand-ins.** The walker stays frozen in `expirements/` until Stage 3
  (ADR 0001), and no browser code belongs here (B1).
- **The pair.** The contract test pairs two readers:
  - a standard-library `html.parser` reader, playing the canonicalizing parser;
  - an lxml reader, playing a second extractor. It maps its blocks onto the first
    reader's `CanonicalDocument`, the sole coordinate system (B5).
- **Failures.** Text the second reader cannot place exactly is an explicit
  `ambiguous_occurrence` failure, never a first match.
- **Stage 3.** Stage 3 reruns the same contract with the ported walker and the
  DOM/layout extractor.

**D-16 — No speaker metadata yet** (Task 5).

- **What A §490 asks.** Its structure row lists "supported speaker names/roles, and
  attribution status".
- **What Stage 2 ships.** `speaker_turn` is an element type now.
- **What waits.** Role, name, and attribution status arrive with Stage 13, as a
  schema bump, once a transcript corpus exists (R2.2, R11.6).

**D-17 — No UTF-16 helper in core** (Task 2).

- **Where offsets live.** Offsets are code points everywhere in Python.
- **Where conversion belongs.** Converting to a browser's UTF-16 code units belongs
  at the browser boundary: Stage 3's capture and Stage 10's view.
- **The evidence.** `test_spans` shows the two counts differ for an emoji.

**D-18 — One mask policy version per document** (Task 10).

- **The rule.** `apply_masks` refuses masks from two policies, or two versions of
  one policy, on the same document. Every comparison period is then masked under one
  rule (A §591).
- **An empty result.** An empty mask set still records which policy ran.

**D-19 — This plan's file name and stamp** (Completion).

- **The name.** This plan is `3-core-evidence-spine.md`, not named after its parent
  spec. The retire step retires a spec whose name matches, and the parent spec must
  stay live for Stages 3–16.
- **The ID.** 3 is the next plan ID: plans 1 and 2 are in `specs/plans/completed/`.
  `specs/deferred_items.md` already has a section headed
  `3-employment-statistics-coverage`, but no plan, script, or findings file of that
  name exists on any branch here. The backlog script keys sections by their full
  name, so the two cannot collide. Every "done in plan 3" pointer this plan writes
  carries its path as well.
- **The stamp.** Stage 2 has no stage spec, so its COMPLETE stamp is appended to the
  Rollout section of `specs/evidence-linked-theme-extraction.md` (roadmap
  §Stage-spec stamp).

**D-20 — The exactness validator lives in core; the verification stage lives in
themes** (Task 9).

- **The apparent conflict.** The package table in `CLAUDE.md` gives "span
  verification" to `earnings-themes`. The README says `earnings-themes` "owns the
  domain decision to accept or reject a candidate quote".
- **Why core anyway.** The roadmap's Stage 2 entry places "an R6.1 validator with no
  tolerance parameter" in `earnings-core`. Stage 3's exit also requires that
  ingestion's canonical documents pass "the Stage 2 validator", and ingestion cannot
  import themes.
- **The split.**
  - `earnings-core` supplies the pure checks: `validate_span`, `validate_elements`,
    `resolve_pointer`, and `resolve_locator`.
  - `earnings-themes` (Stage 7) owns the verification stage that uses them:
    - calling the model;
    - bounded retries;
    - what to do with each verdict;
    - storing verified spans and rejection records (R6.2);
    - support assessment.
- **The README.** Its sentence stays true under this split, and this plan does not
  edit it.

## Requirement map

| Requirement | What closes it | Task |
| --- | --- | --- |
| R3.1 (the contract half) | `hash_canonical_text`; `CanonicalDocument` persists text, hash, and canonicalization version | 2, 4 |
| R3.2 | `TextSpan` with strict code-point offsets; failure rows `R3.2-*` | 2, 11 |
| R3.3 | derived `doc_id` and frozen records; failure rows `R3.3-*` | 4, 11 |
| R3.4 (the contract half) | `OverlayMask`, `apply_masks`; the test that a mask leaves the text and hash unchanged | 10 |
| R4.1 (the element contract) | `ElementType`, `DocumentElement`, `validate_elements` | 5, 6 |
| R4.2 (context only; see D-9) | `TableCellContext` and header references | 5, 6 |
| R5.1 (the resolution half) | `resolve_pointer` | 6 |
| R5.4 | `SpanLocator`, `make_locator`, `resolve_locator`, `ambiguous_occurrence`; failure rows `R5.4-*` | 7, 9, 11 |
| R5.5 | one contiguous range per record; failure rows `R5.5-*` | 9, 11 |
| R6.1 | `validate_span`; failure rows `R6.1-*` | 9, 11 |
| R13.2 | no tolerance parameter anywhere; failure rows `R13.2-*` | 9, 11 |
| V9, all cases but normalization and sentence splitting | see the list below | 2–11 |
| A §193 and the gap analysis's Dev tooling row | `[tool.pytest]` with `live`, importlib imports, and `testpaths` | 1 |
| A §187–191 | `SCHEMA_VERSION`, `docs/data-dictionary.md`, and its drift test | 2, 13 |
| Browser spec, Stage 2 verification | unit tests (Tasks 1–6), the two-parser contract (Task 12), and the import-boundary tests (Task 1) | 1–6, 12 |

V9's cases, and the tests that close each one:

- **Hash and offset round trips.** `test_hashing`, `test_spans`, `test_documents`,
  and failure rows `R3.2-*`.
- **Duplicated passages.** `test_locators`, `test_evidence`, and failure rows
  `R5.4-*`.
- **Invalid pointers.** `test_structure` and failure rows
  `V9-attribution-to-no-element`, `V9-pointer-to-no-element`, and
  `V9-pointer-into-another-version`.
- **Stitched spans.** Failure rows `R5.5-*`.
- **Wrong-document matches.** Failure row `R6.1-same-text-in-another-document`.
- **Chunk-to-document conversion.** `test_chunks` and failure rows
  `V9-chunk-offsets-stored-unconverted` and `V9-local-span-past-its-chunk`.
- **Speaker boundaries.** Failure rows `V9-span-crossing-speaker-turns` and
  `R6.1-wrong-speaker-turn`.
- **Canonical version changes.** `test_documents` and failure rows `R3.3-*`.
- **Unicode and whitespace normalization, and sentence splitting.** These stay with
  Stage 3, which the roadmap assigns them to.

## Human gates

| Gate | Task | Who | What it unblocks |
| --- | --- | --- | --- |
| README wording | Task 13, Step 10 | user | The README paragraphs this plan rewrites are the user's prose. Show the user the diff, and commit only wording they approve. |

Tasks 1–12 need no user input. In subagent-driven execution, the gate step runs in
the controller session with the user, never in a subagent.

## File map

`…/` below is `packages/earnings-core/src/earnings_core/`.

| Path | Responsibility | Task |
| --- | --- | --- |
| `pyproject.toml` (appended) | `[tool.pytest]`: importlib imports, `testpaths`, `strict`, the `live` marker | 1 |
| `tests/test_pytest_configuration.py` | Proves the configuration: `live` registered, deselected by `-m "not live"`, strict markers, no basename collision | 1 |
| `packages/earnings-{core,ingestion,themes}/tests/test_import_boundaries.py` | Each package imports no application, no browser, and no sibling it must not | 1 |
| `…/_model.py` | `ContractModel`, `VersionedRecord`, `SCHEMA_VERSION` | 2 |
| `…/hashing.py` | `Sha256Hex`, `sha256_hex`, `hash_canonical_text` | 2 |
| `…/spans.py` | `TextSpan` | 2 |
| `…/artifacts.py` | `ArtifactRef`, `RightsStatus` | 3 |
| `…/documents.py` | `CanonicalDocument`, `IdPart`, `derive_doc_id`, `document_integrity_problem` | 4 |
| `…/elements.py` | `ElementType`, `LEVELED_TYPES`, `TableCellContext`, `DocumentElement`, `derive_element_id` | 5 |
| `…/rejections.py` | `RejectionReason`, `Rejection`, `VALIDATOR_VERSION` | 6 |
| `…/structure.py` | `validate_elements`, `resolve_pointer` | 6 |
| `…/locators.py` | `SpanLocator`, `occurrences`, `make_locator`, `resolve_locator` | 7 |
| `…/chunks.py` | `TextChunk` | 8 |
| `…/evidence.py` | `SpanCandidate`, `VerifiedSpan`, `parse_span_candidate`, `validate_span` | 9 |
| `…/masks.py` | `MaskCategory`, `OverlayMask`, `MaskedDocument`, `apply_masks` | 10 |
| `…/__init__.py` (replaced) | The public API; `hello()` goes | 11 |
| `packages/earnings-core/tests/conftest.py` | The `sample` fixture, a small call transcript; extended in Task 9 | 6, 9 |
| `packages/earnings-core/tests/test_<module>.py` | One test file per module | 2–10 |
| `packages/earnings-core/tests/test_public_api.py`, `…/tests/test_failure_classes.py` | The public API; the Stage 2 exit table | 11 |
| `tests/contracts/test_element_schema_parsers.py` | Two readers, one element schema | 12 |
| `tests/contracts/test_gold_vocabulary.py` | Every Stage 1 gold type and level is a valid element | 12 |
| `docs/data-dictionary.md`, `tests/contracts/test_data_dictionary.py` | Every field and value documented, with a drift test | 13 |
| `CLAUDE.md`, `README.md` | The project's current state | 13 |

No other file changes. `hello()` has no caller: the README's smoke check only
imports the four packages.

## Preconditions — read before Task 1

- **Start from an up-to-date `main`.** At planning time, `main` and `origin/main`
  were both `b6dc188`. This plan file is untracked on `main` when execution starts.
  Run this and read the result:

  ```bash
  git switch main && git pull --ff-only && git status --short
  ```

  Expected: only `?? specs/plans/3-core-evidence-spine.md`.

- **Branch.** Task 1 Step 1 creates `stage-2-core-evidence-spine` with
  `git switch -c`. That carries the untracked plan onto the branch, where Task 1
  commits it first. Never commit on `main`.
- **Worktrees.** If you execute in a separate worktree (using-git-worktrees):
  1. Run Task 1 Step 1 in the main checkout. A new worktree does not see untracked
     files, so the plan must be committed first.
  2. Switch the main checkout back with `git switch main`: a branch can be checked
     out in only one worktree.
  3. Create the worktree on `stage-2-core-evidence-spine`, and continue from Task 1
     Step 2 there.
- **Environment.** `uv sync --locked --all-packages` (the `dev` group syncs by
  default). `uv --version` must print uv 0.12.15, and the interpreter is Python
  3.14.0.
- **Baseline.** Run this before Task 1:

  ```bash
  uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
  ```

  Expected: `169 passed`. No task changes that number.

- **Empty directories.** `tests/contracts/` and `tests/integration/` may exist
  locally as empty, untracked directories, since Git does not track empty
  directories. Task 12 puts the first files in `tests/contracts/`. Leave
  `tests/integration/` alone.

---

### Task 1: Branch, pytest configuration, and import boundaries

**Files:**

- Modify: `pyproject.toml` (append a `[tool.pytest]` table at the end, after
  `[tool.ruff]`)
- Create: `tests/test_pytest_configuration.py`
- Create: `packages/earnings-core/tests/test_import_boundaries.py`
- Create: `packages/earnings-ingestion/tests/test_import_boundaries.py`
- Create: `packages/earnings-themes/tests/test_import_boundaries.py`

**Interfaces:**

- Consumes: nothing.
- Produces: the root pytest configuration that every later command relies on.
  `uv run --locked --all-packages pytest packages apps tests -m "not live"`:
  - collects `packages/*/tests`, `apps/*/tests` and `tests/`;
  - imports each test module by its path, so later tasks may reuse a module name
    across members;
  - rejects unregistered markers;
  - deselects tests marked `@pytest.mark.live`.

- [ ] **Step 1: Create the branch and commit this plan**

```bash
git switch -c stage-2-core-evidence-spine
git add specs/plans/3-core-evidence-spine.md
git commit -m "docs(specs): add plan 3 for Stage 2, the core evidence spine"
git status --short
```

Expected: the last command prints nothing.

- [ ] **Step 2: Write the failing configuration tests**

Each test runs pytest in a subprocess, under the root `pyproject.toml`, against
throwaway test files in `tmp_path`. That way the tests prove the configuration
itself, not just this suite's own collection.

Create `tests/test_pytest_configuration.py`:

```python
"""The root pytest configuration: registered markers and collision-safe imports (A §193)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "pyproject.toml"


def run_pytest(*args: str) -> subprocess.CompletedProcess[str]:
    """Run pytest under the root configuration, without touching the repo's cache."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-c", str(CONFIG), "-p", "no:cacheprovider"]
        + list(args),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_live_marker_is_registered() -> None:
    result = run_pytest("--markers")
    assert result.returncode == 0, result.stderr
    assert "@pytest.mark.live:" in result.stdout


def test_not_live_deselects_live_tests(tmp_path: Path) -> None:
    (tmp_path / "test_marks.py").write_text(
        "import pytest\n"
        "\n"
        "def test_offline():\n"
        "    pass\n"
        "\n"
        "@pytest.mark.live\n"
        "def test_online():\n"
        "    raise AssertionError('a live test ran by default')\n",
        encoding="utf-8",
    )
    result = run_pytest(str(tmp_path), "-m", "not live", "-q")
    assert result.returncode == 0, result.stdout
    assert "1 passed, 1 deselected" in result.stdout


def test_unregistered_marker_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "test_typo.py").write_text(
        "import pytest\n\n@pytest.mark.lvie\ndef test_typo():\n    pass\n",
        encoding="utf-8",
    )
    result = run_pytest(str(tmp_path), "-q")
    assert result.returncode != 0
    assert "'lvie' not found in `markers`" in result.stdout


def test_same_named_test_modules_do_not_collide(tmp_path: Path) -> None:
    for member in ("first", "second"):
        tests = tmp_path / member / "tests"
        tests.mkdir(parents=True)
        (tests / "test_same_name.py").write_text(
            f"def test_{member}():\n    pass\n", encoding="utf-8"
        )
    result = run_pytest(str(tmp_path), "-q")
    assert result.returncode == 0, result.stdout
    assert "2 passed" in result.stdout
```

- [ ] **Step 3: Write the import-boundary tests**

Each test imports its package in a fresh interpreter and inspects the top-level
modules loaded. The three files share one name on purpose: they are the collision
the configuration must allow.

Create `packages/earnings-core/tests/test_import_boundaries.py`:

```python
"""earnings-core imports no sibling package, the application, or a browser (A §173; B2)."""

import json
import subprocess
import sys

FORBIDDEN = {
    "earnings_ingestion",
    "earnings_themes",
    "earnings_pipeline",
    "selenium",
    "playwright",
    "pyppeteer",
}


def modules_loaded_by(module: str) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing ``module``."""
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return {name.partition(".")[0] for name in json.loads(result.stdout)}


def test_importing_earnings_core_loads_nothing_forbidden() -> None:
    assert modules_loaded_by("earnings_core") & FORBIDDEN == set()
```

Create `packages/earnings-ingestion/tests/test_import_boundaries.py`:

```python
"""earnings-ingestion imports neither earnings-themes nor the application, and no
browser: browser capture stays behind an optional extra (A §173; B3)."""

import json
import subprocess
import sys

FORBIDDEN = {
    "earnings_themes",
    "earnings_pipeline",
    "selenium",
    "playwright",
    "pyppeteer",
}


def modules_loaded_by(module: str) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing ``module``."""
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return {name.partition(".")[0] for name in json.loads(result.stdout)}


def test_importing_earnings_ingestion_loads_nothing_forbidden() -> None:
    assert modules_loaded_by("earnings_ingestion") & FORBIDDEN == set()
```

Create `packages/earnings-themes/tests/test_import_boundaries.py`:

```python
"""earnings-themes imports neither earnings-ingestion nor the application, and no
browser (A §173; browser-rendering spec, Stage 2 verification)."""

import json
import subprocess
import sys

FORBIDDEN = {
    "earnings_ingestion",
    "earnings_pipeline",
    "selenium",
    "playwright",
    "pyppeteer",
}


def modules_loaded_by(module: str) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing ``module``."""
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return {name.partition(".")[0] for name in json.loads(result.stdout)}


def test_importing_earnings_themes_loads_nothing_forbidden() -> None:
    assert modules_loaded_by("earnings_themes") & FORBIDDEN == set()
```

- [ ] **Step 4: Run the new tests to verify they fail**

```bash
uv run --locked --all-packages pytest tests/test_pytest_configuration.py -q
```

Expected: exit 1, `3 failed, 1 passed`:

```
FAILED tests/test_pytest_configuration.py::test_live_marker_is_registered - A...
FAILED tests/test_pytest_configuration.py::test_unregistered_marker_is_an_error
FAILED tests/test_pytest_configuration.py::test_same_named_test_modules_do_not_collide
```

`test_not_live_deselects_live_tests` already passes: `-m "not live"` deselects by
name even when the marker is unregistered. Registering the marker is what turns a
misspelled marker into an error.

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests packages/earnings-ingestion/tests packages/earnings-themes/tests -q
```

Expected: exit 2, `2 errors`. Each is an `import file mismatch`, one for
`packages/earnings-ingestion/tests/test_import_boundaries.py` and one for
`packages/earnings-themes/tests/test_import_boundaries.py`. pytest's default
`prepend` import mode loads all three files as one module named
`test_import_boundaries`.

- [ ] **Step 5: Append the pytest configuration**

Append this block to the end of `pyproject.toml`, after the `[tool.ruff]` table and
one blank line. Change nothing else in the file, and add no `[project]` table.

```toml
[tool.pytest]
# A §193: collect package, application, and shared tests; keep same-named test modules
# in different members from colliding; make live checks opt-in.
# importlib mode imports each test file by its path, so packages/*/tests/test_x.py can
# repeat a basename. The frozen Stage 1 harness imports its modules by bare name and
# still needs prepend mode: its documented command passes --import-mode=prepend, which
# overrides this default.
addopts = ["--import-mode=importlib"]
testpaths = ["packages", "apps", "tests"]
# strict: unknown config keys, unregistered markers, non-strict xfail, and duplicate
# parametrize IDs are errors.
strict = true
markers = [
    "live: needs the network, credentials, or a billable service; run only with -m live",
]
```

- [ ] **Step 6: Run the suite and the harness to verify they pass**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
```

Expected: `7 passed`.

```bash
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
```

Expected: `169 passed`. The harness is untouched: its command-line
`--import-mode=prepend` overrides the new default.

- [ ] **Step 7: Lint**

```bash
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `All checks passed!` and `51 files already formatted`. The count covers
every Python file Ruff sees; each later task states its own.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml tests/test_pytest_configuration.py packages/earnings-core/tests/test_import_boundaries.py packages/earnings-ingestion/tests/test_import_boundaries.py packages/earnings-themes/tests/test_import_boundaries.py
git commit -m "test: configure pytest with a registered live marker and importlib imports"
```

---

### Task 2: Contract base, SHA-256 helpers, and TextSpan

**Files:**

- Create: `packages/earnings-core/src/earnings_core/_model.py`
- Create: `packages/earnings-core/src/earnings_core/hashing.py`
- Create: `packages/earnings-core/src/earnings_core/spans.py`
- Test: `packages/earnings-core/tests/test_hashing.py`
- Test: `packages/earnings-core/tests/test_spans.py`

**Interfaces:**

- Consumes: Task 1's pytest configuration.
- Produces, in `earnings_core._model`:
  - `SCHEMA_VERSION = 1`.
  - `class ContractModel(pydantic.BaseModel)`, with
    `model_config = ConfigDict(frozen=True, extra="forbid", strict=True)`.
  - `class VersionedRecord(ContractModel)`, which adds
    `schema_version: Literal[1] = SCHEMA_VERSION`.
  - Every later record subclasses one of the two: `VersionedRecord` for top-level
    records, `ContractModel` for values nested inside them.
- Produces, in `earnings_core.hashing`:
  - `Sha256Hex`, an `Annotated[str, ...]` matching `^[0-9a-f]{64}$`.
  - `sha256_hex(data: bytes) -> str`.
  - `hash_canonical_text(canonical_text: str) -> str`, which raises
    `UnicodeEncodeError` on a lone surrogate.
- Produces, in `earnings_core.spans`: `class TextSpan(ContractModel)`.
  - Fields: `start: NonNegativeInt` and `end: NonNegativeInt`, with `start < end`,
    else a `ValidationError`.
  - The property `length -> int`.
  - `contains(other: TextSpan) -> bool`: equal spans contain each other.
  - `overlaps(other: TextSpan) -> bool`.
  - `slice_of(text: str) -> str`, which raises `ValueError` rather than truncate when
    the span runs past `text`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-core/tests/test_hashing.py`:

```python
import hashlib

import pytest
from earnings_core.hashing import hash_canonical_text, sha256_hex


def test_sha256_hex_matches_the_published_test_vector() -> None:
    # FIPS 180-2, appendix B.1: SHA-256("abc").
    assert (
        sha256_hex(b"abc")
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_canonical_hash_is_sha256_of_the_utf8_bytes() -> None:
    text = "Revenue rose 5% to \u20ac2.1 billion \U0001f4c8 at the caf\u00e9."
    assert hash_canonical_text(text) == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_canonical_hash_differs_for_composed_and_decomposed_accents() -> None:
    composed = "caf\u00e9"
    decomposed = "cafe\u0301"
    assert hash_canonical_text(composed) != hash_canonical_text(decomposed)


def test_a_lone_surrogate_cannot_be_hashed() -> None:
    with pytest.raises(UnicodeEncodeError):
        hash_canonical_text("broken \ud800 text")
```

Create `packages/earnings-core/tests/test_spans.py`:

```python
import pytest
from earnings_core.spans import TextSpan
from pydantic import ValidationError


def test_a_span_is_half_open() -> None:
    span = TextSpan(start=2, end=5)
    assert span.slice_of("abcdefg") == "cde"
    assert span.length == 3


@pytest.mark.parametrize(
    ("start", "end"),
    [(True, 5), (1.0, 5), ("1", 5), (1, 5.0), (-1, 5)],
    ids=["bool", "float", "numeric-string", "float-end", "negative"],
)
def test_offsets_are_strict_non_negative_integers(start: object, end: object) -> None:
    with pytest.raises(ValidationError):
        TextSpan(start=start, end=end)


@pytest.mark.parametrize(("start", "end"), [(3, 3), (5, 2)], ids=["empty", "reversed"])
def test_a_span_is_never_empty_or_reversed(start: int, end: int) -> None:
    with pytest.raises(ValidationError, match="empty or reversed"):
        TextSpan(start=start, end=end)


def test_offsets_count_code_points_not_bytes_or_utf16_units() -> None:
    text = "Up \U0001f4c8 at the caf\u00e9"
    span = TextSpan(start=text.index("at"), end=text.index("at") + 2)
    assert span.slice_of(text) == "at"
    utf8_start = text.encode("utf-8").index(b"at")
    utf16_start = text.encode("utf-16-le").index("at".encode("utf-16-le")) // 2
    assert utf8_start != span.start
    assert utf16_start != span.start


def test_slicing_past_the_text_raises_rather_than_truncates() -> None:
    with pytest.raises(ValueError, match="runs past"):
        TextSpan(start=2, end=9).slice_of("abc")


def test_containment_and_overlap() -> None:
    outer = TextSpan(start=0, end=10)
    inner = TextSpan(start=2, end=5)
    crossing = TextSpan(start=8, end=12)
    after = TextSpan(start=10, end=12)
    assert outer.contains(inner)
    assert outer.contains(outer)
    assert not inner.contains(outer)
    assert outer.overlaps(crossing)
    assert not outer.contains(crossing)
    assert not outer.overlaps(after)


def test_a_span_is_immutable_and_round_trips_through_json() -> None:
    span = TextSpan(start=4, end=9)
    with pytest.raises(ValidationError):
        span.start = 0
    assert TextSpan.model_validate_json(span.model_dump_json()) == span
```

Run the escape check (Global Constraints):

```bash
python3 -c 'import sys; bad = {p: sorted({hex(ord(c)) for c in open(p, encoding="utf-8").read() if ord(c) > 127} - {"0xa7", "0x20ac"}) for p in sys.argv[1:]}; print({p: b for p, b in bad.items() if b} or "escapes intact")' packages/earnings-core/tests/test_hashing.py packages/earnings-core/tests/test_spans.py
```

Expected: `escapes intact`. If it prints a file name instead, re-extract that file
(Global Constraints, "Writing files from this plan") and rerun the check.

- [ ] **Step 2: Run them to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_hashing.py packages/earnings-core/tests/test_spans.py -q
```

Expected: exit 2, `2 errors`, with
`ModuleNotFoundError: No module named 'earnings_core.hashing'` and
`ModuleNotFoundError: No module named 'earnings_core.spans'`.

- [ ] **Step 3: Write the implementation**

The leading underscore marks `_model.py` as private: Task 11 re-exports
`SCHEMA_VERSION` from the package root.

Create `packages/earnings-core/src/earnings_core/_model.py`:

```python
"""The base classes every earnings-core contract shares."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

SCHEMA_VERSION = 1
"""The version of every earnings-core contract; any field change bumps it (A §187)."""


class ContractModel(BaseModel):
    """Immutable, closed, strictly typed: a contract never coerces a value or grows a field.

    Strict mode rejects a bool, a float, or a numeric string where an integer belongs
    (A §532). ``model_copy(update=...)`` skips validation, so the validators recheck
    every stored invariant instead of trusting construction.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class VersionedRecord(ContractModel):
    """A top-level record that carries its schema version when serialized."""

    schema_version: Literal[1] = SCHEMA_VERSION
```

Create `packages/earnings-core/src/earnings_core/hashing.py`:

```python
"""SHA-256 helpers: the one hash every contract uses."""

import hashlib
from typing import Annotated

from pydantic import StringConstraints

Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
"""A SHA-256 digest written as 64 lowercase hexadecimal characters."""


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 digest of ``data`` as 64 lowercase hexadecimal characters."""
    return hashlib.sha256(data).hexdigest()


def hash_canonical_text(canonical_text: str) -> str:
    """Hash canonical text as R3.1 defines it: SHA-256 over its UTF-8 bytes.

    Raises ``UnicodeEncodeError`` if the text holds a lone surrogate, which has no
    UTF-8 encoding and so can never be canonical text.
    """
    return sha256_hex(canonical_text.encode("utf-8"))
```

Create `packages/earnings-core/src/earnings_core/spans.py`:

```python
"""TextSpan: a half-open range of Unicode code points in one canonical text (R3.2)."""

from typing import Self

from pydantic import NonNegativeInt, model_validator

from earnings_core._model import ContractModel


class TextSpan(ContractModel):
    """Zero-based, half-open ``[start, end)`` code-point offsets; never empty.

    Offsets index a Python ``str``, so they count code points: not UTF-8 bytes, not
    UTF-16 code units, and not model tokens (A §505, R3.2).
    """

    start: NonNegativeInt
    end: NonNegativeInt

    @model_validator(mode="after")
    def _start_before_end(self) -> Self:
        if self.start >= self.end:
            raise ValueError(f"span [{self.start}, {self.end}) is empty or reversed")
        return self

    @property
    def length(self) -> int:
        return self.end - self.start

    def contains(self, other: "TextSpan") -> bool:
        """True when ``other`` lies wholly inside this span; equal spans contain each other."""
        return self.start <= other.start and other.end <= self.end

    def overlaps(self, other: "TextSpan") -> bool:
        """True when the two spans share at least one code point."""
        return self.start < other.end and other.start < self.end

    def slice_of(self, text: str) -> str:
        """The spanned characters of ``text``; raises rather than truncate a short text."""
        if self.end > len(text):
            raise ValueError(
                f"span [{self.start}, {self.end}) runs past a text of length {len(text)}"
            )
        return text[self.start : self.end]
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_hashing.py packages/earnings-core/tests/test_spans.py -q
```

Expected: `16 passed`.

- [ ] **Step 5: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `23 passed`; `All checks passed!`; `56 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git add packages/earnings-core/src/earnings_core/_model.py packages/earnings-core/src/earnings_core/hashing.py packages/earnings-core/src/earnings_core/spans.py packages/earnings-core/tests/test_hashing.py packages/earnings-core/tests/test_spans.py
git commit -m "feat(core): add the contract base, SHA-256 helpers, and TextSpan"
```

---

### Task 3: ArtifactRef and rights status

**Files:**

- Create: `packages/earnings-core/src/earnings_core/artifacts.py`
- Test: `packages/earnings-core/tests/test_artifacts.py`

**Interfaces:**

- Consumes: `VersionedRecord` (Task 2); `Sha256Hex` and `sha256_hex` (Task 2).
- Produces, in `earnings_core.artifacts`:
  - The annotated string types `NonBlankStr` and `MediaType`.
  - `class RightsStatus(StrEnum)`, with members `REDISTRIBUTABLE = "redistributable"`,
    `LOCAL_ONLY = "local_only"`, and `RESTRICTED = "restricted"` (D-3).
  - `class ArtifactRef(VersionedRecord)`, with these fields:
    - `content_sha256: Sha256Hex`;
    - `media_type: MediaType`;
    - `storage_ref: NonBlankStr`, which must be portable (D-12);
    - `rights_status: RightsStatus`;
    - `rights_basis: NonBlankStr`.
  - The classmethod
    `ArtifactRef.for_bytes(data: bytes, *, media_type: str, storage_ref: str, rights_status: RightsStatus, rights_basis: str) -> ArtifactRef`.
  - `ArtifactRef.matches(data: bytes) -> bool`.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-core/tests/test_artifacts.py`:

```python
import pytest
from earnings_core.artifacts import ArtifactRef, RightsStatus
from earnings_core.hashing import sha256_hex
from pydantic import ValidationError

BASIS = "docs/source-register.toml entry sec-edgar"


def make_ref(**changes: object) -> ArtifactRef:
    fields: dict[str, object] = {
        "content_sha256": sha256_hex(b"<html></html>"),
        "media_type": "text/html",
        "storage_ref": "data/raw/example/source.html",
        "rights_status": RightsStatus.LOCAL_ONLY,
        "rights_basis": BASIS,
    }
    fields.update(changes)
    return ArtifactRef(**fields)


def test_for_bytes_records_the_sha256_of_the_content() -> None:
    data = "Revenue rose 5% to €2.1 billion.".encode()
    ref = ArtifactRef.for_bytes(
        data,
        media_type="text/plain; charset=utf-8",
        storage_ref="data/canonical/example.txt",
        rights_status=RightsStatus.REDISTRIBUTABLE,
        rights_basis=BASIS,
    )
    assert ref.content_sha256 == sha256_hex(data)
    assert ref.matches(data)


def test_a_one_byte_change_no_longer_matches() -> None:
    ref = make_ref()
    assert ref.matches(b"<html></html>")
    assert not ref.matches(b"<html> </html>")


@pytest.mark.parametrize(
    "digest",
    ["A" * 64, "a" * 63, "g" * 64, "sha256:" + "a" * 64],
    ids=["uppercase", "short", "not-hex", "prefixed"],
)
def test_a_digest_must_be_64_lowercase_hex_characters(digest: str) -> None:
    with pytest.raises(ValidationError):
        make_ref(content_sha256=digest)


@pytest.mark.parametrize(
    "storage_ref",
    ["/Users/someone/data/raw/x.html", "~/data/x.html", "file:///tmp/x.html", "a\\b"],
    ids=["absolute", "home", "file-uri", "backslash"],
)
def test_storage_ref_must_be_portable(storage_ref: str) -> None:
    with pytest.raises(ValidationError, match="repository-relative"):
        make_ref(storage_ref=storage_ref)


@pytest.mark.parametrize(
    "media_type", ["html", "Text/HTML", "text/html;charset"], ids=str
)
def test_media_type_must_be_well_formed(media_type: str) -> None:
    with pytest.raises(ValidationError):
        make_ref(media_type=media_type)


def test_rights_basis_may_not_be_blank() -> None:
    with pytest.raises(ValidationError):
        make_ref(rights_basis="   ")


def test_rights_status_takes_the_enum_in_python_and_its_value_in_json() -> None:
    with pytest.raises(ValidationError):
        make_ref(rights_status="local_only")
    ref = make_ref(rights_status=RightsStatus.RESTRICTED)
    assert '"rights_status":"restricted"' in ref.model_dump_json()
    assert ArtifactRef.model_validate_json(ref.model_dump_json()) == ref


def test_a_newer_schema_version_is_refused() -> None:
    payload = (
        make_ref().model_dump_json().replace('"schema_version":1', '"schema_version":2')
    )
    with pytest.raises(ValidationError):
        ArtifactRef.model_validate_json(payload)
```

- [ ] **Step 2: Run them to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_artifacts.py -q
```

Expected: exit 2, `1 error`, with
`ModuleNotFoundError: No module named 'earnings_core.artifacts'`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-core/src/earnings_core/artifacts.py`:

```python
"""ArtifactRef: a content-addressed pointer to a stored artifact and its rights."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import StringConstraints, field_validator

from earnings_core._model import VersionedRecord
from earnings_core.hashing import Sha256Hex, sha256_hex

NonBlankStr = Annotated[str, StringConstraints(pattern=r"\S")]
"""A string holding at least one non-whitespace character."""

MediaType = Annotated[
    str,
    StringConstraints(
        pattern=r"^[a-z0-9.+-]+/[a-z0-9.+-]+(; ?[a-z0-9-]+=[A-Za-z0-9._-]+)*$"
    ),
]
"""A lowercase media type with optional parameters, e.g. ``text/plain; charset=utf-8``."""


class RightsStatus(StrEnum):
    """What may be done with an artifact's content (A §58, A §242, R2.1).

    Record unclear rights as ``LOCAL_ONLY``: they keep an artifact local and restrict
    its export (specs/point-in-time-djia-cohort.md, §Failure handling).
    """

    REDISTRIBUTABLE = "redistributable"
    """A recorded basis permits committing and exporting the content."""
    LOCAL_ONLY = "local_only"
    """Retain locally for processing; never commit or export the content."""
    RESTRICTED = "restricted"
    """Terms forbid redistributing the text; keep locators and local features (R2.1)."""


class ArtifactRef(VersionedRecord):
    """A stored artifact, identified by the SHA-256 of its bytes.

    ``storage_ref`` is a repository-relative path or a non-file URI. An absolute local
    path would make otherwise identical records differ between machines (A §413) and
    would publish a home directory from this public repository.
    """

    content_sha256: Sha256Hex
    media_type: MediaType
    storage_ref: NonBlankStr
    rights_status: RightsStatus
    rights_basis: NonBlankStr

    @field_validator("storage_ref")
    @classmethod
    def _portable(cls, value: str) -> str:
        if value.startswith(("/", "~", "file:")) or "\\" in value:
            raise ValueError(
                f"storage_ref {value!r} must be a repository-relative path"
                " or a non-file URI"
            )
        return value

    @classmethod
    def for_bytes(
        cls,
        data: bytes,
        *,
        media_type: str,
        storage_ref: str,
        rights_status: RightsStatus,
        rights_basis: str,
    ) -> Self:
        """The reference for ``data``, with its SHA-256 computed here."""
        return cls(
            content_sha256=sha256_hex(data),
            media_type=media_type,
            storage_ref=storage_ref,
            rights_status=rights_status,
            rights_basis=rights_basis,
        )

    def matches(self, data: bytes) -> bool:
        """True when ``data`` is exactly the artifact this reference names."""
        return sha256_hex(data) == self.content_sha256
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_artifacts.py -q
```

Expected: `16 passed`.

- [ ] **Step 5: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `39 passed`; `All checks passed!`; `58 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git add packages/earnings-core/src/earnings_core/artifacts.py packages/earnings-core/tests/test_artifacts.py
git commit -m "feat(core): add ArtifactRef with a rights status and basis"
```

---

### Task 4: CanonicalDocument

**Files:**

- Create: `packages/earnings-core/src/earnings_core/documents.py`
- Test: `packages/earnings-core/tests/test_documents.py`

**Interfaces:**

- Consumes: `VersionedRecord`, `Sha256Hex` and `hash_canonical_text` (Task 2);
  `ArtifactRef` (Task 3).
- Produces, in `earnings_core.documents`:
  - `IdPart`, an annotated string matching `^[A-Za-z0-9._:-]+$`.
  - `derive_doc_id(source_document_id: str, canonicalization_version: str, canonical_hash: str) -> str`
    (D-2).
  - `class CanonicalDocument(VersionedRecord)`, with these fields:
    - `doc_id: str`;
    - `source_document_id: IdPart`;
    - `canonicalization_version: IdPart`;
    - `canonical_text: str`, at least one character;
    - `canonical_hash: Sha256Hex`;
    - `text_artifact: ArtifactRef | None = None`.
  - The classmethod
    `CanonicalDocument.create(*, source_document_id: str, canonicalization_version: str, canonical_text: str, text_artifact: ArtifactRef | None = None) -> CanonicalDocument`.
    It derives `canonical_hash` and `doc_id`, and raises `ValueError` if the text
    holds a lone surrogate.
  - `document_integrity_problem(document: CanonicalDocument) -> str | None`. It
    recomputes the hash, the `doc_id`, and the artifact match (D-7), then returns the
    first problem, or `None`. Every later check calls it first.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-core/tests/test_documents.py`:

```python
import pytest
from earnings_core.artifacts import ArtifactRef, RightsStatus
from earnings_core.documents import (
    CanonicalDocument,
    derive_doc_id,
    document_integrity_problem,
)
from earnings_core.hashing import hash_canonical_text
from pydantic import ValidationError

TEXT = "Acme reports third-quarter results.\nRevenue rose 5% to €2.1 billion."


def make_document(text: str = TEXT, **changes: object) -> CanonicalDocument:
    fields: dict[str, object] = {
        "source_document_id": "0000007332-09-000032_ex-99",
        "canonicalization_version": "walker-w16.norm-1",
        "canonical_text": text,
    }
    fields.update(changes)
    return CanonicalDocument.create(**fields)


def test_create_derives_the_hash_and_the_doc_id() -> None:
    document = make_document()
    assert document.canonical_hash == hash_canonical_text(TEXT)
    assert document.doc_id == (
        "0000007332-09-000032_ex-99@walker-w16.norm-1#" + hash_canonical_text(TEXT)[:16]
    )
    assert document_integrity_problem(document) is None


def test_changed_text_is_a_new_version() -> None:
    first = make_document()
    second = make_document(TEXT.replace("5%", "6%"))
    assert second.canonical_hash != first.canonical_hash
    assert second.doc_id != first.doc_id
    assert second.source_document_id == first.source_document_id


def test_text_cannot_be_mutated_in_place() -> None:
    document = make_document()
    with pytest.raises(ValidationError):
        document.canonical_text = "Revenue fell."


def test_new_text_under_an_old_doc_id_is_refused() -> None:
    first = make_document()
    changed = TEXT.replace("5%", "6%")
    with pytest.raises(ValidationError, match="is not the derived"):
        CanonicalDocument(
            doc_id=first.doc_id,
            source_document_id=first.source_document_id,
            canonicalization_version=first.canonicalization_version,
            canonical_text=changed,
            canonical_hash=hash_canonical_text(changed),
        )


def test_a_hash_that_is_not_the_texts_is_refused() -> None:
    first = make_document()
    with pytest.raises(ValidationError, match="is not the text's SHA-256"):
        CanonicalDocument(
            doc_id=first.doc_id,
            source_document_id=first.source_document_id,
            canonicalization_version=first.canonicalization_version,
            canonical_text=TEXT + " ",
            canonical_hash=first.canonical_hash,
        )


def test_a_copy_that_skips_validation_is_still_caught() -> None:
    tampered = make_document().model_copy(update={"canonical_text": "Revenue fell."})
    problem = document_integrity_problem(tampered)
    assert problem is not None
    assert "is not the text's SHA-256" in problem


@pytest.mark.parametrize("text", ["", "broken \ud800 text"], ids=["empty", "surrogate"])
def test_empty_or_unencodable_text_is_not_canonical(text: str) -> None:
    with pytest.raises(ValueError):
        make_document(text)


@pytest.mark.parametrize(
    "part", ["0000007332 09", "walker/w16", "a@b", "a#b", ""], ids=str
)
def test_id_parts_are_restricted_so_a_derived_id_reads_back(part: str) -> None:
    with pytest.raises(ValidationError):
        make_document(source_document_id=part)


def test_derive_doc_id_is_a_pure_function() -> None:
    digest = hash_canonical_text(TEXT)
    assert derive_doc_id("s", "v", digest) == derive_doc_id("s", "v", digest)
    assert derive_doc_id("s", "v", digest) == f"s@v#{digest[:16]}"


def test_a_text_artifact_must_hold_exactly_the_canonical_bytes() -> None:
    stored = ArtifactRef.for_bytes(
        TEXT.encode(),
        media_type="text/plain; charset=utf-8",
        storage_ref="data/canonical/example.txt",
        rights_status=RightsStatus.LOCAL_ONLY,
        rights_basis="docs/source-register.toml entry sec-edgar",
    )
    assert make_document(text_artifact=stored).text_artifact == stored
    stale = stored.model_copy(
        update={"content_sha256": hash_canonical_text(TEXT + ".")}
    )
    with pytest.raises(ValidationError, match="holds other bytes"):
        make_document(text_artifact=stale)


def test_a_document_round_trips_through_json() -> None:
    document = make_document()
    restored = CanonicalDocument.model_validate_json(document.model_dump_json())
    assert restored == document
    assert document_integrity_problem(restored) is None
```

Run the escape check:

```bash
python3 -c 'import sys; bad = {p: sorted({hex(ord(c)) for c in open(p, encoding="utf-8").read() if ord(c) > 127} - {"0xa7", "0x20ac"}) for p in sys.argv[1:]}; print({p: b for p, b in bad.items() if b} or "escapes intact")' packages/earnings-core/tests/test_documents.py
```

Expected: `escapes intact`. If it prints a file name instead, re-extract that file
(Global Constraints, "Writing files from this plan") and rerun the check.

- [ ] **Step 2: Run them to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_documents.py -q
```

Expected: exit 2, `1 error`, with
`ModuleNotFoundError: No module named 'earnings_core.documents'`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-core/src/earnings_core/documents.py`:

```python
"""CanonicalDocument: one immutable, hashed version of a source document's text."""

from typing import Annotated, Self

from pydantic import StringConstraints, model_validator

from earnings_core._model import VersionedRecord
from earnings_core.artifacts import ArtifactRef
from earnings_core.hashing import Sha256Hex, hash_canonical_text

IdPart = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9._:-]+$")]
"""One component of a derived identifier: letters, digits, and ``. _ : -`` only."""


def derive_doc_id(
    source_document_id: str, canonicalization_version: str, canonical_hash: str
) -> str:
    """The ID of one canonical version of a source document.

    It embeds the first 16 hex characters of the canonical hash, so changed text is
    always a new ``doc_id`` (R3.3). Plan decision, 2026-09-25: derived and readable.
    """
    return f"{source_document_id}@{canonicalization_version}#{canonical_hash[:16]}"


class CanonicalDocument(VersionedRecord):
    """Canonical text, its SHA-256, and the version that produced it (R3.1, R3.3).

    ``canonicalization_version`` names the whole policy (parser, rules, and
    normalization); parser and library versions belong to Stage 3's run manifest.
    The text is always held here, because the validators are pure functions of it;
    ``text_artifact`` optionally records where the same UTF-8 bytes are stored.
    """

    doc_id: str
    source_document_id: IdPart
    canonicalization_version: IdPart
    canonical_text: Annotated[str, StringConstraints(min_length=1)]
    canonical_hash: Sha256Hex
    text_artifact: ArtifactRef | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        problem = document_integrity_problem(self)
        if problem is not None:
            raise ValueError(problem)
        return self

    @classmethod
    def create(
        cls,
        *,
        source_document_id: str,
        canonicalization_version: str,
        canonical_text: str,
        text_artifact: ArtifactRef | None = None,
    ) -> Self:
        """Build a version from its text, deriving ``canonical_hash`` and ``doc_id``."""
        try:
            canonical_hash = hash_canonical_text(canonical_text)
        except UnicodeEncodeError as error:
            raise ValueError(
                "canonical text holds a lone surrogate and has no UTF-8 encoding"
            ) from error
        return cls(
            doc_id=derive_doc_id(
                source_document_id, canonicalization_version, canonical_hash
            ),
            source_document_id=source_document_id,
            canonicalization_version=canonicalization_version,
            canonical_text=canonical_text,
            canonical_hash=canonical_hash,
            text_artifact=text_artifact,
        )


def document_integrity_problem(document: CanonicalDocument) -> str | None:
    """Recheck a document's stored hash and ``doc_id`` against its text (R6.1, R3.3).

    Validators call this rather than trust construction, because
    ``model_copy(update=...)`` skips validation. Returns ``None`` when consistent.
    """
    if not document.canonical_text:
        return "canonical text is empty"
    try:
        actual = hash_canonical_text(document.canonical_text)
    except UnicodeEncodeError:
        return "canonical text holds a lone surrogate and has no UTF-8 encoding"
    if actual != document.canonical_hash:
        return (
            f"stored canonical_hash {document.canonical_hash} is not the text's"
            f" SHA-256 {actual}"
        )
    expected = derive_doc_id(
        document.source_document_id, document.canonicalization_version, actual
    )
    if document.doc_id != expected:
        return f"doc_id {document.doc_id!r} is not the derived {expected!r}"
    artifact = document.text_artifact
    if artifact is not None and artifact.content_sha256 != actual:
        return (
            f"text_artifact {artifact.storage_ref!r} holds other bytes"
            f" (SHA-256 {artifact.content_sha256})"
        )
    return None
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_documents.py -q
```

Expected: `16 passed`.

- [ ] **Step 5: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `55 passed`; `All checks passed!`; `60 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git add packages/earnings-core/src/earnings_core/documents.py packages/earnings-core/tests/test_documents.py
git commit -m "feat(core): add CanonicalDocument with derived doc IDs"
```

---

### Task 5: DocumentElement

**Files:**

- Create: `packages/earnings-core/src/earnings_core/elements.py`
- Test: `packages/earnings-core/tests/test_elements.py`

**Interfaces:**

- Consumes: `ContractModel`, `VersionedRecord` and `TextSpan` (Task 2);
  `CanonicalDocument` (Task 4).
- Produces, in `earnings_core.elements`:
  - `class ElementType(StrEnum)`, with the values `section`, `heading`, `paragraph`,
    `list_item`, `sentence`, `footnote`, `table`, `table_cell`, `speaker_turn`,
    `page_artifact`, and `other`.
  - `LEVELED_TYPES = frozenset({ElementType.SECTION, ElementType.HEADING, ElementType.LIST_ITEM})`.
  - `class TableCellContext(ContractModel)`, with these fields:
    - `row: NonNegativeInt` and `column: NonNegativeInt`;
    - `row_span: PositiveInt = 1` and `column_span: PositiveInt = 1`;
    - `is_header: bool`;
    - `header_cell_ids: tuple[str, ...] = ()`.
  - `derive_element_id(element_type: ElementType, span: TextSpan) -> str` (D-1).
  - `class DocumentElement(VersionedRecord)`, with these fields:
    - `element_id: str` and `doc_id: str`;
    - `type: ElementType`;
    - `span: TextSpan`;
    - `parent_id: str | None = None`;
    - `level: PositiveInt | None = None`;
    - `table_cell: TableCellContext | None = None`;
    - `source_type: str = ""`.
  - The classmethod
    `DocumentElement.create(document: CanonicalDocument, element_type: ElementType, span: TextSpan, *, parent_id: str | None = None, level: int | None = None, table_cell: TableCellContext | None = None, source_type: str = "") -> DocumentElement`.
- Rules one record enforces by itself:
  - its ID is the derived one;
  - it is not its own parent;
  - a level appears only on `LEVELED_TYPES`, and a heading may have none;
  - table-cell context appears exactly on table cells.
- Rules that need the whole set are Task 6's:
  - parents exist, precede their children, and contain them;
  - spans nest;
  - cells sit in tables;
  - header references are valid.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-core/tests/test_elements.py`:

```python
import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.elements import (
    DocumentElement,
    ElementType,
    TableCellContext,
    derive_element_id,
)
from earnings_core.spans import TextSpan
from pydantic import ValidationError

DOCUMENT = CanonicalDocument.create(
    source_document_id="elements-test",
    canonicalization_version="test-1",
    canonical_text="Results\nRevenue rose.\nMetric\tQ3",
)
HEADING = TextSpan(start=0, end=7)
CELL = TextSpan(start=22, end=28)


def test_the_id_is_derived_from_type_and_span() -> None:
    element = DocumentElement.create(DOCUMENT, ElementType.HEADING, HEADING, level=1)
    assert element.element_id == "heading-0-7"
    assert element.element_id == derive_element_id(ElementType.HEADING, HEADING)
    assert element.doc_id == DOCUMENT.doc_id


def test_the_same_type_and_span_give_the_same_id_from_any_producer() -> None:
    first = DocumentElement.create(
        DOCUMENT, ElementType.HEADING, HEADING, source_type="lxml:h1"
    )
    second = DocumentElement.create(
        DOCUMENT, ElementType.HEADING, HEADING, source_type="html.parser:h1"
    )
    assert first.element_id == second.element_id
    assert first.source_type != second.source_type


def test_an_id_that_is_not_derived_is_refused() -> None:
    with pytest.raises(ValidationError, match="is not the derived"):
        DocumentElement(
            element_id="h1",
            doc_id=DOCUMENT.doc_id,
            type=ElementType.HEADING,
            span=HEADING,
        )


@pytest.mark.parametrize(
    "element_type", [ElementType.PARAGRAPH, ElementType.TABLE, ElementType.FOOTNOTE]
)
def test_only_sections_headings_and_list_items_carry_a_level(
    element_type: ElementType,
) -> None:
    with pytest.raises(ValidationError, match="carries no level"):
        DocumentElement.create(DOCUMENT, element_type, HEADING, level=1)


def test_a_heading_may_have_no_level() -> None:
    element = DocumentElement.create(DOCUMENT, ElementType.HEADING, HEADING)
    assert element.level is None


def test_a_table_cell_requires_its_context() -> None:
    with pytest.raises(ValidationError, match="required on table cells"):
        DocumentElement.create(DOCUMENT, ElementType.TABLE_CELL, CELL)


def test_only_a_table_cell_takes_table_context() -> None:
    context = TableCellContext(row=0, column=0, is_header=True)
    with pytest.raises(ValidationError, match="forbidden elsewhere"):
        DocumentElement.create(
            DOCUMENT, ElementType.PARAGRAPH, CELL, table_cell=context
        )


def test_a_table_cell_records_its_grid_position_and_headers() -> None:
    context = TableCellContext(
        row=1, column=2, is_header=False, header_cell_ids=("table_cell-22-28",)
    )
    cell = DocumentElement.create(
        DOCUMENT, ElementType.TABLE_CELL, TextSpan(start=29, end=31), table_cell=context
    )
    assert cell.table_cell == context
    assert (context.row_span, context.column_span) == (1, 1)


@pytest.mark.parametrize(
    "changes",
    [{"row": -1}, {"column_span": 0}, {"is_header": 1}, {"header_cell_ids": ["x"]}],
    ids=["negative-row", "zero-span", "int-flag", "list-not-tuple"],
)
def test_table_context_is_strictly_typed(changes: dict[str, object]) -> None:
    fields: dict[str, object] = {"row": 0, "column": 0, "is_header": False}
    fields.update(changes)
    with pytest.raises(ValidationError):
        TableCellContext(**fields)


def test_an_element_is_not_its_own_parent() -> None:
    with pytest.raises(ValidationError, match="its own parent"):
        DocumentElement.create(
            DOCUMENT, ElementType.HEADING, HEADING, parent_id="heading-0-7"
        )


def test_an_element_round_trips_through_json() -> None:
    context = TableCellContext(row=0, column=0, is_header=True)
    cell = DocumentElement.create(
        DOCUMENT,
        ElementType.TABLE_CELL,
        CELL,
        parent_id="table-22-31",
        table_cell=context,
        source_type="lxml:th",
    )
    assert DocumentElement.model_validate_json(cell.model_dump_json()) == cell
```

- [ ] **Step 2: Run them to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_elements.py -q
```

Expected: exit 2, `1 error`, with
`ModuleNotFoundError: No module named 'earnings_core.elements'`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-core/src/earnings_core/elements.py`:

```python
"""DocumentElement: a typed structural unit with a stable ID and a code-point span."""

from enum import StrEnum
from typing import Self

from pydantic import NonNegativeInt, PositiveInt, model_validator

from earnings_core._model import ContractModel, VersionedRecord
from earnings_core.documents import CanonicalDocument
from earnings_core.spans import TextSpan


class ElementType(StrEnum):
    """R4.1's structural units, plus the types Stage 1's gold and parsers use.

    ``page_artifact`` and the six block types come from the Stage 1 gold
    (docs/verification/V2-parser-fidelity.md, "Element types and nesting observed in
    the gold"); ``other`` is the parsers' catch-all. Adding a type is a schema change.
    """

    SECTION = "section"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    SENTENCE = "sentence"
    FOOTNOTE = "footnote"
    TABLE = "table"
    TABLE_CELL = "table_cell"
    SPEAKER_TURN = "speaker_turn"
    PAGE_ARTIFACT = "page_artifact"
    OTHER = "other"


LEVELED_TYPES = frozenset(
    {ElementType.SECTION, ElementType.HEADING, ElementType.LIST_ITEM}
)
"""Types that may carry a level: an outline depth, or a list's nesting depth."""


class TableCellContext(ContractModel):
    """A cell's grid position and the header cells that label it (R4.1, R4.2).

    ``row`` and ``column`` count every cell of the table's grid, empty ones included,
    although an empty cell is never an element: every element span holds text.
    """

    row: NonNegativeInt
    column: NonNegativeInt
    row_span: PositiveInt = 1
    column_span: PositiveInt = 1
    is_header: bool
    header_cell_ids: tuple[str, ...] = ()


def derive_element_id(element_type: ElementType, span: TextSpan) -> str:
    """An element's ID: its type and span, e.g. ``paragraph-120-450``.

    Plan decision, 2026-09-25: derived, so two parsers that agree on an element's type
    and span give it the same ID. The ID is unique within one document version; the
    pair ``(doc_id, element_id)`` is unique across versions.
    """
    return f"{element_type.value}-{span.start}-{span.end}"


class DocumentElement(VersionedRecord):
    """One structural unit of one canonical document version (R4.1).

    ``source_type`` records the producing parser's own name for the unit, so each
    producer can publish its type mapping, as Stage 1's dumps did.
    """

    element_id: str
    doc_id: str
    type: ElementType
    span: TextSpan
    parent_id: str | None = None
    level: PositiveInt | None = None
    table_cell: TableCellContext | None = None
    source_type: str = ""

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        expected = derive_element_id(self.type, self.span)
        if self.element_id != expected:
            raise ValueError(
                f"element_id {self.element_id!r} is not the derived {expected!r}"
            )
        if self.parent_id == self.element_id:
            raise ValueError(f"element {self.element_id} is its own parent")
        if self.level is not None and self.type not in LEVELED_TYPES:
            raise ValueError(f"a {self.type.value} element carries no level")
        if (self.type is ElementType.TABLE_CELL) != (self.table_cell is not None):
            raise ValueError(
                "table_cell context is required on table cells and forbidden elsewhere"
            )
        return self

    @classmethod
    def create(
        cls,
        document: CanonicalDocument,
        element_type: ElementType,
        span: TextSpan,
        *,
        parent_id: str | None = None,
        level: int | None = None,
        table_cell: TableCellContext | None = None,
        source_type: str = "",
    ) -> Self:
        """An element of ``document``, with its ID derived from type and span."""
        return cls(
            element_id=derive_element_id(element_type, span),
            doc_id=document.doc_id,
            type=element_type,
            span=span,
            parent_id=parent_id,
            level=level,
            table_cell=table_cell,
            source_type=source_type,
        )
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_elements.py -q
```

Expected: `16 passed`.

- [ ] **Step 5: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `71 passed`; `All checks passed!`; `62 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git add packages/earnings-core/src/earnings_core/elements.py packages/earnings-core/tests/test_elements.py
git commit -m "feat(core): add DocumentElement with derived element IDs"
```

---

### Task 6: Rejection records, element-set checks, and pointer resolution

**Files:**

- Create: `packages/earnings-core/src/earnings_core/rejections.py`
- Create: `packages/earnings-core/src/earnings_core/structure.py`
- Create: `packages/earnings-core/tests/conftest.py`
- Test: `packages/earnings-core/tests/test_structure.py`

**Interfaces:**

- Consumes:
  - `VersionedRecord` and `TextSpan` (Task 2);
  - `CanonicalDocument` and `document_integrity_problem` (Task 4);
  - `DocumentElement`, `ElementType`, `TableCellContext` and `derive_element_id`
    (Task 5).
- Produces, in `earnings_core.rejections`:
  - `VALIDATOR_VERSION = "1"`.
  - `class RejectionReason(StrEnum)`, with 21 values:
    - record, document, and span failures: `malformed_record`,
      `document_integrity`, `wrong_document`, `canonical_hash_mismatch`,
      `span_out_of_bounds`, `quote_text_mismatch`;
    - attribution failures: `unknown_element`, `outside_element`,
      `crosses_speaker_turn`;
    - locator and chunk failures: `locator_mismatch`, `ambiguous_occurrence`,
      `locator_not_found`, `outside_chunk`;
    - element-set failures: `element_id_mismatch`, `duplicate_element`,
      `unknown_parent`, `parent_order`, `outside_parent`, `crossing_elements`,
      `table_cell_parent`, `invalid_header_reference`.
  - `class Rejection(VersionedRecord)`, with the fields `reason: RejectionReason`,
    `detail: str`, and `validator_version: str = VALIDATOR_VERSION`.
- Produces, in `earnings_core.structure`:
  - `validate_elements(document: CanonicalDocument, elements: Sequence[DocumentElement]) -> tuple[Rejection, ...]`.
    It returns an empty tuple for a valid set. Otherwise it returns every problem,
    each detail prefixed with the element's ID (D-8).
  - `resolve_pointer(document: CanonicalDocument, elements: Sequence[DocumentElement], element_id: str) -> TextSpan | Rejection`.
- Produces a session-scoped test fixture, `sample`, in
  `packages/earnings-core/tests/conftest.py`. It is a `Sample` with:
  - `document: CanonicalDocument` and `elements: tuple[DocumentElement, ...]`;
  - the property `text`;
  - `span_of(needle: str, occurrence: int = 0) -> TextSpan`;
  - `element(element_type: ElementType, needle: str, occurrence: int = 0) -> DocumentElement`;
  - `innermost(span: TextSpan) -> DocumentElement`.
- About the sample:
  - Its text has two sections, "Prepared remarks" and "Questions and answers", each
    with a heading and two speaker turns.
  - The CEO and the CFO both say "Results are preliminary.".
  - The text contains a euro sign, an emoji outside the Basic Multilingual Plane,
    and a precomposed é.
  - Tasks 7–11 use it, and Task 9 extends it.

`rejections.py` defines every reason now, including the ones Tasks 7–9 use first.
The enum is closed and documented in one place. Adding a reason later is a
validator-version bump.

- [ ] **Step 1: Write the shared sample**

Create `packages/earnings-core/tests/conftest.py`:

```python
"""A small, fully structured call transcript shared by the earnings-core tests.

Two sections, four speaker turns, and a sentence the CEO and the CFO both say, over
text with a euro sign, an emoji outside the Basic Multilingual Plane, and an accent.
The three are written as escapes so no editor can silently normalize them.
"""

from dataclasses import dataclass

import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.elements import DocumentElement, ElementType
from earnings_core.spans import TextSpan

EURO = "\u20ac"
CHART = "\U0001f4c8"  # outside the Basic Multilingual Plane: two UTF-16 code units
E_ACUTE = "\u00e9"  # precomposed (NFC)
REVENUE = f"Revenue rose 5% to {EURO}2.1 billion {CHART}."
LINES = (
    "Prepared remarks",
    "Operator: Welcome to the call.",
    f"CEO: {REVENUE} Results are preliminary.",
    "Questions and answers",
    f"Analyst: How did the caf{E_ACUTE} segment do?",
    "CFO: Results are preliminary. Margins held at last year's level.",
)
SAMPLE_TEXT = "\n".join(LINES) + "\n"


@dataclass(frozen=True)
class Sample:
    document: CanonicalDocument
    elements: tuple[DocumentElement, ...]

    @property
    def text(self) -> str:
        return self.document.canonical_text

    def span_of(self, needle: str, occurrence: int = 0) -> TextSpan:
        """The span of one occurrence of ``needle``; occurrence 0 is the first."""
        start = -1
        for _ in range(occurrence + 1):
            start = self.text.index(needle, start + 1)
        return TextSpan(start=start, end=start + len(needle))

    def element(
        self, element_type: ElementType, needle: str, occurrence: int = 0
    ) -> DocumentElement:
        """The element of ``element_type`` that holds that occurrence of ``needle``."""
        span = self.span_of(needle, occurrence)
        return next(
            element
            for element in self.elements
            if element.type is element_type and element.span.contains(span)
        )

    def innermost(self, span: TextSpan) -> DocumentElement:
        """The smallest element that contains ``span``."""
        holders = [element for element in self.elements if element.span.contains(span)]
        return min(holders, key=lambda element: element.span.length)


def build_sample() -> Sample:
    document = CanonicalDocument.create(
        source_document_id="sample-call",
        canonicalization_version="test-1",
        canonical_text=SAMPLE_TEXT,
    )
    line_spans: list[TextSpan] = []
    start = 0
    for line in LINES:
        line_spans.append(TextSpan(start=start, end=start + len(line)))
        start += len(line) + 1
    elements: list[DocumentElement] = []

    def add(
        element_type: ElementType,
        span: TextSpan,
        parent: DocumentElement | None = None,
        level: int | None = None,
    ) -> DocumentElement:
        element = DocumentElement.create(
            document,
            element_type,
            span,
            parent_id=None if parent is None else parent.element_id,
            level=level,
        )
        elements.append(element)
        return element

    def sentence(turn: DocumentElement, text: str) -> None:
        start = SAMPLE_TEXT.index(text, turn.span.start)
        add(ElementType.SENTENCE, TextSpan(start=start, end=start + len(text)), turn)

    for first in (0, 3):
        heading, *turn_lines = line_spans[first : first + 3]
        section = add(
            ElementType.SECTION,
            TextSpan(start=heading.start, end=turn_lines[-1].end),
            level=1,
        )
        add(ElementType.HEADING, heading, section, level=1)
        turns = [add(ElementType.SPEAKER_TURN, span, section) for span in turn_lines]
        if first == 0:
            sentence(turns[1], REVENUE)
            sentence(turns[1], "Results are preliminary.")
        else:
            sentence(turns[1], "Results are preliminary.")
            sentence(turns[1], "Margins held at last year's level.")
    return Sample(document=document, elements=tuple(elements))


@pytest.fixture(scope="session")
def sample() -> Sample:
    return build_sample()
```

Run the escape check:

```bash
python3 -c 'import sys; bad = {p: sorted({hex(ord(c)) for c in open(p, encoding="utf-8").read() if ord(c) > 127} - {"0xa7", "0x20ac"}) for p in sys.argv[1:]}; print({p: b for p, b in bad.items() if b} or "escapes intact")' packages/earnings-core/tests/conftest.py
```

Expected: `escapes intact`. If it prints a file name instead, re-extract that file
(Global Constraints, "Writing files from this plan") and rerun the check.

- [ ] **Step 2: Write the failing tests**

Create `packages/earnings-core/tests/test_structure.py`:

```python
import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.elements import DocumentElement, ElementType, TableCellContext
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan
from earnings_core.structure import resolve_pointer, validate_elements


def reasons(rejections: tuple[Rejection, ...]) -> list[RejectionReason]:
    return [rejection.reason for rejection in rejections]


def test_the_sample_structure_is_valid(sample) -> None:
    assert validate_elements(sample.document, sample.elements) == ()


def test_an_element_of_another_document_is_refused(sample) -> None:
    other = CanonicalDocument.create(
        source_document_id="another-call",
        canonicalization_version="test-1",
        canonical_text=sample.text,
    )
    stranger = DocumentElement.create(
        other, ElementType.OTHER, TextSpan(start=0, end=5)
    )
    assert reasons(validate_elements(sample.document, [stranger])) == [
        RejectionReason.WRONG_DOCUMENT
    ]


def test_a_tampered_element_id_is_caught(sample) -> None:
    section = sample.element(ElementType.SECTION, "Prepared remarks")
    moved = section.model_copy(update={"span": TextSpan(start=0, end=8)})
    assert reasons(validate_elements(sample.document, [moved])) == [
        RejectionReason.ELEMENT_ID_MISMATCH
    ]


def test_a_span_past_the_text_is_refused(sample) -> None:
    beyond = DocumentElement.create(
        sample.document,
        ElementType.OTHER,
        TextSpan(start=0, end=len(sample.text) + 1),
    )
    assert reasons(validate_elements(sample.document, [beyond])) == [
        RejectionReason.SPAN_OUT_OF_BOUNDS
    ]


def test_a_duplicate_element_is_refused(sample) -> None:
    section = sample.element(ElementType.SECTION, "Prepared remarks")
    assert reasons(validate_elements(sample.document, [section, section])) == [
        RejectionReason.DUPLICATE_ELEMENT
    ]


def test_parent_references_must_resolve_precede_and_contain(sample) -> None:
    section = sample.element(ElementType.SECTION, "Prepared remarks")
    heading = sample.element(ElementType.HEADING, "Prepared remarks")
    orphan = heading.model_copy(update={"parent_id": "section-999-1000"})
    assert reasons(validate_elements(sample.document, [orphan])) == [
        RejectionReason.UNKNOWN_PARENT
    ]
    assert reasons(validate_elements(sample.document, [heading, section])) == [
        RejectionReason.PARENT_ORDER
    ]
    later = sample.element(ElementType.SPEAKER_TURN, "Analyst:")
    escaped = later.model_copy(update={"parent_id": section.element_id})
    assert reasons(validate_elements(sample.document, [section, escaped])) == [
        RejectionReason.OUTSIDE_PARENT
    ]


def test_spans_that_cross_without_nesting_are_refused(sample) -> None:
    welcome = sample.span_of("Welcome")
    revenue = sample.span_of("Revenue")
    straddle = DocumentElement.create(
        sample.document,
        ElementType.OTHER,
        TextSpan(start=welcome.start, end=revenue.end),
    )
    found = validate_elements(sample.document, [*sample.elements, straddle])
    assert reasons(found) == [RejectionReason.CROSSING_ELEMENTS]


def test_a_tampered_document_is_reported_once(sample) -> None:
    tampered = sample.document.model_copy(update={"canonical_text": "changed"})
    assert reasons(validate_elements(tampered, sample.elements)) == [
        RejectionReason.DOCUMENT_INTEGRITY
    ]


TABLE_TEXT = "Metric\tQ3 2026\nNet sales\t$9.8"
TABLE = CanonicalDocument.create(
    source_document_id="table-test",
    canonicalization_version="test-1",
    canonical_text=TABLE_TEXT,
)


def cell(
    text: str, row: int, column: int, *, header: bool, parent: str, headers=()
) -> DocumentElement:
    start = TABLE_TEXT.index(text)
    return DocumentElement.create(
        TABLE,
        ElementType.TABLE_CELL,
        TextSpan(start=start, end=start + len(text)),
        parent_id=parent,
        table_cell=TableCellContext(
            row=row, column=column, is_header=header, header_cell_ids=tuple(headers)
        ),
    )


def table_elements(parent_type: ElementType = ElementType.TABLE) -> list:
    table = DocumentElement.create(
        TABLE, parent_type, TextSpan(start=0, end=len(TABLE_TEXT))
    )
    metric = cell("Metric", 0, 0, header=True, parent=table.element_id)
    quarter = cell("Q3 2026", 0, 1, header=True, parent=table.element_id)
    sales = cell(
        "Net sales",
        1,
        0,
        header=False,
        parent=table.element_id,
        headers=[metric.element_id],
    )
    value = cell(
        "$9.8",
        1,
        1,
        header=False,
        parent=table.element_id,
        headers=[quarter.element_id],
    )
    return [table, metric, quarter, sales, value]


def test_a_table_with_header_context_is_valid() -> None:
    assert validate_elements(TABLE, table_elements()) == ()


def test_a_table_cell_must_sit_in_a_table() -> None:
    found = validate_elements(TABLE, table_elements(ElementType.PARAGRAPH))
    assert set(reasons(found)) == {RejectionReason.TABLE_CELL_PARENT}


def test_a_header_reference_must_name_a_header_cell_of_the_same_table() -> None:
    table, metric, quarter, sales, _value = table_elements()
    wrong = cell(
        "$9.8", 1, 1, header=False, parent=table.element_id, headers=[sales.element_id]
    )
    found = validate_elements(TABLE, [table, metric, quarter, sales, wrong])
    assert reasons(found) == [RejectionReason.INVALID_HEADER_REFERENCE]


def test_a_pointer_resolves_to_its_elements_span(sample) -> None:
    sentence = sample.element(ElementType.SENTENCE, "Margins held")
    assert resolve_pointer(sample.document, sample.elements, sentence.element_id) == (
        sentence.span
    )


@pytest.mark.parametrize(
    "pointer",
    ["sentence-0-5", "", "sentence-12", "SENTENCE-0-16", "p12"],
    ids=["absent", "empty", "truncated", "wrong-case", "prompt-label"],
)
def test_an_invalid_pointer_is_rejected(sample, pointer: str) -> None:
    outcome = resolve_pointer(sample.document, sample.elements, pointer)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.UNKNOWN_ELEMENT


def test_a_pointer_into_another_version_is_rejected(sample) -> None:
    newer = CanonicalDocument.create(
        source_document_id="sample-call",
        canonicalization_version="test-1",
        canonical_text=sample.text.replace("5%", "6%"),
    )
    heading = sample.element(ElementType.HEADING, "Prepared remarks")
    outcome = resolve_pointer(newer, sample.elements, heading.element_id)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.WRONG_DOCUMENT


def test_a_tampered_pointer_target_is_rejected(sample) -> None:
    heading = sample.element(ElementType.HEADING, "Prepared remarks")
    moved = heading.model_copy(update={"span": TextSpan(start=0, end=8)})
    outcome = resolve_pointer(sample.document, [moved], heading.element_id)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.ELEMENT_ID_MISMATCH
```

- [ ] **Step 3: Run them to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_structure.py -q
```

Expected: exit 2, `1 error`, with
`ModuleNotFoundError: No module named 'earnings_core.rejections'`.

- [ ] **Step 4: Write the implementation**

Create `packages/earnings-core/src/earnings_core/rejections.py`:

```python
"""Rejection: the recorded reason a record failed a check (R6.2: rejections stay auditable)."""

from enum import StrEnum

from earnings_core._model import VersionedRecord

VALIDATOR_VERSION = "1"
"""Bump when any check changes: caches key on the verifier version (R14.6)."""


class RejectionReason(StrEnum):
    """Every reason a check can refuse a record, one per failure class."""

    MALFORMED_RECORD = "malformed_record"
    """Wrong types, missing or extra fields, or a non-integer offset (R3.2, R5.5)."""
    DOCUMENT_INTEGRITY = "document_integrity"
    """The document's own hash or doc_id disagrees with its text (R6.1, R3.3)."""
    WRONG_DOCUMENT = "wrong_document"
    """The record names another document, or another version of it (R6.1, R3.3)."""
    CANONICAL_HASH_MISMATCH = "canonical_hash_mismatch"
    """The record's stored hash is not the document's (R6.1)."""
    SPAN_OUT_OF_BOUNDS = "span_out_of_bounds"
    """The span runs past the canonical text (R6.1)."""
    QUOTE_TEXT_MISMATCH = "quote_text_mismatch"
    """``quote_text`` is not exactly ``canonical_text[start:end]`` (R6.1, R5.5, R13.2)."""
    UNKNOWN_ELEMENT = "unknown_element"
    """A pointer or attribution names no element of this document (R5.1, V9)."""
    OUTSIDE_ELEMENT = "outside_element"
    """The span is not inside the element it is attributed to (R6.1)."""
    CROSSES_SPEAKER_TURN = "crosses_speaker_turn"
    """The span runs across a speaker-turn boundary (A §585, V9)."""
    LOCATOR_MISMATCH = "locator_mismatch"
    """The stored prefix or suffix is not the text around the span (R5.4)."""
    AMBIGUOUS_OCCURRENCE = "ambiguous_occurrence"
    """Repeated text whose context does not single out one occurrence (R5.4)."""
    LOCATOR_NOT_FOUND = "locator_not_found"
    """No occurrence of the text matches the locator (R5.4)."""
    OUTSIDE_CHUNK = "outside_chunk"
    """A chunk-local span runs past its chunk (A §508, V9)."""
    ELEMENT_ID_MISMATCH = "element_id_mismatch"
    """An element's ID is not derived from its type and span (R4.1)."""
    DUPLICATE_ELEMENT = "duplicate_element"
    """Two elements share an ID, so the same type and span (R4.1)."""
    UNKNOWN_PARENT = "unknown_parent"
    """A parent ID names no element of the set (R4.1)."""
    PARENT_ORDER = "parent_order"
    """A child precedes its parent in the element sequence (R4.1)."""
    OUTSIDE_PARENT = "outside_parent"
    """A child's span is not inside its parent's span (R4.1)."""
    CROSSING_ELEMENTS = "crossing_elements"
    """Two spans overlap without one containing the other (R4.1)."""
    TABLE_CELL_PARENT = "table_cell_parent"
    """A table cell's parent is not a table element (R4.1, R4.2)."""
    INVALID_HEADER_REFERENCE = "invalid_header_reference"
    """A header reference names no header cell of the same table (R4.2)."""


class Rejection(VersionedRecord):
    """Why a check refused a record, and which validator version said so."""

    reason: RejectionReason
    detail: str
    validator_version: str = VALIDATOR_VERSION
```

Create `packages/earnings-core/src/earnings_core/structure.py`:

```python
"""Checks over one document's element set, and pointer resolution (R4.1, R5.1)."""

from collections.abc import Sequence

from earnings_core.documents import CanonicalDocument, document_integrity_problem
from earnings_core.elements import DocumentElement, ElementType, derive_element_id
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan


def validate_elements(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> tuple[Rejection, ...]:
    """Every structural problem in ``elements``; empty when the set is valid (R4.1).

    Rechecks each stored ID and span rather than trust construction. Parents must
    precede their children, and any two spans must nest or be disjoint.
    """
    problem = document_integrity_problem(document)
    if problem is not None:
        return (Rejection(reason=RejectionReason.DOCUMENT_INTEGRITY, detail=problem),)
    known: dict[str, DocumentElement] = {}
    for element in elements:
        known.setdefault(element.element_id, element)
    problems: list[Rejection] = []
    earlier: dict[str, DocumentElement] = {}
    for element in elements:
        problems.extend(_own_problems(document, element, earlier, known))
        earlier.setdefault(element.element_id, element)
    for element in elements:
        problems.extend(_table_problems(element, known))
    problems.extend(_crossings(elements))
    return tuple(problems)


def resolve_pointer(
    document: CanonicalDocument, elements: Sequence[DocumentElement], element_id: str
) -> TextSpan | Rejection:
    """The span of the element a model pointed at: code, not the model, supplies offsets.

    Only an element of this document version resolves; anything else is an invalid
    pointer with a recorded reason (R5.1, V9).
    """
    problem = document_integrity_problem(document)
    if problem is not None:
        return Rejection(reason=RejectionReason.DOCUMENT_INTEGRITY, detail=problem)
    for element in elements:
        if element.element_id != element_id:
            continue
        if element.doc_id != document.doc_id:
            return Rejection(
                reason=RejectionReason.WRONG_DOCUMENT,
                detail=f"element {element_id} belongs to {element.doc_id},"
                f" not {document.doc_id}",
            )
        if derive_element_id(element.type, element.span) != element_id:
            return Rejection(
                reason=RejectionReason.ELEMENT_ID_MISMATCH,
                detail=f"element {element_id} does not match its type and span",
            )
        return element.span
    return Rejection(
        reason=RejectionReason.UNKNOWN_ELEMENT,
        detail=f"no element {element_id!r} in {document.doc_id}",
    )


def _own_problems(
    document: CanonicalDocument,
    element: DocumentElement,
    earlier: dict[str, DocumentElement],
    known: dict[str, DocumentElement],
) -> list[Rejection]:
    found: list[Rejection] = []
    name = element.element_id

    def reject(reason: RejectionReason, detail: str) -> None:
        found.append(Rejection(reason=reason, detail=f"{name}: {detail}"))

    if element.doc_id != document.doc_id:
        reject(RejectionReason.WRONG_DOCUMENT, f"belongs to {element.doc_id}")
    if name != derive_element_id(element.type, element.span):
        reject(RejectionReason.ELEMENT_ID_MISMATCH, "ID is not its type and span")
    if element.span.end > len(document.canonical_text):
        reject(
            RejectionReason.SPAN_OUT_OF_BOUNDS,
            f"ends at {element.span.end}, past {len(document.canonical_text)}",
        )
    if name in earlier:
        reject(RejectionReason.DUPLICATE_ELEMENT, "appears twice")
    if element.parent_id is not None:
        parent = known.get(element.parent_id)
        if parent is None:
            reject(RejectionReason.UNKNOWN_PARENT, f"parent {element.parent_id}")
        elif element.parent_id not in earlier:
            reject(RejectionReason.PARENT_ORDER, f"precedes parent {element.parent_id}")
        elif not parent.span.contains(element.span):
            reject(RejectionReason.OUTSIDE_PARENT, f"not inside {parent.element_id}")
    return found


def _table_problems(
    element: DocumentElement, known: dict[str, DocumentElement]
) -> list[Rejection]:
    context = element.table_cell
    if context is None:
        return []
    name = element.element_id
    parent = known.get(element.parent_id) if element.parent_id is not None else None
    if parent is None or parent.type is not ElementType.TABLE:
        return [
            Rejection(
                reason=RejectionReason.TABLE_CELL_PARENT,
                detail=f"{name}: parent {element.parent_id} is not a table",
            )
        ]
    found: list[Rejection] = []
    for header_id in context.header_cell_ids:
        header = known.get(header_id)
        if (
            header is None
            or header.table_cell is None
            or not header.table_cell.is_header
            or header.parent_id != element.parent_id
        ):
            found.append(
                Rejection(
                    reason=RejectionReason.INVALID_HEADER_REFERENCE,
                    detail=f"{name}: {header_id} is not a header cell of"
                    f" {element.parent_id}",
                )
            )
    return found


def _crossings(elements: Sequence[DocumentElement]) -> list[Rejection]:
    """Spans that overlap without nesting, found by one sweep in document order."""
    ordered = sorted(
        elements, key=lambda element: (element.span.start, -element.span.end)
    )
    open_spans: list[DocumentElement] = []
    found: list[Rejection] = []
    for element in ordered:
        while open_spans and open_spans[-1].span.end <= element.span.start:
            open_spans.pop()
        if open_spans and not open_spans[-1].span.contains(element.span):
            found.append(
                Rejection(
                    reason=RejectionReason.CROSSING_ELEMENTS,
                    detail=f"{element.element_id} overlaps"
                    f" {open_spans[-1].element_id} without nesting",
                )
            )
            continue
        open_spans.append(element)
    return found
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_structure.py -q
```

Expected: `19 passed`.

- [ ] **Step 6: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `90 passed`; `All checks passed!`; `66 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git add packages/earnings-core/src/earnings_core/rejections.py packages/earnings-core/src/earnings_core/structure.py packages/earnings-core/tests/conftest.py packages/earnings-core/tests/test_structure.py
git commit -m "feat(core): add rejection records, element-set checks, and pointer resolution"
```

---

### Task 7: Prefix/suffix span locators

**Files:**

- Create: `packages/earnings-core/src/earnings_core/locators.py`
- Test: `packages/earnings-core/tests/test_locators.py`

**Interfaces:**

- Consumes:
  - `ContractModel` and `TextSpan` (Task 2);
  - `CanonicalDocument` and `document_integrity_problem` (Task 4);
  - `Rejection` and `RejectionReason` (Task 6);
  - the `sample` fixture (Task 6).
- Produces, in `earnings_core.locators`:
  - `class SpanLocator(ContractModel)`, with the fields `exact: str` (at least one
    character), `prefix: str = ""`, and `suffix: str = ""`.
  - `occurrences(text: str, locator: SpanLocator) -> list[int]`. It returns every
    start offset whose context matches, overlapping occurrences included.
  - `make_locator(document: CanonicalDocument, span: TextSpan) -> SpanLocator`, which
    uses the fewest whole words of context (D-4).
  - `resolve_locator(document: CanonicalDocument, locator: SpanLocator) -> TextSpan | Rejection`.
    It returns the one span, or `locator_not_found`, or `ambiguous_occurrence`. It
    never returns a first match.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-core/tests/test_locators.py`:

```python
import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.locators import (
    SpanLocator,
    make_locator,
    occurrences,
    resolve_locator,
)
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan
from pydantic import ValidationError


def document(text: str) -> CanonicalDocument:
    return CanonicalDocument.create(
        source_document_id="locator-test",
        canonicalization_version="test-1",
        canonical_text=text,
    )


def span_at(text: str, needle: str, occurrence: int) -> TextSpan:
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(needle, start + 1)
    return TextSpan(start=start, end=start + len(needle))


def test_unique_text_needs_no_context(sample) -> None:
    span = sample.span_of("Margins held")
    assert make_locator(sample.document, span) == SpanLocator(exact="Margins held")


def test_a_repeated_sentence_gets_one_word_each_side(sample) -> None:
    first = make_locator(sample.document, sample.span_of("Results are preliminary."))
    second = make_locator(
        sample.document, sample.span_of("Results are preliminary.", 1)
    )
    assert (first.prefix, first.suffix) == ("\U0001f4c8. ", "\nQuestions")
    assert (second.prefix, second.suffix) == ("CFO: ", " Margins")


def test_context_grows_until_the_occurrence_is_unique() -> None:
    text = "x a b TARGET c y and z a b TARGET c w"
    locator = make_locator(document(text), span_at(text, "TARGET", 1))
    # One word each side ("b ", " c") still matches both; two words do not.
    assert (locator.prefix, locator.suffix) == ("a b ", " c w")


def test_a_word_cut_by_the_span_edge_counts_as_one_word() -> None:
    text = "prerevenue and revenue"
    locator = make_locator(document(text), span_at(text, "revenue", 0))
    assert (locator.prefix, locator.suffix) == ("pre", " and")


def test_context_stops_at_the_document_edges() -> None:
    # "abab" is one word, so each side's context is the rest of that word.
    text = "abab"
    assert make_locator(document(text), TextSpan(start=0, end=2)) == SpanLocator(
        exact="ab", prefix="", suffix="ab"
    )
    assert make_locator(document(text), TextSpan(start=2, end=4)) == SpanLocator(
        exact="ab", prefix="ab", suffix=""
    )


def test_every_span_round_trips_through_its_locator(sample) -> None:
    for element in sample.elements:
        locator = make_locator(sample.document, element.span)
        assert resolve_locator(sample.document, locator) == element.span


def test_overlapping_occurrences_count() -> None:
    assert occurrences("aaa", SpanLocator(exact="aa")) == [0, 1]


def test_a_repeated_text_without_context_is_ambiguous_never_first_match(
    sample,
) -> None:
    outcome = resolve_locator(
        sample.document, SpanLocator(exact="Results are preliminary.")
    )
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.AMBIGUOUS_OCCURRENCE


@pytest.mark.parametrize(
    "locator",
    [
        SpanLocator(exact="Results were final."),
        SpanLocator(exact="Results are preliminary.", prefix="CTO: "),
    ],
    ids=["absent-text", "absent-context"],
)
def test_a_locator_that_matches_nothing_is_rejected(sample, locator) -> None:
    outcome = resolve_locator(sample.document, locator)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.LOCATOR_NOT_FOUND


def test_exact_text_may_not_be_empty() -> None:
    with pytest.raises(ValidationError):
        SpanLocator(exact="")
```

Run the escape check:

```bash
python3 -c 'import sys; bad = {p: sorted({hex(ord(c)) for c in open(p, encoding="utf-8").read() if ord(c) > 127} - {"0xa7", "0x20ac"}) for p in sys.argv[1:]}; print({p: b for p, b in bad.items() if b} or "escapes intact")' packages/earnings-core/tests/test_locators.py
```

Expected: `escapes intact`. If it prints a file name instead, re-extract that file
(Global Constraints, "Writing files from this plan") and rerun the check.

- [ ] **Step 2: Run them to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_locators.py -q
```

Expected: exit 2, `1 error`, with
`ModuleNotFoundError: No module named 'earnings_core.locators'`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-core/src/earnings_core/locators.py`:

```python
"""Span locators: exact text plus the context that singles out one occurrence (R5.4)."""

import re
from typing import Annotated

from pydantic import StringConstraints

from earnings_core._model import ContractModel
from earnings_core.documents import CanonicalDocument, document_integrity_problem
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan

_WORD = re.compile(r"\S+")


class SpanLocator(ContractModel):
    """Exact text with the words just before and after it (R5.4, R7.1).

    Modeled on a text-quote selector: ``prefix`` ends where ``exact`` starts and
    ``suffix`` starts where it ends. Both are empty when ``exact`` occurs once.
    """

    exact: Annotated[str, StringConstraints(min_length=1)]
    prefix: str = ""
    suffix: str = ""


def occurrences(text: str, locator: SpanLocator) -> list[int]:
    """Every start offset of ``exact`` whose surrounding text matches the context.

    Overlapping occurrences count: ``"aa"`` occurs twice in ``"aaa"``.
    """
    found: list[int] = []
    width = len(locator.exact)
    position = text.find(locator.exact)
    while position != -1:
        before = text[max(0, position - len(locator.prefix)) : position]
        after = text[position + width : position + width + len(locator.suffix)]
        if before == locator.prefix and after == locator.suffix:
            found.append(position)
        position = text.find(locator.exact, position + 1)
    return found


def make_locator(document: CanonicalDocument, span: TextSpan) -> SpanLocator:
    """The fewest whole words of context that make ``span``'s occurrence unique.

    Plan decision, 2026-09-25: context grows by one whitespace-delimited word on each
    side at a time, so Stage 10's text-fragment links can reuse it. A word cut by the
    span's edge counts as one word. Full context always suffices, so this terminates.
    """
    text = document.canonical_text
    exact = span.slice_of(text)
    word_starts = [match.start() for match in _WORD.finditer(text, 0, span.start)]
    word_ends = [match.end() for match in _WORD.finditer(text, span.end)]
    words = 0
    while True:
        prefix = _before(text, span.start, word_starts, words)
        suffix = _after(text, span.end, word_ends, words)
        locator = SpanLocator(exact=exact, prefix=prefix, suffix=suffix)
        if occurrences(text, locator) == [span.start]:
            return locator
        words += 1


def resolve_locator(
    document: CanonicalDocument, locator: SpanLocator
) -> TextSpan | Rejection:
    """The one span a locator identifies; never a guess at the first match (R5.4)."""
    problem = document_integrity_problem(document)
    if problem is not None:
        return Rejection(reason=RejectionReason.DOCUMENT_INTEGRITY, detail=problem)
    starts = occurrences(document.canonical_text, locator)
    if not starts:
        return Rejection(
            reason=RejectionReason.LOCATOR_NOT_FOUND,
            detail=f"{locator.exact!r} does not occur with this context",
        )
    if len(starts) > 1:
        return Rejection(
            reason=RejectionReason.AMBIGUOUS_OCCURRENCE,
            detail=f"{locator.exact!r} occurs {len(starts)} times with this context,"
            f" at {starts}",
        )
    return TextSpan(start=starts[0], end=starts[0] + len(locator.exact))


def _before(text: str, start: int, word_starts: list[int], words: int) -> str:
    if words == 0:
        return ""
    if words > len(word_starts):
        return text[:start]
    return text[word_starts[-words] : start]


def _after(text: str, end: int, word_ends: list[int], words: int) -> str:
    if words == 0:
        return ""
    if words > len(word_ends):
        return text[end:]
    return text[end : word_ends[words - 1]]
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_locators.py -q
```

Expected: `11 passed`.

- [ ] **Step 5: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `101 passed`; `All checks passed!`; `68 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git add packages/earnings-core/src/earnings_core/locators.py packages/earnings-core/tests/test_locators.py
git commit -m "feat(core): add prefix/suffix span locators"
```

---

### Task 8: TextChunk and chunk-to-document conversion

**Files:**

- Create: `packages/earnings-core/src/earnings_core/chunks.py`
- Test: `packages/earnings-core/tests/test_chunks.py`

**Interfaces:**

- Consumes:
  - `VersionedRecord`, `Sha256Hex` and `TextSpan` (Task 2);
  - `CanonicalDocument` (Task 4);
  - `ElementType` (Task 5);
  - `Rejection` and `RejectionReason` (Task 6);
  - the `sample` fixture (Task 6).
- Produces, in `earnings_core.chunks`: `class TextChunk(VersionedRecord)`.
  - Fields: `doc_id: str`, `canonical_hash: Sha256Hex`, `span: TextSpan`, and
    `text: str`, which holds exactly `span.length` characters.
  - The classmethod `TextChunk.of(document: CanonicalDocument, span: TextSpan) -> TextChunk`,
    which raises `ValueError` when the span runs past the text.
  - `TextChunk.to_document_span(local: TextSpan) -> TextSpan | Rejection`, which
    returns `outside_chunk` when the local span runs past the chunk. Convert before
    storing any evidence (A §508).

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-core/tests/test_chunks.py`:

```python
import pytest
from earnings_core.chunks import TextChunk
from earnings_core.elements import ElementType
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan
from pydantic import ValidationError


def test_a_local_span_converts_to_the_same_document_text(sample) -> None:
    turn = sample.element(ElementType.SPEAKER_TURN, "CFO:")
    chunk = TextChunk.of(sample.document, turn.span)
    local_start = chunk.text.index("Margins held")
    local = TextSpan(start=local_start, end=local_start + len("Margins held"))
    converted = chunk.to_document_span(local)
    assert converted == sample.span_of("Margins held")
    assert converted.slice_of(sample.text) == local.slice_of(chunk.text)


def test_local_offsets_are_not_document_offsets(sample) -> None:
    turn = sample.element(ElementType.SPEAKER_TURN, "CFO:")
    chunk = TextChunk.of(sample.document, turn.span)
    local = TextSpan(start=0, end=4)
    assert local.slice_of(chunk.text) == "CFO:"
    assert local.slice_of(sample.text) != "CFO:"


def test_a_local_span_past_its_chunk_is_rejected(sample) -> None:
    chunk = TextChunk.of(sample.document, sample.span_of("Margins held"))
    outcome = chunk.to_document_span(TextSpan(start=0, end=len(chunk.text) + 1))
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.OUTSIDE_CHUNK


def test_a_chunk_cannot_run_past_its_document(sample) -> None:
    with pytest.raises(ValueError, match="runs past"):
        TextChunk.of(sample.document, TextSpan(start=0, end=len(sample.text) + 1))


def test_chunk_text_must_fill_its_span(sample) -> None:
    chunk = TextChunk.of(sample.document, sample.span_of("Margins held"))
    with pytest.raises(ValidationError, match="characters for a span"):
        TextChunk(
            doc_id=chunk.doc_id,
            canonical_hash=chunk.canonical_hash,
            span=chunk.span,
            text=chunk.text + " ",
        )


def test_a_chunk_carries_its_documents_identity(sample) -> None:
    chunk = TextChunk.of(sample.document, sample.span_of("Margins held"))
    assert (chunk.doc_id, chunk.canonical_hash) == (
        sample.document.doc_id,
        sample.document.canonical_hash,
    )
    assert TextChunk.model_validate_json(chunk.model_dump_json()) == chunk
```

- [ ] **Step 2: Run them to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_chunks.py -q
```

Expected: exit 2, `1 error`, with
`ModuleNotFoundError: No module named 'earnings_core.chunks'`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-core/src/earnings_core/chunks.py`:

```python
"""TextChunk: a view of one document whose local offsets convert back (A §508)."""

from typing import Self

from pydantic import model_validator

from earnings_core._model import VersionedRecord
from earnings_core.documents import CanonicalDocument
from earnings_core.hashing import Sha256Hex
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan


class TextChunk(VersionedRecord):
    """A slice of a canonical document, handed to a model or a parser as a unit.

    A chunk never re-normalizes its text: ``text`` is exactly the document's
    characters over ``span``, so a local span converts back by adding one offset.
    Convert before storing evidence (A §508).
    """

    doc_id: str
    canonical_hash: Sha256Hex
    span: TextSpan
    text: str

    @model_validator(mode="after")
    def _text_fills_span(self) -> Self:
        if len(self.text) != self.span.length:
            raise ValueError(
                f"chunk text has {len(self.text)} characters for a span of"
                f" {self.span.length}"
            )
        return self

    @classmethod
    def of(cls, document: CanonicalDocument, span: TextSpan) -> Self:
        """The chunk of ``document`` over ``span``; raises if it runs past the text."""
        return cls(
            doc_id=document.doc_id,
            canonical_hash=document.canonical_hash,
            span=span,
            text=span.slice_of(document.canonical_text),
        )

    def to_document_span(self, local: TextSpan) -> TextSpan | Rejection:
        """Convert a span over ``self.text`` into the document's coordinates."""
        if local.end > len(self.text):
            return Rejection(
                reason=RejectionReason.OUTSIDE_CHUNK,
                detail=f"local span [{local.start}, {local.end}) runs past a chunk"
                f" of {len(self.text)} characters",
            )
        return TextSpan(
            start=self.span.start + local.start, end=self.span.start + local.end
        )
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_chunks.py -q
```

Expected: `6 passed`.

- [ ] **Step 5: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `107 passed`; `All checks passed!`; `70 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git add packages/earnings-core/src/earnings_core/chunks.py packages/earnings-core/tests/test_chunks.py
git commit -m "feat(core): add TextChunk and chunk-to-document span conversion"
```

---

### Task 9: The R6.1 span validator

**Files:**

- Create: `packages/earnings-core/src/earnings_core/evidence.py`
- Modify: `packages/earnings-core/tests/conftest.py` (replace the whole file: it gains
  `Sample.candidate` and `Sample.raw`)
- Test: `packages/earnings-core/tests/test_evidence.py`

**Interfaces:**

- Consumes:
  - `VersionedRecord`, `Sha256Hex` and `TextSpan` (Task 2);
  - `CanonicalDocument` and `document_integrity_problem` (Task 4);
  - `DocumentElement`, `ElementType` and `derive_element_id` (Task 5);
  - `VALIDATOR_VERSION`, `Rejection`, `RejectionReason` and `resolve_pointer`
    (Task 6);
  - `SpanLocator`, `occurrences`, `make_locator` and `resolve_locator` (Task 7).
- Produces, in `earnings_core.evidence`:
  - `class SpanCandidate(VersionedRecord)`, with these fields:
    - `doc_id: str` and `canonical_hash: Sha256Hex`;
    - `start: NonNegativeInt` and `end: NonNegativeInt`, with `start < end`;
    - `quote_text: str` and `element_id: str`;
    - `prefix: str = ""` and `suffix: str = ""`.

    It also has the property `span -> TextSpan`.
  - `class VerifiedSpan`, with the same fields plus `validator_version: str`. The two
    classes share a private base, `_EvidenceFields`. One record is always one
    contiguous range (R5.5).
  - `parse_span_candidate(raw: object) -> SpanCandidate | Rejection`. `raw` is JSON
    text, JSON bytes, or an already-decoded mapping, and anything malformed is
    `malformed_record`.
  - `validate_span(document: CanonicalDocument, elements: Sequence[DocumentElement], candidate: SpanCandidate) -> VerifiedSpan | Rejection`.
    It takes exactly these three parameters, and none of them is a tolerance (R13.2).
- `validate_span` runs its checks in a fixed order and records the first failure
  (D-8):
  1. `document_integrity`
  2. `wrong_document`
  3. `canonical_hash_mismatch`
  4. `span_out_of_bounds`
  5. `quote_text_mismatch`
  6. `unknown_element`
  7. `outside_element`
  8. `crosses_speaker_turn`
  9. `locator_mismatch`
  10. `ambiguous_occurrence`
- Produces two helpers in the test fixture:
  - `Sample.candidate(needle: str, occurrence: int = 0, **changes: object) -> SpanCandidate`.
    It builds a valid candidate for that occurrence of `needle`: attributed to the
    innermost element that holds it, with the context `make_locator` chooses. Then
    `changes` override fields.
  - `Sample.raw(needle: str, occurrence: int = 0, **changes: object) -> dict`. It
    returns that valid candidate as a decoded JSON object, then applies `changes`.
    Here `changes` may be ill-typed: that is how Task 11 feeds malformed records.

- [ ] **Step 1: Extend the shared sample**

Replace `packages/earnings-core/tests/conftest.py` with:

```python
"""A small, fully structured call transcript shared by the earnings-core tests.

Two sections, four speaker turns, and a sentence the CEO and the CFO both say, over
text with a euro sign, an emoji outside the Basic Multilingual Plane, and an accent.
The three are written as escapes so no editor can silently normalize them.
"""

from dataclasses import dataclass

import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.elements import DocumentElement, ElementType
from earnings_core.evidence import SpanCandidate
from earnings_core.locators import make_locator
from earnings_core.spans import TextSpan

EURO = "\u20ac"
CHART = "\U0001f4c8"  # outside the Basic Multilingual Plane: two UTF-16 code units
E_ACUTE = "\u00e9"  # precomposed (NFC)
REVENUE = f"Revenue rose 5% to {EURO}2.1 billion {CHART}."
LINES = (
    "Prepared remarks",
    "Operator: Welcome to the call.",
    f"CEO: {REVENUE} Results are preliminary.",
    "Questions and answers",
    f"Analyst: How did the caf{E_ACUTE} segment do?",
    "CFO: Results are preliminary. Margins held at last year's level.",
)
SAMPLE_TEXT = "\n".join(LINES) + "\n"


@dataclass(frozen=True)
class Sample:
    document: CanonicalDocument
    elements: tuple[DocumentElement, ...]

    @property
    def text(self) -> str:
        return self.document.canonical_text

    def span_of(self, needle: str, occurrence: int = 0) -> TextSpan:
        """The span of one occurrence of ``needle``; occurrence 0 is the first."""
        start = -1
        for _ in range(occurrence + 1):
            start = self.text.index(needle, start + 1)
        return TextSpan(start=start, end=start + len(needle))

    def element(
        self, element_type: ElementType, needle: str, occurrence: int = 0
    ) -> DocumentElement:
        """The element of ``element_type`` that holds that occurrence of ``needle``."""
        span = self.span_of(needle, occurrence)
        return next(
            element
            for element in self.elements
            if element.type is element_type and element.span.contains(span)
        )

    def innermost(self, span: TextSpan) -> DocumentElement:
        """The smallest element that contains ``span``."""
        holders = [element for element in self.elements if element.span.contains(span)]
        return min(holders, key=lambda element: element.span.length)

    def candidate(
        self, needle: str, occurrence: int = 0, **changes: object
    ) -> SpanCandidate:
        """A valid candidate for one occurrence of ``needle``, with ``changes`` applied.

        It is attributed to the innermost element holding it, and carries the context
        ``make_locator`` chooses.
        """
        span = self.span_of(needle, occurrence)
        locator = make_locator(self.document, span)
        fields: dict[str, object] = {
            "doc_id": self.document.doc_id,
            "canonical_hash": self.document.canonical_hash,
            "start": span.start,
            "end": span.end,
            "quote_text": needle,
            "element_id": self.innermost(span).element_id,
            "prefix": locator.prefix,
            "suffix": locator.suffix,
        }
        fields.update(changes)
        return SpanCandidate(**fields)

    def raw(self, needle: str, occurrence: int = 0, **changes: object) -> dict:
        """That valid candidate as a decoded JSON object, with ``changes`` applied."""
        return {**self.candidate(needle, occurrence).model_dump(), **changes}


def build_sample() -> Sample:
    document = CanonicalDocument.create(
        source_document_id="sample-call",
        canonicalization_version="test-1",
        canonical_text=SAMPLE_TEXT,
    )
    line_spans: list[TextSpan] = []
    start = 0
    for line in LINES:
        line_spans.append(TextSpan(start=start, end=start + len(line)))
        start += len(line) + 1
    elements: list[DocumentElement] = []

    def add(
        element_type: ElementType,
        span: TextSpan,
        parent: DocumentElement | None = None,
        level: int | None = None,
    ) -> DocumentElement:
        element = DocumentElement.create(
            document,
            element_type,
            span,
            parent_id=None if parent is None else parent.element_id,
            level=level,
        )
        elements.append(element)
        return element

    def sentence(turn: DocumentElement, text: str) -> None:
        start = SAMPLE_TEXT.index(text, turn.span.start)
        add(ElementType.SENTENCE, TextSpan(start=start, end=start + len(text)), turn)

    for first in (0, 3):
        heading, *turn_lines = line_spans[first : first + 3]
        section = add(
            ElementType.SECTION,
            TextSpan(start=heading.start, end=turn_lines[-1].end),
            level=1,
        )
        add(ElementType.HEADING, heading, section, level=1)
        turns = [add(ElementType.SPEAKER_TURN, span, section) for span in turn_lines]
        if first == 0:
            sentence(turns[1], REVENUE)
            sentence(turns[1], "Results are preliminary.")
        else:
            sentence(turns[1], "Results are preliminary.")
            sentence(turns[1], "Margins held at last year's level.")
    return Sample(document=document, elements=tuple(elements))


@pytest.fixture(scope="session")
def sample() -> Sample:
    return build_sample()
```

Run the escape check:

```bash
python3 -c 'import sys; bad = {p: sorted({hex(ord(c)) for c in open(p, encoding="utf-8").read() if ord(c) > 127} - {"0xa7", "0x20ac"}) for p in sys.argv[1:]}; print({p: b for p, b in bad.items() if b} or "escapes intact")' packages/earnings-core/tests/conftest.py
```

Expected: `escapes intact`. If it prints a file name instead, re-extract that file
(Global Constraints, "Writing files from this plan") and rerun the check.

- [ ] **Step 2: Write the failing tests**

Create `packages/earnings-core/tests/test_evidence.py`:

```python
import inspect
import json

import pytest
from earnings_core.elements import ElementType
from earnings_core.evidence import (
    SpanCandidate,
    VerifiedSpan,
    parse_span_candidate,
    validate_span,
)
from earnings_core.locators import SpanLocator, make_locator, resolve_locator
from earnings_core.rejections import VALIDATOR_VERSION, Rejection, RejectionReason
from earnings_core.structure import resolve_pointer
from pydantic import ValidationError


def test_a_valid_candidate_is_verified(sample) -> None:
    candidate = sample.candidate("Margins held at last year's level.")
    verified = validate_span(sample.document, sample.elements, candidate)
    assert isinstance(verified, VerifiedSpan)
    assert verified.quote_text == sample.text[verified.start : verified.end]
    assert verified.validator_version == VALIDATOR_VERSION
    assert verified.span == sample.span_of("Margins held at last year's level.")


def test_each_occurrence_of_repeated_text_verifies_with_its_own_context(
    sample,
) -> None:
    for occurrence in (0, 1):
        candidate = sample.candidate("Results are preliminary.", occurrence)
        verified = validate_span(sample.document, sample.elements, candidate)
        assert isinstance(verified, VerifiedSpan)
        assert (
            verified.start
            == sample.span_of("Results are preliminary.", occurrence).start
        )


def test_a_span_may_be_attributed_to_any_element_that_contains_it(sample) -> None:
    turn = sample.element(ElementType.SPEAKER_TURN, "CFO:")
    candidate = sample.candidate("Margins held", element_id=turn.element_id)
    verified = validate_span(sample.document, sample.elements, candidate)
    assert isinstance(verified, VerifiedSpan)
    assert verified.element_id == turn.element_id


def test_a_pointer_resolves_to_a_span_that_verifies(sample) -> None:
    sentence = sample.element(ElementType.SENTENCE, "Revenue rose")
    span = resolve_pointer(sample.document, sample.elements, sentence.element_id)
    text = span.slice_of(sample.text)
    locator = make_locator(sample.document, span)
    candidate = SpanCandidate(
        doc_id=sample.document.doc_id,
        canonical_hash=sample.document.canonical_hash,
        start=span.start,
        end=span.end,
        quote_text=text,
        element_id=sentence.element_id,
        prefix=locator.prefix,
        suffix=locator.suffix,
    )
    assert isinstance(
        validate_span(sample.document, sample.elements, candidate), VerifiedSpan
    )


def test_a_located_span_verifies(sample) -> None:
    proposed = SpanLocator(exact="Welcome to the call.")
    span = resolve_locator(sample.document, proposed)
    candidate = sample.candidate("Welcome to the call.")
    assert candidate.span == span
    assert isinstance(
        validate_span(sample.document, sample.elements, candidate), VerifiedSpan
    )


def test_the_first_failing_check_is_the_recorded_reason(sample) -> None:
    candidate = sample.candidate(
        "Margins held", doc_id="another@test-1#0000000000000000", quote_text="x"
    )
    outcome = validate_span(sample.document, sample.elements, candidate)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.WRONG_DOCUMENT


def test_the_validator_takes_no_tolerance() -> None:
    assert list(inspect.signature(validate_span).parameters) == [
        "document",
        "elements",
        "candidate",
    ]


def test_candidate_fields_are_closed_and_strict(sample) -> None:
    with pytest.raises(ValidationError):
        sample.candidate("Margins held", start=True)
    with pytest.raises(ValidationError):
        sample.candidate("Margins held", ranges=[(0, 3)])


def test_json_text_bytes_and_mappings_parse_the_same(sample) -> None:
    raw = sample.raw("Margins held")
    expected = SpanCandidate(**raw)
    assert parse_span_candidate(raw) == expected
    assert parse_span_candidate(json.dumps(raw)) == expected
    assert parse_span_candidate(json.dumps(raw).encode()) == expected


@pytest.mark.parametrize(
    "raw",
    ["{not json", "[1, 2]", 42, None, ["doc_id"]],
    ids=["broken-json", "json-array", "int", "none", "list"],
)
def test_anything_but_a_candidate_object_is_malformed(raw: object) -> None:
    outcome = parse_span_candidate(raw)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.MALFORMED_RECORD
    assert outcome.detail


def test_a_malformed_record_names_the_offending_field(sample) -> None:
    outcome = parse_span_candidate(sample.raw("Margins held", start=1.5))
    assert isinstance(outcome, Rejection)
    assert outcome.detail.startswith("start:")
```

- [ ] **Step 3: Run them to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_evidence.py -q
```

Expected: exit 4, with
`ImportError while loading conftest '…/packages/earnings-core/tests/conftest.py'`
and `ModuleNotFoundError: No module named 'earnings_core.evidence'`. Exit 4 means
the shared sample itself failed to import, so every `earnings-core` test is blocked
until Step 4.

- [ ] **Step 4: Write the implementation**

Create `packages/earnings-core/src/earnings_core/evidence.py`:

```python
"""Evidence spans: parse an untrusted candidate, then verify it exactly (R6.1)."""

from collections.abc import Mapping, Sequence
from typing import Self

from pydantic import NonNegativeInt, ValidationError, model_validator

from earnings_core._model import VersionedRecord
from earnings_core.documents import CanonicalDocument, document_integrity_problem
from earnings_core.elements import DocumentElement, ElementType, derive_element_id
from earnings_core.hashing import Sha256Hex
from earnings_core.locators import SpanLocator, occurrences
from earnings_core.rejections import VALIDATOR_VERSION, Rejection, RejectionReason
from earnings_core.spans import TextSpan


class _EvidenceFields(VersionedRecord):
    """One contiguous range of one document version: noncontiguous evidence is
    separate records, never one stitched record (R5.5)."""

    doc_id: str
    canonical_hash: Sha256Hex
    start: NonNegativeInt
    end: NonNegativeInt
    quote_text: str
    element_id: str
    prefix: str = ""
    suffix: str = ""

    @model_validator(mode="after")
    def _start_before_end(self) -> Self:
        if self.start >= self.end:
            raise ValueError(f"span [{self.start}, {self.end}) is empty or reversed")
        return self

    @property
    def span(self) -> TextSpan:
        return TextSpan(start=self.start, end=self.end)


class SpanCandidate(_EvidenceFields):
    """A proposed evidence span, as it arrives for verification.

    ``element_id`` attributes the span to the section, speaker turn, or other element
    that must contain it. ``prefix`` and ``suffix`` are the words around it, needed
    when ``quote_text`` occurs more than once (R5.4).
    """


class VerifiedSpan(_EvidenceFields):
    """A span that passed every check; ``quote_text`` is sliced from the canonical
    text, never copied from the candidate (A §523)."""

    validator_version: str


def parse_span_candidate(raw: object) -> SpanCandidate | Rejection:
    """Type-check untrusted input, recording a schema failure as a reason.

    ``raw`` is JSON text or bytes, or an already-decoded mapping. A bool, float, or
    numeric string offset (R3.2), a list of ranges (R5.5), a missing field, or any
    extra field is ``malformed_record``.
    """
    try:
        if isinstance(raw, str | bytes):
            return SpanCandidate.model_validate_json(raw)
        if isinstance(raw, Mapping):
            return SpanCandidate.model_validate(dict(raw))
    except ValidationError as error:
        return Rejection(
            reason=RejectionReason.MALFORMED_RECORD, detail=_describe(error)
        )
    return Rejection(
        reason=RejectionReason.MALFORMED_RECORD,
        detail=f"a candidate is a JSON object, not {type(raw).__name__}",
    )


def validate_span(
    document: CanonicalDocument,
    elements: Sequence[DocumentElement],
    candidate: SpanCandidate,
) -> VerifiedSpan | Rejection:
    """Accept one evidence span only if every check holds (R6.1); no tolerance exists.

    The checks run in a fixed order, each presupposing the ones before it, and the
    first failure is the recorded reason. Nothing here is a threshold (R13.2): text is
    compared with ``==``, never normalized. Check the element set once with
    ``validate_elements`` before checking spans against it.
    """
    problem = document_integrity_problem(document)
    if problem is not None:
        return _reject(RejectionReason.DOCUMENT_INTEGRITY, problem)
    text = document.canonical_text
    start, end = candidate.start, candidate.end
    if candidate.doc_id != document.doc_id:
        return _reject(
            RejectionReason.WRONG_DOCUMENT,
            f"candidate names {candidate.doc_id}, not {document.doc_id}",
        )
    if candidate.canonical_hash != document.canonical_hash:
        return _reject(
            RejectionReason.CANONICAL_HASH_MISMATCH,
            f"candidate hash {candidate.canonical_hash} is not"
            f" {document.canonical_hash}",
        )
    if not 0 <= start < end <= len(text):
        return _reject(
            RejectionReason.SPAN_OUT_OF_BOUNDS,
            f"[{start}, {end}) is outside a text of length {len(text)}",
        )
    exact = text[start:end]
    if candidate.quote_text != exact:
        return _reject(
            RejectionReason.QUOTE_TEXT_MISMATCH,
            f"quote_text {candidate.quote_text!r} is not the canonical {exact!r}",
        )
    span = candidate.span
    element = _element(document, elements, candidate.element_id)
    if element is None:
        return _reject(
            RejectionReason.UNKNOWN_ELEMENT,
            f"no element {candidate.element_id!r} in {document.doc_id}",
        )
    if not element.span.contains(span):
        return _reject(
            RejectionReason.OUTSIDE_ELEMENT,
            f"[{start}, {end}) is not inside {element.element_id}",
        )
    for turn in _speaker_turns(document, elements):
        if turn.span.overlaps(span) and not turn.span.contains(span):
            return _reject(
                RejectionReason.CROSSES_SPEAKER_TURN,
                f"[{start}, {end}) crosses the boundary of {turn.element_id}",
            )
    before = text[max(0, start - len(candidate.prefix)) : start]
    after = text[end : end + len(candidate.suffix)]
    if before != candidate.prefix or after != candidate.suffix:
        return _reject(
            RejectionReason.LOCATOR_MISMATCH,
            f"stored context {candidate.prefix!r} / {candidate.suffix!r} is not the"
            f" text around [{start}, {end})",
        )
    locator = SpanLocator(exact=exact, prefix=candidate.prefix, suffix=candidate.suffix)
    count = len(occurrences(text, locator))
    if count > 1:
        return _reject(
            RejectionReason.AMBIGUOUS_OCCURRENCE,
            f"{exact!r} occurs {count} times with this context",
        )
    return VerifiedSpan(
        doc_id=document.doc_id,
        canonical_hash=document.canonical_hash,
        start=start,
        end=end,
        quote_text=exact,
        element_id=element.element_id,
        prefix=candidate.prefix,
        suffix=candidate.suffix,
        validator_version=VALIDATOR_VERSION,
    )


def _reject(reason: RejectionReason, detail: str) -> Rejection:
    return Rejection(reason=reason, detail=detail)


def _genuine(document: CanonicalDocument, element: DocumentElement) -> bool:
    """An element of this document version whose ID still matches its type and span."""
    return element.doc_id == document.doc_id and element.element_id == (
        derive_element_id(element.type, element.span)
    )


def _element(
    document: CanonicalDocument, elements: Sequence[DocumentElement], element_id: str
) -> DocumentElement | None:
    for element in elements:
        if element.element_id == element_id and _genuine(document, element):
            return element
    return None


def _speaker_turns(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> list[DocumentElement]:
    return [
        element
        for element in elements
        if element.type is ElementType.SPEAKER_TURN and _genuine(document, element)
    ]


def _describe(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in item['loc']) or 'record'}: {item['msg']}"
        for item in error.errors()
    )
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_evidence.py -q
```

Expected: `15 passed`.

- [ ] **Step 6: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `122 passed`; `All checks passed!`; `72 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git add packages/earnings-core/src/earnings_core/evidence.py packages/earnings-core/tests/conftest.py packages/earnings-core/tests/test_evidence.py
git commit -m "feat(core): add the R6.1 span validator"
```

---

### Task 10: Overlay masks

**Files:**

- Create: `packages/earnings-core/src/earnings_core/masks.py`
- Test: `packages/earnings-core/tests/test_masks.py`

**Interfaces:**

- Consumes:
  - `ContractModel`, `VersionedRecord`, `Sha256Hex`, `hash_canonical_text` and
    `TextSpan` (Task 2);
  - `CanonicalDocument`, `IdPart` and `document_integrity_problem` (Task 4);
  - `validate_span` and `VerifiedSpan` (Task 9);
  - the `sample` fixture with `Sample.candidate` (Task 9).
- Produces, in `earnings_core.masks`:
  - `class MaskCategory(StrEnum)`, with members `SAFE_HARBOR = "safe_harbor"`,
    `NON_GAAP_DISCLAIMER = "non_gaap_disclaimer"`, and
    `REPEATED_LEGAL = "repeated_legal"`.
  - `class OverlayMask(VersionedRecord)`, with the fields `doc_id: str`,
    `canonical_hash: Sha256Hex`, `span: TextSpan`, `category: MaskCategory`,
    `policy_id: IdPart`, and `policy_version: IdPart`.
  - `class MaskedDocument(ContractModel)`, with the fields
    `document: CanonicalDocument`, `policy_id: IdPart`, `policy_version: IdPart`, and
    `masks: tuple[OverlayMask, ...]`. It has one method,
    `masks_overlapping(span: TextSpan) -> tuple[OverlayMask, ...]`.
  - `apply_masks(document: CanonicalDocument, masks: Sequence[OverlayMask], *, policy_id: str, policy_version: str) -> MaskedDocument`.
    It raises `ValueError` for any of these:
    - a document integrity problem;
    - a mask of another document or version;
    - a mask that runs past the text;
    - a mask from another policy (D-18).
- The roadmap's exit test is
  `test_applying_a_mask_leaves_the_text_and_hash_unchanged` (R3.4).

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-core/tests/test_masks.py`:

```python
import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.evidence import VerifiedSpan, validate_span
from earnings_core.hashing import hash_canonical_text
from earnings_core.masks import MaskCategory, OverlayMask, apply_masks
from earnings_core.spans import TextSpan

POLICY = {"policy_id": "boilerplate", "policy_version": "1"}


def mask_over(document: CanonicalDocument, span: TextSpan, **changes) -> OverlayMask:
    fields: dict[str, object] = {
        "doc_id": document.doc_id,
        "canonical_hash": document.canonical_hash,
        "span": span,
        "category": MaskCategory.SAFE_HARBOR,
        **POLICY,
    }
    fields.update(changes)
    return OverlayMask(**fields)


def test_applying_a_mask_leaves_the_text_and_hash_unchanged(sample) -> None:
    before_text = sample.document.canonical_text
    before_hash = sample.document.canonical_hash
    mask = mask_over(sample.document, sample.span_of("Results are preliminary."))
    masked = apply_masks(sample.document, [mask], **POLICY)
    assert masked.document.canonical_text == before_text
    assert masked.document.canonical_hash == before_hash
    assert hash_canonical_text(masked.document.canonical_text) == before_hash
    assert masked.document.doc_id == sample.document.doc_id


def test_a_masked_span_still_verifies_and_is_reported_for_audit(sample) -> None:
    span = sample.span_of("Results are preliminary.")
    mask = mask_over(sample.document, span)
    masked = apply_masks(sample.document, [mask], **POLICY)
    verified = validate_span(
        masked.document, sample.elements, sample.candidate("Results are preliminary.")
    )
    assert isinstance(verified, VerifiedSpan)
    assert masked.masks_overlapping(verified.span) == (mask,)
    assert masked.masks_overlapping(sample.span_of("Margins held")) == ()


def test_a_policy_that_found_nothing_is_still_recorded(sample) -> None:
    masked = apply_masks(sample.document, [], **POLICY)
    assert (masked.policy_id, masked.policy_version, masked.masks) == (
        "boilerplate",
        "1",
        (),
    )


def test_a_mask_of_another_version_is_refused(sample) -> None:
    newer = CanonicalDocument.create(
        source_document_id="sample-call",
        canonicalization_version="test-1",
        canonical_text=sample.text.replace("5%", "6%"),
    )
    stale = mask_over(sample.document, sample.span_of("Margins held"))
    with pytest.raises(ValueError, match="belongs to"):
        apply_masks(newer, [stale], **POLICY)


def test_a_mask_past_the_text_is_refused(sample) -> None:
    beyond = mask_over(sample.document, TextSpan(start=0, end=len(sample.text) + 1))
    with pytest.raises(ValueError, match="runs past"):
        apply_masks(sample.document, [beyond], **POLICY)


def test_masks_from_two_policy_versions_are_refused(sample) -> None:
    older = mask_over(
        sample.document, sample.span_of("Margins held"), policy_version="0"
    )
    with pytest.raises(ValueError, match="under policy"):
        apply_masks(sample.document, [older], **POLICY)


def test_a_mask_round_trips_through_json(sample) -> None:
    mask = mask_over(
        sample.document,
        sample.span_of("Margins held"),
        category=MaskCategory.NON_GAAP_DISCLAIMER,
    )
    assert OverlayMask.model_validate_json(mask.model_dump_json()) == mask
```

- [ ] **Step 2: Run them to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_masks.py -q
```

Expected: exit 2, `1 error`, with
`ModuleNotFoundError: No module named 'earnings_core.masks'`.

- [ ] **Step 3: Write the implementation**

Create `packages/earnings-core/src/earnings_core/masks.py`:

```python
"""Overlay masks: boilerplate marked over canonical text, never cut from it (R3.4)."""

from collections.abc import Sequence
from enum import StrEnum

from earnings_core._model import ContractModel, VersionedRecord
from earnings_core.documents import (
    CanonicalDocument,
    IdPart,
    document_integrity_problem,
)
from earnings_core.hashing import Sha256Hex
from earnings_core.spans import TextSpan


class MaskCategory(StrEnum):
    """R3.4's boilerplate kinds."""

    SAFE_HARBOR = "safe_harbor"
    NON_GAAP_DISCLAIMER = "non_gaap_disclaimer"
    REPEATED_LEGAL = "repeated_legal"


class OverlayMask(VersionedRecord):
    """One boilerplate span, marked by one version of a boilerplate policy (R3.4).

    A masked span stays in the canonical text and keeps its offsets: it is excluded
    from headline prevalence and retained for audit.
    """

    doc_id: str
    canonical_hash: Sha256Hex
    span: TextSpan
    category: MaskCategory
    policy_id: IdPart
    policy_version: IdPart


class MaskedDocument(ContractModel):
    """A document with the masks one policy version computed over it.

    An empty ``masks`` still records which policy ran and found nothing.
    """

    document: CanonicalDocument
    policy_id: IdPart
    policy_version: IdPart
    masks: tuple[OverlayMask, ...]

    def masks_overlapping(self, span: TextSpan) -> tuple[OverlayMask, ...]:
        """The masks sharing at least one code point with ``span``."""
        return tuple(mask for mask in self.masks if mask.span.overlaps(span))


def apply_masks(
    document: CanonicalDocument,
    masks: Sequence[OverlayMask],
    *,
    policy_id: str,
    policy_version: str,
) -> MaskedDocument:
    """Overlay ``masks`` on ``document`` without touching its text or hash (R3.4).

    Raises ``ValueError`` for a mask of another document or version, a mask past the
    text, or a mask from another policy: one policy version per document keeps every
    comparison period under the same rule (A §591).
    """
    problem = document_integrity_problem(document)
    if problem is not None:
        raise ValueError(problem)
    for mask in masks:
        if (mask.doc_id, mask.canonical_hash) != (
            document.doc_id,
            document.canonical_hash,
        ):
            raise ValueError(
                f"mask over [{mask.span.start}, {mask.span.end}) belongs to"
                f" {mask.doc_id}, not {document.doc_id}"
            )
        if mask.span.end > len(document.canonical_text):
            raise ValueError(
                f"mask over [{mask.span.start}, {mask.span.end}) runs past the text"
            )
        if (mask.policy_id, mask.policy_version) != (policy_id, policy_version):
            raise ValueError(
                f"mask from policy {mask.policy_id} {mask.policy_version}"
                f" under policy {policy_id} {policy_version}"
            )
    return MaskedDocument(
        document=document,
        policy_id=policy_id,
        policy_version=policy_version,
        masks=tuple(masks),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_masks.py -q
```

Expected: `7 passed`.

- [ ] **Step 5: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `129 passed`; `All checks passed!`; `74 files already formatted`.

- [ ] **Step 6: Commit**

```bash
git add packages/earnings-core/src/earnings_core/masks.py packages/earnings-core/tests/test_masks.py
git commit -m "feat(core): add overlay masks computed against canonical text"
```

---

### Task 11: The public API and the Stage 2 failure-class table

**Files:**

- Modify: `packages/earnings-core/src/earnings_core/__init__.py` (replace the whole
  file: `hello()` goes)
- Test: `packages/earnings-core/tests/test_public_api.py`
- Test: `packages/earnings-core/tests/test_failure_classes.py`

**Interfaces:**

- Consumes: every name Tasks 2–10 produce; the `sample` fixture, with
  `Sample.raw` (Task 9).
- Produces: the package root, `earnings_core`, which exports exactly this
  `__all__`:
  - constants: `LEVELED_TYPES`, `SCHEMA_VERSION`, `VALIDATOR_VERSION`;
  - types: `ArtifactRef`, `CanonicalDocument`, `DocumentElement`, `ElementType`,
    `MaskCategory`, `MaskedDocument`, `OverlayMask`, `Rejection`,
    `RejectionReason`, `RightsStatus`, `SpanCandidate`, `SpanLocator`,
    `TableCellContext`, `TextChunk`, `TextSpan`, `VerifiedSpan`;
  - functions: `apply_masks`, `derive_doc_id`, `derive_element_id`,
    `document_integrity_problem`, `hash_canonical_text`, `make_locator`,
    `occurrences`, `parse_span_candidate`, `resolve_locator`, `resolve_pointer`,
    `sha256_hex`, `validate_elements`, `validate_span`.

  Later stages import from the package root only, for example
  `from earnings_core import validate_span`.
- About the table in `test_failure_classes.py`:
  - It is the Stage 2 exit evidence: 32 rows, each named for the requirement or V9
    case it closes.
  - Every row starts from a candidate that verifies, changes one thing about it, and
    asserts the recorded reason.
  - The six positive controls prove those starting candidates verify.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-core/tests/test_public_api.py`:

```python
import earnings_core

PUBLIC = {
    "LEVELED_TYPES",
    "SCHEMA_VERSION",
    "VALIDATOR_VERSION",
    "ArtifactRef",
    "CanonicalDocument",
    "DocumentElement",
    "ElementType",
    "MaskCategory",
    "MaskedDocument",
    "OverlayMask",
    "Rejection",
    "RejectionReason",
    "RightsStatus",
    "SpanCandidate",
    "SpanLocator",
    "TableCellContext",
    "TextChunk",
    "TextSpan",
    "VerifiedSpan",
    "apply_masks",
    "derive_doc_id",
    "derive_element_id",
    "document_integrity_problem",
    "hash_canonical_text",
    "make_locator",
    "occurrences",
    "parse_span_candidate",
    "resolve_locator",
    "resolve_pointer",
    "sha256_hex",
    "validate_elements",
    "validate_span",
}


def test_the_package_root_exports_exactly_the_public_api() -> None:
    assert set(earnings_core.__all__) == PUBLIC
    for name in PUBLIC:
        assert getattr(earnings_core, name) is not None


def test_the_scaffold_placeholder_is_gone() -> None:
    assert not hasattr(earnings_core, "hello")


def test_versions_are_pinned() -> None:
    assert earnings_core.SCHEMA_VERSION == 1
    assert earnings_core.VALIDATOR_VERSION == "1"
```

Create `packages/earnings-core/tests/test_failure_classes.py`:

```python
"""Stage 2 exit evidence: each failure class is rejected with a recorded reason.

One row per failure class, named for the requirement or V9 case it closes. Every row
starts from a candidate that verifies and changes one thing about it.
"""

import unicodedata

import pytest
from earnings_core import (
    VALIDATOR_VERSION,
    CanonicalDocument,
    ElementType,
    Rejection,
    RejectionReason,
    SpanLocator,
    TextChunk,
    TextSpan,
    VerifiedSpan,
    hash_canonical_text,
    parse_span_candidate,
    resolve_locator,
    resolve_pointer,
    validate_span,
)

R = RejectionReason
MARGINS = "Margins held at last year's level."
RESULTS = "Results are preliminary."
QUESTION = "How did the caf\u00e9 segment do?"


def check(sample, raw: object) -> VerifiedSpan | Rejection:
    """Parse, then verify: the path every candidate takes."""
    parsed = parse_span_candidate(raw)
    if isinstance(parsed, Rejection):
        return parsed
    return validate_span(sample.document, sample.elements, parsed)


def utf8_offsets(sample):
    data = sample.text.encode("utf-8")
    start = data.index(RESULTS.encode("utf-8"))
    return check(sample, sample.raw(RESULTS, start=start, end=start + len(RESULTS)))


def utf16_offsets(sample):
    units = sample.text.encode("utf-16-le")
    start = units.index(RESULTS.encode("utf-16-le")) // 2
    return check(sample, sample.raw(RESULTS, start=start, end=start + len(RESULTS)))


def newer_version(sample) -> CanonicalDocument:
    return CanonicalDocument.create(
        source_document_id=sample.document.source_document_id,
        canonicalization_version=sample.document.canonicalization_version,
        canonical_text=sample.text.replace("5%", "6%"),
    )


def span_from_previous_version(sample):
    return validate_span(
        newer_version(sample), sample.elements, sample.candidate(MARGINS)
    )


def text_changed_beneath_spans(sample):
    edited = sample.document.model_copy(
        update={"canonical_text": sample.text.replace("5%", "6%")}
    )
    return validate_span(edited, sample.elements, sample.candidate(MARGINS))


def stitched(sample, joiner: str):
    turn = sample.element(ElementType.SPEAKER_TURN, "CEO:")
    return check(
        sample,
        sample.raw(
            "Revenue rose 5%",
            end=sample.span_of(RESULTS).end,
            quote_text=f"Revenue rose 5%{joiner}{RESULTS}",
            element_id=turn.element_id,
        ),
    )


def two_ranges(sample):
    first, second = sample.span_of(RESULTS), sample.span_of(MARGINS)
    return check(
        sample,
        sample.raw(
            RESULTS, ranges=[[first.start, first.end], [second.start, second.end]]
        ),
    )


def end_past_the_text(sample):
    length = len(sample.text)
    return check(
        sample,
        sample.raw(
            MARGINS, start=length - 3, end=length + 5, quote_text=sample.text[-3:]
        ),
    )


def same_text_in_another_document(sample):
    other = CanonicalDocument.create(
        source_document_id="another-call",
        canonicalization_version=sample.document.canonicalization_version,
        canonical_text=sample.text,
    )
    return validate_span(other, sample.elements, sample.candidate(MARGINS))


def attributed_to(sample, needle: str, occurrence: int, element_type, holder: str):
    element = sample.element(element_type, holder)
    return check(sample, sample.raw(needle, occurrence, element_id=element.element_id))


def crossing_speaker_turns(sample):
    start = sample.span_of("Welcome to the call.").start
    end = sample.span_of("CEO: Revenue").end
    section = sample.element(ElementType.SECTION, "Prepared remarks")
    return check(
        sample,
        sample.raw(
            "Welcome to the call.",
            end=end,
            quote_text=sample.text[start:end],
            element_id=section.element_id,
        ),
    )


def chunk_offsets_stored_unconverted(sample):
    turn = sample.element(ElementType.SPEAKER_TURN, "CFO:")
    chunk = TextChunk.of(sample.document, turn.span)
    local = chunk.text.index(MARGINS)
    return check(sample, sample.raw(MARGINS, start=local, end=local + len(MARGINS)))


def local_span_past_its_chunk(sample):
    chunk = TextChunk.of(sample.document, sample.span_of(MARGINS))
    return chunk.to_document_span(TextSpan(start=0, end=len(MARGINS) + 1))


CASES = [
    # R3.2: offsets are strict integers counting code points.
    (
        "R3.2-offset-is-a-bool",
        lambda s: check(s, s.raw(MARGINS, start=True)),
        R.MALFORMED_RECORD,
    ),
    (
        "R3.2-offset-is-a-float",
        lambda s: check(s, s.raw(MARGINS, end=9.0)),
        R.MALFORMED_RECORD,
    ),
    (
        "R3.2-offset-is-a-string",
        lambda s: check(s, s.raw(MARGINS, start="3")),
        R.MALFORMED_RECORD,
    ),
    ("R3.2-utf8-byte-offsets", utf8_offsets, R.QUOTE_TEXT_MISMATCH),
    ("R3.2-utf16-code-unit-offsets", utf16_offsets, R.QUOTE_TEXT_MISMATCH),
    # R3.3 and V9 canonical version changes: changed text is a new version.
    (
        "R3.3-span-from-the-previous-version",
        span_from_previous_version,
        R.WRONG_DOCUMENT,
    ),
    (
        "R3.3-text-changed-beneath-spans",
        text_changed_beneath_spans,
        R.DOCUMENT_INTEGRITY,
    ),
    # R5.4 and V9 duplicated passages: context singles out one occurrence.
    (
        "R5.4-repeated-text-without-context",
        lambda s: check(s, s.raw(RESULTS, 1, prefix="", suffix="")),
        R.AMBIGUOUS_OCCURRENCE,
    ),
    (
        "R5.4-context-not-around-the-span",
        lambda s: check(s, s.raw(RESULTS, 1, prefix="CEO: ")),
        R.LOCATOR_MISMATCH,
    ),
    (
        "R5.4-locating-repeated-text-without-context",
        lambda s: resolve_locator(s.document, SpanLocator(exact=RESULTS)),
        R.AMBIGUOUS_OCCURRENCE,
    ),
    (
        "R5.4-locator-matching-nothing",
        lambda s: resolve_locator(s.document, SpanLocator(exact="Results were final.")),
        R.LOCATOR_NOT_FOUND,
    ),
    # R5.5 and V9 stitched spans: one record is one contiguous range.
    (
        "R5.5-stitched-with-an-ellipsis",
        lambda s: stitched(s, " \u2026 "),
        R.QUOTE_TEXT_MISMATCH,
    ),
    (
        "R5.5-joined-without-an-ellipsis",
        lambda s: stitched(s, " "),
        R.QUOTE_TEXT_MISMATCH,
    ),
    ("R5.5-two-ranges-in-one-record", two_ranges, R.MALFORMED_RECORD),
    # R6.1: bounds, identity, hash, text, and attribution.
    ("R6.1-end-past-the-text", end_past_the_text, R.SPAN_OUT_OF_BOUNDS),
    (
        "R6.1-empty-span",
        lambda s: check(s, s.raw(MARGINS, end=s.span_of(MARGINS).start)),
        R.MALFORMED_RECORD,
    ),
    (
        "R6.1-negative-start",
        lambda s: check(s, s.raw(MARGINS, start=-1)),
        R.MALFORMED_RECORD,
    ),
    (
        "R6.1-same-text-in-another-document",
        same_text_in_another_document,
        R.WRONG_DOCUMENT,
    ),
    (
        "R6.1-stale-hash",
        lambda s: check(
            s, s.raw(MARGINS, canonical_hash=hash_canonical_text(s.text + " "))
        ),
        R.CANONICAL_HASH_MISMATCH,
    ),
    (
        "R6.1-wrong-section",
        lambda s: attributed_to(s, MARGINS, 0, ElementType.SECTION, "Prepared remarks"),
        R.OUTSIDE_ELEMENT,
    ),
    (
        "R6.1-wrong-speaker-turn",
        lambda s: attributed_to(s, RESULTS, 1, ElementType.SPEAKER_TURN, "CEO:"),
        R.OUTSIDE_ELEMENT,
    ),
    # V9 speaker boundaries, invalid pointers, and chunk coordinates.
    ("V9-span-crossing-speaker-turns", crossing_speaker_turns, R.CROSSES_SPEAKER_TURN),
    (
        "V9-attribution-to-no-element",
        lambda s: check(s, s.raw(MARGINS, element_id="sentence-0-5")),
        R.UNKNOWN_ELEMENT,
    ),
    (
        "V9-pointer-to-no-element",
        lambda s: resolve_pointer(s.document, s.elements, "paragraph-0-16"),
        R.UNKNOWN_ELEMENT,
    ),
    (
        "V9-pointer-into-another-version",
        lambda s: resolve_pointer(
            newer_version(s), s.elements, s.elements[0].element_id
        ),
        R.WRONG_DOCUMENT,
    ),
    (
        "V9-chunk-offsets-stored-unconverted",
        chunk_offsets_stored_unconverted,
        R.QUOTE_TEXT_MISMATCH,
    ),
    ("V9-local-span-past-its-chunk", local_span_past_its_chunk, R.OUTSIDE_CHUNK),
    # R13.2: exactness has no tolerance; a near miss is a miss.
    (
        "R13.2-decomposed-accent",
        lambda s: check(
            s, s.raw(QUESTION, quote_text=unicodedata.normalize("NFD", QUESTION))
        ),
        R.QUOTE_TEXT_MISMATCH,
    ),
    (
        "R13.2-curly-apostrophe",
        lambda s: check(s, s.raw(MARGINS, quote_text=MARGINS.replace("'", "\u2019"))),
        R.QUOTE_TEXT_MISMATCH,
    ),
    (
        "R13.2-doubled-space",
        lambda s: check(
            s, s.raw(MARGINS, quote_text=MARGINS.replace(" held", "  held"))
        ),
        R.QUOTE_TEXT_MISMATCH,
    ),
    (
        "R13.2-changed-case",
        lambda s: check(s, s.raw(MARGINS, quote_text=MARGINS.lower())),
        R.QUOTE_TEXT_MISMATCH,
    ),
    (
        "R13.2-trailing-space",
        lambda s: check(s, s.raw(MARGINS, quote_text=MARGINS + " ")),
        R.QUOTE_TEXT_MISMATCH,
    ),
]


@pytest.mark.parametrize(
    ("case", "expected"),
    [pytest.param(case, expected, id=name) for name, case, expected in CASES],
)
def test_the_failure_class_is_rejected_with_its_reason(sample, case, expected) -> None:
    outcome = case(sample)
    assert isinstance(outcome, Rejection), outcome
    assert outcome.reason is expected, outcome.detail
    assert outcome.detail
    assert outcome.validator_version == VALIDATOR_VERSION


@pytest.mark.parametrize(
    ("needle", "occurrence"),
    [
        (MARGINS, 0),
        (RESULTS, 0),
        (RESULTS, 1),
        ("Welcome to the call.", 0),
        ("Revenue rose 5%", 0),
        (QUESTION, 0),
    ],
)
def test_every_row_starts_from_a_candidate_that_verifies(
    sample, needle: str, occurrence: int
) -> None:
    assert isinstance(check(sample, sample.raw(needle, occurrence)), VerifiedSpan)
```

Run the escape check:

```bash
python3 -c 'import sys; bad = {p: sorted({hex(ord(c)) for c in open(p, encoding="utf-8").read() if ord(c) > 127} - {"0xa7", "0x20ac"}) for p in sys.argv[1:]}; print({p: b for p, b in bad.items() if b} or "escapes intact")' packages/earnings-core/tests/test_failure_classes.py
```

Expected: `escapes intact`. If it prints a file name instead, re-extract that file
(Global Constraints, "Writing files from this plan") and rerun the check.

- [ ] **Step 2: Run them to verify they fail**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_public_api.py -q
```

Expected: exit 1, `3 failed`. The three are
`test_the_package_root_exports_exactly_the_public_api`,
`test_the_scaffold_placeholder_is_gone`, and `test_versions_are_pinned`.

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_failure_classes.py -q
```

Expected: exit 2, `1 error`, with
`ImportError: cannot import name 'VALIDATOR_VERSION' from 'earnings_core'`.

- [ ] **Step 3: Write the implementation**

Replace `packages/earnings-core/src/earnings_core/__init__.py` with:

```python
"""earnings-core: the contracts and exactness checks every other package builds on.

Contract schema version 1; docs/data-dictionary.md documents every field.
"""

from earnings_core._model import SCHEMA_VERSION
from earnings_core.artifacts import ArtifactRef, RightsStatus
from earnings_core.chunks import TextChunk
from earnings_core.documents import (
    CanonicalDocument,
    derive_doc_id,
    document_integrity_problem,
)
from earnings_core.elements import (
    LEVELED_TYPES,
    DocumentElement,
    ElementType,
    TableCellContext,
    derive_element_id,
)
from earnings_core.evidence import (
    SpanCandidate,
    VerifiedSpan,
    parse_span_candidate,
    validate_span,
)
from earnings_core.hashing import hash_canonical_text, sha256_hex
from earnings_core.locators import (
    SpanLocator,
    make_locator,
    occurrences,
    resolve_locator,
)
from earnings_core.masks import MaskCategory, MaskedDocument, OverlayMask, apply_masks
from earnings_core.rejections import VALIDATOR_VERSION, Rejection, RejectionReason
from earnings_core.spans import TextSpan
from earnings_core.structure import resolve_pointer, validate_elements

__all__ = [
    "LEVELED_TYPES",
    "SCHEMA_VERSION",
    "VALIDATOR_VERSION",
    "ArtifactRef",
    "CanonicalDocument",
    "DocumentElement",
    "ElementType",
    "MaskCategory",
    "MaskedDocument",
    "OverlayMask",
    "Rejection",
    "RejectionReason",
    "RightsStatus",
    "SpanCandidate",
    "SpanLocator",
    "TableCellContext",
    "TextChunk",
    "TextSpan",
    "VerifiedSpan",
    "apply_masks",
    "derive_doc_id",
    "derive_element_id",
    "document_integrity_problem",
    "hash_canonical_text",
    "make_locator",
    "occurrences",
    "parse_span_candidate",
    "resolve_locator",
    "resolve_pointer",
    "sha256_hex",
    "validate_elements",
    "validate_span",
]
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked --all-packages pytest packages/earnings-core/tests/test_public_api.py packages/earnings-core/tests/test_failure_classes.py -q
```

Expected: `41 passed`.

- [ ] **Step 5: Prove the table bites**

Disable the text-equality check, run the table, then restore the committed file:

```bash
python3 -c 'from pathlib import Path; p = Path("packages/earnings-core/src/earnings_core/evidence.py"); s = p.read_text(); old = "if candidate.quote_text != exact:"; assert s.count(old) == 1; p.write_text(s.replace(old, "if False:"))'
uv run --locked --all-packages pytest packages/earnings-core/tests/test_failure_classes.py -q
git checkout -- packages/earnings-core/src/earnings_core/evidence.py
uv run --locked --all-packages pytest packages/earnings-core/tests/test_failure_classes.py -q
```

Expected, first run: exit 1, `10 failed, 28 passed`. The failures include
`[R3.2-utf8-byte-offsets]`, `[R3.2-utf16-code-unit-offsets]` and
`[R5.5-stitched-with-an-ellipsis]`.

Expected, second run: `38 passed`, and `git status --short` no longer lists
`evidence.py`.

- [ ] **Step 6: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `170 passed`; `All checks passed!`; `76 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git add packages/earnings-core/src/earnings_core/__init__.py packages/earnings-core/tests/test_public_api.py packages/earnings-core/tests/test_failure_classes.py
git commit -m "feat(core): export the public API and the Stage 2 failure-class table"
```

---

### Task 12: The two-parser element contract and the gold vocabulary

**Files:**

- Create: `tests/contracts/test_element_schema_parsers.py`
- Create: `tests/contracts/test_gold_vocabulary.py`

**Interfaces:**

- Consumes:
  - from the package root (Task 11): `CanonicalDocument`, `DocumentElement`,
    `ElementType`, `LEVELED_TYPES`, `Rejection`, `RejectionReason`, `SpanLocator`,
    `TableCellContext`, `TextSpan`, `resolve_locator`, and `validate_elements`;
  - `lxml.html`, installed through `earnings-ingestion`'s dependency, since
    `--all-packages` syncs every member;
  - the eight committed `tests/fixtures/releases/*/gold.toml` files.
- Produces:
  - the browser spec's two-parser contract (D-15), ready for Stage 3 to rerun with
    the ported walker and the DOM/layout extractor;
  - evidence that every block type and level in the Stage 1 gold is a valid
    `DocumentElement`.
- These tests exercise finished code, so they pass as soon as they are written.
  Steps 4 and 5 prove they can fail.

- [ ] **Step 1: Write the two-parser contract test**

The HTML is synthetic and holds a heading, two paragraphs, a list, and a small
table. It repeats "Results are preliminary." once in a paragraph and once in a list
item, so the mapping reader meets text it cannot place exactly.

Create `tests/contracts/test_element_schema_parsers.py`:

```python
"""Two parser implementations emit one browser-neutral element schema.

Stand-ins, not the real pair (browser-rendering spec, Stage 2 verification): a
standard-library ``html.parser`` reader plays the canonicalizing parser, and an lxml
reader plays a second extractor that maps its blocks onto the first reader's
``CanonicalDocument``, the sole coordinate system (B5). Stage 3 reruns this contract
with the ported walker and the DOM/layout extractor in their place.
"""

import json
from dataclasses import dataclass
from html.parser import HTMLParser

import lxml.html
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    Rejection,
    RejectionReason,
    SpanLocator,
    TableCellContext,
    TextSpan,
    resolve_locator,
    validate_elements,
)

SOURCE = """<html><body>
<h1>Acme Reports Third Quarter Results</h1>
<p>Revenue rose 5% to $2.1 billion.</p>
<p>Results are preliminary.</p>
<ul><li>Margins expanded.</li><li>Results are preliminary.</li></ul>
<table>
<tr><th>Metric</th><th>Q3 2026</th></tr>
<tr><td>Net sales</td><td>$9.8</td></tr>
</table>
</body></html>"""

TYPES = {
    "h1": (ElementType.HEADING, 1),
    "p": (ElementType.PARAGRAPH, None),
    "li": (ElementType.LIST_ITEM, 1),
}
Row = tuple[tuple[str, bool], ...]


@dataclass(frozen=True)
class Block:
    """What a reader saw: a typed text block, or a table of (text, is_header) cells."""

    type: ElementType
    source_type: str
    text: str = ""
    level: int | None = None
    rows: tuple[Row, ...] = ()


class StdlibReader(HTMLParser):
    """Stand-in for the canonicalizing parser: standard-library parse events."""

    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[Block] = []
        self._parts: list[str] | None = None
        self._rows: list[list[tuple[str, bool]]] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in TYPES or tag in {"th", "td"}:
            self._parts = []
        elif tag == "tr":
            self._rows.append([])

    def handle_data(self, data: str) -> None:
        if self._parts is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            rows = tuple(tuple(row) for row in self._rows)
            self.blocks.append(Block(ElementType.TABLE, "html.parser:table", rows=rows))
            self._rows = []
        elif self._parts is not None and (tag in TYPES or tag in {"th", "td"}):
            text = " ".join("".join(self._parts).split())
            self._parts = None
            if tag in TYPES:
                element_type, level = TYPES[tag]
                self.blocks.append(
                    Block(element_type, f"html.parser:{tag}", text, level)
                )
            else:
                self._rows[-1].append((text, tag == "th"))


def stdlib_blocks(source: str) -> list[Block]:
    reader = StdlibReader()
    reader.feed(source)
    reader.close()
    return reader.blocks


def lxml_blocks(source: str) -> list[Block]:
    """Stand-in for a second extractor: an lxml tree walked in document order."""
    blocks: list[Block] = []
    for node in lxml.html.fromstring(source).iter("h1", "p", "li", "table"):
        if node.tag == "table":
            rows = tuple(
                tuple(
                    (" ".join(cell.text_content().split()), cell.tag == "th")
                    for cell in row.iter("th", "td")
                )
                for row in node.iter("tr")
            )
            blocks.append(Block(ElementType.TABLE, "lxml:table", rows=rows))
        else:
            element_type, level = TYPES[node.tag]
            text = " ".join(node.text_content().split())
            blocks.append(Block(element_type, f"lxml:{node.tag}", text, level))
    return blocks


def table_elements(
    document: CanonicalDocument, block: Block, spans: list[list[TextSpan]]
) -> list[DocumentElement]:
    """A table element over its cells, then each cell with its column's headers."""
    table = DocumentElement.create(
        document,
        ElementType.TABLE,
        TextSpan(start=spans[0][0].start, end=spans[-1][-1].end),
        source_type=block.source_type,
    )
    cells: list[DocumentElement] = []
    header_ids: dict[int, str] = {}
    for row_index, (row, row_spans) in enumerate(zip(block.rows, spans, strict=True)):
        for column, ((_, is_header), span) in enumerate(
            zip(row, row_spans, strict=True)
        ):
            headers = () if is_header else (header_ids[column],)
            cell = DocumentElement.create(
                document,
                ElementType.TABLE_CELL,
                span,
                parent_id=table.element_id,
                table_cell=TableCellContext(
                    row=row_index,
                    column=column,
                    is_header=is_header,
                    header_cell_ids=headers,
                ),
                source_type=block.source_type.replace(
                    "table", "th" if is_header else "td"
                ),
            )
            if is_header:
                header_ids[column] = cell.element_id
            cells.append(cell)
    return [table, *cells]


def canonicalize(
    blocks: list[Block],
) -> tuple[CanonicalDocument, list[DocumentElement]]:
    """The canonicalizing reader: blocks joined by blank lines, cells by tabs, rows by
    newlines, with every element's span fixed as the text is assembled."""
    pieces: list[str] = []
    starts: list[int] = []
    offset = 0
    for block in blocks:
        text = block.text
        if block.type is ElementType.TABLE:
            text = "\n".join("\t".join(cell for cell, _ in row) for row in block.rows)
        starts.append(offset)
        pieces.append(text)
        offset += len(text) + 2
    document = CanonicalDocument.create(
        source_document_id="contract-release",
        canonicalization_version="stand-in-stdlib-1",
        canonical_text="\n\n".join(pieces),
    )
    elements: list[DocumentElement] = []
    for block, start in zip(blocks, starts, strict=True):
        if block.type is ElementType.TABLE:
            spans: list[list[TextSpan]] = []
            position = start
            for row in block.rows:
                spans.append([])
                for cell, _ in row:
                    spans[-1].append(TextSpan(start=position, end=position + len(cell)))
                    position += len(cell) + 1
            elements.extend(table_elements(document, block, spans))
        else:
            span = TextSpan(start=start, end=start + len(block.text))
            elements.append(
                DocumentElement.create(
                    document,
                    block.type,
                    span,
                    level=block.level,
                    source_type=block.source_type,
                )
            )
    return document, elements


def map_onto(
    document: CanonicalDocument, blocks: list[Block]
) -> tuple[list[DocumentElement], list[Rejection]]:
    """The second reader: each text located exactly in the given document, or refused."""
    elements: list[DocumentElement] = []
    failures: list[Rejection] = []
    for block in blocks:
        texts = [cell for row in block.rows for cell, _ in row] or [block.text]
        located = [resolve_locator(document, SpanLocator(exact=text)) for text in texts]
        refused = [outcome for outcome in located if isinstance(outcome, Rejection)]
        if refused:
            failures.extend(refused)
            continue
        if block.type is ElementType.TABLE:
            cells = iter(located)
            spans = [[next(cells) for _ in row] for row in block.rows]
            elements.extend(table_elements(document, block, spans))
        else:
            elements.append(
                DocumentElement.create(
                    document,
                    block.type,
                    located[0],
                    level=block.level,
                    source_type=block.source_type,
                )
            )
    return elements, failures


def without_provenance(element: DocumentElement) -> dict:
    return element.model_dump(exclude={"source_type"})


def test_the_two_readers_see_the_same_blocks() -> None:
    def shape(blocks: list[Block]) -> list[tuple]:
        return [(b.type, b.text, b.level, b.rows) for b in blocks]

    assert shape(stdlib_blocks(SOURCE)) == shape(lxml_blocks(SOURCE))


def test_the_canonicalizing_reader_emits_a_valid_element_set() -> None:
    document, elements = canonicalize(stdlib_blocks(SOURCE))
    assert validate_elements(document, elements) == ()
    assert {element.source_type.partition(":")[0] for element in elements} == {
        "html.parser"
    }


def test_the_mapping_reader_emits_valid_elements_over_the_same_document() -> None:
    document, _ = canonicalize(stdlib_blocks(SOURCE))
    mapped, _ = map_onto(document, lxml_blocks(SOURCE))
    assert validate_elements(document, mapped) == ()
    assert {element.source_type.partition(":")[0] for element in mapped} == {"lxml"}


def test_elements_both_readers_place_agree_in_everything_but_provenance() -> None:
    document, canonical = canonicalize(stdlib_blocks(SOURCE))
    mapped, _ = map_onto(document, lxml_blocks(SOURCE))
    mapped_ids = {element.element_id for element in mapped}
    assert [without_provenance(e) for e in mapped] == [
        without_provenance(e) for e in canonical if e.element_id in mapped_ids
    ]
    assert len(mapped) == len(canonical) - 2


def test_repeated_text_fails_to_map_explicitly_never_to_the_first_match() -> None:
    document, canonical = canonicalize(stdlib_blocks(SOURCE))
    mapped, failures = map_onto(document, lxml_blocks(SOURCE))
    assert [failure.reason for failure in failures] == [
        RejectionReason.AMBIGUOUS_OCCURRENCE,
        RejectionReason.AMBIGUOUS_OCCURRENCE,
    ]
    mapped_ids = {element.element_id for element in mapped}
    unmapped = [e for e in canonical if e.element_id not in mapped_ids]
    assert [element.type for element in unmapped] == [
        ElementType.PARAGRAPH,
        ElementType.LIST_ITEM,
    ]
    assert {e.span.slice_of(document.canonical_text) for e in unmapped} == {
        "Results are preliminary."
    }


def test_both_readers_emit_records_of_the_one_schema() -> None:
    document, canonical = canonicalize(stdlib_blocks(SOURCE))
    mapped, _ = map_onto(document, lxml_blocks(SOURCE))
    fields = set(DocumentElement.model_fields)
    for element in [*canonical, *mapped]:
        payload = element.model_dump_json()
        assert set(json.loads(payload)) == fields
        assert DocumentElement.model_validate_json(payload) == element
```

- [ ] **Step 2: Write the gold-vocabulary test**

Create `tests/contracts/test_gold_vocabulary.py`:

```python
"""The element contract expresses every type and level in the Stage 1 gold.

Roadmap Stage 2 consumes V2's "Element types and nesting observed in the gold"
(docs/verification/V2-parser-fidelity.md); this reads the eight committed gold files.
"""

from pathlib import Path

import tomllib
from earnings_core import (
    LEVELED_TYPES,
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TextSpan,
)

RELEASES = Path(__file__).resolve().parents[1] / "fixtures" / "releases"


def gold_blocks() -> list[tuple[str, dict]]:
    blocks: list[tuple[str, dict]] = []
    for path in sorted(RELEASES.glob("*/gold.toml")):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        blocks.extend((path.parent.name, block) for block in data["blocks"])
    return blocks


def test_all_eight_gold_files_are_read() -> None:
    blocks = gold_blocks()
    assert len({fixture for fixture, _ in blocks}) == 8
    assert len(blocks) == 574


def test_every_gold_block_type_is_an_element_type() -> None:
    gold_types = {block["type"] for _, block in gold_blocks()}
    assert gold_types == {
        "footnote",
        "heading",
        "list_item",
        "page_artifact",
        "paragraph",
        "table",
    }
    assert gold_types <= {element_type.value for element_type in ElementType}


def test_every_gold_type_and_level_is_a_valid_element() -> None:
    document = CanonicalDocument.create(
        source_document_id="gold-vocabulary",
        canonicalization_version="test-1",
        canonical_text="x",
    )
    seen = {
        (ElementType(block["type"]), block.get("level")) for _, block in gold_blocks()
    }
    for element_type, level in seen:
        DocumentElement.create(
            document, element_type, TextSpan(start=0, end=1), level=level
        )
    assert seen == {
        (ElementType.HEADING, 1),
        (ElementType.HEADING, 2),
        (ElementType.HEADING, 3),
        (ElementType.HEADING, None),
        (ElementType.LIST_ITEM, 1),
        (ElementType.PARAGRAPH, None),
        (ElementType.FOOTNOTE, None),
        (ElementType.PAGE_ARTIFACT, None),
        (ElementType.TABLE, None),
    }


def test_gold_levels_sit_only_on_leveled_types() -> None:
    for fixture, block in gold_blocks():
        if "level" in block:
            assert ElementType(block["type"]) in LEVELED_TYPES, fixture
```

- [ ] **Step 3: Run them**

```bash
uv run --locked --all-packages pytest tests/contracts -q
```

Expected: `10 passed`.

- [ ] **Step 4: Prove the contract test bites**

Make `resolve_locator` fall back to the first match, run the contract, then restore
the committed file:

```bash
python3 -c 'from pathlib import Path; p = Path("packages/earnings-core/src/earnings_core/locators.py"); s = p.read_text(); old = "if len(starts) > 1:"; assert s.count(old) == 1; p.write_text(s.replace(old, "if False:"))'
uv run --locked --all-packages pytest tests/contracts/test_element_schema_parsers.py -q
git checkout -- packages/earnings-core/src/earnings_core/locators.py
```

Expected: exit 1, `2 failed, 4 passed`, with these two failures:

```
FAILED tests/contracts/test_element_schema_parsers.py::test_elements_both_readers_place_agree_in_everything_but_provenance
FAILED tests/contracts/test_element_schema_parsers.py::test_repeated_text_fails_to_map_explicitly_never_to_the_first_match
```

- [ ] **Step 5: Prove the gold-vocabulary test bites**

Stop list items carrying a level, run the test, then restore the committed file:

```bash
python3 -c 'from pathlib import Path; p = Path("packages/earnings-core/src/earnings_core/elements.py"); s = p.read_text(); old = "{ElementType.SECTION, ElementType.HEADING, ElementType.LIST_ITEM}"; assert s.count(old) == 1; p.write_text(s.replace(old, "{ElementType.SECTION, ElementType.HEADING}"))'
uv run --locked --all-packages pytest tests/contracts/test_gold_vocabulary.py -q
git checkout -- packages/earnings-core/src/earnings_core/elements.py
```

Expected: exit 1, `2 failed, 2 passed`, with these two failures:

```
FAILED tests/contracts/test_gold_vocabulary.py::test_every_gold_type_and_level_is_a_valid_element
FAILED tests/contracts/test_gold_vocabulary.py::test_gold_levels_sit_only_on_leveled_types
```

- [ ] **Step 6: Run the suite and lint**

```bash
uv run --locked --all-packages pytest tests/contracts -q
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `10 passed`; `180 passed`; `All checks passed!`; `78 files already
formatted`. `git status --short` lists only the two new test files.

- [ ] **Step 7: Commit**

```bash
git add tests/contracts/test_element_schema_parsers.py tests/contracts/test_gold_vocabulary.py
git commit -m "test(contracts): two readers emit one element schema; gold types are valid elements"
```

---

### Task 13: Data dictionary, current-state docs, and final verification

**Files:**

- Create: `docs/data-dictionary.md`
- Test: `tests/contracts/test_data_dictionary.py`
- Modify: `CLAUDE.md` (four passages about the current state)
- Modify: `README.md` (seven passages about the project status)

**Interfaces:**

- Consumes: the package root (Task 11).
- Produces:
  - `docs/data-dictionary.md`, which documents every field of the 12 contract models
    and every value of the four enums. It also states the schema version, the
    validator version, and the ID conventions, as A §191 requires.
  - `tests/contracts/test_data_dictionary.py`, which fails whenever a contract
    gains, loses, or renames a field or value without a matching dictionary update.
- How the drift test reads the dictionary:
  - Each model or enum has a `` ### `Name` `` heading.
  - Under each heading is a table whose first column holds the field or value in
    backticks.

- [ ] **Step 1: Write the failing test**

Create `tests/contracts/test_data_dictionary.py`:

```python
"""docs/data-dictionary.md documents every field and value of the core contracts.

AGENTS.md §191: document public interfaces and update the data dictionary in the
same change. A contract that gains, loses, or renames a field fails here.
"""

import re
from enum import StrEnum
from pathlib import Path

import earnings_core as core
import pytest
from pydantic import BaseModel

DICTIONARY = Path(__file__).resolve().parents[2] / "docs" / "data-dictionary.md"
MODELS = [
    core.TextSpan,
    core.ArtifactRef,
    core.CanonicalDocument,
    core.TableCellContext,
    core.DocumentElement,
    core.SpanLocator,
    core.TextChunk,
    core.SpanCandidate,
    core.VerifiedSpan,
    core.OverlayMask,
    core.MaskedDocument,
    core.Rejection,
]
ENUMS = [core.RightsStatus, core.ElementType, core.MaskCategory, core.RejectionReason]


def documented(name: str) -> set[str]:
    """The first-column code spans of the table under the heading for ``name``."""
    text = DICTIONARY.read_text(encoding="utf-8")
    heading = f"### `{name}`\n"
    assert heading in text, f"docs/data-dictionary.md has no section for {name}"
    section = text.split(heading, 1)[1].split("\n#", 1)[0]
    return set(re.findall(r"^\| `([^`]+)` \|", section, flags=re.MULTILINE))


@pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__name__)
def test_every_field_is_documented(model: type[BaseModel]) -> None:
    assert documented(model.__name__) == set(model.model_fields)


@pytest.mark.parametrize("enum", ENUMS, ids=lambda enum: enum.__name__)
def test_every_value_is_documented(enum: type[StrEnum]) -> None:
    assert documented(enum.__name__) == {member.value for member in enum}


def test_the_documented_versions_are_the_packages() -> None:
    text = DICTIONARY.read_text(encoding="utf-8")
    assert f"schema version {core.SCHEMA_VERSION}\n" in text
    assert f'`"{core.VALIDATOR_VERSION}"` (`earnings_core.VALIDATOR_VERSION`)' in text
```

- [ ] **Step 2: Run it to verify it fails**

```bash
uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q
```

Expected: exit 1, `17 failed`, each with a `FileNotFoundError` for
`docs/data-dictionary.md`.

- [ ] **Step 3: Write the data dictionary**

Create `docs/data-dictionary.md`:

```markdown
# Data dictionary

The shared contracts, their fields, and their versions (AGENTS.md §187–191). Each
table below lists every field or value of one contract;
`tests/contracts/test_data_dictionary.py` fails when a field or value changes without
this file changing too.

## earnings-core contracts, schema version 1

- **Package.** `packages/earnings-core`, imported as `earnings_core`.
- **Schema version.** `1` (`earnings_core.SCHEMA_VERSION`). Every top-level record
  carries it as `schema_version`, and a payload with another version is refused.
- **Validator version.** `"1"` (`earnings_core.VALIDATOR_VERSION`), stamped on every
  `Rejection` and `VerifiedSpan`. Caches key on it (R14.6); bump it whenever a check
  changes.
- **Compatibility.** This is the first version. No earlier schema exists, so nothing
  migrates and no cache or output is invalidated (A §187).
- **Conventions.**
  - Offsets are zero-based Unicode code points over a half-open `[start, end)`,
    never UTF-8 bytes, UTF-16 code units, or model tokens (R3.2).
  - Every span holds text: `start < end`. An empty table cell is not an element.
  - Hashes are SHA-256, written as 64 lowercase hexadecimal characters. The canonical
    hash covers the canonical text's UTF-8 bytes (R3.1).
  - Records are frozen, refuse unknown fields, and are strictly typed: a bool, float,
    or numeric string is never an offset.

### Identifiers

| Identifier | Derivation | Example |
| --- | --- | --- |
| `doc_id` | `<source_document_id>@<canonicalization_version>#<first 16 hex of canonical_hash>` | `0000007332-09-000032_ex-99@walker-w16.norm-1#<16 hex>` |
| `element_id` | `<type>-<start>-<end>` | `paragraph-120-450` |

Changed canonical text is always a new `doc_id` (R3.3). An `element_id` is unique
within one document version; the pair (`doc_id`, `element_id`) is unique across
versions. Both derivations were chosen on 2026-09-25 (plan 3, Plan decisions).

### `TextSpan`

A half-open range of code points in one canonical text.

| Field | Type | Meaning |
| --- | --- | --- |
| `start` | int ≥ 0 | Offset of the first code point |
| `end` | int > `start` | Offset one past the last code point |

### `ArtifactRef`

A stored artifact, identified by the SHA-256 of its bytes.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Contract schema version |
| `content_sha256` | 64 lowercase hex | SHA-256 of the artifact's bytes |
| `media_type` | string | Lowercase media type, e.g. `text/plain; charset=utf-8` |
| `storage_ref` | string | Repository-relative path or non-file URI; never an absolute local path |
| `rights_status` | `RightsStatus` | What may be done with the content |
| `rights_basis` | non-blank string | Why: the register entry or terms that decide the status |

### `RightsStatus`

| Value | Meaning |
| --- | --- |
| `redistributable` | A recorded basis permits committing and exporting the content |
| `local_only` | Retain locally; never commit or export. Unclear rights are recorded this way |
| `restricted` | Terms forbid redistributing the text; keep locators and local features (R2.1) |

### `CanonicalDocument`

One immutable, hashed version of a source document's text (R3.1, R3.3). The
`canonical_documents` dataset of AGENTS.md §359.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Contract schema version |
| `doc_id` | string | Derived ID of this version (see Identifiers) |
| `source_document_id` | ID part | The source record this text came from |
| `canonicalization_version` | ID part | The whole canonicalization policy: parser, rules, and normalization |
| `canonical_text` | non-empty string | The text every offset indexes; never holds a lone surrogate |
| `canonical_hash` | 64 lowercase hex | SHA-256 of `canonical_text` as UTF-8 |
| `text_artifact` | `ArtifactRef` or null | Where the same UTF-8 bytes are stored, if they are |

An ID part is letters, digits, and `. _ : -` only. Parser and library versions are
run-manifest provenance, recorded by Stage 3, not document fields.

### `ElementType`

| Value | Meaning |
| --- | --- |
| `section` | A run of content under one heading, or a transcript section |
| `heading` | A heading; may carry a level |
| `paragraph` | A paragraph of body text |
| `list_item` | A list item; its level is the list's nesting depth |
| `sentence` | A sentence within a paragraph, list item, or turn |
| `footnote` | A footnote or note |
| `table` | A table; the parent of its cells |
| `table_cell` | One non-empty cell, with its grid position and headers |
| `speaker_turn` | One speaker's uninterrupted turn in a transcript |
| `page_artifact` | A running header or footer, page number, or filing banner |
| `other` | Anything a parser cannot type more precisely |

### `TableCellContext`

A table cell's position and header context (R4.1, R4.2).

| Field | Type | Meaning |
| --- | --- | --- |
| `row` | int ≥ 0 | Row index in the table's full grid, empty cells counted |
| `column` | int ≥ 0 | Column index in the table's full grid, empty cells counted |
| `row_span` | int ≥ 1 | Rows the cell covers |
| `column_span` | int ≥ 1 | Columns the cell covers |
| `is_header` | bool | Whether the cell is a header cell |
| `header_cell_ids` | tuple of `element_id` | Header cells of the same table that label this cell |

### `DocumentElement`

One typed structural unit of one document version (R4.1). The
`document_sections` / `speaker_turns` datasets of AGENTS.md §360.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Contract schema version |
| `element_id` | string | Derived from `type` and `span` (see Identifiers) |
| `doc_id` | string | The document version the element belongs to |
| `type` | `ElementType` | What kind of unit it is |
| `span` | `TextSpan` | Where it lies in the canonical text |
| `parent_id` | `element_id` or null | The containing element; parents precede children |
| `level` | int ≥ 1 or null | Outline or nesting depth; `section`, `heading`, and `list_item` only |
| `table_cell` | `TableCellContext` or null | Required on `table_cell` elements, forbidden elsewhere |
| `source_type` | string | The producing parser's own name for the unit, e.g. `lxml:h1` |

In a valid element set any two spans nest or are disjoint.

### `SpanLocator`

Exact text with the words around it (R5.4). Context grows one whole word at a time
on each side until one occurrence remains.

| Field | Type | Meaning |
| --- | --- | --- |
| `exact` | non-empty string | The text itself |
| `prefix` | string | The words just before it; empty when `exact` occurs once |
| `suffix` | string | The words just after it; empty when `exact` occurs once |

### `TextChunk`

A view of one document handed to a model or parser; local offsets convert back
before evidence is stored (A §508).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Contract schema version |
| `doc_id` | string | The document version it views |
| `canonical_hash` | 64 lowercase hex | That version's canonical hash |
| `span` | `TextSpan` | The chunk's range in the document |
| `text` | string | Exactly the document's characters over `span` |

### `SpanCandidate`

A proposed evidence span before verification: one contiguous range (R5.5).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Contract schema version |
| `doc_id` | string | The document version it claims |
| `canonical_hash` | 64 lowercase hex | That version's hash, as the candidate stored it |
| `start` | int ≥ 0 | Offset of the first code point |
| `end` | int > `start` | Offset one past the last code point |
| `quote_text` | string | The text claimed to lie at `[start, end)` |
| `element_id` | string | The element the span is attributed to, which must contain it |
| `prefix` | string | Context before the span (R5.4) |
| `suffix` | string | Context after the span (R5.4) |

### `VerifiedSpan`

A span that passed every check (R6.1). Its `quote_text` is sliced from the canonical
text, never copied from a candidate (A §523).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Contract schema version |
| `doc_id` | string | The verified document version |
| `canonical_hash` | 64 lowercase hex | Its canonical hash |
| `start` | int ≥ 0 | Offset of the first code point |
| `end` | int > `start` | Offset one past the last code point |
| `quote_text` | string | `canonical_text[start:end]` |
| `element_id` | string | The element that contains the span |
| `prefix` | string | Context before the span |
| `suffix` | string | Context after the span |
| `validator_version` | string | The validator that accepted it |

### `MaskCategory`

| Value | Meaning |
| --- | --- |
| `safe_harbor` | Forward-looking-statement safe-harbor language |
| `non_gaap_disclaimer` | A non-GAAP measure disclaimer |
| `repeated_legal` | Other repeated legal text |

### `OverlayMask`

One boilerplate span marked by one boilerplate policy version (R3.4). It never
changes the text or its offsets.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Contract schema version |
| `doc_id` | string | The document version it overlays |
| `canonical_hash` | 64 lowercase hex | That version's canonical hash |
| `span` | `TextSpan` | The masked range |
| `category` | `MaskCategory` | The kind of boilerplate |
| `policy_id` | ID part | The boilerplate policy that marked it |
| `policy_version` | ID part | That policy's version |

### `MaskedDocument`

A document with the masks one policy version computed over it. An in-memory view,
not a persisted record.

| Field | Type | Meaning |
| --- | --- | --- |
| `document` | `CanonicalDocument` | The unchanged document |
| `policy_id` | ID part | The policy that ran, even if it found nothing |
| `policy_version` | ID part | That policy's version |
| `masks` | tuple of `OverlayMask` | Every mask the policy found |

### `Rejection`

Why a check refused a record (R6.2: rejections stay auditable).

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Contract schema version |
| `reason` | `RejectionReason` | The failure class |
| `detail` | string | What failed, naming the record or element |
| `validator_version` | string | The validator that refused it |

### `RejectionReason`

`parse_span_candidate` records `malformed_record`. `validate_span` then runs its checks
in the order of the next ten rows and records the first failure.

| Value | Meaning |
| --- | --- |
| `malformed_record` | Wrong types, missing or extra fields, or a non-integer offset (R3.2, R5.5) |
| `document_integrity` | The document's own hash or `doc_id` disagrees with its text (R6.1, R3.3) |
| `wrong_document` | The record names another document or version (R6.1, R3.3) |
| `canonical_hash_mismatch` | The record's stored hash is not the document's (R6.1) |
| `span_out_of_bounds` | The span runs past the canonical text (R6.1) |
| `quote_text_mismatch` | `quote_text` is not exactly `canonical_text[start:end]` (R6.1, R5.5, R13.2) |
| `unknown_element` | A pointer or attribution names no element of the document (R5.1, V9) |
| `outside_element` | The span is not inside its attributed element (R6.1) |
| `crosses_speaker_turn` | The span runs across a speaker-turn boundary (A §585, V9) |
| `locator_mismatch` | The stored prefix or suffix is not the text around the span (R5.4) |
| `ambiguous_occurrence` | Repeated text whose context does not single out one occurrence (R5.4) |
| `locator_not_found` | No occurrence matches a locator (R5.4) |
| `outside_chunk` | A chunk-local span runs past its chunk (A §508, V9) |
| `element_id_mismatch` | An element's ID is not derived from its type and span (R4.1) |
| `duplicate_element` | Two elements share an ID (R4.1) |
| `unknown_parent` | A parent ID names no element of the set (R4.1) |
| `parent_order` | A child precedes its parent (R4.1) |
| `outside_parent` | A child's span is not inside its parent's (R4.1) |
| `crossing_elements` | Two spans overlap without nesting (R4.1) |
| `table_cell_parent` | A table cell's parent is not a table (R4.1, R4.2) |
| `invalid_header_reference` | A header reference names no header cell of the same table (R4.2) |
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q
```

Expected: `17 passed`.

- [ ] **Step 5: Prove the drift test bites**

Rename one documented field, run the test, then restore the file:

```bash
cp docs/data-dictionary.md /tmp/data-dictionary.md.orig
python3 -c 'from pathlib import Path; p = Path("docs/data-dictionary.md"); s = p.read_text(); old = "| `rights_basis` |"; assert s.count(old) == 1; p.write_text(s.replace(old, "| `rights_basys` |"))'
uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q
cp /tmp/data-dictionary.md.orig docs/data-dictionary.md && rm /tmp/data-dictionary.md.orig
uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q
```

Expected, first run: exit 1, `1 failed, 16 passed`, with
`FAILED tests/contracts/test_data_dictionary.py::test_every_field_is_documented[ArtifactRef]`.

Expected, second run: `17 passed`.

- [ ] **Step 6: Run the suite and lint**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `197 passed`; `All checks passed!`; `79 files already formatted`.

- [ ] **Step 7: Commit**

```bash
git add docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "docs: add the earnings-core data dictionary with a drift test"
```

- [ ] **Step 8: Update the current-state passages in CLAUDE.md and README.md**

The script replaces exact passages. Each must match exactly once, or the script
stops before writing anything to that file. It stamps the README's status line with
today's date.

````bash
python3 - <<'EOF'
from datetime import date
from pathlib import Path

TODAY = date.today().isoformat()
EDITS = [
    (
        "CLAUDE.md",
        """This repo is documentation-first: its only working code is the Stage 1 investigation harness in `expirements/parser-fidelity/`, its packages are still `hello()` scaffolds, and the rest is instructions.""",
        """This repo is documentation-first: its working code is the Stage 1 investigation harness in `expirements/parser-fidelity/` and the Stage 2 contracts in `packages/earnings-core`; the other packages are still `hello()` scaffolds, and the rest is instructions.""",
    ),
    (
        "CLAUDE.md",
        """## Current state: Stage 1 complete, packages still scaffold""",
        """## Current state: Stages 1 and 2 complete; three packages still scaffold""",
    ),
    (
        "CLAUDE.md",
        """Packages and `apps/earnings-pipeline` still contain only `hello()` stubs, and pytest configuration is still Stage 2's (see "Commands" below). `data/` is gitignored and holds only local, uncommitted material: fetched pages under `data/raw/` and Stage 1 run outputs under `data/runs/`; `config/`, `prompts/`, `codebooks/`, `tests/contracts/` and `tests/integration/` are empty directories.""",
        """Stage 2 of the roadmap (core evidence spine, plan 3, `specs/plans/completed/3-core-evidence-spine.md`) is done:

- `packages/earnings-core` holds the shared contracts, schema version 1: `TextSpan`, `CanonicalDocument`, `DocumentElement`, `ArtifactRef`, `OverlayMask`, `SpanLocator` and `TextChunk`, with the exactness checks `validate_span` and `validate_elements`. Every refusal is a `Rejection` carrying a `RejectionReason`. `docs/data-dictionary.md` documents every field, and `tests/contracts/test_data_dictionary.py` fails if the two drift apart.
- IDs are derived: `doc_id` is `<source_document_id>@<canonicalization_version>#<first 16 hex of the canonical hash>`, and `element_id` is `<type>-<start>-<end>`.
- The root `pyproject.toml` configures pytest (see "Commands" below).

`earnings-ingestion`, `earnings-themes` and `apps/earnings-pipeline` still contain only `hello()` stubs. `data/` is gitignored and holds only local, uncommitted material: fetched pages under `data/raw/` and Stage 1 run outputs under `data/runs/`; `config/`, `prompts/`, `codebooks/` and `tests/integration/` are empty directories.""",
    ),
    (
        "CLAUDE.md",
        """`[tool.ruff] extend-exclude = ["*.md"]`, which keeps Ruff from reformatting code blocks in the
preserved Markdown. **Not yet configured:** pytest. There is no registered `live` marker, no
import mode to keep same-named test modules across members from colliding, and no `testpaths`.
""",
        """`[tool.ruff] extend-exclude = ["*.md"]`, which keeps Ruff from reformatting code blocks in the
preserved Markdown. Stage 2 added `[tool.pytest]`: `--import-mode=importlib`, so members may
repeat a test module's name; `strict = true`; a registered `live` marker; and
`testpaths = ["packages", "apps", "tests"]`. The frozen Stage 1 harness still needs
`--import-mode=prepend`, which its own command passes.
""",
    ),
    (
        "README.md",
        """> **Project status (2026-09-25): Stage 1 complete; packages still scaffold.** The
> `uv` workspace, package boundaries, dependency groups, specifications, and staged
> roadmap exist, and Stage 1's parser investigation is finished. The Python
> packages still contain placeholder APIs; there is no operational pipeline,
> command-line interface, package test suite, approved theme codebook, or published
> dataset yet.""",
        """> **Project status (YYYY-MM-DD): Stages 1 and 2 complete.** The `uv` workspace,
> package boundaries, specifications, and staged roadmap exist; Stage 1's parser
> investigation is finished; and `earnings-core` holds the shared evidence contracts
> and exactness checks, with an offline test suite. The other packages still contain
> placeholder APIs; there is no operational pipeline, command-line interface,
> approved theme codebook, or published dataset yet.""",
    ),
    (
        "README.md",
        """| `packages/earnings-core/` | Shared contracts, identifiers, hashes, provenance, and pure span helpers | Scaffold only |""",
        """| `packages/earnings-core/` | Shared contracts, identifiers, hashes, provenance, and pure span helpers | Stage 2 contracts and exactness checks (schema v1) |""",
    ),
    (
        "README.md",
        """| Source notes, the release source register, verification records V1 and V2, and ADR 0001 |""",
        """| Source notes, the release source register, verification records V1 and V2, ADR 0001, and the `earnings-core` data dictionary |""",
    ),
    (
        "README.md",
        """stages. Stage 1 is complete; Stage 2 is next.""",
        """stages. Stages 1 and 2 are complete; Stage 3 is next.""",
    ),
    (
        "README.md",
        """The next milestone is **Stage 2: core evidence spine**, which gives
`earnings-core` the contracts and exactness validator that every later stage
builds on.""",
        """**Stage 2: core evidence spine** is complete. `earnings-core` now holds the
contracts every later stage builds on: hashed, versioned canonical documents;
typed elements with derived IDs and code-point spans; overlay masks; span
locators; and an exactness validator with no tolerance. The
[data dictionary](docs/data-dictionary.md) documents every field. The next
milestone is **Stage 3: structure-aware canonicalization**.""",
    ),
    (
        "README.md",
        """These imports currently expose only placeholder package functions. They are a
workspace smoke check, not proof that the research pipeline exists.""",
        """`earnings_core` exposes the Stage 2 contracts; the other three still expose only
placeholder functions. The import is a workspace smoke check, not proof that the
research pipeline exists.""",
    ),
    (
        "README.md",
        """Run the checks that are currently configured:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
```

There is no test suite or CI configuration yet. Stage 2 of the roadmap adds the
root pytest configuration, offline contract tests, and the `live` marker. Once
those paths exist, the intended default test command is:

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live"
```
""",
        """Run the configured checks:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked --all-packages pytest packages apps tests -m "not live"
```

The root `pyproject.toml` configures pytest. Test modules are imported by path,
so members may reuse a module name; unknown markers and configuration keys are
errors; and a test that needs the network, credentials, or a billable service
carries the `live` marker and runs only with `-m live`. The Stage 1 harness keeps
its own command, given under "Current roadmap". There is no CI configuration yet.
""",
    ),
]
texts: dict[str, str] = {}
for name, old, new in EDITS:
    text = texts.setdefault(name, Path(name).read_text(encoding="utf-8"))
    count = text.count(old)
    assert count == 1, f"{name}: {count} matches for {old[:60]!r}"
    texts[name] = text.replace(old, new.replace("YYYY-MM-DD", TODAY))
for name, text in texts.items():
    Path(name).write_text(text, encoding="utf-8")
print(f"applied {len(EDITS)} edits")
EOF
````

Expected: `applied 11 edits`. If an assertion fires, the passage changed after this
plan was written. Stop and show the user the current passage rather than improvise
a replacement.

- [ ] **Step 9: Check the edits**

```bash
git diff --stat
grep -n "hello()" CLAUDE.md README.md
```

Expected:

- `git diff --stat` lists only `CLAUDE.md` and `README.md`.
- The `grep` prints two lines, both from `CLAUDE.md` and none from `README.md`:
  - line 7, "the other packages are still `hello()` scaffolds";
  - the new current-state paragraph, "`earnings-ingestion`, `earnings-themes` and
    `apps/earnings-pipeline` still contain only `hello()` stubs".

  Those three still are scaffolds.

- [ ] **Step 10: Human gate — the README wording**

The README's status passages are the user's prose. Show the user
`git diff README.md CLAUDE.md` and ask them to approve the wording or supply their
own. Apply any change they ask for. If they change a passage the steps below check,
adjust that check to match. Do not commit until they approve.

- [ ] **Step 11: Final verification**

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live" -q
uv run --locked --all-packages pytest -q
uv run --locked --all-packages pytest -m live -q
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
uv run --locked ruff check . && uv run --locked ruff format --check .
uv lock --check
git diff main --stat -- uv.lock
uv run --locked python -c "import earnings_core, earnings_ingestion, earnings_themes, earnings_pipeline"
```

Expected, in order:

1. `197 passed`.
2. `197 passed`. With no arguments, pytest collects `testpaths`.
3. Exit 5, `197 deselected`. No `live` test exists yet, and exit 5 means none was
   selected.
4. `169 passed`: the harness is unchanged.
5. `All checks passed!` and `79 files already formatted`.
6. Exit 0, `Resolved 140 packages`.
7. No output: `uv.lock` is unchanged.
8. Exit 0 and no output: the README's workspace smoke check.

- [ ] **Step 12: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs: describe Stage 2 as complete in CLAUDE.md and the README"
git status --short
```

Expected: the last command prints nothing.

---

## Handoffs

Completion's roadmap reconcile carries each block below into the named stage's
entry, so a later session finds it without this plan.

### To the Stage 3 brainstorming pass (structure-aware canonicalization)

1. **Rerun the two-parser contract with the real pair.**
   - `tests/contracts/test_element_schema_parsers.py` states the contract with
     stand-ins (D-15).
   - Stage 3 reruns its assertions with the ported walker as the canonicalizing
     parser and the DOM/layout extractor as the mapping reader.
   - B5 requires that browser-derived elements map exactly onto canonical spans or
     are rejected with an explicit alignment failure.
2. **Alignment failures.**
   - The stand-in records `ambiguous_occurrence` or `locator_not_found`.
   - Decide whether Stage 3 needs a reason of its own, such as `alignment_failed`.
   - Adding a `RejectionReason` bumps `VALIDATOR_VERSION` and updates the data
     dictionary in the same change.
3. **R4.2's narrative and cell rule is Stage 3's exit test (D-9).**
   `validate_elements` checks only nesting, parent types, and header references.
4. **Table grids.** Populate `TableCellContext` from real tables:
   - rows and columns count empty cells, which are not elements (D-10);
   - record each cell's header cell IDs;
   - Pharmacyclics' `<pre>` tables have no HTML grid (V2's gold notes).
5. **Version naming (D-5).**
   - Choose the `canonicalization_version` scheme.
   - Record the parser and library versions in the run manifest (A §412).
   - Decide whether a separate `parser_version` field is worth a schema bump.
6. **Boilerplate policy (D-18).** Compute masks from a versioned policy, and build
   `MaskedDocument`s with `apply_masks`. Choose the `policy_id` and `policy_version`
   naming.
7. **Page artifacts.**
   - `page_artifact` is an element type; the gold uses it for running headers and
     footers.
   - Decide whether page artifacts are masked, excluded from analysis eligibility,
     or both.
8. **UTF-16 conversion at the browser boundary (D-17).** Capture code converts DOM
   offsets to code points before it builds a `TextSpan`.
9. **Browser records stay in ingestion (B2, B3).**
   - A rendered-capture record, and every engine, viewport, layout, or screenshot
     field, lives in `earnings-ingestion` behind the optional `browser-capture`
     extra.
   - Task 1's boundary tests already fail if core or themes imports a browser
     package.
10. **V9's remaining cases** (the roadmap's Stage 3 Exit):
    - Unicode and whitespace normalization;
    - sentence splitting around financial abbreviations and decimals.
11. **Plan 1's open deferred item still applies:** "Carry V2's findings into Stage 3".

### To Stage 4 (point-in-time DJIA cohort)

- **What it consumes.**
  - `sha256_hex` and `ArtifactRef`, as its provenance primitives: content hash,
    media type, portable storage reference (D-12), and rights status with its basis
    (D-3).
  - The root pytest configuration and its `live` marker (Task 1).
- **What core leaves to Stage 4.** Retrieval metadata is not in core: the source
  URL, `retrieved_at`, and request parameters. Stage 4 defines those records at its
  own grain, or proposes a core addition as a schema bump.
- **For the reconcile.** Narrow Stage 4's Consumes line from "provenance and hashing
  primitives" to these names.

### To Stage 7 (evidence selection and verification)

- **Pointers.** The model returns element IDs, and `resolve_pointer` turns them into
  spans (R5.1).
- **Parse, then verify.** Parse untrusted model output with `parse_span_candidate`,
  then verify it with `validate_span`. A `VerifiedSpan`'s `quote_text` is sliced by
  code (A §523).
- **Check the element set first.** Run `validate_elements` once per document before
  verifying spans against its elements (D-8).
- **Chunks.** Build chunks with `TextChunk.of`. Convert chunk-local spans with
  `to_document_span` before storing anything (A §508).
- **Repeated text.** `make_locator` supplies the prefix and suffix (R5.4).
- **Rejections and caching.** `Rejection` is the auditable rejection record (R6.2),
  and `VALIDATOR_VERSION` belongs in the R14.6 cache key.
- **What stays Stage 7's (D-20).** The retry, drop, and storage policy around these
  checks.

### To the Stage 10 plan (cited export)

- **Highlights.** Derive every highlight from a `VerifiedSpan`'s offsets, and
  text-fragment context from `make_locator`'s whole words (R7.1, D-4).
- **Never re-verify from rendered output (B6).** Never verify a quote by re-parsing
  HTML, OCR, a screenshot, or browser-selected text.
- **Masks.** `MaskedDocument.masks_overlapping` identifies masked evidence for the
  headline exclusion (R3.4).
- **Rights.** `RightsStatus` and `rights_basis` gate whether source-rendered or
  screenshot artifacts may be retained or exported (the browser spec's Stage 10
  verification).
- **Offsets.** Convert code points to UTF-16 at the browser boundary (D-17).

### To Stage 13 (transcripts)

- **What waits for Stage 13.** Speaker role, name, and attribution status arrive as a
  schema bump, on `DocumentElement` or on a companion record (D-16).
- **What is already enforced.** `crosses_speaker_turn` enforces the turn boundary
  (A §585).

## Completion

After Task 13, run the final whole-branch review, then:

1. **Plan Completion Protocol** (writing-plans).
   - Run the resolve-before-defer gate.
   - Mark up this plan: tick the steps, add `> Deviation:` notes, and add the status
     header.
2. **Stamp.** Append a blank line and these two lines to the end of
   `specs/evidence-linked-theme-extraction.md`, whose last section is Rollout. Put
   the completion date in place of `YYYY-MM-DD`.

   ```
   > Stage 2: COMPLETE (YYYY-MM-DD) — implemented by plan 3 (specs/plans/completed/3-core-evidence-spine.md).
   > Next: resume the roadmap.
   ```

3. **Deferred items.** In `specs/deferred_items.md`:
   - Tick the open item under `## browser-rendering-integration — 2026-09-24`, ending
     it with `→ done in plan 3 (specs/plans/completed/3-core-evidence-spine.md)`.
     This plan does its contract work (Tasks 1–12, D-15) and leaves the handoffs
     above for the Stage 3 brainstorming pass and the Stage 10 plan.
   - Append this plan's own deferred items, if any, under
     a `## 3-core-evidence-spine — YYYY-MM-DD` heading, with the completion date.
   - Commit steps 1–3 together as
     `docs(specs): mark up plan 3, stamp Stage 2, and record deferred items`.
4. **Backlog triage.** Run
   `uv run --no-project --python 3.13 python ~/.claude/skills/writing-plans/scripts/deferred_stats.py`
   and report its summary line.
5. **Retire.**
   - Run `git mv specs/plans/3-core-evidence-spine.md specs/plans/completed/` in one
     `chore(specs): retire plan 3` commit.
   - Do not retire or move `specs/evidence-linked-theme-extraction.md` (D-19).
   - This plan's paths are plain text, not Markdown links, so nothing needs
     re-pointing.
6. **Roadmap.** Run derive-roadmap's reconcile step:
   - tick Stage 2;
   - re-validate the later stages against what shipped;
   - carry the Handoffs above into the entries for Stages 3, 4, 7, 10 and 13.

   Commit as `docs(roadmap): tick Stage 2 and reconcile the later stages`.
7. **Integrate** with finishing-a-development-branch: open a pull request from
   `stage-2-core-evidence-spine` to `main`, as Stage 1 did.
8. **Report.**
   - State the commands actually run and their results.
   - State that no model was called.
   - State that no live test ran, because none exists yet.
