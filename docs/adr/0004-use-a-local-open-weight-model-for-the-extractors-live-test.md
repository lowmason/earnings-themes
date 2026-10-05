# 0004. Use a local open-weight model for the extractor's live test

- **Status:** Accepted
- **Date:** 2026-10-05
- **Deciders:** Lowell Mason
- **Blast radius:** the live test of Stage 7's extractor
  (`packages/earnings-themes/tests/test_extraction_live.py`) and its configuration,
  `config/models/local-model.toml`. No default test, committed record, or later
  stage's choice depends on it.

## Context

What was known on 2026-10-04, at Stage 7's plan B gates
(`specs/evidence-selection-and-verification.md`, §Gates, plan B;
`specs/plans/12-evidence-selection-and-verification-plan-b.md`, Completion):

- **The question.** The extractor's live test needs one open-weight model, served on
  this machine through an OpenAI-compatible runtime with JSON-schema output (ES15,
  ES19). R14.1 limits the required path to open-weight, self-hosted models. R14.2's
  $100 budget is for the optional hosted ablation only, so no billable call is made.
- **The machine.** 36 GB of memory, which holds the weights, the runtime, and a
  window's context.
- **The candidates.** Each model card was read on 2026-10-04. Each model is served by
  llama.cpp's `llama-server`, whose source reads a strict `json_schema`
  `response_format` from `response_format.json_schema.schema`
  (`tools/server/server-common.cpp`):
  - **Gemma 4 31B-it**, https://huggingface.co/google/gemma-4-31B-it: "Apache 2.0";
    dense, with 30.7B parameters; the QAT Q4_0 GGUF
    (`google/gemma-4-31B-it-qat-q4_0-gguf`), one file of 17.7 GB. Thinking is off
    by default.
  - **Gemma 4 26B-A4B-it**, https://huggingface.co/google/gemma-4-26B-A4B-it:
    "Apache 2.0"; a mixture of experts, with 25.2B parameters and 3.8B active; the
    QAT Q4_0 GGUF, 14.4 GB. Thinking is off by default.
  - **Qwen3.8-27B**, https://huggingface.co/Qwen/Qwen3.8-27B: "Apache License
    Version 2.0"; dense, with 27B parameters and a vision encoder; the Q4_K_M GGUF
    (`ggml-org/Qwen3.8-27B-GGUF`), 19 GB. Thinking is on by default.
  - **Gemma 4 12B-it**, https://huggingface.co/google/gemma-4-12B-it: "Apache 2.0";
    dense, with 11.95B parameters; the QAT Q4_0 GGUF, 6.98 GB. Thinking is off by
    default.

## Decision

Use Gemma 4 31B-it for the live test, served by llama.cpp's `llama-server` 0.5.0
(build 11146, commit 7fe450e19), with:

- the model ID `gemma-4-31b-it-qat-q4_0`;
- the weights' SHA-256
  `179cfb99212709597eae5929112cfca677e1bbf566178b479ae1da0c4772874b`, by
  `shasum -a 256` over the one file `gemma-4-31B_q4_0-it.gguf` (17,651,001,568
  bytes) from `google/gemma-4-31B-it-qat-q4_0-gguf` at revision
  `59dde24573e7e61570dba08b18a2e1fe246955ed`. It equals the SHA-256 that Hugging
  Face publishes for that file;
- the license, "Apache 2.0", from https://huggingface.co/google/gemma-4-31B-it, read
  on 2026-10-04. Google's Gemma 4 license page,
  https://ai.google.dev/gemma/docs/gemma_4_license, read on 2026-10-05, names it
  "Apache License 2.0". Its menu also links a prohibited-use policy and an
  intended-use statement, which the page does not say apply to Gemma 4.

The server runs text only, without the repository's vision projector,
`gemma-4-31B-it-mmproj.gguf`. It is started with
`--alias gemma-4-31b-it-qat-q4_0 --host 127.0.0.1 --port 8080 -c 8192 -np 1
--reasoning off`.

This is not the production choice, which stays open (`AGENTS.md`, §Source basis and
unresolved choices). The model serves the live test only.

## Consequences

- `config/models/local-model.toml` records the endpoint and the model's identity. The
  live test skips visibly without it, or without a server.
- Every cached reply's key names the model, its weights' hash, and the runtime and
  its version (R14.6), so a change of any of them misses the cache.
- `llama-server` names each reply's model by its `--alias`, never by the request's
  `model`. So `model_mismatch` checks the server's configuration, not an echo of the
  request.
- The live run on 2026-10-05 printed `1 passed in 90.64s (0:01:30)`
  (`docs/verification/evidence-selection.md`, plan B's section).

## Alternatives considered

- **Gemma 4 26B-A4B-it.** About twice as fast, with roughly 3 GB more headroom, but
  weaker. The live test must complete both windows, so it favors the stronger model.
- **Qwen3.8-27B.** The newest of the four. But its thinking is on by default and must
  be turned off on the server, and its card gives settings against repetition.
  Either could leave a reply unfinished within the 2048-token limit.
- **Gemma 4 12B-it.** The weakest of the four: a fallback for memory and speed that
  this machine does not need.

## Trade-offs & reversibility

Reversible. Another model is a new configuration and a new ADR, and its replies miss
the cache by key. No committed file stores a reply.
