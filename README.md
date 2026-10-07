# earnings-themes

Evidence-linked research infrastructure for company data and earnings themes.

> [!IMPORTANT]
> **Project status (2026-10-07): Stages 1–9 are complete; Stage 10 is under review.**
> The workspace implements acquisition, canonical evidence, extraction, support
> assessment and coding libraries. Stage 10 adds an offline replay command,
> coverage-aware analytical tables and cited reports, verified on permitted
> synthetic/invented fixtures. No pilot document has been extracted and no research
> theme dataset is published. Native V5 observations, final independent reviews
> and the human-only completion gates remain pending.

## Stage 8 library status (2026-10-05)

Stage 8 is complete. The actual pinned MiniCheck primary smoke passed under
process-wide network denial on invented text, the user’s full root default suite
and both Stage 6 wording gates passed, and the final whole-branch review cleared
its findings. The [verification record](docs/verification/semantic-support.md)
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
[ADR 0005](docs/adr/0005-adopt-local-minicheck-for-support-signals.md) records the
pinned MiniCheck primary, explicit DeBERTa alternative, external configuration,
local-file and rights requirements, and the passed network-denied primary smoke.
The alternative’s real-checkpoint smoke remains unrun. Stage 9 supplies assignment
decisions; Stage 10 implements the replay application command and coverage mapping; Stage 11
owns expert labels, calibration, thresholds, production judge selection, and
fresh-call stability. The offline evidence establishes no pilot accuracy or
stability result.

## Purpose

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

## Research workflow

```mermaid
flowchart LR
    A[Acquire source documents] --> B[Build versioned canonical text]
    B --> C[Traverse typed structural elements]
    C --> D[Propose quote-claim evidence]
    D --> E[Verify exact spans in code]
    E --> F[Assess semantic support]
    F --> G[Apply a versioned codebook]
    G --> H[Aggregate with coverage denominators]
    H --> I[Report with source-linked evidence]
```

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
| `packages/earnings-themes/` | Quote-claim extraction, exact-span verification, support assessment, codebooks, and evaluation | Stages 6–9 contracts, extractor, support and coding; Stage 10 current analytical gates and fourteen typed tables |
| `apps/earnings-pipeline/` | Thin application layer for configuration, stage coordination, checkpoints, and reporting | `earnings-pipeline browser setup`, and the `earnings-pipeline cohort`, `events`, `pilot`, `codebook`, and `gold` commands, plus `extract run --config PATH` for explicit offline replay |
| `docs/` | Source notes and, as the project develops, methodology, source registers, verification reports, and decisions | Source notes, the release and membership source registers, verification records V1 and V2 and those of Stages 3 to 6, ADRs 0001 to 0003, and the data dictionary |
| `specs/` | Binding and exploratory system specifications, reviews, and the staged implementation roadmap | Present |
| `expirements/parser-fidelity/` | Stage 1's investigation harness: parser candidates, scorer, and selection rule | Complete; a record, not product code |
| `tests/fixtures/releases/` | Stage 1's eight release fixtures, with gold annotations and a provenance manifest | Present |
| `config/universe/djia/` | The cohort's curated files and frozen universe manifests: facts and citations, never source text | Stage 4's frozen cohort |
| `tests/fixtures/cohort/` | The synthetic cohort, which replays offline to its frozen manifest | Present |
| `config/corpus/djia-2024q3-2026q2/` | The reviewed event overrides, the frozen event manifest and its evidence record, and the frozen pilot: facts, URLs, hashes, and locators, never source text | Stage 5's frozen event manifest and pilot |
| `tests/fixtures/events/` | The synthetic event corpus, which replays offline to its frozen event manifest and pilot | Present |
| `evaluation/djia-2024q3-2026q2/pilot-v1/` | The pilot's split, coverage report, drafting briefs, and signed gold: IDs, offsets, labels, hashes, and the maintainer's words, never release text | Stage 6's frozen split and report, and three signed bundles |
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
stages. Stages 1–9 are complete; Stage 10 implementation has fixture evidence and
awaits completion gates. The live roadmap remains authoritative.

The roadmap was amended on 2026-09-22 by
[the point-in-time DJIA cohort specification](specs/point-in-time-djia-cohort.md).
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
[ADR 0001](docs/adr/0001-use-the-bespoke-lxml-walker-as-the-base-parser-for-release-canonicalization.md)
selects a bespoke lxml walker as the base parser for canonicalization. The two
eligible parsers tied on coverage, footnote merging, and reading order, so header
loss decided. On those three metrics the walker beat the plain-text control in no
class, so the fixtures are flagged as unable to discriminate there; the decision
was accepted with that caveat. The measurements are in
[V2](docs/verification/V2-parser-fidelity.md) and the return types in
[V1](docs/verification/V1-edgartools-return-types.md). The harness is in
`expirements/parser-fidelity/`, and the fixtures, with their gold annotations, are
in `tests/fixtures/releases/`. The harness's offline tests run with:

```bash
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
```

**Stage 2: core evidence spine** is complete. `earnings-core` now holds the
contracts every later stage builds on: hashed, versioned canonical documents;
typed elements with derived IDs and code-point spans; overlay masks; span
locators; and an exactness validator with no tolerance. The
[data dictionary](docs/data-dictionary.md) documents every field.

