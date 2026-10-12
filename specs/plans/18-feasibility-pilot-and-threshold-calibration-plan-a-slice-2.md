# Stage 11 Plan A, Slice 2: Fresh-Call Mode and the Live Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give extraction, coding and support a `fresh` cache mode, recorded on every run record (A1). Build the live `research` runtime from committed model files, with local token counters (A2). Use no pilot text and load no model.

**Architecture:**
- **`earnings-themes`, A1:**
  - `extraction/records.py` holds the one `CacheMode` (`replay`, `live`, `fresh`), the stability run ID type, and `cache_mode_problem`, which the three run records share.
  - `extraction/cache.py` holds `cache_directory`, which `CachedAdapter`, `CodingCache` and `SupportCache` all call. Under `fresh`, each cache is `live` over `<cache>/fresh/<stability_run_id>/`, which starts empty.
  - `RunRecord`, `ProposalRunRecord` and `SupportRunRecord` record `cache_mode` and `stability_run_id`. Schema versions and cache keys are unchanged.
- **`earnings-themes`, A2:**
  - A new `support/model_files.py` holds `verify_files` (moved from `support/nli.py`) and `files_hash` (extracted from `support/judges.py`). The scorers, the token counter and the runtime builder share them.
  - They move out of `nli.py` because no ordinary module may load `nli.py` (`test_ordinary_imports_do_not_load_nli_adapter`).
  - `support/chat_tokens.py` counts a chat request with the model's own tokenizer and chat template, from hashed local files, with no server call.
- **The application:**
  - `model_runtime.py` reads a runtime manifest and its model files.
  - It checks the judge panel first. It then hashes every model's files under a models root that the caller supplies, and returns a `LiveRuntime`: the `WorkflowRuntime` and the alternative scorer.
- **The spec:** Task 1 amends FP23, A1 and A8, as the user decided on 2026-10-12.

**Tech Stack:** Python 3.14.0 uv workspace; Pydantic v2 (strict, frozen); httpx (`MockTransport` in tests); transformers 5.18.0 and jinja2 3.1.6 behind the `support-nli` extra, never loaded by a test; pytest; Ruff.

**Spec:** `specs/feasibility-pilot-and-threshold-calibration.md`, approved 2026-10-11, merged to `main` at `c1e7ac7`; read at `36f12ec`. This plan implements:
- §Plan A: A1, A2, and A9's data-dictionary rows for their records;
- §Verification's plan A items "the fresh-mode zero-hit and replay tests";
- FP11, and FP23 as Task 1 amends it.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 11 — on plan
> completion, tick the stage and re-validate later stages against what shipped.

**This plan is plan A's second slice, not plan A.** The spec's Rollout says the Roadmap line's "plan completion" means plan B's, and plan A's own completion appends `Plan A: COMPLETE`. Plan 18 does neither. On completion it:
- does not tick Stage 11;
- does not append the spec's `Plan A: COMPLETE` line;
- does not retire the spec.

Instead, it appends a slice stamp to the spec's Rollout and retires only itself (Task 7). Plan A's remainder is A3–A5, then A8, each with A9's dictionary rows for its records.

## Global Constraints

- **GS13, blinding.**
  - The executing session never opens pilot text, a kept draft, or anything under `data/runs/gold/` or `data/runs/pilot/`. It never opens anything under the main checkout's `data/`.
  - Execute in a fresh worktree, which has no `data/` at all.
  - Never load a model, a tokenizer or a scorer runtime. Tests inject fakes: `_loader=` for the chat tokenizer, `_runtime=` or `_scorer_runtime=` for the scorers, and `httpx.MockTransport` for the chat servers.
  - Never run `-m live` (`EDGAR_IDENTITY` is exported in this shell) or `-m browser`.
  - Tests use only invented records, the synthetic layer, and Stage 1's committed fixtures.
- **Tracebacks.** Never pass `--tb=long`, `--tb=auto`, `--full-trace`, `-l`, `--showlocals`, `--pdb`, or `-vv`.
- **User gates.** The default (root) suite and the Stage 6 wording test run in the main checkout, and the user runs them in their own terminal (Task 7). The executor never runs:
  - `pytest packages apps tests`;
  - `tests/integration/test_stage6_wording.py`;
  - `tests/integration/test_stage6_pilot_v1.py`.

  A failing user gate is reported by test name and reason only.
- **The user's gate file.** This plan does not edit `tests/integration/test_stage6_wording.py`. Its globs already cover Stage 11's planned evaluation files (plan 17).
- **`CLAUDE.md`.** Never edit it without asking the user first.
- **TDD.** Every code task writes its failing test first and watches it fail for the stated reason. Task 1 is a docs-only spec amendment. One test in Task 4 pins behaviour that already holds, and it says so.
- **No copied logic (D18-1).** The plan's code calls or extracts a shared helper; it never copies an existing block. If an implementer finds the plan's code repeating a block that already exists, they call or extract it instead, and record a `> Deviation:` line.
- **GS3, the public repository.** Committed files hold IDs, hashes, counts and the user's words, never release text, and never a path on this machine. Model files name directories relative to a models root that the caller supplies (D18-9).
- **Refusals.** Each names its item by ID or field path and its reason, never text. A themes refusal is a `SupportError` or `CodingError` with a closed reason, or a `ValueError` from `cache_directory`. A builder refusal is a `WorkflowError`: `invalid_panel`, `model_mismatch` or `malformed_record`.
- **GS17, units.**
  - `earnings-themes` imports only `earnings-core`, and ingestion and themes never import each other.
  - `extraction/local.py` stays the one themes module that imports httpx (`tests/contracts/test_import_scan.py`).
  - `support/chat_tokens.py` and `support/nli.py` import transformers or torch only inside a constructor. So importing either loads no runtime.
  - No ordinary themes module may load `support/nli.py` (`test_ordinary_imports_do_not_load_nli_adapter`). So `chat_tokens.py` imports nothing from `nli.py` at module level: it imports `nli._verify_runtime_versions` inside its constructor, and only when no `_loader` is injected.
  - The CLI's `--help` must load neither `nli.py` nor the local adapter (`test_ordinary_cli_help_loads_no_concrete_runtime`). So `model_runtime.py` imports both inside its builder, for when A8 wires it into the CLI.
  - `packages/earnings-themes/tests/test_import_boundaries.py` must pass unchanged.
  - A task that adds an import between themes modules runs `test_import_boundaries.py` and `tests/contracts/test_import_scan.py`. An import cycle there forced an unlisted edit in plan 17 (its Task 3 deviation).
- **Data dictionary.** Every new or changed field, value and model goes into `docs/data-dictionary.md` in the same task (AGENTS.md §191). Every new model or enum is registered in `MODELS`, `ENUMS`, `WORKFLOW_MODELS` or `WORKFLOW_DATACLASSES` of `tests/contracts/test_data_dictionary.py`.
- **Schema versions stay 1 (D18-4).** Extraction, coding and support records keep `schema_version` 1, so every cache key is unchanged (A1). A run record without `cache_mode` is refused as malformed. None is committed.
- **The lockfile.** Only Tasks 5 and 6 run `uv lock`. Afterwards `uv lock --check` must print `Resolved 153 packages`, the count at `36f12ec`. No new package is added.
- **Ruff.** Default line length, 88. Run `uv run --locked ruff format <changed files>` before each commit. `uv run --locked ruff check .` and `uv run --locked ruff format --check .` must be clean. ISC004 rejects adjacent string literals inside a list, tuple or set; parenthesise such a pair.
- **Commits.**
  - Before each commit, run `git log -3 --oneline`: the user may commit on the branch mid-run.
  - End each commit message with the attribution trailer your session's instructions give.
- **Line numbers** cited here are at `36f12ec`. Recheck each before relying on it.
- **Agent verification scope.** The executor runs only these, in the worktree:
  - `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_extraction_cache.py packages/earnings-themes/tests/test_extraction_run.py packages/earnings-themes/tests/test_extraction_records.py packages/earnings-themes/tests/test_extraction_store.py packages/earnings-themes/tests/test_import_boundaries.py -q`
  - `uv run --locked --all-packages pytest packages/earnings-themes/tests/coding packages/earnings-themes/tests/support packages/earnings-themes/tests/analysis -q`
  - `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_model_runtime.py apps/earnings-pipeline/tests/test_theme_workflow.py apps/earnings-pipeline/tests/test_theme_config.py apps/earnings-pipeline/tests/test_extract_cli.py -q`
  - `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py tests/contracts/test_coding_contracts.py tests/contracts/test_import_scan.py tests/integration/test_coding_frozen_v0.py tests/integration/test_support_fixtures.py tests/integration/test_theme_frozen_v0.py tests/integration/test_theme_vertical_slice.py -q`
  - `uv run --locked ruff check .`, `uv run --locked ruff format --check .`, and `uv lock --check`

  The baseline for the first three commands, over this plan's modules at `36f12ec`, was 2035 passed, 1 skipped and 2 deselected, in 143 s.

## Decisions

