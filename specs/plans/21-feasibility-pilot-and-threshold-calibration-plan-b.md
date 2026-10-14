# Stage 11 Plan B: Feasibility pilot and threshold calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the approved train/dev feasibility protocol through Plan A's merged interfaces and commit the calibrated pilot baseline, measured report, and user-approved V6 record.

**Architecture:** Reuse the application’s phase-separated passes, extraction-preserving replay, strict committed-byte intake, and pure evaluation package. Add only a fixture-only operator smoke harness; all model-loading and pilot-data operations, including B1–B8, run in the user's terminal. Agents implement and review invented-input code, maintain metadata documentation, and record the user’s safe output at explicit checkpoints.

**Tech Stack:** Existing Python >=3.14 workspace (repository interpreter pin 3.14.0), uv, Pydantic, Polars/Parquet, pytest, Ruff; existing optional local chat/NLI runtime. No new framework or required dependency.

**Spec:** `specs/feasibility-pilot-and-threshold-calibration.md`, approved 2026-10-11 and amended through plans 17–20. Read it with this plan.

> Roadmap: specs/evidence-linked-theme-extraction-roadmap.md, Stage 11

**Status:** IN EXECUTION (owner approved 2026-10-13) — Task 1 engineering steps 1–2 completed with reviewed corrections; B1 model/native evidence remains pending. Owner gates O1–O7 remain unresolved until their specified checkpoints.