**Stage 3: structure-aware canonicalization** is complete. `earnings-ingestion`
turns a saved release into a hashed `walker-1` canonical document with typed
elements, tables, sentences, and boilerplate masks.
[ADR 0002](docs/adr/0002-keep-the-browser-capture-diagnostic-only.md) keeps its
pinned-browser capture diagnostic-only.

**Stage 4: point-in-time DJIA cohort** is complete. `earnings-ingestion` rebuilds
the index's membership security by security, from a dated anchor snapshot and
S&P Dow Jones Indices' announcements. It resolves each security to an issuer and
a zero-padded CIK from SEC's records, and reports every conflict, gap, and
difference. The reviewed cohort is frozen as a versioned, content-hashed
manifest in `config/universe/djia/manifests/` before any earnings document is
acquired. Every SEC request goes through one shared client at 2 requests per
second. The [verification record](docs/verification/djia-cohort.md) has the
details.

**Stage 5: event discovery, eligibility, and acquisition** is complete. Its first
plan finds each cohort issuer's quarterly earnings releases in SEC's filing
metadata, and judges each one's eligibility by point-in-time membership at its
EDGAR acceptance time. It freezes the reviewed event manifest and a deterministic
pilot selection in `config/corpus/djia-2024q3-2026q2/` before any release is
acquired. Its second plan then acquires the pilot's releases from EDGAR through the
shared client, chooses and confirms each release exhibit, and records each document's
processing state. The [verification record](docs/verification/djia-events.md) has
the details.

**Stage 6: the pilot codebook, split, and gold-set protocol** is complete. It
pins the pilot by content hash, splits it by issuer and time into 20 train, 8
dev, and 7 test events, with 5 excluded, and reports its coverage. Codebook v0,
discovered from the training partition alone, is approved in
[ADR 0003](docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md). A Claude
session drafts each bundle's gold under a committed brief, and the maintainer
verifies every item, reads the release for omissions, and signs; committed
files hold pointers, labels, and hashes, never release text. Three train
bundles are signed. The [verification record](docs/verification/pilot-v1-gold-set.md)
has the details.

Key planning documents:

- [Evidence-linked theme extraction specification](specs/evidence-linked-theme-extraction.md)
  — the system requirements and verification criteria.
- [Implementation roadmap](specs/evidence-linked-theme-extraction-roadmap.md)
  — staged delivery, dependencies, and exit conditions.
- [Stage 1 parser-fidelity specification](specs/release-parser-fidelity.md)
  — Stage 1's scope and measurement design.
- [Point-in-time DJIA cohort specification](specs/point-in-time-djia-cohort.md)
  — the firm universe, event corpus, and deterministic pilot selection; the
  stage specification for roadmap Stages 4 and 15, and binding on Stage 5's
  event-eligibility and pilot-selection design.
- [Event discovery, eligibility, and acquisition specification](specs/completed/event-discovery-eligibility-and-acquisition.md)
  — Stage 5's two plans: discovery, eligibility, and the freezes; then
  acquisition and processing states.
- [Pilot codebook, split, and gold-set protocol specification](specs/completed/pilot-codebook-split-and-gold-set-protocol.md)
  — Stage 6: the pin, the issuer-and-time split, codebook v0, and the gold-set
  protocol, with Claude-drafted, user-verified gold.
- [Earnings-theme learning path](docs/earnings-themes.md) — the original staged
  learning exercise that motivates the extraction track.
- [Company-ingestion source note](docs/earnings-ingestion.md) — the original
  research note for membership, identifiers, employment, subsidiaries, and
  establishment data.
- [Repository working rules](AGENTS.md) — binding engineering, evidence, rights,
  and reproducibility requirements.

`AGENTS.md` and the evidence-linked extraction specification define the binding
project rules. Review files and alternative integration specifications under
`specs/` are exploratory unless a binding document explicitly adopts them.

The final taxonomy, production model, non-exactness acceptance thresholds, and
historical company universe are deliberately unresolved. They must be selected
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
not successful test results. A successful full-root duration remains unknown. See the
[verification record](docs/verification/theme-vertical-slice.md) for exact results
and the separate [V5 protocol](docs/verification/stage10-browser.md).

Pytest uses importlib handling, strict configuration and `live`/`browser` markers.
Default tests make no network or billable calls. No type checker or CI configuration
is configured. The Stage 1 harness retains its separate historical command above.

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
[workflow contract](docs/data-dictionary.md#explicit-replay-extraction-workflow-schema-1).
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
no native highlighting. V5 native/capture/manual fallback remains pending, and
external HTTPS behavior is unverified. Stage 11 owns first pilot extraction,
calibration and fresh-call stability; fixture exactness establishes no model quality.

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

## Data, network access, and reproducibility

- `data/raw/`, `data/canonical/`, `data/processed/`, and `data/runs/` are local
  artifact locations and are ignored by Git.
- Only small fixtures with documented redistribution permission belong under
  `tests/fixtures/`.
- The source register that records access, licensing, and redistribution status
  for release fixtures is [`docs/source-register.toml`](docs/source-register.toml),
  a Stage 1 deliverable. Stage 4 added a second register for
  index-membership sources,
  [`docs/membership-source-register.toml`](docs/membership-source-register.toml),
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

1. Read [AGENTS.md](AGENTS.md), the relevant source note and specification, the
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