Taken by the user:
- **D18-1** (user, brief, 2026-10-11): a plan must not mandate copied logic. Its code calls or extracts a shared helper, never copies an existing block (plan 17's ruling at its Task 1). Applied in: Global Constraints; Tasks 2–6 (`cache_directory`, `cache_mode_problem`, `verify_files`, `files_hash`, and `parse_support` for scorer files).
- **D18-2** (user, brief F1, 2026-10-12): this slice is A1 and A2, with A9's dictionary rows for their records. A3–A5 come next and A8 last. A1 changes the run records that A4 and A5 read, and A5's scorer AUC needs A2's DeBERTa run. Applied in: scope.
- **D18-3** (user, brief F2, 2026-10-12): `pilot run` reuses only the pass's stored extraction run. It replays classification and support from the pass's caches into new runs, and decides under the calibrated policy.
  - Widening the workflow's stored-coding reuse (FP23 as written) cannot work. A stored coding run carries its decisions, and `reverify_coding_run` raises `policy_mismatch` against another policy (`coding/store.py:770`). The pass makes no decision.
  - Coding keys bind no run ID (`coding/cache.py:29`). A support target's ID is a digest of the target and its input hash (`support/resolve.py:366`). So every key matches.
  - Applied in: Task 1 (spec amendment: FP23, and A8's table row and last paragraph); §Handoffs.
- **D18-4** (user, planning, 2026-10-12): no schema version bump. `cache_mode` is a required field, and the dictionary records the compatibility decision. A bump would change every coding and support key, which digest their schema version, against A1's "Keys are unchanged". It would also turn an old extraction `CacheEntry` into a parse error that stops a run. Applied in: Tasks 2–4.
  - One consequence, found while planning: a support key binds the extraction run's whole record (`source_run`, `support/cache.py:107`). So a support key now also binds that record's `cache_mode` and `stability_run_id`. The key function is unchanged, but its value for a given run differs from what it would have been before plan 18.
  - Nothing is orphaned: no support cache predates plan 18 (none is committed, and no pilot pass has run).
  - `pilot run` reuses the pass's stored extraction run, so its replayed support keys bind the same record (FP23).
- **D18-5** (user, planning, 2026-10-12): `fresh` is `live` over its own new directory, `<cache>/fresh/<stability_run_id>/`. It never reads the main cache. A request repeated within the run is served from that run's reply, as in the live pass: two quotes with the same text in one target share a scorer key. Applied in: Task 1 (spec amendment: A1's bullet); Tasks 2–4.
- **D18-6** (user, planning, 2026-10-12): `jinja2==3.1.6`, already locked, joins themes' `support-nli` extra, since `apply_chat_template` needs it. The application gains a `live-models` extra pulling `earnings-themes[local-model,support-nli]`. Applied in: Tasks 5 and 6.

Planner defaults, for the user's review:
- **D18-7:** extraction's `RunRecord.cache_mode` is `None` when the run's adapter is not a `CachedAdapter`, as in most tests. Coding and support always run through their cache, so theirs is never null. Applied in: Task 2.
- **D18-8:** one check, `cache_mode_problem`, makes each run record refuse two things. A stability run ID must be present exactly under `fresh` (`invalid_stability_run`). A `replay` run must have dispatched nothing (`replay_dispatched`). Applied in: Tasks 2–4.
- **D18-9:** committed model files name directories relative to a models root that `build_runtime` takes as an argument. A scorer's file is a `LocalScorerConfig` with `directory` in place of `local_directory`, built at run time through `parse_support`, so no field list is copied. A8 picks how the root is supplied. Applied in: Task 6.
- **D18-10:** a chat model's `encoding_version` is `chat-tokens/1:` followed by its tokenizer files' `files_hash`. So the classifier's and judges' identities name the tokenizer that counts their requests. Applied in: Task 6.
- **D18-11:** the builder enforces Stage 8's `validate_panel` only. FP6's "neither judge is Gemma" is ADR 0006's choice of judges, not a refusal. The panel is checked before any model file is hashed or loaded. Applied in: Task 6.
- **D18-12:** the builder makes no server call. It checks the configured runtime identity through the bindings' preflight, and every reply still names its model. It does not query the server's own build, which B1's smoke records. Applied in: Task 6.

---

## File Structure

| File | Change | Responsibility |
| --- | --- | --- |
| `specs/feasibility-pilot-and-threshold-calibration.md` | Modify | FP23, A1 and A8 amendments (Task 1); the slice stamp (Task 7) |
| `packages/earnings-themes/src/earnings_themes/extraction/records.py` | Modify | `CacheMode` (moved here, gains `FRESH`), `STABILITY_RUN_PATTERN`, `StabilityRunId`, `cache_mode_problem`; `RunRecord` fields |
| `packages/earnings-themes/src/earnings_themes/extraction/cache.py` | Modify | `cache_directory`; `CachedAdapter` takes `stability_run_id`, exposes `mode` and `stability_run_id` |
| `packages/earnings-themes/src/earnings_themes/extraction/run.py` | Modify | `extract_run` records the adapter's cache mode |
| `packages/earnings-themes/src/earnings_themes/coding/cache.py` | Modify | `CodingCache` takes `fresh` and `stability_run_id` |
| `packages/earnings-themes/src/earnings_themes/coding/records.py` | Modify | `ProposalRunRecord` takes `fresh` and `stability_run_id` |
| `packages/earnings-themes/src/earnings_themes/coding/run.py` | Modify | `propose_run` records the stability run ID |
| `packages/earnings-themes/src/earnings_themes/coding/classify.py` | Modify | The per-claim mode check accepts `fresh` |
| `packages/earnings-themes/src/earnings_themes/coding/store.py` | Modify | A dispatched attempt is valid under `live` or `fresh` |
| `packages/earnings-themes/src/earnings_themes/support/cache.py` | Modify | `SupportCache` takes `fresh` and `stability_run_id` |
| `packages/earnings-themes/src/earnings_themes/support/records.py` | Modify | `SupportRunRecord.cache_mode` and `stability_run_id` |
| `packages/earnings-themes/src/earnings_themes/support/run.py` | Modify | `assess_run` records both |
| `packages/earnings-themes/src/earnings_themes/support/model_files.py` | Create | `verify_files(directory, files)` and `files_hash(files)`, shared by the scorers, the judge binding, the token counter and the builder |
| `packages/earnings-themes/src/earnings_themes/support/nli.py` | Modify | Its file check moves to `model_files.verify_files` |
| `packages/earnings-themes/src/earnings_themes/support/judges.py` | Modify | `transport_weights_hash` calls `model_files.files_hash` |
| `packages/earnings-themes/src/earnings_themes/support/chat_tokens.py` | Create | `ChatTokenizerConfig`, `ChatTokenCounter` |
| `packages/earnings-themes/pyproject.toml` | Modify | `jinja2==3.1.6` in `support-nli` |
| `apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py` | Create | `RuntimeManifest`, `ChatModelFile`, `LiveRuntime`, `build_runtime` |
| `apps/earnings-pipeline/pyproject.toml` | Modify | The `live-models` extra |
| `uv.lock` | Modify | Extras metadata only |
| `docs/data-dictionary.md` | Modify | Every new field, value, model and compatibility note |
| `tests/contracts/test_data_dictionary.py` | Modify | Registers `CacheMode`, `ChatTokenizerConfig`, `RuntimeManifest`, `ChatModelFile`, `LiveRuntime` |
| Tests under `packages/earnings-themes/tests/` and `apps/earnings-pipeline/tests/` | Modify / Create | As each task lists |

---

### Task 1: Amend the spec: FP23, A1 and A8 (docs only)

**Files:**
- Modify: `specs/feasibility-pilot-and-threshold-calibration.md:72` (FP23), `:139` (A1), `:207` and `:219-222` (A8)

**Interfaces:**
- Consumes: nothing.
- Produces: the amended FP23, A1 and A8 that Tasks 2–4 and A8's later plan implement.

The spec's status line and every other line stay as they are. The user approved each change's substance on 2026-10-12 (D18-3, D18-5). They approve this exact wording at the plan review.

- [ ] **Step 1: Replace FP23's row**

Replace this line:

```text
| FP23 | *(design)* **Replay reuses the pass's stored runs.** Support cache keys bind the extraction run's record (`support/cache.py:107`), so a re-run extraction would miss every support entry. `pilot run` therefore never re-extracts. It reuses the pass's stored extraction, coding and support runs through the workflow's stored-run reuse, and dispatches nothing. Replay needs no model server running. |
```

with:

```text
| FP23 | *(design; amended by the user, plan 18, 2026-10-12)* **Replay reuses the pass's stored extraction run and replays its caches.** Support cache keys bind the extraction run's record (`support/cache.py:107`), so a re-run extraction would miss every support entry. `pilot run` therefore never re-extracts: it reuses the pass's stored extraction run through the workflow's stored-run reuse. It does not reuse the pass's coding or support runs. A stored coding run carries its decisions, `reverify_coding_run` refuses one made under another policy (`policy_mismatch`), and the pass makes no decision. So `pilot run` replays classification and support from the pass's caches into new runs, and decides under the calibrated policy. Coding keys bind no run ID, and a support target's ID is a digest of the target and its input hash, so every key matches and nothing dispatches. Replay needs no model server running. |
```

- [ ] **Step 2: Replace A1's first bullet**

Replace these two lines:

```text
- `fresh` always dispatches and never reads, even on a key that is already cached.
- It writes each reply under `<cache>/fresh/<stability_run_id>/`. So it never collides with the main cache's bytes, and a stability run replays afterwards from its own directory (R14.6).
```

with:

```text
- `fresh` never reads the main cache, even on a key that is already cached there. It is `live` over its own directory, `<cache>/fresh/<stability_run_id>/`, which starts empty. So every first request dispatches, and a request repeated within the run is served from that run's own reply, as in the live pass. *(Amended by the user, plan 18, 2026-10-12: two quotes with the same text in one target share a scorer key.)*
- It writes each reply there. So it never collides with the main cache's bytes, and a stability run replays afterwards from its own directory (R14.6).
```

- [ ] **Step 3: Replace A8's `pilot run` row and its last paragraph**

In the table, replace:

```text
| `pilot run --partition train\|dev` | Runs `run_theme_workflow` under the calibrated policy, reusing the partition's stored pass runs (FP23). Refuses without a calibration artifact, or if any request would dispatch. |
```

with:

```text
| `pilot run --partition train\|dev` | Runs `run_theme_workflow` under the calibrated policy, reusing the partition's stored pass extraction and replaying its coding and support caches (FP23). Refuses without a calibration artifact, or if any request would dispatch. |
```

Then replace the paragraph:

```text
The workflow's stored-run reuse (`theme_workflow.py`) now requires a stored coding run
to have been recorded in `replay` mode. Plan A widens that to `live`, provided every
other identity it checks still matches. A test shows reuse of a `live` pass dispatching
nothing. A `fresh` run is never reused by `pilot run`.
```

with:

```text
The workflow's stored-run reuse (`theme_workflow.py`) is unchanged: it reuses a stored
coding run only when that run was recorded in `replay` mode. `pilot run` reuses the
pass's stored extraction run only, and replays coding and support from the pass's
caches (FP23). A test shows such a run over a `live` pass dispatching nothing. A `fresh`
run is never reused by `pilot run`. *(Amended by the user, plan 18, 2026-10-12.)*
```

- [ ] **Step 4: Check the edits**

Run: `grep -c "plan 18, 2026-10-12" specs/feasibility-pilot-and-threshold-calibration.md`
Expected: `3`

Run: `grep -n "widens that to" specs/feasibility-pilot-and-threshold-calibration.md`
Expected: no output, exit 1.

Run: `git diff --stat`
Expected: one file changed. The roadmap, CLAUDE.md and the spec's first 41 lines are untouched.

- [ ] **Step 5: Commit**

```bash
git log -3 --oneline
git add specs/feasibility-pilot-and-threshold-calibration.md
git commit -m "docs(specs): amend FP23, A1 and A8 for Stage 11 plan A's slice 2"
```

---

### Task 2: Extraction's fresh mode (A1)

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/extraction/records.py:26-41` (imports and constants), `:331-369` (`RunRecord`)
- Modify: `packages/earnings-themes/src/earnings_themes/extraction/cache.py:1-128`
- Modify: `packages/earnings-themes/src/earnings_themes/extraction/run.py:26-50` (imports), `:177-246` (`extract_run`)
- Modify: `packages/earnings-themes/tests/test_extraction_cache.py:153-161` and append tests
- Modify: `packages/earnings-themes/tests/test_extraction_run.py` (imports; append tests)
- Modify: `packages/earnings-themes/tests/test_extraction_records.py:8-20` (imports), `:150-169` (`run_record`); append a test
- Modify: `packages/earnings-themes/tests/support/cases.py:100-120` (a hand-built `RunRecord`)
- Modify: `docs/data-dictionary.md` (extraction intro, `RunRecord`, `CacheEntry`, a new `CacheMode` section)
- Modify: `tests/contracts/test_data_dictionary.py:285-287` (`ENUMS`)

**Interfaces:**
- Consumes: nothing new.
- Produces, in `earnings_themes.extraction.records`:
  - `STABILITY_RUN_PATTERN: str`;
  - `StabilityRunId`, an annotated `str`;
  - `class CacheMode(StrEnum)`: `REPLAY = "replay"`, `LIVE = "live"`, `FRESH = "fresh"`;
  - `cache_mode_problem(mode: str | None, stability_run_id: str | None, dispatched: int) -> str | None`;
  - `RunRecord.cache_mode: CacheMode | None` and `RunRecord.stability_run_id: StabilityRunId | None = None`.
- Produces, in `earnings_themes.extraction.cache`:
  - `cache_directory(directory: Path, mode: CacheMode | str, stability_run_id: str | None) -> tuple[CacheMode, Path]`;
  - `CachedAdapter(inner, directory, mode, *, stability_run_id: str | None = None)`, with properties `mode -> CacheMode` and `stability_run_id -> str | None`.
- `earnings_themes.extraction.cache.CacheMode` stays importable, since `cache.py` imports it.

- [ ] **Step 1: Write the failing tests**

In `packages/earnings-themes/tests/test_extraction_cache.py`, `test_an_identical_key_hits_and_calls_nothing` loops over every `CacheMode`, and `fresh` needs a stability run ID. Narrow its loop to the two modes it means:

```python
    for mode in (CacheMode.LIVE, CacheMode.REPLAY):
```

Then append:

```python
def test_fresh_needs_a_safe_stability_run_id_and_only_fresh_takes_one(
    tmp_path: Path,
) -> None:
    calls: list = []
    for mode, stability_run_id in (
        ("fresh", None),
        ("live", "stability-1"),
        ("replay", "stability-1"),
        ("fresh", ".."),
        ("fresh", "a/b"),
        ("fresh", ""),
    ):
        with pytest.raises(ValueError):
            CachedAdapter(
                echo(IDENTITY, calls), tmp_path, mode, stability_run_id=stability_run_id
            )
    assert (calls, list(tmp_path.iterdir())) == ([], [])


def test_fresh_never_reads_the_main_cache_and_writes_its_own(tmp_path: Path) -> None:
    """A1: a fully populated cache gives zero hits under fresh."""
    calls: list = []
    stored = CachedAdapter(echo(IDENTITY, calls), tmp_path, "live").complete(request())
    fresh = CachedAdapter(
        echo(IDENTITY, calls), tmp_path, "fresh", stability_run_id="stability-1"
    )
    assert (fresh.mode, fresh.stability_run_id) == (CacheMode.FRESH, "stability-1")
    reply = fresh.complete(request())
    assert (len(calls), reply.cached) == (2, False)
    name = f"{digest(cache_key(request(), IDENTITY))}.json"
    assert (tmp_path / "fresh" / "stability-1" / name).is_file()
    again = CachedAdapter(echo(IDENTITY, calls), tmp_path, "live").complete(request())
    assert (len(calls), again) == (2, stored.model_copy(update={"cached": True}))


def test_fresh_serves_a_repeat_within_its_run_from_its_own_reply(
    tmp_path: Path,
) -> None:
    """A1 as plan 18 amends it: fresh is live over its own new directory."""
    calls: list = []
    fresh = CachedAdapter(
        echo(IDENTITY, calls), tmp_path, "fresh", stability_run_id="stability-1"
    )
    first = fresh.complete(request())
    second = fresh.complete(request())
    assert (len(calls), second) == (1, first.model_copy(update={"cached": True}))
```

In `packages/earnings-themes/tests/test_extraction_run.py`, add `from earnings_themes.extraction.cache import CachedAdapter, CacheMode` to the imports, then append:

```python
def test_a_fresh_run_dispatches_every_request_over_a_populated_cache(
    fixtures, template, cite, tmp_path
) -> None:
    """A1: zero hits under fresh; dispatches equal requests; a later replay over the
    fresh directory reproduces the run."""
    bundles = list(fixtures.values())
    live = run(
        bundles,
        CachedAdapter(
            ScriptedAdapter(lambda request: cite(request, model="scripted")),
            tmp_path,
            "live",
        ),
        template,
    )
    adapter = ScriptedAdapter(lambda request: cite(request, model="scripted"))
    fresh = run(
        bundles,
        CachedAdapter(adapter, tmp_path, "fresh", stability_run_id="stability-1"),
        template,
    )
    assert (live.record.cache_mode, live.record.stability_run_id) == (
        CacheMode.LIVE,
        None,
    )
    assert (fresh.record.cache_mode, fresh.record.stability_run_id) == (
        CacheMode.FRESH,
        "stability-1",
    )
    assert (fresh.record.cache_hits, fresh.record.requests, len(adapter.requests)) == (
        0,
        37,
        37,
    )
    silent = ScriptedAdapter(lambda _: pytest.fail("a replay dispatched"))
    replay = run(
        bundles,
        CachedAdapter(silent, tmp_path / "fresh" / "stability-1", "replay"),
        template,
    )
    assert (replay.record.requests, replay.record.cache_hits) == (0, 37)
    assert (replay.quotes, replay.claims) == (fresh.quotes, fresh.claims)


def test_a_run_through_no_cache_records_no_mode(synthetic, template, cite) -> None:
    adapter = ScriptedAdapter(lambda request: cite(request, model="scripted"))
    record = run([synthetic.bundle], adapter, template).record
    assert (record.cache_mode, record.stability_run_id) == (None, None)
```

In `packages/earnings-themes/tests/test_extraction_records.py`, add `CacheMode` to the `earnings_themes.extraction.records` import list, add `"cache_mode": None,` to `run_record`'s `fields` after `"configuration_hash": HASH,`, then append:

```python
def test_a_run_s_cache_mode_and_stability_run_id_agree() -> None:
    """A1 (plan 18, D18-8): a stability run ID goes with fresh alone, and replay
    dispatches nothing."""
    fresh = run_record(cache_mode=CacheMode.FRESH, stability_run_id="stability-1")
    assert fresh.stability_run_id == "stability-1"
    replay = run_record(cache_mode=CacheMode.REPLAY, requests=0, unreported=0)
    assert replay.cache_mode is CacheMode.REPLAY
    for changes in (
        {"cache_mode": CacheMode.FRESH},
        {"cache_mode": CacheMode.LIVE, "stability_run_id": "stability-1"},
        {"stability_run_id": "stability-1"},
        {"cache_mode": CacheMode.REPLAY},
        {"cache_mode": CacheMode.FRESH, "stability_run_id": ".."},
    ):
        with pytest.raises(ValidationError):
            run_record(**changes)
```

(`run_record`'s defaults hold `requests` 1 and `unreported` 1, so `{"cache_mode": CacheMode.REPLAY}` is a replay that dispatched.)

In `packages/earnings-themes/tests/support/cases.py`, add `cache_mode=None,` to the hand-built `RunRecord(...)` (`:100`), after `configuration_hash=...`.

- [ ] **Step 2: Run them, and watch them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_extraction_cache.py packages/earnings-themes/tests/test_extraction_run.py packages/earnings-themes/tests/test_extraction_records.py -q`
Expected: FAIL.
- `test_extraction_records.py` fails at import: `cannot import name 'CacheMode' from 'earnings_themes.extraction.records'`.
- `test_extraction_cache.py`'s new tests fail with `TypeError: ... unexpected keyword argument 'stability_run_id'`.
- `test_extraction_run.py`'s new tests fail with the same `TypeError`, and with `AttributeError: 'RunRecord' object has no attribute 'cache_mode'`.

- [ ] **Step 3: Add the mode, the ID type and the shared check to `extraction/records.py`**

Add `StringConstraints` to the `pydantic` import list (`:28-34`). After `BILLABLE_COST = "none, self-hosted"` (`:41`), add:

```python
STABILITY_RUN_PATTERN = r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}"
"""A stability run's ID: one safe path component, never ``.`` or ``..`` (A1)."""
StabilityRunId = Annotated[
    str, StringConstraints(pattern=rf"^{STABILITY_RUN_PATTERN}$")
]


class CacheMode(StrEnum):
    """How a reply cache uses its directory (the Stage 11 spec, A1, as plan 18
    amends it). ``CachedAdapter``, ``CodingCache`` and ``SupportCache`` share it."""

    REPLAY = "replay"
    """A hit returns the stored reply; a miss is ``replay_miss`` and calls nothing."""
    LIVE = "live"
    """A hit returns the stored reply; a miss calls the model and stores its reply."""
    FRESH = "fresh"
    """``live`` over ``<directory>/fresh/<stability_run_id>/``, which starts empty: the
    main directory is never read."""


def cache_mode_problem(
    mode: str | None, stability_run_id: str | None, dispatched: int
) -> str | None:
    """Why a run record's cache mode, stability run ID and dispatches disagree, or
    ``None``. A stability run ID goes with ``fresh`` alone, and ``replay`` dispatches
    nothing. The extraction, coding and support run records each call it (D18-8)."""
    if (stability_run_id is not None) != (mode == CacheMode.FRESH):
        return "invalid_stability_run"
    if mode == CacheMode.REPLAY and dispatched:
        return "replay_dispatched"
    return None
```

In `RunRecord`, after `configuration_hash: Sha256Hex`, add:

```python
    cache_mode: CacheMode | None
    """The cache the run went through; ``None`` when its adapter is not a
    ``CachedAdapter`` (A1, D18-7)."""
    stability_run_id: StabilityRunId | None = None
    """The stability run whose directory ``fresh`` used, and only then."""
```

In `RunRecord._consistent`, just before `return self`, add:

```python
        problem = cache_mode_problem(
            self.cache_mode, self.stability_run_id, self.requests
        )
        if problem is not None:
            raise ValueError(problem)
```

- [ ] **Step 4: Resolve the directory once, in `extraction/cache.py`**

Replace the module docstring's "Two modes" bullet:

```text
- **Two modes.** A hit returns the stored reply and calls nothing. In ``replay``, a
  miss is ``replay_miss`` and never a call. In ``live``, a miss calls the inner
  adapter and stores its reply atomically, under a directory the caller supplies.
```

with:

```text
- **Three modes.** A hit returns the stored reply and calls nothing. In ``replay``, a
  miss is ``replay_miss`` and never a call. In ``live``, a miss calls the inner
  adapter and stores its reply atomically, under a directory the caller supplies.
  ``fresh`` is ``live`` over ``<directory>/fresh/<stability_run_id>/``, which starts
  empty, so it never reads the main directory (the Stage 11 spec, A1, as plan 18
  amends it).
```

Replace `from enum import StrEnum` with `import re` (keep the imports sorted: `import os`, `import re`, then `from pathlib import Path`). Add `STABILITY_RUN_PATTERN` and `CacheMode` to the `earnings_themes.extraction.records` import. Delete the `class CacheMode(StrEnum)` block (`:91-93`). Add this function before `class CachedAdapter`:

```python
def cache_directory(
    directory: Path, mode: CacheMode | str, stability_run_id: str | None
) -> tuple[CacheMode, Path]:
    """``mode`` as its member, and the directory its replies are read from and
    written to: ``directory``, or under ``fresh``,
    ``directory/fresh/<stability_run_id>``, which no other run shares. Raises
    ``ValueError`` for an unknown mode, and unless a stability run ID, one safe path
    component, is given exactly when the mode is ``fresh``. ``CachedAdapter``,
    ``CodingCache`` and ``SupportCache`` each call it (A1)."""
    member = CacheMode(mode)
    if (stability_run_id is not None) != (member is CacheMode.FRESH):
        raise ValueError("a stability run ID goes with the fresh mode alone")
    if member is not CacheMode.FRESH:
        return member, Path(directory)
    if type(stability_run_id) is not str or not re.fullmatch(
        STABILITY_RUN_PATTERN, stability_run_id
    ):
        raise ValueError("the stability run ID is not one safe path component")
    return member, Path(directory) / "fresh" / stability_run_id
```

Replace `CachedAdapter`'s docstring and `__init__`, and add the two properties after `identity`:

```python
class CachedAdapter:
    """The cache wrapper: an adapter over ``inner``, with ``inner``'s identity. A mode
    given as its value reads as its member, so ``"replay"`` never calls ``inner``.
    Any other value raises ``ValueError`` here, as does a stability run ID that is
    missing under ``fresh``, given under another mode, or unsafe."""

    def __init__(
        self,
        inner: ModelAdapter,
        directory: Path,
        mode: CacheMode | str,
        *,
        stability_run_id: str | None = None,
    ) -> None:
        self._inner = inner
        self._mode, self._directory = cache_directory(directory, mode, stability_run_id)
        self._stability_run_id = stability_run_id

    @property
    def identity(self) -> AdapterIdentity:
        return self._inner.identity

    @property
    def mode(self) -> CacheMode:
        return self._mode

    @property
    def stability_run_id(self) -> str | None:
        return self._stability_run_id
```

`complete` is unchanged. Under `fresh`, its directory is the fresh one, so a repeat within the run hits there.

- [ ] **Step 5: Record the mode in `extract_run`**

In `extraction/run.py`, add `from earnings_themes.extraction.cache import CachedAdapter` after the `earnings_themes.extraction.adapters` import. In `extract_run`, before `record = RunRecord(`, add:

```python
    cached = adapter if isinstance(adapter, CachedAdapter) else None
```

and in `RunRecord(...)`, after `configuration_hash=digest(configuration),`, add:

```python
        cache_mode=None if cached is None else cached.mode,
        stability_run_id=None if cached is None else cached.stability_run_id,
```

Add one sentence to `extract_run`'s docstring: `The run record names the cache's mode and stability run ID, or None for an adapter that is not a CachedAdapter.`

- [ ] **Step 6: Run the tests, and watch them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/test_extraction_cache.py packages/earnings-themes/tests/test_extraction_run.py packages/earnings-themes/tests/test_extraction_records.py packages/earnings-themes/tests/test_extraction_store.py packages/earnings-themes/tests/test_import_boundaries.py -q`
Expected: PASS.

- [ ] **Step 7: Document it**

In `docs/data-dictionary.md`:

1. In `## earnings-themes extraction records, schema version 1`, after the first paragraph (the one ending `…and a refusal prints as its reason and IDs alone\n(GS13).`), insert this paragraph:

   ```text
   **Cache modes (Stage 11, plan 18).** `CacheMode` is `replay`, `live` or `fresh`, and
   extraction, coding and support share it. `fresh` is `live` over
   `<cache>/fresh/<stability_run_id>/`, which starts empty: it never reads the main
   cache, and a request repeated within the run is served from that run's own reply
   (A1). `RunRecord` gained `cache_mode` and `stability_run_id`. The schema version
   stays `1`, so no extraction cache key changes. A run record written before plan 18
   has no `cache_mode`, and is refused as malformed; none was committed (D18-4).
   ```

2. In the `### \`RunRecord\`` table, after the `configuration_hash` row, insert:

   ```text
   | `cache_mode` | `CacheMode` or null | The cache the run went through; null when its adapter is not a `CachedAdapter`; a `replay` run dispatched nothing |
   | `stability_run_id` | ID or null | The stability run whose directory `fresh` used; set exactly when `cache_mode` is `fresh` |
   ```

3. In `### \`CacheEntry\``, replace `written atomically in \`live\` mode under` with `written atomically in \`live\` or \`fresh\` mode under`.

4. Immediately before `### \`LocalModelConfig\``, insert:

   ```text
   ### `CacheMode`

   How a `CachedAdapter`, a `CodingCache` or a `SupportCache` uses its directory
   (`earnings_themes.extraction.records`; A1). `cache_directory(directory, mode,
   stability_run_id)` (`earnings_themes.extraction.cache`) resolves the directory for
   all three, and `cache_mode_problem` checks each run record's mode, stability run ID
   and dispatches.

   | Value | Meaning |
   | --- | --- |
   | `replay` | A hit returns the stored reply; a miss is `replay_miss`, and nothing dispatches |
   | `live` | A hit returns the stored reply; a miss dispatches and stores the reply |
   | `fresh` | `live` over `<directory>/fresh/<stability_run_id>/`, which starts empty; the main directory is never read |

   ```

In `tests/contracts/test_data_dictionary.py`, add `extraction.CacheMode,` to `ENUMS` after `extraction.DocumentOutcome,`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`
Expected: PASS.

- [ ] **Step 8: Run the wider scoped checks**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/coding packages/earnings-themes/tests/support packages/earnings-themes/tests/analysis -q`
Expected: PASS. The coding and support runs now carry an extraction record with `cache_mode`, and nothing pins its hash.

- [ ] **Step 9: Commit**

```bash
git log -3 --oneline
uv run --locked ruff format packages/earnings-themes tests/contracts
uv run --locked ruff check .
git add packages/earnings-themes docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(themes): fresh cache mode for extraction, recorded on the run (A1)"
```

---

### Task 3: Coding's fresh mode (A1)

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/coding/cache.py:1-25` (imports), `:78-85` (`CodingCache`)
- Modify: `packages/earnings-themes/src/earnings_themes/coding/records.py:19-20` (imports), `:316-369` (`ProposalRunRecord`)
- Modify: `packages/earnings-themes/src/earnings_themes/coding/run.py:174-195` (`propose_run`'s record)
- Modify: `packages/earnings-themes/src/earnings_themes/coding/classify.py:409` (the per-claim mode check)
- Modify: `packages/earnings-themes/src/earnings_themes/coding/store.py:514`
- Modify: `packages/earnings-themes/tests/coding/cases.py:157-198` (`make_proposal_job`)
- Modify: `packages/earnings-themes/tests/coding/test_cache.py`, `test_run.py`, `test_store.py` (append tests)
- Modify: `docs/data-dictionary.md` (coding intro, `CodingCache` prose, `ProposalRunRecord`, `CodingRunRecord`)

**Interfaces:**
- Consumes (Task 2): `cache_directory`, `StabilityRunId`, `cache_mode_problem`.
- Produces:
  - `CodingCache(directory: Path, mode: Literal["live", "replay", "fresh"], *, stability_run_id: str | None = None)`, with attributes `mode: str` and `stability_run_id: str | None`;
  - `ProposalRunRecord.cache_mode: Literal["live", "replay", "fresh"]` and `ProposalRunRecord.stability_run_id: StabilityRunId | None = None`, both inherited by `CodingRunRecord`;
  - `make_proposal_job(...).run(replies, cache_mode="live", *, ceilings=None, claim_order=None, stability_run_id=None, directory=None)`.

Three existing tests reject `fresh`, and all three keep passing: a `fresh` mode without its stability run ID is still refused.
- `test_cache.py:266`: the constructor raises `malformed_record`.
- `test_run.py:693` sets `cache.mode = "fresh"` on a live cache. The run's record then has `fresh` and no ID, so `checked` refuses it before any dispatch.
- `test_store.py:161` sets `cache_mode` to `fresh` in a stored manifest, which leaves its configuration hash wrong and its ID missing.

Leave them unchanged.

- [ ] **Step 1: Write the failing tests**

In `packages/earnings-themes/tests/coding/cases.py`, give `make_proposal_job`'s inner `run` two keyword arguments. Replace:

```python
    def run(replies, cache_mode="live", *, ceilings=None, claim_order=None):
```

with:

```python
    def run(
        replies,
        cache_mode="live",
        *,
        ceilings=None,
        claim_order=None,
        stability_run_id=None,
        directory=None,
    ):
```

and replace:

```python
            cache=CodingCache(root / "classifier-cache", cache_mode),
```

with:

```python
            cache=CodingCache(
                directory or root / "classifier-cache",
                cache_mode,
                stability_run_id=stability_run_id,
            ),
```

Append to `packages/earnings-themes/tests/coding/test_cache.py`:

```python
def test_fresh_reads_only_its_own_new_directory(
    coding_request, classifier_identity, tmp_path
):
    """A1 (plan 18): fresh is live over <cache>/fresh/<id>/, which starts empty."""
    model = classifier_identity.runtime.model_id
    main = ModelReply(text='{"main": 1}', model=model)
    CodingCache(tmp_path, "live").put(
        coding_request, classifier_identity, main, input_tokens=5
    )
    fresh = CodingCache(tmp_path, "fresh", stability_run_id="stability-1")
    assert (fresh.mode, fresh.stability_run_id) == ("fresh", "stability-1")
    assert fresh.get(coding_request, classifier_identity) is None
    again = ModelReply(text='{"again": 1}', model=model)
    reference = fresh.put(coding_request, classifier_identity, again, input_tokens=5)
    assert fresh.get(coding_request, classifier_identity).reply == again
    assert (tmp_path / "fresh" / "stability-1" / reference).is_file()
    replayed = CodingCache(tmp_path, "replay").get(coding_request, classifier_identity)
    assert replayed.reply == main


@pytest.mark.parametrize(
    "mode,stability_run_id",
    [
        ("live", "stability-1"),
        ("replay", "stability-1"),
        ("fresh", ".."),
        ("fresh", "a/b"),
    ],
)
def test_a_stability_run_id_goes_with_fresh_alone(tmp_path, mode, stability_run_id):
    with pytest.raises(CodingError, match="^malformed_record$"):
        CodingCache(tmp_path / "unused", mode, stability_run_id=stability_run_id)
    assert list(tmp_path.iterdir()) == []
```

Append to `packages/earnings-themes/tests/coding/test_run.py`:

```python
def test_fresh_dispatches_every_request_and_replays_from_its_own_directory(
    proposal_job,
):
    """A1 (plan 18): over a populated cache, fresh hits nothing and dispatches every
    request, and a replay over its directory reproduces the proposals."""
    reply = {"theme_ids": ["capacity"], "attributes": {}}
    _, live_calls = proposal_job.run([reply])
    fresh, fresh_calls = proposal_job.run(
        [reply], "fresh", stability_run_id="stability-1"
    )
    record = fresh.record
    assert (record.cache_mode, record.stability_run_id) == ("fresh", "stability-1")
    assert record.cache_hits == 0
    assert record.requests == fresh_calls == live_calls == 1
    replay, replay_calls = proposal_job.run(
        [],
        "replay",
        directory=proposal_job.root / "classifier-cache" / "fresh" / "stability-1",
    )
    assert (replay_calls, replay.record.cache_hits) == (0, 1)
    assert replay.targets == fresh.targets
```

Append to `packages/earnings-themes/tests/coding/test_store.py`:

```python
def test_a_fresh_coding_run_writes_and_reads_back(tmp_path, proposal_job):
    """A1 (plan 18): a dispatched attempt is valid under fresh, as under live."""
    proposals, _ = proposal_job.run(
        [{"theme_ids": ["capacity"], "attributes": {}}],
        "fresh",
        stability_run_id="stability-1",
    )
    case = make_assessed_case(proposals, proposal_job.sources, tmp_path / "assessed")
    policy = FixturePolicy(case.proposals, case.support)
    result = make_coding_run(case, policy)
    path = write_coding_run(
        tmp_path / "coding", result, case.sources, case.support, policy
    )
    stored = read_coding_run(path)
    assert (stored.record.cache_mode, stored.record.stability_run_id) == (
        "fresh",
        "stability-1",
    )
```

- [ ] **Step 2: Run them, and watch them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/coding -q`
Expected: FAIL.
- The `test_cache.py` tests fail with `TypeError: ... unexpected keyword argument 'stability_run_id'`.
- The `test_run.py` and `test_store.py` tests fail with the same `TypeError`, raised in `make_proposal_job`.

- [ ] **Step 3: Implement**

In `coding/cache.py`, add `from earnings_themes.extraction.cache import cache_directory` after the `earnings_themes.extraction.adapters` import. Replace `CodingCache`'s docstring and `__init__` with:

```python
class CodingCache:
    """Caller-selected local directory, or under ``fresh`` its stability run's own
    (A1); no dispatch or startup I/O."""

    def __init__(
        self,
        directory: Path,
        mode: Literal["live", "replay", "fresh"],
        *,
        stability_run_id: str | None = None,
    ) -> None:
        if type(mode) is not str:
            raise CodingError("malformed_record")
        try:
            member, self._directory = cache_directory(
                Path(directory), mode, stability_run_id
            )
        except ValueError:
            raise CodingError("malformed_record") from None
        self.mode = member.value
        self.stability_run_id = stability_run_id
```

In `coding/records.py`, replace `from earnings_themes.extraction.records import Parameters` with:

```python
from earnings_themes.extraction.records import (
    Parameters,
    StabilityRunId,
    cache_mode_problem,
)
```

In `ProposalRunRecord`, replace `cache_mode: Literal["live", "replay"]` with:

```python
    cache_mode: Literal["live", "replay", "fresh"]
    stability_run_id: StabilityRunId | None = None
```

In `ProposalRunRecord._bindings`, just before `return self`, add:

```python
        problem = cache_mode_problem(
            self.cache_mode, self.stability_run_id, self.requests
        )
        if problem is not None:
            raise ValueError(problem)
```

In `coding/run.py`, in `ProposalRunRecord.model_construct(...)`, after `cache_mode=cache.mode,` add `stability_run_id=cache.stability_run_id,`. Leave the configuration dictionary alone: the stability run ID is provenance, not configuration, so `CONFIGURATION_FIELDS` (`coding/store.py:225`) is unchanged too.

In `coding/classify.py:409`, `classify_claim` checks the mode again for each claim. Replace:

```python
        if type(cache.mode) is not str or cache.mode not in ("live", "replay"):
```

with:

```python
        if type(cache.mode) is not str or cache.mode not in ("live", "replay", "fresh"):
```

Without this, every claim in a fresh run is refused as `malformed_record`, and the fresh run test above fails. Its dispatch branch needs no change: only `replay` stops at a miss (`classify.py:281`), so `fresh` dispatches as `live` does.

In `coding/store.py:514`, replace:

```python
        _require(record.cache_mode == "live" and not row.cached)
```

with:

```python
        _require(record.cache_mode in ("live", "fresh") and not row.cached)
```

- [ ] **Step 4: Run the tests, and watch them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/coding packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_coding_contracts.py -q`
Expected: PASS.

- [ ] **Step 5: Document it**

In `docs/data-dictionary.md`:

1. In `## earnings-themes coding records, schema version 1`, after the paragraph ending `` `CodingRecord` is the separate base for persisted coding schema 1 records.``, insert:

   ```text
   **Fresh mode (Stage 11, plan 18).** `ProposalRunRecord` and `CodingRunRecord` take
   `cache_mode` `fresh` and a `stability_run_id` (A1). The schema version stays `1`, and
   the stability run ID defaults to null, so coding keys and stored live or replay runs
   are unchanged (D18-4).
   ```

2. Replace the first three lines of the `CodingCache` paragraph:

   ```text
   `CodingCache(directory: Path, mode: Literal["live", "replay"])` selects a local
   raw-artifact directory without startup I/O. Mode strings are exact; neither mode
   provides fresh-call bypass, and lookup performs no inference. The coding cache
   ```

   with:

   ```text
   `CodingCache(directory: Path, mode: Literal["live", "replay", "fresh"], *,
   stability_run_id=None)` selects a local raw-artifact directory without startup I/O.
   Mode strings are exact; `fresh` is `live` over `<directory>/fresh/<stability_run_id>/`
   (A1, plan 18), and lookup performs no inference. The coding cache
   ```

3. In `### \`ProposalRunRecord\``, replace the `cache_mode` row with these two rows:

   ```text
   | `cache_mode` | live, replay, fresh | Explicit raw-cache operation mode; `fresh` is live over the stability run's own directory (A1) |
   | `stability_run_id` | safe ID or null | Stability run whose directory `fresh` used; set exactly when `cache_mode` is `fresh`; outside the configuration hash |
   ```

4. In `### \`CodingRunRecord\``, replace the `cache_mode` row with:

   ```text
   | `cache_mode` | live, replay, fresh | Original cache operation, including empty/refused runs |
   | `stability_run_id` | safe ID or null | Original stability run ID, set exactly under `fresh` |
   ```

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git log -3 --oneline
uv run --locked ruff format packages/earnings-themes
uv run --locked ruff check .
git add packages/earnings-themes docs/data-dictionary.md
git commit -m "feat(themes): fresh cache mode for coding, recorded on the run (A1)"
```

---

### Task 4: Support's fresh mode (A1), and the second support run's judge reuse (A2)

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/support/cache.py:25-27` (imports), `:174-181` (`SupportCache`)
- Modify: `packages/earnings-themes/src/earnings_themes/support/records.py:26` (imports), `:396-447` (`SupportRunRecord`)
- Modify: `packages/earnings-themes/src/earnings_themes/support/run.py:110-140` (`assess_run`'s record)
- Modify: `packages/earnings-themes/tests/support/test_records.py:92-118` (the `run` payload); append a test
- Modify: `packages/earnings-themes/tests/support/test_cache.py`, `test_run.py` (append tests)
- Modify: `docs/data-dictionary.md` (support intro, `SupportRunRecord`, `SupportCache` prose)

**Interfaces:**
- Consumes (Task 2): `cache_directory`, `StabilityRunId`, `cache_mode_problem`.
- Produces:
  - `SupportCache(directory: Path, mode: Literal["live", "replay", "fresh"], *, stability_run_id: str | None = None)`, with attributes `mode: str` and `stability_run_id: str | None`;
  - `SupportRunRecord.cache_mode: Literal["live", "replay", "fresh"]` and `SupportRunRecord.stability_run_id: StabilityRunId | None = None`.

- [ ] **Step 1: Write the failing tests**

In `packages/earnings-themes/tests/support/test_records.py`, add `"cache_mode": "live",` to the `run` payload after `"configuration_hash": H,`. Its counts dispatched, so it is a live run. Then append:

```python
@pytest.mark.parametrize(
    "changes",
    [
        {"cache_mode": "fresh"},
        {"stability_run_id": "stability-1"},
        {"cache_mode": "replay"},
        {"cache_mode": "replay", "requests": 0},
        {"cache_mode": "fresh", "stability_run_id": ".."},
    ],
)
def test_a_run_s_cache_mode_and_stability_run_id_agree(changes):
    """A1 (plan 18, D18-8): a stability run ID goes with fresh alone, and a replay
    dispatches no judge request and no scorer evaluation."""
    assert_refused(dict(payloads()["SupportRunRecord"], **changes), r.SupportRunRecord)


def test_a_fresh_run_names_its_stability_run():
    payload = dict(
        payloads()["SupportRunRecord"],
        cache_mode="fresh",
        stability_run_id="stability-1",
    )
    record = r.parse_support(payload, r.SupportRunRecord)
    assert (record.cache_mode, record.stability_run_id) == ("fresh", "stability-1")
```

(The payload's `evaluations` is 1, so `{"cache_mode": "replay", "requests": 0}` is still a replay that dispatched.)

Append to `packages/earnings-themes/tests/support/test_cache.py`:

```python
def test_fresh_reads_only_its_own_new_directory(
    tmp_path, one_quote, scorer_identity, policy
):
    """A1 (plan 18): fresh is live over <cache>/fresh/<id>/, which starts empty."""
    request = score_requests(one_quote)[0][1]
    key = scorer_key(one_quote, request, scorer_identity, policy)
    main = reply(request, scorer_identity)
    SupportCache(tmp_path, "live").put(key, main)
    fresh = SupportCache(tmp_path, "fresh", stability_run_id="stability-1")
    assert (fresh.mode, fresh.stability_run_id) == ("fresh", "stability-1")
    assert fresh.lookup(key, "scorer") is None
    again = main.model_copy(update={"latency_ms": main.latency_ms + 1})
    reference = fresh.put(key, again)
    assert fresh.lookup(key, "scorer") == again
    assert (tmp_path / "fresh" / "stability-1" / reference).is_file()
    assert SupportCache(tmp_path, "replay").lookup(key, "scorer") == main


@pytest.mark.parametrize(
    "mode,stability_run_id",
    [
        ("fresh", None),
        ("live", "stability-1"),
        ("replay", "stability-1"),
        ("fresh", ".."),
        ("LIVE", None),
    ],
)
def test_a_stability_run_id_goes_with_fresh_alone(tmp_path, mode, stability_run_id):
    with pytest.raises(SupportError, match="^malformed_record$"):
        SupportCache(tmp_path / "unused", mode, stability_run_id=stability_run_id)
    assert list(tmp_path.iterdir()) == []
```

In `packages/earnings-themes/tests/support/test_run.py`, add `from earnings_themes.support.scorers import ScoreReply, ScriptedScorer` to the imports, then append:

```python
def test_fresh_dispatches_every_request_and_replays_from_its_own_directory(
    case, scorer, panel, policy, allowance, tmp_path
):
    """A1 (plan 18): over a populated cache, fresh dispatches what a live run over an
    empty cache does (here 3 evaluations, 4 judge requests and no hit), and a replay
    over its directory reproduces the assessments."""
    first = run(case, scorer, panel, policy, allowance.ceilings, tmp_path).record
    scored, judged = len(scorer.requests), sum(len(j.requests) for j in panel)
    fresh = run(
        case,
        scorer,
        panel,
        policy,
        allowance.ceilings,
        tmp_path,
        cache=SupportCache(tmp_path, "fresh", stability_run_id="stability-1"),
    )
    record = fresh.record
    assert (record.cache_mode, record.stability_run_id) == ("fresh", "stability-1")
    assert (record.requests, record.evaluations, record.cache_hits) == (
        first.requests,
        first.evaluations,
        first.cache_hits,
    )
    assert record.cache_hits == 0
    assert (record.evaluations, record.requests) == (
        len(scorer.requests) - scored,
        sum(len(j.requests) for j in panel) - judged,
    )
    replay = run(
        case,
        scorer,
        panel,
        policy,
        allowance.ceilings,
        tmp_path,
        cache=SupportCache(tmp_path / "fresh" / "stability-1", "replay"),
    )
    assert (replay.record.evaluations, replay.record.requests) == (0, 0)

    def outcomes(result):
        return [
            (a.outcome.status, a.outcome.flags, a.outcome.missing)
            for a in result.assessments
        ]

    assert outcomes(replay) == outcomes(fresh)


def test_a_second_scorer_reuses_the_judges_replies_in_live_mode(
    case, scorer, scorer_identity, panel, policy, allowance, tmp_path
):
    """A2: SupportPolicy carries no scorer identity, so a second support run with
    another scorer and the same judges hits every judge entry in live mode. This
    pins behaviour that already holds: it passes before this task's code. The
    second scorer gives the first's score, so the judges are asked the same
    questions."""
    first = run(case, scorer, panel, policy, allowance.ceilings, tmp_path)
    runtime = scorer_identity.runtime.model_copy(
        update={"model_id": "invented-scorer-2"}
    )
    other_identity = scorer_identity.model_copy(update={"runtime": runtime})
    other = ScriptedScorer(
        lambda r: ScoreReply(
            score=0.99,
            reason=None,
            input_tokens=5,
            latency_ms=1,
            identity=other_identity,
            input_hash=r.input_hash,
        ),
        lambda r: 5,
        other_identity,
    )
    judged = sum(len(j.requests) for j in panel)
    second = run(case, other, panel, policy, allowance.ceilings, tmp_path)
    assert sum(len(j.requests) for j in panel) == judged
    assert (second.record.requests, second.record.evaluations) == (
        0,
        first.record.evaluations,
    )
    assert len(other.requests) == first.record.evaluations
    assert second.record.cache_hits == first.record.requests + first.record.cache_hits
```

(The planning session ran this second test against `36f12ec` in a throwaway file, and it passed.)

- [ ] **Step 2: Run them, and watch them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/support -q`
Expected: FAIL, except `test_a_second_scorer_reuses_the_judges_replies_in_live_mode`, which passes.
- The `test_cache.py` tests and the fresh `test_run.py` test fail with `TypeError: ... unexpected keyword argument 'stability_run_id'`.
- `test_records.py` fails: `cache_mode` is an unknown field, so `test_records_round_trip_and_print_only_hash[SupportRunRecord]` refuses the payload. The new parametrized cases also refuse the payload for the same reason, so they pass; `test_a_fresh_run_names_its_stability_run` fails.

- [ ] **Step 3: Implement**

In `support/cache.py`, add `from earnings_themes.extraction.cache import cache_directory` after the `earnings_themes.extraction.adapters` import. Replace `SupportCache`'s docstring and `__init__` with:

```python
class SupportCache:
    """Caller-selected raw artifact directory, or under ``fresh`` its stability
    run's own (A1); no dispatch or import-time I/O."""

    def __init__(
        self,
        directory: Path,
        mode: Literal["live", "replay", "fresh"],
        *,
        stability_run_id: str | None = None,
    ) -> None:
        try:
            member, self._directory = cache_directory(
                Path(directory), mode, stability_run_id
            )
        except ValueError:
            raise SupportError("malformed_record") from None
        self.mode = member.value
        self.stability_run_id = stability_run_id
```

In `support/records.py`, replace `from earnings_themes.extraction.records import Parameters` with:

```python
from earnings_themes.extraction.records import (
    Parameters,
    StabilityRunId,
    cache_mode_problem,
)
```

In `SupportRunRecord`, after `configuration_hash: Sha256Hex`, add:

```python
    cache_mode: Literal["live", "replay", "fresh"]
    stability_run_id: StabilityRunId | None = None
```

In `SupportRunRecord._run_bindings`, just before `return self`, add:

```python
        problem = cache_mode_problem(
            self.cache_mode, self.stability_run_id, self.requests + self.evaluations
        )
        if problem is not None:
            raise ValueError(problem)
```

In `support/run.py`, in `SupportRunRecord.model_construct(...)`, after `configuration_hash=digest(configuration),` add:

```python
                cache_mode=cache.mode,
                stability_run_id=cache.stability_run_id,
```

The configuration dictionary already binds `"cache_mode": cache.mode` (`:107`), and is unchanged. So the workflow's replay check at `theme_workflow.py:1020` still holds for a replay run.

- [ ] **Step 4: Run the tests, and watch them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/support packages/earnings-themes/tests/coding packages/earnings-themes/tests/analysis packages/earnings-themes/tests/test_import_boundaries.py -q`
Expected: PASS.

- [ ] **Step 5: Document it**

In `docs/data-dictionary.md`:

1. In `## earnings-themes support records, schema version 1`, after its first paragraph, which ends `JSON-mode parsing revalidates model data instead of trusting prior construction.`, insert:

   ```text
   **Fresh mode (Stage 11, plan 18).** `SupportRunRecord` gained `cache_mode` and
   `stability_run_id` (A1). The schema version stays `1`, so the key function is
   unchanged. A support key binds the extraction run's whole record, which now also
   names its cache mode, so a key's value for a given run differs from before plan 18;
   no support cache predates it. A run record written before plan 18 has no
   `cache_mode`, and is refused as malformed; none was committed (D18-4).
   ```

2. In the `### \`SupportRunRecord\`` table, after the `configuration_hash` row, insert:

   ```text
   | `cache_mode` | live, replay, fresh | Cache operation mode, also bound in the configuration hash; a `replay` run dispatched nothing |
   | `stability_run_id` | safe ID or null | Stability run whose directory `fresh` used; set exactly when `cache_mode` is `fresh` |
   ```

3. In the `SupportCache` paragraph, replace the line:

   ```text
   mode)` supports `live` and `replay`, typed `lookup(key, kind)` returning a raw reply
   ```

   with:

   ```text
   mode, *, stability_run_id=None)` supports `live`, `replay` and `fresh` (`live` over
   `<directory>/fresh/<stability_run_id>/`; A1, plan 18), typed `lookup(key, kind)`
   returning a raw reply
   ```

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py tests/integration/test_coding_frozen_v0.py tests/integration/test_support_fixtures.py tests/integration/test_theme_frozen_v0.py tests/integration/test_theme_vertical_slice.py apps/earnings-pipeline/tests/test_theme_workflow.py apps/earnings-pipeline/tests/test_extract_cli.py -q`
Expected: PASS. The Stage 10 workflow runs every stage in `replay`, and each record now says so.

- [ ] **Step 6: Commit**

```bash
git log -3 --oneline
uv run --locked ruff format packages/earnings-themes
uv run --locked ruff check .
git add packages/earnings-themes docs/data-dictionary.md
git commit -m "feat(themes): fresh cache mode for support; pin the second run's judge reuse (A1, A2)"
```

---

### Task 5: Shared model-file checks and the local chat token counter (A2)

**Files:**
- Create: `packages/earnings-themes/src/earnings_themes/support/model_files.py`
- Create: `packages/earnings-themes/src/earnings_themes/support/chat_tokens.py`
- Modify: `packages/earnings-themes/src/earnings_themes/support/nli.py:3` (imports), `:72-98` (`_verify_files` moves out; `_prepare_config`)
- Modify: `packages/earnings-themes/src/earnings_themes/support/judges.py:7` (imports), `:105-121` (`transport_weights_hash`)
- Create: `packages/earnings-themes/tests/support/test_model_files.py`
- Create: `packages/earnings-themes/tests/support/test_chat_tokens.py`
- Modify: `packages/earnings-themes/pyproject.toml` (the `support-nli` extra), `uv.lock`
- Modify: `docs/data-dictionary.md` (a new `ChatTokenizerConfig` section), `tests/contracts/test_data_dictionary.py` (imports, `MODELS`)

**Interfaces:**
- Consumes: `FileHash`, `SafePart` (`support/records.py`); `_validated` (`support/resolve.py`); `_verify_runtime_versions` (`support/nli.py`, imported inside the constructor only); `ChatRequest` (`extraction/adapters.py`).
- Produces, in `earnings_themes.support.model_files`:
  - `verify_files(directory: str | Path, files: tuple[FileHash, ...]) -> None`. It raises `SupportError("model_mismatch")`, with no file diagnostic, unless the directory holds exactly the listed files, none a symlink or outside it, each matching its SHA-256.
  - `files_hash(files: tuple[FileHash, ...]) -> str`: one file's SHA-256, or the sorted digest of several; no file is `model_mismatch`.
- Produces, in `earnings_themes.support.chat_tokens`:
  - `ChatTokenizerConfig(local_directory: str, files: tuple[FileHash, ...])`;
  - `ChatTokenCounter(config, *, _loader=None)`, callable as `counter(request) -> int`. It can serve as `ClassifierBinding`'s and `JudgeBinding`'s `token_counter`.
- Unchanged in name and behaviour: `nli._prepare_config`, `nli._verify_runtime_versions` (`test_nli.py:443` patches `nli.version` and calls it, so it stays in `nli.py`), and `judges.transport_weights_hash`.

Why a new module: no ordinary themes module may load `support/nli.py` (`test_ordinary_imports_do_not_load_nli_adapter`, `test_import_boundaries.py:401`). So the file check moves out of `nli.py` into a module that `nli.py`, `chat_tokens.py` and the application all import. `files_hash` joins it, so the judge binding and the builder share one weights hash.

- [ ] **Step 1: Write the failing tests**

Create `packages/earnings-themes/tests/support/test_model_files.py`:

```python
"""The model-file checks the scorers, the judges' weights binding, the chat token
counter and the live runtime share (the Stage 11 spec, A2; plan 18)."""

from hashlib import sha256

import pytest
from earnings_core import digest
from earnings_themes.support.model_files import files_hash, verify_files
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import FileHash

FILES = {"model.gguf": b"invented weights", "nested/tokenizer.json": b"{}"}


def written(directory):
    for name, data in FILES.items():
        (directory / name).parent.mkdir(parents=True, exist_ok=True)
        (directory / name).write_bytes(data)
    return tuple(
        FileHash(relative_path=name, sha256=sha256(data).hexdigest())
        for name, data in sorted(FILES.items())
    )


def test_a_directory_that_holds_exactly_its_files_verifies(tmp_path):
    directory = tmp_path / "model"
    verify_files(str(directory), written(directory))
    verify_files(directory, written(directory))


@pytest.mark.parametrize("change", ["edit", "extra", "missing", "symlink", "absent"])
def test_anything_else_is_a_model_mismatch(tmp_path, change):
    directory = tmp_path / "model"
    files = written(directory)
    if change == "edit":
        (directory / "model.gguf").write_bytes(b"changed")
    elif change == "extra":
        (directory / "README.md").write_bytes(b"an unlisted file")
    elif change == "missing":
        (directory / "model.gguf").unlink()
    elif change == "symlink":
        outside = tmp_path / "outside.gguf"
        outside.write_bytes(FILES["model.gguf"])
        (directory / "model.gguf").unlink()
        (directory / "model.gguf").symlink_to(outside)
    else:
        directory = tmp_path / "absent"
    with pytest.raises(SupportError, match="^model_mismatch$") as caught:
        verify_files(str(directory), files)
    assert caught.value.__suppress_context__


def test_files_hash_is_one_file_s_hash_or_the_sorted_digest():
    a = FileHash(relative_path="a.gguf", sha256="a" * 64)
    b = FileHash(relative_path="b.gguf", sha256="b" * 64)
    assert files_hash((a,)) == "a" * 64
    assert files_hash((b, a)) == digest(
        [a.model_dump(mode="json"), b.model_dump(mode="json")]
    )
    with pytest.raises(SupportError, match="^model_mismatch$"):
        files_hash(())
```

Create `packages/earnings-themes/tests/support/test_chat_tokens.py`:

```python
"""A2's local chat token counter, over invented files and an injected tokenizer: no
optional installation, no weights, no server (the Stage 11 spec, A2; plan 18)."""

from hashlib import sha256
from types import SimpleNamespace

import pytest
from earnings_themes.extraction.adapters import Message
from earnings_themes.support.chat_tokens import ChatTokenCounter, ChatTokenizerConfig
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import FileHash
from pydantic import ValidationError

FILES = {"tokenizer.json": b"{}", "tokenizer_config.json": b"{}"}
REQUEST = SimpleNamespace(
    messages=(
        Message(role="system", content="Count these words."),
        Message(role="user", content="One two three."),
    )
)


def config(directory, files=FILES):
    for name, data in files.items():
        (directory / name).write_bytes(data)
    hashes = tuple(
        FileHash(relative_path=name, sha256=sha256(data).hexdigest())
        for name, data in sorted(files.items())
    )
    return ChatTokenizerConfig(local_directory=str(directory), files=hashes)


class Tokenizer:
    """Renders each message as its role and words, and counts words."""

    chat_template = "invented"

    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        self.calls.append((tokenize, add_generation_prompt))
        turns = [f"<{m['role']}> {m['content']}" for m in messages]
        return " ".join([*turns, "<model>"] if add_generation_prompt else turns)

    def __call__(self, text, *, add_special_tokens):
        self.calls.append(add_special_tokens)
        return {"input_ids": text.split()}


def loader(tokenizer, options):
    def load(path, **kwargs):
        options.append((path, kwargs))
        return tokenizer

    return load


def test_counts_the_rendered_template_with_the_generation_prompt(
    tmp_path, no_network
):
    tokenizer, options = Tokenizer(), []
    counter = ChatTokenCounter(config(tmp_path), _loader=loader(tokenizer, options))
    # "<system> Count these words. <user> One two three. <model>": 9 words.
    assert counter(REQUEST) == 9
    assert tokenizer.calls == [(False, True), False]
    assert options == [
        (str(tmp_path), {"local_files_only": True, "trust_remote_code": False})
    ]
    assert no_network == []


@pytest.mark.parametrize("change", ["edit", "extra"])
def test_refuses_files_that_do_not_match_their_hashes(tmp_path, change):
    checked = config(tmp_path)
    if change == "edit":
        (tmp_path / "tokenizer.json").write_bytes(b"changed")
    else:
        (tmp_path / "README.md").write_bytes(b"an unlisted file")
    with pytest.raises(SupportError, match="^model_mismatch$"):
        ChatTokenCounter(checked, _loader=loader(Tokenizer(), []))


def test_refuses_a_tokenizer_without_a_chat_template(tmp_path):
    tokenizer = Tokenizer()
    tokenizer.chat_template = None
    with pytest.raises(SupportError, match="^model_mismatch$"):
        ChatTokenCounter(config(tmp_path), _loader=loader(tokenizer, []))


def test_without_an_injected_loader_the_pinned_runtime_is_checked_first(
    tmp_path, monkeypatch
):
    """The production path checks the pinned runtime versions before it imports
    transformers; an unapproved version is refused with nothing loaded."""
    from earnings_themes.support import nli

    monkeypatch.setattr(nli, "version", lambda name: "unapproved")
    with pytest.raises(SupportError, match="^model_mismatch$"):
        ChatTokenCounter(config(tmp_path))


def test_a_config_names_an_absolute_directory_and_both_tokenizer_files(tmp_path):
    with pytest.raises(ValidationError):
        ChatTokenizerConfig(local_directory="relative", files=config(tmp_path).files)
    one = tmp_path / "one"
    one.mkdir()
    with pytest.raises(ValidationError):
        config(one, files={"tokenizer.json": b"{}"})
```

- [ ] **Step 2: Run them, and watch them fail**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/support/test_model_files.py packages/earnings-themes/tests/support/test_chat_tokens.py -q`
Expected: FAIL at collection, with `No module named 'earnings_themes.support.model_files'` and `No module named 'earnings_themes.support.chat_tokens'`.

- [ ] **Step 3: Move the two shared helpers into `support/model_files.py`**

Create `packages/earnings-themes/src/earnings_themes/support/model_files.py`:

```python
"""Model files on local disk: the check that a directory holds exactly its listed
files, and the one hash that names several (the Stage 11 spec, A2; plan 18).

The NLI scorers, the judges' weights binding, the chat token counter and the live
runtime's builder share them. Importing this module loads no runtime. ``nli.py``
imports it, never the reverse, since no ordinary module may load ``nli.py``.
"""

from hashlib import file_digest
from pathlib import Path

from earnings_core import digest

from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import FileHash


def verify_files(directory: str | Path, files: tuple[FileHash, ...]) -> None:
    """Every file under ``directory`` is listed in ``files``, none is a symlink or
    leaves it, and each matches its SHA-256. Anything else, a missing directory
    included, is ``model_mismatch``, with no file diagnostic."""
    try:
        root = Path(directory).resolve(strict=True)
        expected = {f.relative_path: f.sha256 for f in files}
        actual = {
            p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
        }
        if actual != set(expected):
            raise SupportError("model_mismatch")
        for name, checksum in expected.items():
            path = root / name
            if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):
                raise SupportError("model_mismatch")
            with path.open("rb") as stream:
                if file_digest(stream, "sha256").hexdigest() != checksum:
                    raise SupportError("model_mismatch")
    except Exception:  # noqa: BLE001 - redact arbitrary file diagnostics
        raise SupportError("model_mismatch") from None


def files_hash(files: tuple[FileHash, ...]) -> str:
    """One file's SHA-256, or, for several, the canonical digest of their path/hash
    records sorted by relative path. No file at all is ``model_mismatch``."""
    if not files:
        raise SupportError("model_mismatch")
    if len(files) == 1:
        return files[0].sha256
    return digest(
        [
            f.model_dump(mode="json")
            for f in sorted(files, key=lambda f: f.relative_path)
        ]
    )
```

The body of `verify_files` is `nli._verify_files` moved, not copied: delete it from `nli.py`.

In `support/nli.py`:
- delete `from hashlib import file_digest` (`:3`), which nothing else there uses;
- add `from earnings_themes.support.model_files import verify_files` to the `earnings_themes` imports;
- delete `_verify_files` (`:72-84`);
- in `_prepare_config`, replace `_verify_files(checked)` with `verify_files(checked.local_directory, checked.files)`.

In `support/judges.py`:
- delete `from earnings_core import digest` (`:7`), which only `transport_weights_hash` uses;
- add `from earnings_themes.support.model_files import files_hash` to the `earnings_themes` imports;
- replace `transport_weights_hash` (`:105-121`) with:

```python
def transport_weights_hash(identity: JudgeIdentity) -> str:
    """Bind Stage 7's one weights hash to Stage 8's explicit file manifest: the
    ``files_hash`` of the identity's runtime files."""
    return files_hash(identity.runtime.files)
```

- [ ] **Step 4: Write the counter**

Create `packages/earnings-themes/src/earnings_themes/support/chat_tokens.py`:

```python
"""A chat model's local token counter: its own tokenizer and chat template, from
files the caller hashes (the Stage 11 spec, A2; plan 18). Importing this module
loads no runtime, and counting makes no server call, so a runtime built for replay
needs no model server.

The count is the chat template rendered over the request's messages with the
generation prompt, then encoded without adding special tokens again, since the
template writes them. A structured reply adds nothing to it: llama.cpp constrains a
``response_format`` schema by grammar, not by prompt text. Plan B's smoke compares
the count with the server's reported prompt tokens, since a GGUF's embedded template
can differ from its repository's.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any, Self

from pydantic import Field, model_validator

from earnings_themes.extraction.adapters import ChatRequest
from earnings_themes.support.model_files import verify_files
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import FileHash, SafePart
from earnings_themes.support.resolve import _validated

REQUIRED_FILES = frozenset({"tokenizer.json", "tokenizer_config.json"})


class ChatTokenizerConfig(SafePart):
    """A chat model's tokenizer directory and every file in it, by hash."""

    local_directory: str = Field(repr=False)
    files: tuple[FileHash, ...]

    @model_validator(mode="after")
    def _pinned(self) -> Self:
        names = [f.relative_path for f in self.files]
        if (
            not Path(self.local_directory).is_absolute()
            or len(names) != len(set(names))
            or not REQUIRED_FILES <= set(names)
        ):
            raise ValueError("model_mismatch")
        return self


class ChatTokenCounter:
    """``counter(request) -> int``, a ``token_counter`` for ``ClassifierBinding`` and
    ``JudgeBinding``. Construction checks every file's hash and refuses a tokenizer
    with no chat template (``model_mismatch``). ``_loader`` replaces
    ``AutoTokenizer.from_pretrained``, for tests."""

    def __init__(
        self,
        config: ChatTokenizerConfig,
        *,
        _loader: Callable[..., Any] | None = None,
    ) -> None:
        try:
            checked = _validated(config, ChatTokenizerConfig)
            verify_files(checked.local_directory, checked.files)
            if _loader is None:
                # Imported here, never at module level: no ordinary module may
                # load nli.py (test_import_boundaries.py).
                from earnings_themes.support.nli import _verify_runtime_versions

                _verify_runtime_versions()
                from transformers import AutoTokenizer

                _loader = AutoTokenizer.from_pretrained
            tokenizer = _loader(
                checked.local_directory, local_files_only=True, trust_remote_code=False
            )
            if not getattr(tokenizer, "chat_template", None):
                raise SupportError("model_mismatch")
        except Exception:  # noqa: BLE001 - redact arbitrary runtime/file diagnostics
            raise SupportError("model_mismatch") from None
        self._tokenizer = tokenizer

    def __call__(self, request: ChatRequest) -> int:
        text = self._tokenizer.apply_chat_template(
            [message.model_dump() for message in request.messages],
            tokenize=False,
            add_generation_prompt=True,
        )
        return len(self._tokenizer(text, add_special_tokens=False)["input_ids"])

    def __repr__(self) -> str:
        return "ChatTokenCounter()"

    __str__ = __repr__
```

- [ ] **Step 5: Declare jinja2, which `apply_chat_template` needs**

In `packages/earnings-themes/pyproject.toml`, replace the `support-nli` extra with:

```toml
support-nli = [
    "jinja2==3.1.6",                 # transformers' apply_chat_template (A2)
    "sentencepiece==0.2.2",
    "torch==2.14.1",
    "transformers==5.18.0",
]
```

Run: `uv lock`, then `uv lock --check`
Expected: `Resolved 153 packages`. `git diff --stat uv.lock` shows one file, and `git diff uv.lock` changes only `earnings-themes`'s entry: one `jinja2` line under its `support-nli` extra, and one in its `requires-dist`.

- [ ] **Step 6: Run the tests, and watch them pass**

Run: `uv run --locked --all-packages pytest packages/earnings-themes/tests/support packages/earnings-themes/tests/coding packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py -q`
Expected: PASS. That includes:
- `test_importing_earnings_themes_loads_nothing_forbidden` and `test_ordinary_imports_do_not_load_nli_adapter`: `chat_tokens.py` and `model_files.py` load neither transformers nor `nli.py`;
- `test_nli.py`, unchanged, over the moved file check.

- [ ] **Step 7: Document it**

In `docs/data-dictionary.md`, immediately before `## earnings-themes coding records, schema version 1`, which follows `LocalScorerConfig`'s closing paragraph (ending `inference errors return fixed \`scorer_failed\`.`), insert:

```text
### `ChatTokenizerConfig`

A chat model's local tokenizer (`earnings_themes.support.chat_tokens`; A2, plan 18).
`ChatTokenCounter(config)` checks every file's hash, loads the tokenizer with
`local_files_only=True` and `trust_remote_code=False`, and refuses one with no chat
template (`model_mismatch`). It counts a request as the chat template rendered over
its messages with the generation prompt, encoded without adding special tokens again.
It makes no server call; plan B's smoke compares its count with the server's reported
prompt tokens. `earnings_themes.support.model_files` holds the checks it shares with
the scorers and the live runtime: `verify_files(directory, files)`, which requires the
directory to hold exactly the listed files, none a symlink, each matching its hash;
and `files_hash(files)`, one file's SHA-256 or the sorted digest of several, which is
also a judge's `transport_weights_hash`.

| Field | Type | Meaning |
| --- | --- | --- |
| `local_directory` | string | Absolute tokenizer directory, excluded from repr |
| `files` | tuple[FileHash, …] | Every file in it; `tokenizer.json` and `tokenizer_config.json` required |

```

In `tests/contracts/test_data_dictionary.py`, add `from earnings_themes.support.chat_tokens import ChatTokenizerConfig` to the imports, and `ChatTokenizerConfig,` to `MODELS` after `LocalScorerConfig,`.

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git log -3 --oneline
uv run --locked ruff format packages/earnings-themes tests/contracts
uv run --locked ruff check .
git add packages/earnings-themes uv.lock docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(themes): local chat token counter and shared model-file checks (A2)"
```

---

### Task 6: Model files and the live runtime builder (A2)

**Files:**
- Create: `apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py`
- Create: `apps/earnings-pipeline/tests/test_model_runtime.py`
- Modify: `apps/earnings-pipeline/pyproject.toml` (the `live-models` extra), `uv.lock`
- Modify: `docs/data-dictionary.md` (a new section at the end), `tests/contracts/test_data_dictionary.py` (`WORKFLOW_MODELS`, `WORKFLOW_DATACLASSES`)

**Interfaces:**
- Consumes:
  - Task 5: `verify_files`, `files_hash` (`support/model_files.py`); `ChatTokenizerConfig`, `ChatTokenCounter` (`support/chat_tokens.py`).
  - Existing: `validate_panel`, `JudgeBinding` (`support/judges.py`); `ClassifierBinding` (`coding/local.py`); `CodingError` (`coding/records.py`); `parse_support`, `JudgeIdentity`, `RuntimeIdentity`, `FileHash`, `WeightLicense` (`support/records.py`); `SupportError` (`support/problems.py`); `EntailmentScorer` (`support/scorers.py`); `parse`, `RecordError`, `NonBlank` (`earnings_themes.records`); `tomlfile.read`; `AnalysisPart` (`analysis/records.py`); `WorkflowError`, `confined_path` (`theme_config.py`); `WorkflowRuntime` (`theme_workflow.py`).
  - Imported inside the builder only, so importing `model_runtime` loads neither (Global Constraints): `LocalAdapter`, `LocalModelConfig` (`extraction/local.py`); `MiniCheckScorer`, `DebertaScorer`, `LocalScorerConfig` (`support/nli.py`).
- Produces, in `earnings_pipeline.model_runtime`:
  - `CHAT_ENCODING = "chat-tokens/1:"`;
  - `class RuntimeManifest(AnalysisPart)`: `extractor`, `classifier`, `judges: tuple[str, str]`, `scorer`, `alternative_scorer`;
  - `class ChatModelFile(AnalysisPart)`;
  - `@dataclass(frozen=True) class LiveRuntime`: `workflow: WorkflowRuntime`, `alternative_scorer: EntailmentScorer`, `extractor_family: str`;
  - `build_runtime(manifest: Path, models_root: Path, *, transport=None, _tokenizer_loader=None, _scorer_runtime=None) -> LiveRuntime`. It raises `WorkflowError` with reason `invalid_panel`, `model_mismatch` or `malformed_record`.

- [ ] **Step 1: Write the failing tests**

Create `apps/earnings-pipeline/tests/test_model_runtime.py`:

```python
"""A2's live runtime, built from invented model files under a temporary models root,
with injected tokenizers, scorer runtimes and an httpx mock transport: no weights,
no optional runtime, and no model server (the Stage 11 spec, A2; plan 18)."""

import json
import subprocess
import sys
import tomllib
from datetime import date
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from earnings_pipeline.model_runtime import CHAT_ENCODING, build_runtime
from earnings_pipeline.theme_config import WorkflowError
from earnings_themes.extraction.adapters import (
    Message,
    ModelReply,
    ModelRequest,
    RequestSubject,
    ScriptedAdapter,
)
from earnings_themes.extraction.cache import CachedAdapter
from earnings_themes.extraction.records import Parameters
from earnings_themes.support.model_files import files_hash
from earnings_themes.support.nli import (
    ALTERNATIVE_REVISION,
    PRIMARY_REVISION,
    RUNTIME_VERSIONS,
)
from earnings_themes.support.records import FileHash
from earnings_themes.tomlfile import dumps

LICENSE = {
    "source_url": "https://example.test/license",
    "terms_reference": "invented fixture only",
    "intended_use": "offline test",
    "verified_on": date(2026, 10, 12),
    "permits_use": True,
}
WEIGHTS = {"model.gguf": b"invented weights"}
TOKENIZER = {"tokenizer.json": b"{}", "tokenizer_config.json": b"{}"}
SCORER_FILES = {
    "minicheck": (
        "config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "pytorch_model.bin",
    ),
    "deberta": (
        "config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "model.safetensors",
    ),
}
CHAT = ("gemma", "judge-a", "judge-b")


def hashes(directory: Path, files: dict[str, bytes]) -> list[dict]:
    directory.mkdir(parents=True)
    for name, data in files.items():
        (directory / name).write_bytes(data)
    return [
        {"relative_path": name, "sha256": sha256(data).hexdigest()}
        for name, data in sorted(files.items())
    ]


def chat_file(models: Path, name: str, family: str, port: int) -> dict:
    return {
        "family": family,
        "base_url": f"http://127.0.0.1:{port}/v1",
        "model_id": f"{name}-model",
        "runtime": "llama.cpp",
        "runtime_version": "invented-1",
        "revision": "invented-revision",
        "device": "metal",
        "precision": "q4_0",
        "input_limit": 8192,
        "output_limit": 1024,
        "weights_directory": f"{name}/weights",
        "weights": hashes(models / name / "weights", WEIGHTS),
        "tokenizer_directory": f"{name}/tokenizer",
        "tokenizer_files": hashes(models / name / "tokenizer", TOKENIZER),
        "weight_license": LICENSE,
    }


def scorer_file(models: Path, kind: str) -> dict:
    primary = kind == "minicheck"
    return {
        "kind": kind,
        "directory": kind,
        "revision": PRIMARY_REVISION if primary else ALTERNATIVE_REVISION,
        "files": hashes(models / kind, dict.fromkeys(SCORER_FILES[kind], b"{}")),
        "runtime_versions": [list(pair) for pair in RUNTIME_VERSIONS],
        "device": "cpu",
        "precision": "float32",
        "input_limit": 512,
        "encoding_version": "minicheck-first-step/1" if primary else "deberta-pair/1",
        "label_mapping": [3, 209] if primary else [0, 1, 2],
        "weight_license": LICENSE,
    }


def write(path: Path, data: dict) -> None:
    path.write_text(dumps(data), encoding="utf-8")


def layout(tmp_path: Path, families=CHAT) -> tuple[Path, Path]:
    """A manifest and a models root; the extractor and classifier share one file."""
    models, config = tmp_path / "models", tmp_path / "config"
    config.mkdir()
    for port, (name, family) in enumerate(zip(CHAT, families, strict=True), 8080):
        write(config / f"{name}.toml", chat_file(models, name, family, port))
    for kind in SCORER_FILES:
        write(config / f"{kind}.toml", scorer_file(models, kind))
    write(
        config / "runtime.toml",
        {
            "extractor": "gemma.toml",
            "classifier": "gemma.toml",
            "judges": ["judge-a.toml", "judge-b.toml"],
            "scorer": "minicheck.toml",
            "alternative_scorer": "deberta.toml",
        },
    )
    return config / "runtime.toml", models


class ChatTokenizer:
    chat_template = "invented"

    def __init__(self, calls: list) -> None:
        self.calls = calls

    def apply_chat_template(self, messages, **options):
        self.calls.append("render")
        return " ".join(m["content"] for m in messages)

    def __call__(self, text, **options):
        self.calls.append("encode")
        return {"input_ids": text.split()}


def scorer_runtime(loaded: list):
    """MiniCheck's and DeBERTa's checked metadata, by directory name."""

    def tokenizer(path, **options):
        loaded.append(Path(path).name)
        return SimpleNamespace(
            eos_token="</s>",
            pad_token_id=0,
            eos_token_id=1,
            model_max_length=512,
            convert_ids_to_tokens=lambda ids: ["▁", "▁1"],
        )

    def model(path, **options):
        primary = Path(path).name == "minicheck"
        loaded_model = SimpleNamespace(
            config=SimpleNamespace(
                model_type="t5" if primary else "deberta-v2",
                architectures=[
                    "T5ForConditionalGeneration"
                    if primary
                    else "DebertaV2ForSequenceClassification"
                ],
                decoder_start_token_id=0,
                pad_token_id=0,
                eos_token_id=1,
                id2label={0: "entailment", 1: "neutral", 2: "contradiction"},
                max_position_embeddings=512,
            )
        )
        loaded_model.to = lambda **kwargs: loaded_model
        loaded_model.eval = lambda: loaded_model
        return loaded_model

    return (SimpleNamespace(float32="float32"), tokenizer, model)


def failing(calls: list) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        raise AssertionError("no request may be sent")

    return httpx.MockTransport(handle)


def build(manifest, models, *, transport=None, calls=None, loaded=None):
    calls = [] if calls is None else calls
    return build_runtime(
        manifest,
        models,
        transport=transport or failing(calls),
        _tokenizer_loader=lambda path, **options: ChatTokenizer(calls),
        _scorer_runtime=scorer_runtime([] if loaded is None else loaded),
    )


def request() -> ModelRequest:
    return ModelRequest(
        messages=(
            Message(role="system", content="Invented system text."),
            Message(role="user", content="[U1] Invented unit."),
        ),
        reply_schema={"type": "object"},
        parameters=Parameters(),
        subject=RequestSubject(
            doc_id="doc@walker-1#0123456789abcdef",
            canonical_hash="a" * 64,
            window_id="w-0-10",
            unit_ids=("sentence-0-10",),
            window_budget=4000,
            claim_limit=500,
            prompt_sha256="b" * 64,
            extractor_version="pointer-traversal/1",
            validator_version="3",
        ),
    )


def test_builds_every_role_from_its_file_and_calls_nothing(tmp_path: Path) -> None:
    manifest, models = layout(tmp_path)
    calls: list = []
    loaded: list = []
    live = build(manifest, models, calls=calls, loaded=loaded)
    runtime = live.workflow
    extractor = runtime.extractor.identity
    assert (extractor.adapter_kind, extractor.model_id, extractor.weights_sha256) == (
        "local",
        "gemma-model",
        sha256(WEIGHTS["model.gguf"]).hexdigest(),
    )
    classifier = runtime.classifier.identity
    tokenizer = tuple(
        FileHash(relative_path=name, sha256=sha256(data).hexdigest())
        for name, data in sorted(TOKENIZER.items())
    )
    assert (classifier.family, classifier.hosting, classifier.runtime.model_id) == (
        "gemma",
        "local",
        "gemma-model",
    )
    assert classifier.runtime.encoding_version == CHAT_ENCODING + files_hash(tokenizer)
    assert [j.identity.family for j in runtime.judges] == ["judge-a", "judge-b"]
    assert (runtime.scorer.identity.kind, live.alternative_scorer.identity.kind) == (
        "minicheck",
        "deberta",
    )
    assert (live.extractor_family, runtime.assignment_policy, runtime.renderer) == (
        "gemma",
        None,
        None,
    )
    assert sorted(loaded) == ["deberta", "minicheck"]
    assert calls == []


def test_the_extractor_dispatches_through_the_given_transport(tmp_path: Path) -> None:
    manifest, models = layout(tmp_path)
    sent: list = []

    def serve(request: httpx.Request) -> httpx.Response:
        sent.append((str(request.url), json.loads(request.content)["model"]))
        return httpx.Response(
            200,
            json={"model": "gemma-model", "choices": [{"message": {"content": "{}"}}]},
        )

    live = build(manifest, models, transport=httpx.MockTransport(serve))
    reply = live.workflow.extractor.complete(request())
    assert (reply.text, reply.model) == ("{}", "gemma-model")
    assert sent == [("http://127.0.0.1:8080/v1/chat/completions", "gemma-model")]


@pytest.mark.parametrize(
    "families", [("gemma", "judge-a", "judge-a"), ("gemma", "gemma", "gemma")]
)
def test_a_panel_that_breaks_stage_8_s_family_rules_is_refused_first(
    tmp_path: Path, families
) -> None:
    """D18-11: the panel is checked before any model file is hashed or loaded, so
    with every model file gone the refusal is still invalid_panel."""
    manifest, models = layout(tmp_path, families)
    for path in models.rglob("*"):
        if path.is_file():
            path.unlink()
    calls: list = []
    loaded: list = []
    with pytest.raises(WorkflowError, match="^invalid_panel$"):
        build(manifest, models, calls=calls, loaded=loaded)
    assert (calls, loaded) == ([], [])


@pytest.mark.parametrize("directory", ["judge-b/weights", "judge-b/tokenizer"])
@pytest.mark.parametrize("change", ["edit", "extra"])
def test_a_model_directory_that_does_not_match_its_file_is_refused(
    tmp_path: Path, directory, change
) -> None:
    manifest, models = layout(tmp_path)
    target = models / directory
    if change == "edit":
        first = sorted(p for p in target.iterdir() if p.is_file())[0]
        first.write_bytes(b"changed bytes")
    else:
        (target / "README.md").write_bytes(b"an unlisted file")
    with pytest.raises(WorkflowError, match="^model_mismatch$"):
        build(manifest, models)


@pytest.mark.parametrize(
    "name,field,value",
    [
        ("judge-a.toml", "weights_directory", "../elsewhere"),
        ("judge-a.toml", "tokenizer_directory", "/absolute"),
        ("minicheck.toml", "directory", "../elsewhere"),
    ],
)
def test_a_directory_outside_the_models_root_is_refused(
    tmp_path: Path, name, field, value
) -> None:
    manifest, models = layout(tmp_path)
    path = manifest.parent / name
    write(path, {**tomllib.loads(path.read_text(encoding="utf-8")), field: value})
    with pytest.raises(WorkflowError, match="^malformed_record$"):
        build(manifest, models)


def test_a_scorer_file_never_names_an_absolute_local_directory(tmp_path: Path) -> None:
    """D18-9: no committed file holds a path on this machine."""
    manifest, models = layout(tmp_path)
    path = manifest.parent / "minicheck.toml"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    write(path, {**data, "local_directory": str(models / "minicheck")})
    with pytest.raises(WorkflowError, match="^malformed_record$"):
        build(manifest, models)


@pytest.mark.parametrize(
    "changes",
    [
        {"judges": ["judge-a.toml", "judge-b.toml", "gemma.toml"]},
        {"scorer": "absent.toml"},
        {"extractor": "../gemma.toml"},
    ],
)
def test_a_manifest_that_does_not_read_is_refused(tmp_path: Path, changes) -> None:
    manifest, models = layout(tmp_path)
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    write(manifest, {**data, **changes})
    with pytest.raises(WorkflowError, match="^malformed_record$"):
        build(manifest, models)


def test_a_runtime_built_for_replay_needs_no_server(tmp_path: Path) -> None:
    """A2: building sends nothing and counts nothing, and a replay through the built
    extractor dispatches nothing, over transports that fail on any call."""
    manifest, models = layout(tmp_path)
    calls: list = []
    extractor = build(manifest, models, calls=calls).workflow.extractor
    stored = ModelReply(text="{}", model="gemma-model")
    CachedAdapter(
        ScriptedAdapter(lambda _: stored, extractor.identity), tmp_path / "cache", "live"
    ).complete(request())
    replayed = CachedAdapter(extractor, tmp_path / "cache", "replay").complete(
        request()
    )
    assert replayed == stored.model_copy(update={"cached": True})
    assert calls == []


def test_importing_the_builder_loads_no_adapter_or_runtime() -> None:
    """When A8 wires the builder into the CLI, ``--help`` must still load neither
    the local adapter nor the NLI module (test_import_boundaries.py's
    test_ordinary_cli_help_loads_no_concrete_runtime): both load inside the builder."""
    code = (
        "import json, sys; import earnings_pipeline.model_runtime; "
        "print(json.dumps(sorted(sys.modules)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    loaded = set(json.loads(result.stdout))
    assert {
        "earnings_themes.extraction.local",
        "earnings_themes.support.nli",
        "transformers",
        "torch",
    }.isdisjoint(loaded)
```

- [ ] **Step 2: Run them, and watch them fail**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_model_runtime.py -q`
Expected: FAIL at collection with `No module named 'earnings_pipeline.model_runtime'`.

- [ ] **Step 3: Write the builder**

Create `apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py`:

```python
"""The live runtime for scope ``research``, assembled from committed model files (the
Stage 11 spec, A2; plan 18).

- **Files.** A manifest names one model file for each role: the extractor, the
  classifier, two judges, the scorer and the alternative scorer. A chat model's file
  is a ``ChatModelFile``. A scorer's file is a ``LocalScorerConfig`` with a
  ``directory`` relative to the models root in place of its absolute
  ``local_directory``, so no committed file holds a path on this machine (D18-9).
- **Order.** The panel is checked against Stage 8's family rules first, before any
  model file is hashed or loaded (``invalid_panel``; D18-11). Then every chat model's
  weights and tokenizer files are hashed against its file, and each scorer checks its
  own files and installed runtime (``model_mismatch``). A file that does not read, or
  a directory outside the models root, is ``malformed_record``.
- **No server call.** Building sends no request and counts no token: the token
  counters are local tokenizers, and each binding checks its transport's configured
  identity. So a runtime built for replay needs no model server. Every reply still
  names its model (``model_mismatch``), and plan B's smoke records the server's own
  build (D18-12).
- **Choice.** Nothing here chooses a model: ADR 0006 writes the files (B1).
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from earnings_themes.analysis.records import AnalysisPart
from earnings_themes.coding.local import ClassifierBinding
from earnings_themes.coding.records import CodingError
from earnings_themes.records import NonBlank, RecordError, parse
from earnings_themes.support.chat_tokens import ChatTokenCounter, ChatTokenizerConfig
from earnings_themes.support.judges import JudgeBinding, validate_panel
from earnings_themes.support.model_files import files_hash, verify_files
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    FileHash,
    JudgeIdentity,
    RuntimeIdentity,
    WeightLicense,
    parse_support,
)
from earnings_themes.support.scorers import EntailmentScorer
from earnings_themes.tomlfile import read
from pydantic import Field, PositiveFloat, PositiveInt

from earnings_pipeline.theme_config import WorkflowError, confined_path
from earnings_pipeline.theme_workflow import WorkflowRuntime

if TYPE_CHECKING:
    import httpx
    from earnings_themes.extraction.local import LocalAdapter
    from earnings_themes.support.nli import LocalScorerConfig

CHAT_ENCODING = "chat-tokens/1:"
"""A chat model's ``encoding_version`` prefix. The rest is its tokenizer files'
``files_hash``, so its identity names the tokenizer that counts its requests
(D18-10)."""


class RuntimeManifest(AnalysisPart):
    """Which model file fills each role. Names are relative to the manifest's own
    directory."""

    extractor: NonBlank
    classifier: NonBlank
    judges: tuple[NonBlank, NonBlank]
    scorer: NonBlank
    alternative_scorer: NonBlank


class ChatModelFile(AnalysisPart):
    """One local chat model behind an OpenAI-compatible server: its endpoint, its
    identity, and its weights' and tokenizer's files, under directories relative to
    the models root."""

    family: NonBlank
    base_url: NonBlank
    model_id: NonBlank
    runtime: NonBlank
    runtime_version: NonBlank
    structured: bool = True
    timeout_s: PositiveFloat = 300.0
    revision: NonBlank
    device: NonBlank
    precision: NonBlank
    input_limit: PositiveInt
    output_limit: PositiveInt
    weights_directory: NonBlank
    weights: tuple[FileHash, ...] = Field(min_length=1)
    tokenizer_directory: NonBlank
    tokenizer_files: tuple[FileHash, ...] = Field(min_length=1)
    weight_license: WeightLicense


@dataclass(frozen=True, repr=False)
class LiveRuntime:
    """The models ``pilot pass`` and a stability run dispatch to (A2): the workflow's
    runtime, with no assignment policy and no renderer, and the alternative scorer
    for the second support run."""

    workflow: WorkflowRuntime
    alternative_scorer: EntailmentScorer
    extractor_family: str


def build_runtime(
    manifest: Path,
    models_root: Path,
    *,
    transport: httpx.BaseTransport | None = None,
    _tokenizer_loader: Callable[..., Any] | None = None,
    _scorer_runtime: tuple[Any, Any, Any] | None = None,
) -> LiveRuntime:
    """The live runtime ``manifest`` names, with every model directory under
    ``models_root``. ``transport`` replaces httpx's own, for tests, and the two
    private arguments replace the tokenizer loader and the scorers' runtime. A
    refusal is a ``WorkflowError``: ``invalid_panel``, ``model_mismatch`` or
    ``malformed_record``."""
    try:
        return _build(
            manifest, models_root, transport, _tokenizer_loader, _scorer_runtime
        )
    except WorkflowError:
        raise
    except (SupportError, CodingError) as error:
        raise WorkflowError(str(error)) from None
    except (RecordError, ValueError):
        raise WorkflowError("malformed_record") from None


def _build(manifest_path, models_root, transport, tokenizer_loader, scorer_runtime):
    # Imported here, never at module level: the CLI's --help loads neither
    # (test_import_boundaries.py, test_ordinary_cli_help_loads_no_concrete_runtime).
    from earnings_themes.extraction import local
    from earnings_themes.support import nli

    root = manifest_path.parent
    manifest = _read(root, manifest_path.name, RuntimeManifest)
    names = dict.fromkeys((manifest.extractor, manifest.classifier, *manifest.judges))
    chat = {name: _read(root, name, ChatModelFile) for name in names}
    identities = {name: _identity(model) for name, model in chat.items()}
    family = chat[manifest.extractor].family
    panel = validate_panel(family, tuple(identities[n] for n in manifest.judges))
    counters = {}
    for name, model in chat.items():
        verify_files(confined_path(models_root, model.weights_directory), model.weights)
        tokenizer = confined_path(models_root, model.tokenizer_directory)
        counters[name] = ChatTokenCounter(
            ChatTokenizerConfig(
                local_directory=str(tokenizer), files=model.tokenizer_files
            ),
            _loader=tokenizer_loader,
        )

    def adapter(name: str) -> LocalAdapter:
        model = chat[name]
        endpoint = local.LocalModelConfig(
            base_url=model.base_url,
            model_id=model.model_id,
            weights_sha256=files_hash(model.weights),
            runtime=model.runtime,
            runtime_version=model.runtime_version,
            structured=model.structured,
            timeout_s=model.timeout_s,
        )
        return local.LocalAdapter(endpoint, transport=transport)

    def scorer(name: str) -> LocalScorerConfig:
        return _scorer(root, name, models_root, nli.LocalScorerConfig)

    workflow = WorkflowRuntime(
        extractor=adapter(manifest.extractor),
        classifier=ClassifierBinding(
            identities[manifest.classifier],
            adapter(manifest.classifier),
            counters[manifest.classifier],
        ),
        scorer=nli.MiniCheckScorer(scorer(manifest.scorer), _runtime=scorer_runtime),
        judges=tuple(
            JudgeBinding(identity, adapter(name), counters[name])
            for name, identity in zip(manifest.judges, panel, strict=True)
        ),
        assignment_policy=None,
        renderer=None,
    )
    alternative = nli.DebertaScorer(
        scorer(manifest.alternative_scorer), _runtime=scorer_runtime
    )
    return LiveRuntime(workflow, alternative, family)


def _read(directory: Path, name: str, model):
    path = confined_path(directory, name)
    return parse(read(path), model, path.name)


def _identity(model: ChatModelFile) -> JudgeIdentity:
    """The identity a classifier or judge binding checks its transport against."""
    return JudgeIdentity(
        family=model.family,
        runtime=RuntimeIdentity(
            model_id=model.model_id,
            revision=model.revision,
            files=model.weights,
            runtime=model.runtime,
            runtime_version=model.runtime_version,
            device=model.device,
            precision=model.precision,
            encoding_version=CHAT_ENCODING + files_hash(model.tokenizer_files),
        ),
        input_limit=model.input_limit,
        output_limit=model.output_limit,
        hosting="local",
        weight_license=model.weight_license,
    )


def _scorer(
    directory: Path, name: str, models_root: Path, config: type[LocalScorerConfig]
) -> LocalScorerConfig:
    """A scorer's file: a ``LocalScorerConfig`` whose ``directory``, relative to the
    models root, stands in for its absolute ``local_directory`` (D18-9). ``config``
    is the class, which the builder passes in so that this module never imports
    ``nli.py`` at import time."""
    path = confined_path(directory, name)
    data = read(path)
    reference = data.pop("directory", None)
    if "local_directory" in data or type(reference) is not str:
        raise WorkflowError("malformed_record")
    resolved = confined_path(models_root, reference)
    return parse_support({**data, "local_directory": str(resolved)}, config)
```

Python 3.14 evaluates annotations lazily, so the names imported under `TYPE_CHECKING` (`httpx`, `LocalAdapter`, `LocalScorerConfig`) are never looked up at run time. Importing this module loads neither the local adapter nor `nli.py`, nor any model runtime; `test_importing_the_builder_loads_no_adapter_or_runtime` holds it to that.

- [ ] **Step 4: Declare the application's live extra**

In `apps/earnings-pipeline/pyproject.toml`, after the `orchestration` extra, add:

```toml
# Stage 11's live runtime (A2): the local chat adapter and the local NLI and
# tokenizer runtimes, imported only inside model_runtime's builder.
live-models = [
    "earnings-themes[local-model,support-nli]",
]
```

Run: `uv lock`, then `uv lock --check`
Expected: `Resolved 153 packages`. `git diff uv.lock` changes only `earnings-pipeline`'s entry: its optional `live-models` dependency, and its `requires-dist`.

- [ ] **Step 5: Run the tests, and watch them pass**

Run: `uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_model_runtime.py apps/earnings-pipeline/tests/test_theme_workflow.py apps/earnings-pipeline/tests/test_theme_config.py packages/earnings-themes/tests/test_import_boundaries.py tests/contracts/test_import_scan.py -q`
Expected: PASS.

- [ ] **Step 6: Document it**

Append to the end of `docs/data-dictionary.md`:

```text

## Stage 11 live runtime (plan 18)

`earnings_pipeline.model_runtime.build_runtime(manifest, models_root, *, transport=None)`
assembles the live runtime for scope `research` from committed model files (the Stage
11 spec, A2). It chooses no model: ADR 0006 writes the files (B1). It checks the panel
against Stage 8's family rules before any model file is hashed or loaded
(`invalid_panel`). It then hashes every chat model's weights and tokenizer files, and
each scorer checks its own files and installed runtime (`model_mismatch`). A file that
does not read, or a directory outside the models root, is `malformed_record`. Building
sends no request and counts no token, so a runtime built for replay needs no model
server. A scorer's file is a `LocalScorerConfig` whose `directory`, relative to the
models root, stands in for its absolute `local_directory`, so no committed file holds a
path on this machine. A chat model's `encoding_version` is `chat-tokens/1:` and its
tokenizer files' `files_hash`, so its identity names the tokenizer that counts its
requests. The application's `live-models` extra installs the runtimes it needs.

### `RuntimeManifest`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Application record schema version |
| `extractor` | file name | The extractor's `ChatModelFile`, beside the manifest |
| `classifier` | file name | The classifier's `ChatModelFile`; may be the extractor's |
| `judges` | two file names | The two judges' `ChatModelFile`s, in panel order |
| `scorer` | file name | The primary scorer's file, a `minicheck` `LocalScorerConfig` |
| `alternative_scorer` | file name | The alternative scorer's file, a `deberta` `LocalScorerConfig`, for the second support run |

### `ChatModelFile`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | `1` | Application record schema version |
| `family` | string | Model family, for Stage 8's panel rule |
| `base_url` | string | The server's OpenAI-compatible root; loopback only (`LocalModelConfig`) |
| `model_id` | string | The model the server names in each reply |
| `runtime` | string | The serving runtime's name |
| `runtime_version` | string | Its version |
| `structured` | bool | Whether the runtime honors a strict JSON-schema `response_format`; default true |
| `timeout_s` | float > 0 | Seconds per request; default 300 |
| `revision` | string | The weights' repository revision |
| `device` | string | The device the server runs on |
| `precision` | string | The weights' quantization or precision |
| `input_limit` | int > 0 | Total context: full prompt plus reserved output |
| `output_limit` | int > 0 | Bound on `max_tokens` |
| `weights_directory` | relative path | Under the models root; holds exactly `weights` |
| `weights` | tuple[FileHash, …] | Every weights file; their `files_hash` is the adapter's `weights_sha256` |
| `tokenizer_directory` | relative path | Under the models root; holds exactly `tokenizer_files` |
| `tokenizer_files` | tuple[FileHash, …] | Every tokenizer file (`ChatTokenizerConfig`) |
| `weight_license` | WeightLicense | Verified weight terms |

### `LiveRuntime`

| Field | Type | Meaning |
| --- | --- | --- |
| `workflow` | `WorkflowRuntime` | Extractor, classifier, scorer and judges; no assignment policy and no renderer |
| `alternative_scorer` | `EntailmentScorer` | DeBERTa, for the second support run over the same judges |
| `extractor_family` | string | The extractor's family, for Stage 8's panel rule |
```

In `tests/contracts/test_data_dictionary.py`, change `from earnings_pipeline import theme_config, theme_workflow` to `from earnings_pipeline import model_runtime, theme_config, theme_workflow`. Add `model_runtime.RuntimeManifest,` and `model_runtime.ChatModelFile,` to the end of `WORKFLOW_MODELS`. Change `WORKFLOW_DATACLASSES` to:

```python
WORKFLOW_DATACLASSES = [
    theme_workflow.WorkflowRuntime,
    theme_workflow.WorkflowResult,
    model_runtime.LiveRuntime,
]
```

Run: `uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git log -3 --oneline
uv run --locked ruff format apps/earnings-pipeline tests/contracts
uv run --locked ruff check .
git add apps/earnings-pipeline uv.lock docs/data-dictionary.md tests/contracts/test_data_dictionary.py
git commit -m "feat(pipeline): build the live research runtime from model files (A2)"
```

---

### Task 7: Scoped checks, the user's gates, and completion (gate)

**Files:**
- Modify: `specs/feasibility-pilot-and-threshold-calibration.md` (the slice stamp, at the end of §Rollout)
- Modify: `specs/deferred_items.md` (only if execution defers anything)
- Modify: this plan (completion markup), then `git mv` it to `specs/plans/completed/`

- [ ] **Step 1: Run every scoped check in the worktree**

```bash
uv run --locked --all-packages pytest packages/earnings-themes/tests/test_extraction_cache.py packages/earnings-themes/tests/test_extraction_run.py packages/earnings-themes/tests/test_extraction_records.py packages/earnings-themes/tests/test_extraction_store.py packages/earnings-themes/tests/test_import_boundaries.py -q
uv run --locked --all-packages pytest packages/earnings-themes/tests/coding packages/earnings-themes/tests/support packages/earnings-themes/tests/analysis -q
uv run --locked --all-packages pytest apps/earnings-pipeline/tests/test_model_runtime.py apps/earnings-pipeline/tests/test_theme_workflow.py apps/earnings-pipeline/tests/test_theme_config.py apps/earnings-pipeline/tests/test_extract_cli.py -q
uv run --locked --all-packages pytest tests/contracts/test_data_dictionary.py tests/contracts/test_coding_contracts.py tests/contracts/test_import_scan.py tests/integration/test_coding_frozen_v0.py tests/integration/test_support_fixtures.py tests/integration/test_theme_frozen_v0.py tests/integration/test_theme_vertical_slice.py -q
uv run --locked ruff check .
uv run --locked ruff format --check .
uv lock --check
git diff --stat main...HEAD -- evaluation config data CLAUDE.md tests/integration/test_stage6_wording.py
```

Expected:
- every test passes, and Ruff prints no finding;
- `uv lock --check` prints `Resolved 153 packages`;
- the last command prints nothing: no evaluation record, no model config, no `CLAUDE.md` line and no gate file changed.

Record the exact pass counts for the handoff.

- [ ] **Step 2 (gate): Hand the user the checks only they run**

Put this to the user in chat, with `<sha>` set to `git rev-parse HEAD`, and wait for the results:

> Plan 18 (Stage 11 plan A, slice 2) is implemented on `stage-11-plan-a-runtime` at `<sha>`. Two checks are yours, because they run the full suite and the wording gate.
>
> Run them in the main checkout, `/Users/lowell/Projects/earnings-themes`, after `git switch --detach <sha>`, and finish with `git switch main`:
>
> 1. **The root suite:** `uv run --locked --all-packages pytest packages apps tests -m "not live and not browser"`.
>    - The baseline at `3406ba4` was 4336 passed, 2 skipped, 28 deselected, 1 warning, in 832 s.
>    - Expect more passed (this plan's tests), the same skips, and 0 failed.
>
>    Please send the passed, skipped and deselected counts.
> 2. **The Stage 6 wording test:** `uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py -q -rs`.
>    - This plan did not edit it. Expect 7 passed and 0 skipped, as at `3406ba4`.

If any check fails, stop, and debug it with systematic-debugging before going on. Debug from the test name and reason the user reports, never from pilot text.

- [ ] **Step 3: Run the Plan Completion Protocol**

Follow writing-plans' Plan Completion Protocol:
- **Resolve-before-defer:** ask the user about anything left open, in one batch (AskUserQuestion, default option first).
- **Markup:** tick the steps, and set the status header `**Status: COMPLETE (YYYY-MM-DD)** — executed via <skill>; …`.
- **Deferred items:** this slice closes none of `specs/deferred_items.md`'s open items. P17-1, P17-2 and P17-5 stay with A3 and A8 (§Handoffs). Append a `18-…` section only if execution deferred something.
- **Backlog triage:** run it as the protocol describes.
- **The slice stamp:** append at the end of the spec's §Rollout, after plan 17's stamp:

  ```text
  > Plan A, slice 2: COMPLETE (YYYY-MM-DD) — implemented by plan 18 (specs/plans/completed/18-feasibility-pilot-and-threshold-calibration-plan-a-slice-2.md): A1, A2, and A9's dictionary rows for their records; FP23, A1 and A8 amended. Next: write plan A's remainder (A3–A5, then A8, each with A9's dictionary rows for its records).
  ```

  Commit it as `docs(specs): stamp Stage 11 plan A's second slice`.

  Do not append `Plan A: COMPLETE`. Do not tick Stage 11 on the roadmap.
- **Retire:** `git mv` this plan to `specs/plans/completed/` in one `chore(specs): retire plan 18` commit.

  **Do not move the spec**, an exception to the protocol's spec-retire rule: plans for A's remainder and B still implement it.

- [ ] **Step 4: Hand off what goes stale**

Tell the user, without editing these files:
- `CLAUDE.md`'s "Current state" names Stages 1–10. Stage 11's two slices could be noted there, but per the spec's Rollout and the user's rule, only with the user's approval.
- Plan A's remainder is next: a writing-plans session from `main` for A3–A5, using this plan's §Handoffs.

Then go on with finishing-a-development-branch.

---

## Handoffs to plan A's remainder

Verified at `36f12ec`, while this plan was written. Recheck each line number before relying on it.

- **FP23, as Task 1 amends it, for A8's `pilot run`.**
  - `run_theme_workflow` already reuses a stored extraction run whatever its mode. `_extraction` (`theme_workflow.py:667`) checks run ID, identity, policy, ceilings and prompt, never the mode. So `pilot run` sets `stored_extraction` to the pass's extraction directory, leaves `stored_coding` and `stored_support` null, and points `coding_cache` and `support_cache` at the pass's cache directories.
  - The workflow opens both caches in `replay` (`:926-931`), and its configuration-hash check at `:1020` hardcodes `replay`. Both stay right, since the new coding and support runs are replays.
  - **Trap: the provenance hash.** Support keys bind `source.provenance_hash` (`support/cache.py:106`). The workflow computes it as `analysis_provenance_hash(...)` (`theme_workflow.py:~898`). `pilot pass`, which composes the libraries without the workflow, must give its `SupportSources` the same value, or every support key misses in `pilot run`. Extract that computation into one shared helper that both call (D18-1); never copy it.
  - "Refuses if any request would dispatch": `replay_runtime(config)` (`:305`) fails closed on any dispatch, and a replay miss is a `replay_miss` row, not a dispatch. `pilot run` should refuse, or report as partial, any coding or support run whose reasons include `replay_miss`.
  - `WorkflowRuntime` is a frozen dataclass. Bind the calibrated policy with `dataclasses.replace(replay_runtime(config), assignment_policy=...)`.
- **A8's `pilot pass`** composes Task 6's `build_runtime(manifest, models_root)`:
  - extraction through `CachedAdapter(live.workflow.extractor, cache, "live")`;
  - `propose_run` with `live.workflow.classifier` and `CodingCache(cache, "live")`;
  - two `assess_run`s with `live.workflow.scorer` and `live.alternative_scorer`, the same judges, and one `SupportCache(cache, "live")`. Task 4's test shows the second run's judge calls all hit.
  - A8 picks how `models_root` is supplied: an option, or an environment variable.
  - **Trap: the CLI's import weight.** `test_ordinary_cli_help_loads_no_concrete_runtime` (`packages/earnings-themes/tests/test_import_boundaries.py`) fails if `--help` loads `nli.py` or the local adapter. `model_runtime` imports both inside `_build` for that reason. A8's command module may import `model_runtime` at module level, but must not import `nli.py`, the local adapter, or `transformers` there itself.
- **A8's `pilot run --fresh <id>`.** Pass `stability_run_id=<id>` with mode `fresh` to all three caches. Refuse an ID whose `fresh/<id>/` directory already exists under any of the three cache roots (§Failure handling: a crashed fresh run is rerun under a new ID).
  - Run one support run, the policy's scorer. A second run in the same fresh directory would be served the first run's judge replies (D18-5), so it is not wrong, but nothing needs it.
  - Then decide by replaying the workflow over the fresh directories, with the fresh extraction run stored.
- **A4 and A5** read `SupportRunRecord.cache_mode` and `stability_run_id`. The labels bind `target_input_hash`, and a target's ID (`support/resolve.py:366`) does not change between the pass's support run and `pilot run`'s replayed one.
- **Plan B's B1:**
  - The smoke should compare `ChatTokenCounter`'s count with the server's reported `prompt_tokens` on every call, since a GGUF's embedded chat template can differ from its repository's (Task 5).
  - `verify_files` requires each directory to hold exactly the listed files. Download with `--local-dir`, not into the Hugging Face cache, whose files are symlinks, and list or remove any README, `.gitattributes` or `mmproj` file.
  - `build_runtime` never queries the server's build (D18-12). The smoke should record it, for instance from llama.cpp's `/props`.
  - ADR 0006's model files fill `ChatModelFile`'s `revision`, `device`, `precision`, `input_limit` and `output_limit`.
- **A9's dictionary rows** for labels, preregistration, calibration, the report and gates go with the tasks that add those records.
- **Deferred into the remainder, unchanged:** P17-1 and P17-2 go with A8, and P17-5 is A3's item (2) and A8's items (1), (3) and (4) (`specs/deferred_items.md`, section `17-feasibility-pilot-and-threshold-calibration-plan-a-slice-1`).

---

## Self-review

- **Spec coverage:**

  | Spec point | Where it's built |
  | --- | --- |
  | A1: `fresh` joins `live` and `replay` on `CachedAdapter`, `CodingCache` and `SupportCache` (its scorer and judge entries) | Tasks 2, 3, 4 (one `CacheMode`, one `cache_directory`) |
  | A1: `fresh` never reads the main cache, as amended (D18-5) | Task 1 (amendment); Tasks 2–4 (zero-hit tests; within-run repeat test, Task 2) |
  | A1: writes under `<cache>/fresh/<stability_run_id>/`, and replays from there | Tasks 2–4 (replay-over-fresh tests) |
  | A1: keys are unchanged | D18-4: no schema bump, and no key function edited |
  | A1: every run record carries `cache_mode`, and under `fresh` the stability run ID | Tasks 2–4 (`cache_mode_problem`, D18-8) |
  | A1 tests: zero hits under `fresh`; dispatches equal requests; a later `replay` reproduces | Task 2 (`test_a_fresh_run_dispatches_every_request_over_a_populated_cache`), Task 3, Task 4 |
  | A2: a builder makes a `WorkflowRuntime` for `research` from `config/models/*.toml`: extractor, classifier, scorer, two judges | Task 6 (`build_runtime`, `RuntimeManifest`, `ChatModelFile`) |
  | A2: verifies every weight hash and runtime identity | Task 6 (`verify_files` on weights and tokenizer files; the scorers' own checks; the bindings' preflight; D18-12) |
  | A2: refuses a panel that breaks Stage 8's family rules before any dispatch | Task 6 (checked before any model file is hashed or loaded; D18-11) |
  | A2: chooses no model; ADR 0006 writes the configs | Task 6 (module docstring; no committed config) |
  | A2: a second support run with DeBERTa and the same judges; judge calls hit the cache in `live` | Task 6 (`LiveRuntime.alternative_scorer`); Task 4 (`test_a_second_scorer_reuses_the_judges_replies_in_live_mode`) |
  | A2: token counters are local tokenizers, so replay needs no model server | Task 5 (`ChatTokenCounter`); Task 6 (`test_a_runtime_built_for_replay_needs_no_server`) |
  | A2: scripted transports, and a replay test with transports that fail on any call | Task 6 (`httpx.MockTransport`; `failing`) |
  | A9: a data-dictionary row for every new record, enforced by `test_data_dictionary.py` | Tasks 2–6 |
  | §Verification: the fresh-mode zero-hit and replay tests | Tasks 2–4 |
  | §Gates, plan A: the session's scoped tests and Ruff; the user's suite and wording gate | Task 7, Steps 1 and 2 |
  | Brief F2: FP23 | Task 1 (D18-3) |

  Not here, by D18-2: A3–A5, A8, and A9's dictionary rows for their records.
- **Placeholders:** none.
  - Every code step shows its code.
  - The user's gate asks for counts that no session can know in advance.
  - `<sha>` and the dates are filled in at execution.
- **Type consistency.** These names are used identically across Tasks 2–6:
  - `CacheMode` (`REPLAY`, `LIVE`, `FRESH`), `STABILITY_RUN_PATTERN`, `StabilityRunId`, `cache_mode_problem(mode, stability_run_id, dispatched)`;
  - `cache_directory(directory, mode, stability_run_id) -> tuple[CacheMode, Path]`;
  - `CachedAdapter(..., *, stability_run_id=None)` with `.mode` and `.stability_run_id`; `CodingCache(..., *, stability_run_id=None)` and `SupportCache(..., *, stability_run_id=None)` with `.mode: str` and `.stability_run_id`;
  - `RunRecord`, `ProposalRunRecord` (and `CodingRunRecord`), `SupportRunRecord`: `.cache_mode`, `.stability_run_id`;
  - `make_proposal_job(...).run(..., stability_run_id=None, directory=None)`;
  - `verify_files(directory, files)` and `files_hash(files)` in `support.model_files`; `transport_weights_hash(identity)`;
  - `ChatTokenizerConfig(local_directory, files)`, `ChatTokenCounter(config, *, _loader=None)`;
  - `CHAT_ENCODING`, `RuntimeManifest`, `ChatModelFile`, `LiveRuntime(workflow, alternative_scorer, extractor_family)`, `build_runtime(manifest, models_root, *, transport=None, _tokenizer_loader=None, _scorer_runtime=None)`.