**Base:** `25c9f6a7d1c0dc53ea98fc65c6d2ecf7881c6d0e` (merged Plan A, PR #24). Plans 17–20 implement A. Plan 20's **Execution verification** and **Plan B consuming handoff**, rather than its historical embedded patches, describe the as-built consumer contract.

## Global Constraints

- FP1: “Steps B1 and B2 may start as soon as plan A merges. B3 onward waits for the visibility gate (FP2).”
- FP2: “all 28 train and dev bundles are signed and committed, each dev bundle after its ledger row”; 20 train events, 8 dev events, 8 dev ledger rows. Test and excluded events are never run.
- FP3: “Any command that loads a model or reads pilot text runs in the user's own terminal.” Output to the agent is IDs, counts, closed reasons and metric figures only.
- FP8: “70 targets are sampled from train (at most 5 per event) and 24 from dev (3 per event), never by score.” Calibration needs at least 50 usable train joint labels.
- FP5/FP6/FP22: Gemma 4 31B-it is the extractor/classifier baseline only; two open-weight, self-hosted judges from two different families, neither Gemma; “both judges and MiniCheck resident at once, within 36 GB.” Include the actual Python scorer/tokenizer residency in the measurement.
- FP7: “`pointer-1`, Stage 9's classifier prompt and Stage 8's judge prompt run unchanged.” No prompt revision, sampled-temperature arm, model comparison, production selection, codebook change, hosted call or concurrent pilot workers.
- FP9/FP15: preregister before any pilot output, alone in its own commit; event-clustered 90% percentile intervals; dev lower-bound gates; strictly positive gold-evidence recall; undefined values fail any gate that exists. The owner chooses the undefined-interval consequence before results exist.
- FP12: “k = 3 fresh runs over dev's 8 events, at the baseline's own settings.” Main-cache bypass covers extraction, classifier, scorer and judge replies. Within-run duplicate requests may hit that fresh run's cache.
- FP17/GS3: committed research artifacts contain IDs, hashes, numbers and the user's answers only. No source/claim/quote text, responses, local paths, kept drafts, working labels, views, or anchored independent records enter Git.
- FP19: “No pytest over pilot text.” Agents do not execute full-root, Stage 6 wording, browser, live or user-only gates. Invented-input helper tests are separate from the user's live fixture smoke.
- GS13 persists through Stage 14's final test drafting. No drafting session reads extraction-stage code, prompts, outputs, Plan B artifacts/commands, or `data/runs/pilot/`. Execution/implementation sessions never open pilot text, a kept draft, anything under `data/runs/gold/` or `data/runs/pilot/`.
- Every B checkpoint's commit lands before the next B step starts; local-only steps checkpoint in the verification record with IDs/counts/hashes, never copy local material into a commit. B8 has separate report, gates/V6, and completion commits.
- Preserve exact span/hash verification, frozen pilot/split/codebook versions, source rights, masks, missingness and the immutable Stage 5 acquisition baseline. Passes and fresh runs make no Stage 5 state writes; ordinary `pilot run` uses Stage 10's existing replay workflow and may append checked processing transitions. It does not mutate acquisition records.
- Model acquisition and optional-extra installation are user-run setup with explicit choices; no automatic download, remote code, hosted inference, dependency upgrade or global environment change. Offline replay needs no running model server.

## Decisions

- **D21-1** (owner, brief, 2026-10-13): Plan from merged commit `25c9f6a7d1c0dc53ea98fc65c6d2ecf7881c6d0e`; use the approved stage spec and retired Plan A handoff. Applied in: Base, all tasks.
- **D21-2** (owner, brief, 2026-10-13): This session produces a reviewable plan and stops; no pilot steps, model download/load, pilot-text inspection or numeric preregistration selection. Applied in: planning verification and Execution Handoff.
- **D21-3** (owner, plan review, 2026-10-13): Add explicit owner checkpoints for P19-3 tie-group evidence and P19-4 labelled-event bootstrap population **before B2**, with no scoring change implied. Applied in: Task 2, owner gates O3/O4.
- **D21-4** (owner, execution instruction, 2026-10-13): Plan 21 is approved; execute its nine tasks in order using subagent-driven-development and a fresh engineering worktree. This supersedes D21-2's planning-session stop and the stale draft-review handoff below for this execution session. Approval does not settle O1–O7, V6 acceptance, or the separate concrete `CLAUDE.md` Current state diff approval. Preserve the exact implementation bodies, requirements, protected-input boundary and checkpoint commit order.
- **D21-5** (owner, execution correction approval, 2026-10-13): Approve the minimal diagnostic correction to Appendix A's helper: text-mode private temporary file plus Python stdout/stderr redirection, retaining native descriptor redirection and restoration. Approve an appended invented-input test exercising actual smoke preflight with Gemma in either judge slot and an uncalled-builder assertion. Preserve the original appendix bodies as historical planning text; these are the only approved executable departures. Applied in: Task 1 steps 1–2, commit `fa3240455e2183868a6f31183e213cd189c33a63`.
- **D21-6** (owner, O1 selection, 2026-10-13): Select Qwen2.5-14B-Instruct and Mistral-Nemo-Instruct-2407 as the two judge families, both Q4_K_M, using the existing llama.cpp runtime with one slot per judge and a provisional 8,192-token context. Acquisition candidates are Qwen GGUF revision `05244aa5d871c661c80082a15d3bce44714d068d` with original/tokenizer revision `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`, and Mistral GGUF revision `a2dd64a0a76ea1bdb2bb6ab6fa5496b003c7c908` with original/tokenizer revision `04d8a90549d23fc6bd7f642064003592df51e9b3`. Actual local files/hashes, runtime/build, applicable rights attestation, structured-output verification and resident-memory evidence are still pending; this selection does not complete O1/O2 or authorize pilot operations. Applied in: Task 1 step 3.
- **D21-7** (owner, O1 acquisition evidence, 2026-10-13): Report 13 judge files: one Qwen GGUF plus five tokenizer files, one Mistral GGUF plus six tokenizer files. The supplied GGUF SHA-256 values match the pinned upstream values: Qwen `e47ad95dad6ff848b431053b375adb5d39321290ea2c638682577dafca87c008`; Mistral `7c1a10d202d8788dbe5628dc962254d10654c853cae6aaeca0618f05490d4a46`. Report llama.cpp `0.5.0 (build 11146, commit 7fe450e19)`, built with AppleClang `21.0.0.21000334` for Darwin arm64. Confirm applicable weight/base-model terms were reviewed and permit local research use for both judges and ADR 0005's pinned DeBERTa alternative. Full user-supplied file metadata is retained in the controller ledger for the eventual real model TOMLs; agents did not open model files. Remaining chat settings, Gemma/scorer inventory and native evidence are pending; O1/O2 are not complete. Applied in: Task 1 step 3.
- **D21-8** (owner, remaining O1 judge settings, 2026-10-13): Select judge aliases `pilot-v1-qwen2.5-14b-q4_k_m` and `pilot-v1-mistral-nemo-12b-q4_k_m`, loopback ports 8081/8082, Metal GPU offload, input limit 6,144 and output limit 2,048 within each 8,192-token context, timeout 300 seconds, JSON-schema structured output enabled. Report Gemma GGUF/tokenizer and both scorers present “as best I know”; this is an availability report, not verified inventory. The two real judge TOMLs and exact runtime role mapping are prepared from these answers and D21-7 metadata, pending B1 evidence/commit. Native structured behavior, actual residency, remaining Gemma/scorer metadata and O2 provisional authorization remain outstanding. Applied in: Task 1 step 3.

- **D21-9** (owner, remaining O1 inventory/settings evidence, 2026-10-13): Report 20 prerequisite files: one retained Gemma GGUF, four Gemma HF tokenizer files, eight MiniCheck files and seven pinned DeBERTa files; together with D21-7 this is 33 files. The Gemma weight hash matches ADR 0004; both scorer inventories match ADR 0005. Report Gemma tokenizer revision `842da3794eaa0b77d5f08bae87a17459d91ff475`, class `GemmaTokenizer`, chat template present. Report installed versions torch `2.14.1`, transformers `5.18.0`, sentencepiece `0.2.2`, tokenizers `0.23.2`, safetensors `0.8.0`. Select Gemma's retained checkpoint/alias/port 8080, Metal offload, one slot, context 8,192, input 6,144, output 2,048, timeout 300 seconds and structured output enabled; select both NLI scorers on CPU float32 with complete input limit 512 and unchanged ADR 0005 pins, runtime, encodings and label mappings. Full returned hashes are retained in the controller ledger and prepared model TOMLs. No agent loaded or opened model/tokenizer contents. O2 provisional smoke limits/procedure and actual native/phase-residency evidence remain pending; no B1 completion or pilot authorization is implied. Applied in: Task 1 step 3.

- **D21-10** (owner, O2 provisional fixture authorization, 2026-10-13): Explicitly approve the complete smoke-limits JSON at SHA-256 `481394833468d21de0dff6b6c72d1fcfe0c53e67dee7fb7ee20da7449bf58bbd` for the single fixture attempt `s11-fixture-1`: temperature 0, seed 0, max_tokens 2,048 and structured output true for all generation roles; non-null 4,000-character structure-aware windows, 500-character claim limit; all extraction/classification/support request and token ceilings as materialized, including the shipped two-attempt rules. The classifier/judge 6,144 allowance includes reserved output, permitting at most 4,096 prompt tokens with this output setting. Explicitly select the reviewed foreground Gemma-to-both-judges procedure: context 8,192, one slot, all-layer Metal offload, fit off, reasoning off, retaining other pinned-build defaults; leave Python with both scorers and tokenizers resident through the transition. Select sampled Activity Monitor whole-system Memory Used, pressure and swap evidence in both phases, with sampling limitations and uncertain fit reported. Commands remain owner-terminal only in the main checkout. This authorizes the named fixture smoke only; measured timings/usage/residency and final baseline ceilings are still required before B1 completion/B2. Applied in: Task 1 step 4.

- **D21-11** (owner, focused O1/O2 correction and second fixture authorization, 2026-10-14): Select Gemma server context 12,288 and total classifier `input_limit` 12,288, retaining output 2,048. The owner-only diagnostic counted all 23 resolved coding requests: prompts 6,736–7,975 tokens (sum 160,238), requiring 8,784–10,023 with reserved output; all 23 failed `input_too_long` before budget reservation. The previous Gemma allowance 6,144 and server context 8,192 were insufficient. The reviewed one-field Gemma TOML correction has SHA-256 `f9bdb3c65828e813f6ed85f64d996aa4253cd3695809d12ae6e959aa7abc2540`, permitting 10,240 prompt tokens. Explicitly authorize one fresh `s11-fixture-2`, preserving the incomplete `s11-fixture-1`. Retain every other model setting, generation parameter, 4,000-character traversal window, 500-character claim limit, shipped two-attempt rule and numeric ceiling in the limits JSON at SHA-256 `481394833468d21de0dff6b6c72d1fcfe0c53e67dee7fb7ee20da7449bf58bbd`; retain the foreground Gemma-to-both-judges procedure and sampled both-phase Memory Used/pressure/swap method. Judge contexts remain 8,192 with total allowance 6,144. Prior Gemma-phase memory was not captured. Larger-context fit, all remaining native roles and final baseline budgets remain unverified; no B1 completion or pilot authorization is implied. Applied in: Task 1 steps 3–4.

- **D21-12** (owner, final O2 baseline ceiling selection and remaining evidence, 2026-10-14): Explicitly select the reviewed baseline limits JSON at SHA-256 `8fae7afbb60fe45e04e178c800f0ae87e5609423e0a65ad02840ead770d110cd`, retaining all generation/traversal settings. Extraction ceilings: 32 requests/document, 640/run, 7,864,320 tokens/run. Classification: 2 requests/claim, 128/document, 2,560/run, 1,572,864 tokens/document, 31,457,280/run. Each separate support pass: scorer calls 16/target, 2,048/document, 40,960/run; judge calls 8/target, 1,024/document, 20,480/run; judge tokens 6,291,456/document, 125,829,120/run. Run allowances reset per stage/partition/pass/fresh run; common run caps use the 20-document train partition and are not a lifetime budget. Document capacities at full retry bounds are 16 extraction windows, 64 claims and 128 support targets; unseen/fresh workloads may remain visibly incomplete, with no silent frozen-ceiling increase. Native `s11-fixture-2` completed all six roles in 150 returned calls, but the owner reports its memory observations “Not available” and responds “None that I know of” to the build/phase confirmation question. Record no known exceptions without inferring affirmative build/residency proof. Measured both-phase fit and actual runtime/phase evidence remain required before B1 completion/B2. No supplemental measurement or new fixture attempt is authorized by this answer. Applied in: Task 1 step 4.

## Owner gates — unresolved choices remain choices

These are execution checkpoints, not delegated decisions. Approving this plan does not fill them in. Log each actual answer in Decisions with its date and task, before dependent work.

| Gate | Owner input and evidence required | Blocks |
| --- | --- | --- |
| O1 | Two judge checkpoints/families, revisions, weight/base-model rights, local runtime/build, quantization, context/output limits and supported structured output. Recheck the pinned DeBERTa rights/files from ADR 0005; a different alternative needs an explicit design/spec disposition rather than changing the existing adapter's pin. Gemma's ADR 0004 checkpoint and baseline roles stay fixed. | Native B1 smoke |
| O2 | Actual server start/stop procedure, measured resident-memory fit in both phases, fixture-smoke call timings and usage, and the resulting explicit baseline parameters/request/token ceilings. Provisional fixture-smoke limits also need the owner; no test constants are baseline authorization. | B1 completion and B2 |
| O3 | P19-3: explicitly retain the shipped tie-group evidence convention for this preregistered baseline, or commission a separate design and known-answer implementation before B2. The operator supplies only counts/IDs indicating overlapping tie evidence, if available; agents do not inspect signed gold to decide. Reaffirm the decision if the eventual dev span-unit-F1 gate turns on this effect. | B2 commit; conditional B8 review |
| O4 | P19-4: explicitly retain all labelled-target events as the support-precision/scorer-AUC bootstrap population, or commission a separate design before B2. Judge-floor joint-labelled-event population stays as shipped. Reaffirm if the eventual support-precision lower bound depends on events without usable labels. | B2 commit; conditional B8 review |
| O5 | Numeric κ floor within the spec's 0.3–0.6 range; exact candidate IDs and sorted unique MiniCheck cutoff grids; recall floor ρ; sampling seed; extension step; bootstrap seed/resamples/max_undefined_share; and `undefined_gate` (`not_gated` or `point_estimate`). Choose without pilot output and attest that no pilot pass/run output has yet existed. | B2 commit |
| O6 | All 28 signed/committed train/dev gold files validate; all 8 dev records match committed ledger rows, with independent-before-draft commit ordering attested. Gold completion belongs to Plan 9/GS19, outside this plan. | B3 onward |
| O7 | Explicit acceptance of ADR 0007's measured feasibility findings and gate dispositions, including negative findings and undefined metrics. Separate approval of the concrete `CLAUDE.md` Current state diff. | V6 commit and completion |

If O3/O4 selects a scoring change, stop before B2 and have its design and implementation reviewed with invented-input tests. Do not improvise a scoring patch in this operational plan or revise a preregistration after seeing dev results. If a later trigger contradicts the registered convention, record the problem and obtain a protocol disposition; no result-guided refit or quiet version overwrite.

## As-built facts the executor must preserve

| Interface/behavior | Source at the base | Consequence |
| --- | --- | --- |
| `build_runtime(manifest: Path, models_root: Path, ...) -> LiveRuntime` eagerly constructs local tokenizers and **both** NLI scorers. | `apps/earnings-pipeline/src/earnings_pipeline/model_runtime.py` | Measure actual residency; restarting/unloading external Gemma is the operator's job. The application prompt is mandatory after classification and before support. |
| New A8 commands require JSON `--settings`; pass/fresh also need `--models-root`. | `apps/earnings-pipeline/src/earnings_pipeline/pilot_commands.py` | Do not invent a TOML PilotSettings format or a `pilot smoke`/`pilot preregister` command. |
| `PilotSettings(train, dev, runtime_manifest, alternative_scorer)` pins files by byte SHA-256. `WorkflowConfig` remains `mode="replay"`, even when the pilot pass uses live caches. | `pilot_records.py`, `theme_config.py`, `pilot_workflow.py` | The pilot orchestrator supplies mode. Never relax the general extract CLI to live. |
| `open_pilot` validates full pinned inventory, committed gold/ledger/preregistration and matching train/dev configuration before canonical source reads. | `pilot_inputs.py` | No reduced/resealed split, wrong run ID, test/excluded event, or missing committed label base may bypass intake. |
| Ordinary `pilot run` reuses extraction, replays classifier/support, and refuses any dispatch/cache miss. | FP23, `pilot_workflow.py` | Do not re-extract or reuse the pass's coding/support decisions under a new policy. |
| Retention (i) counts quote-reference occurrences including retry proposals; retention (ii) is accepted/assessed, not accepted/all targets. | Plan 20 consuming handoff, `pilot_reporting.py` | Use implemented denominators in tables and prose. |
| `write_report` first validates committed/reproducible coverage v2 and GS5 for both partitions. `write_gates` requires committed report bytes. | `pilot_reporting.py` | Commit coverage before report; commit report before gates. A GS5 mismatch blocks the entire report. |
| The failure table mentions explanation-only GS5 disposition; no implementation override exists. | stage spec Failure handling versus `recount_all` | Use reconciliation and legitimate re-signing through Stage 6. An explanation can document it but cannot bypass the reader. Any requested explanation-only path needs separate owner/design resolution. |
| `no_candidate` and below-floor judges are valid findings. Floor failure is reported-only under current Stage 9 routing. | approved Calibration/Failure handling | Do not change votes or retune dev to make a pass. Stage completion is evidence completion, not a quality-pass promise. |

## File ownership and deliverables

Only the smoke helper and its invented tests are new executable repository code. Existing domain/workflow modules are consumed, not refactored. Necessary deviations require a review checkpoint.

| Files | Owner and responsibility |
| --- | --- |
| Create `tools/stage11_fixture_smoke.py`, `tests/contracts/test_stage11_fixture_smoke.py`; append the smoke-limits section to `docs/data-dictionary.md` | Engineering worker: bounded, fixture-only operator harness, documented local input contract and preflight/output regression tests. No pilot reader or server manager. |
| Create `config/models/pilot-v1-runtime.toml`, `pilot-v1-gemma.toml`, `pilot-v1-judge-a.toml`, `pilot-v1-judge-b.toml`, `pilot-v1-minicheck.toml`, `pilot-v1-deberta.toml` | B1 owner-approved real model metadata; no weights or machine paths. |
| Create `docs/adr/0006-select-the-pilot-baseline-models.md` | B1 research/rights/runtime/memory/ceiling decision and evidence, pilot-only. |
| Local `data/runs/stage11-fixture-smoke/<id>/` | User only: fixture cache/output/measurements. Separate from pilot/gold. |
| Local `data/runs/pilot/config/train.json`, `dev.json`, `settings.json`; `data/runs/pilot/preregistration-fields.toml` | User only: explicit workflow selections and metadata input. No agent inspection even of local metadata under this root. |
| Create `evaluation/djia-2024q3-2026q2/pilot-v1/preregistration-v1.toml` | B2 alone-commit immutable protocol. |
| Create/append `evaluation/djia-2024q3-2026q2/pilot-v1/labels/support-labels-v1.toml` | B4/B6 owner answers only, checked append-only merge. |
| Create `.../calibration-v1.json`, `coverage-v2.json`, `report-v1.json`, `gates-v1.toml` under that evaluation directory | B5/B7/B8 generated numeric artifacts; separate immutable versioned outputs. |
| Create `docs/verification/pilot-v1-feasibility.md` | Checkpoint ledger, figures, provenance hashes, limitations, actual user gate results. No source examples or text. |
| Create `docs/adr/0007-adopt-the-pilot-feasibility-gates.md` | User-approved V6 decision. |
| Modify on actual completion only: this plan, `specs/deferred_items.md`, Stage 11 stamp in the roadmap and shared stage spec, approved `CLAUDE.md` Current state; optionally retire completed stage spec under the shared-spec check | Completion worker, after all owner gates. Never mark Stage 11 complete merely because this plan is written. |

Paths abbreviated with `...` above all resolve under `evaluation/djia-2024q3-2026q2/pilot-v1/`; commands below always use literal paths. No other implementation files are assigned.

## Execution setup and command conventions

Use `using-git-worktrees` at execution time for engineering work. The worker owns only the helper/test files and is not alone in the repository; do not revert other workers' changes. Gold drafting remains in isolated fresh sessions under its own allowlist. After code review, make the reviewed code available in the user's main checkout. **B1–B8 run there**, because that checkout holds local artifacts and authoritative HEAD byte bindings. Never copy protected data into an engineering worktree.

All command blocks below are instructions for execution **after plan approval**, not authorization for this planning session. The user can define this shell function in their terminal to keep every pilot command's uv flags identical:

```bash
function pilot21() {
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 UV_CACHE_DIR=/private/tmp/earnings-plan21-uv \
    uv run --locked --offline --no-sync --all-packages earnings-pipeline pilot "$@"
}
read 'EARNINGS_MODELS_ROOT?Absolute external models root: '
```

The models-root variable is local, never committed or echoed to the agent. Obtain new owner dates/IDs through explicit input as shown below. Literal `s11-dev-1/2/3` are proposed operational IDs, not preregistration numbers; use only if each is unused. For a failed fresh run, use a new ID and record both IDs; never delete/reuse the old directory to make the command pass.

### Task 1 (B1): Build the fixture-only smoke and record the baseline models

**Files:** Create the helper/test, six model TOMLs and ADR 0006 listed above; append the exact Appendix A smoke-limits section to `docs/data-dictionary.md`; start `docs/verification/pilot-v1-feasibility.md` with B1 evidence only.

**Interfaces:**
- Consumes: A2 `build_runtime(...) -> LiveRuntime`; Stage 1 canonical fixtures; existing `extract_run`, `StoredRun`, `SupportSources`, `propose_run`, `assess_run` and reply caches.
- Produces: fixture-only smoke CLI specified in Appendix A; validated real runtime manifest, identities, license evidence, measured memory/timings and owner-approved baseline policies/ceilings for Tasks 2–7.

- [x] **Step 1: Write the invented-input smoke boundary tests in Appendix A, then run RED**

Run in the engineering worktree:

```bash
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_stage11_fixture_smoke.py --tb=short -q
```

Expected RED: missing helper/API. Tests must demonstrate refusal **before runtime construction** for a path outside committed Stage 1 fixtures, modified fixture bytes, a reused output, and a Gemma judge; hostile exception text must not reach stdout/stderr. Use invented data/runtime injection only.

- [x] **Step 2: Implement Appendix A's complete helper; run GREEN and review**

Run the same node file and the existing `tests/contracts/test_data_dictionary.py`, plus `ruff check tools/stage11_fixture_smoke.py tests/contracts/test_stage11_fixture_smoke.py`, `ruff format --check` on those two files, and `git diff --check`, through the same locked/offline/no-sync uv environment. Expected: actual tests pass, lint/format clean. Do not run its native CLI as an agent. Review task/spec compliance and code quality before committing:

```bash
git add tools/stage11_fixture_smoke.py tests/contracts/test_stage11_fixture_smoke.py docs/data-dictionary.md
git commit -m "feat(pilot): add a bounded fixture-only operator smoke"
```

- [ ] **Step 3: Resolve O1 from current primary model cards and user acquisition**

The execution session verifies the owner's candidate judge model cards and pinned DeBERTa/base-model terms using primary sources, quotes only the necessary license words with direct URL/date, and presents a concrete role/config diff. No model checkpoint is selected by this plan. The user selects/downloads immutable files externally and supplies hashes/metadata only. Follow the applicable model-acquisition skill if a CLI is used. Preserve ADR 0004's Gemma weight hash and revision; preserve ADR 0005's supported scorer pins/runtime/encoding/label mapping. If a selected runtime needs a dependency change, stop for its focused review rather than upgrading unrelated pins.

`pilot-v1-runtime.toml` has this exact role mapping:

```toml
extractor = "pilot-v1-gemma.toml"
classifier = "pilot-v1-gemma.toml"
judges = ["pilot-v1-judge-a.toml", "pilot-v1-judge-b.toml"]
scorer = "pilot-v1-minicheck.toml"
alternative_scorer = "pilot-v1-deberta.toml"
```

Each chat file is `ChatModelFile`: `family`, loopback `base_url`, `model_id`, `runtime`, `runtime_version`, `structured`, `timeout_s`, `revision`, `device`, `precision`, `input_limit`, `output_limit`, models-root-relative `weights_directory`/`tokenizer_directory`, complete `weights`/`tokenizer_files` lists of `{relative_path, sha256}`, and a real `weight_license` (`source_url`, `terms_reference`, `intended_use`, `verified_on`, `permits_use=true`). Scorer files are the existing `LocalScorerConfig` TOML with relative `directory` replacing absolute `local_directory`; enumerate every actual file, no repeated/missing names, and MiniCheck input_limit ≤512. Construct dictionaries from the user's measured metadata and serialize with the existing `earnings_themes.tomlfile.dumps`; do not copy invented identity/rights statements from tests.

- [ ] **Step 4: User runs one fixture smoke and resolves O2**

The user first supplies the helper's explicit limits JSON from O2's provisional smoke authorization, installs only the already-declared optional runtime if missing, starts Gemma locally, and runs:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 UV_CACHE_DIR=/private/tmp/earnings-plan21-uv \
  uv run --locked --offline --no-sync --all-packages python tools/stage11_fixture_smoke.py \
  --manifest config/models/pilot-v1-runtime.toml --models-root "$EARNINGS_MODELS_ROOT" \
  --limits config/models/pilot-v1-smoke-limits.json \
  --fixture-id 0000877860-13-000100_ex-99-1 --run-id s11-fixture-1
```

The limits file is local execution input; keep it outside Git if it contains any local/private metadata, otherwise review it with model config. No pilot source is opened. At the checkpoint unload external Gemma and start both judges, then explicitly confirm. Record per-call time/usage, actual server builds and both phase residency including Python tokenizers and **both** scorers. FP22's two-judge+MiniCheck fit and Gemma phase must hold within 36 GB. Disk size alone is not resident-memory evidence. A no-target/partial/failed-role smoke is a visible incomplete check; do not claim every role ran. If B1 needs another attempt, record why and its unique ID, still fixture-only.

Use observed timings/usage plus the known retry rules and conservative corpus workload accounting to propose explicit ceilings; the user approves them before B2. Do not infer throughput/limits from pilot text or treat the fixture as a quality test. ADR 0006 records file hashes, role, model ID/revision, license URL/quote/date, runtime/version/build, memory observations and limitations, smoke ID/fixture/hash, timings and the ceiling rationale. It explicitly says pilot baseline, no production selection.

O2 records explicit approval of every generation parameter or deliberate retention of a shipped provisional default; an omitted JSON field is not owner approval. Keep structure-aware window traversal for the baseline. Whole-document and sampled-temperature comparisons remain Stage 14 arms, not fixture-informed configuration searches here.

- [ ] **Step 5: Commit B1 evidence before B2**

Check the exact staged file list; keep raw smoke outputs/weights/local directories out. Commit the six real TOMLs, approved ADR 0006 and B1-only verification prose with `git add` naming those files, then `git commit -m "docs(pilot): record the fixture-verified baseline runtime"`. Record the SHA and safe figures. Task 1 is complete only with actual user smoke and memory evidence, not synthetic test success.

### Task 2 (B2): Resolve method choices and freeze preregistration alone

**Files:** Create `evaluation/djia-2024q3-2026q2/pilot-v1/preregistration-v1.toml`; local preregistration fields and workflow settings; update Decisions and verification checkpoint ledger.

**Interfaces:**
- Consumes: O1/O2 baseline metadata; committed `load_pinned`, `pinned_split`, `pinned_codebook`; `Preregistration`, `freeze_preregistration(fields) -> Preregistration`, `preregistration_toml(record) -> str`.
- Produces: committed byte-identical preregistration; exact policy menu, sampling/bootstrap/gate rules; JSON `PilotSettings` and train/dev `WorkflowConfig` for Task 3.

- [ ] **Step 1: Stop for O3/O4 method decisions before choosing/finalizing B2 values**

Explain the existing P19-3 redundant-alternative credit/lowest-ID convention and P19-4 event population using invented examples and their backlog entries; no gold inspection. Record either explicit retention for this baseline or the separate prerequisite design. A separate design blocks B2; do not leave a promised patch hidden in this plan. Keep both backlog items open unless their own closure/disposition is actually met. Also record the stricter GS5 reconciliation route from the as-built table; no explanation-only bypass is promised.

- [ ] **Step 2: Owner supplies O5 values and inspectable metadata fields**

The user creates local `data/runs/pilot/preregistration-fields.toml`. Use the existing schema, with these fixed versus owner-supplied fields:

| Section | Fixed contract | Owner input |
| --- | --- | --- |
| Header | preregistration_version=1; actual pinned `Pin`, split.content_hash, and CodebookRef for approved v0 | None; derive, never hand-invent hashes |
| floor | statistic=`cohen_kappa`, reported=`gwet_ac1`, population=`family_verdict_vs_joint_label`, bound=`event_bootstrap_lower`, consequence=`reported_only` | floor in approved range |
| menu | each candidate: rule=`scorer_cutoff`, signal=`minicheck_joint`, signals=1 | candidate_id and sorted unique grid in [0,1] |
| selection | objective=`max_train_precision`, tie_break=`fewer_signals_then_lower_cutoff` | recall_floor ρ in (0,1] |
| sampling | pool=`assessed_and_flagged`, train_size=70, train_cap=5, dev_size=24, dev_cap=3, minimum_usable=50 | seed; positive extension_step; exhaustion/insufficient-label disposition |
| bootstrap | level=0.9; undefined resamples skipped and counted | seed, positive resamples, max_undefined_share in [0,1) |
| gates | rule=`dev-lower-bound/1`; exactly REQUIRED_GATES | undefined_gate=`not_gated` or `point_estimate` |

`REQUIRED_GATES` is release precision/recall, exact theme micro/macro F1, span-unit F1, gold-evidence recall and dev support precision. No agreement/AC1/AUC/rolled-up/rare-theme/stability/prevalence/bias metric is added as a numeric quality gate. The floor is separately reported in V6.

Use the complete metadata constructor in Appendix B to derive fixed fields, accept owner JSON choices interactively, validate and write the local TOML without any model or source loading. This is **user-run** because the destination is protected. Review the numbers/rules through a metadata-only owner summary. Do not ask the owner to paste the local file or views into chat.

- [ ] **Step 3: Freeze through the shipped API and commit only preregistration**

User runs this inherited Plan 20 mechanism:

```bash
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --locked --offline --no-sync --all-packages python - <<'PY'
from pathlib import Path
from earnings_themes import tomlfile
from earnings_themes.evaluation import freeze_preregistration, preregistration_toml

fields = tomlfile.read(Path("data/runs/pilot/preregistration-fields.toml"))
record = freeze_preregistration(fields)
target = Path("evaluation/djia-2024q3-2026q2/pilot-v1/preregistration-v1.toml")
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("x", encoding="utf-8") as stream:
    stream.write(preregistration_toml(record))
print(record.content_hash)
PY
git add evaluation/djia-2024q3-2026q2/pilot-v1/preregistration-v1.toml
git diff --cached --name-only
git commit -m "chore(pilot): preregister the feasibility baseline"
git show --format=fuller --stat HEAD
```

Expected: valid content hash; staged and committed change contains **only this one path**, before any pilot output. If other paths are staged, stop and isolate the commit without discarding their changes. Existing output is a refusal, not permission to overwrite/version-bump after results. Record the preregistration SHA/hash separately in the verification ledger after the alone commit.

- [ ] **Step 4: Specify local workflow selections; defer source preparation to O6**

Review Appendix C's constructor and collect its owner-approved policies/ceilings and metadata selections without opening source bytes. Its source-reading/copying body runs in the user's terminal only **after O6 in Task 3**; no new acquisition or re-canonicalization. The executor can guide schema fields from source, but never opens the user's configs or data. The constructor pins the authoritative 20 train and 8 dev event IDs from split v1, full explicit source files and all acquisition-run selections, existing codebook/prompts/uv.lock and baseline identities/policies/ceilings. Leave every stored selection and assignment policy/reference null. Use `scope="research"`, `mode="replay"`, local audience, capture false, masks as shipped, no invented family/copy/no-theme declarations. Train/dev ceilings and policies must agree exactly; use limits sufficient for train and freeze that common baseline before dev. Cache/output roots are under `data/runs/pilot/`, with partition-separated paths. Software/lockfile hashes are actual values, not fixture strings.

`PilotSettings` selects the two JSON files and runtime manifest by byte SHA-256 plus the exact `alternative_scorer.identity`. Local config hashes and the baseline policies/ceilings are included in the safe checkpoint evidence; full config files stay local. Before O6, only the metadata specification is prepared. Appendix C first rechecks visibility, then copies source bytes; Task 3's `open_pilot` intake validates all resulting bindings again before any pass.

### Task 3 (B3): Enforce visibility and run the train pass

**Files:** Local `data/runs/pilot/train/pass/` and caches; update `docs/verification/pilot-v1-feasibility.md` with O6 and B3 safe evidence only.

**Interfaces:** Consumes `PilotSettings`, committed preregistration/gold/ledger, `open_pilot(...) -> PilotIntake`; produces complete train `PassRecord` plus stored extraction/proposals/primary/alternative support, with no assignment decision.

- [ ] **Step 1: Obtain O6 and user-run gate output, never inspect the protected inputs**

The owner completes Plan 9 Task 19/GS19 independently and runs `gold validate` only for the literal train/dev IDs from split v1. No unqualified command that might select test is used. Check all 28 files are committed, every dev ledger row preceded its draft, every independent local byte hash still matches, and current gold validates. A historical “three signed” paragraph is not a current count. Record names/counts/reasons only. If missing, pause B3 while B1/B2 remain valid; do not draft gold in this execution session or sample replacements.

After O6, the user runs Appendix C to construct the confined immutable input bundle and settings, then runs the explicit intake check:

```bash
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --locked --offline --no-sync --all-packages python - <<'PY'
from pathlib import Path
from earnings_pipeline.pilot_inputs import open_pilot
from earnings_pipeline.pilot_commands import safe
from earnings_pipeline.stage6 import Layout, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH
from earnings_themes.split import Partition

@safe
def check():
    layout = Layout(Path.cwd(), UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH)
    intake = open_pilot(layout, Path("data/runs/pilot/config/settings.json"), Partition.TRAIN)
    print("visibility train 20 dev 8 committed_gold 28 ledger_rows 8")
    print("preregistration", intake.preregistration.content_hash)

check()
PY
```

Expected: successful intake with those exact inventory counts, or a closed refusal before source use. This user-run program reads protected independent bytes; agents never run it. A counts-only operator attestation covers the GS19 chronology the intake byte check cannot infer.

- [ ] **Step 2: User runs the baseline train pass and handles the operator checkpoint**

```bash
pilot21 pass --settings data/runs/pilot/config/settings.json --partition train --models-root "$EARNINGS_MODELS_ROOT"
```

Expected: 20 events, `status complete`, actual counts/reasons; mandatory unload-Gemma/load-both-judges confirmation between classification and support. No decision/policy is applied. On crash rerun the same baseline command and reuse cached replies; on `partial`, report it and resolve the explicit ceiling/failure disposition before proceeding. Never silently enlarge the frozen baseline after dev is exposed. Preserve hashes and all local partial evidence.

- [ ] **Step 3: Record and commit B3 checkpoint**

Record actual reviewed code SHA, user-run command/date, config/runtime/preregistration hashes, event count/status and safe failure/retry evidence in the verification doc. No output excerpts. Commit only `docs/verification/pilot-v1-feasibility.md` with `git commit -m "docs(pilot): record the train pass checkpoint"` after explicitly staging that file. Proceed only after the committed checkpoint is reviewed.

### Task 4 (B4): Collect blinded train support labels

**Files:** Local `data/runs/pilot/labels/views/train.md` and `labels/train-working.toml`; committed `evaluation/djia-2024q3-2026q2/pilot-v1/labels/support-labels-v1.toml`.

**Interfaces:** Consumes primary verified targets, score-independent deterministic sampler and label views; produces checked train support labels bound to preregistration and target input hashes. No score/judge/model identity is shown during labelling.

- [ ] **Step 1: User samples and renders the train views**

```bash
read 'EARNINGS_LABEL_DATE?Deliberate labelling completion date (YYYY-MM-DD): '
pilot21 labels sample --settings data/runs/pilot/config/settings.json --partition train
pilot21 labels view --settings data/runs/pilot/config/settings.json --partition train --labelled-on "$EARNINGS_LABEL_DATE"
```

Expected: up to 70 targets with cap 5/event, same deterministic sample in both commands. Any shortage is recorded and never filled by score or an alternative seed. The user sees only the local view. Both answers must be deliberately completed; initial `unsure` is a real answer, not evidence the user has worked through the target. No agent, drafting model, scorer, or judge helps answer.

- [ ] **Step 2: User labels, checks and commits answers only**

`claim_support` is `supported`/`unsupported`/`unsure`; `theme_fit` is `fits`/`does_not_fit`/`unsure`. Joint label is positive when both are positive, negative if either is negative, otherwise excluded and counted. Preserve attribution, time, scope and polarity when judging the claim. Do not edit IDs/hashes or add free text. Before promotion, finish every target and deliberately confirm any `unsure`; count usable joint answers locally with the existing `joint_label` helper. Committed `unsure` answers are final, not blanks to complete later.

```bash
pilot21 labels check --settings data/runs/pilot/config/settings.json --partition train
git add evaluation/djia-2024q3-2026q2/pilot-v1/labels/support-labels-v1.toml
git commit -m "data(pilot): commit blinded train support labels"
```

Expected: the whole sample validates and only IDs/hashes/answers/date/partition metadata is promoted. Existing committed answers are immutable; a changed base or Git failure refuses. Record total/usable/unsure counts through the user-safe summaries.

- [ ] **Step 3: If fewer than 50 joint labels are usable, follow the preregistered extension**

After the initial deliberate sample is committed, a shortage can only add new targets. The owner chooses the next extension count permitted by O5; run all three commands with that **same** count:

```bash
read 'EARNINGS_TRAIN_EXTENSIONS?Preregistered cumulative train extension count: '
pilot21 labels sample --settings data/runs/pilot/config/settings.json --partition train --extensions "$EARNINGS_TRAIN_EXTENSIONS"
pilot21 labels view --settings data/runs/pilot/config/settings.json --partition train --extensions "$EARNINGS_TRAIN_EXTENSIONS" --labelled-on "$EARNINGS_LABEL_DATE"
pilot21 labels check --settings data/runs/pilot/config/settings.json --partition train --extensions "$EARNINGS_TRAIN_EXTENSIONS"
```

The user labels new targets between view and check; do not run that block unattended. Existing answers remain unchanged, prefix/seed/cap remain fixed, and extension must add targets. Commit each checked extension before calibration. If the finite capped pool cannot supply 50 usable labels, stop and report protocol infeasibility for owner disposition; do not relax the minimum or invent labels.

### Task 5 (B5): Calibrate on train and freeze the baseline policy

**Files:** Create `evaluation/djia-2024q3-2026q2/pilot-v1/calibration-v1.json`; update verification ledger.

**Interfaces:** Consumes committed labels/preregistration and complete train pass; produces `CalibrationArtifact`, selected `CalibratedPolicy` or `no_candidate`, model/prompt/policy/ceiling configuration hash and train agreement/AUC figures.

- [ ] **Step 1: User runs calibration after label commit**

```bash
pilot21 calibrate --settings data/runs/pilot/config/settings.json --partition train
```

Expected: artifact hash and `selected` or `no_candidate` outcome; fewer than 50 usable labels refuses. Check every candidate's fitted cutoff and train precision/recall, exact preregistration/label hashes, both family κ/AC1/90% intervals/floor verdict/uncertain counts, both scorer AUCs and configuration hash in metadata-only output. Labels used for scorer AUC are `claim_support`; policy and floor use `joint_support`. Family uncertainty is a binary not-supporting verdict in the floor population; human `unsure` remains excluded and counted. A floor failure changes no assignment.

- [ ] **Step 2: Commit calibration before any dev pass**

```bash
git add evaluation/djia-2024q3-2026q2/pilot-v1/calibration-v1.json
git commit -m "data(pilot): freeze train calibration and baseline configuration"
```

Record the content hash and frozen `configuration_hash` distinctly from the JSON byte SHA, settings-file pins and pass content hash. Do not use a checkpoint hash as a configuration identity. `no_candidate` is committed as a valid all-review finding; do not skip dev/report/stability merely to conceal it. Any step that cannot proceed under that result must be surfaced as a real protocol blocker.

### Task 6 (B6): Replay train, expose dev once, and collect held-out labels

**Files:** Local train/dev runs and dev pass; append the committed support label file; update verification ledger.

**Interfaces:** Consumes frozen calibration and exact baseline; produces in-sample train decisions, first frozen-baseline dev decisions, and 24 held-out blinded dev labels.

- [ ] **Step 1: User computes train decisions with no server dispatch**

```bash
pilot21 run --settings data/runs/pilot/config/settings.json --partition train
```

Expected: 20 events, complete, `fresh none`; stored extraction reused, classifier/support replies replayed, no dispatch. A replay miss or policy/config/label-hash mismatch refuses. Do not start a server to fill a replay miss. Record train figures as in-sample.

- [ ] **Step 2: User exposes dev under the already-frozen baseline**

```bash
pilot21 pass --settings data/runs/pilot/config/settings.json --partition dev --models-root "$EARNINGS_MODELS_ROOT"
pilot21 run --settings data/runs/pilot/config/settings.json --partition dev
```

Expected: 8 events each, complete; mandatory live operator checkpoint for pass, zero-dispatch replay for run. No dev-informed configuration/prompt/grid changes or model selection. Commit the safe B6 pass/run checkpoint to the verification doc before labelling.

- [ ] **Step 3: User samples, labels and commits dev answers unaided**

```bash
read 'EARNINGS_LABEL_DATE?Deliberate dev labelling completion date (YYYY-MM-DD): '
pilot21 labels sample --settings data/runs/pilot/config/settings.json --partition dev
pilot21 labels view --settings data/runs/pilot/config/settings.json --partition dev --labelled-on "$EARNINGS_LABEL_DATE"
```

User reads only `data/runs/pilot/labels/views/dev.md` and completes `labels/dev-working.toml`, then:

```bash
pilot21 labels check --settings data/runs/pilot/config/settings.json --partition dev
git add evaluation/djia-2024q3-2026q2/pilot-v1/labels/support-labels-v1.toml
git commit -m "data(pilot): add blinded held-out dev support labels"
```

Expected: 24 targets, 3/event where the pool permits; train labels unchanged; same calibration configuration hash still binds. The calibration hash over train labels deliberately remains valid after append-only dev additions. Report any sample shortage explicitly; do not generate a replacement dev pass or refit the policy.

### Task 7 (B7): Measure fresh stability, independent agreement, coverage and GS5

**Files:** Local `data/runs/pilot/fresh/<id>/`; create `evaluation/djia-2024q3-2026q2/pilot-v1/coverage-v2.json`; update verification ledger.

**Interfaces:** Consumes baseline/calibration and committed dev labels/gold/ledger; produces exactly three complete fresh dev records, per-event independent figures, reproducible no-theme coverage and reconciled GS5 counts.

- [ ] **Step 1: User runs three fresh dev replicates sequentially**

```bash
pilot21 run --settings data/runs/pilot/config/settings.json --partition dev --fresh s11-dev-1 --models-root "$EARNINGS_MODELS_ROOT"
pilot21 run --settings data/runs/pilot/config/settings.json --partition dev --fresh s11-dev-2 --models-root "$EARNINGS_MODELS_ROOT"
pilot21 run --settings data/runs/pilot/config/settings.json --partition dev --fresh s11-dev-3 --models-root "$EARNINGS_MODELS_ROOT"
```

Each repeats extraction/classification/both support scorers with all main caches bypassed; confirm the server transition each time. Require complete status, 8 identical event IDs, matching baseline configuration/calibration and distinct IDs. Record each run ID, cache mode, per-kind dispatch/hit counts and operational failures through safe summaries. Within-fresh duplicate-key hits are allowed; main-cache hits are not. A partial/crashed run never counts toward three and never reuses its ID. Keep partial evidence local and list discarded and replacement IDs in the verification doc. If replacements are needed, supply their literal successful IDs to Task 8's repeated `--fresh` flags.

- [ ] **Step 2: User computes dev independent comparisons and ledger byte hash**

```bash
pilot21 independent --settings data/runs/pilot/config/settings.json --partition dev
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --locked --offline --no-sync --all-packages python - <<'PY'
from pathlib import Path
from earnings_core import sha256_hex
from earnings_pipeline.pilot_inputs import require_committed

repo = Path.cwd()
path = repo / "evaluation/djia-2024q3-2026q2/pilot-v1/independent-pass.toml"
require_committed(repo, path, "ledger")
print("independent_ledger_sha256", sha256_hex(path.read_bytes()))
PY
```

Expected: two comparisons for each of 8 events: independent versus kept draft; signed gold versus independent, each release-ID agreement/exact theme F1/unit F1. The command verifies raw independent bytes against the committed ledger before anchoring. Anchored pointer records remain local; no sidecar/schema field is added. The verification doc must cite the **exact byte SHA-256** above, not just a ledger content identifier. Figures are descriptive, not a correction of the gold or an independent-annotator claim.

- [ ] **Step 3: User freezes and commits coverage v2**

```bash
pilot21 coverage --version 2
git add evaluation/djia-2024q3-2026q2/pilot-v1/coverage-v2.json
git commit -m "data(pilot): freeze observed train and dev no-theme coverage"
```

Expected: original coverage-v1 acquisition run IDs preserved, observed no-theme counts over signed train/dev gold, byte-reproducible coverage. No missing acquisition class is repaired by reselection and no zero model output becomes a no-theme signature. Coverage v2 reuses its pinned acquisition history rather than replacing it with ordinary replay's appended processing states.

- [ ] **Step 4: User reruns the train/dev GS5 recheck before shares/reporting**

Use `pilot recount` with the literal sorted 28 train/dev IDs from the pinned split, passed as arguments through Appendix D's exact user-only launcher. Never call unqualified `pilot recount`, which can select committed test gold in a later checkout. Require no mismatch; record accepted/edited/rejected/added counts and denominators. If a mismatch occurs, stop, reconcile through the Stage 6 user-owned re-signing procedure, and rerun all invalidated bindings/checks before any shares are published. Do not alter source/draft text to make a counter pass. If source/gold bindings change after baseline exposure, obtain an explicit protocol disposition before continuing.

Commit the B7 safe verification checkpoint before Task 8. Keep P19-3/P19-4 open at their stated triggers; obtain the owner's registered-method reaffirmation if the actual numeric findings make them consequential.

### Task 8 (B8): Commit the report, derive V6 gates and obtain approval

**Files:** Create `evaluation/djia-2024q3-2026q2/pilot-v1/report-v1.json`, then `gates-v1.toml`; complete `docs/verification/pilot-v1-feasibility.md`; create ADR 0007.

**Interfaces:** Consumes committed coverage/calibration/labels, baseline plus three complete fresh runs; produces `PilotReport`, `Gates`, `GateVerdict`, approved V6 decision and actual-gates reject-everything regression evidence.

- [ ] **Step 1: User generates report with exactly the three successful fresh IDs**

```bash
pilot21 report --settings data/runs/pilot/config/settings.json --fresh s11-dev-1 --fresh s11-dev-2 --fresh s11-dev-3 --version 1
```

Expected: 2 partitions and 8 per-event independent figures in a valid sealed report. If replacement IDs were used, replace the corresponding flags with the recorded successful IDs before running; do not include discarded/partial IDs. GS5 mismatch, uncommitted/nonreproducible coverage, invalid run IDs or config hashes refuse **before output**.

Use the coverage matrix below to write the verification document from numeric metadata/user safe output only. Every table caption/figure is **feasibility-only**; train is **in-sample**. Include point estimates, intervals, undefined counts/reasons and event denominators from the report. Appendix F supplies a user-run numeric supplement for observed per-event distributions and per-theme exact F1, which the current aggregate report schema does not retain. Keep that supplement in the verification prose/tables without adding a new sidecar or changing `PilotReport`. No source evidence examples are needed in this document.

| Figures | Required interpretation |
| --- | --- |
| Release-ID precision/recall | Kept attempt `confirmed` versus gold label; ambiguous labels excluded and counted. |
| Exact micro/macro theme F1 | Event × theme cells; uncertain-only cells excluded/counted; tie-group one either-of cell, registered evidence convention stated. |
| Level-one roll-up F1 | Secondary; self/descendant mapping; sibling earns no exact-level credit. |
| Unit precision/recall/F1; character Jaccard | Pointer-unit evidence grain versus partial gold passages; unit F1 gated, Jaccard secondary. |
| All three retention measures | Verified/proposed quote-reference occurrences; accepted/assessed; recovered gold-supporting units. Gate only gold-evidence recall, strictly >0. |
| Train/dev joint support precision | Train fits policy, dev held-out; usable/unsure/no-acceptance populations explicit. |
| MiniCheck and DeBERTa joint AUC | Claim-support label task, never theme-fit/joint task; undefined AUC retained. |
| Family floor and four view diagnostics | κ/AC1 and uncertainty counts, preregistered floor/bound; family failure reported-only, AC1 never gated. |
| Hard negatives | False acceptance overall and by annotated negative kind; annotated pilot negatives included. |
| Fresh stability | Fleiss κ event×theme presence; mean pairwise unit-set and accepted-assignment Jaccard; k=3 complete runs; temperature-zero result is runtime nondeterminism only. |
| Rare-theme recall | Descriptive, support in ≤2 events; never quality gate. |
| Sector prevalence, source-selection bias | Not estimated, with pilot-size/selection reason. |
| Independent, GS5 and no-theme | Per-event descriptive comparisons plus exact committed ledger byte hash; reconciled GS5 counts/shares per partition; signed no-theme counts/coverage gaps. |
| Operations and provenance | Actual code/lock/runtime/model/prompt/policy/ceiling/preregistration/calibration hashes, dates, run IDs, usage and retries/failures, memory limits; source rights and cache/local retention limits. Unknown usage stays unknown. |

State one annotator, gold drafting-model conflict/GS19 limitations, tiny dev event count, capped sample, undefined intervals, reviewed overrides and observed coverage gaps. A negative feasibility finding may complete Stage 11; never describe these measurements as sector validation or production approval.

- [ ] **Step 2: Commit report before gate generation**

```bash
git add evaluation/djia-2024q3-2026q2/pilot-v1/report-v1.json docs/verification/pilot-v1-feasibility.md
git commit -m "data(pilot): record feasibility report and measured limitations"
pilot21 gates --settings data/runs/pilot/config/settings.json --report-version 1 --version 1
```

Expected: gate file binds committed report/preregistration hashes; baseline verdict prints a **list** of rows, preserving the independent positivity rule even when a metric repeats. Every lower-bound gate is from the dev baseline, with the preregistered undefined-interval fallback/ungated reasons. A `None` candidate metric fails an existing gate; positivity still applies when evidence-recall bounds are zero or absent. No threshold is tuned after seeing these results.

- [ ] **Step 3: User reruns evaluator against actual gate bytes and an invented reject-all input**

Run Appendix E. It loads actual sealed gates and the committed report, checks their hash binding, reevaluates the actual baseline, and evaluates an invented reject-everything `PartitionReport`. Expected: reject case fails with `zero_gold_evidence_recall` independently of vacuous/undefined lower-bound rows. This is a regression of the evaluator with measured thresholds, not a second pilot configuration or dev rerun. Record safe list results and command/SHA; do not replace reported baseline figures with the invented case.

- [ ] **Step 4: Draft ADR 0007 and obtain O7 before committing it**

ADR 0007 cites ADR 0006, preregistration/calibration/report/gates hashes and verification document; lists gated metrics and numeric bounds exactly as generated, ungated/undefined dispositions, judge floor and per-family findings, descriptive-only metrics, those not estimated and reasons, registered P19-3/P19-4 conventions, reject-all evidence, and baseline configuration identity. It says this is V6 for a feasibility pilot, not production selection. Explain `no_candidate` or below-floor outcomes plainly if observed.

Show the concrete ADR and numeric artifact summary for the user's review. The approved spec **Gates** and B8 explicitly require approval; do not infer it from silence or from general plan approval. With approval, commit `gates-v1.toml`, ADR 0007 and the corresponding verified prose. This commit must exist before **any** Stage 14 configuration comparison. No comparison is part of this plan.

### Task 9: Verify, complete Stage 11 and hand off without executing later stages

**Files:** Verification doc, this plan, `specs/deferred_items.md`, roadmap/stage-spec stamps, separately approved `CLAUDE.md` Current state. No change to the global theme spec or later-stage designs.

**Interfaces:** Consumes approved V6 artifacts and actual check results; produces reviewed completion evidence, narrow backlog dispositions and later-stage consuming handoffs.

- [ ] **Step 1: Run only agent-safe engineering checks and final review**

Engineering agent runs the smoke helper's invented test file, applicable pure evaluation/contracts and Ruff after source auditing selected readers. Use Plan 20's allowed individual groups rather than full-root/wording/live/browser. A minimal changed-code gate is:

```bash
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --locked --offline --no-sync --all-packages pytest tests/contracts/test_stage11_fixture_smoke.py packages/earnings-themes/tests/evaluation tests/contracts/test_import_scan.py tests/contracts/test_data_dictionary.py --tb=short -q
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --locked --offline --no-sync ruff check .
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --locked --offline --no-sync ruff format --check .
git diff --check
```

Expected: actual passing counts and clean lint/diff; no type checker is configured. Do not sync/download or run `uv lock` to make checks pass. Use requesting-code-review for whole-branch review, with spec, base/tip SHAs, this plan, actual user safe evidence and the same no-protected-reader constraints. No reviewer opens local artifacts or pilot text.

- [ ] **Step 2: Obtain final SHA-bound user root and wording gates**

Generate literal commands for the reviewed SHA in the user's main checkout. The user runs:

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser" --tb=short -q
uv run --locked --all-packages pytest tests/integration/test_stage6_wording.py --tb=short -q -rs
```

Provide actual SHA via `git rev-parse HEAD`, not a placeholder HEAD assumed later. User reports counts, exit status, elapsed time, warnings and failing names/closed reasons only. Historical Plan 20 counts (4893 passed, 3 skipped, 28 deselected, 1 warning) are provenance, **not** expected totals for this tip. Agents do not run either command. On failure apply systematic-debugging from the safe evidence, reproduce with invented inputs where possible, review fixes, and obtain gates at the new SHA. Never request traceback frames or source text.

- [ ] **Step 3: Resolve leftovers and obtain the specific Current state approval**

Use writing-plans' resolve-before-defer gate. A missing owner answer or missing live evidence is not a completed pilot step. No new scoring conventions, unexplained mismatches, incomplete fresh run, unsigned bundle, absent metric or unapproved ADR is silently deferred to tick Stage 11.

Present the exact `CLAUDE.md` Current state diff, replacing the existing Plan A paragraph with measured status and links to ADRs 0006/0007 and the verification record. Word it from actual outcomes; do not promise a successful configuration. The stage spec Rollout requires user approval before applying this diff. Record approval/decline and its disposition; do not treat this plan approval as approval of future factual text. Do not rewrite historical sections or source notes as part of status maintenance.

- [ ] **Step 4: Update backlog dispositions, handoffs and Stage 11 stamps only after all exit evidence exists**

Keep already-closed Plan A items closed. Mark the Plan 9 unsigned-bundle item done only if its separate user-owned closure (all 28 committed + `gold validate`) was actually evidenced, and credit the Stage 6 work/commit, not new Plan B implementation. P18-1/P18-2, P19-2, unrelated P17/P16/P15 items and Plan 12 failure-output/partial-record/concurrency items stay deferred under their existing triggers. P19-3/P19-4 get the actual owner disposition while retaining historical text; do not tick them merely because an owner checkpoint occurred. Append new leftovers only with paths, reason, Size and a concrete Done when/Revisit if condition.

Add actual `## Handoff to later stages` bullets, citing the stage spec Handoffs:

- Stage 12: train-only verified evidence/novelty and per-theme figures, exact local interfaces/artifact hashes; no dev discovery or codebook change.
- Stage 14: actual gates/evaluator, frozen pilot baseline configuration hash and calibrated policy or no-candidate finding, dev comparison corpus, fresh mode, in-sample caveat; prompt/model/temperature arms and single held-out test evaluation remain its work. GS13 remains intact through test drafting.
- Stage 15: compatible cached pilot replies and current binding rules, but full run uses Stage 14's selected configuration; concurrency/recovery remain its decisions, no implicit cache reuse across changed keys.
- Stage 16: dev independent-pass numeric findings/ledger hash and unchanged Claude drafting conflict; optional hosted ceiling remains separately authorized.

Record deviations/traps found in execution, including any refused/incomplete path, from the execution ledger. Cite current interfaces/paths and spec; do not infer the handoff from final code alone. The approved stage spec supersedes roadmap phrases claiming Stage 11 chooses production models, permits train-informed prompt changes here, or lacks fresh mode. Report those stale descriptions in the handoff for derive-roadmap's **next resume**, without redesigning later stages in this plan.

Tick **only Stage 11** and append the approved Rollout stamp to the stage spec and the roadmap. Name Plan A as plans 17–20 (the spec's A-id slot may name 20 with an explicit “completes plans 17–20” qualifier) and Plan B as plan 21, both at retired paths. Do not alter historical Plan A completion stamps. Include the roadmap's required `Next: resume the roadmap.` line. Shared/global theme specs and the roadmap remain live; Stage 11's dedicated feasibility spec is eligible for retirement only after the no-other-live-plan/shared-spec check in the skill. Repoint links if moved. Do not automatically retire it while B is still active.

- [ ] **Step 5: Retire this plan and offer branch integration after gates**

Mark completed steps once the done/deferred partition is final, with actual deviations and status/date. Run:

```bash
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --offline --no-project --python 3.13 python /Users/lowell/.agents/skills/writing-plans/scripts/deferred_stats.py
```

Report actual backlog summary and apply the skill's read-only triage rubric when its threshold is met; changing backlog dispositions is the owner's call. Retire this plan with `git mv` to `specs/plans/completed/21-feasibility-pilot-and-threshold-calibration-plan-b.md` in a focused `chore(specs): retire plan 21` commit. Apply the dedicated spec's retirement rule only when eligible; never move the live roadmap/global spec. Use finishing-a-development-branch for the explicit integration/cleanup choice. End with a resume-roadmap handoff; do not plan or execute a later stage in the completion session.

## Coverage and checkpoints

| Approved requirement | Plan home |
| --- | --- |
| B1, FP5/6/22, ADR 0006, V4-style rights/hash/native/memory evidence | Task 1 and Appendix A |
| B2 / Preregistration, owner values, commit before output | Task 2 and Appendix B |
| FP2/GS19 / B3, exact full inventory and no test/excluded | Task 3; Appendix C input validation |
| B4/FP8/FP21, blinded labels and minimum/extension | Task 4 |
| B5 / Calibration / R8.2/8.4/8.6 | Task 5 |
| B6 / FP4/FP23, freeze before first dev and held-out labels | Task 6 |
| B7 / FP11/12 / R12.10 | Task 7 step 1 |
| FP16 / independent / exact committed ledger byte hash | Task 7 step 2 |
| B7 / D4 / R12.4 / GS5 | Task 7 steps 3–4 and Appendix D |
| B8 / Metrics / R12.2/12.5/12.7 / all Stage 11 exit clauses | Task 8 matrix |
| V6 / D1 / R13.1 / reject-everything R12.8 | Task 8 steps 2–4 and Appendix E |
| User gates, completion, shared-spec status, later consumers | Task 9 |
| Failure handling/blinding/visibility at every step | Global Constraints, as-built table, Tasks 3–8 |

## Appendices — exact execution bodies

Appendices are part of the plan's tasks, not actions performed by this planning session.

### Appendix A: Fixture-only smoke helper and boundary tests

Create `tools/stage11_fixture_smoke.py` with this body. `--manifest`, `--limits` and all output references are repository-relative. Only `--models-root` is an external machine path. Optional runtimes are loaded only after all lightweight preflight checks. The harness deliberately makes no assignment decision and no quality assertion. A native support disagreement is allowed; an unavailable/incomplete role is not a complete smoke.

```python
"""User-run Stage 11 smoke on one committed Stage 1 fixture; never a pilot reader."""

import argparse
import contextlib
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import tomllib
from earnings_core import canonical_json, digest, sha256_hex
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_ingestion.fetch.store import write_new
from earnings_pipeline.model_runtime import (
    ChatModelFile,
    RuntimeManifest,
    build_runtime,
)
from earnings_pipeline.theme_config import confined_path
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import load_codebook
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.records import CodingCeilings, CodingPolicy
from earnings_themes.coding.run import propose_run
from earnings_themes.extraction.cache import CachedAdapter
from earnings_themes.extraction.prompt import parse_template
from earnings_themes.extraction.records import Ceilings, ExtractionPolicy, Parameters
from earnings_themes.extraction.run import extract_run
from earnings_themes.extraction.store import StoredRun, write_run
from earnings_themes.records import Part, parse
from earnings_themes.support import assess_run, write_support_run
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.records import (
    Presentation,
    SupportCeilings,
    SupportPolicy,
    SupportSources,
)

REASONS = frozenset(
    {
        "fixture_not_allowlisted",
        "fixture_not_committed",
        "output_exists",
        "judge_family_conflict",
        "extraction_incomplete_or_empty",
        "classification_incomplete_or_empty",
        "support_not_ready",
        "support_incomplete",
        "roles_not_exercised",
        "malformed_arguments",
        "smoke_failed",
    }
)


class SmokeRefused(ValueError):
    def __init__(self, reason):
        super().__init__(reason if reason in REASONS else "smoke_failed")


class Limits(Part):
    extraction_policy: ExtractionPolicy
    extraction_ceilings: Ceilings
    coding_parameters: Parameters
    coding_ceilings: CodingCeilings
    support_parameters: Parameters
    support_ceilings: SupportCeilings


def committed(repo, relative):
    path = confined_path(repo, relative)
    result = subprocess.run(
        ["git", "show", "HEAD:" + relative],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    data = path.read_bytes()
    if result.returncode != 0 or result.stdout != data:
        raise SmokeRefused("fixture_not_committed")
    return data


def panel(repo, manifest_path):
    manifest = parse(
        tomllib.loads(manifest_path.read_text()), RuntimeManifest, "runtime_manifest"
    )
    root = manifest_path.parent.relative_to(repo).as_posix()

    def chat(name):
        path = confined_path(repo, root + "/" + name, "config/models")
        return parse(tomllib.loads(path.read_text()), ChatModelFile, "chat_model")

    family = chat(manifest.extractor).family
    if chat(manifest.classifier).family != family:
        raise SmokeRefused("judge_family_conflict")
    judges = tuple(chat(name).family for name in manifest.judges)
    if len(set(judges)) != 2 or family in judges:
        raise SmokeRefused("judge_family_conflict")


class Measured:
    def __init__(self, delegate, role, calls, sink):
        self.delegate, self.role, self.calls, self.sink = delegate, role, calls, sink

    @property
    def identity(self):
        return self.delegate.identity

    def count_tokens(self, request):
        return self.delegate.count_tokens(request)

    def call(self, method, request):
        started = perf_counter()
        row = {"role": self.role, "call": len(self.calls) + 1}
        try:
            counted = (
                self.delegate.count_tokens(request)
                if hasattr(self.delegate, "count_tokens")
                else None
            )
            reply = getattr(self.delegate, method)(request)
            usage = getattr(reply, "usage", None)
            row.update(
                status="returned",
                local_input_tokens=counted,
                reported_input_tokens=(
                    usage.prompt_tokens
                    if usage
                    else getattr(reply, "input_tokens", None)
                ),
                reported_output_tokens=(usage.completion_tokens if usage else None),
            )
            return reply
        except Exception:
            row.update(status="failed")
            raise
        finally:
            row["elapsed_ms"] = max(0, round((perf_counter() - started) * 1000))
            self.calls.append(row)
            self.sink(row)

    def complete(self, request):
        return self.call("complete", request)

    def score(self, request):
        return self.call("score", request)


def smoke(
    repo,
    manifest,
    models_root,
    fixture_id,
    limits_path,
    run_id,
    *,
    builder=build_runtime,
    ready=None,
    sink=lambda row: None,
):
    repo = repo.resolve()
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", run_id) is None:
        raise SmokeRefused("malformed_arguments")
    allowed = tomllib.loads(
        committed(repo, "tests/fixtures/releases/manifest.toml").decode()
    )
    if fixture_id not in {row["fixture_id"] for row in allowed["fixtures"]}:
        raise SmokeRefused("fixture_not_allowlisted")
    fixture_rel = f"tests/fixtures/canonical/{fixture_id}.json"
    confined_path(repo, fixture_rel, "tests/fixtures/canonical")
    fixture = committed(repo, fixture_rel)
    manifest_path = confined_path(repo, manifest, "config/models")
    panel(repo, manifest_path)
    limits = Limits.model_validate_json(confined_path(repo, limits_path).read_bytes())
    output = confined_path(
        repo,
        "data/runs/stage11-fixture-smoke/" + run_id,
        "data/runs/stage11-fixture-smoke",
    )
    if output.exists():
        raise SmokeRefused("output_exists")
    extraction_text = committed(repo, "prompts/extraction/pointer-1.md").decode()
    coding_text = committed(repo, "prompts/coding/deductive-1.md").decode()
    support_text = committed(repo, "prompts/support/judge-1.md").decode()
    book_path = "codebooks/djia-pilot/codebook-v0.toml"
    book_bytes = committed(repo, book_path)
    book = load_codebook(repo / book_path)
    canonical = from_fixture_json(fixture.decode())
    bundle = Bundle(
        fixture_id, canonical.document, canonical.elements, canonical.masked.masks
    )
    software = {"lock_hash": sha256_hex(committed(repo, "uv.lock"))}
    started = datetime.now(timezone.utc)
    rt = builder(manifest_path, models_root)
    if len({j.identity.family for j in rt.workflow.judges}) != 2 or any(
        j.identity.family == rt.extractor_family for j in rt.workflow.judges
    ):
        raise SmokeRefused("judge_family_conflict")
    output.mkdir(parents=True, exist_ok=False)
    calls = []

    def measured(delegate, role):
        return Measured(delegate, role, calls, sink)

    identities = {
        "runtime_manifest": {
            "path": manifest,
            "sha256": sha256_hex(manifest_path.read_bytes()),
        },
        "extractor_family": rt.extractor_family,
        "extraction_identity": rt.workflow.extractor.identity.model_dump(mode="json"),
        "classifier_identity": rt.workflow.classifier.identity.model_dump(mode="json"),
        "scorer_identity": rt.workflow.scorer.identity.model_dump(mode="json"),
        "judge_identities": [
            j.identity.model_dump(mode="json") for j in rt.workflow.judges
        ],
        "alternative_scorer": rt.alternative_scorer.identity.model_dump(mode="json"),
    }
    write_new(output / "identities.json", canonical_json(identities))
    result = extract_run(
        (bundle,),
        CachedAdapter(
            measured(rt.workflow.extractor, "extractor"),
            output / "cache/extraction",
            "live",
        ),
        limits.extraction_policy,
        parse_template(extraction_text),
        limits.extraction_ceilings,
        run_id="stage11-fixture-extraction",
        started_at=started,
        software=software,
    )
    stored = StoredRun.of(result)
    write_run(output / "extraction", stored, (bundle,))
    if not stored.claims or any(
        d.outcome.value != "completed" for d in stored.documents
    ):
        raise SmokeRefused("extraction_incomplete_or_empty")
    sources = SupportSources(
        stored,
        (bundle,),
        book,
        digest(
            {
                "fixture_sha256": sha256_hex(fixture),
                "codebook_sha256": sha256_hex(book_bytes),
            }
        ),
    )
    proposal = propose_run(
        "stage11-fixture-classification",
        sources,
        tuple((claim.doc_id, claim.claim_id) for claim in stored.claims),
        measured(rt.workflow.classifier, "classifier"),
        CodingPolicy(
            prompt_text=coding_text,
            prompt_hash=sha256_hex(coding_text.encode()),
            parameters=limits.coding_parameters,
        ),
        limits.coding_ceilings,
        cache=CodingCache(output / "cache/coding", "live"),
        started_at=started,
        software=software,
    )
    if not proposal.targets or any(
        c.status != "completed" for c in proposal.classifications
    ):
        raise SmokeRefused("classification_incomplete_or_empty")
    if ready is None or not ready():
        raise SmokeRefused("support_not_ready")
    judges = tuple(
        measured(judge, role)
        for judge, role in zip(rt.workflow.judges, ("judge_a", "judge_b"), strict=True)
    )
    policy = SupportPolicy(
        support_version="semantic-support/1",
        prompt_text=support_text,
        prompt_hash=sha256_hex(support_text.encode()),
        parameters=limits.support_parameters,
    )
    primary = None
    for role, scorer in (
        ("minicheck", rt.workflow.scorer),
        ("deberta", rt.alternative_scorer),
    ):
        support = assess_run(
            "stage11-fixture-" + role,
            sources,
            proposal.targets,
            measured(scorer, role),
            judges,
            policy,
            limits.support_ceilings,
            extractor_family=rt.extractor_family,
            cache=SupportCache(output / "cache/support", "live"),
            started_at=started,
            software=software,
        )
        write_support_run(output / role, support, sources)
        if not support.assessments or any(
            a.outcome.status.value in {"incomplete", "refused"}
            for a in support.assessments
        ):
            raise SmokeRefused("support_incomplete")
        if role == "minicheck":
            primary = support
    expected = {
        (j.identity.family, presentation)
        for j in rt.workflow.judges
        for presentation in Presentation
    }
    actual = {
        (trial.identity.family, trial.presentation)
        for a in primary.assessments
        for trial in a.trials
        if trial.answer is not None
    }
    counts = Counter(row["role"] for row in calls if row["status"] == "returned")
    if not expected <= actual or set(counts) != {
        "extractor",
        "classifier",
        "judge_a",
        "judge_b",
        "minicheck",
        "deberta",
    }:
        raise SmokeRefused("roles_not_exercised")
    summary = {
        "status": "complete",
        "fixture_sha256": sha256_hex(fixture),
        "identities_sha256": sha256_hex(canonical_json(identities)),
        "role_calls": dict(sorted(counts.items())),
        "calls": calls,
    }
    write_new(output / "summary.json", canonical_json(summary))
    sink({key: value for key, value in summary.items() if key != "calls"})
    return summary


@contextlib.contextmanager
def private_diagnostics():
    """Suppress Python and native runtime output; only the explicit sink leaves."""
    sys.stdout.flush()
    sys.stderr.flush()
    saved = [os.dup(1), os.dup(2)]
    try:
        with tempfile.TemporaryFile() as diagnostics:
            os.dup2(diagnostics.fileno(), 1)
            os.dup2(diagnostics.fileno(), 2)
            try:
                yield
            finally:
                sys.stdout.flush()
                sys.stderr.flush()
    finally:
        for descriptor, original in zip((1, 2), saved, strict=True):
            os.dup2(original, descriptor)
            os.close(original)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise SmokeRefused("malformed_arguments")


def main(argv=None):
    with os.fdopen(os.dup(1), "w", buffering=1) as console:

        def sink(row):
            console.write(canonical_json(row).decode() + "\n")

        def ready():
            console.write("checkpoint: unload Gemma, load both judges; type ready\n")
            console.flush()
            return sys.stdin.readline().strip() == "ready"

        try:
            parser = Parser()
            for name in ("manifest", "models-root", "fixture-id", "limits", "run-id"):
                parser.add_argument("--" + name, required=True)
            args = parser.parse_args(argv)
            with private_diagnostics():
                smoke(
                    Path(__file__).resolve().parents[1],
                    args.manifest,
                    Path(args.models_root),
                    args.fixture_id,
                    args.limits,
                    args.run_id,
                    ready=ready,
                    sink=sink,
                )
            return 0
        except SmokeRefused as error:
            sink({"status": "refused", "reason": str(error)})
        except Exception:  # noqa: BLE001 - arbitrary runtime diagnostics must stay private
            sink({"status": "refused", "reason": "smoke_failed"})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `tests/contracts/test_stage11_fixture_smoke.py` with these tests first. All file/number literals here are invented test inputs, never real baseline/preregistration choices.

```python
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import stage11_fixture_smoke as smoke


def test_smoke_limits_are_documented():
    path = Path(__file__).resolve().parents[2] / "docs/data-dictionary.md"
    text = path.read_text()
    heading = "## Stage 11 fixture-smoke limits"
    assert text.count(heading) == 1
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    assert all(f"`{name}`" in section for name in smoke.Limits.model_fields)


def test_unknown_fixture_refuses_before_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(
        smoke, "committed", lambda *args: b'[[fixtures]]\nfixture_id="invented"\n'
    )
    called = []
    with pytest.raises(smoke.SmokeRefused, match="^fixture_not_allowlisted$"):
        smoke.smoke(
            tmp_path,
            "config/models/runtime.toml",
            tmp_path / "models",
            "not-allowlisted",
            "limits.json",
            "test",
            builder=lambda *a: called.append(1),
        )
    assert called == []
    assert not (tmp_path / "data").exists()


def test_changed_fixture_bytes_refuse_before_runtime(tmp_path, monkeypatch):
    path = tmp_path / "tests/fixtures/canonical/invented.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"changed fixture")
    manifest = b'[[fixtures]]\nfixture_id="invented"\n'

    def git_show(args, **kwargs):
        value = manifest if args[-1].endswith("manifest.toml") else b"HEAD fixture"
        return SimpleNamespace(returncode=0, stdout=value)

    manifest_path = tmp_path / "tests/fixtures/releases/manifest.toml"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_bytes(manifest)
    monkeypatch.setattr(smoke.subprocess, "run", git_show)
    called = []
    with pytest.raises(smoke.SmokeRefused, match="^fixture_not_committed$"):
        smoke.smoke(
            tmp_path,
            "config/models/runtime.toml",
            tmp_path / "models",
            "invented",
            "limits.json",
            "test",
            builder=lambda *a: called.append(1),
        )
    assert called == []


def test_panel_refuses_either_judge_matching_extractor_before_builder(
    tmp_path, monkeypatch
):
    model_cases = importlib.import_module(
        "apps.earnings-pipeline.tests.test_model_runtime"
    )
    root = tmp_path / "config/models/panel"
    root.mkdir(parents=True)
    manifest, _ = model_cases.layout(root, families=("gemma", "gemma", "other"))
    with pytest.raises(smoke.SmokeRefused, match="^judge_family_conflict$"):
        smoke.panel(tmp_path, manifest)


def test_measurement_never_emits_exception_wording():
    class Failing:
        identity = object()

        def count_tokens(self, request):
            return 7

        def complete(self, request):
            raise RuntimeError("INVENTED_SOURCE_SENTINEL")

    rows, printed = [], []
    wrapped = smoke.Measured(Failing(), "judge_a", rows, printed.append)
    with pytest.raises(RuntimeError):
        wrapped.complete(object())
    assert rows[0]["status"] == "failed"
    assert isinstance(rows[0]["elapsed_ms"], int)
    assert "INVENTED_SOURCE_SENTINEL" not in json.dumps(printed)


def test_main_closes_python_and_native_diagnostics(monkeypatch, capfd):
    def noisy(*args, **kwargs):
        import os

        print("INVENTED_SOURCE_SENTINEL")
        os.write(2, b"INVENTED_SOURCE_SENTINEL")
        raise RuntimeError("INVENTED_SOURCE_SENTINEL")

    monkeypatch.setattr(smoke, "smoke", noisy)
    options = [
        "--manifest",
        "a",
        "--models-root",
        "b",
        "--fixture-id",
        "c",
        "--limits",
        "d",
        "--run-id",
        "e",
    ]
    assert smoke.main(options) == 1
    captured = capfd.readouterr()
    assert "smoke_failed" in captured.out
    assert "INVENTED_SOURCE_SENTINEL" not in captured.out + captured.err


def invented_setup(tmp_path, monkeypatch):
    cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_workflow")
    pilot_cases = importlib.import_module(
        "apps.earnings-pipeline.tests.test_pilot_workflow"
    )
    config, _ = cases.seed_case(tmp_path, seed=False, review=True)
    contents = {
        "tests/fixtures/releases/manifest.toml": b'[[fixtures]]\nfixture_id="invented"\n',
        "tests/fixtures/canonical/invented.json": (
            tmp_path / config.sources[0].canonical.path
        ).read_bytes(),
        "prompts/extraction/pointer-1.md": (
            tmp_path / config.extraction_prompt.path
        ).read_bytes(),
        "prompts/coding/deductive-1.md": config.coding_policy.prompt_text.encode(),
        "prompts/support/judge-1.md": config.support_policy.prompt_text.encode(),
        "codebooks/djia-pilot/codebook-v0.toml": (
            tmp_path / config.codebook.path
        ).read_bytes(),
        "uv.lock": b"invented lock identity",
    }
    for name, data in contents.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    path = tmp_path / "config/models/runtime.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("invented manifest; panel checked separately")
    limits = smoke.Limits(
        extraction_policy=config.extraction_policy,
        extraction_ceilings=config.extraction_ceilings,
        coding_parameters=config.coding_policy.parameters,
        coding_ceilings=config.coding_ceilings,
        support_parameters=config.support_policy.parameters,
        support_ceilings=config.support_ceilings,
    )
    (tmp_path / "limits.json").write_text(limits.model_dump_json())
    monkeypatch.setattr(smoke, "committed", lambda repo, name: contents[name])
    monkeypatch.setattr(smoke, "panel", lambda *args: None)
    phases = []
    from earnings_themes.support.records import ScorerIdentity
    from earnings_themes.support.scorers import ScoreReply, ScriptedScorer

    workflow = pilot_cases.runtime(config, phases)
    # The alternative must have a distinct identity or its scorer calls hit the primary cache.
    fields = workflow.scorer.identity.model_dump(mode="json")
    fields["runtime"]["model_id"] = "invented-alternative"
    alternative_identity = ScorerIdentity.model_validate_json(json.dumps(fields))
    alternative = ScriptedScorer(
        lambda request: ScoreReply(
            score=0.25,
            reason=None,
            input_tokens=5,
            latency_ms=1,
            identity=alternative_identity,
            input_hash=request.input_hash,
        ),
        lambda request: 5,
        alternative_identity,
    )
    rt = SimpleNamespace(
        workflow=workflow,
        alternative_scorer=alternative,
        extractor_family=config.extractor_family,
    )
    return rt, phases


def test_real_library_smoke_on_invented_inputs(tmp_path, monkeypatch):
    rt, phases = invented_setup(tmp_path, monkeypatch)
    rows = []
    result = smoke.smoke(
        tmp_path,
        "config/models/runtime.toml",
        tmp_path / "models",
        "invented",
        "limits.json",
        "test",
        builder=lambda *args: rt,
        ready=lambda: phases.append("ready") or True,
        sink=rows.append,
    )
    assert result["status"] == "complete"
    assert set(result["role_calls"]) == {
        "extractor",
        "classifier",
        "judge_a",
        "judge_b",
        "minicheck",
        "deberta",
    }
    assert all(count > 0 for count in result["role_calls"].values())
    assert phases.index("extract") < phases.index("classify") < phases.index("ready")
    assert (tmp_path / "data/runs/stage11-fixture-smoke/test/summary.json").is_file()
    assert not (tmp_path / "data/runs/pilot").exists()
    assert "Invented expansion" not in json.dumps(rows)


def test_existing_run_refuses_before_runtime(tmp_path, monkeypatch):
    invented_setup(tmp_path, monkeypatch)
    (tmp_path / "data/runs/stage11-fixture-smoke/test").mkdir(parents=True)
    called = []
    with pytest.raises(smoke.SmokeRefused, match="^output_exists$"):
        smoke.smoke(
            tmp_path,
            "config/models/runtime.toml",
            tmp_path / "models",
            "invented",
            "limits.json",
            "test",
            builder=lambda *args: called.append(1),
        )
    assert called == []


def test_unconfirmed_operator_checkpoint_does_not_dispatch_support(
    tmp_path, monkeypatch
):
    rt, _ = invented_setup(tmp_path, monkeypatch)
    rows = []
    with pytest.raises(smoke.SmokeRefused, match="^support_not_ready$"):
        smoke.smoke(
            tmp_path,
            "config/models/runtime.toml",
            tmp_path / "models",
            "invented",
            "limits.json",
            "test",
            builder=lambda *args: rt,
            ready=lambda: False,
            sink=rows.append,
        )
    assert {row["role"] for row in rows} == {"extractor", "classifier"}
    assert not (tmp_path / "data/runs/stage11-fixture-smoke/test/summary.json").exists()


@pytest.mark.parametrize("empty_stage", ["extraction", "classification"])
def test_empty_stage_cannot_claim_an_all_role_smoke(tmp_path, monkeypatch, empty_stage):
    from dataclasses import replace

    from earnings_themes.coding.adapters import ScriptedClassifier
    from earnings_themes.extraction.adapters import ModelReply, ScriptedAdapter

    rt, _ = invented_setup(tmp_path, monkeypatch)
    if empty_stage == "extraction":
        adapter = ScriptedAdapter(
            lambda request: ModelReply(
                model="scripted",
                text='{"candidates":[]}',
            )
        )
        rt.workflow = replace(rt.workflow, extractor=adapter)
        reason = "extraction_incomplete_or_empty"
    else:
        adapter = ScriptedClassifier(
            lambda request: ModelReply(
                model=rt.workflow.classifier.identity.runtime.model_id,
                text='{"theme_ids":[],"attributes":{}}',
            ),
            lambda request: 5,
            rt.workflow.classifier.identity,
        )
        rt.workflow = replace(rt.workflow, classifier=adapter)
        reason = "classification_incomplete_or_empty"
    rows = []
    with pytest.raises(smoke.SmokeRefused, match="^" + reason + "$"):
        smoke.smoke(
            tmp_path,
            "config/models/runtime.toml",
            tmp_path / "models",
            "invented",
            "limits.json",
            "test",
            builder=lambda *args: rt,
            ready=lambda: True,
            sink=rows.append,
        )
    assert not any(
        row["role"] in {"minicheck", "deberta", "judge_a", "judge_b"} for row in rows
    )
    assert not (tmp_path / "data/runs/stage11-fixture-smoke/test/summary.json").exists()
```

Append this exact section to `docs/data-dictionary.md`, without changing other records:

```markdown
## Stage 11 fixture-smoke limits

`tools.stage11_fixture_smoke.Limits` is the explicit local JSON input for the
user-run Stage 11 fixture smoke. It is not a pilot preregistration or an approved
production configuration. Values are owner-supplied; no numeric limit is selected
by the schema. The user may reuse its six policy/ceiling fields in the later local
pilot-input constructor only after the smoke-derived baseline is approved.

| Field | Type | Meaning |
| --- | --- | --- |
| `extraction_policy` | `ExtractionPolicy` | Existing pointer traversal and extraction parameters. |
| `extraction_ceilings` | `Ceilings` | Explicit bounded fixture extraction requests/tokens. |
| `coding_parameters` | `Parameters` | Explicit classifier generation parameters. |
| `coding_ceilings` | `CodingCeilings` | Explicit classifier request/token ceilings. |
| `support_parameters` | `Parameters` | Explicit judge generation parameters. |
| `support_ceilings` | `SupportCeilings` | Explicit scorer/judge/token ceilings. |

The CLI pins a committed Stage 1 canonical fixture before runtime construction,
keeps raw caches and identity/measurement snapshots local under
`data/runs/stage11-fixture-smoke/<run_id>/`, suppresses native diagnostics and emits
only closed statuses, fixed role names, counts, timings, usage and hashes. A
complete smoke exercises extraction, classification, both judge presentations in
each family, and both scorers. Disagreement does not imply failure; incomplete
roles do. The smoke makes no assignment or pilot-quality claim.
```

The worker formats Python with the repository Ruff version during implementation. Do not claim native model/server fit from these tests. The local extractor exposes server usage but no local input counter; report that local count as unknown rather than fabricating it. Tokenizer/server count differences are descriptive here, not a selected tolerance.

### Appendix B: Metadata-only preregistration input constructor

Run in the user's terminal after O1–O5. The prompt accepts actual owner choices without putting any proposed numeric values in this plan. Required JSON keys are exactly `floor`, `menu`, `recall_floor`, `sampling_seed`, `extension_step`, `bootstrap_seed`, `resamples`, `max_undefined_share`, `undefined_gate`. `menu` contains objects with `candidate_id` and `grid`. Do not execute through a shell heredoc while also reading interactive stdin: use a temporary script file or `python -c` with this body. It is shown as Python to save as `data/runs/pilot/prepare-preregistration.py` **by the user**; agents never create/read that local file.

```python
import json
from pathlib import Path
from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
from earnings_pipeline.stage6 import Layout, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH, load_pinned
from earnings_themes import tomlfile
from earnings_themes.evaluation import freeze_preregistration
from earnings_themes.evaluation.preregistration import REQUIRED_GATES
from earnings_themes.gold import CodebookRef

try:
    repo = Path.cwd()
    layout = Layout(repo, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH)
    pinned = load_pinned(layout)
    split, book = pinned_split(layout, pinned), pinned_codebook(layout)
    choices = json.loads(input("Owner-approved preregistration choices JSON: "))
    required = {"floor", "menu", "recall_floor", "sampling_seed", "extension_step",
                "bootstrap_seed", "resamples", "max_undefined_share", "undefined_gate"}
    if set(choices) != required or any(set(c) != {"candidate_id", "grid"} for c in choices["menu"]):
        raise ValueError("choices")
    fields = {
        "preregistration_version": 1,
        "pin": pinned.pin.model_dump(mode="json"), "split_hash": split.content_hash,
        "codebook": CodebookRef(codebook_id=book.codebook_id, codebook_version=book.codebook_version,
                                content_hash=book.content_hash).model_dump(mode="json"),
        "floor": {"statistic": "cohen_kappa", "reported": "gwet_ac1",
                  "population": "family_verdict_vs_joint_label", "bound": "event_bootstrap_lower",
                  "floor": choices["floor"], "consequence": "reported_only"},
        "menu": [{"candidate_id": c["candidate_id"], "grid": c["grid"], "rule": "scorer_cutoff",
                  "signal": "minicheck_joint", "signals": 1} for c in choices["menu"]],
        "selection": {"recall_floor": choices["recall_floor"], "objective": "max_train_precision",
                      "tie_break": "fewer_signals_then_lower_cutoff"},
        "sampling": {"seed": choices["sampling_seed"], "pool": "assessed_and_flagged",
                     "train_size": 70, "train_cap": 5, "dev_size": 24, "dev_cap": 3,
                     "minimum_usable": 50, "extension_step": choices["extension_step"]},
        "bootstrap": {"seed": choices["bootstrap_seed"], "resamples": choices["resamples"],
                      "level": 0.9, "max_undefined_share": choices["max_undefined_share"]},
        "gates": {"rule": "dev-lower-bound/1", "gated": sorted(REQUIRED_GATES),
                  "undefined_gate": choices["undefined_gate"]},
    }
    record = freeze_preregistration(fields)
    target = repo / "data/runs/pilot/preregistration-fields.toml"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(tomlfile.dumps(fields))
    print("validated_preregistration", record.content_hash)
except Exception:
    raise SystemExit("Refused: preregistration_fields: malformed_record") from None
```

Run the saved user file with the locked/offline/no-sync workspace Python, review safe field summaries, then use Task 2's literal freeze/alone-commit command. `open("x")` intentionally refuses an existing local choice file; edit only the pre-output working input deliberately, never overwrite a frozen protocol.

### Appendix C: User-only immutable input preparation after O6

`WorkflowConfig` confines manifests, prompts, codebook and sources to a **single nonempty input_root**; `"."` and the empty string refuse. Therefore the constructor copies exact saved bytes under `data/runs/pilot/inputs/<bundle_id>/`, preserving original IDs/hashes and the original raw `ArtifactRef`. Event/pilot manifest copies remain siblings with their original filenames. This is a local snapshot, not a new acquisition, canonicalization, gold artifact or redistribution permission.

Before O6 the owner may prepare the metadata input JSON only. Its required fields are defined by `Owner` below: unique bundle ID; hash-pinned successful B1 `identities.json`; existing Stage 5 raw-store root; exactly 28 document choice entries (source-supported publisher and event time or null, explicit local retention/no-export permissions); train/dev workflow/stage IDs; owner-approved baseline `Rules`; and existing mask policy plus `include_family_view=false`. No model/data field has an invented default. Identity snapshot hash must match the successful smoke's printed `identities_sha256` and ADR 0006. It is local and never pasted to an agent.

The owner saves this complete body as local `data/runs/pilot/prepare-inputs.py` and runs it after O6. It does not build/load a model; it consumes the hash-pinned B1 identity snapshot and uses replay-only validators, which dispatch nothing. Source bytes are not opened until `visibility` returns. The saved script and owner JSON are user-only, not new committed tools.

```python
import json
import subprocess
from pathlib import Path
from typing import Literal

from earnings_core import canonical_json, digest, sha256_hex
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import DocumentState, ProcessingTransition, current_states
from earnings_ingestion.fetch.client import ProcessLock
from earnings_ingestion.fetch.store import ArtifactStore, write_new
from earnings_ingestion.sec.urls import archive_url
from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
from earnings_pipeline.pilot_inputs import open_pilot, require_committed
from earnings_pipeline.pilot_records import PilotSettings
from earnings_pipeline.stage6 import (
    CODEBOOK_FILE, EVENT_RUNS, PILOT_V1, PILOT_V1_HASH, UNIVERSE_V1, Layout,
    derive_split, documents, file_stem, independent_path, load_pinned, read_ledger,
)
from earnings_pipeline.theme_config import FileSelection, WorkflowConfig, confined_path, validate_paths
from earnings_pipeline.theme_workflow import load_workflow_inputs, replay_runtime
from earnings_themes.analysis import AnalysisPolicy, DocumentMetadata
from earnings_themes.annotation import check_countable
from earnings_themes.coding.records import CodingCeilings, CodingPolicy
from earnings_themes.extraction.records import AdapterIdentity, Ceilings, ExtractionPolicy, Parameters
from earnings_themes.gold import load_gold
from earnings_themes.independent import ledger_check
from earnings_themes.records import IdPart, NonBlank, Part
from earnings_themes.split import Partition
from earnings_themes.support.records import JudgeIdentity, ScorerIdentity, SupportCeilings, SupportPolicy
from pydantic import AwareDatetime
from tools.stage11_fixture_smoke import Limits, panel


class Ids(Part):
    run_id: IdPart
    extraction_run_id: IdPart
    coding_run_id: IdPart
    support_run_id: IdPart


class DocumentChoices(Part):
    publisher: NonBlank
    event_at: AwareDatetime | None
    access_status: Literal["available"]
    retain_text: Literal[True]
    export_text: Literal[False]
    retain_raw: Literal[True]
    export_raw: Literal[False]
    retain_capture: Literal[False]


class AnalysisChoices(Part):
    mask_policy_id: NonBlank
    mask_policy_version: NonBlank
    include_family_view: Literal[False]


class Owner(Part):
    bundle_id: IdPart
    identities: FileSelection
    raw_store_root: str
    documents: dict[str, DocumentChoices]
    ids: dict[str, Ids]
    rules: Limits
    analysis: AnalysisChoices


class Identities(Part):
    runtime_manifest: FileSelection
    extractor_family: IdPart
    extraction_identity: AdapterIdentity
    classifier_identity: JudgeIdentity
    scorer_identity: ScorerIdentity
    judge_identities: tuple[JudgeIdentity, JudgeIdentity]
    alternative_scorer: ScorerIdentity


def need(condition):
    if not condition:
        raise ValueError("binding_mismatch")


def ref(repo, path):
    return FileSelection(path=path.relative_to(repo).as_posix(), sha256=sha256_hex(path.read_bytes()))


def selected(repo, selection, root):
    path = confined_path(repo, selection.path, root)
    data = path.read_bytes()
    need(sha256_hex(data) == selection.sha256)
    return path, data


def committed_bytes(repo, path):
    require_committed(repo, path, "input")
    return path.read_bytes()


def put(repo, relative, data):
    path = confined_path(repo, relative, "data/runs/pilot")
    write_new(path, data)
    return ref(repo, path)


def visibility(layout):
    pinned = load_pinned(layout)
    split = pinned_split(layout, pinned)
    need(split == derive_split(layout, pinned))
    need(len(split.events_in(Partition.TRAIN)) == 20 and len(split.events_in(Partition.DEV)) == 8)
    book, doc_ids = pinned_codebook(layout), documents(layout, pinned)
    events = tuple(sorted((*split.events_in(Partition.TRAIN), *split.events_in(Partition.DEV))))
    for event in events:
        path = pinned.gold_dir / f"{file_stem(event)}.toml"
        require_committed(layout.repo, path, "gold")
        gold = load_gold(path)
        need(not check_countable(gold, event_id=event, pin=pinned.pin, split=split,
                                 codebook=book, doc_id=doc_ids[event]))
    ledger_path = pinned.evaluation / "independent-pass.toml"
    require_committed(layout.repo, ledger_path, "ledger")
    ledger = read_ledger(pinned)
    for event in split.events_in(Partition.DEV):
        path = confined_path(layout.repo, independent_path(layout, event).relative_to(layout.repo).as_posix(),
                             "data/runs/gold/independent")
        need(ledger_check(ledger, event, path.read_bytes() if path.is_file() else None) is None)
    require_committed(layout.repo, pinned.evaluation / "preregistration-v1.toml", "preregistration")
    return pinned, split, events


def prepare(repo, owner_path):
    repo = repo.resolve()
    owner = Owner.model_validate_json(confined_path(repo, owner_path, "data/runs/pilot").read_bytes())
    layout = Layout(repo, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH)
    states_rel = (EVENT_RUNS / "states").as_posix()
    states_dir = confined_path(repo, states_rel, "data/runs/events")
    lock_path = confined_path(repo, states_rel + "/.acquire.lock", "data/runs/events")
    for path in states_dir.glob("*.parquet"):
        confined_path(repo, path.relative_to(repo).as_posix(), states_rel)
    with ProcessLock(lock_path):
        pinned, split, all_events = visibility(layout)
        need(set(owner.documents) == set(all_events) and set(owner.ids) == {"train", "dev"})
        history = read_runs(states_dir)
        need(not any(isinstance(t, ProcessingTransition) and t.pilot_hash == pinned.pin.pilot_hash
                     for t in history))
        latest = current_states(history, pinned.pin.pilot_hash)
        inventory = tuple(ref(repo, path) for path in sorted(states_dir.glob("*.parquet")))
        need(bool(inventory))
        _, identity_bytes = selected(repo, owner.identities, "data/runs/stage11-fixture-smoke")
        identities = Identities.model_validate_json(identity_bytes)
        runtime_path, _ = selected(repo, identities.runtime_manifest, "config/models")
        require_committed(repo, runtime_path, "runtime_manifest")
        panel(repo, runtime_path)
        need(identities.alternative_scorer.kind == "deberta")
        need(identities.scorer_identity.kind == "minicheck")
        need(len({j.family for j in identities.judge_identities}) == 2)
        need(all(j.family != identities.extractor_family for j in identities.judge_identities))
        base = f"data/runs/pilot/inputs/{owner.bundle_id}"
        universe_path, pilot_path = repo / layout.universe, repo / layout.pilot
        events_path = pilot_path.parent / f"events-v{pinned.pin.events_version}.json"
        universe = put(repo, base + "/manifests/" + universe_path.name, committed_bytes(repo, universe_path))
        events = put(repo, base + "/manifests/" + events_path.name, committed_bytes(repo, events_path))
        pilot = put(repo, base + "/manifests/" + pilot_path.name, committed_bytes(repo, pilot_path))
        codebook = put(repo, base + "/codebooks/" + CODEBOOK_FILE.name, committed_bytes(repo, repo / CODEBOOK_FILE))
        prompt_selections, texts = {}, {}
        for stage, original in (("extraction", "prompts/extraction/pointer-1.md"),
                                ("coding", "prompts/coding/deductive-1.md"),
                                ("support", "prompts/support/judge-1.md")):
            data = committed_bytes(repo, repo / original)
            prompt_selections[stage] = put(repo, base + "/" + original, data)
            texts[stage] = data.decode()
        lockfile = ref(repo, repo / "uv.lock")
        committed_bytes(repo, repo / "uv.lock")
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                                  capture_output=True, text=True).stdout.strip()
        software = {"lock_hash": lockfile.sha256, "git_revision": revision}
        raw_root = confined_path(repo, owner.raw_store_root, "data/raw")
        store = ArtifactStore(raw_root, repo)
        event_rows = {event.event_id: event for event in pinned.events.rows}
        sources = {}
        for event in all_events:
            state, row = latest[event + ":release"], event_rows[event]
            need(state.to_state is DocumentState.PARSED)
            canonical_path = confined_path(
                repo, (EVENT_RUNS / "canonical" / f"{state.doc_id}.json").as_posix(),
                "data/runs/events/canonical",
            )
            canonical_bytes = canonical_path.read_bytes()
            canonical = from_fixture_json(canonical_bytes.decode())
            doc, manifest = canonical.document, canonical.manifest
            payload = json.loads(canonical_bytes)
            need(doc.doc_id == state.doc_id and manifest.raw_sha256 == state.artifact_sha256)
            need(doc.source_document_id == f"{state.accession}_{state.exhibit}")
            retrieval_dir = confined_path(
                repo, (raw_root / SEC_SOURCE_ID / "retrievals" / state.artifact_sha256)
                .relative_to(repo).as_posix(), owner.raw_store_root,
            )
            for path in (*retrieval_dir.glob("*.json"),
                         *(raw_root / SEC_SOURCE_ID).glob(state.artifact_sha256 + ".*")):
                confined_path(repo, path.relative_to(repo).as_posix(), owner.raw_store_root)
            saved = store.get(SEC_SOURCE_ID, state.artifact_sha256,
                              rights_status=SEC_RIGHTS.rights_status, rights_basis=SEC_RIGHTS.rights_basis)
            url = archive_url(row.cik, state.accession, state.exhibit)
            matches = [r for r in saved.retrievals if r.retrieved_at == state.retrieved_at
                       and r.request_url == url and r.final_url == url]
            need(len(matches) == 1)
            retrieval = matches[0]
            need(retrieval.media_type == saved.ref.media_type and len(saved.body) == manifest.raw_bytes)
            need((manifest.mask_policy_id, manifest.mask_policy_version)
                 == (owner.analysis.mask_policy_id, owner.analysis.mask_policy_version))
            choices = owner.documents[event]
            metadata = DocumentMetadata(
                doc_id=doc.doc_id, event_id=event, entity_id=row.issuer_id, cik=row.cik,
                publisher=choices.publisher, source_url=url, source_document_id=doc.source_document_id,
                raw_artifact=saved.ref, raw_hash=state.artifact_sha256, canonical_hash=doc.canonical_hash,
                canonicalization_version=doc.canonicalization_version,
                parser_version=f"lxml/{manifest.lxml_version};{manifest.components['walker']}",
                canonical_manifest_hash=digest(payload["manifest"]),
                mask_policy_id=manifest.mask_policy_id, mask_policy_version=manifest.mask_policy_version,
                mask_manifest_hash=digest({"doc_id": doc.doc_id, "canonical_hash": doc.canonical_hash,
                                          "mask_policy_id": manifest.mask_policy_id,
                                          "mask_policy_version": manifest.mask_policy_version,
                                          "masks": payload["masks"]}),
                filing_at=row.filing_acceptance_time, published_at=row.first_publication_time,
                event_at=choices.event_at, retrieved_at=retrieval.retrieved_at, period_end=row.period_end,
                fiscal_year=row.reported_fiscal_year,
                fiscal_quarter={"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}.get(row.reported_fiscal_quarter),
                rights_status=SEC_RIGHTS.rights_status, rights_basis=SEC_RIGHTS.rights_basis,
                access_status=choices.access_status, retain_text=choices.retain_text,
                export_text=choices.export_text, retain_raw=choices.retain_raw,
                export_raw=choices.export_raw, retain_capture=choices.retain_capture,
            )
            folder = base + "/sources/" + file_stem(event)
            sources[event] = {
                "event_id": event, "doc_id": doc.doc_id,
                "canonical": put(repo, folder + "/canonical.json", canonical_bytes).model_dump(mode="json"),
                "metadata": put(repo, folder + "/metadata.json", canonical_json(metadata.model_dump(mode="json"))).model_dump(mode="json"),
                "raw": put(repo, folder + "/raw.bin", saved.body).model_dump(mode="json"),
            }
        configs = {}
        for part in (Partition.TRAIN, Partition.DEV):
            label = part.value
            event_ids = tuple(sorted(split.events_in(part)))
            cache = f"data/runs/pilot/caches/{owner.bundle_id}/{label}"
            fields = dict(
                owner.ids[label].model_dump(mode="json"), scope="research", mode="replay", fixture_started_at=None,
                input_root=base, universe=universe.model_dump(mode="json"), universe_hash=pinned.pin.universe_operative_hash,
                events=events.model_dump(mode="json"), event_hash=pinned.pin.events_hash,
                pilot=pilot.model_dump(mode="json"), pilot_hash=pinned.pin.pilot_hash,
                selected_event_ids=event_ids, states_dir=states_rel,
                acquisition_files=[r.model_dump(mode="json") for r in inventory], sources=[sources[e] for e in event_ids],
                codebook=codebook.model_dump(mode="json"),
                extraction_prompt=prompt_selections["extraction"].model_dump(mode="json"),
                coding_prompt=prompt_selections["coding"].model_dump(mode="json"),
                support_prompt=prompt_selections["support"].model_dump(mode="json"),
                extraction_policy=owner.rules.extraction_policy.model_dump(mode="json"),
                extraction_ceilings=owner.rules.extraction_ceilings.model_dump(mode="json"),
                extraction_identity=identities.extraction_identity.model_dump(mode="json"),
                extractor_family=identities.extractor_family,
                coding_policy=CodingPolicy(prompt_text=texts["coding"], prompt_hash=prompt_selections["coding"].sha256,
                                           parameters=owner.rules.coding_parameters).model_dump(mode="json"),
                coding_ceilings=owner.rules.coding_ceilings.model_dump(mode="json"),
                classifier_identity=identities.classifier_identity.model_dump(mode="json"),
                support_policy=SupportPolicy(support_version="semantic-support/1", prompt_text=texts["support"],
                                             prompt_hash=prompt_selections["support"].sha256,
                                             parameters=owner.rules.support_parameters).model_dump(mode="json"),
                support_ceilings=owner.rules.support_ceilings.model_dump(mode="json"),
                scorer_identity=identities.scorer_identity.model_dump(mode="json"),
                judge_identities=[j.model_dump(mode="json") for j in identities.judge_identities],
                extraction_cache=cache + "/extraction", coding_cache=cache + "/coding", support_cache=cache + "/support",
                stored_extraction=None, stored_support=None, stored_coding=None, stored_analysis=None,
                assignment_policy=None, policy_reference=None,
                analysis_policy=AnalysisPolicy(population_id=pinned.events.definition.corpus_id,
                                               event_ids=event_ids, population_hash=pinned.pin.pilot_hash,
                                               scope="research", **owner.analysis.model_dump()).model_dump(mode="json"),
                families=None, copies=[], no_theme=[], audience="local",
                output_dir=f"data/runs/pilot/workflows/{owner.bundle_id}/{label}",
                capture=False, capture_policy=None, installed_binary_reference=None,
                software=software, lockfile=lockfile.model_dump(mode="json"),
            )
            config = WorkflowConfig.model_validate_json(canonical_json(fields))
            validate_paths(config, repo=repo)
            load_workflow_inputs(config, replay_runtime(config))
            configs[label] = put(repo, f"data/runs/pilot/config/{label}.json", canonical_json(config.model_dump(mode="json")))
        settings = PilotSettings(train=configs["train"], dev=configs["dev"],
                                 runtime_manifest=identities.runtime_manifest,
                                 alternative_scorer=identities.alternative_scorer)
        output = put(repo, "data/runs/pilot/config/settings.json", canonical_json(settings.model_dump(mode="json")))
        for part in (Partition.TRAIN, Partition.DEV):
            open_pilot(layout, repo / output.path, part)
        print(canonical_json({"status": "prepared", "train_events": 20, "dev_events": 8,
                              "settings_sha256": output.sha256}).decode())


try:
    owner_path = input("Repository-relative local owner JSON path: ")
    prepare(Path.cwd(), owner_path)
except BaseException:
    raise SystemExit("Refused: input_preparation: preparation_failed") from None
```

The user invokes this exact command from the repository root. `python -c` keeps the repository root importable for `tools` and leaves stdin available for the owner prompt; no `sys.path` mutation is added:

```bash
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --locked --offline --no-sync --all-packages python -c '
from pathlib import Path
path = Path("data/runs/pilot/prepare-inputs.py")
exec(compile(path.read_bytes(), str(path), "exec"))
'
```

Record the actual invocation and closed output.

The owner map is a source/configuration selection, not a request to infer missing disclosure values. An absent or ambiguous exact historical retrieval refuses; the user supplies a reviewed explicit source-selection disposition, rather than changing to `latest`. `parser_version` above is explicitly derived from the saved lxml version and walker component; it is not a newly asserted parser release. All generated metadata is checked against existing consuming gates. A partial preparation may leave immutable local copies; `write_new` reuses identical bytes and refuses differences. Do not delete them to suppress changed inputs. Obtain an explicit retention/config-path disposition if a repair needs a new bundle, then review the adjusted literal settings paths before any pass.

### Appendix D: Exact train/dev-only user launcher for gold validation or GS5

Save this Python body locally outside Git and run it in the user's terminal. It derives literal IDs from the rechecked split; it never passes the command's default all-gold selection. The first prompt is `validate` at O6 and `recount` at B7. Output remains governed by the existing guarded commands.

```python
from pathlib import Path
from earnings_pipeline.cli import app
from earnings_pipeline.codebook_cli import pinned_split
from earnings_pipeline.stage6 import Layout, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH, load_pinned
from earnings_themes.split import Partition

try:
    operation = input("User gate (validate or recount): ")
    if operation not in {"validate", "recount"}:
        raise ValueError("operation")
    layout = Layout(Path.cwd(), UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH)
    pinned = load_pinned(layout)
    split = pinned_split(layout, pinned)
    events = sorted((*split.events_in(Partition.TRAIN), *split.events_in(Partition.DEV)))
    if len(events) != 28 or len(set(events)) != 28:
        raise ValueError("inventory")
except BaseException:
    raise SystemExit("Refused: visibility: malformed_record") from None

app(args=["gold", "validate", *events] if operation == "validate"
    else ["pilot", "recount", *events])
```

Do not run this as an agent: validation/recount inspect local canonical text and drafts. GS19 ordering remains the owner's separate attestation backed by commit history.

### Appendix E: Rerun actual V6 gates and the reject-everything regression

This user-run metadata-only body can be executed with a shell heredoc; it takes no interactive input and loads no source/model. It uses the actual committed report and generated gate file, then a clearly invented rejected-output record. Gate results are lists, not metric-keyed dictionaries.

```bash
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --locked --offline --no-sync --all-packages python - <<'PY'
from pathlib import Path
from earnings_core import canonical_json
from earnings_pipeline.pilot_inputs import require_committed
from earnings_pipeline.pilot_records import read_json
from earnings_themes.evaluation import PilotReport, evaluate_gates, load_gates
from earnings_themes.evaluation.records import Figure, Metric, PartitionReport
from earnings_themes.split import Partition

try:
    repo = Path.cwd()
    root = repo / "evaluation/djia-2024q3-2026q2/pilot-v1"
    require_committed(repo, root / "report-v1.json", "report")
    report = read_json(root / "report-v1.json", PilotReport, "report")
    gates = load_gates(root / "gates-v1.toml")
    if gates.report_hash != report.content_hash or gates.preregistration_hash != report.preregistration_hash:
        raise ValueError("binding")
    baseline = evaluate_gates(gates, report.partition(Partition.DEV))
    rejecting = PartitionReport(
        partition=Partition.DEV, in_sample=False, events=("invented-reject-everything",),
        figures=(Figure(metric=Metric.GOLD_EVIDENCE_RECALL, point=0.0, interval=None,
                        reason="invented_reject_everything"),
                 Figure(metric=Metric.SUPPORT_PRECISION, point=None, interval=None,
                        reason="invented_reject_everything")),
    )
    rejected = evaluate_gates(gates, rejecting)
    if rejected.passed or not any(row.reason == "zero_gold_evidence_recall" and not row.passed
                                 for row in rejected.results):
        raise ValueError("reject_all_passed")
    print(canonical_json({"baseline": baseline.model_dump(mode="json"),
                          "invented_reject_everything": rejected.model_dump(mode="json"),
                          "gates_hash": gates.content_hash}).decode())
except Exception:
    raise SystemExit("Refused: gate_regression: malformed_record") from None
PY
```

### Appendix F: Safe artifact figures and local usable-label count

The shipped pass/run commands print status/event counts; `calibrate` prints hash/outcome; `report` prints hash/partition/independent counts. They do **not** print all figures. After generation, the user runs this typed metadata formatter for the selected B5 or B8 artifact, returning only numeric/ID/rule/hash output. Committed artifacts are text-free by the approved contract; this does not authorize reading arbitrary JSON or local caches.

Save as a local user script (interactive stdin is required):

```python
from pathlib import Path
from earnings_core import canonical_json
from earnings_pipeline.pilot_records import read_calibration, read_json
from earnings_themes.evaluation import PilotReport

try:
    stage = input("Figures (calibration or report): ")
    root = Path("evaluation/djia-2024q3-2026q2/pilot-v1")
    if stage == "calibration":
        record = read_calibration(root / "calibration-v1.json")
    elif stage == "report":
        record = read_json(root / "report-v1.json", PilotReport, "report")
    else:
        raise ValueError("stage")
    print(canonical_json(record.model_dump(mode="json")).decode())
except Exception:
    raise SystemExit("Refused: figures: malformed_record") from None
```

For the **pre-promotion** usable-label check in B4/B6, user runs this local reader after deliberately completing every answer. This reports no label view, score or judge answer:

```python
from pathlib import Path
from earnings_themes.evaluation import joint_label, load_labels
from earnings_themes.split import Partition

try:
    partition = Partition(input("Completed label partition (train or dev): "))
    if partition not in (Partition.TRAIN, Partition.DEV):
        raise ValueError("partition")
    labels = load_labels(Path("data/runs/pilot/labels") / f"{partition.value}-working.toml")
    own = labels.of(partition)
    usable = sum(joint_label(label) is not None for label in own)
    print("partition", partition.value, "labels", len(own), "usable_joint", usable,
          "excluded_joint", len(own) - usable)
except Exception:
    raise SystemExit("Refused: labels: malformed_record") from None
```

The count cannot establish deliberate human completion. That remains an explicit owner action before `labels check` and commit. After commit, an uncertain answer can only remain uncertain; a preregistered extension adds targets rather than edits answers.

For B8's observed event distributions and Stage 12's **train-only** per-theme handoff, the user runs this additional exact body. It reads protected baseline data through current gates, so an agent must never execute it. It emits IDs and figures only, and changes no model output, scoring rule, calibration, gate or report schema. The per-event points are descriptive; uncertainty for the partition remains the original event-clustered interval. Per-theme exact F1 intervals resample the same partition events under the same preregistered bootstrap, with the existing tie convention.

```bash
UV_CACHE_DIR=/private/tmp/earnings-plan21-uv uv run --locked --offline --no-sync --all-packages python - <<'PY'
from pathlib import Path
from earnings_core import canonical_json
from earnings_pipeline.pilot_commands import safe
from earnings_pipeline.pilot_inputs import open_pilot
from earnings_pipeline.pilot_labels import committed_labels
from earnings_pipeline.pilot_reporting import labelled_targets, load_run, observations
from earnings_pipeline.stage6 import Layout, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH
from earnings_themes.evaluation import estimate, event_cells, partition_report
from earnings_themes.evaluation.scores import Tally, f1, theme_tallies, total
from earnings_themes.split import Partition

@safe
def figures():
    layout = Layout(Path.cwd(), UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH)
    for part in (Partition.TRAIN, Partition.DEV):
        intake = open_pilot(layout, Path("data/runs/pilot/config/settings.json"), part)
        run = load_run(intake, intake.local / part.value / "run/run-record.json")
        labels = committed_labels(intake)
        if labels is None:
            raise ValueError("missing_labels")
        observed = observations(intake, run)
        targets = labelled_targets(intake, run, labels)
        per_event = {}
        for observation in observed:
            predicted = {assignment.theme_id for assignment in observation.accepted}
            cells = event_cells(observation.gold, observation.index, predicted)
            per_event[observation.event_id] = theme_tallies(cells, predicted)
            points = partition_report(
                (observation,), tuple(t for t in targets if t.event_id == observation.event_id),
                intake.codebook, intake.preregistration.bootstrap, partition=part,
            )
            print(canonical_json({
                "partition": part.value, "event_id": observation.event_id,
                "feasibility_only": True, "in_sample": part is Partition.TRAIN,
                "figures": [{"metric": fig.metric.value, "qualifier": fig.qualifier,
                             "point": fig.point, "counts": fig.counts} for fig in points.figures],
            }).decode())
        for theme in intake.codebook.themes:
            measure = estimate(
                per_event, lambda drawn, key=theme.theme_id:
                f1(total(event.get(key, Tally()) for event in drawn)),
                intake.preregistration.bootstrap,
            )
            counts = total(event.get(theme.theme_id, Tally()) for event in per_event.values())
            print(canonical_json({
                "partition": part.value, "theme_id": theme.theme_id, "metric": "exact_theme_f1",
                "feasibility_only": True, "in_sample": part is Partition.TRAIN,
                "tp": counts.tp, "fp": counts.fp, "fn": counts.fn,
                "point": measure.point, "interval": measure.interval.model_dump(mode="json"),
            }).decode())

figures()
PY
```

Do not mistake these diagnostic single-event points for newly calibrated quality gates or population estimates. A theme with no gold support/prediction remains undefined and counted. Preserve the numeric output provenance/code SHA in the verification record; only the train rows feed Stage 12 discovery.

## Planning verification and review handoff

### Execution checkpoint — 2026-10-13

The initial checkout was `main` at the exact Base SHA, with only this untracked plan. Owner approval/status was recorded and this plan alone committed on `plan21-approved-plan` as `95f0d206c53e355cbb4bb419d32d828ab53484f8`. The fresh engineering worktree `.claude/worktrees/plan21-engineering` contains that approval commit and uses branch `plan21-engineering`. Existing dependencies were reused without installation, sync, lockfile change or download.

Task 1 steps 1–2 used a fresh implementer and two-stage task review. Expected missing-helper RED gave one collection error. The exact supplied helper then gave 10 passed/1 failed: native diagnostics were suppressed but Python's replacement capture stream bypassed descriptor redirection. D21-5 authorizes the diagnosed correction and supplemental judge-before-builder test. The unchanged privacy test passed; a controlled ordering mutation gave two expected failures, then correct ordering was restored. Final named checks: helper **13 passed**; dictionary **383 passed, 1 skipped**; scoped Ruff lint/format and whitespace checks clean. Scoped re-review returned **spec PASS and quality PASS** with no new important defect. The helper/test/dictionary alone were committed as `fa3240455e2183868a6f31183e213cd189c33a63`, then made available by fast-forwarding the approval branch in the user's main checkout. The `main` branch itself remains at the merged Plan A baseline.

Before any native smoke, O1 must establish the fixed Gemma extractor/classifier and actual non-Gemma judge metadata; O2 must explicitly approve every materialized generation parameter/default and a non-null structure-aware window budget. Schema acceptance alone supplies neither approval. The owner requested a judge recommendation; candidate recommendations are not selections or O1/O2 evidence. No model/tokenizer/scorer loaded, native smoke or B1–B8 operation ran, protected data opened/copied, or root/wording/live/browser gate executed. Task 1 steps 3–5 and Tasks 2–9 remain incomplete; Stage 11 is not completed or retired. Local progress/review artifacts remain in this worktree's plan-specific `.sdd` directory.

Only this Markdown plan is intended to change in the planning session. Static syntax/interface review and document checks do not establish that the proposed helper/tests/scripts pass; execution must perform the RED/GREEN cycle, user smoke, source-input validation and B1–B8 evidence gates. No planning result is a pilot metric, native fit result or selected numeric preregistration.

Planning observations on 2026-10-13:

- HEAD was the exact requested merged base, with a clean initial checkout. The writing-plans entry check allocated ID 21 with no collision; its first cache-permission refusal was resolved using a writable isolated uv cache, without an escalation or dependency change.
- Read root instructions, README/member/workspace configuration, source notes, approved stage spec, retired Plan A execution/consuming handoff, Stage 11/downstream roadmap requirements, relevant backlog entries, and owning application/evaluation source/tests. No nearer AGENTS.md or CI configuration was found. Read-only parallel audits covered commands/schemas, handoff traps and later-stage/backlog scope.
- Root's own spec-coverage, placeholder and interface self-review is represented by the task coverage table and the exact appendices. It corrected previsibility source preparation, append-only uncertain labels, strict TOML parsing, test setup, ordinary replay processing-state semantics and smoke-limit documentation. No unresolved owner choice was converted to a numeric setting or scoring change.
- Static parsing succeeded for **7 Python blocks and 5 shell heredoc Python bodies**. A source-AST check resolved all referenced existing repository import names without importing application code. The two proposed helper/test bodies passed Ruff lint and format checks via stdin after formatting inside this Markdown only. These checks execute no proposed Python body.
- The placeholder scan found no unfinished-content markers. Whitespace/diff checks had no diagnostics. The plan contains **33 unchecked steps and zero checked steps**. Application/default/live/wording/browser tests, new helper tests, native smoke, input preparation, pilot steps and model/card acquisition checks were not run.
- The only workspace change is this plan. Shared spec, roadmap Stage 11 checkbox, deferred ledger, source notes, application code, model configs and research artifacts remain unchanged. Nothing has been committed in this planning session.

Owner review status updated 2026-10-13: approved for execution by D21-4. The planning observations above remain historical evidence. Execute with subagent-driven engineering for Task 1 and source review, with the controller coordinating each user-run checkpoint in order. Owner gates O1–O7 remain required; do not request plan approval again.
