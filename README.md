# earnings-themes

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://lowmason.github.io/earnings-themes/)

earnings-themes is an ongoing research project about what large US companies say
in their quarterly earnings releases. It builds evidence-linked research
infrastructure for company data and earnings themes. It verifies every quote as an
exact span of versioned canonical text, and it codes themes against a frozen,
versioned codebook.

**Research status (2026-11-15): work in progress.** This is a research project, not
a finished tool or dataset. The pipeline is built and tested on synthetic fixtures.
A feasibility pilot on 40 real earnings events is under way. No theme dataset and
no research finding about earnings themes is published yet. Interfaces, schemas and
results can change.

## Research aims

The project asks which themes companies raise in their earnings releases. It also
asks how those themes differ across firms, fiscal periods, document types and
speaker roles. Each answer must trace back to the exact source words that support
it.

This monorepo is being built around two connected research capabilities:

1. **Company and document ingestion** — connect a dated company universe to
   issuer identifiers, reported industry and employment, disclosed subsidiaries,
   observable locations, and source earnings documents with auditable provenance.
2. **Earnings theme extraction** — extract quote-claim pairs, verify every quote
   as an exact source span, assess semantic support, code evidence against a
   frozen and versioned codebook, and compare themes across firms, fiscal periods,
   document types, and speaker roles.

The tracks share contracts and provenance, but they remain independently
testable. Theme extraction can begin from a saved earnings release without first
completing the broader company-enrichment dataset.

The first corpus is the Dow Jones Industrial Average (DJIA), resolved point in
time, over the eight calendar quarters from 2024Q3 to 2026Q2. The project measures
feasibility before it runs the full corpus:

- Run the pipeline on a 40-event pilot. Compare its output with the gold, the
  answer key that the maintainer verifies and signs for each event.
- Choose the production model, the final theme taxonomy and the quality
  thresholds by measurement, not by assumption.
- Evaluate the selected configuration once, on held-out events.
- Keep the required path free of paid services. It uses open-weight models on
  local hardware.

## Research status

### What has been done

**Stages 1–10 of the 16-stage roadmap are complete.** They built and tested the
pipeline:

- **Sources and parsing (Stages 1–3).** An investigation compared three HTML
  parsers on eight release fixtures and chose a bespoke lxml walker. The core
  package defines canonical documents, exact spans and the checks on them. The
  canonicalizer turns a saved release into hashed, versioned text with typed
  elements.
- **Corpus (Stages 4–5).** The point-in-time DJIA cohort is frozen. The frozen
  event manifest holds 263 earnings events from SEC filing metadata. Of these, 239
  are eligible: the issuer was a DJIA member when SEC accepted the filing. A fixed
  rule chose the 40-event pilot before any release was acquired. Stage 5 then
  acquired the pilot's releases from SEC EDGAR and recorded each one's processing
  state.
- **Pilot protocol (Stage 6).** The pilot is split by issuer and time into 20
  train, 8 dev and 7 test events, with 5 excluded. Codebook v0 has 22 themes, drawn
  from the train events only
  ([ADR 0003](https://github.com/lowmason/earnings-themes/blob/main/docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md)).
- **Theme pipeline (Stages 7–10).** The extractor, support assessment, deductive
  coding and coverage-aware reports are built. Stage 10 joins them in an offline
  replay command. These stages were verified on synthetic and invented fixtures
  only.

**Stage 11, the feasibility pilot and threshold calibration, is in progress.** It
runs the pipeline on real pilot documents in the maintainer's own terminal. Its
[specification](https://github.com/lowmason/earnings-themes/blob/main/specs/feasibility-pilot-and-threshold-calibration.md)
has two plans. Plan A built the evaluation, label and calibration code without
pilot text or a model, and it is complete.
[Plan B](https://github.com/lowmason/earnings-themes/blob/main/specs/plans/21-feasibility-pilot-and-threshold-calibration-plan-b.md)
runs the pilot. So far:

- The baseline models are chosen, and all run locally
  ([ADR 0006](https://github.com/lowmason/earnings-themes/blob/main/docs/adr/0006-select-the-pilot-baseline-models.md)).
  Gemma 4 31B-it extracts claims and classifies them against the codebook.
  Qwen2.5-14B-Instruct and Mistral-Nemo-Instruct-2407 judge support. MiniCheck
  and DeBERTa score support.
- The method choices are preregistered. They were frozen in a commit of their own
  before any pilot run.
- The gold for all 28 train and dev events is signed and committed (2026-10-31).
  The 7 test events have no gold yet, by design.
- The first pass over the 20 train events ended `partial`. Some model replies
  failed validation twice, so 9 of 1,171 classifications and 64 of 1,170 support
  targets stayed incomplete. The maintainer accepted the pass as the train
  baseline (2026-11-11).
- Support assessment cleared almost no targets. Of the 1,170 claim–theme targets,
  1 was `assessed`: every signal was present and no judge objected. 1,105 were
  `flagged`: a judge objected or was unsure, or the judges' answers differed. 64
  were `incomplete`, and none was `refused`.
- 70 train support labels are committed, and 63 of them are usable (2026-11-11). A
  hosted model, Codex, wrote these labels under the maintainer's override, and no
  human reviewed them. So the train agreement figures compare the judges with a
  model, not with a person.
- The train calibration ended `no_candidate` (2026-11-12). No support cutoff
  reached the preregistered recall floor of 0.4. So the baseline selects no
  assignment policy, and every theme assignment stays in human review. This is a
  feasibility finding, not an error.
- The pass over the 8 dev events started on 2026-11-14, under the frozen baseline.
  This step also collects the maintainer's 24 unaided dev labels, and it is in
  progress.

The
[feasibility verification record](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/pilot-v1-feasibility.md)
and plan B's decision log record each step.

### What has not been done yet

- **The rest of Stage 11.** The dev runs and the maintainer's 24 unaided dev
  labels are not complete. Fresh-call stability is not measured. It is how much the
  results change when every model call runs again with no cache. No pilot
  metric, pilot report or V6 record exists. The V6 record will set the quality
  gates for later stages.
- **No theme dataset.** No theme assignment is accepted, and no research result
  about earnings themes is published.
- **Stages 12–16 are still open:**
  - Stage 12: an inductive and hybrid codebook, discovered from train evidence
    only.
  - Stage 13: earnings-call transcripts with speaker roles, only if a lawfully
    usable source exists.
  - Stage 14: a comparison of configurations, then one held-out evaluation on the
    7 test events. Their gold is drafted only after the configuration is frozen.
  - Stage 15: the full run over every eligible DJIA event in the eight quarters.
  - Stage 16 (optional): a hosted-model quality ceiling, within a $100 budget.
- **Most company enrichment.** The cohort resolves each security to an issuer and
  its SEC CIK. Industry, employment, subsidiaries and locations are not built.
- **Some choices are deliberately open.** The production model, the final theme
  taxonomy and the quality thresholds beyond exactness are not chosen. Measurement
  must decide them.
- **A project license.** See [License and source rights](#license-and-source-rights).

## Research workflow

1. Acquire source documents.
2. Build versioned canonical text.
3. Traverse typed structural elements.
4. Propose quote-claim evidence.
5. Verify exact spans in code.
6. Assess semantic support.
7. Apply a versioned codebook.
8. Aggregate with coverage denominators.
9. Report with source-linked evidence.

The core rule is **the model proposes; code disposes**. Models may identify
candidate evidence and judge thematic support, but deterministic code decides
whether a quote is exact. For an accepted quote:

```python
0 <= start < end <= len(canonical_text)
quote_text == canonical_text[start:end]
stored_canonical_hash == sha256(canonical_text.encode("utf-8"))
```

Offsets use zero-based, half-open Python string indices: `[start, end)`. A model
cannot patch source wording, join noncontiguous passages into one verbatim quote,
or waive verification. Exactness also does not establish that a quote supports a
claim; support is assessed separately.

### Key terms

- **Canonical text:** the immutable, versioned text representation against which
  all evidence offsets are measured. Re-canonicalization creates a new version;
  it never changes text beneath existing spans.
- **Quote:** a contiguous source span materialized by code from its document and
  offsets, not a model-generated transcription.
- **Claim:** an interpretation supported by one or more verified quotes.
- **Codebook:** a reviewed, frozen set of theme definitions and coding rules.
  Changing a definition creates a new version.
- **Coverage denominator:** the eligible firms, events, or documents actually
  observable for a reported comparison, including explicit missingness rules.

## Design principles

- **Evidence before interpretation.** Quotes, claims, themes, and theme
  assignments are distinct records. Interpretations always resolve back to
  immutable source evidence.
- **Provenance and time are first-class.** Reference time, publication time,
  retrieval time, source identity, hashes, parser versions, and run versions are
  preserved rather than collapsed into a current value.
- **Coverage is part of the result.** Unavailable, restricted, failed, partial,
  and completed-with-no-theme documents remain visible so successful quotes do
  not become a misleading denominator.
- **Corporate units stay distinct.** Securities, legal entities, reporting
  groups, subsidiaries, and establishments are not merged merely because names
  or addresses resemble one another.
- **Rights and cost constrain the workflow.** Free access is not assumed to
  grant redistribution rights. The required theme-extraction path is designed
  for offline fixtures and open-weight, self-hosted models; hosted or billable
  inference requires separate authorization and an enforced budget.
- **Deterministic stages stay framework-independent.** Acquisition,
  canonicalization, span verification, support assessment, coding, and export
  remain separable. Workflow or model frameworks are optional adapters, not the
  source of domain truth.

## Repository layout

| Path | Responsibility | Current state |
| --- | --- | --- |
| `packages/earnings-core/` | Shared contracts, identifiers, hashes, provenance, and pure span helpers | Stage 2 contracts and exactness checks (schema v2) |
| `packages/earnings-ingestion/` | Source adapters, raw snapshots, deterministic parsing, canonicalization, and entity resolution | Stage 3's canonicalizer and browser diagnostic path; Stage 4's artifact store, shared SEC client, and point-in-time DJIA cohort; Stage 5's event discovery, eligibility, and pilot selection; Stage 6's coverage report |
| `packages/earnings-themes/` | Quote-claim extraction, exact-span verification, support assessment, codebooks, and evaluation | Stages 6–9 contracts, extractor, support and coding; Stage 10 current analytical gates and fourteen typed tables; Stage 11 evaluation, labels and calibration (`earnings_themes.evaluation`) |
| `apps/earnings-pipeline/` | Thin application layer for configuration, stage coordination, checkpoints, and reporting | `earnings-pipeline browser setup`, and the `earnings-pipeline cohort`, `events`, `pilot`, `codebook`, and `gold` commands, plus `extract run --config PATH` for explicit offline replay |
| `docs/` | Source notes and, as the project develops, methodology, source registers, verification reports, and decisions | Source notes, the release and membership source registers, verification records V1 and V2 and those of Stages 3 to 11, ADRs 0001 to 0006, and the data dictionary |
| `specs/` | Binding and exploratory system specifications, reviews, and the staged implementation roadmap | Present |
| `expirements/parser-fidelity/` | Stage 1's investigation harness: parser candidates, scorer, and selection rule | Complete; a record, not product code |
| `tests/fixtures/releases/` | Stage 1's eight release fixtures, with gold annotations and a provenance manifest | Present |
| `config/universe/djia/` | The cohort's curated files and frozen universe manifests: facts and citations, never source text | Stage 4's frozen cohort |
| `tests/fixtures/cohort/` | The synthetic cohort, which replays offline to its frozen manifest | Present |
| `config/corpus/djia-2024q3-2026q2/` | The reviewed event overrides, the frozen event manifest and its evidence record, and the frozen pilot: facts, URLs, hashes, and locators, never source text | Stage 5's frozen event manifest and pilot |
| `tests/fixtures/events/` | The synthetic event corpus, which replays offline to its frozen event manifest and pilot | Present |
| `evaluation/djia-2024q3-2026q2/pilot-v1/` | The pilot's split, coverage report, drafting briefs, and signed gold: IDs, offsets, labels, hashes, and the maintainer's words, never release text | Stage 6's frozen split and report, the 28 signed train and dev gold files, and Stage 11's preregistration, train support labels and train calibration |
| `codebooks/djia-pilot/` | The pilot codebook | Codebook v0, approved in ADR 0003 |
| `tests/fixtures/gold/` | The curated hard negatives, over Stage 1's fixtures | Present |

The intended dependency direction is:

```text
earnings-ingestion ──┐
                     ├──> earnings-core
earnings-themes ─────┘

earnings-pipeline ──────> earnings-core + earnings-ingestion + earnings-themes
```

Ingestion and themes exchange shared contracts and versioned artifacts through
the application; they do not import one another's internals. No package imports
the application. `earnings-core` supplies pure span and hash primitives;
`earnings-themes` owns the domain decision to accept or reject a candidate quote
using those primitives.

## Current roadmap

The implementation is organized as a staged, evidence-first roadmap of sixteen
stages. Stages 1–10 are complete, and Stage 10 merged in PR #14.

Stage 11, the feasibility pilot and threshold calibration, is in progress. Its
plan A is complete. Its plan B has completed steps B1 to B5: the baseline models,
the preregistration, the train pass, the train labels and the train calibration.
Step B6, which replays the train events and exposes the dev events, is in progress.
Stages 12–16 remain open. [Research status](#research-status) summarizes the
results so far. The live roadmap remains authoritative.

The roadmap was amended on 2026-09-22 by
[the point-in-time DJIA cohort specification](https://github.com/lowmason/earnings-themes/blob/main/specs/completed/point-in-time-djia-cohort.md).
It inserts **Stage 4: point-in-time DJIA cohort** before any document is
acquired, moves the 40-event feasibility pilot into **Stage 5** as a
deterministic selection frozen before any acquisition or parse outcome is known,
and adds **Stage 15: the full DJIA eight-quarter run** over calendar period ends
from `2024Q3` through `2026Q2`. The firm universe is the Dow Jones Industrial
Average resolved point in time, not one current roster: a current list would
introduce survivorship bias into earlier periods.

**Stage 1: acquisition-library and parser fidelity** is complete. It was an
investigation, not product code. It measured three candidate HTML parsers and a
plain-text control on eight provenance-recorded earnings-release fixtures, two for
each of four release classes, and recorded the actual return types of the pinned
EDGAR acquisition library, edgartools 5.58.0.
[ADR 0001](https://github.com/lowmason/earnings-themes/blob/main/docs/adr/0001-use-the-bespoke-lxml-walker-as-the-base-parser-for-release-canonicalization.md)
selects a bespoke lxml walker as the base parser for canonicalization. The two
eligible parsers tied on coverage, footnote merging, and reading order, so header
loss decided. On those three metrics the walker beat the plain-text control in no
class, so the fixtures are flagged as unable to discriminate there; the decision
was accepted with that caveat. The measurements are in
[V2](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/V2-parser-fidelity.md) and the return types in
[V1](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/V1-edgartools-return-types.md). The harness is in
`expirements/parser-fidelity/`, and the fixtures, with their gold annotations, are
in `tests/fixtures/releases/`. The harness's offline tests run with:

```bash
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
```

**Stage 2: core evidence spine** is complete. `earnings-core` now holds the
contracts every later stage builds on: hashed, versioned canonical documents;
typed elements with derived IDs and code-point spans; overlay masks; span
locators; and an exactness validator with no tolerance. The
[data dictionary](https://github.com/lowmason/earnings-themes/blob/main/docs/data-dictionary.md) documents every field.

**Stage 3: structure-aware canonicalization** is complete. `earnings-ingestion`
turns a saved release into a hashed `walker-1` canonical document with typed
elements, tables, sentences, and boilerplate masks.
[ADR 0002](https://github.com/lowmason/earnings-themes/blob/main/docs/adr/0002-keep-the-browser-capture-diagnostic-only.md) keeps its
pinned-browser capture diagnostic-only.

**Stage 4: point-in-time DJIA cohort** is complete. `earnings-ingestion` rebuilds
the index's membership security by security, from a dated anchor snapshot and
S&P Dow Jones Indices' announcements. It resolves each security to an issuer and
a zero-padded CIK from SEC's records, and reports every conflict, gap, and
difference. The reviewed cohort is frozen as a versioned, content-hashed
manifest in `config/universe/djia/manifests/` before any earnings document is
acquired. Every SEC request goes through one shared client at 2 requests per
second. The [verification record](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/djia-cohort.md) has the
details.

**Stage 5: event discovery, eligibility, and acquisition** is complete. Its first
plan finds each cohort issuer's quarterly earnings releases in SEC's filing
metadata, and judges each one's eligibility by point-in-time membership at its
EDGAR acceptance time. It freezes the reviewed event manifest and a deterministic
pilot selection in `config/corpus/djia-2024q3-2026q2/` before any release is
acquired. Its second plan then acquires the pilot's releases from EDGAR through the
shared client, chooses and confirms each release exhibit, and records each document's
processing state. The [verification record](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/djia-events.md) has
the details.

**Stage 6: the pilot codebook, split, and gold-set protocol** is complete. It
pins the pilot by content hash, splits it by issuer and time into 20 train, 8
dev, and 7 test events, with 5 excluded, and reports its coverage. Codebook v0,
discovered from the training partition alone, is approved in
[ADR 0003](https://github.com/lowmason/earnings-themes/blob/main/docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md). A Claude
session drafts each bundle's gold under a committed brief, and the maintainer
verifies every item, reads the release for omissions, and signs; committed
files hold pointers, labels, and hashes, never release text. All 28 train and
dev bundles are signed (2026-10-31). The 7 test bundles wait until Stage 14 freezes
a configuration. The [verification record](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/pilot-v1-gold-set.md)
has the details.

**Stage 8: semantic support assessment** is complete (2026-10-05). The actual
pinned MiniCheck primary smoke passed under process-wide network denial on invented text, the user’s full root default suite
and both Stage 6 wording gates passed, and the final whole-branch review cleared
its findings. The [verification record](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/semantic-support.md)
records the observed checks, runtime identity and limits.

`earnings_themes.support` exposes `Target`, `SupportSources`, `ResolvedInput`,
`resolve_target`, `assess_target`, `assess_run`, `write_support_run`,
`read_support_run`, `reverify_support_run`, and the pure `auc_roc` and
`accepted_claim_precision` metrics with their typed inputs/reports. Callers supply
saved extraction records, canonical bundles, a frozen approved codebook, explicit
claim–theme targets, model identities, prompts, ceilings, and a cache. Exact spans
are reverified before scoring, publication, and downstream consumption. Results
retain raw per-quote/joint scores, four independent judge trials, usage, and
`refused`/`incomplete`/`flagged`/`assessed` processing outcomes. An `assessed`
outcome confers no accepted assignment.

Concrete local scorer adapters live in `earnings_themes.support.nli`, behind the
optional `support-nli` extra; ordinary imports need no model runtime or weights.
[ADR 0005](https://github.com/lowmason/earnings-themes/blob/main/docs/adr/0005-adopt-local-minicheck-for-support-signals.md) records the
pinned MiniCheck primary, explicit DeBERTa alternative, external configuration,
local-file and rights requirements, and the passed network-denied primary smoke.

Stage 8 did not run the alternative’s real-checkpoint smoke. Stage 11’s step B1
later loaded both pinned scorers in its fixture-only smoke test, as
[ADR 0006](https://github.com/lowmason/earnings-themes/blob/main/docs/adr/0006-select-the-pilot-baseline-models.md)
records. Stage 9 supplies assignment decisions, and Stage 10 composes them in the
replay application command with coverage mapping. Stage 11’s plan A built the
expert-label, calibration and fresh-call stability code. Its plan B has since run
the label and calibration code on the train events. No pilot accuracy or stability
result exists.

Key planning documents:

- [Evidence-linked theme extraction specification](https://github.com/lowmason/earnings-themes/blob/main/specs/evidence-linked-theme-extraction.md)
  — the system requirements and verification criteria.
- [Implementation roadmap](https://github.com/lowmason/earnings-themes/blob/main/specs/evidence-linked-theme-extraction-roadmap.md)
  — staged delivery, dependencies, and exit conditions.
- [Stage 1 parser-fidelity specification](https://github.com/lowmason/earnings-themes/blob/main/specs/completed/release-parser-fidelity.md)
  — Stage 1's scope and measurement design.
- [Point-in-time DJIA cohort specification](https://github.com/lowmason/earnings-themes/blob/main/specs/completed/point-in-time-djia-cohort.md)
  — the firm universe, event corpus, and deterministic pilot selection; the
  stage specification for roadmap Stages 4 and 15, and binding on Stage 5's
  event-eligibility and pilot-selection design.
- [Event discovery, eligibility, and acquisition specification](https://github.com/lowmason/earnings-themes/blob/main/specs/completed/event-discovery-eligibility-and-acquisition.md)
  — Stage 5's two plans: discovery, eligibility, and the freezes; then
  acquisition and processing states.
- [Pilot codebook, split, and gold-set protocol specification](https://github.com/lowmason/earnings-themes/blob/main/specs/completed/pilot-codebook-split-and-gold-set-protocol.md)
  — Stage 6: the pin, the issuer-and-time split, codebook v0, and the gold-set
  protocol, with Claude-drafted, user-verified gold.
- [Feasibility pilot and threshold calibration specification](https://github.com/lowmason/earnings-themes/blob/main/specs/feasibility-pilot-and-threshold-calibration.md)
  — Stage 11: the pilot run, the support labels, the calibration and the V6 gates.
- [Stage 11 plan B](https://github.com/lowmason/earnings-themes/blob/main/specs/plans/21-feasibility-pilot-and-threshold-calibration-plan-b.md)
  — the pilot's steps and the maintainer's decision log.
- [Earnings-theme learning path](https://github.com/lowmason/earnings-themes/blob/main/docs/earnings-themes.md) — the original staged
  learning exercise that motivates the extraction track.
- [Company-ingestion source note](https://github.com/lowmason/earnings-themes/blob/main/docs/earnings-ingestion.md) — the original
  research note for membership, identifiers, employment, subsidiaries, and
  establishment data.
- [Repository working rules](https://github.com/lowmason/earnings-themes/blob/main/AGENTS.md) — binding engineering, evidence, rights,
  and reproducibility requirements.

`AGENTS.md` and the evidence-linked extraction specification define the binding
project rules. Review files and alternative integration specifications under
`specs/` are exploratory unless a binding document explicitly adopts them.

The final taxonomy, production model, and non-exactness acceptance thresholds
are deliberately unresolved. Stage 4 settled the firm universe as the point-in-time
DJIA cohort. The open choices must be selected
through the documented review and measurement processes rather than embedded as
unstated assumptions.

## Getting started

### Prerequisites

- Python 3.14 or newer
- [`uv`](https://docs.astral.sh/uv/)

From the repository root, create or update the workspace environment from the
reviewed lockfile:

```bash
uv sync --locked --all-packages --group dev
```

The required workspace contains four installable distributions:

```bash
uv run python -c "import earnings_core, earnings_ingestion, earnings_themes, earnings_pipeline"
```

The packages expose their implemented stage-specific modules. Ordinary imports
perform no acquisition or model call; this import checks only workspace packaging.

### Development checks

Stage 10 agent checks use the source-audited, metadata-only runner:

```bash
POLARS_MAX_THREADS=2 UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py contracts
POLARS_MAX_THREADS=2 UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py vertical
POLARS_MAX_THREADS=2 UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py stage10
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync ruff check packages apps tests tools
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync ruff format --check packages apps tests tools
```

Run these from the repository root with the reviewed environment already present.
There is no implicit sync or download. `stage10` is a deduplicated 72-file allowlist
with a 900-second child deadline; individual groups retain 300 seconds. The
human-only `root-user --user-only` route has the approved fixed 1800-second
deadline; wording and browser routes retain 300 seconds. The stage10 union is not
the full-root suite. The runner captures child output and emits only validated
counts, safe test IDs and closed reasons. Audit selected readers before execution;
output guarding does not authorize protected readers. Agents never run full-root,
either Stage 6 wording node or browser/user-only modes. The controller obtains
those human gates at the final reviewed HEAD. The earlier human root run returned
`runner_timeout` at 300 seconds; its zero counters and empty IDs are placeholders,
not successful test results. The only successful full-root durations observed are for
the plain documented root command, not the runner, both on 2026-10-11: 836 seconds at
`4ba5f35` with `PYTHONPATH` set (4294 passed, 1 skipped, 28 deselected, 1 warning), and
819 seconds with no `PYTHONPATH` once `pythonpath` joined the pytest configuration (4243
passed, 9 skipped, 28 deselected); the runner's `root-user` duration remains unknown. See the
[verification record](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/theme-vertical-slice.md) for exact results
and the separate [V5 protocol](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/stage10-browser.md).

Pytest uses importlib handling, strict configuration, `live`/`browser` markers and a
`pythonpath` of the repository root, so the documented root command and a single test
file both collect under the `pytest` console script. Default tests make no network or
billable calls. No type checker is configured. Two CI workflows run on each pull
request and on each push to `main`. The
[tests workflow](https://github.com/lowmason/earnings-themes/blob/main/.github/workflows/tests.yml)
runs Ruff, the documented root command with `-n logical`, and the Stage 1 harness command. Its runner
has no `data/` directory and no secrets, so tests that need local data skip. It does
not replace the human gates above. `-n auto` runs the tests in parallel with
pytest-xdist, one worker for each physical core. `-n logical` starts one worker for
each logical CPU. The two differ only on a CPU with hyperthreads, such as the CI
runner, whose 4 vCPUs are 2 physical cores. On 2026-11-16, in a worktree without
`data/`, `-n auto` ran the same tests as the serial root command, in 73 s rather than
554 s. Tests that read local data have not yet run in parallel. The parallel summary
line leaves out the deselected count. The Stage 10 runner turns off plugin autoloading, so do not add `-n`
to `addopts`. The docs workflow builds and deploys the
documentation site (see [Documentation](#documentation)). The Stage 1 harness retains
its separate historical command above.

### Offline replay extraction

The implemented entry point is:

```bash
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv uv run --locked --offline --no-sync --all-packages earnings-pipeline extract run --config /absolute/path/to/prepared-replay.json
```

The JSON must be fully prepared for the repository used as the command's current
working directory. `load_workflow_config(path: Path, *, repo: Path)` confines
selected paths before loading bytes. The schema requires explicit universe/event/
pilot selections and pins, sorted selected event IDs, acquisition/canonical/source
metadata, frozen codebook, prompts, policies, identities, ceilings, stage run IDs,
cache paths, optional pinned stored stages, analysis policy, family/copy/no-theme
choices, rights audience, output directory and software/lock identity. See the
[workflow contract](https://github.com/lowmason/earnings-themes/blob/main/docs/data-dictionary.md#explicit-replay-extraction-workflow-schema-1).
`tests/fixtures/themes/stage10/replay-config.json` is a template, not a directly
runnable configuration. The audited `tests/integration/stage10_cases.py` helper
fills its confined temporary paths, hashes, identities, ceilings and fixture clock,
and seeds caches with scripted invented replies; the `vertical` check exercises
that complete route through the actual CLI.

The CLI supports replay only. Its inner dispatch and tokenizer methods refuse with
`replay_dispatch_forbidden`; a cache miss stays explicit. Programmatic
`run_theme_workflow(config, runtime, *, now)` accepts explicit injected adapters and
an actual assignment policy, without authorizing a model call. No calibrated
assignment-policy implementation is registered: a CLI policy reference refuses
`policy_unavailable`, while null policy retains `review/calibration_required`.
`fixture-supporting/1` requires fixture scope and an explicit authorization inventory
bound to current corpus/event/pilot/provenance hashes. The allowlist is
`djia-synthetic` and `stage10-invented`; a corpus name alone grants no acceptance.

Analytical schema 1 contains fourteen typed Parquet tables and retains all original
claim–quote and assignment–claim links. Current source/hash/span/mask/book/policy
checks run before aggregation and again before publication. Headline prevalence
counts eligible, fully observed issuer-periods from the declared expected-event
population, at most once per issuer-period. Masked quotes remain in audit and are
excluded from headlines. Disclosure copies count once; parent self-or-descendant
and optional overlapping versioned family views remain separate from direct themes.
An empty quote/target table never proves no theme: `completed-no-theme` needs an
explicit currently bound processing declaration and complete layer evidence.
Release roles are `not_applicable`; transcript slots are unobservable with
`transcript_not_in_scope` and cannot support a negative transcript signal.

The immutable analysis binds its parsed acquisition baseline. A separate receipt
binds actual appended schema-2 processing bytes. Same-workflow retries recheck exact
analysis bytes, completions and the immediate immutable parsed predecessor; they
append once or reuse the recorded state. Another workflow requires an explicit
stored analysis directory and manifest SHA plus all pinned stage runs and current
gates. There is no terminal reopening, latest-run discovery or inferred provenance.

Local and export reports apply current text/raw rights, including nested canonical
artifact rights. Permitted static canonical views highlight the exact occurrence
and work without a browser; required missing raw bytes refuse complete publication.
Rights-denied raw inclusion records `snapshot_withheld`; text-denied evidence is
`withheld/rights_restricted`. Browser UTF-16 coordinates exist only at the application
boundary; stored evidence uses Python code-point offsets. Screenshots are always
`local_only`. Static marks, fake renderer checks and capture completion establish
no native highlighting. Human V5 observations on 2026-10-08 established five native
highlights, one drift non-highlight and six visible canonical fallbacks in the
pinned available Chrome target. Actual screenshot capture and external HTTPS are
unverified; the capture command skipped once with its cause unspecified. See
[the V5 record](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/stage10-browser.md) and
[completion verification](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/theme-vertical-slice.md). Stage 11 owns pilot extraction,
calibration and fresh-call stability; fixture exactness establishes no model quality.

Completion records: [retired plan 15](https://github.com/lowmason/earnings-themes/blob/main/specs/plans/completed/15-evidence-linked-theme-extraction.md) and [read-only backlog proposal](https://github.com/lowmason/earnings-themes/blob/main/docs/verification/stage10-backlog-triage.md). The observed human root result at `611f84a` is 4241 passed / 9 skipped / 28 deselected with zero failures, collection failures and warnings; both wording gates passed one each. No root exit or elapsed time was supplied.

## Optional dependencies

Runtime dependencies are kept package-local. Optional integrations are grouped
so the required path does not install every experimental or hosted provider:

| Package | Extras | Intended use |
| --- | --- | --- |
| `earnings-ingestion` | `edgar`, `entity-matching` | EDGAR-library experiments and fuzzy candidate generation |
| `earnings-ingestion` | `browser-capture` | Stage 3's browser diagnostic path: Selenium and websocket-client drive the pinned Chrome for Testing, which `earnings-pipeline browser setup` installs |
| `earnings-themes` | `extraction`, `fuzzy-localization`, `embeddings` | Typed extraction, candidate localization, and offline clustering experiments |
| `earnings-themes` | `openai`, `anthropic` | Optional hosted-provider adapters; installation does not authorize billable calls |
| `earnings-themes` | `jev`, `jev-langchain` | Optional, separately authorized verification experiments; not part of the required path |
| `earnings-pipeline` | `orchestration` | Optional resumable workflow integration when scale justifies it |

Select extras deliberately. Do not use `--all-extras` as a routine setup step:
several groups are mutually unnecessary for ordinary development, and some exist
only for measured comparisons.

Install an extra by repeating `--extra` for each selected group. For example:

```bash
uv sync --locked --all-packages --extra extraction
```

## Documentation

The documentation site is at <https://lowmason.github.io/earnings-themes/>.
[Great Docs](https://posit-dev.github.io/great-docs/) builds it from this README
and from the numpy-style docstrings of `earnings_core`. The API reference covers
`earnings_core` only. It is the only package that declares its public exports in
`__all__`.

The site configuration is
[`packages/earnings-core/great-docs.yml`](https://github.com/lowmason/earnings-themes/blob/main/packages/earnings-core/great-docs.yml).
Great Docs finds the package to document from a `[project]` table, and the
workspace root has none. So every docs command names the member with
`--project-path`. `packages/earnings-core/README.md` is a symbolic link to this
file, so this README is the site's homepage.

The `docs` dependency group pins `great-docs>=0.17.0,<0.18`, and `uv sync`
installs it by default. A build also needs
[Quarto](https://quarto.org/docs/get-started/). To build and check the site,
run these from the repository root:

```bash
uv run great-docs build --project-path packages/earnings-core </dev/null
uv run great-docs lint --project-path packages/earnings-core
uv run numpydoc lint packages/earnings-core/src/earnings_core/*.py
```

The build writes the site to `packages/earnings-core/great-docs/_site/`, which
Git ignores. To serve it locally, run
`uv run great-docs preview --project-path packages/earnings-core`. The
[docs workflow](https://github.com/lowmason/earnings-themes/blob/main/.github/workflows/docs.yml)
builds the site on each pull request and deploys it to GitHub Pages from `main`.

## Data, network access, and reproducibility

- `data/raw/`, `data/canonical/`, `data/processed/`, and `data/runs/` are local
  artifact locations and are ignored by Git.
- Only small fixtures with documented redistribution permission belong under
  `tests/fixtures/`.
- The source register that records access, licensing, and redistribution status
  for release fixtures is [`docs/source-register.toml`](https://github.com/lowmason/earnings-themes/blob/main/docs/source-register.toml),
  a Stage 1 deliverable. Stage 4 added a second register for
  index-membership sources,
  [`docs/membership-source-register.toml`](https://github.com/lowmason/earnings-themes/blob/main/docs/membership-source-register.toml),
  which quotes no source. A free or open-source
  acquisition tool confers no rights to the underlying index data.
- SEC access requires a descriptive User-Agent with genuine project contact
  information configured outside committed code. The project default is a shared
  maximum of **2 requests per second** across SEC adapters and workers.
- Persistent authorization or access failures stop a run; clients must not rotate
  identities or bypass controls.
- Saved raw inputs and model responses should support offline replay. A fresh
  network fetch or paid model call must not be required for normal development or
  CI.
- Missing or ambiguous observations remain missing or ambiguous. Parser failure,
  source absence, and zero are different states.

## Contributing

Before changing code or contracts:

1. Read [AGENTS.md](https://github.com/lowmason/earnings-themes/blob/main/AGENTS.md), the relevant source note and specification, the
   owning package's metadata, and downstream contract consumers.
2. Make the smallest coherent change and write deterministic fixture-based tests
   before implementation where applicable.
3. Keep source acquisition separate from parsing; parsers consume saved
   bytes/text and metadata rather than network clients.
4. Preserve schema versions and provenance when changing canonical text, offsets,
   identifiers, or codebooks.
5. Run the current Ruff checks. Once a relevant test suite exists, run its pytest
   checks too. Report only commands that actually ran and outcomes that were
   observed.

Do not commit credentials, contact configuration, restricted source text, large
downloads, model caches, traces containing sensitive text, or generated research
outputs.

## License and source rights

This repository does not currently include a project-wide `LICENSE` file. Do not
assume permission to redistribute the software or any acquired data beyond the
rights explicitly documented for that material. Source access conditions,
licenses, and redistribution status are tracked separately because a free or
open-source acquisition tool does not determine the rights of the underlying
documents or datasets.
